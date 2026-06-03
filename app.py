import streamlit as st

# 1. 기계학습 모델의 가중치(Weight) 초기화 - 세션 상태 활용
if 'weight_sleep' not in st.session_state:
    st.session_state.weight_sleep = 1.0  # 수면에 대한 가중치
if 'weight_stress' not in st.session_state:
    st.session_state.weight_stress = -0.5 # 스트레스에 대한 가중치

st.set_page_config(page_title="수면·운동 페이스메이커", page_icon="🏃‍♂️")

st.title("수면·운동 페이스메이커 🏃‍♂️💤")
st.markdown("### Data-Driven Sleep & Exercise Pacemaker")
st.write("당신의 일상 데이터를 분석하여, 오버트레이닝을 방지하는 최적의 활동량을 처방합니다.")

# 2. 데이터 입력 폼 (UI 구조화)
with st.form("input_form"):
    st.subheader("📝 오늘의 컨디션 입력")
    sleep_hours = st.number_input("전날 수면 시간 (단위: 시간)", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
    stress_level = st.slider("오늘의 주관적 스트레스 지수 (1~10)", 1, 10, 5)
    submit_btn = st.form_submit_button("맞춤형 처방받기")

# 3. 처방 로직 (가상 임계점 계산 및 Go/No-Go 판정)
if submit_btn:
    st.divider()
    st.subheader("📊 분석 결과 및 처방")
    
    # 가중치가 반영된 현재 컨디션 점수 계산 (선형 회귀 시뮬레이션)
    condition_score = (sleep_hours * st.session_state.weight_sleep) + (stress_level * st.session_state.weight_stress)
    
    # 임계점에 따른 처방 분기
    if condition_score < 4.0: # No-Go 판정
        st.error(f"🚨 현재 피로도가 높습니다. (컨디션 점수: {condition_score:.2f})")
        st.write("**처방:** 오늘은 고강도 운동을 피하고, 15분 이내의 가벼운 스트레칭(MET 1.5~3.0)과 충분한 휴식을 권장합니다.")
    else: # Go 판정
        st.success(f"✅ 컨디션이 좋습니다! (컨디션 점수: {condition_score:.2f})")
        st.write("**처방:** 오늘의 회복 역량을 고려하여, 40분 이내의 중강도 운동(MET 4.0~5.0)을 진행해도 좋습니다.")

# 4. 피드백 루프 (모델 최적화 과정)
st.divider()
st.subheader("🔄 사용자 맞춤형 모델 학습")
st.write("처방에 따른 운동 수행 후, 실제 수면의 질을 입력해 주시면 모델이 개인에 맞춰 학습(업데이트)됩니다.")

with st.form("feedback_form"):
    actual_sleep_score = st.slider("실제 다음날 수면의 질은 어땠나요? (1~10점)", 1, 10, 5)
    feedback_btn = st.form_submit_button("피드백 제출 및 모델 업데이트")

if feedback_btn:
    # 아주 간단한 가중치 업데이트 시뮬레이션 (Learning rate 적용 느낌)
    if actual_sleep_score > 7:
        st.session_state.weight_sleep += 0.1
    else:
        st.session_state.weight_stress -= 0.1
        
    st.success("✅ 사용자 맞춤형 모델 학습 완료! 다음 처방부터 조정된 가중치가 반영됩니다.")