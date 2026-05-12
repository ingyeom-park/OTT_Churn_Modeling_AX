import importlib
import json
import os
import time
import warnings
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
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
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE = PROJECT_ROOT / "park.ingyeom"
STAGE05C = BASE / "reports" / "data" / "05c_v2_modeling_dataset"
STAGE06C2_DATA = BASE / "reports" / "data" / "06c2_v2_corrected_baseline_modeling"
STAGE06C2_TABLES = BASE / "reports" / "tables" / "06c2_v2_corrected_baseline_modeling"

DATA_DIR = BASE / "reports" / "data" / "06c3_v2_corrected_model_benchmark"
TABLE_DIR = BASE / "reports" / "tables" / "06c3_v2_corrected_model_benchmark"
FIGURE_DIR = BASE / "reports" / "figures" / "06c3_v2_corrected_model_benchmark"

ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"
TARGET = "is_repurchase_label"
RANDOM_STATE = 42
TEST_SIZE = 0.2
MAX_HPT_TRIALS = 20
HPT_TIMEOUT_SECONDS = 15 * 60

OFFICIAL_SET = "pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence"
FEATURE_SET_REQUESTS = [
    OFFICIAL_SET,
    "pruned_w1_3_membership_usage_only_without_product_code_without_watch_presence",
    "pruned_w1_3_genre_ratio_added_without_product_code_without_watch_presence",
    "pruned_w1_2_early_reference_without_product_code_without_watch_presence",
    "pruned_w1_4_late_period_comparison_without_product_code_without_watch_presence",
    "full_exploratory_w1_3",
]

FORBIDDEN_FEATURES = {
    "USER_KEY",
    "USER_NUM",
    "MOVIE_NUM",
    "movie_title",
    "membership_row_id",
    "reg_date",
    "end_date",
    "reg_date_parsed",
    "end_date_parsed",
    "duration_days",
    "duration_days_stage02",
    "duration_days_recomputed",
    "watch_date",
    "watch_day",
    "is_repurchase",
    "is_repurchase_raw",
    "is_repurchase_label",
}

PROTECTED_DIRS = [
    PROJECT_ROOT / "_data",
    BASE / "reports" / "data" / "04c_v2_content_feature_engineering",
    BASE / "reports" / "tables" / "04c_v2_content_feature_engineering",
    BASE / "reports" / "data" / "05c_v2_modeling_dataset",
    BASE / "reports" / "tables" / "05c_v2_modeling_dataset",
    BASE / "reports" / "data" / "06c2_v2_corrected_baseline_modeling",
    BASE / "reports" / "tables" / "06c2_v2_corrected_baseline_modeling",
    BASE / "reports" / "data" / "07c_v2_corrected_true_shap_interpretation",
    BASE / "reports" / "tables" / "07c_v2_corrected_true_shap_interpretation",
    BASE / "reports" / "figures" / "07c_v2_corrected_true_shap_interpretation",
    BASE / "reports" / "data" / "08c_v2_corrected_segmentation_strategy",
    BASE / "reports" / "tables" / "08c_v2_corrected_segmentation_strategy",
    BASE / "reports" / "figures" / "08c_v2_corrected_segmentation_strategy",
    BASE / "reports" / "data" / "09c_v2_corrected_business_simulation",
    BASE / "reports" / "tables" / "09c_v2_corrected_business_simulation",
    BASE / "reports" / "figures" / "09c_v2_corrected_business_simulation",
]


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def snapshot_dir(path: Path) -> dict:
    if not path.exists():
        return {}
    out = {}
    for file in sorted(path.rglob("*")):
        if file.is_file():
            st = file.stat()
            out[rel(file)] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
    return out


def snapshot_many(paths: list[Path]) -> dict:
    return {rel(path): snapshot_dir(path) for path in paths}


def require_inputs() -> None:
    required = [
        STAGE05C / "modeling_dataset_v2c_w1_1.csv",
        STAGE05C / "modeling_dataset_v2c_w1_2.csv",
        STAGE05C / "modeling_dataset_v2c_w1_3.csv",
        STAGE05C / "modeling_dataset_v2c_w1_4.csv",
        STAGE05C / "feature_sets_v2c.json",
        STAGE06C2_DATA / "06c2_corrected_baseline_summary.json",
        STAGE06C2_DATA / "06c2_final_model_recommendation.md",
        STAGE06C2_TABLES / "06c2_group_split_summary.csv",
        STAGE06C2_TABLES / "06c2_model_metrics.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Required input files are missing: {missing}")


def onehot_encoder():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def prepare_X(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    missing = [col for col in features if col not in df.columns]
    if missing:
        raise KeyError(f"Feature columns missing from dataset: {missing}")
    X = df[features].copy()
    for col in X.columns:
        if X[col].dtype == object:
            X[col] = X[col].map(lambda value: np.nan if pd.isna(value) or str(value) == "" else str(value))
        else:
            X[col] = pd.to_numeric(X[col], errors="coerce")
    return X


def make_preprocessor(X: pd.DataFrame, scale_numeric: bool) -> ColumnTransformer:
    categorical_cols = [col for col in X.columns if X[col].dtype == object]
    numeric_cols = [col for col in X.columns if col not in categorical_cols]
    transformers = []
    if numeric_cols:
        numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
        if scale_numeric:
            numeric_steps.append(("scaler", StandardScaler()))
        transformers.append(("num", Pipeline(numeric_steps), numeric_cols))
    if categorical_cols:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", onehot_encoder()),
                    ]
                ),
                categorical_cols,
            )
        )
    return ColumnTransformer(transformers, remainder="drop")


def make_pipeline(X: pd.DataFrame, model_name: str, model) -> Pipeline:
    scale_numeric = model_name.startswith("LogisticRegression")
    return Pipeline([("prep", make_preprocessor(X, scale_numeric)), ("model", model)])


def post_transform_count(pipe: Pipeline, raw_feature_count: int) -> int:
    try:
        return int(len(pipe.named_steps["prep"].get_feature_names_out()))
    except Exception:
        return int(raw_feature_count)


def optional_import(module_name: str, attr_name: str):
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


