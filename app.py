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

# WHO 2020 / ACSM 2022 주간 권장 (성인)
WHO_MET_MIN_WEEK_MIN = 600    # 최소 MET-min/주 (중강도 4 MET × 150분)
WHO_MET_MIN_WEEK_OPT = 1200   # 최적 MET-min/주 (중강도 4 MET × 300분)

# 나이/성별 주간 MET 권장치 배수
# 근거: ACSM (2022) 연령별 VO₂max 정상범위 기반 활동능력 차이
# 기준: 성인 40대 남성 = 1.0
WEEKLY_MET_MULTIPLIER = {
    ("남성", "20대"):  1.20,
    ("남성", "30대"):  1.10,
    ("남성", "40대"):  1.00,
    ("남성", "50대"):  0.90,
    ("남성", "60대↑"): 0.75,
    ("여성", "20대"):  1.05,
    ("여성", "30대"):  0.95,
    ("여성", "40대"):  0.85,
    ("여성", "50대"):  0.78,
    ("여성", "60대↑"): 0.65,
}

def get_weekly_met_targets() -> tuple:
    """나이/성별 보정된 주간 MET-min 최소·최적 목표 반환."""
    sex = st.session_state.get("sex", "남성")
    age = st.session_state.get("age_group", "40대")
    mult = WEEKLY_MET_MULTIPLIER.get((sex, age), 1.0)
    return int(WHO_MET_MIN_WEEK_MIN * mult), int(WHO_MET_MIN_WEEK_OPT * mult)


# ──────────────────────────────────────────
#  data/sleep 통계 로드
# ──────────────────────────────────────────
_SLEEP_STATS_FALLBACK = {
    "HOURS_DECIMAL":    {"mean": 7.58, "std": 0.67, "min": 4.0, "max": 10.0},
    "REM_PERCENT":      {"mean": 18.98,"std": 3.84, "min": 5.0, "max": 35.0},
    "DEEP_PERCENT":     {"mean": 17.21,"std": 3.37, "min": 5.0, "max": 30.0},
    "HR_BELOW_RESTING": {"mean": 76.78,"std": 15.0, "min": 20.0,"max": 100.0},
}

@st.cache_data
def load_sleep_stats():
    base  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sleep")
    files = glob.glob(os.path.join(base, "*.csv"))
    if not files:
        return _SLEEP_STATS_FALLBACK   # data/sleep 없으면 하드코딩 기본값 사용
    dfs   = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df.columns = [str(c).strip().upper() for c in df.columns]
            dfs.append(df)
        except Exception:
            continue
    if not dfs:
        return _SLEEP_STATS_FALLBACK
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


