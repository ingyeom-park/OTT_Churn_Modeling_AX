# PUBLIC 17 promo-scope OOF behavior segmentation design

## Purpose
This is segmentation design, not final campaign targeting. Segment labels are provisional.

## Inputs
The step reads 15 OOF hotfix, 16 SHAP/model explanation, 16b feature family mapping hotfix, and PUBLIC data input CSVs.

## Why promo1 is the main scope
Promo1 is the main 100won business scope; promo0 is the comparison scope.

## OOF score usage
OOF score is row-level risk evidence, not a final campaign threshold. GB top20 is the representative design condition.

## SHAP and 16b family mapping usage
SHAP is model explanation, not causality. 16b hotfix family mapping is used. The original technical_or_unknown bucket is not used.

## Multi-flag design
Flags combine OOF risk, activity, cold-start, retention, inactivity, usage concentration, genre, and content signals. cold_start_weak is corrected so cold-start fixed success flags are not treated as weak activation.

## Representative segment design
Each row receives exactly one provisional representative segment by priority order.

## Demographic profile and action personalization
Age/gender are action personalization variables after EDA evidence, not default representative segment rules.

## Executive rationale memo
See `17_segment_rationale_memo_for_executives.md`.

## What was not done
No model refit, Optuna, SHAP recalculation, OOF regeneration, final model selection, campaign threshold finalization, or final segment naming was performed.

## 07~10 pending validation caveat
07~10 remain pending validation.

## Safe wording
- This is segmentation design, not final campaign targeting.
- Segment labels are provisional.
- Promo1 is the main 100won business scope; promo0 is the comparison scope.
- OOF score is row-level risk evidence, not a final campaign threshold.
- SHAP is model explanation, not causality.
- 16b hotfix family mapping is used.
- Age/gender are action personalization variables after EDA evidence, not default representative segment rules.
- 07~10 remain pending validation.

## Unsafe wording
- segment is final
- 100won caused churn
- SHAP proves cause
- age/gender causes churn
- OOF score is campaign threshold
- 07~10 are completed
- dashboard can be finalized automatically

## Next action
Review the 17 package, then decide whether to proceed to 18 business storyline or segment hotfix.
