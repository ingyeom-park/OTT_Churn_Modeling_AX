# 07_v2 XAI / SHAP Interpretation Report

## Scope
- Stage 07 performed model interpretation only.
- No segmentation, business simulation, Optuna, broad tuning, raw modification, or `_data` output was created.
- SHAP availability: unavailable: No module named 'shap'.
- Because SHAP is unavailable, fallback permutation importance and coefficient-based interpretation were used. These tables must not be called true SHAP values.

## Target And Score Direction
- `is_repurchase` mapping: Y -> 1, N -> 0.
- `repurchase_score = P(is_repurchase = Y)`.
- `churn_risk_score = 1 - repurchase_score`.
- Positive contribution toward repurchase means lower churn-risk direction, not higher churn risk.

## Explained Models
- Primary conservative model: w1_3 / membership_plus_usage_content_w1_3_without_churn_prevented / HistGradientBoostingClassifier.
- Secondary business-interpretable model: w1_3 / same feature set / LogisticRegression.
- Optional comparison: w1_4 / membership_plus_usage_content_w1_4_without_churn_prevented / LGBMClassifier, labeled late-period/end-of-period only.

## Reconstruction
- primary_conservative: HistGradientBoostingClassifier ROC AUC 0.8705, Stage 06 difference 0.0000, status PASS.
- business_interpretable: LogisticRegression ROC AUC 0.8415, Stage 06 difference 0.0000, status PASS.
- optional_late_period: LGBMClassifier ROC AUC 0.9037, Stage 06 difference 0.0000, status PASS.

## Top Drivers
- Top global drivers are stored in `07_v2_global_shap_importance.csv`; values are fallback permutation importance, not SHAP.
- The most important families are summarized in `07_v2_feature_family_importance.csv`.
- Negative direction for repurchase should be interpreted as higher churn-risk association.

## Content Feature Caution
- v2 content metadata is limited to genre and ott_release_month-derived proxies.
- Do not imply country, rating, runtime, actor, director, Wavve, or KOBIS metadata.
- If content proxies matter, report them as active-v2-available content signals only.

## Business Readiness
- Safe to report: split reuse, no group leakage, target mapping, and reproducible conservative-model reconstruction.
- Plausible but cautioned: usage/content proxy importance patterns.
- Do not claim yet: causal drivers, true SHAP values, or w1_4 as early-warning evidence.

## Stage 08 Guidance
- Use conservative w1_3 churn-risk scores and top predictive feature groups as candidate segmentation inputs.
- Keep Stage 08 segments descriptive and prediction-oriented until treatment or causal evidence exists.
