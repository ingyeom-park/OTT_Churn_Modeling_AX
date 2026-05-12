import os
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import streamlit as st
import xgboost as xgb
import shap
from groq import Groq
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from dotenv import load_dotenv

load_dotenv()

# ── 설정 ────────────────────────────────────────────────────────────────────
BASE       = Path(__file__).parent.parent
DATA_PATH  = BASE / '_data/02_interim/260510_features/Membership_features_clean.csv'
GROQ_MODEL = 'llama-3.1-8b-instant'
SEED       = 42
EXCLUDE    = ['USER_KEY','product_code','payment_device','device_group',
              'gender','age_group','is_repurchase']

# ── 데이터 & 모델 ─────────────────────────────────────────────────────────────
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

def age_group_label(age):
    if age < 20:   return '10대'
    elif age < 30: return '20대'
    elif age < 40: return '30대'
    elif age < 50: return '40대'
    else:          return '50대+'

def get_customer_profile(user_key: str):
    """고객 데이터 + 이탈 확률 + 주요 원인 추출"""
    df = load_data()
    model, explainer, FEAT = train_model()

    matches = df[df['USER_KEY'].astype(str).str.contains(user_key, na=False)]
    if len(matches) == 0:
        return None

    row = matches.iloc[0]
    df_enc = df.copy()
    for col in df_enc.select_dtypes('object').columns:
        if col not in EXCLUDE:
            df_enc[col] = LabelEncoder().fit_transform(df_enc[col].astype(str))

    X = df_enc[FEAT].fillna(0)
    customer_X = X.loc[row.name:row.name]

    prob_churn = 1 - model.predict_proba(customer_X)[0, 1]
    shap_vals  = explainer.shap_values(customer_X)[0]

    shap_df = pd.DataFrame({'변수': FEAT, 'SHAP': shap_vals, '값': customer_X.iloc[0].values})
    churn_causes = shap_df[shap_df['SHAP'] < 0].nlargest(3, lambda x: x.abs()
                   if hasattr(x, 'abs') else abs(x))

    # 실제로는 절대값으로 정렬
    shap_df['abs'] = shap_df['SHAP'].abs()
    churn_causes = shap_df[shap_df['SHAP'] < 0].nlargest(3, 'abs')

    # 장르 파악
    genre_map = {
        'drama_ratio':'드라마', 'family_ratio':'패밀리/애니',
        'romance_ratio':'로맨스', 'thriller_ratio':'스릴러',
        'horror_ratio':'공포', 'action_ratio':'액션',
        'sf_ratio':'SF', 'comedy_ratio':'코미디'
    }
    genres = {v: row.get(k, 0) for k, v in genre_map.items()}
    top_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)[:2]
    top_genres = [g for g, v in top_genres if v > 0.05]

    age     = int(row.get('age', 30))
    age_grp = age_group_label(age)

    # 연령대별 혜택
    coupon_map = {
        '10대':  '친구 초대 시 둘 다 1개월 무료',
        '20대':  '다음 달 구독료 50% 할인',
        '30대':  '가족 요금제 첫 달 무료 체험',
        '40대':  '프리미엄 요금제 1개월 무료',
        '50대+': '구독 시 포인트 5,000점 + 가족 요금제 안내',
    }
    coupon = coupon_map.get(age_grp, '다음 달 구독료 30% 할인')

    return {
        'prob_churn':   prob_churn,
        'age':          age,
        'age_grp':      age_grp,
        'dur_w3':       float(row.get('dur_w3', 0)),
        'active_days':  float(row.get('active_days', 0)),
        'top_genres':   top_genres,
        'coupon':       coupon,
        'is_premium':   int(row.get('is_premium', 0)),
        'price_per_day': float(row.get('price_per_day', 0)),
        'churn_causes': churn_causes['변수'].tolist(),
    }

