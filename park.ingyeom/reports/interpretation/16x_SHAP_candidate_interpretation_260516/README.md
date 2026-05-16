# 16x_SHAP_candidate_interpretation_260516

Purpose: SHAP-based model interpretation for candidate models selected from 12x model-family comparison and 14x lightweight tuning. This is not final model selection, Optuna, segmentation, feature removal, thresholding, or causal analysis.

Interpretation unit: row-level / subscription-event-level. Do not describe this as unique-user analysis.

Class direction: target=is_repurchase, positive class=is_repurchase=1, repurchase_score=P(is_repurchase=1), churn_risk=1-repurchase_score. SHAP signs are interpreted only as directions for repurchase_score.

Important wording: model explanation on fitted candidate model, not causal and not OOF explanation.

## Input paths
- 06x: C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\06x_dataset_generation_260515
- 07x: C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\07x_feature_mapping_AARRR_260515
- 10x: C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\10x_feature_distribution_redundancy_pre_audit_260516
- 12x: C:\Code\ott-churn-prediction\park.ingyeom\reports\models\12x_model_family_comparison_260516
- 14x: C:\Code\ott-churn-prediction\park.ingyeom\reports\models\14x_lightweight_candidate_tuning_260516

## Candidate models
- expanded_feature_set / overall_with_promotion / LightGBM: 14x_tuned; 14x use_for_16x_SHAP_candidate=review_candidate; reference_candidate_for_review
- expanded_feature_set / overall_without_promotion / LightGBM: 14x_tuned; 14x use_for_16x_SHAP_candidate=review_candidate; reference_candidate_for_review
- expanded_feature_set / promotion_only / HistGradientBoosting: 14x_tuned; 14x use_for_16x_SHAP_candidate=review_candidate; reference_candidate_for_review
- expanded_feature_set / nonpromotion_only / LightGBM: 14x_tuned; 14x use_for_16x_SHAP_candidate=review_candidate; reference_candidate_for_review
- conservative_safe_22 / overall_with_promotion / CatBoost: 12x_fixed; conservative_safe_22 reference: minimum one overall scope; 12x recommended_for_16x_SHAP used

SHAP sample policy: if scope row count <= 5000, use all rows; otherwise deterministic stratified sample up to 5000 rows with random_state=42. Sample row IDs are saved in 16x_SHAP_sample_row_ids.csv.

Korean font setting: selected_font=Malgun Gothic; axes.unicode_minus=False. Font test figure: 16x_fig_00_korean_font_test.png.

## Main SHAP results
- expanded_feature_set / nonpromotion_only / LightGBM: rank 1 watch_time_min_w3, family=usage_retention_behavior, mean_abs_shap=0.502701
- expanded_feature_set / overall_with_promotion / LightGBM: rank 1 watch_time_min_w3, family=usage_retention_behavior, mean_abs_shap=0.420083
- expanded_feature_set / promotion_only / HistGradientBoosting: rank 1 watch_time_min_w3, family=usage_retention_behavior, mean_abs_shap=0.412504
- expanded_feature_set / overall_without_promotion / LightGBM: rank 1 retention_w2_ratio, family=usage_retention_behavior, mean_abs_shap=0.396722
- expanded_feature_set / overall_with_promotion / LightGBM: rank 2 retention_w2_ratio, family=usage_retention_behavior, mean_abs_shap=0.386725
- expanded_feature_set / overall_without_promotion / LightGBM: rank 2 retention_w3_ratio, family=usage_retention_behavior, mean_abs_shap=0.377039
- expanded_feature_set / overall_without_promotion / LightGBM: rank 3 watch_time_min_w3, family=usage_retention_behavior, mean_abs_shap=0.375039
- expanded_feature_set / nonpromotion_only / LightGBM: rank 2 retention_w3_ratio, family=usage_retention_behavior, mean_abs_shap=0.366799
- expanded_feature_set / overall_with_promotion / LightGBM: rank 3 is_promotion, family=acquisition_split_key, mean_abs_shap=0.362433
- expanded_feature_set / overall_with_promotion / LightGBM: rank 4 retention_w3_ratio, family=usage_retention_behavior, mean_abs_shap=0.354038
- expanded_feature_set / nonpromotion_only / LightGBM: rank 3 retention_w2_ratio, family=usage_retention_behavior, mean_abs_shap=0.343128
- expanded_feature_set / overall_without_promotion / LightGBM: rank 4 drama_ratio, family=content_preference_context, mean_abs_shap=0.336888

