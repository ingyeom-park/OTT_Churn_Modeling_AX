# 06h Team Share Model Summary

- official model candidate: `pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence`
- feature set used: membership context, week1~3 watch_time/sessions, simple usage variables, genre_ratio variables, genre_entropy, recent_content_watch_ratio
- included feature families: membership_context, other
- excluded feature families: product_code, watch-presence shortcut, first/last watch timing, week ratios/deltas, genre watch_time/session_count, coverage/missing complements
- AUC: 0.862148
- churn-risk top-decile lift: 2.755381
- Logistic coefficient caveat: coefficients are for repurchase_score direction; negative values mean higher churn-risk association, not causality.
- TRUE SHAP caveat: positive SHAP pushes toward repurchase_score, negative SHAP pushes toward churn risk; use family-first interpretation.
- recommended figures: auc_vs_interpretability, top_decile_lift_comparison, final_candidate_corr_heatmap, logistic_top_coefficients, SHAP beeswarm and SHAP family bar if SHAP succeeded
- what not to say: do not claim causality, ROI, product_code-driven official model, watch-presence shortcut, or w1_4 as early-warning performance.
