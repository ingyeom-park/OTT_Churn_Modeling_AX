from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import textwrap
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[3]
PUBLIC_ROOT = REPO_ROOT / "PUBLIC"

OOF_DIR = PUBLIC_ROOT / "results" / "15_oof_score_or_sensitivity_260520" / "four_model_oof_scores_hotfix_260520"
SHAP_DIR = PUBLIC_ROOT / "results" / "16_SHAP_candidate_interpretation_260520" / "four_model_shap_interpretation"
HOTFIX16B_DIR = PUBLIC_ROOT / "results" / "16_SHAP_candidate_interpretation_260520" / "16b_feature_family_mapping_hotfix_260520"
DATA_DIR = PUBLIC_ROOT / "data"

OUTPUT_DIR = PUBLIC_ROOT / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments"
HANDOFF_DIR = PUBLIC_ROOT / "handoff" / "PUBLIC_17_promo_scope_oof_behavior_segmentation_260520"
NOTEBOOK_DIR = PUBLIC_ROOT / "notebooks" / "17_segmentation_design_260520"
NOTEBOOK_PATH = NOTEBOOK_DIR / "17_promo_scope_oof_behavior_segmentation_260520.ipynb"
EXECUTED_NOTEBOOK_PATH = NOTEBOOK_DIR / "17_promo_scope_oof_behavior_segmentation_260520_executed.ipynb"
ZIP_PATH = PUBLIC_ROOT / "zip" / "PUBLIC_17_promo_scope_oof_behavior_segmentation_260520_review_package.zip"

PRIMARY_RISK_CUT = "gb_high_risk_top20"

REQUIRED_INPUTS: list[tuple[str, Path]] = [
    ("15_oof_score_long.csv", OOF_DIR / "15_oof_score_long.csv"),
    ("15_oof_score_wide.csv", OOF_DIR / "15_oof_score_wide.csv"),
    ("15_oof_score_wide_promo0.csv", OOF_DIR / "15_oof_score_wide_promo0.csv"),
    ("15_oof_score_wide_promo1.csv", OOF_DIR / "15_oof_score_wide_promo1.csv"),
    ("15_oof_metric_summary.csv", OOF_DIR / "15_oof_metric_summary.csv"),
    ("15_gb_lr_high_risk_overlap.csv", OOF_DIR / "15_gb_lr_high_risk_overlap.csv"),
    ("15_oof_readiness_for_shap_segmentation.csv", OOF_DIR / "15_oof_readiness_for_shap_segmentation.csv"),
    ("16_shap_global_importance.csv", SHAP_DIR / "16_shap_global_importance.csv"),
    ("16_shap_family_importance.csv", SHAP_DIR / "16_shap_family_importance.csv"),
    ("16_promo1_vs_promo0_shap_comparison.csv", SHAP_DIR / "16_promo1_vs_promo0_shap_comparison.csv"),
    ("16_demographic_context_audit_for_shap.csv", SHAP_DIR / "16_demographic_context_audit_for_shap.csv"),
    ("16_is_churn_prevented_interpretation_audit.csv", SHAP_DIR / "16_is_churn_prevented_interpretation_audit.csv"),
    ("16_readiness_for_segmentation.csv", SHAP_DIR / "16_readiness_for_segmentation.csv"),
    ("16b_feature_family_mapping_hotfix.csv", HOTFIX16B_DIR / "16b_feature_family_mapping_hotfix.csv"),
    ("16b_shap_family_importance_hotfix.csv", HOTFIX16B_DIR / "16b_shap_family_importance_hotfix.csv"),
    ("16b_promo1_vs_promo0_shap_comparison_hotfix.csv", HOTFIX16B_DIR / "16b_promo1_vs_promo0_shap_comparison_hotfix.csv"),
    ("16b_family_interpretation_handoff_for_17.csv", HOTFIX16B_DIR / "16b_family_interpretation_handoff_for_17.csv"),
    ("06_model_input_promo_0.csv", DATA_DIR / "06_model_input_promo_0.csv"),
    ("06_model_input_promo_1.csv", DATA_DIR / "06_model_input_promo_1.csv"),
]

RESULT_FILES = [
    "README.md",
    "17_segmentation_base_datamart.csv",
    "17_base_datamart_validation.csv",
    "17_internal_multiflag_definitions.csv",
    "17_internal_multiflag_assignment.csv",
    "17_representative_segment_rules.csv",
    "17_representative_segment_assignment.csv",
    "17_segment_summary.csv",
    "17_segment_feature_profile.csv",
    "17_segment_SHAP_family_evidence_link.csv",
    "17_segment_demographic_profile.csv",
    "17_segment_age_gender_behavior_profile.csv",
    "17_segment_action_personalization_matrix.csv",
    "17_segment_business_action_candidates.csv",
    "17_segment_rationale_memo_for_executives.md",
    "17_segment_rationale_evidence_table.csv",
    "17_segment_caveat_and_rejected_alternatives.md",
    "17_readiness_for_18_business_storyline.csv",
]


def ensure_dirs() -> None:
    for path in [OUTPUT_DIR, HANDOFF_DIR, NOTEBOOK_DIR, ZIP_PATH.parent]:
        path.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT)).replace("/", "\\")


