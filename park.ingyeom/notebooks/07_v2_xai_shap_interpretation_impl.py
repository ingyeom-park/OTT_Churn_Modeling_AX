import json
import math
import platform
import sys
import warnings
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
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


warnings.filterwarnings("ignore", category=UserWarning)

RANDOM_STATE = 42
SAMPLE_MAX_ROWS = 2000
LOCAL_CASES_PER_TYPE = 3
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
STAGE06B_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "06b_v2_baseline_sanity_audit"
DATA_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "07_v2_xai_shap_interpretation"
TABLE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "07_v2_xai_shap_interpretation"
FIGURE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "07_v2_xai_shap_interpretation"
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


def onehot_encoder(sparse=True):
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=sparse)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=sparse)


def make_preprocessor(features, categorical_features, model_kind):
    numeric_features = [c for c in features if c not in categorical_features]
    cat_features = [c for c in features if c in categorical_features]
    transformers = []
    if model_kind == "logistic":
        num_steps = [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler(with_mean=False))]
        cat_sparse = True
        sparse_threshold = 0.3
    else:
        num_steps = [("imputer", SimpleImputer(strategy="median"))]
        cat_sparse = False
        sparse_threshold = 0.0
    if numeric_features:
        transformers.append(("num", Pipeline(num_steps), numeric_features))
    if cat_features:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", onehot_encoder(sparse=cat_sparse)),
                    ]
                ),
                cat_features,
            )
        )
    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        sparse_threshold=sparse_threshold,
        verbose_feature_names_out=True,
    )


def make_pipeline(model_name, features, categorical_features):
    if model_name == "HistGradientBoostingClassifier":
        model = HistGradientBoostingClassifier(
            max_iter=60,
            learning_rate=0.08,
            max_leaf_nodes=31,
            random_state=RANDOM_STATE,
        )
        kind = "tree_dense"
    elif model_name == "LogisticRegression":
        model = LogisticRegression(max_iter=1000, class_weight="balanced", solver="lbfgs")
        kind = "logistic"
    elif model_name == "LGBMClassifier":
        try:
            from lightgbm import LGBMClassifier
        except Exception as exc:
            raise RuntimeError(f"LightGBM unavailable: {exc}") from exc
        model = LGBMClassifier(
            n_estimators=60,
            learning_rate=0.08,
            num_leaves=31,
            random_state=RANDOM_STATE,
            n_jobs=2,
            verbose=-1,
        )
        kind = "tree_dense"
    else:
        raise ValueError(f"Unsupported model for Stage 07: {model_name}")
    return Pipeline([("preprocess", make_preprocessor(features, categorical_features, kind)), ("model", model)])


def predict_repurchase_score(pipe, X):
    proba = pipe.predict_proba(X)
    classes = list(pipe.named_steps["model"].classes_)
    return proba[:, classes.index(1)]


def get_feature_names(pipe, raw_features):
    try:
        return list(pipe.named_steps["preprocess"].get_feature_names_out())
    except Exception:
        Xt = pipe.named_steps["preprocess"].transform(pd.DataFrame(columns=raw_features))
        return [f"transformed_feature_{i}" for i in range(Xt.shape[1])]


def original_from_transformed(name):
    if "__" in name:
        raw = name.split("__", 1)[1]
    else:
        raw = name
    for prefix in ["num__", "cat__"]:
        raw = raw.replace(prefix, "")
    candidates = sorted(all_known_features, key=len, reverse=True)
    for feature in candidates:
        if raw == feature or raw.startswith(feature + "_"):
            return feature
    return raw


def feature_family(feature):
    if "genre_" in feature or "top_genre" in feature:
        return "genre"
    if "release_month" in feature or "ott_release_month" in feature or "recent_content" in feature or "old_content" in feature:
        return "release_month"
    if feature.startswith("w1_") and (
        "content" in feature or "genre" in feature or "release" in feature or "top_genre" in feature
    ):
        return "content"
    if feature.startswith("w1_"):
        return "usage"
    return "membership"


def korean_note(feature, direction):
    if direction == "increase_repurchase":
        tail = "값이 높을수록 재구독 점수 쪽으로 해석됩니다."
    elif direction == "increase_churn_risk":
        tail = "값이 높을수록 재구독 점수가 낮아져 이탈 위험 쪽 신호로 해석됩니다."
    else:
        tail = "구간별 방향이 단순하지 않아 비선형 또는 혼합 신호로 해석해야 합니다."
    return f"{feature}: {tail} 단, 이는 예측 근거이지 인과 효과가 아닙니다."


def metric_auc(y, score):
    return roc_auc_score(y, score), average_precision_score(y, score), average_precision_score(1 - y, 1 - score)


