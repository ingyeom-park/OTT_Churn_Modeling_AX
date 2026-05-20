# 06y_promo_split_260520

## Purpose
Split the PUBLIC 06x expanded dataset into two files using `is_promotion`.

## Source
- `results\_06x_dataset_generation_260515\06x_expanded_dataset.csv`

## Outputs
- `results\_06y_promo_split_260520\06y_expanded_dataset_promo_0.csv`: rows where `is_promotion == 0`
- `results\_06y_promo_split_260520\06y_expanded_dataset_promo_1.csv`: rows where `is_promotion == 1`

## Validation
- Source rows: 23097
- promo_0 rows: 11193
- promo_1 rows: 11904
- unexpected `is_promotion` rows: 0
- Column order is preserved from the source dataset.
- Source dataset hash and mtime are checked before and after writing outputs.
