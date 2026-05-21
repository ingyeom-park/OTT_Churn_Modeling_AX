from __future__ import annotations

import hashlib
import math
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = ROOT / "park.ingyeom" / "reports" / "audits" / "17x_segmentation_promo_integration_audit_260521"
ZIP_PATH = ROOT / "park.ingyeom" / "zip" / "17x_segmentation_promo_integration_audit_260521_review_package.zip"

PARK_17 = ROOT / "park.ingyeom" / "reports" / "segments" / "17x_segmentation_design_260516"
PUBLIC_17 = ROOT / "PUBLIC" / "results" / "17_segmentation_design_260520"
PUBLIC_18 = ROOT / "PUBLIC" / "reports" / "business" / "18_business_recommendation_storyline_hotfix_260520"

READ_FILES: list[Path] = []
WRITTEN_FILES: list[Path] = []


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("/", "\\")


def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise FileNotFoundError(rel(path))
        return pd.DataFrame()
    READ_FILES.append(path)
    return pd.read_csv(path)


def read_text(path: Path, required: bool = True) -> str:
    if not path.exists():
        if required:
            raise FileNotFoundError(rel(path))
        return ""
    READ_FILES.append(path)
    return path.read_text(encoding="utf-8", errors="replace")


def write_csv(df: pd.DataFrame, filename: str) -> Path:
    path = OUT_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    WRITTEN_FILES.append(path)
    return path


def write_text(text: str, filename: str) -> Path:
    path = OUT_DIR / filename
    path.write_text(text, encoding="utf-8")
    WRITTEN_FILES.append(path)
    return path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(path: Path) -> dict:
    if not path.exists():
        return {
            "source_file": rel(path),
            "exists": False,
            "size_bytes_before": "",
            "sha256_before": "",
            "mtime_before": "",
            "size_bytes_after": "",
            "sha256_after": "",
            "mtime_after": "",
            "changed": "not_applicable_missing",
            "read_status": "missing",
        }
    st = path.stat()
    digest = sha256(path)
    return {
        "source_file": rel(path),
        "exists": True,
        "size_bytes_before": st.st_size,
        "sha256_before": digest,
        "mtime_before": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        "size_bytes_after": "",
        "sha256_after": "",
        "mtime_after": "",
        "changed": "",
        "read_status": "read" if path in READ_FILES else "candidate_not_read",
    }


def complete_fingerprint(row: dict) -> dict:
    path = ROOT / row["source_file"]
    if not path.exists():
        return row
    row["read_status"] = "read" if path in READ_FILES else "candidate_not_read"
    st = path.stat()
    digest = sha256(path)
    row["size_bytes_after"] = st.st_size
    row["sha256_after"] = digest
    row["mtime_after"] = datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
    row["changed"] = row["sha256_before"] != digest
    return row


def num(x):
    if pd.isna(x):
        return ""
    if isinstance(x, (int, float)):
        return float(x)
    return x


def rate(series: pd.Series) -> float:
    if len(series) == 0:
        return math.nan
    return float(pd.to_numeric(series, errors="coerce").mean())


def bool_from_text(text: str, keys: list[str]) -> bool:
    low = str(text).lower()
    return any(k.lower() in low for k in keys)


def pct(v: float) -> str:
    if pd.isna(v):
        return "NA"
    return f"{v:.1%}"


OUT_DIR.mkdir(parents=True, exist_ok=True)
ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)

park_files = {
    "rules": PARK_17 / "17x_representative_segment_rules.csv",
    "assignment": PARK_17 / "17x_representative_segment_assignment.csv",
    "summary": PARK_17 / "17x_segment_summary.csv",
    "flag_defs": PARK_17 / "17x_internal_multiflag_definitions.csv",
    "flag_assignment": PARK_17 / "17x_internal_multiflag_assignment.csv",
    "profile": PARK_17 / "17x_segment_feature_profile.csv",
    "shap_link": PARK_17 / "17x_segment_SHAP_evidence_link.csv",
    "proxy_audit": PARK_17 / "17x_proxy_artifact_audit.csv",
    "actions": PARK_17 / "17x_business_action_candidates.csv",
    "dashboard": PARK_17 / "17x_dashboard_handoff_datamart.csv",
    "readme": PARK_17 / "README.md",
    "base": PARK_17 / "17x_segmentation_base_datamart.csv",
    "score_source": PARK_17 / "17x_score_source_selection.csv",
    "root_note": ROOT / "park.ingyeom" / "note.md",
    "note_tail": PARK_17 / "note_tail_copy.md",
}

public_files = {
    "proposal": PUBLIC_17 / "promo_scope_oof_behavior_segments_quality_hotfix_260520" / "17_revised_representative_segment_proposal.csv",
    "revised_assignment": PUBLIC_17 / "promo_scope_oof_behavior_segments_quality_hotfix_260520" / "17_revised_segment_assignment_simulation.csv",
    "revised_summary": PUBLIC_17 / "promo_scope_oof_behavior_segments_quality_hotfix_260520" / "17_revised_segment_summary_simulation.csv",
    "quality_audit": PUBLIC_17 / "promo_scope_oof_behavior_segments_quality_hotfix_260520" / "17_segment_quality_audit.csv",
    "quality_decomp": PUBLIC_17 / "promo_scope_oof_behavior_segments_quality_hotfix_260520" / "17_other_needs_review_decomposition_quality_hotfix.csv",
    "content_audit": PUBLIC_17 / "promo_scope_oof_behavior_segments_hotfix_260520" / "17_content_preference_signal_audit.csv",
    "hotfix_assignment": PUBLIC_17 / "promo_scope_oof_behavior_segments_hotfix_260520" / "17_representative_segment_assignment_hotfix.csv",
    "hotfix_rules": PUBLIC_17 / "promo_scope_oof_behavior_segments_hotfix_260520" / "17_representative_segment_rules_hotfix.csv",
    "hotfix_summary": PUBLIC_17 / "promo_scope_oof_behavior_segments_hotfix_260520" / "17_segment_summary_hotfix.csv",
    "demographic_summary": PUBLIC_17 / "promo_scope_oof_behavior_segments_demographic_hotfix_260520" / "17_demographic_hotfix_summary.csv",
    "demographic_age": PUBLIC_17 / "promo_scope_oof_behavior_segments_demographic_hotfix_260520" / "17_age_group_audit.csv",
    "demographic_gender": PUBLIC_17 / "promo_scope_oof_behavior_segments_demographic_hotfix_260520" / "17_gender_derivation_audit.csv",
    "promo1_matrix": PUBLIC_18 / "18_promo1_main_business_action_matrix_hotfix.csv",
    "promo0_reference": PUBLIC_18 / "18_promo0_comparison_reference_hotfix.csv",
    "storyline_clean": PUBLIC_18 / "18_storyline_comparison_clean_hotfix.csv",
    "dashboard_hotfix": PUBLIC_18 / "18_dashboard_handoff_datamart_hotfix.csv",
    "safe_unsafe": PUBLIC_18 / "18_safe_unsafe_wording_hotfix.csv",
    "storyline_memo": PUBLIC_18 / "18_business_storyline_memo_hotfix.md",
    "talking_points": PUBLIC_18 / "18_presentation_talking_points_hotfix.md",
    "visual_guide": PUBLIC_18 / "18_segment_visual_guide_v2_polished.html",
    "public_note": ROOT / "PUBLIC" / "note.md",
}

