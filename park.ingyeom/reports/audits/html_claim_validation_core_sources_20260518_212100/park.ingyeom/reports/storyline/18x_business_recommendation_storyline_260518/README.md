# 18x_business_recommendation_storyline_260518

## Purpose
18x converts verified 17x segmentation outputs into presentation-ready business recommendation storyline artifacts. It does not perform new modeling, SHAP recalculation, segmentation regeneration, dashboard generation, or final campaign policy selection.

## Inputs
The package reads 17x segment summary, assignment, rules, feature profile, SHAP evidence link, proxy audit, age40-unverified-iOS audit, action candidates, dashboard handoff, safe/unsafe wording, open risks, and final checks. `17x_final_checks.csv` is verified as PASS.

## How to Use
Use `18x_storyline_master.md` and `18x_presentation_narrative_script.md` for the main presentation flow, `18x_slide_outline.csv` for slide planning, and `18x_mentor_QA_defense.csv` for backup defense logic.

## Interpretation Limits
Use subscription-event rows, not customer count. Segment labels are provisional representative segments. Recommendations are campaign candidates and require A/B testing. SHAP is model explanation, not causal evidence. 100-won-deal differences are observed group differences, not causal effects. Payment/auth/demographic proxies are not recommendation bases.

## Remaining Risks
See `18x_open_risks.csv`. Main risks are provisional segment names, need for A/B test, row-level interpretation, content mapping proxy caveat, and exclusion of day21+ behavior from features.
