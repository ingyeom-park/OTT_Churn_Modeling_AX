# 14x_lightweight_candidate_tuning_260516

Purpose: lightweight Optuna tuning for 12x-selected candidate models only. This is not final model selection, SHAP, segmentation, feature removal, or campaign threshold selection.

Inputs:
- 06x: C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\06x_dataset_generation_260515
- 07x: C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\07x_feature_mapping_AARRR_260515
- 10x: C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\10x_feature_distribution_redundancy_pre_audit_260516
- 11x: C:\Code\ott-churn-prediction\park.ingyeom\reports\models\11x_baseline_growth_comparison_260516
- 12x: C:\Code\ott-churn-prediction\park.ingyeom\reports\models\12x_model_family_comparison_260516

Candidate selection: read 12x_candidate_selection_by_scope.csv, selected the highest-AUC candidate first, then added an operating-metric or stability-aware 12x candidate only within the two-model-per-feature-set-scope cap.

Feature sets and scopes: conservative_safe_22 and expanded_feature_set across overall_without_promotion, overall_with_promotion, promotion_only, and nonpromotion_only. USER_KEY is group key only, is_repurchase is target only, and is_promotion is included as a feature only where policy allows.

Model availability:
- LightGBM: import_available=yes, will_run=yes
- XGBoost: import_available=yes, will_run=no
- CatBoost: import_available=yes, will_run=yes
- HistGradientBoosting: import_available=yes, will_run=yes
- RandomForest: import_available=yes, will_run=yes

Optuna policy: 30 trials per selected model/scope, timeout 900 seconds, objective mean validation AUC under StratifiedGroupKFold(n_splits=5, group=USER_KEY, random_state=42). AP, Brier, logloss, train-valid gap, and fold AUC std are recorded as diagnostics.

Search spaces: LightGBM, XGBoost, and CatBoost follow the requested ranges. HistGradientBoosting and RandomForest use bounded lightweight spaces only because they appeared in 12x candidate_selection. Class direction remains is_repurchase=1 as the positive class.

Main results: see 14x_model_summary_by_scope.csv, 14x_vs_12x_comparison.csv, 14x_operating_metrics_at_k.csv, and 14x_calibration_decile_summary.csv.

12x comparison: improvements are reference signals only. AUC alone is insufficient; train-valid gap, AP, Brier, and top-k diagnostics must be reviewed together.

Caveats: top-k is diagnostic rather than a campaign threshold. VIF/redundancy remains documented but no feature removal or feature selection decision was made. This is not a final model.

Next step: 16x SHAP / interpretation can review suitable candidates after this reference tuning step.
