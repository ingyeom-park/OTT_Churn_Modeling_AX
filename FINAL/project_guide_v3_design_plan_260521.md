# project_guide_v3 설계안 260521

> 문서 목적  
> 이 문서는 `project_guide_v3.html`을 만들기 전의 설계도다. 새 대화 또는 새 Codex 세션이 이 문서만 읽어도 현재 프로젝트의 기준, 금지선, 근거 파일, HTML 구성, 검수 방법을 이해할 수 있어야 한다.

---

# 0. Evidence pack 검수 결과

이번 설계안은 사용자가 전달한 `project_guide_v3_evidence_pack_260521_review_package.zip`을 실제로 열어 확인한 뒤 작성한다.

확인한 ZIP 내부 산출물은 다음 15개다.

- `dataset_lineage_summary.csv`
- `preprocessing_policy_summary.md`
- `column_feature_contract_summary.csv`
- `derived_feature_lineage.md`
- `AARRR_design_summary.md`
- `AARRR_feature_mapping_table.csv`
- `stage_07_to_18_timeline.csv`
- `model_and_score_source_summary.md`
- `segmentation_basis_summary.md`
- `guide_v3_required_content_checklist.csv`
- `unanswered_questions_for_chatgpt.md`
- `README.md`
- `final_checks.csv`
- `source_fingerprint_before_after.csv`
- `review_zip_inventory.csv`

`final_checks.csv`는 18개 항목 전부 PASS였다. `source_fingerprint_before_after.csv`도 읽은 핵심 파일들이 수정되지 않았다고 기록한다. 단, ZIP 크기 수치에는 self-reference packaging 때문에 실제 업로드 ZIP 크기와 final_checks의 `zip_size` 숫자가 약간 다를 수 있다. 이는 내용상 blocking issue가 아니라 패키징 self-reference limitation으로 취급한다.

---

# 1. 현재 최종 방향

현재 최종 방향은 다음과 같다.

> 계산 기준은 `park.ingyeom`이다.  
> PUBLIC은 final pipeline이 아니라 100원딜 중심 해석을 실험한 reference branch다.  
> 세그먼트 rule과 assignment는 바꾸지 않는다.  
> 발표용 label, action tier, 100원딜 narrative, age/gender personalization layer를 보강한다.  
> 지금부터는 새 모델링, 새 SHAP, 새 segmentation이 아니라 최종 guide와 발표 문서화 단계다.

이 방향은 `FINAL/final_note.md`, `project_execution_plan_260521.md`, 그리고 이번 evidence pack의 내용과 일치해야 한다.

---

# 2. project_guide_v3의 역할

`project_guide_v3.html`은 단순 발표용 예쁜 페이지가 아니다. 다음 네 가지 역할을 동시에 해야 한다.

## 2.1 프로젝트 인수인계서

처음 보는 사람이 데이터셋이 어디서 시작했고, 어떤 row가 제외됐고, 어떤 feature set이 만들어졌고, 어떤 모델/score source를 기준으로 세그먼트를 만들었는지 이해할 수 있어야 한다.

## 2.2 발표용 설명서

멘토나 팀원에게 “그래서 이 프로젝트가 무엇을 했고, 왜 100원딜 분석인가?”를 설명할 수 있어야 한다.

## 2.3 분석 방어 문서

다음 질문에 방어 가능해야 한다.

- 왜 PUBLIC을 최종 기준으로 쓰지 않았는가?
- 왜 100원딜을 segment rule에 직접 넣지 않았는가?
- 왜 payment-device 계열을 해석 기준에서 제거했는가?
- 왜 `general_observation`과 `content_preference_target_candidate`를 버리지 않고 역할 재분류했는가?
- 왜 세그먼트가 최종 캠페인 타겟이 아니라 개입 우선순위 후보군인가?

## 2.4 Codex 구현 기준서

