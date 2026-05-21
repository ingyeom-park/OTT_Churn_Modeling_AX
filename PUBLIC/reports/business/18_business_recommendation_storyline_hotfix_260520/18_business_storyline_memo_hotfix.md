# 18 Business Recommendation Storyline — Polish Hotfix
## 작성일: 2026-05-20 | 버전: hotfix
## 작성 목적: 기존 18 산출물의 품질 문제를 발견하고 발표 가능한 수준으로 정제

---

## 1. 이번 hotfix의 목적과 배경

이번 hotfix는 기존 18 business recommendation storyline 산출물이 형식적으로 생성되었지만, 실제 발표와 비즈니스 의사결정에 활용하기에는 여러 가지 미흡한 점이 있어 이를 보완하기 위해 수행되었다.

기존 18 산출물에서 발견된 주요 문제는 다음과 같다.

첫째, `18_demographic_action_candidate_selection.csv`에 60개 행이 모두 `include_in_storyline=yes`로 표시되어 있었다. 이는 너무 낙관적인 설정이다. 실제 발표에서 60개의 demographic action candidate를 모두 storyline에 포함시키면 청중은 어떤 것이 진짜 중요한 신호인지 파악하기 어렵다. 더 심각한 문제는 같은 age_group이 동일한 segment 내에서 서로 다른 feature에 대해 반복 등장한다는 것이다. 예를 들어 `promo1, high_risk_activation_or_low_engagement, age_group=30`이 `total_watch_time_min`, `watch_time_min_w2`, `watch_time_min_w3` 각각에 대해 별도 행으로 3번 등장한다. 이는 중복이며 단일 통합 행으로 정리해야 한다.

둘째, `18_segment_business_action_matrix.csv`에서 promo0 행들이 `segment_role=promo0_comparison_scope`로 표시되어 있음에도 불구하고 `final_status=provisional_business_candidate`로 되어 있다. promo0는 비교 reference 역할만 해야 하며, promo1과 동일한 `provisional_business_candidate` 지위를 가져서는 안 된다. 이 문제는 promo0에 대한 action을 암묵적으로 제안하는 것처럼 보일 수 있어 수정이 필요하다.

셋째, `18_promo1_vs_promo0_storyline_comparison.csv`에 `genre_or_content_action_cue`가 포함되어 있다. 이 시그널은 promo1에서 n=11, promo0에서 n=5에 불과하다. n이 이렇게 작은 시그널을 main storyline 비교 지표로 올리면 청중이 오해할 수 있다. 최소 n=300 이상의 representative segment만 main comparison에 포함시켜야 한다.

넷째, 기존 storyline comparison에서 `mid_risk_retention_watchlist`가 누락되어 있다. mid_risk는 promo1 n=1,309로 충분한 규모이며, promo0 대비 delta가 +18.4%p로 5개 segment 중 가장 큰 차이를 보인다. 이는 100원딜 고객군에서 중위험 모니터링의 중요성을 설명하는 핵심 비교 포인트이므로 반드시 storyline comparison에 포함되어야 한다.

다섯째, `18_segment_visual_guide_v2.html`이 요약 수준의 가이드에 불과하다. 발표용 HTML이 갖춰야 할 flag dictionary, segment별 KPI card, promo0 비교 값, safe/unsafe wording 안내, demographic action layer 설명, 100원딜 내러티브 깊이가 모두 부족했다.

이번 hotfix는 이러한 문제들을 수정하고 발표 수준의 산출물로 정제하는 것을 목표로 한다. 단, 어떠한 모델도 재실행하지 않으며, OOF score, SHAP, segment assignment도 변경하지 않는다. 오직 기존 결과를 올바르게 정리하고 표현하는 작업만 수행한다.

---

## 2. 100원딜 프로모션의 특수성과 분석 프레임

### 2.1 100원딜이란 무엇인가

100원딜은 OTT 서비스가 신규 가입자를 유치하기 위해 정가 7,900원 대신 100원이라는 극단적으로 낮은 가격을 제공하는 초저가 체험 프로모션이다. 정가 대비 약 1.3%에 불과한 가격이므로, 가입 결정의 비용-편익 계산이 정가 가입자와 근본적으로 다를 수 있다.

