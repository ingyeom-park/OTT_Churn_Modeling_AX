# 06c3 Final Model for SHAP Recommendation

Recommended official model: HistGradientBoostingClassifier
Recommended feature set: `pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence`
Window: w1_3
Holdout ROC AUC: 0.863473
Churn-risk AP: 0.703717
Top-decile lift: 2.807374

This recommendation is based on corrected strict-core v2c data, excludes product_code and watch-presence shortcuts, excludes full exploratory feature sets, and does not use w1_4 as an official early-warning model.

Decision against Stage 06c2: unchanged
Reason: Stage 06c2 HGB remains the most defensible official model because no fixed challenger cleared a material, stable improvement threshold on the same safe feature set.
