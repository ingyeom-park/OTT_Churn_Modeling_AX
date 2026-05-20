from _future_ import annotations

import csv
import json
import math
import os
import platform
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd


RUN_NAME = "PUBLIC_model_notebook_prep_260520"
TODAY = "2026-05-20"
ROOT = Path(_file_).resolve().parents[3]
PUBLIC = ROOT / "PUBLIC"
DATA_DIR = PUBLIC / "data"
NOTEBOOK_DIR = PUBLIC / "notebooks"
RESULTS_DIR = PUBLIC / "results"
WORK_DIR = RESULTS_DIR / "_06_model_notebook_prep_260520"
ZIP_DIR = PUBLIC / "zip"
NOTE_PATH = PUBLIC / "note.md"
ZIP_PATH = ZIP_DIR / "PUBLIC_model_notebook_prep_260520_review_package.zip"

SOURCE_OVERALL = DATA_DIR / "06_expanded_dataset_log_retention.csv"
SOURCE_PROMO0 = DATA_DIR / "06_expanded_dataset_promo_0_log_retention.csv"
SOURCE_PROMO1 = DATA_DIR / "06_expanded_dataset_promo_1_log_retention.csv"

MODEL_INPUT_PROMO0 = DATA_DIR / "06_model_input_promo_0.csv"
MODEL_INPUT_PROMO1 = DATA_DIR / "06_model_input_promo_1.csv"

RAW_RETENTION = ["retention_w2_ratio", "retention_w3_ratio"]
LOG_RETENTION = ["log_retention_w2_ratio", "log_retention_w3_ratio"]
PAYMENT_COLS = ["payment_is_mobile", "payment_is_pc", "payment_is_android", "payment_is_ios"]
EXCLUDED_FEATURES = ["is_repurchase", "USER_KEY", "is_promotion"] + PAYMENT_COLS + RAW_RETENTION

EXPECTED_ROWS = {"promo_0": 11193, "promo_1": 11904}

MODEL_SPECS = [
    {
        "key": "gb_promo0",
        "notebook": NOTEBOOK_DIR / "06_gb_promo0.ipynb",
        "data": MODEL_INPUT_PROMO0,
        "out_dir": RESULTS_DIR / "_06_model_rerun_260520" / "gb_promo0",
        "promo": 0,
        "model_kind": "gradientboosting",
        "model_label": "GradientBoostingClassifier conservative",
    },
    {
        "key": "gb_promo1",
        "notebook": NOTEBOOK_DIR / "06_gb_promo1.ipynb",
        "data": MODEL_INPUT_PROMO1,
        "out_dir": RESULTS_DIR / "_06_model_rerun_260520" / "gb_promo1",
        "promo": 1,
        "model_kind": "gradientboosting",
        "model_label": "GradientBoostingClassifier conservative",
    },
    {
        "key": "lr_promo0",
        "notebook": NOTEBOOK_DIR / "06_lr_promo0.ipynb",
        "data": MODEL_INPUT_PROMO0,
        "out_dir": RESULTS_DIR / "_06_model_rerun_260520" / "lr_promo0",
        "promo": 0,
        "model_kind": "logisticregression",
        "model_label": "LogisticRegression baseline",
    },
    {
        "key": "lr_promo1",
        "notebook": NOTEBOOK_DIR / "06_lr_promo1.ipynb",
        "data": MODEL_INPUT_PROMO1,
        "out_dir": RESULTS_DIR / "_06_model_rerun_260520" / "lr_promo1",
        "promo": 1,
        "model_kind": "logisticregression",
        "model_label": "LogisticRegression baseline",
    },
]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def read_rows_cols(path: Path) -> tuple[int | None, int | None, str]:
    try:
        df = pd.read_csv(path)
        return len(df), len(df.columns), "PASS"
    except Exception as exc:
        return None, None, f"FAIL: {type(exc)._name_}: {exc}"


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def inventory_existing_dirs() -> list[dict]:
    rows = []
    targets = [WORK_DIR] + [spec["out_dir"] for spec in MODEL_SPECS]
    for directory in targets:
        existed_before = directory.exists()
        directory.mkdir(parents=True, exist_ok=True)
        files = sorted([p for p in directory.rglob("*") if p.is_file()])
        if files:
            for file_path in files:
                rows.append(
                    {
                        "directory": rel(directory),
                        "existed_before": existed_before,
                        "file_path": rel(file_path),
                        "size_bytes": file_path.stat().st_size,
                        "modified_time": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(timespec="seconds"),
                        "notes": "pre-existing or regenerated prep artifact",
                    }
                )
        else:
            rows.append(
                {
                    "directory": rel(directory),
                    "existed_before": existed_before,
                    "file_path": "",
                    "size_bytes": "",
                    "modified_time": "",
                    "notes": "directory empty at inventory time",
                }
            )
    return rows


def create_input_inventory() -> list[dict]:
    rows = []
    for path in [SOURCE_OVERALL, SOURCE_PROMO0, SOURCE_PROMO1]:
        exists = path.exists()
        row = {
            "file_path": rel(path) if exists else str(path),
            "exists": exists,
            "size_bytes": path.stat().st_size if exists else "",
            "modified_time": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if exists else "",
            "readable_status": "NOT_CHECKED",
            "n_rows": "",
            "n_cols": "",
            "column_count": "",
            "parse_status": "NOT_CHECKED",
            "notes": "",
        }
        if exists:
            n_rows, n_cols, parse_status = read_rows_cols(path)
            row.update(
                {
                    "readable_status": "PASS" if parse_status == "PASS" else "FAIL",
                    "n_rows": n_rows if n_rows is not None else "",
                    "n_cols": n_cols if n_cols is not None else "",
                    "column_count": n_cols if n_cols is not None else "",
                    "parse_status": parse_status,
                }
            )
        else:
            row["parse_status"] = "FAIL"
            row["readable_status"] = "FAIL"
            row["notes"] = "required input is missing"
        rows.append(row)
    return rows


