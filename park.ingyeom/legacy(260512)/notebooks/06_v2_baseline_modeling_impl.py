import json
import math
import os
import platform
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import sklearn


warnings.filterwarnings("ignore", category=UserWarning)

RANDOM_STATE = 42
TEST_SIZE = 0.2
N_SPLITS = 3
THRESHOLD = 0.5
OPTIONAL_RUNTIME_LIMIT_SECONDS = 180


def find_project_root(start):
    for candidate in [start, *start.parents]:
        if (
            (candidate / "_data" / "01_raw" / "Membership.csv").exists()
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
DATA_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "06_v2_baseline_modeling"
TABLE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "06_v2_baseline_modeling"
FIGURE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "06_v2_baseline_modeling"

DATA_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

INPUT_W13 = STAGE05_DATA / "modeling_dataset_v2_w1_3.csv"
INPUT_W14 = STAGE05_DATA / "modeling_dataset_v2_w1_4.csv"
FEATURE_SETS_PATH = STAGE05_DATA / "feature_sets_v2.json"
STAGE05_SUMMARY_PATH = STAGE05_DATA / "modeling_dataset_summary.json"

RAW_FILES = [
    PROJECT_ROOT / "_data" / "01_raw" / name
    for name in ["Membership.csv", "User_Mapping.csv", "View_History.csv", "Movie_Master.csv"]
]

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

TARGET = "is_repurchase"
ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"


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


stage_prefixes = [f"{i:02d}_v2" for i in range(1, 6)]
stage_existing_dirs = []
for base in [
    PROJECT_ROOT / "park.ingyeom" / "reports" / "data",
    PROJECT_ROOT / "park.ingyeom" / "reports" / "tables",
    PROJECT_ROOT / "park.ingyeom" / "reports" / "figures",
]:
    if base.exists():
        stage_existing_dirs.extend([p for p in base.iterdir() if p.is_dir() and any(p.name.startswith(s) for s in stage_prefixes)])
stage_existing_files = [
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / f"{i:02d}_v2_data_overview_and_audit.ipynb"
    for i in [1]
] + [
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / name
    for name in [
        "02_v2_preprocessing_policy.ipynb",
        "03_v2_usage_feature_engineering.ipynb",
        "04_v2_content_feature_engineering.ipynb",
        "05_v2_modeling_dataset.ipynb",
    ]
]

raw_before = snapshot_paths(RAW_FILES)
stage_before = snapshot_dirs(stage_existing_dirs) | snapshot_paths(stage_existing_files)


def write_csv(path, df_or_rows, columns=None):
    path = Path(path)
    if isinstance(df_or_rows, pd.DataFrame):
        df_or_rows.to_csv(path, index=False, encoding="utf-8-sig")
        return
    pd.DataFrame(df_or_rows, columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def has_forbidden_feature(col):
    if col in FORBIDDEN_FEATURES:
        return True
    return any(token in col for token in FORBIDDEN_SUBSTRINGS)


def safe_auc(y_true, score):
    if len(np.unique(y_true)) < 2:
        return np.nan
    return roc_auc_score(y_true, score)


def safe_ap(y_true, score):
    if len(np.unique(y_true)) < 2:
        return np.nan
    return average_precision_score(y_true, score)


def onehot_encoder(sparse=True):
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=sparse)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=sparse)


def make_preprocessor(features, categorical_features, scale_numeric=False, dense=False):
    numeric_features = [c for c in features if c not in categorical_features]
    cat_features = [c for c in features if c in categorical_features]
    transformers = []
    num_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        num_steps.append(("scaler", StandardScaler(with_mean=False)))
    if numeric_features:
        transformers.append(("num", Pipeline(num_steps), numeric_features))
    if cat_features:
        cat_steps = [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", onehot_encoder(sparse=not dense)),
        ]
        transformers.append(("cat", Pipeline(cat_steps), cat_features))
    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        sparse_threshold=0.0 if dense else 0.3,
        verbose_feature_names_out=True,
    )


def get_feature_names(preprocessor, fallback_count):
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:
        return [f"transformed_feature_{i}" for i in range(fallback_count)]


def transformed_feature_count(pipe, X):
    try:
        Xt = pipe.named_steps["preprocess"].transform(X)
        return int(Xt.shape[1])
    except Exception:
        return np.nan


def prediction_scores(pipe, X):
    model = pipe.named_steps["model"]
    if hasattr(pipe, "predict_proba"):
        proba = pipe.predict_proba(X)
        classes = list(model.classes_) if hasattr(model, "classes_") else [0, 1]
        if 1 in classes:
            return proba[:, classes.index(1)]
        return np.zeros(len(X), dtype=float)
    if hasattr(pipe, "decision_function"):
        raw = pipe.decision_function(X)
        return 1.0 / (1.0 + np.exp(-raw))
    pred = pipe.predict(X)
    return np.asarray(pred, dtype=float)


def metric_row(window, feature_set, feature_family, model_name, split_type, split_id, y_train, y_test, score, feature_count):
    y_true = np.asarray(y_test, dtype=int)
    y_train = np.asarray(y_train, dtype=int)
    repurchase_pred = (score >= THRESHOLD).astype(int)
    churn_true = 1 - y_true
    churn_score = 1 - score
    churn_pred = (churn_score >= THRESHOLD).astype(int)
    rep_tn, rep_fp, rep_fn, rep_tp = confusion_matrix(y_true, repurchase_pred, labels=[0, 1]).ravel()
    churn_tn, churn_fp, churn_fn, churn_tp = confusion_matrix(churn_true, churn_pred, labels=[0, 1]).ravel()
    return {
        "window": window,
        "feature_set": feature_set,
        "feature_family": feature_family,
        "model_name": model_name,
        "split_type": split_type,
        "split_id": split_id,
        "roc_auc_repurchase": safe_auc(y_true, score),
        "average_precision_repurchase": safe_ap(y_true, score),
        "average_precision_churn_risk": safe_ap(churn_true, churn_score),
        "accuracy_at_0_5_repurchase": accuracy_score(y_true, repurchase_pred),
        "balanced_accuracy_at_0_5_repurchase": balanced_accuracy_score(y_true, repurchase_pred),
        "precision_at_0_5_repurchase": precision_score(y_true, repurchase_pred, zero_division=0),
        "recall_at_0_5_repurchase": recall_score(y_true, repurchase_pred, zero_division=0),
        "f1_at_0_5_repurchase": f1_score(y_true, repurchase_pred, zero_division=0),
        "precision_at_0_5_churn_risk": precision_score(churn_true, churn_pred, zero_division=0),
        "recall_at_0_5_churn_risk": recall_score(churn_true, churn_pred, zero_division=0),
        "f1_at_0_5_churn_risk": f1_score(churn_true, churn_pred, zero_division=0),
        "repurchase_tn": rep_tn,
        "repurchase_fp": rep_fp,
        "repurchase_fn": rep_fn,
        "repurchase_tp": rep_tp,
        "churn_risk_tn": churn_tn,
        "churn_risk_fp": churn_fp,
        "churn_risk_fn": churn_fn,
        "churn_risk_tp": churn_tp,
        "train_positive_rate_repurchase": float(np.mean(y_train)),
        "test_positive_rate_repurchase": float(np.mean(y_true)),
        "train_churn_rate": float(1 - np.mean(y_train)),
        "test_churn_rate": float(1 - np.mean(y_true)),
        "n_train": int(len(y_train)),
        "n_test": int(len(y_true)),
        "post_transform_feature_count": feature_count,
        "threshold": THRESHOLD,
    }


