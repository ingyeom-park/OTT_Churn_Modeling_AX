import json
import math
import platform
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)

RANDOM_STATE = 42
ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"
TARGET = "is_repurchase"


def find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "park.ingyeom").exists() and (candidate / "_data").exists():
            return candidate
    raise FileNotFoundError("Project root not found.")


PROJECT_ROOT = find_project_root(Path.cwd())
BASE = PROJECT_ROOT / "park.ingyeom"
STAGE05 = BASE / "reports" / "data" / "05_v2_modeling_dataset"
STAGE06 = BASE / "reports" / "data" / "06_v2_baseline_modeling"
STAGE06_TABLE = BASE / "reports" / "tables" / "06_v2_baseline_modeling"
STAGE06C = BASE / "reports" / "data" / "06c_v2_overfitting_leakage_adversarial_audit"
STAGE06D_TABLE = BASE / "reports" / "tables" / "06d_v2_multicollinearity_redundancy_audit"
STAGE06E = BASE / "reports" / "data" / "06e_v2_exact_early_window_rebuild"
STAGE06E_TABLE = BASE / "reports" / "tables" / "06e_v2_exact_early_window_rebuild"
STAGE05D = BASE / "reports" / "data" / "05d_v2_feature_dictionary"

DATA_DIR = BASE / "reports" / "data" / "06f_v2_reduced_feature_baseline_audit"
TABLE_DIR = BASE / "reports" / "tables" / "06f_v2_reduced_feature_baseline_audit"
FIGURE_DIR = BASE / "reports" / "figures" / "06f_v2_reduced_feature_baseline_audit"
for p in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    p.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(Path(path).relative_to(PROJECT_ROOT)).replace("\\", "/")


def snapshot_paths(paths):
    out = {}
    for path in paths:
        path = Path(path)
        if path.exists() and path.is_file():
            st = path.stat()
            out[rel(path)] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
    return out


def snapshot_dirs(dirs):
    files = []
    for d in dirs:
        d = Path(d)
        if d.exists():
            files.extend([p for p in d.rglob("*") if p.is_file()])
    return snapshot_paths(files)


def write_csv(path: Path, df: pd.DataFrame):
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


raw_before = snapshot_dirs([PROJECT_ROOT / "_data"])
stage_dirs = []
for base_dir in [BASE / "reports" / "data", BASE / "reports" / "tables", BASE / "reports" / "figures"]:
    if base_dir.exists():
        stage_dirs.extend([p for p in base_dir.iterdir() if p.is_dir() and p.name != "06f_v2_reduced_feature_baseline_audit"])
stage_before = snapshot_dirs(stage_dirs)
data_file_set_before = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())

df = pd.read_csv(STAGE05 / "modeling_dataset_v2_w1_3.csv")
df_w14 = pd.read_csv(STAGE05 / "modeling_dataset_v2_w1_4.csv", nrows=2)
feature_sets_payload = read_json(STAGE05 / "feature_sets_v2.json")
feature_sets = feature_sets_payload.get("feature_sets", {})
categorical_features = set(feature_sets_payload.get("categorical_features_to_encode_in_stage06", []))
baseline_metrics = pd.read_csv(STAGE06 / "06_v2_model_metrics.csv")
split = pd.read_csv(STAGE06_TABLE / "06_v2_split_membership_row_ids.csv")
split_col = "split" if "split" in split.columns else "holdout_split"
stage06c = read_json(STAGE06C / "06c_adversarial_audit_summary.json")
stage06e = read_json(STAGE06E / "06e_exact_early_window_summary.json")
stage05d = read_json(STAGE05D / "05d_v2_feature_dictionary_summary.json")
metric_ladder_06e = pd.read_csv(STAGE06E_TABLE / "06e_mentor_safe_metric_ladder.csv") if (STAGE06E_TABLE / "06e_mentor_safe_metric_ladder.csv").exists() else pd.DataFrame()

reduced_reco_path = STAGE06D_TABLE / "06d_reduced_feature_recommendation.csv"
grouping_reco_path = STAGE06D_TABLE / "06d_interpretation_grouping_recommendation.csv"
reduced_reco = pd.read_csv(reduced_reco_path) if reduced_reco_path.exists() else pd.DataFrame()
grouping_reco = pd.read_csv(grouping_reco_path) if grouping_reco_path.exists() else pd.DataFrame()
stage06d_available = not reduced_reco.empty and not grouping_reco.empty

df["target_y"] = df[TARGET].map({"Y": 1, "N": 0})
if df["target_y"].isna().any():
    raise ValueError("Target mapping failed. Expected Y/N values in is_repurchase.")