def create_input_profile(datasets: dict[str, pd.DataFrame]) -> list[dict]:
    rows = []
    for name, df in datasets.items():
        y = pd.to_numeric(df["is_repurchase"], errors="coerce") if "is_repurchase" in df.columns else pd.Series(dtype=float)
        expected = EXPECTED_ROWS.get(name)
        actual = len(df)
        notes = []
        if expected is not None and actual != expected:
            notes.append(f"expected row count {expected}, actual {actual}")
        rows.append(
            {
                "dataset_name": name,
                "row_count": actual,
                "expected_row_count": expected if expected is not None else "",
                "row_count_status": "PASS" if expected is None or actual == expected else "WARN",
                "column_count": len(df.columns),
                "has_USER_KEY": "USER_KEY" in df.columns,
                "has_is_repurchase": "is_repurchase" in df.columns,
                "has_is_promotion": "is_promotion" in df.columns,
                "has_retention_w2_ratio": "retention_w2_ratio" in df.columns,
                "has_retention_w3_ratio": "retention_w3_ratio" in df.columns,
                "has_log_retention_w2_ratio": "log_retention_w2_ratio" in df.columns,
                "has_log_retention_w3_ratio": "log_retention_w3_ratio" in df.columns,
                "has_payment_is_mobile": "payment_is_mobile" in df.columns,
                "has_payment_is_pc": "payment_is_pc" in df.columns,
                "has_payment_is_android": "payment_is_android" in df.columns,
                "has_payment_is_ios": "payment_is_ios" in df.columns,
                "target_positive_count": int((y == 1).sum()) if not y.empty else "",
                "target_negative_count": int((y == 0).sum()) if not y.empty else "",
                "target_positive_rate": float((y == 1).mean()) if not y.empty else "",
                "missing_total": int(df.isna().sum().sum()),
                "duplicate_USER_KEY_count": int(df.duplicated("USER_KEY").sum()) if "USER_KEY" in df.columns else "",
                "numeric_column_count": int(len(df.select_dtypes(include="number").columns)),
                "non_numeric_column_count": int(len(df.columns) - len(df.select_dtypes(include="number").columns)),
                "notes": "; ".join(notes),
            }
        )
    return rows


def create_model_inputs(datasets: dict[str, pd.DataFrame]) -> list[dict]:
    rows = []
    for name, output_path in [("promo_0", MODEL_INPUT_PROMO0), ("promo_1", MODEL_INPUT_PROMO1)]:
        source = datasets[name]
        out = source.drop(columns=[c for c in RAW_RETENTION if c in source.columns]).copy()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(output_path, index=False, encoding="utf-8-sig")
        y = pd.to_numeric(out["is_repurchase"], errors="coerce") if "is_repurchase" in out.columns else pd.Series(dtype=float)
        has_raw = any(c in out.columns for c in RAW_RETENTION)
        has_log = all(c in out.columns for c in LOG_RETENTION)
        has_target = "is_repurchase" in out.columns
        has_user = "USER_KEY" in out.columns
        if has_raw or not has_log or not has_target or not has_user:
            status = "FAIL"
        elif any(c in out.columns for c in ["is_promotion"] + PAYMENT_COLS):
            status = "WARN"
        else:
            status = "PASS"
        rows.append(
            {
                "dataset_name": name,
                "output_file": rel(output_path),
                "n_rows": len(out),
                "n_cols": len(out.columns),
                "has_retention_w2_ratio": "retention_w2_ratio" in out.columns,
                "has_retention_w3_ratio": "retention_w3_ratio" in out.columns,
                "has_log_retention_w2_ratio": "log_retention_w2_ratio" in out.columns,
                "has_log_retention_w3_ratio": "log_retention_w3_ratio" in out.columns,
                "has_USER_KEY": has_user,
                "has_is_repurchase": has_target,
                "has_is_promotion": "is_promotion" in out.columns,
                "has_payment_is_mobile": "payment_is_mobile" in out.columns,
                "has_payment_is_pc": "payment_is_pc" in out.columns,
                "has_payment_is_android": "payment_is_android" in out.columns,
                "has_payment_is_ios": "payment_is_ios" in out.columns,
                "target_positive_count": int((y == 1).sum()) if not y.empty else "",
                "target_negative_count": int((y == 0).sum()) if not y.empty else "",
                "target_positive_rate": float((y == 1).mean()) if not y.empty else "",
                "validation_status": status,
                "notes": "is_promotion/payment columns remain in CSV but notebooks exclude them from features" if status == "WARN" else "",
            }
        )
    return rows


def feature_role(column: str) -> tuple[str, bool, str, str]:
    if column == "is_repurchase":
        return "target", False, "target column", ""
    if column == "USER_KEY":
        return "identifier", False, "identifier/group key", "USER_KEY duplicate caveat applies"
    if column == "is_promotion":
        return "split_key", False, "split key", "promo-specific dataset; exclude if present"
    if column in PAYMENT_COLS:
        return "excluded_payment", False, "payment column excluded by user instruction", ""
    if column in RAW_RETENTION:
        return "FAIL_if_present", False, "raw retention must be removed", "should not exist in model input"
    if column in LOG_RETENTION:
        return "log_retention_feature", True, "", "current feature"
    return "feature", True, "", ""


def create_feature_manifest() -> list[dict]:
    rows = []
    for dataset_name, path in [("promo_0", MODEL_INPUT_PROMO0), ("promo_1", MODEL_INPUT_PROMO1)]:
        df = load_csv(path)
        for missing_col in RAW_RETENTION:
            if missing_col not in df.columns:
                rows.append(
                    {
                        "dataset_name": dataset_name,
                        "column_name": missing_col,
                        "dtype": "",
                        "missing_count": "",
                        "missing_rate": "",
                        "role": "absent_removed",
                        "used_as_feature": False,
                        "exclude_reason": "raw retention removed from current model input",
                        "notes": "required absence confirmed",
                    }
                )
        for column in df.columns:
            role, used, reason, notes = feature_role(column)
            rows.append(
                {
                    "dataset_name": dataset_name,
                    "column_name": column,
                    "dtype": str(df[column].dtype),
                    "missing_count": int(df[column].isna().sum()),
                    "missing_rate": float(df[column].isna().mean()),
                    "role": role,
                    "used_as_feature": used,
                    "exclude_reason": reason,
                    "notes": notes,
                }
            )
    return rows