Codex가 HTML을 만들 때 판단하지 않도록, 섹션 구성, 사용할 수치, 금지 표현, 표 구성, 검수 조건이 명확해야 한다.

---

# 3. 근거 등급 체계

`project_guide_v3` 안의 모든 주요 주장은 아래 등급 중 하나로 관리한다.

| 등급 | 의미 | 예시 |
|---|---|---|
| 확인됨 | evidence pack의 CSV/MD 또는 기존 검수 ZIP에서 확인된 내용 | primary main cohort 23,079 rows |
| 사용자 확인 | 사용자가 대화에서 직접 확정한 내용 | payment-device 계열은 제거 방향이 맞음 |
| 해석 | 확인된 근거를 바탕으로 ChatGPT가 정리한 판단 | PUBLIC은 final pipeline이 아니라 reference branch |
| 제안 | 최종 승인 전 presentation/action 후보 | 20대에게 친구추천 쿠폰 메시지 제안 |
| 금지 | 사용하면 안 되는 표현 또는 방향 | 100원딜이 이탈을 유발했다 |
| Codex 확인 필요 | 로컬 파일 재확인이 필요한 항목 | project_guide_v2의 정확한 최신 위치 |

HTML에는 모든 등급을 노출할 필요는 없지만, 설계와 검수에서는 반드시 구분한다.

---

# 4. 데이터셋 lineage 설계

## 4.1 HTML 섹션 목적

사용자가 어떤 데이터를 받았고, 어떤 기준으로 최종 분석 row가 확정됐는지 보여준다. 여기서 핵심은 “우리는 23,343개 원천 row를 그대로 쓴 것이 아니라, day0~20 관측창을 만족하는 row-level / subscription-event-level cohort를 만들었다”는 점이다.

## 4.2 guide v3에 반드시 들어갈 수치

| 단계 | 입력 row | 출력 row | 핵심 정책 |
|---|---:|---:|---|
| raw master profile | - | 23,343 | 원천 광일 master. USER_KEY 중복 가능. unique customer 수로 말하지 않음 |
| duration filter | 23,343 | 23,105 | duration < 21인 238행 제외. day0~20 관측창을 완성할 수 없기 때문 |
| exact full duplicate filter | 23,105 | 23,079 | duration filter 이후 exact full duplicate extra row 26행 제외 |
| primary main cohort | 23,105 | 23,079 | 최종 row-level / subscription-event-level 분석 기준 |
| conservative dataset | 23,079 | 23,079 | conservative_safe_22 feature set + USER_KEY + target |
| expanded dataset | 23,079 | 23,079 | expanded_feature_set 80 model features + keys/target |
| expanded_no_payment_device | 23,079 | 23,079 | payment_is_* 4개를 runtime feature matrix에서 제외한 76 feature 기준 |

## 4.3 반드시 들어갈 설명

- 원천 master는 23,343 rows, 91 columns다.
- duration < 21 row는 day0~20 관측창을 완성할 수 없으므로 제외했다.
- exact full duplicate extra row는 duration filter 이후 26행을 제외했다.
- USER_KEY 중복이 있으므로 row count를 unique customer count로 말하지 않는다.
- 최종 분석 단위는 row-level / subscription-event-level이다.
- 최종 primary main cohort는 23,079 rows다.

## 4.4 금지 표현

- “23,079명의 고객”
- “완전히 유저 단위 분석”
- “duration < 21은 이탈했기 때문에 제외했다”
- “중복 USER_KEY는 모두 제거했다”

정확한 표현은 다음이다.

> 최종 분석 단위는 고객 개인 단위가 아니라 구독 이벤트 row 단위다. duration < 21 row는 1~3주차 관측창을 완성할 수 없으므로 primary main cohort에서 제외했다.

---

# 5. 전처리 정책 설계

## 5.1 HTML 섹션 목적

전처리가 단순 cleaning이 아니라 모델링 시간축을 지키기 위한 정책이었다는 점을 설명한다.