정가로 가입하는 고객은 서비스에 대한 어느 정도의 사전 관심, 이용 의도, 혹은 지불 의향을 가진 상태에서 가입 결정을 내릴 가능성이 높다. 반면 100원딜 고객은 "100원이니까 한번 써보지"라는 낮은 진입 장벽 때문에 원래라면 가입하지 않았을 고객을 포함할 수 있다. 이는 100원딜 고객의 이용 행동, 참여도, 재구매 의향이 정가 고객과 체계적으로 다를 수 있음을 의미한다.

따라서 이 분석은 전체 OTT 이탈 분석이 아니다. 분석의 핵심 질문은 "100원딜이라는 초저가 프로모션으로 유입된 고객 중 누가 정가 전환에 성공하고, 누가 실패하는가"이다. 정가 전환 실패는 곧 이탈(재구매 미발생)로 이어진다.

100원딜 고객을 따로 분리해서 분석하는 이유는 명확하다. 만약 전체 고객을 하나의 모델에 넣고 `is_promotion`을 단순 feature로 처리하면, 100원딜 고객 내부에서 누가 정가 전환에 실패하는지를 특정하는 데 한계가 생긴다. 따라서 이 분석에서는 promo1 (100원딜)과 promo0 (정가)를 각각 독립된 scope으로 분리하여 별도의 모델을 실행하고, 그 결과를 비교 분석했다.

### 2.2 분석의 핵심 질문

이 프로젝트의 핵심 질문은 다음과 같이 정확하게 표현해야 한다.

"100원딜로 유입된 고객 중 누가 정가 전환에 실패하는가?"

이것은 "전체 OTT 고객 중 누가 이탈하는가"와 다르다. 전자는 100원딜이라는 특수한 유입 맥락을 중심에 두고, 그 안에서 이탈/전환의 패턴을 찾는 작업이다. 후자는 전체 고객을 대상으로 하는 일반적인 이탈 분석이다.

이 구분이 중요한 이유는 같은 행동 패턴(예: 3주차 시청 감소)이 100원딜 고객에게서 관찰될 때와 정가 고객에게서 관찰될 때의 비즈니스 해석이 다를 수 있기 때문이다. 100원딜 고객의 3주차 시청 감소는 "저가 체험으로 유입된 후 이용 습관이 형성되지 않아 정가 전환을 포기하는 신호"로 해석될 수 있다. 반면 정가 고객의 3주차 시청 감소는 "이미 정상 가격으로 가입한 고객이 콘텐츠 만족도 저하 또는 다른 이유로 이탈을 고려하는 신호"로 해석될 수 있다.

이 차이를 인식하면서 분석을 진행해야 한다. 비교 분석은 "100원딜 고객과 정가 고객에서 같은 행동 패턴이 나타날 때, 100원딜 고객에서 더 높은 이탈률과 위험 점수가 관찰되는가"를 확인하는 용도로 사용한다.

### 2.3 3주차 행동 신호와 개입 타이밍

3주차 시청 감소 또는 비활성이 분석의 핵심 행동 신호로 부각된 이유를 이해하려면, 100원딜의 계약 구조를 생각해야 한다. 100원딜은 보통 1개월 체험 기간을 제공하며, day21 전후에 정가 전환 또는 이탈 결정이 이루어진다고 가정할 수 있다. 따라서 3주차(day15~21)는 고객이 서비스를 계속 이용할지 결정하는 중요한 시점이다.

3주차에 시청량이 급감하거나 비활성 상태가 되는 고객은, day21 정가 전환 결정 시점에서 "계속 쓸 이유가 없다"고 판단할 가능성이 높다. 이것이 3주차 행동 신호가 정가 전환 실패를 구분하는 강한 관찰 신호가 되는 이유이다.

