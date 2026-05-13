# 03_observation_window_policy_260513

This is step 03 only.

- No modeling was performed.
- No SHAP was performed.
- No Optuna was performed.
- No feature engineering was performed.
- No rows were excluded.
- No duplicated rows were removed.
- The policy is 1~3 week observation, day 21 scoring, day 21 onward response period.
- 4th-week behavior is forbidden for modeling.
- duration < 21 rows are flagged but not removed.
- Next recommended step is `04_promotion_split_260513`.

## Source

`C:\Code\ott-churn-prediction\park.ingyeom\data\(광일)Membership_v2_with_derived_features.csv`

## Output Folder

`C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\03_observation_window_policy_260513`
