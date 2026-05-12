# 08c Corrected Segmentation Strategy Report
## 1. Which corrected model score was used for segmentation?
Stage 06c2 corrected official model: **HistGradientBoostingClassifier** on `pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence`. Reconstructed AUC = 0.862939 (expected 0.862939, diff = 0.0). Score direction: `repurchase_score = P(is_repurchase_label=1)`, `churn_risk_score = 1 − repurchase_score`.
## 2. Why old 08/08b segments are no longer official?
Old Stage 08 and 08b were completed before the Stage 02c strict preprocessing correction. They relied on a pre-correction pipeline with AUC ≈ 0.8047. After the 02c correction, the official pipeline was re-run in Stage 06c2 (AUC = 0.8629). All old 08/08b scores and segment assignments are historical/provisional and must not be used as final evidence.
## 3. What are the corrected risk bands?
Risk band thresholds were computed from holdout churn_risk_score percentiles: p40=0.1162, p70=0.4075, p90=0.6999.

| Risk Band | n | Share | Churn Rate | Lift |
|---|---|---|---|---|
| top_10_highest_risk | 463 | 10.0% | 82.5% | 2.84x |
| risk_10_30 | 928 | 20.1% | 57.1% | 1.96x |
| risk_30_60 | 1384 | 29.9% | 26.0% | 0.89x |
| bottom_40_lowest_risk | 1850 | 40.0% | 4.0% | 0.14x |

## 4. What are the corrected final segments?
Six hierarchical segments (priority-assigned, holdout population):

| Segment | n | Share | Churn Rate | Lift | Stability |
|---|---|---|---|---|---|
| 최상위_이탈위험군 | 463 | 10.0% | 82.5% | 2.84x | stable |
| 초기중기_저관여_고위험군 | 434 | 9.4% | 57.6% | 1.98x | stable |
| 주차별이용패턴_고위험군 | 1084 | 23.4% | 37.5% | 1.29x | stable |
| 장르비율_추천후보군 | 2209 | 47.8% | 11.8% | 0.41x | stable |
| 안정유지_후보군 | 354 | 7.6% | 5.1% | 0.17x | stable |
| 일반관찰군 | 81 | 1.8% | 33.3% | 1.15x | stable |

## 5. Which segments are high-risk targeting groups?
- **최상위_이탈위험군**: churn_risk_score ≥ p90. Primary targeting group.
- **초기중기_저관여_고위험군**: churn_risk_score in [p70, p90) AND low total watch time. Onboarding target.
- **주차별이용패턴_고위험군**: churn_risk_score in [p40, p90) AND declining weekly pattern. Pattern-based target.
## 6. Which segments are maintenance or recommendation groups?
- **장르비율_추천후보군**: max genre ratio > 0.4. Content recommendation group. Not necessarily high-risk.
- **안정유지_후보군**: churn_risk_score < p40. Light-touch maintenance. Do not over-intervene.
- **일반관찰군**: Residual. Baseline monitoring only.
## 7. Which old segments changed or disappeared?
| Old 08b Segment | 08c Equivalent | Status | Reason |
|---|---|---|---|
| 최상위 이탈위험군 | 최상위 이탈위험군 | kept_renamed | Same top 10% risk concept. AUC corrected from ~0.8047 to 0.8629; official scores |
| 초기 저관여 고위험군 | 초기/중기 저관여 고위험군 | kept_refined | Similar concept. Now uses corrected 06c2 scores and explicit total watch time th |
| 상위위험 관찰/추천 후보군 | 주차별 이용패턴 기반 고위험군 | changed | Now uses explicit declining weekly pattern threshold instead of residual risk_10 |
| 3주차 집중 시청 안정/전환 후보군 | 안정 유지 후보군 | merged_simplified | Old 08b used late week3 flag separately. 08c uses churn_risk bottom 40% as simpl |
| 장르 선호 기반 콘텐츠 추천군 | 장르비율 기반 추천 후보군 | kept_refined | Same genre affinity concept. Now uses Stage 07c TRUE SHAP as official XAI basis. |
| 저위험/일반 유지군 | 일반 관찰군 | kept_renamed | Residual group kept. Old 08b used pre-02c/06c2 scores; 08c uses corrected offici |

## 8. Which SHAP feature families support the segment interpretation?
Based on Stage 07c TRUE SHAP (corrected official model, AUC=0.8629):

- **weekly_usage_pattern** (sum mean_abs_shap ≈ 1.507): Top driver.   Supports high-risk and low-engagement segment interpretation.
- **genre_ratio_proxy** (sum ≈ 1.433): Second driver.   Supports genre affinity segment design.
- **membership_context** (sum ≈ 0.510): Third.   is_promotion_bin and max_screen_num are notable.
- **simple_usage_volume** (sum ≈ 0.323): Supporting feature family.
- **release_month_proxy** (sum ≈ 0.039): Minor.

All SHAP is observational association; no causal claim permitted.
## 9. Which segments are safe to report?
- `safe_to_report_with_caution`: 최상위_이탈위험군, 초기중기_저관여_고위험군
- `plausible_but_cautioned`: 주차별이용패턴_고위험군, 장르비율_추천후보군
- `safe_to_report_as_context_only`: 안정유지_후보군, 일반관찰군

All presentations must include the caution: predicted risk ranking only; no causality, no ROI, no intervention lift.
## 10. Which segments should be used in Stage 09c simulation?
- **Recommended for Stage 09c**: 최상위_이탈위험군, 초기중기_저관여_고위험군, 주차별이용패턴_고위험군, 장르비율_추천후보군
- **Not recommended as primary**: 안정유지_후보군 (low risk), 일반관찰군 (residual)
- Stage 09c must supply its own business assumptions (lift, cost, reach). Stage 08c provides segment definitions and score thresholds only.

---
*Stage 08c corrected segmentation only. Do not proceed to Stage 09c from this file.*
