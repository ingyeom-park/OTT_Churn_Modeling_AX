- 12c가 최종 모델 비교입니다.
- 14 Optuna 결과가 최종 튜닝 결과입니다.
- review 컬럼은 나중에 보면 됩니다.
- XGBoost가 최종 모델입니다.
- top10 churn_risk가 캠페인 대상입니다.

---

### 7. ChatGPT/LLM에 대한 최상위 행동 규칙

앞으로 이 프로젝트를 이어받는 모든 LLM은 다음을 지킨다.

1. 사용자의 질문에 먼저 정확히 답한다.
2. 사용자가 “묻는 말에만 답하라”고 하면 부연 설명을 줄인다.
3. 파일명, 경로, 컬럼명, 수치, 산출물명은 실제 파일 또는 사용자 로그에 존재하는 것만 확정 표현한다.
4. final_checks PASS만으로 의미 검수까지 통과했다고 말하지 않는다.
5. review 컬럼을 “나중에”로 미루지 않는다.
6. conservative_safe_22를 최종 feature universe처럼 말하지 않는다.
7. 모델 결과를 인과효과나 캠페인 효과로 해석하지 않는다.
8. score 방향을 항상 확인한다.
   - repurchase_score = P(is_repurchase=1)
   - churn_risk = 1 - repurchase_score
9. top-k 위험군은 churn_risk 내림차순으로만 계산한다.
10. 한국어 응답에서는 존댓말을 유지한다.
11. assistant는 스스로를 “제가” 또는 “저는”으로 지칭한다.
12. 실수를 발견하면 즉시 인정하고, 영향 범위와 복구 위치를 말한다.
13. 사용자가 의심을 제기하면 방어하지 말고 실제 검증 대상으로 전환한다.
14. 기존 산출물을 지울 때는 삭제보다 archive/deprecated 격리를 우선한다.
15. 기존 ipynb는 자산이다. 결과물이 오염됐다고 해서 노트북을 무조건 폐기하지 않는다. 복사본을 만들어 패치 후 재실행한다.

---

### 8. 현재 기준 최종 결론

현재 프로젝트는 폐기하지 않는다.  
다만 모델링 pipeline은 재정렬한다.

기존 11b/12c/14는 다음 지위로 강등한다.

`conservative_safe_22 reference`

14 Optuna 진행권은 회수한다.  
13b_review_feature_resolution_and_sensitivity 통과 전까지 11/12/14/16/17 진입을 금지한다.  

이후 모든 모델 비교는 conservative_safe_22와 expanded_feature_set 두 플랜으로 단순화해 보고한다.
expanded_feature_set 내부의 context/content caveat는 별도 플래그로 관리한다.

이 원칙을 어기는 산출물은 final_checks가 PASS여도 canonical으로 인정하지 않는다.
## 00d_full_archive_standardization_260515

- 00d에서 legacy, preliminary, pre-13b conservative_safe_22 산출물, old review zip, handoff snapshot을 표준 archive 구조로 재정리했다.
- 05~14 pre-13b 산출물은 active canonical에서 제거하고 pre13b_conservative_safe_22_reference로 보존한다.
- 이들은 삭제가 아니라 보수 22개 feature 기준 reference로 보존한다.
- 이후 active modeling chain은 13b_review_feature_resolution_and_sensitivity부터 다시 시작한다.
- 모델링 플랜은 conservative_safe_22와 expanded_feature_set 두 가지다.

## 2026-05-15 02:31:36 | 05x_feature_contract_rebuild_260515

