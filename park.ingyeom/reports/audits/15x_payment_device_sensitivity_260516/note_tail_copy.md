ion_only/HistGradientBoosting; expanded_feature_set/nonpromotion_only/LightGBM; conservative_safe_22/overall_with_promotion/CatBoost
- 한글 폰트 설정: selected_font=Malgun Gothic, axes.unicode_minus=False, font test figure 생성 완료.
- 주요 top feature/family는 16x_SHAP_global_importance.csv와 16x_SHAP_family_importance.csv에 기록했다.
- VIF/redundancy 때문에 개별 변수보다 feature family/redundancy family 단위 해석을 권장한다. feature removal은 수행하지 않았다.
- 최종 segmentation/threshold/campaign threshold는 아직 아니다. 다음 단계는 17x segmentation design이다.

## 16x_SHAP_candidate_interpretation_hotfix_260516
- 수행: 16x figure layout hotfix를 수행했다.
- 수정: reports/figures/16x_SHAP_candidate_interpretation_260516/16x_fig_scope_top10_SHAP_comparison.png의 subplot 제목, 축 라벨, 여백 겹침 가능성을 줄이기 위해 2x2 발표용 layout으로 재생성했다.
- SHAP 값 재계산 없음. 모델 재학습 없음. Optuna, segmentation, feature removal 없음.
- 변경 파일: 16x_fig_scope_top10_SHAP_comparison.png, 16x notebook hotfix cell, README.md, note.md, hotfix audit CSV, hotfix review zip.

## 2026-05-16 | 15x 전 결제기기·인증·연령 proxy 리스크 및 sensitivity 필요성 정리

### 1. 이 메모의 목적

이 메모는 12x model family comparison, 14x lightweight tuning, 16x SHAP interpretation까지 완료된 뒤, 17x segmentation으로 넘어가기 전에 새롭게 확인된 중요한 해석 리스크를 기록하기 위해 작성한다.

핵심 리스크는 `payment_device` 원본 및 그 파생변수인 `payment_is_mobile`, `payment_is_pc`, `payment_is_android`, `payment_is_ios` 계열이다.

현재 expanded_feature_set에는 원본 `payment_device`는 들어가지 않았지만, `payment_is_mobile`, `payment_is_pc`, `payment_is_android`, `payment_is_ios` 파생변수가 포함되어 있다.

문제는 이 변수들이 “시청 기기”가 아니라 “결제 기기 또는 결제 환경”에 가깝다는 점이다. 따라서 이 변수가 모델 성능이나 SHAP에서 중요하게 나오더라도, 이를 “아이폰으로 결제하면 이탈이 줄어든다”, “iOS 사용자는 충성도가 높다”, “결제 기기 자체가 재구매를 만든다”처럼 해석하면 안 된다.

이 메모의 목적은 다음과 같다.

1. payment_device 계열 변수가 왜 해석상 위험한지 기록한다.
2. 40대·미인증·iOS 조합이 왜 단순 고객 세그먼트가 아니라 artifact/proxy일 수 있는지 기록한다.
3. 17x segmentation 전에 payment_device 제거 sensitivity를 수행해야 하는 이유를 기록한다.
4. payment_device 계열을 제거할지 유지할지 LLM이 임의 결정하지 않고, 데이터 기반 sensitivity 결과와 사용자 승인으로 결정하도록 한다.

---

### 2. 현재까지의 모델링/해석 상태

현재 최신 흐름은 다음과 같다.

- 06x dataset generation 통과
  - primary main cohort 23,079 rows 기준
  - conservative_dataset과 expanded_dataset 생성
  - cold_start fixed row-level hotfix 완료
  - `is_basic`, `is_cold_start_3d_fixed`, `is_cold_start_7d_fixed`만 새 파생변수로 생성
  - 사용자 승인 없는 새 feature 생성 없음

- 07x feature mapping / AARRR mapping 통과
  - 06x conservative/expanded dataset 기준으로 feature mapping 재작성
  - pre13b 07 구조는 참고만 하고, 06x 기준으로 새 mapping 생성

- 10x feature distribution / redundancy pre-audit 통과
  - VIF, pairwise correlation, redundancy family 확인
  - feature removal은 하지 않음
  - redundancy/VIF는 제거 근거가 아니라 해석 주의사항으로만 기록

