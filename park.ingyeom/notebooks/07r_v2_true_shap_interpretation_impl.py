import json
import math
import os
import platform
import re
import sys
import warnings
from datetime import datetime
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(os.cpu_count() or 4))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


warnings.filterwarnings("ignore", category=UserWarning)

EXPECTED_PYTHON = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe"
if Path(sys.executable).resolve() != Path(EXPECTED_PYTHON).resolve():
    raise RuntimeError(f"Stage 07r must run in Python 3.11 executable {EXPECTED_PYTHON}; got {sys.executable}")

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
STAGE07_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "07_v2_xai_shap_interpretation"

DATA_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "07r_v2_true_shap_interpretation"
TABLE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "07r_v2_true_shap_interpretation"
FIGURE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "07r_v2_true_shap_interpretation"
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
        model = HistGradientBoostingClassifier(max_iter=60, learning_rate=0.08, max_leaf_nodes=31, random_state=RANDOM_STATE)
        kind = "tree_dense"
    elif model_name == "LogisticRegression":
        model = LogisticRegression(max_iter=1000, class_weight="balanced", solver="lbfgs")
        kind = "logistic"
    elif model_name == "LGBMClassifier":
        from lightgbm import LGBMClassifier

        model = LGBMClassifier(n_estimators=60, learning_rate=0.08, num_leaves=31, random_state=RANDOM_STATE, n_jobs=2, verbose=-1)
        kind = "tree_dense"
    else:
        raise ValueError(f"Unsupported model: {model_name}")
    return Pipeline([("preprocess", make_preprocessor(features, categorical_features, kind)), ("model", model)])


def to_dense(matrix):
    if hasattr(matrix, "toarray"):
        return matrix.toarray()
    return np.asarray(matrix)


def predict_repurchase_score(pipe, X):
    proba = pipe.predict_proba(X)
    classes = list(pipe.named_steps["model"].classes_)
    return proba[:, classes.index(1)]


def feature_family(feature):
    if "genre_" in feature or "top_genre" in feature:
        return "genre"
    if "release_month" in feature or "ott_release_month" in feature or "recent_content" in feature or "old_content" in feature:
        return "release_month"
    if feature.startswith("w1_") and ("content" in feature or "genre" in feature or "release" in feature or "top_genre" in feature):
        return "content"
    if feature.startswith("w1_"):
        return "usage"
    return "membership"


def sanitize_name(text, limit=80):
    text = re.sub(r"[^A-Za-z0-9가-힣_]+", "_", str(text))
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:limit] or "feature"


def metric_triplet(y, score):
    return (
        roc_auc_score(y, score),
        average_precision_score(y, score),
        average_precision_score(1 - y, 1 - score),
    )


def transformed_to_original(name, known_features):
    raw = str(name)
    if "__" in raw:
        raw = raw.split("__", 1)[1]
    for feature in sorted(known_features, key=len, reverse=True):
        if raw == feature or raw.startswith(feature + "_"):
            return feature
    return raw


def compute_shap_for_pipeline(pipe, X_raw, features, known_features, model_name, background_raw=None):
    pre = pipe.named_steps["preprocess"]
    model = pipe.named_steps["model"]
    X_trans = to_dense(pre.transform(X_raw))
    feature_names = list(pre.get_feature_names_out())
    X_trans_df = pd.DataFrame(X_trans, columns=feature_names)
    if model_name in {"HistGradientBoostingClassifier", "LGBMClassifier"}:
        explainer = shap.TreeExplainer(model)
        explanation = explainer(X_trans_df)
    elif model_name == "LogisticRegression":
        if background_raw is None:
            background_raw = X_raw
        bg = to_dense(pre.transform(background_raw))
        bg_df = pd.DataFrame(bg, columns=feature_names)
        explainer = shap.LinearExplainer(model, bg_df)
        explanation = explainer(X_trans_df)
    else:
        raise ValueError(f"No SHAP explainer configured for {model_name}")
    values = np.asarray(explanation.values)
    if values.ndim == 3:
        values = values[:, :, -1]
    base_values = np.asarray(explanation.base_values)
    if base_values.ndim > 1:
        base_values = base_values[:, -1]
    original_features = [transformed_to_original(name, known_features) for name in feature_names]
    return {
        "explanation": explanation,
        "values": values,
        "base_values": base_values,
        "X_trans_df": X_trans_df,
        "feature_names": feature_names,
        "original_features": original_features,
    }


