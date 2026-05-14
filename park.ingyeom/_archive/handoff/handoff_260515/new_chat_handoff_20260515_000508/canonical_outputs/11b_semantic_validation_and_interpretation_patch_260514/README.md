# 11b semantic validation and interpretation patch

This is a semantic validation/documentation patch for the completed 11b baseline growth history.

No modeling rerun was performed. No 11b metrics, CV outputs, AUC values, OOF predictions, or old Step 11 artifacts were modified. Old Step 11 remains preserved as deprecated/pre-patch.

The central clarification is that the 11b ladder is a feature-family growth ladder, not a temporal cutoff ladder. At the day21 scoring point, all day0-20 behavior is already available. Therefore `is_only_w1` and `is_w1_over_50pct` are valid at day21, but they should be described as early-only, front-loaded, or early concentration pattern features, not pure activation.

If `11b_semantic_final_checks.csv` passes, 11b can be treated as the canonical corrected Step 11 for downstream Step 12.