단, 이것은 인과 원인이 아니라 관찰 신호임을 반드시 명시해야 한다. "3주차에 시청이 감소했기 때문에 이탈했다"는 표현은 인과 해석이며 이 분석의 범위를 벗어난다. 올바른 표현은 "3주차 시청 감소는 정가 전환 실패를 구분하는 강한 관찰 신호로 나타났다"이다.

개입 타이밍의 관점에서 보면, day18~day20은 3주차 초반으로 시청 감소 조짐이 나타나기 시작하는 구간이다. 이 구간에서 시청 감소 조짐을 감지하고 콘텐츠 추천, 혜택 안내, 재활성화 메시지 등을 검토하는 것이 이탈 방어 후보 타이밍으로 해석될 수 있다. 다만 이 타이밍도 business hypothesis이며, 실제 집행 효과는 A/B test 또는 holdout 검증으로 별도 확인해야 한다.

---

## 3. Revised 5-Family Segment 설명

### 3.1 high_risk_week3_inactivity_or_retention_decay

이 segment family는 100원딜 분석의 핵심 세그먼트이다. promo1에서 n=1,893 (전체의 15.9%)이고, 실제 churn rate는 74.3%, GB OOF risk는 0.740이다.

이 family가 필요한 이유는 3주차 시청 감소 또는 비활성이 정가 전환 실패를 가장 강하게 구분하는 행동 패턴이기 때문이다. log_retention_w3_ratio, watch_time_min_w3, week3_inactive_flag 등이 이 세그먼트의 핵심 기준 feature들이다. 3주차에 시청이 급감하거나 거의 이용하지 않는 고객들은 day21 정가 전환 결정 시점에서 이탈할 가능성이 매우 높다.

promo0와의 비교에서는 같은 패턴이 promo0 (n=1,890, churn=68.0%)에서도 관찰된다. delta는 +6.2%p로, 100원딜 고객에서 이 패턴의 위험이 더 두드러진다. 이것은 "100원딜 고객군에서 3주차 비활성 패턴이 더 강하게 위험과 연결되어 있음"을 시사하는 비교 신호이다.

비즈니스 액션 후보로는 week3_save_campaign을 제안할 수 있다. day18~day20 구간에서 시청 감소 조짐을 감지하고, in-app push 또는 renewal-reminder message를 검토한다. 단, 콘텐츠 추천을 포함할 경우에는 해당 고객의 최근 시청 맥락과 장르 cue가 있을 때만 한정적으로 적용해야 한다. 장르 cue 없이 대규모 콘텐츠 카탈로그를 무작위로 추천하는 것은 적절하지 않다.

Caveat: 이 모든 것은 provisional candidate이다. OOF score는 campaign threshold가 아니며, SHAP은 인과 원인이 아니다. demographic 정보(female n=1,163; male n=730)는 personalization layer이며 이탈 원인이 아니다.

### 3.2 high_risk_activation_or_low_engagement

이 segment family는 100원딜 고객 중 초기 이용 습관 형성에 실패한 고객군이다. promo1에서 n=370 (전체의 3.1%)이고, 실제 churn rate는 78.4%로 5개 segment 중 가장 높다. GB OOF risk는 0.732이다.

이 family가 필요한 이유는 1주차부터 시청량이 매우 낮거나 거의 이용하지 않는 고객들이 distinct한 행동 패턴을 보이기 때문이다. 이들은 3주차까지 기다릴 필요 없이 1~2주차 초반부터 이미 이탈 위험 신호를 보인다. low_activation_flag, 1주차 시청량 매우 낮음이 핵심 기준이다.

promo0와의 비교에서 주목할 점이 있다. promo0에서 이 family는 n=273으로 subsignal_only로 분류된다. 즉, promo0에서는 이 family가 충분한 규모의 대표 segment를 형성하지 못한다. promo1에서는 representative_candidate이지만 promo0에서는 subsignal_only인 이 역할 차이를 발표에서 명시해야 한다.

