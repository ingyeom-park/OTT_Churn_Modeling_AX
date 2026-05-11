# 06e v2 Exact Early-Window Rebuild and Timing-Sensitivity Audit

## Scope
- This stage rebuilt exact early-window usage/content features from Stage 02 membership/user/movie policy outputs and raw view logs.
- No Optuna, SHAP, segmentation, business simulation, or production model tuning was performed.
- New outputs were written only under `06e_v2_exact_early_window_rebuild` report folders.

## Source File Note
- Requested raw view path was checked by alias; actual raw view source used: `_data/01_raw/Views_train.csv`.
- Requested raw movie path was checked by alias; actual raw movie source used: `_data/01_raw/Movies.csv`.
- Movie metadata used for modeling came from policy-checked and deduplicated `park.ingyeom/reports/data/02_v2_preprocessing_policy/moviemaster_v2_policy_checked.csv`.

## Exact AUC Answers
1. Exact `w1_1` AUC: 0.626133.
2. Exact `w1_2` AUC: 0.740175.
3. Exact `w1_3` AUC: 0.871092.
4. Exact `w1_4` AUC: 0.902250.
5. AUC increase from `w1_1` to `w1_4`: 0.276117; from `w1_2` to `w1_3`: 0.130917.

## Timing Interpretation
- `w1_1` is the cleanest early-window audit because it uses only rel_day 0 through 6.
- `w1_2` remains mentor-safe for a conservative response because it uses rel_day 0 through 13 and is exact, not proxy-derived.
- `w1_3` is the current conservative candidate but should be described as timing-sensitive because it includes behavior through rel_day 20.
- `w1_4` is late-period/end-of-period only and must not be presented as early-warning performance.
- After Stage 06c, the high AUC remains classified as `target_adjacent_but_not_direct_leakage`.

## Stage 06c Proxy vs Exact w1_2
- Stage 06c proxy `w1_2` AUC: 0.6505859355759969.
- Stage 06e exact `w1_2` AUC: 0.740175.
- If the exact value is higher than the proxy, the proxy under-estimated because it reconstructed an early window indirectly from saved `w1_3` columns instead of rebuilding event-level features.
- If the exact value is similar, early-window signal is genuinely limited.

## Mentor-Safe Recommendation
- Safest mentor-facing number: exact `w1_2` AUC 0.740175.
- Suitable presentation number with caveats: exact `w1_3` AUC 0.871092.
- Do not present the `w1_4` AUC as early-warning performance because it uses observation through rel_day 27.
- Do not claim causality or operational readiness from high AUC alone.

## Required Output Tables
- `park.ingyeom/reports/tables/06e_v2_exact_early_window_rebuild/06e_exact_window_model_metrics.csv`
- `park.ingyeom/reports/tables/06e_v2_exact_early_window_rebuild/06e_auc_by_window.csv`
- `park.ingyeom/reports/tables/06e_v2_exact_early_window_rebuild/06e_mentor_safe_metric_ladder.csv`