- 11x baseline growth comparison 통과
  - conservative_safe_22 vs expanded_feature_set 비교
  - expanded_feature_set의 성능 향상이 확인됨
  - feature removal 없음

- 12x model family comparison 통과
  - LightGBM, CatBoost, XGBoost 등 model family 비교
  - expanded_feature_set의 성능이 전반적으로 우수
  - 최종 모델 확정은 아님

- 14x lightweight tuning 통과
  - 12x 후보 기반 경량 Optuna tuning 수행
  - 최종 모델 확정은 아님
  - 일부 tuned 후보에서 성능 개선 확인

- 16x SHAP interpretation 통과
  - SHAP은 인과가 아니라 model explanation으로 제한
  - 한글 폰트 및 시각화 산출물 검수 완료
  - 16x hotfix로 scope top10 SHAP comparison figure layout 개선 완료

현재 다음 정식 단계는 17x segmentation design이지만, 17x 전에 payment_device 계열의 해석 리스크를 정리할 필요가 생겼다.

---

### 3. payment_device 계열의 본질적 문제

`payment_device`는 이름상 기기 정보처럼 보이지만, 실제 의미는 “시청 기기”가 아니라 “결제 기기 또는 결제 환경”이다.

사용자 설명 기준으로 다음과 같은 상황이 가능하다.

- 아버지가 iPhone으로 결제하고, 실제 시청자는 자녀일 수 있다.
- 결제는 iOS에서 했지만, 실제 시청은 TV, PC, Android, 태블릿에서 할 수 있다.
- 결제 기기는 계정 생성 또는 결제 경로의 흔적일 뿐, 콘텐츠 시청 경험을 직접 의미하지 않는다.
- iPhone으로 결제했다고 해서 화질, 콘텐츠 선호, 시청 몰입도, 서비스 경험이 직접 달라진다고 보기 어렵다.
- Galaxy로 시청한다고 해서 화질이 달라지는 것도 아니며, 결제 기기와 시청 기기는 개념적으로 다르다.

따라서 `payment_is_ios` 또는 `payment_is_android`가 SHAP에서 높게 나오더라도, 이를 다음처럼 해석하면 안 된다.

금지 해석:

- “iOS로 결제하면 이탈 확률이 낮다.”
- “아이폰 사용자는 재구매율이 높다.”
- “안드로이드 사용자는 이탈한다.”
- “결제 기기가 재구매를 유발한다.”
- “시청 기기 경험 차이가 이탈을 설명한다.”

허용 가능한 해석:

- “payment_device 계열은 결제 환경, 인증 상태, 유입 경로, 계정 생성 맥락, 비프로모션 구조와 얽힌 proxy일 수 있다.”
- “모델은 payment_device 파생변수를 재구매 score 설명에 사용했지만, 이는 시청 경험의 인과효과를 뜻하지 않는다.”
- “payment_is_ios는 시청 기기가 아니라 결제 환경의 흔적이므로, 비즈니스 세그먼트명이나 원인 설명에 직접 사용하지 않는다.”
- “이 변수는 artifact/proxy risk를 가진 변수로 보고, segmentation 전 sensitivity 검토가 필요하다.”

---

### 4. 40대·미인증·iOS 조합의 리스크

이 프로젝트에서 사용자와의 논의 중 중요한 관찰이 있었다.

`40대 + 미인증 + iOS` 조합은 단순한 “고객 특성”처럼 보이지만, 실제로는 다음 문제가 있다.

1. 미인증 상태의 연령 정보는 인구통계적으로 충분히 검증된 값인지 불명확하다.
2. 결제기기 iOS는 시청기기가 아니라 결제기기다.
3. 이 조합은 promotion/nonpromotion split과 강하게 얽힐 가능성이 있다.
4. 이 조합이 모델에서 중요하게 나오더라도, 고객의 실제 성향이나 시청 경험이라고 단정할 수 없다.
5. 40대·미인증·iOS를 세그먼트 이름으로 쓰면, 데이터 생성 구조의 artifact를 실제 고객군처럼 포장할 위험이 있다.

특히 프로젝트 초기에 promotion/nonpromotion 방향으로 분석 축을 튼 이유 중 하나도, 40대·미인증 계열을 인구통계적으로 해석하기 어렵다는 점이 포함되어 있었다.

