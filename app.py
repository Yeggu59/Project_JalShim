import streamlit as st
import random

# --- [앱 기본 설정] ---
st.set_page_config(page_title="맞춤형 운동 페이스메이커", page_icon="🏃", layout="centered")

# --- [세션 상태(Session State) 초기화] ---
if 'onboarded' not in st.session_state:
    st.session_state['onboarded'] = False
if 'streak' not in st.session_state:
    st.session_state['streak'] = 0 # 0일부터 시작
if 'baseline_met' not in st.session_state:
    st.session_state['baseline_met'] = 300
if 'sleep_score' not in st.session_state:
    st.session_state['sleep_score'] = None
if 'use_watch' not in st.session_state:
    st.session_state['use_watch'] = False # 워치 사용 여부 저장

# ==========================================
# 🚀 화면 1: 온보딩
# ==========================================
def show_onboarding():
    st.title("👋 환영합니다! 당신만의 페이스메이커입니다.")
    
    with st.form("onboarding_form"):
        # [추가됨] 0. 워치 사용 여부 확인
        st.subheader("0. 스마트 기기 연동")
        use_watch_input = st.radio(
            "스마트워치(핏빗, 애플워치, 갤럭시워치 등)를 사용하시나요?", 
            ["예, 사용합니다.", "아니오, 스마트폰만 사용합니다."]
        )
        
        st.subheader("1. 기본 정보 입력")
        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("성별", ["남성", "여성", "선택안함"])
        with col2:
            age = st.number_input("나이", min_value=10, max_value=100, value=25)
            
        st.subheader("2. 평소 체력 수준 (Baseline)")
        fitness_level = st.select_slider(
            "최근 한 달간의 평균적인 활동량을 알려주세요.",
            options=["숨쉬기 운동만 함 (초보)", "가벼운 산책을 즐김 (보통)", "주 3회 이상 땀흘려 운동함 (고수)"]
        )
        
        st.subheader("3. 주요 목표")
        goal = st.radio("운동을 통해 이루고 싶은 목표는 무엇인가요?", 
                        ["다이어트 및 일상 체력 향상", "근육량 증가 및 몸 가꾸기"])
        
        submit_button = st.form_submit_button(label="내 맞춤형 처방 시작하기")
        
        if submit_button:
            # 워치 사용 여부 저장
            st.session_state['use_watch'] = True if "예" in use_watch_input else False
            
            # 체력 수준을 MET 부하량으로 치환
            if "초보" in fitness_level:
                st.session_state['baseline_met'] = 150
            elif "보통" in fitness_level:
                st.session_state['baseline_met'] = 350
            else:
                st.session_state['baseline_met'] = 600
                
            st.session_state['onboarded'] = True
            st.rerun()

# ==========================================
# 🔄 화면 2: 메인 루프 (대시보드)
# ==========================================
def show_main_dashboard():
    # --- [사이드바: 상태 및 테스트 도구] ---
    st.sidebar.title("🔥 챌린지 기록")
    st.sidebar.metric(label="누적 운동 완료", value=f"{st.session_state['streak']} 일")
    
    st.sidebar.divider()
    
    # [추가됨] 루프 테스트용 건너뛰기 버튼
    st.sidebar.subheader("🛠️ 테스트 도구")
    st.sidebar.caption("개발 및 시연을 위한 시간 감기 기능입니다.")
    if st.sidebar.button("⏭️ 다음 날 아침으로 가기"):
        st.session_state['sleep_score'] = None # 수면 점수 초기화 = 새로운 하루 시작
        st.rerun()

    # --- [메인 화면 시작] ---
    st.title("오늘의 맞춤형 운동 처방 📋")
    
    # [추가됨] 워치 사용 여부에 따른 분기 처리 예시
    if st.session_state['use_watch']:
        st.info("⌚ 스마트워치 유저시군요! 자동 동기화 기능은 준비 중이므로 임시로 수동 입력해 주세요.")
    else:
        st.info("📱 수동 입력 모드입니다. 오늘 아침의 컨디션을 기록해 주세요.")

    # --- [1. 수면 데이터 및 컨디션 입력] ---
    st.header("1. 오늘의 컨디션은 어떠신가요? 🛌")
    
    if st.session_state['sleep_score'] is None:
        with st.form("sleep_form"):
            col1, col2 = st.columns(2)
            with col1:
                sleep_hours = st.number_input("어제 수면 시간 (시간)", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
            with col2:
                subjective_feel = st.slider("주관적인 피로도 (1: 최악 ~ 5: 개운함)", 1, 5, 3)
            
            calc_button = st.form_submit_button("컨디션 분석하기")
            
            if calc_button:
                # 간단한 수면 점수 계산 로직
                base_score = min(sleep_hours / 8.0, 1.0) * 100
                feel_modifier = subjective_feel / 5.0
                final_score = int(base_score * feel_modifier)
                st.session_state['sleep_score'] = final_score
                st.rerun()
    else:
        # 컨디션 입력 완료 시 보여지는 화면
        score = st.session_state['sleep_score']
        if score >= 80:
            st.success(f"🟢 오늘의 수면 점수: {score}점 (최상의 컨디션!)")
            multiplier = 1.2
        elif score >= 50:
            st.warning(f"🟡 오늘의 수면 점수: {score}점 (약간의 피로 누적)")
            multiplier = 0.8
        else:
            st.error(f"🔴 오늘의 수면 점수: {score}점 (휴식이 필요한 상태)")
            multiplier = 0.4

        st.divider()

        # --- [2. 운동 처방 제안] ---
        st.header("2. 오늘의 맞춤 운동 처방 🎯")
        target_load = int(st.session_state['baseline_met'] * multiplier)
        
        st.metric("오늘의 목표 운동 부하량 (MET-minutes)", value=f"{target_load} MET")
        
        st.write("💡 **이 부하량을 채우기 위한 추천 운동:**")
        if target_load < 100:
            st.info("가벼운 스트레칭 15분 또는 요가 20분 (MET 2.0)")
        elif target_load < 300:
            st.info("빠른 걷기 40분 (MET 4.0) 또는 가벼운 실내 자전거 30분 (MET 5.0)")
        else:
            st.info("러닝머신(가볍게 뛰기) 40분 (MET 8.0) + 웨이트 트레이닝 20분")
            
        # 운동 완료 기록
        with st.expander("✅ 운동을 완료하셨나요? (기록하기)"):
            done_minutes = st.number_input("오늘 총 운동한 시간(분)", min_value=0, value=30)
            if st.button("운동 완료 기록하기"):
                st.session_state['streak'] += 1
                st.session_state['sleep_score'] = None # 내일을 위해 초기화
                st.success(f"훌륭합니다! 누적 {st.session_state['streak']}일째 운동을 완료하셨습니다. (사이드바에서 다음날로 이동해보세요)")
                st.balloons()
                
        st.divider()

        # --- [3. 흥미로운 정보 제공] ---
        st.header("3. 오늘의 1분 건강 상식 📚")
        tips = [
            "수면이 부족한 날 고강도 운동을 하면 오히려 코르티솔이 분비되어 피로가 심해집니다.",
            "빠르게 걷기(MET 4.0~5.0)는 관절에 무리를 주지 않으면서도 훌륭한 심폐지구력 향상 효과를 가져옵니다.",
            "수면 중 가장 회복이 많이 일어나는 시간은 잠든 직후 90분 사이의 깊은 수면(Deep Sleep) 구간입니다."
        ]
        st.info(random.choice(tips))

# ==========================================
# 🎮 메인 라우터
# ==========================================
if not st.session_state['onboarded']:
    show_onboarding()
else:
    show_main_dashboard()