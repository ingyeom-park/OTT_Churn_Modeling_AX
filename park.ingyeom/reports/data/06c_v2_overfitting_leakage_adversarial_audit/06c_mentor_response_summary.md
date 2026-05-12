# 06c 멘토 지적 대응 요약

## 멘토님의 과적합 지적을 어떻게 검증했는가
AUC 0.87~0.90이 너무 높다는 지적을 방어하지 않고, 같은 Stage 06 split을 기준으로 성능을 깨는 방향의 감사를 수행했습니다. 구체적으로 관측창 축소, 상위 피처 제거, 콘텐츠 proxy 분해, 단일 피처 AUC, 하위그룹 일반화, 더 어려운 split, train/test 분포 차이, 중복 feature vector, forbidden feature 재점검, calibration과 decile 안정성을 확인했습니다.

## 어떤 검증은 통과했는가
Stage 06b의 target shuffle AUC는 0.4672였고, repeated GroupShuffleSplit 평균 AUC는 0.8751였습니다. Stage 06c에서도 w1_3 보수 모델 feature 안에 end_date, duration_days, watch_date, watch_day, USER_KEY, USER_NUM, MOVIE_NUM, is_repurchase, w1_4 feature가 들어가지 않았음을 다시 확인했습니다.

## 어떤 부분은 여전히 위험한가
가장 큰 위험은 직접 누수라기보다 target-adjacent behavior proxy입니다. 특히 3주차 시청량, 첫 시청일, 마지막 시청일, 주차별 ratio, 주차 간 변화량은 재구독 의사결정 시점에 가까운 행동 신호일 수 있습니다. 콘텐츠 watch_time과 session_count도 순수 취향이라기보다 사용량 강도를 다시 표현할 수 있습니다.

## 그래서 공식 발표에는 어떤 성능 수치를 쓰는 것이 가장 보수적인가
- A_full_model_result: AUC 0.8705, window w1_3, model HistGradientBoostingClassifier, mentor_safe N.
- B_conservative_model_result: AUC 0.8659, window w1_3, model HistGradientBoostingClassifier, mentor_safe Y_WITH_CAVEATS.
- C_ultra_conservative_model_result: AUC 0.6506, window w1_2_proxy, model LogisticRegression, mentor_safe Y_FOR_MENTOR_RESPONSE.

## 0.87/0.90을 그대로 주장하지 않는다면 어떤 수치를 주장할 것인가
0.90은 w1_4 late-period 결과이므로 조기 예측 성능으로 주장하지 않는 편이 안전합니다. 0.87 역시 full w1_3 결과로 제시하되, 멘토 대응에서는 target-adjacent 피처를 제거한 B안 또는 w1_2 proxy 기반 C안을 함께 제시하는 것이 더 보수적입니다.

## w1_3와 w1_4를 어떻게 구분해서 설명할 것인가
w1_3는 day 0~20 기반 early-observation에 가까운 모델입니다. w1_4는 day 0~27까지 포함하므로 종료 직전 행동을 많이 반영한 late-period/end-of-period 비교 모델입니다. 따라서 w1_4의 높은 AUC는 모델이 운영적으로 더 빨리 개입할 수 있다는 뜻이 아니라, 더 늦은 행동을 보면 구분력이 커진다는 뜻으로 설명해야 합니다.

## 최종 보수 판단
Stage 06c의 최종 분류는 `target_adjacent_but_not_direct_leakage`입니다. 직접 누수라고 단정할 근거는 부족하지만, 현재 높은 AUC를 무비판적으로 발표용 대표 성능으로 쓰기에는 위험합니다.