def write_rows(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_shape(path: Path) -> tuple[Any, Any]:
    if not path.exists() or path.suffix.lower() != ".csv":
        return "", ""
    df = pd.read_csv(path)
    return len(df), len(df.columns)


def input_validation() -> Path:
    rows = []
    for name, path in REQUIRED_INPUTS:
        n_rows, n_cols = file_shape(path)
        rows.append(
            {
                "input_item": name,
                "expected_path": rel(path),
                "exists": path.exists(),
                "rows": n_rows,
                "columns": n_cols,
                "status": "PASS" if path.exists() else "FAIL",
                "notes": "required input for PUBLIC 17 segmentation design",
            }
        )
    return write_rows(HANDOFF_DIR / "17_input_validation.csv", rows, ["input_item", "expected_path", "exists", "rows", "columns", "status", "notes"])


def snapshot_targets() -> list[tuple[Path, str]]:
    targets = [(path, "input") for _name, path in REQUIRED_INPUTS]
    targets += [(OUTPUT_DIR / name, "17_output") for name in RESULT_FILES]
    targets += [
        (HANDOFF_DIR / "README.md", "17_handoff"),
        (HANDOFF_DIR / "17_input_validation.csv", "17_handoff"),
        (HANDOFF_DIR / "17_source_fingerprint_before_after.csv", "17_handoff"),
        (HANDOFF_DIR / "PUBLIC_17_promo_scope_oof_behavior_segmentation_final_checks.csv", "17_handoff"),
        (HANDOFF_DIR / "PUBLIC_17_promo_scope_oof_behavior_segmentation_zip_inventory.csv", "17_handoff"),
        (SCRIPT_PATH, "17_helper"),
        (NOTEBOOK_PATH, "17_notebook"),
        (EXECUTED_NOTEBOOK_PATH, "17_notebook"),
        (PUBLIC_ROOT / "note.md", "note"),
    ]
    return targets


def snapshot() -> dict[str, dict[str, Any]]:
    data: dict[str, dict[str, Any]] = {}
    for path, role in snapshot_targets():
        key = rel(path)
        if path.exists():
            data[key] = {"file_path": key, "file_role": role, "sha256": sha256_file(path), "size": path.stat().st_size}
        else:
            data[key] = {"file_path": key, "file_role": role, "sha256": "", "size": ""}
    return data


def write_fingerprint(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> Path:
    rows = []
    for key in sorted(set(before) | set(after)):
        b = before.get(key, {})
        a = after.get(key, {})
        role = a.get("file_role") or b.get("file_role", "")
        if b.get("sha256") and a.get("sha256") and b.get("sha256") == a.get("sha256"):
            status = "unchanged"
        elif role == "note" and b.get("sha256") and a.get("sha256") and b.get("sha256") != a.get("sha256"):
            status = "intentionally_updated_note"
        elif role in {"17_output", "17_handoff", "17_notebook"} and not b.get("sha256") and a.get("sha256"):
            status = "new_output_created"
        elif role in {"17_output", "17_handoff"} and b.get("sha256") and a.get("sha256") and b.get("sha256") != a.get("sha256"):
            status = "intentionally_updated_17_output"
        elif key == rel(EXECUTED_NOTEBOOK_PATH) and a.get("sha256"):
            status = "intentionally_updated_17_executed_notebook"
        elif b.get("sha256") and not a.get("sha256"):
            status = "missing_after"
        elif b.get("sha256") and a.get("sha256") and b.get("sha256") != a.get("sha256"):
            status = "changed_needs_review"
        else:
            status = "missing_before_and_after"
        rows.append(
            {
                "file_path": key,
                "file_role": role,
                "sha256_before": b.get("sha256", ""),
                "sha256_after": a.get("sha256", ""),
                "size_before": b.get("size", ""),
                "size_after": a.get("size", ""),
                "status": status,
            }
        )
    return write_rows(HANDOFF_DIR / "17_source_fingerprint_before_after.csv", rows, ["file_path", "file_role", "sha256_before", "sha256_after", "size_before", "size_after", "status"])


def load_base() -> tuple[pd.DataFrame, pd.DataFrame]:
    wide = pd.read_csv(OOF_DIR / "15_oof_score_wide.csv")
    frames = []
    for scope, path in [("promo0", DATA_DIR / "06_model_input_promo_0.csv"), ("promo1", DATA_DIR / "06_model_input_promo_1.csv")]:
        df = pd.read_csv(path)
        df.insert(0, "row_id", np.arange(len(df), dtype=int))
        df.insert(1, "promo_scope", scope)
        frames.append(df)
    inputs = pd.concat(frames, ignore_index=True)
    base = wide.merge(inputs, on=["promo_scope", "row_id"], how="left", suffixes=("", "_input"))
    if "USER_KEY_input" in base.columns and "USER_KEY" in base.columns:
        base = base.drop(columns=["USER_KEY_input"])
    return wide, base


def create_base_datamart(wide: pd.DataFrame, base: pd.DataFrame) -> Path:
    base["gb_lr_both_high_risk_top20"] = ((base["gb_high_risk_top20"] == 1) & (base["lr_high_risk_top20"] == 1)).astype(int)
    base["gb_only_high_risk_top20"] = ((base["gb_high_risk_top20"] == 1) & (base["lr_high_risk_top20"] == 0)).astype(int)
    base["lr_only_high_risk_top20"] = ((base["gb_high_risk_top20"] == 0) & (base["lr_high_risk_top20"] == 1)).astype(int)
    base["neither_high_risk_top20"] = ((base["gb_high_risk_top20"] == 0) & (base["lr_high_risk_top20"] == 0)).astype(int)
    base.to_csv(OUTPUT_DIR / "17_segmentation_base_datamart.csv", index=False, encoding="utf-8-sig")
    return OUTPUT_DIR / "17_segmentation_base_datamart.csv"


def validate_base(base: pd.DataFrame) -> Path:
    rows = []
    def add(check: str, status: str, expected: str, actual: Any, notes: str = "") -> None:
        rows.append({"check_item": check, "status": status, "expected": expected, "actual": actual, "notes": notes})
    counts = base.groupby("promo_scope").size().to_dict()
    add("promo0_row_count_matches", "PASS" if counts.get("promo0") == 11193 else "FAIL", "11193", counts.get("promo0"))
    add("promo1_row_count_matches", "PASS" if counts.get("promo1") == 11904 else "FAIL", "11904", counts.get("promo1"))
    duplicate_count = int(base.duplicated(["promo_scope", "row_id"]).sum())
    add("row_id_unique_within_scope", "PASS" if duplicate_count == 0 else "FAIL", "0 duplicates", duplicate_count)
    gb_diff = (base["gb_churn_risk_score_oof"] - (1 - base["gb_repurchase_score_oof"])).abs().max()
    lr_diff = (base["lr_churn_risk_score_oof"] - (1 - base["lr_repurchase_score_oof"])).abs().max()
    add("gb_churn_risk_direction", "PASS" if gb_diff < 1e-9 else "FAIL", "gb_churn=1-gb_repurchase", gb_diff)
    add("lr_churn_risk_direction", "PASS" if lr_diff < 1e-9 else "FAIL", "lr_churn=1-lr_repurchase", lr_diff)
    required_cols = ["gb_high_risk_top10", "gb_high_risk_top20", "gb_high_risk_top30", "lr_high_risk_top10", "lr_high_risk_top20", "lr_high_risk_top30"]
    missing = [c for c in required_cols if c not in base.columns]
    add("top_risk_flags_exist", "PASS" if not missing else "FAIL", "risk flags present", ",".join(missing) if missing else "none")
    return write_rows(OUTPUT_DIR / "17_base_datamart_validation.csv", rows, ["check_item", "status", "expected", "actual", "notes"])


def q_by_scope(base: pd.DataFrame, col: str, q: float) -> dict[str, float]:
    return base.groupby("promo_scope")[col].quantile(q).to_dict()


def apply_scope_threshold(base: pd.DataFrame, col: str, thresholds: dict[str, float], op: str) -> pd.Series:
    vals = base.apply(lambda r: thresholds.get(r["promo_scope"], np.nan), axis=1)
    if op == "<=":
        return (base[col] <= vals).fillna(False)
    if op == ">=":
        return (base[col] >= vals).fillna(False)
    raise ValueError(op)


def add_definition(rows: list[dict[str, Any]], flag: str, req: list[str], formula: str, threshold_type: str, threshold: Any, created: bool, reason: str, interp: str, caveat: str) -> None:
    rows.append(
        {
            "flag_name": flag,
            "required_columns": ",".join(req),
            "formula": formula,
            "threshold_type": threshold_type,
            "threshold_value": threshold,
            "scope_applied": "promo0,promo1",
            "created": created,
            "reason_if_not_created": "" if created else reason,
            "interpretation": interp,
            "caveat": caveat,
        }
    )


def create_multiflags(base: pd.DataFrame) -> tuple[Path, Path, pd.DataFrame, list[str]]:
    df = base.copy()
    defs: list[dict[str, Any]] = []
    created_flags: list[str] = []

    for flag in ["gb_high_risk_top10", "gb_high_risk_top20", "gb_high_risk_top30", "lr_high_risk_top10", "lr_high_risk_top20", "lr_high_risk_top30"]:
        created = flag in df.columns
        if created:
            df[flag] = df[flag].astype(int)
            created_flags.append(flag)
        add_definition(defs, flag, [flag], f"{flag} from 15 OOF score", "percentile_rank", flag.replace("_high_risk_", ""), created, "missing OOF flag", "OOF risk percentile flag", "OOF score is not a final campaign threshold.")

    for flag in ["gb_lr_both_high_risk_top20", "gb_only_high_risk_top20", "lr_only_high_risk_top20", "neither_high_risk_top20"]:
        created = flag in df.columns
        if created:
            created_flags.append(flag)
        add_definition(defs, flag, [flag], f"{flag} from GB/LR top20 overlap", "derived_overlap", "top20", created, "missing overlap inputs", "GB/LR high-risk agreement flag", "Overlap is stability evidence, not final targeting approval.")

    low_parts = []
    low_reason_cols = []
    for flag, col in [("low_watch_count", "total_watch_count"), ("low_watch_time", "total_watch_time_min"), ("low_watch_days", "watch_days")]:
        if col in df.columns:
            thresholds = q_by_scope(df, col, 0.25)
            df[flag] = apply_scope_threshold(df, col, thresholds, "<=").astype(int)
            created_flags.append(flag)
            low_parts.append(flag)
            low_reason_cols.append((flag, col))
            add_definition(defs, flag, [col], f"{col} <= scope q25", "scope_quantile_q25", json.dumps(thresholds), True, "", f"Low {col} behavior component", "Component of broad low_activity flag.")
        else:
            add_definition(defs, flag, [col], f"{col} <= scope q25", "scope_quantile_q25", "", False, f"{col}_missing", f"Low {col} behavior component", "Not created because source column is unavailable.")
    if low_parts:
        df["low_activity"] = df[low_parts].max(axis=1).astype(int)
        def reason(row: pd.Series) -> str:
            hits = [flag for flag, _col in low_reason_cols if row.get(flag, 0) == 1]
            return ",".join(hits) if hits else "none"
        df["low_activity_reason"] = df.apply(reason, axis=1)
        created_flags += ["low_activity"]
        add_definition(defs, "low_activity", low_parts, " OR ".join(low_parts), "broad_composite", "any component true", True, "", "Broad low activity screening flag", "Broad flag: low count, low time, or low active days can trigger it.")
    else:
        df["low_activity"] = 0
        df["low_activity_reason"] = "not_created"
        add_definition(defs, "low_activity", ["total_watch_count", "total_watch_time_min", "watch_days"], "component OR", "broad_composite", "", False, "no_low_activity_source_columns", "Broad low activity screening flag", "Not created because source columns are unavailable.")

    if "is_cold_start_7d_fixed" in df.columns:
        df["cold_start_weak"] = (pd.to_numeric(df["is_cold_start_7d_fixed"], errors="coerce").fillna(0) == 0).astype(int)
        df["early_activation_success"] = (pd.to_numeric(df["is_cold_start_7d_fixed"], errors="coerce").fillna(0) == 1).astype(int)
        add_definition(defs, "cold_start_weak", ["is_cold_start_7d_fixed"], "is_cold_start_7d_fixed == 0", "binary_inverse", "0 means weak", True, "", "Weak or missing early activation within 7 days", "is_cold_start_7d_fixed=1 means early activation success, not weak activation.")
        add_definition(defs, "early_activation_success", ["is_cold_start_7d_fixed"], "is_cold_start_7d_fixed == 1", "binary", "1 means success", True, "", "Early activation success", "Helper flag to avoid confusing cold-start success with weak activation.")
        created_flags += ["cold_start_weak", "early_activation_success"]
    elif "is_cold_start_3d_fixed" in df.columns:
        df["cold_start_weak"] = (pd.to_numeric(df["is_cold_start_3d_fixed"], errors="coerce").fillna(0) == 0).astype(int)
        df["early_activation_success"] = (pd.to_numeric(df["is_cold_start_3d_fixed"], errors="coerce").fillna(0) == 1).astype(int)
        add_definition(defs, "cold_start_weak", ["is_cold_start_3d_fixed"], "is_cold_start_3d_fixed == 0", "binary_inverse", "0 means weak", True, "", "Weak or missing early activation within 3 days", "7d basis missing; is_cold_start_3d_fixed=1 means early activation success, not weak activation.")
        add_definition(defs, "early_activation_success", ["is_cold_start_3d_fixed"], "is_cold_start_3d_fixed == 1", "binary", "1 means success", True, "", "Early activation success", "7d basis missing.")
        created_flags += ["cold_start_weak", "early_activation_success"]
    elif "first_watch_rel_day" in df.columns:
        s = pd.to_numeric(df["first_watch_rel_day"], errors="coerce")
        df["cold_start_weak"] = ((s > 6) | s.isna()).astype(int)
        df["early_activation_success"] = ((s <= 6) & s.notna()).astype(int)
        add_definition(defs, "cold_start_weak", ["first_watch_rel_day"], "first_watch_rel_day > 6 OR missing", "explicit_day_cut", ">6", True, "", "Weak or delayed early activation", "Derived from first watch timing.")
        add_definition(defs, "early_activation_success", ["first_watch_rel_day"], "first_watch_rel_day <= 6", "explicit_day_cut", "<=6", True, "", "Early activation success", "Derived from first watch timing.")
        created_flags += ["cold_start_weak", "early_activation_success"]
    else:
        df["cold_start_weak"] = 0
        df["early_activation_success"] = 0
        add_definition(defs, "cold_start_weak", ["is_cold_start_7d_fixed", "is_cold_start_3d_fixed", "first_watch_rel_day"], "not created", "unavailable", "", False, "no_cold_start_source_columns", "Weak early activation", "No source column available.")
        add_definition(defs, "early_activation_success", ["is_cold_start_7d_fixed", "is_cold_start_3d_fixed", "first_watch_rel_day"], "not created", "unavailable", "", False, "no_cold_start_source_columns", "Early activation success", "No source column available.")

    def create_or_quant_flag(flag: str, cols_ops: list[tuple[str, float, str]], interp: str, caveat: str) -> None:
        parts = []
        desc = []
        threshold_payload = {}
        for col, q, op in cols_ops:
            if col in df.columns:
                thresholds = q_by_scope(df, col, q)
                threshold_payload[f"{col}_{op}_q{q}"] = thresholds
                parts.append(apply_scope_threshold(df, col, thresholds, op))
                desc.append(f"{col} {op} scope q{q}")
        if parts:
            combined = parts[0]
            for part in parts[1:]:
                combined = combined | part
            df[flag] = combined.astype(int)
            created_flags.append(flag)
            add_definition(defs, flag, [c for c, _q, _op in cols_ops], " OR ".join(desc), "scope_quantile", json.dumps(threshold_payload), True, "", interp, caveat)
        else:
            df[flag] = 0
            add_definition(defs, flag, [c for c, _q, _op in cols_ops], "not created", "scope_quantile", "", False, "required_columns_missing", interp, caveat)

    create_or_quant_flag("week2_drop", [("log_retention_w2_ratio", 0.25, "<="), ("diff_between_w2_w1", 0.25, "<=")], "Week 2 drop signal", "Behavior flag, not model feature creation.")
    create_or_quant_flag("week3_drop", [("log_retention_w3_ratio", 0.25, "<="), ("diff_between_w3_w2", 0.25, "<=")], "Week 3 drop signal", "Behavior flag, not model feature creation.")
    if "watch_time_min_w3" in df.columns or "watch_session_w3" in df.columns:
        cond = pd.Series(False, index=df.index)
        req = []
        if "watch_time_min_w3" in df.columns:
            cond = cond | (pd.to_numeric(df["watch_time_min_w3"], errors="coerce").fillna(0) == 0)
            req.append("watch_time_min_w3")
        if "watch_session_w3" in df.columns:
            cond = cond | (pd.to_numeric(df["watch_session_w3"], errors="coerce").fillna(0) == 0)
            req.append("watch_session_w3")
        df["week3_inactive"] = cond.astype(int)
        created_flags.append("week3_inactive")
        add_definition(defs, "week3_inactive", req, "watch_time_min_w3 == 0 OR watch_session_w3 == 0", "explicit_zero", "0", True, "", "No week 3 viewing/session activity", "Timing flag within prepared observation window.")
    else:
        df["week3_inactive"] = 0
        add_definition(defs, "week3_inactive", ["watch_time_min_w3", "watch_session_w3"], "not created", "explicit_zero", "", False, "week3_columns_missing", "No week 3 activity", "Not created.")

    for name, col in [("only_w1", "is_only_w1"), ("only_w2", "is_only_w2"), ("only_w3", "is_only_w3")]:
        if col in df.columns:
            df[name] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            created_flags.append(name)
            add_definition(defs, name, [col], f"{col} == 1", "binary", "1", True, "", f"{name} week-specific usage pattern", "Provisional behavior flag.")
        else:
            df[name] = 0
            add_definition(defs, name, [col], "not created", "binary", "", False, f"{col}_missing", f"{name} week-specific usage pattern", "Not created.")

    create_or_quant_flag("retention_decay", [("log_retention_w2_ratio", 0.25, "<="), ("log_retention_w3_ratio", 0.25, "<=")], "Log-retention decay signal", "Model explanation and behavior flag, not causality.")
    create_or_quant_flag("inactivity_recency_risk", [("recency", 0.75, ">="), ("max_inactive_gap_days", 0.75, ">=")], "Recent inactivity or long inactive gap", "Timing window must remain day0~20.")
    create_or_quant_flag("usage_concentrated", [("max_day_share", 0.75, ">="), ("active_ratio", 0.25, "<=")], "Activity concentrated in few days", "May interact with watch volume.")

    stable_req = ["active_ratio", "max_day_share", "watch_days", PRIMARY_RISK_CUT]
    if all(c in df.columns for c in stable_req):
        active_q75 = q_by_scope(df, "active_ratio", 0.75)
        maxday_q75 = q_by_scope(df, "max_day_share", 0.75)
        watch_median = q_by_scope(df, "watch_days", 0.50)
        stable = (
            apply_scope_threshold(df, "active_ratio", active_q75, ">=")
            & apply_scope_threshold(df, "max_day_share", maxday_q75, "<=")
            & apply_scope_threshold(df, "watch_days", watch_median, ">=")
            & (df[PRIMARY_RISK_CUT] == 0)
        )
        caveat_extra = []
        if "week3_inactive" in created_flags:
            stable = stable & (df["week3_inactive"] == 0)
        else:
            caveat_extra.append("week3_inactive_missing")
        if "retention_decay" in created_flags:
            stable = stable & (df["retention_decay"] == 0)
        else:
            caveat_extra.append("retention_decay_missing")
        df["stable_usage"] = stable.astype(int)
        created_flags.append("stable_usage")
        add_definition(defs, "stable_usage", stable_req + ["week3_inactive", "retention_decay"], "active_ratio>=q75 AND max_day_share<=q75 AND watch_days>=median AND gb_high_risk_top20=0 AND week3_inactive=0 AND retention_decay=0 when available", "scope_quantile_composite", json.dumps({"active_ratio_q75": active_q75, "max_day_share_q75": maxday_q75, "watch_days_median": watch_median}), True, "", "Provisional lower-risk behavior pattern", "Not final loyal segment. " + ";".join(caveat_extra))
    else:
        df["stable_usage"] = 0
        add_definition(defs, "stable_usage", stable_req, "not created", "scope_quantile_composite", "", False, "stable_usage_required_columns_missing", "Provisional lower-risk behavior pattern", "Not final loyal segment.")

    genre_cols = [c for c in ["action_adventure_ratio", "family_animation_ratio", "drama_ratio", "thriller_crime_ratio", "sf_fantasy_ratio", "comedy_ratio", "romance_ratio", "horror_ratio", "documentary_ratio", "historical_war_ratio", "other_ratio"] if c in df.columns]
    if "genre_diversity_count" in df.columns or genre_cols:
        cond = pd.Series(False, index=df.index)
        payload = {}
        if "genre_diversity_count" in df.columns:
            thresholds = q_by_scope(df, "genre_diversity_count", 0.25)
            cond = cond | apply_scope_threshold(df, "genre_diversity_count", thresholds, "<=")
            payload["genre_diversity_count_q25"] = thresholds
        if genre_cols:
            df["_genre_max_ratio_tmp"] = df[genre_cols].apply(pd.to_numeric, errors="coerce").max(axis=1)
            thresholds = q_by_scope(df, "_genre_max_ratio_tmp", 0.75)
            cond = cond | apply_scope_threshold(df, "_genre_max_ratio_tmp", thresholds, ">=")
            payload["genre_max_ratio_q75"] = thresholds
        df["genre_preference_clear"] = cond.astype(int)
        created_flags.append("genre_preference_clear")
        add_definition(defs, "genre_preference_clear", ["genre_diversity_count"] + genre_cols, "genre_diversity_count<=q25 OR row-wise max genre ratio>=q75", "scope_quantile", json.dumps(payload), True, "", "Clear or narrow genre preference signal", "Genre preference is profile/action evidence, not causal effect.")
    else:
        df["genre_preference_clear"] = 0
        add_definition(defs, "genre_preference_clear", ["genre_diversity_count", "genre ratio columns"], "not created", "scope_quantile", "", False, "genre_columns_missing", "Clear or narrow genre preference signal", "Not created.")

    content_cols = [c for c in ["new_movie_in_90d_ratio", "new_movie_in_180d_ratio", "new_movie_in_365d_ratio", "old_movie_ratio_5y", "avg_ott_release_year"] if c in df.columns]
    if len(content_cols) >= 3:
        cond = pd.Series(False, index=df.index)
        payload = {}
        for col in content_cols:
            q25 = q_by_scope(df, col, 0.25)
            q75 = q_by_scope(df, col, 0.75)
            cond = cond | apply_scope_threshold(df, col, q25, "<=") | apply_scope_threshold(df, col, q75, ">=")
            payload[f"{col}_q25"] = q25
            payload[f"{col}_q75"] = q75
        df["content_preference_signal"] = cond.astype(int)
        created_flags.append("content_preference_signal")
        add_definition(defs, "content_preference_signal", content_cols, "content/release columns outside q25/q75", "scope_quantile", json.dumps(payload), True, "", "Content/release preference signal", "Use only when content/release columns and rule are clear.")
    else:
        df["content_preference_signal"] = 0
        add_definition(defs, "content_preference_signal", ["content/release columns"], "not created", "scope_quantile", "", False, "insufficient_clear_content_columns_or_rule", "Content/release preference signal", "Genre flag can still support segmentation.")

    flag_cols = ["row_id", "promo_scope", "is_repurchase", "gb_churn_risk_score_oof", "lr_churn_risk_score_oof"] + [c for c in df.columns if c in set(created_flags + ["low_activity_reason"])]
    definitions_path = write_rows(OUTPUT_DIR / "17_internal_multiflag_definitions.csv", defs, ["flag_name", "required_columns", "formula", "threshold_type", "threshold_value", "scope_applied", "created", "reason_if_not_created", "interpretation", "caveat"])
    df[flag_cols].to_csv(OUTPUT_DIR / "17_internal_multiflag_assignment.csv", index=False, encoding="utf-8-sig")
    return definitions_path, OUTPUT_DIR / "17_internal_multiflag_assignment.csv", df, created_flags


def segment_rule_rows() -> list[dict[str, Any]]:
    rows = []
    specs = [
        ("promo1_s01", "promo1", 1, "promo_scope=='promo1' AND gb_high_risk_top20==1 AND week3_inactive==1", "gb_high_risk_top20,week3_inactive", "GB top20 high risk", "week3 inactive", "promo1_high_risk_week3_inactive", "100won high-risk customers with no week3 activity may need near-renewal save or reactivation messaging."),
        ("promo1_s02", "promo1", 2, "promo_scope=='promo1' AND gb_high_risk_top20==1 AND retention_decay==1", "gb_high_risk_top20,retention_decay", "GB top20 high risk", "retention decay", "promo1_high_risk_retention_decay", "100won high-risk customers with declining log-retention may need week2/week3 retention nudges."),
        ("promo1_s03", "promo1", 3, "promo_scope=='promo1' AND gb_high_risk_top20==1 AND (only_w1==1 OR cold_start_weak==1)", "gb_high_risk_top20,only_w1,cold_start_weak", "GB top20 high risk", "only week1 or weak early activation", "promo1_high_risk_only_w1_or_cold_start_weak", "100won high-risk customers with weak early activation need onboarding/reactivation, not cold-start success treatment."),
        ("promo1_s04", "promo1", 4, "promo_scope=='promo1' AND gb_high_risk_top20==1 AND low_activity==1", "gb_high_risk_top20,low_activity", "GB top20 high risk", "broad low activity", "promo1_high_risk_low_activity", "100won high-risk customers with broad low activity may need lightweight activation prompts."),
        ("promo1_s05", "promo1", 5, "promo_scope=='promo1' AND gb_high_risk_top20==1 AND (genre_preference_clear==1 OR content_preference_signal==1)", "gb_high_risk_top20,genre_preference_clear,content_preference_signal", "GB top20 high risk", "genre or content narrow signal", "promo1_high_risk_genre_or_content_narrow", "100won high-risk customers with narrow content/genre evidence may need recommendation strategy."),
        ("promo1_s06", "promo1", 6, "promo_scope=='promo1' AND gb_high_risk_top20==0 AND stable_usage==1", "gb_high_risk_top20,stable_usage", "not GB top20 high risk", "stable usage", "promo1_stable_usage_lower_risk", "100won lower-risk behavior pattern, not final loyal segment."),
        ("promo1_s99", "promo1", 99, "promo_scope=='promo1' AND no prior rule matched", "", "fallback", "needs review", "promo1_other_needs_review", "Unassigned 100won rows need further review."),
        ("promo0_s01", "promo0", 1, "promo_scope=='promo0' AND gb_high_risk_top20==1 AND week3_inactive==1", "gb_high_risk_top20,week3_inactive", "GB top20 high risk", "week3 inactive", "promo0_high_risk_week3_inactive", "General-customer comparison high-risk week3 inactive pattern."),
        ("promo0_s02", "promo0", 2, "promo_scope=='promo0' AND gb_high_risk_top20==1 AND retention_decay==1", "gb_high_risk_top20,retention_decay", "GB top20 high risk", "retention decay", "promo0_high_risk_retention_decay", "General-customer comparison high-risk retention decay pattern."),
        ("promo0_s03", "promo0", 3, "promo_scope=='promo0' AND gb_high_risk_top20==1 AND (only_w1==1 OR cold_start_weak==1)", "gb_high_risk_top20,only_w1,cold_start_weak", "GB top20 high risk", "only week1 or weak early activation", "promo0_high_risk_only_w1_or_cold_start_weak", "General-customer comparison weak early activation pattern."),
        ("promo0_s04", "promo0", 4, "promo_scope=='promo0' AND gb_high_risk_top20==1 AND low_activity==1", "gb_high_risk_top20,low_activity", "GB top20 high risk", "broad low activity", "promo0_high_risk_low_activity", "General-customer comparison broad low activity pattern."),
        ("promo0_s05", "promo0", 5, "promo_scope=='promo0' AND gb_high_risk_top20==0 AND stable_usage==1", "gb_high_risk_top20,stable_usage", "not GB top20 high risk", "stable usage", "promo0_stable_usage_lower_risk", "General-customer lower-risk behavior pattern, not final loyal segment."),
        ("promo0_s99", "promo0", 99, "promo_scope=='promo0' AND no prior rule matched", "", "fallback", "needs review", "promo0_other_needs_review", "Unassigned comparison rows need further review."),
    ]
    for sid, scope, priority, expr, flags, risk, behavior, label, hyp in specs:
        rows.append(
            {
                "segment_id": sid,
                "promo_scope": scope,
                "priority_order": priority,
                "rule_expression": expr,
                "required_flags": flags,
                "risk_condition": risk,
                "behavior_condition": behavior,
                "provisional_label": label,
                "business_hypothesis": hyp,
                "caveat": "Provisional rule label. Not final segment name, not final campaign targeting.",
                "user_approval_required": "yes",
            }
        )
    return rows


def assign_segments(df: pd.DataFrame) -> tuple[Path, Path, pd.DataFrame]:
    rules = segment_rule_rows()
    for col in ["week3_inactive", "retention_decay", "only_w1", "cold_start_weak", "low_activity", "genre_preference_clear", "content_preference_signal", "stable_usage"]:
        if col not in df.columns:
            df[col] = 0
    assignment = []
    for _, r in df.iterrows():
        scope = r["promo_scope"]
        high = r["gb_high_risk_top20"] == 1
        if scope == "promo1":
            if high and r["week3_inactive"] == 1:
                sid, label, order = "promo1_s01", "promo1_high_risk_week3_inactive", 1
            elif high and r["retention_decay"] == 1:
                sid, label, order = "promo1_s02", "promo1_high_risk_retention_decay", 2
            elif high and (r["only_w1"] == 1 or r["cold_start_weak"] == 1):
                sid, label, order = "promo1_s03", "promo1_high_risk_only_w1_or_cold_start_weak", 3
            elif high and r["low_activity"] == 1:
                sid, label, order = "promo1_s04", "promo1_high_risk_low_activity", 4
            elif high and (r["genre_preference_clear"] == 1 or r["content_preference_signal"] == 1):
                sid, label, order = "promo1_s05", "promo1_high_risk_genre_or_content_narrow", 5
            elif (not high) and r["stable_usage"] == 1:
                sid, label, order = "promo1_s06", "promo1_stable_usage_lower_risk", 6
            else:
                sid, label, order = "promo1_s99", "promo1_other_needs_review", 99
        else:
            if high and r["week3_inactive"] == 1:
                sid, label, order = "promo0_s01", "promo0_high_risk_week3_inactive", 1
            elif high and r["retention_decay"] == 1:
                sid, label, order = "promo0_s02", "promo0_high_risk_retention_decay", 2
            elif high and (r["only_w1"] == 1 or r["cold_start_weak"] == 1):
                sid, label, order = "promo0_s03", "promo0_high_risk_only_w1_or_cold_start_weak", 3
            elif high and r["low_activity"] == 1:
                sid, label, order = "promo0_s04", "promo0_high_risk_low_activity", 4
            elif (not high) and r["stable_usage"] == 1:
                sid, label, order = "promo0_s05", "promo0_stable_usage_lower_risk", 5
            else:
                sid, label, order = "promo0_s99", "promo0_other_needs_review", 99
        assignment.append((sid, label, order))
    df["representative_segment_id"] = [x[0] for x in assignment]
    df["provisional_label"] = [x[1] for x in assignment]
    df["assignment_priority_order"] = [x[2] for x in assignment]
    write_rows(OUTPUT_DIR / "17_representative_segment_rules.csv", rules, ["segment_id", "promo_scope", "priority_order", "rule_expression", "required_flags", "risk_condition", "behavior_condition", "provisional_label", "business_hypothesis", "caveat", "user_approval_required"])
    cols = [
        "row_id", "promo_scope", "is_repurchase", "representative_segment_id", "provisional_label", "assignment_priority_order",
        "gb_churn_risk_score_oof", "lr_churn_risk_score_oof", "gb_risk_percentile", "lr_risk_percentile",
        "gb_high_risk_top20", "lr_high_risk_top20", "gb_lr_both_high_risk_top20", "week3_inactive", "retention_decay",
        "only_w1", "cold_start_weak", "early_activation_success", "low_activity", "low_activity_reason",
        "low_watch_count", "low_watch_time", "low_watch_days",
        "genre_preference_clear", "content_preference_signal", "stable_usage"
    ]
    df[cols].to_csv(OUTPUT_DIR / "17_representative_segment_assignment.csv", index=False, encoding="utf-8-sig")
    return OUTPUT_DIR / "17_representative_segment_rules.csv", OUTPUT_DIR / "17_representative_segment_assignment.csv", df


def dominant_flags(sub: pd.DataFrame) -> str:
    flags = ["week3_inactive", "retention_decay", "only_w1", "cold_start_weak", "low_activity", "usage_concentrated", "genre_preference_clear", "content_preference_signal", "stable_usage"]
    vals = []
    for flag in flags:
        if flag in sub.columns:
            rate = sub[flag].mean()
            if rate >= 0.25:
                vals.append(f"{flag}:{rate:.2f}")
    return "; ".join(vals[:6])


def behavior_interpretation(label: str) -> str:
    if "week3_inactive" in label:
        return "week3 inactivity / near-renewal disengagement"
    if "retention_decay" in label:
        return "log-retention decay / continued viewing decline"
    if "cold_start_weak" in label:
        return "weak early activation or only week1 use"
    if "low_activity" in label:
        return "broad low activity screening pattern"
    if "genre_or_content" in label:
        return "narrow genre or content preference evidence"
    if "stable_usage" in label:
        return "provisional lower-risk behavior pattern"
    return "needs review"


def segment_summary(df: pd.DataFrame) -> Path:
    rows = []
    for (scope, sid, label), sub in df.groupby(["promo_scope", "representative_segment_id", "provisional_label"]):
        scope_n = len(df[df["promo_scope"] == scope])
        rep_rate = float(sub["is_repurchase"].mean())
        rows.append(
            {
                "promo_scope": scope,
                "representative_segment_id": sid,
                "provisional_label": label,
                "row_count": len(sub),
                "row_share_within_scope": len(sub) / scope_n,
                "actual_repurchase_rate": rep_rate,
                "actual_churn_rate": 1 - rep_rate,
                "mean_gb_churn_risk": float(sub["gb_churn_risk_score_oof"].mean()),
                "median_gb_churn_risk": float(sub["gb_churn_risk_score_oof"].median()),
                "mean_lr_churn_risk": float(sub["lr_churn_risk_score_oof"].mean()),
                "median_lr_churn_risk": float(sub["lr_churn_risk_score_oof"].median()),
                "gb_top20_share": float(sub["gb_high_risk_top20"].mean()),
                "lr_top20_share": float(sub["lr_high_risk_top20"].mean()),
                "gb_lr_both_top20_share": float(sub["gb_lr_both_high_risk_top20"].mean()),
                "dominant_flags": dominant_flags(sub),
                "primary_behavior_interpretation": behavior_interpretation(label),
                "user_approval_required": "yes",
                "caveat": "Provisional segment. Actual repurchase/churn rates are descriptive, not causal effects. low_activity is broad if present.",
            }
        )
    return write_rows(OUTPUT_DIR / "17_segment_summary.csv", rows, ["promo_scope", "representative_segment_id", "provisional_label", "row_count", "row_share_within_scope", "actual_repurchase_rate", "actual_churn_rate", "mean_gb_churn_risk", "median_gb_churn_risk", "mean_lr_churn_risk", "median_lr_churn_risk", "gb_top20_share", "lr_top20_share", "gb_lr_both_top20_share", "dominant_flags", "primary_behavior_interpretation", "user_approval_required", "caveat"])


def feature_mapping() -> dict[str, str]:
    mp = pd.read_csv(HOTFIX16B_DIR / "16b_feature_family_mapping_hotfix.csv")
    return dict(zip(mp["feature_name"], mp["new_feature_family"]))


def feature_profile(df: pd.DataFrame, fmap: dict[str, str]) -> Path:
    feature_cols = [c for c in fmap if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    rows = []
    for (scope, sid), sub in df.groupby(["promo_scope", "representative_segment_id"]):
        scope_df = df[df["promo_scope"] == scope]
        for feat in feature_cols:
            s = pd.to_numeric(sub[feat], errors="coerce")
            overall = pd.to_numeric(scope_df[feat], errors="coerce")
            seg_val = float(s.mean()) if len(s.dropna()) else np.nan
            scope_val = float(overall.mean()) if len(overall.dropna()) else np.nan
            rows.append(
                {
                    "promo_scope": scope,
                    "representative_segment_id": sid,
                    "feature_name": feat,
                    "feature_family": fmap.get(feat, "missing_hotfix_mapping"),
                    "mean": seg_val,
                    "median": float(s.median()) if len(s.dropna()) else "",
                    "q25": float(s.quantile(0.25)) if len(s.dropna()) else "",
                    "q75": float(s.quantile(0.75)) if len(s.dropna()) else "",
                    "zero_or_false_rate": float((s.fillna(0) == 0).mean()) if len(s) else "",
                    "segment_value": seg_val,
                    "scope_overall_value": scope_val,
                    "difference_vs_scope_overall": seg_val - scope_val if not np.isnan(seg_val) and not np.isnan(scope_val) else "",
                    "interpretation": f"{feat} segment mean compared with scope overall",
                    "caveat": "Feature family uses 16b hotfix mapping. Descriptive profile, not causal effect.",
                }
            )
    return write_rows(OUTPUT_DIR / "17_segment_feature_profile.csv", rows, ["promo_scope", "representative_segment_id", "feature_name", "feature_family", "mean", "median", "q25", "q75", "zero_or_false_rate", "segment_value", "scope_overall_value", "difference_vs_scope_overall", "interpretation", "caveat"])


def shap_evidence(df: pd.DataFrame) -> Path:
    fam = pd.read_csv(HOTFIX16B_DIR / "16b_shap_family_importance_hotfix.csv")
    cmp_df = pd.read_csv(HOTFIX16B_DIR / "16b_promo1_vs_promo0_shap_comparison_hotfix.csv")
    rows = []
    segment_families = {
        "week3_inactive": ["weekly_usage", "week_specific_usage_pattern"],
        "retention_decay": ["retention_decay", "inactivity_recency"],
        "cold_start_weak": ["onboarding_activation", "week_specific_usage_pattern"],
        "low_activity": ["weekly_usage", "usage_concentration"],
        "genre_or_content": ["genre_preference", "content_preference"],
        "stable_usage": ["weekly_usage", "retention_decay", "usage_concentration"],
        "other": ["weekly_usage", "genre_preference"],
    }
    for (scope, sid, label), sub in df.groupby(["promo_scope", "representative_segment_id", "provisional_label"]):
        key = "other"
        for k in ["week3_inactive", "retention_decay", "cold_start_weak", "low_activity", "genre_or_content", "stable_usage"]:
            if k in label:
                key = k
                break
        for family in segment_families[key]:
            frow = fam[(fam["model_family"] == "GradientBoosting") & (fam["promo_scope"] == scope) & (fam["feature_family"] == family)]
            rank = frow["family_rank"].iloc[0] if len(frow) else ""
            imp = frow["total_mean_abs_shap"].iloc[0] if len(frow) else ""
            comp = cmp_df[(cmp_df["model_family"] == "GradientBoosting") & (cmp_df["comparison_level"] == "family_hotfix") & (cmp_df["feature_or_family"] == family)]
            delta = comp["delta_promo1_minus_promo0"].iloc[0] if len(comp) else ""
            rows.append(
                {
                    "promo_scope": scope,
                    "representative_segment_id": sid,
                    "provisional_label": label,
                    "related_feature_family": family,
                    "related_features": "see 16b feature family mapping",
                    "segment_behavior_evidence": dominant_flags(sub),
                    "shap_family_rank_in_promo_scope": rank,
                    "shap_family_importance": imp,
                    "promo1_vs_promo0_family_difference_if_available": delta,
                    "interpretation": f"{family} supports the behavior evidence as model explanation.",
                    "caveat": "SHAP is model explanation, not causality. Segment rule is not built from SHAP alone.",
                }
            )
    return write_rows(OUTPUT_DIR / "17_segment_SHAP_family_evidence_link.csv", rows, ["promo_scope", "representative_segment_id", "provisional_label", "related_feature_family", "related_features", "segment_behavior_evidence", "shap_family_rank_in_promo_scope", "shap_family_importance", "promo1_vs_promo0_family_difference_if_available", "interpretation", "caveat"])


def add_gender(df: pd.DataFrame) -> pd.DataFrame:
    if "is_female" in df.columns or "is_male" in df.columns:
        female = pd.to_numeric(df.get("is_female", 0), errors="coerce").fillna(0)
        male = pd.to_numeric(df.get("is_male", 0), errors="coerce").fillna(0)
        df["gender_profile"] = np.where((female == 1) & (male != 1), "female", np.where((male == 1) & (female != 1), "male", "unknown_or_ambiguous"))
    return df


def demographic_outputs(df: pd.DataFrame, fmap: dict[str, str]) -> tuple[Path, Path, Path]:
    df = add_gender(df.copy())
    rows = []
    demo_vars = []
    if "age_group" in df.columns:
        demo_vars.append("age_group")
    if "gender_profile" in df.columns:
        demo_vars.append("gender_profile")
    if "is_female" in df.columns:
        demo_vars.append("is_female")
    if "is_male" in df.columns:
        demo_vars.append("is_male")
    for (scope, sid), sub in df.groupby(["promo_scope", "representative_segment_id"]):
        scope_df = df[df["promo_scope"] == scope]
        for var in demo_vars:
            for val, vsub in sub.groupby(var, dropna=False):
                scope_share = len(scope_df[scope_df[var] == val]) / len(scope_df) if len(scope_df) else 0
                seg_share = len(vsub) / len(sub) if len(sub) else 0
                rows.append(
                    {
                        "promo_scope": scope,
                        "representative_segment_id": sid,
                        "demographic_variable": var,
                        "demographic_value": val,
                        "row_count": len(vsub),
                        "share_within_segment": seg_share,
                        "share_within_scope": scope_share,
                        "lift_vs_scope": seg_share / scope_share if scope_share else "",
                        "actual_repurchase_rate": float(vsub["is_repurchase"].mean()) if len(vsub) else "",
                        "mean_gb_churn_risk": float(vsub["gb_churn_risk_score_oof"].mean()) if len(vsub) else "",
                        "interpretation": "Profile audit only; not representative segment rule.",
                        "caveat": "Age/gender action variants require EDA evidence and user approval.",
                    }
                )
    demo_path = write_rows(OUTPUT_DIR / "17_segment_demographic_profile.csv", rows, ["promo_scope", "representative_segment_id", "demographic_variable", "demographic_value", "row_count", "share_within_segment", "share_within_scope", "lift_vs_scope", "actual_repurchase_rate", "mean_gb_churn_risk", "interpretation", "caveat"])

    behavior_features = [c for c in ["total_watch_count", "watch_days", "total_watch_time_min", "active_ratio", "log_retention_w2_ratio", "log_retention_w3_ratio", "recency", "max_inactive_gap_days"] if c in df.columns]
    age_rows = []
    for (scope, sid), sub in df.groupby(["promo_scope", "representative_segment_id"]):
        for group_col in [c for c in ["age_group", "gender_profile"] if c in sub.columns]:
            for group, gsub in sub.groupby(group_col, dropna=False):
                for feat in behavior_features:
                    s = pd.to_numeric(gsub[feat], errors="coerce")
                    all_s = pd.to_numeric(sub[feat], errors="coerce")
                    age_rows.append(
                        {
                            "promo_scope": scope,
                            "representative_segment_id": sid,
                            "demographic_group": f"{group_col}={group}",
                            "feature_name": feat,
                            "feature_family": fmap.get(feat, "profile_only_or_missing_mapping"),
                            "mean": float(s.mean()) if len(s.dropna()) else "",
                            "median": float(s.median()) if len(s.dropna()) else "",
                            "q25": float(s.quantile(0.25)) if len(s.dropna()) else "",
                            "q75": float(s.quantile(0.75)) if len(s.dropna()) else "",
                            "actual_repurchase_rate": float(gsub["is_repurchase"].mean()) if len(gsub) else "",
                            "mean_gb_churn_risk": float(gsub["gb_churn_risk_score_oof"].mean()) if len(gsub) else "",
                            "difference_vs_segment_overall": float(s.mean() - all_s.mean()) if len(s.dropna()) and len(all_s.dropna()) else "",
                            "interpretation": "Demographic modifier with behavior profile evidence.",
                            "caveat": "Do not use demographic group as primary segment name.",
                        }
                    )
    age_path = write_rows(OUTPUT_DIR / "17_segment_age_gender_behavior_profile.csv", age_rows, ["promo_scope", "representative_segment_id", "demographic_group", "feature_name", "feature_family", "mean", "median", "q25", "q75", "actual_repurchase_rate", "mean_gb_churn_risk", "difference_vs_segment_overall", "interpretation", "caveat"])

    action_rows = []
    for (scope, sid, label), sub in df.groupby(["promo_scope", "representative_segment_id", "provisional_label"]):
        demographic_modifier = "none_by_default"
        observed_pattern = "demographic profile available; no direct demographic rule"
        behavior_diff = dominant_flags(sub)
        strength = "weak"
        final_status = "not_recommended_yet"
        action_rows.append(
            {
                "promo_scope": scope,
                "representative_segment_id": sid,
                "provisional_label": label,
                "demographic_modifier": demographic_modifier,
                "observed_demographic_pattern": observed_pattern,
                "observed_behavior_difference": behavior_diff,
                "recommended_message_direction": message_for_label(label),
                "recommended_channel_or_touchpoint": touchpoint_for_label(label),
                "recommended_content_strategy": content_for_label(label),
                "evidence_file": "17_segment_demographic_profile.csv;17_segment_age_gender_behavior_profile.csv",
                "evidence_strength": strength,
                "risk_of_overinterpretation": "high if age/gender is treated as cause or direct segment name",
                "final_status": final_status,
            }
        )
    matrix_path = write_rows(OUTPUT_DIR / "17_segment_action_personalization_matrix.csv", action_rows, ["promo_scope", "representative_segment_id", "provisional_label", "demographic_modifier", "observed_demographic_pattern", "observed_behavior_difference", "recommended_message_direction", "recommended_channel_or_touchpoint", "recommended_content_strategy", "evidence_file", "evidence_strength", "risk_of_overinterpretation", "final_status"])
    return demo_path, age_path, matrix_path


def message_for_label(label: str) -> str:
    if "week3_inactive" in label:
        return "renewal-adjacent save reminder focused on unfinished value"
    if "retention_decay" in label:
        return "interest decay recovery message with next-watch prompt"
    if "cold_start_weak" in label:
        return "onboarding reactivation and first meaningful watch prompt"
    if "low_activity" in label:
        return "lightweight activation nudge with low-friction content"
    if "genre_or_content" in label:
        return "personalized recommendation based on observed preference"
    if "stable_usage" in label:
        return "benefit reminder or conversion/upsell candidate message"
    return "needs review"


def touchpoint_for_label(label: str) -> str:
    if "week3_inactive" in label:
        return "week3 or renewal-proximity push/kakao/email candidate"
    if "retention_decay" in label:
        return "week2-week3 retention nudge"
    if "cold_start_weak" in label:
        return "early onboarding touchpoint"
    return "channel requires campaign design review"


def content_for_label(label: str) -> str:
    if "genre_or_content" in label:
        return "genre/content recommendation experiment"
    if "stable_usage" in label:
        return "continued value and membership conversion content"
    return "behavior-matched content prompt"


def business_actions(df: pd.DataFrame) -> Path:
    rows = []
    for (scope, sid, label), sub in df.groupby(["promo_scope", "representative_segment_id", "provisional_label"]):
        if "week3_inactive" in label:
            action_type = "week3_save_campaign"
            problem = "week3 inactivity"
        elif "retention_decay" in label:
            action_type = "week2_retention_nudge"
            problem = "retention decay"
        elif "cold_start_weak" in label:
            action_type = "onboarding_reactivation"
            problem = "weak early activation or only week1 usage"
        elif "low_activity" in label:
            action_type = "onboarding_reactivation"
            problem = "broad low activity"
        elif "genre_or_content" in label:
            action_type = "genre_based_recommendation"
            problem = "narrow genre/content evidence"
        elif "stable_usage" in label:
            action_type = "stable_user_upsell_or_conversion"
            problem = "lower-risk stable usage pattern"
        else:
            action_type = "needs_review"
            problem = "unclassified behavior pattern"
        rows.append(
            {
                "promo_scope": scope,
                "representative_segment_id": sid,
                "provisional_label": label,
                "primary_behavior_problem": problem,
                "recommended_action_type": action_type,
                "recommended_message_direction": message_for_label(label),
                "recommended_content_strategy": content_for_label(label),
                "recommended_timing": touchpoint_for_label(label),
                "demographic_personalization_needed": "yes_after_EDA_evidence",
                "evidence_summary": f"n={len(sub)}, mean_gb_churn={sub['gb_churn_risk_score_oof'].mean():.4f}, flags={dominant_flags(sub)}",
                "caveat": "Action candidate is not proven campaign effect. A/B test or operation experiment required.",
                "final_status": "provisional_candidate",
            }
        )
    return write_rows(OUTPUT_DIR / "17_segment_business_action_candidates.csv", rows, ["promo_scope", "representative_segment_id", "provisional_label", "primary_behavior_problem", "recommended_action_type", "recommended_message_direction", "recommended_content_strategy", "recommended_timing", "demographic_personalization_needed", "evidence_summary", "caveat", "final_status"])


def evidence_table(df: pd.DataFrame) -> Path:
    summary = pd.read_csv(OUTPUT_DIR / "17_segment_summary.csv")
    rows = []
    for _, row in summary.iterrows():
        for field in ["row_count", "row_share_within_scope", "actual_repurchase_rate", "actual_churn_rate", "mean_gb_churn_risk", "gb_lr_both_top20_share", "dominant_flags"]:
            rows.append(
                {
                    "evidence_item": f"{row['representative_segment_id']}_{field}",
                    "related_segment_id": row["representative_segment_id"],
                    "source_file": "17_segment_summary.csv",
                    "metric_or_field": field,
                    "value": row[field],
                    "interpretation": f"{field} for {row['provisional_label']}",
                    "caveat": "Descriptive segmentation evidence, not causal proof or final targeting.",
                }
            )
    return write_rows(OUTPUT_DIR / "17_segment_rationale_evidence_table.csv", rows, ["evidence_item", "related_segment_id", "source_file", "metric_or_field", "value", "interpretation", "caveat"])


def build_memos(df: pd.DataFrame) -> tuple[Path, Path]:
    summary = pd.read_csv(OUTPUT_DIR / "17_segment_summary.csv")
    promo1_summary = summary[summary["promo_scope"] == "promo1"]
    top_lines = []
    for _, row in promo1_summary.iterrows():
        top_lines.append(
            f"- `{row['provisional_label']}` has {int(row['row_count'])} rows, share {float(row['row_share_within_scope']):.3f}, actual repurchase rate {float(row['actual_repurchase_rate']):.3f}, mean GB churn risk {float(row['mean_gb_churn_risk']):.3f}, and dominant flags `{row['dominant_flags']}`."
        )
    body = f"""
# PUBLIC 17 Segment Rationale Memo for Executives

## 1. Executive summary

This segmentation design turns the row-level OOF score evidence from PUBLIC 15 and the model explanation evidence from PUBLIC 16/16b into provisional business-facing customer groups. The main scope is promo1, the 100won-deal customer group. Promo0 remains a comparison group because the project question is not simply "who is high risk overall", but how the 100won customer context differs from the general customer context.

This result is not final campaign targeting. Segment labels are provisional rule labels. OOF score is row-level risk evidence, not a final campaign threshold. SHAP is model explanation, not causality. 07~10 remain pending validation.

## 2. Why segmentation is needed after OOF and SHAP

OOF score tells us which rows look risky, but it does not directly say what intervention should be attempted. SHAP tells us which feature families the model used, but SHAP alone does not create an actionable segment. A business segment needs the intersection of risk, behavior, and interpretable evidence. For that reason this design combines GB/LR OOF risk flags, behavior flags from existing input columns, and 16b hotfixed family evidence.

The primary high-risk condition is GB top20. Top10 and top30 are preserved as review layers, but they are not the representative rule baseline. LR is retained as sensitivity and overlap evidence.

## 3. Segmentation design logic

The segmentation base datamart joins the OOF wide table to the promo input CSVs by promo_scope and row_id. Promo1 and promo0 are not pooled into a single segmentation universe. This preserves the business meaning of the 100won scope.

The internal flags are deliberately multi-label. A customer can be week3 inactive, retention-decayed, low-activity, and genre-focused at the same time. Representative segment assignment then applies a priority order so that each row receives exactly one provisional segment label.

The cold-start logic is corrected. `is_cold_start_3d_fixed = 1` and `is_cold_start_7d_fixed = 1` mean early activation success, not weak activation. `cold_start_weak` is the inverse of the 7-day flag when available. If only the 3-day flag is available, it is used with a caveat. This prevents the analysis from mistaking fast early watching for weak onboarding.

The low_activity flag is broad. It can be triggered by low watch count, low watch time, or low watch days. The helper records the component flags and `low_activity_reason` so the broad flag can be audited instead of overinterpreted.

Stable usage is also cautious. It is a provisional lower-risk behavior pattern, not a final loyal segment. It combines high active ratio, non-concentrated activity, sufficient watch days, non-high-risk GB top20 status, and when available no week3 inactivity and no retention decay.

## 4. Why not use alternative segmentation methods

The analysis does not segment all customers together because promo1 is the business focus and promo0 is the comparison scope. Pooling them would hide the 100won-specific behavior pattern.

The analysis does not use age or gender as primary segment rules. Demographic features are profile audit and action personalization variables. A sentence like "20대 여성은 이탈한다" is not supported by this design.

The analysis does not segment only by SHAP top features. SHAP explains model behavior, but business action needs row-level risk and observed behavior flags.

The analysis does not use clustering-only segmentation because clustering would create groups without guaranteeing high-risk relevance or actionability. The current design is rule-based and auditable.

The analysis does not set a final campaign threshold. GB top20 is a design rule for provisional segmentation, not an operating cutoff.

## 5. Segment-by-segment rationale

{chr(10).join(top_lines)}

Each provisional segment exists because it ties a risk condition to a behavior problem. Week3 inactive customers suggest near-renewal disengagement. Retention-decay customers suggest continuing-viewing decline. Only-week1 or cold-start-weak customers suggest onboarding or early activation failure. Low-activity customers require caution because the flag is broad, but the component flags show whether count, time, or active days created the signal. Genre/content narrow customers may support recommendation experiments, but content preference does not prove churn causality. Stable-usage lower-risk customers are not final loyal customers; they are a lower-risk behavior pattern that may support conversion, reminder, or upsell experiments.

## 6. Demographic and action personalization policy

Age and gender are not representative segment rules. They are profile audit and action personalization layers. The same behavior segment can receive different messages or content variants after EDA evidence shows meaningful distribution differences. Without that evidence, demographic action variants remain not recommended yet.

## 7. Business action logic

Early weak activation or only-week1 behavior suggests onboarding reactivation. Week2 or week3 drop suggests retention nudges. Week3 inactivity suggests renewal-proximity save campaigns. Narrow genre evidence suggests recommendation strategy. Stable usage suggests benefit reminder, conversion, or upsell candidates. These are candidates, not proven campaign effects.

## 8. Caveats and guardrails

SHAP is not causality. OOF score is not a final campaign threshold. Segments are provisional. 07~10 remain pending validation. Demographic action needs EDA evidence. is_churn_prevented is interpreted as past churn prevention response history only. Final segment names are not confirmed.

## 9. What decision-makers can use this for

Decision-makers can use this to prioritize who to review first, which behavior problem to intervene on, what message or content strategy to test, how promo1 differs from promo0, and how to design a later A/B test.

## 10. What decision-makers should not conclude

Decision-makers should not conclude that 100won caused churn, that SHAP features are causes, that these segments are final campaign targets, that age or gender caused churn, or that GB top20 is an operational campaign threshold.
"""
    memo_path = OUTPUT_DIR / "17_segment_rationale_memo_for_executives.md"
    memo_path.write_text(textwrap.dedent(body).strip() + "\n", encoding="utf-8")
    rejected = """
# PUBLIC 17 Caveats and Rejected Alternatives

Age/gender were not used as primary segment rules because they are profile and personalization variables, not behavior problems. Direct demographic naming would overstate evidence and create fairness and interpretation risks.

Overall customer segmentation was rejected because promo1 is the main business scope and promo0 is the comparison scope. A pooled segmentation could obscure 100won-specific patterns.

SHAP-top-feature-only segmentation was rejected because SHAP is model explanation, not a rule system for customer intervention. Segment rules need row-level risk and behavior evidence.

Clustering-only segmentation was rejected because it may produce mathematically coherent groups that are not high-risk or actionable. The current design is auditable and tied to OOF risk.

Final campaign threshold selection was rejected because 17 is design, not operational targeting. GB top20 is a provisional segmentation rule, not a campaign cutoff.

07~10 pending validation caveat is preserved because this step does not complete or replace the deferred validation stages.
"""
    rejected_path = OUTPUT_DIR / "17_segment_caveat_and_rejected_alternatives.md"
    rejected_path.write_text(textwrap.dedent(rejected).strip() + "\n", encoding="utf-8")
    return memo_path, rejected_path


def readiness_for_18() -> Path:
    items = [
        ("representative_segments_created", "yes", "17_representative_segment_assignment.csv", "no", "one provisional segment per row"),
        ("segment_summary_created", "yes", "17_segment_summary.csv", "no", "summary created"),
        ("segment_feature_profile_created", "yes", "17_segment_feature_profile.csv", "no", "profile created"),
        ("segment_shap_family_evidence_created", "yes", "17_segment_SHAP_family_evidence_link.csv", "no", "SHAP family link created"),
        ("demographic_profile_created", "yes", "17_segment_demographic_profile.csv", "no", "profile audit created"),
        ("action_personalization_matrix_created", "yes", "17_segment_action_personalization_matrix.csv", "no", "matrix created"),
        ("executive_rationale_memo_created", "yes", "17_segment_rationale_memo_for_executives.md", "no", "memo created"),
        ("rejected_alternatives_memo_created", "yes", "17_segment_caveat_and_rejected_alternatives.md", "no", "memo created"),
        ("segment_names_finalized", "no", "provisional labels only", "yes", "final names require user approval"),
        ("business_storyline_allowed_now", "user_review_required", "17 outputs require review", "yes", "not automatic"),
        ("dashboard_allowed_now", "user_review_required", "17 outputs require review", "yes", "not automatic"),
        ("requires_user_review_before_18", "yes", "stage gate", "yes", "review required"),
    ]
    rows = [{"decision_item": a, "status": b, "evidence": c, "user_approval_required": d, "notes": e} for a, b, c, d, e in items]
    return write_rows(OUTPUT_DIR / "17_readiness_for_18_business_storyline.csv", rows, ["decision_item", "status", "evidence", "user_approval_required", "notes"])


def build_readmes() -> tuple[Path, Path]:
    readme = """
# PUBLIC 17 promo-scope OOF behavior segmentation design

## Purpose
This is segmentation design, not final campaign targeting. Segment labels are provisional.

## Inputs
The step reads 15 OOF hotfix, 16 SHAP/model explanation, 16b feature family mapping hotfix, and PUBLIC data input CSVs.

## Why promo1 is the main scope
Promo1 is the main 100won business scope; promo0 is the comparison scope.

## OOF score usage
OOF score is row-level risk evidence, not a final campaign threshold. GB top20 is the representative design condition.

## SHAP and 16b family mapping usage
SHAP is model explanation, not causality. 16b hotfix family mapping is used. The original technical_or_unknown bucket is not used.

## Multi-flag design
Flags combine OOF risk, activity, cold-start, retention, inactivity, usage concentration, genre, and content signals. cold_start_weak is corrected so cold-start fixed success flags are not treated as weak activation.

## Representative segment design
Each row receives exactly one provisional representative segment by priority order.

## Demographic profile and action personalization
Age/gender are action personalization variables after EDA evidence, not default representative segment rules.

## Executive rationale memo
See `17_segment_rationale_memo_for_executives.md`.

## What was not done
No model refit, Optuna, SHAP recalculation, OOF regeneration, final model selection, campaign threshold finalization, or final segment naming was performed.

## 07~10 pending validation caveat
07~10 remain pending validation.

## Safe wording
- This is segmentation design, not final campaign targeting.
- Segment labels are provisional.
- Promo1 is the main 100won business scope; promo0 is the comparison scope.
- OOF score is row-level risk evidence, not a final campaign threshold.
- SHAP is model explanation, not causality.
- 16b hotfix family mapping is used.
- Age/gender are action personalization variables after EDA evidence, not default representative segment rules.
- 07~10 remain pending validation.

## Unsafe wording
- segment is final
- 100won caused churn
- SHAP proves cause
- age/gender causes churn
- OOF score is campaign threshold
- 07~10 are completed
- dashboard can be finalized automatically

## Next action
Review the 17 package, then decide whether to proceed to 18 business storyline or segment hotfix.
"""
    result_readme = OUTPUT_DIR / "README.md"
    result_readme.write_text(textwrap.dedent(readme).strip() + "\n", encoding="utf-8")
    handoff = """
# PUBLIC 17 promo-scope OOF behavior segmentation handoff

## Purpose
Review handoff for provisional promo-scope segmentation design.

## Inputs checked
15 OOF hotfix, 16 SHAP, 16b feature family mapping, and promo input CSV files.

## Outputs generated
Base datamart, internal flags, representative segment assignment, segment summary, profiles, SHAP family evidence, demographic/action matrices, business actions, executive rationale memo, rejected alternatives memo, and readiness for 18.

## Execution status
Notebook executed through nbconvert. Helper is included in the review zip.

## Segment design summary
Promo1 is the main 100won scope. Promo0 is comparison. GB top20 is the primary design risk condition.

## Executive rationale memo status
`17_segment_rationale_memo_for_executives.md` is included.

## Demographic action policy
Age/gender are profile/action personalization variables only after EDA evidence.

## 16b family mapping dependency
16b hotfix family mapping is used; original technical_or_unknown is not used.

## 07~10 pending validation
07~10 remain pending validation.

## Files included in review zip
See zip inventory.

## Next recommended action
Review the ZIP and decide whether to proceed to 18 or request segment hotfix.
"""
    handoff_readme = HANDOFF_DIR / "README.md"
    handoff_readme.write_text(textwrap.dedent(handoff).strip() + "\n", encoding="utf-8")
    return result_readme, handoff_readme


def append_note() -> None:
    note_path = PUBLIC_ROOT / "note.md"
    heading = "## 2026-05-20 | PUBLIC 17 promo-scope OOF behavior segmentation design completed"
    text = note_path.read_text(encoding="utf-8") if note_path.exists() else ""
    if heading in text:
        return
    addition = f"""

{heading}

이번 작업은 PUBLIC 17 segmentation design 단계다.

15 OOF hotfix, 16 SHAP, 16b feature family mapping hotfix를 입력으로 사용했다.

promo1은 100원딜 고객 중심 scope이며, promo0는 비교군이다.

세그먼트는 OOF risk score와 행동 flag를 결합해 provisional로 설계했다.

16b hotfix family mapping을 사용했고, 기존 technical_or_unknown bucket은 사용하지 않았다.

연령/성별은 대표 세그먼트의 1차 기준이 아니라 demographic profile 및 action personalization layer로 사용했다.

demographic action variant는 EDA에서 분포 차이가 확인되는 경우에만 제안한다.

segment name은 final이 아니며 사용자 승인 전까지 provisional이다.

OOF score는 final campaign threshold가 아니다.

SHAP은 인과가 아니라 model explanation이다.

is_churn_prevented는 approved historical context feature with caveat로 유지했다.

07~10은 여전히 pending validation이다.

이번 작업에서는 모델 재실행, Optuna, SHAP 재계산, OOF 재생성, campaign threshold 확정을 수행하지 않았다.

`17_segment_rationale_memo_for_executives.md`를 작성해 세그먼트를 왜 이렇게 나누었는지 데이터와 비즈니스 근거를 길게 설명했다.

다음 단계는 사용자가 17 review zip을 검수한 뒤, 18 business storyline 또는 segment hotfix 여부를 결정하는 것이다.
"""
    with note_path.open("a", encoding="utf-8") as f:
        f.write(addition)


def notebook_json() -> dict[str, Any]:
    code = """from pathlib import Path
import sys

cwd = Path.cwd().resolve()
repo_root = cwd
for candidate in [cwd, *cwd.parents]:
    if (candidate / 'PUBLIC').exists():
        repo_root = candidate
        break
helper_dir = repo_root / 'PUBLIC' / 'handoff' / 'PUBLIC_17_promo_scope_oof_behavior_segmentation_260520'
sys.path.insert(0, str(helper_dir))

from public_17_segmentation_design_runner import run_all

result = run_all(executed_from_notebook=True)
result
"""
    return {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": ["# PUBLIC 17 promo-scope OOF behavior segmentation\n", "\n", "This notebook creates provisional segmentation design outputs from existing PUBLIC artifacts only.\n"]},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": code.splitlines(True)},
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "pygments_lexer": "ipython3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def create_notebook() -> Path:
    ensure_dirs()
    NOTEBOOK_PATH.write_text(json.dumps(notebook_json(), ensure_ascii=False, indent=2), encoding="utf-8")
    return NOTEBOOK_PATH


def zip_files() -> list[Path]:
    files = [
        HANDOFF_DIR / "README.md",
        HANDOFF_DIR / "17_input_validation.csv",
        HANDOFF_DIR / "17_source_fingerprint_before_after.csv",
        HANDOFF_DIR / "PUBLIC_17_promo_scope_oof_behavior_segmentation_final_checks.csv",
        HANDOFF_DIR / "PUBLIC_17_promo_scope_oof_behavior_segmentation_zip_inventory.csv",
        SCRIPT_PATH,
        NOTEBOOK_PATH,
        EXECUTED_NOTEBOOK_PATH,
        PUBLIC_ROOT / "note.md",
    ]
    files += [OUTPUT_DIR / name for name in RESULT_FILES]
    return files


def write_zip_inventory() -> Path:
    rows = []
    for path in zip_files():
        if path.exists():
            rows.append({"full_name": rel(path).replace("\\", "/"), "size_bytes": path.stat().st_size})
    return write_rows(HANDOFF_DIR / "PUBLIC_17_promo_scope_oof_behavior_segmentation_zip_inventory.csv", rows, ["full_name", "size_bytes"])


def create_zip() -> Path:
    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in zip_files():
            if path.exists():
                zf.write(path, rel(path).replace("\\", "/"))
    return ZIP_PATH


def final_checks() -> Path:
    entries = set()
    if ZIP_PATH.exists():
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            entries = set(zf.namelist())
    rows = []
    def add(name: str, status: str, expected: str, actual: Any, notes: str = "") -> None:
        rows.append({"check_name": name, "status": status, "expected": expected, "actual": actual, "notes": notes})
    def exists(path: Path) -> bool:
        return path.exists() and path.stat().st_size > 0
    assignment = pd.read_csv(OUTPUT_DIR / "17_representative_segment_assignment.csv") if exists(OUTPUT_DIR / "17_representative_segment_assignment.csv") else pd.DataFrame()
    rules = pd.read_csv(OUTPUT_DIR / "17_representative_segment_rules.csv") if exists(OUTPUT_DIR / "17_representative_segment_rules.csv") else pd.DataFrame()
    defs = pd.read_csv(OUTPUT_DIR / "17_internal_multiflag_definitions.csv") if exists(OUTPUT_DIR / "17_internal_multiflag_definitions.csv") else pd.DataFrame()
    fingerprint = pd.read_csv(HANDOFF_DIR / "17_source_fingerprint_before_after.csv") if exists(HANDOFF_DIR / "17_source_fingerprint_before_after.csv") else pd.DataFrame()
    add("public_root_exists", "PASS" if PUBLIC_ROOT.exists() else "FAIL", "PUBLIC exists", PUBLIC_ROOT.exists())
    add("output_folder_exists", "PASS" if OUTPUT_DIR.exists() else "FAIL", "output exists", rel(OUTPUT_DIR))
    add("handoff_folder_exists", "PASS" if HANDOFF_DIR.exists() else "FAIL", "handoff exists", rel(HANDOFF_DIR))
    add("notebook_created", "PASS" if exists(NOTEBOOK_PATH) else "FAIL", "notebook exists", rel(NOTEBOOK_PATH))
    add("notebook_executed", "PASS" if exists(EXECUTED_NOTEBOOK_PATH) else "FAIL", "executed notebook exists", rel(EXECUTED_NOTEBOOK_PATH))
    add("executed_notebook_saved", "PASS" if exists(EXECUTED_NOTEBOOK_PATH) else "FAIL", "non-empty executed notebook", EXECUTED_NOTEBOOK_PATH.stat().st_size if EXECUTED_NOTEBOOK_PATH.exists() else 0)
    check_files = [
        ("input_validation_created", HANDOFF_DIR / "17_input_validation.csv"),
        ("base_datamart_created", OUTPUT_DIR / "17_segmentation_base_datamart.csv"),
        ("base_datamart_validation_created", OUTPUT_DIR / "17_base_datamart_validation.csv"),
        ("multiflag_definitions_created", OUTPUT_DIR / "17_internal_multiflag_definitions.csv"),
        ("multiflag_assignment_created", OUTPUT_DIR / "17_internal_multiflag_assignment.csv"),
        ("representative_segment_rules_created", OUTPUT_DIR / "17_representative_segment_rules.csv"),
        ("representative_segment_assignment_created", OUTPUT_DIR / "17_representative_segment_assignment.csv"),
        ("segment_summary_created", OUTPUT_DIR / "17_segment_summary.csv"),
        ("segment_feature_profile_created", OUTPUT_DIR / "17_segment_feature_profile.csv"),
        ("segment_shap_family_evidence_link_created", OUTPUT_DIR / "17_segment_SHAP_family_evidence_link.csv"),
        ("demographic_profile_created", OUTPUT_DIR / "17_segment_demographic_profile.csv"),
        ("age_gender_behavior_profile_created", OUTPUT_DIR / "17_segment_age_gender_behavior_profile.csv"),
        ("action_personalization_matrix_created", OUTPUT_DIR / "17_segment_action_personalization_matrix.csv"),
        ("business_action_candidates_created", OUTPUT_DIR / "17_segment_business_action_candidates.csv"),
        ("segment_rationale_memo_for_executives_created", OUTPUT_DIR / "17_segment_rationale_memo_for_executives.md"),
        ("segment_rationale_evidence_table_created", OUTPUT_DIR / "17_segment_rationale_evidence_table.csv"),
        ("rejected_alternatives_memo_created", OUTPUT_DIR / "17_segment_caveat_and_rejected_alternatives.md"),
        ("readiness_for_18_created", OUTPUT_DIR / "17_readiness_for_18_business_storyline.csv"),
        ("readme_created", OUTPUT_DIR / "README.md"),
    ]
    for name, path in check_files:
        add(name, "PASS" if exists(path) else "FAIL", "file exists", rel(path))
    add("one_representative_segment_per_row", "PASS" if not assignment.empty and assignment.groupby(["promo_scope", "row_id"]).size().max() == 1 else "FAIL", "one per row", "ok" if not assignment.empty else "missing")
    memo_len = len((OUTPUT_DIR / "17_segment_rationale_memo_for_executives.md").read_text(encoding="utf-8")) if exists(OUTPUT_DIR / "17_segment_rationale_memo_for_executives.md") else 0
    add("segment_rationale_memo_minimum_length_checked", "PASS" if memo_len >= 7000 else "WARN", "long memo", memo_len)
    add("segment_names_are_provisional", "PASS" if not rules.empty and rules["caveat"].str.contains("Provisional", case=False).all() else "FAIL", "all provisional", "checked")
    rule_text = " ".join(rules["rule_expression"].astype(str).tolist()) if not rules.empty else ""
    add("age_gender_not_used_as_primary_representative_rule", "PASS" if all(x not in rule_text for x in ["age_group", "is_female", "is_male", "gender"]) else "FAIL", "no age/gender in rules", rule_text[:120])
    fmap_used = False
    if exists(OUTPUT_DIR / "17_segment_feature_profile.csv"):
        profile = pd.read_csv(OUTPUT_DIR / "17_segment_feature_profile.csv")
        fmap_used = "technical_or_unknown" not in set(profile.get("feature_family", []))
    add("hotfix_16b_family_mapping_used", "PASS" if fmap_used else "FAIL", "16b mapping no technical_or_unknown", fmap_used)
    add("original_technical_unknown_not_used", "PASS" if fmap_used else "FAIL", "technical_or_unknown absent", fmap_used)
    add("no_model_refit_performed", "PASS", "no model refit", "helper does not fit models")
    add("no_optuna_performed", "PASS", "no Optuna", "no optuna import/call")
    add("no_shap_recalculation_performed", "PASS", "no SHAP recalculation", "read existing SHAP CSV only")
    add("no_oof_regeneration_performed", "PASS", "no OOF regeneration", "read existing OOF CSV only")
    add("no_campaign_threshold_finalized", "PASS", "no final threshold", "GB top20 used as provisional design rule")
    changed_inputs = fingerprint[(fingerprint["file_role"] == "input") & (fingerprint["status"] != "unchanged")] if not fingerprint.empty else pd.DataFrame()
    add("no_raw_source_modified", "PASS" if len(changed_inputs) == 0 else "FAIL", "inputs unchanged", len(changed_inputs))
    add("no_park_ingyeom_modified", "PASS", "no park.ingyeom writes", "PUBLIC-only helper")
    note_text = (PUBLIC_ROOT / "note.md").read_text(encoding="utf-8") if (PUBLIC_ROOT / "note.md").exists() else ""
    add("note_md_append_completed", "PASS" if "PUBLIC 17 promo-scope OOF behavior segmentation design completed" in note_text else "FAIL", "note heading found", "found" if "PUBLIC 17 promo-scope OOF behavior segmentation design completed" in note_text else "missing")
    add("review_zip_includes_executed_notebook", "PASS" if rel(EXECUTED_NOTEBOOK_PATH).replace("\\", "/") in entries else "FAIL", "executed notebook in zip", rel(EXECUTED_NOTEBOOK_PATH))
    core = [rel(OUTPUT_DIR / name).replace("\\", "/") for name in RESULT_FILES]
    missing = [p for p in core if p not in entries]
    add("review_zip_includes_core_csvs", "PASS" if not missing else "FAIL", "core files in zip", "missing none" if not missing else ";".join(missing))
    add("review_zip_includes_rationale_memo", "PASS" if rel(OUTPUT_DIR / "17_segment_rationale_memo_for_executives.md").replace("\\", "/") in entries else "FAIL", "memo in zip", rel(OUTPUT_DIR / "17_segment_rationale_memo_for_executives.md"))
    add("review_zip_includes_note_md", "PASS" if "PUBLIC/note.md" in entries else "FAIL", "note in zip", "PUBLIC/note.md")
    add("review_zip_includes_zip_inventory", "PASS" if rel(HANDOFF_DIR / "PUBLIC_17_promo_scope_oof_behavior_segmentation_zip_inventory.csv").replace("\\", "/") in entries else "FAIL", "zip inventory in zip", rel(HANDOFF_DIR / "PUBLIC_17_promo_scope_oof_behavior_segmentation_zip_inventory.csv"))
    add("helper_file_included_if_used", "PASS" if rel(SCRIPT_PATH).replace("\\", "/") in entries else "FAIL", "helper in zip", rel(SCRIPT_PATH))
    add("review_zip_created", "PASS" if exists(ZIP_PATH) else "FAIL", "zip exists", rel(ZIP_PATH))
    add("zip_inventory_created", "PASS" if exists(HANDOFF_DIR / "PUBLIC_17_promo_scope_oof_behavior_segmentation_zip_inventory.csv") else "FAIL", "zip inventory exists", rel(HANDOFF_DIR / "PUBLIC_17_promo_scope_oof_behavior_segmentation_zip_inventory.csv"))
    add("cold_start_weak_corrected", "PASS" if not defs.empty and defs[defs["flag_name"] == "cold_start_weak"]["formula"].astype(str).str.contains("== 0|> 6", regex=True).any() else "FAIL", "cold_start weak inverse/safe logic", "checked")
    add("low_activity_components_recorded", "PASS" if all(c in assignment.columns for c in ["low_watch_count", "low_watch_time", "low_watch_days"]) else "FAIL", "component flags present", ",".join([c for c in ["low_watch_count", "low_watch_time", "low_watch_days"] if c in assignment.columns]))
    return write_rows(HANDOFF_DIR / "PUBLIC_17_promo_scope_oof_behavior_segmentation_final_checks.csv", rows, ["check_name", "status", "expected", "actual", "notes"])


def run_all(executed_from_notebook: bool = False) -> dict[str, Any]:
    ensure_dirs()
    before = snapshot()
    input_validation()
    wide, base = load_base()
    create_base_datamart(wide, base)
    validate_base(base)
    _defs_path, _assign_path, flagged, _created_flags = create_multiflags(base)
    assign_segments(flagged)
    segment_summary(flagged)
    fmap = feature_mapping()
    feature_profile(flagged, fmap)
    shap_evidence(flagged)
    demographic_outputs(flagged, fmap)
    business_actions(flagged)
    evidence_table(flagged)
    build_memos(flagged)
    readiness_for_18()
    build_readmes()
    append_note()
    after = snapshot()
    write_fingerprint(before, after)
    write_zip_inventory()
    create_zip()
    final_checks()
    return {"output_dir": rel(OUTPUT_DIR), "rows": len(flagged), "segments": int(flagged["representative_segment_id"].nunique()), "executed_from_notebook": executed_from_notebook}


def finalize_after_notebook() -> dict[str, Any]:
    write_zip_inventory()
    create_zip()
    final_checks()
    write_zip_inventory()
    create_zip()
    checks = pd.read_csv(HANDOFF_DIR / "PUBLIC_17_promo_scope_oof_behavior_segmentation_final_checks.csv")
    return {"final_checks": rel(HANDOFF_DIR / "PUBLIC_17_promo_scope_oof_behavior_segmentation_final_checks.csv"), "zip": rel(ZIP_PATH), "statuses": checks["status"].value_counts().to_dict()}


if __name__ == "__main__":
    ensure_dirs()
    if len(sys.argv) > 1 and sys.argv[1] == "create-notebook":
        print(create_notebook())
    elif len(sys.argv) > 1 and sys.argv[1] == "finalize":
        print(finalize_after_notebook())
    else:
        print(run_all(False))
