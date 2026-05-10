# 08b v2 Segmentation Refinement Report

Generated at: 2026-05-11T01:20:27

## 1. Why Stage 08 Needed Refinement
Stage 08 created useful risk bands and exploratory rule segments, but several rule segments were too small, too broad, highly overlapping, or named in a way that could mislead presentation. Stage 08b keeps the risk-score bands as the primary targeting frame and converts many rule segments into explanatory modifiers.

## 2. Robust Risk Bands Kept
- top_10_highest_risk: n=478, churn rate=0.785, lift=2.73, captured churners=375.
- risk_10_30: n=956, churn rate=0.591, lift=2.06, captured churners=565.
- risk_30_60: n=1433, churn rate=0.256, lift=0.89, captured churners=367.
- bottom_40_lowest_risk: n=1910, churn rate=0.034, lift=0.12, captured churners=64.

## 3. Stage 08 Keep, Merge, Rename, Drop Decisions
- Kept/refined: top_decile_high_churn_risk, low_or_no_early_engagement, late_heavy_week3_intensive.
- Merged: genre_affinity_thriller_crime, genre_affinity_animation_family, genre_affinity_drama, genre_affinity_action_adventure.
- Renamed/downplayed: late_heavy_week3_intensive, early_routine_stable.
- Dropped from presentation: week2_surge_users, general_other.
- Modifier only: delayed_start, high_price_or_promotion_sensitive.

## 4. Final Presentation-Ready Segment Set
- 최상위 이탈위험군 (`top_decile_high_churn_risk`): n=478, churn rate=0.785, lift=2.73, action=고위험 모니터링, 개인화 리텐션 메시지, 초기 콘텐츠 재추천.
- 초기 저관여 고위험군 (`risk_10_30_low_engagement`): n=478, churn rate=0.567, lift=1.98, action=초기 온보딩, 첫 시청 유도, 개인화 콘텐츠 추천.
- 상위위험 관찰/추천 후보군 (`risk_10_30_other_review`): n=478, churn rate=0.615, lift=2.14, action=위험 점수 기반 모니터링과 장르/이용 패턴별 후속 추천.
- 3주차 집중 시청 안정/전환 후보군 (`late_week3_engaged_retention_candidate`): n=1174, churn rate=0.070, lift=0.24, action=이어보기, 시리즈 연속 추천, 구독 종료 전 유지 메시지.
- 장르 선호 기반 콘텐츠 추천군 (`genre_affinity_content_recommendation_pool`): n=1496, churn rate=0.144, lift=0.50, action=장르별 이어보기, 신작/유사작 추천, 취향 기반 큐레이션.
- 저위험/일반 유지군 (`low_risk_or_general_maintenance`): n=673, churn rate=0.198, lift=0.69, action=과도한 개입보다 기본 추천과 모니터링 유지.

## 5. Targeting Groups Versus Explanatory Modifiers
- Targeting groups: top_decile_high_churn_risk, risk_10_30_low_engagement, risk_10_30_other_review.
- Maintenance/retention group: late_week3_engaged_retention_candidate.
- Modifier/action layer: genre_affinity_content_recommendation_pool, price/promotion context, delayed start, low/no engagement, week3 intensity.
- Residual context: low_risk_or_general_maintenance.

## 6. Stage 09 Simulation Suitability
- 최상위 이탈위험군: Stage09=Y, lever=high-risk targeted retention message, assumptions=reachable audience, treatment cost, response rate, retention lift, contact fatigue.
- 초기 저관여 고위험군: Stage09=Y, lever=onboarding and first-watch activation, assumptions=message reach, recommendation inventory, response rate, retention lift.
- 상위위험 관찰/추천 후보군: Stage09=Y, lever=risk-score guided recommendation or message, assumptions=targeting capacity, treatment cost, expected lift, exclusion rules.
- 3주차 집중 시청 안정/전환 후보군: Stage09=Y, lever=continuation cue and late-period retention reminder, assumptions=eligible content availability, message timing, incremental retention lift.
- 장르 선호 기반 콘텐츠 추천군: Stage09=Y, lever=genre-based content recommendation, assumptions=genre inventory, recommendation exposure, response rate, incremental lift.
- 저위험/일반 유지군: Stage09=N, lever=monitoring only, assumptions=baseline monitoring policy only.

## 7. Claims Must Not Be Made
- Do not claim segment membership causes churn or repurchase.
- Do not claim SHAP proves a retention intervention effect.
- Do not calculate or imply financial impact in Stage 08b.
- Do not use Stage 07 fallback as final XAI evidence.
- Do not call 3주차 집중 시청군 a churn-risk group when observed churn is low.

## 8. Business Assumptions Needed Before Financial Simulation
- Reachable audience size after channel constraints.
- Campaign/contact cost.
- Expected response rate.
- Incremental retention lift under low/base/high scenarios.
- Message fatigue and exclusion rules.
- Content inventory and recommendation feasibility.

## 08b Internal Critique and Final Segment Selection Rationale
- Kept: top_decile_high_churn_risk, low_or_no_early_engagement, late_heavy_week3_intensive.
- Merged: genre_affinity_thriller_crime, genre_affinity_animation_family, genre_affinity_drama, genre_affinity_action_adventure.
- Renamed: late_heavy_week3_intensive, early_routine_stable.
- Dropped: week2_surge_users, general_other.
- Modifier only: delayed_start, high_price_or_promotion_sensitive.
- Ready for presentation: top_decile_high_churn_risk, risk_10_30_low_engagement, risk_10_30_other_review, late_week3_engaged_retention_candidate, genre_affinity_content_recommendation_pool, low_risk_or_general_maintenance.
- Stage 09 candidates: top_decile_high_churn_risk, risk_10_30_low_engagement, risk_10_30_other_review, late_week3_engaged_retention_candidate, genre_affinity_content_recommendation_pool.
- Avoid causal, financial, and unsupported intervention claims until Stage 09 assumptions and experiments are defined.
