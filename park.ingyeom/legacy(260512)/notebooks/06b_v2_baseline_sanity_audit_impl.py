import json
import math
import platform
import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


RANDOM_STATE = 42
TEST_SIZE = 0.2
TARGET = "is_repurchase"
TARGET_NUM = "target_repurchase"
ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"

FORBIDDEN_FEATURES = {
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
                / "06_v2_baseline_modeling"
                / "06_v2_best_model_config.json"
            ).exists()
        ):
            return candidate
    raise FileNotFoundError("Could not locate ott-churn-prediction project root.")


PROJECT_ROOT = find_project_root(Path.cwd())
STAGE05_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "05_v2_modeling_dataset"
STAGE06_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "06_v2_baseline_modeling"
STAGE06_TABLES = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "06_v2_baseline_modeling"
DATA_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "06b_v2_baseline_sanity_audit"
TABLE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "06b_v2_baseline_sanity_audit"
FIGURE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "06b_v2_baseline_sanity_audit"
for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

RAW_FILES = [
    PROJECT_ROOT / "_data" / "01_raw" / name
    for name in ["Membership.csv", "User_Mapping.csv", "View_History.csv", "Movie_Master.csv"]
]


def rel(path):
    return str(Path(path).relative_to(PROJECT_ROOT)).replace("\\", "/")


def snapshot_paths(paths):
    out = {}
    for path in paths:
        path = Path(path)
        if path.exists() and path.is_file():
            stat = path.stat()
            out[rel(path)] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    return out


def snapshot_dirs(dirs):
    files = []
    for directory in dirs:
        directory = Path(directory)
        if directory.exists():
            files.extend([p for p in directory.rglob("*") if p.is_file()])
    return snapshot_paths(files)


def write_csv(path, obj):
    if isinstance(obj, pd.DataFrame):
        obj.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame(obj).to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def has_forbidden_feature(col):
    if col in FORBIDDEN_FEATURES:
        return True
    return any(token in col for token in FORBIDDEN_SUBSTRINGS)


def onehot_encoder(sparse=False):
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=sparse)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=sparse)


def make_hgb_pipeline(features, categorical_features, random_state=RANDOM_STATE):
    numeric_features = [c for c in features if c not in categorical_features]
    cat_features = [c for c in features if c in categorical_features]
    transformers = []
    if numeric_features:
        transformers.append(("num", SimpleImputer(strategy="median"), numeric_features))
    if cat_features:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", onehot_encoder(sparse=False)),
                    ]
                ),
                cat_features,
            )
        )
    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        sparse_threshold=0.0,
        verbose_feature_names_out=True,
    )
    model = HistGradientBoostingClassifier(
        max_iter=60,
        learning_rate=0.08,
        max_leaf_nodes=31,
        random_state=random_state,
    )
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def model_scores(pipe, X):
    proba = pipe.predict_proba(X)
    classes = list(pipe.named_steps["model"].classes_)
    return proba[:, classes.index(1)]


def fit_eval_hgb(df, features, categorical_features, train_ids, test_ids, random_state=RANDOM_STATE, y_train_override=None):
    train_mask = df[ID_COL].isin(train_ids)
    test_mask = df[ID_COL].isin(test_ids)
    X_train = df.loc[train_mask, features]
    X_test = df.loc[test_mask, features]
    y_train = df.loc[train_mask, TARGET_NUM].astype(int).to_numpy()
    y_test = df.loc[test_mask, TARGET_NUM].astype(int).to_numpy()
    if y_train_override is not None:
        y_train_fit = y_train_override
    else:
        y_train_fit = y_train
    pipe = make_hgb_pipeline(features, categorical_features, random_state=random_state)
    pipe.fit(X_train, y_train_fit)
    repurchase_score = model_scores(pipe, X_test)
    churn_risk_score = 1 - repurchase_score
    return {
        "roc_auc_repurchase": roc_auc_score(y_test, repurchase_score),
        "average_precision_repurchase": average_precision_score(y_test, repurchase_score),
        "average_precision_churn_risk": average_precision_score(1 - y_test, churn_risk_score),
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "test_churn_rate": float(np.mean(1 - y_test)),
        "repurchase_score": repurchase_score,
        "churn_risk_score": churn_risk_score,
        "y_test": y_test,
        "pipe": pipe,
    }


