# 09 v2 Business Simulation and Retention Strategy Report

Generated at: 2026-05-11T01:39:04

## 1. What Is Being Simulated
This stage simulates retained-user impact under explicit low/base/high intervention assumptions for Stage 08b final segments. It is not causal proof and not an experiment result.

## 2. Included Segments
- 최상위 이탈위험군 (`top_decile_high_churn_risk`): Stage09=Y.
- 초기 저관여 고위험군 (`risk_10_30_low_engagement`): Stage09=Y.
- 상위위험 관찰/추천 후보군 (`risk_10_30_other_review`): Stage09=Y.
- 3주차 집중 시청 안정/전환 후보군 (`late_week3_engaged_retention_candidate`): Stage09=Y.
- 장르 선호 기반 콘텐츠 추천군 (`genre_affinity_content_recommendation_pool`): Stage09=Y.
- 저위험/일반 유지군 (`low_risk_or_general_maintenance`): Stage09=N.

## 3. Assumptions Used
- reachable_rate, treatment_rate, response_rate, incremental_retention_lift_low/base/high, contact_fatigue_penalty_rate, and max_contact_capacity are editable assumptions.
- cost_per_contact and gross_margin_per_retained_user are intentionally blank because no real business values were provided.

## 4. Facts Versus Placeholders
- Facts from current artifacts: Stage 08b segment membership, holdout n, observed holdout churn rate, observed holdout repurchase rate, and Stage 07r TRUE SHAP evidence.
- Placeholders: all lift, reach, treatment, response, cost, margin, and fatigue values.

## 5. Incremental Retained Users Under Low/Base/High
- 최상위 이탈위험군: low=3.5, base=10.4, high=17.3.
- 초기 저관여 고위험군: low=3.3, base=9.8, high=16.3.
- 상위위험 관찰/추천 후보군: low=2.7, base=8.0, high=13.4.
- 3주차 집중 시청 안정/전환 후보군: low=2.2, base=6.6, high=11.0.
- 장르 선호 기반 콘텐츠 추천군: low=2.8, base=8.4, high=14.0.

## 6. Most Presentation-Safe Portfolio
The most presentation-safe portfolio is `high_risk_plus_low_engagement` because it stays focused on high-risk customers while adding a clear low-engagement action group. `high_risk_only` is the most conservative option; `maintenance_light` is broader and more assumption-sensitive.

## 7. What Cannot Be Claimed Without Cost/Margin Data
- Campaign cost cannot be claimed.
- Gross retention value cannot be claimed.
- Net value and ROI cannot be claimed.
- Profitability cannot be claimed.

## 8. What Needs A/B Testing
- Whether each message or recommendation causes incremental retention.
- Whether response rates are realistic.
- Whether contact fatigue offsets the benefit.
- Whether genre recommendation or onboarding actions work differently by segment.

## 9. Feed Into Final Presentation
- Use retained-user impact ranges, not profit, unless real cost and margin are supplied.
- Present Stage 09 as scenario planning based on model segments and assumptions.
- Pair every simulated result with the assumption row that generated it.

## 10. Exclude From Final Claims
- Causal claims.
- Guaranteed retention lift.
- Financial ROI.
- Any claim based on Stage 07 fallback as final evidence.

## 09 Internal Critique and Simulation Reliability Review
- Dominant assumptions: incremental retention lift, treatment rate, reachable rate, and real cost/margin if financial claims are desired.
- Most sensitive segments: high-volume or high-risk segments where the high-low retained-user range is largest.
- Safest scenario to present: `high_risk_plus_low_engagement`; most conservative scenario is `high_risk_only`.
- Too aggressive scenario: `maintenance_light` because it combines high-risk targeting with maintenance/recommendation groups and larger contact volume.
- Financial claims cannot be made until cost_per_contact and gross_margin_per_retained_user are supplied.
- Intervention claims require A/B testing before being treated as effects.
- Descriptive model outputs: segment n, observed churn rate, expected churners. Assumed business effects: reach, response, lift, cost, margin, retained-user increments.