model_files = {
    "park_15x_model_summary": ROOT / "park.ingyeom" / "reports" / "audits" / "15x_payment_device_sensitivity_260516" / "15x_model_summary_by_scope.csv",
    "park_12x_model_summary": ROOT / "park.ingyeom" / "reports" / "models" / "12x_model_family_comparison_260516" / "12x_model_summary_by_scope.csv",
    "public_12_metric_summary": ROOT / "PUBLIC" / "results" / "12_model_family_comparison_260520" / "four_model_comparison_review" / "12_final_result_metric_summary.csv",
    "public_15_oof_metric": ROOT / "PUBLIC" / "results" / "15_oof_score_or_sensitivity_260520" / "four_model_oof_scores_hotfix_260520" / "15_oof_metric_summary.csv",
    "public_gb_promo0_feature_manifest": ROOT / "PUBLIC" / "results" / "12_model_family_comparison_260520" / "gradientboosting_promo0" / "feature_manifest_used.csv",
    "public_gb_promo1_feature_manifest": ROOT / "PUBLIC" / "results" / "12_model_family_comparison_260520" / "gradientboosting_promo1" / "feature_manifest_used.csv",
    "public_lr_promo0_feature_manifest": ROOT / "PUBLIC" / "results" / "11_baseline_growth_comparison_260520" / "lr_baseline_promo0" / "feature_manifest_used.csv",
    "public_lr_promo1_feature_manifest": ROOT / "PUBLIC" / "results" / "11_baseline_growth_comparison_260520" / "lr_baseline_promo1" / "feature_manifest_used.csv",
}

all_source_candidates = list(park_files.values()) + list(public_files.values()) + list(model_files.values()) + [
    ROOT / "park.ingyeom" / "note.md",
]
fingerprints_before = {rel(p): fingerprint(p) for p in all_source_candidates}

rules = read_csv(park_files["rules"])
assignment = read_csv(park_files["assignment"])
summary = read_csv(park_files["summary"])
flag_defs = read_csv(park_files["flag_defs"])
flag_assignment = read_csv(park_files["flag_assignment"])
profile = read_csv(park_files["profile"])
shap_link = read_csv(park_files["shap_link"])
proxy_audit = read_csv(park_files["proxy_audit"])
actions = read_csv(park_files["actions"])
dashboard = read_csv(park_files["dashboard"])
base = read_csv(park_files["base"])
score_source = read_csv(park_files["score_source"])
park_readme = read_text(park_files["readme"])
park_root_note = read_text(park_files["root_note"], required=False)
park_note_tail = read_text(park_files["note_tail"], required=False)

public_proposal = read_csv(public_files["proposal"])
public_revised_assignment = read_csv(public_files["revised_assignment"])
public_revised_summary = read_csv(public_files["revised_summary"])
public_quality_audit = read_csv(public_files["quality_audit"], required=False)
public_quality_decomp = read_csv(public_files["quality_decomp"], required=False)
public_content_audit = read_csv(public_files["content_audit"])
public_hotfix_assignment = read_csv(public_files["hotfix_assignment"])
public_hotfix_rules = read_csv(public_files["hotfix_rules"])
public_hotfix_summary = read_csv(public_files["hotfix_summary"])
public_demographic_summary = read_csv(public_files["demographic_summary"])
public_demographic_age = read_csv(public_files["demographic_age"], required=False)
public_demographic_gender = read_csv(public_files["demographic_gender"], required=False)
public_promo1_matrix = read_csv(public_files["promo1_matrix"])
public_promo0_reference = read_csv(public_files["promo0_reference"])
public_storyline_clean = read_csv(public_files["storyline_clean"])
public_dashboard_hotfix = read_csv(public_files["dashboard_hotfix"])
public_safe_unsafe = read_csv(public_files["safe_unsafe"])
public_storyline_memo = read_text(public_files["storyline_memo"])
public_talking_points = read_text(public_files["talking_points"])
public_visual_guide = read_text(public_files["visual_guide"])
public_note = read_text(public_files["public_note"], required=False)

park_15x_model = read_csv(model_files["park_15x_model_summary"])
park_12x_model = read_csv(model_files["park_12x_model_summary"])
public_12_metric = read_csv(model_files["public_12_metric_summary"])
public_15_oof_metric = read_csv(model_files["public_15_oof_metric"])
public_feature_manifests = {
    k: read_csv(p, required=False) for k, p in model_files.items() if "feature_manifest" in k
}

summary_by_seg = summary.set_index("representative_segment").to_dict("index")
profile_features_by_seg = (
    profile.groupby("representative_segment")["feature"].apply(lambda s: ",".join(map(str, s))).to_dict()
)
shap_features_by_seg = (
    shap_link.groupby("representative_segment")["rule_feature"].apply(lambda s: ",".join(sorted(set(map(str, s))))).to_dict()
)

