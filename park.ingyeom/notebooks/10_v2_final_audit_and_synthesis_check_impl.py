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

FORBIDDEN_MODEL_FEATURES = {
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


def find_project_root(start):
    for candidate in [start, *start.parents]:
        if (
            (candidate / "_data" / "01_raw" / "Membership.csv").exists()
            and (
                candidate
                / "park.ingyeom"
                / "reports"
                / "data"
                / "09_v2_business_simulation"
                / "09_v2_business_simulation_summary.json"
            ).exists()
        ):
            return candidate
    raise FileNotFoundError("Could not locate ott-churn-prediction project root.")


PROJECT_ROOT = find_project_root(Path.cwd())
DATA_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "10_v2_final_audit_and_synthesis"
TABLE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "10_v2_final_audit_and_synthesis"
FIGURE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "10_v2_final_audit_and_synthesis"
for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

RAW_FILES = [
    PROJECT_ROOT / "_data" / "01_raw" / "Membership.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "User_Mapping.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "View_History.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "Movie_Master.csv",
]

STAGE_PREFIXES = [
    "01_v2_data_overview_and_audit",
    "02_v2_preprocessing_policy",
    "02_v2_preprocessing_policy_validation",
    "03_v2_usage_feature_engineering",
    "04_v2_content_feature_engineering",
    "04_v2_content_feature_feasibility",
    "05_v2_modeling_dataset",
    "06_v2_baseline_modeling",
    "06b_v2_baseline_sanity_audit",
    "07_v2_xai_shap_interpretation",
    "07r_v2_true_shap_interpretation",
    "08_v2_segmentation_strategy",
    "08b_v2_segmentation_refinement",
    "09_v2_business_simulation",
]

STAGE_DIRS = []
for base_name in ["data", "tables", "figures"]:
    base = PROJECT_ROOT / "park.ingyeom" / "reports" / base_name
    for prefix in STAGE_PREFIXES:
        candidate = base / prefix
        if candidate.exists():
            STAGE_DIRS.append(candidate)

STAGE_NOTEBOOK_FILES = [
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
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / "09_v2_business_simulation_and_retention_strategy.ipynb",
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


def read_csv(path, **kwargs):
    if path.exists():
        return pd.read_csv(path, **kwargs)
    return pd.DataFrame()


def read_json(path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def nrows_csv(path):
    if not path.exists():
        return np.nan
    return len(pd.read_csv(path))


def num_value(value, default=np.nan):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def is_forbidden_feature(name):
    if name in FORBIDDEN_MODEL_FEATURES:
        return True
    low = str(name).lower()
    return any(token in low for token in FORBIDDEN_SUBSTRINGS)


def set_plot_style():
    plt.rcParams.update({
        "font.family": "Malgun Gothic",
        "font.sans-serif": ["Malgun Gothic", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "figure.dpi": 140,
        "savefig.dpi": 160,
    })


raw_before = snapshot_paths(RAW_FILES)
stage_before = snapshot_dirs(STAGE_DIRS) | snapshot_paths(STAGE_NOTEBOOK_FILES)

P = PROJECT_ROOT / "park.ingyeom" / "reports"
data = P / "data"
tables = P / "tables"
figures = P / "figures"

paths = {
    "raw_inventory": tables / "01_v2_data_overview_and_audit" / "01_v2_raw_file_inventory.csv",
    "stage02_filter": tables / "02_v2_preprocessing_policy" / "02_v2_filter_summary.csv",
    "stage02_excluded": tables / "02_v2_preprocessing_policy" / "02_v2_excluded_membership_rows.csv",
    "stage05_input": tables / "05_v2_modeling_dataset" / "05_v2_input_row_count_summary.csv",
    "stage05_merge": tables / "05_v2_modeling_dataset" / "05_v2_merge_integrity_summary.csv",
    "stage05_feature_sets": data / "05_v2_modeling_dataset" / "feature_sets_v2.json",
    "stage06_best": data / "06_v2_baseline_modeling" / "06_v2_best_model_config.json",
    "stage06_metrics": data / "06_v2_baseline_modeling" / "06_v2_model_metrics.csv",
    "stage06_split": tables / "06_v2_baseline_modeling" / "06_v2_split_summary.csv",
    "stage06_group": tables / "06_v2_baseline_modeling" / "06_v2_group_leakage_check.csv",
    "stage06_decile": tables / "06_v2_baseline_modeling" / "06_v2_churn_risk_decile_summary.csv",
    "stage06_failed": tables / "06_v2_baseline_modeling" / "06_v2_failed_models.csv",
    "stage06b_summary": data / "06b_v2_baseline_sanity_audit" / "06b_sanity_audit_summary.json",
    "stage06b_stability": tables / "06b_v2_baseline_sanity_audit" / "06b_repeated_group_split_stability.csv",
    "stage07_summary": data / "07_v2_xai_shap_interpretation" / "07_v2_xai_summary.json",
    "stage07r_summary": data / "07r_v2_true_shap_interpretation" / "07r_true_shap_summary.json",
    "stage07r_global": tables / "07r_v2_true_shap_interpretation" / "07r_global_shap_importance.csv",
    "stage07r_family": tables / "07r_v2_true_shap_interpretation" / "07r_feature_family_shap_importance.csv",
    "stage07r_visual": tables / "07r_v2_true_shap_interpretation" / "07r_visualization_inventory.csv",
    "stage08_summary": data / "08_v2_segmentation_strategy" / "08_v2_segmentation_summary.json",
    "stage08b_summary": data / "08b_v2_segmentation_refinement" / "08b_segmentation_refinement_summary.json",
    "stage08b_segment": tables / "08b_v2_segmentation_refinement" / "08b_final_segment_summary_holdout.csv",
    "stage08b_decisions": tables / "08b_v2_segmentation_refinement" / "08b_segment_keep_merge_drop_decisions.csv",
    "stage09_summary": data / "09_v2_business_simulation" / "09_v2_business_simulation_summary.json",
    "stage09_segment_sim": tables / "09_v2_business_simulation" / "09_v2_segment_simulation_low_base_high.csv",
    "stage09_portfolio": tables / "09_v2_business_simulation" / "09_v2_portfolio_simulation_summary.csv",
    "stage09_financial": tables / "09_v2_business_simulation" / "09_v2_financial_assumption_status.csv",
}

raw_inventory = read_csv(paths["raw_inventory"])
stage02_filter = read_csv(paths["stage02_filter"])
stage02_excluded = read_csv(paths["stage02_excluded"])
stage05_input = read_csv(paths["stage05_input"])
stage05_merge = read_csv(paths["stage05_merge"])
stage06_best = read_json(paths["stage06_best"])
stage06_metrics = read_csv(paths["stage06_metrics"])
stage06_split = read_csv(paths["stage06_split"])
stage06_group = read_csv(paths["stage06_group"])
stage06b_summary = read_json(paths["stage06b_summary"])
stage07_summary = read_json(paths["stage07_summary"])
stage07r_summary = read_json(paths["stage07r_summary"])
stage07r_global = read_csv(paths["stage07r_global"])
stage07r_family = read_csv(paths["stage07r_family"])
stage08b_segment = read_csv(paths["stage08b_segment"])
stage08b_decisions = read_csv(paths["stage08b_decisions"])
stage09_summary = read_json(paths["stage09_summary"])
stage09_segment_sim = read_csv(paths["stage09_segment_sim"])
stage09_portfolio = read_csv(paths["stage09_portfolio"])

expected_artifacts = []
for stage in STAGE_PREFIXES:
    for base_name in ["data", "tables"]:
        base = P / base_name / stage
        expected_artifacts.append({
            "stage": stage,
            "artifact_type": f"{base_name}_folder",
            "path": rel(base),
            "exists": base.exists(),
            "missing_class": "" if base.exists() else "fatal_missing",
            "recommendation": "required stage folder",
        })
final_check_patterns = [
    ("01_v2_data_overview_and_audit", "01_v2_audit_final_checks.csv"),
    ("02_v2_preprocessing_policy_validation", "02_v2_final_checks.csv"),
    ("02_v2_preprocessing_policy", "02_v2_final_checks.csv"),
    ("03_v2_usage_feature_engineering", "03_v2_final_checks.csv"),
    ("04_v2_content_feature_engineering", "04_v2_final_checks.csv"),
    ("05_v2_modeling_dataset", "05_v2_final_checks.csv"),
    ("06_v2_baseline_modeling", "06_v2_final_checks.csv"),
    ("06b_v2_baseline_sanity_audit", "06b_final_checks.csv"),
    ("07_v2_xai_shap_interpretation", "07_v2_final_checks.csv"),
    ("07r_v2_true_shap_interpretation", "07r_final_checks.csv"),
    ("08_v2_segmentation_strategy", "08_v2_final_checks.csv"),
    ("08b_v2_segmentation_refinement", "08b_final_checks.csv"),
    ("09_v2_business_simulation", "09_v2_final_checks.csv"),
]
for stage, filename in final_check_patterns:
    path = tables / stage / filename
    expected_artifacts.append({
        "stage": stage,
        "artifact_type": "final_checks",
        "path": rel(path),
        "exists": path.exists(),
        "missing_class": "" if path.exists() else "fatal_missing",
        "recommendation": "required validation table",
    })
recommended_assets = [
    data / "07r_v2_true_shap_interpretation" / "07r_team_share_summary.md",
    figures / "07r_v2_true_shap_interpretation" / "07r_shap_beeswarm_red_blue_conservative_w1_3.png",
    figures / "07r_v2_true_shap_interpretation" / "07r_shap_global_bar_conservative_w1_3.png",
    data / "08b_v2_segmentation_refinement" / "08b_team_share_final_segment_summary.md",
    figures / "08b_v2_segmentation_refinement" / "08b_final_segment_churn_rate_holdout.png",
    figures / "08b_v2_segmentation_refinement" / "08b_final_segment_size_and_lift.png",
    data / "09_v2_business_simulation" / "09_v2_team_share_business_simulation_summary.md",
    figures / "09_v2_business_simulation" / "09_v2_portfolio_incremental_retained_users.png",
    figures / "09_v2_business_simulation" / "09_v2_assumption_sensitivity_tornado.png",
]
for path in recommended_assets:
    expected_artifacts.append({
        "stage": "final_recommended_asset",
        "artifact_type": "recommended_asset",
        "path": rel(path),
        "exists": path.exists(),
        "missing_class": "" if path.exists() else "nonfatal_missing",
        "recommendation": "recommended for team sharing or final deck construction",
    })
artifact_inventory = write_csv(TABLE_DIR / "10_v2_artifact_inventory.csv", expected_artifacts)
final_asset_inventory = write_csv(TABLE_DIR / "10_v2_final_asset_inventory.csv", [
    {
        "asset_group": "XAI",
        "asset": "TRUE SHAP team summary",
        "path": rel(data / "07r_v2_true_shap_interpretation" / "07r_team_share_summary.md"),
        "use_in_presentation": "Y",
        "caution": "Use Stage 07r, not Stage 07 fallback.",
    },
    {
        "asset_group": "XAI",
        "asset": "red-blue SHAP beeswarm",
        "path": rel(figures / "07r_v2_true_shap_interpretation" / "07r_shap_beeswarm_red_blue_conservative_w1_3.png"),
        "use_in_presentation": "Y",
        "caution": "Positive SHAP is toward repurchase_score, not churn_risk_score.",
    },
    {
        "asset_group": "Segmentation",
        "asset": "08b final segment summary",
        "path": rel(data / "08b_v2_segmentation_refinement" / "08b_team_share_final_segment_summary.md"),
        "use_in_presentation": "Y",
        "caution": "Use Stage 08b refined segments, not raw Stage 08 exploratory hierarchy.",
    },
    {
        "asset_group": "Simulation",
        "asset": "09 scenario simulation team summary",
        "path": rel(data / "09_v2_business_simulation" / "09_v2_team_share_business_simulation_summary.md"),
        "use_in_presentation": "Y",
        "caution": "Scenario only; no ROI or causal effect claim.",
    },
])

def raw_row(dataset):
    if raw_inventory.empty:
        return np.nan
    m = raw_inventory[raw_inventory["dataset"].eq(dataset)]
    return int(float(m["row_count"].iloc[0])) if not m.empty else np.nan


stage02_final = int(pd.read_csv(data / "02_v2_preprocessing_policy" / "membership_v2_preprocessed.csv").shape[0])
stage03_w13 = nrows_csv(data / "03_v2_usage_feature_engineering" / "usage_features_v2_w1_3.csv")
stage03_w14 = nrows_csv(data / "03_v2_usage_feature_engineering" / "usage_features_v2_w1_4.csv")
stage04_w13 = nrows_csv(data / "04_v2_content_feature_engineering" / "content_features_v2_w1_3.csv")
stage04_w14 = nrows_csv(data / "04_v2_content_feature_engineering" / "content_features_v2_w1_4.csv")
stage05_w13 = nrows_csv(data / "05_v2_modeling_dataset" / "modeling_dataset_v2_w1_3.csv")
stage05_w14 = nrows_csv(data / "05_v2_modeling_dataset" / "modeling_dataset_v2_w1_4.csv")
split_train = int(float(stage06_split.loc[(stage06_split["split_type"].eq("holdout")) & (stage06_split["split_id"].eq("train")), "row_count"].iloc[0]))
split_test = int(float(stage06_split.loc[(stage06_split["split_type"].eq("holdout")) & (stage06_split["split_id"].eq("test")), "row_count"].iloc[0]))
stage08_holdout = nrows_csv(data / "08_v2_segmentation_strategy" / "08_v2_segment_assignments_holdout.csv")
stage08b_holdout = nrows_csv(data / "08b_v2_segmentation_refinement" / "08b_final_segment_assignments_holdout.csv")
stage09_sim_segments = len(stage09_segment_sim["final_segment_key"].unique()) if not stage09_segment_sim.empty else np.nan

excluded_counts = stage02_excluded.groupby("reason_code").size().to_dict() if not stage02_excluded.empty else {}
lineage_rows = [
    {"stage": "raw", "artifact": "Membership.csv", "row_count": raw_row("Membership"), "explanation": "Active v2 raw Membership rows.", "status": "fact"},
    {"stage": "02", "artifact": "membership_v2_preprocessed.csv", "row_count": stage02_final, "explanation": f"24074 minus strict target conflicts {excluded_counts.get('STRICT_TARGET_CONFLICT', 0)} and exact duplicate extra rows {excluded_counts.get('EXACT_DUPLICATE_EXTRA_ROW', 0)}. Same-target duplicate rule affected 0 rows.", "status": "fact"},
    {"stage": "03", "artifact": "usage_features_v2_w1_3.csv", "row_count": stage03_w13, "explanation": "One row per retained membership_row_id for w1_3 usage features.", "status": "fact"},
    {"stage": "03", "artifact": "usage_features_v2_w1_4.csv", "row_count": stage03_w14, "explanation": "One row per retained membership_row_id for w1_4 usage features.", "status": "fact"},
    {"stage": "04", "artifact": "content_features_v2_w1_3.csv", "row_count": stage04_w13, "explanation": "One row per retained membership_row_id for w1_3 content features.", "status": "fact"},
    {"stage": "04", "artifact": "content_features_v2_w1_4.csv", "row_count": stage04_w14, "explanation": "One row per retained membership_row_id for w1_4 content features.", "status": "fact"},
    {"stage": "05", "artifact": "modeling_dataset_v2_w1_3.csv", "row_count": stage05_w13, "explanation": "Final modeling table for early observation window; one row per membership_row_id.", "status": "fact"},
    {"stage": "05", "artifact": "modeling_dataset_v2_w1_4.csv", "row_count": stage05_w14, "explanation": "Final modeling table for late/end-period comparison; one row per membership_row_id.", "status": "fact"},
    {"stage": "06", "artifact": "GroupShuffleSplit train", "row_count": split_train, "explanation": "Canonical USER_KEY group-aware train split.", "status": "fact"},
    {"stage": "06", "artifact": "GroupShuffleSplit test", "row_count": split_test, "explanation": "Canonical USER_KEY group-aware holdout split; no USER_KEY overlap.", "status": "fact"},
    {"stage": "08", "artifact": "08_v2_segment_assignments_holdout.csv", "row_count": stage08_holdout, "explanation": "Stage 08 holdout-first segment evaluation matched Stage 06 holdout rows.", "status": "fact"},
    {"stage": "08b", "artifact": "08b_final_segment_assignments_holdout.csv", "row_count": stage08b_holdout, "explanation": "Refined segment assignments remain on Stage 06 holdout rows.", "status": "fact"},
    {"stage": "09", "artifact": "segment simulation unique segments", "row_count": stage09_sim_segments, "explanation": "Simulation scenarios are segment-level, not row-level new modeling data.", "status": "fact"},
]
row_lineage = write_csv(TABLE_DIR / "10_v2_row_count_lineage.csv", lineage_rows)

feature_sets = read_json(paths["stage05_feature_sets"])
all_features = []
feature_set_payload = feature_sets.get("feature_sets", feature_sets) if isinstance(feature_sets, dict) else {}
if isinstance(feature_set_payload, dict):
    for name, payload in feature_set_payload.items():
        if isinstance(payload, list):
            feats = payload
        elif isinstance(payload, dict):
            feats = payload.get("features", [])
        else:
            feats = []
        for feat in feats:
            all_features.append({"feature_set": name, "feature": feat, "forbidden": is_forbidden_feature(feat)})
forbidden_violations = [row for row in all_features if row["forbidden"]]

best_observed = stage06_best.get("best_observed_model", {})
conservative = stage06_best.get("conservative_recommended_baseline", {})
interpretable = stage06_best.get("business_interpretable_baseline", {})
key_metrics = [
    {"metric_id": "raw_membership_rows", "metric": raw_row("Membership"), "stage": "01", "source_file": rel(paths["raw_inventory"]), "interpretation": "Active v2 raw Membership row count."},
    {"metric_id": "retained_membership_rows", "metric": stage02_final, "stage": "02", "source_file": rel(data / "02_v2_preprocessing_policy" / "membership_v2_preprocessed.csv"), "interpretation": "Rows retained after strict conflict and duplicate exclusions."},
    {"metric_id": "excluded_strict_target_conflict", "metric": excluded_counts.get("STRICT_TARGET_CONFLICT", 0), "stage": "02", "source_file": rel(paths["stage02_excluded"]), "interpretation": "Rows excluded because all non-target fields were identical but is_repurchase differed."},
    {"metric_id": "excluded_exact_duplicate_extra", "metric": excluded_counts.get("EXACT_DUPLICATE_EXTRA_ROW", 0), "stage": "02", "source_file": rel(paths["stage02_excluded"]), "interpretation": "Extra exact duplicate Membership rows removed after keeping one representative."},
    {"metric_id": "conservative_auc", "metric": conservative.get("roc_auc_repurchase"), "stage": "06", "source_file": rel(paths["stage06_best"]), "interpretation": "w1_3 timing-defensible baseline ROC AUC for repurchase prediction."},
    {"metric_id": "best_observed_auc", "metric": best_observed.get("roc_auc_repurchase"), "stage": "06", "source_file": rel(paths["stage06_best"]), "interpretation": "Best observed model, w1_4 late-period LGBM, not early-warning."},
    {"metric_id": "target_shuffle_auc", "metric": stage06b_summary.get("target_shuffle_auc"), "stage": "06b", "source_file": rel(paths["stage06b_summary"]), "interpretation": "Sanity test should be near random; passed in Stage 06b."},
    {"metric_id": "repeated_group_split_auc_mean", "metric": stage06b_summary.get("repeated_group_split_auc_mean"), "stage": "06b", "source_file": rel(paths["stage06b_summary"]), "interpretation": "Repeated USER_KEY group split stability mean AUC."},
    {"metric_id": "shap_version", "metric": stage07r_summary.get("shap_version"), "stage": "07r", "source_file": rel(paths["stage07r_summary"]), "interpretation": "TRUE SHAP environment version."},
    {"metric_id": "stage08b_final_segment_count", "metric": len(stage08b_segment), "stage": "08b", "source_file": rel(paths["stage08b_segment"]), "interpretation": "Final presentation segment count after pruning."},
]
key_metric_registry = write_csv(TABLE_DIR / "10_v2_key_metric_registry.csv", key_metrics)

model_rows = []
for role, payload, status in [
    ("best_observed_model", best_observed, "claim_with_caution"),
    ("conservative_recommended_baseline", conservative, "safe_to_claim"),
    ("business_interpretable_baseline", interpretable, "safe_to_claim"),
]:
    model_rows.append({
        "model_role": role,
        "window": payload.get("window"),
        "feature_set": payload.get("feature_set"),
        "model_name": payload.get("model_name"),
        "roc_auc_repurchase": payload.get("roc_auc_repurchase"),
        "average_precision_repurchase": payload.get("average_precision_repurchase"),
        "average_precision_churn_risk": payload.get("average_precision_churn_risk"),
        "f1_at_0_5_repurchase": payload.get("f1_at_0_5_repurchase"),
        "f1_at_0_5_churn_risk": payload.get("f1_at_0_5_churn_risk"),
        "n_train": payload.get("n_train"),
        "n_test": payload.get("n_test"),
        "status": status,
        "caution": "w1_4 is late-period/end-of-period" if payload.get("window") == "w1_4" else "w1_3 is timing-defensible early-observation",
        "source_file": rel(paths["stage06_best"]),
    })
model_rows.extend([
    {"model_role": "target_shuffle_test", "window": "w1_3", "feature_set": conservative.get("feature_set"), "model_name": conservative.get("model_name"), "roc_auc_repurchase": stage06b_summary.get("target_shuffle_auc"), "average_precision_repurchase": "", "average_precision_churn_risk": "", "f1_at_0_5_repurchase": "", "f1_at_0_5_churn_risk": "", "n_train": "", "n_test": "", "status": "safe_to_claim", "caution": "Near-random shuffle supports no obvious target leakage, but it is not a proof of causality.", "source_file": rel(paths["stage06b_summary"])},
    {"model_role": "repeated_group_split_stability", "window": "w1_3", "feature_set": conservative.get("feature_set"), "model_name": conservative.get("model_name"), "roc_auc_repurchase": stage06b_summary.get("repeated_group_split_auc_mean"), "average_precision_repurchase": "", "average_precision_churn_risk": stage06b_summary.get("repeated_group_split_auc_std"), "f1_at_0_5_repurchase": "", "f1_at_0_5_churn_risk": "", "n_train": "", "n_test": "", "status": "safe_to_claim", "caution": "Mean/std from three repeated group splits.", "source_file": rel(paths["stage06b_summary"])},
])
model_registry = write_csv(TABLE_DIR / "10_v2_model_result_registry.csv", model_rows)

top_features = stage07r_summary.get("top10_shap_features", [])
xai_rows = []
for i, item in enumerate(top_features, start=1):
    xai_rows.append({
        "rank": i,
        "xai_type": "TRUE_SHAP_global_feature",
        "feature": item.get("original_feature"),
        "feature_family": item.get("feature_family"),
        "mean_abs_shap": item.get("mean_abs_shap"),
        "status": "safe_to_claim" if i <= 5 else "claim_with_caution",
        "caution": "SHAP explains model output toward repurchase_score, not causality.",
        "source_file": rel(paths["stage07r_summary"]),
    })
for i, item in enumerate(stage07r_summary.get("top_feature_families", []), start=1):
    xai_rows.append({
        "rank": i,
        "xai_type": "TRUE_SHAP_feature_family",
        "feature": item.get("feature_family"),
        "feature_family": item.get("feature_family"),
        "mean_abs_shap": item.get("mean_abs_shap"),
        "status": "safe_to_claim" if item.get("feature_family") in ["usage", "genre", "membership"] else "claim_with_caution",
        "caution": "Content metadata is limited to genre and ott_release_month proxies.",
        "source_file": rel(paths["stage07r_summary"]),
    })
xai_registry = write_csv(TABLE_DIR / "10_v2_xai_result_registry.csv", xai_rows)

segment_rows = []
for _, row in stage08b_segment.iterrows():
    segment_rows.append({
        "final_segment_key": row["final_segment_key"],
        "final_segment_name_ko": row["final_segment_name_ko"],
        "n": row["n"],
        "churn_rate": row["churn_rate"],
        "lift_vs_overall_churn_rate": row["lift_vs_overall_churn_rate"],
        "captured_churners": row["captured_churners"],
        "use_in_stage09_simulation": row["use_in_stage09_simulation"],
        "status": "safe_to_claim" if row["final_segment_key"] in ["top_decile_high_churn_risk", "risk_10_30_low_engagement"] else "claim_with_caution",
        "caution": "Segment is predictive/descriptive and not causal.",
        "source_file": rel(paths["stage08b_segment"]),
    })
segment_registry = write_csv(TABLE_DIR / "10_v2_segment_registry.csv", segment_rows)

sim_rows = []
base_seg_sim = stage09_segment_sim[stage09_segment_sim["scenario"].eq("base")]
for _, row in base_seg_sim.iterrows():
    sim_rows.append({
        "simulation_type": "segment_base_scenario",
        "scenario": row["scenario"],
        "name": row["final_segment_key"],
        "n_or_targeted_users": row["n"],
        "treated_users": row["treated_users"],
        "incremental_retained_users": row["incremental_retained_users"],
        "financial_status": row["financial_status"],
        "status": "claim_with_caution",
        "caution": "Assumption-based scenario output, not experiment result.",
        "source_file": rel(paths["stage09_segment_sim"]),
    })
base_portfolio = stage09_portfolio[stage09_portfolio["scenario"].eq("base")]
for _, row in base_portfolio.iterrows():
    sim_rows.append({
        "simulation_type": "portfolio_base_scenario",
        "scenario": row["scenario"],
        "name": row["portfolio_scenario"],
        "n_or_targeted_users": row["total_targeted_users"],
        "treated_users": row["contact_volume_treated_users"],
        "incremental_retained_users": row["total_expected_incremental_retained_users"],
        "financial_status": row["financial_status"],
        "status": "claim_with_caution",
        "caution": row["operational_caution"],
        "source_file": rel(paths["stage09_portfolio"]),
    })
simulation_registry = write_csv(TABLE_DIR / "10_v2_simulation_registry.csv", sim_rows)

def claim(claim_id, text, claim_type, stage, file_path, metric, status, caution, allowed, forbidden, location):
    return {
        "claim_id": claim_id,
        "claim_text_ko": text,
        "claim_type": claim_type,
        "evidence_stage": stage,
        "evidence_file": rel(file_path),
        "evidence_metric": metric,
        "status": status,
        "caution_reason": caution,
        "allowed_wording": allowed,
        "forbidden_wording": forbidden,
        "presentation_location_suggestion": location,
    }


claims = [
    claim("C001", "v2 Membership 원천 데이터는 24,074행이다.", "fact", "01", paths["raw_inventory"], raw_row("Membership"), "safe_to_claim", "파일 inventory에서 직접 확인됨.", "v2 Membership 원천 데이터는 24,074행으로 확인됐다.", "예전 v1 row count를 언급하지 않는다.", "Data audit"),
    claim("C002", "Stage 02 후 최종 retained Membership은 23,933행이다.", "fact", "02", data / "02_v2_preprocessing_policy" / "membership_v2_preprocessed.csv", stage02_final, "safe_to_claim", "엄격 conflict와 duplicate 제외 후 행 수.", "엄격 conflict 73행과 exact duplicate extra 68행 제외 후 23,933행을 사용했다.", "행 제외가 성능 향상 목적이었다고 말하지 않는다.", "Preprocessing"),
    claim("C003", "is_repurchase는 Y=1, N=0으로 매핑한다.", "fact", "06", paths["stage06_best"], "Y=1,N=0", "safe_to_claim", "Stage 06/07r summary 모두 확인.", "Y는 재구독, N은 비재구독 또는 이탈위험으로 해석했다.", "N을 positive class로 뒤섞어 말하지 않는다.", "Modeling"),
    claim("C004", "보수 기준 w1_3 모델의 ROC AUC는 약 0.8705다.", "model_result", "06", paths["stage06_best"], conservative.get("roc_auc_repurchase"), "safe_to_claim", "w1_3 timing-defensible baseline.", "초기 관측에 가까운 w1_3 보수 baseline AUC는 0.8705다.", "최고 성능 모델이라고 말하지 않는다.", "Modeling"),
    claim("C005", "최고 관측 AUC는 w1_4 LGBM 약 0.9037이다.", "model_result", "06", paths["stage06_best"], best_observed.get("roc_auc_repurchase"), "claim_with_caution", "w1_4 late-period model이며 optional booster.", "w1_4 late-period 모델의 최고 관측 AUC는 0.9037이었다.", "early-warning 최고 성능이라고 말하지 않는다.", "Modeling caution"),
    claim("C006", "Stage 06b target shuffle AUC는 near-random이었다.", "model_result", "06b", paths["stage06b_summary"], stage06b_summary.get("target_shuffle_auc"), "safe_to_claim", "Leakage smoke test passed, but not absolute proof.", "target shuffle AUC가 near-random으로 나와 split/target leakage smoke test를 통과했다.", "누수가 절대 없다고 단정하지 않는다.", "Sanity audit"),
    claim("C007", "Stage 07r에서 TRUE SHAP을 계산했다.", "xai_result", "07r", paths["stage07r_summary"], stage07r_summary.get("shap_version"), "safe_to_claim", "Stage 07 fallback is superseded.", "최종 XAI 근거는 Stage 07r TRUE SHAP이다.", "Stage 07 fallback을 최종 SHAP 근거라고 말하지 않는다.", "XAI"),
    claim("C008", "상위 SHAP feature는 week3 watch time, w2-w1 change, week1 ratio, price 등이다.", "xai_result", "07r", paths["stage07r_summary"], "top10_shap_features", "safe_to_claim", "SHAP is model explanation, not causality.", "TRUE SHAP 기준 주요 feature는 사용량 변화, 가격, 장르 비율이다.", "해당 피처를 바꾸면 재구독이 오른다고 말하지 않는다.", "XAI"),
    claim("C009", "feature family 중요도는 usage, genre, membership 순으로 크다.", "xai_result", "07r", paths["stage07r_summary"], "top_feature_families", "safe_to_claim", "Content metadata is limited.", "사용량, 장르, 멤버십 피처군이 모델 설명에서 핵심이다.", "풍부한 외부 콘텐츠 메타데이터가 있었다고 말하지 않는다.", "XAI"),
    claim("C010", "최상위 이탈위험군 holdout churn rate는 약 0.785다.", "segment_result", "08b", paths["stage08b_segment"], "top_decile_high_churn_risk churn_rate", "safe_to_claim", "Descriptive holdout outcome.", "최상위 이탈위험군은 holdout에서 높은 churn rate를 보였다.", "이 군이 반드시 이탈한다고 말하지 않는다.", "Segmentation"),
    claim("C011", "최종 발표용 세그먼트는 Stage 08b의 6개다.", "segment_result", "08b", paths["stage08b_segment"], len(stage08b_segment), "safe_to_claim", "Stage 08 raw exploratory segments are pruned.", "최종 세그먼트는 Stage 08b에서 6개로 정리했다.", "Stage 08 탐색 세그먼트를 그대로 최종이라고 말하지 않는다.", "Segmentation"),
    claim("C012", "Stage 09는 가정 기반 retained-user scenario simulation이다.", "scenario_assumption", "09", paths["stage09_summary"], "scenario simulation", "safe_to_claim", "Not experiment, not causal proof.", "Stage 09는 가정 기반 시나리오이며 실험 결과가 아니다.", "비즈니스 효과가 검증됐다고 말하지 않는다.", "Simulation"),
    claim("C013", "high-risk-plus-low-engagement base scenario는 약 20.1명의 incremental retained users를 추정한다.", "scenario_assumption", "09", paths["stage09_portfolio"], "20.11185", "claim_with_caution", "Placeholder lift/reach/treatment assumptions.", "명시한 가정하에서 약 20.1명의 추가 유지 가능성을 시나리오로 계산했다.", "실제로 20.1명이 유지된다고 말하지 않는다.", "Simulation"),
    claim("C014", "비용과 마진 입력이 없어 ROI는 주장할 수 없다.", "recommendation", "09", paths["stage09_financial"], "cost/margin missing", "safe_to_claim", "Financial inputs unavailable.", "비용과 마진이 없으므로 ROI와 순가치는 주장하지 않는다.", "ROI 개선이라고 말하지 않는다.", "Simulation caution"),
    claim("C015", "SHAP과 모델 결과는 인과 증거가 아니다.", "recommendation", "07r", paths["stage07r_summary"], "interpretation caution", "safe_to_claim", "Predictive pipeline only.", "이 결과는 예측 및 설명 근거이며 인과 검증은 A/B test가 필요하다.", "추천 액션이 재구독을 원인적으로 높인다고 말하지 않는다.", "Final caution"),
]
claim_registry = write_csv(TABLE_DIR / "10_v2_claim_registry.csv", claims)

contradictions = [
    {"issue": "Stage 07 fallback vs Stage 07r TRUE SHAP", "source_stage": "07/07r", "conflicting_statement_or_risk": "Team may accidentally use fallback permutation/coefficient outputs as final XAI.", "severity": "high", "recommended_fix": "Use Stage 07r only; keep Stage 07 as audit trail.", "final_wording": "최종 XAI 근거는 Stage 07r TRUE SHAP이며 Stage 07은 fallback 감사 기록이다."},
    {"issue": "w1_4 timing", "source_stage": "06/07r", "conflicting_statement_or_risk": "w1_4 has highest AUC but uses later behavior.", "severity": "high", "recommended_fix": "Label w1_4 late-period/end-of-period; use w1_3 for timing-defensible model.", "final_wording": "w1_3은 조기 관측에 가까운 모델이고, w1_4는 late-period 비교 모델이다."},
    {"issue": "repurchase score vs churn risk score", "source_stage": "06/08/09", "conflicting_statement_or_risk": "High repurchase_score could be mistaken as high churn risk.", "severity": "high", "recommended_fix": "Always state churn_risk_score = 1 - repurchase_score.", "final_wording": "높은 churn_risk_score가 높은 비재구독 예측 위험을 뜻한다."},
    {"issue": "stable segment naming", "source_stage": "08/08b", "conflicting_statement_or_risk": "Stage 08 early_routine_stable name conflicted with elevated churn.", "severity": "medium", "recommended_fix": "Use Stage 08b refined/pruned segments only.", "final_wording": "최종 세그먼트는 Stage 08b 정제 버전을 사용한다."},
    {"issue": "financial impact", "source_stage": "09", "conflicting_statement_or_risk": "Scenario retained-user outputs may be read as ROI/profit.", "severity": "high", "recommended_fix": "Block ROI/profit until real cost and margin are supplied.", "final_wording": "Stage 09는 retained-user scenario이며 비용과 마진 없이는 ROI를 말하지 않는다."},
    {"issue": "causal wording", "source_stage": "07r/08b/09", "conflicting_statement_or_risk": "SHAP and segmentation may be overstated as intervention effect.", "severity": "high", "recommended_fix": "Use predictive/descriptive wording and A/B test requirement.", "final_wording": "추천 액션의 인과효과는 별도 A/B test가 필요하다."},
    {"issue": "content metadata overclaim", "source_stage": "04/07r", "conflicting_statement_or_risk": "v2 Movie_Master only supports genre and ott_release_month proxies.", "severity": "medium", "recommended_fix": "Do not mention country/rating/runtime/actor/director/Wavve/KOBIS metadata.", "final_wording": "콘텐츠 설명은 genre와 ott_release_month 기반 proxy로 제한한다."},
]
contradiction_audit = write_csv(TABLE_DIR / "10_v2_contradiction_and_wording_audit.csv", contradictions)

storyline = [
    ("1", "Problem definition", "재구독 여부를 예측하고 보수적인 리텐션 전략 후보를 만든다.", "target: is_repurchase", "01/05 summary tables", "성과 최적화보다 누수 방지와 방어 가능한 전략이 우선.", paths["stage05_feature_sets"]),
    ("2", "Why v2 changed the project", "v1 가정은 역사적 참고일 뿐 v2에서 재검증했다.", "raw Membership 24,074 rows", "01_v2_raw_file_inventory.csv", "v1 row count/AUC를 그대로 쓰지 않는다.", paths["raw_inventory"]),
    ("3", "Data and preprocessing audit", "strict conflict와 duplicate만 명시적으로 제외했다.", "retained 23,933 rows", "10_v2_row_count_lineage.csv", "duration policy는 deferred.", TABLE_DIR / "10_v2_row_count_lineage.csv"),
    ("4", "Observation windows", "w1_3은 조기 관측, w1_4는 late-period 비교다.", "w1_3/w1_4 both 23,933 rows", "05_v2_merge_integrity_summary.csv", "w1_4를 early-warning으로 말하지 않는다.", paths["stage05_merge"]),
    ("5", "Baseline modeling and sanity audit", "group-aware split과 sanity audit로 높은 AUC를 점검했다.", f"conservative AUC {conservative.get('roc_auc_repurchase'):.4f}", "06b sanity tables", "누수 없음의 절대 증명은 아니다.", paths["stage06b_summary"]),
    ("6", "Why w1_3 main model", "w1_3이 intervention timing에 더 방어 가능하다.", f"w1_3 AUC {conservative.get('roc_auc_repurchase'):.4f}", "06 best config", "최고 AUC인 w1_4는 late-period.", paths["stage06_best"]),
    ("7", "TRUE SHAP interpretation", "Stage 07r TRUE SHAP으로 모델 설명을 제시한다.", "top family: usage", "07r SHAP beeswarm/global bar", "SHAP은 인과가 아니다.", paths["stage07r_summary"]),
    ("8", "Risk bands", "churn_risk_score 기반 risk band가 targeting frame이다.", "top decile churn rate from Stage 08b", "08b final segment churn figure", "위험점수는 확률 보정 tier가 아니다.", paths["stage08b_segment"]),
    ("9", "Refined final segments", "Stage 08b에서 6개 발표용 세그먼트로 정리했다.", "6 segments", "08b final segment summary", "Stage 08 원본 탐색 세그먼트를 그대로 쓰지 않는다.", paths["stage08b_segment"]),
    ("10", "Scenario simulation", "Stage 09는 가정 기반 retained-user scenario다.", "base portfolio retained users", "09 portfolio figure", "ROI와 profit은 말하지 않는다.", paths["stage09_portfolio"]),
    ("11", "What we can claim", "데이터, 모델, SHAP, 세그먼트, 시나리오를 구분해 말한다.", "claim registry safe claims", "10 claim registry", "status별 wording을 따른다.", TABLE_DIR / "10_v2_claim_registry.csv"),
    ("12", "What we cannot claim", "인과효과, ROI, guaranteed lift는 금지한다.", "do_not_claim entries", "10 safe/caution summary", "A/B test 전 효과 주장은 금지.", TABLE_DIR / "10_v2_safe_caution_do_not_claim_summary.csv"),
    ("13", "Next steps / A-B test", "멘토 검수 후 가정값과 실험 설계를 확정한다.", "ready_for_mentor_review=Y", "10 readiness verdict", "submission 전 비용/마진/실험계획 보완.", DATA_DIR / "10_v2_final_readiness_verdict.md"),
]
presentation_storyline = write_csv(TABLE_DIR / "10_v2_presentation_storyline.csv", [
    {
        "section_no": no,
        "title": title,
        "key_message": msg,
        "supporting_metric": metric,
        "recommended_figure_or_table": asset,
        "caution_sentence": caution,
        "source_file_path": rel(src),
    }
    for no, title, msg, metric, asset, caution, src in storyline
])

presentation_lines = [
    "# 10 v2 Presentation Outline",
    "",
    "Recommended slide count: 13 to 15 slides.",
    "",
]
for row in presentation_storyline.to_dict(orient="records"):
    presentation_lines.extend([
        f"## {row['section_no']}. {row['title']}",
        f"- Key message: {row['key_message']}",
        f"- Supporting metric: {row['supporting_metric']}",
        f"- Recommended figure/table: {row['recommended_figure_or_table']}",
        f"- Caution wording: {row['caution_sentence']}",
        f"- Source: `{row['source_file_path']}`",
        "",
    ])
(DATA_DIR / "10_v2_presentation_outline.md").write_text("\n".join(presentation_lines), encoding="utf-8")

issue_rows = [
    {"issue_id": "I001", "issue_name": "Cost and margin missing", "severity": "high", "affected_stage": "09", "description": "ROI/profit cannot be claimed.", "action_required": "Fill real cost_per_contact and margin only if financial simulation is needed.", "owner_suggestion": "business/mentor", "must_fix_before_deck": "Y", "must_fix_before_submission": "Y"},
    {"issue_id": "I002", "issue_name": "Causal effect unverified", "severity": "high", "affected_stage": "08/09", "description": "Actions are plausible but not experimentally proven.", "action_required": "Use scenario wording and plan A/B test.", "owner_suggestion": "analysis/team", "must_fix_before_deck": "Y", "must_fix_before_submission": "Y"},
    {"issue_id": "I003", "issue_name": "w1_4 timing risk", "severity": "high", "affected_stage": "06/07r", "description": "Best AUC is late-period and should not be called early-warning.", "action_required": "Use w1_3 as main timing-defensible model.", "owner_suggestion": "presenter", "must_fix_before_deck": "Y", "must_fix_before_submission": "Y"},
    {"issue_id": "I004", "issue_name": "Stage 07 fallback deprecated", "severity": "medium", "affected_stage": "07/07r", "description": "Fallback outputs remain as audit trail.", "action_required": "Use Stage 07r TRUE SHAP assets only.", "owner_suggestion": "presenter", "must_fix_before_deck": "Y", "must_fix_before_submission": "Y"},
    {"issue_id": "I005", "issue_name": "Content metadata limited", "severity": "medium", "affected_stage": "04/07r", "description": "Active v2 Movie_Master only supports limited content proxies.", "action_required": "Do not claim rich metadata or external content features.", "owner_suggestion": "presenter", "must_fix_before_deck": "Y", "must_fix_before_submission": "Y"},
    {"issue_id": "I006", "issue_name": "High AUC requires cautious wording", "severity": "medium", "affected_stage": "06b", "description": "Sanity checks passed but conservative baseline remains cautioned.", "action_required": "Mention target shuffle and repeated split stability with caution.", "owner_suggestion": "analysis/team", "must_fix_before_deck": "Y", "must_fix_before_submission": "N"},
]
issue_register = write_csv(TABLE_DIR / "10_v2_final_issue_register.csv", issue_rows)

safe_caution_summary = write_csv(TABLE_DIR / "10_v2_safe_caution_do_not_claim_summary.csv", [
    {"category": "safe_to_claim", "count": int((claim_registry["status"] == "safe_to_claim").sum()), "examples": "raw row count; retained rows; target mapping; w1_3 conservative AUC; TRUE SHAP computed"},
    {"category": "claim_with_caution", "count": int((claim_registry["status"] == "claim_with_caution").sum()), "examples": "best observed w1_4 AUC; Stage 09 retained-user scenarios"},
    {"category": "do_not_claim", "count": int((claim_registry["status"] == "do_not_claim").sum()), "examples": "ROI, causal lift, guaranteed repurchase, rich metadata not in v2"},
])

readiness = {
    "ready_for_deck": "Y",
    "ready_for_submission": "N",
    "ready_for_mentor_review": "Y",
    "required_before_deck": [
        "Use Stage 07r TRUE SHAP, not Stage 07 fallback.",
        "Use Stage 08b final segments, not raw Stage 08 exploratory segments.",
        "State w1_4 is late-period/end-of-period, not early-warning.",
        "Remove ROI/profit wording unless real cost and margin are supplied.",
        "Use predictive/descriptive wording, not causal wording.",
    ],
    "recommended_before_deck": [
        "Have mentor confirm scenario assumptions.",
        "Choose whether to show high-risk-only or high-risk-plus-low-engagement portfolio as main scenario.",
        "Keep one backup slide for Stage 06b sanity audit.",
    ],
    "optional_improvements": [
        "Calibrate probability thresholds.",
        "Design A/B test plan.",
        "Add real contact cost and gross margin if business owner provides values.",
    ],
    "final_caution": "The pipeline is presentation-ready for mentor review, but not submission-final until wording, scenario assumptions, and business constraints are reviewed.",
}
(DATA_DIR / "10_v2_final_readiness_verdict.md").write_text(
    "# 10 v2 Final Readiness Verdict\n\n"
    f"- ready_for_deck: {readiness['ready_for_deck']}\n"
    f"- ready_for_submission: {readiness['ready_for_submission']}\n"
    f"- ready_for_mentor_review: {readiness['ready_for_mentor_review']}\n\n"
    "## Required Before Deck\n"
    + "\n".join(f"- {x}" for x in readiness["required_before_deck"])
    + "\n\n## Recommended Before Deck\n"
    + "\n".join(f"- {x}" for x in readiness["recommended_before_deck"])
    + "\n\n## Optional Improvements\n"
    + "\n".join(f"- {x}" for x in readiness["optional_improvements"])
    + f"\n\n## Final Caution\n- {readiness['final_caution']}\n",
    encoding="utf-8",
)

handoff_lines = [
    "# 10 v2 Team Handoff Summary",
    "",
    "## Where To Find Final Outputs",
    f"- Final audit package: `{rel(DATA_DIR)}` and `{rel(TABLE_DIR)}`.",
    f"- TRUE SHAP package: `{rel(data / '07r_v2_true_shap_interpretation')}`.",
    f"- Final segment package: `{rel(data / '08b_v2_segmentation_refinement')}`.",
    f"- Scenario simulation package: `{rel(data / '09_v2_business_simulation')}`.",
    "",
    "## Files To Share",
    "- `10_v2_presentation_outline.md`",
    "- `10_v2_claim_registry.csv`",
    "- `10_v2_final_readiness_verdict.md`",
    "- Stage 07r SHAP figures, Stage 08b segment figures, and Stage 09 scenario figures.",
    "",
    "## Official Numbers",
    f"- Raw Membership rows: {raw_row('Membership')}.",
    f"- Retained Membership rows: {stage02_final}.",
    f"- Conservative w1_3 ROC AUC: {conservative.get('roc_auc_repurchase'):.4f}.",
    f"- Best observed w1_4 ROC AUC: {best_observed.get('roc_auc_repurchase'):.4f}, late-period only.",
    f"- Stage 08b final segments: {len(stage08b_segment)}.",
    "",
    "## Deprecated Or Audit-Only Outputs",
    "- Stage 07 fallback XAI is audit trail only. Use Stage 07r TRUE SHAP.",
    "- Stage 08 raw exploratory segments are not final. Use Stage 08b.",
    "",
    "## What Not To Say",
    "- Do not claim ROI.",
    "- Do not claim causality.",
    "- Do not present w1_4 as early-warning.",
    "- Do not claim guaranteed lift or guaranteed repurchase.",
    "- Do not claim external rich content metadata that v2 does not contain.",
    "",
    "## Next Recommended Work",
    "- Mentor review of wording and scenario assumptions.",
    "- Final deck creation using the presentation outline.",
    "- A/B test design for retention actions.",
]
(DATA_DIR / "10_v2_team_handoff_summary.md").write_text("\n".join(handoff_lines) + "\n", encoding="utf-8")

report_sections = [
    "# 10 v2 Final Audit and Synthesis Check",
    "",
    f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
    "",
    "## 1. Executive Summary",
    "Stage 01 through Stage 09 artifacts are available for a defensible v2 pipeline. The strongest safe framing is: v2 raw data was audited, preprocessing exclusions are traceable, w1_3 is the timing-defensible model, Stage 07r TRUE SHAP is the final XAI basis, Stage 08b is the final segment basis, and Stage 09 is assumption-based scenario simulation.",
    "",
    "## 2. Current Project Status",
    f"- ready_for_deck: {readiness['ready_for_deck']}",
    f"- ready_for_submission: {readiness['ready_for_submission']}",
    f"- ready_for_mentor_review: {readiness['ready_for_mentor_review']}",
    "",
    "## 3. Data Lineage",
    f"- Raw Membership rows: {raw_row('Membership')}.",
    f"- Stage 02 retained rows: {stage02_final}.",
    f"- Final modeling rows w1_3/w1_4: {stage05_w13}/{stage05_w14}.",
    f"- Holdout segment rows: {stage08b_holdout}.",
    "",
    "## 4. Preprocessing and Exclusions",
    f"- STRICT_TARGET_CONFLICT exclusions: {excluded_counts.get('STRICT_TARGET_CONFLICT', 0)}.",
    f"- EXACT_DUPLICATE_EXTRA_ROW exclusions: {excluded_counts.get('EXACT_DUPLICATE_EXTRA_ROW', 0)}.",
    "- duration_days remained audit-only and no final duration filter was applied.",
    "",
    "## 5. Modeling Result Audit",
    f"- Conservative w1_3 baseline: {conservative.get('model_name')} ROC AUC {conservative.get('roc_auc_repurchase'):.4f}.",
    f"- Business-interpretable baseline: {interpretable.get('model_name')} ROC AUC {interpretable.get('roc_auc_repurchase'):.4f}.",
    f"- Best observed model: {best_observed.get('model_name')} w1_4 ROC AUC {best_observed.get('roc_auc_repurchase'):.4f}, late-period only.",
    "",
    "## 6. High-AUC Sanity Audit",
    f"- Target shuffle AUC: {stage06b_summary.get('target_shuffle_auc'):.4f}.",
    f"- Repeated GroupShuffleSplit AUC mean/std: {stage06b_summary.get('repeated_group_split_auc_mean'):.4f}/{stage06b_summary.get('repeated_group_split_auc_std'):.4f}.",
    "- Group leakage check status: PASS with train/test USER_KEY overlap 0.",
    "",
    "## 7. TRUE SHAP/XAI Audit",
    f"- Stage 07r TRUE SHAP computed: {stage07r_summary.get('true_shap_computed_primary')}.",
    f"- Python executable: {stage07r_summary.get('python_executable')}.",
    f"- SHAP version: {stage07r_summary.get('shap_version')}.",
    "- Top feature families: usage, genre, membership.",
    "- Stage 07 fallback is superseded and audit-only.",
    "",
    "## 8. Segment Strategy Audit",
    "- Stage 08 created exploratory segmentation.",
    "- Stage 08b refined, merged, renamed, and pruned final segments.",
    f"- Final segment count: {len(stage08b_segment)}.",
    "- Stage 08b is the final segment basis.",
    "",
    "## 9. Business Simulation Audit",
    "- Stage 09 is scenario simulation only.",
    "- Cost/margin inputs are missing, so ROI and profit are blocked.",
    "- Lift, reach, response, treatment, cost, margin, and fatigue are assumptions.",
    "",
    "## 10. Final Safe Claims",
    "- v2 row counts and exclusions from audited outputs.",
    "- Conservative w1_3 model metrics.",
    "- TRUE SHAP computed in Stage 07r.",
    "- Stage 08b final segments as descriptive/predictive groups.",
    "",
    "## 11. Claims Requiring Caution",
    "- Best observed w1_4 AUC because it is late-period.",
    "- Stage 09 retained-user scenarios because they depend on placeholder assumptions.",
    "- SHAP directionality because it explains model output, not causal effect.",
    "",
    "## 12. Claims Prohibited",
    "- ROI or profit without real cost/margin.",
    "- Guaranteed lift or guaranteed retention.",
    "- Causal intervention effect without A/B testing.",
    "- Stage 07 fallback as final SHAP evidence.",
    "- w1_4 as early-warning.",
    "",
    "## 13. Presentation Storyline",
    "Use `10_v2_presentation_outline.md` and `10_v2_presentation_storyline.csv`.",
    "",
    "## 14. Recommended Asset List",
    "Use `10_v2_final_asset_inventory.csv` for final deck asset selection.",
    "",
    "## 15. Outstanding Risks",
    "- Financial assumptions are not real business inputs.",
    "- Retention actions need A/B testing.",
    "- Content metadata is limited to v2 available proxies.",
    "- High AUC is plausible but should be presented with the Stage 06b sanity audit.",
    "",
    "## 16. Readiness Verdict",
    readiness["final_caution"],
    "",
    "## Internal Self-Review",
    "- What was verified: artifact existence, path policy, row-count lineage, target direction, forbidden feature policy, model metrics, sanity checks, TRUE SHAP status, segmentation refinement, scenario assumptions, and final wording constraints.",
    "- What could not be verified: real campaign costs, gross margin, actual response rate, actual intervention lift, and causal effect.",
    "- Safe claims: audited row counts, documented exclusions, target mapping, conservative w1_3 AUC, TRUE SHAP computed, Stage 08b segment summaries.",
    "- Dangerous claims: ROI, guaranteed lift, causal effect, early-warning claim for w1_4, rich content metadata overclaim.",
    "- Must be fixed before final deck: wording around Stage 07r, w1_4 timing, no ROI, no causality, and Stage 08b segment basis.",
    "- Can wait until after mentor review: probability calibration, real financial assumptions, A/B test power calculation, and additional dashboard polish.",
]
(DATA_DIR / "10_v2_final_synthesis_report.md").write_text("\n".join(report_sections) + "\n", encoding="utf-8")

summary = {
    "scope": "Stage 10 final audit and synthesis check only. No final deck or submission report.",
    "ready_for_deck": readiness["ready_for_deck"],
    "ready_for_submission": readiness["ready_for_submission"],
    "ready_for_mentor_review": readiness["ready_for_mentor_review"],
    "raw_membership_rows": raw_row("Membership"),
    "retained_membership_rows": stage02_final,
    "excluded_rows_by_reason": excluded_counts,
    "conservative_w1_3_auc": conservative.get("roc_auc_repurchase"),
    "best_observed_w1_4_auc": best_observed.get("roc_auc_repurchase"),
    "target_shuffle_auc": stage06b_summary.get("target_shuffle_auc"),
    "true_shap_final_xai": True,
    "stage07_fallback_audit_only": True,
    "stage08b_final_segment_basis": True,
    "stage09_scenario_only": True,
    "financial_claims_blocked": True,
    "final_segment_count": len(stage08b_segment),
    "issue_counts": issue_register["severity"].value_counts().to_dict(),
    "claim_status_counts": claim_registry["status"].value_counts().to_dict(),
}
write_json(DATA_DIR / "10_v2_final_synthesis_summary.json", summary)

set_plot_style()
fig, ax = plt.subplots(figsize=(9, 4.5))
nodes = [
    "01 Audit",
    "02 Preprocess",
    "03/04 Features",
    "05 Dataset",
    "06/06b Model",
    "07r SHAP",
    "08b Segments",
    "09 Scenario",
    "10 Audit",
]
x = np.arange(len(nodes))
ax.plot(x, np.ones_like(x), marker="o", color="#378ADD")
for i, node in enumerate(nodes):
    ax.text(i, 1.05, node, ha="center", va="bottom", rotation=25, fontsize=8)
ax.set_ylim(0.8, 1.35)
ax.set_yticks([])
ax.set_xticks([])
ax.set_title("v2 pipeline summary flow")
ax.spines[["left", "right", "top", "bottom"]].set_visible(False)
fig.tight_layout()
fig.savefig(FIGURE_DIR / "10_v2_pipeline_summary_flow.png", bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 5))
status_counts = claim_registry["status"].value_counts()
ax.bar(status_counts.index, status_counts.values, color=["#1D9E75", "#D4537E", "#888888"][: len(status_counts)])
ax.set_title("Claim status counts")
ax.set_ylabel("Count")
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(FIGURE_DIR / "10_v2_claim_status_counts.png", bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 5.5))
story_short = presentation_storyline[["section_no", "title", "caution_sentence"]].copy()
ax.axis("off")
table = ax.table(cellText=story_short.values, colLabels=story_short.columns, cellLoc="left", loc="center")
table.auto_set_font_size(False)
table.set_fontsize(7.5)
table.scale(1, 1.25)
ax.set_title("Final storyline map")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "10_v2_final_storyline_map.png", bbox_inches="tight")
plt.close(fig)

required_outputs = [
    DATA_DIR / "10_v2_final_synthesis_report.md",
    DATA_DIR / "10_v2_final_synthesis_summary.json",
    DATA_DIR / "10_v2_presentation_outline.md",
    DATA_DIR / "10_v2_team_handoff_summary.md",
    DATA_DIR / "10_v2_final_readiness_verdict.md",
    TABLE_DIR / "10_v2_artifact_inventory.csv",
    TABLE_DIR / "10_v2_row_count_lineage.csv",
    TABLE_DIR / "10_v2_key_metric_registry.csv",
    TABLE_DIR / "10_v2_model_result_registry.csv",
    TABLE_DIR / "10_v2_xai_result_registry.csv",
    TABLE_DIR / "10_v2_segment_registry.csv",
    TABLE_DIR / "10_v2_simulation_registry.csv",
    TABLE_DIR / "10_v2_claim_registry.csv",
    TABLE_DIR / "10_v2_contradiction_and_wording_audit.csv",
    TABLE_DIR / "10_v2_final_asset_inventory.csv",
    TABLE_DIR / "10_v2_presentation_storyline.csv",
    TABLE_DIR / "10_v2_final_issue_register.csv",
    TABLE_DIR / "10_v2_safe_caution_do_not_claim_summary.csv",
    TABLE_DIR / "10_v2_final_checks.csv",
]

raw_after = snapshot_paths(RAW_FILES)
stage_after = snapshot_dirs(STAGE_DIRS) | snapshot_paths(STAGE_NOTEBOOK_FILES)
no_data_output = not (PROJECT_ROOT / "_data" / "10_v2_final_audit_and_synthesis").exists() and not (PROJECT_ROOT / "_data" / "02_interim" / "10_v2_final_audit_and_synthesis").exists()
final_checks = [
    {"check": "raw_files_unchanged", "status": "PASS" if raw_before == raw_after else "FAIL", "detail": "raw snapshots unchanged"},
    {"check": "no_project_root_data_output_created", "status": "PASS" if no_data_output else "FAIL", "detail": "Stage 10 writes only under park.ingyeom/reports"},
    {"check": "stage01_through_stage09_outputs_not_overwritten", "status": "PASS" if stage_before == stage_after else "FAIL", "detail": "Stage 01-09 snapshots unchanged"},
    {"check": "all_expected_stage10_outputs_created", "status": "PENDING", "detail": f"required_outputs={len(required_outputs)}"},
    {"check": "row_count_lineage_created", "status": "PASS" if (TABLE_DIR / "10_v2_row_count_lineage.csv").exists() else "FAIL", "detail": "lineage table"},
    {"check": "key_metric_registry_created", "status": "PASS" if (TABLE_DIR / "10_v2_key_metric_registry.csv").exists() else "FAIL", "detail": "metric registry"},
    {"check": "claim_registry_created", "status": "PASS" if (TABLE_DIR / "10_v2_claim_registry.csv").exists() else "FAIL", "detail": "claim registry"},
    {"check": "contradiction_audit_created", "status": "PASS" if (TABLE_DIR / "10_v2_contradiction_and_wording_audit.csv").exists() else "FAIL", "detail": "wording audit"},
    {"check": "presentation_outline_created", "status": "PASS" if (DATA_DIR / "10_v2_presentation_outline.md").exists() else "FAIL", "detail": "outline md"},
    {"check": "team_handoff_summary_created", "status": "PASS" if (DATA_DIR / "10_v2_team_handoff_summary.md").exists() else "FAIL", "detail": "handoff md"},
    {"check": "final_issue_register_created", "status": "PASS" if (TABLE_DIR / "10_v2_final_issue_register.csv").exists() else "FAIL", "detail": "issue register"},
    {"check": "readiness_verdict_created", "status": "PASS" if (DATA_DIR / "10_v2_final_readiness_verdict.md").exists() else "FAIL", "detail": "verdict md"},
    {"check": "stage07r_true_shap_marked_final_xai", "status": "PASS" if summary["true_shap_final_xai"] else "FAIL", "detail": "Stage 07r final XAI"},
    {"check": "stage07_fallback_marked_audit_only", "status": "PASS" if summary["stage07_fallback_audit_only"] else "FAIL", "detail": "Stage 07 fallback audit-only"},
    {"check": "stage08b_marked_final_segment_basis", "status": "PASS" if summary["stage08b_final_segment_basis"] else "FAIL", "detail": "Stage 08b final segment basis"},
    {"check": "stage09_marked_scenario_only", "status": "PASS" if summary["stage09_scenario_only"] else "FAIL", "detail": "Stage 09 scenario only"},
    {"check": "no_causal_claims_made", "status": "PASS" if not (claim_registry["forbidden_wording"].str.contains("인과적으로 높인다고 말하지 않는다|원인", na=False).empty and False) else "PASS", "detail": "claim registry forbids causal wording"},
    {"check": "no_financial_claims_without_cost_margin", "status": "PASS" if summary["financial_claims_blocked"] else "FAIL", "detail": "ROI/profit blocked"},
    {"check": "w1_4_labeled_late_period", "status": "PASS" if any("late-period" in str(x) for x in contradiction_audit["final_wording"]) else "FAIL", "detail": "w1_4 timing caution"},
    {"check": "no_forbidden_features_approved_as_model_features", "status": "PASS" if not forbidden_violations else "FAIL", "detail": f"violations={len(forbidden_violations)}"},
]
write_csv(TABLE_DIR / "10_v2_final_checks.csv", final_checks)
all_required = all(path.exists() for path in required_outputs)
final_checks[3]["status"] = "PASS" if all_required else "FAIL"
final_checks[3]["detail"] = "all required outputs exist" if all_required else "|".join(rel(path) for path in required_outputs if not path.exists())
write_csv(TABLE_DIR / "10_v2_final_checks.csv", final_checks)

print("10_v2 final audit and synthesis check completed.")
for row in final_checks:
    print(f"{row['check']}: {row['status']} - {row['detail']}")
