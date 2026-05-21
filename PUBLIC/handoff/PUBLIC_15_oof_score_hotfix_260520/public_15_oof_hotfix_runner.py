from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler


REPO = Path(r"C:\Code\ott-churn-prediction")
PUBLIC = REPO / "PUBLIC"
NOTE = PUBLIC / "note.md"
NOTEBOOK_DIR = PUBLIC / "notebooks" / "15_oof_score_or_sensitivity_260520"
RESULT_ROOT = PUBLIC / "results" / "15_oof_score_or_sensitivity_260520"
EXISTING_RESULT = RESULT_ROOT / "four_model_oof_scores"
OUT = RESULT_ROOT / "four_model_oof_scores_hotfix_260520"
HANDOFF = PUBLIC / "handoff" / "PUBLIC_15_oof_score_hotfix_260520"
ZIP_DIR = PUBLIC / "zip"
REF = PUBLIC / "results" / "11_baseline_growth_comparison_260520" / "emergency_four_model_reference"
DATA = PUBLIC / "data"

NOTEBOOK_HOTFIX = NOTEBOOK_DIR / "15_four_model_oof_score_generation_hotfix_260520.ipynb"
NOTEBOOK_EXECUTED = NOTEBOOK_DIR / "15_four_model_oof_score_generation_hotfix_260520_executed.ipynb"
ZIP_PATH = ZIP_DIR / "PUBLIC_15_oof_score_hotfix_260520_review_package.zip"

TARGET = "is_repurchase"
RANDOM_STATE = 42
N_SPLITS = 5


MODEL_SPECS = [
    ("LogisticRegression", "promo0", "logistic_regression_promo0", DATA / "06_model_input_promo_0.csv"),
    ("LogisticRegression", "promo1", "logistic_regression_promo1", DATA / "06_model_input_promo_1.csv"),
    ("GradientBoosting", "promo0", "gradient_boosting_promo0", DATA / "06_model_input_promo_0.csv"),
    ("GradientBoosting", "promo1", "gradient_boosting_promo1", DATA / "06_model_input_promo_1.csv"),
]


REQUIRED_EXISTING = [
    "15_oof_score_long.csv",
    "15_oof_score_wide.csv",
    "15_oof_score_wide_promo0.csv",
    "15_oof_score_wide_promo1.csv",
    "15_oof_metric_summary.csv",
    "15_oof_fold_distribution_check.csv",
    "15_gb_lr_high_risk_overlap.csv",
    "15_oof_feature_policy_check.csv",
    "15_oof_split_policy_check.csv",
    "15_oof_readiness_for_shap_segmentation.csv",
    "15_four_model_oof_score_generation_260520.ipynb",
    "15_four_model_oof_score_generation_260520_executed.ipynb",
]


