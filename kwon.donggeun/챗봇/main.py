import streamlit as st

st.set_page_config(
    page_title='OTT 이탈 방지 시스템',
    page_icon='📺',
    layout='centered'
)

st.title('📺 OTT 이탈 방지 AI 시스템')
st.caption('권동근 | 2026.05')

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('### 💬 고객 상담')
    st.caption('고객이 직접 AI 상담사와 대화\n이탈 방지 혜택 자동 제안')
    if st.button('상담 시작하기', use_container_width=True, type='primary'):
        st.switch_page('pages/1_고객상담.py')

with col2:
    st.markdown('### 🛡️ 이탈 방지 AI')
    st.caption('고위험 고객 탐색\n맞춤 개입 전략 생성')
    if st.button('분석 시작하기', use_container_width=True):
        st.switch_page('pages/2_이탈방지.py')

with col3:
    st.markdown('### 🤖 AI 에이전트')
    st.caption('자연어 명령으로\n자동 분석 + 엑셀 저장')
    if st.button('에이전트 시작하기', use_container_width=True):
        st.switch_page('pages/3_에이전트.py')

st.divider()

st.markdown('**프로젝트 개요**')
c1, c2, c3, c4 = st.columns(4)
c1.metric('분석 구독자', '23,343명')
c2.metric('이탈률', '28.4%')
c3.metric('모델 AUC', '0.8826')
c4.metric('관측창', '21일')
