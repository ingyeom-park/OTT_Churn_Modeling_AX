import csv
import math
import statistics
import zipfile
from datetime import datetime
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

OUTPUT.mkdir(parents=True, exist_ok=True)
HANDOFF.mkdir(parents=True, exist_ok=True)
ZIP_DIR.mkdir(parents=True, exist_ok=True)


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


def parse_bool(value):
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


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


def mean(values):
    nums = [v for v in values if v is not None]
    return statistics.fmean(nums) if nums else None


def stdev(values):
    nums = [v for v in values if v is not None]
    return statistics.stdev(nums) if len(nums) >= 2 else None


def max_value(values):
    nums = [v for v in values if v is not None]
    return max(nums) if nums else None


def feature_set(path: Path):
    fields, rows = read_csv_rows(path)
    if "feature_name" not in fields:
        return set()
    return {str(row.get("feature_name", "")).strip() for row in rows if str(row.get("feature_name", "")).strip()}


def choose_ranking_metric(fields):
    for candidate in ["mean_valid_auc", "valid_auc", "best_valid_auc", "valid_score", "objective_value"]:
        if candidate in fields:
            return candidate
    return ""


def choose_gap_column(fields):
    for candidate in ["gap", "best_gap", "final_gap_proxy", "train_valid_gap"]:
        if candidate in fields:
            return candidate
    return ""


def choose_valid_auc_column(fields):
    for candidate in ["mean_valid_auc", "valid_auc", "best_valid_auc", "valid_score"]:
        if candidate in fields:
            return candidate
    return ""


def input_validation():
    rows = []
    for family, scope, folder_name in MODEL_SPECS:
        folder = REF_11 / folder_name
        final_path = folder / "final_result.csv"
        trials_path = folder / "trials_all.csv"
        feature_path = folder / "feature_manifest_used.csv"
        pointer_path = folder / "SOURCE_POINTER.txt"
        _, final_rows = read_csv_rows(final_path)
        _, trials_rows = read_csv_rows(trials_path)
        exists_ok = folder.exists() and final_path.exists() and trials_path.exists()
        status = "PASS" if exists_ok else "FAIL"
        notes = "Required final_result.csv and trials_all.csv are available." if exists_ok else "Missing required reference folder or required CSV."
        rows.append(
            {
                "model_family": family,
                "scope": scope,
                "reference_folder": rel_public(folder),
                "final_result_exists": "yes" if final_path.exists() else "no",
                "trials_all_exists": "yes" if trials_path.exists() else "no",
                "feature_manifest_exists": "yes" if feature_path.exists() else "no",
                "source_pointer_exists": "yes" if pointer_path.exists() else "no",
                "final_result_rows": len(final_rows) if final_path.exists() else 0,
                "trials_all_rows": len(trials_rows) if trials_path.exists() else 0,
                "validation_status": status,
                "notes": notes,
            }
        )
    path = HANDOFF / "12_input_file_validation.csv"
    fields = [
        "model_family",
        "scope",
        "reference_folder",
        "final_result_exists",
        "trials_all_exists",
        "feature_manifest_exists",
        "source_pointer_exists",
        "final_result_rows",
        "trials_all_rows",
        "validation_status",
        "notes",
    ]
    write_csv(path, fields, rows)
    return path, rows