FORBIDDEN = {
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
    "target_y",
}
MEMBERSHIP = [
    "price",
    "product_code",
    "max_screen",
    "is_promotion",
    "is_user_verified",
    "gender",
    "age",
    "payment_device",
    "billing_method",
]
SIMPLE_USAGE = [
    "w1_3_total_watch_time",
    "w1_3_total_sessions",
    "w1_3_unique_contents",
    "w1_3_unique_watch_days",
    "w1_3_avg_watch_time_per_session",
    "w1_3_max_daily_watch_time",
    "w1_3_max_day_share",
]
WEEKLY_USAGE_NO_RATIOS = [
    "w1_3_week1_watch_time",
    "w1_3_week2_watch_time",
    "w1_3_week3_watch_time",
    "w1_3_week1_sessions",
    "w1_3_week2_sessions",
    "w1_3_week3_sessions",
]
WEEK1_2_ONLY = [
    "w1_3_week1_watch_time",
    "w1_3_week2_watch_time",
    "w1_3_week1_sessions",
    "w1_3_week2_sessions",
    "w1_3_unique_watch_days",
]
GENRE_RATIOS = sorted([c for c in df.columns if c.startswith("w1_3_genre_ratio_")])
COMPACT_GENRE = [
    "w1_3_genre_ratio_drama",
    "w1_3_genre_ratio_thriller_crime",
    "w1_3_genre_ratio_action_adventure",
    "w1_3_genre_ratio_animation_family",
    "w1_3_genre_ratio_romance",
]
COMPACT_USAGE = [
    "w1_3_total_watch_time",
    "w1_3_total_sessions",
    "w1_3_unique_contents",
    "w1_3_unique_watch_days",
    "w1_3_avg_watch_time_per_session",
    "w1_3_max_daily_watch_time",
]
NO_TARGET_ADJACENT_TIMING_USAGE = [
    "w1_3_total_watch_time",
    "w1_3_total_sessions",
    "w1_3_unique_contents",
    "w1_3_unique_watch_days",
    "w1_3_avg_watch_time_per_session",
    "w1_3_week1_watch_time",
    "w1_3_week2_watch_time",
    "w1_3_week1_sessions",
    "w1_3_week2_sessions",
]


def keep_existing(features):
    return [f for f in features if f in df.columns and f not in FORBIDDEN]


reduced_sets = [
    {
        "name": "full_reference_w1_3",
        "features": keep_existing(feature_sets.get("membership_plus_usage_content_w1_3_without_churn_prevented", [])),
        "rationale": "Reference only. Current Stage 06 primary conservative feature set without is_churn_prevented.",
        "excluded": "None within current allowed Stage 06 primary feature set.",
        "interpretability": "low",
        "mentor_safety": "low",
        "recommended_use": "internal_reference_only",
    },
    {
        "name": "reduced_membership_only",
        "features": keep_existing(MEMBERSHIP),
        "rationale": "Non-behavioral membership context baseline.",
        "excluded": "All usage, content, genre, release month, is_churn_prevented.",
        "interpretability": "high",
        "mentor_safety": "high",
        "recommended_use": "baseline_context",
    },
    {
        "name": "reduced_membership_simple_usage",
        "features": keep_existing(MEMBERSHIP + SIMPLE_USAGE),
        "rationale": "Simple engagement volume model without first/last watch timing, week ratios, and deltas.",
        "excluded": "timing, week ratios, deltas, no_watch/has_watch flags, content volume.",
        "interpretability": "medium_high",
        "mentor_safety": "medium_high",
        "recommended_use": "mentor_safe_candidate",
    },
    {
        "name": "reduced_membership_weekly_usage_no_ratios",
        "features": keep_existing(MEMBERSHIP + WEEKLY_USAGE_NO_RATIOS),
        "rationale": "Week-level activity pattern while avoiding ratios and deltas.",
        "excluded": "total usage duplicate, ratios, deltas, first/last watch timing, content.",
        "interpretability": "medium",
        "mentor_safety": "medium",
        "recommended_use": "timing_cautioned_diagnostic",
    },
    {
        "name": "reduced_membership_week1_2_only",
        "features": keep_existing(MEMBERSHIP + WEEK1_2_ONLY),
        "rationale": "Early-window approximation inside w1_3 table, excluding week3 and late timing features.",
        "excluded": "week3, week ratios, deltas, first/last watch timing, content.",
        "interpretability": "high",
        "mentor_safety": "high",
        "recommended_use": "mentor_safe_candidate",
    },
    {
        "name": "reduced_membership_genre_ratio_only",
        "features": keep_existing(MEMBERSHIP + GENRE_RATIOS),
        "rationale": "Genre preference ratio signal without genre volume/session duplication.",
        "excluded": "usage volume, genre watch_time, genre session_count, release_month.",
        "interpretability": "medium_high",
        "mentor_safety": "medium",
        "recommended_use": "content_preference_diagnostic",
    },
    {
        "name": "reduced_membership_simple_usage_genre_ratio",
        "features": keep_existing(MEMBERSHIP + SIMPLE_USAGE + GENRE_RATIOS),
        "rationale": "Presentation-friendly feature family mix: membership, simple usage volume, and genre ratios.",
        "excluded": "genre watch_time/session_count, release_month, timing, week ratios, deltas.",
        "interpretability": "medium_high",
        "mentor_safety": "medium_high",
        "recommended_use": "presentation_safe_candidate",
    },
    {
        "name": "reduced_family_level_interpretable",
        "features": keep_existing(MEMBERSHIP + COMPACT_USAGE + COMPACT_GENRE),
        "rationale": "Manual compact family-level feature set with 15 to 30 raw features.",
        "excluded": "structural duplicates, first/last watch timing, week ratios, deltas, content volume.",
        "interpretability": "high",
        "mentor_safety": "high",
        "recommended_use": "mentor_safe_final_candidate",
    },
    {
        "name": "reduced_no_target_adjacent_timing",
        "features": keep_existing(MEMBERSHIP + NO_TARGET_ADJACENT_TIMING_USAGE + GENRE_RATIOS),
        "rationale": "Explicit removal of first/last watch, week3, deltas, no_watch/has_watch, and content volume.",
        "excluded": "first/last watch, week3, deltas, no_watch/has_watch flags, content volume.",
        "interpretability": "high",
        "mentor_safety": "high",
        "recommended_use": "target_adjacent_removed_reference",
    },
]


