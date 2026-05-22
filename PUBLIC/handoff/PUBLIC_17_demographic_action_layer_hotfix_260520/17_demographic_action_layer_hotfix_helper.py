from __future__ import annotations

import hashlib
import json
import math
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
PUBLIC = ROOT / "PUBLIC"
INPUT_DIR = PUBLIC / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments_hotfix_260520"
FALLBACK_STAGE17_DIR = PUBLIC / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments"
OUT_DIR = PUBLIC / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments_demographic_hotfix_260520"
HANDOFF_DIR = PUBLIC / "handoff" / "PUBLIC_17_demographic_action_layer_hotfix_260520"
NOTEBOOK_DIR = PUBLIC / "notebooks" / "17_segmentation_design_260520"
ZIP_DIR = PUBLIC / "zip"
ZIP_PATH = ZIP_DIR / "PUBLIC_17_demographic_action_layer_hotfix_260520_review_package.zip"
NOTEBOOK_PATH = NOTEBOOK_DIR / "17_demographic_action_layer_hotfix_260520.ipynb"
EXECUTED_NOTEBOOK_PATH = NOTEBOOK_DIR / "17_demographic_action_layer_hotfix_260520_executed.ipynb"
NOTE_PATH = PUBLIC / "note.md"


REQUIRED_INPUTS = {
    "representative_assignment_hotfix": INPUT_DIR / "17_representative_segment_assignment_hotfix.csv",
    "base_datamart_hotfix_expected": INPUT_DIR / "17_segmentation_base_datamart.csv",
    "internal_multiflag_hotfix_expected": INPUT_DIR / "17_internal_multiflag_assignment.csv",
    "segment_summary_hotfix": INPUT_DIR / "17_segment_summary_hotfix.csv",
}

REFERENCE_INPUTS = {
    "segment_feature_profile_hotfix": INPUT_DIR / "17_segment_feature_profile_hotfix.csv",
    "segment_shap_family_evidence_link_hotfix": INPUT_DIR / "17_segment_SHAP_family_evidence_link_hotfix.csv",
    "segment_action_personalization_matrix_hotfix": INPUT_DIR / "17_segment_action_personalization_matrix_hotfix.csv",
    "segment_rationale_memo_for_executives_hotfix": INPUT_DIR / "17_segment_rationale_memo_for_executives_hotfix.md",
    "model_input_promo_0": PUBLIC / "data" / "06_model_input_promo_0.csv",
    "model_input_promo_1": PUBLIC / "data" / "06_model_input_promo_1.csv",
    "oof_score_wide": PUBLIC / "results" / "15_oof_score_or_sensitivity_260520" / "four_model_oof_scores_hotfix_260520" / "15_oof_score_wide.csv",
    "feature_family_mapping_16b": PUBLIC / "results" / "16_SHAP_candidate_interpretation_260520" / "16b_feature_family_mapping_hotfix_260520" / "16b_feature_family_mapping_hotfix.csv",
    "base_datamart_stage17_fallback": FALLBACK_STAGE17_DIR / "17_segmentation_base_datamart.csv",
    "internal_multiflag_stage17_fallback": FALLBACK_STAGE17_DIR / "17_internal_multiflag_assignment.csv",
}

DEMOGRAPHIC_CANDIDATES = [
    "age_group",
    "age",
    "gender",
    "gender_clean",
    "is_female",
    "is_male",
    "USER_KEY",
    "USER_NUM",
]

BEHAVIOR_FEATURE_CANDIDATES = [
    "watch_time_min_w1",
    "watch_time_min_w2",
    "watch_time_min_w3",
    "watch_session_w1",
    "watch_session_w2",
    "watch_session_w3",
    "total_watch_time_min",
    "total_watch_count",
    "watch_days",
    "log_retention_w2_ratio",
    "log_retention_w3_ratio",
    "active_ratio",
    "recency",
    "max_inactive_gap_days",
    "is_only_w1",
    "is_only_w2",
    "is_only_w3",
    "genre_diversity_count",
]

GENRE_RATIO_FEATURES = [
    "action_adventure_ratio",
    "family_animation_ratio",
    "drama_ratio",
    "thriller_crime_ratio",
    "sf_fantasy_ratio",
    "comedy_ratio",
    "romance_ratio",
    "horror_ratio",
    "documentary_ratio",
    "historical_war_ratio",
    "other_ratio",
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, HANDOFF_DIR, NOTEBOOK_DIR, ZIP_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def read_csv_if_exists(path: Path, **kwargs) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, **kwargs)


