"""
OTT 이탈 방지 Multi-Agent System
빌드일: 2026-05-12
아키텍처: LangGraph + Gemini + XGBoost + SHAP

[흐름]
START → Supervisor → Data Analyst → Explainer → Retention Strategist → Action Executor → END

[State]
customer_id, customer_data, churn_prob, shap_values,
risk_level, risk_explanation, strategies, final_messages, action_log
"""

import os
import warnings
warnings.filterwarnings('ignore')

import json
import numpy as np
import pandas as pd
import streamlit as st
import xgboost as xgb
import shap
from pathlib import Path
from typing import TypedDict, Annotated, List
from datetime import datetime
from dotenv import load_dotenv

from google import genai as google_genai
from langgraph.graph import StateGraph, END, START

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

load_dotenv()

# ── 설정 ─────────────────────────────────────────────────────────────────────
BASE      = Path(__file__).parent.parent
DATA_PATH = BASE / '_data/02_interim/260510_features/Membership_features_clean.csv'
GEMINI    = 'gemini-1.5-flash'
SEED      = 42
EXCLUDE   = ['USER_KEY','product_code','payment_device','device_group',
             'gender','age_group','is_repurchase']

# ── State 정의 ────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    customer_id:      str
    customer_data:    dict
    churn_prob:       float
    shap_top:         list        # [(변수명, shap값, 실제값), ...]
    risk_level:       str         # high / medium / low
    risk_explanation: str
    strategies:       list        # 리텐션 전략 목록
    final_messages:   dict        # {A안, B안}
    action_log:       list        # 실행 기록
    messages:         list        # LLM 메시지 히스토리

# ── 데이터 & 모델 (캐시) ──────────────────────────────────────────────────────
@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH, encoding='utf-8-sig')

@st.cache_resource
def train_model():
    df = load_data().copy()
    for col in df.select_dtypes('object').columns:
        if col not in EXCLUDE:
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))
    FEAT = [c for c in df.columns if c not in EXCLUDE]
    X, y = df[FEAT].fillna(0), df['is_repurchase']
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
    spw = (y_tr==0).sum() / (y_tr==1).sum()
    model = xgb.XGBClassifier(
        n_estimators=500, learning_rate=0.05, max_depth=6,
        scale_pos_weight=spw, subsample=0.8, colsample_bytree=0.8,
        eval_metric='logloss', early_stopping_rounds=50,
        random_state=SEED, n_jobs=-1, verbosity=0
    )
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)
    explainer = shap.TreeExplainer(model)
    return model, explainer, FEAT

def age_label(age):
    if age < 20: return '10대'
    elif age < 30: return '20대'
    elif age < 40: return '30대'
    elif age < 50: return '40대'
    return '50대+'

# ── 툴 함수 ───────────────────────────────────────────────────────────────────
def get_customer_data(customer_id: str) -> dict:
    df = load_data()
    matches = df[df['USER_KEY'].astype(str).str.contains(customer_id, na=False)]
    if len(matches) == 0:
        return {}
    return matches.iloc[0].to_dict()

def predict_and_explain(customer_data: dict) -> tuple:
    model, explainer, FEAT = train_model()
    df_enc = load_data().copy()
    for col in df_enc.select_dtypes('object').columns:
        if col not in EXCLUDE:
            df_enc[col] = LabelEncoder().fit_transform(df_enc[col].astype(str))
    X_all = df_enc[FEAT].fillna(0)

    uk = customer_data.get('USER_KEY', '')
    df_raw = load_data()
    idx = df_raw[df_raw['USER_KEY'].astype(str).str.contains(str(uk)[:10], na=False)].index
    if len(idx) == 0:
        return 0.5, []
    X_cust = X_all.loc[idx[0]:idx[0]]

    churn_prob = 1 - model.predict_proba(X_cust)[0, 1]
    shap_vals  = explainer.shap_values(X_cust)[0]

    shap_df = pd.DataFrame({'변수': FEAT, 'SHAP': shap_vals, '값': X_cust.iloc[0].values})
    shap_df['abs'] = shap_df['SHAP'].abs()
    top5 = shap_df.nlargest(5, 'abs')
    shap_top = [(r['변수'], round(r['SHAP'], 4), round(r['값'], 2)) for _, r in top5.iterrows()]
    return churn_prob, shap_top