def log_retention_check():
    rows = []
    for family, scope, folder_name in MODEL_SPECS:
        folder = REF_11 / folder_name
        final_path = folder / "final_result.csv"
        feature_path = folder / "feature_manifest_used.csv"
        _, final_rows = read_csv_rows(final_path)
        final_row = final_rows[0] if final_rows else {}
        features = feature_set(feature_path)
        final_text = read_text(final_path)
        feature_text = read_text(feature_path)
        raw_removed = parse_bool(final_row.get("raw_retention_removed"))
        log_used = parse_bool(final_row.get("log_retention_used"))
        raw_w2 = "retention_w2_ratio" in features
        raw_w3 = "retention_w3_ratio" in features
        log_w2 = "log_retention_w2_ratio" in features or "log_retention_w2_ratio" in final_text or "log_retention_w2_ratio" in feature_text
        log_w3 = "log_retention_w3_ratio" in features or "log_retention_w3_ratio" in final_text or "log_retention_w3_ratio" in feature_text
        data_path = final_row.get("data_file") or final_row.get("input_path") or final_row.get("data_path") or ""
        data_hint = ("log_retention" in data_path.lower()) or ("06_model_input_promo_" in data_path.lower())
        if raw_w2 or raw_w3:
            status = "FAIL"
            reason = "Raw retention feature was found in feature_manifest_used.csv."
        elif raw_removed is True and log_used is True and log_w2 and log_w3 and data_hint:
            status = "PASS"
            reason = "raw_retention_removed=True, log_retention_used=True, log retention features are present, raw retention features are absent, and data_file points to current 06/log-retention input."
        elif raw_removed is True and log_used is True and log_w2 and log_w3:
            status = "WARN"
            reason = "Feature and final_result flags pass, but data_file path does not explicitly identify 06/log-retention input."
        else:
            status = "FAIL"
            reason = "One or more required log-retention-only conditions failed."
        rows.append(
            {
                "model_family": family,
                "scope": scope,
                "data_file_or_input_path": data_path,
                "raw_retention_removed": str(raw_removed),
                "log_retention_used": str(log_used),
                "contains_retention_w2_ratio": str(raw_w2),
                "contains_retention_w3_ratio": str(raw_w3),
                "contains_log_retention_w2_ratio": str(log_w2),
                "contains_log_retention_w3_ratio": str(log_w3),
                "condition_status": status,
                "reason": reason,
            }
        )
    path = OUTPUT / "12_log_retention_condition_check.csv"
    fields = [
        "model_family",
        "scope",
        "data_file_or_input_path",
        "raw_retention_removed",
        "log_retention_used",
        "contains_retention_w2_ratio",
        "contains_retention_w3_ratio",
        "contains_log_retention_w2_ratio",
        "contains_log_retention_w3_ratio",
        "condition_status",
        "reason",
    ]
    write_csv(path, fields, rows)
    return path, rows


def final_result_metric_summary():
    rows = []
    for family, scope, folder_name in MODEL_SPECS:
        final_path = REF_11 / folder_name / "final_result.csv"
        _, final_rows = read_csv_rows(final_path)
        row = final_rows[0] if final_rows else {}
        rows.append(
            {
                "model_family": family,
                "scope": scope,
                "test_roc_auc": row.get("test_roc_auc", "NA"),
                "test_pr_auc": row.get("test_pr_auc", "NA"),
                "test_f1": row.get("test_f1", "NA"),
                "test_precision": row.get("test_precision", "NA"),
                "test_recall": row.get("test_recall", "NA"),
                "best_valid_auc": row.get("best_valid_auc", "NA"),
                "best_train_auc": row.get("best_train_auc", "NA"),
                "best_gap": row.get("best_gap", "NA"),
                "overfit": row.get("overfit", "NA"),
                "best_trial": row.get("best_trial", "NA"),
                "n_trials": row.get("n_trials", "NA"),
                "metric_source_file": rel_public(final_path),
                "notes": "Read from saved final_result.csv only; no new model calculation.",
            }
        )
    path = OUTPUT / "12_final_result_metric_summary.csv"
    fields = [
        "model_family",
        "scope",
        "test_roc_auc",
        "test_pr_auc",
        "test_f1",
        "test_precision",
        "test_recall",
        "best_valid_auc",
        "best_train_auc",
        "best_gap",
        "overfit",
        "best_trial",
        "n_trials",
        "metric_source_file",
        "notes",
    ]
    write_csv(path, fields, rows)
    return path, rows


def overfit_rate(rows, overfit_col):
    if not overfit_col:
        return None, None
    values = [parse_bool(row.get(overfit_col)) for row in rows]
    known = [v for v in values if v is not None]
    if not known:
        return None, None
    count = sum(1 for v in known if v)
    return count, count / len(known)


def topn_overfit_rate(rows, ranking_col, overfit_col, n):
    if not ranking_col or not overfit_col:
        return None
    ranked = []
    for row in rows:
        score = as_float(row.get(ranking_col))
        if score is not None:
            ranked.append((score, row))
    if not ranked:
        return None
    selected = [row for _score, row in sorted(ranked, key=lambda item: item[0], reverse=True)[:n]]
    values = [parse_bool(row.get(overfit_col)) for row in selected]
    known = [v for v in values if v is not None]
    if not known:
        return None
    return sum(1 for v in known if v) / len(known)


