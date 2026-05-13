# 02_target_score_orientation_260513

This is step 02 only.

- No modeling was performed.
- No SHAP was performed.
- No feature engineering was performed.
- No rows were excluded.
- No duplicated rows were removed.
- `is_repurchase=1` is the positive class for model evaluation.
- Model output should be called `repurchase_score`.
- Operational `churn_risk` should be computed as `1 - repurchase_score`.
- Analysis unit should be treated as row-level / subscription-event-level.
- Next recommended step is `03_observation_window_policy_260513`.

## Source

`C:\Code\ott-churn-prediction\park.ingyeom\data\(광일)Membership_v2_with_derived_features.csv`

## Output Folder

`C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\02_target_score_orientation_260513`