비즈니스 액션 후보로는 activation_reengagement를 제안한다. 1주차 activation 여부를 조기에 확인하고, 2주차 초반까지 onboarding 메시지 또는 재활성화 push를 검토한다. 단, 대규모 콘텐츠 카탈로그 추천은 부적합하다. 이미 이용 장벽이 높은 고객에게 수천 개의 콘텐츠를 나열하면 오히려 혼란을 줄 수 있으므로, 진입 장벽을 낮추는 short-list 형태의 추천이 적절하다.

Caveat: n=370으로 규모가 작다. 독립 segment로 단독 강조할 경우 과해석 위험이 있다. promo0 subsignal_only 사실을 반드시 함께 명시해야 한다. male n=147 churn=82.3%는 주목할 만한 하위 신호이지만, n이 작고 행동 차이(diff)가 미미해 personalization layer로만 활용한다.

### 3.3 mid_risk_retention_watchlist

이 segment family는 고위험 확정은 아니지만 2~3주차 행동 변화에 따라 이탈 위험이 상승할 수 있는 관찰군이다. promo1에서 n=1,309 (전체의 11.0%)이고, 실제 churn rate는 60.1%, GB OOF risk는 0.528이다.

이 family가 5개 segment 중 특히 주목받아야 하는 이유가 있다. promo0 대비 delta가 +18.4%p로 5개 segment 중 가장 크다. promo0에서 mid_risk의 churn이 41.7%인 반면, promo1에서는 60.1%이다. 이는 "일반 가입자에서도 중위험은 존재하지만, 100원딜 고객군에서는 그 위험이 훨씬 더 높다"는 강한 비교 신호이다.

비즈니스 액션으로는 과도한 save campaign보다 light-touch nurture를 권장한다. 이 군은 "고위험 확정"이 아니라 "관찰군"이다. 따라서 강한 개입보다 2~3주차 행동 변화를 모니터링하면서 상황에 따라 가볍게 접근하는 것이 적절하다. 과도한 intervention은 오히려 역효과를 낳을 수 있다.

기존 storyline comparison에서 이 family가 누락되어 있었다는 점은 심각한 oversight였다. delta가 가장 큰 segment가 비교 지표에서 빠져 있었으니, hotfix에서 반드시 추가되어야 한다.

Caveat: 중위험군이라는 용어 자체가 "어느 정도 이탈할 것"처럼 들릴 수 있으므로 주의가 필요하다. "중위험군은 확정 이탈이 아니라 2~3주차 행동 모니터링 후보다"라고 명확히 해야 한다.

### 3.4 stable_usage_lower_risk

이 segment family는 상대적으로 안정적인 이용 패턴을 보이는 낮은 위험군이다. promo1에서 n=1,999 (전체의 16.8%)이고, 실제 churn rate는 12.0%, GB OOF risk는 0.134이다.

이 family에서 주의해야 할 점이 있다. stable이라는 이름 때문에 "이 군은 이탈 위험이 없다"고 오해하기 쉽지만, promo0에서 stable 군의 churn이 6.8%인 반면 promo1에서는 12.0%이다. 이 차이(+5.2%p)는 "promo1 stable 군도 일반 가입자 stable 군보다 이탈률이 높다"는 사실을 보여준다. 즉, 100원딜 맥락에서는 "stable"이 promo0에서의 "stable"과 완전히 같은 의미가 아닐 수 있다.

비즈니스 액션으로는 방어 캠페인보다 만족 유지와 업셀 후보 관리를 권장한다. 이 군에 대한 강한 이탈 방어 캠페인은 불필요한 비용을 유발하며, 오히려 이미 만족하고 있는 고객에게 불필요한 알림을 보내 역효과를 낳을 수 있다. 개입 최소화가 원칙이며, 필요한 경우 선호 장르 기반의 콘텐츠 유지/확장 추천을 low-frequency CRM으로 제공한다.

Caveat: 안정 군에도 이탈 위험이 0이 아님을 명시한다. stable 군의 행동 패턴을 세심하게 모니터링하고, 급격한 변화가 감지되면 즉시 대응 체계를 갖추어야 한다.

### 3.5 other_needs_review_residual

