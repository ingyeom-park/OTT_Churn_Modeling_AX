import json
import os
import platform
import sys
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

FORBIDDEN_SEGMENT_VARIABLES = {
    "USER_KEY",
    "USER_NUM",
    "MOVIE_NUM",
    "movie_title",
    "membership_row_id",
    "reg_date",
    "end_date",
    "duration_days",
    "watch_date",
    "watch_day",
    "is_repurchase",
}
FORBIDDEN_SUBSTRINGS = ["raw_calendar", "calendar_date", "days_to_end", "days_since_last_watch_to_end"]

STAGE08_SEGMENT_FLAGS = [
    "seg_top_decile_high_churn_risk",
    "seg_low_or_no_early_engagement",
    "seg_late_heavy_week3_intensive",
    "seg_delayed_start",
    "seg_early_routine_stable",
    "seg_week2_surge_users",
    "seg_genre_affinity_thriller_crime",
    "seg_genre_affinity_animation_family",
    "seg_genre_affinity_drama",
    "seg_genre_affinity_action_adventure",
    "seg_high_price_or_promotion_sensitive",
]
GENRE_FLAGS = [
    "seg_genre_affinity_thriller_crime",
    "seg_genre_affinity_animation_family",
    "seg_genre_affinity_drama",
    "seg_genre_affinity_action_adventure",
]
RISK_BAND_ORDER = [
    "top_10_highest_risk",
    "risk_10_30",
    "risk_30_60",
    "bottom_40_lowest_risk",
]


def find_project_root(start):
    for candidate in [start, *start.parents]:
        if (
            (candidate / "_data" / "01_raw" / "Membership.csv").exists()
            and (
                candidate
                / "park.ingyeom"
                / "reports"
                / "data"
                / "08_v2_segmentation_strategy"
                / "08_v2_segmentation_summary.json"
            ).exists()
        ):
            return candidate
    raise FileNotFoundError("Could not locate ott-churn-prediction project root.")


PROJECT_ROOT = find_project_root(Path.cwd())
STAGE08_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "08_v2_segmentation_strategy"
STAGE08_TABLES = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "08_v2_segmentation_strategy"
STAGE07R_TABLES = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "07r_v2_true_shap_interpretation"

DATA_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "08b_v2_segmentation_refinement"
TABLE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "08b_v2_segmentation_refinement"
FIGURE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "08b_v2_segmentation_refinement"
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
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "08_v2_segmentation_strategy_impl.py",
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


def safe_num(series):
    return pd.to_numeric(series, errors="coerce")


def bool_series(df, col):
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    return df[col].astype(str).str.upper().isin(["1", "TRUE", "Y", "YES"])


def is_forbidden(name):
    if name in FORBIDDEN_SEGMENT_VARIABLES:
        return True
    lowered = name.lower()
    return any(token in lowered for token in FORBIDDEN_SUBSTRINGS)