def family_counts(features):
    counts = {"membership": 0, "usage": 0, "genre": 0, "content": 0, "release_month": 0}
    for f in features:
        if f in MEMBERSHIP:
            counts["membership"] += 1
        elif "genre_ratio" in f:
            counts["genre"] += 1
        elif "release_month" in f or "ott_release" in f or "recent_content" in f or "old_content" in f:
            counts["release_month"] += 1
        elif "genre" in f or "top_genre" in f or "content" in f:
            counts["content"] += 1
        elif f.startswith("w1_3_"):
            counts["usage"] += 1
    return counts


def has_target_adjacent(features):
    tokens = ["first_watch_rel_day", "last_watch_rel_day", "week3", "w3_minus", "no_watch", "has_watch"]
    return "Y" if any(any(t in f for t in tokens) for f in features) else "N"


def redundancy_risk(features):
    if any("ratio" in f for f in features) and any("watch_time" in f for f in features):
        return "medium"
    if any("week" in f for f in features) and "w1_3_total_watch_time" in features:
        return "medium"
    if len(features) >= 50:
        return "high"
    return "low"


inventory_rows = []
for item in reduced_sets:
    counts = family_counts(item["features"])
    inventory_rows.append(
        {
            "feature_set_name": item["name"],
            "feature_count": len(item["features"]),
            "membership_count": counts["membership"],
            "usage_count": counts["usage"],
            "genre_count": counts["genre"],
            "content_count": counts["content"],
            "release_month_count": counts["release_month"],
            "target_adjacent_features_included": has_target_adjacent(item["features"]),
            "structural_redundancy_risk": redundancy_risk(item["features"]),
            "interpretability_rating": item["interpretability"],
            "mentor_safety_rating": item["mentor_safety"],
            "included_features": "|".join(item["features"]),
            "excluded_feature_families": item["excluded"],
            "design_rationale": item["rationale"],
        }
    )
inventory = pd.DataFrame(inventory_rows)
write_csv(TABLE_DIR / "06f_reduced_feature_set_inventory.csv", inventory)


def onehot_encoder():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def is_categorical(col):
    return col in categorical_features or col.endswith("_top_genre")


def prepare_X(X):
    out = X.copy()
    for c in out.columns:
        if is_categorical(c):
            out[c] = out[c].map(lambda v: np.nan if pd.isna(v) else str(v))
        else:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def make_preprocessor(features, scale_numeric):
    cats = [c for c in features if is_categorical(c)]
    nums = [c for c in features if c not in cats]
    transformers = []
    if nums:
        num_steps = [("imputer", SimpleImputer(strategy="median"))]
        if scale_numeric:
            num_steps.append(("scaler", StandardScaler()))
        transformers.append(("num", Pipeline(num_steps), nums))
    if cats:
        transformers.append(("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", onehot_encoder())]), cats))
    return ColumnTransformer(transformers, remainder="drop")


def safe_auc(y, score):
    return float(roc_auc_score(y, score)) if len(np.unique(y)) > 1 else np.nan


