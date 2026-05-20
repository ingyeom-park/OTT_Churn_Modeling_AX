# 06x_dataset_generation_260515

## Cold Start Row-Level Hotfix
The previous 06x retry passed row policy, but its cold_start fixed calculation failed semantic review because it used a USER_KEY-level first-watch basis. This hotfix recalculates first_watch_rel_day by `master_row_id`, treating each master row as one subscription-event row.

## Row-Level Calculation
Each source master row receives `master_row_id`. View rows are joined through User_Mapping and View_History, `watch_rel_day = watch_date - reg_date` is computed per master row, only `0 <= watch_rel_day <= 20` is used, and the minimum per `master_row_id` becomes `first_watch_rel_day`.

## Validation Counts
- Raw full master changed counts: 3d = 1802, 7d = 985.
- Primary main cohort changed counts: 3d = 1786, 7d = 969.
- Negative first_watch_rel_day count must be 0. Current count: 0.

## Dataset Policy
The primary main cohort is 23,097 rows for the PUBLIC source dataset. Conservative and expanded datasets are regenerated from that cohort. Model features use `is_cold_start_3d_fixed` and `is_cold_start_7d_fixed`, not original `is_cold_start_3d` or `is_cold_start_7d`.

## New Feature Policy
No new feature was added in this hotfix. The only generated feature columns remain the previously approved `is_basic`, `is_cold_start_3d_fixed`, and `is_cold_start_7d_fixed`.

## 07x Readiness
07x may proceed only if `06x_final_checks.csv` has `critical_fail_count_zero = PASS` and `06x_cold_start_hotfix_validation.csv` has PASS for both raw and primary bases.

## Other Caveats
- `old_movie_ratio_5y`: Kwangil master value retained as-is; 9-row mismatch caveat remains.
- Genre ratios: Kwangil master value retained as-is; Movie_Master can have multiple categories for the same MOVIE_NUM.
- `watch_ratio_under_1m` and `watch_ratio_under_5m`: official thresholds are <= 1 minute and <= 5 minutes.
