> 최종 프로젝트 주제

100원딜 OTT 가입자의 정가 전환 실패 위험을 row-level / subscription-event-level 데이터로 관찰하고, day0~20 이용 행동을 기준으로 이탈 위험 신호와 개입 우선순위 후보를 정리하는 프로젝트다. 이 프로젝트는 100원딜이 이탈을 유발했다는 인과 분석이 아니다. 이 프로젝트는 100원딜이라는 초저가 유입 맥락에서 어떤 행동 신호가 재구매 실패와 함께 관찰되는지 설명하는 분석이다.

> 현재 최종 결론

현재 최종 방향은 park.ingyeom 파이프라인을 따른다. 최종 score source는 park 17x에서 선택한 `LightGBM / expanded_no_payment_device / overall_with_promotion / OOF churn_risk`다. 17x 대표 segment rule과 assignment는 수정하지 않는다. 다만 발표용 label, business action matrix, demographic personalization layer는 보정한다.

100원딜은 segment rule에 직접 넣지 않는다. 대신 presentation label, segment interpretation, business strategy에서 적극적으로 살린다. age/gender는 segment rule이 아니라 메시지와 채널을 조정하는 action personalization layer로만 사용한다. payment_device 계열은 최종 해석 기준에서 제거된 상태로 본다.

> park.ingyeom을 최종 파이프라인으로 채택하는 이유

park.ingyeom 17x는 06x expanded dataset 23,079행과 15x OOF score를 row_id 기준으로 맞춘 뒤 representative segment를 만들었다. 17x score source file은 `17x_score_source_selection.csv`이며, primary row는 `feature_set_variant == expanded_no_payment_device`, `dataset_scope == overall_with_promotion`, `model_name == LightGBM`, row_count 23,079이다.

이 선택은 16x payment-removed SHAP candidate plan과 기준을 맞춘다. 16x `overall_with_promotion`은 LightGBM, payment removed, feature_count 76, row_count 23,079로 기록되어 있다. 따라서 17x segmentation score와 16x explanation basis가 같은 model family와 feature policy 위에 놓인다.

> PUBLIC의 지위

PUBLIC은 final pipeline이 아니다. PUBLIC은 100원딜 중심 promo-scope segmentation과 business storyline을 시도한 reference branch다. PUBLIC 11 README는 emergency four-model reference stage라고 기록하고, PUBLIC 12 README는 final model selection이 아니라고 기록한다. 그러므로 PUBLIC의 numeric score, segment assignment, model decision은 FINAL 기준으로 가져오지 않는다.

PUBLIC에서 가져올 수 있는 것은 narrative 구조, visual guide 구성, safe wording, action matrix 표현 방식이다. PUBLIC은 실패한 헛수고가 아니라 100원딜 해석을 어떻게 안전하게 말할지 검토한 우회 검증이다.

> PUBLIC에서 얻은 교훈

PUBLIC 18 hotfix는 100원딜 해석에서 다음 교훈을 남겼다. 첫째, 100원딜은 낮은 진입 비용 때문에 유입 맥락이 다를 수 있지만, 이 차이를 인과로 말하면 안 된다. 둘째, demographic action layer는 segment rule이 아니라 메시지 조정 layer다. 셋째, content signal이 너무 넓으면 대표 segment discriminator로 과장하지 말아야 한다. 넷째, promo0는 action 대상이 아니라 comparison reference로 두는 편이 안전하다.

> row count / feature set / score source 충돌

park 17x 전체 row count는 23,079이다. 그중 promo1은 11,904행, promo0는 11,175행이다. park 17x primary score source는 overall_with_promotion 전체 23,079행을 대상으로 한 LightGBM OOF score다.

반면 PUBLIC GradientBoosting promo1 final_result는 11,904행, promo0 final_result는 11,193행이며, log-retention-only input을 사용한다. PUBLIC promo0 row count는 park 15x nonpromotion_only row count 11,175와도 다르다. 따라서 park 17x와 PUBLIC numeric score를 섞으면 row scope, feature policy, model stage가 충돌한다.

> LightGBM score source 채택 이유

LightGBM은 park 17x의 primary score source다. 15x overall_with_promotion 기준에서 LightGBM OOF AUC는 0.878716, CatBoost는 0.877838, HistGradientBoosting은 0.877867다. 성능 차이만으로 final model을 확정한 것은 아니다. 더 중요한 이유는 16x payment-removed SHAP candidate plan이 overall_with_promotion LightGBM을 설명 기준으로 사용했고, 17x segmentation도 같은 기준의 OOF churn_risk를 사용했기 때문이다.

> CatBoost / GB / PUBLIC 모델을 최종 기준으로 쓰지 않는 이유

