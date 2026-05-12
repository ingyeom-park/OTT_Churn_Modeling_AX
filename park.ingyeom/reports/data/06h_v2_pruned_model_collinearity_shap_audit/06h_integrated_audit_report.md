# 06h Integrated Audit Report

## Executive Answer
1. Official final model candidate: `pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence` with HGB.
2. It uses full 1~3 week information: Y.
3. It excludes product_code by default: Y.
4. It excludes watch-presence shortcut by default: Y.
5. It avoids first/last watch timing features: Y.
6. It avoids ratio/delta structural duplicates: Y.
7. It avoids genre volume/session_count usage proxies: Y.
8. AUC: 0.862148.
9. churn-risk PR AUC: 0.700385.
10. top-decile lift: 2.755381.
11. Comparison: full w1_3 reference AUC 0.872458629449125; exact w1_2 reference AUC 0.7401751232325673; w1_4 late-period reference AUC 0.9022499874722302.
12. Remaining multicollinearity: max abs corr 0.911655, max VIF 6.060558681911423.
13. Weekly usage pattern and genre-ratio features must be interpreted at family level.
14. LogisticRegression coefficients suggest directional association with repurchase_score only; negative coefficients indicate churn-risk association.
15. TRUE SHAP status: TRUE SHAP succeeded for the final HGB candidate.
16. Stage 07r should be updated to use this pruned official candidate for family-first TRUE SHAP wording.
17. Stage 08b segmentation should be described as model-informed risk grouping, not causal segmentation.
18. Mentor message is in 06h_mentor_response_update.md.
19. Final presentation should use official pruned AUC, top-decile lift, coefficient caveat, and TRUE SHAP family-first caveat.
20. Must not claim causality, ROI/profit, hyperparameter-optimized performance, product_code official shortcut, watch-presence shortcut, or w1_4 as early-warning.

## Optional Warnings