## Feature family interpretation
- expanded_feature_set / nonpromotion_only: usage_retention_behavior, AARRR=Retention, redundancy_family=week_watch_level_change_ratio_family, sum_mean_abs_shap=1.783295, top_features=watch_time_min_w3; retention_w3_ratio; retention_w2_ratio; diff_between_w2_w1; diff_between_w3_w2
- expanded_feature_set / overall_without_promotion: content_preference_context, AARRR=Retention_context, redundancy_family=genre_ratio_compositional_family, sum_mean_abs_shap=1.681760, top_features=drama_ratio; family_animation_ratio; romance_ratio; thriller_crime_ratio; action_adventure_ratio
- expanded_feature_set / overall_with_promotion: usage_retention_behavior, AARRR=Retention, redundancy_family=week_watch_level_change_ratio_family, sum_mean_abs_shap=1.669166, top_features=watch_time_min_w3; retention_w2_ratio; retention_w3_ratio; diff_between_w2_w1; diff_between_w3_w2
- expanded_feature_set / overall_without_promotion: usage_retention_behavior, AARRR=Retention, redundancy_family=week_watch_level_change_ratio_family, sum_mean_abs_shap=1.657475, top_features=retention_w2_ratio; retention_w3_ratio; watch_time_min_w3; diff_between_w2_w1; diff_between_w3_w2
- expanded_feature_set / overall_with_promotion: content_preference_context, AARRR=Retention_context, redundancy_family=genre_ratio_compositional_family, sum_mean_abs_shap=1.632498, top_features=drama_ratio; family_animation_ratio; romance_ratio; thriller_crime_ratio; action_adventure_ratio
- expanded_feature_set / nonpromotion_only: content_preference_context, AARRR=Retention_context, redundancy_family=genre_ratio_compositional_family, sum_mean_abs_shap=1.504820, top_features=drama_ratio; family_animation_ratio; thriller_crime_ratio; romance_ratio; action_adventure_ratio
- expanded_feature_set / promotion_only: usage_retention_behavior, AARRR=Retention, redundancy_family=week_watch_level_change_ratio_family, sum_mean_abs_shap=1.495126, top_features=watch_time_min_w3; retention_w2_ratio; retention_w3_ratio; diff_between_w2_w1; diff_between_w3_w2
- conservative_safe_22 / overall_with_promotion: usage_retention_behavior, AARRR=Retention, redundancy_family=week_watch_level_change_ratio_family, sum_mean_abs_shap=1.290311, top_features=watch_time_min_w3; retention_w3_ratio; retention_w2_ratio; diff_between_w2_w1; diff_between_w3_w2

## 10x redundancy caveat
High VIF and correlation clusters mean individual feature importance can be split across related variables. Use feature family or redundancy cluster wording; no feature removal was performed and user approval remains required for removal decisions.

## EDA/modeling alignment
Use SHAP together with 10x redundancy diagnostics, 12x candidate comparison, 14x tuning sensitivity, and prior EDA. A repeated week-3 usage or retention signal can be described as a common descriptive/model-explanation signal, not as an intervention effect.

## Forbidden interpretations
- Do not say SHAP identified causes.
- Do not say changing one feature will raise repurchase.
- Do not say promotion caused churn or retention.
- Do not use top-k churn_risk as a campaign threshold.
- Do not call this final model selection or unique-user analysis.

Next step: 17x segmentation design.

## 16x figure layout hotfix 260516

This hotfix improves figure layout only. It does not recalculate SHAP values, refit models, run Optuna, remove features, create new features, perform segmentation, or select a campaign threshold.

Changed figure:
- 16x_fig_scope_top10_SHAP_comparison.png was redrawn from the existing 16x_scope_comparison_top_features.csv because the original multi-panel layout could show overlapping subplot titles, axis labels, and margins in presentation view.

Presentation recommendation:
- Use 16x_fig_scope_top10_SHAP_comparison.png as the scope-comparison slide figure after this hotfix.
- Keep SHAP wording as model explanation for repurchase_score, not causality.
