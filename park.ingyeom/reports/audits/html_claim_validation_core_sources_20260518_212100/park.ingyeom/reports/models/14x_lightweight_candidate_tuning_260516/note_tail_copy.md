- iOS 결제 고객은 이탈한다.
- 미인증 고객은 충성도가 낮다.

안전 표현:

- `payment_is_ios`, `is_user_verified`, `age_group`, 성별 관련 변수는 실제 인구통계라기보다 결제 경로와 본인인증 정책에서 발생한 데이터 생성 구조를 반영했을 가능성이 있다.
- App Store 경유 결제와 본인인증 미수행 계정에서 default-like demographic artifact가 발생했을 수 있다.
- 이 변수들은 structural proxy risk로 관리하며, 고객 특성으로 직접 해석하지 않는다.

---

### 12. 향후 단계 반영사항

10x feature distribution / redundancy / group-proxy pre-audit에서 반드시 반영할 것:

- Activation은 day0~20 기준으로만 해석한다.
- day21 이후 첫 시청은 feature가 아니라 대응기간 activation 유도 후보로만 다룬다.
- `payment_is_ios`, `is_user_verified`, `age_group`, 성별 관련 변수는 structural proxy risk로 별도 관리한다.
- near-constant / group-proxy / default demographic artifact 가능성을 감사한다.
- 이 변수들을 제거하지 말고, 11x modeling preflight로 넘긴다.
- feature 제거 여부는 사용자 승인 전까지 결정하지 않는다.

11x / 12x 모델링에서 반드시 반영할 것:

- expanded feature set에 이 변수들이 포함되더라도 actual model input feature list를 반드시 저장하고 검수한다.
- context/profile/payment 계열이 성능을 과도하게 끌어올리는지 확인한다.
- usage/retention 계열만으로도 설명력이 유지되는지 확인한다.
- `payment_is_ios`, `is_user_verified`, `age_group`, 성별 관련 변수의 scope별 민감도를 확인한다.
- SHAP에서 이 변수들이 상위에 올라오면 고객 특성이 아니라 structural proxy caveat와 함께 해석한다.

Segmentation에서 반드시 반영할 것:

- segment 이름을 먼저 붙이지 않는다.
- 기준식과 분포 확인이 먼저다.
- `40대 미인증 iOS 고객군` 같은 이름은 금지한다.
- 필요하면 `App Store 경유 / 인증정보 결측 가능 계정군`처럼 데이터 생성 구조 중심으로 표현한다.
- final segment는 사용자 승인 전까지 provisional로 둔다.

---

### 최종 판단

현재 AARRR 프레임은 유지 가능하다.  
다만 각 단계는 반드시 본 프로젝트의 관측창과 데이터 한계를 반영해 재정의해야 한다.

가장 중요한 보정은 다음이다.

> Activation은 전체 구독기간 기준이 아니라 day0~20 관측창 기준이다.  
> 3~4주차에 처음 시청한 고객은 서비스 전체 관점에서는 activation 고객일 수 있지만, 본 프로젝트의 scoring point에서는 activation 미관측 고객이다.  
> Referral은 현재 데이터로 검증된 결과가 아니라 후속 실험 제안이다.  
> App Store 결제 / 본인인증 / default demographic artifact 가능성은 AARRR, 모델링, SHAP, segmentation 전 과정에서 caveat로 관리해야 한다.

이 원칙을 지키면 AARRR은 단순한 발표용 프레임이 아니라, 데이터 관측 가능성과 비즈니스 제언을 연결하는 안전한 구조로 사용할 수 있다.

## 2026-05-16 10x_feature_distribution_redundancy_pre_audit_260516_hotfix
- 10x hotfix 수행.
- `10x_final_checks.csv`와 실제 notebook artifact 상태의 불일치 가능성을 보정했고, executed notebook visible outputs 저장 상태를 확인했다.
- `10x_feature_distribution_redundancy_pre_audit_260516_executed.ipynb`를 저장했다.
- review zip duplicate entry를 제거한 hotfix review package를 새로 생성했다.
- `age_group`은 단순 near-constant가 아니라 default-demographic artifact / group-proxy risk로 관리한다.
- high-VIF feature는 자동 제거하지 않는다.
- expanded_full 80개 feature는 보존한다.
- redundancy-aware sensitivity는 11x에서 별도 비교 후보로만 관리한다.
- feature 제거는 사용자 승인 필요 상태로 유지한다.
- 다음 단계는 11x modeling preflight / baseline growth comparison이다.

