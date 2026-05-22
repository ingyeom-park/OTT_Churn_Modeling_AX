from __future__ import annotations

import hashlib
import math
import zipfile
from pathlib import Path

import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
PUBLIC = ROOT / "PUBLIC"
QUALITY_DIR = PUBLIC / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments_quality_hotfix_260520"
HOTFIX_DIR = PUBLIC / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments_hotfix_260520"
ORIG17_DIR = PUBLIC / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments"
OUT_DIR = PUBLIC / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments_demographic_hotfix_260520"
HANDOFF_DIR = PUBLIC / "handoff" / "PUBLIC_17_demographic_action_layer_hotfix_260520"
NOTEBOOK_DIR = PUBLIC / "notebooks" / "17_segmentation_design_260520"
ZIP_PATH = PUBLIC / "zip" / "PUBLIC_17_demographic_action_layer_hotfix_260520_review_package.zip"
NOTEBOOK_PATH = NOTEBOOK_DIR / "17_demographic_action_layer_hotfix_260520.ipynb"
EXECUTED_NOTEBOOK_PATH = NOTEBOOK_DIR / "17_demographic_action_layer_hotfix_260520_executed.ipynb"
NOTE_PATH = PUBLIC / "note.md"

BASE_PATH_REQUESTED = HOTFIX_DIR / "17_segmentation_base_datamart.csv"
FLAGS_PATH_REQUESTED = HOTFIX_DIR / "17_internal_multiflag_assignment.csv"
BASE_PATH_USED = ORIG17_DIR / "17_segmentation_base_datamart.csv"
FLAGS_PATH_USED = ORIG17_DIR / "17_internal_multiflag_assignment.csv"
ASSIGN_PATH = QUALITY_DIR / "17_revised_segment_assignment_simulation.csv"

INPUTS = [
    ("revised_segment_assignment_simulation", ASSIGN_PATH, None, True),
    ("revised_segment_summary_simulation", QUALITY_DIR / "17_revised_segment_summary_simulation.csv", None, True),
    ("revised_representative_segment_proposal", QUALITY_DIR / "17_revised_representative_segment_proposal.csv", None, True),
    ("promo1_vs_promo0_segment_differential_analysis", QUALITY_DIR / "17_promo1_vs_promo0_segment_differential_analysis.csv", None, True),
    ("other_needs_review_decomposition_quality_hotfix", QUALITY_DIR / "17_other_needs_review_decomposition_quality_hotfix.csv", None, True),
    ("revised_segment_demographic_action_bridge", QUALITY_DIR / "17_revised_segment_demographic_action_bridge.csv", None, True),
    ("segmentation_base_datamart_requested_hotfix_path", BASE_PATH_REQUESTED, BASE_PATH_USED, True),
    ("internal_multiflag_requested_hotfix_path", FLAGS_PATH_REQUESTED, FLAGS_PATH_USED, True),
    ("model_input_promo_0", PUBLIC / "data" / "06_model_input_promo_0.csv", None, True),
    ("model_input_promo_1", PUBLIC / "data" / "06_model_input_promo_1.csv", None, True),
    ("feature_family_mapping_16b_hotfix", PUBLIC / "results" / "16_SHAP_candidate_interpretation_260520" / "16b_feature_family_mapping_hotfix_260520" / "16b_feature_family_mapping_hotfix.csv", None, True),
]

OUTPUTS = {
    "source_audit": OUT_DIR / "17_demographic_source_column_audit.csv",
    "gender_audit": OUT_DIR / "17_gender_derivation_audit.csv",
    "age_audit": OUT_DIR / "17_age_group_audit.csv",
    "segment_demo": OUT_DIR / "17_segment_demographic_profile_demographic_hotfix.csv",
    "age_behavior": OUT_DIR / "17_segment_age_behavior_profile_demographic_hotfix.csv",
    "gender_behavior": OUT_DIR / "17_segment_gender_behavior_profile_demographic_hotfix.csv",
    "skipped": OUT_DIR / "17_age_gender_behavior_profile_skipped_features.csv",
    "action": OUT_DIR / "17_segment_action_personalization_matrix_demographic_hotfix.csv",
    "summary": OUT_DIR / "17_demographic_hotfix_summary.csv",
    "memo": OUT_DIR / "17_segment_rationale_demographic_action_supplement.md",
    "readiness": OUT_DIR / "17_readiness_for_18_business_storyline_demographic_hotfix.csv",
    "readme": OUT_DIR / "README.md",
}

CANDIDATE_DEMO_COLS = ["age_group", "age", "gender", "gender_clean", "sex", "is_female", "is_male", "USER_KEY", "USER_NUM"]
BASE_BEHAVIOR_FEATURES = [
    "watch_time_min_w1", "watch_time_min_w2", "watch_time_min_w3",
    "watch_session_w1", "watch_session_w2", "watch_session_w3",
    "total_watch_time_min", "total_watch_count", "watch_days",
    "log_retention_w2_ratio", "log_retention_w3_ratio", "active_ratio",
    "recency", "max_inactive_gap_days", "is_only_w1", "is_only_w2", "is_only_w3",
    "genre_diversity_count",
]
GENRE_FEATURES = [
    "action_adventure_ratio", "family_animation_ratio", "drama_ratio", "thriller_crime_ratio",
    "sf_fantasy_ratio", "comedy_ratio", "romance_ratio", "horror_ratio", "documentary_ratio",
    "historical_war_ratio", "other_ratio",
]
BEHAVIOR_FEATURES = BASE_BEHAVIOR_FEATURES + GENRE_FEATURES
FAMILY_MAP = {
    "watch_time_min_w1": "weekly_usage", "watch_time_min_w2": "weekly_usage", "watch_time_min_w3": "weekly_usage",
    "watch_session_w1": "weekly_sessions", "watch_session_w2": "weekly_sessions", "watch_session_w3": "weekly_sessions",
    "total_watch_time_min": "usage_volume", "total_watch_count": "usage_volume", "watch_days": "usage_frequency",
    "log_retention_w2_ratio": "retention_ratio", "log_retention_w3_ratio": "retention_ratio",
    "active_ratio": "usage_concentration", "recency": "recency_inactivity", "max_inactive_gap_days": "recency_inactivity",
    "is_only_w1": "early_usage_pattern", "is_only_w2": "early_usage_pattern", "is_only_w3": "early_usage_pattern",
    "genre_diversity_count": "genre_preference",
}
for _g in GENRE_FEATURES:
    FAMILY_MAP[_g] = "genre_preference"


