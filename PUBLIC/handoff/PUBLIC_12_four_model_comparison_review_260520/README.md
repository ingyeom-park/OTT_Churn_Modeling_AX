# PUBLIC 12 Four-Model Comparison Review Handoff

## Purpose

This handoff summarizes the Step 12 four-model comparison review after high-AUC leakage/proxy steering.

This is not final model selection.

Because AUC appears unusually high for this project context, this step treats high performance as a validation target rather than as immediate evidence of model quality.

현재 AUC가 프로젝트 맥락상 과도하게 높아 보일 수 있으므로, 이번 단계에서는 높은 성능을 곧바로 성과로 해석하지 않고 leakage, proxy, overfit, split issue 검수 대상으로 취급한다.

## Inputs checked

- LogisticRegression promo0
- LogisticRegression promo1
- GradientBoosting promo0
- GradientBoosting promo1

For each model, saved final_result, trials_all, feature manifest, and split-policy metadata were checked where available.

## Outputs generated

- `12_input_file_validation.csv`
- `12_log_retention_condition_check.csv`
- `12_final_result_metric_summary.csv`
- `12_trials_overfit_stability_summary.csv`
- `12_scopewise_gb_vs_lr_comparison.csv`
- `12_oof_readiness_decision.csv`
- `12_high_auc_suspicion_audit.csv`
- `12_leakage_proxy_feature_audit.csv`
- `12_split_policy_audit.csv`
- Review README
- Final checks
- Review zip

## Key findings

- High AUC is treated as validation target rather than model-quality evidence.
- Models with any recorded AUC metric at or above 0.90 are flagged.
- Target-like/proxy feature audit and split policy audit must be reviewed before final model wording.
- Existing final_result metadata records StratifiedKFold and a USER_KEY duplication caveat; GroupKFold was not used.

## Limitations

This review did not train models, execute notebooks, run Optuna, run SHAP, run segmentation, or generate an OOF score table.

## OOF readiness summary

OOF generation remains blocked until user approval.

## 07~10 pending validation status

07~10 remain pending validation. This Step 12 review does not mark them complete.

## Files included in review zip

- `PUBLIC\handoff\PUBLIC_12_four_model_comparison_review_260520\README.md`
- `PUBLIC\handoff\PUBLIC_12_four_model_comparison_review_260520\12_input_file_validation.csv`
- `PUBLIC\handoff\PUBLIC_12_four_model_comparison_review_260520\PUBLIC_12_four_model_comparison_review_final_checks.csv`
- `PUBLIC\handoff\PUBLIC_12_four_model_comparison_review_260520\PUBLIC_12_four_model_comparison_review_zip_inventory.csv`
- `PUBLIC\results\12_model_family_comparison_260520\four_model_comparison_review\README.md`
- `PUBLIC\results\12_model_family_comparison_260520\four_model_comparison_review\12_log_retention_condition_check.csv`
- `PUBLIC\results\12_model_family_comparison_260520\four_model_comparison_review\12_final_result_metric_summary.csv`
- `PUBLIC\results\12_model_family_comparison_260520\four_model_comparison_review\12_trials_overfit_stability_summary.csv`
- `PUBLIC\results\12_model_family_comparison_260520\four_model_comparison_review\12_scopewise_gb_vs_lr_comparison.csv`
- `PUBLIC\results\12_model_family_comparison_260520\four_model_comparison_review\12_oof_readiness_decision.csv`
- `PUBLIC\results\12_model_family_comparison_260520\four_model_comparison_review\12_high_auc_suspicion_audit.csv`
- `PUBLIC\results\12_model_family_comparison_260520\four_model_comparison_review\12_leakage_proxy_feature_audit.csv`
- `PUBLIC\results\12_model_family_comparison_260520\four_model_comparison_review\12_split_policy_audit.csv`
- `PUBLIC\note.md`
- `PUBLIC\handoff\PUBLIC_12_four_model_comparison_review_260520\run_public_12_four_model_comparison_review.py`
- `PUBLIC\handoff\PUBLIC_12_four_model_comparison_review_260520\apply_high_auc_leakage_steering.py`

## Next recommended action

Review leakage/proxy/split audit outputs before deciding whether to approve OOF score table generation or return to 07~10 pending validation.