## 2026-05-16 11x_baseline_growth_comparison_260516
- 11x 수행.
- 기존 11/11b notebook은 archive에서 발견했고, 11b 복사본을 새 11x notebook 위치에 둔 뒤 현재 목적에 맞는 baseline comparison notebook으로 수정했다.
- 06x/07x/10x canonical chain 기준 입력을 사용했다.
- conservative_safe_22와 expanded_feature_set을 4개 scope에서 같은 StratifiedGroupKFold 정책으로 비교했다.
- feature 제거 없음.
- VIF/redundancy는 해석 주의 및 후속 sensitivity 후보로만 기록했다.
- 모델링 결과는 baseline comparison이며 최종 모델이 아니다.
- 다음 단계는 12x model family comparison이다.

## 2026-05-16 12x_model_family_comparison_260516
- 12x 수행.
- 기존 12/12c notebook은 archive에서 발견했고, 12c 복사본을 새 12x notebook 위치에 둔 뒤 현재 목적에 맞는 model family comparison notebook으로 수정했다.
- 06x/07x/10x/11x canonical chain 기준 입력을 사용했다.
- conservative_safe_22 vs expanded_feature_set model family comparison을 수행했다.
- feature 제거 없음.
- VIF/redundancy는 해석 주의 및 후속 sensitivity 후보로만 기록했다.
- 모델링 결과는 candidate comparison이며 최종 모델이 아니다.
- 다음 단계는 14x 또는 16x 후보 결정이다.


## 2026-05-16 12:47:24 | 12x_model_family_comparison_260516 deletion before CatBoost rerun

- 기존 12x 결과는 CatBoost import unavailable 상태에서 생성되어 삭제했다.
- 삭제 대상은 12x notebook, 12x reports/models output, 12x figures output, 12x review zip/temp zip으로 제한했다.
- raw source CSV, 06x, 07x, 10x, 11x 산출물은 수정하지 않았다.
- CatBoost 설치 후 12x_model_family_comparison_260516을 다시 실행한다.
- 삭제 로그: zip\12x_deleted_for_catboost_rerun_260516.csv

## 14x_lightweight_candidate_tuning_260516
- 수행 시각: 2026-05-16T14:45:30
- 12x 후보 기반 경량 Optuna tuning을 수행했다. 최종 모델 확정, SHAP, segmentation, feature removal 단계가 아니다.
- n_trials_per_model_scope=30, timeout_per_model_scope_seconds=900, CV=StratifiedGroupKFold(n_splits=5, group=USER_KEY).
- 튜닝 대상 model/scope:
  - conservative_safe_22 / nonpromotion_only / RandomForest
  - conservative_safe_22 / nonpromotion_only / HistGradientBoosting
  - conservative_safe_22 / overall_with_promotion / LightGBM
  - conservative_safe_22 / overall_with_promotion / CatBoost
  - conservative_safe_22 / overall_without_promotion / LightGBM
  - conservative_safe_22 / overall_without_promotion / CatBoost
  - conservative_safe_22 / promotion_only / LightGBM
  - conservative_safe_22 / promotion_only / HistGradientBoosting
  - expanded_feature_set / nonpromotion_only / LightGBM
  - expanded_feature_set / nonpromotion_only / HistGradientBoosting
  - expanded_feature_set / overall_with_promotion / LightGBM
  - expanded_feature_set / overall_with_promotion / CatBoost
  - expanded_feature_set / overall_without_promotion / LightGBM
  - expanded_feature_set / overall_without_promotion / HistGradientBoosting
  - expanded_feature_set / promotion_only / LightGBM
  - expanded_feature_set / promotion_only / HistGradientBoosting
- 12x 대비 AUC 양수 delta 조합 수: 15/16. 세부 값은 14x_vs_12x_comparison.csv 기준이다.
- VIF/redundancy가 높아도 피처 제거를 수행하지 않았고, feature selection decision도 내리지 않았다.
- use_for_final_model은 기본 no로 유지했다.
- 다음 단계 후보는 16x SHAP / interpretation 검토다.
