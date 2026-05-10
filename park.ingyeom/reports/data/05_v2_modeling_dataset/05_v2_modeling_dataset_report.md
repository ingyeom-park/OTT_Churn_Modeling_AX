# 05_v2 Modeling Dataset Report

## Scope
- Created final modeling tables only.
- No model training, SHAP, segmentation, or business simulation was performed.

## Outputs
- park.ingyeom/reports/data/05_v2_modeling_dataset/modeling_dataset_v2_w1_3.csv
- park.ingyeom/reports/data/05_v2_modeling_dataset/modeling_dataset_v2_w1_4.csv
- park.ingyeom/reports/data/05_v2_modeling_dataset/feature_sets_v2.json
- park.ingyeom/reports/data/05_v2_modeling_dataset/modeling_dataset_summary.json

## Row Counts
- w1_3: 23,933 rows.
- w1_4: 23,933 rows.

## Feature Policy
- `is_repurchase` is target only.
- `USER_KEY` is group metadata only.
- `membership_row_id` is ID metadata only.
- Categorical columns are not one-hot encoded here and are recorded for Stage 06 pipelines.
