> 01 S7 definition and residual structure

> 확인된 것

- S7 internal id: `general_observation`
- S7 segment priority: `7`
- S7 rows: `7,896` out of `23,079` park17x_basis rows
- S7 assignment source column: `representative_segment`
- S7 matched rule text: `no prior rule matched`
- park notebook source confirms `np.select(conditions, segments[:6], default='general_observation')`, so S7 is the default residual after priority rules 1 through 6.

> representative rule priority

 segment_priority               representative_segment                                                                                             matched_rule_text
                1     high_risk_week3_inactive_or_drop flag_high_risk_top20 == 1 AND (flag_week3_inactive == 1 OR flag_week3_drop == 1 OR flag_retention_decay == 1)
                2 high_risk_only_w1_or_cold_start_weak                                flag_high_risk_top20 == 1 AND (flag_only_w1 == 1 OR flag_cold_start_weak == 1)
                3               high_risk_low_activity                                                          flag_high_risk_top20 == 1 AND flag_low_activity == 1
                4          medium_risk_retention_decay                      flag_high_risk_top20 == 0 AND churn_risk top 20-50 percent AND flag_retention_decay == 1
                5  content_preference_target_candidate                              flag_high_risk_top20 == 0 AND flag_low_activity == 0 AND content proxy flag == 1
                6                 stable_retained_user                                                                                     flag_low_risk_stable == 1
                7                  general_observation                                                                                         no prior rule matched

> 해석

S7는 1~6순위 대표 rule에 먼저 배정되지 않은 residual입니다. 따라서 `일반 고객`이라고 부르면 안 됩니다. 이 표현은 S7 내부에 행동 신호가 없거나, 정상/평균 고객이라는 뜻으로 오해될 수 있습니다. 실제 S7 안에는 기존 17x flag가 일부 남아 있습니다. 그러므로 이 집단은 `추가분해 검토 대상 residual` 또는 `monitoring group`으로 보는 편이 안전합니다.

> 확인하지 못한 것

- 17x에서 선언된 row-level `15x_oof_predictions.csv` 파일은 현재 로컬 15x 폴더에 존재하지 않습니다. 다만 17x assignment와 base datamart에는 이미 선택된 `repurchase_score`와 `churn_risk`가 포함되어 있습니다.
- 이번 작업은 새 segment assignment를 만들지 않았습니다.

> 사용자 승인 필요 항목

- S7 발표용 label 변경 여부
- S7 내부 subgroup을 action layer 또는 dashboard diagnostic tag로 사용할지 여부
- 새 파생변수 검토 여부