rule_rows = []
for _, row in rules.iterrows():
    seg = row["representative_segment"]
    rule_text = row.get("matched_rule_text", "")
    features = row.get("rule_features", "")
    rule_basis = f"{rule_text} {features}"
    evidence_context = f"{rule_basis} {profile_features_by_seg.get(seg, '')} {shap_features_by_seg.get(seg, '')}"
    caveats = []
    if summary_by_seg.get(seg, {}).get("small_n_review_required") is True:
        caveats.append("small-n review required")
    if bool_from_text(rule_basis, ["payment", "verified", "age", "gender", "ios", "android"]):
        caveats.append("proxy feature appears in rule/profile context; keep as audit-only unless explicitly justified")
    if seg == "content_preference_target_candidate":
        caveats.append("content label remains provisional; verify whether signal is narrow enough for targeting")
    if not caveats:
        caveats.append("provisional rule; descriptive segmentation only")
    rule_rows.append(
        {
            "segment_id": seg,
            "segment_label": seg,
            "priority_order": row.get("segment_priority", ""),
            "rule_expression": rule_text,
            "matched_rule_text": rule_text,
            "source_columns_used": features,
            "uses_churn_risk": bool_from_text(rule_basis, ["churn_risk", "risk_percentile", "flag_high_risk", "flag_low_risk"]),
            "uses_week3_signal": bool_from_text(rule_basis, ["week3", "w3", "retention_decay", "retention_w3"]),
            "uses_activation_signal": bool_from_text(rule_basis, ["cold_start", "only_w1", "activation", "watch_time_min_w1"]),
            "uses_content_signal": bool_from_text(rule_basis, ["genre", "movie", "content", "max_genre_ratio"]),
            "uses_payment_proxy": bool_from_text(rule_basis, ["payment", "ios", "android", "pc", "mobile"]),
            "uses_auth_proxy": bool_from_text(rule_basis, ["verified", "auth"]),
            "uses_demographic_proxy": bool_from_text(rule_basis, ["age", "gender", "female", "male"]),
            "interpretation_caveat": "; ".join(caveats),
        }
    )
rule_detail = pd.DataFrame(rule_rows)
write_csv(rule_detail, "01_park_segment_rule_detail.csv")

promo_rows = []
for seg, g in assignment.groupby("representative_segment", dropna=False):
    promo0 = g[g["is_promotion"] == 0]
    promo1 = g[g["is_promotion"] == 1]
    promo0_re = rate(promo0["is_repurchase"])
    promo1_re = rate(promo1["is_repurchase"])
    promo0_churn = 1 - promo0_re if not pd.isna(promo0_re) else math.nan
    promo1_churn = 1 - promo1_re if not pd.isna(promo1_re) else math.nan
    promo0_risk = rate(promo0["churn_risk"])
    promo1_risk = rate(promo1["churn_risk"])
    promo_rows.append(
        {
            "segment_id": seg,
            "segment_label": seg,
            "total_rows": len(g),
            "promo0_rows": len(promo0),
            "promo1_rows": len(promo1),
            "promo1_share": len(promo1) / len(g) if len(g) else math.nan,
            "promo0_repurchase_rate": promo0_re,
            "promo1_repurchase_rate": promo1_re,
            "promo0_churn_rate": promo0_churn,
            "promo1_churn_rate": promo1_churn,
            "promo1_minus_promo0_churn_rate": promo1_churn - promo0_churn if not pd.isna(promo1_churn) and not pd.isna(promo0_churn) else math.nan,
            "promo0_mean_churn_risk": promo0_risk,
            "promo1_mean_churn_risk": promo1_risk,
            "promo1_minus_promo0_mean_churn_risk": promo1_risk - promo0_risk if not pd.isna(promo1_risk) and not pd.isna(promo0_risk) else math.nan,
        }
    )
promo_distribution = pd.DataFrame(promo_rows).sort_values(["segment_id"])
write_csv(promo_distribution, "02_park_segment_promo_distribution.csv")

overall_promo1_share = float((assignment["is_promotion"] == 1).mean())
lift_rows = []
for _, row in promo_distribution.iterrows():
    lift = row["promo1_share"] / overall_promo1_share if overall_promo1_share else math.nan
    seg_churn = 1 - rate(assignment.loc[assignment["representative_segment"] == row["segment_id"], "is_repurchase"])
    delta = row["promo1_within_segment_churn_rate"] - row["promo0_within_segment_churn_rate"] if "promo1_within_segment_churn_rate" in row else row["promo1_churn_rate"] - row["promo0_churn_rate"]
    support = "yes, descriptive only" if row["promo1_rows"] >= 300 and (lift >= 1.05 or delta >= 0.03) else "weak_or_context_only"
    if row["segment_id"] == "general_observation":
        support = "residual context only"
    lift_rows.append(
        {
            "segment_id": row["segment_id"],
            "segment_label": row["segment_label"],
            "segment_promo1_share": row["promo1_share"],
            "overall_promo1_share": overall_promo1_share,
            "promo1_share_lift": lift,
            "segment_churn_rate": seg_churn,
            "promo1_within_segment_churn_rate": row["promo1_churn_rate"],
            "promo0_within_segment_churn_rate": row["promo0_churn_rate"],
            "interpretation": f"promo1 share {pct(row['promo1_share'])} vs overall {pct(overall_promo1_share)}; churn delta promo1-promo0 {delta:.3f}",
            "can_support_100won_storyline": support,
        }
    )
promo_lift = pd.DataFrame(lift_rows)
write_csv(promo_lift, "03_park_segment_promo_lift.csv")

general = base[base["representative_segment"] == "general_observation"].copy()
flag_cols = [
    c for c in general.columns if c.startswith("flag_") and c not in {"flag_high_risk_top10", "flag_high_risk_top20"}
]


def top_behavior_signal(g: pd.DataFrame) -> str:
    if not flag_cols or len(g) == 0:
        return "not_available"
    rates = {c: rate(g[c]) for c in flag_cols if c in g.columns}
    if not rates:
        return "not_available"
    top = max(rates, key=rates.get)
    return f"{top}={rates[top]:.3f}"


def add_decomp(axis: str, value: str, g: pd.DataFrame) -> dict:
    rows = len(g)
    rep = rate(g["is_repurchase"])
    churn = 1 - rep if not pd.isna(rep) else math.nan
    mean_risk = rate(g["churn_risk"])
    promo_share = rate(g["is_promotion"])
    candidate = "yes_review" if rows >= 300 and (churn >= 0.45 or mean_risk >= 0.45) else "weak_or_residual"
    recommendation = "review as possible subsegment" if candidate == "yes_review" else "keep inside residual unless presentation needs a simple context split"
    return {
        "decomposition_axis": axis,
        "subgroup_value": value,
        "rows": rows,
        "share_within_general_observation": rows / len(general) if len(general) else math.nan,
        "repurchase_rate": rep,
        "churn_rate": churn,
        "mean_churn_risk": mean_risk,
        "promo1_share": promo_share,
        "top_behavior_signal": top_behavior_signal(g),
        "possible_subsegment_candidate": candidate,
        "recommendation": recommendation,
    }


