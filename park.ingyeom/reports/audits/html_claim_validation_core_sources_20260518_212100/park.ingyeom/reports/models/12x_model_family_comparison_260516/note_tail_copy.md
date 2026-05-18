> 이후 1주차에서 3주차까지 사용이 유지되는지, 특히 3주차 watch time, session, recency가 살아 있는지가 Retention 단계의 핵심 신호다.  
> 이 Retention 신호는 다음 달 재결제 여부인 Revenue proxy와 연결될 수 있다.  
> Referral은 현재 데이터에서 직접 관측되지 않지만, 모바일 친화적 고객군과 프로모션 참여 고객을 활용한 친구 추천 100원딜 쿠폰 실험으로 설계할 수 있다.  
> 단, Referral 효과는 본 프로젝트에서 입증하지 않고, 실제 OTT사가 실행할 경우 검증해야 할 후속 실험 제안으로 둔다.

---

### 11. 금지 표현과 안전 표현

#### Activation 관련

금지 표현:

- 전체 구독기간 중 한 번이라도 봤으면 Activation이다.
- 3~4주차에 처음 본 사람도 모델의 Activation feature에 포함한다.
- day21 이후 첫 시청도 feature로 사용한다.

안전 표현:

- 본 프로젝트의 Activation은 day0~20 안에서 관측된 첫 시청이다.
- day21 이후 처음 시청한 고객은 서비스 전체 관점에서는 Activation 고객일 수 있으나, day21 scoring point 기준으로는 Activation 미관측 고객이다.
- day21 이후 첫 시청은 모델 feature가 아니라 대응기간 마케팅 액션의 결과 또는 후보로만 해석한다.

#### Referral 관련

금지 표현:

- Referral 효과를 검증했다.
- 친구 추천 쿠폰이 재구매율을 올린다.
- 20대는 반드시 공유한다.
- 본인인증 때문에 어뷰징은 불가능하다.

안전 표현:

- Referral은 현재 데이터로 직접 관측되지 않는다.
- Referral은 후속 실험 제안이다.
- 외부 자료를 통해 모바일 친화 고객군의 공유 성향을 보강할 수 있다.
- 본인인증 조건은 단순 다계정 어뷰징 위험을 제한할 수 있으나, 실제 운영에서는 중복 방지 정책이 필요하다.
- 본 프로젝트에서는 Referral 효과를 입증하지 않고, 실제 실행 시 확인해야 할 KPI를 제안한다.

#### App Store / default demographic artifact 관련

금지 표현:

- 40대 고객이 많아서 그렇다.
- 성별 N 고객은 이탈한다.
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
