> Executive summary

This memo explains the PUBLIC 17 segmentation quality hotfix. The current segmentation is technically usable in the narrow sense that rows, score direction, and rule-based representative assignment can be revalidated from the saved 17 datamart and multiflag files. The quality issue is different. A segmentation can be mechanically correct and still be weak as a business artifact if its labels are too broad, if it creates tiny representative groups, or if it allows a very large residual group to be described as though it were a clean middle-risk segment.

The audited base contains 23,097 rows: promo1 has 11,904 rows and promo0 has 11,193 rows. Promo1 is the 100won-deal customer scope. Promo0 is the general-customer comparison scope. The revised language therefore treats promo1 as the intervention-priority scope and promo0 as the comparison scope. It does not claim that the promotion caused the observed behavior. The hotfix keeps the segmentation provisional, keeps segment names provisional rule labels, and keeps OOF score as a review signal rather than a campaign threshold.

The most important finding is that content_preference_signal is too broad to be a representative segment rule. The saved audit shows overall prevalence of 97.1%. A flag that appears in almost all rows cannot separate a business population in a defensible way. It may still carry useful context for message personalization, content recommendation, or post-segment profiling, but it should not be promoted as the reason a row belongs to a representative segment.

The second finding is that several small segments should not be presented as independent representative business segments. In this hotfix, n >= 300 is treated as the default minimum for representative-candidate status. Rows below that level are not deleted. They are demoted to sub-signals, profile notes, action cues, or user-review candidates. This is a conservative choice because small groups can show sharp churn rates simply because the denominator is small.

The third finding is that other_needs_review must remain a residual category. It is not a synonym for middle risk. The other bucket contains high-risk unexplained rows, mid-risk watchlist rows, low-risk general rows, stable-like residual rows, and profile-note rows. Calling the entire bucket middle risk would erase the most important operational caveat.

> Why minimum segment size matters

The minimum segment size policy is a practical business-control rule. A segment is not only a statistical grouping. It is also a presentation object, a planning object, and potentially an action object. If a segment has only a handful of rows, the team may overinterpret a noisy churn rate, build a campaign story around a fragile pattern, or imply precision that the data cannot support.

The threshold used here is simple. Segments with n >= 300 may be representative candidates if they also have a clear behavioral rule and a plausible action. Segments with 100 <= n < 300 are small provisional sub-signals. They may be mentioned as a pattern but should usually be merged into a broader family. Segments with 30 <= n < 100 are rare pattern notes. They are useful for monitoring and hypothesis generation, not for executive-level segmentation. Segments with n < 30 are case notes only. They should not become representative segments.

This policy is not a claim that 299 rows are worthless or that 300 rows are magically safe. The point is to create a review discipline. A minimum size rule forces the analyst to ask whether a segment can survive presentation, comparison, and action design. It also prevents the segmentation from becoming a list of interesting exceptions.

The small-segment policy found the following cases:

promo0 promo0_s01 has n=1736, min-n status=pass_representative_candidate, recommended action=keep_representative, and preserved signal=not_demoted.
promo0 promo0_s02 has n=154, min-n status=small_provisional_subsignal, recommended action=merge_to_retention_inactivity_family, and preserved signal=retention_decay_subsignal.
promo0 promo0_s03 has n=230, min-n status=small_provisional_subsignal, recommended action=merge_to_activation_low_engagement_family, and preserved signal=low_activity_or_cold_start_subsignal.
promo0 promo0_s04 has n=43, min-n status=rare_pattern_note, recommended action=merge_to_activation_low_engagement_family, and preserved signal=low_activity_or_cold_start_subsignal.
promo0 promo0_s05 has n=5, min-n status=case_note_only, recommended action=demote_to_genre_action_cue, and preserved signal=genre_action_cue.
promo0 promo0_s06 has n=2031, min-n status=pass_representative_candidate, recommended action=keep_representative, and preserved signal=not_demoted.
promo0 promo0_s99 has n=6994, min-n status=pass_representative_candidate, recommended action=keep_as_needs_review, and preserved signal=residual_review_bucket.
promo1 promo1_s01 has n=1700, min-n status=pass_representative_candidate, recommended action=keep_representative, and preserved signal=not_demoted.
promo1 promo1_s02 has n=193, min-n status=small_provisional_subsignal, recommended action=merge_to_retention_inactivity_family, and preserved signal=retention_decay_subsignal.
promo1 promo1_s03 has n=329, min-n status=pass_representative_candidate, recommended action=keep_representative, and preserved signal=not_demoted.
promo1 promo1_s04 has n=41, min-n status=rare_pattern_note, recommended action=merge_to_activation_low_engagement_family, and preserved signal=low_activity_or_cold_start_subsignal.
promo1 promo1_s05 has n=11, min-n status=case_note_only, recommended action=demote_to_genre_action_cue, and preserved signal=genre_action_cue.
promo1 promo1_s06 has n=2086, min-n status=pass_representative_candidate, recommended action=keep_representative, and preserved signal=not_demoted.
promo1 promo1_s99 has n=7544, min-n status=pass_representative_candidate, recommended action=keep_as_needs_review, and preserved signal=residual_review_bucket.