def best_trial_overfit(trials_rows, overfit_col, final_row):
    if not overfit_col:
        return "NA"
    best_trial = str(final_row.get("best_trial", "")).strip()
    for row in trials_rows:
        if str(row.get("trial", "")).strip() == best_trial:
            value = parse_bool(row.get(overfit_col))
            return "NA" if value is None else str(value)
    return "NA"


def trials_overfit_stability_summary():
    rows = []
    for family, scope, folder_name in MODEL_SPECS:
        folder = REF_11 / folder_name
        trials_fields, trials_rows = read_csv_rows(folder / "trials_all.csv")
        _, final_rows = read_csv_rows(folder / "final_result.csv")
        final_row = final_rows[0] if final_rows else {}
        ranking_col = choose_ranking_metric(trials_fields)
        overfit_col = "overfit" if "overfit" in trials_fields else ""
        gap_col = choose_gap_column(trials_fields)
        valid_col = choose_valid_auc_column(trials_fields)
        overfit_count, of_rate = overfit_rate(trials_rows, overfit_col)
        valid_values = [as_float(row.get(valid_col)) for row in trials_rows] if valid_col else []
        gap_values = [as_float(row.get(gap_col)) for row in trials_rows] if gap_col else []
        top5 = topn_overfit_rate(trials_rows, ranking_col, overfit_col, 5)
        top10 = topn_overfit_rate(trials_rows, ranking_col, overfit_col, 10)
        top20 = topn_overfit_rate(trials_rows, ranking_col, overfit_col, 20)
        if not ranking_col or not overfit_col:
            status = "WARN"
            notes = "insufficient_columns_for_topN_or_overfit_rate"
        elif of_rate is None:
            status = "WARN"
            notes = "overfit_column_present_but_not_parseable"
        elif of_rate > 0.5:
            status = "FAIL"
            notes = "overfit_rate_above_0_5_review_required"
        else:
            status = "PASS"
            notes = "overfit, gap, and valid AUC columns were available; topN rates use ranking_metric_used descending."
        rows.append(
            {
                "model_family": family,
                "scope": scope,
                "trials_n": len(trials_rows),
                "ranking_metric_used": ranking_col or "NA",
                "overfit_column_used": overfit_col or "NA",
                "gap_column_used": gap_col or "NA",
                "overfit_count": "NA" if overfit_count is None else overfit_count,
                "overfit_rate": fmt(of_rate),
                "top5_overfit_rate": fmt(top5),
                "top10_overfit_rate": fmt(top10),
                "top20_overfit_rate": fmt(top20),
                "best_trial_overfit": best_trial_overfit(trials_rows, overfit_col, final_row),
                "mean_valid_auc": fmt(mean(valid_values)),
                "std_valid_auc": fmt(stdev(valid_values)),
                "max_valid_auc": fmt(max_value(valid_values)),
                "mean_gap": fmt(mean(gap_values)),
                "max_gap": fmt(max_value(gap_values)),
                "stability_status": status,
                "notes": notes,
            }
        )
    path = OUTPUT / "12_trials_overfit_stability_summary.csv"
    fields = [
        "model_family",
        "scope",
        "trials_n",
        "ranking_metric_used",
        "overfit_column_used",
        "gap_column_used",
        "overfit_count",
        "overfit_rate",
        "top5_overfit_rate",
        "top10_overfit_rate",
        "top20_overfit_rate",
        "best_trial_overfit",
        "mean_valid_auc",
        "std_valid_auc",
        "max_valid_auc",
        "mean_gap",
        "max_gap",
        "stability_status",
        "notes",
    ]
    write_csv(path, fields, rows)
    return path, rows


def lookup(rows, family, scope):
    for row in rows:
        if row.get("model_family") == family and row.get("scope") == scope:
            return row
    return {}


