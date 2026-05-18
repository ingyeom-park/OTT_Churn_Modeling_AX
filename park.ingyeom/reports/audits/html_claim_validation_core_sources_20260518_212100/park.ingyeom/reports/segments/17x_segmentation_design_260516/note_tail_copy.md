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

## 2026-05-17 23:30:32 | 16x payment-included SHAP outputs deleted before rerun

- 기존 16x SHAP 산출물은 payment_is_mobile, payment_is_pc, payment_is_android, payment_is_ios가 포함된 expanded_feature_set 기준이었으므로 삭제했다.
- 삭제 대상은 active 16x notebook, interpretation output, hotfix output, figure output, review zip으로 제한했다.
- 06x, 07x, 10x, 11x, 12x, 14x, 15x 산출물은 수정하지 않았다.
- raw source CSV는 수정하지 않았다.
- 새 16x는 payment_is_* 4개를 제거한 기준으로 재실행한다.
- 삭제 로그: zip\16x_deleted_payment_included_outputs_260516.csv

## 2026-05-17 | 16x_SHAP_candidate_interpretation_260516 payment 제거 기준 재실행 승인 및 기록

사용자가 15x_payment_device_sensitivity_260516 결과를 확인한 뒤, `payment_is_mobile`, `payment_is_pc`, `payment_is_android`, `payment_is_ios` 네 개 payment 파생변수를 새 16x SHAP input에서 제거하는 방향을 승인했다. 이 승인은 payment_device 계열 전체를 인과적으로 나쁘다고 판단했다는 뜻이 아니라, 현재 프로젝트의 해석 안전선을 기준으로 볼 때 해당 변수들이 성능상 이득보다 해석 리스크가 더 크다고 판단한 것이다.

기존 16x_SHAP_candidate_interpretation_260516 산출물은 `expanded_feature_set` 기준으로 만들어졌고, 이 feature set에는 `payment_is_mobile`, `payment_is_pc`, `payment_is_android`, `payment_is_ios`가 포함되어 있었다. 따라서 기존 16x SHAP 결과는 사용자 승인 이후의 payment-device removal policy와 더 이상 정렬되지 않는다. 기존 16x의 SHAP global importance, family importance, direction summary, beeswarm, bar, dependence, scope comparison figure를 그대로 active 해석 기준으로 쓰면, 발표 또는 17x segmentation 설계에서 payment_device 계열을 실제 시청기기, 고객 성향, 또는 재구매 원인처럼 오해할 위험이 있다.

이 때문에 기존 16x active notebook, interpretation output, hotfix output, figure output, review zip은 active 해석 기준에서 제거하고, payment 제거 feature list 기준으로 16x를 다시 수행한다. 삭제 대상은 16x SHAP 관련 active 산출물로 제한한다. `06x_dataset_generation_260515`, `07x_feature_mapping_AARRR_260515`, `10x_feature_distribution_redundancy_pre_audit_260516`, `12x_model_family_comparison_260516`, `14x_lightweight_candidate_tuning_260516`, `15x_payment_device_sensitivity_260516` 산출물은 수정하지 않는다. raw source CSV, repo root, `_data`, `.tmp`, 다른 팀원 폴더도 수정하지 않는다.

payment_device 계열을 새 16x SHAP input에서 제거하는 이유는 다음과 같다. 첫째, `payment_device`는 시청기기가 아니라 결제기기 또는 결제환경에 가깝다. 둘째, 결제자와 실제 시청자가 다를 수 있으므로 결제기기 정보를 시청경험으로 직접 해석하면 안 된다. 셋째, iOS 결제 여부는 콘텐츠 선호, 시청 만족도, 재구매의 인과효과가 아니다. 넷째, 15x sensitivity에서 payment_is_* 4개 제거 시 성능 손실은 near-neutral 수준이었고, 일부 모델에서는 오히려 성능이 개선됐다. 다섯째, 이 변수들이 SHAP 또는 segmentation에서 상위로 나타날 경우 성능상 이득보다 해석 리스크가 더 크다.