These signals were preserved rather than discarded. Retention decay can be retained as a retention_decay_subsignal under the broader inactivity or retention-decay family. Low activity can be retained under an activation or low-engagement family. Genre and content cues can be retained as personalization cues. This preserves analytical information while reducing the risk of overclaiming.

> Why content_preference_signal was demoted

content_preference_signal was demoted because its prevalence is too high for a representative rule. The saved 17_content_preference_signal_audit.csv reports overall prevalence of 97.1%. Promo0 and promo1 both show broad prevalence. That means the flag is closer to a context marker than a discriminating segment criterion.

A representative segment rule should answer a basic question: why is this row meaningfully different from rows outside the segment? A broad flag does not answer that question. If almost every row has the signal, then using it as a representative criterion makes the segment label look more meaningful than it is. It may still matter downstream. For example, if a row belongs to a high-risk inactivity family and also has strong genre or content evidence, the campaign team can personalize the message with content-specific copy. But the representative reason should remain the behavior signal, not the broad content marker.

This distinction is important because it protects the explanation. The hotfix does not say content preference is useless. It says content preference is not strong enough as the top-level segmentation rule in this dataset. That is a narrower and more defensible claim.

> How other_needs_review should be interpreted

other_needs_review is the residual group left after the current representative rules have assigned the rows they can explain. It is not a middle-risk segment. It is not a coherent business persona. It is a container for rows that the current provisional rule system does not explain well enough.

The quality decomposition shows:

In promo0, other_demographic_or_profile_note contains n=4037 (57.7% of other, 36.1% of scope), with actual churn=0.1246 and mean GB risk=0.1504.
In promo0, other_high_risk_unexplained contains n=71 (1.0% of other, 0.6% of scope), with actual churn=0.6338 and mean GB risk=0.5316.
In promo0, other_low_risk_general contains n=83 (1.2% of other, 0.7% of scope), with actual churn=0.1084 and mean GB risk=0.1233.
In promo0, other_mid_risk_watchlist contains n=1054 (15.1% of other, 9.4% of scope), with actual churn=0.3956 and mean GB risk=0.3523.
In promo0, other_stable_like_residual contains n=1749 (25.0% of other, 15.6% of scope), with actual churn=0.0120 and mean GB risk=0.0295.
In promo1, other_demographic_or_profile_note contains n=4350 (57.7% of other, 36.5% of scope), with actual churn=0.2510 and mean GB risk=0.2564.
In promo1, other_high_risk_unexplained contains n=107 (1.4% of other, 0.9% of scope), with actual churn=0.8131 and mean GB risk=0.6672.
In promo1, other_low_risk_general contains n=97 (1.3% of other, 0.8% of scope), with actual churn=0.2680 and mean GB risk=0.2404.
In promo1, other_mid_risk_watchlist contains n=1104 (14.6% of other, 9.3% of scope), with actual churn=0.5688 and mean GB risk=0.5140.
In promo1, other_stable_like_residual contains n=1886 (25.0% of other, 15.8% of scope), with actual churn=0.0143 and mean GB risk=0.0478.

This decomposition is intentionally conservative. It does not convert the subgroups into new final segments. The decomposition is a diagnostic layer. It helps the team see whether the residual group contains hidden high-risk pockets, ordinary low-risk rows, or stable-like rows that missed the current stable rule. Only subgroups with enough size, behavior clarity, and actionability should be promoted later, and even then only after user approval.

The reason not to over-split other is the same reason not to keep every small segment as representative. A residual bucket can always be chopped into smaller bins after the fact. That does not mean those bins are business segments. A good segmentation should reduce confusion. If the segmentation creates many tiny labels that cannot be acted on differently, it has become a taxonomy exercise rather than a decision tool.

> Promo1 vs Promo0 differential analysis

