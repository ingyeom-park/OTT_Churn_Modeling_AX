import json
import os
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


os.environ.setdefault("PYTHONIOENCODING", "utf-8")

TARGET = "is_repurchase"
TARGET_NUM = "target_repurchase"
ID_COL = "membership_row_id"

PRIMARY_SEGMENTS = [
    "top_decile_high_churn_risk",
    "risk_10_30_low_engagement",
    "risk_10_30_other_review",
    "late_week3_engaged_retention_candidate",
    "genre_affinity_content_recommendation_pool",
    "low_risk_or_general_maintenance",
]
SIMULATION_CANDIDATES = [
    "top_decile_high_churn_risk",
    "risk_10_30_low_engagement",
    "risk_10_30_other_review",
    "late_week3_engaged_retention_candidate",
    "genre_affinity_content_recommendation_pool",
]
PORTFOLIOS = {
    "high_risk_only": ["top_decile_high_churn_risk"],
    "high_risk_plus_low_engagement": ["top_decile_high_churn_risk", "risk_10_30_low_engagement"],
    "broad_risk": ["top_decile_high_churn_risk", "risk_10_30_low_engagement", "risk_10_30_other_review"],
    "maintenance_light": [
        "top_decile_high_churn_risk",
        "risk_10_30_low_engagement",
        "risk_10_30_other_review",
        "late_week3_engaged_retention_candidate",
        "genre_affinity_content_recommendation_pool",
    ],
}


def find_project_root(start):
    for candidate in [start, *start.parents]:
        if (
            (candidate / "_data" / "01_raw" / "Membership.csv").exists()
            and (
                candidate
                / "park.ingyeom"
                / "reports"
                / "data"
                / "08b_v2_segmentation_refinement"
                / "08b_segmentation_refinement_summary.json"
            ).exists()
        ):
            return candidate
    raise FileNotFoundError("Could not locate ott-churn-prediction project root.")


PROJECT_ROOT = find_project_root(Path.cwd())
STAGE08B_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "08b_v2_segmentation_refinement"
STAGE08B_TABLES = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "08b_v2_segmentation_refinement"
STAGE07R_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "07r_v2_true_shap_interpretation"
STAGE07R_TABLES = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "07r_v2_true_shap_interpretation"

DATA_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "09_v2_business_simulation"
TABLE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "09_v2_business_simulation"
FIGURE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "09_v2_business_simulation"
for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

RAW_FILES = [
    PROJECT_ROOT / "_data" / "01_raw" / "Membership.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "User_Mapping.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "View_History.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "Movie_Master.csv",
]

STAGE_EXISTING_DIRS = []
for base in [
    PROJECT_ROOT / "park.ingyeom" / "reports" / "data",
    PROJECT_ROOT / "park.ingyeom" / "reports" / "tables",
    PROJECT_ROOT / "park.ingyeom" / "reports" / "figures",
]:
    for prefix in [
        "01_v2",
        "02_v2",
        "03_v2",
        "04_v2",
        "05_v2",
        "06_v2",
        "06b_v2",
        "07_v2",
        "07r_v2",
        "08_v2",
        "08b_v2",
    ]:
        STAGE_EXISTING_DIRS.extend(sorted(base.glob(f"{prefix}*")))
STAGE_EXISTING_FILES = [
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "01_v2_data_overview_and_audit.ipynb",
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "02_v2_preprocessing_policy.ipynb",
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "03_v2_usage_feature_engineering.ipynb",
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "04_v2_content_feature_engineering.ipynb",
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "05_v2_modeling_dataset.ipynb",
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "06_v2_baseline_modeling.ipynb",
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "06b_v2_baseline_sanity_audit.ipynb",
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "07_v2_xai_shap_interpretation.ipynb",
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "07r_v2_true_shap_interpretation.ipynb",
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "08_v2_segmentation_strategy.ipynb",
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "08b_v2_segmentation_refinement.ipynb",
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "08b_v2_segmentation_refinement_impl.py",
]


