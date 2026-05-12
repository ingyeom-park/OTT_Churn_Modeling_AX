import os
import io
import contextlib
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import streamlit as st
from groq import Groq
import xgboost as xgb
import shap
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from dotenv import load_dotenv

load_dotenv()

# ── 설정 ────────────────────────────────────────────────────────────────────
BASE      = Path(__file__).parent.parent.parent
DATA_PATH  = BASE / '_data/02_interim/260510_features/Membership_features_clean.csv'
MEM_PATH   = BASE / '_data/02_interim/260510_merged_v2/Membership_v2.csv'
GROQ_MODEL = 'llama-3.1-8b-instant'
SEED      = 42
EXCLUDE   = ['USER_KEY','product_code','payment_device','device_group',
             'gender','age_group','is_repurchase']

# ── 데이터 & 모델 로드 (캐시) ────────────────────────────────────────────────
def mask_future_features(customer_dict, sub_day):
    """경과일 기준으로 아직 안 일어난 주차 데이터 0으로 마스킹"""
    masked = customer_dict.copy()
    if sub_day < 14:  # 3주차 미진입
        for col in ['dur_w3','retention_w3','retention_w3_ratio',
                    'w3_minus_w1','w3_minus_w2','late_binge_flag']:
            if col in masked: masked[col] = 0
    if sub_day < 7:   # 2주차 미진입
        for col in ['dur_w2','retention_w2','retention_w2_ratio','w2_minus_w1']:
            if col in masked: masked[col] = 0
    return masked

def decode_date(s):
    # "2014-03-21" → day=14, month=03, year=2021 → 2021-03-14
    parts = str(s).split('-')
    day   = int(parts[0][2:])
    month = int(parts[1])
    year  = 2000 + int(parts[2])
    return pd.Timestamp(year=year, month=month, day=day)

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH, encoding='utf-8-sig')

@st.cache_data
def load_membership_dates():
    df = pd.read_csv(MEM_PATH, encoding='utf-8-sig', usecols=['USER_KEY','reg_date'])
    df['reg_date_decoded'] = df['reg_date'].apply(decode_date)
    return df[['USER_KEY','reg_date_decoded']]

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
PERSONA_GUIDE = {
    '10대':    ('SNS 공유 민감, 트렌드 선도',        '친구 초대 시 둘 다 1달 무료',        '캐주얼·이모지'),
    '20대 여성': ('뷰티/엔터 소비 최상위, 소셜 활발',   '친구 초대 100원 쿠폰+드라마 신작',   '트렌디·감성적'),
    '20대 남성': ('게임/액션 선호, 가성비 중시',        '구독료 50% 할인+액션 신작 3편',      '직접적·수치 명확'),
    '30대 여성': ('드라마 충성, 바쁜 일상',            '이어보기 큐레이션+가족요금제 30%할인', '따뜻·공감'),
    '30대 남성': ('다큐/스포츠, 가성비·실용성',         '프리미엄 첫달 500원+다음달 30%할인', '실용적·수치'),
    '40대 여성': ('라이브쇼핑 적극, 가족 중심',         '가족4인 프리미엄 첫달 무료',          '정중·신뢰'),
    '40대 남성': ('실용혜택·브랜드 신뢰',              '6개월 장기구독 20% 할인',            '간결·신뢰'),
    '50대+':   ('CTR 최고, 앱테크·포인트 선호',       '구독 시 포인트 5000점+가족요금제',    '정중·혜택강조'),
}

