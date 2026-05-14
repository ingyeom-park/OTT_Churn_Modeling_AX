# 100원딜 OTT 이탈 분석 작업 메모

이 파일은 100원딜 OTT 이탈 분석 프로젝트의 작업 인수인계, 검수 메모, 단계별 주의사항을 누적 기록하는 문서이다.

모든 작업은 `C:\Code\ott-churn-prediction\park.ingyeom` 내부에서만 수행한다.  
모든 실행 작업 파일은 기본적으로 `.ipynb` 노트북 형식으로 만든다.  
`.py` 스크립트는 사용자가 명시적으로 허용한 경우에만 만든다.  
각 단계 산출물은 docx 마스터 플랜의 단계 번호를 폴더명 앞에 붙인다.  
각 Codex 작업이 끝나면 검수용 zip을 `C:\Code\ott-churn-prediction\park.ingyeom\zip`에 생성한다.  
각 Codex 작업이 끝나면 이 `note.md`를 반드시 업데이트한다.

---

## 2026-05-13 | 세션: 광일 v2 기준 작업 구조 재정렬 및 01_data_contract 검수

### 1. 프로젝트 기준 재확인

현재 프로젝트의 최종 기준 데이터는 다음 파일로 고정한다.

`C:\Code\ott-churn-prediction\park.ingyeom\data\(광일)Membership_v2_with_derived_features.csv`

이 파일은 광일이 v2 최종 마스터 파일이며, 이상치 처리와 변수명 통일이 반영된 현재 기준 파일이다.

기존 v1 파이프라인, corrected chain, `Membership_train.csv` 기반 baseline은 최종 근거가 아니라 구조 참고용이다.  
v1 또는 corrected chain의 행 수, 재구매율, AUC, SHAP 결과를 광일 v2 최종 결과처럼 섞으면 안 된다.

프로젝트의 최상위 분석 축은 `promotion / non-promotion`이다.  
`is_promotion`은 단순한 feature 하나가 아니라, 전체 분석 세계를 나누는 split 기준이다.

시간축은 다음으로 고정한다.

- 1주차: 가입일 기준 day 0~6
- 2주차: 가입일 기준 day 7~13
- 3주차: 가입일 기준 day 14~20
- 대응기간: day 21 이후, 구독 종료 전까지
- target: 다음 달 재구매 여부, 즉 `is_repurchase`

4주차 행동은 대응기간의 행동이므로 모델 feature로 사용하면 안 된다.  
3주차까지 본 모델은 “초조기 예측 모델”이 아니라 “갱신 직전 이탈 방어 모델”로 표현해야 한다.

---

### 2. 작업 폴더 규칙 확정

모든 작업 파일과 산출물은 반드시 `park.ingyeom` 내부에만 둔다.

금지 위치:

- repo root
- `_data`
- `.tmp`
- `kim.kwangil`
- `kim.nahyun`
- `kwon.donggeun`
- 그 외 `park.ingyeom` 바깥의 모든 폴더

작업 노트북은 다음과 같이 단계 번호 폴더 아래에 둔다.

예시:

`park.ingyeom\notebook\01_data_contract_260513\01_data_contract_260513.ipynb`

보고서 산출물은 다음과 같이 단계 번호 폴더 아래에 둔다.

예시:

`park.ingyeom\reports\audits\01_data_contract_260513`

검수용 zip은 다음 폴더에 둔다.

`park.ingyeom\zip`

예시:

`park.ingyeom\zip\01_data_contract_260513_review_package.zip`

---

### 3. 사전 실험물과 정식 단계 산출물 구분

`00_preliminary`는 정식 분석 단계가 아니라 기존 사전 실험 보관함이다.

`260513_master.ipynb`, `260513_baseline.ipynb`, `260513_shap_lightgbm_structured.ipynb`는 정식 단계 결과라기보다 사전 탐색 및 preliminary 결과로 본다.

주의할 점:

현재 `park.ingyeom\reports\(광일)baseline_outputs_260513`의 결과는 이름은 baseline이지만 진짜 “깡통 baseline”이 아니다.  
해당 결과는 광일 v2 파일의 다수 feature, 즉 retention, watch time, genre ratio, cold start 등까지 포함한 full-feature preliminary model에 가깝다.  
따라서 최종 보고서에서 이것을 “L0 깡통 baseline”이라고 부르면 안 된다.

진짜 membership-only 또는 깡통 baseline 참고 결과는 기존 `Membership_train.csv` 기반의 `membership_blank_baseline_outputs` 쪽이다.  
다만 이것 역시 최종 광일 v2 기준 baseline이 아니라 “과거 기준 참고 baseline”이다.

---

### 4. 01_data_contract_260513 수행 및 검수 요약

Codex가 수행한 01단계:

`01_data_contract_260513`

목적:

광일 v2 최종 마스터 파일을 실제로 읽고, 행 수, 컬럼 수, 결측, USER_KEY 중복, target 분포, promotion 분포, duration anomaly를 고정한다.

생성된 노트북:

`park.ingyeom\notebook\01_data_contract_260513\01_data_contract_260513.ipynb`

생성된 산출물 폴더:

`park.ingyeom\reports\audits\01_data_contract_260513`

생성된 주요 파일:

- `01_data_contract_summary.csv`
- `01_column_inventory.csv`
- `01_target_distribution.csv`
- `01_promotion_distribution.csv`
- `01_promotion_target_2x2.csv`
- `01_date_parse_audit.csv`
- `01_duration_distribution.csv`
- `01_duration_anomaly_audit.csv`
- `01_user_key_duplicate_audit.csv`
- `01_user_key_duplicate_samples.csv`
- `01_expected_vs_actual_checks.csv`
- `01_final_checks.csv`
- `README.md`

Codex 보고 기준 final checks:

- 33 PASS
- 0 FAIL

ChatGPT 검수 상태:

- 산출물 zip을 열어 주요 CSV 존재 여부 확인
- `01_final_checks.csv`의 33 PASS 확인
- `01_expected_vs_actual_checks.csv` 확인
- `01_user_key_duplicate_audit.csv` 확인
- `01_data_contract_summary.csv` 확인
- 별도로 업로드된 `01_data_contract_260513.ipynb`를 열어 정적 확인
- 노트북은 `.ipynb` 파일이며, 실행 카운트와 출력이 존재함
- 노트북 내부에서 source path는 `park.ingyeom\data\(광일)Membership_v2_with_derived_features.csv`를 사용함
- ChatGPT가 노트북을 로컬에서 재실행한 것은 아님

---

### 5. 01단계에서 확정된 값

광일 v2 최종 마스터 파일 기준:

- row_count: 23,343
- column_count: 91
- total_missing_count: 0
- unique USER_KEY count: 23,134
- duplicated USER_KEY extra rows: 209
- duration < 21 count: 238
- duration = 0 count: 90
- duration between 21 and 30 count: 0

프로모션 × 재구매 2x2:

- 비프로모션, 미재구매: 2,746
- 비프로모션, 재구매: 8,642
- 프로모션, 미재구매: 3,895
- 프로모션, 재구매: 8,060

재구매율:

- 비프로모션 재구매율: 약 75.89%
- 프로모션 재구매율: 약 67.42%

해석 주의:

이 차이는 관찰된 차이다.  
프로모션이 재구매율 감소를 유발했다고 말하면 안 된다.

---

### 6. USER_KEY 중복 관련 주의사항

`USER_KEY 중복 209행`이라는 표현은 축약 표현이다.  
정확하게는 다음과 같이 구분해야 한다.

- 중복 USER_KEY key 수: 143개
- 중복 USER_KEY 그룹에 속한 전체 행 수: 352행
- 첫 번째 행을 제외한 추가 중복분: 209행

따라서 발표나 보고서에서는 “중복 USER_KEY 추가 행 209개” 또는 “143개 USER_KEY가 총 352행에 걸쳐 반복되며, 첫 행 제외 추가 중복분은 209행”이라고 쓰는 것이 더 정확하다.

이 결과 때문에 분석 단위는 unique user-level이라고 단정하면 안 된다.  
현재는 row-level 또는 subscription-event-level로 표현해야 한다.

---

### 7. 완전 중복 행 관련 주의사항

01단계에서 새로 확인된 중요한 관리 포인트:

`duplicated_full_row_count = 48`