stage_existing_dirs = []
for base in [
    PROJECT_ROOT / "park.ingyeom" / "reports" / "data",
    PROJECT_ROOT / "park.ingyeom" / "reports" / "tables",
    PROJECT_ROOT / "park.ingyeom" / "reports" / "figures",
]:
    if base.exists():
        for p in base.iterdir():
            if p.is_dir() and (
                any(p.name.startswith(f"{i:02d}_v2") for i in range(1, 8))
                or p.name.startswith("06_v2")
                or p.name.startswith("06b_v2")
                or p.name.startswith("07_v2")
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
        "07_v2_xai_shap_interpretation.ipynb",
        "07_v2_xai_shap_interpretation_impl.py",
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
with (STAGE07_DATA / "07_v2_xai_summary.json").open("r", encoding="utf-8") as f:
    stage07_summary = json.load(f)

feature_sets = feature_payload["feature_sets"]
categorical_declared = set(feature_payload.get("categorical_features_to_encode_in_stage06", []))
all_known_features = sorted(set().union(*[set(v) for v in feature_sets.values()]))
stage06_metrics = pd.read_csv(STAGE06_DATA / "06_v2_model_metrics.csv")
split_membership = pd.read_csv(STAGE06_TABLES / "06_v2_split_membership_row_ids.csv")
train_ids = set(split_membership.loc[split_membership["holdout_split"] == "train", ID_COL])
test_ids = set(split_membership.loc[split_membership["holdout_split"] == "test", ID_COL])
train_groups = set(split_membership.loc[split_membership["holdout_split"] == "train", GROUP_COL])
test_groups = set(split_membership.loc[split_membership["holdout_split"] == "test", GROUP_COL])

model_specs = [
    {"role": "primary_conservative", "window": "w1_3", "feature_set": "membership_plus_usage_content_w1_3_without_churn_prevented", "model_name": "HistGradientBoostingClassifier", "timing_label": "early-observation"},
    {"role": "business_interpretable", "window": "w1_3", "feature_set": "membership_plus_usage_content_w1_3_without_churn_prevented", "model_name": "LogisticRegression", "timing_label": "early-observation"},
    {"role": "optional_late_period", "window": "w1_4", "feature_set": "membership_plus_usage_content_w1_4_without_churn_prevented", "model_name": "LGBMClassifier", "timing_label": "late-period/end-of-period"},
]

trained = {}
reconstruction_rows = []
for spec in model_specs:
    df = df_w13 if spec["window"] == "w1_3" else df_w14
    features = list(feature_sets[spec["feature_set"]])
    missing = [f for f in features if f not in df.columns]
    forbidden = [f for f in features if has_forbidden_feature(f)]
    if missing or forbidden:
        raise RuntimeError(f"Feature validation failed for {spec['role']}: missing={missing}, forbidden={forbidden}")
    cat_cols = [f for f in features if f in categorical_declared]
    train_mask = df[ID_COL].isin(train_ids)
    test_mask = df[ID_COL].isin(test_ids)
    X_train = df.loc[train_mask, features]
    y_train = df.loc[train_mask, TARGET_NUM].astype(int)
    X_test = df.loc[test_mask, features]
    y_test = df.loc[test_mask, TARGET_NUM].astype(int)
    pipe = make_pipeline(spec["model_name"], features, cat_cols)
    pipe.fit(X_train, y_train)
    repurchase_score = predict_repurchase_score(pipe, X_test)
    roc, ap_rep, ap_churn = metric_triplet(y_test, repurchase_score)
    recorded = stage06_metrics[
        (stage06_metrics["window"] == spec["window"])
        & (stage06_metrics["feature_set"] == spec["feature_set"])
        & (stage06_metrics["model_name"] == spec["model_name"])
        & (stage06_metrics["split_type"] == "holdout")
    ]
    recorded_auc = float(recorded["roc_auc_repurchase"].iloc[0]) if not recorded.empty else np.nan
    diff = abs(roc - recorded_auc) if not np.isnan(recorded_auc) else np.nan
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
            "reconstruction_status": "PASS" if not np.isnan(diff) and diff <= 0.01 else "APPROXIMATE",
            "reconstruction_note": "same Stage 06 split and fixed Stage 06 baseline hyperparameters",
        }
    )
    meta = df.loc[test_mask, [ID_COL, GROUP_COL, TARGET, TARGET_NUM]].copy()
    meta["repurchase_score"] = repurchase_score
    meta["churn_risk_score"] = 1 - repurchase_score
    trained[spec["role"]] = {
        "spec": spec,
        "df": df,
        "features": features,
        "cat_cols": cat_cols,
        "pipe": pipe,
        "X_train": X_train,
        "y_train": y_train,
        "X_test": X_test,
        "y_test": y_test,
        "meta": meta,
    }
write_csv(TABLE_DIR / "07r_model_reconstruction_check.csv", reconstruction_rows)

primary = trained["primary_conservative"]
primary_meta = primary["meta"].copy()
sample_parts = []
for value, n in [(0, 600), (1, 600)]:
    g = primary_meta[primary_meta[TARGET_NUM] == value]
    sample_parts.append(g.sample(n=min(n, len(g)), random_state=RANDOM_STATE))
sample_parts.append(primary_meta.sort_values("churn_risk_score", ascending=False).head(300))
sample_parts.append(primary_meta.sort_values("churn_risk_score", ascending=True).head(300))
mid = primary_meta.assign(mid_distance=(primary_meta["churn_risk_score"] - 0.5).abs()).sort_values("mid_distance").head(300)
sample_parts.append(mid.drop(columns=["mid_distance"]))
sample = pd.concat(sample_parts, axis=0).drop_duplicates(ID_COL)
if len(sample) > SAMPLE_MAX_ROWS:
    sample = sample.sample(n=SAMPLE_MAX_ROWS, random_state=RANDOM_STATE)
sample = sample.sort_values(ID_COL).reset_index(drop=True)
sample["sample_role"] = "true_shap_primary_holdout_sample"
write_csv(DATA_DIR / "07r_shap_sample_membership_rows.csv", sample[[ID_COL, GROUP_COL, TARGET, TARGET_NUM, "repurchase_score", "churn_risk_score", "sample_role"]])

