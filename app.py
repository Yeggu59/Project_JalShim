import streamlit as st
import pickle
import numpy as np
import pandas as pd
import os
import glob

# ──────────────────────────────────────────
#  기본 설정
# ──────────────────────────────────────────
st.set_page_config(page_title="PACE MAKER", page_icon="🏃", layout="centered")

st.markdown("""
<style>
    /* 전체 배경 */
    .stApp { background-color: #0f0f0f; color: #f0f0f0; }
    #MainMenu, footer, header { visibility: hidden; }

    /* 컨테이너 카드 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 16px !important;
        padding: 8px !important;
    }

    /* 버튼 */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        font-weight: 600;
        height: 52px;
        font-size: 15px;
        border: none;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }

    /* primary 버튼 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6c63ff, #4f46e5);
        color: white;
    }

    /* 탭 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1a1a;
        border-radius: 14px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-weight: 600;
        color: #888;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6c63ff !important;
        color: white !important;
    }

    /* 입력 필드 */
    .stNumberInput input, .stSelectbox select {
        background-color: #222 !important;
        border-color: #333 !important;
        color: #f0f0f0 !important;
        border-radius: 10px !important;
    }

    /* 슬라이더 */
    .stSlider [data-baseweb="slider"] { padding: 0; }

    /* 구분선 */
    hr { border-color: #2a2a2a; }

    /* 메트릭 */
    [data-testid="stMetricValue"] { color: #6c63ff; font-size: 2rem !important; }

    /* 프로그레스바 */
    .stProgress > div > div { background: linear-gradient(90deg, #6c63ff, #4f46e5); border-radius: 99px; }

    /* 토스트 */
    [data-testid="stToast"] { background-color: #1a1a1a; border: 1px solid #2a2a2a; }

    h1, h2, h3, h4 {
        font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
        color: #f0f0f0;
    }
    p, label, span { color: #aaa; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
#  상수
# ──────────────────────────────────────────
BASELINE_MET_ALL  = 967    # 전체 (저강도 이상, 2.5+ MET)
BASELINE_MET_3_0  = 399    # 중강도 이상 (3.0+ MET) ← 기본 기준
BASELINE_MET_6_0  = 320    # 고강도 이상 (6.0+ MET)

# ──────────────────────────────────────────
#  data/sleep 통계 로드 (결측치 보완 + 워치 시뮬레이션)
# ──────────────────────────────────────────
@st.cache_data
def load_sleep_stats():
    """data/sleep/ CSV 전체를 읽어 피처별 평균·표준편차 반환"""
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sleep")
    files = glob.glob(os.path.join(base, "*.csv"))

    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df.columns = [str(c).strip().upper() for c in df.columns]
        dfs.append(df)

    raw = pd.concat(dfs, ignore_index=True)

    def time_to_hours(t):
        if pd.isna(t): return None
        parts = str(t).split(":")
        return int(parts[0]) + int(parts[1]) / 60 if len(parts) >= 2 else None

    raw["HOURS_DECIMAL"] = raw["HOURS OF SLEEP"].apply(time_to_hours)
    raw["REM_PERCENT"]   = raw["REM SLEEP"].astype(str).str.replace("%", "").astype(float)
    raw["DEEP_PERCENT"]  = raw["DEEP SLEEP"].astype(str).str.replace("%", "").astype(float)
    hr_col = next((c for c in raw.columns if "HEART" in c or "RESTING" in c), None)
    raw["HR_BELOW_RESTING"] = raw[hr_col].astype(str).str.replace("%", "").astype(float) if hr_col else np.nan
    raw = raw.dropna(subset=["HOURS_DECIMAL", "REM_PERCENT", "DEEP_PERCENT", "HR_BELOW_RESTING"])

    stats = {}
    for col in ["HOURS_DECIMAL", "REM_PERCENT", "DEEP_PERCENT", "HR_BELOW_RESTING"]:
        stats[col] = {
            "mean": float(raw[col].mean()),
            "std":  float(raw[col].std()),
            "min":  float(raw[col].min()),
            "max":  float(raw[col].max()),
        }
    return stats

SLEEP_STATS = load_sleep_stats()

def _clamp(val, col):
    """평균 ± 2σ 범위로 클램프"""
    s = SLEEP_STATS[col]
    return float(np.clip(val, s["min"], s["max"]))

def simulate_watch_sync():
    """워치 동기화 시뮬레이션: data/sleep 통계 기반 정규분포 랜덤 생성"""
    result = {}
    for col in ["HOURS_DECIMAL", "REM_PERCENT", "DEEP_PERCENT", "HR_BELOW_RESTING"]:
        s = SLEEP_STATS[col]
        val = np.random.normal(s["mean"], s["std"] * 0.5)   # std 절반 → 너무 극단값 방지
        result[col] = _clamp(val, col)
    return result

# ──────────────────────────────────────────
#  ACWR 계산 (Foster sRPE + Gabbett)
# ──────────────────────────────────────────
def calc_acwr(logs: list, baseline: float, current_day: int) -> dict:
    """
    logs: [{"day": int, "load": float}, ...]
    baseline: 온보딩 기준 만성부하 (초기값)
    current_day: 오늘 streak 번호

    반환:
      acute  : 최근 7일 부하 합산
      chronic: 최근 28일 일평균 부하
      acwr   : acute / chronic
      zone   : "부족" / "최적" / "주의" / "위험"
      target_multiplier: 다음 처방 배수
    """
    # 최근 7일 / 28일 로그 필터
    acute_logs   = [l["load"] for l in logs if current_day - l["day"] < 7]
    chronic_logs = [l["load"] for l in logs if current_day - l["day"] < 28]

    acute = sum(acute_logs)

    if len(chronic_logs) >= 7:
        # 28일 평균 × 7 → 주간 chronic
        chronic = (sum(chronic_logs) / len(chronic_logs)) * 7
    else:
        # 데이터 부족 → baseline을 주간 환산으로 사용
        chronic = baseline * 7

    acwr = acute / chronic if chronic > 0 else 1.0

    if acwr < 0.8:
        zone, load_mult = "부족",  1.2
    elif acwr <= 1.3:
        zone, load_mult = "최적",  1.0
    elif acwr <= 1.5:
        zone, load_mult = "주의",  0.85
    else:
        zone, load_mult = "위험",  0.6

    return {"acute": round(acute), "chronic": round(chronic),
            "acwr": round(acwr, 2), "zone": zone, "load_mult": load_mult}


def calc_sleep_modifier(score: int) -> float:
    if score >= 80: return 1.1
    if score >= 50: return 1.0
    return 0.8


def impute_missing(hist):
    """간편 입력 결측치 보완: 유저 이력 평균 → data/sleep 평균 순"""
    return {
        "REM_PERCENT":     float(np.mean(hist["rem"]))  if hist["rem"]  else SLEEP_STATS["REM_PERCENT"]["mean"],
        "DEEP_PERCENT":    float(np.mean(hist["deep"])) if hist["deep"] else SLEEP_STATS["DEEP_PERCENT"]["mean"],
        "HR_BELOW_RESTING":float(np.mean(hist["hr"]))  if hist["hr"]   else SLEEP_STATS["HR_BELOW_RESTING"]["mean"],
    }

# ──────────────────────────────────────────
#  ML 모델 로드
# ──────────────────────────────────────────
@st.cache_resource
def load_ml_model():
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sleep_model.pkl")
    try:
        with open(model_path, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None

ml_model = load_ml_model()

# ──────────────────────────────────────────
#  세션 상태 초기화
# ──────────────────────────────────────────
defaults = {
    "step":         0,          # 온보딩 단계 (0=시작 전, 1~N=진행, -1=완료)
    "use_watch":    False,
    "baseline_met": BASELINE_MET_3_0,
    "streak":       0,
    "sleep_score":  None,
    "user_history": {"rem": [], "deep": [], "hr": []},
    # 운동 부하 기록 (ACWR 계산용): [{"day": int, "load": float}, ...]
    "session_logs": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────
#  온보딩 (한 질문씩)
# ──────────────────────────────────────────
ONBOARDING_STEPS = 2

def show_onboarding():
    step = st.session_state["step"]

    # 진행 바
    st.progress(step / ONBOARDING_STEPS)
    st.markdown(f"<p style='text-align:right; color:#555; font-size:13px;'>{step} / {ONBOARDING_STEPS}</p>", unsafe_allow_html=True)
    st.write("")

    # ── STEP 0: 시작 화면 ──────────────────
    if step == 0:
        st.markdown("<h1 style='font-size:2.4rem;'>🏃 PACE MAKER</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:1rem; color:#888;'>수면 데이터를 기반으로<br>당신만의 운동 리듬을 설계합니다.</p>", unsafe_allow_html=True)
        st.write("")
        if st.button("시작하기", type="primary"):
            st.session_state["step"] = 1
            st.rerun()

    # ── STEP 1: 워치 유무 ──────────────────
    elif step == 1:
        st.markdown("### ⌚ 스마트워치를 사용 중이신가요?")
        st.markdown("<p style='color:#666;'>워치가 있으면 수면 데이터를 자동으로 불러올 수 있어요.</p>", unsafe_allow_html=True)
        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 사용합니다", type="primary"):
                st.session_state["use_watch"] = True
                st.session_state["step"] = 2
                st.rerun()
        with col2:
            if st.button("📱 스마트폰만"):
                st.session_state["use_watch"] = False
                st.session_state["step"] = 2
                st.rerun()

    # ── STEP 2: 활동 수준 ──────────────────
    elif step == 2:
        st.markdown("### 💪 최근 한 달간 활동 수준은?")
        st.markdown("<p style='color:#666;'>운동 처방 기준값 설정에 사용돼요.</p>", unsafe_allow_html=True)
        st.write("")

        levels = {
            "🛋️  거의 안 움직여요": BASELINE_MET_3_0 * 0.6,
            "🚶 가끔 산책해요":     BASELINE_MET_3_0,
            "🏋️ 주 3회 이상 운동해요": BASELINE_MET_3_0 * 1.5,
        }
        for label, val in levels.items():
            if st.button(label):
                st.session_state["baseline_met"] = int(val)
                st.session_state["step"] = -1   # 온보딩 완료
                st.rerun()

# ──────────────────────────────────────────
#  메인 앱 (탭 UI)
# ──────────────────────────────────────────
def show_main():
    # 상단 헤더
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"<h2 style='margin-bottom:0;'>PACE MAKER</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#555; margin-top:0;'>Day {st.session_state['streak']}</p>", unsafe_allow_html=True)
    with col2:
        icon = "⌚" if st.session_state["use_watch"] else "📱"
        st.markdown(f"<h2 style='text-align:right; margin-top:10px;'>{icon}</h2>", unsafe_allow_html=True)

    st.progress(min(st.session_state["streak"] / 30, 1.0))
    st.write("")

    # ── 탭 구성 ───────────────────────────
    tab_today, tab_history, tab_settings = st.tabs(["🏠  오늘", "📈  기록", "⚙️  설정"])

    # ════════════════════════════════════════
    #  탭 1 : 오늘 (수면 체크 + 운동 처방)
    # ════════════════════════════════════════
    with tab_today:
        if st.session_state["sleep_score"] is None:
            _show_sleep_input()
        else:
            _show_prescription()

    # ════════════════════════════════════════
    #  탭 2 : 기록
    # ════════════════════════════════════════
    with tab_history:
        st.markdown("#### 📈 활동 기록")
        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.metric("🔥 연속 달성", f"{st.session_state['streak']}일")
        with col2:
            with st.container(border=True):
                hist = st.session_state["user_history"]
                avg_rem = f"{np.mean(hist['rem']):.1f}%" if hist["rem"] else "-"
                st.metric("💤 평균 REM", avg_rem)

        st.write("")
        with st.container(border=True):
            st.markdown("**수면 데이터 이력**")
            if hist["rem"]:
                for i, (r, d, h) in enumerate(zip(hist["rem"], hist["deep"], hist["hr"]), 1):
                    st.markdown(f"<p style='color:#888; font-size:13px;'>#{i} &nbsp; REM {r:.0f}% &nbsp;|&nbsp; 깊은수면 {d:.0f}% &nbsp;|&nbsp; 안정심박 {h:.0f}%</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#555;'>아직 기록된 데이터가 없어요.</p>", unsafe_allow_html=True)

    # ════════════════════════════════════════
    #  탭 3 : 설정
    # ════════════════════════════════════════
    with tab_settings:
        st.markdown("#### ⚙️ 설정")
        st.write("")

        with st.container(border=True):
            st.markdown("**MET 기준 보기**")
            st.markdown(f"<p style='color:#666; font-size:13px;'>현재 기준: 3.0 MET 이상</p>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("전체 (저강도↑)", f"{BASELINE_MET_ALL}")
            with col2:
                st.metric("중강도↑ (3.0+)", f"{BASELINE_MET_3_0}")
            with col3:
                st.metric("고강도↑ (6.0+)", f"{BASELINE_MET_6_0}")

        st.write("")
        with st.container(border=True):
            st.markdown("**디바이스**")
            new_watch = st.toggle("스마트워치 연동", value=st.session_state["use_watch"])
            if new_watch != st.session_state["use_watch"]:
                st.session_state["use_watch"] = new_watch
                st.rerun()

        st.write("")
        with st.container(border=True):
            st.markdown("**초기화**")
            if st.button("⚠️ 처음부터 다시 시작", type="secondary"):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()


# ──────────────────────────────────────────
#  수면 입력 섹션
# ──────────────────────────────────────────
def _show_sleep_input():
    with st.container(border=True):
        st.markdown("#### 🌙 오늘 컨디션 체크")
        st.write("")

        if st.session_state["use_watch"]:
            # 워치 동기화 시뮬레이션: data/sleep 통계 기반 랜덤 생성
            if "watch_synced_data" not in st.session_state:
                st.session_state["watch_synced_data"] = simulate_watch_sync()

            wd = st.session_state["watch_synced_data"]
            st.success("⌚ 어제 수면 데이터를 동기화했습니다.")
            st.markdown(
                f"<p style='color:#666; font-size:13px;'>"
                f"수면 {wd['HOURS_DECIMAL']:.1f}h &nbsp;|&nbsp; "
                f"REM {wd['REM_PERCENT']:.0f}% &nbsp;|&nbsp; "
                f"깊은수면 {wd['DEEP_PERCENT']:.0f}% &nbsp;|&nbsp; "
                f"안정심박이하 {wd['HR_BELOW_RESTING']:.0f}%"
                f"</p>", unsafe_allow_html=True
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("동기화 데이터로 처방받기", type="primary"):
                    if ml_model:
                        X = pd.DataFrame([[wd["HOURS_DECIMAL"], wd["REM_PERCENT"],
                                           wd["DEEP_PERCENT"], wd["HR_BELOW_RESTING"]]],
                                         columns=["HOURS_DECIMAL", "REM_PERCENT",
                                                  "DEEP_PERCENT", "HR_BELOW_RESTING"])
                        score = int(ml_model.predict(X)[0])
                        st.session_state["sleep_score"] = min(max(score, 0), 100)
                        del st.session_state["watch_synced_data"]   # 다음날 새로 생성
                        st.rerun()
            with col2:
                if st.button("수동으로 입력하기"):
                    del st.session_state["watch_synced_data"]
                    st.session_state["use_watch"] = False
                    st.rerun()
            return

        input_mode = st.radio("입력 방식", ["⚡ 간편 입력", "🔬 상세 입력 (정확도 ↑)"], horizontal=True, label_visibility="collapsed")
        st.write("")

        # ── 간편 입력 ──
        if "간편" in input_mode:
            col1, col2 = st.columns(2)
            with col1:
                sleep_hours = st.number_input("수면 시간 (h)", 0.0, 24.0, 7.0, 0.5, format="%.1f")
            with col2:
                subjective_feel = st.slider("개운함", 1, 5, 3, help="1 최악 → 5 상쾌")

            st.write("")
            if st.button("분석하기", type="primary"):
                if ml_model is None:
                    st.error("모델 파일(sleep_model.pkl)을 찾을 수 없습니다.")
                else:
                    imp = impute_missing(st.session_state["user_history"])
                    X = pd.DataFrame([[sleep_hours, imp["REM_PERCENT"],
                                       imp["DEEP_PERCENT"], imp["HR_BELOW_RESTING"]]],
                                     columns=["HOURS_DECIMAL", "REM_PERCENT",
                                              "DEEP_PERCENT", "HR_BELOW_RESTING"])
                    score = int(ml_model.predict(X)[0] * (subjective_feel / 3.0))
                    st.session_state["sleep_score"] = min(max(score, 0), 100)
                    st.rerun()

        # ── 상세 입력 ──
        else:
            col1, col2 = st.columns(2)
            with col1:
                sleep_hours  = st.number_input("수면 시간 (h)", 0.0, 24.0, 7.0, 0.5, format="%.1f")
                rem_percent  = st.number_input("REM 수면 (%)", 0.0, 100.0, 18.0, 1.0)
            with col2:
                deep_percent = st.number_input("깊은 수면 (%)", 0.0, 100.0, 17.0, 1.0)
                hr_below     = st.number_input("안정심박 이하 비율 (%)", 0.0, 100.0, 85.0, 1.0)

            st.write("")
            if st.button("분석하기", type="primary"):
                if ml_model is None:
                    st.error("모델 파일(sleep_model.pkl)을 찾을 수 없습니다.")
                else:
                    X = pd.DataFrame([[sleep_hours, rem_percent, deep_percent, hr_below]],
                                     columns=["HOURS_DECIMAL", "REM_PERCENT", "DEEP_PERCENT", "HR_BELOW_RESTING"])
                    score = int(ml_model.predict(X)[0])
                    st.session_state["user_history"]["rem"].append(rem_percent)
                    st.session_state["user_history"]["deep"].append(deep_percent)
                    st.session_state["user_history"]["hr"].append(hr_below)
                    st.session_state["sleep_score"] = min(max(score, 0), 100)
                    st.rerun()


# ──────────────────────────────────────────
#  운동 처방 섹션
# ──────────────────────────────────────────
def _show_prescription():
    score    = st.session_state["sleep_score"]
    logs     = st.session_state["session_logs"]
    baseline = st.session_state["baseline_met"]
    day      = st.session_state["streak"]

    # ── 수면 회복 카드 ──────────────────────
    if score >= 80:   s_emoji, s_msg = "🟢", "회복 양호 — 강도를 높여봐요!"
    elif score >= 50: s_emoji, s_msg = "🟡", "회복 보통 — 평소대로 운동하세요."
    else:             s_emoji, s_msg = "🔴", "회복 부족 — 가볍게만 움직이세요."

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"#### {s_emoji} 회복 점수")
            st.markdown(f"<p style='color:#888; font-size:13px;'>{s_msg}</p>", unsafe_allow_html=True)
        with col2:
            st.metric("", f"{score}점")
        st.progress(score / 100)
        if st.button("다시 측정", key="rescore"):
            st.session_state["sleep_score"] = None
            st.rerun()

    st.write("")

    # ── ACWR 부하 상태 카드 ─────────────────
    acwr_info = calc_acwr(logs, baseline, day)
    zone = acwr_info["zone"]
    acwr_val = acwr_info["acwr"]

    zone_emoji = {"부족": "📉", "최적": "✅", "주의": "⚠️", "위험": "🚨"}[zone]
    zone_color = {"부족": "#4fc3f7", "최적": "#81c784", "주의": "#ffb74d", "위험": "#e57373"}[zone]

    with st.container(border=True):
        st.markdown(f"#### 📊 훈련 부하 상태")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("급성 부하 (7일)", f"{acwr_info['acute']}")
        with col2:
            st.metric("만성 부하 (28일)", f"{acwr_info['chronic']}")
        with col3:
            st.metric("ACWR", f"{acwr_val}")
        st.markdown(
            f"<div style='background:{zone_color}22; border:1px solid {zone_color}55; "
            f"border-radius:10px; padding:8px 14px; margin-top:6px;'>"
            f"<span style='color:{zone_color}; font-weight:700;'>{zone_emoji} {zone} 구간</span>"
            f"<span style='color:#888; font-size:12px;'> &nbsp;|&nbsp; Sweet Spot: 0.8 ~ 1.3</span>"
            f"</div>", unsafe_allow_html=True
        )

    st.write("")

    # ── 오늘의 처방 ─────────────────────────
    sleep_mod = calc_sleep_modifier(score)
    load_mult = acwr_info["load_mult"] * sleep_mod
    target    = int(baseline * load_mult)

    with st.container(border=True):
        st.markdown("#### 🎯 오늘의 운동 처방")
        st.metric("목표 세션 부하 (RPE × 분)", f"{target}")
        st.markdown(
            f"<p style='color:#555; font-size:12px;'>"
            f"기준 {baseline} × ACWR보정 {acwr_info['load_mult']} × 수면보정 {sleep_mod:.1f}"
            f"</p>", unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='color:#888; font-size:12px;'>"
            f"💡 예: RPE 7 × {target//7}분 / RPE 5 × {target//5}분 / RPE 3 × {target//3}분"
            f"</p>", unsafe_allow_html=True
        )
        st.write("")

        # 운동 완료 입력 (RPE + 시간)
        with st.expander("✅ 운동 완료 기록하기"):
            col1, col2 = st.columns(2)
            with col1:
                duration = st.number_input("운동 시간 (분)", min_value=1, max_value=300, value=30, step=5)
            with col2:
                rpe = st.slider("운동 강도 (RPE)", 1, 10, 5,
                                help="1=매우 쉬움 ~ 10=최대 강도 (운동 끝나고 15~30분 후 평가)")

            session_load = duration * rpe
            st.markdown(f"<p style='color:#6c63ff; font-size:13px;'>세션 부하: {duration}분 × RPE {rpe} = <b>{session_load}</b></p>",
                        unsafe_allow_html=True)

            st.write("")
            st.markdown("<p style='color:#888; font-size:12px;'>오늘 운동이 어떠셨나요?</p>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            feedback = None
            with col1:
                if st.button("😰 너무 힘들었어"):  feedback = "hard"
            with col2:
                if st.button("👍 딱 적당했어"):     feedback = "ok"
            with col3:
                if st.button("💪 너무 쉬웠어"):     feedback = "easy"

            if feedback:
                # 피드백 → baseline 수렴 (±5%)
                adj = {"hard": 0.95, "ok": 1.0, "easy": 1.05}[feedback]
                st.session_state["baseline_met"] = int(baseline * adj)

                # 세션 부하 기록
                st.session_state["session_logs"].append({"day": day, "load": session_load})

                st.session_state["streak"] += 1
                st.session_state["sleep_score"] = None
                st.toast("기록 완료! 🔥", icon="🔥")
                st.rerun()


# ──────────────────────────────────────────
#  라우터
# ──────────────────────────────────────────
if st.session_state["step"] != -1:
    show_onboarding()
else:
    show_main()
