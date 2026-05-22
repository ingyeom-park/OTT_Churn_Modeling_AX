# 12 Review User-Confirmed Interpretation Hotfix Summary

작성일: 2026-05-20  
작업 성격: 모델 재실행 없음 / 기존 12 review 해석 보정

---

## 이번 hotfix의 목적

기존 12 four-model comparison review에서 PR-AUC 기반 과잉 차단 표현, is_churn_prevented 자동 FAIL, USER_KEY 기반 split FAIL 언어가 사용됐다. 사용자 확인 사항 4개를 반영해 이 해석들을 보정했다.

---

## 사용자 확인 사항 4개 반영 결과

### 1. ROC-AUC가 primary metric

- primary_metric: ROC-AUC
- secondary_metric: PR-AUC
- PR-AUC가 0.90 이상이라는 이유만으로 suspicious_high_auc_flag를 1로 두지 않는다.
- 기존 suspicious_high_auc_flag는 test_pr_auc >= 0.90 트리거였다. 이를 전면 수정했다.
- 보정 후 ROC-AUC 범위: LR 0.844~0.860 / GB 0.862~0.883
- 이 범위는 high_but_plausible_pending_standard_checks로 기록한다.
- ROC-AUC 자체가 비정상적으로 높거나 train-valid gap이 큰 경우에만 suspicious flag를 사용한다.

### 2. is_churn_prevented는 approved context feature with interpretation caveat

- 이전 상태: leakage_FAIL
- 보정 후 상태: approved_context_feature_with_interpretation_caveat
- 사용자 확인 의미: 과거 포인트 수령 또는 churn prevention event 긍정 반응 이력 flag
- 현재 개입의 인과효과로 말하지 않는다.
- 안전한 해석: "과거 churn prevention 반응 이력"
- 금지 표현: "current-cycle post-treatment effect", "current intervention caused repurchase"

### 3. split 기준은 USER_NUM

- 사용자 확인: USER_NUM 기준 중복 처리 완료
- 입력 CSV에서 USER_NUM 컬럼은 확인되지 않았다. USER_KEY 컬럼이 존재하며 promo0 56건 / promo1 1건 중복이 있다.
- 이 수치가 곧바로 split leakage를 의미하지는 않는다. USER_NUM 기준 dedup이 upstream에서 처리됐다는 사용자 확인을 따른다.
- USER_KEY 중복을 근거로 GroupKFold 미사용을 자동 FAIL 처리하지 않는다.
- split 상태: WARN_needs_verification (FAIL 아님)

### 4. 07~10은 pending validation (skipped 아님)

- 현재 바쁜 일정으로 나중에 처리한다.
- 이 사실은 README와 note.md에 유지된다.
- 07~10 pending을 이유로 현재 12 comparison 정리와 OOF 준비 판단을 전면 차단하지 않는다.

---

## 이번 작업에서 수행한 것

- 기존 12 review CSV 내용 확인
- 모델 입력 CSV에서 USER_NUM/USER_KEY 컬럼 및 중복 여부 직접 확인
- feature_manifest_used.csv에서 is_churn_prevented 포함 여부 확인
- correction CSV 4개 생성
- README, hotfix_summary, note append, final_checks, zip 생성

---

## 이번 작업에서 수행하지 않은 것

- 모델 실행 없음
- 노트북 실행 없음
- OOF score table 생성 없음
- Optuna 없음
- SHAP 없음
- segmentation 없음
- raw source CSV 수정 없음
- park.ingyeom 폴더 수정 없음

---

## 현재 상태 요약

이번 결과는 final model selection이 아니다. OOF 전 해석 보정 및 readiness update다.

OOF score table은 사용자 승인 후 별도 goal로 진행한다.

사용자 선택지:
- Option A: 사용자 승인 후 OOF score table 생성으로 바로 진행
- Option B: 07~10 validation을 먼저 완료한 뒤 OOF 진행
