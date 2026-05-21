# PUBLIC 11/12 Emergency Model Restructure 260520

## Purpose

This handoff documents the correction of PUBLIC emergency modeling stage meaning for Steps 11 and 12.

## User decision

The user decided that Step 11 must not be interpreted as LogisticRegression-only and Step 12 must not be interpreted as GradientBoosting-only.

## Why 11 is not Logistic-only

11 is an emergency four-model reference stage.

It gathers the confirmed log-retention-only LogisticRegression promo0, LogisticRegression promo1, GradientBoosting promo0, and GradientBoosting promo1 results into one reference structure.

## Why 12 is not Gradient-only

12 is a four-model comparison summary stage.

It compares the four Step 11 references by scope and model family. It is not a GradientBoosting-only folder and it is not a final model selection result.

## What was copied

- logistic_regression_promo0: copied from `PUBLIC\results\11_baseline_growth_comparison_260520\lr_baseline_promo0`
- logistic_regression_promo1: copied from `PUBLIC\results\11_baseline_growth_comparison_260520\lr_baseline_promo1`
- gradient_boosting_promo0: copied from `PUBLIC\results\12_model_family_comparison_260520\gradientboosting_promo0`
- gradient_boosting_promo1: copied from `PUBLIC\results\12_model_family_comparison_260520\gradientboosting_promo1`

The original result folders were retained. Files were copied, not moved.

## What was not changed

No model was trained.

No notebook was executed.

No Optuna run was performed.

No SHAP run was performed.

No segmentation run was performed.

No raw source file was intentionally modified by this task.

No `park.ingyeom` file was written by this task.

No `_data` file was written by this task.

No existing result folder was deleted or moved.

## Current four-model reference structure

- `PUBLIC/results/11_baseline_growth_comparison_260520/emergency_four_model_reference/logistic_regression_promo0/`
- `PUBLIC/results/11_baseline_growth_comparison_260520/emergency_four_model_reference/logistic_regression_promo1/`
- `PUBLIC/results/11_baseline_growth_comparison_260520/emergency_four_model_reference/gradient_boosting_promo0/`
- `PUBLIC/results/11_baseline_growth_comparison_260520/emergency_four_model_reference/gradient_boosting_promo1/`

## 07~10 pending validation status

07~10 remain pending validation.

The current emergency 11/12 structure does not complete or replace Steps 07~10.

## Current next step

The next step is either Step 12 comparison review or resolving the pending validation for Steps 07~10.

## Safe wording

- 11 is an emergency four-model reference stage.
- 12 is a four-model comparison summary stage.
- 07~10 remain pending validation.
- The copied four-model results are not final canonical model evidence.

## Unsafe wording

- 11 is LogisticRegression.
- 12 is GradientBoosting.
- 07~10 are skipped.
- The four-model results are final.
- SHAP or segmentation can start now.

## Source pointers

- `PUBLIC\results\11_baseline_growth_comparison_260520\emergency_four_model_reference\logistic_regression_promo0\SOURCE_POINTER.txt`
- `PUBLIC\results\11_baseline_growth_comparison_260520\emergency_four_model_reference\logistic_regression_promo1\SOURCE_POINTER.txt`
- `PUBLIC\results\11_baseline_growth_comparison_260520\emergency_four_model_reference\gradient_boosting_promo0\SOURCE_POINTER.txt`
- `PUBLIC\results\11_baseline_growth_comparison_260520\emergency_four_model_reference\gradient_boosting_promo1\SOURCE_POINTER.txt`

## Files generated

- `PUBLIC\handoff\PUBLIC_11_12_emergency_model_restructure_260520\README.md`
- `PUBLIC\handoff\PUBLIC_11_12_emergency_model_restructure_260520\PUBLIC_inventory_before_11_12_restructure.csv`
- `PUBLIC\handoff\PUBLIC_11_12_emergency_model_restructure_260520\PUBLIC_detected_model_result_candidates.csv`
- `PUBLIC\results\11_baseline_growth_comparison_260520\README.md`
- `PUBLIC\results\12_model_family_comparison_260520\README.md`
- `PUBLIC\notebooks\11_baseline_growth_comparison_260520\README.md`
- `PUBLIC\notebooks\12_model_family_comparison_260520\README.md`
- `PUBLIC\results\12_model_family_comparison_260520\four_model_comparison_summary\12_four_model_comparison_input_manifest.csv`
- `PUBLIC\results\12_model_family_comparison_260520\four_model_comparison_summary\12_four_model_metric_preview.csv`
- `PUBLIC\handoff\PUBLIC_11_12_emergency_model_restructure_260520\PUBLIC_11_12_emergency_model_restructure_final_checks.csv`
- `PUBLIC\handoff\PUBLIC_11_12_emergency_model_restructure_260520\PUBLIC_11_12_emergency_model_restructure_zip_inventory.csv`
- `PUBLIC\handoff\PUBLIC_11_12_emergency_model_restructure_260520\run_public_11_12_restructure.py`

- `PUBLIC\zip\PUBLIC_11_12_emergency_model_restructure_260520_review_package.zip`