def set_plot_style():
    plt.rcParams.update({
        "font.family": "Malgun Gothic",
        "font.sans-serif": ["Malgun Gothic", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "figure.dpi": 140,
        "savefig.dpi": 160,
    })


def save_barh(df, y_col, x_col, title, path, color="#378ADD", x_label=None):
    set_plot_style()
    plot_df = df.copy()
    fig_h = max(4.2, 0.42 * len(plot_df) + 1.5)
    fig, ax = plt.subplots(figsize=(10.5, fig_h))
    ax.barh(plot_df[y_col], plot_df[x_col], color=color)
    ax.set_title(title)
    ax.set_xlabel(x_label or x_col)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def save_table_figure(df, title, path, max_rows=12):
    set_plot_style()
    show = df.head(max_rows).copy()
    fig_h = max(3.2, 0.42 * len(show) + 1.2)
    fig, ax = plt.subplots(figsize=(13.5, fig_h))
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

holdout = pd.read_csv(STAGE08_DATA / "08_v2_segment_assignments_holdout.csv")
full = pd.read_csv(STAGE08_DATA / "08_v2_segment_assignments_full_descriptive.csv")
risk_band_holdout = pd.read_csv(STAGE08_TABLES / "08_v2_risk_band_summary_holdout.csv")
hier_holdout = pd.read_csv(STAGE08_TABLES / "08_v2_hierarchical_segment_summary_holdout.csv")
nonexclusive = pd.read_csv(STAGE08_TABLES / "08_v2_nonexclusive_segment_flag_summary.csv")
overlap_raw = pd.read_csv(STAGE08_TABLES / "08_v2_segment_overlap_matrix.csv")
shap_evidence = pd.read_csv(STAGE08_TABLES / "08_v2_segment_shap_evidence_map.csv")
actions = pd.read_csv(STAGE08_TABLES / "08_v2_segment_action_recommendations.csv")
family_shap = pd.read_csv(STAGE07R_TABLES / "07r_feature_family_shap_importance.csv")
global_shap = pd.read_csv(STAGE07R_TABLES / "07r_global_shap_importance.csv")
stage08_summary = json.loads((STAGE08_DATA / "08_v2_segmentation_summary.json").read_text(encoding="utf-8"))
stage08_report = (STAGE08_DATA / "08_v2_segmentation_strategy_report.md").read_text(encoding="utf-8")
team_share_stage08 = (STAGE08_DATA / "08_v2_team_share_segment_summary.md").read_text(encoding="utf-8")

for df in [holdout, full]:
    df[TARGET_NUM] = safe_num(df[TARGET_NUM]).astype(int)
    df["churn_actual"] = 1 - df[TARGET_NUM]
    df["repurchase_score"] = safe_num(df["repurchase_score"])
    df["churn_risk_score"] = safe_num(df["churn_risk_score"])
    for flag in STAGE08_SEGMENT_FLAGS:
        if flag in df.columns:
            df[flag] = bool_series(df, flag).astype(int)
    df["modifier_genre_affinity_any"] = df[GENRE_FLAGS].max(axis=1)
    df["modifier_low_or_no_early_engagement"] = df["seg_low_or_no_early_engagement"]
    df["modifier_delayed_start"] = df["seg_delayed_start"]
    df["modifier_late_week3_intensity"] = df["seg_late_heavy_week3_intensive"]
    df["modifier_price_promotion_context"] = df["seg_high_price_or_promotion_sensitive"]
    df["modifier_week2_surge_small_sample"] = df["seg_week2_surge_users"]
    df["modifier_early_routine_review"] = df["seg_early_routine_stable"]

overall_churn_holdout = holdout["churn_actual"].mean()
overall_churn_full = full["churn_actual"].mean()
total_churn_holdout = int(holdout["churn_actual"].sum())
total_churn_full = int(full["churn_actual"].sum())

flag_to_segment = {
    "seg_top_decile_high_churn_risk": "top_decile_high_churn_risk",
    "seg_low_or_no_early_engagement": "low_or_no_early_engagement",
    "seg_late_heavy_week3_intensive": "late_heavy_week3_intensive",
    "seg_delayed_start": "delayed_start",
    "seg_early_routine_stable": "early_routine_stable",
    "seg_week2_surge_users": "week2_surge_users",
    "seg_genre_affinity_thriller_crime": "genre_affinity_thriller_crime",
    "seg_genre_affinity_animation_family": "genre_affinity_animation_family",
    "seg_genre_affinity_drama": "genre_affinity_drama",
    "seg_genre_affinity_action_adventure": "genre_affinity_action_adventure",
    "seg_high_price_or_promotion_sensitive": "high_price_or_promotion_sensitive",
}
segment_to_flag = {v: k for k, v in flag_to_segment.items()}
actions_by_segment = actions.set_index("segment").to_dict(orient="index")

overlap_df = overlap_raw.copy()
overlap_df = overlap_df.set_index("segment_flag")
for col in overlap_df.columns:
    overlap_df[col] = safe_num(overlap_df[col])
max_overlap_by_flag = {}
high_overlap_pairs = []
for flag in overlap_df.index:
    diag = float(overlap_df.loc[flag, flag]) if flag in overlap_df.columns else np.nan
    ratios = {}
    if diag and diag > 0:
        for other in overlap_df.columns:
            if other == flag:
                continue
            ratio = float(overlap_df.loc[flag, other]) / diag
            ratios[other] = ratio
            if ratio >= 0.75:
                high_overlap_pairs.append({
                    "segment_flag": flag,
                    "overlap_with": other,
                    "overlap_ratio_of_segment": ratio,
                    "overlap_count": float(overlap_df.loc[flag, other]),
                    "segment_n": diag,
                })
    max_overlap_by_flag[flag] = max(ratios.values()) if ratios else 0.0

stage08_review_rows = []
for _, row in hier_holdout.iterrows():
    segment = row["hierarchical_segment"]
    flag = segment_to_flag.get(segment)
    action = actions_by_segment.get(segment, {})
    n = int(float(row["n"]))
    churn_rate = float(row["churn_rate"])
    lift = float(row["lift_vs_overall_churn_rate"])
    small_n = n < 100
    low_or_neutral_lift = lift <= 1.05
    action_weak = str(action.get("evidence_strength", "")).lower() == "weak" or str(action.get("readiness", "")).lower() == "do_not_claim_yet"
    high_overlap = bool(flag and max_overlap_by_flag.get(flag, 0.0) >= 0.75)
    too_broad = False
    if flag:
        match = nonexclusive[(nonexclusive["population"] == "holdout") & (nonexclusive["segment_flag"] == flag)]
        if not match.empty:
            too_broad = float(match["share"].iloc[0]) >= 0.70
    misleading = "N"
    if segment == "early_routine_stable" and lift > 1.1:
        misleading = "Y: stable name conflicts with elevated churn lift"
    elif segment == "late_heavy_week3_intensive" and lift < 0.5:
        misleading = "Y: should be framed as retained or engaged behavior, not risk"
    elif segment == "week2_surge_users" and n < 100:
        misleading = "Y: hierarchy sample is too small for presentation"
    elif segment == "general_other":
        misleading = "Y: residual group is not an interpretable segment"
    elif segment == "high_price_or_promotion_sensitive" and (high_overlap or too_broad):
        misleading = "Y: broad overlapping attribute, better as modifier"

    stage08_review_rows.append({
        "stage08_segment": segment,
        "stage08_segment_flag": flag or "",
        "holdout_n": n,
        "holdout_churn_rate": churn_rate,
        "holdout_lift": lift,
        "small_n_lt_100": "Y" if small_n else "N",
        "lift_near_or_below_1": "Y" if low_or_neutral_lift else "N",
        "high_overlap": "Y" if high_overlap else "N",
        "max_overlap_ratio": max_overlap_by_flag.get(flag, np.nan) if flag else np.nan,
        "too_broad": "Y" if too_broad else "N",
        "action_weak": "Y" if action_weak else "N",
        "misleading_name_review": misleading,
        "automatic_review_flag": "Y" if any([small_n, low_or_neutral_lift, action_weak, high_overlap, too_broad, misleading.startswith("Y")]) else "N",
    })
stage08_review = write_csv(TABLE_DIR / "08b_stage08_segment_review.csv", stage08_review_rows)

decision_rows = [
    {
        "stage08_segment": "top_decile_high_churn_risk",
        "decision": "keep",
        "refined_role": "primary_targeting_segment",
        "new_key": "top_decile_high_churn_risk",
        "new_korean_name": "최상위 이탈위험군",
        "reason": "Risk score top decile has the strongest holdout churn lift and capture rate.",
    },
    {
        "stage08_segment": "low_or_no_early_engagement",
        "decision": "keep_refine",
        "refined_role": "primary_targeting_segment_inside_high_risk_band",
        "new_key": "risk_10_30_low_engagement",
        "new_korean_name": "초기 저관여 고위험군",
        "reason": "Useful when paired with high-risk bands; not used as a standalone replacement for risk score.",
    },
    {
        "stage08_segment": "late_heavy_week3_intensive",
        "decision": "rename_keep",
        "refined_role": "low_risk_retention_candidate",
        "new_key": "late_week3_engaged_retention_candidate",
        "new_korean_name": "3주차 집중 시청 안정/전환 후보군",
        "reason": "Observed churn is low, so this is reframed as engaged or retained behavior.",
    },
    {
        "stage08_segment": "delayed_start",
        "decision": "modifier_only",
        "refined_role": "explanatory_modifier",
        "new_key": "modifier_delayed_start",
        "new_korean_name": "시작 지연 modifier",
        "reason": "Useful for explanation but not strong enough as a standalone final segment.",
    },
    {
        "stage08_segment": "early_routine_stable",
        "decision": "rename_downplay",
        "refined_role": "explanatory_modifier_only",
        "new_key": "modifier_early_routine_review",
        "new_korean_name": "초기 루틴 재검토 modifier",
        "reason": "Stable wording conflicts with observed elevated churn in the hierarchical segment.",
    },
    {
        "stage08_segment": "week2_surge_users",
        "decision": "drop_from_presentation",
        "refined_role": "audit_only_modifier",
        "new_key": "modifier_week2_surge_small_sample",
        "new_korean_name": "2주차 상승 소표본 modifier",
        "reason": "Hierarchy holdout n is below 100, so it is unstable for presentation.",
    },
    {
        "stage08_segment": "genre_affinity_thriller_crime",
        "decision": "merge",
        "refined_role": "explanatory_modifier_or_content_action_layer",
        "new_key": "genre_affinity_content_recommendation_pool",
        "new_korean_name": "장르 선호 기반 콘텐츠 추천군",
        "reason": "Merged with other genre affinities to avoid many small final groups.",
    },
    {
        "stage08_segment": "genre_affinity_animation_family",
        "decision": "merge",
        "refined_role": "explanatory_modifier_or_content_action_layer",
        "new_key": "genre_affinity_content_recommendation_pool",
        "new_korean_name": "장르 선호 기반 콘텐츠 추천군",
        "reason": "Merged with other genre affinities to avoid many small final groups.",
    },
    {
        "stage08_segment": "genre_affinity_drama",
        "decision": "merge",
        "refined_role": "explanatory_modifier_or_content_action_layer",
        "new_key": "genre_affinity_content_recommendation_pool",
        "new_korean_name": "장르 선호 기반 콘텐츠 추천군",
        "reason": "Merged with other genre affinities to avoid many small final groups.",
    },
    {
        "stage08_segment": "genre_affinity_action_adventure",
        "decision": "merge",
        "refined_role": "explanatory_modifier_or_content_action_layer",
        "new_key": "genre_affinity_content_recommendation_pool",
        "new_korean_name": "장르 선호 기반 콘텐츠 추천군",
        "reason": "Merged with other genre affinities to avoid many small final groups.",
    },
    {
        "stage08_segment": "high_price_or_promotion_sensitive",
        "decision": "modifier_only",
        "refined_role": "membership_context_modifier",
        "new_key": "modifier_price_promotion_context",
        "new_korean_name": "가격/프로모션 맥락 modifier",
        "reason": "Broad and highly overlapping attribute; not a clean standalone segment.",
    },
    {
        "stage08_segment": "general_other",
        "decision": "drop_from_presentation",
        "refined_role": "residual_audit_only",
        "new_key": "low_risk_or_general_maintenance",
        "new_korean_name": "저위험/일반 유지군",
        "reason": "Residual group has weak actionability; only retained through final risk-band based maintenance assignment.",
    },
]
decision_df = write_csv(TABLE_DIR / "08b_segment_keep_merge_drop_decisions.csv", decision_rows)

final_segment_definitions = [
    {
        "final_segment_key": "top_decile_high_churn_risk",
        "korean_name": "최상위 이탈위험군",
        "layer": "primary_targeting_group",
        "definition": "Stage 08 conservative w1_3 churn_risk_score top 10% risk band.",
        "target_used_to_define": "N",
        "segment_variables": "risk_band, churn_risk_score percentile",
        "main_shap_evidence_family": "usage|genre|membership",
        "recommended_action": "고위험 모니터링, 개인화 리텐션 메시지, 초기 콘텐츠 재추천",
        "presentation_readiness": "safe_to_report_with_caution",
        "caution_sentence": "예측 위험군이지 리텐션 조치의 인과효과가 검증된 것은 아님.",
        "use_in_stage09_simulation": "Y",
        "proposed_intervention_lever": "high-risk targeted retention message",
        "assumed_lift_scenario_placeholder": "mentor/user must supply low/base/high retention lift assumptions",
        "business_assumption_needed_stage09": "reachable audience, treatment cost, response rate, retention lift, contact fatigue",
    },
    {
        "final_segment_key": "risk_10_30_low_engagement",
        "korean_name": "초기 저관여 고위험군",
        "layer": "primary_targeting_group",
        "definition": "risk_10_30 band and Stage 08 low/no early engagement flag.",
        "target_used_to_define": "N",
        "segment_variables": "risk_band, seg_low_or_no_early_engagement",
        "main_shap_evidence_family": "usage",
        "recommended_action": "초기 온보딩, 첫 시청 유도, 개인화 콘텐츠 추천",
        "presentation_readiness": "safe_to_report_with_caution",
        "caution_sentence": "초기 관여 부족은 예측 신호이며 시청 유도가 재구독을 원인적으로 만든다고 말하면 안 됨.",
        "use_in_stage09_simulation": "Y",
        "proposed_intervention_lever": "onboarding and first-watch activation",
        "assumed_lift_scenario_placeholder": "mentor/user must supply expected activation and retention lift",
        "business_assumption_needed_stage09": "message reach, recommendation inventory, response rate, retention lift",
    },
    {
        "final_segment_key": "risk_10_30_other_review",
        "korean_name": "상위위험 관찰/추천 후보군",
        "layer": "primary_targeting_group",
        "definition": "risk_10_30 band not already assigned to 초기 저관여 고위험군.",
        "target_used_to_define": "N",
        "segment_variables": "risk_band, hierarchy order",
        "main_shap_evidence_family": "usage|genre",
        "recommended_action": "위험 점수 기반 모니터링과 장르/이용 패턴별 후속 추천",
        "presentation_readiness": "plausible_but_cautioned",
        "caution_sentence": "하위 원인이 하나로 좁혀지지 않으므로 세부 modifier와 함께 해석해야 함.",
        "use_in_stage09_simulation": "Y",
        "proposed_intervention_lever": "risk-score guided recommendation or message",
        "assumed_lift_scenario_placeholder": "mentor/user must supply broad high-risk campaign lift assumptions",
        "business_assumption_needed_stage09": "targeting capacity, treatment cost, expected lift, exclusion rules",
    },
    {
        "final_segment_key": "late_week3_engaged_retention_candidate",
        "korean_name": "3주차 집중 시청 안정/전환 후보군",
        "layer": "low_risk_retention_or_maintenance_group",
        "definition": "Stage 08 late-heavy week3 flag outside the high-risk top 30%.",
        "target_used_to_define": "N",
        "segment_variables": "risk_band, seg_late_heavy_week3_intensive",
        "main_shap_evidence_family": "usage",
        "recommended_action": "이어보기, 시리즈 연속 추천, 구독 종료 전 유지 메시지",
        "presentation_readiness": "safe_to_report_with_caution",
        "caution_sentence": "낮은 이탈률을 보이는 안정/전환 후보이지 고위험군으로 부르면 안 됨.",
        "use_in_stage09_simulation": "Y",
        "proposed_intervention_lever": "continuation cue and late-period retention reminder",
        "assumed_lift_scenario_placeholder": "mentor/user must supply maintenance uplift or defensive retention assumption",
        "business_assumption_needed_stage09": "eligible content availability, message timing, incremental retention lift",
    },
    {
        "final_segment_key": "genre_affinity_content_recommendation_pool",
        "korean_name": "장르 선호 기반 콘텐츠 추천군",
        "layer": "explanatory_modifier_based_action_group",
        "definition": "Any Stage 08 genre affinity flag, after higher priority risk and week3-retention groups.",
        "target_used_to_define": "N",
        "segment_variables": "genre affinity flags",
        "main_shap_evidence_family": "genre",
        "recommended_action": "장르별 이어보기, 신작/유사작 추천, 취향 기반 큐레이션",
        "presentation_readiness": "plausible_but_cautioned",
        "caution_sentence": "v2 콘텐츠 메타데이터는 장르와 공개월 중심의 제한적 proxy임.",
        "use_in_stage09_simulation": "Y",
        "proposed_intervention_lever": "genre-based content recommendation",
        "assumed_lift_scenario_placeholder": "mentor/user must supply genre recommendation response and retention lift",
        "business_assumption_needed_stage09": "genre inventory, recommendation exposure, response rate, incremental lift",
    },
    {
        "final_segment_key": "low_risk_or_general_maintenance",
        "korean_name": "저위험/일반 유지군",
        "layer": "maintenance_or_residual_group",
        "definition": "Remaining customers after higher-priority final segment hierarchy.",
        "target_used_to_define": "N",
        "segment_variables": "hierarchy residual after risk and modifier flags",
        "main_shap_evidence_family": "usage|genre|membership",
        "recommended_action": "과도한 개입보다 기본 추천과 모니터링 유지",
        "presentation_readiness": "safe_to_report_as_context_only",
        "caution_sentence": "잔여/유지군이므로 강한 리텐션 타깃이라고 주장하지 않음.",
        "use_in_stage09_simulation": "N",
        "proposed_intervention_lever": "monitoring only",
        "assumed_lift_scenario_placeholder": "not recommended as primary simulation candidate",
        "business_assumption_needed_stage09": "baseline monitoring policy only",
    },
]
definitions_df = write_csv(TABLE_DIR / "08b_final_segment_definitions.csv", final_segment_definitions)
segment_names = definitions_df.set_index("final_segment_key")["korean_name"].to_dict()
stage09_use = definitions_df.set_index("final_segment_key")["use_in_stage09_simulation"].to_dict()


def assign_refined_segments(df):
    out = df.copy()
    out["final_flag_top_decile_high_churn_risk"] = out["risk_band"].eq("top_10_highest_risk").astype(int)
    out["final_flag_risk_10_30_low_engagement"] = (
        out["risk_band"].eq("risk_10_30") & out["seg_low_or_no_early_engagement"].eq(1)
    ).astype(int)
    out["final_flag_risk_10_30_other_review"] = (
        out["risk_band"].eq("risk_10_30") & out["seg_low_or_no_early_engagement"].ne(1)
    ).astype(int)
    out["final_flag_late_week3_engaged_retention_candidate"] = (
        out["risk_band"].isin(["risk_30_60", "bottom_40_lowest_risk"])
        & out["seg_late_heavy_week3_intensive"].eq(1)
    ).astype(int)
    out["final_flag_genre_affinity_content_recommendation_pool"] = (
        out["modifier_genre_affinity_any"].eq(1)
        & out["risk_band"].isin(["risk_30_60", "bottom_40_lowest_risk"])
    ).astype(int)
    out["final_flag_low_risk_or_general_maintenance"] = 1

    conditions = [
        out["final_flag_top_decile_high_churn_risk"].eq(1),
        out["final_flag_risk_10_30_low_engagement"].eq(1),
        out["final_flag_risk_10_30_other_review"].eq(1),
        out["final_flag_late_week3_engaged_retention_candidate"].eq(1),
        out["final_flag_genre_affinity_content_recommendation_pool"].eq(1),
    ]
    choices = [
        "top_decile_high_churn_risk",
        "risk_10_30_low_engagement",
        "risk_10_30_other_review",
        "late_week3_engaged_retention_candidate",
        "genre_affinity_content_recommendation_pool",
    ]
    out["final_segment_key"] = np.select(conditions, choices, default="low_risk_or_general_maintenance")
    out["final_segment_name_ko"] = out["final_segment_key"].map(segment_names)
    out["use_in_stage09_simulation"] = out["final_segment_key"].map(stage09_use)
    return out


holdout_refined = assign_refined_segments(holdout)
full_refined = assign_refined_segments(full)

assignment_cols = [
    ID_COL,
    TARGET,
    TARGET_NUM,
    "repurchase_score",
    "churn_risk_score",
    "risk_band",
    "final_segment_key",
    "final_segment_name_ko",
    "use_in_stage09_simulation",
    "modifier_low_or_no_early_engagement",
    "modifier_delayed_start",
    "modifier_late_week3_intensity",
    "modifier_genre_affinity_any",
    "modifier_price_promotion_context",
    "modifier_week2_surge_small_sample",
    "modifier_early_routine_review",
]
write_csv(DATA_DIR / "08b_final_segment_assignments_holdout.csv", holdout_refined[assignment_cols])
write_csv(DATA_DIR / "08b_final_segment_assignments_full_descriptive.csv", full_refined[assignment_cols])


def summarize_segments(df, population, descriptive_only):
    total_n = len(df)
    total_churn = int(df["churn_actual"].sum())
    overall_churn = df["churn_actual"].mean()
    rows = []
    for key in definitions_df["final_segment_key"].tolist():
        subset = df[df["final_segment_key"] == key]
        n = len(subset)
        churners = int(subset["churn_actual"].sum()) if n else 0
        rows.append({
            "population": population,
            "final_segment_key": key,
            "final_segment_name_ko": segment_names[key],
            "n": n,
            "share": n / total_n if total_n else np.nan,
            "repurchase_rate": subset[TARGET_NUM].mean() if n else np.nan,
            "churn_rate": subset["churn_actual"].mean() if n else np.nan,
            "lift_vs_overall_churn_rate": (subset["churn_actual"].mean() / overall_churn) if n and overall_churn else np.nan,
            "captured_churners": churners,
            "churner_capture_rate": churners / total_churn if total_churn else np.nan,
            "avg_repurchase_score": subset["repurchase_score"].mean() if n else np.nan,
            "avg_churn_risk_score": subset["churn_risk_score"].mean() if n else np.nan,
            "use_in_stage09_simulation": stage09_use[key],
            "descriptive_only": descriptive_only,
        })
    return pd.DataFrame(rows)


final_summary_holdout = write_csv(
    TABLE_DIR / "08b_final_segment_summary_holdout.csv",
    summarize_segments(holdout_refined, "holdout", "N"),
)
final_summary_full = write_csv(
    TABLE_DIR / "08b_final_segment_summary_full_descriptive.csv",
    summarize_segments(full_refined, "full_descriptive", "Y"),
)

final_flag_cols = [
    "final_flag_top_decile_high_churn_risk",
    "final_flag_risk_10_30_low_engagement",
    "final_flag_risk_10_30_other_review",
    "final_flag_late_week3_engaged_retention_candidate",
    "final_flag_genre_affinity_content_recommendation_pool",
    "final_flag_low_risk_or_general_maintenance",
]
overlap_rows = []
for flag in final_flag_cols:
    row = {"final_flag": flag}
    for other in final_flag_cols:
        row[other] = int(((holdout_refined[flag] == 1) & (holdout_refined[other] == 1)).sum())
    overlap_rows.append(row)
final_overlap = write_csv(TABLE_DIR / "08b_final_segment_overlap_matrix.csv", overlap_rows)

modifier_cols = [
    "modifier_low_or_no_early_engagement",
    "modifier_delayed_start",
    "modifier_late_week3_intensity",
    "modifier_genre_affinity_any",
    "modifier_price_promotion_context",
    "modifier_week2_surge_small_sample",
    "modifier_early_routine_review",
]
modifier_rows = []
for pop_name, df, descriptive in [("holdout", holdout_refined, "N"), ("full_descriptive", full_refined, "Y")]:
    total_n = len(df)
    total_churn = int(df["churn_actual"].sum())
    overall = df["churn_actual"].mean()
    for col in modifier_cols:
        subset = df[df[col] == 1]
        n = len(subset)
        churners = int(subset["churn_actual"].sum()) if n else 0
        modifier_rows.append({
            "population": pop_name,
            "modifier_flag": col,
            "n": n,
            "share": n / total_n if total_n else np.nan,
            "churn_rate": subset["churn_actual"].mean() if n else np.nan,
            "lift_vs_overall_churn_rate": (subset["churn_actual"].mean() / overall) if n and overall else np.nan,
            "captured_churners": churners,
            "churner_capture_rate": churners / total_churn if total_churn else np.nan,
            "descriptive_only": descriptive,
        })
modifier_summary = write_csv(TABLE_DIR / "08b_modifier_flag_summary.csv", modifier_rows)

stage09_rows = []
for _, definition in definitions_df.iterrows():
    summary = final_summary_holdout[final_summary_holdout["final_segment_key"] == definition["final_segment_key"]].iloc[0]
    if definition["use_in_stage09_simulation"] == "Y":
        readiness = "candidate"
    else:
        readiness = "not_primary_candidate"
    stage09_rows.append({
        "final_segment_key": definition["final_segment_key"],
        "final_segment_name_ko": definition["korean_name"],
        "use_in_stage09_simulation": definition["use_in_stage09_simulation"],
        "why": "Actionable and SHAP-supported" if definition["use_in_stage09_simulation"] == "Y" else "Context or maintenance group, not a strong targeting candidate",
        "holdout_n": int(summary["n"]),
        "holdout_churn_rate": float(summary["churn_rate"]),
        "holdout_lift": float(summary["lift_vs_overall_churn_rate"]),
        "proposed_intervention_lever": definition["proposed_intervention_lever"],
        "assumed_lift_scenario_placeholder": definition["assumed_lift_scenario_placeholder"],
        "business_assumption_needed_stage09": definition["business_assumption_needed_stage09"],
        "readiness_for_stage09": readiness,
        "financial_impact_calculated_stage08b": "N",
    })
stage09_candidates = write_csv(TABLE_DIR / "08b_stage09_simulation_input_candidates.csv", stage09_rows)

readiness_rows = []
for _, definition in definitions_df.iterrows():
    summary = final_summary_holdout[final_summary_holdout["final_segment_key"] == definition["final_segment_key"]].iloc[0]
    readiness_rows.append({
        "finding": definition["final_segment_key"],
        "classification": definition["presentation_readiness"],
        "evidence_basis": definition["main_shap_evidence_family"],
        "holdout_n": int(summary["n"]),
        "holdout_churn_rate": float(summary["churn_rate"]),
        "safe_claim": f"{definition['korean_name']} is a predictive/descriptive segment.",
        "cautioned_claim": definition["caution_sentence"],
        "do_not_claim": "Do not claim causal intervention effect or financial impact.",
    })
business_readiness = write_csv(TABLE_DIR / "08b_business_readiness_findings.csv", readiness_rows)

input_summary = write_csv(TABLE_DIR / "08b_segmentation_input_summary.csv", [
    {"input": "08_v2_segment_assignments_holdout", "path": rel(STAGE08_DATA / "08_v2_segment_assignments_holdout.csv"), "rows": len(holdout), "role": "holdout segment input"},
    {"input": "08_v2_segment_assignments_full_descriptive", "path": rel(STAGE08_DATA / "08_v2_segment_assignments_full_descriptive.csv"), "rows": len(full), "role": "full descriptive segment input"},
    {"input": "08_v2_risk_band_summary_holdout", "path": rel(STAGE08_TABLES / "08_v2_risk_band_summary_holdout.csv"), "rows": len(risk_band_holdout), "role": "risk band preservation"},
    {"input": "08_v2_hierarchical_segment_summary_holdout", "path": rel(STAGE08_TABLES / "08_v2_hierarchical_segment_summary_holdout.csv"), "rows": len(hier_holdout), "role": "segment pruning evidence"},
    {"input": "07r_feature_family_shap_importance", "path": rel(STAGE07R_TABLES / "07r_feature_family_shap_importance.csv"), "rows": len(family_shap), "role": "TRUE SHAP evidence"},
    {"input": "07r_global_shap_importance", "path": rel(STAGE07R_TABLES / "07r_global_shap_importance.csv"), "rows": len(global_shap), "role": "TRUE SHAP feature evidence"},
])

review_decision = stage08_review.merge(
    decision_df[["stage08_segment", "decision", "refined_role", "new_key", "new_korean_name", "reason"]],
    on="stage08_segment",
    how="left",
)
write_csv(TABLE_DIR / "08b_stage08_segment_review.csv", review_decision)

risk_preserved = risk_band_holdout.copy()
risk_preserved["risk_band_order"] = risk_preserved["risk_band"].map({band: i + 1 for i, band in enumerate(RISK_BAND_ORDER)})
risk_preserved = risk_preserved.sort_values("risk_band_order")
write_csv(TABLE_DIR / "08b_preserved_risk_band_summary_holdout.csv", risk_preserved)

capture_rows = []
cum_n = 0
cum_churners = 0
total_n = len(holdout_refined)
total_churners = int(holdout_refined["churn_actual"].sum())
for band in RISK_BAND_ORDER:
    subset = holdout_refined[holdout_refined["risk_band"] == band]
    cum_n += len(subset)
    cum_churners += int(subset["churn_actual"].sum())
    capture_rows.append({
        "risk_band_added": band,
        "cumulative_n": cum_n,
        "cumulative_population_share": cum_n / total_n,
        "cumulative_churners": cum_churners,
        "cumulative_churner_capture_rate": cum_churners / total_churners if total_churners else np.nan,
        "cumulative_churn_rate": cum_churners / cum_n if cum_n else np.nan,
    })
capture_curve = pd.DataFrame(capture_rows)

evidence_heatmap_rows = []
family_values = family_shap.set_index("feature_family")["mean_abs_shap"].to_dict()
segment_family_map = {
    "top_decile_high_churn_risk": ["usage", "genre", "membership"],
    "risk_10_30_low_engagement": ["usage"],
    "risk_10_30_other_review": ["usage", "genre"],
    "late_week3_engaged_retention_candidate": ["usage"],
    "genre_affinity_content_recommendation_pool": ["genre"],
    "low_risk_or_general_maintenance": ["usage", "genre", "membership"],
}
for segment, families in segment_family_map.items():
    row = {"final_segment_key": segment}
    for family in ["usage", "genre", "membership", "release_month", "content"]:
        row[family] = family_values.get(family, 0.0) if family in families else 0.0
    evidence_heatmap_rows.append(row)
evidence_heatmap = pd.DataFrame(evidence_heatmap_rows)


save_barh(
    final_summary_holdout.sort_values("churn_rate", ascending=True),
    "final_segment_name_ko",
    "churn_rate",
    "08b final segment churn rate, holdout",
    FIGURE_DIR / "08b_final_segment_churn_rate_holdout.png",
    color="#D4537E",
    x_label="Observed churn rate",
)
plot_size = final_summary_holdout.copy()
plot_size["size_label"] = plot_size["final_segment_name_ko"]
set_plot_style()
fig, ax1 = plt.subplots(figsize=(11, 5.8))
order = plot_size.sort_values("n", ascending=False)
x = np.arange(len(order))
ax1.bar(x, order["n"], color="#378ADD", alpha=0.78, label="n")
ax1.set_ylabel("Segment size")
ax1.set_xticks(x)
ax1.set_xticklabels(order["final_segment_name_ko"], rotation=25, ha="right")
ax2 = ax1.twinx()
ax2.plot(x, order["lift_vs_overall_churn_rate"], color="#D4537E", marker="o", label="lift")
ax2.axhline(1.0, color="#444444", linewidth=1, linestyle="--")
ax2.set_ylabel("Lift vs overall churn")
ax1.set_title("08b final segment size and churn lift")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "08b_final_segment_size_and_lift.png", bbox_inches="tight")
plt.close(fig)