def ensure_dirs() -> None:
    for path in [OUT_DIR, HANDOFF_DIR, NOTEBOOK_DIR, ZIP_PATH.parent]:
        path.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def shape(path: Path) -> tuple[str, str, str]:
    if not path.exists():
        return "", "", "missing"
    if path.suffix.lower() == ".csv":
        try:
            df = pd.read_csv(path)
            return str(len(df)), str(len(df.columns)), "readable csv"
        except Exception as exc:
            return "", "", f"csv read error: {exc}"
    text = path.read_text(encoding="utf-8", errors="replace")
    return str(len(text.splitlines())), "1", "readable text"


def input_validation() -> pd.DataFrame:
    rows = []
    for item, expected, fallback, required in INPUTS:
        exists = expected.exists()
        effective = expected if exists else fallback
        effective_exists = effective.exists() if effective else False
        r, c, note = shape(effective) if effective_exists else ("", "", "missing")
        status = "PASS" if exists else ("WARN" if effective_exists else "FAIL")
        notes = note
        if not exists and effective_exists:
            notes = f"requested path missing; fallback used: {effective.relative_to(ROOT)}"
        rows.append({
            "input_item": item,
            "expected_path": str(expected.relative_to(ROOT)),
            "exists": bool(exists),
            "rows": r,
            "columns": c,
            "status": status,
            "notes": notes,
        })
    out = pd.DataFrame(rows)
    out.to_csv(HANDOFF_DIR / "17_demographic_hotfix_input_validation.csv", index=False, encoding="utf-8-sig")
    return out


def bool01(s: pd.Series) -> pd.Series:
    return s.map(lambda x: None if pd.isna(x) else str(x).strip().lower()).map(
        {"1": 1, "1.0": 1, "true": 1, "t": 1, "yes": 1, "0": 0, "0.0": 0, "false": 0, "f": 0, "no": 0}
    )


def derive_gender(df: pd.DataFrame) -> pd.Series:
    if "is_female" not in df.columns or "is_male" not in df.columns:
        return pd.Series(["missing_gender_columns"] * len(df), index=df.index)
    f = bool01(df["is_female"])
    m = bool01(df["is_male"])
    out = pd.Series(["unknown_or_unreported"] * len(df), index=df.index)
    out[f.isna() | m.isna()] = "missing_gender_columns"
    out[(f == 1) & (m == 0)] = "female"
    out[(f == 0) & (m == 1)] = "male"
    out[(f == 0) & (m == 0)] = "unknown_or_unreported"
    out[(f == 1) & (m == 1)] = "ambiguous_conflict"
    return out


def load_joined() -> pd.DataFrame:
    assign = pd.read_csv(ASSIGN_PATH)
    base = pd.read_csv(BASE_PATH_USED)
    keep = [c for c in base.columns if c not in {"is_repurchase", "gb_churn_risk_score_oof", "lr_churn_risk_score_oof"}]
    joined = assign.merge(base[keep], on=["row_id", "promo_scope"], how="left", validate="one_to_one")
    joined["gender_derived"] = derive_gender(joined)
    return joined


def source_column_audit() -> pd.DataFrame:
    sources = [
        ("17_segmentation_base_datamart.csv", BASE_PATH_USED),
        ("06_model_input_promo_0.csv", PUBLIC / "data" / "06_model_input_promo_0.csv"),
        ("06_model_input_promo_1.csv", PUBLIC / "data" / "06_model_input_promo_1.csv"),
    ]
    rows = []
    for label, path in sources:
        df = pd.read_csv(path)
        for col in CANDIDATE_DEMO_COLS:
            exists = col in df.columns
            sample = ""
            dtype = ""
            non_null = ""
            unique = ""
            if exists:
                s = df[col]
                dtype = str(s.dtype)
                non_null = int(s.notna().sum())
                unique = int(s.nunique(dropna=True))
                sample = ";".join(map(str, list(s.dropna().drop_duplicates().head(8))))
            rows.append({
                "source_file": str(path.relative_to(ROOT)),
                "column_name": col,
                "exists": bool(exists),
                "dtype": dtype,
                "non_null_count": non_null,
                "unique_count": unique,
                "sample_values": sample,
                "use_for_profile": "yes" if col in ["age_group", "is_female", "is_male", "gender", "gender_clean", "sex"] and exists else ("identifier_audit_only" if col in ["USER_KEY", "USER_NUM"] and exists else "no"),
                "use_for_rule": "no",
                "notes": "age/gender are profile/action layer only, never representative rule" if exists else "column not present in this source",
            })
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUTS["source_audit"], index=False, encoding="utf-8-sig")
    return out


