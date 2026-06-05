import streamlit as st
import random
import pickle
import numpy as np

# --- [앱 기본 설정 & CSS] ---
st.set_page_config(page_title="PACE MAKER", page_icon="🏃", layout="centered")
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 50px; }
        .stSelectbox, .stNumberInput, .stSlider { padding-bottom: 15px; }
        h1, h2, h3 { font-family: 'Pretendard', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# --- [글로벌 평균 데이터 (사진 데이터 및 기존 통계 기반)] ---
# 유저의 과거 데이터가 없을 때 ML 모델의 빈칸을 채워줄 기본값입니다.
GLOBAL_AVG_REM = 18.0
GLOBAL_AVG_DEEP = 17.0
GLOBAL_AVG_HR_RESTING = 85.0

# --- [세션 상태 초기화] ---
if 'onboarded' not in st.session_state: st.session_state['onboarded'] = False
if 'streak' not in st.session_state: st.session_state['streak'] = 0
if 'baseline_met' not in st.session_state: st.session_state['baseline_met'] = 300
if 'sleep_score' not in st.session_state: st.session_state['sleep_score'] = None
if 'use_watch' not in st.session_state: st.session_state['use_watch'] = False

# [핵심] 유저의 과거 수면 데이터 기록 (ML 결측치 보완용)
if 'user_history' not in st.session_state: 
    st.session_state['user_history'] = {'rem': [], 'deep': [], 'hr': []}

# --- [ML 모델 로드 함수] ---
@st.cache_resource
def load_ml_model():
    try:
        with open('sleep_model.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        st.error("🚨 'sleep_model.pkl' 파일을 찾을 수 없습니다! 같은 폴더에 넣어주세요.")
        return None

ml_model = load_ml_model()

# ==========================================
# 🚀 화면 1: 온보딩 (생략 - 이전과 동일)
# ==========================================
def show_onboarding():
    st.title("🏃 PACE MAKER")
    st.markdown("<p style='color: gray; margin-bottom: 30px;'>나만의 완벽한 운동 리듬을 찾아보세요.</p>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("⌚ 디바이스 연동")
        use_watch_input = st.radio("스마트워치를 사용 중이신가요?", ["사용합니다", "스마트폰만 사용합니다"])
    with st.container(border=True):
        st.subheader("💪 체력 베이스라인")
        fitness_level = st.select_slider("최근 1달간의 활동량을 알려주세요.", options=["숨쉬기 운동 (초보)", "가벼운 산책 (보통)", "주 3회 땀 흘림 (고수)"])
    st.write("") 
    if st.button("내 맞춤형 처방 시작하기", type="primary"):
        st.session_state['use_watch'] = True if "사용합니다" in use_watch_input else False
        st.session_state['baseline_met'] = 150 if "초보" in fitness_level else 350 if "보통" in fitness_level else 600
        st.session_state['onboarded'] = True
        st.rerun()

# ==========================================
# 🔄 화면 2: 메인 앱 (대시보드)
# ==========================================
def show_main_dashboard():
    with st.sidebar:
        st.subheader("🛠️ 개발자 테스트 도구")
        if st.button("⏭️ 다음 날 아침으로 가기"):
            st.session_state['sleep_score'] = None 
            st.rerun()

    col1, col2 = st.columns([3, 1])
    with col1: st.title(f"Day {st.session_state['streak']}")
    with col2: st.markdown(f"<h1 style='text-align: right; color: {'#4CAF50' if st.session_state['use_watch'] else '#FF9800'};'>{'⌚' if st.session_state['use_watch'] else '📱'}</h1>", unsafe_allow_html=True)
    st.progress(min(st.session_state['streak'] / 30, 1.0))
    st.write("")

    # --- [섹션 1: 컨디션 (수면) 체크 카드] ---
    if st.session_state['sleep_score'] is None:
        with st.container(border=True):
            st.subheader("🌙 좋은 아침입니다!")
            
            # 1. 워치 유저 분기 처리
            show_manual_input = True
            if st.session_state['use_watch']:
                st.success("⌚ 워치에서 어제 수면 데이터를 성공적으로 동기화했습니다! (추정치)")
                show_manual_input = False
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    if st.button("동기화된 데이터로 처방 받기", type="primary"):
                        # 워치 동기화 가정 (임의의 점수 생성)
                        st.session_state['sleep_score'] = random.randint(75, 95)
                        st.rerun()
                with col2:
                    if st.button("오류 수정 (수동 입력)"):
                        show_manual_input = True

            # 2. 수동 입력 폼 (워치 미사용자 OR 수정 버튼 누른 워치 사용자)
            if show_manual_input:
                st.markdown("---")
                input_mode = st.radio("입력 방식 선택", ["간편 입력 (추천)", "상세 입력 (ML 정확도 상승)"], horizontal=True)
                
                # --- A. 간편 입력 모드 ---
                if "간편" in input_mode:
                    col1, col2 = st.columns(2)
                    with col1:
                        sleep_hours = st.number_input("어젯밤 수면 (시간)", min_value=0.0, max_value=24.0, value=7.0, step=0.5, format="%.1f")
                    with col2:
                        subjective_feel = st.slider("기상 직후 개운함", 1, 5, 3, help="1: 최악, 5: 상쾌함")
                    
                    if st.button("ML 분석 실행 (간편)"):
                        # 결측치 채우기 로직 (과거 이력 우선 -> 없으면 글로벌 평균)
                        hist = st.session_state['user_history']
                        pred_rem = np.mean(hist['rem']) if hist['rem'] else GLOBAL_AVG_REM
                        pred_deep = np.mean(hist['deep']) if hist['deep'] else GLOBAL_AVG_DEEP
                        pred_hr = np.mean(hist['hr']) if hist['hr'] else GLOBAL_AVG_HR_RESTING
                        
                        if ml_model:
                            X_input = np.array([[sleep_hours, pred_rem, pred_deep, pred_hr]])
                            ml_score = ml_model.predict(X_input)[0]
                            # 주관적 피로도를 약간의 가중치로 반영
                            final_score = int(ml_score * (subjective_feel / 3.0)) 
                            st.session_state['sleep_score'] = min(max(final_score, 0), 100)
                            st.rerun()

                # --- B. 상세 입력 모드 ---
                else:
                    st.caption("핏빗 앱의 상세 데이터를 직접 입력하여 가장 정확한 점수를 예측합니다.")
                    col1, col2 = st.columns(2)
                    with col1:
                        sleep_hours = st.number_input("수면 시간", value=7.0, step=0.5, format="%.1f")
                        rem_percent = st.number_input("렘 수면 비율 (%)", value=18.0, step=1.0)
                    with col2:
                        deep_percent = st.number_input("깊은 수면 비율 (%)", value=17.0, step=1.0)
                        hr_below = st.number_input("안정시 심박수 이하 비율 (%)", value=85.0, step=1.0)
                    
                    if st.button("ML 분석 실행 (상세)", type="primary"):
                        if ml_model:
                            # 1. 모델 예측
                            X_input = np.array([[sleep_hours, rem_percent, deep_percent, hr_below]])
                            final_score = int(ml_model.predict(X_input)[0])
                            
                            # 2. 미래의 간편 입력을 위해 유저 히스토리에 디테일 데이터 저장
                            st.session_state['user_history']['rem'].append(rem_percent)
                            st.session_state['user_history']['deep'].append(deep_percent)
                            st.session_state['user_history']['hr'].append(hr_below)
                            
                            st.session_state['sleep_score'] = min(max(final_score, 0), 100)
                            st.rerun()
    else:
        # [처방 화면 - 이전과 동일하게 유지]
        score = st.session_state['sleep_score']
        status_emoji = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
        multiplier = 1.2 if score >= 80 else 0.8 if score >= 50 else 0.4
            
        with st.container(border=True):
            st.markdown(f"#### {status_emoji} 오늘의 회복 점수 (ML 예측): {score}점")
            st.progress(score / 100)
            if st.button("점수 재측정"):
                st.session_state['sleep_score'] = None
                st.rerun()

        st.write("")
        with st.container(border=True):
            st.subheader("🎯 오늘의 운동 미션")
            target_load = int(st.session_state['baseline_met'] * multiplier)
            st.metric(label="목표 활동 부하량", value=f"{target_load} MET")
            
            with st.expander("✅ 운동 완료 기록하기"):
                if st.button("수고하셨습니다! 미션 완료 👏", type="primary"):
                    st.session_state['streak'] += 1
                    st.session_state['sleep_score'] = None 
                    st.toast('기록 완료!', icon='🔥')
                    st.rerun()

if not st.session_state['onboarded']:
    show_onboarding()
else:
    show_main_dashboard()