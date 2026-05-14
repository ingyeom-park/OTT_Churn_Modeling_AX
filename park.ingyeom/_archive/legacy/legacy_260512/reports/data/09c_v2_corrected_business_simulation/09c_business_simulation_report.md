# 09c Corrected Business Simulation Report

## 1. What is being simulated?
An assumption-based scenario simulation estimating how many users might be retained under different targeting strategies applied to Stage 08c corrected segments. This is NOT causal proof, NOT an A/B test result, and NOT a financial forecast.

## 2. Which corrected segments are included?
All six Stage 08c corrected hierarchical segments are included:
- **Primary targets** (simulation active): 최상위_이탈위험군, 초기중기_저관여_고위험군, 주차별이용패턴_고위험군
- **Secondary recommendation**: 장르비율_추천후보군
- **Excluded from aggressive targeting**: 안정유지_후보군, 일반관찰군

## 3. Which segments are excluded from aggressive targeting?
**안정유지_후보군** (churn_rate=5.1%) and **일반관찰군** (churn_rate=33.3% but residual/unexplained). Both appear only in Portfolio E (monitoring_only) with no intervention impact claimed.

## 4. Which assumptions are used?
All rates (reachable_rate, treatment_rate, response_rate, incremental_retention_lift) are editable placeholder assumptions — NOT real business data.
See `09c_assumption_scenarios.csv` for all values. High-risk groups: lift_base=0.03. Secondary: lift_base=0.015.

## 5. Which values are facts and which are placeholders?
| Metric | Type |
|---|---|
| churn_rate, n, repurchase_rate | **Observed** (Stage 06c2 corrected model, holdout) |
| reachable_rate, treatment_rate, response_rate | **Placeholder assumption** |
| incremental_retention_lift | **Placeholder assumption** |
| incremental_retained_users | **Derived from assumptions** |
| campaign_cost, net_value, ROI | **NOT computed** (no cost/margin provided) |

## 6. Low/Base/High retained-user estimates by segment (Holdout)
| Segment | n | Churn Rate | Low | Base | High |
|---|---|---|---|---|---|
| 최상위_이탈위험군 | 463 | 82.5% | 3.3 | 10.0 | 16.7 |
| 초기중기_저관여_고위험군 | 434 | 57.6% | 3.0 | 8.9 | 14.8 |
| 주차별이용패턴_고위험군 | 1084 | 37.5% | 6.5 | 19.5 | 32.5 |
| 장르비율_추천후보군 | 2209 | 11.8% | 4.6 | 13.7 | 27.3 |

## 7. Which portfolio is safest to present?
**Portfolio B (high_risk_plus_low_engagement)**: 최상위_이탈위험군 + 초기중기_저관여_고위험군. High churn rates confirmed by corrected model; smallest scope; most defensible.

## 8. Which portfolio is too aggressive?
**Portfolio D (recommendation_light)**: 장르비율_추천후보군 has low churn (11.8%) and genre-based lift is the most assumption-sensitive. Do not present as primary targeting.

## 9. What financial claims cannot be made?
Revenue, profit, ROI, net value, and campaign cost cannot be claimed. cost_per_contact and gross_margin_per_retained_user were not provided. All financial fields are NaN in the simulation outputs.

## 10. What needs A/B testing?
All intervention effectiveness assumptions (lift rates) need A/B testing before operational deployment. No lift has been measured in this pipeline.

## 11. How should this feed into final presentation?
Present Portfolio B (base scenario) with explicit low/high range. Label all retained-user estimates as 'assumption-based scenario only.' Do not present financial projections. Recommend A/B test design as next step.

## 12. What must not be claimed?
- Causality: these actions do not proven cause retention
- ROI, revenue, profit (no cost/margin data)
- Intervention guarantee
- Old Stage 09 numbers as current evidence
- SHAP as proof of causal drivers

## 09c Internal Critique and Simulation Reliability Review

### 1. Which assumptions dominate the result?
**`incremental_retention_lift_base`** is the primary driver of the retained-user estimate.
A ±0.01 change in lift directly scales the final number nearly linearly.
This is confirmed by the tornado analysis: `lift_base` shows the largest absolute swing.

`reachable_rate` and `treatment_rate` are secondary drivers — together they determine the
treated user pool which the lift is applied to.

**Implication**: the simulation output is only as reliable as the lift assumption.
Since no real-world lift data exists, results are illustrative scenario estimates only.

### 2. Which scenario is safest to present?
**Portfolio B (high_risk_plus_low_engagement)**: 최상위_이탈위험군 + 초기중기_저관여_고위험군.
- Smallest contact volume among multi-segment portfolios
- Both segments have objectively high churn rates (82.5% and 57.6%)
- Segment definitions are transparent and based on model score + usage threshold
- Easiest to defend without causal claims

### 3. Which scenario is too broad or too aggressive?
**Portfolio D (recommendation_light)**: includes 장르비율_추천후보군 (n=2,209; churn_rate=11.8%).
- This segment has a LOW churn rate — treating it as a retention target is questionable
- The incremental lift assumption for genre recommendation is the most uncertain
- Contact volume is very large; cost efficiency is unknown without real margin data
- Do not present as a primary intervention target

### 4. Which segment has low churn and should not be treated as high-risk?
- **장르비율_추천후보군**: churn_rate = 11.8%. Not a high-risk group. Content recommendation only.
- **안정유지_후보군**: churn_rate = 5.1%. Lowest predicted risk. No aggressive targeting.
- These two should be explicitly labeled as non-targeting groups in presentations.

### 5. Which financial claims cannot be made?
- **Revenue**: not claimable (gross_margin_per_retained_user not provided)
- **Profit**: not claimable (cost_per_contact not provided)
- **ROI**: not claimable (no cost or margin data)
- **Net value**: not claimable
- **Campaign cost**: not claimable
- Only claimable (with caveat): targeted users, treated users, estimated incremental retained users

### 6. Which claims need A/B testing?
- ALL intervention effectiveness claims need A/B testing before any operational decision
- Specifically:
  - Do retention messages reduce churn for 최상위_이탈위험군?
  - Does onboarding activation reduce churn for 초기중기_저관여_고위험군?
  - Does genre recommendation increase tenure for 장르비율_추천후보군?
- The simulation uses placeholder lift rates (0.01–0.05) that are entirely unvalidated

### 7. Which numbers are observed vs assumption-based?
| Type | Examples |
|---|---|
| **Observed (model output)** | churn_rate, repurchase_rate, n, avg_churn_risk_score, segment assignments |
| **Assumption-based** | reachable_rate, treatment_rate, response_rate, incremental_retention_lift, all financial fields |
| **Derived from assumptions** | reachable_users, treated_users, incremental_retained_users, churn_rate_reduction_pp |

### 8. What should be excluded from final presentation?
- Any ROI, revenue, or profit number
- Portfolio D (recommendation_light) as a primary intervention scenario
- Portfolio E (monitoring_only) as an intervention result — context only
- Any claim that these actions will cause retention
- Old Stage 09 numbers as current evidence

### Summary Recommendation
Present **Portfolio B** (high_risk_plus_low_engagement) as the primary scenario.
Show low/base/high range explicitly. Label all as assumptions.
Exclude financial rows entirely until cost and margin data are provided by the business.
