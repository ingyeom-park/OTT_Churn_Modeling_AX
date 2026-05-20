# 06 log retention distribution EDA

## Scope

Matplotlib-only distribution EDA for `log_retention_w2_ratio` and `log_retention_w3_ratio`.

## Inputs

- `PUBLIC/data/06_expanded_dataset_log_retention.csv`
- `PUBLIC/data/06_expanded_dataset_promo_0_log_retention.csv`
- `PUBLIC/data/06_expanded_dataset_promo_1_log_retention.csv`

## Outputs

- `06_log_retention_distribution_summary.csv`
- `06_log_retention_baseline_direction_summary.csv`
- `06_fig_01_log_retention_histograms.png`
- `06_fig_02_log_retention_boxplot_by_dataset.png`
- `06_fig_03_overall_raw_vs_log_histograms.png`

## Interpretation rule

- log value < 0: lower than week 1 baseline.
- log value = 0: same as week 1 baseline.
- log value > 0: higher than week 1 baseline.
