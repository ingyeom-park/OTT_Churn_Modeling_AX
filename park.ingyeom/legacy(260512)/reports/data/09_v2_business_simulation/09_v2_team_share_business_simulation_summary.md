# 09 v2 Team Share Business Simulation Summary

## What This Is
- Stage 09 is an assumption-based scenario simulation.
- It is not causal proof, not an experiment result, and not a financial forecast.
- Official segment basis: Stage 08b final segments.
- Official XAI basis: Stage 07r TRUE SHAP.

## Segment Baseline
- 최상위 이탈위험군: n=478, churn rate=0.785, expected churners=375.0, Stage09=Y.
- 초기 저관여 고위험군: n=478, churn rate=0.567, expected churners=271.0, Stage09=Y.
- 상위위험 관찰/추천 후보군: n=478, churn rate=0.615, expected churners=294.0, Stage09=Y.
- 3주차 집중 시청 안정/전환 후보군: n=1174, churn rate=0.070, expected churners=82.0, Stage09=Y.
- 장르 선호 기반 콘텐츠 추천군: n=1496, churn rate=0.144, expected churners=216.0, Stage09=Y.
- 저위험/일반 유지군: n=673, churn rate=0.198, expected churners=133.0, Stage09=N.

## Assumed Low/Base/High Lift
- High-risk groups: low 1pp, base 3pp, high 5pp incremental retention lift.
- Maintenance/recommendation groups: lower placeholder lift where applicable.
- All lift, reach, response, cost, and margin values are assumptions, not facts.

## Base Scenario Incremental Retained Users
- 최상위 이탈위험군: 10.4 retained users.
- 초기 저관여 고위험군: 9.8 retained users.
- 장르 선호 기반 콘텐츠 추천군: 8.4 retained users.
- 상위위험 관찰/추천 후보군: 8.0 retained users.
- 3주차 집중 시청 안정/전환 후보군: 6.6 retained users.

## Portfolio Comparison
- high_risk_only: targeted=478, treated=345.4, retained=10.4, financial=assumption_required_no_profit_claim.
- high_risk_plus_low_engagement: targeted=956, treated=670.4, retained=20.1, financial=assumption_required_no_profit_claim.
- broad_risk: targeted=1434, treated=938.1, retained=28.1, financial=assumption_required_no_profit_claim.
- maintenance_light: targeted=4104, treated=1939.3, retained=43.2, financial=assumption_required_no_profit_claim.

## Safe Presentation Wording
- Under explicit placeholder assumptions, the scenario estimates possible retained-user impact by segment.
- The safest presentation scope is high-risk-only or high-risk-plus-low-engagement.
- Cost, margin, profit, and ROI require real business inputs before any claim.

## Recommended Figures
- 09_v2_incremental_retained_users_by_segment.png
- 09_v2_portfolio_incremental_retained_users.png
- 09_v2_assumption_sensitivity_tornado.png
- 09_v2_business_simulation_summary_card.png