## 5.2 핵심 정책

- day0은 `reg_date` 기준 가입 시작일이다.
- day0~20은 모델 feature와 행동 신호를 관측하는 기간이다.
- day21 이후는 리텐션 대응기간이다.
- day21 이후 행동은 feature로 쓰지 않는다.
- target은 `is_repurchase`다.
- 모델은 `repurchase_score = P(is_repurchase=1)`를 출력하고, 비즈니스 해석에서는 `churn_risk = 1 - repurchase_score`로 변환한다.

## 5.3 영어/변수명 풀이

- `duration`: 구독기간 또는 관측 가능한 기간. 이 프로젝트에서는 21일 미만이면 day0~20 관측창을 완성하지 못함.
- `row-level`: 행 단위.
- `subscription-event-level`: 구독 이벤트 단위. 한 고객이 여러 subscription-event row를 가질 수 있음.
- `is_repurchase`: 다음 달 재구매 여부. 1이면 재구매, 0이면 미재구매.
- `repurchase_score`: 모델이 예측한 재구매 가능성.
- `churn_risk`: 이탈 위험 점수. `1 - repurchase_score`.

---

# 6. feature contract 설계

## 6.1 HTML 섹션 목적

91개 원천 컬럼이 어떻게 모델 feature, target, group key, split key, audit-only, action layer로 정리됐는지 보여준다.

## 6.2 반드시 들어갈 핵심 컬럼

| 컬럼 | 최종 역할 | guide v3 설명 |
|---|---|---|
| USER_KEY | group key / audit-only | 모델 feature 아님. USER_KEY 중복 때문에 unique user 분석이라고 말하지 않음 |
| is_repurchase | target | positive class는 재구매. churn_risk는 여기서 변환됨 |
| is_promotion | Acquisition context / split variable | 100원딜 맥락. 인과 효과 아님 |
| payment_is_mobile / pc / android / ios | excluded from expanded_no_payment_device | 결제기기 proxy. 시청기기 아님. 최종 해석 기준에서 제외 |
| is_churn_prevented | historical churn prevention context | 과거 churn prevention 이력. current-cycle 사후효과처럼 말하지 않음 |
| age_group | demographic context / action layer | 원인이 아니라 메시지 조정 layer |
| is_female / is_male | demographic context / action layer | 원인이 아니라 메시지 조정 layer |
| is_user_verified | profile context | 모델 feature에는 남을 수 있으나 원인처럼 해석 금지 |
| is_cold_start_3d_fixed / 7d_fixed | Activation | row-level first watch timing 기준 fixed cold_start |
| retention_w2_ratio / retention_w3_ratio | Retention | 1~3주차 사용 유지/감소 신호 |
| watch_time_min_w1/w2/w3 | Activation / Retention | 주차별 시청시간 |
| watch_session_w1/w2/w3 | Activation / Retention | 주차별 시청 세션 |
| recency | Retention | day0~20 안에서의 최근성. day21+ 아님 |
| genre/content ratio 계열 | Retention_context / content proxy | 콘텐츠 선호 직접 증명 아님. Movie_Master mapping proxy |

## 6.3 설계 원칙

- feature를 넣었다고 해서 원인으로 해석하지 않는다.
- demographic은 segment rule이 아니라 action personalization layer다.
- payment-device는 최종 해석 기준에서 제외한다.
- content/genre feature는 proxy다.

---

# 7. derived feature lineage 설계

## 7.1 HTML 섹션 목적

원래 컬럼이 어떻게 파생변수로 변환됐는지, 그리고 그 파생변수를 어떻게 해석해야 하는지 설명한다.

## 7.2 반드시 설명할 파생변수

