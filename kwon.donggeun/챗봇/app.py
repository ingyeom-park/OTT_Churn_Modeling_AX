import os
import io
import contextlib
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import streamlit as st
import google.generativeai as genai
import xgboost as xgb
import shap
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from dotenv import load_dotenv

load_dotenv()

# ── 설정 ────────────────────────────────────────────────────────────────────
BASE      = Path(__file__).parent.parent
DATA_PATH = BASE / '_data/02_interim/260510_features/Membership_features_clean.csv'
GEMINI    = 'gemini-1.5-flash'
SEED      = 42
EXCLUDE   = ['USER_KEY','product_code','payment_device','device_group',
             'gender','age_group','is_repurchase']

# ── 데이터 & 모델 로드 (캐시) ────────────────────────────────────────────────
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
    spw = (y_tr == 0).sum() / (y_tr == 1).sum()
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
    df      = load_data().copy()
    model, _, FEAT = train_model()
    for col in df.select_dtypes('object').columns:
        if col not in EXCLUDE:
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))
    probs = model.predict_proba(df[FEAT].fillna(0))[:, 1]
    df['이탈확률'] = 1 - probs          # is_repurchase=1이 재구매, 이탈=낮은 확률
    df['이탈확률'] = 1 - df['이탈확률'] # 이탈 확률 = 1 - 재구매 확률
    # 재정의: 이탈(0)일 확률
    df['이탈확률'] = model.predict_proba(df[FEAT].fillna(0))[:, 0]
    return df

# ── 유틸 함수 ────────────────────────────────────────────────────────────────
def age_group_label(age):
    if age < 20:   return '10대'
    elif age < 30: return '20대'
    elif age < 40: return '30대'
    elif age < 50: return '40대'
    else:          return '50대+'

def risk_color(prob):
    if prob >= 0.7:   return '🔴 고위험'
    elif prob >= 0.4: return '🟡 중위험'
    else:             return '🟢 저위험'

def get_top_genres(customer):
    genre_map = {
        'drama_ratio': '드라마', 'family_ratio': '패밀리/애니',
        'romance_ratio': '로맨스', 'thriller_ratio': '스릴러',
        'horror_ratio': '공포', 'action_ratio': '액션',
        'sf_ratio': 'SF', 'comedy_ratio': '코미디'
    }
    genres = {v: customer.get(k, 0) for k, v in genre_map.items()}
    return sorted(genres.items(), key=lambda x: x[1], reverse=True)[:3]

def predict_customer(customer_dict, model, explainer, features):
    X = pd.DataFrame([customer_dict])[features].fillna(0)
    prob_repurchase = model.predict_proba(X)[0, 1]
    prob_churn      = 1 - prob_repurchase
    shap_vals = explainer.shap_values(X)[0]
    shap_df = pd.DataFrame({
        '변수': features,
        'SHAP': shap_vals,
        '값':   X.iloc[0].values
    }).reindex(columns=['변수', 'SHAP', '값'])
    shap_df['절대값'] = shap_df['SHAP'].abs()
    shap_df = shap_df.sort_values('절대값', ascending=False).drop(columns='절대값')
    return prob_churn, shap_df

# ── Gemini 추천 생성 ──────────────────────────────────────────────────────────
def generate_recommendation(customer, prob_churn, shap_df, api_key):
    genai.configure(api_key=api_key)

    age       = int(customer.get('age', 30))
    age_grp   = age_group_label(age)
    top_genres = get_top_genres(customer)
    genre_text = ', '.join([f'{g}({v:.0%})' for g, v in top_genres if v > 0])

    # 이탈 방향 주요 요인 (SHAP < 0 = 재구매 확률 낮추는 방향)
    churn_factors = shap_df[shap_df['SHAP'] < 0].head(4)
    factor_text = '\n'.join([
        f"  - {row['변수']}: {row['값']:.2f}" for _, row in churn_factors.iterrows()
    ]) or '  - 복합적 요인'

    prompt = f"""당신은 OTT 플랫폼의 이탈 방지 전략 전문가입니다.
아래 고객 데이터를 분석하여 이탈을 막기 위한 맞춤 전략을 수립해주세요.

=== 고객 프로필 ===
- 나이: {age}세 ({age_grp})
- 이탈 예측 확률: {prob_churn:.1%}  ({risk_color(prob_churn)})
- 구독 기간: {customer.get('duration_days', 21):.0f}일
- 3주차 시청 시간: {customer.get('dur_w3', 0):.0f}분
- 평균 시청 시간: {customer.get('avg_session_time', 0):.0f}분/회
- 시청 일수: {customer.get('active_days', 0):.0f}일
- 하루 구독 단가: {customer.get('price_per_day', 0):.0f}원
- 주요 장르: {genre_text or '없음'}
- 이탈 방지 이력: {'있음' if customer.get('is_churn_prevented', 0) else '없음'}
- 프리미엄 요금제: {'예' if customer.get('is_premium', 0) else '아니오'}

=== 이탈 주요 원인 (AI 분석) ===
{factor_text}

위 정보를 바탕으로 다음 3가지를 작성해주세요:

## 1. 이탈 위험 분석
이 고객이 이탈할 것 같은 구체적 이유를 2~3문장으로 설명해주세요.

## 2. 맞춤 개입 전략 ({age_grp} 맞춤)
- 🎟️ 추천 쿠폰/혜택: (구체적 수치 포함, 예: "다음 달 구독료 30% 할인")
- 🎬 콘텐츠 추천: (시청 장르 기반)
- 💡 추가 제안: (요금제 변경, 기능 안내 등 1가지)

## 3. 발송 문자 메시지
고객에게 실제로 보낼 문자 메시지를 80자 이내로 작성해주세요.
자연스럽고 따뜻한 톤으로, 혜택이 명확하게 드러나야 합니다."""

    model_gemini = genai.GenerativeModel(GEMINI)
    response = model_gemini.generate_content(prompt)
    return response.text