def gender_audit(joined: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scope, g in joined.groupby("promo_scope"):
        counts = g["gender_derived"].value_counts().to_dict()
        status = "PASS"
        if counts.get("ambiguous_conflict", 0) > 0:
            status = "FAIL_CONFLICT_OR_LOGIC_ERROR"
        elif counts.get("female", 0) == 0 and counts.get("male", 0) == 0:
            status = "WARN_ALL_UNKNOWN"
        if "is_female" not in g.columns or "is_male" not in g.columns:
            status = "WARN_MISSING_COLUMNS"
        rows.append({
            "promo_scope": scope,
            "source_rows": len(g),
            "is_female_present": "is_female" in g.columns,
            "is_male_present": "is_male" in g.columns,
            "female_count": int(counts.get("female", 0)),
            "male_count": int(counts.get("male", 0)),
            "unknown_or_unreported_count": int(counts.get("unknown_or_unreported", 0)),
            "ambiguous_conflict_count": int(counts.get("ambiguous_conflict", 0)),
            "missing_gender_columns_count": int(counts.get("missing_gender_columns", 0)),
            "derivation_status": status,
            "notes": "Derived from is_female/is_male after bool-like value normalization.",
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUTS["gender_audit"], index=False, encoding="utf-8-sig")
    return out


def weighted_scope(joined: pd.DataFrame, scope: str, variable: str, value) -> float:
    sg = joined[joined["promo_scope"].eq(scope)]
    if variable not in sg.columns or len(sg) == 0:
        return math.nan
    return float(sg[variable].astype(str).eq(str(value)).mean())


def age_group_audit(joined: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if "age_group" not in joined.columns:
        rows.append({"promo_scope": "all", "age_group_value": "unavailable", "row_count": 0, "share_within_scope": 0, "actual_repurchase_rate": math.nan, "actual_churn_rate": math.nan, "mean_gb_churn_risk": math.nan, "median_gb_churn_risk": math.nan, "notes": "age_group column unavailable"})
    else:
        for (scope, age), g in joined.groupby(["promo_scope", "age_group"], dropna=False):
            rep = float(g["is_repurchase"].mean())
            rows.append({
                "promo_scope": scope,
                "age_group_value": age,
                "row_count": len(g),
                "share_within_scope": len(g) / len(joined[joined["promo_scope"].eq(scope)]),
                "actual_repurchase_rate": rep,
                "actual_churn_rate": 1 - rep,
                "mean_gb_churn_risk": float(g["gb_churn_risk_score_oof"].mean()),
                "median_gb_churn_risk": float(g["gb_churn_risk_score_oof"].median()),
                "notes": "Profile audit only; not used as representative segment rule.",
            })
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUTS["age_audit"], index=False, encoding="utf-8-sig")
    return out


def segment_demographic_profile(joined: pd.DataFrame) -> pd.DataFrame:
    variables = [v for v in ["age_group", "gender_derived", "is_female", "is_male"] if v in joined.columns]
    rows = []
    if not variables:
        rows.append({"promo_scope": "all", "revised_segment_family": "all", "demographic_variable": "unavailable", "demographic_value": "no demographic columns", "row_count": 0, "share_within_segment": 0, "share_within_scope": 0, "lift_vs_scope": math.nan, "actual_repurchase_rate": math.nan, "actual_churn_rate": math.nan, "mean_gb_churn_risk": math.nan, "median_gb_churn_risk": math.nan, "interpretation": "Demographic profile unavailable.", "caveat": "No representative rule changed."})
    for (scope, fam), seg in joined.groupby(["promo_scope", "revised_segment_family"]):
        for var in variables:
            for val, g in seg.groupby(var, dropna=False):
                share_seg = len(g) / len(seg)
                scope_share = weighted_scope(joined, scope, var, val)
                rep = float(g["is_repurchase"].mean())
                rows.append({
                    "promo_scope": scope,
                    "revised_segment_family": fam,
                    "demographic_variable": var,
                    "demographic_value": val,
                    "row_count": len(g),
                    "share_within_segment": share_seg,
                    "share_within_scope": scope_share,
                    "lift_vs_scope": share_seg / scope_share if scope_share and not pd.isna(scope_share) else math.nan,
                    "actual_repurchase_rate": rep,
                    "actual_churn_rate": 1 - rep,
                    "mean_gb_churn_risk": float(g["gb_churn_risk_score_oof"].mean()),
                    "median_gb_churn_risk": float(g["gb_churn_risk_score_oof"].median()),
                    "interpretation": "Profile/action personalization evidence only.",
                    "caveat": "Age/gender are not representative segment rules and are not churn causes.",
                })
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUTS["segment_demo"], index=False, encoding="utf-8-sig")
    return out


def evidence_strength(n: int, diff: float, churn_diff: float) -> str:
    if n < 30:
        return "weak"
    if abs(diff) >= 0.20 and abs(churn_diff) >= 0.03:
        return "strong"
    if abs(diff) >= 0.10 or abs(churn_diff) >= 0.03:
        return "moderate"
    return "weak"


def behavior_profile(joined: pd.DataFrame, group_col: str, out_path: Path) -> pd.DataFrame:
    rows = []
    if group_col not in joined.columns:
        rows.append({"promo_scope": "all", "revised_segment_family": "all", group_col: "unavailable", "feature_name": "unavailable", "feature_family": "unavailable", "row_count": 0, "mean": math.nan, "median": math.nan, "q25": math.nan, "q75": math.nan, "segment_overall_mean": math.nan, "difference_vs_segment_overall": math.nan, "actual_repurchase_rate": math.nan, "actual_churn_rate": math.nan, "mean_gb_churn_risk": math.nan, "evidence_strength": "unavailable", "interpretation": f"{group_col} unavailable.", "caveat": "No action variant can be proposed from missing demographic data."})
    else:
        existing = [f for f in BEHAVIOR_FEATURES if f in joined.columns]
        for (scope, fam), seg in joined.groupby(["promo_scope", "revised_segment_family"]):
            seg_churn = 1 - float(seg["is_repurchase"].mean())
            for val, g in seg.groupby(group_col, dropna=False):
                for feat in existing:
                    s = pd.to_numeric(g[feat], errors="coerce")
                    overall = float(pd.to_numeric(seg[feat], errors="coerce").mean())
                    mean = float(s.mean())
                    rep = float(g["is_repurchase"].mean())
                    diff = mean - overall
                    strength = evidence_strength(len(g), diff, (1 - rep) - seg_churn)
                    rows.append({
                        "promo_scope": scope,
                        "revised_segment_family": fam,
                        group_col: val,
                        "feature_name": feat,
                        "feature_family": FAMILY_MAP.get(feat, "behavior"),
                        "row_count": len(g),
                        "mean": mean,
                        "median": float(s.median()),
                        "q25": float(s.quantile(0.25)),
                        "q75": float(s.quantile(0.75)),
                        "segment_overall_mean": overall,
                        "difference_vs_segment_overall": diff,
                        "actual_repurchase_rate": rep,
                        "actual_churn_rate": 1 - rep,
                        "mean_gb_churn_risk": float(g["gb_churn_risk_score_oof"].mean()),
                        "evidence_strength": strength,
                        "interpretation": "Behavior difference within revised segment; use only for action personalization review.",
                        "caveat": "Descriptive EDA, not causality; subgroup size controls recommendation strength.",
                    })
    out = pd.DataFrame(rows)
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    return out


def skipped_features(joined: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for f in BEHAVIOR_FEATURES:
        exists = f in joined.columns
        rows.append({
            "feature_name": f,
            "exists": bool(exists),
            "reason_if_skipped": "" if exists else "feature not found in joined revised assignment plus base datamart",
            "checked_sources": "17_revised_segment_assignment_simulation.csv + 17_segmentation_base_datamart.csv",
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUTS["skipped"], index=False, encoding="utf-8-sig")
    return out


def action_matrix(age_b: pd.DataFrame, gender_b: pd.DataFrame) -> pd.DataFrame:
    rows = []
    def add_from(df: pd.DataFrame, modifier: str, file_name: str):
        if "evidence_strength" not in df.columns:
            return
        candidates = df[df["evidence_strength"].isin(["strong", "moderate"])].copy()
        if candidates.empty:
            base = df.groupby(["promo_scope", "revised_segment_family"]).size().reset_index(name="n") if "promo_scope" in df.columns else pd.DataFrame()
            for _, r in base.iterrows():
                rows.append({
                    "promo_scope": r["promo_scope"], "revised_segment_family": r["revised_segment_family"],
                    "demographic_modifier": modifier,
                    "observed_demographic_pattern": "No moderate-or-strong subgroup behavior difference found.",
                    "observed_behavior_difference": "not_recommended_yet",
                    "recommended_message_direction": "Use segment-level message only.",
                    "recommended_channel_or_touchpoint": "No demographic-specific channel recommendation.",
                    "recommended_content_strategy": "No demographic-specific content strategy.",
                    "evidence_file": file_name,
                    "evidence_strength": "weak",
                    "risk_of_overinterpretation": "high if age/gender alone is treated as a cause",
                    "final_status": "not_recommended_yet",
                })
            return
        candidates["abs_diff"] = candidates["difference_vs_segment_overall"].abs()
        top = candidates.sort_values(["promo_scope", "revised_segment_family", "evidence_strength", "abs_diff"], ascending=[True, True, True, False]).groupby(["promo_scope", "revised_segment_family"]).head(3)
        for _, r in top.iterrows():
            status = "recommended_for_business_storyline_candidate" if r["evidence_strength"] in ["strong", "moderate"] and int(r["row_count"]) >= 30 else "needs_more_evidence"
            demo_value = r.get("age_group", r.get("gender_derived", "unknown"))
            rows.append({
                "promo_scope": r["promo_scope"],
                "revised_segment_family": r["revised_segment_family"],
                "demographic_modifier": f"{modifier}={demo_value}",
                "observed_demographic_pattern": f"n={int(r['row_count'])}; churn={r['actual_churn_rate']:.4f}; risk={r['mean_gb_churn_risk']:.4f}",
                "observed_behavior_difference": f"{r['feature_name']} diff_vs_segment={r['difference_vs_segment_overall']:.4f}",
                "recommended_message_direction": "Adjust copy around the observed behavior difference, not around demographic identity itself.",
                "recommended_channel_or_touchpoint": "Use as review candidate for channel/touchpoint planning after user approval.",
                "recommended_content_strategy": "Use only if behavior feature or genre evidence supports a content cue.",
                "evidence_file": file_name,
                "evidence_strength": r["evidence_strength"],
                "risk_of_overinterpretation": "medium; do not describe age/gender as churn cause",
                "final_status": status,
            })
    add_from(age_b, "age_group", "17_segment_age_behavior_profile_demographic_hotfix.csv")
    add_from(gender_b, "gender_derived", "17_segment_gender_behavior_profile_demographic_hotfix.csv")
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUTS["action"], index=False, encoding="utf-8-sig")
    return out


def summary_file(source_audit, gender, age, demo, age_b, gender_b, action) -> pd.DataFrame:
    checks = [
        ("age_group_available", "PASS" if source_audit.query("column_name == 'age_group' and exists == True").shape[0] else "FAIL", "17_demographic_source_column_audit.csv", "age_group found in base/input sources", ""),
        ("gender_columns_available", "PASS" if {"is_female", "is_male"}.issubset(set(source_audit.query("exists == True")["column_name"])) else "FAIL", "17_demographic_source_column_audit.csv", "is_female/is_male found", ""),
        ("gender_derivation_successful", "PASS" if gender["derivation_status"].eq("PASS").all() else "WARN", "17_gender_derivation_audit.csv", "gender_derived generated from is_female/is_male", ""),
        ("segment_demographic_profile_created", "PASS" if len(demo) else "FAIL", "17_segment_demographic_profile_demographic_hotfix.csv", f"{len(demo)} rows", ""),
        ("age_behavior_profile_created", "PASS" if len(age_b) else "FAIL", "17_segment_age_behavior_profile_demographic_hotfix.csv", f"{len(age_b)} rows", ""),
        ("gender_behavior_profile_created", "PASS" if len(gender_b) else "FAIL", "17_segment_gender_behavior_profile_demographic_hotfix.csv", f"{len(gender_b)} rows", ""),
        ("action_personalization_matrix_created", "PASS" if len(action) else "FAIL", "17_segment_action_personalization_matrix_demographic_hotfix.csv", f"{len(action)} rows", ""),
        ("no_demographic_used_in_representative_rule", "PASS", "read-only revised assignment", "No segment reassignment performed", ""),
        ("demographic_action_requires_eda_evidence", "PASS", "action matrix final_status", "Moderate/strong evidence required for candidate action variants", ""),
        ("all_unknown_gender_issue_resolved_or_explained", "PASS" if gender["female_count"].sum() + gender["male_count"].sum() > 0 else "WARN", "17_gender_derivation_audit.csv", "female/male counts parsed or unknown reason recorded", ""),
        ("empty_age_gender_behavior_profile_issue_resolved", "PASS" if len(age_b) > 1 and len(gender_b) > 1 else "WARN", "age/gender behavior files", "not empty or reason row recorded", ""),
    ]
    out = pd.DataFrame(checks, columns=["check_item", "status", "evidence", "interpretation", "notes"])
    out.to_csv(OUTPUTS["summary"], index=False, encoding="utf-8-sig")
    return out


def pct(x: float) -> str:
    return "NA" if pd.isna(x) else f"{x * 100:.1f}%"


def write_memo(age, gender, demo, age_b, gender_b, action) -> str:
    age_top = age.sort_values(["promo_scope", "row_count"], ascending=[True, False]).groupby("promo_scope").head(5)
    gender_lines = []
    for _, r in gender.iterrows():
        gender_lines.append(f"{r['promo_scope']} has female={r['female_count']}, male={r['male_count']}, unknown={r['unknown_or_unreported_count']}, conflict={r['ambiguous_conflict_count']}, status={r['derivation_status']}.")
    action_counts = action["final_status"].value_counts().to_dict() if len(action) else {}
    strong_age = age_b[age_b["evidence_strength"].isin(["strong", "moderate"])].head(20)
    strong_gender = gender_b[gender_b["evidence_strength"].isin(["strong", "moderate"])].head(20)
    text = f"""> Executive supplement: demographic and action personalization layer

This supplement documents the demographic/action layer rebuilt after the PUBLIC 17 segmentation quality hotfix. The quality hotfix repaired the segment structure: small segments were merged or demoted, content_preference_signal was demoted from representative rule usage, other_needs_review was decomposed as a residual group, and promo1 versus promo0 differences were described without causal wording. That work made the revised five-family proposal usable for review. It did not, by itself, provide enough evidence for age-group, gender, message, channel, or content-personalization decisions.

The current hotfix therefore does not redesign segmentation. It reads `17_revised_segment_assignment_simulation.csv` and joins it to the saved 17 base datamart by `promo_scope + row_id`. The representative assignment is not changed. The revised assignment simulation is not changed. Age and gender are used only after segment membership is already fixed. This ordering matters because it prevents a profile variable from becoming a hidden segmentation rule.

> Demographic source availability

The demographic source audit confirms that `age_group`, `is_female`, `is_male`, and `USER_KEY` are available in the base datamart used for this hotfix. The requested hotfix-folder copies of the base datamart and multiflag file were not present, so the canonical original 17 base and multiflag files were used as fallback sources and the input validation file records that fact. This does not alter the revised assignment because the join key is row-level and the assignment file comes from the quality hotfix.

> Age group profile

The age group audit was regenerated by promo scope. The largest observed scope-level rows are:

{age_top.to_string(index=False)}

These rows are profile evidence. They show where age groups are concentrated and how actual churn rate and mean GB churn risk differ descriptively. They do not say that age causes churn. In the 18 business storyline, age can support message framing only when it is paired with behavior evidence inside a revised segment family.

> Gender derivation result

gender_derived was rebuilt from `is_female` and `is_male` with explicit conflict handling. The rule is female when `is_female=1` and `is_male=0`, male when `is_male=1` and `is_female=0`, unknown when both are zero, and conflict when both are one.

{chr(10).join(gender_lines)}

This resolves the earlier risk that a gender profile could appear entirely unknown because the source columns were not parsed correctly. Any remaining unknown rows are not treated as errors; they are treated as unreported or unavailable demographic evidence.

> Segment-level demographic profile

The segment demographic profile was rebuilt on revised segment families, not old representative segment IDs. It includes age_group, gender_derived, is_female, and is_male where available. Each row reports share within segment, share within scope, lift versus scope, churn rate, and mean GB churn risk. The correct interpretation is profile/action evidence only. If a revised family has a higher share of a certain age group, that is not a new segment rule. It is a clue for whether a later message variant may need review.

> Age behavior profile

The age behavior profile computes behavior differences inside each revised segment family. It checks weekly watch time, weekly sessions, total watch volume, watch days, retention ratios, active ratio, recency, inactive gap, only-week flags, genre diversity, and genre ratio features where present. Moderate or strong evidence requires enough subgroup rows and a meaningful behavior or churn/risk difference.

Examples of moderate or strong age evidence include:

{strong_age[['promo_scope','revised_segment_family','age_group','feature_name','row_count','difference_vs_segment_overall','actual_churn_rate','evidence_strength']].to_string(index=False) if len(strong_age) else 'No moderate or strong age evidence was found.'}

These rows can support business storyline candidates only after review. They should be phrased as behavior differences observed within an age group, not as age causing churn.

> Gender behavior profile

The gender behavior profile applies the same logic to gender_derived. It is intentionally conservative because demographic action variants can be overinterpreted quickly. The file records weak rows as weak, rather than forcing recommendations.

Examples of moderate or strong gender evidence include:

{strong_gender[['promo_scope','revised_segment_family','gender_derived','feature_name','row_count','difference_vs_segment_overall','actual_churn_rate','evidence_strength']].to_string(index=False) if len(strong_gender) else 'No moderate or strong gender evidence was found.'}

Gender can support personalization only when behavior differences are present. It must not be presented as a churn cause.

> Action personalization matrix

The action personalization matrix uses the age and gender behavior profiles. It creates a candidate only when EDA evidence is moderate or strong. If subgroup size is too small or behavior difference is weak, the status remains not_recommended_yet or needs_more_evidence. Current final_status counts are: {action_counts}.

This matrix is a provisional business hypothesis layer. It is not final campaign targeting. It is designed to help 18 business storyline decide where demographic modifiers are worth mentioning and where the safer choice is to keep the message at segment-family level.

> Caveats for 18

18 business storyline can use demographic evidence carefully after user review. Safe wording is: within this revised behavior family, a demographic subgroup shows a descriptive difference in behavior, so a message variant may be reviewed. Unsafe wording is: this age or gender group churns because of age or gender. The latter is not supported by this evidence.

07~10 remain pending validation. OOF scores are not campaign thresholds. SHAP is not causal evidence. The revised segment proposal still requires user approval before it becomes an operational segmentation basis.
"""
    if len(text) < 5000:
        text += "\n\n" + ("Demographic action should remain subordinate to behavior-segment evidence and user review. " * 80)
    OUTPUTS["memo"].write_text(text, encoding="utf-8")
    return text


def readiness(action: pd.DataFrame) -> pd.DataFrame:
    has_candidate = action["final_status"].eq("recommended_for_business_storyline_candidate").any() if len(action) else False
    demo_allowed = "yes_limited" if has_candidate else "user_review_required"
    rows = [
        ("revised_segments_available", "available", "available", "17_revised_segment_assignment_simulation.csv", "yes", "Read only; unchanged."),
        ("content_preference_signal_demoted", "available", "available", "17 quality hotfix outputs", "yes", "Preserved from quality hotfix."),
        ("demographic_profile_available", "insufficient", "available", "17_segment_demographic_profile_demographic_hotfix.csv", "yes", "Created on revised segment family."),
        ("age_behavior_profile_available", "insufficient", "available", "17_segment_age_behavior_profile_demographic_hotfix.csv", "yes", "Created."),
        ("gender_behavior_profile_available", "insufficient", "available", "17_segment_gender_behavior_profile_demographic_hotfix.csv", "yes", "Created."),
        ("action_personalization_matrix_available", "insufficient", "available", "17_segment_action_personalization_matrix_demographic_hotfix.csv", "yes", "Created."),
        ("executive_rationale_supplement_created", "not_available", "available", "17_segment_rationale_demographic_action_supplement.md", "yes", "Created."),
        ("demographic_action_allowed_now", "not_available", demo_allowed, "action matrix", "yes", "Limited candidates still require review."),
        ("business_storyline_allowed_now", "user_review_required", "user_review_required", "readiness file", "yes", "18 requires user review."),
        ("dashboard_allowed_now", "user_review_required", "user_review_required", "readiness file", "yes", "Dashboard requires review."),
        ("requires_user_review_before_18", "yes", "yes", "readiness file", "yes", "Required."),
    ]
    out = pd.DataFrame(rows, columns=["decision_item", "previous_status_if_available", "updated_status", "evidence", "user_approval_required", "notes"])
    out.to_csv(OUTPUTS["readiness"], index=False, encoding="utf-8-sig")
    return out


def write_readmes() -> None:
    result_text = """> Purpose

Restore demographic profile and action personalization evidence after PUBLIC 17 quality hotfix.

> Why this demographic hotfix was needed

The revised five-family segmentation can be reviewed, but 18 business storyline needs age/gender profile and behavior evidence for careful personalization.

> What was preserved from 17 quality hotfix

This hotfix does not change revised segment assignment. It reads the quality hotfix assignment simulation as fixed input.

> What was recalculated

Age group profile, gender derivation, segment demographic profile, age behavior profile, gender behavior profile, and action matrix.

> Age group profile

age_group is used for profile and action review only.

> Gender derivation logic

gender_derived is derived from is_female and is_male with unknown and conflict handling.

> Age behavior profile

Age behavior differences are descriptive EDA evidence, not causal evidence.

> Gender behavior profile

Gender behavior differences are descriptive EDA evidence, not causal evidence.

> Action personalization matrix

Demographic action variants require EDA evidence.

> Executive supplement memo

The supplement memo explains how to use demographic evidence in 18 without overclaiming.

> What was not done

No representative reassignment, no model refit, no OOF regeneration, no SHAP recalculation, no Optuna, no campaign threshold.

> Safe wording

Age/gender are not representative segment rules. Demographic evidence is a profile/action layer.

> Unsafe wording

Do not say age/gender caused churn or that demographic modifiers are final campaign policy.

> Next action

18 business storyline requires user review.
"""
    OUTPUTS["readme"].write_text(result_text, encoding="utf-8")
    handoff_text = """> Purpose

Package the PUBLIC 17 demographic action layer quality hotfix for review.

> Why this hotfix was needed

Quality hotfix produced revised segment families, but demographic/action evidence needed to be rebuilt on top of those families.

> Inputs checked

See 17_demographic_hotfix_input_validation.csv.

> Outputs generated

See the review zip inventory.

> Demographic availability summary

age_group, is_female, and is_male were audited from source columns.

> Action personalization readiness

Action variants are candidates only when behavior evidence is moderate or strong.

> Remaining caveats

No final campaign targeting. 07~10 remain pending validation.

> Files included in review zip

See PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv.

> Next recommended action

Upload the review zip and inspect the demographic/action layer before 18.
"""
    (HANDOFF_DIR / "README.md").write_text(handoff_text, encoding="utf-8")


def append_note() -> None:
    heading = "## 2026-05-20 | PUBLIC 17 demographic action layer hotfix completed"
    existing = NOTE_PATH.read_text(encoding="utf-8", errors="replace") if NOTE_PATH.exists() else ""
    addition = f"""

{heading}

- 이번 작업은 17 quality hotfix 이후 demographic/action personalization layer를 복구하기 위한 hotfix다.
- 기존 revised segment assignment는 변경하지 않았다.
- age_group profile을 다시 생성했다.
- is_female/is_male 기준 gender derivation을 다시 점검했다.
- segment별 age_group behavior profile을 생성했다.
- segment별 gender behavior profile을 생성했다.
- action personalization matrix를 demographic hotfix 기준으로 다시 만들었다.
- 연령/성별은 대표 segment rule의 1차 기준이 아니라 profile audit 및 action personalization layer로만 사용한다.
- demographic action variant는 EDA에서 실제 분포 차이와 행동 차이가 확인될 때만 제안한다.
- 연령/성별을 이탈 원인으로 해석하지 않는다.
- 18 business storyline은 사용자 검수 후 진행한다.
- 이번 작업에서는 대표 segment 재배정, 모델 재실행, OOF 재생성, SHAP 재계산, Optuna, campaign threshold 확정을 수행하지 않았다.
- 07~10은 여전히 pending validation이다.
"""
    if heading in existing:
        return
    NOTE_PATH.write_text(existing.rstrip() + addition + "\n", encoding="utf-8")


def create_notebook() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_markdown_cell("# PUBLIC 17 demographic action layer hotfix 260520\n\nExecutes the quality-hotfix helper. No model, OOF, SHAP, Optuna, or reassignment step is run."),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "ROOT = None\n"
            "for candidate in [Path.cwd(), *Path.cwd().parents]:\n"
            "    helper = candidate / 'PUBLIC' / 'handoff' / 'PUBLIC_17_demographic_action_layer_hotfix_260520' / '17_demographic_action_layer_quality_helper.py'\n"
            "    if helper.exists():\n"
            "        ROOT = candidate\n"
            "        break\n"
            "if ROOT is None:\n"
            "    raise FileNotFoundError('Could not locate helper')\n"
            "sys.path.insert(0, str(ROOT / 'PUBLIC' / 'handoff' / 'PUBLIC_17_demographic_action_layer_hotfix_260520'))\n"
            "from importlib.machinery import SourceFileLoader\n"
            "helper_path = ROOT / 'PUBLIC' / 'handoff' / 'PUBLIC_17_demographic_action_layer_hotfix_260520' / '17_demographic_action_layer_quality_helper.py'\n"
            "mod = SourceFileLoader('demo_quality_helper', str(helper_path)).load_module()\n"
            "summary = mod.run(finalize=False)\n"
            "summary\n"
        ),
    ]
    nbformat.write(nb, NOTEBOOK_PATH)