CatBoost는 15x에서 비교된 후보지만 17x primary score source가 아니다. 16x에서도 nonpromotion_only scope에는 CatBoost가 포함되지만, overall_with_promotion의 설명 기준은 LightGBM이다. 따라서 CatBoost를 final segment score 기준으로 바꾸면 17x assignment와 16x explanation basis가 어긋난다.

GB 또는 PUBLIC GradientBoosting은 PUBLIC reference branch의 산출물이다. PUBLIC은 promo0/promo1 분리와 log-retention-only 조건을 중심으로 한 emergency/reference 구조이며, final canonical model evidence가 아니다. 그러므로 PUBLIC GB score는 발표 구조 참고용이지 park 17x final interpretation의 numeric 기준이 아니다.

> payment-device 제거 결정

15x payment-device policy는 `payment_is_mobile`, `payment_is_pc`, `payment_is_android`, `payment_is_ios`를 viewing device가 아니라 payment/account/acquisition context proxy로 보라고 기록한다. 16x payment_removed_input_gate에서는 네 payment feature가 모두 input에 없고 status가 PASS다. 이번 FINAL 해석에서는 payment_device 계열을 segment rule, label, action strategy의 기준으로 사용하지 않는다. 원본 CSV나 기존 feature set을 삭제하지는 않았다. 해석 기준에서 제거했을 뿐이다.

> 17x segmentation rule 요약

- 1. `high_risk_week3_inactive_or_drop`: 3,793행, share 16.4%, churn rate 73.2%, mean churn_risk 0.733, promo1 share 59.0%
- 2. `high_risk_only_w1_or_cold_start_weak`: 265행, share 1.1%, churn rate 71.7%, mean churn_risk 0.698, promo1 share 70.6%
- 3. `high_risk_low_activity`: 511행, share 2.2%, churn rate 81.4%, mean churn_risk 0.765, promo1 share 60.9%
- 4. `medium_risk_retention_decay`: 3,195행, share 13.8%, churn rate 38.8%, mean churn_risk 0.358, promo1 share 54.6%
- 5. `content_preference_target_candidate`: 6,195행, share 26.8%, churn rate 10.1%, mean churn_risk 0.095, promo1 share 48.5%
- 6. `stable_retained_user`: 1,224행, share 5.3%, churn rate 1.1%, mean churn_risk 0.017, promo1 share 34.2%
- 7. `general_observation`: 7,896행, share 34.2%, churn rate 15.9%, mean churn_risk 0.169, promo1 share 50.6%

모든 segment name은 provisional label이다. assignment와 rule은 그대로 유지했다.

> general_observation 검토 결과

`general_observation`은 7,896행이며 전체의 34.2%다. 기술적으로는 default residual이 맞다. 그러나 내부에 행동 신호가 전혀 없는 것은 아니다. `flag_low_activity` 51.5%, `flag_cold_start_weak` 45.8%, `flag_retention_decay` 40.6%, `flag_week3_inactive` 35.3%가 관찰된다.

결론은 residual monitoring group으로 낮추는 것이다. 발표 핵심 세그먼트로 유지하지 않는다. 추천 발표명은 `추가 관찰 필요 잔여군`이다. 100원딜 문맥에서는 `100원딜 추가 관찰 필요군`으로 부를 수 있지만, final segment 확정명이 아니다.

> content_preference_target_candidate 검토 결과

`content_preference_target_candidate`는 6,195행이며 전체의 26.8%다. 내부에서 `flag_genre_focused`는 19.5%, `flag_new_movie_oriented`는 41.4%, `flag_old_movie_oriented`는 50.2%다. segment churn rate는 10.1%로 전체 churn rate 28.3%보다 낮다.

따라서 이 집단을 churn target candidate로 말하는 것은 과하다. 추천 결론은 이름 약화와 action layer 강등이다. 발표명은 `콘텐츠 큐레이션 반응 후보군`이 안전하다.

> 비중이 큰 비핵심 세그먼트와 표본 크기 제약에 대한 최종 해석

`general_observation`과 `content_preference_target_candidate`는 전체 row에서 차지하는 비중이 크기 때문에 분석 범위에서 제외하거나 단순히 버리는 방식으로 처리하면 안 된다. 두 집단은 각각 7,896행(34.2%), 6,195행(26.8%)으로 전체의 약 61%를 차지한다. 따라서 이 둘을 “강등”한다고 표현할 때 그 의미는 분석에서 제외한다는 뜻이 아니라, 고위험 이탈 방어 세그먼트에서 다른 비즈니스 역할로 재분류한다는 뜻이다.