# ── Streamlit UI ──────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title='이탈 방지 AI', page_icon='🛡️', layout='wide')
    st.title('🛡️ OTT 이탈 방지 AI')
    st.caption('이탈 위험 고객을 탐지하고 맞춤 개입 전략을 생성합니다')

    # ── 사이드바 ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header('⚙️ 설정')
        api_key = st.text_input(
            'Google Gemini API Key',
            value=os.getenv('GEMINI_API_KEY', ''),
            type='password', placeholder='AIza...'
        )
        if not api_key:
            st.warning('API Key를 입력하세요')

        st.divider()
        st.header('📊 전체 현황')
        try:
            df_raw = load_data()
            total  = len(df_raw)
            churn  = (df_raw['is_repurchase'] == 0).sum()
            st.metric('총 구독자', f'{total:,}명')
            st.metric('이탈자', f'{churn:,}명', f'{churn/total:.1%}')
            data_ok = True
        except FileNotFoundError:
            st.error('데이터 파일 없음')
            data_ok = False

    if not data_ok:
        st.stop()

    # ── 모델 로딩 ─────────────────────────────────────────────────────────────
    with st.spinner('🤖 AI 모델 로딩 중... (최초 1회만)'):
        model, explainer, features = train_model()

    tab1, tab2 = st.tabs(['🔍 고위험 고객 탐색', '➕ 새 고객 분석'])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1: 기존 고위험 고객
    # ════════════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader('이탈 고위험 고객 목록')

        with st.spinner('이탈 확률 계산 중...'):
            df_scored = compute_all_probs()

        # 필터
        col1, col2 = st.columns([1, 2])
        with col1:
            top_n = st.slider('상위 N명 표시', 10, 200, 50)
        with col2:
            min_prob = st.slider('최소 이탈 확률', 0.0, 1.0, 0.5, 0.05)

        df_risk = (df_scored[df_scored['이탈확률'] >= min_prob]
                   .sort_values('이탈확률', ascending=False)
                   .head(top_n)
                   .reset_index(drop=True))
        df_risk.index += 1

        # 표 출력
        display_cols = ['USER_KEY', '이탈확률', 'age', 'duration_days',
                        'dur_w3', 'avg_session_time', 'active_days', 'price_per_day']
        display_cols = [c for c in display_cols if c in df_risk.columns]

        st.dataframe(
            df_risk[display_cols].style.background_gradient(
                subset=['이탈확률'], cmap='RdYlGn_r'
            ).format({'이탈확률': '{:.1%}', 'price_per_day': '{:.0f}원'}),
            use_container_width=True, height=300
        )

        st.divider()
        st.subheader('고객 선택 후 개입 전략 생성')

        if len(df_risk) == 0:
            st.info('해당 조건의 고객이 없습니다. 필터를 조정하세요.')
        else:
            user_keys = df_risk['USER_KEY'].astype(str).tolist() if 'USER_KEY' in df_risk.columns else df_risk.index.astype(str).tolist()
            selected  = st.selectbox('고객 선택', user_keys)

            if st.button('🚨 개입 전략 생성', type='primary', use_container_width=True):
                if not api_key:
                    st.error('API Key를 입력해주세요')
                else:
                    if 'USER_KEY' in df_risk.columns:
                        row = df_risk[df_risk['USER_KEY'].astype(str) == selected].iloc[0]
                    else:
                        row = df_risk.loc[int(selected)]

                    customer = row.to_dict()
                    prob_churn, shap_df = predict_customer(customer, model, explainer, features)

                    # 결과 표시
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric('이탈 확률', f'{prob_churn:.1%}')
                    c2.metric('위험 등급', risk_color(prob_churn))
                    c3.metric('나이', f"{int(customer.get('age', 0))}세 ({age_group_label(int(customer.get('age', 0)))})")
                    c4.metric('3주차 시청', f"{customer.get('dur_w3', 0):.0f}분")

                    col_a, col_b = st.columns([1, 2])
                    with col_a:
                        st.markdown('**SHAP 이탈 원인 Top 5**')
                        top5 = shap_df.head(5)
                        for _, r in top5.iterrows():
                            direction = '⬇️ 이탈' if r['SHAP'] < 0 else '⬆️ 재구매'
                            st.write(f"`{r['변수']}` = {r['값']:.2f} → {direction}")

                    with col_b:
                        with st.spinner('Gemini가 전략 생성 중...'):
                            recommendation = generate_recommendation(customer, prob_churn, shap_df, api_key)
                        st.markdown(recommendation)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2: 새 고객 직접 입력
    # ════════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader('새 고객 정보 입력')
        st.caption('주요 정보만 입력하면 나머지는 자동으로 처리됩니다')

        with st.form('new_customer_form'):
            st.markdown('**👤 기본 정보**')
            c1, c2, c3 = st.columns(3)
            age          = c1.number_input('나이', 10, 80, 35)
            duration     = c2.number_input('구독 기간 (일)', 1, 365, 21)
            price_per_day = c3.number_input('하루 구독 단가 (원)', 0, 2000, 476)

            st.markdown('**📺 시청 행동**')
            c1, c2, c3, c4 = st.columns(4)
            dur_w1       = c1.number_input('1주차 시청(분)', 0, 3000, 120)
            dur_w2       = c2.number_input('2주차 시청(분)', 0, 3000, 80)
            dur_w3       = c3.number_input('3주차 시청(분)', 0, 3000, 0)
            active_days  = c4.number_input('시청 일수', 0, 21, 5)

            c1, c2 = st.columns(2)
            avg_session  = c1.number_input('평균 시청 시간(분)', 0, 300, 45)
            is_prevented = c2.selectbox('이탈 방지 처리 이력', [0, 1], format_func=lambda x: '있음' if x else '없음')

            st.markdown('**🎬 장르 비율** (합계 1.0 기준)')
            c1, c2, c3, c4 = st.columns(4)
            drama_r   = c1.slider('드라마',   0.0, 1.0, 0.3, 0.05)
            family_r  = c2.slider('패밀리',   0.0, 1.0, 0.1, 0.05)
            romance_r = c3.slider('로맨스',   0.0, 1.0, 0.1, 0.05)
            thriller_r = c4.slider('스릴러',  0.0, 1.0, 0.2, 0.05)
            c1, c2, c3, c4 = st.columns(4)
            horror_r  = c1.slider('공포',     0.0, 1.0, 0.1, 0.05)
            action_r  = c2.slider('액션',     0.0, 1.0, 0.1, 0.05)
            sf_r      = c3.slider('SF',       0.0, 1.0, 0.05, 0.05)
            comedy_r  = c4.slider('코미디',   0.0, 1.0, 0.05, 0.05)

            submitted = st.form_submit_button('🔍 분석 및 전략 생성', type='primary', use_container_width=True)

        if submitted:
            if not api_key:
                st.error('API Key를 입력해주세요')
            else:
                # 특성 벡터 구성 (입력값 + 파생값 + 나머지 0)
                ret_w2 = 1.0 if dur_w2 > 0 else 0.0
                ret_w3 = 1.0 if dur_w3 > 0 else 0.0
                total_watch = dur_w1 + dur_w2 + dur_w3

                base = {f: 0 for f in features}
                base.update({
                    'age':                   age,
                    'duration_days':         duration,
                    'price_per_day':         price_per_day,
                    'dur_w1':                dur_w1,
                    'dur_w2':                dur_w2,
                    'dur_w3':                dur_w3,
                    'active_days':           active_days,
                    'avg_session_time':      avg_session,
                    'is_churn_prevented':    is_prevented,
                    'retention_w2_ratio':    ret_w2,
                    'retention_w3_ratio':    ret_w3,
                    'retention_w2':          ret_w2,
                    'retention_w3':          ret_w3,
                    'w3_minus_w1':           dur_w3 - dur_w1,
                    'activity_rate':         active_days / 21,
                    'drama_ratio':           drama_r,
                    'family_ratio':          family_r,
                    'romance_ratio':         romance_r,
                    'thriller_ratio':        thriller_r,
                    'horror_ratio':          horror_r,
                    'action_ratio':          action_r,
                    'sf_ratio':              sf_r,
                    'comedy_ratio':          comedy_r,
                    'stream_watch_interaction': total_watch,
                })

                prob_churn, shap_df = predict_customer(base, model, explainer, features)

                st.divider()
                c1, c2, c3, c4 = st.columns(4)
                c1.metric('이탈 확률', f'{prob_churn:.1%}')
                c2.metric('위험 등급', risk_color(prob_churn))
                c3.metric('나이', f'{age}세 ({age_group_label(age)})')
                c4.metric('3주차 시청', f'{dur_w3}분')

                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.markdown('**SHAP 이탈 원인 Top 5**')
                    for _, r in shap_df.head(5).iterrows():
                        direction = '⬇️ 이탈' if r['SHAP'] < 0 else '⬆️ 재구매'
                        st.write(f"`{r['변수']}` = {r['값']:.2f} → {direction}")

                with col_b:
                    with st.spinner('Gemini가 전략 생성 중...'):
                        recommendation = generate_recommendation(base, prob_churn, shap_df, api_key)
                    st.markdown(recommendation)


if __name__ == '__main__':
    main()
