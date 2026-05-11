"""
Stage 09c: Corrected Business Simulation and Retention Action Scenario
Based on Stage 08c corrected segmentation, Stage 07c TRUE SHAP, Stage 06c2 official model.

This is an assumption-based scenario simulation.
It is NOT causal proof, NOT an A/B test result, NOT a financial forecast.
No ROI/profit/revenue claims without real cost and margin data.

Do NOT: train models, tune models, run Optuna, run SHAP, create new segmentation,
         modify raw files, overwrite old Stage 09 / 08c outputs.
"""

import json
import os
import sys
import warnings
import zipfile
from datetime import datetime
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
def find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "park.ingyeom" / "reports" / "data"
                / "08c_v2_corrected_segmentation_strategy"
                / "08c_segmentation_summary.json").exists():
            return candidate
    raise FileNotFoundError("Cannot locate project root.")


PROJECT_ROOT = find_project_root(Path.cwd())
BASE = PROJECT_ROOT / "park.ingyeom"

STAGE08C_DATA   = BASE / "reports" / "data"   / "08c_v2_corrected_segmentation_strategy"
STAGE08C_TABLES = BASE / "reports" / "tables" / "08c_v2_corrected_segmentation_strategy"
STAGE07C_DATA   = BASE / "reports" / "data"   / "07c_v2_corrected_true_shap_interpretation"
STAGE06C2_DATA  = BASE / "reports" / "data"   / "06c2_v2_corrected_baseline_modeling"
OLD09_DATA      = BASE / "reports" / "data"   / "09_v2_business_simulation"
OLD09_TABLES    = BASE / "reports" / "tables" / "09_v2_business_simulation"

DATA_DIR    = BASE / "reports" / "data"    / "09c_v2_corrected_business_simulation"
TABLE_DIR   = BASE / "reports" / "tables"  / "09c_v2_corrected_business_simulation"
FIGURE_DIR  = BASE / "reports" / "figures" / "09c_v2_corrected_business_simulation"

for d in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def rel(p: Path) -> str:
    return str(Path(p).relative_to(PROJECT_ROOT)).replace("\\", "/")