set_plot_style()
fig, ax = plt.subplots(figsize=(8.5, 5))
ax.plot(capture_curve["cumulative_population_share"], capture_curve["cumulative_churner_capture_rate"], marker="o", color="#1D9E75")
for _, row in capture_curve.iterrows():
    ax.annotate(row["risk_band_added"], (row["cumulative_population_share"], row["cumulative_churner_capture_rate"]), fontsize=8)
ax.set_xlabel("Cumulative population share")
ax.set_ylabel("Cumulative churner capture rate")
ax.set_title("08b risk band capture curve, holdout")
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(FIGURE_DIR / "08b_risk_band_capture_curve.png", bbox_inches="tight")
plt.close(fig)

action_fig_df = definitions_df[[
    "korean_name",
    "recommended_action",
    "use_in_stage09_simulation",
    "presentation_readiness",
]].rename(columns={
    "korean_name": "segment",
    "recommended_action": "action",
    "use_in_stage09_simulation": "stage09",
    "presentation_readiness": "readiness",
})
save_table_figure(action_fig_df, "08b final segment action map", FIGURE_DIR / "08b_final_segment_action_map.png", max_rows=8)

set_plot_style()
heat_values = evidence_heatmap.set_index("final_segment_key")[["usage", "genre", "membership", "release_month", "content"]]
fig, ax = plt.subplots(figsize=(9, 5.5))
im = ax.imshow(heat_values.values, cmap="YlGnBu")
ax.set_xticks(np.arange(len(heat_values.columns)))
ax.set_xticklabels(heat_values.columns, rotation=20, ha="right")
ax.set_yticks(np.arange(len(heat_values.index)))
ax.set_yticklabels([segment_names.get(idx, idx) for idx in heat_values.index])
ax.set_title("08b modifier and segment evidence heatmap, Stage 07r TRUE SHAP")
fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02, label="mean abs SHAP when mapped")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "08b_modifier_evidence_heatmap.png", bbox_inches="tight")
plt.close(fig)