이 segment family는 현재 rule로 충분히 설명되지 않은 잔여군이다. promo1에서 n=6,333으로 전체의 53.2%를 차지하며, 5개 segment 중 가장 큰 군이다. 실제 churn rate는 18.1%, GB OOF risk는 0.194이다.

이 family를 이해하는 데 가장 중요한 것은 "other를 중위험군으로 단정하지 않는 것"이다. other_needs_review_residual의 churn이 18.1%라고 해서 이것이 "중간 수준의 이탈 위험을 가진 균질한 집단"을 의미하지 않는다. 이 군 내부에는 실제 위험 고객, 안전 고객, 현재 rule로 설명하기 어려운 다양한 패턴이 혼재한다.

이 family가 이렇게 크게 남아 있는 이유는 현재 segmentation rule의 한계 때문이다. 이것은 솔직하게 인정해야 할 사항이며, 은폐하거나 축소해서는 안 된다. 발표에서는 "현재 rule로 완전히 설명하지 못한 53.2%가 있으며, 이 군의 내부 구조를 추가 분석하는 것이 다음 단계"라고 명확히 밝혀야 한다.

promo0 비교에서는 promo0의 other residual churn이 9.1%로 매우 낮다. promo1 other residual(18.1%)과의 delta가 +9.0%p인 것은, "100원딜 고객의 잔여군조차도 일반 가입자의 잔여군보다 더 위험하다"는 것을 시사한다. 이것도 추가 분석의 필요성을 지지하는 비교 신호이다.

age=60 subgroup (n=172)은 잔여군 내에서 총시청량이 세그먼트 평균보다 약 28분 낮은 주목할 만한 하위 신호이다. 단, 이것도 잔여군 내부 신호이므로 action 제안은 보류하고 모니터링 대상으로만 분류한다.

---

## 4. promo1 Main Scope와 promo0 Comparison Reference 분리

### 4.1 왜 이 분리가 중요한가

100원딜 분석의 핵심은 promo1 (100원딜 고객)이 분석의 주인공이고, promo0 (정가 고객)는 비교 기준이라는 것이다. 이 역할 분리가 명확하지 않으면 두 가지 위험이 생긴다.

첫째, promo0에 대한 불필요한 action을 제안할 수 있다. promo0는 이미 정가로 가입한 고객들이므로, 이들을 대상으로 100원딜 전환 방어 캠페인을 적용하는 것은 의미가 없다.

둘째, 비교 분석의 결론을 잘못 해석할 수 있다. "promo0에서도 같은 패턴이 나타난다"는 사실을 "100원딜 분석이 의미 없다"는 식으로 오해할 수 있다. 올바른 해석은 "공통 패턴이 있더라도, 100원딜 고객군에서 더 높은 위험으로 나타난다면 100원딜 고객 특화 대응이 필요하다"는 것이다.

### 4.2 어떻게 사용해야 하는가

발표와 의사결정에서 promo1과 promo0의 역할을 다음과 같이 명확히 구분한다.

promo1은 action의 대상이다. high_risk_week3_inactivity_or_retention_decay, high_risk_activation_or_low_engagement, mid_risk_retention_watchlist, stable_usage_lower_risk, other_needs_review_residual — 이 5개 family가 promo1의 main business action matrix를 구성한다.

promo0는 비교 기준이다. promo0의 segment별 churn rate와 GB risk는 "promo1에서 같은 패턴이 얼마나 더 위험하게 나타나는가"를 평가하는 비교 지표로 사용한다. promo0에 대한 별도 action 제안은 하지 않는다.

---

## 5. Demographic Action Layer

### 5.1 연령/성별은 대표 segment rule이 아니다

이 분석의 segment는 행동 기반으로 설계되었다. 연령이나 성별은 segment를 나누는 기준이 아니라, segment 내부에서 메시지와 콘텐츠 추천을 개인화하는 보조 layer이다. 이 구분이 매우 중요하다.