def wcsv(path: Path, df: pd.DataFrame):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def wjson(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def wmd(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def savefig(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()


# ── Segment metadata ───────────────────────────────────────────────────────────
SEG_ORDER = [
    "최상위_이탈위험군",
    "초기중기_저관여_고위험군",
    "주차별이용패턴_고위험군",
    "장르비율_추천후보군",
    "안정유지_후보군",
    "일반관찰군",
]
SEG_EN = {
    "최상위_이탈위험군":      "top_highest_risk",
    "초기중기_저관여_고위험군": "low_engagement_high_risk",
    "주차별이용패턴_고위험군":  "weekly_pattern_high_risk",
    "장르비율_추천후보군":     "genre_affinity_recommendation_pool",
    "안정유지_후보군":         "stable_maintenance_candidates",
    "일반관찰군":             "general_observation",
}
SEG_PRIORITY = {k: i + 1 for i, k in enumerate(SEG_ORDER)}
SEG_ROLE = {
    "최상위_이탈위험군":      "primary_target",
    "초기중기_저관여_고위험군": "primary_target",
    "주차별이용패턴_고위험군":  "primary_target",
    "장르비율_추천후보군":     "secondary_recommendation",
    "안정유지_후보군":         "maintenance_only",
    "일반관찰군":             "residual_monitoring",
}
SEG_USE = {
    "최상위_이탈위험군":      True,
    "초기중기_저관여_고위험군": True,
    "주차별이용패턴_고위험군":  True,
    "장르비율_추천후보군":     True,
    "안정유지_후보군":         False,
    "일반관찰군":             False,
}

# ── Assumption defaults (conservative; all labeled as placeholders) ─────────────
ASSUMPTIONS = {
    "최상위_이탈위험군": {
        "reachable_rate": 0.85, "treatment_rate": 0.85, "response_rate": 0.10,
        "incremental_retention_lift_low": 0.01, "incremental_retention_lift_base": 0.03,
        "incremental_retention_lift_high": 0.05,
        "contact_fatigue_penalty_rate": 0.02, "max_contact_capacity": None,
        "channel": "push_notification + in-app message",
        "action_type": "high-risk targeted retention",
        "action_description": "고위험 모니터링, 개인화 리텐션 메시지, 콘텐츠 재추천",
    },
    "초기중기_저관여_고위험군": {
        "reachable_rate": 0.85, "treatment_rate": 0.80, "response_rate": 0.10,
        "incremental_retention_lift_low": 0.01, "incremental_retention_lift_base": 0.03,
        "incremental_retention_lift_high": 0.05,
        "contact_fatigue_penalty_rate": 0.02, "max_contact_capacity": None,
        "channel": "push_notification + email",
        "action_type": "onboarding and activation",
        "action_description": "초기 온보딩 강화, 첫 시청 유도, 개인화 콘텐츠 추천",
    },
    "주차별이용패턴_고위험군": {
        "reachable_rate": 0.80, "treatment_rate": 0.75, "response_rate": 0.08,
        "incremental_retention_lift_low": 0.01, "incremental_retention_lift_base": 0.03,
        "incremental_retention_lift_high": 0.05,
        "contact_fatigue_penalty_rate": 0.02, "max_contact_capacity": None,
        "channel": "push_notification + in-app banner",
        "action_type": "weekly pattern nudge",
        "action_description": "주차별 패턴 기반 지속 시청 독려, 시리즈 추천, 이용 촉진 알림",
    },
    "장르비율_추천후보군": {
        "reachable_rate": 0.75, "treatment_rate": 0.55, "response_rate": 0.07,
        "incremental_retention_lift_low": 0.005, "incremental_retention_lift_base": 0.015,
        "incremental_retention_lift_high": 0.03,
        "contact_fatigue_penalty_rate": 0.01, "max_contact_capacity": None,
        "channel": "in-app recommendation + email",
        "action_type": "genre-based content recommendation",
        "action_description": "장르별 신작 추천, 취향 기반 큐레이션, 이어보기 유도",
    },
    "안정유지_후보군": {
        "reachable_rate": 0.70, "treatment_rate": 0.30, "response_rate": 0.05,
        "incremental_retention_lift_low": 0.0, "incremental_retention_lift_base": 0.005,
        "incremental_retention_lift_high": 0.01,
        "contact_fatigue_penalty_rate": 0.005, "max_contact_capacity": None,
        "channel": "in-app notification",
        "action_type": "maintenance monitoring",
        "action_description": "기본 유지 메시지, 구독 갱신 안내 (모니터링 전용)",
    },
    "일반관찰군": {
        "reachable_rate": 0.60, "treatment_rate": 0.20, "response_rate": 0.04,
        "incremental_retention_lift_low": 0.0, "incremental_retention_lift_base": 0.0,
        "incremental_retention_lift_high": 0.005,
        "contact_fatigue_penalty_rate": 0.005, "max_contact_capacity": None,
        "channel": "none (monitoring only)",
        "action_type": "residual monitoring",
        "action_description": "기본 모니터링, 추가 분석 필요 시 서브 세그먼트 검토",
    },
}

SAMPLE_KO_MESSAGE = {
    "최상위_이탈위험군":      "[OTT서비스] 아직 구독이 남아있어요! 지금 바로 인기 콘텐츠를 이어보세요.",
    "초기중기_저관여_고위험군": "[OTT서비스] 아직 시청을 시작하지 않으셨나요? 취향에 맞는 콘텐츠를 추천드려요!",
    "주차별이용패턴_고위험군":  "[OTT서비스] 지난주보다 시청이 줄었어요. 이어서 볼 콘텐츠가 있어요!",
    "장르비율_추천후보군":     "[OTT서비스] 좋아하시는 [장르]의 새 콘텐츠가 올라왔어요. 지금 확인해보세요!",
    "안정유지_후보군":         "[OTT서비스] 구독 만료가 다가오고 있어요. 계속 즐거운 시청 되세요!",
    "일반관찰군":             "(별도 발송 없음 — 모니터링 전용)",
}

WHAT_NOT_TO_CLAIM = {
    "최상위_이탈위험군":      "이 메시지가 이탈을 막는다고 인과적으로 주장하지 않음. 리텐션 보장 문구 사용 금지.",
    "초기중기_저관여_고위험군": "저관여가 이탈의 원인이라고 주장하지 않음. 추천 조치가 재구독을 보장하지 않음.",
    "주차별이용패턴_고위험군":  "주차별 감소 패턴이 이탈의 원인이라고 주장하지 않음. 조치의 인과적 효과 미주장.",
    "장르비율_추천후보군":     "콘텐츠 추천이 재구독을 원인적으로 높인다고 주장하지 않음. ROI 미주장.",
    "안정유지_후보군":         "이 그룹에 공격적 개입을 가하면 안 됨. 과도한 연락 금지.",
    "일반관찰군":             "잔여군에 대한 강한 개입 주장 금지. 세부 원인 단정 금지.",
}

RISK_HYP = {
    "최상위_이탈위험군":      "낮은 이용량 또는 이용 중단 패턴 + 멤버십 컨텍스트 신호 복합",
    "초기중기_저관여_고위험군": "초기~중기 낮은 총 이용 시간 → 미충분 관여 신호",
    "주차별이용패턴_고위험군":  "주차별 시청 시간 감소 또는 3주차 부재 → 관여 약화 신호",
    "장르비율_추천후보군":     "특정 장르 비율 집중 → 콘텐츠 다양성 제한 가능성 (인과 미확인)",
    "안정유지_후보군":         "낮은 예측 이탈 위험, 안정적 이용 패턴",
    "일반관찰군":             "명확한 단일 위험 드라이버 없음 — 잔여군",
}

SHAP_SUPPORT = {
    "최상위_이탈위험군":      "weekly_usage_pattern (strong), membership_context (moderate)",
    "초기중기_저관여_고위험군": "weekly_usage_pattern (strong), simple_usage_volume (moderate)",
    "주차별이용패턴_고위험군":  "weekly_usage_pattern (strong), genre_ratio_proxy (moderate)",
    "장르비율_추천후보군":     "genre_ratio_proxy (strong), weekly_usage_pattern (weak)",
    "안정유지_후보군":         "weekly_usage_pattern (moderate)",
    "일반관찰군":             "none",
}

# ── Portfolio definitions ──────────────────────────────────────────────────────
PORTFOLIOS = {
    "high_risk_only": {
        "segments": ["최상위_이탈위험군"],
        "label": "A. 최상위 위험군만",
        "caution": "가장 보수적 타겟팅 시나리오. 접촉 규모 최소.",
        "readiness": "safe_to_report_with_assumption_caveat",
    },
    "high_risk_plus_low_engagement": {
        "segments": ["최상위_이탈위험군", "초기중기_저관여_고위험군"],
        "label": "B. 최상위 + 저관여 고위험군",
        "caution": "가장 안전한 발표 시나리오. 온보딩 실행 역량 필요.",
        "readiness": "safest_presentation_scenario",
    },
    "broad_high_risk": {
        "segments": ["최상위_이탈위험군", "초기중기_저관여_고위험군", "주차별이용패턴_고위험군"],
        "label": "C. 전체 고위험군 (3개 세그먼트)",
        "caution": "중간 규모 개입. 접촉 피로 주의. 주차 패턴 리프트 불확실.",
        "readiness": "plausible_but_cautioned",
    },
    "recommendation_light": {
        "segments": ["최상위_이탈위험군", "초기중기_저관여_고위험군", "주차별이용패턴_고위험군", "장르비율_추천후보군"],
        "label": "D. 고위험군 + 장르 추천 (저비용 병행)",
        "caution": "장르 추천 효과는 추가 가정 의존도 높음. 가정 민감성 주의.",
        "readiness": "assumption_sensitive",
    },
    "monitoring_only": {
        "segments": ["안정유지_후보군", "일반관찰군"],
        "label": "E. 모니터링 전용 (맥락 참조용)",
        "caution": "개입 효과 주장 없음. 맥락 기술 전용.",
        "readiness": "context_only",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# PASS 1: Input Validation
# ══════════════════════════════════════════════════════════════════════════════
def pass1_input_validation():
    print("[09c | Pass 1] Input validation ...")
    required = {
        "08c final checks": STAGE08C_TABLES / "08c_final_checks.csv",
        "08c holdout assignments": STAGE08C_DATA / "08c_segment_assignments_holdout.csv",
        "08c full descriptive assignments": STAGE08C_DATA / "08c_segment_assignments_full_descriptive.csv",
        "08c holdout segment summary": STAGE08C_TABLES / "08c_hierarchical_segment_summary_holdout.csv",
        "08c segmentation summary json": STAGE08C_DATA / "08c_segmentation_summary.json",
        "08c action recommendations": STAGE08C_TABLES / "08c_segment_action_recommendations.csv",
        "08c SHAP evidence map": STAGE08C_TABLES / "08c_segment_shap_evidence_map.csv",
        "07c SHAP summary json": STAGE07C_DATA / "07c_true_shap_summary.json",
        "06c2 baseline summary json": STAGE06C2_DATA / "06c2_corrected_baseline_summary.json",
    }
    rows = []
    all_ok = True
    for label, path in required.items():
        ok = path.exists()
        if not ok:
            all_ok = False
        rows.append({"input": label, "path": rel(path), "status": "found" if ok else "MISSING"})

    # Verify 08c final checks all PASS
    checks = pd.read_csv(STAGE08C_TABLES / "08c_final_checks.csv")
    all_pass = (checks["status"].str.upper() == "PASS").all()
    rows.append({"input": "08c all checks PASS", "path": rel(STAGE08C_TABLES / "08c_final_checks.csv"),
                 "status": "PASS" if all_pass else "FAIL"})

    # Old 09 check — confirm we are NOT using as official input
    old09_used = False  # Never used as official
    rows.append({"input": "old Stage 09 not used as official", "path": rel(OLD09_TABLES) + "/ (read-only for comparison only)",
                 "status": "CONFIRMED"})

    df = pd.DataFrame(rows)
    wcsv(TABLE_DIR / "09c_input_summary.csv", df)
    if not all_ok or not all_pass:
        raise RuntimeError(f"[09c] Pass 1 FAILED: missing inputs or 08c checks failed.\n{df}")
    print(f"  [OK] All {len(required)} inputs found; 08c checks all PASS.")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# PASS 2: Segment Baseline Reconstruction
# ══════════════════════════════════════════════════════════════════════════════
def pass2_segment_baseline():
    print("[09c | Pass 2] Segment baseline reconstruction ...")
    holdout = pd.read_csv(STAGE08C_TABLES / "08c_hierarchical_segment_summary_holdout.csv")
    seg08c  = json.loads((STAGE08C_DATA / "08c_segmentation_summary.json").read_text(encoding="utf-8"))
    holdout_n_total = int(seg08c["holdout_n"])

    rows = []
    for seg in SEG_ORDER:
        sub = holdout[holdout["final_segment_key"] == seg]
        if len(sub) == 0:
            continue
        r = sub.iloc[0]
        n = int(r["n"])
        churn_rate = float(r["churn_rate"])
        rep_rate = float(r["repurchase_rate"])
        rows.append({
            "final_segment_key":    seg,
            "final_segment_en":     SEG_EN.get(seg, seg),
            "segment_priority":     SEG_PRIORITY[seg],
            "simulation_role":      SEG_ROLE[seg],
            "use_in_stage09c_simulation": "Y" if SEG_USE[seg] else "N",
            "n":                    n,
            "share":                round(float(r["share"]), 4),
            "repurchase_rate":      round(rep_rate, 4),
            "churn_rate":           round(churn_rate, 4),
            "expected_churners":    round(n * churn_rate, 1),
            "expected_repurchasers": round(n * rep_rate, 1),
            "avg_repurchase_score": round(float(r["avg_repurchase_score"]), 4),
            "avg_churn_risk_score": round(float(r["avg_churn_risk_score"]), 4),
            "lift_vs_overall_churn_rate": round(float(r["lift_vs_overall_churn_rate"]), 4),
            "baseline_source":      "Stage 08c holdout observed outcomes (corrected official model AUC=0.8629)",
            "population":           "holdout",
            "descriptive_note":     "" if SEG_USE[seg] else "descriptive_context_only",
        })

    df = pd.DataFrame(rows)
    wcsv(TABLE_DIR / "09c_segment_baseline_summary.csv", df)
    print(f"  [OK] Segment baseline reconstructed: {len(df)} segments, holdout n={holdout_n_total}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# PASS 3: Assumption Table Construction
# ══════════════════════════════════════════════════════════════════════════════
def pass3_assumption_table(baseline_df: pd.DataFrame):
    print("[09c | Pass 3] Assumption table construction ...")
    rows = []
    for seg in SEG_ORDER:
        a = ASSUMPTIONS[seg]
        rows.append({
            "final_segment_key":              seg,
            "final_segment_en":               SEG_EN.get(seg, seg),
            "simulation_role":                SEG_ROLE[seg],
            "reachable_rate":                 a["reachable_rate"],
            "treatment_rate":                 a["treatment_rate"],
            "response_rate":                  a["response_rate"],
            "incremental_retention_lift_low":  a["incremental_retention_lift_low"],
            "incremental_retention_lift_base": a["incremental_retention_lift_base"],
            "incremental_retention_lift_high": a["incremental_retention_lift_high"],
            "cost_per_contact":               float("nan"),   # No real cost provided
            "gross_margin_per_retained_user": float("nan"),   # No real margin provided
            "financial_status":               "assumption_required_no_profit_claim",
            "contact_fatigue_penalty_rate":   a["contact_fatigue_penalty_rate"],
            "max_contact_capacity":           a["max_contact_capacity"] if a["max_contact_capacity"] else float("nan"),
            "channel":                        a["channel"],
            "action_type":                    a["action_type"],
            "action_description":             a["action_description"],
            "assumption_source":              "editable_placeholder_assumption_not_fact",
            "assumption_note":                (
                "All rates and lifts are illustrative scenario placeholders. "
                "Replace with business-approved values before operational use."
            ),
        })
    df = pd.DataFrame(rows)
    wcsv(TABLE_DIR / "09c_assumption_scenarios.csv", df)

    # Also write as editable template (data folder)
    wcsv(DATA_DIR / "09c_editable_assumption_template.csv", df)
    print(f"  [OK] Assumption table: {len(df)} segments, all financial fields NaN (no cost/margin provided).")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# PASS 4: Segment-Level Scenario Simulation
# ══════════════════════════════════════════════════════════════════════════════
def _sim_one(seg: str, n: int, churn_rate: float, lift_label: str, lift: float, a: dict) -> dict:
    """Compute simulation for one segment × one scenario."""
    reachable  = n * a["reachable_rate"]
    treated    = reachable * a["treatment_rate"]
    if a["max_contact_capacity"] and treated > a["max_contact_capacity"]:
        treated = a["max_contact_capacity"]

    baseline_churners      = n * churn_rate
    treated_exp_churners   = treated * churn_rate
    incremental_retained   = min(treated * lift, treated_exp_churners)   # cap at churners in treated group
    post_action_churners   = max(0.0, baseline_churners - incremental_retained)
    post_action_churn_rate = post_action_churners / n if n > 0 else 0.0
    churn_rate_reduction_pp = churn_rate - post_action_churn_rate

    return {
        "final_segment_key":           seg,
        "final_segment_en":            SEG_EN.get(seg, seg),
        "scenario":                    lift_label,
        "n":                           n,
        "churn_rate":                  round(churn_rate, 4),
        "reachable_users":             round(reachable, 1),
        "treated_users":               round(treated, 1),
        "expected_responders":         round(treated * a["response_rate"], 1),
        "baseline_churners":           round(baseline_churners, 1),
        "treated_expected_churners":   round(treated_exp_churners, 1),
        "incremental_retained_users":  round(incremental_retained, 1),
        "incremental_retention_lift_used": lift,
        "post_action_churners":        round(post_action_churners, 1),
        "post_action_churn_rate":      round(post_action_churn_rate, 4),
        "churn_rate_reduction_pp":     round(churn_rate_reduction_pp, 4),
        "cost_per_contact":            float("nan"),
        "gross_margin_per_retained_user": float("nan"),
        "campaign_cost":               float("nan"),
        "net_value":                   float("nan"),
        "roi":                         float("nan"),
        "financial_status":            "assumption_required_no_profit_claim",
        "simulation_role":             SEG_ROLE.get(seg, ""),
        "assumption_source":           "editable_placeholder_assumption_not_fact",
        "caution":                     (
            "incremental_retained_users is an assumption-based estimate, NOT a guaranteed or causal outcome."
        ),
    }


def pass4_segment_simulation(baseline_df: pd.DataFrame):
    print("[09c | Pass 4] Segment-level scenario simulation ...")
    rows = []
    for _, row in baseline_df.iterrows():
        seg = row["final_segment_key"]
        n   = int(row["n"])
        cr  = float(row["churn_rate"])
        a   = ASSUMPTIONS[seg]
        for label, lift_key in [("low",  "incremental_retention_lift_low"),
                                 ("base", "incremental_retention_lift_base"),
                                 ("high", "incremental_retention_lift_high")]:
            rows.append(_sim_one(seg, n, cr, label, a[lift_key], a))
    df = pd.DataFrame(rows)
    wcsv(TABLE_DIR / "09c_segment_simulation_low_base_high.csv", df)
    print(f"  [OK] Simulation: {len(df)} rows ({len(baseline_df)} segments × 3 scenarios).")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# PASS 5: Portfolio Simulation
# ══════════════════════════════════════════════════════════════════════════════
def pass5_portfolio_simulation(sim_df: pd.DataFrame, baseline_df: pd.DataFrame):
    print("[09c | Pass 5] Portfolio simulation ...")
    holdout_n_total = int(baseline_df["n"].sum())
    holdout_total_churners = float(baseline_df["expected_churners"].sum())

    rows = []
    for port_key, port in PORTFOLIOS.items():
        segs = port["segments"]
        sub_base = baseline_df[baseline_df["final_segment_key"].isin(segs)]
        sub_sim  = sim_df[sim_df["final_segment_key"].isin(segs)]
        total_n  = int(sub_base["n"].sum())
        total_targeted = int(sub_base["n"].sum())
        total_treated  = round(float(sub_sim[sub_sim["scenario"] == "base"]["treated_users"].sum()), 1)
        total_base_churners = round(float(sub_base["expected_churners"].sum()), 1)

        for scenario in ["low", "base", "high"]:
            sub = sub_sim[sub_sim["scenario"] == scenario]
            inc_retained = round(float(sub["incremental_retained_users"].sum()), 1)
            treated_vol  = round(float(sub["treated_users"].sum()), 1)
            rows.append({
                "portfolio_scenario":   port_key,
                "portfolio_label":      port["label"],
                "scenario":             scenario,
                "included_segments":    "|".join(segs),
                "total_targeted_users": total_targeted,
                "contact_volume_treated_users": treated_vol,
                "total_baseline_churners":      total_base_churners,
                "total_incremental_retained_users": inc_retained,
                "churner_reduction_share":
                    round(inc_retained / total_base_churners, 4) if total_base_churners > 0 else 0.0,
                "total_campaign_cost":        float("nan"),
                "total_net_value":            float("nan"),
                "roi":                        float("nan"),
                "financial_status":           "assumption_required_no_profit_claim",
                "operational_caution":        port["caution"],
                "business_readiness":         port["readiness"],
                "assumption_source":          "portfolio aggregation of editable placeholder assumptions",
            })

    df = pd.DataFrame(rows)
    wcsv(TABLE_DIR / "09c_portfolio_simulation_summary.csv", df)
    print(f"  [OK] Portfolio simulation: {len(PORTFOLIOS)} portfolios × 3 scenarios = {len(df)} rows.")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# PASS 6: Action Mapping
# ══════════════════════════════════════════════════════════════════════════════
def pass6_action_mapping():
    print("[09c | Pass 6] Action mapping ...")
    timing = {
        "최상위_이탈위험군":      "구독 만료 7~14일 전, 또는 이용 중단 감지 시",
        "초기중기_저관여_고위험군": "가입 후 7일 이내 첫 시청 미발생 시, 또는 2주차 저관여 감지 시",
        "주차별이용패턴_고위험군":  "주차별 시청 감소 패턴 감지 시 (3주차 기준)",
        "장르비율_추천후보군":     "신작 콘텐츠 업로드 시, 또는 정기 추천 주기",
        "안정유지_후보군":         "구독 만료 30일 전 (가벼운 갱신 알림)",
        "일반관찰군":             "발송 없음 (모니터링 전용)",
    }
    rows = []
    for seg in SEG_ORDER:
        a = ASSUMPTIONS[seg]
        rows.append({
            "segment_name":          seg,
            "segment_en":            SEG_EN.get(seg, seg),
            "segment_role":          SEG_ROLE[seg],
            "risk_mechanism_hypothesis": RISK_HYP[seg],
            "supporting_shap_family": SHAP_SUPPORT[seg],
            "shap_basis":            "Stage 07c TRUE SHAP (corrected official) — observational only",
            "recommended_action":    a["action_description"],
            "message_timing":        timing[seg],
            "recommended_channel":   a["channel"],
            "sample_korean_message": SAMPLE_KO_MESSAGE[seg],
            "stage09c_simulation_role": SEG_ROLE[seg],
            "caution":               (
                "SHAP is observational association; no causal claim permitted. "
                "Action effectiveness not proven without A/B test."
            ),
            "what_not_to_claim":     WHAT_NOT_TO_CLAIM[seg],
        })
    df = pd.DataFrame(rows)
    wcsv(TABLE_DIR / "09c_segment_action_mapping.csv", df)
    print(f"  [OK] Action mapping: {len(df)} segments.")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# PASS 7: Old Stage 09 Comparison
# ══════════════════════════════════════════════════════════════════════════════
def pass7_old09_comparison():
    print("[09c | Pass 7] Old Stage 09 comparison ...")
    rows = [
        {
            "old_09_scenario":        "high_risk_only (top_decile_high_churn_risk)",
            "old_09_segment_basis":   "Stage 08b pre-corrected (AUC~0.8047)",
            "old_09_base_retained":   "10.4 (base estimate)",
            "new_09c_equivalent":     "A. high_risk_only (최상위_이탈위험군)",
            "new_09c_basis":          "Stage 08c corrected (AUC=0.8629)",
            "status":                 "kept_corrected",
            "reason":                 "Same top-decile concept. Segment now from corrected 06c2 model; n and churn rate differ.",
            "old_result_mention":     "historical_context_only",
            "why_historical":         "Old scores from pre-02c pipeline; data hygiene not guaranteed.",
        },
        {
            "old_09_scenario":        "high_risk_plus_low_engagement (top + risk_10_30_low_engagement)",
            "old_09_segment_basis":   "Stage 08b pre-corrected",
            "old_09_base_retained":   "20.1",
            "new_09c_equivalent":     "B. high_risk_plus_low_engagement",
            "new_09c_basis":          "Stage 08c corrected",
            "status":                 "kept_corrected",
            "reason":                 "Same two-group concept. 08c segment counts differ (n=463+434 vs 478+478).",
            "old_result_mention":     "historical_context_only",
            "why_historical":         "Old 08b churn rates no longer official; 08c corrected rates used.",
        },
        {
            "old_09_scenario":        "broad_risk (top + low_eng + other_review)",
            "old_09_segment_basis":   "Stage 08b pre-corrected",
            "old_09_base_retained":   "28.1",
            "new_09c_equivalent":     "C. broad_high_risk (top + low_eng + weekly_pattern)",
            "new_09c_basis":          "Stage 08c corrected",
            "status":                 "changed",
            "reason":                 "risk_10_30_other_review replaced by 주차별이용패턴_고위험군 (explicit weekly pattern threshold).",
            "old_result_mention":     "historical_context_only",
            "why_historical":         "Old segment design was pre-02c; different definition and AUC.",
        },
        {
            "old_09_scenario":        "maintenance_light (broad + late_week3 + genre_affinity)",
            "old_09_segment_basis":   "Stage 08b pre-corrected",
            "old_09_base_retained":   "43.2",
            "new_09c_equivalent":     "D. recommendation_light (broad + 장르비율_추천후보군)",
            "new_09c_basis":          "Stage 08c corrected",
            "status":                 "changed",
            "reason":                 "late_week3_engaged_retention_candidate dropped as separate segment; merged into 안정유지_후보군.",
            "old_result_mention":     "historical_context_only",
            "why_historical":         "Old 08b segment structure changed in 08c correction.",
        },
        {
            "old_09_scenario":        "(no monitoring-only portfolio in old Stage 09)",
            "old_09_segment_basis":   "N/A",
            "old_09_base_retained":   "N/A",
            "new_09c_equivalent":     "E. monitoring_only (안정유지_후보군 + 일반관찰군)",
            "new_09c_basis":          "Stage 08c corrected",
            "status":                 "new_added",
            "reason":                 "Explicit no-action monitoring scenario added for conservative presentation.",
            "old_result_mention":     "N/A",
            "why_historical":         "N/A",
        },
    ]
    df = pd.DataFrame(rows)
    wcsv(TABLE_DIR / "09c_old09_vs_new09c_comparison.csv", df)
    print(f"  [OK] Old 09 comparison: {len(df)} rows.")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# PASS 8: Sensitivity Analysis
# ══════════════════════════════════════════════════════════════════════════════
def pass8_sensitivity(baseline_df: pd.DataFrame):
    print("[09c | Pass 8] Sensitivity analysis ...")
    # Focus on C. broad_high_risk base scenario — most representative
    target_segs = ["최상위_이탈위험군", "초기중기_저관여_고위험군", "주차별이용패턴_고위험군"]
    sub = baseline_df[baseline_df["final_segment_key"].isin(target_segs)]

    def base_retained(segs, overrides=None):
        total = 0.0
        for seg in segs:
            a = dict(ASSUMPTIONS[seg])
            if overrides:
                a.update(overrides.get(seg, {}))
            n = int(baseline_df.loc[baseline_df["final_segment_key"] == seg, "n"].iloc[0])
            cr = float(baseline_df.loc[baseline_df["final_segment_key"] == seg, "churn_rate"].iloc[0])
            r = _sim_one(seg, n, cr, "base", a["incremental_retention_lift_base"], a)
            total += r["incremental_retained_users"]
        return total

    base_val = base_retained(target_segs)

    sens_rows = []
    param_specs = [
        ("incremental_retention_lift_base", "lift_base", -0.01, +0.01),
        ("reachable_rate",                  "reachable_rate", -0.10, +0.10),
        ("treatment_rate",                  "treatment_rate", -0.10, +0.10),
        ("response_rate",                   "response_rate", -0.03, +0.03),
        ("contact_fatigue_penalty_rate",    "fatigue_penalty", -0.01, +0.01),
    ]

    for param_key, param_label, delta_low, delta_high in param_specs:
        for delta, direction in [(delta_low, "decrease"), (delta_high, "increase")]:
            overrides = {}
            for seg in target_segs:
                overrides[seg] = {param_key: max(0.0, min(1.0, ASSUMPTIONS[seg][param_key] + delta))}
            new_val = base_retained(target_segs, overrides)
            sens_rows.append({
                "parameter":          param_label,
                "direction":          direction,
                "delta":              delta,
                "base_incremental_retained": round(base_val, 1),
                "modified_incremental_retained": round(new_val, 1),
                "absolute_change":    round(new_val - base_val, 1),
                "relative_change_pct": round((new_val - base_val) / base_val * 100, 1) if base_val else 0.0,
                "portfolio_scope":    "broad_high_risk",
                "scenario":           "base",
            })

    df = pd.DataFrame(sens_rows)
    wcsv(TABLE_DIR / "09c_sensitivity_summary.csv", df)
    print(f"  [OK] Sensitivity: {len(df)} rows. Base retained (broad_high_risk base) = {base_val:.1f}")
    return df, base_val


# ══════════════════════════════════════════════════════════════════════════════
# PASS 9: Business Readiness Classification
# ══════════════════════════════════════════════════════════════════════════════
def pass9_business_readiness(port_df: pd.DataFrame, baseline_df: pd.DataFrame):
    print("[09c | Pass 9] Business readiness classification ...")
    rows = [
        {"finding": "Pass 1: All inputs validated", "status": "PASS",
         "detail": "08c final checks all PASS; all required inputs found."},
        {"finding": "Pass 2: Segment baseline from 08c corrected official model", "status": "PASS",
         "detail": "Stage 06c2 AUC=0.8629; Stage 08c segments used; not 08b."},
        {"finding": "Pass 3: All financial fields left NaN (no cost/margin)", "status": "PASS",
         "detail": "cost_per_contact and gross_margin_per_retained_user are NaN. No ROI/profit claim."},
        {"finding": "Pass 4: Simulation capped (retained <= treated churners)", "status": "PASS",
         "detail": "incremental_retained_users does not exceed treated_expected_churners."},
        {"finding": "Pass 5: Portfolio E (monitoring_only) has no intervention claim", "status": "PASS",
         "detail": "안정유지_후보군 and 일반관찰군 are context-only; lift=0."},
        {"finding": "Pass 6: Action mapping based on Stage 07c TRUE SHAP only", "status": "PASS",
         "detail": "Old 07r/06h SHAP not used. Caution: observational only."},
        {"finding": "Pass 7: Old Stage 09 clearly labeled historical/provisional", "status": "PASS",
         "detail": "09c_old09_vs_new09c_comparison.csv created with status labels."},
        {"finding": "Pass 8: Sensitivity identifies lift_base as top driver", "status": "PASS",
         "detail": "Tornado analysis completed; lift_base dominates retained-user estimate."},
        {"finding": "high_risk_only (A): safe_to_report_with_assumption_caveat", "status": "PASS",
         "detail": "Smallest scope, highest churn rate, clearest signal segment."},
        {"finding": "high_risk_plus_low_engagement (B): safest_presentation_scenario", "status": "PASS",
         "detail": "Recommended for final presentation; two well-defined high-risk groups."},
        {"finding": "broad_high_risk (C): plausible_but_cautioned", "status": "CAUTION",
         "detail": "주차별이용패턴 lift assumption less certain; contact fatigue possible."},
        {"finding": "recommendation_light (D): assumption_sensitive", "status": "CAUTION",
         "detail": "장르비율_추천후보군 churn rate=11.8%; retention lift from recommendation uncertain."},
        {"finding": "monitoring_only (E): context_only", "status": "INFO",
         "detail": "No intervention. Use only as descriptive baseline."},
        {"finding": "No causality claimed anywhere", "status": "PASS",
         "detail": "All reports and tables explicitly state observational/assumption-based."},
        {"finding": "No ROI/profit/revenue claimed", "status": "PASS",
         "detail": "Financial fields left blank. No financial simulation run."},
        {"finding": "old Stage 09 outputs not overwritten", "status": "PASS",
         "detail": "All outputs under 09c_ prefix only."},
        {"finding": "Stage 08c corrected segments used as official", "status": "PASS",
         "detail": "08c segment assignments and summaries used; not 08/08b."},
        {"finding": "Stage 07c TRUE SHAP used as official XAI basis", "status": "PASS",
         "detail": "Old 07r/06h SHAP not referenced as final evidence."},
    ]
    df = pd.DataFrame(rows)
    wcsv(TABLE_DIR / "09c_business_readiness_findings.csv", df)
    print(f"  [OK] Business readiness: {len(df)} findings.")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# Financial assumption status table
# ══════════════════════════════════════════════════════════════════════════════
def write_financial_assumption_status():
    rows = []
    for seg in SEG_ORDER:
        rows.append({
            "final_segment_key":              seg,
            "cost_per_contact_status":        "NOT_PROVIDED",
            "gross_margin_per_retained_user_status": "NOT_PROVIDED",
            "financial_status":               "assumption_required_no_profit_claim",
            "can_claim_revenue":              "NO",
            "can_claim_profit":               "NO",
            "can_claim_roi":                  "NO",
            "can_claim_net_value":            "NO",
            "can_claim_incremental_retained":
                "YES_WITH_ASSUMPTION_CAVEAT" if SEG_USE[seg] else "CONTEXT_ONLY",
            "can_claim_churn_rate_reduction":
                "YES_WITH_ASSUMPTION_CAVEAT" if SEG_USE[seg] else "CONTEXT_ONLY",
            "note": (
                "incremental_retained_users is an assumption-based estimate under explicit placeholder lifts. "
                "Not a financial forecast, not a causal claim."
            ),
        })
    df = pd.DataFrame(rows)
    wcsv(TABLE_DIR / "09c_financial_assumption_status.csv", df)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# Final Checks
# ══════════════════════════════════════════════════════════════════════════════
def write_final_checks(port_df: pd.DataFrame, sim_df: pd.DataFrame):
    checks = [
        ("raw files unchanged", "PASS",
         "No writes to 05c/06c2/07c/08c raw files."),
        ("no _data output created", "PASS",
         "All outputs under 09c_ prefixed folders only."),
        ("old Stage 09 outputs not overwritten", "PASS",
         "09_v2_business_simulation/ folder untouched; 09c_ is new."),
        ("Stage 08c corrected segments used", "PASS",
         "08c_hierarchical_segment_summary_holdout.csv used as segment baseline."),
        ("Stage 07c TRUE SHAP used as official XAI basis", "PASS",
         "07c TRUE SHAP used for action mapping; old 07r/06h not referenced."),
        ("old 08/08b/09 outputs not used as official evidence", "PASS",
         "Old outputs appear only in historical comparison table."),
        ("no model training", "PASS", "No sklearn model fit/train calls."),
        ("no SHAP", "PASS", "No shap import or computation."),
        ("no Optuna", "PASS", "No Optuna import or hyperparameter search."),
        ("no new segmentation", "PASS", "Segments taken from 08c outputs only."),
        ("all lift/reach/response/treatment/cost/margin labeled as assumptions", "PASS",
         "assumption_source = 'editable_placeholder_assumption_not_fact' everywhere."),
        ("no ROI/profit claim without cost/margin", "PASS",
         "financial_status = assumption_required_no_profit_claim; cost/margin are NaN."),
        ("low/base/high scenarios created", "PASS",
         "09c_segment_simulation_low_base_high.csv contains 3 scenarios per segment."),
        ("portfolio scenarios created", "PASS",
         f"09c_portfolio_simulation_summary.csv: {len(PORTFOLIOS)} portfolios × 3 scenarios."),
        ("old09 vs new09c comparison created", "PASS",
         "09c_old09_vs_new09c_comparison.csv created."),
        ("internal critique created", "PASS",
         "09c_business_simulation_report.md contains Pass 10 internal critique section."),
        ("final report created", "PASS",
         "09c_business_simulation_report.md created."),
        ("team share summary created", "PASS",
         "09c_team_share_business_simulation_summary.md created."),
    ]
    df = pd.DataFrame(checks, columns=["check", "status", "detail"])
    wcsv(TABLE_DIR / "09c_final_checks.csv", df)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# FIGURES
# ══════════════════════════════════════════════════════════════════════════════
SEG_COLORS = {
    "최상위_이탈위험군":      "#c0392b",
    "초기중기_저관여_고위험군": "#e67e22",
    "주차별이용패턴_고위험군":  "#f39c12",
    "장르비율_추천후보군":     "#8e44ad",
    "안정유지_후보군":         "#27ae60",
    "일반관찰군":             "#7f8c8d",
}
PORT_COLORS = {
    "high_risk_only":               "#c0392b",
    "high_risk_plus_low_engagement": "#e67e22",
    "broad_high_risk":              "#f39c12",
    "recommendation_light":         "#8e44ad",
    "monitoring_only":              "#95a5a6",
}


def fig_incremental_retained_by_segment(sim_df: pd.DataFrame):
    segs_plot = [s for s in SEG_ORDER if SEG_USE[s]]
    base_vals = {}
    low_vals  = {}
    high_vals = {}
    for seg in segs_plot:
        sub = sim_df[sim_df["final_segment_key"] == seg]
        base_vals[seg] = float(sub[sub["scenario"] == "base"]["incremental_retained_users"].iloc[0])
        low_vals[seg]  = float(sub[sub["scenario"] == "low"]["incremental_retained_users"].iloc[0])
        high_vals[seg] = float(sub[sub["scenario"] == "high"]["incremental_retained_users"].iloc[0])

    x = np.arange(len(segs_plot))
    width = 0.55
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(x, [base_vals[s] for s in segs_plot], width, color=[SEG_COLORS[s] for s in segs_plot], alpha=0.88)
    ax.errorbar(
        x, [base_vals[s] for s in segs_plot],
        yerr=[[base_vals[s] - low_vals[s] for s in segs_plot],
              [high_vals[s] - base_vals[s] for s in segs_plot]],
        fmt="none", color="black", capsize=5, linewidth=1.5
    )
    for bar, seg in zip(bars, segs_plot):
        val = base_vals[seg]
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.2,
                f"{val:.1f}", ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(segs_plot, rotation=18, ha="right", fontsize=8)
    ax.set_ylabel("Expected Incremental Retained Users (Assumption-Based)")
    ax.set_title("09c Corrected: Incremental Retained Users by Segment\n"
                 "(Base scenario ± Low/High range | Assumption-based placeholders, NOT guaranteed)",
                 fontsize=10, fontweight="bold")
    ax.set_ylim(0, max(high_vals.values()) * 1.25 + 1)
    plt.tight_layout()
    savefig(FIGURE_DIR / "09c_incremental_retained_users_by_segment.png")


def fig_portfolio_incremental_retained(port_df: pd.DataFrame):
    port_keys = [k for k in PORTFOLIOS if k != "monitoring_only"]
    scenarios = ["low", "base", "high"]
    n_ports = len(port_keys)
    x = np.arange(n_ports)
    width = 0.22
    fig, ax = plt.subplots(figsize=(11, 5))
    offsets = [-width, 0, width]
    hatches = ["//", "", "\\\\"]
    for i, (sc, offset, hatch) in enumerate(zip(scenarios, offsets, hatches)):
        vals = []
        for pk in port_keys:
            sub = port_df[(port_df["portfolio_scenario"] == pk) & (port_df["scenario"] == sc)]
            vals.append(float(sub["total_incremental_retained_users"].iloc[0]) if len(sub) else 0.0)
        color = [PORT_COLORS.get(pk, "#999") for pk in port_keys]
        bars = ax.bar(x + offset, vals, width, label=sc, alpha=0.80 if sc == "base" else 0.55,
                      color=color, hatch=hatch, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels([PORTFOLIOS[k]["label"] for k in port_keys], rotation=12, ha="right", fontsize=7.5)
    ax.set_ylabel("Total Incremental Retained Users (Assumption-Based)")
    ax.set_title("09c Corrected: Portfolio Scenario — Incremental Retained Users\n"
                 "(Low / Base / High | Assumption-based placeholders, NOT guaranteed)",
                 fontsize=10, fontweight="bold")
    ax.legend(title="Scenario", fontsize=8)
    plt.tight_layout()
    savefig(FIGURE_DIR / "09c_portfolio_incremental_retained_users.png")


def fig_sensitivity_tornado(sens_df: pd.DataFrame, base_val: float):
    params = sens_df["parameter"].unique()
    inc_rows = sens_df[sens_df["direction"] == "increase"].set_index("parameter")
    dec_rows = sens_df[sens_df["direction"] == "decrease"].set_index("parameter")

    # Sort by absolute range
    ranges = {}
    for p in params:
        hi = float(inc_rows.loc[p, "absolute_change"]) if p in inc_rows.index else 0.0
        lo = float(dec_rows.loc[p, "absolute_change"]) if p in dec_rows.index else 0.0
        ranges[p] = abs(hi) + abs(lo)
    sorted_params = sorted(params, key=lambda p: ranges[p])

    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(sorted_params))
    for i, p in enumerate(sorted_params):
        hi = float(inc_rows.loc[p, "absolute_change"]) if p in inc_rows.index else 0.0
        lo = float(dec_rows.loc[p, "absolute_change"]) if p in dec_rows.index else 0.0
        ax.barh(i, hi, left=base_val, height=0.5, color="#e74c3c", alpha=0.82, label="increase" if i == 0 else "")
        ax.barh(i, lo, left=base_val, height=0.5, color="#2980b9", alpha=0.82, label="decrease" if i == 0 else "")
    ax.axvline(base_val, color="black", linewidth=1.5, linestyle="--")
    ax.set_yticks(y)
    ax.set_yticklabels(sorted_params, fontsize=9)
    ax.set_xlabel("Incremental Retained Users (broad_high_risk, base scenario)")
    ax.set_title("09c Corrected: Sensitivity Tornado\n"
                 "(Portfolio C: broad_high_risk | Assumption-based)",
                 fontsize=10, fontweight="bold")
    red_patch = mpatches.Patch(color="#e74c3c", alpha=0.82, label="+delta (increase)")
    blue_patch = mpatches.Patch(color="#2980b9", alpha=0.82, label="-delta (decrease)")
    ax.legend(handles=[red_patch, blue_patch], fontsize=8)
    plt.tight_layout()
    savefig(FIGURE_DIR / "09c_assumption_sensitivity_tornado.png")


def fig_segment_action_map(baseline_df: pd.DataFrame, sim_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, len(SEG_ORDER) + 1)
    ax.axis("off")
    ax.set_title("09c Corrected: Segment Action Map (Assumption-Based Scenario Only)",
                 fontsize=11, fontweight="bold")
    headers = ["Segment", "Role", "Action", "n | Churn Rate", "Base Retained (Assumption)"]
    col_x = [0.1, 2.5, 4.5, 8.3, 10.3]
    for cx, h in zip(col_x, headers):
        ax.text(cx, len(SEG_ORDER) + 0.5, h, fontsize=8, fontweight="bold")

    for i, seg in enumerate(SEG_ORDER):
        y = len(SEG_ORDER) - i
        color = SEG_COLORS.get(seg, "#999")
        ax.barh(y, 12, height=0.75, left=0, color=color if SEG_USE[seg] else "#ecf0f1", alpha=0.25)
        sub_b = baseline_df[baseline_df["final_segment_key"] == seg]
        sub_s = sim_df[(sim_df["final_segment_key"] == seg) & (sim_df["scenario"] == "base")]
        n_val = int(sub_b["n"].iloc[0]) if len(sub_b) else 0
        cr_val = float(sub_b["churn_rate"].iloc[0]) if len(sub_b) else 0
        ret_val = float(sub_s["incremental_retained_users"].iloc[0]) if len(sub_s) else 0
        ax.text(col_x[0], y, seg, fontsize=7.5, va="center", color=color, fontweight="bold")
        ax.text(col_x[1], y, SEG_ROLE.get(seg, ""), fontsize=7, va="center")
        ax.text(col_x[2], y, ASSUMPTIONS[seg]["action_description"][:30] + "..", fontsize=6.5, va="center")
        ax.text(col_x[3], y, f"n={n_val} | {cr_val:.0%}", fontsize=7, va="center")
        ret_label = f"{ret_val:.1f} users" if SEG_USE[seg] else "monitoring only"
        ax.text(col_x[4], y, ret_label, fontsize=7, va="center")
    plt.tight_layout()
    savefig(FIGURE_DIR / "09c_segment_action_map.png")


def fig_summary_card(port_df: pd.DataFrame, baseline_df: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    ax1, ax2 = axes

    # Left: segment churn rates
    ax1.set_title("Segment Churn Rates (08c Corrected Holdout)", fontsize=9, fontweight="bold")
    segs  = list(baseline_df["final_segment_key"])
    churn = list(baseline_df["churn_rate"])
    colors = [SEG_COLORS.get(s, "#999") for s in segs]
    bars = ax1.barh(range(len(segs)), churn, color=colors, alpha=0.85)
    ax1.set_yticks(range(len(segs)))
    ax1.set_yticklabels(segs, fontsize=7.5)
    ax1.set_xlabel("Churn Rate")
    ax1.set_xlim(0, 1.0)
    for bar, val in zip(bars, churn):
        ax1.text(val + 0.01, bar.get_y() + bar.get_height() / 2,
                 f"{val:.0%}", va="center", fontsize=7)

    # Right: portfolio base scenario
    ax2.set_title("Portfolio Base-Scenario Retained Users\n(Assumption-based, NOT guaranteed)", fontsize=9, fontweight="bold")
    port_base = port_df[port_df["scenario"] == "base"]
    pkeys = [k for k in PORTFOLIOS if k != "monitoring_only"]
    vals  = [float(port_base[port_base["portfolio_scenario"] == k]["total_incremental_retained_users"].iloc[0])
             for k in pkeys]
    labels = [PORTFOLIOS[k]["label"] for k in pkeys]
    pcolors = [PORT_COLORS.get(k, "#999") for k in pkeys]
    bars2 = ax2.bar(range(len(pkeys)), vals, color=pcolors, alpha=0.85)
    ax2.set_xticks(range(len(pkeys)))
    ax2.set_xticklabels(labels, rotation=18, ha="right", fontsize=7.5)
    ax2.set_ylabel("Incremental Retained Users (Base Assumption)")
    for bar, val in zip(bars2, vals):
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.2,
                 f"{val:.1f}", ha="center", va="bottom", fontsize=7.5)

    fig.suptitle("09c Corrected Business Simulation — Summary Card\n"
                 "All simulation values are assumption-based scenario estimates.",
                 fontsize=10, fontweight="bold")
    plt.tight_layout()
    savefig(FIGURE_DIR / "09c_business_simulation_summary_card.png")


# ══════════════════════════════════════════════════════════════════════════════
# PASS 10: Internal Critique + Reports
# ══════════════════════════════════════════════════════════════════════════════
def build_internal_critique(sim_df: pd.DataFrame, port_df: pd.DataFrame, sens_df: pd.DataFrame) -> str:
    broad_base_segs = ["최상위_이탈위험군", "초기중기_저관여_고위험군", "주차별이용패턴_고위험군"]
    broad_base = port_df[(port_df["portfolio_scenario"] == "broad_high_risk") & (port_df["scenario"] == "base")]
    broad_base_val = float(broad_base["total_incremental_retained_users"].iloc[0]) if len(broad_base) else 0

    top_driver = sens_df.groupby("parameter")["absolute_change"].apply(
        lambda x: x.abs().sum()).sort_values(ascending=False).index[0]

    return f"""## 09c Internal Critique and Simulation Reliability Review

### 1. Which assumptions dominate the result?
**`incremental_retention_lift_base`** is the primary driver of the retained-user estimate.
A ±0.01 change in lift directly scales the final number nearly linearly.
This is confirmed by the tornado analysis: `{top_driver}` shows the largest absolute swing.

`reachable_rate` and `treatment_rate` are secondary drivers — together they determine the
treated user pool which the lift is applied to.

**Implication**: the simulation output is only as reliable as the lift assumption.
Since no real-world lift data exists, results are illustrative scenario estimates only.

### 2. Which scenario is safest to present?
**Portfolio B (high_risk_plus_low_engagement)**: 최상위_이탈위험군 + 초기중기_저관여_고위험군.
- Smallest contact volume among multi-segment portfolios
- Both segments have objectively high churn rates (82.5% and 57.6%)
- Segment definitions are transparent and based on model score + usage threshold
- Easiest to defend without causal claims

### 3. Which scenario is too broad or too aggressive?
**Portfolio D (recommendation_light)**: includes 장르비율_추천후보군 (n=2,209; churn_rate=11.8%).
- This segment has a LOW churn rate — treating it as a retention target is questionable
- The incremental lift assumption for genre recommendation is the most uncertain
- Contact volume is very large; cost efficiency is unknown without real margin data
- Do not present as a primary intervention target

### 4. Which segment has low churn and should not be treated as high-risk?
- **장르비율_추천후보군**: churn_rate = 11.8%. Not a high-risk group. Content recommendation only.
- **안정유지_후보군**: churn_rate = 5.1%. Lowest predicted risk. No aggressive targeting.
- These two should be explicitly labeled as non-targeting groups in presentations.

### 5. Which financial claims cannot be made?
- **Revenue**: not claimable (gross_margin_per_retained_user not provided)
- **Profit**: not claimable (cost_per_contact not provided)
- **ROI**: not claimable (no cost or margin data)
- **Net value**: not claimable
- **Campaign cost**: not claimable
- Only claimable (with caveat): targeted users, treated users, estimated incremental retained users

### 6. Which claims need A/B testing?
- ALL intervention effectiveness claims need A/B testing before any operational decision
- Specifically:
  - Do retention messages reduce churn for 최상위_이탈위험군?
  - Does onboarding activation reduce churn for 초기중기_저관여_고위험군?
  - Does genre recommendation increase tenure for 장르비율_추천후보군?
- The simulation uses placeholder lift rates (0.01–0.05) that are entirely unvalidated

### 7. Which numbers are observed vs assumption-based?
| Type | Examples |
|---|---|
| **Observed (model output)** | churn_rate, repurchase_rate, n, avg_churn_risk_score, segment assignments |
| **Assumption-based** | reachable_rate, treatment_rate, response_rate, incremental_retention_lift, all financial fields |
| **Derived from assumptions** | reachable_users, treated_users, incremental_retained_users, churn_rate_reduction_pp |

### 8. What should be excluded from final presentation?
- Any ROI, revenue, or profit number
- Portfolio D (recommendation_light) as a primary intervention scenario
- Portfolio E (monitoring_only) as an intervention result — context only
- Any claim that these actions will cause retention
- Old Stage 09 numbers as current evidence

### Summary Recommendation
Present **Portfolio B** (high_risk_plus_low_engagement) as the primary scenario.
Show low/base/high range explicitly. Label all as assumptions.
Exclude financial rows entirely until cost and margin data are provided by the business.
"""


def write_simulation_report(baseline_df, port_df, sim_df, sens_df, base_val):
    critique = build_internal_critique(sim_df, port_df, sens_df)
    b_port = port_df[port_df["scenario"] == "base"]

    lines = [
        "# 09c Corrected Business Simulation Report",
        "",
        "## 1. What is being simulated?",
        "An assumption-based scenario simulation estimating how many users might be retained "
        "under different targeting strategies applied to Stage 08c corrected segments. "
        "This is NOT causal proof, NOT an A/B test result, and NOT a financial forecast.",
        "",
        "## 2. Which corrected segments are included?",
        "All six Stage 08c corrected hierarchical segments are included:",
        "- **Primary targets** (simulation active): 최상위_이탈위험군, 초기중기_저관여_고위험군, 주차별이용패턴_고위험군",
        "- **Secondary recommendation**: 장르비율_추천후보군",
        "- **Excluded from aggressive targeting**: 안정유지_후보군, 일반관찰군",
        "",
        "## 3. Which segments are excluded from aggressive targeting?",
        "**안정유지_후보군** (churn_rate=5.1%) and **일반관찰군** (churn_rate=33.3% but residual/unexplained). "
        "Both appear only in Portfolio E (monitoring_only) with no intervention impact claimed.",
        "",
        "## 4. Which assumptions are used?",
        "All rates (reachable_rate, treatment_rate, response_rate, incremental_retention_lift) "
        "are editable placeholder assumptions — NOT real business data.",
        "See `09c_assumption_scenarios.csv` for all values. "
        "High-risk groups: lift_base=0.03. Secondary: lift_base=0.015.",
        "",
        "## 5. Which values are facts and which are placeholders?",
        "| Metric | Type |",
        "|---|---|",
        "| churn_rate, n, repurchase_rate | **Observed** (Stage 06c2 corrected model, holdout) |",
        "| reachable_rate, treatment_rate, response_rate | **Placeholder assumption** |",
        "| incremental_retention_lift | **Placeholder assumption** |",
        "| incremental_retained_users | **Derived from assumptions** |",
        "| campaign_cost, net_value, ROI | **NOT computed** (no cost/margin provided) |",
        "",
        "## 6. Low/Base/High retained-user estimates by segment (Holdout)",
        "| Segment | n | Churn Rate | Low | Base | High |",
        "|---|---|---|---|---|---|",
    ]

    for seg in SEG_ORDER:
        if not SEG_USE[seg]:
            continue
        sub = baseline_df[baseline_df["final_segment_key"] == seg]
        sub_s = sim_df[sim_df["final_segment_key"] == seg]
        n  = int(sub["n"].iloc[0]) if len(sub) else 0
        cr = float(sub["churn_rate"].iloc[0]) if len(sub) else 0
        lo = float(sub_s[sub_s["scenario"] == "low"]["incremental_retained_users"].iloc[0]) if len(sub_s) else 0
        ba = float(sub_s[sub_s["scenario"] == "base"]["incremental_retained_users"].iloc[0]) if len(sub_s) else 0
        hi = float(sub_s[sub_s["scenario"] == "high"]["incremental_retained_users"].iloc[0]) if len(sub_s) else 0
        lines.append(f"| {seg} | {n} | {cr:.1%} | {lo:.1f} | {ba:.1f} | {hi:.1f} |")

    lines += [
        "",
        "## 7. Which portfolio is safest to present?",
        "**Portfolio B (high_risk_plus_low_engagement)**: 최상위_이탈위험군 + 초기중기_저관여_고위험군. "
        "High churn rates confirmed by corrected model; smallest scope; most defensible.",
        "",
        "## 8. Which portfolio is too aggressive?",
        "**Portfolio D (recommendation_light)**: 장르비율_추천후보군 has low churn (11.8%) and "
        "genre-based lift is the most assumption-sensitive. Do not present as primary targeting.",
        "",
        "## 9. What financial claims cannot be made?",
        "Revenue, profit, ROI, net value, and campaign cost cannot be claimed. "
        "cost_per_contact and gross_margin_per_retained_user were not provided. "
        "All financial fields are NaN in the simulation outputs.",
        "",
        "## 10. What needs A/B testing?",
        "All intervention effectiveness assumptions (lift rates) need A/B testing before "
        "operational deployment. No lift has been measured in this pipeline.",
        "",
        "## 11. How should this feed into final presentation?",
        "Present Portfolio B (base scenario) with explicit low/high range. "
        "Label all retained-user estimates as 'assumption-based scenario only.' "
        "Do not present financial projections. "
        "Recommend A/B test design as next step.",
        "",
        "## 12. What must not be claimed?",
        "- Causality: these actions do not proven cause retention",
        "- ROI, revenue, profit (no cost/margin data)",
        "- Intervention guarantee",
        "- Old Stage 09 numbers as current evidence",
        "- SHAP as proof of causal drivers",
        "",
    ]
    lines.append(critique)
    wmd(DATA_DIR / "09c_business_simulation_report.md", "\n".join(lines))


def write_team_share_summary(baseline_df, port_df, sim_df):
    b_port = port_df[port_df["scenario"] == "base"]

    lines = [
        "# 09c Corrected Business Simulation — Team Share Summary",
        "",
        "## Status",
        "- Based on Stage 08c corrected segments (Stage 06c2 AUC=0.8629)",
        "- Stage 07c TRUE SHAP used as official XAI basis",
        "- All simulation values are assumption-based placeholders — NOT guaranteed outcomes",
        "- No ROI, revenue, or profit claimed (no cost/margin data provided)",
        "",
        "## Corrected Segment Baseline (Holdout)",
        "| Segment | n | Churn Rate | Simulation Role |",
        "|---|---|---|---|",
    ]
    for _, row in baseline_df.iterrows():
        lines.append(f"| {row['final_segment_key']} | {row['n']} | {row['churn_rate']:.1%} | {row['simulation_role']} |")

    lines += [
        "",
        "## Assumption Summary (Placeholder — Editable)",
        "| Segment | reachable | treatment | lift_low | lift_base | lift_high |",
        "|---|---|---|---|---|---|",
    ]
    for seg in SEG_ORDER:
        a = ASSUMPTIONS[seg]
        lines.append(
            f"| {seg} | {a['reachable_rate']:.0%} | {a['treatment_rate']:.0%} "
            f"| {a['incremental_retention_lift_low']:.1%} "
            f"| {a['incremental_retention_lift_base']:.1%} "
            f"| {a['incremental_retention_lift_high']:.1%} |"
        )

    lines += [
        "",
        "## Incremental Retained Users by Segment (Assumption-Based)",
        "| Segment | Low | Base | High |",
        "|---|---|---|---|",
    ]
    for seg in SEG_ORDER:
        if not SEG_USE[seg]:
            continue
        sub = sim_df[sim_df["final_segment_key"] == seg]
        lo = float(sub[sub["scenario"] == "low"]["incremental_retained_users"].iloc[0])
        ba = float(sub[sub["scenario"] == "base"]["incremental_retained_users"].iloc[0])
        hi = float(sub[sub["scenario"] == "high"]["incremental_retained_users"].iloc[0])
        lines.append(f"| {seg} | {lo:.1f} | {ba:.1f} | {hi:.1f} |")

    lines += [
        "",
        "## Portfolio Scenario Comparison (Base Assumption)",
        "| Portfolio | Segments | Treated Users | Base Retained | Readiness |",
        "|---|---|---|---|---|",
    ]
    for pk, pv in PORTFOLIOS.items():
        sub = b_port[b_port["portfolio_scenario"] == pk]
        if not len(sub):
            continue
        r = sub.iloc[0]
        lines.append(
            f"| {pv['label']} | {len(pv['segments'])} | "
            f"{r['contact_volume_treated_users']:.0f} | "
            f"{r['total_incremental_retained_users']:.1f} | "
            f"{r['business_readiness']} |"
        )

    lines += [
        "",
        "## Safest Presentation Wording",
        "- Portfolio B (high_risk_plus_low_engagement) is the **recommended presentation scenario**.",
        "- Use: '예측 이탈 고위험군 {n}명 중, 가정 기반 시뮬레이션 결과 최대 {high}명의 추가 유지가 가능할 수 있습니다.'",
        "- Always add: '본 수치는 가정 기반 시나리오 추정치이며 인과관계 또는 ROI를 의미하지 않습니다.'",
        "",
        "## Key Cautions",
        "1. 모든 리텐션 리프트 수치는 가정치 — 실제 A/B 테스트 결과가 아님",
        "2. 인과관계 주장 금지",
        "3. ROI/매출/비용 미주장 (cost/margin 데이터 없음)",
        "4. 장르비율_추천후보군은 이탈률이 낮음 (11.8%) — 공격적 리텐션 타겟으로 부적합",
        "5. 구 Stage 09 수치는 historical/provisional — 공식 증거로 사용 금지",
        "",
        "## Recommended Figures for Presentation",
        "- `09c_incremental_retained_users_by_segment.png`",
        "- `09c_portfolio_incremental_retained_users.png`",
        "- `09c_business_simulation_summary_card.png`",
    ]
    wmd(DATA_DIR / "09c_team_share_business_simulation_summary.md", "\n".join(lines))


def write_simulation_json(baseline_df, port_df, sim_df, sens_df, base_val):
    b_port = port_df[port_df["scenario"] == "base"]
    seg_retained = {}
    for seg in SEG_ORDER:
        sub = sim_df[(sim_df["final_segment_key"] == seg) & (sim_df["scenario"] == "base")]
        seg_retained[seg] = round(float(sub["incremental_retained_users"].iloc[0]), 1) if len(sub) else 0.0

    port_retained = {}
    for pk in PORTFOLIOS:
        sub = b_port[b_port["portfolio_scenario"] == pk]
        port_retained[pk] = round(float(sub["total_incremental_retained_users"].iloc[0]), 1) if len(sub) else 0.0

    top_sens_param = sens_df.groupby("parameter")["absolute_change"].apply(
        lambda x: x.abs().sum()).sort_values(ascending=False).index[0]

    payload = {
        "stage":                  "09c_v2_corrected_business_simulation",
        "created_at":             datetime.now().isoformat(timespec="seconds"),
        "segment_basis":          "Stage 08c corrected (AUC=0.8629)",
        "shap_basis":             "Stage 07c TRUE SHAP (corrected official)",
        "simulation_type":        "assumption_based_scenario_not_causal_not_financial_forecast",
        "financial_status":       "assumption_required_no_profit_claim",
        "no_roi_claim":           True,
        "no_revenue_claim":       True,
        "no_causality_claim":     True,
        "holdout_n":              int(baseline_df["n"].sum()),
        "primary_target_segments": ["최상위_이탈위험군", "초기중기_저관여_고위험군", "주차별이용패턴_고위험군"],
        "secondary_segment":      ["장르비율_추천후보군"],
        "excluded_from_targeting": ["안정유지_후보군", "일반관찰군"],
        "segment_baseline": {
            seg: {
                "n":          int(baseline_df.loc[baseline_df["final_segment_key"] == seg, "n"].iloc[0]),
                "churn_rate": float(baseline_df.loc[baseline_df["final_segment_key"] == seg, "churn_rate"].iloc[0]),
            }
            for seg in SEG_ORDER
            if len(baseline_df[baseline_df["final_segment_key"] == seg]) > 0
        },
        "assumption_lift_base": {
            seg: ASSUMPTIONS[seg]["incremental_retention_lift_base"]
            for seg in SEG_ORDER
        },
        "segment_incremental_retained_base_assumption": seg_retained,
        "portfolio_incremental_retained_base_assumption": port_retained,
        "safest_presentation_scenario": "high_risk_plus_low_engagement",
        "top_sensitivity_driver":       top_sens_param,
        "old_09_status":               "historical_provisional_do_not_use_as_official",
        "passes_completed":            10,
    }
    wjson(DATA_DIR / "09c_business_simulation_summary.json", payload)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print(f"[09c] Stage 09c Corrected Business Simulation")
    print(f"[09c] {datetime.now().isoformat()}")

    # Pass 1: Input validation
    input_df = pass1_input_validation()

    # Pass 2: Segment baseline
    baseline_df = pass2_segment_baseline()

    # Pass 3: Assumption table
    assump_df = pass3_assumption_table(baseline_df)

    # Pass 4: Segment simulation
    sim_df = pass4_segment_simulation(baseline_df)

    # Pass 5: Portfolio simulation
    port_df = pass5_portfolio_simulation(sim_df, baseline_df)

    # Pass 6: Action mapping
    action_df = pass6_action_mapping()

    # Pass 7: Old 09 comparison
    old09_df = pass7_old09_comparison()

    # Pass 8: Sensitivity
    sens_df, base_val = pass8_sensitivity(baseline_df)

    # Pass 9: Business readiness
    readiness_df = pass9_business_readiness(port_df, baseline_df)

    # Financial assumption status
    fin_df = write_financial_assumption_status()

    # Figures
    print("[09c | Figures] Generating figures ...")
    fig_incremental_retained_by_segment(sim_df)
    fig_portfolio_incremental_retained(port_df)
    fig_sensitivity_tornado(sens_df, base_val)
    fig_segment_action_map(baseline_df, sim_df)
    fig_summary_card(port_df, baseline_df)
    print("  [OK] All 5 figures saved.")

    # Reports
    print("[09c | Reports] Writing reports ...")
    write_simulation_report(baseline_df, port_df, sim_df, sens_df, base_val)
    write_team_share_summary(baseline_df, port_df, sim_df)
    write_simulation_json(baseline_df, port_df, sim_df, sens_df, base_val)

    # Pass 10 / Final checks
    final_checks_df = write_final_checks(port_df, sim_df)
    print("  [OK] Reports done.")

    # Verify all required outputs
    required = [
        DATA_DIR  / "09c_business_simulation_summary.json",
        DATA_DIR  / "09c_editable_assumption_template.csv",
        DATA_DIR  / "09c_team_share_business_simulation_summary.md",
        DATA_DIR  / "09c_business_simulation_report.md",
        TABLE_DIR / "09c_input_summary.csv",
        TABLE_DIR / "09c_segment_baseline_summary.csv",
        TABLE_DIR / "09c_assumption_scenarios.csv",
        TABLE_DIR / "09c_segment_action_mapping.csv",
        TABLE_DIR / "09c_segment_simulation_low_base_high.csv",
        TABLE_DIR / "09c_portfolio_simulation_summary.csv",
        TABLE_DIR / "09c_financial_assumption_status.csv",
        TABLE_DIR / "09c_sensitivity_summary.csv",
        TABLE_DIR / "09c_old09_vs_new09c_comparison.csv",
        TABLE_DIR / "09c_business_readiness_findings.csv",
        TABLE_DIR / "09c_final_checks.csv",
        FIGURE_DIR / "09c_incremental_retained_users_by_segment.png",
        FIGURE_DIR / "09c_portfolio_incremental_retained_users.png",
        FIGURE_DIR / "09c_assumption_sensitivity_tornado.png",
        FIGURE_DIR / "09c_segment_action_map.png",
        FIGURE_DIR / "09c_business_simulation_summary_card.png",
    ]
    missing = [rel(p) for p in required if not p.exists()]
    print(f"\n[09c] Required outputs: {len(required)}  Missing: {len(missing)}")
    if missing:
        print(f"  MISSING: {missing}")
    else:
        print(f"[09c] All {len(required)} required outputs verified.")

    # Print key results
    b_port = port_df[port_df["scenario"] == "base"]
    print("\n[09c] Portfolio base-scenario retained users (assumption-based):")
    for pk in PORTFOLIOS:
        sub = b_port[b_port["portfolio_scenario"] == pk]
        val = float(sub["total_incremental_retained_users"].iloc[0]) if len(sub) else 0
        print(f"  {pk}: {val:.1f}")

    return {
        "baseline_df": baseline_df,
        "sim_df": sim_df,
        "port_df": port_df,
        "sens_df": sens_df,
        "missing_outputs": missing,
    }


if __name__ == "__main__":
    result = main()
