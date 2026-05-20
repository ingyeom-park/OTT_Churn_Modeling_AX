# 06_dataset_260520

## stage_name
06_dataset_260520

## stage_status
structure_created_needs_or_has_input_audit

## expected_inputs
User-confirmed 01~05 contracts and existing PUBLIC current input candidates under PUBLIC/data, if validated later.

## expected_outputs
06_preflight_contract_inheritance_check.csv; 06_log_retention_feature_policy.csv; 06_model_input_dataset_inventory.csv; 06_dataset_schema_check.csv; 06_raw_retention_exclusion_check.csv; 06_log_retention_presence_check.csv; 06_scope_row_count_check.csv; 06_open_risks_for_07.csv; 06_safe_unsafe_wording.csv; 06_final_checks.csv; README.md.

## why_this_stage_exists
This stage inherits the 01~05 contract and prepares or verifies model-input datasets under a current feature policy.

## what_must_not_be_done_here
Do not train models. Do not create final_result.csv, trials_all.csv, oof_predictions.csv, SHAP files, segmentation files, Optuna studies, model pickles/joblib files, or model comparison summaries here.

## next_stage
07_feature_mapping_AARRR_260520

## canonical_boundary
06 is dataset/input preparation only. Modeling artifacts must not be stored under 06.

## included_substep_notebooks
- `06x_dataset_generation_260515.ipynb`: existing PUBLIC dataset generation / cold_start row-level hotfix substep.
- `06y_promo_split_260520.ipynb`: existing PUBLIC promotion split substep.

These are kept inside 06 because they are dataset/input preparation work, not model-selection notebooks.


## Pipeline guardrail

This folder represents a PUBLIC pipeline stage placeholder or working area.
The existence of this folder does not mean the stage has been executed.
Stage execution requires explicit notebook execution, outputs, final checks, README, note update, and review zip.
Do not treat placeholder folders as completed analysis.

## 파이프라인 가드레일

이 폴더는 PUBLIC 파이프라인 단계의 placeholder 또는 작업 위치이다.
이 폴더가 존재한다고 해서 해당 단계가 실행 완료되었다는 뜻은 아니다.
단계 완료는 노트북 실행, 산출물 생성, final_checks, README, note 업데이트, review zip이 모두 갖춰졌을 때만 말할 수 있다.
placeholder 폴더를 완료된 분석으로 해석하지 않는다.
