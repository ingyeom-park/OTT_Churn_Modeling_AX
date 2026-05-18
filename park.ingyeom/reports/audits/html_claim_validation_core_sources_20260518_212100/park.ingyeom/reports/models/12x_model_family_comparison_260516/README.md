# 12x model family comparison

## Purpose
12x performs fixed-parameter model family comparison for `conservative_safe_22` and `expanded_feature_set` using the canonical 06x/07x/10x/11x chain. It is not final model selection, Optuna, SHAP, segmentation, feature removal, or causal/business thresholding.

## Notebook reuse
Archived reference notebook found: `C:\Code\ott-churn-prediction\park.ingyeom\_archive\logs\r00_prev\pre13b_ref\notebook\12_model_baseline_comparison_canonical_260514\12_model_baseline_comparison_canonical_260514.ipynb`. This is the archived 12/12c reference. A copy was placed at the 12x notebook path before the current 12x model-family notebook was rewritten for the new canonical chain.

## Inputs
- 06x: `C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\06x_dataset_generation_260515`
- 07x: `C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\07x_feature_mapping_AARRR_260515`
- 10x: `C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\10x_feature_distribution_redundancy_pre_audit_260516`
- 11x: `C:\Code\ott-churn-prediction\park.ingyeom\reports\models\11x_baseline_growth_comparison_260516`

## Feature sets
- `conservative_safe_22`: 06x conservative dataset features.
- `expanded_feature_set`: 06x expanded dataset features. High VIF/redundancy from 10x is preserved as caution, not feature removal.

## Dataset scopes
- overall_without_promotion: all rows, `is_promotion` excluded.
- overall_with_promotion: all rows, `is_promotion` included when available.
- promotion_only: `is_promotion == 1`, `is_promotion` excluded.
- nonpromotion_only: `is_promotion == 0`, `is_promotion` excluded.

## Models and CV
- Required models: LogisticRegression, HistGradientBoosting, RandomForest, GradientBoosting, ExtraTrees.
- Optional models: LightGBM, XGBoost, CatBoost when import_available=yes.
- CV: StratifiedGroupKFold, n_splits=5, random_state=42, group key=`USER_KEY`.
- OOF predictions are validation-fold predictions only.

## Optional availability
          model_name import_available will_run unavailable_reason
  LogisticRegression              yes      yes                   
HistGradientBoosting              yes      yes                   
        RandomForest              yes      yes                   
    GradientBoosting              yes      yes                   
          ExtraTrees              yes      yes                   
            LightGBM              yes      yes                   
             XGBoost              yes      yes                   
            CatBoost              yes      yes                   

## Major results
    feature_set_name             dataset_scope           model_name  oof_auc   oof_ap  train_valid_auc_gap
expanded_feature_set         nonpromotion_only             LightGBM 0.883833 0.957616             0.070497
expanded_feature_set         nonpromotion_only HistGradientBoosting 0.882967 0.957129             0.075419
expanded_feature_set         nonpromotion_only             CatBoost 0.878657 0.956811             0.012043
expanded_feature_set         nonpromotion_only              XGBoost 0.878486 0.956288             0.020625
expanded_feature_set         nonpromotion_only     GradientBoosting 0.878323 0.956444             0.022503
expanded_feature_set    overall_with_promotion             LightGBM 0.877346 0.947321             0.042405
expanded_feature_set    overall_with_promotion HistGradientBoosting 0.876571 0.947263             0.043872
expanded_feature_set overall_without_promotion             LightGBM 0.873284 0.945362             0.043617

## Candidate selection
    feature_set_name             dataset_scope highest_auc_candidate  highest_auc_oof_auc operating_metric_candidate                                                       operating_metric_basis stability_aware_candidate                                                                        stability_basis recommended_for_14x_tuning recommended_for_16x_SHAP                                                                                       caution