즉, 완전히 동일한 행이 48개 존재한다.

01단계에서는 이를 제거하지 않았다.  
그러나 02, 05, 06 단계에서 다음 판단이 필요하다.

- 완전 중복 48행을 유지할 것인가?
- 제거할 것인가?
- 제거한다면 target/promotion/duration 분포가 바뀌는가?
- 완전 중복이 실제 중복 적재인지, 동일 구독 이벤트 반복 기록인지 CSV만으로 판단 가능한가?

현재 결론:

01에서는 flag 및 기록만 한다.  
제거 정책은 아직 정하지 않는다.

---

### 8. duration anomaly 관련 주의사항

01단계에서 확인된 duration anomaly:

- duration < 21: 238행
- duration = 0: 90행
- duration 21~30: 0행

해석 주의:

duration < 21 행은 1~3주차 관측창을 완성하지 못한 행이다.  
이들을 main model cohort에 그대로 넣으면 “행동이 적어서 이탈한 것”과 “관측할 시간이 부족했던 것”이 섞일 수 있다.

현재 결론:

01에서는 제외하지 않았다.  
03 관측창 정책 또는 06 최종 cohort 확정 단계에서 main cohort 제외 여부를 결정해야 한다.

사용자 가설:

단기 종료는 고객센터에 연락하여 즉시 계정 삭제 또는 구독 종료를 요청한 케이스일 수 있다.  
다만 CSV만으로는 확정할 수 없으므로 발표에서는 “단기 종료 후보” 또는 “조기 종료 후보”라고 표현해야 한다.

---

### 9. 02단계로 넘어갈 때의 핵심 인수인계

다음 단계는:

`02_target_score_orientation_260513`

목적:

분석 단위, target 방향, score 방향을 고정한다.

반드시 고정해야 할 점:

- `is_repurchase=1`은 재구매이다.
- 모델 평가의 positive class는 재구매이다.
- 모델 출력 점수는 `repurchase_score`로 명명하는 것이 안전하다.
- 비즈니스 운영용 이탈 위험 점수는 `churn_risk = 1 - repurchase_score`로 변환한다.
- `score가 높다`라는 표현은 반드시 어떤 score인지 명시해야 한다.
- `repurchase_score`가 높으면 재구매 가능성이 높은 것이다.
- `churn_risk`가 높으면 이탈 위험이 높은 것이다.
- 이 둘을 혼동하면 고위험군과 안정군이 뒤집힌다.

02단계에서는 모델링하지 않는다.  
02단계에서는 SHAP도 하지 않는다.  
02단계에서는 feature set도 만들지 않는다.  
02단계에서는 duration < 21 제외도 하지 않는다.

02단계에서는 문서, 표, 규칙을 만드는 것이 목적이다.

---

### 10. 이후 단계에서 계속 들고 갈 open risks

현재 open risk는 다음과 같다.

1. 분석 단위 문제  
   USER_KEY 중복이 있으므로 unique user-level이라고 말하면 안 된다.

2. 완전 중복 48행  
   유지/제거 정책 미정. 05 또는 06에서 반드시 검토해야 한다.

3. duration < 21 238행  
   1~3주차 관측창과 충돌한다. 03 또는 06에서 main cohort 제외 여부를 정해야 한다.

4. end_date / duration timing  
   end_date가 운영 시점에 이미 예정 종료일로 알려진 값인지, 사후 확정 종료일인지 확인이 필요하다.  
   CSV만으로 불명확하면 leakage/timing audit에서 review로 둔다.

5. is_churn_prevented timing  
   과거 해지 방어 이력이라면 사용 가능할 수 있지만, 현재 구독 cycle의 사후 개입 결과라면 leakage이다.  
   CSV만으로 명확하지 않으면 review로 둔다.

6. preliminary full-feature model 혼동  
   현재 `(광일)baseline_outputs_260513`는 진짜 깡통 baseline이 아니다.  
   최종 baseline growth history는 별도로 11단계에서 다시 설계해야 한다.

7. SHAP 인과 오해  
   SHAP은 모델 설명이지 원인 설명이 아니다.  
   “SHAP 상위 피처를 바꾸면 재구매가 오른다”라고 말하면 안 된다.

8. 프로모션 인과 오해  
   “프로모션 고객과 비프로모션 고객 사이에 재구매율 차이가 관찰되었다”는 가능하다.  
   “100원딜이 재구매율 감소를 유발했다”는 현재 데이터로 말하면 안 된다.

---

### 11. 앞으로 모든 Codex /goal에 포함할 공통 요구사항

앞으로 모든 Codex goal에는 다음 요구사항을 포함한다.

1. 모든 파일 읽기/쓰기는 `park.ingyeom` 내부에서만 수행한다.
2. 모든 실행 작업 파일은 `.ipynb`로 만든다.
3. `.py` 스크립트는 만들지 않는다.
4. 기존 파일을 수정하지 않는다. 필요한 경우 새 단계 폴더를 만든다.
5. output folder가 이미 있으면 `run_YYYYMMDD_HHMMSS` 하위 폴더를 만든다.
6. 각 단계 종료 시 `final_checks.csv`를 만든다.
7. 각 단계 종료 시 필요한 경우 `expected_vs_actual_checks.csv`를 만든다.
8. 각 단계 종료 시 `README.md`를 만든다.
9. 각 단계 종료 시 `C:\Code\ott-churn-prediction\park.ingyeom\note.md`를 업데이트한다.
10. 각 단계 종료 시 검수용 zip을 `C:\Code\ott-churn-prediction\park.ingyeom\zip`에 만든다.
11. 검수용 zip에는 해당 단계의 `.ipynb`, 산출물 CSV, README, final_checks, expected_vs_actual, 주요 로그 또는 요약 파일을 포함한다.
12. 원천 데이터 full CSV는 사용자가 명시적으로 요구하지 않는 한 zip에 포함하지 않는다.

---

## 다음 예정 단계

다음 단계:

`02_target_score_orientation_260513`

진행 전 조건:

- 01_data_contract_260513 통과
- note.md 업데이트
- Codex goal에 note.md 업데이트와 review package zip 생성을 포함할 것

02에서 확인할 핵심 질문:

1. 행 하나를 무엇으로 부를 것인가?
2. `is_repurchase=1`의 의미를 어떻게 고정할 것인가?
3. 모델 평가용 score와 운영용 churn risk score를 어떻게 구분할 것인가?
4. 보고서와 발표에서 금지해야 할 score 표현은 무엇인가?
5. 이후 모델링 산출물에서 score 컬럼명을 어떻게 표준화할 것인가?

## 2026-05-13 22:19:36 - 02_target_score_orientation_260513

- Purpose: 분석 단위, target 의미, score 방향, 안전 문구, downstream naming contract를 고정했다.
- Files created: notebook `notebook/02_target_score_orientation_260513/02_target_score_orientation_260513.ipynb`, output folder `reports\audits\02_target_score_orientation_260513`, review zip `zip/02_target_score_orientation_260513_review_package.zip`.
- Key decisions: 분석 단위는 row-level / subscription-event-level; target은 `is_repurchase`; positive class는 `is_repurchase=1`; model output은 `repurchase_score`; 운영상 `churn_risk = 1 - repurchase_score`.
- Checks: source CSV exists=True; previous 01 folder exists=True; row_count=23343; column_count=91; unique_USER_KEY_count=23134; duplicated_USER_KEY_extra_rows=209; duplicated_full_row_count=48.
- Interpretation limits: modeling, prediction, SHAP, Optuna, feature engineering, leakage/timing audit, row exclusion은 수행하지 않았다. 행을 unique user로 부르지 않는다.
- Risks to carry forward: USER_KEY duplication, duplicated full rows, duration < 21 rows, end_date/duration timing, is_churn_prevented timing, preliminary full-feature model naming, groupwise model에서 is_promotion 제외 필요.
- Warnings: none.
- Next step recommendation: 03_observation_window_policy_260513.


## 2026-05-13 22:56:54 - 03_observation_window_policy_260513

