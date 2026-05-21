> AARRR design summary

> AARRR을 왜 사용했는가

AARRR은 feature를 마케팅 퍼널과 행동 해석 축으로 묶기 위한 설계 프레임이다. 이 프로젝트에서는 모델 성능만 설명하면 발표자가 어떤 행동을 보고 어떤 리텐션 전략을 세워야 하는지 설명하기 어렵다. 그래서 07x에서 feature를 Acquisition, Activation, Retention, Revenue, Referral 맥락으로 매핑했다.

> Acquisition 정의

Acquisition은 가입 또는 유입 맥락이다. 이 프로젝트에서 100원딜은 `is_promotion=1`로 표시되는 acquisition context다. 실제 관측 가능한 feature 예시는 `is_basic, is_premium, is_standard, payment_is_android, payment_is_ios, payment_is_mobile, payment_is_pc, reg_hour_afternoon, reg_hour_evening, reg_hour_morning, reg_hour_night, reg_is_weekend, is_promotion`이다. 단, 100원딜은 인과 효과가 아니라 유입 맥락과 비교 축이다.

> Activation 정의

Activation은 가입 직후 실제 이용 습관이 형성되는지 보는 단계다. 실제 관측 가능한 feature 예시는 `is_cold_start_3d_fixed, is_cold_start_7d_fixed, is_only_w1, is_w1_over_50pct, watch_session_w1, watch_time_min_w1`이다. day0~20 중 특히 day0~6, cold-start, week1 활동 신호가 중심이다.

> Retention 정의

Retention은 2~3주차 이용 유지와 감소를 보는 단계다. 실제 관측 가능한 feature 예시는 `avg_gap_w1_watch_days, avg_gap_w2_watch_days, avg_gap_w3_watch_days, diff_between_w2_w1, diff_between_w3_w1, diff_between_w3_w2, is_only_w2, is_only_w3, is_w2_over_50pct, is_w3_over_50pct, retention_w2_ratio, retention_w3_ratio, watch_session_w2, watch_session_w3, watch_time_min_w2, watch_time_min_w3, active_ratio, avg_daily_watch_time_min, avg_gap_between_watch_days, avg_rewatch_ratio`이다. 3주차 시청 감소는 원인이 아니라 이탈 위험 신호로만 표현한다.

> Revenue 정의

Revenue는 정가 전환 또는 재구매 proxy다. 이 프로젝트의 target `is_repurchase`가 Revenue proxy에 해당한다. 실제 관측 가능한 feature로 target 자체를 segment rule에 넣지는 않는다. 모델은 `is_repurchase=1`을 positive class로 학습하고, 운영 해석은 `churn_risk = 1 - repurchase_score`로 변환한다.

> Referral 정의

Referral은 추천, 친구초대, 바이럴 확산 같은 후속 실험 축이다. 현재 파일 기준으로 referral 행동 결과가 검증된 것은 아니다. guide v3에서는 분석 결과가 아니라 후속 A/B test 제안으로만 다룬다. 07x mapping에서 referral 관련 feature가 제한적이거나 관측 불가능한 경우, 이를 명시해야 한다.

> day0~20 기준과 day21 이후 대응기간

day0~20은 feature 관측창이다. day21 이후는 리텐션 메시지, 정가 전환 안내, 쿠폰 또는 추천 실험 같은 대응 설계가 놓이는 시점이다. day21 이후 행동은 모델 feature로 쓰지 않는다.

> 관측 불가능하거나 후속 실험으로만 다루는 것

진짜 이용 동기, 지불 의향, referral 효과, 캠페인 반응률, 실제 개입 효과는 현재 산출물만으로 확정할 수 없다. 이들은 guide v3에서 후속 실험 또는 팀 검토 항목으로 분리해야 한다.

> evidence files

- `park.ingyeom\reports\audits\07x_feature_mapping_AARRR_260515\07x_feature_mapping_master.csv`
- `park.ingyeom\reports\audits\07x_feature_mapping_AARRR_260515\07x_AARRR_summary_by_feature_set.csv`
- `park.ingyeom\reports\audits\03_observation_window_policy_260513\03_observation_window_policy.csv`
- `park.ingyeom\reports\audits\02_target_score_orientation_260513\02_target_contract.csv`
