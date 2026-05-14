# 12_model_baseline_comparison_rebuild_260514

This is Step 12 rebuild. Old Step 12 is superseded because it lacked required operating metrics. 11b is canonical corrected Step 11 and the 11b semantic patch is applied.

This is a fixed-parameter model family comparison. No review columns, no Optuna, no SHAP, no tuning, no final threshold, and no segmentation were used. AUC is a primary ranking metric but is not sufficient for marketing execution. Operating metrics at top-k churn_risk are included as diagnostics, not campaign target rules.

Actual model output folder: C:\Code\ott-churn-prediction\park.ingyeom\reports\models\12_model_baseline_comparison_rebuild_260514\run_20260514_225947
Actual figure output folder: C:\Code\ott-churn-prediction\park.ingyeom\reports\figures\12_model_baseline_comparison_rebuild_260514

Next recommended step: decide candidate path, then 14_optuna_candidate_tuning_260513 if tuning is needed, 16_SHAP if candidate is stable enough for interpretation, or optional lightweight 13 synthesis if documentation sequence requires.