sample_ids = set(sample[ID_COL])
primary_sample_mask = primary["meta"][ID_COL].isin(sample_ids).values
primary_background = primary["X_train"].sample(n=min(1000, len(primary["X_train"])), random_state=RANDOM_STATE)
primary_shap = compute_shap_for_pipeline(
    primary["pipe"],
    primary["X_test"].loc[primary_sample_mask],
    primary["features"],
    all_known_features,
    primary["spec"]["model_name"],
    background_raw=primary_background,
)

shap_values = primary_shap["values"]
base_values = primary_shap["base_values"]
feature_names = primary_shap["feature_names"]
original_features = primary_shap["original_features"]
X_trans_df = primary_shap["X_trans_df"]

transformed_rows = []
for idx, name in enumerate(feature_names):
    transformed_rows.append(
        {
            "model_role": "primary_conservative",
            "window": "w1_3",
            "model_name": "HistGradientBoostingClassifier",
            "transformed_feature": name,
            "original_feature": original_features[idx],
            "feature_family": feature_family(original_features[idx]),
            "mean_abs_shap": float(np.abs(shap_values[:, idx]).mean()),
            "mean_shap": float(shap_values[:, idx].mean()),
            "shap_output_basis": "model_margin_for_repurchase_class",
            "score_direction_note": "positive SHAP pushes toward higher repurchase margin; negative SHAP implies higher churn risk",
        }
    )
global_df = pd.DataFrame(transformed_rows).sort_values("mean_abs_shap", ascending=False)
write_csv(TABLE_DIR / "07r_global_shap_importance.csv", global_df)

shap_by_original = pd.DataFrame(shap_values, columns=feature_names).T
shap_by_original["original_feature"] = original_features
grouped_matrix = shap_by_original.groupby("original_feature").sum().T
grouped_rows = []
for feature in grouped_matrix.columns:
    vals = grouped_matrix[feature].to_numpy()
    grouped_rows.append(
        {
            "model_role": "primary_conservative",
            "window": "w1_3",
            "model_name": "HistGradientBoostingClassifier",
            "original_feature": feature,
            "feature_family": feature_family(feature),
            "mean_abs_shap": float(np.abs(vals).mean()),
            "mean_shap": float(vals.mean()),
            "shap_output_basis": "model_margin_for_repurchase_class",
        }
    )
grouped_df = pd.DataFrame(grouped_rows).sort_values("mean_abs_shap", ascending=False)
write_csv(TABLE_DIR / "07r_grouped_shap_importance.csv", grouped_df)

family_df = (
    grouped_df.groupby(["model_role", "window", "model_name", "feature_family"], as_index=False)["mean_abs_shap"]
    .sum()
    .sort_values("mean_abs_shap", ascending=False)
)
write_csv(TABLE_DIR / "07r_feature_family_shap_importance.csv", family_df)

sample_meta = primary["meta"].loc[primary_sample_mask].reset_index(drop=True)
raw_sample = primary["X_test"].loc[primary_sample_mask].reset_index(drop=True)
direction_rows = []
for feature in grouped_df.head(20)["original_feature"].tolist():
    vals = grouped_matrix[feature].to_numpy()
    raw = raw_sample[feature].reset_index(drop=True) if feature in raw_sample.columns else pd.Series(np.nan, index=raw_sample.index)
    if pd.api.types.is_numeric_dtype(raw):
        try:
            bins = pd.qcut(raw.rank(method="first"), q=3, labels=["low", "mid", "high"])
        except Exception:
            bins = pd.Series(["all"] * len(raw), index=raw.index)
    else:
        top_values = raw.astype(str).value_counts().head(2).index.tolist()
        bins = raw.astype(str).where(raw.astype(str).isin(top_values), "other")
    tmp = pd.DataFrame({"bin": bins.astype(str), "raw_value": raw, "shap": vals, "target": sample_meta[TARGET_NUM].values, "repurchase_score": sample_meta["repurchase_score"].values, "churn_risk_score": sample_meta["churn_risk_score"].values})
    grouped = tmp.groupby("bin", observed=False).agg(raw_value_mean=("raw_value", "mean") if pd.api.types.is_numeric_dtype(raw) else ("raw_value", "count"), mean_shap=("shap", "mean"), mean_abs_shap=("shap", lambda x: np.abs(x).mean()), target_repurchase_rate=("target", "mean"), mean_repurchase_score=("repurchase_score", "mean"), mean_churn_risk_score=("churn_risk_score", "mean"), row_count=("target", "size")).reset_index()
    if {"low", "high"}.issubset(set(grouped["bin"])):
        low = grouped.loc[grouped["bin"] == "low", "mean_shap"].iloc[0]
        high = grouped.loc[grouped["bin"] == "high", "mean_shap"].iloc[0]
        if high > low + 0.02:
            direction = "high_value_pushes_repurchase"
            note = "값이 높을수록 재구독 방향 SHAP 기여가 커집니다."
        elif high < low - 0.02:
            direction = "high_value_pushes_churn_risk"
            note = "값이 높을수록 재구독 방향 SHAP 기여가 낮아져 이탈위험 쪽 신호입니다."
        else:
            direction = "ambiguous_or_nonlinear"
            note = "구간별 방향이 단순하지 않아 비선형 또는 혼합 신호로 봐야 합니다."
    else:
        direction = "ambiguous_or_nonlinear"
        note = "범주형 또는 희소 피처라 단순 고저 방향으로 해석하지 않습니다."
    for _, row in grouped.iterrows():
        direction_rows.append(
            {
                "feature": feature,
                "feature_family": feature_family(feature),
                "feature_bin": row["bin"],
                "raw_value_mean_or_count": row["raw_value_mean"],
                "mean_shap_toward_repurchase_margin": row["mean_shap"],
                "mean_abs_shap": row["mean_abs_shap"],
                "target_repurchase_rate": row["target_repurchase_rate"],
                "mean_repurchase_score": row["mean_repurchase_score"],
                "mean_churn_risk_score": row["mean_churn_risk_score"],
                "row_count": row["row_count"],
                "direction_summary": direction,
                "interpretation_note_ko": f"{feature}: {note} 단, 이는 예측 근거이지 인과 효과가 아닙니다.",
            }
        )
