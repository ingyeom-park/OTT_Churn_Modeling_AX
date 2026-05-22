# PUBLIC 15 — Four-Model OOF Score Generation Results

**Date:** 2026-05-20  
**Scope:** LogisticRegression × {promo0, promo1}, GradientBoosting × {promo0, promo1}  
**Split:** StratifiedKFold(n_splits=5, shuffle=True, random_state=42)  
**Split warning:** USER_NUM absent in input CSVs. USER_KEY duplicates: promo0=56, promo1=1. User domain-confirmed dedup handled upstream. Status: WARN_WITH_USER_CONFIRMATION.

---

## OOF Metric Summary

| model_family | scope | oof_roc_auc | oof_pr_auc | suspicious_high_auc_flag |
|---|---|---|---|---|
| LogisticRegression | promo0 | 0.864944 | 0.951351 | OK |
| LogisticRegression | promo1 | 0.839502 | 0.917268 | OK |
| GradientBoosting | promo0 | 0.880476 | 0.957362 | OK |
| GradientBoosting | promo1 | 0.859147 | 0.929921 | OK |

All 4 combos: suspicious_high_auc_flag=OK. All shap_readiness=READY, segmentation_readiness=READY.

PR-AUC ≥ 0.90 alone does NOT trigger suspicious_high_auc_flag. Flag is triggered only by ROC-AUC ≥ 0.99 or large train-valid gap. See PUBLIC 12 hotfix policy.

---

## Feature Policy

- 75 features from `feature_manifest_used.csv` (same across all 4 model/scope combos)
- `retention_w2_ratio`, `retention_w3_ratio` excluded
- `log_retention_w2_ratio`, `log_retention_w3_ratio` included
- `is_churn_prevented` included as approved context feature (past churn prevention response history, NOT current-cycle post-treatment)
- `is_promotion` present in CSV but excluded from features per manifest policy
- `USER_KEY` excluded from features

---

## Model Params (from existing final_result.csv — no Optuna rerun)

| model_family | scope | key params |
|---|---|---|
| LogisticRegression | promo0 | C=0.1638, class_weight=balanced, best_trial=84 |
| LogisticRegression | promo1 | C=0.0509, class_weight=balanced, best_trial=61 |
| GradientBoosting | promo0 | n_estimators=246, lr=0.0490, max_depth=2, best_trial=77 |
| GradientBoosting | promo1 | n_estimators=219, lr=0.0446, max_depth=3, best_trial=76 |

---

## Output Files

| file | description | rows |
|---|---|---|
| `15_oof_score_long.csv` | long format — all 4 combos stacked | 46,194 |
| `15_oof_score_wide_promo0.csv` | wide format — promo0, LR+GB side-by-side | 11,193 |
| `15_oof_score_wide_promo1.csv` | wide format — promo1, LR+GB side-by-side | 11,904 |
| `15_oof_metric_summary.csv` | OOF ROC-AUC / PR-AUC per combo | 4 |
| `15_oof_fold_distribution_check.csv` | per-fold ROC-AUC / PR-AUC / val_pos / val_neg | 20 |
| `15_gb_lr_high_risk_overlap.csv` | LR/GB high-risk overlap at thresholds 0.5/0.6/0.7 | 12 |
| `15_oof_readiness_for_shap_segmentation.csv` | READY/WARN/BLOCK per combo | 4 |
| `15_oof_input_validation.csv` | pre-flight input validation | 14 |
| `15_model_config_extraction.csv` | params extracted from final_result.csv | 4 |
| `15_oof_feature_policy_check.csv` | feature inclusion/exclusion audit | 2 |
| `15_oof_split_policy_check.csv` | split method audit | 2 |

---

## Score Columns

- `repurchase_score_oof` = P(is_repurchase=1) from held-out fold
- `churn_risk_score_oof` = 1 − repurchase_score_oof
- Higher `churn_risk_score_oof` → higher churn risk

---

## Interpretation Guardrail

OOF score는 final campaign target이 아니다.

다음 단계에서 사용할 row-level risk evidence다:
- GB/LR high-risk overlap 검수
- SHAP 대상 모델 선정 보조
- segmentation rule 설계 보조
- promo1 중심 risk profile 확인
- promo0 비교군 risk profile 확인

OOF score가 생성되었다고 해서 바로 SHAP, segmentation, dashboard, business action으로 넘어가는 것이 아니다.

---

## Notebook

- `PUBLIC/notebooks/15_oof_score_or_sensitivity_260520/15_four_model_oof_score_generation_260520.ipynb`
- Executed: `15_four_model_oof_score_generation_260520_executed.ipynb`
