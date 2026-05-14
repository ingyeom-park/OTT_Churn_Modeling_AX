# 07c Corrected TRUE SHAP Interpretation Report

## 1. TRUE SHAP Status
- TRUE SHAP was successfully computed.
- SHAP version: 0.51.0.
- Python executable: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe`.

## 2. Corrected Official Model Explained
- Model: HistGradientBoostingClassifier.
- Feature set: `pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence`.
- Window: w1_3.

## 3. Model Reconstruction
- Reconstructed AUC: 0.862939.
- Stage 06c2 recorded AUC: 0.862939.
- Absolute difference: 0.0000000000.
- Train/test USER_KEY overlap: 0.

## 4. Top SHAP Features
- w1_3_week3_watch_time (weekly_usage_pattern): mean abs SHAP 0.831380.
- w1_3_genre_ratio_drama (genre_ratio_proxy): mean abs SHAP 0.319754.
- w1_3_week1_watch_time (weekly_usage_pattern): mean abs SHAP 0.300214.
- w1_3_week2_watch_time (weekly_usage_pattern): mean abs SHAP 0.287447.
- is_promotion_bin (membership_context): mean abs SHAP 0.269955.
- w1_3_genre_ratio_animation_family (genre_ratio_proxy): mean abs SHAP 0.260305.
- w1_3_genre_ratio_thriller_crime (genre_ratio_proxy): mean abs SHAP 0.216430.
- w1_3_genre_ratio_romance (genre_ratio_proxy): mean abs SHAP 0.215474.
- w1_3_genre_ratio_action_adventure (genre_ratio_proxy): mean abs SHAP 0.170894.
- w1_3_avg_watch_time_per_session (simple_usage_volume): mean abs SHAP 0.157880.

## 5. Top SHAP Feature Families
- weekly_usage_pattern: mean abs SHAP 1.506672.
- genre_ratio_proxy: mean abs SHAP 1.432598.
- membership_context: mean abs SHAP 0.509841.
- simple_usage_volume: mean abs SHAP 0.322993.
- release_month_proxy: mean abs SHAP 0.038996.

## 6. Features Pushing Toward Repurchase
- w1_3_week1_watch_time: mean SHAP 0.007779.
- w1_3_week2_watch_time: mean SHAP 0.027044.
- w1_3_genre_ratio_animation_family: mean SHAP 0.006039.
- w1_3_week3_sessions: mean SHAP 0.007111.
- w1_3_genre_ratio_sf_fantasy: mean SHAP 0.000002.
- w1_3_week1_sessions: mean SHAP 0.000101.
- w1_3_week2_sessions: mean SHAP 0.002211.

## 7. Features Pushing Toward Churn Risk
- w1_3_week3_watch_time: mean SHAP -0.040797.
- w1_3_genre_ratio_drama: mean SHAP -0.002884.
- is_promotion_bin: mean SHAP -0.000842.
- w1_3_genre_ratio_thriller_crime: mean SHAP -0.004243.
- w1_3_genre_ratio_romance: mean SHAP -0.007750.
- w1_3_genre_ratio_action_adventure: mean SHAP -0.005753.
- w1_3_avg_watch_time_per_session: mean SHAP -0.021933.
- w1_3_unique_contents: mean SHAP -0.018829.
- max_screen_num: mean SHAP -0.000873.
- age_num: mean SHAP -0.002455.

## 8. Difference From Old 07r/06h SHAP
- 07c explains the corrected official Stage 06c2 model and corrected v2c dataset.
- Old 07r and 06h SHAP outputs are historical/provisional only because they were based on earlier pre-02c or pre-06c2 data.
- Use `07c_previous_shap_comparison.csv` only for historical comparison, not final evidence.

## 9. Figures To Share
- park.ingyeom/reports/figures/07c_v2_corrected_true_shap_interpretation/07c_churn_risk_top_decile_shap_push.png
- park.ingyeom/reports/figures/07c_v2_corrected_true_shap_interpretation/07c_shap_beeswarm_red_blue_corrected_official.png
- park.ingyeom/reports/figures/07c_v2_corrected_true_shap_interpretation/07c_shap_feature_family_importance_corrected_official.png
- park.ingyeom/reports/figures/07c_v2_corrected_true_shap_interpretation/07c_shap_global_bar_corrected_official.png

## 10. Must Not Be Claimed
- Do not claim causality.
- Do not claim ROI, profit, retention lift, or business simulation results.
- Do not claim segmentation results from Stage 07c.
- Do not claim old 07r or 06h SHAP as final evidence.
- Do not reverse the SHAP direction. Positive SHAP means higher repurchase score, not higher churn risk.
- Do not claim w1_4 as early-warning evidence.