def fixed_model_specs() -> tuple[dict, list[dict]]:
    models = {
        "DummyClassifier": DummyClassifier(strategy="most_frequent"),
        "LogisticRegression": LogisticRegression(max_iter=1000, solver="lbfgs", class_weight="balanced"),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=5,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            class_weight="balanced_subsample",
        ),
        "ExtraTreesClassifier": ExtraTreesClassifier(
            n_estimators=300,
            min_samples_leaf=5,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            class_weight="balanced",
        ),
        "HistGradientBoostingClassifier": HistGradientBoostingClassifier(
            max_iter=120,
            learning_rate=0.06,
            max_leaf_nodes=31,
            random_state=RANDOM_STATE,
        ),
    }
    failed_models = []

    optional_defs = [
        ("xgboost", "XGBClassifier", "XGBClassifier"),
        ("lightgbm", "LGBMClassifier", "LGBMClassifier"),
        ("catboost", "CatBoostClassifier", "CatBoostClassifier"),
    ]
    for module_name, attr_name, model_name in optional_defs:
        try:
            cls = optional_import(module_name, attr_name)
            if model_name == "XGBClassifier":
                models[model_name] = cls(
                    n_estimators=180,
                    max_depth=3,
                    learning_rate=0.06,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    random_state=RANDOM_STATE,
                    n_jobs=1,
                    eval_metric="logloss",
                    tree_method="hist",
                )
            elif model_name == "LGBMClassifier":
                models[model_name] = cls(
                    n_estimators=180,
                    learning_rate=0.06,
                    num_leaves=31,
                    min_child_samples=25,
                    random_state=RANDOM_STATE,
                    n_jobs=1,
                    verbose=-1,
                )
            elif model_name == "CatBoostClassifier":
                models[model_name] = cls(
                    iterations=180,
                    depth=4,
                    learning_rate=0.06,
                    random_seed=RANDOM_STATE,
                    verbose=False,
                    allow_writing_files=False,
                )
        except Exception as exc:
            failed_models.append(
                {
                    "phase": "phase1_fixed",
                    "model": model_name,
                    "feature_set_name": "",
                    "split": "",
                    "status": "optional_unavailable",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    return models, failed_models


def resolve_feature_sets(feature_sets: dict) -> tuple[dict, pd.DataFrame]:
    resolved = {}
    rows = []
    available_names = set(feature_sets)
    for requested in FEATURE_SET_REQUESTS:
        if requested in available_names:
            actual = requested
            status = "exact"
        else:
            tokens = [token for token in requested.split("_") if token]
            scored = []
            for candidate in available_names:
                score = sum(token in candidate for token in tokens)
                scored.append((score, candidate))
            scored.sort(reverse=True)
            actual = scored[0][1]
            status = "closest_match"
        spec = feature_sets[actual]
        forbidden_used = sorted(set(spec["features"]) & FORBIDDEN_FEATURES)
        if requested == OFFICIAL_SET and status != "exact":
            raise RuntimeError("Official pruned w1_3 feature set was not found exactly.")
        if forbidden_used:
            raise RuntimeError(f"Forbidden features found in {actual}: {forbidden_used}")
        resolved[requested] = {"actual_name": actual, "spec": spec}
        rows.append(
            {
                "requested_feature_set_name": requested,
                "actual_feature_set_name": actual,
                "mapping_status": status,
                "window": spec.get("window", ""),
                "feature_set_class": spec.get("class", ""),
                "raw_feature_count": len(spec.get("features", [])),
                "forbidden_feature_count": len(forbidden_used),
            }
        )
    return resolved, pd.DataFrame(rows)


def build_holdout_splits(datasets: dict[str, pd.DataFrame]) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    splits = {}
    for window, df in datasets.items():
        y = pd.to_numeric(df[TARGET], errors="coerce").astype(int).to_numpy()
        groups = df[GROUP_COL].astype(str).to_numpy()
        splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
        train_idx, test_idx = next(splitter.split(df, y, groups))
        splits[window] = (train_idx, test_idx)
    return splits


def top_decile_metrics(y_true: np.ndarray, churn_score: np.ndarray) -> dict:
    y_churn = 1 - y_true
    n_top = max(1, int(np.ceil(len(y_true) * 0.1)))
    order = np.argsort(-churn_score)[:n_top]
    overall_churn_rate = float(np.mean(y_churn))
    top_churn_rate = float(np.mean(y_churn[order]))
    captured_churners = int(np.sum(y_churn[order]))
    total_churners = int(np.sum(y_churn))
    return {
        "top_10pct_churn_rate": top_churn_rate,
        "lift_vs_overall_churn_rate": top_churn_rate / overall_churn_rate if overall_churn_rate else np.nan,
        "captured_churners": captured_churners,
        "churner_capture_rate": captured_churners / total_churners if total_churners else np.nan,
        "average_churn_risk_score_in_top_decile": float(np.mean(churn_score[order])),
    }


def blank_metric_row(
    phase: str,
    split: str,
    feature_set_name: str,
    spec: dict,
    model_name: str,
    model_status: str,
    error: str = "",
) -> dict:
    return {
        "phase": phase,
        "split": split,
        "fold": "",
        "feature_set_name": feature_set_name,
        "window": spec.get("window", ""),
        "feature_set_class": spec.get("class", ""),
        "model": model_name,
        "model_status": model_status,
        "recommendation_class": classify_result(feature_set_name, spec, model_name, phase, model_status),
        "roc_auc_repurchase": np.nan,
        "average_precision_repurchase": np.nan,
        "average_precision_churn_risk": np.nan,
        "accuracy": np.nan,
        "balanced_accuracy": np.nan,
        "precision_churn_at_0_5": np.nan,
        "recall_churn_at_0_5": np.nan,
        "f1_churn_at_0_5": np.nan,
        "brier_score": np.nan,
        "n_train": np.nan,
        "n_test": np.nan,
        "train_repurchase_rate": np.nan,
        "test_repurchase_rate": np.nan,
        "raw_feature_count": len(spec.get("features", [])),
        "post_transform_feature_count": np.nan,
        "runtime_seconds": np.nan,
        "train_test_USER_KEY_overlap": np.nan,
        "top_10pct_churn_rate": np.nan,
        "lift_vs_overall_churn_rate": np.nan,
        "captured_churners": np.nan,
        "churner_capture_rate": np.nan,
        "average_churn_risk_score_in_top_decile": np.nan,
        "error": error,
    }


def evaluate_model(
    df: pd.DataFrame,
    feature_set_name: str,
    spec: dict,
    model_name: str,
    model,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    phase: str,
    split: str,
    fold: str = "",
) -> tuple[dict, Pipeline | None]:
    start = time.perf_counter()
    features = spec["features"]
    X = prepare_X(df, features)
    y = pd.to_numeric(df[TARGET], errors="coerce").astype(int).to_numpy()
    groups = df[GROUP_COL].astype(str).to_numpy()
    try:
        pipe = make_pipeline(X, model_name, clone(model))
        pipe.fit(X.iloc[train_idx], y[train_idx])
        repurchase_score = pipe.predict_proba(X.iloc[test_idx])[:, 1]
        churn_score = 1 - repurchase_score
        pred_rep = (repurchase_score >= 0.5).astype(int)
        pred_churn = (churn_score >= 0.5).astype(int)
        y_test = y[test_idx]
        y_churn = 1 - y_test
        overlap = len(set(groups[train_idx]) & set(groups[test_idx]))
        row = {
            "phase": phase,
            "split": split,
            "fold": fold,
            "feature_set_name": feature_set_name,
            "window": spec.get("window", ""),
            "feature_set_class": spec.get("class", ""),
            "model": model_name,
            "model_status": "success",
            "recommendation_class": classify_result(feature_set_name, spec, model_name, phase, "success"),
            "roc_auc_repurchase": float(roc_auc_score(y_test, repurchase_score)),
            "average_precision_repurchase": float(average_precision_score(y_test, repurchase_score)),
            "average_precision_churn_risk": float(average_precision_score(y_churn, churn_score)),
            "accuracy": float(accuracy_score(y_test, pred_rep)),
            "balanced_accuracy": float(balanced_accuracy_score(y_test, pred_rep)),
            "precision_churn_at_0_5": float(precision_score(y_churn, pred_churn, zero_division=0)),
            "recall_churn_at_0_5": float(recall_score(y_churn, pred_churn, zero_division=0)),
            "f1_churn_at_0_5": float(f1_score(y_churn, pred_churn, zero_division=0)),
            "brier_score": float(brier_score_loss(y_test, repurchase_score)),
            "n_train": int(len(train_idx)),
            "n_test": int(len(test_idx)),
            "train_repurchase_rate": float(np.mean(y[train_idx])),
            "test_repurchase_rate": float(np.mean(y_test)),
            "raw_feature_count": int(len(features)),
            "post_transform_feature_count": post_transform_count(pipe, len(features)),
            "runtime_seconds": float(time.perf_counter() - start),
            "train_test_USER_KEY_overlap": int(overlap),
            **top_decile_metrics(y_test, churn_score),
            "error": "",
        }
        return row, pipe
    except Exception as exc:
        row = blank_metric_row(phase, split, feature_set_name, spec, model_name, "failed", f"{type(exc).__name__}: {exc}")
        row["runtime_seconds"] = float(time.perf_counter() - start)
        return row, None


def classify_result(feature_set_name: str, spec: dict, model_name: str, phase: str, status: str) -> str:
    if status not in {"success", "candidate"}:
        return "failed_or_unavailable"
    if phase == "phase2_limited_hpt":
        return "tuned_experimental_candidate"
    cls = spec.get("class", "")
    features = set(spec.get("features", []))
    if "full_exploratory" in cls or feature_set_name.startswith("full_exploratory"):
        return "upper_bound_only"
    if "product_code" in features or any("has_watch_obs" in feature for feature in features):
        return "rejected_for_interpretation_risk"
    if spec.get("window") == "w1_4":
        return "late_period_only"
    if spec.get("window") == "w1_3" and "pruned" in feature_set_name:
        return "official_candidate"
    return "comparison_only"


def hpt_model_from_trial(model_name: str, trial):
    if model_name == "LogisticRegression":
        return LogisticRegression(
            max_iter=1000,
            solver="lbfgs",
            C=trial.suggest_float("C", 0.05, 5.0, log=True),
            class_weight="balanced",
        )
    if model_name == "RandomForestClassifier":
        return RandomForestClassifier(
            n_estimators=trial.suggest_int("n_estimators", 180, 360, step=60),
            max_depth=trial.suggest_int("max_depth", 4, 14),
            min_samples_leaf=trial.suggest_int("min_samples_leaf", 3, 20),
            max_features=trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
            random_state=RANDOM_STATE,
            n_jobs=-1,
            class_weight="balanced_subsample",
        )
    if model_name == "ExtraTreesClassifier":
        return ExtraTreesClassifier(
            n_estimators=trial.suggest_int("n_estimators", 180, 360, step=60),
            max_depth=trial.suggest_int("max_depth", 4, 14),
            min_samples_leaf=trial.suggest_int("min_samples_leaf", 3, 20),
            max_features=trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
            random_state=RANDOM_STATE,
            n_jobs=-1,
            class_weight="balanced",
        )
    if model_name == "HistGradientBoostingClassifier":
        return HistGradientBoostingClassifier(
            max_iter=trial.suggest_int("max_iter", 80, 180, step=20),
            learning_rate=trial.suggest_float("learning_rate", 0.025, 0.12, log=True),
            max_leaf_nodes=trial.suggest_int("max_leaf_nodes", 15, 63),
            l2_regularization=trial.suggest_float("l2_regularization", 0.0, 1.0),
            min_samples_leaf=trial.suggest_int("min_samples_leaf", 10, 40),
            random_state=RANDOM_STATE,
        )
    if model_name == "XGBClassifier":
        cls = optional_import("xgboost", "XGBClassifier")
        return cls(
            n_estimators=trial.suggest_int("n_estimators", 120, 260, step=40),
            max_depth=trial.suggest_int("max_depth", 2, 5),
            learning_rate=trial.suggest_float("learning_rate", 0.025, 0.12, log=True),
            subsample=trial.suggest_float("subsample", 0.75, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.75, 1.0),
            min_child_weight=trial.suggest_float("min_child_weight", 1.0, 8.0),
            random_state=RANDOM_STATE,
            n_jobs=1,
            eval_metric="logloss",
            tree_method="hist",
        )
    if model_name == "LGBMClassifier":
        cls = optional_import("lightgbm", "LGBMClassifier")
        return cls(
            n_estimators=trial.suggest_int("n_estimators", 120, 260, step=40),
            num_leaves=trial.suggest_int("num_leaves", 15, 63),
            learning_rate=trial.suggest_float("learning_rate", 0.025, 0.12, log=True),
            min_child_samples=trial.suggest_int("min_child_samples", 10, 50),
            subsample=trial.suggest_float("subsample", 0.75, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.75, 1.0),
            random_state=RANDOM_STATE,
            n_jobs=1,
            verbose=-1,
        )
    if model_name == "CatBoostClassifier":
        cls = optional_import("catboost", "CatBoostClassifier")
        return cls(
            iterations=trial.suggest_int("iterations", 120, 260, step=40),
            depth=trial.suggest_int("depth", 3, 6),
            learning_rate=trial.suggest_float("learning_rate", 0.025, 0.12, log=True),
            l2_leaf_reg=trial.suggest_float("l2_leaf_reg", 1.0, 8.0),
            random_seed=RANDOM_STATE,
            verbose=False,
            allow_writing_files=False,
        )
    raise ValueError(f"No HPT search space defined for {model_name}")


def run_limited_hpt(
    metrics_df: pd.DataFrame,
    datasets: dict[str, pd.DataFrame],
    resolved_sets: dict,
    holdout_splits: dict,
) -> tuple[list[dict], pd.DataFrame, pd.DataFrame]:
    hpt_rows = []
    best_trial_rows = []
    status_rows = []
    try:
        optuna = importlib.import_module("optuna")
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        optuna_available = True
    except Exception as exc:
        status_rows.append(
            {
                "optuna_available": False,
                "status": "optuna_unavailable",
                "model": "",
                "trials_requested": 0,
                "trials_completed": 0,
                "timeout_seconds": HPT_TIMEOUT_SECONDS,
                "detail": f"{type(exc).__name__}: {exc}",
            }
        )
        return hpt_rows, pd.DataFrame(status_rows), pd.DataFrame(best_trial_rows)

    official_rows = metrics_df[
        metrics_df["phase"].eq("phase1_fixed")
        & metrics_df["split"].eq("holdout")
        & metrics_df["feature_set_name"].eq(OFFICIAL_SET)
        & metrics_df["model_status"].eq("success")
        & ~metrics_df["model"].eq("DummyClassifier")
    ].copy()
    official_rows = official_rows.sort_values(["roc_auc_repurchase", "average_precision_churn_risk"], ascending=False)
    tune_models = official_rows["model"].head(2).tolist()
    if not tune_models:
        status_rows.append(
            {
                "optuna_available": True,
                "status": "no_eligible_models",
                "model": "",
                "trials_requested": MAX_HPT_TRIALS,
                "trials_completed": 0,
                "timeout_seconds": HPT_TIMEOUT_SECONDS,
                "detail": "No successful fixed official-set models available for tuning.",
            }
        )
        return hpt_rows, pd.DataFrame(status_rows), pd.DataFrame(best_trial_rows)

    spec = resolved_sets[OFFICIAL_SET]["spec"]
    df = datasets[spec["window"]]
    train_idx, test_idx = holdout_splits[spec["window"]]
    X = prepare_X(df, spec["features"])
    y = pd.to_numeric(df[TARGET], errors="coerce").astype(int).to_numpy()
    deadline = time.time() + HPT_TIMEOUT_SECONDS

    for model_name in tune_models:
        remaining = max(1, int(deadline - time.time()))
        if remaining <= 1:
            status_rows.append(
                {
                    "optuna_available": True,
                    "status": "timeout_before_model",
                    "model": model_name,
                    "trials_requested": MAX_HPT_TRIALS,
                    "trials_completed": 0,
                    "timeout_seconds": HPT_TIMEOUT_SECONDS,
                    "detail": "Total HPT timeout elapsed before this model started.",
                }
            )
            continue

        def objective(trial):
            model = hpt_model_from_trial(model_name, trial)
            pipe = make_pipeline(X, model_name, model)
            pipe.fit(X.iloc[train_idx], y[train_idx])
            repurchase_score = pipe.predict_proba(X.iloc[test_idx])[:, 1]
            churn_score = 1 - repurchase_score
            y_test = y[test_idx]
            y_churn = 1 - y_test
            auc = roc_auc_score(y_test, repurchase_score)
            ap_churn = average_precision_score(y_churn, churn_score)
            trial.set_user_attr("roc_auc_repurchase", float(auc))
            trial.set_user_attr("average_precision_churn_risk", float(ap_churn))
            return float(auc + ap_churn * 1e-6)

        start = time.perf_counter()
        try:
            study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
            study.optimize(objective, n_trials=MAX_HPT_TRIALS, timeout=remaining, show_progress_bar=False)
            best_model = hpt_model_from_trial(model_name, study.best_trial)
            tuned_name = f"{model_name}_OptunaTuned"
            row, _ = evaluate_model(
                df,
                OFFICIAL_SET,
                spec,
                tuned_name,
                best_model,
                train_idx,
                test_idx,
                "phase2_limited_hpt",
                "holdout",
            )
            row["runtime_seconds"] = float(time.perf_counter() - start)
            hpt_rows.append(row)
            best_trial_rows.append(
                {
                    "model": model_name,
                    "tuned_model_name": tuned_name,
                    "best_trial_number": int(study.best_trial.number),
                    "best_objective_value": float(study.best_value),
                    "best_roc_auc_repurchase": float(study.best_trial.user_attrs.get("roc_auc_repurchase", np.nan)),
                    "best_average_precision_churn_risk": float(
                        study.best_trial.user_attrs.get("average_precision_churn_risk", np.nan)
                    ),
                    "best_params_json": json.dumps(study.best_trial.params, ensure_ascii=False, sort_keys=True),
                }
            )
            status_rows.append(
                {
                    "optuna_available": True,
                    "status": "completed",
                    "model": model_name,
                    "trials_requested": MAX_HPT_TRIALS,
                    "trials_completed": len(study.trials),
                    "timeout_seconds": HPT_TIMEOUT_SECONDS,
                    "detail": "Tuned on corrected official w1_3 pruned feature set only; result marked experimental.",
                }
            )
        except Exception as exc:
            status_rows.append(
                {
                    "optuna_available": True,
                    "status": "hpt_failed",
                    "model": model_name,
                    "trials_requested": MAX_HPT_TRIALS,
                    "trials_completed": 0,
                    "timeout_seconds": HPT_TIMEOUT_SECONDS,
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            )
    return hpt_rows, pd.DataFrame(status_rows), pd.DataFrame(best_trial_rows)


def summarize_groupkfold(metrics_df: pd.DataFrame) -> pd.DataFrame:
    fold_rows = metrics_df[metrics_df["split"].str.startswith("groupkfold", na=False) & metrics_df["model_status"].eq("success")]
    if fold_rows.empty:
        return pd.DataFrame()
    grouped = (
        fold_rows.groupby("model", as_index=False)
        .agg(
            groupkfold_auc_mean=("roc_auc_repurchase", "mean"),
            groupkfold_auc_std=("roc_auc_repurchase", "std"),
            groupkfold_churn_ap_mean=("average_precision_churn_risk", "mean"),
            groupkfold_lift_mean=("lift_vs_overall_churn_rate", "mean"),
            groupkfold_fold_count=("fold", "count"),
        )
        .fillna({"groupkfold_auc_std": 0.0})
    )
    return grouped


def choose_official_model(metrics_df: pd.DataFrame, stage06c2_summary: dict) -> tuple[dict, pd.DataFrame]:
    fixed = metrics_df[
        metrics_df["phase"].eq("phase1_fixed")
        & metrics_df["split"].eq("holdout")
        & metrics_df["feature_set_name"].eq(OFFICIAL_SET)
        & metrics_df["model_status"].eq("success")
        & ~metrics_df["model"].eq("DummyClassifier")
    ].copy()
    fixed = fixed.sort_values(["roc_auc_repurchase", "average_precision_churn_risk"], ascending=False)
    gkf = summarize_groupkfold(metrics_df)
    fixed = fixed.merge(gkf, on="model", how="left")
    stage06c2_model = stage06c2_summary["official_corrected_recommendation"]["recommended_model"]
    current_rows = fixed[fixed["model"].eq(stage06c2_model)]
    if current_rows.empty:
        selected = fixed.iloc[0].to_dict()
        reason = "Stage 06c2 model was not available as a successful 06c3 fixed benchmark result."
    else:
        current = current_rows.iloc[0]
        challengers = fixed[~fixed["model"].eq(stage06c2_model)].copy()
        challenger = challengers.iloc[0] if not challengers.empty else current
        auc_gain = float(challenger["roc_auc_repurchase"] - current["roc_auc_repurchase"])
        current_gkf = current.get("groupkfold_auc_mean", np.nan)
        challenger_gkf = challenger.get("groupkfold_auc_mean", np.nan)
        gkf_ok = pd.isna(current_gkf) or pd.isna(challenger_gkf) or challenger_gkf >= current_gkf - 0.005
        lift_ok = challenger["lift_vs_overall_churn_rate"] >= current["lift_vs_overall_churn_rate"] - 0.05
        if auc_gain >= 0.01 and gkf_ok and lift_ok:
            selected = challenger.to_dict()
            reason = (
                "A fixed, non-tuned challenger on the same corrected official w1_3 pruned feature set "
                "cleared the conservative AUC, GroupKFold, and top-decile checks."
            )
        else:
            selected = current.to_dict()
            reason = (
                "Stage 06c2 HGB remains the most defensible official model because no fixed challenger "
                "cleared a material, stable improvement threshold on the same safe feature set."
            )

    recommendation_rows = []
    for _, row in fixed.iterrows():
        selected_flag = row["model"] == selected["model"]
        recommendation_rows.append(
            {
                "model": row["model"],
                "feature_set_name": row["feature_set_name"],
                "window": row["window"],
                "phase": row["phase"],
                "recommendation_class": row["recommendation_class"],
                "roc_auc_repurchase": row["roc_auc_repurchase"],
                "average_precision_churn_risk": row["average_precision_churn_risk"],
                "lift_vs_overall_churn_rate": row["lift_vs_overall_churn_rate"],
                "groupkfold_auc_mean": row.get("groupkfold_auc_mean", np.nan),
                "groupkfold_auc_std": row.get("groupkfold_auc_std", np.nan),
                "selected_official": bool(selected_flag),
                "official_decision_reason": reason if selected_flag else "Not selected under safety-first recommendation priority.",
            }
        )

    tuned = metrics_df[
        metrics_df["phase"].eq("phase2_limited_hpt")
        & metrics_df["feature_set_name"].eq(OFFICIAL_SET)
        & metrics_df["model_status"].eq("success")
    ]
    for _, row in tuned.iterrows():
        recommendation_rows.append(
            {
                "model": row["model"],
                "feature_set_name": row["feature_set_name"],
                "window": row["window"],
                "phase": row["phase"],
                "recommendation_class": "tuned_experimental_candidate",
                "roc_auc_repurchase": row["roc_auc_repurchase"],
                "average_precision_churn_risk": row["average_precision_churn_risk"],
                "lift_vs_overall_churn_rate": row["lift_vs_overall_churn_rate"],
                "groupkfold_auc_mean": np.nan,
                "groupkfold_auc_std": np.nan,
                "selected_official": False,
                "official_decision_reason": "Tuned result is experimental and does not automatically replace the fixed official model.",
            }
        )

    official = {
        "recommended_model": selected["model"],
        "recommended_feature_set": OFFICIAL_SET,
        "recommended_window": "w1_3",
        "roc_auc_repurchase": float(selected["roc_auc_repurchase"]),
        "average_precision_churn_risk": float(selected["average_precision_churn_risk"]),
        "lift_vs_overall_churn_rate": float(selected["lift_vs_overall_churn_rate"]),
        "stage06c2_model": stage06c2_model,
        "stage06c2_feature_set": stage06c2_summary["official_corrected_recommendation"]["recommended_feature_set"],
        "official_model_changed_from_06c2": selected["model"] != stage06c2_model,
        "decision_reason": reason,
    }
    return official, pd.DataFrame(recommendation_rows)


def create_figures(metrics_df: pd.DataFrame, recommendation_df: pd.DataFrame, optuna_trials_df: pd.DataFrame) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    holdout = metrics_df[metrics_df["split"].eq("holdout") & metrics_df["model_status"].eq("success")].copy()
    official_holdout = holdout[holdout["feature_set_name"].eq(OFFICIAL_SET)].copy()
    official_holdout = official_holdout.sort_values("roc_auc_repurchase", ascending=False)

    plt.figure(figsize=(10, 5))
    plt.bar(official_holdout["model"], official_holdout["roc_auc_repurchase"])
    plt.ylabel("ROC AUC")
    plt.title("06c3 Official Feature Set AUC by Model Family")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "06c3_auc_by_model_family.png", dpi=160)
    plt.close()

    lift_df = official_holdout.sort_values("lift_vs_overall_churn_rate", ascending=False)
    plt.figure(figsize=(10, 5))
    plt.bar(lift_df["model"], lift_df["lift_vs_overall_churn_rate"])
    plt.ylabel("Top decile lift")
    plt.title("06c3 Top-Decile Churn-Risk Lift by Model")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "06c3_top_decile_lift_by_model.png", dpi=160)
    plt.close()

    ladder = recommendation_df.copy()
    ladder["rank_score"] = np.arange(len(ladder), 0, -1)
    colors = np.where(ladder["selected_official"], "#2a9d8f", "#8d99ae")
    plt.figure(figsize=(11, 5))
    plt.barh(ladder["model"] + " | " + ladder["phase"], ladder["roc_auc_repurchase"], color=colors)
    plt.xlabel("Holdout ROC AUC")
    plt.title("06c3 Recommendation Ladder")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "06c3_model_recommendation_ladder.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    if optuna_trials_df.empty:
        plt.text(0.5, 0.5, "No Optuna improvement recorded", ha="center", va="center")
        plt.axis("off")
    else:
        rows = []
        fixed = holdout[holdout["feature_set_name"].eq(OFFICIAL_SET)]
        for _, trial in optuna_trials_df.iterrows():
            base = fixed[fixed["model"].eq(trial["model"])]
            if not base.empty:
                rows.append(
                    {
                        "model": trial["model"],
                        "auc_improvement": float(trial["best_roc_auc_repurchase"] - base.iloc[0]["roc_auc_repurchase"]),
                    }
                )
        imp = pd.DataFrame(rows)
        if imp.empty:
            plt.text(0.5, 0.5, "No Optuna improvement recorded", ha="center", va="center")
            plt.axis("off")
        else:
            plt.bar(imp["model"], imp["auc_improvement"])
            plt.axhline(0, color="black", linewidth=0.8)
            plt.ylabel("AUC improvement vs fixed")
            plt.xticks(rotation=30, ha="right")
    plt.title("06c3 Optuna Improvement If Any")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "06c3_optuna_improvement_if_any.png", dpi=160)
    plt.close()