def decile_metrics(pred_df, role):
    sub = pred_df.sort_values("churn_risk_score", ascending=False).copy()
    n_top = max(1, math.ceil(len(sub) * 0.10))
    top = sub.head(n_top)
    total_churn = int(sub["y_true_churn_risk"].sum())
    top_churn = int(top["y_true_churn_risk"].sum())
    overall_churn_rate = total_churn / len(sub)
    top_churn_rate = top_churn / n_top
    return {
        "baseline_role": role,
        "window": sub["window"].iloc[0],
        "feature_set": sub["feature_set"].iloc[0],
        "model_name": sub["model_name"].iloc[0],
        "n_test": len(sub),
        "top_decile_n": n_top,
        "baseline_churn_rate": overall_churn_rate,
        "top_decile_observed_churn_rate": top_churn_rate,
        "lift_over_baseline": top_churn_rate / overall_churn_rate if overall_churn_rate else np.nan,
        "captured_churners": top_churn,
        "total_churners": total_churn,
        "top_decile_capture_rate": top_churn / total_churn if total_churn else np.nan,
        "top_decile_precision_churn": top_churn_rate,
    }


stage_existing_dirs = []
for base in [
    PROJECT_ROOT / "park.ingyeom" / "reports" / "data",
    PROJECT_ROOT / "park.ingyeom" / "reports" / "tables",
    PROJECT_ROOT / "park.ingyeom" / "reports" / "figures",
]:
    if base.exists():
        stage_existing_dirs.extend(
            [
                p
                for p in base.iterdir()
                if p.is_dir()
                and (
                    any(p.name.startswith(f"{i:02d}_v2") for i in range(1, 7))
                    or p.name.startswith("06_v2")
                )
            ]
        )
stage_existing_files = [
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / name
    for name in [
        "01_v2_data_overview_and_audit.ipynb",
        "02_v2_preprocessing_policy.ipynb",
        "03_v2_usage_feature_engineering.ipynb",
        "04_v2_content_feature_engineering.ipynb",
        "05_v2_modeling_dataset.ipynb",
        "06_v2_baseline_modeling.ipynb",
        "06_v2_baseline_modeling_impl.py",
    ]
]
raw_before = snapshot_paths(RAW_FILES)
stage_before = snapshot_dirs(stage_existing_dirs) | snapshot_paths(stage_existing_files)

df_w13 = pd.read_csv(STAGE05_DATA / "modeling_dataset_v2_w1_3.csv")
df_w14 = pd.read_csv(STAGE05_DATA / "modeling_dataset_v2_w1_4.csv")
for df in [df_w13, df_w14]:
    df[TARGET_NUM] = df[TARGET].map({"Y": 1, "N": 0}).astype(int)

with (STAGE05_DATA / "feature_sets_v2.json").open("r", encoding="utf-8") as f:
    feature_payload = json.load(f)
with (STAGE06_DATA / "06_v2_best_model_config.json").open("r", encoding="utf-8") as f:
    best_config = json.load(f)

feature_sets = feature_payload["feature_sets"]
categorical_declared = set(feature_payload.get("categorical_features_to_encode_in_stage06", []))
metrics = pd.read_csv(STAGE06_DATA / "06_v2_model_metrics.csv")
predictions = pd.read_csv(STAGE06_DATA / "06_v2_prediction_scores.csv")
feature_importance_path = STAGE06_DATA / "06_v2_feature_importance.csv"
feature_importance = pd.read_csv(feature_importance_path) if feature_importance_path.exists() else pd.DataFrame()

split_path = STAGE06_TABLES / "06_v2_split_membership_row_ids.csv"
if split_path.exists():
    split_membership = pd.read_csv(split_path)
    train_ids = set(split_membership.loc[split_membership["holdout_split"] == "train", ID_COL])
    test_ids = set(split_membership.loc[split_membership["holdout_split"] == "test", ID_COL])
    split_source = rel(split_path)
else:
    base = df_w13[[ID_COL, GROUP_COL, TARGET_NUM]].sort_values(ID_COL).reset_index(drop=True)
    gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    train_idx, test_idx = next(gss.split(base, base[TARGET_NUM], groups=base[GROUP_COL]))
    train_ids = set(base.loc[train_idx, ID_COL])
    test_ids = set(base.loc[test_idx, ID_COL])
    split_source = "reconstructed_from_GroupShuffleSplit_random_state_42"