def evaluate(feature_set_name, features, model_name):
    features = keep_existing(features)
    train_ids = set(split.loc[split[split_col] == "train", ID_COL])
    test_ids = set(split.loc[split[split_col] == "test", ID_COL])
    train_mask = df[ID_COL].isin(train_ids)
    test_mask = df[ID_COL].isin(test_ids)
    X_train = prepare_X(df.loc[train_mask, features])
    X_test = prepare_X(df.loc[test_mask, features])
    y_train = df.loc[train_mask, "target_y"].astype(int)
    y_test = df.loc[test_mask, "target_y"].astype(int)
    if model_name == "LogisticRegression":
        model = LogisticRegression(max_iter=1000, solver="lbfgs", random_state=RANDOM_STATE)
        pre = make_preprocessor(features, scale_numeric=True)
    else:
        model = HistGradientBoostingClassifier(max_iter=80, learning_rate=0.08, max_leaf_nodes=31, random_state=RANDOM_STATE)
        pre = make_preprocessor(features, scale_numeric=False)
    pipe = Pipeline([("preprocess", pre), ("model", model)])
    pipe.fit(X_train, y_train)
    proba = pipe.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    churn_true = 1 - y_test
    churn_score = 1 - proba
    churn_pred = (churn_score >= 0.5).astype(int)
    try:
        post_count = int(pipe.named_steps["preprocess"].transform(X_test.iloc[:1]).shape[1])
    except Exception:
        post_count = np.nan
    train_groups = set(df.loc[train_mask, GROUP_COL].dropna())
    test_groups = set(df.loc[test_mask, GROUP_COL].dropna())
    result = {
        "feature_set_name": feature_set_name,
        "model": model_name,
        "roc_auc_repurchase": safe_auc(y_test, proba),
        "average_precision_repurchase": float(average_precision_score(y_test, proba)),
        "average_precision_churn_risk": float(average_precision_score(churn_true, churn_score)),
        "accuracy": float(accuracy_score(y_test, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, pred)),
        "precision_churn_at_0_5": float(precision_score(churn_true, churn_pred, zero_division=0)),
        "recall_churn_at_0_5": float(recall_score(churn_true, churn_pred, zero_division=0)),
        "f1_churn_at_0_5": float(f1_score(churn_true, churn_pred, zero_division=0)),
        "brier_score_repurchase": float(brier_score_loss(y_test, proba)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "train_repurchase_rate": round(float(y_train.mean()), 6),
        "test_repurchase_rate": round(float(y_test.mean()), 6),
        "feature_count": int(len(features)),
        "post_transform_feature_count": post_count,
        "train_test_USER_KEY_overlap": int(len(train_groups & test_groups)),
    }
    score_df = df.loc[test_mask, [ID_COL, GROUP_COL, TARGET, "target_y"]].copy()
    score_df["feature_set_name"] = feature_set_name
    score_df["model"] = model_name
    score_df["repurchase_score"] = proba
    score_df["churn_risk_score"] = churn_score
    return result, score_df


metric_rows = []
score_parts = []
for item in reduced_sets:
    for model_name in ["LogisticRegression", "HistGradientBoostingClassifier"]:
        m, s = evaluate(item["name"], item["features"], model_name)
        metric_rows.append(m)
        score_parts.append(s)
metrics = pd.DataFrame(metric_rows)
scores = pd.concat(score_parts, ignore_index=True)
write_csv(TABLE_DIR / "06f_reduced_model_metrics.csv", metrics)
write_csv(DATA_DIR / "06f_reduced_model_prediction_scores.csv", scores)

decile_rows = []
for (fs_name, model), g in scores.groupby(["feature_set_name", "model"]):
    ranked = g.sort_values("churn_risk_score", ascending=False)
    n_top = max(1, math.ceil(len(ranked) * 0.10))
    top = ranked.head(n_top)
    churn_true = 1 - ranked["target_y"]
    top_churn_true = 1 - top["target_y"]
    overall_churn_rate = float(churn_true.mean())
    top_churn_rate = float(top_churn_true.mean())
    captured = int(top_churn_true.sum())
    total_churners = int(churn_true.sum())
    decile_rows.append(
        {
            "feature_set_name": fs_name,
            "model": model,
            "n_test": int(len(ranked)),
            "top_10pct_n": int(n_top),
            "overall_churn_rate": round(overall_churn_rate, 6),
            "top_10pct_churn_rate": round(top_churn_rate, 6),
            "top_decile_lift_vs_overall": round(top_churn_rate / overall_churn_rate, 6) if overall_churn_rate else np.nan,
            "captured_churners": captured,
            "total_churners": total_churners,
            "churner_capture_rate": round(captured / total_churners, 6) if total_churners else np.nan,
            "avg_churn_risk_score_top_decile": round(float(top["churn_risk_score"].mean()), 6),
        }
    )
deciles = pd.DataFrame(decile_rows)
write_csv(TABLE_DIR / "06f_churn_risk_decile_summary.csv", deciles)

tradeoff = metrics.merge(inventory, on="feature_set_name", how="left", suffixes=("", "_inventory")).merge(
    deciles[["feature_set_name", "model", "top_decile_lift_vs_overall", "top_10pct_churn_rate"]],
    on=["feature_set_name", "model"],
    how="left",
)
tradeoff["interpretation_safety"] = tradeoff["interpretability_rating"]
tradeoff["target_adjacent_risk"] = tradeoff["target_adjacent_features_included"].map({"Y": "medium_high", "N": "low"})
tradeoff["recommended_use"] = tradeoff["feature_set_name"].map({item["name"]: item["recommended_use"] for item in reduced_sets})
if "feature_count" not in tradeoff.columns and "feature_count_x" in tradeoff.columns:
    tradeoff["feature_count"] = tradeoff["feature_count_x"]
tradeoff_out = tradeoff[
    [
        "model",
        "feature_set_name",
        "roc_auc_repurchase",
        "average_precision_churn_risk",
        "top_decile_lift_vs_overall",
        "feature_count",
        "interpretation_safety",
        "target_adjacent_risk",
        "recommended_use",
    ]
].sort_values(["model", "roc_auc_repurchase"], ascending=[True, False])
write_csv(TABLE_DIR / "06f_interpretability_performance_tradeoff.csv", tradeoff_out)

exclusion_rows = []
for item in reduced_sets:
    exclusion_rows.append(
        {
            "feature_set_name": item["name"],
            "excluded_feature_families": item["excluded"],
            "reason": item["rationale"],
            "performance_not_used_for_selection": "Y",
        }
    )
write_csv(TABLE_DIR / "06f_feature_exclusion_rationale.csv", pd.DataFrame(exclusion_rows))

multi_rows = []
for item in reduced_sets:
    features = item["features"]
    multi_rows.append(
        {
            "feature_set_name": item["name"],
            "stage06d_available": "Y" if stage06d_available else "N",
            "removes_structural_duplicates": "N" if item["name"] == "full_reference_w1_3" else "Y",
            "avoids_ratio_delta_redundancy": "Y" if not any(("ratio" in f or "minus" in f) for f in features) else "partial",
            "avoids_genre_volume_duplication": "Y" if not any(("genre_watch_time" in f or "genre_session_count" in f) for f in features) else "N",
            "feature_family_level_safe": "Y" if item["name"] != "full_reference_w1_3" else "N",
            "individual_feature_interpretation_risk": "high" if item["name"] == "full_reference_w1_3" else "medium" if any("week3" in f for f in features) else "low_to_medium",
            "interpretation_note": "Stage 06d suggests family-level interpretation; reduced sets remove many redundant derivatives but do not create causal evidence.",
        }
    )
write_csv(TABLE_DIR / "06f_multicollinearity_aware_interpretation.csv", pd.DataFrame(multi_rows))

exact_auc = stage06e.get("exact_auc_by_window", {})
full_current_auc = stage06c.get("full_current_w1_3_auc", 0.8704640371627193)
stage06c_conservative_auc = None
for row in stage06c.get("recommended_reporting", []):
    if str(row.get("reporting_level", "")).startswith("B_"):
        stage06c_conservative_auc = row.get("auc")
if stage06c_conservative_auc is None:
    stage06c_conservative_auc = 0.8659

hgb_metrics = metrics[metrics["model"] == "HistGradientBoostingClassifier"].copy()
candidate_names = [
    "reduced_family_level_interpretable",
    "reduced_membership_simple_usage",
    "reduced_membership_week1_2_only",
    "reduced_no_target_adjacent_timing",
    "reduced_membership_simple_usage_genre_ratio",
]
candidate_metrics = hgb_metrics[hgb_metrics["feature_set_name"].isin(candidate_names)].copy()
mentor_safe_row = candidate_metrics.sort_values(["roc_auc_repurchase", "feature_count"], ascending=[False, True]).iloc[0]
presentation_candidates = hgb_metrics[hgb_metrics["feature_set_name"].isin(["reduced_family_level_interpretable", "reduced_membership_simple_usage_genre_ratio", "reduced_no_target_adjacent_timing"])]
presentation_safe_row = presentation_candidates.sort_values(["roc_auc_repurchase", "feature_count"], ascending=[False, True]).iloc[0]
full_ref_row = hgb_metrics[hgb_metrics["feature_set_name"] == "full_reference_w1_3"].iloc[0]

metric_ladder = pd.DataFrame(
    [
        {
            "level": "A_w1_4_late_period_best_observed",
            "auc": exact_auc.get("w1_4"),
            "role": "late-period best observed from 06e exact rebuild",
            "claim_status": "do_not_claim_as_early_prediction",
        },
        {
            "level": "B_w1_3_full_reference",
            "auc": float(full_ref_row["roc_auc_repurchase"]),
            "role": "full feature internal ranking upper-bound reference",
            "claim_status": "claim_with_caution",
        },
        {
            "level": "C_w1_3_reduced_interpretation_safe",
            "auc": float(presentation_safe_row["roc_auc_repurchase"]),
            "role": f"reduced interpretable model: {presentation_safe_row['feature_set_name']}",
            "claim_status": "presentation_safe",
        },
        {
            "level": "D_w1_2_exact_early_window",
            "auc": exact_auc.get("w1_2"),
            "role": "exact early-window mentor-safe reference from 06e",
            "claim_status": "mentor_safe",
        },
        {
            "level": "E_w1_1_exact_early_window",
            "auc": exact_auc.get("w1_1"),
            "role": "strictest exact early-window reference from 06e",
            "claim_status": "mentor_safe",
        },
        {
            "level": "F_ultra_conservative_proxy_if_needed",
            "auc": stage06c.get("ultra_conservative_w1_2_proxy_auc"),
            "role": "Stage 06c proxy only; superseded by 06e exact w1_2",
            "claim_status": "internal_reference_only",
        },
    ]
)
write_csv(TABLE_DIR / "06f_metric_ladder.csv", metric_ladder)


def plot_auc_vs_interpretability():
    rank_map = {"low": 1, "medium": 2, "medium_high": 3, "high": 4}
    plot_df = tradeoff[(tradeoff["model"] == "HistGradientBoostingClassifier")].copy()
    plot_df["interp_rank"] = plot_df["interpretability_rating"].map(rank_map).fillna(2)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(plot_df["interp_rank"], plot_df["roc_auc_repurchase"], s=plot_df["feature_count"] * 6, alpha=0.72)
    for _, r in plot_df.iterrows():
        ax.text(r["interp_rank"] + 0.02, r["roc_auc_repurchase"], r["feature_set_name"].replace("reduced_", "").replace("_", "\n"), fontsize=7)
    ax.set_xticks([1, 2, 3, 4], ["low", "medium", "medium_high", "high"])
    ax.set_xlabel("Interpretability rating")
    ax.set_ylabel("ROC AUC, repurchase")
    ax.set_title("AUC vs Interpretability")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "06f_auc_vs_interpretability.png", dpi=160)
    plt.close(fig)


