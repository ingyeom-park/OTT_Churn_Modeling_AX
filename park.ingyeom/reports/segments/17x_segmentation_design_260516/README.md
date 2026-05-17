# 17x_segmentation_design_260516

## Purpose
17x is segmentation design for the 100-won-deal OTT churn analysis project. It is not modeling, Optuna, SHAP recalculation, feature removal, or final campaign threshold selection.

## Inputs and score source
Primary score source is `15x_oof_predictions.csv` filtered to `feature_set_variant == expanded_no_payment_device`, `dataset_scope == overall_with_promotion`, and `model_name == LightGBM`. This aligns the segmentation score with 16x payment-removed LightGBM SHAP evidence. It is not final model selection. `churn_risk = 1 - repurchase_score`, and top-k risk is sorted by churn_risk descending.

## Representative segment principle
Each subscription-event row receives exactly one representative provisional segment by priority rule. Payment, auth, and demographic proxy variables are not used in representative rules. `flag_age40_unverified_ios` is audit only.

## Key counts
- 06x expanded rows: 23079
- 06x expanded feature count from feature list: 80
- representative assignment rows: 23079
- segment count: 7

## Interpretation caveats
SHAP is model explanation, not causal evidence. is_promotion is not interpreted causally. Row counts are subscription-event rows, not unique customers. Genre/content fields are Movie_Master category mapping proxies. Payment/auth/demographic proxy variables are audit/caveat only.