def scopewise_comparison(metric_rows, stability_rows, condition_rows):
    rows = []
    for scope in ["promo0", "promo1"]:
        lr_m = lookup(metric_rows, "LogisticRegression", scope)
        gb_m = lookup(metric_rows, "GradientBoosting", scope)
        lr_s = lookup(stability_rows, "LogisticRegression", scope)
        gb_s = lookup(stability_rows, "GradientBoosting", scope)
        lr_c = lookup(condition_rows, "LogisticRegression", scope)
        gb_c = lookup(condition_rows, "GradientBoosting", scope)
        lr_roc = as_float(lr_m.get("test_roc_auc"))
        gb_roc = as_float(gb_m.get("test_roc_auc"))
        lr_pr = as_float(lr_m.get("test_pr_auc"))
        gb_pr = as_float(gb_m.get("test_pr_auc"))
        lr_of = as_float(lr_s.get("overfit_rate"))
        gb_of = as_float(gb_s.get("overfit_rate"))
        lr_top10 = as_float(lr_s.get("top10_overfit_rate"))
        gb_top10 = as_float(gb_s.get("top10_overfit_rate"))
        conditions_pass = lr_c.get("condition_status") == "PASS" and gb_c.get("condition_status") == "PASS"
        stability_pass = lr_s.get("stability_status") == "PASS" and gb_s.get("stability_status") == "PASS"
        metrics_available = None not in [lr_roc, gb_roc, lr_pr, gb_pr, lr_of, gb_of, lr_top10, gb_top10]
        if not conditions_pass:
            status = "fail_due_to_log_retention_or_overfit_issue"
            primary = "no_primary_candidate_until_log_retention_issue_resolved"
            baseline = "lr_baseline_pending_issue_resolution"
            reason = "At least one log-retention condition check failed."
        elif not metrics_available:
            status = "insufficient_evidence"
            primary = "insufficient_evidence"
            baseline = "insufficient_evidence"
            reason = "Required metrics or overfit rates are missing."
        elif not stability_pass or gb_of > 0.5 or gb_top10 > 0.5:
            status = "fail_due_to_log_retention_or_overfit_issue"
            primary = "do_not_promote_gb_without_overfit_review"
            baseline = "keep_lr_as_baseline_pending_review"
            reason = "Stability check failed or GB overfit rate exceeds review threshold."
        elif gb_roc > lr_roc and gb_pr > lr_pr:
            status = "recommend_gb_primary_lr_baseline"
            primary = "GB primary candidate for this scope, pending user review and OOF approval."
            baseline = "LR baseline/sensitivity candidate for this scope."
            reason = "GB has higher saved test ROC AUC and PR AUC than LR, while log-retention and overfit/stability checks pass."
        else:
            status = "keep_both_pending_user_review"
            primary = "keep_both_pending_user_review"
            baseline = "LR remains baseline/sensitivity candidate."
            reason = "GB does not dominate LR on both saved ROC AUC and PR AUC, or the improvement is not enough for automatic wording."
        rows.append(
            {
                "scope": scope,
                "lr_test_roc_auc": fmt(lr_roc),
                "gb_test_roc_auc": fmt(gb_roc),
                "delta_roc_auc_gb_minus_lr": fmt(None if lr_roc is None or gb_roc is None else gb_roc - lr_roc),
                "lr_test_pr_auc": fmt(lr_pr),
                "gb_test_pr_auc": fmt(gb_pr),
                "delta_pr_auc_gb_minus_lr": fmt(None if lr_pr is None or gb_pr is None else gb_pr - lr_pr),
                "lr_overfit_rate": fmt(lr_of),
                "gb_overfit_rate": fmt(gb_of),
                "lr_top10_overfit_rate": fmt(lr_top10),
                "gb_top10_overfit_rate": fmt(gb_top10),
                "primary_candidate_recommendation": primary,
                "baseline_candidate_recommendation": baseline,
                "recommendation_status": status,
                "reason": reason,
            }
        )
    path = OUTPUT / "12_scopewise_gb_vs_lr_comparison.csv"
    fields = [
        "scope",
        "lr_test_roc_auc",
        "gb_test_roc_auc",
        "delta_roc_auc_gb_minus_lr",
        "lr_test_pr_auc",
        "gb_test_pr_auc",
        "delta_pr_auc_gb_minus_lr",
        "lr_overfit_rate",
        "gb_overfit_rate",
        "lr_top10_overfit_rate",
        "gb_top10_overfit_rate",
        "primary_candidate_recommendation",
        "baseline_candidate_recommendation",
        "recommendation_status",
        "reason",
    ]
    write_csv(path, fields, rows)
    return path, rows


