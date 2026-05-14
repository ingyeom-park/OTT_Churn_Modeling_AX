# 02_v2 Preprocessing Policy Validation Report

## Scope
- Re-read Stage 01 outputs and active v2 raw files.
- Validate preprocessing candidates only.
- No interim dataset, usage feature, modeling table, or trained model was created.

## Applied Rules
- `APPLIED_NONE_01`: no row exclusion or correction was applied in Stage 02. All proposed rules remain candidates.

## Candidate Findings
- Strict target conflict groups: 35 groups, 73 rows.
- Exact duplicate groups: 67 groups.
- Core-event ambiguous groups: 35 groups.
- UserMapping one-to-many USER_KEY cases: 50.
- UserMapping many-to-one USER_NUM cases: 0.

## Duration Policy Validation
- Compared keep-all-parseable, positive-only, 31-or-32-only, and 28-to-35-day policies.
- No duration policy was applied. Final policy is deferred until business definition of subscription duration and end_date inclusiveness is confirmed.

## Decision Matrix
- Decisions are limited to `apply`, `flag`, `keep`, `defer`, and `ask_mentor` candidates.
- Current applied decision is only `keep` for the scope guard, meaning no preprocessing output is produced.

## Row Exclusion Reason Codes
- Candidate row-exclusion reason rows: 144.
- Every candidate row-exclusion row has a reason_code in `02_v2_row_exclusion_reason_candidates.csv`.

## Output Files
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_stage01_reread_inventory.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_strict_conflict_group_audit.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_strict_conflict_sample_rows.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_duplicate_group_audit.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_duplicate_group_sample_rows.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_candidate_rule_summary.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_candidate_rule_affected_samples.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_candidate_policy_before_after_counts.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_duration_policy_comparison.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_duration_policy_samples.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_usermapping_one_to_many_audit.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_usermapping_many_to_one_audit.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_join_expansion_by_membership_policy.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_value_anomaly_audit.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_value_anomaly_samples.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_decision_matrix.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_reason_code_catalog.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_row_exclusion_reason_candidates.csv
- park.ingyeom/reports/tables/02_v2_preprocessing_policy_validation/02_v2_final_checks.csv
- park.ingyeom/reports/data/02_v2_preprocessing_policy_validation/02_v2_policy_validation_summary.json
- park.ingyeom/reports/data/02_v2_preprocessing_policy_validation/02_v2_preprocessing_policy_validation_report.md

## Final Checks
- stage01_outputs_reread: PASS (checked=11)
- raw_files_unchanged: PASS (raw file size and mtime unchanged)
- no_interim_dataset_created: PASS (Stage 02 validation writes reports only)
- no_usage_features_created: PASS (No usage feature table is written)
- no_model_trained: PASS (No modeling library or training routine is used)
- strict_target_conflicts_validated: PASS (groups=35)
- duration_policies_compared: PASS (policies=4)
- join_expansion_recomputed: PASS (policies=6)
- decision_matrix_created: PASS (rules=25)
- decision_values_are_allowed: PASS (allowed=apply|flag|keep|defer|ask_mentor)
- candidate_and_applied_rules_separated: PASS (applied scope guard is separate from candidate preprocessing rules)
- every_candidate_row_exclusion_has_reason_code: PASS (candidate_reason_rows=144)
- all_required_outputs_created: PASS (required_csvs=18)
- markdown_report_created: PASS (park.ingyeom/reports/data/02_v2_preprocessing_policy_validation/02_v2_preprocessing_policy_validation_report.md)
- json_summary_created: PASS (park.ingyeom/reports/data/02_v2_preprocessing_policy_validation/02_v2_policy_validation_summary.json)
