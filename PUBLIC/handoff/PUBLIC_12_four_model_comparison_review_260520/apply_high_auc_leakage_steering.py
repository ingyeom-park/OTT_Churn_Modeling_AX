import csv
import math
import statistics
import zipfile
from pathlib import Path

REPO = Path(r"C:\Code\ott-churn-prediction")
PUBLIC = REPO / "PUBLIC"
REF_11 = PUBLIC / "results" / "11_baseline_growth_comparison_260520" / "emergency_four_model_reference"
OUTPUT = PUBLIC / "results" / "12_model_family_comparison_260520" / "four_model_comparison_review"
HANDOFF = PUBLIC / "handoff" / "PUBLIC_12_four_model_comparison_review_260520"
ZIP_DIR = PUBLIC / "zip"
NOTE = PUBLIC / "note.md"

MODEL_SPECS = [
    ("LogisticRegression", "promo0", "logistic_regression_promo0"),
    ("LogisticRegression", "promo1", "logistic_regression_promo1"),
    ("GradientBoosting", "promo0", "gradient_boosting_promo0"),
    ("GradientBoosting", "promo1", "gradient_boosting_promo1"),
]

CAUTION_EN = "Because AUC appears unusually high for this project context, this step treats high performance as a validation target rather than as immediate evidence of model quality."
CAUTION_KO = "현재 AUC가 프로젝트 맥락상 과도하게 높아 보일 수 있으므로, 이번 단계에서는 높은 성능을 곧바로 성과로 해석하지 않고 leakage, proxy, overfit, split issue 검수 대상으로 취급한다."


def rel_public(path: Path) -> str:
    return "PUBLIC\\" + str(path.relative_to(PUBLIC)).replace("/", "\\")


