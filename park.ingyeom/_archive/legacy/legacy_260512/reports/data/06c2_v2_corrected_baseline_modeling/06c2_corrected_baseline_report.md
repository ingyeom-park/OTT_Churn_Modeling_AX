# 06c2 Corrected Baseline Modeling Report

- rows_after_strict_core: 23115
- target_distribution: {'repurchase_count': 16591, 'non_repurchase_count': 6524, 'repurchase_rate': 0.7177590309322951}
- corrected_w1_1_auc: 0.6283372245897181
- corrected_w1_2_auc: 0.7418050140538581
- corrected_w1_3_official_pruned_auc: 0.8629394097379637
- corrected_w1_4_late_period_auc: 0.8936589899356242
- old_pre_02c_official_auc: 0.8046508435579209
- strict_preprocessing_story_change: Compare corrected official AUC and row count against old 06g; strict-core preprocessing removed problematic rows and this 06c2 table is now the authoritative baseline.
- official_model_now: HistGradientBoostingClassifier on pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence
- deprecated_outputs: Pre-02c Stage 04/05/06/06g outputs are deprecated/provisional for final claims; corrected 04c/05c/06c2 supersede them for baseline modeling.
- rerun_next: Rerun SHAP only for the corrected official model, then rerun downstream segmentation/simulation only after corrected SHAP is accepted.
- shap_required: Yes. SHAP was intentionally not run here and is required later for corrected official-model explanations.
- GroupKFold: not run in this combined rebuild; holdout GroupShuffleSplit only was used and documented.
- Interpretation: Logistic coefficients are associations only. Positive means pushes toward repurchase; negative means higher churn-risk association.
