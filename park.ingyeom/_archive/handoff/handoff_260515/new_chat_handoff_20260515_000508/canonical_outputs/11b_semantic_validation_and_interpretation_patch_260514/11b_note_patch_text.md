## 2026-05-14 | 11b semantic validation and interpretation patch

- why this patch was needed: 11b fixed the Step 11 L2 ladder contamination, but the semantic meaning of L1 still needed clearer wording.
- not a model rerun: this patch did not rerun modeling, did not change CV metrics, did not change OOF predictions, and did not edit old Step 11 outputs.
- L1 semantic clarification: L1 is early activation plus early concentration / early-only pattern family, not a week1-only temporal cutoff model.
- feature-family ladder vs temporal cutoff ladder: Step 11b ladder grows by feature family. At the day21 scoring point, all day0-20 behavior is already observable.
- is_only_w1 / is_w1_over_50pct interpretation: these are valid day21 features but not pure activation. They should be described as early-only, front-loaded, or early concentration patterns.
- 11b canonical status after patch: 11b can be used as the canonical corrected Step 11 after this semantic documentation patch.
- old 11 deprecated status: old Step 11 remains preserved as deprecated/pre-patch and should not be used for downstream modeling interpretation.
- next step recommendation: 12_model_baseline_comparison_260513.