PERSONA_OFFERS = {
    '10대':  ['친구 초대 시 둘 다 1개월 무료', '인기 아이돌 독점 콘텐츠 알림'],
    '20대':  ['다음 달 구독료 50% 할인', '드라마 신작 3편 무료 미리보기'],
    '30대':  ['가족 요금제 첫 달 무료 체험', '바쁜 직장인 맞춤 이어보기 큐레이션'],
    '40대':  ['프리미엄 요금제 1개월 무료', '가족 4인 공유 요금제 안내'],
    '50대+': ['구독 시 포인트 5,000점 적립', '가족 요금제 + 전화 상담 연결'],
}

# ══════════════════════════════════════════════════════════════════════════════
# AGENT NODES
# ══════════════════════════════════════════════════════════════════════════════

def supervisor_node(state: AgentState) -> AgentState:
    """고객 데이터 조회 + 이탈 확률 계산 → 위험도 분류"""
    log = state.get('action_log', [])
    log.append(f'[{datetime.now().strftime("%H:%M:%S")}] Supervisor: 고객 조회 시작')

    data = get_customer_data(state['customer_id'])
    if not data:
        return {**state, 'action_log': log, 'risk_level': 'unknown',
                'customer_data': {}, 'churn_prob': 0.0, 'shap_top': []}

    churn_prob, shap_top = predict_and_explain(data)

    if churn_prob >= 0.7:   risk = 'high'
    elif churn_prob >= 0.4: risk = 'medium'
    else:                   risk = 'low'

    log.append(f'[{datetime.now().strftime("%H:%M:%S")}] Supervisor: 이탈확률 {churn_prob:.1%} → {risk} 위험')
    return {**state, 'customer_data': data, 'churn_prob': churn_prob,
            'shap_top': shap_top, 'risk_level': risk, 'action_log': log}


def explainer_node(state: AgentState) -> AgentState:
    """SHAP 값 → 자연어 위험 설명 생성 (Gemini)"""
    log = state['action_log']
    log.append(f'[{datetime.now().strftime("%H:%M:%S")}] Explainer: 이탈 원인 분석 중')

    api_key = os.getenv('GEMINI_API_KEY', st.session_state.get('gemini_key', ''))
    client  = google_genai.Client(api_key=api_key)

    data  = state['customer_data']
    age   = int(data.get('age', 30))
    shap_text = '\n'.join([f'- {v}: {val:.2f} (값={rv})' for v, val, rv in state['shap_top']])

    prompt = f"""OTT 이탈 분석 전문가. 아래 SHAP 분석 결과를 바탕으로
이 고객이 왜 이탈할 것 같은지 2~3문장으로 설명하세요. 수치 언급 금지, 자연어로만.

고객: {age}세 ({age_label(age)}) | 이탈확률: {state['churn_prob']:.1%}
SHAP 주요 원인:
{shap_text}"""

    resp = client.models.generate_content(model=GEMINI, contents=prompt)
    log.append(f'[{datetime.now().strftime("%H:%M:%S")}] Explainer: 분석 완료')
    return {**state, 'risk_explanation': resp.text, 'action_log': log}


