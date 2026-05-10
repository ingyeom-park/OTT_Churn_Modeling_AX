# 03_v2 Usage Feature Engineering Report

## Scope
- Created usage behavior features only.
- No content features, modeling dataset for training, SHAP output, or model was created.

## Observation Windows
- `w1_3`: rel_day 0 through 20.
- `w1_4`: rel_day 0 through 27.
- Features are separated by `w1_3_` and `w1_4_` prefixes.

## Join Policy
- `USER_KEY` and `USER_NUM` were used only for temporary joining and aggregation.
- Expanded view logs were aggregated back to one row per `membership_row_id`.

## Temporal Policy
- Included logs require `watch_date >= reg_date` and rel_day inside the requested window.
- `end_date` inclusiveness remains unresolved, so no end_date-derived features were created.

## Row Counts
- w1_3 rows: 23,933.
- w1_4 rows: 23,933.

## Output Files
- park.ingyeom/reports/data/03_v2_usage_feature_engineering/usage_features_v2_w1_3.csv
- park.ingyeom/reports/data/03_v2_usage_feature_engineering/usage_features_v2_w1_4.csv
- park.ingyeom/reports/data/03_v2_usage_feature_engineering/usage_feature_summary.json
- park.ingyeom/reports/tables/03_v2_usage_feature_engineering/03_v2_usage_input_summary.csv
- park.ingyeom/reports/tables/03_v2_usage_feature_engineering/03_v2_join_expansion_summary.csv
- park.ingyeom/reports/tables/03_v2_usage_feature_engineering/03_v2_temporal_filter_summary.csv
- park.ingyeom/reports/tables/03_v2_usage_feature_engineering/03_v2_window_row_count_summary.csv
- park.ingyeom/reports/tables/03_v2_usage_feature_engineering/03_v2_no_watch_summary.csv
- park.ingyeom/reports/tables/03_v2_usage_feature_engineering/03_v2_short_watch_summary.csv
- park.ingyeom/reports/tables/03_v2_usage_feature_engineering/03_v2_usage_feature_numeric_summary.csv
- park.ingyeom/reports/tables/03_v2_usage_feature_engineering/03_v2_usage_feature_missing_summary.csv
- park.ingyeom/reports/tables/03_v2_usage_feature_engineering/03_v2_final_checks.csv
- park.ingyeom/reports/data/03_v2_usage_feature_engineering/03_v2_usage_feature_engineering_report.md
