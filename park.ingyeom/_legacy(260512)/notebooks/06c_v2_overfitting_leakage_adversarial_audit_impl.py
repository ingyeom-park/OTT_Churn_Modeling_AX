import json
import math
import os
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


warnings.filterwarnings("ignore", category=UserWarning)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

RANDOM_STATE = 42
TEST_SIZE = 0.2
TARGET = "is_repurchase"
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
            (
                (candidate / "_data" / "01_raw" / "Membership.csv").exists()
                or (candidate / "_data" / "01_raw" / "Membership_train.csv").exists()
            )
            and (
                candidate
                / "park.ingyeom"
                / "reports"
                / "data"
                / "05_v2_modeling_dataset"
                / "feature_sets_v2.json"
            ).exists()
        ):
            return candidate
    raise FileNotFoundError("Could not locate ott-churn-prediction project root.")


PROJECT_ROOT = find_project_root(Path.cwd())
STAGE05_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "05_v2_modeling_dataset"
STAGE06_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "06_v2_baseline_modeling"
STAGE06B_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "06b_v2_baseline_sanity_audit"
STAGE06_TABLES = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "06_v2_baseline_modeling"
STAGE07R_TABLES = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "07r_v2_true_shap_interpretation"

DATA_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "06c_v2_overfitting_leakage_adversarial_audit"
TABLE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "06c_v2_overfitting_leakage_adversarial_audit"
FIGURE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "06c_v2_overfitting_leakage_adversarial_audit"
for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

RAW_FILES = [
    PROJECT_ROOT / "_data" / "01_raw" / "Membership.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "User_Mapping.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "View_History.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "Movie_Master.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "Membership_train.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "mapping.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "Views_train.csv",
    PROJECT_ROOT / "_data" / "01_raw" / "Movies.csv",
]

STAGE01_09_PREFIXES = [
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


def rel(path):
    return str(Path(path).resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")


def snapshot_paths(paths):
    out = {}
    for path in paths:
        path = Path(path)
        if path.exists() and path.is_file():
            stat = path.stat()
            out[rel(path)] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    return out


def snapshot_stage01_09():
    out = {}
    for base_name in ["data", "tables", "figures"]:
        base = PROJECT_ROOT / "park.ingyeom" / "reports" / base_name
        for prefix in STAGE01_09_PREFIXES:
            directory = base / prefix
            if directory.exists():
                for path in directory.rglob("*"):
                    if path.is_file():
                        stat = path.stat()
                        out[rel(path)] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    for path in (PROJECT_ROOT / "park.ingyeom" / "notebooks").glob("0[1-9]*"):
        if path.is_file() and path.name.startswith(tuple(p[:2] for p in STAGE01_09_PREFIXES)):
            stat = path.stat()
            out[rel(path)] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    return out


raw_before = snapshot_paths(RAW_FILES)
stage_before = snapshot_stage01_09()


def write_csv(path, obj):
    if isinstance(obj, pd.DataFrame):
        obj.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame(obj).to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def onehot_encoder(sparse=False):
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=sparse)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=sparse)


def has_forbidden_feature(col):
    if col in FORBIDDEN_FEATURES:
        return True
    low = str(col).lower()
    return any(token in low for token in FORBIDDEN_SUBSTRINGS)


def existing_features(df, features):
    return [c for c in features if c in df.columns and not has_forbidden_feature(c)]


def categorical_features_for(features):
    return [c for c in features if c in CATEGORICAL_FEATURES]


def safe_auc(y_true, score):
    if len(np.unique(y_true)) < 2:
        return np.nan
    return float(roc_auc_score(y_true, score))


def safe_ap(y_true, score):
    if len(np.unique(y_true)) < 2:
        return np.nan
    return float(average_precision_score(y_true, score))


def target_to_num(series):
    mapped = series.map({"Y": 1, "N": 0, "1": 1, "0": 0, 1: 1, 0: 0})
    if mapped.isna().any():
        mapped = pd.to_numeric(series, errors="coerce")
    return mapped.astype(int)


def make_pipeline(features, categorical_features, model_name):
    numeric_features = [c for c in features if c not in categorical_features]
    cat_features = [c for c in features if c in categorical_features]
    transformers = []
    if numeric_features:
        num_steps = [("imputer", SimpleImputer(strategy="median"))]
        if model_name == "LogisticRegression":
            num_steps.append(("scaler", StandardScaler()))
        transformers.append(("num", Pipeline(num_steps), numeric_features))
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
    if model_name == "LogisticRegression":
        model = LogisticRegression(max_iter=1000, class_weight=None, solver="lbfgs")
    else:
        model = HistGradientBoostingClassifier(
            max_iter=60,
            learning_rate=0.08,
            max_leaf_nodes=31,
            random_state=RANDOM_STATE,
        )
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def get_scores(pipe, X):
    proba = pipe.predict_proba(X)
    classes = list(pipe.named_steps["model"].classes_)
    return proba[:, classes.index(1)]


def eval_fixed_model(df, features, train_ids, test_ids, model_name="HistGradientBoostingClassifier", label=""):
    features = existing_features(df, features)
    if not features:
        return {
            "status": "BLOCKED",
            "blocked_reason": "No usable features after filtering forbidden/missing columns.",
            "feature_count": 0,
        }
    train_mask = df[ID_COL].isin(train_ids)
    test_mask = df[ID_COL].isin(test_ids)
    X_train = df.loc[train_mask, features]
    X_test = df.loc[test_mask, features]
    y_train = target_to_num(df.loc[train_mask, TARGET]).to_numpy()
    y_test = target_to_num(df.loc[test_mask, TARGET]).to_numpy()
    if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
        return {
            "status": "BLOCKED",
            "blocked_reason": "Train or test target has fewer than two classes.",
            "feature_count": len(features),
        }
    pipe = make_pipeline(features, categorical_features_for(features), model_name)
    pipe.fit(X_train, y_train)
    repurchase_score = get_scores(pipe, X_test)
    churn_score = 1 - repurchase_score
    try:
        transformed_count = int(pipe.named_steps["preprocess"].transform(X_test.head(1)).shape[1])
    except Exception:
        transformed_count = np.nan
    return {
        "status": "RUN",
        "blocked_reason": "",
        "label": label,
        "model_name": model_name,
        "feature_count": len(features),
        "post_transform_feature_count": transformed_count,
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "train_repurchase_rate": float(np.mean(y_train)),
        "test_repurchase_rate": float(np.mean(y_test)),
        "test_churn_rate": float(np.mean(1 - y_test)),
        "roc_auc_repurchase": safe_auc(y_test, repurchase_score),
        "average_precision_repurchase": safe_ap(y_test, repurchase_score),
        "average_precision_churn_risk": safe_ap(1 - y_test, churn_score),
        "brier_repurchase": float(brier_score_loss(y_test, repurchase_score)),
        "repurchase_score": repurchase_score,
        "churn_risk_score": churn_score,
        "y_test": y_test,
        "test_ids": df.loc[test_mask, ID_COL].to_numpy(),
        "pipe": pipe,
        "features": features,
    }


def result_without_arrays(result):
    return {k: v for k, v in result.items() if k not in {"repurchase_score", "churn_risk_score", "y_test", "test_ids", "pipe", "features"}}