| 파생변수 | 뜻 | 사용 위치 | caveat |
|---|---|---|---|
| is_basic | basic plan 여부 | expanded feature | plan/product proxy. 선호도 아님 |
| is_cold_start_3d_fixed | 가입 후 첫 3일 안 첫 시청 여부 | Activation | original cold_start가 아니라 row-level fixed version |
| is_cold_start_7d_fixed | 가입 후 7일 안 첫 시청 여부 | Activation | day0~6 기준 |
| age_group | 나이대 bucket | action personalization | 이탈 원인 아님 |
| is_female / is_male | 성별 flag | action personalization | 원인 아님 |
| payment_is_* | 결제기기 one-hot | 최종 해석 기준 제외 | 시청기기 아님 |
| reg_hour_* / reg_is_weekend | 가입 시간대/주말 여부 | context feature | 의도 직접 증명 아님 |
| retention_w2_ratio / w3_ratio | 사용 유지 비율 | Retention | 저활동 row에서 불안정 가능 |
| diff_between_w* | 주차 간 사용량 차이 | Retention | 감소의 인과 아님. 관측 신호 |
| watch_ratio_under_1m / 5m | 짧은 시청 비율 | expanded feature | 탐색/중단/짧은 콘텐츠 가능성 |
| genre ratio | 장르별 시청 비중 | content proxy | Movie_Master mapping proxy |
| new/old movie ratio | 신작/구작 비중 | content proxy | release 기준 caveat |
| recency / inactive gap | 최근 시청/비활성 gap | Retention | day0~20 안에서만 해석 |
| only_w1 / w2 / w3 | 특정 주차에만 시청 | Activation/Retention | 행동 신호이지 원인 아님 |

---

# 8. AARRR 설계

## 8.1 AARRR을 반드시 넣는 이유

AARRR은 이 프로젝트를 단순 모델링 결과가 아니라 마케팅/비즈니스 프레임으로 설명하기 위한 구조다. 모델 성능만 말하면 “그래서 어떤 고객에게 무엇을 해야 하는가?”를 설명하기 어렵다. 따라서 feature와 행동 신호를 Acquisition, Activation, Retention, Revenue, Referral로 묶어 설명한다.

## 8.2 Acquisition

정의:

> 가입 또는 유입 맥락. 이 프로젝트에서는 100원딜 여부인 `is_promotion=1`이 핵심 Acquisition context다.

주요 feature:

- `is_promotion`
- `is_basic`, `is_premium`, `is_standard`
- registration time flags
- payment-device 계열은 원래 Acquisition context였으나 최종 해석 기준에서는 제거 또는 caveat 처리

해석:

> 100원딜은 가입 장벽을 극단적으로 낮춘 유입 장치다. 다만 이것을 이탈의 원인으로 말하지 않는다.

## 8.3 Activation

정의:

> 가입 직후 실제 이용이 시작되는가. 본 프로젝트에서는 day0~20 관측창 안, 특히 day0~6 초기 시청과 cold-start fixed가 핵심이다.

주요 feature:

- `is_cold_start_3d_fixed`
- `is_cold_start_7d_fixed`
- `watch_time_min_w1`
- `watch_session_w1`
- `is_only_w1`
- `is_w1_over_50pct`

주의:

> day21 이후 처음 시청한 사람은 서비스 전체 관점에서는 activation일 수 있으나, 본 프로젝트의 scoring point에서는 activation 미관측 고객이다. day21 이후 행동은 feature로 사용하지 않는다.

## 8.4 Retention

정의:

> 1~3주차 동안 사용이 유지되는가. 특히 2~3주차와 3주차 시청 유지/감소가 핵심이다.

주요 feature:

- `watch_time_min_w2`, `watch_time_min_w3`
- `watch_session_w2`, `watch_session_w3`
- `retention_w2_ratio`, `retention_w3_ratio`
- `diff_between_w2_w1`, `diff_between_w3_w2`, `diff_between_w3_w1`
- `recency`, `max_inactive_gap_days`
- `is_only_w2`, `is_only_w3`
- `active_ratio`, gap 계열

