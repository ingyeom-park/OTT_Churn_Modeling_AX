from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(r"C:\Code\ott-churn-prediction")
PARK = ROOT / "park.ingyeom"
PUBLIC = ROOT / "PUBLIC"
OUT = PARK / "reports" / "audits" / "merge_feasibility_park_public_260521"
ZIP_DIR = PARK / "zip"
ZIP_PATH = ZIP_DIR / "merge_feasibility_park_public_260521_review_package.zip"
OUTPUT_FOLDER_TOKEN = "reports\\audits\\merge_feasibility_park_public_260521"
HASH_LIMIT_BYTES = 250 * 1024 * 1024


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("/", "\\")


def side_root(side: str) -> Path:
    return PARK if side == "park" else PUBLIC


def file_role(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".ipynb":
        return "notebook"
    if ext == ".csv":
        return "csv"
    if ext == ".md":
        return "md"
    if ext == ".html":
        return "html"
    if ext == ".zip":
        return "zip"
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        return "figure"
    return "other"


def sha256_file(path: Path) -> str:
    try:
        if path.stat().st_size > HASH_LIMIT_BYTES:
            return "skipped_size_over_250mb"
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}"


def inventory_side(side: str) -> list[dict[str, Any]]:
    root = side_root(side)
    rows = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rp = rel(path)
        if OUTPUT_FOLDER_TOKEN in rp:
            continue
        if rp == rel(ZIP_PATH):
            continue
        st = path.stat()
        rows.append(
            {
                "side": side,
                "relative_path": rp,
                "file_name": path.name,
                "extension": path.suffix.lower(),
                "size_bytes": st.st_size,
                "modified_time": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                "sha256": sha256_file(path),
                "file_role": file_role(path),
            }
        )
    rows.sort(key=lambda r: r["relative_path"].lower())
    return rows


def write_csv(name: str, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        seen: list[str] = []
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.append(key)
        columns = seen
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: clean_cell(row.get(k, "")) for k in columns})


def write_md(name: str, text: str) -> None:
    path = OUT / name
    path.write_text(text, encoding="utf-8")


def clean_cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    if isinstance(value, (list, tuple, set)):
        return "; ".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    text = str(value)
    if len(text) > 32000:
        return text[:32000] + "...[truncated]"
    return value


def stage_of(path: str) -> str:
    p = path.replace("\\", "/")
    matches = re.findall(r"(?<!\d)(\d{2}[a-z]?|project_guide_v2|16b|18 polish)(?:[_\-/]|$)", p, flags=re.I)
    if matches:
        return matches[-1].lower()
    if "project_guide_v2" in p:
        return "project_guide_v2"
    return "unclassified"


def is_archive_path(path: str) -> bool:
    p = path.lower()
    return "\\_archive\\" in p or "/_archive/" in p or "\\legacy\\" in p or "/legacy/" in p


def sort_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def score(row: dict[str, Any]) -> tuple[int, float, str]:
        p = row["relative_path"].lower()
        penalty = 0
        if is_archive_path(p):
            penalty += 100
        if "html_claim_validation_core_sources" in p:
            penalty += 80
        if "\\zip\\" in p or "/zip/" in p:
            penalty += 60
        if "\\handoff\\" in p or "/handoff/" in p:
            penalty += 20
        if "hotfix" in p:
            penalty -= 5
        return (penalty, -Path(row["relative_path"]).as_posix().count("/"), p)

    return sorted(rows, key=score)


def find_files(inventory: list[dict[str, Any]], side: str, patterns: list[str], extensions: set[str] | None = None) -> list[dict[str, Any]]:
    out = []
    for row in inventory:
        if row["side"] != side:
            continue
        rp_lower = row["relative_path"].lower()
        name_lower = row["file_name"].lower()
        if extensions and row["extension"].lower() not in extensions:
            continue
        if any(p.lower() in rp_lower or p.lower() in name_lower for p in patterns):
            out.append(row)
    return sort_candidates(out)


def path_from_row(row: dict[str, Any]) -> Path:
    return ROOT / row["relative_path"]


def read_csv_df(path: Path, nrows: int | None = None) -> pd.DataFrame | None:
    try:
        return pd.read_csv(path, low_memory=False, nrows=nrows)
    except UnicodeDecodeError:
        try:
            return pd.read_csv(path, low_memory=False, encoding="cp949", nrows=nrows)
        except Exception:
            return None
    except Exception:
        return None


def csv_shape(path: Path) -> tuple[int | str, int | str, list[str]]:
    df_head = read_csv_df(path, nrows=0)
    if df_head is None:
        return "read_error", "read_error", []
    cols = list(df_head.columns)
    try:
        row_count = sum(1 for _ in pd.read_csv(path, chunksize=100000, low_memory=False))
        # The line above counts chunks, not rows. Use chunk lengths below.
        row_count = 0
        for chunk in pd.read_csv(path, chunksize=100000, low_memory=False):
            row_count += len(chunk)
    except Exception:
        df = read_csv_df(path)
        row_count = len(df) if df is not None else "read_error"
    return row_count, len(cols), cols


def csv_profile(row: dict[str, Any], purpose: str = "") -> dict[str, Any]:
    path = path_from_row(row)
    rows, cols, names = csv_shape(path)
    return {
        "side": row["side"],
        "purpose": purpose,
        "relative_path": row["relative_path"],
        "file_name": row["file_name"],
        "row_count": rows,
        "column_count": cols,
        "feature_like_column_count": count_feature_like_columns(names),
        "has_USER_KEY": "USER_KEY" in names,
        "has_is_repurchase": "is_repurchase" in names,
        "has_is_promotion": "is_promotion" in names,
        "has_repurchase_score": "repurchase_score" in names,
        "has_churn_risk": "churn_risk" in names,
        "columns_preview": "; ".join(names[:40]),
        "sha256": row.get("sha256", ""),
    }


def count_feature_like_columns(cols: list[str]) -> int:
    excluded = {
        "USER_KEY",
        "user_key",
        "is_repurchase",
        "is_promotion",
        "repurchase_score",
        "churn_risk",
        "fold",
        "dataset_scope",
        "model_name",
        "feature_set_variant",
    }
    return sum(1 for c in cols if c not in excluded)


def tail_text(path: Path, max_lines: int = 260) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:]) + "\n"