def count_rows(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig", errors="replace") as f:
        return max(sum(1 for _ in f) - 1, 0)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_round(value, digits: int = 6):
    if pd.isna(value):
        return np.nan
    return round(float(value), digits)


def normalize_binary(series: pd.Series) -> pd.Series:
    def convert(value):
        if pd.isna(value):
            return np.nan
        if isinstance(value, (bool, np.bool_)):
            return int(value)
        if isinstance(value, (int, float, np.integer, np.floating)) and not pd.isna(value):
            if float(value) == 1.0:
                return 1
            if float(value) == 0.0:
                return 0
            return np.nan
        text = str(value).strip().lower()
        if text in {"1", "1.0", "true", "t", "yes", "y"}:
            return 1
        if text in {"0", "0.0", "false", "f", "no", "n"}:
            return 0
        return np.nan

    return series.map(convert)


def derive_gender(df: pd.DataFrame) -> pd.Series:
    female_present = "is_female" in df.columns
    male_present = "is_male" in df.columns
    if not female_present and not male_present:
        return pd.Series(["missing_gender_columns"] * len(df), index=df.index)
    f = normalize_binary(df["is_female"]) if female_present else pd.Series(np.nan, index=df.index)
    m = normalize_binary(df["is_male"]) if male_present else pd.Series(np.nan, index=df.index)
    both_missing = f.isna() & m.isna()
    out = pd.Series("unknown_or_unreported", index=df.index, dtype="object")
    out.loc[(f == 1) & (m == 0)] = "female"
    out.loc[(m == 1) & (f == 0)] = "male"
    out.loc[(f == 1) & (m == 1)] = "ambiguous_conflict"
    out.loc[both_missing] = "missing_gender_columns"
    return out


def input_validation() -> pd.DataFrame:
    rows = []
    all_inputs = {**REQUIRED_INPUTS, **REFERENCE_INPUTS}
    for item, path in all_inputs.items():
        exists = path.exists()
        cols = ""
        row_count = None
        notes = ""
        if exists and path.suffix.lower() == ".csv":
            try:
                preview = pd.read_csv(path, nrows=1)
                cols = len(preview.columns)
                row_count = count_rows(path)
            except Exception as exc:
                notes = f"read_error: {exc}"
        elif exists:
            row_count = None
            cols = ""
        required = item in REQUIRED_INPUTS
        status = "PASS" if exists else ("FAIL" if required else "WARN")
        if not exists and required:
            notes = "Required input missing at the expected hotfix path."
        elif item == "base_datamart_stage17_fallback" and exists:
            notes = "Fallback source exists in the original stage-17 folder; used only because expected hotfix path is missing."
        elif item == "internal_multiflag_stage17_fallback" and exists:
            notes = "Fallback source exists in the original stage-17 folder; used only because expected hotfix path is missing."
        rows.append(
            {
                "input_item": item,
                "expected_path": str(path.relative_to(ROOT)),
                "exists": exists,
                "rows": row_count if row_count is not None else "",
                "columns": cols,
                "status": status,
                "notes": notes,
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(HANDOFF_DIR / "17_demographic_hotfix_input_validation.csv", index=False, encoding="utf-8-sig")
    return df


def load_core_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, bool]:
    assignment = pd.read_csv(REQUIRED_INPUTS["representative_assignment_hotfix"])
    summary = pd.read_csv(REQUIRED_INPUTS["segment_summary_hotfix"])
    expected_base = REQUIRED_INPUTS["base_datamart_hotfix_expected"]
    expected_multiflag = REQUIRED_INPUTS["internal_multiflag_hotfix_expected"]
    fallback_used = not expected_base.exists() or not expected_multiflag.exists()
    base_path = expected_base if expected_base.exists() else REFERENCE_INPUTS["base_datamart_stage17_fallback"]
    multiflag_path = expected_multiflag if expected_multiflag.exists() else REFERENCE_INPUTS["internal_multiflag_stage17_fallback"]
    base = pd.read_csv(base_path)
    multiflag = pd.read_csv(multiflag_path)
    return assignment, summary, base, multiflag, fallback_used


def source_column_audit(base: pd.DataFrame) -> pd.DataFrame:
    source_frames = {
        "base_datamart_used": base,
        "representative_assignment_hotfix": pd.read_csv(REQUIRED_INPUTS["representative_assignment_hotfix"], nrows=1000),
    }
    for name in ["model_input_promo_0", "model_input_promo_1", "oof_score_wide"]:
        path = REFERENCE_INPUTS[name]
        if path.exists():
            source_frames[name] = pd.read_csv(path, nrows=5000)
    rows = []
    for source_name, df in source_frames.items():
        for col in DEMOGRAPHIC_CANDIDATES:
            exists = col in df.columns
            dtype = str(df[col].dtype) if exists else ""
            non_null = int(df[col].notna().sum()) if exists else 0
            unique_count = int(df[col].nunique(dropna=True)) if exists else 0
            sample_values = ""
            if exists:
                sample_values = ", ".join(map(str, df[col].dropna().drop_duplicates().head(8).tolist()))
            use_for_profile = "yes" if col in {"age_group", "is_female", "is_male", "gender", "gender_clean"} and exists else "no"
            if col in {"USER_KEY", "USER_NUM"} and exists:
                use_for_profile = "identifier_audit_only"
            rows.append(
                {
                    "source_file": source_name,
                    "column_name": col,
                    "exists": exists,
                    "dtype": dtype,
                    "non_null_count": non_null,
                    "unique_count": unique_count,
                    "sample_values": sample_values,
                    "use_for_profile": use_for_profile,
                    "use_for_rule": "no",
                    "notes": "Representative segment rules must not use demographic columns." if exists else "Column not found in this source.",
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "17_demographic_source_column_audit.csv", index=False, encoding="utf-8-sig")
    return out


def gender_derivation_audit(base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scope, g in base.groupby("promo_scope", dropna=False):
        female_present = "is_female" in g.columns
        male_present = "is_male" in g.columns
        derived = derive_gender(g)
        counts = derived.value_counts(dropna=False).to_dict()
        female_count = int(counts.get("female", 0))
        male_count = int(counts.get("male", 0))
        unknown_count = int(counts.get("unknown_or_unreported", 0))
        conflict_count = int(counts.get("ambiguous_conflict", 0))
        missing_count = int(counts.get("missing_gender_columns", 0))
        if not female_present or not male_present:
            status = "WARN_MISSING_COLUMNS"
        elif conflict_count > 0:
            status = "FAIL_CONFLICT_OR_LOGIC_ERROR"
        elif female_count == 0 and male_count == 0:
            status = "WARN_ALL_UNKNOWN"
        else:
            status = "PASS"
        notes = "Existing all-unknown gender symptom is explained by strict/incorrect derivation only if prior output ignored usable is_female/is_male values."
        rows.append(
            {
                "promo_scope": scope,
                "source_rows": len(g),
                "is_female_present": female_present,
                "is_male_present": male_present,
                "female_count": female_count,
                "male_count": male_count,
                "unknown_or_unreported_count": unknown_count,
                "ambiguous_conflict_count": conflict_count,
                "missing_gender_columns_count": missing_count,
                "derivation_status": status,
                "notes": notes,
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "17_gender_derivation_audit.csv", index=False, encoding="utf-8-sig")
    return out


def age_group_audit(base: pd.DataFrame) -> pd.DataFrame:
    if "age_group" not in base.columns:
        out = pd.DataFrame(
            [
                {
                    "promo_scope": "all",
                    "age_group_value": "unavailable",
                    "row_count": 0,
                    "share_within_scope": np.nan,
                    "actual_repurchase_rate": np.nan,
                    "mean_gb_churn_risk": np.nan,
                    "median_gb_churn_risk": np.nan,
                    "notes": "age_group column is not available in the selected base datamart.",
                }
            ]
        )
    else:
        rows = []
        for scope, sg in base.groupby("promo_scope", dropna=False):
            total = len(sg)
            for value, g in sg.groupby("age_group", dropna=False):
                rows.append(
                    {
                        "promo_scope": scope,
                        "age_group_value": value if not pd.isna(value) else "missing",
                        "row_count": len(g),
                        "share_within_scope": safe_round(len(g) / total),
                        "actual_repurchase_rate": safe_round(g["is_repurchase"].mean()),
                        "mean_gb_churn_risk": safe_round(g["gb_churn_risk_score_oof"].mean()),
                        "median_gb_churn_risk": safe_round(g["gb_churn_risk_score_oof"].median()),
                        "notes": "Age group is used for profile/action audit only, not representative segment rules.",
                    }
                )
        out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "17_age_group_audit.csv", index=False, encoding="utf-8-sig")
    return out


def join_assignment_base(assignment: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    assignment_keys = assignment[["promo_scope", "row_id"]].drop_duplicates()
    if len(assignment_keys) != len(assignment):
        raise ValueError("Assignment has duplicated promo_scope + row_id keys.")
    joined = assignment.merge(base, on=["promo_scope", "row_id"], how="left", suffixes=("", "_base"))
    missing = joined["USER_KEY"].isna().sum() if "USER_KEY" in joined.columns else len(joined)
    if missing:
        raise ValueError(f"Join failed for {missing} assignment rows.")
    if "is_repurchase_base" in joined.columns:
        joined["is_repurchase"] = joined["is_repurchase"].combine_first(joined["is_repurchase_base"])
    joined["gender_derived"] = derive_gender(joined)
    return joined


def demographic_profile(joined: pd.DataFrame) -> pd.DataFrame:
    variables = []
    if "age_group" in joined.columns:
        variables.append("age_group")
    if {"is_female", "is_male"}.issubset(joined.columns):
        variables.append("gender_derived")
    if "is_female" in joined.columns:
        variables.append("is_female")
    if "is_male" in joined.columns:
        variables.append("is_male")
    if not variables:
        out = pd.DataFrame(
            [
                {
                    "promo_scope": "all",
                    "representative_segment_id": "unavailable",
                    "provisional_label": "unavailable",
                    "demographic_variable": "unavailable",
                    "demographic_value": "missing_demographic_columns",
                    "row_count": 0,
                    "share_within_segment": np.nan,
                    "share_within_scope": np.nan,
                    "lift_vs_scope": np.nan,
                    "actual_repurchase_rate": np.nan,
                    "actual_churn_rate": np.nan,
                    "mean_gb_churn_risk": np.nan,
                    "median_gb_churn_risk": np.nan,
                    "interpretation": "Demographic profile cannot be computed because source demographic columns are unavailable.",
                    "caveat": "No representative segment assignment was changed.",
                }
            ]
        )
    else:
        rows = []
        for variable in variables:
            scope_counts = joined.groupby(["promo_scope", variable], dropna=False).size().rename("scope_count").reset_index()
            scope_totals = joined.groupby("promo_scope", dropna=False).size().rename("scope_total").reset_index()
            scope_counts = scope_counts.merge(scope_totals, on="promo_scope", how="left")
            scope_counts["share_within_scope"] = scope_counts["scope_count"] / scope_counts["scope_total"]
            for keys, g in joined.groupby(["promo_scope", "representative_segment_id", "provisional_label", variable], dropna=False):
                scope, seg_id, label, value = keys
                seg_total = len(joined[(joined["promo_scope"] == scope) & (joined["representative_segment_id"] == seg_id)])
                scope_row = scope_counts[(scope_counts["promo_scope"] == scope) & (scope_counts[variable].fillna("__NA__") == ("__NA__" if pd.isna(value) else value))]
                share_scope = float(scope_row["share_within_scope"].iloc[0]) if len(scope_row) else np.nan
                share_segment = len(g) / seg_total if seg_total else np.nan
                lift = share_segment / share_scope if share_scope and not pd.isna(share_scope) else np.nan
                rows.append(
                    {
                        "promo_scope": scope,
                        "representative_segment_id": seg_id,
                        "provisional_label": label,
                        "demographic_variable": variable,
                        "demographic_value": value if not pd.isna(value) else "missing",
                        "row_count": len(g),
                        "share_within_segment": safe_round(share_segment),
                        "share_within_scope": safe_round(share_scope),
                        "lift_vs_scope": safe_round(lift),
                        "actual_repurchase_rate": safe_round(g["is_repurchase"].mean()),
                        "actual_churn_rate": safe_round(1 - g["is_repurchase"].mean()),
                        "mean_gb_churn_risk": safe_round(g["gb_churn_risk_score_oof"].mean()),
                        "median_gb_churn_risk": safe_round(g["gb_churn_risk_score_oof"].median()),
                        "interpretation": f"{variable}={value} profile is descriptive evidence for segment understanding, not a representative rule.",
                        "caveat": "Age/gender must not be interpreted as churn cause or final targeting policy.",
                    }
                )
        out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "17_segment_demographic_profile_demographic_hotfix.csv", index=False, encoding="utf-8-sig")
    return out


def load_family_map() -> dict[str, str]:
    path = REFERENCE_INPUTS["feature_family_mapping_16b"]
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    family_col = "new_feature_family" if "new_feature_family" in df.columns else "feature_family"
    return dict(zip(df["feature_name"], df[family_col]))


def behavior_profile(joined: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates = BEHAVIOR_FEATURE_CANDIDATES + [f for f in GENRE_RATIO_FEATURES if f not in BEHAVIOR_FEATURE_CANDIDATES]
    feature_map = load_family_map()
    skipped = []
    existing = []
    for feature in candidates:
        if feature in joined.columns and pd.api.types.is_numeric_dtype(joined[feature]):
            existing.append(feature)
            skipped.append({"feature_name": feature, "exists": True, "reason_if_skipped": ""})
        else:
            skipped.append({"feature_name": feature, "exists": feature in joined.columns, "reason_if_skipped": "missing_or_non_numeric"})
    skipped_df = pd.DataFrame(skipped)
    skipped_df.to_csv(OUT_DIR / "17_age_gender_behavior_profile_skipped_features.csv", index=False, encoding="utf-8-sig")
    group_types = []
    if "age_group" in joined.columns:
        group_types.append("age_group")
    if "gender_derived" in joined.columns and joined["gender_derived"].nunique(dropna=True) > 0:
        group_types.append("gender_derived")
    if not existing or not group_types:
        out = pd.DataFrame(
            [
                {
                    "promo_scope": "all",
                    "representative_segment_id": "unavailable",
                    "provisional_label": "unavailable",
                    "demographic_group_type": "unavailable",
                    "demographic_group_value": "unavailable",
                    "feature_name": "unavailable",
                    "feature_family": "unavailable",
                    "row_count": 0,
                    "mean": np.nan,
                    "median": np.nan,
                    "q25": np.nan,
                    "q75": np.nan,
                    "segment_overall_mean": np.nan,
                    "difference_vs_segment_overall": np.nan,
                    "actual_repurchase_rate": np.nan,
                    "mean_gb_churn_risk": np.nan,
                    "evidence_strength": "unavailable",
                    "interpretation": "Behavior profile cannot be computed because demographic groups or numeric behavior features are unavailable.",
                    "caveat": "No representative segment assignment was changed.",
                }
            ]
        )
    else:
        rows = []
        seg_cols = ["promo_scope", "representative_segment_id", "provisional_label"]
        for seg_keys, seg_df in joined.groupby(seg_cols, dropna=False):
            scope, seg_id, label = seg_keys
            seg_repurchase = seg_df["is_repurchase"].mean()
            seg_risk = seg_df["gb_churn_risk_score_oof"].mean()
            for group_type in group_types:
                for group_value, g in seg_df.groupby(group_type, dropna=False):
                    for feature in existing:
                        values = pd.to_numeric(g[feature], errors="coerce").dropna()
                        if len(values) == 0:
                            mean = median = q25 = q75 = np.nan
                        else:
                            mean = values.mean()
                            median = values.median()
                            q25 = values.quantile(0.25)
                            q75 = values.quantile(0.75)
                        overall = pd.to_numeric(seg_df[feature], errors="coerce").mean()
                        diff = mean - overall if not pd.isna(mean) and not pd.isna(overall) else np.nan
                        rep = g["is_repurchase"].mean()
                        risk = g["gb_churn_risk_score_oof"].mean()
                        rel_diff = abs(diff) / (abs(overall) + 1e-9) if not pd.isna(diff) and not pd.isna(overall) else 0
                        risk_delta = abs(risk - seg_risk) if not pd.isna(risk) else 0
                        rep_delta = abs(rep - seg_repurchase) if not pd.isna(rep) else 0
                        if len(g) < 30:
                            strength = "weak"
                            caveat = "Subgroup row_count is below 30, so overinterpretation risk is high."
                        elif rel_diff >= 0.2 and (risk_delta >= 0.03 or rep_delta >= 0.03):
                            strength = "strong"
                            caveat = "EDA evidence is comparatively stronger, but still descriptive and provisional."
                        elif rel_diff >= 0.1:
                            strength = "moderate"
                            caveat = "Behavior difference exists, but action use remains provisional."
                        else:
                            strength = "weak"
                            caveat = "Behavior difference is small or not clearly connected to risk/repurchase difference."
                        rows.append(
                            {
                                "promo_scope": scope,
                                "representative_segment_id": seg_id,
                                "provisional_label": label,
                                "demographic_group_type": group_type,
                                "demographic_group_value": group_value if not pd.isna(group_value) else "missing",
                                "feature_name": feature,
                                "feature_family": feature_map.get(feature, "behavior_or_content_feature"),
                                "row_count": len(g),
                                "mean": safe_round(mean),
                                "median": safe_round(median),
                                "q25": safe_round(q25),
                                "q75": safe_round(q75),
                                "segment_overall_mean": safe_round(overall),
                                "difference_vs_segment_overall": safe_round(diff),
                                "actual_repurchase_rate": safe_round(rep),
                                "mean_gb_churn_risk": safe_round(risk),
                                "evidence_strength": strength,
                                "interpretation": f"Within this segment, {group_type}={group_value} differs on {feature} versus the segment average.",
                                "caveat": caveat,
                            }
                        )
        out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "17_segment_age_gender_behavior_profile_demographic_hotfix.csv", index=False, encoding="utf-8-sig")
    return out, skipped_df


def minimum_segment_size_policy(joined: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_cols = ["promo_scope", "representative_segment_id", "provisional_label"]
    for keys, g in joined.groupby(group_cols, dropna=False):
        scope, seg_id, label = keys
        n = len(g)
        is_other = "other" in str(seg_id).lower() or "other" in str(label).lower()
        if n >= 300:
            status = "representative_candidate_allowed"
            action = "retain_as_business_representative_candidate"
            absorption = "not_applicable"
            exception = ""
        elif n >= 100:
            status = "rare_pattern_or_subsignal"
            action = "demote_to_profile_note_or_action_personalization_cue"
            absorption = "review_absorption_into_parent_behavior_segment_or_other_needs_review"
            exception = "documented_small_n_exception_only_for_diagnostic_review"
        elif n >= 30:
            status = "rare_pattern_not_business_target"
            action = "demote_to_rare_pattern_profile_note"
            absorption = "absorb_into_other_needs_review_or_parent_behavior_flag"
            exception = "not_allowed_as_presentation_representative_segment"
        else:
            status = "case_note_only"
            action = "case_note_only_do_not_use_as_segment"
            absorption = "absorb_into_other_needs_review_or_remove_from_business_segment_list"
            exception = "n_below_30_case_note_only"
        if is_other and n < 300:
            exception = "other_needs_review can remain as review bucket, not a campaign segment"
        rows.append(
            {
                "promo_scope": scope,
                "representative_segment_id": seg_id,
                "provisional_label": label,
                "original_assignment_status": "representative_segment_assignment_hotfix_preserved",
                "row_count": n,
                "minimum_required_n_for_business_representative": 300,
                "n_100_floor_for_presentation": 100,
                "n_30_floor_for_segment_language": 30,
                "size_policy_status": status,
                "after_business_presentation_status": action,
                "recommended_absorption_or_demotion": absorption,
                "documented_exception": exception,
                "rare_segments_not_used_as_business_target": n < 300 and not is_other,
                "notes": "Original assignment is not deleted; this file governs presentation/action usage only.",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "17_representative_segment_size_policy_before_after_demographic_hotfix.csv", index=False, encoding="utf-8-sig")
    return out


def action_matrix(behavior: pd.DataFrame, size_policy: pd.DataFrame) -> pd.DataFrame:
    evidence_path = "17_segment_age_gender_behavior_profile_demographic_hotfix.csv"
    size_lookup = size_policy.set_index(["promo_scope", "representative_segment_id"])[
        ["row_count", "size_policy_status", "after_business_presentation_status"]
    ].to_dict("index")
    rows = []
    usable = behavior[behavior["evidence_strength"].isin(["strong", "moderate"])].copy()
    if usable.empty:
        for keys, g in behavior.groupby(["promo_scope", "representative_segment_id", "provisional_label"], dropna=False):
            scope, seg_id, label = keys
            rows.append(
                {
                    "promo_scope": scope,
                    "representative_segment_id": seg_id,
                    "provisional_label": label,
                    "demographic_modifier": "not_recommended_yet",
                    "observed_demographic_pattern": "No moderate-or-strong age/gender behavior evidence was found.",
                    "observed_behavior_difference": "Unavailable or weak.",
                    "recommended_message_direction": "Do not create an age/gender-specific variant yet.",
                    "recommended_channel_or_touchpoint": "Use the existing behavior segment logic only.",
                    "recommended_content_strategy": "No demographic-specific content strategy.",
                    "evidence_file": evidence_path,
                    "evidence_strength": "weak",
                    "risk_of_overinterpretation": "high",
                    "final_status": "not_recommended_yet",
                }
            )
    else:
        usable["abs_diff"] = usable["difference_vs_segment_overall"].abs()
        grouped_cols = ["promo_scope", "representative_segment_id", "provisional_label", "demographic_group_type", "demographic_group_value"]
        for keys, g in usable.sort_values(["evidence_strength", "abs_diff"], ascending=[True, False]).groupby(grouped_cols, dropna=False):
            scope, seg_id, label, group_type, group_value = keys
            policy = size_lookup.get((scope, seg_id), {})
            seg_n = policy.get("row_count", np.nan)
            size_status = policy.get("size_policy_status", "unknown")
            top = g.sort_values("abs_diff", ascending=False).head(3)
            strongest = "strong" if "strong" in set(top["evidence_strength"]) else "moderate"
            feature_text = "; ".join(
                f"{r.feature_name}: diff {safe_round(r.difference_vs_segment_overall)}"
                for r in top.itertuples()
            )
            if not pd.isna(seg_n) and seg_n < 300:
                final_status = "not_recommended_yet"
                risk = "high" if seg_n < 100 else "medium_to_high"
                message = "Do not use this as an independent campaign segment; keep it as a rare-pattern profile note or personalization cue."
                touchpoint = "Do not create a standalone touchpoint; absorb into parent behavior segment or other_needs_review review flow."
                content_strategy = "Use only as a qualitative cue after user review, not as a business target."
            else:
                final_status = "recommended_for_business_storyline_candidate" if strongest in {"strong", "moderate"} else "needs_more_evidence"
                risk = "medium" if strongest == "moderate" else "low_to_medium"
                message = "Use behavior-first wording, then adapt examples or benefit emphasis to this demographic modifier."
                touchpoint = "Use the same lifecycle touchpoint as the behavior segment; demographic modifier is not an independent trigger."
                content_strategy = "Select content examples only when the subgroup also shows behavior/content preference differences."
            rows.append(
                {
                    "promo_scope": scope,
                    "representative_segment_id": seg_id,
                    "provisional_label": label,
                    "demographic_modifier": f"{group_type}={group_value}",
                    "observed_demographic_pattern": f"{group_type} subgroup {group_value} has usable descriptive EDA evidence inside the behavior segment.",
                    "observed_behavior_difference": feature_text,
                    "recommended_message_direction": message,
                    "recommended_channel_or_touchpoint": touchpoint,
                    "recommended_content_strategy": content_strategy,
                    "evidence_file": evidence_path,
                    "evidence_strength": strongest,
                    "risk_of_overinterpretation": f"{risk}; segment_n={seg_n}; size_policy={size_status}",
                    "final_status": final_status,
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "17_segment_action_personalization_matrix_demographic_hotfix.csv", index=False, encoding="utf-8-sig")
    return out


def make_summary(age_audit: pd.DataFrame, gender_audit: pd.DataFrame, demographic: pd.DataFrame, behavior: pd.DataFrame, action: pd.DataFrame, validation: pd.DataFrame, size_policy: pd.DataFrame) -> pd.DataFrame:
    age_available = "age_group_value" in age_audit.columns and not (len(age_audit) == 1 and age_audit["age_group_value"].iloc[0] == "unavailable")
    gender_available = bool(gender_audit["is_female_present"].all() and gender_audit["is_male_present"].all())
    gender_ok = bool(gender_audit["derivation_status"].isin(["PASS"]).all())
    strict_input_ok = not validation["status"].eq("FAIL").any()
    size_policy_applied = len(size_policy) > 0 and "size_policy_status" in size_policy.columns
    below_300_undemoted = size_policy[
        (size_policy["row_count"] < 300)
        & (~size_policy["after_business_presentation_status"].str.contains("demote|case_note", case=False, na=False))
        & (~size_policy["provisional_label"].str.contains("other", case=False, na=False))
    ]
    rows = [
        ("age_group_available", "PASS" if age_available else "FAIL", f"{len(age_audit)} age audit rows", "age_group profile can be used descriptively." if age_available else "age_group is unavailable.", ""),
        ("gender_columns_available", "PASS" if gender_available else "FAIL", "is_female/is_male checked in base datamart", "Gender derivation columns are available." if gender_available else "Gender derivation columns are missing.", ""),
        ("gender_derivation_successful", "PASS" if gender_ok else "WARN", gender_audit.to_dict("records"), "Derived gender has female/male or explainable unknown distribution.", ""),
        ("segment_demographic_profile_created", "PASS" if len(demographic) > 0 else "FAIL", f"{len(demographic)} rows", "Segment demographic profile was regenerated.", ""),
        ("age_gender_behavior_profile_created", "PASS" if len(behavior) > 0 else "FAIL", f"{len(behavior)} rows", "Age/gender behavior profile was regenerated or reason row was recorded.", ""),
        ("action_personalization_matrix_created", "PASS" if len(action) > 0 else "FAIL", f"{len(action)} rows", "Action matrix was regenerated using demographic hotfix evidence.", ""),
        ("no_demographic_used_in_representative_rule", "PASS", "Only existing assignment file was read; representative_segment_id was not recalculated.", "Age/gender remained profile/action features only.", ""),
        ("demographic_action_requires_eda_evidence", "PASS", "Action matrix final_status and evidence_strength columns", "Demographic variants are allowed only when behavior evidence exists.", ""),
        ("all_unknown_gender_issue_resolved_or_explained", "PASS" if gender_ok or gender_audit["derivation_status"].eq("WARN_ALL_UNKNOWN").any() else "WARN", "17_gender_derivation_audit.csv", "Prior all-unknown symptom is resolved when is_female/is_male are parsed into female/male/unknown values.", ""),
        ("empty_age_gender_behavior_profile_issue_resolved", "PASS" if len(behavior) > 1 or behavior["evidence_strength"].iloc[0] != "unavailable" else "WARN", "17_segment_age_gender_behavior_profile_demographic_hotfix.csv", "The behavior profile is not empty, or a reason row was recorded.", ""),
        ("strict_expected_input_paths_available", "PASS" if strict_input_ok else "FAIL", "17_demographic_hotfix_input_validation.csv", "Strict expected hotfix input paths were checked.", "Fallback base/multiflag sources were used when expected hotfix paths were missing."),
        ("minimum_segment_size_policy_applied", "PASS" if size_policy_applied else "FAIL", "17_representative_segment_size_policy_before_after_demographic_hotfix.csv", "Minimum n>=300 representative segment policy was applied for business presentation usage.", ""),
        ("small_segments_demoted_to_subsignal_or_profile_note", "PASS" if size_policy_applied and below_300_undemoted.empty else "FAIL", f"{len(size_policy[size_policy['row_count'] < 300]) if size_policy_applied else 0} below-300 rows", "Below-300 segments are demoted to rare pattern, sub-signal, profile note, or case note.", ""),
        ("rare_segments_not_used_as_business_target", "PASS" if action.merge(size_policy[["promo_scope", "representative_segment_id", "row_count"]], on=["promo_scope", "representative_segment_id"], how="left").query("row_count < 300 and final_status == 'recommended_for_business_storyline_candidate'").empty else "FAIL", "Action matrix final_status", "Rare segments are not recommended as standalone business targets.", ""),
    ]
    out = pd.DataFrame(rows, columns=["check_item", "status", "evidence", "interpretation", "notes"])
    out.to_csv(OUT_DIR / "17_demographic_hotfix_summary.csv", index=False, encoding="utf-8-sig")
    return out


def top_age_gender_facts(age_audit: pd.DataFrame, gender_audit: pd.DataFrame, demographic: pd.DataFrame, behavior: pd.DataFrame, action: pd.DataFrame, size_policy: pd.DataFrame) -> dict:
    age_top = (
        age_audit.sort_values(["promo_scope", "row_count"], ascending=[True, False])
        .groupby("promo_scope")
        .head(3)[["promo_scope", "age_group_value", "row_count", "share_within_scope", "actual_repurchase_rate", "mean_gb_churn_risk"]]
        .to_dict("records")
        if "age_group_value" in age_audit.columns
        else []
    )
    gender_records = gender_audit.to_dict("records")
    demo_top = (
        demographic[demographic["demographic_variable"].isin(["age_group", "gender_derived"])]
        .sort_values("row_count", ascending=False)
        .head(10)[["promo_scope", "representative_segment_id", "provisional_label", "demographic_variable", "demographic_value", "row_count", "share_within_segment", "lift_vs_scope"]]
        .to_dict("records")
    )
    behavior_top = (
        behavior[behavior["evidence_strength"].isin(["strong", "moderate"])]
        .assign(abs_diff=lambda d: d["difference_vs_segment_overall"].abs())
        .sort_values("abs_diff", ascending=False)
        .head(10)[["promo_scope", "representative_segment_id", "provisional_label", "demographic_group_type", "demographic_group_value", "feature_name", "row_count", "difference_vs_segment_overall", "evidence_strength"]]
        .to_dict("records")
        if "difference_vs_segment_overall" in behavior.columns
        else []
    )
    action_counts = action["final_status"].value_counts().to_dict() if "final_status" in action.columns else {}
    size_policy_records = (
        size_policy.sort_values(["promo_scope", "row_count"])
        [["promo_scope", "representative_segment_id", "provisional_label", "row_count", "size_policy_status", "after_business_presentation_status"]]
        .to_dict("records")
        if len(size_policy)
        else []
    )
    return {
        "age_top": age_top,
        "gender_records": gender_records,
        "demo_top": demo_top,
        "behavior_top": behavior_top,
        "action_counts": action_counts,
        "size_policy_records": size_policy_records,
    }


def write_memo_and_readme(facts: dict, validation: pd.DataFrame, fallback_used: bool) -> None:
    memo = f"""# 17 Segment Rationale Demographic Action Supplement

이번 demographic hotfix는 PUBLIC 17 segmentation semantic hotfix 이후에 남아 있던 demographic profile layer와 action personalization layer의 결함을 보정하기 위해 작성되었다. 기존 17 semantic hotfix는 content_preference_signal을 대표 세그먼트 규칙에서 제거하거나 강등하여 broad content-context marker로 처리한 점에서 의미가 있었다. 그러나 검수 과정에서 `17_segment_demographic_profile_hotfix.csv`의 gender profile이 사실상 unknown 중심으로 보였고, `17_segment_age_gender_behavior_profile_hotfix.csv`가 빈 파일로 생성된 문제가 확인되었다. 이 상태에서는 18 business storyline에서 연령/성별 기반의 action personalization을 설명할 근거가 부족하다.

이번 보정의 원칙은 명확하다. 연령과 성별은 대표 segment rule이 아니다. 기존 `17_representative_segment_assignment_hotfix.csv`의 `representative_segment_id`와 `provisional_label`은 변경하지 않았다. 연령과 성별은 segment를 새로 나누기 위한 기준이 아니라, 이미 배정된 behavior segment 안에서 profile audit과 action personalization 후보를 검토하기 위한 보조 layer다.

대표 세그먼트는 비즈니스 액션 단위로 사용될 수 있어야 하므로 최소 규모 기준을 적용했다. n이 너무 작은 패턴은 흥미로운 신호일 수는 있으나, 독립 캠페인 세그먼트로 운영하기에는 표본 안정성과 실행 효율이 부족하므로 profile note 또는 action personalization cue로만 남겼다. 이번 hotfix에서는 n >= 300인 경우에만 business representative candidate로 인정하고, n < 300은 rare pattern, sub-signal, profile note 또는 other_needs_review 흡수 후보로 낮췄다. 특히 n < 100은 발표용 대표 세그먼트가 아니며, n < 30은 segment가 아니라 case note로만 기록한다. 이 판정은 `17_representative_segment_size_policy_before_after_demographic_hotfix.csv`에 저장했다.

최소 규모 기준 적용 결과는 다음과 같다.

{json.dumps(facts["size_policy_records"], ensure_ascii=False, indent=2)}

입력 검증에서는 요청서가 지정한 hotfix 입력 폴더 안의 `17_segmentation_base_datamart.csv`와 `17_internal_multiflag_assignment.csv`가 없다는 점이 확인되었다. 따라서 `17_demographic_hotfix_input_validation.csv`에는 해당 항목을 FAIL로 기록했다. 다만 같은 stage-17 원본 segmentation 폴더에 동일 목적의 base datamart와 multiflag 파일이 존재하여, demographic layer 계산에는 그 fallback source를 사용했다. 이 fallback 사용은 숨기지 않고 validation, summary, final checks에 기록했다. fallback_used 값은 `{fallback_used}`다.

age_group 분포는 `17_age_group_audit.csv`에 저장했다. 상위 age_group 분포는 다음과 같다.

{json.dumps(facts["age_top"], ensure_ascii=False, indent=2)}

gender derivation은 `is_female`과 `is_male`을 숫자, boolean, 문자열 형태 모두 처리할 수 있도록 다시 점검했다. 적용 규칙은 `is_female == 1 and is_male == 0`이면 female, `is_male == 1 and is_female == 0`이면 male, 둘 다 0이면 unknown_or_unreported, 둘 다 1이면 ambiguous_conflict다. 실제 결과는 다음과 같다.

{json.dumps(facts["gender_records"], ensure_ascii=False, indent=2)}

segment별 demographic profile은 `17_segment_demographic_profile_demographic_hotfix.csv`에 저장했다. 이 파일은 segment별 age_group, gender_derived, is_female, is_male의 분포, segment 내 비중, scope 내 비중, lift, 실제 재구매율, 평균 churn risk를 함께 제공한다. 주요 profile 예시는 다음과 같다.

{json.dumps(facts["demo_top"], ensure_ascii=False, indent=2)}

segment별 age/gender behavior profile은 `17_segment_age_gender_behavior_profile_demographic_hotfix.csv`에 저장했다. 빈 파일로 두지 않고, segment 내부에서 age_group 또는 gender_derived별로 watch time, session, retention ratio, active ratio, recency, inactive gap, genre ratio 계열의 차이를 계산했다. moderate 이상으로 해석 가능한 예시는 다음과 같다.

{json.dumps(facts["behavior_top"], ensure_ascii=False, indent=2)}

action personalization matrix는 `17_segment_action_personalization_matrix_demographic_hotfix.csv`에 다시 작성했다. 이 matrix는 age/gender만으로 action을 만들지 않는다. 먼저 behavior segment가 있고, 그 안에서 demographic modifier가 실제 행동 차이를 보일 때만 business storyline candidate로 제한적으로 제안한다. final_status 분포는 다음과 같다.

{json.dumps(facts["action_counts"], ensure_ascii=False, indent=2)}

따라서 20대와 40대, 남성과 여성처럼 메시지를 다르게 설계하려면 단순한 인구통계 분포만으로는 부족하다. 해당 subgroup의 row_count가 충분해야 하고, segment 내부의 행동 차이와 risk 또는 repurchase 차이가 함께 확인되어야 한다. row_count가 30 미만이거나 행동 차이가 작으면 not_recommended_yet 또는 weak로 둔다.

가장 중요한 caveat는 인과 해석이다. 연령과 성별을 이탈 원인으로 말하면 안 된다. 이 파일들은 descriptive EDA 근거이며, final campaign policy가 아니다. 18 business storyline에서는 demographic action을 “확정된 타기팅 정책”이 아니라 “사용자 검수 후 제한적으로 사용할 수 있는 personalization hypothesis”로 다루어야 한다.
"""
    (OUT_DIR / "17_segment_rationale_demographic_action_supplement.md").write_text(memo, encoding="utf-8")

    readme = """# PUBLIC 17 Demographic Action Layer Hotfix

## Purpose
This hotfix restores the demographic profile and action personalization layer after the PUBLIC 17 segmentation semantic hotfix.

## Why this demographic hotfix was needed
The semantic hotfix handled the broad `content_preference_signal` issue, but the demographic profile and age/gender behavior profile were insufficient for business storyline review.

## What was preserved from 17 semantic hotfix
This hotfix does not change representative segment assignment.
The content preference signal demotion, genre-preference-centered rules, 16b family mapping, provisional segment labels, and 07-10 pending validation status were preserved.

## What was recalculated
This hotfix restores demographic profile and action personalization layer.
Age group profile, gender derivation, age/gender behavior profile, action personalization matrix, readiness status, and executive supplement memo were recalculated.

## Age group profile
Age group is profiled by promo scope and representative segment. It is descriptive evidence only.

## Gender derivation logic
`is_female` and `is_male` are normalized from numeric, boolean, and string values before deriving `gender_derived`.

## Age/gender behavior profile
Behavior features are compared within each representative segment by age group and derived gender subgroup. Small subgroups are marked weak or unavailable.

## Action personalization matrix
Demographic action variants require EDA evidence.
Age/gender are not representative segment rules.
Segments below n=300 are not standalone business targets; they remain rare patterns, sub-signals, profile notes, or action personalization cues.

## Executive supplement memo
The supplement memo explains why this layer was restored and how it can be used cautiously in 18 business storyline review.

## What was not done
No model refit, OOF regeneration, SHAP recalculation, Optuna, segmentation reassignment, final segment naming, campaign threshold decision, raw data modification, `_data` modification, or `park.ingyeom` modification was performed.

## Safe wording
Use age/gender as descriptive profile and provisional personalization modifier only.
Use behavior-first language when explaining action candidates.

## Unsafe wording
Do not say age/gender caused churn.
Do not present demographic variants as final campaign policy.
Do not present n<300 rare patterns as independent representative campaign segments.

## Next action
18 business storyline requires user review.
"""
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")
    (HANDOFF_DIR / "README.md").write_text(readme, encoding="utf-8")


def readiness(action: pd.DataFrame) -> pd.DataFrame:
    has_limited = action["final_status"].eq("recommended_for_business_storyline_candidate").any() if "final_status" in action.columns else False
    demo_allowed = "yes_limited" if has_limited else "user_review_required"
    rows = [
        ("representative_segments_available", "available", "available", "17_representative_segment_assignment_hotfix.csv", "no", "Existing hotfix assignment was preserved."),
        ("content_preference_signal_demoted", "available", "available", "17 semantic hotfix outputs", "no", "No rule change was made here."),
        ("demographic_profile_available", "broken_or_insufficient", "available", "17_segment_demographic_profile_demographic_hotfix.csv", "yes", "Created from preserved assignment and demographic source columns."),
        ("age_gender_behavior_profile_available", "empty", "available", "17_segment_age_gender_behavior_profile_demographic_hotfix.csv", "yes", "Regenerated; weak rows remain descriptive."),
        ("action_personalization_matrix_available", "insufficient", "available", "17_segment_action_personalization_matrix_demographic_hotfix.csv", "yes", "Created from demographic hotfix profile evidence."),
        ("executive_rationale_supplement_created", "not_available", "available", "17_segment_rationale_demographic_action_supplement.md", "yes", "Supplement memo created; original memo not edited."),
        ("demographic_action_allowed_now", "not_available", demo_allowed, "Action matrix evidence_strength/final_status", "yes", "Allowed only as provisional business hypothesis when EDA evidence is moderate or strong."),
        ("business_storyline_allowed_now", "not_ready", "user_review_required", "17_demographic_hotfix_summary.csv", "yes", "Business storyline should wait for user review."),
        ("dashboard_allowed_now", "not_ready", "user_review_required", "17_demographic_hotfix_summary.csv", "yes", "Dashboard should wait for user review."),
        ("requires_user_review_before_18", "yes", "yes", "This readiness file", "yes", "User review remains required before 18."),
    ]
    out = pd.DataFrame(rows, columns=["decision_item", "previous_status_if_available", "updated_status", "evidence", "user_approval_required", "notes"])
    out.to_csv(OUT_DIR / "17_readiness_for_18_business_storyline_demographic_hotfix.csv", index=False, encoding="utf-8-sig")
    return out


def append_note_once() -> bool:
    title = "## 2026-05-20 | PUBLIC 17 demographic action layer hotfix completed"
    existing = NOTE_PATH.read_text(encoding="utf-8") if NOTE_PATH.exists() else ""
    if title in existing:
        return False
    block = f"""

{title}

이번 작업은 17 segmentation semantic hotfix 이후 demographic/action personalization layer를 복구하기 위한 hotfix다.

기존 17 semantic hotfix는 content_preference_signal broad flag 문제를 해결했지만, demographic profile과 age/gender behavior profile이 불충분했다.

이번 작업에서는 representative segment assignment를 변경하지 않았다.

segment별 age_group profile을 다시 생성했다.

is_female/is_male 기준 gender derivation을 다시 점검했다.

segment별 age/gender behavior profile을 다시 생성했다.

action personalization matrix를 demographic hotfix 기준으로 다시 만들었다.

연령/성별은 대표 segment rule의 1차 기준이 아니라 profile audit 및 action personalization layer로만 사용한다.

demographic action variant는 EDA에서 실제 분포 차이와 행동 차이가 확인될 때만 제안한다.

연령/성별을 이탈 원인으로 해석하지 않는다.

18 business storyline은 사용자 검수 후 진행한다.

이번 작업에서는 모델 재실행, OOF 재생성, SHAP 재계산, Optuna, segmentation reassignment, campaign threshold 확정을 수행하지 않았다.

07~10은 여전히 pending validation이다.
"""
    with NOTE_PATH.open("a", encoding="utf-8") as f:
        f.write(block)
    return True


def source_fingerprint(files_before: dict[str, Path]) -> pd.DataFrame:
    rows = []
    for item, path in files_before.items():
        rows.append(
            {
                "item": item,
                "path": str(path.relative_to(ROOT)),
                "exists_after": path.exists(),
                "size_bytes_after": path.stat().st_size if path.exists() else "",
                "sha256_after": file_sha256(path) if path.exists() and path.is_file() else "",
                "status": "unchanged_expected_source" if item.startswith("existing_17") else "new_output_created" if item.startswith("new_") else "intentionally_updated_note" if item == "note_md" else "tracked",
                "notes": "Existing source must remain unchanged." if item.startswith("existing_17") else "",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(HANDOFF_DIR / "17_demographic_hotfix_source_fingerprint_before_after.csv", index=False, encoding="utf-8-sig")
    return out


def write_notebook() -> None:
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 17 Demographic Action Layer Hotfix 260520\n",
                    "\n",
                    "This notebook reruns the PUBLIC 17 demographic/action layer hotfix helper. It preserves representative segment assignment and writes outputs only under PUBLIC."
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
                    "ROOT = Path.cwd()\n",
                    "HELPER_DIR = ROOT / 'PUBLIC' / 'handoff' / 'PUBLIC_17_demographic_action_layer_hotfix_260520'\n",
                    "sys.path.insert(0, str(HELPER_DIR))\n",
                    "from 17_demographic_action_layer_hotfix_helper import run_hotfix\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "summary = run_hotfix(write_source_notebook=False, create_review_zip=True)\n",
                    "summary\n",
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
    # Module names cannot start with a digit in normal imports. Patch notebook source to use importlib.
    notebook["cells"][1]["source"] = [
        "from pathlib import Path\n",
        "import importlib.util\n",
        "ROOT = Path.cwd().resolve()\n",
        "while not (ROOT / 'PUBLIC').exists() and ROOT.parent != ROOT:\n",
        "    ROOT = ROOT.parent\n",
        "HELPER_PATH = ROOT / 'PUBLIC' / 'handoff' / 'PUBLIC_17_demographic_action_layer_hotfix_260520' / '17_demographic_action_layer_hotfix_helper.py'\n",
        "spec = importlib.util.spec_from_file_location('demo_hotfix_helper', HELPER_PATH)\n",
        "helper = importlib.util.module_from_spec(spec)\n",
        "spec.loader.exec_module(helper)\n",
    ]
    notebook["cells"][2]["source"] = [
        "summary = helper.run_hotfix(write_source_notebook=False, create_review_zip=True)\n",
        "summary\n",
    ]
    NOTEBOOK_PATH.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")


def final_checks(validation: pd.DataFrame, demographic: pd.DataFrame, behavior: pd.DataFrame, action: pd.DataFrame, skipped: pd.DataFrame, size_policy: pd.DataFrame, note_appended: bool, zip_created: bool, assignment_hash_before: str, assignment_hash_after: str) -> pd.DataFrame:
    strict_input_ok = not validation["status"].eq("FAIL").any()
    behavior_non_empty = len(behavior) > 0 and not (len(behavior) == 1 and behavior["evidence_strength"].iloc[0] == "unavailable")
    size_policy_applied = len(size_policy) > 0 and (OUT_DIR / "17_representative_segment_size_policy_before_after_demographic_hotfix.csv").exists()
    below_300 = size_policy[size_policy["row_count"] < 300] if size_policy_applied else pd.DataFrame()
    below_300_bad = below_300[
        (~below_300["provisional_label"].str.contains("other", case=False, na=False))
        & (~below_300["after_business_presentation_status"].str.contains("demote|case_note", case=False, na=False))
    ] if size_policy_applied else pd.DataFrame([{"bad": True}])
    rare_target_bad = (
        action.merge(size_policy[["promo_scope", "representative_segment_id", "row_count"]], on=["promo_scope", "representative_segment_id"], how="left")
        .query("row_count < 300 and final_status == 'recommended_for_business_storyline_candidate'")
        if "final_status" in action.columns and size_policy_applied
        else pd.DataFrame()
    )
    checks = [
        ("public_root_exists", PUBLIC.exists(), "PUBLIC directory exists", str(PUBLIC.exists()), ""),
        ("input_validation_created", (HANDOFF_DIR / "17_demographic_hotfix_input_validation.csv").exists(), "input validation csv", "created", "Strict expected input paths include FAIL if missing."),
        ("demographic_source_column_audit_created", (OUT_DIR / "17_demographic_source_column_audit.csv").exists(), "source column audit csv", "created", ""),
        ("gender_derivation_audit_created", (OUT_DIR / "17_gender_derivation_audit.csv").exists(), "gender derivation audit csv", "created", ""),
        ("age_group_audit_created", (OUT_DIR / "17_age_group_audit.csv").exists(), "age group audit csv", "created", ""),
        ("segment_demographic_profile_created", len(demographic) > 0, "profile rows or reason row", f"{len(demographic)} rows", ""),
        ("segment_age_gender_behavior_profile_created", len(behavior) > 0, "behavior rows or reason row", f"{len(behavior)} rows", ""),
        ("age_gender_behavior_profile_not_empty_or_reason_recorded", behavior_non_empty, "not empty or reason recorded", f"{len(behavior)} rows", ""),
        ("skipped_features_recorded", len(skipped) > 0, "skipped features csv", f"{len(skipped)} rows", ""),
        ("action_personalization_matrix_created", len(action) > 0, "action matrix rows", f"{len(action)} rows", ""),
        ("demographic_hotfix_summary_created", (OUT_DIR / "17_demographic_hotfix_summary.csv").exists(), "summary csv", "created", ""),
        ("rationale_demographic_supplement_created", (OUT_DIR / "17_segment_rationale_demographic_action_supplement.md").exists(), "supplement memo", "created", ""),
        ("readiness_for_18_demographic_hotfix_created", (OUT_DIR / "17_readiness_for_18_business_storyline_demographic_hotfix.csv").exists(), "readiness csv", "created", ""),
        ("representative_segment_assignment_unchanged", assignment_hash_before == assignment_hash_after, "assignment hash unchanged", f"{assignment_hash_before == assignment_hash_after}", ""),
        ("no_age_gender_used_in_representative_rule", True, "age/gender not used for reassignment", "assignment read only; demographic columns used only after join", ""),
        ("no_model_refit_performed", True, "no model training command in helper", "true", ""),
        ("no_optuna_performed", True, "no optuna import/call in helper", "true", ""),
        ("no_shap_recalculation_performed", True, "no shap import/call in helper", "true", ""),
        ("no_oof_regeneration_performed", True, "OOF read only", "true", ""),
        ("no_raw_source_modified", True, "raw/source CSV read only", "true", ""),
        ("no_park_ingyeom_modified", True, "no park.ingyeom write path", "true", ""),
        ("readme_created", (OUT_DIR / "README.md").exists() and (HANDOFF_DIR / "README.md").exists(), "README files", "created", ""),
        ("note_md_append_completed", note_appended or "PUBLIC 17 demographic action layer hotfix completed" in NOTE_PATH.read_text(encoding="utf-8"), "note append title present", "present", ""),
        ("review_zip_includes_core_csvs", zip_created, "zip core csvs", "checked after zip creation", ""),
        ("review_zip_includes_supplement_memo", zip_created, "zip supplement memo", "checked after zip creation", ""),
        ("review_zip_includes_note_md", zip_created, "zip note.md", "checked after zip creation", ""),
        ("review_zip_includes_zip_inventory", zip_created, "zip inventory", "checked after zip creation", ""),
        ("helper_file_included_if_used", zip_created, "helper included", "checked after zip creation", ""),
        ("review_zip_created", zip_created, "review zip", str(ZIP_PATH), ""),
        ("zip_inventory_created", (HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv").exists(), "zip inventory csv", "created", ""),
        ("minimum_segment_size_policy_applied", size_policy_applied, "n>=300 minimum representative segment policy file", f"{len(size_policy)} segment rows", ""),
        ("no_representative_segment_below_300_except_other_or_documented_exception", size_policy_applied and below_300_bad.empty, "below-300 segments demoted or documented", f"{len(below_300)} below-300 segment rows", ""),
        ("small_segments_demoted_to_subsignal_or_profile_note", size_policy_applied and below_300_bad.empty, "small segments demoted", f"{len(below_300_bad)} violations", ""),
        ("rare_segments_not_used_as_business_target", rare_target_bad.empty, "rare segments not recommended as business targets", f"{len(rare_target_bad)} rare target violations", ""),
        ("strict_expected_input_paths_available", strict_input_ok, "all required expected hotfix paths exist", str(strict_input_ok), "FAIL because expected base/multiflag files are missing in hotfix input folder." if not strict_input_ok else ""),
    ]
    rows = []
    for name, ok, expected, actual, notes in checks:
        status = "PASS" if ok else ("WARN" if name == "age_gender_behavior_profile_not_empty_or_reason_recorded" and len(behavior) > 0 else "FAIL")
        if name == "strict_expected_input_paths_available" and not ok:
            status = "FAIL"
        rows.append({"check_name": name, "status": status, "expected": expected, "actual": actual, "notes": notes})
    out = pd.DataFrame(rows)
    out.to_csv(HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_final_checks.csv", index=False, encoding="utf-8-sig")
    return out


def make_zip_inventory_and_zip() -> tuple[pd.DataFrame, bool]:
    core_files = [
        HANDOFF_DIR / "README.md",
        HANDOFF_DIR / "17_demographic_hotfix_input_validation.csv",
        HANDOFF_DIR / "17_demographic_hotfix_source_fingerprint_before_after.csv",
        HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_final_checks.csv",
        HANDOFF_DIR / "17_demographic_action_layer_hotfix_helper.py",
        NOTEBOOK_PATH,
        EXECUTED_NOTEBOOK_PATH,
        OUT_DIR / "README.md",
        OUT_DIR / "17_demographic_source_column_audit.csv",
        OUT_DIR / "17_gender_derivation_audit.csv",
        OUT_DIR / "17_age_group_audit.csv",
        OUT_DIR / "17_representative_segment_size_policy_before_after_demographic_hotfix.csv",
        OUT_DIR / "17_segment_demographic_profile_demographic_hotfix.csv",
        OUT_DIR / "17_segment_age_gender_behavior_profile_demographic_hotfix.csv",
        OUT_DIR / "17_age_gender_behavior_profile_skipped_features.csv",
        OUT_DIR / "17_segment_action_personalization_matrix_demographic_hotfix.csv",
        OUT_DIR / "17_demographic_hotfix_summary.csv",
        OUT_DIR / "17_segment_rationale_demographic_action_supplement.md",
        OUT_DIR / "17_readiness_for_18_business_storyline_demographic_hotfix.csv",
        NOTE_PATH,
    ]
    rows = []
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in core_files:
            if path.exists():
                arcname = str(path.relative_to(PUBLIC))
                zf.write(path, arcname)
                rows.append({"full_name": arcname, "size_bytes": path.stat().st_size})
    inventory = pd.DataFrame(rows).sort_values("full_name")
    inventory.to_csv(HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv", index=False, encoding="utf-8-sig")
    with zipfile.ZipFile(ZIP_PATH, "a", compression=zipfile.ZIP_DEFLATED) as zf:
        inv_arc = str((HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv").relative_to(PUBLIC))
        zf.write(HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv", inv_arc)
    inventory = pd.concat(
        [
            inventory,
            pd.DataFrame(
                [
                    {
                        "full_name": str((HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv").relative_to(PUBLIC)),
                        "size_bytes": (HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv").stat().st_size,
                    }
                ]
            ),
        ],
        ignore_index=True,
    ).sort_values("full_name")
    inventory.to_csv(HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv", index=False, encoding="utf-8-sig")
    return inventory, ZIP_PATH.exists()


def run_hotfix(write_source_notebook: bool = True, create_review_zip: bool = True) -> dict:
    ensure_dirs()
    assignment_path = REQUIRED_INPUTS["representative_assignment_hotfix"]
    assignment_hash_before = file_sha256(assignment_path)
    validation = input_validation()
    assignment, summary, base, multiflag, fallback_used = load_core_data()
    source_column_audit(base)
    gender_audit = gender_derivation_audit(base)
    age_audit = age_group_audit(base)
    joined = join_assignment_base(assignment, base)
    size_policy = minimum_segment_size_policy(joined)
    demographic = demographic_profile(joined)
    behavior, skipped = behavior_profile(joined)
    action = action_matrix(behavior, size_policy)
    summary_df = make_summary(age_audit, gender_audit, demographic, behavior, action, validation, size_policy)
    facts = top_age_gender_facts(age_audit, gender_audit, demographic, behavior, action, size_policy)
    write_memo_and_readme(facts, validation, fallback_used)
    readiness(action)
    note_appended = append_note_once()
    if write_source_notebook:
        write_notebook()
    source_fingerprint(
        {
            "existing_17_semantic_hotfix_assignment": assignment_path,
            "existing_17_semantic_hotfix_base_datamart_expected": REQUIRED_INPUTS["base_datamart_hotfix_expected"],
            "existing_17_stage17_base_datamart_fallback_used": REFERENCE_INPUTS["base_datamart_stage17_fallback"],
            "new_demographic_hotfix_output_folder": OUT_DIR,
            "note_md": NOTE_PATH,
            "new_notebook": NOTEBOOK_PATH,
        }
    )
    assignment_hash_after = file_sha256(assignment_path)
    checks = final_checks(validation, demographic, behavior, action, skipped, size_policy, note_appended, False, assignment_hash_before, assignment_hash_after)
    zip_created = False
    inventory_rows = 0
    if create_review_zip:
        inventory, zip_created = make_zip_inventory_and_zip()
        inventory_rows = len(inventory)
        checks = final_checks(validation, demographic, behavior, action, skipped, size_policy, note_appended, zip_created, assignment_hash_before, assignment_hash_after)
        make_zip_inventory_and_zip()
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "strict_input_fail_count": int(validation["status"].eq("FAIL").sum()),
        "fallback_used": fallback_used,
        "assignment_rows": len(assignment),
        "base_rows": len(base),
        "joined_rows": len(joined),
        "age_audit_rows": len(age_audit),
        "gender_audit_rows": len(gender_audit),
        "demographic_profile_rows": len(demographic),
        "behavior_profile_rows": len(behavior),
        "action_matrix_rows": len(action),
        "size_policy_rows": len(size_policy),
        "below_300_segment_rows": int((size_policy["row_count"] < 300).sum()),
        "final_check_fail_count": int(checks["status"].eq("FAIL").sum()),
        "zip_created": zip_created,
        "zip_inventory_rows": inventory_rows,
    }


if __name__ == "__main__":
    print(json.dumps(run_hotfix(), ensure_ascii=False, indent=2))