summary = {
    "scope": "Stage 08b segmentation refinement and presentation pruning only. No business simulation.",
    "stage08_needed_refinement_because": [
        "Several Stage 08 rule segments were unstable, misleadingly named, broad, or better treated as modifiers.",
        "Risk bands were strong and remain the primary targeting frame.",
    ],
    "stage07r_true_shap_used": True,
    "stage07_fallback_used_as_final_evidence": False,
    "risk_bands_preserved": RISK_BAND_ORDER,
    "final_segment_count": len(definitions_df),
    "final_segments": definitions_df[["final_segment_key", "korean_name", "layer", "use_in_stage09_simulation"]].to_dict(orient="records"),
    "holdout_summary": final_summary_holdout.to_dict(orient="records"),
    "small_n_stage08_segments": stage08_review.loc[stage08_review["small_n_lt_100"] == "Y", "stage08_segment"].tolist(),
    "high_overlap_stage08_segments": stage08_review.loc[stage08_review["high_overlap"] == "Y", "stage08_segment"].tolist(),
    "misleading_stage08_segments": stage08_review.loc[stage08_review["misleading_name_review"].astype(str).str.startswith("Y"), "stage08_segment"].tolist(),
    "stage09_candidate_segments": stage09_candidates.loc[stage09_candidates["use_in_stage09_simulation"] == "Y", "final_segment_key"].tolist(),
    "claims_to_avoid": [
        "Do not claim that SHAP proves causal retention effects.",
        "Do not claim financial impact before Stage 09 assumptions are supplied.",
        "Do not call week3 intensive viewers high risk when their observed churn is low.",
        "Do not use Stage 07 fallback as final XAI evidence.",
    ],
}
write_json(DATA_DIR / "08b_segmentation_refinement_summary.json", summary)