- Purpose: 1~3주차 관측창, day 21 scoring point, day 21 이후 대응기간, 4주차 금지 정책, duration anomaly 후보 정책을 문서화했다.
- Files created: notebook `notebook/03_observation_window_policy_260513/03_observation_window_policy_260513.ipynb`, output folder `reports\audits\03_observation_window_policy_260513`, review zip `zip/03_observation_window_policy_260513_review_package.zip`.
- Key decisions: reg_date를 day 0 anchor로 두고 week1=day0~6, week2=day7~13, week3=day14~20, scoring point=day21, response period=day21~subscription end 전으로 정의했다. 4th-week behavior는 modeling feature로 금지한다.
- Checks: source CSV exists=True; previous 01 folder exists=True; previous 02 folder exists=True; row_count=23343; column_count=91; duration_lt_21=238; duration_eq_0=90; duration_21_30=0; duplicated_full_row_count=48.
- Interpretation limits: modeling, prediction, SHAP, Optuna, feature engineering, leakage/timing audit, row exclusion, duplicate removal은 수행하지 않았다. 행을 unique user로 부르지 않는다.
- Risks to carry forward: duration < 21 rows, duration=0 interpretation, total/all-period timing, recency timing, content window proof, end_date/duration leakage, full duplicate row policy, groupwise model에서 is_promotion 제외 필요.
- Warnings: none.
- Next step recommendation: 04_promotion_split_260513.


## 2026-05-13 23:08:26 - 04_promotion_split_260513

- Purpose: is_promotion을 최상위 promotion/non-promotion split 변수로 고정하고, group distribution, promotion-target 2x2, promotion-duration anomaly, groupwise modeling policy를 문서화했다.
- Files created: notebook `notebook/04_promotion_split_260513/04_promotion_split_260513.ipynb`, output folder `reports\audits\04_promotion_split_260513`, review zip `zip/04_promotion_split_260513_review_package.zip`.
- Key decisions: `is_promotion`은 단순 feature가 아니라 top-level split이다. 전체 모델에서는 with/without 비교가 가능하지만, promotion-only와 nonpromotion-only 모델에서는 feature로 넣지 않는다.
- Checks: source CSV exists=True; previous 01/02/03 folders exist=True/True/True; row_count=23343; column_count=91; duplicated_full_row_count=48; duration_lt_21=238; promotion distribution=[{'is_promotion': 0, 'n': 11388, 'rate': 0.4878550314869554, 'unique_USER_KEY_count': 11221, 'duplicated_USER_KEY_extra_rows': 167, 'duplicated_full_rows': 47}, {'is_promotion': 1, 'n': 11955, 'rate': 0.5121449685130446, 'unique_USER_KEY_count': 11951, 'duplicated_USER_KEY_extra_rows': 4, 'duplicated_full_rows': 1}].
- Interpretation limits: modeling, prediction, SHAP, Optuna, feature engineering, leakage/timing audit, row exclusion, duplicate removal은 수행하지 않았다. promotion 차이는 descriptive이며 causal claim이 아니다.
- Risks to carry forward: promotion 차이의 비인과성, groupwise model에서 is_promotion 제외, duration anomaly의 promotion별 차이, duration < 21 포함 상태, duplicated full rows 포함 상태, USER_KEY 중복, overall with/without promotion 비교 필요.
- Warnings: none.
- Next step recommendation: 05_column_role_leakage_timing_audit_260513.

## 2026-05-14 01:04:36 | 05_column_role_leakage_timing_audit_260513

- Purpose: classify all 91 source CSV columns by role, leakage risk, timing family, and future modeling eligibility without creating a modeling dataset.
- Files created: 05_input_consistency_check.csv, 05_full_column_inventory.csv, 05_column_role_dictionary.csv, 05_timing_audit.csv, 05_leakage_suspect_audit.csv, 05_human_review_required_columns.csv, 05_baseline_ladder_feature_family_policy.csv, 05_recommended_feature_set_contracts.csv, 05_forbidden_drop_columns.csv, 05_review_required_columns.csv, 05_conservative_safe_candidate_columns.csv, 05_redundancy_and_naming_risk_audit.csv, 05_safe_unsafe_wording.csv, 05_open_risks_for_next_steps.csv, 05_final_checks.csv, README.md
- Key decisions: `USER_KEY` is id; `is_repurchase` is target; `is_promotion` is split; groupwise models must exclude `is_promotion`; response-period and target-like columns are excluded; uncertain columns remain review.
- Checks summary: source file exists, previous folders checked, all 91 columns inventoried, role dictionary and timing audit produced.
- Counts: conservative safe=16, review-required=72, forbidden/drop=6; overall={'review': 69, 'yes': 17, 'no': 5}; groupwise={'review': 69, 'yes': 16, 'no': 6}.
- Especially risky columns: `is_churn_prevented` may be intervention/outcome-like; `end_date` and duration logic require scoring-time confirmation; total usage and recency require timing confirmation; content/genre ratio and new movie columns require construction-window confirmation.
- Interpretation limits: this audit does not prove absence of leakage; `review` means not approved for modeling yet; no rows or duplicate rows were removed.
- Risks to carry forward: unresolved timing for total/all-period, recency, end_date/duration, content/genre ratio; cross-promotion USER_KEY overlap makes user-level promotion wording risky; final cohort exclusion policy remains future step.
- Next step recommendation: `06_common_preprocessing_final_cohort_policy_260513` or docx-strict `06_common_preprocessing_and_final_cohort_260513`.

## 2026-05-14 01:19:27 | 05b_column_role_dictionary_patch_260513

- Purpose: patch semantic role/family/timing errors from step 05 and create canonical 05b outputs for downstream use.
- Files created: 05b_input_validation.csv, 05b_detected_issues_from_05.csv, 05b_canonical_column_role_dictionary.csv, 05b_column_role_patch_log.csv, 05b_canonical_timing_audit.csv, 05b_canonical_leakage_suspect_audit.csv, 05b_true_human_review_required_columns.csv, 05b_human_review_summary.csv, 05b_canonical_recommended_feature_set_contracts.csv, 05b_conservative_safe_candidate_columns.csv, 05b_review_required_columns.csv, 05b_forbidden_drop_columns.csv, 05b_role_and_status_summary.csv, 05b_downstream_handoff_policy.csv, 05b_safe_unsafe_wording.csv, 05b_open_risks_for_next_steps.csv, 05b_final_checks.csv, README.md
- Key issues corrected: retention ratio columns no longer genre; usage ratio columns no longer genre; cold_start columns are activation/onboarding; diff_between_w*_w* columns are retention_change; review and forbidden contract groups separated.
- Patched columns: 84; detected issues: 48.
- Checks summary: source and previous 05 files validated; actual repo root recorded; canonical dictionary and timing audit contain 91 columns.
- Role/status summary after patch: overall={'review': 65, 'yes': 23, 'no': 3}; groupwise={'review': 65, 'yes': 22, 'no': 4}.
- Remaining risky columns: is_churn_prevented, end_date/duration logic, total usage, recency, content/genre ratio windows, review-required metadata/context columns.
- Interpretation limits: 05b corrects dictionary semantics but does not prove no leakage; review remains not approved for modeling.
- Risks to carry forward: downstream must use 05b canonical files; 06 must decide final cohort/preprocessing policy without silently modeling with review columns.
- Next step recommendation: 06_common_preprocessing_and_final_cohort_260513.



## 2026-05-14 01:45:23 | 06_common_preprocessing_and_final_cohort_260513

- Purpose: 공통 전처리 row policy와 최종 primary main cohort를 확정하고, downstream baseline 후보 테이블을 보수적으로 생성했다.
- Files created: 19 CSV files, README.md, notebook, review package zip.
- Key row policy decisions: duration < 21 제외, 완전 중복 extra row 제외, duplicated USER_KEY 유지, cross-promotion USER_KEY overlap 유지.
- Primary main cohort row count: 23079
- Excluded duration < 21 count: 238
- Excluded full duplicate extra row count: 26
- Conservative feature count: 22
- Checks passed or failed: final checks table 참조.
- Interpretation limits: 모델 학습, 예측, SHAP, Optuna, causal claim 없음. cohort와 policy 산출물만 생성했다.
- Risks to carry forward: review 컬럼, is_churn_prevented, end_date/duration feature timing, total/all-period usage, recency, content/genre window 미해결.
- Next step recommendation: 07_AARRR_feature_mapping_260513 우선. 11_baseline_growth_history_260513는 AARRR/EDA 계획 확인 후 진행.