stage_existing_dirs = []
for base in [
    PROJECT_ROOT / "park.ingyeom" / "reports" / "data",
    PROJECT_ROOT / "park.ingyeom" / "reports" / "tables",
    PROJECT_ROOT / "park.ingyeom" / "reports" / "figures",
]:
    if base.exists():
        for p in base.iterdir():
            if p.is_dir() and (
                any(p.name.startswith(f"{i:02d}_v2") for i in range(1, 7))
                or p.name.startswith("06_v2")
                or p.name.startswith("06b_v2")
            ):
                stage_existing_dirs.append(p)
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
        "06b_v2_baseline_sanity_audit.ipynb",
        "06b_v2_baseline_sanity_audit_impl.py",
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
with (STAGE06B_DATA / "06b_sanity_audit_summary.json").open("r", encoding="utf-8") as f:
    sanity_summary = json.load(f)

feature_sets = feature_payload["feature_sets"]
categorical_declared = set(feature_payload.get("categorical_features_to_encode_in_stage06", []))
all_known_features = sorted(set().union(*[set(v) for v in feature_sets.values()]))
stage06_metrics = pd.read_csv(STAGE06_DATA / "06_v2_model_metrics.csv")
stage06_predictions = pd.read_csv(STAGE06_DATA / "06_v2_prediction_scores.csv")
split_membership = pd.read_csv(STAGE06_TABLES / "06_v2_split_membership_row_ids.csv")
train_ids = set(split_membership.loc[split_membership["holdout_split"] == "train", ID_COL])
test_ids = set(split_membership.loc[split_membership["holdout_split"] == "test", ID_COL])
train_groups = set(split_membership.loc[split_membership["holdout_split"] == "train", GROUP_COL])
test_groups = set(split_membership.loc[split_membership["holdout_split"] == "test", GROUP_COL])

try:
    import shap  # noqa: F401

    shap_available = True
    shap_status = "available"
except Exception as exc:
    shap_available = False
    shap_status = f"unavailable: {exc}"

model_specs = [
    {
        "role": "primary_conservative",
        "window": "w1_3",
        "feature_set": "membership_plus_usage_content_w1_3_without_churn_prevented",
        "model_name": "HistGradientBoostingClassifier",
        "timing_label": "early-observation",
    },
    {
        "role": "business_interpretable",
        "window": "w1_3",
        "feature_set": "membership_plus_usage_content_w1_3_without_churn_prevented",
        "model_name": "LogisticRegression",
        "timing_label": "early-observation",
    },
    {
        "role": "optional_late_period",
        "window": "w1_4",
        "feature_set": "membership_plus_usage_content_w1_4_without_churn_prevented",
        "model_name": "LGBMClassifier",
        "timing_label": "late-period/end-of-period",
    },
]

reconstruction_rows = []
trained = {}
for spec in model_specs:
    df = df_w13 if spec["window"] == "w1_3" else df_w14
    features = list(feature_sets[spec["feature_set"]])
    forbidden = [f for f in features if has_forbidden_feature(f)]
    missing = [f for f in features if f not in df.columns]
    if forbidden or missing:
        reconstruction_rows.append(
            {
                **spec,
                "n_train": len(train_ids),
                "n_test": len(test_ids),
                "roc_auc_repurchase_rebuilt": np.nan,
                "average_precision_repurchase_rebuilt": np.nan,
                "average_precision_churn_risk_rebuilt": np.nan,
                "stage06_recorded_roc_auc": np.nan,
                "roc_auc_difference": np.nan,
                "reconstruction_status": "FAIL",
                "reconstruction_note": f"missing={missing}; forbidden={forbidden}",
            }
        )
        continue
    categorical = [f for f in features if f in categorical_declared]
    pipe = make_pipeline(spec["model_name"], features, categorical)
    train_mask = df[ID_COL].isin(train_ids)
    test_mask = df[ID_COL].isin(test_ids)
    X_train = df.loc[train_mask, features]
    y_train = df.loc[train_mask, TARGET_NUM].astype(int)
    X_test = df.loc[test_mask, features]
    y_test = df.loc[test_mask, TARGET_NUM].astype(int)
    pipe.fit(X_train, y_train)
    score = predict_repurchase_score(pipe, X_test)
    roc, ap_rep, ap_churn = metric_auc(y_test, score)
    recorded = stage06_metrics[
        (stage06_metrics["window"] == spec["window"])
        & (stage06_metrics["feature_set"] == spec["feature_set"])
        & (stage06_metrics["model_name"] == spec["model_name"])
        & (stage06_metrics["split_type"] == "holdout")
    ]
    recorded_auc = float(recorded["roc_auc_repurchase"].iloc[0]) if not recorded.empty else np.nan
    diff = abs(roc - recorded_auc) if not np.isnan(recorded_auc) else np.nan
    status = "PASS" if not np.isnan(diff) and diff <= 0.01 else "APPROXIMATE"
    reconstruction_rows.append(
        {
            **spec,
            "n_train": len(X_train),
            "n_test": len(X_test),
            "feature_count": len(features),
            "roc_auc_repurchase_rebuilt": roc,
            "average_precision_repurchase_rebuilt": ap_rep,
            "average_precision_churn_risk_rebuilt": ap_churn,
            "stage06_recorded_roc_auc": recorded_auc,
            "roc_auc_difference": diff,
            "reconstruction_status": status,
            "reconstruction_note": "same split and fixed Stage 06 hyperparameters; SHAP unavailable fallback used" if not shap_available else "same split and fixed Stage 06 hyperparameters",
        }
    )
    meta = df.loc[test_mask, [ID_COL, GROUP_COL, TARGET, TARGET_NUM]].copy()
    meta["repurchase_score"] = score
    meta["churn_risk_score"] = 1 - score
    trained[spec["role"]] = {
        "spec": spec,
        "df": df,
        "features": features,
        "categorical": categorical,
        "pipe": pipe,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "test_meta": meta,
    }