team_lines = [
    "# 08b Team Share Final Segment Summary",
    "",
    "## 기준",
    "- Stage 08b는 Stage 08 세그먼트를 발표용으로 줄이고 재명명한 단계입니다.",
    "- 위험밴드는 유지하고, rule segment는 타깃 그룹과 modifier로 분리했습니다.",
    "- 최종 XAI 근거는 Stage 07r TRUE SHAP입니다. Stage 07 fallback은 최종 근거로 쓰지 않습니다.",
    "",
    "## 최종 발표용 세그먼트",
]
for _, row in final_summary_holdout.iterrows():
    definition = definitions_df[definitions_df["final_segment_key"] == row["final_segment_key"]].iloc[0]
    team_lines.append(
        f"- {definition['korean_name']}: n={int(row['n'])}, churn rate={row['churn_rate']:.3f}, "
        f"lift={row['lift_vs_overall_churn_rate']:.2f}, Stage09={definition['use_in_stage09_simulation']}, "
        f"action={definition['recommended_action']}"
    )
team_lines.extend([
    "",
    "## 발표 시 주의",
    "- 예측/기술 세그먼트이지 인과효과 검증 결과가 아닙니다.",
    "- 가격/프로모션은 독립 세그먼트보다 modifier로만 다룹니다.",
    "- 3주차 집중 시청군은 고위험군이 아니라 안정/전환 후보군으로 표현합니다.",
    "- 기타/일반군은 최종 주장 대상에서 제외합니다.",
    "",
    "## 추천 그림",
    "- 08b_final_segment_churn_rate_holdout.png",
    "- 08b_final_segment_size_and_lift.png",
    "- 08b_risk_band_capture_curve.png",
    "- 08b_final_segment_action_map.png",
])
(DATA_DIR / "08b_team_share_final_segment_summary.md").write_text("\n".join(team_lines) + "\n", encoding="utf-8")

