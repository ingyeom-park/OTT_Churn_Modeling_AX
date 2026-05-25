> FINAL_S7_residual_promo_decomposition_diagnostic_260522

> 작업 목적

이 패키지는 park 17x `general_observation` residual 안에서 100원딜(promo1)과 비100원딜(promo0)의 관찰 이탈률 차이가 기존 17x flag와 기존 approved feature로 어느 정도 설명 가능한지 진단합니다. 이 작업은 diagnostic입니다. canonical segmentation 변경, 새 segment assignment, 새 representative rule 확정, 새 파생변수 생성이 아닙니다.

> 사용한 input basis

- basis name: `park17x_basis`
- assignment: `park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_representative_segment_assignment.csv`
- dataset: `park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_segmentation_base_datamart.csv`
- rows: `23,079`
- score source: `expanded_no_payment_device / overall_with_promotion / LightGBM / OOF churn_risk`
- S7 id: `general_observation`
- S7 rows: `7,896`

> 23,079 / 23,097 기준 충돌 확인

park 17x는 23,079행 기준입니다. PUBLIC reference branch에는 23,097행 기준 OOF/assignment 파일이 존재합니다. 이번 분석은 23,097 PUBLIC branch를 병합하거나 기준으로 승격하지 않았습니다.

> LightGBM / GradientBoosting 기준 충돌 확인

park 17x는 LightGBM OOF churn_risk를 사용합니다. PUBLIC reference branch는 promo-scope GradientBoosting/LogisticRegression OOF score를 포함합니다. PUBLIC numeric score와 segment assignment는 이번 분석에 사용하지 않았습니다.

> S7 정의

S7 `general_observation`은 priority 1~6 rule에 먼저 배정되지 않은 default residual입니다. notebook source에서 `np.select(..., default='general_observation')` 구조를 확인했습니다. 따라서 S7를 일반 고객군으로 확정하면 안 됩니다.

> S7 promo gap 관찰 결과

S7 안에서 promo0 observed churn rate는 `0.127469`, promo1 observed churn rate는 `0.190643`입니다. 차이는 `6.317` percentage point입니다. 이 값은 관찰 차이이며 인과 효과가 아닙니다.

> 기존 feature/flag로 설명 가능한 신호

기존 numeric feature profile과 기존 17x flag gap ranking을 생성했습니다. 큰 차이를 보이는 feature/flag는 후속 모니터링 subgroup 후보를 설명할 수 있지만, 사용자 승인 전에는 action layer diagnostic tag로도 확정하지 않았습니다.

> 새 feature 필요 여부

이 패키지는 새 feature가 필요하다고 확정하지 않습니다. 기존 feature/flag만으로 설명 가능한 가능성, 기존 flag subgroup 검토 가능성, 새 feature hypothesis 가능성, insufficient evidence 가능성을 모두 decision evidence table에 분리했습니다.

> 확인한 것

- park 17x assignment/rule/flag/base datamart를 실제로 읽었습니다.
- S7 residual 정의를 실제 rule file과 notebook source에서 확인했습니다.
- S7 promo x outcome 4-cell, flag distribution, near-miss, existing feature profile, demographic action layer descriptive를 생성했습니다.
- source fingerprint before/after를 생성해 기존 source 파일이 바뀌지 않았음을 확인했습니다.

> 확인하지 못한 것

- 17x_score_source_selection이 선언한 row-level `15x_oof_predictions.csv`는 현재 로컬 15x 폴더에서 찾지 못했습니다. 대신 17x base datamart 안의 score columns와 15x model summary를 기준으로 score lineage를 기록했습니다.

> 판단 보류 항목

- S7 발표용 label 변경
- 기존 flag 조합을 action layer diagnostic tag로 사용할지 여부
- 새 원자료 기반 feature 검토 여부

> 다음 질문

ChatGPT 검수 후, 사용자가 기존 feature/flag 기반 monitoring subgroup을 action layer로 둘지 승인해야 합니다.
