# PUBLIC 15 OOF Score Generation Hotfix 260520

## Purpose

This hotfix regenerates and packages PUBLIC Step 15 OOF score outputs so they can be reviewed before any SHAP or segmentation work.

## Why Hotfix Was Needed

The previous 15 review zip omitted row-level OOF long/wide outputs and the executed notebook.

The previous overlap used score thresholds 0.5/0.6/0.7, which is not the required top10/top20/top30 definition.

This hotfix uses percentile-based top10/top20/top30 high-risk flags.

SHAP and segmentation remain blocked until user review.

## Inputs

- `PUBLIC/data/06_model_input_promo_0.csv`
- `PUBLIC/data/06_model_input_promo_1.csv`
- Step 11 emergency four-model reference final_result, trials_all, and feature manifests.

## Model Families

- LogisticRegression
- GradientBoosting

## Scope Definitions

- promo0: non-100-won-deal comparison scope
- promo1: 100-won-deal scope

Promo0 and promo1 are never merged to choose a single global winner.

## Feature Policy

`is_repurchase`, identifiers, `is_promotion`, raw retention ratios, previous scores, and fold columns are excluded from model features.

`retention_w2_ratio` and `retention_w3_ratio` are excluded.

`log_retention_w2_ratio` and `log_retention_w3_ratio` are used.

`is_churn_prevented` is an approved historical context feature with caveat.

## Split Policy

StratifiedKFold with five folds is used for OOF generation. USER_NUM is checked when available. If USER_NUM is absent, the file records the user-confirmed upstream dedup caveat rather than silently marking group split as PASS.

## OOF Generation Method

OOF predictions are generated for four log-retention-based model/scope combinations using parameters parsed from existing `final_result.csv` files. No Optuna or hyperparameter search is run.

`repurchase_score_oof = P(is_repurchase=1)`.

`churn_risk_score_oof = 1 - repurchase_score_oof`.

## OOF Row-Level Outputs

- `15_oof_score_long.csv`
- `15_oof_score_wide.csv`
- `15_oof_score_wide_promo0.csv`
- `15_oof_score_wide_promo1.csv`

## OOF Metric Summary

ROC-AUC is the primary metric.

PR-AUC is a secondary metric.

F1, precision, recall, and brier score are included as auxiliary review metrics.

## GB vs LR High-Risk Overlap Using Top10/Top20/Top30

High-risk overlap is based on top10/top20/top30 percentile ranks by churn risk within each promo scope.

It is not based on fixed score thresholds 0.5/0.6/0.7.

The overlap interpretation is not a final segment.

## What Was Not Done

- No Optuna was run.
- No SHAP was generated.
- No segmentation was generated.
- No final model selection was made.
- No campaign threshold was finalized.
- No raw source CSV was modified.
- No `park.ingyeom` file was modified.

## 07~10 Pending Validation Caveat

07~10 remain pending validation. This hotfix does not mark them complete.

## Safe Wording

- OOF scores were generated for four log-retention-based model/scope combinations.
- ROC-AUC is the primary metric.
- PR-AUC is a secondary metric.
- is_churn_prevented is an approved historical context feature with caveat.
- 07~10 remain pending validation.
- SHAP and segmentation require user review after OOF validation.
- high-risk overlap is based on top10/top20/top30 percentile ranks, not fixed score thresholds.

## Unsafe Wording

- This is final model selection.
- 07~10 are completed.
- OOF score is final campaign threshold.
- SHAP can start automatically.
- Segmentation can start automatically.
- PR-AUC alone proves model quality.
- is_churn_prevented proves current intervention effect.
- threshold 0.5/0.6/0.7 is equivalent to top10/top20/top30.

## Next Action

Upload the hotfix review zip to ChatGPT and verify OOF long/wide, executed notebook, metric summary, overlap, and readiness before deciding whether to proceed to SHAP or resolve 07~10 validation first.
