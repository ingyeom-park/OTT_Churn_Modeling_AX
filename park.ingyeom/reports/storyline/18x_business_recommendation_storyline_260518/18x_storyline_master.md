# 18x Business Recommendation Storyline

## 1. 문제 제기
100원딜 프로모션 유입 row는 단순히 재구매율만 비교해서 판단하기보다, day0~20 관측창 안에서 어떤 행동 신호를 보였는지를 기준으로 이탈 방어 전략을 설계해야 한다. 이 단계의 목적은 고객 개인을 단정하는 것이 아니라 subscription-event rows에서 관측된 행동 신호를 바탕으로 대응 후보를 정리하는 것이다.

## 2. 분석 설계
분석 시간축은 day0~20 관측, day21 scoring point, 이후 대응기간으로 둔다. target은 다음 달 재구매 여부인 `is_repurchase`이며, `repurchase_score = P(is_repurchase=1)`, `churn_risk = 1 - repurchase_score`로 해석한다. 분석 단위는 고객 수가 아니라 row-level subscription-event rows다.

## 3. 모델 결과의 역할
모델은 고객을 단정하는 도구가 아니라 이탈 위험과 행동 패턴을 묶어 대응 우선순위를 정하는 보조 도구다. SHAP은 원인이 아니라 fitted model이 어떤 변수를 중요하게 사용했는지에 대한 설명이다.

## 4. Segment 전환
17x에서는 high risk, retention decay, low activity, content preference, stable retained 등 행동 기반 provisional representative segment를 만들었다. 총 7개 segment이며, representative assignment는 23,079 subscription-event rows에 대해 row당 하나씩 부여되었다.

## 5. 비즈니스 제언
segment별로 다른 대응이 필요하다. 모든 row에 같은 할인 또는 알림을 보내기보다, week3 inactive/drop, 초기 activation 약화, 저활동, retention decay, content preference proxy, stable retained 상태에 따라 메시지와 타이밍을 다르게 가져간다.

## 6. 주의점
payment/auth/demographic proxy를 제언 근거로 쓰지 않는다. SHAP은 인과가 아니다. 100원딜 효과도 인과가 아니다. 이 결과는 row-level 분석이며 unique customer 수로 표현하지 않는다.

## 7. 결론
100원딜 이탈 방어의 핵심은 '싸게 들어온 고객을 붙잡자'가 아니라, day0~20 안에서 식어가는 신호를 조기에 발견하고 day21 이후 대응기간에 맞춤 개입하자는 것이다.
