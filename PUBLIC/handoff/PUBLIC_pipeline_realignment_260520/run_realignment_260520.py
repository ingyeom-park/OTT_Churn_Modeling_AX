from pathlib import Path
import csv
import shutil
import zipfile
from datetime import datetime


ROOT = Path.cwd().resolve()
PUBLIC = ROOT / "PUBLIC"
RUN_ID = "PUBLIC_pipeline_realignment_260520"
HANDOFF = PUBLIC / "handoff" / RUN_ID
ZIP_ROOT = PUBLIC / "zip"
ZIP_PATH = ZIP_ROOT / "PUBLIC_pipeline_realignment_260520_review_package.zip"

STAGES = [
    ("06", "06_dataset_260520", "reports/audits", "structure_created_needs_or_has_input_audit"),
    ("07", "07_feature_mapping_AARRR_260520", "reports/audits", "placeholder_created_pending_execution"),
    ("08", "08_promotion_nonpromotion_EDA_260520", "reports/eda", "placeholder_created_pending_execution"),
    ("09", "09_promotion_repurchase_2x2_EDA_260520", "reports/eda", "placeholder_created_pending_execution"),
    ("10", "10_feature_distribution_redundancy_pre_audit_260520", "reports/audits", "placeholder_created_pending_execution"),
    ("11", "11_baseline_growth_comparison_260520", "reports/models", "placeholder_created_blocked_until_07_10"),
    ("12", "12_model_family_comparison_260520", "reports/models", "placeholder_created_blocked_until_11"),
    ("14", "14_candidate_tuning_260520", "reports/models", "placeholder_created_blocked_until_12"),
    ("15", "15_oof_score_or_sensitivity_260520", "reports/models", "placeholder_created_blocked_until_model_candidate"),
    ("16", "16_SHAP_candidate_interpretation_260520", "reports/interpretation", "placeholder_created_blocked_until_candidate_model"),
    ("17", "17_segmentation_design_260520", "reports/segmentation", "placeholder_created_blocked_until_oof_score_and_16"),
    ("18", "18_business_recommendation_storyline_260520", "reports/business", "placeholder_created_blocked_until_17"),
]
STAGE_NAME = {sid: name for sid, name, _, _ in STAGES}
FIGURE_STAGE_IDS = {"08", "09", "10", "11", "12", "14", "16", "17", "18"}
RESULT_STAGE_IDS = {"11", "12", "14", "15"}
MISNUMBERED_NOTEBOOK_NAMES = {
    "06_gb_promo0.ipynb",
    "06_gb_promo1.ipynb",
    "06_lr_promo0.ipynb",
    "06_lr_promo1.ipynb",
}
MODEL_KEYWORDS = [
    "final_result",
    "trials_all",
    "oof",
    "shap",
    "optuna",
    "model",
    "gb_",
    "lr_",
    "catboost",
    "svm",
    "gradientboosting",
    "rf_",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def rel_public(path: Path) -> str:
    return path.relative_to(PUBLIC).as_posix()


def write_csv(path: Path, rows, fieldnames) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def unique_dest(dest: Path) -> Path:
    if not dest.exists():
        return dest
    idx = 1
    while True:
        candidate = dest.with_name(f"{dest.stem}_archived_{idx}{dest.suffix}")
        if not candidate.exists():
            return candidate
        idx += 1


def guess_stage(rel: str) -> str:
    low = rel.lower()
    parts = low.split("/")
    for sid, _, _, _ in STAGES:
        if Path(low).name.startswith(sid) or any(part.startswith(sid) for part in parts):
            return f"guessed_from_name:{sid}"
    if "06x" in low:
        return "guessed_from_name:06x_noncanonical_predecessor"
    if "06y" in low:
        return "guessed_from_name:06y_noncanonical_predecessor"
    return "not_guessed_from_name"


def is_misnumbered_notebook(rel: str) -> bool:
    return rel.startswith("notebooks/") and Path(rel).name in MISNUMBERED_NOTEBOOK_NAMES


def is_misnumbered_result(rel: str) -> bool:
    return rel == "results/_06_model_rerun_260520" or rel.startswith(
        "results/_06_model_rerun_260520/"
    )


NOTEBOOK_ARCHIVE = PUBLIC / "notebooks" / "_archive" / "misnumbered_06_model_notebooks_260520"
RESULT_ARCHIVE_ROOT = PUBLIC / "results" / "_archive" / "misnumbered_06_model_outputs_260520"
RESULT_SOURCE = PUBLIC / "results" / "_06_model_rerun_260520"
RESULT_DEST = RESULT_ARCHIVE_ROOT / "_06_model_rerun_260520"


def proposal_for(rel: str, item_type: str):
    low = rel.lower()
    if is_misnumbered_notebook(rel):
        new = (NOTEBOOK_ARCHIVE / Path(rel).name).relative_to(PUBLIC).as_posix()
        return (
            "move_to_archive_reference",
            new,
            "guessed 06 item is a model notebook by filename and must not remain in canonical 06 dataset/input stage",
        )
    if is_misnumbered_result(rel):
        suffix = rel[len("results/_06_model_rerun_260520") :].lstrip("/")
        new_path = RESULT_DEST / suffix if suffix else RESULT_DEST
        return (
            "move_to_archive_reference",
            new_path.relative_to(PUBLIC).as_posix(),
            "guessed 06 result folder contains model rerun artifacts and must be archive/reference, not canonical 06",
        )
    if rel.startswith("data/") and ("06_model_input" in low or "log_retention" in low):
        return (
            "keep_in_place",
            rel,
            "existing PUBLIC data input candidate kept in place; schema/content not validated in this structural realignment",
        )
    if rel.startswith("results/_06x") or rel.startswith("results/_06y"):
        return (
            "leave_unmodified_needs_user_review",
            "",
            "noncanonical predecessor output kept unchanged because this task does not validate or migrate its contents",
        )
    if rel.startswith("results/model") or (rel.startswith("notebooks/") and any(k in low for k in MODEL_KEYWORDS)):
        return (
            "leave_unmodified_needs_user_review",
            "",
            "existing model-related artifact is outside explicit 06 archive rule and needs user review before migration",
        )
    if rel.startswith("legacy/"):
        return ("leave_unmodified_needs_user_review", "", "legacy item kept unchanged as reference")
    return ("keep_in_place", rel, "existing item kept in place")


def snapshot_before():
    rows = []
    handoff_rel = f"handoff/{RUN_ID}"
    for path in sorted(PUBLIC.rglob("*"), key=lambda x: str(x).lower()):
        rel = path.relative_to(PUBLIC).as_posix()
        if rel == handoff_rel or rel.startswith(handoff_rel + "/"):
            continue
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        rows.append(
            {
                "path": path,
                "relative_path": rel,
                "item_type": "directory" if path.is_dir() else "file",
                "size_bytes": "" if path.is_dir() else stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            }
        )
    return rows


def safe_move(src: Path, dest: Path, before_entries, moved_map) -> None:
    if not src.exists():
        return
    ensure_dir(dest.parent)
    final_dest = unique_dest(dest)
    shutil.move(str(src), str(final_dest))
    src_rel = rel_public(src)
    dest_rel = rel_public(final_dest)
    moved_map[src_rel] = dest_rel
    if final_dest.is_dir():
        for entry in before_entries:
            r = entry["relative_path"]
            if r.startswith(src_rel + "/"):
                moved_map[r] = dest_rel + r[len(src_rel) :]


def create_stage_folders() -> None:
    for base in [
        PUBLIC / "notebooks",
        PUBLIC / "reports",
        PUBLIC / "results",
        ZIP_ROOT,
        HANDOFF,
        PUBLIC / "results" / "_archive",
        PUBLIC / "results" / "_current",
    ]:
        ensure_dir(base)
    for extra in [
        "reports/audits",
        "reports/eda",
        "reports/models",
        "reports/interpretation",
        "reports/segmentation",
        "reports/business",
        "reports/figures",
    ]:
        ensure_dir(PUBLIC / extra)
    for sid, stage_name, report_root, _ in STAGES:
        ensure_dir(PUBLIC / "notebooks" / stage_name)
        ensure_dir(PUBLIC / report_root / stage_name)
        if sid in FIGURE_STAGE_IDS:
            ensure_dir(PUBLIC / "reports" / "figures" / stage_name)
        if sid in RESULT_STAGE_IDS:
            ensure_dir(PUBLIC / "results" / stage_name)


def create_inventory(before_entries, moved_map) -> None:
    rows = []
    before_rel_set = {entry["relative_path"] for entry in before_entries}
    for entry in before_entries:
        rel = entry["relative_path"]
        action, proposed_new, reason = proposal_for(rel, entry["item_type"])
        status = "moved" if rel in moved_map else "not_moved"
        if action == "move_to_archive_reference" and status != "moved":
            status = "not_moved_source_missing_or_already_archived"
        rows.append(
            {
                "relative_path": rel,
                "item_type": entry["item_type"],
                "size_bytes": entry["size_bytes"],
                "modified_time": entry["modified_time"],
                "guessed_stage_from_name": guess_stage(rel),
                "current_location": rel,
                "proposed_action": action,
                "proposed_new_location": moved_map.get(rel, proposed_new),
                "reason": reason,
                "status": status,
            }
        )
    for sid, stage_name, _, _ in STAGES:
        rel = f"notebooks/{stage_name}"
        if rel not in before_rel_set:
            rows.append(
                {
                    "relative_path": rel,
                    "item_type": "directory",
                    "size_bytes": "",
                    "modified_time": "created_during_realignment",
                    "guessed_stage_from_name": f"guessed_from_name:{sid}",
                    "current_location": rel,
                    "proposed_action": "create_placeholder_only",
                    "proposed_new_location": rel,
                    "reason": "canonical placeholder folder required to preserve original pipeline sequence",
                    "status": "created",
                }
            )
    write_csv(
        HANDOFF / "PUBLIC_existing_inventory_before_realignment.csv",
        rows,
        [
            "relative_path",
            "item_type",
            "size_bytes",
            "modified_time",
            "guessed_stage_from_name",
            "current_location",
            "proposed_action",
            "proposed_new_location",
            "reason",
            "status",
        ],
    )


def create_misnumbered_audit(before_entries, moved_map) -> int:
    rows = []
    for entry in before_entries:
        rel = entry["relative_path"]
        if not (is_misnumbered_notebook(rel) or is_misnumbered_result(rel)):
            continue
        rows.append(
            {
                "original_relative_path": rel,
                "artifact_type": "notebook" if is_misnumbered_notebook(rel) else entry["item_type"],
                "detected_reason": "06 name with modeling/rerun artifact pattern; canonical 06 is dataset/input preparation only",
                "action_taken": "moved_to_archive_reference" if rel in moved_map else "not_moved_source_missing_or_already_archived",
                "new_relative_path": moved_map.get(rel, proposal_for(rel, entry["item_type"])[1]),
                "requires_user_review": "TRUE",
                "notes": "Do not treat as canonical 06. User approval is required before reusing under 11/12/14.",
            }
        )
    write_csv(
        HANDOFF / "misnumbered_06_model_artifacts_audit.csv",
        rows,
        [
            "original_relative_path",
            "artifact_type",
            "detected_reason",
            "action_taken",
            "new_relative_path",
            "requires_user_review",
            "notes",
        ],
    )
    return len(rows)


STAGE_SPECS = {
    "06": (
        "structure_created_needs_or_has_input_audit",
        "User-confirmed 01~05 contracts and existing PUBLIC current input candidates under PUBLIC/data, if validated later.",
        "06_preflight_contract_inheritance_check.csv; 06_log_retention_feature_policy.csv; 06_model_input_dataset_inventory.csv; 06_dataset_schema_check.csv; 06_raw_retention_exclusion_check.csv; 06_log_retention_presence_check.csv; 06_scope_row_count_check.csv; 06_open_risks_for_07.csv; 06_safe_unsafe_wording.csv; 06_final_checks.csv; README.md.",
        "This stage inherits the 01~05 contract and prepares or verifies model-input datasets under a current feature policy.",
        "Do not train models. Do not create final_result.csv, trials_all.csv, oof_predictions.csv, SHAP files, segmentation files, Optuna studies, model pickles/joblib files, or model comparison summaries here.",
        "07_feature_mapping_AARRR_260520",
        "06 is dataset/input preparation only. Modeling artifacts must not be stored under 06.",
    ),
    "07": (
        "placeholder_created_pending_execution",
        "Canonical 06 dataset/input checks and feature policy.",
        "Feature mapping and AARRR mapping audit outputs.",
        "current changes must be reflected in retention-family and AARRR mapping before modeling.",
        "Do not perform modeling, tuning, SHAP, or segmentation here.",
        "08_promotion_nonpromotion_EDA_260520",
        "",
    ),
    "08": (
        "placeholder_created_pending_execution",
        "06 canonical dataset/input checks and 07 feature mapping outputs.",
        "Promotion vs nonpromotion descriptive EDA tables and figures.",
        "Promotion and nonpromotion groups need descriptive comparison before model interpretation or business claims.",
        "Do not make causal claims. Do not model. Do not run SHAP. Do not segment.",
        "09_promotion_repurchase_2x2_EDA_260520",
        "",
    ),
    "09": (
        "placeholder_created_pending_execution",
        "06 canonical dataset/input checks, 07 mapping, and 08 promotion EDA outputs.",
        "Promotion x repurchase 2x2 descriptive EDA outputs.",
        "Repurchase and non-repurchase behavior should be compared inside promotion/nonpromotion groups before modeling claims.",
        "Do not model. Do not claim feature importance.",
        "10_feature_distribution_redundancy_pre_audit_260520",
        "",
    ),
    "10": (
        "placeholder_created_pending_execution",
        "06 canonical checks and 07~09 validation/EDA outputs.",
        "Feature distribution, redundancy, correlation/VIF, near-constant, and proxy-risk pre-audit handoff.",
        "Feature risks must be reviewed before 11 modeling preflight.",
        "Do not remove features in this stage. Record removal candidates or caution candidates only.",
        "11_baseline_growth_comparison_260520",
        "",
    ),
    "11": (
        "placeholder_created_blocked_until_07_10",
        "Completed or explicitly inherited/validated 07~10 outputs.",
        "Baseline growth comparison outputs for conservative/expanded or current feature sets.",
        "This is the first modeling stage after pre-model validation.",
        "Do not jump here directly from 06. Do not call outputs final model selection.",
        "12_model_family_comparison_260520",
        "",
    ),
    "12": (
        "placeholder_created_blocked_until_11",
        "11 baseline comparison outputs.",
        "Model-family comparison outputs for candidates such as LR, RF, GB/HGB, LightGBM, XGBoost, or CatBoost if approved later.",
        "Model-family comparison should occur after baseline behavior is established.",
        "Do not declare a final model here.",
        "14_candidate_tuning_260520",
        "",
    ),
    "14": (
        "placeholder_created_blocked_until_12",
        "12 candidate comparison outputs.",
        "Limited candidate tuning outputs after feature set, scope, and metric are locked.",
        "Tuning is only meaningful after candidate families and evaluation policy are constrained.",
        "Do not run Optuna until feature set, scope, and metric are locked. Do not declare final model here.",
        "15_oof_score_or_sensitivity_260520",
        "",
    ),
    "15": (
        "placeholder_created_blocked_until_model_candidate",
        "A fitted candidate model and locked score orientation.",
        "OOF score table or sensitivity audit outputs.",
        "This stage checks score behavior before interpretation and segmentation.",
        "Do not skip score-direction checks. Verify churn_risk = 1 - repurchase_score before downstream use.",
        "16_SHAP_candidate_interpretation_260520",
        "",
    ),
    "16": (
        "placeholder_created_blocked_until_candidate_model",
        "Fitted candidate model and validated score outputs.",
        "Candidate-model explanation outputs, preferably summarized by feature family.",
        "Model explanation must be tied to an actual fitted candidate model.",
        "Do not treat SHAP as causal evidence.",
        "17_segmentation_design_260520",
        "",
    ),
    "17": (
        "placeholder_created_blocked_until_oof_score_and_16",
        "OOF score outputs and behavior-rule evidence, plus 16 interpretation outputs if validated.",
        "Provisional segmentation design outputs.",
        "Segmentation should combine score evidence and behavior rules after model interpretation.",
        "Do not finalize segment names or final segments without user approval.",
        "18_business_recommendation_storyline_260520",
        "",
    ),
    "18": (
        "placeholder_created_blocked_until_17",
        "Validated 17 provisional segment design and upstream evidence.",
        "Dashboard, presentation, or business-action storyline materials.",
        "Business storyline should be built only after structural and analytical stages are complete.",
        "Do not make causal claims. Do not claim campaign effect proof. Separate experiment proposals from verified results.",
        "No later canonical stage defined in this realignment.",
        "",
    ),
}


def create_stage_readmes() -> None:
    for sid, stage_name, _, _ in STAGES:
        status, inputs, outputs, why, must_not, next_stage, extra = STAGE_SPECS[sid]
        text = f"""# {stage_name}

## stage_name
{stage_name}

## stage_status
{status}

## expected_inputs
{inputs}

## expected_outputs
{outputs}

## why_this_stage_exists
{why}

## what_must_not_be_done_here
{must_not}

## next_stage
{next_stage}
"""
        if extra:
            text += f"\n## canonical_boundary\n{extra}\n"
        (PUBLIC / "notebooks" / stage_name / "README.md").write_text(text, encoding="utf-8")


def create_stage_map() -> None:
    rows = []
    for sid, stage_name, report_root, status in STAGES:
        if sid == "06":
            allowed = "Create or verify dataset/input preparation artifacts only; record contract inheritance and current feature policy."
            forbidden = "Model training; Optuna; SHAP; segmentation; final_result.csv; trials_all.csv; model comparison summary."
            required = "06 canonical dataset/input checks and open risks must be reviewed before 07."
            equiv = "park.ingyeom stage 06-style dataset/input preparation boundary, adapted to PUBLIC current scope"
        elif sid in {"07", "08", "09", "10"}:
            allowed = "Pre-model validation, descriptive EDA, feature mapping, or feature-risk audit according to stage purpose."
            forbidden = "Modeling; tuning; SHAP; segmentation; causal claims."
            required = "Stage outputs must be completed or explicitly validated as inherited before moving forward."
            equiv = f"park.ingyeom {sid[:2]} pre-model validation/EDA/audit stage, adapted to PUBLIC current scope"
        else:
            allowed = "Placeholder only in this goal; later execution only after all upstream gates are complete."
            forbidden = "Execution during this realignment goal; skipping 07~10; finality claims without validation."
            required = "All upstream canonical gates required by stage status must be completed before execution."
            equiv = f"park.ingyeom {sid[:2]} downstream modeling/interpretation/business stage, adapted to PUBLIC current scope"
        rows.append(
            {
                "stage_id": sid,
                "canonical_stage_name": stage_name,
                "folder_notebooks": f"PUBLIC/notebooks/{stage_name}",
                "folder_reports": f"PUBLIC/{report_root}/{stage_name}",
                "folder_figures": f"PUBLIC/reports/figures/{stage_name}" if sid in FIGURE_STAGE_IDS else "",
                "folder_results": f"PUBLIC/results/{stage_name}" if sid in RESULT_STAGE_IDS else "",
                "expected_status_after_this_goal": status,
                "original_park_ingyeom_equivalent": equiv,
                "allowed_actions": allowed,
                "forbidden_actions": forbidden,
                "required_before_next_stage": required,
                "notes": "Created to preserve 06 -> 07 -> 08 -> 09 -> 10 -> 11 -> 12 -> 14 -> 15 -> 16 -> 17 -> 18 sequence.",
            }
        )
    write_csv(
        HANDOFF / "PUBLIC_pipeline_stage_map_260520.csv",
        rows,
        [
            "stage_id",
            "canonical_stage_name",
            "folder_notebooks",
            "folder_reports",
            "folder_figures",
            "folder_results",
            "expected_status_after_this_goal",
            "original_park_ingyeom_equivalent",
            "allowed_actions",
            "forbidden_actions",
            "required_before_next_stage",
            "notes",
        ],
    )


def create_handoff_readme() -> None:
    text = """# PUBLIC pipeline realignment 260520

## 1. Purpose
This handoff records a structural realignment of `PUBLIC` to the original `park.ingyeom`-style pipeline sequence from 06 through 18. This work is not model execution.

## 2. User-confirmed assumptions
- 01~05 contracts are treated as inherited by user confirmation.
- PUBLIC work must continue from 06 in the original sequence.
- Existing files must not be deleted.
- Ambiguous artifacts require user review before migration.
- 07~10 must not be skipped before modeling.

## 3. What was changed
- Canonical stage folders were created for 06, 07, 08, 09, 10, 11, 12, 14, 15, 16, 17, and 18.
- Placeholder README files were created under each canonical notebook stage folder.
- Explicitly misnumbered 06 model notebooks and rerun outputs were moved to archive/reference locations.
- Handoff CSVs, final checks, note append, zip inventory, and a review zip were created.

## 4. What was not changed
- No raw source data was modified.
- `park.ingyeom` was not modified.
- No model notebook was executed.
- No Optuna, SHAP, or segmentation work was performed.
- Existing non-06 model outputs were not migrated because they need user review.

## 5. Pipeline stage map
See `PUBLIC_pipeline_stage_map_260520.csv` for the canonical folder map, allowed actions, forbidden actions, and required gates.

## 6. Misnumbered artifact handling
Files named as 06 but behaving as modeling artifacts are not canonical 06 artifacts. They were moved to archive/reference when explicitly detected. See `misnumbered_06_model_artifacts_audit.csv`.

## 7. Empty placeholder folders
Empty folders are intentional placeholders. They preserve the required sequence even when a stage has not been executed.

## 8. Current canonical next step
The next canonical action is 06 dataset/input check, followed by 07 feature mapping, 08 EDA, 09 2x2 EDA, and 10 redundancy/proxy pre-audit before 11 modeling.

## 9. Blockers before modeling
11 modeling is blocked until 07~10 are completed or explicitly validated as inherited. 06 alone is not enough to begin modeling.

## 10. Safe / unsafe wording
Safe wording:
- 01~05 contracts are inherited by user confirmation, but 06 and downstream PUBLIC artifacts must still follow the original park.ingyeom pipeline sequence.
- 06 is dataset/input preparation only. Modeling must start only after 07~10 are completed or explicitly validated as inherited.

Unsafe wording:
- 06 model results are canonical.
- 07~10 can be skipped.
- Modeling is complete.
- SHAP or segmentation can start now.
- final_checks alone proves semantic validity.
"""
    (HANDOFF / "README.md").write_text(text, encoding="utf-8")


def append_note() -> None:
    note_path = PUBLIC / "note.md"
    heading = "## 2026-05-20 | PUBLIC pipeline realignment to park.ingyeom canonical flow"
    addition = f"""

{heading}

- 이번 작업은 모델 실행이 아니라 pipeline 구조 정렬 작업임.
- 01~05 계약은 사용자 확인 기준 동일하다고 보고 승계함.
- 06부터 원래 park.ingyeom 흐름을 최대한 따라가도록 구조를 생성함.
- 06는 dataset/input preparation으로 제한함.
- 06 안에 있던 모델 노트북/결과는 misnumbered/modeling artifact로 보고 archive/reference 또는 user review 대상으로 분리함.
- 07~10는 생략 대상이 아니며, 모델링 전 반드시 존재해야 하는 검증/EDA/audit 단계임.
- 11/12/14/15/16/17/18는 placeholder를 생성했지만 이번 작업에서 실행하지 않음.
- 빈 폴더는 의도적으로 생성한 placeholder임.
- 이후 실제 실행 순서는 06 canonical check -> 07 -> 08 -> 09 -> 10 -> 11 -> 12 -> 14 -> 15 -> 16 -> 17 -> 18.
- 사용자 승인 없이 07~10을 건너뛰고 모델링으로 가지 말 것.
"""
    if note_path.exists():
        old = note_path.read_text(encoding="utf-8", errors="replace")
        if heading not in old:
            note_path.write_text(old.rstrip() + addition, encoding="utf-8")
    else:
        note_path.write_text(addition.lstrip(), encoding="utf-8")


def package_files():
    files = [
        HANDOFF / "README.md",
        HANDOFF / "PUBLIC_existing_inventory_before_realignment.csv",
        HANDOFF / "PUBLIC_pipeline_stage_map_260520.csv",
        HANDOFF / "misnumbered_06_model_artifacts_audit.csv",
        HANDOFF / "PUBLIC_pipeline_realignment_final_checks.csv",
        HANDOFF / "PUBLIC_pipeline_realignment_zip_inventory.csv",
        PUBLIC / "note.md",
    ]
    for _, stage_name, _, _ in STAGES:
        files.append(PUBLIC / "notebooks" / stage_name / "README.md")
    return sorted({p for p in files if p.exists() and p.is_file()}, key=lambda p: p.relative_to(PUBLIC).as_posix())


def create_zip() -> None:
    ensure_dir(ZIP_PATH.parent)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in package_files():
            zf.write(path, path.relative_to(PUBLIC).as_posix())


def inspect_zip_rows():
    rows = []
    if ZIP_PATH.exists():
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            for info in sorted(zf.infolist(), key=lambda x: x.filename):
                rows.append({"full_name": info.filename, "size_bytes": info.file_size})
    return rows


def text_of(rel: str) -> str:
    path = PUBLIC / rel
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def create_final_checks(mis_count: int) -> None:
    checks = []

    def add(name, ok, expected, actual, notes=""):
        checks.append(
            {
                "check_name": name,
                "status": "PASS" if ok else "FAIL",
                "expected": expected,
                "actual": actual,
                "notes": notes,
            }
        )

    add("PUBLIC root exists", PUBLIC.exists(), "PUBLIC directory", str(PUBLIC.exists()))
    add("notebooks root exists", (PUBLIC / "notebooks").exists(), "PUBLIC/notebooks", str((PUBLIC / "notebooks").exists()))
    add("reports root exists", (PUBLIC / "reports").exists(), "PUBLIC/reports", str((PUBLIC / "reports").exists()))
    add("zip root exists", ZIP_ROOT.exists(), "PUBLIC/zip", str(ZIP_ROOT.exists()))
    add("handoff root exists", HANDOFF.exists(), f"PUBLIC/handoff/{RUN_ID}", str(HANDOFF.exists()))
    for sid, stage_name, _, _ in STAGES:
        add(f"{sid} folder exists", (PUBLIC / "notebooks" / stage_name).exists(), f"PUBLIC/notebooks/{stage_name}", str((PUBLIC / "notebooks" / stage_name).exists()))
    add("stage map exists", (HANDOFF / "PUBLIC_pipeline_stage_map_260520.csv").exists(), "stage map CSV", str((HANDOFF / "PUBLIC_pipeline_stage_map_260520.csv").exists()))
    add("before inventory exists", (HANDOFF / "PUBLIC_existing_inventory_before_realignment.csv").exists(), "before inventory CSV", str((HANDOFF / "PUBLIC_existing_inventory_before_realignment.csv").exists()))
    add("misnumbered audit exists", (HANDOFF / "misnumbered_06_model_artifacts_audit.csv").exists(), "misnumbered audit CSV", str((HANDOFF / "misnumbered_06_model_artifacts_audit.csv").exists()))
    add("README exists", (HANDOFF / "README.md").exists(), "handoff README", str((HANDOFF / "README.md").exists()))
    add("note updated", "PUBLIC pipeline realignment to park.ingyeom canonical flow" in text_of("note.md"), "note append section", str("PUBLIC pipeline realignment to park.ingyeom canonical flow" in text_of("note.md")))
    add("no model execution performed", True, "No model execution during this goal", "No notebook/model command executed by this realignment script", "Structural file operations only")
    add("no Optuna performed", True, "No Optuna during this goal", "No Optuna command executed", "Structural file operations only")
    add("no SHAP performed", True, "No SHAP during this goal", "No SHAP command executed", "Structural file operations only")
    add("no segmentation performed", True, "No segmentation during this goal", "No segmentation command executed", "Structural file operations only")
    readme06 = text_of(f"notebooks/{STAGE_NAME['06']}/README.md")
    readme11 = text_of(f"notebooks/{STAGE_NAME['11']}/README.md")
    add("06 README states dataset/input only", "06 is dataset/input preparation only" in readme06, "Boundary sentence present", str("06 is dataset/input preparation only" in readme06))
    add("11 README states blocked until 07~10", "blocked_until_07_10" in readme11 or "Do not jump here directly from 06" in readme11, "11 blocked wording", str("blocked_until_07_10" in readme11 or "Do not jump here directly from 06" in readme11))
    archive_ok = (NOTEBOOK_ARCHIVE.exists() or RESULT_ARCHIVE_ROOT.exists()) if mis_count > 0 else True
    add("archive/reference folder exists if misnumbered artifacts detected", archive_ok, "Archive exists when misnumbered artifacts detected", f"mis_count={mis_count}; archive_ok={archive_ok}")
    add("zip package created", ZIP_PATH.exists(), "review zip exists", str(ZIP_PATH.exists()))
    add("zip inventory created", (HANDOFF / "PUBLIC_pipeline_realignment_zip_inventory.csv").exists(), "zip inventory CSV exists", str((HANDOFF / "PUBLIC_pipeline_realignment_zip_inventory.csv").exists()))
    write_csv(
        HANDOFF / "PUBLIC_pipeline_realignment_final_checks.csv",
        checks,
        ["check_name", "status", "expected", "actual", "notes"],
    )


def main() -> None:
    if not PUBLIC.exists():
        raise SystemExit("PUBLIC root does not exist")
    before_entries = snapshot_before()
    create_stage_folders()
    moved_map = {}
    for nb in sorted(MISNUMBERED_NOTEBOOK_NAMES):
        safe_move(PUBLIC / "notebooks" / nb, NOTEBOOK_ARCHIVE / nb, before_entries, moved_map)
    safe_move(RESULT_SOURCE, RESULT_DEST, before_entries, moved_map)
    create_inventory(before_entries, moved_map)
    mis_count = create_misnumbered_audit(before_entries, moved_map)
    create_stage_readmes()
    create_stage_map()
    create_handoff_readme()
    append_note()
    write_csv(HANDOFF / "PUBLIC_pipeline_realignment_zip_inventory.csv", [], ["full_name", "size_bytes"])
    create_zip()
    write_csv(HANDOFF / "PUBLIC_pipeline_realignment_zip_inventory.csv", inspect_zip_rows(), ["full_name", "size_bytes"])
    create_final_checks(mis_count)
    create_zip()
    write_csv(HANDOFF / "PUBLIC_pipeline_realignment_zip_inventory.csv", inspect_zip_rows(), ["full_name", "size_bytes"])
    create_zip()
    print("PUBLIC pipeline realignment complete")
    print(f"before_entries={len(before_entries)}")
    print(f"misnumbered_entries={mis_count}")
    print(f"moved_entries={len(moved_map)}")
    print(f"zip={ZIP_PATH.relative_to(PUBLIC).as_posix()}")


if _name_ == "_main_":
    main()
