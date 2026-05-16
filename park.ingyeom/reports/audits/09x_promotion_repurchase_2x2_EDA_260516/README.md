# 09x promotion x repurchase 2x2 EDA

## Purpose
09x performs descriptive EDA after 08x by crossing promotion status and repurchase status into four cohorts. It checks row counts, feature distributions, AARRR stages, and feature-family patterns for conservative and expanded datasets.

## What This Step Does
- Builds 2x2 analysis cohorts from is_promotion and is_repurchase.
- Profiles numeric and binary features by 2x2 cohort.
- Compares repurchase vs nonrepurchase within promotion and nonpromotion groups.
- Compares promotion vs nonpromotion after fixing repurchase status.
- Reviews context, profile, and payment proxy risk candidates.
- Reviews usage, retention, and onboarding observed differences.
- Creates 10x and 11x handoff files.

## What This Step Does Not Do
- No modeling.
- No train/test split.
- No prediction or probability generation.
- No SHAP.
- No Optuna.
- No segmentation.
- No final business recommendation.
- No causal claim.
- No feature importance claim.
- No feature selection decision.

## Inputs
- 06x conservative and expanded datasets plus feature-list and policy files.
- 07x feature mapping and AARRR mapping files.
- 08x promotion vs nonpromotion EDA files.
- Raw source CSVs under park.ingyeom/data for fingerprint verification only.

## Inherited Basis From 06x, 07x, 08x
06x provided conservative and expanded datasets. 07x provided AARRR stage and feature-family mapping. 08x provided promotion vs nonpromotion EDA and the target-rate summary used for consistency checking.

## 2x2 Cohort Definition
- promotion_repurchase: is_promotion=1 and is_repurchase=1
- promotion_nonrepurchase: is_promotion=1 and is_repurchase=0
- nonpromotion_repurchase: is_promotion=0 and is_repurchase=1
- nonpromotion_nonrepurchase: is_promotion=0 and is_repurchase=0

The 2x2 cohort label is role=analysis_group_label and use_as_feature=False.

## Conservative And Expanded Dataset Separation
Conservative data did not contain is_promotion, so 09x verified row alignment by USER_KEY and is_repurchase, then used expanded is_promotion only as the split key for conservative EDA. Expanded EDA used its own is_promotion field.

## Cohort Size Summary
```text
cohort_2x2_label      nonpromotion_nonrepurchase  nonpromotion_repurchase  promotion_nonrepurchase  promotion_repurchase
feature_set_name                                                                                                        
conservative_safe_22                        2655                     8520                     3867                  8037
expanded_feature_set                        2655                     8520                     3867                  8037
```

## Within Promotion Summary
Top observed difference review candidates: watch_time_min_w3, watch_time_min_w3, watch_session_w3, watch_session_w3, recency

## Within Nonpromotion Summary
Top observed difference review candidates: watch_session_w3, watch_session_w3, watch_time_min_w3, watch_time_min_w3, recency

## Promotion Status Fixed By Repurchase Summary
Top observed difference review candidates: is_user_verified, is_user_verified, age_group, age_group, payment_is_ios

## Context Profile Payment Proxy Risk Summary
Proxy or near-constant risk candidates for 10x or 11x audit: is_user_verified, payment_is_ios, payment_is_mobile, is_female, is_male, payment_is_pc

## Usage Retention Observed Pattern Summary
Usage, retention, or onboarding candidates for 10x distribution review: watch_session_w3, watch_time_min_w3, recency, total_watch_time_min, max_watch_time_min, watch_days, active_ratio, max_daily_watch_time_min, avg_gap_w3_watch_days, max_inactive_gap_days

## Interpretation Caveats
All results are observed 2x2 cohort differences only. They are not causal estimates, marketing effectiveness evidence, feature importance, feature selection, or final business recommendations.

## Handoff
10x should recheck feature distributions, missingness, outliers, near-constant fields, and top 09x observed differences. 10x or 11x should perform VIF, pairwise correlation, feature-family redundancy cluster, duplicate-like, target leakage suspect, and group-proxy audits. 11x modeling preflight must re-check conservative vs expanded feature usage before any model fit.

## Next Step
Next step is 10x feature distribution EDA or 10x feature/redundancy EDA.