"20대는 고위험 segment이다" — 이것은 잘못된 표현이다. 올바른 표현은 "high_risk_week3_inactivity_or_retention_decay segment 내에서 age=20 고객군이 특정 행동 차이를 보인다는 EDA 신호가 있어, 이 subgroup에 대한 메시지 variant를 검토할 수 있다"이다.

### 5.2 Shortlist 근거

기존 60개 demographic action candidate를 16개로 축소한 근거는 다음과 같다.

첫째, n < 50인 subgroup은 main storyline에서 제외했다. n=48인 stable 군 age=10은 통계적으로 불안정하므로 action 제안이 부적절하다.

둘째, 같은 age_group이 동일 segment 내에서 여러 feature에 걸쳐 반복 등장하는 경우 하나로 통합했다. high_risk_activation_or_low_engagement의 age=30은 3개 feature 행이 1개 통합 행으로 정리되었다.

셋째, promo0 candidate는 `include_in_storyline=comparison_only`로 분리했다. promo0 demographic 정보는 비교 맥락에서만 참조하며, action 제안 대상이 아니다.

넷째, 행동 diff가 매우 작은 경우(특히 high_risk_activation 군의 gender diff)는 overinterpretation_risk를 high로 표시하고, evidence_strength를 limited로 유지했다.

### 5.3 팀원 검토 및 외부 리서치 필요성

demographic action personalization을 실제로 적용하려면 데이터 분석만으로는 부족하다. 다음 단계가 필요하다.

팀원 검토: 마케팅팀, 콘텐츠팀, CRM팀이 각 demographic action candidate를 검토하고 실현 가능성을 판단해야 한다.

외부 리서치: 특정 age_group이나 gender의 OTT 이용 패턴에 대한 업계 리서치나 사용자 인터뷰를 통해 EDA 신호를 검증해야 한다.

실험 설계: 실제 집행 전에 소규모 A/B test를 통해 demographic 기반 메시지 variant의 효과를 검증해야 한다.

---

## 6. Small Signal Handling

### 6.1 genre_or_content_action_cue 강등 이유

genre_or_content_action_cue가 main storyline comparison에서 강등된 이유는 단 하나이다. promo1에서 n=11, promo0에서 n=5 — 이 숫자는 main segment 수준에서 논의하기에 너무 작다.

n=11인 신호를 main storyline 비교 지표로 올리면 다음과 같은 문제가 생긴다. 첫째, 11명의 churn rate가 81.8%라고 해도 이것이 모집단 수준에서 의미 있는 신호인지 확인하기 어렵다. 11명 중 한두 명의 차이로 churn rate가 크게 달라질 수 있다. 둘째, 청중이 "장르/콘텐츠가 이탈을 결정한다"는 잘못된 인상을 받을 수 있다.

따라서 genre_or_content_action_cue는 main storyline에서 profile/action personalization cue로 강등되었다. 이 신호가 완전히 무의미하다는 것이 아니라, main segment 기준으로 사용하기에는 n이 너무 작다는 것이다. 추후 충분한 n이 확보되면 재검토할 수 있다.

### 6.2 Small signal 처리 원칙

이 분석에서 small signal을 처리하는 원칙은 다음과 같다.

제거하지 않는다: small signal은 삭제하지 않고 보존한다. 향후 분석에서 활용될 수 있다.

승격하지 않는다: n이 작은 signal을 대표 segment로 승격시키지 않는다.

레이블을 명확히 한다: profile note, action cue, sub-signal, flagged_for_review 등의 레이블을 붙여 main segment와 구분한다.

n 기준을 명시한다: 이 분석에서 main comparison 기준은 최소 n=300으로 한다. 이것은 보수적 기준이며, 팀 협의에 따라 조정될 수 있다.

---

## 7. 주요 Caveat 모음

### 7.1 SHAP 인과 아님

이 분석에서 SHAP은 model explanation 목적으로만 사용했다. SHAP 값이 높다는 것은 해당 feature가 모델의 예측에 강하게 영향을 미친다는 것을 의미한다. 그것이 그 feature가 이탈의 원인이라는 것을 의미하지 않는다.