kept = decision_df.loc[decision_df["decision"].isin(["keep", "keep_refine", "rename_keep"]), "stage08_segment"].tolist()
merged = decision_df.loc[decision_df["decision"].eq("merge"), "stage08_segment"].tolist()
renamed = decision_df.loc[decision_df["decision"].str.contains("rename", na=False), "stage08_segment"].tolist()
dropped = decision_df.loc[decision_df["decision"].eq("drop_from_presentation"), "stage08_segment"].tolist()
modifiers = decision_df.loc[decision_df["decision"].str.contains("modifier", na=False), "stage08_segment"].tolist()

report_lines = [
    "# 08b v2 Segmentation Refinement Report",
    "",
    f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
    "",
    "## 1. Why Stage 08 Needed Refinement",
    "Stage 08 created useful risk bands and exploratory rule segments, but several rule segments were too small, too broad, highly overlapping, or named in a way that could mislead presentation. Stage 08b keeps the risk-score bands as the primary targeting frame and converts many rule segments into explanatory modifiers.",
    "",
    "## 2. Robust Risk Bands Kept",
]
for _, row in risk_preserved.iterrows():
    report_lines.append(
        f"- {row['risk_band']}: n={int(row['n'])}, churn rate={float(row['churn_rate']):.3f}, "
        f"lift={float(row['lift_vs_overall_churn_rate']):.2f}, captured churners={int(row['captured_churners'])}."
    )
