# 05_column_role_leakage_timing_audit_260513

This is step 05 only.

- No modeling was performed.
- No predictions were created.
- No SHAP was performed.
- No Optuna was performed.
- No feature engineering was performed.
- No rows were excluded.
- No duplicate rows were removed.
- No model-ready dataset was created.
- This audit is conservative.
- Review means not approved for modeling yet.
- `is_promotion` is split variable and forbidden in groupwise models.
- 4th-week/response-period behavior is forbidden.
- total/all-period and ambiguous content/window columns require timing review.

Source: `park.ingyeom/data/(광일)Membership_v2_with_derived_features.csv`

Rows: 23,343
Columns: 91
Output folder mode: `base_output_folder_used`

## Summary Counts

- Conservative safe candidate columns: 16
- Review-required columns: 72
- Forbidden/drop columns: 6

## Overall Model Candidate Counts

{
  "review": 69,
  "yes": 17,
  "no": 5
}

## Groupwise Model Candidate Counts

{
  "review": 69,
  "yes": 16,
  "no": 6
}

## Role Counts

| primary_role            |   count |
|:------------------------|--------:|
| unknown_review_required |      31 |
| genre_ratio             |      23 |
| retention               |      11 |
| membership_context      |       7 |
| activation              |       7 |
| content_recency         |       4 |
| aggregate_usage_review  |       2 |
| id                      |       1 |
| split                   |       1 |
| leakage_suspect         |       1 |
| date_or_time_anchor     |       1 |
| timing_review_required  |       1 |
| target                  |       1 |

## Interpretation Limits

This audit does not prove that all remaining columns are leakage-free. It only classifies columns using the current CSV, column names, established project contracts, and available previous audit outputs. Any `review` column must stay out of modeling until timing and semantics are confirmed.

## Next Recommended Step

`06_common_preprocessing_final_cohort_policy_260513`, or, if following the docx strictly, `06_common_preprocessing_and_final_cohort_260513`.
