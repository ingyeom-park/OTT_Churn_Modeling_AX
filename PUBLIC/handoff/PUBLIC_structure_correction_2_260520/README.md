# PUBLIC structure correction 2 260520

## 1. Purpose

This correction clarifies that PUBLIC/results/model and PUBLIC/notebooks/99_model_selections are not canonical PUBLIC pipeline stage outputs. It creates review evidence for user inspection without running models or notebooks.

## 2. User context

The user already realigned the PUBLIC folder into dataset, feature mapping, EDA, audit, modeling, interpretation, segmentation, and business recommendation areas. This correction addresses remaining ambiguity caused by numeric prefixes in legacy model result folders and candidate notebook filenames.

## 3. What was checked

- PUBLIC/results/model existence and immediate child items.
- PUBLIC/notebooks/99_model_selections existence and recursive child items.
- PUBLIC/note.md existence and the corrupted 99_model_selections notebook reorganization record.
- PUBLIC stage folders from 06 through 18 as requested.
- File and folder paths for inventory and manifest creation.

The inferred_role column in PUBLIC_inventory_before_correction2.csv is an inferred value based only on file name and location. It is not semantic validation.

## 4. What was changed

- Created or updated PUBLIC/results/model/README.md.
- Updated PUBLIC/notebooks/99_model_selections/README.md.
- Appended a correction record to PUBLIC/note.md when present.
- Created or updated stage README guardrail sections for 06, 07, 08, 09, 10, 11, 12, 14, 15, 16, 17, and 18.
- Created handoff inventory, manifests, final checks, zip inventory, and review zip.

## 5. What was not changed

- No raw source CSV was modified.
- No _data folder was modified.
- No park.ingyeom folder was modified.
- No existing model result folder was moved or deleted.
- No notebook was executed.
- No model training, retuning, Optuna, SHAP, or segmentation was performed.
- No model performance value was read for judgment.

## 6. Status of PUBLIC/results/model

PUBLIC/results/model contains legacy/reference model candidate outputs, not canonical stage outputs.

This folder contains legacy/reference model candidate outputs created before the current PUBLIC pipeline realignment.
This folder is NOT an active canonical pipeline stage output.
Numeric prefixes such as 01, 02, 03 in this folder are model candidate labels, not PUBLIC pipeline step numbers.
Do not interpret these folders as Step 01~10 pipeline outputs.
Do not use these outputs as canonical modeling evidence unless a later stage explicitly validates or promotes them.

이 폴더는 현재 PUBLIC canonical pipeline 단계 산출물이 아니라, 구조 재정렬 이전 또는 모델 후보 탐색 과정에서 생성된 reference/legacy 모델 결과 보관 위치이다.
폴더명 앞의 01, 02, 03 등 숫자는 정규 파이프라인 단계 번호가 아니다.
이 결과를 01~10 단계 산출물로 해석하면 안 된다.
이 결과는 이후 11/12/14 계열 단계에서 명시적으로 검증 또는 승격되기 전까지 canonical model result가 아니다.

## 7. Status of PUBLIC/notebooks/99_model_selections

PUBLIC/notebooks/99_model_selections is a candidate notebook pool, not a pipeline stage.

This folder is a model candidate notebook pool, not a canonical PUBLIC pipeline stage.
Notebook filename prefixes such as 01, 02, 06, 09 are candidate labels or legacy numbering, not pipeline step numbers.
Canonical modeling should proceed through 11_baseline_growth_comparison, 12_model_family_comparison, and 14_candidate_tuning after 07~10 have been completed or explicitly validated.
Do not skip 07, 08, 09, or 10 because this folder exists.

이 폴더는 모델 후보 노트북 보관소이며, 정규 PUBLIC 파이프라인 단계가 아니다.
노트북 파일명 앞의 01, 02, 06, 09 같은 숫자는 정규 단계 번호가 아니다.
정규 모델링은 07~10 단계가 완료되었거나 명시적으로 승계 검증된 뒤, 11/12/14 계열에서 진행해야 한다.
이 폴더가 존재한다고 해서 07, 08, 09, 10을 건너뛰면 안 된다.

## 8. Why 07~10 must not be skipped

07 through 10 are the bridge between dataset creation and modeling. They cover feature mapping, promotion/non-promotion EDA, 2x2 promotion-repurchase EDA, and feature redundancy/proxy pre-audit. Their folders existing as placeholders does not prove that the stages were executed or validated.

## 9. Current recommended next step

Review this package first. If the correction passes review, proceed to 06 dataset/input canonical check or 07 feature mapping. Do not start 11 modeling unless 07, 08, 09, and 10 are completed or explicitly validated as inherited.

## 10. Files generated in this correction

- PUBLIC/handoff/PUBLIC_structure_correction_2_260520/README.md
- PUBLIC/handoff/PUBLIC_structure_correction_2_260520/PUBLIC_inventory_before_correction2.csv
- PUBLIC/handoff/PUBLIC_structure_correction_2_260520/PUBLIC_results_model_reference_manifest.csv
- PUBLIC/handoff/PUBLIC_structure_correction_2_260520/PUBLIC_99_model_selections_manifest.csv
- PUBLIC/handoff/PUBLIC_structure_correction_2_260520/PUBLIC_structure_correction_2_final_checks.csv
- PUBLIC/handoff/PUBLIC_structure_correction_2_260520/PUBLIC_structure_correction_2_zip_inventory.csv
- PUBLIC/zip/PUBLIC_structure_correction_2_260520_review_package.zip
- PUBLIC/results/model/README.md
- PUBLIC/notebooks/99_model_selections/README.md
- Stage README files for 06, 07, 08, 09, 10, 11, 12, 14, 15, 16, 17, and 18.

## 11. Safe / unsafe wording

Safe wording:

- PUBLIC/results/model contains legacy/reference model candidate outputs, not canonical stage outputs.
- PUBLIC/notebooks/99_model_selections is a candidate notebook pool, not a pipeline stage.
- 07~10 must be completed or explicitly validated before 11 modeling.

Unsafe wording:

- PUBLIC/results/model is canonical.
- 99_model_selections means modeling is ready.
- 07~10 can be skipped.
- The current model results are final.
- SHAP or segmentation can start now.

## Encoding note

The existing corrupted note text was preserved. A new correction record was appended with UTF-8 output. Full-file encoding conversion was not forced because preserving the existing file safely was prioritized.

## Packaging accuracy note

During review package creation, the newly generated review zip was recreated so that `final_checks` and `zip_inventory` matched the final package. No existing source data, notebook, model result folder, raw file, `_data` file, `park.ingyeom` file, or team-member folder was deleted by this correction.
