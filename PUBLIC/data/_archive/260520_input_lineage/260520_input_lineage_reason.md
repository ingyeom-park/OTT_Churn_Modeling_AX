# 260520_input_lineage reason

This folder stores intermediate lineage and validation files used to trace how the current model input files were prepared.

Reason for isolation:

- These files are not directly consumed by the current model notebooks.
- The active model inputs remain in `PUBLIC/data/06_model_input_promo_0.csv` and `PUBLIC/data/06_model_input_promo_1.csv`.
- These files are retained for audit and recovery only, not for direct modeling.
