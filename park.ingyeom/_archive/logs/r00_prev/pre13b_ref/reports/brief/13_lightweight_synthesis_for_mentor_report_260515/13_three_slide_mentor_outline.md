# 13 three-slide mentor outline

## Slide 1. 데이터 기준과 분석 설계
- raw master 23,343행에서 primary main cohort 23,079행으로 정리
- duration < 21 제외 238행, duration 정책 이후 중복 extra 제외 26행
- 22개 conservative feature 기준, row-level / subscription-event-level 분석
- 09b에서 day0~20 core usage mismatch 0 확인

What to say verbally: 데이터 기준과 시간축을 먼저 고정했기 때문에 이후 결과는 같은 분석 단위 위에서 설명할 수 있다고 말합니다.

What not to say: unique user 분석이라고 말하지 않습니다. day21+ 행동까지 모델 feature에 들어갔다고 말하지 않습니다.

## Slide 2. 핵심 발견: promotion 평균 차이보다 2x2 내부 3주차 신호
- 비프로모션 재구매율 76.2416%, 프로모션 재구매율 67.5151%로 관찰
- gap은 promotion minus nonpromotion 기준 -8.73 percentage points
- promotion 평균 행동 차이는 작았고, 2x2 내부 재구매/미재구매 차이가 더 강하게 관찰
- 주요 기술통계 신호: watch_time(min)_w3, watch_session_w3, is_only_w1

What to say verbally: 프로모션 자체의 평균 차이보다 같은 promotion 여부 안에서 재구매 여부를 가르는 3주차 사용 신호가 더 설명력이 있어 보였다고 말합니다.

What not to say: 100원딜 때문에 이탈했다고 말하지 않습니다. 행동 패턴이 완전히 다르다고 말하지 않습니다.

## Slide 3. 모델 후보와 다음 단계
- 11b는 corrected baseline으로 사용
- 12c는 canonical fixed-parameter model comparison으로 사용
- XGBoost는 높은 AUC 모델 후보로 관찰되지만 최종 모델은 아님
- top-k churn_risk는 운영 진단 지표이며 운영 threshold 아님
- 다음 단계는 12c 후보 확인 후 14 Optuna 또는 16 SHAP, segmentation은 17 이후

What to say verbally: 현재는 최종 운영 모델이 아니라 후보 비교 단계이며, 튜닝과 설명은 후보 확정 뒤에 해야 한다고 말합니다.

What not to say: XGBoost가 최종 모델이라고 말하지 않습니다. SHAP이 원인을 밝혔다고 말하지 않습니다.