def rel(path):
    return str(Path(path).resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")


def snapshot_paths(paths):
    out = {}
    for path in paths:
        if path.exists() and path.is_file():
            stat = path.stat()
            out[rel(path)] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    return out


def snapshot_dirs(paths):
    out = {}
    for directory in paths:
        if not directory.exists() or not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file():
                stat = path.stat()
                out[rel(path)] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    return out


def write_csv(path, rows_or_df):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(rows_or_df, pd.DataFrame):
        df = rows_or_df
    else:
        df = pd.DataFrame(rows_or_df)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return df


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def num(series):
    return pd.to_numeric(series, errors="coerce")


def set_plot_style():
    plt.rcParams.update({
        "font.family": "Malgun Gothic",
        "font.sans-serif": ["Malgun Gothic", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "figure.dpi": 140,
        "savefig.dpi": 160,
    })


def save_table_figure(df, title, path, max_rows=12):
    set_plot_style()
    show = df.head(max_rows).copy()
    fig_h = max(3.2, 0.42 * len(show) + 1.2)
    fig, ax = plt.subplots(figsize=(14, fig_h))
    ax.axis("off")
    ax.set_title(title, pad=14)
    table = ax.table(cellText=show.values, colLabels=show.columns, cellLoc="left", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.35)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


raw_before = snapshot_paths(RAW_FILES)
stage_before = snapshot_dirs(STAGE_EXISTING_DIRS) | snapshot_paths(STAGE_EXISTING_FILES)

holdout_assign = pd.read_csv(STAGE08B_DATA / "08b_final_segment_assignments_holdout.csv")
full_assign = pd.read_csv(STAGE08B_DATA / "08b_final_segment_assignments_full_descriptive.csv")
stage08b_summary = json.loads((STAGE08B_DATA / "08b_segmentation_refinement_summary.json").read_text(encoding="utf-8"))
team_share_08b = (STAGE08B_DATA / "08b_team_share_final_segment_summary.md").read_text(encoding="utf-8")
seg_holdout = pd.read_csv(STAGE08B_TABLES / "08b_final_segment_summary_holdout.csv")
seg_full = pd.read_csv(STAGE08B_TABLES / "08b_final_segment_summary_full_descriptive.csv")
stage09_candidates = pd.read_csv(STAGE08B_TABLES / "08b_stage09_simulation_input_candidates.csv")
family_shap = pd.read_csv(STAGE07R_TABLES / "07r_feature_family_shap_importance.csv")
global_shap = pd.read_csv(STAGE07R_TABLES / "07r_global_shap_importance.csv")
team_share_07r = (STAGE07R_DATA / "07r_team_share_summary.md").read_text(encoding="utf-8")

for col in ["n", "repurchase_rate", "churn_rate", "avg_churn_risk_score", "captured_churners", "churner_capture_rate"]:
    if col in seg_holdout.columns:
        seg_holdout[col] = num(seg_holdout[col])
    if col in seg_full.columns:
        seg_full[col] = num(seg_full[col])

input_summary = write_csv(TABLE_DIR / "09_v2_input_summary.csv", [
    {"input": "08b_final_segment_assignments_holdout", "path": rel(STAGE08B_DATA / "08b_final_segment_assignments_holdout.csv"), "rows": len(holdout_assign), "role": "official Stage 08b holdout segment assignments"},
    {"input": "08b_final_segment_assignments_full_descriptive", "path": rel(STAGE08B_DATA / "08b_final_segment_assignments_full_descriptive.csv"), "rows": len(full_assign), "role": "full descriptive segment assignments"},
    {"input": "08b_stage09_simulation_input_candidates", "path": rel(STAGE08B_TABLES / "08b_stage09_simulation_input_candidates.csv"), "rows": len(stage09_candidates), "role": "candidate actions and placeholders"},
    {"input": "07r_feature_family_shap_importance", "path": rel(STAGE07R_TABLES / "07r_feature_family_shap_importance.csv"), "rows": len(family_shap), "role": "official TRUE SHAP XAI basis"},
    {"input": "07r_global_shap_importance", "path": rel(STAGE07R_TABLES / "07r_global_shap_importance.csv"), "rows": len(global_shap), "role": "official TRUE SHAP feature evidence"},
])

segment_name = stage09_candidates.set_index("final_segment_key")["final_segment_name_ko"].to_dict()
stage09_use = stage09_candidates.set_index("final_segment_key")["use_in_stage09_simulation"].to_dict()
segment_lever = stage09_candidates.set_index("final_segment_key")["proposed_intervention_lever"].to_dict()

baseline = seg_holdout[[
    "final_segment_key",
    "final_segment_name_ko",
    "n",
    "repurchase_rate",
    "churn_rate",
    "avg_churn_risk_score",
    "use_in_stage09_simulation",
]].copy()
baseline["expected_churners"] = baseline["n"] * baseline["churn_rate"]
baseline["expected_repurchasers"] = baseline["n"] * baseline["repurchase_rate"]
baseline["segment_priority"] = baseline["final_segment_key"].map({
    "top_decile_high_churn_risk": 1,
    "risk_10_30_low_engagement": 2,
    "risk_10_30_other_review": 3,
    "late_week3_engaged_retention_candidate": 4,
    "genre_affinity_content_recommendation_pool": 5,
    "low_risk_or_general_maintenance": 9,
})
baseline["baseline_source"] = "Stage08b holdout observed outcomes"
baseline = baseline.sort_values("segment_priority")
write_csv(TABLE_DIR / "09_v2_segment_baseline_summary.csv", baseline)

assumption_rows = [
    {
        "final_segment_key": "top_decile_high_churn_risk",
        "final_segment_name_ko": segment_name["top_decile_high_churn_risk"],
        "reachable_rate": 0.85,
        "treatment_rate": 0.85,
        "response_rate": 0.12,
        "incremental_retention_lift_low": 0.01,
        "incremental_retention_lift_base": 0.03,
        "incremental_retention_lift_high": 0.05,
        "cost_per_contact": np.nan,
        "gross_margin_per_retained_user": np.nan,
        "contact_fatigue_penalty_rate": 0.02,
        "max_contact_capacity": np.nan,
        "action_type": "high-risk targeted retention",
        "action_description": "고위험 모니터링, 개인화 리텐션 메시지, 초기 콘텐츠 재추천",
        "assumption_source": "editable_placeholder_assumption_not_fact",
    },
    {
        "final_segment_key": "risk_10_30_low_engagement",
        "final_segment_name_ko": segment_name["risk_10_30_low_engagement"],
        "reachable_rate": 0.85,
        "treatment_rate": 0.80,
        "response_rate": 0.15,
        "incremental_retention_lift_low": 0.01,
        "incremental_retention_lift_base": 0.03,
        "incremental_retention_lift_high": 0.05,
        "cost_per_contact": np.nan,
        "gross_margin_per_retained_user": np.nan,
        "contact_fatigue_penalty_rate": 0.02,
        "max_contact_capacity": np.nan,
        "action_type": "onboarding and activation",
        "action_description": "온보딩, 첫 시청 유도, 개인화 콘텐츠 추천",
        "assumption_source": "editable_placeholder_assumption_not_fact",
    },
    {
        "final_segment_key": "risk_10_30_other_review",
        "final_segment_name_ko": segment_name["risk_10_30_other_review"],
        "reachable_rate": 0.80,
        "treatment_rate": 0.70,
        "response_rate": 0.10,
        "incremental_retention_lift_low": 0.01,
        "incremental_retention_lift_base": 0.03,
        "incremental_retention_lift_high": 0.05,
        "cost_per_contact": np.nan,
        "gross_margin_per_retained_user": np.nan,
        "contact_fatigue_penalty_rate": 0.02,
        "max_contact_capacity": np.nan,
        "action_type": "risk-score guided recommendation",
        "action_description": "위험 점수 기반 모니터링, 장르/이용 패턴별 후속 추천",
        "assumption_source": "editable_placeholder_assumption_not_fact",
    },
    {
        "final_segment_key": "late_week3_engaged_retention_candidate",
        "final_segment_name_ko": segment_name["late_week3_engaged_retention_candidate"],
        "reachable_rate": 0.75,
        "treatment_rate": 0.50,
        "response_rate": 0.08,
        "incremental_retention_lift_low": 0.005,
        "incremental_retention_lift_base": 0.015,
        "incremental_retention_lift_high": 0.025,
        "cost_per_contact": np.nan,
        "gross_margin_per_retained_user": np.nan,
        "contact_fatigue_penalty_rate": 0.01,
        "max_contact_capacity": np.nan,
        "action_type": "maintenance continuation cue",
        "action_description": "이어보기, 시리즈 연속 추천, 종료 전 유지 메시지",
        "assumption_source": "editable_placeholder_assumption_not_fact",
    },
    {
        "final_segment_key": "genre_affinity_content_recommendation_pool",
        "final_segment_name_ko": segment_name["genre_affinity_content_recommendation_pool"],
        "reachable_rate": 0.75,
        "treatment_rate": 0.50,
        "response_rate": 0.08,
        "incremental_retention_lift_low": 0.005,
        "incremental_retention_lift_base": 0.015,
        "incremental_retention_lift_high": 0.025,
        "cost_per_contact": np.nan,
        "gross_margin_per_retained_user": np.nan,
        "contact_fatigue_penalty_rate": 0.01,
        "max_contact_capacity": np.nan,
        "action_type": "genre-based recommendation",
        "action_description": "장르별 이어보기, 신작/유사작 추천, 취향 기반 큐레이션",
        "assumption_source": "editable_placeholder_assumption_not_fact",
    },
    {
        "final_segment_key": "low_risk_or_general_maintenance",
        "final_segment_name_ko": segment_name["low_risk_or_general_maintenance"],
        "reachable_rate": 0.70,
        "treatment_rate": 0.20,
        "response_rate": 0.05,
        "incremental_retention_lift_low": 0.0,
        "incremental_retention_lift_base": 0.0,
        "incremental_retention_lift_high": 0.005,
        "cost_per_contact": np.nan,
        "gross_margin_per_retained_user": np.nan,
        "contact_fatigue_penalty_rate": 0.005,
        "max_contact_capacity": np.nan,
        "action_type": "monitoring only",
        "action_description": "과도한 개입보다 기본 추천과 모니터링 유지",
        "assumption_source": "editable_placeholder_assumption_not_fact",
    },
]
assumptions = pd.DataFrame(assumption_rows)
write_csv(DATA_DIR / "09_v2_editable_assumption_template.csv", assumptions)
write_csv(TABLE_DIR / "09_v2_assumption_scenarios.csv", assumptions)

family_strength = family_shap.set_index("feature_family")["mean_abs_shap"].to_dict()
action_rows = [
    {
        "final_segment_key": "top_decile_high_churn_risk",
        "final_segment_name_ko": segment_name["top_decile_high_churn_risk"],
        "primary_risk_mechanism_hypothesis": "usage, genre, and membership signals jointly indicate low predicted repurchase probability.",
        "top_shap_evidence_family": "usage|genre|membership",
        "recommended_action": "고위험 모니터링, 개인화 리텐션 메시지, 초기 콘텐츠 재추천",
        "timing": "w1_3 early-observation period or immediately after risk scoring",
        "message_example_ko": "최근 이용 패턴에 맞춘 추천작을 준비했어요. 지금 이어서 볼 만한 콘텐츠를 확인해 보세요.",
        "channel_suggestion": "app push or in-app message",
        "risk_of_over_contact": "medium",
        "why_plausible": f"Stage 07r TRUE SHAP shows usage={family_strength.get('usage', 0):.3f}, genre={family_strength.get('genre', 0):.3f}, membership={family_strength.get('membership', 0):.3f}.",
        "what_not_to_claim": "Do not claim the message causes repurchase without experiment.",
    },
    {
        "final_segment_key": "risk_10_30_low_engagement",
        "final_segment_name_ko": segment_name["risk_10_30_low_engagement"],
        "primary_risk_mechanism_hypothesis": "Low or no early engagement is associated with higher churn-risk score.",
        "top_shap_evidence_family": "usage",
        "recommended_action": "온보딩, 첫 시청 유도, 개인화 콘텐츠 추천",
        "timing": "early subscription period after low engagement is detected",
        "message_example_ko": "아직 많이 시청하지 않으셨다면, 취향에 맞는 첫 추천작부터 가볍게 시작해 보세요.",
        "channel_suggestion": "app push, email, or onboarding banner",
        "risk_of_over_contact": "medium",
        "why_plausible": "Usage is the strongest Stage 07r TRUE SHAP family.",
        "what_not_to_claim": "Do not claim forcing early viewing will cause repurchase.",
    },
    {
        "final_segment_key": "risk_10_30_other_review",
        "final_segment_name_ko": segment_name["risk_10_30_other_review"],
        "primary_risk_mechanism_hypothesis": "Risk score is high, but no single rule explains the segment cleanly.",
        "top_shap_evidence_family": "usage|genre",
        "recommended_action": "위험 점수 기반 모니터링, 장르/이용 패턴별 후속 추천",
        "timing": "after risk scoring and before subscription end",
        "message_example_ko": "최근 관심사에 맞춰 이어볼 만한 콘텐츠를 골라봤어요.",
        "channel_suggestion": "personalized recommendation surface",
        "risk_of_over_contact": "medium_high",
        "why_plausible": "Usage and genre families are important, but segment is more assumption-sensitive.",
        "what_not_to_claim": "Do not claim a specific mechanism until additional diagnosis.",
    },
    {
        "final_segment_key": "late_week3_engaged_retention_candidate",
        "final_segment_name_ko": segment_name["late_week3_engaged_retention_candidate"],
        "primary_risk_mechanism_hypothesis": "Week-3 engagement appears consistent with lower churn and may benefit from continuation cues.",
        "top_shap_evidence_family": "usage",
        "recommended_action": "이어보기, 시리즈 연속 추천, 종료 전 유지 메시지",
        "timing": "late w1_3 / near week 3, not framed as early warning",
        "message_example_ko": "이어보던 콘텐츠와 비슷한 작품을 계속 즐겨보세요.",
        "channel_suggestion": "in-app recommendation or watch-next module",
        "risk_of_over_contact": "low_medium",
        "why_plausible": "w1_3 week3 watch time is the top Stage 07r SHAP driver.",
        "what_not_to_claim": "Do not call this group high-risk.",
    },
    {
        "final_segment_key": "genre_affinity_content_recommendation_pool",
        "final_segment_name_ko": segment_name["genre_affinity_content_recommendation_pool"],
        "primary_risk_mechanism_hypothesis": "Genre affinity may support content continuation or recommendation action.",
        "top_shap_evidence_family": "genre",
        "recommended_action": "장르별 이어보기, 신작/유사작 추천, 취향 기반 큐레이션",
        "timing": "after enough genre preference signal appears",
        "message_example_ko": "즐겨보신 장르와 비슷한 신작을 추천해 드릴게요.",
        "channel_suggestion": "recommendation rail, app push only for high-confidence cases",
        "risk_of_over_contact": "medium",
        "why_plausible": "Genre is the second strongest Stage 07r TRUE SHAP family, but v2 metadata is limited.",
        "what_not_to_claim": "Do not claim rich content metadata or causal genre effect.",
    },
    {
        "final_segment_key": "low_risk_or_general_maintenance",
        "final_segment_name_ko": segment_name["low_risk_or_general_maintenance"],
        "primary_risk_mechanism_hypothesis": "Lower observed churn suggests aggressive retention contact is not the priority.",
        "top_shap_evidence_family": "usage|genre|membership",
        "recommended_action": "과도한 개입보다 기본 추천과 모니터링 유지",
        "timing": "always-on low-cost monitoring",
        "message_example_ko": "취향에 맞는 추천 콘텐츠를 계속 확인해 보세요.",
        "channel_suggestion": "standard recommendation surface",
        "risk_of_over_contact": "high if targeted too aggressively",
        "why_plausible": "Segment is not a Stage 09 primary target and should mainly serve as context.",
        "what_not_to_claim": "Do not present as an aggressive retention target.",
    },
]
action_mapping = write_csv(TABLE_DIR / "09_v2_segment_action_mapping.csv", action_rows)


def compute_segment_scenarios():
    rows = []
    baseline_by_segment = baseline.set_index("final_segment_key").to_dict(orient="index")
    for _, assumption in assumptions.iterrows():
        key = assumption["final_segment_key"]
        base = baseline_by_segment[key]
        n = float(base["n"])
        churn_rate = float(base["churn_rate"])
        baseline_churners = n * churn_rate
        reachable = n * float(assumption["reachable_rate"])
        treated_raw = reachable * float(assumption["treatment_rate"])
        max_capacity = assumption["max_contact_capacity"]
        if pd.notna(max_capacity):
            treated = min(treated_raw, float(max_capacity))
            capacity_applied = "Y"
        else:
            treated = treated_raw
            capacity_applied = "N"
        responders = treated * float(assumption["response_rate"])
        treated_expected_churners = treated * churn_rate
        for scenario in ["low", "base", "high"]:
            lift = float(assumption[f"incremental_retention_lift_{scenario}"])
            raw_incremental = treated * lift
            incremental_retained = min(raw_incremental, treated_expected_churners)
            post_churners = max(baseline_churners - incremental_retained, 0.0)
            post_churn_rate = post_churners / n if n else np.nan
            churn_reduction_pp = churn_rate - post_churn_rate
            cost = assumption["cost_per_contact"]
            margin = assumption["gross_margin_per_retained_user"]
            has_cost = pd.notna(cost)
            has_margin = pd.notna(margin)
            campaign_cost = treated * float(cost) if has_cost else np.nan
            gross_value = incremental_retained * float(margin) if has_margin else np.nan
            net_value = gross_value - campaign_cost if has_cost and has_margin else np.nan
            roi = net_value / campaign_cost if has_cost and has_margin and campaign_cost else np.nan
            rows.append({
                "final_segment_key": key,
                "final_segment_name_ko": assumption["final_segment_name_ko"],
                "scenario": scenario,
                "n": n,
                "observed_churn_rate": churn_rate,
                "baseline_churners": baseline_churners,
                "reachable_rate_assumption": float(assumption["reachable_rate"]),
                "treatment_rate_assumption": float(assumption["treatment_rate"]),
                "response_rate_assumption": float(assumption["response_rate"]),
                "incremental_retention_lift_assumption": lift,
                "cost_per_contact_assumption": cost,
                "gross_margin_per_retained_user_assumption": margin,
                "contact_fatigue_penalty_rate_assumption": float(assumption["contact_fatigue_penalty_rate"]),
                "max_contact_capacity_assumption": max_capacity,
                "capacity_cap_applied": capacity_applied,
                "reachable_users": reachable,
                "treated_users": treated,
                "expected_responders": responders,
                "treated_expected_churners": treated_expected_churners,
                "incremental_retained_users": incremental_retained,
                "post_action_churners": post_churners,
                "post_action_churn_rate": post_churn_rate,
                "churn_rate_reduction_pp": churn_reduction_pp,
                "campaign_cost": campaign_cost,
                "gross_retention_value": gross_value,
                "net_value": net_value,
                "roi": roi,
                "financial_status": "computed" if has_cost and has_margin else "assumption_required_no_profit_claim",
                "assumption_source": assumption["assumption_source"],
            })
    return pd.DataFrame(rows)


segment_sim = compute_segment_scenarios()
write_csv(TABLE_DIR / "09_v2_segment_simulation_low_base_high.csv", segment_sim)

portfolio_rows = []
for portfolio_name, segments in PORTFOLIOS.items():
    for scenario in ["low", "base", "high"]:
        subset = segment_sim[
            segment_sim["final_segment_key"].isin(segments)
            & segment_sim["scenario"].eq(scenario)
        ]
        total_targeted = float(subset["n"].sum())
        total_contact_volume = float(subset["treated_users"].sum())
        total_incremental = float(subset["incremental_retained_users"].sum())
        baseline_churners = float(subset["baseline_churners"].sum())
        total_cost = subset["campaign_cost"].sum(min_count=1)
        total_net = subset["net_value"].sum(min_count=1)
        total_roi = total_net / total_cost if pd.notna(total_cost) and total_cost else np.nan
        portfolio_rows.append({
            "portfolio_scenario": portfolio_name,
            "scenario": scenario,
            "included_segments": "|".join(segments),
            "total_targeted_users": total_targeted,
            "contact_volume_treated_users": total_contact_volume,
            "total_expected_incremental_retained_users": total_incremental,
            "total_expected_churn_reduction": total_incremental,
            "baseline_churners_in_portfolio": baseline_churners,
            "portfolio_churner_reduction_share": total_incremental / baseline_churners if baseline_churners else np.nan,
            "total_campaign_cost": total_cost,
            "total_net_value": total_net,
            "roi": total_roi,
            "financial_status": "computed" if pd.notna(total_cost) and pd.notna(total_net) else "assumption_required_no_profit_claim",
            "operational_caution": {
                "high_risk_only": "Safest presentation scope and smallest contact volume.",
                "high_risk_plus_low_engagement": "Still focused, but requires onboarding execution capacity.",
                "broad_risk": "More aggressive high-risk contact; watch contact fatigue.",
                "maintenance_light": "Largest scope; maintenance and recommendation effects are more assumption-sensitive.",
            }[portfolio_name],
            "assumption_source": "portfolio aggregation of editable placeholder assumptions",
        })
portfolio_summary = write_csv(TABLE_DIR / "09_v2_portfolio_simulation_summary.csv", portfolio_rows)

financial_status = write_csv(TABLE_DIR / "09_v2_financial_assumption_status.csv", [
    {
        "financial_item": "cost_per_contact",
        "status": "missing_editable_assumption",
        "business_effect": "campaign_cost cannot be claimed",
        "where_to_fill": rel(DATA_DIR / "09_v2_editable_assumption_template.csv"),
    },
    {
        "financial_item": "gross_margin_per_retained_user",
        "status": "missing_editable_assumption",
        "business_effect": "gross_retention_value, net_value, and ROI cannot be claimed",
        "where_to_fill": rel(DATA_DIR / "09_v2_editable_assumption_template.csv"),
    },
    {
        "financial_item": "response_rate and incremental_retention_lift",
        "status": "placeholder_assumptions_only",
        "business_effect": "incremental retained users are scenario outputs, not experimental facts",
        "where_to_fill": rel(DATA_DIR / "09_v2_editable_assumption_template.csv"),
    },
])

sensitivity_rows = []
for key in SIMULATION_CANDIDATES:
    subset = segment_sim[segment_sim["final_segment_key"].eq(key)]
    low = float(subset.loc[subset["scenario"].eq("low"), "incremental_retained_users"].iloc[0])
    base_case = float(subset.loc[subset["scenario"].eq("base"), "incremental_retained_users"].iloc[0])
    high = float(subset.loc[subset["scenario"].eq("high"), "incremental_retained_users"].iloc[0])
    sensitivity_rows.append({
        "final_segment_key": key,
        "final_segment_name_ko": segment_name[key],
        "low_incremental_retained_users": low,
        "base_incremental_retained_users": base_case,
        "high_incremental_retained_users": high,
        "high_minus_low_range": high - low,
        "dominant_assumption": "incremental_retention_lift",
        "sensitivity_note": "Reachable/treatment rates set contact volume; lift assumption dominates retained-user delta.",
    })
sensitivity = write_csv(TABLE_DIR / "09_v2_simulation_sensitivity_summary.csv", sensitivity_rows)

readiness_rows = []
for key in PRIMARY_SEGMENTS:
    base_row = baseline[baseline["final_segment_key"].eq(key)].iloc[0]
    if key == "low_risk_or_general_maintenance":
        classification = "do_not_claim_yet"
    elif key in ["top_decile_high_churn_risk", "risk_10_30_low_engagement"]:
        classification = "safe_to_report"
    elif key == "risk_10_30_other_review":
        classification = "plausible_but_cautioned"
    else:
        classification = "assumption_sensitive"
    readiness_rows.append({
        "final_segment_key": key,
        "final_segment_name_ko": segment_name[key],
        "classification": classification,
        "descriptive_model_output": f"holdout churn_rate={float(base_row['churn_rate']):.3f}",
        "assumed_business_effect": "incremental_retention_lift_low/base/high are placeholder assumptions",
        "safe_to_report": "Scenario retained-user impact under explicit assumptions",
        "must_not_claim": "causal lift, guaranteed retention, profit, or ROI without experiment and cost/margin",
    })
business_readiness = write_csv(TABLE_DIR / "09_v2_business_readiness_findings.csv", readiness_rows)


set_plot_style()
base_segment = segment_sim[segment_sim["scenario"].eq("base") & segment_sim["final_segment_key"].isin(SIMULATION_CANDIDATES)].copy()
base_segment = base_segment.sort_values("incremental_retained_users", ascending=True)
fig, ax = plt.subplots(figsize=(10.5, 5.8))
ax.barh(base_segment["final_segment_name_ko"], base_segment["incremental_retained_users"], color="#378ADD")
ax.set_title("09 base scenario incremental retained users by segment")
ax.set_xlabel("Incremental retained users, assumption-based")
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()
fig.savefig(FIGURE_DIR / "09_v2_incremental_retained_users_by_segment.png", bbox_inches="tight")
plt.close(fig)

set_plot_style()
portfolio_plot = portfolio_summary[portfolio_summary["scenario"].eq("base")].copy()
fig, ax = plt.subplots(figsize=(10, 5.3))
ax.bar(portfolio_plot["portfolio_scenario"], portfolio_plot["total_expected_incremental_retained_users"], color="#1D9E75")
ax.set_title("09 base scenario portfolio incremental retained users")
ax.set_ylabel("Incremental retained users, assumption-based")
ax.tick_params(axis="x", rotation=20)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(FIGURE_DIR / "09_v2_portfolio_incremental_retained_users.png", bbox_inches="tight")
plt.close(fig)

action_fig = action_mapping[[
    "final_segment_name_ko",
    "recommended_action",
    "timing",
    "channel_suggestion",
    "what_not_to_claim",
]].rename(columns={
    "final_segment_name_ko": "segment",
    "recommended_action": "action",
    "channel_suggestion": "channel",
})
save_table_figure(action_fig, "09 segment action map", FIGURE_DIR / "09_v2_segment_action_map.png", max_rows=8)

set_plot_style()
tornado = sensitivity.sort_values("high_minus_low_range", ascending=True)
fig, ax = plt.subplots(figsize=(10.5, 5.5))
ax.barh(tornado["final_segment_name_ko"], tornado["high_minus_low_range"], color="#D4537E")
ax.set_title("09 assumption sensitivity tornado: high-low retained-user range")
ax.set_xlabel("High scenario minus low scenario incremental retained users")
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()
fig.savefig(FIGURE_DIR / "09_v2_assumption_sensitivity_tornado.png", bbox_inches="tight")
plt.close(fig)

summary_card = portfolio_summary[
    portfolio_summary["scenario"].eq("base")
][[
    "portfolio_scenario",
    "total_targeted_users",
    "contact_volume_treated_users",
    "total_expected_incremental_retained_users",
    "financial_status",
]].copy()
summary_card["total_targeted_users"] = summary_card["total_targeted_users"].round(1)
summary_card["contact_volume_treated_users"] = summary_card["contact_volume_treated_users"].round(1)
summary_card["total_expected_incremental_retained_users"] = summary_card["total_expected_incremental_retained_users"].round(1)
save_table_figure(summary_card, "09 business simulation summary card, base scenario", FIGURE_DIR / "09_v2_business_simulation_summary_card.png", max_rows=8)

best_safe_portfolio = "high_risk_plus_low_engagement"
too_aggressive_portfolio = "maintenance_light"
base_portfolio = portfolio_summary[portfolio_summary["scenario"].eq("base")]
summary = {
    "scope": "Stage 09 business simulation and retention action scenario only. No final deck/report generation.",
    "simulation_type": "scenario simulation, not causal proof or experiment result",
    "official_segment_basis": "Stage 08b final segments",
    "official_xai_basis": "Stage 07r TRUE SHAP",
    "stage07_fallback_used_as_final_evidence": False,
    "cost_margin_available": False,
    "financial_claim_status": "profit, net value, and ROI are not claimed because cost/margin assumptions are missing",
    "primary_simulation_segments": SIMULATION_CANDIDATES,
    "baseline_summary": baseline.to_dict(orient="records"),
    "base_segment_incremental_retained_users": base_segment.sort_values("incremental_retained_users", ascending=False).to_dict(orient="records"),
    "portfolio_base_summary": base_portfolio.to_dict(orient="records"),
    "presentation_safe_portfolio": best_safe_portfolio,
    "too_aggressive_portfolio": too_aggressive_portfolio,
    "dominant_assumptions": [
        "incremental_retention_lift",
        "treatment_rate",
        "reachable_rate",
        "real cost_per_contact and gross_margin_per_retained_user for financial claims",
    ],
}
write_json(DATA_DIR / "09_v2_business_simulation_summary.json", summary)

team_lines = [
    "# 09 v2 Team Share Business Simulation Summary",
    "",
    "## What This Is",
    "- Stage 09 is an assumption-based scenario simulation.",
    "- It is not causal proof, not an experiment result, and not a financial forecast.",
    "- Official segment basis: Stage 08b final segments.",
    "- Official XAI basis: Stage 07r TRUE SHAP.",
    "",
    "## Segment Baseline",
]
for _, row in baseline.iterrows():
    team_lines.append(
        f"- {row['final_segment_name_ko']}: n={int(row['n'])}, churn rate={row['churn_rate']:.3f}, "
        f"expected churners={row['expected_churners']:.1f}, Stage09={row['use_in_stage09_simulation']}."
    )
team_lines.extend([
    "",
    "## Assumed Low/Base/High Lift",
    "- High-risk groups: low 1pp, base 3pp, high 5pp incremental retention lift.",
    "- Maintenance/recommendation groups: lower placeholder lift where applicable.",
    "- All lift, reach, response, cost, and margin values are assumptions, not facts.",
    "",
    "## Base Scenario Incremental Retained Users",
])
for _, row in base_segment.sort_values("incremental_retained_users", ascending=False).iterrows():
    team_lines.append(f"- {row['final_segment_name_ko']}: {row['incremental_retained_users']:.1f} retained users.")
team_lines.extend([
    "",
    "## Portfolio Comparison",
])
for _, row in base_portfolio.iterrows():
    team_lines.append(
        f"- {row['portfolio_scenario']}: targeted={row['total_targeted_users']:.0f}, "
        f"treated={row['contact_volume_treated_users']:.1f}, retained={row['total_expected_incremental_retained_users']:.1f}, "
        f"financial={row['financial_status']}."
    )
team_lines.extend([
    "",
    "## Safe Presentation Wording",
    "- Under explicit placeholder assumptions, the scenario estimates possible retained-user impact by segment.",
    "- The safest presentation scope is high-risk-only or high-risk-plus-low-engagement.",
    "- Cost, margin, profit, and ROI require real business inputs before any claim.",
    "",
    "## Recommended Figures",
    "- 09_v2_incremental_retained_users_by_segment.png",
    "- 09_v2_portfolio_incremental_retained_users.png",
    "- 09_v2_assumption_sensitivity_tornado.png",
    "- 09_v2_business_simulation_summary_card.png",
])
(DATA_DIR / "09_v2_team_share_business_simulation_summary.md").write_text("\n".join(team_lines) + "\n", encoding="utf-8")

report_lines = [
    "# 09 v2 Business Simulation and Retention Strategy Report",
    "",
    f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
    "",
    "## 1. What Is Being Simulated",
    "This stage simulates retained-user impact under explicit low/base/high intervention assumptions for Stage 08b final segments. It is not causal proof and not an experiment result.",
    "",
    "## 2. Included Segments",
]
for segment in PRIMARY_SEGMENTS:
    report_lines.append(f"- {segment_name[segment]} (`{segment}`): Stage09={stage09_use[segment]}.")
report_lines.extend([
    "",
    "## 3. Assumptions Used",
    "- reachable_rate, treatment_rate, response_rate, incremental_retention_lift_low/base/high, contact_fatigue_penalty_rate, and max_contact_capacity are editable assumptions.",
    "- cost_per_contact and gross_margin_per_retained_user are intentionally blank because no real business values were provided.",
    "",
    "## 4. Facts Versus Placeholders",
    "- Facts from current artifacts: Stage 08b segment membership, holdout n, observed holdout churn rate, observed holdout repurchase rate, and Stage 07r TRUE SHAP evidence.",
    "- Placeholders: all lift, reach, treatment, response, cost, margin, and fatigue values.",
    "",
    "## 5. Incremental Retained Users Under Low/Base/High",
])
for segment in SIMULATION_CANDIDATES:
    rows = segment_sim[segment_sim["final_segment_key"].eq(segment)].set_index("scenario")
    report_lines.append(
        f"- {segment_name[segment]}: low={rows.loc['low', 'incremental_retained_users']:.1f}, "
        f"base={rows.loc['base', 'incremental_retained_users']:.1f}, high={rows.loc['high', 'incremental_retained_users']:.1f}."
    )
report_lines.extend([
    "",
    "## 6. Most Presentation-Safe Portfolio",
    f"The most presentation-safe portfolio is `{best_safe_portfolio}` because it stays focused on high-risk customers while adding a clear low-engagement action group. `high_risk_only` is the most conservative option; `maintenance_light` is broader and more assumption-sensitive.",
    "",
    "## 7. What Cannot Be Claimed Without Cost/Margin Data",
    "- Campaign cost cannot be claimed.",
    "- Gross retention value cannot be claimed.",
    "- Net value and ROI cannot be claimed.",
    "- Profitability cannot be claimed.",
    "",
    "## 8. What Needs A/B Testing",
    "- Whether each message or recommendation causes incremental retention.",
    "- Whether response rates are realistic.",
    "- Whether contact fatigue offsets the benefit.",
    "- Whether genre recommendation or onboarding actions work differently by segment.",
    "",
    "## 9. Feed Into Final Presentation",
    "- Use retained-user impact ranges, not profit, unless real cost and margin are supplied.",
    "- Present Stage 09 as scenario planning based on model segments and assumptions.",
    "- Pair every simulated result with the assumption row that generated it.",
    "",
    "## 10. Exclude From Final Claims",
    "- Causal claims.",
    "- Guaranteed retention lift.",
    "- Financial ROI.",
    "- Any claim based on Stage 07 fallback as final evidence.",
    "",
    "## 09 Internal Critique and Simulation Reliability Review",
    "- Dominant assumptions: incremental retention lift, treatment rate, reachable rate, and real cost/margin if financial claims are desired.",
    "- Most sensitive segments: high-volume or high-risk segments where the high-low retained-user range is largest.",
    f"- Safest scenario to present: `{best_safe_portfolio}`; most conservative scenario is `high_risk_only`.",
    f"- Too aggressive scenario: `{too_aggressive_portfolio}` because it combines high-risk targeting with maintenance/recommendation groups and larger contact volume.",
    "- Financial claims cannot be made until cost_per_contact and gross_margin_per_retained_user are supplied.",
    "- Intervention claims require A/B testing before being treated as effects.",
    "- Descriptive model outputs: segment n, observed churn rate, expected churners. Assumed business effects: reach, response, lift, cost, margin, retained-user increments.",
])
(DATA_DIR / "09_v2_business_simulation_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

required_outputs = [
    DATA_DIR / "09_v2_business_simulation_summary.json",
    DATA_DIR / "09_v2_editable_assumption_template.csv",
    DATA_DIR / "09_v2_team_share_business_simulation_summary.md",
    DATA_DIR / "09_v2_business_simulation_report.md",
    TABLE_DIR / "09_v2_segment_baseline_summary.csv",
    TABLE_DIR / "09_v2_segment_action_mapping.csv",
    TABLE_DIR / "09_v2_assumption_scenarios.csv",
    TABLE_DIR / "09_v2_segment_simulation_low_base_high.csv",
    TABLE_DIR / "09_v2_portfolio_simulation_summary.csv",
    TABLE_DIR / "09_v2_financial_assumption_status.csv",
    TABLE_DIR / "09_v2_business_readiness_findings.csv",
    TABLE_DIR / "09_v2_simulation_sensitivity_summary.csv",
    TABLE_DIR / "09_v2_final_checks.csv",
    FIGURE_DIR / "09_v2_incremental_retained_users_by_segment.png",
    FIGURE_DIR / "09_v2_portfolio_incremental_retained_users.png",
    FIGURE_DIR / "09_v2_segment_action_map.png",
    FIGURE_DIR / "09_v2_assumption_sensitivity_tornado.png",
    FIGURE_DIR / "09_v2_business_simulation_summary_card.png",
]

official_stage08b_segments = set(stage09_candidates["final_segment_key"])
used_segments = set(baseline["final_segment_key"])
raw_after = snapshot_paths(RAW_FILES)
stage_after = snapshot_dirs(STAGE_EXISTING_DIRS) | snapshot_paths(STAGE_EXISTING_FILES)
financial_missing = assumptions["cost_per_contact"].isna().all() and assumptions["gross_margin_per_retained_user"].isna().all()
financial_not_claimed = segment_sim["financial_status"].eq("assumption_required_no_profit_claim").all()
assumptions_labeled = assumptions["assumption_source"].eq("editable_placeholder_assumption_not_fact").all()
scenario_set_ok = set(segment_sim["scenario"]) == {"low", "base", "high"}
portfolio_ok = set(portfolio_summary["portfolio_scenario"]) == set(PORTFOLIOS.keys())
internal_critique = "09 Internal Critique and Simulation Reliability Review" in (DATA_DIR / "09_v2_business_simulation_report.md").read_text(encoding="utf-8")

final_checks = [
    {"check": "raw_files_unchanged", "status": "PASS" if raw_before == raw_after else "FAIL", "detail": "raw snapshots unchanged"},
    {"check": "no_project_root_data_output_created", "status": "PASS" if not (PROJECT_ROOT / "_data" / "09_v2_business_simulation").exists() and not (PROJECT_ROOT / "_data" / "02_interim" / "09_v2_business_simulation").exists() else "FAIL", "detail": "Stage 09 writes only under park.ingyeom/reports"},
    {"check": "stage01_through_stage08b_outputs_not_overwritten", "status": "PASS" if stage_before == stage_after else "FAIL", "detail": "Stage 01-08b snapshots unchanged"},
    {"check": "stage07r_true_shap_used_as_xai_basis", "status": "PASS" if len(family_shap) > 0 and len(global_shap) > 0 else "FAIL", "detail": "Stage 07r TRUE SHAP tables read"},
    {"check": "stage07_fallback_not_used_as_final_evidence", "status": "PASS", "detail": "No Stage 07 fallback files read"},
    {"check": "no_model_training_performed", "status": "PASS", "detail": "No model libraries or fit calls used"},
    {"check": "no_shap_run", "status": "PASS", "detail": "No shap import or computation used"},
    {"check": "no_optuna_run", "status": "PASS", "detail": "No Optuna import or tuning used"},
    {"check": "no_segmentation_redefinition_beyond_stage08b_final_segments", "status": "PASS" if used_segments.issubset(official_stage08b_segments) else "FAIL", "detail": "|".join(sorted(used_segments))},
    {"check": "financial_impact_not_claimed_without_cost_margin", "status": "PASS" if financial_missing and financial_not_claimed else "FAIL", "detail": "cost/margin blank; financial outputs marked assumption_required"},
    {"check": "lift_response_cost_margin_values_labeled_assumptions", "status": "PASS" if assumptions_labeled else "FAIL", "detail": "editable_placeholder_assumption_not_fact"},
    {"check": "low_base_high_scenarios_created", "status": "PASS" if scenario_set_ok else "FAIL", "detail": "|".join(sorted(set(segment_sim["scenario"])))},
    {"check": "portfolio_scenarios_created", "status": "PASS" if portfolio_ok else "FAIL", "detail": "|".join(sorted(set(portfolio_summary["portfolio_scenario"])))},
    {"check": "internal_critique_created", "status": "PASS" if internal_critique else "FAIL", "detail": "report contains required section"},
    {"check": "final_report_and_team_share_summary_created", "status": "PASS" if (DATA_DIR / "09_v2_business_simulation_report.md").exists() and (DATA_DIR / "09_v2_team_share_business_simulation_summary.md").exists() else "FAIL", "detail": "report and team-share summary"},
    {"check": "all_required_outputs_created", "status": "PENDING", "detail": f"required_outputs={len(required_outputs)}"},
]
write_csv(TABLE_DIR / "09_v2_final_checks.csv", final_checks)
all_required = all(path.exists() for path in required_outputs)
final_checks[-1]["status"] = "PASS" if all_required else "FAIL"
final_checks[-1]["detail"] = "all required outputs exist" if all_required else "|".join(rel(path) for path in required_outputs if not path.exists())
write_csv(TABLE_DIR / "09_v2_final_checks.csv", final_checks)

print("09_v2 business simulation completed.")
for row in final_checks:
    print(f"{row['check']}: {row['status']} - {row['detail']}")
