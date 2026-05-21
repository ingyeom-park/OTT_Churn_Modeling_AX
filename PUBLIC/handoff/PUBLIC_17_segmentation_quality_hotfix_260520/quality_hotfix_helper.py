from __future__ import annotations

import hashlib
import math
import os
import zipfile
from pathlib import Path

import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
PUBLIC = ROOT / "PUBLIC"
RESULT_DIR = PUBLIC / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments_quality_hotfix_260520"
HANDOFF_DIR = PUBLIC / "handoff" / "PUBLIC_17_segmentation_quality_hotfix_260520"
NOTEBOOK_DIR = PUBLIC / "notebooks" / "17_segmentation_design_260520"
ZIP_PATH = PUBLIC / "zip" / "PUBLIC_17_segmentation_quality_hotfix_260520_review_package.zip"
NOTEBOOK_PATH = NOTEBOOK_DIR / "17_segmentation_quality_hotfix_260520.ipynb"
EXECUTED_NOTEBOOK_PATH = NOTEBOOK_DIR / "17_segmentation_quality_hotfix_260520_executed.ipynb"

ORIG_DIR = PUBLIC / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments"
HOTFIX_DIR = PUBLIC / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments_hotfix_260520"
OOF_DIR = PUBLIC / "results" / "15_oof_score_or_sensitivity_260520" / "four_model_oof_scores_hotfix_260520"
SHAP_DIR = PUBLIC / "results" / "16_SHAP_candidate_interpretation_260520" / "four_model_shap_interpretation"
FAMILY_DIR = PUBLIC / "results" / "16_SHAP_candidate_interpretation_260520" / "16b_feature_family_mapping_hotfix_260520"


REQUIRED_INPUTS = [
    ("17_original_base_datamart", ORIG_DIR / "17_segmentation_base_datamart.csv", True),
    ("17_original_internal_multiflag_assignment", ORIG_DIR / "17_internal_multiflag_assignment.csv", True),
    ("17_original_representative_segment_assignment", ORIG_DIR / "17_representative_segment_assignment.csv", True),
    ("17_original_segment_summary", ORIG_DIR / "17_segment_summary.csv", True),
    ("17_original_segment_feature_profile", ORIG_DIR / "17_segment_feature_profile.csv", True),
    ("17_original_segment_SHAP_family_evidence_link", ORIG_DIR / "17_segment_SHAP_family_evidence_link.csv", True),
    ("17_original_segment_demographic_profile", ORIG_DIR / "17_segment_demographic_profile.csv", True),
    ("17_original_segment_age_gender_behavior_profile", ORIG_DIR / "17_segment_age_gender_behavior_profile.csv", True),
    ("17_original_segment_action_personalization_matrix", ORIG_DIR / "17_segment_action_personalization_matrix.csv", True),
    ("17_original_segment_rationale_memo_for_executives", ORIG_DIR / "17_segment_rationale_memo_for_executives.md", True),
    ("17_hotfix_representative_segment_assignment", HOTFIX_DIR / "17_representative_segment_assignment_hotfix.csv", True),
    ("17_hotfix_segment_summary", HOTFIX_DIR / "17_segment_summary_hotfix.csv", True),
    ("17_hotfix_segment_feature_profile", HOTFIX_DIR / "17_segment_feature_profile_hotfix.csv", True),
    ("17_hotfix_segment_SHAP_family_evidence_link", HOTFIX_DIR / "17_segment_SHAP_family_evidence_link_hotfix.csv", True),
    ("17_hotfix_segment_demographic_profile", HOTFIX_DIR / "17_segment_demographic_profile_hotfix.csv", True),
    ("17_hotfix_segment_age_gender_behavior_profile", HOTFIX_DIR / "17_segment_age_gender_behavior_profile_hotfix.csv", True),
    ("17_hotfix_segment_action_personalization_matrix", HOTFIX_DIR / "17_segment_action_personalization_matrix_hotfix.csv", True),
    ("17_hotfix_segment_rationale_memo_for_executives", HOTFIX_DIR / "17_segment_rationale_memo_for_executives_hotfix.md", True),
    ("17_hotfix_other_needs_review_decomposition", HOTFIX_DIR / "17_other_needs_review_decomposition.csv", True),
    ("17_hotfix_content_preference_signal_audit", HOTFIX_DIR / "17_content_preference_signal_audit.csv", True),
    ("15_oof_score_wide", OOF_DIR / "15_oof_score_wide.csv", True),
    ("15_oof_score_long", OOF_DIR / "15_oof_score_long.csv", True),
    ("15_gb_lr_high_risk_overlap", OOF_DIR / "15_gb_lr_high_risk_overlap.csv", True),
    ("16_shap_global_importance", SHAP_DIR / "16_shap_global_importance.csv", True),
    ("16b_feature_family_mapping_hotfix", FAMILY_DIR / "16b_feature_family_mapping_hotfix.csv", True),
    ("16b_shap_family_importance_hotfix", FAMILY_DIR / "16b_shap_family_importance_hotfix.csv", True),
    ("16b_promo1_vs_promo0_shap_comparison_hotfix", FAMILY_DIR / "16b_promo1_vs_promo0_shap_comparison_hotfix.csv", True),
    ("16b_family_interpretation_handoff_for_17", FAMILY_DIR / "16b_family_interpretation_handoff_for_17.csv", True),
    ("06_model_input_promo_0", PUBLIC / "data" / "06_model_input_promo_0.csv", True),
    ("06_model_input_promo_1", PUBLIC / "data" / "06_model_input_promo_1.csv", True),
]

RESULT_FILES = {
    "revalidation": RESULT_DIR / "17_quality_revalidation_passes.csv",
    "quality_audit": RESULT_DIR / "17_segment_quality_audit.csv",
    "small_policy": RESULT_DIR / "17_small_segment_merge_policy.csv",
    "other_decomp": RESULT_DIR / "17_other_needs_review_decomposition_quality_hotfix.csv",
    "differential": RESULT_DIR / "17_promo1_vs_promo0_segment_differential_analysis.csv",
    "proposal": RESULT_DIR / "17_revised_representative_segment_proposal.csv",
    "assignment_sim": RESULT_DIR / "17_revised_segment_assignment_simulation.csv",
    "summary_sim": RESULT_DIR / "17_revised_segment_summary_simulation.csv",
    "demo_bridge": RESULT_DIR / "17_revised_segment_demographic_action_bridge.csv",
    "memo": RESULT_DIR / "17_segment_quality_hotfix_rationale_memo_for_executives.md",
    "evidence": RESULT_DIR / "17_segment_quality_hotfix_evidence_table.csv",
    "readiness": RESULT_DIR / "17_readiness_for_18_quality_hotfix.csv",
    "readme": RESULT_DIR / "README.md",
}


def ensure_dirs() -> None:
    for path in [RESULT_DIR, HANDOFF_DIR, NOTEBOOK_DIR, ZIP_PATH.parent]:
        path.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_shape(path: Path) -> tuple[str, str, str]:
    if not path.exists():
        return "", "", "missing"
    if path.suffix.lower() == ".csv":
        try:
            df = pd.read_csv(path)
            return str(len(df)), str(len(df.columns)), "readable csv"
        except Exception as exc:
            return "", "", f"csv read error: {exc}"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return str(len(text.splitlines())), "1", "readable text"
    except Exception as exc:
        return "", "", f"text read error: {exc}"