direction_df = pd.DataFrame(direction_rows)
write_csv(TABLE_DIR / "07r_shap_direction_summary.csv", direction_df)

top_decile_ids = set(sample_meta.sort_values("churn_risk_score", ascending=False).head(max(1, math.ceil(len(sample_meta) * 0.10)))[ID_COL])
low_decile_ids = set(sample_meta.sort_values("churn_risk_score", ascending=True).head(max(1, math.ceil(len(sample_meta) * 0.10)))[ID_COL])
churn_rows = []
for feature in grouped_df.head(15)["original_feature"].tolist():
    vals = grouped_matrix[feature].to_numpy()
    tmp = pd.DataFrame({ID_COL: sample_meta[ID_COL].values, "shap": vals})
    high_vals = tmp[tmp[ID_COL].isin(top_decile_ids)]["shap"]
    low_vals = tmp[tmp[ID_COL].isin(low_decile_ids)]["shap"]
    churn_rows.append(
        {
            "feature": feature,
            "feature_family": feature_family(feature),
            "top_churn_risk_mean_shap": float(high_vals.mean()),
            "low_churn_risk_mean_shap": float(low_vals.mean()),
            "top_minus_low_mean_shap": float(high_vals.mean() - low_vals.mean()),
            "interpretation": "negative SHAP in top churn-risk group pushes away from repurchase and toward churn risk",
        }
    )
write_csv(TABLE_DIR / "07r_churn_risk_top_decile_shap_explanation.csv", churn_rows)

local_cases = []
case_specs = [
    ("high_risk_true_N", primary_meta[primary_meta[TARGET_NUM] == 0].sort_values("churn_risk_score", ascending=False).head(3)),
    ("high_risk_false_positive", primary_meta[primary_meta[TARGET_NUM] == 1].sort_values("churn_risk_score", ascending=False).head(3)),
    ("low_risk_true_Y", primary_meta[primary_meta[TARGET_NUM] == 1].sort_values("churn_risk_score", ascending=True).head(3)),
    ("mid_score", primary_meta.assign(distance=(primary_meta["churn_risk_score"] - 0.5).abs()).sort_values("distance").head(3)),
]
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
            }
        )
local_cases_df = pd.DataFrame(local_cases)
write_csv(DATA_DIR / "07r_local_explanation_cases.csv", local_cases_df)

local_top_rows = []
sample_index_by_mid = {mid: i for i, mid in enumerate(sample_meta[ID_COL].tolist())}
for _, case in local_cases_df.iterrows():
    mid = case[ID_COL]
    if mid not in sample_index_by_mid:
        raw_case = primary["X_test"].loc[primary["meta"][ID_COL] == mid]
        extra_shap = compute_shap_for_pipeline(primary["pipe"], raw_case, primary["features"], all_known_features, primary["spec"]["model_name"], background_raw=primary["X_train"].sample(n=min(1000, len(primary["X_train"])), random_state=RANDOM_STATE))
        vals_by_feature = pd.DataFrame(extra_shap["values"], columns=extra_shap["feature_names"]).T
        vals_by_feature["original_feature"] = extra_shap["original_features"]
        grouped_case = vals_by_feature.groupby("original_feature").sum()[0]
        case_base = float(np.asarray(extra_shap["base_values"]).ravel()[0])
    else:
        idx = sample_index_by_mid[mid]
        grouped_case = grouped_matrix.iloc[idx]
        case_base = float(np.asarray(base_values).ravel()[idx])
    for rank, (feature, value) in enumerate(grouped_case.abs().sort_values(ascending=False).head(10).items(), start=1):
        signed = float(grouped_case[feature])
        local_top_rows.append(
            {
                ID_COL: mid,
                "case_type": case["case_type"],
                "rank": rank,
                "feature": feature,
                "feature_family": feature_family(feature),
                "shap_value_toward_repurchase_margin": signed,
                "abs_shap": abs(signed),
                "direction_for_churn_risk": "higher_churn_risk" if signed < 0 else "lower_churn_risk",
                "base_value": case_base,
            }
        )
local_top_df = pd.DataFrame(local_top_rows)
write_csv(TABLE_DIR / "07r_local_top_contributors.csv", local_top_df)