즉, 이 문제는 새로 생긴 문제가 아니라, 프로젝트 방향성의 배경에 이미 존재하던 리스크다. 다만 16x SHAP 이후, payment/auth/demographic 계열이 모델 설명에 일정 부분 나타날 수 있으므로 17x segmentation 전에 명시적으로 관리해야 한다.

---

### 5. 왜 바로 제거하지 않고 sensitivity를 먼저 하는가

현재 가장 보수적인 선택은 payment_device 파생변수를 모델 feature에서 제거하는 것이다.

제거 대상 후보:

- `payment_is_mobile`
- `payment_is_pc`
- `payment_is_android`
- `payment_is_ios`

하지만 바로 canonical expanded_feature_set에서 제거하고 06x부터 모든 단계를 다시 실행하는 것은 부담이 크다. 이미 06x, 07x, 10x, 11x, 12x, 14x, 16x까지 진행됐기 때문이다.

반대로 이 변수를 아무 조치 없이 그대로 두고 17x segmentation으로 가는 것도 위험하다. 세그먼트가 payment_device proxy에 오염될 수 있고, 발표에서 결제기기를 실제 시청경험처럼 잘못 설명할 수 있기 때문이다.

따라서 현재 가장 안전한 방식은 다음이다.

`15x_payment_device_sensitivity_260516`

15x의 목적은 canonical 전체를 즉시 갈아엎는 것이 아니라, 다음 두 조건을 비교하는 것이다.

1. 기존 expanded_feature_set
2. expanded_feature_set에서 payment_is_* 4개를 제거한 sensitivity feature set

이 비교를 통해 다음을 확인한다.

- payment_is_* 제거 시 AUC/AP/Brier/top-k 성능이 얼마나 변하는가
- payment_is_* 제거 시 SHAP 상위 feature가 행동 변수 중심으로 더 안정되는가
- payment_is_* 제거 시 segment 후보가 proxy 오염에서 벗어나는가
- 성능 손실이 작다면 canonical에서도 제거할 수 있는가
- 성능 손실이 크다면 모델 feature로 유지하되, 해석/세그먼트/비즈니스 제언에서는 artifact/proxy로만 다룰 것인가

---

### 6. 15x의 성격

15x는 최종 모델링 단계가 아니다.

15x는 다음도 아니다.

- Optuna 단계 아님
- SHAP 본단계 아님
- segmentation 단계 아님
- feature removal 확정 단계 아님
- campaign threshold 결정 단계 아님

15x는 sensitivity audit 단계다.

목적은 다음이다.

- payment_device 계열을 제거했을 때 성능과 해석 안정성이 어떻게 변하는지 확인한다.
- 제거 여부를 LLM이 확정하지 않는다.
- 결과를 보고 사용자가 canonical feature contract를 수정할지 결정한다.

따라서 15x 결과는 다음과 같이 해석해야 한다.

- 성능 손실이 거의 없음 → payment_is_*를 canonical expanded에서 제거하는 방향 검토
- 성능 손실이 큼 → 모델 feature로는 유지할 수 있으나, 해석/세그먼트 rule에서는 사용 금지
- SHAP 해석이 더 깨끗해짐 → segmentation에서는 payment_device 계열 제외 강하게 권장
- 성능은 좋아도 SHAP이 payment_device에 과의존 → proxy-contamination risk로 기록

---

### 7. 17x segmentation에 대한 영향

17x segmentation에서는 payment_device 계열을 대표 세그먼트 rule에 직접 사용하면 안 된다.

금지되는 세그먼트 예시:

- “40대 미인증 iOS 안정군”
- “iOS 결제 고충성군”
- “Android 결제 이탈위험군”
- “미인증 iOS 고객군”
- “iOS 사용자 재구매군”

이런 이름은 payment_device를 시청기기나 고객 성향으로 오해하게 만든다.

17x에서는 다음 방식이 안전하다.

1. 대표 세그먼트 rule은 행동 기반으로 만든다.
   - 3주차 시청량
   - retention ratio
   - week-to-week drop
   - only_w1
   - cold_start_fixed
   - churn_risk
   - content preference caveat

2. payment_device, is_user_verified, age_group 조합은 세그먼트 조건이 아니라 artifact/proxy audit flag로 관리한다.

