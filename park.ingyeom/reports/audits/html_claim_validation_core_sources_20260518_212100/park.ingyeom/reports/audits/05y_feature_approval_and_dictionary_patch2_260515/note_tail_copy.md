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