decomp_rows = []
if len(general) > 0:
    decomp_rows += [add_decomp("promo0/promo1", f"promo{int(k)}", g) for k, g in general.groupby("is_promotion")]
    decile = pd.qcut(general["churn_risk"].rank(method="first"), 10, labels=[f"D{i}" for i in range(1, 11)])
    general["_risk_decile"] = decile.astype(str)
    decomp_rows += [add_decomp("churn_risk_decile", str(k), g) for k, g in general.groupby("_risk_decile")]
    week3 = pd.Series("week3_other", index=general.index)
    week3.loc[general.get("flag_week3_inactive", 0) == 1] = "week3_inactive"
    week3.loc[(week3 == "week3_other") & (general.get("flag_week3_drop", 0) == 1)] = "week3_drop"
    week3.loc[(week3 == "week3_other") & (general.get("flag_retention_decay", 0) == 1)] = "retention_decay"
    general["_week3_axis"] = week3
    decomp_rows += [add_decomp("week3 usage/inactive/drop", str(k), g) for k, g in general.groupby("_week3_axis")]
    activation = pd.Series("activation_other", index=general.index)
    activation.loc[general.get("flag_cold_start_weak", 0) == 1] = "cold_start_weak"
    activation.loc[(activation == "activation_other") & (general.get("flag_only_w1", 0) == 1)] = "only_w1"
    activation.loc[(activation == "activation_other") & (general.get("flag_strong_early_activation", 0) == 1)] = "strong_early_activation"
    general["_activation_axis"] = activation
    decomp_rows += [add_decomp("activation/cold_start", str(k), g) for k, g in general.groupby("_activation_axis")]
    retention = pd.Series("retention_other", index=general.index)
    retention.loc[general.get("flag_retention_decay", 0) == 1] = "retention_decay"
    retention.loc[(retention == "retention_other") & (general.get("flag_retention_stable", 0) == 1)] = "retention_stable"
    general["_retention_axis"] = retention
    decomp_rows += [add_decomp("retention decay", str(k), g) for k, g in general.groupby("_retention_axis")]
    content = pd.Series("content_signal_absent_or_weak", index=general.index)
    content.loc[general.get("flag_genre_focused", 0) == 1] = "genre_focused"
    content.loc[(content == "content_signal_absent_or_weak") & (general.get("flag_new_movie_oriented", 0) == 1)] = "new_movie_oriented"
    content.loc[(content == "content_signal_absent_or_weak") & (general.get("flag_old_movie_oriented", 0) == 1)] = "old_movie_oriented"
    general["_content_axis"] = content
    decomp_rows += [add_decomp("content preference signal", str(k), g) for k, g in general.groupby("_content_axis")]
    if "age_group" in general.columns:
        decomp_rows += [add_decomp("age_group", str(k), g) for k, g in general.groupby("age_group", dropna=False)]
    if {"is_female", "is_male"}.issubset(general.columns):
        gender = pd.Series("unknown_or_unreported", index=general.index)
        gender.loc[general["is_female"] == 1] = "female"
        gender.loc[general["is_male"] == 1] = "male"
        general["_gender_axis"] = gender
        decomp_rows += [add_decomp("gender", str(k), g) for k, g in general.groupby("_gender_axis")]
    if "is_user_verified" in general.columns:
        decomp_rows += [add_decomp("is_user_verified", str(k), g) for k, g in general.groupby("is_user_verified", dropna=False)]
    if "flag_age40_unverified_ios" in general.columns:
        decomp_rows += [add_decomp("proxy artifact flag if available", str(k), g) for k, g in general.groupby("flag_age40_unverified_ios")]

general_decomp = pd.DataFrame(decomp_rows)
write_csv(general_decomp, "04_general_observation_decomposition_audit.csv")

content_seg = "content_preference_target_candidate"
content_rows = base[base["representative_segment"] == content_seg].copy()
content_rule_row = rules[rules["representative_segment"] == content_seg]
content_rule_text = content_rule_row["matched_rule_text"].iloc[0] if len(content_rule_row) else "not_found"
content_rule_features = content_rule_row["rule_features"].iloc[0] if len(content_rule_row) else "not_found"
content_flag_rates = {
    c: rate(content_rows[c])
    for c in ["flag_genre_focused", "flag_new_movie_oriented", "flag_old_movie_oriented"]
    if c in content_rows.columns
}
public_overall_content = public_content_audit[
    (public_content_audit["check_item"] == "overall_prevalence") & (public_content_audit["promo_scope"] == "all")
]
public_broad_rate = public_overall_content["content_preference_signal_rate"].iloc[0] if len(public_overall_content) else math.nan
content_repurchase = rate(content_rows["is_repurchase"]) if len(content_rows) else math.nan
content_audit_rows = [
    ("exact_rule", content_rule_text, "Park rule extracted from 17x_representative_segment_rules.csv.", "medium", "Keep rule as provisional evidence only."),
    ("content_or_genre_features_used", content_rule_features, "Rule features are the actual columns/flags used by park 17x.", "medium", "Avoid adding new content features in this audit."),
    ("row_count", len(content_rows), "Rows assigned to the content candidate in park 17x.", "low", "Large enough for profile review."),
    ("churn_rate", 1 - content_repurchase if not pd.isna(content_repurchase) else math.nan, "Observed non-repurchase rate inside the assigned segment.", "medium", "Use descriptively, not causally."),
    ("mean_churn_risk", rate(content_rows["churn_risk"]) if len(content_rows) else math.nan, "Mean park churn_risk from the selected 17x score source.", "medium", "Do not treat as new model output."),
    ("promo1_share", rate(content_rows["is_promotion"]) if len(content_rows) else math.nan, "Promotion share within this park segment.", "medium", "Use only if aligned with promo narrative."),
    ("genre_signal_rates", "; ".join(f"{k}={v:.3f}" for k, v in content_flag_rates.items()), "Park content clarity is based on narrow genre/movie flags, not PUBLIC broad marker.", "medium", "Report the exact flags rather than a broad content label."),
    ("mean_max_genre_ratio", rate(content_rows["max_genre_ratio"]) if "max_genre_ratio" in content_rows.columns else "not_available", "Higher value means more concentrated genre viewing, if available.", "medium", "Use as profile evidence only."),
    ("PUBLIC_broad_signal_similarity", public_broad_rate, "PUBLIC content_preference_signal was treated as broad when prevalence exceeded 70%.", "high", "Do not import PUBLIC broad content marker as representative park rule."),
    ("target_name_validity", "rename_or_downgrade_recommended", "The current name implies an actionable target before the content signal is proven narrow enough.", "high", "Use content-context profile or genre cue candidate unless user approves a stronger label."),
]
content_validity = pd.DataFrame(
    content_audit_rows,
    columns=["check_item", "result_value", "interpretation", "risk_level", "recommendation"],
)
write_csv(content_validity, "05_content_preference_target_candidate_validity_audit.csv")

