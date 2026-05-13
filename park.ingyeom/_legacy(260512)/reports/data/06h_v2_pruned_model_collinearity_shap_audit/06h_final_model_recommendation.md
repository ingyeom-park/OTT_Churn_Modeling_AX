# 06h Final Model Recommendation

## Official Candidate
The official final model candidate is `pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence` with `HistGradientBoostingClassifier`.

- AUC: 0.862148
- churn-risk PR AUC: 0.700385
- top-decile lift: 2.755381
- full 1~3 week information: Y
- product_code excluded by default: Y
- watch-presence shortcut excluded by default: Y
- first/last watch timing features excluded: Y
- ratio/delta structural duplicates excluded: Y
- genre watch_time/session_count usage proxies excluded: Y

## Why This Is Official
This candidate is not selected because it has the highest possible AUC. It is selected because it keeps the project-defined 1~3 week observation window while removing product-code memorization risk, watch-presence shortcuts, first/last watch timing shortcuts, ratio/delta duplication, and genre volume/session-count usage proxies.

## Interpretation Boundary
The model is usable for churn-risk ranking. It must not be presented as causal proof. Because multicollinearity remains inside weekly usage and genre-ratio families, individual feature coefficients and individual SHAP values should be interpreted at feature-family level first.
