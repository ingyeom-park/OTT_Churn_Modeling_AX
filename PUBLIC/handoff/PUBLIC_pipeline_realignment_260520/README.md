# PUBLIC pipeline realignment 260520

## 1. Purpose
This handoff records a structural realignment of `PUBLIC` to the original `park.ingyeom`-style pipeline sequence from 06 through 18. This work is not model execution.

## 2. User-confirmed assumptions
- 01~05 contracts are treated as inherited by user confirmation.
- PUBLIC work must continue from 06 in the original sequence.
- Existing files must not be deleted.
- Ambiguous artifacts require user review before migration.
- 07~10 must not be skipped before modeling.

## 3. What was changed
- Canonical stage folders were created for 06, 07, 08, 09, 10, 11, 12, 14, 15, 16, 17, and 18.
- Placeholder README files were created under each canonical notebook stage folder.
- Explicitly misnumbered 06 model notebooks and rerun outputs were moved to archive/reference locations.
- Handoff CSVs, final checks, note append, zip inventory, and a review zip were created.

## 4. What was not changed
- No raw source data was modified.
- `park.ingyeom` was not modified.
- No model notebook was executed.
- No Optuna, SHAP, or segmentation work was performed.
- Existing non-06 model outputs were not migrated because they need user review.

## 5. Pipeline stage map
See `PUBLIC_pipeline_stage_map_260520.csv` for the canonical folder map, allowed actions, forbidden actions, and required gates.

## 6. Misnumbered artifact handling
Files named as 06 but behaving as modeling artifacts are not canonical 06 artifacts. They were moved to archive/reference when explicitly detected. See `misnumbered_06_model_artifacts_audit.csv`.

## 7. Empty placeholder folders
Empty folders are intentional placeholders. They preserve the required sequence even when a stage has not been executed.

## 8. Current canonical next step
The next canonical action is 06 dataset/input check, followed by 07 feature mapping, 08 EDA, 09 2x2 EDA, and 10 redundancy/proxy pre-audit before 11 modeling.

## 9. Blockers before modeling
11 modeling is blocked until 07~10 are completed or explicitly validated as inherited. 06 alone is not enough to begin modeling.

## 10. Safe / unsafe wording
Safe wording:
- 01~05 contracts are inherited by user confirmation, but 06 and downstream PUBLIC artifacts must still follow the original park.ingyeom pipeline sequence.
- 06 is dataset/input preparation only. Modeling must start only after 07~10 are completed or explicitly validated as inherited.

Unsafe wording:
- 06 model results are canonical.
- 07~10 can be skipped.
- Modeling is complete.
- SHAP or segmentation can start now.
- final_checks alone proves semantic validity.
