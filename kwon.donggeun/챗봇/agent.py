import os
import io
import json
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import streamlit as st
import xgboost as xgb
import shap
from groq import Groq
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score
from dotenv import load_dotenv

load_dotenv()

# ── 설정 ────────────────────────────────────────────────────────────────────
BASE       = Path(__file__).parent.parent
DATA_PATH  = BASE / '_data/02_interim/260510_features/Membership_features_clean.csv'
MEM_PATH   = BASE / '_data/02_interim/260510_merged_v2/Membership_v2.csv'
REPORT_DIR = Path(__file__).parent / 'reports'
REPORT_DIR.mkdir(exist_ok=True)

GROQ_MODEL = 'llama-3.1-8b-instant'
SEED       = 42
EXCLUDE    = ['USER_KEY','product_code','payment_device','device_group',
              'gender','age_group','is_repurchase']

# ── 데이터 & 모델 (캐시) ─────────────────────────────────────────────────────
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

@st.cache_data
def compute_all_probs():
    df = load_data().copy()
    model, _, FEAT = train_model()
    for col in df.select_dtypes('object').columns:
        if col not in EXCLUDE:
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))
    df['이탈확률'] = model.predict_proba(df[FEAT].fillna(0))[:, 0]
    return df

def decode_date(s):
    parts = str(s).split('-')
    return pd.Timestamp(year=2000+int(parts[2]), month=int(parts[1]), day=int(parts[0][2:]))

@st.cache_data
def load_membership_dates():
    df = pd.read_csv(MEM_PATH, encoding='utf-8-sig', usecols=['USER_KEY','reg_date'])
    df['reg_date_decoded'] = df['reg_date'].apply(decode_date)
    return df[['USER_KEY','reg_date_decoded']]

def age_group_label(age):
    if age < 20:   return '10대'
    elif age < 30: return '20대'
    elif age < 40: return '30대'
    elif age < 50: return '40대'
    else:          return '50대+'

def get_top_genres(customer):
    genre_map = {
        'drama_ratio':'드라마','family_ratio':'패밀리','romance_ratio':'로맨스',
        'thriller_ratio':'스릴러','horror_ratio':'공포','action_ratio':'액션'
    }
    genres = {v: customer.get(k, 0) for k, v in genre_map.items()}
    return sorted(genres.items(), key=lambda x: x[1], reverse=True)[:2]

# ── 에이전트 도구 함수 ─────────────────────────────────────────────────────────
def tool_get_high_risk_customers(n: int = 10, min_prob: float = 0.5, date: str = None) -> str:
    """고위험 이탈 고객 목록 조회"""
    df = compute_all_probs()

    if date:
        df_dates = load_membership_dates()
        df = df.merge(df_dates, on='USER_KEY', how='left')
        ts = pd.Timestamp(date)
        df['end_date'] = df['reg_date_decoded'] + pd.Timedelta(days=21)
        df = df[(df['reg_date_decoded'] <= ts) & (df['end_date'] > ts)]

    result = (df[df['이탈확률'] >= min_prob]
              .sort_values('이탈확률', ascending=False)
              .head(n))

    summary = []
    for _, row in result.iterrows():
        summary.append({
            'USER_KEY': str(row['USER_KEY'])[:16] + '...',
            '이탈확률': f"{row['이탈확률']:.1%}",
            '나이': int(row.get('age', 0)),
            '3주차시청(분)': int(row.get('dur_w3', 0)),
            '활동일': int(row.get('active_days', 0))
        })
    return json.dumps({'고위험고객수': len(result), '목록': summary}, ensure_ascii=False)