def impute_missing(hist, sleep_hours: float = None):
    """
    결측치 보완 + 수면시간 비율 보정.

    기존 문제: 수면시간과 무관하게 평균값을 그대로 채워 짧은 수면을 '보통'으로 평가.

    해결: sleep_hours가 주어지면 정상 수면시간 대비 비율(ratio)을 계산해 각 피처를 스케일 다운.
    근거:
      - REM은 수면 후반부에 집중 → 짧게 자면 REM 사이클 자체를 못 채움 (Walker, 2017)
      - 깊은수면은 초반 90분에 집중 → 상대적으로 덜 감소 (Ohayon et al., 2004)
      - HR이하비율은 회복 시간 비례 → 선형 감소

    power 지수:
      REM:  1.5 (가장 민감)
      deep: 0.8 (덜 민감)
      HR:   1.0 (선형)
    """
    base_rem  = float(np.mean(hist["rem"]))  if hist["rem"]  else SLEEP_STATS["REM_PERCENT"]["mean"]
    base_deep = float(np.mean(hist["deep"])) if hist["deep"] else SLEEP_STATS["DEEP_PERCENT"]["mean"]
    base_hr   = float(np.mean(hist["hr"]))   if hist["hr"]   else SLEEP_STATS["HR_BELOW_RESTING"]["mean"]

    if sleep_hours is not None:
        normal_h = SLEEP_STATS["HOURS_DECIMAL"]["mean"]   # ~7.58h
        ratio    = float(np.clip(sleep_hours / normal_h, 0.0, 1.0))
        base_rem  = base_rem  * (ratio ** 1.5)
        base_deep = base_deep * (ratio ** 0.8)
        base_hr   = base_hr   * (ratio ** 1.0)

    return {
        "REM_PERCENT":      base_rem,
        "DEEP_PERCENT":     base_deep,
        "HR_BELOW_RESTING": base_hr,
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
def calc_acwr(logs, baseline):
    """
    ACWR 날짜 기반 계산 (Foster + Gabbett).
    이전: streak 번호(day) 기반 → 쉬는 날이 반영 안 됨
    변경: 실제 날짜(date 필드) 기반 → 공백 기간 자동 반영, MET-min 단위 통일
    """
    today = date.today()

    def days_ago(log):
        d = log.get("date")
        if not d:
            return 9999   # date 없으면 제외
        return (today - date.fromisoformat(d)).days

    acute_loads   = [l.get("met_min", l.get("load", 0)) for l in logs if days_ago(l) < 7]
    chronic_loads = [l.get("met_min", l.get("load", 0)) for l in logs if days_ago(l) < 28]

    acute = sum(acute_loads)

    # 올바른 chronic 계산: 28일 총합 ÷ 4주 = 주간 평균 MET-min
    # 이전 버그: sum/len × 7 → 세션 평균 × 7 → 주 1회 운동자의 chronic이 7배 뻥튀기됨
    # 예: 28일간 500 MET-min × 4회 = 2000총합 → 2000/4 = 500/주 (올바름)
    #     이전식: 2000/4 × 7 = 3500/주 (잘못됨)
    if len(chronic_loads) >= 4:
        chronic = sum(chronic_loads) / 4
    else:
        chronic = baseline  # 데이터 부족 시 baseline 주간 목표를 만성부하로 사용

    acwr = acute / chronic if chronic > 0 else 1.0

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

def try_retrain_model() -> bool:
    """
    high/medium quality 데이터가 30개 이상이면 재학습.
    재학습 성공 시 labeled_data 초기화 → 이후 30개 새로 쌓여야 다시 재학습.
    (이전 버그: 초기화 없이 30개 초과 상태 유지 → 매 예측마다 재학습 반복)
    """
    global ml_model
    data = st.session_state.get("labeled_data", [])
    hq   = [d for d in data if d.get("quality") in ("high", "medium")]
    if len(hq) < AUTO_RETRAIN_THRESHOLD:
        return False

    from sklearn.linear_model import LinearRegression
    import pickle as _pkl

    X = [d["X"] for d in hq]
    y = [d["y"] for d in hq]

    try:
        new_model = LinearRegression()
        new_model.fit(X, y)

        ml_model = new_model
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sleep_model.pkl")
        with open(model_path, "wb") as f:
            _pkl.dump(new_model, f)

        # 재학습 완료 후 labeled_data 초기화 → 다음 30개부터 다시 누적
        st.session_state["labeled_data"] = []
        return True
    except Exception as e:
        # 재학습 실패해도 앱이 죽으면 안 됨 (데이터 부족, 수치 불안정 등)
        st.session_state["labeled_data"] = []   # 불량 데이터 초기화
        return False


def save_labeled(features: list, true_score: int, quality: str = "low"):
    """
    (입력값, 실제점수) 쌍 저장. quality: high/medium/low.
    high+medium 30개 누적 시 자동 재학습 후 초기화.
    """
    st.session_state["labeled_data"].append({"X": features, "y": true_score, "quality": quality})

    hq_count = sum(1 for d in st.session_state["labeled_data"]
                   if d.get("quality") in ("high", "medium"))
    if hq_count >= AUTO_RETRAIN_THRESHOLD:
        if try_retrain_model():
            st.toast("✨ 수면 모델이 내 데이터로 재학습됐어요!", icon="🧠")


def apply_age_offset(score: int) -> int:
    """나이대별 수면 점수 기준 보정. 나이 들수록 깊은수면이 자연 감소하므로 offset 적용."""
    age = st.session_state.get("age_group", "30대")
    offset = SLEEP_SCORE_AGE_OFFSET.get(age, 0)
    return min(max(score + offset, 0), 100)


def calc_streak(session_logs: list) -> int:
    """
    실제 날짜 기반 연속 운동일 계산.
    - 오늘 또는 어제를 기준으로 연속된 날 수를 역산
    - 휴식일(rest)도 연속에 포함 (쉬는 것도 의도적 행동)
    - 이전: streak = 운동 완료 횟수(누적) → 3일 쉬어도 연속처럼 보임
    - 변경: 날짜 기반 연속일 수 → 하루라도 건너뛰면 1로 리셋
    """
    if not session_logs:
        return 0
    logged_dates = sorted({
        date.fromisoformat(l["date"]) for l in session_logs if l.get("date")
    }, reverse=True)
    if not logged_dates:
        return 0

    today      = date.today()
    # 오늘 또는 어제부터 시작 (당일 아직 기록 안 했을 수 있으니)
    check_from = today if logged_dates[0] == today else (today - timedelta(days=1))
    if logged_dates[0] < check_from:
        return 0   # 마지막 기록이 어제 이전이면 연속 끊김

    streak = 0
    expected = check_from
    for d in logged_dates:
        if d == expected:
            streak += 1
            expected -= timedelta(days=1)
        elif d < expected:
            break   # 하루라도 건너뜀 → 종료
    return streak


_USER_HISTORY_MAX = 30   # 최근 N개만 유지

def append_user_history(rem: float, deep: float, hr: float):
    """user_history에 추가 + 최근 30개 초과분 자동 제거."""
    hist = st.session_state["user_history"]
    hist["rem"].append(rem)
    hist["deep"].append(deep)
    hist["hr"].append(hr)
    # 오래된 항목 제거 (최근 N개 유지)
    for key in ("rem", "deep", "hr"):
        if len(hist[key]) > _USER_HISTORY_MAX:
            hist[key] = hist[key][-_USER_HISTORY_MAX:]


def already_measured_today() -> bool:
    """오늘 날짜 기준으로 수면 점수가 이미 측정됐는지 확인."""
    today = date.today().isoformat()
    return any(s["date"] == today for s in st.session_state.get("sleep_logs", []))


def save_sleep_score(score: int):
    """수면 점수를 sleep_logs에 오늘 날짜로 저장 (중복 시 덮어쓰기)."""
    today = date.today().isoformat()
    logs  = st.session_state["sleep_logs"]
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

PERSIST_KEYS = ["step", "use_watch", "baseline_met", "streak", "total_workouts",
                "user_history", "session_logs", "sleep_logs", "start_date",
                "labeled_data", "sex", "age_group", "today_completed_date"]

_DEFAULTS = {
    "step":         0,
    "use_watch":    False,
    "baseline_met": BASELINE_MET_3_0,
    "streak":       0,       # 현재 연속 운동일 수
    "total_workouts": 0,    # 누적 운동 횟수 (연속 아니어도 카운트)
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
    # 오늘 완료 여부 (운동 완료 or 휴식 선택 시 오늘 날짜로 설정)
    "today_completed_date": None,
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
    # ── 디버그 버튼 (사이드바 구석) ──
    with st.sidebar:
        st.markdown("<p style='color:#cbd5e1;font-size:10px;margin-bottom:4px;'>🛠 debug</p>",
                    unsafe_allow_html=True)
        if st.button("⏭ 다음날로", help="today_completed_date·sleep_score 초기화 (테스트용)"):
            st.session_state["today_completed_date"] = None
            st.session_state["sleep_score"]          = None
            save_user_data()
            st.rerun()

    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("<h2 style='margin-bottom:0;'>🌙 잘쉼</h2>", unsafe_allow_html=True)
        streak = st.session_state["streak"]
        total  = st.session_state.get("total_workouts", 0)
        st.markdown(f"<p style='color:#94a3b8;margin-top:0;'>🔥 {streak}일 연속 &nbsp;·&nbsp; 총 {total}회</p>",
                    unsafe_allow_html=True)
    with col2:
        icon = "⌚" if st.session_state["use_watch"] else "📱"
        st.markdown(f"<h2 style='text-align:right;margin-top:10px;'>{icon}</h2>", unsafe_allow_html=True)

    st.progress(min(st.session_state["streak"] / 30, 1.0))
    st.write("")

    tab_today, tab_history, tab_settings = st.tabs(["🏠  오늘", "📈  기록", "⚙️  설정"])

    with tab_today:
        today_str = date.today().isoformat()

        # [FIX 1] 오늘 이미 완료(운동 or 휴식)했으면 완료 화면
        if st.session_state.get("today_completed_date") == today_str:
            _show_today_done()

        # 수면 점수 없으면 → 오늘 sleep_logs에서 복원 시도 → 없으면 측정 화면
        elif st.session_state["sleep_score"] is None:
            today_log = next((s for s in st.session_state["sleep_logs"]
                              if s["date"] == today_str), None)
            if today_log:
                st.session_state["sleep_score"] = today_log["score"]
                st.rerun()
            else:
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
def _show_today_done():
    """오늘 운동 완료 or 휴식 선택 후 표시되는 완료 화면."""
    logs        = st.session_state["session_logs"]
    today_str   = date.today().isoformat()
    today_log   = next((l for l in reversed(logs) if l.get("date") == today_str), None)
    is_rest     = today_log and today_log.get("feedback") == "rest"

    wm_min, wm_opt = get_weekly_met_targets()
    week_met = sum(l.get("met_min", 0) for l in logs
                   if l.get("date") and (date.today() - date.fromisoformat(l["date"])).days < 7)

    with st.container(border=True):
        if is_rest:
            st.markdown("### 😴 오늘은 잘 쉬어요!")
            st.markdown("<p style='color:#64748b;'>회복도 훈련이에요. 내일 더 좋은 컨디션으로 만나요.</p>",
                        unsafe_allow_html=True)
        else:
            met_done = today_log.get("met_min", 0) if today_log else 0
            st.markdown("### 🎉 오늘 운동 완료!")
            st.markdown(f"<p style='color:#64748b;'>오늘 {met_done} MET-min 달성했어요. 수고하셨어요!</p>",
                        unsafe_allow_html=True)

        st.write("")

        # 이번 주 진행률 (나이/성별 보정 기준)
        st.markdown("<p style='color:#475569;font-size:13px;font-weight:600;'>📊 이번 주 운동량</p>",
                    unsafe_allow_html=True)
        pct_min = min(week_met / wm_min, 1.0) if wm_min > 0 else 0
        pct_opt = min(week_met / wm_opt, 1.0) if wm_opt > 0 else 0
        color   = "#10b981" if week_met >= wm_opt else "#2563EB" if week_met >= wm_min else "#f59e0b"
        label   = "최적 달성! 🌟" if week_met >= wm_opt else ("최소 권장 달성 ✅" if week_met >= wm_min else "권장량 미달")

        st.markdown(
            f"<p style='color:{color};font-size:13px;font-weight:700;margin-bottom:4px;'>"
            f"{week_met} MET-min &nbsp;·&nbsp; {label}</p>", unsafe_allow_html=True)
        st.progress(pct_opt)
        st.markdown(
            f"<p style='color:#94a3b8;font-size:11px;'>"
            f"최소 {wm_min} / 최적 {wm_opt} MET-min/주 "
            f"(WHO 2020 기준, {st.session_state.get('sex','성인')} "
            f"{st.session_state.get('age_group','')} 보정값)</p>",
            unsafe_allow_html=True)

        st.write("")
        st.markdown("<p style='color:#94a3b8;font-size:12px;text-align:center;'>내일 아침 다시 수면 체크를 해주세요 🌙</p>",
                    unsafe_allow_html=True)


def _show_sleep_input():
    with st.container(border=True):
        st.markdown("#### 🌙 오늘 컨디션 체크")
        # [FIX 2] 오늘 이미 측정한 경우 안내 (재측정은 허용하되 중복 수집 방지)
        if already_measured_today():
            st.info("오늘 수면 점수를 이미 측정했어요. 재측정하면 오늘 점수가 업데이트됩니다.")
        st.write("")

        if st.session_state["use_watch"]:
            # [FIX 3] 오늘 날짜 기준으로 하루에 한 번만 생성
            # 이전: session_state 없을 때마다 생성 → 앱 껐다 켜면 새 랜덤값
            # 변경: watch_synced_date 비교 → 오늘 날짜 다르면 새로 생성
            today_str = date.today().isoformat()
            if (st.session_state.get("watch_synced_date") != today_str
                    or "watch_synced_data" not in st.session_state):
                st.session_state["watch_synced_data"] = simulate_watch_sync()
                st.session_state["watch_synced_date"] = today_str

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
                        save_labeled([wd["HOURS_DECIMAL"], wd["REM_PERCENT"],
                                      wd["DEEP_PERCENT"], wd["HR_BELOW_RESTING"]], final, quality="medium")
                        save_user_data()
                        # 워치 데이터도 user_history에 저장 (결측치 보완 품질 향상)
                        append_user_history(wd["REM_PERCENT"], wd["DEEP_PERCENT"], wd["HR_BELOW_RESTING"])
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
                    imp = impute_missing(st.session_state["user_history"], sleep_hours)
                    X   = pd.DataFrame([[sleep_hours, imp["REM_PERCENT"],
                                         imp["DEEP_PERCENT"], imp["HR_BELOW_RESTING"]]],
                                       columns=["HOURS_DECIMAL","REM_PERCENT","DEEP_PERCENT","HR_BELOW_RESTING"])
                    # [FIX 6] 이전: score * (feel/3.0) → feel=1이면 점수 1/3 토막 (85→28)
                    # 변경: ±10점 가산 방식으로 교체 (feel 1→-10, 3→0, 5→+10, 범위 제한)
                    raw   = ml_model.predict(X)[0]
                    score = int(raw + (subjective_feel - 3) * 5)
                    final = apply_age_offset(min(max(score, 0), 100))
                    st.session_state["sleep_score"] = final
                    save_sleep_score(final)
                    save_labeled([sleep_hours, imp["REM_PERCENT"],
                                  imp["DEEP_PERCENT"], imp["HR_BELOW_RESTING"]], final, quality="low")
                    save_user_data()
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
                    append_user_history(rem_percent, deep_percent, hr_below)
                    final = apply_age_offset(min(max(score, 0), 100))
                    st.session_state["sleep_score"] = final
                    save_sleep_score(final)
                    save_labeled([sleep_hours, rem_percent, deep_percent, hr_below], final, quality="high")
                    save_user_data()
                    st.rerun()


# ──────────────────────────────────────────
#  운동 처방
# ──────────────────────────────────────────
def _show_prescription():
    score    = st.session_state["sleep_score"]
    logs     = st.session_state["session_logs"]
    baseline = st.session_state["baseline_met"]

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
        # 재학습 진행 카운터 표시 (자동 수집됨)
        # [FIX 6] high/medium quality만 카운트
        labeled_count = sum(1 for d in st.session_state.get("labeled_data", [])
                            if d.get("quality") in ("high", "medium"))
        remaining = max(0, AUTO_RETRAIN_THRESHOLD - labeled_count)
        if remaining > 0:
            st.markdown(
                f"<p style='color:#94a3b8;font-size:11px;margin-top:4px;'>"
                f"🧠 개인 모델 재학습까지 <b>{remaining}회</b> 남음 (예측할 때마다 자동 수집)</p>",
                unsafe_allow_html=True)
        else:
            st.markdown(
                "<p style='color:#10b981;font-size:11px;margin-top:4px;'>"
                "🧠 개인 모델로 재학습 완료!</p>",
                unsafe_allow_html=True)

        if st.button("다시 측정", key="rescore"):
            st.session_state["sleep_score"] = None
            st.rerun()

    st.write("")

    # ── ACWR 상태 카드 ──
    acwr_info = calc_acwr(logs, baseline)
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

    # 주간 MET-min (나이/성별 보정 기준)
    weekly_met_est       = sum(l.get("met_min", 0) for l in logs
                               if l.get("date") and (date.today() - date.fromisoformat(l["date"])).days < 7)
    wm_min, wm_opt       = get_weekly_met_targets()
    who_progress_min     = min(weekly_met_est / wm_min, 1.0) if wm_min > 0 else 0
    who_color            = "#10b981" if weekly_met_est >= wm_opt else "#2563EB" if weekly_met_est >= wm_min else "#f59e0b"
    who_label            = "최적 달성 🌟" if weekly_met_est >= wm_opt else ("최소 권장 달성 ✅" if weekly_met_est >= wm_min else "권장량 미달")

    with st.container(border=True):
        st.markdown("#### 🎯 오늘의 운동 처방")

        # 주간 달성률 (나이/성별 보정 기준)
        st.markdown(
            f"<p style='color:#64748b;font-size:12px;margin-bottom:4px;'>"
            f"주간 MET-min 달성률 &nbsp;·&nbsp; "
            f"<span style='color:{who_color};font-weight:600;'>{who_label}</span></p>",
            unsafe_allow_html=True)
        st.progress(who_progress_min)
        st.markdown(
            f"<p style='color:{who_color};font-size:12px;margin-top:2px;'>"
            f"이번 주 {weekly_met_est} MET-min &nbsp;·&nbsp; "
            f"최소 {wm_min} / 최적 {wm_opt}"
            f"<span style='color:#94a3b8;'> ({st.session_state.get('sex','성인')} "
            f"{st.session_state.get('age_group','')} 보정)</span></p>",
            unsafe_allow_html=True)

        st.write("")

        target_met_min = target

        # [FIX 4] 처방 이유 한 줄 설명
        def _prescription_reason(score, zone, load_mult):
            if score >= 80 and zone == "부족":
                return "수면 회복이 좋고 최근 운동량이 부족해서 오늘은 강도를 올렸어요 💪"
            elif score >= 80 and zone == "최적":
                return "컨디션도 좋고 운동 페이스도 이상적이에요. 오늘도 유지하세요 ✅"
            elif score >= 80 and zone == "주의":
                return "컨디션은 좋지만 최근 운동량이 많아요. 살짝 조절할게요 ⚠️"
            elif score >= 80 and zone == "위험":
                return "컨디션은 좋지만 과부하 상태예요. 오늘은 가볍게 풀어주세요 🚨"
            elif score >= 50 and zone == "부족":
                return "보통 컨디션에 운동량이 부족해서 평소보다 조금 더 권장해요 📈"
            elif score >= 50 and zone == "최적":
                return "컨디션과 운동량이 균형 잡혀 있어요. 평소대로 운동하세요 👍"
            elif score >= 50 and zone in ("주의", "위험"):
                return "컨디션이 보통이고 최근 운동이 많았어요. 오늘은 줄여봐요 📉"
            elif score < 50 and zone in ("주의", "위험"):
                return "수면 회복이 부족하고 과부하 상태예요. 오늘은 꼭 쉬어야 해요 🛌"
            else:
                return "수면 회복이 부족해요. 오늘은 가벼운 스트레칭 정도만 하세요 😴"

        reason = _prescription_reason(score, zone, load_mult)
        st.markdown(
            f"<div style='background:#EFF6FF;border-left:3px solid #2563EB;"
            f"border-radius:0 10px 10px 0;padding:8px 14px;margin-bottom:12px;'>"
            f"<p style='color:#2563EB;font-size:13px;margin:0;'>{reason}</p>"
            f"</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("오늘 목표", f"{target} MET-min",
                      help="수면 보정 × ACWR 보정이 적용된 오늘의 권장 운동량이에요.")
        with col2:
            st.metric("베이스라인 대비", f"{load_mult:.2f}×",
                      help=f"기준 {baseline} × ACWR {acwr_info['load_mult']} × 수면 {sleep_mod:.1f}")
        st.markdown(
            f"<p style='color:#94a3b8;font-size:11px;'>"
            f"기준 {baseline} MET-min × ACWR보정 {acwr_info['load_mult']} × 수면보정 {sleep_mod:.1f} = {target}"
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
        intensity_label = "저강도" if score < 50 else ("고강도" if score >= 80 and zone == "부족" else "중강도")
        with st.expander(f"📋 오늘 추천 운동 예시 보기 ({intensity_label})"):
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
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✅ 운동 완료 기록하기", type="primary", key="go_workout_log"):
                st.session_state["target_load"]    = target
                st.session_state["target_met_min"] = target_met_min
                st.session_state["page"] = "workout_log"
                st.rerun()
        with col_btn2:
            if st.button("😴 오늘은 쉬어요", key="rest_day"):
                today_iso = date.today().isoformat()
                # [FIX 5] 오늘 날짜 로그가 이미 있으면 중복 추가 방지
                already = any(l.get("date") == today_iso for l in st.session_state["session_logs"])
                if not already:
                    st.session_state["session_logs"].append({
                        "day":      st.session_state.get("total_workouts", 0),
                        "date":     today_iso,
                        "load":     0,
                        "met_min":  0,
                        "rpe":      0,
                        "duration": 0,
                        "entries":  [],
                        "notes":    "휴식일",
                        "feedback": "rest",
                    })
                st.session_state["streak"]               = calc_streak(st.session_state["session_logs"])
                st.session_state["sleep_score"]          = None
                st.session_state["today_completed_date"] = date.today().isoformat()
                save_user_data()
                st.toast("오늘 하루도 수고하셨어요 🛌", icon="😴")
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
        is_rest     = workout and workout.get("feedback") == "rest"
        high_load   = workout and not is_rest and workout.get("met_min", 0) >= 300
        great_sleep = sleep_s and sleep_s >= 80
        any_workout = bool(workout) and not is_rest

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
        elif is_rest:
            # 😴 휴식일
            bg     = "#F8F8F8"
            border = "1px solid #CBD5E1"
            shadow = "none"
            badge  = "😴"
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
      <span style='font-size:12px;color:#64748b;'>😴 휴식일</span>
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

    # ── 요약 지표 ──
    col1, col2, col3 = st.columns(3)
    sleep_logs = st.session_state.get("sleep_logs", [])
    session_logs = st.session_state.get("session_logs", [])
    with col1:
        with st.container(border=True):
            st.metric("🔥 운동 완료", f"{st.session_state['streak']}회")
    with col2:
        with st.container(border=True):
            avg_score = f"{np.mean([s['score'] for s in sleep_logs]):.0f}점" if sleep_logs else "-"
            st.metric("💤 평균 수면점수", avg_score)
    with col3:
        with st.container(border=True):
            week_met = sum(l.get("met_min", 0) for l in session_logs
                          if l.get("date") and (date.today() - date.fromisoformat(l["date"])).days < 7)
            st.metric("⚡ 이번주 MET-min", f"{week_met}")

    st.write("")

    # [FIX 8] 차트 — 수면 점수 추이 + 주간 MET-min
    with st.container(border=True):
        st.markdown("**📊 수면 점수 추이 (최근 30일)**")
        if len(sleep_logs) >= 2:
            # 날짜 정렬 후 DataFrame 생성
            chart_df = pd.DataFrame(
                [(s["date"], s["score"]) for s in sorted(sleep_logs, key=lambda x: x["date"])[-30:]],
                columns=["날짜", "수면점수"]
            ).set_index("날짜")
            st.line_chart(chart_df, color="#2563EB", height=160)
        else:
            st.markdown("<p style='color:#94a3b8;font-size:12px;'>데이터가 2일 이상 쌓이면 차트가 표시돼요.</p>",
                        unsafe_allow_html=True)

    st.write("")

    with st.container(border=True):
        st.markdown("**📊 주간 MET-min (최근 8주)**")
        if session_logs:
            # 주별 MET-min 집계
            from collections import defaultdict
            weekly = defaultdict(int)
            for l in session_logs:
                if l.get("date"):
                    d = date.fromisoformat(l["date"])
                    # ISO 주 번호
                    week_key = d.strftime("%Y-W%W")
                    weekly[week_key] += l.get("met_min", 0)
            if weekly:
                week_df = pd.DataFrame(
                    list(weekly.items()), columns=["주차", "MET-min"]
                ).sort_values("주차").tail(8).set_index("주차")
                st.bar_chart(week_df, color="#2563EB", height=160)
                st.markdown(
                    f"<p style='color:#94a3b8;font-size:11px;'>WHO 2020 최소 {get_weekly_met_targets()[0]} / 최적 {get_weekly_met_targets()[1]} MET-min/주 (개인 보정값)</p>",
                    unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#94a3b8;font-size:12px;'>운동을 기록하면 여기에 집계돼요.</p>",
                        unsafe_allow_html=True)

    st.write("")

    hist = st.session_state["user_history"]

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

    # [FIX 7] 수면 점수 이력 — sleep_logs(모든 입력 방식) 기반으로 통합
    with st.container(border=True):
        st.markdown("**💤 수면 점수 이력**")
        sleep_logs = st.session_state.get("sleep_logs", [])
        if sleep_logs:
            recent = sorted(sleep_logs, key=lambda x: x["date"], reverse=True)[:10]
            for s in recent:
                score_c = "#10b981" if s["score"] >= 80 else "#f59e0b" if s["score"] >= 50 else "#ef4444"
                st.markdown(
                    f"<p style='color:#64748b;font-size:13px;border-bottom:1px solid #F1F5F9;padding:6px 0;'>"
                    f"{s['date']} &nbsp;·&nbsp; "
                    f"<b style='color:{score_c};'>{s['score']}점</b>"
                    f"</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#94a3b8;'>수면 점수를 측정하면 여기에 기록이 쌓여요.</p>",
                        unsafe_allow_html=True)

    st.write("")

    # 세션 부하 이력
    with st.container(border=True):
        st.markdown("**🏋️ 세션 부하 이력**")
        logs = st.session_state["session_logs"]
        if logs:
            # 주간 MET-min 합계 (날짜 기반)
            weekly_met  = sum(l.get("met_min", 0) for l in logs
                              if l.get("date") and (date.today() - date.fromisoformat(l["date"])).days < 7)
            weekly_load = sum(l.get("load", 0) for l in logs
                              if l.get("date") and (date.today() - date.fromisoformat(l["date"])).days < 7)
            wm_min_h, wm_opt_h = get_weekly_met_targets()
            st.markdown(
                f"<p style='color:#2563EB;font-size:13px;font-weight:600;'>"
                f"이번 주 누적: {weekly_load} RPE-min &nbsp;·&nbsp; ≈ {weekly_met} MET-min"
                f"<span style='color:#94a3b8;font-weight:400;'> / 최소 {wm_min_h} / 최적 {wm_opt_h}</span></p>",
                unsafe_allow_html=True)
            st.progress(min(weekly_met / wm_opt_h, 1.0) if wm_opt_h > 0 else 0)
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
    # [FIX 5] 베이스라인 수동 조정
    with st.container(border=True):
        st.markdown("**🎯 베이스라인 수동 조정**")
        st.markdown(
            "<p style='color:#64748b;font-size:12px;'>부상·장기 공백 후 또는 현재 처방이 너무 높거나 낮을 때 직접 조정하세요.</p>",
            unsafe_allow_html=True)
        current_bl = st.session_state["baseline_met"]
        new_bl = st.slider(
            "일일 목표 MET-min", 50, 1500, current_bl, 10,
            help="낮출수록 가벼운 처방, 높일수록 강한 처방. 피드백으로 자동 수렴됩니다.")
        st.markdown(
            f"<p style='color:#94a3b8;font-size:11px;'>"
            f"참고: 걷기 4.5 MET × 60분 = 270 MET-min / 조깅 7 MET × 60분 = 420 MET-min</p>",
            unsafe_allow_html=True)
        if st.button("베이스라인 적용", key="apply_baseline"):
            st.session_state["baseline_met"] = new_bl
            save_user_data()
            st.toast(f"베이스라인을 {new_bl} MET-min으로 조정했어요.", icon="✅")
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

            # MET 수동 조정 — key에 종목명 포함 → 종목 바뀌면 위젯 리셋되어 자동값 반영
            safe_key = ex_name.replace(" ", "_").replace("/", "_")
            col_met, col_met_help = st.columns([2, 3])
            with col_met:
                c_met_custom = st.number_input(
                    "MET 값 (직접 조정 가능)", 0.5, 20.0, float(ex_met), 0.5,
                    key=f"c_met_{safe_key}",
                    help="종목 선택 시 자동 입력됩니다. 실제 강도에 맞게 조정 가능해요.")
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

            # 종목별 기본 MET (ACSM 2024)
            _STR_MET = {
                "🏋️ 웨이트 (머신)":             5.0,
                "🏋️ 웨이트 (프리웨이트)":        5.5,
                "💪 맨몸 운동 (푸시업·스쿼트 등)": 3.8,
                "🤸 케틀벨":                     8.0,
            }
            s_met_default = _STR_MET.get(s_selected, 5.0)
            s_safe_key    = s_name.replace(" ", "_").replace("/", "_")

            # MET 수동 조정 — key에 종목명 포함 → 종목 바뀌면 자동값으로 리셋
            col_met2, col_met2h = st.columns([2, 3])
            with col_met2:
                s_met_custom = st.number_input(
                    "MET 값 (직접 조정)", 0.5, 20.0, float(s_met_default), 0.5,
                    key=f"s_met_{s_safe_key}",
                    help="종목 선택 시 자동 입력됩니다. 조정 가능해요.")
            with col_met2h:
                st.markdown(
                    f"<p style='color:#64748b;font-size:12px;margin-top:28px;'>"
                    f"자동값: <b style='color:#2563EB;'>{s_met_default}</b> "
                    f"(ACSM 2024)</p>",
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

            # 종목별 기본 MET (ACSM 2024)
            _REC_MET = {
                "🧘 요가":     2.5,
                "🤸 스트레칭": 2.3,
                "🛁 냉온욕":   2.0,
                "🚶 가벼운 산책": 3.0,
            }
            r_met_default = _REC_MET.get(r_selected, 2.5)
            r_safe_key    = r_name.replace(" ", "_").replace("/", "_")

            # MET 수동 조정 — key에 종목명 포함 → 종목 바뀌면 자동값으로 리셋
            col_rmet, col_rmeth = st.columns([2, 3])
            with col_rmet:
                r_met_custom = st.number_input(
                    "MET 값 (직접 조정)", 0.5, 10.0, float(r_met_default), 0.5,
                    key=f"r_met_{r_safe_key}",
                    help="종목 선택 시 자동 입력됩니다. 조정 가능해요.")
            with col_rmeth:
                st.markdown(
                    f"<p style='color:#64748b;font-size:12px;margin-top:28px;'>"
                    f"자동값: <b style='color:#2563EB;'>{r_met_default}</b> "
                    f"(ACSM 2024)</p>",
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

            # [FIX 5] 오늘 날짜 운동 로그 중복 방지 → 있으면 업데이트, 없으면 추가
            today_iso = date.today().isoformat()
            existing  = next((i for i, l in enumerate(st.session_state["session_logs"])
                              if l.get("date") == today_iso and l.get("feedback") != "rest"), None)
            new_log = {
                "day": st.session_state.get("total_workouts", 0),
                "date": today_iso,
                "load": f_load, "met_min": f_met_min,
                "rpe": overall_rpe, "duration": f_dur,
                "entries": saved_entries, "notes": notes, "feedback": feedback,
            }
            if existing is not None:
                st.session_state["session_logs"][existing] = new_log
            else:
                st.session_state["session_logs"].append(new_log)
            st.session_state["total_workouts"]       = st.session_state.get("total_workouts", 0) + 1
            st.session_state["streak"]               = calc_streak(st.session_state["session_logs"])
            st.session_state["sleep_score"]          = None
            st.session_state["today_completed_date"] = date.today().isoformat()
            st.session_state["page"]                 = "main"
            st.session_state["wl_entries"]    = []
            st.session_state["wl_edit_idx"]   = -1
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