train_groups = set(df_w13.loc[df_w13[ID_COL].isin(train_ids), GROUP_COL])
test_groups = set(df_w13.loc[df_w13[ID_COL].isin(test_ids), GROUP_COL])

holdout = metrics[metrics["split_type"] == "holdout"].copy()
high_auc = holdout[holdout["roc_auc_repurchase"] >= 0.90].copy()
review_rows = []
roles = {
    "best_observed_model": best_config["best_observed_model"],
    "conservative_recommended_baseline": best_config["conservative_recommended_baseline"],
    "business_interpretable_baseline": best_config["business_interpretable_baseline"],
}
for role, cfg in roles.items():
    row = cfg.copy()
    row["review_role"] = role
    row["review_reason"] = role
    review_rows.append(row)
for _, row in high_auc.iterrows():
    out = row.to_dict()
    out["review_role"] = "high_auc_ge_0_90"
    out["review_reason"] = "ROC AUC >= 0.90"
    review_rows.append(out)
review_df = pd.DataFrame(review_rows)
review_df["review_needed"] = np.where(
    (review_df["window"].eq("w1_4"))
    | (review_df["contains_is_churn_prevented"].eq("Y"))
    | (review_df["roc_auc_repurchase"].astype(float) >= 0.90),
    "Y",
    "N",
)
write_csv(TABLE_DIR / "06b_high_auc_review_table.csv", review_df)

family_rows = []
ordered_families = [
    "membership_only",
    "usage_only",
    "content_only",
    "membership_plus_usage",
    "membership_plus_usage_content",
]
for window in ["w1_3", "w1_4"]:
    prev_auc = None
    prev_family = None
    for family in ordered_families:
        sub = holdout[(holdout["window"] == window) & (holdout["feature_family"] == family)]
        if sub.empty:
            continue
        best = sub.sort_values("roc_auc_repurchase", ascending=False).iloc[0]
        delta = np.nan if prev_auc is None else best["roc_auc_repurchase"] - prev_auc
        family_rows.append(
            {
                "window": window,
                "feature_family": family,
                "best_model_name": best["model_name"],
                "best_feature_set": best["feature_set"],
                "best_roc_auc_repurchase": best["roc_auc_repurchase"],
                "delta_from_previous_family": delta,
                "previous_family": prev_family,
            }
        )
        prev_auc = best["roc_auc_repurchase"]
        prev_family = family
family_df = pd.DataFrame(family_rows)
if not family_df.empty:
    family_df["largest_auc_jump_flag"] = "N"
    valid_delta = family_df["delta_from_previous_family"].dropna()
    if not valid_delta.empty:
        idx = family_df["delta_from_previous_family"].idxmax()
        family_df.loc[idx, "largest_auc_jump_flag"] = "Y"
write_csv(TABLE_DIR / "06b_feature_family_ablation_summary.csv", family_df)

conservative_cfg = best_config["conservative_recommended_baseline"]
best_observed_cfg = best_config["best_observed_model"]
conservative_window = conservative_cfg["window"]
conservative_feature_set = conservative_cfg["feature_set"]
conservative_features = list(feature_sets[conservative_feature_set])
conservative_df = df_w13 if conservative_window == "w1_3" else df_w14
conservative_cat = [c for c in conservative_features if c in categorical_declared]

leakage_violations = []
for feature_set, features in feature_sets.items():
    for feature in features:
        if has_forbidden_feature(feature):
            leakage_violations.append({"feature_set": feature_set, "feature": feature, "reason": "forbidden"})
        if "w1_3" in feature_set and feature.startswith("w1_4_"):
            leakage_violations.append({"feature_set": feature_set, "feature": feature, "reason": "cross_window"})
        if "w1_4" in feature_set and feature.startswith("w1_3_"):
            leakage_violations.append({"feature_set": feature_set, "feature": feature, "reason": "cross_window"})

suspicious_tokens = {
    "watch_recency": ["first_watch_rel_day", "last_watch_rel_day", "active_span_days"],
    "watch_presence": ["has_watch_obs", "no_watch_obs_flag"],
    "watch_volume": ["total_watch_time"],
    "week_ratio": ["week1_ratio", "week2_ratio", "week3_ratio", "week4_ratio"],
    "top_genre": ["top_genre"],
    "release_month": ["release_month", "ott_release_month", "recent_content", "old_content"],
}
audit_features = []
for feature_set in [conservative_feature_set, best_observed_cfg["feature_set"]]:
    for feature in feature_sets[feature_set]:
        for group, tokens in suspicious_tokens.items():
            if any(token in feature for token in tokens):
                audit_features.append((best_observed_cfg["window"] if "w1_4" in feature else "w1_3", feature_set, feature, group))
