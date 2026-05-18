# 11x baseline growth comparison

## Purpose
11x compares `conservative_safe_22` and `expanded_feature_set` baseline performance using the canonical 06x/07x/10x chain. It is not final model selection, Optuna, SHAP, segmentation, feature removal, or causal/business thresholding.

## Notebook reuse
Archived reference notebook found: `C:\Code\ott-churn-prediction\park.ingyeom\_archive\logs\r00_prev\pre13b_ref\notebook\11b_baseline_growth_history_ladder_fix_260514\11b_baseline_growth_history_ladder_fix_260514.ipynb`. A copy was placed at the 11x notebook path before this simplified 11x notebook was written for the current scope.

## Inputs
- 06x: `C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\06x_dataset_generation_260515`
- 07x: `C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\07x_feature_mapping_AARRR_260515`
- 10x: `C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\10x_feature_distribution_redundancy_pre_audit_260516`

## Feature sets
- `conservative_safe_22`: 06x conservative dataset features.
- `expanded_feature_set`: 06x expanded dataset features. High VIF/redundancy from 10x is preserved as caution, not feature removal.

## Dataset scopes
- overall_without_promotion: all rows, `is_promotion` excluded.
- overall_with_promotion: all rows, `is_promotion` included when available.
- promotion_only: `is_promotion == 1`, `is_promotion` excluded.
- nonpromotion_only: `is_promotion == 0`, `is_promotion` excluded.

## Models and CV
- Models: DummyPrior, LogisticRegression, HistGradientBoosting, RandomForest.
- CV: StratifiedGroupKFold, n_splits=5, random_state=42, group key=`USER_KEY`.
- OOF predictions are validation-fold predictions only.

## Main result files
- `11x_model_summary_by_scope.csv`
- `11x_conservative_vs_expanded_comparison.csv`
- `11x_oof_predictions.csv`
- `11x_operating_metrics_at_k.csv`
- `11x_calibration_decile_summary.csv`
- `11x_redundancy_caveat_handoff.csv`

## Key cautions
- VIF/redundancy does not justify feature removal in 11x.
- LogisticRegression coefficient interpretation is limited under high VIF.
- Tree/boosting models are not excluded solely because of high VIF.
- Later SHAP should be interpreted by feature family/redundancy cluster.
- Top-k churn risk is diagnostic, not a campaign threshold.
- Results are row-level / subscription-event-level, not unique-user analysis.

## Next step
12x model family comparison.
