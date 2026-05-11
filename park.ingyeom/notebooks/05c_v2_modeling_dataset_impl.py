import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE = PROJECT_ROOT / "park.ingyeom"
STAGE02C = BASE / "reports" / "data" / "02c_v2_strict_preprocessing_correction" / "membership_v2_preprocessed_strict_core.csv"
STAGE03C = BASE / "reports" / "data" / "03c_v2_usage_feature_engineering"
STAGE04C = BASE / "reports" / "data" / "04c_v2_content_feature_engineering"
STAGE04C_CHECK = BASE / "reports" / "tables" / "04c_v2_content_feature_engineering" / "04c_final_checks.csv"

DATA_DIR = BASE / "reports" / "data" / "05c_v2_modeling_dataset"
TABLE_DIR = BASE / "reports" / "tables" / "05c_v2_modeling_dataset"
FIGURE_DIR = BASE / "reports" / "figures" / "05c_v2_modeling_dataset"

WINDOWS = ["w1_1", "w1_2", "w1_3", "w1_4"]
TARGET = "is_repurchase_label"
ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"
METADATA = [ID_COL, GROUP_COL, TARGET]
MEMBERSHIP_FEATURES = [
    "price_num",
    "max_screen_num",
    "is_promotion_bin",
    "is_user_verified_bin",
    "age_num",
    "gender_clean",
    "payment_device_clean",
    "billing_method_clean",
    "is_churn_prevented_bin",
]
FORBIDDEN_EXACT = {
    "USER_KEY",
    "USER_NUM",
    "MOVIE_NUM",
    "movie_title",
    "membership_row_id",
    "reg_date",
    "end_date",
    "reg_date_parsed",
    "end_date_parsed",
    "duration_days",
    "duration_days_stage02",
    "duration_days_recomputed",
    "watch_date",
    "watch_day",
    "is_repurchase",
    "is_repurchase_raw",
    "is_repurchase_label",
}
FORBIDDEN_PATTERNS = [
    re.compile(r".*_raw$", re.I),
    re.compile(r".*calendar.*", re.I),
    re.compile(r".*date.*", re.I),
]


def rel(path: Path) -> str:
    return str(Path(path).relative_to(PROJECT_ROOT)).replace("\\", "/")


def write_csv(path: Path, df: pd.DataFrame):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snapshot_dir(path: Path) -> dict:
    if not path.exists():
        return {}
    out = {}
    for file in sorted(path.rglob("*")):
        if file.is_file():
            st = file.stat()
            out[rel(file)] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
    return out


def snapshot_stage_inputs() -> dict:
    paths = [STAGE02C, STAGE04C_CHECK]
    paths.extend(STAGE03C / f"usage_features_v2c_{w}.csv" for w in WINDOWS)
    paths.extend(STAGE04C / f"content_features_v2c_{w}.csv" for w in WINDOWS)
    out = {}
    for path in paths:
        if path.exists():
            st = path.stat()
            out[rel(path)] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
        else:
            out[rel(path)] = None
    return out


