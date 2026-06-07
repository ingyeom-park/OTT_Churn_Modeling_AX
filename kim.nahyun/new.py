import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import html as _html
import re
import sys
from pathlib import Path

_AGENT_DIR = Path(__file__).parent / "에이전트"
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

# ══════════════════════════════════════════════════════════════════════════════
# 1. 페이지 설정 & CSS
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="OTT 이탈 방어 대시보드",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; padding-left: 20% !important; padding-right: 20% !important; }
[data-testid="stSidebar"] { display: none; }
hr { margin: 12px 0 !important; }
.streamlit-expanderHeader { font-size: 13px !important; color: #555 !important; }

/* KPI 카드 */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 16px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
/* 탭 */
[data-testid="stTabs"] button {
    font-size: 14px !important;
    font-weight: 600 !important;
}
/* 시사점 박스 공통 */
.insight-box {
    background: #f1f5f9;
    border-radius: 8px;
    padding: 16px 20px;
    font-size: 14px;
    line-height: 1.8;
    color: #1a1a1a;
}
/* 처방 카드 */
.rx-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 14px;
    height: 100%;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
/* 세그먼트 처방 대응 버튼 폰트 색/크기 */
[data-testid="baseButton-secondary"] p,
[data-testid="baseButton-secondary"] div,
[data-testid="baseButton-secondary"] span,
[data-testid="baseButton-secondary"] {
    color: #94a3b8 !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    box-shadow: 0 2px 8px rgba(0,0,0,0.07) !important;
    border-color: #e2e8f0 !important;
}
.stButton > button {
    font-size: 11px !important;
}
.stButton > button p,
.stButton > button div,
.stButton > button span {
    font-size: 11px !important;
}
div.stButton button p {
    font-size: 11px !important;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 2. 헬퍼 함수
# ══════════════════════════════════════════════════════════════════════════════
def strip_md(text: str) -> str:
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\*{1,3}([^*\n]+)\*{1,3}", r"\1", text)
    text = re.sub(r"^[\s]*[-*+]\s+", "• ", text, flags=re.MULTILINE)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_segment(w12: float, w3: float, fivecut: float = 0.0) -> str:
    early_stable = (w12 >= 119)
    if early_stable:
        if w3 >= 141: return "S1 유지보호"
        elif w3 > 0:  return "S2 이용약화"
        else:         return "S3 초기관심"
    else:
        if w3 >= 141: return "S4 늦은활성"
        elif w3 > 0:  return "S5 저관여"
        else:         return "S6 휴면군"


def hex_to_rgba(hex_color: str, alpha: float = 0.15) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def top_genre(row) -> str:
    genre_cols = {
        "drama":    "drama_ratio",
        "thriller": "thriller_crime_ratio",
        "action":   "action_adventure_ratio",
        "romance":  "romance_ratio",
    }
    vals = {g: float(row.get(c, 0)) for g, c in genre_cols.items()}
    return max(vals, key=vals.get) if max(vals.values()) > 0 else "drama"


SEG_META = {
    "S1 유지보호": {
        "risk": "🟢 저위험",   "color": "#27ae60",
        "rx":   "관련 장르 신작 알림 · 개인화 큐레이션 · 낮은 빈도 안내",
        "action": "관련 장르 신작 알림 · 개인화 큐레이션",
        "feat": "초기 소비형성·후반활성형 · 이탈률 7.45% 최저 · 과발송·위기감 조성·무차별 할인 전면 금지",
    },
    "S2 이용약화": {
        "risk": "🟠 중위험",   "color": "#f9a825",
        "rx":   "시청작 후속 추천 · 이어보기 큐레이션 · 주말 재방문 유도",
        "action": "후속 추천 · 이어보기 즉시 큐레이션",
        "feat": "초기 소비형성·후반약화형 · 이탈률 23.29% · 3주차 이용 신호 약화 회복 필요 · 온보딩 재노출·무관련 인기작 일괄 푸시 금지",
    },
    "S3 초기관심": {
        "risk": "🔴 고위험",   "color": "#e65100",
        "rx":   "과거 시청 자산 기반 재활성화 · 이어보기 · 공백 리마인드",
        "action": "과거 시청작 기반 재활성화 · 2단계 전환 파이프라인",
        "feat": "초기 소비형성·후반휴면형 · 이탈률 38.54% 고위험 · 초반 시청 데이터 자산 존재 · 즉시 정가 할인 남발·온보딩 재노출 금지",
    },
    "S4 늦은활성": {
        "risk": "🟢 저위험",   "color": "#388e3c",
        "rx":   "최근 몰입작 연관 추천 · 루틴 강화 타겟팅 · 활성 흐름 보호",
        "action": "활성 흐름 보호 · 루틴 강화 타겟팅",
        "feat": "초기 소비미형성·후반활성형 · 이탈률 8.03% 우수 · 3주차 뒤늦게 몰입 시작 · 재온보딩 팝업·불필요한 과도 할인 금지",
    },
    "S5 저관여": {
        "risk": "🟠 중위험",   "color": "#FB8C00",
        "rx":   "낮은 장벽 콘텐츠 · 제한적 큐레이션 · 관심사 재선택",
        "action": "짧게 시작 가능한 콘텐츠 탐색 유도",
        "feat": "초기 소비미형성·후반약화형 · 이탈률 27.41% · 전체 이탈자 19.6% 차지 대규모 집단 · 수십 개 무차별 나열·즉시 고액 보상 금지",
    },
    "S6 휴면군": {
        "risk": "🔴 최고위험", "color": "#c0392b",
        "rx":   "Sub-Group A: 첫 재생 장벽 제거 / B: 접촉 단서 소수 큐레이션",
        "action": "내부 상태 정밀 라우팅 · 첫 재생 장벽 낮추기",
        "feat": "초기 소비미형성·후반휴면형 · 이탈률 50.47% 최고위험 · 전체 이탈 손실 37.5% 차지 · A(무시청)/B(저소비) 정밀 라우팅 필수 · 전원 무조건 할인 금지",
    },
}
# S1 → S6 숫자 순 (바차트 y축은 아래→위이므로 역순)
SEG_ORDER = ["S6 휴면군", "S5 저관여", "S4 늦은활성", "S3 초기관심", "S2 이용약화", "S1 유지보호"]

SEG_ACTIONS = {
    "S6 휴면군": {
        
        "btns_promo": [
            "① [A] 첫 재생 장벽 제거 · 화제작 1화 무료 시청 유도",
            "② [A] 장르 선택형 온보딩 재실행",
            "③ [B] 접촉 단서 기반 소수 큐레이션 (저소비형)",
        ],
        "btns_nonpromo": [
            "① [A] 첫 재생 장벽 제거 · 화제작 1화 무료 시청 유도",
            "② [A] 장르 선택형 온보딩 재실행",
            "③ [B] 접촉 단서 기반 소수 큐레이션 (저소비형)",
        ],
        "promo_overlay": "🎟️ 프로모션 오버레이 — 저비용 메시지 우선 필터: 체리피커 위험이 높은 집단이므로 즉시 고비용 쿠폰 지급 금지. 저비용 콘텐츠 알림에 클릭 반응 후 앱에 진입한 유저에게만 조건부 갱신 혜택 부여.",
        "prefix": "s6",
    },
    "S3 초기관심": {
       
        "btns_promo": [
            "① 과거 시청 자산 기반 유사 신작 추천",
            "② 미완수 이력 이어보기 유도 (클라이맥스 요약 연동)",
            "③ 공백 리마인드 메시지 (마지막 시청 후 신작 안내)",
        ],
        "btns_nonpromo": [
            "① 과거 시청 자산 기반 유사 신작 추천",
            "② 미완수 이력 이어보기 유도 (클라이맥스 요약 연동)",
            "③ 공백 리마인드 메시지 (마지막 시청 후 신작 안내)",
        ],
        "promo_overlay": "🎟️ 프로모션 오버레이 — 2단계 전환 파이프라인: 다이렉트 결제 유도는 실패율이 높으므로, 앱 진입 및 1화 시청 회복을 1차 확인 후에만 정가 전환 조건부 혜택 팝업 노출.",
        "prefix": "s3",
    },
    "S5 저관여": {
       
        "btns_promo": [
            "① 낮은 진입 장벽 콘텐츠 배치 (단편·예능 숏폼 중심)",
            "② 스친 장르 기반 제한적 킬러 콘텐츠 노출",
            "③ 관심사 재선택 팝업 · 홈 화면 장르 재구성",
        ],
        "btns_nonpromo": [
            "① 낮은 진입 장벽 콘텐츠 배치 (단편·예능 숏폼 중심)",
            "② 스친 장르 기반 제한적 킬러 콘텐츠 노출",
            "③ 관심사 재선택 팝업 · 홈 화면 장르 재구성",
        ],
        "promo_overlay": "🎟️ 프로모션 오버레이 — 시청 도달 연계 실험: 킬러 콘텐츠 1화 완주 등 최소 유효 시청 반응 감지 직후에만 후속 정가 전환 프로모션 분기 실행.",
        "prefix": "s5",
    },
    "S2 이용약화": {
        
        "btns_promo": [
            "① 시청작 후속 추천 알림 · 유사 장르 신작 연계",
            "② 이어보기 즉시 큐레이션 (중단 회차 유효 푸시)",
            "③ 주말 재방문 유도 팝업 (주간 접속 미미 시)",
        ],
        "btns_nonpromo": [
            "① 시청작 후속 추천 알림 · 유사 장르 신작 연계",
            "② 이어보기 즉시 큐레이션 (중단 회차 유효 푸시)",
            "③ 주말 재방문 유도 팝업 (주간 접속 미미 시)",
        ],
        "promo_overlay": "🎟️ 프로모션 오버레이 — 조건부 잔존 혜택 검증: 킬러 콘텐츠 클릭 등 능동적 시청 신호가 포착된 시점에만 정상 요금제 전환 혜택(쿠폰/장기권) 실험 적용.",
        "prefix": "s2",
    },
    "S4 늦은활성": {
       
        "btns_promo": [
            "① 최근 몰입작 연관·후속 웰메이드 콘텐츠 즉시 배치",
            "② 활성 요일·시간대 가중 신작 알림 (루틴 강화)",
            "③ 유사 스핀오프 활성 흐름 보호 큐레이션",
        ],
        "btns_nonpromo": [
            "① 최근 몰입작 연관·후속 웰메이드 콘텐츠 즉시 배치",
            "② 활성 요일·시간대 가중 신작 알림 (루틴 강화)",
            "③ 유사 스핀오프 활성 흐름 보호 큐레이션",
        ],
        "promo_overlay": "🎟️ 프로모션 오버레이 — 종료 시점 밸류 안내: 현재 콘텐츠 가치를 가장 높게 느끼는 구간이므로 과도한 쿠폰 비용 투입 금지. 정상 종료·정가 유지 시 누릴 장기 가치 중심 안내.",
        "prefix": "s4",
    },
    "S1 유지보호": {
        
        "btns_promo": [
            "① 시청 이력 기반 관련 장르 신작 알림",
            "② 홈 최상단 웰메이드 콘텐츠 개인화 큐레이션",
            "③ 시청 흐름 일치 정보성 큐레이션",
        ],
        "btns_nonpromo": [
            "① 시청 이력 기반 관련 장르 신작 알림",
            "② 홈 최상단 웰메이드 콘텐츠 개인화 큐레이션",
            "③ 시청 흐름 일치 정보성 큐레이션",
        ],
        "promo_overlay": "🎟️ 프로모션 오버레이 — 낮은 빈도의 가치 전달: 과도한 복귀 독촉 전면 차단. 정상 요금 이후에도 이어 볼 콘텐츠를 주 1회 이하 낮은 빈도로만 안내.",
        "prefix": "s1",
    },
}

_FEAT_KR = {
    "watch_time_min_w1": "W1 시청(분)", "watch_time_min_w2": "W2 시청(분)",
    "watch_time_min_w3": "W3 시청(분)", "watch_session_w1":  "W1 세션수",
    "watch_session_w2":  "W2 세션수",   "watch_session_w3":  "W3 세션수",
    "retention_w2_ratio": "W2 유지율", "retention_w3_ratio": "W3 유지율",
    "is_cold_start_3d_fixed": "3일 콜드스타트", "is_cold_start_7d_fixed": "7일 콜드스타트",
    "is_only_w1": "1주차만 시청", "is_w1_over_50pct": "W1 50%+",
    "diff_between_w3_w2": "W3-W2 변화", "diff_between_w3_w1": "W3-W1 변화",
    "diff_between_w2_w1": "W2-W1 변화", "recency": "마지막시청 경과일",
    "max_inactive_gap_days": "최대 공백일", "active_ratio": "활성비율",
    "watch_per_day": "일일 시청량", "age_group": "연령대",
    "is_promotion": "프로모션 유입", "watch_ratio_under_5m": "5분컷 비율",
}


def show_movies(movies: list):
    if not movies:
        st.info("영화를 불러오지 못했어요.")
        return
    cols = st.columns(min(5, max(len(movies), 1)))
    for i, m in enumerate(movies[:5]):
        with cols[i]:
            ai_badge = "🥇 AI 1순위 추천" if i == 0 else f"✨ AI 추천 {i+1}"
            st.markdown(
                f'<div style="background:{"linear-gradient(135deg,#fff8e1,#fffde7)" if i==0 else "#f8f9ff"};'
                f'border:{"2px solid #f59e0b" if i==0 else "1px solid #e2e8f0"};'
                f'border-radius:8px;padding:4px 7px;margin-bottom:5px;'
                f'font-size:11px;font-weight:700;color:{"#b45309" if i==0 else "#5c6bc0"};'
                f'text-align:center;">{ai_badge}</div>',
                unsafe_allow_html=True,
            )
            if m.get("poster"):
                st.image(m["poster"], use_container_width=True)
            st.markdown(f"**{m.get('title', '')}**")
            st.caption(f"★ {m.get('vote_average', 0):.1f}")
            ov = m.get("overview", "")
            st.write((ov[:80] + "...") if len(ov) > 80 else ov)


def _top_genre_for_demo(df_ref, age: int, gender_kor: str):
    genre_cols = {
        "drama":    "drama_ratio",
        "thriller": "thriller_crime_ratio",
        "action":   "action_adventure_ratio",
        "romance":  "romance_ratio",
    }
    group = df_ref[(df_ref["age_group"] == age) & (df_ref["gender_kor"] == gender_kor)]
    if group.empty:
        group = df_ref[df_ref["gender_kor"] == gender_kor]
    if group.empty:
        return None
    vals = {g: float(group[c].mean()) for g, c in genre_cols.items() if c in group.columns}
    return max(vals, key=vals.get) if vals and max(vals.values()) > 0 else None


def get_vip_crm_message(user_key, age, days_inactive, genre, gender, movie_title) -> tuple:
    try:
        from agent import _llm
        gender_kor = "남성" if gender == "M" else "여성"
        prompt = (
            f"OTT 서비스 CRM 마케터로서 VIP 고객에게 보낼 이탈 방지 문자를 작성해주세요.\n"
            f"고객: {user_key} | {age}대 {gender_kor} | 미접속 {days_inactive}일 | 선호장르: {genre}\n"
            f"추천 영화: 【{movie_title}】\n\n"
            "규칙: 반드시 영화 제목 포함, 콘텐츠는 '영화'로만 표현 (드라마·시리즈 금지), "
            "2~3문장, 이모지 1~2개, 친근하고 짧게, 마크다운 기호·번호 없이 순수 텍스트로만."
        )
        return _llm(0.7).invoke(prompt).content, "Gemini"
    except Exception:
        try:
            from agent import generate_retention_message
            return generate_retention_message(age, days_inactive, gender, genre), "Gemini"
        except Exception as e:
            return f"메시지 생성 실패: {e}", "오류"


# ══════════════════════════════════════════════════════════════════════════════
# 3. 데이터 로드
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    import joblib
    from sklearn.ensemble import GradientBoostingClassifier

    # 주요 데이터: 06x_expanded_dataset.csv (reg_date/end_date 없음)
    # → Membership_v3.csv에서 reg_date + end_date 조인 (중복제거 없이)
    data_path  = Path(__file__).parent / "06x_expanded_dataset.csv"
    model_path = _AGENT_DIR / "churn_model.pkl"
    v3_path    = _AGENT_DIR / "Membership_v3.csv"

    df = pd.read_csv(data_path)
    df = df.drop_duplicates().reset_index(drop=True)

    if v3_path.exists():
        _v3 = pd.read_csv(v3_path, usecols=["USER_KEY", "reg_date", "end_date"])
        _v3["reg_date"] = pd.to_datetime(_v3["reg_date"])
        _v3["end_date"] = pd.to_datetime(_v3["end_date"])
        df = df.merge(_v3, on="USER_KEY", how="left")  # 중복제거 없이 조인
    else:
        df["reg_date"] = pd.Timestamp("2021-03-01")
        df["end_date"] = pd.Timestamp("2021-04-16")

    df["reg_date"] = pd.to_datetime(df["reg_date"])

    feature_cols = [
        "watch_time_min_w1", "watch_time_min_w2", "watch_time_min_w3",
        "watch_session_w1",  "watch_session_w2",  "watch_session_w3",
        "retention_w2_ratio", "retention_w3_ratio",
        "is_cold_start_3d_fixed", "is_cold_start_7d_fixed",
        "is_only_w1", "is_w1_over_50pct",
        "diff_between_w3_w2", "diff_between_w3_w1", "diff_between_w2_w1",
        "recency", "max_inactive_gap_days", "active_ratio", "watch_per_day",
        "age_group", "is_promotion",
    ]
    available = [c for c in feature_cols if c in df.columns]
    try:
        model, cols = joblib.load(model_path)
        cols = [c for c in cols if c in df.columns]
        proba = model.predict_proba(df[cols].fillna(0))[:, 1]
        df["churn_score"] = (1 - proba) * 100
    except Exception:
        from sklearn.model_selection import train_test_split
        X = df[available].fillna(0)
        y = df["is_repurchase"]
        X_tr, X_te, y_tr, _ = train_test_split(X, y, test_size=0.2, random_state=42)
        model = GradientBoostingClassifier(n_estimators=300, max_depth=5,
                                           learning_rate=0.05, random_state=42)
        model.fit(X_tr, y_tr)
        joblib.dump((model, available), model_path)
        df["churn_score"] = (1 - model.predict_proba(X)[:, 1]) * 100

    df["is_churn"]   = (df["is_repurchase"] == 0).astype(int)
    df["gender_kor"] = np.where(df["is_female"] == 1, "여성",
                       np.where(df["is_male"] == 1, "남성", "미상"))
    df["plan"]       = np.where(df["is_premium"] == 1, "프리미엄",
                       np.where(df["is_standard"] == 1, "스탠다드", "베이직"))
    df["w12"]        = df["watch_time_min_w1"] + df["watch_time_min_w2"]
    _fc = "watch_ratio_under_5m"
    df["segment"]    = df.apply(
        lambda r: get_segment(r["w12"], r["watch_time_min_w3"],
                              float(r[_fc]) if _fc in df.columns else 0.0), axis=1)
    df["가입경로"]   = np.where(df["is_promotion"] == 1, "🎟️ 프로모션", "💼 정가")
    df["end_date_d"] = df["end_date"].dt.date
    df["reg_date_d"] = df["reg_date"].dt.date
    return df


@st.cache_resource
def load_shap_explainer():
    try:
        import shap, joblib
        model, cols = joblib.load(_AGENT_DIR / "churn_model.pkl")
        return shap.TreeExplainer(model), list(cols)
    except Exception:
        return None, []


@st.cache_data(show_spinner=False)
def compute_shap(_explainer, X_df: pd.DataFrame) -> np.ndarray:
    raw = _explainer.shap_values(X_df, check_additivity=False)
    arr = np.array(raw[1] if isinstance(raw, list) else raw)
    return -arr


@st.cache_data(show_spinner=False)
def gen_shap_insight(label: str, cr: float, feats_str: str, _ver: int = 0) -> str:
    try:
        from agent import _llm
        prompt = (
            f"OTT 이탈 분석 전문가로서 아래 SHAP 분석 결과를 바탕으로 "
            f"비전문가도 이해할 수 있게 핵심 요인 3가지를 설명하고 마지막에 한 줄 결론을 써주세요.\n"
            f"세그먼트: {label} | 이탈률: {cr:.1f}%\n"
            f"주요 이탈 요인(SHAP): {feats_str}\n\n"
            "출력 형식(반드시 이 형식 사용):\n"
            "• [피처명]: [한 문장 해석 — 어떤 값이 이탈 위험을 높이는지 쉽게]\n"
            "• [피처명]: ...\n"
            "• [피처명]: ...\n"
            "💡 결론: [핵심 CRM 액션 한 문장]\n\n"
            "규칙: 마크다운 기호 없이, 숫자·방향 포함, 친근하고 간결하게."
        )
        return _llm(0.3).invoke(prompt).content
    except Exception:
        parts = [p.split("(")[0] for p in feats_str.split(" / ")]
        f1 = parts[0] if parts else ""
        return f"• {f1}: 이탈 위험에 가장 큰 영향을 미치는 요인입니다.\n💡 결론: {label} 이탈률 {cr:.1f}% — 해당 요인 중심 CRM 개입 권고."


@st.cache_data(show_spinner=False)
def gen_daily_insight(
    date_str: str, today_expire: int, today_high: int,
    pred_high: int, cr: float, _ver: int = 0
) -> str:
    try:
        from agent import _llm
        prompt = (
            f"OTT CRM 담당자에게 오늘의 이탈 현황을 2~3문장으로 요약하세요.\n"
            f"기준일: {date_str} | 오늘 만기: {today_expire}명 | 오늘 만기 고위험: {today_high}명 | "
            f"향후 7일 예측 고위험: {pred_high}명 | 지난 7일 이탈률: {cr:.1f}%\n"
            "규칙: 마크다운 없이 순수 텍스트. 숫자 포함. 즉각 대응 권고 포함."
        )
        return _llm(0.3).invoke(prompt).content
    except Exception:
        return (
            f"오늘 만기 고객 {today_expire:,}명 중 고위험군 {today_high:,}명이 확인됩니다. "
            f"향후 7일 예측 고위험 {pred_high:,}명 포함, S6 휴면군·S3 초기관심 고객 중심 CRM 처방이 필요합니다."
        )


# ══════════════════════════════════════════════════════════════════════════════
# 4. 세션 상태 초기화
# ══════════════════════════════════════════════════════════════════════════════
_DATE_DEFAULT = datetime.date(2021, 4, 8)
_DATE_MIN     = datetime.date(2021, 3, 1)
_DATE_MAX     = datetime.date(2021, 4, 16)

for _k, _v in [
    ("action_log", {}),
    ("budget_used", 0),
    ("wk1_3d_sent", False), ("wk1_7d_sent", False),
    ("wk2_mid_step", 0), ("wk2_zero_sent", False),
    ("wk3_hi_sent", False), ("wk3_low_step", 0), ("wk3_zero_sent", False),
    ("wk1_3d_sent_n", False), ("wk1_7d_sent_n", False),
    ("wk2_mid_step_n", 0), ("wk2_zero_sent_n", False),
    ("wk3_hi_sent_n", False), ("wk3_low_step_n", 0), ("wk3_zero_sent_n", False),
    ("wk4_s3s6_sent", False), ("wk4_under31_sent", False), ("wk4_31to101_sent", False),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ══════════════════════════════════════════════════════════════════════════════
# 5. 데이터 로드 & 코호트 필터
# ══════════════════════════════════════════════════════════════════════════════
df_all = load_data()

# ── 헤더: 제목 (전체 폭) ─────────────────────────────────────────────────────
st.markdown(
    "<h2 style='margin-bottom:4px;'>🎬 OTT 이탈 방어 대시보드</h2>"
    "<p style='color:#666;font-size:14px;margin-top:0;line-height:1.6;margin-bottom:16px;'>"
    "데이터 기반 이탈 예측 · 세그먼트 분석 · CRM 처방 통합 콘솔 &nbsp;|&nbsp; "
    "🤖 <b>AI 에이전트(Gemini)</b> 기반 자동 개인화 메시지 생성</p>",
    unsafe_allow_html=True,
)

# ── 필터: 별도 행 (라벨 표시) ────────────────────────────────────────────────
_fc1, _fc2, _fc3 = st.columns([2, 2, 3])
with _fc1:
    cohort_opt = st.selectbox(
        "👥 분석 대상 필터",
        ["전체 가입자", "프로모션 유입", "정가 구독"],
        key="cohort_filter",
    )
with _fc2:
    sel_date = st.date_input(
        "📅 분석 기준일",
        value=_DATE_DEFAULT,
        min_value=_DATE_MIN,
        max_value=_DATE_MAX,
        key="sel_date",
    )
with _fc3:
    st.caption("데이터 기간: 2021-03-01 ~ 2021-04-16 · 기준일 이전 = 실제 이탈률 / 이후 = 예측 이탈률")

st.markdown("---")

# ── 코호트 적용 ───────────────────────────────────────────────────────────────
if cohort_opt == "프로모션 유입":
    df = df_all[df_all["is_promotion"] == 1].copy()
elif cohort_opt == "정가 구독":
    df = df_all[df_all["is_promotion"] == 0].copy()
else:
    df = df_all.copy()

# ══════════════════════════════════════════════════════════════════════════════
# 6. 공통 집계
# ══════════════════════════════════════════════════════════════════════════════
# KPI 1: 기준일 기준 활성 구독자 (reg_date <= sel_date AND end_date >= sel_date)
# end_date == sel_date: 오늘 만기 = 오늘까지는 활성으로 포함
TOTAL       = int(
    ((df["reg_date_d"] <= sel_date) & (df["end_date_d"] >= sel_date)).sum()
)

# 오늘 만기 고객 (시사점·온보딩용)
_today_df        = df[df["end_date_d"] == sel_date]
TODAY_EXPIRE     = len(_today_df)
TODAY_HIGH_RISK  = int((_today_df["churn_score"] >= 40).sum())

# KPI 2: 지난 7일 실제 이탈률 (end_date가 [sel_date-7, sel_date-1] 구간)
_w7_start   = sel_date - datetime.timedelta(days=7)
_w7_mask    = (df["end_date_d"] >= _w7_start) & (df["end_date_d"] < sel_date)
_w7_df      = df[_w7_mask]
_W7_TOTAL   = max(len(_w7_df), 1)
_W7_CHURN   = int(_w7_df["is_churn"].sum())
CHURN_RATE  = _W7_CHURN / _W7_TOTAL * 100
CHURNED     = _W7_CHURN

# KPI 3: 향후 7일 예측 이탈률 (오늘 제외, sel_date+1 ~ min(sel_date+7, 4/16))
_DATA_MAX   = datetime.date(2021, 4, 16)
_n7_start   = sel_date + datetime.timedelta(days=1)
_n7_end     = min(sel_date + datetime.timedelta(days=7), _DATA_MAX)
_no_future  = _n7_start > _DATA_MAX           # 4/16 선택 시 미래 데이터 없음
_pred_cut   = sel_date - datetime.timedelta(days=21)
if _no_future:
    _n7_df   = df.iloc[:0]                    # 빈 DataFrame
else:
    _n7_mask = (
        (df["end_date_d"] >= _n7_start) &
        (df["end_date_d"] <= _n7_end) &
        (df["reg_date_d"] <= _pred_cut)
    )
    _n7_df   = df[_n7_mask]
_N7_TOTAL   = len(_n7_df)
HIGH_RISK   = int((_n7_df["churn_score"] >= 40).sum()) if _N7_TOTAL > 0 else 0
PRED_RATE   = HIGH_RISK / _N7_TOTAL * 100 if _N7_TOTAL > 0 else 0.0

# KPI 4: 향후 7일 만기 예정 전체 고객 수 (오늘 제외, 4/15 cap)
NEXT7_TOTAL = int(
    ((df["end_date_d"] >= _n7_start) & (df["end_date_d"] <= _n7_end)).sum()
)

# 세그먼트 마스크
seg_masks = {s: df[df["segment"] == s] for s in SEG_META}

# ══════════════════════════════════════════════════════════════════════════════
# 7. 탭 정의
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab3 = st.tabs([
    " 일별 이탈 현황 & 예측 추이",
    " 주차별 초기 고객 관리 · 세그먼트 처방",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — 이탈 현황
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown(
        "<p style='font-size:14px;color:#555;margin-bottom:20px;'>"
        "날짜별 실제·예측 이탈률과 고위험군 특징을 한눈에 파악합니다. "
        "슬라이더로 기준일을 이동하면 실제(막대)↔예측(선) 구간이 자동 전환됩니다.</p>",
        unsafe_allow_html=True,
    )

    # ── KPI 4개 ──────────────────────────────────────────────────────────────
    _CARD  = (
        'background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;'
        'padding:14px 16px;box-shadow:0 1px 4px rgba(0,0,0,0.06);'
    )
    _TTL   = 'font-size:13px;color:#555;font-weight:500;margin-bottom:6px;'
    _TTL_B = 'font-size:13px;color:#555;font-weight:700;margin-bottom:6px;'
    _VAL   = 'font-size:30px;font-weight:600;color:#1a1a1a;line-height:1.2;'
    _VAL_B = 'font-size:30px;font-weight:800;color:#1a1a1a;line-height:1.2;'
    _SUB   = 'font-size:12px;color:#888;margin-top:6px;'

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f'<div style="{_CARD}">'
            f'<div style="{_TTL}"> 현재 이용 고객</div>'
            f'<div style="{_VAL}">{TOTAL:,} 명</div>'
            f'<div style="{_SUB}">{sel_date.strftime("%m/%d")} 구독 중 기준</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with k2:
        _w7_period = (f"{_w7_start.strftime('%m/%d')}~"
                      f"{(sel_date - datetime.timedelta(1)).strftime('%m/%d')}")
        st.markdown(
            f'<div style="{_CARD}">'
            f'<div style="{_TTL}"> 지난 7일 실제 이탈률</div>'
            f'<div style="{_VAL}">{CHURN_RATE:.1f} %</div>'
            f'<div style="{_SUB}">{_W7_TOTAL:,}명 중 {CHURNED:,}명 이탈 ({_w7_period})</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with k3:
        _pred_val = "— " if _no_future else f"{PRED_RATE:.1f} %"
        _pred_sub = ("데이터 마지막 날 — 미래 구간 없음" if _no_future else
                     f"{_N7_TOTAL:,}명 중 {HIGH_RISK:,}명 이탈 예측 "
                     f"({_n7_start.strftime('%m/%d')}~{_n7_end.strftime('%m/%d')})")
        st.markdown(
            f'<div style="{_CARD}">'
            f'<div style="{_TTL_B}"> 향후 7일 예측 이탈률</div>'
            f'<div style="{_VAL_B}">{_pred_val}</div>'
            f'<div style="{_SUB}">{_pred_sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    _high_pct = f" ({TODAY_HIGH_RISK/TODAY_EXPIRE*100:.1f}%)" if TODAY_EXPIRE > 0 else ""
    with k4:
        st.markdown(
            f'<div style="{_CARD}">'
            f'<div style="{_TTL}"> 오늘 만기 고객</div>'
            f'<div style="{_VAL}">{TODAY_EXPIRE:,} 명</div>'
            f'<div style="{_SUB}">'
            f'└  고위험 {TODAY_HIGH_RISK:,}명{_high_pct}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.caption(
        f"💡 활성 고객: {sel_date.strftime('%m/%d')} 기준 구독 중 {TOTAL:,}명 · "
        f"지난 7일: {_W7_TOTAL:,}명 만기 중 {CHURNED:,}명 이탈 · "
        f"향후 7일: {_N7_TOTAL:,}명 만기 예정 중 {HIGH_RISK:,}명 이탈 예측 "
    )
    st.markdown("---")

    # ── 메인 차트: 실제 이탈률(막대) + 예측 이탈률(선, 전 구간) ─────────────
    st.markdown("####  일별 실제 이탈률 vs 예측 이탈률")
    st.caption(
        "x축 기준: end_date (구독 만료일) · "
        " 빨간 막대: 실제 이탈률 (확정값) · "
        " 보라 선: AI 예측 이탈률 (전 구간) · "
        "겹치는 구간에서 모델 정확도 비교 가능"
    )

    # ── 데이터 집계 (둘 다 end_date 기준) ──────────────────────────────────
    _CHART_START = datetime.date(2021, 4, 1)   # 3월 소수 데이터 제외 (1~3명 수준)
    _CHART_END   = datetime.date(2021, 4, 16)  # 4/16 포함
    _ed          = df.dropna(subset=["end_date_d"]).copy()
    _ed          = _ed[
        (_ed["end_date_d"] >= _CHART_START) &
        (_ed["end_date_d"] <= _CHART_END)
    ]
    _pred_cutoff = sel_date - datetime.timedelta(days=21)

    # 빨간 막대: 실제 이탈률 — end_date < sel_date
    _past_df = _ed[_ed["end_date_d"] < sel_date]
    _past = (
        _past_df.groupby("end_date_d")
        .agg(만료수=("USER_KEY", "count"), 이탈수=("is_churn", "sum"))
        .reset_index()
    )
    _past["이탈률"] = _past["이탈수"] / _past["만료수"] * 100
    _past["날짜"]   = pd.to_datetime(_past["end_date_d"])
    _past = _past.sort_values("날짜")

    # 보라 선: 예측 이탈률 — 전 end_date 구간 (3주 완료 고객만)
    _pred_df = _ed[_ed["reg_date_d"] <= _pred_cutoff]
    _pred = (
        _pred_df.groupby("end_date_d")
        .agg(만료수=("USER_KEY", "count"),
             고위험수=("churn_score", lambda x: (x >= 40).sum()))
        .reset_index()
    )
    _pred["예측이탈률"] = _pred["고위험수"] / _pred["만료수"] * 100
    _pred["날짜"]       = pd.to_datetime(_pred["end_date_d"])
    _pred = _pred.sort_values("날짜")

    fig_main = go.Figure()

    # ── 빨간 막대: 실제 이탈률 ──────────────────────────────────────────────
    if not _past.empty:
        fig_main.add_trace(go.Bar(
            x=_past["날짜"], y=_past["이탈률"],
            name=" 실제 이탈률",
            marker_color="#ef4444",
            opacity=0.75,
            hovertemplate="%{x|%m/%d}<br>실제 이탈률: %{y:.1f}%<extra></extra>",
        ))

    # ── 보라 선: 예측 이탈률 (전 구간, 막대 위에 겹쳐서 비교) ───────────────
    if not _pred.empty:
        fig_main.add_trace(go.Scatter(
            x=_pred["날짜"], y=_pred["예측이탈률"],
            name=" 예측 이탈률",
            mode="lines+markers",
            line=dict(color="#8b5cf6", width=2.5),
            marker=dict(size=7, symbol="circle"),
            hovertemplate="%{x|%m/%d}<br>예측 이탈률: %{y:.1f}%<extra></extra>",
        ))

    # ── 기준일 수직선 ────────────────────────────────────────────────────────
    _vx = sel_date.strftime("%Y-%m-%d")
    fig_main.add_shape(
        type="line",
        x0=_vx, x1=_vx, y0=0, y1=1, yref="paper",
        line=dict(dash="dash", color="#64748b", width=1.5),
    )
    fig_main.add_annotation(
        x=_vx, y=0.97, yref="paper",
        text=f"기준일<br>{sel_date.strftime('%m/%d')}",
        showarrow=False,
        font=dict(size=10, color="#64748b"),
        xanchor="left", yanchor="top",
        bgcolor="rgba(255,255,255,0.8)",
        borderpad=3,
    )

    # ── 지난 7일 평균 수평선 ─────────────────────────────────────────────────
    fig_main.add_hline(
        y=CHURN_RATE, line_dash="dash", line_color="#94a3b8",
        annotation_text=f"지난 7일 평균 {CHURN_RATE:.1f}%",
        annotation_position="bottom right",
        annotation_font=dict(size=10, color="#94a3b8"),
    )

    fig_main.update_layout(
        height=380, plot_bgcolor="white", hovermode="x unified",
        margin=dict(t=20, b=40, l=50, r=20),
        legend=dict(orientation="h", y=1.08, x=0),
        yaxis=dict(gridcolor="#f0f0f0", title="이탈률 (%)", range=[0, 55]),
        xaxis=dict(
            tickformat="%m/%d", gridcolor="#f0f0f0",
            range=["2021-03-20", "2021-04-17"],
            dtick="D2",
        ),
        bargap=0.25,
    )
    st.plotly_chart(fig_main, use_container_width=True)

    st.markdown("---")

    # ── 향후 7일 고위험군 공통 변수 ──────────────────────────────────────────
    _n7_high = _n7_df[_n7_df["churn_score"] >= 40]
    _n7_safe = _n7_df[_n7_df["churn_score"] <  40]

    # ── 향후 7일 고위험군 분석 (양열: 왼쪽=행동프로파일 / 오른쪽=SHAP+AI) ──
    st.markdown("#### 향후 7일 고위험군 분석")

    if len(_n7_high) == 0:
        st.info(
            "향후 7일 만기 고위험 고객이 없습니다. "
            "기준일을 앞으로 이동하거나 코호트 필터를 변경해보세요."
        )
    else:
        st.caption(
            f"🔴 고위험군({len(_n7_high):,}명) vs 🟢 안전군({len(_n7_safe):,}명) · "
            f"향후 7일 만기 예정 ({_n7_start.strftime('%m/%d')}~{_n7_end.strftime('%m/%d')}) · "
        )

        # ── 공통 데이터 계산 ─────────────────────────────────────────────────
        _weeks   = ["1주차", "2주차", "3주차"]
        _w_cols  = ["watch_time_min_w1", "watch_time_min_w2", "watch_time_min_w3"]
        _high_mean = [_n7_high[c].mean() for c in _w_cols]
        _safe_mean = [_n7_safe[c].mean() if len(_n7_safe) > 0 else 0.0 for c in _w_cols]
        _h5m      = _n7_high["watch_ratio_under_5m"].mean() * 100
        _s5m      = _n7_safe["watch_ratio_under_5m"].mean() * 100 if len(_n7_safe) > 0 else 0.0
        _hact     = _n7_high["active_ratio"].mean() * 100
        _sact     = _n7_safe["active_ratio"].mean() * 100 if len(_n7_safe) > 0 else 0.0
        _h_w1only = _n7_high["is_only_w1"].mean() * 100
        _s_w1only = _n7_safe["is_only_w1"].mean() * 100 if len(_n7_safe) > 0 else 0.0
        _h_genre  = _n7_high["genre_diversity_count"].mean() if "genre_diversity_count" in _n7_high.columns else 2.0
        _s_genre  = _n7_safe["genre_diversity_count"].mean() if "genre_diversity_count" in _n7_safe.columns and len(_n7_safe) > 0 else 3.0
        _h_1m     = _n7_high["watch_ratio_under_1m"].mean() * 100 if "watch_ratio_under_1m" in _n7_high.columns else 0.0
        _s_1m     = _n7_safe["watch_ratio_under_1m"].mean() * 100 if "watch_ratio_under_1m" in _n7_safe.columns and len(_n7_safe) > 0 else 0.0
        _h_uniq   = _n7_high["unique_movie"].mean() if "unique_movie" in _n7_high.columns else 0.0
        _s_uniq   = _n7_safe["unique_movie"].mean() if "unique_movie" in _n7_safe.columns and len(_n7_safe) > 0 else 0.0

        # ── SHAP 계산 ────────────────────────────────────────────────────────
        _t1_shap_expl, _t1_shap_cols = load_shap_explainer()
        _t1_shap_ready = False
        _t1_sv_df = None
        _t1_clrs  = None
        _t1_feats_str = ""
        _n7_cr = _n7_high["is_churn"].mean() * 100

        if _t1_shap_expl is not None:
            _t1_valid = [c for c in _t1_shap_cols if c in _n7_high.columns]
            with st.spinner("SHAP 계산 중..."):
                _t1_sv = compute_shap(_t1_shap_expl, _n7_high[_t1_valid].fillna(0))
            _t1_feat_arr = _n7_high[_t1_valid].fillna(0).values
            _t1_sm = _t1_sv.mean(axis=0)
            _t1_sv_df = (
                pd.DataFrame({"피처": [_FEAT_KR.get(c, c) for c in _t1_valid], "SHAP": _t1_sm})
                .reindex(pd.Series(_t1_sm).abs().sort_values(ascending=False).index)
                .head(10).sort_values("SHAP", key=lambda x: x.abs())
            )
            _t1_clrs = ["#e74c3c" if v > 0 else "#3498db" for v in _t1_sv_df["SHAP"]]
            _top5_idx = pd.Series(_t1_sm).abs().sort_values(ascending=False).head(5).index.tolist()
            _feat_details = []
            for _fi in _top5_idx:
                _fname = _FEAT_KR.get(_t1_valid[_fi], _t1_valid[_fi])
                _corr = np.corrcoef(_t1_feat_arr[:, _fi], _t1_sv[:, _fi])[0, 1]
                _dir = "높으면 이탈↑" if _corr > 0 else "낮으면 이탈↑"
                _feat_details.append(f"{_fname}(SHAP:{_t1_sm[_fi]:+.3f}, {_dir})")
            _t1_feats_str = " / ".join(_feat_details)
            _t1_top_idx = pd.Series(_t1_sm).abs().sort_values(ascending=False).head(10).index.tolist()
            _t1_shap_ready = True

        # ── 양열 레이아웃 ────────────────────────────────────────────────────
        _main_l, _main_r = st.columns([1, 1])

        with _main_l:
            st.markdown("안전군 대비 고위험군 특징")
            # ── 레이더 차트 (5축, 전체 평균 기준) ────────────────────────────────
            # (lbl, col, is_pct, invert) — invert=True: avg/val로 역전(낮을수록 좋음)
            _radar_cfg = [
                ("활성비율",   "active_ratio",          True,  False),
                ("장르다양성", "genre_diversity_count", False, False),
                ("고유영화수", "unique_movie",          False, False),
                ("시청 지속률", "watch_ratio_under_5m", True,  True),
                ("최근 접속도", "recency",              False, True),
            ]
            _n_axes = len(_radar_cfg)
            _r_labels, _h_scores, _s_scores = [], [], []
            _h_vals, _s_vals, _a_vals = [], [], []
            _df_p  = df[df["reg_date_d"] <= _pred_cut]
            _n7_lo = _n7_df[_n7_df["churn_score"] < 20]
            for lbl, col, is_pct, invert in _radar_cfg:
                _r_labels.append(lbl)
                mul = 100 if is_pct else 1
                hv = _n7_high[col].mean() * mul if col in _n7_high.columns else 0.0
                sv = _n7_lo[col].mean()   * mul if col in _n7_lo.columns and len(_n7_lo) > 0 else 0.0
                av = _df_p[col].mean()    * mul if col in _df_p.columns else 1.0
                _h_vals.append(hv); _s_vals.append(sv); _a_vals.append(av)
                if invert:
                    _h_scores.append(min(av / hv if hv > 0 else 2.0, 2.0))
                    _s_scores.append(min(av / sv if sv > 0 else 2.0, 2.0))
                else:
                    _h_scores.append(min(hv / av if av > 0 else 1.0, 2.0))
                    _s_scores.append(min(sv / av if av > 0 else 1.0, 2.0))
            _rl = _r_labels + [_r_labels[0]]
            _hs = _h_scores + [_h_scores[0]]
            _ss = _s_scores + [_s_scores[0]]
            _h_cd = [[f"{_h_vals[i]:.2f}", f"{_a_vals[i]:.2f}", f"{_h_scores[i]:.2f}x"]
                     for i in range(_n_axes)] + [[f"{_h_vals[0]:.2f}", f"{_a_vals[0]:.2f}", f"{_h_scores[0]:.2f}x"]]
            _s_cd = [[f"{_s_vals[i]:.2f}", f"{_a_vals[i]:.2f}", f"{_s_scores[i]:.2f}x"]
                     for i in range(_n_axes)] + [[f"{_s_vals[0]:.2f}", f"{_a_vals[0]:.2f}", f"{_s_scores[0]:.2f}x"]]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=[1.0] * (_n_axes + 1), theta=_rl, fill=None, name=" 전체 평균",
                line=dict(color="#94a3b8", width=1.5, dash="dash"),
                hovertemplate="<b>%{theta}</b><br>전체 평균 (기준선 1.0x)<extra></extra>",
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=_ss, theta=_rl, fill="toself", name=" 안전군",
                line=dict(color="#22c55e", width=1.5, dash="dot"),
                fillcolor="rgba(34,197,94,0.1)",
                customdata=_s_cd,
                hovertemplate="<b>%{theta}</b><br>안전군: %{customdata[0]}<br>전체 평균: %{customdata[1]}<br>평균 대비: %{customdata[2]}<extra></extra>",
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=_hs, theta=_rl, fill="toself", name=" 고위험군",
                line=dict(color="#ef4444", width=2),
                fillcolor="rgba(239,68,68,0.18)",
                customdata=_h_cd,
                hovertemplate="<b>%{theta}</b><br>고위험군: %{customdata[0]}<br>전체 평균: %{customdata[1]}<br>평균 대비: %{customdata[2]}<extra></extra>",
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(
                    visible=True, range=[0, 2.0],
                    tickvals=[0.5, 1.0, 1.5, 2.0],
                    ticktext=["0.5x", "1.0x", "1.5x", "2.0x"],
                    tickfont=dict(size=8), gridcolor="#e2e8f0",
                )),
                height=250, margin=dict(t=20, b=50, l=40, r=40),
                legend=dict(orientation="h", y=-0.12, x=0.5,
                            xanchor="center", font=dict(size=9)),
                showlegend=True,
            )
            st.plotly_chart(fig_radar, use_container_width=True)


            # ── 하단 나란히: 주차별 시청시간 | 1주차만 시청 비율 ────────────
            _sub_l, _sub_r = st.columns([3, 2])
            with _sub_l:
                fig_cmp = go.Figure()
                fig_cmp.add_trace(go.Bar(
                    name=" 고위험군", x=_weeks, y=_high_mean,
                    marker_color="#ef4444", opacity=0.8,
                    text=[f"{v:.0f}분" for v in _high_mean], textposition="outside",
                ))
                fig_cmp.add_trace(go.Bar(
                    name=" 안전군", x=_weeks, y=_safe_mean,
                    marker_color="#22c55e", opacity=0.8,
                    text=[f"{v:.0f}분" for v in _safe_mean], textposition="outside",
                ))
                _y_max = max(max(_high_mean), max(_safe_mean), 1) * 1.5
                fig_cmp.update_layout(
                    barmode="group", height=240, plot_bgcolor="white",
                    margin=dict(t=30, b=5, l=30, r=5),
                    title=dict(text="주차별 평균 시청시간 (분)", font_size=11, y=0.98),
                    legend=dict(orientation="h", y=1.1, x=0, font=dict(size=9)),
                    yaxis=dict(gridcolor="#f0f0f0", visible=False, range=[0, _y_max]),
                    xaxis=dict(title="", tickfont=dict(size=10)),
                    bargap=0.3,
                )
                st.plotly_chart(fig_cmp, use_container_width=True)

            with _sub_r:
                _w1ratio = _h_w1only / _s_w1only if _s_w1only > 0 else 0
                fig_w1 = go.Figure()
                fig_w1.add_trace(go.Bar(
                    x=[" 고위험", " 안전군"],
                    y=[_h_w1only, _s_w1only],
                    marker_color=["#ef4444", "#22c55e"],
                    opacity=0.85,
                    text=[f"{_h_w1only:.1f}%", f"{_s_w1only:.1f}%"],
                    textposition="outside",
                    textfont=dict(size=11, color=["#ef4444", "#22c55e"]),
                    width=[0.4, 0.4],
                ))
                fig_w1.add_annotation(
                    x=0.5, y=max(_h_w1only, _s_w1only, 1) * 1.12,
                    xref="paper",
                    text=f"<b>{_w1ratio:.0f}배 차이</b>",
                    showarrow=False,
                    font=dict(size=11, color="#ef4444"),
                    bgcolor="rgba(255,245,245,0.9)",
                    bordercolor="#ef4444",
                    borderwidth=1,
                    borderpad=3,
                )
                fig_w1.update_layout(
                    height=220, plot_bgcolor="white", showlegend=False,
                    margin=dict(t=30, b=5, l=5, r=5),
                    title=dict(text=" 1주차만 시청 비율 (%)", font_size=11, y=0.98),
                    yaxis=dict(gridcolor="#f0f0f0", visible=False,
                               range=[0, max(_h_w1only, _s_w1only, 1) * 1.5]),
                    xaxis=dict(title="", tickfont=dict(size=10)),
                )
                st.plotly_chart(fig_w1, use_container_width=True)

        with _main_r:
            if _t1_shap_ready:
                st.markdown("**🤖 SHAP Beeswarm — 이탈 요인 분포**")
                st.caption("🔴 빨강: 피처값 높음 / 🔵 파랑: 피처값 낮음 · 점 1개 = 고객 1명")
                # Beeswarm 차트
                fig_t1_shap = go.Figure()
                _bsw_top = list(reversed(_t1_top_idx))  # 중요도 높은 피처가 위로
                for _rank, _fi in enumerate(_bsw_top):
                    _sv_col = _t1_sv[:, _fi]
                    _fv_col = _t1_feat_arr[:, _fi]
                    _fv_min, _fv_max = _fv_col.min(), _fv_col.max()
                    _fv_norm = (_fv_col - _fv_min) / (_fv_max - _fv_min + 1e-9)
                    np.random.seed(_fi)
                    _yj = np.random.uniform(-0.35, 0.35, len(_sv_col))
                    _fname = _FEAT_KR.get(_t1_valid[_fi], _t1_valid[_fi])
                    fig_t1_shap.add_trace(go.Scatter(
                        x=_sv_col,
                        y=_rank + _yj,
                        mode="markers",
                        marker=dict(
                            size=4, opacity=0.65,
                            color=_fv_norm,
                            colorscale=[[0, "#3498db"], [0.5, "#9b59b6"], [1, "#e74c3c"]],
                            cmin=0, cmax=1,
                            showscale=(_rank == len(_bsw_top) - 1),
                            colorbar=dict(
                                title="Feature<br>value",
                                tickvals=[0, 1], ticktext=["Low", "High"],
                                thickness=12, len=0.55, x=1.01,
                                titlefont=dict(size=10), tickfont=dict(size=9),
                            ),
                        ),
                        showlegend=False, name=_fname,
                        hovertemplate=f"<b>{_fname}</b><br>SHAP: %{{x:+.4f}}<extra></extra>",
                    ))
                _bsw_labels = [_FEAT_KR.get(_t1_valid[i], _t1_valid[i]) for i in _bsw_top]
                fig_t1_shap.add_vline(x=0, line_color="#94a3b8", line_width=1.5)
                fig_t1_shap.update_layout(
                    height=380, plot_bgcolor="white",
                    margin=dict(t=10, b=40, l=10, r=80),
                    xaxis=dict(gridcolor="#f0f0f0", title="SHAP value (이탈 위험 영향)", zeroline=False),
                    yaxis=dict(tickvals=list(range(len(_bsw_top))), ticktext=_bsw_labels,
                               gridcolor="#f0f0f0", tickfont=dict(size=10)),
                )
                st.plotly_chart(fig_t1_shap, use_container_width=True)

                # AI 인사이트 (하단)
                st.markdown("AI 인사이트")
                with st.spinner("AI 분석 중..."):
                    _t1_ai_txt = gen_shap_insight(
                        "향후 7일 고위험군", _n7_cr, _t1_feats_str,
                    )
                _safe_t1_ai = _html.escape(strip_md(_t1_ai_txt)).replace("\n", "<br>")
                st.markdown(
                    f'<div style="background:#f1f5f9;'
                    f'border-radius:8px;padding:12px 16px;font-size:13px;'
                    f'line-height:1.75;color:#1a1a1a;">{_safe_t1_ai}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("SHAP 분석을 위해 shap 패키지가 필요합니다.")

    st.markdown("---")

    # ── 오늘의 시사점 (AI 요약) ───────────────────────────────────────────────
    st.markdown("#### 💡 오늘의 시사점")
    with st.spinner("AI 분석 중..."):
        _insight = gen_daily_insight(
            sel_date.strftime("%Y-%m-%d"),
            TODAY_EXPIRE, TODAY_HIGH_RISK,
            HIGH_RISK, CHURN_RATE,
        )
        _safe_ins = _html.escape(strip_md(_insight)).replace("\n", "<br>")
        st.markdown(
            f'<div class="insight-box">{_safe_ins}<br><br>'
            f'<span style="font-size:12px;color:#64748b;">'
            f' 즉시 처방: <b>CRM 처방 탭</b> &nbsp;|&nbsp; VIP 정밀 대응: <b>프리미엄 대응 탭</b>'
            f'</span></div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    # ── 설명 + 예산 카드 (같은 행) ───────────────────────────────────────────
    _BUDGET_TOTAL  = 10_000_000
    _budget_used   = st.session_state["budget_used"]
    _budget_used_pct = min(_budget_used / _BUDGET_TOTAL * 100, 100)
    _bar_clr = "#22c55e" if _budget_used_pct < 50 else "#f59e0b" if _budget_used_pct < 80 else "#ef4444"

    _desc_col, _bdg_col = st.columns([3, 1])
    with _desc_col:
        st.markdown(
            "<p style='font-size:14px;color:#555;margin-bottom:0;line-height:1.8;'>"
            "가입 초기(1~3주차 초기 고객 관리)부터 구독 결정(세그먼트 처방)까지 "
            "전 생애주기 CRM 처방을 실행합니다.</p>",
            unsafe_allow_html=True,
        )
    with _bdg_col:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;padding:6px 0;">'
            f'<span style="font-size:12px;font-weight:600;color:#374151;white-space:nowrap;">'
            f'💸 사용 예산 <b style="color:#1a1a1a;">₩{_budget_used:,}</b></span>'
            f'<div style="flex:1;background:#f1f5f9;border-radius:4px;height:8px;overflow:hidden;">'
            f'<div style="background:{_bar_clr};width:{_budget_used_pct:.1f}%;height:100%;border-radius:4px;"></div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    _crm_sub2, _crm_sub1, _crm_sub3 = st.tabs([
        " 오늘의 처방 실행",
        " 가입 초기 고객 관리 ",
        " ..",
    ])

    # ── 서브탭 A: 주차별 타이밍 레이어 ─────────────────────────────────────
    with _crm_sub1:
        st.caption(
            f"기준일 {sel_date.strftime('%m/%d')} 기준 · "
            "가입 후 1~27일 진행 중인 고객의 주차별 CRM 개입 타이밍 "
        )

        _today_ts = pd.Timestamp(sel_date)
        _days     = (_today_ts - df["reg_date"]).dt.days

        _wk1_base = df[(_days >= 1)  & (_days <= 7)]
        _wk2_base = df[(_days >= 8)  & (_days <= 14)]
        _wk3_base = df[(_days >= 15) & (_days <= 20)]
        # _crm_sub3 공용 변수 (유지 필수)
        _wk1_3d   = _wk1_base[_wk1_base["is_cold_start_3d_fixed"] == 1]
        _wk1_7d   = _wk1_base[_wk1_base["is_cold_start_7d_fixed"] == 1]
        _w1_w2    = _wk2_base["watch_time_min_w1"]
        _wk2_act  = _wk2_base[_w1_w2 > 0]
        _wk2_zero = _wk2_base[_w1_w2 == 0]
        _w12_w3   = _wk3_base["watch_time_min_w1"] + _wk3_base["watch_time_min_w2"]
        _fc3      = "watch_ratio_under_5m"
        _early_stable_w3 = (_w12_w3 >= 119)
        _wk3_hi   = _wk3_base[_early_stable_w3]
        _wk3_low  = _wk3_base[(_w12_w3 > 0) & ~_early_stable_w3]
        _wk3_zero = _wk3_base[_w12_w3 == 0]
        _w2act_sub = f"평균 {_wk2_act['watch_time_min_w1'].mean():.0f}분 시청" if len(_wk2_act) > 0 else "시청 데이터 없음"
        _w3hi_sub  = (f"평균 {(_wk3_hi['watch_time_min_w1'] + _wk3_hi['watch_time_min_w2']).mean():.0f}분 누적 시청"
                      if len(_wk3_hi) > 0 else "시청 데이터 없음")

        # Week 1: 완주율 기반 디펜스 타겟 (시청 시작 후 5분 이내 이탈 비율 ≥30%)
        if _fc3 in _wk1_base.columns:
            _wk1_dropoff = _wk1_base[
                (_wk1_base["is_cold_start_3d_fixed"] == 0) &
                (_wk1_base[_fc3] >= 0.3)
            ]
        else:
            _wk1_dropoff = _wk1_7d

        # Week 2: 전주 대비 시청 반토막 이하 감소 유저
        _wk2_drop = _wk2_base[
            (_wk2_base["watch_time_min_w1"] > 0) &
            (_wk2_base["watch_time_min_w2"] < _wk2_base["watch_time_min_w1"] * 0.5)
        ]

        # Week 3: 소비미형성 통합 (S4~S6 예비)
        _wk3_notformed = _wk3_base[_w12_w3 < 119]

        st.markdown("---")

        def _send_btn(key, sent_key, label, n, cost=15, preview=""):
            sent = st.session_state.get(sent_key, False)
            if n == 0:
                st.button(label, key=key, disabled=True, use_container_width=True)
                return
            if not sent:
                if preview:
                    _scol, _pcol = st.columns([5, 1])
                    btn_clicked = _scol.button(
                        label, key=key, type="secondary", use_container_width=True)
                    with _pcol:
                        with st.popover(""):
                            st.caption("발송 예정 메시지 샘플")
                            st.markdown(
                                f'<div style="background:#f8fafc;border:1px solid #e2e8f0;'
                                f'border-radius:6px;padding:10px 12px;font-size:12px;'
                                f'line-height:1.7;color:#374151;">{preview}</div>',
                                unsafe_allow_html=True,
                            )
                else:
                    btn_clicked = st.button(
                        label, key=key, type="secondary", use_container_width=True)
                if btn_clicked:
                    st.session_state[sent_key] = True
                    st.session_state["action_log"][key] = (
                        n, datetime.datetime.now().strftime("%H:%M"))
                    st.session_state["budget_used"] += cost * n
                    st.rerun()
            else:
                st.success(" 발송 완료")
            if key in st.session_state["action_log"]:
                cnt, t = st.session_state["action_log"][key]
                st.caption(f" {cnt:,}명 · {t} 발송")

        def _step_btns(step_key, btn1_key, btn2_key, label1, label2, n,
                       preview1="", preview2="", cost1=15, cost2=15):
            step = st.session_state.get(step_key, 0)
            st.markdown(
                '<div style="font-size:10px;color:#94a3b8;margin-bottom:4px;">'
                '단계별 대응 — 시청 이력 있는 고객 → 무시청 고객 순</div>',
                unsafe_allow_html=True,
            )
            _bb1, _bb2 = st.columns(2)
            with _bb1:
                if step == 0 and n > 0:
                    if preview1:
                        _s1c, _p1c = st.columns([4, 1])
                        c1 = _s1c.button(f"1단계: {label1}", key=btn1_key,
                                         use_container_width=True)
                        with _p1c:
                            with st.popover(""):
                                st.caption("발송 예정 메시지 샘플")
                                st.markdown(
                                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;'
                                    f'border-radius:6px;padding:10px 12px;font-size:12px;'
                                    f'line-height:1.7;">{preview1}</div>',
                                    unsafe_allow_html=True,
                                )
                    else:
                        c1 = st.button(f"1단계: {label1}", key=btn1_key,
                                       use_container_width=True)
                    if c1:
                        st.session_state[step_key] = 1
                        st.session_state["action_log"][btn1_key] = (
                            n, datetime.datetime.now().strftime("%H:%M"))
                        st.session_state["budget_used"] += cost1 * n
                        st.rerun()
                elif step >= 1:
                    st.success(" 1단계 완료")
                else:
                    st.button(f"1단계: {label1}", key=btn1_key, disabled=True,
                              use_container_width=True)
            with _bb2:
                if step == 1 and n > 0:
                    if preview2:
                        _s2c, _p2c = st.columns([4, 1])
                        c2 = _s2c.button(f"2단계: {label2}", key=btn2_key,
                                         use_container_width=True)
                        with _p2c:
                            with st.popover(""):
                                st.caption("발송 예정 메시지 샘플")
                                st.markdown(
                                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;'
                                    f'border-radius:6px;padding:10px 12px;font-size:12px;'
                                    f'line-height:1.7;">{preview2}</div>',
                                    unsafe_allow_html=True,
                                )
                    else:
                        c2 = st.button(f"2단계: {label2}", key=btn2_key,
                                       use_container_width=True)
                    if c2:
                        st.session_state[step_key] = 2
                        st.session_state["action_log"][btn2_key] = (
                            n, datetime.datetime.now().strftime("%H:%M"))
                        st.session_state["budget_used"] += cost2 * n
                        st.rerun()
                elif step >= 2:
                    st.success(" 2단계 완료")
                else:
                    st.button(f"2단계: {label2}", key=btn2_key, disabled=True,
                              use_container_width=True)
            _log = []
            if btn1_key in st.session_state["action_log"]:
                cnt, t = st.session_state["action_log"][btn1_key]
                _log.append(f"1단계 {cnt:,}명 {t}")
            if btn2_key in st.session_state["action_log"]:
                cnt, t = st.session_state["action_log"][btn2_key]
                _log.append(f"2단계 {cnt:,}명 {t}")
            if _log:
                st.caption(" · ".join(_log))

        # ── Week 1 ~ 3: 3열 ──────────────────────────────────────────────────
        _wc1, _wc2, _wc3 = st.columns(3)
        _div = '<hr style="margin:10px 0;border:none;border-top:1px solid #e2e8f0;">'
        _div_dark = '<hr style="margin:8px 0;border:none;border-top:1.5px solid #94a3b8;">'

        with _wc1:
            with st.container(border=True):

                st.markdown(
                    '<div style="padding:0 0 10px 0;">'
                    '<b style="font-size:15px;">Week 1. 온보딩 골든타임</b><br>'
                    '<span style="font-size:11px;color:#64748b;">초기 시청 형성 여부 확인 (Day 0~6)</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(_div_dark, unsafe_allow_html=True)
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                    f'<span style="font-size:14px;font-weight:700;color:#1a1a1a;">① 첫 시청 미발생 조기 차단 알림</span>'
                    f'<b style="font-size:16px;color:#1e293b;">{len(_wk1_3d):,}명</b>'
                    f'</div>'
                    f'<div style="font-size:11px;color:#94a3b8;margin-bottom:8px;">가입 후 3일간 시청 로그 없음 · 소비형성 위험</div>',
                    unsafe_allow_html=True,
                )
                _send_btn(
                    "wk1_3d", "wk1_3d_sent", "화제작 추천 푸시 발송", len(_wk1_3d),
                    preview="안녕하세요 고객님  가입하셨는데 아직 첫 작품을 못 고르셨군요!<br>"
                            "지금 가장 화제인 작품 1화를 지금 바로 시작해보세요 ",
                )
                st.markdown(_div, unsafe_allow_html=True)
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                    f'<span style="font-size:14px;font-weight:700;color:#1a1a1a;">② 완주율 기반 디펜스 추천</span>'
                    f'<b style="font-size:16px;color:#1e293b;">{len(_wk1_dropoff):,}명</b>'
                    f'</div>'
                    f'<div style="font-size:11px;color:#94a3b8;margin-bottom:8px;">시청 시작 후 조기 이탈 비율 높음 · 몰입도 검증 콘텐츠 매칭</div>',
                    unsafe_allow_html=True,
                )
                _send_btn(
                    "wk1_7d", "wk1_7d_sent", "검증 콘텐츠 디펜스 추천 발송", len(_wk1_dropoff),
                    preview="고객님, 시청 완주율 1위 작품만 골라드렸어요! <br>"
                            "1화만 보시면 바로 빠져드실 거예요 ",
                )

        with _wc2:
            with st.container(border=True):

                st.markdown(
                    '<div style="padding:0 0 10px 0;">'
                    '<b style="font-size:15px;">Week 2. 이탈 조기 신호 포착 구간</b><br>'
                    '<span style="font-size:11px;color:#64748b;">w1 대비 w2 이용 약화 신호 조기 감지 (Day 7~14)</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(_div_dark, unsafe_allow_html=True)
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                    f'<span style="font-size:14px;font-weight:700;color:#1a1a1a;">① w2 이용약화 조기 개입 메시지</span>'
                    f'<b style="font-size:16px;color:#1e293b;">{len(_wk2_drop):,}명</b>'
                    f'</div>'
                    f'<div style="font-size:11px;color:#94a3b8;margin-bottom:8px;">전주 대비 시청 반토막 이하 감소 · 즉시 단발 개입 필요</div>',
                    unsafe_allow_html=True,
                )
                _send_btn(
                    "wk2_act_s1", "wk2_mid_step", "w2 이용약화 단발 리마인드 발송", len(_wk2_drop),
                    preview="고객님, 지난주보다 접속이 줄었어요 <br>"
                            "보시던 작품 다음 편이 기다리고 있어요. 지금 이어보기 하시겠어요?",
                )
                st.markdown(_div, unsafe_allow_html=True)
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                    f'<span style="font-size:14px;font-weight:700;color:#1a1a1a;">② 회차 이탈 이어보기 푸시</span>'
                    f'<b style="font-size:16px;color:#1e293b;">{len(_wk2_act):,}명</b>'
                    f'</div>'
                    f'<div style="font-size:11px;color:#94a3b8;margin-bottom:8px;">{_w2act_sub} · 끊긴 회차 다음 편 연동 가능</div>',
                    unsafe_allow_html=True,
                )
                _send_btn(
                    "wk2_zero_s1", "wk2_zero_sent", "이어보기 회차 연동 푸시 발송", len(_wk2_act),
                    preview="고객님, 지난번 보시던 작품 기억하세요? <br>"
                            "다음 편이 기다리고 있어요. 지금 이어보기 하시겠어요?",
                )

        with _wc3:
            _cr_w3notformed = _wk3_notformed["is_churn"].mean() * 100 if len(_wk3_notformed) > 0 else 0.0
            with st.container(border=True):

                st.markdown(
                    '<div style="padding:0 0 10px 0;">'
                    '<b style="font-size:15px;">Week 3. 정밀 타겟 구간</b><br>'
                    '<span style="font-size:11px;color:#64748b;">w1+w2 누적 기반 예비 분류, 그룹별 초개인화 (Day 14~20)</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(_div_dark, unsafe_allow_html=True)
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                    f'<span style="font-size:14px;font-weight:700;color:#1a1a1a;">① 소비형성군 초개인화 메시징</span>'
                    f'<b style="font-size:16px;color:#1e293b;">{len(_wk3_hi):,}명</b>'
                    f'</div>'
                    f'<div style="font-size:11px;color:#94a3b8;margin-bottom:8px;">{_w3hi_sub} · w1+w2≥119분</div>',
                    unsafe_allow_html=True,
                )
                _send_btn(
                    "wk3_hi", "wk3_hi_sent", "시청 이력 기반 초개인화 메시지 발송", len(_wk3_hi),
                    preview="고객님, 좋아하시는 작품과 꼭 닮은 신작이 나왔어요! <br>"
                            "취향 저격 콘텐츠를 Gemini가 직접 골라드렸어요 ",
                )
                st.markdown(_div, unsafe_allow_html=True)
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                    f'<span style="font-size:14px;font-weight:700;color:#1a1a1a;">② 소비미형성군 단편 위주 재온보딩 </span>'
                    f'<b style="font-size:16px;color:#1e293b;">{len(_wk3_notformed):,}명</b>'
                    f'</div>'
                    f'<div style="font-size:11px;color:#94a3b8;margin-bottom:8px;">이탈률 {_cr_w3notformed:.1f}% · w1+w2&lt;119분 · 선택 피로 최소화 필요</div>',
                    unsafe_allow_html=True,
                )
                _send_btn(
                    "wk3_low_s1", "wk3_low_step", "단편·숏폼 위주 재온보딩 팝업 발송", len(_wk3_notformed),
                    preview="고객님, 짧게 시작할 수 있는 콘텐츠를 골라봐요! <br>"
                            "30분짜리 단편 하나로 오늘 OTT 생활을 시작해보세요 ",
                )

    # ── 서브탭 C: 주차별 AI 온보딩 시나리오 ─────────────────────────────────
    with _crm_sub3:
        st.caption(
            f"기준일 {sel_date.strftime('%m/%d')} 기준 · "
            "가입 후 1~21일 진행 중인 고객의 주차별 CRM 개입 타이밍"
        )
        _nc1, _nc2, _nc3 = st.columns(3)

        with _nc1:
            with st.container(border=True):
                st.markdown(
                    f'<div style="padding:4px 0 8px 0;">'
                    f'<div style="font-weight:800;font-size:16px;color:#1e293b;margin-bottom:4px;">Week 1. 온보딩 골든타임</div>'
                    f'<div style="font-size:12px;color:#64748b;margin-bottom:12px;">첫 재생 장벽 제거 — 시청 경험 진입이 목표</div>'
                    f'<div style="display:flex;flex-direction:column;gap:6px;min-height:177px;">'
                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;">'
                    f'<div><div style="font-size:12px;font-weight:700;color:#1a1a1a;"> 초기 소비 미진입 신호 (3~6일)</div>'
                    f'<div style="font-size:11px;color:#94a3b8;">첫 콘텐츠 미진입 · 소비형성 위험</div></div>'
                    f'<div style="font-weight:700;font-size:14px;">{len(_wk1_3d):,}명</div></div>'
                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;">'
                    f'<div><div style="font-size:12px;font-weight:700;color:#1a1a1a;"> 초기 소비 미형성 고위험 (7일+)</div>'
                    f'<div style="font-size:11px;color:#94a3b8;">첫 7일 내 시청 없음 · 휴면군 진입 위험</div></div>'
                    f'<div style="font-weight:700;font-size:14px;">{len(_wk1_7d):,}명</div></div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(_div_dark, unsafe_allow_html=True)
                _wk1_tabs_n = st.tabs([" 소비 미진입 (3~6일)", " 소비 미형성 고위험 (7일+)"])
            with _wk1_tabs_n[0]:
                st.markdown(
                    '<div style="background:#fef9c3;padding:7px 10px;border-radius:6px;'
                    'font-size:11px;color:#92400e;line-height:1.4;margin-bottom:8px;">'
                    '<b>🤖 AI 가이드:</b> 인기작·장르 선택형 첫 콘텐츠 제안으로 첫 재생 장벽을 낮춥니다.</div>',
                    unsafe_allow_html=True,
                )
                _send_btn(
                    "wk1_3d_n", "wk1_3d_sent_n", "웰컴 큐레이션 발송", len(_wk1_3d),
                    preview="안녕하세요 고객님  가입하셨는데 아직 첫 작품을 못 고르셨군요!<br>"
                            "고객님 취향에 딱 맞는 드라마를 골라뒀어요. 지금 바로 시작해보세요 ",
                )
                st.markdown('<div style="height:62px"></div>', unsafe_allow_html=True)
            with _wk1_tabs_n[1]:
                st.markdown(
                    '<div style="background:#fee2e2;padding:7px 10px;border-radius:6px;'
                    'font-size:11px;color:#991b1b;line-height:1.4;margin-bottom:8px;">'
                    '<b>🤖 AI 가이드:</b> S6 휴면군 예비 — 첫 재생 장벽 제거 우선. 인기 콘텐츠로 진입 메시지를 생성합니다. 쿠폰·할인보다 시청 경험이 먼저입니다.</div>',
                    unsafe_allow_html=True,
                )
                _send_btn(
                    "wk1_7d_n", "wk1_7d_sent_n", "첫 시청 진입 유도 발송", len(_wk1_7d),
                    preview="고객님, 가입하신 지 벌써 일주일이 됐어요 <br>"
                            "아직 첫 작품을 못 보셨군요. 지금 가장 인기 있는 작품 한 편만 보시면 완전 달라질 거예요! ",
                )
                st.markdown('<div style="height:62px"></div>', unsafe_allow_html=True)

        with _nc2:
            _cr_zero_n = _wk2_zero["is_churn"].mean() * 100 if len(_wk2_zero) > 0 else 0.0
            with st.container(border=True):
                st.markdown(
                    f'<div style="padding:4px 0 8px 0;">'
                    f'<div style="font-weight:800;font-size:16px;color:#1e293b;margin-bottom:4px;">Week 2. 이탈 조기 신호 포착</div>'
                    f'<div style="font-size:12px;color:#64748b;margin-bottom:12px;">w1 시청량으로 w2 유지 여부 조기 감지 (Day 7~14)</div>'
                    f'<div style="display:flex;flex-direction:column;gap:6px;">'
                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;">'
                    f'<div><div style="font-size:12px;font-weight:700;color:#1a1a1a;"> w2 약화 감지 가능군 (w1&gt;0)</div>'
                    f'<div style="font-size:11px;color:#94a3b8;">{_w2act_sub} · 재구매자 +4.7분 / 이탈자 −132.4분</div></div>'
                    f'<div style="font-weight:700;font-size:14px;">{len(_wk2_act):,}명</div></div>'
                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;">'
                    f'<div><div style="font-size:12px;font-weight:700;color:#1a1a1a;"> 소비미형성 지속군 (w1=0)</div>'
                    f'<div style="font-size:11px;color:#94a3b8;">이탈률 {_cr_zero_n:.1f}% · 온보딩 재시도 필요</div></div>'
                    f'<div style="font-weight:700;font-size:14px;">{len(_wk2_zero):,}명</div></div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(_div_dark, unsafe_allow_html=True)
                _wk2_tabs_n = st.tabs([" w2 약화 감지 가능군", " 소비미형성 지속"])
            with _wk2_tabs_n[0]:
                st.markdown(
                    '<div style="background:#fef9c3;padding:7px 10px;border-radius:6px;'
                    'font-size:11px;color:#92400e;line-height:1.4;margin-bottom:8px;">'
                    '<b>🤖 AI 가이드:</b> w2-w1 변화량 감지 즉시 단발 1회 메시지. 보던 작품 기반 이어보기를 제안합니다. 인센티브 없이 콘텐츠 중심으로만.</div>',
                    unsafe_allow_html=True,
                )
                _send_btn(
                    "wk2_act_s1_n", "wk2_mid_step_n", "이어보기 기반 단발 메시지", len(_wk2_act),
                    preview="고객님, 지난번 보시던 작품 기억하세요? <br>"
                            "다음 편이 기다리고 있어요. 지금 이어보기 하시겠어요?",
                )
            with _wk2_tabs_n[1]:
                st.markdown(
                    '<div style="background:#fee2e2;padding:7px 10px;border-radius:6px;'
                    'font-size:11px;color:#991b1b;line-height:1.4;margin-bottom:8px;">'
                    '<b>🤖 AI 가이드:</b> 선호 장르 기반 첫 콘텐츠 진입 유도 — 쿠폰보다 시청 경험이 우선입니다.</div>',
                    unsafe_allow_html=True,
                )
                _send_btn(
                    "wk2_zero_s1_n", "wk2_zero_sent_n", "온보딩 큐레이션 발송", len(_wk2_zero),
                    preview="고객님, 아직 첫 작품을 못 보셨나요? <br>"
                            "딱 10분이면 충분해요! 고객님 연령대에서 가장 인기 있는 작품 1화를 지금 바로 시작해보세요 ",
                )

        with _nc3:
            _cr_w3low_n  = _wk3_low["is_churn"].mean()  * 100 if len(_wk3_low)  > 0 else 0.0
            _cr_w3zero_n = _wk3_zero["is_churn"].mean() * 100 if len(_wk3_zero) > 0 else 0.0
            with st.container(border=True):
                st.markdown(
                    f'<div style="padding:4px 0 8px 0;">'
                    f'<div style="font-weight:800;font-size:16px;color:#1e293b;margin-bottom:4px;">Week 3. 세그먼트 예비 분류 · 결제 유지 방어</div>'
                    f'<div style="font-size:12px;color:#64748b;margin-bottom:12px;">w1+w2 누적 기반 예비 분류 — Day 21 세그먼트 확정</div>'
                    f'<div style="display:flex;flex-direction:column;gap:6px;">'
                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;">'
                    f'<div><div style="font-size:12px;font-weight:700;color:#1a1a1a;"> 소비형성 유력군 (w1+w2≥119분)</div>'
                    f'<div style="font-size:11px;color:#94a3b8;">{_w3hi_sub}</div></div>'
                    f'<div style="font-weight:700;font-size:14px;">{len(_wk3_hi):,}명</div></div>'
                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;">'
                    f'<div><div style="font-size:12px;font-weight:700;color:#1a1a1a;"> S5 저관여 예비군 (0&lt;w1+w2&lt;119분)</div>'
                    f'<div style="font-size:11px;color:#94a3b8;">이탈률 {_cr_w3low_n:.1f}% · 탐색 폭 확대 필요</div></div>'
                    f'<div style="font-weight:700;font-size:14px;">{len(_wk3_low):,}명</div></div>'
                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;">'
                    f'<div><div style="font-size:12px;font-weight:700;color:#1a1a1a;"> S6 휴면군 예비 (w1+w2=0)</div>'
                    f'<div style="font-size:11px;color:#94a3b8;">이탈률 {_cr_w3zero_n:.1f}% · 마지막 개입 기회</div></div>'
                    f'<div style="font-weight:700;font-size:14px;">{len(_wk3_zero):,}명</div></div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(_div_dark, unsafe_allow_html=True)
                _wk3_tabs_n = st.tabs([" 소비형성 유력군 (S1~S3 예비)", " S5 저관여 예비", " S6 휴면군 예비"])
            with _wk3_tabs_n[0]:
                st.markdown(
                    '<div style="background:#ede9fe;padding:7px 10px;border-radius:6px;'
                    'font-size:11px;color:#5b21b6;line-height:1.4;margin-bottom:8px;">'
                    '<b>🤖 AI 가이드:</b> 소비형성 예비군 — 이어볼 콘텐츠 리스트와 신작 알림으로 w3 시청량을 확보합니다.</div>',
                    unsafe_allow_html=True,
                )
                _send_btn(
                    "wk3_hi_n", "wk3_hi_sent_n", "이어볼 콘텐츠 리스트 + 신작 알림 발송", len(_wk3_hi),
                    preview="고객님, 보시던 작품 다음 편과 새로 나온 시리즈가 기다리고 있어요! <br>"
                            "취향에 맞는 콘텐츠를 골라봤어요. 지금 바로 확인해보세요 ",
                )
            with _wk3_tabs_n[1]:
                st.markdown(
                    '<div style="background:#fee2e2;padding:7px 10px;border-radius:6px;'
                    'font-size:11px;color:#991b1b;line-height:1.4;margin-bottom:8px;">'
                    '<b>🤖 AI 가이드:</b> S5 저관여 예비 — 낮은 장벽 콘텐츠와 다양한 장르 큐레이션으로 유효 시청을 형성합니다.</div>',
                    unsafe_allow_html=True,
                )
                _send_btn(
                    "wk3_low_s1_n", "wk3_low_step_n", "장르 다양성 탐색 추천", len(_wk3_low),
                    preview="고객님, 아직 못 보신 장르가 많아요! <br>"
                            "다양한 장르를 조금씩 경험해보시면 딱 맞는 작품을 찾을 수 있어요.",
                )
            with _wk3_tabs_n[2]:
                st.markdown(
                    '<div style="background:#f1f5f9;padding:7px 10px;border-radius:6px;'
                    'font-size:11px;color:#475569;line-height:1.4;margin-bottom:8px;">'
                    '<b>🤖 AI 가이드:</b> S6 휴면군 예비 — 시청 이력 있는 고객에게는 1단계(복귀 메시지), 무시청 고객에게는 2단계(인기작 온보딩). 운영자가 직접 선택. 쿠폰 없이 콘텐츠로만.</div>',
                    unsafe_allow_html=True,
                )
                _step_btns(
                    "wk3_zero_step_n", "wk3_zero_s1_n", "wk3_zero_s2_n",
                    "시청 이력 기반 복귀 메시지",
                    "인기작 온보딩 메시지",
                    len(_wk3_zero),
                    preview1="고객님, 예전에 보시던 작품 기억하시나요? <br>"
                             "그 작품과 비슷한 콘텐츠가 기다리고 있어요. 지금 돌아오세요!",
                    preview2="고객님, 아직 첫 작품을 못 보셨군요! <br>"
                             "지금 가장 인기 있는 작품으로 시작해보세요. 입문자에게 딱 맞는 콘텐츠를 골라드렸어요.",
                )

    # ── 서브탭 B: 세그먼트 처방 ──────────────────────────────────────────────
    with _crm_sub2:

        # ── 오늘 처방 우선순위 (Tab 1 고위험군 연동) ─────────────────────────
        _priority_df    = _n7_df[_n7_df["churn_score"] >= 40] if _N7_TOTAL > 0 else df.iloc[:0]
        _priority_total = len(_priority_df)

        if _priority_total == 0:
            st.info("향후 7일 이내 처방 우선순위 고객이 없습니다. 기준일을 앞으로 이동해보세요.")
        else:
            _pri_seg = (
                _priority_df["segment"].value_counts()
                .reset_index()
                .rename(columns={"index": "segment", "segment": "segment", "count": "count"})
            )
            _pri_seg.columns = ["segment", "count"]
            _seg_risk_order = ["S6 휴면군", "S3 초기관심", "S5 저관여",
                               "S2 이용약화", "S4 늦은활성", "S1 유지보호"]
            _pri_seg["_ord"] = _pri_seg["segment"].map(
                {s: i for i, s in enumerate(_seg_risk_order)}
            )
            _pri_seg = _pri_seg.sort_values("_ord").reset_index(drop=True)

            _pc1, _pc3 = st.columns([2, 3])
            with _pc1:
                fig_donut = go.Figure(go.Pie(
                    labels=_pri_seg["segment"].tolist(),
                    values=_pri_seg["count"].tolist(),
                    hole=0.5,
                    marker=dict(
                        colors=[SEG_META.get(s, {"color": "#94a3b8"})["color"] for s in _pri_seg["segment"]],
                    ),
                    textinfo="percent",
                    textfont=dict(size=10),
                    hovertemplate="%{label}<br>%{value:,}명 (%{percent})<extra></extra>",
                ))
                fig_donut.update_layout(
                    height=200,
                    margin=dict(t=25, b=5, l=5, r=5),
                    title=dict(text="고위험군 세그먼트 분포", font=dict(size=10, color="#555"), y=0.98),
                    showlegend=False,
                    annotations=[dict(
                        text=f"<b>{_priority_total:,}</b><br><span style='font-size:11px'>고위험</span>",
                        x=0.5, y=0.5,
                        font=dict(size=13, color="#1a1a1a"),
                        showarrow=False,
                    )],
                )
                st.plotly_chart(fig_donut, use_container_width=True, key="donut_priority")
            with _pc3:
                _bar_rows = []
                for _bseg in ["S6 휴면군", "S3 초기관심", "S5 저관여",
                              "S2 이용약화", "S4 늦은활성", "S1 유지보호"]:
                    _bsm = _n7_df[_n7_df["segment"] == _bseg] if _N7_TOTAL > 0 else df.iloc[:0]
                    if len(_bsm) == 0:
                        continue
                    _bar_rows.append({
                        "seg":  _bseg,
                        "고위험": int((_bsm["churn_score"] >= 40).sum()),
                        "위험":   int(((_bsm["churn_score"] >= 20) & (_bsm["churn_score"] < 40)).sum()),
                        "안전":   int((_bsm["churn_score"] < 20).sum()),
                    })
                if _bar_rows:
                    _bd = pd.DataFrame(_bar_rows).iloc[::-1].reset_index(drop=True)
                    fig_stack = go.Figure()
                    _tot = _bd["고위험"] + _bd["위험"] + _bd["안전"]
                    for _tier, _clr in [("고위험", "#ef4444"), ("위험", "#f59e0b"), ("안전", "#22c55e")]:
                        _pct = (_bd[_tier] / _tot.replace(0, 1) * 100).round(1)
                        _cd  = np.column_stack([_pct.values, _bd[_tier].values, _tot.values])
                        fig_stack.add_trace(go.Bar(
                            name=_tier, y=_bd["seg"], x=_bd[_tier],
                            orientation="h", marker_color=_clr, opacity=0.85,
                            customdata=_cd,
                            hovertemplate=(
                                f"{_tier}: %{{customdata[1]:,.0f}}명 (%{{customdata[0]:.1f}}%)"
                                f"<extra></extra>"
                            ),
                        ))
                    fig_stack.update_layout(
                        barmode="stack", hovermode="y unified",
                        height=210, plot_bgcolor="white",
                        margin=dict(t=30, b=40, l=5, r=10),
                        title=dict(text=f"세그먼트별 위험 구성 ({sel_date.strftime('%m/%d')} 향후 7일)",
                                   font=dict(size=10, color="#555"), y=0.98),
                        legend=dict(orientation="h", y=-0.18, x=0.5,
                                    xanchor="center", font=dict(size=9),
                                    traceorder="normal"),
                        xaxis=dict(gridcolor="#f0f0f0", title=""),
                        yaxis=dict(title=""),
                    )
                    st.plotly_chart(fig_stack, use_container_width=True, key="stack_priority")
                else:
                    st.info("향후 7일 만기 데이터가 없습니다.")
            st.caption(
                f"⬇ 아래 세그먼트 처방에서 해당 세그먼트를 바로 실행하세요 · "
                f"기준일: {sel_date.strftime('%m/%d')} 향후 7일 만기 예정 고위험"
            )

        st.markdown(
            " 세그먼트별 CRM 처방 · 21일 완료 코호트 기준 · 위험도 높은 순 정렬"
            "&nbsp;&nbsp;&nbsp;<span style='color:#bbb;font-size:11px;'>",
            unsafe_allow_html=True,
        )


        def _seg_card(seg):
            _all_m   = seg_masks[seg]
            m        = _all_m[_all_m["reg_date_d"] <= _pred_cut]
            if len(m) == 0:
                m = _all_m
            meta     = SEG_META.get(seg, {"risk": "", "color": "#94a3b8", "rx": "", "action": seg, "feat": ""})
            cr       = m["is_churn"].mean() * 100 if len(m) > 0 else 0.0
            m_hi     = m[m["churn_score"] >= 40]
            _hi_pct  = len(m_hi) / max(len(m), 1) * 100
            _acts    = SEG_ACTIONS.get(seg, {})
            _pfx     = _acts.get("prefix", seg.replace(" ", "_"))
            # 코호트 필터에 따라 버튼 분기 (전체/프로모션 → promo, 정가 → nonpromo)
            _is_promo = cohort_opt == "프로모션 유입"
            _cohort_key = "p" if _is_promo else "n"
            _cohort_label = " 프로모션" if _is_promo else " 정가"
            _btns = _acts.get(
                "btns_promo" if _is_promo else "btns_nonpromo",
                [f" {meta['action']}"],
            )
            # 모든 버튼은 세그먼트 전체를 대상으로 (tier 필터 없음)
            _tier_dfs  = [m] * len(_btns)
            _tier_data = [(len(m), "전체")] * len(_btns)

            # ── 샘플 메시지 생성 대기 처리 (버튼 클릭 다음 렌더 사이클) ─────
            for _bi in range(1, len(_btns) + 1):
                _bk_i     = f"rx_{_pfx}_{_cohort_key}_{_bi}"
                _gen_key  = f"{_bk_i}_gen"
                _samp_key = f"{_bk_i}_samples"
                if _gen_key in st.session_state:
                    _gd = st.session_state.pop(_gen_key)
                    with st.spinner(f"🤖 {seg} {_gd['tier']} 샘플 2명 AI 알람 문구 생성 중..."):
                        _slist = []
                        for _rd in _gd["rows"]:
                            try:
                                from tmdb import get_movies_by_genres, add_reasons
                                _uid_s   = str(_rd["USER_KEY"])[:6]
                                _age_s   = int(_rd["age_group"])
                                _g_s     = "M" if _rd.get("gender_kor") == "남성" else "F"
                                _days_s  = int(min(float(_rd.get("recency", 14)), 30))
                                _genre_s = _rd.get("_genre", "drama")
                                # 고객 장르 비율로 TMDB 추천 영화 조회
                                _genre_ratios = {
                                    "drama":    float(_rd.get("drama_ratio", 0)),
                                    "thriller": float(_rd.get("thriller_crime_ratio", 0)),
                                    "action":   float(_rd.get("action_adventure_ratio", 0)),
                                    "romance":  float(_rd.get("romance_ratio", 0)),
                                }
                                _movies = get_movies_by_genres(
                                    _genre_ratios, customer_key=str(_rd["USER_KEY"])
                                )
                                _movies = add_reasons(_movies, _genre_s, _age_s, _g_s)
                                _top_movie  = _movies[0]["title"] if _movies else ""
                                _action_ctx = _gd.get("action", "")
                                _seg_ctx    = _gd.get("seg", "")
                                _gender_kor = "여성" if _g_s == "F" else "남성"
                                _movie_part = f"\n추천 영화: 【{_top_movie}】" if _top_movie else ""
                                from agent import _llm as _gen_llm
                                _msg_s = _gen_llm(0.7).invoke(
                                    f"OTT CRM 마케터로서 아래 고객에게 맞는 이탈 방지 문자를 작성해주세요.\n"
                                    f"고객: {_uid_s}… | {_age_s}대 {_gender_kor} | 미접속 {_days_s}일 | 선호장르: {_genre_s}\n"
                                    f"세그먼트: {_seg_ctx}{_movie_part}\n"
                                    f"CRM 액션: {_action_ctx}\n\n"
                                    "규칙: CRM 액션 목적에 맞는 문구를 작성하세요. "
                                    "영화 제목이 있으면 반드시 포함하고 '영화'로만 표현(드라마·시리즈 금지). "
                                    "2~3문장, 이모지 1~2개, 친근하고 짧게, 마크다운 기호·번호 없이 순수 텍스트로만."
                                ).content
                                _slist.append({
                                    "uid":    _uid_s,
                                    "age":    _age_s,
                                    "gender": _rd.get("gender_kor", "미상"),
                                    "genre":  _genre_s,
                                    "msg":    _msg_s,
                                    "tier":   _gd["tier"],
                                    "score":  round(float(_rd.get("churn_score", 0)), 1),
                                    "movies": _movies,
                                })
                            except Exception as _e:
                                _slist.append({
                                    "uid":    str(_rd.get("USER_KEY", ""))[:6],
                                    "msg":    f"메시지 생성 실패: {_e}",
                                    "tier":   _gd["tier"],
                                    "score":  0, "age": 0, "gender": "", "genre": "",
                                    "movies": [],
                                })
                    st.session_state[_samp_key] = _slist
                    st.rerun()

            st.markdown(
                f'<div style="background:#fff;border:1px solid #e2e8f0;'
                f'border-radius:10px;padding:12px 14px;'
                f'border-top:3px solid {meta["color"]};">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<div style="font-weight:800;font-size:13px;color:{meta["color"]};">{seg}</div>'
                f'<div style="font-size:10px;color:#888;background:#f1f5f9;'
                f'border-radius:4px;padding:2px 6px;">{_cohort_label} 전략</div>'
                f'</div>'
                f'<div style="font-size:11px;color:#555;margin-top:6px;">'
                f'전체 {len(m):,}명 · 이탈률 {cr:.1f}% · '
                f'고위험 {len(m_hi):,}명({_hi_pct:.0f}%)</div>'
                f'<div style="font-size:11px;color:#1a1a1a;margin-top:5px;line-height:1.55;">'
                f'{_acts.get("desc", meta["feat"])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            _btn_cols = st.columns(len(_btns))
            for i, (btn_label, (tier_cnt, _), _bcol) in enumerate(
                zip(_btns, _tier_data, _btn_cols), 1
            ):
                with _bcol:
                    _bk       = f"rx_{_pfx}_{_cohort_key}_{i}"
                    _gen_key  = f"{_bk}_gen"
                    _samp_key = f"{_bk}_samples"
                    _action   = btn_label.lstrip("①②③ ")
                    _lbl      = f"{i}. {_action}"
                    if st.button(_lbl, key=_bk, use_container_width=True,
                                 type="secondary", disabled=(tier_cnt == 0)):
                        now = datetime.datetime.now().strftime("%H:%M")
                        st.session_state["action_log"][_bk] = (tier_cnt, now)
                        st.session_state["budget_used"] += (
                            2000 if "쿠폰" in btn_label else 15
                        ) * tier_cnt
                        if tier_cnt > 0:
                            _tdf  = _tier_dfs[i - 1]
                            _samp = _tdf.sample(min(2, len(_tdf)))
                            _rows = []
                            for _, _row in _samp.iterrows():
                                _rd = _row.to_dict()
                                _rd["_genre"] = top_genre(_row)
                                _rows.append(_rd)
                            st.session_state[_gen_key] = {
                                "tier": _tier_data[i - 1][1],
                                "rows": _rows,
                                "action": btn_label,
                                "seg": seg,
                            }
                        st.rerun()
                    if _bk in st.session_state["action_log"]:
                        c, t = st.session_state["action_log"][_bk]
                        st.markdown(
                            f'<div style="font-size:10px;color:#388e3c;text-align:center;">'
                            f' {c:,}명 · {t}</div>',
                            unsafe_allow_html=True,
                        )

            # ── 프로모션 오버레이 (프로모션 코호트 선택 시에만) ─────────────
            if _is_promo and _acts.get("promo_overlay"):
                st.markdown(
                    f'<div style="background:#fff8e1;border:1px solid #fde68a;'
                    f'border-radius:6px;padding:8px 12px;margin-top:8px;'
                    f'font-size:12px;color:#92400e;line-height:1.6;'
                    f'box-shadow:0 2px 6px rgba(0,0,0,0.07);">'
                    f'{_acts["promo_overlay"]}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # ── 샘플 알람 문구 표시 ──────────────────────────────────────────
            for i in range(1, len(_btns) + 1):
                _bk       = f"rx_{_pfx}_{_cohort_key}_{i}"
                _samp_key = f"{_bk}_samples"
                if _samp_key in st.session_state and st.session_state[_samp_key]:
                    _sl       = st.session_state[_samp_key]
                    _tier_n   = _sl[0].get("tier", f"버튼 {i}")
                    _btn_name = _btns[i - 1].lstrip("①②③ ") if i <= len(_btns) else ""
                    with st.expander(
                        f"🤖 샘플 알람 미리보기 — {_btn_name} ({_tier_n} 2명)",
                        expanded=True,
                    ):
                        for _s in _sl:
                            _safe = _html.escape(_s.get("msg", "")).replace("\n", "<br>")
                            st.markdown(
                                f'<div style="background:#f8fafc;'
                                f'border-left:3px solid #f59e0b;border-radius:8px;'
                                f'padding:12px 14px;margin-bottom:8px;">'
                                f'<div style="font-size:11px;color:#64748b;margin-bottom:6px;">'
                                f'👤 {_s.get("uid", "")}… · {_s.get("age", "")}대 '
                                f'{_s.get("gender", "")} · {_s.get("genre", "")} · '
                                f'이탈위험 {_s.get("score", 0)}점 · {_tier_n}</div>'
                                f'<div style="font-size:13px;line-height:1.8;color:#1a1a1a;">'
                                f'{_safe}</div></div>',
                                unsafe_allow_html=True,
                            )

        def _seg_chart(seg):
            _all_m = seg_masks[seg]
            m      = _all_m[_all_m["reg_date_d"] <= _pred_cut]
            if len(m) == 0:
                m = _all_m
            m_hi = m[m["churn_score"] >= 40]
            m_lo = m[m["churn_score"] <  20]
            if len(m_hi) == 0:
                st.info("고위험군 데이터가 없습니다.")
                return

            # ── 레이더 차트 (5각형, 클수록 좋음 통일) ──────────────────────
            # (lbl, col, is_pct, invert) — invert=True: av/hv로 뒤집어 클수록 좋게
            _radar_cfg = [
                ("활성비율",   "active_ratio",          True,  False),
                ("장르다양성", "genre_diversity_count", False, False),
                ("고유영화수", "unique_movie",          False, False),
                ("시청 지속률", "watch_ratio_under_5m", True,  True),
                ("최근 접속도", "recency",              False, True),
            ]
            _n_axes = len(_radar_cfg)
            _r_labels, _h_scores, _s_scores = [], [], []
            _h_vals, _s_vals, _a_vals = [], [], []
            for lbl, col, is_pct, invert in _radar_cfg:
                _r_labels.append(lbl)
                mul = 100 if is_pct else 1
                hv = m_hi[col].mean() * mul if col in m_hi.columns else 0.0
                sv = m_lo[col].mean() * mul if col in m_lo.columns and len(m_lo) > 0 else 0.0
                _df_p = df[df["reg_date_d"] <= _pred_cut]
                av = _df_p[col].mean() * mul if col in _df_p.columns else 1.0
                _h_vals.append(hv); _s_vals.append(sv); _a_vals.append(av)
                if invert:
                    _h_scores.append(min(av / hv if hv > 0 else 2.0, 2.0))
                    _s_scores.append(min(av / sv if sv > 0 else 2.0, 2.0))
                else:
                    _h_scores.append(min(hv / av if av > 0 else 1.0, 2.0))
                    _s_scores.append(min(sv / av if av > 0 else 1.0, 2.0))
            _rl = _r_labels + [_r_labels[0]]
            _hs = _h_scores + [_h_scores[0]]
            _ss = _s_scores + [_s_scores[0]]

            _h_cd = [[f"{_h_vals[i]:.2f}", f"{_a_vals[i]:.2f}", f"{_h_scores[i]:.2f}x"]
                     for i in range(_n_axes)] + [[f"{_h_vals[0]:.2f}", f"{_a_vals[0]:.2f}", f"{_h_scores[0]:.2f}x"]]
            _s_cd = [[f"{_s_vals[i]:.2f}", f"{_a_vals[i]:.2f}", f"{_s_scores[i]:.2f}x"]
                     for i in range(_n_axes)] + [[f"{_s_vals[0]:.2f}", f"{_a_vals[0]:.2f}", f"{_s_scores[0]:.2f}x"]]

            fig_radar = go.Figure()
            # 전체 평균 (회색, 선만)
            fig_radar.add_trace(go.Scatterpolar(
                r=[1.0]*7, theta=_rl, fill=None, name=" 전체 평균",
                line=dict(color="#94a3b8", width=1.5, dash="dash"),
                hovertemplate="<b>%{theta}</b><br>전체 평균 (기준선 1.0x)<extra></extra>",
            ))
            # 안전군 (초록, 연한 채움)
            fig_radar.add_trace(go.Scatterpolar(
                r=_ss, theta=_rl, fill="toself", name=" 안전군",
                line=dict(color="#22c55e", width=1.5, dash="dot"),
                fillcolor="rgba(34,197,94,0.1)",
                customdata=_s_cd,
                hovertemplate="<b>%{theta}</b><br>안전군: %{customdata[0]}<br>전체 평균: %{customdata[1]}<br>평균 대비: %{customdata[2]}<extra></extra>",
            ))
            # 고위험군 (빨강, 강한 채움)
            fig_radar.add_trace(go.Scatterpolar(
                r=_hs, theta=_rl, fill="toself", name=" 고위험군",
                line=dict(color="#ef4444", width=2),
                fillcolor="rgba(239,68,68,0.18)",
                customdata=_h_cd,
                hovertemplate="<b>%{theta}</b><br>고위험군: %{customdata[0]}<br>전체 평균: %{customdata[1]}<br>평균 대비: %{customdata[2]}<extra></extra>",
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(
                    visible=True, range=[0, 2.0],
                    tickvals=[0.5, 1.0, 1.5, 2.0],
                    ticktext=["0.5x", "1.0x", "1.5x", "2.0x"],
                    tickfont=dict(size=8), gridcolor="#e2e8f0",
                )),
                height=250, margin=dict(t=20, b=50, l=40, r=40),
                legend=dict(orientation="h", y=-0.12, x=0.5,
                            xanchor="center", font=dict(size=9)),
                showlegend=True,
            )
            st.plotly_chart(fig_radar, use_container_width=True, key=f"radar_{seg}")

            # ── 주차별 시청시간 | 1주차만 시청 비율 ───────────────────────
            _weeks   = ["1주차", "2주차", "3주차"]
            _w_cols  = ["watch_time_min_w1", "watch_time_min_w2", "watch_time_min_w3"]
            _hi_mean = [m_hi[c].mean() for c in _w_cols]
            _lo_mean = [m_lo[c].mean() if len(m_lo) > 0 else 0.0 for c in _w_cols]
            _df_p    = df[df["reg_date_d"] <= _pred_cut]
            _av_mean = [_df_p[c].mean() for c in _w_cols]

            # 1주차만 시청: 세그먼트 고위험 vs 전체 안전군 (동일 pred_cut 필터)
            _df_safe = _df_p[_df_p["churn_score"] < 20]
            _h_w1 = m_hi["is_only_w1"].mean() * 100 if "is_only_w1" in m_hi.columns else 0.0
            _s_w1 = _df_safe["is_only_w1"].mean() * 100 if "is_only_w1" in _df_safe.columns and len(_df_safe) > 0 else 0.0

            _sl, _sr = st.columns([3, 2])
            with _sl:
                fig_cmp = go.Figure()
                fig_cmp.add_trace(go.Bar(
                    name=" 고위험", x=_weeks, y=_hi_mean,
                    marker_color="#ef4444", opacity=0.8,
                    text=[f"{v:.0f}분" for v in _hi_mean], textposition="outside",
                ))
                fig_cmp.add_trace(go.Bar(
                    name=" 안전군", x=_weeks, y=_lo_mean,
                    marker_color="#22c55e", opacity=0.8,
                    text=[f"{v:.0f}분" for v in _lo_mean], textposition="outside",
                ))
                fig_cmp.add_trace(go.Scatter(
                    name=" 전체 평균", x=_weeks, y=_av_mean,
                    mode="lines+markers",
                    line=dict(color="#94a3b8", width=2, dash="dot"),
                    marker=dict(size=6, color="#94a3b8"),
                    hovertemplate="전체 평균: %{y:.0f}분<extra></extra>",
                ))
                _ym = max(max(_hi_mean), max(_lo_mean), max(_av_mean), 1) * 1.5
                fig_cmp.update_layout(
                    barmode="group", height=220, plot_bgcolor="white",
                    margin=dict(t=30, b=5, l=30, r=5),
                    title=dict(text="주차별 평균 시청시간 (분)", font_size=11, y=0.98),
                    legend=dict(orientation="h", y=1.1, x=0, font=dict(size=9)),
                    yaxis=dict(gridcolor="#f0f0f0", visible=False, range=[0, _ym]),
                    xaxis=dict(title="", tickfont=dict(size=10)), bargap=0.3,
                )
                st.plotly_chart(fig_cmp, use_container_width=True, key=f"cmp_{seg}")
            with _sr:
                _w1ratio = _h_w1 / _s_w1 if _s_w1 > 0 else 0
                fig_w1 = go.Figure()
                fig_w1.add_trace(go.Bar(
                    x=[" 고위험\n(세그먼트)", " 전체\n안전군"],
                    y=[_h_w1, _s_w1],
                    marker_color=["#ef4444", "#22c55e"], opacity=0.85,
                    text=[f"{_h_w1:.1f}%", f"{_s_w1:.1f}%"], textposition="outside",
                    textfont=dict(size=11, color=["#ef4444", "#22c55e"]),
                    width=[0.4, 0.4],
                ))
                if _w1ratio > 0:
                    fig_w1.add_annotation(
                        x=0.5, y=max(_h_w1, _s_w1, 1) * 1.12, xref="paper",
                        text=f"<b>{_w1ratio:.0f}배 차이</b>", showarrow=False,
                        font=dict(size=11, color="#ef4444"),
                        bgcolor="rgba(255,245,245,0.9)",
                        bordercolor="#ef4444", borderwidth=1, borderpad=3,
                    )
                fig_w1.update_layout(
                    height=220, plot_bgcolor="white", showlegend=False,
                    margin=dict(t=30, b=5, l=5, r=5),
                    title=dict(text=" 1주차만 시청 비율 (%)", font_size=11, y=0.98),
                    yaxis=dict(gridcolor="#f0f0f0", visible=False,
                               range=[0, max(_h_w1, _s_w1, 1) * 1.5]),
                    xaxis=dict(title="", tickfont=dict(size=10)),
                )
                st.plotly_chart(fig_w1, use_container_width=True, key=f"w1_{seg}")

        # ── 상단: 최고위험 2개 (큰 카드) ─────────────────────────────────────
        _top_l, _top_r = st.columns(2)
        for _col, _seg in zip([_top_l, _top_r], ["S6 휴면군", "S3 초기관심"]):
            with _col:
                _seg_card(_seg)
                with st.expander(" 시청 추이 보기"):
                    _seg_chart(_seg)

        st.divider()

        # ── 하단: 나머지 4개 (2행 × 2열) ───────────────────────────────────
        for _row_segs in [["S5 저관여", "S2 이용약화"], ["S4 늦은활성", "S1 유지보호"]]:
            _rc1, _rc2 = st.columns(2)
            for _col, _seg in zip([_rc1, _rc2], _row_segs):
                with _col:
                    _seg_card(_seg)
                    with st.expander(" 시청 추이"):
                        _seg_chart(_seg)