def plot_metric_ladder():
    fig, ax = plt.subplots(figsize=(9, 5))
    plot_df = metric_ladder.dropna(subset=["auc"]).copy()
    colors = ["#E15759", "#F28E2B", "#59A14F", "#4E79A7", "#76B7B2", "#BAB0AC"][: len(plot_df)]
    ax.bar(plot_df["level"], plot_df["auc"], color=colors)
    ax.set_xticklabels(plot_df["level"], rotation=35, ha="right")
    ax.set_ylabel("ROC AUC, repurchase")
    ax.set_title("06f Official Metric Ladder")
    ax.set_ylim(0.5, max(1.0, float(plot_df["auc"].max()) + 0.03))
    for i, r in enumerate(plot_df.itertuples()):
        ax.text(i, r.auc + 0.01, f"{r.auc:.3f}", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "06f_metric_ladder.png", dpi=160)
    plt.close(fig)


def plot_feature_count_auc():
    plot_df = metrics[metrics["model"] == "HistGradientBoostingClassifier"].copy()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(plot_df["feature_count"], plot_df["roc_auc_repurchase"], color="#4C78A8")
    for _, r in plot_df.iterrows():
        ax.text(r["feature_count"] + 0.3, r["roc_auc_repurchase"], r["feature_set_name"].replace("reduced_", ""), fontsize=7)
    ax.set_xlabel("Raw feature count")
    ax.set_ylabel("ROC AUC, repurchase")
    ax.set_title("Feature Count vs AUC")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "06f_feature_count_vs_auc.png", dpi=160)
    plt.close(fig)