The promo1 versus promo0 comparison is central because the business question is not simply whether a behavior predicts churn. The question is whether a behavior should be handled differently for 100won-deal customers than for general customers. The hotfix therefore compares segment families across promo scopes.

genre_or_content_action_cue: promo1 n=11, promo0 n=5, promo1 churn=0.8181818181818182, promo0 churn=0.8, risk delta=0.12763988267986015. Interpretation: Common observed behavior signal; compare strength by scope without causal wording.
high_risk_activation_or_low_engagement: promo1 n=370, promo0 n=273, promo1 churn=0.7837837837837838, promo0 churn=0.7509157509157509, risk delta=0.10280800143687141. Interpretation: Common observed behavior signal; compare strength by scope without causal wording.
high_risk_week3_inactivity_or_retention_decay: promo1 n=1893, promo0 n=1890, promo1 churn=0.7427363972530375, promo0 churn=0.6804232804232804, risk delta=0.08620232756445789. Interpretation: Common observed behavior signal; compare strength by scope without causal wording.
other_needs_review_residual: promo1 n=7544, promo0 n=6994, promo1 churn=0.2465535524920467, promo0 churn=0.14226479839862738, risk delta=0.09346651347605459. Interpretation: Common observed behavior signal; compare strength by scope without causal wording.
stable_usage_lower_risk: promo1 n=2086, promo0 n=2031, promo1 churn=0.14477468839884944, promo0 churn=0.08173313638601676, risk delta=0.06971465870796628. Interpretation: Common observed behavior signal; compare strength by scope without causal wording.

The interpretation rule is strict. If the same behavior appears in both promo1 and promo0, the memo does not call it a 100won-specific pattern. It calls it a common risk signal and then checks whether it appears more severe in promo1. If the pattern is strong in promo1 and weak or absent in promo0, it can become a 100won-focused intervention candidate. If it is strong in both, it is a general OTT churn signal that may still deserve priority in promo1 because promo1 is the business scope of interest. None of these statements imply causal impact from the promotion.

This language matters for executives. A causal statement would require a different design. The saved data and OOF scores can support descriptive segmentation and prioritization. They cannot prove that the 100won deal caused the risk pattern. The defensible wording is therefore: observed in promo1, compared against promo0, prioritized for review, not causal.

> Revised representative segment proposal

The revised proposal is a review artifact. It does not overwrite the official assignment. It groups small and overlapping signals into broader behavior families. The recommended families are high_risk_week3_inactivity_or_retention_decay, high_risk_activation_or_low_engagement, mid_risk_retention_watchlist, stable_usage_lower_risk, and other_needs_review_residual.

For promo0, high_risk_activation_or_low_engagement has estimated n=273 (2.4%), actual churn rate=0.7509, mean GB churn risk=0.6289, min-n status=small_provisional_subsignal, and representative status=subsignal_only.
For promo0, high_risk_week3_inactivity_or_retention_decay has estimated n=1890 (16.9%), actual churn rate=0.6804, mean GB churn risk=0.6537, min-n status=pass_representative_candidate, and representative status=representative_candidate_after_review.
For promo0, mid_risk_retention_watchlist has estimated n=1195 (10.7%), actual churn rate=0.4167, mean GB churn risk=0.3634, min-n status=pass_representative_candidate, and representative status=representative_candidate_after_review.
For promo0, other_needs_review_residual has estimated n=5869 (52.4%), actual churn rate=0.0908, mean GB churn risk=0.1140, min-n status=pass_representative_candidate, and representative status=needs_user_review.
For promo0, stable_usage_lower_risk has estimated n=1966 (17.6%), actual churn rate=0.0682, mean GB churn risk=0.0712, min-n status=pass_representative_candidate, and representative status=representative_candidate_after_review.
For promo1, high_risk_activation_or_low_engagement has estimated n=370 (3.1%), actual churn rate=0.7838, mean GB churn risk=0.7317, min-n status=pass_representative_candidate, and representative status=representative_candidate_after_review.
For promo1, high_risk_week3_inactivity_or_retention_decay has estimated n=1893 (15.9%), actual churn rate=0.7427, mean GB churn risk=0.7399, min-n status=pass_representative_candidate, and representative status=representative_candidate_after_review.
For promo1, mid_risk_retention_watchlist has estimated n=1309 (11.0%), actual churn rate=0.6012, mean GB churn risk=0.5276, min-n status=pass_representative_candidate, and representative status=representative_candidate_after_review.
For promo1, other_needs_review_residual has estimated n=6333 (53.2%), actual churn rate=0.1808, mean GB churn risk=0.1941, min-n status=pass_representative_candidate, and representative status=needs_user_review.
For promo1, stable_usage_lower_risk has estimated n=1999 (16.8%), actual churn rate=0.1196, mean GB churn risk=0.1341, min-n status=pass_representative_candidate, and representative status=representative_candidate_after_review.

