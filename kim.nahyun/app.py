import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime

# ==========================================
# 1. 페이지 설정 및 커스텀 CSS
# ==========================================
st.set_page_config(page_title="OTT 이탈 방어 '골든 타임' 대시보드", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    section[data-testid="stSidebar"] { background-color: #FAFAFA !important; }
    hr { margin: 15px 0 !important; }
    /* Expander 내부 여백 타이트하게 압축 */
    .streamlit-expanderContent { padding-top: 5px !important; padding-bottom: 10px !important; }
    .streamlit-expanderHeader { font-size: 13px !important; color: #555 !important; }
    /* Playbook 버튼 사이 여백 축소 */
    div[data-testid="stButton"] { margin-bottom: -10px !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터 로드 및 전처리 (가상 데이터)
# ==========================================
@st.cache_data
def load_data():
    np.random.seed(42)
    n = 1500
    df = pd.DataFrame({
        'USER_KEY': [f'U{i:05d}' for i in range(n)],
        'gender_kor': np.random.choice(['남성', '여성'], n),
        'age_group': np.random.choice([20, 30, 40, 50], n),
        'plan': np.random.choice(['베이직', '스탠다드', '프리미엄'], n),
        'is_promotion': np.random.choice([0, 1], n, p=[0.3, 0.7]),
        'is_repurchase': np.random.choice([0, 1], n, p=[0.674, 0.326]), 
        'cluster_name': np.random.choice([' C0 (맛보기형)', ' C1 (헤비유저형)', ' C2 (후반몰입형)', ' C3 (휴면형)'], n),
        'churn_score': np.random.uniform(15, 99, n),
        
        # 시청 이력 변수
        'watch_time(min)_w1': np.random.randint(50, 400, n),
        'watch_time(min)_w2': np.random.randint(30, 350, n),
        'watch_time(min)_w3': np.random.randint(10, 300, n),
        'active_ratio': np.random.uniform(0.1, 1, n),
        'watch_ratio_under_5m': np.random.uniform(0, 0.8, n),
        'avg_rewatch_ratio': np.random.uniform(0, 0.4, n),
        'genre_diversity_count': np.random.randint(1, 8, n),
        'max_inactive_gap_days': np.random.randint(1, 15, n),
        'recency': np.random.randint(0, 15, n),
        
        # 플래그 변수
        'is_only_w1': np.random.choice([0, 1], n, p=[0.8, 0.2]),
        'is_w1_over_50pct': np.random.choice([0, 1], n, p=[0.7, 0.3]),
        'is_cold_start_3d': np.random.choice([0, 1], n, p=[0.9, 0.1]),
        'is_only_w2': np.random.choice([0, 1], n, p=[0.95, 0.05]),
        'weekend_watch_ratio': np.random.uniform(0.1, 0.9, n),
        
        # 장르 변수
        'thriller_crime_ratio': np.random.uniform(0.0, 0.6, n),
        'action_adventure_ratio': np.random.uniform(0.0, 0.5, n),
        'romance_ratio': np.random.uniform(0.0, 0.5, n),
        'drama_ratio': np.random.uniform(0.0, 0.7, n)
    })
    
    df['is_churn'] = (df['is_repurchase'] == 0).astype(int)
    
    # [데이터 현실성 보정]
    df['watch_time(min)_w3'] = df['watch_time(min)_w3'].astype(float)
    df.loc[(df['is_promotion'] == 1) & (df['is_churn'] == 1), 'watch_time(min)_w3'] *= 0.15
    df.loc[(df['is_promotion'] == 0), 'watch_time(min)_w3'] = df['watch_time(min)_w2'] * np.random.uniform(0.8, 1.1)
    
    df.loc[df['is_churn'] == 1, 'watch_ratio_under_5m'] += 0.25
    df.loc[df['is_churn'] == 0, 'avg_rewatch_ratio'] += 0.15
    
    df.loc[df['is_churn'] == 1, 'recency'] += np.random.randint(5, 12, size=(df['is_churn'] == 1).sum())
    df.loc[df['is_churn'] == 1, 'max_inactive_gap_days'] += np.random.randint(4, 9, size=(df['is_churn'] == 1).sum())
    
    df.loc[df['cluster_name'] == ' C3 (휴면형)', ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']] = 0
    df['total_watch_time(min)'] = df['watch_time(min)_w1'] + df['watch_time(min)_w2'] + df['watch_time(min)_w3']
    
    df['final_result'] = np.where(df['is_repurchase'] == 1, '🟢 잔존 (재결제 성공)',
                         np.where(np.random.rand(n) < 0.2, '🟡 결제 실패 (비자발적)', '🔴 자발적 해지 (이탈)'))
    df['risk_group'] = np.where(df['churn_score'] > 70, "🔴 고위험군 (이탈)", np.where(df['churn_score'] > 40, "🟡 중위험군", "🟢 안전군 (잔존)"))
    df['가입경로'] = np.where(df['is_promotion'] == 1, '🎟️ 100원 프로모션 유입', '💼 정가 구독 유입')
    
    return df

df = load_data()

if 'action_log' not in st.session_state:
    st.session_state['action_log'] = {}

# ==========================================
# 3. 사이드바
# ==========================================
st.sidebar.title("🛠️ 대시보드 제어 센터")
st.sidebar.markdown("---")
st.sidebar.subheader("📅 분석 코호트 설정")
st.sidebar.markdown("""
<div style="background-color: #FFE0B2; padding: 15px; border-radius: 8px; border-left: 5px solid #FF7A00; color: #333; margin-bottom: 15px;">
    <b>🎯 분석 타임라인:</b><br>3월 1일~15일 가입자 코호트<br>(과거 3주 행동 기반 이탈 요인 도출)
</div>
""", unsafe_allow_html=True)

cohort_option = st.sidebar.radio(
    "👥 분석 대상 코호트 선택",
    ["전체 가입자 보기", "🎟️ 100원 프로모션 가입자만 보기", "💼 정가 구독 가입자만 보기"]
)

if cohort_option == "🎟️ 100원 프로모션 가입자만 보기":
    df_filtered = df[df["is_promotion"] == 1]
elif cohort_option == "💼 정가 구독 가입자만 보기":
    df_filtered = df[df["is_promotion"] == 0]
else:
    df_filtered = df.copy()

st.sidebar.markdown("---")
st.sidebar.caption("v11.0 - CRM Analyst Studio")

TOTAL = len(df_filtered)
CONVERTED = int(df_filtered['is_repurchase'].sum())
CHURNED = int(df_filtered['is_churn'].sum())
CHURN_RATE = (CHURNED / max(TOTAL, 1)) * 100

# ── 공통 마스크 (탭 간 공유) ─────────────────────────────────────────
cv_churn  = df_filtered[df_filtered['is_churn'] == 1]
cv_retain = df_filtered[df_filtered['is_churn'] == 0]
_w1 = df_filtered['watch_time(min)_w1'] > 0
_w2 = df_filtered['watch_time(min)_w2'] > 0
_w3 = df_filtered['watch_time(min)_w3'] > 0
_conv   = df_filtered['is_repurchase'] == 1
_m_none = ~_w1 & ~_w2 & ~_w3
_mx_ac  = (~_m_none) & _conv
_mx_pc  = _m_none    & _conv
_mx_ach = (~_m_none) & ~_conv
_mx_cc  = _m_none    & ~_conv

# ── 7개 세그먼트 — 실제 분석 결과 (하드코딩) ───────────────────────
_seg_table = pd.DataFrame({
    '순위': [1, 2, 3, 4, 5, 6, 7],
    '세그먼트명': [
        '3주차 이탈 임박 고위험군',
        '초기 활성화 약화 고위험군',
        '저활동 고위험군',
        '관심 감소 관찰군',
        '콘텐츠 큐레이션 기반 정가 전환 강화군',
        '안정 재구매 가능군',
        '추가 관찰 필요 잔여군',
    ],
    'segment_id': [
        'high_risk_week3_inactive_or_drop',
        'high_risk_only_w1_or_cold_start_weak',
        'high_risk_low_activity',
        'medium_risk_retention_decay',
        'content_preference_target_candidate',
        'stable_retained_user',
        'general_observation',
    ],
    '인원': [3793, 265, 511, 3195, 6195, 1224, 7896],
    '비중(%)': [16.4, 1.1, 2.2, 13.8, 26.8, 5.3, 34.2],
    '이탈률(%)': [73.2, 71.7, 81.4, 38.8, 10.1, 1.1, 15.9],
    '평균 이탈위험도': [0.733, 0.698, 0.765, 0.358, 0.095, 0.017, 0.169],
    '프로모션 비중(%)': [59.0, 70.6, 60.9, 54.6, 48.5, 34.2, 50.6],
    '위험도': ['🔴 최고위험', '🔴 고위험', '🔴 고위험', '🟠 중위험', '🟢 저위험', '🟢 저위험', '🟡 관찰'],
    '색': ['#c0392b', '#e65100', '#ff7043', '#f9a825', '#388e3c', '#27ae60', '#78909c'],
})

# ── 세그먼트별 시뮬레이션 마스크 (비교 차트용) ──────────────────────
_seg_masks = {
    '3주차 이탈 임박 고위험군':
        df_filtered[(df_filtered['watch_time(min)_w3'] == 0) & (df_filtered['churn_score'] > 60)],
    '초기 활성화 약화 고위험군':
        df_filtered[(df_filtered['is_only_w1'] == 1) | (df_filtered['is_cold_start_3d'] == 1)],
    '저활동 고위험군':
        df_filtered[(df_filtered['active_ratio'] < 0.3) & (df_filtered['churn_score'] > 70)],
    '관심 감소 관찰군':
        df_filtered[(df_filtered['churn_score'] >= 35) & (df_filtered['churn_score'] < 70)],
    '콘텐츠 큐레이션 기반 정가 전환 강화군':
        df_filtered[(df_filtered['genre_diversity_count'] >= 4) & (df_filtered['churn_score'] < 40)],
    '안정 재구매 가능군':
        df_filtered[(df_filtered['churn_score'] < 25) & (df_filtered['is_repurchase'] == 1)],
    '추가 관찰 필요 잔여군':
        df_filtered[(df_filtered['churn_score'] >= 15) & (df_filtered['churn_score'] < 35)],
}
_high_risk_segs = ['3주차 이탈 임박 고위험군', '초기 활성화 약화 고위험군', '저활동 고위험군', '관심 감소 관찰군']
_baseline_seg   = '안정 재구매 가능군'

# ==========================================
# 4. 메인 헤더 및 탭 구성
# ==========================================
def draw_action_playbook(col, border_color, icon, title, desc, btn1, btn2, btn3, prefix):
    with col:
        st.markdown(f"""
        <div style="border-top: 4px solid {border_color}; padding: 12px 15px 10px 15px; background: #fff; border-radius: 5px 5px 0 0; box-shadow: 0 -1px 2px rgba(0,0,0,0.05); margin-bottom: 5px;">
            <div style="font-weight: 700; font-size: 14px; margin-bottom: 5px;">{icon} {title}</div>
            <div style="font-size: 12px; color: #666; line-height: 1.4;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        with st.container():
            b1 = st.button(f"① {btn1}", key=f"pb_{prefix}_1", use_container_width=True)
            b2 = st.button(f"② {btn2}", key=f"pb_{prefix}_2", use_container_width=True)
            b3 = st.button(f"③ {btn3}", key=f"pb_{prefix}_3", use_container_width=True)
            if b1 or b2 or b3:
                st.success("✅ 시나리오 처방 완료!")

st.title("📺 OTT 이탈 방어 및 분석 스튜디오")
st.markdown(f"##### 🚀 **대상 그룹: {cohort_option.split(' ')[0].replace('🎟️', '').replace('💼', '')} 코호트 회고 및 액션 도출**")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📌 [실행] 오늘의 Action Hub", "📊 [진단] 세그먼트 비교 & 다중 처방", "📈 [분석] 이탈 요인 딥다이브 & 흐름도", "🔍 [프로필] 고객 상세 XAI"])

# ==========================================
# [TAB 1] 오늘의 Action Hub & 다중 처방 Playbook
# ==========================================
with tab1:
    col1, col2, col3 = st.columns(3)
    high_risk_cnt = len(df_filtered[df_filtered["churn_score"] >= 70])
    
    with col1: st.metric(label="👥 분석 코호트 전체 모수", value=f"{TOTAL:,} 명", delta="코호트 완료")
    with col2: st.metric(label="🚨 고위험군 (이탈 점수 70점 이상)", value=f"{high_risk_cnt:,} 명", delta=f"전체 비중 {high_risk_cnt/max(TOTAL, 1)*100:.1f}%", delta_color="inverse")
    with col3: st.metric(label="📉 실제 이탈률 (결과)", value=f"{CHURN_RATE:.1f} %", delta=f"{CHURNED:,}명 이탈 발생", delta_color="inverse")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("🔥 Today's Action List (즉각 발송 타겟)")
    st.caption("이탈 징후를 Expander로 펼쳐 근거를 확인하고 즉시 방어 액션을 실행하세요.")

    high_risk_df = df_filtered[df_filtered['churn_score'] >= 70]
    grp1 = high_risk_df[high_risk_df['watch_ratio_under_5m'] > 0.4]
    grp2 = high_risk_df[(high_risk_df['weekend_watch_ratio'] > 0.6) & (high_risk_df['recency'] > 4)]
    grp3 = high_risk_df[high_risk_df['is_only_w1'] == 1]
    grp4 = high_risk_df[high_risk_df['watch_time(min)_w3'] == 0]

    def _mini_bar(labels, values, colors, y_label, fmt="%{text:.1f}"):
        _df = pd.DataFrame({'그룹': labels, y_label: values})
        fig = px.bar(_df, x='그룹', y=y_label, color='그룹',
                     color_discrete_sequence=colors, text=y_label)
        fig.update_traces(texttemplate=fmt, textposition='outside')
        fig.update_layout(height=150, margin=dict(t=5, b=5, l=5, r=5), showlegend=False,
                          yaxis=dict(range=[0, max(values) * 1.45 if max(values) > 0 else 1]))
        return fig

    def mini_grp1(grp):
        if grp.empty: return None
        others = high_risk_df[~high_risk_df.index.isin(grp.index)]
        return _mini_bar(['5분컷 유목민', '기타 고위험'],
                         [grp['watch_ratio_under_5m'].mean()*100, others['watch_ratio_under_5m'].mean()*100],
                         ['#EF553B', '#B0BEC5'], '5분컷 비율(%)', '%{text:.1f}%')

    def mini_grp2(grp):
        if grp.empty: return None
        others = high_risk_df[~high_risk_df.index.isin(grp.index)]
        return _mini_bar(['주말 잠수러', '기타 고위험'],
                         [grp['recency'].mean(), others['recency'].mean()],
                         ['#FECB52', '#B0BEC5'], 'Recency(일)', '%{text:.1f}일')

    def mini_grp3(grp):
        if grp.empty: return None
        vals = [grp['watch_time(min)_w1'].mean(), grp['watch_time(min)_w2'].mean(), grp['watch_time(min)_w3'].mean()]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=['1주차', '2주차', '3주차'], y=vals,
                             marker_color=['#AB63FA', '#D4BBFF', '#EDE4FF'],
                             text=[f"{v:.0f}분" for v in vals], textposition='outside'))
        fig.update_layout(height=150, margin=dict(t=5, b=5, l=5, r=5), showlegend=False,
                          yaxis=dict(range=[0, max(vals)*1.45 if max(vals)>0 else 1]))
        return fig

    def mini_grp4(grp):
        if grp.empty: return None
        vals = [grp['watch_time(min)_w1'].mean(), grp['watch_time(min)_w2'].mean(), grp['watch_time(min)_w3'].mean()]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=['1주차', '2주차', '3주차'], y=vals,
                             marker_color=['#78C1FF', '#FFA07A', '#EF5350'],
                             text=[f"{v:.0f}분" for v in vals], textposition='outside'))
        fig.update_layout(height=150, margin=dict(t=5, b=5, l=5, r=5), showlegend=False,
                          yaxis=dict(range=[0, max(vals)*1.45 if max(vals)>0 else 1]))
        return fig

    action_items = [
        ("grp1", "🔴 **5분 컷 메뉴 유목민**", grp1,
         "📊 이탈 징후 분석",
         "**근거:**\n* 콘텐츠를 **5분 미만으로만 보고 끈 비율이 40% 이상**\n* UI 탐색 실패 → 볼 콘텐츠를 찾지 못하는 상태",
         mini_grp1, "🚀 숏폼 추천 일괄 발송", "act_1"),
        ("grp2", "⏳ **주말 정주행 잠수러**", grp2,
         "📊 이탈 징후 분석",
         "**근거:**\n* 시청 모멘텀의 **60% 이상이 주말에 집중**\n* **평일 미접속 4일 이상** 지속 — 이탈 궤도 진입",
         mini_grp2, "📅 주말 예약 발송", "act_2"),
        ("grp3", "👻 **1주차 체리피커**", grp3,
         "📊 이탈 징후 분석",
         "**근거:**\n* 1주차에만 반짝 시청, 2~3주차 접속 **전무**\n* 프로모션 목적이거나 초기 온보딩 완전 실패",
         mini_grp3, "💬 혜택 만료 알림 발송", "act_3"),
        ("grp4", "📉 **흥미 급감 이탈 직전**", grp4,
         "📊 이탈 징후 분석",
         "**근거:**\n* 1~2주차 대비 **3주차 시청 시간 = 0분**\n* 흥미 완전 소멸, 해지 버튼 직전 초고위험군",
         mini_grp4, "📲 반값 SMS 발송", "act_4"),
    ]

    with st.container(border=True):
        h1, h2, h3, h4 = st.columns([1.5, 1, 2.5, 1.2])
        h1.markdown("**🎯 타겟 세그먼트**"); h2.markdown("**👥 인원**")
        h3.markdown("**🔍 이탈 징후 분석**"); h4.markdown("**⚡ 즉시 발송**")
        st.markdown("<hr style='margin:5px 0 !important;'>", unsafe_allow_html=True)

        for grp_key, title, grp_df, exp_title, exp_body, mini_fn, btn_txt, btn_key in action_items:
            count = len(grp_df)
            r1, r2, r3, r4 = st.columns([1.5, 1, 2.5, 1.2])
            r1.markdown(f"<span style='font-size:14px;'>{title}</span>", unsafe_allow_html=True)
            r2.markdown(f"<span style='font-size:14px; font-weight:bold;'>{count:,} 명</span>", unsafe_allow_html=True)
            with r3.expander(exp_title, expanded=False):
                st.markdown(exp_body)
                fig = mini_fn(grp_df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            if r4.button(btn_txt, key=btn_key, use_container_width=True):
                now = datetime.datetime.now().strftime("%H:%M")
                st.session_state['action_log'][btn_key] = (count, now)
            if btn_key in st.session_state['action_log']:
                cnt_log, time_log = st.session_state['action_log'][btn_key]
                r4.markdown(f"""<div style="background:#e8f5e9; border-left:3px solid #388e3c;
                    padding:5px 8px; border-radius:4px; font-size:11px; margin-top:3px; line-height:1.4;">
                    ✅ {cnt_log:,}명 추출<br>API 통신 성공<br>{time_log} 발송 완료</div>""",
                    unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    _total_targets = len(grp1) + len(grp2) + len(grp3) + len(grp4)
    bc1, bc2 = st.columns([3, 1])
    with bc1:
        st.markdown(f"**🚀 일괄 발송** — 4개 세그먼트 전체 타겟 **{_total_targets:,}명**에게 한 번에 발송합니다.")
        st.caption("개별 발송 상태는 위 Action List에서 확인하세요.")
    with bc2:
        if st.button("📣 전체 일괄 발송", key="bulk_send", use_container_width=True, type="primary"):
            now = datetime.datetime.now().strftime("%H:%M")
            for _bk, _grp in [("act_1", grp1), ("act_2", grp2), ("act_3", grp3), ("act_4", grp4)]:
                st.session_state['action_log'][_bk] = (len(_grp), now)
            st.success(f"✅ {_total_targets:,}명 전체 일괄 발송 완료! ({now})")

# ==========================================
# [TAB 2] 세그먼트 비교 진단 및 다중 처방
# ==========================================
with tab2:
    st.caption("📊 7개 세그먼트 전략적 조망 및 고위험 vs 안정군 비교 분석 · 다중 처방 시나리오")

    # ── Section 1: 7개 세그먼트 종합 조망 ──────────────────────────────
    st.subheader("🗺️ 7개 세그먼트 종합 조망")
    s1a, s1b = st.columns([1, 1.5])

    with s1a:
        _disp = _seg_table[['순위', '세그먼트명', '인원', '이탈률(%)', '위험도']].reset_index(drop=True)
        st.dataframe(_disp, use_container_width=True, height=265, hide_index=True)

    with s1b:
        fig_bub = px.scatter(
            _seg_table,
            x='비중(%)', y='이탈률(%)',
            size='인원',
            color='위험도',
            color_discrete_map={
                '🔴 최고위험': '#c0392b', '🔴 고위험': '#e65100',
                '🟠 중위험': '#f9a825', '🟢 저위험': '#388e3c', '🟡 관찰': '#78909c'
            },
            hover_name='세그먼트명',
            size_max=55,
            title='세그먼트 포지셔닝 맵 (X: 비중, Y: 이탈률, 크기: 인원수)'
        )
        fig_bub.update_layout(height=275, margin=dict(t=35, b=0, l=0, r=0),
                               legend=dict(orientation='h', y=-0.15, font=dict(size=10)))
        st.plotly_chart(fig_bub, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Section 2: 고위험 vs 저위험 대조 분석 ────────────────────────────
    st.subheader("🔬 고위험 vs 안정군 대조 분석")
    _sel_seg = st.selectbox("비교할 고위험 세그먼트 선택:", _high_risk_segs)

    _sel_df  = _seg_masks[_sel_seg]
    _base_df = _seg_masks[_baseline_seg]

    if _sel_df.empty or _base_df.empty:
        st.warning("선택한 세그먼트에 해당하는 데이터가 없습니다. 시뮬레이션 마스크를 확인하세요.")
    else:
        _A = _sel_seg[:7] + '...'
        _B = '안정군'

        # ── KPI 4개 ─────────────────────────────────────────────────────────
        _wt_diff  = _sel_df['total_watch_time(min)'].mean() - _base_df['total_watch_time(min)'].mean()
        _act_diff = (_sel_df['active_ratio'].mean() - _base_df['active_ratio'].mean()) * 100
        ck1, ck2, ck3, ck4 = st.columns(4)
        ck1.metric("고위험군 인원",   f"{len(_sel_df):,}명",  f"이탈률 {_sel_df['is_churn'].mean()*100:.1f}%",  delta_color="inverse")
        ck2.metric("안정군 인원",     f"{len(_base_df):,}명", f"이탈률 {_base_df['is_churn'].mean()*100:.1f}%")
        ck3.metric("총 시청 시간 차이", f"{_wt_diff:.0f}분",  "고위험이 안정군보다 적게 시청",                  delta_color="inverse")
        ck4.metric("활성비율 차이",    f"{_act_diff:.1f}%p",  "고위험이 안정군보다 낮음",                        delta_color="inverse")

        st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

        # ── Row A: 이탈 신호 플래그 | 장르 취향 차이 | 주차 간 증감 ──────────
        cv_rA1, cv_rA2, cv_rA3 = st.columns(3)

        with cv_rA1:
            st.caption("**이탈 신호 플래그 비율 (%)**")
            _flag_info = [
                ('is_only_w1',       '1주차만 시청'),
                ('is_w1_over_50pct', 'W1 시청 50%+'),
                ('is_cold_start_3d', '3일 콜드스타트'),
                ('is_only_w2',       '2주차만 시청'),
            ]
            _flag_rows = [{'지표': lbl, _A: round(_sel_df[col].mean()*100, 1),
                           _B: round(_base_df[col].mean()*100, 1)} for col, lbl in _flag_info]
            _flag_df = pd.DataFrame(_flag_rows)
            fig_flag = go.Figure()
            for _grp, _clr in [(_A, '#c0392b'), (_B, '#52A068')]:
                fig_flag.add_trace(go.Bar(
                    name=_grp, x=_flag_df['지표'].tolist(), y=_flag_df[_grp].tolist(),
                    marker_color=_clr, text=[f'{v}' for v in _flag_df[_grp].tolist()],
                    textposition='outside', textfont=dict(size=10),
                ))
            fig_flag.update_layout(barmode='group', height=310, margin=dict(t=10, b=5, l=0, r=0),
                plot_bgcolor='white', xaxis_title='', yaxis_title='비율 (%)',
                yaxis=dict(gridcolor='#f0f0f0'),
                legend=dict(orientation='h', y=1.08, x=0, font=dict(size=10)))
            st.plotly_chart(fig_flag, use_container_width=True)

        with cv_rA2:
            st.caption(f"**장르 취향 차이 ({_A} − {_B}, %p) · 빨강=고위험이 더 시청**")
            _genre_info = [
                ('thriller_crime_ratio',   '스릴러/범죄'),
                ('action_adventure_ratio', '액션/어드벤처'),
                ('romance_ratio',          '로맨스'),
                ('drama_ratio',            '드라마'),
            ]
            _gdiff_rows = [
                {'장르': lbl,
                 '차이': round((_sel_df[col].mean() - _base_df[col].mean()) * 100, 2)}
                for col, lbl in _genre_info
            ]
            _gdiff_df = pd.DataFrame(_gdiff_rows)
            _gdiff_df['색'] = _gdiff_df['차이'].apply(lambda x: '#c0392b' if x > 0 else '#52A068')
            _gdiff_df = _gdiff_df.sort_values('차이')
            fig_genre = go.Figure(go.Bar(
                x=_gdiff_df['차이'], y=_gdiff_df['장르'], orientation='h',
                marker_color=_gdiff_df['색'].tolist(),
                text=[f'{v:+.1f}%p' for v in _gdiff_df['차이']],
                textposition='outside', textfont=dict(size=10),
            ))
            fig_genre.add_vline(x=0, line_dash='dash', line_color='#888', line_width=1)
            fig_genre.update_layout(height=310, margin=dict(t=10, b=5, l=60, r=45),
                plot_bgcolor='white',
                xaxis=dict(title='차이 (%p)', gridcolor='#f0f0f0'),
                yaxis=dict(title=''))
            st.plotly_chart(fig_genre, use_container_width=True)

        with cv_rA3:
            st.caption("**주차 간 시청 증감 비교 (분) · 고위험은 갈수록 급감**")
            _wdiff_rows = []
            for _lbl, (_wa, _wb) in [('W2 − W1', ('watch_time(min)_w2', 'watch_time(min)_w1')),
                                      ('W3 − W1', ('watch_time(min)_w3', 'watch_time(min)_w1')),
                                      ('W3 − W2', ('watch_time(min)_w3', 'watch_time(min)_w2'))]:
                _wdiff_rows.append({
                    '구간': _lbl,
                    _A: round(_sel_df[_wa].mean()  - _sel_df[_wb].mean(),  1),
                    _B: round(_base_df[_wa].mean() - _base_df[_wb].mean(), 1),
                })
            _wdiff_melt = pd.DataFrame(_wdiff_rows).melt(id_vars='구간', var_name='구분', value_name='증감(분)')
            _wdiff_abs  = max(_wdiff_melt['증감(분)'].abs().max(), 1)
            fig_wdiff = px.bar(_wdiff_melt, x='구간', y='증감(분)', color='구분', barmode='group',
                color_discrete_map={_A: '#c0392b', _B: '#52A068'}, text='증감(분)')
            fig_wdiff.update_traces(textposition='outside', textfont_size=10)
            fig_wdiff.add_hline(y=0, line_color='#333', line_width=1.2)
            fig_wdiff.update_layout(height=310, margin=dict(t=10, b=5, l=0, r=0),
                plot_bgcolor='white', xaxis_title='', yaxis_title='평균 증감 (분)',
                yaxis=dict(gridcolor='#f0f0f0', range=[-_wdiff_abs*1.4, _wdiff_abs*1.4]),
                legend=dict(orientation='h', y=1.08, x=0, font=dict(size=10)))
            st.plotly_chart(fig_wdiff, use_container_width=True)

        st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

        # ── Row B: 주차별 추이 | 시청 습관 지표 | 장르 다양성 & Gap ─────────
        cv_rB1, cv_rB2, cv_rB3 = st.columns([3, 4.5, 2])

        with cv_rB1:
            st.caption("**주차별 시청 패턴 추이 — 고위험은 W2·W3로 갈수록 급감**")
            _line_rows = []
            for _g, _dfl in [(_A, _sel_df), (_B, _base_df)]:
                for _w, _c in zip(['1주차', '2주차', '3주차'],
                                  ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']):
                    _line_rows.append({'구분': _g, '주차': _w, '평균 시청(분)': round(_dfl[_c].mean(), 1)})
            _line_df = pd.DataFrame(_line_rows)
            fig_line = px.line(_line_df, x='주차', y='평균 시청(분)', color='구분',
                markers=True, text='평균 시청(분)',
                color_discrete_map={_A: '#c0392b', _B: '#52A068'})
            fig_line.update_traces(textposition='top center', textfont_size=11, line_width=2.5, marker_size=9)
            fig_line.update_layout(height=300, margin=dict(t=20, b=5, l=0, r=0),
                plot_bgcolor='white', xaxis_title='',
                yaxis=dict(gridcolor='#f0f0f0', title='평균 시청 시간 (분)',
                           range=[0, max(_line_df['평균 시청(분)'].max(), 1) * 1.3]),
                legend=dict(orientation='h', y=1.08, x=0, font=dict(size=11)))
            st.plotly_chart(fig_line, use_container_width=True)

        with cv_rB2:
            st.caption("**시청 습관 지표 비교 (%) — 고위험은 단타·집중형 시청 패턴**")
            _habit_info = [
                ('active_ratio',         '활성화\n비율'),
                ('watch_ratio_under_5m', '5분 미만\n시청'),
                ('avg_rewatch_ratio',    '재시청\n비율'),
            ]
            _habit_rows = [{'지표': lbl, _A: round(_sel_df[col].mean()*100, 1),
                            _B: round(_base_df[col].mean()*100, 1)} for col, lbl in _habit_info]
            _habit_melt = pd.DataFrame(_habit_rows).melt(id_vars='지표', var_name='구분', value_name='값(%)')
            fig_habit = px.bar(_habit_melt, x='지표', y='값(%)', color='구분', barmode='group',
                color_discrete_map={_A: '#c0392b', _B: '#52A068'}, text='값(%)')
            fig_habit.update_traces(textposition='outside', textfont_size=10)
            fig_habit.update_layout(height=300, margin=dict(t=10, b=5, l=0, r=0),
                plot_bgcolor='white', xaxis_title='', yaxis_title='비율 (%)',
                yaxis=dict(gridcolor='#f0f0f0', range=[0, max(_habit_melt['값(%)'].max(), 1)*1.35]),
                legend=dict(orientation='h', y=1.08, x=0, font=dict(size=11)))
            st.plotly_chart(fig_habit, use_container_width=True)

        with cv_rB3:
            st.caption("**장르 다양성 · 최대 미접속 Gap 비교**")
            _div_rows = [{'구분': _g,
                          '장르 다양성(개)': round(_dfl['genre_diversity_count'].mean(), 1),
                          'Gap(일)':         round(_dfl['max_inactive_gap_days'].mean(), 1)}
                         for _g, _dfl in [(_A, _sel_df), (_B, _base_df)]]
            _div_melt = pd.DataFrame(_div_rows).melt(id_vars='구분', var_name='지표', value_name='값')
            fig_div = px.bar(_div_melt, x='지표', y='값', color='구분', barmode='group',
                color_discrete_map={_A: '#c0392b', _B: '#52A068'}, text='값')
            fig_div.update_traces(textposition='outside', textfont_size=11)
            fig_div.update_layout(height=300, margin=dict(t=10, b=5, l=0, r=0),
                plot_bgcolor='white', xaxis_title='', yaxis_title='평균',
                yaxis=dict(gridcolor='#f0f0f0', range=[0, max(_div_melt['값'].max(), 1)*1.35]),
                legend=dict(orientation='h', y=1.08, x=0, font=dict(size=10)))
            st.plotly_chart(fig_div, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Section 3: Playbook ───────────────────────────────────────────────
    st.subheader("📝 고위험군 타겟별 다중 처방 제어 센터 (Action Playbook)")
    st.caption("세그먼트별로 분화된 CRM 시나리오 액션을 즉시 실행할 수 있는 컨트롤 패널입니다.")
    play1, play2, play3, play4 = st.columns(4)
    draw_action_playbook(play1, "#EF553B", "🔴", "5분 컷 메뉴 유목민",   "탐색 피로도를 즉각적으로 낮추고 빠른 시청 경험을 유도합니다.",  "장르 개인화 3픽 푸시",  "신작 하이라이트 숏폼",   "탐색 유도 무료 체험권",  "t2_c0")
    draw_action_playbook(play2, "#FECB52", "⏳", "주말 정주행 잠수러",   "평일 마케팅을 배제하고 시청 모멘텀을 주말에 집중시킵니다.",     "금요일 18시 신작 알림", "주말 한정 시간제 쿠폰",  "주말 정주행 챌린지",     "t2_c1")
    draw_action_playbook(play3, "#AB63FA", "👻", "1주차 단기 체리피커",  "가입 혜택이 종료되기 전에 강력한 락인 요소를 꽂아넣습니다.",    "만료 D-3 리마인드 톡",  "유사 명작 큐레이션",     "1개월 연장 방어 쿠폰",   "t2_c2")
    draw_action_playbook(play4, "#19D3F3", "📉", "흥미 급감 이탈 직전",  "미접속 상태를 끊고 서비스의 가치를 다시 각인시켜야 합니다.",     "미접속 즉각 리마인드",  "VIP 승급 시뮬레이션",    "고객센터 아웃바운드 Call","t2_c3")

# ==========================================
# [TAB 3] 이탈 요인 딥다이브 & 흐름도 (v12.5 고밀도)
# ==========================================
with tab3:
    st.caption("📊 타겟팅의 객관적 근거를 제공합니다. 매트릭스와 심층 비교를 통해 인사이트를 발굴하세요.")

    H = 210
    comp_ac  = df_filtered[_mx_ac]
    comp_ach = df_filtered[_mx_ach]

    # ── Row 1: 시청 추이 + 퍼널 ──────────────────────────────────────────
    r1a, r1b = st.columns([3, 2])
    with r1a:
        _tcols = ['watch_time(min)_w1', 'watch_time(min)_w2', 'watch_time(min)_w3']
        _wks   = ['1주차', '2주차', '3주차']
        seg_opt = st.selectbox(
            "분석 기준",
            ["🔴 이탈 vs 잔존 대조", "✨ 가입 경로별 (프로모션 vs 정가)", "📋 요금제별 (플랜 기준)"],
            label_visibility="collapsed"
        )
        fig_tr = go.Figure()
        if seg_opt == "🔴 이탈 vs 잔존 대조":
            fig_tr.add_trace(go.Scatter(x=_wks, y=[cv_churn[c].mean() for c in _tcols],
                                        name='🔴 이탈군', mode='lines+markers',
                                        line=dict(color='#c0392b', width=3), marker=dict(size=9)))
            fig_tr.add_trace(go.Scatter(x=_wks, y=[cv_retain[c].mean() for c in _tcols],
                                        name='🟢 잔존군', mode='lines+markers',
                                        line=dict(color='#388e3c', width=3), marker=dict(size=9)))
        elif seg_opt == "✨ 가입 경로별 (프로모션 vs 정가)":
            for path, color in [('🎟️ 100원 프로모션 유입', '#FB8C00'), ('💼 정가 구독 유입', '#1E88E5')]:
                _sub = df[df['가입경로'] == path]
                fig_tr.add_trace(go.Scatter(x=_wks, y=[_sub[c].mean() for c in _tcols],
                                            name=path, mode='lines+markers',
                                            line=dict(color=color, width=3), marker=dict(size=9)))
        else:
            _plan_colors = {'베이직': '#78909c', '스탠다드': '#AB63FA', '프리미엄': '#19D3F3'}
            for plan, color in _plan_colors.items():
                _sub = df_filtered[df_filtered['plan'] == plan]
                fig_tr.add_trace(go.Scatter(x=_wks, y=[_sub[c].mean() for c in _tcols],
                                            name=plan, mode='lines+markers',
                                            line=dict(color=color, width=3), marker=dict(size=9)))
        fig_tr.update_layout(height=H, margin=dict(t=5, b=0, l=0, r=0),
                              legend=dict(orientation='h', y=1.08, x=0),
                              yaxis_title="평균 시청 시간(분)")
        st.plotly_chart(fig_tr, use_container_width=True)

    with r1b:
        st.caption("**이탈 소거 깔대기 (시계열 기준)**")
        _churn_f = df_filtered['is_repurchase'] == 0
        _f_w1 = int(((df_filtered['is_only_w1'] == 1) & _churn_f).sum())
        _f_w2 = int(((df_filtered['is_only_w2'] == 1) & _churn_f).sum())
        _f_nw = int((_m_none & _churn_f).sum())
        s1, s2 = TOTAL, TOTAL - _f_w1
        s3, s4, s5 = s2 - _f_w2, s2 - _f_w2 - _f_nw, CONVERTED
        fig_fn = go.Figure(go.Funnel(
            y=['전체 가입자', '1주차 이탈 소거', '2주차 이탈 소거', '미시청 소거', '최종 전환'],
            x=[s1, s2, s3, s4, s5],
            textinfo="value+percent initial",
            marker=dict(color=['#78909c', '#ff8a65', '#ffa726', '#ef5350', '#388e3c'])
        ))
        fig_fn.update_layout(height=H, margin=dict(t=5, b=0, l=5, r=5))
        st.plotly_chart(fig_fn, use_container_width=True)

    # ── Row 2: 참여-전환 매트릭스 + 능동유저 심층 대조 ──────────────────
    r2a, r2b = st.columns([1, 1.6])
    with r2a:
        st.caption("**📋 시청 참여 × 전환 매트릭스**")
        mc1, mc2 = st.columns(2)
        mc3, mc4 = st.columns(2)
        def _mx_card(col, icon, title, desc, mask, border, bg):
            cnt = int(mask.sum())
            col.markdown(f"""
            <div style="background:{bg}; border-left:4px solid {border}; padding:10px 12px;
                border-radius:6px; margin-bottom:6px;">
                <div style="font-weight:700; font-size:13px;">{icon} {title}</div>
                <div style="font-size:10px; color:#666; margin:2px 0 4px;">{desc}</div>
                <div style="font-size:18px; font-weight:800; color:{border}; line-height:1.1;">{cnt:,}
                  <span style="font-size:10px; font-weight:400; color:#888;">명<br>({cnt/max(TOTAL,1)*100:.1f}%)</span>
                </div>
            </div>""", unsafe_allow_html=True)
        _mx_card(mc1, '🟢', '능동 전환', '시청O·결제O', _mx_ac,  '#388e3c', '#e8f5e9')
        _mx_card(mc2, '🟡', '수동 전환', '시청X·결제O', _mx_pc,  '#f9a825', '#fff8e1')
        _mx_card(mc3, '🟠', '능동 이탈', '시청O·결제X', _mx_ach, '#e65100', '#fff3e0')
        _mx_card(mc4, '🔴', '완전 이탈', '시청X·결제X', _mx_cc,  '#c0392b', '#ffebee')
        st.markdown(
            f"<div style='font-size:11px; color:#888; margin-top:4px; line-height:1.5;'>"
            f"💡 수동 전환자 <b>{int(_mx_pc.sum()):,}명</b> — 시청 없이 재결제.<br>"
            f"자동결제 의존 → 다음 주기 폭탄 이탈 위험</div>",
            unsafe_allow_html=True)

    with r2b:
        st.caption("**🔍 능동 유저 심층 대조 — 시청했는데 왜 결제 안 했나?**")
        ca1, ca2, ca3 = st.columns(3)
        with ca1:
            fig_ca1 = go.Figure()
            fig_ca1.add_trace(go.Bar(name='전환', x=['W1','W2','W3'],
                                     y=[comp_ac[f'watch_time(min)_w{w}'].mean() for w in [1,2,3]],
                                     marker_color='#388e3c'))
            fig_ca1.add_trace(go.Bar(name='이탈', x=['W1','W2','W3'],
                                     y=[comp_ach[f'watch_time(min)_w{w}'].mean() for w in [1,2,3]],
                                     marker_color='#e65100'))
            fig_ca1.update_layout(barmode='group', height=H, margin=dict(t=22, b=0, l=0, r=0),
                                   legend=dict(orientation='h', y=1.1, font=dict(size=10)),
                                   title=dict(text='시청 유지력(분)', font=dict(size=11), y=0.99))
            st.plotly_chart(fig_ca1, use_container_width=True)
        with ca2:
            _fd = pd.DataFrame({'그룹': ['전환', '이탈'],
                                '5분컷(%)': [comp_ac['watch_ratio_under_5m'].mean()*100,
                                            comp_ach['watch_ratio_under_5m'].mean()*100]})
            fig_ca2 = px.bar(_fd, x='그룹', y='5분컷(%)', color='그룹',
                             color_discrete_map={'전환':'#388e3c','이탈':'#e65100'}, text='5분컷(%)')
            fig_ca2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_ca2.update_layout(height=H, margin=dict(t=22, b=0, l=0, r=0), showlegend=False,
                                   title=dict(text='5분컷 실패율', font=dict(size=11), y=0.99),
                                   yaxis=dict(range=[0, _fd['5분컷(%)'].max()*1.45]))
            st.plotly_chart(fig_ca2, use_container_width=True)
        with ca3:
            _dd = pd.DataFrame({'그룹': ['전환', '이탈'],
                                '장르 수': [comp_ac['genre_diversity_count'].mean(),
                                           comp_ach['genre_diversity_count'].mean()]})
            fig_ca3 = px.bar(_dd, x='그룹', y='장르 수', color='그룹',
                             color_discrete_map={'전환':'#388e3c','이탈':'#e65100'}, text='장르 수')
            fig_ca3.update_traces(texttemplate='%{text:.1f}개', textposition='outside')
            fig_ca3.update_layout(height=H, margin=dict(t=22, b=0, l=0, r=0), showlegend=False,
                                   title=dict(text='장르 다양성', font=dict(size=11), y=0.99),
                                   yaxis=dict(range=[0, _dd['장르 수'].max()*1.45]))
            st.plotly_chart(fig_ca3, use_container_width=True)

    # ── Row 3: 증거물 4종 (4열 2x2 그리드) ──────────────────────────────
    st.caption("**📊 이탈 vs 잔존 고객 행동 증거 4종**")
    g1, g2, g3, g4 = st.columns(4)

    with g1:
        _flag_info = [('is_only_w1','1주차만'),('is_cold_start_3d','3일콜드스타트'),('is_only_w2','2주차만')]
        _flag_df = pd.DataFrame(
            [{'지표':l,'이탈':round(cv_churn[c].mean()*100,1),'잔존':round(cv_retain[c].mean()*100,1)}
             for c, l in _flag_info]
        ).melt(id_vars='지표', var_name='그룹', value_name='비율(%)')
        fig_g1 = px.bar(_flag_df, x='지표', y='비율(%)', color='그룹', barmode='group',
                        color_discrete_map={'이탈':'#c0392b','잔존':'#52A068'}, text='비율(%)')
        fig_g1.update_traces(textposition='outside', textfont_size=9)
        fig_g1.update_layout(height=H, margin=dict(t=22, b=0, l=0, r=0),
                              legend=dict(orientation='h', y=1.1, x=0, font=dict(size=9)),
                              title=dict(text='이탈 신호 플래그(%)', font=dict(size=11), y=0.99),
                              yaxis=dict(range=[0, _flag_df['비율(%)'].max()*1.4]))
        st.plotly_chart(fig_g1, use_container_width=True)

    with g2:
        _habit_info = [('active_ratio','활성화'),('watch_ratio_under_5m','5분컷'),('avg_rewatch_ratio','재시청')]
        _habit_df = pd.DataFrame(
            [{'지표':l,'이탈':round(cv_churn[c].mean()*100,1),'잔존':round(cv_retain[c].mean()*100,1)}
             for c, l in _habit_info]
        ).melt(id_vars='지표', var_name='그룹', value_name='비율(%)')
        fig_g2 = px.bar(_habit_df, x='지표', y='비율(%)', color='그룹', barmode='group',
                        color_discrete_map={'이탈':'#c0392b','잔존':'#52A068'}, text='비율(%)')
        fig_g2.update_traces(textposition='outside', textfont_size=9)
        fig_g2.update_layout(height=H, margin=dict(t=22, b=0, l=0, r=0),
                              legend=dict(orientation='h', y=1.1, x=0, font=dict(size=9)),
                              title=dict(text='시청 습관 지표(%)', font=dict(size=11), y=0.99),
                              yaxis=dict(range=[0, _habit_df['비율(%)'].max()*1.4]))
        st.plotly_chart(fig_g2, use_container_width=True)

    with g3:
        _rg_df = pd.DataFrame({
            '지표': ['Recency(일)', 'Gap(최대미접속)'],
            '이탈': [cv_churn['recency'].mean(), cv_churn['max_inactive_gap_days'].mean()],
            '잔존': [cv_retain['recency'].mean(), cv_retain['max_inactive_gap_days'].mean()]
        }).melt(id_vars='지표', var_name='그룹', value_name='일수')
        fig_g3 = px.bar(_rg_df, x='지표', y='일수', color='그룹', barmode='group',
                        color_discrete_map={'이탈':'#c0392b','잔존':'#52A068'}, text='일수')
        fig_g3.update_traces(texttemplate='%{text:.1f}일', textposition='outside', textfont_size=9)
        fig_g3.update_layout(height=H, margin=dict(t=22, b=0, l=0, r=0),
                              legend=dict(orientation='h', y=1.1, x=0, font=dict(size=9)),
                              title=dict(text='Recency & Gap', font=dict(size=11), y=0.99),
                              yaxis=dict(range=[0, _rg_df['일수'].max()*1.4]))
        st.plotly_chart(fig_g3, use_container_width=True)

    with g4:
        g_info = [('thriller_crime_ratio','스릴러'),('action_adventure_ratio','액션'),
                  ('romance_ratio','로맨스'),('drama_ratio','드라마')]
        g_df = pd.DataFrame(
            [{'장르':l, '차이':(cv_churn[c].mean()-cv_retain[c].mean())*100,
              '색':'#c0392b' if (cv_churn[c].mean()-cv_retain[c].mean())>0 else '#52A068'}
             for c, l in g_info]
        ).sort_values('차이')
        fig_g4 = px.bar(g_df, x='차이', y='장르', orientation='h',
                        color='장르', color_discrete_sequence=g_df['색'])
        fig_g4.update_layout(height=H, showlegend=False, xaxis_title="%p",
                              margin=dict(t=22, b=0, l=0, r=0),
                              title=dict(text='장르 취향 차이(%p)', font=dict(size=11), y=0.99))
        fig_g4.add_vline(x=0, line_dash='dash', line_color='#888')
        st.plotly_chart(fig_g4, use_container_width=True)

    # ── Row 4: Sankey (전체 폭, 최소 높이) ──────────────────────────────
    st.caption("**🌊 코호트 저니 흐름 — 유입 경로 ➔ 3주차 핵심 행동 ➔ 최종 결제 상태**")
    _sk = df_filtered.copy()
    _sk['source_node']   = '👥 전체 가입자'
    _sk['inflow_node']   = _sk['가입경로']
    _sk['behavior_node'] = np.where(_sk['watch_ratio_under_5m'] > 0.4, '메뉴 유목민 (5분컷)',
                           np.where(_sk['is_only_w1'] == 1, '1주차 단기 체리피커',
                           np.where(_sk['watch_time(min)_w3'] == 0, '3주차 시청 단절', '정상 및 지속 시청군')))
    _sk['final_node']    = _sk['final_result']
    lk1 = _sk.groupby(['source_node',  'inflow_node'  ]).size().reset_index(name='value')
    lk2 = _sk.groupby(['inflow_node',  'behavior_node']).size().reset_index(name='value')
    lk3 = _sk.groupby(['behavior_node','final_node'   ]).size().reset_index(name='value')
    lk1.columns = lk2.columns = lk3.columns = ['source', 'target', 'value']
    s_df = pd.concat([lk1, lk2, lk3])
    nodes = list(pd.unique(s_df[['source', 'target']].values.ravel('K')))
    n_map = {nd: i for i, nd in enumerate(nodes)}
    node_clrs = []
    for n in nodes:
        if '해지'    in n: node_clrs.append('#E53935')
        elif '결제 실패' in n: node_clrs.append('#FDD835')
        elif '잔존'   in n: node_clrs.append('#43A047')
        elif '프로모션' in n: node_clrs.append('#FB8C00')
        elif '정가'   in n: node_clrs.append('#1E88E5')
        else: node_clrs.append('#B0BEC5')
    fig_sk = go.Figure(go.Sankey(
        node=dict(pad=10, thickness=15, label=nodes, color=node_clrs),
        link=dict(source=[n_map[s] for s in s_df['source']],
                  target=[n_map[t] for t in s_df['target']],
                  value=s_df['value'], color=['rgba(200,200,200,0.3)']*len(s_df))
    ))
    fig_sk.update_layout(height=220, margin=dict(t=0, b=0, l=10, r=10))
    st.plotly_chart(fig_sk, use_container_width=True)

# ==========================================
# [TAB 4] 고객 상세 프로필 (Local XAI 유지)
# ==========================================
with tab4:
    st.subheader("🔍 개별 고객 행동 변수 검사 및 Local XAI")
    uid_list = df_filtered['USER_KEY'].tolist()
    target_uid = st.selectbox("분석할 유저 키 선택:", uid_list)
    
    if target_uid:
        u_row = df_filtered[df_filtered['USER_KEY'] == target_uid].iloc[0]
        c_sub = df_filtered[df_filtered['cluster_name'] == u_row['cluster_name']]
        
        x_c1, x_c2 = st.columns([1, 2])
        with x_c1:
            st.markdown(f"### 유저 ID: `{target_uid}`")
            st.metric("이탈 예측 점수", f"{u_row['churn_score']:.1f} 점")
            st.markdown(f"""
            - **성별/연령:** {u_row['gender_kor']} / {u_row['age_group']}대
            - **가입 경로:** {u_row['가입경로']}
            - **최종 결과:** {u_row['final_result']}
            """)
        with x_c2:
            st.caption("**유저 지표 vs 소속 군집 평균 편차 (빨간색이 위험 신호)**")
            FEAT_COLS = {'1주차 시청(분)': 'watch_time(min)_w1', '3주차 시청(분)': 'watch_time(min)_w3', '5분 미만 비율': 'watch_ratio_under_5m'}
            f_names, devs, clrs = [], [], []
            for lbl, col in FEAT_COLS.items():
                u_v = float(u_row[col])
                c_m = float(c_sub[col].mean())
                dev = (u_v - c_m) / (c_m + 1e-9)
                f_names.append(lbl)
                devs.append(dev)
                clrs.append('#EA002C' if (dev > 0 if col == 'watch_ratio_under_5m' else dev < 0) else '#388e3c')
                
            fig_xai = go.Figure(go.Bar(x=devs, y=f_names, orientation='h', marker_color=clrs, text=[f"{v:+.1%}" for v in devs], textposition='outside'))
            fig_xai.update_layout(height=220, margin=dict(t=10, b=10, l=10, r=50), xaxis=dict(tickformat='.0%'))
            fig_xai.add_vline(x=0, line_color='#aaa')
            st.plotly_chart(fig_xai, use_container_width=True)