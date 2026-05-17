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
        background: #f0f4ff !important;
        border-color: #4f8bf9 !important;
        color: #1a1a1a !important;
    }
    section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked),
    section[data-testid="stSidebar"] .stRadio [aria-checked="true"] {
        background: #1565c0 !important;
        color: white !important;
        border-color: #1565c0 !important;
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

    .border-very-high { border-top: 4px solid #d32f2f; }
    .border-high      { border-top: 4px solid #f57c00; }
    .border-medium    { border-top: 4px solid #fbc02d; }
    .border-low       { border-top: 4px solid #388e3c; }

    .cluster-card {
        border-radius: 8px;
        padding: 14px 12px;
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
    ' C1 (헤비유저형)': '#F06292',
    ' C0 (맛보기형)':   '#FFB74D',
    ' C3 (휴면형)':     '#90CAF9',
    ' C2 (후반몰입형)': '#66BB6A',
}
CLUSTER_MAP = {
    0: ' C0 (맛보기형)',
    1: ' C1 (헤비유저형)',
    2: ' C2 (후반몰입형)',
    3: ' C3 (휴면형)'
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
DATA_FILE      = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Membership_v4_clustered.csv')
DATA_FILE_ALL  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Membership_v4.csv')

@st.cache_data
def load_data():
    df_all = pd.read_csv(DATA_FILE_ALL, encoding='utf-8-sig')
    total_all = len(df_all)

    df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
    # ArrowStringArray → object 변환 (구버전 Streamlit LargeUtf8 오류 방지)
    for col in df.select_dtypes(include=['string']).columns:
        df[col] = df[col].astype(object)

    promo = df[df['is_promotion'] == 1].copy().reset_index(drop=True)

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

    return promo, pca_sample, total_all


def fmt_min(m):
    m = int(m)
    if m >= 60:
        return f"{m // 60}시간 {m % 60}분"
    return f"{m}분"


promo_df, pca_df, TOTAL_ALL = load_data()
TOTAL = len(promo_df)
CONVERTED = int(promo_df['is_repurchase'].sum())
CHURNED   = int(promo_df['is_churn'].sum())

# ==========================================
# 3. 좌측 사이드바 (탭 스타일)
# ==========================================
with st.sidebar:
    st.title("🎯 Retention Lab")
    st.caption("2021년 프로모션 이탈 방어 시스템")
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
        "프로모션 이탈 방어 종합 현황</h1>",
        unsafe_allow_html=True,
    )

    # 군집 통계 (탭 공통 사전 계산)
    cstats_m = promo_df.groupby(['cluster', 'cluster_name']).agg(
        총인원=('USER_KEY', 'count'),
        이탈자=('is_churn', 'sum'),
    ).reset_index().sort_values('cluster')
    cstats_m['이탈률'] = cstats_m['이탈자'] / cstats_m['총인원'] * 100
    cstats_m['비중']   = cstats_m['총인원'] / TOTAL * 100

    tab0, tab1, tab2 = st.tabs(["고객 현황", "군집 분포", "인구통계 분석"])

    # ── 탭0: 전체 고객 현황 ────────────────────────────────────────────
    with tab0:
        # 미니 KPI
        ov1, ov2, ov3, ov4 = st.columns(4)
        gender_counts = promo_df['gender_kor'].value_counts()
        male_pct   = gender_counts.get('남성', 0) / TOTAL * 100
        female_pct = gender_counts.get('여성', 0) / TOTAL * 100
        age_mode   = int(promo_df['age_group'].mode()[0])
        ov1.metric("100원 프로모션 가입자", f"{TOTAL:,} 명",             f"전체의 {TOTAL/TOTAL_ALL*100:.1f}%", delta_color="off")
        ov2.metric("이탈률",                f"{CHURNED/TOTAL*100:.1f} %", f"{CHURNED:,}명 이탈",               delta_color="inverse")
        ov3.metric("최다 연령대",           f"{age_mode}대",              "가장 많은 나이대",                   delta_color="off")
        ov4.metric("남성 : 여성",           f"{male_pct:.0f} : {female_pct:.0f}", "성별 비율",                 delta_color="off")

        st.markdown("<hr style='margin:14px 0;'>", unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns([2, 3, 5])

        # 성별 도넛 차트
        with col_a:
            st.caption("**성별 분포**")
            gen_dist = promo_df[promo_df['gender_kor'].isin(['남성', '여성'])]['gender_kor'].value_counts().reset_index()
            gen_dist.columns = ['성별', '인원']
            fig_gen_pie = px.pie(
                gen_dist, names='성별', values='인원',
                hole=0.55,
                color='성별',
                color_discrete_map={'남성': '#1565c0', '여성': '#e91e8c'},
            )
            fig_gen_pie.update_traces(textinfo='label+percent', textfont=dict(size=13, color='black', family='Arial'), insidetextorientation='horizontal')
            fig_gen_pie.update_layout(
                height=300, margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False,
            )
            st.plotly_chart(fig_gen_pie, use_container_width=True)

        # 나이대 분포 바 차트
        with col_b:
            st.caption("**나이대 분포**")
            age_dist = promo_df.groupby('age_group')['USER_KEY'].count().reset_index()
            age_dist.columns = ['나이대', '인원']
            age_dist['나이대'] = age_dist['나이대'].astype(str) + '대'
            age_dist['비중']   = (age_dist['인원'] / TOTAL * 100).round(1)
            fig_age_bar = px.bar(
                age_dist, x='나이대', y='인원',
                text=age_dist['비중'].astype(str) + '%',
                color='인원', color_continuous_scale='Blues',
            )
            fig_age_bar.update_traces(textposition='outside')
            fig_age_bar.update_layout(
                height=300, margin=dict(t=40, b=10, l=0, r=0),
                coloraxis_showscale=False,
                yaxis=dict(range=[0, age_dist['인원'].max() * 1.45], title='인원 수'),
                xaxis_title='',
            )
            st.plotly_chart(fig_age_bar, use_container_width=True)

        # 성별 × 나이대별 이탈률 라인 차트
        with col_c:
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

            fig_ga = px.line(
                gen_age_churn, x='나이대', y='이탈률', color='성별',
                markers=True,
                color_discrete_map={'남성': '#1565c0', '여성': '#e91e8c'},
                text='이탈률',
            )
            fig_ga.update_traces(textposition='top center', textfont_size=10, line_width=2.5, marker_size=9)
            fig_ga.update_layout(
                height=300, margin=dict(t=30, b=10, l=0, r=10),
                plot_bgcolor='white',
                yaxis=dict(gridcolor='#f0f0f0', title='이탈률 (%)', range=[15, 50]),
                xaxis_title='',
                legend=dict(
                    orientation='v', x=1.01, y=1, xanchor='left', yanchor='top',
                    bgcolor='rgba(255,255,255,0.9)', bordercolor='#e0e0e0', borderwidth=1,
                    font=dict(size=12),
                ),
            )
            st.plotly_chart(fig_ga, use_container_width=True)

        st.markdown("<hr style='margin:14px 0;'>", unsafe_allow_html=True)

        # 요금제 분포 + 이탈률
        plan_color_map = {'베이직': '#90caf9', '스탠다드': '#1565c0', '프리미엄': '#0d47a1'}
        plan_stats = promo_df.groupby('plan').agg(
            인원=('USER_KEY', 'count'),
            이탈=('is_churn', 'sum'),
        ).reset_index()
        plan_stats['이탈률'] = (plan_stats['이탈'] / plan_stats['인원'] * 100).round(1)
        plan_stats['비중']   = (plan_stats['인원'] / TOTAL * 100).round(1)

        pc1, pc2 = st.columns([1, 3])

        with pc1:
            st.caption("**요금제 분포**")
            fig_plan_pie = px.pie(
                plan_stats, names='plan', values='인원',
                hole=0.55,
                color='plan',
                color_discrete_map=plan_color_map,
            )
            fig_plan_pie.update_traces(
                textinfo='label+percent',
                textfont=dict(size=13, color='black', family='Arial'),
            )
            fig_plan_pie.update_layout(
                height=400, margin=dict(t=10, b=10, l=10, r=10), showlegend=False,
            )
            st.plotly_chart(fig_plan_pie, use_container_width=True)

        with pc2:
            st.caption("**요금제별 나이대 비율 (색상 = 이탈률)**")
            age_groups = sorted(promo_df['age_group'].dropna().unique())

            at_labels  = ['전체']
            at_parents = ['']
            at_values  = [TOTAL]
            at_colors  = [CHURNED / TOTAL * 100]
            at_custom  = ['']

            for plan in ['베이직', '스탠다드', '프리미엄']:
                sub_plan = promo_df[promo_df['plan'] == plan]
                n_plan   = len(sub_plan)
                cr_plan  = sub_plan['is_churn'].mean() * 100
                at_labels  += [plan]
                at_parents += ['전체']
                at_values  += [n_plan]
                at_colors  += [cr_plan]
                at_custom  += [f"{n_plan:,}명 | 이탈 {cr_plan:.1f}%"]

                for ag in age_groups:
                    sub = sub_plan[sub_plan['age_group'] == ag]
                    if len(sub) == 0:
                        continue
                    n_sub  = len(sub)
                    cr_sub = sub['is_churn'].mean() * 100
                    at_labels  += [f"{plan}·{int(ag)}대"]
                    at_parents += [plan]
                    at_values  += [n_sub]
                    at_colors  += [cr_sub]
                    at_custom  += [f"{int(ag)}대 | {n_sub:,}명 ({n_sub/n_plan*100:.1f}%) | 이탈 {cr_sub:.1f}%"]

            fig_age_tree = go.Figure(go.Treemap(
                labels=at_labels, parents=at_parents, values=at_values,
                branchvalues='total',
                marker=dict(
                    colors=at_colors,
                    colorscale='RdBu_r',
                    cmin=15, cmax=50,
                    showscale=True,
                    colorbar=dict(
                        title=dict(text='이탈률(%)', side='right'),
                        thickness=14, len=0.8,
                        tickvals=[15, 25, 35, 50],
                        ticktext=['15%', '25%', '35%', '50%+'],
                    ),
                    line=dict(width=2, color='white'),
                ),
                customdata=at_custom,
                texttemplate='<b>%{label}</b><br>%{customdata}',
                textfont=dict(size=11, color='#1a1a1a', family='Arial'),
                hovertemplate='<b>%{label}</b><br>%{customdata}<extra></extra>',
                root_color='#eeeeee',
            ))
            fig_age_tree.update_layout(height=400, margin=dict(t=10, b=10, l=10, r=80))
            st.plotly_chart(fig_age_tree, use_container_width=True)
            st.caption("🟥 붉을수록 이탈 고위험 &nbsp;&nbsp; 🟦 파랄수록 이탈 저위험 &nbsp;&nbsp;|&nbsp;&nbsp; 면적 = 인원 수 비례")

    # ── 탭1: 군집 분포 ─────────────────────────────────────────────────
    with tab1:
        # KPI 행
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("총 프로모션 가입자", f"{TOTAL:,} 명",             "전체 데이터 기준",        delta_color="off")
        kpi2.metric("이탈률",             f"{CHURNED/TOTAL*100:.1f} %", f"{CHURNED:,}명 이탈",     delta_color="inverse")
        kpi3.metric("이탈 고위험군",      "X 명",                   "즉시 대응 필요 (37.3%)", delta_color="inverse")

        st.markdown("<hr style='margin:14px 0;'>", unsafe_allow_html=True)

        # ── [2, 3, 5] 비율: 인원 비중 | 이탈률 | 주차별 추이 ──────────
        cl_names  = cstats_m['cluster_name'].tolist()
        cl_colors = [COLOR_MAP.get(n, '#999') for n in cl_names]
        cl_labels = [n.strip() for n in cl_names]

        col_a, col_b, col_c = st.columns([2, 3, 5])

        with col_a:
            st.caption("**군집별 인원 비중**")
            fig_pie = go.Figure(go.Pie(
                labels=cl_labels,
                values=cstats_m['총인원'].tolist(),
                hole=0.5,
                marker=dict(colors=cl_colors, line=dict(color='white', width=2)),
                textinfo='percent',
                textfont=dict(size=12, color='white', family='Arial'),
                insidetextorientation='horizontal',
                hovertemplate='<b>%{label}</b><br>인원: %{value:,}명<br>비중: %{percent}<extra></extra>',
            ))
            fig_pie.update_layout(
                height=300, margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_b:
            st.caption("**군집별 이탈률**")
            churn_sorted = cstats_m.sort_values('이탈률', ascending=True)
            bar_colors   = [COLOR_MAP.get(n, '#999') for n in churn_sorted['cluster_name']]
            fig_churn_bar = go.Figure(go.Bar(
                y=[n.strip() for n in churn_sorted['cluster_name']],
                x=churn_sorted['이탈률'].round(1),
                orientation='h',
                marker=dict(color=bar_colors),
                text=churn_sorted['이탈률'].round(1).astype(str) + '%',
                textposition='outside',
                textfont=dict(size=12),
                hovertemplate='<b>%{y}</b><br>이탈률: %{x:.1f}%<extra></extra>',
            ))
            fig_churn_bar.update_layout(
                height=300, margin=dict(t=10, b=10, l=10, r=50),
                plot_bgcolor='white',
                xaxis=dict(gridcolor='#f0f0f0', title='이탈률 (%)',
                           range=[0, churn_sorted['이탈률'].max() * 1.3]),
                yaxis=dict(title=''),
            )
            st.plotly_chart(fig_churn_bar, use_container_width=True)

        with col_c:
            st.caption("**주차별 평균 시청 시간 추이**")
            wt_cols = ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']
            trend_order = [' C0 (맛보기형)', ' C1 (헤비유저형)', ' C2 (후반몰입형)', ' C3 (휴면형)']
            trend_colors_list = ['#FFB74D', '#F06292', '#66BB6A', '#90CAF9']

            trend_rows = []
            for cn in trend_order:
                row_t = promo_df[promo_df['cluster_name'] == cn][wt_cols].mean()
                vals = [round(row_t[c], 1) for c in wt_cols]
                for i, (w, v) in enumerate(zip(['1주차', '2주차', '3주차'], vals)):
                    if i == 0:
                        label = f"{v}분"
                    else:
                        diff = v - vals[i - 1]
                        sign = '△' if diff >= 0 else '▽'
                        label = f"{v}분<br><sub>{sign}{abs(diff):.1f}</sub>"
                    trend_rows.append({'군집': cn.strip(), '주차': w, '시청시간(분)': v, '라벨': label})
            trend_df = pd.DataFrame(trend_rows)

            fig_trend = px.bar(
                trend_df, x='주차', y='시청시간(분)', color='군집',
                barmode='group',
                color_discrete_sequence=trend_colors_list,
                text='라벨',
            )
            fig_trend.update_traces(textposition='outside', textfont_size=11)
            fig_trend.update_layout(
                height=300,
                margin=dict(t=10, b=10, l=0, r=0),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
                yaxis_title='평균 시청 시간 (분)',
                xaxis_title='',
                plot_bgcolor='white',
                yaxis=dict(gridcolor='#f0f0f0', range=[0, trend_df['시청시간(분)'].max() * 1.25]),
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        # ── 군집별 특성 프로파일: 4열 가로 나열 ──────────────────────
        st.caption("**📋 군집별 특성 프로파일**")
        CLUSTER_ICONS_M  = {' C0 (맛보기형)': '🔍', ' C1 (헤비유저형)': '🎬',
                            ' C2 (후반몰입형)': '🌱', ' C3 (휴면형)': '👻'}
        CLUSTER_LABEL_M  = {' C0 (맛보기형)': '맛보기형', ' C1 (헤비유저형)': '헤비유저형',
                            ' C2 (후반몰입형)': '안정형',   ' C3 (휴면형)': '휴면형'}
        CLUSTER_DESC_M   = {
            ' C0 (맛보기형)':   '평균 시청 13분, 5분 미만 시청 비율 높음. 콘텐츠를 시작하지만 완주 못하고 이탈.',
            ' C1 (헤비유저형)': '총 시청 827분, 장르 다양성 최고(5.25). 가장 충성도 높은 핵심 고객군.',
            ' C2 (후반몰입형)': '3주차 리텐션 51.9%로 전 군집 중 최고. 시간이 갈수록 몰입도 상승하는 성장 패턴.',
            ' C3 (휴면형)':     '시청 횟수 평균 1회, 최근 접속 15일. 가입 후 사실상 미접속 상태.'
        }
        CLUSTER_BORDER_M = {' C0 (맛보기형)': '#FFA726', ' C1 (헤비유저형)': '#EC407A',
                            ' C2 (후반몰입형)': '#66BB6A', ' C3 (휴면형)': '#42A5F5'}

        def churn_badge_color(rate):
            if rate >= 40:   return '#e53935', '#ffebee'
            elif rate >= 25: return '#f57c00', '#fff3e0'
            else:            return '#2e7d32', '#e8f5e9'

        prof_cols = st.columns(4)
        for i, cname in enumerate([' C0 (맛보기형)', ' C1 (헤비유저형)', ' C2 (후반몰입형)', ' C3 (휴면형)']):
            row_c = cstats_m[cstats_m['cluster_name'] == cname].iloc[0]
            color = CLUSTER_BORDER_M[cname]
            text_color, bg_color = churn_badge_color(row_c['이탈률'])
            with prof_cols[i]:
                st.markdown(
                    f"""<div class="cluster-card" style="border-top: 4px solid {color}; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                      <div class="cluster-title" style="font-size:13px; margin:0;">{CLUSTER_ICONS_M[cname]} {cname.strip()}</div>
                      <span style="font-size:11px; font-weight:700; color:{text_color}; background:{bg_color};
                                   padding:2px 7px; border-radius:10px; white-space:nowrap;">
                        이탈 {row_c['이탈률']:.1f}%
                      </span>
                    </div>
                    <span style="font-size:12px; color:#555;">{CLUSTER_DESC_M[cname]}</span>
                    </div>""",
                    unsafe_allow_html=True
                )

        # ── 요금제 분포 트리맵 ─────────────────────────────────────────
        st.markdown("<hr style='margin:20px 0 12px 0;'>", unsafe_allow_html=True)
        st.markdown("**요금제 × 군집 분포 (트리맵)**")

        plan_color_map_t = {'베이직': '#90caf9', '스탠다드': '#1565c0', '프리미엄': '#0d47a1'}
        plan_order = ['베이직', '스탠다드', '프리미엄']
        cluster_order = [' C0 (맛보기형)', ' C1 (헤비유저형)', ' C2 (후반몰입형)', ' C3 (휴면형)']

        pt_labels, pt_parents, pt_values, pt_colors, pt_custom, pt_textcolors = ['전체'], [''], [TOTAL], ['#ffffff'], [''], ['#212121']

        for plan in plan_order:
            sub_plan = promo_df[promo_df['plan'] == plan]
            n_plan   = len(sub_plan)
            cr_plan  = sub_plan['is_churn'].mean() * 100
            pt_labels      += [plan]
            pt_parents     += ['전체']
            pt_values      += [n_plan]
            pt_colors      += [plan_color_map_t[plan]]
            pt_custom      += [f"{n_plan:,}명 ({n_plan/TOTAL*100:.1f}%) | 이탈 {cr_plan:.1f}%"]
            pt_textcolors  += ['white']   # 베이직/스탠다드/프리미엄 → 흰색 유지

            for cname in cluster_order:
                sub = sub_plan[sub_plan['cluster_name'] == cname]
                if len(sub) == 0:
                    continue
                n_sub  = len(sub)
                cr_sub = sub['is_churn'].mean() * 100
                pt_labels      += [f"{plan}·{cname.strip()}"]
                pt_parents     += [plan]
                pt_values      += [n_sub]
                pt_colors      += [COLOR_MAP[cname]]
                pt_custom      += [f"{n_sub:,}명 | 이탈 {cr_sub:.1f}%"]
                pt_textcolors  += ['#212121']  # 군집 항목 → 검정

        fig_plan_tree = go.Figure(go.Treemap(
            labels=pt_labels, parents=pt_parents, values=pt_values,
            branchvalues='total',
            marker=dict(colors=pt_colors, line=dict(width=2, color='white')),
            customdata=pt_custom,
            texttemplate='<b>%{label}</b><br>%{customdata}',
            textfont=dict(size=11, color=pt_textcolors),
            hovertemplate='<b>%{label}</b><br>%{customdata}<extra></extra>',
            root_color='white',
        ))
        fig_plan_tree.update_layout(height=400, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_plan_tree, use_container_width=True)
        st.caption("🟦 요금제 색상 (베이직/스탠다드/프리미엄) &nbsp;&nbsp; 🟫 군집별 색상으로 세분화 &nbsp;&nbsp;|&nbsp;&nbsp; 면적 = 인원 수 비례")

    # ── 탭2: 인구통계 분석 (전용 미니 KPI + 차트) ────────────────────
    with tab2:
        # 인구통계 전용 사전 계산
        age_df = promo_df.groupby('age_group')['is_churn'].agg(['mean', 'count']).reset_index()
        age_df.columns = ['나이대', '이탈률', '인원']
        age_df['이탈률'] *= 100
        age_df['나이대_str'] = age_df['나이대'].astype(str) + '대'

        gen_df = promo_df[promo_df['gender_kor'].isin(['여성', '남성'])].groupby('gender_kor').agg(
            이탈률=('is_churn', 'mean'), 인원=('USER_KEY', 'count')
        ).reset_index()
        gen_df['이탈률'] *= 100
        gen_df.columns = ['성별', '이탈률', '인원']

        top_age      = age_df.loc[age_df['이탈률'].idxmax(), '나이대_str']
        top_age_rate = age_df['이탈률'].max()
        gen_gap      = abs(gen_df['이탈률'].max() - gen_df['이탈률'].min())
        high_gen     = gen_df.loc[gen_df['이탈률'].idxmax(), '성별']

        # 인구통계 전용 미니 KPI
        mk1, mk2, mk3 = st.columns(3)
        mk1.metric("전체 이탈률 (기준선)", f"{CHURNED/TOTAL*100:.1f} %", f"총 {TOTAL:,}명 중 {CHURNED:,}명", delta_color="off")
        mk2.metric("최고위험 나이대",      top_age,                       f"이탈률 {top_age_rate:.1f}%",       delta_color="inverse")
        mk3.metric("성별 이탈률 격차",     f"{gen_gap:.1f} %p",           f"{high_gen}이 더 높음",             delta_color="inverse")

        st.markdown("---")

        dem_col1, dem_col2 = st.columns(2)

        with dem_col1:
            st.caption("**나이대별 이탈률 (%)**")
            fig_age = px.bar(
                age_df, x='나이대_str', y='이탈률',
                text=age_df['이탈률'].round(1).astype(str) + '%',
                color='이탈률', color_continuous_scale='RdYlGn_r', range_color=[0, 60],
                labels={'나이대_str': '나이대'},
            )
            fig_age.update_traces(textposition='outside')
            fig_age.update_layout(
                height=320, margin=dict(t=10, b=10, l=0, r=0),
                coloraxis_showscale=False, yaxis_title='이탈률 (%)', xaxis_title=''
            )
            st.plotly_chart(fig_age, use_container_width=True)

        with dem_col2:
            st.caption("**성별 이탈률 (%)**")
            fig_gen = px.bar(
                gen_df, x='성별', y='이탈률',
                text=gen_df['이탈률'].round(1).astype(str) + '%',
                color='성별', color_discrete_map={'여성': '#e91e8c', '남성': '#1565c0'},
            )
            fig_gen.update_traces(textposition='outside')
            fig_gen.update_layout(
                height=320, margin=dict(t=10, b=10, l=0, r=0),
                showlegend=False, yaxis_title='이탈률 (%)', xaxis_title=''
            )
            st.plotly_chart(fig_gen, use_container_width=True)

        st.caption("**나이대 × 군집별 이탈률 히트맵 (%)**")
        age_cl = promo_df.groupby(['age_group', 'cluster_name'])['is_churn'].mean().reset_index()
        age_cl.columns = ['나이대', '군집', '이탈률']
        age_cl['이탈률'] *= 100
        age_cl['나이대'] = age_cl['나이대'].astype(str) + '대'
        age_pivot = age_cl.pivot(index='나이대', columns='군집', values='이탈률')
        fig_hm = px.imshow(
            age_pivot.round(1), color_continuous_scale='RdYlGn_r',
            zmin=0, zmax=60, text_auto='.1f', labels={'color': '이탈률(%)'},
        )
        fig_hm.update_layout(height=300, margin=dict(t=10, b=10, l=0, r=0))
        st.plotly_chart(fig_hm, use_container_width=True)

        st.caption("**성별 × 군집별 이탈률 (%)**")
        gen_cl = promo_df[promo_df['gender_kor'].isin(['여성', '남성'])].groupby(
            ['gender_kor', 'cluster_name'])['is_churn'].mean().reset_index()
        gen_cl.columns = ['성별', '군집', '이탈률']
        gen_cl['이탈률'] *= 100
        fig_gcl = px.bar(
            gen_cl, x='군집', y='이탈률', color='성별', barmode='group',
            color_discrete_map={'여성': '#e91e8c', '남성': '#1565c0'},
            text=gen_cl['이탈률'].round(1).astype(str) + '%',
        )
        fig_gcl.update_traces(textposition='outside')
        fig_gcl.update_layout(
            height=300, margin=dict(t=10, b=10, l=0, r=0),
            yaxis_title='이탈률 (%)', xaxis_title=''
        )
        st.plotly_chart(fig_gcl, use_container_width=True)

        st.markdown("<hr style='margin:14px 0;'>", unsafe_allow_html=True)

        # 나이대 × 주차별 평균 시청 시간 선그래프
        st.caption("**나이대별 주차별 평균 시청 시간 추이**")
        wt_cols_tab2 = ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']
        age_line_rows = []
        for ag in sorted(promo_df['age_group'].unique()):
            grp = promo_df[promo_df['age_group'] == ag][wt_cols_tab2].mean()
            for w, col_w in zip(['1주차', '2주차', '3주차'], wt_cols_tab2):
                age_line_rows.append({'나이대': f"{int(ag)}대", '주차': w, '평균 시청(분)': round(grp[col_w], 1)})
        age_line_df = pd.DataFrame(age_line_rows)

        fig_age_line = px.line(
            age_line_df, x='주차', y='평균 시청(분)', color='나이대',
            markers=True, text='평균 시청(분)',
        )
        fig_age_line.update_traces(textposition='top center', textfont_size=10, line_width=2, marker_size=7)
        fig_age_line.update_layout(
            height=320, margin=dict(t=20, b=10, l=0, r=120),
            plot_bgcolor='white',
            yaxis=dict(gridcolor='#f0f0f0', title='평균 시청 시간 (분)'),
            xaxis_title='',
            legend=dict(
                orientation='v', x=1.01, y=1, xanchor='left', yanchor='top',
                bgcolor='rgba(255,255,255,0.9)', bordercolor='#e0e0e0', borderwidth=1,
                font=dict(size=12), title=dict(text='나이대', font=dict(size=12)),
            ),
        )
        st.plotly_chart(fig_age_line, use_container_width=True)

        st.markdown("<hr style='margin:14px 0;'>", unsafe_allow_html=True)

        # 성별 × 주차별 평균 시청 시간 선그래프
        st.caption("**성별 주차별 평균 시청 시간 추이**")
        wt_cols_dem = ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']
        gender_line_rows = []
        for g in ['남성', '여성']:
            grp = promo_df[promo_df['gender_kor'] == g][wt_cols_dem].mean()
            for w, col_w in zip(['1주차', '2주차', '3주차'], wt_cols_dem):
                gender_line_rows.append({'성별': g, '주차': w, '평균 시청(분)': round(grp[col_w], 1)})
        gender_line_df = pd.DataFrame(gender_line_rows)

        fig_gen_line = px.line(
            gender_line_df, x='주차', y='평균 시청(분)', color='성별',
            markers=True,
            color_discrete_map={'남성': '#1565c0', '여성': '#e91e8c'},
            text='평균 시청(분)',
        )
        fig_gen_line.update_traces(textposition='top center', textfont_size=11, line_width=2.5, marker_size=9)
        fig_gen_line.update_layout(
            height=320, margin=dict(t=20, b=10, l=0, r=120),
            plot_bgcolor='white',
            yaxis=dict(gridcolor='#f0f0f0', title='평균 시청 시간 (분)'),
            xaxis_title='',
            legend=dict(
                orientation='v', x=1.01, y=1, xanchor='left', yanchor='top',
                bgcolor='rgba(255,255,255,0.9)', bordercolor='#e0e0e0', borderwidth=1,
                font=dict(size=12),
            ),
        )
        st.plotly_chart(fig_gen_line, use_container_width=True)

# ==========================================
# 4-1. 100원 프로모션 유저 분석
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

    # KPI
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("100원 프로모션 가입자",   f"{TOTAL:,} 명",  "전체의 51.2%", delta_color="off")
    kpi2.metric("유료 전환율",          f"{CONVERTED/TOTAL*100:.1f} %", f"{CONVERTED:,}명 재구매 완료")
    kpi3.metric("이탈 고위험군",        "4,463 명",        "즉시 대응 필요 (37.3%)", delta_color="inverse")
    kpi4.metric("방어 성공 시 기대 매출", "약 1.4억 원",    "추정 LTV 기준")

    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    # 필터 헤더
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

    # 실제 데이터 필터링
    filtered_raw = promo_df[
        (promo_df['cluster_name'].isin(selected_segs)) &
        (promo_df['churn_score'] >= prob_range[0]) &
        (promo_df['churn_score'] <= prob_range[1]) &
        (promo_df['watch_time(min)_w1'] >= watch_range[0]) &
        (promo_df['watch_time(min)_w1'] <= watch_range[1])
    ].sort_values('churn_score', ascending=False).head(50)

    display_df = pd.DataFrame({
        '고객 ID':       filtered_raw['USER_KEY'].str[:10].values,
        '성별':          filtered_raw['gender_kor'].values,
        '나이대':        (filtered_raw['age_group'].astype(int).astype(object).apply(lambda x: f"{x}대")),
        '이탈 위험 점수(%)': filtered_raw['churn_score'].round(1).values,
        '소속 세그먼트':  filtered_raw['cluster_name'].str.strip().values,
        '1주차 시청':    filtered_raw['watch_time(min)_w1'].apply(fmt_min).values,
        '2주차 시청':    filtered_raw['watch_time(min)_w2'].apply(fmt_min).values,
        '3주차 시청':    filtered_raw['watch_time(min)_w3'].apply(fmt_min).values,
        '위험 패턴':     filtered_raw['cluster_name'].map(PATTERN_MAP).values,
        '대응 액션':     filtered_raw['cluster_name'].map(ACTION_MAP).values,
    })
    st.dataframe(display_df.set_index('고객 ID').astype(object), use_container_width=True, height=280)

    # 액션 버튼
    st.markdown("<br>", unsafe_allow_html=True)
    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1:
        if st.button("🚨 C1 체리피커 타겟 푸시", use_container_width=True): st.success("푸시 발송 완료!")
    with ac2:
        if st.button("📧 C0 맞춤 추천 메일",      use_container_width=True): st.success("메일 발송 완료!")
    with ac3:
        if st.button("🎫 C3 재참여 쿠폰 발송",    use_container_width=True): st.success("쿠폰 발송 완료!")
    with ac4:
        if st.button("💎 C2 VIP 혜택 제안",       use_container_width=True): st.success("혜택 발송 완료!")

    st.markdown("<br><hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    # XAI Expander
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

    with st.expander("🕵️‍♂️ 특정 고객 이탈 원인 심층 분석 (Local XAI) 열기"):
        user_options = display_df['고객 ID'].tolist() if not display_df.empty else ["선택 불가"]
        target_uid   = st.selectbox("분석할 고객 ID 선택", user_options)

        if not display_df.empty:
            row     = display_df[display_df['고객 ID'] == target_uid].iloc[0]
            raw_row = filtered_raw[filtered_raw['USER_KEY'].str[:10] == target_uid].iloc[0]
            segment = row['소속 세그먼트']
            seg_key = ' ' + segment if not segment.startswith(' ') else segment
            cluster_sub = promo_df[promo_df['cluster_name'] == seg_key]

            # 좌(유저정보+레이더+라인) / 우(편차 바) 분할
            main_left, main_right = st.columns([5, 5])

            with main_left:
                # 상단: 유저 정보 | 레이더 차트
                info_col, radar_col = st.columns([2, 3])

                with info_col:
                    st.markdown(
                        f"**이탈 위험:** <span style='color:#d32f2f; font-size:18px; font-weight:bold;'>"
                        f"{row['이탈 위험 점수(%)']:.1f}%</span>", unsafe_allow_html=True)
                    st.markdown(f"**소속 그룹:** {segment}")
                    st.markdown(f"**성별 / 나이대:** {row['성별']} / {row['나이대']}")

                with radar_col:
                    st.caption("**시청 장르 분포**")
                    g_vals  = [float(raw_row.get(col, 0)) for col in GENRE_COLS.values()]
                    g_names = list(GENRE_COLS.keys())
                    if sum(g_vals) == 0:
                        st.info("장르 시청 데이터 없음")
                    else:
                        fig_radar = go.Figure(go.Scatterpolar(
                            r=g_vals + [g_vals[0]],
                            theta=g_names + [g_names[0]],
                            fill='toself',
                            fillcolor='rgba(92,107,192,0.25)',
                            line=dict(color='#5c6bc0', width=2),
                        ))
                        fig_radar.update_layout(
                            polar=dict(
                                radialaxis=dict(visible=True,
                                                range=[0, max(g_vals) * 1.3 + 0.01],
                                                showticklabels=False),
                                angularaxis=dict(tickfont=dict(size=8))
                            ),
                            height=175,
                            margin=dict(t=45, b=45, l=45, r=45),
                            showlegend=False
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)

                # 하단: 주차별 시청 시간 (좌측 전체 폭)
                st.caption("**주차별 시청 시간 추이**")
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
                    name='선택 유저', line=dict(color='#d32f2f', width=2), marker=dict(size=7)
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
                # 유저 vs 군집 평균 편차 바 차트
                st.caption("**유저 지표 vs 군집 평균 (편차 비율)**")
                feat_names, deviations, bar_colors = [], [], []
                for label, col in FEAT_COLS.items():
                    u_val  = float(raw_row.get(col, 0))
                    c_mean = float(cluster_sub[col].mean())
                    dev    = (u_val - c_mean) / (c_mean + 1e-9) if c_mean != 0 else 0.0
                    feat_names.append(label)
                    deviations.append(round(dev, 3))
                    bar_colors.append('#d32f2f' if dev < 0 else '#388e3c')

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

    # LTV Expander
    with st.expander("💰 세그먼트별 예상 LTV 및 마케팅 예산 할당 가이드 열기"):
        ltv_col1, ltv_col2 = st.columns([5, 5])
        with ltv_col1:
            avg_watch = promo_df.groupby('cluster_name')['total_watch_time(min)'].mean()
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
                    "- **C2 (안정적)**: 유료 전환 가장 높음 → 적극적 VIP 혜택 투입 권장.\n"
                    "- **C1 (체리피커)**: 고시청 후 이탈 → 시리즈 큐레이션 알림.\n"
                    "- **C0/C3**: 이탈 위험 최고 → 저비용 알림 + 쿠폰 중심 방어.")

# ==========================================
# 4-2. 프로모션 행동 분석
# ==========================================
elif menu == "👥 프로모션 행동 분석":
    st.header("👥 프로모션 행동 분석 현황")
    st.markdown("---")

    # 이탈 위험도별 고객 분포 (실제 데이터 기반 행동 버킷)
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
            <div class="card-value" style="color:#d32f2f;">{n_only_w1:,}<span class="card-unit">명</span></div>
            <div class="card-percent">(전체의 {n_only_w1/TOTAL*100:.1f}%)</div></div>""",
            unsafe_allow_html=True)
    with card2:
        st.markdown(f"""<div class="risk-card border-high">
            <div class="card-title">높음 — 3주차 미시청</div>
            <div class="card-value" style="color:#f57c00;">{n_no_w3:,}<span class="card-unit">명</span></div>
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

    # AARRR 전환율 지표 (실제 데이터)
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

    # Sankey — 실제 숫자 기반
    n_never_active = TOTAL - n_activated
    n_drop_after_w1 = n_activated - n_retained
    n_churn_after_retain = n_retained - n_revenue
    st.subheader("🌊 프로모션 유저 흐름 (Sankey Flow)")
    st.caption("프로모션 가입 → 활성화 → 유지 → 유료 전환 흐름 (실제 데이터)")
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15, thickness=20,
            line=dict(color="black", width=0.5),
            label=[
                f"프로모션 가입\n({TOTAL:,})",
                f"1주차 활성화\n({n_activated:,})",
                f"2주 이상 유지\n({n_retained:,})",
                f"유료 전환\n({n_revenue:,})",
                "이탈"
            ],
            color=["#9e9e9e", "#5c6bc0", "#388e3c", "#1565c0", "#d32f2f"]
        ),
        link=dict(
            source=[0, 0, 1, 1, 2, 2],
            target=[1, 4, 2, 4, 3, 4],
            value= [n_activated, n_never_active,
                    n_retained,  n_drop_after_w1,
                    n_revenue,   n_churn_after_retain],
            color=["rgba(92,107,192,0.4)",  "rgba(211,47,47,0.3)",
                   "rgba(56,142,60,0.4)",   "rgba(211,47,47,0.3)",
                   "rgba(21,101,192,0.4)",  "rgba(251,192,45,0.3)"]
        )
    )])
    fig_sankey.update_layout(height=400, margin=dict(t=20, b=20, l=10, r=10))
    st.plotly_chart(fig_sankey, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # 군집 요약 시각화 (PCA / 도넛 / 트렌드)
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

    # ==========================================
    # 군집 심층 분석 섹션 (NEW)
    # ==========================================
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("🔬 군집별 이탈 패턴 심층 분석")

    # 군집별 통계
    cstats = promo_df.groupby(['cluster', 'cluster_name']).agg(
        총인원=('USER_KEY', 'count'),
        이탈자=('is_churn', 'sum'),
        방어성공=('is_churn_prevented', 'sum')
    ).reset_index()
    cstats['이탈률'] = cstats['이탈자'] / cstats['총인원'] * 100
    cstats['방어율'] = cstats['방어성공'] / cstats['총인원'] * 100
    cstats['비중']   = cstats['총인원'] / TOTAL * 100
    cstats = cstats.sort_values('cluster')

    avg_w = promo_df.groupby('cluster_name')[
        ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']
    ].mean()

    col_bar_l, col_bar_r = st.columns([3, 2])
    with col_bar_l:
        st.caption("**군집별 이탈자 / 방어 성공 인원**")
        fig_cbar = go.Figure()
        fig_cbar.add_trace(go.Bar(
            name='이탈자',
            x=cstats['cluster_name'],
            y=cstats['이탈자'],
            marker_color='#e57373',
            text=cstats['이탈자'].apply(lambda x: f"{x:,}명"),
            textposition='inside'
        ))
        fig_cbar.add_trace(go.Bar(
            name='방어 성공',
            x=cstats['cluster_name'],
            y=cstats['방어성공'],
            marker_color='#66bb6a',
            text=cstats['방어성공'].apply(lambda x: f"{x:,}명"),
            textposition='inside'
        ))
        fig_cbar.update_layout(
            barmode='stack', height=320,
            margin=dict(t=10, b=10, l=0, r=0),
            legend=dict(orientation="h", y=1.05)
        )
        st.plotly_chart(fig_cbar, use_container_width=True)

    with col_bar_r:
        st.caption("**군집별 이탈률 (%)**")
        fig_rate = px.bar(
            cstats, x='cluster_name', y='이탈률',
            color='cluster_name', color_discrete_map=COLOR_MAP,
            text=cstats['이탈률'].round(1).astype(str) + '%'
        )
        fig_rate.update_traces(textposition='outside')
        fig_rate.update_layout(
            height=320, showlegend=False,
            margin=dict(t=10, b=10, l=0, r=0),
            yaxis=dict(range=[75, 90])
        )
        st.plotly_chart(fig_rate, use_container_width=True)

    # 군집 프로파일 카드
    st.markdown("#### 군집별 특성 프로파일")
    CLUSTER_ICONS   = {' C0 (맛보기형)': '🔍', ' C1 (헤비유저형)': '🎬', ' C2 (후반몰입형)': '🌱', ' C3 (휴면형)': '👻'}
    CLUSTER_LABEL   = {' C0 (맛보기형)': '맛보기형', ' C1 (헤비유저형)': '헤비유저형', ' C2 (후반몰입형)': '안정형', ' C3 (휴면형)': '휴면형'}
    CLUSTER_DESC    = {
        ' C0 (맛보기형)':   '평균 시청 13분, 5분 미만 시청 비율 높음. 콘텐츠를 시작하지만 완주 못하고 이탈.',
        ' C1 (헤비유저형)': '총 시청 827분, 장르 다양성 최고(5.25). 가장 충성도 높은 핵심 고객군. 이탈률 15.8%.',
        ' C2 (후반몰입형)':     '3주차 리텐션 51.9%로 전 군집 중 최고. 시간이 갈수록 몰입도 상승하는 성장 패턴.',
        ' C3 (휴면형)':     '시청 횟수 평균 1회, 최근 접속 15일. 가입 후 사실상 미접속 상태.'
    }
    CLUSTER_BORDER  = {' C0 (맛보기형)': '#f57c00', ' C1 (헤비유저형)': '#d32f2f',
                       ' C2 (후반몰입형)': '#388e3c', ' C3 (휴면형)': '#fbc02d'}

    cc0, cc1, cc2, cc3 = st.columns(4)
    col_order = [' C0 (맛보기형)', ' C1 (헤비유저형)', ' C2 (후반몰입형)', ' C3 (휴면형)']
    for col_widget, cname in zip([cc0, cc1, cc2, cc3], col_order):
        row = cstats[cstats['cluster_name'] == cname].iloc[0]
        wt_row = avg_w.loc[cname]
        color  = CLUSTER_BORDER[cname]
        with col_widget:
            st.markdown(
                f"""<div class="cluster-card" style="border-top: 4px solid {color};">
                <div class="cluster-title">{CLUSTER_ICONS[cname]} {cname.strip()}</div>
                <div style="color:#666; margin-bottom:6px; font-size:12px;">{CLUSTER_LABEL[cname]}</div>
                <b>인원:</b> {int(row['총인원']):,}명 ({row['비중']:.1f}%)<br>
                <b>이탈률:</b> <span style="color:#d32f2f;">{row['이탈률']:.1f}%</span> &nbsp;
                <b>방어율:</b> <span style="color:#388e3c;">{row['방어율']:.1f}%</span><br>
                <b>시청 추이:</b> {wt_row['watch_time(min)_w1']:.0f}분 →
                                  {wt_row['watch_time(min)_w2']:.0f}분 →
                                  {wt_row['watch_time(min)_w3']:.0f}분<br>
                <hr style="margin:6px 0;">
                <span style="font-size:12px;">{CLUSTER_DESC[cname]}</span>
                </div>""",
                unsafe_allow_html=True
            )

    # 나이대 × 군집 이탈률 히트맵
    st.markdown("#### 나이대 × 군집별 이탈률 (%)")
    age_cl = promo_df.groupby(['age_group', 'cluster_name'])['is_churn'].mean().reset_index()
    age_cl.columns = ['나이대', '군집', '이탈률']
    age_cl['이탈률'] = age_cl['이탈률'] * 100
    age_cl['나이대'] = age_cl['나이대'].astype(str) + '대'
    age_pivot = age_cl.pivot(index='나이대', columns='군집', values='이탈률')

    hm_col, bar_col = st.columns([3, 2])
    with hm_col:
        fig_hm = px.imshow(
            age_pivot.round(1),
            text_auto=True,
            color_continuous_scale='RdYlGn_r',
            zmin=75, zmax=95,
            labels={'color': '이탈률(%)'}
        )
        fig_hm.update_layout(height=280, margin=dict(t=10, b=10, l=0, r=0))
        st.plotly_chart(fig_hm, use_container_width=True)

    with bar_col:
        age_total = promo_df.groupby('age_group')['is_churn'].agg(['mean', 'count']).reset_index()
        age_total.columns = ['나이대', '이탈률', '인원']
        age_total['이탈률'] *= 100
        age_total['나이대'] = age_total['나이대'].astype(str) + '대'
        fig_age = px.bar(age_total, x='나이대', y='이탈률',
                         text=age_total['이탈률'].round(1).astype(str) + '%',
                         color='이탈률', color_continuous_scale='RdYlGn_r',
                         range_color=[75, 95])
        fig_age.update_traces(textposition='outside')
        fig_age.update_layout(height=280, margin=dict(t=10, b=10, l=0, r=0),
                               showlegend=False, coloraxis_showscale=False,
                               yaxis=dict(range=[75, 95]))
        st.plotly_chart(fig_age, use_container_width=True)

    # 성별 × 군집 이탈률
    st.markdown("#### 성별 × 군집별 이탈률 (%)")
    gen_cl = promo_df[promo_df['gender_kor'].isin(['여성', '남성'])].groupby(
        ['gender_kor', 'cluster_name'])['is_churn'].mean().reset_index()
    gen_cl.columns = ['성별', '군집', '이탈률']
    gen_cl['이탈률'] *= 100

    gen_col1, gen_col2 = st.columns([3, 2])
    with gen_col1:
        fig_gen = px.bar(gen_cl, x='군집', y='이탈률', color='성별',
                         barmode='group',
                         color_discrete_map={'여성': '#e91e8c', '남성': '#1565c0'},
                         text=gen_cl['이탈률'].round(1).astype(str) + '%')
        fig_gen.update_traces(textposition='outside')
        fig_gen.update_layout(height=280, margin=dict(t=10, b=10, l=0, r=0),
                               yaxis=dict(range=[78, 92]))
        st.plotly_chart(fig_gen, use_container_width=True)

    with gen_col2:
        gender_total = promo_df[promo_df['gender_kor'].isin(['여성','남성'])].groupby(
            'gender_kor').agg(이탈률=('is_churn','mean'), 인원=('USER_KEY','count')).reset_index()
        gender_total['이탈률'] *= 100
        gender_total.columns = ['성별', '이탈률(%)', '인원']
        gender_total['인원'] = gender_total['인원'].apply(lambda x: f"{x:,}명")
        gender_total['이탈률(%)'] = gender_total['이탈률(%)'].round(1)
        st.dataframe(gender_total.set_index('성별').astype(object), use_container_width=True, height=130)
        st.markdown("")
        st.info("**📌 인사이트**\n\n"
                "성별 이탈률(재구매 안 함 비율) 분포를 확인하세요.\n"
                "C0·C3 군집에서 성별 차이가 두드러질 수 있습니다.")

    # 대응 전략 카드
    st.markdown("#### 📋 군집별 핵심 대응 전략")
    s0, s1, s2, s3 = st.columns(4)
    strategies = {
        ' C0 (맛보기형)': {
            'icon': '📬',
            'short': '취향 매칭 온보딩',
            'items': ['① 취향 파악 설문 (3문항)', '② 맞춤 인기작 큐레이션 메일', '③ 첫 시청 완료 보상 쿠폰']
        },
        ' C1 (헤비유저형)': {
            'icon': '🎯',
            'short': '후속 콘텐츠 연결',
            'items': ['① 1주차 시청 완료 후 즉시 알림', '② 동일 장르 시리즈 추천', '③ 한정 타임딜 오퍼']
        },
        ' C2 (후반몰입형)': {
            'icon': '💎',
            'short': 'VIP 전환 유도',
            'items': ['① 독점 콘텐츠 선공개 안내', '② 유료 첫 달 할인 혜택', '③ VIP 등급 혜택 시뮬레이션']
        },
        ' C3 (휴면형)': {
            'icon': '🔔',
            'short': '재활성화 자동화',
            'items': ['① 3일 미접속 시 알림 발송', '② 이전 관심사 기반 추천', '③ 단기 무료 연장 쿠폰']
        }
    }
    for col_widget, cname in zip([s0, s1, s2, s3], col_order):
        s = strategies[cname]
        color = CLUSTER_BORDER[cname]
        with col_widget:
            st.markdown(
                f"""<div class="cluster-card" style="border-top: 4px solid {color};">
                <div class="cluster-title">{s['icon']} {cname.strip()}</div>
                <div style="font-weight:600; margin-bottom:8px; color:#444;">{s['short']}</div>
                {'<br>'.join(f'<span style="font-size:12px;">{i}</span>' for i in s['items'])}
                </div>""",
                unsafe_allow_html=True
            )

# ==========================================
# 4-3. 예측 모델 설정
# ==========================================
elif menu == "⚙️ 예측 모델 설정":
    st.header("⚙️ 예측 모델 설정")
    st.caption("이탈 예측 알고리즘의 파라미터를 조정하고 모델의 신뢰도를 모니터링합니다.")
    st.markdown("---")

    st.subheader("📈 모델 성능 지표 (Model Health)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Model Accuracy", "88.4%", "+0.5%")
    m2.metric("ROC-AUC",        "0.92",  "Stable", delta_color="off")
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
        st.markdown("""
        <div style="position:relative; border-radius:10px; overflow:hidden; margin-top:8px;">
            <div style="filter:blur(2px) grayscale(0.3); pointer-events:none; opacity:0.4; padding:12px 0;">
                <p style="font-size:18px; font-weight:600; margin-bottom:8px;">⚖️ 변수 가중치 조정</p>
                <p style="font-size:14px; color:#555;">주차별 시청 시간 &nbsp;✅&nbsp; 3주차 리텐션 &nbsp;✅&nbsp; 1주차 단독 시청 여부 &nbsp;✅</p>
            </div>
            <div style="
                position:absolute; top:0; left:0; width:100%; height:100%;
                background:rgba(180,180,180,0.72);
                border-radius:10px;
                display:flex; align-items:center; justify-content:center;
                flex-direction:column; gap:6px;
            ">
                <span style="font-size:22px;">🔒</span>
                <span style="font-size:13px; font-weight:700; color:#444;">준비 중인 기능입니다</span>
                <span style="font-size:11px; color:#666;">모델 고도화 후 활성화 예정</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with set_col2:
        st.subheader("🎯 모델 재학습")
        st.text("마지막 학습일: 2021-04-10")
        if st.button("🚀 지금 즉시 모델 재학습 시작", use_container_width=True):
            import time
            with st.spinner("최적화 중..."):
                time.sleep(1)
            st.success("학습 완료!")
        st.markdown("---")
        st.subheader("📂 데이터 익스포트")
        st.button("📥 고위험군 명단 다운로드 (.csv)", use_container_width=True)
