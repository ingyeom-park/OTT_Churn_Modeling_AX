# 06h 멘토 대응 업데이트

멘토님 지적 이후에는 높은 AUC를 그대로 공식 모델로 주장하지 않고, 원본/파생 중복 피처와 shortcut 가능성이 있는 피처를 분리해서 다시 점검했습니다.

원본/파생 중복 피처는 `total_watch_time`, week ratio, week-to-week delta, genre watch_time, genre session_count, coverage/missing complement처럼 같은 사용량 정보를 반복해서 담는 변수군을 공식 후보에서 제외하는 방식으로 정리했습니다.

`product_code`는 요금제나 상품 조합을 외우는 방향으로 성능을 끌어올릴 수 있고, `watch-presence shortcut`은 시청 여부 자체가 이탈 여부와 너무 가까운 신호가 될 수 있기 때문에 기본 모델에서는 제외했습니다.

1~3주 전체 관측창은 week1, week2, week3의 watch_time과 sessions를 모두 포함하는 방식으로 반영했습니다. 다만 week3 정보가 들어가므로 “완전한 1주차 조기예측”이 아니라 “1~3주 관측 기반 이탈 위험 랭킹”으로 표현하는 것이 안전합니다.

최종 추천 모델의 AUC는 0.862148, top-decile lift는 2.755381입니다.

0.90 수준의 성능은 w1_4 late-period 또는 더 강한 시점 정보가 들어간 결과와 연결될 수 있으므로 조기예측 성능으로 주장하지 않습니다. 이 값은 말기 관측 또는 탐색적 상한선으로만 분리해서 설명해야 합니다.

개별 변수보다 feature family 단위로 해석해야 하는 이유는 weekly usage, genre ratio처럼 서로 강하게 연동되는 변수들이 남아 있기 때문입니다. 따라서 개별 변수 하나가 독립적으로 이탈을 만든다고 말하기보다, 사용량 패턴, 장르 선호 구성, 멤버십 맥락 같은 묶음 단위로 설명하는 것이 방어 가능합니다.
