import streamlit as st
import pickle
import numpy as np
import pandas as pd
import os
import glob
import json

# ──────────────────────────────────────────
#  기본 설정
# ──────────────────────────────────────────
st.set_page_config(page_title="잘쉼", page_icon="🌙", layout="centered")

# ── 6:3:1 컬러 시스템 ──────────────────────
# 60% : #F0F4FF  (메인 배경 — 연한 블루화이트)
# 30% : #FFFFFF / #DBEAFE  (카드 배경 — 흰색 / 연파랑)
# 10% : #2563EB  (포인트 — 파랑)
st.markdown("""
<style>
    /* ── 전체 배경 (60%) ── */
    .stApp { background-color: #F0F4FF; color: #1e293b; }
    #MainMenu, footer, header { visibility: hidden; }

    /* ── 카드 컨테이너 (30%) ── */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 16px !important;
        padding: 8px !important;
        box-shadow: 0 1px 6px rgba(37,99,235,0.07) !important;
    }

    /* ── 버튼 기본 ── */
    .stButton > button {
        width: 100%; border-radius: 12px; font-weight: 600;
        height: 52px; font-size: 15px; border: 1.5px solid #CBD5E1;
        background-color: #FFFFFF; color: #1e293b !important;
        transition: all 0.18s;
    }
    .stButton > button:hover {
        background-color: #EEF2FF; border-color: #2563EB; color: #2563EB !important;
    }

    /* ── primary 버튼 (10% 포인트) ── */
    .stButton > button[kind="primary"] {
        background: #2563EB !important; color: #FFFFFF !important; border: none;
        box-shadow: 0 2px 8px rgba(37,99,235,0.25);
    }
    .stButton > button[kind="primary"]:hover {
        background: #1d4ed8 !important; color: #FFFFFF !important;
    }
    /* primary 버튼 내부 p, span 텍스트 강제 흰색 */
    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span {
        color: #FFFFFF !important;
    }

    /* ── secondary 버튼 ── */
    .stButton > button[kind="secondary"] {
        background: #FFF1F2 !important; color: #e11d48 !important;
        border-color: #fda4af !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #ffe4e6 !important; color: #be123c !important;
    }

    /* ── 탭 ── */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #FFFFFF; border-radius: 14px;
        padding: 6px; gap: 8px;
        border: 1px solid #CBD5E1;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px; font-weight: 600; color: #64748b;
        padding: 8px 20px !important; font-size: 14px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563EB !important; color: #FFFFFF !important;
    }
    .stTabs [aria-selected="true"] p,
    .stTabs [aria-selected="true"] span {
        color: #FFFFFF !important;
    }

    /* ── 입력 필드 ── */
    .stNumberInput input, .stTextInput input {
        background-color: #FFFFFF !important;
        border-color: #CBD5E1 !important;
        color: #1e293b !important;
        border-radius: 10px !important;
    }

    /* ── 슬라이더 포인트 색 ── */
    [data-testid="stSlider"] [role="slider"] { background: #2563EB !important; }

    /* ── 프로그레스바 ── */
    .stProgress > div > div {
        background: linear-gradient(90deg, #2563EB, #60a5fa);
        border-radius: 99px;
    }

    /* ── 메트릭 숫자 ── */
    [data-testid="stMetricValue"] { color: #2563EB !important; font-size: 1.8rem !important; }

    /* ── 라디오 ── */
    .stRadio [data-testid="stWidgetLabel"] { color: #64748b !important; }

    /* ── expander ── */
    .streamlit-expanderHeader { background-color: #EEF2FF !important; border-radius: 10px !important; }

    /* ── 토스트 ── */
    [data-testid="stToast"] { background: #FFFFFF; border: 1px solid #CBD5E1; }

    /* ── 알림 박스 ── */
    .stSuccess { background-color: #ECFDF5 !important; border-color: #10b981 !important; }
    .stInfo    { background-color: #EFF6FF !important; border-color: #2563EB !important; }
    .stWarning { background-color: #FFFBEB !important; border-color: #f59e0b !important; }

    h1, h2, h3, h4 {
        font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
        color: #1e293b;
    }
    p, label, span { color: #64748b; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
#  상수
# ──────────────────────────────────────────
BASELINE_MET_ALL = 967   # 전체 (저강도 이상)
BASELINE_MET_3_0 = 399   # 중강도 이상 (3.0+ MET) ← 기본 기준
BASELINE_MET_6_0 = 320   # 고강도 이상 (6.0+ MET)

# ACSM 2024 Compendium 기반 운동 DB (MET 값 + 설명)
EXERCISE_DB = {
    "저강도": [
        {"name": "스트레칭 / 요가",    "met": 2.5,  "emoji": "🧘"},
        {"name": "평지 천천히 걷기",    "met": 3.0,  "emoji": "🚶"},
        {"name": "자전거 매우 가볍게",  "met": 3.5,  "emoji": "🚲"},
    ],
    "중강도": [
        {"name": "빠르게 걷기",         "met": 4.5,  "emoji": "🚶‍♂️"},
        {"name": "자전거 (일반 속도)",   "met": 6.0,  "emoji": "🚴"},
        {"name": "배드민턴 / 탁구",     "met": 5.5,  "emoji": "🏸"},
        {"name": "수영 (천천히)",        "met": 5.8,  "emoji": "🏊"},
        {"name": "등산 (완만한 경사)",   "met": 6.0,  "emoji": "⛰️"},
        {"name": "웨이트 트레이닝",      "met": 5.0,  "emoji": "🏋️"},
    ],
    "고강도": [
        {"name": "달리기 (8km/h)",       "met": 7.5,  "emoji": "🏃"},
        {"name": "달리기 (10km/h)",      "met": 9.8,  "emoji": "🏃‍♂️"},
        {"name": "줄넘기 (보통)",         "met": 8.8,  "emoji": "⏩"},
        {"name": "수영 (빠르게)",         "met": 7.0,  "emoji": "🏊‍♂️"},
        {"name": "축구 / 농구",           "met": 7.5,  "emoji": "⚽"},
        {"name": "등산 (가파른 경사)",    "met": 8.0,  "emoji": "🧗"},
    ],
}

# WHO 2020 주간 권장 (성인)
WHO_MODERATE_MIN_WEEK = 150   # 중강도 최소 분/주
WHO_VIGOROUS_MIN_WEEK = 75    # 고강도 최소 분/주
WHO_MET_MIN_WEEK      = 600   # 최소 MET-min/주 (중강도 4 MET × 150분)


# ──────────────────────────────────────────
#  data/sleep 통계 로드
# ──────────────────────────────────────────
@st.cache_data
def load_sleep_stats():
    base  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sleep")
    files = glob.glob(os.path.join(base, "*.csv"))
    dfs   = []
    for f in files:
        df = pd.read_csv(f)
        df.columns = [str(c).strip().upper() for c in df.columns]
        dfs.append(df)
    raw = pd.concat(dfs, ignore_index=True)

    def _t2h(t):
        if pd.isna(t): return None
        p = str(t).split(":")
        return int(p[0]) + int(p[1]) / 60 if len(p) >= 2 else None

    raw["HOURS_DECIMAL"]    = raw["HOURS OF SLEEP"].apply(_t2h)
    raw["REM_PERCENT"]      = raw["REM SLEEP"].astype(str).str.replace("%","").astype(float)
    raw["DEEP_PERCENT"]     = raw["DEEP SLEEP"].astype(str).str.replace("%","").astype(float)
    hr_col = next((c for c in raw.columns if "HEART" in c or "RESTING" in c), None)
    raw["HR_BELOW_RESTING"] = raw[hr_col].astype(str).str.replace("%","").astype(float) if hr_col else np.nan
    raw = raw.dropna(subset=["HOURS_DECIMAL","REM_PERCENT","DEEP_PERCENT","HR_BELOW_RESTING"])

    return {col: {"mean": float(raw[col].mean()), "std": float(raw[col].std()),
                  "min":  float(raw[col].min()),  "max": float(raw[col].max())}
            for col in ["HOURS_DECIMAL","REM_PERCENT","DEEP_PERCENT","HR_BELOW_RESTING"]}

SLEEP_STATS = load_sleep_stats()


def simulate_watch_sync():
    result = {}
    for col in ["HOURS_DECIMAL","REM_PERCENT","DEEP_PERCENT","HR_BELOW_RESTING"]:
        s   = SLEEP_STATS[col]
        val = np.random.normal(s["mean"], s["std"] * 0.5)
        result[col] = float(np.clip(val, s["min"], s["max"]))
    return result


def impute_missing(hist):
    return {
        "REM_PERCENT":      float(np.mean(hist["rem"]))  if hist["rem"]  else SLEEP_STATS["REM_PERCENT"]["mean"],
        "DEEP_PERCENT":     float(np.mean(hist["deep"])) if hist["deep"] else SLEEP_STATS["DEEP_PERCENT"]["mean"],
        "HR_BELOW_RESTING": float(np.mean(hist["hr"]))  if hist["hr"]   else SLEEP_STATS["HR_BELOW_RESTING"]["mean"],
    }


# ──────────────────────────────────────────
#  ML 모델 로드
# ──────────────────────────────────────────
@st.cache_resource
def load_ml_model():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sleep_model.pkl")
    try:
        with open(path, "rb") as f: return pickle.load(f)
    except FileNotFoundError:      return None

ml_model = load_ml_model()


# ──────────────────────────────────────────
#  ACWR 계산 (Foster sRPE + Gabbett)
# ──────────────────────────────────────────
def calc_acwr(logs, baseline, current_day):
    acute_loads   = [l["load"] for l in logs if current_day - l["day"] < 7]
    chronic_loads = [l["load"] for l in logs if current_day - l["day"] < 28]

    acute   = sum(acute_loads)
    chronic = (sum(chronic_loads) / len(chronic_loads) * 7) if len(chronic_loads) >= 7 else baseline * 7
    acwr    = acute / chronic if chronic > 0 else 1.0

    if   acwr < 0.8:  zone, load_mult = "부족",  1.20
    elif acwr <= 1.3: zone, load_mult = "최적",  1.00
    elif acwr <= 1.5: zone, load_mult = "주의",  0.85
    else:             zone, load_mult = "위험",  0.60

    return {"acute": round(acute), "chronic": round(chronic),
            "acwr":  round(acwr, 2), "zone": zone, "load_mult": load_mult}


def calc_sleep_modifier(score):
    if score >= 80: return 1.1
    if score >= 50: return 1.0
    return 0.8


def rpe_to_met(rpe: int) -> float:
    """
    CR10 RPE → MET 근사 변환
    근거: Borg CR10 기준, 중강도(RPE 5) ≈ 4.5 MET, 고강도(RPE 8) ≈ 8 MET
    선형 근사: MET ≈ RPE × 0.9 + 1.0  (일반 성인 기준, 개인 VO2max에 따라 다름)
    """
    return round(rpe * 0.9 + 1.0, 1)


# ──────────────────────────────────────────
#  데이터 영속성 (JSON 파일)
# ──────────────────────────────────────────
USER_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data.json")

PERSIST_KEYS = ["step", "use_watch", "baseline_met", "streak", "user_history", "session_logs"]

_DEFAULTS = {
    "step":         0,
    "use_watch":    False,
    "baseline_met": BASELINE_MET_3_0,
    "streak":       0,
    "sleep_score":  None,
    "user_history": {"rem": [], "deep": [], "hr": []},
    "session_logs": [],
    "page":         "main",   # "main" | "workout_log"
}

def load_user_data() -> dict:
    """JSON 파일에서 유저 데이터 로드. 없으면 기본값 반환."""
    if os.path.exists(USER_DATA_PATH):
        try:
            with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # 기본값 위에 저장값 덮어쓰기 (새 키 누락 방지)
            data = dict(_DEFAULTS)
            data.update(saved)
            return data
        except Exception:
            pass
    return dict(_DEFAULTS)


def save_user_data():
    """현재 session_state의 영속 키들을 JSON 파일에 저장."""
    payload = {k: st.session_state[k] for k in PERSIST_KEYS if k in st.session_state}
    with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────
#  세션 상태 초기화 (JSON에서 복원)
# ──────────────────────────────────────────
if "data_loaded" not in st.session_state:
    saved = load_user_data()
    for k, v in saved.items():
        st.session_state[k] = v
    st.session_state["data_loaded"] = True


# ──────────────────────────────────────────
#  공통 UI 컴포넌트
# ──────────────────────────────────────────
def _info_box(title: str, body: str, color: str = "#2563EB"):
    st.markdown(
        f"""<div style='background:{color}11; border-left:4px solid {color};
            border-radius:0 10px 10px 0; padding:10px 14px; margin:8px 0;'>
            <span style='color:{color}; font-weight:700; font-size:13px;'>{title}</span>
            <p style='color:#475569; font-size:12px; margin:4px 0 0;'>{body}</p>
            </div>""",
        unsafe_allow_html=True,
    )


def _badge(text: str, color: str):
    st.markdown(
        f"<span style='background:{color}22; color:{color}; font-weight:700; "
        f"font-size:12px; padding:3px 10px; border-radius:99px; "
        f"border:1px solid {color}44;'>{text}</span>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────
#  온보딩 (한 질문씩)
# ──────────────────────────────────────────
ONBOARDING_STEPS = 2

def show_onboarding():
    step = st.session_state["step"]
    st.progress(step / ONBOARDING_STEPS)
    st.markdown(f"<p style='text-align:right;color:#94a3b8;font-size:12px;'>{step}/{ONBOARDING_STEPS}</p>",
                unsafe_allow_html=True)
    st.write("")

    if step == 0:
        st.markdown("<h1 style='font-size:2.4rem;'>🌙 잘쉼</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:1rem;color:#64748b;'>수면 회복력을 분석해<br>나에게 딱 맞는 운동 처방을 드려요.</p>",
                    unsafe_allow_html=True)
        st.write("")
        if st.button("시작하기", type="primary"):
            st.session_state["step"] = 1
            st.rerun()

    elif step == 1:
        st.markdown("### ⌚ 스마트워치를 사용 중이신가요?")
        _info_box("워치가 있다면?", "수면 데이터(REM, 깊은수면, 심박수)를 자동으로 불러와 더 정확한 분석이 가능해요.")
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

    elif step == 2:
        st.markdown("### 💪 최근 한 달간 활동 수준은?")
        _info_box("왜 물어보나요?", "운동 처방의 초기 기준값(베이스라인)을 설정하는 데 사용돼요. 쓰면 쓸수록 나에게 맞게 자동 조정됩니다.")
        st.write("")
        levels = {
            "🛋️  거의 안 움직여요":     int(BASELINE_MET_3_0 * 0.6),
            "🚶  가끔 산책해요":         BASELINE_MET_3_0,
            "🏋️  주 3회 이상 운동해요": int(BASELINE_MET_3_0 * 1.5),
        }
        for label, val in levels.items():
            if st.button(label):
                st.session_state["baseline_met"] = val
                st.session_state["step"] = -1
                save_user_data()
                st.rerun()


# ──────────────────────────────────────────
#  메인 앱
# ──────────────────────────────────────────
def show_main():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("<h2 style='margin-bottom:0;'>🌙 잘쉼</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8;margin-top:0;'>Day {st.session_state['streak']}</p>",
                    unsafe_allow_html=True)
    with col2:
        icon = "⌚" if st.session_state["use_watch"] else "📱"
        st.markdown(f"<h2 style='text-align:right;margin-top:10px;'>{icon}</h2>", unsafe_allow_html=True)

    st.progress(min(st.session_state["streak"] / 30, 1.0))
    st.write("")

    tab_today, tab_history, tab_settings = st.tabs(["🏠  오늘", "📈  기록", "⚙️  설정"])

    with tab_today:
        if st.session_state["sleep_score"] is None:
            _show_sleep_input()
        else:
            _show_prescription()

    with tab_history:
        _show_history()

    with tab_settings:
        _show_settings()


# ──────────────────────────────────────────
#  수면 입력
# ──────────────────────────────────────────
def _show_sleep_input():
    with st.container(border=True):
        st.markdown("#### 🌙 오늘 컨디션 체크")
        st.write("")

        if st.session_state["use_watch"]:
            if "watch_synced_data" not in st.session_state:
                st.session_state["watch_synced_data"] = simulate_watch_sync()

            wd = st.session_state["watch_synced_data"]
            st.success("⌚ 어제 수면 데이터를 동기화했습니다.")
            st.markdown(
                f"<p style='color:#64748b;font-size:13px;'>"
                f"수면 {wd['HOURS_DECIMAL']:.1f}h &nbsp;·&nbsp; "
                f"REM {wd['REM_PERCENT']:.0f}% &nbsp;·&nbsp; "
                f"깊은수면 {wd['DEEP_PERCENT']:.0f}% &nbsp;·&nbsp; "
                f"안정심박이하 {wd['HR_BELOW_RESTING']:.0f}%"
                f"</p>", unsafe_allow_html=True)

            with st.expander("📖 이 수치들이 뭔가요?"):
                st.markdown("""
| 항목 | 의미 | 건강 기준 |
|------|------|-----------|
| **REM 수면** | 꿈꾸는 단계, 기억 정리·감정 회복 | 총 수면의 **20~25%** |
| **깊은 수면** | 몸이 가장 깊이 쉬는 단계, 근육 회복 | 총 수면의 **15~20%** |
| **안정심박이하 비율** | 수면 중 심박수가 안정시보다 낮은 시간 비율, 심혈관 회복 지표 | **높을수록** 회복 양호 |
                """)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("이 데이터로 분석하기", type="primary"):
                    if ml_model:
                        X = pd.DataFrame([[wd["HOURS_DECIMAL"], wd["REM_PERCENT"],
                                           wd["DEEP_PERCENT"],  wd["HR_BELOW_RESTING"]]],
                                         columns=["HOURS_DECIMAL","REM_PERCENT","DEEP_PERCENT","HR_BELOW_RESTING"])
                        score = int(ml_model.predict(X)[0])
                        st.session_state["sleep_score"] = min(max(score, 0), 100)
                        # 워치 데이터도 user_history에 저장 (결측치 보완 품질 향상)
                        st.session_state["user_history"]["rem"].append(wd["REM_PERCENT"])
                        st.session_state["user_history"]["deep"].append(wd["DEEP_PERCENT"])
                        st.session_state["user_history"]["hr"].append(wd["HR_BELOW_RESTING"])
                        del st.session_state["watch_synced_data"]
                        st.rerun()
            with col2:
                if st.button("수동으로 입력하기"):
                    del st.session_state["watch_synced_data"]
                    st.session_state["use_watch"] = False
                    st.rerun()
            return

        # ── 수동 입력 ──
        input_mode = st.radio("입력 방식", ["⚡ 간편 입력", "🔬 상세 입력 (정확도 ↑)"],
                              horizontal=True, label_visibility="collapsed")
        st.write("")

        if "간편" in input_mode:
            _info_box("간편 입력이란?",
                      "수면 시간과 개운한 정도만 입력하면 나머지는 내 이전 데이터(없으면 통계 평균)로 자동 채워집니다.")
            st.write("")
            col1, col2 = st.columns(2)
            with col1:
                sleep_hours = st.number_input("수면 시간 (시간)", 0.0, 24.0, 7.0, 0.5, format="%.1f")
            with col2:
                subjective_feel = st.slider("기상 직후 개운함", 1, 5, 3,
                                            help="1=최악(개운하지 않음) ~ 5=상쾌함")
            st.caption("💡 개운함 척도: 1 😴 2 😪 3 😐 4 😊 5 😄")
            st.write("")
            if st.button("분석하기", type="primary"):
                if ml_model is None:
                    st.error("모델 파일(sleep_model.pkl)을 찾을 수 없습니다.")
                else:
                    imp = impute_missing(st.session_state["user_history"])
                    X   = pd.DataFrame([[sleep_hours, imp["REM_PERCENT"],
                                         imp["DEEP_PERCENT"], imp["HR_BELOW_RESTING"]]],
                                       columns=["HOURS_DECIMAL","REM_PERCENT","DEEP_PERCENT","HR_BELOW_RESTING"])
                    score = int(ml_model.predict(X)[0] * (subjective_feel / 3.0))
                    st.session_state["sleep_score"] = min(max(score, 0), 100)
                    st.rerun()
        else:
            _info_box("상세 입력이란?",
                      "핏빗 앱 등에서 확인한 수면 세부 데이터를 직접 입력해 가장 정확한 점수를 예측합니다.")
            st.write("")
            col1, col2 = st.columns(2)
            with col1:
                sleep_hours  = st.number_input("수면 시간 (시간)", 0.0, 24.0, 7.0, 0.5, format="%.1f")
                rem_percent  = st.number_input("REM 수면 비율 (%)", 0.0, 100.0, 18.0, 1.0,
                                               help="꿈꾸는 단계. 건강 기준: 20~25%")
            with col2:
                deep_percent = st.number_input("깊은 수면 비율 (%)", 0.0, 100.0, 17.0, 1.0,
                                               help="몸이 가장 깊이 쉬는 단계. 건강 기준: 15~20%")
                hr_below     = st.number_input("안정심박이하 비율 (%)", 0.0, 100.0, 77.0, 1.0,
                                               help="수면 중 심박수가 낮을수록 심혈관 회복이 잘 된 것")
            st.write("")
            if st.button("분석하기", type="primary"):
                if ml_model is None:
                    st.error("모델 파일(sleep_model.pkl)을 찾을 수 없습니다.")
                else:
                    X = pd.DataFrame([[sleep_hours, rem_percent, deep_percent, hr_below]],
                                     columns=["HOURS_DECIMAL","REM_PERCENT","DEEP_PERCENT","HR_BELOW_RESTING"])
                    score = int(ml_model.predict(X)[0])
                    st.session_state["user_history"]["rem"].append(rem_percent)
                    st.session_state["user_history"]["deep"].append(deep_percent)
                    st.session_state["user_history"]["hr"].append(hr_below)
                    st.session_state["sleep_score"] = min(max(score, 0), 100)
                    st.rerun()


# ──────────────────────────────────────────
#  운동 처방
# ──────────────────────────────────────────
def _show_prescription():
    score    = st.session_state["sleep_score"]
    logs     = st.session_state["session_logs"]
    baseline = st.session_state["baseline_met"]
    day      = st.session_state["streak"]

    # ── 수면 점수 카드 ──
    if score >= 80:   s_color, s_emoji, s_msg = "#10b981", "🟢", "회복 양호 — 오늘은 강도를 높여봐요!"
    elif score >= 50: s_color, s_emoji, s_msg = "#f59e0b", "🟡", "회복 보통 — 평소대로 운동하세요."
    else:             s_color, s_emoji, s_msg = "#ef4444", "🔴", "회복 부족 — 오늘은 가볍게만 움직이세요."

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"#### {s_emoji} 오늘의 회복 점수")
            st.markdown(f"<p style='color:{s_color};font-weight:600;'>{s_msg}</p>",
                        unsafe_allow_html=True)
        with col2:
            st.metric("", f"{score}점")
        st.progress(score / 100)

        with st.expander("💡 수면 점수란?"):
            st.markdown("""
수면 중 **REM 비율**, **깊은수면 비율**, **심박수 안정도**, **총 수면 시간**을 AI가 종합해 0~100점으로 산출한 **회복 지수**예요.

| 구간 | 의미 |
|------|------|
| **80점 이상** 🟢 | 충분히 회복됨 |
| **50~79점** 🟡 | 어느 정도 회복됨 |
| **50점 미만** 🔴 | 회복 부족, 휴식 권장 |

> 피트빗이 제공하는 수면 점수와 유사한 방식으로 계산됩니다. (학습 데이터 기반 선형회귀 모델)
            """)
        if st.button("다시 측정", key="rescore"):
            st.session_state["sleep_score"] = None
            st.rerun()

    st.write("")

    # ── ACWR 상태 카드 ──
    acwr_info = calc_acwr(logs, baseline, day)
    zone      = acwr_info["zone"]
    acwr_val  = acwr_info["acwr"]
    z_color   = {"부족":"#3b82f6","최적":"#10b981","주의":"#f59e0b","위험":"#ef4444"}[zone]
    z_emoji   = {"부족":"📉",       "최적":"✅",     "주의":"⚠️",    "위험":"🚨"}[zone]
    z_desc    = {
        "부족":  "운동이 부족해요. 오늘은 조금 더 해도 좋아요.",
        "최적":  "훈련 부하가 이상적인 범위예요. 지금 페이스를 유지하세요!",
        "주의":  "최근 운동 강도가 높아지고 있어요. 살짝 줄여봐요.",
        "위험":  "과부하 상태예요! 오늘은 휴식 또는 가벼운 스트레칭만 하세요.",
    }[zone]

    with st.container(border=True):
        st.markdown("#### 📊 훈련 부하 상태 (ACWR)")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("급성 부하", f"{acwr_info['acute']}",  help="최근 7일간 세션 부하 합산")
        with col2: st.metric("만성 부하", f"{acwr_info['chronic']}", help="최근 28일 평균 주간 부하")
        with col3: st.metric("ACWR 비율", f"{acwr_val}")
        st.markdown(
            f"<div style='background:{z_color}15;border:1px solid {z_color}40;"
            f"border-radius:10px;padding:10px 14px;margin-top:8px;'>"
            f"<span style='color:{z_color};font-weight:700;'>{z_emoji} {zone} 구간</span>"
            f"<span style='color:#64748b;font-size:12px;'> &nbsp;|&nbsp; Sweet Spot 0.8 ~ 1.3</span>"
            f"<p style='color:#475569;font-size:12px;margin:4px 0 0;'>{z_desc}</p>"
            f"</div>", unsafe_allow_html=True)

        with st.expander("💡 ACWR이 뭔가요?"):
            st.markdown("""
**ACWR (급성:만성 부하 비율)**은 *"지난 1주일 운동량"*이 *"최근 한 달 평균 운동량"*의 몇 배인지 나타내요.

*Dr. Tim Gabbett (2016, BJSM)* 연구에 따르면 이 비율이 너무 높거나 낮으면 부상 위험이 올라가요.

| ACWR | 구간 | 의미 |
|------|------|------|
| **< 0.8** | 📉 부족 | 운동량이 너무 적어요 |
| **0.8 ~ 1.3** | ✅ 최적 | 가장 이상적인 범위! |
| **1.3 ~ 1.5** | ⚠️ 주의 | 운동이 빠르게 늘고 있어요 |
| **> 1.5** | 🚨 위험 | 과부하, 부상 위험 증가 |

> 처음 7일간은 내 데이터가 쌓이기 전이라 온보딩에서 설정한 기준값으로 계산돼요.
            """)

    st.write("")

    # ── 운동 처방 카드 ──
    sleep_mod = calc_sleep_modifier(score)
    load_mult = acwr_info["load_mult"] * sleep_mod
    target    = int(baseline * load_mult)

    # WHO 주간 현황
    weekly_load    = sum(l["load"] for l in logs if day - l["day"] < 7)
    # sRPE-min → MET-min 근사 변환 (RPE 5 ≈ 중강도 4.5 MET)
    weekly_met_est = int(weekly_load * 0.9)
    who_progress   = min(weekly_met_est / WHO_MET_MIN_WEEK, 1.0)

    with st.container(border=True):
        st.markdown("#### 🎯 오늘의 운동 처방")

        # WHO 주간 달성률
        st.markdown(f"<p style='color:#64748b;font-size:12px;margin-bottom:4px;'>"
                    f"WHO 주간 권장 달성률 (600 MET-min/주 기준)</p>",
                    unsafe_allow_html=True)
        st.progress(who_progress)
        st.markdown(f"<p style='color:#2563EB;font-size:12px;margin-top:2px;'>"
                    f"이번 주 약 {weekly_met_est} / {WHO_MET_MIN_WEEK} MET-min</p>",
                    unsafe_allow_html=True)

        st.write("")

        # 목표 세션 부하 — RPE 단위 + MET-min 병기
        # 대표 RPE 5 기준으로 MET 환산 (중강도 처방 기준)
        target_met_min = int(target * rpe_to_met(5) / 5)   # RPE5 기준 MET-min 근사
        col1, col2 = st.columns(2)
        with col1:
            st.metric("오늘 목표 세션 부하", f"{target} RPE-min",
                      help="RPE(운동 강도 1~10) × 운동 시간(분)으로 계산되는 운동량 지표예요.")
        with col2:
            st.metric("MET-min 환산 (참고)", f"≈ {target_met_min}",
                      help="RPE 5(중강도) 기준 MET-min 근사값이에요. 실제 운동 강도에 따라 달라집니다.")
        st.markdown(
            f"<p style='color:#94a3b8;font-size:12px;'>"
            f"기준 {baseline} × ACWR 보정 {acwr_info['load_mult']} × 수면 보정 {sleep_mod:.1f}"
            f"&nbsp;·&nbsp; MET 환산: RPE × 0.9 + 1.0 (CR10 근사)"
            f"</p>", unsafe_allow_html=True)

        with st.expander("💡 세션 부하(RPE × 분)란?"):
            st.markdown("""
**세션 부하 = 운동 강도(RPE) × 운동 시간(분)**

Dr. Carl Foster(2001)가 고안한 검증된 방법으로, 심박수 측정 없이도 운동량을 수치화할 수 있어요.

**RPE(운동 자각도) 척도:**
| RPE | 느낌 | 해당 운동 강도 |
|-----|------|----------------|
| 1~2 | 매우 쉬움 | 가볍게 걷기, 스트레칭 |
| 3~4 | 쉬움 | 평지 걷기, 요가 |
| 5~6 | 보통 | 빠르게 걷기, 자전거 |
| 7~8 | 힘듦 | 조깅, 등산 |
| 9~10 | 매우 힘듦 | 전력 달리기, 줄넘기 |

> 운동 **직후가 아닌 15~30분 후**에 평가하는 게 가장 정확해요.
            """)

        st.write("")
        st.markdown("<p style='color:#475569;font-weight:600;font-size:14px;'>📋 운동 예시</p>",
                    unsafe_allow_html=True)

        # 강도별 추천 운동 (WHO 2020 + ACSM 2024 Compendium 기반)
        intensity_label = "저강도" if score < 50 else ("고강도" if score >= 80 and zone == "부족" else "중강도")
        exercises = EXERCISE_DB[intensity_label]

        for ex in exercises:
            # 목표 세션부하 → RPE 역산으로 권장 시간 계산
            # RPE ≈ MET * 0.7 (근사)
            rpe_approx = max(1, int(ex["met"] * 0.7))
            mins = max(5, target // rpe_approx) if rpe_approx > 0 else 30
            # MET-min
            met_min = int(ex["met"] * mins)
            st.markdown(
                f"<div style='background:#F8FAFF;border:1px solid #CBD5E1;"
                f"border-radius:10px;padding:8px 14px;margin:5px 0;"
                f"display:flex;justify-content:space-between;align-items:center;'>"
                f"<span style='font-size:14px;color:#1e293b;'>{ex['emoji']} {ex['name']}</span>"
                f"<span style='color:#2563EB;font-weight:700;font-size:13px;'>약 {mins}분"
                f"<span style='color:#94a3b8;font-weight:400;'> · {met_min} MET-min</span></span>"
                f"</div>", unsafe_allow_html=True)

        st.markdown(
            f"<p style='color:#94a3b8;font-size:11px;margin-top:6px;'>"
            f"📚 WHO 2020 가이드라인: 중강도 150~300분/주 또는 고강도 75~150분/주 권장 "
            f"· ACSM 2024 Compendium MET 값 기준</p>",
            unsafe_allow_html=True)

        st.write("")
        if st.button("✅ 운동 완료 기록하기", type="primary", key="go_workout_log"):
            st.session_state["page"] = "workout_log"
            st.rerun()


# ──────────────────────────────────────────
#  기록 탭
# ──────────────────────────────────────────
def _show_history():
    st.markdown("#### 📈 활동 기록")
    st.write("")

    # 연속 달성 + 평균 REM
    col1, col2 = st.columns(2)
    hist = st.session_state["user_history"]
    with col1:
        with st.container(border=True):
            st.metric("🔥 연속 달성", f"{st.session_state['streak']}일")
    with col2:
        with st.container(border=True):
            avg_rem = f"{np.mean(hist['rem']):.1f}%" if hist["rem"] else "-"
            st.metric("💤 평균 REM", avg_rem)

    st.write("")

    # 나만의 MET 기준 (기존 설정 탭에 있던 것)
    with st.container(border=True):
        st.markdown("**🏃 나만의 MET 기준**")
        st.markdown(
            "<p style='color:#94a3b8;font-size:12px;'>Fitbit 데이터(유저 1503960366, 30일)에서 "
            "산출한 운동 강도별 일평균 MET-min 베이스라인이에요.</p>",
            unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("전체 포함",    f"{BASELINE_MET_ALL}", help="저강도 이상 모든 활동 포함")
        with col2: st.metric("중강도↑ (3+)", f"{BASELINE_MET_3_0}", help="MET 3.0 이상 활동만")
        with col3: st.metric("고강도↑ (6+)", f"{BASELINE_MET_6_0}", help="MET 6.0 이상 활동만")
        st.markdown(
            f"<p style='color:#2563EB;font-size:12px;'>현재 내 베이스라인: "
            f"<b>{st.session_state['baseline_met']} RPE-min</b> (피드백으로 자동 조정됨)</p>",
            unsafe_allow_html=True)

    st.write("")

    # 수면 데이터 이력
    with st.container(border=True):
        st.markdown("**💤 수면 데이터 이력**")
        if hist["rem"]:
            for i, (r, d, h) in enumerate(zip(hist["rem"], hist["deep"], hist["hr"]), 1):
                st.markdown(
                    f"<p style='color:#64748b;font-size:13px;border-bottom:1px solid #F1F5F9;padding:6px 0;'>"
                    f"#{i} &nbsp; REM {r:.0f}% &nbsp;·&nbsp; 깊은수면 {d:.0f}% &nbsp;·&nbsp; 안정심박이하 {h:.0f}%"
                    f"</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#94a3b8;'>상세 입력을 하면 여기에 기록이 쌓여요.</p>",
                        unsafe_allow_html=True)

    st.write("")

    # 세션 부하 이력
    with st.container(border=True):
        st.markdown("**🏋️ 세션 부하 이력**")
        logs = st.session_state["session_logs"]
        if logs:
            # 주간 MET-min 합계
            current_day   = st.session_state["streak"]
            weekly_met    = sum(l.get("met_min", 0) for l in logs if current_day - l["day"] < 7)
            weekly_load   = sum(l["load"] for l in logs if current_day - l["day"] < 7)
            st.markdown(
                f"<p style='color:#2563EB;font-size:13px;font-weight:600;'>"
                f"이번 주 누적: {weekly_load} RPE-min &nbsp;·&nbsp; ≈ {weekly_met} MET-min"
                f"<span style='color:#94a3b8;font-weight:400;'> / WHO 권장 600</span></p>",
                unsafe_allow_html=True)
            st.progress(min(weekly_met / WHO_MET_MIN_WEEK, 1.0))
            st.write("")
            for l in reversed(logs[-10:]):
                met_str = f" &nbsp;·&nbsp; ≈ <b>{l.get('met_min','?')}</b> MET-min" if "met_min" in l else ""
                rpe_str = f" &nbsp;·&nbsp; RPE {l['rpe']} × {l['duration']}분" if "rpe" in l else ""
                st.markdown(
                    f"<p style='color:#64748b;font-size:13px;border-bottom:1px solid #F1F5F9;padding:6px 0;'>"
                    f"Day {l['day']}{rpe_str} &nbsp;·&nbsp; "
                    f"<b style='color:#2563EB;'>{l['load']}</b> RPE-min{met_str}"
                    f"</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#94a3b8;'>운동 완료 기록을 하면 여기에 쌓여요.</p>",
                        unsafe_allow_html=True)


# ──────────────────────────────────────────
#  설정 탭
# ──────────────────────────────────────────
def _show_settings():
    st.markdown("#### ⚙️ 설정")
    st.write("")

    with st.container(border=True):
        st.markdown("**디바이스**")
        new_watch = st.toggle("스마트워치 연동", value=st.session_state["use_watch"])
        if new_watch != st.session_state["use_watch"]:
            st.session_state["use_watch"] = new_watch
            st.rerun()

    st.write("")
    with st.container(border=True):
        st.markdown("**앱 정보**")
        st.markdown("""
<p style='color:#94a3b8;font-size:12px;'>
🌙 <b>잘쉼</b> — 수면 기반 운동 처방 앱<br><br>
📚 사용 근거:<br>
· Foster et al. (2001) — Session RPE 훈련 부하 계산법<br>
· Gabbett (2016, BJSM) — ACWR 부상 위험 구간<br>
· WHO 2020 신체활동 가이드라인 — 주간 운동 권장량<br>
· ACSM 2024 Compendium — 운동 종목별 MET 값
</p>
        """, unsafe_allow_html=True)

    st.write("")
    with st.container(border=True):
        st.markdown("**초기화**")
        if st.button("⚠️ 처음부터 다시 시작", type="secondary"):
            # JSON 파일 삭제
            if os.path.exists(USER_DATA_PATH):
                os.remove(USER_DATA_PATH)
            # 세션 상태 전체 초기화
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ──────────────────────────────────────────
#  운동 기록 페이지
# ──────────────────────────────────────────
def show_workout_log():
    day      = st.session_state["streak"]
    baseline = st.session_state["baseline_met"]

    # 헤더
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 뒤로"):
            st.session_state["page"] = "main"
            st.rerun()
    with col2:
        st.markdown("<h3 style='margin:0; padding-top:4px;'>✅ 운동 기록</h3>",
                    unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#CBD5E1; margin: 8px 0 16px;'>", unsafe_allow_html=True)

    # ── 운동 유형 탭 ──
    t_cardio, t_strength, t_recovery = st.tabs(["🏃 유산소", "🏋️ 근력", "🧘 유연성·회복"])

    entries = []   # 기록된 운동 목록 (여러 개 가능)

    # ════════ 유산소 ════════
    with t_cardio:
        st.write("")
        ex_names = [f"{e['emoji']} {e['name']}" for e in EXERCISE_DB["중강도"] + EXERCISE_DB["고강도"]]
        selected = st.selectbox("운동 종목", ["직접 입력"] + ex_names, key="cardio_ex")
        if selected == "직접 입력":
            custom = st.text_input("종목 이름", placeholder="예: 배드민턴, 줄넘기 ...", key="cardio_custom")
            ex_name = custom if custom else "기타 유산소"
            ex_met  = 5.0
        else:
            ex_name = selected
            all_ex  = EXERCISE_DB["중강도"] + EXERCISE_DB["고강도"]
            ex_met  = next((e["met"] for e in all_ex if f"{e['emoji']} {e['name']}" == selected), 5.0)

        col1, col2 = st.columns(2)
        with col1:
            c_duration = st.number_input("운동 시간 (분)", 1, 300, 30, 5, key="c_dur")
        with col2:
            c_rpe = st.slider("전체 강도 (RPE)", 1, 10, 5, key="c_rpe",
                              help="운동 끝나고 15~30분 후 평가 · 1=매우 쉬움 ~ 10=최대 강도")

        c_met_approx = rpe_to_met(c_rpe)
        c_met_min    = int(ex_met * c_duration)
        c_load       = c_duration * c_rpe

        st.markdown(
            f"<div style='background:#EFF6FF;border-radius:10px;padding:10px 14px;margin-top:8px;'>"
            f"<span style='color:#2563EB;font-weight:700;'>{ex_name}</span>"
            f"<p style='color:#475569;font-size:13px;margin:4px 0 0;'>"
            f"⏱ {c_duration}분 &nbsp;·&nbsp; RPE {c_rpe} &nbsp;·&nbsp; "
            f"세션 부하 <b>{c_load} RPE-min</b> &nbsp;·&nbsp; "
            f"≈ <b>{c_met_min} MET-min</b> (MET {ex_met} 기준)"
            f"</p></div>", unsafe_allow_html=True)

        if st.button("➕ 유산소 추가", key="add_cardio"):
            entries.append({
                "type": "유산소", "name": ex_name,
                "duration": c_duration, "rpe": c_rpe,
                "load": c_load, "met_min": c_met_min, "met": ex_met,
            })
            st.toast(f"{ex_name} 추가됨!", icon="✅")

    # ════════ 근력 ════════
    with t_strength:
        st.write("")
        strength_options = [
            "🏋️ 웨이트 (머신)", "🏋️ 웨이트 (프리웨이트)", "💪 맨몸 운동 (푸시업·스쿼트 등)",
            "🤸 케틀벨", "직접 입력"
        ]
        s_selected = st.selectbox("운동 종목", strength_options, key="str_ex")
        if s_selected == "직접 입력":
            s_name = st.text_input("종목 이름", placeholder="예: 데드리프트, 벤치프레스 ...", key="str_custom")
            s_name = s_name if s_name else "기타 근력"
        else:
            s_name = s_selected

        col1, col2, col3 = st.columns(3)
        with col1: s_sets = st.number_input("세트 수", 1, 20, 3, 1, key="s_sets")
        with col2: s_reps = st.number_input("세트당 반복 수", 1, 50, 10, 1, key="s_reps")
        with col3: s_weight = st.number_input("무게 (kg, 맨몸=0)", 0, 500, 0, 5, key="s_weight")

        s_duration = st.number_input("총 운동 시간 (분, 휴식 포함)", 1, 180, 45, 5, key="s_dur")
        s_rpe = st.slider("전체 강도 (RPE)", 1, 10, 6, key="s_rpe",
                          help="모든 세트 끝난 후 15~30분 뒤 전체 강도를 평가해주세요.")

        s_met     = 5.0   # 웨이트 트레이닝 기준 MET (ACSM 2024)
        s_met_min = int(s_met * s_duration)
        s_load    = s_duration * s_rpe
        weight_str = f"{s_weight}kg" if s_weight > 0 else "맨몸"

        st.markdown(
            f"<div style='background:#EFF6FF;border-radius:10px;padding:10px 14px;margin-top:8px;'>"
            f"<span style='color:#2563EB;font-weight:700;'>{s_name}</span>"
            f"<p style='color:#475569;font-size:13px;margin:4px 0 0;'>"
            f"{s_sets}세트 × {s_reps}회 · {weight_str} &nbsp;·&nbsp; ⏱ {s_duration}분 &nbsp;·&nbsp; RPE {s_rpe}"
            f"<br>세션 부하 <b>{s_load} RPE-min</b> &nbsp;·&nbsp; ≈ <b>{s_met_min} MET-min</b>"
            f"</p></div>", unsafe_allow_html=True)

        if st.button("➕ 근력 추가", key="add_strength"):
            entries.append({
                "type": "근력", "name": s_name,
                "duration": s_duration, "rpe": s_rpe,
                "load": s_load, "met_min": s_met_min, "met": s_met,
                "sets": s_sets, "reps": s_reps, "weight": s_weight,
            })
            st.toast(f"{s_name} 추가됨!", icon="✅")

    # ════════ 유연성·회복 ════════
    with t_recovery:
        st.write("")
        recovery_options = [
            "🧘 요가", "🤸 스트레칭", "🛁 냉온욕", "🚶 가벼운 산책", "직접 입력"
        ]
        r_selected = st.selectbox("종류", recovery_options, key="rec_ex")
        if r_selected == "직접 입력":
            r_name = st.text_input("종류 이름", key="rec_custom")
            r_name = r_name if r_name else "기타 회복"
        else:
            r_name = r_selected

        r_duration = st.number_input("시간 (분)", 1, 120, 20, 5, key="r_dur")
        r_rpe      = st.slider("전체 강도 (RPE)", 1, 5, 2, key="r_rpe",
                               help="회복 운동은 보통 1~3 사이로 낮아요.")
        r_met      = 2.5
        r_met_min  = int(r_met * r_duration)
        r_load     = r_duration * r_rpe

        st.markdown(
            f"<div style='background:#EFF6FF;border-radius:10px;padding:10px 14px;margin-top:8px;'>"
            f"<span style='color:#2563EB;font-weight:700;'>{r_name}</span>"
            f"<p style='color:#475569;font-size:13px;margin:4px 0 0;'>"
            f"⏱ {r_duration}분 &nbsp;·&nbsp; RPE {r_rpe} &nbsp;·&nbsp; "
            f"≈ <b>{r_met_min} MET-min</b>"
            f"</p></div>", unsafe_allow_html=True)

        if st.button("➕ 회복 추가", key="add_recovery"):
            entries.append({
                "type": "회복", "name": r_name,
                "duration": r_duration, "rpe": r_rpe,
                "load": r_load, "met_min": r_met_min, "met": r_met,
            })
            st.toast(f"{r_name} 추가됨!", icon="✅")

    st.write("")

    # ── 세션 메모 + 전체 피드백 ──
    with st.container(border=True):
        st.markdown("#### 📝 오늘 운동 총평")
        notes = st.text_area("메모 (선택)", placeholder="컨디션, 특이사항, 부위 피로감 등을 자유롭게 적어보세요.",
                             height=80, key="workout_notes")
        st.write("")

        # 대표 RPE — 입력된 운동들의 최대 RPE 또는 직접 입력
        overall_rpe = st.slider(
            "오늘 전체 운동 강도 (RPE)", 1, 10, 5, key="overall_rpe",
            help="모든 운동을 합쳐서 오늘 하루 전체 강도를 평가해주세요. (15~30분 후 권장)")

        st.write("")
        st.markdown("<p style='color:#64748b;font-size:13px;font-weight:600;'>오늘 운동 어떠셨나요?</p>",
                    unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        feedback = None
        with col1:
            if st.button("😰 너무 힘들었어", key="fb_hard"): feedback = "hard"
        with col2:
            if st.button("👍 딱 적당했어",   key="fb_ok"):   feedback = "ok"
        with col3:
            if st.button("💪 너무 쉬웠어",   key="fb_easy"): feedback = "easy"

        if feedback:
            # 총 세션 부하 계산 (entries 합산 OR overall_rpe 기반)
            if entries:
                total_load    = sum(e["load"]    for e in entries)
                total_met_min = sum(e["met_min"] for e in entries)
                total_dur     = sum(e["duration"] for e in entries)
            else:
                # entries 없이 바로 피드백만 누른 경우 → overall_rpe로 추정
                total_dur     = 30
                total_load    = total_dur * overall_rpe
                total_met_min = int(rpe_to_met(overall_rpe) * total_dur)

            adj = {"hard": 0.95, "ok": 1.0, "easy": 1.05}[feedback]
            st.session_state["baseline_met"] = int(baseline * adj)
            st.session_state["session_logs"].append({
                "day":      day,
                "load":     total_load,
                "met_min":  total_met_min,
                "rpe":      overall_rpe,
                "duration": total_dur,
                "entries":  entries,
                "notes":    notes,
                "feedback": feedback,
            })
            st.session_state["streak"]     += 1
            st.session_state["sleep_score"] = None
            st.session_state["page"]        = "main"
            save_user_data()
            msg = {"hard":"베이스라인을 살짝 낮췄어요 📉","ok":"딱 맞는 강도네요! 유지할게요 👍","easy":"베이스라인을 올렸어요 📈"}[feedback]
            st.toast(f"{msg} 🔥", icon="🔥")
            st.rerun()


# ──────────────────────────────────────────
#  라우터
# ──────────────────────────────────────────
if st.session_state["step"] != -1:
    show_onboarding()
elif st.session_state.get("page") == "workout_log":
    show_workout_log()
else:
    show_main()
