# PUBLIC 17 Caveats and Rejected Alternatives

Age/gender were not used as primary segment rules because they are profile and personalization variables, not behavior problems. Direct demographic naming would overstate evidence and create fairness and interpretation risks.

Overall customer segmentation was rejected because promo1 is the main business scope and promo0 is the comparison scope. A pooled segmentation could obscure 100won-specific patterns.

SHAP-top-feature-only segmentation was rejected because SHAP is model explanation, not a rule system for customer intervention. Segment rules need row-level risk and behavior evidence.

Clustering-only segmentation was rejected because it may produce mathematically coherent groups that are not high-risk or actionable. The current design is auditable and tied to OOF risk.

Final campaign threshold selection was rejected because 17 is design, not operational targeting. GB top20 is a provisional segmentation rule, not a campaign cutoff.

07~10 pending validation caveat is preserved because this step does not complete or replace the deferred validation stages.
