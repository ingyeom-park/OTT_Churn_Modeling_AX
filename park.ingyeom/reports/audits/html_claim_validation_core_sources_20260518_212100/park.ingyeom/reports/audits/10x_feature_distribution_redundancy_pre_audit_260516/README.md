# 10x feature distribution redundancy pre-audit

## Purpose
10x is a feature distribution EDA plus redundancy / group-proxy pre-audit step after 09x. It uses the 06x conservative and expanded datasets, 07x AARRR mapping, 08x promotion vs nonpromotion EDA, and 09x promotion x repurchase 2x2 EDA outputs.

## What 10x does
- Profiles conservative_safe_22 and expanded_feature_set distributions overall, by promotion split, and by promotion x repurchase 2x2 cohorts.
- Audits zero-inflation, heavy-tail, outlier, sparse binary, near-constant, pairwise correlation, VIF, duplicate-like risk, group-proxy risk, and leakage-suspect candidates.
- Carries content/genre caveats, old_movie_ratio_5y 9-row mismatch caveat, cold_start_fixed caveat, and context/profile/payment proxy-risk caveat forward.
- Creates handoff tables for 11x / 12x / SHAP / segmentation review.

## What 10x does not do
10x does not perform modeling, target prediction, train/test split, SHAP, Optuna, segmentation, final segment creation, final business recommendation, causal claim, feature importance claim, feature removal, or feature selection decision.

## Strengthened relative to master plan 7-10
This step adds a stricter source fingerprint before/after check, 2x2 distribution review, VIF diagnostic, redundancy cluster pre-audit, duplicate-like feature audit, group-proxy review, target-leakage suspect pre-audit, and a modeling preflight risk register.

## Conservative / expanded distinction
- conservative_safe_22 rows: 23079, columns: 24
- expanded_feature_set rows: 23079, columns: 82
- Row alignment: True

## Diagnostic summary
- Numeric overall rows: 69
- Binary overall rows: 32
- Group numeric rows: 483
- Group binary rows: 224
- Zero/tail risk rows: 69
- Near-constant/group-proxy rows: 33
- Pairwise correlation rows: 3312
- Redundancy clusters: 15
- VIF rows: 101
- Duplicate-like rows: 76
- Leakage suspect rows: 101

## Interpretation caveats
Distribution differences are not feature importance. Correlation and VIF do not imply automatic removal. Group-proxy risk does not imply automatic exclusion. Referral has no directly observed feature and must not be claimed as data-validated.

## Downstream handoff
The next step is 11x modeling preflight or 11x baseline growth comparison, not direct Optuna, SHAP, or segmentation. 11x must save and inspect the actual model input feature list, verify whether expanded features were actually used, review near-constant/group-proxy sensitivity, and carry redundancy clusters into interpretation guardrails. SHAP should interpret correlated features by family/cluster. Segmentation should validate rule and distribution before provisional naming.

## Hotfix: 10x_feature_distribution_redundancy_pre_audit_260516_hotfix
This hotfix repairs validation and packaging issues without discarding 10x, rerunning a new analysis direction, modeling, splitting data, predicting, SHAP, Optuna, segmentation, feature removal, or feature-selection decisions.

### Artifact alignment
- `10x_feature_distribution_redundancy_pre_audit_260516_executed.ipynb` was created from nbconvert execution and retains visible code-cell outputs.
- `10x_hotfix_execution_log.txt` records notebook execution/output checks, ZIP duplicate checks, age_group correction, policy-table creation, warnings, errors, and final status.
- `10x_final_checks.csv` and `10x_hotfix_final_checks.csv` are rebuilt to match the actual hotfix artifacts.

### Redundancy and VIF policy
- `expanded_full` preserves the 80 `use_as_feature=yes` features.
- High VIF, high correlation, duplicate-like evidence, one-hot full sets, nested ratios, and compositional ratios are not removal decisions.
- `10x_feature_refinement_candidate_policy.csv` is a policy table for 11x redundancy-aware sensitivity and interpretation grouping only.
- Feature removal requires user approval.
- Logistic Regression coefficient interpretation is limited under high-VIF families.
- Tree/boosting models are not excluded solely due to high VIF.
- Future SHAP interpretation should be by feature family or redundancy cluster when attribution can split across correlated features.

### Default demographic artifact caveat
`age_group` is no longer treated as a simple near-constant signal. It is managed as default demographic artifact / structural group-proxy risk under the user domain hypothesis that iOS App Store payment and non-verified accounts may create default-like age, gender, and authentication patterns. These variables should not be interpreted directly as true customer demographics.

### 11x handoff
11x should distinguish `conservative_safe_22`, `expanded_full`, and optional `expanded_redundancy_aware_sensitivity`, and must save the actual model input feature list for each scope.