새 16x는 15x에서 생성한 `expanded_no_payment_device` feature list를 기준으로 fitted candidate model explanation을 다시 수행한다. 제거 대상 feature는 `payment_is_mobile`, `payment_is_pc`, `payment_is_android`, `payment_is_ios` 네 개뿐이다. 이 네 개 외의 feature 제거, 새 feature 생성, feature selection decision, 모델 재튜닝, Optuna, segmentation은 이번 16x에서 수행하지 않는다. 06x canonical expanded dataset 원본도 수정하지 않는다.

SHAP 해석은 positive class `is_repurchase = 1`의 `repurchase_score` 기준 model explanation으로 제한한다. SHAP 값이 양수라는 것은 해당 fitted model의 출력에서 재구매 score를 높이는 방향으로 기여했다는 뜻이지, 해당 feature가 실제 재구매를 발생시킨 원인이라는 뜻이 아니다. churn_risk 관점으로 바꿔 말할 때도 SHAP 부호를 인과효과처럼 해석하지 않는다.

17x segmentation은 새 16x payment 제거 기준의 SHAP 결과를 참고하되, payment, auth, demographic proxy를 대표 segment rule로 직접 쓰지 않는다. `payment_is_*`, `is_user_verified`, `age_group`, gender 관련 변수는 필요한 경우 audit 또는 caveat로 관리한다. 세그먼트 대표 rule은 행동 기반 변수와 관측창 안의 사용 패턴을 우선해야 하며, payment/auth/demographic proxy를 고객군 이름이나 원인 설명으로 직접 쓰면 안 된다.

삭제 및 재실행 감사 파일은 새 16x interpretation folder의 `16x_deleted_payment_included_shap_manifest.csv`에 남긴다. 기존 삭제 대상이 이미 없었던 경우는 실패가 아니라 `already_missing`으로 기록한다.

## 2026-05-17 | 16x payment-removed SHAP rerun completion

새 16x_SHAP_candidate_interpretation_260516을 payment 제거 기준으로 재실행했다. 새 SHAP input에서는 `payment_is_mobile`, `payment_is_pc`, `payment_is_android`, `payment_is_ios` 네 개만 제거했고, 사용자 승인 없는 다른 feature 제거는 수행하지 않았다. 06x expanded dataset 원본, 07x mapping, 10x redundancy audit, 12x model comparison, 14x tuning, 15x sensitivity 산출물은 읽기 전용으로만 사용했다.

삭제 또는 already_missing으로 기록한 active 16x 대상은 notebook/16x_SHAP_candidate_interpretation_260516, reports/interpretation/16x_SHAP_candidate_interpretation_260516, reports/interpretation/16x_SHAP_candidate_interpretation_hotfix_260516, reports/figures/16x_SHAP_candidate_interpretation_260516, zip/16x_SHAP_candidate_interpretation_260516_review_package.zip, zip/16x_SHAP_candidate_interpretation_hotfix_260516_review_package.zip이다. 삭제 manifest는 새 interpretation folder의 `16x_deleted_payment_included_shap_manifest.csv`에 남겼다.

이번 16x는 SHAP 기반 model explanation 단계다. 최종 모델 확정, Optuna, segmentation, threshold 결정, campaign action, 일반 feature removal 단계가 아니다. SHAP 방향은 positive class `is_repurchase = 1`의 repurchase_score 기준으로 해석하며, churn_risk 관점으로 바꾸어 말하더라도 인과효과처럼 쓰지 않는다.

17x segmentation에서는 이번 payment 제거 기준 16x를 참고하되, payment/auth/demographic proxy를 대표 rule로 직접 쓰지 않는다. 해당 변수들은 audit/caveat로 관리한다.

## 2026-05-17 | 16x payment-removed retry hard gate completion

직전 16x retry는 payment_is_*가 SHAP input에 남아 실패한 것으로 기록하고, 기존 active 16x notebook, interpretation output, figure output, review zip을 삭제 또는 already_missing으로 정리했다. 삭제 감사는 `16x_deleted_failed_payment_not_removed_manifest.csv`에 남겼다.

이번 retry는 15x의 `expanded_no_payment_device` feature list를 기준으로 SHAP input을 다시 구성했다. `payment_is_mobile`, `payment_is_pc`, `payment_is_android`, `payment_is_ios` 네 개는 SHAP input에서 제거했다. expected feature count는 `overall_with_promotion = 76`, `overall_without_promotion = 75`, `promotion_only = 75`, `nonpromotion_only = 75`이며, 이 조건은 `16x_payment_removed_input_gate.csv`에서 SHAP 계산 전에 검증했다.