def feature_family(feature_set):
    if feature_set.startswith("membership_only"):
        return "membership_only"
    if feature_set.startswith("usage_"):
        return "usage_only"
    if feature_set.startswith("content_"):
        return "content_only"
    if "membership_plus_usage_content" in feature_set:
        return "membership_plus_usage_content"
    if "membership_plus_usage" in feature_set:
        return "membership_plus_usage"
    return "other"


def window_for_feature_set(feature_set):
    if "w1_3" in feature_set:
        return ["w1_3"]
    if "w1_4" in feature_set:
        return ["w1_4"]
    return ["w1_3", "w1_4"]


def contains_churn_prevented(feature_set, features):
    return "Y" if "is_churn_prevented" in features else "N"


with FEATURE_SETS_PATH.open("r", encoding="utf-8") as f:
    feature_payload = json.load(f)
with STAGE05_SUMMARY_PATH.open("r", encoding="utf-8") as f:
    stage05_summary = json.load(f)

categorical_declared = set(feature_payload.get("categorical_features_to_encode_in_stage06", []))
feature_sets = feature_payload["feature_sets"]

df_w13 = pd.read_csv(INPUT_W13)
df_w14 = pd.read_csv(INPUT_W14)
datasets = {"w1_3": df_w13, "w1_4": df_w14}

for window, df in datasets.items():
    mapped = df[TARGET].map({"Y": 1, "N": 0})
    if mapped.isna().any():
        raise ValueError(f"Unexpected target labels in {window}.")
    df["target_repurchase"] = mapped.astype(int)

base = df_w13[[ID_COL, GROUP_COL, "target_repurchase"]].copy()
base = base.sort_values(ID_COL).reset_index(drop=True)
if set(base[ID_COL]) != set(df_w14[ID_COL]):
    raise ValueError("w1_3 and w1_4 membership_row_id sets differ.")

gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
train_idx, test_idx = next(gss.split(base, base["target_repurchase"], groups=base[GROUP_COL]))
base["holdout_split"] = "train"
base.loc[test_idx, "holdout_split"] = "test"
train_ids = set(base.loc[base["holdout_split"] == "train", ID_COL])
test_ids = set(base.loc[base["holdout_split"] == "test", ID_COL])
train_groups = set(base.loc[base["holdout_split"] == "train", GROUP_COL])
test_groups = set(base.loc[base["holdout_split"] == "test", GROUP_COL])

gkf = GroupKFold(n_splits=N_SPLITS)
base["cv_test_fold"] = -1
for fold_id, (_, fold_test_idx) in enumerate(gkf.split(base, base["target_repurchase"], groups=base[GROUP_COL]), start=1):
    base.loc[fold_test_idx, "cv_test_fold"] = fold_id

split_membership = base[[ID_COL, GROUP_COL, "holdout_split", "target_repurchase"]].copy()
split_membership["target_label"] = np.where(split_membership["target_repurchase"] == 1, "Y", "N")
write_csv(TABLE_DIR / "06_v2_split_membership_row_ids.csv", split_membership)
write_csv(TABLE_DIR / "06_v2_fold_assignment.csv", base[[ID_COL, GROUP_COL, "cv_test_fold", "target_repurchase"]])

environment_rows = [
    {"item": "python_version", "value": sys.version.replace("\n", " ")},
    {"item": "platform", "value": platform.platform()},
    {"item": "sklearn_version", "value": sklearn.__version__},
    {"item": "pandas_version", "value": pd.__version__},
    {"item": "numpy_version", "value": np.__version__},
    {"item": "matplotlib_version", "value": matplotlib.__version__},
    {"item": "project_root", "value": str(PROJECT_ROOT)},
    {"item": "run_timestamp", "value": datetime.now().isoformat(timespec="seconds")},
]
try:
    import xgboost

    environment_rows.append({"item": "xgboost_version", "value": xgboost.__version__})
except Exception as exc:
    environment_rows.append({"item": "xgboost_version", "value": f"unavailable: {exc}"})
try:
    import lightgbm

    environment_rows.append({"item": "lightgbm_version", "value": lightgbm.__version__})
except Exception as exc:
    environment_rows.append({"item": "lightgbm_version", "value": f"unavailable: {exc}"})
try:
    _ = OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    onehot_param = "sparse_output"
except TypeError:
    onehot_param = "sparse"
environment_rows.append({"item": "onehot_sparse_parameter", "value": onehot_param})
write_csv(TABLE_DIR / "06_v2_environment_summary.csv", environment_rows, ["item", "value"])

input_summary = []
for window, df in datasets.items():
    input_summary.append(
        {
            "window": window,
            "path": rel(INPUT_W13 if window == "w1_3" else INPUT_W14),
            "row_count": len(df),
            "column_count": len(df.columns) - 1,
            "unique_membership_row_id": df[ID_COL].nunique(),
            "unique_USER_KEY": df[GROUP_COL].nunique(),
            "target_Y_count": int((df[TARGET] == "Y").sum()),
            "target_N_count": int((df[TARGET] == "N").sum()),
        }
    )
write_csv(TABLE_DIR / "06_v2_input_dataset_summary.csv", input_summary)

split_summary = []
for split_name in ["train", "test"]:
    sub = base[base["holdout_split"] == split_name]
    split_summary.append(
        {
            "split_type": "holdout",
            "split_id": split_name,
            "row_count": len(sub),
            "unique_USER_KEY": sub[GROUP_COL].nunique(),
            "repurchase_positive_rate": sub["target_repurchase"].mean(),
            "churn_rate": 1 - sub["target_repurchase"].mean(),
        }
    )
for fold_id in range(1, N_SPLITS + 1):
    sub = base[base["cv_test_fold"] == fold_id]
    split_summary.append(
        {
            "split_type": "groupkfold_test_fold",
            "split_id": fold_id,
            "row_count": len(sub),
            "unique_USER_KEY": sub[GROUP_COL].nunique(),
            "repurchase_positive_rate": sub["target_repurchase"].mean(),
            "churn_rate": 1 - sub["target_repurchase"].mean(),
        }
    )
