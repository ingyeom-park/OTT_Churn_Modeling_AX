# 08b Team Share Final Segment Summary

## 기준
- Stage 08b는 Stage 08 세그먼트를 발표용으로 줄이고 재명명한 단계입니다.
- 위험밴드는 유지하고, rule segment는 타깃 그룹과 modifier로 분리했습니다.
- 최종 XAI 근거는 Stage 07r TRUE SHAP입니다. Stage 07 fallback은 최종 근거로 쓰지 않습니다.

## 최종 발표용 세그먼트
- 최상위 이탈위험군: n=478, churn rate=0.785, lift=2.73, Stage09=Y, action=고위험 모니터링, 개인화 리텐션 메시지, 초기 콘텐츠 재추천
- 초기 저관여 고위험군: n=478, churn rate=0.567, lift=1.98, Stage09=Y, action=초기 온보딩, 첫 시청 유도, 개인화 콘텐츠 추천
- 상위위험 관찰/추천 후보군: n=478, churn rate=0.615, lift=2.14, Stage09=Y, action=위험 점수 기반 모니터링과 장르/이용 패턴별 후속 추천
- 3주차 집중 시청 안정/전환 후보군: n=1174, churn rate=0.070, lift=0.24, Stage09=Y, action=이어보기, 시리즈 연속 추천, 구독 종료 전 유지 메시지
- 장르 선호 기반 콘텐츠 추천군: n=1496, churn rate=0.144, lift=0.50, Stage09=Y, action=장르별 이어보기, 신작/유사작 추천, 취향 기반 큐레이션
- 저위험/일반 유지군: n=673, churn rate=0.198, lift=0.69, Stage09=N, action=과도한 개입보다 기본 추천과 모니터링 유지

## 발표 시 주의
- 예측/기술 세그먼트이지 인과효과 검증 결과가 아닙니다.
- 가격/프로모션은 독립 세그먼트보다 modifier로만 다룹니다.
- 3주차 집중 시청군은 고위험군이 아니라 안정/전환 후보군으로 표현합니다.
- 기타/일반군은 최종 주장 대상에서 제외합니다.

## 추천 그림
- 08b_final_segment_churn_rate_holdout.png
- 08b_final_segment_size_and_lift.png
- 08b_risk_band_capture_curve.png
- 08b_final_segment_action_map.png
