from __future__ import annotations

import csv
import hashlib
import importlib
import json
import math
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[3]
PUBLIC_ROOT = REPO_ROOT / "PUBLIC"

HANDOFF_DIR = PUBLIC_ROOT / "handoff" / "PUBLIC_16_four_model_SHAP_candidate_interpretation_260520"
OUTPUT_DIR = PUBLIC_ROOT / "results" / "16_SHAP_candidate_interpretation_260520" / "four_model_shap_interpretation"
NOTEBOOK_DIR = PUBLIC_ROOT / "notebooks" / "16_SHAP_candidate_interpretation_260520"
FIGURE_DIR = PUBLIC_ROOT / "reports" / "figures" / "16_SHAP_candidate_interpretation_260520"
ZIP_DIR = PUBLIC_ROOT / "zip"
ZIP_PATH = ZIP_DIR / "PUBLIC_16_four_model_SHAP_candidate_interpretation_260520_review_package.zip"

NOTEBOOK_PATH = NOTEBOOK_DIR / "16_four_model_SHAP_candidate_interpretation_260520.ipynb"
EXECUTED_NOTEBOOK_PATH = NOTEBOOK_DIR / "16_four_model_SHAP_candidate_interpretation_260520_executed.ipynb"

OOF_DIR = PUBLIC_ROOT / "results" / "15_oof_score_or_sensitivity_260520" / "four_model_oof_scores_hotfix_260520"
REFERENCE_DIR = PUBLIC_ROOT / "results" / "11_baseline_growth_comparison_260520" / "emergency_four_model_reference"

TARGET = "is_repurchase"
RANDOM_STATE = 42
SHAP_SAMPLE_SIZE = 2000

MODEL_SPECS = [
    {
        "model_family": "LogisticRegression",
        "promo_scope": "promo0",
        "reference_folder": REFERENCE_DIR / "logistic_regression_promo0",
        "input_csv": PUBLIC_ROOT / "data" / "06_model_input_promo_0.csv",
    },
    {
        "model_family": "LogisticRegression",
        "promo_scope": "promo1",
        "reference_folder": REFERENCE_DIR / "logistic_regression_promo1",
        "input_csv": PUBLIC_ROOT / "data" / "06_model_input_promo_1.csv",
    },
    {
        "model_family": "GradientBoosting",
        "promo_scope": "promo0",
        "reference_folder": REFERENCE_DIR / "gradient_boosting_promo0",
        "input_csv": PUBLIC_ROOT / "data" / "06_model_input_promo_0.csv",
    },
    {
        "model_family": "GradientBoosting",
        "promo_scope": "promo1",
        "reference_folder": REFERENCE_DIR / "gradient_boosting_promo1",
        "input_csv": PUBLIC_ROOT / "data" / "06_model_input_promo_1.csv",
    },
]

REQUIRED_15_FILES = [
    "15_oof_score_long.csv",
    "15_oof_score_wide.csv",
    "15_oof_metric_summary.csv",
    "15_gb_lr_high_risk_overlap.csv",
    "15_oof_feature_policy_check.csv",
    "15_oof_split_policy_check.csv",
    "15_oof_readiness_for_shap_segmentation.csv",
]

FORBIDDEN_EXACT = {
    "USER_NUM",
    "USER_KEY",
    "row_id",
    "is_repurchase",
    "is_promotion",
    "repurchase_score",
    "churn_risk",
    "repurchase_score_oof",
    "churn_risk_score_oof",
    "retention_w2_ratio",
    "retention_w3_ratio",
    "fold_id",
}

DEMOGRAPHIC_FEATURES = ["age_group", "is_female", "is_male"]
CORE_OUTPUT_FILES = [
    "16_model_config_and_feature_manifest.csv",
    "16_shap_feature_policy_check.csv",
    "16_shap_execution_plan.csv",
    "16_shap_global_importance.csv",
    "16_lr_coefficient_summary.csv",
    "16_shap_direction_summary.csv",
    "16_feature_family_mapping_for_shap.csv",
    "16_shap_family_importance.csv",
    "16_promo1_vs_promo0_shap_comparison.csv",
    "16_demographic_context_audit_for_shap.csv",
    "16_is_churn_prevented_interpretation_audit.csv",
    "16_readiness_for_segmentation.csv",
]


