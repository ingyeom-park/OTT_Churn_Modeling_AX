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