## 2026-05-14 | 보수적 feature 사용 원칙 및 06 메모 정정

- Context: 06_common_preprocessing_and_final_cohort_260513 검수 이후, 이후 모델링과 EDA 진행 방향을 보수적으로 고정하기로 했다.
- Decision: 앞으로 baseline ladder, 모델링, SHAP, 세그먼트 설계의 기본 입력은 `06_primary_main_cohort_conservative_features.csv`와 05b canonical 산출물을 기준으로 한다.
- Conservative principle: 05b/06에서 safe candidate로 확정된 feature를 우선 사용한다. review 컬럼은 timing, semantic, leakage 가능성이 해소되기 전까지 표준 모델링에 넣지 않는다.
- Review columns policy: membership/context, total/all-period usage, recency, content/genre ratio, `is_churn_prevented`, `end_date/duration` 관련 review 컬럼은 별도 확인 또는 sensitivity 실험으로 분리한다.
- Modeling implication: 당장 L0 membership-only baseline을 만들기 어렵더라도, review 컬럼을 성급하게 넣어 성능을 올리지 않는다. 표준 baseline은 conservative safe-window feature 기준으로 시작한다.
- Naming caution: 기존 preliminary full-feature model은 L0 baseline으로 부르지 않는다. 필요하면 `full-feature preliminary model` 또는 `preliminary exploratory model`로만 부른다.
- Downstream rule: 06 이후 단계는 원본 05가 아니라 `05b_canonical_column_role_dictionary.csv`, `05b_canonical_timing_audit.csv`, `05b_canonical_recommended_feature_set_contracts.csv`를 기준으로 한다.
- 06 correction: 이전 note.md에는 06 로그가 두 번 기록되어 있었고, full duplicate extra row count가 26과 48로 다르게 적혀 있었다. 중복된 01:47:04 로그는 삭제했다. 정확한 해석은 다음과 같다.
  - source 전체 기준 exact full duplicate extra rows: 48
  - duration < 21 제외와 겹친 duplicate extra rows: 22
  - duration >= 21 eligible cohort 안에서 primary main cohort에서 추가 제외된 exact full duplicate extra rows: 26
  - 따라서 primary main cohort 계산은 `23,343 - 238 - 26 = 23,079`가 맞다.
  - `238 + 48 = 286행 제외`라고 말하면 안 된다.
- Correct 06 main cohort summary:
  - raw source rows: 23,343
  - duration < 21 excluded from primary main cohort: 238
  - additional exact full duplicate extra rows excluded after duration policy: 26
  - primary main cohort final rows: 23,079
  - conservative feature count: 22
- Next recommended step: `07_AARRR_feature_mapping_260513`을 먼저 진행한다. 11_baseline_growth_history로 바로 가지 않는다. AARRR mapping과 EDA 계획을 먼저 잠근 뒤 보수적 baseline ladder로 넘어간다.


## 2026-05-14 02:12:59 | 07_AARRR_feature_mapping_260513

- Purpose: 기존 91개 컬럼과 06 conservative feature를 AARRR 단계에 개념적으로 매핑하고, 표준 분석 가능 영역과 review/proposal 영역을 분리했다.
- Files created: 14 CSV files, README.md, notebook, review package zip.
- Key AARRR mapping decisions: Acquisition=`is_promotion` descriptive split, Activation=early viewing/cold-start proxy, Retention=week1~3 behavior proxy, Revenue=`is_repurchase` target proxy, Referral=not observed/proposal only.
- Conservative feature count by AARRR stage: {"activation": 6, "retention": 16}. Acquisition은 split metadata, Revenue는 target proxy, Referral은 observed feature 없음으로 정리했다.
- Review columns policy: review 컬럼은 개념적으로 AARRR에 매핑되더라도 표준 모델링 승인으로 보지 않는다.
- Referral boundary: 현재 데이터에 referral/invite/share/campaign response 로그가 없어 측정 claim 금지, 후속 실험 제안만 허용한다.
- Checks passed or failed: final checks table 참조.
- Interpretation limits: 모델링, 예측, SHAP, Optuna, 통계검정, 시각화, feature engineering 없음.
- Risks to carry forward: membership/context L0는 strict conservative 기준에서 제한적이며, review resolution 또는 sensitivity design 필요. Referral, revenue proxy, acquisition causal wording 주의.
- Next step recommendation: 08_promotion_vs_nonpromotion_eda_260513.

## 2026-05-14 02:23:23 | 08_promotion_vs_nonpromotion_eda_260513

- Purpose: primary main cohort 안에서 promotion/non-promotion 행을 conservative safe feature 기준으로 descriptive EDA 비교했다.
- Success output folder: `reports/eda/08_promotion_vs_nonpromotion_eda_260513/run_20260514_022322`. 첫 실행 실패 후 최종 성공 산출물은 이 run 폴더 기준이다.
- Files created: 17 CSV files, README.md, notebook, review package zip.
- Promotion/non-promotion row counts: {"0": 11175, "1": 11904, "overall": 23079}
- Repurchase rates by promotion: {"0": 0.7624161073825504, "1": 0.6751512096774194, "overall": 0.717405433510984}
- Key descriptive findings: primary main cohort에서 프로모션 행의 재구매율이 비프로모션 행보다 약 8.73%p 낮게 관찰되었다. 단, 이는 descriptive difference이며 인과효과가 아니다.
- Conservative feature count: 22
- Conservative feature finding: promotion/non-promotion 간 conservative feature 평균 차이는 표준화 평균 차이 기준 모두 negligible bucket이었다. 따라서 08만으로 “프로모션/비프로모션 행동 feature 분포가 크게 다르다”고 주장하면 안 된다.
- Important interpretation: 08의 결과는 “재구매율 차이는 관찰되지만, 보수적 safe feature 기준의 promotion 간 평균 행동 차이는 약하다”로 해석해야 한다. 09와 10에서 promotion × repurchase 2x2 및 target 내부 차이를 더 깊게 봐야 한다.
- AARRR summary caution: `08_AARRR_summary_by_promotion.csv`의 stage별 평균값은 서로 단위가 다른 feature를 평균낸 값이므로 해석에 사용하지 않는다. stage별 feature 개수와 목록 확인용으로만 본다.
- Review columns policy: 05b review columns는 standard conservative EDA feature table에서 제외했다.
- Checks passed or failed: final checks table 참조. final checks는 47 PASS / 0 FAIL로 검수했다.
- Interpretation limits: descriptive only, no p-values, no statistical testing, no modeling, no causal claim, no Referral measurement.
- Risks to carry forward: promotion 차이는 인과가 아니며, duplicated USER_KEY/cross-promotion overlap은 row-level 언어로 유지해야 한다. review columns는 후속 resolution 또는 sensitivity design 필요. 09 이후 단계에서 08 입력을 사용할 경우 반드시 `run_20260514_022322` 기준 산출물을 사용한다.
- Next step recommendation: 09_promotion_repurchase_2x2_eda_260513.

## 2026-05-14 11:36:44 - 08b_promotion_vs_nonpromotion_eda_audit_patch_260513

- purpose: 08 해석 위험 패치, 성공 08 run folder source lock, 09 handoff.
- files created: 08b_preflight_input_validation.csv, 08b_08_run_folder_inventory.csv, 08b_08_source_of_truth_lock.csv, 08b_key_metric_recomputation.csv, 08b_internal_consistency_audit.csv, 08b_conservative_feature_difference_interpretation_audit.csv, 08b_promotion_feature_difference_negative_finding.csv, 08b_promotion_target_signal_preview_from_08.csv, 08b_AARRR_summary_interpretability_audit.csv, 08b_AARRR_summary_safe_replacement.csv, 08b_review_column_exclusion_validation.csv, 08b_interpretation_guardrail.csv, 08b_handoff_to_09_question_design.csv, 08b_decision_summary.csv, 08b_safe_unsafe_wording.csv, 08b_open_risks_for_next_steps.csv, README.md
- valid 08 run folder: reports/eda/08_promotion_vs_nonpromotion_eda_260513/run_20260514_022322
- recomputed key metrics: primary=23,079; nonpromotion=11,175; promotion=11,904; nonpromotion repurchase rate=0.762416; promotion repurchase rate=0.675151; max abs SMD=0.026469; SMD buckets={'negligible': 22}
- final interpretation of 08: 재구매율 차이는 descriptive하게 관찰되지만, conservative feature 평균 차이는 전반적으로 negligible이므로 행동 프로필이 크게 다르다고 주장하지 않는다.
- restricted 08 outputs: 08_AARRR_summary_by_promotion.csv raw stage mean averages; base-folder 08 artifacts outside run_20260514_022322; review columns as standard feature interpretation.
- whether 08 should be rerun: no
- checks passed or failed: audit_fail_count=0; metric_mismatch_count=0; accept_08_structure=yes
- risks to carry forward: causal language forbidden; referral not observed; review columns excluded; AARRR raw stage averages restricted; 09 must not overclaim.
- next step recommendation: 09_promotion_repurchase_2x2_eda_260513


