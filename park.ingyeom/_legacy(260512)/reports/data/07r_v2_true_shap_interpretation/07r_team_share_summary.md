# 07r True SHAP Team Share Summary

## Primary Model
- w1_3 / membership_plus_usage_content_w1_3_without_churn_prevented / HistGradientBoostingClassifier.
- AUC explained: 0.8705.

## Target And Score Direction
- Y -> 1 means repurchase; N -> 0 means non-repurchase / churn risk.
- Positive SHAP pushes toward higher repurchase margin and lower churn risk.
- Negative SHAP pushes away from repurchase and toward higher churn risk.

## Top 10 SHAP Features
- w1_3_week3_watch_time: mean abs SHAP 0.619701, family usage
- w1_3_w2_minus_w1_watch_time: mean abs SHAP 0.264763, family usage
- w1_3_week1_ratio: mean abs SHAP 0.227194, family usage
- price: mean abs SHAP 0.191771, family membership
- w1_3_first_watch_rel_day: mean abs SHAP 0.173888, family usage
- w1_3_genre_ratio_thriller_crime: mean abs SHAP 0.164927, family genre
- w1_3_genre_ratio_animation_family: mean abs SHAP 0.127053, family genre
- w1_3_genre_ratio_drama: mean abs SHAP 0.113679, family genre
- w1_3_genre_session_count_drama: mean abs SHAP 0.109960, family genre
- w1_3_genre_ratio_action_adventure: mean abs SHAP 0.109491, family genre

## Top Feature Families
- usage: 2.154410
- genre: 1.346995
- membership: 0.340206
- release_month: 0.040568
- content: 0.004311

## Interpretation Cautions
- SHAP is model explanation, not causality.
- Content features are genre and ott_release_month proxies only.
- w1_4 comparison is late-period/end-of-period, not early-warning.

## Recommended Figures
- park.ingyeom/reports/figures/07r_v2_true_shap_interpretation/07r_churn_risk_top_decile_shap_push.png
- park.ingyeom/reports/figures/07r_v2_true_shap_interpretation/07r_feature_family_shap_importance_conservative_w1_3.png
- park.ingyeom/reports/figures/07r_v2_true_shap_interpretation/07r_shap_beeswarm_red_blue_conservative_w1_3.png
- park.ingyeom/reports/figures/07r_v2_true_shap_interpretation/07r_shap_global_bar_conservative_w1_3.png
- park.ingyeom/reports/figures/07r_v2_true_shap_interpretation/07r_w1_3_vs_w1_4_family_importance.png
