# 06b_v2 Baseline Sanity Audit Report

## Scope
- Stage 06b audited Stage 06 high AUC plausibility and leakage safety.
- No production model, SHAP, segmentation, business simulation, Optuna, or `_data` output was created.

## High AUC Review
- Best observed model: w1_4 / membership_plus_usage_content_w1_4_without_churn_prevented / LGBMClassifier with ROC AUC 0.9037.
- Conservative recommended baseline: w1_3 / membership_plus_usage_content_w1_3_without_churn_prevented / HistGradientBoostingClassifier with ROC AUC 0.8705.
- Business-interpretable baseline: w1_3 / membership_plus_usage_content_w1_3_without_churn_prevented / LogisticRegression with ROC AUC 0.8415.
- Holdout results with ROC AUC >= 0.90: 4.

## Sanity Tests
- Target shuffle ROC AUC: 0.4672; status: PASS.
- Repeated GroupShuffleSplit ROC AUC mean/std: 0.8751 / 0.0018.
- Naive random split diagnostic ROC AUC: 0.8778; USER_KEY overlap: 79.
- Largest conservative drop-test AUC drop: 0.0464.

## Interpretation
- Conservative baseline decision: cautioned.
- Reason: Leakage smoke tests passed, but AUC is high and behavior/content features require business review before final claims.
- Safe to use: Stage 06 split and score-orientation mechanics, because group leakage and target-shuffle checks passed.
- Plausible but requires caution: the conservative w1_3 behavior/content baseline, because it uses behavioral features with high predictive power.
- Not ready for final claims: w1_4 high-AUC results and any result driven by late-period behavior until business timing is explicitly framed.

## Required Output Tables
- park.ingyeom/reports/tables/06b_v2_baseline_sanity_audit/06b_high_auc_review_table.csv
- park.ingyeom/reports/tables/06b_v2_baseline_sanity_audit/06b_feature_family_ablation_summary.csv
- park.ingyeom/reports/tables/06b_v2_baseline_sanity_audit/06b_suspicious_feature_audit.csv
- park.ingyeom/reports/tables/06b_v2_baseline_sanity_audit/06b_drop_suspicious_feature_test.csv
- park.ingyeom/reports/tables/06b_v2_baseline_sanity_audit/06b_target_shuffle_test.csv
- park.ingyeom/reports/tables/06b_v2_baseline_sanity_audit/06b_repeated_group_split_stability.csv
- park.ingyeom/reports/tables/06b_v2_baseline_sanity_audit/06b_churn_risk_decile_audit.csv
- park.ingyeom/reports/tables/06b_v2_baseline_sanity_audit/06b_final_checks.csv