def retention_strategist_node(state: AgentState) -> AgentState:
    """연령/장르/위험도 기반 리텐션 전략 생성 (Gemini)"""
    log = state['action_log']
    log.append(f'[{datetime.now().strftime("%H:%M:%S")}] Retention Strategist: 전략 수립 중')

    api_key = os.getenv('GEMINI_API_KEY', st.session_state.get('gemini_key', ''))
    llm = ChatGoogleGenerativeAI(model=GEMINI, google_api_key=api_key, temperature=0.5)

    data     = state['customer_data']
    age      = int(data.get('age', 30))
    age_grp  = age_label(age)
    offers   = PERSONA_OFFERS.get(age_grp, ['구독료 30% 할인'])

    # 장르 파악
    genre_map = {'drama_ratio':'드라마','family_ratio':'패밀리','romance_ratio':'로맨스',
                 'thriller_ratio':'스릴러','horror_ratio':'공포','action_ratio':'액션'}
    genres = sorted([(v, data.get(k, 0)) for k, v in genre_map.items()],
                    key=lambda x: x[1], reverse=True)
    top_genres = [g for g, v in genres if v > 0.05][:2]

    prompt = f"""OTT 리텐션 전략가. 아래 고객에게 맞는 전략 3가지를 JSON 배열로만 반환하세요.
다른 설명 없이 JSON만: ["전략1", "전략2", "전략3"]

고객: {age}세 {age_grp} | 위험도: {state['risk_level']} | 장르: {', '.join(top_genres) or '없음'}
이탈 원인: {state['risk_explanation'][:100]}
제공 가능 혜택: {', '.join(offers)}"""

    api_key2 = os.getenv('GEMINI_API_KEY', st.session_state.get('gemini_key', ''))
    client2  = google_genai.Client(api_key=api_key2)
    resp = client2.models.generate_content(model=GEMINI, contents=prompt)
    try:
        import re
        arr = re.search(r'\[.*\]', resp.text, re.DOTALL)
        strategies = json.loads(arr.group()) if arr else offers
    except:
        strategies = offers

    log.append(f'[{datetime.now().strftime("%H:%M:%S")}] Retention Strategist: {len(strategies)}개 전략 수립')
    return {**state, 'strategies': strategies, 'action_log': log}


def action_executor_node(state: AgentState) -> AgentState:
    """최종 문자 메시지 A/B 생성 + 실행 (Mock)"""
    log = state['action_log']
    log.append(f'[{datetime.now().strftime("%H:%M:%S")}] Action Executor: 메시지 생성 중')

    api_key = os.getenv('GEMINI_API_KEY', st.session_state.get('gemini_key', ''))
    client3 = google_genai.Client(api_key=api_key)

    data    = state['customer_data']
    age_grp = age_label(int(data.get('age', 30)))
    strats  = '\n'.join([f'- {s}' for s in state['strategies'][:2]])

    prompt = f"""{age_grp} 고객에게 보낼 이탈 방지 문자 2가지를 작성하세요.

전략:
{strats}

형식 (정확히):
A안: (혜택 강조, 70자 이내)
B안: (감성형, 70자 이내)"""

    resp = client3.models.generate_content(model=GEMINI, contents=prompt)
    raw  = resp.text

    import re
    a = re.search(r'A안[:\s]+(.*?)(?=B안|$)', raw, re.DOTALL)
    b = re.search(r'B안[:\s]+(.*?)$', raw, re.DOTALL)
    sms_a = a.group(1).strip() if a else raw.strip()
    sms_b = b.group(1).strip() if b else ''

    final = {'A안': sms_a, 'B안': sms_b}

    # Mock 발송 로그
    log.append(f'[{datetime.now().strftime("%H:%M:%S")}] Action Executor: 문자 생성 완료')
    log.append(f'[{datetime.now().strftime("%H:%M:%S")}] [MOCK] 문자 발송 시뮬레이션 완료')

    return {**state, 'final_messages': final, 'action_log': log}


def skip_node(state: AgentState) -> AgentState:
    """저위험 고객 — 분석 스킵"""
    log = state.get('action_log', [])
    log.append(f'[{datetime.now().strftime("%H:%M:%S")}] 저위험 고객 — 개입 불필요')
    return {**state, 'action_log': log,
            'risk_explanation': '이탈 위험이 낮아 별도 개입이 필요하지 않습니다.',
            'strategies': [], 'final_messages': {}}


# ── 라우팅 ────────────────────────────────────────────────────────────────────
def route_by_risk(state: AgentState) -> str:
    if state['risk_level'] == 'unknown': return 'skip'
    if state['risk_level'] == 'low':     return 'skip'
    return 'explainer'

# ── 그래프 빌드 ────────────────────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node('supervisor',  supervisor_node)
    graph.add_node('explainer',   explainer_node)
    graph.add_node('strategist',  retention_strategist_node)
    graph.add_node('executor',    action_executor_node)
    graph.add_node('skip',        skip_node)

    graph.add_edge(START, 'supervisor')
    graph.add_conditional_edges('supervisor', route_by_risk, {
        'explainer': 'explainer',
        'skip':      'skip',
    })
    graph.add_edge('explainer',  'strategist')
    graph.add_edge('strategist', 'executor')
    graph.add_edge('executor',   END)
    graph.add_edge('skip',       END)

    return graph.compile()

