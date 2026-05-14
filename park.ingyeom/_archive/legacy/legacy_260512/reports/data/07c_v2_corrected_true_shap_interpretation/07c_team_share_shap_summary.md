# 07c Corrected TRUE SHAP Team Share Summary

## Status
- TRUE SHAP was computed for the corrected official Stage 06c2 model only.
- Model: HistGradientBoostingClassifier.
- Feature set: `pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence`.
- Reconstructed AUC: 0.862939; Stage 06c2 AUC: 0.862939; difference: 0.0000000000.

## Direction
- Target `is_repurchase_label`: 1 = repurchase, 0 = non-repurchase / churn risk.
- Positive SHAP pushes toward `repurchase_score`.
- Negative SHAP pushes toward higher churn risk.

## Top SHAP Features
- w1_3_week3_watch_time: 0.831380 (weekly_usage_pattern)
- w1_3_genre_ratio_drama: 0.319754 (genre_ratio_proxy)
- w1_3_week1_watch_time: 0.300214 (weekly_usage_pattern)
- w1_3_week2_watch_time: 0.287447 (weekly_usage_pattern)
- is_promotion_bin: 0.269955 (membership_context)
- w1_3_genre_ratio_animation_family: 0.260305 (genre_ratio_proxy)
- w1_3_genre_ratio_thriller_crime: 0.216430 (genre_ratio_proxy)
- w1_3_genre_ratio_romance: 0.215474 (genre_ratio_proxy)
- w1_3_genre_ratio_action_adventure: 0.170894 (genre_ratio_proxy)
- w1_3_avg_watch_time_per_session: 0.157880 (simple_usage_volume)

## Feature Families
- weekly_usage_pattern: 1.506672
- genre_ratio_proxy: 1.432598
- membership_context: 0.509841
- simple_usage_volume: 0.322993
- release_month_proxy: 0.038996

## Recommended Figures
- park.ingyeom/reports/figures/07c_v2_corrected_true_shap_interpretation/07c_churn_risk_top_decile_shap_push.png
- park.ingyeom/reports/figures/07c_v2_corrected_true_shap_interpretation/07c_shap_beeswarm_red_blue_corrected_official.png
- park.ingyeom/reports/figures/07c_v2_corrected_true_shap_interpretation/07c_shap_feature_family_importance_corrected_official.png
- park.ingyeom/reports/figures/07c_v2_corrected_true_shap_interpretation/07c_shap_global_bar_corrected_official.png

## Do Not Claim
- Do not claim causality, ROI, intervention lift, or business simulation results.
- Do not use old 07r or 06h SHAP as final evidence.
- Do not treat w1_4 as early-warning evidence.