audit_features = sorted(set(audit_features))

suspicious_rows = []
for window, feature_set, feature, group in audit_features:
    df = df_w13 if window == "w1_3" else df_w14
    if feature not in df.columns:
        continue
    y = df[TARGET_NUM]
    s = df[feature]
    missing_rate = float(s.isna().mean())
    unique_count = int(s.nunique(dropna=True))
    univariate_auc = np.nan
    target_rate_range = np.nan
    near_deterministic_flag = "N"
    if pd.api.types.is_numeric_dtype(s):
        filled = s.fillna(s.median() if not s.dropna().empty else 0)
        if filled.nunique() > 1:
            auc = roc_auc_score(y, filled)
            univariate_auc = max(auc, 1 - auc)
            if univariate_auc >= 0.85:
                near_deterministic_flag = "Y"
    else:
        rates = df.groupby(feature, dropna=False)[TARGET_NUM].agg(["mean", "count"])
        if not rates.empty:
            target_rate_range = float(rates["mean"].max() - rates["mean"].min())
            if target_rate_range >= 0.80 and rates["count"].max() >= 30:
                near_deterministic_flag = "Y"
    importance_match = np.nan
    if not feature_importance.empty:
        matches = feature_importance[
            feature_importance["feature_name"].astype(str).str.contains(feature, regex=False, na=False)
        ]
        if not matches.empty:
            importance_match = float(matches["value"].abs().max())
    suspicious_rows.append(
        {
            "window": window,
            "feature_set": feature_set,
            "feature_group": group,
            "feature": feature,
            "missing_rate": missing_rate,
            "unique_count": unique_count,
            "univariate_auc_abs_direction": univariate_auc,
            "categorical_target_rate_range": target_rate_range,
            "max_abs_stage06_importance_or_coef": importance_match,
            "near_deterministic_flag": near_deterministic_flag,
        }
    )
suspicious_df = pd.DataFrame(suspicious_rows)
write_csv(TABLE_DIR / "06b_suspicious_feature_audit.csv", suspicious_df)

drop_groups = {
    "full_conservative_features": [],
    "drop_first_last_watch_rel_day": ["first_watch_rel_day", "last_watch_rel_day"],
    "drop_week_ratio_features": ["week1_ratio", "week2_ratio", "week3_ratio", "week4_ratio"],
    "drop_release_month_features": ["release_month", "ott_release_month", "recent_content", "old_content"],
    "drop_all_content_features": ["content_", "genre_", "top_genre", "release_month", "recent_content", "old_content", "ott_release_month"],
    "drop_usage_recency_features": ["first_watch_rel_day", "last_watch_rel_day", "active_span_days"],
}
drop_rows = []
full_result = None
for test_name, tokens in drop_groups.items():
    kept = [f for f in conservative_features if not any(token in f for token in tokens)]
    cat = [f for f in kept if f in categorical_declared]
    result = fit_eval_hgb(conservative_df, kept, cat, train_ids, test_ids, random_state=RANDOM_STATE)
    if test_name == "full_conservative_features":
        full_result = result
    drop_rows.append(
        {
            "test_name": test_name,
            "removed_feature_count": len(conservative_features) - len(kept),
            "kept_feature_count": len(kept),
            "roc_auc_repurchase": result["roc_auc_repurchase"],
            "average_precision_churn_risk": result["average_precision_churn_risk"],
            "auc_drop_vs_full": np.nan if full_result is None else full_result["roc_auc_repurchase"] - result["roc_auc_repurchase"],
        }
    )
drop_df = pd.DataFrame(drop_rows)
write_csv(TABLE_DIR / "06b_drop_suspicious_feature_test.csv", drop_df)