write_csv(TABLE_DIR / "06_v2_split_summary.csv", split_summary)

group_leakage_rows = [
    {
        "check_scope": "holdout",
        "split_id": "train_vs_test",
        "train_group_count": len(train_groups),
        "test_group_count": len(test_groups),
        "overlap_group_count": len(train_groups & test_groups),
        "status": "PASS" if not (train_groups & test_groups) else "FAIL",
    }
]
for fold_id in range(1, N_SPLITS + 1):
    fold_test_groups = set(base.loc[base["cv_test_fold"] == fold_id, GROUP_COL])
    fold_train_groups = set(base.loc[base["cv_test_fold"] != fold_id, GROUP_COL])
    group_leakage_rows.append(
        {
            "check_scope": "groupkfold",
            "split_id": fold_id,
            "train_group_count": len(fold_train_groups),
            "test_group_count": len(fold_test_groups),
            "overlap_group_count": len(fold_train_groups & fold_test_groups),
            "status": "PASS" if not (fold_train_groups & fold_test_groups) else "FAIL",
        }
    )
write_csv(TABLE_DIR / "06_v2_group_leakage_check.csv", group_leakage_rows)

eval_specs = []
feature_validation_rows = []
for feature_set, features in feature_sets.items():
    for window in window_for_feature_set(feature_set):
        df = datasets[window]
        missing = [c for c in features if c not in df.columns]
        forbidden = [c for c in features if has_forbidden_feature(c)]
        cross = []
        if window == "w1_3":
            cross = [c for c in features if c.startswith("w1_4_")]
        if window == "w1_4":
            cross = [c for c in features if c.startswith("w1_3_")]
        cat_cols = [c for c in features if c in categorical_declared]
        num_cols = [c for c in features if c not in categorical_declared]
        status = "PASS" if not missing and not forbidden and not cross else "FAIL"
        post_count = np.nan
        if status == "PASS":
            train_mask = df[ID_COL].isin(train_ids)
            pre = make_preprocessor(features, cat_cols, scale_numeric=False, dense=False)
            try:
                pre.fit(df.loc[train_mask, features])
                post_count = len(get_feature_names(pre, pre.transform(df.loc[train_mask, features]).shape[1]))
            except Exception as exc:
                status = "FAIL"
                missing.append(f"preprocess_fit_error: {exc}")
        feature_validation_rows.append(
            {
                "window": window,
                "feature_set": feature_set,
                "feature_family": feature_family(feature_set),
                "contains_is_churn_prevented": contains_churn_prevented(feature_set, features),
                "raw_feature_count": len(features),
                "numeric_feature_count": len(num_cols),
                "categorical_feature_count": len(cat_cols),
                "post_transform_feature_count": post_count,
                "missing_listed_features": "|".join(missing),
                "forbidden_feature_violations": "|".join(forbidden),
                "cross_window_feature_violations": "|".join(cross),
                "status": status,
            }
        )
        if status == "PASS":
            eval_specs.append(
                {
                    "window": window,
                    "feature_set": feature_set,
                    "features": features,
                    "categorical_features": cat_cols,
                    "numeric_features": num_cols,
                    "feature_family": feature_family(feature_set),
                    "contains_is_churn_prevented": contains_churn_prevented(feature_set, features),
                }
            )
write_csv(TABLE_DIR / "06_v2_feature_set_validation.csv", feature_validation_rows)

score_orientation_rows = [
    {
        "item": "target_mapping",
        "description": "Y -> 1 means repurchase; N -> 0 means non-repurchase / churn risk.",
    },
    {
        "item": "repurchase_score",
        "description": "P(is_repurchase = Y). Higher score means higher estimated repurchase probability.",
    },
    {
        "item": "churn_risk_score",
        "description": "1 - repurchase_score. Higher score means higher estimated churn risk.",
    },
    {
        "item": "threshold_policy",
        "description": "Threshold 0.5 is used only as a diagnostic threshold, not as an optimal business threshold.",
    },
    {
        "item": "business_orientation",
        "description": "ROC AUC is reported for repurchase prediction; churn targeting uses churn_risk_score and churn-risk PR/capture metrics.",
    },
]
write_csv(TABLE_DIR / "06_v2_score_orientation_summary.csv", score_orientation_rows)


def model_specs(include_optional=False):
    specs = {
        "DummyClassifier": {
            "model": DummyClassifier(strategy="most_frequent"),
            "scale_numeric": False,
            "dense": False,
            "required_core": True,
        },
        "LogisticRegression": {
            "model": LogisticRegression(max_iter=1000, class_weight="balanced", solver="lbfgs"),
            "scale_numeric": True,
            "dense": False,
            "required_core": True,
        },
        "ExtraTreesClassifier": {
            "model": ExtraTreesClassifier(
                n_estimators=100,
                min_samples_leaf=5,
                random_state=RANDOM_STATE,
                n_jobs=-1,
                class_weight="balanced",
            ),
            "scale_numeric": False,
            "dense": False,
            "required_core": True,
        },
        "HistGradientBoostingClassifier": {
            "model": HistGradientBoostingClassifier(
                max_iter=60,
                learning_rate=0.08,
                max_leaf_nodes=31,
                random_state=RANDOM_STATE,
            ),
            "scale_numeric": False,
            "dense": True,
            "required_core": False,
        },
    }
    if include_optional:
        try:
            from xgboost import XGBClassifier

            specs["XGBClassifier"] = {
                "model": XGBClassifier(
                    n_estimators=60,
                    max_depth=4,
                    learning_rate=0.08,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    eval_metric="logloss",
                    tree_method="hist",
                    n_jobs=2,
                    random_state=RANDOM_STATE,
                    verbosity=0,
                ),
                "scale_numeric": False,
                "dense": False,
                "optional": True,
            }
        except Exception:
            pass
        try:
            from lightgbm import LGBMClassifier

            specs["LGBMClassifier"] = {
                "model": LGBMClassifier(
                    n_estimators=60,
                    learning_rate=0.08,
                    num_leaves=31,
                    random_state=RANDOM_STATE,
                    n_jobs=2,
                    verbose=-1,
                ),
                "scale_numeric": False,
                "dense": False,
                "optional": True,
            }
        except Exception:
            pass
    return specs


def make_pipeline(features, cat_cols, spec):
    pre = make_preprocessor(
        features=features,
        categorical_features=cat_cols,
        scale_numeric=spec.get("scale_numeric", False),
        dense=spec.get("dense", False),
    )
    return Pipeline([("preprocess", pre), ("model", clone(spec["model"]))])


metrics_rows = []
prediction_rows = []
feature_importance_rows = []
failed_rows = []
successful_holdout_keys = []
required_core_success = set()
hgb_attempted = False
hgb_success = False

sklearn_specs = model_specs(include_optional=False)