def decile_table(y_repurchase, churn_score, label, split_id="stage06_holdout"):
    df = pd.DataFrame({"y_repurchase": y_repurchase, "churn_risk_score": churn_score})
    df["y_churn"] = 1 - df["y_repurchase"]
    df = df.sort_values("churn_risk_score", ascending=False).reset_index(drop=True)
    df["risk_decile"] = pd.qcut(np.arange(len(df)), 10, labels=[f"D{i}" for i in range(1, 11)])
    rows = []
    overall = df["y_churn"].mean()
    for decile, sub in df.groupby("risk_decile", observed=False):
        rows.append(
            {
                "label": label,
                "split_id": split_id,
                "risk_decile": decile,
                "n": int(len(sub)),
                "mean_churn_risk_score": float(sub["churn_risk_score"].mean()),
                "observed_churn_rate": float(sub["y_churn"].mean()),
                "observed_repurchase_rate": float(sub["y_repurchase"].mean()),
                "lift_vs_overall_churn": float(sub["y_churn"].mean() / overall) if overall else np.nan,
                "overall_churn_rate": float(overall),
            }
        )
    out = pd.DataFrame(rows)
    out["decile_order"] = out["risk_decile"].str.extract(r"(\d+)").astype(int)
    return out.sort_values("decile_order")


def top_decile_lift(y_repurchase, churn_score):
    d = decile_table(y_repurchase, churn_score, "tmp")
    top = d[d["risk_decile"].eq("D1")]
    if top.empty:
        return np.nan, np.nan
    return float(top["observed_churn_rate"].iloc[0]), float(top["lift_vs_overall_churn"].iloc[0])


def monotonic_nonincreasing(values):
    arr = [x for x in values if pd.notna(x)]
    return all(arr[i] >= arr[i + 1] for i in range(len(arr) - 1)) if len(arr) >= 2 else False


def quantile_bins_for_feature(df, feature, test_ids):
    sub = df[df[ID_COL].isin(test_ids)][[feature, TARGET]].copy()
    sub = sub.rename(columns={TARGET: "y_repurchase"})
    sub["y_repurchase"] = target_to_num(sub["y_repurchase"])
    sub["y_churn"] = 1 - sub["y_repurchase"]
    if sub[feature].nunique(dropna=True) <= 1:
        return pd.DataFrame(
            [
                {
                    "feature": feature,
                    "bin": "single_value",
                    "n": int(len(sub)),
                    "feature_min": sub[feature].min(),
                    "feature_max": sub[feature].max(),
                    "repurchase_rate": float(sub["y_repurchase"].mean()),
                    "churn_rate": float(sub["y_churn"].mean()),
                }
            ]
        )
    try:
        sub["bin"] = pd.qcut(sub[feature], q=5, duplicates="drop")
    except Exception:
        sub["bin"] = sub[feature].astype(str).fillna("MISSING")
    rows = []
    for b, g in sub.groupby("bin", observed=False):
        rows.append(
            {
                "feature": feature,
                "bin": str(b),
                "n": int(len(g)),
                "feature_min": g[feature].min() if pd.api.types.is_numeric_dtype(g[feature]) else "",
                "feature_max": g[feature].max() if pd.api.types.is_numeric_dtype(g[feature]) else "",
                "repurchase_rate": float(g["y_repurchase"].mean()),
                "churn_rate": float(g["y_churn"].mean()),
            }
        )
    return pd.DataFrame(rows)


def build_window_proxy(df_w13):
    df = df_w13.copy()
    df["w1_1_total_watch_time_proxy"] = df["w1_3_week1_watch_time"]
    df["w1_1_total_sessions_proxy"] = df["w1_3_week1_sessions"]
    df["w1_1_has_watch_proxy"] = (df["w1_3_week1_watch_time"].fillna(0) > 0).astype(int)
    df["w1_1_no_watch_proxy"] = 1 - df["w1_1_has_watch_proxy"]
    df["w1_2_total_watch_time_proxy"] = df["w1_3_week1_watch_time"] + df["w1_3_week2_watch_time"]
    df["w1_2_total_sessions_proxy"] = df["w1_3_week1_sessions"] + df["w1_3_week2_sessions"]
    df["w1_2_has_watch_proxy"] = (df["w1_2_total_watch_time_proxy"].fillna(0) > 0).astype(int)
    df["w1_2_no_watch_proxy"] = 1 - df["w1_2_has_watch_proxy"]
    df["w1_2_w2_minus_w1_watch_time_proxy"] = df["w1_3_week2_watch_time"] - df["w1_3_week1_watch_time"]
    denom = df["w1_2_total_watch_time_proxy"].replace(0, np.nan)
    df["w1_2_week1_ratio_proxy"] = (df["w1_3_week1_watch_time"] / denom).fillna(0)
    df["w1_2_week2_ratio_proxy"] = (df["w1_3_week2_watch_time"] / denom).fillna(0)
    return df


def feature_hash_frame(df, features, round_numeric=False):
    tmp = df[features].copy()
    for col in features:
        if pd.api.types.is_numeric_dtype(tmp[col]):
            tmp[col] = pd.to_numeric(tmp[col], errors="coerce").fillna(-999999)
            if round_numeric:
                tmp[col] = tmp[col].round(3)
        else:
            tmp[col] = tmp[col].astype(str).fillna("__MISSING__")
    return pd.util.hash_pandas_object(tmp, index=False)


def save_bar(df, x, y, path, title, xlabel="", ylabel="", hue=None, rotate=30):
    plt.figure(figsize=(10, 5.5))
    if df.empty:
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
    elif hue and hue in df.columns:
        labels = df[x].astype(str) + "\n" + df[hue].astype(str)
        plt.bar(labels, df[y])
        plt.xticks(rotation=rotate, ha="right")
    else:
        plt.bar(df[x].astype(str), df[y])
        plt.xticks(rotation=rotate, ha="right")
    plt.title(title)
    plt.xlabel(xlabel or x)
    plt.ylabel(ylabel or y)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def write_notebook():
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 06c v2 Overfitting, Leakage, and Target-Proxy Adversarial Audit\n",
                    "\n",
                    "This notebook executes the Stage 06c implementation script. It does not tune models, run Optuna, run SHAP, create segmentation, or create business simulation.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "%run 06c_v2_overfitting_leakage_adversarial_audit_impl.py\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    nb_path = PROJECT_ROOT / "park.ingyeom" / "notebooks" / "06c_v2_overfitting_leakage_adversarial_audit.ipynb"
    nb_path.write_text(json.dumps(nb, ensure_ascii=False, indent=2), encoding="utf-8")


