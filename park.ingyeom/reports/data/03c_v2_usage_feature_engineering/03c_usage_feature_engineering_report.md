# 03c v2 Usage Feature Engineering Report

## Scope
- Rebuilt usage features from 02c strict-core corrected Membership rows.
- Raw files were read only.
- Outputs were written only under the new 03c report folders.
- No model training, SHAP, content features, or modeling dataset was created.

## Temporal Policy
- Dates use `reg_date_parsed` and `end_date_parsed` from 02c when available.
- `watch_rel_day` was recomputed as `watch_date - reg_date`.
- Logs before `reg_date` and after `end_date` were excluded from feature windows.
- No end_date-derived feature was created.

## Windows
- `w1_1`: rel_day 0 through 6, rows 23,115.
- `w1_2`: rel_day 0 through 13, rows 23,115.
- `w1_3`: rel_day 0 through 20, rows 23,115.
- `w1_4`: rel_day 0 through 27, rows 23,115.

## Derived Feature Note
- Week ratios and week deltas are included as derived/redundant audit columns and marked for later pruning.

## Final Checks
- raw_files_unchanged: PASS (_data snapshot and protected input file snapshots unchanged)
- no_data_output_created: PASS (No files were created or modified under _data)
- old_stage03_outputs_not_overwritten: PASS (Existing 03_v2 output directory snapshots unchanged)
- one_row_per_membership_row_id_in_every_window: PASS (w1_1 rows=23115; w1_2 rows=23115; w1_3 rows=23115; w1_4 rows=23115)
- row_count_matches_02c_strict_core_membership: PASS (strict_core_membership_rows=23115)
- w1_1_w1_2_w1_3_w1_4_separated: PASS (Each window table uses its own prefixed feature columns)
- no_model_training: PASS (No estimator, fit, prediction, or model artifact is created)
- no_shap: PASS (No SHAP package, explainer, or SHAP artifact is used)
- no_content_features: PASS (none)
- no_modeling_dataset: PASS (Only per-window usage feature tables and audit artifacts were created)
- no_identifier_or_date_model_features: PASS (none)
- all_required_outputs_created: PASS (required_outputs=14)

## Output Files
- park.ingyeom/reports/data/03c_v2_usage_feature_engineering/usage_features_v2c_w1_1.csv
- park.ingyeom/reports/data/03c_v2_usage_feature_engineering/usage_features_v2c_w1_2.csv
- park.ingyeom/reports/data/03c_v2_usage_feature_engineering/usage_features_v2c_w1_3.csv
- park.ingyeom/reports/data/03c_v2_usage_feature_engineering/usage_features_v2c_w1_4.csv
- park.ingyeom/reports/data/03c_v2_usage_feature_engineering/03c_usage_feature_summary.json
- park.ingyeom/reports/tables/03c_v2_usage_feature_engineering/03c_input_row_count_summary.csv
- park.ingyeom/reports/tables/03c_v2_usage_feature_engineering/03c_join_expansion_summary.csv
- park.ingyeom/reports/tables/03c_v2_usage_feature_engineering/03c_temporal_filter_summary.csv
- park.ingyeom/reports/tables/03c_v2_usage_feature_engineering/03c_window_row_count_summary.csv
- park.ingyeom/reports/tables/03c_v2_usage_feature_engineering/03c_no_watch_summary.csv
- park.ingyeom/reports/tables/03c_v2_usage_feature_engineering/03c_short_watch_summary.csv
- park.ingyeom/reports/tables/03c_v2_usage_feature_engineering/03c_usage_feature_numeric_summary.csv
- park.ingyeom/reports/tables/03c_v2_usage_feature_engineering/03c_final_checks.csv
- park.ingyeom/reports/data/03c_v2_usage_feature_engineering/03c_usage_feature_engineering_report.md