def tool_analyze_customer(user_key_prefix: str) -> str:
    """특정 고객 SHAP 분석"""
    model, explainer, FEAT = train_model()
    df = compute_all_probs()

    matches = df[df['USER_KEY'].astype(str).str.startswith(user_key_prefix)]
    if len(matches) == 0:
        return json.dumps({'error': '고객을 찾을 수 없습니다'}, ensure_ascii=False)

    row = matches.iloc[0]
    df_enc = df.copy()
    for col in df_enc.select_dtypes('object').columns:
        if col not in EXCLUDE:
            df_enc[col] = LabelEncoder().fit_transform(df_enc[col].astype(str))

    X = df_enc[FEAT].fillna(0)
    customer_X = X.loc[row.name:row.name]
    shap_vals = explainer.shap_values(customer_X)[0]

    shap_df = pd.DataFrame({'변수': FEAT, 'SHAP': shap_vals, '값': customer_X.iloc[0].values})
    shap_df['절대값'] = shap_df['SHAP'].abs()
    top5_churn = shap_df[shap_df['SHAP'] < 0].nlargest(3, '절대값')

    age = int(row.get('age', 0))
    genres = get_top_genres(row.to_dict())

    result = {
        '이탈확률': f"{row['이탈확률']:.1%}",
        '나이': age,
        '연령대': age_group_label(age),
        '3주차시청(분)': int(row.get('dur_w3', 0)),
        '활동일': int(row.get('active_days', 0)),
        '주요장르': [f"{g}({v:.0%})" for g, v in genres if v > 0],
        '이탈주요원인': [f"{r['변수']}={r['값']:.2f}" for _, r in top5_churn.iterrows()]
    }
    return json.dumps(result, ensure_ascii=False)

def tool_generate_sms(user_key_prefix: str, api_key: str) -> str:
    """고객 맞춤 문자 메시지 생성"""
    analysis_json = tool_analyze_customer(user_key_prefix)
    analysis = json.loads(analysis_json)

    if 'error' in analysis:
        return analysis_json

    age = analysis.get('나이', 30)
    age_grp = analysis.get('연령대', '30대')
    genres = ', '.join(analysis.get('주요장르', []))
    causes = ', '.join(analysis.get('이탈주요원인', []))

    persona_tips = {
        '10대': '친구 초대 시 둘 다 1달 무료',
        '20대': '친구 초대 100원 쿠폰 + 신작 알림',
        '30대': '이어보기 큐레이션 + 가족요금제 30% 할인',
        '40대': '가족 4인 프리미엄 첫달 무료',
        '50대+': '구독 시 포인트 5000점 + 가족요금제'
    }
    coupon = persona_tips.get(age_grp, '구독료 30% 할인')

    prompt = f"""OTT 이탈 방지 전략가. 고객 맞춤 문자 2가지 작성.

고객: {age}세 {age_grp} | 이탈확률 {analysis['이탈확률']} | 장르: {genres}
이탈원인: {causes} | 추천혜택: {coupon}

A안 (혜택강조, 80자 이내):
B안 (감성형, 80자 이내):"""

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=300, temperature=0.7
    )
    return json.dumps({
        'user_key': user_key_prefix + '...',
        '이탈확률': analysis['이탈확률'],
        '연령대': age_grp,
        '추천혜택': coupon,
        '문자': response.choices[0].message.content
    }, ensure_ascii=False)