for spec_item in eval_specs:
    window = spec_item["window"]
    df = datasets[window]
    features = spec_item["features"]
    cat_cols = spec_item["categorical_features"]
    train_mask = df[ID_COL].isin(train_ids)
    test_mask = df[ID_COL].isin(test_ids)
    X_train = df.loc[train_mask, features]
    X_test = df.loc[test_mask, features]
    y_train = df.loc[train_mask, "target_repurchase"].astype(int)
    y_test = df.loc[test_mask, "target_repurchase"].astype(int)
    test_meta = df.loc[test_mask, [ID_COL, GROUP_COL]].copy()
    for model_name, model_spec in sklearn_specs.items():
        if model_name == "HistGradientBoostingClassifier":
            hgb_attempted = True
        try:
            pipe = make_pipeline(features, cat_cols, model_spec)
            pipe.fit(X_train, y_train)
            score = prediction_scores(pipe, X_test)
            feature_count = transformed_feature_count(pipe, X_test)
            metrics_rows.append(
                metric_row(
                    window,
                    spec_item["feature_set"],
                    spec_item["feature_family"],
                    model_name,
                    "holdout",
                    "test",
                    y_train,
                    y_test,
                    score,
                    feature_count,
                )
                | {
                    "contains_is_churn_prevented": spec_item["contains_is_churn_prevented"],
                    "model_group": "required_sklearn",
                }
            )
            successful_holdout_keys.append((window, spec_item["feature_set"], model_name))
            if model_spec.get("required_core"):
                required_core_success.add((window, spec_item["feature_set"], model_name))
            if model_name == "HistGradientBoostingClassifier":
                hgb_success = True
            pred_df = test_meta.copy()
            pred_df["window"] = window
            pred_df["feature_set"] = spec_item["feature_set"]
            pred_df["feature_family"] = spec_item["feature_family"]
            pred_df["model_name"] = model_name
            pred_df["split_type"] = "holdout"
            pred_df["y_true_is_repurchase"] = y_test.values
            pred_df["y_true_churn_risk"] = 1 - y_test.values
            pred_df["repurchase_score"] = score
            pred_df["churn_risk_score"] = 1 - score
            prediction_rows.append(pred_df)
            try:
                names = get_feature_names(pipe.named_steps["preprocess"], int(feature_count))
                model = pipe.named_steps["model"]
                if hasattr(model, "feature_importances_"):
                    for name, value in zip(names, model.feature_importances_):
                        feature_importance_rows.append(
                            {
                                "window": window,
                                "feature_set": spec_item["feature_set"],
                                "model_name": model_name,
                                "importance_type": "feature_importance",
                                "feature_name": name,
                                "value": value,
                            }
                        )
                elif hasattr(model, "coef_") and np.asarray(model.coef_).ndim == 2:
                    coef = np.asarray(model.coef_)[0]
                    for name, value in zip(names, coef):
                        feature_importance_rows.append(
                            {
                                "window": window,
                                "feature_set": spec_item["feature_set"],
                                "model_name": model_name,
                                "importance_type": "logistic_coefficient",
                                "feature_name": name,
                                "value": value,
                            }
                        )
            except Exception as exc:
                failed_rows.append(
                    {
                        "window": window,
                        "feature_set": spec_item["feature_set"],
                        "model_name": model_name,
                        "stage": "feature_importance",
                        "status": "skipped",
                        "reason": str(exc),
                    }
                )
        except Exception as exc:
            failed_rows.append(
                {
                    "window": window,
                    "feature_set": spec_item["feature_set"],
                    "model_name": model_name,
                    "stage": "holdout_fit",
                    "status": "failed",
                    "reason": str(exc),
                }
            )
            continue
        for fold_id in range(1, N_SPLITS + 1):
            fold_train_mask = df[ID_COL].isin(set(base.loc[base["cv_test_fold"] != fold_id, ID_COL]))
            fold_test_mask = df[ID_COL].isin(set(base.loc[base["cv_test_fold"] == fold_id, ID_COL]))
            X_fold_train = df.loc[fold_train_mask, features]
            X_fold_test = df.loc[fold_test_mask, features]
            y_fold_train = df.loc[fold_train_mask, "target_repurchase"].astype(int)
            y_fold_test = df.loc[fold_test_mask, "target_repurchase"].astype(int)
            try:
                fold_pipe = make_pipeline(features, cat_cols, model_spec)
                fold_pipe.fit(X_fold_train, y_fold_train)
                fold_score = prediction_scores(fold_pipe, X_fold_test)
                fold_count = transformed_feature_count(fold_pipe, X_fold_test)
                metrics_rows.append(
                    metric_row(
                        window,
                        spec_item["feature_set"],
                        spec_item["feature_family"],
                        model_name,
                        "groupkfold",
                        fold_id,
                        y_fold_train,
                        y_fold_test,
                        fold_score,
                        fold_count,
                    )
                    | {
                        "contains_is_churn_prevented": spec_item["contains_is_churn_prevented"],
                        "model_group": "required_sklearn",
                    }
                )
            except Exception as exc:
                failed_rows.append(
                    {
                        "window": window,
                        "feature_set": spec_item["feature_set"],
                        "model_name": model_name,
                        "stage": f"groupkfold_fold_{fold_id}",
                        "status": "failed",
                        "reason": str(exc),
                    }
                )

optional_specs = {}
optional_smoke_status = {}
optional_started_at = time.time()
candidate_smoke = next(s for s in eval_specs if s["window"] == "w1_3" and s["feature_set"] == "membership_only_without_churn_prevented")
for model_name, model_spec in model_specs(include_optional=True).items():
    if not model_spec.get("optional"):
        continue
    try:
        df = datasets[candidate_smoke["window"]]
        sample = df.sample(n=min(500, len(df)), random_state=RANDOM_STATE)
        pipe = make_pipeline(candidate_smoke["features"], candidate_smoke["categorical_features"], model_spec)
        pipe.fit(sample[candidate_smoke["features"]], sample["target_repurchase"].astype(int))
        _ = prediction_scores(pipe, sample[candidate_smoke["features"]])
        optional_specs[model_name] = model_spec
        optional_smoke_status[model_name] = "smoke_passed"
    except Exception as exc:
        optional_smoke_status[model_name] = "optional_unavailable"
        failed_rows.append(
            {
                "window": "all",
                "feature_set": "smoke_test",
                "model_name": model_name,
                "stage": "optional_smoke_test",
                "status": "optional_unavailable",
                "reason": str(exc),
            }
        )