def build_system_prompt(profile: dict) -> str:
    """고객 프로필 기반 상담원 시스템 프롬프트"""
    risk_level = '높음' if profile['prob_churn'] > 0.6 else ('중간' if profile['prob_churn'] > 0.3 else '낮음')
    genres_str = ', '.join(profile['top_genres']) if profile['top_genres'] else '다양한 장르'

    # 이탈 위험 원인 → 상담 포인트로 변환
    cause_hints = []
    for cause in profile['churn_causes']:
        if 'dur_w3' in cause or 'retention_w3' in cause:
            cause_hints.append('최근 시청량이 줄었음 → 새로운 콘텐츠 추천으로 재참여 유도')
        elif 'recency' in cause:
            cause_hints.append('마지막 접속이 오래됨 → 복귀 유도 혜택 제안')
        elif 'price' in cause:
            cause_hints.append('요금 부담 가능성 → 가성비 강조 또는 할인 제안')
        elif 'thriller' in cause or 'horror' in cause:
            cause_hints.append('장르 쏠림 현상 → 다양한 장르 추천')

    return f"""당신은 OTT 플랫폼 "스트리밍+" 의 AI 고객 상담사 "루나"입니다.
지금 대화 중인 고객의 프로필을 알고 있으며, 이를 바탕으로 친절하고 자연스럽게 상담합니다.

=== 고객 정보 (내부용, 고객에게 직접 수치 노출 금지) ===
- 나이: {profile['age']}세 ({profile['age_grp']})
- 이탈 위험도: {risk_level}
- 최근 3주차 시청: {profile['dur_w3']:.0f}분
- 총 시청 일수: {profile['active_days']:.0f}일
- 주요 관심 장르: {genres_str}
- 요금제: {'프리미엄' if profile['is_premium'] else '스탠다드'}

=== 상담 전략 ===
{chr(10).join(f'- {h}' for h in cause_hints) if cause_hints else '- 전반적 만족도 확인 후 혜택 안내'}

=== 제공 가능한 혜택 (적절한 타이밍에 제안) ===
- {profile['coupon']}

=== 행동 지침 ===
1. 절대 "이탈 위험", "이탈 확률" 같은 내부 용어 사용 금지
2. 고객이 불만을 말하면 공감 먼저, 해결책은 그 다음
3. 혜택은 대화 흐름에서 자연스럽게 제안 (처음부터 억지로 X)
4. {profile['age_grp']} 특성에 맞는 톤으로 대화
5. 고객이 "해지", "취소", "그만" 언급 시 → 혜택 적극 제안
6. 짧고 친근하게 답변 (3~4문장 이내)
7. 한국어로만 답변"""

def chat_with_customer(messages: list, api_key: str) -> str:
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=300,
        temperature=0.8,
    )
    return response.choices[0].message.content