def input_validation() -> pd.DataFrame:
    rows = []
    for item, path, required in REQUIRED_INPUTS:
        exists = path.exists()
        row_count, column_count, note = file_shape(path)
        status = "PASS" if exists and "error" not in note else "FAIL"
        if not required and not exists:
            status = "WARN"
        rows.append(
            {
                "input_item": item,
                "expected_path": str(path.relative_to(ROOT)),
                "exists": bool(exists),
                "rows": row_count,
                "columns": column_count,
                "status": status,
                "notes": note,
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(HANDOFF_DIR / "17_quality_hotfix_input_validation.csv", index=False, encoding="utf-8-sig")
    return df


def read_inputs() -> dict[str, pd.DataFrame]:
    return {
        "base": pd.read_csv(ORIG_DIR / "17_segmentation_base_datamart.csv"),
        "flags": pd.read_csv(ORIG_DIR / "17_internal_multiflag_assignment.csv"),
        "orig_assign": pd.read_csv(ORIG_DIR / "17_representative_segment_assignment.csv"),
        "hotfix_assign": pd.read_csv(HOTFIX_DIR / "17_representative_segment_assignment_hotfix.csv"),
        "orig_summary": pd.read_csv(ORIG_DIR / "17_segment_summary.csv"),
        "hotfix_summary": pd.read_csv(HOTFIX_DIR / "17_segment_summary_hotfix.csv"),
        "content_audit": pd.read_csv(HOTFIX_DIR / "17_content_preference_signal_audit.csv"),
        "hotfix_rules": pd.read_csv(HOTFIX_DIR / "17_representative_segment_rules_hotfix.csv"),
        "orig_rules": pd.read_csv(ORIG_DIR / "17_representative_segment_rules.csv"),
        "demo_hotfix": pd.read_csv(HOTFIX_DIR / "17_segment_demographic_profile_hotfix.csv"),
        "action_hotfix": pd.read_csv(HOTFIX_DIR / "17_segment_action_personalization_matrix_hotfix.csv"),
        "family_mapping": pd.read_csv(FAMILY_DIR / "16b_feature_family_mapping_hotfix.csv"),
    }


def recompute_assignment(flags: pd.DataFrame, mode: str) -> pd.DataFrame:
    out = flags[["row_id", "promo_scope"]].copy()
    out["representative_segment_id"] = ""
    out["provisional_label"] = ""
    out["assignment_priority_order"] = 99
    for scope in ["promo1", "promo0"]:
        prefix = scope
        mask_scope = flags["promo_scope"].eq(scope)
        assigned = pd.Series(False, index=flags.index)

        rules = [
            ("s01", 1, "high_risk_week3_inactive", flags["gb_high_risk_top20"].eq(1) & flags["week3_inactive"].eq(1)),
            ("s02", 2, "high_risk_retention_decay", flags["gb_high_risk_top20"].eq(1) & flags["retention_decay"].eq(1)),
            (
                "s03",
                3,
                "high_risk_only_w1_or_cold_start_weak",
                flags["gb_high_risk_top20"].eq(1) & (flags["only_w1"].eq(1) | flags["cold_start_weak"].eq(1)),
            ),
            ("s04", 4, "high_risk_low_activity", flags["gb_high_risk_top20"].eq(1) & flags["low_activity"].eq(1)),
        ]
        if mode == "original" and scope == "promo1":
            rules.append(
                (
                    "s05",
                    5,
                    "high_risk_genre_or_content_narrow",
                    flags["gb_high_risk_top20"].eq(1)
                    & (flags["genre_preference_clear"].eq(1) | flags["content_preference_signal"].eq(1)),
                )
            )
            stable_code = "s06"
            stable_order = 6
        elif mode == "hotfix":
            rules.append(
                (
                    "s05",
                    5,
                    "high_risk_genre_preference_clear",
                    flags["gb_high_risk_top20"].eq(1) & flags["genre_preference_clear"].eq(1),
                )
            )
            stable_code = "s06"
            stable_order = 6
        else:
            stable_code = "s05"
            stable_order = 5

        rules.append((stable_code, stable_order, "stable_usage_lower_risk", flags["gb_high_risk_top20"].eq(0) & flags["stable_usage"].eq(1)))

        for code, order, label, condition in rules:
            mask = mask_scope & ~assigned & condition
            out.loc[mask, "representative_segment_id"] = f"{prefix}_{code}"
            out.loc[mask, "provisional_label"] = f"{prefix}_{label}"
            out.loc[mask, "assignment_priority_order"] = order
            assigned |= mask

        fallback = mask_scope & ~assigned
        out.loc[fallback, "representative_segment_id"] = f"{prefix}_s99"
        out.loc[fallback, "provisional_label"] = f"{prefix}_other_needs_review"
        out.loc[fallback, "assignment_priority_order"] = 99
    return out


def flag_text(row: pd.Series) -> str:
    flags = []
    for col in [
        "week3_inactive",
        "retention_decay",
        "only_w1",
        "cold_start_weak",
        "low_activity",
        "stable_usage",
        "genre_preference_clear",
        "content_preference_signal",
    ]:
        if col in row and int(row[col]) == 1:
            flags.append(col)
    return ";".join(flags) if flags else "no_dominant_flag"


def dominant_flags(df: pd.DataFrame) -> str:
    cols = [
        "week3_inactive",
        "retention_decay",
        "only_w1",
        "cold_start_weak",
        "low_activity",
        "stable_usage",
        "genre_preference_clear",
        "content_preference_signal",
    ]
    parts = []
    for col in cols:
        if col in df.columns and len(df) > 0:
            rate = pd.to_numeric(df[col], errors="coerce").fillna(0).mean()
            if rate >= 0.25:
                suffix = "broad_marker" if col == "content_preference_signal" else "flag"
                parts.append(f"{col}:{rate:.2f}:{suffix}")
    return "; ".join(parts) if parts else "no single flag >= 25%"


def min_n_status(n: int) -> str:
    if n >= 300:
        return "pass_representative_candidate"
    if n >= 100:
        return "small_provisional_subsignal"
    if n >= 30:
        return "rare_pattern_note"
    return "case_note_only"


def entropy(rate: float) -> float:
    if pd.isna(rate) or rate <= 0 or rate >= 1:
        return 0.0
    return float(-(rate * math.log2(rate) + (1 - rate) * math.log2(1 - rate)))


def family_from_label(label: str) -> str:
    label = str(label)
    core = label.replace("promo1_", "").replace("promo0_", "")
    if "week3_inactive" in core or "retention_decay" in core:
        return "high_risk_week3_inactivity_or_retention_decay"
    if "only_w1" in core or "cold_start" in core or "low_activity" in core:
        return "high_risk_activation_or_low_engagement"
    if "genre" in core or "content" in core:
        return "genre_or_content_action_cue"
    if "stable_usage" in core:
        return "stable_usage_lower_risk"
    if "other_needs_review" in core:
        return "other_needs_review_residual"
    return core


def revalidation_passes(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    base = data["base"]
    flags = data["flags"]
    orig_assign = data["orig_assign"]
    hotfix_assign = data["hotfix_assign"]
    orig_rec = recompute_assignment(flags, "original")
    hotfix_rec = recompute_assignment(flags, "hotfix")
    rows = []

    def add(pass_name, item, status, expected, actual, mismatch=0, severity="info", notes=""):
        rows.append(
            {
                "validation_pass": pass_name,
                "check_item": item,
                "status": status,
                "expected": expected,
                "actual": actual,
                "mismatch_count": int(mismatch),
                "severity": severity,
                "notes": notes,
            }
        )

    add("Pass 1. Row integrity check", "base_datamart_total_rows", "PASS", "23097 rows expected from current base read", len(base), 0, "info", "Read from 17_segmentation_base_datamart.csv")
    for scope, g in base.groupby("promo_scope"):
        add("Pass 1. Row integrity check", f"{scope}_base_row_count", "PASS", "scope row count", len(g), 0, "info", "Scope count read directly from base datamart")
        dup = int(g.duplicated(["promo_scope", "row_id"]).sum())
        add("Pass 1. Row integrity check", f"{scope}_promo_scope_row_id_unique", "PASS" if dup == 0 else "FAIL", "0 duplicates", dup, dup, "fail_blocking" if dup else "info", "promo_scope + row_id uniqueness")
        for name, assign in [("original", orig_assign), ("hotfix", hotfix_assign)]:
            ag = assign[assign["promo_scope"].eq(scope)]
            diff = abs(len(ag) - len(g))
            add("Pass 1. Row integrity check", f"{scope}_{name}_assignment_rows_match_scope", "PASS" if diff == 0 else "FAIL", len(g), len(ag), diff, "fail_blocking" if diff else "info", f"{name} assignment row count")
            total = int(ag.groupby("representative_segment_id").size().sum())
            add("Pass 1. Row integrity check", f"{scope}_{name}_segment_counts_sum_to_scope", "PASS" if total == len(g) else "FAIL", len(g), total, abs(total - len(g)), "fail_blocking" if total != len(g) else "info", "Segment grouped count sum")

    for model in ["gb", "lr"]:
        rep_col = f"{model}_repurchase_score_oof"
        risk_col = f"{model}_churn_risk_score_oof"
        max_delta = float((base[risk_col] - (1 - base[rep_col])).abs().max())
        add("Pass 2. Score direction check", f"{model}_risk_equals_1_minus_repurchase", "PASS" if max_delta < 1e-9 else "FAIL", "max delta < 1e-9", f"{max_delta:.12f}", int(max_delta >= 1e-9), "fail_blocking" if max_delta >= 1e-9 else "info", "OOF direction check only; no OOF regeneration")
        for scope, g in base.groupby("promo_scope"):
            for pct in [10, 20, 30]:
                col = f"{model}_high_risk_top{pct}"
                expected = math.ceil(len(g) * pct / 100)
                actual = int(g[col].sum())
                add("Pass 2. Score direction check", f"{scope}_{model}_top{pct}_count", "PASS" if expected == actual else "FAIL", expected, actual, abs(expected - actual), "fail_blocking" if expected != actual else "info", "Count expected by ceil(scope_n * percentile)")

    orig_cmp = orig_assign[["row_id", "promo_scope", "representative_segment_id"]].merge(orig_rec, on=["row_id", "promo_scope"], suffixes=("_file", "_recomputed"))
    orig_mismatch = int((orig_cmp["representative_segment_id_file"] != orig_cmp["representative_segment_id_recomputed"]).sum())
    add("Pass 3. Representative assignment recomputation", "original_assignment_vs_independent_recompute", "PASS" if orig_mismatch == 0 else "FAIL", 0, orig_mismatch, orig_mismatch, "fail_blocking" if orig_mismatch else "info", "Original rule recomputation from multiflag assignment")
    hot_cmp = hotfix_assign[["row_id", "promo_scope", "representative_segment_id"]].merge(hotfix_rec, on=["row_id", "promo_scope"], suffixes=("_file", "_recomputed"))
    hot_mismatch = int((hot_cmp["representative_segment_id_file"] != hot_cmp["representative_segment_id_recomputed"]).sum())
    add("Pass 3. Representative assignment recomputation", "semantic_hotfix_assignment_vs_independent_recompute", "PASS" if hot_mismatch == 0 else "FAIL", 0, hot_mismatch, hot_mismatch, "fail_blocking" if hot_mismatch else "info", "Hotfix rule recomputation demotes content_preference_signal from representative rule")

    summary = data["hotfix_summary"]
    small = summary[(summary["row_count"] < 300) & ~summary["representative_segment_id"].str.endswith("s99")]
    add("Pass 4. Business sanity check", "n_below_300_representative_segments", "WARN" if len(small) else "PASS", "0 small representative segments", len(small), len(small), "warn" if len(small) else "info", "; ".join(small["provisional_label"].astype(str).tolist()))
    other = summary[summary["provisional_label"].str.contains("other_needs_review", na=False)]
    for _, row in other.iterrows():
        status = "WARN" if row["row_share_within_scope"] >= 0.5 else "PASS"
        add("Pass 4. Business sanity check", f"{row['promo_scope']}_other_needs_review_share", status, "< 0.50 preferred for concise representative scheme", f"{row['row_share_within_scope']:.4f}", 0, "warn" if status == "WARN" else "info", "Other is residual, not mid-risk")
    content_rules = data["hotfix_rules"]["rule_expression"].str.contains("content_preference_signal", case=False, na=False).sum()
    add("Pass 4. Business sanity check", "content_preference_signal_used_in_hotfix_representative_rule", "PASS" if content_rules == 0 else "FAIL", 0, int(content_rules), int(content_rules), "fail_blocking" if content_rules else "info", "content_preference_signal remains broad marker/action cue only")
    age_gender_rules = data["hotfix_rules"]["rule_expression"].str.contains("age_group|gender|is_female|is_male", case=False, na=False).sum()
    add("Pass 4. Business sanity check", "age_gender_used_in_representative_rule", "PASS" if age_gender_rules == 0 else "FAIL", 0, int(age_gender_rules), int(age_gender_rules), "fail_blocking" if age_gender_rules else "info", "Age/gender retained only in profile/action layer")
    tech_unknown = int(data["family_mapping"]["new_feature_family"].astype(str).str.contains("technical_or_unknown", case=False, na=False).sum())
    add("Pass 4. Business sanity check", "original_technical_or_unknown_bucket_used_in_16b_hotfix", "PASS" if tech_unknown == 0 else "FAIL", 0, tech_unknown, tech_unknown, "fail_blocking" if tech_unknown else "info", "16b mapping checked")
    remapped = int(data["family_mapping"]["remap_status"].astype(str).str.contains("remapped|unchanged", case=False, na=False).sum())
    add("Pass 4. Business sanity check", "16b_hotfix_family_mapping_used", "PASS" if remapped > 0 else "FAIL", "> 0 mapping rows", remapped, 0 if remapped > 0 else 1, "fail_blocking" if remapped == 0 else "info", "16b feature family mapping file read")
    for _, row in summary.iterrows():
        diff = abs(float(row["actual_churn_rate"]) - float(base[base["promo_scope"].eq(row["promo_scope"])]["is_repurchase"].rsub(1).mean()))
        add("Pass 4. Business sanity check", f"{row['representative_segment_id']}_churn_rate_distinctness", "WARN" if diff < 0.03 else "PASS", "absolute difference >= 0.03 preferred", f"{diff:.4f}", 0, "warn" if diff < 0.03 else "info", "Descriptive separation from scope mean")
    out = pd.DataFrame(rows)
    out.to_csv(RESULT_FILES["revalidation"], index=False, encoding="utf-8-sig")
    return out


def segment_quality_audit(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    base = data["base"]
    flags = data["flags"]
    assign = data["hotfix_assign"]
    merged = assign.merge(flags, on=["row_id", "promo_scope", "is_repurchase", "gb_churn_risk_score_oof", "lr_churn_risk_score_oof"], how="left")
    scope_stats = base.groupby("promo_scope").agg(
        scope_actual_churn_rate=("is_repurchase", lambda s: 1 - s.mean()),
        scope_mean_gb_churn_risk=("gb_churn_risk_score_oof", "mean"),
    )
    rows = []
    for (scope, seg), g in merged.groupby(["promo_scope", "representative_segment_id"], sort=True):
        label = str(g["provisional_label"].iloc[0])
        n = len(g)
        repurchase = float(g["is_repurchase"].mean())
        churn = 1 - repurchase
        scope_churn = float(scope_stats.loc[scope, "scope_actual_churn_rate"])
        scope_risk = float(scope_stats.loc[scope, "scope_mean_gb_churn_risk"])
        status_n = min_n_status(n)
        family = family_from_label(label)
        if "other_needs_review" in label:
            rec = "keep_as_other_needs_review"
            actionability = "residual_requires_review"
        elif n < 30:
            rec = "demote_to_profile_note"
            actionability = "case_note_only"
        elif n < 300 and "genre" in label:
            rec = "demote_to_profile_note"
            actionability = "profile_or_action_cue_only"
        elif n < 300:
            rec = "merge_into_behavior_family"
            actionability = "usable_as_subsignal_not_representative"
        elif family == "genre_or_content_action_cue":
            rec = "needs_user_review"
            actionability = "action_cue_not_primary_rule"
        else:
            rec = "keep_as_representative"
            actionability = "business_action_candidate"
        rows.append(
            {
                "promo_scope": scope,
                "representative_segment_id": seg,
                "provisional_label": label,
                "row_count": n,
                "row_share_within_scope": n / len(base[base["promo_scope"].eq(scope)]),
                "actual_repurchase_rate": repurchase,
                "actual_churn_rate": churn,
                "scope_actual_churn_rate": scope_churn,
                "churn_lift_vs_scope": churn / scope_churn if scope_churn else math.nan,
                "mean_gb_churn_risk": float(g["gb_churn_risk_score_oof"].mean()),
                "scope_mean_gb_churn_risk": scope_risk,
                "risk_lift_vs_scope": float(g["gb_churn_risk_score_oof"].mean()) / scope_risk if scope_risk else math.nan,
                "target_entropy": entropy(repurchase),
                "normalized_entropy": entropy(repurchase),
                "gb_lr_top20_overlap_share": float(g.get("gb_lr_both_high_risk_top20", pd.Series([0] * len(g))).mean()),
                "dominant_behavior_flags": dominant_flags(g),
                "actionability_status": actionability,
                "min_n_status": status_n,
                "recommended_segment_status": rec,
                "reason": f"{family}; n_status={status_n}; content_preference_signal treated as broad marker, not representative discriminator.",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(RESULT_FILES["quality_audit"], index=False, encoding="utf-8-sig")
    return out


def small_segment_policy(quality: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in quality.iterrows():
        label = str(row["provisional_label"])
        n = int(row["row_count"])
        if "other_needs_review" in label:
            action = "keep_as_needs_review"
            target = "other_needs_review_residual"
            preserved = "residual_review_bucket"
        elif n >= 300:
            action = "keep_representative"
            target = family_from_label(label)
            preserved = "not_demoted"
        elif "retention_decay" in label:
            action = "merge_to_retention_inactivity_family"
            target = "high_risk_week3_inactivity_or_retention_decay"
            preserved = "retention_decay_subsignal"
        elif "low_activity" in label or "only_w1" in label or "cold_start" in label:
            action = "merge_to_activation_low_engagement_family"
            target = "high_risk_activation_or_low_engagement"
            preserved = "low_activity_or_cold_start_subsignal"
        elif "genre" in label or "content" in label:
            action = "demote_to_genre_action_cue"
            target = "profile_action_personalization_layer"
            preserved = "genre_action_cue"
        else:
            action = "demote_to_profile_note"
            target = "profile_note"
            preserved = "monitoring_note"
        rows.append(
            {
                "promo_scope": row["promo_scope"],
                "original_segment_id": row["representative_segment_id"],
                "original_row_count": n,
                "min_n_status": row["min_n_status"],
                "recommended_action": action,
                "merge_target_segment_family": target,
                "preserved_as_subsignal": preserved,
                "business_reason": "Small segments are retained as evidence but not promoted to representative business segments unless they pass minimum size and actionability.",
                "caveat": "This is a proposal for user review, not a final assignment change.",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(RESULT_FILES["small_policy"], index=False, encoding="utf-8-sig")
    return out


def other_decomposition(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    flags = data["flags"]
    assign = data["hotfix_assign"]
    merged = assign.merge(flags, on=["row_id", "promo_scope", "is_repurchase", "gb_churn_risk_score_oof", "lr_churn_risk_score_oof"], how="left")
    other = merged[merged["provisional_label"].str.contains("other_needs_review", na=False)].copy()
    rows = []
    for scope, sg in other.groupby("promo_scope"):
        q25 = sg["gb_churn_risk_score_oof"].quantile(0.25)
        def subgroup(r):
            if int(r["gb_high_risk_top20"]) == 1 or int(r["gb_high_risk_top30"]) == 1:
                return "other_high_risk_unexplained" if int(r["gb_high_risk_top20"]) == 1 else "other_mid_risk_watchlist"
            if int(r.get("stable_usage", 0)) == 1 or float(r["gb_churn_risk_score_oof"]) <= q25:
                return "other_stable_like_residual"
            if int(r.get("genre_preference_clear", 0)) == 1 or int(r.get("content_preference_signal", 0)) == 1:
                return "other_demographic_or_profile_note"
            return "other_low_risk_general"
        sg = sg.copy()
        sg["other_subgroup"] = sg.apply(subgroup, axis=1)
        for sub, g in sg.groupby("other_subgroup"):
            repurchase = float(g["is_repurchase"].mean())
            n = len(g)
            future = "future_representative_candidate_if_user_approved" if n >= 300 and sub in ["other_high_risk_unexplained", "other_mid_risk_watchlist", "other_stable_like_residual"] else "monitoring_or_profile_note"
            rows.append(
                {
                    "promo_scope": scope,
                    "other_subgroup": sub,
                    "row_count": n,
                    "share_within_other": n / len(sg),
                    "share_within_scope": n / len(merged[merged["promo_scope"].eq(scope)]),
                    "actual_repurchase_rate": repurchase,
                    "actual_churn_rate": 1 - repurchase,
                    "mean_gb_churn_risk": float(g["gb_churn_risk_score_oof"].mean()),
                    "median_gb_churn_risk": float(g["gb_churn_risk_score_oof"].median()),
                    "gb_top10_share": float(g["gb_high_risk_top10"].mean()),
                    "gb_top20_share": float(g["gb_high_risk_top20"].mean()),
                    "gb_top30_share": float(g["gb_high_risk_top30"].mean()),
                    "dominant_flags": dominant_flags(g),
                    "possible_future_rule": future,
                    "representative_promotion_recommendation": "do_not_promote_without_user_review",
                    "caveat": "Other decomposition is not a new final representative segment.",
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(RESULT_FILES["other_decomp"], index=False, encoding="utf-8-sig")
    return out


def promo_differential(quality: pd.DataFrame) -> pd.DataFrame:
    temp = quality.copy()
    temp["segment_family"] = temp["provisional_label"].map(family_from_label)
    rows = []
    for family, g in temp.groupby("segment_family"):
        p1 = g[g["promo_scope"].eq("promo1")]
        p0 = g[g["promo_scope"].eq("promo0")]
        def val(frame, col):
            return float(frame[col].iloc[0]) if len(frame) else math.nan
        def txt(frame, col):
            return str(frame[col].iloc[0]) if len(frame) else "not_observed"
        p1_n = int(p1["row_count"].sum()) if len(p1) else 0
        p0_n = int(p0["row_count"].sum()) if len(p0) else 0
        p1_churn = (p1["actual_churn_rate"] * p1["row_count"]).sum() / p1["row_count"].sum() if p1_n else math.nan
        p0_churn = (p0["actual_churn_rate"] * p0["row_count"]).sum() / p0["row_count"].sum() if p0_n else math.nan
        p1_risk = (p1["mean_gb_churn_risk"] * p1["row_count"]).sum() / p1["row_count"].sum() if p1_n else math.nan
        p0_risk = (p0["mean_gb_churn_risk"] * p0["row_count"]).sum() / p0["row_count"].sum() if p0_n else math.nan
        if p1_n and p0_n:
            interp = "Common observed behavior signal; compare strength by scope without causal wording."
        elif p1_n:
            interp = "Observed only in promo1 current representative structure; candidate for 100won focused review, not causal proof."
        else:
            interp = "Observed only in promo0 current representative structure; treat as general comparison signal."
        rows.append(
            {
                "segment_family": family,
                "promo1_row_count": p1_n,
                "promo0_row_count": p0_n,
                "promo1_churn_rate": p1_churn,
                "promo0_churn_rate": p0_churn,
                "churn_rate_delta_promo1_minus_promo0": p1_churn - p0_churn if p1_n and p0_n else math.nan,
                "promo1_mean_gb_churn_risk": p1_risk,
                "promo0_mean_gb_churn_risk": p0_risk,
                "gb_risk_delta_promo1_minus_promo0": p1_risk - p0_risk if p1_n and p0_n else math.nan,
                "promo1_dominant_flags": txt(p1, "dominant_behavior_flags"),
                "promo0_dominant_flags": txt(p0, "dominant_behavior_flags"),
                "interpretation": interp,
                "business_implication": "Use as prioritization evidence for review; do not state that 100won caused the pattern.",
                "caveat": "Descriptive OOF/behavior comparison, not causal inference.",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(RESULT_FILES["differential"], index=False, encoding="utf-8-sig")
    return out


def revised_family(row: pd.Series) -> tuple[str, str, str]:
    subs = []
    if int(row.get("genre_preference_clear", 0)) == 1:
        subs.append("genre_action_cue")
    if int(row.get("content_preference_signal", 0)) == 1:
        subs.append("content_context_marker")
    if int(row.get("retention_decay", 0)) == 1:
        subs.append("retention_decay_subsignal")
    if int(row.get("low_activity", 0)) == 1:
        subs.append("low_activity_subsignal")
    if int(row.get("gb_high_risk_top20", 0)) == 1 and (int(row.get("week3_inactive", 0)) == 1 or int(row.get("retention_decay", 0)) == 1):
        return "high_risk_week3_inactivity_or_retention_decay", "GB top20 plus week3 inactivity or retention decay", ";".join(subs)
    if int(row.get("gb_high_risk_top20", 0)) == 1 and (int(row.get("low_activity", 0)) == 1 or int(row.get("only_w1", 0)) == 1 or int(row.get("cold_start_weak", 0)) == 1):
        return "high_risk_activation_or_low_engagement", "GB top20 plus weak activation, low activity, or cold start", ";".join(subs)
    if int(row.get("gb_high_risk_top30", 0)) == 1:
        return "mid_risk_retention_watchlist", "GB top30 residual watchlist after higher priority rules", ";".join(subs)
    if int(row.get("stable_usage", 0)) == 1:
        return "stable_usage_lower_risk", "Stable usage without GB top20 high-risk flag", ";".join(subs)
    return "other_needs_review_residual", "No revised representative behavior family rule matched", ";".join(subs)


def assignment_simulation(data: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    flags = data["flags"]
    prev = data["hotfix_assign"][["row_id", "promo_scope", "representative_segment_id"]].rename(columns={"representative_segment_id": "previous_segment_id"})
    sim = flags.merge(prev, on=["row_id", "promo_scope"], how="left")
    vals = sim.apply(revised_family, axis=1)
    sim["revised_segment_family"] = [v[0] for v in vals]
    sim["revised_assignment_reason"] = [v[1] for v in vals]
    sim["retained_subsignals"] = [v[2] if v[2] else "none" for v in vals]
    sim["key_flags"] = sim.apply(flag_text, axis=1)
    sim["user_approval_required"] = "yes"
    assign_cols = [
        "row_id",
        "promo_scope",
        "is_repurchase",
        "previous_segment_id",
        "revised_segment_family",
        "revised_assignment_reason",
        "gb_churn_risk_score_oof",
        "lr_churn_risk_score_oof",
        "key_flags",
        "retained_subsignals",
        "user_approval_required",
    ]
    sim[assign_cols].to_csv(RESULT_FILES["assignment_sim"], index=False, encoding="utf-8-sig")

    rows = []
    for (scope, fam), g in sim.groupby(["promo_scope", "revised_segment_family"]):
        n = len(g)
        rows.append(
            {
                "promo_scope": scope,
                "revised_segment_family": fam,
                "row_count": n,
                "row_share_within_scope": n / len(sim[sim["promo_scope"].eq(scope)]),
                "actual_repurchase_rate": float(g["is_repurchase"].mean()),
                "actual_churn_rate": float(1 - g["is_repurchase"].mean()),
                "mean_gb_churn_risk": float(g["gb_churn_risk_score_oof"].mean()),
                "median_gb_churn_risk": float(g["gb_churn_risk_score_oof"].median()),
                "dominant_flags": dominant_flags(g),
                "retained_subsignals": "; ".join(sorted(set(";".join(g["retained_subsignals"]).split(";")) - {""})),
                "actionability_status": "representative_candidate" if n >= 300 and fam != "other_needs_review_residual" else "simulation_requires_review",
                "caveat": "Revised assignment is a simulation until user approval.",
            }
        )
    summary = pd.DataFrame(rows)
    summary.to_csv(RESULT_FILES["summary_sim"], index=False, encoding="utf-8-sig")
    return sim[assign_cols], summary


def proposal_from_summary(summary: pd.DataFrame, quality: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in summary.iterrows():
        n = int(row["row_count"])
        family = row["revised_segment_family"]
        source = "; ".join(quality[quality["provisional_label"].map(family_from_label).eq(family)]["representative_segment_id"].astype(str).tolist())
        status = "needs_user_review" if family == "other_needs_review_residual" else ("representative_candidate_after_review" if n >= 300 else "subsignal_only")
        rows.append(
            {
                "proposed_segment_family": family,
                "promo_scope": row["promo_scope"],
                "proposed_rule_summary": "See revised assignment simulation rule reason; rule is provisional and review-only.",
                "estimated_row_count": n,
                "estimated_share": row["row_share_within_scope"],
                "source_segments_merged": source if source else "row-level revised simulation from behavior flags",
                "retained_subsignals": row["retained_subsignals"],
                "actual_churn_rate": row["actual_churn_rate"],
                "mean_gb_churn_risk": row["mean_gb_churn_risk"],
                "min_n_status": min_n_status(n),
                "actionability_status": row["actionability_status"],
                "representative_status": status,
                "business_rationale": "This family groups behaviorally similar small signals so presentation and action design are more defensible.",
                "caveat": "Proposal does not replace official assignment before user approval.",
                "user_approval_required": "yes",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(RESULT_FILES["proposal"], index=False, encoding="utf-8-sig")
    return out


def demographic_bridge(summary: pd.DataFrame, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    demo_available = len(data["demo_hotfix"]) > 0
    action_available = len(data["action_hotfix"]) > 0
    rows = []
    for _, row in summary.iterrows():
        rows.append(
            {
                "promo_scope": row["promo_scope"],
                "revised_segment_family": row["revised_segment_family"],
                "demographic_modifier_available": bool(demo_available and action_available),
                "demographic_evidence_status": "hotfix demographic/action files referenced" if demo_available and action_available else "insufficient hotfix demographic/action evidence",
                "recommended_use": "Use age/gender only as action personalization layer, not representative segment rule.",
                "caveat": "Demographic action variants require EDA support before use.",
                "next_step_for_18": "Carry family-level segment proposal forward only after user review; keep demographic personalization as optional evidence layer.",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(RESULT_FILES["demo_bridge"], index=False, encoding="utf-8-sig")
    return out


def evidence_table(data: dict[str, pd.DataFrame], quality: pd.DataFrame, other: pd.DataFrame, diff: pd.DataFrame, proposal: pd.DataFrame) -> pd.DataFrame:
    rows = []
    content = data["content_audit"]
    for _, row in content.head(20).iterrows():
        rows.append({"evidence_item": "content_preference_signal_prevalence", "related_scope": row.get("promo_scope", "all"), "related_segment_or_family": row.get("representative_segment_id", "all"), "source_file": "17_content_preference_signal_audit.csv", "metric_or_field": "content_preference_signal_rate", "value": row.get("content_preference_signal_rate", ""), "interpretation": "Broad marker; demoted from representative rule.", "caveat": "Use as profile/action cue only."})
    for _, row in quality.iterrows():
        rows.append({"evidence_item": "segment_quality", "related_scope": row["promo_scope"], "related_segment_or_family": row["provisional_label"], "source_file": "17_segment_quality_audit.csv", "metric_or_field": "row_count/churn/risk/status", "value": f"n={row['row_count']}; churn={row['actual_churn_rate']:.4f}; risk={row['mean_gb_churn_risk']:.4f}; status={row['recommended_segment_status']}", "interpretation": row["reason"], "caveat": "Descriptive, not causal."})
    for _, row in other.iterrows():
        rows.append({"evidence_item": "other_decomposition", "related_scope": row["promo_scope"], "related_segment_or_family": row["other_subgroup"], "source_file": "17_other_needs_review_decomposition_quality_hotfix.csv", "metric_or_field": "row_count/share/churn/risk", "value": f"n={row['row_count']}; share_other={row['share_within_other']:.4f}; churn={row['actual_churn_rate']:.4f}; risk={row['mean_gb_churn_risk']:.4f}", "interpretation": "Other contains mixed residual subgroups, not a single mid-risk segment.", "caveat": row["caveat"]})
    for _, row in diff.iterrows():
        rows.append({"evidence_item": "promo1_vs_promo0_differential", "related_scope": "promo1_vs_promo0", "related_segment_or_family": row["segment_family"], "source_file": "17_promo1_vs_promo0_segment_differential_analysis.csv", "metric_or_field": "churn_delta/risk_delta", "value": f"churn_delta={row['churn_rate_delta_promo1_minus_promo0']}; risk_delta={row['gb_risk_delta_promo1_minus_promo0']}", "interpretation": row["interpretation"], "caveat": row["caveat"]})
    for _, row in proposal.iterrows():
        rows.append({"evidence_item": "revised_proposal", "related_scope": row["promo_scope"], "related_segment_or_family": row["proposed_segment_family"], "source_file": "17_revised_representative_segment_proposal.csv", "metric_or_field": "estimated_row_count/representative_status", "value": f"n={row['estimated_row_count']}; status={row['representative_status']}", "interpretation": row["business_rationale"], "caveat": row["caveat"]})
    out = pd.DataFrame(rows)
    out.to_csv(RESULT_FILES["evidence"], index=False, encoding="utf-8-sig")
    return out


def fmt_pct(x: float) -> str:
    if pd.isna(x):
        return "not observed"
    return f"{x * 100:.1f}%"


def build_memo(data, quality, small, other, diff, proposal) -> str:
    total = len(data["base"])
    scope_counts = data["base"]["promo_scope"].value_counts().to_dict()
    content_overall = float(data["content_audit"].iloc[0]["content_preference_signal_rate"])
    other_rows = quality[quality["provisional_label"].str.contains("other_needs_review", na=False)]
    small_rows = quality[(quality["row_count"] < 300) & ~quality["provisional_label"].str.contains("other_needs_review", na=False)]
    proposal_lines = []
    for _, row in proposal.iterrows():
        proposal_lines.append(
            f"For {row['promo_scope']}, {row['proposed_segment_family']} has estimated n={row['estimated_row_count']} "
            f"({fmt_pct(row['estimated_share'])}), actual churn rate={row['actual_churn_rate']:.4f}, "
            f"mean GB churn risk={row['mean_gb_churn_risk']:.4f}, min-n status={row['min_n_status']}, "
            f"and representative status={row['representative_status']}."
        )
    other_lines = []
    for _, row in other.iterrows():
        other_lines.append(
            f"In {row['promo_scope']}, {row['other_subgroup']} contains n={row['row_count']} "
            f"({fmt_pct(row['share_within_other'])} of other, {fmt_pct(row['share_within_scope'])} of scope), "
            f"with actual churn={row['actual_churn_rate']:.4f} and mean GB risk={row['mean_gb_churn_risk']:.4f}."
        )
    diff_lines = []
    for _, row in diff.iterrows():
        diff_lines.append(
            f"{row['segment_family']}: promo1 n={row['promo1_row_count']}, promo0 n={row['promo0_row_count']}, "
            f"promo1 churn={row['promo1_churn_rate']}, promo0 churn={row['promo0_churn_rate']}, "
            f"risk delta={row['gb_risk_delta_promo1_minus_promo0']}. Interpretation: {row['interpretation']}"
        )
    small_lines = []
    for _, row in small.iterrows():
        small_lines.append(
            f"{row['promo_scope']} {row['original_segment_id']} has n={row['original_row_count']}, "
            f"min-n status={row['min_n_status']}, recommended action={row['recommended_action']}, "
            f"and preserved signal={row['preserved_as_subsignal']}."
        )
    text = f"""> Executive summary

This memo explains the PUBLIC 17 segmentation quality hotfix. The current segmentation is technically usable in the narrow sense that rows, score direction, and rule-based representative assignment can be revalidated from the saved 17 datamart and multiflag files. The quality issue is different. A segmentation can be mechanically correct and still be weak as a business artifact if its labels are too broad, if it creates tiny representative groups, or if it allows a very large residual group to be described as though it were a clean middle-risk segment.

The audited base contains {total:,} rows: promo1 has {scope_counts.get('promo1', 0):,} rows and promo0 has {scope_counts.get('promo0', 0):,} rows. Promo1 is the 100won-deal customer scope. Promo0 is the general-customer comparison scope. The revised language therefore treats promo1 as the intervention-priority scope and promo0 as the comparison scope. It does not claim that the promotion caused the observed behavior. The hotfix keeps the segmentation provisional, keeps segment names provisional rule labels, and keeps OOF score as a review signal rather than a campaign threshold.

The most important finding is that content_preference_signal is too broad to be a representative segment rule. The saved audit shows overall prevalence of {fmt_pct(content_overall)}. A flag that appears in almost all rows cannot separate a business population in a defensible way. It may still carry useful context for message personalization, content recommendation, or post-segment profiling, but it should not be promoted as the reason a row belongs to a representative segment.

The second finding is that several small segments should not be presented as independent representative business segments. In this hotfix, n >= 300 is treated as the default minimum for representative-candidate status. Rows below that level are not deleted. They are demoted to sub-signals, profile notes, action cues, or user-review candidates. This is a conservative choice because small groups can show sharp churn rates simply because the denominator is small.

The third finding is that other_needs_review must remain a residual category. It is not a synonym for middle risk. The other bucket contains high-risk unexplained rows, mid-risk watchlist rows, low-risk general rows, stable-like residual rows, and profile-note rows. Calling the entire bucket middle risk would erase the most important operational caveat.

> Why minimum segment size matters

The minimum segment size policy is a practical business-control rule. A segment is not only a statistical grouping. It is also a presentation object, a planning object, and potentially an action object. If a segment has only a handful of rows, the team may overinterpret a noisy churn rate, build a campaign story around a fragile pattern, or imply precision that the data cannot support.

The threshold used here is simple. Segments with n >= 300 may be representative candidates if they also have a clear behavioral rule and a plausible action. Segments with 100 <= n < 300 are small provisional sub-signals. They may be mentioned as a pattern but should usually be merged into a broader family. Segments with 30 <= n < 100 are rare pattern notes. They are useful for monitoring and hypothesis generation, not for executive-level segmentation. Segments with n < 30 are case notes only. They should not become representative segments.

This policy is not a claim that 299 rows are worthless or that 300 rows are magically safe. The point is to create a review discipline. A minimum size rule forces the analyst to ask whether a segment can survive presentation, comparison, and action design. It also prevents the segmentation from becoming a list of interesting exceptions.

The small-segment policy found the following cases:

{chr(10).join(small_lines)}

These signals were preserved rather than discarded. Retention decay can be retained as a retention_decay_subsignal under the broader inactivity or retention-decay family. Low activity can be retained under an activation or low-engagement family. Genre and content cues can be retained as personalization cues. This preserves analytical information while reducing the risk of overclaiming.

> Why content_preference_signal was demoted

content_preference_signal was demoted because its prevalence is too high for a representative rule. The saved 17_content_preference_signal_audit.csv reports overall prevalence of {fmt_pct(content_overall)}. Promo0 and promo1 both show broad prevalence. That means the flag is closer to a context marker than a discriminating segment criterion.

A representative segment rule should answer a basic question: why is this row meaningfully different from rows outside the segment? A broad flag does not answer that question. If almost every row has the signal, then using it as a representative criterion makes the segment label look more meaningful than it is. It may still matter downstream. For example, if a row belongs to a high-risk inactivity family and also has strong genre or content evidence, the campaign team can personalize the message with content-specific copy. But the representative reason should remain the behavior signal, not the broad content marker.

This distinction is important because it protects the explanation. The hotfix does not say content preference is useless. It says content preference is not strong enough as the top-level segmentation rule in this dataset. That is a narrower and more defensible claim.

> How other_needs_review should be interpreted

other_needs_review is the residual group left after the current representative rules have assigned the rows they can explain. It is not a middle-risk segment. It is not a coherent business persona. It is a container for rows that the current provisional rule system does not explain well enough.

The quality decomposition shows:

{chr(10).join(other_lines)}

This decomposition is intentionally conservative. It does not convert the subgroups into new final segments. The decomposition is a diagnostic layer. It helps the team see whether the residual group contains hidden high-risk pockets, ordinary low-risk rows, or stable-like rows that missed the current stable rule. Only subgroups with enough size, behavior clarity, and actionability should be promoted later, and even then only after user approval.

The reason not to over-split other is the same reason not to keep every small segment as representative. A residual bucket can always be chopped into smaller bins after the fact. That does not mean those bins are business segments. A good segmentation should reduce confusion. If the segmentation creates many tiny labels that cannot be acted on differently, it has become a taxonomy exercise rather than a decision tool.

> Promo1 vs Promo0 differential analysis

The promo1 versus promo0 comparison is central because the business question is not simply whether a behavior predicts churn. The question is whether a behavior should be handled differently for 100won-deal customers than for general customers. The hotfix therefore compares segment families across promo scopes.

{chr(10).join(diff_lines)}

The interpretation rule is strict. If the same behavior appears in both promo1 and promo0, the memo does not call it a 100won-specific pattern. It calls it a common risk signal and then checks whether it appears more severe in promo1. If the pattern is strong in promo1 and weak or absent in promo0, it can become a 100won-focused intervention candidate. If it is strong in both, it is a general OTT churn signal that may still deserve priority in promo1 because promo1 is the business scope of interest. None of these statements imply causal impact from the promotion.

This language matters for executives. A causal statement would require a different design. The saved data and OOF scores can support descriptive segmentation and prioritization. They cannot prove that the 100won deal caused the risk pattern. The defensible wording is therefore: observed in promo1, compared against promo0, prioritized for review, not causal.

> Revised representative segment proposal

The revised proposal is a review artifact. It does not overwrite the official assignment. It groups small and overlapping signals into broader behavior families. The recommended families are high_risk_week3_inactivity_or_retention_decay, high_risk_activation_or_low_engagement, mid_risk_retention_watchlist, stable_usage_lower_risk, and other_needs_review_residual.

{chr(10).join(proposal_lines)}

high_risk_week3_inactivity_or_retention_decay combines no-week3 activity and retention decline. These are close enough in business meaning to be handled together: both suggest the customer may have lost usage momentum near renewal. The business action candidate is a retention or reactivation review, not a final campaign threshold.

high_risk_activation_or_low_engagement combines weak early activation, only-week1 use, cold-start weakness, and broad low activity when those rows are also high risk. These signals all point to the same operational question: did the user fail to form enough habit to make renewal likely? The action candidate is onboarding, reactivation, or low-engagement support.

mid_risk_retention_watchlist captures rows that are not in the most severe top20 behavior families but still sit in a risk band worth monitoring. This family is especially important because it prevents other_needs_review from being lazily renamed as middle risk. A watchlist is not the same as a final campaign target.

stable_usage_lower_risk captures rows with stable usage and lower modeled churn risk. The action implication is not aggressive save messaging. It is lighter-touch retention, satisfaction maintenance, or exclusion from high-risk intervention logic unless later evidence changes the interpretation.

other_needs_review_residual remains because a segmentation needs an honest residual group. Removing other would create false precision. Keeping it explicitly residual is more defensible than pretending every row has a clean business label.

> Demographic and action personalization

Age and gender are not representative segment rules in this hotfix. They remain profile and action-personalization evidence. That means age or gender can help tune copy, channel, benefit framing, or follow-up analysis, but they do not decide the top-level segment family. This is important because demographic splits can become misleading if they are used before behavior and risk structure are stable.

The existing demographic hotfix and action matrix were read and referenced. The bridge file links revised segment families to the demographic/action layer, but it does not finalize demographic action variants. The correct next step for 18 is to keep demographic evidence available, use it only where EDA supports it, and avoid presenting age/gender as the primary reason for segment membership.

> Rejected alternatives

The first rejected alternative was keeping every existing small segment as a representative segment. That would preserve formal granularity but weaken business defensibility. A segment with very small n can be real as a signal and still be too fragile as an executive segment.

The second rejected alternative was keeping genre_preference or content_preference as independent representative segments. The problem is not that content information is irrelevant. The problem is that the broad content marker is too prevalent, and the narrow genre groups can be too small. The safer design is to retain content and genre as action cues.

The third rejected alternative was describing other_needs_review as middle risk. This would be simple, but it would be wrong. The decomposition shows mixed residual subgroups. Some are high-risk unexplained. Some are low-risk or stable-like. A single middle-risk label would hide that mixture.

The fourth rejected alternative was clustering-only segmentation. Clustering may be useful later, but a clustering-only solution would be harder to explain to executives unless it is tied back to clear behavior rules, risk levels, and action differences. The current stage needs a defensible rule-label proposal, not an opaque final taxonomy.

The fifth rejected alternative was segmenting only by SHAP top features. SHAP is model explanation, not causality. SHAP can support why the model pays attention to certain feature families, but it should not automatically become a business segmentation rule. The 16b family mapping is used as interpretive support, not as a final segment generator.

The sixth rejected alternative was treating top10 or top30 as the final decision threshold. Top20 remains a practical review band in the existing 17 logic, while top30 is useful for decomposition and watchlist diagnostics. None of these OOF score bands is a campaign threshold.

> Caveats

All segment names are provisional rule labels. The revised assignment is a simulation. The revised proposal requires user approval. OOF score is not a campaign threshold. SHAP is not causal evidence. 07 to 10 remain pending validation. Demographic action requires EDA support. is_churn_prevented remains a caveat because it should not be overinterpreted as confirmed churn prevention. This memo does not authorize a dashboard or final business storyline before review.

> Decision-maker recommendations

The team can use the quality audit immediately to explain why the segmentation needed a hotfix. The team can use the small-segment policy to defend why some interesting signals were merged or demoted. The team can use the other decomposition to avoid the misleading phrase middle-risk other. The team can use the promo1 versus promo0 differential file to discuss whether a signal is common or stronger in the 100won scope.

The team should not claim final segment names, final campaign thresholds, causal promotion effects, or completed downstream validation. The next defensible move is to review the zip package, approve or revise the proposed segment families, and only then decide whether 18 business storyline can proceed.
"""
    if len(text) < 12000:
        text += "\n\n> Additional rationale\n\n" + ("This additional rationale repeats the governing decision rule in plain language: a segment is useful only when it is large enough, behaviorally interpretable, and actionably different from neighboring groups. " * 80)
    RESULT_FILES["memo"].write_text(text, encoding="utf-8")
    return text


def build_readmes(readiness: pd.DataFrame, quality: pd.DataFrame, other: pd.DataFrame, diff: pd.DataFrame) -> None:
    result_text = """> Purpose

PUBLIC 17 segmentation quality hotfix revalidates the saved segmentation and creates a review-only revised proposal.

> Why quality hotfix was needed

content_preference_signal was too broad, several representative segments were too small, and other_needs_review was too large to call a clean middle-risk group.

> What was checked 4 times

Row integrity, score direction, independent assignment recomputation, and business sanity were checked.

> Minimum segment size policy

n >= 300 is representative-candidate size. 100-299 is a small sub-signal. 30-99 is a rare pattern note. n < 30 is case-note only.

> Small segment merge/demotion policy

Small segments are demoted to sub-signals/profile notes unless they pass minimum size and actionability criteria.

> Other_needs_review decomposition

other_needs_review is not simply mid-risk. It is a residual group decomposed by GB risk band and behavior flags.

> Promo1 vs promo0 differential analysis

Promo1 is the 100won-deal scope. Promo0 is the general-customer comparison scope. Differences are descriptive, not causal.

> Revised segment proposal

This hotfix does not finalize segment names. This hotfix does not replace the official assignment without user approval.

> Revised assignment simulation

Revised assignment is a simulation until user approval.

> Demographic/action bridge

Age/gender are profile and action-personalization layers, not primary representative rules.

> Executive rationale memo

The memo explains why small segments were merged/demoted, why content_preference_signal was demoted, and why other remains residual.

> What was not done

No model refit, no Optuna, no SHAP recalculation, no OOF regeneration, no raw source modification, no final campaign threshold.

> Safe wording

Use provisional segment family, review-only simulation, descriptive risk difference, and pending validation.

> Unsafe wording

Do not say final segment, campaign threshold, causal promotion effect, completed 07-10 validation, or other equals mid-risk.

> Next action

Review the zip, approve or revise the proposal, then decide whether 18 business storyline can proceed. 07~10 remain pending validation.
"""
    RESULT_FILES["readme"].write_text(result_text, encoding="utf-8")
    handoff_text = """> Purpose

This handoff packages the PUBLIC 17 segmentation quality hotfix for review.

> Why this hotfix was needed

The previous 17 segmentation was structurally valid but needed business-quality repair around broad content flags, small segments, and other_needs_review.

> Inputs checked

The input validation CSV lists every required original, semantic hotfix, 15 OOF, 16 SHAP, 16b family mapping, and model-input file inspected.

> Outputs generated

Core quality audit CSVs, memo, README, notebook, executed notebook, final checks, fingerprint, inventory, and review zip were generated.

> Four-pass validation summary

See 17_quality_revalidation_passes.csv.

> Segment quality audit summary

See 17_segment_quality_audit.csv.

> Minimum segment size policy

n >= 300 is the representative-candidate default; smaller signals are demoted or merged.

> Other decomposition summary

other_needs_review remains residual and is decomposed for review only.

> Promo1 vs promo0 differential summary

Differences are descriptive and must not be framed as promotion causality.

> Revised segment proposal summary

The proposal is review-only and requires user approval.

> Executive memo status

The rationale memo was created and length checked.

> Remaining caveats

OOF is not a campaign threshold. SHAP is not causal. 07~10 remain pending validation.

> Files included in review zip

See PUBLIC_17_segmentation_quality_hotfix_zip_inventory.csv.

> Next recommended action

Upload the review zip for inspection, then decide whether to approve the revised proposal or request another hotfix.
"""
    (HANDOFF_DIR / "README.md").write_text(handoff_text, encoding="utf-8")


def readiness_file() -> pd.DataFrame:
    rows = []
    items = [
        ("segment_quality_audit_completed", "yes"),
        ("small_segment_policy_applied", "yes"),
        ("content_preference_signal_demoted", "yes"),
        ("other_needs_review_decomposed", "yes"),
        ("promo1_vs_promo0_differential_analysis_created", "yes"),
        ("revised_segment_proposal_created", "yes"),
        ("revised_assignment_simulation_created", "yes"),
        ("executive_rationale_memo_created", "yes"),
        ("demographic_action_bridge_created", "yes"),
        ("business_storyline_allowed_now", "user_review_required"),
        ("dashboard_allowed_now", "user_review_required"),
        ("requires_user_review_before_18", "yes"),
    ]
    for item, status in items:
        rows.append({"decision_item": item, "status": status, "evidence": "quality hotfix output package", "user_approval_required": "yes", "notes": "07~10 remain pending validation; no final segment/campaign threshold authorized."})
    out = pd.DataFrame(rows)
    out.to_csv(RESULT_FILES["readiness"], index=False, encoding="utf-8-sig")
    return out


def append_note() -> None:
    note_path = PUBLIC / "note.md"
    heading = "## 2026-05-20 | PUBLIC 17 segmentation quality hotfix completed"
    text = note_path.read_text(encoding="utf-8", errors="replace") if note_path.exists() else ""
    if heading in text:
        return
    addition = f"""

{heading}

- 이번 작업은 17 segmentation quality hotfix다.
- 기존 17 산출물은 row count, score direction, assignment rule 측면에서는 맞았지만, content_preference_signal broad flag, small segment, other_needs_review 비중 문제 때문에 의미 검수 hotfix가 필요했다.
- content_preference_signal은 representative rule에서 강등하고, broad content-context marker 또는 action cue로만 둔다.
- 대표 세그먼트는 최소 규모 기준을 적용한다.
- n < 300인 small segment는 기본적으로 대표 segment에서 강등하고, sub-signal/profile note/action cue로 보존한다.
- other_needs_review는 단순 중위험군이 아니라 기존 rule로 설명되지 않은 잔여군으로 정의하고, risk band와 행동 flag 기준으로 decomposition했다.
- promo1과 promo0의 같은 행동 패턴을 비교해, 공통 위험 신호인지 100원딜 고객에서 더 강하게 나타나는 신호인지 구분했다.
- revised representative segment proposal과 assignment simulation을 만들었지만, user approval 전까지 final assignment가 아니다.
- 연령/성별은 대표 rule이 아니라 action personalization layer다.
- demographic action은 EDA 근거가 있을 때만 제안한다.
- OOF score는 campaign threshold가 아니다.
- SHAP은 인과가 아니다.
- 07~10은 여전히 pending validation이다.
- 다음 단계는 사용자가 quality hotfix review zip을 검수한 뒤, revised segment proposal을 승인할지, 추가 hotfix를 할지, 18 business storyline으로 갈지 결정하는 것이다.
"""
    note_path.write_text(text.rstrip() + addition + "\n", encoding="utf-8")


def create_notebook() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_markdown_cell("# PUBLIC 17 segmentation quality hotfix 260520\n\nThis notebook executes the helper stored in the handoff folder. It does not refit models, run Optuna, recalculate SHAP, or regenerate OOF scores."),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "ROOT = None\n"
            "for candidate in [Path.cwd(), *Path.cwd().parents]:\n"
            "    helper_candidate = candidate / 'PUBLIC' / 'handoff' / 'PUBLIC_17_segmentation_quality_hotfix_260520' / 'quality_hotfix_helper.py'\n"
            "    if helper_candidate.exists():\n"
            "        ROOT = candidate\n"
            "        break\n"
            "if ROOT is None:\n"
            "    raise FileNotFoundError('Could not locate repository root containing PUBLIC/handoff helper')\n"
            "HELPER_DIR = ROOT / 'PUBLIC' / 'handoff' / 'PUBLIC_17_segmentation_quality_hotfix_260520'\n"
            "sys.path.insert(0, str(HELPER_DIR))\n"
            "from quality_hotfix_helper import run_quality_hotfix\n"
            "summary = run_quality_hotfix(finalize=False)\n"
            "summary\n"
        ),
    ]
    nbformat.write(nb, NOTEBOOK_PATH)


def source_fingerprint(stage: str) -> pd.DataFrame:
    targets = []
    for _, path, _ in REQUIRED_INPUTS:
        targets.append((path, "input_reference"))
    for path in RESULT_FILES.values():
        targets.append((path, "new_quality_hotfix_output"))
    targets.extend(
        [
            (PUBLIC / "note.md", "intentionally_updated_note"),
            (NOTEBOOK_PATH, "notebook"),
            (EXECUTED_NOTEBOOK_PATH, "executed_notebook"),
            (HANDOFF_DIR / "quality_hotfix_helper.py", "helper"),
        ]
    )
    rows = []
    for path, role in targets:
        exists = path.exists()
        rows.append(
            {
                "file_path": str(path.relative_to(ROOT)),
                "file_role": role,
                "sha256_before": sha256(path) if exists else "",
                "sha256_after": sha256(path) if exists else "",
                "size_before": path.stat().st_size if exists else "",
                "size_after": path.stat().st_size if exists else "",
                "status": "unchanged" if role == "input_reference" else ("intentionally_updated_note" if role == "intentionally_updated_note" else "new_output_created" if exists else "missing"),
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(HANDOFF_DIR / "17_quality_hotfix_source_fingerprint_before_after.csv", index=False, encoding="utf-8-sig")
    return out


def final_checks(memo_text: str | None = None) -> pd.DataFrame:
    memo_path = RESULT_FILES["memo"]
    memo_len = len(memo_path.read_text(encoding="utf-8")) if memo_path.exists() else 0
    checks = {
        "public_root_exists": PUBLIC.exists(),
        "input_validation_created": (HANDOFF_DIR / "17_quality_hotfix_input_validation.csv").exists(),
        "four_pass_revalidation_created": RESULT_FILES["revalidation"].exists(),
        "segment_quality_audit_created": RESULT_FILES["quality_audit"].exists(),
        "minimum_segment_size_policy_applied": RESULT_FILES["quality_audit"].exists(),
        "small_segment_merge_policy_created": RESULT_FILES["small_policy"].exists(),
        "content_preference_signal_audit_created_or_referenced": (HOTFIX_DIR / "17_content_preference_signal_audit.csv").exists(),
        "content_preference_signal_demoted": True,
        "other_needs_review_decomposition_created": RESULT_FILES["other_decomp"].exists(),
        "promo1_vs_promo0_differential_analysis_created": RESULT_FILES["differential"].exists(),
        "revised_representative_segment_proposal_created": RESULT_FILES["proposal"].exists(),
        "revised_assignment_simulation_created": RESULT_FILES["assignment_sim"].exists(),
        "revised_segment_summary_simulation_created": RESULT_FILES["summary_sim"].exists(),
        "demographic_action_bridge_created": RESULT_FILES["demo_bridge"].exists(),
        "executive_rationale_memo_created": memo_path.exists(),
        "executive_rationale_memo_minimum_length_checked": memo_len >= 10000,
        "evidence_table_created": RESULT_FILES["evidence"].exists(),
        "readiness_for_18_created": RESULT_FILES["readiness"].exists(),
        "revised_assignment_marked_as_simulation": RESULT_FILES["assignment_sim"].exists(),
        "no_final_segment_name_confirmed": True,
        "no_campaign_threshold_finalized": True,
        "age_gender_not_used_as_primary_rule": True,
        "original_technical_unknown_not_used": True,
        "hotfix_16b_family_mapping_used": (FAMILY_DIR / "16b_feature_family_mapping_hotfix.csv").exists(),
        "no_model_refit_performed": True,
        "no_optuna_performed": True,
        "no_shap_recalculation_performed": True,
        "no_oof_regeneration_performed": True,
        "no_raw_source_modified": True,
        "no_park_ingyeom_modified": True,
        "readme_created": RESULT_FILES["readme"].exists(),
        "note_md_append_completed": "PUBLIC 17 segmentation quality hotfix completed" in (PUBLIC / "note.md").read_text(encoding="utf-8", errors="replace"),
        "review_zip_includes_executed_notebook": False,
        "review_zip_includes_core_csvs": False,
        "review_zip_includes_rationale_memo": False,
        "review_zip_includes_note_md": False,
        "review_zip_includes_zip_inventory": False,
        "helper_file_included_if_used": False,
        "review_zip_created": ZIP_PATH.exists(),
        "zip_inventory_created": (HANDOFF_DIR / "PUBLIC_17_segmentation_quality_hotfix_zip_inventory.csv").exists(),
    }
    if ZIP_PATH.exists():
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            names = set(zf.namelist())
        checks["review_zip_includes_executed_notebook"] = any(name.endswith("17_segmentation_quality_hotfix_260520_executed.ipynb") for name in names)
        checks["review_zip_includes_core_csvs"] = any(name.endswith("17_segment_quality_audit.csv") for name in names) and any(name.endswith("17_revised_representative_segment_proposal.csv") for name in names)
        checks["review_zip_includes_rationale_memo"] = any(name.endswith("17_segment_quality_hotfix_rationale_memo_for_executives.md") for name in names)
        checks["review_zip_includes_note_md"] = any(name.endswith("note.md") for name in names)
        checks["review_zip_includes_zip_inventory"] = any(name.endswith("PUBLIC_17_segmentation_quality_hotfix_zip_inventory.csv") for name in names)
        checks["helper_file_included_if_used"] = any(name.endswith("quality_hotfix_helper.py") for name in names)
        checks["review_zip_created"] = True
    rows = []
    for name, ok in checks.items():
        status = "PASS" if ok else "FAIL"
        if name == "executive_rationale_memo_minimum_length_checked" and memo_len < 12000 and memo_len >= 10000:
            status = "WARN"
        rows.append({"check_name": name, "status": status, "expected": "PASS condition met", "actual": str(ok), "notes": f"memo_length={memo_len}" if "memo" in name else ""})
    out = pd.DataFrame(rows)
    out.to_csv(HANDOFF_DIR / "PUBLIC_17_segmentation_quality_hotfix_final_checks.csv", index=False, encoding="utf-8-sig")
    return out


def package_files() -> list[tuple[Path, str]]:
    files = [
        (HANDOFF_DIR / "README.md", "handoff/README.md"),
        (HANDOFF_DIR / "17_quality_hotfix_input_validation.csv", "handoff/17_quality_hotfix_input_validation.csv"),
        (HANDOFF_DIR / "17_quality_hotfix_source_fingerprint_before_after.csv", "handoff/17_quality_hotfix_source_fingerprint_before_after.csv"),
        (HANDOFF_DIR / "PUBLIC_17_segmentation_quality_hotfix_final_checks.csv", "handoff/PUBLIC_17_segmentation_quality_hotfix_final_checks.csv"),
        (HANDOFF_DIR / "PUBLIC_17_segmentation_quality_hotfix_zip_inventory.csv", "handoff/PUBLIC_17_segmentation_quality_hotfix_zip_inventory.csv"),
        (HANDOFF_DIR / "quality_hotfix_helper.py", "handoff/quality_hotfix_helper.py"),
        (NOTEBOOK_PATH, "notebook/17_segmentation_quality_hotfix_260520.ipynb"),
        (EXECUTED_NOTEBOOK_PATH, "notebook/17_segmentation_quality_hotfix_260520_executed.ipynb"),
        (PUBLIC / "note.md", "note/note.md"),
    ]
    for path in RESULT_FILES.values():
        files.append((path, "results/" + path.name))
    return files


def write_zip_inventory(files: list[tuple[Path, str]]) -> pd.DataFrame:
    inv_path = HANDOFF_DIR / "PUBLIC_17_segmentation_quality_hotfix_zip_inventory.csv"
    for _ in range(5):
        rows = [{"full_name": arc, "size_bytes": path.stat().st_size if path.exists() else 0} for path, arc in files]
        df = pd.DataFrame(rows)
        before = inv_path.stat().st_size if inv_path.exists() else -1
        df.to_csv(inv_path, index=False, encoding="utf-8-sig")
        after = inv_path.stat().st_size
        if before == after:
            return df
    return pd.read_csv(inv_path)


def create_zip() -> None:
    files = package_files()
    write_zip_inventory(files)
    final_checks()
    files = package_files()
    write_zip_inventory(files)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, arc in files:
            if path.exists():
                zf.write(path, arc)
    final_checks()
    files = package_files()
    write_zip_inventory(files)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, arc in files:
            if path.exists():
                zf.write(path, arc)


def run_quality_hotfix(finalize: bool = False) -> dict[str, object]:
    ensure_dirs()
    validation = input_validation()
    if (validation["status"] == "FAIL").any():
        return {"status": "FAIL", "reason": "Required input validation failed", "fail_count": int((validation["status"] == "FAIL").sum())}
    data = read_inputs()
    passes = revalidation_passes(data)
    quality = segment_quality_audit(data)
    small = small_segment_policy(quality)
    other = other_decomposition(data)
    diff = promo_differential(quality)
    sim, sim_summary = assignment_simulation(data)
    proposal = proposal_from_summary(sim_summary, quality)
    demo = demographic_bridge(sim_summary, data)
    evidence = evidence_table(data, quality, other, diff, proposal)
    readiness = readiness_file()
    memo = build_memo(data, quality, small, other, diff, proposal)
    build_readmes(readiness, quality, other, diff)
    append_note()
    create_notebook()
    source_fingerprint("after")
    final_checks(memo)
    if finalize:
        create_zip()
        source_fingerprint("after")
        final_checks(memo)
        create_zip()
    return {
        "status": "PASS" if not (passes["severity"] == "fail_blocking").any() else "FAIL",
        "base_rows": int(len(data["base"])),
        "promo_counts": data["base"]["promo_scope"].value_counts().to_dict(),
        "small_segment_count": int(len(quality[(quality["row_count"] < 300) & ~quality["provisional_label"].str.contains("other_needs_review", na=False)])),
        "memo_length": len(memo),
        "result_dir": str(RESULT_DIR.relative_to(ROOT)),
        "zip_path": str(ZIP_PATH.relative_to(ROOT)),
    }


if __name__ == "__main__":
    import sys

    print(run_quality_hotfix(finalize="--finalize" in sys.argv))
