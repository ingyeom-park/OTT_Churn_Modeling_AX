# PUBLIC 15 OOF Score Hotfix Handoff 260520

## Purpose

Strictly revalidate and hotfix PUBLIC 15 OOF score outputs using local files.

## Why Previous 15 Review Failed

The previous review package omitted row-level OOF long/wide outputs, the executed notebook, note.md, and zip inventory. Its GB/LR overlap used fixed score cutoffs 0.5/0.6/0.7 instead of the required top10/top20/top30 percentile high-risk definition.

## Inputs Checked

- PUBLIC promo0/promo1 input CSVs
- Step 11 emergency four-model reference folders
- Existing 15 OOF artifacts and notebooks

## Existing Artifacts Validation

See `15_existing_oof_artifact_validation.csv`.

## Outputs Generated

See the review zip file list below.

## Execution Status

Hotfix notebook execution is required and the executed notebook is included when `notebook_executed` passes final checks.

## OOF Score Definitions

`repurchase_score_oof = P(is_repurchase=1)`.

`churn_risk_score_oof = 1 - repurchase_score_oof`.

## Metric Summary

ROC-AUC is primary. PR-AUC is secondary. F1, precision, recall, and brier score are included as auxiliary metrics.

## High-Risk Overlap Summary

GB/LR overlap is calculated using top10/top20/top30 percentile ranks by churn risk within each promo scope. It is not a fixed score cutoff.

## Readiness Status

SHAP and segmentation are blocked until user review.

## Limitations

07~10 remain pending validation. This is not final model selection and not final campaign thresholding.

## Files Included In Review Zip

- `PUBLIC\handoff\PUBLIC_15_oof_score_hotfix_260520\README.md`
- `PUBLIC\handoff\PUBLIC_15_oof_score_hotfix_260520\15_existing_oof_inventory_before_hotfix.csv`
- `PUBLIC\handoff\PUBLIC_15_oof_score_hotfix_260520\15_existing_oof_artifact_validation.csv`
- `PUBLIC\handoff\PUBLIC_15_oof_score_hotfix_260520\15_oof_hotfix_input_validation.csv`
- `PUBLIC\handoff\PUBLIC_15_oof_score_hotfix_260520\15_source_fingerprint_before_after.csv`
- `PUBLIC\handoff\PUBLIC_15_oof_score_hotfix_260520\PUBLIC_15_oof_score_hotfix_final_checks.csv`
- `PUBLIC\handoff\PUBLIC_15_oof_score_hotfix_260520\PUBLIC_15_oof_score_hotfix_zip_inventory.csv`
- `PUBLIC\notebooks\15_oof_score_or_sensitivity_260520\15_four_model_oof_score_generation_hotfix_260520.ipynb`
- `PUBLIC\notebooks\15_oof_score_or_sensitivity_260520\15_four_model_oof_score_generation_hotfix_260520_executed.ipynb`
- `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\README.md`
- `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\15_model_config_extraction.csv`
- `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\15_oof_feature_policy_check.csv`
- `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\15_oof_split_policy_check.csv`
- `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\15_oof_score_long.csv`
- `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\15_oof_score_wide.csv`
- `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\15_oof_score_wide_promo0.csv`
- `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\15_oof_score_wide_promo1.csv`
- `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\15_oof_metric_summary.csv`
- `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\15_oof_fold_distribution_check.csv`
- `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\15_gb_lr_high_risk_overlap.csv`
- `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\15_oof_readiness_for_shap_segmentation.csv`
- `PUBLIC\note.md`

## Next Recommended Action

Upload the hotfix review zip to ChatGPT and inspect OOF long/wide, executed notebook, metrics, overlap, and readiness before proceeding.