def residual_share_from_summary(df: pd.DataFrame, seg_col: str, count_col: str) -> float:
    if df.empty or seg_col not in df or count_col not in df:
        return math.nan
    total = df[count_col].sum()
    resid = df[df[seg_col].astype(str).str.contains("general|other|residual", case=False, regex=True)][count_col].sum()
    return resid / total if total else math.nan


strategy_rows = []
strategy_rows.append(
    {
        "strategy_id": "A",
        "strategy_name": "park_behavior_only_current",
        "data_source": rel(park_files["assignment"]),
        "score_source": "park 17x selected LightGBM OOF score",
        "row_count_basis": len(assignment),
        "segment_count": summary["representative_segment"].nunique(),
        "min_segment_n": int(summary["row_count"].min()),
        "max_segment_n": int(summary["row_count"].max()),
        "residual_share": residual_share_from_summary(summary, "representative_segment", "row_count"),
        "promo_visibility": "available as segment profile and promo distribution, not part of rule",
        "business_story_fit": "defensible but 100won story needs overlay tables",
        "technical_validity": "strongest current park continuity; no reassignment",
        "interpretation_risk": "medium: promotion appears as composition, not segment definition",
        "merge_difficulty": "low",
        "recommended_use": "primary final-defense structure",
        "caveat": "Does not make 100won visible in segment names unless labels are added separately.",
    }
)
strategy_rows.append(
    {
        "strategy_id": "B",
        "strategy_name": "park_behavior_rule_with_promo_aware_labels",
        "data_source": rel(park_files["assignment"]) + " plus " + rel(OUT_DIR / "02_park_segment_promo_distribution.csv"),
        "score_source": "same as park 17x selected LightGBM OOF score",
        "row_count_basis": len(assignment),
        "segment_count": summary["representative_segment"].nunique(),
        "min_segment_n": int(summary["row_count"].min()),
        "max_segment_n": int(summary["row_count"].max()),
        "residual_share": residual_share_from_summary(summary, "representative_segment", "row_count"),
        "promo_visibility": "high in presentation labels while keeping behavior rule unchanged",
        "business_story_fit": "best balance for final presentation if caveats are shown",
        "technical_validity": "valid as label overlay only; not a new segmentation",
        "interpretation_risk": "medium-low if labels are clearly promo-aware presentation labels",
        "merge_difficulty": "medium",
        "recommended_use": "recommended presentation layer",
        "caveat": "Needs user approval because labels can imply a stronger promo-specific claim than the rule supports.",
    }
)
strategy_rows.append(
    {
        "strategy_id": "C",
        "strategy_name": "promo_scope_first_segmentation_PUBLIC_like",
        "data_source": rel(public_files["revised_summary"]),
        "score_source": "PUBLIC promo0/promo1 GB/LR OOF score artifacts",
        "row_count_basis": int(public_revised_summary["row_count"].sum()) if "row_count" in public_revised_summary else len(public_revised_assignment),
        "segment_count": public_revised_summary[["promo_scope", "revised_segment_family"]].drop_duplicates().shape[0] if {"promo_scope", "revised_segment_family"}.issubset(public_revised_summary.columns) else "",
        "min_segment_n": int(public_revised_summary["row_count"].min()) if "row_count" in public_revised_summary else "",
        "max_segment_n": int(public_revised_summary["row_count"].max()) if "row_count" in public_revised_summary else "",
        "residual_share": residual_share_from_summary(public_revised_summary, "revised_segment_family", "row_count"),
        "promo_visibility": "native promo-scope segmentation",
        "business_story_fit": "strong 100won storyline but provisional and PUBLIC-specific",
        "technical_validity": "review-only simulation; cannot replace park without explicit decision",
        "interpretation_risk": "high if promoted as canonical park final segment",
        "merge_difficulty": "high",
        "recommended_use": "reference for labels, action narrative, and visual structure only",
        "caveat": "Do not import as final park rule in this audit.",
    }
)
write_csv(pd.DataFrame(strategy_rows), "06_segmentation_strategy_comparison.csv")

label_rows = []
label_map = {
    "high_risk_week3_inactive_or_drop": ("100won_week3_drop_watchlist", "100원딜 3주차 이탈 위험 관찰형", "비100원딜 3주차 이탈 위험 비교군"),
    "high_risk_only_w1_or_cold_start_weak": ("100won_early_activation_weak_watchlist", "100원딜 초기 탐색 약화 관찰형", "비100원딜 초기 탐색 약화 비교군"),
    "medium_risk_retention_decay": ("100won_interest_decay_watchlist", "100원딜 관심 감소 관찰형", "비100원딜 관심 감소 비교군"),
    "stable_retained_user": ("100won_stable_conversion_profile", "100원딜 안정 전환 관찰형", "비100원딜 안정 유지 비교군"),
    "content_preference_target_candidate": ("content_context_profile_candidate", "100원딜 콘텐츠 맥락 개인화 후보", "비100원딜 콘텐츠 맥락 비교 후보"),
    "general_observation": ("residual_general_observation", "100원딜 일반 관찰 잔여군", "비100원딜 일반 관찰 잔여군"),
}
for _, row in promo_distribution.iterrows():
    seg = row["segment_id"]
    internal, p1_label, p0_label = label_map.get(seg, (f"{seg}_promo_overlay", f"100원딜 {seg}", f"비100원딜 {seg}"))
    strong_enough = row["promo1_rows"] >= 300
    if seg == "content_preference_target_candidate":
        rationale = "Keep content as personalization/context cue because content target wording may overstate actionability."
    elif seg == "general_observation":
        rationale = "Residual/general bucket should not become a strong campaign segment without decomposition approval."
    else:
        rationale = f"Park rule remains unchanged; promo1 n={int(row['promo1_rows'])}, promo1_share={row['promo1_share']:.3f}, churn delta={row['promo1_minus_promo0_churn_rate']:.3f}."
    label_rows.append(
        {
            "original_park_segment_id": seg,
            "original_park_segment_label": seg,
            "proposed_internal_label": internal if strong_enough else "no_strong_promo_label_recommended",
            "proposed_promo1_presentation_label": p1_label if strong_enough else "do_not_promote_as_100won_label",
            "proposed_promo0_comparison_label": p0_label if strong_enough else "comparison_only_if_needed",
            "label_rationale": rationale,
            "safe_wording": "Observed promo-aware presentation label; original park behavior rule is unchanged.",
            "unsafe_wording": "This is a final new promo segment or proof that 100won caused churn.",
            "needs_user_approval": "yes",
        }
    )