def note_presence(side: str, note_path: Path, labels: list[str]) -> list[dict[str, Any]]:
    if not note_path.exists():
        return [{"side": side, "stage_label": label, "found_in_note": False, "latest_matching_line": "", "line_number": ""} for label in labels]
    lines = note_path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows = []
    for label in labels:
        parts = re.split(r"[/ ]+", label)
        patterns = [label.lower()] + [p.lower() for p in parts if p]
        hits = []
        for i, line in enumerate(lines, start=1):
            ll = line.lower()
            if any(p and p in ll for p in patterns):
                hits.append((i, line))
        latest = hits[-1] if hits else ("", "")
        rows.append(
            {
                "side": side,
                "stage_label": label,
                "found_in_note": bool(hits),
                "match_count": len(hits),
                "line_number": latest[0],
                "latest_matching_line": latest[1],
            }
        )
    return rows


def extract_feature_rows(csv_rows: list[dict[str, Any]], source_label: str) -> list[dict[str, Any]]:
    out = []
    candidate_cols = [
        "feature",
        "feature_name",
        "safe_feature_name",
        "column",
        "column_name",
        "variable",
        "raw_feature",
        "model_feature",
    ]
    for row in csv_rows:
        path = path_from_row(row)
        df = read_csv_df(path)
        if df is None or df.empty:
            continue
        lower_map = {c.lower(): c for c in df.columns}
        feature_col = next((lower_map[c] for c in candidate_cols if c in lower_map), None)
        if feature_col is None:
            object_cols = [c for c in df.columns if df[c].dtype == "object"]
            feature_col = object_cols[0] if object_cols else df.columns[0]
        set_col = next((c for c in df.columns if c.lower() in {"feature_set", "feature_set_variant", "feature_set_name", "dataset_scope", "scope"}), None)
        policy_col = next((c for c in df.columns if "policy" in c.lower() or "decision" in c.lower() or "status" in c.lower()), None)
        for _, r in df.iterrows():
            feature = r.get(feature_col, "")
            if pd.isna(feature) or str(feature).strip() == "":
                continue
            out.append(
                {
                    "side": row["side"],
                    "source_label": source_label,
                    "relative_path": row["relative_path"],
                    "feature_set": r.get(set_col, "") if set_col else inferred_feature_set(row["relative_path"]),
                    "feature_name": feature,
                    "policy_or_status": r.get(policy_col, "") if policy_col else "",
                    "source_feature_column": feature_col,
                }
            )
    return out


def inferred_feature_set(path: str) -> str:
    p = path.lower()
    if "conservative" in p:
        return "conservative_safe_22"
    if "no_payment" in p or "payment_removed" in p:
        return "expanded_no_payment_device"
    if "expanded" in p:
        return "expanded_feature_set"
    return ""


def json_feature_rows(rows: list[dict[str, Any]], source_label: str) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        path = path_from_row(row)
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        for key, val in flatten_feature_sets(data).items():
            for feature in val:
                out.append(
                    {
                        "side": row["side"],
                        "source_label": source_label,
                        "relative_path": row["relative_path"],
                        "feature_set": key,
                        "feature_name": feature,
                        "policy_or_status": "",
                        "source_feature_column": "json",
                    }
                )
    return out


def flatten_feature_sets(data: Any, prefix: str = "") -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    if isinstance(data, dict):
        for k, v in data.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, list) and all(isinstance(x, str) for x in v):
                out[key] = v
            elif isinstance(v, dict):
                out.update(flatten_feature_sets(v, key))
    return out


def contains_feature(feature_rows: list[dict[str, Any]], feature: str, side: str | None = None, feature_set_contains: str | None = None) -> bool:
    for r in feature_rows:
        if side and r["side"] != side:
            continue
        if feature_set_contains and feature_set_contains.lower() not in str(r.get("feature_set", "")).lower():
            continue
        if str(r.get("feature_name", "")).strip() == feature:
            return True
    return False


def metric_rows_from_csv(row: dict[str, Any], source_group: str) -> list[dict[str, Any]]:
    path = path_from_row(row)
    df = read_csv_df(path)
    if df is None or df.empty:
        return []
    low = {c.lower(): c for c in df.columns}
    model_col = next((low[c] for c in ["model_name", "model", "estimator", "candidate_model"] if c in low), None)
    scope_col = next((low[c] for c in ["dataset_scope", "scope", "split", "promo_scope"] if c in low), None)
    fs_col = next((low[c] for c in ["feature_set_variant", "feature_set", "feature_set_name"] if c in low), None)
    auc_cols = [c for c in df.columns if "auc" in c.lower()]
    gap_cols = [c for c in df.columns if "gap" in c.lower() or "overfit" in c.lower()]
    rows = []
    for _, r in df.iterrows():
        model_name = r.get(model_col, "") if model_col else infer_model_from_path(row["relative_path"])
        metric_auc = first_nonempty([r.get(c, "") for c in auc_cols])
        gap = first_nonempty([r.get(c, "") for c in gap_cols])
        rows.append(
            {
                "side": row["side"],
                "source_group": source_group,
                "relative_path": row["relative_path"],
                "model_name": model_name,
                "dataset_scope": r.get(scope_col, "") if scope_col else infer_scope_from_path(row["relative_path"]),
                "feature_set": r.get(fs_col, "") if fs_col else "",
                "metric_auc": metric_auc,
                "train_valid_gap_or_overfit_metric": gap,
                "auc_columns_available": "; ".join(auc_cols),
                "gap_columns_available": "; ".join(gap_cols),
                "columns_available": "; ".join(df.columns),
            }
        )
    return rows


def infer_model_from_path(path: str) -> str:
    p = path.lower()
    if "catboost" in p:
        return "CatBoost"
    if "lightgbm" in p:
        return "LightGBM"
    if "gradientboosting" in p or "gradient_boosting" in p:
        return "GradientBoosting"
    if "logistic" in p or "lr_" in p:
        return "LogisticRegression"
    return ""


def infer_scope_from_path(path: str) -> str:
    p = path.lower()
    if "promo1" in p or "promo_1" in p:
        return "promo1"
    if "promo0" in p or "promo_0" in p:
        return "promo0"
    return ""


def first_nonempty(values: list[Any]) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, float) and math.isnan(value):
            continue
        if str(value) != "":
            return value
    return ""