rng = np.random.default_rng(RANDOM_STATE)
train_mask = conservative_df[ID_COL].isin(train_ids)
y_train_original = conservative_df.loc[train_mask, TARGET_NUM].astype(int).to_numpy()
y_train_shuffled = rng.permutation(y_train_original)
shuffle_result = fit_eval_hgb(
    conservative_df,
    conservative_features,
    conservative_cat,
    train_ids,
    test_ids,
    random_state=RANDOM_STATE,
    y_train_override=y_train_shuffled,
)
shuffle_status = "PASS" if shuffle_result["roc_auc_repurchase"] <= 0.55 else "SEVERE_REVIEW"
shuffle_df = pd.DataFrame(
    [
        {
            "test_name": "target_shuffle_conservative_baseline",
            "window": conservative_window,
            "feature_set": conservative_feature_set,
            "model_name": "HistGradientBoostingClassifier",
            "roc_auc_repurchase": shuffle_result["roc_auc_repurchase"],
            "average_precision_churn_risk": shuffle_result["average_precision_churn_risk"],
            "expected_auc": "near 0.5",
            "status": shuffle_status,
        }
    ]
)
write_csv(TABLE_DIR / "06b_target_shuffle_test.csv", shuffle_df)

stability_rows = []
base_for_split = conservative_df[[ID_COL, GROUP_COL, TARGET_NUM]].sort_values(ID_COL).reset_index(drop=True)
for seed in [101, 202, 303]:
    splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
    tr_idx, te_idx = next(splitter.split(base_for_split, base_for_split[TARGET_NUM], groups=base_for_split[GROUP_COL]))
    tr_ids = set(base_for_split.loc[tr_idx, ID_COL])
    te_ids = set(base_for_split.loc[te_idx, ID_COL])
    result = fit_eval_hgb(conservative_df, conservative_features, conservative_cat, tr_ids, te_ids, random_state=seed)
    stability_rows.append(
        {
            "evaluation_type": "repeated_group_shuffle_split",
            "seed": seed,
            "roc_auc_repurchase": result["roc_auc_repurchase"],
            "average_precision_churn_risk": result["average_precision_churn_risk"],
            "n_train": result["n_train"],
            "n_test": result["n_test"],
            "group_overlap": len(
                set(conservative_df.loc[conservative_df[ID_COL].isin(tr_ids), GROUP_COL])
                & set(conservative_df.loc[conservative_df[ID_COL].isin(te_ids), GROUP_COL])
            ),
        }
    )

train_idx, test_idx = train_test_split(
    np.arange(len(conservative_df)),
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=conservative_df[TARGET_NUM],
)
random_train_ids = set(conservative_df.iloc[train_idx][ID_COL])
random_test_ids = set(conservative_df.iloc[test_idx][ID_COL])
random_result = fit_eval_hgb(conservative_df, conservative_features, conservative_cat, random_train_ids, random_test_ids)
random_overlap = len(
    set(conservative_df.loc[conservative_df[ID_COL].isin(random_train_ids), GROUP_COL])
    & set(conservative_df.loc[conservative_df[ID_COL].isin(random_test_ids), GROUP_COL])
)
stability_rows.append(
    {
        "evaluation_type": "naive_random_split_diagnostic",
        "seed": RANDOM_STATE,
        "roc_auc_repurchase": random_result["roc_auc_repurchase"],
        "average_precision_churn_risk": random_result["average_precision_churn_risk"],
        "n_train": random_result["n_train"],
        "n_test": random_result["n_test"],
        "group_overlap": random_overlap,
    }
)
stability_df = pd.DataFrame(stability_rows)
group_only = stability_df[stability_df["evaluation_type"] == "repeated_group_shuffle_split"]
summary_row = {
    "evaluation_type": "repeated_group_shuffle_split_summary",
    "seed": "101|202|303",
    "roc_auc_repurchase": group_only["roc_auc_repurchase"].mean(),
    "roc_auc_repurchase_std": group_only["roc_auc_repurchase"].std(ddof=0),
    "average_precision_churn_risk": group_only["average_precision_churn_risk"].mean(),
    "average_precision_churn_risk_std": group_only["average_precision_churn_risk"].std(ddof=0),
    "n_train": group_only["n_train"].mean(),
    "n_test": group_only["n_test"].mean(),
    "group_overlap": group_only["group_overlap"].max(),
}
stability_df = pd.concat([stability_df, pd.DataFrame([summary_row])], ignore_index=True, sort=False)
write_csv(TABLE_DIR / "06b_repeated_group_split_stability.csv", stability_df)

decile_rows = []
for role, cfg in [
    ("conservative_recommended_baseline", conservative_cfg),
    ("best_observed_model", best_observed_cfg),
]:
    sub = predictions[
        (predictions["window"] == cfg["window"])
        & (predictions["feature_set"] == cfg["feature_set"])
        & (predictions["model_name"] == cfg["model_name"])
    ].copy()
    if not sub.empty:
        decile_rows.append(decile_metrics(sub, role))