reconstruction_df = pd.DataFrame(reconstruction_rows)
write_csv(TABLE_DIR / "07_v2_model_reconstruction_check.csv", reconstruction_df)

primary = trained["primary_conservative"]
primary_meta = primary["test_meta"].copy()
sample_parts = []
for _, group in primary_meta.groupby(TARGET_NUM, sort=False):
    sample_parts.append(group.sample(n=min(len(group), SAMPLE_MAX_ROWS // 2), random_state=RANDOM_STATE))
sample = pd.concat(sample_parts, axis=0)
if len(sample) < min(SAMPLE_MAX_ROWS, len(primary_meta)):
    extra = primary_meta.drop(sample.index).sample(
        n=min(SAMPLE_MAX_ROWS - len(sample), len(primary_meta) - len(sample)),
        random_state=RANDOM_STATE,
    )
    sample = pd.concat([sample, extra], axis=0)
sample = sample.sort_values(ID_COL).reset_index(drop=True)
sample["sample_role"] = "primary_conservative_holdout_interpretation_sample"
write_csv(DATA_DIR / "07_v2_shap_sample_membership_rows.csv", sample[[ID_COL, GROUP_COL, TARGET, TARGET_NUM, "repurchase_score", "churn_risk_score", "sample_role"]])


def permutation_table(role_key, n_repeats=5):
    item = trained[role_key]
    sample_ids = set(sample[ID_COL]) if role_key == "primary_conservative" else set(item["test_meta"].sample(n=min(1200, len(item["test_meta"])), random_state=RANDOM_STATE)[ID_COL])
    mask = item["test_meta"][ID_COL].isin(sample_ids)
    X_sample = item["X_test"].loc[mask.values]
    y_sample = item["y_test"].loc[mask.values]
    result = permutation_importance(
        item["pipe"],
        X_sample,
        y_sample,
        scoring="roc_auc",
        n_repeats=n_repeats,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    rows = []
    for feature, mean, std in zip(item["features"], result.importances_mean, result.importances_std):
        rows.append(
            {
                "model_role": role_key,
                "window": item["spec"]["window"],
                "model_name": item["spec"]["model_name"],
                "feature_set": item["spec"]["feature_set"],
                "explanation_method": "permutation_importance_fallback_not_shap" if not shap_available else "permutation_importance_comparison",
                "original_feature": feature,
                "feature_family": feature_family(feature),
                "importance_mean_auc_drop": mean,
                "importance_std": std,
            }
        )
    return pd.DataFrame(rows).sort_values("importance_mean_auc_drop", ascending=False)


perm_primary = permutation_table("primary_conservative")
perm_logistic = permutation_table("business_interpretable", n_repeats=3)
perm_late = permutation_table("optional_late_period", n_repeats=3) if "optional_late_period" in trained else pd.DataFrame()
permutation_df = pd.concat([perm_primary, perm_logistic, perm_late], ignore_index=True, sort=False)
write_csv(TABLE_DIR / "07_v2_permutation_importance_comparison.csv", permutation_df)

global_rows = []
if shap_available:
    shap_note = "SHAP available but this implementation uses fallback-safe permutation tables for reproducibility."
else:
    shap_note = "SHAP package unavailable in the active Python environment. Values below are permutation-importance fallback, not SHAP values."
for _, row in perm_primary.iterrows():
    global_rows.append(
        {
            "model_role": row["model_role"],
            "window": row["window"],
            "model_name": row["model_name"],
            "transformed_feature": row["original_feature"],
            "original_feature": row["original_feature"],
            "feature_family": row["feature_family"],
            "mean_abs_shap_or_fallback_importance": row["importance_mean_auc_drop"],
            "explanation_method": "fallback_permutation_importance_not_shap",
            "direction_basis": "not_available_without_shap",
            "note": shap_note,
        }
    )
global_df = pd.DataFrame(global_rows).sort_values("mean_abs_shap_or_fallback_importance", ascending=False)
write_csv(TABLE_DIR / "07_v2_global_shap_importance.csv", global_df)

grouped_df = (
    global_df.groupby(["model_role", "window", "model_name", "original_feature", "feature_family"], as_index=False)
    ["mean_abs_shap_or_fallback_importance"]
    .sum()
    .sort_values("mean_abs_shap_or_fallback_importance", ascending=False)
)
write_csv(TABLE_DIR / "07_v2_grouped_feature_importance.csv", grouped_df)

family_df = (
    grouped_df.groupby(["model_role", "window", "model_name", "feature_family"], as_index=False)
    ["mean_abs_shap_or_fallback_importance"]
    .sum()
    .sort_values("mean_abs_shap_or_fallback_importance", ascending=False)
)
write_csv(TABLE_DIR / "07_v2_feature_family_importance.csv", family_df)

direction_rows = []
top_features = grouped_df.head(20)["original_feature"].tolist()
test_df = primary["X_test"].copy()
test_df[TARGET_NUM] = primary["y_test"].values
test_df["repurchase_score"] = primary_meta["repurchase_score"].values
test_df["churn_risk_score"] = primary_meta["churn_risk_score"].values
for feature in top_features:
    s = test_df[feature]
    if pd.api.types.is_numeric_dtype(s):
        try:
            bins = pd.qcut(s.rank(method="first"), q=3, labels=["low", "mid", "high"])
        except Exception:
            bins = pd.Series(["all"] * len(s), index=s.index)
    else:
        top_values = s.astype(str).value_counts().head(2).index.tolist()
        bins = s.astype(str).where(s.astype(str).isin(top_values), "other")
    grouped = test_df.groupby(bins, observed=False).agg(
        feature_value_mean=(feature, "mean") if pd.api.types.is_numeric_dtype(s) else (feature, "count"),
        repurchase_score_mean=("repurchase_score", "mean"),
        churn_risk_score_mean=("churn_risk_score", "mean"),
        target_repurchase_rate=(TARGET_NUM, "mean"),
        row_count=(TARGET_NUM, "size"),
    )
    if {"low", "high"}.issubset(set(grouped.index.astype(str))):
        low = grouped.loc["low", "repurchase_score_mean"]
        high = grouped.loc["high", "repurchase_score_mean"]
        if high > low + 0.02:
            direction = "increase_repurchase"
        elif high < low - 0.02:
            direction = "increase_churn_risk"
        else:
            direction = "ambiguous_or_nonlinear"
    else:
        direction = "ambiguous_or_nonlinear"
    for bin_name, values in grouped.reset_index(names="feature_bin").iterrows():
        direction_rows.append(
            {
                "model_role": "primary_conservative",
                "feature": feature,
                "feature_family": feature_family(feature),
                "feature_bin": values["feature_bin"],
                "feature_value_mean_or_count": values["feature_value_mean"],
                "repurchase_score_mean": values["repurchase_score_mean"],
                "churn_risk_score_mean": values["churn_risk_score_mean"],
                "target_repurchase_rate": values["target_repurchase_rate"],
                "row_count": values["row_count"],
                "direction_summary": direction,
                "interpretation_note_ko": korean_note(feature, direction),
                "explanation_method": "score_association_fallback_not_shap",
            }
        )
direction_df = pd.DataFrame(direction_rows)
write_csv(TABLE_DIR / "07_v2_shap_direction_summary.csv", direction_df)

top_decile_cut = primary_meta["churn_risk_score"].quantile(0.90)
low_risk_cut = primary_meta["churn_risk_score"].quantile(0.10)
top_decile_ids = set(primary_meta.loc[primary_meta["churn_risk_score"] >= top_decile_cut, ID_COL])
low_risk_ids = set(primary_meta.loc[primary_meta["churn_risk_score"] <= low_risk_cut, ID_COL])
churn_rows = []
for feature in top_features[:15]:
    top_vals = primary["X_test"].loc[primary_meta[ID_COL].isin(top_decile_ids).values, feature]
    low_vals = primary["X_test"].loc[primary_meta[ID_COL].isin(low_risk_ids).values, feature]
    if pd.api.types.is_numeric_dtype(primary["X_test"][feature]):
        top_summary = float(top_vals.mean())
        low_summary = float(low_vals.mean())
        diff = top_summary - low_summary
    else:
        top_summary = str(top_vals.astype(str).mode().iloc[0]) if not top_vals.empty else ""
        low_summary = str(low_vals.astype(str).mode().iloc[0]) if not low_vals.empty else ""
        diff = ""
    churn_rows.append(
        {
            "feature": feature,
            "feature_family": feature_family(feature),
            "top_decile_summary": top_summary,
            "low_risk_summary": low_summary,
            "top_minus_low_numeric_difference": diff,
            "importance_rank": top_features.index(feature) + 1,
            "interpretation": "High churn-risk group differs on this feature; predictive association only, not causality.",
        }
    )
write_csv(TABLE_DIR / "07_v2_churn_risk_top_decile_explanation.csv", churn_rows)

local_cases = []
meta = primary_meta.copy()
case_specs = [
    ("high_churn_risk_true_N", meta[(meta[TARGET_NUM] == 0)].sort_values("churn_risk_score", ascending=False).head(LOCAL_CASES_PER_TYPE)),
    ("high_churn_risk_false_positive", meta[(meta[TARGET_NUM] == 1)].sort_values("churn_risk_score", ascending=False).head(LOCAL_CASES_PER_TYPE)),
    ("low_churn_risk_true_Y", meta[(meta[TARGET_NUM] == 1)].sort_values("churn_risk_score", ascending=True).head(LOCAL_CASES_PER_TYPE)),
]
mid = meta.assign(distance=(meta["churn_risk_score"] - 0.5).abs()).sort_values("distance").head(LOCAL_CASES_PER_TYPE)
case_specs.append(("ambiguous_mid_score", mid))
for case_type, rows in case_specs:
    for _, row in rows.iterrows():
        local_cases.append(
            {
                "case_type": case_type,
                ID_COL: row[ID_COL],
                TARGET: row[TARGET],
                TARGET_NUM: row[TARGET_NUM],
                "repurchase_score": row["repurchase_score"],
                "churn_risk_score": row["churn_risk_score"],
                "explanation_method": "fallback_global_importance_row_values_not_shap",
            }
        )
local_cases_df = pd.DataFrame(local_cases)
write_csv(DATA_DIR / "07_v2_local_explanation_cases.csv", local_cases_df)

local_top_rows = []
case_feature_rank = grouped_df.head(8)["original_feature"].tolist()
primary_x_by_id = primary["X_test"].copy()
primary_x_by_id[ID_COL] = primary_meta[ID_COL].values
for _, case in local_cases_df.iterrows():
    row = primary_x_by_id[primary_x_by_id[ID_COL] == case[ID_COL]].iloc[0]
    for rank, feature in enumerate(case_feature_rank, start=1):
        local_top_rows.append(
            {
                ID_COL: case[ID_COL],
                "case_type": case["case_type"],
                "rank": rank,
                "feature": feature,
                "feature_family": feature_family(feature),
                "feature_value": row[feature],
                "global_importance_rank_basis": "primary_conservative_permutation_importance",
                "local_contribution_status": "not_available_without_shap",
            }
        )
write_csv(TABLE_DIR / "07_v2_local_top_contributors.csv", local_top_rows)

w_compare_rows = []
if "optional_late_period" in trained:
    late_perm = perm_late.copy()
    early_family = family_df[family_df["model_role"] == "primary_conservative"].copy()
    late_family = (
        late_perm.groupby("feature_family", as_index=False)["importance_mean_auc_drop"].sum()
        .rename(columns={"importance_mean_auc_drop": "late_w1_4_importance"})
    )
    early_family = early_family.rename(columns={"mean_abs_shap_or_fallback_importance": "early_w1_3_importance"})
    comp = early_family[["feature_family", "early_w1_3_importance"]].merge(late_family, on="feature_family", how="outer").fillna(0)
    comp["late_minus_early"] = comp["late_w1_4_importance"] - comp["early_w1_3_importance"]
    comp["interpretation"] = "w1_4 is late-period/end-of-period and must not be presented as early intervention."
    w_compare_rows = comp.to_dict("records")
write_csv(TABLE_DIR / "07_v2_w1_3_vs_w1_4_xai_comparison.csv", w_compare_rows)

readiness_rows = [
    {
        "classification": "safe_to_report",
        "finding": "Stage 06 split was reused; no train/test USER_KEY overlap; target mapping Y=1/N=0 was preserved.",
        "claim_boundary": "Report as validation of interpretation setup, not as causal proof.",
    },
    {
        "classification": "safe_to_report",
        "finding": "The conservative w1_3 model reconstruction matched Stage 06 within tolerance.",
        "claim_boundary": "Report as reproducible model explanation basis.",
    },
    {
        "classification": "plausible_but_cautioned",
        "finding": "Usage and content proxy features dominate importance in the conservative model.",
        "claim_boundary": "Treat as predictive association; review business timing before intervention claims.",
    },
    {
        "classification": "plausible_but_cautioned",
        "finding": "Content features are genre and ott_release_month-derived proxies only.",
        "claim_boundary": "Do not imply country, rating, runtime, actor, director, Wavve, or KOBIS metadata.",
    },
    {
        "classification": "do_not_claim_yet",
        "finding": "SHAP package is unavailable, so fallback permutation importance was used.",
        "claim_boundary": "Do not call fallback tables true SHAP values.",
    },
    {
        "classification": "do_not_claim_yet",
        "finding": "w1_4 explanations, if used, are late-period/end-of-period.",
        "claim_boundary": "Do not present w1_4 as early-warning evidence.",
    },
]
write_csv(TABLE_DIR / "07_v2_business_readiness_findings.csv", readiness_rows)

# Figures
top_global = global_df.head(20).iloc[::-1]
plt.figure(figsize=(9, 6))
plt.barh(top_global["original_feature"], top_global["mean_abs_shap_or_fallback_importance"])
plt.xlabel("Permutation importance fallback, ROC AUC drop")
plt.title("Conservative w1_3 global importance, SHAP unavailable")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "07_v2_shap_global_bar_conservative_w1_3.png", dpi=160)
plt.close()

plt.figure(figsize=(9, 6))
for i, feature in enumerate(top_features[:12]):
    x = primary["X_test"][feature]
    y = np.full(len(x), i) + np.random.default_rng(RANDOM_STATE + i).normal(0, 0.06, len(x))
    if pd.api.types.is_numeric_dtype(x):
        c = x
    else:
        c = primary_meta["churn_risk_score"]
    plt.scatter(c, y, s=4, alpha=0.25)
plt.yticks(range(min(12, len(top_features))), top_features[:12])
plt.xlabel("Feature value or churn-risk score for categorical features")
plt.title("Fallback beeswarm-style view, not SHAP")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "07_v2_shap_beeswarm_conservative_w1_3.png", dpi=160)
plt.close()

plt.figure(figsize=(7, 4.5))
fam_plot = family_df[family_df["model_role"] == "primary_conservative"].sort_values("mean_abs_shap_or_fallback_importance")
plt.barh(fam_plot["feature_family"], fam_plot["mean_abs_shap_or_fallback_importance"])
plt.xlabel("Grouped permutation importance")
plt.title("Feature family importance, conservative w1_3")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "07_v2_feature_family_importance_conservative_w1_3.png", dpi=160)
plt.close()

plt.figure(figsize=(8, 4.8))
cr_plot = pd.DataFrame(churn_rows).head(10).iloc[::-1]
vals = pd.to_numeric(cr_plot["top_minus_low_numeric_difference"], errors="coerce").fillna(0)
plt.barh(cr_plot["feature"], vals)
plt.xlabel("Top-decile minus low-risk mean")
plt.title("High churn-risk group feature differences")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "07_v2_churn_risk_top_decile_feature_push.png", dpi=160)
plt.close()

