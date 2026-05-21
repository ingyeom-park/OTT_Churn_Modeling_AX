# 11_baseline_growth_comparison_260520

## Purpose

11 is an emergency four-model reference stage, not a LogisticRegression-only stage.

11은 LogisticRegression 전용 단계가 아니라 log-retention-only 4개 모델을 모으는 emergency four-model reference 단계이다.

This folder keeps copied references to the four log-retention-only emergency model results:

- LogisticRegression promo0
- LogisticRegression promo1
- GradientBoosting promo0
- GradientBoosting promo1

## Emergency Status

This stage was created under an emergency bypass situation. It is a baseline/emergency reference layer, not a final canonical model evidence layer.

Steps 07~10 remain pending validation.

07~10은 여전히 pending validation 상태다.

These copied results are not final canonical model evidence.

이 결과는 final canonical model evidence가 아니다.

## What 11 Is Not

11 is not a LogisticRegression-only stage.

11 is not a GradientBoosting-only stage.

11 is not permission to move directly into SHAP or segmentation.

## What 11 Is

11 collects the confirmed log-retention-only four-model outputs in one reference location so that Step 12 can compare them consistently.

The original result folders are retained. This step copied files into the emergency reference structure and did not move or delete the source result folders.

## Current Emergency Reference Structure

- logistic_regression_promo0: copied from `PUBLIC\results\11_baseline_growth_comparison_260520\lr_baseline_promo0`
- logistic_regression_promo1: copied from `PUBLIC\results\11_baseline_growth_comparison_260520\lr_baseline_promo1`
- gradient_boosting_promo0: copied from `PUBLIC\results\12_model_family_comparison_260520\gradientboosting_promo0`
- gradient_boosting_promo1: copied from `PUBLIC\results\12_model_family_comparison_260520\gradientboosting_promo1`

## Existing 11x/12x Meaning

The original `11x_baseline_growth_comparison_260516.ipynb` was a baseline growth comparison reference, not a LogisticRegression-only stage.

The original `12x_model_family_comparison_260516.ipynb` was a model family comparison reference, not a GradientBoosting-only stage.

The current PUBLIC emergency structure is a temporary narrowed application of that older 11x/12x meaning.

The original 11x/12x notebooks are future template/reference materials only. They were not executed in this restructuring task.

## Next Step

12 must compare the four model results for metric, overfit, and stability review before any stronger wording is used.

These copied results are not final canonical model evidence.