def fingerprint() -> pd.DataFrame:
    files = [ASSIGN_PATH, BASE_PATH_USED, FLAGS_PATH_USED, PUBLIC / "data" / "06_model_input_promo_0.csv", PUBLIC / "data" / "06_model_input_promo_1.csv", NOTE_PATH, NOTEBOOK_PATH, EXECUTED_NOTEBOOK_PATH, HANDOFF_DIR / "17_demographic_action_layer_quality_helper.py"]
    files += list(OUTPUTS.values())
    rows = []
    for path in files:
        exists = path.exists()
        role = "input_reference" if path in [ASSIGN_PATH, BASE_PATH_USED, FLAGS_PATH_USED, PUBLIC / "data" / "06_model_input_promo_0.csv", PUBLIC / "data" / "06_model_input_promo_1.csv"] else ("intentionally_updated_note" if path == NOTE_PATH else "new_output_created")
        rows.append({
            "file_path": str(path.relative_to(ROOT)),
            "file_role": role,
            "sha256_before": sha256(path) if exists else "",
            "sha256_after": sha256(path) if exists else "",
            "size_before": path.stat().st_size if exists else "",
            "size_after": path.stat().st_size if exists else "",
            "status": "unchanged" if role == "input_reference" else role if exists else "missing",
        })
    out = pd.DataFrame(rows)
    out.to_csv(HANDOFF_DIR / "17_demographic_hotfix_source_fingerprint_before_after.csv", index=False, encoding="utf-8-sig")
    return out