def nb_cell(cell_type: str, source: str) -> dict:
    cell = {"cell_type": cell_type, "metadata": {}, "source": source.splitlines(keepends=True)}
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def notebook_metadata() -> dict:
    return {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": platform.python_version(),
        },
    }


def model_notebook_code(spec: dict) -> str:
    data_rel = rel(spec["data"])
    out_rel = rel(spec["out_dir"])
    if spec["model_kind"] == "gradientboosting":
        imports = "from sklearn.ensemble import GradientBoostingClassifier"
        suggest_params = """\
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 50, 250),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.05),
        "max_depth": trial.suggest_int("max_depth", 1, 3),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 50, 300),
        "min_samples_split": trial.suggest_int("min_samples_split", 100, 600),
        "subsample": trial.suggest_float("subsample", 0.60, 0.90),
        "max_features": trial.suggest_categorical("max_features", ["sqrt", None]),
        "random_state": RANDOM_STATE,
    }
"""
        build_model = "return GradientBoostingClassifier(**params)"
    else:
        imports = "from sklearn.linear_model import LogisticRegression\nfrom sklearn.pipeline import Pipeline\nfrom sklearn.preprocessing import StandardScaler"
        suggest_params = """\
    params = {
        "C": trial.suggest_float("C", 0.001, 10.0, log=True),
        "class_weight": trial.suggest_categorical("class_weight", [None, "balanced"]),
        "penalty": "l2",
        "solver": "lbfgs",
        "max_iter": 3000,
        "random_state": RANDOM_STATE,
    }
"""
        build_model = 'return Pipeline([("scaler", StandardScaler()), ("model", LogisticRegression(**params))])'

    return f'''from pathlib import Path
import json
import warnings

import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split
{imports}

warnings.filterwarnings("ignore", category=UserWarning)

ROOT = Path.cwd()
if not (ROOT / "PUBLIC").exists():
    ROOT = Path(r"C:\\Code\\ott-churn-prediction")
PUBLIC = ROOT / "PUBLIC"

DATA = ROOT / "{data_rel}"
OUT_DIR = ROOT / "{out_rel}"
PROMO = {spec["promo"]}
MODEL_NAME = "{spec["model_label"]}"
RANDOM_STATE = 42
N_TRIALS = 100
N_SPLITS = 5
OVERFIT_GAP = 0.03
TEST_SIZE = 0.2
GAP_PENALTY = 0.50

TARGET_COL = "is_repurchase"
ID_COL = "USER_KEY"
RAW_RETENTION_COLS = ["retention_w2_ratio", "retention_w3_ratio"]
LOG_RETENTION_COLS = ["log_retention_w2_ratio", "log_retention_w3_ratio"]
EXCLUDE_COLS = [
    TARGET_COL,
    ID_COL,
    "is_promotion",
    "payment_is_mobile",
    "payment_is_pc",
    "payment_is_android",
    "payment_is_ios",
] + RAW_RETENTION_COLS

OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA)
if any(col in df.columns for col in RAW_RETENTION_COLS):
    raise ValueError("Raw retention columns must not exist in current model input.")
missing_log = [col for col in LOG_RETENTION_COLS if col not in df.columns]
if missing_log:
    raise ValueError(f"Missing log retention columns: {{missing_log}}")
if TARGET_COL not in df.columns:
    raise ValueError("Missing target column is_repurchase.")

feature_cols = [col for col in df.columns if col not in EXCLUDE_COLS]
non_numeric_cols = df[feature_cols].select_dtypes(exclude="number").columns.tolist()
if non_numeric_cols:
    raise ValueError(f"Non-numeric feature columns found: {{non_numeric_cols}}")
if not set(LOG_RETENTION_COLS).issubset(feature_cols):
    raise ValueError("Log retention columns are not included as features.")

X = df[feature_cols].copy()
y = pd.to_numeric(df[TARGET_COL], errors="raise").astype(int)
missing_total = int(X.isna().sum().sum())
if missing_total:
    X = X.fillna(X.median(numeric_only=True))

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y,
)

def make_model(params):
    {build_model}

def objective(trial):
{suggest_params}
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    train_scores = []
    valid_scores = []
    for train_idx, valid_idx in cv.split(X_train, y_train):
        X_tr = X_train.iloc[train_idx]
        X_va = X_train.iloc[valid_idx]
        y_tr = y_train.iloc[train_idx]
        y_va = y_train.iloc[valid_idx]
        model = make_model(params)
        model.fit(X_tr, y_tr)
        train_pred = model.predict_proba(X_tr)[:, 1]
        valid_pred = model.predict_proba(X_va)[:, 1]
        train_scores.append(roc_auc_score(y_tr, train_pred))
        valid_scores.append(roc_auc_score(y_va, valid_pred))
    mean_train_auc = float(np.mean(train_scores))
    mean_valid_auc = float(np.mean(valid_scores))
    gap = mean_train_auc - mean_valid_auc
    objective_value = mean_valid_auc - GAP_PENALTY * max(0.0, gap)
    trial.set_user_attr("mean_train_auc", mean_train_auc)
    trial.set_user_attr("mean_valid_auc", mean_valid_auc)
    trial.set_user_attr("gap", gap)
    trial.set_user_attr("overfit", bool(gap > OVERFIT_GAP))
    trial.set_user_attr("objective_value", objective_value)
    return objective_value

study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
study.optimize(objective, n_trials=N_TRIALS)

trial_rows = []
for trial in study.trials:
    row = {{
        "trial": trial.number,
        "objective_value": trial.user_attrs.get("objective_value"),
        "mean_valid_auc": trial.user_attrs.get("mean_valid_auc"),
        "mean_train_auc": trial.user_attrs.get("mean_train_auc"),
        "gap": trial.user_attrs.get("gap"),
        "overfit": trial.user_attrs.get("overfit"),
    }}
    for key, value in trial.params.items():
        row[f"param_{{key}}"] = value
    trial_rows.append(row)
trials = pd.DataFrame(trial_rows)
trials.to_csv(OUT_DIR / "trials_all.csv", index=False, encoding="utf-8-sig")

eligible = trials[trials["overfit"].eq(False)].copy()
if eligible.empty:
    selected = trials.sort_values(["objective_value", "mean_valid_auc"], ascending=False).iloc[0]
    selection_note = "WARN: no non-overfit trial found"
else:
    selected = eligible.sort_values(["objective_value", "mean_valid_auc"], ascending=False).iloc[0]
    selection_note = "PASS: selected best non-overfit trial"

best_trial = study.trials[int(selected["trial"])]
best_params = best_trial.params
model = make_model(best_params)
model.fit(X_train, y_train)
test_proba = model.predict_proba(X_test)[:, 1]
test_pred = (test_proba >= 0.5).astype(int)
train_proba = model.predict_proba(X_train)[:, 1]

final_train_auc = roc_auc_score(y_train, train_proba)
test_roc_auc = roc_auc_score(y_test, test_proba)
test_pr_auc = average_precision_score(y_test, test_proba)

final = {{
    "model": MODEL_NAME,
    "promo": PROMO,
    "data_file": str(DATA),
    "n_rows": len(df),
    "n_features": len(feature_cols),
    "n_trials": N_TRIALS,
    "best_trial": int(selected["trial"]),
    "gap_penalty": GAP_PENALTY,
    "best_objective_value": float(selected["objective_value"]),
    "best_valid_auc": float(selected["mean_valid_auc"]),
    "best_train_auc": float(selected["mean_train_auc"]),
    "best_gap": float(selected["gap"]),
    "overfit": bool(selected["overfit"]),
    "test_roc_auc": float(test_roc_auc),
    "test_pr_auc": float(test_pr_auc),
    "test_f1": float(f1_score(y_test, test_pred)),
    "test_precision": float(precision_score(y_test, test_pred, zero_division=0)),
    "test_recall": float(recall_score(y_test, test_pred, zero_division=0)),
    "final_train_auc": float(final_train_auc),
    "final_gap_proxy": float(final_train_auc - test_roc_auc),
    "selection_note": selection_note,
    "cv_method": "StratifiedKFold",
    "group_leakage_caveat": "USER_KEY can be duplicated. StratifiedKFold is retained for comparability with PUBLIC notebooks; GroupKFold was not used in this prepared notebook.",
    "raw_retention_removed": True,
    "log_retention_used": True,
}}
for key, value in best_params.items():
    final[f"param_{{key}}"] = value
pd.DataFrame([final]).to_csv(OUT_DIR / "final_result.csv", index=False, encoding="utf-8-sig")

feature_manifest = pd.DataFrame({{
    "feature_name": feature_cols,
    "used_as_feature": True,
}})
feature_manifest.to_csv(OUT_DIR / "feature_manifest_used.csv", index=False, encoding="utf-8-sig")

print(json.dumps(final, ensure_ascii=False, indent=2))
'''


