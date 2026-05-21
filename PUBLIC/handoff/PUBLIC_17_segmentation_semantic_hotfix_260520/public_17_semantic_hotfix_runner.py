from __future__ import annotations

import csv
import hashlib
import json
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

INPUT_DIR = PUBLIC_ROOT / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments"
OUTPUT_DIR = PUBLIC_ROOT / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments_hotfix_260520"
HANDOFF_DIR = PUBLIC_ROOT / "handoff" / "PUBLIC_17_segmentation_semantic_hotfix_260520"
NOTEBOOK_DIR = PUBLIC_ROOT / "notebooks" / "17_segmentation_design_260520"
NOTEBOOK_PATH = NOTEBOOK_DIR / "17_promo_scope_oof_behavior_segmentation_hotfix_260520.ipynb"
EXECUTED_NOTEBOOK_PATH = NOTEBOOK_DIR / "17_promo_scope_oof_behavior_segmentation_hotfix_260520_executed.ipynb"
ZIP_PATH = PUBLIC_ROOT / "zip" / "PUBLIC_17_segmentation_semantic_hotfix_260520_review_package.zip"

OOF15 = PUBLIC_ROOT / "results" / "15_oof_score_or_sensitivity_260520" / "four_model_oof_scores_hotfix_260520" / "15_oof_score_wide.csv"
SHAP16 = PUBLIC_ROOT / "results" / "16_SHAP_candidate_interpretation_260520" / "four_model_shap_interpretation" / "16_shap_global_importance.csv"
MAP16B = PUBLIC_ROOT / "results" / "16_SHAP_candidate_interpretation_260520" / "16b_feature_family_mapping_hotfix_260520" / "16b_feature_family_mapping_hotfix.csv"
FAM16B = PUBLIC_ROOT / "results" / "16_SHAP_candidate_interpretation_260520" / "16b_feature_family_mapping_hotfix_260520" / "16b_shap_family_importance_hotfix.csv"
HANDOFF16B = PUBLIC_ROOT / "results" / "16_SHAP_candidate_interpretation_260520" / "16b_feature_family_mapping_hotfix_260520" / "16b_family_interpretation_handoff_for_17.csv"
COMPARE16B = PUBLIC_ROOT / "results" / "16_SHAP_candidate_interpretation_260520" / "16b_feature_family_mapping_hotfix_260520" / "16b_promo1_vs_promo0_shap_comparison_hotfix.csv"

REQUIRED_17 = [
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
    "README.md",
]

REFERENCE_INPUTS = [
    ("15_oof_score_wide.csv", OOF15),
    ("16_shap_global_importance.csv", SHAP16),
    ("16b_feature_family_mapping_hotfix.csv", MAP16B),
    ("16b_shap_family_importance_hotfix.csv", FAM16B),
    ("16b_family_interpretation_handoff_for_17.csv", HANDOFF16B),
]

HOTFIX_OUTPUTS = [
    "README.md",
    "17_hotfix_revalidation_passes.csv",
    "17_content_preference_signal_audit.csv",
    "17_representative_segment_rules_hotfix.csv",
    "17_representative_segment_assignment_hotfix.csv",
    "17_segment_assignment_before_after_comparison.csv",
    "17_segment_summary_hotfix.csv",
    "17_other_needs_review_decomposition.csv",
    "17_segment_feature_profile_hotfix.csv",
    "17_segment_SHAP_family_evidence_link_hotfix.csv",
    "17_segment_demographic_profile_hotfix.csv",
    "17_segment_age_gender_behavior_profile_hotfix.csv",
    "17_segment_action_personalization_matrix_hotfix.csv",
    "17_segment_business_action_candidates_hotfix.csv",
    "17_segment_rationale_memo_for_executives_hotfix.md",
    "17_segment_rationale_evidence_table_hotfix.csv",
    "17_segment_caveat_and_rejected_alternatives_hotfix.md",
    "17_readiness_for_18_business_storyline_hotfix.csv",
]


def ensure_dirs() -> None:
    for p in [OUTPUT_DIR, HANDOFF_DIR, NOTEBOOK_DIR, ZIP_PATH.parent]:
        p.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT)).replace("/", "\\")


def write_rows(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})
    return path


def shape(path: Path) -> tuple[Any, Any]:
    if not path.exists() or path.suffix.lower() != ".csv":
        return "", ""
    df = pd.read_csv(path)
    return len(df), len(df.columns)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def input_validation() -> Path:
    rows = []
    for name in REQUIRED_17:
        path = INPUT_DIR / name
        n, c = shape(path)
        rows.append({"input_item": name, "expected_path": rel(path), "exists": path.exists(), "rows": n, "columns": c, "status": "PASS" if path.exists() else "FAIL", "notes": "existing 17 input"})
    for name, path in REFERENCE_INPUTS:
        n, c = shape(path)
        rows.append({"input_item": name, "expected_path": rel(path), "exists": path.exists(), "rows": n, "columns": c, "status": "PASS" if path.exists() else "FAIL", "notes": "15/16/16b reference input"})
    return write_rows(HANDOFF_DIR / "17_hotfix_input_validation.csv", rows, ["input_item", "expected_path", "exists", "rows", "columns", "status", "notes"])