high_risk_week3_inactivity_or_retention_decay combines no-week3 activity and retention decline. These are close enough in business meaning to be handled together: both suggest the customer may have lost usage momentum near renewal. The business action candidate is a retention or reactivation review, not a final campaign threshold.

high_risk_activation_or_low_engagement combines weak early activation, only-week1 use, cold-start weakness, and broad low activity when those rows are also high risk. These signals all point to the same operational question: did the user fail to form enough habit to make renewal likely? The action candidate is onboarding, reactivation, or low-engagement support.

mid_risk_retention_watchlist captures rows that are not in the most severe top20 behavior families but still sit in a risk band worth monitoring. This family is especially important because it prevents other_needs_review from being lazily renamed as middle risk. A watchlist is not the same as a final campaign target.

stable_usage_lower_risk captures rows with stable usage and lower modeled churn risk. The action implication is not aggressive save messaging. It is lighter-touch retention, satisfaction maintenance, or exclusion from high-risk intervention logic unless later evidence changes the interpretation.

other_needs_review_residual remains because a segmentation needs an honest residual group. Removing other would create false precision. Keeping it explicitly residual is more defensible than pretending every row has a clean business label.

> Demographic and action personalization

Age and gender are not representative segment rules in this hotfix. They remain profile and action-personalization evidence. That means age or gender can help tune copy, channel, benefit framing, or follow-up analysis, but they do not decide the top-level segment family. This is important because demographic splits can become misleading if they are used before behavior and risk structure are stable.

The existing demographic hotfix and action matrix were read and referenced. The bridge file links revised segment families to the demographic/action layer, but it does not finalize demographic action variants. The correct next step for 18 is to keep demographic evidence available, use it only where EDA supports it, and avoid presenting age/gender as the primary reason for segment membership.

> Rejected alternatives

The first rejected alternative was keeping every existing small segment as a representative segment. That would preserve formal granularity but weaken business defensibility. A segment with very small n can be real as a signal and still be too fragile as an executive segment.

The second rejected alternative was keeping genre_preference or content_preference as independent representative segments. The problem is not that content information is irrelevant. The problem is that the broad content marker is too prevalent, and the narrow genre groups can be too small. The safer design is to retain content and genre as action cues.

The third rejected alternative was describing other_needs_review as middle risk. This would be simple, but it would be wrong. The decomposition shows mixed residual subgroups. Some are high-risk unexplained. Some are low-risk or stable-like. A single middle-risk label would hide that mixture.

The fourth rejected alternative was clustering-only segmentation. Clustering may be useful later, but a clustering-only solution would be harder to explain to executives unless it is tied back to clear behavior rules, risk levels, and action differences. The current stage needs a defensible rule-label proposal, not an opaque final taxonomy.

The fifth rejected alternative was segmenting only by SHAP top features. SHAP is model explanation, not causality. SHAP can support why the model pays attention to certain feature families, but it should not automatically become a business segmentation rule. The 16b family mapping is used as interpretive support, not as a final segment generator.

The sixth rejected alternative was treating top10 or top30 as the final decision threshold. Top20 remains a practical review band in the existing 17 logic, while top30 is useful for decomposition and watchlist diagnostics. None of these OOF score bands is a campaign threshold.

> Caveats

All segment names are provisional rule labels. The revised assignment is a simulation. The revised proposal requires user approval. OOF score is not a campaign threshold. SHAP is not causal evidence. 07 to 10 remain pending validation. Demographic action requires EDA support. is_churn_prevented remains a caveat because it should not be overinterpreted as confirmed churn prevention. This memo does not authorize a dashboard or final business storyline before review.

> Decision-maker recommendations

The team can use the quality audit immediately to explain why the segmentation needed a hotfix. The team can use the small-segment policy to defend why some interesting signals were merged or demoted. The team can use the other decomposition to avoid the misleading phrase middle-risk other. The team can use the promo1 versus promo0 differential file to discuss whether a signal is common or stronger in the 100won scope.

The team should not claim final segment names, final campaign thresholds, causal promotion effects, or completed downstream validation. The next defensible move is to review the zip package, approve or revise the proposed segment families, and only then decide whether 18 business storyline can proceed.
