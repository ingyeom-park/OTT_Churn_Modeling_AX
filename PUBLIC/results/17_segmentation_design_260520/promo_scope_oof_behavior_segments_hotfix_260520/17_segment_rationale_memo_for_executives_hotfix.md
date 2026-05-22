# PUBLIC 17 Segmentation Semantic Hotfix Executive Rationale Memo

## 1. Executive summary

This semantic hotfix reopens the PUBLIC 17 segmentation outputs with an adversarial review posture. The original 17 package had the right structural shape: the row counts matched, the OOF score direction was correct, and each row had exactly one representative segment assignment. However, structural correctness is not enough. Segmentation can be formally correct and still be semantically misleading if a broad marker is treated as though it separates a distinct customer group.

The key issue is `content_preference_signal`. The hotfix audit reads the existing `17_internal_multiflag_assignment.csv` directly and finds that `content_preference_signal` is active for 22416 out of 23097 rows, or 97.05% overall. Because this is above the 70% broad-flag threshold, the hotfix treats it as a broad content-context marker, not as a segment-discriminating condition. This does not mean content information is useless. It means the marker is too common to justify a representative segment rule.

Promo1 remains the main 100won business scope, and promo0 remains the comparison scope. The output is still provisional segmentation design, not final campaign targeting. The segment labels are still provisional. GB top20 remains a design risk condition, not an operating campaign threshold. SHAP remains model explanation, not causality. 07~10 remain pending validation.

The second important result is that `other_needs_review` remains large: promo1 has 7544 rows in other-needs-review, or 63.37%; promo0 has 6994 rows, or 62.49%. This hotfix does not hide that fact. It records it as a caveat: the segmentation identifies high-risk core behavior patterns and lower-risk stable usage patterns, but a large majority still needs additional validation or more refined rules.

## 2. Why we do not rely on content_preference_signal as a segment rule

The original 17 design allowed a genre-or-content segment to be triggered by either `genre_preference_clear` or `content_preference_signal`. That is risky because `content_preference_signal` is not rare or discriminating. A flag that is active for nearly the entire population cannot distinguish a meaningful subgroup. If such a flag is placed inside a representative segment rule, it can make a segment look behaviorally specific when it is actually a very common marker.

The hotfix therefore removes `content_preference_signal` from representative rule logic. Content information is not discarded. It is moved to profile and action personalization. That is the correct evidence tier. It can help later message or content recommendation design, but it cannot by itself justify a segment such as "content preference narrow" when the flag is present for almost everyone.

`genre_preference_clear` is different. It is narrower and tied to genre concentration or clarity. The hotfix keeps genre-preference segments only when `genre_preference_clear` is present. This distinction matters for executives: content context can inform personalization, while genre clarity can support a more specific action hypothesis.

## 3. Why these representative segments exist


### promo0_high_risk_week3_inactive

This provisional segment contains 1736 rows in promo0, which is 15.51% of that scope. Its actual repurchase rate is 31.28%, so the descriptive churn rate is 68.72%. The mean GB churn risk is 0.6624, while the median GB churn risk is 0.6592. The GB/LR both-top20 share is 84.22%. The dominant flags recorded for this segment are `week3_inactive:1.00:flag; retention_decay:0.80:flag; only_w1:0.57:flag; low_activity:0.79:flag; usage_concentrated:0.77:flag; genre_preference_clear:0.55:flag; content_preference_signal:0.99:broad_marker`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo0_high_risk_retention_decay

This provisional segment contains 154 rows in promo0, which is 1.38% of that scope. Its actual repurchase rate is 39.61%, so the descriptive churn rate is 60.39%. The mean GB churn risk is 0.5552, while the median GB churn risk is 0.5307. The GB/LR both-top20 share is 70.13%. The dominant flags recorded for this segment are `retention_decay:1.00:flag; low_activity:0.31:flag; usage_concentrated:0.27:flag; content_preference_signal:0.97:broad_marker`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo0_high_risk_only_w1_or_cold_start_weak

This provisional segment contains 230 rows in promo0, which is 2.05% of that scope. Its actual repurchase rate is 21.30%, so the descriptive churn rate is 78.70%. The mean GB churn risk is 0.6343, while the median GB churn risk is 0.6057. The GB/LR both-top20 share is 84.35%. The dominant flags recorded for this segment are `cold_start_weak:1.00:flag; low_activity:0.99:flag; usage_concentrated:0.96:flag; genre_preference_clear:0.82:flag; content_preference_signal:1.00:broad_marker`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo0_high_risk_low_activity

