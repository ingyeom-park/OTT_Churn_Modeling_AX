# 08_v2 Segmentation Strategy Report

## Scope
- Stage 08 created SHAP-informed segmentation strategy artifacts only.
- No business simulation, Optuna, tuning, raw modification, legacy modification, or `_data` output was created.
- Stage 07r true SHAP outputs are used as final XAI evidence. Stage 07 fallback is not used as final evidence.

## Model And Score
- Segmentation model: w1_3 / membership_plus_usage_content_w1_3_without_churn_prevented / HistGradientBoostingClassifier.
- `is_repurchase`: Y -> 1, N -> 0.
- `repurchase_score = P(is_repurchase = Y)`.
- `churn_risk_score = 1 - repurchase_score`; high score means high predicted non-repurchase risk.
- w1_3 is primary because it is closer to early intervention timing. w1_4 is late-period/end-of-period only.

## Churn-Risk Bands
- top_10_highest_risk: n=478, churn rate=0.785, lift=2.73, captured churners=375.
- risk_10_30: n=956, churn rate=0.591, lift=2.06, captured churners=565.
- risk_30_60: n=1433, churn rate=0.256, lift=0.89, captured churners=367.
- bottom_40_lowest_risk: n=1910, churn rate=0.034, lift=0.12, captured churners=64.

## SHAP-Informed Rule Segments
- Created non-exclusive segment flags and one documented hierarchical assignment.
- Largest and highest-risk segments are available in `08_v2_hierarchical_segment_summary_holdout.csv`.
- Segment actions are mapped to Stage 07r SHAP feature families in `08_v2_segment_shap_evidence_map.csv`.

## Business Actionability
- 최상위 이탈위험군 (top_decile_high_churn_risk): 고위험 모니터링 및 개인화 리텐션 메시지 / readiness=plausible_but_cautioned / evidence=strong.
- 초기 미시청/저관여군 (low_or_no_early_engagement): no-watch onboarding 및 초기 콘텐츠 추천 / readiness=safe_to_report / evidence=strong.
- 3주차 집중 시청군 (late_heavy_week3_intensive): week3 타깃 메시지와 이어보기 추천 / readiness=safe_to_report / evidence=strong.
- 시작 지연군 (delayed_start): 가입 직후 탐색 도움 및 첫 시청 유도 / readiness=plausible_but_cautioned / evidence=strong.
- 스릴러/범죄 선호군 (genre_affinity_thriller_crime): 스릴러/범죄 후속 콘텐츠 추천 / readiness=plausible_but_cautioned / evidence=strong.
- 애니/가족 선호군 (genre_affinity_animation_family): 가족/애니 continuation cue / readiness=plausible_but_cautioned / evidence=strong.
- 드라마 선호군 (genre_affinity_drama): 드라마 이어보기 및 신작 알림 / readiness=plausible_but_cautioned / evidence=strong.
- 액션/어드벤처 선호군 (genre_affinity_action_adventure): 액션/어드벤처 continuation recommendation / readiness=plausible_but_cautioned / evidence=strong.
- 초기 루틴 형성군 (early_routine_stable): 루틴 유지형 알림과 이어보기 큐 / readiness=safe_to_report / evidence=strong.
- 가격/프로모션 민감 가능군 (high_price_or_promotion_sensitive): 요금제/downsell 안내 후보 / readiness=plausible_but_cautioned / evidence=strong.
- 2주차 상승 관여군 (week2_surge_users): 관심 상승 구간 후속 콘텐츠 추천 / readiness=safe_to_report / evidence=strong.
- 일반 기타군 (general_other): 일반 콘텐츠 추천 및 관찰 유지 / readiness=do_not_claim_yet / evidence=weak.

## Claims Not To Make
- Do not claim SHAP proves causal intervention effects.
- Do not claim changing a feature will cause repurchase.
- Do not present w1_4 as early-warning evidence.
- Do not calculate or claim financial impact in Stage 08.

## Stage 09 Guidance
- Use holdout segment counts, churn rates, top-decile capture, and action hypotheses as inputs to Stage 09 business simulation.
- Stage 09 should explicitly test business assumptions such as reach, cost, response rate, and retention lift.

## Internal Critique and Segment Reliability Review
- Segments with n < 100 in holdout: ['early_routine_stable', 'general_other', 'week2_surge_users'].
- High-overlap flag pairs: ['seg_low_or_no_early_engagement x seg_top_decile_high_churn_risk: 0.80', 'seg_delayed_start x seg_high_price_or_promotion_sensitive: 0.82', 'seg_early_routine_stable x seg_high_price_or_promotion_sensitive: 0.81', 'seg_genre_affinity_thriller_crime x seg_high_price_or_promotion_sensitive: 0.81', 'seg_genre_affinity_animation_family x seg_high_price_or_promotion_sensitive: 0.80', 'seg_genre_affinity_drama x seg_high_price_or_promotion_sensitive: 0.81', 'seg_genre_affinity_action_adventure x seg_high_price_or_promotion_sensitive: 0.79', 'seg_high_price_or_promotion_sensitive x seg_top_decile_high_churn_risk: 0.88', 'seg_high_price_or_promotion_sensitive x seg_low_or_no_early_engagement: 0.81', 'seg_high_price_or_promotion_sensitive x seg_late_heavy_week3_intensive: 0.79', 'seg_high_price_or_promotion_sensitive x seg_week2_surge_users: 0.80'].
- Threshold critique: All thresholds are quantile-based, but quartile cutoffs are still heuristic business rules.; Risk bands are percentile bands and should not be interpreted as calibrated probability tiers.
- Weakly supported actions: ['general_other'].
- Presentation-ready segments: ['top_decile_high_churn_risk', 'low_or_no_early_engagement', 'late_heavy_week3_intensive', 'delayed_start', 'genre_affinity_thriller_crime', 'genre_affinity_animation_family', 'genre_affinity_drama', 'genre_affinity_action_adventure', 'early_routine_stable', 'high_price_or_promotion_sensitive', 'week2_surge_users'].
- Exclude or downplay in final reporting: ['general_other'].