---

## 2026-05-14 12:07:36 | step: 09_promotion_repurchase_2x2_eda_260513

### purpose
promotion × repurchase 2x2 구조에서 promotion/non-promotion 각 내부의 재구매/미재구매 행을 구분하는 보수적 행동 신호를 기술적으로 확인했다.

### files created
- 09_08_vs_09_contrast_summary.csv
- 09_2x2_cohort_definition.csv
- 09_2x2_structure_summary.csv
- 09_AARRR_2x2_interpretation_summary.csv
- 09_cohort_and_08b_consistency_check.csv
- 09_conservative_feature_distribution_by_2x2.csv
- 09_cross_group_target_signal_comparison.csv
- 09_descriptive_findings_summary.csv
- 09_open_risks_for_next_steps.csv
- 09_preflight_input_validation.csv
- 09_safe_unsafe_wording.csv
- 09_top_target_signals_by_group.csv
- 09_week_stage_signal_summary.csv
- 09_within_nonpromotion_target_difference_summary.csv
- 09_within_promotion_target_difference_summary.csv
- README.md

### 2x2 cohort counts
- nonpromotion_repurchase: 8520
- nonpromotion_nonrepurchase: 2655
- promotion_repurchase: 8037
- promotion_nonrepurchase: 3867

### key within-promotion target signals
- watch_time(min)_w3 | SMD=0.6913 | large
- watch_session_w3 | SMD=0.6627 | large
- is_only_w1 | SMD=-0.5487 | large

### key within-nonpromotion target signals
- watch_session_w3 | SMD=0.7501 | large
- watch_time(min)_w3 | SMD=0.7434 | large
- is_only_w1 | SMD=-0.6689 | large

### 08 vs 09 contrast
- 09 target-internal signal이 08 promotion-average signal보다 큰 feature 수: 22
- 해석: 기술적 SMD 비교이며 인과, 유의성, 예측 성능을 뜻하지 않는다.

### checks
- final check status: PASS
- primary main cohort rows: 23079
- conservative feature count: 22

### interpretation limits
- 모델링, 예측, SHAP, Optuna, p-value, 통계적 유의성 검정은 수행하지 않았다.
- review columns는 표준 보수 feature 비교에 사용하지 않았다.
- row-level subscription-event 단위이며 unique-user 분석으로 말하면 안 된다.
- promotion 효과에 대한 인과 주장은 금지한다.

### risks to carry forward
- SMD는 descriptive effect size로만 사용해야 한다.
- duplicated USER_KEY와 cross-promotion overlap 때문에 row-level 언어를 유지해야 한다.
- step 10에서 분포 모양과 안정성을 더 확인해야 한다.

### next step recommendation
10_feature_eda_260513

## 2026-05-14 | raw view window validation 사전 검산

- Purpose: 광일 마스터의 행동 feature가 정말 1~3주차(day0~20) 기준인지 확인하기 위해 raw `Membership_train.csv`, `View_History_v2.csv`, `User_Mapping_v2.csv`, `Movie_Master_v2.csv`와 대조했다.
- Key result: raw `View_History_v2.csv`에는 day21 이후 시청 로그가 존재한다. day21+ matched view rows는 17,621건, 관련 membership rows는 6,044행, watch_time 합계는 767,791분이다.
- Main validation: master의 `watch_time(min)_w1/w2/w3`, `watch_session_w1/w2/w3`, `total_watch_time(min)`, `total_watch_count`는 raw day0~20 재계산값과 23,343행 전체에서 일치했다.
- Interpretation: `total_watch_time(min)`과 `total_watch_count`라는 이름은 전체 기간처럼 보일 수 있으나, 실제 계산값은 w1+w2+w3, 즉 day0~20 관측창 기준이다.
- Additional validation: `unique_movie`, `watch_days`, `active_ratio`, `recency`, `watch_per_day`, 평균/중앙/표준편차 시청시간, 일별 평균/최대 시청시간, 최대 일별 세션도 day0~20 기준 재계산과 일치했다.
- Content validation: `avg_ott_release_year`는 day0~20 raw view와 Movie_Master_v2를 결합한 watch_time 가중평균과 일치했다. 장르 ratio 대부분도 day0~20 기준으로 일치했다.
- Remaining caveat: 일부 `action_adventure_ratio`, `family_animation_ratio` 불일치는 4주차 포함 문제가 아니라 Movie_Master_v2의 동일 MOVIE_NUM 다중 category 충돌에서 비롯된 것으로 보인다. `new_movie_in_90d/180d/365d_ratio`는 release-month 기준 convention 확인이 추가로 필요하다.
- Decision: usage feature 기준으로는 광일 마스터가 1~3주차 관측창을 사용했다는 근거가 강하다. 다만 이 검증은 정식 산출물로 남기기 위해 `09b_raw_view_window_validation_260514` 단계로 공식화하는 것이 좋다.

## 2026-05-14 13:01:52 | 09b_raw_view_window_validation_260514

- purpose: 광일 master의 usage/content feature가 raw view day0~20, 즉 1~3주 관측창 기준인지 공식 검증했다.
- files created: notebook 1개, audit CSV 20개, README.md, review package zip.
- raw view day21+ presence: day21+ matched view rows 17,621건, source rows 6,044행, watch_time 합계 767,791분.
- core usage day0~20 validation result: core usage 8개 비교의 mismatch 합계 0건.
- day21+ leakage contrast result: day0~20 기준과 day21+ 포함 기준을 분리 비교했으며, 상세 결과는 `09b_day21_plus_leakage_contrast_test.csv`에 저장했다.
- membership-master alignment result: raw Membership_train과 master의 key/date/target 정렬 검증을 `09b_membership_master_alignment_check.csv`에 저장했다.
- content validation result: avg release year, genre ratio, new movie ratio를 day0~20 content join 기준으로 검토했다. genre mismatch 합계는 206건이다.
- unresolved caveats: derived unresolved count 1개, new movie ratio exact formula 확인 여부 False. Movie_Master_v2 중복 MOVIE_NUM/category 충돌 가능성은 계속 관리한다.
- checks passed or failed: 최종 PASS/FAIL은 `09b_final_checks.csv` 기준으로 확인한다.
- interpretation limits: 모델링, 예측, SHAP, Optuna, p-value, 통계적 유의성 검정, 인과 주장은 수행하지 않았다.
- risks to carry forward: raw View_History에는 day21+가 있으므로 raw 자체가 3주 제한 데이터라고 말하면 안 된다. 핵심은 master feature가 day0~20 기준인지다.
- next step recommendation: core usage window validation이 PASS이면 `10_feature_eda_260513`로 진행한다.


## 2026-05-14 13:04:27 | 09b_raw_view_window_validation_260514

- purpose: 광일 master의 usage/content feature가 raw view day0~20, 즉 1~3주 관측창 기준인지 공식 검증했다.
- files created: notebook 1개, audit CSV 20개, README.md, review package zip.
- raw view day21+ presence: day21+ matched view rows 17,621건, source rows 6,044행, watch_time 합계 767,791분.
- core usage day0~20 validation result: core usage 8개 비교의 mismatch 합계 0건.
- day21+ leakage contrast result: day0~20 기준과 day21+ 포함 기준을 분리 비교했으며, 상세 결과는 `09b_day21_plus_leakage_contrast_test.csv`에 저장했다.
- membership-master alignment result: raw Membership_train과 master의 key/date/target 정렬 검증을 `09b_membership_master_alignment_check.csv`에 저장했다.
- content validation result: avg release year, genre ratio, new movie ratio를 day0~20 content join 기준으로 검토했다. genre mismatch 합계는 206건이다.
- unresolved caveats: derived unresolved count 1개, new movie ratio exact formula 확인 여부 False. Movie_Master_v2 중복 MOVIE_NUM/category 충돌 가능성은 계속 관리한다.
- checks passed or failed: 최종 PASS/FAIL은 `09b_final_checks.csv` 기준으로 확인한다.
- interpretation limits: 모델링, 예측, SHAP, Optuna, p-value, 통계적 유의성 검정, 인과 주장은 수행하지 않았다.
- risks to carry forward: raw View_History에는 day21+가 있으므로 raw 자체가 3주 제한 데이터라고 말하면 안 된다. 핵심은 master feature가 day0~20 기준인지다.
- next step recommendation: core usage window validation이 PASS이면 `10_feature_eda_260513`로 진행한다.

