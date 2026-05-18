# 05y_feature_approval_and_dictionary_260515

## Purpose
Apply the user-approved 05x feature decisions and create the safe-name mapping and feature dictionary package before 06x dataset generation.

## User Approval Summary
- Excluded parent/raw context variables: product_code, billing_method, payment_device, gender, age, reg_hour, price, max_screen, reg_date, end_date, USER_KEY.
- Target: is_repurchase.
- Approved derived context variables: payment device flags, gender flags, age_group, registration time-band flags, reg_is_weekend, is_standard, is_premium, is_basic.
- Usage summary features: all approved.
- Content and genre features: all approved with caveats where noted.
- is_promotion: split criterion; feature only in overall_with_promotion.
- is_churn_prevented: approved as historical ever-benefited flag, interpreted as users who ever accepted churn-prevention benefit.
- recency: approved.

## Conservative And Expanded Plans
- Conservative plan follows the 05x conservative_safe_22 basis, replacing cold_start originals with fixed names.
- Expanded plan includes approved context, usage, content, genre, recency, and scope-limited is_promotion policy.

## Fixed Variables
- is_cold_start_3d_fixed = 1 if first_watch_rel_day <= 2 else 0.
- is_cold_start_7d_fixed = 1 if first_watch_rel_day <= 6 else 0.
- is_basic = 1 if is_standard == 0 and is_premium == 0 else 0.
- old_movie_ratio_5y uses the Kwangil master value as-is. This is option A because the user approved preserving the master value and recording the 9-row mismatch as a caveat instead of rebuilding a fixed column.

## Rename Rules
Parentheses become underscores, percent signs become pct, spaces are removed, special characters become underscores, repeated underscores collapse to one, and leading/trailing underscores are removed. Original names are preserved in mapping files.

## v3 Comparison
v3 active file status: missing in active park.ingyeom tree.

## 06x Gate
06x can proceed conditionally using approved features and safe_model_feature_name. Pending-user-review features must remain excluded until separately approved.

## Remaining Caveats
- old_movie_ratio_5y: 9-row mismatch caveat retained.
- genre ratios: Movie_Master same MOVIE_NUM multiple category caveat retained.
- pending_user_review feature count: 1.