3. 예를 들어 다음 flag를 검수용으로만 만들 수 있다.

`flag_age40_unverified_ios`

단, 이 flag는 segment assignment 조건으로 쓰지 않는다. segment별 proxy concentration을 점검하는 용도다.

4. 각 segment별로 다음을 확인한다.

- payment_is_ios 비중
- is_user_verified=0 비중
- age_group=40 비중
- flag_age40_unverified_ios 비중
- 이 조합이 특정 segment에 과도하게 몰려 있는지

5. 특정 segment가 payment/auth/demographic proxy에 과도하게 의존하면, 그 segment는 행동 기반 세그먼트가 아니라 proxy-contaminated segment일 수 있으므로 caveat를 붙인다.

---

### 8. 15x에서 반드시 확인할 지표

15x는 최소 다음을 확인해야 한다.

성능 비교:

- 기존 expanded_feature_set AUC
- payment_is_* 제거 sensitivity AUC
- delta AUC
- AP 변화
- Brier 변화
- logloss 변화
- train-valid gap 변화
- fold AUC std 변화

운영 지표 비교:

- top5pct precision / recall / lift
- top10pct precision / recall / lift
- top20pct precision / recall / lift
- churn_risk decile calibration 변화

해석 안정성 비교:

- SHAP top feature에서 payment_is_* 제거 후 상위 feature 변화
- 행동 feature의 상대 중요도 변화
- retention / week3 / only_w1 / cold_start_fixed 계열이 더 중심으로 나오는지
- artifact/proxy family importance 감소 여부

세그먼트 위험 사전점검:

- top churn_risk 집단에서 payment_is_* 비중 변화
- 40대·미인증·iOS 조합의 고위험군 과대표집 여부
- payment/auth/demographic artifact family의 위험도

---

### 9. 15x의 권장 산출물

15x에서 생성해야 할 산출물 후보는 다음과 같다.

- `15x_preflight_input_validation.csv`
- `15x_payment_device_feature_policy.csv`
- `15x_feature_set_comparison_design.csv`
- `15x_expanded_no_payment_device_feature_list.csv`
- `15x_model_comparison_without_payment_device.csv`
- `15x_vs_12x_14x_performance_comparison.csv`
- `15x_topk_comparison_without_payment_device.csv`
- `15x_proxy_artifact_audit.csv`
- `15x_age40_unverified_ios_audit.csv`
- `15x_segment_risk_handoff.csv`
- `15x_recommendation_for_canonical_feature_contract.csv`
- `15x_safe_unsafe_wording.csv`
- `15x_open_risks_for_17x.csv`
- `15x_final_checks.csv`
- `README.md`
- review zip

---

### 10. 15x의 최종 결정 원칙

15x는 payment_device 계열 제거 여부를 확정하지 않는다.

15x는 다음 decision을 제안할 수 있다.

1. `remove_payment_device_from_canonical_recommended`
   - 성능 손실이 작고 해석이 개선되는 경우

2. `keep_for_model_but_exclude_from_interpretation`
   - 성능 손실이 크지만, 인과/비즈니스 해석은 위험한 경우

3. `keep_with_strong_proxy_caveat`
   - 성능과 운영 지표에 유의미하게 기여하지만 proxy 위험이 큰 경우

4. `requires_user_decision`
   - 성능/해석 trade-off가 애매해 사용자 판단이 필요한 경우

최종 결정은 LLM이 하지 않는다.  
최종 feature contract 수정 여부는 사용자가 승인한다.

---

### 11. 현재 결론

현재 가장 안전한 방향은 다음이다.

`17x segmentation으로 바로 가지 않고, 15x_payment_device_sensitivity_260516을 먼저 수행한다.`

이유는 다음과 같다.

- payment_device는 시청기기가 아니라 결제기기/결제환경이다.
- payment_device 계열은 비즈니스 인과 해석이 매우 위험하다.
- 40대·미인증·iOS 조합은 인구통계/인증/결제 구조의 proxy일 수 있다.
- 17x segmentation에서 이 조합을 세그먼트 이름이나 rule로 쓰면 오해가 생길 수 있다.
- sensitivity를 통해 제거해도 성능이 유지되는지 확인한 뒤 canonical feature contract 수정 여부를 결정하는 것이 안전하다.