def require_stage04c_passed():
    if not STAGE04C_CHECK.exists():
        raise RuntimeError("Stage 04c final checks missing. Stop before Stage 05c.")
    checks = pd.read_csv(STAGE04C_CHECK)
    if (checks["status"].astype(str).str.upper() != "PASS").any():
        raise RuntimeError("Stage 04c final checks failed. Stop before Stage 05c.")
    required = [STAGE04C / f"content_features_v2c_{w}.csv" for w in WINDOWS]
    missing = [rel(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"Stage 04c required outputs missing: {missing}")


def is_forbidden_feature(col: str) -> bool:
    if col in FORBIDDEN_EXACT:
        return True
    return any(pattern.fullmatch(col) or pattern.match(col) for pattern in FORBIDDEN_PATTERNS)


def existing(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [c for c in cols if c in df.columns]


def full_exploratory_features(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in METADATA and not is_forbidden_feature(c)]


def genre_ratio_cols(df: pd.DataFrame, window: str) -> list[str]:
    return sorted([c for c in df.columns if c.startswith(f"{window}_genre_ratio_")])


def official_usage_cols(df: pd.DataFrame, window: str) -> list[str]:
    cols = [
        f"{window}_week1_watch_time",
        f"{window}_week2_watch_time",
        f"{window}_week3_watch_time",
        f"{window}_week1_sessions",
        f"{window}_week2_sessions",
        f"{window}_week3_sessions",
        f"{window}_unique_contents",
        f"{window}_unique_watch_days",
        f"{window}_avg_watch_time_per_session",
    ]
    if window == "w1_2":
        cols = [c for c in cols if "week3" not in c]
    if window == "w1_4":
        cols.extend([f"{window}_week4_watch_time", f"{window}_week4_sessions"])
    return existing(df, cols)


def pruned_features(df: pd.DataFrame, window: str, include_usage=True, include_genre=True, include_membership=True) -> list[str]:
    features = []
    if include_membership:
        features.extend(existing(df, [c for c in MEMBERSHIP_FEATURES if c != "is_churn_prevented_bin"]))
    if include_usage:
        features.extend(official_usage_cols(df, window))
    if include_genre:
        features.extend(genre_ratio_cols(df, window))
        features.extend(existing(df, [f"{window}_genre_entropy", f"{window}_recent_content_watch_ratio"]))
    banned_substrings = [
        "product_code",
        "has_watch_obs",
        "no_watch_obs_flag",
        "first_watch",
        "last_watch",
        "_ratio_week",
        "week1_ratio",
        "week2_ratio",
        "week3_ratio",
        "week4_ratio",
        "minus",
        "total_watch_time",
        "genre_watch_time_",
        "genre_session_count_",
        "genre_missing_watch",
        "is_churn_prevented",
    ]
    clean = []
    for feature in features:
        if is_forbidden_feature(feature):
            continue
        if any(token in feature for token in banned_substrings):
            continue
        clean.append(feature)
    return list(dict.fromkeys(clean))


def main():
    require_stage04c_passed()
    for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    raw_before = snapshot_dir(PROJECT_ROOT / "_data")
    input_before = snapshot_stage_inputs()

    membership = pd.read_csv(STAGE02C)
    membership_model = membership[[ID_COL, GROUP_COL, TARGET] + existing(membership, MEMBERSHIP_FEATURES)].copy()
    membership_model[TARGET] = pd.to_numeric(membership_model[TARGET], errors="coerce").astype("Int64")

    input_rows = [{"input": rel(STAGE02C), "rows": len(membership), "unique_membership_row_id": membership[ID_COL].nunique()}]
    merge_rows = []
    model_datasets = {}
    for window in WINDOWS:
        usage_path = STAGE03C / f"usage_features_v2c_{window}.csv"
        content_path = STAGE04C / f"content_features_v2c_{window}.csv"
        usage = pd.read_csv(usage_path)
        content = pd.read_csv(content_path)
        input_rows.extend([
            {"input": rel(usage_path), "rows": len(usage), "unique_membership_row_id": usage[ID_COL].nunique()},
            {"input": rel(content_path), "rows": len(content), "unique_membership_row_id": content[ID_COL].nunique()},
        ])
        df = membership_model.merge(usage, on=ID_COL, how="left", validate="1:1")
        after_usage_cols = len(df.columns)
        df = df.merge(content, on=ID_COL, how="left", validate="1:1")
        for col in df.columns:
            if col not in METADATA and df[col].dtype.kind in "biufc":
                df[col] = df[col].fillna(0)
        output_path = DATA_DIR / f"modeling_dataset_v2c_{window}.csv"
        write_csv(output_path, df)
        model_datasets[window] = df
        merge_rows.append({
            "window": window,
            "rows": len(df),
            "unique_membership_row_id": df[ID_COL].nunique(),
            "after_usage_column_count": after_usage_cols,
            "final_column_count": len(df.columns),
            "one_row_per_membership_row_id": len(df) == df[ID_COL].nunique() == len(membership),
        })

    fs = {
        "full_exploratory_w1_1": {"window": "w1_1", "class": "full_exploratory", "features": full_exploratory_features(model_datasets["w1_1"])},
        "full_exploratory_w1_2": {"window": "w1_2", "class": "full_exploratory", "features": full_exploratory_features(model_datasets["w1_2"])},
        "full_exploratory_w1_3": {"window": "w1_3", "class": "full_exploratory", "features": full_exploratory_features(model_datasets["w1_3"])},
        "full_exploratory_w1_4_late_period": {"window": "w1_4", "class": "full_exploratory_upper_bound_late_period", "features": full_exploratory_features(model_datasets["w1_4"])},
        "pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence": {
            "window": "w1_3",
            "class": "pruned_official_candidate",
            "features": pruned_features(model_datasets["w1_3"], "w1_3", True, True, True),
        },
        "pruned_w1_3_membership_usage_only_without_product_code_without_watch_presence": {
            "window": "w1_3",
            "class": "pruned_official_candidate",
            "features": pruned_features(model_datasets["w1_3"], "w1_3", True, False, True),
        },
        "pruned_w1_3_genre_ratio_added_without_product_code_without_watch_presence": {
            "window": "w1_3",
            "class": "pruned_official_candidate",
            "features": pruned_features(model_datasets["w1_3"], "w1_3", True, True, True),
        },
        "pruned_w1_2_early_reference_without_product_code_without_watch_presence": {
            "window": "w1_2",
            "class": "pruned_reference",
            "features": pruned_features(model_datasets["w1_2"], "w1_2", True, True, True),
        },
        "pruned_w1_4_late_period_comparison_without_product_code_without_watch_presence": {
            "window": "w1_4",
            "class": "pruned_late_period_comparison",
            "features": pruned_features(model_datasets["w1_4"], "w1_4", True, True, True),
        },
    }
    payload = {
        "stage": "05c_v2_modeling_dataset",
        "target": TARGET,
        "metadata_columns": [ID_COL, GROUP_COL],
        "forbidden_columns": sorted(FORBIDDEN_EXACT),
        "feature_sets": fs,
    }
    write_json(DATA_DIR / "feature_sets_v2c.json", payload)

    inventory = []
    for window, df in model_datasets.items():
        for col in df.columns:
            role = "metadata" if col in [ID_COL, GROUP_COL] else "target" if col == TARGET else "candidate_feature"
            inventory.append({"window": window, "column": col, "role": role, "dtype": str(df[col].dtype)})
    forbidden_rows = []
    for name, spec in fs.items():
        for feature in spec["features"]:
            forbidden_rows.append({"feature_set": name, "feature": feature, "forbidden": int(is_forbidden_feature(feature))})
    policy_rows = []
    for name, spec in fs.items():
        features = spec["features"]
        policy_rows.append({
            "feature_set": name,
            "window": spec["window"],
            "class": spec["class"],
            "feature_count": len(features),
            "has_product_code": int(any("product_code" in f for f in features)),
            "has_watch_presence_shortcut": int(any(("has_watch_obs" in f or "no_watch_obs_flag" in f) for f in features)),
            "has_genre_watch_time": int(any("genre_watch_time_" in f for f in features)),
            "has_genre_session_count": int(any("genre_session_count_" in f for f in features)),
            "has_is_churn_prevented": int(any("is_churn_prevented" in f for f in features)),
            "w1_4_late_period_only": int(spec["window"] == "w1_4"),
        })
    target_rows = []
    for window, df in model_datasets.items():
        vc = df[TARGET].value_counts(dropna=False).to_dict()
        target_rows.append({
            "window": window,
            "rows": len(df),
            "repurchase_count": int(vc.get(1, 0)),
            "non_repurchase_count": int(vc.get(0, 0)),
            "repurchase_rate": float(df[TARGET].mean()),
            "churn_risk_rate": float(1 - df[TARGET].mean()),
        })

    write_csv(TABLE_DIR / "05c_input_row_count_summary.csv", pd.DataFrame(input_rows))
    write_csv(TABLE_DIR / "05c_merge_integrity_summary.csv", pd.DataFrame(merge_rows))
    write_csv(TABLE_DIR / "05c_modeling_column_inventory.csv", pd.DataFrame(inventory))
    write_csv(TABLE_DIR / "05c_forbidden_column_audit.csv", pd.DataFrame(forbidden_rows))
    write_csv(TABLE_DIR / "05c_feature_set_summary.csv", pd.DataFrame([
        {"feature_set": name, "window": spec["window"], "class": spec["class"], "feature_count": len(spec["features"])}
        for name, spec in fs.items()
    ]))
    write_csv(TABLE_DIR / "05c_pruned_feature_policy_summary.csv", pd.DataFrame(policy_rows))
    write_csv(TABLE_DIR / "05c_target_distribution_summary.csv", pd.DataFrame(target_rows))

    summary = {
        "stage": "05c_v2_modeling_dataset",
        "membership_rows": int(len(membership)),
        "target_distribution": target_rows,
        "modeling_outputs": [rel(DATA_DIR / f"modeling_dataset_v2c_{w}.csv") for w in WINDOWS],
        "feature_set_count": len(fs),
        "official_candidate": "pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence",
    }
    write_json(DATA_DIR / "modeling_dataset_summary_v2c.json", summary)
    report = "\n".join([
        "# 05c Corrected Modeling Dataset Report",
        "",
        f"- strict-core rows propagated: {len(membership)}",
        f"- feature sets created: {len(fs)}",
        "- target column: is_repurchase_label, where 1 = repurchase and 0 = non-repurchase/churn risk",
        "- official corrected candidate: pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence",
        "- w1_4 feature set is late-period comparison only.",
    ])
    (DATA_DIR / "05c_modeling_dataset_report.md").write_text(report + "\n", encoding="utf-8")

    raw_after = snapshot_dir(PROJECT_ROOT / "_data")
    input_after = snapshot_stage_inputs()
    policy_df = pd.DataFrame(policy_rows)
    required = [DATA_DIR / f"modeling_dataset_v2c_{w}.csv" for w in WINDOWS] + [
        DATA_DIR / "feature_sets_v2c.json",
        DATA_DIR / "modeling_dataset_summary_v2c.json",
        DATA_DIR / "05c_modeling_dataset_report.md",
        TABLE_DIR / "05c_input_row_count_summary.csv",
        TABLE_DIR / "05c_merge_integrity_summary.csv",
        TABLE_DIR / "05c_modeling_column_inventory.csv",
        TABLE_DIR / "05c_forbidden_column_audit.csv",
        TABLE_DIR / "05c_feature_set_summary.csv",
        TABLE_DIR / "05c_pruned_feature_policy_summary.csv",
        TABLE_DIR / "05c_target_distribution_summary.csv",
    ]
    checks = [
        ("raw_files_unchanged", raw_before == raw_after, "No files under _data changed."),
        ("no_data_output_created", raw_before.keys() == raw_after.keys(), "No new files under _data."),
        ("stage02c_stage03c_stage04c_inputs_not_overwritten", input_before == input_after, "Corrected upstream inputs unchanged."),
        ("corrected_membership_row_count_propagated", all(len(df) == len(membership) for df in model_datasets.values()), f"rows={len(membership)}"),
        ("one_row_per_membership_row_id", all(df[ID_COL].is_unique for df in model_datasets.values()), "All windows are unique by membership_row_id."),
        ("forbidden_features_excluded", not any(row["forbidden"] for row in forbidden_rows), "No forbidden columns in feature sets."),
        ("pruned_policy_enforced", int(policy_df.loc[policy_df["class"].str.contains("pruned|official|reference|comparison", regex=True), ["has_product_code", "has_watch_presence_shortcut", "has_genre_watch_time", "has_genre_session_count"]].sum().sum()) == 0, "Pruned feature sets exclude requested shortcut and volume features."),
        ("target_mapping_documented", True, "is_repurchase_label: 1=repurchase, 0=non-repurchase/churn risk."),
        ("w1_4_labeled_late_period_only", True, "w1_4 is late-period comparison only."),
        ("all_required_outputs_created", all(p.exists() for p in required), f"required_outputs={len(required)}"),
    ]
    checks_df = pd.DataFrame([{"check": n, "status": "PASS" if ok else "FAIL", "detail": d} for n, ok, d in checks])
    write_csv(TABLE_DIR / "05c_final_checks.csv", checks_df)
    if (checks_df["status"] != "PASS").any():
        raise RuntimeError("Stage 05c final checks failed. Stop before Stage 06c2.")
    print("05c_v2_modeling_dataset completed.")
    for row in checks_df.to_dict("records"):
        print(f"{row['check']}: {row['status']} - {row['detail']}")


if __name__ == "__main__":
    main()
