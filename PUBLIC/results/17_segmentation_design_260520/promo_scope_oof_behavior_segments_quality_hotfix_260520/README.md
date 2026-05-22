> Purpose

PUBLIC 17 segmentation quality hotfix revalidates the saved segmentation and creates a review-only revised proposal.

> Why quality hotfix was needed

content_preference_signal was too broad, several representative segments were too small, and other_needs_review was too large to call a clean middle-risk group.

> What was checked 4 times

Row integrity, score direction, independent assignment recomputation, and business sanity were checked.

> Minimum segment size policy

n >= 300 is representative-candidate size. 100-299 is a small sub-signal. 30-99 is a rare pattern note. n < 30 is case-note only.

> Small segment merge/demotion policy

Small segments are demoted to sub-signals/profile notes unless they pass minimum size and actionability criteria.

> Other_needs_review decomposition

other_needs_review is not simply mid-risk. It is a residual group decomposed by GB risk band and behavior flags.

> Promo1 vs promo0 differential analysis

Promo1 is the 100won-deal scope. Promo0 is the general-customer comparison scope. Differences are descriptive, not causal.

> Revised segment proposal

This hotfix does not finalize segment names. This hotfix does not replace the official assignment without user approval.

> Revised assignment simulation

Revised assignment is a simulation until user approval.

> Demographic/action bridge

Age/gender are profile and action-personalization layers, not primary representative rules.

> Executive rationale memo

The memo explains why small segments were merged/demoted, why content_preference_signal was demoted, and why other remains residual.

> What was not done

No model refit, no Optuna, no SHAP recalculation, no OOF regeneration, no raw source modification, no final campaign threshold.

> Safe wording

Use provisional segment family, review-only simulation, descriptive risk difference, and pending validation.

> Unsafe wording

Do not say final segment, campaign threshold, causal promotion effect, completed 07-10 validation, or other equals mid-risk.

> Next action

Review the zip, approve or revise the proposal, then decide whether 18 business storyline can proceed. 07~10 remain pending validation.
