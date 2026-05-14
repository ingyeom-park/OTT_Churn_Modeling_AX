# 13 mentor briefing narrative

## 1. 현재까지 한 일
05b에서 컬럼 역할 기준을 정리했고, 06에서 primary main cohort와 22개 conservative feature 기준을 확정했습니다. 08b에서는 promotion 평균 차이 해석을 보수적으로 패치했고, 09에서는 promotion x repurchase 2x2 구조 안에서 재구매/미재구매 차이를 기술통계로 확인했습니다. 09b는 사용량 feature가 day0~20 원천 view 기준과 일치한다는 점을 검증했습니다.

## 2. 데이터 기준과 시간축
raw master는 23,343행이고, duration < 21 제외 238행과 duration 정책 이후 중복 extra 26행을 제외한 primary main cohort는 23,079행입니다. 분석 단위는 unique user가 아니라 row-level / subscription-event-level입니다. 09b 기준 day21+ raw views는 17,621건이 있었지만, core usage mismatch day0~20은 0으로 관찰되었습니다.

## 3. 가장 중요한 발견 3개
첫째, 프로모션 행의 재구매율은 67.5151%이고 비프로모션 행의 재구매율은 76.2416%로 관찰되었습니다. 이 차이는 인과효과 아님이며 기술통계입니다. 둘째, 08b 기준 promotion 평균 행동 차이는 작게 관찰되었고, 09의 2x2 내부 재구매/미재구매 차이에서 watch_time(min)_w3, watch_session_w3, is_only_w1 신호가 더 강하게 관찰되었습니다. 셋째, 10 feature EDA는 이 신호를 분포 관점에서 다시 확인했지만, 새 모델링이나 threshold를 만들지는 않았습니다.

## 4. 모델링 현재 상태
11b는 corrected baseline growth history로 사용합니다. 12c canonical comparison found and used. 12c가 있는 경우 XGBoost는 여러 scope에서 높은 AUC 모델 후보로 관찰되지만, 안정성 후보는 별도로 봅니다. 현재 결과는 모델 후보 비교이며 최종 모델, 운영 threshold, segmentation이 아닙니다.

## 5. 아직 확정하면 안 되는 것
100원딜 때문에 이탈했다는 식의 인과 주장은 하면 안 됩니다. top-k churn_risk는 운영 threshold 아님이며, 캠페인 대상 확정도 아닙니다. SHAP과 Optuna는 아직 수행하지 않았고, Referral 성과 분석과 final segmentation도 Step 13 범위가 아닙니다.

## 6. 다음 단계
멘토 보고에서는 Step 13 synthesis를 기준으로 현재 상태를 공유하고, 다음으로 12c 후보 검증 후 14 Optuna candidate tuning 또는 16 SHAP candidate interpretation으로 넘어가는 것이 안전합니다. segmentation은 이후 17 단계에서 별도로 다루는 편이 맞습니다.
