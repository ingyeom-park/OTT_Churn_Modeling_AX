> preprocessing policy summary

> 왜 duration < 21을 제외했는가

최종 모델과 segmentation은 day0~20 관측창을 전제로 한다. `03_observation_window_policy.csv`는 week 1을 day0~6, week 2를 day7~13, week 3을 day14~20으로 정의한다. duration이 21일보다 짧은 row는 3주차까지의 관측창을 완전히 가질 수 없으므로 06x row policy에서 제외했다. 실제 제외 수는 238행이며, 제외 후 eligible row는 23,105행이다.

> 완전 중복은 어떻게 처리했는가

duration filter 이후 exact full duplicate extra row 26행을 제외했다. 이 처리는 같은 USER_KEY가 여러 번 등장한다는 이유만으로 row를 제거하는 방식이 아니다. 완전히 동일한 중복 extra row만 제거한 뒤 primary main cohort를 23,079행으로 확정했다.

> USER_KEY 중복은 왜 unique user로 부르면 안 되는가

`02_analysis_unit_contract.csv`는 분석 단위를 `row-level / subscription-event-level`로 정의한다. 이유는 USER_KEY duplication이 존재하기 때문이다. 따라서 row 수를 고객 수 또는 unique user 수라고 부르면 안 된다.

> row-level / subscription-event-level이 무슨 뜻인가

각 행은 한 명의 고유 고객이라기보다 구독 이벤트 또는 가입 이벤트 단위의 관측치다. 같은 USER_KEY가 여러 subscription-event row에 나타날 수 있다. 그래서 guide v3에서는 항상 `row`, `subscription-event row`, `분석 row`라고 표현해야 한다.

> day0~20 관측창과 day21 이후 대응기간

day0은 reg_date 기준 시작일이다. day0~20은 모델 feature와 행동 신호를 관측하는 기간이다. day21 이후는 대응 또는 개입 설계가 논리적으로 놓이는 기간이다. day21 이후 정보를 feature로 쓰면 사후 정보를 보는 문제가 생긴다.

> target is_repurchase의 의미

`is_repurchase=1`은 repurchase, renewal, next-month continuation proxy다. `is_repurchase=0`은 non-repurchase 또는 churn-like outcome proxy다. 이것은 confirmed cancellation reason이 아니라 operational churn-like proxy다. guide v3에서는 target을 `churn`으로 이름 바꾸지 않고, 모델 출력은 `repurchase_score`, 운영 변환은 `churn_risk = 1 - repurchase_score`로 설명한다.

> evidence files

- `park.ingyeom\reports\audits\02_target_score_orientation_260513\02_target_contract.csv`
- `park.ingyeom\reports\audits\02_target_score_orientation_260513\02_analysis_unit_contract.csv`
- `park.ingyeom\reports\audits\03_observation_window_policy_260513\03_observation_window_policy.csv`
- `park.ingyeom\reports\audits\06x_dataset_generation_260515\06x_row_policy_audit.csv`