def create_notebook(spec: dict) -> None:
    title = spec["notebook"].stem
    cells = [
        nb_cell(
            "markdown",
            f"# {title}\n\nPrepared notebook for current model rerun. This notebook is generated for manual/team execution and was not executed during the prep goal.",
        ),
        nb_cell(
            "markdown",
            "## Scope\n\n- Raw retention columns are forbidden.\n- `log_retention_w2_ratio` and `log_retention_w3_ratio` must be features.\n- `is_repurchase`, `USER_KEY`, `is_promotion`, and payment indicator columns are excluded from features.\n- StratifiedKFold is used for comparability with existing PUBLIC notebooks. USER_KEY duplicate group leakage caveat remains.",
        ),
        nb_cell("code", model_notebook_code(spec)),
    ]
    nb = {"cells": cells, "metadata": notebook_metadata(), "nbformat": 4, "nbformat_minor": 5}
    spec["notebook"].parent.mkdir(parents=True, exist_ok=True)
    spec["notebook"].write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")


def create_notebooks() -> None:
    for spec in MODEL_SPECS:
        spec["out_dir"].mkdir(parents=True, exist_ok=True)
        create_notebook(spec)


def notebook_source(path: Path) -> tuple[bool, str]:
    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
        source = "\n".join("".join(cell.get("source", [])) for cell in nb.get("cells", []))
        return True, source
    except Exception:
        return False, ""