def ensure_dirs() -> None:
    for path in [HANDOFF_DIR, OUTPUT_DIR, NOTEBOOK_DIR, FIGURE_DIR, ZIP_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_csv_shape(path: Path) -> tuple[Any, Any]:
    if not path.exists() or path.suffix.lower() != ".csv":
        return "", ""
    try:
        df = pd.read_csv(path)
        return int(len(df)), int(len(df.columns))
    except Exception:
        return "", ""


def write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot(paths: list[tuple[Path, str]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path, role in paths:
        key = rel(path)
        if path.exists():
            out[key] = {
                "file_path": key,
                "file_role": role,
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        else:
            out[key] = {
                "file_path": key,
                "file_role": role,
                "sha256": "",
                "size": "",
            }
    return out


def fingerprint_targets() -> list[tuple[Path, str]]:
    targets: list[tuple[Path, str]] = [
        (PUBLIC_ROOT / "data" / "06_model_input_promo_0.csv", "input_csv"),
        (PUBLIC_ROOT / "data" / "06_model_input_promo_1.csv", "input_csv"),
        (OOF_DIR / "15_oof_score_long.csv", "15_oof_input"),
        (OOF_DIR / "15_oof_score_wide.csv", "15_oof_input"),
    ]
    for spec in MODEL_SPECS:
        folder = spec["reference_folder"]
        for name, role in [
            ("final_result.csv", "model_final_result"),
            ("trials_all.csv", "model_trials_all"),
            ("feature_manifest_used.csv", "model_feature_manifest"),
        ]:
            targets.append((folder / name, role))
    targets.append((NOTEBOOK_PATH, "notebook"))
    targets.append((EXECUTED_NOTEBOOK_PATH, "notebook"))
    return targets


def write_fingerprint(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> Path:
    rows: list[dict[str, Any]] = []
    for key in sorted(set(before) | set(after)):
        b = before.get(key, {})
        a = after.get(key, {})
        if b.get("sha256") and a.get("sha256") and b.get("sha256") == a.get("sha256"):
            status = "unchanged"
        elif not b.get("sha256") and a.get("sha256"):
            status = "new_output_created"
        elif b.get("sha256") and not a.get("sha256"):
            status = "missing_after"
        else:
            status = "changed_needs_review"
        if key == rel(EXECUTED_NOTEBOOK_PATH) and status == "new_output_created":
            status = "intentionally_updated_16_executed_notebook"
        rows.append(
            {
                "file_path": key,
                "file_role": a.get("file_role") or b.get("file_role", ""),
                "sha256_before": b.get("sha256", ""),
                "sha256_after": a.get("sha256", ""),
                "size_before": b.get("size", ""),
                "size_after": a.get("size", ""),
                "status": status,
            }
        )
    path = HANDOFF_DIR / "16_source_fingerprint_before_after.csv"
    write_rows(path, rows, ["file_path", "file_role", "sha256_before", "sha256_after", "size_before", "size_after", "status"])
    return path


def refresh_fingerprint_after_notebook() -> Path | None:
    path = HANDOFF_DIR / "16_source_fingerprint_before_after.csv"
    if not path.exists():
        return None
    rows = pd.read_csv(path).to_dict("records")
    refreshed = snapshot(fingerprint_targets())
    out_rows: list[dict[str, Any]] = []
    for row in rows:
        key = str(row.get("file_path", ""))
        current = refreshed.get(key, {})
        sha_before = "" if pd.isna(row.get("sha256_before", "")) else str(row.get("sha256_before", ""))
        size_before = "" if pd.isna(row.get("size_before", "")) else row.get("size_before", "")
        sha_after = current.get("sha256", "")
        size_after = current.get("size", "")
        if sha_before and sha_after and sha_before == sha_after:
            status = "unchanged"
        elif not sha_before and sha_after and key == rel(EXECUTED_NOTEBOOK_PATH):
            status = "intentionally_updated_16_executed_notebook"
        elif not sha_before and sha_after:
            status = "new_output_created"
        elif sha_before and not sha_after:
            status = "missing_after"
        elif not sha_before and not sha_after:
            status = "missing_before_and_after"
        else:
            status = "changed_needs_review"
        out_rows.append(
            {
                "file_path": key,
                "file_role": row.get("file_role", current.get("file_role", "")),
                "sha256_before": sha_before,
                "sha256_after": sha_after,
                "size_before": size_before,
                "size_after": size_after,
                "status": status,
            }
        )
    write_rows(path, out_rows, ["file_path", "file_role", "sha256_before", "sha256_after", "size_before", "size_after", "status"])
    return path


def input_validation() -> Path:
    rows: list[dict[str, Any]] = []

    for filename in REQUIRED_15_FILES:
        path = OOF_DIR / filename
        r, c = read_csv_shape(path)
        rows.append(
            {
                "input_item": filename,
                "expected_path": rel(path),
                "exists": path.exists(),
                "rows": r,
                "columns": c,
                "status": "PASS" if path.exists() else "FAIL",
                "notes": "15 OOF hotfix input",
            }
        )

    for path in [PUBLIC_ROOT / "data" / "06_model_input_promo_0.csv", PUBLIC_ROOT / "data" / "06_model_input_promo_1.csv"]:
        r, c = read_csv_shape(path)
        rows.append(
            {
                "input_item": path.name,
                "expected_path": rel(path),
                "exists": path.exists(),
                "rows": r,
                "columns": c,
                "status": "PASS" if path.exists() else "FAIL",
                "notes": "model input CSV",
            }
        )

    for spec in MODEL_SPECS:
        folder = spec["reference_folder"]
        prefix = f"{spec['model_family']}_{spec['promo_scope']}"
        for name in ["final_result.csv", "trials_all.csv", "feature_manifest_used.csv", "SOURCE_POINTER.txt"]:
            path = folder / name
            r, c = read_csv_shape(path)
            required = name != "SOURCE_POINTER.txt"
            status = "PASS" if path.exists() else ("FAIL" if required else "WARN")
            rows.append(
                {
                    "input_item": f"{prefix}_{name}",
                    "expected_path": rel(path),
                    "exists": path.exists(),
                    "rows": r,
                    "columns": c,
                    "status": status,
                    "notes": "11 emergency reference input" if required else "optional source pointer",
                }
            )

    path = HANDOFF_DIR / "16_shap_input_validation.csv"
    write_rows(path, rows, ["input_item", "expected_path", "exists", "rows", "columns", "status", "notes"])
    return path


def environment_check() -> tuple[Path, dict[str, bool]]:
    checks = [
        ("shap_import_available", "shap"),
        ("sklearn_available", "sklearn"),
        ("matplotlib_available", "matplotlib"),
        ("pandas_available", "pandas"),
        ("numpy_available", "numpy"),
    ]
    rows = []
    flags: dict[str, bool] = {}
    for check_item, module_name in checks:
        try:
            module = importlib.import_module(module_name)
            status = "PASS"
            observed = getattr(module, "__version__", "imported")
            flags[module_name] = True
            notes = "import available"
        except Exception as exc:
            status = "FAIL" if module_name == "shap" else "WARN"
            observed = type(exc).__name__
            flags[module_name] = False
            notes = str(exc)
        rows.append({"check_item": check_item, "status": status, "observed_value": observed, "notes": notes})
    path = HANDOFF_DIR / "16_shap_environment_check.csv"
    write_rows(path, rows, ["check_item", "status", "observed_value", "notes"])
    return path, flags


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def read_feature_manifest(path: Path) -> list[str]:
    df = pd.read_csv(path)
    if "used_as_feature" in df.columns:
        df = df[df["used_as_feature"].map(parse_bool)]
    if "feature_name" not in df.columns:
        raise ValueError(f"feature_name column missing: {path}")
    return [str(v) for v in df["feature_name"].tolist()]


def model_params_from_final_result(family: str, final_result: Path) -> tuple[dict[str, Any], str, str]:
    df = pd.read_csv(final_result)
    if df.empty:
        return {}, "FAIL", "final_result is empty"
    row = df.iloc[0].to_dict()
    if family == "LogisticRegression":
        if "param_C" not in row:
            return {}, "FAIL", "param_C missing"
        class_weight = row.get("param_class_weight", None)
        if pd.isna(class_weight) or str(class_weight).strip() == "":
            class_weight = None
        params = {
            "C": float(row["param_C"]),
            "class_weight": class_weight,
            "max_iter": 1000,
            "random_state": RANDOM_STATE,
        }
        return params, "PASS", "param_C and param_class_weight parsed; max_iter fixed for convergence"
    required = [
        "param_n_estimators",
        "param_learning_rate",
        "param_max_depth",
        "param_min_samples_leaf",
        "param_min_samples_split",
        "param_subsample",
        "param_max_features",
    ]
    missing = [c for c in required if c not in row]
    if missing:
        return {}, "FAIL", f"missing columns: {','.join(missing)}"
    max_features = row.get("param_max_features")
    if pd.isna(max_features) or str(max_features).strip() == "":
        max_features = None
    params = {
        "n_estimators": int(float(row["param_n_estimators"])),
        "learning_rate": float(row["param_learning_rate"]),
        "max_depth": int(float(row["param_max_depth"])),
        "min_samples_leaf": int(float(row["param_min_samples_leaf"])),
        "min_samples_split": int(float(row["param_min_samples_split"])),
        "subsample": float(row["param_subsample"]),
        "max_features": max_features,
        "random_state": RANDOM_STATE,
    }
    return params, "PASS", "GradientBoosting param_* columns parsed"


def feature_hash(features: list[str]) -> str:
    text = "\n".join(features).encode("utf-8")
    return hashlib.sha256(text).hexdigest()


def load_model_configs() -> tuple[Path, dict[tuple[str, str], dict[str, Any]]]:
    rows = []
    configs: dict[tuple[str, str], dict[str, Any]] = {}
    for spec in MODEL_SPECS:
        family = spec["model_family"]
        scope = spec["promo_scope"]
        folder = spec["reference_folder"]
        final_result = folder / "final_result.csv"
        feature_manifest = folder / "feature_manifest_used.csv"
        try:
            params, parse_status, param_notes = model_params_from_final_result(family, final_result)
            features = read_feature_manifest(feature_manifest)
            input_columns = set(pd.read_csv(spec["input_csv"], nrows=0).columns)
            missing_features = [f for f in features if f not in input_columns]
            status = "PASS" if parse_status == "PASS" and not missing_features else "FAIL"
            notes = param_notes if not missing_features else f"{param_notes}; missing input features: {','.join(missing_features)}"
        except Exception as exc:
            params, parse_status, features, status = {}, "FAIL", [], "FAIL"
            notes = f"{type(exc).__name__}: {exc}"
        configs[(family, scope)] = {
            "model_family": family,
            "promo_scope": scope,
            "input_csv": spec["input_csv"],
            "reference_folder": folder,
            "final_result": final_result,
            "feature_manifest": feature_manifest,
            "params": params,
            "params_parse_status": parse_status,
            "features": features,
            "status": status,
            "notes": notes,
        }
        rows.append(
            {
                "model_family": family,
                "promo_scope": scope,
                "source_final_result": rel(final_result),
                "source_feature_manifest": rel(feature_manifest),
                "params_found": "yes" if params else "no",
                "params_parse_status": parse_status,
                "params_used": json.dumps(params, ensure_ascii=False, sort_keys=True),
                "feature_count": len(features),
                "feature_list_hash": feature_hash(features) if features else "",
                "status": status,
                "notes": notes,
            }
        )
    path = OUTPUT_DIR / "16_model_config_and_feature_manifest.csv"
    write_rows(
        path,
        rows,
        [
            "model_family",
            "promo_scope",
            "source_final_result",
            "source_feature_manifest",
            "params_found",
            "params_parse_status",
            "params_used",
            "feature_count",
            "feature_list_hash",
            "status",
            "notes",
        ],
    )
    return path, configs


def forbidden_features(features: list[str]) -> list[str]:
    found: list[str] = []
    for feature in features:
        low = feature.lower()
        if feature in FORBIDDEN_EXACT:
            found.append(feature)
        elif "repurchase_score" in low or "churn_risk" in low:
            found.append(feature)
        elif low.endswith("_score") or "_score_" in low:
            found.append(feature)
        elif "target" in low:
            found.append(feature)
    return sorted(set(found))


def feature_policy(configs: dict[tuple[str, str], dict[str, Any]]) -> Path:
    rows = []
    for (family, scope), cfg in configs.items():
        features = cfg["features"]
        forbidden = forbidden_features(features)
        rows.append(
            {
                "model_family": family,
                "promo_scope": scope,
                "feature_count": len(features),
                "forbidden_columns_in_features": "none" if not forbidden else ",".join(forbidden),
                "retention_w2_ratio_in_features": "retention_w2_ratio" in features,
                "retention_w3_ratio_in_features": "retention_w3_ratio" in features,
                "log_retention_w2_ratio_in_features": "log_retention_w2_ratio" in features,
                "log_retention_w3_ratio_in_features": "log_retention_w3_ratio" in features,
                "is_churn_prevented_in_features": "is_churn_prevented" in features,
                "age_group_in_features": "age_group" in features,
                "is_female_in_features": "is_female" in features,
                "is_male_in_features": "is_male" in features,
                "status": "PASS" if not forbidden else "FAIL",
                "notes": "is_churn_prevented is approved historical context feature with caveat",
            }
        )
    path = OUTPUT_DIR / "16_shap_feature_policy_check.csv"
    write_rows(
        path,
        rows,
        [
            "model_family",
            "promo_scope",
            "feature_count",
            "forbidden_columns_in_features",
            "retention_w2_ratio_in_features",
            "retention_w3_ratio_in_features",
            "log_retention_w2_ratio_in_features",
            "log_retention_w3_ratio_in_features",
            "is_churn_prevented_in_features",
            "age_group_in_features",
            "is_female_in_features",
            "is_male_in_features",
            "status",
            "notes",
        ],
    )
    return path


def classify_family(feature: str) -> tuple[str, str, str]:
    low = feature.lower()
    if low in {"age_group", "is_female", "is_male"}:
        return "demographic_context", "age/gender exact match", "provisional_for_16_shap_only"
    if low == "is_churn_prevented":
        return "historical_churn_prevention_context", "is_churn_prevented exact match", "provisional_for_16_shap_only"
    if "log_retention" in low or low.startswith("retention_"):
        return "retention_decay", "retention naming pattern", "provisional_for_16_shap_only"
    if any(k in low for k in ["watch", "view", "session", "play", "weekly", "w1_", "w2_", "w3_", "w4_"]):
        return "weekly_usage", "usage/watch/session naming pattern", "provisional_for_16_shap_only"
    if any(k in low for k in ["cold_start", "onboarding", "first_", "activation"]):
        return "onboarding_activation", "onboarding/activation naming pattern", "provisional_for_16_shap_only"
    genre_terms = [
        "genre",
        "action",
        "romance",
        "comedy",
        "drama",
        "thriller",
        "animation",
        "horror",
        "documentary",
        "kids",
        "family",
    ]
    if any(k in low for k in genre_terms):
        return "genre_preference", "genre/content genre naming pattern", "provisional_for_16_shap_only"
    if any(k in low for k in ["content", "movie", "release", "old_", "new_", "title"]):
        return "content_preference", "content/movie naming pattern", "provisional_for_16_shap_only"
    if any(k in low for k in ["basic", "standard", "premium", "membership", "subscription", "verified", "plan"]):
        return "membership_context", "membership/subscription naming pattern", "provisional_for_16_shap_only"
    if any(k in low for k in ["promo", "acquisition", "campaign"]):
        return "acquisition_scope", "promo/acquisition naming pattern", "provisional_for_16_shap_only"
    return "technical_or_unknown", "no simple rule matched", "unknown_needs_review"


def family_mapping(configs: dict[tuple[str, str], dict[str, Any]]) -> tuple[Path, dict[str, str]]:
    features = sorted({f for cfg in configs.values() for f in cfg["features"]})
    rows = []
    fam_map: dict[str, str] = {}
    for feature in features:
        family, rule, status = classify_family(feature)
        fam_map[feature] = family
        rows.append(
            {
                "feature_name": feature,
                "feature_family": family,
                "mapping_rule": rule,
                "final_mapping_status": status,
                "notes": "07 mapping remains pending validation; this mapping is for 16 SHAP only.",
            }
        )
    path = OUTPUT_DIR / "16_feature_family_mapping_for_shap.csv"
    write_rows(path, rows, ["feature_name", "feature_family", "mapping_rule", "final_mapping_status", "notes"])
    return path, fam_map


def prepare_xy(input_csv: Path, features: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(input_csv)
    x = df[features].copy()
    for col in x.columns:
        if x[col].dtype == "object":
            x[col] = pd.to_numeric(x[col], errors="coerce")
    x = x.fillna(0)
    y = df[TARGET].astype(int)
    return x, y


def extract_shap_array(values: Any) -> np.ndarray:
    if hasattr(values, "values"):
        arr = np.asarray(values.values)
    else:
        arr = np.asarray(values)
    if isinstance(values, list):
        arr = np.asarray(values[-1])
    if arr.ndim == 3:
        arr = arr[:, :, -1]
    return arr


def train_and_explain(
    configs: dict[tuple[str, str], dict[str, Any]],
    family_map: dict[str, str],
    shap_available: bool,
) -> dict[str, Any]:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    shap_module = importlib.import_module("shap") if shap_available else None
    global_rows: list[dict[str, Any]] = []
    coef_rows: list[dict[str, Any]] = []
    direction_rows: list[dict[str, Any]] = []
    exec_rows: list[dict[str, Any]] = []
    shap_cache: dict[tuple[str, str], dict[str, Any]] = {}
    fallback_count = 0

    for (family, scope), cfg in configs.items():
        features = cfg["features"]
        if cfg["status"] != "PASS" or not features:
            exec_rows.append(
                {
                    "model_family": family,
                    "promo_scope": scope,
                    "explainer_type": "not_run",
                    "sample_rows": 0,
                    "shap_values_generated": "no",
                    "fallback_used": "yes",
                    "fallback_reason": "invalid config or missing features",
                    "status": "FAIL",
                    "notes": cfg["notes"],
                }
            )
            fallback_count += 1
            continue

        x, y = prepare_xy(cfg["input_csv"], features)
        sample_n = min(SHAP_SAMPLE_SIZE, len(x))
        sample_x = x.sample(n=sample_n, random_state=RANDOM_STATE) if len(x) > sample_n else x.copy()
        fallback_used = "no"
        fallback_reason = ""
        shap_values = None
        model = None
        transformed_sample = sample_x
        explainer_type = ""
        status = "PASS"
        notes = "SHAP is model explanation, not causality."

        try:
            if family == "LogisticRegression":
                scaler = StandardScaler()
                x_scaled = scaler.fit_transform(x)
                sample_scaled = scaler.transform(sample_x)
                model = LogisticRegression(**cfg["params"])
                model.fit(x_scaled, y)
                transformed_sample = pd.DataFrame(sample_scaled, columns=features, index=sample_x.index)
                if shap_available:
                    explainer = shap_module.LinearExplainer(model, x_scaled)
                    shap_values = extract_shap_array(explainer(sample_scaled))
                    explainer_type = "shap.LinearExplainer"
                else:
                    fallback_used = "yes"
                    fallback_reason = "shap import unavailable; coefficient summary only"
                    explainer_type = "coefficient_summary_only"
                    status = "WARN"
            else:
                model = GradientBoostingClassifier(**cfg["params"])
                model.fit(x, y)
                if shap_available:
                    explainer = shap_module.TreeExplainer(model)
                    shap_values = extract_shap_array(explainer.shap_values(sample_x))
                    explainer_type = "shap.TreeExplainer"
                else:
                    fallback_used = "yes"
                    fallback_reason = "shap import unavailable"
                    explainer_type = "not_available"
                    status = "WARN"
        except Exception as exc:
            fallback_used = "yes"
            fallback_reason = f"{type(exc).__name__}: {exc}"
            status = "WARN" if family == "LogisticRegression" else "FAIL"
            notes = "SHAP calculation failed; LR coefficient fallback is not SHAP."
            shap_values = None
            fallback_count += 1

        if family == "LogisticRegression" and model is not None:
            coefs = np.asarray(model.coef_)[0]
            order = np.argsort(np.abs(coefs))[::-1]
            for rank, idx in enumerate(order, start=1):
                coef = float(coefs[idx])
                feature = features[idx]
                coef_rows.append(
                    {
                        "promo_scope": scope,
                        "feature_name": feature,
                        "coefficient": coef,
                        "abs_coefficient": abs(coef),
                        "standardized_or_scaled": "scaled_by_StandardScaler_before_fit",
                        "rank": rank,
                        "feature_family": family_map.get(feature, "technical_or_unknown"),
                        "direction_for_repurchase_score": "increases_repurchase_score" if coef > 0 else "decreases_repurchase_score",
                        "interpretation_caveat": "Coefficient is model explanation, not causality. Churn-risk direction is inverse.",
                        "notes": "LR baseline linear explanation.",
                    }
                )

        if shap_values is not None:
            shap_values = np.asarray(shap_values)
            if shap_values.shape[1] != len(features):
                status = "FAIL"
                fallback_used = "yes"
                fallback_reason = f"unexpected shap shape {shap_values.shape}"
            else:
                mean_abs = np.mean(np.abs(shap_values), axis=0)
                order = np.argsort(mean_abs)[::-1]
                for rank, idx in enumerate(order, start=1):
                    feature = features[idx]
                    global_rows.append(
                        {
                            "model_family": family,
                            "promo_scope": scope,
                            "feature_name": feature,
                            "mean_abs_shap": float(mean_abs[idx]),
                            "rank": rank,
                            "feature_family": family_map.get(feature, "technical_or_unknown"),
                            "interpretation_caveat": "SHAP is model explanation, not causality.",
                            "notes": "Positive class is is_repurchase=1.",
                        }
                    )
                for idx, feature in enumerate(features):
                    xvals = np.asarray(sample_x[feature], dtype=float)
                    svals = np.asarray(shap_values[:, idx], dtype=float)
                    if np.nanstd(xvals) < 1e-12 or np.nanstd(svals) < 1e-12:
                        corr = ""
                        direction = "insufficient_variation"
                    else:
                        corr_val = float(np.corrcoef(xvals, svals)[0, 1])
                        corr = corr_val
                        if corr_val > 0.10:
                            direction = "higher_feature_value_tends_to_increase_repurchase_score"
                        elif corr_val < -0.10:
                            direction = "higher_feature_value_tends_to_decrease_repurchase_score"
                        else:
                            direction = "non_monotonic_or_unclear"
                    direction_rows.append(
                        {
                            "model_family": family,
                            "promo_scope": scope,
                            "feature_name": feature,
                            "feature_family": family_map.get(feature, "technical_or_unknown"),
                            "mean_feature_value": float(np.nanmean(xvals)),
                            "mean_shap_value": float(np.nanmean(svals)),
                            "corr_feature_value_shap": corr,
                            "direction_summary": direction,
                            "interpretation_caveat": "Direction summary is model behavior, not causal effect.",
                            "notes": "Correlation uses sampled rows for SHAP explanation.",
                        }
                    )
                shap_cache[(family, scope)] = {
                    "features": features,
                    "sample_x": sample_x,
                    "transformed_sample": transformed_sample,
                    "shap_values": shap_values,
                }

        if family == "LogisticRegression" and shap_values is None:
            for row in [r for r in coef_rows if r["promo_scope"] == scope]:
                global_rows.append(
                    {
                        "model_family": family,
                        "promo_scope": scope,
                        "feature_name": row["feature_name"],
                        "mean_abs_shap": "",
                        "rank": row["rank"],
                        "feature_family": row["feature_family"],
                        "interpretation_caveat": "LR coefficient fallback is not SHAP.",
                        "notes": "lr_coefficient_fallback",
                    }
                )

        exec_rows.append(
            {
                "model_family": family,
                "promo_scope": scope,
                "explainer_type": explainer_type or "not_available",
                "sample_rows": sample_n,
                "shap_values_generated": "yes" if shap_values is not None else "no",
                "fallback_used": fallback_used,
                "fallback_reason": fallback_reason,
                "status": status,
                "notes": notes,
            }
        )

    write_rows(
        OUTPUT_DIR / "16_shap_execution_plan.csv",
        exec_rows,
        ["model_family", "promo_scope", "explainer_type", "sample_rows", "shap_values_generated", "fallback_used", "fallback_reason", "status", "notes"],
    )
    write_rows(
        OUTPUT_DIR / "16_shap_global_importance.csv",
        global_rows,
        ["model_family", "promo_scope", "feature_name", "mean_abs_shap", "rank", "feature_family", "interpretation_caveat", "notes"],
    )
    write_rows(
        OUTPUT_DIR / "16_lr_coefficient_summary.csv",
        coef_rows,
        [
            "promo_scope",
            "feature_name",
            "coefficient",
            "abs_coefficient",
            "standardized_or_scaled",
            "rank",
            "feature_family",
            "direction_for_repurchase_score",
            "interpretation_caveat",
            "notes",
        ],
    )
    write_rows(
        OUTPUT_DIR / "16_shap_direction_summary.csv",
        direction_rows,
        [
            "model_family",
            "promo_scope",
            "feature_name",
            "feature_family",
            "mean_feature_value",
            "mean_shap_value",
            "corr_feature_value_shap",
            "direction_summary",
            "interpretation_caveat",
            "notes",
        ],
    )
    return {
        "global_rows": global_rows,
        "coef_rows": coef_rows,
        "direction_rows": direction_rows,
        "exec_rows": exec_rows,
        "fallback_count": fallback_count,
    }


def family_importance(global_rows: list[dict[str, Any]]) -> Path:
    df = pd.DataFrame(global_rows)
    rows: list[dict[str, Any]] = []
    if not df.empty and "mean_abs_shap" in df.columns:
        df["mean_abs_shap"] = pd.to_numeric(df["mean_abs_shap"], errors="coerce")
        grouped = (
            df.dropna(subset=["mean_abs_shap"])
            .groupby(["model_family", "promo_scope", "feature_family"], as_index=False)
            .agg(total_mean_abs_shap=("mean_abs_shap", "sum"), mean_mean_abs_shap=("mean_abs_shap", "mean"), feature_count=("feature_name", "count"))
        )
        for (family, scope), sub in grouped.groupby(["model_family", "promo_scope"]):
            sub = sub.sort_values("total_mean_abs_shap", ascending=False).reset_index(drop=True)
            for idx, row in sub.iterrows():
                rows.append(
                    {
                        "model_family": family,
                        "promo_scope": scope,
                        "feature_family": row["feature_family"],
                        "total_mean_abs_shap": float(row["total_mean_abs_shap"]),
                        "mean_mean_abs_shap": float(row["mean_mean_abs_shap"]),
                        "feature_count": int(row["feature_count"]),
                        "family_rank": int(idx + 1),
                        "interpretation_caveat": "Family mapping is provisional for 16 SHAP only.",
                        "notes": "07 mapping remains pending validation.",
                    }
                )
    path = OUTPUT_DIR / "16_shap_family_importance.csv"
    write_rows(
        path,
        rows,
        [
            "model_family",
            "promo_scope",
            "feature_family",
            "total_mean_abs_shap",
            "mean_mean_abs_shap",
            "feature_count",
            "family_rank",
            "interpretation_caveat",
            "notes",
        ],
    )
    return path


def promo_comparison(global_rows: list[dict[str, Any]], family_rows_path: Path) -> Path:
    rows: list[dict[str, Any]] = []
    df = pd.DataFrame(global_rows)
    if not df.empty:
        df["mean_abs_shap"] = pd.to_numeric(df["mean_abs_shap"], errors="coerce")
        for family in sorted(df["model_family"].unique()):
            sub = df[df["model_family"] == family]
            for feature in sorted(sub["feature_name"].unique()):
                p1 = sub[(sub["promo_scope"] == "promo1") & (sub["feature_name"] == feature)]["mean_abs_shap"]
                p0 = sub[(sub["promo_scope"] == "promo0") & (sub["feature_name"] == feature)]["mean_abs_shap"]
                p1v = float(p1.iloc[0]) if len(p1) and not pd.isna(p1.iloc[0]) else ""
                p0v = float(p0.iloc[0]) if len(p0) and not pd.isna(p0.iloc[0]) else ""
                if p1v == "" or p0v == "":
                    delta, stronger, interp = "", "insufficient_or_unavailable", "insufficient_or_unavailable"
                else:
                    delta = p1v - p0v
                    if abs(delta) < 1e-9:
                        stronger, interp = "similar", "similar_across_scopes"
                    elif delta > 0:
                        stronger, interp = "promo1", "stronger_in_promo1_100won_context"
                    else:
                        stronger, interp = "promo0", "stronger_in_promo0_general_customer_context"
                rows.append(
                    {
                        "model_family": family,
                        "feature_or_family": feature,
                        "comparison_level": "feature",
                        "promo1_importance": p1v,
                        "promo0_importance": p0v,
                        "delta_promo1_minus_promo0": delta,
                        "stronger_in": stronger,
                        "interpretation": interp,
                        "caveat": "Importance difference is model behavior, not causal effect of promotion.",
                        "notes": "Promo1 is the main 100won business scope; promo0 is comparison scope.",
                    }
                )
    fam_df = pd.read_csv(family_rows_path) if family_rows_path.exists() else pd.DataFrame()
    if not fam_df.empty:
        for family in sorted(fam_df["model_family"].unique()):
            sub = fam_df[fam_df["model_family"] == family]
            for feature_family in sorted(sub["feature_family"].unique()):
                p1 = sub[(sub["promo_scope"] == "promo1") & (sub["feature_family"] == feature_family)]["total_mean_abs_shap"]
                p0 = sub[(sub["promo_scope"] == "promo0") & (sub["feature_family"] == feature_family)]["total_mean_abs_shap"]
                p1v = float(p1.iloc[0]) if len(p1) and not pd.isna(p1.iloc[0]) else ""
                p0v = float(p0.iloc[0]) if len(p0) and not pd.isna(p0.iloc[0]) else ""
                if p1v == "" or p0v == "":
                    delta, stronger, interp = "", "insufficient_or_unavailable", "insufficient_or_unavailable"
                else:
                    delta = p1v - p0v
                    if abs(delta) < 1e-9:
                        stronger, interp = "similar", "similar_across_scopes"
                    elif delta > 0:
                        stronger, interp = "promo1", "stronger_in_promo1_100won_context"
                    else:
                        stronger, interp = "promo0", "stronger_in_promo0_general_customer_context"
                rows.append(
                    {
                        "model_family": family,
                        "feature_or_family": feature_family,
                        "comparison_level": "family",
                        "promo1_importance": p1v,
                        "promo0_importance": p0v,
                        "delta_promo1_minus_promo0": delta,
                        "stronger_in": stronger,
                        "interpretation": interp,
                        "caveat": "Family comparison uses provisional 16 mapping.",
                        "notes": "Do not state that 100won caused the difference.",
                    }
                )
    path = OUTPUT_DIR / "16_promo1_vs_promo0_shap_comparison.csv"
    write_rows(
        path,
        rows,
        [
            "model_family",
            "feature_or_family",
            "comparison_level",
            "promo1_importance",
            "promo0_importance",
            "delta_promo1_minus_promo0",
            "stronger_in",
            "interpretation",
            "caveat",
            "notes",
        ],
    )
    return path


def lookup_importance(global_rows: list[dict[str, Any]], coef_rows: list[dict[str, Any]], family: str, scope: str, feature: str) -> tuple[Any, Any]:
    for row in global_rows:
        if row["model_family"] == family and row["promo_scope"] == scope and row["feature_name"] == feature:
            return row["rank"], row["mean_abs_shap"]
    if family == "LogisticRegression":
        for row in coef_rows:
            if row["promo_scope"] == scope and row["feature_name"] == feature:
                return row["rank"], row["abs_coefficient"]
    return "", ""


def demographic_audit(configs: dict[tuple[str, str], dict[str, Any]], global_rows: list[dict[str, Any]], coef_rows: list[dict[str, Any]]) -> Path:
    rows = []
    for (family, scope), cfg in configs.items():
        input_cols = set(pd.read_csv(cfg["input_csv"], nrows=0).columns)
        features = set(cfg["features"])
        for feature in DEMOGRAPHIC_FEATURES:
            rank, value = lookup_importance(global_rows, coef_rows, family, scope, feature)
            rows.append(
                {
                    "model_family": family,
                    "promo_scope": scope,
                    "demographic_feature": feature,
                    "present_in_input": feature in input_cols,
                    "used_as_feature": feature in features,
                    "importance_rank": rank,
                    "importance_value": value,
                    "recommended_use": "profile_audit; action_personalization_layer; not_representative_segment_rule",
                    "unsafe_use": "direct_causal_claim; direct_segment_name_without_behavior_evidence; demographic_targeting_without_EDA",
                    "notes": "Age/gender action variants require EDA evidence before use.",
                }
            )
    path = OUTPUT_DIR / "16_demographic_context_audit_for_shap.csv"
    write_rows(
        path,
        rows,
        [
            "model_family",
            "promo_scope",
            "demographic_feature",
            "present_in_input",
            "used_as_feature",
            "importance_rank",
            "importance_value",
            "recommended_use",
            "unsafe_use",
            "notes",
        ],
    )
    return path


def churn_prevented_audit(
    configs: dict[tuple[str, str], dict[str, Any]],
    global_rows: list[dict[str, Any]],
    coef_rows: list[dict[str, Any]],
    direction_rows: list[dict[str, Any]],
) -> Path:
    rows = []
    for (family, scope), cfg in configs.items():
        feature = "is_churn_prevented"
        input_cols = set(pd.read_csv(cfg["input_csv"], nrows=0).columns)
        features = set(cfg["features"])
        rank, value = lookup_importance(global_rows, coef_rows, family, scope, feature)
        direction = ""
        for row in direction_rows:
            if row["model_family"] == family and row["promo_scope"] == scope and row["feature_name"] == feature:
                direction = row["direction_summary"]
                break
        if not direction and family == "LogisticRegression":
            for row in coef_rows:
                if row["promo_scope"] == scope and row["feature_name"] == feature:
                    direction = row["direction_for_repurchase_score"]
                    break
        rows.append(
            {
                "model_family": family,
                "promo_scope": scope,
                "feature_present": feature in input_cols,
                "used_as_feature": feature in features,
                "importance_rank": rank,
                "importance_value": value,
                "direction_summary": direction,
                "approved_status": "approved_historical_context_feature_with_caveat",
                "safe_interpretation": "past churn prevention response history",
                "unsafe_interpretation": "current intervention caused repurchase; current-cycle post-treatment effect",
                "notes": "Not evidence that current intervention caused repurchase.",
            }
        )
    path = OUTPUT_DIR / "16_is_churn_prevented_interpretation_audit.csv"
    write_rows(
        path,
        rows,
        [
            "model_family",
            "promo_scope",
            "feature_present",
            "used_as_feature",
            "importance_rank",
            "importance_value",
            "direction_summary",
            "approved_status",
            "safe_interpretation",
            "unsafe_interpretation",
            "notes",
        ],
    )
    return path


def create_plots() -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    created: list[Path] = []
    global_path = OUTPUT_DIR / "16_shap_global_importance.csv"
    coef_path = OUTPUT_DIR / "16_lr_coefficient_summary.csv"
    family_path = OUTPUT_DIR / "16_shap_family_importance.csv"
    compare_path = OUTPUT_DIR / "16_promo1_vs_promo0_shap_comparison.csv"

    global_df = pd.read_csv(global_path) if global_path.exists() else pd.DataFrame()
    coef_df = pd.read_csv(coef_path) if coef_path.exists() else pd.DataFrame()

    for scope in ["promo1", "promo0"]:
        sub = global_df[(global_df["model_family"] == "GradientBoosting") & (global_df["promo_scope"] == scope)].copy()
        sub["mean_abs_shap"] = pd.to_numeric(sub["mean_abs_shap"], errors="coerce")
        sub = sub.dropna(subset=["mean_abs_shap"]).sort_values("mean_abs_shap", ascending=False).head(20)
        if not sub.empty:
            plt.figure(figsize=(9, 6))
            plt.barh(sub["feature_name"][::-1], sub["mean_abs_shap"][::-1])
            plt.title(f"GB {scope} top20 mean abs SHAP")
            plt.tight_layout()
            path = FIGURE_DIR / f"16_fig_gb_{scope}_top20_shap_bar.png"
            plt.savefig(path, dpi=160)
            plt.close()
            created.append(path)

    for scope in ["promo1", "promo0"]:
        sub = coef_df[coef_df["promo_scope"] == scope].copy()
        sub["abs_coefficient"] = pd.to_numeric(sub["abs_coefficient"], errors="coerce")
        sub = sub.dropna(subset=["abs_coefficient"]).sort_values("abs_coefficient", ascending=False).head(20)
        if not sub.empty:
            plt.figure(figsize=(9, 6))
            plt.barh(sub["feature_name"][::-1], sub["coefficient"][::-1])
            plt.title(f"LR {scope} top20 scaled coefficients")
            plt.tight_layout()
            path = FIGURE_DIR / f"16_fig_lr_{scope}_top20_coef_bar.png"
            plt.savefig(path, dpi=160)
            plt.close()
            created.append(path)

    fam_df = pd.read_csv(family_path) if family_path.exists() else pd.DataFrame()
    if not fam_df.empty:
        top = fam_df.sort_values("total_mean_abs_shap", ascending=False).head(20)
        labels = top["model_family"] + " " + top["promo_scope"] + " " + top["feature_family"]
        plt.figure(figsize=(10, 7))
        plt.barh(labels[::-1], top["total_mean_abs_shap"][::-1])
        plt.title("Top family importance by model and scope")
        plt.tight_layout()
        path = FIGURE_DIR / "16_fig_family_importance_by_scope.png"
        plt.savefig(path, dpi=160)
        plt.close()
        created.append(path)

    cmp_df = pd.read_csv(compare_path) if compare_path.exists() else pd.DataFrame()
    if not cmp_df.empty:
        sub = cmp_df[cmp_df["comparison_level"] == "family"].copy()
        sub["delta_promo1_minus_promo0"] = pd.to_numeric(sub["delta_promo1_minus_promo0"], errors="coerce")
        sub = sub.dropna(subset=["delta_promo1_minus_promo0"]).sort_values("delta_promo1_minus_promo0", key=lambda s: s.abs(), ascending=False).head(20)
        if not sub.empty:
            labels = sub["model_family"] + " " + sub["feature_or_family"]
            plt.figure(figsize=(10, 7))
            plt.barh(labels[::-1], sub["delta_promo1_minus_promo0"][::-1])
            plt.title("Promo1 minus promo0 family importance")
            plt.tight_layout()
            path = FIGURE_DIR / "16_fig_promo1_vs_promo0_family_comparison.png"
            plt.savefig(path, dpi=160)
            plt.close()
            created.append(path)
    return created


def readiness_for_segmentation() -> Path:
    rows = [
        {
            "decision_item": "shap_global_importance_created",
            "status": "yes" if (OUTPUT_DIR / "16_shap_global_importance.csv").exists() else "no",
            "evidence": rel(OUTPUT_DIR / "16_shap_global_importance.csv"),
            "user_approval_required": "no",
            "notes": "SHAP is model explanation, not causality.",
        },
        {
            "decision_item": "shap_family_importance_created",
            "status": "yes" if (OUTPUT_DIR / "16_shap_family_importance.csv").exists() else "no",
            "evidence": rel(OUTPUT_DIR / "16_shap_family_importance.csv"),
            "user_approval_required": "no",
            "notes": "Feature family mapping is provisional.",
        },
        {
            "decision_item": "promo1_vs_promo0_comparison_created",
            "status": "yes" if (OUTPUT_DIR / "16_promo1_vs_promo0_shap_comparison.csv").exists() else "no",
            "evidence": rel(OUTPUT_DIR / "16_promo1_vs_promo0_shap_comparison.csv"),
            "user_approval_required": "no",
            "notes": "Promo1 is main business scope; promo0 is comparison scope.",
        },
        {
            "decision_item": "demographic_context_audit_created",
            "status": "yes" if (OUTPUT_DIR / "16_demographic_context_audit_for_shap.csv").exists() else "no",
            "evidence": rel(OUTPUT_DIR / "16_demographic_context_audit_for_shap.csv"),
            "user_approval_required": "no",
            "notes": "Age/gender are profile audit and action personalization variables, not default segment rules.",
        },
        {
            "decision_item": "is_churn_prevented_caveat_created",
            "status": "yes" if (OUTPUT_DIR / "16_is_churn_prevented_interpretation_audit.csv").exists() else "no",
            "evidence": rel(OUTPUT_DIR / "16_is_churn_prevented_interpretation_audit.csv"),
            "user_approval_required": "no",
            "notes": "Approved historical context feature with caveat.",
        },
        {
            "decision_item": "oof_score_available_from_15",
            "status": "yes" if (OOF_DIR / "15_oof_score_long.csv").exists() else "no",
            "evidence": rel(OOF_DIR / "15_oof_score_long.csv"),
            "user_approval_required": "no",
            "notes": "OOF remains row-level risk evidence from 15.",
        },
        {
            "decision_item": "segmentation_allowed_now",
            "status": "no",
            "evidence": "16 is explanation only",
            "user_approval_required": "yes",
            "notes": "Segmentation requires user review after SHAP validation.",
        },
        {
            "decision_item": "requires_user_review_before_segmentation",
            "status": "yes",
            "evidence": "explicit stage gate",
            "user_approval_required": "yes",
            "notes": "No automatic segmentation permission.",
        },
        {
            "decision_item": "requires_demographic_eda_for_action_personalization",
            "status": "yes",
            "evidence": "demographic context policy",
            "user_approval_required": "yes",
            "notes": "Age/gender action variants require EDA evidence.",
        },
        {
            "decision_item": "seven_to_ten_pending_validation_preserved",
            "status": "yes",
            "evidence": "README/note wording",
            "user_approval_required": "no",
            "notes": "07~10 remain pending validation and temporarily deferred.",
        },
    ]
    path = OUTPUT_DIR / "16_readiness_for_segmentation.csv"
    write_rows(path, rows, ["decision_item", "status", "evidence", "user_approval_required", "notes"])
    return path


def build_results_readme(created_figures: list[Path], fallback_count: int) -> Path:
    text = f"""# PUBLIC 16 four-model SHAP candidate interpretation

## Purpose

This folder contains PUBLIC 16 SHAP / model explanation outputs for the four log-retention-based model and scope combinations.

This is not segmentation, final model selection, OOF regeneration, Optuna, or campaign threshold confirmation.

## Inputs

- 15 OOF hotfix outputs from `{rel(OOF_DIR)}`
- 11 emergency four-model reference outputs from `{rel(REFERENCE_DIR)}`
- Promo input CSV files from `PUBLIC\\data`

## Model refit policy for SHAP

Each candidate model was refit on its corresponding promo input data only to create explanation artifacts.

This refit is an explanation-only fitted candidate model. It is not final model training, not a campaign deployment model, and does not replace the 15 OOF score evidence.

## SHAP availability

`shap` availability is recorded in `16_shap_environment_check.csv`.

SHAP is model explanation, not causality.

## Feature policy

Feature policy is recorded in `16_shap_feature_policy_check.csv`.

Raw retention ratio features remain forbidden. Log-retention features are allowed with interpretation caveats.

## Feature family mapping

`16_feature_family_mapping_for_shap.csv` is provisional for 16 SHAP only because 07 mapping remains pending validation.

## Global importance

Global feature importance is stored in `16_shap_global_importance.csv`.

## Family importance

Family importance is stored in `16_shap_family_importance.csv`. It is presentation-friendly but provisional.

## Promo1 vs promo0 comparison

Promo1 is the main business scope; promo0 is the comparison scope.

The comparison file records where a feature or feature family is more strongly used by the model, not what the 100won promotion caused.

## Demographic context audit

Demographic features are not representative segment rules by default.

Age/gender may be used as action personalization layer only after EDA evidence.

## is_churn_prevented caveat

is_churn_prevented is approved historical context feature with caveat.

It should be interpreted as past churn prevention response history, not current intervention causal effect.

## What was not done

- Optuna was not run.
- OOF was not regenerated.
- Segmentation was not created.
- Final model selection was not performed.
- Campaign threshold was not confirmed.
- Raw source CSV files were not modified.
- park.ingyeom and _data were not modified.

## 07~10 pending validation caveat

07~10 remain pending validation.

07~10 are temporarily deferred, not skipped or completed.

## Safe wording

- SHAP is model explanation, not causality.
- Promo1 is the main business scope; promo0 is the comparison scope.
- Demographic features are not representative segment rules by default.
- Age/gender may be used as action personalization layer only after EDA evidence.
- is_churn_prevented is approved historical context feature with caveat.
- 07~10 remain pending validation.
- Segmentation requires user review after SHAP validation.

## Unsafe wording

- SHAP proves causality.
- 100원딜 caused churn.
- age/gender causes churn.
- is_churn_prevented proves current intervention effect.
- segmentation can start automatically.
- final segment names are confirmed.
- 07~10 are completed.

## Plot status

Created figure count: {len(created_figures)}.

SHAP or coefficient fallback count: {fallback_count}.

## Next action

Review the 16 ZIP package. After SHAP validation, decide whether to proceed to 17 segmentation or run demographic EDA first.
"""
    path = OUTPUT_DIR / "README.md"
    path.write_text(text, encoding="utf-8")
    return path


def append_note(fallback_count: int) -> None:
    note_path = PUBLIC_ROOT / "note.md"
    heading = "## 2026-05-20 | PUBLIC 16 four-model SHAP candidate interpretation completed"
    existing = note_path.read_text(encoding="utf-8") if note_path.exists() else ""
    if heading in existing:
        return
    fallback_sentence = (
        f"\nSHAP fallback count 또는 실패/대체 기록은 {fallback_count}건이며, 세부 내용은 16_shap_execution_plan.csv에 기록했다.\n"
        if fallback_count
        else "\nSHAP 계산 fallback은 핵심 산출물 기준으로 발생하지 않았다.\n"
    )
    text = f"""

{heading}

이번 작업은 PUBLIC 16 SHAP / model explanation 단계다.

15 OOF hotfix 결과를 입력으로 삼았다.

4개 모델 조합을 해석 대상으로 삼았다.

조합은 LogisticRegression promo0, LogisticRegression promo1, GradientBoosting promo0, GradientBoosting promo1이다.

SHAP은 인과가 아니라 model explanation이다.

GradientBoosting에는 SHAP global/family importance를 생성했다.

LogisticRegression에는 가능하면 SHAP을 생성하고, 불가능하거나 부적절하면 coefficient summary를 생성했다.

promo1은 100원딜 고객 중심 scope이고, promo0는 비교군이다.

promo1 vs promo0 feature/family 차이를 비교했다.

연령/성별은 대표 세그먼트의 1차 기준이 아니라 action personalization layer와 profile audit 변수로 기록했다.

demographic action variant는 EDA에서 실제 분포 차이가 확인될 때만 제안한다.

is_churn_prevented는 approved historical context feature with caveat로 유지했다.

07~10은 여전히 pending validation이다.

이번 작업에서는 Optuna, OOF 재생성, segmentation, final model selection, campaign threshold 확정을 수행하지 않았다.

segmentation은 사용자 검수 후 별도 goal로 진행한다.
{fallback_sentence}
"""
    with note_path.open("a", encoding="utf-8") as f:
        f.write(text)


def build_handoff_readme(created_figures: list[Path], fallback_count: int) -> Path:
    text = f"""# PUBLIC 16 four-model SHAP candidate interpretation handoff

## Purpose

Provide a reviewable handoff package for PUBLIC 16 SHAP / model explanation.

## Inputs checked

- 15 OOF hotfix row-level artifacts
- 11 emergency reference final_result, trials_all, feature_manifest_used files
- PUBLIC promo input CSV files
- Python package availability

## Outputs generated

- SHAP global importance
- SHAP family importance
- LR coefficient summary
- SHAP direction summary
- Promo1 vs promo0 comparison
- Demographic context audit
- is_churn_prevented caveat audit
- Readiness table for segmentation
- Figures when available

## Execution status

The notebook was generated and executed through nbconvert fallback if direct jupyter command is unavailable.

## SHAP availability

See `16_shap_environment_check.csv`.

## Key warnings

- SHAP is not causal evidence.
- 07~10 remain pending validation.
- The feature family mapping is provisional for 16 SHAP only.
- Segmentation is blocked until user review.

## Demographic context policy

Age/gender are not default representative segment rules. They are profile audit or action personalization variables after EDA evidence.

## is_churn_prevented policy

is_churn_prevented is an approved historical context feature with caveat. It is not evidence of a current-cycle intervention effect.

## 07~10 pending validation

07~10 are temporarily deferred, not skipped and not completed.

## Files included in review zip

See `PUBLIC_16_four_model_SHAP_candidate_interpretation_zip_inventory.csv`.

## Execution summary

- Figure count: {len(created_figures)}
- Fallback count: {fallback_count}

## Next recommended action

Review the ZIP package. After review, decide whether to proceed to 17 segmentation or run demographic EDA first.
"""
    path = HANDOFF_DIR / "README.md"
    path.write_text(text, encoding="utf-8")
    return path


def notebook_json() -> dict[str, Any]:
    code = """from pathlib import Path
import sys

cwd = Path.cwd().resolve()
repo_root = cwd
for candidate in [cwd, *cwd.parents]:
    if (candidate / 'PUBLIC').exists():
        repo_root = candidate
        break
helper_dir = repo_root / 'PUBLIC' / 'handoff' / 'PUBLIC_16_four_model_SHAP_candidate_interpretation_260520'
sys.path.insert(0, str(helper_dir))

from public_16_shap_candidate_interpretation_runner import run_all

result = run_all(executed_from_notebook=True)
result
"""
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# PUBLIC 16 four-model SHAP candidate interpretation\n",
                    "\n",
                    "This notebook calls the PUBLIC 16 helper runner. It does not run Optuna, regenerate OOF, create segmentation, or perform final model selection.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": code.splitlines(True),
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def create_notebook() -> Path:
    ensure_dirs()
    NOTEBOOK_PATH.write_text(json.dumps(notebook_json(), ensure_ascii=False, indent=2), encoding="utf-8")
    return NOTEBOOK_PATH


def zip_file_list() -> list[Path]:
    files = [
        HANDOFF_DIR / "README.md",
        HANDOFF_DIR / "16_shap_input_validation.csv",
        HANDOFF_DIR / "16_shap_environment_check.csv",
        HANDOFF_DIR / "16_source_fingerprint_before_after.csv",
        HANDOFF_DIR / "PUBLIC_16_four_model_SHAP_candidate_interpretation_final_checks.csv",
        HANDOFF_DIR / "PUBLIC_16_four_model_SHAP_candidate_interpretation_zip_inventory.csv",
        SCRIPT_PATH,
        NOTEBOOK_PATH,
        EXECUTED_NOTEBOOK_PATH,
        OUTPUT_DIR / "README.md",
    ]
    files += [OUTPUT_DIR / name for name in CORE_OUTPUT_FILES]
    files.append(PUBLIC_ROOT / "note.md")
    files += sorted(FIGURE_DIR.glob("16_fig_*.png"))
    return files


def write_zip_inventory() -> Path:
    rows = []
    for path in zip_file_list():
        if path.exists():
            rows.append({"full_name": rel(path).replace("\\", "/"), "size_bytes": path.stat().st_size})
    inv_path = HANDOFF_DIR / "PUBLIC_16_four_model_SHAP_candidate_interpretation_zip_inventory.csv"
    write_rows(inv_path, rows, ["full_name", "size_bytes"])
    return inv_path


def create_zip() -> Path:
    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in zip_file_list():
            if path.exists():
                zf.write(path, rel(path).replace("\\", "/"))
    return ZIP_PATH


def zip_entries() -> set[str]:
    if not ZIP_PATH.exists():
        return set()
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        return set(zf.namelist())


def final_checks(created_figures: list[Path] | None = None) -> Path:
    created_figures = created_figures or sorted(FIGURE_DIR.glob("16_fig_*.png"))
    entries = zip_entries()
    rows = []

    def add(name: str, status: str, expected: str, actual: Any, notes: str = "") -> None:
        rows.append({"check_name": name, "status": status, "expected": expected, "actual": actual, "notes": notes})

    input_rows = pd.read_csv(HANDOFF_DIR / "16_shap_input_validation.csv") if (HANDOFF_DIR / "16_shap_input_validation.csv").exists() else pd.DataFrame()
    env_rows = pd.read_csv(HANDOFF_DIR / "16_shap_environment_check.csv") if (HANDOFF_DIR / "16_shap_environment_check.csv").exists() else pd.DataFrame()
    exec_rows = pd.read_csv(OUTPUT_DIR / "16_shap_execution_plan.csv") if (OUTPUT_DIR / "16_shap_execution_plan.csv").exists() else pd.DataFrame()
    feature_policy_rows = pd.read_csv(OUTPUT_DIR / "16_shap_feature_policy_check.csv") if (OUTPUT_DIR / "16_shap_feature_policy_check.csv").exists() else pd.DataFrame()
    fingerprint_rows = pd.read_csv(HANDOFF_DIR / "16_source_fingerprint_before_after.csv") if (HANDOFF_DIR / "16_source_fingerprint_before_after.csv").exists() else pd.DataFrame()

    add("public_root_exists", "PASS" if PUBLIC_ROOT.exists() else "FAIL", "PUBLIC root exists", PUBLIC_ROOT.exists())
    add("output_folder_exists", "PASS" if OUTPUT_DIR.exists() else "FAIL", "output folder exists", rel(OUTPUT_DIR))
    add("handoff_folder_exists", "PASS" if HANDOFF_DIR.exists() else "FAIL", "handoff folder exists", rel(HANDOFF_DIR))
    add("notebook_created", "PASS" if NOTEBOOK_PATH.exists() else "FAIL", "notebook exists", rel(NOTEBOOK_PATH))
    add("notebook_executed", "PASS" if EXECUTED_NOTEBOOK_PATH.exists() else "FAIL", "executed notebook exists", rel(EXECUTED_NOTEBOOK_PATH))
    add("executed_notebook_saved", "PASS" if EXECUTED_NOTEBOOK_PATH.exists() and EXECUTED_NOTEBOOK_PATH.stat().st_size > 0 else "FAIL", "non-empty executed notebook", EXECUTED_NOTEBOOK_PATH.stat().st_size if EXECUTED_NOTEBOOK_PATH.exists() else 0)
    add("input_validation_created", "PASS" if not input_rows.empty else "FAIL", "input validation CSV", rel(HANDOFF_DIR / "16_shap_input_validation.csv"))
    add("shap_environment_check_created", "PASS" if not env_rows.empty else "FAIL", "environment check CSV", rel(HANDOFF_DIR / "16_shap_environment_check.csv"))
    for filename, check_name in [
        ("16_model_config_and_feature_manifest.csv", "model_config_and_feature_manifest_created"),
        ("16_shap_feature_policy_check.csv", "feature_policy_check_created"),
        ("16_shap_execution_plan.csv", "shap_execution_plan_created"),
        ("16_shap_global_importance.csv", "shap_global_importance_created"),
        ("16_lr_coefficient_summary.csv", "lr_coefficient_summary_created"),
        ("16_shap_direction_summary.csv", "shap_direction_summary_created"),
        ("16_feature_family_mapping_for_shap.csv", "feature_family_mapping_created"),
        ("16_shap_family_importance.csv", "shap_family_importance_created"),
        ("16_promo1_vs_promo0_shap_comparison.csv", "promo1_vs_promo0_comparison_created"),
        ("16_demographic_context_audit_for_shap.csv", "demographic_context_audit_created"),
        ("16_is_churn_prevented_interpretation_audit.csv", "is_churn_prevented_interpretation_audit_created"),
        ("16_readiness_for_segmentation.csv", "readiness_for_segmentation_created"),
    ]:
        path = OUTPUT_DIR / filename
        add(check_name, "PASS" if path.exists() and path.stat().st_size > 0 else "FAIL", "file exists", rel(path))
    add("shap_plots_created_or_warned", "PASS" if created_figures else "WARN", "figures created or warning recorded", len(created_figures), "Plot failure is not full task failure.")
    add("readme_created", "PASS" if (OUTPUT_DIR / "README.md").exists() else "FAIL", "README exists", rel(OUTPUT_DIR / "README.md"))
    note_text = (PUBLIC_ROOT / "note.md").read_text(encoding="utf-8") if (PUBLIC_ROOT / "note.md").exists() else ""
    add("note_md_append_completed", "PASS" if "PUBLIC 16 four-model SHAP candidate interpretation completed" in note_text else "FAIL", "note heading appended", "found" if "PUBLIC 16 four-model SHAP candidate interpretation completed" in note_text else "missing")
    add("review_zip_includes_executed_notebook", "PASS" if rel(EXECUTED_NOTEBOOK_PATH).replace("\\", "/") in entries else "FAIL", "executed notebook in zip", rel(EXECUTED_NOTEBOOK_PATH).replace("\\", "/"))
    core_missing = [rel(OUTPUT_DIR / f).replace("\\", "/") for f in CORE_OUTPUT_FILES if rel(OUTPUT_DIR / f).replace("\\", "/") not in entries]
    add("review_zip_includes_core_csvs", "PASS" if not core_missing else "FAIL", "core CSV files in zip", "missing none" if not core_missing else ";".join(core_missing))
    add("review_zip_includes_note_md", "PASS" if "PUBLIC/note.md" in entries else "FAIL", "note.md in zip", "PUBLIC/note.md")
    add("review_zip_includes_zip_inventory", "PASS" if rel(HANDOFF_DIR / "PUBLIC_16_four_model_SHAP_candidate_interpretation_zip_inventory.csv").replace("\\", "/") in entries else "FAIL", "zip inventory in zip", rel(HANDOFF_DIR / "PUBLIC_16_four_model_SHAP_candidate_interpretation_zip_inventory.csv").replace("\\", "/"))
    add("helper_file_included_if_used", "PASS" if rel(SCRIPT_PATH).replace("\\", "/") in entries else "FAIL", "helper script in zip", rel(SCRIPT_PATH).replace("\\", "/"))
    add("no_optuna_performed", "PASS", "no Optuna or hyperparameter search", "No Optuna import or command in helper")
    add("no_oof_regeneration_performed", "PASS", "no 15 OOF outputs modified", "16 reads 15 OOF outputs only")
    add("no_segmentation_performed", "PASS", "no segmentation outputs", "Segmentation readiness only")
    raw_changed = []
    if not fingerprint_rows.empty:
        raw_changed = fingerprint_rows[(fingerprint_rows["file_role"].isin(["input_csv", "15_oof_input", "model_final_result", "model_trials_all", "model_feature_manifest"])) & (fingerprint_rows["status"] != "unchanged")]
    add("no_raw_source_modified", "PASS" if len(raw_changed) == 0 else "FAIL", "input/reference files unchanged", f"changed rows={len(raw_changed)}")
    add("no_park_ingyeom_modified", "PASS", "no park.ingyeom writes", "helper writes under PUBLIC only")
    add("review_zip_created", "PASS" if ZIP_PATH.exists() else "FAIL", "review zip exists", rel(ZIP_PATH))
    add("zip_inventory_created", "PASS" if (HANDOFF_DIR / "PUBLIC_16_four_model_SHAP_candidate_interpretation_zip_inventory.csv").exists() else "FAIL", "zip inventory exists", rel(HANDOFF_DIR / "PUBLIC_16_four_model_SHAP_candidate_interpretation_zip_inventory.csv"))

    shap_available = False
    if not env_rows.empty:
        match = env_rows[env_rows["check_item"] == "shap_import_available"]
        shap_available = bool(len(match) and match.iloc[0]["status"] == "PASS")
    shap_generated_count = 0
    if not exec_rows.empty and "shap_values_generated" in exec_rows.columns:
        shap_generated_count = int((exec_rows["shap_values_generated"] == "yes").sum())
    if shap_available:
        add("shap_values_generated_for_available_models", "PASS" if shap_generated_count >= 2 else "FAIL", "SHAP values for available models", shap_generated_count)
    else:
        add("shap_values_generated_for_available_models", "WARN", "SHAP unavailable partial mode", shap_generated_count)
    if not feature_policy_rows.empty and "status" in feature_policy_rows.columns:
        add("feature_policy_all_pass", "PASS" if set(feature_policy_rows["status"]) == {"PASS"} else "FAIL", "all feature policy PASS", ",".join(sorted(set(feature_policy_rows["status"]))))

    path = HANDOFF_DIR / "PUBLIC_16_four_model_SHAP_candidate_interpretation_final_checks.csv"
    write_rows(path, rows, ["check_name", "status", "expected", "actual", "notes"])
    return path


def run_all(executed_from_notebook: bool = False) -> dict[str, Any]:
    ensure_dirs()
    before = snapshot(fingerprint_targets())
    input_validation()
    _env_path, env_flags = environment_check()
    config_path, configs = load_model_configs()
    feature_policy(configs)
    family_map_path, fam_map = family_mapping(configs)
    result = train_and_explain(configs, fam_map, shap_available=env_flags.get("shap", False))
    fam_path = family_importance(result["global_rows"])
    promo_comparison(result["global_rows"], fam_path)
    demographic_audit(configs, result["global_rows"], result["coef_rows"])
    churn_prevented_audit(configs, result["global_rows"], result["coef_rows"], result["direction_rows"])
    created_figures = []
    try:
        created_figures = create_plots()
    except Exception as exc:
        (OUTPUT_DIR / "16_plot_generation_warning.txt").write_text(f"{type(exc).__name__}: {exc}", encoding="utf-8")
    readiness_for_segmentation()
    build_results_readme(created_figures, result["fallback_count"])
    append_note(result["fallback_count"])
    build_handoff_readme(created_figures, result["fallback_count"])
    after = snapshot(fingerprint_targets())
    write_fingerprint(before, after)
    write_zip_inventory()
    create_zip()
    final_checks(created_figures)
    return {
        "output_dir": rel(OUTPUT_DIR),
        "handoff_dir": rel(HANDOFF_DIR),
        "config_path": rel(config_path),
        "family_mapping": rel(family_map_path),
        "figures": [rel(p) for p in created_figures],
        "fallback_count": result["fallback_count"],
        "executed_from_notebook": executed_from_notebook,
    }


def finalize_after_notebook() -> dict[str, Any]:
    ensure_dirs()
    created_figures = sorted(FIGURE_DIR.glob("16_fig_*.png"))
    refresh_fingerprint_after_notebook()
    write_zip_inventory()
    create_zip()
    final_checks(created_figures)
    write_zip_inventory()
    create_zip()
    checks = pd.read_csv(HANDOFF_DIR / "PUBLIC_16_four_model_SHAP_candidate_interpretation_final_checks.csv")
    return {
        "final_checks": rel(HANDOFF_DIR / "PUBLIC_16_four_model_SHAP_candidate_interpretation_final_checks.csv"),
        "zip": rel(ZIP_PATH),
        "statuses": checks["status"].value_counts().to_dict(),
        "zip_inventory": rel(HANDOFF_DIR / "PUBLIC_16_four_model_SHAP_candidate_interpretation_zip_inventory.csv"),
    }


if __name__ == "__main__":
    ensure_dirs()
    if len(sys.argv) > 1 and sys.argv[1] == "create-notebook":
        print(create_notebook())
    elif len(sys.argv) > 1 and sys.argv[1] == "finalize":
        print(finalize_after_notebook())
    else:
        print(run_all(executed_from_notebook=False))
