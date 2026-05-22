# PUBLIC 16b feature family mapping hotfix

## Purpose

This folder contains the 16b hotfix for PUBLIC 16 SHAP feature family mapping.

## Why this hotfix was needed

Important behavior, genre, and registration-timing variables were left in `technical_or_unknown`.

technical_or_unknown was a provisional fallback label, not evidence that the features are useless.

## What was not changed

This hotfix does not recalculate SHAP values.

This hotfix only corrects feature family mapping and re-aggregates existing SHAP outputs.

No model refit, SHAP recalculation, OOF regeneration, Optuna, segmentation, final model selection, or campaign threshold confirmation was performed.

## Original technical_or_unknown issue

The original bucket mixed recency, inactivity gap, week-specific viewing, usage concentration, genre ratio, and registration timing context. That would distort family importance and 17 segmentation handoff.

## Hotfix mapping rules

- `reg_hour_*`, `reg_is_weekend` -> `registration_timing_context`
- `active_ratio`, `max_day_share`, `day_count_over_3times` -> `usage_concentration`
- `recency`, `max_inactive_gap_days` -> `inactivity_recency`
- `is_only_w1`, `is_only_w2`, `is_only_w3` -> `week_specific_usage_pattern`
- `historical_war_ratio`, `sf_fantasy_ratio`, `other_ratio` -> `genre_preference`

## Before/after family importance

See `16b_family_importance_before_after_comparison.csv`.

## Promo1 vs promo0 comparison after hotfix

See `16b_promo1_vs_promo0_shap_comparison_hotfix.csv`.

Promo1 strength means the model used that family more strongly inside promo1. It does not mean 100won caused the difference.

## Handoff to 17 segmentation

17 segmentation should use the hotfixed family mapping, not the original technical_or_unknown bucket.

See `16b_family_interpretation_handoff_for_17.csv`.

## Demographic and action personalization policy

Demographic features are profile/action personalization variables, not default representative segment rules.

age_group, is_female, and is_male should not be used directly as segment names in 17. Age/gender action variants require EDA evidence.

## is_churn_prevented caveat

is_churn_prevented remains an approved historical context feature with caveat. It is not evidence of a current-cycle intervention effect.

## 07~10 pending validation caveat

07~10 remain pending validation.

## Safe wording

- technical_or_unknown was a provisional fallback label.
- This hotfix preserves existing SHAP values.
- 17 should use 16b hotfix family mapping.
- Demographic features are profile/action personalization variables.
- 07~10 remain pending validation.

## Unsafe wording

- technical_or_unknown means useless.
- technical_or_unknown is a business segment.
- recency is technical noise.
- age/gender causes churn.
- 100won caused the SHAP difference.
- segmentation can start automatically.
- 07~10 are completed.

## Next action

Review the 16b ZIP package. After review, decide whether to proceed to 17 segmentation or run demographic EDA first.
