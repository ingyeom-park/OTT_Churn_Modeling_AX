# 05b_column_role_dictionary_patch_260513

This is 05b patch step.

It patches semantic role/family errors from step 05. Original 05 outputs were not overwritten.

## Scope Guardrails

- No modeling was performed.
- No predictions were created.
- No SHAP was performed.
- No Optuna was performed.
- No feature engineering was performed.
- No rows were excluded.
- No duplicate rows were removed.
- No model-ready dataset was created.
- Downstream steps should use 05b canonical outputs.
- Review means not approved for modeling yet.

## Repository Root Warning

- Requested repo root: `C:\Code\ott-churn-prediction`
- Actual repo root from `git rev-parse --show-toplevel`: `C:/Code/Github Repository/ott-churn-prediction`
- Warning recorded: `True`

## Patch Summary

- Detected issues: 48
- Patched columns: 84
- Role-changed columns: 46
- Allowed-status-changed columns: 8
- True human-review columns: 66
- Conservative safe columns: 22
- Forbidden/drop columns: 4

## Key Corrections

- `retention_w2_ratio`, `retention_w3_ratio`: retention ratio, not genre ratio.
- `active_ratio`, `avg_rewatch_ratio`, `weekend_watch_ratio`, `watch_ratio_under_1m`, `watch_ratio_under_5m`: usage/behavior ratios, not genre ratios.
- `is_cold_start_3d`, `is_cold_start_7d`: activation/onboarding, not content recency.
- `diff_between_w2_w1`, `diff_between_w3_w1`, `diff_between_w3_w2`: retention change.
- `forbidden_drop_columns` and `review_required_candidate` are separated in the 05b feature set contracts.

## Interpretation Limits

This patch corrects obvious semantic role/family errors. It does not prove absence of leakage. Columns marked `review` are still not approved for modeling.

## Next Recommended Step

`06_common_preprocessing_and_final_cohort_260513`.