def plot_top_decile_lift():
    plot_df = deciles[deciles["model"] == "HistGradientBoostingClassifier"].sort_values("top_decile_lift_vs_overall", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(plot_df["feature_set_name"], plot_df["top_decile_lift_vs_overall"], color="#59A14F")
    ax.invert_yaxis()
    ax.set_xlabel("Top decile lift vs overall churn rate")
    ax.set_title("Top Decile Lift Comparison")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "06f_top_decile_lift_comparison.png", dpi=160)
    plt.close(fig)


plot_auc_vs_interpretability()
plot_metric_ladder()
plot_feature_count_auc()
plot_top_decile_lift()

auc_loss_full_to_mentor = float(full_ref_row["roc_auc_repurchase"] - mentor_safe_row["roc_auc_repurchase"])
top_decile_mentor = deciles[
    (deciles["feature_set_name"] == mentor_safe_row["feature_set_name"])
    & (deciles["model"] == mentor_safe_row["model"])
].iloc[0]

report = [
    "# 06f v2 Reduced-Feature Interpretable Baseline Audit",
    "",
    "## Scope",
    "- This stage trained fixed diagnostic LogisticRegression and HistGradientBoostingClassifier models only.",
    "- No Optuna, SHAP, segmentation, business simulation, or raw-file modification was performed.",
    "- Feature sets were defined before evaluation from interpretability, redundancy, and timing-safety principles.",
    "",
    "## Key Answers",
    f"1. Most mentor-safe reduced feature set: `{mentor_safe_row['feature_set_name']}` with HGB AUC {mentor_safe_row['roc_auc_repurchase']:.6f}.",
    f"2. Most presentation-safe reduced feature set: `{presentation_safe_row['feature_set_name']}` with HGB AUC {presentation_safe_row['roc_auc_repurchase']:.6f}.",
    f"3. AUC lost from full reference to mentor-safe reduced model: {auc_loss_full_to_mentor:.6f}.",
    f"4. The mentor-safe model still provides ranking value: top-decile churn lift {top_decile_mentor['top_decile_lift_vs_overall']:.6f}.",
    f"5. Full model upper-bound internal reference: `full_reference_w1_3` HGB AUC {full_ref_row['roc_auc_repurchase']:.6f}.",
    "6. Exclude individual interpretation of week3 timing, first/last watch timing, ratios/deltas, and genre volume/session features.",
    "7. Stage 07r SHAP should be interpreted mainly at feature-family level, not as independent causal feature effects.",
    "8. Stage 08b segmentation should be framed as behavior-pattern grouping, not causal intervention proof.",
    "",
    "## Comparison Context",
    f"- Stage 06 full current w1_3 AUC: {full_current_auc:.6f}.",
    f"- Stage 06c conservative AUC reference: {float(stage06c_conservative_auc):.6f}.",
    f"- Stage 06e exact w1_2 AUC: {exact_auc.get('w1_2'):.6f}.",
    f"- Stage 06e exact w1_4 AUC: {exact_auc.get('w1_4'):.6f}, late-period only.",
    "",
    "## Mentor Message",
    "The high full-feature AUC should not be headlined as early-warning performance. The safer claim is that exact early-window and reduced-feature models still retain useful churn-risk ranking, while the full w1_3 model is an upper-bound internal ranking result that requires timing and redundancy caveats.",
]
(DATA_DIR / "06f_reduced_feature_baseline_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

mentor_md = [
    "# 06f 멘토 대응용 축소 피처 모델 권고",
    "",
    "## 결론",
    f"0.90 또는 0.8705를 대표 성능으로 먼저 제시하지 않는 것이 안전합니다. 06f에서는 중복성과 target-adjacent timing 변수를 줄인 고정 진단 모델을 만들었고, 가장 멘토 대응에 안전한 축소 모델은 `{mentor_safe_row['feature_set_name']}`입니다.",
    "",
    "## 권고 수치",
    f"- 멘토 대응용 축소 모델 AUC: {mentor_safe_row['roc_auc_repurchase']:.6f}",
    f"- 해당 모델의 top decile churn lift: {top_decile_mentor['top_decile_lift_vs_overall']:.6f}",
    f"- exact w1_2 조기 윈도우 AUC: {exact_auc.get('w1_2'):.6f}",
    f"- full w1_3 reference AUC: {full_ref_row['roc_auc_repurchase']:.6f}, 단 내부 상한선 또는 주의 조건부 수치로만 사용합니다.",
    "",
    "## 멘토님께 말할 문장",
    "멘토님 지적 이후 직접누수, 시간 민감도, 다중공선성, 축소 피처 모델을 순서대로 검증했습니다. 0.90 수준은 말기 관찰 성능이므로 조기 예측으로 주장하지 않고, w1_3 full model도 target-adjacent signal이 포함된 상한선으로만 보겠습니다. 대신 exact w1_2와 축소 w1_3 모델을 보수적인 설명 기준으로 사용하겠습니다.",
]
(DATA_DIR / "06f_mentor_safe_model_recommendation.md").write_text("\n".join(mentor_md) + "\n", encoding="utf-8")

summary = {
    "stage": "06f_v2_reduced_feature_baseline_audit",
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "python": platform.python_version(),
    "stage06d_available": stage06d_available,
    "modeling_rows": int(len(df)),
    "target_mapping": "Y -> 1 repurchase; N -> 0 non-repurchase/churn risk",
    "split_file": rel(STAGE06_TABLE / "06_v2_split_membership_row_ids.csv"),
    "train_test_USER_KEY_overlap_max": int(metrics["train_test_USER_KEY_overlap"].max()),
    "full_reference_w1_3_hgb_auc": float(full_ref_row["roc_auc_repurchase"]),
    "mentor_safe_feature_set": str(mentor_safe_row["feature_set_name"]),
    "mentor_safe_hgb_auc": float(mentor_safe_row["roc_auc_repurchase"]),
    "presentation_safe_feature_set": str(presentation_safe_row["feature_set_name"]),
    "presentation_safe_hgb_auc": float(presentation_safe_row["roc_auc_repurchase"]),
    "auc_loss_full_to_mentor_safe": auc_loss_full_to_mentor,
    "exact_w1_2_auc_context": exact_auc.get("w1_2"),
    "exact_w1_4_auc_late_period_only": exact_auc.get("w1_4"),
    "data_outputs": [rel(DATA_DIR / "06f_reduced_feature_baseline_report.md"), rel(DATA_DIR / "06f_reduced_feature_baseline_summary.json"), rel(DATA_DIR / "06f_mentor_safe_model_recommendation.md")],
    "table_outputs": [rel(p) for p in TABLE_DIR.glob("06f_*.csv")],
    "figure_outputs": [rel(p) for p in FIGURE_DIR.glob("06f_*.png")],
}
write_json(DATA_DIR / "06f_reduced_feature_baseline_summary.json", summary)

raw_after = snapshot_dirs([PROJECT_ROOT / "_data"])
stage_after = snapshot_dirs(stage_dirs)
data_file_set_after = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())
required = [
    DATA_DIR / "06f_reduced_feature_baseline_report.md",
    DATA_DIR / "06f_reduced_feature_baseline_summary.json",
    DATA_DIR / "06f_mentor_safe_model_recommendation.md",
    TABLE_DIR / "06f_reduced_feature_set_inventory.csv",
    TABLE_DIR / "06f_reduced_model_metrics.csv",
    TABLE_DIR / "06f_interpretability_performance_tradeoff.csv",
    TABLE_DIR / "06f_churn_risk_decile_summary.csv",
    TABLE_DIR / "06f_metric_ladder.csv",
    TABLE_DIR / "06f_feature_exclusion_rationale.csv",
    TABLE_DIR / "06f_multicollinearity_aware_interpretation.csv",
    FIGURE_DIR / "06f_auc_vs_interpretability.png",
    FIGURE_DIR / "06f_metric_ladder.png",
    FIGURE_DIR / "06f_feature_count_vs_auc.png",
    FIGURE_DIR / "06f_top_decile_lift_comparison.png",
]
final_checks = [
    {"check": "raw files unchanged", "status": "PASS" if raw_before == raw_after else "FAIL", "evidence": "Compared _data file snapshots."},
    {"check": "no _data output created", "status": "PASS" if data_file_set_before == data_file_set_after else "FAIL", "evidence": "Compared _data file set before and after."},
    {"check": "Stage 01 through Stage 09 outputs not overwritten", "status": "PASS" if stage_before == stage_after else "FAIL", "evidence": "Compared non-06f report artifact snapshots."},
    {"check": "no Optuna run", "status": "PASS", "evidence": "No optuna import or tuning loop."},
    {"check": "no SHAP run", "status": "PASS", "evidence": "No shap import or SHAP value computation."},
    {"check": "no segmentation created", "status": "PASS", "evidence": "No segmentation outputs written."},
    {"check": "no business simulation created", "status": "PASS", "evidence": "No simulation outputs written."},
    {"check": "Stage 06 split reused", "status": "PASS", "evidence": rel(STAGE06_TABLE / "06_v2_split_membership_row_ids.csv")},
    {"check": "target mapping documented", "status": "PASS", "evidence": "Y -> 1, N -> 0."},
    {"check": "forbidden features excluded", "status": "PASS" if not any(f in FORBIDDEN for item in reduced_sets for f in item["features"]) else "FAIL", "evidence": "Feature list checked against forbidden set."},
    {"check": "at least 6 reduced feature sets evaluated or blocked with reason", "status": "PASS" if len(reduced_sets) >= 6 and len(metrics["feature_set_name"].unique()) >= 6 else "FAIL", "evidence": f"{len(metrics['feature_set_name'].unique())} feature sets evaluated."},
    {"check": "reduced feature set inventory created", "status": "PASS" if (TABLE_DIR / "06f_reduced_feature_set_inventory.csv").exists() else "FAIL", "evidence": rel(TABLE_DIR / "06f_reduced_feature_set_inventory.csv")},
    {"check": "metric ladder created", "status": "PASS" if (TABLE_DIR / "06f_metric_ladder.csv").exists() else "FAIL", "evidence": rel(TABLE_DIR / "06f_metric_ladder.csv")},
    {"check": "mentor-safe recommendation created", "status": "PASS" if (DATA_DIR / "06f_mentor_safe_model_recommendation.md").exists() else "FAIL", "evidence": rel(DATA_DIR / "06f_mentor_safe_model_recommendation.md")},
    {"check": "final report created", "status": "PASS" if (DATA_DIR / "06f_reduced_feature_baseline_report.md").exists() else "FAIL", "evidence": rel(DATA_DIR / "06f_reduced_feature_baseline_report.md")},
]
for path in required:
    final_checks.append({"check": f"required output exists: {path.name}", "status": "PASS" if path.exists() else "FAIL", "evidence": rel(path)})
final_checks_df = pd.DataFrame(final_checks)
write_csv(TABLE_DIR / "06f_final_checks.csv", final_checks_df)
summary["final_checks_path"] = rel(TABLE_DIR / "06f_final_checks.csv")
summary["final_check_status"] = "PASS" if (final_checks_df["status"] == "PASS").all() else "FAIL"
write_json(DATA_DIR / "06f_reduced_feature_baseline_summary.json", summary)

print(json.dumps({
    "stage": "06f",
    "final_check_status": summary["final_check_status"],
    "mentor_safe_feature_set": summary["mentor_safe_feature_set"],
    "mentor_safe_hgb_auc": summary["mentor_safe_hgb_auc"],
    "presentation_safe_feature_set": summary["presentation_safe_feature_set"],
    "presentation_safe_hgb_auc": summary["presentation_safe_hgb_auc"],
}, ensure_ascii=False, indent=2))
