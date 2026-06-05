import streamlit as st
import pickle
import numpy as np
import os

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
GLOBAL_AVG_REM       = 18.0
GLOBAL_AVG_DEEP      = 17.0
GLOBAL_AVG_HR_RESTING = 85.0

BASELINE_MET_ALL  = 2390   # 전체 포함
BASELINE_MET_1_2  = 1153   # 1.2 이하 제외
BASELINE_MET_3_0  = 766    # 3.0 미만 제외 (기본 기준)

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
                st.metric("전체 포함", f"{BASELINE_MET_ALL}")
            with col2:
                st.metric("1.2↑ 기준", f"{BASELINE_MET_1_2}")
            with col3:
                st.metric("3.0↑ 기준", f"{BASELINE_MET_3_0}")

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
            st.success("⌚ 어제 수면 데이터를 동기화했습니다.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("동기화 데이터로 처방받기", type="primary"):
                    import random
                    st.session_state["sleep_score"] = random.randint(75, 95)
                    st.rerun()
            with col2:
                if st.button("수동으로 입력하기"):
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
                    hist = st.session_state["user_history"]
                    pred_rem  = np.mean(hist["rem"])  if hist["rem"]  else GLOBAL_AVG_REM
                    pred_deep = np.mean(hist["deep"]) if hist["deep"] else GLOBAL_AVG_DEEP
                    pred_hr   = np.mean(hist["hr"])   if hist["hr"]   else GLOBAL_AVG_HR_RESTING

                    import pandas as pd
                    X = pd.DataFrame([[sleep_hours, pred_rem, pred_deep, pred_hr]],
                                     columns=["HOURS OF SLEEP_num", "REM SLEEP_num", "DEEP SLEEP_num", "HEART RATE UNDER RESTING_num"])
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
                    import pandas as pd
                    X = pd.DataFrame([[sleep_hours, rem_percent, deep_percent, hr_below]],
                                     columns=["HOURS OF SLEEP_num", "REM SLEEP_num", "DEEP SLEEP_num", "HEART RATE UNDER RESTING_num"])
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
    score = st.session_state["sleep_score"]
    if score >= 80:
        status, emoji, multiplier, msg = "좋음",   "🟢", 1.2, "컨디션이 좋아요. 오늘은 강도를 높여봐요!"
    elif score >= 50:
        status, emoji, multiplier, msg = "보통",   "🟡", 1.0, "평소대로 운동하면 좋아요."
    else:
        status, emoji, multiplier, msg = "주의",   "🔴", 0.5, "회복이 필요해요. 가볍게 움직여요."

    with st.container(border=True):
        st.markdown(f"#### {emoji} 회복 점수")
        st.metric("수면 점수 (ML 예측)", f"{score}점")
        st.progress(score / 100)
        st.markdown(f"<p style='color:#888;'>{msg}</p>", unsafe_allow_html=True)
        if st.button("다시 측정"):
            st.session_state["sleep_score"] = None
            st.rerun()

    st.write("")
    with st.container(border=True):
        target = int(st.session_state["baseline_met"] * multiplier)
        st.markdown(f"#### 🎯 오늘의 운동 처방")
        st.metric("목표 활동 부하 (MET)", f"{target}")
        st.markdown(f"<p style='color:#555; font-size:13px;'>기준 MET {st.session_state['baseline_met']} × {multiplier}</p>", unsafe_allow_html=True)

        st.write("")
        if st.button("✅ 운동 완료!", type="primary"):
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