해석:

> 3주차 시청 감소는 이탈 원인이 아니라 이탈 위험과 함께 관찰되는 행동 신호다.

## 8.5 Revenue

정의:

> 실제 매출액이 아니라 다음 달 재구매 여부인 `is_repurchase`를 Revenue proxy로 사용한다.

주의:

- 매출액, ARPU, LTV를 직접 분석한 것이 아니다.
- `is_repurchase`는 target이다.
- target을 segment rule에 직접 넣지 않는다.

## 8.6 Referral

정의:

> 추천, 친구초대, 공유, 바이럴 확산.

현재 상태:

> 현재 데이터에는 referral 행동 로그가 없으므로 분석 결과가 아니라 후속 실험 제안으로만 다룬다.

제안:

- 20대/30대 100원딜 고객에게 친구추천 100원딜 쿠폰 실험 제안 가능
- 단, 현재 데이터로 효과를 검증한 것이 아니므로 A/B test 또는 후속 캠페인으로 확인해야 함

---

# 9. stage 07~18 pipeline 설계

## 9.1 HTML 섹션 목적

07x부터 18x까지 단계가 너무 많으므로, 각 단계가 무엇을 했고 무엇을 하지 않았는지 한 줄 timeline으로 보여준다.

| 단계 | 목적 | 수행한 것 | 수행하지 않은 것 | guide v3 relevance |
|---|---|---|---|---|
| 07x | AARRR feature mapping | 06x feature를 AARRR stage와 caveat로 매핑 | 모델링, SHAP, segmentation | feature 설명 근거 |
| 08x | promotion vs nonpromotion EDA | 100원딜/비100원딜 관찰 비교 | 인과 주장, 모델링 | 100원딜 narrative caveat |
| 09x | promotion x repurchase 2x2 EDA | 2x2 집단 기술통계 | causal claim | target/scope 설명 |
| 10x | feature distribution / redundancy pre-audit | 분포, 중복, VIF, proxy risk 점검 | feature 제거 | feature caveat |
| 11x | baseline growth comparison | conservative vs expanded baseline 비교 | final model 확정 | baseline story |
| 12x | model family comparison | 모델군 비교 | final campaign model 확정 | CatBoost/LightGBM 맥락 |
| 14x | lightweight tuning | 후보 경량 tuning | 최종 모델 확정 | tuning reference |
| 15x | payment-device sensitivity | payment_is_* 제거 민감도 | canonical 전체 재생성 | payment 제거 근거 |
| 16x | payment-removed SHAP | payment 제거 기준 model explanation | 인과 증명 | XAI 설명 근거 |
| 17x | segmentation | OOF churn_risk와 행동 flag로 대표 segment 배정 | 캠페인 확정 | segment cards |
| 18x | business storyline / FINAL patches | 발표 안전 문구와 action layer 정리 | 새 분석 | 최종 guide story |

---

# 10. model and score source 설계

## 10.1 최종 기준

`LightGBM / expanded_no_payment_device / overall_with_promotion / OOF churn_risk`

## 10.2 왜 LightGBM인가

- 17x의 primary score source다.
- 16x payment-removed SHAP candidate plan과 기준이 맞다.
- payment-device 제거 이후의 해석 기준과 연결된다.
- CatBoost가 강하더라도 17x assignment와 16x explanation basis를 바꾸지 않는다.
- PUBLIC GB는 reference branch 산출물이므로 final score source로 쓰지 않는다.

## 10.3 반드시 들어갈 제한

> 이 score source는 최종 운영 모델 확정이 아니라 17x segmentation을 위한 기준 score source다.

---

# 11. segmentation 설계

## 11.1 HTML 섹션 목적

7개 segment를 단순 나열하지 않고, 4개 action tier로 재배치한다.

## 11.2 7개 segment 요약

