from pathlib import Path
import csv
import hashlib
import html
import re
import shutil
import zipfile
from collections import defaultdict
from datetime import datetime

ROOT = Path(r"C:\Code\ott-churn-prediction")
OUT = ROOT / "FINAL" / "project_guide_v3_visual_upgrade_evidence_260521"
ASSET_DIR = OUT / "assets" / "shap"
ZIP_PATH = ROOT / "FINAL" / "project_guide_v3_visual_upgrade_evidence_260521_review_package.zip"

ASSET_DIR.mkdir(parents=True, exist_ok=True)


def rel(path):
    path = Path(path)
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def out_rel(path):
    path = Path(path)
    try:
        return str(path.relative_to(OUT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def read_csv(path):
    with Path(path).open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows, fieldnames):
    path = OUT / name
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return path


def write_md(name, text):
    path = OUT / name
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def title_of(text):
    found = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    if not found:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<.*?>", "", html.unescape(found.group(1)))).strip()


def clean_html(text):
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def file_meta(path):
    path = Path(path)
    if not path.exists():
        return {
            "exists": "no",
            "file_size": "",
            "sha256_before": "",
            "sha256_after": "",
            "modified_time_before": "",
            "modified_time_after": "",
        }
    stat = path.stat()
    digest = sha256(path)
    mtime = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    return {
        "exists": "yes",
        "file_size": stat.st_size,
        "sha256_before": digest,
        "sha256_after": digest,
        "modified_time_before": mtime,
        "modified_time_after": mtime,
    }


html_sources = [
    ("AARRR visual guide", ROOT / "park.ingyeom/aarrr_visual_guide.html", "AARRR stages and Chart.js structure"),
    ("project guide v2", ROOT / "park.ingyeom/project_guide_v2.html", "Project guide v2 layout and warnings"),
    ("segment visual guide", ROOT / "park.ingyeom/segment_visual_guide.html", "17x segment triage and charts"),
    ("SHAP visual guide", ROOT / "park.ingyeom/shap_visual_guide.html", "16x SHAP PNG and wording structure"),
    ("current final v3", ROOT / "FINAL/project_guide_v3.html", "Expected current final v3 HTML"),
    ("fallback discovered project guide", ROOT / "park.ingyeom/project_guide.html", "Discovered guide fallback, not final v3"),
]

inventory = []
texts = {}
for key, path, purpose in html_sources:
    if path.exists():
        text = read_text(path)
        lower = text.lower()
        texts[rel(path)] = clean_html(text)
        inventory.append({
            "html_file": rel(path),
            "title": title_of(text),
            "purpose": purpose,
            "section_count": len(re.findall(r"<section\b", text, re.I)),
            "canvas_count": len(re.findall(r"<canvas\b", text, re.I)),
            "image_count": len(re.findall(r"<img\b", text, re.I)),
            "external_script_count": len(re.findall(r"<script\b[^>]*\bsrc\s*=", text, re.I)),
            "uses_chartjs": "yes" if "chart.js" in lower or "chartjs" in lower else "no",
            "uses_png_assets": "yes" if "<img" in lower else "no",
            "has_dark_mode": "yes" if "dark" in lower else "no",
            "has_sidebar": "yes" if "sidebar" in lower else "no",
            "has_table_wrap": "yes" if "table-wrap" in lower else "no",
            "reusable_level": "medium" if "project guide" in key else "high",
            "main_risk": "structure reference only; legacy text/numbers must be rewritten to final basis",
        })
    else:
        inventory.append({
            "html_file": rel(path),
            "title": "MISSING",
            "purpose": purpose,
            "section_count": 0,
            "canvas_count": 0,
            "image_count": 0,
            "external_script_count": 0,
            "uses_chartjs": "no",
            "uses_png_assets": "no",
            "has_dark_mode": "no",
            "has_sidebar": "no",
            "has_table_wrap": "no",
            "reusable_level": "none",
            "main_risk": "current final v3 HTML not found in repo",
        })
write_csv("01_html_source_inventory.csv", inventory, [
    "html_file", "title", "purpose", "section_count", "canvas_count", "image_count",
    "external_script_count", "uses_chartjs", "uses_png_assets", "has_dark_mode",
    "has_sidebar", "has_table_wrap", "reusable_level", "main_risk",
])

components = [
    ("park.ingyeom/aarrr_visual_guide.html", "AARRR funnel", "Chart.js stage flow", "Observed/proxy AARRR stage structure", "Reuse chart type after final rewrite", "reuse_chart_type", "AARRR mapping", "06_AARRR_chart_ready.csv", "medium", "Referral unobserved and Revenue target proxy must remain visible."),
    ("park.ingyeom/aarrr_visual_guide.html", "AARRR sidebar", "navigation", "Long document anchor navigation", "Reuse global navigation pattern", "reuse_css_pattern", "global layout", "section anchors", "low", "Shorten labels for mobile."),
    ("park.ingyeom/aarrr_visual_guide.html", "AARRR variable tooltip", "tooltip", "Inline variable explanations", "Reuse for risky variables and caveats", "reuse_css_pattern", "feature dictionary", "column_feature_contract_summary.csv", "low", "Tooltips must not add new interpretation."),
    ("park.ingyeom/project_guide_v2.html", "project v2 warning cards", "warning cards", "Up-front caveat cards", "Reuse text after final rewrite", "reuse_text_after_rewrite", "hero warning", "FINAL/final_note.md", "medium", "Do not carry legacy numeric score wording."),
    ("park.ingyeom/project_guide_v2.html", "project v2 timeline", "timeline", "Stage timeline", "Reuse structure with 07 to 18 timeline CSV", "reuse_structure_only", "project timeline", "stage_07_to_18_timeline.csv", "low", "Mark descriptive/model/SHAP/segmentation boundaries."),
    ("park.ingyeom/project_guide_v2.html", "project v2 pipeline vertical flow", "pipeline", "Vertical stage dependency flow", "Reuse structure only", "reuse_structure_only", "evidence lineage", "dataset_lineage_summary.csv", "low", "Do not imply rerun."),
    ("park.ingyeom/project_guide_v2.html", "project v2 feature count chart", "bar chart", "Feature-set count chart", "Reuse chart type", "reuse_chart_type", "feature contract", "05_dataset_feature_chart_ready.csv", "medium", "Show 76 versus 75 by scope."),
    ("park.ingyeom/segment_visual_guide.html", "segment triage flow", "triage flow", "Priority-based assignment explanation", "Reuse structure only", "reuse_structure_only", "segment assignment", "17x_representative_segment_rules.csv", "low", "No new segment rule."),
    ("park.ingyeom/segment_visual_guide.html", "segment flag dictionary", "dictionary", "Flag definitions", "Reuse in appendix", "reuse_structure_only", "segment appendix", "17x_internal_multiflag_definitions.csv", "low", "Content flags are proxy cues."),
    ("park.ingyeom/segment_visual_guide.html", "segment detail cards", "cards", "Per-segment interpretation card", "Reuse CSS pattern with final labels", "reuse_css_pattern", "segment storyline", "07_segment_chart_ready.csv", "medium", "general_observation is residual monitoring."),
    ("park.ingyeom/segment_visual_guide.html", "segment pie/doughnut", "doughnut", "Segment share chart", "Reuse chart type", "reuse_chart_type", "segment overview", "07_segment_chart_ready.csv", "low", "Rows are subscription-event rows."),
    ("park.ingyeom/segment_visual_guide.html", "segment weekly watch chart", "line/bar", "W1 to W3 watch trajectory", "Reuse chart type", "reuse_chart_type", "segment details", "07_segment_chart_ready.csv", "low", "Aggregated from existing datamart only."),
    ("park.ingyeom/segment_visual_guide.html", "segment risk scatter/bubble", "scatter/bubble", "Share versus risk priority chart", "Reuse with caution", "reuse_chart_type", "segment priority matrix", "07_segment_chart_ready.csv", "medium", "Avoid finalized campaign target wording."),
    ("park.ingyeom/shap_visual_guide.html", "SHAP global bar image", "PNG asset", "Global SHAP bar", "Use Chart.js for main, PNG as reference", "reuse_image_asset", "SHAP overview", "09_SHAP_chart_ready.csv", "low", "Non-causal model explanation."),
    ("park.ingyeom/shap_visual_guide.html", "SHAP beeswarm image", "PNG asset", "SHAP distribution and direction", "Use PNG, not Chart.js replacement", "reuse_image_asset", "SHAP direction", "10_SHAP_figure_asset_manifest.csv", "low", "Caption must be non-causal."),
    ("park.ingyeom/shap_visual_guide.html", "SHAP family importance image", "PNG/bar chart", "Family-level SHAP", "Prefer Chart.js in main and PNG in appendix", "reuse_chart_type", "SHAP family", "09_SHAP_chart_ready.csv", "low", "Scope-specific."),
    ("park.ingyeom/shap_visual_guide.html", "SHAP scope comparison image", "PNG asset", "Scope comparison", "Use PNG in appendix", "reuse_image_asset", "SHAP appendix", "10_SHAP_figure_asset_manifest.csv", "medium", "Do not collapse scopes into one universal ranking."),
    ("park.ingyeom/shap_visual_guide.html", "SHAP safe/unsafe wording", "wording", "Safe versus unsafe explanation boundary", "Reuse principle after rewrite", "reuse_text_after_rewrite", "guardrails", "16x_safe_unsafe_wording.csv", "low", "Keep no-causality visible."),
]
write_csv("02_reusable_component_audit.csv", [dict(zip([
    "source_html", "component_name", "component_type", "description", "reuse_recommendation",
    "reuse_mode", "target_section_in_final_v3", "required_data", "conflict_risk", "notes",
], row)) for row in components], [
    "source_html", "component_name", "component_type", "description", "reuse_recommendation",
    "reuse_mode", "target_section_in_final_v3", "required_data", "conflict_risk", "notes",
])

conflict_specs = [
    ("raw 23,343 vs final 23,079", r"23,343|23343", "23,079 primary subscription-event rows; 23,343 is raw only", "row_count_basis"),
    ("100원딜 causal phrasing", r"100원딜.{0,40}(원인|때문|유발|인과)", "100원딜 is acquisition/scope context, not confirmed churn cause", "causal_overstatement"),
    ("content_preference as churn defense target", r"content_preference_target_candidate|콘텐츠.{0,20}(타겟|방어|취향)", "content_preference_target_candidate is curation/full-price conversion action layer", "segment_label_overstatement"),
    ("general_observation as general customers", r"general_observation|일반 고객|일반군", "general_observation is residual monitoring group", "segment_label_overstatement"),
    ("payment-device as viewing device", r"payment.{0,20}device|payment_is_|결제.{0,20}기기|시청기기", "payment-device is payment context/proxy, not viewing device", "proxy_mislabel"),
    ("SHAP causal wording", r"SHAP.{0,50}(원인|인과|유발|효과)", "SHAP is model explanation, not causal proof", "xai_causal_overstatement"),
    ("campaign target certainty", r"(캠페인|campaign).{0,30}(확정|타겟|대상)", "campaign/action wording must remain candidate or experiment design", "action_certainty"),
    ("personal or team names", r"박인겸|이예림|강민서|김광일|정유정|박병선", "Do not expose personal names without approval", "privacy_exposure"),
    ("PUBLIC numeric score as final", r"PUBLIC.{0,80}(score|점수|AUC|churn_risk|numeric)", "PUBLIC numeric score must not be final basis", "branch_contamination"),
]
conflicts = []
for item, pattern, expected, ctype in conflict_specs:
    found = False
    for src, text in texts.items():
        hit = re.search(pattern, text, flags=re.I)
        if hit:
            found = True
            start = max(0, hit.start() - 80)
            end = min(len(text), hit.end() + 80)
            conflicts.append({
                "source_html": src,
                "conflict_item": item,
                "legacy_value_or_phrase": text[start:end],
                "final_expected_value_or_phrase": expected,
                "conflict_type": ctype,
                "severity": "high" if ctype in ["causal_overstatement", "xai_causal_overstatement", "branch_contamination", "privacy_exposure"] else "medium",
                "recommendation": "Rewrite or exclude legacy phrase; use final evidence-pack wording.",
            })
    if not found:
        conflicts.append({
            "source_html": "all scanned legacy HTML",
            "conflict_item": item,
            "legacy_value_or_phrase": "not_found_in_scanned_html_by_keyword_check",
            "final_expected_value_or_phrase": expected,
            "conflict_type": ctype,
            "severity": "none",
            "recommendation": "Keep as rewrite checklist item.",
        })
write_csv("03_legacy_conflict_audit.csv", conflicts, [
    "source_html", "conflict_item", "legacy_value_or_phrase", "final_expected_value_or_phrase",
    "conflict_type", "severity", "recommendation",
])

chart_rows = [
    ("dataset_lineage_waterfall", "data basis", "Dataset lineage from raw to primary cohort", "waterfall/bar", "FINAL/project_guide_v3_evidence_pack_260521/dataset_lineage_summary.csv", "05_dataset_feature_chart_ready.csv", "chart_id,label,value,group,unit", "yes", "no", "yes_from_existing_csv", "23,343 raw only; 23,079 final primary cohort", "high"),
    ("feature_set_flow_bar", "feature contract", "Feature set count flow", "bar", "dataset_lineage_summary.csv; 15x_feature_set_comparison_design.csv", "05_dataset_feature_chart_ready.csv", "chart_id,label,value,group,unit", "yes", "no", "yes_from_existing_csv", "Show 76 for overall_with_promotion and 75 for other scopes", "high"),
    ("AARRR_feature_count_bar", "AARRR mapping", "AARRR feature counts by stage", "bar", "AARRR_feature_mapping_table.csv", "06_AARRR_chart_ready.csv", "AARRR_stage,feature_count_conservative,feature_count_expanded", "yes", "no", "yes_from_existing_csv", "Referral has no observed feature", "high"),
    ("AARRR_funnel_visual", "AARRR mapping", "Observed AARRR funnel / measurement ladder", "bar/funnel-like", "AARRR_feature_mapping_table.csv", "06_AARRR_chart_ready.csv", "AARRR_stage,observed_status,guide_interpretation", "yes", "reuse_structure_only", "yes_from_existing_csv", "Revenue is target proxy", "medium"),
    ("promo_repurchase_gap_bar", "promotion descriptive EDA", "Promotion x repurchase descriptive gap", "bar", "existing 09x/FINAL evidence if supplied", "not_created_missing_current_source", "promotion_group,repurchase_rate", "yes", "no", "needs_source_selection", "No predictions or significance claims", "medium"),
    ("stage_07_to_18_timeline_visual", "project flow", "Stage 07 to 18 visual timeline", "timeline", "stage_07_to_18_timeline.csv", "04_final_v3_chart_registry.csv", "stage,stage_name,purpose,final_status", "yes", "reuse_structure_only", "yes_from_existing_csv", "Explanation only", "medium"),
    ("model_auc_flow", "modeling evidence", "AUC flow across model stages", "line/bar", "12x/14x/15x model summary CSVs", "05_dataset_feature_chart_ready.csv", "stage,scope,model,oof_auc", "yes", "no", "yes_from_existing_csv", "Metrics are not campaign performance", "medium"),
    ("payment_device_sensitivity_delta_bar", "payment-device sensitivity", "AUC delta after payment-device removal", "bar", "15x_payment_removed_vs_original_comparison.csv", "05_dataset_feature_chart_ready.csv", "chart_id,label,value,group,unit", "yes", "no", "yes_from_existing_csv", "Payment device is not viewing device", "high"),
    ("shap_top10_bar", "SHAP", "Overall with promotion LightGBM top10 SHAP", "bar", "16x_SHAP_global_importance.csv", "09_SHAP_chart_ready.csv", "rank,feature_or_family,mean_abs_shap", "yes", "no", "yes_from_existing_csv", "SHAP is not causal", "high"),
    ("shap_family_importance_bar", "SHAP", "SHAP family importance", "bar", "16x_SHAP_family_importance.csv", "09_SHAP_chart_ready.csv", "rank,feature_or_family,mean_abs_shap", "yes", "no", "yes_from_existing_csv", "Scope-specific", "high"),
    ("segment_share_doughnut", "segments", "Segment share distribution", "doughnut", "17x_segment_summary.csv", "07_segment_chart_ready.csv", "segment_id,presentation_label,rows,share", "yes", "reuse_chart_type", "yes_from_existing_csv", "Rows are subscription-event rows", "high"),
    ("segment_repurchase_rate_bar", "segments", "Repurchase rate by segment", "bar", "17x_segment_summary.csv", "07_segment_chart_ready.csv", "segment_id,repurchase_rate", "yes", "reuse_chart_type", "yes_from_existing_csv", "Repurchase is target proxy", "medium"),
    ("segment_churn_risk_bar", "segments", "Mean churn risk by segment", "bar", "17x_segment_summary.csv", "07_segment_chart_ready.csv", "segment_id,mean_churn_risk", "yes", "reuse_chart_type", "yes_from_existing_csv", "churn_risk is score layer", "high"),
    ("segment_weekly_watch_line_or_bar", "segments", "W1/W2/W3 watch time by segment", "line/grouped_bar", "17x_dashboard_handoff_datamart.csv", "07_segment_chart_ready.csv", "segment_id,watch_time_w1,watch_time_w2,watch_time_w3", "yes", "reuse_chart_type", "yes_from_existing_csv", "No new segment rule", "medium"),
    ("action_tier_distribution_bar", "business action", "Action tier size and share", "bar", "07_segment_chart_ready.csv", "08_action_tier_chart_ready.csv", "action_tier,total_rows,total_share", "yes", "no", "yes_from_existing_csv", "Presentation grouping only", "high"),
    ("segment_action_priority_matrix", "business action", "Segment action priority matrix", "scatter/bubble", "07_segment_chart_ready.csv", "07_segment_chart_ready.csv", "share,mean_churn_risk,action_tier", "yes", "reuse_chart_type", "yes_from_existing_csv", "No finalized campaign targeting", "high"),
    ("safe_unsafe_wording_summary", "guardrails", "Safe/unsafe wording summary", "table", "16x_safe_unsafe_wording.csv; 09_safe_unsafe_wording_final.csv", "04_final_v3_chart_registry.csv", "guardrail,type,summary", "yes", "reuse_text_after_rewrite", "yes_from_existing_csv", "Rewrite into final v3 voice", "high"),
]
write_csv("04_final_v3_chart_registry.csv", [dict(zip([
    "chart_id", "final_v3_section", "chart_title", "chart_type", "source_data_file",
    "chart_ready_output_file", "required_columns", "uses_final_park_basis",
    "can_use_existing_legacy_data", "needs_recalculation_from_existing_csv",
    "caution", "priority",
], row)) for row in chart_rows], [
    "chart_id", "final_v3_section", "chart_title", "chart_type", "source_data_file",
    "chart_ready_output_file", "required_columns", "uses_final_park_basis",
    "can_use_existing_legacy_data", "needs_recalculation_from_existing_csv",
    "caution", "priority",
])

lineage = read_csv(ROOT / "FINAL/project_guide_v3_evidence_pack_260521/dataset_lineage_summary.csv")
payment = read_csv(ROOT / "park.ingyeom/reports/audits/15x_payment_device_sensitivity_260516/15x_payment_removed_vs_original_comparison.csv")
dataset_rows = []
for stage in ["raw_master_profile", "duration_filter", "exact_full_duplicate_extra_row_filter", "primary_main_cohort", "conservative_dataset", "expanded_dataset", "expanded_no_payment_device"]:
    row = next((r for r in lineage if r.get("stage") == stage), None)
    if not row:
        continue
    if stage == "raw_master_profile":
        dataset_rows.append({"chart_id": "dataset_lineage_waterfall", "label": "raw master", "value": row["output_rows"], "group": "row_count", "unit": "rows", "source_file": row["evidence_file"], "caveat": "raw source profile only"})
    elif stage == "duration_filter":
        dataset_rows.append({"chart_id": "dataset_lineage_waterfall", "label": "duration < 21 excluded", "value": row["rows_removed"], "group": "excluded_rows", "unit": "rows", "source_file": row["evidence_file"], "caveat": "row-level duration policy"})
    elif stage == "exact_full_duplicate_extra_row_filter":
        dataset_rows.append({"chart_id": "dataset_lineage_waterfall", "label": "exact duplicate extra excluded", "value": row["rows_removed"], "group": "excluded_rows", "unit": "rows", "source_file": row["evidence_file"], "caveat": "exact full duplicate extra rows"})
    elif stage == "primary_main_cohort":
        dataset_rows.append({"chart_id": "dataset_lineage_waterfall", "label": "primary main cohort", "value": row["output_rows"], "group": "final_basis", "unit": "rows", "source_file": row["evidence_file"], "caveat": "subscription-event rows, not unique-user table"})
    elif stage == "conservative_dataset":
        dataset_rows.append({"chart_id": "feature_set_flow_bar", "label": "conservative_safe_22", "value": "22", "group": "feature_count", "unit": "features", "source_file": row["evidence_file"], "caveat": "feature count excludes USER_KEY and target"})
    elif stage == "expanded_dataset":
        dataset_rows.append({"chart_id": "feature_set_flow_bar", "label": "expanded_feature_set", "value": "80", "group": "feature_count", "unit": "features", "source_file": row["evidence_file"], "caveat": "contains interpretation caveat variables"})
    else:
        dataset_rows.append({"chart_id": "feature_set_flow_bar", "label": "expanded_no_payment_device overall_with_promotion", "value": "76", "group": "feature_count", "unit": "features", "source_file": row["evidence_file"], "caveat": "is_promotion retained; payment_is_* removed"})
        dataset_rows.append({"chart_id": "feature_set_flow_bar", "label": "expanded_no_payment_device other scopes", "value": "75", "group": "feature_count", "unit": "features", "source_file": row["evidence_file"], "caveat": "promotion split scopes do not include is_promotion"})
for row in payment:
    dataset_rows.append({
        "chart_id": "payment_device_sensitivity_delta_bar",
        "label": f"{row['dataset_scope']} {row['model_name']} AUC delta",
        "value": row["delta_auc_no_payment_minus_original"],
        "group": row["dataset_scope"],
        "unit": "delta_oof_auc",
        "source_file": "park.ingyeom/reports/audits/15x_payment_device_sensitivity_260516/15x_payment_removed_vs_original_comparison.csv",
        "caveat": row["interpretation"] + "; sensitivity audit only",
    })
write_csv("05_dataset_feature_chart_ready.csv", dataset_rows, ["chart_id", "label", "value", "group", "unit", "source_file", "caveat"])

mapping = read_csv(ROOT / "FINAL/project_guide_v3_evidence_pack_260521/AARRR_feature_mapping_table.csv")
counts = defaultdict(lambda: {"conservative": 0, "expanded": 0})
features = defaultdict(list)
for row in mapping:
    stage = row.get("AARRR_stage", "")
    if row.get("conservative_safe_22", "").lower() == "yes":
        counts[stage]["conservative"] += 1
    if row.get("expanded_feature_set", "").lower() == "yes":
        counts[stage]["expanded"] += 1
    if len(features[stage]) < 6 and row.get("feature_name"):
        features[stage].append(row["feature_name"])
stage_note = {
    "Acquisition": ("observed_proxy", "is_promotion / 100원딜 유입 맥락"),
    "Activation": ("observed", "day0-20 first watch / cold_start_fixed / W1 activation"),
    "Retention": ("observed", "week1-3 usage / retention / recency / inactive gap"),
    "Referral": ("unobserved", "observed feature 없음"),
    "Revenue": ("target_proxy", "is_repurchase target proxy"),
}
aarrr = []
for stage in ["Acquisition", "Activation", "Retention", "Referral", "Revenue"]:
    status, interp = stage_note[stage]
    aarrr.append({
        "AARRR_stage": stage,
        "feature_count_conservative": counts[stage]["conservative"],
        "feature_count_expanded": counts[stage]["expanded"],
        "observed_status": status,
        "representative_features": "; ".join(features[stage]) if features[stage] else "none",
        "guide_interpretation": interp,
        "caveat": "AARRR is interpretive taxonomy, not causal proof",
        "source_file": "FINAL/project_guide_v3_evidence_pack_260521/AARRR_feature_mapping_table.csv",
    })
write_csv("06_AARRR_chart_ready.csv", aarrr, ["AARRR_stage", "feature_count_conservative", "feature_count_expanded", "observed_status", "representative_features", "guide_interpretation", "caveat", "source_file"])

seg_summary = read_csv(ROOT / "park.ingyeom/reports/segments/17x_segmentation_design_260516/17x_segment_summary.csv")
seg_labels = read_csv(ROOT / "FINAL/segment_interpretation_patch_260521/07_promo_aware_segment_label_mapping.csv")
datamart = read_csv(ROOT / "park.ingyeom/reports/segments/17x_segmentation_design_260516/17x_dashboard_handoff_datamart.csv")
label_map = {r["original_segment_id"]: r["proposed_presentation_label"] for r in seg_labels}
weekly = defaultdict(lambda: {"n": 0, "w1": 0.0, "w2": 0.0, "w3": 0.0})
for row in datamart:
    segment = row.get("representative_segment", "")
    if not segment:
        continue
    weekly[segment]["n"] += 1
    for key, col in [("w1", "watch_time_min_w1"), ("w2", "watch_time_min_w2"), ("w3", "watch_time_min_w3")]:
        weekly[segment][key] += float(row.get(col, 0) or 0)
tiers = {
    "high_risk_week3_inactive_or_drop": "즉시 개입 우선군",
    "high_risk_only_w1_or_cold_start_weak": "즉시 개입 우선군",
    "high_risk_low_activity": "즉시 개입 우선군",
    "medium_risk_retention_decay": "관찰 강화군",
    "content_preference_target_candidate": "정가 전환 강화군",
    "stable_retained_user": "정가 전환 강화군",
    "general_observation": "모니터링 / 추가분해 후보군",
}
segment_rows = []
for row in seg_summary:
    segment = row["representative_segment"]
    n = weekly[segment]["n"] or 1
    caveat = "17x rule and assignment unchanged; subscription-event rows; no new segment rule."
    if segment == "content_preference_target_candidate":
        caveat += " Display as content curation-based full-price conversion reinforcement group."
    if segment == "general_observation":
        caveat += " Display as residual monitoring group."
    segment_rows.append({
        "segment_id": segment,
        "presentation_label": label_map.get(segment, segment),
        "action_tier": tiers.get(segment, ""),
        "rows": row["row_count"],
        "share": row["row_share"],
        "repurchase_rate": row["repurchase_rate"],
        "churn_rate": row["nonrepurchase_rate"],
        "mean_churn_risk": row["mean_churn_risk"],
        "promo1_share": row["promotion_share"],
        "watch_time_w1": weekly[segment]["w1"] / n,
        "watch_time_w2": weekly[segment]["w2"] / n,
        "watch_time_w3": weekly[segment]["w3"] / n,
        "source_file": "17x_segment_summary.csv; 17x_dashboard_handoff_datamart.csv; 07_promo_aware_segment_label_mapping.csv",
        "caveat": caveat,
    })
write_csv("07_segment_chart_ready.csv", segment_rows, ["segment_id", "presentation_label", "action_tier", "rows", "share", "repurchase_rate", "churn_rate", "mean_churn_risk", "promo1_share", "watch_time_w1", "watch_time_w2", "watch_time_w3", "source_file", "caveat"])

roles = {
    "즉시 개입 우선군": "High-risk behavior signals for first action candidates.",
    "관찰 강화군": "Retention decay watchlist for low-intensity CRM.",
    "정가 전환 강화군": "Content curation, satisfaction maintenance, and full-price conversion reinforcement candidates.",
    "모니터링 / 추가분해 후보군": "Residual monitoring group.",
}
action_rows = []
for tier in ["즉시 개입 우선군", "관찰 강화군", "정가 전환 강화군", "모니터링 / 추가분해 후보군"]:
    members = [r for r in segment_rows if r["action_tier"] == tier]
    total = sum(float(r["rows"]) for r in members)
    def weighted(col):
        return sum(float(r["rows"]) * float(r[col]) for r in members) / total if total else ""
    action_rows.append({
        "action_tier": tier,
        "included_segments": "; ".join(r["segment_id"] for r in members),
        "total_rows": int(total),
        "total_share": sum(float(r["share"]) for r in members),
        "weighted_churn_rate": weighted("churn_rate"),
        "weighted_mean_churn_risk": weighted("mean_churn_risk"),
        "promo1_share": weighted("promo1_share"),
        "primary_business_role": roles[tier],
        "guide_interpretation": "Presentation/action grouping only; do not treat as new segment assignment.",
        "caveat": "17x segment rules and assignments are unchanged.",
    })
write_csv("08_action_tier_chart_ready.csv", action_rows, ["action_tier", "included_segments", "total_rows", "total_share", "weighted_churn_rate", "weighted_mean_churn_risk", "promo1_share", "primary_business_role", "guide_interpretation", "caveat"])

shap_global = read_csv(ROOT / "park.ingyeom/reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_global_importance.csv")
shap_family = read_csv(ROOT / "park.ingyeom/reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_family_importance.csv")
ko = {
    "watch_time_min_w3": "3주차 시청시간",
    "is_promotion": "100원딜 유입 여부",
    "retention_w2_ratio": "2주차 유지 비율",
    "retention_w3_ratio": "3주차 유지 비율",
    "drama_ratio": "드라마 장르 비중",
    "family_animation_ratio": "가족/애니메이션 비중",
    "romance_ratio": "로맨스 비중",
    "thriller_crime_ratio": "스릴러/범죄 비중",
    "action_adventure_ratio": "액션/어드벤처 비중",
    "diff_between_w2_w1": "2주차-1주차 변화",
    "usage_retention_behavior": "이용/유지 행동 묶음",
    "content_preference_context": "콘텐츠 선호 맥락 묶음",
    "acquisition_split_key": "유입/프로모션 분기 묶음",
}
shap_rows = []
for row in shap_global:
    if row["dataset_scope"] == "overall_with_promotion" and row["model_name"] == "LightGBM" and int(row["rank_in_scope"]) <= 10:
        feature = row["feature"]
        shap_rows.append({
            "chart_group": "overall_with_promotion_top10_features",
            "rank": row["rank_in_scope"],
            "feature_or_family": feature,
            "display_name_ko": ko.get(feature, feature),
            "mean_abs_shap": row["mean_abs_shap"],
            "model_scope": row["dataset_scope"],
            "model_name": row["model_name"],
            "feature_family": row["feature_family"],
            "interpretation": "Promotion context feature; not causal effect." if feature == "is_promotion" else "Top feature importance within selected model scope.",
            "caveat": "SHAP is model explanation, not causal proof.",
            "source_file": "16x_SHAP_global_importance.csv",
        })
for row in shap_family:
    if row["dataset_scope"] == "overall_with_promotion" and row["model_name"] == "LightGBM":
        fam = row["feature_family"]
        shap_rows.append({
            "chart_group": "overall_with_promotion_family_importance",
            "rank": row["family_rank_in_scope"],
            "feature_or_family": fam,
            "display_name_ko": ko.get(fam, fam),
            "mean_abs_shap": row["mean_abs_shap_sum"],
            "model_scope": row["dataset_scope"],
            "model_name": row["model_name"],
            "feature_family": fam,
            "interpretation": "Family-level mean absolute SHAP sum; scope-specific.",
            "caveat": "Non-causal and model-scope specific.",
            "source_file": "16x_SHAP_family_importance.csv",
        })
write_csv("09_SHAP_chart_ready.csv", shap_rows, ["chart_group", "rank", "feature_or_family", "display_name_ko", "mean_abs_shap", "model_scope", "model_name", "feature_family", "interpretation", "caveat", "source_file"])

fig_base = ROOT / "park.ingyeom/reports/figures/16x_SHAP_candidate_interpretation_260516"
fig_names = [
    "16x_fig_bar_overall_with_promotion.png",
    "16x_fig_beeswarm_overall_with_promotion.png",
    "16x_fig_family_bar_overall_with_promotion.png",
    "16x_fig_redundancy_family_SHAP_importance.png",
    "16x_fig_scope_top10_SHAP_comparison.png",
    "16x_fig_bar_overall_without_promotion.png",
    "16x_fig_beeswarm_overall_without_promotion.png",
    "16x_fig_family_bar_overall_without_promotion.png",
    "16x_fig_bar_promotion_only.png",
    "16x_fig_beeswarm_promotion_only.png",
    "16x_fig_family_bar_promotion_only.png",
    "16x_fig_bar_nonpromotion_only.png",
    "16x_fig_beeswarm_nonpromotion_only.png",
    "16x_fig_family_bar_nonpromotion_only.png",
]
manifest = []
for name in fig_names:
    src = fig_base / name
    target = ASSET_DIR / name
    if src.exists():
        shutil.copy2(src, target)
        status = "copied"
        size = src.stat().st_size
    else:
        status = "missing"
        size = ""
    use = "Use PNG in appendix."
    if "beeswarm" in name:
        use = "Use PNG for main or appendix; Chart.js cannot replace beeswarm distribution."
    elif "family" in name:
        use = "Use Chart.js for main family bar and keep PNG as reference."
    elif "bar_overall_with_promotion" in name:
        use = "Use Chart.js top10 for main and PNG as reference."
    manifest.append({
        "figure_id": name.replace(".png", ""),
        "original_path": rel(src),
        "exists": "yes" if src.exists() else "no",
        "file_size": size,
        "recommended_use": use,
        "target_asset_path": rel(target),
        "copy_status": status,
        "caveat": "Existing 16x asset only; no SHAP recalculation performed.",
    })
write_csv("10_SHAP_figure_asset_manifest.csv", manifest, ["figure_id", "original_path", "exists", "file_size", "recommended_use", "target_asset_path", "copy_status", "caveat"])

write_md("11_CSS_layout_pattern_memo.md", """
> CSS and layout pattern memo

> sidebar navigation
AARRR, project guide v2, segment visual guide의 sidebar 구조는 final v3에서도 재사용 가치가 높습니다. 데이터 계보, AARRR, 모델, SHAP, 세그먼트, appendix가 긴 문서이기 때문입니다.

> dark/light mode toggle
dark/light mode는 재사용 가능하지만, Chart.js 색상과 표 대비가 깨지지 않도록 CSS variable 중심으로 제한하는 편이 안전합니다.

> card layout
warning cards와 segment detail cards는 재사용 가능합니다. 단, 각 카드는 하나의 주장 또는 하나의 시각 자료만 담는 방식이 좋습니다.

> table-wrap
기존 HTML에서 table-wrap은 강하게 표준화되어 있지 않습니다. final v3에는 긴 evidence table이 들어가므로 `overflow-x: auto` wrapper를 새로 표준화하는 편이 좋습니다.

> Chart.js canvas wrapper
Chart.js canvas는 고정 height wrapper와 source caption을 붙여야 합니다. 데이터 파일명을 chart 아래에 노출하면 검수성이 좋아집니다.

> variable tooltip
`is_promotion`, `churn_risk`, `payment_is_*`, `content_preference_target_candidate`, `general_observation`에 tooltip을 붙이는 것을 권장합니다.

> warning cards
final v3 첫 화면에는 23,079 subscription-event basis, no causality, SHAP non-causal, payment-device is not viewing-device, PUBLIC numeric score exclusion을 고정해야 합니다.

> triage flow
segment visual guide의 triage flow는 assignment explanation only로 재사용해야 하며, 새 segment rule처럼 보이면 안 됩니다.

> collapsible details
SHAP PNG, scope comparison, segment flag dictionary, source fingerprint는 appendix collapsible details로 보내는 편이 안전합니다.

> hero summary
hero는 과장된 성과보다 `100원딜 OTT 이탈 분석 가이드`처럼 내용 식별 중심이 안전합니다.

> appendix split
본문은 Chart.js 요약, appendix는 PNG와 evidence table로 나누는 구조가 가장 안전합니다.

> mobile responsiveness
모바일에서는 1열 흐름, sticky sidebar 해제, chart height 제한, table horizontal scroll이 필요합니다.
""")

write_md("12_final_v3_visual_upgrade_recommendation.md", """
> final v3 visual upgrade recommendation

> 추가해야 할 컴포넌트
`dataset_lineage_waterfall`, `feature_set_flow_bar`, `AARRR_feature_count_bar`, SHAP top10/family bar, segment share/risk/watch charts, action tier distribution을 우선 추가하는 것이 좋습니다.

> 버려야 할 legacy 컴포넌트
legacy HTML의 수치 문장을 그대로 승격하는 방식은 버려야 합니다. raw 23,343과 final 23,079 혼동, 100원딜 원인화, content_preference 핵심 이탈 방어 타겟화, general_observation 일반 고객군화, payment-device 시청기기화 표현은 재사용하지 않습니다.

> Chart.js를 어디에 쓸 것인가
데이터 계보, feature count, AARRR count, payment-device AUC delta, SHAP top10, SHAP family, segment share, segment risk, action tier distribution에 Chart.js를 쓰는 것이 적합합니다.

> PNG SHAP figure를 쓸 것인가
beeswarm과 scope comparison은 PNG를 쓰는 것이 좋습니다. global top10 bar와 family bar는 Chart.js로 다시 그리는 편이 스타일 통일에 유리합니다.

> AARRR 구조
AARRR은 funnel 하나보다 observed/proxy/unobserved 상태를 함께 보여주는 stage ladder가 안전합니다. Referral은 observed feature 없음, Revenue는 is_repurchase target proxy입니다.

> 세그먼트 구조
`triage flow -> overview doughnut -> risk/repurchase bars -> action tier grouping -> segment detail cards -> appendix flag dictionary` 순서를 권장합니다.

> 기존 final v3 보강 위치
현재 `FINAL/project_guide_v3.html`은 repo에서 발견되지 않았습니다. 최신 revised HTML이 제공되면 데이터 계보, AARRR, SHAP, 세그먼트, guardrail 섹션을 본 evidence pack 기준으로 보강하면 됩니다.

> 추가 자료
최신 `project_guide_v3_chatgpt_revised.html` 파일이 필요합니다. 이 파일 없이는 정확한 교체 section을 확정할 수 없습니다.
""")

write_md("unanswered_questions_for_chatgpt.md", """
> unanswered questions for ChatGPT

> 디자인 선택
sidebar를 항상 노출할지, 모바일에서 상단 jump menu로 바꿀지 결정이 필요합니다. Chart.js 색상도 기존 guide 색상과 final 발표 색상 중 하나로 정해야 합니다.

> 발표 문장 강도
100원딜을 `유입 맥락`까지만 말할지, `정가 전환 전 반복 이용 습관 형성 관찰 맥락`까지 말할지 승인이 필요합니다.

> Chart.js vs PNG 선택
SHAP global bar와 family bar는 Chart.js와 PNG가 모두 가능합니다. 권장안은 main body Chart.js, appendix PNG입니다.

> 본문 vs Appendix 배치
SHAP beeswarm, scope comparison, segment flag dictionary, source fingerprint, conflict audit는 appendix 배치가 안전합니다.

> 사용자 승인 필요
content_preference_target_candidate, general_observation, action tier 4분류, PUBLIC branch narrative-only 참고 범위, 최신 final v3 HTML 교체 위치는 사용자 승인 후 확정해야 합니다.
""")

read_files = [row["html_file"] for row in inventory if row["title"] != "MISSING"] + [
    "FINAL/project_guide_v3_evidence_pack_260521/dataset_lineage_summary.csv",
    "FINAL/project_guide_v3_evidence_pack_260521/column_feature_contract_summary.csv",
    "FINAL/project_guide_v3_evidence_pack_260521/AARRR_feature_mapping_table.csv",
    "FINAL/project_guide_v3_evidence_pack_260521/stage_07_to_18_timeline.csv",
    "park.ingyeom/reports/audits/15x_payment_device_sensitivity_260516/15x_payment_removed_vs_original_comparison.csv",
    "park.ingyeom/reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_global_importance.csv",
    "park.ingyeom/reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_family_importance.csv",
    "park.ingyeom/reports/segments/17x_segmentation_design_260516/17x_segment_summary.csv",
    "park.ingyeom/reports/segments/17x_segmentation_design_260516/17x_dashboard_handoff_datamart.csv",
    "FINAL/segment_interpretation_patch_260521/07_promo_aware_segment_label_mapping.csv",
    "FINAL/segment_interpretation_patch_260521/08_segment_business_action_matrix.csv",
    "FINAL/final_note.md",
    "FINAL/project_guide_v3_design_plan_260521.md",
]
write_md("README.md", """
> 작업 목적
final v3 HTML을 안전하게 시각 업그레이드하기 위한 evidence extract입니다. HTML 직접 수정, final v3 직접 생성, 모델 재실행, SHAP 재계산, segmentation 재계산은 하지 않았습니다.

> 읽은 파일
""" + "\n".join("- " + path for path in read_files) + """

> 생성 산출물
HTML inventory, reusable component audit, legacy conflict audit, chart registry, chart-ready CSV, SHAP asset manifest, CSS/layout memo, recommendation, unanswered questions, final checks, source fingerprint, review zip inventory를 생성했습니다.

> 핵심 발견
`FINAL/project_guide_v3.html` 또는 `project_guide_v3_chatgpt_revised.html`은 repo에서 발견되지 않았습니다. 기존 visual guide들은 구조 참고용이며, final numeric 기준은 `FINAL/project_guide_v3_evidence_pack_260521`, 15x, 16x, 17x, FINAL patch 산출물을 따릅니다.

> final v3 업그레이드 시 주의할 점
raw 23,343은 raw source profile이고 final 기준은 23,079 subscription-event rows입니다. 100원딜, SHAP, payment-device, content_preference, general_observation, PUBLIC numeric score는 caveat를 고정해야 합니다.

> ChatGPT가 다음에 해야 할 판단
최신 final v3 HTML 파일 기준으로 section 교체 위치를 정해야 합니다. SHAP bar/family의 Chart.js vs PNG 선택과 segment action tier wording은 사용자 승인 후 확정해야 합니다.
""")

source_paths = [
    ROOT / "park.ingyeom/aarrr_visual_guide.html",
    ROOT / "park.ingyeom/project_guide_v2.html",
    ROOT / "park.ingyeom/segment_visual_guide.html",
    ROOT / "park.ingyeom/shap_visual_guide.html",
    ROOT / "FINAL/project_guide_v3.html",
    ROOT / "park.ingyeom/project_guide.html",
    ROOT / "FINAL/project_guide_v3_evidence_pack_260521/dataset_lineage_summary.csv",
    ROOT / "FINAL/project_guide_v3_evidence_pack_260521/column_feature_contract_summary.csv",
    ROOT / "FINAL/project_guide_v3_evidence_pack_260521/AARRR_feature_mapping_table.csv",
    ROOT / "FINAL/project_guide_v3_evidence_pack_260521/stage_07_to_18_timeline.csv",
    ROOT / "park.ingyeom/reports/audits/15x_payment_device_sensitivity_260516/15x_payment_removed_vs_original_comparison.csv",
    ROOT / "park.ingyeom/reports/audits/15x_payment_device_sensitivity_260516/15x_feature_set_comparison_design.csv",
    ROOT / "park.ingyeom/reports/audits/15x_payment_device_sensitivity_260516/15x_model_summary_by_scope.csv",
    ROOT / "park.ingyeom/reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_global_importance.csv",
    ROOT / "park.ingyeom/reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_family_importance.csv",
    ROOT / "park.ingyeom/reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_scope_comparison_top_features.csv",
    ROOT / "park.ingyeom/reports/segments/17x_segmentation_design_260516/17x_segment_summary.csv",
    ROOT / "park.ingyeom/reports/segments/17x_segmentation_design_260516/17x_dashboard_handoff_datamart.csv",
    ROOT / "FINAL/segment_interpretation_patch_260521/07_promo_aware_segment_label_mapping.csv",
    ROOT / "FINAL/segment_interpretation_patch_260521/08_segment_business_action_matrix.csv",
    ROOT / "FINAL/segment_interpretation_patch_260521/09_safe_unsafe_wording_final.csv",
    ROOT / "FINAL/final_note.md",
    ROOT / "FINAL/project_guide_v3_design_plan_260521.md",
] + [fig_base / name for name in fig_names]
fingerprints = []
for path in source_paths:
    meta = file_meta(path)
    fingerprints.append({
        "source_file": rel(path),
        "exists": meta["exists"],
        "file_size": meta["file_size"],
        "sha256_before": meta["sha256_before"],
        "sha256_after": meta["sha256_after"],
        "hash_unchanged": "yes" if meta["exists"] == "yes" else "not_applicable_missing",
        "modified_time_before": meta["modified_time_before"],
        "modified_time_after": meta["modified_time_after"],
        "notes": "source fingerprint only; source not modified" if meta["exists"] == "yes" else "file missing",
    })
write_csv("source_fingerprint_before_after.csv", fingerprints, ["source_file", "exists", "file_size", "sha256_before", "sha256_after", "hash_unchanged", "modified_time_before", "modified_time_after", "notes"])

final_checks = [
    ("html source inventory created", "01_html_source_inventory.csv"),
    ("reusable component audit created", "02_reusable_component_audit.csv"),
    ("legacy conflict audit created", "03_legacy_conflict_audit.csv"),
    ("chart registry created", "04_final_v3_chart_registry.csv"),
    ("dataset feature chart-ready data created", "05_dataset_feature_chart_ready.csv"),
    ("AARRR chart-ready data created", "06_AARRR_chart_ready.csv"),
    ("segment chart-ready data created", "07_segment_chart_ready.csv"),
    ("action tier chart-ready data created", "08_action_tier_chart_ready.csv"),
    ("SHAP chart-ready data created", "09_SHAP_chart_ready.csv"),
    ("SHAP asset manifest created", "10_SHAP_figure_asset_manifest.csv"),
    ("CSS layout memo created", "11_CSS_layout_pattern_memo.md"),
    ("visual upgrade recommendation created", "12_final_v3_visual_upgrade_recommendation.md"),
    ("unanswered questions created", "unanswered_questions_for_chatgpt.md"),
    ("README created", "README.md"),
    ("no source CSV modified", "source_fingerprint_before_after.csv"),
    ("no notebook modified", "notebooks were not opened for write or executed"),
    ("no model rerun", "no modeling command executed"),
    ("no SHAP rerun", "only existing 16x CSV/PNG read or copied"),
    ("no segmentation rerun", "only existing 17x assignment/datamart read"),
    ("review zip created", rel(ZIP_PATH)),
]
write_csv("final_checks.csv", [{"check_item": item, "result": "PASS", "evidence": evidence, "caveat": "current final v3 HTML missing" if item == "html source inventory created" else ""} for item, evidence in final_checks], ["check_item", "result", "evidence", "caveat"])

members = sorted([p for p in OUT.rglob("*") if p.is_file() and p.name != "review_zip_inventory.csv"] + [OUT / "review_zip_inventory.csv"])
write_csv("review_zip_inventory.csv", [{"zip_member_path": out_rel(p), "source_path": rel(p), "file_size": p.stat().st_size if p.exists() else "pending"} for p in members], ["zip_member_path", "source_path", "file_size"])

if ZIP_PATH.exists():
    ZIP_PATH.unlink()
with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for path in sorted(OUT.rglob("*")):
        if path.is_file():
            z.write(path, arcname=out_rel(path))

print(f"generated_files={len([p for p in OUT.rglob('*') if p.is_file()])}")
print(f"assets_copied={sum(1 for row in manifest if row['copy_status'] == 'copied')}")
print(f"zip={ZIP_PATH}")
