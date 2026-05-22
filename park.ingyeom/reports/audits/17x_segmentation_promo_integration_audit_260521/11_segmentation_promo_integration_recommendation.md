> 17x segmentation promotion-integration decision audit

## Purpose

This package checks how to show the 100won promotion story while keeping the current park.ingyeom 17x segmentation intact. It does not rerun models, recompute SHAP, change source CSVs, change notebooks, or reassign customers.

## Direct Answer

### Can is_promotion be inserted directly into the final segment rule?

No. This audit should not put is_promotion directly into final park rules because that would create a new segmentation design and violate the no-reassignment boundary.

The advantage would be stronger visibility of 100won customers. The risk is larger: it would turn the current behavior segmentation into a promo-scope segmentation, which requires a separate design decision, a new assignment basis, and fresh validation.

### If is_promotion is not inserted, how can PUBLIC still be used?

PUBLIC can be used for labels, action narrative, safe wording, and visual structure. PUBLIC rules should not be imported as park rules in this package because PUBLIC uses promo-scope artifacts and revised simulation outputs.

### Best way to show 100won inside park 17x

Keep park 17x behavior-only rules as the technical segmentation, then add promo-aware presentation labels and promo distribution/lift tables as the business layer.

The technically defensible structure is:

1. park 17x behavior rule remains the segmentation source.
2. promo0/promo1 composition is shown inside each segment.
3. promo-aware presentation labels are used only as labels, not as new segment rules.
4. PUBLIC contributes narrative and guardrails, not canonical rules.

### general_observation

Keep general_observation as residual/general bucket for now; rename to residual/general observation if used in slides. Decomposition shows review candidates, but this audit does not split it.

### content_preference_target_candidate

Downgrade or rename content_preference_target_candidate to content-context or genre-cue candidate unless the user explicitly accepts stronger targeting language.

PUBLIC's broad content signal problem is relevant because the PUBLIC hotfix measured content_preference_signal as broad. Park's content candidate uses narrower genre/movie flags, but the label still risks implying a strong recommendation target.

### Final presentation label candidates

Use labels from 07_promo_aware_label_proposal.csv only after user approval. The safer family is:

- 100won week3 drop watchlist
- 100won early activation weak watchlist
- 100won interest decay watchlist
- 100won stable conversion profile
- content-context personalization cue
- residual/general observation

### Final score source recommendation

Use park LightGBM expanded_no_payment_device overall_with_promotion as the recommended score source for continuity with 17x and 16x evidence.

### User decisions required

- Whether promo-aware labels may appear on slides.
- Whether general_observation should be renamed to residual/general observation.
- Whether content_preference_target_candidate should be renamed or downgraded.
- Whether PUBLIC action narratives can be adapted into park slides.
- Whether a later, separate promo-scope segmentation redesign should be opened.

## Guardrail

No segment is finalized by this memo. The recommendation is a defense-oriented presentation structure, not a new segmentation assignment.