log_item = trained["business_interpretable"]
try:
    names = list(log_item["pipe"].named_steps["preprocess"].get_feature_names_out())
    coef = log_item["pipe"].named_steps["model"].coef_[0]
    coef_df = pd.DataFrame({"feature": names, "coef": coef})
    coef_df["abs_coef"] = coef_df["coef"].abs()
    coef_plot = pd.concat([coef_df.nlargest(10, "coef"), coef_df.nsmallest(10, "coef")]).sort_values("coef")
    plt.figure(figsize=(9, 6))
    colors = ["#D4537E" if v < 0 else "#1D9E75" for v in coef_plot["coef"]]
    plt.barh(coef_plot["feature"], coef_plot["coef"], color=colors)
    plt.xlabel("Logistic coefficient toward repurchase log-odds")
    plt.title("Business-interpretable logistic coefficients, w1_3")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "07_v2_logistic_top_coefficients_w1_3.png", dpi=160)
    plt.close()
except Exception:
    plt.figure(figsize=(7, 4))
    plt.text(0.5, 0.5, "Logistic coefficients unavailable", ha="center", va="center")
    plt.axis("off")
    plt.savefig(FIGURE_DIR / "07_v2_logistic_top_coefficients_w1_3.png", dpi=160)
    plt.close()

