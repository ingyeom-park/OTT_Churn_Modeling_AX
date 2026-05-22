# PUBLIC 12 Review Hotfix — User-Confirmed Interpretation Correction

작성일: 2026-05-20  
작업 성격: 해석 보정 / 모델 재실행 없음

---

## 목적

기존 PUBLIC 12 four-model comparison review에서 발생한 과잉 차단 표현 3가지를 사용자 확인 사항에 맞게 보정했다.

1. suspicious_high_auc_flag가 PR-AUC 기준으로 설정된 것 → ROC-AUC 기준으로 보정
2. is_churn_prevented를 leakage FAIL로 처리한 것 → approved context feature with caveat로 보정
3. USER_KEY 중복 기반 GroupKFold 자동 FAIL → USER_NUM 기준 WARN_needs_verification으로 보정

---

## output folder

```
PUBLIC/results/12_model_family_comparison_260520/four_model_comparison_review_hotfix_user_confirmed/
├── README.md
├── 12_metric_interpretation_correction.csv
├── 12_is_churn_prevented_policy_correction.csv
├── 12_split_policy_usernum_correction.csv
├── 12_oof_readiness_user_confirmed_update.csv
└── 12_hotfix_summary.md
```

---

## 다음 단계

사용자가 review zip을 검수하고, OOF score table 생성 여부를 승인한다.

- Option A: 사용자 승인 후 OOF score table 생성으로 진행
- Option B: 07~10 validation 완료 후 OOF 진행
