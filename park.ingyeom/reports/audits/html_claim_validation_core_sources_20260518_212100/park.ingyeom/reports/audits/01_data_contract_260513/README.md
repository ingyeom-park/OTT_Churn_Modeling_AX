# 01_data_contract_260513

This is step 01 only.

- No modeling was performed.
- No SHAP was performed.
- No leakage/timing audit was performed yet.
- The source file is the 광일 v2 master file: `(광일)Membership_v2_with_derived_features.csv`.
- The analysis unit should be treated as row-level / subscription-event-level because USER_KEY duplication exists.
- duration < 21 rows are only flagged here; no exclusion is applied in this goal.
- Next recommended step is 02_target_score_orientation_260513.

## Source

`C:\Code\ott-churn-prediction\park.ingyeom\data\(광일)Membership_v2_with_derived_features.csv`

## Output Folder

`C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\01_data_contract_260513`