# ── Streamlit UI ──────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title='스트리밍+ 고객센터', page_icon='📺', layout='centered')

    st.title('📺 스트리밍+ 고객센터')
    st.caption('AI 상담사 루나와 대화하세요')

    with st.sidebar:
        st.header('⚙️ 설정')
        api_key = st.text_input('Groq API Key', value=os.getenv('GROQ_API_KEY',''),
                                type='password', placeholder='gsk_...')
        st.divider()
        st.info('💡 실제 서비스에서는 로그인으로 자동 인식됩니다.\n\n테스트용으로 USER_KEY 일부를 입력하세요.')

    if not api_key:
        st.info('👈 사이드바에 Groq API Key를 입력하세요')
        st.stop()

    # 고객 인증
    if 'customer_profile' not in st.session_state:
        st.session_state.customer_profile = None
        st.session_state.chat_messages    = []
        st.session_state.system_prompt    = None

    if st.session_state.customer_profile is None:
        st.subheader('본인 확인')
        user_key_input = st.text_input('회원 ID (USER_KEY 앞 10자리)', placeholder='예: 7a6960912b')

        col1, col2 = st.columns(2)
        # 테스트용 랜덤 고객
        if col2.button('🎲 랜덤 고객으로 테스트', use_container_width=True):
            df = load_data()
            model, _, FEAT = train_model()
            df_enc = df.copy()
            for col in df_enc.select_dtypes('object').columns:
                if col not in EXCLUDE:
                    df_enc[col] = LabelEncoder().fit_transform(df_enc[col].astype(str))
            probs = 1 - model.predict_proba(df_enc[FEAT].fillna(0))[:, 1]
            # 이탈 위험 높은 고객 중 랜덤
            high_risk_idx = np.where(probs > 0.6)[0]
            if len(high_risk_idx) > 0:
                idx = np.random.choice(high_risk_idx)
                user_key_input = str(df.iloc[idx]['USER_KEY'])[:12]
                st.session_state['test_key'] = user_key_input

        if 'test_key' in st.session_state:
            user_key_input = st.session_state['test_key']

        if col1.button('✅ 확인', type='primary', use_container_width=True) and user_key_input:
            with st.spinner('확인 중...'):
                profile = get_customer_profile(user_key_input)
            if profile:
                st.session_state.customer_profile = profile
                st.session_state.system_prompt    = build_system_prompt(profile)
                # 루나 첫 인사
                risk = profile['prob_churn']
                if risk > 0.6:
                    first_msg = f"안녕하세요! 스트리밍+ 상담사 루나입니다 😊 최근에 어떻게 지내셨어요? 혹시 서비스 이용하시면서 불편하신 점이 있으셨나요?"
                else:
                    first_msg = f"안녕하세요! 스트리밍+ 상담사 루나입니다 😊 오늘 무엇을 도와드릴까요?"
                st.session_state.chat_messages = [
                    {'role': 'assistant', 'content': first_msg}
                ]
                st.rerun()
            else:
                st.error('회원 정보를 찾을 수 없습니다. USER_KEY를 다시 확인해주세요.')
        return

    # 채팅 화면
    profile = st.session_state.customer_profile

    # 내부 정보 표시 (상담원 뷰 - 토글)
    with st.expander('🔒 내부 고객 정보 (상담원용)', expanded=False):
        col1, col2, col3 = st.columns(3)
        col1.metric('이탈 위험도', f"{profile['prob_churn']:.1%}")
        col2.metric('나이', f"{profile['age']}세 ({profile['age_grp']})")
        col3.metric('3주차 시청', f"{profile['dur_w3']:.0f}분")
        st.write(f"**관심 장르**: {', '.join(profile['top_genres']) or '없음'}")
        st.write(f"**제공 가능 혜택**: {profile['coupon']}")

    st.divider()

    # 채팅 메시지 출력
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg['role'], avatar='🤖' if msg['role']=='assistant' else '👤'):
            st.markdown(msg['content'])

    # 입력
    user_input = st.chat_input('메시지를 입력하세요...')

    if user_input:
        st.session_state.chat_messages.append({'role': 'user', 'content': user_input})
        with st.chat_message('user', avatar='👤'):
            st.markdown(user_input)

        # Groq 호출
        groq_messages = [{'role': 'system', 'content': st.session_state.system_prompt}]
        for msg in st.session_state.chat_messages:
            groq_messages.append({'role': msg['role'], 'content': msg['content']})

        with st.chat_message('assistant', avatar='🤖'):
            with st.spinner('루나가 답변 중...'):
                reply = chat_with_customer(groq_messages, api_key)
            st.markdown(reply)

        st.session_state.chat_messages.append({'role': 'assistant', 'content': reply})

    # 상담 종료
    col1, col2 = st.columns([4, 1])
    if col2.button('상담 종료', use_container_width=True):
        st.session_state.customer_profile = None
        st.session_state.chat_messages    = []
        st.session_state.system_prompt    = None
        if 'test_key' in st.session_state:
            del st.session_state['test_key']
        st.rerun()


if __name__ == '__main__':
    main()