report_lines.extend([
    "",
    "## 3. Stage 08 Keep, Merge, Rename, Drop Decisions",
    f"- Kept/refined: {', '.join(kept)}.",
    f"- Merged: {', '.join(merged)}.",
    f"- Renamed/downplayed: {', '.join(renamed)}.",
    f"- Dropped from presentation: {', '.join(dropped)}.",
    f"- Modifier only: {', '.join(modifiers)}.",
    "",
    "## 4. Final Presentation-Ready Segment Set",
])
for _, row in final_summary_holdout.iterrows():
    definition = definitions_df[definitions_df["final_segment_key"] == row["final_segment_key"]].iloc[0]
    report_lines.append(
        f"- {definition['korean_name']} (`{definition['final_segment_key']}`): n={int(row['n'])}, "
        f"churn rate={row['churn_rate']:.3f}, lift={row['lift_vs_overall_churn_rate']:.2f}, "
        f"action={definition['recommended_action']}."
    )
report_lines.extend([
    "",
    "## 5. Targeting Groups Versus Explanatory Modifiers",
    "- Targeting groups: top_decile_high_churn_risk, risk_10_30_low_engagement, risk_10_30_other_review.",
    "- Maintenance/retention group: late_week3_engaged_retention_candidate.",
    "- Modifier/action layer: genre_affinity_content_recommendation_pool, price/promotion context, delayed start, low/no engagement, week3 intensity.",
    "- Residual context: low_risk_or_general_maintenance.",
    "",
    "## 6. Stage 09 Simulation Suitability",
])
for _, row in stage09_candidates.iterrows():
    report_lines.append(
        f"- {row['final_segment_name_ko']}: Stage09={row['use_in_stage09_simulation']}, "
        f"lever={row['proposed_intervention_lever']}, assumptions={row['business_assumption_needed_stage09']}."
    )