## 2026-05-14 13:50:02 - 10_feature_eda_260513

- purpose: Step 09 target-internal signal 뒤의 분포 형태를 conservative safe features 기준으로 확인했다.
- files created: 21 CSV audit outputs, README.md, matplotlib PNG figures, executed notebook, review zip.
- actual_output_folder: C:\Code\ott-churn-prediction\park.ingyeom\reports\eda\10_feature_eda_260513
- actual_figure_folder: C:\Code\ott-churn-prediction\park.ingyeom\reports\figures\10_feature_eda_260513
- focus features analyzed: watch_time(min)_w3, watch_session_w3, is_only_w1, is_w1_over_50pct, retention_w3_ratio, retention_w2_ratio, diff_between_w3_w1, diff_between_w3_w2, diff_between_w2_w1, watch_time(min)_w2, watch_session_w2, is_cold_start_3d, is_cold_start_7d
- key distribution findings: 3주차 시청시간/세션, is_only_w1, retention/diff feature를 중심으로 2x2 분포 차이를 확인했다.
- zero-inflation/outlier caveats: 일부 feature는 zero/nonzero 비율 또는 상위 tail 영향 가능성이 있어 평균만으로 해석하지 않는다.
- week3/retention findings: 재구매/미재구매 내부 비교에서 w3 사용량과 1주차만 시청 패턴을 우선 확인할 필요가 있다.
- supports proceeding to 11: yes, descriptive EDA 기준으로 11_baseline_growth_history_260513 진행 가능. 단 review-column resolution은 별도 선택 사항이다.
- checks passed or failed: see 10_final_checks.csv.
- interpretation limits: no causality, no p-value, no modeling, no final segment threshold.
- risks to carry forward: review columns excluded, content/context signals limited, feature overlap needs later care, USER_KEY duplication requires group-aware CV later.
- next step recommendation: 11_baseline_growth_history_260513.

## 2026-05-14 14:38:12 - 11_baseline_growth_history_260513

- 목적: 보수 safe-window feature 기반 baseline growth history 구축.
- 생성 파일: 모델 CSV 23개, README.md, PNG figure 6개, 실행 저장 notebook, review package zip.
- dataset scopes: overall_without_promotion, overall_with_promotion, promotion_only, nonpromotion_only.
- feature ladder: L0 dummy prior, L1 activation safe, L2 week2 retention, L3 week3 retention, L4 all conservative behavior, L5 promotion indicator only for overall_with_promotion.
- models: DummyPrior, LogisticRegression, HistGradientBoosting, RandomForest. 튜닝은 수행하지 않았다.
- best baseline by scope: [{'dataset_scope': 'nonpromotion_only', 'best_model_name': 'RandomForest', 'best_ladder_step': 'L4_all_conservative_behavior', 'best_oof_auc': 0.8303052527342334, 'train_valid_gap': 0.0197840949996292}, {'dataset_scope': 'overall_with_promotion', 'best_model_name': 'HistGradientBoosting', 'best_ladder_step': 'L5_all_conservative_plus_promotion_indicator', 'best_oof_auc': 0.8211437468292977, 'train_valid_gap': 0.0391284644979338}, {'dataset_scope': 'overall_without_promotion', 'best_model_name': 'HistGradientBoosting', 'best_ladder_step': 'L4_all_conservative_behavior', 'best_oof_auc': 0.8136740303172799, 'train_valid_gap': 0.0379134937487572}, {'dataset_scope': 'promotion_only', 'best_model_name': 'RandomForest', 'best_ladder_step': 'L4_all_conservative_behavior', 'best_oof_auc': 0.7931624035577116, 'train_valid_gap': 0.0202161826770433}]
- AUC growth summary: `11_ladder_growth_summary.csv`에 기록.
- overfit/stability caveats: AUC 최고 후보와 후속/발표용 안전 후보를 구분했고, train-valid gap caution을 남겼다.
- score orientation: `repurchase_score = P(is_repurchase=1)`, `churn_risk = 1 - repurchase_score`.
- score 제한: selected OOF score는 score orientation audit용이며 세그먼트 후보, 타겟팅 기준, 최종 threshold로 해석하지 않는다.
- checks: `11_final_checks.csv` 기준 50/50 PASS.
- interpretation limits: 인과 주장, 통계적 유의성 주장, deployment readiness 주장 금지.
- risks to carry forward: review columns 제외 유지, group-aware CV 유지, SHAP/Optuna/threshold/segmentation은 후속 단계에서 별도 설계.
- next step recommendation: 12_model_baseline_comparison_260513.


## 2026-05-14 16:06:40 - 11b_baseline_growth_history_ladder_fix_260514

- step name: 11b_baseline_growth_history_ladder_fix_260514
- purpose: Step 11 feature ladder contamination 버그 수정. diff_between_w3_w2가 L2에 포함되던 오류를 수정한 canonical baseline growth history.
- why 11b was needed: 기존 Step 11의 L2_add_week2_retention에 diff_between_w3_w2(3주차-2주차 변화량)가 포함됨. Week3 정보가 L2에 누출되어 L1->L2 AUC 상승 해석이 오염됨.
- old 11 contamination issue: 07_AARRR_to_baseline_ladder_handoff.csv의 L2 열에 diff_between_w3_w2 오기재 -> handoff_cols()가 이를 L2에 포함. Step 11 L2 feature count was 14 (should be 13).
- corrected ladder summary: L2=13개(diff_between_w3_w2 제거), L3=21개(diff_between_w3_w2 정상 포함), L4=22개, L5=23개(overall_with_promotion 전용).
- dataset scopes: overall_without_promotion, overall_with_promotion, promotion_only, nonpromotion_only
- models used: DummyPrior(L0), LogisticRegression, HistGradientBoosting, RandomForest (L1-L5). 튜닝 미수행.
- best baseline by scope: [{'dataset_scope': 'nonpromotion_only', 'best_model_name': 'RandomForest', 'best_ladder_step': 'L4_all_conservative_behavior', 'best_oof_auc': 0.8303052527342334, 'train_valid_gap': 0.019784094999629208}, {'dataset_scope': 'overall_with_promotion', 'best_model_name': 'HistGradientBoosting', 'best_ladder_step': 'L5_all_conservative_plus_promotion_indicator', 'best_oof_auc': 0.8211437468292977, 'train_valid_gap': 0.039128464497933835}, {'dataset_scope': 'overall_without_promotion', 'best_model_name': 'HistGradientBoosting', 'best_ladder_step': 'L4_all_conservative_behavior', 'best_oof_auc': 0.8136740303172799, 'train_valid_gap': 0.03791349374875723}, {'dataset_scope': 'promotion_only', 'best_model_name': 'RandomForest', 'best_ladder_step': 'L4_all_conservative_behavior', 'best_oof_auc': 0.7931624035577116, 'train_valid_gap': 0.020216182677043303}]
- AUC growth summary: 11b_ladder_growth_summary.csv 참조
- overfit/stability caveats: AUC 최고 후보와 gap-safe 후보를 구분. train_valid_gap_audit 참조.
- score orientation: repurchase_score = P(is_repurchase=1), churn_risk = 1 - repurchase_score
- checks passed/failed: 11b_final_checks.csv 참조
- interpretation limits: 인과 주장, threshold, segmentation, deployment readiness 금지.
- risks to carry forward: review columns 제외 유지, group-aware CV 유지, SHAP/Optuna/threshold/segmentation은 후속 단계에서 별도 설계.
- next step recommendation: 12_model_baseline_comparison_260513 (11b 기준으로 진행).
- deprecated audit: 11b_deprecated_11_audit.csv
- contamination check: 11b_ladder_contamination_check.csv
- old Step 11은 pre-patch/deprecated로 보존. 삭제하지 않음.
- generated files: 25 CSVs, README.md, 7 PNG figures, review zip.