This provisional segment contains 43 rows in promo0, which is 0.38% of that scope. Its actual repurchase rate is 44.19%, so the descriptive churn rate is 55.81%. The mean GB churn risk is 0.5998, while the median GB churn risk is 0.5762. The GB/LR both-top20 share is 55.81%. The dominant flags recorded for this segment are `low_activity:1.00:flag; usage_concentrated:0.58:flag; content_preference_signal:1.00:broad_marker`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo0_high_risk_genre_preference_clear

This provisional segment contains 5 rows in promo0, which is 0.04% of that scope. Its actual repurchase rate is 20.00%, so the descriptive churn rate is 80.00%. The mean GB churn risk is 0.5638, while the median GB churn risk is 0.5715. The GB/LR both-top20 share is 80.00%. The dominant flags recorded for this segment are `genre_preference_clear:1.00:flag; content_preference_signal:1.00:broad_marker`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo0_stable_usage_lower_risk

This provisional segment contains 2031 rows in promo0, which is 18.15% of that scope. Its actual repurchase rate is 91.83%, so the descriptive churn rate is 8.17%. The mean GB churn risk is 0.0800, while the median GB churn risk is 0.0508. The GB/LR both-top20 share is 0.00%. The dominant flags recorded for this segment are `content_preference_signal:0.93:broad_marker; stable_usage:1.00:flag`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo0_other_needs_review

This provisional segment contains 6994 rows in promo0, which is 62.49% of that scope. Its actual repurchase rate is 85.77%, so the descriptive churn rate is 14.23%. The mean GB churn risk is 0.1541, while the median GB churn risk is 0.1105. The GB/LR both-top20 share is 0.64%. The dominant flags recorded for this segment are `week3_inactive:0.34:flag; retention_decay:0.56:flag; cold_start_weak:0.46:flag; low_activity:0.48:flag; usage_concentrated:0.47:flag; genre_preference_clear:0.31:flag; content_preference_signal:0.98:broad_marker`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo1_high_risk_week3_inactive

This provisional segment contains 1700 rows in promo1, which is 14.28% of that scope. Its actual repurchase rate is 25.06%, so the descriptive churn rate is 74.94%. The mean GB churn risk is 0.7455, while the median GB churn risk is 0.7445. The GB/LR both-top20 share is 84.59%. The dominant flags recorded for this segment are `week3_inactive:1.00:flag; retention_decay:0.81:flag; only_w1:0.55:flag; low_activity:0.79:flag; usage_concentrated:0.77:flag; genre_preference_clear:0.56:flag; content_preference_signal:1.00:broad_marker`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo1_high_risk_retention_decay

This provisional segment contains 193 rows in promo1, which is 1.62% of that scope. Its actual repurchase rate is 31.61%, so the descriptive churn rate is 68.39%. The mean GB churn risk is 0.6899, while the median GB churn risk is 0.6830. The GB/LR both-top20 share is 69.43%. The dominant flags recorded for this segment are `retention_decay:1.00:flag; low_activity:0.32:flag; content_preference_signal:0.97:broad_marker`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo1_high_risk_only_w1_or_cold_start_weak

This provisional segment contains 329 rows in promo1, which is 2.76% of that scope. Its actual repurchase rate is 19.76%, so the descriptive churn rate is 80.24%. The mean GB churn risk is 0.7326, while the median GB churn risk is 0.7247. The GB/LR both-top20 share is 83.59%. The dominant flags recorded for this segment are `cold_start_weak:1.00:flag; low_activity:0.92:flag; usage_concentrated:0.89:flag; genre_preference_clear:0.75:flag; content_preference_signal:1.00:broad_marker`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo1_high_risk_low_activity

This provisional segment contains 41 rows in promo1, which is 0.34% of that scope. Its actual repurchase rate is 36.59%, so the descriptive churn rate is 63.41%. The mean GB churn risk is 0.7245, while the median GB churn risk is 0.7137. The GB/LR both-top20 share is 70.73%. The dominant flags recorded for this segment are `low_activity:1.00:flag; usage_concentrated:0.34:flag; content_preference_signal:1.00:broad_marker`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo1_high_risk_genre_preference_clear

This provisional segment contains 11 rows in promo1, which is 0.09% of that scope. Its actual repurchase rate is 18.18%, so the descriptive churn rate is 81.82%. The mean GB churn risk is 0.6915, while the median GB churn risk is 0.7018. The GB/LR both-top20 share is 90.91%. The dominant flags recorded for this segment are `genre_preference_clear:1.00:flag; content_preference_signal:0.91:broad_marker`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo1_stable_usage_lower_risk