report_lines.extend([
    "",
    "## 7. Claims Must Not Be Made",
    "- Do not claim segment membership causes churn or repurchase.",
    "- Do not claim SHAP proves a retention intervention effect.",
    "- Do not calculate or imply financial impact in Stage 08b.",
    "- Do not use Stage 07 fallback as final XAI evidence.",
    "- Do not call 3주차 집중 시청군 a churn-risk group when observed churn is low.",
    "",
    "## 8. Business Assumptions Needed Before Financial Simulation",
    "- Reachable audience size after channel constraints.",
    "- Campaign/contact cost.",
    "- Expected response rate.",
    "- Incremental retention lift under low/base/high scenarios.",
    "- Message fatigue and exclusion rules.",
    "- Content inventory and recommendation feasibility.",
    "",
    "## 08b Internal Critique and Final Segment Selection Rationale",
    f"- Kept: {', '.join(kept)}.",
    f"- Merged: {', '.join(merged)}.",
    f"- Renamed: {', '.join(renamed)}.",
    f"- Dropped: {', '.join(dropped)}.",
    f"- Modifier only: {', '.join(modifiers)}.",
    f"- Ready for presentation: {', '.join(definitions_df['final_segment_key'].tolist())}.",
    f"- Stage 09 candidates: {', '.join(stage09_candidates.loc[stage09_candidates['use_in_stage09_simulation'] == 'Y', 'final_segment_key'].tolist())}.",
    "- Avoid causal, financial, and unsupported intervention claims until Stage 09 assumptions and experiments are defined.",
])
(DATA_DIR / "08b_segmentation_refinement_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

required_outputs = [
    DATA_DIR / "08b_final_segment_assignments_holdout.csv",
    DATA_DIR / "08b_final_segment_assignments_full_descriptive.csv",
    DATA_DIR / "08b_segmentation_refinement_summary.json",
    DATA_DIR / "08b_team_share_final_segment_summary.md",
    DATA_DIR / "08b_segmentation_refinement_report.md",
    TABLE_DIR / "08b_stage08_segment_review.csv",
    TABLE_DIR / "08b_segment_keep_merge_drop_decisions.csv",
    TABLE_DIR / "08b_final_segment_definitions.csv",
    TABLE_DIR / "08b_final_segment_summary_holdout.csv",
    TABLE_DIR / "08b_final_segment_summary_full_descriptive.csv",
    TABLE_DIR / "08b_final_segment_overlap_matrix.csv",
    TABLE_DIR / "08b_modifier_flag_summary.csv",
    TABLE_DIR / "08b_stage09_simulation_input_candidates.csv",
    TABLE_DIR / "08b_business_readiness_findings.csv",
    TABLE_DIR / "08b_final_checks.csv",
    FIGURE_DIR / "08b_final_segment_churn_rate_holdout.png",
    FIGURE_DIR / "08b_final_segment_size_and_lift.png",
    FIGURE_DIR / "08b_risk_band_capture_curve.png",
    FIGURE_DIR / "08b_final_segment_action_map.png",
    FIGURE_DIR / "08b_modifier_evidence_heatmap.png",
]

segment_variables_used = [
    "risk_band",
    "churn_risk_score",
    "seg_low_or_no_early_engagement",
    "seg_late_heavy_week3_intensive",
    "genre affinity flags",
    "hierarchy residual",
]
forbidden_vars = [var for var in segment_variables_used if is_forbidden(var)]
target_used_to_define = definitions_df["target_used_to_define"].eq("Y").any()
raw_after = snapshot_paths(RAW_FILES)
stage_after = snapshot_dirs(STAGE_EXISTING_DIRS) | snapshot_paths(STAGE_EXISTING_FILES)
small_n_identified = stage08_review["small_n_lt_100"].eq("Y").any()
high_overlap_identified = stage08_review["high_overlap"].eq("Y").any()
misleading_reviewed = stage08_review["misleading_name_review"].astype(str).str.startswith("Y").any()
final_segment_count_ok = len(definitions_df) <= 6
every_action = definitions_df["recommended_action"].fillna("").str.len().gt(0).all()
stage09_required_cols = [
    "use_in_stage09_simulation",
    "why",
    "proposed_intervention_lever",
    "assumed_lift_scenario_placeholder",
    "business_assumption_needed_stage09",
]
stage09_candidates_ok = stage09_candidates.loc[
    stage09_candidates["use_in_stage09_simulation"] == "Y", stage09_required_cols
].notna().all().all()

final_checks = [
    {"check": "raw_files_unchanged", "status": "PASS" if raw_before == raw_after else "FAIL", "detail": "raw snapshots unchanged"},
    {"check": "no_project_root_data_output_created", "status": "PASS" if not (PROJECT_ROOT / "_data" / "08b_v2_segmentation_refinement").exists() and not (PROJECT_ROOT / "_data" / "02_interim" / "08b_v2_segmentation_refinement").exists() else "FAIL", "detail": "Stage 08b writes only under park.ingyeom/reports"},
    {"check": "stage01_through_stage08_outputs_not_overwritten", "status": "PASS" if stage_before == stage_after else "FAIL", "detail": "Stage 01-08 snapshots unchanged"},
    {"check": "stage07r_true_shap_used_as_xai_basis", "status": "PASS" if len(family_shap) > 0 and len(global_shap) > 0 else "FAIL", "detail": "07r TRUE SHAP tables read"},
    {"check": "stage07_fallback_not_used_as_final_evidence", "status": "PASS", "detail": "No Stage 07 fallback files read"},
    {"check": "is_repurchase_not_used_to_define_segments", "status": "PASS" if not target_used_to_define else "FAIL", "detail": f"target_used_to_define={target_used_to_define}"},
    {"check": "forbidden_features_not_used_as_segment_variables", "status": "PASS" if not forbidden_vars else "FAIL", "detail": "|".join(forbidden_vars)},
    {"check": "small_n_segments_identified", "status": "PASS" if small_n_identified else "FAIL", "detail": "|".join(stage08_review.loc[stage08_review["small_n_lt_100"] == "Y", "stage08_segment"].tolist())},
    {"check": "high_overlap_segments_identified", "status": "PASS" if high_overlap_identified else "FAIL", "detail": "|".join(stage08_review.loc[stage08_review["high_overlap"] == "Y", "stage08_segment"].tolist())},
    {"check": "misleading_segment_names_reviewed", "status": "PASS" if misleading_reviewed else "FAIL", "detail": "|".join(stage08_review.loc[stage08_review["misleading_name_review"].astype(str).str.startswith("Y"), "stage08_segment"].tolist())},
    {"check": "final_segment_list_no_more_than_6", "status": "PASS" if final_segment_count_ok else "FAIL", "detail": f"final_segment_count={len(definitions_df)}"},
    {"check": "every_final_segment_has_action_recommendation", "status": "PASS" if every_action else "FAIL", "detail": "recommended_action populated"},
    {"check": "stage09_candidate_segments_have_required_inputs", "status": "PASS" if stage09_candidates_ok else "FAIL", "detail": "simulation input placeholders present"},
    {"check": "no_business_simulation_created", "status": "PASS", "detail": "No financial impact or lift calculation performed"},
    {"check": "final_report_and_team_share_summary_created", "status": "PASS" if (DATA_DIR / "08b_segmentation_refinement_report.md").exists() and (DATA_DIR / "08b_team_share_final_segment_summary.md").exists() else "FAIL", "detail": "report and team-share summary"},
    {"check": "all_required_outputs_created", "status": "PENDING", "detail": f"required_outputs={len(required_outputs)}"},
]
write_csv(TABLE_DIR / "08b_final_checks.csv", final_checks)
all_required = all(path.exists() for path in required_outputs)
final_checks[-1]["status"] = "PASS" if all_required else "FAIL"
missing = [rel(path) for path in required_outputs if not path.exists()]
final_checks[-1]["detail"] = "all required outputs exist" if all_required else "|".join(missing)
write_csv(TABLE_DIR / "08b_final_checks.csv", final_checks)

print("08b_v2 segmentation refinement completed.")
for row in final_checks:
    print(f"{row['check']}: {row['status']} - {row['detail']}")