따라서 다음 작업은 15x다.

`15x_payment_device_sensitivity_260516`

이 단계는 17x segmentation의 사전 안전장치다.

> 15x_payment_device_sensitivity_260516 기록

15x에서는 `payment_is_mobile`, `payment_is_pc`, `payment_is_android`, `payment_is_ios` 네 개 파생변수가 모델 성능과 해석에 미치는 영향을 sensitivity 방식으로 점검했습니다. 이번 작업은 canonical `expanded_feature_set`을 바꾸는 단계가 아니며, 최종 모델 확정, SHAP 본단계, segmentation, feature removal 확정도 아닙니다. 06x의 expanded dataset과 feature contract는 읽기 전용으로 유지했고, 실행 중에만 `expanded_no_payment_device` feature list를 만들어 비교했습니다.

해석상 가장 중요한 전제는 `payment_device`가 시청기기가 아니라 결제기기 또는 결제환경이라는 점입니다. iPhone으로 결제했다고 해서 iPhone으로 시청했다고 볼 수 없고, 결제자와 실제 시청자가 다를 수도 있습니다. 따라서 `payment_is_*`가 모델 성능이나 기존 SHAP 해석에서 중요하게 보이더라도 이를 시청경험, 콘텐츠 소비 방식, 또는 재구매의 인과효과로 해석하면 안 됩니다. 이 변수들은 결제 환경, 계정 생성 맥락, 인증 상태, 유입 구조의 proxy일 가능성이 있습니다.

사용자 확인 사항도 15x handoff에 반영했습니다. `is_user_verified`는 진짜 본인인증 여부이고, 미인증 row의 age/gender는 사용자가 직접 기입했을 수 있지만 일단 신뢰한다는 가정으로 진행합니다. `gender=N`은 Neutral이 아니라 NaN으로 해석합니다. `age_group`은 원본 age를 10단위로 묶은 파생변수입니다. age/gender/auth는 모델 feature로 유지 가능하지만 대표 세그먼트 이름이나 원인 설명에 직접 쓰지 않는 것이 안전합니다. `is_churn_prevented`는 과거 churn prevention 이력이고, `is_promotion=1`은 정확히 100원딜입니다. `recency`는 day0 to day20 관측창 안의 recency로만 해석해야 합니다. `under_1m`과 `under_5m`은 서로 다른 행동 proxy이므로 둘 다 유지합니다. retention ratio는 smoothing이 들어간 상대 변화 지표이고, `is_only_w*`는 day0 to day20 관측창 안에서 해당 주차에만 시청했다는 뜻입니다. genre ratio는 Movie_Master category mapping 기준 proxy입니다.

모델링은 fixed-parameter sensitivity 비교로만 수행했습니다. Optuna, SHAP 재계산, segmentation은 수행하지 않았습니다. scope는 `overall_without_promotion`, `overall_with_promotion`, `promotion_only`, `nonpromotion_only` 네 가지로 유지했고, `USER_KEY`는 group key로만 사용했습니다. 산출된 평균 AUC 변화는 0.003590, 가장 큰 AUC 손실은 -0.000150이며, 성능 손실 레벨은 `near_neutral`로 기록했습니다. 다만 이 수치는 제거 확정 근거가 아니라 사용자 승인 전 검토 근거입니다.

`flag_age40_unverified_ios`는 `age_group == 40`, `is_user_verified == 0`, `payment_is_ios == 1` 조합을 audit 전용으로 계산한 것입니다. 이 flag는 모델 feature로 만들지 않았고, segment rule로도 사용하지 않았습니다. 고위험군 안에서 이 조합의 비중이 보이더라도 '40대 미인증 iOS가 이탈 원인'이라고 쓰면 안 되며, artifact 또는 proxy concentration 가능성으로만 다뤄야 합니다.

최종 recommendation은 `pending_user_approval`입니다. 17x representative segment rule에서는 payment/auth/demographic proxy를 직접 rule로 쓰지 말고, 행동 기반 변수 우선 원칙을 유지해야 합니다. 만약 사용자가 payment-device 계열을 canonical feature contract에서 제거하기로 승인하면, 기존 16x SHAP은 새 contract와 맞지 않으므로 보강 또는 재실행 여부를 다시 결정해야 합니다.
