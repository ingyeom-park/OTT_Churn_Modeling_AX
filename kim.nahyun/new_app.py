import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
from sklearn.decomposition import PCA

# pandas 2.x에서 모든 문자열을 ArrowStringArray(LargeUtf8)로 저장하는 동작 비활성화
# → 구버전 Streamlit의 LargeUtf8 직렬화 오류 방지
try:
    pd.options.future.infer_string = False
except AttributeError:
    pass
from sklearn.preprocessing import StandardScaler

# ==========================================
# 1. 페이지 설정 및 커스텀 CSS
# ==========================================
st.set_page_config(page_title="100원 프로모션 이탈 방어 대시보드", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 1rem; }

    /* 사이드바 라디오 → 탭 스타일 */
    section[data-testid="stSidebar"] .stRadio > div {
        flex-direction: column !important;
        gap: 0px !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        width: 100% !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        margin: 3px 0 !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        border: 1px solid #e0e0e0 !important;
        background: #ffffff !important;
        color: #444 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: #fff0f0 !important;
        border-color: #E57373 !important;
        color: #1a1a1a !important;
    }
    section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked),
    section[data-testid="stSidebar"] .stRadio [aria-checked="true"] {
        background: #E57373 !important;
        color: white !important;
        border-color: #E57373 !important;
    }
    /* 라디오 원형 점 숨기기 */
    section[data-testid="stSidebar"] .stRadio [role="radio"],
    section[data-testid="stSidebar"] .stRadio span[data-testid="stMarkdownContainer"] ~ div {
        display: none !important;
    }
    section[data-testid="stSidebar"] .stRadio label > div:first-child {
        display: none !important;
    }

    .risk-card {
        border-radius: 8px;
        padding: 15px 10px;
        color: #333;
        background-color: #ffffff;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border: 1px solid #e0e0e0;
    }
    .card-title   { font-size: 13px; font-weight: 600; margin-bottom: 5px; color: #555; }
    .card-value   { font-size: 24px; font-weight: 800; margin: 0; line-height: 1.1; }
    .card-unit    { font-size: 12px; font-weight: normal; color: #777; }
    .card-percent { font-size: 11px; font-weight: 400; color: #888; margin-top: 2px; }

    .border-very-high { border-top: 4px solid #EA002C; }
    .border-high      { border-top: 4px solid #FF7A00; }
    .border-medium    { border-top: 4px solid #fbc02d; }
    .border-low       { border-top: 4px solid #388e3c; }

    .cluster-card {
        border-radius: 8px;
        padding: 10px 9px;
        background-color: #fafafa;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
        font-size: 13px;
        line-height: 1.6;
    }
    .cluster-title { font-size: 15px; font-weight: 700; margin-bottom: 6px; }

    hr { margin: 15px 0 !important; }
    </style>
""", unsafe_allow_html=True)

COLOR_MAP = {
    ' C1 (헤비유저형)': '#FF8FA3',   # pastel rose
    ' C0 (맛보기형)':   '#FFB347',   # pastel orange
    ' C3 (휴면형)':     '#64B5F6',   # pastel blue
    ' C2 (후반몰입형)': '#81C784',   # pastel green
}
CLUSTER_MAP = {
    0: ' C3 (휴면형)',      # total=1회, recency=15일 → 사실상 미접속
    1: ' C1 (헤비유저형)',
    2: ' C2 (후반몰입형)',
    3: ' C0 (맛보기형)',    # 5분미만 비율 74%, w1>w2>w3 감소
}
PATTERN_MAP = {
    ' C0 (맛보기형)':   '짧은 시청 후 이탈',
    ' C1 (헤비유저형)': '장기 충성 시청',
    ' C2 (후반몰입형)':     '점진적 몰입 성장',
    ' C3 (휴면형)':     '가입 후 사실상 미접속'
}
ACTION_MAP = {
    ' C0 (맛보기형)': '맞춤 콘텐츠 추천 메일',
    ' C1 (헤비유저형)':  '후속 시리즈 큐레이션',
    ' C2 (후반몰입형)':    'VIP 전환 혜택 제안',
    ' C3 (휴면형)':  '재참여 알림 + 할인 쿠폰'
}

# ==========================================
# 2. 데이터 로드 및 캐싱
# ==========================================
DATA_FILE         = os.path.join(os.path.dirname(os.path.abspath(__file__)), '데이터', 'Membership_v4_churn_clustered.csv')
DATA_FILE_ALL     = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Membership_v4.csv')
DATA_FILE_DERIVED = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kim.kwangil', 'derived_variable', '260513_derived_membership.csv')

@st.cache_data
def load_data():
    df_all = pd.read_csv(DATA_FILE_ALL, encoding='utf-8-sig')
    total_all = len(df_all)

    df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
    # ArrowStringArray → object 변환 (구버전 Streamlit LargeUtf8 오류 방지)
    for col in df.select_dtypes(include=['string']).columns:
        df[col] = df[col].astype(object)

    promo = df[df['is_promotion'] == 1].drop_duplicates().reset_index(drop=True)

    promo['is_churn']     = (promo['is_repurchase'] == 0).astype(int)
    promo['cluster_name'] = promo['cluster'].map(CLUSTER_MAP).astype(object)
    promo['gender_kor']   = promo['gender'].map({'F': '여성', 'M': '남성', 'N': '기타'}).astype(object)
    promo['plan'] = '베이직'
    promo.loc[promo['is_standard'] == 1, 'plan'] = '스탠다드'
    promo.loc[promo['is_premium']  == 1, 'plan'] = '프리미엄'

    # 행동 기반 위험 점수 (모델 대용)
    promo['risk_base'] = np.where(
        promo['is_only_w1'] == 1, 90,
        np.where(
            promo['watch_time(min)_w3'] == 0, 72,
            np.where(promo['retention_w3_ratio'].fillna(0) < 0.3, 52, 20)
        )
    )
    rng = np.random.default_rng(42)
    promo['churn_score'] = (promo['risk_base'] + rng.normal(0, 4, len(promo))).clip(0, 99.9)

    # PCA
    pca_cols = [
        'watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3',
        'total_watch_time(min)', 'avg_watch_time(min)',
        'retention_w2_ratio', 'retention_w3_ratio',
        'active_ratio', 'genre_diversity_count', 'recency'
    ]
    X = promo[pca_cols].fillna(0)
    X_sc = StandardScaler().fit_transform(X)
    pcs = PCA(n_components=2, random_state=42).fit_transform(X_sc)
    promo['PC1'] = pcs[:, 0]
    promo['PC2'] = pcs[:, 1]

    pca_sample = (
        promo.groupby('cluster', group_keys=False)
             .apply(lambda g: g.sample(min(200, len(g)), random_state=42))
             .reset_index(drop=True)
    )

    # 비프로모션 비교용 데이터
    df_derived = pd.read_csv(DATA_FILE_DERIVED, encoding='utf-8-sig')
    nonpromo = df_derived[df_derived['is_promotion'] == 0].copy().reset_index(drop=True)
    nonpromo['is_churn']   = (nonpromo['is_repurchase'] == 0).astype(int)
    nonpromo['gender_kor'] = nonpromo['gender'].map({'F': '여성', 'M': '남성', 'N': '기타'})
    nonpromo['plan'] = '베이직'
    nonpromo.loc[nonpromo['is_standard'] == 1, 'plan'] = '스탠다드'
    nonpromo.loc[nonpromo['is_premium']  == 1, 'plan'] = '프리미엄'

    return promo, pca_sample, total_all, nonpromo


def fmt_min(m):
    m = int(m)
    if m >= 60:
        return f"{m // 60}시간 {m % 60}분"
    return f"{m}분"


promo_df, pca_df, TOTAL_ALL, nonpromo_df = load_data()
promo_df    = promo_df[promo_df['age_group'] != 70].reset_index(drop=True)
nonpromo_df = nonpromo_df[nonpromo_df['age_group'] != 70].reset_index(drop=True)
TOTAL = len(promo_df)
CONVERTED = int(promo_df['is_repurchase'].sum())
CHURNED   = int(promo_df['is_churn'].sum())

# 이탈 고위험군 (모델 예측 결과)
_CHURN_PROBA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'churn_proba_B.csv')
try:
    _prob_df = pd.read_csv(_CHURN_PROBA_FILE, encoding='utf-8-sig')
    _prob_df = _prob_df.groupby('USER_KEY', as_index=False).agg({'churn_proba': 'mean', 'is_high_risk': 'max'})
    promo_df = promo_df.merge(_prob_df[['USER_KEY', 'churn_proba', 'is_high_risk']], on='USER_KEY', how='left')
    HIGH_RISK_COUNT = int(promo_df['is_high_risk'].sum())
    HIGH_RISK_RATIO = promo_df['is_high_risk'].mean() * 100
except Exception:
    HIGH_RISK_COUNT = None
    HIGH_RISK_RATIO = None

HR_LABEL = f"{HIGH_RISK_COUNT:,} 명" if HIGH_RISK_COUNT is not None else "- 명"
HR_DELTA = f"즉시 대응 필요 ({HIGH_RISK_RATIO:.1f}%)" if HIGH_RISK_RATIO is not None else "즉시 대응 필요"

# ==========================================
# 3. 좌측 사이드바 (탭 스타일)
# ==========================================
with st.sidebar:
    st.title("🎯 Retention Lab")
    st.caption("2021년 프로모션 이탈 방어 시스템")
    st.markdown(f"""
    <div style="background:#FFE0B2; border-radius:10px; padding:12px 14px;
                margin:8px 0 4px 0;">
      <div style="font-size:11px; color:#BF360C; margin-bottom:5px;">
        📡 2021년 &nbsp;·&nbsp; SKT OTT &nbsp;·&nbsp; 100원 체험 프로모션
      </div>
      <div style="font-size:13px; line-height:1.6; margin-bottom:8px; color:#333;">
        가입자 <b>{TOTAL:,}명</b> 중<br>
        <b style="font-size:1.15rem; color:#E07830;">{CHURNED/TOTAL*100:.1f}%</b>
        <span style="font-size:12px; color:#555;"> 유료 전환 없이 이탈</span>
      </div>
      <div style="font-size:11px; color:#666; line-height:1.8;">
        📅 분석 기간 : 2021년 3월 (1~3주차)<br>
        🎯 분석 목적 : 4주차 유료 전환율 제고<br>
        🔬 분석 방법 : K-Means 군집화 + 행동 기반 위험 점수
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("분석 메뉴", [
        "🏠 종합 현황",
        "🛡️ 이탈 방어 전략",
        "👥 프로모션 행동 분석",
        "⚙️ 예측 모델 설정"
    ], label_visibility="collapsed")

# ==========================================
# 4-0. 종합 현황 (Main)
# ==========================================
if menu == "🏠 종합 현황":
    st.markdown(
        "<h1 style='font-size:2rem; font-weight:800; margin-bottom:2px;'>"
        "고객 이탈 현황</h1>",
        unsafe_allow_html=True,
    )

    # 군집 통계 (탭 공통 사전 계산)
    cstats_m = promo_df.groupby(['cluster', 'cluster_name']).agg(
        총인원=('USER_KEY', 'count'),
        이탈자=('is_churn', 'sum'),
    ).reset_index().sort_values('cluster')
    cstats_m['이탈률'] = cstats_m['이탈자'] / cstats_m['총인원'] * 100
    cstats_m['비중']   = cstats_m['총인원'] / TOTAL * 100

    # 탭 공통 사전 계산 (plan_color_map, plan_stats)
    plan_color_map = {'베이직': '#90caf9', '스탠다드': '#FFA040', '프리미엄': '#E05070'}
    plan_stats = promo_df.groupby('plan').agg(
        인원=('USER_KEY', 'count'),
        이탈=('is_churn', 'sum'),
    ).reset_index()
    plan_stats['이탈률'] = (plan_stats['이탈'] / plan_stats['인원'] * 100).round(1)
    plan_stats['비중']   = (plan_stats['인원'] / TOTAL * 100).round(1)

    tab0, tab1, tab2 = st.tabs(["고객 현황", "군집 분포", "세부 인구통계 분석"])

    # ── 탭0: 전체 고객 현황 ────────────────────────────────────────────
    with tab0:
        # 미니 KPI
        ov1, ov2, ov3 = st.columns(3)
        _age_churn_tab0    = promo_df.groupby('age_group')['is_churn'].mean()
        _top_churn_age     = int(_age_churn_tab0.idxmax())
        _top_churn_age_rate = _age_churn_tab0.max() * 100
        ov1.metric("총 프로모션 가입자", f"{TOTAL:,} 명",             f"전체의 {TOTAL/TOTAL_ALL*100:.1f}%", delta_color="off")
        ov2.metric("이탈률",                f"{CHURNED/TOTAL*100:.1f} %", f"{CHURNED:,}명 이탈",               delta_color="inverse")
        # ov3.metric("이탈률 1위 연령대",      f"{_top_churn_age}대",        f"이탈률 {_top_churn_age_rate:.1f}%", delta_color="inverse")
        ov3.metric("이탈 고위험군",         HR_LABEL,                     HR_DELTA,                            delta_color="inverse")

        st.markdown("<hr style='margin:14px 0;'>", unsafe_allow_html=True)

        # ── 이탈률 2종 ────────────────────────────────────────────
        ch1, ch2 = st.columns([3, 2])

        with ch1:
            st.caption("**성별 및 나이대별 이탈률**")
            gen_age_churn = (
                promo_df[promo_df['gender_kor'].isin(['남성', '여성'])]
                .groupby(['age_group', 'gender_kor'])['is_churn']
                .mean()
                .reset_index()
            )
            gen_age_churn['이탈률'] = (gen_age_churn['is_churn'] * 100).round(1)
            gen_age_churn['나이대'] = gen_age_churn['age_group'].astype(int).astype(str) + '대'
            gen_age_churn = gen_age_churn.rename(columns={'gender_kor': '성별'})
            gen_age_churn = gen_age_churn.sort_values('age_group')

            fig_ga = px.bar(
                gen_age_churn, x='나이대', y='이탈률', color='성별',
                barmode='group',
                color_discrete_map={'남성': '#5B8DD9', '여성': '#D4609A'},
                text='이탈률',
            )
            fig_ga.update_traces(texttemplate='%{text:.1f}%', textposition='outside', textfont_size=10)
            fig_ga.update_layout(
                height=400, margin=dict(t=30, b=10, l=0, r=10),
                plot_bgcolor='white',
                yaxis=dict(gridcolor='#f0f0f0', title='이탈률 (%)', range=[20, 40]),
                xaxis_title='',
                legend=dict(
                    orientation='v', x=1.01, y=1, xanchor='left', yanchor='top',
                    bgcolor='rgba(255,255,255,0.9)', bordercolor='#e0e0e0', borderwidth=1,
                    font=dict(size=12),
                ),
            )
            st.plotly_chart(fig_ga, use_container_width=True)

        with ch2:
            cr_baseline = CHURNED / TOTAL * 100
            st.caption("**요금제별 이탈률**")
            plan_order_ch2 = ['베이직', '스탠다드', '프리미엄']
            plan_cr  = [promo_df[promo_df['plan'] == p]['is_churn'].mean() * 100 for p in plan_order_ch2]
            plan_n   = [int((promo_df['plan'] == p).sum()) for p in plan_order_ch2]
            plan_clr = [plan_color_map[p] for p in plan_order_ch2]

            fig_plan_bar = go.Figure()
            fig_plan_bar.add_trace(go.Bar(
                x=plan_order_ch2,
                y=plan_cr,
                marker_color=plan_clr,
                text=[f'{cr:.1f}%' for cr in plan_cr],
                textposition='outside',
                textfont=dict(size=13, color='#333'),
                hovertemplate='<b>%{x}</b><br>이탈률: %{y:.1f}%<extra></extra>',
            ))
            for x_val, n_val in zip(plan_order_ch2, plan_n):
                fig_plan_bar.add_annotation(
                    x=x_val, y=0, text=f'{n_val:,}명',
                    showarrow=False, yanchor='bottom', yshift=6,
                    font=dict(size=11, color='#555'),
                )
            fig_plan_bar.add_hline(
                y=cr_baseline, line_dash='dash', line_color='#888', line_width=1.5,
                annotation_text=f'평균 {cr_baseline:.1f}%',
                annotation_position='top right',
                annotation_font=dict(size=11, color='#555'),
            )
            fig_plan_bar.update_layout(
                height=400,
                margin=dict(t=30, b=10, l=0, r=10),
                plot_bgcolor='white',
                xaxis=dict(title='', tickfont=dict(size=13)),
                yaxis=dict(gridcolor='#f0f0f0', title='이탈률 (%)',
                           range=[0, max(plan_cr) * 1.3], zeroline=False),
                showlegend=False,
            )
            st.plotly_chart(fig_plan_bar, use_container_width=True)

        # ── 가입자 구성 차트 준비 ────────────────────────────────────────
        _t0_g_df = (
            promo_df[promo_df['gender_kor'].isin(['남성', '여성'])]
            .groupby('gender_kor')['USER_KEY'].count().reset_index()
        )
        _t0_g_df.columns = ['성별', '인원']
        _t0_g_labels = _t0_g_df['성별'].tolist()
        _t0_g_values = _t0_g_df['인원'].tolist()
        _t0_g_colors = [{'남성': '#5B8DD9', '여성': '#D4609A'}[l] for l in _t0_g_labels]
        fig_t0_gen = go.Figure(go.Pie(
            labels=_t0_g_labels, values=_t0_g_values, hole=0.55,
            marker=dict(colors=_t0_g_colors, line=dict(color='white', width=2)),
            textinfo='label+percent', textfont=dict(size=12, color='black'),
            insidetextorientation='horizontal', automargin=True,
            hovertemplate='<b>%{label}</b><br>인원: %{value:,}명<br>비중: %{percent}<extra></extra>',
        ))
        fig_t0_gen.update_layout(height=225, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)

        _t0_age = promo_df.groupby('age_group')['USER_KEY'].count().reset_index()
        _t0_age.columns = ['나이대', '인원']
        _t0_age['나이대'] = _t0_age['나이대'].astype(str) + '대'
        _t0_age['비중']   = (_t0_age['인원'] / TOTAL * 100).round(1)
        fig_t0_age_dist = px.bar(_t0_age, x='나이대', y='인원',
            text=_t0_age['비중'].astype(str) + '%',
            color='인원', color_continuous_scale=['#FFE0B2', '#FF7A00'])
        fig_t0_age_dist.update_traces(textposition='outside')
        fig_t0_age_dist.update_layout(height=230, margin=dict(t=30, b=10, l=0, r=0),
            coloraxis_showscale=False,
            yaxis=dict(range=[0, _t0_age['인원'].max() * 1.45], title='인원 수'), xaxis_title='')

        _t0_p_labels = plan_stats['plan'].tolist()
        _t0_p_values = plan_stats['인원'].tolist()
        _t0_p_colors = [plan_color_map[p] for p in _t0_p_labels]
        fig_t0_plan = go.Figure(go.Pie(
            labels=_t0_p_labels, values=_t0_p_values, hole=0.55,
            marker=dict(colors=_t0_p_colors, line=dict(color='white', width=2)),
            textinfo='label+percent', textfont=dict(size=12, color='black'),
            insidetextorientation='horizontal', automargin=True,
            hovertemplate='<b>%{label}</b><br>인원: %{value:,}명<br>비중: %{percent}<extra></extra>',
        ))
        fig_t0_plan.update_layout(height=225, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)

        # ── 이탈 집중 구간 데이터 준비 ───────────────────────────────────
        _t0c_age_df = promo_df.groupby('age_group')['is_churn'].agg(['mean', 'count']).reset_index()
        _t0c_age_df.columns = ['나이대', '이탈률', '인원']
        _t0c_age_df['이탈률'] *= 100
        _t0c_age_df['나이대_str'] = _t0c_age_df['나이대'].astype(str) + '대'

        _t0c_gen_df = promo_df[promo_df['gender_kor'].isin(['여성', '남성'])].groupby('gender_kor').agg(
            이탈률=('is_churn', 'mean'), 인원=('USER_KEY', 'count')
        ).reset_index()
        _t0c_gen_df['이탈률'] *= 100
        _t0c_gen_df.columns = ['성별', '이탈률', '인원']

        _t0c_cr_avg     = CHURNED / TOTAL * 100
        _t0c_top_age    = _t0c_age_df.loc[_t0c_age_df['이탈률'].idxmax(), '나이대_str']
        _t0c_top_age_rt = _t0c_age_df['이탈률'].max()
        _t0c_gen_gap    = abs(_t0c_gen_df['이탈률'].max() - _t0c_gen_df['이탈률'].min())
        _t0c_high_gen   = _t0c_gen_df.loc[_t0c_gen_df['이탈률'].idxmax(), '성별']
        _t0c_top_plan   = plan_stats.loc[plan_stats['이탈률'].idxmax()]

        fig_t0c_age = px.bar(_t0c_age_df, x='나이대_str', y='이탈률',
            text=_t0c_age_df['이탈률'].round(1).astype(str) + '%',
            color='이탈률', color_continuous_scale=['#f0c4b0', '#c0392b'], range_color=[0, 60],
            labels={'나이대_str': '나이대'})
        fig_t0c_age.update_traces(textposition='outside')
        fig_t0c_age.add_hline(y=_t0c_cr_avg, line_dash='dash', line_color='#888', line_width=1.5,
            annotation_text=f'평균 {_t0c_cr_avg:.1f}%', annotation_position='bottom right',
            annotation_font=dict(size=10, color='#555'))
        fig_t0c_age.update_layout(height=300, margin=dict(t=10, b=5, l=0, r=0),
            coloraxis_showscale=False, plot_bgcolor='white',
            yaxis=dict(gridcolor='#f0f0f0', title='이탈률 (%)', range=[0, _t0c_age_df['이탈률'].max() * 1.3]),
            xaxis_title='')

        fig_t0c_gen = px.bar(_t0c_gen_df, x='성별', y='이탈률',
            text=_t0c_gen_df['이탈률'].round(1).astype(str) + '%',
            color='성별', color_discrete_map={'여성': '#D4609A', '남성': '#5B8DD9'})
        fig_t0c_gen.update_traces(textposition='outside')
        fig_t0c_gen.add_hline(y=_t0c_cr_avg, line_dash='dash', line_color='#888', line_width=1.5,
            annotation_text=f'평균 {_t0c_cr_avg:.1f}%', annotation_position='bottom right',
            annotation_font=dict(size=10, color='#555'))
        fig_t0c_gen.update_layout(height=300, margin=dict(t=10, b=5, l=0, r=0),
            showlegend=False, plot_bgcolor='white',
            yaxis=dict(gridcolor='#f0f0f0', title='이탈률 (%)', range=[0, _t0c_gen_df['이탈률'].max() * 1.3]),
            xaxis_title='')

        # ── 나이대/성별 주차별 시청 추이 데이터 준비 ────────────────────────
        _t0w_cols = ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']
        _t0_age_rows = []
        for _ag in sorted(promo_df['age_group'].unique()):
            _grp = promo_df[promo_df['age_group'] == _ag][_t0w_cols].mean()
            for _wk, _cw in zip(['1주차', '2주차', '3주차'], _t0w_cols):
                _t0_age_rows.append({'나이대': f"{int(_ag)}대", '주차': _wk, '평균 시청(분)': round(_grp[_cw], 1)})
        _t0_age_line_df = pd.DataFrame(_t0_age_rows)

        _t0_gen_rows = []
        for _g in ['남성', '여성']:
            _grp = promo_df[promo_df['gender_kor'] == _g][_t0w_cols].mean()
            for _wk, _cw in zip(['1주차', '2주차', '3주차'], _t0w_cols):
                _t0_gen_rows.append({'성별': _g, '주차': _wk, '평균 시청(분)': round(_grp[_cw], 1)})
        _t0_gen_line_df = pd.DataFrame(_t0_gen_rows)

        fig_t0_age_line = px.line(_t0_age_line_df, x='주차', y='평균 시청(분)', color='나이대',
            markers=True, text='평균 시청(분)')
        fig_t0_age_line.update_traces(textposition='top center', textfont_size=10, line_width=2, marker_size=7)
        fig_t0_age_line.update_layout(height=300, margin=dict(t=10, b=5, l=0, r=120),
            plot_bgcolor='white', xaxis_title='',
            yaxis=dict(gridcolor='#f0f0f0', title='평균 시청 시간 (분)'),
            legend=dict(orientation='v', x=1.01, y=1, xanchor='left', yanchor='top',
                bgcolor='rgba(255,255,255,0.9)', bordercolor='#e0e0e0', borderwidth=1,
                font=dict(size=11), title=dict(text='나이대', font=dict(size=11))))

        fig_t0_gen_line = px.line(_t0_gen_line_df, x='주차', y='평균 시청(분)', color='성별',
            markers=True, color_discrete_map={'남성': '#5B8DD9', '여성': '#D4609A'}, text='평균 시청(분)')
        fig_t0_gen_line.update_traces(textposition='top center', textfont_size=11, line_width=2.5, marker_size=9)
        fig_t0_gen_line.update_layout(height=300, margin=dict(t=10, b=5, l=0, r=120),
            plot_bgcolor='white', xaxis_title='',
            yaxis=dict(gridcolor='#f0f0f0', title='평균 시청 시간 (분)'),
            legend=dict(orientation='v', x=1.01, y=1, xanchor='left', yanchor='top',
                bgcolor='rgba(255,255,255,0.9)', bordercolor='#e0e0e0', borderwidth=1, font=dict(size=12)))

        # ── 하나의 expander: 가입자 구성 + 이탈 집중 구간 ─────────────────
        with st.expander("세부 분석 보기 (가입자 구성 · 이탈 집중 구간)", expanded=False):
            col_a0, col_b0, col_c0 = st.columns([2, 3, 2])
            with col_a0:
                st.caption("**가입자 성별 분포**")
                st.plotly_chart(fig_t0_gen, use_container_width=True)
            with col_b0:
                st.caption("**가입자 나이대 분포**")
                st.plotly_chart(fig_t0_age_dist, use_container_width=True)
            with col_c0:
                st.caption("**가입자 요금제 분포**")
                st.plotly_chart(fig_t0_plan, use_container_width=True)

            st.markdown("""<div style="display:flex; align-items:center; margin:16px 0 12px 0; gap:12px;">
              <span style="font-size:13px; font-weight:600; color:#4472C4; white-space:nowrap;">세그먼트별 이탈 위험도 파악</span>
              <div style="flex:1; height:1px; background:#e0e0e0;"></div>
            </div>""", unsafe_allow_html=True)

            mk1, mk2, mk3, mk4 = st.columns(4)
            mk1.metric("전체 이탈률",     f"{_t0c_cr_avg:.1f} %",          f"{CHURNED:,}명 이탈",                   delta_color="inverse")
            mk2.metric("최고위험 나이대",  _t0c_top_age,                     f"이탈률 {_t0c_top_age_rt:.1f}%",        delta_color="inverse")
            mk3.metric("성별 이탈률 격차", f"{_t0c_gen_gap:.1f} %p",         f"{_t0c_high_gen}이 더 높음",            delta_color="inverse")
            mk4.metric("최고위험 요금제",  _t0c_top_plan['plan'],            f"이탈률 {_t0c_top_plan['이탈률']:.1f}%", delta_color="inverse")

            cr1, cr2 = st.columns(2)
            with cr1:
                st.caption("**나이대별 이탈률 (%)**")
                st.plotly_chart(fig_t0c_age, use_container_width=True)
            with cr2:
                st.caption("**성별 이탈률 (%)**")
                st.plotly_chart(fig_t0c_gen, use_container_width=True)

            st.markdown("""<div style="display:flex; align-items:center; margin:16px 0 12px 0; gap:12px;">
              <span style="font-size:13px; font-weight:600; color:#4472C4; white-space:nowrap;">세그먼트별 주차 시청 추이</span>
              <div style="flex:1; height:1px; background:#e0e0e0;"></div>
            </div>""", unsafe_allow_html=True)

            tr1, tr2 = st.columns(2)
            with tr1:
                st.caption("**나이대별 주차별 평균 시청 시간 추이**")
                st.plotly_chart(fig_t0_age_line, use_container_width=True)
            with tr2:
                st.caption("**성별 주차별 평균 시청 시간 추이**")
                st.plotly_chart(fig_t0_gen_line, use_container_width=True)

    # ── 탭1: 군집 분포 ─────────────────────────────────────────────────
    with tab1:
        # KPI 행
        top_churn_row  = cstats_m.loc[cstats_m['이탈률'].idxmax()]
        top_churn_name = top_churn_row['cluster_name'].strip().split('(')[-1].rstrip(')')
        top_churn_rate = top_churn_row['이탈률']

        _plan_order_kpi    = ['베이직', '스탠다드', '프리미엄']
        _cluster_order_kpi = [' C0 (맛보기형)', ' C1 (헤비유저형)', ' C2 (후반몰입형)', ' C3 (휴면형)']
        _cross_rows_kpi = []
        for _plan in _plan_order_kpi:
            for _cname in _cluster_order_kpi:
                _sub = promo_df[(promo_df['plan'] == _plan) & (promo_df['cluster_name'] == _cname)]
                if len(_sub) == 0:
                    continue
                _cross_rows_kpi.append({'plan': _plan, 'cluster': _cname.strip().split('(')[-1].rstrip(')'),
                                        'n': len(_sub), 'cr': _sub['is_churn'].mean() * 100})
        _cross_df_kpi = pd.DataFrame(_cross_rows_kpi)
        _top_cross    = _cross_df_kpi.loc[_cross_df_kpi['cr'].idxmax()]

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("총 프로모션 가입자", f"{TOTAL:,} 명",  f"전체의 {TOTAL/TOTAL_ALL*100:.1f}%", delta_color="off")
        kpi2.metric("최다 이탈 군집",     top_churn_name,   f"이탈률 {top_churn_rate:.1f}%",      delta_color="inverse")
        kpi3.metric("이탈 집중 구간",
                    f"{_top_cross['plan']} × {_top_cross['cluster'].split('(')[-1].rstrip(')')}",
                    f"이탈률 {_top_cross['cr']:.1f}%",
                    delta_color="inverse")
        kpi4.metric("이탈 고위험군",       HR_LABEL,         HR_DELTA,                             delta_color="inverse")

        cl_names  = cstats_m['cluster_name'].tolist()
        cl_colors = [COLOR_MAP.get(n, '#999') for n in cl_names]
        cl_labels = [n.strip().split('(')[-1].rstrip(')') if '(' in n else n.strip() for n in cl_names]

        
        CLUSTER_LABEL_M  = {' C0 (맛보기형)': '맛보기형', ' C1 (헤비유저형)': '헤비유저형',
                            ' C2 (후반몰입형)': '안정형',   ' C3 (휴면형)': '휴면형'}
        CLUSTER_DESC_M   = {
            ' C0 (맛보기형)':   '평균 시청 13분, 5분 미만 시청 비율 높음. 콘텐츠를 시작하지만 완주 못하고 이탈.',
            ' C1 (헤비유저형)': '총 시청 827분, 장르 다양성 최고(5.25). 가장 충성도 높은 핵심 고객군.',
            ' C2 (후반몰입형)': '3주차 리텐션 51.9%로 전 군집 중 최고. 시간이 갈수록 몰입도 상승하는 성장 패턴.',
            ' C3 (휴면형)':     '시청 횟수 평균 1회, 최근 접속 15일. 가입 후 사실상 미접속 상태.'
        }
        CLUSTER_NUM_M = {
            ' C0 (맛보기형)':   '평균 시청 13분 · 5분 미만 비율 높음',
            ' C1 (헤비유저형)': '총 시청 827분 · 장르 다양성 5.25',
            ' C2 (후반몰입형)': '3주차 리텐션 51.9% — 전 군집 최고',
            ' C3 (휴면형)':     '시청 횟수 1회 · 최근 접속 15일',
        }
        CLUSTER_TXT_M = {
            ' C0 (맛보기형)':   '콘텐츠를 시작하지만 완주 못하고 이탈',
            ' C1 (헤비유저형)': '가장 충성도 높은 핵심 고객군',
            ' C2 (후반몰입형)': '시간이 갈수록 몰입도 상승하는 성장 패턴',
            ' C3 (휴면형)':     '가입 후 사실상 미접속 상태',
        }
        CLUSTER_BORDER_M = {' C0 (맛보기형)': '#FFB347', ' C1 (헤비유저형)': '#FF8FA3',
                            ' C2 (후반몰입형)': '#81C784', ' C3 (휴면형)': '#64B5F6'}

        def churn_badge_color(rate):
            if rate >= 40:   return '#e53935', '#ffebee'
            elif rate >= 25: return '#FF7A00', '#fff3e0'
            else:            return '#2e7d32', '#e8f5e9'

        # ── 군집별 이탈률 + 군집 × 요금제별 이탈률 비교 (1:3 행) ──────────────────────
        st.markdown("<hr style='margin:20px 0 12px 0;'>", unsafe_allow_html=True)
        col_left, col_right = st.columns([1.5, 3])

        with col_left:
            st.caption("**군집별 이탈률**")
            churn_sorted = cstats_m.sort_values('이탈률', ascending=True)
            _cr_avg_bar  = promo_df['is_churn'].mean() * 100
            bar_colors   = [COLOR_MAP.get(n, '#999') for n in churn_sorted['cluster_name']]
            churn_names = [n.strip().split('(')[-1].rstrip(')') if '(' in n else n.strip() for n in churn_sorted['cluster_name']]
            churn_rates = churn_sorted['이탈률'].round(1).tolist()
            fig_churn_bar = go.Figure(go.Bar(
                y=churn_names,
                x=churn_rates,
                orientation='h',
                marker=dict(color=bar_colors),
                text=churn_names,
                textposition='inside',
                textfont=dict(size=12, color='white', family='Arial'),
                hovertemplate='<b>%{y}</b><br>이탈률: %{x:.1f}%<extra></extra>',
            ))
            for name, rate in zip(churn_names, churn_rates):
                _num_color = '#e53935' if rate > _cr_avg_bar else '#333'
                _num_text = f'<b>{rate:.1f}%</b>' if rate > _cr_avg_bar else f'{rate:.1f}%'
                fig_churn_bar.add_annotation(
                    x=rate, y=name,
                    text=_num_text,
                    showarrow=False,
                    xanchor='left',
                    xshift=6,
                    font=dict(size=12, color=_num_color),
                )
            fig_churn_bar.update_layout(
                height=315, margin=dict(t=10, b=10, l=10, r=60),
                plot_bgcolor='white',
                xaxis=dict(gridcolor='#f0f0f0', title='이탈률 (%)',
                           range=[0, 50]),
                yaxis=dict(title='', showticklabels=False),
            )
            st.plotly_chart(fig_churn_bar, use_container_width=True)

        with col_right:
            plan_order    = ['베이직', '스탠다드', '프리미엄']
            cluster_order = [' C0 (맛보기형)', ' C1 (헤비유저형)', ' C2 (후반몰입형)', ' C3 (휴면형)']

            cross_df  = _cross_df_kpi.copy()
            top_cross = _top_cross

            # 군집별 요금제 그룹 막대차트
            cr_avg = promo_df['is_churn'].mean() * 100

            st.markdown(
                f'<small style="color:rgba(49,51,63,0.6);">'
                f'<b>군집 × 요금제별 이탈률 비교</b>'
                f' - 점선 = 전체 평균 {cr_avg:.1f}% · 같은 군집 안에서 요금제 차이를 비교'
                f'</small>',
                unsafe_allow_html=True,
            )
            cluster_order_bar = ['맛보기형', '헤비유저형', '후반몰입형', '휴면형']
            cluster_short_to_full = {
                '맛보기형':  ' C0 (맛보기형)',
                '헤비유저형': ' C1 (헤비유저형)',
                '후반몰입형': ' C2 (후반몰입형)',
                '휴면형':    ' C3 (휴면형)',
            }
            plan_colors_bar   = {'베이직': '#90caf9', '스탠다드': '#FFA040', '프리미엄': '#E05070'}

            fig_bar = go.Figure()
            for _plan in ['베이직', '프리미엄', '스탠다드']:
                y_vals, x_vals = [], []
                for _cname_bare in cluster_order_bar:
                    _cname_full = cluster_short_to_full[_cname_bare]
                    _sub = promo_df[(promo_df['plan'] == _plan) & (promo_df['cluster_name'] == _cname_full)]
                    cr = _sub['is_churn'].mean() * 100 if len(_sub) > 0 else 0
                    y_vals.append(round(cr, 1))
                    x_vals.append(_cname_bare)
                fig_bar.add_trace(go.Bar(
                    name=_plan,
                    x=x_vals,
                    y=y_vals,
                    marker_color=plan_colors_bar[_plan],
                    text=[f'{v:.1f}%' for v in y_vals],
                    textposition='outside',
                    textfont=dict(size=11, color=['#e53935' if v > cr_avg else '#333' for v in y_vals]),
                ))

            fig_bar.add_hline(
                y=cr_avg, line_dash='dash', line_color='#888', line_width=1.5,
                annotation_text=f'평균 {cr_avg:.1f}%',
                annotation_position='bottom right',
                annotation_font=dict(size=11, color='#555'),
            )
            fig_bar.update_layout(
                barmode='group',
                height=315,
                margin=dict(t=20, b=10, l=50, r=20),
                plot_bgcolor='white',
                xaxis=dict(title='', tickfont=dict(size=12)),
                yaxis=dict(title='이탈률 (%)', gridcolor='#f0f0f0', zeroline=False,
                           range=[0, cross_df['cr'].max() * 1.25]),
                legend=dict(orientation='h', yanchor='bottom', y=1.01,
                            xanchor='left', x=0, font=dict(size=12)),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("<hr style='margin:20px 0 12px 0;'>", unsafe_allow_html=True)
        col_pie, col_prof = st.columns([2, 5])

        with col_pie:
            st.caption("**군집별 인원 비중**")
            fig_pie = go.Figure(go.Pie(
                labels=cl_labels,
                values=cstats_m['총인원'].tolist(),
                hole=0.5,
                marker=dict(colors=cl_colors, line=dict(color='white', width=2)),
                textinfo='label+percent',
                textfont=dict(size=11, color='black', family='Arial'),
                insidetextorientation='horizontal',
                automargin=True,
                hovertemplate='<b>%{label}</b><br>인원: %{value:,}명<br>비중: %{percent}<extra></extra>',
            ))
            fig_pie.update_layout(
                height=200, margin=dict(t=30, b=30, l=30, r=30),
                showlegend=False,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_prof:
            st.caption("**군집별 특성 프로파일**")
            cluster_order_prof = [' C0 (맛보기형)', ' C1 (헤비유저형)', ' C2 (후반몰입형)', ' C3 (휴면형)']
            for row_idx in range(2):
                card_cols = st.columns(2)
                for col_idx in range(2):
                    cname = cluster_order_prof[row_idx * 2 + col_idx]
                    color = CLUSTER_BORDER_M[cname]
                    with card_cols[col_idx]:
                        st.markdown(
                            f"""<div class="cluster-card" style="border-top: 4px solid {color}; margin-bottom:8px;">
                            <div style="margin-bottom:6px;">
                              <div class="cluster-title" style="font-size:13px; margin:0;">{cname.strip().split('(')[-1].rstrip(')')}</div>
                            </div>
                            <span style="font-size:11px; color:#888; display:block; margin-bottom:4px;">{CLUSTER_NUM_M[cname]}</span>
                            <span style="font-size:13px; color:#333; font-weight:500;">{CLUSTER_TXT_M[cname]}</span>
                            </div>""",
                            unsafe_allow_html=True
                        )

        # ── 시청 행동 패턴 데이터 준비 ─────────────────────────────────────
        _t1b_wt_cols       = ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']
        _t1b_cluster_order = [' C0 (맛보기형)', ' C1 (헤비유저형)', ' C2 (후반몰입형)', ' C3 (휴면형)']
        _t1b_cl_colors     = ['#FFB347', '#FF8FA3', '#81C784', '#64B5F6']

        _t1b_trend_rows = []
        for cn in _t1b_cluster_order:
            _row_t = promo_df[promo_df['cluster_name'] == cn][_t1b_wt_cols].mean()
            _vals  = [round(_row_t[c], 1) for c in _t1b_wt_cols]
            _short = cn.strip().split('(')[-1].rstrip(')')
            for _w, _v in zip(['1주차', '2주차', '3주차'], _vals):
                _t1b_trend_rows.append({'군집': _short, '주차': _w, '시청시간(분)': _v})
        _t1b_trend_df = pd.DataFrame(_t1b_trend_rows)

        _t1b_beh_rows = []
        for cn in _t1b_cluster_order:
            _sub   = promo_df[promo_df['cluster_name'] == cn]
            _short = cn.strip().split('(')[-1].rstrip(')')
            _t1b_beh_rows.append({
                '군집':              _short,
                '활성 비율(%)':      round(_sub['active_ratio'].mean() * 100, 1),
                '단타 시청(%)(5분↓)': round(_sub['watch_ratio_under_5m'].mean() * 100, 1),
                '장르 다양성(개)':    round(_sub['genre_diversity_count'].mean(), 1),
            })
        _t1b_beh_df  = pd.DataFrame(_t1b_beh_rows)
        _t1b_pct_melt = _t1b_beh_df[['군집', '활성 비율(%)', '단타 시청(%)(5분↓)']].melt(
            id_vars='군집', var_name='지표', value_name='값')

        # 차트 생성
        fig_t1b_trend = px.line(_t1b_trend_df, x='주차', y='시청시간(분)', color='군집',
            markers=True, text='시청시간(분)', color_discrete_sequence=_t1b_cl_colors)
        fig_t1b_trend.update_traces(textposition='top center', textfont_size=10, line_width=2.5, marker_size=9)
        fig_t1b_trend.update_layout(height=300, margin=dict(t=10, b=5, l=0, r=120),
            plot_bgcolor='white', xaxis_title='',
            yaxis=dict(gridcolor='#f0f0f0', title='평균 시청 시간 (분)'),
            legend=dict(orientation='v', x=1.01, y=1, xanchor='left', yanchor='top',
                bgcolor='rgba(255,255,255,0.9)', bordercolor='#e0e0e0', borderwidth=1, font=dict(size=11)))

        fig_t1b_beh = px.bar(_t1b_pct_melt, x='군집', y='값', color='지표', barmode='group',
            color_discrete_sequence=['#4472C4', '#ED7D31'], text='값')
        fig_t1b_beh.update_traces(textposition='outside', textfont_size=10)
        fig_t1b_beh.update_layout(height=300, margin=dict(t=10, b=5, l=0, r=0),
            plot_bgcolor='white', yaxis_title='(%)', xaxis_title='',
            yaxis=dict(gridcolor='#f0f0f0', range=[0, _t1b_pct_melt['값'].max() * 1.35]),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0, font=dict(size=10)))

        fig_t1b_genre = px.bar(_t1b_beh_df, x='군집', y='장르 다양성(개)',
            color='군집', color_discrete_sequence=_t1b_cl_colors, text='장르 다양성(개)')
        fig_t1b_genre.update_traces(textposition='outside', textfont_size=11, showlegend=False)
        fig_t1b_genre.update_layout(height=300, margin=dict(t=10, b=5, l=0, r=0),
            plot_bgcolor='white', xaxis_title='', showlegend=False,
            yaxis=dict(gridcolor='#f0f0f0', title='평균 장르 수',
                range=[0, _t1b_beh_df['장르 다양성(개)'].max() * 1.4]))

        # ── expander: 시청 행동 패턴 UI ──────────────────────────────────
        with st.expander("시청 행동 패턴 상세 보기 (군집별 시청 추이)", expanded=False):
            st.caption("시청 데이터로 보는 이탈 신호")

            st.plotly_chart(fig_t1b_trend, use_container_width=True)

    # ── 탭2: 세부 인구통계 분석 ────────────────────────────────────────────
    with tab2:
        # ── 공통 사전 계산 ──────────────────────────────────────────────
        _wt_cols = ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']
        _t2_cluster_order = [' C0 (맛보기형)', ' C1 (헤비유저형)', ' C2 (후반몰입형)', ' C3 (휴면형)']
        _t2_cl_colors     = ['#FFB347', '#FF8FA3', '#81C784', '#64B5F6']
        _t2_short_color   = {'맛보기형':'#FFB347','헤비유저형':'#FF8FA3','후반몰입형':'#81C784','휴면형':'#64B5F6'}

        age_df = promo_df.groupby('age_group')['is_churn'].agg(['mean', 'count']).reset_index()
        age_df.columns = ['나이대', '이탈률', '인원']
        age_df['이탈률'] *= 100
        age_df['나이대_str'] = age_df['나이대'].astype(str) + '대'

        gen_df = promo_df[promo_df['gender_kor'].isin(['여성', '남성'])].groupby('gender_kor').agg(
            이탈률=('is_churn', 'mean'), 인원=('USER_KEY', 'count')
        ).reset_index()
        gen_df['이탈률'] *= 100
        gen_df.columns = ['성별', '이탈률', '인원']

        top_age       = age_df.loc[age_df['이탈률'].idxmax(), '나이대_str']
        top_age_rate  = age_df['이탈률'].max()
        gen_gap       = abs(gen_df['이탈률'].max() - gen_df['이탈률'].min())
        high_gen      = gen_df.loc[gen_df['이탈률'].idxmax(), '성별']
        _t2_top_plan  = plan_stats.loc[plan_stats['이탈률'].idxmax()]
        _cr_avg_t2    = CHURNED / TOTAL * 100

        # ── 핵심 인사이트 카드 (맨 위 — 결론 먼저, 전부 동적 계산) ────────
        _ins_cl_rows = []
        for _cn in _t2_cluster_order:
            _s = promo_df[promo_df['cluster_name'] == _cn]
            _sn = _cn.strip().split('(')[-1].rstrip(')')
            _ins_cl_rows.append({
                '군집':     _sn,
                '이탈률':   _s['is_churn'].mean() * 100,
                '총시청':   _s['total_watch_time(min)'].mean(),
                'only_w1':  _s['is_only_w1'].mean() * 100,
                'w3_잔존':  (_s['watch_time(min)_w3'] > 0).mean() * 100,
                'w3_증감':  _s['watch_time(min)_w3'].mean() - _s['watch_time(min)_w1'].mean(),
            })
        _ins_cl_df   = pd.DataFrame(_ins_cl_rows)
        _ins_c2 = _ins_cl_df.loc[_ins_cl_df['이탈률'].idxmax()]   # 이탈률 최고 군집
        _ins_c3 = _ins_cl_df.loc[_ins_cl_df['이탈률'].idxmin()]   # 이탈률 최저 군집
        _ins_c4 = _ins_cl_df.loc[_ins_cl_df['w3_증감'].idxmax()]  # 3주차 성장 최고 군집

        _ins_data = [
            (
                "이탈 집중 구간",
                f"{top_age} · {high_gen} · {_t2_top_plan['plan']}",
                f"세 세그먼트 모두 전체 평균 {_cr_avg_t2:.1f}% 상회 — 우선 대응 필요",
            ),
            (
                f"{_ins_c2['군집']} — 이탈 고위험",
                f"이탈률 {_ins_c2['이탈률']:.1f}% · 1주차만 시청 {_ins_c2['only_w1']:.0f}%",
                "1주차 종료 즉시 재참여 쿠폰 + 맞춤 알림 발송",
            ),
            (
                f"{_ins_c3['군집']} — 핵심 유지 자산",
                f"이탈률 {_ins_c3['이탈률']:.1f}% · 평균 총 시청 {_ins_c3['총시청']:.0f}분",
                "충성 고객 록인 — 후속 콘텐츠 큐레이션 · VIP 혜택 제안",
            ),
            (
                f"{_ins_c4['군집']} — 전환 기회",
                f"3주차 잔존 {_ins_c4['w3_잔존']:.0f}% · w3 시청 변화 {_ins_c4['w3_증감']:+.0f}분",
                "4주차 유료 전환 유도 메시지 집중 발송",
            ),
        ]
        st.markdown('<div style="font-size:14px; font-weight:700; color:#333; margin-bottom:8px;">핵심 인사이트 &amp; 마케팅 액션 포인트</div>', unsafe_allow_html=True)
        _ins_cols = st.columns(4)
        for _col, (_title, _val, _desc) in zip(_ins_cols, _ins_data):
            _col.markdown(f"""<div style="border-radius:8px; padding:12px; background:#fafafa;
                border:1px solid #e0e0e0; border-top:3px solid #FF7A00;">
              <div style="font-size:11px; font-weight:700; color:#FF7A00; margin-bottom:4px;">{_title}</div>
              <div style="font-size:12px; font-weight:600; color:#333; margin-bottom:4px;">{_val}</div>
              <div style="font-size:11px; color:#888; line-height:1.5;">{_desc}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<hr style='margin:14px 0;'>", unsafe_allow_html=True)

        # ─────────────────────────────────────────────────────────────
        # 이탈 vs 유지 고객 차이 시각화
        # ─────────────────────────────────────────────────────────────
        st.markdown("""<div style="background:linear-gradient(90deg,#f5f0ff,#fff);
            border-left:4px solid #7B1FA2; padding:10px 16px;
            border-radius:0 8px 8px 0; margin-bottom:12px;">
          <span style="font-size:16px; font-weight:700; color:#333;">이탈 vs 유지 고객 비교</span>
          &nbsp;<span style="font-size:12px; color:#888;">실제 이탈/유지 고객의 행동 차이 심층 분석</span>
        </div>""", unsafe_allow_html=True)

        _cv_churn  = promo_df[promo_df['is_churn'] == 1]
        _cv_retain = promo_df[promo_df['is_churn'] == 0]
        _cv_wt_diff  = _cv_retain['total_watch_time(min)'].mean() - _cv_churn['total_watch_time(min)'].mean()
        _cv_act_diff = (_cv_retain['active_ratio'].mean() - _cv_churn['active_ratio'].mean()) * 100

        cvk1, cvk2, cvk3, cvk4 = st.columns(4)
        cvk1.metric("이탈 고객 수",      f"{len(_cv_churn):,}명",
                    f"이탈률 {len(_cv_churn)/len(promo_df)*100:.1f}%", delta_color="inverse")
        cvk2.metric("유지 고객 수",      f"{len(_cv_retain):,}명",
                    f"잔존률 {len(_cv_retain)/len(promo_df)*100:.1f}%")
        cvk3.metric("총 시청 시간 차이", f"{_cv_wt_diff:.0f}분",
                    "유지가 이탈보다 더 시청")
        cvk4.metric("활성비율 차이",     f"{_cv_act_diff:.1f}%p",
                    "유지가 이탈보다 활성 비율 높음")

        st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

        cv_r2a, cv_r2b = st.columns(2)

        with cv_r2a:
            st.caption("**이탈 vs 유지: 주차별 평균 시청 시간 (분)**")
            _cv_wt_cols   = ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']
            _cv_wt_labels = ['1주차', '2주차', '3주차']
            _cv_wt_rows   = []
            for _g, _df in [('이탈', _cv_churn), ('유지', _cv_retain)]:
                for _w, _c in zip(_cv_wt_labels, _cv_wt_cols):
                    _cv_wt_rows.append({'구분': _g, '주차': _w, '평균 시청(분)': round(_df[_c].mean(), 1)})
            _cv_wt_df = pd.DataFrame(_cv_wt_rows)
            fig_cv_wt = px.bar(_cv_wt_df, x='주차', y='평균 시청(분)', color='구분', barmode='group',
                color_discrete_map={'이탈': '#C05555', '유지': '#52A068'},
                text='평균 시청(분)')
            fig_cv_wt.update_traces(textposition='outside', textfont_size=11)
            fig_cv_wt.update_layout(height=290, margin=dict(t=10, b=5, l=0, r=0),
                plot_bgcolor='white', xaxis_title='', yaxis_title='평균 시청 (분)',
                yaxis=dict(gridcolor='#f0f0f0'),
                legend=dict(orientation='h', y=1.08, x=0, font=dict(size=11)))
            st.plotly_chart(fig_cv_wt, use_container_width=True)

        with cv_r2b:
            st.caption("**이탈 vs 유지: 행동 지표 비교**")
            _cv_beh_rows = []
            for _g, _df in [('이탈', _cv_churn), ('유지', _cv_retain)]:
                _cv_beh_rows.append({
                    '구분':              _g,
                    '활성 비율(%)':      round(_df['active_ratio'].mean() * 100, 1),
                    '단타 시청(%)(5분↓)': round(_df['watch_ratio_under_5m'].mean() * 100, 1),
                    '장르 다양성(개)':    round(_df['genre_diversity_count'].mean(), 1),
                })
            _cv_beh_df   = pd.DataFrame(_cv_beh_rows)
            _cv_beh_melt = _cv_beh_df.melt(id_vars='구분', var_name='지표', value_name='값')
            fig_cv_beh = px.bar(_cv_beh_melt, x='지표', y='값', color='구분', barmode='group',
                color_discrete_map={'이탈': '#C05555', '유지': '#52A068'},
                text='값')
            fig_cv_beh.update_traces(textposition='outside', textfont_size=11)
            fig_cv_beh.update_layout(height=290, margin=dict(t=10, b=5, l=0, r=0),
                plot_bgcolor='white', xaxis_title='', yaxis_title='값',
                yaxis=dict(gridcolor='#f0f0f0'),
                legend=dict(orientation='h', y=1.08, x=0, font=dict(size=11)))
            st.plotly_chart(fig_cv_beh, use_container_width=True)

        st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

        # ── Row 2: 이탈 신호 플래그 & 장르 취향 차이 ──────────────────────
        cv_r3a, cv_r3b = st.columns(2)

        with cv_r3a:
            st.caption("**이탈 신호 플래그 비율 (%)**")
            _cv_flag_info = [
                ('is_only_w1',       '1주차만 시청'),
                ('is_w1_over_50pct', 'W1 시청 50%+'),
                ('is_cold_start_3d', '3일 콜드스타트'),
                ('is_only_w2',       '2주차만 시청'),
            ]
            _cv_flag_rows = []
            for _col, _lbl in _cv_flag_info:
                _cv_flag_rows.append({
                    '지표': _lbl,
                    '이탈': round(_cv_churn[_col].mean() * 100, 1),
                    '유지': round(_cv_retain[_col].mean() * 100, 1),
                })
            _cv_flag_melt = pd.DataFrame(_cv_flag_rows).melt(id_vars='지표', var_name='구분', value_name='비율(%)')
            fig_cv_flag = px.bar(_cv_flag_melt, x='지표', y='비율(%)', color='구분', barmode='group',
                color_discrete_map={'이탈': '#C05555', '유지': '#52A068'}, text='비율(%)')
            fig_cv_flag.update_traces(textposition='outside', textfont_size=10)
            fig_cv_flag.update_layout(height=290, margin=dict(t=10, b=5, l=0, r=0),
                plot_bgcolor='white', xaxis_title='', yaxis_title='비율 (%)',
                yaxis=dict(gridcolor='#f0f0f0'),
                legend=dict(orientation='h', y=1.08, x=0, font=dict(size=11)))
            st.plotly_chart(fig_cv_flag, use_container_width=True)

        with cv_r3b:
            st.caption("**장르 취향 차이 (이탈 − 유지, %p) · 빨강=이탈 더 많이 시청**")
            _cv_genre_info = [
                ('thriller_crime_ratio',   '스릴러/범죄'),
                ('action_adventure_ratio', '액션/어드벤처'),
                ('horror_ratio',           '호러'),
                ('drama_ratio',            '드라마'),
                ('romance_ratio',          '로맨스'),
                ('family_animation_ratio', '가족/애니'),
                ('comedy_ratio',           '코미디'),
                ('documentary_ratio',      '다큐멘터리'),
            ]
            _cv_gdiff_rows = []
            for _col, _lbl in _cv_genre_info:
                _diff = round((_cv_churn[_col].mean() - _cv_retain[_col].mean()) * 100, 2)
                _cv_gdiff_rows.append({'장르': _lbl, '차이': _diff, '색': '#C05555' if _diff > 0 else '#52A068'})
            _cv_gdiff_df = pd.DataFrame(_cv_gdiff_rows).sort_values('차이')
            fig_cv_genre = go.Figure(go.Bar(
                x=_cv_gdiff_df['차이'], y=_cv_gdiff_df['장르'],
                orientation='h',
                marker_color=_cv_gdiff_df['색'].tolist(),
                text=[f'{v:+.1f}%p' for v in _cv_gdiff_df['차이']],
                textposition='outside',
            ))
            fig_cv_genre.add_vline(x=0, line_dash='dash', line_color='#888', line_width=1)
            fig_cv_genre.update_layout(height=290, margin=dict(t=10, b=5, l=80, r=60),
                plot_bgcolor='white',
                xaxis=dict(title='차이 (이탈 − 유지, %p)', gridcolor='#f0f0f0'),
                yaxis=dict(title=''))
            st.plotly_chart(fig_cv_genre, use_container_width=True)

        st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

        # ── Row 3: 주차별 증감 & 핵심 지표 비교표 ────────────────────────
        cv_r4a, cv_r4b = st.columns(2)

        with cv_r4a:
            st.caption("**주차 간 시청 증감 비교 (분) · 이탈 고객은 갈수록 급감**")
            _cv_wdiff_info = [
                ('diff_between_w2_w1', 'W2 − W1'),
                ('diff_between_w3_w1', 'W3 − W1'),
                ('diff_between_w3_w2', 'W3 − W2'),
            ]
            _cv_wdiff_rows = []
            for _col, _lbl in _cv_wdiff_info:
                _cv_wdiff_rows.append({
                    '구간': _lbl,
                    '이탈': round(_cv_churn[_col].mean(), 1),
                    '유지': round(_cv_retain[_col].mean(), 1),
                })
            _cv_wdiff_melt = pd.DataFrame(_cv_wdiff_rows).melt(id_vars='구간', var_name='구분', value_name='증감(분)')
            _wdiff_abs_max = _cv_wdiff_melt['증감(분)'].abs().max()
            fig_cv_wdiff = px.bar(_cv_wdiff_melt, x='구간', y='증감(분)', color='구분', barmode='group',
                color_discrete_map={'이탈': '#C05555', '유지': '#52A068'}, text='증감(분)')
            fig_cv_wdiff.update_traces(textposition='outside', textfont_size=10)
            fig_cv_wdiff.add_hline(y=0, line_color='#333', line_width=1.2)
            fig_cv_wdiff.update_layout(height=290, margin=dict(t=10, b=5, l=0, r=0),
                plot_bgcolor='white', xaxis_title='', yaxis_title='평균 증감 (분)',
                yaxis=dict(gridcolor='#f0f0f0', range=[-_wdiff_abs_max * 1.4, _wdiff_abs_max * 1.4]),
                legend=dict(orientation='h', y=1.08, x=0, font=dict(size=11)))
            st.plotly_chart(fig_cv_wdiff, use_container_width=True)

        with cv_r4b:
            st.caption("**핵심 지표 이탈 vs 유지 비교**")
            _cv_kpi_rows = [
                ("마지막 시청 후 경과일",
                 f"{_cv_churn['recency'].mean():.1f}일",
                 f"{_cv_retain['recency'].mean():.1f}일", "이탈↑"),
                ("5분 미만 단타 시청 비율",
                 f"{_cv_churn['watch_ratio_under_5m'].mean()*100:.1f}%",
                 f"{_cv_retain['watch_ratio_under_5m'].mean()*100:.1f}%", "이탈↑"),
                ("최다 시청일 집중도",
                 f"{_cv_churn['max_day_share'].mean()*100:.1f}%",
                 f"{_cv_retain['max_day_share'].mean()*100:.1f}%", "이탈↑"),
                ("3회+ 시청일 수",
                 f"{_cv_churn['day_count_over_3times'].mean():.2f}일",
                 f"{_cv_retain['day_count_over_3times'].mean():.2f}일", "유지↑"),
                ("시청 고유 영화 수",
                 f"{_cv_churn['unique_movie'].mean():.1f}편",
                 f"{_cv_retain['unique_movie'].mean():.1f}편", "유지↑"),
                ("장르 다양성",
                 f"{_cv_churn['genre_diversity_count'].mean():.1f}개",
                 f"{_cv_retain['genre_diversity_count'].mean():.1f}개", "유지↑"),
            ]
            _kpi_html = """<table style="width:100%;border-collapse:collapse;font-size:12px;margin-top:4px;">
              <thead><tr style="background:#f8f8f8;">
                <th style="text-align:left;padding:7px 8px;border-bottom:2px solid #ddd;">지표</th>
                <th style="text-align:center;padding:7px 8px;border-bottom:2px solid #ddd;color:#C05555;">이탈</th>
                <th style="text-align:center;padding:7px 8px;border-bottom:2px solid #ddd;color:#52A068;">유지</th>
                <th style="text-align:center;padding:7px 8px;border-bottom:2px solid #ddd;">방향</th>
              </tr></thead><tbody>"""
            for _nm, _cv_v, _rv_v, _dir in _cv_kpi_rows:
                _ds = "color:#C05555;" if "이탈" in _dir else "color:#52A068;"
                _kpi_html += f"""<tr style="border-bottom:1px solid #eee;">
                  <td style="padding:7px 8px;">{_nm}</td>
                  <td style="text-align:center;padding:7px 8px;font-weight:600;color:#C05555;">{_cv_v}</td>
                  <td style="text-align:center;padding:7px 8px;font-weight:600;color:#52A068;">{_rv_v}</td>
                  <td style="text-align:center;padding:7px 8px;font-weight:700;{_ds}">{_dir}</td>
                </tr>"""
            _kpi_html += "</tbody></table>"
            st.markdown(_kpi_html, unsafe_allow_html=True)

        st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

        # ── Row 4: 주차별 시청 패턴 LINE & 시청 습관 지표 ─────────────────
        cv_r5a, cv_r5b = st.columns(2)

        with cv_r5a:
            st.caption("**주차별 시청 패턴 추이 — 이탈 고객은 W2·W3로 갈수록 급감**")
            _cv_lw_cols = ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']
            _cv_line_rows = []
            for _g, _dfl in [('이탈', _cv_churn), ('유지', _cv_retain)]:
                for _w, _c in zip(['1주차', '2주차', '3주차'], _cv_lw_cols):
                    _cv_line_rows.append({'구분': _g, '주차': _w, '평균 시청(분)': round(_dfl[_c].mean(), 1)})
            _cv_line_df = pd.DataFrame(_cv_line_rows)
            fig_cv_line = px.line(_cv_line_df, x='주차', y='평균 시청(분)', color='구분',
                markers=True, text='평균 시청(분)',
                color_discrete_map={'이탈': '#C05555', '유지': '#52A068'})
            fig_cv_line.update_traces(textposition='top center', textfont_size=11, line_width=2.5, marker_size=9)
            _cv_line_ymax = _cv_line_df['평균 시청(분)'].max()
            fig_cv_line.update_layout(height=290, margin=dict(t=20, b=5, l=0, r=0),
                plot_bgcolor='white', xaxis_title='',
                yaxis=dict(gridcolor='#f0f0f0', title='평균 시청 시간 (분)',
                           range=[0, _cv_line_ymax * 1.3]),
                legend=dict(orientation='h', y=1.08, x=0, font=dict(size=11)))
            st.plotly_chart(fig_cv_line, use_container_width=True)

        with cv_r5b:
            st.caption("**시청 습관 지표 비교 (%) — 이탈 고객은 단타·집중형 시청 패턴**")
            _cv_habit_info = [
                ('active_ratio',         '활성화\n비율'),
                ('watch_ratio_under_1m', '1분 미만\n시청'),
                ('watch_ratio_under_5m', '5분 미만\n시청'),
                ('avg_rewatch_ratio',    '재시청\n비율'),
                ('weekend_watch_ratio',  '주말 시청\n비율'),
                ('max_day_share',        '최다 시청일\n집중도'),
            ]
            _cv_habit_rows = []
            for _col, _lbl in _cv_habit_info:
                _cv_habit_rows.append({
                    '지표': _lbl,
                    '이탈': round(_cv_churn[_col].mean() * 100, 1),
                    '유지': round(_cv_retain[_col].mean() * 100, 1),
                })
            _cv_habit_melt = pd.DataFrame(_cv_habit_rows).melt(id_vars='지표', var_name='구분', value_name='값(%)')
            fig_cv_habit = px.bar(_cv_habit_melt, x='지표', y='값(%)', color='구분', barmode='group',
                color_discrete_map={'이탈': '#C05555', '유지': '#52A068'}, text='값(%)')
            fig_cv_habit.update_traces(textposition='outside', textfont_size=10)
            _cv_habit_ymax = _cv_habit_melt['값(%)'].max()
            fig_cv_habit.update_layout(height=290, margin=dict(t=10, b=5, l=0, r=0),
                plot_bgcolor='white', xaxis_title='', yaxis_title='비율 (%)',
                yaxis=dict(gridcolor='#f0f0f0', range=[0, _cv_habit_ymax * 1.35]),
                legend=dict(orientation='h', y=1.08, x=0, font=dict(size=11)))
            st.plotly_chart(fig_cv_habit, use_container_width=True)

        st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

        # ── Row 5: 군집별 행동 지표 ─────────────────────────────────────
        st.markdown("""<div style="display:flex; align-items:center; margin:4px 0 12px 0; gap:12px;">
          <span style="font-size:13px; font-weight:600; color:#4472C4; white-space:nowrap;">이탈 vs 잔존 — 장르 다양성</span>
          <div style="flex:1; height:1px; background:#e0e0e0;"></div>
        </div>""", unsafe_allow_html=True)

        cv_r6b, _ = st.columns(2)

        with cv_r6b:
            st.caption("**장르 다양성 (개)**")
            _cv_genre_div = pd.DataFrame({
                '구분': ['이탈', '잔존'],
                '장르 다양성(개)': [
                    round(_cv_churn['genre_diversity_count'].mean(), 1),
                    round(_cv_retain['genre_diversity_count'].mean(), 1),
                ],
            })
            fig_cv_gdiv = px.bar(_cv_genre_div, x='구분', y='장르 다양성(개)',
                color='구분', color_discrete_map={'이탈': '#C05555', '잔존': '#52A068'},
                text='장르 다양성(개)')
            fig_cv_gdiv.update_traces(textposition='outside', textfont_size=12,
                texttemplate='%{text}개')
            _gdiv_max = _cv_genre_div['장르 다양성(개)'].max()
            fig_cv_gdiv.update_layout(height=280, margin=dict(t=10, b=5, l=0, r=0),
                plot_bgcolor='white', xaxis_title='', yaxis_title='평균 장르 수 (개)',
                yaxis=dict(gridcolor='#f0f0f0', range=[0, _gdiv_max * 1.35]),
                showlegend=False)
            st.plotly_chart(fig_cv_gdiv, use_container_width=True)


# ==========================================
# 이탈 방어 전략
# ==========================================
elif menu == "🛡️ 이탈 방어 전략":

    head_col1, head_col2, head_col3 = st.columns([5, 2.5, 2.5])
    with head_col1:
        st.header("🛡️ 이탈 방어 전략")
        st.caption("목적: 4주차 유료 전환 고위험군 조기 식별 및 맞춤 액션 실행")
    with head_col2:
        st.date_input("📅 분석 대상 가입일",
                      value=(datetime.date(2021, 3, 1), datetime.date(2021, 3, 15)))
    with head_col3:
        st.date_input("🗓️ 타겟팅 기준일", value=datetime.date(2021, 4, 1))

    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex; gap:10px; margin: 6px 0 16px 0;">
      <div style="flex:1; background:#e3f2fd; border-radius:8px; padding:12px 14px; border-left:3px solid #1565c0;">
        <div style="font-size:11px; font-weight:700; color:#0d47a1; margin-bottom:4px;">📌 이 페이지에서 알 수 있는 것 ①</div>
        <div style="font-size:13px; color:#333; line-height:1.5;">이탈 위험 점수와 세그먼트로 필터링한 <b>즉시 대응 가능한 고위험 고객 리스트</b>를 확인합니다.</div>
      </div>
      <div style="flex:1; background:#fff8e1; border-radius:8px; padding:12px 14px; border-left:3px solid #f9a825;">
        <div style="font-size:11px; font-weight:700; color:#e65100; margin-bottom:4px;">📌 이 페이지에서 알 수 있는 것 ②</div>
        <div style="font-size:13px; color:#333; line-height:1.5;">Local XAI 심층 분석으로 <b>특정 고객이 왜 이탈 위험인지</b> 군집 평균과 비교해 파악합니다.</div>
      </div>
      <div style="flex:1; background:#e8f5e9; border-radius:8px; padding:12px 14px; border-left:3px solid #388e3c;">
        <div style="font-size:11px; font-weight:700; color:#1b5e20; margin-bottom:4px;">📌 이 페이지에서 알 수 있는 것 ③</div>
        <div style="font-size:13px; color:#333; line-height:1.5;">세그먼트별 예상 LTV와 예산 배분 가이드로 <b>방어 성공 시 기대 매출</b>을 추정합니다.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("100원 프로모션 가입자",   f"{TOTAL:,} 명",  "전체의 51.2%", delta_color="off")
    kpi2.metric("유료 전환율",          f"{CONVERTED/TOTAL*100:.1f} %", f"{CONVERTED:,}명 재구매 완료")
    kpi3.metric("이탈 고위험군",        "4,463 명",        "즉시 대응 필요 (37.3%)", delta_color="inverse")
    kpi4.metric("방어 성공 시 기대 매출", "약 1.4억 원",    "추정 LTV 기준")

    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    header_col, filter_col1, filter_col2 = st.columns([4, 3, 3])
    with header_col:
        st.markdown("<h3 style='margin-top: 15px;'>📋 고위험군 타겟 리스트</h3>", unsafe_allow_html=True)
    with filter_col1:
        prob_range = st.slider("이탈 위험 점수 필터 (%)", 0.0, 100.0, (70.0, 100.0))
    with filter_col2:
        watch_range = st.slider("1주차 시청 시간 필터 (분)", 0, 1500, (0, 1500))

    st.markdown("<div style='font-size: 14px; font-weight: 600; margin-bottom: 5px;'>세그먼트 필터</div>",
                unsafe_allow_html=True)
    seg_cols = st.columns(4)
    segments_list   = [' C1 (헤비유저형)', ' C0 (맛보기형)', ' C3 (휴면형)', ' C2 (후반몰입형)']
    default_checked = [' C1 (헤비유저형)', ' C0 (맛보기형)', ' C3 (휴면형)']
    selected_segs = []
    for i, seg in enumerate(segments_list):
        with seg_cols[i]:
            if st.checkbox(seg.strip(), value=(seg in default_checked)):
                selected_segs.append(seg)

    filtered_raw = promo_df[
        (promo_df['cluster_name'].isin(selected_segs)) &
        (promo_df['churn_score'] >= prob_range[0]) &
        (promo_df['churn_score'] <= prob_range[1]) &
        (promo_df['watch_time(min)_w1'] >= watch_range[0]) &
        (promo_df['watch_time(min)_w1'] <= watch_range[1])
    ].sort_values('churn_score', ascending=False).head(50)

    fmt_min = lambda x: f"{int(x)}분"
    PATTERN_MAP = {
        ' C1 (헤비유저형)': '1주차 폭식 후 급감',
        ' C0 (맛보기형)':   '콘텐츠 탐색만 하다 이탈',
        ' C3 (휴면형)':     '가입 후 미접속',
        ' C2 (후반몰입형)': '유료 전환 트리거 부재',
    }
    ACTION_MAP = {
        ' C1 (헤비유저형)': '후속 콘텐츠 알림',
        ' C0 (맛보기형)':   '취향 매칭 큐레이션',
        ' C3 (휴면형)':     '재참여 쿠폰',
        ' C2 (후반몰입형)': 'VIP 혜택 안내',
    }

    display_df = pd.DataFrame({
        '고객 ID':       filtered_raw['USER_KEY'].str[:10].values,
        '성별':          filtered_raw['gender_kor'].values,
        '나이대':        filtered_raw['age_group'].astype(int).astype(object).apply(lambda x: f"{x}대").values,
        '이탈 위험 점수(%)': filtered_raw['churn_score'].round(1).values,
        '소속 세그먼트':  filtered_raw['cluster_name'].str.strip().values,
        '1주차 시청':    filtered_raw['watch_time(min)_w1'].apply(fmt_min).values,
        '2주차 시청':    filtered_raw['watch_time(min)_w2'].apply(fmt_min).values,
        '3주차 시청':    filtered_raw['watch_time(min)_w3'].apply(fmt_min).values,
        '위험 패턴':     filtered_raw['cluster_name'].map(PATTERN_MAP).values,
        '대응 액션':     filtered_raw['cluster_name'].map(ACTION_MAP).values,
    })
    st.dataframe(display_df.set_index('고객 ID').astype(object), use_container_width=True, height=280)

    st.markdown("<br>", unsafe_allow_html=True)
    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1:
        if st.button("🚨 C1 헤비유저 타겟 푸시", use_container_width=True): st.success("푸시 발송 완료!")
    with ac2:
        if st.button("📧 C0 맞춤 추천 메일",      use_container_width=True): st.success("메일 발송 완료!")
    with ac3:
        if st.button("🎫 C3 재참여 쿠폰 발송",    use_container_width=True): st.success("쿠폰 발송 완료!")
    with ac4:
        if st.button("💎 C2 VIP 혜택 제안",       use_container_width=True): st.success("혜택 발송 완료!")

    st.markdown("<br><hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    GENRE_COLS = {
        '액션/어드벤처': 'action_adventure_ratio',
        '드라마':        'drama_ratio',
        '코미디':        'comedy_ratio',
        'SF/판타지':     'sf_fantasy_ratio',
        '스릴러/범죄':   'thriller_crime_ratio',
        '로맨스':        'romance_ratio',
        '공포':          'horror_ratio',
        '다큐':          'documentary_ratio',
        '애니/가족':     'family_animation_ratio',
        '역사/전쟁':     'historical_war_ratio',
    }
    FEAT_COLS = {
        '3주차 시청(분)':  'watch_time(min)_w3',
        '3주차 리텐션':    'retention_w3_ratio',
        '활동 비율':       'active_ratio',
        '장르 다양성':     'genre_diversity_count',
        '재시청 비율':     'avg_rewatch_ratio',
        '1주차 시청(분)':  'watch_time(min)_w1',
    }

    with st.expander("🕵️ 특정 고객 이탈 원인 심층 분석 (Local XAI) 열기"):
        user_options = display_df['고객 ID'].tolist() if not display_df.empty else ["선택 불가"]
        target_uid   = st.selectbox("분석할 고객 ID 선택", user_options)

        if not display_df.empty and target_uid != "선택 불가":
            raw_row   = filtered_raw[filtered_raw['USER_KEY'].str[:10] == target_uid].iloc[0]
            segment   = raw_row['cluster_name']
            cluster_sub = promo_df[promo_df['cluster_name'] == segment]

            main_left, main_right = st.columns([3, 4])
            with main_left:
                st.caption("**주차별 시청 시간 추이 (유저 vs 군집 평균)**")
                weeks   = ['1주차', '2주차', '3주차']
                wt_user = [float(raw_row['watch_time(min)_w1']),
                           float(raw_row['watch_time(min)_w2']),
                           float(raw_row['watch_time(min)_w3'])]
                wt_avg  = [float(cluster_sub['watch_time(min)_w1'].mean()),
                           float(cluster_sub['watch_time(min)_w2'].mean()),
                           float(cluster_sub['watch_time(min)_w3'].mean())]
                fig_wt = go.Figure()
                fig_wt.add_trace(go.Scatter(
                    x=weeks, y=wt_user, mode='lines+markers',
                    name='선택 유저', line=dict(color='#EA002C', width=2), marker=dict(size=7)
                ))
                fig_wt.add_trace(go.Scatter(
                    x=weeks, y=wt_avg, mode='lines+markers',
                    name='군집 평균', line=dict(color='#9e9e9e', width=2, dash='dash'),
                    marker=dict(size=7)
                ))
                fig_wt.update_layout(
                    height=160,
                    margin=dict(t=30, b=10, l=40, r=10),
                    yaxis=dict(title='분', title_font=dict(size=10)),
                    legend=dict(orientation='h', y=1.12, font=dict(size=9)),
                    hovermode='x unified'
                )
                st.plotly_chart(fig_wt, use_container_width=True)

            with main_right:
                st.caption("**유저 지표 vs 군집 평균 (편차 비율)**")
                feat_names, deviations, bar_colors = [], [], []
                for label, col in FEAT_COLS.items():
                    u_val  = float(raw_row.get(col, 0))
                    c_mean = float(cluster_sub[col].mean())
                    dev    = (u_val - c_mean) / (c_mean + 1e-9) if c_mean != 0 else 0.0
                    feat_names.append(label)
                    deviations.append(round(dev, 3))
                    bar_colors.append('#EA002C' if dev < 0 else '#388e3c')

                if 'C1' in segment:
                    desc = "1주차 폭식 시청 후 급격한 접속 감소 패턴"
                elif 'C0' in segment:
                    desc = "콘텐츠 탐색 중심, 실제 시청으로 전환 실패"
                elif 'C3' in segment:
                    desc = "가입 후 사실상 콘텐츠 미소비 상태"
                else:
                    desc = "안정적 시청이나 유료 전환 트리거 부재"

                st.info(f"🤖 **AI 요약:** {desc}")
                fig_xai = go.Figure(go.Bar(
                    x=deviations, y=feat_names,
                    orientation='h', marker_color=bar_colors,
                    text=[f"{v:+.1%}" for v in deviations],
                    textposition='outside'
                ))
                fig_xai.add_vline(x=0, line_color='#aaa', line_width=1)
                fig_xai.update_layout(
                    height=300,
                    margin=dict(t=5, b=5, l=0, r=65),
                    yaxis=dict(autorange="reversed"),
                    xaxis=dict(tickformat='.0%')
                )
                st.plotly_chart(fig_xai, use_container_width=True)
                st.caption("🟢 군집 평균 이상 &nbsp;&nbsp; 🔴 군집 평균 미달")

    with st.expander("💰 세그먼트별 예상 LTV 및 마케팅 예산 할당 가이드 열기"):
        ltv_col1, ltv_col2 = st.columns([5, 5])
        with ltv_col1:
            df_ltv = pd.DataFrame({
                '세그먼트': [' C2 (후반몰입형)', ' C1 (헤비유저형)', ' C0 (맛보기형)', ' C3 (휴면형)'],
                '예상 LTV': [150000, 95000, 28000, 12000]
            })
            fig_ltv = px.bar(df_ltv, x='예상 LTV', y='세그먼트', orientation='h',
                             text='예상 LTV', color='세그먼트', color_discrete_map=COLOR_MAP)
            fig_ltv.update_traces(texttemplate='%{text:,}원', textposition='outside')
            fig_ltv.update_layout(height=200, margin=dict(t=0, b=0, l=0, r=0),
                                  showlegend=False, xaxis=dict(range=[0, 180000]))
            st.plotly_chart(fig_ltv, use_container_width=True)
        with ltv_col2:
            st.info("**💡 예산 운영 가이드**\n\n"
                    "- **C2 (후반몰입형)**: 유료 전환 가장 높음 → 적극적 VIP 혜택 투입 권장.\n"
                    "- **C1 (헤비유저형)**: 고시청 후 이탈 → 시리즈 큐레이션 알림.\n"
                    "- **C0/C3**: 이탈 위험 최고 → 저비용 알림 + 쿠폰 중심 방어.")

# ==========================================
# 프로모션 행동 분석
# ==========================================
elif menu == "👥 프로모션 행동 분석":
    st.header("👥 프로모션 행동 분석 현황")
    st.markdown("---")

    n_only_w1  = int((promo_df['is_only_w1'] == 1).sum())
    n_no_w3    = int(((promo_df['watch_time(min)_w3'] == 0) & (promo_df['is_only_w1'] != 1)).sum())
    n_low_ret  = int(((promo_df['retention_w3_ratio'].fillna(0) < 0.5) &
                       (promo_df['watch_time(min)_w3'] > 0)).sum())
    n_stable   = TOTAL - n_only_w1 - n_no_w3 - n_low_ret

    st.markdown("### 🚨 이탈 위험도별 고객 분포")
    card1, card2, card3, card4 = st.columns(4)
    with card1:
        st.markdown(f"""<div class="risk-card border-very-high">
            <div class="card-title">매우 높음 — 1주차만 시청</div>
            <div class="card-value" style="color:#EA002C;">{n_only_w1:,}<span class="card-unit">명</span></div>
            <div class="card-percent">(전체의 {n_only_w1/TOTAL*100:.1f}%)</div></div>""",
            unsafe_allow_html=True)
    with card2:
        st.markdown(f"""<div class="risk-card border-high">
            <div class="card-title">높음 — 3주차 미시청</div>
            <div class="card-value" style="color:#FF7A00;">{n_no_w3:,}<span class="card-unit">명</span></div>
            <div class="card-percent">(전체의 {n_no_w3/TOTAL*100:.1f}%)</div></div>""",
            unsafe_allow_html=True)
    with card3:
        st.markdown(f"""<div class="risk-card border-medium">
            <div class="card-title">보통 — 3주차 시청 감소</div>
            <div class="card-value" style="color:#fbc02d;">{n_low_ret:,}<span class="card-unit">명</span></div>
            <div class="card-percent">(전체의 {n_low_ret/TOTAL*100:.1f}%)</div></div>""",
            unsafe_allow_html=True)
    with card4:
        st.markdown(f"""<div class="risk-card border-low">
            <div class="card-title">낮음 — 지속 시청</div>
            <div class="card-value" style="color:#388e3c;">{n_stable:,}<span class="card-unit">명</span></div>
            <div class="card-percent">(전체의 {n_stable/TOTAL*100:.1f}%)</div></div>""",
            unsafe_allow_html=True)

    st.markdown("<br><hr>", unsafe_allow_html=True)

    n_activated  = int((promo_df['watch_time(min)_w1'] > 0).sum())
    n_retained   = int((promo_df['watch_time(min)_w2'] > 0).sum())
    n_revenue    = CONVERTED

    st.markdown("### 📊 단계별 주요 전환율")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("유입 ➡️ 활성화",     f"{n_activated/TOTAL*100:.1f}%",
              f"{n_activated:,}명 1주차 시청")
    c2.metric("활성화 ➡️ 유지",     f"{n_retained/n_activated*100:.1f}%",
              "2주 이상 지속 시청", delta_color="off")
    c3.metric("유지 ➡️ 유료 전환",  f"{n_revenue/n_retained*100:.1f}%",
              f"{n_revenue:,}명 방어 성공", delta_color="off")
    c4.metric("전체 전환율",        f"{n_revenue/TOTAL*100:.1f}%",
              "유입 → 최종 전환", delta_color="off")

    st.markdown("<br><hr>", unsafe_allow_html=True)

    col_funnel, col_shap = st.columns([3, 2])
    with col_funnel:
        st.subheader("🎯 AARRR 퍼널 분석")
        aarrr = pd.DataFrame({
            '단계 (Stage)': ['Acquisition', 'Activation', 'Retention', 'Revenue', 'Referral'],
            '유저 수':      [TOTAL, n_activated, n_retained, n_revenue, max(1, n_revenue // 6)]
        })
        fig_funnel = px.funnel(aarrr, x='유저 수', y='단계 (Stage)',
                               color_discrete_sequence=['#5c6bc0'])
        fig_funnel.update_layout(height=350, margin=dict(t=10, b=10, l=0, r=0))
        st.plotly_chart(fig_funnel, use_container_width=True)

    with col_shap:
        st.subheader("💡 이탈 판별 주요 변수")
        shap_df = pd.DataFrame({
            'Feature':    ['3주차 시청 시간', '3주차 리텐션', '1주차만 시청 여부',
                           '활동 비율', '평균 시청 시간'],
            'SHAP Value': [0.52, 0.44, 0.38, 0.25, 0.18]
        }).sort_values('SHAP Value')
        fig_shap = px.bar(shap_df, x='SHAP Value', y='Feature',
                          orientation='h', color_discrete_sequence=['#78909c'])
        fig_shap.update_layout(height=350, margin=dict(t=10, b=10, l=0, r=0))
        st.plotly_chart(fig_shap, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    n_never_active   = TOTAL - n_activated
    n_drop_after_w1  = n_activated - n_retained
    n_churn_after_ret = n_retained - n_revenue

    st.subheader("🌊 프로모션 유저 흐름 (Sankey Flow)")
    st.caption("프로모션 가입 → 활성화 → 유지 → 유료 전환 흐름 (실제 데이터)")
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            label=['전체 가입', '1주차 활성', '미활성', '2주차 유지', '1주차 이탈', '유료 전환', '이탈'],
            color=['#5c6bc0', '#42a5f5', '#ef9a9a', '#66bb6a', '#ef9a9a', '#388e3c', '#e53935'],
            pad=15, thickness=20,
        ),
        link=dict(
            source=[0, 0, 1, 1, 3, 3],
            target=[1, 2, 3, 4, 5, 6],
            value=[n_activated, n_never_active, n_retained, n_drop_after_w1, n_revenue, n_churn_after_ret],
            color=['rgba(92,107,192,0.4)', 'rgba(239,154,154,0.4)',
                   'rgba(66,165,245,0.4)', 'rgba(239,154,154,0.4)',
                   'rgba(102,187,106,0.4)', 'rgba(229,57,53,0.4)'],
        )
    )])
    fig_sankey.update_layout(height=400, margin=dict(t=20, b=20, l=10, r=10))
    st.plotly_chart(fig_sankey, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("🧠 고객 행동 패턴 및 군집 분석")
    col_ml, col_donut, col_line = st.columns([3, 3, 4])

    with col_ml:
        st.caption("**K-Means 패턴 군집 (PCA 2D, 실제 데이터)**")
        fig_scatter = px.scatter(
            pca_df, x='PC1', y='PC2', color='cluster_name',
            opacity=0.6, color_discrete_map=COLOR_MAP,
            labels={'cluster_name': '군집'}
        )
        fig_scatter.update_layout(height=300, margin=dict(t=10, b=0, l=0, r=0), showlegend=False)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_donut:
        st.caption("**군집 구성 비중 (실제 인원)**")
        seg_pie = promo_df.groupby('cluster_name', as_index=False)['USER_KEY'].count()
        seg_pie.columns = ['세그먼트', '인원']
        fig_donut = px.pie(seg_pie, values='인원', names='세그먼트',
                           hole=0.5, color='세그먼트', color_discrete_map=COLOR_MAP)
        fig_donut.update_layout(height=300, margin=dict(t=10, b=0, l=0, r=0), showlegend=False)
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_line:
        st.caption("**군집별 주차별 평균 시청 시간 (분)**")
        wt = promo_df.groupby('cluster_name')[
            ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']
        ].mean().reset_index()
        df_trend = wt.melt(id_vars='cluster_name',
                           value_vars=['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3'],
                           var_name='주차', value_name='시청 시간(분)')
        df_trend['주차'] = df_trend['주차'].map({
            'watch_time(min)_w1': '1주차',
            'watch_time(min)_w2': '2주차',
            'watch_time(min)_w3': '3주차'
        })
        fig_line = px.line(df_trend, x='주차', y='시청 시간(분)', color='cluster_name',
                           markers=True, color_discrete_map=COLOR_MAP,
                           labels={'cluster_name': '군집'})
        fig_line.update_layout(height=300, margin=dict(t=10, b=0, l=0, r=0),
                               legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("🔬 군집별 이탈 패턴 심층 분석")

    _p_cstats = promo_df.groupby(['cluster', 'cluster_name']).agg(
        총인원=('USER_KEY', 'count'),
        이탈자=('is_churn', 'sum'),
        방어성공=('is_churn_prevented', 'sum')
    ).reset_index()
    _p_cstats['이탈률'] = _p_cstats['이탈자'] / _p_cstats['총인원'] * 100
    _p_cstats['방어율'] = _p_cstats['방어성공'] / _p_cstats['총인원'] * 100
    _p_cstats['비중']   = _p_cstats['총인원'] / TOTAL * 100
    _p_cstats = _p_cstats.sort_values('cluster')

    _p_avg_w = promo_df.groupby('cluster_name')[
        ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']
    ].mean()

    col_bar_l, col_bar_r = st.columns([3, 2])
    with col_bar_l:
        st.caption("**군집별 이탈자 / 방어 성공 인원**")
        fig_cbar = go.Figure()
        fig_cbar.add_trace(go.Bar(
            name='이탈자',
            x=_p_cstats['cluster_name'],
            y=_p_cstats['이탈자'],
            marker_color='#e57373',
        ))
        fig_cbar.add_trace(go.Bar(
            name='방어 성공',
            x=_p_cstats['cluster_name'],
            y=_p_cstats['방어성공'],
            marker_color='#81c784',
        ))
        fig_cbar.update_layout(
            barmode='group', height=280,
            margin=dict(t=10, b=10, l=0, r=0),
            legend=dict(orientation='h', y=1.05),
        )
        st.plotly_chart(fig_cbar, use_container_width=True)

    with col_bar_r:
        st.caption("**군집별 이탈률 (%)**")
        fig_rate = px.bar(
            _p_cstats, x='cluster_name', y='이탈률',
            color='cluster_name', color_discrete_map=COLOR_MAP,
            text=_p_cstats['이탈률'].round(1).astype(str) + '%'
        )
        fig_rate.update_traces(textposition='outside')
        fig_rate.update_layout(
            height=280, showlegend=False,
            margin=dict(t=10, b=10, l=0, r=0),
        )
        st.plotly_chart(fig_rate, use_container_width=True)

    _p_CLUSTER_ICONS  = {' C0 (맛보기형)': '🔍', ' C1 (헤비유저형)': '🎬', ' C2 (후반몰입형)': '🌱', ' C3 (휴면형)': '👻'}
    _p_CLUSTER_LABEL  = {' C0 (맛보기형)': '맛보기형', ' C1 (헤비유저형)': '헤비유저형', ' C2 (후반몰입형)': '후반몰입형', ' C3 (휴면형)': '휴면형'}
    _p_CLUSTER_DESC   = {
        ' C0 (맛보기형)':   '평균 시청 13분, 단타 시청 비율 높음. 콘텐츠를 시작하지만 완주 못하고 이탈.',
        ' C1 (헤비유저형)': '총 시청 827분, 장르 다양성 최고. 가장 충성도 높은 핵심 고객군.',
        ' C2 (후반몰입형)': '3주차 리텐션 전 군집 중 최고. 시간이 갈수록 몰입도 상승하는 성장 패턴.',
        ' C3 (휴면형)':     '시청 횟수 평균 1회. 가입 후 사실상 미접속 상태.',
    }
    _p_CLUSTER_BORDER = {' C0 (맛보기형)': '#FF7A00', ' C1 (헤비유저형)': '#EA002C',
                         ' C2 (후반몰입형)': '#388e3c', ' C3 (휴면형)': '#fbc02d'}

    st.markdown("#### 군집별 특성 프로파일")
    pc0, pc1, pc2, pc3 = st.columns(4)
    _p_col_order = [' C0 (맛보기형)', ' C1 (헤비유저형)', ' C2 (후반몰입형)', ' C3 (휴면형)']
    for col_widget, cname in zip([pc0, pc1, pc2, pc3], _p_col_order):
        row = _p_cstats[_p_cstats['cluster_name'] == cname].iloc[0]
        wt_row = _p_avg_w.loc[cname]
        color  = _p_CLUSTER_BORDER[cname]
        with col_widget:
            st.markdown(
                f"""<div class="cluster-card" style="border-top: 4px solid {color};">
                <div class="cluster-title">{_p_CLUSTER_ICONS[cname]} {cname.strip()}</div>
                <div style="color:#666; margin-bottom:6px; font-size:12px;">{_p_CLUSTER_LABEL[cname]}</div>
                <b>인원:</b> {int(row['총인원']):,}명 ({row['비중']:.1f}%)<br>
                <b>이탈률:</b> <span style="color:#EA002C;">{row['이탈률']:.1f}%</span><br>
                <b>시청 추이:</b> {wt_row['watch_time(min)_w1']:.0f}분 →
                                  {wt_row['watch_time(min)_w2']:.0f}분 →
                                  {wt_row['watch_time(min)_w3']:.0f}분<br>
                <hr style="margin:6px 0;">
                <span style="font-size:12px;">{_p_CLUSTER_DESC[cname]}</span>
                </div>""",
                unsafe_allow_html=True
            )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("#### 📋 군집별 핵심 대응 전략")
    _p_strategies = {
        ' C0 (맛보기형)': {
            'icon': '📬', 'short': '취향 매칭 온보딩',
            'items': ['① 취향 파악 설문 (3문항)', '② 맞춤 인기작 큐레이션 메일', '③ 첫 시청 완료 보상 쿠폰']
        },
        ' C1 (헤비유저형)': {
            'icon': '🎯', 'short': '후속 콘텐츠 연결',
            'items': ['① 1주차 시청 완료 후 즉시 알림', '② 동일 장르 시리즈 추천', '③ 한정 타임딜 오퍼']
        },
        ' C2 (후반몰입형)': {
            'icon': '💎', 'short': 'VIP 전환 유도',
            'items': ['① 독점 콘텐츠 선공개 안내', '② 유료 첫 달 할인 혜택', '③ VIP 등급 혜택 시뮬레이션']
        },
        ' C3 (휴면형)': {
            'icon': '🔔', 'short': '재활성화 자동화',
            'items': ['① 3일 미접속 시 알림 발송', '② 이전 관심사 기반 추천', '③ 단기 무료 연장 쿠폰']
        }
    }
    ps0, ps1, ps2, ps3 = st.columns(4)
    for col_widget, cname in zip([ps0, ps1, ps2, ps3], _p_col_order):
        s = _p_strategies[cname]
        color = _p_CLUSTER_BORDER[cname]
        with col_widget:
            st.markdown(
                f"""<div class="cluster-card" style="border-top: 4px solid {color};">
                <div class="cluster-title">{s['icon']} {cname.strip()}</div>
                <div style="font-weight:600; margin-bottom:8px; color:#444;">{s['short']}</div>
                {'<br>'.join(f'<span style="font-size:12px;">{it}</span>' for it in s['items'])}
                </div>""",
                unsafe_allow_html=True
            )

# ==========================================
# 예측 모델 설정
# ==========================================
elif menu == "⚙️ 예측 모델 설정":
    st.header("⚙️ 예측 모델 설정")
    st.caption("이탈 예측 알고리즘의 파라미터를 조정하고 모델의 신뢰도를 모니터링합니다.")
    st.markdown("---")

    st.markdown("""
    <div style="display:flex; gap:10px; margin: 6px 0 18px 0;">
      <div style="flex:1; background:#e8f5e9; border-radius:8px; padding:12px 14px; border-left:3px solid #388e3c;">
        <div style="font-size:11px; font-weight:700; color:#1b5e20; margin-bottom:4px;">📌 이 페이지에서 알 수 있는 것 ①</div>
        <div style="font-size:13px; color:#333; line-height:1.5;">행동 기반 위험 점수의 <b>임계값을 조정</b>해 정밀도와 재현율의 균형을 직접 설정합니다.</div>
      </div>
      <div style="flex:1; background:#e3f2fd; border-radius:8px; padding:12px 14px; border-left:3px solid #1565c0;">
        <div style="font-size:11px; font-weight:700; color:#0d47a1; margin-bottom:4px;">📌 이 페이지에서 알 수 있는 것 ②</div>
        <div style="font-size:13px; color:#333; line-height:1.5;">각 군집별로 <b>독립적인 모델 파라미터</b>를 설정해 세그먼트 특성에 맞는 예측을 구성합니다.</div>
      </div>
      <div style="flex:1; background:#fff8e1; border-radius:8px; padding:12px 14px; border-left:3px solid #f9a825;">
        <div style="font-size:11px; font-weight:700; color:#e65100; margin-bottom:4px;">📌 이 페이지에서 알 수 있는 것 ③</div>
        <div style="font-size:13px; color:#333; line-height:1.5;">모델의 <b>혼동 행렬·ROC·정밀도-재현율</b> 곡선으로 현재 예측 성능을 모니터링합니다.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("모델 성능 지표 (Model Health)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Model Accuracy", "88.4%", "+0.5%")
    m2.metric("ROC-AUC",        "0.92",  "Stable")
    m3.metric("Precision",      "84.1%", "-1.2%")
    m4.metric("Recall",         "81.5%", "+2.3%")

    st.markdown("<br>", unsafe_allow_html=True)
    set_col1, set_col2 = st.columns(2)

    with set_col1:
        st.subheader("🛠️ 이탈 정의 및 임계값")
        threshold = st.slider("이탈 위험 임계값 (Threshold)", 0.0, 1.0, 0.7, step=0.01)
        n_above   = int((promo_df['churn_score'] >= threshold * 100).sum())
        st.info(f"현재 설정: 위험 점수 **{threshold*100:.0f}점** 이상 → **{n_above:,}명** 고위험 분류")
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("⚖️ 변수 가중치 조정")
        st.multiselect("우선 반영 행동 데이터",
                       ["주차별 시청 시간", "3주차 리텐션", "1주차 단독 시청 여부", "활동 비율", "장르 다양성"],
                       default=["주차별 시청 시간", "3주차 리텐션", "1주차 단독 시청 여부"])

    with set_col2:
        st.subheader("🎯 모델 재학습")
        st.text("마지막 학습일: 2021-04-10")
        if st.button("🚀 지금 즉시 모델 재학습 시작", use_container_width=True):
            import time
            with st.spinner('최적화 중...'): time.sleep(1)
            st.success("학습 완료!")
        st.markdown("---")
        st.subheader("📂 데이터 익스포트")
        st.button("📥 고위험군 명단 다운로드 (.csv)", use_container_width=True)