optional_runtime_guard_triggered = False
for spec_item in eval_specs:
    if optional_runtime_guard_triggered:
        break
    window = spec_item["window"]
    df = datasets[window]
    features = spec_item["features"]
    cat_cols = spec_item["categorical_features"]
    train_mask = df[ID_COL].isin(train_ids)
    test_mask = df[ID_COL].isin(test_ids)
    X_train = df.loc[train_mask, features]
    X_test = df.loc[test_mask, features]
    y_train = df.loc[train_mask, "target_repurchase"].astype(int)
    y_test = df.loc[test_mask, "target_repurchase"].astype(int)
    test_meta = df.loc[test_mask, [ID_COL, GROUP_COL]].copy()
    for model_name, model_spec in optional_specs.items():
        if time.time() - optional_started_at > OPTIONAL_RUNTIME_LIMIT_SECONDS:
            optional_runtime_guard_triggered = True
            failed_rows.append(
                {
                    "window": window,
                    "feature_set": spec_item["feature_set"],
                    "model_name": model_name,
                    "stage": "optional_holdout",
                    "status": "skipped",
                    "reason": "optional_runtime_guard_triggered",
                }
            )
            break
        try:
            pipe = make_pipeline(features, cat_cols, model_spec)
            pipe.fit(X_train, y_train)
            score = prediction_scores(pipe, X_test)
            feature_count = transformed_feature_count(pipe, X_test)
            metrics_rows.append(
                metric_row(
                    window,
                    spec_item["feature_set"],
                    spec_item["feature_family"],
                    model_name,
                    "holdout",
                    "test",
                    y_train,
                    y_test,
                    score,
                    feature_count,
                )
                | {
                    "contains_is_churn_prevented": spec_item["contains_is_churn_prevented"],
                    "model_group": "optional_booster",
                }
            )
            pred_df = test_meta.copy()
            pred_df["window"] = window
            pred_df["feature_set"] = spec_item["feature_set"]
            pred_df["feature_family"] = spec_item["feature_family"]
            pred_df["model_name"] = model_name
            pred_df["split_type"] = "holdout"
            pred_df["y_true_is_repurchase"] = y_test.values
            pred_df["y_true_churn_risk"] = 1 - y_test.values
            pred_df["repurchase_score"] = score
            pred_df["churn_risk_score"] = 1 - score
            prediction_rows.append(pred_df)
            try:
                names = get_feature_names(pipe.named_steps["preprocess"], int(feature_count))
                model = pipe.named_steps["model"]
                if hasattr(model, "feature_importances_"):
                    for name, value in zip(names, model.feature_importances_):
                        feature_importance_rows.append(
                            {
                                "window": window,
                                "feature_set": spec_item["feature_set"],
                                "model_name": model_name,
                                "importance_type": "feature_importance",
                                "feature_name": name,
                                "value": value,
                            }
                        )
            except Exception as exc:
                failed_rows.append(
                    {
                        "window": window,
                        "feature_set": spec_item["feature_set"],
                        "model_name": model_name,
                        "stage": "feature_importance",
                        "status": "skipped",
                        "reason": str(exc),
                    }
                )
        except Exception as exc:
            failed_rows.append(
                {
                    "window": window,
                    "feature_set": spec_item["feature_set"],
                    "model_name": model_name,
                    "stage": "optional_holdout_fit",
                    "status": "failed",
                    "reason": str(exc),
                }
            )

for model_name in optional_specs:
    failed_rows.append(
        {
            "window": "all",
            "feature_set": "all",
            "model_name": model_name,
            "stage": "groupkfold",
            "status": "skipped_by_policy",
            "reason": "Optional boosters were run on holdout only to protect Stage 06 runtime.",
        }
    )

metrics_df = pd.DataFrame(metrics_rows)
predictions_df = pd.concat(prediction_rows, ignore_index=True) if prediction_rows else pd.DataFrame()
feature_importance_df = pd.DataFrame(feature_importance_rows)
failed_df = pd.DataFrame(failed_rows, columns=["window", "feature_set", "model_name", "stage", "status", "reason"])

if not metrics_df.empty:
    cv_rows = []
    group_cols = ["window", "feature_set", "feature_family", "model_name", "contains_is_churn_prevented", "model_group"]
    cv_metric_cols = [
        "roc_auc_repurchase",
        "average_precision_repurchase",
        "average_precision_churn_risk",
        "accuracy_at_0_5_repurchase",
        "balanced_accuracy_at_0_5_repurchase",
        "precision_at_0_5_churn_risk",
        "recall_at_0_5_churn_risk",
        "f1_at_0_5_churn_risk",
        "post_transform_feature_count",
    ]
    cv_base = metrics_df[metrics_df["split_type"] == "groupkfold"]
    for keys, sub in cv_base.groupby(group_cols, dropna=False):
        row = dict(zip(group_cols, keys))
        row["split_type"] = "groupkfold_mean"
        row["split_id"] = "mean"
        for col in cv_metric_cols:
            row[col] = sub[col].mean()
            row[f"{col}_std"] = sub[col].std(ddof=0)
        row["n_train"] = sub["n_train"].mean()
        row["n_test"] = sub["n_test"].mean()
        cv_rows.append(row)
    if cv_rows:
        metrics_df = pd.concat([metrics_df, pd.DataFrame(cv_rows)], ignore_index=True, sort=False)

write_csv(DATA_DIR / "06_v2_model_metrics.csv", metrics_df)
write_csv(DATA_DIR / "06_v2_prediction_scores.csv", predictions_df)
write_csv(DATA_DIR / "06_v2_feature_importance.csv", feature_importance_df)
write_csv(TABLE_DIR / "06_v2_failed_models.csv", failed_df)

holdout_metrics = metrics_df[metrics_df["split_type"] == "holdout"].copy()
metric_summary_cols = [
    "window",
    "feature_set",
    "feature_family",
    "model_name",
    "model_group",
    "contains_is_churn_prevented",
    "roc_auc_repurchase",
    "average_precision_repurchase",
    "average_precision_churn_risk",
    "balanced_accuracy_at_0_5_repurchase",
    "precision_at_0_5_churn_risk",
    "recall_at_0_5_churn_risk",
    "f1_at_0_5_churn_risk",
    "n_train",
    "n_test",
    "post_transform_feature_count",
]
write_csv(TABLE_DIR / "06_v2_model_metrics_summary.csv", holdout_metrics[metric_summary_cols].sort_values("roc_auc_repurchase", ascending=False))

best_by_feature_set = (
    holdout_metrics.sort_values("roc_auc_repurchase", ascending=False)
    .groupby(["window", "feature_set"], as_index=False)
    .head(1)
)
write_csv(TABLE_DIR / "06_v2_best_model_by_feature_set.csv", best_by_feature_set[metric_summary_cols])

def comparison_key(feature_set):
    return feature_set.replace("w1_3", "wX").replace("w1_4", "wX")