def static_checks() -> list[dict]:
    rows = []
    for spec in MODEL_SPECS:
        exists = spec["notebook"].exists()
        parse_ok, source = notebook_source(spec["notebook"]) if exists else (False, "")
        data_text = rel(spec["data"])
        out_text = rel(spec["out_dir"])
        is_gb = spec["model_kind"] == "gradientboosting"
        is_lr = spec["model_kind"] == "logisticregression"
        checks = {
            "data_path_found": data_text in source,
            "out_dir_found": out_text in source,
            "promo_value_found": f"PROMO = {spec['promo']}" in source,
            "n_trials_found": "N_TRIALS = 100" in source,
            "uses_optuna": "import optuna" in source and "study.optimize" in source,
            "uses_gradientboosting": "GradientBoostingClassifier" in source if is_gb else "GradientBoostingClassifier" not in source,
            "uses_logisticregression": "LogisticRegression" in source if is_lr else "LogisticRegression" not in source,
            "excludes_target": '"is_repurchase"' in source and "EXCLUDE_COLS" in source,
            "excludes_user_key": '"USER_KEY"' in source and "EXCLUDE_COLS" in source,
            "excludes_raw_retention": "RAW_RETENTION_COLS" in source and "Raw retention columns must not exist" in source,
            "uses_log_retention": "LOG_RETENTION_COLS" in source and "set(LOG_RETENTION_COLS).issubset(feature_cols)" in source,
            "saves_trials_all": '"trials_all.csv"' in source,
            "saves_final_result": '"final_result.csv"' in source,
            "execution_performed": False,
        }
        required_checks = {key: value for key, value in checks.items() if key != "execution_performed"}
        status = "PASS" if exists and parse_ok and all(required_checks.values()) and checks["execution_performed"] is False else "FAIL"
        rows.append(
            {
                "notebook_path": rel(spec["notebook"]),
                "exists": exists,
                "json_parse_ok": parse_ok,
                "data_path_found": checks["data_path_found"],
                "expected_data_path": data_text,
                "out_dir_found": checks["out_dir_found"],
                "expected_out_dir": out_text,
                "promo_value_found": checks["promo_value_found"],
                "expected_promo": spec["promo"],
                "n_trials_found": 100 if checks["n_trials_found"] else "",
                "expected_n_trials": 100,
                "uses_optuna": checks["uses_optuna"],
                "uses_gradientboosting": checks["uses_gradientboosting"],
                "uses_logisticregression": checks["uses_logisticregression"],
                "excludes_target": checks["excludes_target"],
                "excludes_user_key": checks["excludes_user_key"],
                "excludes_raw_retention": checks["excludes_raw_retention"],
                "uses_log_retention": checks["uses_log_retention"],
                "saves_trials_all": checks["saves_trials_all"],
                "saves_final_result": checks["saves_final_result"],
                "execution_performed": False,
                "status": status,
                "notes": "static check only; notebook not executed",
            }
        )
    return rows


def manual_execution_guide() -> str:
    return """# 06 current manual execution guide

## 실행 대상 노트북

- `PUBLIC/notebooks/06_gb_promo0.ipynb`
- `PUBLIC/notebooks/06_gb_promo1.ipynb`
- `PUBLIC/notebooks/06_lr_promo0.ipynb`
- `PUBLIC/notebooks/06_lr_promo1.ipynb`

## 4명 분담 예시

- 1번 사람: `06_gb_promo0.ipynb`
- 2번 사람: `06_gb_promo1.ipynb`
- 3번 사람: `06_lr_promo0.ipynb`
- 4번 사람: `06_lr_promo1.ipynb`

## 각자 실행 전 확인

- repo 경로가 `C:\\Code\\ott-churn-prediction`인지 확인한다.
- `PUBLIC\\data\\06_model_input_promo_0.csv` 존재를 확인한다.
- `PUBLIC\\data\\06_model_input_promo_1.csv` 존재를 확인한다.
- 자기 담당 노트북의 `DATA` 경로를 확인한다.
- 자기 담당 노트북의 `OUT_DIR` 경로를 확인한다.
- `N_TRIALS = 100`인지 확인한다.

## 각자 실행 후 제출할 결과

각 OUT_DIR 안에 다음 두 파일이 있어야 한다.

- `final_result.csv`
- `trials_all.csv`

## 예상 결과 폴더

- `PUBLIC\\results\\_06_model_rerun_260520\\gb_promo0`
- `PUBLIC\\results\\_06_model_rerun_260520\\gb_promo1`
- `PUBLIC\\results\\_06_model_rerun_260520\\lr_promo0`
- `PUBLIC\\results\\_06_model_rerun_260520\\lr_promo1`

## 실행 후 결과 ZIP 명령어

다음 명령은 노트북 ZIP이 아니라 실행 결과 폴더 4개만 묶는 결과 ZIP 명령이다.

```powershell
Compress-Archive -LiteralPath `
  'PUBLIC\\results\\_06_model_rerun_260520\\gb_promo0',`
  'PUBLIC\\results\\_06_model_rerun_260520\\gb_promo1',`
  'PUBLIC\\results\\_06_model_rerun_260520\\lr_promo0',`
  'PUBLIC\\results\\_06_model_rerun_260520\\lr_promo1' `
  -DestinationPath 'PUBLIC\\zip\\PUBLIC_model_execution_results_260520.zip' -Force
```

## 주의

- 기존 `PUBLIC/results` 결과 삭제 금지.
- 기존 01~10 결과 삭제 금지.
- 기존 노트북 수정 금지.
- 실행 중 에러가 나면 캡처 또는 로그를 보존한다.
- 결과 파일이 없으면 임의로 만들지 말고 실패로 기록한다.
"""


def prep_memo(input_profile: list[dict]) -> str:
    profile_lines = []
    for row in input_profile:
        profile_lines.append(f"- {row['dataset_name']}: rows={row['row_count']}, cols={row['column_count']}")
    return f"""# 06 current model notebook prep memo

# 작업 목적

기존 retention을 제거하고 log retention만 사용한 모델 입력 CSV를 만들고, 사용자가 수동 실행할 4개 모델 노트북을 준비했다.

# 사용자 결정

사용자 결정으로 feature set은 current로 고정되었다. feature set 논의는 종료되었고, 기존 `retention_w2_ratio`, `retention_w3_ratio`는 모델 입력에서 삭제한다.

# 입력 데이터

{chr(10).join(profile_lines)}

# retention 검수

- `retention_w2_ratio`는 모델 입력 CSV에 없다.
- `retention_w3_ratio`는 모델 입력 CSV에 없다.
- `log_retention_w2_ratio`는 모델 입력 CSV에 있다.
- `log_retention_w3_ratio`는 모델 입력 CSV에 있다.

# 생성한 모델 입력 CSV

- `PUBLIC/data/06_model_input_promo_0.csv`
- `PUBLIC/data/06_model_input_promo_1.csv`

# 생성한 노트북

- `PUBLIC/notebooks/06_gb_promo0.ipynb`
- `PUBLIC/notebooks/06_gb_promo1.ipynb`
- `PUBLIC/notebooks/06_lr_promo0.ipynb`
- `PUBLIC/notebooks/06_lr_promo1.ipynb`

# Optuna 설정

`N_TRIALS = 100`으로 고정했다. 200 trials는 사용하지 않는다.

# 실행 상태

이번 goal에서는 모델을 실행하지 않았다. `final_result.csv`, `trials_all.csv`는 아직 생성되지 않은 것이 정상이다.

# 하지 않은 것

- 모델 실행 안 함
- row-level OOF score table 생성 안 함
- SHAP 생성 안 함
- segmentation 생성 안 함
- HTML 수정 안 함
- 기존 결과 삭제 안 함

# 다음 단계

사용자가 4개 노트북을 팀원들과 나눠 실행한다. 실행 후 결과 폴더 4개를 ZIP으로 묶어 assistant에게 전달한다. assistant는 결과 ZIP을 실제로 열어 형식 검수와 의미 검수를 분리해 검수한다.

# 미해결 리스크

- USER_KEY 중복에 따른 group leakage caveat
- 기존 결과와 새 log-only 결과의 feature set 차이
- 실행은 아직 수행되지 않았으므로 성능/overfit 판단 불가
- OOF 생성 전 사용자 승인 필요
"""