- purpose: 기존 05~14 pre-13b 산출물이 archive로 격리된 상태에서 91개 전체 컬럼을 재검토하고 사용자 승인용 feature contract를 작성했다.
- pre-13b 지위: 05~14 pre-13b 결과는 _archive/pre13b_conservative_safe_22_reference에 보존됨. canonical 복원 안 함.
- conservative_safe_22 count: 22
- expanded_feature_set candidate count (incl conservative_22): 84
- forbidden_or_audit_only count: 4
- unresolved count: 1
- user_approval_checklist items: 66
- LLM 원칙: LLM은 feature 최종 제외/승격을 결정하지 않는다. 근거와 후보만 제시. 최종 결정은 사용자 승인 후 확정.
- final_checks: PASS (fail_count=0)
- output_dir: C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\05x_feature_contract_rebuild_260515
- next step: 06x_dataset_generation (사용자 승인 후 진행)
- gate: 05x_user_approval_checklist.csv 승인 전 06x/11/12/14/16/17 진행 금지

## 2026-05-15 16:24:05 | 05x_feature_contract_rebuild_patch_260515

- 05x patch 수행.
- 기존 05x의 decision table 오류 수정.
- USER_KEY와 is_repurchase는 모델 feature 금지로 정책상 고정.
- price/max_screen은 사용자 확인 필요 항목으로 표시.
- 05x patch 이후에도 최종 feature 사용 여부는 사용자 승인 전까지 확정 아님.
- 06x는 사용자 승인 후 진행.
- output_dir: C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\05x_feature_contract_rebuild_patch_260515
- review_zip: C:\Code\ott-churn-prediction\park.ingyeom\zip\05x_feature_contract_rebuild_patch_260515_review_package.zip


## 05y_feature_approval_and_dictionary_260515
- 05y 수행: 사용자 승인 내용을 반영해 feature approval contract, safe model feature name mapping, feature dictionary xlsx를 생성했다.
- 사용자 승인 내용: product_code, billing_method, payment_device, gender, age, reg_hour, price, max_screen, reg_date, end_date 제외. USER_KEY는 feature 금지, is_repurchase는 target으로 기록했다.
- 파생 context 변수 사용: payment flags, gender flags, age_group, registration time-band flags, reg_is_weekend, is_standard, is_premium, is_basic.
- usage summary 전부 사용, content/genre 전부 사용 정책을 반영했다.
- is_promotion 정책: split 기준으로 사용하며 overall_with_promotion 모델에는 feature로 포함 가능, split-specific 모델에서는 제외한다.
- is_churn_prevented 의미와 사용 승인: 현재 cycle 사후 결과가 아니라 과거에 한 번이라도 churn prevention 혜택을 받은 이력 flag로 승인되었고, 한 번이라도 회유에 넘어간 유저군으로 해석한다.
- recency 사용 승인 반영.
- cold_start fixed 생성 정책: is_cold_start_3d_fixed는 first_watch_rel_day <= 2, is_cold_start_7d_fixed는 first_watch_rel_day <= 6 기준으로 06x에서 생성한다.
- old_movie_ratio_5y는 광일 master 값을 유지하고 9행 mismatch caveat를 기록했다.
- 컬럼명 안전화 규칙: 괄호/특수문자 언더바 처리, percent to pct, 공백 제거, 연속 언더바 축약, 앞뒤 언더바 제거.
- feature_dictionary.xlsx 생성 완료.
- 다음 단계는 06x dataset generation이다.


## 05y patch2 수행 기록 - 2026-05-15 18:30:28
- 05y patch2 수행: `05y_feature_approval_and_dictionary_patch2_260515`.
- v3 팀 합의 CSV를 실제로 읽어 비교함: `C:\Code\ott-churn-prediction\park.ingyeom\data\변수_합집합_비교_v3.csv`.
- `is_user_verified` expanded_feature_set 포함 승인 반영.
- feature dictionary formula placeholder 제거.
- cold_start fixed 정책 기록: `is_cold_start_3d_fixed = first_watch_rel_day <= 2`, `is_cold_start_7d_fixed = first_watch_rel_day <= 6`.
- `old_movie_ratio_5y`는 광일 master 유지 및 9행 mismatch caveat 기록.
- `watch_ratio_under_1m`, `watch_ratio_under_5m`는 `<=` 기준으로 공식 기록.
- genre 다중 category caveat 기록: 동일 `MOVIE_NUM` 다중 category 가능성.
- 다음 단계는 06x dataset generation.

