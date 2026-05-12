# 06d v2 Multicollinearity and Feature Redundancy Audit

Generated at: 2026-05-11T16:17:46

## Scope
This stage audits feature redundancy and multicollinearity only. It does not train production models, tune models, run Optuna, run SHAP, create segmentation, or create business simulation.

## 1. Are there severe multicollinearity or redundancy issues?
Yes. Pearson high-correlation pairs at abs(corr) >= 0.95: 15. VIF >= 10 features: 38. Extreme/infinite VIF features: 27. This is a serious interpretation issue, even if tree models can still predict with correlated inputs.

## 2. Which feature groups are most redundant?
The most redundant groups are weekly usage volume, usage ratios/deltas, genre watch-time/session-count proxies, genre ratio compositions, and coverage/missing complement variables.

## 3. Which variables should not be interpreted individually?
Do not interpret total/weekly watch-time, weekly ratios, deltas, genre watch-time, genre session-count, and complement flags as independent evidence. They are structurally related.

## 4. Which variables should be grouped as usage behavior?
Group total watch time, weekly watch time, sessions, active days, first/last watch rel_day, ratios, deltas, max-day concentration, and short-watch behavior as usage behavior.

## 5. Which variables should be grouped as genre/content proxies?
Group genre ratios, top genre, genre entropy, genre watch-time, genre session-count, and release-month proxies as content/genre proxy signals.

## 6. Which variables are structurally derived from others?
Weekly totals, ratios, deltas, genre ratio sums, genre watch-time sums, and coverage/missing complements are structurally derived or compositional.

## 7. Which variables remain safe to explain individually?
Relatively safer standalone variables include basic membership context such as max_screen, age, gender, payment_device, and billing_method, but price/product/promotion still require cohort-policy caution.

## 8. How should this change SHAP interpretation?
SHAP should be interpreted mostly at feature-family or grouped-concept level. Individual SHAP ranks can split credit across redundant derivatives, so rank order should not be read as independent causal importance.

## 9. Should any feature be removed before final presentation or future modeling?
No current production model is changed here. For future reduced-feature modeling, use one representative from each structural group and consider dropping complements, totals plus components, and duplicated volume proxies.

## 10. What should be told to the mentor?
The high AUC is not only target-adjacent per Stage 06c; it also relies on many correlated and structurally related behavior/content variables. Prediction may remain valid for ranking, but interpretation must be grouped and cautious.

## Key Output Tables
- Feature inventory: `park.ingyeom/reports/tables/06d_v2_multicollinearity_redundancy_audit/06d_feature_inventory.csv`
- High corr pairs: `park.ingyeom/reports/tables/06d_v2_multicollinearity_redundancy_audit/06d_high_corr_pairs_pearson.csv`
- VIF: `park.ingyeom/reports/tables/06d_v2_multicollinearity_redundancy_audit/06d_vif_results.csv`
- Reduced recommendation: `park.ingyeom/reports/tables/06d_v2_multicollinearity_redundancy_audit/06d_reduced_feature_recommendation.csv`
