# 18x Presentation Narrative Script

본 분석은 고객 개인을 단정하는 것이 아니라, subscription-event row에서 관측된 행동 신호를 바탕으로 대응 후보를 설계하는 것입니다.

먼저 분석 시간축은 day0~20 관측창, day21 scoring point, 이후 대응기간으로 나누었습니다. target은 다음 달 재구매 여부이며, 모델의 repurchase_score는 재구매 가능성 점수, churn_risk는 1에서 repurchase_score를 뺀 값으로 사용했습니다.

모델은 고객을 확정적으로 분류하기 위한 도구가 아니라, 어떤 row에서 이탈 위험이 높게 나타나고 어떤 행동 신호가 함께 보이는지 정리하기 위한 보조 도구입니다. SHAP은 원인이 아니라 모델이 어떤 변수를 중요하게 사용했는지에 대한 설명입니다.

17x segmentation에서는 payment/auth/demographic 변수는 대표 세그먼트 기준으로 쓰지 않았습니다. payment/auth/demographic 변수는 해석 리스크가 있어 대표 세그먼트 기준으로 쓰지 않았습니다.

100원딜 여부는 집단 차이로 해석하며, 인과효과로 단정하지 않습니다. 따라서 발표에서는 100원딜이 이탈을 유발했다고 말하지 않고, 관측된 집단과 행동 신호의 차이를 바탕으로 대응 후보를 제안합니다.

비즈니스 제언은 모든 row에 동일한 할인이나 알림을 보내는 것이 아니라, week3 inactive/drop, 초기 activation 약화, low activity, retention decay, content preference proxy, stable retained 상태에 따라 메시지와 타이밍을 다르게 설계하는 방향입니다.

결론적으로 100원딜 이탈 방어의 핵심은 싸게 들어온 고객을 붙잡자는 단순 메시지가 아니라, day0~20 안에서 식어가는 신호를 조기에 발견하고 day21 이후 대응기간에 맞춤 개입하자는 것입니다.
