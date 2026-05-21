> segmentation basis summary

> 17x segmentation 생성 기준

17x는 15x OOF churn_risk와 17x 내부 flag를 사용해 각 subscription-event row에 하나의 representative segment를 배정했다. 기존 assignment와 rule은 변경하지 않는다.

> 7개 segment 요약

- 1. `high_risk_week3_inactive_or_drop`: 3,793 rows, churn_rate 0.732, mean_churn_risk 0.733, promo1_share 0.590
- 2. `high_risk_only_w1_or_cold_start_weak`: 265 rows, churn_rate 0.717, mean_churn_risk 0.698, promo1_share 0.706
- 3. `high_risk_low_activity`: 511 rows, churn_rate 0.814, mean_churn_risk 0.765, promo1_share 0.609
- 4. `medium_risk_retention_decay`: 3,195 rows, churn_rate 0.388, mean_churn_risk 0.358, promo1_share 0.546
- 5. `content_preference_target_candidate`: 6,195 rows, churn_rate 0.101, mean_churn_risk 0.095, promo1_share 0.485
- 6. `stable_retained_user`: 1,224 rows, churn_rate 0.011, mean_churn_risk 0.017, promo1_share 0.342
- 7. `general_observation`: 7,896 rows, churn_rate 0.159, mean_churn_risk 0.169, promo1_share 0.506

> 4개 action tier

1. 즉시 개입 우선군: `high_risk_week3_inactive_or_drop`, `high_risk_low_activity`, `high_risk_only_w1_or_cold_start_weak`
2. 관찰 강화군: `medium_risk_retention_decay`
3. 정가 전환 강화군: `content_preference_target_candidate`, `stable_retained_user`
4. 모니터링 / 추가분해 후보군: `general_observation`

> 1~4순위 우선순위 논리

1~3순위는 churn_risk 상위권과 3주차 비활성, 초기 activation 약화, 저활동 같은 행동 신호가 결합된 고위험군이다. 4순위는 상위 20% 고위험은 아니지만 retention decay가 관찰되는 watchlist다.

> 5~7순위 역할 재분류

5~7순위는 버리는 것이 아니라 역할을 재분류한다. `content_preference_target_candidate`는 콘텐츠 큐레이션 기반 정가 전환 강화군, `stable_retained_user`는 안정 유지군, `general_observation`은 monitoring residual이다.

> general_observation 처리

`general_observation`은 default residual이지만 전체 비중이 크므로 제외하지 않는다. 핵심 이탈 방어 target이 아니라 monitoring group과 후속 decomposition 후보로 둔다.

> content_preference_target_candidate 처리

이 segment는 content proxy OR 조건이다. 고위험 이탈 방어군이라고 말하지 않고, 콘텐츠 큐레이션 반응 후보군으로 약화한다.

> promo-aware presentation label 원칙

100원딜은 segment rule에 직접 넣지 않는다. presentation label과 business context에서 promo1을 100원딜로 설명하고 promo0는 comparison reference로 둔다.

> age/gender action layer 원칙

age/gender는 원인이나 대표 segment rule이 아니다. 메시지, 채널, 콘텐츠 묶음의 personalization layer로만 쓴다.

> evidence files

- `park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_representative_segment_rules.csv`
- `park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_segment_summary.csv`
- `FINAL\segment_interpretation_patch_260521\07_promo_aware_segment_label_mapping.csv`
- `FINAL\final_note.md`
