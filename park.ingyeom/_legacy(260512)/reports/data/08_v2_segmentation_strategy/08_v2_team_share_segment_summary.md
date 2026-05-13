# 08_v2 Team Share Segment Summary

## Primary Model And Score
- Primary model: w1_3 / membership_plus_usage_content_w1_3_without_churn_prevented / HistGradientBoostingClassifier.
- `churn_risk_score = 1 - repurchase_score`; high score means high predicted non-repurchase risk.
- Stage 07r true SHAP is the XAI basis.

## Top Risk Bands
- top_10_highest_risk: n=478, churn rate=0.785, lift=2.73.
- risk_10_30: n=956, churn rate=0.591, lift=2.06.
- risk_30_60: n=1433, churn rate=0.256, lift=0.89.
- bottom_40_lowest_risk: n=1910, churn rate=0.034, lift=0.12.

## Final Segments
- top_decile_high_churn_risk: n=478, churn rate=0.785, lift=2.73, action=고위험 모니터링 및 개인화 리텐션 메시지.
- early_routine_stable: n=91, churn rate=0.505, lift=1.76, action=루틴 유지형 알림과 이어보기 큐.
- genre_affinity_action_adventure: n=163, churn rate=0.362, lift=1.26, action=액션/어드벤처 continuation recommendation.
- low_or_no_early_engagement: n=1273, churn rate=0.321, lift=1.12, action=no-watch onboarding 및 초기 콘텐츠 추천.
- genre_affinity_thriller_crime: n=444, churn rate=0.320, lift=1.11, action=스릴러/범죄 후속 콘텐츠 추천.
- general_other: n=22, churn rate=0.273, lift=0.95, action=일반 콘텐츠 추천 및 관찰 유지.
- high_price_or_promotion_sensitive: n=147, churn rate=0.252, lift=0.88, action=요금제/downsell 안내 후보.
- genre_affinity_drama: n=282, churn rate=0.223, lift=0.78, action=드라마 이어보기 및 신작 알림.
- genre_affinity_animation_family: n=401, churn rate=0.217, lift=0.76, action=가족/애니 continuation cue.
- delayed_start: n=311, churn rate=0.186, lift=0.65, action=가입 직후 탐색 도움 및 첫 시청 유도.
- late_heavy_week3_intensive: n=1148, churn rate=0.078, lift=0.27, action=week3 타깃 메시지와 이어보기 추천.
- week2_surge_users: n=17, churn rate=0.000, lift=0.00, action=관심 상승 구간 후속 콘텐츠 추천.

## Recommended Figures
- park.ingyeom/reports/figures/08_v2_segmentation_strategy/08_v2_risk_band_churn_rate_holdout.png
- park.ingyeom/reports/figures/08_v2_segmentation_strategy/08_v2_hierarchical_segment_size_and_churn.png
- park.ingyeom/reports/figures/08_v2_segmentation_strategy/08_v2_segment_shap_evidence_heatmap.png
- park.ingyeom/reports/figures/08_v2_segmentation_strategy/08_v2_top_decile_churn_capture.png

## Presentation Cautions
- Segments are descriptive and prediction-oriented, not causal.
- Do not claim financial impact in Stage 08.
- w1_4 is late-period only and is not the primary segmentation basis.
