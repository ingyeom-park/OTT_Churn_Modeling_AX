# 09c Corrected Business Simulation — Team Share Summary

## Status
- Based on Stage 08c corrected segments (Stage 06c2 AUC=0.8629)
- Stage 07c TRUE SHAP used as official XAI basis
- All simulation values are assumption-based placeholders — NOT guaranteed outcomes
- No ROI, revenue, or profit claimed (no cost/margin data provided)

## Corrected Segment Baseline (Holdout)
| Segment | n | Churn Rate | Simulation Role |
|---|---|---|---|
| 최상위_이탈위험군 | 463 | 82.5% | primary_target |
| 초기중기_저관여_고위험군 | 434 | 57.6% | primary_target |
| 주차별이용패턴_고위험군 | 1084 | 37.5% | primary_target |
| 장르비율_추천후보군 | 2209 | 11.8% | secondary_recommendation |
| 안정유지_후보군 | 354 | 5.1% | maintenance_only |
| 일반관찰군 | 81 | 33.3% | residual_monitoring |

## Assumption Summary (Placeholder — Editable)
| Segment | reachable | treatment | lift_low | lift_base | lift_high |
|---|---|---|---|---|---|
| 최상위_이탈위험군 | 85% | 85% | 1.0% | 3.0% | 5.0% |
| 초기중기_저관여_고위험군 | 85% | 80% | 1.0% | 3.0% | 5.0% |
| 주차별이용패턴_고위험군 | 80% | 75% | 1.0% | 3.0% | 5.0% |
| 장르비율_추천후보군 | 75% | 55% | 0.5% | 1.5% | 3.0% |
| 안정유지_후보군 | 70% | 30% | 0.0% | 0.5% | 1.0% |
| 일반관찰군 | 60% | 20% | 0.0% | 0.0% | 0.5% |

## Incremental Retained Users by Segment (Assumption-Based)
| Segment | Low | Base | High |
|---|---|---|---|
| 최상위_이탈위험군 | 3.3 | 10.0 | 16.7 |
| 초기중기_저관여_고위험군 | 3.0 | 8.9 | 14.8 |
| 주차별이용패턴_고위험군 | 6.5 | 19.5 | 32.5 |
| 장르비율_추천후보군 | 4.6 | 13.7 | 27.3 |

## Portfolio Scenario Comparison (Base Assumption)
| Portfolio | Segments | Treated Users | Base Retained | Readiness |
|---|---|---|---|---|
| A. 최상위 위험군만 | 1 | 334 | 10.0 | safe_to_report_with_assumption_caveat |
| B. 최상위 + 저관여 고위험군 | 2 | 630 | 18.9 | safest_presentation_scenario |
| C. 전체 고위험군 (3개 세그먼트) | 3 | 1280 | 38.4 | plausible_but_cautioned |
| D. 고위험군 + 장르 추천 (저비용 병행) | 4 | 2191 | 52.1 | assumption_sensitive |
| E. 모니터링 전용 (맥락 참조용) | 2 | 84 | 0.4 | context_only |

## Safest Presentation Wording
- Portfolio B (high_risk_plus_low_engagement) is the **recommended presentation scenario**.
- Use: '예측 이탈 고위험군 {n}명 중, 가정 기반 시뮬레이션 결과 최대 {high}명의 추가 유지가 가능할 수 있습니다.'
- Always add: '본 수치는 가정 기반 시나리오 추정치이며 인과관계 또는 ROI를 의미하지 않습니다.'

## Key Cautions
1. 모든 리텐션 리프트 수치는 가정치 — 실제 A/B 테스트 결과가 아님
2. 인과관계 주장 금지
3. ROI/매출/비용 미주장 (cost/margin 데이터 없음)
4. 장르비율_추천후보군은 이탈률이 낮음 (11.8%) — 공격적 리텐션 타겟으로 부적합
5. 구 Stage 09 수치는 historical/provisional — 공식 증거로 사용 금지

## Recommended Figures for Presentation
- `09c_incremental_retained_users_by_segment.png`
- `09c_portfolio_incremental_retained_users.png`
- `09c_business_simulation_summary_card.png`