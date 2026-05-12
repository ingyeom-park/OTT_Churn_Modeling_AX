# 06c v2 Overfitting, Leakage, and Target-Proxy Adversarial Audit

Generated at: 2026-05-11T15:53:15

## 1. Re-stated Concern
The mentor concern is valid: v2 AUC values around 0.87 to 0.90 are much higher than the earlier v1 baseline and may be overfitting, leakage, or a too-good-to-be-true target proxy.

Existing Stage 06b checks passed target shuffle, repeated USER_KEY group split, and official USER_KEY group split diagnostics. These checks are necessary, but not sufficient, because a model can pass them while still relying on behavior observed very close to the target decision.

## 2. Time-Window Shrinkage
w1_1 and w1_2 were approximated only with in-memory week-level proxy columns available inside the saved w1_3 table. Exact w1_1/w1_2 content reconstruction is BLOCKED without rebuilding Stage 03/04 audit-only features.

## 3. Top-Feature Removal
The largest HGB AUC drop from fixed removal tests was 0.0464. Large drops after removing timing/usage features should be interpreted as target-adjacent behavior risk, not proof of direct leakage.

## 4. Content Proxy Audit
Content watch_time and session_count groups are high-risk content proxies because they can duplicate usage intensity. Genre ratio groups are safer than volume features, but still conditional on observed viewing.

## 5. Single-Feature Audit
Single-feature AUC and bin tables were generated for top TRUE SHAP features and watch/no-watch flags. Near-deterministic flags should be treated as a warning sign for target adjacency.

## 6. Subgroup Generalization
Subgroup AUC rows identify where performance collapses or remains stable across promotion, price, max_screen, watch-history, and high-risk product groups.

## 7. Harder Split Diagnostics
Repeated GroupShuffleSplit, product-code holdout, and max-screen holdout diagnostics were run where feasible. reg_date time split is blocked because reg_date is not present in the Stage 05 modeling table.

## 8. Distribution Shift
Train/test top-feature distribution shift was checked using means, medians, quantiles, missing rates, categorical proportions, and standardized mean differences.

## 9. Duplicate Feature Vectors
Exact and rounded near-duplicate train/test feature-vector hashes were checked after removing metadata and target.

## 10. Label and Temporal Recheck
The conservative w1_3 feature list contains no end_date, duration_days, raw watch_date/watch_day, w1_4 columns, target, USER_KEY, USER_NUM, or MOVIE_NUM.

## 11. Calibration and Decile Stability
Calibration bins, Brier score, risk decile churn rates, and repeated-split top-decile rows were generated.

## 12. Conservative Metric Recommendation
- A_full_model_result: window=w1_3, model=HistGradientBoostingClassifier, AUC=0.8705, churn-risk PR AUC=0.7046, top-decile lift=2.7335, mentor_safe=N
- B_conservative_model_result: window=w1_3, model=HistGradientBoostingClassifier, AUC=0.8659, churn-risk PR AUC=0.6933, top-decile lift=2.7044, mentor_safe=Y_WITH_CAVEATS
- C_ultra_conservative_model_result: window=w1_2_proxy, model=LogisticRegression, AUC=0.6506, churn-risk PR AUC=0.3932, top-decile lift=1.4579, mentor_safe=Y_FOR_MENTOR_RESPONSE

## 13. Final Verdict
Final conservative classification: `target_adjacent_but_not_direct_leakage`.

This does not prove direct leakage. However, the audit treats the high AUC as timing-sensitive and target-adjacent until an earlier-window rebuild or operational validation confirms otherwise.

## Required Output Index
- Summary JSON: `park.ingyeom/reports/data/06c_v2_overfitting_leakage_adversarial_audit/06c_adversarial_audit_summary.json`
- Mentor response: `park.ingyeom/reports/data/06c_v2_overfitting_leakage_adversarial_audit/06c_mentor_response_summary.md`
- Final checks: `park.ingyeom/reports/tables/06c_v2_overfitting_leakage_adversarial_audit/06c_final_checks.csv`