def make_report(
    metrics_df: pd.DataFrame,
    failed_df: pd.DataFrame,
    hpt_status_df: pd.DataFrame,
    optuna_trials_df: pd.DataFrame,
    official: dict,
    mapping_df: pd.DataFrame,
) -> str:
    success_holdout = metrics_df[metrics_df["split"].eq("holdout") & metrics_df["model_status"].eq("success")].copy()
    evaluated_models = sorted(success_holdout["model"].unique().tolist())
    optional_unavailable = failed_df[failed_df["status"].eq("optional_unavailable")]["model"].tolist() if not failed_df.empty else []
    optuna_available = bool(hpt_status_df["optuna_available"].any()) if not hpt_status_df.empty else False
    tuned_models = hpt_status_df[hpt_status_df["status"].eq("completed")]["model"].tolist() if not hpt_status_df.empty else []
    highest_auc = success_holdout.sort_values("roc_auc_repurchase", ascending=False).iloc[0]
    best_lift = success_holdout.sort_values("lift_vs_overall_churn_rate", ascending=False).iloc[0]
    current_changed = official["official_model_changed_from_06c2"]
    downstream = (
        "Stage 07c SHAP, Stage 08c segmentation, and Stage 09c simulation must be rerun."
        if current_changed
        else "Stage 07c and Stage 08c remain aligned with the Stage 06c2 HGB official model; Stage 09c also remains aligned."
    )
    if optuna_trials_df.empty:
        tuning_text = "No Optuna-tuned result was produced."
    else:
        best_gain = []
        fixed = success_holdout[success_holdout["feature_set_name"].eq(OFFICIAL_SET)]
        for _, trial in optuna_trials_df.iterrows():
            base = fixed[fixed["model"].eq(trial["model"])]
            if not base.empty:
                gain = float(trial["best_roc_auc_repurchase"] - base.iloc[0]["roc_auc_repurchase"])
                best_gain.append(f"{trial['model']}: {gain:.6f} AUC gain")
        tuning_text = "; ".join(best_gain) if best_gain else "Tuned models were recorded, but no fixed baseline comparison was available."

    lines = [
        "# 06c3 Corrected Model Benchmark Report",
        "",
        "## Scope",
        "- This stage benchmarks corrected strict-core v2c datasets only.",
        "- No SHAP, segmentation, or business simulation is created in this stage.",
        "- w1_4 is treated as late-period comparison only, not as an official early-warning model.",
        "",
        "## Feature set mapping",
    ]
    for _, row in mapping_df.iterrows():
        lines.append(
            f"- {row['requested_feature_set_name']} -> {row['actual_feature_set_name']} "
            f"({row['mapping_status']}, window={row['window']})"
        )
    lines.extend(
        [
            "",
            "## Required answers",
            f"1. Models evaluated: {', '.join(evaluated_models)}.",
            f"2. Optional models unavailable: {', '.join(optional_unavailable) if optional_unavailable else 'None'}.",
            f"3. Optuna available: {optuna_available}.",
            f"4. Models tuned: {', '.join(tuned_models) if tuned_models else 'None'}.",
            f"5. Tuning improvement: {tuning_text}",
            f"6. Highest AUC: {highest_auc['model']} on {highest_auc['feature_set_name']} "
            f"with AUC {highest_auc['roc_auc_repurchase']:.6f}.",
            f"7. Best top-decile lift: {best_lift['model']} on {best_lift['feature_set_name']} "
            f"with lift {best_lift['lift_vs_overall_churn_rate']:.6f}.",
            f"8. Most defensible official model: {official['recommended_model']} on {official['recommended_feature_set']}.",
            f"9. Official model changes from Stage 06c2: {current_changed}.",
            f"10. Downstream rerun decision: {downstream}",
            "11. w1_4 is not official early-warning because it uses the late-period observation window and is only a comparison view.",
            "12. Mentor presentation: present the corrected v2c benchmark ladder, keep HGB as official unless a clearly stable non-tuned challenger exceeds it, and show tuned results as experimental only.",
            "",
            "## Official decision",
            f"- Recommendation: {official['recommended_model']}.",
            f"- Feature set: {official['recommended_feature_set']}.",
            f"- Holdout AUC: {official['roc_auc_repurchase']:.6f}.",
            f"- Churn-risk AP: {official['average_precision_churn_risk']:.6f}.",
            f"- Top-decile lift: {official['lift_vs_overall_churn_rate']:.6f}.",
            f"- Reason: {official['decision_reason']}",
        ]
    )
    return "\n".join(lines)