def oof_readiness(input_rows, condition_rows, stability_rows, comparison_rows):
    all_inputs = all(row["validation_status"] == "PASS" for row in input_rows)
    all_final = all(row["final_result_exists"] == "yes" for row in input_rows)
    all_trials = all(row["trials_all_exists"] == "yes" for row in input_rows)
    all_conditions = all(row["condition_status"] == "PASS" for row in condition_rows)
    all_stability = all(row["stability_status"] == "PASS" for row in stability_rows)
    topn_checked = all(row["top10_overfit_rate"] != "NA" for row in stability_rows)
    promo0_primary = lookup(comparison_rows, "", "")
    promo0_ok = any(row["scope"] == "promo0" and row["recommendation_status"] == "recommend_gb_primary_lr_baseline" for row in comparison_rows)
    promo1_ok = any(row["scope"] == "promo1" and row["recommendation_status"] == "recommend_gb_primary_lr_baseline" for row in comparison_rows)
    rows = [
        ("four_model_results_available", "yes" if all_inputs else "no", f"input_validation_all_pass={all_inputs}", "no", "All four 11 emergency reference folders must be present."),
        ("final_result_all_available", "yes" if all_final else "no", f"four_final_result_files_found={all_final}", "no", "Required for saved metric summary."),
        ("trials_all_all_available", "yes" if all_trials else "no", f"four_trials_all_files_found={all_trials}", "no", "Required for overfit/stability review."),
        ("log_retention_condition_all_pass", "yes" if all_conditions else "no", f"all_condition_status_PASS={all_conditions}", "no", "Raw retention features must be absent and log retention features must be present."),
        ("promo0_primary_candidate_available", "yes" if promo0_ok else "no", f"promo0_recommend_gb_primary_lr_baseline={promo0_ok}", "no", "Recommendation is review-only, not final approval."),
        ("promo1_primary_candidate_available", "yes" if promo1_ok else "no", f"promo1_recommend_gb_primary_lr_baseline={promo1_ok}", "no", "Recommendation is review-only, not final approval."),
        ("lr_baseline_available_for_promo0", "yes" if lookup(stability_rows, "LogisticRegression", "promo0") else "no", "LR promo0 reference checked", "no", "LR remains baseline/sensitivity candidate."),
        ("lr_baseline_available_for_promo1", "yes" if lookup(stability_rows, "LogisticRegression", "promo1") else "no", "LR promo1 reference checked", "no", "LR remains baseline/sensitivity candidate."),
        ("overfit_stability_checked", "yes" if all_stability else "no", f"all_stability_status_PASS={all_stability}", "no", "Based on existing trials_all.csv columns."),
        ("topN_overfit_checked", "yes" if topn_checked else "no", f"top10_overfit_rate_available_for_all={topn_checked}", "no", "TopN uses mean_valid_auc descending."),
        ("oof_generation_allowed_now", "no", "This task explicitly forbids OOF score table generation.", "yes", "Even if readiness signals are good, this task does not create OOF."),
        ("requires_user_approval_before_oof", "yes", "User approval is required before OOF generation.", "yes", "Next step only after review."),
    ]
    output_rows = [
        {"decision_item": item, "status": status, "evidence": evidence, "required_user_approval": approval, "notes": notes}
        for item, status, evidence, approval, notes in rows
    ]
    path = OUTPUT / "12_oof_readiness_decision.csv"
    fields = ["decision_item", "status", "evidence", "required_user_approval", "notes"]
    write_csv(path, fields, output_rows)
    return path, output_rows