This provisional segment contains 2086 rows in promo1, which is 17.52% of that scope. Its actual repurchase rate is 85.52%, so the descriptive churn rate is 14.48%. The mean GB churn risk is 0.1497, while the median GB churn risk is 0.1062. The GB/LR both-top20 share is 0.00%. The dominant flags recorded for this segment are `content_preference_signal:0.91:broad_marker; stable_usage:1.00:flag`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.

### promo1_other_needs_review

This provisional segment contains 7544 rows in promo1, which is 63.37% of that scope. Its actual repurchase rate is 75.34%, so the descriptive churn rate is 24.66%. The mean GB churn risk is 0.2476, while the median GB churn risk is 0.2154. The GB/LR both-top20 share is 0.81%. The dominant flags recorded for this segment are `week3_inactive:0.34:flag; retention_decay:0.55:flag; cold_start_weak:0.46:flag; low_activity:0.47:flag; usage_concentrated:0.46:flag; genre_preference_clear:0.32:flag; content_preference_signal:0.98:broad_marker`.

The segment is kept only when its rule is behaviorally interpretable. If this row group is a high-risk week3 inactive or retention-decay group, it points to an observable timing problem. If it is a cold-start-weak group, the hotfix preserves the corrected meaning that cold-start fixed success flags are early activation success, not weak activation. If it is the genre-preference segment, the segment is now based on `genre_preference_clear`; the broad `content_preference_signal` is not allowed to create this segment. If it is an other-needs-review segment, the correct interpretation is not that the model failed, but that the current conservative rules intentionally refused to over-segment ambiguous rows.

The business action candidate should therefore remain provisional. The group can inform which behavior problem to investigate first, but it should not be treated as a final campaign target. Any action must be validated through a later operational test or A/B test design.


## 4. Why other_needs_review remains large

The hotfix intentionally avoids creating more segments just to reduce the size of the other bucket. A smaller other bucket would look cleaner, but it could be less honest. The current design has enough evidence to identify certain high-risk patterns: week3 inactivity, retention decay, weak early activation or only-week1 use, low activity, and clear genre preference. It also identifies lower-risk stable usage patterns. Rows outside those rules are not forced into invented groups.

This matters because segmentation is supposed to guide action, not decorate a dashboard. If a row does not show the behavior evidence needed for a rule, leaving it in `other_needs_review` is safer than assigning it to a weakly justified action category. The large other bucket should be treated as an analytical limitation and a future validation target, especially because 07~10 are still pending validation.

## 5. Why demographic is not the primary segment rule

Age and gender are not used as primary segment rules. They can modify communication, channel, and content choices after EDA evidence shows meaningful differences, but they do not define the representative segment. The same behavioral segment can contain different demographic profiles. That profile can matter for personalization, but it does not prove that age or gender caused churn risk.

This guardrail prevents statements such as "young women churn" or "men are high risk". The hotfix keeps demographic information in profile and action personalization tables only.

## 6. Business action logic

Week3 inactive segments suggest a renewal-proximity save or reactivation message. Retention-decay segments suggest a week2 or week3 retention nudge. Only-week1 or cold-start-weak segments suggest onboarding reactivation. Low-activity segments require caution because the flag is broad; the component flags should be checked before action. Genre-preference-clear segments can support a recommendation experiment. Stable lower-risk segments may support benefit reminders or conversion/upsell tests. Other-needs-review segments should not receive a specific action until additional evidence is available.

## 7. Rejected alternatives

The hotfix rejects content-preference-only segmentation because `content_preference_signal` is too broad. It rejects age/gender segmentation because demographics are profile variables, not behavior rules. It rejects top10-only segmentation because it would be too narrow for provisional design, and top30 as the primary criterion because it would be too broad. It rejects clustering-only segmentation because cluster labels would not guarantee risk relevance or actionability. It rejects SHAP-top-feature-only segmentation because SHAP explains the model but does not define a campaign-ready customer group.

## 8. Caveats

SHAP is not causal evidence. OOF score is not a campaign threshold. Segment labels are provisional. `content_preference_signal` is a broad marker. `other_needs_review` is large. Demographic action requires EDA evidence. `is_churn_prevented` remains a historical context feature with caveat. 07~10 remain pending validation.

## 9. What executives can use this for

Executives can use this hotfix to see which 100won customer risk patterns are currently interpretable, where content personalization is supported only as a cue, why the unclassified majority should not be overclaimed, and which action hypotheses should be reviewed before 18 business storyline work.

## 10. What executives should not conclude

Executives should not conclude that these segments are final campaign targets, that 100won caused churn, that SHAP proves causes, that `content_preference_signal` proves a content-preference segment, that age/gender caused churn, or that GB top20 is an operational threshold.