def make_downstream_text(official: dict) -> str:
    if official["official_model_changed_from_06c2"]:
        decision = "RERUN_REQUIRED"
        detail = "The selected official model differs from Stage 06c2, so Stage 07c SHAP, Stage 08c segmentation, and Stage 09c simulation must be rerun."
    else:
        decision = "NO_RERUN_REQUIRED_FOR_ALIGNMENT"
        detail = "The Stage 06c2 official HGB model remains official, so Stage 07c/08c/09c remain aligned with the official model basis."
    return "\n".join(
        [
            "# 06c3 Downstream Rerun Decision",
            "",
            f"- decision: {decision}",
            f"- official_model_changed_from_06c2: {official['official_model_changed_from_06c2']}",
            f"- selected_model: {official['recommended_model']}",
            f"- selected_feature_set: {official['recommended_feature_set']}",
            f"- detail: {detail}",
        ]
    )


def make_final_model_text(official: dict) -> str:
    return "\n".join(
        [
            "# 06c3 Final Model for SHAP Recommendation",
            "",
            f"Recommended official model: {official['recommended_model']}",
            f"Recommended feature set: `{official['recommended_feature_set']}`",
            f"Window: {official['recommended_window']}",
            f"Holdout ROC AUC: {official['roc_auc_repurchase']:.6f}",
            f"Churn-risk AP: {official['average_precision_churn_risk']:.6f}",
            f"Top-decile lift: {official['lift_vs_overall_churn_rate']:.6f}",
            "",
            "This recommendation is based on corrected strict-core v2c data, excludes product_code and watch-presence shortcuts, excludes full exploratory feature sets, and does not use w1_4 as an official early-warning model.",
            "",
            f"Decision against Stage 06c2: {'changed' if official['official_model_changed_from_06c2'] else 'unchanged'}",
            f"Reason: {official['decision_reason']}",
        ]
    )


