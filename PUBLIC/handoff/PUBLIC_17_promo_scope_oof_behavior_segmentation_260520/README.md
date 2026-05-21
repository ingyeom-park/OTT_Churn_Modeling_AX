# PUBLIC 17 promo-scope OOF behavior segmentation handoff

## Purpose
Review handoff for provisional promo-scope segmentation design.

## Inputs checked
15 OOF hotfix, 16 SHAP, 16b feature family mapping, and promo input CSV files.

## Outputs generated
Base datamart, internal flags, representative segment assignment, segment summary, profiles, SHAP family evidence, demographic/action matrices, business actions, executive rationale memo, rejected alternatives memo, and readiness for 18.

## Execution status
Notebook executed through nbconvert. Helper is included in the review zip.

## Segment design summary
Promo1 is the main 100won scope. Promo0 is comparison. GB top20 is the primary design risk condition.

## Executive rationale memo status
`17_segment_rationale_memo_for_executives.md` is included.

## Demographic action policy
Age/gender are profile/action personalization variables only after EDA evidence.

## 16b family mapping dependency
16b hotfix family mapping is used; original technical_or_unknown is not used.

## 07~10 pending validation
07~10 remain pending validation.

## Files included in review zip
See zip inventory.

## Next recommended action
Review the ZIP and decide whether to proceed to 18 or request segment hotfix.
