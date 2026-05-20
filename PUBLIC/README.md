# PUBLIC workspace

## Folder map

- `data/`: PUBLIC pipeline input data.
- `notebooks/`: executable notebooks and notebook-generation scripts.
- `results/`: generated outputs, audit tables, model outputs, and review inventories.
- `zip/`: review packages created from PUBLIC workflows.
- `legacy/`: older PUBLIC files kept for reference only.
- `note.md`: chronological PUBLIC work notes.

## Current 06 flow

1. Run `notebooks/06x_dataset_generation_260515.ipynb`.
2. Check `results/_06x_dataset_generation_260515/06x_final_checks.csv`.
3. Run `notebooks/06y_promo_split_260520.ipynb`.
4. Check `results/_06y_promo_split_260520/06y_final_checks.csv`.

The current PUBLIC source master is `data/260520_raw_Membership_v2_with_derived_features.csv`.
