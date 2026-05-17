# 18x Onepager

## 문제
100원딜 프로모션 유입 이후 재구매 방어는 단순 재구매율 비교가 아니라 day0~20 관측창 내 행동 신호 기반 대응 설계가 필요하다.

## 분석 설계
day0~20 관측, day21 scoring point, 이후 대응기간으로 나누고, target은 다음 달 재구매 여부로 둔다. 분석 단위는 subscription-event rows다.

## 핵심 발견
17x에서 7개 provisional representative segment가 생성되었고, 고위험 inactive/drop, 초기 activation 약화, 저활동, retention decay, content proxy, stable retained 등 행동 기반 대응 후보가 분리되었다.

## 대표 Segment
가장 큰 segment는 general_observation과 content_preference_target_candidate이며, 고위험 대응 후보로는 high_risk_week3_inactive_or_drop, high_risk_only_w1_or_cold_start_weak, high_risk_low_activity가 있다.

## 제언
day21 이후 동일한 메시지를 보내기보다 행동 신호별로 재진입, 온보딩, broad recommendation, retention decay 대응, content proxy 추천, 안정 row 유지/업셀 후보를 분리한다.

## 주의점
SHAP은 인과가 아니며, 100원딜 여부도 인과로 해석하지 않는다. payment/auth/demographic proxy는 제언 근거로 직접 쓰지 않는다.

## 한 줄 결론
100원딜 이탈 방어의 핵심은 day0~20 안에서 식어가는 신호를 조기에 발견하고 day21 이후 대응기간에 맞춤 개입하는 것이다.