conservative_safe_22         nonpromotion_only          RandomForest             0.831756       HistGradientBoosting highest top10pct lift_at_k among fixed-parameter 12x models; diagnostic only                  CatBoost within 0.01 OOF AUC of best, then lowest absolute train-valid AUC gap and fold AUC std               RandomForest                 CatBoost Candidate comparison only; not final model selection, thresholding, SHAP, or feature removal.
conservative_safe_22    overall_with_promotion              LightGBM             0.812208                   LightGBM highest top10pct lift_at_k among fixed-parameter 12x models; diagnostic only                  CatBoost within 0.01 OOF AUC of best, then lowest absolute train-valid AUC gap and fold AUC std                   LightGBM                 CatBoost Candidate comparison only; not final model selection, thresholding, SHAP, or feature removal.
conservative_safe_22 overall_without_promotion              LightGBM             0.812208                   LightGBM highest top10pct lift_at_k among fixed-parameter 12x models; diagnostic only                  CatBoost within 0.01 OOF AUC of best, then lowest absolute train-valid AUC gap and fold AUC std                   LightGBM                 CatBoost Candidate comparison only; not final model selection, thresholding, SHAP, or feature removal.
conservative_safe_22            promotion_only              LightGBM             0.796661       HistGradientBoosting highest top10pct lift_at_k among fixed-parameter 12x models; diagnostic only                  CatBoost within 0.01 OOF AUC of best, then lowest absolute train-valid AUC gap and fold AUC std                   LightGBM                 CatBoost Candidate comparison only; not final model selection, thresholding, SHAP, or feature removal.
expanded_feature_set         nonpromotion_only              LightGBM             0.883833       HistGradientBoosting highest top10pct lift_at_k among fixed-parameter 12x models; diagnostic only                  CatBoost within 0.01 OOF AUC of best, then lowest absolute train-valid AUC gap and fold AUC std                   LightGBM                 CatBoost Candidate comparison only; not final model selection, thresholding, SHAP, or feature removal.
expanded_feature_set    overall_with_promotion              LightGBM             0.877346                   LightGBM highest top10pct lift_at_k among fixed-parameter 12x models; diagnostic only                  CatBoost within 0.01 OOF AUC of best, then lowest absolute train-valid AUC gap and fold AUC std                   LightGBM                 CatBoost Candidate comparison only; not final model selection, thresholding, SHAP, or feature removal.
expanded_feature_set overall_without_promotion              LightGBM             0.873284       HistGradientBoosting highest top10pct lift_at_k among fixed-parameter 12x models; diagnostic only                  LightGBM within 0.01 OOF AUC of best, then lowest absolute train-valid AUC gap and fold AUC std                   LightGBM                 LightGBM Candidate comparison only; not final model selection, thresholding, SHAP, or feature removal.
expanded_feature_set            promotion_only              LightGBM             0.861608       HistGradientBoosting highest top10pct lift_at_k among fixed-parameter 12x models; diagnostic only                   XGBoost within 0.01 OOF AUC of best, then lowest absolute train-valid AUC gap and fold AUC std                   LightGBM                  XGBoost Candidate comparison only; not final model selection, thresholding, SHAP, or feature removal.

## Main result files
- `12x_model_summary_by_scope.csv`
- `12x_conservative_vs_expanded_comparison.csv`
- `12x_vs_11x_baseline_comparison.csv`
- `12x_oof_predictions.csv`
- `12x_operating_metrics_at_k.csv`
- `12x_calibration_decile_summary.csv`
- `12x_redundancy_caveat_handoff.csv`
- `12x_candidate_selection_by_scope.csv`

## Key cautions
- VIF/redundancy does not justify feature removal in 12x.
- LogisticRegression coefficient interpretation is limited under high VIF.
- Tree/boosting models are not excluded solely because of high VIF.
- Later SHAP should be interpreted by feature family/redundancy cluster.
- Top-k churn risk is diagnostic, not a campaign threshold.
- Results are row-level / subscription-event-level, not unique-user analysis.

## Next step
Review candidates for 14x tuning or 16x SHAP. 12x itself does not select the final model.