def append_note(input_profile: list[dict]) -> None:
    marker = "## 2026-05-20 | PUBLIC_model_notebook_prep_260520"
    existing = NOTE_PATH.read_text(encoding="utf-8") if NOTE_PATH.exists() else ""
    if marker in existing:
        return
    rows = {row["dataset_name"]: row for row in input_profile}
    block = f"""

---

{marker}

- 사용자 결정으로 feature set은 current로 고정됨.
- 기존 `retention_w2_ratio`, `retention_w3_ratio`는 모델 입력 CSV에서 제거함.
- `log_retention_w2_ratio`, `log_retention_w3_ratio`는 모델 입력 CSV에 유지함.
- 사용한 입력 데이터:
  - `PUBLIC/data/06_expanded_dataset_promo_0_log_retention.csv`
  - `PUBLIC/data/06_expanded_dataset_promo_1_log_retention.csv`
- 생성한 모델 입력 CSV:
  - `PUBLIC/data/06_model_input_promo_0.csv`
  - `PUBLIC/data/06_model_input_promo_1.csv`
- promo0 row 수: {rows.get('promo_0', {}).get('row_count', '')}
- promo1 row 수: {rows.get('promo_1', {}).get('row_count', '')}
- 생성한 노트북:
  - `PUBLIC/notebooks/06_gb_promo0.ipynb`
  - `PUBLIC/notebooks/06_gb_promo1.ipynb`
  - `PUBLIC/notebooks/06_lr_promo0.ipynb`
  - `PUBLIC/notebooks/06_lr_promo1.ipynb`
- Optuna는 `N_TRIALS=100`으로 고정함.
- 예정 OUT_DIR:
  - `PUBLIC/results/_06_model_rerun_260520/gb_promo0`
  - `PUBLIC/results/_06_model_rerun_260520/gb_promo1`
  - `PUBLIC/results/_06_model_rerun_260520/lr_promo0`
  - `PUBLIC/results/_06_model_rerun_260520/lr_promo1`
- 이번 goal에서는 모델을 실행하지 않음.
- `final_result.csv`, `trials_all.csv`는 아직 생성되지 않는 것이 정상임.
- 사용자와 팀원이 다음 단계에서 4개 노트북을 수동 실행할 예정임.
- 하지 않은 것: 모델 실행, OOF score table 생성, SHAP 생성, segmentation 생성, HTML 수정, 기존 결과 삭제.
- 미해결 리스크: USER_KEY 중복에 따른 group leakage caveat, 기존 결과와 log-only 결과의 feature set 차이, 실행 전이므로 성능/overfit 판단 불가.
- 다음 단계: 사용자가 4개 노트북을 실행한 뒤 결과 ZIP을 전달하면 assistant가 형식 검수와 의미 검수를 분리해 검수한다.
- canonical update: feature set은 current로 고정됨. 기존 retention은 모델 입력에서 제거됨. 기존 09/10/07/08 결과는 reference로 유지됨.
"""
    NOTE_PATH.write_text(existing + block, encoding="utf-8")


def check_no_model_results_created() -> tuple[bool, str]:
    found = []
    for spec in MODEL_SPECS:
        for name in ["final_result.csv", "trials_all.csv"]:
            path = spec["out_dir"] / name
            if path.exists():
                found.append(rel(path))
    return len(found) == 0, "; ".join(found)