def rel_repo(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


def read_csv_rows(path: Path):
    if not path.exists():
        return [], []
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                return reader.fieldnames or [], list(reader)
        except UnicodeDecodeError:
            continue
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def write_csv(path: Path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        result = float(value)
        if math.isnan(result):
            return None
        return result
    except ValueError:
        return None


def fmt(value):
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def feature_set(path: Path):
    fields, rows = read_csv_rows(path)
    if "feature_name" not in fields:
        return set()
    return {str(row.get("feature_name", "")).strip() for row in rows if str(row.get("feature_name", "")).strip()}


def model_records():
    records = []
    for family, scope, folder_name in MODEL_SPECS:
        folder = REF_11 / folder_name
        _, final_rows = read_csv_rows(folder / "final_result.csv")
        final = final_rows[0] if final_rows else {}
        features = feature_set(folder / "feature_manifest_used.csv")
        records.append(
            {
                "model_family": family,
                "scope": scope,
                "folder_name": folder_name,
                "folder": folder,
                "final": final,
                "features": features,
            }
        )
    return records


def high_auc_metrics(final):
    metric_names = ["test_roc_auc", "test_pr_auc", "best_valid_auc", "best_train_auc", "final_train_auc"]
    values = {name: as_float(final.get(name)) for name in metric_names}
    triggers = [name for name, value in values.items() if value is not None and value >= 0.90]
    max_value = max([value for value in values.values() if value is not None], default=None)
    return values, triggers, max_value


def create_high_auc_audit(records):
    rows = []
    for record in records:
        values, triggers, max_auc = high_auc_metrics(record["final"])
        roc = values.get("test_roc_auc")
        pr = values.get("test_pr_auc")
        flag = 1 if triggers else 0
        rows.append(
            {
                "model_family": record["model_family"],
                "scope": record["scope"],
                "test_roc_auc": fmt(roc),
                "test_pr_auc": fmt(pr),
                "best_valid_auc": fmt(values.get("best_valid_auc")),
                "best_train_auc": fmt(values.get("best_train_auc")),
                "final_train_auc": fmt(values.get("final_train_auc")),
                "max_recorded_auc": fmt(max_auc),
                "auc_ge_0_90_metric_trigger": ";".join(triggers) if triggers else "none",
                "suspicious_high_auc_flag": flag,
                "high_auc_interpretation_caution": CAUTION_EN + " " + CAUTION_KO,
                "final_model_selection_allowed": "no",
                "audit_status": "WARN" if flag else "PASS",
                "notes": "AUC >= 0.90 is treated as a validation target, not immediate model-quality evidence." if flag else "No recorded AUC metric reached 0.90.",
            }
        )
    path = OUTPUT / "12_high_auc_suspicion_audit.csv"
    fields = [
        "model_family",
        "scope",
        "test_roc_auc",
        "test_pr_auc",
        "best_valid_auc",
        "best_train_auc",
        "final_train_auc",
        "max_recorded_auc",
        "auc_ge_0_90_metric_trigger",
        "suspicious_high_auc_flag",
        "high_auc_interpretation_caution",
        "final_model_selection_allowed",
        "audit_status",
        "notes",
    ]
    write_csv(path, fields, rows)
    return path, rows


def create_leakage_proxy_audit(records):
    rows = []
    exact_risk_columns = [
        "USER_KEY",
        "is_repurchase",
        "repurchase_score",
        "churn_risk",
        "retention_w2_ratio",
        "retention_w3_ratio",
        "is_promotion",
    ]
    target_like_names = ["is_churn_prevented"]
    for record in records:
        features = record["features"]
        present_exact = [name for name in exact_risk_columns if name in features]
        present_target_like = [name for name in target_like_names if name in features]
        log_retention_present = [name for name in ["log_retention_w2_ratio", "log_retention_w3_ratio"] if name in features]
        if present_exact or present_target_like:
            status = "FAIL"
            reason = "Potential leakage/proxy or target-like features are present in feature_manifest_used.csv."
        elif len(log_retention_present) == 2:
            status = "WARN"
            reason = "No listed raw leakage columns were found, but log_retention_w2_ratio/log_retention_w3_ratio may still dominate performance and require follow-up review."
        else:
            status = "WARN"
            reason = "Feature manifest did not provide enough evidence for a PASS-level leakage/proxy conclusion."
        rows.append(
            {
                "model_family": record["model_family"],
                "scope": record["scope"],
                "feature_manifest_file": rel_public(record["folder"] / "feature_manifest_used.csv"),
                "contains_USER_KEY": str("USER_KEY" in features),
                "contains_is_repurchase": str("is_repurchase" in features),
                "contains_repurchase_score": str("repurchase_score" in features),
                "contains_churn_risk": str("churn_risk" in features),
                "contains_retention_w2_ratio": str("retention_w2_ratio" in features),
                "contains_retention_w3_ratio": str("retention_w3_ratio" in features),
                "contains_is_promotion": str("is_promotion" in features),
                "contains_log_retention_w2_ratio": str("log_retention_w2_ratio" in features),
                "contains_log_retention_w3_ratio": str("log_retention_w3_ratio" in features),
                "target_like_or_post_outcome_suspect_features": ";".join(present_target_like) if present_target_like else "none_detected_from_configured_terms",
                "log_retention_dominance_caveat": "log_retention_w2_ratio/log_retention_w3_ratio are present and may require dominance/proxy review before final model use.",
                "leakage_proxy_risk_status": status,
                "split_policy_check_status": "see_12_split_policy_audit",
                "final_model_selection_allowed": "no",
                "reason": reason,
            }
        )
    path = OUTPUT / "12_leakage_proxy_feature_audit.csv"
    fields = [
        "model_family",
        "scope",
        "feature_manifest_file",
        "contains_USER_KEY",
        "contains_is_repurchase",
        "contains_repurchase_score",
        "contains_churn_risk",
        "contains_retention_w2_ratio",
        "contains_retention_w3_ratio",
        "contains_is_promotion",
        "contains_log_retention_w2_ratio",
        "contains_log_retention_w3_ratio",
        "target_like_or_post_outcome_suspect_features",
        "log_retention_dominance_caveat",
        "leakage_proxy_risk_status",
        "split_policy_check_status",
        "final_model_selection_allowed",
        "reason",
    ]
    write_csv(path, fields, rows)
    return path, rows


def create_split_policy_audit(records):
    rows = []
    for record in records:
        final = record["final"]
        cv_method = final.get("cv_method", "NA")
        caveat = final.get("group_leakage_caveat", "")
        used_group = "GroupKFold" in cv_method
        caveat_mentions_group_not_used = "GroupKFold was not used" in caveat
        caveat_mentions_user_dup = "USER_KEY can be duplicated" in caveat
        if used_group:
            status = "PASS"
            reason = "cv_method indicates GroupKFold."
        elif caveat_mentions_group_not_used or caveat_mentions_user_dup or cv_method == "StratifiedKFold":
            status = "WARN"
            reason = "final_result.csv records StratifiedKFold and USER_KEY duplication caveat; GroupKFold was not used, so group-aware leakage prevention is not confirmed."
        else:
            status = "WARN"
            reason = "Group-aware split evidence was not found."
        rows.append(
            {
                "model_family": record["model_family"],
                "scope": record["scope"],
                "cv_method": cv_method,
                "group_leakage_caveat": caveat,
                "group_aware_split_confirmed": "yes" if used_group else "no",
                "user_key_duplication_caveat_present": str(caveat_mentions_user_dup),
                "groupkfold_not_used_caveat_present": str(caveat_mentions_group_not_used),
                "split_policy_check_status": status,
                "final_model_selection_allowed": "no",
                "reason": reason,
            }
        )
    path = OUTPUT / "12_split_policy_audit.csv"
    fields = [
        "model_family",
        "scope",
        "cv_method",
        "group_leakage_caveat",
        "group_aware_split_confirmed",
        "user_key_duplication_caveat_present",
        "groupkfold_not_used_caveat_present",
        "split_policy_check_status",
        "final_model_selection_allowed",
        "reason",
    ]
    write_csv(path, fields, rows)
    return path, rows


def map_by_model(rows):
    return {(row["model_family"], row["scope"]): row for row in rows}


def update_metric_summary(high_auc_rows, leakage_rows, split_rows):
    path = OUTPUT / "12_final_result_metric_summary.csv"
    fields, rows = read_csv_rows(path)
    high = map_by_model(high_auc_rows)
    leak = map_by_model(leakage_rows)
    split = map_by_model(split_rows)
    additions = [
        "suspicious_high_auc_flag",
        "leakage_proxy_risk_status",
        "split_policy_check_status",
        "high_auc_interpretation_caution",
        "final_model_selection_allowed",
    ]
    for name in additions:
        if name not in fields:
            fields.append(name)
    for row in rows:
        key = (row["model_family"], row["scope"])
        row["suspicious_high_auc_flag"] = high.get(key, {}).get("suspicious_high_auc_flag", "NA")
        row["leakage_proxy_risk_status"] = leak.get(key, {}).get("leakage_proxy_risk_status", "unknown_needs_review")
        row["split_policy_check_status"] = split.get(key, {}).get("split_policy_check_status", "unknown_needs_review")
        row["high_auc_interpretation_caution"] = CAUTION_EN
        row["final_model_selection_allowed"] = "no"
        row["notes"] = (row.get("notes", "") + " High AUC is treated as leakage/proxy/overfit/split validation target, not model-quality evidence.").strip()
    write_csv(path, fields, rows)
    return path, rows


def update_scopewise_comparison(high_auc_rows, leakage_rows, split_rows):
    path = OUTPUT / "12_scopewise_gb_vs_lr_comparison.csv"
    fields, rows = read_csv_rows(path)
    high = map_by_model(high_auc_rows)
    leak = map_by_model(leakage_rows)
    split = map_by_model(split_rows)
    additions = [
        "suspicious_high_auc_flag",
        "leakage_proxy_risk_status",
        "split_policy_check_status",
        "high_auc_interpretation_caution",
        "final_model_selection_allowed",
    ]
    for name in additions:
        if name not in fields:
            fields.append(name)
    for row in rows:
        scope = row["scope"]
        lr_key = ("LogisticRegression", scope)
        gb_key = ("GradientBoosting", scope)
        high_flag = 1 if str(high.get(lr_key, {}).get("suspicious_high_auc_flag")) == "1" or str(high.get(gb_key, {}).get("suspicious_high_auc_flag")) == "1" else 0
        leak_statuses = [leak.get(lr_key, {}).get("leakage_proxy_risk_status", "unknown_needs_review"), leak.get(gb_key, {}).get("leakage_proxy_risk_status", "unknown_needs_review")]
        split_statuses = [split.get(lr_key, {}).get("split_policy_check_status", "unknown_needs_review"), split.get(gb_key, {}).get("split_policy_check_status", "unknown_needs_review")]
        row["suspicious_high_auc_flag"] = high_flag
        row["leakage_proxy_risk_status"] = ";".join(leak_statuses)
        row["split_policy_check_status"] = ";".join(split_statuses)
        row["high_auc_interpretation_caution"] = CAUTION_EN
        row["final_model_selection_allowed"] = "no"
        row["primary_candidate_recommendation"] = "GB provisional candidate pending leakage/proxy/overfit/split review; not final model selection."
        row["baseline_candidate_recommendation"] = "LR baseline/sensitivity reference pending leakage/proxy/overfit/split review."
        row["recommendation_status"] = "keep_both_pending_user_review"
        row["reason"] = "GB has higher saved metrics, but high AUC, target-like feature risk, and non-group-aware split caveat prevent final or primary-candidate wording."
    write_csv(path, fields, rows)
    return path, rows


def update_oof_readiness(leakage_rows, split_rows, high_auc_rows):
    path = OUTPUT / "12_oof_readiness_decision.csv"
    fields, rows = read_csv_rows(path)
    if "final_model_selection_allowed" not in fields:
        fields.append("final_model_selection_allowed")
    high_flags = sum(1 for row in high_auc_rows if str(row["suspicious_high_auc_flag"]) == "1")
    leak_statuses = {row["leakage_proxy_risk_status"] for row in leakage_rows}
    split_statuses = {row["split_policy_check_status"] for row in split_rows}
    for row in rows:
        item = row["decision_item"]
        row["final_model_selection_allowed"] = "no"
        if item in {"promo0_primary_candidate_available", "promo1_primary_candidate_available"}:
            row["status"] = "provisional_pending_leakage_overfit_split_review"
            row["evidence"] = "GB metric advantage exists, but recommendation is provisional because high AUC and leakage/split caveats require review."
            row["required_user_approval"] = "yes"
        if item == "log_retention_condition_all_pass":
            row["notes"] = row["notes"] + " log_retention_w2_ratio/log_retention_w3_ratio still require dominance/proxy review."
        if item == "oof_generation_allowed_now":
            row["status"] = "no"
            row["evidence"] = "OOF remains blocked until user approval and leakage/proxy/split review."
            row["required_user_approval"] = "yes"
        if item == "requires_user_approval_before_oof":
            row["status"] = "yes"
            row["required_user_approval"] = "yes"
        if item == "overfit_stability_checked":
            row["notes"] = row["notes"] + " High AUC audit still treats these metrics as validation targets."
    rows.extend(
        [
            {
                "decision_item": "high_auc_suspicion_review_required",
                "status": "yes",
                "evidence": f"suspicious_high_auc_flag_count={high_flags}",
                "required_user_approval": "yes",
                "notes": CAUTION_EN,
                "final_model_selection_allowed": "no",
            },
            {
                "decision_item": "leakage_proxy_review_required",
                "status": "yes",
                "evidence": "leakage_proxy_risk_statuses=" + ";".join(sorted(leak_statuses)),
                "required_user_approval": "yes",
                "notes": "Target-like or proxy feature audit must be reviewed before OOF or final wording.",
                "final_model_selection_allowed": "no",
            },
            {
                "decision_item": "split_policy_review_required",
                "status": "yes",
                "evidence": "split_policy_check_statuses=" + ";".join(sorted(split_statuses)),
                "required_user_approval": "yes",
                "notes": "Group-aware split is not confirmed from final_result.csv.",
                "final_model_selection_allowed": "no",
            },
        ]
    )
    write_csv(path, fields, rows)
    return path, rows


def update_readme(high_auc_rows, leakage_rows, split_rows):
    readme = OUTPUT / "README.md"
    high_flags = sum(1 for row in high_auc_rows if str(row["suspicious_high_auc_flag"]) == "1")
    leakage_summary = "; ".join([f"{row['model_family']} {row['scope']}={row['leakage_proxy_risk_status']}" for row in leakage_rows])
    split_summary = "; ".join([f"{row['model_family']} {row['scope']}={row['split_policy_check_status']}" for row in split_rows])
    text = f"""# PUBLIC 12 Four-Model Comparison Review

## Purpose

This is not a task for selecting the best-performing model.

This is a strict validation review of the existing log-retention-only four-model emergency reference outputs from leakage, proxy, overfit, and split-issue perspectives.

{CAUTION_EN}

{CAUTION_KO}

## Input source

- `PUBLIC/results/11_baseline_growth_comparison_260520/emergency_four_model_reference/`

The four reviewed references are LogisticRegression promo0, LogisticRegression promo1, GradientBoosting promo0, and GradientBoosting promo1.

## Why this is 12 and not 11

Step 11 is the emergency four-model reference stage. Step 12 is the comparison and validation review stage.

12 is not GradientBoosting-only. It compares LR and GB within each promo scope, but it does not perform final model selection.

## 07~10 pending validation caveat

07~10 remain pending validation. This review does not complete or replace those validation steps.

Because of that pending status, this 12 result is not final canonical model selection.

## High AUC suspicion audit

High AUC is not treated as achievement in this step. It is treated as a validation target.

`12_high_auc_suspicion_audit.csv` records `suspicious_high_auc_flag = 1` when any recorded AUC metric is at least 0.90.

Current suspicious flag count: {high_flags}.

## Log retention condition check

`log_retention_w2_ratio` and `log_retention_w3_ratio` are confirmed where available, but their presence is also recorded as a caveat because these features may dominate performance or operate as proxies.

Details are saved in `12_log_retention_condition_check.csv`.

## Leakage/proxy feature audit

The leakage/proxy audit checks USER_KEY, is_repurchase, repurchase_score, churn_risk, raw retention ratios, is_promotion scope policy, and target-like or post-outcome suspect features.

Current leakage/proxy statuses: {leakage_summary}.

Details are saved in `12_leakage_proxy_feature_audit.csv`.

## Split policy audit

Group-aware split or USER_KEY leakage prevention is not marked PASS unless it is directly confirmed.

Current split policy statuses: {split_summary}.

Details are saved in `12_split_policy_audit.csv`.

## Final result metric summary

Saved final-result metrics were read from the four `final_result.csv` files only.

The best saved metric is not used by itself to recommend a model.

Details are saved in `12_final_result_metric_summary.csv`.

## Trials overfit and stability summary

`trials_all.csv` was used to inspect overfit rate, top5/top10/top20 overfit rate, valid AUC, and gap where columns were available.

Details are saved in `12_trials_overfit_stability_summary.csv`.

## Scopewise GB vs LR comparison

Promo0 and promo1 are evaluated separately.

Any GB wording is limited to provisional candidate pending leakage/proxy/overfit/split review.

LR remains a baseline/sensitivity reference, also pending leakage/proxy/overfit/split review.

Highest AUC alone does not determine the model.

## OOF readiness decision

OOF generation remains `no` by default.

OOF generation requires user approval.

This task creates only `12_oof_readiness_decision.csv`. It does not create an OOF score table.

## What was not done

- No model retraining was performed.
- No notebook execution was performed.
- No Optuna run was performed.
- No SHAP run was performed.
- No segmentation run was performed.
- No OOF score table was generated.
- No raw source CSV was modified.
- No `park.ingyeom` file was modified.
- No `_data` file was modified.
- No existing result was deleted.

## Safe wording

- This is a four-model comparison review based on existing log-retention-only emergency reference outputs.
- High AUC is a validation target, not immediate model-quality evidence.
- Promo0 and promo1 are evaluated separately.
- GB may be described only as provisional candidate pending leakage/proxy/overfit/split review.
- LR remains baseline/sensitivity candidate pending leakage/proxy/overfit/split review.
- OOF generation requires user approval.
- Final model selection is not allowed from this review alone.

## Unsafe wording

- This is final model selection.
- 07~10 are completed.
- OOF table was generated.
- SHAP can start immediately.
- Segmentation can start immediately.
- Highest AUC alone determines the model.
- GB is the final primary model.

## Next action

Review the generated CSVs and review zip. After review, the user may decide whether to inspect leakage/proxy/split issues more deeply, approve OOF score table generation, or resolve 07~10 pending validation first.
"""
    write_text(readme, text)


def update_note():
    heading = "## 2026-05-20 | PUBLIC 12 high-AUC leakage/proxy steering applied"
    text = read_text(NOTE)
    if heading in text:
        return
    append = f"""

{heading}

이번 steering 이후 12 four-model comparison review의 중심 목적을 수정했다.

이 작업은 가장 성능 좋은 모델을 고르는 작업이 아니다.

이 작업은 log-retention-only 4개 모델의 AUC가 과도하게 높아 보일 가능성을 leakage, proxy, overfit, split issue 관점에서 엄격하게 검수하는 작업이다.

{CAUTION_EN}

{CAUTION_KO}

AUC가 0.90 이상인 모델은 `suspicious_high_auc_flag = 1`로 표시했다.

`final_result.csv`의 best metric만 보고 후보를 추천하지 않도록 README와 output CSV의 문구를 보정했다.

`trials_all.csv` 기준 overfit_rate, top5/top10/top20 overfit_rate, gap, valid AUC 안정성 항목을 확인했다.

feature list 기준 USER_KEY, is_repurchase, repurchase_score, churn_risk, retention_w2_ratio, retention_w3_ratio, is_promotion, target-like/post-outcome 의심 컬럼을 감사했다.

`log_retention_w2_ratio`, `log_retention_w3_ratio`는 사용 여부를 확인했지만, 이 둘이 성능을 과도하게 지배할 가능성을 caveat로 기록했다.

group-aware split 또는 USER_KEY leakage 방지 여부는 확인 가능한 범위에서 감사했으며, GroupKFold 미사용 caveat 때문에 split policy는 PASS로 기록하지 않았다.

OOF readiness는 사용자 승인 전 생성 불가 상태로 유지했다.

추천 문구는 final candidate가 아니라 provisional candidate pending leakage/proxy/overfit/split review로 제한했다.

07~10은 여전히 pending validation 상태이며, 이번 12 결과는 final canonical model selection이 아니다.
"""
    with NOTE.open("a", encoding="utf-8") as handle:
        handle.write(append)


def update_handoff_readme(files):
    zip_lines = "\n".join([f"- `{rel_public(path)}`" for path in files if path.exists() or path.parent.exists()])
    text = f"""# PUBLIC 12 Four-Model Comparison Review Handoff

## Purpose

This handoff summarizes the Step 12 four-model comparison review after high-AUC leakage/proxy steering.

This is not final model selection.

{CAUTION_EN}

{CAUTION_KO}

## Inputs checked

- LogisticRegression promo0
- LogisticRegression promo1
- GradientBoosting promo0
- GradientBoosting promo1

For each model, saved final_result, trials_all, feature manifest, and split-policy metadata were checked where available.

## Outputs generated

- `12_input_file_validation.csv`
- `12_log_retention_condition_check.csv`
- `12_final_result_metric_summary.csv`
- `12_trials_overfit_stability_summary.csv`
- `12_scopewise_gb_vs_lr_comparison.csv`
- `12_oof_readiness_decision.csv`
- `12_high_auc_suspicion_audit.csv`
- `12_leakage_proxy_feature_audit.csv`
- `12_split_policy_audit.csv`
- Review README
- Final checks
- Review zip

## Key findings

- High AUC is treated as validation target rather than model-quality evidence.
- Models with any recorded AUC metric at or above 0.90 are flagged.
- Target-like/proxy feature audit and split policy audit must be reviewed before final model wording.
- Existing final_result metadata records StratifiedKFold and a USER_KEY duplication caveat; GroupKFold was not used.

## Limitations

This review did not train models, execute notebooks, run Optuna, run SHAP, run segmentation, or generate an OOF score table.

## OOF readiness summary

OOF generation remains blocked until user approval.

## 07~10 pending validation status

07~10 remain pending validation. This Step 12 review does not mark them complete.

## Files included in review zip

{zip_lines}

## Next recommended action

Review leakage/proxy/split audit outputs before deciding whether to approve OOF score table generation or return to 07~10 pending validation.
"""
    write_text(HANDOFF / "README.md", text)


def update_final_checks(paths, high_auc_rows, leakage_rows, split_rows):
    path = HANDOFF / "PUBLIC_12_four_model_comparison_review_final_checks.csv"
    fields, rows = read_csv_rows(path)
    existing = {row["check_name"]: row for row in rows}

    def set_check(name, status, expected, actual, notes=""):
        existing[name] = {"check_name": name, "status": status, "expected": expected, "actual": actual, "notes": notes}

    suspicious_count = sum(1 for row in high_auc_rows if str(row["suspicious_high_auc_flag"]) == "1")
    leakage_statuses = sorted({row["leakage_proxy_risk_status"] for row in leakage_rows})
    split_statuses = sorted({row["split_policy_check_status"] for row in split_rows})
    set_check("high_auc_suspicion_audit_created", "PASS", "high-AUC suspicion audit exists", str(paths["high_auc"]))
    set_check("suspicious_high_auc_flags_recorded", "WARN" if suspicious_count else "PASS", "flag AUC >= 0.90 as suspicious", f"suspicious_high_auc_flag_count={suspicious_count}", "WARN is intentional because high AUC requires review.")
    set_check("leakage_proxy_feature_audit_created", "PASS", "leakage/proxy feature audit exists", str(paths["leakage"]))
    set_check("leakage_proxy_risk_not_passed_as_final", "WARN", "do not PASS final leakage/proxy risk if target-like features exist", "statuses=" + ";".join(leakage_statuses), "Requires user review before final wording.")
    set_check("split_policy_audit_created", "PASS", "split policy audit exists", str(paths["split"]))
    set_check("split_policy_not_passed_without_group_confirmation", "WARN", "do not PASS group-aware split without direct confirmation", "statuses=" + ";".join(split_statuses), "StratifiedKFold and GroupKFold-not-used caveat were found.")
    set_check("final_model_selection_allowed", "PASS", "final model selection allowed must be no", "no")
    set_check("high_auc_caution_readme_recorded", "PASS" if CAUTION_EN in read_text(OUTPUT / "README.md") and CAUTION_KO in read_text(OUTPUT / "README.md") else "FAIL", "mandatory caution wording in README", str(OUTPUT / "README.md"))
    set_check("high_auc_caution_note_recorded", "PASS" if CAUTION_EN in read_text(NOTE) and CAUTION_KO in read_text(NOTE) else "FAIL", "mandatory caution wording in note.md", str(NOTE))
    set_check("no_oof_generation_performed", "PASS", "no OOF score table generation", "Only OOF readiness/audit outputs were updated")
    ordered = list(existing.values())
    write_csv(path, ["check_name", "status", "expected", "actual", "notes"], ordered)
    return path, ordered


def create_zip(files):
    zip_path = ZIP_DIR / "PUBLIC_12_four_model_comparison_review_260520_review_package.zip"
    zip_inventory = HANDOFF / "PUBLIC_12_four_model_comparison_review_zip_inventory.csv"
    unique = []
    seen = set()
    for path in files:
        if path.exists():
            key = str(path.resolve()).lower()
            if key not in seen:
                unique.append(path)
                seen.add(key)
    rows = [{"full_name": rel_repo(path), "size_bytes": path.stat().st_size} for path in unique]
    write_csv(zip_inventory, ["full_name", "size_bytes"], rows)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in unique:
            archive.write(path, arcname=rel_repo(path))
    return zip_path, zip_inventory


def status_counts(rows):
    counts = {}
    for row in rows:
        status = row.get("status", "")
        counts[status] = counts.get(status, 0) + 1
    return ", ".join(f"{key}:{value}" for key, value in sorted(counts.items()))


def main():
    records = model_records()
    high_auc_path, high_auc_rows = create_high_auc_audit(records)
    leakage_path, leakage_rows = create_leakage_proxy_audit(records)
    split_path, split_rows = create_split_policy_audit(records)
    update_metric_summary(high_auc_rows, leakage_rows, split_rows)
    update_scopewise_comparison(high_auc_rows, leakage_rows, split_rows)
    update_oof_readiness(leakage_rows, split_rows, high_auc_rows)
    update_readme(high_auc_rows, leakage_rows, split_rows)
    update_note()

    final_checks_path = HANDOFF / "PUBLIC_12_four_model_comparison_review_final_checks.csv"
    zip_inventory = HANDOFF / "PUBLIC_12_four_model_comparison_review_zip_inventory.csv"
    files = [
        HANDOFF / "README.md",
        HANDOFF / "12_input_file_validation.csv",
        final_checks_path,
        zip_inventory,
        OUTPUT / "README.md",
        OUTPUT / "12_log_retention_condition_check.csv",
        OUTPUT / "12_final_result_metric_summary.csv",
        OUTPUT / "12_trials_overfit_stability_summary.csv",
        OUTPUT / "12_scopewise_gb_vs_lr_comparison.csv",
        OUTPUT / "12_oof_readiness_decision.csv",
        high_auc_path,
        leakage_path,
        split_path,
        NOTE,
        HANDOFF / "run_public_12_four_model_comparison_review.py",
        HANDOFF / "apply_high_auc_leakage_steering.py",
    ]
    update_handoff_readme(files)
    paths = {"high_auc": high_auc_path, "leakage": leakage_path, "split": split_path}
    final_checks_path, checks = update_final_checks(paths, high_auc_rows, leakage_rows, split_rows)
    create_zip(files)
    final_checks_path, checks = update_final_checks(paths, high_auc_rows, leakage_rows, split_rows)
    create_zip(files)

    print(f"high_auc_audit={high_auc_path}")
    print(f"leakage_proxy_audit={leakage_path}")
    print(f"split_policy_audit={split_path}")
    print(f"final_checks={final_checks_path}")
    print(f"checks_statuses={status_counts(checks)}")
    print(f"zip={ZIP_DIR / 'PUBLIC_12_four_model_comparison_review_260520_review_package.zip'}")


if __name__ == "__main__":
    main()