현재 최종 세그먼트는 1~7순위로 정리되어 있다. 이 중 1~3순위는 재구매율이 낮고 평균 `churn_risk`가 높은 고위험군이며, 4순위는 중간위험군이다. 본 프로젝트의 목적이 이탈 방지와 리텐션 개입 우선순위 도출이므로, 1~4순위는 1차 분석과 비즈니스 제언의 중심에 둔다. 이들은 3주차 비활성/감소, 초기 활성화 약화, 저활동, retention decay와 같은 행동 신호를 보이므로 리텐션 개입 우선순위 후보군으로 해석한다.

반면 5~7순위는 재구매율이 상대적으로 높거나 residual 성격이 강하다. 따라서 이들을 고위험 이탈 방어 타겟처럼 말하면 안 된다. 다만 이들이 전체에서 차지하는 비중이 크기 때문에 분석에서 제외하지 않는다. 5순위 `content_preference_target_candidate`는 고위험 이탈 방어군이 아니라 콘텐츠 큐레이션 기반 정가 전환 강화군으로 해석한다. 6순위 `stable_retained_user`는 안정 유지군으로 해석한다. 7순위 `general_observation`은 명확한 대표 rule에 걸리지 않은 추가 관찰 필요 잔여군 또는 monitoring group으로 해석한다.

현재 데이터는 제공받은 분석 표본이다. 샘플링 비율과 샘플링 방식, 모집단 대표성은 이 문서만으로 확정하지 않는다. 따라서 현재 세그먼트를 다시 `promo 여부 × 성별 × 연령대`로 지나치게 세분화하면 일부 cell의 N이 급격히 작아질 수 있다. 특히 고위험군 중 일부 세그먼트는 전체 row 수 자체가 작기 때문에, 이를 다시 100원딜/비100원딜, 남성/여성, 20대/30대/40대 이상으로 나누면 통계적으로나 발표상으로 방어하기 어려운 작은 집단이 생길 수 있다.

따라서 최종 대표 세그먼트는 행동 기반 17x rule을 유지한다. `is_promotion`, age, gender는 대표 세그먼트를 다시 쪼개는 1차 rule로 사용하지 않는다. 대신 각 행동 세그먼트 안에서 100원딜 고객의 비중, 재구매율, 평균 `churn_risk`, 성별/연령대 분포를 확인하고, 이를 메시지와 개입 전략을 조정하는 action layer로 사용한다.

이 구조는 다음과 같이 정리한다.

1. 즉시 개입 우선군  
   `high_risk_week3_inactive_or_drop`, `high_risk_low_activity`, `high_risk_only_w1_or_cold_start_weak`

2. 관찰 강화군  
   `medium_risk_retention_decay`

3. 정가 전환 강화군  
   `content_preference_target_candidate`, `stable_retained_user`

4. 모니터링 / 추가분해 후보군  
   `general_observation`

이 계층은 기존 17x representative segment assignment를 변경하는 것이 아니다. 기존 segment rule과 assignment는 유지한다. 다만 발표와 비즈니스 제언에서 각 세그먼트의 역할을 다르게 부여하기 위한 해석 계층이다.

추가 파생변수를 만든다면, 새 representative segment rule로 만들지 않는다. 대신 `segment_action_tier`, `general_subsignal_tag`, `content_curation_signal_type`, `promo_action_context`, `demographic_message_variant` 같은 action layer 또는 dashboard 보조 tag로만 만든다. 이 보조 tag는 기존 세그먼트 배정을 바꾸지 않고, 각 세그먼트 안에서 어떤 메시지와 개입 전략을 설계할지 설명하기 위한 용도다.

실제 현업 적용 시에는 전체 고객 DB에서 동일 rule을 재적용해 세그먼트별 row 수, 재구매율, `churn_risk`, 캠페인 반응률을 다시 검증해야 한다. 현재 분석은 최종 캠페인 확정 타겟이 아니라, 제공받은 분석 표본을 기준으로 한 개입 우선순위 후보와 리텐션 전략 설계안이다.

금지할 표현은 다음과 같다.

- `general_observation`은 분석에서 제외한다.
- `general_observation`은 별 특징이 없는 일반 고객군이다.
- `content_preference_target_candidate`는 명확한 이탈 방어 타겟이다.
- 5~7순위는 유의하지 않다.
- 표본 데이터이므로 작은 N은 신경 쓰지 않아도 된다.
- promo, 성별, 연령대를 모두 조합해 세그먼트를 새로 확정한다.
- 새 보조 tag를 최종 segment rule처럼 사용한다.

허용되는 표현은 다음과 같다.