def generate_recommendation(customer, prob_churn, shap_df, api_key):
    age        = int(customer.get('age', 30))
    age_grp    = age_group_label(age)
    gender_enc = int(customer.get('gender_enc', 2))
    gender_str = '남성' if gender_enc == 1 else ('여성' if gender_enc == 0 else '')
    persona    = f"{age_grp} {gender_str}".strip()

    # 페르소나 매칭
    p_key = next((k for k in PERSONA_GUIDE if k in persona), age_grp)
    p = PERSONA_GUIDE.get(p_key, ('일반 소비자', '구독료 30% 할인', '친근하게'))
    p_trait, p_coupon, p_tone = p

    top_genres = get_top_genres(customer)
    genre_text = ', '.join([f'{g}({v:.0%})' for g, v in top_genres if v > 0]) or '없음'

    churn_factors = shap_df[shap_df['SHAP'] < 0].head(3)
    factor_text = ', '.join([row['변수'] for _, row in churn_factors.iterrows()]) or '복합적 요인'

    prompt = f"""OTT 이탈 방지 전략가. 아래 고객 정보로 개입 전략 작성.

고객: {age}세 {persona} | 이탈확률 {prob_churn:.0%} | 장르: {genre_text}
시청: 3주차 {customer.get('dur_w3',0):.0f}분 | 활동일 {customer.get('active_days',0):.0f}일 | 단가 {customer.get('price_per_day',0):.0f}원/일
이탈원인(SHAP): {factor_text}
페르소나: {p_trait} | 추천혜택: {p_coupon} | 톤: {p_tone}

## 1. 이탈 위험 분석 (2문장)
## 2. {persona} 맞춤 개입 전략
- 🎟️ 쿠폰/혜택:
- 🎬 콘텐츠 추천:
- 👥 소셜/추가 제안:
## 3. 발송 문자 2가지 (각 80자 이내)
- A안 (혜택강조):
- B안 (감성형):"""

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=1024,
        temperature=0.7,
    )
    return response.choices[0].message.content

