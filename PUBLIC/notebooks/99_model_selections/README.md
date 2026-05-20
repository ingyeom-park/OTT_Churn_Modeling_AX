# 99_model_selections

This folder stores model-running notebooks that should not sit in the canonical 06-18 pipeline stage folders.

## Rule
- Keep canonical pipeline stage folders for ordered pipeline work.
- Keep model-selection notebooks here, grouped by model family.
- Moving notebooks here does not mean the notebooks were executed or validated.
- Existing result folders are not moved by this notebook reorganization.

## Model folders
- catboost
- svm
- random_forest
- logistic_regression
- gradient_boosting

## Manifest
See `99_model_selections_notebook_manifest_260520.csv` for original and new notebook paths.


## Canonical status clarification

This folder is a model candidate notebook pool, not a canonical PUBLIC pipeline stage.
Notebook filename prefixes such as 01, 02, 06, 09 are candidate labels or legacy numbering, not pipeline step numbers.
Canonical modeling should proceed through 11_baseline_growth_comparison, 12_model_family_comparison, and 14_candidate_tuning after 07~10 have been completed or explicitly validated.
Do not skip 07, 08, 09, or 10 because this folder exists.

이 폴더는 모델 후보 노트북 보관소이며, 정규 PUBLIC 파이프라인 단계가 아니다.
노트북 파일명 앞의 01, 02, 06, 09 같은 숫자는 정규 단계 번호가 아니다.
정규 모델링은 07~10 단계가 완료되었거나 명시적으로 승계 검증된 뒤, 11/12/14 계열에서 진행해야 한다.
이 폴더가 존재한다고 해서 07, 08, 09, 10을 건너뛰면 안 된다.