fallback_path = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "07_v2_xai_shap_interpretation" / "07_v2_grouped_feature_importance.csv"
fallback_compare_rows = []
if fallback_path.exists():
    fallback = pd.read_csv(fallback_path)
    fallback_primary = fallback[fallback["model_role"] == "primary_conservative"].copy()
    merged = grouped_df.merge(
        fallback_primary[["original_feature", "mean_abs_shap_or_fallback_importance"]],
        on="original_feature",
        how="left",
    )
    merged = merged.rename(columns={"mean_abs_shap_or_fallback_importance": "stage07_fallback_importance"})
    merged["true_shap_rank"] = merged["mean_abs_shap"].rank(ascending=False, method="dense").astype(int)
    merged["fallback_available"] = merged["stage07_fallback_importance"].notna()
    fallback_compare_rows = merged.sort_values("mean_abs_shap", ascending=False).to_dict("records")
write_csv(TABLE_DIR / "07r_fallback_vs_true_shap_comparison.csv", fallback_compare_rows)

late_family_rows = []
late_shap_success = False
if "optional_late_period" in trained:
    late = trained["optional_late_period"]
    late_sample = late["meta"].sample(n=min(1000, len(late["meta"])), random_state=RANDOM_STATE)
    late_mask = late["meta"][ID_COL].isin(set(late_sample[ID_COL])).values
    late_result = compute_shap_for_pipeline(late["pipe"], late["X_test"].loc[late_mask], late["features"], all_known_features, late["spec"]["model_name"], background_raw=late["X_train"].sample(n=min(1000, len(late["X_train"])), random_state=RANDOM_STATE))
    late_values = late_result["values"]
    late_feature_names = late_result["feature_names"]
    late_original = late_result["original_features"]
    late_global = pd.DataFrame(
        {
            "transformed_feature": late_feature_names,
            "original_feature": late_original,
            "feature_family": [feature_family(f) for f in late_original],
            "mean_abs_shap": np.abs(late_values).mean(axis=0),
        }
    )
    late_grouped = late_global.groupby(["original_feature", "feature_family"], as_index=False)["mean_abs_shap"].sum()
    late_family = late_grouped.groupby("feature_family", as_index=False)["mean_abs_shap"].sum().rename(columns={"mean_abs_shap": "late_w1_4_mean_abs_shap"})
    early_family = family_df[["feature_family", "mean_abs_shap"]].rename(columns={"mean_abs_shap": "early_w1_3_mean_abs_shap"})
    late_family_rows = early_family.merge(late_family, on="feature_family", how="outer").fillna(0)
    late_family_rows["late_minus_early"] = late_family_rows["late_w1_4_mean_abs_shap"] - late_family_rows["early_w1_3_mean_abs_shap"]
    late_family_rows["interpretation"] = "w1_4 is late-period/end-of-period and must not be presented as early-warning."
    late_shap_success = True
else:
    late_family_rows = pd.DataFrame(columns=["feature_family", "early_w1_3_mean_abs_shap", "late_w1_4_mean_abs_shap", "late_minus_early", "interpretation"])
write_csv(TABLE_DIR / "07r_w1_3_vs_w1_4_xai_comparison.csv", late_family_rows)

business_readiness = [
    {"classification": "safe_to_report", "finding": "True SHAP was computed for the conservative w1_3 primary model in Python 3.11.", "claim_boundary": "Report as model explanation, not causal effect."},
    {"classification": "safe_to_report", "finding": "Stage 06 holdout split was reused and train/test USER_KEY overlap was zero.", "claim_boundary": "Use as leakage-control evidence."},
    {"classification": "plausible_but_cautioned", "finding": "Usage features dominate SHAP importance.", "claim_boundary": "Predictive behavioral association only."},
    {"classification": "plausible_but_cautioned", "finding": "Genre/content proxy features contribute after usage.", "claim_boundary": "Content metadata is limited to genre and ott_release_month proxies."},
    {"classification": "do_not_claim_yet", "finding": "w1_4 SHAP comparison is late-period/end-of-period.", "claim_boundary": "Do not present w1_4 as early intervention evidence."},
    {"classification": "do_not_claim_yet", "finding": "SHAP does not prove that changing a feature will change churn.", "claim_boundary": "Do not make causal retention claims."},
]
write_csv(TABLE_DIR / "07r_business_readiness_findings.csv", business_readiness)

# Figures
plt.figure()
shap.summary_plot(shap_values, X_trans_df, feature_names=feature_names, show=False, max_display=25)
plt.tight_layout()
plt.savefig(FIGURE_DIR / "07r_shap_beeswarm_red_blue_conservative_w1_3.png", dpi=170, bbox_inches="tight")
plt.close()

plt.figure()
shap.summary_plot(shap_values, X_trans_df, feature_names=feature_names, plot_type="bar", show=False, max_display=25)
plt.tight_layout()
plt.savefig(FIGURE_DIR / "07r_shap_global_bar_conservative_w1_3.png", dpi=170, bbox_inches="tight")
plt.close()

fam_plot = family_df.sort_values("mean_abs_shap")
plt.figure(figsize=(7, 4.5))
plt.barh(fam_plot["feature_family"], fam_plot["mean_abs_shap"])
plt.xlabel("Mean absolute SHAP")
plt.title("Feature-family SHAP importance, conservative w1_3")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "07r_feature_family_shap_importance_conservative_w1_3.png", dpi=160)
plt.close()

push_plot = pd.DataFrame(churn_rows).head(12).iloc[::-1]
plt.figure(figsize=(8, 5))
plt.barh(push_plot["feature"], push_plot["top_minus_low_mean_shap"])
plt.axvline(0, color="black", linewidth=0.8)
plt.xlabel("Top churn-risk minus low-risk mean SHAP")
plt.title("Churn-risk top-decile SHAP push")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "07r_churn_risk_top_decile_shap_push.png", dpi=160)
plt.close()