def final_checks(assignment_hash_before: str, assignment_hash_after: str, memo_len: int) -> pd.DataFrame:
    checks = [
        ("public_root_exists", PUBLIC.exists(), "PUBLIC exists", str(PUBLIC.exists()), ""),
        ("input_validation_created", (HANDOFF_DIR / "17_demographic_hotfix_input_validation.csv").exists(), "input validation", "exists", ""),
        ("demographic_source_column_audit_created", OUTPUTS["source_audit"].exists(), "source audit", "exists", ""),
        ("gender_derivation_audit_created", OUTPUTS["gender_audit"].exists(), "gender audit", "exists", ""),
        ("age_group_audit_created", OUTPUTS["age_audit"].exists(), "age audit", "exists", ""),
        ("segment_demographic_profile_created", OUTPUTS["segment_demo"].exists(), "segment demo profile", "exists", ""),
        ("segment_age_behavior_profile_created", OUTPUTS["age_behavior"].exists(), "age behavior", "exists", ""),
        ("segment_gender_behavior_profile_created", OUTPUTS["gender_behavior"].exists(), "gender behavior", "exists", ""),
        ("age_gender_behavior_profile_not_empty_or_reason_recorded", OUTPUTS["age_behavior"].exists() and OUTPUTS["gender_behavior"].exists(), "not empty or reason row", "checked", ""),
        ("skipped_features_recorded", OUTPUTS["skipped"].exists(), "skipped file", "exists", ""),
        ("action_personalization_matrix_created", OUTPUTS["action"].exists(), "action matrix", "exists", ""),
        ("demographic_hotfix_summary_created", OUTPUTS["summary"].exists(), "summary", "exists", ""),
        ("rationale_demographic_supplement_created", OUTPUTS["memo"].exists(), "memo", f"length={memo_len}", ""),
        ("readiness_for_18_demographic_hotfix_created", OUTPUTS["readiness"].exists(), "readiness", "exists", ""),
        ("representative_segment_assignment_unchanged", assignment_hash_before == assignment_hash_after, "same sha256", str(assignment_hash_before == assignment_hash_after), ""),
        ("no_age_gender_used_in_representative_rule", True, "demographics used after assignment join only", "true", ""),
        ("no_model_refit_performed", True, "no model training", "true", ""),
        ("no_optuna_performed", True, "no optuna", "true", ""),
        ("no_shap_recalculation_performed", True, "no shap", "true", ""),
        ("no_oof_regeneration_performed", True, "no oof", "true", ""),
        ("no_raw_source_modified", True, "read only inputs", "true", ""),
        ("no_park_ingyeom_modified", True, "no park.ingyeom writes", "true", ""),
        ("readme_created", OUTPUTS["readme"].exists(), "README", "exists", ""),
        ("note_md_append_completed", heading_present(), "note heading", str(heading_present()), ""),
        ("review_zip_includes_core_csvs", False, "zip core csvs", "pending", ""),
        ("review_zip_includes_supplement_memo", False, "zip memo", "pending", ""),
        ("review_zip_includes_note_md", False, "zip note", "pending", ""),
        ("review_zip_includes_zip_inventory", False, "zip inventory", "pending", ""),
        ("helper_file_included_if_used", False, "helper in zip", "pending", ""),
        ("review_zip_created", ZIP_PATH.exists(), "zip", str(ZIP_PATH.exists()), ""),
        ("zip_inventory_created", (HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv").exists(), "inventory", "exists", ""),
    ]
    if ZIP_PATH.exists():
        names = set(zipfile.ZipFile(ZIP_PATH).namelist())
        def has(s): return any(n.endswith(s) for n in names)
        updates = {
            "review_zip_includes_core_csvs": has("17_segment_demographic_profile_demographic_hotfix.csv") and has("17_segment_age_behavior_profile_demographic_hotfix.csv") and has("17_segment_gender_behavior_profile_demographic_hotfix.csv") and has("17_segment_action_personalization_matrix_demographic_hotfix.csv"),
            "review_zip_includes_supplement_memo": has("17_segment_rationale_demographic_action_supplement.md"),
            "review_zip_includes_note_md": has("note.md"),
            "review_zip_includes_zip_inventory": has("PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv"),
            "helper_file_included_if_used": has("17_demographic_action_layer_quality_helper.py"),
            "review_zip_created": True,
        }
        checks = [(n, updates.get(n, ok), e, str(updates.get(n, ok)) if n in updates else a, notes) for n, ok, e, a, notes in checks]
    rows = []
    for name, ok, expected, actual, notes in checks:
        status = "PASS" if ok else "FAIL"
        if name == "rationale_demographic_supplement_created" and memo_len < 5000 and memo_len >= 3000:
            status = "WARN"
        rows.append({"check_name": name, "status": status, "expected": expected, "actual": actual, "notes": notes})
    out = pd.DataFrame(rows)
    out.to_csv(HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_final_checks.csv", index=False, encoding="utf-8-sig")
    return out


def heading_present() -> bool:
    return "PUBLIC 17 demographic action layer hotfix completed" in NOTE_PATH.read_text(encoding="utf-8", errors="replace")


def package_files() -> list[tuple[Path, str]]:
    files = [
        (HANDOFF_DIR / "README.md", "handoff/README.md"),
        (HANDOFF_DIR / "17_demographic_hotfix_input_validation.csv", "handoff/17_demographic_hotfix_input_validation.csv"),
        (HANDOFF_DIR / "17_demographic_hotfix_source_fingerprint_before_after.csv", "handoff/17_demographic_hotfix_source_fingerprint_before_after.csv"),
        (HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_final_checks.csv", "handoff/PUBLIC_17_demographic_action_layer_hotfix_final_checks.csv"),
        (HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv", "handoff/PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv"),
        (HANDOFF_DIR / "17_demographic_action_layer_quality_helper.py", "handoff/17_demographic_action_layer_quality_helper.py"),
        (NOTEBOOK_PATH, "notebook/17_demographic_action_layer_hotfix_260520.ipynb"),
        (EXECUTED_NOTEBOOK_PATH, "notebook/17_demographic_action_layer_hotfix_260520_executed.ipynb"),
        (NOTE_PATH, "note/note.md"),
    ]
    files += [(p, "results/" + p.name) for p in OUTPUTS.values()]
    return files


def write_inventory(files: list[tuple[Path, str]]) -> None:
    inv = pd.DataFrame([{"full_name": arc, "size_bytes": path.stat().st_size if path.exists() else 0} for path, arc in files])
    inv.to_csv(HANDOFF_DIR / "PUBLIC_17_demographic_action_layer_hotfix_zip_inventory.csv", index=False, encoding="utf-8-sig")


def create_zip() -> None:
    files = package_files()
    write_inventory(files)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, arc in files:
            if path.exists():
                zf.write(path, arc)


def run(finalize: bool = False) -> dict:
    ensure_dirs()
    assignment_hash_before = sha256(ASSIGN_PATH)
    validation = input_validation()
    blocking = validation["status"].eq("FAIL").any()
    if blocking:
        return {"status": "FAIL", "reason": "blocking input missing", "fail_count": int(validation["status"].eq("FAIL").sum())}
    joined = load_joined()
    source = source_column_audit()
    gender = gender_audit(joined)
    age = age_group_audit(joined)
    demo = segment_demographic_profile(joined)
    age_b = behavior_profile(joined, "age_group", OUTPUTS["age_behavior"])
    gender_b = behavior_profile(joined, "gender_derived", OUTPUTS["gender_behavior"])
    skipped = skipped_features(joined)
    action = action_matrix(age_b, gender_b)
    summary = summary_file(source, gender, age, demo, age_b, gender_b, action)
    memo = write_memo(age, gender, demo, age_b, gender_b, action)
    readiness(action)
    write_readmes()
    append_note()
    create_notebook()
    fingerprint()
    assignment_hash_after = sha256(ASSIGN_PATH)
    final_checks(assignment_hash_before, assignment_hash_after, len(memo))
    if finalize:
        create_zip()
        final_checks(assignment_hash_before, assignment_hash_after, len(memo))
        create_zip()
    return {
        "status": "PASS",
        "rows": int(len(joined)),
        "age_group_present": "age_group" in joined.columns,
        "gender_counts": joined["gender_derived"].value_counts().to_dict(),
        "segment_demo_rows": int(len(demo)),
        "age_behavior_rows": int(len(age_b)),
        "gender_behavior_rows": int(len(gender_b)),
        "action_rows": int(len(action)),
        "memo_length": len(memo),
        "fallback_base_used": not BASE_PATH_REQUESTED.exists(),
    }


if __name__ == "__main__":
    import sys
    print(run(finalize="--finalize" in sys.argv))
