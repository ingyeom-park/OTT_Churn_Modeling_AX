# PUBLIC 15 — Four-Model OOF Score Generation Handoff

**Date:** 2026-05-20  
**Task:** Row-level OOF score generation for 4 model/scope combinations

---

## What was done

1. Pre-flight validation — all 14 input items verified (PASS)
2. Model params extracted from existing `final_result.csv` — no Optuna rerun
3. Feature policy confirmed — 75 features, raw retention excluded, log retention used
4. Split policy confirmed — StratifiedKFold(n_splits=5, shuffle=True, random_state=42), WARN_WITH_USER_CONFIRMATION
5. OOF generation notebook written and executed
6. All output files generated and verified

---

## OOF Results Summary

| model_family | scope | oof_roc_auc | oof_pr_auc | flag | readiness |
|---|---|---|---|---|---|
| LogisticRegression | promo0 | 0.864944 | 0.951351 | OK | READY |
| LogisticRegression | promo1 | 0.839502 | 0.917268 | OK | READY |
| GradientBoosting | promo0 | 0.880476 | 0.957362 | OK | READY |
| GradientBoosting | promo1 | 0.859147 | 0.929921 | OK | READY |

---

## Output File Locations

**Results:**  
`PUBLIC/results/15_oof_score_or_sensitivity_260520/four_model_oof_scores/`

- `15_oof_score_long.csv` — 46,194 rows
- `15_oof_score_wide_promo0.csv` — 11,193 rows
- `15_oof_score_wide_promo1.csv` — 11,904 rows
- `15_oof_metric_summary.csv`
- `15_oof_fold_distribution_check.csv`
- `15_gb_lr_high_risk_overlap.csv`
- `15_oof_readiness_for_shap_segmentation.csv`
- `README.md`

**Notebooks:**  
`PUBLIC/notebooks/15_oof_score_or_sensitivity_260520/`
- `15_four_model_oof_score_generation_260520.ipynb`
- `15_four_model_oof_score_generation_260520_executed.ipynb`

**Handoff:**  
`PUBLIC/handoff/PUBLIC_15_four_model_oof_score_generation_260520/`
- `15_oof_input_validation.csv`
- `15_source_fingerprint_before_after.csv`
- `PUBLIC_15_four_model_oof_score_generation_final_checks.csv`

---

## Constraints Confirmed

- No Optuna rerun
- No SHAP
- No segmentation
- No final model selection
- No raw source modification
- No park.ingyeom folder modification

---

## Next Steps (pending user review)

1. User reviews OOF metric interpretation (ROC-AUC range, GB vs LR delta, promo0 vs promo1 gap)
2. User reviews high-risk overlap at threshold 0.5/0.6/0.7
3. If OOF accepted: proceed to SHAP target model selection
4. Then: segmentation rule design
