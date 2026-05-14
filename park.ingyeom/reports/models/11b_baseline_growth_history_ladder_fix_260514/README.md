# 11b_baseline_growth_history_ladder_fix_260514

## IMPORTANT: This is the 11b correction run (canonical Step 11)

Old Step 11 (`11_baseline_growth_history_260513`) is deprecated/pre-patch due to
feature ladder contamination: `diff_between_w3_w2` was erroneously included in
`L2_add_week2_retention`. See `11b_deprecated_11_audit.csv` and
`11b_ladder_contamination_check.csv` for details.

**11b is the canonical corrected baseline growth history.**
Steps 12, 16, and 17 use 11b results only.

## Core boundaries
- This is step 11b only: conservative baseline growth history modeling (corrected).
- Old Step 11 is deprecated/pre-patch due to ladder contamination.
- L2 feature count: 13 (corrected from 14 in Step 11).
- SHAP was not performed.
- Optuna was not performed.
- Hyperparameter tuning was not performed.
- Review columns were not used.
- `is_promotion` was not used in groupwise models.
- In `overall_with_promotion`, `is_promotion` was used only at L5, not L0-L4.
- `USER_KEY` was used as group key, not feature.
- AUC uses `is_repurchase=1` as positive class.
- `repurchase_score` means probability of repurchase.
- `churn_risk` is `1 - repurchase_score`.
- Selected OOF scores are score orientation audit outputs only.
- No final threshold.
- No final segmentation.
- This is not the final model.
- AUC may be modest because the feature set is conservative.
- Next recommended step is `12_model_baseline_comparison_260513`.

## Output folders
- Model outputs: `C:\Code\ott-churn-prediction\park.ingyeom\reports\models\11b_baseline_growth_history_ladder_fix_260514`
- Figure outputs: `C:\Code\ott-churn-prediction\park.ingyeom\reports\figures\11b_baseline_growth_history_ladder_fix_260514`
- Detected 09b folder: `C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\09b_raw_view_window_validation_260514\run_20260514_130402`
- Detected 10 folder: `C:\Code\ott-churn-prediction\park.ingyeom\reports\eda\10_feature_eda_260513`