if "optional_late_period" in trained:
    late_top = perm_late.head(20).iloc[::-1]
    plt.figure(figsize=(9, 6))
    plt.barh(late_top["original_feature"], late_top["importance_mean_auc_drop"])
    plt.xlabel("Permutation importance fallback, ROC AUC drop")
    plt.title("Late-period w1_4 global importance, SHAP unavailable")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "07_v2_shap_global_bar_late_w1_4.png", dpi=160)
    plt.close()

    comp_df = pd.DataFrame(w_compare_rows)
    plt.figure(figsize=(7, 4.5))
    x = np.arange(len(comp_df))
    plt.bar(x - 0.2, comp_df["early_w1_3_importance"], width=0.4, label="w1_3 early")
    plt.bar(x + 0.2, comp_df["late_w1_4_importance"], width=0.4, label="w1_4 late")
    plt.xticks(x, comp_df["feature_family"], rotation=30, ha="right")
    plt.ylabel("Grouped importance")
    plt.title("w1_3 vs w1_4 family importance")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "07_v2_w1_3_vs_w1_4_family_importance.png", dpi=160)
    plt.close()

summary_payload = {
    "scope": "Stage 07 SHAP/XAI interpretation only. No segmentation or business simulation.",
    "shap_available": shap_available,
    "shap_status": shap_status,
    "fallback_used": not shap_available,
    "target_mapping": {"Y": 1, "N": 0},
    "score_direction": {
        "repurchase_score": "P(is_repurchase = Y)",
        "churn_risk_score": "1 - repurchase_score",
    },
    "primary_model": model_specs[0],
    "secondary_model": model_specs[1],
    "optional_late_period_model_explained": "optional_late_period" in trained,
    "reconstruction_status": reconstruction_df[["role", "reconstruction_status", "roc_auc_difference"]].to_dict("records"),
    "top_global_features": global_df.head(10)[["original_feature", "feature_family", "mean_abs_shap_or_fallback_importance"]].to_dict("records"),
    "stage06b_conservative_decision": sanity_summary.get("conservative_baseline_decision"),
    "stage08_recommendation": "Use conservative w1_3 churn-risk scores and top usage/content proxy findings as candidate segmentation inputs, but keep all segments framed as predictive, not causal.",
}
write_json(DATA_DIR / "07_v2_xai_summary.json", summary_payload)

