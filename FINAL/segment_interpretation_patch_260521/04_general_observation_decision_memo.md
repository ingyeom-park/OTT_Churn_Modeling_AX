> general_observation decision memo

작성일: 2026-05-21
기준 파일: park.ingyeom 17x segmentation outputs
분석 단위: row-level / subscription-event-level

> 1. general_observation은 진짜 residual인가?

기술적으로는 residual이 맞습니다. 17x notebook은 여섯 개 priority rule을 먼저 적용한 뒤, 어느 rule에도 걸리지 않은 row를 `general_observation`으로 배정했습니다. 실제 rule source는 `np.select(..., default='general_observation')` 구조입니다.

다만 의미적으로는 완전히 빈 잔여군이 아닙니다. 이 집단은 7,896행이며 전체의 34.2%입니다. 평균 churn_risk는 0.169이고 실제 churn rate는 15.9%입니다. 내부에는 `flag_low_activity` 51.5%, `flag_cold_start_weak` 45.8%, `flag_retention_decay` 40.6%, `flag_week3_inactive` 35.3%, `flag_week3_drop` 33.7%가 남아 있습니다.

따라서 이 집단은 아무 특징도 없는 사람이 아닙니다. 현재 17x priority rule로 대표 이름을 붙이지 못한 혼합 잔여군입니다.

> 2. 더 나눌 만한 행동 신호가 있는가?

행동 신호는 있습니다. target split으로 보면 non-repurchase row에서 churn_risk, risk_percentile_desc, 3주차 이용 약화, cold-start 계열, low-activity 계열의 차이가 관찰됩니다. 다만 이번 작업의 원칙상 `is_repurchase`를 새 rule로 쓰면 안 되고, segment 재배정도 금지되어 있습니다. 그러므로 지금 할 수 있는 결론은 후속 rule 후보는 존재하지만 이번 FINAL에서는 새 segment로 확정하지 않는다는 것입니다.

상위 차이 feature 예시는 다음과 같습니다.

- `risk_percentile_desc`: smd=1.336, direction=repurchase_1_higher
- `repurchase_score`: smd=1.255, direction=repurchase_1_higher
- `churn_risk`: smd=-1.255, direction=repurchase_0_higher
- `watch_time_min_w2`: smd=0.582, direction=repurchase_1_higher
- `genre_diversity_count`: smd=0.572, direction=repurchase_1_higher
- `recency`: smd=-0.561, direction=repurchase_0_higher
- `active_ratio`: smd=0.561, direction=repurchase_1_higher
- `watch_session_w2`: smd=0.544, direction=repurchase_1_higher

> 3. target 기준으로만 차이가 있고 사전 행동 rule로는 설명이 약한가?

score source 차이는 target과 모델 출력에 가까우므로 강한 행동 rule 근거로 쓰기 어렵습니다. 그러나 watch time, session, retention, cold-start 관련 차이는 사전 행동 신호로 볼 수 있습니다. 문제는 이 신호들이 이미 기존 17x priority rule에 부분적으로 쓰였고, general_observation에 남은 row는 그 조합이 강하지 않거나 score threshold와 결합되지 않은 row라는 점입니다.

> 4. 발표에서 핵심 세그먼트로 유지해도 되는가?

핵심 세그먼트로 유지하는 것은 권장하지 않습니다. 이 집단은 row 수가 크기 때문에 발표에서 언급할 필요는 있지만, 핵심 이탈 방어 타겟으로 말하면 과장입니다.

> 5. monitoring group 또는 residual로 낮춰야 하는가?

monitoring residual로 낮추는 것을 추천합니다. promo1 share는 50.6%로 100원딜 맥락을 살릴 수 있지만, 이것은 segment rule이 아니라 presentation interpretation입니다.

> 6. 추천 발표명

추천 발표명은 `추가 관찰 필요 잔여군`입니다. 100원딜 발표 문맥에서는 `100원딜 추가 관찰 필요군`으로 부를 수 있습니다. 단, final segment 확정명이 아니라 presentation label 후보입니다.