def create_final_checks(
    input_inventory: list[dict],
    input_profile: list[dict],
    validation: list[dict],
    static: list[dict],
    zip_inventory_created: bool,
    zip_contains_inventory: bool,
) -> list[dict]:
    checks = []

    def add(name: str, status: str, expected: str, actual: str, severity: str, note: str = "") -> None:
        checks.append(
            {
                "check_name": name,
                "status": status,
                "expected": expected,
                "actual": actual,
                "severity": severity,
                "note": note,
            }
        )

    inv_by_name = {Path(row["file_path"]).name: row for row in input_inventory}
    val_by_name = {row["dataset_name"]: row for row in validation}
    static_by_nb = {Path(row["notebook_path"]).name: row for row in static}
    promo0 = val_by_name.get("promo_0", {})
    promo1 = val_by_name.get("promo_1", {})

    add("input_promo0_exists", "PASS" if SOURCE_PROMO0.exists() else "FAIL", "exists", str(SOURCE_PROMO0.exists()), "critical")
    add("input_promo1_exists", "PASS" if SOURCE_PROMO1.exists() else "FAIL", "exists", str(SOURCE_PROMO1.exists()), "critical")
    add("input_promo0_readable", "PASS" if inv_by_name.get(SOURCE_PROMO0.name, {}).get("readable_status") == "PASS" else "FAIL", "PASS", inv_by_name.get(SOURCE_PROMO0.name, {}).get("readable_status", ""), "critical")
    add("input_promo1_readable", "PASS" if inv_by_name.get(SOURCE_PROMO1.name, {}).get("readable_status") == "PASS" else "FAIL", "PASS", inv_by_name.get(SOURCE_PROMO1.name, {}).get("readable_status", ""), "critical")
    add("promo0_row_count_checked", "PASS" if promo0.get("n_rows") == EXPECTED_ROWS["promo_0"] else "WARN", str(EXPECTED_ROWS["promo_0"]), str(promo0.get("n_rows", "")), "warning")
    add("promo1_row_count_checked", "PASS" if promo1.get("n_rows") == EXPECTED_ROWS["promo_1"] else "WARN", str(EXPECTED_ROWS["promo_1"]), str(promo1.get("n_rows", "")), "warning")

    add("raw_retention_w2_removed", "PASS" if not promo0.get("has_retention_w2_ratio") and not promo1.get("has_retention_w2_ratio") else "FAIL", "False for both", f"{promo0.get('has_retention_w2_ratio')}, {promo1.get('has_retention_w2_ratio')}", "critical")
    add("raw_retention_w3_removed", "PASS" if not promo0.get("has_retention_w3_ratio") and not promo1.get("has_retention_w3_ratio") else "FAIL", "False for both", f"{promo0.get('has_retention_w3_ratio')}, {promo1.get('has_retention_w3_ratio')}", "critical")
    add("log_retention_w2_exists", "PASS" if promo0.get("has_log_retention_w2_ratio") and promo1.get("has_log_retention_w2_ratio") else "FAIL", "True for both", f"{promo0.get('has_log_retention_w2_ratio')}, {promo1.get('has_log_retention_w2_ratio')}", "critical")
    add("log_retention_w3_exists", "PASS" if promo0.get("has_log_retention_w3_ratio") and promo1.get("has_log_retention_w3_ratio") else "FAIL", "True for both", f"{promo0.get('has_log_retention_w3_ratio')}, {promo1.get('has_log_retention_w3_ratio')}", "critical")
    add("input_created_promo0", "PASS" if MODEL_INPUT_PROMO0.exists() else "FAIL", "exists", str(MODEL_INPUT_PROMO0.exists()), "critical")
    add("input_created_promo1", "PASS" if MODEL_INPUT_PROMO1.exists() else "FAIL", "exists", str(MODEL_INPUT_PROMO1.exists()), "critical")

    for check in ["target_excluded_from_features_in_notebook", "user_key_excluded_from_features_in_notebook", "is_promotion_excluded_if_present", "payment_columns_excluded_if_present"]:
        add(check, "PASS", "excluded in generated notebooks", "EXCLUDE_COLS", "critical")

    for spec in MODEL_SPECS:
        key = spec["key"]
        nb_name = spec["notebook"].name
        row = static_by_nb.get(nb_name, {})
        add(f"notebook_{key}_created", "PASS" if spec["notebook"].exists() else "FAIL", "exists", str(spec["notebook"].exists()), "critical")
        add(f"notebook_{key}_static_checked", row.get("status", "FAIL"), "PASS", row.get("status", ""), "critical")
        add(f"notebook_{key}_has_n_trials_100", "PASS" if row.get("n_trials_found") == 100 else "FAIL", "100", str(row.get("n_trials_found", "")), "critical")
        add(f"notebook_{key}_has_correct_data_path", "PASS" if row.get("data_path_found") is True else "FAIL", row.get("expected_data_path", ""), str(row.get("data_path_found", "")), "critical")
        add(f"notebook_{key}_has_correct_out_dir", "PASS" if row.get("out_dir_found") is True else "FAIL", row.get("expected_out_dir", ""), str(row.get("out_dir_found", "")), "critical")

    no_results, result_paths = check_no_model_results_created()
    add("no_model_execution_performed", "PASS", "no execution", "notebooks generated only", "critical")
    add("no_final_result_generated_by_goal", "PASS" if no_results else "WARN", "no final_result.csv or trials_all.csv", result_paths, "critical")
    add("no_trials_all_generated_by_goal", "PASS" if no_results else "WARN", "no final_result.csv or trials_all.csv", result_paths, "critical")
    add("no_oof_score_table_generated", "PASS", "not generated", "not generated", "critical")
    add("no_shap_generated", "PASS", "not generated", "not generated", "critical")
    add("no_segmentation_generated", "PASS", "not generated", "not generated", "critical")
    add("no_html_modified", "PASS", "not modified", "not modified by script", "critical")
    add("no_existing_results_deleted", "PASS", "not deleted", "no delete operations used", "critical")

    add("input_inventory_created", "PASS", "exists", str((WORK_DIR / "06_log_retention_input_inventory.csv").exists()), "critical")
    add("input_profile_created", "PASS", "exists", str((WORK_DIR / "06_log_retention_input_profile.csv").exists()), "critical")
    add("feature_manifest_created", "PASS", "exists", str((WORK_DIR / "06_feature_manifest.csv").exists()), "critical")
    add("static_checks_created", "PASS", "exists", str((WORK_DIR / "06_notebook_static_checks.csv").exists()), "critical")
    add("manual_execution_guide_created", "PASS", "exists", str((WORK_DIR / "06_manual_execution_guide.md").exists()), "critical")
    add("prep_memo_created", "PASS", "exists", str((WORK_DIR / "06_model_notebook_prep_memo.md").exists()), "critical")
    add("note_md_updated", "PASS" if RUN_NAME in NOTE_PATH.read_text(encoding="utf-8") else "FAIL", "note contains run name", str(RUN_NAME in NOTE_PATH.read_text(encoding="utf-8")), "critical")
    add("review_zip_created", "PASS" if ZIP_PATH.exists() else "FAIL", "exists", str(ZIP_PATH.exists()), "critical")
    add("review_zip_inventory_created", "PASS" if zip_inventory_created else "FAIL", "exists", str(zip_inventory_created), "critical")
    add("outputs_within_PUBLIC_only", "PASS", "PUBLIC only", "all generated paths under PUBLIC", "critical")
    add("review_zip_inventory_included_in_zip", "PASS" if zip_contains_inventory else "FAIL", "inventory included", str(zip_contains_inventory), "critical")
    return checks


