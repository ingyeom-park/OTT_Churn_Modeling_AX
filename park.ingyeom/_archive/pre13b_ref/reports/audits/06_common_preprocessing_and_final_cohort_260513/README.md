# 06_common_preprocessing_and_final_cohort_260513

This is step 06 only.

- No modeling was performed.
- No predictions were created.
- No SHAP was performed.
- No Optuna was performed.
- No model scores were created.
- Source CSV was not modified.
- Original 05/05b outputs were not overwritten.

Main row policy:

- duration < 21 excluded from primary main modeling cohort.
- Exact full duplicate extra rows excluded from primary main modeling cohort by keeping first source row order.
- duplicated USER_KEY rows are not collapsed.
- cross-promotion USER_KEY overlap rows are not collapsed.

duration < 21 rows are preserved in reference/anomaly outputs.
Full duplicate rows are preserved in audit outputs.

The conservative feature table uses only 05b conservative safe candidate columns. Review columns are not included in the conservative feature table.

Downstream modeling must use group-aware CV with USER_KEY where applicable.

Next recommended step:

- 07_AARRR_feature_mapping_260513 if following docx sequentially.
- 11_baseline_growth_history_260513 only after confirming AARRR/EDA planning.
- Do not skip 07~10 lightly.