| 순위 | segment_id | rows | churn_rate | mean_churn_risk | promo1_share | 역할 |
|---:|---|---:|---:|---:|---:|---|
| 1 | high_risk_week3_inactive_or_drop | 3,793 | 0.732 | 0.733 | 0.590 | 즉시 개입 우선군 |
| 2 | high_risk_only_w1_or_cold_start_weak | 265 | 0.717 | 0.698 | 0.706 | 즉시 개입 우선군 |
| 3 | high_risk_low_activity | 511 | 0.814 | 0.765 | 0.609 | 즉시 개입 우선군 |
| 4 | medium_risk_retention_decay | 3,195 | 0.388 | 0.358 | 0.546 | 관찰 강화군 |
| 5 | content_preference_target_candidate | 6,195 | 0.101 | 0.095 | 0.485 | 정가 전환 강화군 |
| 6 | stable_retained_user | 1,224 | 0.011 | 0.017 | 0.342 | 안정 유지군 |
| 7 | general_observation | 7,896 | 0.159 | 0.169 | 0.506 | 모니터링 / 추가분해 후보군 |

## 11.3 발표용 label 제안

| 내부 segment_id | 발표용 label | 설명 |
|---|---|---|
| high_risk_week3_inactive_or_drop | 3주차 이탈 임박 고위험군 | 3주차 비활성/감소 신호가 있는 고위험군 |
| high_risk_only_w1_or_cold_start_weak | 초기 활성화 약화 고위험군 | 1주차 집중 또는 cold-start 약화 신호 |
| high_risk_low_activity | 저활동 고위험군 | 전반적 활동량이 낮고 churn_risk가 높음 |
| medium_risk_retention_decay | 관심 감소 관찰군 | 사용 유지가 약해지는 중간위험군 |
| content_preference_target_candidate | 콘텐츠 큐레이션 기반 정가 전환 강화군 | 이탈 방어보다 콘텐츠 추천과 가치 상기 대상 |
| stable_retained_user | 안정 재구매 가능군 | 안정적 이용/낮은 churn_risk |
| general_observation | 추가 관찰 필요 잔여군 | 명확한 대표 rule에 걸리지 않은 monitoring group |

## 11.4 important caveat

- 세그먼트 rule과 assignment는 변경하지 않는다.
- presentation label만 바꾼다.
- 100원딜은 segment rule이 아니라 context/action layer에서 살린다.
- `general_observation`과 `content_preference_target_candidate`는 버리는 것이 아니라 역할 재분류한다.

---

# 12. 100원딜 narrative 설계

## 12.1 guide v3 핵심 문장

> 100원딜은 가입 장벽을 극단적으로 낮춘 유입 장치다. 따라서 정가 가입자보다 이용 동기와 지불 의향이 이질적인 고객이 함께 유입될 가능성이 크다. 이 때문에 100원딜 고객은 가입 자체보다 가입 이후 1~3주차에 실제 이용 습관으로 전환되는지가 핵심이며, 특히 3주차 이용 유지 여부는 정가 전환 실패 위험을 설명하는 중요한 행동 신호로 볼 수 있다.

## 12.2 금지 문장

- 100원딜이 이탈을 유발했다.
- 100원딜 고객은 어차피 이탈한다.
- 100원딜 때문에 충성도가 낮다.

## 12.3 허용 문장

- 100원딜은 가입 장벽을 낮춘다.
- 100원딜 고객은 이용 동기와 지불 의향이 이질적일 수 있다.
- 100원딜 고객에게 중요한 것은 가입 이후 이용 습관 전환이다.
- 3주차 이용 유지 여부는 정가 전환 실패 위험을 설명하는 중요한 행동 신호다.

---

# 13. age/gender personalization 설계

## 13.1 원칙

age/gender는 segment rule이 아니다.

age/gender는 메시지, 채널, 콘텐츠 추천 방식을 조정하는 action personalization layer다.

