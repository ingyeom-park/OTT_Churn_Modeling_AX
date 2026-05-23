from pathlib import Path
import hashlib
import zipfile

import pandas as pd


ROOT = Path(r"C:\Code\ott-churn-prediction")
OUT = ROOT / "FINAL" / "S7_residual_promo_decomposition_diagnostic_260522"
ZIP_PATH = ROOT / "FINAL" / "S7_residual_promo_decomposition_diagnostic_260522_review_package.zip"

MANDATORY = [
    "S7_residual_promo_decomposition_diagnostic_260522.ipynb",
    "00_input_basis_resolution.csv",
    "00_basis_conflict_note.md",
    "01_S7_definition_and_residual_structure.md",
    "01_S7_row_inventory.csv",
    "02_S7_promo_outcome_4cell_summary.csv",
    "03_S7_promo_gap_summary.csv",
    "04_S7_existing_flag_distribution_by_promo_outcome.csv",
    "05_S7_existing_flag_gap_ranking.csv",
    "06_S7_rule_component_coverage.csv",
    "07_S7_rule_near_miss_patterns.csv",
    "08_S7_existing_numeric_feature_profile.csv",
    "09_S7_existing_binary_categorical_profile.csv",
    "10_S7_demographic_action_layer_descriptive.csv",
    "11_S7_decomposition_decision_evidence_table.csv",
    "12_S7_chart_ready_summary.csv",
    "figure_01_S7_promo_churn_rate_comparison.png",
    "figure_02_S7_promo_outcome_4cell_rows.png",
    "figure_03_S7_top_existing_feature_gaps.png",
    "figure_04_S7_existing_flag_gap_heatmap.png",
    "figure_05_S7_rule_near_miss_summary.png",
    "README.md",
    "execution_log.txt",
    "final_checks.csv",
    "source_fingerprint_before_after.csv",
    "review_zip_inventory.csv",
]


def sha256_file(path):
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


inventory_rows = []
for name in MANDATORY:
    path = OUT / name
    inventory_rows.append(
        {
            "zip_member": name,
            "source_path": rel(path),
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else "",
            "sha256": sha256_file(path) if path.exists() else "",
        }
    )

inventory = pd.DataFrame(inventory_rows)
all_exist = bool(inventory["exists"].all())
inventory.to_csv(OUT / "review_zip_inventory.csv", index=False, encoding="utf-8-sig")

checks_path = OUT / "final_checks.csv"
checks = pd.read_csv(checks_path)
checks.loc[checks["check"].eq("review zip inventory verified"), "status"] = "PASS" if all_exist else "FAIL"
checks.loc[checks["check"].eq("review zip inventory verified"), "detail"] = "all mandatory members exist before final zip rebuild"
checks.loc[checks["check"].eq("review zip created"), "status"] = "PASS"
checks.loc[checks["check"].eq("review zip created"), "detail"] = rel(ZIP_PATH)
checks.to_csv(checks_path, index=False, encoding="utf-8-sig")

inventory_rows = []
for name in MANDATORY:
    path = OUT / name
    inventory_rows.append(
        {
            "zip_member": name,
            "source_path": rel(path),
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else "",
            "sha256": sha256_file(path) if path.exists() else "",
        }
    )
pd.DataFrame(inventory_rows).to_csv(OUT / "review_zip_inventory.csv", index=False, encoding="utf-8-sig")

with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for name in MANDATORY:
        zf.write(OUT / name, arcname=name)

with zipfile.ZipFile(ZIP_PATH, "r") as zf:
    names = set(zf.namelist())
missing = [name for name in MANDATORY if name not in names]
if missing:
    raise RuntimeError(f"Missing zip members: {missing}")

print(rel(ZIP_PATH))
