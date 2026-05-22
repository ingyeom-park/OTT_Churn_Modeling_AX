> merge_feasibility_park_public_260521

## 작업 목적

이 폴더는 `park.ingyeom` canonical pipeline 후보와 `PUBLIC` promo-split branch의 병합 가능성을 검토하기 위한 증거 패키지다. 실제 병합, 기존 산출물 수정, canonical 결정은 수행하지 않았다.

## 수정하지 않은 것

- 원본 CSV
- 기존 notebook
- 기존 reports/results/figures/html
- 기존 active 산출물 위치
- 모델, Optuna, SHAP, segmentation 실행 결과

## 확인한 폴더

- `park.ingyeom`
- `PUBLIC`

## 생성한 산출물

`01_inventory_park.csv`부터 `37_review_zip_inventory.csv`까지의 감사 CSV/MD와 이 README를 생성했다.

## 핵심 발견 요약

- `park.ingyeom`에는 06x dataset, 15x payment-device sensitivity, 16x payment-removed SHAP, 17x segmentation, 18x storyline 흐름이 존재한다.
- `PUBLIC`에는 06x/06y promo split, 15 OOF, 16/16b SHAP family mapping, 17 segmentation hotfixes, 18 business storyline/polish hotfix 흐름이 존재한다.
- row count와 score source는 같은 기준으로 단정 병합하면 안 되며, 파일 기준 검수가 필요하다.
- CatBoost 관련 결과는 파일 evidence와 note 기록의 일치 여부를 `18_catboost_rerun_missing_note_audit.csv`에서 별도로 검토하도록 분리했다.

## blocking conflicts

- score source가 다를 수 있으므로 numeric dashboard/report 기준은 사용자 결정 전까지 합치면 안 된다.
- PUBLIC segment rule을 park 대표 rule로 승격하는 것은 사용자 결정 전까지 보류해야 한다.

## non-blocking conflicts

- PUBLIC의 100원딜 narrative, safe/unsafe wording, visual guide 구조, action matrix 형식은 reference로 가져올 수 있다.
- row count 차이는 원인 추정 없이 파일 기준 차이로 표시하면 병합 검토 자체를 막지는 않는다.

## 추천 병합 전략

`park.ingyeom`을 최종 뼈대 후보로 두고, `PUBLIC`은 promo1 100원딜 중심 storyline/reference/sensitivity 후보로 라벨링해 검토한다. 숫자는 하나의 기준처럼 섞지 않는다.

## ChatGPT가 추가 검수해야 할 파일

- `07_dataset_row_column_comparison.csv`
- `18_catboost_rerun_missing_note_audit.csv`
- `19_score_source_comparison.csv`
- `20_oof_score_source_comparison.csv`
- `28_segment_merge_candidate_table.csv`
- `31_business_storyline_merge_candidate_table.csv`
- `32_merge_feasibility_decision_table.csv`

## 사용자 결정 필요 항목

`34_open_questions_for_user.md`에 별도로 정리했다.

## self-reference limitation

`37_review_zip_inventory.csv`는 ZIP 생성 후 다시 ZIP에 추가했다. 따라서 ZIP 자체의 최종 해시를 이 파일 안에서 자기완결적으로 검증하지는 않는다. inventory는 ZIP 내부 member 목록 검사용이다.