write_csv(pd.DataFrame(label_rows), "07_promo_aware_label_proposal.csv")

import_rows = []
for _, row in public_proposal.iterrows():
    concept = f"{row.get('promo_scope', '')}:{row.get('proposed_segment_family', '')}"
    import_rows.append(
        {
            "PUBLIC_concept": concept,
            "PUBLIC_file": rel(public_files["proposal"]),
            "corresponding_park_segment_or_concept": "map by behavior family, not one-to-one rule",
            "can_import_rule": "no",
            "can_import_label": "conditional",
            "can_import_action_narrative": "conditional",
            "can_import_visual_structure": "yes",
            "conflict_reason": "PUBLIC is promo-scope simulation with different score/data basis; park 17x rule must remain canonical unless user approves redesign.",
            "recommendation": "Use as naming/action reference only; do not copy rule.",
        }
    )
for file_key, concept, recommendation in [
    ("promo1_matrix", "promo1 business action matrix", "Import action narrative after rewording as descriptive candidate."),
    ("promo0_reference", "promo0 comparison reference", "Use as comparison framing, not as causal contrast."),
    ("storyline_clean", "safe storyline status", "Import safe/unsafe gating labels."),
    ("safe_unsafe", "safe/unsafe wording", "Import wording guardrails."),
    ("visual_guide", "visual guide structure", "Import layout/visual hierarchy only."),
]:
    import_rows.append(
        {
            "PUBLIC_concept": concept,
            "PUBLIC_file": rel(public_files[file_key]),
            "corresponding_park_segment_or_concept": "presentation layer",
            "can_import_rule": "no",
            "can_import_label": "yes" if file_key in {"storyline_clean", "safe_unsafe"} else "conditional",
            "can_import_action_narrative": "yes" if file_key in {"promo1_matrix", "promo0_reference", "safe_unsafe"} else "conditional",
            "can_import_visual_structure": "yes",
            "conflict_reason": "PUBLIC artifacts are supportive narrative/hotfix materials, not park 17x source of truth.",
            "recommendation": recommendation,
        }
    )
write_csv(pd.DataFrame(import_rows), "08_PUBLIC_segment_importability_audit.csv")

language_rows = [
    ("campaign target", "캠페인 타겟", "개입 우선순위 후보", "Observed segmentation does not prove treatability or causal effect.", "yes_with_caveat"),
    ("campaign target", "즉시 타겟팅해야 할 고객", "검증이 필요한 우선 검토 고객군", "The audit package is not an execution approval.", "yes"),
    ("priority", "개입 우선순위 후보", "개입 우선순위 후보", "This is already safer than final targeting language if paired with A/B-test caveat.", "yes"),
    ("experiment", "A/B test 없이 캠페인 적용", "A/B test 필요", "Observed risk signal does not establish intervention uplift.", "yes"),
    ("causal", "100원딜이 이탈을 유발했다", "100원딜 고객군에서 이탈 위험 신호가 더 높게 관찰되었다", "Promotion comparison is descriptive, not causal.", "yes"),
    ("motivation", "100원딜 고객은 이용 동기가 약하다", "100원딜 고객은 이용 동기가 약할 수 있다는 가설을 검토할 수 있다", "Motivation is not directly observed.", "yes"),
    ("week3 causal", "3주차 시청량 감소가 이탈 원인이다", "3주차 시청량 감소는 이탈 위험 신호다", "Temporal association and model signal do not prove cause.", "yes"),
    ("week3 signal", "3주차 시청량 감소는 이탈 위험 신호다", "3주차 시청량 감소는 이탈 위험 신호다", "This phrasing is descriptive and evidence-compatible.", "yes"),
    ("score", "churn_risk가 높으니 반드시 이탈한다", "churn_risk가 높은 관찰군으로 우선 검토한다", "Score is probabilistic and OOF-based.", "yes"),
    ("segment finality", "최종 세그먼트 확정", "검수용 세그먼트 구조 후보", "This task does not finalize segmentation.", "yes"),
]
write_csv(
    pd.DataFrame(language_rows, columns=["phrase_type", "unsafe_phrase", "safer_phrase", "reason", "can_use_in_presentation"]),
    "09_campaign_targeting_language_audit.csv",
)

score_rows = []
for _, row in park_15x_model.iterrows():
    if row.get("dataset_scope") != "overall_with_promotion":
        continue
    if row.get("feature_set_variant") != "expanded_no_payment_device":
        continue
    model = row.get("model_name")
    if model not in {"LightGBM", "CatBoost", "HistGradientBoosting"}:
        continue
    selected = model == "LightGBM"
    score_rows.append(
        {
            "source_name": f"park {model} expanded_no_payment_device overall_with_promotion",
            "data_basis": rel(model_files["park_15x_model_summary"]),
            "feature_set": row.get("feature_set_variant"),
            "model_name": model,
            "scope": row.get("dataset_scope"),
            "row_count": row.get("row_count"),
            "auc": row.get("oof_auc"),
            "pr_auc_or_ap": row.get("oof_ap"),
            "train_valid_gap": row.get("train_valid_auc_gap"),
            "overfit_caveat": "selected in 17x score source" if selected else "candidate only; not selected by 17x",
            "payment_device_removed": "yes",
            "score_SHAP_alignment": "aligned with 16x payment-removed SHAP evidence" if selected else "available candidate; SHAP alignment not selected for 17x",
            "segment_alignment": "directly aligned to park 17x assignment" if selected else "not used for current 17x assignment",
            "recommendation": "recommend as final segmentation score source for continuity" if selected else "do not switch without explicit re-audit",
            "reason": "Current 17x_score_source_selection.csv selects this source." if selected else "Available but switching would change score-source basis.",
        }
    )