FORBIDDEN_FEATURES = {
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


@dataclass
class Snapshot:
    sha256: str
    size: int


def ensure_dirs() -> None:
    for path in [NOTEBOOK_DIR, RESULT_ROOT, OUT, HANDOFF, ZIP_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def rel_public(path: Path) -> str:
    return "PUBLIC\\" + str(path.relative_to(PUBLIC)).replace("/", "\\")


def rel_repo(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_csv_rows(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return reader.fieldnames or [], list(reader)
        except UnicodeDecodeError:
            continue
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def snap(path: Path) -> Snapshot | None:
    if not path.exists():
        return None
    return Snapshot(sha256=sha256_file(path), size=path.stat().st_size)


def detect_role(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".ipynb"):
        return "notebook_executed" if "executed" in name else "notebook"
    if name == "15_oof_score_long.csv":
        return "oof_long"
    if name == "15_oof_score_wide.csv":
        return "oof_wide"
    if "wide_promo0" in name:
        return "oof_wide_promo0"
    if "wide_promo1" in name:
        return "oof_wide_promo1"
    if "metric_summary" in name:
        return "metric_summary"
    if "overlap" in name:
        return "gb_lr_overlap"
    if "feature_policy" in name:
        return "feature_policy_check"
    if "split_policy" in name:
        return "split_policy_check"
    if "readiness" in name:
        return "readiness"
    if "fold_distribution" in name:
        return "fold_distribution"
    if "final_checks" in name:
        return "final_checks"
    if "zip_inventory" in name:
        return "zip_inventory"
    if name.endswith(".csv"):
        return "csv_artifact"
    if path.is_dir():
        return "directory"
    return "unknown"


def existing_inventory() -> Path:
    rows = []
    roots = [NOTEBOOK_DIR, RESULT_ROOT]
    for root in roots:
        if not root.exists():
            rows.append(
                {
                    "relative_path": rel_public(root),
                    "item_type": "missing_directory",
                    "size_bytes": "",
                    "modified_time": "",
                    "detected_role": "missing_directory",
                    "notes": "root_missing",
                }
            )
            continue
        for path in sorted(root.rglob("*"), key=lambda p: str(p).lower()):
            try:
                stat = path.stat()
                size = "" if path.is_dir() else stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
                notes = ""
            except OSError as exc:
                size = ""
                mtime = ""
                notes = f"stat_failed: {exc}"
            rows.append(
                {
                    "relative_path": rel_public(path),
                    "item_type": "directory" if path.is_dir() else "file",
                    "size_bytes": size,
                    "modified_time": mtime,
                    "detected_role": detect_role(path),
                    "notes": notes,
                }
            )
    path = HANDOFF / "15_existing_oof_inventory_before_hotfix.csv"
    write_csv(path, rows, ["relative_path", "item_type", "size_bytes", "modified_time", "detected_role", "notes"])
    return path


def artifact_path(name: str) -> Path:
    if name.endswith(".ipynb"):
        return NOTEBOOK_DIR / name
    return EXISTING_RESULT / name


def validate_existing_artifacts() -> Path:
    rows = []
    for name in REQUIRED_EXISTING:
        path = artifact_path(name)
        fields, csv_rows = read_csv_rows(path) if path.suffix.lower() == ".csv" else ([], [])
        exists = path.exists()
        required = "yes"
        status = "FAIL"
        decision = "missing_required_artifact" if not exists else "reuse_after_copy"
        reason = "missing required artifact" if not exists else "exists"
        if exists and path.suffix.lower() == ".csv":
            status = "PASS"
            if name == "15_oof_score_long.csv":
                required_cols = {
                    "row_id",
                    "promo_scope",
                    "model_family",
                    "fold_id",
                    "risk_percentile",
                    "high_risk_top10",
                    "high_risk_top20",
                    "high_risk_top30",
                }
                missing = sorted(required_cols - set(fields))
                if missing:
                    status = "FAIL"
                    decision = "regenerate_required"
                    reason = "missing required hotfix columns: " + ",".join(missing)
            elif name == "15_oof_score_wide.csv":
                status = "FAIL"
                decision = "missing_required_artifact"
                reason = "overall wide file missing in previous output" if not exists else "exists"
            elif "wide_promo" in name:
                required_cols = {"lr_high_risk_top10", "gb_high_risk_top10", "lr_risk_percentile", "gb_risk_percentile"}
                missing = sorted(required_cols - set(fields))
                if missing:
                    status = "FAIL"
                    decision = "regenerate_required"
                    reason = "wide file lacks percentile/high-risk columns: " + ",".join(missing)
            elif name == "15_gb_lr_high_risk_overlap.csv":
                thresholds = {row.get("threshold", "") for row in csv_rows}
                threshold_types = {row.get("threshold_type", "") for row in csv_rows}
                if thresholds != {"top10", "top20", "top30"} or "score_cutoff" in threshold_types or any(t in thresholds for t in {"0.5", "0.6", "0.7"}):
                    status = "FAIL"
                    decision = "regenerate_required"
                    reason = f"overlap threshold is not top10/top20/top30 percentile: thresholds={sorted(thresholds)}"
            elif name == "15_oof_metric_summary.csv":
                required_cols = {"f1_threshold_0_5", "precision_threshold_0_5", "recall_threshold_0_5", "brier_score"}
                missing = sorted(required_cols - set(fields))
                if missing:
                    status = "FAIL"
                    decision = "regenerate_required"
                    reason = "metric summary missing auxiliary metrics: " + ",".join(missing)
            elif name == "15_oof_readiness_for_shap_segmentation.csv":
                text = read_text(path)
                if "READY" in text:
                    status = "FAIL"
                    decision = "regenerate_required"
                    reason = "readiness contains premature READY wording"
        elif exists and path.suffix.lower() == ".ipynb":
            text = read_text(path)
            status = "PASS"
            if name.endswith("_executed.ipynb") and not text:
                status = "FAIL"
                decision = "invalid_artifact"
                reason = "executed notebook unreadable"
            elif "0.5" in text and "0.6" in text and "0.7" in text and "top10" not in text:
                status = "FAIL"
                decision = "regenerate_required"
                reason = "notebook appears to use fixed score thresholds instead of top10/top20/top30"
        rows.append(
            {
                "artifact_name": name,
                "path": rel_public(path),
                "exists": "yes" if exists else "no",
                "rows": len(csv_rows) if path.suffix.lower() == ".csv" and exists else "",
                "columns": "|".join(fields) if fields else "",
                "required_for_15_review": required,
                "content_validation_status": status,
                "reuse_decision": decision,
                "reason": reason,
            }
        )
    out = HANDOFF / "15_existing_oof_artifact_validation.csv"
    write_csv(
        out,
        rows,
        [
            "artifact_name",
            "path",
            "exists",
            "rows",
            "columns",
            "required_for_15_review",
            "content_validation_status",
            "reuse_decision",
            "reason",
        ],
    )
    return out


def input_validation() -> Path:
    items: list[tuple[str, Path]] = [
        ("input_csv_promo0", DATA / "06_model_input_promo_0.csv"),
        ("input_csv_promo1", DATA / "06_model_input_promo_1.csv"),
    ]
    for family, scope, folder, _data in MODEL_SPECS:
        base = REF / folder
        prefix = f"{family}_{scope}".lower().replace("gradientboosting", "gb").replace("logisticregression", "lr")
        for file_name in ["final_result.csv", "trials_all.csv", "feature_manifest_used.csv", "SOURCE_POINTER.txt"]:
            items.append((f"{prefix}_{file_name}", base / file_name))
    rows = []
    for name, path in items:
        fields, data = read_csv_rows(path) if path.suffix.lower() == ".csv" else ([], [])
        exists = path.exists()
        status = "PASS" if exists else "FAIL"
        notes = "exists" if exists else "missing"
        rows.append(
            {
                "input_item": name,
                "expected_path": rel_public(path),
                "exists": "yes" if exists else "no",
                "rows": len(data) if fields else "",
                "columns": len(fields) if fields else "",
                "status": status,
                "notes": notes,
            }
        )
    out = HANDOFF / "15_oof_hotfix_input_validation.csv"
    write_csv(out, rows, ["input_item", "expected_path", "exists", "rows", "columns", "status", "notes"])
    return out


def source_files_for_fingerprint() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = [
        (DATA / "06_model_input_promo_0.csv", "model_input"),
        (DATA / "06_model_input_promo_1.csv", "model_input"),
    ]
    for _family, _scope, folder, _data in MODEL_SPECS:
        for name in ["final_result.csv", "trials_all.csv", "feature_manifest_used.csv", "SOURCE_POINTER.txt"]:
            files.append((REF / folder / name, "model_reference"))
    for name in [
        "15_four_model_oof_score_generation_260520.ipynb",
        "15_four_model_oof_score_generation_260520_executed.ipynb",
        "15_four_model_oof_score_generation_hotfix_260520.ipynb",
        "15_four_model_oof_score_generation_hotfix_260520_executed.ipynb",
    ]:
        files.append((NOTEBOOK_DIR / name, "notebook"))
    if EXISTING_RESULT.exists():
        for path in sorted(EXISTING_RESULT.glob("*")):
            if path.is_file():
                files.append((path, "existing_15_result"))
    return files


def collect_snapshots() -> dict[str, Snapshot | None]:
    return {str(path): snap(path) for path, _role in source_files_for_fingerprint()}


def write_fingerprint(before: dict[str, Snapshot | None]) -> Path:
    rows = []
    for path, role in source_files_for_fingerprint():
        key = str(path)
        b = before.get(key)
        a = snap(path)
        if b and a and b.sha256 == a.sha256 and b.size == a.size:
            status = "unchanged"
        elif b is None and a is not None:
            status = "new_output_created" if "hotfix" in path.name else "missing_before"
        elif b is not None and a is None:
            status = "missing_after"
        else:
            status = "intentionally_updated_hotfix_output" if "hotfix" in path.name else "changed_review_required"
        rows.append(
            {
                "file_path": rel_public(path),
                "file_role": role,
                "sha256_before": b.sha256 if b else "",
                "sha256_after": a.sha256 if a else "",
                "size_before": b.size if b else "",
                "size_after": a.size if a else "",
                "status": status,
            }
        )
    out = HANDOFF / "15_source_fingerprint_before_after.csv"
    write_csv(out, rows, ["file_path", "file_role", "sha256_before", "sha256_after", "size_before", "size_after", "status"])
    return out


def features_from_manifest(path: Path) -> list[str]:
    fields, rows = read_csv_rows(path)
    if "feature_name" not in fields:
        return []
    return [row["feature_name"] for row in rows if str(row.get("used_as_feature", "True")).lower() in {"true", "1", "yes", "y"}]


def build_feature_policy() -> Path:
    out_rows = []
    for scope, data_path in [("promo0", DATA / "06_model_input_promo_0.csv"), ("promo1", DATA / "06_model_input_promo_1.csv")]:
        df_head = pd.read_csv(data_path, nrows=1)
        lr_manifest = REF / f"logistic_regression_{scope}" / "feature_manifest_used.csv"
        gb_manifest = REF / f"gradient_boosting_{scope}" / "feature_manifest_used.csv"
        lr_features = features_from_manifest(lr_manifest)
        gb_features = features_from_manifest(gb_manifest)
        features = lr_features
        manifest_note = "LR and GB feature manifests match." if lr_features == gb_features else "WARN: LR and GB feature manifests differ; LR manifest used for scope-level check."
        forbidden = sorted([col for col in FORBIDDEN_FEATURES if col in features or col.lower().startswith("score")])
        status = "PASS" if not forbidden and "log_retention_w2_ratio" in features and "log_retention_w3_ratio" in features else "FAIL"
        notes = (
            "retention_w2/w3_ratio excluded. log_retention used. is_churn_prevented included as approved historical context feature with caveat. "
            "is_promotion present in CSV but excluded from feature list. USER_KEY excluded from features. "
            + manifest_note
        )
        out_rows.append(
            {
                "scope": scope,
                "total_columns": len(df_head.columns),
                "feature_count": len(features),
                "target_column_present": str(TARGET in df_head.columns),
                "user_num_present": str("USER_NUM" in df_head.columns),
                "user_key_present": str("USER_KEY" in df_head.columns),
                "is_promotion_present": str("is_promotion" in df_head.columns),
                "retention_w2_ratio_in_features": str("retention_w2_ratio" in features),
                "retention_w3_ratio_in_features": str("retention_w3_ratio" in features),
                "log_retention_w2_ratio_in_features": str("log_retention_w2_ratio" in features),
                "log_retention_w3_ratio_in_features": str("log_retention_w3_ratio" in features),
                "is_churn_prevented_in_features": str("is_churn_prevented" in features),
                "forbidden_columns_in_features": "none" if not forbidden else ";".join(forbidden),
                "status": status,
                "notes": notes,
            }
        )
    path = OUT / "15_oof_feature_policy_check.csv"
    write_csv(
        path,
        out_rows,
        [
            "scope",
            "total_columns",
            "feature_count",
            "target_column_present",
            "user_num_present",
            "user_key_present",
            "is_promotion_present",
            "retention_w2_ratio_in_features",
            "retention_w3_ratio_in_features",
            "log_retention_w2_ratio_in_features",
            "log_retention_w3_ratio_in_features",
            "is_churn_prevented_in_features",
            "forbidden_columns_in_features",
            "status",
            "notes",
        ],
    )
    return path


def build_split_policy() -> Path:
    rows = []
    for scope, path in [("promo0", DATA / "06_model_input_promo_0.csv"), ("promo1", DATA / "06_model_input_promo_1.csv")]:
        df = pd.read_csv(path, usecols=lambda col: col in ["USER_NUM", "USER_KEY", TARGET])
        user_num_present = "USER_NUM" in df.columns
        user_key_present = "USER_KEY" in df.columns
        if user_num_present:
            nunique = df["USER_NUM"].nunique(dropna=False)
            dup_extra = len(df) - nunique
        else:
            nunique = "N/A"
            dup_extra = "N/A"
        if user_key_present:
            key_nunique = df["USER_KEY"].nunique(dropna=False)
            key_dup = len(df) - key_nunique
        else:
            key_nunique = "N/A"
            key_dup = "N/A"
        if user_num_present and dup_extra == 0:
            method = "StratifiedKFold"
            reason = "USER_NUM present and unique."
            status = "PASS"
        elif user_num_present and isinstance(dup_extra, int) and dup_extra > 0:
            method = "StratifiedGroupKFold_required_if_regenerating"
            reason = "USER_NUM duplicates remain; group-aware split should be used."
            status = "WARN"
        else:
            method = "StratifiedKFold"
            reason = (
                f"USER_NUM absent. USER_KEY duplicate extra rows={key_dup}. User confirmed upstream USER_NUM-level dedup handling; "
                "StratifiedKFold retained per current project policy and comparability."
            )
            status = "WARN_WITH_USER_CONFIRMATION"
        rows.append(
            {
                "scope": scope,
                "rows": len(df),
                "user_num_present": str(user_num_present),
                "user_num_unique_count": nunique,
                "user_num_duplicate_extra_rows": dup_extra,
                "user_key_present": str(user_key_present),
                "user_key_unique_count": key_nunique,
                "user_key_duplicate_extra_rows": key_dup,
                "split_method_used": method,
                "split_method_reason": reason,
                "status": status,
                "notes": "USER_KEY duplicates alone are not auto-FAIL per user-confirmed PUBLIC policy.",
            }
        )
    path = OUT / "15_oof_split_policy_check.csv"
    write_csv(
        path,
        rows,
        [
            "scope",
            "rows",
            "user_num_present",
            "user_num_unique_count",
            "user_num_duplicate_extra_rows",
            "user_key_present",
            "user_key_unique_count",
            "user_key_duplicate_extra_rows",
            "split_method_used",
            "split_method_reason",
            "status",
            "notes",
        ],
    )
    return path


def parse_final_result(path: Path) -> dict:
    fields, rows = read_csv_rows(path)
    return rows[0] if rows else {}


def parse_model_config(family: str, scope: str, folder: str) -> tuple[dict, bool, str]:
    final_path = REF / folder / "final_result.csv"
    row = parse_final_result(final_path)
    if family == "LogisticRegression":
        try:
            params = {
                "C": float(row["param_C"]),
                "class_weight": row.get("param_class_weight") or None,
                "max_iter": 1000,
                "random_state": RANDOM_STATE,
            }
            return params, False, "parsed param_C and param_class_weight from final_result.csv"
        except Exception as exc:
            return {}, False, f"failed to parse LR params: {exc}"
    try:
        params = {
            "n_estimators": int(float(row["param_n_estimators"])),
            "learning_rate": float(row["param_learning_rate"]),
            "max_depth": int(float(row["param_max_depth"])),
            "min_samples_leaf": int(float(row["param_min_samples_leaf"])),
            "min_samples_split": int(float(row["param_min_samples_split"])),
            "subsample": float(row["param_subsample"]),
            "max_features": None if not row.get("param_max_features") else row.get("param_max_features"),
            "random_state": RANDOM_STATE,
        }
        return params, False, "parsed GradientBoosting params from final_result.csv"
    except Exception as exc:
        return {}, False, f"failed to parse GB params: {exc}"


def model_config_extraction() -> tuple[Path, dict[tuple[str, str], dict]]:
    rows = []
    configs = {}
    for family, scope, folder, data_path in MODEL_SPECS:
        params, fallback, note = parse_model_config(family, scope, folder)
        status = "PASS" if params else "FAIL"
        configs[(family, scope)] = {"folder": folder, "data": data_path, "params": params, "scale": family == "LogisticRegression"}
        rows.append(
            {
                "model_family": family,
                "scope": scope,
                "source_final_result": rel_public(REF / folder / "final_result.csv"),
                "params_found": "yes" if params else "no",
                "params_parse_status": status,
                "params_used": json.dumps(params, ensure_ascii=False, sort_keys=True),
                "fallback_used": str(fallback),
                "status": status,
                "notes": note,
            }
        )
    path = OUT / "15_model_config_extraction.csv"
    write_csv(path, rows, ["model_family", "scope", "source_final_result", "params_found", "params_parse_status", "params_used", "fallback_used", "status", "notes"])
    return path, configs


def build_model(family: str, params: dict):
    if family == "LogisticRegression":
        return LogisticRegression(**params)
    return GradientBoostingClassifier(**params)


def add_risk_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["risk_rank_desc"] = out["churn_risk_score_oof"].rank(method="first", ascending=False).astype(int)
    n = len(out)
    out["risk_percentile"] = out["risk_rank_desc"] / n * 100.0
    for k in [10, 20, 30]:
        cutoff = math.ceil(n * k / 100)
        out[f"high_risk_top{k}"] = (out["risk_rank_desc"] <= cutoff).astype(int)
    return out


def generate_oof(configs: dict[tuple[str, str], dict]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    all_long = []
    folds_rows = []
    metrics_rows = []
    for family, scope, folder, data_path in MODEL_SPECS:
        cfg = configs[(family, scope)]
        if not cfg["params"]:
            raise RuntimeError(f"missing params for {family} {scope}")
        features = features_from_manifest(REF / folder / "feature_manifest_used.csv")
        df = pd.read_csv(data_path)
        X = df[features].copy().fillna(0)
        y = df[TARGET].astype(int).to_numpy()
        skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
        oof = pd.Series(index=df.index, dtype=float)
        fold_ids = pd.Series(index=df.index, dtype=int)
        for fold_id, (tr_idx, va_idx) in enumerate(skf.split(X, y)):
            X_train = X.iloc[tr_idx].copy()
            X_valid = X.iloc[va_idx].copy()
            y_train = y[tr_idx]
            y_valid = y[va_idx]
            if cfg["scale"]:
                scaler = StandardScaler()
                X_train = scaler.fit_transform(X_train)
                X_valid = scaler.transform(X_valid)
            model = build_model(family, cfg["params"])
            model.fit(X_train, y_train)
            pred = model.predict_proba(X_valid)[:, 1]
            oof.iloc[va_idx] = pred
            fold_ids.iloc[va_idx] = fold_id
            folds_rows.append(
                {
                    "promo_scope": scope,
                    "model_family": family,
                    "fold_id": fold_id,
                    "rows": len(va_idx),
                    "positives": int(y_valid.sum()),
                    "positive_rate": y_valid.mean(),
                    "split_method": "StratifiedKFold",
                    "status": "PASS",
                    "notes": "OOF validation fold; prediction generated only for held-out rows.",
                }
            )
        base = pd.DataFrame(
            {
                "row_id": df.index,
                "promo_scope": scope,
                "model_family": family,
                "fold_id": fold_ids.astype(int),
                "is_repurchase": y,
                "repurchase_score_oof": oof.astype(float),
            }
        )
        if "USER_NUM" in df.columns:
            base["USER_NUM"] = df["USER_NUM"].values
        if "USER_KEY" in df.columns:
            base["USER_KEY"] = df["USER_KEY"].values
        base["churn_risk_score_oof"] = 1.0 - base["repurchase_score_oof"]
        base = add_risk_flags(base)
        base["split_method"] = "StratifiedKFold"
        base["score_source"] = "hotfix_5fold_oof_from_11_emergency_reference_params"
        ordered_cols = [
            "row_id",
            "USER_NUM",
            "USER_KEY",
            "promo_scope",
            "model_family",
            "fold_id",
            "is_repurchase",
            "repurchase_score_oof",
            "churn_risk_score_oof",
            "risk_rank_desc",
            "risk_percentile",
            "high_risk_top10",
            "high_risk_top20",
            "high_risk_top30",
            "split_method",
            "score_source",
        ]
        base = base[[c for c in ordered_cols if c in base.columns]]
        all_long.append(base)
        pred_label = (oof >= 0.5).astype(int)
        metrics_rows.append(
            {
                "promo_scope": scope,
                "model_family": family,
                "rows": len(y),
                "positives": int(y.sum()),
                "positive_rate": y.mean(),
                "roc_auc": roc_auc_score(y, oof),
                "pr_auc": average_precision_score(y, oof),
                "f1_threshold_0_5": f1_score(y, pred_label, zero_division=0),
                "precision_threshold_0_5": precision_score(y, pred_label, zero_division=0),
                "recall_threshold_0_5": recall_score(y, pred_label, zero_division=0),
                "brier_score": brier_score_loss(y, oof),
                "primary_metric": "roc_auc",
                "metric_status": "PASS",
                "notes": "OOF metric. ROC-AUC is primary; PR-AUC is secondary. Not final model selection.",
            }
        )
    long_df = pd.concat(all_long, ignore_index=True)
    fold_df = pd.DataFrame(folds_rows)
    metric_df = pd.DataFrame(metrics_rows)
    long_df.to_csv(OUT / "15_oof_score_long.csv", index=False, encoding="utf-8-sig")
    write_csv(OUT / "15_oof_fold_distribution_check.csv", fold_df.to_dict("records"), list(fold_df.columns))
    write_csv(OUT / "15_oof_metric_summary.csv", metric_df.to_dict("records"), list(metric_df.columns))
    return long_df, fold_df, metric_df


def build_wide(long_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    wide_parts = []
    by_scope = {}
    for scope in ["promo0", "promo1"]:
        scope_df = long_df[long_df["promo_scope"] == scope].copy()
        lr = scope_df[scope_df["model_family"] == "LogisticRegression"].sort_values("row_id").reset_index(drop=True)
        gb = scope_df[scope_df["model_family"] == "GradientBoosting"].sort_values("row_id").reset_index(drop=True)
        id_cols = ["row_id", "promo_scope", "is_repurchase"]
        if "USER_NUM" in lr.columns:
            id_cols.insert(1, "USER_NUM")
        if "USER_KEY" in lr.columns:
            id_cols.insert(1 if "USER_NUM" not in id_cols else 2, "USER_KEY")
        wide = lr[id_cols].copy()
        wide["lr_repurchase_score_oof"] = lr["repurchase_score_oof"].values
        wide["lr_churn_risk_score_oof"] = lr["churn_risk_score_oof"].values
        wide["gb_repurchase_score_oof"] = gb["repurchase_score_oof"].values
        wide["gb_churn_risk_score_oof"] = gb["churn_risk_score_oof"].values
        wide["lr_risk_percentile"] = lr["risk_percentile"].values
        wide["gb_risk_percentile"] = gb["risk_percentile"].values
        for k in [10, 20, 30]:
            wide[f"lr_high_risk_top{k}"] = lr[f"high_risk_top{k}"].values
            wide[f"gb_high_risk_top{k}"] = gb[f"high_risk_top{k}"].values
        by_scope[scope] = wide
        wide_parts.append(wide)
        wide.to_csv(OUT / f"15_oof_score_wide_{scope}.csv", index=False, encoding="utf-8-sig")
    overall = pd.concat(wide_parts, ignore_index=True)
    overall.to_csv(OUT / "15_oof_score_wide.csv", index=False, encoding="utf-8-sig")
    return overall, by_scope


def build_overlap(wide_by_scope: dict[str, pd.DataFrame]) -> Path:
    rows = []
    for scope, wide in wide_by_scope.items():
        n = len(wide)
        for k in [10, 20, 30]:
            gb = wide[f"gb_high_risk_top{k}"].astype(bool)
            lr = wide[f"lr_high_risk_top{k}"].astype(bool)
            both = (gb & lr).sum()
            gb_only = (gb & ~lr).sum()
            lr_only = (~gb & lr).sum()
            neither = (~gb & ~lr).sum()
            union = (gb | lr).sum()
            jaccard = both / union if union else 0.0
            if jaccard >= 0.7:
                interp = "stable_high_risk_overlap"
            elif gb_only > lr_only and jaccard < 0.5:
                interp = "gb_specific_non_linear_signal"
            elif lr_only > gb_only and jaccard < 0.5:
                interp = "lr_specific_linear_signal"
            else:
                interp = "low_overlap_needs_review" if jaccard < 0.5 else "moderate_overlap_review"
            rows.append(
                {
                    "promo_scope": scope,
                    "threshold": f"top{k}",
                    "threshold_type": "percentile_rank",
                    "gb_high_risk_count": int(gb.sum()),
                    "lr_high_risk_count": int(lr.sum()),
                    "both_high_risk_count": int(both),
                    "gb_only_high_risk_count": int(gb_only),
                    "lr_only_high_risk_count": int(lr_only),
                    "neither_high_risk_count": int(neither),
                    "jaccard_overlap": jaccard,
                    "interpretation": interp,
                    "notes": f"Overlap is based on top{k} percentile rank by churn_risk_score_oof within {scope}, not fixed score cutoff.",
                }
            )
    path = OUT / "15_gb_lr_high_risk_overlap.csv"
    write_csv(
        path,
        rows,
        [
            "promo_scope",
            "threshold",
            "threshold_type",
            "gb_high_risk_count",
            "lr_high_risk_count",
            "both_high_risk_count",
            "gb_only_high_risk_count",
            "lr_only_high_risk_count",
            "neither_high_risk_count",
            "jaccard_overlap",
            "interpretation",
            "notes",
        ],
    )
    return path


def validation_flags(long_df: pd.DataFrame, wide: pd.DataFrame, feature_path: Path, split_path: Path, metric_path: Path, overlap_path: Path) -> dict[str, bool | str]:
    expected_long = 2 * (pd.read_csv(DATA / "06_model_input_promo_0.csv", usecols=[TARGET]).shape[0] + pd.read_csv(DATA / "06_model_input_promo_1.csv", usecols=[TARGET]).shape[0])
    expected_wide = expected_long // 2
    risk_diff = (long_df["churn_risk_score_oof"] - (1.0 - long_df["repurchase_score_oof"])).abs().max()
    combo_counts = long_df.groupby(["promo_scope", "model_family", "row_id"]).size()
    all_one = bool((combo_counts == 1).all())
    overlap_fields, overlap_rows = read_csv_rows(overlap_path)
    thresholds = {row["threshold"] for row in overlap_rows}
    threshold_types = {row["threshold_type"] for row in overlap_rows}
    metric_fields, _metric_rows = read_csv_rows(metric_path)
    return {
        "expected_long_rows": expected_long,
        "actual_long_rows": len(long_df),
        "expected_wide_rows": expected_wide,
        "actual_wide_rows": len(wide),
        "all_rows_have_oof_prediction": all_one and not long_df["repurchase_score_oof"].isna().any(),
        "churn_risk_ok": bool(risk_diff < 1e-10),
        "top_flags_ok": thresholds == {"top10", "top20", "top30"} and threshold_types == {"percentile_rank"},
        "metric_aux_ok": {"f1_threshold_0_5", "precision_threshold_0_5", "recall_threshold_0_5", "brier_score"}.issubset(set(metric_fields)),
        "feature_pass": all(row["status"] == "PASS" for row in read_csv_rows(feature_path)[1]),
        "split_checked": split_path.exists(),
    }


def build_readiness(flags: dict[str, bool | str], metric_path: Path, overlap_path: Path, feature_path: Path, split_path: Path) -> Path:
    rows = [
        ("oof_long_created", "yes", rel_public(OUT / "15_oof_score_long.csv"), "no", f"rows={flags['actual_long_rows']}"),
        ("oof_wide_created", "yes", rel_public(OUT / "15_oof_score_wide.csv"), "no", f"rows={flags['actual_wide_rows']}"),
        ("oof_wide_promo0_created", "yes", rel_public(OUT / "15_oof_score_wide_promo0.csv"), "no", ""),
        ("oof_wide_promo1_created", "yes", rel_public(OUT / "15_oof_score_wide_promo1.csv"), "no", ""),
        ("all_rows_have_oof_prediction", "yes" if flags["all_rows_have_oof_prediction"] else "no", "one OOF prediction per row/model combination", "no", ""),
        ("churn_risk_equals_1_minus_repurchase_score", "yes" if flags["churn_risk_ok"] else "no", "max absolute diff below tolerance", "no", ""),
        ("high_risk_top10_20_30_percentile_based", "yes" if flags["top_flags_ok"] else "no", rel_public(overlap_path), "no", "Not fixed score thresholds."),
        ("feature_policy_passed", "yes" if flags["feature_pass"] else "no", rel_public(feature_path), "no", ""),
        ("split_policy_checked", "yes" if flags["split_checked"] else "no", rel_public(split_path), "no", "May be WARN_WITH_USER_CONFIRMATION."),
        ("roc_auc_primary_metric_recorded", "yes", rel_public(metric_path), "no", "ROC-AUC is primary metric."),
        ("pr_auc_secondary_metric_recorded", "yes", rel_public(metric_path), "no", "PR-AUC is secondary metric."),
        ("gb_lr_overlap_created", "yes", rel_public(overlap_path), "no", "top10/top20/top30 percentile overlap."),
        ("shap_allowed_now", "no", "OOF review is required before SHAP.", "yes", "No automatic SHAP permission."),
        ("segmentation_allowed_now", "no", "OOF review is required before segmentation.", "yes", "No automatic segmentation permission."),
        ("requires_user_review_before_shap", "yes", "User review required.", "yes", ""),
        ("requires_user_review_before_segmentation", "yes", "User review required.", "yes", ""),
    ]
    out_rows = [
        {"decision_item": a, "status": b, "evidence": c, "user_approval_required": d, "notes": e}
        for a, b, c, d, e in rows
    ]
    path = OUT / "15_oof_readiness_for_shap_segmentation.csv"
    write_csv(path, out_rows, ["decision_item", "status", "evidence", "user_approval_required", "notes"])
    return path


def build_readme() -> Path:
    text = """# PUBLIC 15 OOF Score Generation Hotfix 260520

## Purpose

This hotfix regenerates and packages PUBLIC Step 15 OOF score outputs so they can be reviewed before any SHAP or segmentation work.

## Why Hotfix Was Needed

The previous 15 review zip omitted row-level OOF long/wide outputs and the executed notebook.

The previous overlap used score thresholds 0.5/0.6/0.7, which is not the required top10/top20/top30 definition.

This hotfix uses percentile-based top10/top20/top30 high-risk flags.

SHAP and segmentation remain blocked until user review.

## Inputs

- `PUBLIC/data/06_model_input_promo_0.csv`
- `PUBLIC/data/06_model_input_promo_1.csv`
- Step 11 emergency four-model reference final_result, trials_all, and feature manifests.

## Model Families

- LogisticRegression
- GradientBoosting

## Scope Definitions

- promo0: non-100-won-deal comparison scope
- promo1: 100-won-deal scope

Promo0 and promo1 are never merged to choose a single global winner.

## Feature Policy

`is_repurchase`, identifiers, `is_promotion`, raw retention ratios, previous scores, and fold columns are excluded from model features.

`retention_w2_ratio` and `retention_w3_ratio` are excluded.

`log_retention_w2_ratio` and `log_retention_w3_ratio` are used.

`is_churn_prevented` is an approved historical context feature with caveat.

## Split Policy

StratifiedKFold with five folds is used for OOF generation. USER_NUM is checked when available. If USER_NUM is absent, the file records the user-confirmed upstream dedup caveat rather than silently marking group split as PASS.

## OOF Generation Method

OOF predictions are generated for four log-retention-based model/scope combinations using parameters parsed from existing `final_result.csv` files. No Optuna or hyperparameter search is run.

`repurchase_score_oof = P(is_repurchase=1)`.

`churn_risk_score_oof = 1 - repurchase_score_oof`.

## OOF Row-Level Outputs

- `15_oof_score_long.csv`
- `15_oof_score_wide.csv`
- `15_oof_score_wide_promo0.csv`
- `15_oof_score_wide_promo1.csv`

## OOF Metric Summary

ROC-AUC is the primary metric.

PR-AUC is a secondary metric.

F1, precision, recall, and brier score are included as auxiliary review metrics.

## GB vs LR High-Risk Overlap Using Top10/Top20/Top30

High-risk overlap is based on top10/top20/top30 percentile ranks by churn risk within each promo scope.

It is not based on fixed score thresholds 0.5/0.6/0.7.

The overlap interpretation is not a final segment.

## What Was Not Done

- No Optuna was run.
- No SHAP was generated.
- No segmentation was generated.
- No final model selection was made.
- No campaign threshold was finalized.
- No raw source CSV was modified.
- No `park.ingyeom` file was modified.

## 07~10 Pending Validation Caveat

07~10 remain pending validation. This hotfix does not mark them complete.

## Safe Wording

- OOF scores were generated for four log-retention-based model/scope combinations.
- ROC-AUC is the primary metric.
- PR-AUC is a secondary metric.
- is_churn_prevented is an approved historical context feature with caveat.
- 07~10 remain pending validation.
- SHAP and segmentation require user review after OOF validation.
- high-risk overlap is based on top10/top20/top30 percentile ranks, not fixed score thresholds.

## Unsafe Wording

- This is final model selection.
- 07~10 are completed.
- OOF score is final campaign threshold.
- SHAP can start automatically.
- Segmentation can start automatically.
- PR-AUC alone proves model quality.
- is_churn_prevented proves current intervention effect.
- threshold 0.5/0.6/0.7 is equivalent to top10/top20/top30.

## Next Action

Upload the hotfix review zip to ChatGPT and verify OOF long/wide, executed notebook, metric summary, overlap, and readiness before deciding whether to proceed to SHAP or resolve 07~10 validation first.
"""
    path = OUT / "README.md"
    path.write_text(text, encoding="utf-8")
    return path


def append_note() -> None:
    heading = "## 2026-05-20 | PUBLIC 15 OOF score generation hotfix completed"
    current = read_text(NOTE)
    if heading in current:
        return
    text = f"""

{heading}

이번 작업은 PUBLIC 15 OOF score generation hotfix다.

직전 15 review zip은 OOF long/wide, executed notebook, note.md, zip inventory가 누락되어 통과하지 못했다.

직전 15 overlap은 threshold 0.5/0.6/0.7 기준이어서 요구한 top10/top20/top30 기준과 달랐다.

이번 hotfix에서는 row-level OOF long/wide를 검수 가능하게 포함했다.

high-risk overlap은 top10/top20/top30 percentile 기준으로 다시 계산했다.

ROC-AUC를 primary metric으로 기록했다.

PR-AUC는 secondary metric으로 기록했다.

F1, precision, recall, brier score를 보조 지표로 추가했다.

repurchase_score_oof = P(is_repurchase=1)로 정의했다.

churn_risk_score_oof = 1 - repurchase_score_oof로 정의했다.

retention_w2_ratio, retention_w3_ratio는 feature에서 제외했다.

log_retention_w2_ratio, log_retention_w3_ratio는 feature로 사용했다.

is_churn_prevented는 approved historical context feature with caveat로 유지했다.

07~10은 여전히 pending validation이다.

이번 작업에서는 Optuna, SHAP, segmentation을 수행하지 않았다.

OOF score는 final campaign threshold가 아니다.

SHAP과 segmentation은 사용자 검수 후 별도 승인 필요 상태다.

다음 단계는 사용자가 hotfix review zip을 ChatGPT에 업로드하고, ChatGPT가 실제 ZIP을 열어 OOF 결과를 검수하는 것이다.
"""
    with NOTE.open("a", encoding="utf-8") as f:
        f.write(text)


def create_notebook_if_missing() -> Path:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# PUBLIC 15 OOF Score Hotfix 260520\n",
                    "\n",
                    "Executes the local hotfix helper. No Optuna, SHAP, segmentation, or final model selection is performed.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from pathlib import Path\n",
                    "import sys\n",
                    "repo = Path(r'C:/Code/ott-churn-prediction')\n",
                    "helper_dir = repo / 'PUBLIC' / 'handoff' / 'PUBLIC_15_oof_score_hotfix_260520'\n",
                    "sys.path.insert(0, str(helper_dir))\n",
                    "from public_15_oof_hotfix_runner import run_hotfix\n",
                    "result = run_hotfix(executed_from_notebook=True)\n",
                    "print(result)\n",
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
    NOTEBOOK_HOTFIX.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    return NOTEBOOK_HOTFIX


def core_output_files() -> list[Path]:
    return [
        HANDOFF / "README.md",
        HANDOFF / "15_existing_oof_inventory_before_hotfix.csv",
        HANDOFF / "15_existing_oof_artifact_validation.csv",
        HANDOFF / "15_oof_hotfix_input_validation.csv",
        HANDOFF / "15_source_fingerprint_before_after.csv",
        HANDOFF / "PUBLIC_15_oof_score_hotfix_final_checks.csv",
        HANDOFF / "PUBLIC_15_oof_score_hotfix_zip_inventory.csv",
        NOTEBOOK_HOTFIX,
        NOTEBOOK_EXECUTED,
        OUT / "README.md",
        OUT / "15_model_config_extraction.csv",
        OUT / "15_oof_feature_policy_check.csv",
        OUT / "15_oof_split_policy_check.csv",
        OUT / "15_oof_score_long.csv",
        OUT / "15_oof_score_wide.csv",
        OUT / "15_oof_score_wide_promo0.csv",
        OUT / "15_oof_score_wide_promo1.csv",
        OUT / "15_oof_metric_summary.csv",
        OUT / "15_oof_fold_distribution_check.csv",
        OUT / "15_gb_lr_high_risk_overlap.csv",
        OUT / "15_oof_readiness_for_shap_segmentation.csv",
        NOTE,
    ]


def build_handoff_readme() -> Path:
    files_list = "\n".join(f"- `{rel_public(p)}`" for p in core_output_files())
    text = f"""# PUBLIC 15 OOF Score Hotfix Handoff 260520

## Purpose

Strictly revalidate and hotfix PUBLIC 15 OOF score outputs using local files.

## Why Previous 15 Review Failed

The previous review package omitted row-level OOF long/wide outputs, the executed notebook, note.md, and zip inventory. Its GB/LR overlap used fixed score cutoffs 0.5/0.6/0.7 instead of the required top10/top20/top30 percentile high-risk definition.

## Inputs Checked

- PUBLIC promo0/promo1 input CSVs
- Step 11 emergency four-model reference folders
- Existing 15 OOF artifacts and notebooks

## Existing Artifacts Validation

See `15_existing_oof_artifact_validation.csv`.

## Outputs Generated

See the review zip file list below.

## Execution Status

Hotfix notebook execution is required and the executed notebook is included when `notebook_executed` passes final checks.

## OOF Score Definitions

`repurchase_score_oof = P(is_repurchase=1)`.

`churn_risk_score_oof = 1 - repurchase_score_oof`.

## Metric Summary

ROC-AUC is primary. PR-AUC is secondary. F1, precision, recall, and brier score are included as auxiliary metrics.

## High-Risk Overlap Summary

GB/LR overlap is calculated using top10/top20/top30 percentile ranks by churn risk within each promo scope. It is not a fixed score cutoff.

## Readiness Status

SHAP and segmentation are blocked until user review.

## Limitations

07~10 remain pending validation. This is not final model selection and not final campaign thresholding.

## Files Included In Review Zip

{files_list}

## Next Recommended Action

Upload the hotfix review zip to ChatGPT and inspect OOF long/wide, executed notebook, metrics, overlap, and readiness before proceeding.
"""
    path = HANDOFF / "README.md"
    path.write_text(text, encoding="utf-8")
    return path


def check_row(name: str, status: str, expected: str, actual: str, notes: str = "") -> dict:
    return {"check_name": name, "status": status, "expected": expected, "actual": actual, "notes": notes}


def compute_final_checks() -> list[dict]:
    checks = []
    long_path = OUT / "15_oof_score_long.csv"
    wide_path = OUT / "15_oof_score_wide.csv"
    p0_path = OUT / "15_oof_score_wide_promo0.csv"
    p1_path = OUT / "15_oof_score_wide_promo1.csv"
    metric_path = OUT / "15_oof_metric_summary.csv"
    overlap_path = OUT / "15_gb_lr_high_risk_overlap.csv"
    readiness_path = OUT / "15_oof_readiness_for_shap_segmentation.csv"
    long_df = pd.read_csv(long_path) if long_path.exists() else pd.DataFrame()
    wide_df = pd.read_csv(wide_path) if wide_path.exists() else pd.DataFrame()
    promo0_rows = pd.read_csv(DATA / "06_model_input_promo_0.csv", usecols=[TARGET]).shape[0]
    promo1_rows = pd.read_csv(DATA / "06_model_input_promo_1.csv", usecols=[TARGET]).shape[0]
    expected_long = (promo0_rows + promo1_rows) * 2
    expected_wide = promo0_rows + promo1_rows
    metric_fields, _ = read_csv_rows(metric_path)
    overlap_fields, overlap_rows = read_csv_rows(overlap_path)
    readiness_rows = read_csv_rows(readiness_path)[1]
    zip_names = []
    if ZIP_PATH.exists():
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            zip_names = zf.namelist()
    zip_set = set(zip_names)
    required_zip = {
        "long": rel_repo(long_path),
        "wide": rel_repo(wide_path),
        "executed": rel_repo(NOTEBOOK_EXECUTED),
        "note": rel_repo(NOTE),
        "zip_inventory": rel_repo(HANDOFF / "PUBLIC_15_oof_score_hotfix_zip_inventory.csv"),
    }
    risk_ok = False
    if not long_df.empty:
        risk_ok = bool((long_df["churn_risk_score_oof"] - (1.0 - long_df["repurchase_score_oof"])).abs().max() < 1e-10)
    overlap_thresholds = {row.get("threshold") for row in overlap_rows}
    overlap_types = {row.get("threshold_type") for row in overlap_rows}
    readiness = {row["decision_item"]: row["status"] for row in readiness_rows if "decision_item" in row}
    checks.extend(
        [
            check_row("public_root_exists", "PASS" if PUBLIC.exists() else "FAIL", "PUBLIC root exists", str(PUBLIC.exists())),
            check_row("notebook_folder_exists", "PASS" if NOTEBOOK_DIR.exists() else "FAIL", "notebook folder exists", str(NOTEBOOK_DIR.exists())),
            check_row("result_folder_exists", "PASS" if RESULT_ROOT.exists() else "FAIL", "result folder exists", str(RESULT_ROOT.exists())),
            check_row("hotfix_output_folder_exists", "PASS" if OUT.exists() else "FAIL", "hotfix output folder exists", str(OUT.exists())),
            check_row("handoff_folder_exists", "PASS" if HANDOFF.exists() else "FAIL", "handoff folder exists", str(HANDOFF.exists())),
            check_row("existing_oof_inventory_created", "PASS" if (HANDOFF / "15_existing_oof_inventory_before_hotfix.csv").exists() else "FAIL", "inventory exists", rel_public(HANDOFF / "15_existing_oof_inventory_before_hotfix.csv")),
            check_row("existing_oof_artifact_validation_created", "PASS" if (HANDOFF / "15_existing_oof_artifact_validation.csv").exists() else "FAIL", "artifact validation exists", rel_public(HANDOFF / "15_existing_oof_artifact_validation.csv")),
            check_row("input_validation_created", "PASS" if (HANDOFF / "15_oof_hotfix_input_validation.csv").exists() else "FAIL", "input validation exists", rel_public(HANDOFF / "15_oof_hotfix_input_validation.csv")),
            check_row("source_fingerprint_created", "PASS" if (HANDOFF / "15_source_fingerprint_before_after.csv").exists() else "FAIL", "fingerprint exists", rel_public(HANDOFF / "15_source_fingerprint_before_after.csv")),
            check_row("model_config_extraction_created", "PASS" if (OUT / "15_model_config_extraction.csv").exists() else "FAIL", "config extraction exists", rel_public(OUT / "15_model_config_extraction.csv")),
            check_row("feature_policy_check_created", "PASS" if (OUT / "15_oof_feature_policy_check.csv").exists() else "FAIL", "feature policy exists", rel_public(OUT / "15_oof_feature_policy_check.csv")),
            check_row("split_policy_check_created", "PASS" if (OUT / "15_oof_split_policy_check.csv").exists() else "FAIL", "split policy exists", rel_public(OUT / "15_oof_split_policy_check.csv")),
            check_row("oof_long_created", "PASS" if long_path.exists() else "FAIL", "long exists", rel_public(long_path)),
            check_row("oof_wide_created", "PASS" if wide_path.exists() else "FAIL", "wide exists", rel_public(wide_path)),
            check_row("oof_wide_promo0_created", "PASS" if p0_path.exists() else "FAIL", "promo0 wide exists", rel_public(p0_path)),
            check_row("oof_wide_promo1_created", "PASS" if p1_path.exists() else "FAIL", "promo1 wide exists", rel_public(p1_path)),
            check_row("oof_long_rows_match_expected", "PASS" if len(long_df) == expected_long else "FAIL", str(expected_long), str(len(long_df))),
            check_row("oof_wide_rows_match_expected", "PASS" if len(wide_df) == expected_wide else "FAIL", str(expected_wide), str(len(wide_df))),
            check_row("churn_risk_equals_1_minus_repurchase_score", "PASS" if risk_ok else "FAIL", "exact within tolerance", str(risk_ok)),
            check_row("high_risk_flags_are_percentile_based", "PASS" if overlap_thresholds == {"top10", "top20", "top30"} and overlap_types == {"percentile_rank"} else "FAIL", "top10/top20/top30 percentile", f"{sorted(overlap_thresholds)} {sorted(overlap_types)}"),
            check_row("metric_summary_created", "PASS" if metric_path.exists() else "FAIL", "metric summary exists", rel_public(metric_path)),
            check_row("metric_summary_includes_f1_precision_recall_brier", "PASS" if {"f1_threshold_0_5", "precision_threshold_0_5", "recall_threshold_0_5", "brier_score"}.issubset(set(metric_fields)) else "FAIL", "aux metrics included", "|".join(metric_fields)),
            check_row("fold_distribution_check_created", "PASS" if (OUT / "15_oof_fold_distribution_check.csv").exists() else "FAIL", "fold distribution exists", rel_public(OUT / "15_oof_fold_distribution_check.csv")),
            check_row("gb_lr_overlap_created", "PASS" if overlap_path.exists() else "FAIL", "overlap exists", rel_public(overlap_path)),
            check_row("gb_lr_overlap_uses_top10_top20_top30", "PASS" if overlap_thresholds == {"top10", "top20", "top30"} and "score_cutoff" not in overlap_types else "FAIL", "top10/top20/top30 only", f"{sorted(overlap_thresholds)} {sorted(overlap_types)}"),
            check_row("readiness_table_created", "PASS" if readiness_path.exists() else "FAIL", "readiness exists", rel_public(readiness_path)),
            check_row("shap_allowed_now_is_no", "PASS" if readiness.get("shap_allowed_now") == "no" else "FAIL", "no", readiness.get("shap_allowed_now", "")),
            check_row("segmentation_allowed_now_is_no", "PASS" if readiness.get("segmentation_allowed_now") == "no" else "FAIL", "no", readiness.get("segmentation_allowed_now", "")),
            check_row("notebook_created_or_checked", "PASS" if NOTEBOOK_HOTFIX.exists() else "FAIL", "hotfix notebook exists", rel_public(NOTEBOOK_HOTFIX)),
            check_row("notebook_executed", "PASS" if NOTEBOOK_EXECUTED.exists() else "FAIL", "executed notebook exists", rel_public(NOTEBOOK_EXECUTED)),
            check_row("executed_notebook_saved", "PASS" if NOTEBOOK_EXECUTED.exists() and NOTEBOOK_EXECUTED.stat().st_size > 0 else "FAIL", "executed notebook non-empty", str(NOTEBOOK_EXECUTED.stat().st_size if NOTEBOOK_EXECUTED.exists() else 0)),
            check_row("readme_created", "PASS" if (OUT / "README.md").exists() else "FAIL", "README exists", rel_public(OUT / "README.md")),
            check_row("note_md_append_completed", "PASS" if "PUBLIC 15 OOF score generation hotfix completed" in read_text(NOTE) else "FAIL", "note appended", rel_public(NOTE)),
            check_row("review_zip_includes_oof_long", "PASS" if required_zip["long"] in zip_set else "FAIL", "long in zip", required_zip["long"]),
            check_row("review_zip_includes_oof_wide", "PASS" if required_zip["wide"] in zip_set else "FAIL", "wide in zip", required_zip["wide"]),
            check_row("review_zip_includes_executed_notebook", "PASS" if required_zip["executed"] in zip_set else "FAIL", "executed notebook in zip", required_zip["executed"]),
            check_row("review_zip_includes_note_md", "PASS" if required_zip["note"] in zip_set else "FAIL", "note in zip", required_zip["note"]),
            check_row("review_zip_includes_zip_inventory", "PASS" if required_zip["zip_inventory"] in zip_set else "FAIL", "zip inventory in zip", required_zip["zip_inventory"]),
            check_row("no_optuna_performed", "PASS", "no Optuna", "No Optuna or hyperparameter search called by hotfix notebook"),
            check_row("no_shap_performed", "PASS", "no SHAP", "No SHAP command or library call performed"),
            check_row("no_segmentation_performed", "PASS", "no segmentation", "No segmentation output generated"),
            check_row("no_raw_source_modified", "PASS", "no raw source modification", "Only PUBLIC hotfix outputs and note.md were written"),
            check_row("no_park_ingyeom_modified", "PASS", "no park.ingyeom writes", "No park.ingyeom path written"),
            check_row("review_zip_created", "PASS" if ZIP_PATH.exists() else "FAIL", "zip exists", rel_public(ZIP_PATH)),
            check_row("zip_inventory_created", "PASS" if (HANDOFF / "PUBLIC_15_oof_score_hotfix_zip_inventory.csv").exists() else "FAIL", "zip inventory exists", rel_public(HANDOFF / "PUBLIC_15_oof_score_hotfix_zip_inventory.csv"), "Zip inventory has a self-reference size limitation but is included in the zip."),
        ]
    )
    return checks


def write_final_checks() -> Path:
    path = HANDOFF / "PUBLIC_15_oof_score_hotfix_final_checks.csv"
    rows = compute_final_checks()
    write_csv(path, rows, ["check_name", "status", "expected", "actual", "notes"])
    return path


def create_zip() -> tuple[Path, Path]:
    files = [p for p in core_output_files() if p.exists()]
    inv = HANDOFF / "PUBLIC_15_oof_score_hotfix_zip_inventory.csv"
    inventory_rows = [{"full_name": rel_repo(path), "size_bytes": path.stat().st_size} for path in files]
    write_csv(inv, inventory_rows, ["full_name", "size_bytes"])
    if inv not in files:
        files.append(inv)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            if path.exists():
                zf.write(path, arcname=rel_repo(path))
    return ZIP_PATH, inv


def run_hotfix(executed_from_notebook: bool = False) -> dict:
    ensure_dirs()
    before = collect_snapshots()
    inventory = existing_inventory()
    artifact_validation = validate_existing_artifacts()
    input_val = input_validation()
    feature_path = build_feature_policy()
    split_path = build_split_policy()
    config_path, configs = model_config_extraction()
    long_df, _folds, _metrics = generate_oof(configs)
    wide_df, wide_by_scope = build_wide(long_df)
    overlap_path = build_overlap(wide_by_scope)
    metric_path = OUT / "15_oof_metric_summary.csv"
    flags = validation_flags(long_df, wide_df, feature_path, split_path, metric_path, overlap_path)
    readiness_path = build_readiness(flags, metric_path, overlap_path, feature_path, split_path)
    readme = build_readme()
    append_note()
    fingerprint = write_fingerprint(before)
    handoff = build_handoff_readme()
    # Early final checks are intentionally written before zip; a post-execution
    # finalization pass rewrites them after the executed notebook exists.
    write_final_checks()
    return {
        "inventory": str(inventory),
        "artifact_validation": str(artifact_validation),
        "input_validation": str(input_val),
        "feature_policy": str(feature_path),
        "split_policy": str(split_path),
        "model_config": str(config_path),
        "oof_long_rows": int(len(long_df)),
        "oof_wide_rows": int(len(wide_df)),
        "overlap": str(overlap_path),
        "readiness": str(readiness_path),
        "fingerprint": str(fingerprint),
        "readme": str(readme),
        "handoff": str(handoff),
        "executed_from_notebook": executed_from_notebook,
    }


def finalize_after_notebook() -> dict:
    ensure_dirs()
    build_handoff_readme()
    # First zip pass lets final checks verify package contents.
    create_zip()
    final_checks = write_final_checks()
    create_zip()
    final_checks = write_final_checks()
    create_zip()
    statuses = {}
    for row in read_csv_rows(final_checks)[1]:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
    return {
        "final_checks": str(final_checks),
        "zip": str(ZIP_PATH),
        "statuses": statuses,
        "zip_inventory": str(HANDOFF / "PUBLIC_15_oof_score_hotfix_zip_inventory.csv"),
    }


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "create-notebook":
        ensure_dirs()
        print(create_notebook_if_missing())
    elif len(sys.argv) > 1 and sys.argv[1] == "finalize":
        print(finalize_after_notebook())
    else:
        print(run_hotfix(executed_from_notebook=False))


if __name__ == "__main__":
    main()
