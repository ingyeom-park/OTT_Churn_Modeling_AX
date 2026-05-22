> Purpose

Restore demographic profile and action personalization evidence after PUBLIC 17 quality hotfix.

> Why this demographic hotfix was needed

The revised five-family segmentation can be reviewed, but 18 business storyline needs age/gender profile and behavior evidence for careful personalization.

> What was preserved from 17 quality hotfix

This hotfix does not change revised segment assignment. It reads the quality hotfix assignment simulation as fixed input.

> What was recalculated

Age group profile, gender derivation, segment demographic profile, age behavior profile, gender behavior profile, and action matrix.

> Age group profile

age_group is used for profile and action review only.

> Gender derivation logic

gender_derived is derived from is_female and is_male with unknown and conflict handling.

> Age behavior profile

Age behavior differences are descriptive EDA evidence, not causal evidence.

> Gender behavior profile

Gender behavior differences are descriptive EDA evidence, not causal evidence.

> Action personalization matrix

Demographic action variants require EDA evidence.

> Executive supplement memo

The supplement memo explains how to use demographic evidence in 18 without overclaiming.

> What was not done

No representative reassignment, no model refit, no OOF regeneration, no SHAP recalculation, no Optuna, no campaign threshold.

> Safe wording

Age/gender are not representative segment rules. Demographic evidence is a profile/action layer.

> Unsafe wording

Do not say age/gender caused churn or that demographic modifiers are final campaign policy.

> Next action

18 business storyline requires user review.
