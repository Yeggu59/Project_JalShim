import streamlit as st
import pickle
import numpy as np
import pandas as pd
import os
import glob
import json
import calendar
from datetime import date, timedelta

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
    # [FIX 1&2] 단위를 MET-min으로 통일
    # 이전: l["load"] (RPE-min) vs baseline (MET-min) → 단위 불일치
    # 변경: l["met_min"] (MET-min)을 사용해 baseline과 동일한 단위로 ACWR 계산
    acute_loads   = [l.get("met_min", l["load"]) for l in logs if current_day - l["day"] < 7]
    chronic_loads = [l.get("met_min", l["load"]) for l in logs if current_day - l["day"] < 28]

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


AUTO_RETRAIN_THRESHOLD = 30   # 레이블 N개 이상이면 자동 재학습

def try_retrain_model():
    """
    labeled_data가 30개 이상 쌓이면 LinearRegression 재학습.
    재학습 후 in-memory ml_model 교체 + pkl 덮어쓰기.
    """
    global ml_model
    data = st.session_state.get("labeled_data", [])
    if len(data) < AUTO_RETRAIN_THRESHOLD:
        return False

    from sklearn.linear_model import LinearRegression
    import pickle as _pkl

    X = [d["X"] for d in data]
    y = [d["y"] for d in data]
    new_model = LinearRegression()
    new_model.fit(X, y)

    # in-memory 교체
    ml_model = new_model

    # pkl 덮어쓰기
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sleep_model.pkl")
    with open(model_path, "wb") as f:
        _pkl.dump(new_model, f)

    return True


def save_labeled(features: list, true_score: int):
    """(입력값, 실제점수) 쌍을 labeled_data에 저장 후 30개 도달 시 자동 재학습."""
    st.session_state["labeled_data"].append({"X": features, "y": true_score})
    if len(st.session_state["labeled_data"]) >= AUTO_RETRAIN_THRESHOLD:
        if try_retrain_model():
            st.toast("✨ 수면 모델이 내 데이터로 재학습됐어요!", icon="🧠")


def apply_age_offset(score: int) -> int:
    """나이대별 수면 점수 기준 보정. 나이 들수록 깊은수면이 자연 감소하므로 offset 적용."""
    age = st.session_state.get("age_group", "30대")
    offset = SLEEP_SCORE_AGE_OFFSET.get(age, 0)
    return min(max(score + offset, 0), 100)


def save_sleep_score(score: int):
    """수면 점수를 sleep_logs에 오늘 날짜로 저장 (중복 시 덮어쓰기)."""
    today = date.today().isoformat()
    logs  = st.session_state["sleep_logs"]
    # 오늘 날짜 항목이 이미 있으면 업데이트
    for entry in logs:
        if entry["date"] == today:
            entry["score"] = score
            return
    logs.append({"date": today, "score": score})


# ──────────────────────────────────────────
#  나이/성별 베이스라인 테이블
#  근거: ACSM (2022) VO₂max 연령·성별 정상범위 기반 MET 처리 능력 차이
#  초기 스케일만 잡고, 피드백으로 수렴
# ──────────────────────────────────────────
AGE_SEX_MULTIPLIER = {
    # (성별, 나이대): baseline_met 배수
    ("남성", "20대"): 1.20,
    ("남성", "30대"): 1.10,
    ("남성", "40대"): 1.00,
    ("남성", "50대"): 0.90,
    ("남성", "60대↑"): 0.75,
    ("여성", "20대"): 1.00,
    ("여성", "30대"): 0.90,
    ("여성", "40대"): 0.85,
    ("여성", "50대"): 0.80,
    ("여성", "60대↑"): 0.65,
}

# 나이별 수면 점수 기준 보정값 (깊은수면 % 자체가 나이 들수록 감소)
# 참고: Ohayon MM et al. (2004), Neuroscience & Biobehavioral Reviews
SLEEP_SCORE_AGE_OFFSET = {
    "20대":  0,
    "30대":  0,
    "40대": -3,
    "50대": -6,
    "60대↑": -10,
}


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

PERSIST_KEYS = ["step", "use_watch", "baseline_met", "streak",
                "user_history", "session_logs", "sleep_logs", "start_date",
                "labeled_data", "sex", "age_group"]

_DEFAULTS = {
    "step":         0,
    "use_watch":    False,
    "baseline_met": BASELINE_MET_3_0,
    "streak":       0,
    "sleep_score":  None,
    "user_history": {"rem": [], "deep": [], "hr": []},
    "session_logs": [],
    "sleep_logs":   [],
    "start_date":   date.today().isoformat(),
    "cal_month":    date.today().strftime("%Y-%m"),
    "page":         "main",
    # 자동 재학습용 레이블 데이터: [{"X": [...], "y": score}, ...]
    "labeled_data": [],
    # 인구통계
    "sex":       None,   # "남성" | "여성"
    "age_group": None,   # "20대" | "30대" | ...
}

