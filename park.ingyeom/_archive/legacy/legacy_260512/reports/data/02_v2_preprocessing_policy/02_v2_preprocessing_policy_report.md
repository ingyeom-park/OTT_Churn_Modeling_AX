# 02_v2 Preprocessing Policy Report

## Scope
- Applied Stage 02 Membership preprocessing only.
- No usage features, content features, modeling datasets, SHAP outputs, or model training were created.

## Applied Rules
- Created `membership_row_id` and `source_row_number` before filtering.
- Excluded strict target-conflict rows by default.
- Removed exact duplicate Membership rows by keeping the lowest `membership_row_id` representative after prior exclusions.
- Removed same non-target/same-target duplicate rows by keeping the lowest `membership_row_id` representative after prior exclusions.

## Deferred Rules
- `duration_days` was computed for audit only.
- No duration filter was applied because `end_date` inclusiveness and valid subscription-duration definition are not fully confirmed.
- Value anomalies were audited and flagged only; no automatic deletion was performed.

## Row Counts
- Raw Membership rows: 24,074.
- Excluded Membership rows: 141.
- Final retained Membership rows: 23,933.

## Exclusion Counts By Reason
- EXACT_DUPLICATE_EXTRA_ROW: 68
- STRICT_TARGET_CONFLICT: 73

## Join Expansion After Membership Cleaning
- Expected joined temporal rows: 177,815.
- Expansion versus raw ViewHistory rows: 2,514.
- This remains audit-only. No usage features were created.

## Model Feature Guard
- Stage 02 does not create a modeling dataset.
- Forbidden model features noted but not used as model features: USER_KEY, USER_NUM, MOVIE_NUM, reg_date, end_date, duration_days, watch_date, is_repurchase.

## Output Files
- park.ingyeom/reports/data/02_v2_preprocessing_policy/membership_v2_preprocessed.csv
- park.ingyeom/reports/data/02_v2_preprocessing_policy/usermapping_v2_policy_checked.csv
- park.ingyeom/reports/data/02_v2_preprocessing_policy/moviemaster_v2_policy_checked.csv
- park.ingyeom/reports/data/02_v2_preprocessing_policy/v2_preprocessing_summary.json
- park.ingyeom/reports/tables/02_v2_preprocessing_policy/02_v2_filter_summary.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy/02_v2_excluded_membership_rows.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy/02_v2_duplicate_resolution_summary.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy/02_v2_target_conflict_resolution_summary.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy/02_v2_duration_policy_deferred_summary.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy/02_v2_value_anomaly_flag_summary.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy/02_v2_usermapping_policy_summary.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy/02_v2_moviemaster_policy_summary.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy/02_v2_join_expansion_after_membership_cleaning.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy/02_v2_final_checks.csv
- park.ingyeom/reports/data/02_v2_preprocessing_policy/02_v2_preprocessing_summary.json
- park.ingyeom/reports/data/02_v2_preprocessing_policy/02_v2_preprocessing_policy_report.md
