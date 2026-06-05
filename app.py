import streamlit as st
import pandas as pd
import datetime
import random

# --- [앱 기본 설정] ---
st.set_page_config(page_title="맞춤형 운동 페이스메이커", page_icon="🏃", layout="centered")

# --- [세션 상태(Session State) 초기화] ---
# 앱이 새로고침 되어도 데이터가 날아가지 않도록 상태를 저장합니다.
if 'onboarded' not in st.session_state:
    st.session_state['onboarded'] = False
if 'streak' not in st.session_state:
    st.session_state['streak'] = 1
if 'baseline_met' not in st.session_state:
    st.session_state['baseline_met'] = 300 # 기본 체력(부하량) 디폴트
if 'sleep_score' not in st.session_state:
    st.session_state['sleep_score'] = None
if 'prescription_done' not in st.session_state:
    st.session_state['prescription_done'] = False

# ==========================================
# 🚀 화면 1: 온보딩 (최초 실행 시 사용자 데이터 입력)
# ==========================================
def show_onboarding():
    st.title("👋 환영합니다! 당신만의 페이스메이커입니다.")
    st.write("스마트워치 없이도 완벽한 맞춤형 운동 처방을 시작해 보세요.")
    
    with st.form("onboarding_form"):
        st.subheader("1. 기본 정보 입력")
        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("성별", ["남성", "여성", "선택안함"])
        with col2:
            age = st.number_input("나이", min_value=10, max_value=100, value=25)
            
        st.subheader("2. 평소 체력 수준 (Baseline)")
        st.write("최근 한 달간의 평균적인 활동량을 알려주세요.")
        fitness_level = st.select_slider(
            "나의 체력은?",
            options=["숨쉬기 운동만 함 (초보)", "가벼운 산책을 즐김 (보통)", "주 3회 이상 땀흘려 운동함 (고수)"]
        )
        
        st.subheader("3. 주요 목표")
        goal = st.radio("운동을 통해 이루고 싶은 목표는 무엇인가요?", 
                        ["다이어트 및 일상 체력 향상", "근육량 증가 및 몸 가꾸기"])
        
        submit_button = st.form_submit_button(label="내 맞춤형 처방 시작하기")
        
        if submit_button:
            # 체력 수준을 우리가 논의했던 MET 부하량 숫자로 치환하여 저장
            if "초보" in fitness_level:
                st.session_state['baseline_met'] = 150
            elif "보통" in fitness_level:
                st.session_state['baseline_met'] = 350
            else:
                st.session_state['baseline_met'] = 600
                
            st.session_state['goal'] = goal
            st.session_state['onboarded'] = True
            st.rerun() # 메인 화면으로 즉시 전환

# ==========================================
# 🔄 화면 2: 메인 루프 (대시보드)
# ==========================================
def show_main_dashboard():
    # --- [상단: 우선순위 2 - 연속 달성 캘린더/Day] ---
    st.sidebar.title("🔥 달성 기록")
    st.sidebar.metric(label="연속 운동 일수", value=f"Day {st.session_state['streak']}")
    st.sidebar.progress(min(st.session_state['streak'] / 30, 1.0))
    st.sidebar.write("30일 챌린지를 향해 달려보세요!")

    st.title("오늘의 맞춤형 운동 처방 📋")
    
    # --- [우선순위 1: 수면 데이터 및 주관적 컨디션 입력 (회복도)] ---
    st.header("1. 오늘의 컨디션은 어떠신가요? 🛌")
    if st.session_state['sleep_score'] is None:
        with st.form("sleep_form"):
            st.write("운동 처방을 위해 어젯밤 수면 상태를 알려주세요.")
            col1, col2 = st.columns(2)
            with col1:
                sleep_hours = st.number_input("어제 수면 시간 (시간)", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
            with col2:
                subjective_feel = st.slider("주관적인 피로도 (1: 최악 ~ 5: 개운함)", 1, 5, 3)
            
            calc_button = st.form_submit_button("컨디션 분석하기")
            
            if calc_button:
                # 간단한 수면 점수 계산 로직 (실제로는 여기에 모델이 들어감)
                # 수면 시간(최대 8시간=1.0) * 주관적 피로도 비율
                base_score = min(sleep_hours / 8.0, 1.0) * 100
                feel_modifier = subjective_feel / 5.0
                final_score = int(base_score * feel_modifier)
                
                st.session_state['sleep_score'] = final_score
                st.rerun()
    else:
        # 이미 입력한 경우 점수 보여주기
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
            
        st.button("수면 데이터 다시 입력하기", on_click=lambda: st.session_state.update(sleep_score=None))

        st.divider()

        # --- [우선순위 2(핵심): 운동 처방 제안] ---
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
            
        # 운동 완료 기록 (수동 입력)
        with st.expander("✅ 운동을 완료하셨나요? (기록하기)"):
            done_minutes = st.number_input("오늘 총 운동한 시간(분)", min_value=0, value=30)
            if st.button("운동 완료 기록하기"):
                st.session_state['streak'] += 1
                st.session_state['sleep_score'] = None # 내일(다음 루프)을 위해 초기화
                # 실제로는 여기서 done_minutes를 바탕으로 baseline_met을 업데이트 (피드백 루프)
                st.success("훌륭합니다! 오늘의 운동이 기록되었습니다. 내일 뵙겠습니다!")
                st.balloons()
                
        st.divider()

        # --- [우선순위 3: 운동 관련 흥미로운 정보 제공] ---
        st.header("3. 오늘의 1분 건강 상식 📚")
        tips = [
            "수면이 부족한 날 고강도 운동을 하면 코르티솔 분비가 늘어나 오히려 근육이 분해될 수 있습니다.",
            "빠르게 걷기(MET 4.0~5.0)는 관절에 무리를 주지 않으면서도 훌륭한 심폐지구력 향상 효과를 가져옵니다.",
            "운동 후 30분 이내에 단백질과 적절한 탄수화물을 섭취하면 근육 회복 속도가 2배 빨라집니다."
        ]
        st.info(random.choice(tips))


# ==========================================
# 🎮 메인 라우터 (앱 실행 흐름 제어)
# ==========================================
if not st.session_state['onboarded']:
    show_onboarding()
else:
    show_main_dashboard()