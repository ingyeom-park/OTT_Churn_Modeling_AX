# 06g v2 Pruned Baseline Modeling Report

## Result Classes
- Full exploratory model: AUC 0.872459; use only as exploratory upper bound.
- Timing-sensitive pruned w1_3 model: best no-product/no-presence AUC 0.861858; usable only with timing caveat.
- Early-safer pruned w1_3 or exact w1_2: pruned early-safer AUC 0.804651; exact w1_2 AUC 0.740175.
- Late-period w1_4 comparison model: AUC 0.896979; not early prediction.

## Final Recommendation
- Recommended model: `HistGradientBoostingClassifier`.
- Recommended feature set: `pruned_w1_3_early_safer_week1_2_without_product_code_without_watch_presence_flag`.
- AUC: 0.804651.
- Churn-risk PR AUC: 0.611947.
- Top-decile lift: 2.587726.
- Feature count: 16.
- Reason: selected by safety priority before performance.

## Answers
1. Best pruned w1_3 model by AUC: `pruned_w1_3_core_interpretable_without_product_code_without_watch_presence_flag`.
2. Most interpretable pruned model: `pruned_w1_3_early_safer_week1_2_without_product_code_without_watch_presence_flag` under the revised priority order.
3. AUC loss versus full w1_3 exploratory model: 0.067808.
4. Pruning reduces redundancy by removing totals with weekly variables, ratios, deltas, content volume proxies, and default product/watch-presence shortcuts.
5. Pruning preserves useful ranking: recommended top-decile lift 2.587726.
6. Official final presentation candidate: `pruned_w1_3_early_safer_week1_2_without_product_code_without_watch_presence_flag`.
7. Full model results should be treated as exploratory upper bounds.
8. Removed derived/original duplication: total_watch_time, ratios, deltas, coverage complements.
9. Removed target-adjacent features: first/last watch rel day and default watch-presence shortcut.
10. Removed content-volume usage proxies: genre watch_time and genre session_count.
11. Mentor wording is in the final recommendation table and markdown.