def tool_save_report(n: int = 10, min_prob: float = 0.6, api_key: str = '') -> str:
    """고위험 고객 분석 리포트 엑셀 저장"""
    df = compute_all_probs()
    top_customers = (df[df['이탈확률'] >= min_prob]
                     .sort_values('이탈확률', ascending=False)
                     .head(n))

    rows = []
    progress = st.progress(0, text='리포트 생성 중...')

    for i, (_, row) in enumerate(top_customers.iterrows()):
        uk = str(row['USER_KEY'])[:20]
        sms_json = tool_generate_sms(uk, api_key)
        sms_data = json.loads(sms_json)

        age = int(row.get('age', 0))
        rows.append({
            'USER_KEY':    str(row['USER_KEY'])[:20] + '...',
            '이탈확률':    f"{row['이탈확률']:.1%}",
            '나이':        age,
            '연령대':      age_group_label(age),
            '3주차시청(분)': int(row.get('dur_w3', 0)),
            '활동일':      int(row.get('active_days', 0)),
            '추천혜택':    sms_data.get('추천혜택', ''),
            '문자(A안)':   sms_data.get('문자', '').split('B안')[0].replace('A안 (혜택강조, 80자 이내):', '').strip(),
            '문자(B안)':   'B안' + sms_data.get('문자', '').split('B안')[-1] if 'B안' in sms_data.get('문자', '') else '',
        })
        progress.progress((i+1)/n, text=f'진행 중... {i+1}/{n}명')

    progress.empty()

    report_df = pd.DataFrame(rows)
    filename = f"churn_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    filepath = REPORT_DIR / filename
    report_df.to_excel(filepath, index=False)

    return json.dumps({'저장경로': str(filepath), '생성고객수': len(rows)}, ensure_ascii=False)

# ── 에이전트 루프 ──────────────────────────────────────────────────────────────
TOOLS = [
    {
        'type': 'function',
        'function': {
            'name': 'get_high_risk_customers',
            'description': '이탈 위험이 높은 고객 목록을 조회합니다',
            'parameters': {
                'type': 'object',
                'properties': {
                    'n':        {'type': 'integer', 'description': '조회할 고객 수 (기본 10)'},
                    'min_prob': {'type': 'number',  'description': '최소 이탈 확률 (기본 0.5)'},
                    'date':     {'type': 'string',  'description': '날짜 (YYYY-MM-DD, 선택)'},
                },
                'required': []
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'analyze_customer',
            'description': '특정 고객의 이탈 원인을 SHAP으로 분석합니다',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_key_prefix': {'type': 'string', 'description': 'USER_KEY 앞부분'}
                },
                'required': ['user_key_prefix']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'generate_sms',
            'description': '고객 맞춤 문자 메시지를 생성합니다',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_key_prefix': {'type': 'string', 'description': 'USER_KEY 앞부분'}
                },
                'required': ['user_key_prefix']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'save_report',
            'description': '고위험 고객 전체 분석 리포트를 엑셀로 저장합니다',
            'parameters': {
                'type': 'object',
                'properties': {
                    'n':        {'type': 'integer', 'description': '저장할 고객 수 (기본 10)'},
                    'min_prob': {'type': 'number',  'description': '최소 이탈 확률 (기본 0.6)'},
                },
                'required': []
            }
        }
    },
]

def run_agent(user_message: str, api_key: str) -> str:
    client = Groq(api_key=api_key)
    messages = [
        {
            'role': 'system',
            'content': (
                '당신은 OTT 플랫폼 이탈 방지 AI 에이전트입니다. '
                '도구를 사용해 고위험 고객을 찾고, 분석하고, 맞춤 문자를 만들고, 리포트를 저장합니다. '
                '한국어로 답변하고 완료된 작업을 명확히 설명하세요.\n\n'
                '중요 규칙:\n'
                '1. 날짜 언급이 없으면 get_high_risk_customers에서 date 파라미터를 절대 사용하지 말 것\n'
                '2. 고객 목록이 비어있으면 date 없이 다시 조회할 것\n'
                '3. 문자 생성 전에 반드시 get_high_risk_customers로 USER_KEY를 먼저 확인할 것\n'
                '4. USER_KEY는 목록에서 받은 값의 앞 20글자를 사용할 것'
            )
        },
        {'role': 'user', 'content': user_message}
    ]

    tool_calls_log = []

    while True:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice='auto',
            max_tokens=1024
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content, tool_calls_log

        messages.append({'role': 'assistant', 'content': msg.content or '', 'tool_calls': [
            {'id': tc.id, 'type': 'function',
             'function': {'name': tc.function.name, 'arguments': tc.function.arguments}}
            for tc in msg.tool_calls
        ]})

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)

            if fn_name == 'get_high_risk_customers':
                result = tool_get_high_risk_customers(**fn_args)
            elif fn_name == 'analyze_customer':
                result = tool_analyze_customer(**fn_args)
            elif fn_name == 'generate_sms':
                result = tool_generate_sms(api_key=api_key, **fn_args)
            elif fn_name == 'save_report':
                result = tool_save_report(api_key=api_key, **fn_args)
            else:
                result = json.dumps({'error': f'알 수 없는 도구: {fn_name}'})

            tool_calls_log.append({'도구': fn_name, '결과': result})
            messages.append({'role': 'tool', 'tool_call_id': tc.id, 'content': result})

