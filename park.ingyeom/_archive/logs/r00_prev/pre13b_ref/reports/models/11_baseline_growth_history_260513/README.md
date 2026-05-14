# 11_baseline_growth_history_260513

This is step 11 only: conservative baseline growth history modeling.

## Core boundaries
- SHAP was not performed.
- Optuna was not performed.
- Hyperparameter tuning was not performed.
- Review columns were not used.
- `is_promotion` was not used in groupwise models.
- In `overall_with_promotion`, `is_promotion` was used only at L5, not L0-L4.
- `USER_KEY` was used as group key, not feature.
- AUC uses `is_repurchase=1` as positive class.
- `repurchase_score` means probability of repurchase.
- `churn_risk`, if created, is `1 - repurchase_score`.
- Selected OOF scores are score orientation audit outputs only, not segmentation candidates, targeting criteria, or final thresholds.
- No final threshold.
- No final segmentation.
- This is not the final model.
- AUC may be modest because the feature set is conservative.
- Next recommended step is `12_model_baseline_comparison_260513`.

## Output folders
- Model outputs: `C:\Code\ott-churn-prediction\park.ingyeom\reports\models\11_baseline_growth_history_260513`
- Figure outputs: `C:\Code\ott-churn-prediction\park.ingyeom\reports\figures\11_baseline_growth_history_260513`
- Detected 09b folder: `C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\09b_raw_view_window_validation_260514\run_20260514_130402`
- Detected 10 folder: `C:\Code\ott-churn-prediction\park.ingyeom\reports\eda\10_feature_eda_260513`