## 2026-05-14 | 11b semantic validation and interpretation patch

- why this patch was needed: 11b fixed the Step 11 L2 ladder contamination, but the semantic meaning of L1 still needed clearer wording.
- not a model rerun: this patch did not rerun modeling, did not change CV metrics, did not change OOF predictions, and did not edit old Step 11 outputs.
- L1 semantic clarification: L1 is early activation plus early concentration / early-only pattern family, not a week1-only temporal cutoff model.
- feature-family ladder vs temporal cutoff ladder: Step 11b ladder grows by feature family. At the day21 scoring point, all day0-20 behavior is already observable.
- is_only_w1 / is_w1_over_50pct interpretation: these are valid day21 features but not pure activation. They should be described as early-only, front-loaded, or early concentration patterns.
- 11b canonical status after patch: 11b can be used as the canonical corrected Step 11 after this semantic documentation patch.
- old 11 deprecated status: old Step 11 remains preserved as deprecated/pre-patch and should not be used for downstream modeling interpretation.
- next step recommendation: 12_model_baseline_comparison_260513.

## 2026-05-14 | 12_model_baseline_comparison_260513

- purpose: 고정 파라미터 기반 다양한 baseline model family를 11b canonical conservative setup에서 비교했다.
- input/canonical sources: 06 primary cohort, 05b conservative safe columns, 09b window validation, canonical 11b, 11b semantic patch.
- models compared: LogisticRegression, HistGradientBoosting, RandomForest, GradientBoosting, ExtraTrees, LightGBM, XGBoost.
- optional model availability: [{'model_name': 'LightGBM', 'import_available': 'yes', 'will_run': 'yes'}, {'model_name': 'XGBoost', 'import_available': 'yes', 'will_run': 'yes'}, {'model_name': 'CatBoost', 'import_available': 'no', 'will_run': 'no'}].
- best candidate by scope: [{'dataset_scope': 'nonpromotion_only', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8326691599692315, 'safer_candidate_model': 'XGBoost', 'safer_candidate_oof_auc': 0.8326691599692315}, {'dataset_scope': 'overall_with_promotion', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8234957455197796, 'safer_candidate_model': 'XGBoost', 'safer_candidate_oof_auc': 0.8234957455197796}, {'dataset_scope': 'overall_without_promotion', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8152121178143351, 'safer_candidate_model': 'XGBoost', 'safer_candidate_oof_auc': 0.8152121178143351}, {'dataset_scope': 'promotion_only', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8002004177794328, 'safer_candidate_model': 'XGBoost', 'safer_candidate_oof_auc': 0.8002004177794328}].
- comparison vs 11b: [{'dataset_scope': 'nonpromotion_only', '11b_best_model': 'RandomForest', '11b_best_oof_auc': 0.8303052527342334, '12_best_model': 'XGBoost', '12_best_oof_auc': 0.8326691599692315, 'delta_auc_12_minus_11b': 0.0023639072349981305}, {'dataset_scope': 'overall_with_promotion', '11b_best_model': 'HistGradientBoosting', '11b_best_oof_auc': 0.8211437468292977, '12_best_model': 'XGBoost', '12_best_oof_auc': 0.8234957455197796, 'delta_auc_12_minus_11b': 0.00235199869048186}, {'dataset_scope': 'overall_without_promotion', '11b_best_model': 'HistGradientBoosting', '11b_best_oof_auc': 0.8136740303172799, '12_best_model': 'XGBoost', '12_best_oof_auc': 0.8152121178143351, 'delta_auc_12_minus_11b': 0.001538087497055196}, {'dataset_scope': 'promotion_only', '11b_best_model': 'RandomForest', '11b_best_oof_auc': 0.7931624035577116, '12_best_model': 'XGBoost', '12_best_oof_auc': 0.8002004177794328, 'delta_auc_12_minus_11b': 0.007038014221721234}].
- train-valid gap caveats: see `12_train_valid_gap_audit.csv`; high AUC is not final model selection.
- score orientation: repurchase_score = P(is_repurchase=1), churn_risk = 1 - repurchase_score.
- interpretation limits: no causality, no uplift/campaign effect, no deployment readiness, no threshold, no segmentation.
- risks to carry forward: review columns remain excluded; optional model availability can vary; SHAP and Optuna remain later.
- next step recommendation: decide candidate path, then 14_optuna_candidate_tuning_260513 or 16_SHAP after model candidate decision.

## 2026-05-14 | 12_model_baseline_comparison_rebuild_260514

- why rebuild was needed: prior Step 12 was AUC-centered and lacked required top-k operating diagnostics and calibration/decile checks for marketing execution review.
- old Step 12 superseded: `12_model_baseline_comparison_260513` is preserved as pre-rebuild/deprecated.
- models compared: LogisticRegression, HistGradientBoosting, RandomForest, GradientBoosting, ExtraTrees, LightGBM, XGBoost.
- optional model availability: [{'model_name': 'LightGBM', 'import_available': 'yes', 'will_run': 'yes'}, {'model_name': 'XGBoost', 'import_available': 'yes', 'will_run': 'yes'}, {'model_name': 'CatBoost', 'import_available': 'no', 'will_run': 'no'}].
- AUC results: [{'dataset_scope': 'nonpromotion_only', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8326691599692315}, {'dataset_scope': 'overall_with_promotion', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8234957455197796}, {'dataset_scope': 'overall_without_promotion', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8152121178143351}, {'dataset_scope': 'promotion_only', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8002004177794328}].
- operating top-k metrics: see `12r_operating_metrics_at_k.csv`; top-k ranks by churn_risk descending and is diagnostic only.
- calibration caveats: decile summaries are descriptive diagnostics, not deployment calibration guarantees.
- best candidate by scope: [{'dataset_scope': 'nonpromotion_only', 'best_auc_model': 'XGBoost', 'operating_metric_candidate_model': 'XGBoost', 'safer_candidate_model': 'XGBoost'}, {'dataset_scope': 'overall_with_promotion', 'best_auc_model': 'XGBoost', 'operating_metric_candidate_model': 'XGBoost', 'safer_candidate_model': 'XGBoost'}, {'dataset_scope': 'overall_without_promotion', 'best_auc_model': 'XGBoost', 'operating_metric_candidate_model': 'XGBoost', 'safer_candidate_model': 'XGBoost'}, {'dataset_scope': 'promotion_only', 'best_auc_model': 'XGBoost', 'operating_metric_candidate_model': 'XGBoost', 'safer_candidate_model': 'XGBoost'}].
- stability-aware candidate: [{'dataset_scope': 'nonpromotion_only', 'recommended_candidate_for_14': 'XGBoost', 'recommended_candidate_for_16': 'XGBoost', 'highest_lift10_model': 'XGBoost'}, {'dataset_scope': 'overall_with_promotion', 'recommended_candidate_for_14': 'XGBoost', 'recommended_candidate_for_16': 'XGBoost', 'highest_lift10_model': 'XGBoost'}, {'dataset_scope': 'overall_without_promotion', 'recommended_candidate_for_14': 'XGBoost', 'recommended_candidate_for_16': 'XGBoost', 'highest_lift10_model': 'XGBoost'}, {'dataset_scope': 'promotion_only', 'recommended_candidate_for_14': 'XGBoost', 'recommended_candidate_for_16': 'XGBoost', 'highest_lift10_model': 'XGBoost'}].
- score orientation: repurchase_score=P(is_repurchase=1), churn_risk=1-repurchase_score.
- interpretation limits: no causality, no uplift/campaign effect, no deployment readiness, no threshold, no segmentation.
- risks to carry forward: review columns excluded, optional packages vary, high AUC may overfit, top-k is not campaign policy.
- next step recommendation: decide candidate path, then 14_optuna_candidate_tuning_260513 or 16_SHAP; optional lightweight 13 synthesis if documentation sequence requires.

## 2026-05-14 23:24:08 | Step 12 deprecated outputs isolation