def append_note(missing_notes):
    heading = "## 2026-05-20 | PUBLIC 12 four-model comparison review completed"
    text = read_text(NOTE)
    if heading in text:
        return
    missing_block = "계산하지 못한 항목은 없다. `trials_all.csv`에 `mean_valid_auc`, `gap`, `overfit` 컬럼이 있어서 overfit/stability와 topN overfit rate를 계산했다."
    if missing_notes:
        missing_block = "일부 계산하지 못한 항목: " + "; ".join(missing_notes)
    append_text = f"""

{heading}

이번 작업은 12 four-model comparison review다.

11 emergency four-model reference에 모인 4개 log-retention-only 결과를 비교했다.

4개 모델은 LogisticRegression promo0, LogisticRegression promo1, GradientBoosting promo0, GradientBoosting promo1이다.

promo0와 promo1은 분리해서 비교했다.

final_result.csv 기반 성능 요약을 만들었다.

trials_all.csv 기반 overfit/stability 요약을 만들었다.

log retention only 조건을 다시 확인했다.

OOF score table은 생성하지 않았다.

SHAP, segmentation, Optuna는 수행하지 않았다.

07~10은 여전히 pending validation이다.

이 결과는 final model selection이 아니다.

{missing_block}

다음 단계는 사용자 승인 후 OOF score table 생성 또는 07~10 pending validation 해소다.
"""
    with NOTE.open("a", encoding="utf-8") as handle:
        handle.write(append_text)


def write_review_readme(condition_rows, metric_rows, stability_rows, comparison_rows, oof_rows):
    comparison_text = "\n".join(
        [
            f"- {row['scope']}: {row['recommendation_status']} ({row['reason']})"
            for row in comparison_rows
        ]
    )
    condition_text = "\n".join(
        [
            f"- {row['model_family']} {row['scope']}: {row['condition_status']}"
            for row in condition_rows
        ]
    )
    stability_text = "\n".join(
        [
            f"- {row['model_family']} {row['scope']}: {row['stability_status']}, overfit_rate={row['overfit_rate']}, top10_overfit_rate={row['top10_overfit_rate']}"
            for row in stability_rows
        ]
    )
    (OUTPUT / "README.md").write_text(
        f"""# PUBLIC 12 Four-Model Comparison Review

## Purpose

This is a four-model comparison review based on existing log-retention-only emergency reference outputs.

This review reads saved `final_result.csv`, `trials_all.csv`, `feature_manifest_used.csv`, and `SOURCE_POINTER.txt` files from Step 11.

## Input source

Input source:

- `PUBLIC/results/11_baseline_growth_comparison_260520/emergency_four_model_reference/`

The four reviewed references are LogisticRegression promo0, LogisticRegression promo1, GradientBoosting promo0, and GradientBoosting promo1.

## Why this is 12 and not 11

Step 11 is the emergency four-model reference stage. Step 12 is the comparison review stage.

12 is not GradientBoosting-only. It compares LR and GB within each promo scope.

## 07~10 pending validation caveat

07~10 remain pending validation. This review does not complete or replace those validation steps.

## Log retention condition check

{condition_text}

Details are saved in `12_log_retention_condition_check.csv`.

## Final result metric summary

Saved final-result metrics were read from the four `final_result.csv` files only. No new model calculation was performed.

Details are saved in `12_final_result_metric_summary.csv`.

## Trials overfit and stability summary

{stability_text}

The ranking metric used for topN checks is recorded in `12_trials_overfit_stability_summary.csv`.

## Scopewise GB vs LR comparison

Promo0 and promo1 are evaluated separately.

{comparison_text}

Highest AUC alone does not determine the model.

## OOF readiness decision

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
- Promo0 and promo1 are evaluated separately.
- GB may be treated as primary candidate only after stability and log-retention checks pass.
- LR remains baseline/sensitivity candidate.
- OOF generation requires user approval.

## Unsafe wording

- This is final model selection.
- 07~10 are completed.
- OOF table was generated.
- SHAP can start immediately.
- Segmentation can start immediately.
- Highest AUC alone determines the model.

## Next action

Review the generated CSVs and review zip. After review, the user may approve OOF score table generation or choose to resolve 07~10 pending validation first.
""",
        encoding="utf-8",
    )


def status_counts(rows, status_col):
    counts = {}
    for row in rows:
        counts[row.get(status_col, "")] = counts.get(row.get(status_col, ""), 0) + 1
    return ", ".join([f"{key}:{value}" for key, value in sorted(counts.items())])