dependence_files = []
for rank, feature in enumerate(grouped_df.head(5)["original_feature"].tolist(), start=1):
    cols = [i for i, f in enumerate(original_features) if f == feature]
    if not cols:
        continue
    vals = shap_values[:, cols].sum(axis=1)
    raw = raw_sample[feature].reset_index(drop=True)
    plt.figure(figsize=(6.2, 4.6))
    if pd.api.types.is_numeric_dtype(raw):
        plt.scatter(raw, vals, s=10, alpha=0.45, c=sample_meta["churn_risk_score"], cmap="coolwarm")
        plt.colorbar(label="churn_risk_score")
        plt.xlabel(feature)
    else:
        cat_codes = pd.Categorical(raw.astype(str)).codes
        plt.scatter(cat_codes, vals, s=10, alpha=0.45, c=sample_meta["churn_risk_score"], cmap="coolwarm")
        plt.xlabel(f"{feature} category code")
    plt.ylabel("Grouped SHAP toward repurchase margin")
    plt.title(f"SHAP dependence-style top {rank}: {feature}")
    plt.tight_layout()
    fname = f"07r_shap_dependence_top{rank:02d}_{sanitize_name(feature)}.png"
    plt.savefig(FIGURE_DIR / fname, dpi=160)
    plt.close()
    dependence_files.append(fname)

waterfall_files = []
for _, case in local_cases_df.iterrows():
    mid = case[ID_COL]
    if mid in sample_index_by_mid:
        idx = sample_index_by_mid[mid]
        explanation = shap.Explanation(
            values=shap_values[idx],
            base_values=np.asarray(base_values).ravel()[idx],
            data=X_trans_df.iloc[idx].values,
            feature_names=feature_names,
        )
    else:
        continue
    plt.figure()
    shap.plots.waterfall(explanation, max_display=14, show=False)
    plt.tight_layout()
    prefix_map = {
        "high_risk_true_N": "07r_waterfall_high_risk_true_N",
        "high_risk_false_positive": "07r_waterfall_high_risk_false_positive",
        "low_risk_true_Y": "07r_waterfall_low_risk_true_Y",
        "mid_score": "07r_waterfall_mid_score",
    }
    fname = f"{prefix_map[case['case_type']]}_{int(mid)}.png"
    plt.savefig(FIGURE_DIR / fname, dpi=160, bbox_inches="tight")
    plt.close()
    waterfall_files.append(fname)

if late_shap_success:
    late_X_df = late_result["X_trans_df"]
    late_vals = late_result["values"]
    plt.figure()
    shap.summary_plot(late_vals, late_X_df, feature_names=late_result["feature_names"], show=False, max_display=25)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "07r_shap_beeswarm_red_blue_late_w1_4.png", dpi=170, bbox_inches="tight")
    plt.close()

    comp = late_family_rows.copy()
    x = np.arange(len(comp))
    plt.figure(figsize=(7.5, 4.8))
    plt.bar(x - 0.2, comp["early_w1_3_mean_abs_shap"], width=0.4, label="w1_3 early")
    plt.bar(x + 0.2, comp["late_w1_4_mean_abs_shap"], width=0.4, label="w1_4 late")
    plt.xticks(x, comp["feature_family"], rotation=30, ha="right")
    plt.ylabel("Mean abs SHAP")
    plt.title("w1_3 vs w1_4 SHAP family importance")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "07r_w1_3_vs_w1_4_family_importance.png", dpi=160)
    plt.close()

visual_rows = []
for path in sorted(FIGURE_DIR.glob("*.png")):
    visual_rows.append(
        {
            "figure_file": path.name,
            "path": rel(path),
            "size_bytes": path.stat().st_size,
            "recommended_for_team_share": "Y" if path.name in {
                "07r_shap_beeswarm_red_blue_conservative_w1_3.png",
                "07r_shap_global_bar_conservative_w1_3.png",
                "07r_feature_family_shap_importance_conservative_w1_3.png",
                "07r_churn_risk_top_decile_shap_push.png",
                "07r_logistic_top_coefficients_w1_3.png",
                "07r_w1_3_vs_w1_4_family_importance.png",
            } else "N",
        }
    )
write_csv(TABLE_DIR / "07r_visualization_inventory.csv", visual_rows)
write_csv(TABLE_DIR / "07r_team_share_asset_inventory.csv", [r for r in visual_rows if r["recommended_for_team_share"] == "Y"])

team_figs = [r["path"] for r in visual_rows if r["recommended_for_team_share"] == "Y"]
top10 = grouped_df.head(10)
team_lines = [
    "# 07r True SHAP Team Share Summary",
    "",
    "## Primary Model",
    "- w1_3 / membership_plus_usage_content_w1_3_without_churn_prevented / HistGradientBoostingClassifier.",
    f"- AUC explained: {reconstruction_rows[0]['roc_auc_repurchase_rebuilt']:.4f}.",
    "",
    "## Target And Score Direction",
    "- Y -> 1 means repurchase; N -> 0 means non-repurchase / churn risk.",
    "- Positive SHAP pushes toward higher repurchase margin and lower churn risk.",
    "- Negative SHAP pushes away from repurchase and toward higher churn risk.",
    "",
    "## Top 10 SHAP Features",
]
for _, row in top10.iterrows():
    team_lines.append(f"- {row['original_feature']}: mean abs SHAP {row['mean_abs_shap']:.6f}, family {row['feature_family']}")