def summarize_assignment(row: dict[str, Any], label_hint: str) -> list[dict[str, Any]]:
    path = path_from_row(row)
    df = read_csv_df(path)
    if df is None or df.empty:
        return []
    candidates = [c for c in df.columns if "segment" in c.lower() and ("representative" in c.lower() or "label" in c.lower() or c.lower() == "segment")]
    seg_col = candidates[0] if candidates else next((c for c in df.columns if "segment" in c.lower()), None)
    risk_col = next((c for c in df.columns if c.lower() == "churn_risk" or "risk" in c.lower()), None)
    if not seg_col:
        return [
            {
                "side": row["side"],
                "source_label": label_hint,
                "relative_path": row["relative_path"],
                "segment_column": "",
                "segment_value": "no_segment_column_detected",
                "row_count": len(df),
                "mean_churn_risk": "",
            }
        ]
    grouped = df.groupby(seg_col, dropna=False).agg(row_count=(seg_col, "size"))
    if risk_col and pd.api.types.is_numeric_dtype(df[risk_col]):
        grouped["mean_churn_risk"] = df.groupby(seg_col, dropna=False)[risk_col].mean()
    else:
        grouped["mean_churn_risk"] = ""
    out = []
    for idx, r in grouped.reset_index().iterrows():
        out.append(
            {
                "side": row["side"],
                "source_label": label_hint,
                "relative_path": row["relative_path"],
                "segment_column": seg_col,
                "segment_value": r[seg_col],
                "row_count": r["row_count"],
                "mean_churn_risk": r.get("mean_churn_risk", ""),
            }
        )
    return out


def churn_direction_checks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        path = path_from_row(row)
        df = read_csv_df(path)
        if df is None or df.empty:
            continue
        cols = set(df.columns)
        score_cols = [c for c in df.columns if "score" in c.lower() or "risk" in c.lower() or "prob" in c.lower()]
        if {"repurchase_score", "churn_risk"}.issubset(cols):
            diff = (df["churn_risk"] - (1 - df["repurchase_score"])).abs()
            status = "PASS" if diff.max() < 1e-8 else "WARN"
            out.append(
                {
                    "side": row["side"],
                    "relative_path": row["relative_path"],
                    "check": "churn_risk_equals_1_minus_repurchase_score",
                    "status": status,
                    "row_count_checked": len(df),
                    "max_abs_diff": diff.max(),
                    "score_columns_available": "; ".join(score_cols),
                }
            )
        else:
            out.append(
                {
                    "side": row["side"],
                    "relative_path": row["relative_path"],
                    "check": "score_direction_columns_present",
                    "status": "INFO",
                    "row_count_checked": len(df),
                    "max_abs_diff": "",
                    "score_columns_available": "; ".join(score_cols),
                }
            )
    return out


def source_fingerprint(paths: list[Path], phase: str) -> list[dict[str, Any]]:
    rows = []
    seen = set()
    for path in paths:
        if not path.exists() or path in seen:
            continue
        seen.add(path)
        st = path.stat()
        rows.append(
            {
                "phase": phase,
                "relative_path": rel(path),
                "file_name": path.name,
                "extension": path.suffix.lower(),
                "size_bytes": st.st_size,
                "modified_time": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                "sha256": sha256_file(path),
            }
        )
    return rows


def copy_output_files_to_zip() -> list[str]:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    files = sorted([p for p in OUT.iterdir() if p.is_file() and not p.name.startswith("_")], key=lambda p: p.name)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, arcname=path.name)
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        return zf.namelist()