# ── Streamlit UI ──────────────────────────────────────────────────────────────
def main():
    pass
    st.title('🛡️ OTT 이탈 방지 AI')
    st.caption('이탈 위험 고객을 탐지하고 맞춤 개입 전략을 생성합니다')

    # ── 사이드바 ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header('⚙️ 설정')
        api_key = st.text_input(
            'Groq API Key',
            value=os.getenv('GROQ_API_KEY', ''),
            type='password', placeholder='gsk_...'
        )
        st.caption('무료 발급: console.groq.com')
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

    tab1, tab2, tab3 = st.tabs(['🔍 고위험 고객 탐색', '➕ 새 고객 분석', '📅 일별 모니터링'])

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


    # ════════════════════════════════════════════════════════════════════════
    # TAB 3: 일별 모니터링
    # ════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader('📅 날짜별 개입 대상 고객')
        st.caption('해당 날짜 기준으로 구독 14~20일차인 고객 = 3주차 진입 = 이탈 위험 최고 구간')

        # 날짜 데이터 로드 + 이탈 확률 병합
        df_dates  = load_membership_dates()
        df_scored2 = compute_all_probs()
        df_merged = df_scored2.merge(df_dates, on='USER_KEY', how='left')

        # 날짜 범위 계산
        min_date = df_merged['reg_date_decoded'].min().date()
        max_date = (df_merged['reg_date_decoded'].max() + pd.Timedelta(days=20)).date()

        selected_date = st.date_input(
            '날짜 선택',
            value=min_date + pd.Timedelta(days=14),
            min_value=min_date,
            max_value=max_date
        )
        selected_ts = pd.Timestamp(selected_date)

        # 구독 경과일 계산
        df_merged['sub_day'] = (selected_ts - df_merged['reg_date_decoded']).dt.days

        # 구간 분류
        def day_zone(d):
            if 18 <= d <= 20: return '🔴 긴급 (만료 직전)'
            elif 14 <= d <= 17: return '🟡 위험 (3주차 진입)'
            elif 7 <= d <= 13:  return '🟢 예방 (2주차)'
            else: return None

        df_merged['구간'] = df_merged['sub_day'].apply(day_zone)
        df_today = df_merged[df_merged['구간'].notna()].copy()
        df_today = df_today.sort_values(['sub_day', '이탈확률'], ascending=[False, False])

        # ── 오늘의 가입/이탈 현황 ───────────────────────────────────────────
        st.markdown('**📊 오늘의 구독 현황**')

        df_merged['end_date_decoded'] = df_merged['reg_date_decoded'] + pd.Timedelta(days=21)
        prev_ts = selected_ts - pd.Timedelta(days=1)

        # 오늘/어제 활성 구독자 (가입일 <= 날짜 < 만료일)
        active_today = ((df_merged['reg_date_decoded'] <= selected_ts) &
                        (df_merged['end_date_decoded'] >  selected_ts)).sum()
        active_prev  = ((df_merged['reg_date_decoded'] <= prev_ts) &
                        (df_merged['end_date_decoded'] >  prev_ts)).sum()
        active_delta = int(active_today) - int(active_prev)

        # 오늘 가입자
        new_today = (df_merged['reg_date_decoded'] == selected_ts).sum()

        # 오늘 만료자
        expire_today = df_merged[df_merged['end_date_decoded'] == selected_ts]
        expire_n     = len(expire_today)
        churn_n      = int((expire_today['is_repurchase'] == 0).sum()) if 'is_repurchase' in expire_today.columns else 0
        repurchase_n = int(expire_today['is_repurchase'].sum())         if 'is_repurchase' in expire_today.columns else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric('총 활성 구독자', f'{active_today:,}명',
                  f'{active_delta:+,}명' if active_delta != 0 else '변동 없음')
        c2.metric('신규 가입', f'{new_today:,}명')
        c3.metric('오늘 만료', f'{expire_n:,}명')
        c4.metric('이탈 확정', f'{churn_n:,}명',
                  f'{churn_n/expire_n:.1%}' if expire_n else '')
        c5.metric('재구매 확정', f'{repurchase_n:,}명',
                  f'{repurchase_n/expire_n:.1%}' if expire_n else '')

        st.divider()

        # ── 개입 대상 요약 ──────────────────────────────────────────────────
        red    = (df_today['구간'] == '🔴 긴급 (만료 직전)').sum()
        yellow = (df_today['구간'] == '🟡 위험 (3주차 진입)').sum()
        green  = (df_today['구간'] == '🟢 예방 (2주차)').sum()
        c1, c2, c3 = st.columns(3)
        c1.metric('🔴 긴급 개입', f'{red:,}명')
        c2.metric('🟡 위험 모니터링', f'{yellow:,}명')
        c3.metric('🟢 예방적 접근', f'{green:,}명')

        st.divider()

        # 구간 필터
        zone_filter = st.selectbox('구간 선택', ['전체', '🔴 긴급 (만료 직전)', '🟡 위험 (3주차 진입)', '🟢 예방 (2주차)'])
        if zone_filter != '전체':
            df_show = df_today[df_today['구간'] == zone_filter]
        else:
            df_show = df_today

        disp_cols = ['USER_KEY', '구간', 'sub_day', '이탈확률', 'age', 'dur_w3', 'avg_session_time']
        disp_cols = [c for c in disp_cols if c in df_show.columns]

        st.dataframe(
            df_show[disp_cols].rename(columns={'sub_day': '구독 경과일'})
            .style.background_gradient(subset=['이탈확률'], cmap='RdYlGn_r')
            .format({'이탈확률': '{:.1%}'}),
            use_container_width=True, height=300
        )

        st.divider()
        st.subheader('오늘의 개입 전략 생성')

        if len(df_show) == 0:
            st.info('해당 날짜에 개입 대상 고객이 없습니다.')
        else:
            sel_keys = df_show['USER_KEY'].astype(str).tolist()
            sel_user = st.selectbox('고객 선택', sel_keys, key='daily_user')

            if st.button('🚨 오늘의 개입 전략 생성', type='primary', use_container_width=True):
                if not api_key:
                    st.error('API Key를 입력해주세요')
                else:
                    row      = df_show[df_show['USER_KEY'].astype(str) == sel_user].iloc[0]
                    sub_day  = int(row.get('sub_day', 0))
                    customer = mask_future_features(row.to_dict(), sub_day)
                    prob_churn, shap_df = predict_customer(customer, model, explainer, features)
                    zone    = row.get('구간', '')

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric('구독 경과일', f'{sub_day}일차')
                    c2.metric('구간', zone)
                    c3.metric('이탈 확률', f'{prob_churn:.1%}')
                    c4.metric('남은 기간', f'{21 - sub_day}일')

                    col_a, col_b = st.columns([1, 2])
                    with col_a:
                        st.markdown('**이탈 원인 Top 5**')
                        for _, r in shap_df.head(5).iterrows():
                            direction = '⬇️ 이탈' if r['SHAP'] < 0 else '⬆️ 재구매'
                            st.write(f"`{r['변수']}` = {r['값']:.2f} → {direction}")
                    with col_b:
                        with st.spinner('Gemini가 오늘의 개입 전략 생성 중...'):
                            recommendation = generate_recommendation(customer, prob_churn, shap_df, api_key)
                        st.markdown(recommendation)


if __name__ == '__main__':
    main()