## 13.2 메시지 variant

| 대상 | 메시지/채널 방향 |
|---|---|
| 20대 | 짧고 즉시성 있는 인기 콘텐츠, 친구추천/쿠폰 메시지, 모바일 push |
| 30대 | 퇴근 후/주말 시청 맥락, 시간 효율, 취향 기반 추천 |
| 40대 이상 | 명확한 혜택 안내, 장르 기반 추천, 가족/주말 시청 맥락 |
| 남성/여성 | 데이터에서 관찰된 선호 차이가 있을 때만 메시지 variant 후보로 사용. 원인처럼 말하지 않음 |

---

# 14. safe/unsafe wording 섹션 설계

HTML의 마지막 또는 appendix에 반드시 넣는다.

| 위험 표현 | 안전 표현 |
|---|---|
| 100원딜이 이탈을 유발했다 | 100원딜 고객군에서 특정 행동 신호와 재구매 실패가 함께 관찰됐다 |
| 3주차 시청량 감소가 이탈 원인이다 | 3주차 시청량 감소는 이탈 위험 신호다 |
| SHAP이 원인을 증명했다 | SHAP은 fitted model explanation이다 |
| age/gender가 이탈 원인이다 | age/gender는 메시지 차별화 layer다 |
| 세그먼트는 최종 캠페인 타겟이다 | 세그먼트는 개입 우선순위 후보군이다 |
| content_preference는 명확한 이탈 방어 타겟이다 | content_preference는 콘텐츠 큐레이션 기반 정가 전환 강화군이다 |
| general은 별 특징 없는 고객군이다 | general은 추가 관찰 필요 residual / monitoring group이다 |

---

# 15. HTML 구현 지침

## 15.1 스타일

화려한 애니메이션은 사용하지 않는다. 문서형 HTML로 만든다. 흰 배경 또는 연한 배경, 카드형 섹션, 넓은 여백, 읽기 쉬운 글자 크기를 사용한다.

## 15.2 표 깨짐 방지

이전 HTML에서 표가 깨졌으므로 반드시 아래 원칙을 따른다.

```css
.table-wrap {
  width: 100%;
  overflow-x: auto;
  margin: 16px 0;
}
.table-wrap table {
  width: 100%;
  border-collapse: collapse;
  table-layout: auto;
}
td, th {
  white-space: normal;
  word-break: keep-all;
  overflow-wrap: anywhere;
}
```

본문 전체에 가로 스크롤이 생기면 실패다. 표 영역 안에서만 좌우 스크롤이 생겨야 한다.

## 15.3 필수 산출물

Codex가 구현할 때 생성해야 하는 파일은 다음이다.

- `FINAL/project_guide_v3.html`
- `FINAL/project_guide_v3_assets`가 필요하면 생성하되, 외부 의존성을 최소화
- `FINAL/project_guide_v3_generation_readme.md`
- `FINAL/project_guide_v3_final_checks.csv`
- `FINAL/project_guide_v3_source_fingerprint_before_after.csv`
- `FINAL/project_guide_v3_review_zip_inventory.csv`
- `FINAL/project_guide_v3_review_package.zip`

---

# 16. Codex에게 금지할 작업

다음은 Codex 구현 goal에 반드시 넣는다.

- 원본 CSV 수정 금지
- park.ingyeom 산출물 수정 금지
- PUBLIC 산출물 수정 금지
- 기존 notebook 수정 금지
- 모델 재실행 금지
- Optuna 실행 금지
- SHAP 재계산 금지
- segmentation 재계산 금지
- 17x assignment 변경 금지
- PUBLIC numeric score를 final 기준으로 사용 금지
- 새 대표 segment 생성 금지
- age/gender를 segment rule로 사용 금지
- payment-device를 해석 기준으로 사용 금지

---

# 17. traceability matrix