- Purpose: 기존 Step 12 관련 산출물을 삭제하지 않고 archive로 격리했다.
- Archive root: $ARCHIVE_ROOT
- Reason: 기존 12_model_baseline_comparison_260513은 AUC 중심 비교였고, 광일이 리뷰에서 요구한 top-k/lift/calibration 운영 지표가 부족했다.
- Reason: 기존 12_model_baseline_comparison_rebuild_260514는 운영 지표를 추가했지만, stability-aware candidate 산정 로직에 문제가 있어 canonical Step 12로 확정하지 않는다.
- Action: 기존 12/12r notebook, model outputs, figure outputs, review zips, cleanup review logs를 $ARCHIVE_ROOT 아래로 이동했다.
- Important: 기존 12/12r은 삭제가 아니라 deprecated/archive 처리했다.
- Canonical policy: 다음 Step 12는 12_model_baseline_comparison_canonical_260514 또는 이에 준하는 새 canonical run으로 다시 생성한다.
- Manifest: $MANIFEST
- Interpretation limit: archived outputs are retained for audit trail only and must not be used as final Step 12 evidence.

## 2026-05-14 | 12_model_baseline_comparison_canonical_260514

- Canonical rebuild reason: previous Step 12 was AUC-centered and lacked operating metrics; previous Step 12r added operating metrics but had candidate-selection logic risk, especially for stability-aware selection.
- Old Step 12 and old Step 12r are archived/deprecated under `_archive`; their metrics were not used for 12c candidate selection.
- Models compared: LogisticRegression, HistGradientBoosting, RandomForest, GradientBoosting, ExtraTrees, LightGBM, XGBoost.
- Optional model availability: [{'model_name': 'LogisticRegression', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'HistGradientBoosting', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'RandomForest', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'GradientBoosting', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'ExtraTrees', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'LightGBM', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'XGBoost', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'CatBoost', 'will_run': 'no', 'unavailable_reason': 'module not installed'}].
- AUC results and fold stability are in `12c_model_comparison_summary.csv`; AUC is predictive performance evidence only.
- Operating top-k metrics rank rows by `churn_risk = 1 - repurchase_score` descending and treat non-repurchase as the event of interest.
- Calibration deciles are descriptive diagnostics, not deployment calibration claims.
- Highest AUC candidate by scope: [{'dataset_scope': 'overall_without_promotion', 'highest_auc_candidate': 'XGBoost'}, {'dataset_scope': 'overall_with_promotion', 'highest_auc_candidate': 'XGBoost'}, {'dataset_scope': 'promotion_only', 'highest_auc_candidate': 'XGBoost'}, {'dataset_scope': 'nonpromotion_only', 'highest_auc_candidate': 'XGBoost'}].
- Operating metric candidate by scope: [{'dataset_scope': 'overall_without_promotion', 'operating_metric_candidate': 'XGBoost'}, {'dataset_scope': 'overall_with_promotion', 'operating_metric_candidate': 'XGBoost'}, {'dataset_scope': 'promotion_only', 'operating_metric_candidate': 'XGBoost'}, {'dataset_scope': 'nonpromotion_only', 'operating_metric_candidate': 'XGBoost'}].
- Stability-aware candidate by scope: [{'dataset_scope': 'overall_without_promotion', 'stability_aware_candidate': 'GradientBoosting'}, {'dataset_scope': 'overall_with_promotion', 'stability_aware_candidate': 'GradientBoosting'}, {'dataset_scope': 'promotion_only', 'stability_aware_candidate': 'GradientBoosting'}, {'dataset_scope': 'nonpromotion_only', 'stability_aware_candidate': 'RandomForest'}].
- Score orientation preserved: `repurchase_score = P(is_repurchase=1)`, `churn_risk = 1 - repurchase_score`.
- Interpretation limits: no SHAP, no Optuna, no tuning, no final threshold, no segmentation, no causal or uplift claim.
- Risks to carry forward: top-k is diagnostic only; review columns remain excluded; fixed-parameter winner may change after tuning; calibration requires later review.
- Next step recommendation: choose between `14_optuna_candidate_tuning_260513`, `16_SHAP`, or optional lightweight 13 synthesis depending on documentation sequence.

## 2026-05-14 | 광일이 deep review 피드백 반영 및 Step 12 재정리 메모

- Context: 광일이가 `(260513)ott_churn_master_plan.docx`를 LLM으로 심층 검토한 결과를 공유했다. 해당 피드백은 프로젝트 방향을 폐기하라는 내용이 아니라, 범위와 주장 강도를 보수적으로 조정하라는 내용에 가깝다.
- Review summary: 큰 방향은 타당하나 원안 그대로 3주 안에 전부 수행하기에는 과하므로 MVP 범위와 품질 gate를 분명히 해야 한다.
- Key feedback 1: 핵심 문장인 “100원딜 고객과 비프로모션 고객은 행동 신호가 다르므로”는 검증 전 결론처럼 보일 수 있다. 앞으로는 “행동 신호가 다르게 나타나는지 검증하고, 차이가 확인되는 병목에 한해 전략을 설계한다”로 표현한다.
- Key feedback 2: USER_KEY 중복이 있으므로 unique-user-level 분석이라고 말하면 안 된다. 분석 단위는 row-level / subscription-event-level로 유지한다.
- Key feedback 3: derived feature가 정말 day0~20 기준인지 반드시 검증해야 한다. 이 우려는 09b raw view window validation에서 core usage 8개 feature mismatch 0건으로 상당 부분 해소되었으나, genre/new movie ratio 계열의 일부 caveat는 계속 관리한다.
- Key feedback 4: AUC는 primary metric으로 사용할 수 있지만, 마케팅 실행 관점에서는 AUC만으로 부족하다. top-k precision, recall, lift@10/20, calibration/decile 같은 operating metrics를 추가해야 한다.
- Key feedback 5: 모델 범위를 무리하게 키우면 품질이 떨어질 수 있다. 모델 zoo, Optuna, SHAP, segmentation은 gate를 통과한 뒤 순차적으로 진행한다.
- Key feedback 6: SHAP은 원인이 아니라 model explanation이다. SHAP 결과는 EDA와 일치할 때만 본문 주장으로 사용한다.
- Key feedback 7: Referral은 현재 데이터에서 직접 관측되지 않는다. Referral은 후속 실험 제안으로만 다룬다.

### Step 12 관련 정리

- Existing Step 12 `12_model_baseline_comparison_260513` status: deprecated / archived.
- Reason: 고정 파라미터 모델군 비교 자체는 수행했지만 AUC 중심이었고, 광일이 리뷰에서 요구한 top-k/lift/calibration 운영 지표가 부족했다.
- Existing Step 12 rebuild `12_model_baseline_comparison_rebuild_260514` status: deprecated / archived.
- Reason: top-k와 calibration을 추가했지만, stability-aware candidate 산정 로직에 문제가 있었다. 특히 safer/stability-aware candidate가 실제 gap/fold stability 기준으로 분리되지 않고 XGBoost로 과도하게 수렴했다.
- Archive policy: 기존 12/12r 산출물은 삭제하지 않고 archive/deprecated 처리했다. 최종 Step 12 근거로 사용하지 않는다.
- Cleanup review policy: `_cleanup_review`는 기존 12/12r 격리 근거 로그로 사용했고, 이후 archive 대상이다.
- Current canonical policy: 다음 Step 12는 `12_model_baseline_comparison_canonical_260514`를 새로 생성한다.
- New canonical Step 12 requirements:
  - old 12/12r metrics 사용 금지
  - 11b canonical baseline과 11b semantic patch 기준 사용
  - conservative safe features 22개 기준 유지
  - review/forbidden columns 사용 금지
  - USER_KEY는 group key로만 사용
  - StratifiedGroupKFold 유지
  - AUC/AP/Brier/train-valid gap/fold stability 계산
  - churn_risk 기준 top-k precision, recall, lift@10/20 계산
  - calibration/risk decile summary 포함
  - highest AUC candidate, operating metric candidate, stability-aware candidate를 분리
  - stability-aware candidate를 highest AUC model로 자동 고정하지 않음
  - top-k 지표는 운영 진단용이며 campaign threshold가 아님
- Next action: `12_model_baseline_comparison_canonical_260514` 실행 후, 그 결과만 canonical Step 12로 사용한다.