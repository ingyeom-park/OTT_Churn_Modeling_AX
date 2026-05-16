# 05y feature approval and dictionary patch2 260515

## Purpose
Patch semantic review issues in the previous 05y package before 06x dataset generation. This step is feature contract and feature dictionary quality control only. No modeling, EDA, SHAP, Optuna, or segmentation was performed.

## Previous 05y Issues Patched
- v3 team variable CSV was actually loaded and compared in `05y_patch2_v3_comparison_summary.csv`.
- `05y_feature_dictionary.xlsx` formula placeholders were removed for usable model candidates.
- `is_user_verified` was moved from pending to approved for expanded_feature_set.
- `genre_diversity_count` and genre ratio caveats were made consistent across dictionary, expanded contract, and formula validation summary.
- cold_start original and fixed policy descriptions were strengthened.

## v3 Comparison Result
- v3 rows loaded: 80.
- current-only or generated/fixed rows are marked as `current_only_not_in_v3` with generic mismatch/action wording and no `current_feature_name` column.
- v3-only rows are marked as `v3_only_not_in_current_contract` and require human review if the team wants to add them later.
- formula mismatches are recorded for under_1m/under_5m threshold policy and cold_start fixed policy.

## User Approval Reflected
- `is_user_verified` is approved for expanded_feature_set.
- product_code, billing_method, payment_device, gender, age, reg_hour, price, max_screen, reg_date, end_date, USER_KEY, and is_repurchase are excluded from model features or retained only for audit/target/group-key use.
- `is_churn_prevented` is approved as a historical ever-benefited flag.
- `is_promotion` remains a split key and is only allowed as a feature in overall_with_promotion.

## Formula Dictionary Patch
- Usable feature formulas no longer contain the previous placeholder text.
- Source-retained features explicitly say `source master value used as-is`.
- Formula gaps are marked only as `unresolved exact formula` with the unclear part stated.

## cold_start Policy
- Original `is_cold_start_3d` appears to be day0 through day3 and is not used as a model feature.
- Original `is_cold_start_7d` appears to be day0 through day7 and is not used as a model feature.
- `is_cold_start_3d_fixed` uses `first_watch_rel_day <= 2`.
- `is_cold_start_7d_fixed` uses `first_watch_rel_day <= 6`.
- Hotfix official changed row counts: 1,782 rows for 3d and 964 rows for 7d.

## old_movie_ratio A Option
- `old_movie_ratio(5y)` keeps Kwangil source master value as-is.
- No fixed replacement is created.
- The 9-row raw Movie_Master reconstruction mismatch is retained as a caveat.

## under_1m/under_5m Formula
- `watch_ratio_under_1m` is officially recorded as `<= 1` minute.
- `watch_ratio_under_5m` is officially recorded as `<= 5` minutes.
- v3 `<` descriptions are recorded as policy mismatches, and Kwangil master policy is followed.

## Genre Caveat
- `genre_diversity_count` and genre ratio features carry the same caveat everywhere: Movie_Master_v2 can contain multiple category rows for the same MOVIE_NUM.

## 06x Gate
- Can proceed to 06x: yes.
- Blocking issue: .

## 05y Patch2 Hotfix 260515
- Corrected cold_start changed row counts to 1,782 for `is_cold_start_3d` and 964 for `is_cold_start_7d`.
- Fixed excluded feature dictionary source/principle/formula descriptions for membership/source-master columns, target label, and identifier/group key.
- Confirmed genre caveats are consistent across expanded contract, formula validation summary, and feature dictionary.
- Kept v3 current-only handling in existing columns without adding `current_feature_name`.
