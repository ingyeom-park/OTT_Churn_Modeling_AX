# PUBLIC 16 four-model SHAP candidate interpretation

## Purpose

This folder contains PUBLIC 16 SHAP / model explanation outputs for the four log-retention-based model and scope combinations.

This is not segmentation, final model selection, OOF regeneration, Optuna, or campaign threshold confirmation.

## Inputs

- 15 OOF hotfix outputs from `PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520`
- 11 emergency four-model reference outputs from `PUBLIC\results\11_baseline_growth_comparison_260520\emergency_four_model_reference`
- Promo input CSV files from `PUBLIC\data`

## Model refit policy for SHAP

Each candidate model was refit on its corresponding promo input data only to create explanation artifacts.

This refit is an explanation-only fitted candidate model. It is not final model training, not a campaign deployment model, and does not replace the 15 OOF score evidence.

## SHAP availability

`shap` availability is recorded in `16_shap_environment_check.csv`.

SHAP is model explanation, not causality.

## Feature policy

Feature policy is recorded in `16_shap_feature_policy_check.csv`.

Raw retention ratio features remain forbidden. Log-retention features are allowed with interpretation caveats.

## Feature family mapping

`16_feature_family_mapping_for_shap.csv` is provisional for 16 SHAP only because 07 mapping remains pending validation.

## Global importance

Global feature importance is stored in `16_shap_global_importance.csv`.

## Family importance

Family importance is stored in `16_shap_family_importance.csv`. It is presentation-friendly but provisional.

## Promo1 vs promo0 comparison

Promo1 is the main business scope; promo0 is the comparison scope.

The comparison file records where a feature or feature family is more strongly used by the model, not what the 100won promotion caused.

## Demographic context audit

Demographic features are not representative segment rules by default.

Age/gender may be used as action personalization layer only after EDA evidence.

## is_churn_prevented caveat

is_churn_prevented is approved historical context feature with caveat.

It should be interpreted as past churn prevention response history, not current intervention causal effect.

## What was not done

- Optuna was not run.
- OOF was not regenerated.
- Segmentation was not created.
- Final model selection was not performed.
- Campaign threshold was not confirmed.
- Raw source CSV files were not modified.
- park.ingyeom and _data were not modified.

## 07~10 pending validation caveat

07~10 remain pending validation.

07~10 are temporarily deferred, not skipped or completed.

## Safe wording

- SHAP is model explanation, not causality.
- Promo1 is the main business scope; promo0 is the comparison scope.
- Demographic features are not representative segment rules by default.
- Age/gender may be used as action personalization layer only after EDA evidence.
- is_churn_prevented is approved historical context feature with caveat.
- 07~10 remain pending validation.
- Segmentation requires user review after SHAP validation.

## Unsafe wording

- SHAP proves causality.
- 100원딜 caused churn.
- age/gender causes churn.
- is_churn_prevented proves current intervention effect.
- segmentation can start automatically.
- final segment names are confirmed.
- 07~10 are completed.

## Plot status

Created figure count: 6.

SHAP or coefficient fallback count: 0.

## Next action

Review the 16 ZIP package. After SHAP validation, decide whether to proceed to 17 segmentation or run demographic EDA first.
