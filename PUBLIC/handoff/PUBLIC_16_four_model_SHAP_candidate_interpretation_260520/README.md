# PUBLIC 16 four-model SHAP candidate interpretation handoff

## Purpose

Provide a reviewable handoff package for PUBLIC 16 SHAP / model explanation.

## Inputs checked

- 15 OOF hotfix row-level artifacts
- 11 emergency reference final_result, trials_all, feature_manifest_used files
- PUBLIC promo input CSV files
- Python package availability

## Outputs generated

- SHAP global importance
- SHAP family importance
- LR coefficient summary
- SHAP direction summary
- Promo1 vs promo0 comparison
- Demographic context audit
- is_churn_prevented caveat audit
- Readiness table for segmentation
- Figures when available

## Execution status

The notebook was generated and executed through nbconvert fallback if direct jupyter command is unavailable.

## SHAP availability

See `16_shap_environment_check.csv`.

## Key warnings

- SHAP is not causal evidence.
- 07~10 remain pending validation.
- The feature family mapping is provisional for 16 SHAP only.
- Segmentation is blocked until user review.

## Demographic context policy

Age/gender are not default representative segment rules. They are profile audit or action personalization variables after EDA evidence.

## is_churn_prevented policy

is_churn_prevented is an approved historical context feature with caveat. It is not evidence of a current-cycle intervention effect.

## 07~10 pending validation

07~10 are temporarily deferred, not skipped and not completed.

## Files included in review zip

See `PUBLIC_16_four_model_SHAP_candidate_interpretation_zip_inventory.csv`.

## Execution summary

- Figure count: 6
- Fallback count: 0

## Next recommended action

Review the ZIP package. After review, decide whether to proceed to 17 segmentation or run demographic EDA first.