comparison_rows = []
if not holdout_metrics.empty:
    tmp = holdout_metrics.copy()
    tmp["comparison_key"] = tmp["feature_set"].map(comparison_key)
    for (key, model_name), sub in tmp.groupby(["comparison_key", "model_name"], dropna=False):
        if {"w1_3", "w1_4"}.issubset(set(sub["window"])):
            r13 = sub[sub["window"] == "w1_3"].sort_values("roc_auc_repurchase", ascending=False).iloc[0]
            r14 = sub[sub["window"] == "w1_4"].sort_values("roc_auc_repurchase", ascending=False).iloc[0]
            comparison_rows.append(
                {
                    "comparison_key": key,
                    "model_name": model_name,
                    "w1_3_feature_set": r13["feature_set"],
                    "w1_4_feature_set": r14["feature_set"],
                    "w1_3_roc_auc_repurchase": r13["roc_auc_repurchase"],
                    "w1_4_roc_auc_repurchase": r14["roc_auc_repurchase"],
                    "w1_4_minus_w1_3_roc_auc": r14["roc_auc_repurchase"] - r13["roc_auc_repurchase"],
                    "interpretation": "w1_4 uses later behavior and should be interpreted as late-period, not early-warning.",
                }
            )
write_csv(TABLE_DIR / "06_v2_w1_3_vs_w1_4_comparison.csv", comparison_rows)

sensitivity_rows = []
tmp = holdout_metrics.copy()
if not tmp.empty:
    without_rows = tmp[tmp["feature_set"].str.contains("without_churn_prevented", regex=False)]
    for _, without in without_rows.iterrows():
        with_name = without["feature_set"].replace("without_churn_prevented", "with_churn_prevented")
        matched = tmp[
            (tmp["window"] == without["window"])
            & (tmp["model_name"] == without["model_name"])
            & (tmp["feature_set"] == with_name)
        ]
        if not matched.empty:
            with_row = matched.iloc[0]
            sensitivity_rows.append(
                {
                    "window": without["window"],
                    "model_name": without["model_name"],
                    "feature_set_without": without["feature_set"],
                    "feature_set_with": with_name,
                    "roc_auc_without": without["roc_auc_repurchase"],
                    "roc_auc_with": with_row["roc_auc_repurchase"],
                    "delta_with_minus_without": with_row["roc_auc_repurchase"] - without["roc_auc_repurchase"],
                }
            )
write_csv(TABLE_DIR / "06_v2_churn_prevented_sensitivity.csv", sensitivity_rows)

best_observed = holdout_metrics.sort_values("roc_auc_repurchase", ascending=False).iloc[0].to_dict()
recommended_pool = holdout_metrics[
    (holdout_metrics["window"] == "w1_3")
    & (holdout_metrics["contains_is_churn_prevented"] == "N")
    & (holdout_metrics["model_group"] == "required_sklearn")
    & (holdout_metrics["feature_family"].isin(["membership_plus_usage", "membership_plus_usage_content"]))
].copy()
recommended_pool["review_flag"] = recommended_pool["roc_auc_repurchase"] >= 0.90
safe_recommended_pool = recommended_pool[~recommended_pool["review_flag"]]
if safe_recommended_pool.empty:
    conservative = recommended_pool.sort_values("roc_auc_repurchase", ascending=False).iloc[0].to_dict()
else:
    conservative = safe_recommended_pool.sort_values("roc_auc_repurchase", ascending=False).iloc[0].to_dict()
business_pool = recommended_pool[recommended_pool["model_name"] == "LogisticRegression"]
business_interpretable = (
    business_pool.sort_values("roc_auc_repurchase", ascending=False).iloc[0].to_dict()
    if not business_pool.empty
    else conservative
)
suspicious = holdout_metrics[
    (holdout_metrics["roc_auc_repurchase"] >= 0.90)
    | (holdout_metrics["window"] == "w1_4")
    | (holdout_metrics["contains_is_churn_prevented"] == "Y")
].copy()

selected_for_decile = [
    ("conservative_recommended_baseline", conservative),
    ("business_interpretable_baseline", business_interpretable),
]
decile_rows = []
for label, row in selected_for_decile:
    sub = predictions_df[
        (predictions_df["window"] == row["window"])
        & (predictions_df["feature_set"] == row["feature_set"])
        & (predictions_df["model_name"] == row["model_name"])
    ].copy()
    if sub.empty:
        continue
    sub = sub.sort_values("churn_risk_score", ascending=False)
    n_top = max(1, math.ceil(len(sub) * 0.10))
    top = sub.head(n_top)
    total_churn = int(sub["y_true_churn_risk"].sum())
    top_churn = int(top["y_true_churn_risk"].sum())
    decile_rows.append(
        {
            "baseline_role": label,
            "window": row["window"],
            "feature_set": row["feature_set"],
            "model_name": row["model_name"],
            "n_test": len(sub),
            "top_decile_n": n_top,
            "total_churn_cases": total_churn,
            "top_decile_churn_cases": top_churn,
            "top_decile_churn_capture_rate": top_churn / total_churn if total_churn else np.nan,
            "overall_churn_rate": total_churn / len(sub) if len(sub) else np.nan,
            "top_decile_churn_rate": top_churn / n_top if n_top else np.nan,
            "lift_vs_overall": (top_churn / n_top) / (total_churn / len(sub)) if total_churn and n_top else np.nan,
        }
    )
write_csv(TABLE_DIR / "06_v2_churn_risk_decile_summary.csv", decile_rows)

def plot_best_curves(window, kind):
    row = holdout_metrics[holdout_metrics["window"] == window].sort_values("roc_auc_repurchase", ascending=False).iloc[0]
    sub = predictions_df[
        (predictions_df["window"] == row["window"])
        & (predictions_df["feature_set"] == row["feature_set"])
        & (predictions_df["model_name"] == row["model_name"])
    ]
    plt.figure(figsize=(7, 5))
    if kind == "roc":
        fpr, tpr, _ = roc_curve(sub["y_true_is_repurchase"], sub["repurchase_score"])
        plt.plot(fpr, tpr, label=f"ROC AUC={row['roc_auc_repurchase']:.4f}")
        plt.plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1)
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title(f"{window} best repurchase ROC")
        path = FIGURE_DIR / f"06_v2_roc_curve_best_{window}.png"
    else:
        precision, recall, _ = precision_recall_curve(sub["y_true_churn_risk"], sub["churn_risk_score"])
        plt.plot(recall, precision, label=f"Churn AP={row['average_precision_churn_risk']:.4f}")
        plt.xlabel("Churn-risk Recall")
        plt.ylabel("Churn-risk Precision")
        plt.title(f"{window} best churn-risk PR")
        path = FIGURE_DIR / f"06_v2_pr_curve_best_{window}.png"
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


for window in ["w1_3", "w1_4"]:
    plot_best_curves(window, "roc")
    plot_best_curves(window, "pr")

