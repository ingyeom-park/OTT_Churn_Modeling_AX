# PUBLIC 12 Four-Model Comparison Review

## Purpose

This is not a task for selecting the best-performing model.

This is a strict validation review of the existing log-retention-only four-model emergency reference outputs from leakage, proxy, overfit, and split-issue perspectives.

Because AUC appears unusually high for this project context, this step treats high performance as a validation target rather than as immediate evidence of model quality.

현재 AUC가 프로젝트 맥락상 과도하게 높아 보일 수 있으므로, 이번 단계에서는 높은 성능을 곧바로 성과로 해석하지 않고 leakage, proxy, overfit, split issue 검수 대상으로 취급한다.

## Input source

- `PUBLIC/results/11_baseline_growth_comparison_260520/emergency_four_model_reference/`

The four reviewed references are LogisticRegression promo0, LogisticRegression promo1, GradientBoosting promo0, and GradientBoosting promo1.

## Why this is 12 and not 11

Step 11 is the emergency four-model reference stage. Step 12 is the comparison and validation review stage.

12 is not GradientBoosting-only. It compares LR and GB within each promo scope, but it does not perform final model selection.

## 07~10 pending validation caveat

07~10 remain pending validation. This review does not complete or replace those validation steps.

Because of that pending status, this 12 result is not final canonical model selection.

## High AUC suspicion audit

High AUC is not treated as achievement in this step. It is treated as a validation target.

`12_high_auc_suspicion_audit.csv` records `suspicious_high_auc_flag = 1` when any recorded AUC metric is at least 0.90.

Current suspicious flag count: 4.

## Log retention condition check

`log_retention_w2_ratio` and `log_retention_w3_ratio` are confirmed where available, but their presence is also recorded as a caveat because these features may dominate performance or operate as proxies.

Details are saved in `12_log_retention_condition_check.csv`.

## Leakage/proxy feature audit

The leakage/proxy audit checks USER_KEY, is_repurchase, repurchase_score, churn_risk, raw retention ratios, is_promotion scope policy, and target-like or post-outcome suspect features.

Current leakage/proxy statuses: LogisticRegression promo0=FAIL; LogisticRegression promo1=FAIL; GradientBoosting promo0=FAIL; GradientBoosting promo1=FAIL.

Details are saved in `12_leakage_proxy_feature_audit.csv`.

## Split policy audit

Group-aware split or USER_KEY leakage prevention is not marked PASS unless it is directly confirmed.

Current split policy statuses: LogisticRegression promo0=WARN; LogisticRegression promo1=WARN; GradientBoosting promo0=WARN; GradientBoosting promo1=WARN.

Details are saved in `12_split_policy_audit.csv`.

## Final result metric summary

Saved final-result metrics were read from the four `final_result.csv` files only.

The best saved metric is not used by itself to recommend a model.

Details are saved in `12_final_result_metric_summary.csv`.

## Trials overfit and stability summary

`trials_all.csv` was used to inspect overfit rate, top5/top10/top20 overfit rate, valid AUC, and gap where columns were available.

Details are saved in `12_trials_overfit_stability_summary.csv`.

## Scopewise GB vs LR comparison

Promo0 and promo1 are evaluated separately.

Any GB wording is limited to provisional candidate pending leakage/proxy/overfit/split review.

LR remains a baseline/sensitivity reference, also pending leakage/proxy/overfit/split review.

Highest AUC alone does not determine the model.

## OOF readiness decision

OOF generation remains `no` by default.

OOF generation requires user approval.

This task creates only `12_oof_readiness_decision.csv`. It does not create an OOF score table.

## What was not done

- No model retraining was performed.
- No notebook execution was performed.
- No Optuna run was performed.
- No SHAP run was performed.
- No segmentation run was performed.
- No OOF score table was generated.
- No raw source CSV was modified.
- No `park.ingyeom` file was modified.
- No `_data` file was modified.
- No existing result was deleted.

## Safe wording

- This is a four-model comparison review based on existing log-retention-only emergency reference outputs.
- High AUC is a validation target, not immediate model-quality evidence.
- Promo0 and promo1 are evaluated separately.
- GB may be described only as provisional candidate pending leakage/proxy/overfit/split review.
- LR remains baseline/sensitivity candidate pending leakage/proxy/overfit/split review.
- OOF generation requires user approval.
- Final model selection is not allowed from this review alone.

## Unsafe wording

- This is final model selection.
- 07~10 are completed.
- OOF table was generated.
- SHAP can start immediately.
- Segmentation can start immediately.
- Highest AUC alone determines the model.
- GB is the final primary model.

## Next action

Review the generated CSVs and review zip. After review, the user may decide whether to inspect leakage/proxy/split issues more deeply, approve OOF score table generation, or resolve 07~10 pending validation first.
