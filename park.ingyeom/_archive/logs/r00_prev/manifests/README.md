# 00_realign_archive_cleanup_260515

## Purpose

This cleanup preserves existing work while removing old modeling artifacts from the active canonical path. The project now uses two plans only:

- Conservative plan: existing conservative_safe_22 feature baseline/reference.
- Expanded plan: re-review the full 91-column universe, promote only allowed features, then rerun feature-set-aware 11/12 modeling.

No raw source CSV was modified. No files were deleted. Existing artifacts were moved into `park.ingyeom/_archive/realignment_260515` with a manifest.

## Archive Layout

- `conservative_safe_22_reference`: old 11, 11b, 12c, and 13 artifacts reclassified as conservative 22-feature references.
- `deprecated_or_superseded`: old active Step 12 artifacts that should not remain canonical.
- `aborted_or_incomplete`: Step 14 Optuna traces created before 13b review-feature resolution.
- `manifests`: cleanup manifest, active remaining inventory, folder summary, final checks, and this README.

## What Was Archived

The cleanup archived existing active paths for:

- `11_baseline_growth_history_260513`
- `11b_baseline_growth_history_ladder_fix_260514`
- `11b_semantic_validation_and_interpretation_patch_260514`
- `12_model_baseline_comparison_canonical_260514`
- `12_full_feature_preliminary_model_260513`
- `13_lightweight_synthesis_for_mentor_report_260515`
- `14_optuna_candidate_tuning_260515`

Detailed path-level actions are in `00_realign_archive_cleanup_manifest.csv`.

## What Remains Active

Active 05-10 artifacts remain available as prior validation/reference material. Any remaining active 05-14 related folders after cleanup are listed in `00_realign_active_remaining_inventory.csv`.

## Next Step

The next modeling pipeline step is:

`13b_review_feature_resolution_and_sensitivity`

Until 13b passes, do not re-enter 11/12/14/16/17 as active canonical modeling.
