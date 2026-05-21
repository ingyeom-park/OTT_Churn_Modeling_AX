import csv
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

REPO = Path(r"C:\Code\ott-churn-prediction")
PUBLIC = REPO / "PUBLIC"
HANDOFF = PUBLIC / "handoff" / "PUBLIC_11_12_emergency_model_restructure_260520"
ZIP_DIR = PUBLIC / "zip"
RESULTS_11 = PUBLIC / "results" / "11_baseline_growth_comparison_260520"
REF_11 = RESULTS_11 / "emergency_four_model_reference"
RESULTS_12 = PUBLIC / "results" / "12_model_family_comparison_260520"
SUMMARY_12 = RESULTS_12 / "four_model_comparison_summary"
NB_11 = PUBLIC / "notebooks" / "11_baseline_growth_comparison_260520"
NB_12 = PUBLIC / "notebooks" / "12_model_family_comparison_260520"
NOTE = PUBLIC / "note.md"
COPIED_AT = datetime.now().astimezone().isoformat(timespec="seconds")

for directory in [HANDOFF, ZIP_DIR, RESULTS_11, REF_11, RESULTS_12, SUMMARY_12, NB_11, NB_12]:
    directory.mkdir(parents=True, exist_ok=True)


def rel_public(path: Path) -> str:
    return "PUBLIC\\" + str(path.relative_to(PUBLIC)).replace("/", "\\")


def write_csv(path: Path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def parse_csv_first_row(path: Path):
    if not path.exists():
        return [], {}
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                return reader.fieldnames or [], next(reader, {}) or {}
        except UnicodeDecodeError:
            continue
        except StopIteration:
            return [], {}
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], next(reader, {}) or {}