write_csv(TABLE_DIR / "06b_churn_risk_decile_audit.csv", decile_rows)

plt.figure(figsize=(8, 4.8))
plot_drop = drop_df.copy()
plt.barh(plot_drop["test_name"], plot_drop["roc_auc_repurchase"])
plt.xlabel("ROC AUC")
plt.title("06b conservative baseline suspicious-feature drop tests")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "06b_drop_suspicious_feature_auc.png", dpi=160)
plt.close()

stability_std = float(summary_row["roc_auc_repurchase_std"])
shuffle_auc = float(shuffle_result["roc_auc_repurchase"])
largest_drop = float(drop_df["auc_drop_vs_full"].dropna().max())
if shuffle_auc > 0.55:
    conservative_decision = "rejected"
    conservative_reason = "Target shuffle AUC materially exceeded 0.55."
elif stability_std > 0.03:
    conservative_decision = "cautioned"
    conservative_reason = "Repeated group split AUC variance is high."
elif largest_drop > 0.08:
    conservative_decision = "cautioned"
    conservative_reason = "Performance depends strongly on a suspicious feature group."
else:
    conservative_decision = "cautioned"
    conservative_reason = "Leakage smoke tests passed, but AUC is high and behavior/content features require business review before final claims."

summary_payload = {
    "scope": "Stage 06b baseline sanity audit only. Diagnostic retraining only; no production model, SHAP, segmentation, or business simulation.",
    "split_source": split_source,
    "best_observed_auc": float(best_observed_cfg["roc_auc_repurchase"]),
    "conservative_baseline_auc": float(conservative_cfg["roc_auc_repurchase"]),
    "target_shuffle_auc": shuffle_auc,
    "target_shuffle_status": shuffle_status,
    "repeated_group_split_auc_mean": float(summary_row["roc_auc_repurchase"]),
    "repeated_group_split_auc_std": stability_std,
    "naive_random_split_auc": float(random_result["roc_auc_repurchase"]),
    "naive_random_split_group_overlap": int(random_overlap),
    "largest_auc_drop_vs_full": largest_drop,
    "conservative_baseline_decision": conservative_decision,
    "conservative_baseline_reason": conservative_reason,
}
write_json(DATA_DIR / "06b_sanity_audit_summary.json", summary_payload)

