# 05x feature contract rebuild patch 260515

## Patch purpose
This patch corrects specific review findings in the previous 05x outputs without rebuilding the full 05x analysis.
No modeling, EDA, SHAP, Optuna, or segmentation was performed.

## Previous 05x issues found
- The review zip contained a notebook that was not an executed saved copy.
- `USER_KEY` and `is_repurchase` had reason sentences in `llm_proposed_decision` instead of approved decision codes.
- `USER_KEY` and `is_repurchase` had blank `user_approval_required` values.
- `price` and `max_screen` were expanded candidates, but may conflict with prior user decisions.
- Previous preflight recorded `archive_reference_exists = WARN False`.

## Patch changes
- Rebuilt the decision table as a patched 91-column contract copy.
- Restricted `llm_proposed_decision` values to the approved decision-code set.
- Removed blanks from key columns: `column_name`, `llm_proposed_decision`, `reason`, `user_approval_required`, `final_decision_status`.
- Wrote patch audit, approval checklist, candidate contracts, forbidden/audit-only candidates, unresolved review table, diff summary, final checks, and review zip.

## USER_KEY / is_repurchase result
- `USER_KEY`: `forbidden_or_audit_only_candidate`, policy fixed as row identifier / group key only, not a model feature.
- `is_repurchase`: `forbidden_or_audit_only_candidate`, policy fixed as target variable, never a model feature.

## price / max_screen user review
- `price` exists and is marked `unresolved_user_review_required` with `user_approval_required=yes`.
- `max_screen` exists and is marked `unresolved_user_review_required` with `user_approval_required=yes`.
- Caution: 과거 사용자 결정과 충돌 가능성 있음. price/max_screen은 사용자가 제거 또는 대체를 언급한 이력이 있으므로 자동 expanded 승인 금지

## archive_reference WARN
Previous 05x preflight recorded `archive_reference_exists` as `WARN False`.
The patch does not hide this warning. The patch was performed from the existing 05x outputs and source master; the archive reference was an optional reference.

## Before 06x
The final feature-use decision is not complete until the user reviews the approval checklist.
Next step: review `05x_user_approval_checklist.csv`, then decide whether 06x may proceed.