예를 들어 watch_time_min_w3가 SHAP에서 높게 나온다고 해서 "3주차 시청량 감소가 이탈을 유발했다"고 말하면 안 된다. 올바른 표현은 "모델은 3주차 시청량을 위험 판단에 강하게 활용했다"이다.

### 7.2 OOF threshold 아님

OOF score는 out-of-fold cross-validation 방식으로 산출된 모델 예측값이다. 이 score는 고객의 이탈 위험을 ranking하는 데 유용하다. 그러나 "score가 0.7 이상이면 캠페인 대상"처럼 campaign threshold로 직접 사용해서는 안 된다. threshold 설정은 별도의 의사결정 과정이 필요하다.

### 7.3 07~10 pending

분석 파이프라인에서 07~10 validation 단계는 아직 pending이다. 현재 결과는 발표 준비 단계이며, 최종 validation이 완료되기 전까지 모든 segment와 action candidate는 provisional로 표기한다.

### 7.4 segment provisional

모든 segment label은 provisional이다. 사용자의 최종 승인 없이 어떠한 segment name도 확정 이름으로 사용하면 안 된다.

### 7.5 residual caveat

other_needs_review_residual이 promo1의 53.2%를 차지하는 것은 솔직한 현재 한계이다. 이를 축소하거나 은폐하지 않는다. 내부 decomposition 분석이 추가로 필요하다.

---

## 8. 발표용 핵심 메시지

### 8.1 한 줄 메시지

"100원딜 고객은 낮은 진입 비용으로 유입된 체험 고객이므로, 핵심은 가입 여부가 아니라 3주차까지 정가 전환을 감수할 만큼의 반복 이용 습관이 형성되었는지를 보는 것이다."

### 8.2 세 가지 핵심 포인트

첫 번째 포인트: "3주차 시청 행동이 정가 전환 실패를 구분하는 강한 관찰 신호이다." 100원딜 고객 중 3주차에 시청이 급감하거나 비활성 상태가 되는 군(n=1,893, churn=74.3%)이 가장 중요한 개입 후보이다.

두 번째 포인트: "같은 위험 패턴이 100원딜 고객군에서 더 높은 이탈률로 관찰된다." 5개 segment 모두에서 promo1의 churn이 promo0보다 높다. 특히 mid_risk segment에서 delta가 +18.4%p로 가장 크다. 이는 100원딜 고객 특화 대응의 필요성을 지지한다.

세 번째 포인트: "현재 rule로 설명되지 않는 53.2%가 있으며, 이에 대한 추가 분석이 필요하다." other_needs_review_residual의 존재를 솔직하게 인정하고, 이를 다음 단계 분석 과제로 명시한다.

### 8.3 발표에서 반드시 언급해야 할 caveat

발표 시작 시 또는 결론 부분에서 다음을 명시한다. "이 분석의 segment는 all provisional이며, OOF score는 campaign threshold가 아니다. SHAP은 인과 원인이 아니라 model explanation이다. demographic action candidate는 EDA 기반 hypothesis이며 실제 적용 전 팀 검토와 A/B test가 필요하다."

---

## 9. Hotfix 변경 요약

이번 hotfix에서 변경된 내용과 변경하지 않은 내용을 명확히 기록한다.

### 변경된 내용 (hotfix)

- demographic action candidate를 60행 all-yes에서 16행 shortlist로 축소
- promo0 action matrix를 별도 comparison_reference 파일로 분리
- storyline comparison에서 genre_or_content_action_cue (n=11) 강등
- storyline comparison에 mid_risk_retention_watchlist 추가 (기존 누락)
- HTML visual guide를 comprehensive version으로 재작성 (flag dictionary, segment cards, safe/unsafe wording, demographic layer 추가)

### 변경하지 않은 내용

- 어떠한 모델도 재실행하지 않았다
- OOF score, SHAP 값도 변경하지 않았다
- segment assignment도 재실행하지 않았다
- canonical segment set의 n, churn rate, GB risk 값도 변경하지 않았다
- 기존 18 원본 파일들은 그대로 보존되어 있다

---