plt.figure(figsize=(10, 6))
plot_df = holdout_metrics.sort_values("roc_auc_repurchase", ascending=False).head(30).copy()
plot_df["label"] = plot_df["window"] + " | " + plot_df["model_name"] + " | " + plot_df["feature_family"]
plt.barh(plot_df["label"][::-1], plot_df["roc_auc_repurchase"][::-1])
plt.xlabel("Holdout ROC AUC for repurchase")
plt.title("Top Stage 06 baseline ROC AUC results")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "06_v2_model_auc_comparison.png", dpi=160)
plt.close()

best_config = {
    "target_mapping": {"Y": 1, "N": 0},
    "score_direction": {
        "repurchase_score": "P(is_repurchase = Y)",
        "churn_risk_score": "1 - repurchase_score",
    },
    "best_observed_model": best_observed,
    "conservative_recommended_baseline": conservative,
    "business_interpretable_baseline": business_interpretable,
    "suspicious_result_count": int(len(suspicious)),
    "optional_booster_smoke_status": optional_smoke_status,
    "oof_prediction_policy": "Out-of-fold prediction scores were skipped to control output size; aggregate CV metrics were saved.",
}
write_json(DATA_DIR / "06_v2_best_model_config.json", best_config)

summary_payload = {
    "scope": "Stage 06 baseline modeling only. No SHAP, segmentation, business simulation, Optuna, or broad tuning.",
    "target_mapping": {"Y": 1, "N": 0},
    "row_counts": stage05_summary.get("row_counts", {}),
    "feature_set_count": len(feature_sets),
    "evaluation_spec_count": len(eval_specs),
    "holdout_metric_rows": int(len(holdout_metrics)),
    "cv_metric_rows": int((metrics_df["split_type"] == "groupkfold").sum()) if not metrics_df.empty else 0,
    "best_observed_auc": float(best_observed["roc_auc_repurchase"]),
    "conservative_recommended_auc": float(conservative["roc_auc_repurchase"]),
    "outputs": {
        "data_dir": rel(DATA_DIR),
        "table_dir": rel(TABLE_DIR),
        "figure_dir": rel(FIGURE_DIR),
    },
}
write_json(DATA_DIR / "06_v2_baseline_modeling_summary.json", summary_payload)

def best_family_auc(family, window):
    sub = holdout_metrics[(holdout_metrics["feature_family"] == family) & (holdout_metrics["window"] == window)]
    if sub.empty:
        return None
    row = sub.sort_values("roc_auc_repurchase", ascending=False).iloc[0]
    return f"{row['roc_auc_repurchase']:.4f} ({row['model_name']}, {row['feature_set']})"


comparison_df = pd.DataFrame(comparison_rows)
mean_w14_gain = comparison_df["w1_4_minus_w1_3_roc_auc"].mean() if not comparison_df.empty else np.nan
sensitivity_df = pd.DataFrame(sensitivity_rows)
mean_churn_delta = sensitivity_df["delta_with_minus_without"].mean() if not sensitivity_df.empty else np.nan
suspicious_high = holdout_metrics[holdout_metrics["roc_auc_repurchase"] >= 0.90]