payment_device는 시청기기가 아니라 결제기기 또는 결제환경 proxy다. 결제자와 실제 시청자가 다를 수 있으며, iOS 결제 여부는 재구매 또는 이탈의 인과효과가 아니다. SHAP은 fitted candidate model의 repurchase_score 설명이지 원인 설명이 아니다.

이번 retry는 SHAP 재실행 단계이며 모델 재튜닝, Optuna, segmentation, feature selection, 일반 feature removal 단계가 아니다. 17x segmentation에서는 payment/auth/demographic proxy를 대표 rule로 직접 쓰지 말고 audit/caveat로만 관리한다.

## 2026-05-18 | 17x_segmentation_design_260516 completion

17x_segmentation_design_260516을 수행했다. 이번 17x는 segmentation design 단계이며 모델링, Optuna, SHAP 재계산, feature removal, campaign final threshold 결정 단계가 아니다.

score source는 15x `15x_oof_predictions.csv`에서 `feature_set_variant == expanded_no_payment_device`, `dataset_scope == overall_with_promotion`, `model_name == LightGBM` 조건으로 필터링한 OOF score를 primary로 사용했다. 이 선택은 16x payment-removed SHAP candidate plan이 LightGBM 기준으로 수행되었기 때문에 segmentation score와 SHAP evidence의 모델 기준을 맞추기 위한 것이다. 최종 모델 확정이라는 뜻은 아니다.

`churn_risk = 1 - repurchase_score` 관계를 검증했고, top-k risk는 `churn_risk` 내림차순 기준으로 사용했다. 16x payment-removed SHAP은 segment rule feature와 연결하는 evidence로만 사용했으며 SHAP은 인과가 아니라 fitted model explanation이다.

대표 segment rule에는 `payment_is_*`, payment_device, age_group, gender/is_female/is_male, is_user_verified를 사용하지 않았다. `flag_age40_unverified_ios`는 audit only로 생성했고 representative segment assignment에는 사용하지 않았다. representative segment name은 provisional label이며 사용자 승인 전 final segment가 아니다.

이번 산출물은 row-level/subscription-event-level 분석이다. row count를 고객 수 또는 unique customer 수로 표현하면 안 된다.

생성 산출물: 17x_preflight_input_validation.csv, 17x_score_source_selection.csv, 17x_segmentation_base_datamart.csv, 17x_threshold_audit.csv, 17x_internal_multiflag_definitions.csv, 17x_internal_multiflag_assignment.csv, 17x_representative_segment_rules.csv, 17x_representative_segment_assignment.csv, 17x_segment_summary.csv, 17x_segment_feature_profile.csv, 17x_segment_SHAP_evidence_link.csv, 17x_proxy_artifact_audit.csv, 17x_age40_unverified_ios_audit.csv, 17x_business_action_candidates.csv, 17x_dashboard_handoff_datamart.csv, 17x_safe_unsafe_wording.csv, 17x_open_risks.csv, 17x_source_fingerprint_before_after.csv, 17x_final_checks.csv, README.md, note_tail_copy.md, 17x_execution_log.txt, 17x_review_zip_inventory.csv, review zip.

미해결 리스크: threshold와 segment label은 provisional이고, payment/auth/demographic proxy는 audit만 가능하다. OOF score는 final campaign 확정 기준이 아니며, genre/content는 mapping proxy다. 다음 단계에서는 17x 산출물을 기준으로 발표 또는 dashboard handoff 문구를 안전 표현으로만 정리해야 한다.

17x final_checks 결과는 `38 PASS / 0 WARN / 0 FAIL`이다. 핵심 검증에서 `row_count_23079`, `churn_risk_equals_1_minus_repurchase_score`, `one_representative_segment_per_row`, `no_payment_feature_used_in_representative_rule`, `no_auth_feature_used_in_representative_rule`, `no_demographic_feature_used_in_representative_rule`, `flag_age40_unverified_ios_audit_only`, `raw_source_csv_not_modified`, `review_zip_created`가 PASS로 확인되었다. review zip은 `zip/17x_segmentation_design_260516_review_package.zip`에 생성했다.