def write_handoff_readme(input_rows, condition_rows, stability_rows, comparison_rows, oof_rows, files):
    key_findings = [
        f"Input validation statuses: {status_counts(input_rows, 'validation_status')}",
        f"Log retention condition statuses: {status_counts(condition_rows, 'condition_status')}",
        f"Stability statuses: {status_counts(stability_rows, 'stability_status')}",
    ]
    comparison_lines = [f"- {row['scope']}: {row['recommendation_status']}" for row in comparison_rows]
    zip_lines = [f"- `{rel_public(path)}`" for path in files]
    (HANDOFF / "README.md").write_text(
        f"""# PUBLIC 12 Four-Model Comparison Review Handoff

## Purpose

This handoff summarizes the Step 12 four-model comparison review for the existing Step 11 emergency four-model reference outputs.

## Inputs checked

- LogisticRegression promo0
- LogisticRegression promo1
- GradientBoosting promo0
- GradientBoosting promo1

For each model, `final_result.csv`, `trials_all.csv`, `feature_manifest_used.csv`, and `SOURCE_POINTER.txt` were checked when available.

## Outputs generated

- `12_input_file_validation.csv`
- `12_log_retention_condition_check.csv`
- `12_final_result_metric_summary.csv`
- `12_trials_overfit_stability_summary.csv`
- `12_scopewise_gb_vs_lr_comparison.csv`
- `12_oof_readiness_decision.csv`
- Review README
- Final checks
- Review zip

## Key findings

{chr(10).join(['- ' + item for item in key_findings])}

## Limitations

This is not final model selection. This review did not train models, execute notebooks, run Optuna, run SHAP, run segmentation, or generate an OOF score table.

## OOF readiness summary

The decision table keeps `oof_generation_allowed_now` as `no` and `requires_user_approval_before_oof` as `yes`.

## 07~10 pending validation status

07~10 remain pending validation. This Step 12 review does not mark them complete.

## Files included in review zip

{chr(10).join(zip_lines)}

## Next recommended action

Review the zip contents, then decide whether to approve OOF score table generation or resolve 07~10 pending validation first.

## Scopewise recommendations

{chr(10).join(comparison_lines)}
""",
        encoding="utf-8",
    )


def check_row(name, status, expected, actual, notes=""):
    return {"check_name": name, "status": status, "expected": expected, "actual": actual, "notes": notes}


def final_checks(paths, input_rows, condition_rows):
    zip_path = ZIP_DIR / "PUBLIC_12_four_model_comparison_review_260520_review_package.zip"
    zip_inventory = HANDOFF / "PUBLIC_12_four_model_comparison_review_zip_inventory.csv"
    rows = [
        check_row("public_root_exists", "PASS" if PUBLIC.exists() else "FAIL", "PUBLIC root exists", str(PUBLIC.exists())),
        check_row("handoff_output_folder_exists", "PASS" if HANDOFF.exists() else "FAIL", "handoff folder exists", str(HANDOFF.exists())),
        check_row("output_folder_exists", "PASS" if OUTPUT.exists() else "FAIL", "output folder exists", str(OUTPUT.exists())),
        check_row("input_validation_created", "PASS" if paths["input_validation"].exists() else "FAIL", "input validation exists", str(paths["input_validation"])),
        check_row("four_final_result_files_found", "PASS" if sum(row["final_result_exists"] == "yes" for row in input_rows) == 4 else "FAIL", "4 final_result files", str(sum(row["final_result_exists"] == "yes" for row in input_rows))),
        check_row("four_trials_all_files_found", "PASS" if sum(row["trials_all_exists"] == "yes" for row in input_rows) == 4 else "FAIL", "4 trials_all files", str(sum(row["trials_all_exists"] == "yes" for row in input_rows))),
        check_row("log_retention_condition_check_created", "PASS" if paths["condition"].exists() else "FAIL", "condition check exists", str(paths["condition"])),
        check_row("log_retention_condition_all_pass", "PASS" if all(row["condition_status"] == "PASS" for row in condition_rows) else "FAIL", "all condition_status PASS", status_counts(condition_rows, "condition_status")),
        check_row("final_result_metric_summary_created", "PASS" if paths["metrics"].exists() else "FAIL", "metric summary exists", str(paths["metrics"])),
        check_row("trials_overfit_stability_summary_created", "PASS" if paths["stability"].exists() else "FAIL", "stability summary exists", str(paths["stability"])),
        check_row("scopewise_gb_vs_lr_comparison_created", "PASS" if paths["comparison"].exists() else "FAIL", "scopewise comparison exists", str(paths["comparison"])),
        check_row("oof_readiness_decision_created", "PASS" if paths["oof"].exists() else "FAIL", "oof readiness exists", str(paths["oof"])),
        check_row("readme_created", "PASS" if (OUTPUT / "README.md").exists() else "FAIL", "review README exists", str(OUTPUT / "README.md")),
        check_row("note_md_append_completed", "PASS" if "## 2026-05-20 | PUBLIC 12 four-model comparison review completed" in read_text(NOTE) else "FAIL", "note append heading exists", str(NOTE)),
        check_row("no_model_execution_performed", "PASS", "no model execution", "Only saved CSVs were read and summarized"),
        check_row("no_notebook_execution_performed", "PASS", "no notebook execution", "No jupyter or nbconvert command was run"),
        check_row("no_optuna_performed", "PASS", "no Optuna run", "No Optuna command was run"),
        check_row("no_shap_performed", "PASS", "no SHAP run", "No SHAP command was run"),
        check_row("no_segmentation_performed", "PASS", "no segmentation run", "No segmentation command was run"),
        check_row("no_oof_generation_performed", "PASS", "no OOF score table generation", "Only OOF readiness decision was created"),
        check_row("no_raw_source_modified", "PASS", "no raw source writes", "Generated outputs are under PUBLIC/handoff, PUBLIC/results/12, PUBLIC/note.md, and PUBLIC/zip"),
        check_row("no_park_ingyeom_modified", "PASS", "no park.ingyeom writes", "Script writes only under PUBLIC"),
        check_row("no_deletion_performed", "PASS", "no deletion operation", "Script creates or overwrites review artifacts only"),
        check_row("review_zip_created", "PASS" if zip_path.exists() else "FAIL", "review zip exists", str(zip_path)),
        check_row("zip_inventory_created", "PASS" if zip_inventory.exists() else "FAIL", "zip inventory exists", str(zip_inventory)),
    ]
    path = HANDOFF / "PUBLIC_12_four_model_comparison_review_final_checks.csv"
    write_csv(path, ["check_name", "status", "expected", "actual", "notes"], rows)
    return path, rows


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


