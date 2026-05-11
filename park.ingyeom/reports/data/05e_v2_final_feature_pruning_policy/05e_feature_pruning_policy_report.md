# 05e v2 Final Feature Pruning Policy Report

## Why Pruning Was Necessary
- Stage 05 full datasets are exploratory because original variables and derived variables coexist.
- Stage 06c classified high AUC as target-adjacent but not direct leakage.
- Stage 06d found structural redundancy and multicollinearity risk, making individual feature interpretation unsafe.
- Stage 06f showed reduced diagnostic models can retain useful ranking, so final reporting datasets should be pruned.

## Key Policy Corrections
- `product_code` is excluded from default official feature sets and appears only in sensitivity variants.
- `has_watch_obs` is treated as a behavior-presence proxy and appears only in sensitivity variants.
- Any w1_3 feature set with week3 variables is labeled `timing_sensitive_w1_3`.
- A week1/week2-only early-safer variant is created.
- w1_4 is labeled `late_period_only` and is not an early-warning candidate.

## Kept Feature Families
- Membership context without `product_code` by default.
- Weekly source watch/session variables instead of totals, ratios, and deltas.
- Genre ratio and entropy features as preference proxies.
- Minimal coverage/release proxy features where interpretable.

## Dropped Feature Families
- Forbidden role columns from feature sets.
- `no_watch_obs_flag`, default `has_watch_obs`, total watch time, ratios, deltas, first/last watch rel day, short-watch variables, top_genre family, genre watch_time/session_count, and content volume proxies.

## Final Candidate Feature Sets
- `pruned_w1_3_core_interpretable_without_product_code_without_watch_presence_flag`: 31 features, label `timing_sensitive_w1_3`, claim `presentation_candidate_with_timing_caveat`.
- `pruned_w1_3_core_interpretable_with_product_code_without_watch_presence_flag`: 32 features, label `timing_sensitive_w1_3`, claim `sensitivity_only_product_memorization_risk`.
- `pruned_w1_3_core_interpretable_without_product_code_with_watch_presence_flag`: 32 features, label `timing_sensitive_w1_3`, claim `sensitivity_only_watch_presence_proxy_risk`.
- `pruned_w1_3_membership_usage_only_without_product_code_without_watch_presence_flag`: 18 features, label `timing_sensitive_w1_3`, claim `presentation_candidate_with_timing_caveat`.
- `pruned_w1_3_early_safer_week1_2_without_product_code_without_watch_presence_flag`: 16 features, label `early_safer_w1_3_proxy`, claim `mentor_safe_early_safer_proxy`.
- `pruned_w1_3_genre_ratio_only_added_without_product_code_without_watch_presence_flag`: 27 features, label `early_cautioned_preference_proxy`, claim `genre_preference_diagnostic`.
- `pruned_w1_4_late_period_comparison_without_product_code_without_watch_presence_flag`: 33 features, label `late_period_only`, claim `late_period_comparison_only`.

## Original Stage 05 Status
- Original Stage 05 modeling datasets should now be treated as exploratory/full datasets, not final reporting datasets.