# ── Streamlit UI ──────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title='이탈 방지 AI 에이전트', page_icon='🤖', layout='wide')
    st.title('🤖 OTT 이탈 방지 AI 에이전트')
    st.caption('자연어 명령으로 고객 탐지 → 분석 → 문자 생성 → 엑셀 저장까지 자동 실행')

    with st.sidebar:
        st.header('⚙️ 설정')
        api_key = st.text_input('Groq API Key', value=os.getenv('GROQ_API_KEY',''),
                                type='password', placeholder='gsk_...')
        st.caption('무료 발급: console.groq.com')
        st.divider()
        st.header('💡 명령 예시')
        examples = [
            '이탈 위험 고객 5명 목록 보여줘',
            '이탈 확률 높은 고객 TOP 3 문자 만들어줘',
            '고위험 고객 10명 분석해서 엑셀로 저장해줘',
            '이탈 확률 80% 이상 고객 찾아줘',
        ]
        for ex in examples:
            if st.button(ex, use_container_width=True):
                st.session_state['prefill'] = ex

    if not api_key:
        st.info('👈 사이드바에 Groq API Key를 입력하세요')
        st.stop()

    with st.spinner('🤖 모델 로딩 중... (최초 1회)'):
        train_model()

    if 'agent_messages' not in st.session_state:
        st.session_state.agent_messages = []

    for msg in st.session_state.agent_messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
            if msg.get('tools'):
                with st.expander('🔧 실행된 도구'):
                    for t in msg['tools']:
                        st.write(f"**{t['도구']}**")
                        try:
                            st.json(json.loads(t['결과']))
                        except:
                            st.write(t['결과'])

    prefill = st.session_state.pop('prefill', '')
    user_input = st.chat_input('명령을 입력하세요... (예: 고위험 고객 5명 엑셀로 저장해줘)') or prefill

    if user_input:
        st.session_state.agent_messages.append({'role': 'user', 'content': user_input})
        with st.chat_message('user'):
            st.markdown(user_input)

        with st.chat_message('assistant'):
            with st.spinner('🤖 에이전트 실행 중...'):
                answer, tools_log = run_agent(user_input, api_key)
            st.markdown(answer)
            if tools_log:
                with st.expander('🔧 실행된 도구 보기'):
                    for t in tools_log:
                        st.write(f"**{t['도구']}**")
                        try:
                            st.json(json.loads(t['결과']))
                        except:
                            st.write(t['결과'])

            # 엑셀 다운로드
            for t in tools_log:
                if t['도구'] == 'save_report':
                    try:
                        saved = json.loads(t['결과'])
                        filepath = Path(saved['저장경로'])
                        if filepath.exists():
                            with open(filepath, 'rb') as f:
                                st.download_button(
                                    '📥 엑셀 다운로드',
                                    f.read(),
                                    file_name=filepath.name,
                                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                                )
                    except:
                        pass

        st.session_state.agent_messages.append({
            'role': 'assistant', 'content': answer, 'tools': tools_log
        })

    if st.session_state.agent_messages:
        if st.button('🗑️ 대화 초기화'):
            st.session_state.agent_messages = []
            st.rerun()


if __name__ == '__main__':
    main()