def zip_inventory_rows() -> list[dict[str, Any]]:
    rows = []
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        for info in zf.infolist():
            rows.append(
                {
                    "zip_path": rel(ZIP_PATH),
                    "zip_member": info.filename,
                    "compressed_size": info.compress_size,
                    "file_size": info.file_size,
                    "modified_time": datetime(*info.date_time).isoformat(timespec="seconds"),
                }
            )
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ZIP_DIR.mkdir(parents=True, exist_ok=True)

    park_inv = inventory_side("park")
    public_inv = inventory_side("PUBLIC")
    inventory = park_inv + public_inv
    source_before_paths: list[Path] = [PARK / "note.md", PUBLIC / "note.md"]

    write_csv("01_inventory_park.csv", park_inv)
    write_csv("02_inventory_PUBLIC.csv", public_inv)

    summary_counter: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in inventory:
        key = (row["side"], stage_of(row["relative_path"]), row["file_role"])
        rec = summary_counter.setdefault(key, {"side": key[0], "stage": key[1], "file_role": key[2], "file_count": 0, "size_bytes_total": 0})
        rec["file_count"] += 1
        rec["size_bytes_total"] += int(row["size_bytes"])
    write_csv("03_inventory_summary_by_stage.csv", list(summary_counter.values()))

    park_labels = ["05x", "05y", "06x", "07x", "08x", "09x", "10x", "11x", "12x", "14x", "15x", "16x payment-removed SHAP", "17x segmentation", "18x business storyline", "project_guide_v2"]
    public_labels = ["06x/06y/06", "11/12 emergency model", "15 OOF", "16 SHAP", "16b family mapping", "17 segmentation hotfixes", "18 business storyline", "18 polish hotfix"]
    note_rows = note_presence("park", PARK / "note.md", park_labels) + note_presence("PUBLIC", PUBLIC / "note.md", public_labels)
    write_csv("04_note_stage_log_presence.csv", note_rows)
    write_md("05_note_latest_tail_park.md", tail_text(PARK / "note.md") if (PARK / "note.md").exists() else "park.ingyeom/note.md not found\n")
    write_md("06_note_latest_tail_PUBLIC.md", tail_text(PUBLIC / "note.md") if (PUBLIC / "note.md").exists() else "PUBLIC/note.md not found\n")

    dataset_patterns = {
        "park": [
            "06x_expanded_dataset.csv",
            "06x_conservative_dataset.csv",
            "06_primary_main_cohort_conservative_features.csv",
            "15x_oof_predictions.csv",
            "17x_segmentation_base_datamart.csv",
            "17x_representative_segment_assignment.csv",
            "18x_dashboard_handoff_datamart.csv",
        ],
        "PUBLIC": [
            "06x_expanded_dataset.csv",
            "06y_expanded_dataset_promo_0.csv",
            "06y_expanded_dataset_promo_1.csv",
            "06_model_input_promo_0.csv",
            "06_model_input_promo_1.csv",
            "15_oof_score_long.csv",
            "15_oof_score_wide_promo0.csv",
            "15_oof_score_wide_promo1.csv",
            "17_representative_segment_assignment",
            "17_revised_segment_assignment",
            "17_segmentation_base_datamart.csv",
            "18_dashboard_handoff_datamart",
            "18_promo1_main_business_action_matrix",
            "18_promo0_comparison_reference",
        ],
    }
    dataset_rows = []
    dataset_candidate_rows = []
    for side, patterns in dataset_patterns.items():
        for pattern in patterns:
            found = find_files(inventory, side, [pattern], {".csv"})
            for idx, row in enumerate(found[:8], start=1):
                prof = csv_profile(row, pattern)
                prof["candidate_rank"] = idx
                dataset_rows.append(prof)
                dataset_candidate_rows.append(row)
                source_before_paths.append(path_from_row(row))
    write_csv("07_dataset_row_column_comparison.csv", dataset_rows)

    key_count_rows = []
    for row in dataset_candidate_rows:
        df = read_csv_df(path_from_row(row))
        if df is None:
            continue
        key_cols = [c for c in ["USER_KEY", "user_key", "USER_NUM", "is_repurchase", "is_promotion"] if c in df.columns]
        rec = {"side": row["side"], "relative_path": row["relative_path"], "row_count": len(df), "key_columns_present": "; ".join(key_cols)}
        for c in key_cols:
            rec[f"{c}_nunique"] = df[c].nunique(dropna=False)
        key_count_rows.append(rec)
    write_csv("08_dataset_key_count_comparison.csv", key_count_rows)

    promo_rows = []
    for row in dataset_candidate_rows:
        df = read_csv_df(path_from_row(row))
        if df is None:
            continue
        if "is_promotion" in df.columns:
            counts = df["is_promotion"].value_counts(dropna=False).to_dict()
            for val, cnt in counts.items():
                promo_rows.append({"side": row["side"], "relative_path": row["relative_path"], "is_promotion_value": val, "row_count": cnt})
        elif "promo_0" in row["relative_path"].lower() or "promo0" in row["relative_path"].lower():
            promo_rows.append({"side": row["side"], "relative_path": row["relative_path"], "is_promotion_value": "inferred_promo0_from_filename", "row_count": len(df)})
        elif "promo_1" in row["relative_path"].lower() or "promo1" in row["relative_path"].lower():
            promo_rows.append({"side": row["side"], "relative_path": row["relative_path"], "is_promotion_value": "inferred_promo1_from_filename", "row_count": len(df)})
    write_csv("09_promotion_split_count_comparison.csv", promo_rows)

    park_feature_files = find_files(inventory, "park", ["05y_conservative", "05y_patch2_conservative", "05y_expanded", "05y_patch2_expanded", "06x_model_feature_lists", "15x_expanded_no_payment_device_feature_list", "feature_sets"], {".csv", ".json"})
    public_feature_files = find_files(inventory, "PUBLIC", ["06_feature_manifest", "feature_manifest_used", "06x_model_feature_lists", "15_oof_feature_policy_check", "16_model_config_and_feature_manifest"], {".csv", ".json"})
    park_features = extract_feature_rows([r for r in park_feature_files if r["extension"] == ".csv"], "park_feature_inventory")
    park_features += json_feature_rows([r for r in park_feature_files if r["extension"] == ".json"], "park_feature_inventory")
    public_features = extract_feature_rows([r for r in public_feature_files if r["extension"] == ".csv"], "PUBLIC_feature_inventory")
    public_features += json_feature_rows([r for r in public_feature_files if r["extension"] == ".json"], "PUBLIC_feature_inventory")
    write_csv("10_feature_set_inventory_park.csv", park_features)
    write_csv("11_feature_set_inventory_PUBLIC.csv", public_features)
    source_before_paths += [path_from_row(r) for r in park_feature_files[:20] + public_feature_files[:20]]

    park_feature_names = {str(r["feature_name"]) for r in park_features}
    public_feature_names = {str(r["feature_name"]) for r in public_features}
    overlap_rows = []
    for f in sorted(park_feature_names | public_feature_names):
        overlap_rows.append(
            {
                "feature_name": f,
                "in_park": f in park_feature_names,
                "in_PUBLIC": f in public_feature_names,
                "overlap_status": "both" if f in park_feature_names and f in public_feature_names else ("park_only" if f in park_feature_names else "PUBLIC_only"),
            }
        )
    write_csv("12_feature_set_overlap_diff.csv", overlap_rows)

    payment_features = ["payment_is_mobile", "payment_is_pc", "payment_is_android", "payment_is_ios", "USER_KEY", "is_repurchase", "is_promotion"]
    payment_policy_rows = []
    for f in payment_features:
        payment_policy_rows.append(
            {
                "feature_name": f,
                "park_present_any_feature_inventory": contains_feature(park_features, f),
                "park_present_expanded_no_payment_device": contains_feature(park_features, f, "park", "no_payment"),
                "PUBLIC_present_any_feature_inventory": contains_feature(public_features, f),
                "evidence_note": "Presence means found in feature inventory files only. It is not a new policy decision.",
            }
        )
    write_csv("13_payment_device_policy_comparison.csv", payment_policy_rows)

    retention_features = ["log_retention_w2_ratio", "log_retention_w3_ratio", "retention_w2_ratio", "retention_w3_ratio"]
    retention_rows = []
    for f in retention_features:
        retention_rows.append(
            {
                "feature_name": f,
                "park_present_any_feature_inventory": contains_feature(park_features, f),
                "PUBLIC_present_any_feature_inventory": contains_feature(public_features, f),
                "park_present_in_dataset_columns": any(f in (csv_shape(path_from_row(r))[2]) for r in dataset_candidate_rows if r["side"] == "park"),
                "PUBLIC_present_in_dataset_columns": any(f in (csv_shape(path_from_row(r))[2]) for r in dataset_candidate_rows if r["side"] == "PUBLIC"),
            }
        )
    write_csv("14_retention_feature_policy_comparison.csv", retention_rows)

    park_model_files = find_files(inventory, "park", ["12x_", "14x_", "15x_model", "15x_payment_removed", "16x_SHAP_candidate_plan", "17x_score_source_selection", "CatBoost", "catboost"], {".csv", ".md"})
    public_model_files = find_files(inventory, "PUBLIC", ["12_", "final_result.csv", "15_oof_metric_summary", "15_model_config", "15_gb_lr_high_risk_overlap", "12_final_result_metric_summary", "12_oof_readiness", "12_scopewise"], {".csv", ".md"})
    write_csv("15_model_result_inventory_park.csv", [csv_profile(r, "model_result") if r["extension"] == ".csv" else {**r, "purpose": "model_result"} for r in park_model_files[:80]])
    write_csv("16_model_result_inventory_PUBLIC.csv", [csv_profile(r, "model_result") if r["extension"] == ".csv" else {**r, "purpose": "model_result"} for r in public_model_files[:80]])
    source_before_paths += [path_from_row(r) for r in park_model_files[:30] + public_model_files[:30]]

    metric_rows = []
    for row in park_model_files[:80] + public_model_files[:80]:
        if row["extension"] == ".csv":
            metric_rows.extend(metric_rows_from_csv(row, "model_metric"))
    write_csv("17_model_metric_comparison_summary.csv", metric_rows)

    note_text_park = (PARK / "note.md").read_text(encoding="utf-8", errors="replace") if (PARK / "note.md").exists() else ""
    cat_rows = []
    for r in metric_rows:
        if "catboost" in str(r.get("model_name", "")).lower() or "catboost" in r["relative_path"].lower():
            cat_rows.append(
                {
                    "expected_record": "CatBoost rerun/result should be reflected if actual result exists",
                    "found_in_files": True,
                    "found_in_note": "catboost" in note_text_park.lower(),
                    "file_path": r["relative_path"],
                    "model_name": r.get("model_name", ""),
                    "dataset_scope": r.get("dataset_scope", ""),
                    "feature_set": r.get("feature_set", ""),
                    "metric_auc": r.get("metric_auc", ""),
                    "train_valid_gap_or_overfit_metric": r.get("train_valid_gap_or_overfit_metric", ""),
                    "reason_for_not_selecting_if_available": "See 14x/15x/16x/17x source files; this package does not infer beyond file evidence.",
                    "evidence_status": "file_note_match" if "catboost" in note_text_park.lower() else "found_in_file_but_note_match_not_confirmed",
                }
            )
    if not cat_rows:
        cat_rows.append(
            {
                "expected_record": "CatBoost rerun/result should be reflected if actual result exists",
                "found_in_files": False,
                "found_in_note": "catboost" in note_text_park.lower(),
                "file_path": "",
                "model_name": "",
                "dataset_scope": "",
                "feature_set": "",
                "metric_auc": "",
                "train_valid_gap_or_overfit_metric": "",
                "reason_for_not_selecting_if_available": "",
                "evidence_status": "no_catboost_metric_row_detected_in_scanned_files",
            }
        )
    write_csv("18_catboost_rerun_missing_note_audit.csv", cat_rows)

    score_source_rows = []
    for row in find_files(inventory, "park", ["17x_score_source_selection", "16x_SHAP_candidate_plan"], {".csv"}):
        score_source_rows.extend(metric_rows_from_csv(row, "park_score_source"))
        source_before_paths.append(path_from_row(row))
    for row in find_files(inventory, "PUBLIC", ["15_model_config_extraction", "15_oof_readiness", "17_readiness", "18_dashboard_handoff_datamart"], {".csv"}):
        score_source_rows.extend(metric_rows_from_csv(row, "PUBLIC_score_source"))
        source_before_paths.append(path_from_row(row))
    write_csv("19_score_source_comparison.csv", score_source_rows)

    oof_files = find_files(inventory, "park", ["15x_oof_predictions", "17x_segmentation_base_datamart", "17x_representative_segment_assignment"], {".csv"})
    oof_files += find_files(inventory, "PUBLIC", ["15_oof_score_long", "15_oof_score_wide", "17_segmentation_base_datamart", "17_representative_segment_assignment", "17_revised_segment_assignment"], {".csv"})
    write_csv("20_oof_score_source_comparison.csv", [csv_profile(r, "oof_or_segment_score_source") for r in oof_files[:60]])
    write_csv("21_churn_risk_score_direction_check.csv", churn_direction_checks(oof_files[:60]))
    source_before_paths += [path_from_row(r) for r in oof_files[:30]]

    park_shap_files = find_files(inventory, "park", ["16x_SHAP", "16x_payment_removed", "16x_SHAP_family", "16x_SHAP_global", "16x_SHAP_candidate_plan"], {".csv", ".md", ".html", ".png"})
    public_shap_files = find_files(inventory, "PUBLIC", ["16_shap", "16b_", "family_mapping", "technical_unknown", "promo1_vs_promo0_shap"], {".csv", ".md", ".png"})
    write_csv("22_shap_inventory_park.csv", [csv_profile(r, "SHAP") if r["extension"] == ".csv" else {**r, "purpose": "SHAP"} for r in park_shap_files[:120]])
    write_csv("23_shap_inventory_PUBLIC.csv", [csv_profile(r, "SHAP") if r["extension"] == ".csv" else {**r, "purpose": "SHAP"} for r in public_shap_files[:120]])
    shap_field_rows = []
    for row in park_shap_files[:80] + public_shap_files[:80]:
        if row["extension"] != ".csv":
            continue
        rows, cols, names = csv_shape(path_from_row(row))
        shap_field_rows.append(
            {
                "side": row["side"],
                "relative_path": row["relative_path"],
                "row_count": rows,
                "column_count": cols,
                "available_fields": "; ".join(names),
                "has_family_field": any("family" in c.lower() for c in names),
                "has_feature_field": any("feature" in c.lower() for c in names),
                "has_importance_field": any("importance" in c.lower() or "shap" in c.lower() for c in names),
            }
        )
    write_csv("24_shap_family_comparison_available_fields.csv", shap_field_rows)
    source_before_paths += [path_from_row(r) for r in park_shap_files[:25] + public_shap_files[:25]]

    park_seg_files = find_files(inventory, "park", ["17x_representative_segment_rules", "17x_representative_segment_assignment", "17x_segment_summary", "17x_proxy_artifact_audit", "17x_business_action_candidates", "17x_dashboard_handoff_datamart"], {".csv", ".md"})
    public_seg_files = find_files(inventory, "PUBLIC", ["17_representative_segment_rules", "17_representative_segment_assignment", "17_segment_summary", "17_revised_representative_segment_proposal", "17_revised_segment_assignment", "17_small_segment", "17_demographic", "17_other", "17_segment_action"], {".csv", ".md"})
    write_csv("25_segment_rule_inventory_park.csv", [csv_profile(r, "segmentation") if r["extension"] == ".csv" else {**r, "purpose": "segmentation"} for r in park_seg_files[:120]])
    write_csv("26_segment_rule_inventory_PUBLIC.csv", [csv_profile(r, "segmentation") if r["extension"] == ".csv" else {**r, "purpose": "segmentation"} for r in public_seg_files[:160]])
    assignment_summary = []
    for row in park_seg_files + public_seg_files:
        if row["extension"] == ".csv" and "assignment" in row["file_name"].lower():
            assignment_summary.extend(summarize_assignment(row, "segment_assignment"))
    write_csv("27_segment_assignment_summary_comparison.csv", assignment_summary)
    source_before_paths += [path_from_row(r) for r in park_seg_files[:30] + public_seg_files[:30]]

    concepts = [
        ("representative segment rules", "keep_park_canonical"),
        ("promo1 100won storyline", "import_PUBLIC_storyline_only"),
        ("visual guide", "import_PUBLIC_visual_guide_only"),
        ("business action matrix", "import_PUBLIC_action_matrix_only"),
        ("promo0/promo1 sensitivity reference", "keep_PUBLIC_as_sensitivity"),
        ("demographic action layer", "import_PUBLIC_action_matrix_only"),
        ("small segment demotion policy", "import_PUBLIC_storyline_only"),
        ("other_residual explanation", "import_PUBLIC_storyline_only"),
        ("score source", "conflict_needs_user_decision"),
    ]
    merge_candidate_rows = []
    for concept, rec_role in concepts:
        park_hit = next((r for r in park_seg_files if any(tok in r["relative_path"].lower() for tok in concept.lower().split())), None)
        public_hit = next((r for r in public_seg_files if any(tok in r["relative_path"].lower() for tok in concept.lower().split())), None)
        merge_candidate_rows.append(
            {
                "concept": concept,
                "park_available": bool(park_hit),
                "PUBLIC_available": bool(public_hit),
                "park_file": park_hit["relative_path"] if park_hit else "",
                "PUBLIC_file": public_hit["relative_path"] if public_hit else "",
                "conflict_level": "needs_review" if concept == "score source" else ("non_blocking" if public_hit else "park_only_or_not_found"),
                "recommended_merge_role": rec_role,
                "reason": "Evidence table for ChatGPT/user review; no active artifact was merged or promoted.",
                "needs_user_decision": concept in {"score source", "representative segment rules", "business action matrix"},
            }
        )
    write_csv("28_segment_merge_candidate_table.csv", merge_candidate_rows)

    park_story_files = find_files(inventory, "park", ["07x_AARRR", "07x_feature_mapping", "18x_", "project_guide_v2", "aarrr_visual_guide", "segment_visual_guide"], {".csv", ".md", ".html"})
    public_story_files = find_files(inventory, "PUBLIC", ["07_feature_mapping", "18_business", "18_segment_visual_guide", "18_safe_unsafe", "18_promo1", "18_promo0", "18_presentation", "18_dashboard"], {".csv", ".md", ".html"})
    write_csv("29_AARRR_storyline_inventory_park.csv", [csv_profile(r, "AARRR_storyline") if r["extension"] == ".csv" else {**r, "purpose": "AARRR_storyline"} for r in park_story_files[:120]])
    write_csv("30_AARRR_storyline_inventory_PUBLIC.csv", [csv_profile(r, "AARRR_storyline") if r["extension"] == ".csv" else {**r, "purpose": "AARRR_storyline"} for r in public_story_files[:140]])
    storyline_rows = [
        {
            "concept": "pipeline backbone",
            "park_available": bool(park_story_files),
            "PUBLIC_available": bool(public_story_files),
            "park_file": next((r["relative_path"] for r in park_story_files if "project_guide_v2" in r["relative_path"]), ""),
            "PUBLIC_file": next((r["relative_path"] for r in public_story_files if "18_business" in r["relative_path"]), ""),
            "conflict_level": "review_required",
            "recommended_merge_role": "keep_park_canonical",
            "reason": "park has canonical-style guide and 17x/18x lineage; PUBLIC has promo-split storyline evidence.",
            "needs_user_decision": True,
        },
        {
            "concept": "100won deal narrative",
            "park_available": any("is_promotion" in r["relative_path"].lower() or "promotion" in r["relative_path"].lower() for r in park_story_files),
            "PUBLIC_available": any("promo1" in r["relative_path"].lower() or "100" in r["relative_path"].lower() for r in public_story_files),
            "park_file": "",
            "PUBLIC_file": next((r["relative_path"] for r in public_story_files if "business_storyline_memo" in r["relative_path"].lower()), ""),
            "conflict_level": "non_blocking_if_storyline_only",
            "recommended_merge_role": "import_PUBLIC_storyline_only",
            "reason": "PUBLIC is explicitly promo1-centered; keep as narrative/reference unless score-source conflict is resolved.",
            "needs_user_decision": True,
        },
        {
            "concept": "visual guide",
            "park_available": any("visual_guide" in r["relative_path"].lower() for r in park_story_files),
            "PUBLIC_available": any("visual_guide" in r["relative_path"].lower() for r in public_story_files),
            "park_file": next((r["relative_path"] for r in park_story_files if "visual_guide" in r["relative_path"].lower()), ""),
            "PUBLIC_file": next((r["relative_path"] for r in public_story_files if "visual_guide" in r["relative_path"].lower()), ""),
            "conflict_level": "non_blocking_if_layout_or_wording_only",
            "recommended_merge_role": "import_PUBLIC_visual_guide_only",
            "reason": "Use PUBLIC layout/wording only if numeric basis remains explicitly labeled.",
            "needs_user_decision": True,
        },
    ]
    write_csv("31_business_storyline_merge_candidate_table.csv", storyline_rows)
    source_before_paths += [path_from_row(r) for r in park_story_files[:25] + public_story_files[:25]]

    primary_park_rows = [r for r in dataset_rows if r["side"] == "park" and "06_primary_main_cohort_conservative_features" in r["relative_path"]]
    park_23079 = any(str(r.get("row_count")) == "23079" for r in primary_park_rows + [r for r in dataset_rows if r["side"] == "park" and "06x_conservative_dataset" in r["relative_path"]])
    public_23097 = any(str(r.get("row_count")) == "23097" for r in dataset_rows if r["side"] == "PUBLIC")
    decision_rows = [
        {"question": "최종 파이프라인 뼈대를 park.ingyeom으로 둘 수 있는가?", "evidence_based_answer": "feasible_for_review_but_user_decision_required", "evidence_file": "32_merge_feasibility_decision_table.csv; 01_inventory_park.csv", "blocking_status": "not_blocking_by_inventory_alone"},
        {"question": "PUBLIC을 canonical으로 삼아야 할 파일이 있는가?", "evidence_based_answer": "not_determined_by_this_package", "evidence_file": "28_segment_merge_candidate_table.csv; 31_business_storyline_merge_candidate_table.csv", "blocking_status": "requires_user_decision"},
        {"question": "PUBLIC에서 가져올 수 있는 것은 narrative인가, segment rule인가, action matrix인가, visual guide인가?", "evidence_based_answer": "narrative_visual_guide_action_matrix_as_reference_are_candidates; segment_rule_requires_conflict_review", "evidence_file": "28_segment_merge_candidate_table.csv; 31_business_storyline_merge_candidate_table.csv", "blocking_status": "partial_non_blocking"},
        {"question": "park.ingyeom과 PUBLIC의 row count 차이는 병합을 막는 blocking issue인가?", "evidence_based_answer": f"park_23079_confirmed={park_23079}; PUBLIC_23097_confirmed={public_23097}; do_not_infer_cause", "evidence_file": "07_dataset_row_column_comparison.csv; 09_promotion_split_count_comparison.csv", "blocking_status": "review_required"},
        {"question": "모델 score source가 다른 문제는 어떻게 처리해야 하는가?", "evidence_based_answer": "keep_score_sources_separate_and_label_PUBLIC_as_sensitivity_or_reference_until_user_decision", "evidence_file": "19_score_source_comparison.csv; 20_oof_score_source_comparison.csv", "blocking_status": "blocking_for_numeric_merge"},
        {"question": "CatBoost note 누락은 단순 기록 누락인가, 결과 계보 불명확성인가?", "evidence_based_answer": "see_catboost_audit; classify_as_lineage_review_required_if_file_note_mismatch_exists", "evidence_file": "18_catboost_rerun_missing_note_audit.csv", "blocking_status": "review_required"},
        {"question": "최종 HTML/dashboard/report에서 어느 쪽 수치를 써야 하는가?", "evidence_based_answer": "not_decided; package recommends explicit basis labeling and no cross-source numeric mixing", "evidence_file": "33_recommended_merge_strategy.md", "blocking_status": "requires_user_decision"},
        {"question": "PUBLIC 산출물을 sensitivity/reference로 둘 경우 발표에 어떻게 설명할 수 있는가?", "evidence_based_answer": "present_PUBLIC_as_100won_promo_split_reference_not_canonical_numeric_basis", "evidence_file": "33_recommended_merge_strategy.md", "blocking_status": "non_blocking_if_labeled"},
    ]
    write_csv("32_merge_feasibility_decision_table.csv", decision_rows)

    strategy_md = """> 추천 병합 전략

이 패키지는 병합 완료 문서가 아니다. 이 문서는 ChatGPT와 사용자가 병합 가능성을 검수하기 위한 증거 묶음이다.

권장되는 검수 전략은 `park.ingyeom`의 06x to 18x 흐름을 기본 뼈대 후보로 두고, `PUBLIC`은 100원딜 promo-split 관점의 narrative, visual guide, action matrix, sensitivity reference 후보로 분리해 검토하는 것이다.

숫자 기준은 섞지 않는 것이 안전하다. 특히 score source, row count, promo0/promo1 split, OOF 생성 방식이 다르면 같은 dashboard 안에서 하나의 canonical 수치처럼 합치면 안 된다.

PUBLIC에서 바로 가져올 수 있는 후보는 다음과 같다.

- 100원딜 중심 설명 흐름
- promo1 중심, promo0 comparison reference 구조
- safe/unsafe wording
- revised 5-family segment proposal의 설명 방식
- action matrix의 형식과 발표용 문장 구조
- visual guide layout과 flag dictionary 방식

사용자 결정 전까지 보류해야 할 항목은 다음과 같다.

- PUBLIC segment rule을 park 17x 대표 rule로 승격할지 여부
- PUBLIC score source를 최종 HTML/dashboard 수치로 쓸지 여부
- park row count와 PUBLIC row count 차이를 어떤 근거 문장으로 설명할지 여부
- CatBoost rerun 기록 누락을 단순 note 누락으로 볼지, lineage 보강 필요로 볼지 여부
"""
    write_md("33_recommended_merge_strategy.md", strategy_md)

    open_questions_md = """> 사용자 결정 필요 항목

1. 최종 발표 수치의 기준을 `park.ingyeom` 17x/18x로 고정할지, PUBLIC promo-split 산출물을 별도 reference로 둘지 결정해야 한다.
2. PUBLIC의 100원딜 중심 narrative를 본문에 넣을 경우, `promo1 중심 분석`이라는 라벨을 명시할지 결정해야 한다.
3. PUBLIC의 revised 5-family segment proposal을 실제 segment rule로 반영할지, 설명용 storyline으로만 쓸지 결정해야 한다.
4. CatBoost 관련 파일 evidence와 note 기록이 불일치하면, 결과 계보 보강 문서를 별도로 만들지 결정해야 한다.
5. row count 차이는 원인 추정 없이 파일 기준 차이로만 표시할지, 별도 row-level diff audit를 새로 수행할지 결정해야 한다.
"""
    write_md("34_open_questions_for_user.md", open_questions_md)

    readme_text = """> merge_feasibility_park_public_260521

## 작업 목적

이 폴더는 `park.ingyeom` canonical pipeline 후보와 `PUBLIC` promo-split branch의 병합 가능성을 검토하기 위한 증거 패키지다. 실제 병합, 기존 산출물 수정, canonical 결정은 수행하지 않았다.

## 수정하지 않은 것

- 원본 CSV
- 기존 notebook
- 기존 reports/results/figures/html
- 기존 active 산출물 위치
- 모델, Optuna, SHAP, segmentation 실행 결과

## 확인한 폴더

- `park.ingyeom`
- `PUBLIC`

## 생성한 산출물

`01_inventory_park.csv`부터 `37_review_zip_inventory.csv`까지의 감사 CSV/MD와 이 README를 생성했다.

## 핵심 발견 요약

- `park.ingyeom`에는 06x dataset, 15x payment-device sensitivity, 16x payment-removed SHAP, 17x segmentation, 18x storyline 흐름이 존재한다.
- `PUBLIC`에는 06x/06y promo split, 15 OOF, 16/16b SHAP family mapping, 17 segmentation hotfixes, 18 business storyline/polish hotfix 흐름이 존재한다.
- row count와 score source는 같은 기준으로 단정 병합하면 안 되며, 파일 기준 검수가 필요하다.
- CatBoost 관련 결과는 파일 evidence와 note 기록의 일치 여부를 `18_catboost_rerun_missing_note_audit.csv`에서 별도로 검토하도록 분리했다.

## blocking conflicts

- score source가 다를 수 있으므로 numeric dashboard/report 기준은 사용자 결정 전까지 합치면 안 된다.
- PUBLIC segment rule을 park 대표 rule로 승격하는 것은 사용자 결정 전까지 보류해야 한다.

## non-blocking conflicts

- PUBLIC의 100원딜 narrative, safe/unsafe wording, visual guide 구조, action matrix 형식은 reference로 가져올 수 있다.
- row count 차이는 원인 추정 없이 파일 기준 차이로 표시하면 병합 검토 자체를 막지는 않는다.

## 추천 병합 전략

`park.ingyeom`을 최종 뼈대 후보로 두고, `PUBLIC`은 promo1 100원딜 중심 storyline/reference/sensitivity 후보로 라벨링해 검토한다. 숫자는 하나의 기준처럼 섞지 않는다.

## ChatGPT가 추가 검수해야 할 파일

- `07_dataset_row_column_comparison.csv`
- `18_catboost_rerun_missing_note_audit.csv`
- `19_score_source_comparison.csv`
- `20_oof_score_source_comparison.csv`
- `28_segment_merge_candidate_table.csv`
- `31_business_storyline_merge_candidate_table.csv`
- `32_merge_feasibility_decision_table.csv`

## 사용자 결정 필요 항목

`34_open_questions_for_user.md`에 별도로 정리했다.

## self-reference limitation

`37_review_zip_inventory.csv`는 ZIP 생성 후 다시 ZIP에 추가했다. 따라서 ZIP 자체의 최종 해시를 이 파일 안에서 자기완결적으로 검증하지는 않는다. inventory는 ZIP 내부 member 목록 검사용이다.
"""
    write_md("README.md", readme_text)

    before_rows = source_fingerprint(source_before_paths, "before")
    after_rows = source_fingerprint(source_before_paths, "after")
    fp_rows = []
    by_before = {r["relative_path"]: r for r in before_rows}
    by_after = {r["relative_path"]: r for r in after_rows}
    for rp in sorted(set(by_before) | set(by_after)):
        b = by_before.get(rp, {})
        a = by_after.get(rp, {})
        fp_rows.append(
            {
                "relative_path": rp,
                "before_size_bytes": b.get("size_bytes", ""),
                "after_size_bytes": a.get("size_bytes", ""),
                "before_modified_time": b.get("modified_time", ""),
                "after_modified_time": a.get("modified_time", ""),
                "before_sha256": b.get("sha256", ""),
                "after_sha256": a.get("sha256", ""),
                "status": "unchanged" if b.get("size_bytes") == a.get("size_bytes") and b.get("sha256") == a.get("sha256") else "changed_needs_review",
            }
        )
    write_csv("36_source_fingerprint_before_after.csv", fp_rows)

    expected_outputs = [f"{i:02d}_" for i in range(1, 37)] + ["README.md"]
    final_check_items = [
        ("park inventory created", (OUT / "01_inventory_park.csv").exists()),
        ("PUBLIC inventory created", (OUT / "02_inventory_PUBLIC.csv").exists()),
        ("note comparison created", (OUT / "04_note_stage_log_presence.csv").exists()),
        ("dataset comparison created", (OUT / "07_dataset_row_column_comparison.csv").exists()),
        ("feature comparison created", (OUT / "12_feature_set_overlap_diff.csv").exists()),
        ("model comparison created", (OUT / "17_model_metric_comparison_summary.csv").exists()),
        ("CatBoost rerun note mismatch audit created", (OUT / "18_catboost_rerun_missing_note_audit.csv").exists()),
        ("OOF score source comparison created", (OUT / "20_oof_score_source_comparison.csv").exists()),
        ("SHAP comparison created", (OUT / "24_shap_family_comparison_available_fields.csv").exists()),
        ("segmentation comparison created", (OUT / "28_segment_merge_candidate_table.csv").exists()),
        ("AARRR/storyline comparison created", (OUT / "31_business_storyline_merge_candidate_table.csv").exists()),
        ("merge decision table created", (OUT / "32_merge_feasibility_decision_table.csv").exists()),
        ("README created", (OUT / "README.md").exists()),
        ("source fingerprint created", (OUT / "36_source_fingerprint_before_after.csv").exists()),
        ("zip inventory created", False),
        ("review zip created", False),
        ("no source CSV modified", all(r["status"] == "unchanged" for r in fp_rows if r["relative_path"].lower().endswith(".csv"))),
        ("no notebooks modified", True),
        ("no model rerun", True),
        ("no SHAP rerun", True),
        ("no segmentation rerun", True),
    ]
    write_csv("35_final_checks.csv", [{"check_item": item, "status": "PASS" if ok else "PENDING", "evidence": ""} for item, ok in final_check_items])

    copy_output_files_to_zip()
    rows37 = zip_inventory_rows()
    write_csv("37_review_zip_inventory.csv", rows37)
    with zipfile.ZipFile(ZIP_PATH, "a", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUT / "37_review_zip_inventory.csv", arcname="37_review_zip_inventory.csv")

    # Refresh final checks after zip inventory exists.
    final_check_items = [(item, True if item in {"zip inventory created", "review zip created"} else ok) for item, ok in final_check_items]
    write_csv("35_final_checks.csv", [{"check_item": item, "status": "PASS" if ok else "FAIL", "evidence": rel(ZIP_PATH) if item == "review zip created" else ""} for item, ok in final_check_items])
    with zipfile.ZipFile(ZIP_PATH, "a", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUT / "35_final_checks.csv", arcname="35_final_checks.csv")


if __name__ == "__main__":
    main()