# ── Streamlit UI ──────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title='LangGraph 이탈 방지 에이전트', page_icon='🔗', layout='wide')
    st.title('🔗 OTT 이탈 방지 Multi-Agent (LangGraph)')
    st.caption('Supervisor → Explainer → Retention Strategist → Action Executor')

    with st.sidebar:
        st.header('⚙️ 설정')
        api_key = st.text_input('Gemini API Key', value=os.getenv('GEMINI_API_KEY', ''),
                                type='password', placeholder='AIza...')
        if api_key:
            st.session_state['gemini_key'] = api_key
            os.environ['GEMINI_API_KEY']   = api_key

        st.divider()
        st.markdown('**에이전트 흐름**')
        st.markdown('''
```
START
  ↓
🎯 Supervisor
  이탈확률 계산 + 위험도 분류
  ↓ (고/중위험)        ↓ (저위험)
🔍 Explainer        ⏭️ Skip
  SHAP → 자연어
  ↓
💡 Retention Strategist
  맞춤 전략 3가지
  ↓
📨 Action Executor
  문자 A/B 생성
  ↓
END
```''')

    if not api_key:
        st.info('👈 Gemini API Key를 입력하세요')
        st.stop()

    with st.spinner('모델 로딩 중...'):
        train_model()

    st.subheader('고객 분석')

    col1, col2 = st.columns([3, 1])
    customer_id = col1.text_input('USER_KEY (앞 10자리)', placeholder='7a6960912b')

    if col2.button('🎲 랜덤', use_container_width=True):
        df = load_data()
        model, _, FEAT = train_model()
        df_enc = df.copy()
        for c in df_enc.select_dtypes('object').columns:
            if c not in EXCLUDE:
                df_enc[c] = LabelEncoder().fit_transform(df_enc[c].astype(str))
        probs = 1 - model.predict_proba(df_enc[FEAT].fillna(0))[:, 1]
        idx = np.random.choice(np.where(probs > 0.6)[0])
        st.session_state['cid'] = str(df.iloc[idx]['USER_KEY'])[:12]
        st.rerun()

    if 'cid' in st.session_state:
        customer_id = st.session_state['cid']
        st.info(f'선택된 고객: `{customer_id}`')

    if st.button('🚀 에이전트 실행', type='primary', use_container_width=True) and customer_id:
        graph = build_graph()
        init_state = AgentState(
            customer_id=customer_id, customer_data={},
            churn_prob=0.0, shap_top=[], risk_level='',
            risk_explanation='', strategies=[], final_messages={},
            action_log=[], messages=[]
        )

        with st.spinner('에이전트 실행 중...'):
            result = graph.invoke(init_state)

        # 결과 출력
        st.divider()

        # 메트릭
        c1, c2, c3 = st.columns(3)
        risk_emoji = {'high':'🔴', 'medium':'🟡', 'low':'🟢'}.get(result['risk_level'], '⚪')
        c1.metric('이탈 확률', f"{result['churn_prob']:.1%}")
        c2.metric('위험 등급', f"{risk_emoji} {result['risk_level'].upper()}")
        c3.metric('나이', f"{int(result['customer_data'].get('age', 0))}세")

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown('**🔍 이탈 원인 분석**')
            st.info(result['risk_explanation'])

            st.markdown('**📊 SHAP Top 5**')
            for var, val, rv in result['shap_top']:
                direction = '⬇️ 이탈' if val < 0 else '⬆️ 재구매'
                st.write(f'`{var}` = {rv} → {direction}')

        with col_b:
            if result['strategies']:
                st.markdown('**💡 리텐션 전략**')
                for i, s in enumerate(result['strategies'], 1):
                    st.write(f'{i}. {s}')

            if result['final_messages']:
                st.markdown('**📨 발송 문자**')
                if result['final_messages'].get('A안'):
                    st.success(f"**A안 (혜택강조)**\n{result['final_messages']['A안']}")
                if result['final_messages'].get('B안'):
                    st.info(f"**B안 (감성형)**\n{result['final_messages']['B안']}")

        # 실행 로그
        with st.expander('📋 에이전트 실행 로그'):
            for log in result['action_log']:
                st.text(log)


if __name__ == '__main__':
    main()