## 05y patch2 hotfix 수행 기록 - 2026-05-15
- 05y patch2 hotfix 수행: 기존 `05y_feature_approval_and_dictionary_patch2_260515` 산출물을 새 단계로 만들지 않고 직접 보정했다.
- cold_start 변경 행 수를 `is_cold_start_3d = 1782`, `is_cold_start_7d = 964`로 정정했다.
- 제외 컬럼의 source/principle 설명 오류를 membership/source master, target variable, identifier/group key 기준으로 수정했다.
- `current_feature_name` 별도 컬럼은 만들지 않고 기존 v3 match/status 계열 컬럼으로 처리했다.
- 06x 진행 전 05y feature dictionary 품질 보정을 완료했다.


## 2026-05-15 06x_dataset_generation_260515
- 06x 수행.
- 기존 06 노트북 재활용 여부: 재활용함.
- 05y hotfix 기준으로 conservative / expanded dataset 생성.
- 생성한 새 파생변수는 is_basic, is_cold_start_3d_fixed, is_cold_start_7d_fixed뿐임.
- 사용자 승인 없는 새 feature 생성 없음.
- USER_KEY는 group key, is_repurchase는 target.
- is_promotion scope별 사용 정책은 06x_scope_feature_policy.csv에 기록.
- 다음 단계는 07x.
## 2026-05-15 06x_dataset_generation_retry_260515 pre-retry failure record
- 직전 06x는 실행되었으나 의미 검수에서 실패했다.
- 실패 이유는 23,343 raw master 전체 행으로 dataset을 생성했고, primary main cohort 23,079 rows 기준을 반영하지 않았기 때문이다.
- 직전 실패한 06x 산출물은 사용자가 일부 또는 전부 수동 삭제한 상태였다.
- 이번 retry에서는 해당 경로의 존재 여부를 확인하고, 남아 있는 경우만 삭제했다.
- 이미 없는 경로는 already_missing_user_deleted로 기록했다.
- 직전 06x notebook, reports, review zip은 삭제 또는 삭제 확인 처리했다.
- raw source CSV는 수정하지 않았다.
- 이번 retry는 기존 06 notebook 자산을 복사해 재활용하되, row policy를 강제 반영한다.
- 06x retry의 완료 조건은 primary main cohort 23,079 rows 기준 dataset 생성이다.


## 2026-05-15 06x_dataset_generation_retry_260515 completed
- 직전 06x는 raw 23,343 rows 기준 dataset을 생성해 실패했다.
- 해당 06x notebook, reports, review zip을 삭제 또는 삭제 확인 처리했다.
- 이번 06x retry는 primary main cohort 23,079 rows 기준으로 재생성했다.
- 기존 06 notebook 재활용 여부: 재활용함.
- 05y hotfix 기준으로 conservative / expanded dataset 생성.
- 생성한 새 파생변수는 is_basic, is_cold_start_3d_fixed, is_cold_start_7d_fixed뿐임.
- 사용자 승인 없는 새 feature 생성 없음.
- USER_KEY는 group key, is_repurchase는 target.
- is_promotion scope별 사용 정책은 06x_scope_feature_policy.csv에 기록.
- 다음 단계는 07x.


## 2026-05-15 06x_cold_start_rowlevel_hotfix_260515
- 06x cold_start row-level hotfix 수행.
- USER_KEY 단위 first watch 방식이 아니라 master_row_id/subscription-event row 기준으로 재계산함.
- raw 기준 변경 수 1782 / 964.
- primary cohort 기준 변경 수 1767 / 956.
- negative first_watch_rel_day 0건.
- conservative/expanded dataset은 23079 rows 유지.
- 새로 생성된 feature는 기존 승인된 3개뿐임: is_basic, is_cold_start_3d_fixed, is_cold_start_7d_fixed.
- 다음 단계는 07x.