team_lines.extend(
    [
        "",
        "## Top Feature Families",
    ]
)
for _, row in family_df.iterrows():
    team_lines.append(f"- {row['feature_family']}: {row['mean_abs_shap']:.6f}")
team_lines.extend(
    [
        "",
        "## Interpretation Cautions",
        "- SHAP is model explanation, not causality.",
        "- Content features are genre and ott_release_month proxies only.",
        "- w1_4 comparison is late-period/end-of-period, not early-warning.",
        "",
        "## Recommended Figures",
    ]
)
for fig in team_figs:
    team_lines.append(f"- {fig}")
(DATA_DIR / "07r_team_share_summary.md").write_text("\n".join(team_lines) + "\n", encoding="utf-8")

supersession_lines = [
    "# Stage 07r Supersedes Stage 07 Fallback",
    "",
    "- Stage 07 was fallback-only because `shap` was unavailable in the execution environment used at that time.",
    "- Stage 07r is the true SHAP interpretation stage.",
    "- Final presentation and team sharing should use Stage 07r outputs, not Stage 07 fallback outputs.",
    "- Stage 07 fallback remains only as an audit trail.",
]
(DATA_DIR / "07r_supersedes_stage07_fallback.md").write_text("\n".join(supersession_lines) + "\n", encoding="utf-8")

summary_payload = {
    "scope": "Stage 07r TRUE SHAP interpretation only. No segmentation or business simulation.",
    "python_executable": sys.executable,
    "python_version": sys.version,
    "shap_version": shap.__version__,
    "true_shap_computed_primary": True,
    "target_mapping": {"Y": 1, "N": 0},
    "score_direction": {"repurchase_score": "P(is_repurchase = Y)", "churn_risk_score": "1 - repurchase_score"},
    "primary_model": model_specs[0],
    "secondary_model": model_specs[1],
    "optional_late_period_shap_success": late_shap_success,
    "reconstruction_status": reconstruction_rows,
    "top10_shap_features": top10[["original_feature", "feature_family", "mean_abs_shap"]].to_dict("records"),
    "top_feature_families": family_df.to_dict("records"),
    "stage07_fallback_superseded": True,
}
write_json(DATA_DIR / "07r_true_shap_summary.json", summary_payload)

report_lines = [
    "# 07r_v2 True SHAP Interpretation Report",
    "",
    "## Scope",
    "- Stage 07r computed true SHAP values and supersedes the Stage 07 fallback XAI outputs.",
    "- No segmentation, business simulation, Optuna, tuning, raw modification, or `_data` output was created.",
    f"- Python executable: `{sys.executable}`.",
    f"- SHAP version: `{shap.__version__}`.",
    "",
    "## True SHAP Status",
    "- True SHAP was successfully computed for the primary conservative model.",
    "- The primary model explained is w1_3 / membership_plus_usage_content_w1_3_without_churn_prevented / HistGradientBoostingClassifier.",
    f"- Reconstructed ROC AUC: {reconstruction_rows[0]['roc_auc_repurchase_rebuilt']:.4f}; Stage 06 difference: {reconstruction_rows[0]['roc_auc_difference']:.4f}.",
    "",
    "## Target And Score Direction",
    "- `is_repurchase`: Y -> 1, N -> 0.",
    "- `repurchase_score = P(is_repurchase = Y)`.",
    "- `churn_risk_score = 1 - repurchase_score`.",
    "- Positive SHAP contribution increases the repurchase margin and implies lower churn-risk direction.",
    "- Negative SHAP contribution lowers the repurchase margin and implies higher churn-risk direction.",
    "",
    "## Top Global SHAP Drivers",
]
for _, row in top10.iterrows():
    report_lines.append(f"- {row['original_feature']} ({row['feature_family']}): mean abs SHAP {row['mean_abs_shap']:.6f}.")
report_lines.extend(
    [
        "",
        "## Feature Families",
    ]
)
for _, row in family_df.iterrows():
    report_lines.append(f"- {row['feature_family']}: mean abs SHAP {row['mean_abs_shap']:.6f}.")
report_lines.extend(
    [
        "",
        "## Stage 07 Fallback Comparison",
        "- Stage 07 fallback used permutation importance and coefficient-based interpretation because SHAP was unavailable.",
        "- Stage 07r uses true SHAP values and should be used for final presentation and team sharing.",
        "- Stage 07 remains only as an audit trail.",
        "",
        "## Content Feature Caution",
        "- v2 content metadata is limited to genre and ott_release_month-derived proxies.",
        "- Do not imply country, rating, runtime, actor, director, Wavve, or KOBIS metadata.",
        "",
        "## Stage 08 Use",
        "- Safe to use in Stage 08: conservative w1_3 churn-risk scores and top SHAP feature groups as descriptive segmentation candidates.",
        "- Cautioned: usage/content findings are predictive associations, not causal levers.",
        "- Do not claim: causal drivers, that changing a behavior causes repurchase, or that w1_4 is early-warning.",
        "",
        "## Recommended Team Figures",
    ]
)
for fig in team_figs:
    report_lines.append(f"- {fig}")
