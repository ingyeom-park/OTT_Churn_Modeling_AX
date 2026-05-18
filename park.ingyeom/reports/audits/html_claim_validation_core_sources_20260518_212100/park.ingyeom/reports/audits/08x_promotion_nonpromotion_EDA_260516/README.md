# 08x promotion vs non-promotion EDA

## Purpose
08x performs descriptive promotion vs non-promotion EDA using 06x conservative and expanded datasets, with 07x feature mapping, AARRR mapping, and downstream EDA handoff as the interpretation frame.

## What This Step Does
- Compares observed promotion and non-promotion distributions.
- Keeps conservative_safe_22 and expanded_feature_set separate.
- Summarizes observed differences by feature family and AARRR stage.
- Creates 09x, 10x, and 11x handoff files.
- Verifies raw source CSV immutability with sha256, mtime, and size.

## What This Step Does Not Do
- No modeling, train/test split, prediction, SHAP, Optuna, segmentation, final segment, or final business recommendation.
- No new derived variables are persisted.
- No feature removal or final feature-use decision is made.
- No causal, uplift, or marketing effectiveness claim is made.

## Inputs
- 06x dataset generation: `C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\06x_dataset_generation_260515`
- 07x feature mapping and AARRR handoff: `C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\07x_feature_mapping_AARRR_260515`
- Raw source fingerprint target folder: `C:\Code\ott-churn-prediction\park.ingyeom\data`

## 06x/07x Carryover
- 06x final checks pass: True
- 07x final checks pass: True
- Conservative split caveat: conservative does not store `is_promotion`; 08x uses row-aligned expanded `is_promotion` only after row-level `USER_KEY` and `is_repurchase` validation.

## Target Distribution Summary
```
    feature_set_name   group_name  row_count  repurchase_rate
conservative_safe_22    promotion      11904         0.675151
conservative_safe_22 nonpromotion      11175         0.762416
expanded_feature_set    promotion      11904         0.675151
expanded_feature_set nonpromotion      11175         0.762416
```

## Top Observed Differences For Review
```
    feature_set_name  rank safe_model_feature_name  effect_size_or_abs_smd
conservative_safe_22     1   avg_gap_w3_watch_days                0.026469
conservative_safe_22     2              is_only_w2                0.022760
conservative_safe_22     3              is_only_w3                0.019910
conservative_safe_22     4   avg_gap_w2_watch_days                0.019552
conservative_safe_22     5              is_only_w1                0.015995
conservative_safe_22     6  is_cold_start_7d_fixed                0.012994
conservative_safe_22     7        watch_session_w3                0.010976
conservative_safe_22     8  is_cold_start_3d_fixed                0.008022
```

## Interpretation Caveat
All findings are observed group differences only. Do not write that promotion caused churn, prevented churn, increased repurchase, or reduced repurchase.

## Handoff
- 09x: promotion x repurchase 2x2 descriptive EDA.
- 10x: feature distribution EDA by family and AARRR stage.
- 10x or 11x: VIF, pairwise correlation, redundancy cluster, near-constant, duplicate-like, and target leakage suspect audits.
- 11x: modeling preflight must re-check conservative vs expanded feature usage before any model fit.

Next step: 09x promotion x repurchase 2x2 EDA.
