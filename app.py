import streamlit as st
import random

# --- [앱 기본 설정] ---
st.set_page_config(page_title="PACE MAKER", page_icon="🏃", layout="centered")

# --- [커스텀 CSS (사이드바 버튼 복구)] ---
# header 숨김 처리를 제거하여 좌측 상단 사이드바 열기(>) 버튼이 정상 작동하도록 수정했습니다.
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            font-weight: bold;
            height: 50px;
        }
        .stSelectbox, .stNumberInput, .stSlider {
            padding-bottom: 15px;
        }
        h1, h2, h3 {
            font-family: 'Pretendard', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
        }
    </style>
""", unsafe_allow_html=True)

# --- [세션 상태 초기화] ---
if 'onboarded' not in st.session_state:
    st.session_state['onboarded'] = False
if 'streak' not in st.session_state:
    st.session_state['streak'] = 0
if 'baseline_met' not in st.session_state:
    st.session_state['baseline_met'] = 300
if 'sleep_score' not in st.session_state:
    st.session_state['sleep_score'] = None
if 'use_watch' not in st.session_state:
    st.session_state['use_watch'] = False

# ==========================================
# 🚀 화면 1: 온보딩
# ==========================================
def show_onboarding():
    st.title("🏃 PACE MAKER")
    st.markdown("<p style='color: gray; margin-bottom: 30px;'>나만의 완벽한 운동 리듬을 찾아보세요.</p>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.subheader("⌚ 디바이스 연동")
        use_watch_input = st.radio(
            "스마트워치를 사용 중이신가요?", 
            ["사용합니다 (Apple Watch, Galaxy Fit 등)", "스마트폰만 사용합니다"]
        )
        
    with st.container(border=True):
        st.subheader("👤 프로필 설정")
        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("성별", ["남성", "여성", "선택안함"])
        with col2:
            age = st.number_input("나이", min_value=10, max_value=100, value=25)
            
    with st.container(border=True):
        st.subheader("💪 체력 베이스라인")
        fitness_level = st.select_slider(
            "최근 1달간의 활동량을 알려주세요.",
            options=["숨쉬기 운동 (초보)", "가벼운 산책 (보통)", "주 3회 땀 흘림 (고수)"]
        )
        
    with st.container(border=True):
        st.subheader("🎯 나의 목표")
        goal = st.radio("달성하고 싶은 목표를 선택하세요.", 
                        ["체지방 감량 및 체력 증진", "근육량 증가 및 바디프로필"])
        
    st.write("") # 여백
    if st.button("내 맞춤형 처방 시작하기", type="primary"):
        st.session_state['use_watch'] = True if "사용합니다" in use_watch_input else False
        
        if "초보" in fitness_level:
            st.session_state['baseline_met'] = 150
        elif "보통" in fitness_level:
            st.session_state['baseline_met'] = 350
        else:
            st.session_state['baseline_met'] = 600
            
        st.session_state['onboarded'] = True
        st.rerun()

# ==========================================
# 🔄 화면 2: 메인 앱 (대시보드)
# ==========================================
def show_main_dashboard():
    # --- [사이드바 (개발자 도구)] ---
    with st.sidebar:
        st.subheader("🛠️ 개발자 테스트 도구")
        if st.button("⏭️ 다음 날 아침으로 가기"):
            st.session_state['sleep_score'] = None 
            st.rerun()
        if st.button("🔄 데이터 초기화"):
            st.session_state.clear()
            st.rerun()

    # --- [앱 상단 헤더: 스트릭(연속 달성) UI] ---
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"Day {st.session_state['streak']}")
    with col2:
        if st.session_state['use_watch']:
            st.markdown("<h1 style='text-align: right; color: #4CAF50;'>⌚</h1>", unsafe_allow_html=True)
        else:
            st.markdown("<h1 style='text-align: right; color: #FF9800;'>📱</h1>", unsafe_allow_html=True)
            
    st.progress(min(st.session_state['streak'] / 30, 1.0))
    st.markdown("<p style='font-size: 0.8em; color: gray;'>30일 챌린지 진행 중 🔥</p>", unsafe_allow_html=True)
    st.write("")

    # --- [섹션 1: 컨디션 (수면) 체크 카드] ---
    if st.session_state['sleep_score'] is None:
        with st.container(border=True):
            st.subheader("🌙 좋은 아침입니다!")
            st.write("완벽한 처방을 위해 수면 컨디션을 기록해 주세요.")
            
            col1, col2 = st.columns(2)
            with col1:
                # [버그 수정됨] format에 문자를 빼고 '%.1f'만 남겼습니다. 단위는 라벨로 이동했습니다.
                sleep_hours = st.number_input("어젯밤 수면 (시간)", min_value=0.0, max_value=24.0, value=7.0, step=0.5, format="%.1f")
            with col2:
                subjective_feel = st.slider("기상 직후 개운함", 1, 5, 3, help="1: 최악, 5: 상쾌함")
            
            if st.button("컨디션 분석하기"):
                base_score = min(sleep_hours / 8.0, 1.0) * 100
                feel_modifier = subjective_feel / 5.0
                final_score = int(base_score * feel_modifier)
                st.session_state['sleep_score'] = final_score
                st.rerun()
    else:
        score = st.session_state['sleep_score']
        
        if score >= 80:
            status_emoji = "🟢"
            multiplier = 1.2
        elif score >= 50:
            status_emoji = "🟡"
            multiplier = 0.8
        else:
            status_emoji = "🔴"
            multiplier = 0.4
            
        with st.container(border=True):
            st.markdown(f"#### {status_emoji} 오늘의 회복 점수: {score}점")
            st.progress(score / 100)
            
            col1, col2, col3 = st.columns([1, 1, 1.5])
            with col3:
                if st.button("다시 입력", use_container_width=True):
                    st.session_state['sleep_score'] = None
                    st.rerun()

        # --- [섹션 2: 맞춤 운동 처방 카드] ---
        st.write("")
        with st.container(border=True):
            st.subheader("🎯 오늘의 운동 미션")
            target_load = int(st.session_state['baseline_met'] * multiplier)
            
            st.metric(label="목표 활동 부하량", value=f"{target_load} MET")
            
            st.divider()
            st.markdown("**💡 추천하는 운동 루틴**")
            
            if target_load < 100:
                st.info("🧘‍♀️ 휴식이 필요한 날입니다. 15분간 가벼운 스트레칭만 해주세요.")
            elif target_load < 300:
                st.success("🚶‍♂️ 빠른 걸음으로 40분 산책 또는 가벼운 자전거 타기를 추천합니다.")
            else:
                st.warning("🏃‍♂️ 에너지가 넘치는 날! 40분 러닝과 20분 근력 운동에 도전하세요!")
                
            st.write("")
            with st.expander("✅ 운동 완료 기록하기"):
                done_minutes = st.number_input("오늘 총 운동한 시간(분)", min_value=0, value=30, step=5)
                if st.button("수고하셨습니다! 미션 완료 👏", type="primary"):
                    st.session_state['streak'] += 1
                    st.session_state['sleep_score'] = None 
                    st.toast('운동 기록 완료! 내일도 화이팅입니다.', icon='🔥')
                    st.rerun()

        # --- [섹션 3: 건강 팁 카드] ---
        st.write("")
        with st.container(border=True):
            st.markdown("##### 📚 오늘의 1분 건강 상식")
            tips = [
                "수면이 부족한 날 고강도 운동을 하면 피로 물질이 훨씬 더 많이 쌓입니다.",
                "빠르게 걷기(MET 4.0~5.0)는 관절에 무리를 주지 않는 최고의 심폐 운동입니다.",
                "가장 강력한 피로 회복은 잠든 직후 첫 90분(Deep Sleep)에 일어납니다."
            ]
            st.caption(random.choice(tips))

# ==========================================
# 🎮 메인 라우터
# ==========================================
if not st.session_state['onboarded']:
    show_onboarding()
else:
    show_main_dashboard()