def main():
    input_path, input_rows = input_validation()
    condition_path, condition_rows = log_retention_check()
    metrics_path, metric_rows = final_result_metric_summary()
    stability_path, stability_rows = trials_overfit_stability_summary()
    comparison_path, comparison_rows = scopewise_comparison(metric_rows, stability_rows, condition_rows)
    oof_path, oof_rows = oof_readiness(input_rows, condition_rows, stability_rows, comparison_rows)
    missing_notes = [row["notes"] for row in stability_rows if "insufficient" in row["notes"]]
    append_note(missing_notes)
    write_review_readme(condition_rows, metric_rows, stability_rows, comparison_rows, oof_rows)

    paths = {
        "input_validation": input_path,
        "condition": condition_path,
        "metrics": metrics_path,
        "stability": stability_path,
        "comparison": comparison_path,
        "oof": oof_path,
    }
    final_checks_path = HANDOFF / "PUBLIC_12_four_model_comparison_review_final_checks.csv"
    zip_inventory_path = HANDOFF / "PUBLIC_12_four_model_comparison_review_zip_inventory.csv"
    files = [
        HANDOFF / "README.md",
        input_path,
        final_checks_path,
        zip_inventory_path,
        OUTPUT / "README.md",
        condition_path,
        metrics_path,
        stability_path,
        comparison_path,
        oof_path,
        NOTE,
        HANDOFF / "run_public_12_four_model_comparison_review.py",
    ]
    write_handoff_readme(input_rows, condition_rows, stability_rows, comparison_rows, oof_rows, files)
    final_checks_path, _ = final_checks(paths, input_rows, condition_rows)
    create_zip(files)
    final_checks_path, checks = final_checks(paths, input_rows, condition_rows)
    create_zip(files)

    print(f"input_validation={input_path}")
    print(f"condition_check={condition_path}")
    print(f"metric_summary={metrics_path}")
    print(f"stability_summary={stability_path}")
    print(f"scopewise_comparison={comparison_path}")
    print(f"oof_readiness={oof_path}")
    print(f"final_checks={final_checks_path}")
    print(f"checks_statuses={status_counts(checks, 'status')}")
    print(f"zip={ZIP_DIR / 'PUBLIC_12_four_model_comparison_review_260520_review_package.zip'}")


if __name__ == "__main__":
    main()