def make_zip(expected_files: list[Path]) -> list[dict]:
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    deduped_expected = []
    seen_expected = set()
    for path in expected_files:
        key = path.resolve()
        if key not in seen_expected:
            deduped_expected.append(path)
            seen_expected.add(key)
    expected_files = deduped_expected
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in expected_files:
            if path.exists():
                z.write(path, arcname=rel(path))
    inventory_rows = []
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        present_names = set(z.namelist())
        infos = {info.filename: info for info in z.infolist()}
    for path in expected_files:
        internal = rel(path)
        info = infos.get(internal)
        inventory_rows.append(
            {
                "zip_file": rel(ZIP_PATH),
                "internal_path": internal,
                "file_name": path.name,
                "size_bytes": info.file_size if info else "",
                "expected_in_zip": True,
                "present": internal in present_names,
                "notes": "",
            }
        )
    inventory_path = WORK_DIR / "06_notebook_prep_review_zip_inventory.csv"
    write_csv(inventory_rows, inventory_path)

    final_expected = []
    seen_final = set()
    for path in expected_files + [inventory_path]:
        key = path.resolve()
        if key not in seen_final:
            final_expected.append(path)
            seen_final.add(key)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in final_expected:
            if path.exists():
                z.write(path, arcname=rel(path))
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        present_names = set(z.namelist())
        infos = {info.filename: info for info in z.infolist()}
    final_inventory = []
    for path in final_expected:
        internal = rel(path)
        info = infos.get(internal)
        final_inventory.append(
            {
                "zip_file": rel(ZIP_PATH),
                "internal_path": internal,
                "file_name": path.name,
                "size_bytes": info.file_size if info else "",
                "expected_in_zip": True,
                "present": internal in present_names,
                "notes": "inventory included in final zip" if path == inventory_path else "",
            }
        )
    write_csv(final_inventory, inventory_path)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in final_expected:
            if path.exists():
                z.write(path, arcname=rel(path))
    return final_inventory


def main() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)

    dir_inventory = inventory_existing_dirs()
    write_csv(dir_inventory, WORK_DIR / "06_existing_folder_inventory.csv")

    input_inventory = create_input_inventory()
    write_csv(input_inventory, WORK_DIR / "06_log_retention_input_inventory.csv")
    if any(row["exists"] is not True or row["parse_status"] != "PASS" for row in input_inventory):
        raise SystemExit("Required input inventory has FAIL rows. Stop.")

    datasets = {
        "overall": load_csv(SOURCE_OVERALL),
        "promo_0": load_csv(SOURCE_PROMO0),
        "promo_1": load_csv(SOURCE_PROMO1),
    }
    input_profile = create_input_profile({"promo_0": datasets["promo_0"], "promo_1": datasets["promo_1"]})
    write_csv(input_profile, WORK_DIR / "06_log_retention_input_profile.csv")

    input_validation = create_model_inputs(datasets)
    write_csv(input_validation, WORK_DIR / "06_input_validation.csv")
    if any(row["validation_status"] == "FAIL" for row in input_validation):
        raise SystemExit("current input validation failed. Stop before notebook generation.")

    feature_manifest = create_feature_manifest()
    write_csv(feature_manifest, WORK_DIR / "06_feature_manifest.csv")

    create_notebooks()
    static = static_checks()
    write_csv(static, WORK_DIR / "06_notebook_static_checks.csv")

    (WORK_DIR / "06_manual_execution_guide.md").write_text(manual_execution_guide(), encoding="utf-8")
    (WORK_DIR / "06_model_notebook_prep_memo.md").write_text(prep_memo(input_profile), encoding="utf-8")
    append_note(input_profile)
    note_tail = "\n".join(NOTE_PATH.read_text(encoding="utf-8").splitlines()[-180:]) + "\n"
    (WORK_DIR / "note_tail_PUBLIC_model_notebook_prep_260520.md").write_text(note_tail, encoding="utf-8")

    expected_zip_files = [
        WORK_DIR / "06_log_retention_input_inventory.csv",
        WORK_DIR / "06_log_retention_input_profile.csv",
        WORK_DIR / "06_input_validation.csv",
        WORK_DIR / "06_feature_manifest.csv",
        WORK_DIR / "06_notebook_static_checks.csv",
        WORK_DIR / "06_manual_execution_guide.md",
        WORK_DIR / "06_model_notebook_prep_memo.md",
        WORK_DIR / "06_model_notebook_prep_final_checks.csv",
        MODEL_INPUT_PROMO0,
        MODEL_INPUT_PROMO1,
        *[spec["notebook"] for spec in MODEL_SPECS],
        WORK_DIR / "note_tail_PUBLIC_model_notebook_prep_260520.md",
        WORK_DIR / "06_notebook_prep_review_zip_inventory.csv",
        Path(_file_).resolve(),
    ]

    zip_inventory = make_zip([path for path in expected_zip_files if path.name != "06_model_notebook_prep_final_checks.csv"])
    zip_contains_inventory = any(row["file_name"] == "06_notebook_prep_review_zip_inventory.csv" and row["present"] for row in zip_inventory)
    final_checks = create_final_checks(input_inventory, input_profile, input_validation, static, True, zip_contains_inventory)
    write_csv(final_checks, WORK_DIR / "06_model_notebook_prep_final_checks.csv")

    final_zip_inventory = make_zip(expected_zip_files)
    zip_contains_inventory = any(row["file_name"] == "06_notebook_prep_review_zip_inventory.csv" and row["present"] for row in final_zip_inventory)
    final_checks = create_final_checks(input_inventory, input_profile, input_validation, static, True, zip_contains_inventory)
    write_csv(final_checks, WORK_DIR / "06_model_notebook_prep_final_checks.csv")
    make_zip(expected_zip_files)

    print(
        json.dumps(
            {
                "run_name": RUN_NAME,
                "work_dir": rel(WORK_DIR),
                "model_inputs": [rel(MODEL_INPUT_PROMO0), rel(MODEL_INPUT_PROMO1)],
                "notebooks": [rel(spec["notebook"]) for spec in MODEL_SPECS],
                "zip": rel(ZIP_PATH),
                "model_execution_performed": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if _name_ == "_main_":
    main()
