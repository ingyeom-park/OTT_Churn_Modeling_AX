# PUBLIC 17 Segment Rationale Memo for Executives

## 1. Executive summary

This segmentation design turns the row-level OOF score evidence from PUBLIC 15 and the model explanation evidence from PUBLIC 16/16b into provisional business-facing customer groups. The main scope is promo1, the 100won-deal customer group. Promo0 remains a comparison group because the project question is not simply "who is high risk overall", but how the 100won customer context differs from the general customer context.

This result is not final campaign targeting. Segment labels are provisional rule labels. OOF score is row-level risk evidence, not a final campaign threshold. SHAP is model explanation, not causality. 07~10 remain pending validation.

## 2. Why segmentation is needed after OOF and SHAP

OOF score tells us which rows look risky, but it does not directly say what intervention should be attempted. SHAP tells us which feature families the model used, but SHAP alone does not create an actionable segment. A business segment needs the intersection of risk, behavior, and interpretable evidence. For that reason this design combines GB/LR OOF risk flags, behavior flags from existing input columns, and 16b hotfixed family evidence.

The primary high-risk condition is GB top20. Top10 and top30 are preserved as review layers, but they are not the representative rule baseline. LR is retained as sensitivity and overlap evidence.

## 3. Segmentation design logic

The segmentation base datamart joins the OOF wide table to the promo input CSVs by promo_scope and row_id. Promo1 and promo0 are not pooled into a single segmentation universe. This preserves the business meaning of the 100won scope.

The internal flags are deliberately multi-label. A customer can be week3 inactive, retention-decayed, low-activity, and genre-focused at the same time. Representative segment assignment then applies a priority order so that each row receives exactly one provisional segment label.

The cold-start logic is corrected. `is_cold_start_3d_fixed = 1` and `is_cold_start_7d_fixed = 1` mean early activation success, not weak activation. `cold_start_weak` is the inverse of the 7-day flag when available. If only the 3-day flag is available, it is used with a caveat. This prevents the analysis from mistaking fast early watching for weak onboarding.

The low_activity flag is broad. It can be triggered by low watch count, low watch time, or low watch days. The helper records the component flags and `low_activity_reason` so the broad flag can be audited instead of overinterpreted.

Stable usage is also cautious. It is a provisional lower-risk behavior pattern, not a final loyal segment. It combines high active ratio, non-concentrated activity, sufficient watch days, non-high-risk GB top20 status, and when available no week3 inactivity and no retention decay.

## 4. Why not use alternative segmentation methods

The analysis does not segment all customers together because promo1 is the business focus and promo0 is the comparison scope. Pooling them would hide the 100won-specific behavior pattern.

The analysis does not use age or gender as primary segment rules. Demographic features are profile audit and action personalization variables. A sentence like "20대 여성은 이탈한다" is not supported by this design.

The analysis does not segment only by SHAP top features. SHAP explains model behavior, but business action needs row-level risk and observed behavior flags.

The analysis does not use clustering-only segmentation because clustering would create groups without guaranteeing high-risk relevance or actionability. The current design is rule-based and auditable.

The analysis does not set a final campaign threshold. GB top20 is a design rule for provisional segmentation, not an operating cutoff.

## 5. Segment-by-segment rationale

- `promo1_high_risk_week3_inactive` has 1700 rows, share 0.143, actual repurchase rate 0.251, mean GB churn risk 0.746, and dominant flags `week3_inactive:1.00; retention_decay:0.81; only_w1:0.55; low_activity:0.79; usage_concentrated:0.77; genre_preference_clear:0.56`.
- `promo1_high_risk_retention_decay` has 193 rows, share 0.016, actual repurchase rate 0.316, mean GB churn risk 0.690, and dominant flags `retention_decay:1.00; low_activity:0.32; content_preference_signal:0.97`.
- `promo1_high_risk_only_w1_or_cold_start_weak` has 329 rows, share 0.028, actual repurchase rate 0.198, mean GB churn risk 0.733, and dominant flags `cold_start_weak:1.00; low_activity:0.92; usage_concentrated:0.89; genre_preference_clear:0.75; content_preference_signal:1.00`.
- `promo1_high_risk_low_activity` has 41 rows, share 0.003, actual repurchase rate 0.366, mean GB churn risk 0.724, and dominant flags `low_activity:1.00; usage_concentrated:0.34; content_preference_signal:1.00`.
- `promo1_high_risk_genre_or_content_narrow` has 117 rows, share 0.010, actual repurchase rate 0.188, mean GB churn risk 0.670, and dominant flags `content_preference_signal:0.99`.
- `promo1_stable_usage_lower_risk` has 2086 rows, share 0.175, actual repurchase rate 0.855, mean GB churn risk 0.150, and dominant flags `content_preference_signal:0.91; stable_usage:1.00`.
- `promo1_other_needs_review` has 7438 rows, share 0.625, actual repurchase rate 0.761, mean GB churn risk 0.242, and dominant flags `week3_inactive:0.34; retention_decay:0.56; cold_start_weak:0.46; low_activity:0.47; usage_concentrated:0.46; genre_preference_clear:0.32`.

Each provisional segment exists because it ties a risk condition to a behavior problem. Week3 inactive customers suggest near-renewal disengagement. Retention-decay customers suggest continuing-viewing decline. Only-week1 or cold-start-weak customers suggest onboarding or early activation failure. Low-activity customers require caution because the flag is broad, but the component flags show whether count, time, or active days created the signal. Genre/content narrow customers may support recommendation experiments, but content preference does not prove churn causality. Stable-usage lower-risk customers are not final loyal customers; they are a lower-risk behavior pattern that may support conversion, reminder, or upsell experiments.

## 6. Demographic and action personalization policy

Age and gender are not representative segment rules. They are profile audit and action personalization layers. The same behavior segment can receive different messages or content variants after EDA evidence shows meaningful distribution differences. Without that evidence, demographic action variants remain not recommended yet.

## 7. Business action logic

Early weak activation or only-week1 behavior suggests onboarding reactivation. Week2 or week3 drop suggests retention nudges. Week3 inactivity suggests renewal-proximity save campaigns. Narrow genre evidence suggests recommendation strategy. Stable usage suggests benefit reminder, conversion, or upsell candidates. These are candidates, not proven campaign effects.

## 8. Caveats and guardrails

SHAP is not causality. OOF score is not a final campaign threshold. Segments are provisional. 07~10 remain pending validation. Demographic action needs EDA evidence. is_churn_prevented is interpreted as past churn prevention response history only. Final segment names are not confirmed.

## 9. What decision-makers can use this for

Decision-makers can use this to prioritize who to review first, which behavior problem to intervene on, what message or content strategy to test, how promo1 differs from promo0, and how to design a later A/B test.

## 10. What decision-makers should not conclude

Decision-makers should not conclude that 100won caused churn, that SHAP features are causes, that these segments are final campaign targets, that age or gender caused churn, or that GB top20 is an operational campaign threshold.
