# 06c3 Corrected Model Benchmark Report

## Scope
- This stage benchmarks corrected strict-core v2c datasets only.
- No SHAP, segmentation, or business simulation is created in this stage.
- w1_4 is treated as late-period comparison only, not as an official early-warning model.

## Feature set mapping
- pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence -> pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence (exact, window=w1_3)
- pruned_w1_3_membership_usage_only_without_product_code_without_watch_presence -> pruned_w1_3_membership_usage_only_without_product_code_without_watch_presence (exact, window=w1_3)
- pruned_w1_3_genre_ratio_added_without_product_code_without_watch_presence -> pruned_w1_3_genre_ratio_added_without_product_code_without_watch_presence (exact, window=w1_3)
- pruned_w1_2_early_reference_without_product_code_without_watch_presence -> pruned_w1_2_early_reference_without_product_code_without_watch_presence (exact, window=w1_2)
- pruned_w1_4_late_period_comparison_without_product_code_without_watch_presence -> pruned_w1_4_late_period_comparison_without_product_code_without_watch_presence (exact, window=w1_4)
- full_exploratory_w1_3 -> full_exploratory_w1_3 (exact, window=w1_3)

## Required answers
1. Models evaluated: CatBoostClassifier, DummyClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier, HistGradientBoostingClassifier_OptunaTuned, LGBMClassifier, LGBMClassifier_OptunaTuned, LogisticRegression, RandomForestClassifier, XGBClassifier.
2. Optional models unavailable: None.
3. Optuna available: True.
4. Models tuned: LGBMClassifier, HistGradientBoostingClassifier.
5. Tuning improvement: LGBMClassifier: 0.001778 AUC gain; HistGradientBoostingClassifier: 0.000489 AUC gain
6. Highest AUC: LGBMClassifier on pruned_w1_4_late_period_comparison_without_product_code_without_watch_presence with AUC 0.895722.
7. Best top-decile lift: LGBMClassifier on pruned_w1_4_late_period_comparison_without_product_code_without_watch_presence with lift 2.963339.
8. Most defensible official model: HistGradientBoostingClassifier on pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence.
9. Official model changes from Stage 06c2: False.
10. Downstream rerun decision: Stage 07c and Stage 08c remain aligned with the Stage 06c2 HGB official model; Stage 09c also remains aligned.
11. w1_4 is not official early-warning because it uses the late-period observation window and is only a comparison view.
12. Mentor presentation: present the corrected v2c benchmark ladder, keep HGB as official unless a clearly stable non-tuned challenger exceeds it, and show tuned results as experimental only.

## Official decision
- Recommendation: HistGradientBoostingClassifier.
- Feature set: pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence.
- Holdout AUC: 0.863473.
- Churn-risk AP: 0.703717.
- Top-decile lift: 2.807374.
- Reason: Stage 06c2 HGB remains the most defensible official model because no fixed challenger cleared a material, stable improvement threshold on the same safe feature set.