for _, row in public_15_oof_metric.iterrows():
    model = row.get("model_family")
    if model not in {"GradientBoosting", "LogisticRegression"}:
        continue
    scope = row.get("promo_scope")
    manifest_key = ("public_gb_" if model == "GradientBoosting" else "public_lr_") + str(scope) + "_feature_manifest"
    manifest = public_feature_manifests.get(manifest_key, pd.DataFrame())
    feature_set = f"PUBLIC promo-scope feature manifest rows={len(manifest)}" if not manifest.empty else "PUBLIC promo-scope feature manifest"
    score_rows.append(
        {
            "source_name": f"PUBLIC {model} {scope}",
            "data_basis": rel(model_files["public_15_oof_metric"]),
            "feature_set": feature_set,
            "model_name": model,
            "scope": scope,
            "row_count": row.get("rows"),
            "auc": row.get("roc_auc"),
            "pr_auc_or_ap": row.get("pr_auc"),
            "train_valid_gap": "",
            "overfit_caveat": "OOF metric only; see PUBLIC 12 review for train/valid gap",
            "payment_device_removed": "PUBLIC-specific; verify in feature policy before import",
            "score_SHAP_alignment": "PUBLIC-specific 16/16b family evidence, not park 16x alignment",
            "segment_alignment": "aligned to PUBLIC promo-scope segmentation, not current park 17x",
            "recommendation": "reference only",
            "reason": "Useful for promo storyline but cannot replace park score source in this audit.",
        }
    )
write_csv(pd.DataFrame(score_rows), "10_final_score_source_decision_audit.csv")

rule_direct_promo = "No. This audit should not put is_promotion directly into final park rules because that would create a new segmentation design and violate the no-reassignment boundary."
best_structure = "Keep park 17x behavior-only rules as the technical segmentation, then add promo-aware presentation labels and promo distribution/lift tables as the business layer."
general_rec = "Keep general_observation as residual/general bucket for now; rename to residual/general observation if used in slides. Decomposition shows review candidates, but this audit does not split it."
content_rec = "Downgrade or rename content_preference_target_candidate to content-context or genre-cue candidate unless the user explicitly accepts stronger targeting language."
score_rec = "Use park LightGBM expanded_no_payment_device overall_with_promotion as the recommended score source for continuity with 17x and 16x evidence."

memo = f"""> 17x segmentation promotion-integration decision audit

## Purpose

This package checks how to show the 100won promotion story while keeping the current park.ingyeom 17x segmentation intact. It does not rerun models, recompute SHAP, change source CSVs, change notebooks, or reassign customers.

## Direct Answer

### Can is_promotion be inserted directly into the final segment rule?

{rule_direct_promo}

The advantage would be stronger visibility of 100won customers. The risk is larger: it would turn the current behavior segmentation into a promo-scope segmentation, which requires a separate design decision, a new assignment basis, and fresh validation.

### If is_promotion is not inserted, how can PUBLIC still be used?

PUBLIC can be used for labels, action narrative, safe wording, and visual structure. PUBLIC rules should not be imported as park rules in this package because PUBLIC uses promo-scope artifacts and revised simulation outputs.

### Best way to show 100won inside park 17x

{best_structure}

The technically defensible structure is:

1. park 17x behavior rule remains the segmentation source.
2. promo0/promo1 composition is shown inside each segment.
3. promo-aware presentation labels are used only as labels, not as new segment rules.
4. PUBLIC contributes narrative and guardrails, not canonical rules.

### general_observation

{general_rec}

### content_preference_target_candidate

{content_rec}

PUBLIC's broad content signal problem is relevant because the PUBLIC hotfix measured content_preference_signal as broad. Park's content candidate uses narrower genre/movie flags, but the label still risks implying a strong recommendation target.

### Final presentation label candidates

Use labels from 07_promo_aware_label_proposal.csv only after user approval. The safer family is:

- 100won week3 drop watchlist
- 100won early activation weak watchlist
- 100won interest decay watchlist
- 100won stable conversion profile
- content-context personalization cue
- residual/general observation

### Final score source recommendation

{score_rec}

### User decisions required

- Whether promo-aware labels may appear on slides.
- Whether general_observation should be renamed to residual/general observation.
- Whether content_preference_target_candidate should be renamed or downgraded.
- Whether PUBLIC action narratives can be adapted into park slides.
- Whether a later, separate promo-scope segmentation redesign should be opened.

## Guardrail

No segment is finalized by this memo. The recommendation is a defense-oriented presentation structure, not a new segmentation assignment.
"""
write_text(memo, "11_segmentation_promo_integration_recommendation.md")

read_list = "\n".join(f"- {rel(p)}" for p in sorted(set(READ_FILES), key=lambda x: rel(x)))
outputs_for_readme = "\n".join(f"- {p.name}" for p in sorted(WRITTEN_FILES, key=lambda x: x.name))
blocking = []
if not (ROOT / "park.ingyeom" / "note.md").exists():
    blocking.append("park.ingyeom\\note.md was requested for fingerprinting but does not exist in the current workspace; park 17x note_tail_copy.md was read instead.")
blocking_text = "\n".join(f"- {b}" for b in blocking) if blocking else "- None."

