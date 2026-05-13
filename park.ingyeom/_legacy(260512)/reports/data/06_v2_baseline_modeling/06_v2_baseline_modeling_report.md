# 06_v2 Baseline Modeling Report

## Scope
- Stage 06 trained and evaluated baseline models only.
- No SHAP, segmentation, business simulation, Optuna, or broad hyperparameter tuning was run.
- w1_3 is the early-observation window and is closer to early intervention.
- w1_4 is an end-of-period / late-period behavior window. Higher w1_4 performance is not leakage by itself, but it changes the business timing interpretation.

## Target And Score Direction
- `is_repurchase` was mapped as Y -> 1 and N -> 0.
- `repurchase_score` means P(is_repurchase = Y).
- `churn_risk_score` is 1 - repurchase_score. High churn-risk targeting must use `churn_risk_score`, not `repurchase_score`.
- Threshold 0.5 is a diagnostic threshold only, not an optimized business threshold.

## Baseline ROC AUC Answers
- Membership-only baseline ROC AUC: w1_3 0.5737 (LogisticRegression, membership_only_without_churn_prevented); w1_4 0.5737 (LogisticRegression, membership_only_without_churn_prevented).
- Usage-only baseline ROC AUC: w1_3 0.8137 (LGBMClassifier, usage_w1_3_only); w1_4 0.8508 (LGBMClassifier, usage_w1_4_only).
- Content-only baseline ROC AUC: w1_3 0.7737 (ExtraTreesClassifier, content_w1_3_only); w1_4 0.8024 (ExtraTreesClassifier, content_w1_4_only).
- Membership+usage ROC AUC: w1_3 0.8241 (HistGradientBoostingClassifier, membership_plus_usage_w1_3_with_churn_prevented); w1_4 0.8601 (LGBMClassifier, membership_plus_usage_w1_4_with_churn_prevented).
- Membership+usage+content ROC AUC: w1_3 0.8709 (LGBMClassifier, membership_plus_usage_content_w1_3_with_churn_prevented); w1_4 0.9037 (LGBMClassifier, membership_plus_usage_content_w1_4_with_churn_prevented).
- Mean matched w1_4 minus w1_3 ROC AUC difference: 0.0209.
- Mean with_churn_prevented minus without_churn_prevented ROC AUC difference: -0.0001.

## Recommendation
- Best observed model: w1_4 / membership_plus_usage_content_w1_4_without_churn_prevented / LGBMClassifier with ROC AUC 0.9037.
- Conservative recommended baseline: w1_3 / membership_plus_usage_content_w1_3_without_churn_prevented / HistGradientBoostingClassifier with ROC AUC 0.8705.
- Business-interpretable baseline: w1_3 / membership_plus_usage_content_w1_3_without_churn_prevented / LogisticRegression with ROC AUC 0.8415.
- Suspiciously high results with ROC AUC >= 0.90: 4.
- Results depending on w1_4 or `is_churn_prevented` should be reviewed before retention strategy use.

## Before SHAP
- Confirm whether `is_churn_prevented` is valid historical prior information or a post-treatment variable.
- Review top w1_4 gains under the late-period interpretation.
- Confirm no feature family contains unresolved temporal leakage.
- Choose one conservative, timing-defensible model before explanation.

## Output Files
- Data: park.ingyeom/reports/data/06_v2_baseline_modeling
- Tables: park.ingyeom/reports/tables/06_v2_baseline_modeling
- Figures: park.ingyeom/reports/figures/06_v2_baseline_modeling