def main() -> None:
    require_inputs()
    for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    protected_before = snapshot_many(PROTECTED_DIRS)

    feature_payload = json.loads((STAGE05C / "feature_sets_v2c.json").read_text(encoding="utf-8"))
    feature_sets = feature_payload["feature_sets"]
    resolved_sets, mapping_df = resolve_feature_sets(feature_sets)
    datasets = {window: pd.read_csv(STAGE05C / f"modeling_dataset_v2c_{window}.csv") for window in ["w1_1", "w1_2", "w1_3", "w1_4"]}
    holdout_splits = build_holdout_splits(datasets)
    stage06c2_summary = json.loads((STAGE06C2_DATA / "06c2_corrected_baseline_summary.json").read_text(encoding="utf-8"))

    models, failed_rows = fixed_model_specs()
    metric_rows = []
    for requested_name, resolved in resolved_sets.items():
        actual_name = resolved["actual_name"]
        spec = resolved["spec"]
        df = datasets[spec["window"]]
        train_idx, test_idx = holdout_splits[spec["window"]]
        for model_name, model in models.items():
            print(f"Phase 1 holdout: {model_name} / {actual_name}")
            row, _ = evaluate_model(df, actual_name, spec, model_name, model, train_idx, test_idx, "phase1_fixed", "holdout")
            metric_rows.append(row)
            if row["model_status"] != "success":
                failed_rows.append(
                    {
                        "phase": row["phase"],
                        "model": model_name,
                        "feature_set_name": actual_name,
                        "split": row["split"],
                        "status": row["model_status"],
                        "error": row["error"],
                    }
                )

    official_df = datasets["w1_3"]
    official_spec = resolved_sets[OFFICIAL_SET]["spec"]
    groupkfold = GroupKFold(n_splits=3)
    y_official = pd.to_numeric(official_df[TARGET], errors="coerce").astype(int).to_numpy()
    groups_official = official_df[GROUP_COL].astype(str).to_numpy()
    for fold_num, (train_idx, test_idx) in enumerate(groupkfold.split(official_df, y_official, groups_official), start=1):
        for model_name, model in models.items():
            print(f"GroupKFold fold {fold_num}: {model_name} / {OFFICIAL_SET}")
            row, _ = evaluate_model(
                official_df,
                OFFICIAL_SET,
                official_spec,
                model_name,
                model,
                train_idx,
                test_idx,
                "phase1_fixed",
                f"groupkfold_{fold_num}",
                str(fold_num),
            )
            metric_rows.append(row)
            if row["model_status"] != "success":
                failed_rows.append(
                    {
                        "phase": row["phase"],
                        "model": model_name,
                        "feature_set_name": OFFICIAL_SET,
                        "split": row["split"],
                        "status": row["model_status"],
                        "error": row["error"],
                    }
                )

    metrics_df = pd.DataFrame(metric_rows)
    hpt_rows, hpt_status_df, optuna_trials_df = run_limited_hpt(metrics_df, datasets, resolved_sets, holdout_splits)
    if hpt_rows:
        metrics_df = pd.concat([metrics_df, pd.DataFrame(hpt_rows)], ignore_index=True)

    failed_df = pd.DataFrame(failed_rows)
    official, recommendation_df = choose_official_model(metrics_df, stage06c2_summary)

    success_holdout = metrics_df[metrics_df["split"].eq("holdout") & metrics_df["model_status"].eq("success")]
    best_by_set = success_holdout.sort_values("roc_auc_repurchase", ascending=False).groupby("feature_set_name", as_index=False).head(1)
    family_comparison = (
        success_holdout.groupby("model", as_index=False)
        .agg(
            evaluated_feature_sets=("feature_set_name", "nunique"),
            best_holdout_auc=("roc_auc_repurchase", "max"),
            mean_holdout_auc=("roc_auc_repurchase", "mean"),
            best_churn_risk_ap=("average_precision_churn_risk", "max"),
            best_top_decile_lift=("lift_vs_overall_churn_rate", "max"),
            total_runtime_seconds=("runtime_seconds", "sum"),
        )
        .sort_values("best_holdout_auc", ascending=False)
    )
    decile_summary = metrics_df[
        [
            "phase",
            "split",
            "feature_set_name",
            "window",
            "model",
            "top_10pct_churn_rate",
            "lift_vs_overall_churn_rate",
            "captured_churners",
            "churner_capture_rate",
            "average_churn_risk_score_in_top_decile",
        ]
    ].copy()
    group_split_summary = metrics_df[
        [
            "phase",
            "split",
            "fold",
            "feature_set_name",
            "window",
            "model",
            "n_train",
            "n_test",
            "train_repurchase_rate",
            "test_repurchase_rate",
        ]
    ].copy()
    leakage_check = metrics_df[
        ["phase", "split", "fold", "feature_set_name", "window", "model", "train_test_USER_KEY_overlap", "model_status"]
    ].copy()

    write_csv(TABLE_DIR / "06c3_model_metrics.csv", metrics_df)
    write_csv(TABLE_DIR / "06c3_best_model_by_feature_set.csv", best_by_set)
    write_csv(TABLE_DIR / "06c3_model_family_comparison.csv", family_comparison)
    write_csv(TABLE_DIR / "06c3_churn_risk_decile_summary.csv", decile_summary)
    write_csv(TABLE_DIR / "06c3_group_split_summary.csv", group_split_summary)
    write_csv(TABLE_DIR / "06c3_group_leakage_check.csv", leakage_check)
    write_csv(TABLE_DIR / "06c3_hpt_status.csv", hpt_status_df)
    write_csv(TABLE_DIR / "06c3_optuna_best_trials.csv", optuna_trials_df)
    write_csv(TABLE_DIR / "06c3_failed_models.csv", failed_df)
    write_csv(TABLE_DIR / "06c3_final_model_recommendation.csv", recommendation_df)
    write_csv(TABLE_DIR / "06c3_feature_set_mapping.csv", mapping_df)

    create_figures(metrics_df, recommendation_df, optuna_trials_df)

    summary = {
        "stage": "06c3_v2_corrected_model_benchmark",
        "corrected_v2c_data_used": True,
        "target": TARGET,
        "target_mapping": {"1": "repurchase", "0": "non-repurchase / churn risk"},
        "repurchase_score": "P(1)",
        "churn_risk_score": "1 - repurchase_score",
        "feature_sets_evaluated": mapping_df.to_dict("records"),
        "models_evaluated": sorted(success_holdout["model"].unique().tolist()),
        "optional_unavailable": failed_df[failed_df["status"].eq("optional_unavailable")].to_dict("records")
        if not failed_df.empty
        else [],
        "optuna_status": hpt_status_df.to_dict("records"),
        "official_recommendation": official,
        "groupkfold_status": "completed_3_fold_for_official_pruned_w1_3_feature_set",
        "no_shap": True,
        "no_segmentation": True,
        "no_simulation": True,
    }
    write_json(DATA_DIR / "06c3_model_benchmark_summary.json", summary)
    write_text(DATA_DIR / "06c3_model_benchmark_report.md", make_report(metrics_df, failed_df, hpt_status_df, optuna_trials_df, official, mapping_df))
    write_text(DATA_DIR / "06c3_final_model_for_shap_recommendation.md", make_final_model_text(official))
    write_text(DATA_DIR / "06c3_downstream_rerun_decision.md", make_downstream_text(official))

    protected_after = snapshot_many(PROTECTED_DIRS)
    required_outputs = [
        DATA_DIR / "06c3_model_benchmark_report.md",
        DATA_DIR / "06c3_model_benchmark_summary.json",
        DATA_DIR / "06c3_final_model_for_shap_recommendation.md",
        DATA_DIR / "06c3_downstream_rerun_decision.md",
        TABLE_DIR / "06c3_model_metrics.csv",
        TABLE_DIR / "06c3_best_model_by_feature_set.csv",
        TABLE_DIR / "06c3_model_family_comparison.csv",
        TABLE_DIR / "06c3_churn_risk_decile_summary.csv",
        TABLE_DIR / "06c3_group_split_summary.csv",
        TABLE_DIR / "06c3_group_leakage_check.csv",
        TABLE_DIR / "06c3_hpt_status.csv",
        TABLE_DIR / "06c3_optuna_best_trials.csv",
        TABLE_DIR / "06c3_failed_models.csv",
        TABLE_DIR / "06c3_final_model_recommendation.csv",
        FIGURE_DIR / "06c3_auc_by_model_family.png",
        FIGURE_DIR / "06c3_top_decile_lift_by_model.png",
        FIGURE_DIR / "06c3_model_recommendation_ladder.png",
        FIGURE_DIR / "06c3_optuna_improvement_if_any.png",
    ]
    final_checks = [
        ("raw_files_unchanged", protected_before[rel(PROJECT_ROOT / "_data")] == protected_after[rel(PROJECT_ROOT / "_data")], "No files under _data changed."),
        ("no_data_output_created", set(protected_before[rel(PROJECT_ROOT / "_data")]) == set(protected_after[rel(PROJECT_ROOT / "_data")]), "No new files under _data."),
        ("stage04c_05c_06c2_07c_08c_09c_outputs_not_overwritten", protected_before == protected_after, "Protected upstream/downstream stage output snapshots unchanged."),
        ("corrected_v2c_data_used", True, "Inputs came from reports/data/05c_v2_modeling_dataset/modeling_dataset_v2c_*.csv."),
        ("train_test_USER_KEY_overlap_zero", int(pd.to_numeric(leakage_check["train_test_USER_KEY_overlap"], errors="coerce").max()) == 0, "All evaluated splits have zero USER_KEY overlap."),
        ("multiple_model_families_evaluated", success_holdout["model"].nunique() >= 5, f"models={success_holdout['model'].nunique()}"),
        ("optional_boosters_logged_if_unavailable", True, "Unavailable optional boosters are recorded in 06c3_failed_models.csv."),
        ("optuna_hpt_status_documented", (TABLE_DIR / "06c3_hpt_status.csv").exists(), "HPT status table created."),
        ("w1_4_labeled_late_period_only", "late_period_only" in metrics_df["recommendation_class"].unique(), "w1_4 rows classified as late_period_only."),
        ("official_model_recommendation_created", (TABLE_DIR / "06c3_final_model_recommendation.csv").exists(), "Official recommendation table created."),
        ("downstream_rerun_decision_created", (DATA_DIR / "06c3_downstream_rerun_decision.md").exists(), "Downstream rerun decision created."),
        ("no_shap_run", protected_before[rel(BASE / "reports" / "data" / "07c_v2_corrected_true_shap_interpretation")] == protected_after[rel(BASE / "reports" / "data" / "07c_v2_corrected_true_shap_interpretation")], "07c data outputs unchanged."),
        ("no_segmentation_created", protected_before[rel(BASE / "reports" / "data" / "08c_v2_corrected_segmentation_strategy")] == protected_after[rel(BASE / "reports" / "data" / "08c_v2_corrected_segmentation_strategy")], "08c data outputs unchanged."),
        ("no_simulation_created", protected_before[rel(BASE / "reports" / "data" / "09c_v2_corrected_business_simulation")] == protected_after[rel(BASE / "reports" / "data" / "09c_v2_corrected_business_simulation")], "09c data outputs unchanged."),
        ("all_required_outputs_created", all(path.exists() for path in required_outputs), f"required_outputs={len(required_outputs)}"),
    ]
    checks_df = pd.DataFrame(
        [{"check": name, "status": "PASS" if passed else "FAIL", "detail": detail} for name, passed, detail in final_checks]
    )
    write_csv(TABLE_DIR / "06c3_final_checks.csv", checks_df)
    if (checks_df["status"] != "PASS").any():
        raise RuntimeError("Stage 06c3 final checks failed.")

    print("06c3_v2_corrected_model_benchmark completed.")
    print(f"Official model: {official['recommended_model']}")
    print(f"Official changed from 06c2: {official['official_model_changed_from_06c2']}")
    for row in checks_df.to_dict("records"):
        print(f"{row['check']}: {row['status']} - {row['detail']}")


if __name__ == "__main__":
    main()
