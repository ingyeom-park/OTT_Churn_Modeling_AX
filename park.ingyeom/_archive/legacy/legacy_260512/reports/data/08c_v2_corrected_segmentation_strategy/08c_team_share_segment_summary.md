# 08c Corrected Segmentation Strategy — Team Share Summary

## Model Basis
- Official model: HistGradientBoostingClassifier (Stage 06c2 corrected)
- Feature set: `pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence`
- Reconstructed AUC: 0.862939 (expected: 0.862939)
- Score direction: churn_risk_score = 1 − repurchase_score (high → high predicted churn risk)

## Why Old 08/08b Segments Are No Longer Official
- Old Stage 08 and 08b were created before Stage 02c strict preprocessing correction.
- Old segments used a pre-correction model (AUC ~0.8047), which had data hygiene issues.
- Stage 06c2 corrected the official model to AUC=0.8629 on the clean pipeline.
- All old 08/08b segment numbers are historical/provisional only.

## Risk Bands (Holdout)
| Risk Band | n | Share | Churn Rate | Lift |
|---|---|---|---|---|
| top_10_highest_risk | 463 | 10.0% | 82.5% | 2.84x |
| risk_10_30 | 928 | 20.1% | 57.1% | 1.96x |
| risk_30_60 | 1384 | 29.9% | 26.0% | 0.89x |
| bottom_40_lowest_risk | 1850 | 40.0% | 4.0% | 0.14x |

## Corrected Final Segments (Holdout)
| Segment | n | Share | Churn Rate | Lift |
|---|---|---|---|---|
| 최상위_이탈위험군 | 463 | 10.0% | 82.5% | 2.84x |
| 초기중기_저관여_고위험군 | 434 | 9.4% | 57.6% | 1.98x |
| 주차별이용패턴_고위험군 | 1084 | 23.4% | 37.5% | 1.29x |
| 장르비율_추천후보군 | 2209 | 47.8% | 11.8% | 0.41x |
| 안정유지_후보군 | 354 | 7.6% | 5.1% | 0.17x |
| 일반관찰군 | 81 | 1.8% | 33.3% | 1.15x |

## High-Risk Targeting Groups
- **최상위_이탈위험군**: Top 10% by predicted churn risk. Primary targeting group.
- **초기중기_저관여_고위험군**: High risk + low usage. Onboarding activation candidate.
- **주차별이용패턴_고위험군**: Declining weekly watch pattern within mid-high risk band.

## Maintenance / Recommendation Groups
- **장르비율_추천후보군**: Genre affinity signal. Content curation candidate.
- **안정유지_후보군**: Low predicted churn risk. Light-touch maintenance.
- **일반관찰군**: Residual. Baseline monitoring only.

## SHAP Feature Family Support
- weekly_usage_pattern: top family (sum mean_abs_shap ≈ 1.507)
- genre_ratio_proxy: second family (sum mean_abs_shap ≈ 1.433)
- membership_context: third family
- All SHAP is Stage 07c TRUE SHAP on corrected official model.
- SHAP is observational association only; no causality claim.

## Safe to Report
- 최상위_이탈위험군, 초기중기_저관여_고위험군: safe_to_report_with_caution
- 주차별이용패턴_고위험군, 장르비율_추천후보군: plausible_but_cautioned
- 안정유지_후보군, 일반관찰군: safe_to_report_as_context_only

## Use in Stage 09c Simulation
- Recommended for Stage 09c: 최상위_이탈위험군, 초기중기_저관여_고위험군, 주차별이용패턴_고위험군, 장르비율_추천후보군
- Not recommended as primary simulation targets: 안정유지_후보군, 일반관찰군

## Do Not Claim
- Do not claim causality, ROI, intervention lift, or retention rate from segmentation.
- Do not use old 07r or 06h SHAP as final evidence.
- Do not use old 08/08b segment numbers as official.