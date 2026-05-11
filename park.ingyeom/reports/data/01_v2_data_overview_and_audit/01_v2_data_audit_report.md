# 01_v2 Data Audit Report

## What Was Inspected
- _data/01_raw/Membership.csv
- _data/01_raw/User_Mapping.csv
- _data/01_raw/View_History.csv
- _data/01_raw/Movie_Master.csv

## What Was Not Inspected
- __legacy
- park.ingyeom/__legacy
- old reports
- old handoff documents
- team member folders
- preprocessed/interim datasets

## Confirmed Facts
- Active v2 raw files inspected: Membership, User_Mapping, View_History, Movie_Master.
- Membership rows: 24074; target distribution: {'Y': 17325, 'N': 6749}.
- Membership unique USER_KEY count: 23679; duplicate USER_KEY keys: 261.
- Strict target-conflict groups: 35; strict conflict rows: 73.
- User_Mapping one-to-many USER_KEY count: 50.
- View_History rows: 175301; watch_day range: 2021-03-01 to 2021-04-12.
- Movie_Master duplicate MOVIE_NUM count: 380.

## Suspicious Issues
- Strict target-conflict rows exist and require label-policy review before modeling.
- Some USER_KEY values map to multiple USER_NUM values; joins must not multiply Membership rows silently.
- Movie_Master has duplicate MOVIE_NUM rows; raw join to View_History would create multiplication.
- watch_date == end_date exists and end_date inclusiveness remains unresolved.
- Very short watch logs exist and should be classified before deciding whether to keep, downweight, or exclude them.

## Unresolved Business-Definition Questions
- Is end_date inclusive or exclusive for behavior observation and leakage control?
- Should strict target-conflict rows be excluded, flagged, or resolved by a documented business rule?
- Should one USER_KEY mapping to multiple USER_NUM values be interpreted as multiple devices/accounts or mapping duplication?
- Which Movie_Master duplicate row should represent a MOVIE_NUM when metadata differs?
- Are 1-minute and <=5-minute watch logs meaningful engagement, accidental playback, or noise?

## Recommended Preprocessing Candidates
- Assign membership_row_id before any joins and preserve one final row per membership_row_id.
- Aggregate all mapped USER_NUM logs back to membership_row_id instead of expanding Membership rows.
- Deduplicate Movie_Master by MOVIE_NUM before any content-feature join, with conflict audit retained.
- Keep w1_3 and w1_4 feature windows separate in later stages.
- Exclude raw identifiers and raw dates from model features in later stages.

## Old v1 Assumptions Still Plausible
- The broad workflow EDA -> modeling -> interpretation -> segmentation -> retention strategy remains plausible as a business workflow.
- Leakage-controlled baseline modeling remains a necessary next step.
- Audit artifacts should be retained for every exclusion or correction decision.

## Old v1 Assumptions That Must Be Revalidated
- All old row counts and AUC values must be recomputed from v2.
- Old 1-3 week observation-window assumptions must be revalidated against v2, especially with week-4 behavior available.
- Old preprocessing rules for duplicates, short watches, end_date handling, and Movie_Master metadata must be revalidated.
- Old feature conclusions must not be carried forward without v2 evidence.

## Temporal Join Expansion Validation

- Raw `View_History` rows: 175,301.
- Joined `Membership -> User_Mapping -> View_History` rows used in temporal audit: 180,001.
- Expansion rows: 4,700.
- Expansion ratio: 1.026811.
- Raw view rows attached to multiple `membership_row_id` values: 2,577.
- Membership rows attached to multiple `USER_NUM` values: 205.
- `USER_KEY` values with multiple Membership events: 261.
- Raw view rows attached to zero Membership rows: 0.
- Gross extra rows from multiple Membership-event attachment: 4,700.

Interpretation: the temporal audit is membership-event-level, not raw ViewHistory-level. A raw view row can be counted more than once when the mapped `USER_KEY` has multiple Membership subscription events. Some raw view rows can also be counted zero times when their mapped `USER_KEY` is absent from Membership. The net result is 180,001 joined temporal rows versus 175,301 raw ViewHistory rows.

- `watch_date_gt_end_date = 5,740` is a joined membership-event-level count, not a raw ViewHistory-level count.
- `watch_date_eq_end_date = 260` is a joined membership-event-level count, not a raw ViewHistory-level count.
- Detailed audit table: `park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_join_expansion_summary.csv`.

## Exact Output File List
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_join_expansion_summary.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_raw_file_inventory.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_schema_summary.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_membership_target_summary.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_membership_duplicate_audit.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_membership_target_conflict_rows.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_membership_duration_distribution.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_membership_value_anomaly_summary.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_usermapping_cardinality_audit.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_viewhistory_basic_audit.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_viewhistory_duplicate_audit.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_membership_view_temporal_audit.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_moviemaster_duplicate_audit.csv
- park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_audit_final_checks.csv
- park.ingyeom/reports/data/01_v2_data_overview_and_audit/01_v2_data_audit_report.md
- park.ingyeom/reports/data/01_v2_data_overview_and_audit/01_v2_audit_summary.json

## Final Checks
See `01_v2_audit_final_checks.csv` for pass/fail validation.
