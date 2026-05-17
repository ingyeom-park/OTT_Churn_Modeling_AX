# 15x payment device sensitivity audit

## Purpose
This step checks how removing `payment_is_mobile`, `payment_is_pc`, `payment_is_android`, and `payment_is_ios` affects model performance, top-k targeting behavior, calibration, and proxy/artifact risk.

This is not a canonical feature-contract change, not a final-model decision, not SHAP, not segmentation, and not feature-removal approval.

## User interpretation rules
- `payment_device` means payment device or payment environment, not viewing device.
- Paying on an iPhone does not prove viewing on an iPhone.
- The payer and actual viewer can differ.
- High SHAP or model sensitivity for `payment_is_*` must not be interpreted as viewing experience or causal effect.
- `payment_is_*` can proxy payment environment, account status, authentication, acquisition structure, or account creation context.
- 17x representative segment rules should first consider not using `payment_is_*` directly.
- 15x is only a sensitivity audit.

Additional confirmed assumptions: `is_user_verified` is real identity verification; unverified age/gender may be self-entered but is provisionally trusted; gender=N is NaN, not Neutral; `age_group` is age binned by decade; age/gender/auth can remain model features but should not directly name representative segments or causes; `is_churn_prevented` is past churn-prevention history; `is_promotion=1` is exactly the 100-won deal; `recency` is only day0 to day20 recency; under_1m and under_5m remain different behavior proxies; retention ratio is smoothed relative change; `is_only_w*` means viewing only in that week within day0 to day20; genre ratios are Movie_Master category mapping proxies.

## Sensitivity design
Baseline reference is 12x `expanded_feature_set`. The runtime sensitivity feature set is `expanded_no_payment_device`, which removes only the four payment-device derived columns from model features. The 06x expanded dataset and canonical feature list are not overwritten.

CV uses StratifiedGroupKFold with `USER_KEY` as group key, 5 folds, random_state 42. Target is `is_repurchase`, positive class is repurchase, and `churn_risk = 1 - repurchase_score`.

## Performance comparison summary
Mean delta AUC, no payment minus original: 0.003590. Worst delta AUC: -0.000150. Performance-loss label: near_neutral.

Worst rows by AUC delta:

```text
            dataset_scope           model_name  delta_auc_no_payment_minus_original  delta_ap  delta_brier
        nonpromotion_only HistGradientBoosting                            -0.000150  0.000447     0.001022
           promotion_only             LightGBM                             0.000342  0.000088    -0.000109
overall_without_promotion             LightGBM                             0.000526  0.000241    -0.000297
overall_without_promotion HistGradientBoosting                             0.000676  0.000239    -0.000325
```

## Proxy artifact audit
`flag_age40_unverified_ios` was calculated only for audit. It was not added as a model feature and must not be used as a segment rule. A high-risk concentration should be described only as a possible artifact/proxy concentration, not as a causal group.

## Handoff
Canonical feature-contract change remains pending user approval. If the user later approves removing payment-device features from canonical modeling, 16x SHAP should be revisited because previous SHAP would not match the new feature contract. For 17x, representative segment rules should prioritize behavior variables and avoid direct payment/auth/demographic proxy naming.