| guide v3 주장 | 근거 파일 | 근거 등급 | 사용 위치 | 검수 기준 |
|---|---|---|---|---|
| primary main cohort는 23,079 rows | dataset_lineage_summary.csv | 확인됨 | 데이터셋 lineage | 수치 일치 |
| duration < 21 row 238개 제외 | dataset_lineage_summary.csv | 확인됨 | 전처리 정책 | 수치 일치 |
| exact duplicate extra row 26개 제외 | dataset_lineage_summary.csv | 확인됨 | 전처리 정책 | 수치 일치 |
| 최종 score source는 LightGBM / expanded_no_payment_device / overall_with_promotion / OOF churn_risk | model_and_score_source_summary.md | 확인됨 | score source | 표현 제한 포함 |
| PUBLIC은 reference branch | final_note.md / PUBLIC policy | 확인됨 + 해석 | PUBLIC 섹션 | numeric 병합 금지 |
| AARRR은 feature 해석 프레임 | AARRR_design_summary.md | 확인됨 | AARRR 섹션 | Referral 제한 포함 |
| general_observation은 monitoring group | segmentation_basis_summary.md / final_note patch | 확인됨 + 해석 | segmentation 섹션 | 버린다고 쓰지 않음 |
| content_preference는 정가 전환 강화군 | segmentation_basis_summary.md / final_note patch | 확인됨 + 해석 | action tier | 이탈 방어 타겟 과장 금지 |
| age/gender는 personalization layer | final_note.md | 사용자 확인 + 해석 | action layer | 원인 표현 금지 |
| 100원딜은 강하게 말하되 인과 금지 | 사용자 확인 / final_note | 사용자 확인 + 해석 | narrative | 유발 표현 금지 |

---

# 18. guide v3 검수 체크리스트

Codex가 HTML을 만든 뒤 반드시 아래 항목을 점검한다.

- 데이터셋 lineage가 들어갔는가?
- 전처리 정책이 들어갔는가?
- feature contract가 들어갔는가?
- derived feature 설명이 들어갔는가?
- AARRR 설계가 들어갔는가?
- 07x~18x timeline이 들어갔는가?
- score source 제한이 들어갔는가?
- 7개 segment와 4개 action tier가 들어갔는가?
- 100원딜 narrative가 충분히 강한가?
- PUBLIC을 reference branch로만 설명했는가?
- general/content 역할 재분류가 들어갔는가?
- age/gender가 원인처럼 쓰이지 않았는가?
- Referral이 후속 실험 제안으로만 들어갔는가?
- safe/unsafe wording이 들어갔는가?
- 멘토 Q&A가 들어갔는가?
- 표가 깨지지 않는가?
- final_checks, source_fingerprint, zip_inventory가 있는가?

---

# 19. 아직 사용자 승인 필요한 항목

아래 항목은 project_guide_v3 구현 전 사용자 승인이 있으면 좋다.

- `content_preference_target_candidate` 발표명을 `콘텐츠 큐레이션 기반 정가 전환 강화군`으로 확정할지
- `general_observation` 발표명을 `추가 관찰 필요 잔여군`으로 확정할지
- 100원딜 narrative를 위 핵심 문장 수준으로 강하게 쓸지
- age/gender personalization을 본문에 넣을지 appendix로 뺄지
- 멘토 Q&A를 HTML 끝에 넣을지 별도 문서로 만들지

---

# 20. 다음 행동

1. 사용자가 이 설계안을 검토한다.
2. 사용자가 수정할 표현이나 누락된 섹션을 지적한다.
3. ChatGPT가 Codex용 `project_guide_v3_html_generation_goal`을 작성한다.
4. Codex는 이 설계안 기준으로 HTML과 검수 패키지만 만든다.
5. 사용자가 ZIP을 업로드한다.
6. ChatGPT가 최종 검수한다.

현재 단계에서 새 분석을 돌리면 안 된다. 지금은 guide v3 설계와 구현 단계다.