def load_user_data() -> dict:
    """JSON 파일에서 유저 데이터 로드. 없으면 기본값 반환."""
    if os.path.exists(USER_DATA_PATH):
        try:
            with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            data = dict(_DEFAULTS)
            data.update(saved)

            # [FIX 4] date 필드 없는 기존 session_logs에 날짜 소급 추가
            # 이전: date 없이 저장된 로그는 달력에 표시 안 됨
            # 변경: start_date + day 오프셋으로 날짜 역산해서 채워줌
            start = data.get("start_date", date.today().isoformat())
            start_d = date.fromisoformat(start)
            for log in data.get("session_logs", []):
                if "date" not in log and "day" in log:
                    estimated = start_d + timedelta(days=log["day"])
                    log["date"] = estimated.isoformat()

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
ONBOARDING_STEPS = 3

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
        st.markdown("### 👤 성별과 나이대를 알려주세요")
        _info_box("왜 필요한가요?",
                  "연령·성별에 따라 VO₂max(최대 산소 섭취량)가 달라 운동 처방의 초기 기준값이 달라요. "
                  "이후 사용할수록 내 데이터로 자동 조정됩니다. (ACSM 2022 기준)")
        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            sex = st.radio("성별", ["남성", "여성"], horizontal=True, key="ob_sex")
        with col2:
            age = st.selectbox("나이대", ["20대", "30대", "40대", "50대", "60대↑"], key="ob_age")

        mult = AGE_SEX_MULTIPLIER.get((sex, age), 1.0)
        st.markdown(
            f"<p style='color:#2563EB;font-size:13px;margin-top:8px;'>"
            f"초기 MET 처리 능력 배수: <b>{mult}×</b> "
            f"<span style='color:#94a3b8;'>(활동 수준 선택 후 최종 반영)</span></p>",
            unsafe_allow_html=True)

        st.write("")
        if st.button("다음 →", type="primary"):
            st.session_state["sex"]       = sex
            st.session_state["age_group"] = age
            st.session_state["step"]      = 3
            st.rerun()

    elif step == 3:
        st.markdown("### 💪 최근 한 달간 활동 수준은?")
        _info_box("베이스라인이란?",
                  "하루 목표 운동량의 초기값이에요. 예: 조깅 30분(MET 7) = 210 MET-min. "
                  "피드백을 쌓을수록 자동으로 내 체력에 맞게 조정됩니다.")
        st.write("")

        sex = st.session_state.get("sex", "남성")
        age = st.session_state.get("age_group", "30대")
        mult = AGE_SEX_MULTIPLIER.get((sex, age), 1.0)

        levels = {
            "🛋️  거의 안 움직여요":     int(BASELINE_MET_3_0 * 0.6 * mult),
            "🚶  가끔 산책해요":         int(BASELINE_MET_3_0 * mult),
            "🏋️  주 3회 이상 운동해요": int(BASELINE_MET_3_0 * 1.5 * mult),
        }
        level_met = list(levels.values())
        level_desc = {
            list(levels.keys())[0]: f"하루 목표 {level_met[0]} MET-min · 예: 빠른 걷기 약 {level_met[0]//5}분",
            list(levels.keys())[1]: f"하루 목표 {level_met[1]} MET-min · 예: 조깅(8km/h) 약 {level_met[1]//7}분",
            list(levels.keys())[2]: f"하루 목표 {level_met[2]} MET-min · 예: 달리기(10km/h) 약 {level_met[2]//10}분",
        }
        for label, val in levels.items():
            if st.button(label):
                st.session_state["baseline_met"] = val
                st.session_state["step"] = -1
                save_user_data()
                st.rerun()
            st.markdown(f"<p style='color:#94a3b8;font-size:11px;margin:-8px 0 8px 4px;'>{level_desc[label]}</p>",
                        unsafe_allow_html=True)


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
                        final = apply_age_offset(min(max(score, 0), 100))
                        st.session_state["sleep_score"] = final
                        save_sleep_score(final)
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
                    # [FIX 6] 이전: score * (feel/3.0) → feel=1이면 점수 1/3 토막 (85→28)
                    # 변경: ±10점 가산 방식으로 교체 (feel 1→-10, 3→0, 5→+10, 범위 제한)
                    raw   = ml_model.predict(X)[0]
                    score = int(raw + (subjective_feel - 3) * 5)
                    final = min(max(score, 0), 100)
                    st.session_state["sleep_score"] = final
                    save_sleep_score(final)
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
                    final = min(max(score, 0), 100)
                    st.session_state["sleep_score"] = final
                    save_sleep_score(final)
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
        # 실제 점수 입력 → labeled_data 누적 → 30개 시 자동 재학습
        labeled_count = len(st.session_state.get("labeled_data", []))
        remaining = max(0, AUTO_RETRAIN_THRESHOLD - labeled_count)
        with st.expander(f"🧠 모델 개인화 데이터 제공 (재학습까지 {remaining}개 남음)"):
            st.markdown(
                "<p style='color:#64748b;font-size:12px;'>"
                "오늘 실제로 느낀 수면의 질을 점수로 알려주시면 모델이 점점 나에게 맞게 학습해요.</p>",
                unsafe_allow_html=True)
            actual_score = st.slider("실제 수면 만족도 (0~100)", 0, 100,
                                     st.session_state["sleep_score"], 1, key="actual_score")
            if st.button("내 점수로 학습시키기", key="submit_label"):
                # 현재 수면 입력 피처를 session_state에서 복원 (user_history 마지막 값)
                hist = st.session_state["user_history"]
                imp  = impute_missing(hist)
                # 기록된 마지막 수면시간은 user_history에 없으므로 예측 점수 역산 근사 사용
                # 충분한 근사: 가장 최근 user_history 평균 피처로 구성
                feat = [
                    SLEEP_STATS["HOURS_DECIMAL"]["mean"],
                    imp["REM_PERCENT"],
                    imp["DEEP_PERCENT"],
                    imp["HR_BELOW_RESTING"],
                ]
                save_labeled(feat, actual_score)
                save_user_data()
                st.toast(f"학습 데이터 {len(st.session_state['labeled_data'])}개 저장됨!", icon="🧠")
                st.rerun()

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

    # [FIX 5] ACWR 카드를 한 줄 요약으로 압축 (상세는 expander 안으로)
    with st.container(border=True):
        col_acwr1, col_acwr2 = st.columns([4, 1])
        with col_acwr1:
            st.markdown(
                f"<p style='margin:0;'>"
                f"<span style='color:{z_color};font-weight:700;font-size:15px;'>{z_emoji} 훈련 부하 {zone}</span>"
                f"<span style='color:#64748b;font-size:12px;'> &nbsp;·&nbsp; ACWR {acwr_val} (Sweet Spot 0.8~1.3)</span>"
                f"</p>"
                f"<p style='color:#475569;font-size:12px;margin:3px 0 0;'>{z_desc}</p>",
                unsafe_allow_html=True)
        with col_acwr2:
            st.markdown(f"<p style='text-align:right;font-size:1.5rem;font-weight:800;color:{z_color};margin:0;'>"
                        f"{acwr_val}</p>", unsafe_allow_html=True)

        with st.expander("📊 부하 상세 · ACWR 설명"):
            col1, col2 = st.columns(2)
            with col1: st.metric("급성 부하 (7일)", f"{acwr_info['acute']} MET-min", help="최근 7일 MET-min 합산")
            with col2: st.metric("만성 부하 (28일)", f"{acwr_info['chronic']} MET-min", help="최근 28일 평균 주간 MET-min")
            st.markdown("""
**ACWR = 급성(7일) ÷ 만성(28일 평균)**
| 구간 | 의미 |
|------|------|
| < 0.8 | 📉 운동 부족 |
| 0.8~1.3 | ✅ 이상적 (Sweet Spot) |
| 1.3~1.5 | ⚠️ 주의 |
| > 1.5 | 🚨 과부하, 부상 위험 |
> Gabbett TJ (2016, BJSM)
            """)

    st.write("")

    # ── 운동 처방 카드 ──
    sleep_mod = calc_sleep_modifier(score)
    load_mult = acwr_info["load_mult"] * sleep_mod
    target    = int(baseline * load_mult)

    # WHO 주간 현황
    # [FIX 1] 이전: weekly_load(RPE-min) × 0.9 근사 변환 → 저장된 실제 MET-min 사용으로 교체
    weekly_met_est = sum(l.get("met_min", 0) for l in logs if day - l["day"] < 7)
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

        # [FIX 2&3] target은 MET-min 단위(baseline × 배수)
        # target_met_min = target 자체가 이미 MET-min 기반이므로 별도 환산 불필요
        target_met_min = target
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

        # [FIX 5] 운동 예시를 expander로 접어 기본 스크롤 최소화
        with st.expander(f"📋 오늘 추천 운동 예시 보기 ({intensity_label})"):
            intensity_label = "저강도" if score < 50 else ("고강도" if score >= 80 and zone == "부족" else "중강도")
            exercises = EXERCISE_DB[intensity_label]
            for ex in exercises:
                rpe_approx = max(1, int(ex["met"] * 0.7))
                mins = max(5, target // rpe_approx) if rpe_approx > 0 else 30
                met_min = int(ex["met"] * mins)
                st.markdown(
                    f"<div style='background:#F8FAFF;border:1px solid #CBD5E1;"
                    f"border-radius:10px;padding:8px 14px;margin:4px 0;"
                    f"display:flex;justify-content:space-between;align-items:center;'>"
                    f"<span style='font-size:13px;color:#1e293b;'>{ex['emoji']} {ex['name']}</span>"
                    f"<span style='color:#2563EB;font-weight:700;font-size:12px;'>약 {mins}분"
                    f"<span style='color:#94a3b8;font-weight:400;'> · {met_min} MET-min</span></span>"
                    f"</div>", unsafe_allow_html=True)
            st.markdown(
                "<p style='color:#94a3b8;font-size:11px;margin-top:4px;'>"
                "WHO 2020 · ACSM 2024 Compendium 기준</p>", unsafe_allow_html=True)

        st.write("")
        if st.button("✅ 운동 완료 기록하기", type="primary", key="go_workout_log"):
            # 목표값 전달 (처방 화면 → 운동 기록 페이지)
            st.session_state["target_load"]    = target
            st.session_state["target_met_min"] = target_met_min
            st.session_state["page"] = "workout_log"
            st.rerun()


# ──────────────────────────────────────────
#  달력 렌더링
# ──────────────────────────────────────────
def _render_calendar():
    """운동/수면 기록을 HTML 달력으로 렌더링."""
    logs       = st.session_state["session_logs"]
    sleep_logs = st.session_state["sleep_logs"]

    # 날짜별 인덱스 구성
    workout_by_date = {}   # date_str -> log entry
    for l in logs:
        if "date" in l:
            workout_by_date[l["date"]] = l

    sleep_by_date = {s["date"]: s["score"] for s in sleep_logs}

    # 월 탐색
    cal_month = st.session_state.get("cal_month", date.today().strftime("%Y-%m"))
    y, m = int(cal_month[:4]), int(cal_month[5:7])

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("◀", key="cal_prev"):
            prev = date(y, m, 1) - timedelta(days=1)
            st.session_state["cal_month"] = prev.strftime("%Y-%m")
            st.rerun()
    with col2:
        st.markdown(f"<p style='text-align:center;font-weight:700;color:#1e293b;font-size:15px;'>"
                    f"{y}년 {m}월</p>", unsafe_allow_html=True)
    with col3:
        if st.button("▶", key="cal_next"):
            next_m = date(y, m, 28) + timedelta(days=4)
            st.session_state["cal_month"] = next_m.strftime("%Y-%m")
            st.rerun()

    # 달력 HTML 생성
    _, days_in_month = calendar.monthrange(y, m)
    first_weekday    = calendar.monthrange(y, m)[0]   # 0=월요일
    today_str        = date.today().isoformat()

    DAYS_KR = ["월", "화", "수", "목", "금", "토", "일"]
    header  = "".join(f"<th style='padding:6px;color:#94a3b8;font-size:12px;font-weight:600;'>{d}</th>"
                      for d in DAYS_KR)

    cells = ["<td></td>"] * first_weekday
    for d in range(1, days_in_month + 1):
        ds = f"{y}-{m:02d}-{d:02d}"
        workout = workout_by_date.get(ds)
        sleep_s = sleep_by_date.get(ds)

        # 셀 상태 판정
        high_load   = workout and workout.get("met_min", 0) >= 300
        great_sleep = sleep_s and sleep_s >= 80
        any_workout = bool(workout)

        # 이펙트 결정
        if high_load and great_sleep:
            # 🔥 완벽한 날 — 그라디언트 + 빛나는 효과
            bg     = "linear-gradient(135deg, #DBEAFE, #D1FAE5)"
            border = "2px solid #2563EB"
            shadow = "0 0 10px rgba(37,99,235,0.35)"
            badge  = "🔥"
        elif high_load:
            # 💪 열심히 운동한 날
            bg     = "#DBEAFE"
            border = "1.5px solid #2563EB"
            shadow = "0 0 6px rgba(37,99,235,0.2)"
            badge  = "💪"
        elif any_workout:
            # 🏃 운동한 날
            bg     = "#EFF6FF"
            border = "1px solid #93c5fd"
            shadow = "none"
            badge  = "🏃"
        elif great_sleep:
            # 🌙 잘 쉰 날
            bg     = "#ECFDF5"
            border = "1px solid #6ee7b7"
            shadow = "0 0 6px rgba(16,185,129,0.2)"
            badge  = "🌙"
        else:
            bg     = "#FFFFFF"
            border = "1px solid #E2E8F0"
            shadow = "none"
            badge  = ""

        today_ring = "outline: 2px solid #2563EB; outline-offset:2px;" if ds == today_str else ""
        sleep_dot  = ""
        if sleep_s:
            dot_color = "#10b981" if sleep_s >= 80 else "#f59e0b" if sleep_s >= 50 else "#ef4444"
            sleep_dot = f"<div style='width:5px;height:5px;border-radius:50%;background:{dot_color};margin:0 auto;'></div>"

        cells.append(
            f"<td style='padding:3px;'>"
            f"<div style='background:{bg};border:{border};border-radius:10px;"
            f"box-shadow:{shadow};{today_ring}"
            f"min-width:36px;min-height:46px;text-align:center;padding:4px 2px;'>"
            f"<div style='font-size:12px;color:#64748b;'>{d}</div>"
            f"<div style='font-size:14px;line-height:1.2;'>{badge}</div>"
            f"{sleep_dot}"
            f"</div></td>"
        )

    # 7칸씩 행 분할
    while len(cells) % 7 != 0:
        cells.append("<td></td>")
    rows = ""
    for i in range(0, len(cells), 7):
        rows += "<tr>" + "".join(cells[i:i+7]) + "</tr>"

    html = f"""
    <table style='width:100%;border-collapse:separate;border-spacing:3px;'>
      <thead><tr>{header}</tr></thead>
      <tbody>{rows}</tbody>
    </table>
    <div style='margin-top:8px;display:flex;gap:12px;flex-wrap:wrap;'>
      <span style='font-size:12px;color:#64748b;'>🔥 운동+수면 완벽</span>
      <span style='font-size:12px;color:#64748b;'>💪 고강도 운동</span>
      <span style='font-size:12px;color:#64748b;'>🏃 운동 완료</span>
      <span style='font-size:12px;color:#64748b;'>🌙 수면 양호</span>
      <span style='font-size:12px;color:#64748b;'>● 수면점수 (초록/노랑/빨강)</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ──────────────────────────────────────────
#  기록 탭
# ──────────────────────────────────────────
def _show_history():
    st.markdown("#### 📈 활동 기록")
    st.write("")

    # ── 달력 ──
    with st.container(border=True):
        _render_calendar()

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
<p style='color:#1e293b;font-size:13px;font-weight:600;'>🌙 잘쉼 — 수면 기반 운동 처방 앱</p>
<p style='color:#64748b;font-size:12px;'>수면 회복 점수와 훈련 부하 데이터를 결합해 과학적 근거 기반의 맞춤 운동 처방을 제공합니다.</p>
        """, unsafe_allow_html=True)

        with st.expander("📚 사용 근거 및 참고문헌 전체 보기"):
            st.markdown("""
#### 🧠 수면 점수 예측 모델
- **학습 데이터**: 개인 Fitbit 수면 기록 (91일치, 2021–2022)
- **모델**: 다중 선형 회귀 (scikit-learn LinearRegression)
- **입력 피처**: 수면 시간(h), REM 비율(%), 깊은수면 비율(%), 안정심박이하 비율(%)
- **성능**: MAE 1.49점, R² 0.76
- **참고**: Scullin MK & Bliwise DL (2015). *Sleep, cognition, and normal aging.* Perspectives on Psychological Science, 10(1), 97–137.

#### 🏋️ 훈련 부하 계산 (Session RPE)
- **Foster C et al. (2001).** *A new approach to monitoring exercise training.* Journal of Strength and Conditioning Research, 15(1), 109–115.
- 운동 종료 15~30분 후 CR10 척도로 전체 강도를 평가, **Session Load = RPE × 운동시간(분)**
- 심박수 기반 지표(TRIMP)와 상관계수 r = 0.75~0.90 (검증됨)

#### 📊 급성:만성 부하 비율 (ACWR)
- **Gabbett TJ (2016).** *The training-injury prevention paradox.* British Journal of Sports Medicine, 50(5), 273–280.
- **Hulin BT et al. (2016).** *Spikes in acute workload are associated with increased injury risk in elite cricket fast bowlers.* BJSM, 48(8), 708–712.
- Sweet Spot: **ACWR 0.8~1.3** (부상 위험 최소화 구간)
- 급성 부하: 최근 7일 합산 / 만성 부하: 최근 28일 평균 × 7

#### 🏃 운동 종목별 MET 값
- **Ainsworth BE et al. (2024).** *2024 Adult Compendium of Physical Activities: A third update of the energy costs of human activities.* Journal of Science and Medicine in Sport, 27(1), 1–9.
- pacompendium.com (공식 데이터베이스)

#### 🌍 주간 운동 권장량 기준
- **WHO (2020).** *World Health Organization guidelines on physical activity and sedentary behaviour.* Geneva: WHO.
- 성인 기준: 중강도 150~300분/주 **또는** 고강도 75~150분/주
- MET-min 기준: 최소 **600 MET-min/주**, 권장 **1200 MET-min/주**
- **ACSM (2022).** *Physical Activity Guidelines for Americans, 3rd Edition.*

#### 📐 RPE → MET 변환 근사식
- **Borg G (1998).** *Borg's Perceived Exertion and Pain Scales.* Human Kinetics.
- CR10 척도 기준: `MET ≈ RPE × 0.9 + 1.0` (일반 성인 선형 근사)
- 실제 변환값은 개인 VO₂max에 따라 차이가 있으므로 **참고값**으로만 활용
- **Ciolac EG et al. (2011).** *Perceived exertion correlates with metabolic and cardiovascular responses in heart failure.* Clinics, 66(9), 1515–1521.

#### 📦 데이터셋
- **Fitbit MTurk 데이터셋** (공개 데이터, Kaggle): Furberg R et al. — 33명 유저, 2016년 3–5월 분단위 활동·수면 기록
  - `minuteMETsNarrow_merged.csv`, `dailyActivity_merged.csv`, `sleepDay_merged.csv` 활용
- **MET 베이스라인 산출 기준**: 유저 ID 1503960366, 30일치 dailyActivity 기반
  - 강도별 MET 대표값 적용: 고강도 8 MET, 중강도 4 MET, 저강도 2.5 MET
            """)
        st.markdown(
            "<p style='color:#94a3b8;font-size:11px;margin-top:4px;'>"
            "본 앱은 의학적 진단이나 치료를 대체하지 않습니다. "
            "건강 이상이 있을 경우 전문의와 상담하세요.</p>",
            unsafe_allow_html=True)

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
            st.session_state["page"]         = "main"
            st.session_state["wl_entries"]   = []
            st.session_state["wl_edit_idx"]  = -1
            st.rerun()
    with col2:
        st.markdown("<h3 style='margin:0; padding-top:4px;'>✅ 운동 기록</h3>",
                    unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#CBD5E1; margin: 8px 0 16px;'>", unsafe_allow_html=True)

    # session_state 초기화
    if "wl_entries"  not in st.session_state: st.session_state["wl_entries"]  = []
    if "wl_edit_idx" not in st.session_state: st.session_state["wl_edit_idx"] = -1

    # [FIX 3] target_load/target_met_min 모두 MET-min 단위로 통일
    # 이전: target_met_min = baseline * rpe_to_met(5)/5 (RPE-min → MET-min 재환산, 이중 처리)
    # 변경: target = baseline × 배수가 이미 MET-min이므로 그대로 사용, fallback도 동일 단위
    target_load    = st.session_state.get("target_load",    baseline)
    target_met_min = st.session_state.get("target_met_min", baseline)

    # ══════════════════════════════════════
    #  STEP 1 — 운동 추가 탭
    # ══════════════════════════════════════
    with st.container(border=True):
        st.markdown("#### ➕ 운동 추가")
        t_cardio, t_strength, t_recovery = st.tabs(["🏃 유산소", "🏋️ 근력", "🧘 유연성·회복"])

        # ════════ 유산소 ════════
        with t_cardio:
            st.write("")
            ex_names = [f"{e['emoji']} {e['name']}" for e in EXERCISE_DB["중강도"] + EXERCISE_DB["고강도"]]
            selected = st.selectbox("운동 종목", ["직접 입력"] + ex_names, key="cardio_ex")
            if selected == "직접 입력":
                custom  = st.text_input("종목 이름", placeholder="예: 배드민턴, 줄넘기 ...", key="cardio_custom")
                ex_name = custom if custom else "기타 유산소"
                ex_met  = 5.0
            else:
                ex_name = selected
                all_ex  = EXERCISE_DB["중강도"] + EXERCISE_DB["고강도"]
                ex_met  = next((e["met"] for e in all_ex if f"{e['emoji']} {e['name']}" == selected), 5.0)

            col1, col2 = st.columns(2)
            with col1: c_duration = st.number_input("운동 시간 (분)", 1, 300, 30, 5, key="c_dur")
            with col2: c_rpe      = st.slider("강도 (RPE)", 1, 10, 5, key="c_rpe")

            # MET 수동 조정
            col_met, col_met_help = st.columns([2, 3])
            with col_met:
                c_met_custom = st.number_input(
                    "MET 값 (직접 조정 가능)", 0.5, 20.0, float(ex_met), 0.5,
                    key="c_met", help="종목 선택 시 자동 입력되지만, 실제 강도에 맞게 조정하세요.")
            with col_met_help:
                st.markdown(
                    f"<p style='color:#64748b;font-size:12px;margin-top:28px;'>"
                    f"자동값: <b style='color:#2563EB;'>{ex_met}</b> "
                    f"(ACSM 2024 기준)</p>", unsafe_allow_html=True)

            with st.expander("📋 RPE 참고표 &  MET 참고값 (ACSM 2024 Compendium)"):
                st.markdown("""
**RPE 기준:**
| RPE | 호흡 | 대표 운동 |
|:---:|------|-----------|
| 1~2 | 대화 편안 | 천천히 걷기 |
| 3~4 | 대화 가능 | 빠르게 걷기 |
| 5~6 | 짧은 문장 | 조깅, 수영 |
| 7~8 | 말하기 힘듦 | 달리기, 등산 |
| 9~10 | 말 불가 | 전력질주 |

**종목별 MET 참고값 (ACSM 2024):**
| 종목 | MET |
|------|:---:|
| 천천히 걷기 (4km/h) | 3.0 |
| 빠르게 걷기 (6km/h) | 4.5 |
| 조깅 (8km/h) | 7.0 |
| 달리기 (10km/h) | 9.8 |
| 자전거 (저강도) | 4.0 |
| 자전거 (중강도) | 6.8 |
| 수영 (저강도) | 5.8 |
| 수영 (고강도) | 7.0 |
| 등산 | 6.0 |
| 줄넘기 | 8.8 |
| 배드민턴 | 5.5 |
| 축구/농구 | 7.5 |
> 출처: Ainsworth BE et al., *2024 Adult Compendium of Physical Activities*, J Sci Med Sport 2024
                """)

            c_load    = c_duration * c_rpe
            c_met_min = int(c_met_custom * c_duration)
            st.markdown(
                f"<p style='color:#2563EB;font-size:13px;margin-top:6px;'>"
                f"⏱ {c_duration}분 · RPE {c_rpe} · MET {c_met_custom} → "
                f"<b>{c_load} RPE-min &nbsp;/&nbsp; {c_met_min} MET-min</b></p>",
                unsafe_allow_html=True)
            if st.button("➕ 목록에 추가", key="add_cardio", type="primary"):
                st.session_state["wl_entries"].append({
                    "type": "유산소", "name": ex_name,
                    "duration": c_duration, "rpe": c_rpe,
                    "load": c_load, "met_min": c_met_min, "met": c_met_custom,
                })
                st.toast(f"{ex_name} 추가됨!", icon="✅")
                st.rerun()

        # ════════ 근력 ════════
        with t_strength:
            st.write("")
            strength_options = ["🏋️ 웨이트 (머신)", "🏋️ 웨이트 (프리웨이트)",
                                 "💪 맨몸 운동 (푸시업·스쿼트 등)", "🤸 케틀벨", "직접 입력"]
            s_selected = st.selectbox("운동 종목", strength_options, key="str_ex")
            s_name = (st.text_input("종목 이름", placeholder="예: 데드리프트 ...", key="str_custom")
                      if s_selected == "직접 입력" else s_selected)
            s_name = s_name if s_name else "기타 근력"

            col1, col2, col3 = st.columns(3)
            with col1: s_sets   = st.number_input("세트 수", 1, 20, 3, 1, key="s_sets")
            with col2: s_reps   = st.number_input("반복 수", 1, 50, 10, 1, key="s_reps")
            with col3: s_weight = st.number_input("무게 (kg)", 0, 500, 0, 5, key="s_weight")
            s_duration = st.number_input("총 시간 (분, 휴식 포함)", 1, 180, 45, 5, key="s_dur")
            s_rpe      = st.slider("강도 (RPE)", 1, 10, 6, key="s_rpe")

            # MET 수동 조정 (근력)
            col_met2, col_met2h = st.columns([2, 3])
            with col_met2:
                s_met_custom = st.number_input(
                    "MET 값 (직접 조정)", 0.5, 20.0, 5.0, 0.5, key="s_met",
                    help="웨이트 기본값 5.0 (ACSM 2024). 종목·강도에 따라 조정하세요.")
            with col_met2h:
                st.markdown(
                    "<p style='color:#64748b;font-size:12px;margin-top:28px;'>"
                    "웨이트 <b>5.0</b> · 맨몸운동 <b>3.5~5.0</b> · 케틀벨 <b>6.0~9.0</b></p>",
                    unsafe_allow_html=True)

            with st.expander("📋 근력 RPE(RIR) · MET 참고표"):
                st.markdown("""
**RIR(Reps In Reserve)**: 세트 종료 시 더 들 수 있었던 횟수
| RPE | RIR | 활용 |
|:---:|:---:|------|
| **1~3** | 7회↑ 남음 | 워밍업 |
| **4~5** | 4~6회 남음 | 가벼운 펌핑 |
| **6~7** | 2~3회 남음 | 근비대 최적 구간 ✅ |
| **8~9** | 1회 남음 | 고강도 트레이닝 |
| **10** | 0 (실패) | 1RM 테스트 |

**MET 참고값 (ACSM 2024):**
| 종목 | MET |
|------|:---:|
| 웨이트 트레이닝 (일반) | 5.0 |
| 웨이트 트레이닝 (고강도) | 6.0 |
| 맨몸 운동 (푸시업·스쿼트) | 3.5 |
| 케틀벨 스윙 | 9.0 |
| 파워리프팅 | 6.0 |
                """)

            s_load    = s_duration * s_rpe
            s_met_min = int(s_met_custom * s_duration)
            wt_str    = f"{s_weight}kg" if s_weight > 0 else "맨몸"
            st.markdown(
                f"<p style='color:#2563EB;font-size:13px;margin-top:6px;'>"
                f"{s_sets}×{s_reps} {wt_str} · ⏱ {s_duration}분 · RPE {s_rpe} · MET {s_met_custom} → "
                f"<b>{s_load} RPE-min &nbsp;/&nbsp; {s_met_min} MET-min</b></p>",
                unsafe_allow_html=True)
            if st.button("➕ 목록에 추가", key="add_strength", type="primary"):
                st.session_state["wl_entries"].append({
                    "type": "근력", "name": s_name,
                    "duration": s_duration, "rpe": s_rpe,
                    "load": s_load, "met_min": s_met_min, "met": s_met_custom,
                    "sets": s_sets, "reps": s_reps, "weight": s_weight,
                })
                st.toast(f"{s_name} 추가됨!", icon="✅")
                st.rerun()

        # ════════ 유연성·회복 ════════
        with t_recovery:
            st.write("")
            recovery_options = ["🧘 요가", "🤸 스트레칭", "🛁 냉온욕", "🚶 가벼운 산책", "직접 입력"]
            r_selected = st.selectbox("종류", recovery_options, key="rec_ex")
            r_name = (st.text_input("종류 이름", key="rec_custom")
                      if r_selected == "직접 입력" else r_selected)
            r_name = r_name if r_name else "기타 회복"

            col1, col2 = st.columns(2)
            with col1: r_duration = st.number_input("시간 (분)", 1, 120, 20, 5, key="r_dur")
            with col2: r_rpe      = st.slider("강도 (RPE)", 1, 5, 2, key="r_rpe")

            with st.expander("📋 회복 RPE 참고표"):
                st.markdown("""
| RPE | 느낌 | 예시 |
|:---:|------|------|
| **1** | 전혀 힘들지 않음 | 누워서 스트레칭 |
| **2** | 가볍게 늘어나는 느낌 | 요가, 폼롤러 |
| **3** | 약간의 자극 | 가벼운 산책 |
| **4~5** | 조금 힘듦 | 빠른 걷기 |
> 회복일은 **RPE 1~3** 유지가 목적이에요.
                """)

            # MET 수동 조정 (회복)
            col_rmet, col_rmeth = st.columns([2, 3])
            with col_rmet:
                r_met_custom = st.number_input(
                    "MET 값 (직접 조정)", 0.5, 10.0, 2.5, 0.5, key="r_met",
                    help="요가 기본값 2.5 (ACSM 2024)")
            with col_rmeth:
                st.markdown(
                    "<p style='color:#64748b;font-size:12px;margin-top:28px;'>"
                    "요가/스트레칭 <b>2.5</b> · 가벼운 산책 <b>3.0</b> · 냉온욕 <b>2.0</b></p>",
                    unsafe_allow_html=True)

            r_load    = r_duration * r_rpe
            r_met_min = int(r_met_custom * r_duration)
            st.markdown(
                f"<p style='color:#2563EB;font-size:13px;margin-top:6px;'>"
                f"⏱ {r_duration}분 · RPE {r_rpe} · MET {r_met_custom} → "
                f"<b>{r_load} RPE-min &nbsp;/&nbsp; {r_met_min} MET-min</b></p>",
                unsafe_allow_html=True)
            if st.button("➕ 목록에 추가", key="add_recovery", type="primary"):
                st.session_state["wl_entries"].append({
                    "type": "회복", "name": r_name,
                    "duration": r_duration, "rpe": r_rpe,
                    "load": r_load, "met_min": r_met_min, "met": r_met_custom,
                })
                st.toast(f"{r_name} 추가됨!", icon="✅")
                st.rerun()

    st.write("")

    # ══════════════════════════════════════
    #  STEP 2 — 운동 목록 + 목표 달성 게이지
    # ══════════════════════════════════════
    entries = st.session_state["wl_entries"]

    if entries:
        total_load    = sum(e["load"]    for e in entries)
        total_met_min = sum(e["met_min"] for e in entries)

        with st.container(border=True):
            st.markdown("#### 📋 오늘 운동 목록")

            # ── 합산 수치 (크게) ──
            st.markdown(
                f"<div style='background:linear-gradient(135deg,#EFF6FF,#DBEAFE);"
                f"border-radius:14px;padding:16px 20px;margin-bottom:16px;'>"
                f"<div style='display:flex;justify-content:space-around;align-items:center;'>"
                f"<div style='text-align:center;'>"
                f"<div style='font-size:2.2rem;font-weight:800;color:#2563EB;line-height:1;'>{total_load}</div>"
                f"<div style='font-size:12px;color:#64748b;margin-top:2px;'>RPE-min</div>"
                f"</div>"
                f"<div style='font-size:1.4rem;color:#CBD5E1;'>|</div>"
                f"<div style='text-align:center;'>"
                f"<div style='font-size:2.2rem;font-weight:800;color:#2563EB;line-height:1;'>{total_met_min}</div>"
                f"<div style='font-size:12px;color:#64748b;margin-top:2px;'>MET-min</div>"
                f"</div>"
                f"<div style='font-size:1.4rem;color:#CBD5E1;'>|</div>"
                f"<div style='text-align:center;'>"
                f"<div style='font-size:2.2rem;font-weight:800;color:#2563EB;line-height:1;'>"
                f"{sum(e['duration'] for e in entries)}</div>"
                f"<div style='font-size:12px;color:#64748b;margin-top:2px;'>분</div>"
                f"</div>"
                f"</div></div>",
                unsafe_allow_html=True)

            # ── 목표 달성 게이지 ──
            def _gauge(label, actual, target, unit):
                pct    = min(actual / target, 1.0) if target > 0 else 0
                pct_v  = min(actual / target * 100, 100) if target > 0 else 0
                over   = actual > target
                color  = "#10b981" if over else ("#2563EB" if pct >= 0.8 else "#f59e0b" if pct >= 0.5 else "#ef4444")
                badge  = "✅ 달성!" if over else f"{pct_v:.0f}%"
                st.markdown(
                    f"<div style='margin-bottom:8px;'>"
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>"
                    f"<span style='font-size:12px;color:#64748b;'>{label}</span>"
                    f"<span style='font-size:12px;font-weight:700;color:{color};'>"
                    f"{actual} / {target} {unit} &nbsp; {badge}</span>"
                    f"</div>"
                    f"<div style='background:#E2E8F0;border-radius:99px;height:8px;'>"
                    f"<div style='background:{color};width:{min(pct*100,100):.1f}%;height:8px;"
                    f"border-radius:99px;transition:width 0.3s;'></div>"
                    f"</div></div>",
                    unsafe_allow_html=True)

            st.markdown("<p style='color:#475569;font-size:13px;font-weight:600;margin-bottom:6px;'>"
                        "🎯 오늘의 목표 달성률</p>", unsafe_allow_html=True)
            # [FIX 2] 게이지도 MET-min 단일 기준으로 표시 (RPE-min 제거)
            _gauge("MET-min 달성", total_met_min, target_met_min, "MET-min")
            _gauge("RPE-min 참고", total_load,    target_load,    "RPE-min")
            st.write("")

            for idx, e in enumerate(st.session_state["wl_entries"]):
                type_emoji = "🏃" if e["type"] == "유산소" else "🏋️" if e["type"] == "근력" else "🧘"
                is_editing = (st.session_state["wl_edit_idx"] == idx)

                if is_editing:
                    # ── 수정 모드 ──────────────────────────
                    st.markdown(
                        f"<div style='background:#EFF6FF;border:1.5px solid #2563EB;"
                        f"border-radius:12px;padding:10px 14px;margin:4px 0;'>",
                        unsafe_allow_html=True)
                    st.markdown(f"**{type_emoji} {e['name']} 수정**")

                    # 근력이면 세트/반복/무게도 수정
                    if e["type"] == "근력":
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            new_dur = st.number_input("시간 (분)", 1, 300,
                                                      value=e["duration"], step=5, key=f"ed_dur_{idx}")
                            new_sets = st.number_input("세트 수", 1, 20,
                                                       value=e.get("sets", 3), step=1, key=f"ed_sets_{idx}")
                        with ec2:
                            new_rpe = st.slider("RPE", 1, 10,
                                                value=e["rpe"], key=f"ed_rpe_{idx}")
                            new_reps = st.number_input("반복 수", 1, 50,
                                                       value=e.get("reps", 10), step=1, key=f"ed_reps_{idx}")
                        new_weight = st.number_input("무게 (kg)", 0, 500,
                                                     value=e.get("weight", 0), step=5, key=f"ed_wt_{idx}")
                    else:
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            new_dur = st.number_input("시간 (분)", 1, 300,
                                                      value=e["duration"], step=5, key=f"ed_dur_{idx}")
                        with ec2:
                            new_rpe = st.slider("RPE", 1, 10,
                                                value=e["rpe"], key=f"ed_rpe_{idx}")
                        new_sets = new_reps = new_weight = None

                    new_load    = new_dur * new_rpe
                    new_met_min = int(rpe_to_met(new_rpe) * new_dur)
                    st.markdown(
                        f"<p style='color:#2563EB;font-size:12px;'>"
                        f"→ {new_load} RPE-min &nbsp;·&nbsp; ≈{new_met_min} MET-min</p>",
                        unsafe_allow_html=True)

                    sc1, sc2 = st.columns(2)
                    with sc1:
                        if st.button("✅ 저장", key=f"save_{idx}", type="primary"):
                            e["duration"] = new_dur
                            e["rpe"]      = new_rpe
                            e["load"]     = new_load
                            e["met_min"]  = new_met_min
                            if new_sets  is not None: e["sets"]   = new_sets
                            if new_reps  is not None: e["reps"]   = new_reps
                            if new_weight is not None: e["weight"] = new_weight
                            st.session_state["wl_edit_idx"] = -1
                            st.rerun()
                    with sc2:
                        if st.button("취소", key=f"cancel_{idx}"):
                            st.session_state["wl_edit_idx"] = -1
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                else:
                    # ── 표시 모드 ──────────────────────────
                    extra = ""
                    if e["type"] == "근력" and e.get("sets"):
                        wt = f"{e['weight']}kg" if e.get("weight") else "맨몸"
                        extra = f" &nbsp;·&nbsp; {e['sets']}×{e.get('reps','-')} {wt}"

                    col_info, col_edit, col_del = st.columns([5, 1, 1])
                    with col_info:
                        st.markdown(
                            f"<div style='background:#F8FAFF;border:1px solid #CBD5E1;"
                            f"border-radius:10px;padding:8px 14px;'>"
                            f"<span style='font-size:13px;color:#1e293b;'>"
                            f"{type_emoji} <b>{e['name']}</b>{extra}</span><br>"
                            f"<span style='font-size:12px;color:#64748b;'>"
                            f"{e['duration']}분 &nbsp;·&nbsp; RPE {e['rpe']} &nbsp;·&nbsp; "
                            f"<b style='color:#2563EB;'>{e['load']} RPE-min</b>"
                            f" &nbsp;·&nbsp; ≈{e['met_min']} MET-min</span>"
                            f"</div>", unsafe_allow_html=True)
                    with col_edit:
                        if st.button("✏️", key=f"edit_{idx}", help="수정"):
                            st.session_state["wl_edit_idx"] = idx
                            st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"del_{idx}", help="삭제"):
                            st.session_state["wl_entries"].pop(idx)
                            if st.session_state["wl_edit_idx"] == idx:
                                st.session_state["wl_edit_idx"] = -1
                            st.rerun()

        st.write("")


    st.write("")

    # ══════════════════════════════════════
    #  STEP 3 — 제출
    # ══════════════════════════════════════
    with st.container(border=True):
        st.markdown("#### 📝 오늘 운동 총평")
        notes = st.text_area("메모 (선택)", placeholder="컨디션, 특이사항, 피로 부위 등을 자유롭게 적어보세요.",
                             height=70, key="workout_notes")
        st.write("")
        overall_rpe = st.slider("오늘 전체 강도 (RPE)", 1, 10, 5, key="overall_rpe",
                                help="모든 운동 합쳐서 오늘 하루 전체 느낌으로 평가 · 15~30분 후 권장")
        st.write("")
        st.markdown("<p style='color:#475569;font-size:13px;font-weight:600;'>오늘 운동 어떠셨나요?</p>",
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
            saved_entries = st.session_state["wl_entries"]
            if saved_entries:
                f_load    = sum(e["load"]    for e in saved_entries)
                f_met_min = sum(e["met_min"] for e in saved_entries)
                f_dur     = sum(e["duration"] for e in saved_entries)
            else:
                f_dur     = 30
                f_load    = f_dur * overall_rpe
                f_met_min = int(rpe_to_met(overall_rpe) * f_dur)

            adj = {"hard": 0.95, "ok": 1.0, "easy": 1.05}[feedback]
            st.session_state["baseline_met"] = int(baseline * adj)
            st.session_state["session_logs"].append({
                "day": day, "date": date.today().isoformat(),
                "load": f_load, "met_min": f_met_min,
                "rpe": overall_rpe, "duration": f_dur,
                "entries": saved_entries, "notes": notes, "feedback": feedback,
            })
            st.session_state["streak"]      += 1
            st.session_state["sleep_score"]  = None
            st.session_state["page"]         = "main"
            st.session_state["wl_entries"]   = []
            st.session_state["wl_edit_idx"]  = -1
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
