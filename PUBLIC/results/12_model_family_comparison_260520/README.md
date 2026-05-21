# 12_model_family_comparison_260520

## Purpose

12 is a four-model comparison stage, not a GradientBoosting-only stage.

12는 GradientBoosting 전용 단계가 아니라 4개 모델 비교 단계이다.

This stage compares the four model references gathered in Step 11.

## Scope Rule

Promo0 and promo1 must be evaluated separately.

promo0와 promo1은 분리해서 평가해야 한다.

This is not a single contest that chooses one winner across all four outputs. Promo0 and promo1 are different scopes and must not be collapsed into one final ranking without explicit review.

## Required Checks Before Comparison

Before any comparison claim is made, the reviewer must confirm:

- log-retention-only condition
- required `final_result.csv` and `trials_all.csv` files
- trial-level evidence in `trials_all.csv`
- overfit and stability signals
- the fact that Steps 07~10 remain pending validation

## Current Status

This is not final model selection.

이 단계는 final model selection이 아니다.

The current input manifest is:

- `four_model_comparison_summary/12_four_model_comparison_input_manifest.csv`

If present, `four_model_comparison_summary/12_four_model_metric_preview.csv` only summarizes metrics already saved in existing `final_result.csv` files. It is not a new calculation, not a model rerun, and not a final decision.

## Existing 11x/12x Meaning

The original `11x_baseline_growth_comparison_260516.ipynb` was a baseline growth comparison reference, not a LogisticRegression-only stage.

The original `12x_model_family_comparison_260516.ipynb` was a model family comparison reference, not a GradientBoosting-only stage.

The current PUBLIC emergency structure is a temporary narrowed application of that older 11x/12x meaning. The original 11x/12x notebooks are future template/reference materials only and were not executed in this restructuring task.