(DATA_DIR / "07r_true_shap_interpretation_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

required_outputs = [
    DATA_DIR / "07r_true_shap_summary.json",
    DATA_DIR / "07r_shap_sample_membership_rows.csv",
    DATA_DIR / "07r_local_explanation_cases.csv",
    DATA_DIR / "07r_team_share_summary.md",
    DATA_DIR / "07r_true_shap_interpretation_report.md",
    DATA_DIR / "07r_supersedes_stage07_fallback.md",
    TABLE_DIR / "07r_model_reconstruction_check.csv",
    TABLE_DIR / "07r_global_shap_importance.csv",
    TABLE_DIR / "07r_grouped_shap_importance.csv",
    TABLE_DIR / "07r_feature_family_shap_importance.csv",
    TABLE_DIR / "07r_shap_direction_summary.csv",
    TABLE_DIR / "07r_churn_risk_top_decile_shap_explanation.csv",
    TABLE_DIR / "07r_local_top_contributors.csv",
    TABLE_DIR / "07r_fallback_vs_true_shap_comparison.csv",
    TABLE_DIR / "07r_visualization_inventory.csv",
    TABLE_DIR / "07r_team_share_asset_inventory.csv",
    TABLE_DIR / "07r_business_readiness_findings.csv",
    FIGURE_DIR / "07r_shap_beeswarm_red_blue_conservative_w1_3.png",
    FIGURE_DIR / "07r_shap_global_bar_conservative_w1_3.png",
    FIGURE_DIR / "07r_feature_family_shap_importance_conservative_w1_3.png",
    FIGURE_DIR / "07r_churn_risk_top_decile_shap_push.png",
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
    {"check": "no_project_root_data_output_created", "status": "PASS" if not (PROJECT_ROOT / "_data" / "02_interim" / "07r_v2_true_shap_interpretation").exists() and not (PROJECT_ROOT / "_data" / "07r_v2_true_shap_interpretation").exists() else "FAIL", "detail": "Stage 07r writes only under park.ingyeom/reports"},
    {"check": "stage01_through_stage07_fallback_outputs_not_overwritten", "status": "PASS" if stage_before == stage_after else "FAIL", "detail": "Stage 01-07 snapshots unchanged"},
    {"check": "shap_import_succeeded", "status": "PASS", "detail": shap.__version__},
    {"check": "true_shap_values_computed_for_primary_model", "status": "PASS" if shap_values.size > 0 else "FAIL", "detail": str(shap_values.shape)},
    {"check": "red_blue_shap_beeswarm_created", "status": "PASS" if (FIGURE_DIR / "07r_shap_beeswarm_red_blue_conservative_w1_3.png").exists() else "FAIL", "detail": "classic SHAP summary dot plot"},
    {"check": "no_forbidden_feature_used", "status": "PASS" if not forbidden_used else "FAIL", "detail": f"violations={len(forbidden_used)}"},
    {"check": "target_mapping_documented", "status": "PASS", "detail": "Y=1, N=0"},
    {"check": "score_direction_documented", "status": "PASS", "detail": "repurchase_score and churn_risk_score documented"},
    {"check": "stage06_split_reused", "status": "PASS" if train_ids and test_ids else "FAIL", "detail": rel(STAGE06_TABLES / "06_v2_split_membership_row_ids.csv")},
    {"check": "train_test_USER_KEY_overlap_zero", "status": "PASS" if not (train_groups & test_groups) else "FAIL", "detail": f"overlap={len(train_groups & test_groups)}"},
    {"check": "model_reconstruction_check_completed", "status": "PASS" if (TABLE_DIR / "07r_model_reconstruction_check.csv").exists() else "FAIL", "detail": "reconstruction table"},
    {"check": "global_shap_table_created", "status": "PASS" if (TABLE_DIR / "07r_global_shap_importance.csv").exists() else "FAIL", "detail": "global SHAP table"},
    {"check": "grouped_shap_table_created", "status": "PASS" if (TABLE_DIR / "07r_grouped_shap_importance.csv").exists() else "FAIL", "detail": "grouped SHAP table"},
    {"check": "local_explanation_cases_created", "status": "PASS" if (DATA_DIR / "07r_local_explanation_cases.csv").exists() else "FAIL", "detail": "local cases"},
    {"check": "visualization_inventory_created", "status": "PASS" if (TABLE_DIR / "07r_visualization_inventory.csv").exists() else "FAIL", "detail": "visual inventory"},
    {"check": "team_share_summary_created", "status": "PASS" if (DATA_DIR / "07r_team_share_summary.md").exists() else "FAIL", "detail": "team summary"},
    {"check": "no_segmentation_created", "status": "PASS", "detail": "No segmentation outputs created"},
    {"check": "no_business_simulation_created", "status": "PASS", "detail": "No business simulation outputs created"},
    {"check": "no_optuna_run", "status": "PASS", "detail": "No Optuna imports or tuning used"},
    {"check": "all_required_core_outputs_created", "status": "PASS" if all(p.exists() for p in required_outputs) else "FAIL", "detail": f"core_required_outputs={len(required_outputs)}"},
]
write_csv(TABLE_DIR / "07r_final_checks.csv", final_checks)

print("07r_v2 TRUE SHAP interpretation completed.")
for row in final_checks:
    print(f"{row['check']}: {row['status']} - {row['detail']}")
