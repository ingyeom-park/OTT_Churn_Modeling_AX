# four_model_comparison_review_hotfix_user_confirmed

작성일: 2026-05-20

---

## Purpose

기존 12 four-model comparison review의 해석 오류를 사용자 확인 사항에 맞게 보정한다. 모델 재실행, 노트북 실행, OOF 생성은 수행하지 않는다.

---

## User corrections applied

1. ROC-AUC를 primary metric으로 확정. PR-AUC는 secondary metric.
2. is_churn_prevented는 과거 이력 flag로 확인. leakage FAIL이 아니라 approved context feature with caveat.
3. split 기준은 USER_NUM. USER_KEY 중복 기반 자동 FAIL 제거.
4. 07~10은 pending validation. 현재 12 review 진행을 차단하지 않음.

---

## Metric interpretation correction

- 기존 suspicious_high_auc_flag는 PR-AUC >= 0.90 트리거였음. 이를 보정함.
- 보정 후 모든 4개 모델의 suspicious_high_auc_flag_after = 0.
- ROC-AUC 범위 0.844~0.883은 high_but_plausible_pending_standard_checks로 기록.
- ROC-AUC 이상 여부는 train-valid gap, test gap, leakage feature 유무 기준으로 판단.

| model | scope | ROC-AUC | PR-AUC | flag_before | flag_after |
|---|---|---|---|---|---|
| LR | promo0 | 0.860 | 0.949 | 1 | 0 |
| LR | promo1 | 0.844 | 0.918 | 1 | 0 |
| GB | promo0 | 0.883 | 0.957 | 1 | 0 |
| GB | promo1 | 0.862 | 0.928 | 1 | 0 |

---

## is_churn_prevented correction

- 이전: leakage_FAIL
- 보정 후: approved_context_feature_with_interpretation_caveat
- 의미: 과거 포인트 수령 또는 churn prevention event 긍정 반응 이력
- 금지 표현: current-cycle post-treatment effect / current intervention caused repurchase
- 안전한 표현: past churn prevention response history

---

## Split policy correction

- split 기준: USER_NUM (사용자 확인)
- USER_NUM 컬럼은 현재 입력 CSV에 없음. USER_KEY 존재. promo0 중복 56건 / promo1 중복 1건.
- 이 중복이 곧바로 split leakage를 의미하지는 않음. USER_NUM upstream dedup 사용자 확인.
- split 상태: WARN_needs_verification (FAIL 아님)
- GroupKFold 미사용은 자동 FAIL 아님.

---

## 07~10 pending validation status

07~10은 현재 일정으로 인해 temporarily deferred 상태다. pending validation이며 skipped가 아니다. 이 상태는 12 review 진행을 차단하지 않는다.

---

## OOF readiness after correction

- oof_generation_allowed_without_user_approval: no
- oof_generation_allowed_after_user_approval: conditional yes
- 사용자가 승인하면 OOF score table 생성으로 진행 가능
- 사용자 선택: OOF 먼저 vs 07~10 validation 먼저

---

## What was not done

- 모델 실행 없음
- 노트북 실행 없음
- OOF score table 생성 없음
- Optuna 없음
- SHAP 없음
- segmentation 없음
- raw source CSV 수정 없음
- park.ingyeom 폴더 수정 없음
- final model selection 없음

---

## Safe wording

- ROC-AUC is the primary metric.
- PR-AUC is a secondary metric and high PR-AUC alone is not leakage evidence.
- is_churn_prevented is an approved historical context feature with interpretation caveat.
- Split policy should be interpreted under USER_NUM-based duplicate handling, not old USER_KEY caveat.
- 07~10 remain pending validation.
- OOF generation requires user approval.

## Unsafe wording

- PR-AUC over 0.90 proves leakage.
- is_churn_prevented is automatically leakage.
- GroupKFold absence is automatically FAIL because of USER_KEY.
- 07~10 are skipped. (use: 07~10 remain pending validation, temporarily deferred due to schedule)
- OOF was generated.
- SHAP or segmentation can start immediately.
- final model selected.

---

## Next action

사용자가 이 review zip을 검수한다. 검수 후 OOF score table 생성 여부를 승인한다.
