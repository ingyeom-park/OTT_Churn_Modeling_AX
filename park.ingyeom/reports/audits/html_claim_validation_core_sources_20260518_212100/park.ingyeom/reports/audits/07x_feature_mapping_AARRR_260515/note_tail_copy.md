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


## 2026-05-15 07x_feature_mapping_AARRR_260515
- 07x 수행.
- 기존 07 notebook 재활용 여부: 재활용함.
- pre13b 07은 구조 참고용이고, 06x 기준으로 새 mapping 작성.
- conservative_safe_22와 expanded_feature_set 각각 AARRR mapping 생성.
- 원본 cold_start가 아니라 fixed cold_start 사용.
- USER_KEY는 group key, is_repurchase는 target/Revenue proxy로 기록.
- is_promotion scope별 사용 정책을 master mapping과 scope handoff에 모두 반영.
- 다음 단계는 08x.