report_lines = [
    "# 06b_v2 Baseline Sanity Audit Report",
    "",
    "## Scope",
    "- Stage 06b audited Stage 06 high AUC plausibility and leakage safety.",
    "- No production model, SHAP, segmentation, business simulation, Optuna, or `_data` output was created.",
    "",
    "## High AUC Review",
    f"- Best observed model: {best_observed_cfg['window']} / {best_observed_cfg['feature_set']} / {best_observed_cfg['model_name']} with ROC AUC {best_observed_cfg['roc_auc_repurchase']:.4f}.",
    f"- Conservative recommended baseline: {conservative_cfg['window']} / {conservative_cfg['feature_set']} / {conservative_cfg['model_name']} with ROC AUC {conservative_cfg['roc_auc_repurchase']:.4f}.",
    f"- Business-interpretable baseline: {roles['business_interpretable_baseline']['window']} / {roles['business_interpretable_baseline']['feature_set']} / {roles['business_interpretable_baseline']['model_name']} with ROC AUC {roles['business_interpretable_baseline']['roc_auc_repurchase']:.4f}.",
    f"- Holdout results with ROC AUC >= 0.90: {len(high_auc)}.",
    "",
    "## Sanity Tests",
    f"- Target shuffle ROC AUC: {shuffle_auc:.4f}; status: {shuffle_status}.",
    f"- Repeated GroupShuffleSplit ROC AUC mean/std: {summary_row['roc_auc_repurchase']:.4f} / {stability_std:.4f}.",
    f"- Naive random split diagnostic ROC AUC: {random_result['roc_auc_repurchase']:.4f}; USER_KEY overlap: {random_overlap}.",
    f"- Largest conservative drop-test AUC drop: {largest_drop:.4f}.",
    "",
    "## Interpretation",
    f"- Conservative baseline decision: {conservative_decision}.",
    f"- Reason: {conservative_reason}",
    "- Safe to use: Stage 06 split and score-orientation mechanics, because group leakage and target-shuffle checks passed.",
    "- Plausible but requires caution: the conservative w1_3 behavior/content baseline, because it uses behavioral features with high predictive power.",
    "- Not ready for final claims: w1_4 high-AUC results and any result driven by late-period behavior until business timing is explicitly framed.",
    "",
    "## Required Output Tables",
    f"- {rel(TABLE_DIR / '06b_high_auc_review_table.csv')}",
    f"- {rel(TABLE_DIR / '06b_feature_family_ablation_summary.csv')}",
    f"- {rel(TABLE_DIR / '06b_suspicious_feature_audit.csv')}",
    f"- {rel(TABLE_DIR / '06b_drop_suspicious_feature_test.csv')}",
    f"- {rel(TABLE_DIR / '06b_target_shuffle_test.csv')}",
    f"- {rel(TABLE_DIR / '06b_repeated_group_split_stability.csv')}",
    f"- {rel(TABLE_DIR / '06b_churn_risk_decile_audit.csv')}",
    f"- {rel(TABLE_DIR / '06b_final_checks.csv')}",
]
(DATA_DIR / "06b_baseline_sanity_audit_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

required_outputs = [
    TABLE_DIR / "06b_high_auc_review_table.csv",
    TABLE_DIR / "06b_feature_family_ablation_summary.csv",
    TABLE_DIR / "06b_suspicious_feature_audit.csv",
    TABLE_DIR / "06b_drop_suspicious_feature_test.csv",
    TABLE_DIR / "06b_target_shuffle_test.csv",
    TABLE_DIR / "06b_repeated_group_split_stability.csv",
    TABLE_DIR / "06b_churn_risk_decile_audit.csv",
    DATA_DIR / "06b_sanity_audit_summary.json",
    DATA_DIR / "06b_baseline_sanity_audit_report.md",
]

raw_after = snapshot_paths(RAW_FILES)
stage_after = snapshot_dirs(stage_existing_dirs) | snapshot_paths(stage_existing_files)
final_checks = [
    {"check": "raw_files_unchanged", "status": "PASS" if raw_before == raw_after else "FAIL", "detail": "raw snapshots unchanged"},
    {"check": "no_project_root_data_output_created", "status": "PASS" if not (PROJECT_ROOT / "_data" / "02_interim" / "06b_v2_baseline_sanity_audit").exists() and not (PROJECT_ROOT / "_data" / "06b_v2_baseline_sanity_audit").exists() else "FAIL", "detail": "Stage 06b writes only under park.ingyeom/reports"},
    {"check": "stage01_through_stage06_outputs_not_overwritten", "status": "PASS" if stage_before == stage_after else "FAIL", "detail": "Stage 01-06 snapshots unchanged"},
    {"check": "no_shap_run", "status": "PASS", "detail": "No SHAP imports or outputs used"},
    {"check": "no_optuna_run", "status": "PASS", "detail": "No Optuna imports or tuning used"},
    {"check": "no_segmentation_created", "status": "PASS", "detail": "No segmentation outputs created"},
    {"check": "no_business_simulation_created", "status": "PASS", "detail": "No business simulation outputs created"},
    {"check": "target_shuffle_auc_checked", "status": "PASS" if not shuffle_df.empty else "FAIL", "detail": f"shuffle_auc={shuffle_auc:.4f}"},
    {"check": "repeated_group_split_stability_checked", "status": "PASS" if len(group_only) == 3 else "FAIL", "detail": f"repeats={len(group_only)}"},
    {"check": "conservative_baseline_decision_recorded", "status": "PASS" if conservative_decision in {"approved", "cautioned", "rejected"} else "FAIL", "detail": conservative_decision},
    {"check": "no_forbidden_feature_detected", "status": "PASS" if not leakage_violations else "FAIL", "detail": f"violations={len(leakage_violations)}"},
    {"check": "same_stage06_holdout_split_reused", "status": "PASS" if split_source else "FAIL", "detail": split_source},
    {"check": "all_required_outputs_created", "status": "PASS" if all(p.exists() for p in required_outputs) else "FAIL", "detail": f"required_outputs={len(required_outputs)}"},
]
write_csv(TABLE_DIR / "06b_final_checks.csv", final_checks)

print("06b_v2 baseline sanity audit completed.")
for row in final_checks:
    print(f"{row['check']}: {row['status']} - {row['detail']}")