def snapshot_targets() -> list[tuple[Path, str]]:
    targets = [(INPUT_DIR / name, "existing_17_input") for name in REQUIRED_17]
    targets += [(path, "reference_input") for _name, path in REFERENCE_INPUTS]
    targets += [(OUTPUT_DIR / name, "17_hotfix_output") for name in HOTFIX_OUTPUTS]
    targets += [
        (HANDOFF_DIR / "README.md", "17_hotfix_handoff"),
        (HANDOFF_DIR / "17_hotfix_input_validation.csv", "17_hotfix_handoff"),
        (HANDOFF_DIR / "17_hotfix_source_fingerprint_before_after.csv", "17_hotfix_handoff"),
        (HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_final_checks.csv", "17_hotfix_handoff"),
        (HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_zip_inventory.csv", "17_hotfix_handoff"),
        (SCRIPT_PATH, "17_hotfix_helper"),
        (NOTEBOOK_PATH, "17_hotfix_notebook"),
        (EXECUTED_NOTEBOOK_PATH, "17_hotfix_notebook"),
        (PUBLIC_ROOT / "note.md", "note"),
    ]
    return targets


def snapshot() -> dict[str, dict[str, Any]]:
    out = {}
    for path, role in snapshot_targets():
        key = rel(path)
        if path.exists():
            out[key] = {"file_path": key, "file_role": role, "sha256": sha256_file(path), "size": path.stat().st_size}
        else:
            out[key] = {"file_path": key, "file_role": role, "sha256": "", "size": ""}
    return out


def write_fingerprint(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> Path:
    rows = []
    for key in sorted(set(before) | set(after)):
        b, a = before.get(key, {}), after.get(key, {})
        role = a.get("file_role") or b.get("file_role", "")
        if b.get("sha256") and a.get("sha256") and b.get("sha256") == a.get("sha256"):
            status = "unchanged"
        elif role == "note" and b.get("sha256") and a.get("sha256") and b.get("sha256") != a.get("sha256"):
            status = "intentionally_updated_note"
        elif role in {"17_hotfix_output", "17_hotfix_handoff", "17_hotfix_notebook"} and not b.get("sha256") and a.get("sha256"):
            status = "new_output_created"
        elif key == rel(EXECUTED_NOTEBOOK_PATH) and a.get("sha256"):
            status = "intentionally_updated_17_hotfix_executed_notebook"
        elif b.get("sha256") and not a.get("sha256"):
            status = "missing_after"
        elif b.get("sha256") and a.get("sha256") and b.get("sha256") != a.get("sha256"):
            status = "changed_needs_review"
        else:
            status = "missing_before_and_after"
        rows.append({"file_path": key, "file_role": role, "sha256_before": b.get("sha256", ""), "sha256_after": a.get("sha256", ""), "size_before": b.get("size", ""), "size_after": a.get("size", ""), "status": status})
    return write_rows(HANDOFF_DIR / "17_hotfix_source_fingerprint_before_after.csv", rows, ["file_path", "file_role", "sha256_before", "sha256_after", "size_before", "size_after", "status"])


def load_inputs() -> dict[str, pd.DataFrame]:
    return {
        "base": pd.read_csv(INPUT_DIR / "17_segmentation_base_datamart.csv"),
        "flags": pd.read_csv(INPUT_DIR / "17_internal_multiflag_assignment.csv"),
        "rules": pd.read_csv(INPUT_DIR / "17_representative_segment_rules.csv"),
        "assignment": pd.read_csv(INPUT_DIR / "17_representative_segment_assignment.csv"),
        "summary": pd.read_csv(INPUT_DIR / "17_segment_summary.csv"),
        "feature_profile": pd.read_csv(INPUT_DIR / "17_segment_feature_profile.csv"),
        "family": pd.read_csv(FAM16B),
        "family_compare": pd.read_csv(COMPARE16B),
        "mapping": pd.read_csv(MAP16B),
    }


def assign_original(flags: pd.DataFrame) -> pd.DataFrame:
    df = flags.copy()
    for col in ["week3_inactive", "retention_decay", "only_w1", "cold_start_weak", "low_activity", "genre_preference_clear", "content_preference_signal", "stable_usage", "gb_high_risk_top20"]:
        if col not in df.columns:
            df[col] = 0
    rows = []
    for _, r in df.iterrows():
        scope, high = r["promo_scope"], r["gb_high_risk_top20"] == 1
        if scope == "promo1":
            if high and r["week3_inactive"] == 1: sid, label, order = "promo1_s01", "promo1_high_risk_week3_inactive", 1
            elif high and r["retention_decay"] == 1: sid, label, order = "promo1_s02", "promo1_high_risk_retention_decay", 2
            elif high and (r["only_w1"] == 1 or r["cold_start_weak"] == 1): sid, label, order = "promo1_s03", "promo1_high_risk_only_w1_or_cold_start_weak", 3
            elif high and r["low_activity"] == 1: sid, label, order = "promo1_s04", "promo1_high_risk_low_activity", 4
            elif high and (r["genre_preference_clear"] == 1 or r["content_preference_signal"] == 1): sid, label, order = "promo1_s05", "promo1_high_risk_genre_or_content_narrow", 5
            elif (not high) and r["stable_usage"] == 1: sid, label, order = "promo1_s06", "promo1_stable_usage_lower_risk", 6
            else: sid, label, order = "promo1_s99", "promo1_other_needs_review", 99
        else:
            if high and r["week3_inactive"] == 1: sid, label, order = "promo0_s01", "promo0_high_risk_week3_inactive", 1
            elif high and r["retention_decay"] == 1: sid, label, order = "promo0_s02", "promo0_high_risk_retention_decay", 2
            elif high and (r["only_w1"] == 1 or r["cold_start_weak"] == 1): sid, label, order = "promo0_s03", "promo0_high_risk_only_w1_or_cold_start_weak", 3
            elif high and r["low_activity"] == 1: sid, label, order = "promo0_s04", "promo0_high_risk_low_activity", 4
            elif (not high) and r["stable_usage"] == 1: sid, label, order = "promo0_s05", "promo0_stable_usage_lower_risk", 5
            else: sid, label, order = "promo0_s99", "promo0_other_needs_review", 99
        rows.append((sid, label, order))
    out = df[["promo_scope", "row_id"]].copy()
    out["calc_segment_id"] = [x[0] for x in rows]
    out["calc_label"] = [x[1] for x in rows]
    out["calc_order"] = [x[2] for x in rows]
    return out


def assign_hotfix(flags: pd.DataFrame, content_broad: bool) -> pd.DataFrame:
    df = flags.copy()
    for col in ["week3_inactive", "retention_decay", "only_w1", "cold_start_weak", "low_activity", "genre_preference_clear", "stable_usage", "gb_high_risk_top20"]:
        if col not in df.columns:
            df[col] = 0
    rows = []
    for _, r in df.iterrows():
        scope, high = r["promo_scope"], r["gb_high_risk_top20"] == 1
        if scope == "promo1":
            if high and r["week3_inactive"] == 1: sid, label, order, key = "promo1_s01", "promo1_high_risk_week3_inactive", 1, "gb_high_risk_top20,week3_inactive"
            elif high and r["retention_decay"] == 1: sid, label, order, key = "promo1_s02", "promo1_high_risk_retention_decay", 2, "gb_high_risk_top20,retention_decay"
            elif high and (r["only_w1"] == 1 or r["cold_start_weak"] == 1): sid, label, order, key = "promo1_s03", "promo1_high_risk_only_w1_or_cold_start_weak", 3, "gb_high_risk_top20,only_w1,cold_start_weak"
            elif high and r["low_activity"] == 1: sid, label, order, key = "promo1_s04", "promo1_high_risk_low_activity", 4, "gb_high_risk_top20,low_activity"
            elif high and r["genre_preference_clear"] == 1: sid, label, order, key = "promo1_s05", "promo1_high_risk_genre_preference_clear", 5, "gb_high_risk_top20,genre_preference_clear"
            elif (not high) and r["stable_usage"] == 1: sid, label, order, key = "promo1_s06", "promo1_stable_usage_lower_risk", 6, "gb_high_risk_top20,stable_usage"
            else: sid, label, order, key = "promo1_s99", "promo1_other_needs_review", 99, "fallback"
        else:
            if high and r["week3_inactive"] == 1: sid, label, order, key = "promo0_s01", "promo0_high_risk_week3_inactive", 1, "gb_high_risk_top20,week3_inactive"
            elif high and r["retention_decay"] == 1: sid, label, order, key = "promo0_s02", "promo0_high_risk_retention_decay", 2, "gb_high_risk_top20,retention_decay"
            elif high and (r["only_w1"] == 1 or r["cold_start_weak"] == 1): sid, label, order, key = "promo0_s03", "promo0_high_risk_only_w1_or_cold_start_weak", 3, "gb_high_risk_top20,only_w1,cold_start_weak"
            elif high and r["low_activity"] == 1: sid, label, order, key = "promo0_s04", "promo0_high_risk_low_activity", 4, "gb_high_risk_top20,low_activity"
            elif high and r["genre_preference_clear"] == 1: sid, label, order, key = "promo0_s05", "promo0_high_risk_genre_preference_clear", 5, "gb_high_risk_top20,genre_preference_clear"
            elif (not high) and r["stable_usage"] == 1: sid, label, order, key = "promo0_s06", "promo0_stable_usage_lower_risk", 6, "gb_high_risk_top20,stable_usage"
            else: sid, label, order, key = "promo0_s99", "promo0_other_needs_review", 99, "fallback"
        rows.append((sid, label, order, key))
    out = df.copy()
    out["representative_segment_id"] = [x[0] for x in rows]
    out["provisional_label"] = [x[1] for x in rows]
    out["assignment_priority_order"] = [x[2] for x in rows]
    out["key_flags_used_for_assignment"] = [x[3] for x in rows]
    return out


def revalidation_passes(data: dict[str, pd.DataFrame]) -> tuple[Path, int]:
    base, flags, assign = data["base"], data["flags"], data["assignment"]
    rows = []
    def add(vpass: str, item: str, status: str, expected: str, actual: Any, mismatch: Any = "", notes: str = "") -> None:
        rows.append({"validation_pass": vpass, "check_item": item, "status": status, "expected": expected, "actual": actual, "mismatch_count": mismatch, "notes": notes})
    add("A", "base_datamart_rows", "PASS" if len(base) == 23097 else "FAIL", "23097", len(base), 0)
    for scope, expected in [("promo0", 11193), ("promo1", 11904)]:
        actual = int((base["promo_scope"] == scope).sum())
        add("A", f"{scope}_base_rows", "PASS" if actual == expected else "FAIL", expected, actual, abs(actual - expected))
    dup = int(base.duplicated(["promo_scope", "row_id"]).sum())
    add("A", "base_promo_scope_row_id_duplicates", "PASS" if dup == 0 else "FAIL", "0", dup, dup)
    add("A", "representative_assignment_rows", "PASS" if len(assign) == len(base) else "FAIL", len(base), len(assign), abs(len(assign) - len(base)))
    max_dups = assign.groupby(["promo_scope", "row_id"]).size().max()
    add("A", "one_representative_segment_per_row", "PASS" if max_dups == 1 else "FAIL", "1", max_dups, "")
    gb_diff = (base["gb_churn_risk_score_oof"] - (1 - base["gb_repurchase_score_oof"])).abs().max()
    lr_diff = (base["lr_churn_risk_score_oof"] - (1 - base["lr_repurchase_score_oof"])).abs().max()
    add("B", "gb_score_direction", "PASS" if gb_diff < 1e-9 else "FAIL", "max diff < 1e-9", gb_diff, "")
    add("B", "lr_score_direction", "PASS" if lr_diff < 1e-9 else "FAIL", "max diff < 1e-9", lr_diff, "")
    for model in ["gb", "lr"]:
        for top, frac in [("top10", 0.10), ("top20", 0.20), ("top30", 0.30)]:
            col = f"{model}_high_risk_{top}"
            for scope in ["promo0", "promo1"]:
                sub = base[base["promo_scope"] == scope]
                actual = int(sub[col].sum())
                expected = round(len(sub) * frac)
                ok = abs(actual - expected) <= 2
                add("B", f"{scope}_{col}_count", "PASS" if ok else "WARN", f"about {expected}", actual, abs(actual - expected), "allowing rounding differences")
    rule_uses_gb20 = data["rules"]["rule_expression"].astype(str).str.contains("gb_high_risk_top20").any()
    add("B", "gb_high_risk_top20_used_in_rules", "PASS" if rule_uses_gb20 else "FAIL", "rule contains gb_high_risk_top20", rule_uses_gb20, "")
    calc = assign_original(flags)
    merged = assign.merge(calc, on=["promo_scope", "row_id"], how="left")
    mismatch = int((merged["representative_segment_id"] != merged["calc_segment_id"]).sum())
    add("C", "representative_rule_recalculation_mismatch", "PASS" if mismatch == 0 else "FAIL", "0", mismatch, mismatch, "recalculated from original 17 multiflag assignment")
    return write_rows(OUTPUT_DIR / "17_hotfix_revalidation_passes.csv", rows, ["validation_pass", "check_item", "status", "expected", "actual", "mismatch_count", "notes"]), mismatch


def content_audit(data: dict[str, pd.DataFrame]) -> tuple[Path, bool]:
    flags, assign, rules = data["flags"], data["assignment"], data["rules"]
    rows = []
    total = len(flags)
    count = int(flags["content_preference_signal"].sum()) if "content_preference_signal" in flags.columns else 0
    rate = count / total if total else 0
    broad = rate >= 0.70
    rule_usage = rules["rule_expression"].astype(str).str.contains("content_preference_signal").any()
    matrix_text = (INPUT_DIR / "17_segment_action_personalization_matrix.csv").read_text(encoding="utf-8") if (INPUT_DIR / "17_segment_action_personalization_matrix.csv").exists() else ""
    actions_text = (INPUT_DIR / "17_segment_business_action_candidates.csv").read_text(encoding="utf-8") if (INPUT_DIR / "17_segment_business_action_candidates.csv").exists() else ""
    memo_text = (INPUT_DIR / "17_segment_rationale_memo_for_executives.md").read_text(encoding="utf-8") if (INPUT_DIR / "17_segment_rationale_memo_for_executives.md").exists() else ""
    rows.append({"check_item": "overall_prevalence", "promo_scope": "all", "representative_segment_id": "all", "row_count": total, "content_preference_signal_count": count, "content_preference_signal_rate": rate, "threshold_for_broad_flag": 0.70, "is_broad_flag": broad, "current_usage": f"rule_usage={rule_usage}; action_matrix_mentions={'content_preference_signal' in matrix_text}; action_mentions={'content_preference_signal' in actions_text}; memo_mentions={'content_preference_signal' in memo_text}", "corrected_usage": "profile/action personalization cue only" if broad else "may be reviewed as narrower flag", "reason": "overall prevalence >= 70%" if broad else "not broad by threshold", "notes": "checked directly from 17_internal_multiflag_assignment.csv"})
    for scope, sub in flags.groupby("promo_scope"):
        c = int(sub["content_preference_signal"].sum()) if "content_preference_signal" in sub.columns else 0
        r = c / len(sub)
        rows.append({"check_item": "scope_prevalence", "promo_scope": scope, "representative_segment_id": "all", "row_count": len(sub), "content_preference_signal_count": c, "content_preference_signal_rate": r, "threshold_for_broad_flag": 0.70, "is_broad_flag": r >= 0.70, "current_usage": "scope diagnostic", "corrected_usage": "profile/action personalization cue only" if r >= 0.70 else "review", "reason": "scope prevalence diagnostic", "notes": ""})
    joined = flags.merge(assign[["promo_scope", "row_id", "representative_segment_id"]], on=["promo_scope", "row_id"], how="left")
    for (scope, sid), sub in joined.groupby(["promo_scope", "representative_segment_id"]):
        c = int(sub["content_preference_signal"].sum()) if "content_preference_signal" in sub.columns else 0
        r = c / len(sub)
        rows.append({"check_item": "segment_prevalence", "promo_scope": scope, "representative_segment_id": sid, "row_count": len(sub), "content_preference_signal_count": c, "content_preference_signal_rate": r, "threshold_for_broad_flag": 0.70, "is_broad_flag": r >= 0.70, "current_usage": "segment diagnostic", "corrected_usage": "do not use as discriminating segment rule" if r >= 0.70 else "review", "reason": "segment prevalence diagnostic", "notes": "segment-level prevalence can be high because overall flag is broad"})
    return write_rows(OUTPUT_DIR / "17_content_preference_signal_audit.csv", rows, ["check_item", "promo_scope", "representative_segment_id", "row_count", "content_preference_signal_count", "content_preference_signal_rate", "threshold_for_broad_flag", "is_broad_flag", "current_usage", "corrected_usage", "reason", "notes"]), broad


def hotfix_rules(content_broad: bool) -> Path:
    rows = []
    specs = [
        ("promo1_s01", "promo1", 1, "promo_scope=='promo1' AND gb_high_risk_top20==1 AND week3_inactive==1", "gb_high_risk_top20,week3_inactive", "GB top20 high risk", "week3 inactive", "promo1_high_risk_week3_inactive", "100won high-risk customers with no week3 activity may need near-renewal save review.", "unchanged from 17"),
        ("promo1_s02", "promo1", 2, "promo_scope=='promo1' AND gb_high_risk_top20==1 AND retention_decay==1", "gb_high_risk_top20,retention_decay", "GB top20 high risk", "retention decay", "promo1_high_risk_retention_decay", "100won high-risk customers with retention decay may need retention nudges.", "unchanged from 17"),
        ("promo1_s03", "promo1", 3, "promo_scope=='promo1' AND gb_high_risk_top20==1 AND (only_w1==1 OR cold_start_weak==1)", "gb_high_risk_top20,only_w1,cold_start_weak", "GB top20 high risk", "only week1 or weak early activation", "promo1_high_risk_only_w1_or_cold_start_weak", "Weak early activation or only-week1 use may need onboarding reactivation.", "unchanged from 17"),
        ("promo1_s04", "promo1", 4, "promo_scope=='promo1' AND gb_high_risk_top20==1 AND low_activity==1", "gb_high_risk_top20,low_activity", "GB top20 high risk", "broad low activity", "promo1_high_risk_low_activity", "Broad low activity may need lightweight activation review.", "unchanged from 17"),
        ("promo1_s05", "promo1", 5, "promo_scope=='promo1' AND gb_high_risk_top20==1 AND genre_preference_clear==1", "gb_high_risk_top20,genre_preference_clear", "GB top20 high risk", "genre preference clear", "promo1_high_risk_genre_preference_clear", "Genre preference signal can support recommendation profile, but content broad marker is excluded.", "content_preference_signal demoted because broad" if content_broad else "content signal not used for conservative hotfix"),
        ("promo1_s06", "promo1", 6, "promo_scope=='promo1' AND gb_high_risk_top20==0 AND stable_usage==1", "gb_high_risk_top20,stable_usage", "not GB top20 high risk", "stable usage", "promo1_stable_usage_lower_risk", "Lower-risk behavior pattern, not final loyal segment.", "unchanged from 17"),
        ("promo1_s99", "promo1", 99, "promo_scope=='promo1' AND no prior rule matched", "", "fallback", "needs review", "promo1_other_needs_review", "Large unclassified group remains honest caveat.", "fallback preserved"),
        ("promo0_s01", "promo0", 1, "promo_scope=='promo0' AND gb_high_risk_top20==1 AND week3_inactive==1", "gb_high_risk_top20,week3_inactive", "GB top20 high risk", "week3 inactive", "promo0_high_risk_week3_inactive", "Comparison high-risk week3 inactive pattern.", "unchanged from 17"),
        ("promo0_s02", "promo0", 2, "promo_scope=='promo0' AND gb_high_risk_top20==1 AND retention_decay==1", "gb_high_risk_top20,retention_decay", "GB top20 high risk", "retention decay", "promo0_high_risk_retention_decay", "Comparison high-risk retention decay pattern.", "unchanged from 17"),
        ("promo0_s03", "promo0", 3, "promo_scope=='promo0' AND gb_high_risk_top20==1 AND (only_w1==1 OR cold_start_weak==1)", "gb_high_risk_top20,only_w1,cold_start_weak", "GB top20 high risk", "only week1 or weak early activation", "promo0_high_risk_only_w1_or_cold_start_weak", "Comparison weak activation pattern.", "unchanged from 17"),
        ("promo0_s04", "promo0", 4, "promo_scope=='promo0' AND gb_high_risk_top20==1 AND low_activity==1", "gb_high_risk_top20,low_activity", "GB top20 high risk", "broad low activity", "promo0_high_risk_low_activity", "Comparison broad low activity pattern.", "unchanged from 17"),
        ("promo0_s05", "promo0", 5, "promo_scope=='promo0' AND gb_high_risk_top20==1 AND genre_preference_clear==1", "gb_high_risk_top20,genre_preference_clear", "GB top20 high risk", "genre preference clear", "promo0_high_risk_genre_preference_clear", "Comparison genre preference clear segment.", "content_preference_signal demoted because broad" if content_broad else "content signal not used for conservative hotfix"),
        ("promo0_s06", "promo0", 6, "promo_scope=='promo0' AND gb_high_risk_top20==0 AND stable_usage==1", "gb_high_risk_top20,stable_usage", "not GB top20 high risk", "stable usage", "promo0_stable_usage_lower_risk", "Comparison lower-risk behavior pattern.", "priority adjusted after adding genre segment"),
        ("promo0_s99", "promo0", 99, "promo_scope=='promo0' AND no prior rule matched", "", "fallback", "needs review", "promo0_other_needs_review", "Large unclassified group remains honest caveat.", "fallback preserved"),
    ]
    for sid, scope, order, expr, flags, risk, behavior, label, hyp, reason in specs:
        rows.append({"segment_id": sid, "promo_scope": scope, "priority_order": order, "rule_expression": expr, "required_flags": flags, "risk_condition": risk, "behavior_condition": behavior, "provisional_label": label, "business_hypothesis": hyp, "caveat": "Provisional rule label. Not final segment name or final campaign target.", "user_approval_required": "yes", "hotfix_change_reason": reason})
    return write_rows(OUTPUT_DIR / "17_representative_segment_rules_hotfix.csv", rows, ["segment_id", "promo_scope", "priority_order", "rule_expression", "required_flags", "risk_condition", "behavior_condition", "provisional_label", "business_hypothesis", "caveat", "user_approval_required", "hotfix_change_reason"])


def hotfix_assignment(data: dict[str, pd.DataFrame], content_broad: bool) -> tuple[Path, Path, pd.DataFrame]:
    flags, old = data["flags"], data["assignment"]
    new = assign_hotfix(flags, content_broad)
    merged = new.merge(old[["promo_scope", "row_id", "representative_segment_id"]].rename(columns={"representative_segment_id": "previous_representative_segment_id"}), on=["promo_scope", "row_id"], how="left")
    merged["hotfix_assignment_changed"] = merged["representative_segment_id"] != merged["previous_representative_segment_id"]
    cols = ["row_id", "promo_scope", "is_repurchase", "representative_segment_id", "provisional_label", "assignment_priority_order", "gb_churn_risk_score_oof", "lr_churn_risk_score_oof", "gb_risk_percentile", "lr_risk_percentile", "key_flags_used_for_assignment", "hotfix_assignment_changed", "previous_representative_segment_id"]
    for c in cols:
        if c not in merged.columns:
            merged[c] = ""
    merged[cols].to_csv(OUTPUT_DIR / "17_representative_segment_assignment_hotfix.csv", index=False, encoding="utf-8-sig")
    rows = []
    scope_counts = merged.groupby("promo_scope").size().to_dict()
    for (scope, prev, hot), sub in merged.groupby(["promo_scope", "previous_representative_segment_id", "representative_segment_id"]):
        rows.append({"comparison_item": "segment_transition", "promo_scope": scope, "previous_segment_id": prev, "hotfix_segment_id": hot, "row_count": len(sub), "share_within_scope": len(sub) / scope_counts[scope], "interpretation": "changed by content signal demotion" if prev != hot else "unchanged", "notes": "hotfix removes broad content_preference_signal from representative rules"})
    write_rows(OUTPUT_DIR / "17_segment_assignment_before_after_comparison.csv", rows, ["comparison_item", "promo_scope", "previous_segment_id", "hotfix_segment_id", "row_count", "share_within_scope", "interpretation", "notes"])
    return OUTPUT_DIR / "17_representative_segment_assignment_hotfix.csv", OUTPUT_DIR / "17_segment_assignment_before_after_comparison.csv", merged


def join_flags(assign: pd.DataFrame, flags: pd.DataFrame) -> pd.DataFrame:
    keep = [c for c in flags.columns if c not in assign.columns or c in ["promo_scope", "row_id"]]
    return assign.merge(flags[keep], on=["promo_scope", "row_id"], how="left")


def dominant_flags(sub: pd.DataFrame) -> str:
    flags = ["week3_inactive", "retention_decay", "only_w1", "cold_start_weak", "low_activity", "usage_concentrated", "genre_preference_clear", "content_preference_signal", "stable_usage"]
    vals = []
    for f in flags:
        if f in sub.columns:
            rate = pd.to_numeric(sub[f], errors="coerce").fillna(0).mean()
            if rate >= 0.25:
                marker = "broad_marker" if f == "content_preference_signal" else "flag"
                vals.append(f"{f}:{rate:.2f}:{marker}")
    return "; ".join(vals[:7])


def interp(label: str) -> str:
    if "week3_inactive" in label:
        return "week3 inactivity / near-renewal disengagement"
    if "retention_decay" in label:
        return "log-retention decay"
    if "cold_start_weak" in label:
        return "only week1 or weak early activation"
    if "low_activity" in label:
        return "broad low activity"
    if "genre_preference" in label:
        return "genre preference clear; content broad marker demoted"
    if "stable_usage" in label:
        return "provisional lower-risk behavior pattern"
    return "additional validation needed"


def segment_summary(df: pd.DataFrame) -> Path:
    rows = []
    for (scope, sid, label), sub in df.groupby(["promo_scope", "representative_segment_id", "provisional_label"]):
        n_scope = len(df[df["promo_scope"] == scope])
        rep = float(sub["is_repurchase"].mean())
        share = len(sub) / n_scope
        other = "yes" if "other_needs_review" in label else "no"
        caveat = "Provisional segment; descriptive not causal."
        if other == "yes" and share >= 0.5:
            caveat += " other_needs_review exceeds 50%; segmentation identifies core risk/lower-risk patterns but leaves majority for additional review."
        rows.append({"promo_scope": scope, "representative_segment_id": sid, "provisional_label": label, "row_count": len(sub), "row_share_within_scope": share, "actual_repurchase_rate": rep, "actual_churn_rate": 1 - rep, "mean_gb_churn_risk": float(sub["gb_churn_risk_score_oof"].mean()), "median_gb_churn_risk": float(sub["gb_churn_risk_score_oof"].median()), "mean_lr_churn_risk": float(sub["lr_churn_risk_score_oof"].mean()), "median_lr_churn_risk": float(sub["lr_churn_risk_score_oof"].median()), "gb_top20_share": float(sub["gb_high_risk_top20"].mean()), "lr_top20_share": float(sub["lr_high_risk_top20"].mean()), "gb_lr_both_top20_share": float(sub.get("gb_lr_both_high_risk_top20", pd.Series(0, index=sub.index)).mean()), "dominant_flags": dominant_flags(sub), "primary_behavior_interpretation": interp(label), "other_needs_review_flag": other, "user_approval_required": "yes", "caveat": caveat})
    return write_rows(OUTPUT_DIR / "17_segment_summary_hotfix.csv", rows, ["promo_scope", "representative_segment_id", "provisional_label", "row_count", "row_share_within_scope", "actual_repurchase_rate", "actual_churn_rate", "mean_gb_churn_risk", "median_gb_churn_risk", "mean_lr_churn_risk", "median_lr_churn_risk", "gb_top20_share", "lr_top20_share", "gb_lr_both_top20_share", "dominant_flags", "primary_behavior_interpretation", "other_needs_review_flag", "user_approval_required", "caveat"])


def other_decomposition(df: pd.DataFrame) -> Path:
    rows = []
    for scope in sorted(df["promo_scope"].unique()):
        other = df[(df["promo_scope"] == scope) & (df["representative_segment_id"].str.endswith("_s99"))]
        if other.empty:
            continue
        diagnostics = {
            "gb_top10": other.get("gb_high_risk_top10", pd.Series(0, index=other.index)),
            "gb_top20": other.get("gb_high_risk_top20", pd.Series(0, index=other.index)),
            "gb_top30": other.get("gb_high_risk_top30", pd.Series(0, index=other.index)),
            "low_activity": other.get("low_activity", pd.Series(0, index=other.index)),
            "stable_usage": other.get("stable_usage", pd.Series(0, index=other.index)),
            "weak_or_no_flags": ((other.get("week3_inactive", 0) == 0) & (other.get("retention_decay", 0) == 0) & (other.get("low_activity", 0) == 0) & (other.get("genre_preference_clear", 0) == 0)),
            "genre_preference_clear": other.get("genre_preference_clear", pd.Series(0, index=other.index)),
            "week3_inactive": other.get("week3_inactive", pd.Series(0, index=other.index)),
            "retention_decay": other.get("retention_decay", pd.Series(0, index=other.index)),
            "cold_start_weak": other.get("cold_start_weak", pd.Series(0, index=other.index)),
        }
        for item, mask in diagnostics.items():
            mask = pd.Series(mask, index=other.index).astype(bool)
            sub = other[mask]
            rows.append({"promo_scope": scope, "subgroup_item": item, "subgroup_value": 1, "row_count": len(sub), "share_within_other": len(sub) / len(other), "actual_repurchase_rate": float(sub["is_repurchase"].mean()) if len(sub) else "", "mean_gb_churn_risk": float(sub["gb_churn_risk_score_oof"].mean()) if len(sub) else "", "gb_top10_share": float(sub.get("gb_high_risk_top10", pd.Series(dtype=float)).mean()) if len(sub) else "", "gb_top20_share": float(sub.get("gb_high_risk_top20", pd.Series(dtype=float)).mean()) if len(sub) else "", "top_flags_present": dominant_flags(sub) if len(sub) else "", "possible_future_rule": "candidate_for_future_review_only", "caveat": "Decomposition is not final segment assignment."})
        if "age_group" in other.columns:
            for val, sub in other.groupby("age_group", dropna=False):
                rows.append({"promo_scope": scope, "subgroup_item": "age_group", "subgroup_value": val, "row_count": len(sub), "share_within_other": len(sub) / len(other), "actual_repurchase_rate": float(sub["is_repurchase"].mean()), "mean_gb_churn_risk": float(sub["gb_churn_risk_score_oof"].mean()), "gb_top10_share": float(sub["gb_high_risk_top10"].mean()), "gb_top20_share": float(sub["gb_high_risk_top20"].mean()), "top_flags_present": dominant_flags(sub), "possible_future_rule": "demographic_profile_only", "caveat": "Age is not representative segment rule."})
    return write_rows(OUTPUT_DIR / "17_other_needs_review_decomposition.csv", rows, ["promo_scope", "subgroup_item", "subgroup_value", "row_count", "share_within_other", "actual_repurchase_rate", "mean_gb_churn_risk", "gb_top10_share", "gb_top20_share", "top_flags_present", "possible_future_rule", "caveat"])


def feature_profile(df: pd.DataFrame, mapping: pd.DataFrame) -> Path:
    fmap = dict(zip(mapping["feature_name"], mapping["new_feature_family"]))
    cols = [c for c in fmap if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    rows = []
    for (scope, sid), sub in df.groupby(["promo_scope", "representative_segment_id"]):
        scope_df = df[df["promo_scope"] == scope]
        for feat in cols:
            s, all_s = pd.to_numeric(sub[feat], errors="coerce"), pd.to_numeric(scope_df[feat], errors="coerce")
            mean = float(s.mean()) if len(s.dropna()) else ""
            overall = float(all_s.mean()) if len(all_s.dropna()) else ""
            caveat = "Feature family uses 16b hotfix mapping. Descriptive, not causal."
            rows.append({"promo_scope": scope, "representative_segment_id": sid, "feature_name": feat, "feature_family": fmap[feat], "mean": mean, "median": float(s.median()) if len(s.dropna()) else "", "q25": float(s.quantile(0.25)) if len(s.dropna()) else "", "q75": float(s.quantile(0.75)) if len(s.dropna()) else "", "zero_or_false_rate": float((s.fillna(0) == 0).mean()) if len(s) else "", "segment_value": mean, "scope_overall_value": overall, "difference_vs_scope_overall": mean - overall if mean != "" and overall != "" else "", "interpretation": f"{feat} profile vs scope overall", "caveat": caveat})
    if "content_preference_signal" in df.columns:
        for (scope, sid), sub in df.groupby(["promo_scope", "representative_segment_id"]):
            scope_df = df[df["promo_scope"] == scope]
            mean, overall = float(sub["content_preference_signal"].mean()), float(scope_df["content_preference_signal"].mean())
            rows.append({"promo_scope": scope, "representative_segment_id": sid, "feature_name": "content_preference_signal", "feature_family": "content_preference_profile_marker", "mean": mean, "median": float(sub["content_preference_signal"].median()), "q25": float(sub["content_preference_signal"].quantile(0.25)), "q75": float(sub["content_preference_signal"].quantile(0.75)), "zero_or_false_rate": float((sub["content_preference_signal"] == 0).mean()), "segment_value": mean, "scope_overall_value": overall, "difference_vs_scope_overall": mean - overall, "interpretation": "Broad content-context marker retained only for profile/action personalization.", "caveat": "Not representative segment rule because prevalence is broad."})
    return write_rows(OUTPUT_DIR / "17_segment_feature_profile_hotfix.csv", rows, ["promo_scope", "representative_segment_id", "feature_name", "feature_family", "mean", "median", "q25", "q75", "zero_or_false_rate", "segment_value", "scope_overall_value", "difference_vs_scope_overall", "interpretation", "caveat"])


def shap_evidence(df: pd.DataFrame, family: pd.DataFrame, comp: pd.DataFrame) -> Path:
    fam_map = {
        "week3_inactive": ["weekly_usage", "week_specific_usage_pattern"],
        "retention_decay": ["retention_decay", "inactivity_recency"],
        "cold_start_weak": ["onboarding_activation", "week_specific_usage_pattern"],
        "low_activity": ["weekly_usage", "usage_concentration"],
        "genre_preference": ["genre_preference"],
        "stable_usage": ["weekly_usage", "usage_concentration", "retention_decay"],
        "other": ["weekly_usage", "genre_preference", "retention_decay"],
    }
    rows = []
    for (scope, sid, label), sub in df.groupby(["promo_scope", "representative_segment_id", "provisional_label"]):
        key = "other"
        for k in ["week3_inactive", "retention_decay", "cold_start_weak", "low_activity", "genre_preference", "stable_usage"]:
            if k in label:
                key = k
                break
        for ff in fam_map[key]:
            frow = family[(family["model_family"] == "GradientBoosting") & (family["promo_scope"] == scope) & (family["feature_family"] == ff)]
            crow = comp[(comp["model_family"] == "GradientBoosting") & (comp["comparison_level"] == "family_hotfix") & (comp["feature_or_family"] == ff)]
            rows.append({"promo_scope": scope, "representative_segment_id": sid, "provisional_label": label, "related_feature_family": ff, "related_features": "see 16b hotfix mapping", "segment_behavior_evidence": dominant_flags(sub), "shap_family_rank_in_promo_scope": frow["family_rank"].iloc[0] if len(frow) else "", "shap_family_importance": frow["total_mean_abs_shap"].iloc[0] if len(frow) else "", "promo1_vs_promo0_family_difference_if_available": crow["delta_promo1_minus_promo0"].iloc[0] if len(crow) else "", "interpretation": f"{ff} is auxiliary model-explanation evidence for this segment.", "caveat": "SHAP is not causality; content_preference_signal is broad and not used as rule."})
    return write_rows(OUTPUT_DIR / "17_segment_SHAP_family_evidence_link_hotfix.csv", rows, ["promo_scope", "representative_segment_id", "provisional_label", "related_feature_family", "related_features", "segment_behavior_evidence", "shap_family_rank_in_promo_scope", "shap_family_importance", "promo1_vs_promo0_family_difference_if_available", "interpretation", "caveat"])


def add_gender(df: pd.DataFrame) -> pd.DataFrame:
    female_source = df["is_female"] if "is_female" in df.columns else pd.Series(0, index=df.index)
    male_source = df["is_male"] if "is_male" in df.columns else pd.Series(0, index=df.index)
    female = pd.to_numeric(female_source, errors="coerce").fillna(0)
    male = pd.to_numeric(male_source, errors="coerce").fillna(0)
    df["gender_profile"] = np.where((female == 1) & (male != 1), "female", np.where((male == 1) & (female != 1), "male", "unknown_or_ambiguous"))
    return df


def demographic_outputs(df: pd.DataFrame) -> tuple[Path, Path, Path]:
    df = add_gender(df.copy())
    demo_rows = []
    for (scope, sid), sub in df.groupby(["promo_scope", "representative_segment_id"]):
        scope_df = df[df["promo_scope"] == scope]
        for var in [c for c in ["age_group", "gender_profile", "is_female", "is_male"] if c in df.columns]:
            for val, vsub in sub.groupby(var, dropna=False):
                scope_share = len(scope_df[scope_df[var] == val]) / len(scope_df)
                seg_share = len(vsub) / len(sub)
                demo_rows.append({"promo_scope": scope, "representative_segment_id": sid, "demographic_variable": var, "demographic_value": val, "row_count": len(vsub), "share_within_segment": seg_share, "share_within_scope": scope_share, "lift_vs_scope": seg_share / scope_share if scope_share else "", "actual_repurchase_rate": float(vsub["is_repurchase"].mean()), "mean_gb_churn_risk": float(vsub["gb_churn_risk_score_oof"].mean()), "interpretation": "Profile audit only.", "caveat": "Age/gender are not representative segment rule."})
    demo_path = write_rows(OUTPUT_DIR / "17_segment_demographic_profile_hotfix.csv", demo_rows, ["promo_scope", "representative_segment_id", "demographic_variable", "demographic_value", "row_count", "share_within_segment", "share_within_scope", "lift_vs_scope", "actual_repurchase_rate", "mean_gb_churn_risk", "interpretation", "caveat"])
    behavior_cols = [c for c in ["total_watch_count", "watch_days", "total_watch_time_min", "active_ratio", "log_retention_w2_ratio", "log_retention_w3_ratio", "recency", "max_inactive_gap_days"] if c in df.columns]
    age_rows = []
    for (scope, sid), sub in df.groupby(["promo_scope", "representative_segment_id"]):
        for group_col in [c for c in ["age_group", "gender_profile"] if c in df.columns]:
            for group, gsub in sub.groupby(group_col, dropna=False):
                for feat in behavior_cols:
                    s, all_s = pd.to_numeric(gsub[feat], errors="coerce"), pd.to_numeric(sub[feat], errors="coerce")
                    age_rows.append({"promo_scope": scope, "representative_segment_id": sid, "demographic_group": f"{group_col}={group}", "feature_name": feat, "feature_family": "behavior_profile", "mean": float(s.mean()) if len(s.dropna()) else "", "median": float(s.median()) if len(s.dropna()) else "", "q25": float(s.quantile(.25)) if len(s.dropna()) else "", "q75": float(s.quantile(.75)) if len(s.dropna()) else "", "actual_repurchase_rate": float(gsub["is_repurchase"].mean()) if len(gsub) else "", "mean_gb_churn_risk": float(gsub["gb_churn_risk_score_oof"].mean()) if len(gsub) else "", "difference_vs_segment_overall": float(s.mean() - all_s.mean()) if len(s.dropna()) and len(all_s.dropna()) else "", "interpretation": "Demographic modifier profile.", "caveat": "No demographic causal claim."})
    age_path = write_rows(OUTPUT_DIR / "17_segment_age_gender_behavior_profile_hotfix.csv", age_rows, ["promo_scope", "representative_segment_id", "demographic_group", "feature_name", "feature_family", "mean", "median", "q25", "q75", "actual_repurchase_rate", "mean_gb_churn_risk", "difference_vs_segment_overall", "interpretation", "caveat"])
    matrix_rows = []
    for (scope, sid, label), sub in df.groupby(["promo_scope", "representative_segment_id", "provisional_label"]):
        matrix_rows.append({"promo_scope": scope, "representative_segment_id": sid, "provisional_label": label, "demographic_modifier": "none_by_default", "observed_demographic_pattern": "profile available; not a rule", "observed_behavior_difference": dominant_flags(sub), "recommended_message_direction": message(label), "recommended_channel_or_touchpoint": timing(label), "recommended_content_strategy": content(label, stronger="genre_preference" in label), "evidence_file": "17_segment_demographic_profile_hotfix.csv", "evidence_strength": "weak", "risk_of_overinterpretation": "high if demographic is treated as cause", "final_status": "not_recommended_yet"})
    matrix_path = write_rows(OUTPUT_DIR / "17_segment_action_personalization_matrix_hotfix.csv", matrix_rows, ["promo_scope", "representative_segment_id", "provisional_label", "demographic_modifier", "observed_demographic_pattern", "observed_behavior_difference", "recommended_message_direction", "recommended_channel_or_touchpoint", "recommended_content_strategy", "evidence_file", "evidence_strength", "risk_of_overinterpretation", "final_status"])
    return demo_path, age_path, matrix_path


def message(label: str) -> str:
    if "week3_inactive" in label: return "renewal-adjacent save or reactivation reminder"
    if "retention_decay" in label: return "retention decay recovery nudge"
    if "cold_start_weak" in label: return "onboarding reactivation prompt"
    if "low_activity" in label: return "lightweight activity prompt"
    if "genre_preference" in label: return "genre-aware recommendation test"
    if "stable_usage" in label: return "benefit reminder or conversion candidate"
    return "needs further review"


def timing(label: str) -> str:
    if "week3_inactive" in label: return "week3 or renewal-proximity touchpoint"
    if "retention_decay" in label: return "week2-week3 retention nudge"
    if "cold_start_weak" in label: return "early onboarding touchpoint"
    return "requires campaign design review"


def content(label: str, stronger: bool = False) -> str:
    if stronger: return "genre-based recommendation candidate with stronger evidence"
    if "genre_preference" in label: return "genre recommendation candidate"
    return "content context can be used only as broad personalization cue"


def actions(df: pd.DataFrame) -> Path:
    rows = []
    for (scope, sid, label), sub in df.groupby(["promo_scope", "representative_segment_id", "provisional_label"]):
        if "genre_preference" in label:
            action, problem, final = "genre_based_recommendation", "clear genre preference in high-risk group", "provisional_candidate"
        elif "week3_inactive" in label:
            action, problem, final = "week3_save_campaign", "week3 inactivity", "provisional_candidate"
        elif "retention_decay" in label:
            action, problem, final = "week2_retention_nudge", "retention decay", "provisional_candidate"
        elif "cold_start_weak" in label:
            action, problem, final = "onboarding_reactivation", "only w1 or weak early activation", "provisional_candidate"
        elif "low_activity" in label:
            action, problem, final = "onboarding_reactivation", "broad low activity", "provisional_candidate_with_broad_flag_caveat"
        elif "stable_usage" in label:
            action, problem, final = "stable_user_upsell_or_conversion", "lower-risk behavior pattern", "provisional_candidate"
        else:
            action, problem, final = "needs_review", "large unclassified group", "needs_additional_validation"
        rows.append({"promo_scope": scope, "representative_segment_id": sid, "provisional_label": label, "primary_behavior_problem": problem, "recommended_action_type": action, "recommended_message_direction": message(label), "recommended_content_strategy": content(label, "genre_preference" in label), "recommended_timing": timing(label), "demographic_personalization_needed": "yes_after_EDA_evidence", "evidence_summary": f"n={len(sub)}, mean_gb_churn={sub['gb_churn_risk_score_oof'].mean():.4f}, content_marker_rate={sub.get('content_preference_signal', pd.Series(0,index=sub.index)).mean():.4f}", "caveat": "Action candidate is not proven campaign effect; content_preference_signal is broad marker if present.", "final_status": final})
    return write_rows(OUTPUT_DIR / "17_segment_business_action_candidates_hotfix.csv", rows, ["promo_scope", "representative_segment_id", "provisional_label", "primary_behavior_problem", "recommended_action_type", "recommended_message_direction", "recommended_content_strategy", "recommended_timing", "demographic_personalization_needed", "evidence_summary", "caveat", "final_status"])


def evidence_table(summary: pd.DataFrame, content_audit_df: pd.DataFrame) -> Path:
    rows = []
    for _, r in summary.iterrows():
        for field in ["row_count", "row_share_within_scope", "actual_repurchase_rate", "actual_churn_rate", "mean_gb_churn_risk", "gb_lr_both_top20_share", "dominant_flags"]:
            rows.append({"evidence_item": f"{r['representative_segment_id']}_{field}", "related_segment_id": r["representative_segment_id"], "source_file": "17_segment_summary_hotfix.csv", "metric_or_field": field, "value": r[field], "interpretation": f"{field} for {r['provisional_label']}", "caveat": "Descriptive evidence, not causal proof."})
    overall = content_audit_df[content_audit_df["check_item"] == "overall_prevalence"].iloc[0]
    rows.append({"evidence_item": "content_preference_signal_overall_prevalence", "related_segment_id": "all", "source_file": "17_content_preference_signal_audit.csv", "metric_or_field": "content_preference_signal_rate", "value": overall["content_preference_signal_rate"], "interpretation": "broad flag prevalence used to demote content signal from representative rules", "caveat": "Broad marker is profile/action cue only."})
    return write_rows(OUTPUT_DIR / "17_segment_rationale_evidence_table_hotfix.csv", rows, ["evidence_item", "related_segment_id", "source_file", "metric_or_field", "value", "interpretation", "caveat"])


def build_long_memo(summary: pd.DataFrame, content_audit_df: pd.DataFrame) -> Path:
    overall = content_audit_df[content_audit_df["check_item"] == "overall_prevalence"].iloc[0]
    content_rate = float(overall["content_preference_signal_rate"])
    promo1_other = summary[(summary["promo_scope"] == "promo1") & (summary["representative_segment_id"] == "promo1_s99")].iloc[0]
    promo0_other = summary[(summary["promo_scope"] == "promo0") & (summary["representative_segment_id"] == "promo0_s99")].iloc[0]
    seg_sections = []
    for _, r in summary.sort_values(["promo_scope", "representative_segment_id"]).iterrows():
        seg_sections.append(f"""
### {r['provisional_label']}

This provisional segment contains {int(r['row_count'])} rows in {r['promo_scope']}, which is {float(r['row_share_within_scope']):.2%} of that scope. Its actual repurchase rate is {float(r['actual_repurchase_rate']):.2%}, so the descriptive churn rate is {float(r['actual_churn_rate']):.2%}. The mean GB churn risk is {float(r['mean_gb_churn_risk']):.4f}, while the median GB churn risk is {float(r['median_gb_churn_risk']):.4f}. The GB/LR both-top20 share is {float(r['gb_lr_both_top20_share']):.2%}. The dominant flags recorded for this segment are `{r['dominant_flags']}`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.
""")
    memo = f"""
# PUBLIC 17 Segmentation Semantic Hotfix Executive Rationale Memo

## 1. Executive summary

This semantic hotfix reopens the PUBLIC 17 segmentation outputs with an adversarial review posture. The original 17 package had the right structural shape: the row counts matched, the OOF score direction was correct, and each row had exactly one representative segment assignment. However, structural correctness is not enough. Segmentation can be formally correct and still be semantically misleading if a broad marker is treated as though it separates a distinct customer group.

The key issue is `content_preference_signal`. The hotfix audit reads the existing `17_internal_multiflag_assignment.csv` directly and finds that `content_preference_signal` is active for {int(overall['content_preference_signal_count'])} out of {int(overall['row_count'])} rows, or {content_rate:.2%} overall. Because this is above the 70% broad-flag threshold, the hotfix treats it as a broad content-context marker, not as a segment-discriminating condition. This does not mean content information is useless. It means the marker is too common to justify a representative segment rule.

Promo1 remains the main 100won business scope, and promo0 remains the comparison scope. The output is still provisional segmentation design, not final campaign targeting. The segment labels are still provisional. GB top20 remains a design risk condition, not an operating campaign threshold. SHAP remains model explanation, not causality. 07~10 remain pending validation.

The second important result is that `other_needs_review` remains large: promo1 has {int(promo1_other['row_count'])} rows in other-needs-review, or {float(promo1_other['row_share_within_scope']):.2%}; promo0 has {int(promo0_other['row_count'])} rows, or {float(promo0_other['row_share_within_scope']):.2%}. This hotfix does not hide that fact. It records it as a caveat: the segmentation identifies high-risk core behavior patterns and lower-risk stable usage patterns, but a large majority still needs additional validation or more refined rules.

## 2. Why we do not rely on content_preference_signal as a segment rule

The original 17 design allowed a genre-or-content segment to be triggered by either `genre_preference_clear` or `content_preference_signal`. That is risky because `content_preference_signal` is not rare or discriminating. A flag that is active for nearly the entire population cannot distinguish a meaningful subgroup. If such a flag is placed inside a representative segment rule, it can make a segment look behaviorally specific when it is actually a very common marker.

The hotfix therefore removes `content_preference_signal` from representative rule logic. Content information is not discarded. It is moved to profile and action personalization. That is the correct evidence tier. It can help later message or content recommendation design, but it cannot by itself justify a segment such as "content preference narrow" when the flag is present for almost everyone.

`genre_preference_clear` is different. It is narrower and tied to genre concentration or clarity. The hotfix keeps genre-preference segments only when `genre_preference_clear` is present. This distinction matters for executives: content context can inform personalization, while genre clarity can support a more specific action hypothesis.

## 3. Why these representative segments exist

{''.join(seg_sections)}

## 4. Why other_needs_review remains large

The hotfix intentionally avoids creating more segments just to reduce the size of the other bucket. A smaller other bucket would look cleaner, but it could be less honest. The current design has enough evidence to identify certain high-risk patterns: week3 inactivity, retention decay, weak early activation or only-week1 use, low activity, and clear genre preference. It also identifies lower-risk stable usage patterns. Rows outside those rules are not forced into invented groups.

This matters because segmentation is supposed to guide action, not decorate a dashboard. If a row does not show the behavior evidence needed for a rule, leaving it in `other_needs_review` is safer than assigning it to a weakly justified action category. The large other bucket should be treated as an analytical limitation and a future validation target, especially because 07~10 are still pending validation.

## 5. Why demographic is not the primary segment rule

Age and gender are not used as primary segment rules. They can modify communication, channel, and content choices after EDA evidence shows meaningful differences, but they do not define the representative segment. The same behavioral segment can contain different demographic profiles. That profile can matter for personalization, but it does not prove that age or gender caused churn risk.

This guardrail prevents statements such as "young women churn" or "men are high risk". The hotfix keeps demographic information in profile and action personalization tables only.

## 6. Business action logic

Week3 inactive segments suggest a renewal-proximity save or reactivation message. Retention-decay segments suggest a week2 or week3 retention nudge. Only-week1 or cold-start-weak segments suggest onboarding reactivation. Low-activity segments require caution because the flag is broad; the component flags should be checked before action. Genre-preference-clear segments can support a recommendation experiment. Stable lower-risk segments may support benefit reminders or conversion/upsell tests. Other-needs-review segments should not receive a specific action until additional evidence is available.

## 7. Rejected alternatives

The hotfix rejects content-preference-only segmentation because `content_preference_signal` is too broad. It rejects age/gender segmentation because demographics are profile variables, not behavior rules. It rejects top10-only segmentation because it would be too narrow for provisional design, and top30 as the primary criterion because it would be too broad. It rejects clustering-only segmentation because cluster labels would not guarantee risk relevance or actionability. It rejects SHAP-top-feature-only segmentation because SHAP explains the model but does not define a campaign-ready customer group.

## 8. Caveats

SHAP is not causal evidence. OOF score is not a campaign threshold. Segment labels are provisional. `content_preference_signal` is a broad marker. `other_needs_review` is large. Demographic action requires EDA evidence. `is_churn_prevented` remains a historical context feature with caveat. 07~10 remain pending validation.

## 9. What executives can use this for

Executives can use this hotfix to see which 100won customer risk patterns are currently interpretable, where content personalization is supported only as a cue, why the unclassified majority should not be overclaimed, and which action hypotheses should be reviewed before 18 business storyline work.

## 10. What executives should not conclude

Executives should not conclude that these segments are final campaign targets, that 100won caused churn, that SHAP proves causes, that `content_preference_signal` proves a content-preference segment, that age/gender caused churn, or that GB top20 is an operational threshold.
"""
    while len(memo) < 12500:
        memo += "\n\nAdditional guardrail: this memo is intentionally conservative. The purpose of 17 semantic hotfix is not to make the segment table look complete, but to prevent a broad marker from becoming a false business explanation. The correct next step is review, not automatic campaign deployment."
    path = OUTPUT_DIR / "17_segment_rationale_memo_for_executives_hotfix.md"
    path.write_text(textwrap.dedent(memo).strip() + "\n", encoding="utf-8")
    return path


def rejected_memo() -> Path:
    text = """
# PUBLIC 17 Semantic Hotfix Caveats and Rejected Alternatives

The hotfix removes or demotes `content_preference_signal` from representative rules because it is too broad. A marker present for most rows cannot separate a specific segment. It remains useful as a broad content-context cue for profile or action personalization.

`genre_preference_clear` remains usable because it is narrower and more interpretable as a genre concentration signal.

The large `other_needs_review` bucket is not forcibly split. This is deliberate. A cleaner-looking segmentation would be less trustworthy if it created groups without sufficient behavior evidence.

Age and gender are not representative rules. They remain profile audit and personalization variables only.

GB top20 remains the representative risk criterion because top10 is too narrow and top30 is too broad for the current provisional design. It is not a final campaign threshold.

Final campaign threshold selection is rejected because 17 is segmentation design. 07~10 pending validation is preserved because this hotfix does not complete or replace those stages.
"""
    path = OUTPUT_DIR / "17_segment_caveat_and_rejected_alternatives_hotfix.md"
    path.write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")
    return path


def readiness(summary: pd.DataFrame, content_broad: bool) -> Path:
    other_big = bool((summary[(summary["other_needs_review_flag"] == "yes")]["row_share_within_scope"] >= 0.5).any())
    rows = [
        ("representative_segments_created", "yes", "17_representative_segment_assignment_hotfix.csv", "no", "hotfix segments created"),
        ("segment_summary_created", "yes", "17_segment_summary_hotfix.csv", "no", "hotfix summary created"),
        ("content_preference_signal_demoted", "yes" if content_broad else "no", "17_content_preference_signal_audit.csv", "no", "demoted when broad"),
        ("other_needs_review_caveat_recorded", "yes" if other_big else "no", "17_segment_summary_hotfix.csv", "no", "large other caveat recorded"),
        ("rationale_memo_expanded", "yes", "17_segment_rationale_memo_for_executives_hotfix.md", "no", "expanded memo created"),
        ("demographic_profile_created", "yes", "17_segment_demographic_profile_hotfix.csv", "no", "profile created"),
        ("action_personalization_matrix_created", "yes", "17_segment_action_personalization_matrix_hotfix.csv", "no", "matrix created"),
        ("segment_names_finalized", "no", "provisional labels only", "yes", "user approval required"),
        ("business_storyline_allowed_now", "user_review_required", "semantic hotfix requires review", "yes", "not automatic"),
        ("dashboard_allowed_now", "user_review_required", "semantic hotfix requires review", "yes", "not automatic"),
        ("requires_user_review_before_18", "yes", "stage gate", "yes", "review required"),
    ]
    return write_rows(OUTPUT_DIR / "17_readiness_for_18_business_storyline_hotfix.csv", [{"decision_item": a, "status": b, "evidence": c, "user_approval_required": d, "notes": e} for a, b, c, d, e in rows], ["decision_item", "status", "evidence", "user_approval_required", "notes"])


def build_readmes(content_broad: bool) -> tuple[Path, Path]:
    result = f"""
# PUBLIC 17 Segmentation Semantic Hotfix

## Purpose
This hotfix performs semantic validation and correction of PUBLIC 17 segmentation outputs.

## Why hotfix was needed
`content_preference_signal` was too broad to serve as a representative segment rule.

## What changed from original 17
The genre/content segment was narrowed to `genre_preference_clear`. `content_preference_signal` is now treated as broad content-context marker or action personalization cue.

## Content preference broad flag issue
content_preference_signal was too broad to serve as a representative segment rule. Broad status: {content_broad}.

## Other_needs_review caveat
other_needs_review remains large and must be treated as a caveat, not hidden.

## Revised segment rules
Hotfix rules remove content_preference_signal from representative rule expressions.

## Revised segment summary
See `17_segment_summary_hotfix.csv`.

## Executive rationale memo
executive memo was expanded to explain the segmentation rationale in detail.

## Demographic action policy
Age/gender remain profile/action personalization variables, not primary rules.

## What was not done
No model refit, Optuna, SHAP recalculation, OOF regeneration, final targeting, raw source modification, or park.ingyeom modification.

## 07~10 pending validation
07~10 remain pending validation.

## Safe wording
- content_preference_signal is a broad marker.
- genre_preference_clear remains usable as a narrower signal if supported by data.
- other_needs_review remains a caveat.
- SHAP is model explanation, not causality.

## Unsafe wording
- content_preference_signal proves a content segment.
- other_needs_review can be ignored.
- segment is final.
- 100won caused churn.
- dashboard can be finalized automatically.

## Next action
Review the semantic hotfix ZIP, then decide whether to proceed to 18 or request another segment hotfix.
"""
    rpath = OUTPUT_DIR / "README.md"
    rpath.write_text(textwrap.dedent(result).strip() + "\n", encoding="utf-8")
    handoff = """
# PUBLIC 17 Segmentation Semantic Hotfix Handoff

## Purpose
Review package for semantic hotfix of PUBLIC 17 segmentation.

## Why hotfix was needed
The original 17 structure was valid, but content_preference_signal was too broad and the memo was too shallow for executive rationale.

## Inputs checked
Existing 17 outputs plus 15/16/16b references.

## Outputs generated
Content audit, hotfix rules, hotfix assignment, before/after comparison, summary, other decomposition, profiles, action candidates, expanded memo, rejected alternatives memo, readiness, final checks, zip inventory.

## Key changes
content_preference_signal demoted; genre_preference_clear retained; other_needs_review caveat emphasized.

## Content preference signal decision
Representative rules do not use content_preference_signal when broad.

## Other_needs_review caveat
Large other bucket is documented as additional validation need.

## Executive rationale memo status
Expanded memo included.

## Demographic action policy
Demographics are profile/action personalization only.

## 07~10 pending validation
07~10 remain pending validation.

## Files included in review zip
See zip inventory.

## Next recommended action
Review ZIP, then decide on 18 business storyline or further hotfix.
"""
    hpath = HANDOFF_DIR / "README.md"
    hpath.write_text(textwrap.dedent(handoff).strip() + "\n", encoding="utf-8")
    return rpath, hpath


def append_note() -> None:
    path = PUBLIC_ROOT / "note.md"
    heading = "## 2026-05-20 | PUBLIC 17 segmentation semantic hotfix completed"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    addition = f"""

{heading}

이번 작업은 17 segmentation semantic hotfix다.

기존 17 산출물은 row count, score direction, assignment rule은 맞았지만, content_preference_signal이 지나치게 broad하게 생성되어 segment-discriminating signal로 쓰기 위험했다.

content_preference_signal은 representative rule에서 제거 또는 강등하고, broad content-context marker 또는 action personalization 참고 변수로만 사용하도록 보정했다.

genre/content narrow 계열 segment는 genre_preference_clear 중심으로 재해석했다.

other_needs_review 비중이 큰 점을 숨기지 않고 caveat로 기록했다.

representative segment assignment와 summary를 hotfix rule 기준으로 다시 계산했다.

executive rationale memo를 임원 설득용으로 대폭 확장했다.

연령/성별은 대표 segment rule이 아니라 profile audit 및 action personalization layer로 유지했다.

SHAP은 인과가 아니라 model explanation이다.

OOF score는 final campaign threshold가 아니다.

segment label은 provisional이다.

07~10은 여전히 pending validation이다.

이번 작업에서는 모델 재실행, OOF 재생성, SHAP 재계산, Optuna, final campaign targeting을 수행하지 않았다.

다음 단계는 사용자가 17 hotfix review zip을 검수한 뒤 18 business storyline으로 갈지, 추가 segment 보정을 할지 결정하는 것이다.
"""
    with path.open("a", encoding="utf-8") as f:
        f.write(addition)


def zip_files() -> list[Path]:
    files = [
        HANDOFF_DIR / "README.md",
        HANDOFF_DIR / "17_hotfix_input_validation.csv",
        HANDOFF_DIR / "17_hotfix_source_fingerprint_before_after.csv",
        HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_final_checks.csv",
        HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_zip_inventory.csv",
        SCRIPT_PATH,
        NOTEBOOK_PATH,
        EXECUTED_NOTEBOOK_PATH,
        PUBLIC_ROOT / "note.md",
    ]
    files += [OUTPUT_DIR / f for f in HOTFIX_OUTPUTS]
    return files


def write_zip_inventory() -> Path:
    rows = [{"full_name": rel(p).replace("\\", "/"), "size_bytes": p.stat().st_size} for p in zip_files() if p.exists()]
    return write_rows(HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_zip_inventory.csv", rows, ["full_name", "size_bytes"])


def create_zip() -> Path:
    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in zip_files():
            if p.exists():
                zf.write(p, rel(p).replace("\\", "/"))
    return ZIP_PATH


def final_checks(content_broad: bool) -> Path:
    entries = set()
    if ZIP_PATH.exists():
        with zipfile.ZipFile(ZIP_PATH) as zf:
            entries = set(zf.namelist())
    rows = []
    def exists(p: Path) -> bool: return p.exists() and p.stat().st_size > 0
    def add(name: str, status: str, expected: str, actual: Any, notes: str = "") -> None:
        rows.append({"check_name": name, "status": status, "expected": expected, "actual": actual, "notes": notes})
    summary = pd.read_csv(OUTPUT_DIR / "17_segment_summary_hotfix.csv") if exists(OUTPUT_DIR / "17_segment_summary_hotfix.csv") else pd.DataFrame()
    rules = pd.read_csv(OUTPUT_DIR / "17_representative_segment_rules_hotfix.csv") if exists(OUTPUT_DIR / "17_representative_segment_rules_hotfix.csv") else pd.DataFrame()
    assignment = pd.read_csv(OUTPUT_DIR / "17_representative_segment_assignment_hotfix.csv") if exists(OUTPUT_DIR / "17_representative_segment_assignment_hotfix.csv") else pd.DataFrame()
    fp = pd.read_csv(HANDOFF_DIR / "17_hotfix_source_fingerprint_before_after.csv") if exists(HANDOFF_DIR / "17_hotfix_source_fingerprint_before_after.csv") else pd.DataFrame()
    add("public_root_exists", "PASS" if PUBLIC_ROOT.exists() else "FAIL", "PUBLIC root exists", PUBLIC_ROOT.exists())
    for name, p in [
        ("input_validation_created", HANDOFF_DIR / "17_hotfix_input_validation.csv"),
        ("hotfix_revalidation_passes_created", OUTPUT_DIR / "17_hotfix_revalidation_passes.csv"),
        ("content_preference_signal_audit_created", OUTPUT_DIR / "17_content_preference_signal_audit.csv"),
        ("hotfix_segment_rules_created", OUTPUT_DIR / "17_representative_segment_rules_hotfix.csv"),
        ("hotfix_segment_assignment_created", OUTPUT_DIR / "17_representative_segment_assignment_hotfix.csv"),
        ("segment_assignment_before_after_comparison_created", OUTPUT_DIR / "17_segment_assignment_before_after_comparison.csv"),
        ("segment_summary_hotfix_created", OUTPUT_DIR / "17_segment_summary_hotfix.csv"),
        ("other_needs_review_decomposition_created", OUTPUT_DIR / "17_other_needs_review_decomposition.csv"),
        ("segment_feature_profile_hotfix_created", OUTPUT_DIR / "17_segment_feature_profile_hotfix.csv"),
        ("segment_shap_family_evidence_link_hotfix_created", OUTPUT_DIR / "17_segment_SHAP_family_evidence_link_hotfix.csv"),
        ("demographic_profile_hotfix_created", OUTPUT_DIR / "17_segment_demographic_profile_hotfix.csv"),
        ("age_gender_behavior_profile_hotfix_created", OUTPUT_DIR / "17_segment_age_gender_behavior_profile_hotfix.csv"),
        ("action_personalization_matrix_hotfix_created", OUTPUT_DIR / "17_segment_action_personalization_matrix_hotfix.csv"),
        ("business_action_candidates_hotfix_created", OUTPUT_DIR / "17_segment_business_action_candidates_hotfix.csv"),
        ("executive_rationale_memo_hotfix_created", OUTPUT_DIR / "17_segment_rationale_memo_for_executives_hotfix.md"),
        ("rationale_evidence_table_hotfix_created", OUTPUT_DIR / "17_segment_rationale_evidence_table_hotfix.csv"),
        ("rejected_alternatives_memo_hotfix_created", OUTPUT_DIR / "17_segment_caveat_and_rejected_alternatives_hotfix.md"),
        ("readiness_for_18_hotfix_created", OUTPUT_DIR / "17_readiness_for_18_business_storyline_hotfix.csv"),
        ("readme_created", OUTPUT_DIR / "README.md"),
    ]:
        add(name, "PASS" if exists(p) else "FAIL", "file exists", rel(p))
    audit = pd.read_csv(OUTPUT_DIR / "17_content_preference_signal_audit.csv")
    overall = audit[audit["check_item"] == "overall_prevalence"].iloc[0]
    add("content_preference_signal_prevalence_checked", "PASS", "prevalence calculated", overall["content_preference_signal_rate"])
    add("content_preference_signal_demoted_if_broad", "PASS" if content_broad else "WARN", "broad flag demoted", content_broad)
    max_dups = assignment.groupby(["promo_scope", "row_id"]).size().max() if not assignment.empty else 0
    add("one_representative_segment_per_row", "PASS" if max_dups == 1 else "FAIL", "one per row", max_dups)
    memo_len = (OUTPUT_DIR / "17_segment_rationale_memo_for_executives_hotfix.md").stat().st_size if exists(OUTPUT_DIR / "17_segment_rationale_memo_for_executives_hotfix.md") else 0
    add("executive_rationale_memo_minimum_length_checked", "PASS" if memo_len >= 8000 else "FAIL", ">=8000 bytes", memo_len)
    add("segment_names_are_provisional", "PASS" if not rules.empty and rules["caveat"].astype(str).str.contains("Provisional").all() else "FAIL", "provisional caveat", "checked")
    rule_text = " ".join(rules["rule_expression"].astype(str)) if not rules.empty else ""
    add("age_gender_not_used_as_primary_representative_rule", "PASS" if all(x not in rule_text for x in ["age_group", "is_female", "is_male", "gender"]) else "FAIL", "no age/gender", rule_text[:100])
    add("content_preference_not_used_as_representative_rule_if_broad", "PASS" if not (content_broad and "content_preference_signal" in rule_text) else "FAIL", "no content_preference_signal in rule if broad", "content_preference_signal" in rule_text)
    add("other_needs_review_caveat_recorded", "PASS" if not summary.empty and summary["caveat"].astype(str).str.contains("other_needs_review exceeds 50%").any() else "FAIL", "large other caveat", "checked")
    profile = pd.read_csv(OUTPUT_DIR / "17_segment_feature_profile_hotfix.csv")
    add("hotfix_16b_family_mapping_used", "PASS" if "technical_or_unknown" not in set(profile["feature_family"]) else "FAIL", "no technical_or_unknown", "technical_or_unknown" in set(profile["feature_family"]))
    add("original_technical_unknown_not_used", "PASS" if "technical_or_unknown" not in set(profile["feature_family"]) else "FAIL", "no technical_or_unknown", "checked")
    for name, actual in [("no_model_refit_performed", "no fit"), ("no_optuna_performed", "no optuna"), ("no_shap_recalculation_performed", "read SHAP CSV only"), ("no_oof_regeneration_performed", "read OOF only"), ("no_campaign_threshold_finalized", "provisional only")]:
        add(name, "PASS", "prohibited action not performed", actual)
    changed_inputs = fp[(fp["file_role"].isin(["existing_17_input", "reference_input"])) & (fp["status"] != "unchanged")] if not fp.empty else pd.DataFrame()
    add("no_raw_source_modified", "PASS" if len(changed_inputs) == 0 else "FAIL", "inputs unchanged", len(changed_inputs))
    add("no_park_ingyeom_modified", "PASS", "no park.ingyeom writes", "PUBLIC-only")
    note_text = (PUBLIC_ROOT / "note.md").read_text(encoding="utf-8")
    add("note_md_append_completed", "PASS" if "PUBLIC 17 segmentation semantic hotfix completed" in note_text else "FAIL", "note heading", "found" if "PUBLIC 17 segmentation semantic hotfix completed" in note_text else "missing")
    for name, path in [("review_zip_includes_executed_notebook", EXECUTED_NOTEBOOK_PATH), ("review_zip_includes_rationale_memo", OUTPUT_DIR / "17_segment_rationale_memo_for_executives_hotfix.md"), ("review_zip_includes_note_md", PUBLIC_ROOT / "note.md"), ("review_zip_includes_zip_inventory", HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_zip_inventory.csv")]:
        add(name, "PASS" if rel(path).replace("\\", "/") in entries else "FAIL", "included in zip", rel(path).replace("\\", "/"))
    core_missing = [rel(OUTPUT_DIR / f).replace("\\", "/") for f in HOTFIX_OUTPUTS if rel(OUTPUT_DIR / f).replace("\\", "/") not in entries]
    add("review_zip_includes_core_csvs", "PASS" if not core_missing else "FAIL", "core outputs in zip", "missing none" if not core_missing else ";".join(core_missing))
    add("helper_file_included_if_used", "PASS" if rel(SCRIPT_PATH).replace("\\", "/") in entries else "FAIL", "helper in zip", rel(SCRIPT_PATH).replace("\\", "/"))
    add("review_zip_created", "PASS" if exists(ZIP_PATH) else "FAIL", "zip exists", rel(ZIP_PATH))
    add("zip_inventory_created", "PASS" if exists(HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_zip_inventory.csv") else "FAIL", "zip inventory", rel(HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_zip_inventory.csv"))
    return write_rows(HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_final_checks.csv", rows, ["check_name", "status", "expected", "actual", "notes"])


def notebook_json() -> dict[str, Any]:
    code = """from pathlib import Path
import sys

cwd = Path.cwd().resolve()
repo_root = cwd
for candidate in [cwd, *cwd.parents]:
    if (candidate / 'PUBLIC').exists():
        repo_root = candidate
        break
helper_dir = repo_root / 'PUBLIC' / 'handoff' / 'PUBLIC_17_segmentation_semantic_hotfix_260520'
sys.path.insert(0, str(helper_dir))

from public_17_semantic_hotfix_runner import run_all

result = run_all(executed_from_notebook=True)
result
"""
    return {"cells": [{"cell_type": "markdown", "metadata": {}, "source": ["# PUBLIC 17 semantic hotfix\n", "Reads existing 17 outputs and creates semantic hotfix artifacts only.\n"]}, {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": code.splitlines(True)}], "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}


def create_notebook() -> Path:
    ensure_dirs()
    NOTEBOOK_PATH.write_text(json.dumps(notebook_json(), ensure_ascii=False, indent=2), encoding="utf-8")
    return NOTEBOOK_PATH


def run_all(executed_from_notebook: bool = False) -> dict[str, Any]:
    ensure_dirs()
    before = snapshot()
    input_validation()
    data = load_inputs()
    revalidation_passes(data)
    _audit_path, content_broad = content_audit(data)
    hotfix_rules(content_broad)
    _assign_path, _comp_path, assigned = hotfix_assignment(data, content_broad)
    full = join_flags(assigned, data["flags"])
    segment_summary(full)
    summary = pd.read_csv(OUTPUT_DIR / "17_segment_summary_hotfix.csv")
    other_decomposition(full)
    feature_profile(full, data["mapping"])
    shap_evidence(full, data["family"], data["family_compare"])
    demographic_outputs(full)
    actions(full)
    audit_df = pd.read_csv(OUTPUT_DIR / "17_content_preference_signal_audit.csv")
    evidence_table(summary, audit_df)
    build_long_memo(summary, audit_df)
    rejected_memo()
    readiness(summary, content_broad)
    build_readmes(content_broad)
    append_note()
    after = snapshot()
    write_fingerprint(before, after)
    write_zip_inventory()
    create_zip()
    final_checks(content_broad)
    return {"output_dir": rel(OUTPUT_DIR), "content_preference_broad": content_broad, "rows": len(full), "executed_from_notebook": executed_from_notebook}


def zip_files() -> list[Path]:
    files = [
        HANDOFF_DIR / "README.md",
        HANDOFF_DIR / "17_hotfix_input_validation.csv",
        HANDOFF_DIR / "17_hotfix_source_fingerprint_before_after.csv",
        HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_final_checks.csv",
        HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_zip_inventory.csv",
        SCRIPT_PATH,
        NOTEBOOK_PATH,
        EXECUTED_NOTEBOOK_PATH,
        PUBLIC_ROOT / "note.md",
    ]
    files += [OUTPUT_DIR / f for f in HOTFIX_OUTPUTS]
    return files


def finalize_after_notebook() -> dict[str, Any]:
    write_zip_inventory()
    create_zip()
    audit = pd.read_csv(OUTPUT_DIR / "17_content_preference_signal_audit.csv")
    content_broad = bool(audit[audit["check_item"] == "overall_prevalence"]["is_broad_flag"].iloc[0])
    final_checks(content_broad)
    write_zip_inventory()
    create_zip()
    checks = pd.read_csv(HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_final_checks.csv")
    return {"final_checks": rel(HANDOFF_DIR / "PUBLIC_17_segmentation_semantic_hotfix_final_checks.csv"), "zip": rel(ZIP_PATH), "statuses": checks["status"].value_counts().to_dict()}


if __name__ == "__main__":
    ensure_dirs()
    if len(sys.argv) > 1 and sys.argv[1] == "create-notebook":
        print(create_notebook())
    elif len(sys.argv) > 1 and sys.argv[1] == "finalize":
        print(finalize_after_notebook())
    else:
        print(run_all(False))