- 1~4순위는 이탈 방어와 리텐션 개입의 1차 우선순위다.
- 5~7순위는 버리는 것이 아니라 역할을 재분류한다.
- `general_observation`은 명확한 대표 rule에 걸리지 않은 residual이지만, 규모가 크므로 monitoring group으로 유지한다.
- `content_preference_target_candidate`는 고위험 이탈 방어군이 아니라 콘텐츠 큐레이션 기반 정가 전환 강화군으로 해석한다.
- 대표 세그먼트는 행동 기반으로 유지하고, promo·성별·연령은 메시지와 개입 전략을 조정하는 action layer로 사용한다.
- 실제 현업 적용 시에는 전체 고객 DB에서 동일 rule을 재검증해야 한다.

> 최종 세그먼트 해석 원칙

세그먼트는 원인이 아니다. 세그먼트는 day0~20 관측 행동과 OOF churn_risk를 바탕으로 만든 개입 우선순위 후보군이다. row count는 고객 수가 아니라 subscription-event row 수다. SHAP은 원인이 아니라 fitted model explanation이다. content/genre는 Movie_Master mapping proxy다. age/gender와 promo 여부는 segment rule이 아니라 해석 layer다.

> promo-aware presentation label 원칙

100원딜은 segment rule에 직접 넣지 않는다. 그러나 발표에서는 promo1을 `100원딜`로 설명하고, promo0를 `비100원딜 비교 reference`로 둔다. promo1 label은 business context를 강조하되, 인과나 확정 target 표현을 피한다.

> 100원딜 해석 강도

허용되는 표현은 `100원딜 고객은 유입 맥락과 지불 의향이 정가 고객과 다를 수 있다`, `100원딜 고객군에서 특정 행동 신호가 더 두드러질 수 있다`이다. 금지되는 표현은 `100원딜이 이탈을 유발했다`, `100원딜 고객은 어차피 이탈한다`이다.

> age/gender personalization layer

age/gender는 원인이 아니다. age/gender는 메시지, 채널, 콘텐츠 묶음을 조정하는 personalization layer다. 20대는 짧고 즉시성 있는 인기 콘텐츠, 친구추천 또는 쿠폰 메시지, 모바일 push가 적합한 후보로 둘 수 있다. 30대는 퇴근 후 또는 주말 시청 맥락, 시간 효율, 취향 기반 추천을 강조할 수 있다. 40대 이상은 명확한 혜택 안내, 장르 기반 추천, 가족 또는 주말 시청 맥락을 사용할 수 있다. 성별은 원인 해석이 아니라 메시지 variant 후보로만 둔다.

> Referral은 후속 실험 제안

Referral은 이번 17x segment rule에 넣지 않는다. 친구추천, 추천인 쿠폰, invite 메시지는 20대 또는 promo1 action strategy에서 후속 A/B test 제안으로만 둔다. 현재 산출물만으로 referral 효과를 검증했다고 말하지 않는다.

> Activation은 day0~20 기준

Activation과 retention 해석은 day0~20 관측창 기준이다. 3주차 신호는 day0~20 안의 행동 변화다. 4주차 이후 행동이나 장기 재구매 원인을 본 것처럼 말하지 않는다.

> campaign target 표현 제한

`campaign target`이라는 표현은 확정 타겟처럼 들릴 수 있다. 이번 FINAL에서는 `개입 우선순위 후보군`, `검토 후보군`, `monitoring group`, `action layer` 표현을 우선 사용한다. 실제 캠페인 집행 전에는 팀 검토와 A/B test가 필요하다.

> 다음 작업

다음 작업은 새 모델 실행이 아니다. 발표용 storyline에서 segment label을 사용자 승인 기준으로 확정하고, dashboard에는 residual과 content action layer의 caution을 명시해야 한다. general_observation은 후속 decomposition 후보로 남긴다. content_preference_target_candidate는 추천 action layer로 낮춘다. referral은 후속 실험 설계로만 둔다.

> 아직 사용자 승인 필요한 항목

첫째, 발표용 segment label 확정이 필요하다. 둘째, content_preference_target_candidate를 `콘텐츠 큐레이션 반응 후보군`으로 약화할지 승인해야 한다. 셋째, general_observation을 `추가 관찰 필요 잔여군`으로 낮출지 승인해야 한다. 넷째, 100원딜 중심 표현의 강도를 어디까지 허용할지 승인해야 한다. 다섯째, business action matrix의 메시지 variant를 실제 발표에 넣을지 승인해야 한다.

> 절대 하지 말아야 할 표현

- 100원딜이 이탈을 유발했다.
- 3주차 시청량 감소가 이탈의 원인이다.
- SHAP이 원인을 증명했다.
- age/gender가 이탈 원인이다.
- 세그먼트가 최종 캠페인 타겟이다.
- content_preference_target_candidate는 명확한 콘텐츠 취향 세그먼트다.
- general_observation은 일반 고객군이라서 해석이 끝났다.
- PUBLIC이 final canonical pipeline이다.
- row count를 고객 수 또는 unique customer 수라고 말한다.