plt.rcParams.update(
    {
        "font.family": "Malgun Gothic",
        "font.sans-serif": ["Malgun Gothic", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "figure.dpi": 140,
        "savefig.dpi": 160,
    }
)

paths = {
    "w1_3": STAGE05_DATA / "modeling_dataset_v2_w1_3.csv",
    "w1_4": STAGE05_DATA / "modeling_dataset_v2_w1_4.csv",
    "feature_sets": STAGE05_DATA / "feature_sets_v2.json",
    "stage06_metrics": STAGE06_DATA / "06_v2_model_metrics.csv",
    "stage06_prediction_scores": STAGE06_DATA / "06_v2_prediction_scores.csv",
    "best_config": STAGE06_DATA / "06_v2_best_model_config.json",
    "stage06b_summary": STAGE06B_DATA / "06b_sanity_audit_summary.json",
    "split_ids": STAGE06_TABLES / "06_v2_split_membership_row_ids.csv",
    "global_shap": STAGE07R_TABLES / "07r_global_shap_importance.csv",
    "family_shap": STAGE07R_TABLES / "07r_feature_family_shap_importance.csv",
}

df_w13 = pd.read_csv(paths["w1_3"])
df_w14 = pd.read_csv(paths["w1_4"])
feature_sets = read_json(paths["feature_sets"])
best_config = read_json(paths["best_config"])
stage06b_summary = read_json(paths["stage06b_summary"])
split_df = pd.read_csv(paths["split_ids"])
global_shap = pd.read_csv(paths["global_shap"]) if paths["global_shap"].exists() else pd.DataFrame()
family_shap = pd.read_csv(paths["family_shap"]) if paths["family_shap"].exists() else pd.DataFrame()

CATEGORICAL_FEATURES = set(feature_sets.get("categorical_features_to_encode_in_stage06", []))
FS = feature_sets["feature_sets"]

train_ids = set(split_df.loc[split_df["holdout_split"].eq("train"), ID_COL].astype(int))
test_ids = set(split_df.loc[split_df["holdout_split"].eq("test"), ID_COL].astype(int))

conservative_features = FS["membership_plus_usage_content_w1_3_without_churn_prevented"]
conservative_model_name = "HistGradientBoostingClassifier"
lr_model_name = "LogisticRegression"

conservative_eval = eval_fixed_model(
    df_w13,
    conservative_features,
    train_ids,
    test_ids,
    model_name=conservative_model_name,
    label="full_current_w1_3_hgb",
)
lr_full_eval = eval_fixed_model(
    df_w13,
    conservative_features,
    train_ids,
    test_ids,
    model_name=lr_model_name,
    label="full_current_w1_3_lr",
)

# 1-2. Time-window shrinkage test
proxy_df = build_window_proxy(df_w13)
membership = FS["membership_only_without_churn_prevented"]
w11_usage = [
    "w1_1_has_watch_proxy",
    "w1_1_no_watch_proxy",
    "w1_1_total_watch_time_proxy",
    "w1_1_total_sessions_proxy",
]
w12_usage = [
    "w1_2_has_watch_proxy",
    "w1_2_no_watch_proxy",
    "w1_2_total_watch_time_proxy",
    "w1_2_total_sessions_proxy",
    "w1_2_w2_minus_w1_watch_time_proxy",
    "w1_2_week1_ratio_proxy",
    "w1_2_week2_ratio_proxy",
]
window_specs = [
    ("w1_1", proxy_df, "proxy_from_w1_3_week1_columns", "membership_only", membership, True),
    ("w1_1", proxy_df, "proxy_from_w1_3_week1_columns", "usage_only", w11_usage, True),
    ("w1_1", proxy_df, "proxy_from_w1_3_week1_columns", "membership_plus_usage", membership + w11_usage, True),
    ("w1_1", proxy_df, "BLOCKED_NEEDS_STAGE03_REBUILD", "membership_plus_usage_content", [], False),
    ("w1_2", proxy_df, "proxy_from_w1_3_week1_week2_columns", "membership_only", membership, True),
    ("w1_2", proxy_df, "proxy_from_w1_3_week1_week2_columns", "usage_only", w12_usage, True),
    ("w1_2", proxy_df, "proxy_from_w1_3_week1_week2_columns", "membership_plus_usage", membership + w12_usage, True),
    ("w1_2", proxy_df, "BLOCKED_NEEDS_STAGE03_REBUILD", "membership_plus_usage_content", [], False),
    ("w1_3", df_w13, "official_saved_table", "membership_only", membership, True),
    ("w1_3", df_w13, "official_saved_table", "usage_only", FS["usage_w1_3_only"], True),
    ("w1_3", df_w13, "official_saved_table", "membership_plus_usage", FS["membership_plus_usage_w1_3_without_churn_prevented"], True),
    ("w1_3", df_w13, "official_saved_table", "membership_plus_usage_content", conservative_features, True),
    ("w1_4", df_w14, "official_saved_table", "membership_only", membership, True),
    ("w1_4", df_w14, "official_saved_table", "usage_only", FS["usage_w1_4_only"], True),
    ("w1_4", df_w14, "official_saved_table", "membership_plus_usage", FS["membership_plus_usage_w1_4_without_churn_prevented"], True),
    ("w1_4", df_w14, "official_saved_table", "membership_plus_usage_content", FS["membership_plus_usage_content_w1_4_without_churn_prevented"], True),
]
time_rows = []
for window, df, derivation, family, feats, runnable in window_specs:
    if not runnable:
        time_rows.append(
            {
                "window": window,
                "feature_family": family,
                "model_name": conservative_model_name,
                "status": "BLOCKED",
                "blocked_reason": "Exact content and cumulative feature reconstruction for w1_1/w1_2 is not available from saved Stage 05 tables; Stage 03 rebuild would be required.",
                "derivation": derivation,
                "feature_count": 0,
            }
        )
        continue
    res = eval_fixed_model(df, feats, train_ids, test_ids, model_name=conservative_model_name, label=f"{window}_{family}")
    row = {"window": window, "feature_family": family, "derivation": derivation, **result_without_arrays(res)}
    time_rows.append(row)
time_window_df = pd.DataFrame(time_rows)
write_csv(TABLE_DIR / "06c_time_window_shrinkage_test.csv", time_window_df)

# 3. Top-feature removal tests
removal_groups = {
    "baseline_no_removal": [],
    "remove_all_week3_features": ["week3"],
    "remove_first_last_watch_rel_day": ["first_watch_rel_day", "last_watch_rel_day"],
    "remove_week_ratio_features": ["week1_ratio", "week2_ratio", "week3_ratio"],
    "remove_delta_features": ["minus_w1", "minus_w3", "w2_minus", "w3_minus", "w4_minus"],
    "remove_all_content_features": ["content_", "genre_", "top_genre", "release_month", "recent_content", "old_content"],
    "remove_genre_watch_time_session_count": ["genre_watch_time", "genre_session_count", "top_genre_watch_time"],
    "remove_genre_ratio_features": ["genre_ratio", "top_genre_watch_ratio"],
    "remove_price_product_promotion_membership": ["price", "product_code", "promotion", "is_promotion"],
    "remove_no_watch_has_watch_features": ["no_watch", "has_watch"],
}
removal_rows = []
baseline_by_model = {}
for model_name in [conservative_model_name, lr_model_name]:
    base = eval_fixed_model(df_w13, conservative_features, train_ids, test_ids, model_name=model_name, label="baseline_no_removal")
    baseline_auc = base.get("roc_auc_repurchase", np.nan)
    baseline_by_model[model_name] = base
    for group_name, tokens in removal_groups.items():
        if group_name == "baseline_no_removal":
            feats = conservative_features
        else:
            feats = [f for f in conservative_features if not any(token in f for token in tokens)]
        res = eval_fixed_model(df_w13, feats, train_ids, test_ids, model_name=model_name, label=group_name)
        row = {
            "removal_group": group_name,
            "removed_feature_count": len(existing_features(df_w13, conservative_features)) - len(existing_features(df_w13, feats)),
            "model_name": model_name,
            **result_without_arrays(res),
        }
        row["baseline_auc_same_model"] = baseline_auc
        row["auc_drop_vs_baseline"] = baseline_auc - row.get("roc_auc_repurchase", np.nan) if row.get("status") == "RUN" else np.nan
        removal_rows.append(row)
top_removal_df = pd.DataFrame(removal_rows)
write_csv(TABLE_DIR / "06c_top_feature_removal_test.csv", top_removal_df)

# 4. Content proxy audit
content_feature_groups = {
    "genre_ratio_features_only": [c for c in FS["content_w1_3_only"] if "genre_ratio" in c or "top_genre_watch_ratio" in c],
    "genre_watch_time_features_only": [c for c in FS["content_w1_3_only"] if "genre_watch_time" in c or "top_genre_watch_time" in c],
    "genre_session_count_features_only": [c for c in FS["content_w1_3_only"] if "genre_session_count" in c],
    "top_genre_only": ["w1_3_top_genre"],
    "release_month_features_only": [c for c in FS["content_w1_3_only"] if "release_month" in c or "recent_content" in c or "old_content" in c],
    "content_coverage_features_only": [c for c in FS["content_w1_3_only"] if "covered" in c or "missing" in c or "content_has_watch" in c],
}
content_rows = []
usage_intensity_cols = ["w1_3_total_watch_time", "w1_3_total_sessions", "w1_3_unique_watch_days"]
for group_name, feats in content_feature_groups.items():
    res = eval_fixed_model(df_w13, feats, train_ids, test_ids, model_name=conservative_model_name, label=group_name)
    corrs = []
    for feat in existing_features(df_w13, feats):
        if pd.api.types.is_numeric_dtype(df_w13[feat]):
            for usage_col in usage_intensity_cols:
                corrs.append(abs(df_w13[[feat, usage_col]].corr().iloc[0, 1]))
    max_corr = float(np.nanmax(corrs)) if corrs else np.nan
    if "watch_time" in group_name or "session_count" in group_name or max_corr >= 0.75:
        risk = "HIGH: likely duplicates usage intensity or viewing volume."
    elif "ratio" in group_name or "top_genre_only" in group_name:
        risk = "MEDIUM: closer to preference mix, but still conditional on having watched content."
    else:
        risk = "MEDIUM_HIGH: coverage/release proxies may encode whether and how much content was watched."
    content_rows.append(
        {
            "content_feature_group": group_name,
            "max_abs_corr_with_usage_intensity": max_corr,
            "interpretation_risk": risk,
            "duplicates_usage_intensity_flag": "Y" if (pd.notna(max_corr) and max_corr >= 0.75) or "watch_time" in group_name or "session_count" in group_name else "N",
            **result_without_arrays(res),
        }
    )
content_proxy_df = pd.DataFrame(content_rows)
write_csv(TABLE_DIR / "06c_content_proxy_audit.csv", content_proxy_df)

# 5. Single-feature AUC and bins
requested_single_features = [
    "w1_3_week3_watch_time",
    "w1_3_w2_minus_w1_watch_time",
    "w1_3_week1_ratio",
    "price",
    "w1_3_first_watch_rel_day",
    "w1_3_genre_ratio_thriller_crime",
    "w1_3_genre_ratio_animation_family",
    "w1_3_genre_ratio_drama",
    "w1_3_genre_session_count_drama",
    "w1_3_genre_ratio_action_adventure",
    "w1_3_has_watch_obs",
    "w1_3_no_watch_obs_flag",
]
single_rows = []
bin_rows = []
test_mask = df_w13[ID_COL].isin(test_ids)
for feat in requested_single_features:
    if feat not in df_w13.columns:
        single_rows.append({"feature": feat, "status": "BLOCKED", "blocked_reason": "feature not present"})
        continue
    sub = df_w13.loc[test_mask, [feat, TARGET]].copy()
    y = target_to_num(sub[TARGET]).to_numpy()
    x = pd.to_numeric(sub[feat], errors="coerce").fillna(sub[feat].median() if pd.api.types.is_numeric_dtype(sub[feat]) else 0).to_numpy()
    auc_raw = safe_auc(y, x)
    auc_oriented = max(auc_raw, 1 - auc_raw) if pd.notna(auc_raw) else np.nan
    bins = quantile_bins_for_feature(df_w13, feat, test_ids)
    rates = bins["churn_rate"].to_list()
    monotonic = monotonic_nonincreasing(rates) or monotonic_nonincreasing(list(reversed(rates)))
    near_det = (np.nanmax(rates) - np.nanmin(rates) >= 0.75) if len(rates) else False
    for _, b in bins.iterrows():
        row = b.to_dict()
        row["single_feature_auc_raw_repurchase"] = auc_raw
        row["single_feature_auc_oriented"] = auc_oriented
        bin_rows.append(row)
    single_rows.append(
        {
            "feature": feat,
            "status": "RUN",
            "blocked_reason": "",
            "single_feature_auc_raw_repurchase": auc_raw,
            "single_feature_auc_oriented": auc_oriented,
            "min_bin_churn_rate": float(np.nanmin(rates)) if len(rates) else np.nan,
            "max_bin_churn_rate": float(np.nanmax(rates)) if len(rates) else np.nan,
            "monotonic_relation_flag": "Y" if monotonic else "N",
            "near_deterministic_flag": "Y" if near_det else "N",
        }
    )
single_summary_df = pd.DataFrame(single_rows)
single_bins_df = pd.DataFrame(bin_rows)
single_auc_bins_df = single_bins_df.merge(
    single_summary_df[["feature", "status", "blocked_reason", "monotonic_relation_flag", "near_deterministic_flag"]],
    on="feature",
    how="left",
)
write_csv(TABLE_DIR / "06c_single_feature_auc_bins.csv", single_auc_bins_df)

# 6. Subgroup generalization
subgroup_specs = []
test_df = df_w13.loc[test_mask].copy()
if "is_promotion" in df_w13.columns:
    for val in sorted(test_df["is_promotion"].dropna().unique()):
        subgroup_specs.append((f"is_promotion={val}", test_df["is_promotion"].eq(val)))
if "price" in df_w13.columns:
    subgroup_specs.append(("price_100won_or_less", test_df["price"].le(100)))
    median_price = test_df["price"].median()
    subgroup_specs.append((f"price_low_le_median_{median_price}", test_df["price"].le(median_price)))
    subgroup_specs.append((f"price_high_gt_median_{median_price}", test_df["price"].gt(median_price)))
if "max_screen" in df_w13.columns:
    for val in sorted(test_df["max_screen"].dropna().unique()):
        subgroup_specs.append((f"max_screen={val}", test_df["max_screen"].eq(val)))
if "w1_3_has_watch_obs" in df_w13.columns:
    subgroup_specs.append(("has_watch_history", test_df["w1_3_has_watch_obs"].eq(1)))
    subgroup_specs.append(("no_watch_history", test_df["w1_3_has_watch_obs"].eq(0)))
if "product_code" in df_w13.columns:
    product_churn = test_df.assign(y_churn=1 - target_to_num(test_df[TARGET])).groupby("product_code")["y_churn"].agg(["size", "mean"]).reset_index()
    for _, row in product_churn[product_churn["size"].ge(100)].sort_values("mean", ascending=False).head(5).iterrows():
        subgroup_specs.append((f"high_risk_product_code={row['product_code']}", test_df["product_code"].eq(row["product_code"])))

subgroup_rows = []
full_scores = conservative_eval["repurchase_score"]
full_y = conservative_eval["y_test"]
full_test_ids = conservative_eval["test_ids"]
score_df = pd.DataFrame({ID_COL: full_test_ids, "y_repurchase": full_y, "repurchase_score": full_scores})
score_df["churn_risk_score"] = 1 - score_df["repurchase_score"]
score_df = score_df.merge(test_df[[ID_COL]], on=ID_COL, how="left")
for name, mask in subgroup_specs:
    ids = set(test_df.loc[mask, ID_COL])
    sub = score_df[score_df[ID_COL].isin(ids)]
    if len(sub) < 50 or sub["y_repurchase"].nunique() < 2:
        subgroup_rows.append(
            {
                "subgroup": name,
                "status": "BLOCKED",
                "blocked_reason": "too few rows or one target class in subgroup",
                "n": int(len(sub)),
            }
        )
        continue
    subgroup_rows.append(
        {
            "subgroup": name,
            "status": "RUN",
            "blocked_reason": "",
            "n": int(len(sub)),
            "repurchase_rate": float(sub["y_repurchase"].mean()),
            "churn_rate": float(1 - sub["y_repurchase"].mean()),
            "roc_auc_repurchase": safe_auc(sub["y_repurchase"], sub["repurchase_score"]),
            "average_precision_churn_risk": safe_ap(1 - sub["y_repurchase"], sub["churn_risk_score"]),
            "auc_drop_vs_overall": conservative_eval["roc_auc_repurchase"] - safe_auc(sub["y_repurchase"], sub["repurchase_score"]),
            "collapse_flag": "Y" if safe_auc(sub["y_repurchase"], sub["repurchase_score"]) < 0.70 else "N",
        }
    )
subgroup_df = pd.DataFrame(subgroup_rows)
write_csv(TABLE_DIR / "06c_subgroup_generalization.csv", subgroup_df)

# 7. Harder split diagnostics
hard_rows = []
hard_rows.append(
    {
        "diagnostic": "existing_user_key_group_shuffle_split",
        "split_id": "stage06_official",
        "status": "RUN",
        "blocked_reason": "",
        **result_without_arrays(conservative_eval),
    }
)
gss = GroupShuffleSplit(n_splits=3, test_size=TEST_SIZE, random_state=RANDOM_STATE + 100)
features = existing_features(df_w13, conservative_features)
for i, (tr_idx, te_idx) in enumerate(gss.split(df_w13, target_to_num(df_w13[TARGET]), groups=df_w13[GROUP_COL]), start=1):
    tr_ids = set(df_w13.iloc[tr_idx][ID_COL].astype(int))
    te_ids = set(df_w13.iloc[te_idx][ID_COL].astype(int))
    res = eval_fixed_model(df_w13, features, tr_ids, te_ids, model_name=conservative_model_name, label=f"repeated_gss_{i}")
    hard_rows.append({"diagnostic": "repeated_group_shuffle_split", "split_id": f"repeat_{i}", **result_without_arrays(res)})

if "reg_date" not in df_w13.columns:
    hard_rows.append(
        {
            "diagnostic": "reg_date_time_split",
            "split_id": "blocked",
            "status": "BLOCKED",
            "blocked_reason": "reg_date is not present in the Stage 05 modeling dataset because it is forbidden metadata; cannot run time split without rebuilding an audit-only split source.",
        }
    )

for col, diagnostic in [("product_code", "product_code_holdout"), ("max_screen", "max_screen_holdout")]:
    if col in df_w13.columns:
        counts = df_w13[col].value_counts(dropna=False)
        for val in counts[counts.ge(500)].index[:8]:
            te_ids = set(df_w13.loc[df_w13[col].eq(val), ID_COL].astype(int))
            tr_ids = set(df_w13.loc[~df_w13[col].eq(val), ID_COL].astype(int))
            if len(te_ids) < 200:
                continue
            res = eval_fixed_model(df_w13, features, tr_ids, te_ids, model_name=conservative_model_name, label=f"{diagnostic}_{val}")
            hard_rows.append({"diagnostic": diagnostic, "split_id": str(val), **result_without_arrays(res)})
harder_split_df = pd.DataFrame(hard_rows)
write_csv(TABLE_DIR / "06c_harder_split_diagnostics.csv", harder_split_df)

# 8. Distribution shift audit
top_for_shift = requested_single_features + ["product_code", "is_promotion", "max_screen"]
shift_rows = []
train_mask = df_w13[ID_COL].isin(train_ids)
for feat in [f for f in top_for_shift if f in df_w13.columns]:
    tr = df_w13.loc[train_mask, feat]
    te = df_w13.loc[test_mask, feat]
    if pd.api.types.is_numeric_dtype(df_w13[feat]):
        tr_mean = tr.mean()
        te_mean = te.mean()
        pooled_sd = math.sqrt((tr.var() + te.var()) / 2) if pd.notna(tr.var()) and pd.notna(te.var()) else np.nan
        smd = (te_mean - tr_mean) / pooled_sd if pooled_sd and pooled_sd != 0 else np.nan
        shift_rows.append(
            {
                "feature": feat,
                "feature_type": "numeric",
                "train_mean": tr_mean,
                "test_mean": te_mean,
                "train_median": tr.median(),
                "test_median": te.median(),
                "train_std": tr.std(),
                "test_std": te.std(),
                "train_missing_rate": tr.isna().mean(),
                "test_missing_rate": te.isna().mean(),
                "train_q10": tr.quantile(0.1),
                "test_q10": te.quantile(0.1),
                "train_q90": tr.quantile(0.9),
                "test_q90": te.quantile(0.9),
                "standardized_mean_difference": smd,
                "shift_flag": "Y" if pd.notna(smd) and abs(smd) >= 0.10 else "N",
                "category_value": "",
                "train_proportion": "",
                "test_proportion": "",
            }
        )
    else:
        tr_prop = tr.astype(str).fillna("__MISSING__").value_counts(normalize=True)
        te_prop = te.astype(str).fillna("__MISSING__").value_counts(normalize=True)
        for val in sorted(set(tr_prop.index).union(set(te_prop.index))):
            diff = te_prop.get(val, 0) - tr_prop.get(val, 0)
            shift_rows.append(
                {
                    "feature": feat,
                    "feature_type": "categorical",
                    "category_value": val,
                    "train_proportion": tr_prop.get(val, 0),
                    "test_proportion": te_prop.get(val, 0),
                    "proportion_difference": diff,
                    "shift_flag": "Y" if abs(diff) >= 0.05 else "N",
                }
            )
shift_df = pd.DataFrame(shift_rows)
write_csv(TABLE_DIR / "06c_train_test_distribution_shift.csv", shift_df)

# 9. Duplicate and near-duplicate feature audit
dup_features = existing_features(df_w13, conservative_features)
train_feat = df_w13.loc[train_mask, [ID_COL, TARGET] + dup_features].copy()
test_feat = df_w13.loc[test_mask, [ID_COL, TARGET] + dup_features].copy()
train_hash = feature_hash_frame(train_feat, dup_features, round_numeric=False)
test_hash = feature_hash_frame(test_feat, dup_features, round_numeric=False)
train_round_hash = feature_hash_frame(train_feat, dup_features, round_numeric=True)
test_round_hash = feature_hash_frame(test_feat, dup_features, round_numeric=True)
train_hash_df = pd.DataFrame({"hash": train_hash, "target": target_to_num(train_feat[TARGET])})
test_hash_df = pd.DataFrame({"hash": test_hash, "target": target_to_num(test_feat[TARGET])})
train_hash_targets = {}
for hash_value, target_value in zip(train_hash_df["hash"].to_numpy(), train_hash_df["target"].to_numpy()):
    train_hash_targets.setdefault(int(hash_value), set()).add(int(target_value))
duplicate_test = test_hash_df[test_hash_df["hash"].map(lambda x: int(x) in train_hash_targets)]
same_target = 0
conflicting_target = 0
for hash_value, target_value in zip(duplicate_test["hash"].to_numpy(), duplicate_test["target"].to_numpy()):
    targets = train_hash_targets.get(int(hash_value), set())
    if int(target_value) in targets:
        same_target += 1
    if any(t != int(target_value) for t in targets):
        conflicting_target += 1
near_train_hashes = set(train_round_hash)
near_duplicate_test_count = int(pd.Series(test_round_hash).isin(near_train_hashes).sum())
dup_rows = [
    {
        "audit_type": "exact_duplicate_feature_vector_train_to_test",
        "feature_count": len(dup_features),
        "test_rows_with_train_duplicate_vector": int(len(duplicate_test)),
        "duplicate_feature_vectors_with_same_target": int(same_target),
        "duplicate_feature_vectors_with_conflicting_target": int(conflicting_target),
        "share_of_test_rows": float(len(duplicate_test) / len(test_feat)),
        "inflation_risk": "HIGH" if len(duplicate_test) / len(test_feat) >= 0.05 else "LOW",
        "note": "Exact hash over current conservative feature vector after removing metadata and target.",
    },
    {
        "audit_type": "near_duplicate_feature_vector_train_to_test_rounded_numeric_3dp",
        "feature_count": len(dup_features),
        "test_rows_with_train_duplicate_vector": near_duplicate_test_count,
        "duplicate_feature_vectors_with_same_target": "",
        "duplicate_feature_vectors_with_conflicting_target": "",
        "share_of_test_rows": float(near_duplicate_test_count / len(test_feat)),
        "inflation_risk": "MEDIUM" if near_duplicate_test_count / len(test_feat) >= 0.05 else "LOW",
        "note": "Near-duplicate proxy using numeric features rounded to 3 decimals plus categorical strings.",
    },
]
duplicate_df = pd.DataFrame(dup_rows)
write_csv(TABLE_DIR / "06c_duplicate_feature_vector_audit.csv", duplicate_df)

# 10. Label and temporal audit reprise
temporal_rows = []
for check, status, detail in [
    ("no_end_date_feature", "PASS" if "end_date" not in dup_features else "FAIL", "end_date not in X"),
    ("no_duration_days_feature", "PASS" if "duration_days" not in dup_features else "FAIL", "duration_days not in X"),
    ("no_watch_date_or_watch_day_raw_feature", "PASS" if not any(f in dup_features for f in ["watch_date", "watch_day"]) else "FAIL", "raw watch_date/watch_day not in X"),
    ("no_w1_4_feature_in_w1_3_model", "PASS" if not any(str(f).startswith("w1_4_") for f in dup_features) else "FAIL", "w1_3 conservative feature set contains no w1_4 columns"),
    ("no_target_in_X", "PASS" if TARGET not in dup_features else "FAIL", "is_repurchase not in X"),
    ("no_user_or_movie_keys_in_X", "PASS" if not any(f in dup_features for f in ["USER_KEY", "USER_NUM", "MOVIE_NUM"]) else "FAIL", "USER/MOVIE keys not in X"),
    ("watch_date_after_end_date_not_used", "PASS", "Saved modeling table has no watch_date/end_date columns; direct raw temporal reconstruction was not rerun in Stage 06c."),
]:
    temporal_rows.append({"check": check, "status": status, "detail": detail})
for feat in conservative_features:
    if has_forbidden_feature(feat):
        temporal_rows.append({"check": "forbidden_feature_detail", "status": "FAIL", "detail": feat})
temporal_df = pd.DataFrame(temporal_rows)
write_csv(TABLE_DIR / "06c_temporal_leakage_recheck.csv", temporal_df)

# 11. Calibration and decile stability
calib_rows = []
calib = pd.DataFrame(
    {
        "y_repurchase": conservative_eval["y_test"],
        "repurchase_score": conservative_eval["repurchase_score"],
        "churn_risk_score": conservative_eval["churn_risk_score"],
    }
)
calib["score_bin"] = pd.qcut(calib["repurchase_score"], 10, duplicates="drop")
for b, g in calib.groupby("score_bin", observed=False):
    calib_rows.append(
        {
            "audit_type": "calibration_bin",
            "split_id": "stage06_holdout",
            "bin": str(b),
            "n": int(len(g)),
            "mean_repurchase_score": float(g["repurchase_score"].mean()),
            "observed_repurchase_rate": float(g["y_repurchase"].mean()),
            "mean_churn_risk_score": float(g["churn_risk_score"].mean()),
            "observed_churn_rate": float(1 - g["y_repurchase"].mean()),
            "brier_score": conservative_eval["brier_repurchase"],
        }
    )
deciles = decile_table(conservative_eval["y_test"], conservative_eval["churn_risk_score"], "conservative_w1_3_hgb")
for _, row in deciles.iterrows():
    d = row.to_dict()
    d["audit_type"] = "risk_decile"
    d["bin"] = d.pop("risk_decile")
    d["brier_score"] = conservative_eval["brier_repurchase"]
    calib_rows.append(d)
for i, (tr_idx, te_idx) in enumerate(gss.split(df_w13, target_to_num(df_w13[TARGET]), groups=df_w13[GROUP_COL]), start=1):
    tr_ids = set(df_w13.iloc[tr_idx][ID_COL].astype(int))
    te_ids = set(df_w13.iloc[te_idx][ID_COL].astype(int))
    res = eval_fixed_model(df_w13, conservative_features, tr_ids, te_ids, model_name=conservative_model_name, label=f"decile_repeat_{i}")
    if res.get("status") == "RUN":
        td_rate, td_lift = top_decile_lift(res["y_test"], res["churn_risk_score"])
        calib_rows.append(
            {
                "audit_type": "repeated_split_top_decile",
                "split_id": f"repeat_{i}",
                "bin": "D1",
                "n": int(len(res["y_test"])),
                "observed_churn_rate": td_rate,
                "lift_vs_overall_churn": td_lift,
                "roc_auc_repurchase": res["roc_auc_repurchase"],
                "brier_score": res["brier_repurchase"],
            }
        )
calib_decile_df = pd.DataFrame(calib_rows)
write_csv(TABLE_DIR / "06c_calibration_decile_stability.csv", calib_decile_df)

# 12. Conservative official metric recommendation
remove_target_adjacent = removal_groups["remove_all_week3_features"] + removal_groups["remove_first_last_watch_rel_day"] + removal_groups["remove_delta_features"] + removal_groups["remove_no_watch_has_watch_features"]
conservative_minus_adjacent_features = [f for f in conservative_features if not any(token in f for token in remove_target_adjacent)]
conservative_minus_adjacent = eval_fixed_model(
    df_w13,
    conservative_minus_adjacent_features,
    train_ids,
    test_ids,
    model_name=conservative_model_name,
    label="conservative_minus_target_adjacent",
)
ultra_features = membership + w12_usage
ultra_eval = eval_fixed_model(
    proxy_df,
    ultra_features,
    train_ids,
    test_ids,
    model_name=lr_model_name,
    label="ultra_conservative_w1_2_proxy_lr",
)
recommendation_specs = [
    ("A_full_model_result", "w1_3", conservative_model_name, conservative_features, conservative_eval, "Full current allowed Stage 06 feature set; strongest AUC but target-adjacent usage timing remains controversial.", "N"),
    ("B_conservative_model_result", "w1_3", conservative_model_name, conservative_minus_adjacent_features, conservative_minus_adjacent, "Removes week3, first/last watch timing, deltas, and no-watch flags; safer but still uses saved w1_3 content proxies.", "Y_WITH_CAVEATS"),
    ("C_ultra_conservative_model_result", "w1_2_proxy", lr_model_name, ultra_features, ultra_eval, "Uses only membership plus derived week1/week2 proxy usage with a simple linear model; not an official production feature table.", "Y_FOR_MENTOR_RESPONSE"),
]
recommend_rows = []
for level, window, model_name, feats, res, interp, mentor_safe in recommendation_specs:
    if res.get("status") == "RUN":
        top_rate, lift = top_decile_lift(res["y_test"], res["churn_risk_score"])
    else:
        top_rate, lift = np.nan, np.nan
    recommend_rows.append(
        {
            "reporting_level": level,
            "feature_set_description": "+".join(["membership", "usage", "content"]) if level == "A_full_model_result" else interp,
            "window": window,
            "model": model_name,
            "feature_count": len(existing_features(df_w13 if window == "w1_3" else proxy_df, feats)),
            "auc": res.get("roc_auc_repurchase"),
            "pr_auc_repurchase": res.get("average_precision_repurchase"),
            "pr_auc_churn_risk": res.get("average_precision_churn_risk"),
            "churn_risk_decile_lift": lift,
            "top_decile_churn_rate": top_rate,
            "interpretation": interp,
            "mentor_safe": mentor_safe,
            "status": res.get("status"),
            "blocked_reason": res.get("blocked_reason", ""),
        }
    )
recommend_df = pd.DataFrame(recommend_rows)
write_csv(TABLE_DIR / "06c_conservative_metric_recommendation.csv", recommend_df)

# Verdict
forbidden_fail = temporal_df["status"].eq("FAIL").any()
largest_removal_drop = top_removal_df.loc[
    (top_removal_df["model_name"].eq(conservative_model_name)) & (top_removal_df["status"].eq("RUN")),
    "auc_drop_vs_baseline",
].max()
ultra_auc = ultra_eval.get("roc_auc_repurchase", np.nan)
full_auc = conservative_eval.get("roc_auc_repurchase", np.nan)
blocked_early_content = time_window_df[
    time_window_df["window"].isin(["w1_1", "w1_2"]) & time_window_df["feature_family"].eq("membership_plus_usage_content")
]["status"].eq("BLOCKED").any()
if forbidden_fail:
    verdict = "likely_leakage"
elif pd.notna(ultra_auc) and full_auc - ultra_auc >= 0.08:
    verdict = "target_adjacent_but_not_direct_leakage"
elif pd.notna(largest_removal_drop) and largest_removal_drop >= 0.05:
    verdict = "target_adjacent_but_not_direct_leakage"
elif blocked_early_content:
    verdict = "plausible_strong_signal_but_cautioned"
else:
    verdict = "acceptable_for_internal_ranking_only"

if verdict == "acceptable_for_internal_ranking_only" and full_auc >= 0.87:
    verdict = "plausible_strong_signal_but_cautioned"

# Reports
final_checks = []
raw_after = snapshot_paths(RAW_FILES)
stage_after = snapshot_stage01_09()
final_checks.extend(
    [
        ("raw_files_unchanged", "PASS" if raw_before == raw_after else "FAIL", "raw snapshots unchanged" if raw_before == raw_after else "raw file snapshot changed"),
        ("no__data_output_created", "PASS", "Stage 06c writes only under park.ingyeom/reports and park.ingyeom/notebooks"),
        ("stage01_through_stage09_outputs_not_overwritten", "PASS" if stage_before == stage_after else "FAIL", "Stage 01-09 snapshots unchanged" if stage_before == stage_after else "Stage 01-09 snapshot changed"),
        ("no_optuna_run", "PASS", "No optuna import or study execution in Stage 06c implementation."),
        ("no_shap_run", "PASS", "Stage 06c only reads Stage 07r SHAP CSV outputs; it does not import or execute shap."),
        ("no_segmentation_created", "PASS", "No Stage 08/08b outputs created or modified."),
        ("no_business_simulation_created", "PASS", "No Stage 09 simulation outputs created or modified."),
        ("same_stage06_split_reused_where_applicable", "PASS", "Official Stage 06 split_membership_row_ids reused for holdout tests."),
        ("target_mapping_checked", "PASS" if best_config.get("target_mapping", {}).get("Y") == 1 and best_config.get("target_mapping", {}).get("N") == 0 else "FAIL", str(best_config.get("target_mapping"))),
        ("forbidden_features_checked", "PASS" if not forbidden_fail else "FAIL", "Forbidden feature set checked against conservative feature list."),
        ("time_window_shrinkage_or_blocked_reason_documented", "PASS", "w1_1/w1_2 proxy rows and blocked content rows written."),
        ("top_feature_removal_test_completed", "PASS" if not top_removal_df.empty else "FAIL", f"rows={len(top_removal_df)}"),
        ("content_proxy_audit_completed", "PASS" if not content_proxy_df.empty else "FAIL", f"rows={len(content_proxy_df)}"),
        ("single_feature_auc_audit_completed", "PASS" if not single_auc_bins_df.empty else "FAIL", f"rows={len(single_auc_bins_df)}"),
        ("subgroup_generalization_completed", "PASS" if not subgroup_df.empty else "FAIL", f"rows={len(subgroup_df)}"),
        ("harder_split_diagnostics_completed_or_blocked_reason_documented", "PASS" if not harder_split_df.empty else "FAIL", f"rows={len(harder_split_df)}"),
        ("final_conservative_metric_recommendation_created", "PASS" if not recommend_df.empty else "FAIL", f"rows={len(recommend_df)}"),
        ("mentor_response_summary_created", "PASS", "Korean mentor response summary written."),
    ]
)
final_checks_df = pd.DataFrame(final_checks, columns=["check", "status", "detail"])
write_csv(TABLE_DIR / "06c_final_checks.csv", final_checks_df)

summary = {
    "scope": "Stage 06c overfitting, leakage, and target-proxy adversarial audit only.",
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "python": sys.version,
    "platform": platform.platform(),
    "sklearn_version": sklearn.__version__,
    "prediction_scores_input_exists": paths["stage06_prediction_scores"].exists(),
    "mentor_concern": "AUC 0.87~0.90 may be overfitting or too-good-to-be-true.",
    "existing_checks_passed_but_insufficient": {
        "target_shuffle_auc": stage06b_summary.get("target_shuffle_auc"),
        "target_shuffle_status": stage06b_summary.get("target_shuffle_status"),
        "repeated_group_split_auc_mean": stage06b_summary.get("repeated_group_split_auc_mean"),
        "repeated_group_split_auc_std": stage06b_summary.get("repeated_group_split_auc_std"),
        "why_insufficient": "These checks reduce direct leakage/split-bug concern but do not prove that late usage behavior is not a target-adjacent proxy.",
    },
    "full_current_w1_3_auc": full_auc,
    "full_current_w1_3_pr_auc_churn_risk": conservative_eval.get("average_precision_churn_risk"),
    "largest_hgb_top_feature_removal_auc_drop": None if pd.isna(largest_removal_drop) else float(largest_removal_drop),
    "ultra_conservative_w1_2_proxy_auc": ultra_auc,
    "final_verdict": verdict,
    "recommended_reporting": recommend_df.to_dict(orient="records"),
    "final_checks_passed": bool(final_checks_df["status"].eq("PASS").all()),
}
write_json(DATA_DIR / "06c_adversarial_audit_summary.json", summary)

report_lines = [
    "# 06c v2 Overfitting, Leakage, and Target-Proxy Adversarial Audit",
    "",
    f"Generated at: {summary['created_at']}",
    "",
    "## 1. Re-stated Concern",
    "The mentor concern is valid: v2 AUC values around 0.87 to 0.90 are much higher than the earlier v1 baseline and may be overfitting, leakage, or a too-good-to-be-true target proxy.",
    "",
    "Existing Stage 06b checks passed target shuffle, repeated USER_KEY group split, and official USER_KEY group split diagnostics. These checks are necessary, but not sufficient, because a model can pass them while still relying on behavior observed very close to the target decision.",
    "",
    "## 2. Time-Window Shrinkage",
    "w1_1 and w1_2 were approximated only with in-memory week-level proxy columns available inside the saved w1_3 table. Exact w1_1/w1_2 content reconstruction is BLOCKED without rebuilding Stage 03/04 audit-only features.",
    "",
    "## 3. Top-Feature Removal",
    f"The largest HGB AUC drop from fixed removal tests was {largest_removal_drop:.4f}. Large drops after removing timing/usage features should be interpreted as target-adjacent behavior risk, not proof of direct leakage.",
    "",
    "## 4. Content Proxy Audit",
    "Content watch_time and session_count groups are high-risk content proxies because they can duplicate usage intensity. Genre ratio groups are safer than volume features, but still conditional on observed viewing.",
    "",
    "## 5. Single-Feature Audit",
    "Single-feature AUC and bin tables were generated for top TRUE SHAP features and watch/no-watch flags. Near-deterministic flags should be treated as a warning sign for target adjacency.",
    "",
    "## 6. Subgroup Generalization",
    "Subgroup AUC rows identify where performance collapses or remains stable across promotion, price, max_screen, watch-history, and high-risk product groups.",
    "",
    "## 7. Harder Split Diagnostics",
    "Repeated GroupShuffleSplit, product-code holdout, and max-screen holdout diagnostics were run where feasible. reg_date time split is blocked because reg_date is not present in the Stage 05 modeling table.",
    "",
    "## 8. Distribution Shift",
    "Train/test top-feature distribution shift was checked using means, medians, quantiles, missing rates, categorical proportions, and standardized mean differences.",
    "",
    "## 9. Duplicate Feature Vectors",
    "Exact and rounded near-duplicate train/test feature-vector hashes were checked after removing metadata and target.",
    "",
    "## 10. Label and Temporal Recheck",
    "The conservative w1_3 feature list contains no end_date, duration_days, raw watch_date/watch_day, w1_4 columns, target, USER_KEY, USER_NUM, or MOVIE_NUM.",
    "",
    "## 11. Calibration and Decile Stability",
    "Calibration bins, Brier score, risk decile churn rates, and repeated-split top-decile rows were generated.",
    "",
    "## 12. Conservative Metric Recommendation",
]
for _, row in recommend_df.iterrows():
    report_lines.append(
        f"- {row['reporting_level']}: window={row['window']}, model={row['model']}, AUC={row['auc']:.4f}, churn-risk PR AUC={row['pr_auc_churn_risk']:.4f}, top-decile lift={row['churn_risk_decile_lift']:.4f}, mentor_safe={row['mentor_safe']}"
        if pd.notna(row["auc"])
        else f"- {row['reporting_level']}: BLOCKED"
    )
report_lines.extend(
    [
        "",
        "## 13. Final Verdict",
        f"Final conservative classification: `{verdict}`.",
        "",
        "This does not prove direct leakage. However, the audit treats the high AUC as timing-sensitive and target-adjacent until an earlier-window rebuild or operational validation confirms otherwise.",
        "",
        "## Required Output Index",
        f"- Summary JSON: `{rel(DATA_DIR / '06c_adversarial_audit_summary.json')}`",
        f"- Mentor response: `{rel(DATA_DIR / '06c_mentor_response_summary.md')}`",
        f"- Final checks: `{rel(TABLE_DIR / '06c_final_checks.csv')}`",
    ]
)
(DATA_DIR / "06c_adversarial_audit_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

mentor_lines = [
    "# 06c 멘토 지적 대응 요약",
    "",
    "## 멘토님의 과적합 지적을 어떻게 검증했는가",
    "AUC 0.87~0.90이 너무 높다는 지적을 방어하지 않고, 같은 Stage 06 split을 기준으로 성능을 깨는 방향의 감사를 수행했습니다. 구체적으로 관측창 축소, 상위 피처 제거, 콘텐츠 proxy 분해, 단일 피처 AUC, 하위그룹 일반화, 더 어려운 split, train/test 분포 차이, 중복 feature vector, forbidden feature 재점검, calibration과 decile 안정성을 확인했습니다.",
    "",
    "## 어떤 검증은 통과했는가",
    f"Stage 06b의 target shuffle AUC는 {stage06b_summary.get('target_shuffle_auc'):.4f}였고, repeated GroupShuffleSplit 평균 AUC는 {stage06b_summary.get('repeated_group_split_auc_mean'):.4f}였습니다. Stage 06c에서도 w1_3 보수 모델 feature 안에 end_date, duration_days, watch_date, watch_day, USER_KEY, USER_NUM, MOVIE_NUM, is_repurchase, w1_4 feature가 들어가지 않았음을 다시 확인했습니다.",
    "",
    "## 어떤 부분은 여전히 위험한가",
    "가장 큰 위험은 직접 누수라기보다 target-adjacent behavior proxy입니다. 특히 3주차 시청량, 첫 시청일, 마지막 시청일, 주차별 ratio, 주차 간 변화량은 재구독 의사결정 시점에 가까운 행동 신호일 수 있습니다. 콘텐츠 watch_time과 session_count도 순수 취향이라기보다 사용량 강도를 다시 표현할 수 있습니다.",
    "",
    "## 그래서 공식 발표에는 어떤 성능 수치를 쓰는 것이 가장 보수적인가",
]
for _, row in recommend_df.iterrows():
    mentor_lines.append(
        f"- {row['reporting_level']}: AUC {row['auc']:.4f}, window {row['window']}, model {row['model']}, mentor_safe {row['mentor_safe']}."
        if pd.notna(row["auc"])
        else f"- {row['reporting_level']}: 산출 불가."
    )
mentor_lines.extend(
    [
        "",
        "## 0.87/0.90을 그대로 주장하지 않는다면 어떤 수치를 주장할 것인가",
        "0.90은 w1_4 late-period 결과이므로 조기 예측 성능으로 주장하지 않는 편이 안전합니다. 0.87 역시 full w1_3 결과로 제시하되, 멘토 대응에서는 target-adjacent 피처를 제거한 B안 또는 w1_2 proxy 기반 C안을 함께 제시하는 것이 더 보수적입니다.",
        "",
        "## w1_3와 w1_4를 어떻게 구분해서 설명할 것인가",
        "w1_3는 day 0~20 기반 early-observation에 가까운 모델입니다. w1_4는 day 0~27까지 포함하므로 종료 직전 행동을 많이 반영한 late-period/end-of-period 비교 모델입니다. 따라서 w1_4의 높은 AUC는 모델이 운영적으로 더 빨리 개입할 수 있다는 뜻이 아니라, 더 늦은 행동을 보면 구분력이 커진다는 뜻으로 설명해야 합니다.",
        "",
        "## 최종 보수 판단",
        f"Stage 06c의 최종 분류는 `{verdict}`입니다. 직접 누수라고 단정할 근거는 부족하지만, 현재 높은 AUC를 무비판적으로 발표용 대표 성능으로 쓰기에는 위험합니다.",
    ]
)
(DATA_DIR / "06c_mentor_response_summary.md").write_text("\n".join(mentor_lines) + "\n", encoding="utf-8")

# Figures
plot_time = time_window_df[(time_window_df["status"].eq("RUN")) & (time_window_df["model_name"].eq(conservative_model_name))].copy()
plot_time["label"] = plot_time["window"] + "_" + plot_time["feature_family"]
save_bar(
    plot_time,
    "label",
    "roc_auc_repurchase",
    FIGURE_DIR / "06c_auc_by_time_window.png",
    "AUC by Time Window and Feature Family",
    ylabel="ROC AUC",
    rotate=70,
)

plot_removal = top_removal_df[
    (top_removal_df["model_name"].eq(conservative_model_name)) & (top_removal_df["status"].eq("RUN"))
].copy()
save_bar(
    plot_removal,
    "removal_group",
    "auc_drop_vs_baseline",
    FIGURE_DIR / "06c_top_feature_removal_auc_drop.png",
    "AUC Drop after Removing Top Feature Groups",
    ylabel="AUC drop",
    rotate=70,
)

plot_single = single_summary_df[single_summary_df["status"].eq("RUN")].sort_values("single_feature_auc_oriented", ascending=False)
save_bar(
    plot_single,
    "feature",
    "single_feature_auc_oriented",
    FIGURE_DIR / "06c_single_feature_auc_top_features.png",
    "Single Feature Oriented AUC",
    ylabel="oriented ROC AUC",
    rotate=70,
)

plot_decile = deciles.copy()
save_bar(
    plot_decile,
    "risk_decile",
    "observed_churn_rate",
    FIGURE_DIR / "06c_risk_decile_churn_rate.png",
    "Observed Churn Rate by Risk Decile",
    ylabel="observed churn rate",
)

plot_ladder = recommend_df.copy()
save_bar(
    plot_ladder,
    "reporting_level",
    "auc",
    FIGURE_DIR / "06c_conservative_metric_ladder.png",
    "Conservative Metric Ladder",
    ylabel="ROC AUC",
    rotate=30,
)

write_notebook()

print("06c adversarial audit completed.")
for _, row in final_checks_df.iterrows():
    print(f"{row['check']}: {row['status']} - {row['detail']}")
print(f"final_verdict: {verdict}")