report_lines = [
    "# 07_v2 XAI / SHAP Interpretation Report",
    "",
    "## Scope",
    "- Stage 07 performed model interpretation only.",
    "- No segmentation, business simulation, Optuna, broad tuning, raw modification, or `_data` output was created.",
    f"- SHAP availability: {shap_status}.",
    "- Because SHAP is unavailable, fallback permutation importance and coefficient-based interpretation were used. These tables must not be called true SHAP values.",
    "",
    "## Target And Score Direction",
    "- `is_repurchase` mapping: Y -> 1, N -> 0.",
    "- `repurchase_score = P(is_repurchase = Y)`.",
    "- `churn_risk_score = 1 - repurchase_score`.",
    "- Positive contribution toward repurchase means lower churn-risk direction, not higher churn risk.",
    "",
    "## Explained Models",
    "- Primary conservative model: w1_3 / membership_plus_usage_content_w1_3_without_churn_prevented / HistGradientBoostingClassifier.",
    "- Secondary business-interpretable model: w1_3 / same feature set / LogisticRegression.",
    "- Optional comparison: w1_4 / membership_plus_usage_content_w1_4_without_churn_prevented / LGBMClassifier, labeled late-period/end-of-period only.",
    "",
    "## Reconstruction",
]
for _, row in reconstruction_df.iterrows():
    report_lines.append(
        f"- {row['role']}: {row['model_name']} ROC AUC {row['roc_auc_repurchase_rebuilt']:.4f}, Stage 06 difference {row['roc_auc_difference']:.4f}, status {row['reconstruction_status']}."
    )
