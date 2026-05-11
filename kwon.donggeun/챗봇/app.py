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
PERSONA_GUIDE = """
=== 토스 2024 리포트 기반 연령/성별 페르소나 ===

[10대]
- 특징: 장기 고가치 사용자, SNS·소셜 공유에 극도로 민감, 트렌드 선도
- 효과적 혜택: 친구 초대 시 둘 다 무료(친구 데려오면 1개월 무료), 인기 아이돌/영화 관련 독점 콘텐츠 알림
- 메시지 톤: 짧고 캐주얼, 이모지 적극 활용
- 예시 쿠폰: "친구 초대하면 둘 다 한 달 무료 🎁"

[20대 여성]
- 특징: 뷰티/패션/엔터테인먼트 소비 최상위, 소셜 공유 활발, 트렌드에 민감
- 효과적 혜택: 친구 초대 추천인 쿠폰(소셜 효과), 드라마/로맨스 신작 큐레이션, 뷰티 브랜드 콜라보 혜택
- 메시지 톤: 트렌디하고 감성적, 짧은 문장
- 예시 쿠폰: "친구 초대하면 100원 추가 할인 + 드라마 신작 알림"

[20대 남성]
- 특징: 게임/스포츠/액션 콘텐츠 선호, 가성비 중시, 모바일 헤비유저
- 효과적 혜택: 액션·SF 신작 알림, 게임 콜라보 이벤트, 친구와 함께 보기 기능 강조
- 메시지 톤: 직접적, 혜택 숫자 명확히
- 예시 쿠폰: "이번 달 구독료 50% 할인 + 액션 신작 3편 무료"

[30대 여성]
- 특징: 재방문율 80% 높음, 드라마·로맨스 충성 시청자, 바쁜 일상 속 콘텐츠 소비
- 효과적 혜택: 이어보기 큐레이션(바빠서 못 본 콘텐츠), 가족 요금제 할인, 주말 몰아보기 추천 플레이리스트
- 메시지 톤: 따뜻하고 공감적
- 예시 쿠폰: "못 보셨던 드라마 이어보기 + 가족 요금제 30% 할인"

[30대 남성]
- 특징: 경제적으로 안정, 다큐·정보·스포츠 선호, 가성비와 실용성 중시
- 효과적 혜택: 다음 달 구독료 할인, 프리미엄 요금제 업그레이드 유도, 스포츠 시즌 이벤트 연계
- 메시지 톤: 실용적, 수치 명확히
- 예시 쿠폰: "프리미엄 첫 달 500원 체험 + 다음 달 30% 할인"

[40대 여성]
- 특징: 라이브 쇼핑·혜택 탭 적극 활용, 클릭률 높음(62.1%), 가족 중심 소비
- 효과적 혜택: 가족 공유 요금제, 라이브 이벤트 알림, 건강/리빙 관련 콜라보 혜택
- 메시지 톤: 정중하고 신뢰감 있게
- 예시 쿠폰: "가족 4인 함께 쓰는 프리미엄 요금제 첫 달 무료"

[40대 남성]
- 특징: 모빌리티·가전 소비 높음, 실용적 혜택 선호, 브랜드 신뢰 중시
- 효과적 혜택: 가족 요금제, 프리미엄 콘텐츠 체험, 장기 구독 할인
- 메시지 톤: 간결하고 신뢰감 있게
- 예시 쿠폰: "6개월 장기 구독 시 20% 할인"

[50대+]
- 특징: CTR 70%+ 최고, 가구 금융 의사결정자, 앱테크(포인트 적립) 선호, 쉬운 UI 선호
- 효과적 혜택: 포인트 적립 혜택, 전화 상담 연결, 가족 공유 요금제, 건강·다큐 콘텐츠 큐레이션
- 메시지 톤: 정중하고 명확하게, 혜택 강조
- 예시 쿠폰: "구독 시 포인트 5,000점 적립 + 가족 요금제 안내"
"""

def generate_recommendation(customer, prob_churn, shap_df, api_key):
    genai.configure(api_key=api_key)

    age        = int(customer.get('age', 30))
    age_grp    = age_group_label(age)
    gender_enc = int(customer.get('gender_enc', 2))
    gender_str = '남성' if gender_enc == 1 else ('여성' if gender_enc == 0 else '미상')
    persona    = f"{age_grp} {gender_str}" if gender_enc != 2 else age_grp

    top_genres = get_top_genres(customer)
    genre_text = ', '.join([f'{g}({v:.0%})' for g, v in top_genres if v > 0])

    churn_factors = shap_df[shap_df['SHAP'] < 0].head(4)
    factor_text = '\n'.join([
        f"  - {row['변수']}: {row['값']:.2f}" for _, row in churn_factors.iterrows()
    ]) or '  - 복합적 요인'

    prompt = f"""당신은 OTT 플랫폼의 이탈 방지 전략 전문가입니다.
토스 2024 리포트 기반 페르소나 가이드를 참고하여 해당 고객에게 최적화된 개입 전략을 수립해주세요.

{PERSONA_GUIDE}

=== 분석 대상 고객 ===
- 나이: {age}세 ({persona})
- 이탈 예측 확률: {prob_churn:.1%}  ({risk_color(prob_churn)})
- 구독 기간: {customer.get('duration_days', 21):.0f}일
- 3주차 시청 시간: {customer.get('dur_w3', 0):.0f}분
- 평균 시청 시간: {customer.get('avg_session_time', 0):.0f}분/회
- 시청 일수: {customer.get('active_days', 0):.0f}일
- 하루 구독 단가: {customer.get('price_per_day', 0):.0f}원
- 주요 장르: {genre_text or '없음'}
- 이탈 방지 이력: {'있음 (이전 혜택 효과 없었음)' if customer.get('is_churn_prevented', 0) else '없음'}
- 프리미엄 요금제: {'사용 중' if customer.get('is_premium', 0) else '미사용'}

=== AI 이탈 원인 분석 (SHAP) ===
{factor_text}

위 페르소나 가이드와 고객 데이터를 바탕으로 다음을 작성해주세요:

## 1. 이탈 위험 분석
이 고객이 이탈할 것 같은 구체적 이유 (2~3문장)

## 2. {persona} 맞춤 개입 전략
- 🎟️ 추천 쿠폰/혜택: 구체적 수치 포함 (예: "친구 초대 시 둘 다 한 달 무료")
- 🎬 콘텐츠 추천: 시청 장르와 페르소나 특성 결합
- 👥 소셜/추가 제안: 페르소나에 맞는 특별 제안 1가지 (친구 초대, 가족 요금제, 포인트 적립 등)

## 3. 발송 문자 메시지
실제 발송용 문자를 **2가지 버전**으로 작성해주세요.
- A안 (혜택 강조형, 80자 이내)
- B안 (감성/공감형, 80자 이내)
페르소나 톤에 맞게 작성해주세요."""

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
