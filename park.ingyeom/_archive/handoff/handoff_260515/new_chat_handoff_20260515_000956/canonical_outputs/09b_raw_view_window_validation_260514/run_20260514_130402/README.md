# 09b_raw_view_window_validation_260514

This is 09b raw view window validation only.
No modeling was performed.
No predictions were created.
No repurchase_score or churn_risk was created.
No SHAP was performed.
No Optuna was performed.
No statistical significance testing was performed.
No p-values were created.
No feature engineering for modeling was performed.
Source CSVs were not modified.
This step validates whether master features are based on day0~20.
Raw View_History may contain day21+ views; the key question is whether master features include them.
If core usage features match day0~20 and mismatch day21+ included formulas, this supports the 1~3 week observation contract.
Any unresolved content formulas are clearly stated.
Membership-master alignment is recorded in 09b_membership_master_alignment_check.csv.
Next recommended step is 10_feature_eda_260513 if core usage window validation passes.

Output CSV count: 20 CSV files plus this README.md.
Output folder: C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\09b_raw_view_window_validation_260514\run_20260514_130402