def truthy(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def infer_top_level(rel: Path) -> str:
    return rel.parts[0] if rel.parts else "PUBLIC_ROOT"


def infer_role(path: Path, is_dir: bool) -> str:
    rel = path.relative_to(PUBLIC)
    parts = rel.parts
    name = path.name.lower()
    text = str(rel).lower()
    if is_dir:
        if parts and parts[0] == "results":
            return "results_directory"
        if parts and parts[0] == "notebooks":
            return "notebook_directory"
        if parts and parts[0] == "handoff":
            return "handoff_directory"
        if parts and parts[0] == "data":
            return "data_directory"
        if parts and parts[0] == "zip":
            return "zip_directory"
        return "directory"
    if name == "final_result.csv":
        return "model_final_result"
    if name == "trials_all.csv":
        return "model_trials_all"
    if name == "feature_manifest_used.csv":
        return "model_feature_manifest"
    if name == "readme.md":
        return "readme"
    if name == "note.md":
        return "project_note"
    if name.endswith(".ipynb"):
        return "notebook"
    if name.endswith(".csv"):
        return "csv_artifact"
    if name.endswith(".zip"):
        return "review_or_archive_zip"
    if "source_pointer" in text:
        return "source_pointer"
    return "file"


def infer_family(row, directory: Path) -> str:
    text = " ".join([str(row.get("model", "")), directory.name, str(directory)]).lower()
    if "logistic" in text or re.search(r"(^|[_-])lr([_-]|$)", text):
        return "LogisticRegression"
    if "gradientboosting" in text or "gradient_boosting" in text or "gb_" in text:
        return "GradientBoosting"
    return "unknown"


def infer_scope(row, directory: Path) -> str:
    promo = str(row.get("promo", "")).strip()
    if promo == "0":
        return "promo0"
    if promo == "1":
        return "promo1"
    text = str(directory).lower()
    if "promo_0" in text or "promo0" in text:
        return "promo0"
    if "promo_1" in text or "promo1" in text:
        return "promo1"
    return "unknown"


def feature_set_from_manifest(path: Path):
    features = set()
    if not path.exists():
        return features
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames and "feature_name" in reader.fieldnames:
                    for row in reader:
                        value = (row.get("feature_name") or "").strip()
                        if value:
                            features.add(value)
                    return features
        except UnicodeDecodeError:
            continue
    return features


def inventory_before():
    rows = []
    for path in sorted(PUBLIC.rglob("*"), key=lambda item: str(item).lower()):
        rel = path.relative_to(PUBLIC)
        is_dir = path.is_dir()
        try:
            stat = path.stat()
            size = "" if is_dir else stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
            notes = ""
        except OSError as exc:
            size = ""
            mtime = ""
            notes = f"stat_failed: {exc}"
        rows.append(
            {
                "relative_path": str(rel).replace("/", "\\"),
                "item_type": "directory" if is_dir else "file",
                "size_bytes": size,
                "modified_time": mtime,
                "top_level_area": infer_top_level(rel),
                "inferred_role": infer_role(path, is_dir),
                "notes": notes,
            }
        )
    path = HANDOFF / "PUBLIC_inventory_before_11_12_restructure.csv"
    write_csv(
        path,
        ["relative_path", "item_type", "size_bytes", "modified_time", "top_level_area", "inferred_role", "notes"],
        rows,
    )
    return path


def detect_candidates():
    candidate_dirs = set()
    for file_name in ("final_result.csv", "trials_all.csv"):
        for path in PUBLIC.rglob(file_name):
            if REF_11 in path.parents:
                continue
            candidate_dirs.add(path.parent)

    rows = []
    selected = {}
    for directory in sorted(candidate_dirs, key=lambda item: str(item).lower()):
        final_path = directory / "final_result.csv"
        trials_path = directory / "trials_all.csv"
        has_final = final_path.exists()
        has_trials = trials_path.exists()
        _, row = parse_csv_first_row(final_path)
        family = infer_family(row, directory)
        scope = infer_scope(row, directory)
        features = feature_set_from_manifest(directory / "feature_manifest_used.csv")
        final_text = read_text(final_path)
        feature_text = read_text(directory / "feature_manifest_used.csv")
        raw_removed = truthy(row.get("raw_retention_removed", ""))
        log_used = truthy(row.get("log_retention_used", ""))
        raw_w2 = "retention_w2_ratio" in features
        raw_w3 = "retention_w3_ratio" in features
        log_w2 = "log_retention_w2_ratio" in features or "log_retention_w2_ratio" in final_text or "log_retention_w2_ratio" in feature_text
        log_w3 = "log_retention_w3_ratio" in features or "log_retention_w3_ratio" in final_text or "log_retention_w3_ratio" in feature_text
        is_selected = False
        if not (has_final and has_trials):
            status = "rejected_missing_required_files"
            reason = "final_result.csv and trials_all.csv are both required."
        elif raw_w2 or raw_w3 or not raw_removed or not log_used:
            status = "rejected_pre_log_retention"
            reason = "Raw retention feature or missing log-retention flags were detected."
        elif raw_removed and log_used and log_w2 and log_w3 and family in {"LogisticRegression", "GradientBoosting"} and scope in {"promo0", "promo1"}:
            status = "selected_log_retention_current"
            reason = "final_result.csv has raw_retention_removed=True and log_retention_used=True; feature_manifest_used.csv contains log_retention_w2_ratio and log_retention_w3_ratio and does not contain raw retention_w2_ratio or retention_w3_ratio."
            is_selected = True
        else:
            status = "unknown_needs_user_review"
            reason = "Required files exist, but log-retention-only status could not be fully confirmed from final_result.csv and feature manifest."

        rows.append(
            {
                "candidate_result_dir": str(directory.relative_to(PUBLIC)).replace("/", "\\"),
                "has_final_result_csv": "yes" if has_final else "no",
                "has_trials_all_csv": "yes" if has_trials else "no",
                "inferred_model_family": family,
                "inferred_scope": scope,
                "data_file_or_input_path": row.get("data_file") or row.get("input_path") or row.get("data_path") or "",
                "raw_retention_removed": str(raw_removed),
                "log_retention_used": str(log_used),
                "contains_retention_w2_ratio": str(raw_w2),
                "contains_retention_w3_ratio": str(raw_w3),
                "contains_log_retention_w2_ratio": str(log_w2),
                "contains_log_retention_w3_ratio": str(log_w3),
                "candidate_status": status,
                "reason": reason,
                "selected_for_11_emergency_reference": "yes" if is_selected else "no",
            }
        )
        if is_selected:
            selected[(family, scope)] = directory

    path = HANDOFF / "PUBLIC_detected_model_result_candidates.csv"
    fields = [
        "candidate_result_dir",
        "has_final_result_csv",
        "has_trials_all_csv",
        "inferred_model_family",
        "inferred_scope",
        "data_file_or_input_path",
        "raw_retention_removed",
        "log_retention_used",
        "contains_retention_w2_ratio",
        "contains_retention_w3_ratio",
        "contains_log_retention_w2_ratio",
        "contains_log_retention_w3_ratio",
        "candidate_status",
        "reason",
        "selected_for_11_emergency_reference",
    ]
    write_csv(path, fields, rows)
    return path, rows, selected


ROLE_MAP = {
    ("LogisticRegression", "promo0"): "logistic_regression_promo0",
    ("LogisticRegression", "promo1"): "logistic_regression_promo1",
    ("GradientBoosting", "promo0"): "gradient_boosting_promo0",
    ("GradientBoosting", "promo1"): "gradient_boosting_promo1",
}


def copy_reference(selected):
    records = []
    for key, folder_name in ROLE_MAP.items():
        target = REF_11 / folder_name
        target.mkdir(parents=True, exist_ok=True)
        source = selected.get(key)
        if source:
            for item in source.iterdir():
                if item.is_file():
                    shutil.copy2(item, target / item.name)
            (target / "SOURCE_POINTER.txt").write_text(
                "\n".join(
                    [
                        f"original_result_dir: {source}",
                        f"copied_to: {target}",
                        f"copied_at: {COPIED_AT}",
                        "reason: Confirmed log-retention-only result with final_result.csv and trials_all.csv; copied into Step 11 emergency four-model reference without deleting or moving the original result folder.",
                        "this_is_emergency_reference_not_final_canonical: yes",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            records.append((folder_name, source, target, False))
        else:
            (target / "MISSING_REQUIRED_RESULT.txt").write_text(
                "\n".join(
                    [
                        f"expected_model_family: {key[0]}",
                        f"expected_scope: {key[1]}",
                        "reason: A confirmed log-retention-only result with both final_result.csv and trials_all.csv was not found in PUBLIC.",
                        "selected_for_11_emergency_reference: no",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            records.append((folder_name, None, target, True))
    return records


def selected_block(selected):
    lines = []
    for key, folder_name in ROLE_MAP.items():
        source = selected.get(key)
        if source:
            lines.append(f"- {folder_name}: copied from `{rel_public(source)}`")
        else:
            lines.append(f"- {folder_name}: missing confirmed source; see `MISSING_REQUIRED_RESULT.txt`")
    return "\n".join(lines)


def write_readmes(selected):
    copied = selected_block(selected)
    (RESULTS_11 / "README.md").write_text(
        f"""# 11_baseline_growth_comparison_260520

## Purpose

11 is an emergency four-model reference stage, not a LogisticRegression-only stage.

11은 LogisticRegression 전용 단계가 아니라 log-retention-only 4개 모델을 모으는 emergency four-model reference 단계이다.

This folder keeps copied references to the four log-retention-only emergency model results:

- LogisticRegression promo0
- LogisticRegression promo1
- GradientBoosting promo0
- GradientBoosting promo1

## Emergency Status

This stage was created under an emergency bypass situation. It is a baseline/emergency reference layer, not a final canonical model evidence layer.

Steps 07~10 remain pending validation.

07~10은 여전히 pending validation 상태다.

These copied results are not final canonical model evidence.

이 결과는 final canonical model evidence가 아니다.

## What 11 Is Not

11 is not a LogisticRegression-only stage.

11 is not a GradientBoosting-only stage.

11 is not permission to move directly into SHAP or segmentation.

## What 11 Is

11 collects the confirmed log-retention-only four-model outputs in one reference location so that Step 12 can compare them consistently.

The original result folders are retained. This step copied files into the emergency reference structure and did not move or delete the source result folders.

## Current Emergency Reference Structure

{copied}

## Existing 11x/12x Meaning

The original `11x_baseline_growth_comparison_260516.ipynb` was a baseline growth comparison reference, not a LogisticRegression-only stage.

The original `12x_model_family_comparison_260516.ipynb` was a model family comparison reference, not a GradientBoosting-only stage.

The current PUBLIC emergency structure is a temporary narrowed application of that older 11x/12x meaning.

The original 11x/12x notebooks are future template/reference materials only. They were not executed in this restructuring task.

## Next Step

12 must compare the four model results for metric, overfit, and stability review before any stronger wording is used.

These copied results are not final canonical model evidence.
""",
        encoding="utf-8",
    )
    (RESULTS_12 / "README.md").write_text(
        """# 12_model_family_comparison_260520

## Purpose

12 is a four-model comparison stage, not a GradientBoosting-only stage.

12는 GradientBoosting 전용 단계가 아니라 4개 모델 비교 단계이다.

This stage compares the four model references gathered in Step 11.

## Scope Rule

Promo0 and promo1 must be evaluated separately.

promo0와 promo1은 분리해서 평가해야 한다.

This is not a single contest that chooses one winner across all four outputs. Promo0 and promo1 are different scopes and must not be collapsed into one final ranking without explicit review.

## Required Checks Before Comparison

Before any comparison claim is made, the reviewer must confirm:

- log-retention-only condition
- required `final_result.csv` and `trials_all.csv` files
- trial-level evidence in `trials_all.csv`
- overfit and stability signals
- the fact that Steps 07~10 remain pending validation

## Current Status

This is not final model selection.

이 단계는 final model selection이 아니다.

The current input manifest is:

- `four_model_comparison_summary/12_four_model_comparison_input_manifest.csv`

If present, `four_model_comparison_summary/12_four_model_metric_preview.csv` only summarizes metrics already saved in existing `final_result.csv` files. It is not a new calculation, not a model rerun, and not a final decision.

## Existing 11x/12x Meaning

The original `11x_baseline_growth_comparison_260516.ipynb` was a baseline growth comparison reference, not a LogisticRegression-only stage.

The original `12x_model_family_comparison_260516.ipynb` was a model family comparison reference, not a GradientBoosting-only stage.

The current PUBLIC emergency structure is a temporary narrowed application of that older 11x/12x meaning. The original 11x/12x notebooks are future template/reference materials only and were not executed in this restructuring task.
""",
        encoding="utf-8",
    )
    (NB_11 / "README.md").write_text(
        """# 11_baseline_growth_comparison_260520 notebooks

## Purpose

11 is an emergency reference step for collecting and organizing log-retention-only four-model results.

11 is not LogisticRegression-only.

11은 log-retention-only 4개 모델 결과를 수집하고 정리하는 emergency reference 단계다.

11은 LogisticRegression 전용이 아니다.

## Execution Status

No notebook was executed in this restructuring task.

이번 작업에서 노트북 실행은 하지 않았다.

Steps 07~10 remain pending validation.

07~10은 여전히 pending validation 상태다.

## Existing 11x/12x Meaning

The original `11x_baseline_growth_comparison_260516.ipynb` was a baseline growth comparison step, not a LogisticRegression-only step.

The current PUBLIC emergency structure narrows that meaning into a temporary log-retention-only four-model reference.

The original 11x notebook is future template/reference only and was not executed in this task.
""",
        encoding="utf-8",
    )
    (NB_12 / "README.md").write_text(
        """# 12_model_family_comparison_260520 notebooks

## Purpose

12 is a four-model comparison step.

12 is not GradientBoosting-only.

12는 4개 모델 비교 단계다.

12는 GradientBoosting 전용이 아니다.

## Execution Status

No notebook was executed in this restructuring task.

이번 작업에서 노트북 실행은 하지 않았다.

The actual comparison notebook must be written and executed later if the user decides to proceed with Step 12 comparison review.

## Existing 11x/12x Meaning

The original `12x_model_family_comparison_260516.ipynb` was a model family comparison step, not a GradientBoosting-only step.

The current PUBLIC emergency structure narrows that meaning into a temporary four-model comparison summary.

The original 12x notebook is future template/reference only and was not executed in this task.
""",
        encoding="utf-8",
    )


def write_12_manifests():
    manifest_rows = []
    metric_rows = []
    for key, folder_name in ROLE_MAP.items():
        family, scope = key
        folder = REF_11 / folder_name
        has_final = (folder / "final_result.csv").exists()
        has_trials = (folder / "trials_all.csv").exists()
        manifest_rows.append(
            {
                "comparison_item": folder_name,
                "model_family": family,
                "scope": scope,
                "source_in_11_reference": rel_public(folder),
                "has_final_result_csv": "yes" if has_final else "no",
                "has_trials_all_csv": "yes" if has_trials else "no",
                "ready_for_metric_comparison": "yes" if has_final and has_trials else "no",
                "notes": "Ready for limited saved-metric comparison only; not final selection." if has_final and has_trials else "Missing required copied files.",
            }
        )
        if has_final:
            _, row = parse_csv_first_row(folder / "final_result.csv")
            metric_rows.append(
                {
                    "comparison_item": folder_name,
                    "model_family": family,
                    "scope": scope,
                    "source_in_11_reference": rel_public(folder),
                    "test_roc_auc": row.get("test_roc_auc", ""),
                    "test_pr_auc": row.get("test_pr_auc", ""),
                    "test_f1": row.get("test_f1", ""),
                    "best_valid_auc": row.get("best_valid_auc", ""),
                    "best_train_auc": row.get("best_train_auc", ""),
                    "best_gap": row.get("best_gap", ""),
                    "overfit": row.get("overfit", ""),
                    "selection_note": row.get("selection_note", ""),
                    "notes": "Preview reads saved final_result.csv fields only; no new model calculation.",
                }
            )
    manifest_path = SUMMARY_12 / "12_four_model_comparison_input_manifest.csv"
    write_csv(
        manifest_path,
        ["comparison_item", "model_family", "scope", "source_in_11_reference", "has_final_result_csv", "has_trials_all_csv", "ready_for_metric_comparison", "notes"],
        manifest_rows,
    )
    metric_path = SUMMARY_12 / "12_four_model_metric_preview.csv"
    write_csv(
        metric_path,
        ["comparison_item", "model_family", "scope", "source_in_11_reference", "test_roc_auc", "test_pr_auc", "test_f1", "best_valid_auc", "best_train_auc", "best_gap", "overfit", "selection_note", "notes"],
        metric_rows,
    )
    return manifest_path, metric_path


def append_note():
    heading = "## 2026-05-20 | PUBLIC 11/12 emergency model stage meaning corrected"
    append_text = f"""

{heading}

이전에 급한 일정 때문에 11로 emergency bypass하는 결정을 했다.

하지만 11을 LogisticRegression 전용, 12를 GradientBoosting 전용으로 해석하면 pipeline 의미가 깨진다.

11은 log-retention-only four-model emergency reference 단계로 재정의한다.

12는 four-model comparison summary 단계로 재정의한다.

LogisticRegression promo0/promo1과 GradientBoosting promo0/promo1은 모두 11 emergency reference 안에 모은다.

12에서는 네 결과를 비교한다.

07~10은 여전히 pending validation이다.

이번 작업에서는 모델 실행, 노트북 실행, Optuna, SHAP, segmentation을 하지 않았다.

기존 결과는 이동하지 않고, 11 reference 구조로 copy했다.

copied result는 final canonical model evidence가 아니다.

기존 `11x_baseline_growth_comparison_260516.ipynb`는 LogisticRegression 전용 단계가 아니라 baseline growth comparison 단계였다.

기존 `12x_model_family_comparison_260516.ipynb`는 GradientBoosting 전용 단계가 아니라 model family comparison 단계였다.

현재 PUBLIC emergency 구조는 기존 11x/12x의 의미를 축소 적용한 임시 구조다.

기존 11x/12x 원본 notebook은 future template/reference로만 기록하며, 이번 작업에서 실행하지 않았다.

이번 결과는 final canonical model evidence가 아니다.

다음 단계는 12 comparison review 또는 07~10 pending validation 해소다.
"""
    text = read_text(NOTE)
    if heading not in text:
        with NOTE.open("a", encoding="utf-8") as handle:
            handle.write(append_text)


def write_handoff_readme(selected, inventory_path, candidates_path, manifest_path, metric_path):
    generated = [
        HANDOFF / "README.md",
        inventory_path,
        candidates_path,
        RESULTS_11 / "README.md",
        RESULTS_12 / "README.md",
        NB_11 / "README.md",
        NB_12 / "README.md",
        manifest_path,
        metric_path,
        HANDOFF / "PUBLIC_11_12_emergency_model_restructure_final_checks.csv",
        HANDOFF / "PUBLIC_11_12_emergency_model_restructure_zip_inventory.csv",
        HANDOFF / "run_public_11_12_restructure.py",
    ]
    generated_text = "\n".join([f"- `{rel_public(path)}`" for path in generated if path.exists() or path.parent.exists()])
    pointer_text = "\n".join([f"- `{rel_public(REF_11 / folder / 'SOURCE_POINTER.txt')}`" for folder in ROLE_MAP.values()])
    (HANDOFF / "README.md").write_text(
        f"""# PUBLIC 11/12 Emergency Model Restructure 260520

## Purpose

This handoff documents the correction of PUBLIC emergency modeling stage meaning for Steps 11 and 12.

## User decision

The user decided that Step 11 must not be interpreted as LogisticRegression-only and Step 12 must not be interpreted as GradientBoosting-only.

## Why 11 is not Logistic-only

11 is an emergency four-model reference stage.

It gathers the confirmed log-retention-only LogisticRegression promo0, LogisticRegression promo1, GradientBoosting promo0, and GradientBoosting promo1 results into one reference structure.

## Why 12 is not Gradient-only

12 is a four-model comparison summary stage.

It compares the four Step 11 references by scope and model family. It is not a GradientBoosting-only folder and it is not a final model selection result.

## What was copied

{selected_block(selected)}

The original result folders were retained. Files were copied, not moved.

## What was not changed

No model was trained.

No notebook was executed.

No Optuna run was performed.

No SHAP run was performed.

No segmentation run was performed.

No raw source file was intentionally modified by this task.

No `park.ingyeom` file was written by this task.

No `_data` file was written by this task.

No existing result folder was deleted or moved.

## Current four-model reference structure

- `PUBLIC/results/11_baseline_growth_comparison_260520/emergency_four_model_reference/logistic_regression_promo0/`
- `PUBLIC/results/11_baseline_growth_comparison_260520/emergency_four_model_reference/logistic_regression_promo1/`
- `PUBLIC/results/11_baseline_growth_comparison_260520/emergency_four_model_reference/gradient_boosting_promo0/`
- `PUBLIC/results/11_baseline_growth_comparison_260520/emergency_four_model_reference/gradient_boosting_promo1/`

## 07~10 pending validation status

07~10 remain pending validation.

The current emergency 11/12 structure does not complete or replace Steps 07~10.

## Current next step

The next step is either Step 12 comparison review or resolving the pending validation for Steps 07~10.

## Safe wording

- 11 is an emergency four-model reference stage.
- 12 is a four-model comparison summary stage.
- 07~10 remain pending validation.
- The copied four-model results are not final canonical model evidence.

## Unsafe wording

- 11 is LogisticRegression.
- 12 is GradientBoosting.
- 07~10 are skipped.
- The four-model results are final.
- SHAP or segmentation can start now.

## Source pointers

{pointer_text}

## Files generated

{generated_text}

- `PUBLIC\\zip\\PUBLIC_11_12_emergency_model_restructure_260520_review_package.zip`
""",
        encoding="utf-8",
    )


def has_text(path: Path, phrase: str) -> bool:
    return path.exists() and phrase in read_text(path)


def check(name, status, expected, actual, notes=""):
    return {"check_name": name, "status": status, "expected": expected, "actual": actual, "notes": notes}


def build_checks(inventory_path, candidates_path, selected, manifest_path, zip_path, zip_inventory_path):
    checks = [
        check("public_root_exists", "PASS" if PUBLIC.exists() else "FAIL", "PUBLIC root exists", str(PUBLIC.exists())),
        check("handoff_output_folder_exists", "PASS" if HANDOFF.exists() else "FAIL", "handoff folder exists", str(HANDOFF.exists())),
        check("inventory_before_exists", "PASS" if inventory_path.exists() else "FAIL", "inventory CSV exists", str(inventory_path.exists())),
        check("detected_model_result_candidates_created", "PASS" if candidates_path.exists() else "FAIL", "candidate manifest exists", str(candidates_path.exists())),
    ]
    for key, name in [
        (("LogisticRegression", "promo0"), "selected_log_retention_lr_promo0_found"),
        (("LogisticRegression", "promo1"), "selected_log_retention_lr_promo1_found"),
        (("GradientBoosting", "promo0"), "selected_log_retention_gb_promo0_found"),
        (("GradientBoosting", "promo1"), "selected_log_retention_gb_promo1_found"),
    ]:
        source = selected.get(key)
        checks.append(check(name, "PASS" if source else "FAIL", "one confirmed selected log-retention-only source", rel_public(source) if source else "not found"))
    checks.append(check("eleven_emergency_reference_folder_exists", "PASS" if REF_11.exists() else "FAIL", "11 emergency reference folder exists", str(REF_11.exists())))
    for folder, name in [
        ("logistic_regression_promo0", "eleven_lr_promo0_folder_exists"),
        ("logistic_regression_promo1", "eleven_lr_promo1_folder_exists"),
        ("gradient_boosting_promo0", "eleven_gb_promo0_folder_exists"),
        ("gradient_boosting_promo1", "eleven_gb_promo1_folder_exists"),
    ]:
        checks.append(check(name, "PASS" if (REF_11 / folder).exists() else "FAIL", "folder exists", str((REF_11 / folder).exists())))
    for folder, prefix in [
        ("logistic_regression_promo0", "eleven_lr_promo0"),
        ("logistic_regression_promo1", "eleven_lr_promo1"),
        ("gradient_boosting_promo0", "eleven_gb_promo0"),
        ("gradient_boosting_promo1", "eleven_gb_promo1"),
    ]:
        checks.append(check(f"{prefix}_final_result_exists", "PASS" if (REF_11 / folder / "final_result.csv").exists() else "FAIL", "final_result.csv exists", str((REF_11 / folder / "final_result.csv").exists())))
        checks.append(check(f"{prefix}_trials_all_exists", "PASS" if (REF_11 / folder / "trials_all.csv").exists() else "FAIL", "trials_all.csv exists", str((REF_11 / folder / "trials_all.csv").exists())))
    checks.extend(
        [
            check("twelve_comparison_folder_exists", "PASS" if SUMMARY_12.exists() else "FAIL", "12 comparison folder exists", str(SUMMARY_12.exists())),
            check("twelve_input_manifest_exists", "PASS" if manifest_path.exists() else "FAIL", "12 input manifest exists", str(manifest_path.exists())),
            check("eleven_readme_updated", "PASS" if has_text(RESULTS_11 / "README.md", "11 is an emergency four-model reference stage, not a LogisticRegression-only stage.") else "FAIL", "mandatory 11 README wording present", str(RESULTS_11 / "README.md")),
            check("twelve_readme_updated", "PASS" if has_text(RESULTS_12 / "README.md", "12 is a four-model comparison stage, not a GradientBoosting-only stage.") else "FAIL", "mandatory 12 README wording present", str(RESULTS_12 / "README.md")),
            check("note_md_append_completed", "PASS" if has_text(NOTE, "## 2026-05-20 | PUBLIC 11/12 emergency model stage meaning corrected") else "FAIL", "note heading appended", str(NOTE)),
            check("no_model_execution_performed", "PASS", "no model execution command used", "Only filesystem scan/copy/CSV/README/zip generation script was run"),
            check("no_notebook_execution_performed", "PASS", "no notebook execution command used", "No jupyter or nbconvert execution was run"),
            check("no_optuna_performed", "PASS", "no Optuna run", "No Optuna command was run"),
            check("no_shap_performed", "PASS", "no SHAP run", "No SHAP command was run"),
            check("no_segmentation_performed", "PASS", "no segmentation run", "No segmentation command was run"),
            check("no_raw_source_modified", "PASS", "no raw source writes by this task", "Generated output paths are handoff, results 11/12, notebooks 11/12 README, note.md, and zip"),
            check("no_park_ingyeom_modified", "PASS", "no park.ingyeom writes by this task", "This script only wrote under PUBLIC"),
            check("no_deletion_performed", "PASS", "no deletion command or deletion operation", "The script used mkdir, copy, write, and zip operations only"),
            check("review_zip_created", "PASS" if zip_path.exists() else "FAIL", "review zip exists", str(zip_path)),
            check("zip_inventory_created", "PASS" if zip_inventory_path.exists() else "FAIL", "zip inventory exists", str(zip_inventory_path)),
        ]
    )
    return checks


def create_zip(inventory_path, candidates_path, manifest_path, metric_path, final_checks_path):
    zip_path = ZIP_DIR / "PUBLIC_11_12_emergency_model_restructure_260520_review_package.zip"
    zip_inventory_path = HANDOFF / "PUBLIC_11_12_emergency_model_restructure_zip_inventory.csv"
    files = [
        HANDOFF / "README.md",
        inventory_path,
        candidates_path,
        final_checks_path,
        zip_inventory_path,
        HANDOFF / "run_public_11_12_restructure.py",
        RESULTS_11 / "README.md",
        RESULTS_12 / "README.md",
        NB_11 / "README.md",
        NB_12 / "README.md",
        manifest_path,
        metric_path,
        NOTE,
    ]
    for folder in ROLE_MAP.values():
        ref = REF_11 / folder
        for name in ["SOURCE_POINTER.txt", "MISSING_REQUIRED_RESULT.txt", "final_result.csv", "trials_all.csv", "feature_manifest_used.csv"]:
            path = ref / name
            if path.exists():
                files.append(path)
    unique = []
    seen = set()
    for path in files:
        if path.exists():
            key = str(path.resolve()).lower()
            if key not in seen:
                unique.append(path)
                seen.add(key)
    rows = [{"full_name": str(path.relative_to(REPO)).replace("\\", "/"), "size_bytes": path.stat().st_size} for path in unique]
    write_csv(zip_inventory_path, ["full_name", "size_bytes"], rows)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in unique:
            archive.write(path, arcname=str(path.relative_to(REPO)).replace("\\", "/"))
    return zip_path, zip_inventory_path


def main():
    inventory_path = inventory_before()
    candidates_path, _candidate_rows, selected = detect_candidates()
    copy_reference(selected)
    write_readmes(selected)
    manifest_path, metric_path = write_12_manifests()
    append_note()
    write_handoff_readme(selected, inventory_path, candidates_path, manifest_path, metric_path)

    final_checks_path = HANDOFF / "PUBLIC_11_12_emergency_model_restructure_final_checks.csv"
    zip_inventory_path = HANDOFF / "PUBLIC_11_12_emergency_model_restructure_zip_inventory.csv"
    zip_path = ZIP_DIR / "PUBLIC_11_12_emergency_model_restructure_260520_review_package.zip"
    write_csv(final_checks_path, ["check_name", "status", "expected", "actual", "notes"], build_checks(inventory_path, candidates_path, selected, manifest_path, zip_path, zip_inventory_path))
    zip_path, zip_inventory_path = create_zip(inventory_path, candidates_path, manifest_path, metric_path, final_checks_path)
    write_csv(final_checks_path, ["check_name", "status", "expected", "actual", "notes"], build_checks(inventory_path, candidates_path, selected, manifest_path, zip_path, zip_inventory_path))
    create_zip(inventory_path, candidates_path, manifest_path, metric_path, final_checks_path)

    print(f"selected_count={len(selected)}")
    for key, source in selected.items():
        print(f"{key[0]} {key[1]} <- {source}")
    print(f"final_checks={final_checks_path}")
    print(f"review_zip={zip_path}")


if __name__ == "__main__":
    main()