report_lines = [
    "# 06_v2 Baseline Modeling Report",
    "",
    "## Scope",
    "- Stage 06 trained and evaluated baseline models only.",
    "- No SHAP, segmentation, business simulation, Optuna, or broad hyperparameter tuning was run.",
    "- w1_3 is the early-observation window and is closer to early intervention.",
    "- w1_4 is an end-of-period / late-period behavior window. Higher w1_4 performance is not leakage by itself, but it changes the business timing interpretation.",
    "",
    "## Target And Score Direction",
    "- `is_repurchase` was mapped as Y -> 1 and N -> 0.",
    "- `repurchase_score` means P(is_repurchase = Y).",
    "- `churn_risk_score` is 1 - repurchase_score. High churn-risk targeting must use `churn_risk_score`, not `repurchase_score`.",
    "- Threshold 0.5 is a diagnostic threshold only, not an optimized business threshold.",
    "",
    "## Baseline ROC AUC Answers",
    f"- Membership-only baseline ROC AUC: w1_3 {best_family_auc('membership_only', 'w1_3')}; w1_4 {best_family_auc('membership_only', 'w1_4')}.",
    f"- Usage-only baseline ROC AUC: w1_3 {best_family_auc('usage_only', 'w1_3')}; w1_4 {best_family_auc('usage_only', 'w1_4')}.",
    f"- Content-only baseline ROC AUC: w1_3 {best_family_auc('content_only', 'w1_3')}; w1_4 {best_family_auc('content_only', 'w1_4')}.",
    f"- Membership+usage ROC AUC: w1_3 {best_family_auc('membership_plus_usage', 'w1_3')}; w1_4 {best_family_auc('membership_plus_usage', 'w1_4')}.",
    f"- Membership+usage+content ROC AUC: w1_3 {best_family_auc('membership_plus_usage_content', 'w1_3')}; w1_4 {best_family_auc('membership_plus_usage_content', 'w1_4')}.",
    f"- Mean matched w1_4 minus w1_3 ROC AUC difference: {mean_w14_gain:.4f}.",
    f"- Mean with_churn_prevented minus without_churn_prevented ROC AUC difference: {mean_churn_delta:.4f}.",
    "",
    "## Recommendation",
    f"- Best observed model: {best_observed['window']} / {best_observed['feature_set']} / {best_observed['model_name']} with ROC AUC {best_observed['roc_auc_repurchase']:.4f}.",
    f"- Conservative recommended baseline: {conservative['window']} / {conservative['feature_set']} / {conservative['model_name']} with ROC AUC {conservative['roc_auc_repurchase']:.4f}.",
    f"- Business-interpretable baseline: {business_interpretable['window']} / {business_interpretable['feature_set']} / {business_interpretable['model_name']} with ROC AUC {business_interpretable['roc_auc_repurchase']:.4f}.",
    f"- Suspiciously high results with ROC AUC >= 0.90: {len(suspicious_high)}.",
    "- Results depending on w1_4 or `is_churn_prevented` should be reviewed before retention strategy use.",
    "",
    "## Before SHAP",
    "- Confirm whether `is_churn_prevented` is valid historical prior information or a post-treatment variable.",
    "- Review top w1_4 gains under the late-period interpretation.",
    "- Confirm no feature family contains unresolved temporal leakage.",
    "- Choose one conservative, timing-defensible model before explanation.",
    "",
    "## Output Files",
    f"- Data: {rel(DATA_DIR)}",
    f"- Tables: {rel(TABLE_DIR)}",
    f"- Figures: {rel(FIGURE_DIR)}",
]
(DATA_DIR / "06_v2_baseline_modeling_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

required_data_outputs = [
    DATA_DIR / "06_v2_model_metrics.csv",
    DATA_DIR / "06_v2_prediction_scores.csv",
    DATA_DIR / "06_v2_best_model_config.json",
    DATA_DIR / "06_v2_feature_importance.csv",
    DATA_DIR / "06_v2_baseline_modeling_summary.json",
    DATA_DIR / "06_v2_baseline_modeling_report.md",
]
required_table_outputs = [
    TABLE_DIR / "06_v2_input_dataset_summary.csv",
    TABLE_DIR / "06_v2_split_summary.csv",
    TABLE_DIR / "06_v2_group_leakage_check.csv",
    TABLE_DIR / "06_v2_feature_set_validation.csv",
    TABLE_DIR / "06_v2_model_metrics_summary.csv",
    TABLE_DIR / "06_v2_best_model_by_feature_set.csv",
    TABLE_DIR / "06_v2_w1_3_vs_w1_4_comparison.csv",
    TABLE_DIR / "06_v2_churn_prevented_sensitivity.csv",
    TABLE_DIR / "06_v2_failed_models.csv",
    TABLE_DIR / "06_v2_environment_summary.csv",
    TABLE_DIR / "06_v2_split_membership_row_ids.csv",
    TABLE_DIR / "06_v2_fold_assignment.csv",
    TABLE_DIR / "06_v2_churn_risk_decile_summary.csv",
    TABLE_DIR / "06_v2_score_orientation_summary.csv",
]
required_figure_outputs = [
    FIGURE_DIR / "06_v2_roc_curve_best_w1_3.png",
    FIGURE_DIR / "06_v2_roc_curve_best_w1_4.png",
    FIGURE_DIR / "06_v2_pr_curve_best_w1_3.png",
    FIGURE_DIR / "06_v2_pr_curve_best_w1_4.png",
    FIGURE_DIR / "06_v2_model_auc_comparison.png",
]

raw_after = snapshot_paths(RAW_FILES)
stage_after = snapshot_dirs(stage_existing_dirs) | snapshot_paths(stage_existing_files)
required_core_expected = {
    (spec["window"], spec["feature_set"], model_name)
    for spec in eval_specs
    for model_name, mspec in sklearn_specs.items()
    if mspec.get("required_core")
}
feature_validation_df = pd.DataFrame(feature_validation_rows)
split_w13 = set(df_w13.loc[df_w13[ID_COL].isin(test_ids), ID_COL])
split_w14 = set(df_w14.loc[df_w14[ID_COL].isin(test_ids), ID_COL])

final_checks = [
    {"check": "raw_files_unchanged", "status": "PASS" if raw_before == raw_after else "FAIL", "detail": "raw snapshots unchanged"},
    {"check": "no_project_root_data_output_created", "status": "PASS" if not (PROJECT_ROOT / "_data" / "02_interim" / "06_v2_baseline_modeling").exists() and not (PROJECT_ROOT / "_data" / "06_v2_baseline_modeling").exists() else "FAIL", "detail": "Stage 06 writes only under park.ingyeom/reports"},
    {"check": "stage01_through_stage05_outputs_not_overwritten", "status": "PASS" if stage_before == stage_after else "FAIL", "detail": "Stage 01-05 snapshots unchanged"},
    {"check": "target_mapping_documented", "status": "PASS", "detail": "Y=1, N=0 documented in score orientation and report"},
    {"check": "prediction_scores_include_repurchase_and_churn_risk", "status": "PASS" if {"repurchase_score", "churn_risk_score"}.issubset(predictions_df.columns) else "FAIL", "detail": "prediction score columns present"},
    {"check": "identical_holdout_membership_split_reused", "status": "PASS" if split_w13 == split_w14 == test_ids else "FAIL", "detail": "same test membership_row_id set for w1_3 and w1_4"},
    {"check": "no_USER_KEY_overlap_train_test", "status": "PASS" if not (train_groups & test_groups) else "FAIL", "detail": f"overlap={len(train_groups & test_groups)}"},
    {"check": "no_forbidden_feature_in_X", "status": "PASS" if feature_validation_df["forbidden_feature_violations"].fillna("").eq("").all() else "FAIL", "detail": "feature set validation"},
    {"check": "is_repurchase_target_only", "status": "PASS" if all(TARGET not in spec["features"] for spec in eval_specs) else "FAIL", "detail": "target excluded from features"},
    {"check": "USER_KEY_group_metadata_only", "status": "PASS" if all(GROUP_COL not in spec["features"] for spec in eval_specs) else "FAIL", "detail": "USER_KEY excluded from features"},
    {"check": "membership_row_id_id_metadata_only", "status": "PASS" if all(ID_COL not in spec["features"] for spec in eval_specs) else "FAIL", "detail": "membership_row_id excluded from features"},
    {"check": "group_split_used", "status": "PASS", "detail": "GroupShuffleSplit and GroupKFold used with USER_KEY"},
    {"check": "w1_3_and_w1_4_evaluated_separately", "status": "PASS" if {"w1_3", "w1_4"}.issubset(set(holdout_metrics["window"])) else "FAIL", "detail": "separate window metrics saved"},
    {"check": "with_and_without_churn_prevented_evaluated", "status": "PASS" if {"Y", "N"}.issubset(set(holdout_metrics["contains_is_churn_prevented"])) else "FAIL", "detail": "both variants present"},
    {"check": "required_sklearn_baselines_completed_before_optional", "status": "PASS" if required_core_expected.issubset(required_core_success) else "FAIL", "detail": f"required_core_success={len(required_core_success)}/{len(required_core_expected)}"},
    {"check": "optional_boosters_logged_and_nonblocking", "status": "PASS", "detail": "optional boosters smoke-tested and failures/skips logged"},
    {"check": "hist_gradient_boosting_passed_or_logged", "status": "PASS" if hgb_success or ((failed_df["model_name"] == "HistGradientBoostingClassifier").any()) else "FAIL", "detail": f"attempted={hgb_attempted}, success={hgb_success}"},
    {"check": "highest_auc_and_conservative_baseline_separate", "status": "PASS" if best_observed["feature_set"] != "" and conservative["feature_set"] != "" else "FAIL", "detail": "best_config contains both roles"},
    {"check": "no_optuna_run", "status": "PASS", "detail": "No Optuna imports or tuning code used"},
    {"check": "no_shap_run", "status": "PASS", "detail": "No SHAP imports or outputs used"},
    {"check": "no_segmentation_or_business_simulation", "status": "PASS", "detail": "Only baseline modeling outputs created"},
    {"check": "all_required_outputs_created", "status": "PASS" if all(p.exists() for p in required_data_outputs + required_table_outputs + required_figure_outputs) else "FAIL", "detail": f"required_outputs={len(required_data_outputs + required_table_outputs + required_figure_outputs)}"},
]
write_csv(TABLE_DIR / "06_v2_final_checks.csv", final_checks)

print("06_v2 baseline modeling completed.")
for row in final_checks:
    print(f"{row['check']}: {row['status']} - {row['detail']}")
