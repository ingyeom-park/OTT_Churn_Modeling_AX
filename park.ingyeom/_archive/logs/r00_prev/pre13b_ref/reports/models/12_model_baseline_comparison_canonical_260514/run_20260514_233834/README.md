# 12_model_baseline_comparison_canonical_260514

This is the canonical rebuilt Step 12. Old Step 12 and old Step 12r are archived/deprecated and their metrics were not used as final evidence.

- 11b is the canonical corrected Step 11 baseline reference.
- 11b semantic patch was applied as an interpretation guardrail.
- This step performs fixed-parameter model family comparison only.
- No review columns used.
- No Optuna, SHAP, tuning, final threshold, segmentation, campaign effect claim, or causal claim.
- AUC is the primary ranking metric but is not sufficient for marketing execution.
- Operating metrics at top-k churn_risk are diagnostics only and are not campaign target rules.
- Stability-aware candidate selection is not automatically the highest AUC model.

Actual model output folder: `C:\Code\ott-churn-prediction\park.ingyeom\reports\models\12_model_baseline_comparison_canonical_260514\run_20260514_233834`

Actual figure output folder: `C:\Code\ott-churn-prediction\park.ingyeom\reports\figures\12_model_baseline_comparison_canonical_260514\run_20260514_233834`

Next recommended step: decide candidate path: 1. `14_optuna_candidate_tuning_260513` if tuning is needed. 2. `16_SHAP` if candidate is stable enough for interpretation. 3. Optional lightweight 13 synthesis if documentation sequence requires.
