# 06f v2 Reduced-Feature Interpretable Baseline Audit

## Scope
- This stage trained fixed diagnostic LogisticRegression and HistGradientBoostingClassifier models only.
- No Optuna, SHAP, segmentation, business simulation, or raw-file modification was performed.
- Feature sets were defined before evaluation from interpretability, redundancy, and timing-safety principles.

## Key Answers
1. Most mentor-safe reduced feature set: `reduced_no_target_adjacent_timing` with HGB AUC 0.857099.
2. Most presentation-safe reduced feature set: `reduced_no_target_adjacent_timing` with HGB AUC 0.857099.
3. AUC lost from full reference to mentor-safe reduced model: 0.015360.
4. The mentor-safe model still provides ranking value: top-decile churn lift 2.697066.
5. Full model upper-bound internal reference: `full_reference_w1_3` HGB AUC 0.872459.
6. Exclude individual interpretation of week3 timing, first/last watch timing, ratios/deltas, and genre volume/session features.
7. Stage 07r SHAP should be interpreted mainly at feature-family level, not as independent causal feature effects.
8. Stage 08b segmentation should be framed as behavior-pattern grouping, not causal intervention proof.

## Comparison Context
- Stage 06 full current w1_3 AUC: 0.870464.
- Stage 06c conservative AUC reference: 0.865924.
- Stage 06e exact w1_2 AUC: 0.740175.
- Stage 06e exact w1_4 AUC: 0.902250, late-period only.

## Mentor Message
The high full-feature AUC should not be headlined as early-warning performance. The safer claim is that exact early-window and reduced-feature models still retain useful churn-risk ranking, while the full w1_3 model is an upper-bound internal ranking result that requires timing and redundancy caveats.