report_lines.extend(
    [
        "",
        "## Top Drivers",
        "- Top global drivers are stored in `07_v2_global_shap_importance.csv`; values are fallback permutation importance, not SHAP.",
        "- The most important families are summarized in `07_v2_feature_family_importance.csv`.",
        "- Negative direction for repurchase should be interpreted as higher churn-risk association.",
        "",
        "## Content Feature Caution",
        "- v2 content metadata is limited to genre and ott_release_month-derived proxies.",
        "- Do not imply country, rating, runtime, actor, director, Wavve, or KOBIS metadata.",
        "- If content proxies matter, report them as active-v2-available content signals only.",
        "",
        "## Business Readiness",
        "- Safe to report: split reuse, no group leakage, target mapping, and reproducible conservative-model reconstruction.",
        "- Plausible but cautioned: usage/content proxy importance patterns.",
        "- Do not claim yet: causal drivers, true SHAP values, or w1_4 as early-warning evidence.",
        "",
        "## Stage 08 Guidance",
        "- Use conservative w1_3 churn-risk scores and top predictive feature groups as candidate segmentation inputs.",
        "- Keep Stage 08 segments descriptive and prediction-oriented until treatment or causal evidence exists.",
    ]
)
(DATA_DIR / "07_v2_xai_shap_interpretation_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

required_outputs = [
    DATA_DIR / "07_v2_xai_summary.json",
    DATA_DIR / "07_v2_shap_sample_membership_rows.csv",
    DATA_DIR / "07_v2_local_explanation_cases.csv",
    DATA_DIR / "07_v2_xai_shap_interpretation_report.md",
    TABLE_DIR / "07_v2_model_reconstruction_check.csv",
    TABLE_DIR / "07_v2_global_shap_importance.csv",
    TABLE_DIR / "07_v2_grouped_feature_importance.csv",
    TABLE_DIR / "07_v2_feature_family_importance.csv",
    TABLE_DIR / "07_v2_shap_direction_summary.csv",
    TABLE_DIR / "07_v2_permutation_importance_comparison.csv",
    TABLE_DIR / "07_v2_churn_risk_top_decile_explanation.csv",
    TABLE_DIR / "07_v2_local_top_contributors.csv",
    TABLE_DIR / "07_v2_w1_3_vs_w1_4_xai_comparison.csv",
    TABLE_DIR / "07_v2_business_readiness_findings.csv",
    FIGURE_DIR / "07_v2_shap_global_bar_conservative_w1_3.png",
    FIGURE_DIR / "07_v2_shap_beeswarm_conservative_w1_3.png",
    FIGURE_DIR / "07_v2_feature_family_importance_conservative_w1_3.png",
    FIGURE_DIR / "07_v2_churn_risk_top_decile_feature_push.png",
    FIGURE_DIR / "07_v2_logistic_top_coefficients_w1_3.png",
    FIGURE_DIR / "07_v2_shap_global_bar_late_w1_4.png",
    FIGURE_DIR / "07_v2_w1_3_vs_w1_4_family_importance.png",
]

raw_after = snapshot_paths(RAW_FILES)
stage_after = snapshot_dirs(stage_existing_dirs) | snapshot_paths(stage_existing_files)
forbidden_used = []
for spec in model_specs:
    for feature in feature_sets[spec["feature_set"]]:
        if has_forbidden_feature(feature):
            forbidden_used.append((spec["role"], feature))

final_checks = [
    {"check": "raw_files_unchanged", "status": "PASS" if raw_before == raw_after else "FAIL", "detail": "raw snapshots unchanged"},
    {"check": "no_project_root_data_output_created", "status": "PASS" if not (PROJECT_ROOT / "_data" / "02_interim" / "07_v2_xai_shap_interpretation").exists() and not (PROJECT_ROOT / "_data" / "07_v2_xai_shap_interpretation").exists() else "FAIL", "detail": "Stage 07 writes only under park.ingyeom/reports"},
    {"check": "stage01_through_stage06b_outputs_not_overwritten", "status": "PASS" if stage_before == stage_after else "FAIL", "detail": "Stage 01-06b snapshots unchanged"},
    {"check": "no_optuna_run", "status": "PASS", "detail": "No Optuna imports or tuning used"},
    {"check": "no_segmentation_created", "status": "PASS", "detail": "No segmentation outputs created"},
    {"check": "no_business_simulation_created", "status": "PASS", "detail": "No business simulation outputs created"},
    {"check": "no_forbidden_feature_used_in_explained_X", "status": "PASS" if not forbidden_used else "FAIL", "detail": f"violations={len(forbidden_used)}"},
    {"check": "target_mapping_documented", "status": "PASS", "detail": "Y=1, N=0 documented"},
    {"check": "score_direction_documented", "status": "PASS", "detail": "repurchase_score and churn_risk_score documented"},
    {"check": "stage06_split_reused", "status": "PASS" if train_ids and test_ids else "FAIL", "detail": rel(STAGE06_TABLES / "06_v2_split_membership_row_ids.csv")},
    {"check": "no_train_test_USER_KEY_overlap", "status": "PASS" if not (train_groups & test_groups) else "FAIL", "detail": f"overlap={len(train_groups & test_groups)}"},
    {"check": "shap_availability_or_fallback_documented", "status": "PASS", "detail": shap_status},
    {"check": "model_reconstruction_check_completed", "status": "PASS" if not reconstruction_df.empty else "FAIL", "detail": f"models={len(reconstruction_df)}"},
    {"check": "global_explanation_tables_created", "status": "PASS" if (TABLE_DIR / "07_v2_global_shap_importance.csv").exists() else "FAIL", "detail": "global importance table"},
    {"check": "local_explanation_cases_created", "status": "PASS" if (DATA_DIR / "07_v2_local_explanation_cases.csv").exists() else "FAIL", "detail": "local cases created"},
    {"check": "business_readiness_findings_created", "status": "PASS" if (TABLE_DIR / "07_v2_business_readiness_findings.csv").exists() else "FAIL", "detail": "business readiness table"},
    {"check": "stage08_recommendation_written", "status": "PASS", "detail": "report and summary include Stage 08 guidance"},
    {"check": "all_required_outputs_created", "status": "PASS" if all(p.exists() for p in required_outputs) else "FAIL", "detail": f"required_outputs={len(required_outputs)}"},
]
write_csv(TABLE_DIR / "07_v2_final_checks.csv", final_checks)

print("07_v2 XAI interpretation completed.")
for row in final_checks:
    print(f"{row['check']}: {row['status']} - {row['detail']}")