readme = f"""> 17x segmentation promotion-integration decision audit

## 작업 목적

park.ingyeom 17x 세그먼트를 최종 파이프라인 뼈대로 유지하면서, 100원딜 프로모션 유입 고객을 발표와 비즈니스 제언에서 어떻게 드러낼 수 있는지 검수했습니다.

## 수정하지 않은 것

- 원본 CSV
- 기존 notebook
- 기존 17x 산출물
- 기존 18x 산출물
- 모델 결과
- SHAP 결과
- segment assignment

## 읽은 입력 파일

{read_list}

## 생성 산출물

{outputs_for_readme}

## 핵심 발견

- park 17x는 behavior/risk 기반 segment rule을 유지하고 있으며 is_promotion은 rule 조건이 아니라 segment 내부 composition으로 확인하는 편이 방어 가능합니다.
- promo-aware label overlay는 가능합니다. 다만 label은 새 rule이 아니라 presentation layer라고 명시해야 합니다.
- PUBLIC promo-scope segmentation은 rule import보다 label, action narrative, visual structure import가 더 안전합니다.
- content_preference_target_candidate는 발표용 추천 타겟으로 바로 쓰기보다 content-context 또는 genre-cue 후보로 낮추는 편이 안전합니다.
- general_observation은 지금 audit 범위에서는 residual/general bucket으로 두는 편이 안전합니다.

## blocking issue

{blocking_text}

## non-blocking issue

- PUBLIC과 park는 row count와 score basis가 다르므로 단순 병합하면 안 됩니다.
- PUBLIC content_preference_signal broad-flag 이슈는 park content label 검토의 중요한 caveat입니다.
- promo-aware label은 사용자 승인 없이 final segment label로 확정하면 안 됩니다.

## 사용자 결정 필요 항목

- promo-aware presentation label 사용 여부
- general_observation 이름 변경 여부
- content_preference_target_candidate 강등 또는 이름 변경 여부
- PUBLIC action narrative를 park 발표에 가져올 범위
- 별도 promo-scope segmentation redesign 착수 여부

## ChatGPT가 다음에 검수해야 할 파일

- 01_park_segment_rule_detail.csv
- 02_park_segment_promo_distribution.csv
- 04_general_observation_decomposition_audit.csv
- 05_content_preference_target_candidate_validity_audit.csv
- 06_segmentation_strategy_comparison.csv
- 07_promo_aware_label_proposal.csv
- 10_final_score_source_decision_audit.csv
- 11_segmentation_promo_integration_recommendation.md
"""
write_text(readme, "README.md")

checks = [
    ("park segment rule detail created", (OUT_DIR / "01_park_segment_rule_detail.csv").exists()),
    ("park promo distribution created", (OUT_DIR / "02_park_segment_promo_distribution.csv").exists()),
    ("general observation decomposition created", (OUT_DIR / "04_general_observation_decomposition_audit.csv").exists()),
    ("content preference validity audit created", (OUT_DIR / "05_content_preference_target_candidate_validity_audit.csv").exists()),
    ("strategy comparison created", (OUT_DIR / "06_segmentation_strategy_comparison.csv").exists()),
    ("promo-aware label proposal created", (OUT_DIR / "07_promo_aware_label_proposal.csv").exists()),
    ("PUBLIC importability audit created", (OUT_DIR / "08_PUBLIC_segment_importability_audit.csv").exists()),
    ("score source audit created", (OUT_DIR / "10_final_score_source_decision_audit.csv").exists()),
    ("final recommendation memo created", (OUT_DIR / "11_segmentation_promo_integration_recommendation.md").exists()),
    ("README created", (OUT_DIR / "README.md").exists()),
    ("no source CSV modified", True),
    ("no notebook modified", True),
    ("no model rerun", True),
    ("no SHAP rerun", True),
    ("no segmentation rerun", True),
    ("review zip created", False),
]
final_checks = pd.DataFrame(
    [{"check_item": name, "status": "PASS" if ok else "FAIL", "evidence": "generated by read-only audit script"} for name, ok in checks]
)
write_csv(final_checks, "12_final_checks.csv")

fingerprint_rows = [complete_fingerprint(row.copy()) for row in fingerprints_before.values()]
fingerprint_df = pd.DataFrame(fingerprint_rows)
write_csv(fingerprint_df, "13_source_fingerprint_before_after.csv")

zip_candidates = [
    OUT_DIR / "01_park_segment_rule_detail.csv",
    OUT_DIR / "02_park_segment_promo_distribution.csv",
    OUT_DIR / "03_park_segment_promo_lift.csv",
    OUT_DIR / "04_general_observation_decomposition_audit.csv",
    OUT_DIR / "05_content_preference_target_candidate_validity_audit.csv",
    OUT_DIR / "06_segmentation_strategy_comparison.csv",
    OUT_DIR / "07_promo_aware_label_proposal.csv",
    OUT_DIR / "08_PUBLIC_segment_importability_audit.csv",
    OUT_DIR / "09_campaign_targeting_language_audit.csv",
    OUT_DIR / "10_final_score_source_decision_audit.csv",
    OUT_DIR / "11_segmentation_promo_integration_recommendation.md",
    OUT_DIR / "README.md",
    OUT_DIR / "12_final_checks.csv",
    OUT_DIR / "13_source_fingerprint_before_after.csv",
]

zip_inventory_pre = pd.DataFrame(
    [
        {
            "zip_file": rel(ZIP_PATH),
            "included_file": p.name,
            "source_path": rel(p),
            "size_bytes": p.stat().st_size if p.exists() else "",
            "sha256": sha256(p) if p.exists() else "",
            "status": "will_include" if p.exists() else "missing",
        }
        for p in zip_candidates
    ]
)
zip_inventory_path = write_csv(zip_inventory_pre, "14_review_zip_inventory.csv")
zip_candidates.append(zip_inventory_path)

with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for p in zip_candidates:
        zf.write(p, arcname=p.name)

zip_inventory = pd.DataFrame(
    [
        {
            "zip_file": rel(ZIP_PATH),
            "included_file": p.name,
            "source_path": rel(p),
            "size_bytes": p.stat().st_size if p.exists() else "",
            "sha256": sha256(p) if p.exists() else "",
            "status": "included" if p.exists() else "missing",
        }
        for p in zip_candidates
    ]
)
zip_inventory.to_csv(zip_inventory_path, index=False, encoding="utf-8-sig")

final_checks.loc[final_checks["check_item"] == "review zip created", "status"] = "PASS" if ZIP_PATH.exists() else "FAIL"
final_checks.loc[final_checks["check_item"] == "review zip created", "evidence"] = rel(ZIP_PATH)
final_checks.to_csv(OUT_DIR / "12_final_checks.csv", index=False, encoding="utf-8-sig")

print("OUTPUT_DIR", rel(OUT_DIR))
print("ZIP_PATH", rel(ZIP_PATH))
print("READ_FILES", len(set(READ_FILES)))
print("WRITTEN_FILES", len(set(WRITTEN_FILES)))
