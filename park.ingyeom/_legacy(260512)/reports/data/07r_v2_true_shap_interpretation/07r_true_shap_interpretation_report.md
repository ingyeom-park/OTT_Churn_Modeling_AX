# 07r_v2 True SHAP Interpretation Report

## Scope
- Stage 07r computed true SHAP values and supersedes the Stage 07 fallback XAI outputs.
- No segmentation, business simulation, Optuna, tuning, raw modification, or `_data` output was created.
- Python executable: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe`.
- SHAP version: `0.51.0`.

## True SHAP Status
- True SHAP was successfully computed for the primary conservative model.
- The primary model explained is w1_3 / membership_plus_usage_content_w1_3_without_churn_prevented / HistGradientBoostingClassifier.
- Reconstructed ROC AUC: 0.8705; Stage 06 difference: 0.0000.

## Target And Score Direction
- `is_repurchase`: Y -> 1, N -> 0.
- `repurchase_score = P(is_repurchase = Y)`.
- `churn_risk_score = 1 - repurchase_score`.
- Positive SHAP contribution increases the repurchase margin and implies lower churn-risk direction.
- Negative SHAP contribution lowers the repurchase margin and implies higher churn-risk direction.

## Top Global SHAP Drivers
- w1_3_week3_watch_time (usage): mean abs SHAP 0.619701.
- w1_3_w2_minus_w1_watch_time (usage): mean abs SHAP 0.264763.
- w1_3_week1_ratio (usage): mean abs SHAP 0.227194.
- price (membership): mean abs SHAP 0.191771.
- w1_3_first_watch_rel_day (usage): mean abs SHAP 0.173888.
- w1_3_genre_ratio_thriller_crime (genre): mean abs SHAP 0.164927.
- w1_3_genre_ratio_animation_family (genre): mean abs SHAP 0.127053.
- w1_3_genre_ratio_drama (genre): mean abs SHAP 0.113679.
- w1_3_genre_session_count_drama (genre): mean abs SHAP 0.109960.
- w1_3_genre_ratio_action_adventure (genre): mean abs SHAP 0.109491.

## Feature Families
- usage: mean abs SHAP 2.154410.
- genre: mean abs SHAP 1.346995.
- membership: mean abs SHAP 0.340206.
- release_month: mean abs SHAP 0.040568.
- content: mean abs SHAP 0.004311.

## Stage 07 Fallback Comparison
- Stage 07 fallback used permutation importance and coefficient-based interpretation because SHAP was unavailable.
- Stage 07r uses true SHAP values and should be used for final presentation and team sharing.
- Stage 07 remains only as an audit trail.

## Content Feature Caution
- v2 content metadata is limited to genre and ott_release_month-derived proxies.
- Do not imply country, rating, runtime, actor, director, Wavve, or KOBIS metadata.

## Stage 08 Use
- Safe to use in Stage 08: conservative w1_3 churn-risk scores and top SHAP feature groups as descriptive segmentation candidates.
- Cautioned: usage/content findings are predictive associations, not causal levers.
- Do not claim: causal drivers, that changing a behavior causes repurchase, or that w1_4 is early-warning.

## Recommended Team Figures
- park.ingyeom/reports/figures/07r_v2_true_shap_interpretation/07r_churn_risk_top_decile_shap_push.png
- park.ingyeom/reports/figures/07r_v2_true_shap_interpretation/07r_feature_family_shap_importance_conservative_w1_3.png
- park.ingyeom/reports/figures/07r_v2_true_shap_interpretation/07r_shap_beeswarm_red_blue_conservative_w1_3.png
- park.ingyeom/reports/figures/07r_v2_true_shap_interpretation/07r_shap_global_bar_conservative_w1_3.png
- park.ingyeom/reports/figures/07r_v2_true_shap_interpretation/07r_w1_3_vs_w1_4_family_importance.png
