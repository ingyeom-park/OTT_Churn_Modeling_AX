import json
import platform
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


STAGE_NAME = "02c_v2_strict_preprocessing_correction"


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "park.ingyeom").exists() and (candidate / "_data").exists():
            return candidate
    raise FileNotFoundError("Project root not found.")


PROJECT_ROOT = find_root(Path.cwd())
BASE = PROJECT_ROOT / "park.ingyeom"
STAGE02_DATA = BASE / "reports" / "data" / "02_v2_preprocessing_policy"
STAGE02B_DATA = BASE / "reports" / "data" / "02b_v2_preprocessing_forensic_audit"
STAGE02B_TABLE = BASE / "reports" / "tables" / "02b_v2_preprocessing_forensic_audit"
STAGE03_TABLE = BASE / "reports" / "tables" / "03_v2_usage_feature_engineering"
STAGE04_TABLE = BASE / "reports" / "tables" / "04_v2_content_feature_engineering"

DATA_DIR = BASE / "reports" / "data" / STAGE_NAME
TABLE_DIR = BASE / "reports" / "tables" / STAGE_NAME
FIGURE_DIR = BASE / "reports" / "figures" / STAGE_NAME


def rel(path: Path) -> str:
    return str(Path(path).resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, df: pd.DataFrame) -> None:
    df.to_csv(path, index=False, encoding="utf-8-sig")


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def snapshot_paths(paths) -> dict:
    out = {}
    for path in paths:
        path = Path(path)
        if path.exists() and path.is_file():
            st = path.stat()
            out[rel(path)] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
    return out


def snapshot_dirs(dirs) -> dict:
    files = []
    for directory in dirs:
        directory = Path(directory)
        if directory.exists():
            files.extend([p for p in directory.rglob("*") if p.is_file()])
    return snapshot_paths(files)


def norm_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()


def missingish(series: pd.Series) -> pd.Series:
    s = norm_text(series).str.lower()
    return s.isna() | s.isin(["", "nan", "none", "null", "na", "n/a", "__missing__"])


def parse_number(series: pd.Series) -> pd.Series:
    s = norm_text(series).str.replace(",", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


def parse_date(series: pd.Series) -> pd.Series:
    s = norm_text(series)
    parsed = pd.to_datetime(s, errors="coerce", format="%y-%m-%d")
    needs_retry = parsed.isna() & ~missingish(s)
    if needs_retry.any():
        parsed_retry = pd.to_datetime(s[needs_retry], errors="coerce")
        parsed.loc[needs_retry] = parsed_retry
    return parsed


def value_counts_df(df: pd.DataFrame, column: str, label: str, value_col: str = "value") -> pd.DataFrame:
    if column not in df.columns:
        return pd.DataFrame(columns=["dataset", "column", value_col, "count", "share"])
    values = df[column].astype("object").where(pd.notna(df[column]), "__NA__").astype(str)
    vc = values.value_counts(dropna=False).reset_index()
    vc.columns = [value_col, "count"]
    vc["dataset"] = label
    vc["column"] = column
    vc["share"] = np.where(len(df) > 0, vc["count"] / len(df), 0)
    return vc[["dataset", "column", value_col, "count", "share"]]


def numeric_summary(df: pd.DataFrame, column: str, label: str) -> dict:
    if column not in df.columns:
        return {
            "dataset": label,
            "column": column,
            "count": 0,
            "missing": 0,
            "mean": np.nan,
            "median": np.nan,
            "min": np.nan,
            "max": np.nan,
        }
    s = pd.to_numeric(df[column], errors="coerce")
    return {
        "dataset": label,
        "column": column,
        "count": int(s.notna().sum()),
        "missing": int(s.isna().sum()),
        "mean": float(s.mean()) if s.notna().any() else np.nan,
        "median": float(s.median()) if s.notna().any() else np.nan,
        "min": float(s.min()) if s.notna().any() else np.nan,
        "max": float(s.max()) if s.notna().any() else np.nan,
    }


def binary_map_observed(series: pd.Series) -> tuple[pd.Series, pd.DataFrame]:
    raw = norm_text(series)
    upper = raw.str.upper()
    observed = sorted([v for v in upper.dropna().unique().tolist() if v != ""])
    observed_set = set(observed)
    mapping = {}
    policy = "unmapped"
    if observed_set.issubset({"Y", "N"}):
        mapping = {"Y": 1, "N": 0}
        policy = "Y/N"
    elif observed_set.issubset({"O", "X"}):
        mapping = {"O": 1, "X": 0}
        policy = "O/X"
    elif observed_set.issubset({"1", "0"}):
        mapping = {"1": 1, "0": 0}
        policy = "1/0"
    mapped = upper.map(mapping).astype("float")
    policy_rows = []
    for value in sorted(set(observed + ["__MISSING__"])):
        if value == "__MISSING__":
            count = int(missingish(raw).sum())
            mapped_value = ""
            action = "flag_unknown"
            unexpected = count > 0
        else:
            count = int((upper == value).sum())
            mapped_value = mapping.get(value, "")
            action = "map" if value in mapping else "flag_unknown"
            unexpected = value not in mapping
        policy_rows.append(
            {
                "observed_value": value,
                "mapped_value": mapped_value,
                "count": count,
                "mapping_policy": policy,
                "action": action,
                "unexpected_value_flag": bool(unexpected),
            }
        )
    return mapped, pd.DataFrame(policy_rows)


for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

summary02b_path = STAGE02B_DATA / "02b_preprocessing_forensic_summary.json"
summary02b = read_json(summary02b_path)
summary02 = read_json(STAGE02_DATA / "v2_preprocessing_summary.json")

raw_paths = {k: PROJECT_ROOT / v for k, v in summary02b["raw_input_files"].items()}
stage02_paths = {
    "membership": PROJECT_ROOT / summary02b["stage02_input_files"]["membership"],
    "usermapping": PROJECT_ROOT / summary02b["stage02_input_files"]["usermapping"],
    "moviemaster": PROJECT_ROOT / summary02b["stage02_input_files"]["moviemaster"],
    "summary": PROJECT_ROOT / summary02b["stage02_input_files"]["summary"],
}

raw_files_before = snapshot_paths(raw_paths.values())
data_file_set_before = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())
protected_dirs = []
for parent in [BASE / "reports" / "data", BASE / "reports" / "tables", BASE / "reports" / "figures"]:
    if parent.exists():
        for p in parent.iterdir():
            if p.is_dir() and p.name != STAGE_NAME and p.name[:2].isdigit() and 1 <= int(p.name[:2]) <= 9:
                protected_dirs.append(p)
stage01_09_before = snapshot_dirs(protected_dirs)

membership = read_csv(stage02_paths["membership"])
usermapping = read_csv(stage02_paths["usermapping"])
moviemaster = read_csv(stage02_paths["moviemaster"])
raw_membership = read_csv(raw_paths["Membership"])
raw_views = read_csv(raw_paths["ViewHistory"])

before_rows = len(membership)
df = membership.copy()
if "source_row_number" not in df.columns:
    df["source_row_number"] = np.arange(2, len(df) + 2).astype(str)
    source_row_reference_note = "source_row_number missing; created from Stage 02 preprocessed file order."
else:
    source_row_reference_note = "source_row_number preserved from Stage 02 preprocessed membership."

raw_backup_cols = [
    "is_repurchase",
    "is_promotion",
    "is_churn_prevented",
    "is_user_verified",
    "gender",
    "product_code",
    "payment_device",
    "billing_method",
    "reg_date",
    "end_date",
    "age",
    "price",
    "max_screen",
    "reg_hour",
]
for col in raw_backup_cols:
    if col in df.columns:
        df[f"{col}_raw"] = df[col]
    else:
        df[f"{col}_raw"] = ""

if "duration_days" in df.columns:
    df["duration_days_stage02"] = df["duration_days"]
else:
    df["duration_days_stage02"] = ""

target_raw = norm_text(df["is_repurchase_raw"]).str.upper()
df["is_repurchase_label"] = target_raw.map({"Y": 1, "N": 0}).astype("float")
target_audit = (
    pd.DataFrame({"raw_value": target_raw.replace("", "__MISSING__"), "mapped_value": df["is_repurchase_label"]})
    .groupby(["raw_value", "mapped_value"], dropna=False)
    .size()
    .reset_index(name="count")
)
target_audit["action"] = np.where(target_audit["mapped_value"].isin([0.0, 1.0]), "map_to_target_label", "remove_row")
target_audit["unexpected_value_flag"] = ~target_audit["mapped_value"].isin([0.0, 1.0])
write_csv(TABLE_DIR / "02c_target_encoding_audit.csv", target_audit)

binary_policy_parts = []
binary_audit_parts = []
for col in ["is_promotion", "is_churn_prevented", "is_user_verified"]:
    bin_col = f"{col}_bin"
    flag_col = f"{col}_unknown_flag"
    mapped, policy_df = binary_map_observed(df[f"{col}_raw"])
    df[bin_col] = mapped
    df[flag_col] = df[bin_col].isna().astype(int)
    policy_df.insert(0, "column", col)
    binary_policy_parts.append(policy_df)
    audit = value_counts_df(df, f"{col}_raw", "stage02_retained", value_col="raw_value")
    audit["standardized_column"] = bin_col
    audit["unknown_count"] = int(df[flag_col].sum())
    binary_audit_parts.append(audit)
binary_policy = pd.concat(binary_policy_parts, ignore_index=True)
binary_audit = pd.concat(binary_audit_parts, ignore_index=True)
write_csv(TABLE_DIR / "02c_binary_encoding_policy.csv", binary_policy)
write_csv(TABLE_DIR / "02c_binary_encoding_audit.csv", binary_audit)

df["reg_date_parsed"] = parse_date(df["reg_date_raw"])
df["end_date_parsed"] = parse_date(df["end_date_raw"])
df["duration_days_recomputed"] = (df["end_date_parsed"] - df["reg_date_parsed"]).dt.days
date_parse_audit_rows = []
for col, parsed_col in [("reg_date", "reg_date_parsed"), ("end_date", "end_date_parsed")]:
    raw_col = f"{col}_raw"
    failures = df.loc[df[parsed_col].isna(), raw_col].drop_duplicates().head(10).tolist()
    date_parse_audit_rows.append(
        {
            "column": col,
            "parse_success_count": int(df[parsed_col].notna().sum()),
            "parse_failure_count": int(df[parsed_col].isna().sum()),
            "failed_raw_value_examples": "|".join(map(str, failures)),
        }
    )
date_parse_audit = pd.DataFrame(date_parse_audit_rows)
write_csv(TABLE_DIR / "02c_date_parse_audit.csv", date_parse_audit)

for col in ["age", "price", "max_screen", "reg_hour"]:
    df[f"{col}_num"] = parse_number(df[f"{col}_raw"])

numeric_parse_audit = []
for col in ["age", "price", "max_screen", "reg_hour"]:
    raw_col = f"{col}_raw"
    num_col = f"{col}_num"
    fail_mask = df[num_col].isna() & ~missingish(df[raw_col])
    numeric_parse_audit.append(
        {
            "column": col,
            "parse_success_count": int(df[num_col].notna().sum()),
            "parse_failure_count": int(fail_mask.sum()),
            "missing_count": int(missingish(df[raw_col]).sum()),
            "failed_raw_value_examples": "|".join(df.loc[fail_mask, raw_col].drop_duplicates().head(10).astype(str).tolist()),
        }
    )
numeric_parse_audit = pd.DataFrame(numeric_parse_audit)
write_csv(TABLE_DIR / "02c_numeric_parse_audit.csv", numeric_parse_audit)

df["product_code_clean"] = norm_text(df["product_code_raw"]).where(~missingish(df["product_code_raw"]), "unknown")
df["payment_device_clean"] = norm_text(df["payment_device_raw"]).str.lower().where(~missingish(df["payment_device_raw"]), "unknown")
df["billing_method_clean"] = norm_text(df["billing_method_raw"]).where(~missingish(df["billing_method_raw"]), "unknown")
gender_clean = norm_text(df["gender_raw"]).str.upper()
df["gender_clean"] = gender_clean.where(~(missingish(df["gender_raw"]) | gender_clean.eq("N")), "unknown")
for col in ["gender", "product_code", "payment_device", "billing_method"]:
    df[f"{col}_unknown_flag"] = (df[f"{col}_clean"] == "unknown").astype(int)

categorical_audit_parts = []
for raw_col, clean_col in [
    ("gender_raw", "gender_clean"),
    ("product_code_raw", "product_code_clean"),
    ("payment_device_raw", "payment_device_clean"),
    ("billing_method_raw", "billing_method_clean"),
]:
    tmp = df.groupby([raw_col, clean_col], dropna=False).size().reset_index(name="count")
    tmp.insert(0, "column", raw_col.replace("_raw", ""))
    tmp["action"] = np.where(tmp[clean_col].eq("unknown"), "normalize_to_unknown", "trim_and_preserve")
    categorical_audit_parts.append(tmp.rename(columns={raw_col: "raw_value", clean_col: "clean_value"}))
categorical_audit = pd.concat(categorical_audit_parts, ignore_index=True)
write_csv(TABLE_DIR / "02c_categorical_standardization_audit.csv", categorical_audit)

rare_rows = []
for col in ["product_code_clean", "gender_clean", "payment_device_clean", "billing_method_clean"]:
    vc = df[col].value_counts(dropna=False).reset_index()
    vc.columns = ["level", "count"]
    vc["column"] = col
    vc["rare_threshold"] = 10
    vc["rare_level_flag"] = vc["count"] <= 10
    rare_rows.append(vc[["column", "level", "count", "rare_threshold", "rare_level_flag"]])
rare_code_audit = pd.concat(rare_rows, ignore_index=True)
write_csv(TABLE_DIR / "02c_rare_code_audit.csv", rare_code_audit)

invalid_target = df["is_repurchase_label"].isna()
date_parse_failure = df["reg_date_parsed"].isna() | df["end_date_parsed"].isna()
invalid_duration = df["duration_days_recomputed"].isna() | df["duration_days_recomputed"].eq(0) | ~df["duration_days_recomputed"].isin([31, 32])
invalid_age = df["age_num"].isna() | df["age_num"].lt(10) | df["age_num"].gt(100) | df["age_num"].eq(950)
invalid_max_screen = df["max_screen_num"].isna() | ~df["max_screen_num"].isin([1, 2, 4])
invalid_price = df["price_num"].isna() | df["price_num"].lt(0)
invalid_reg_hour = df["reg_hour_num"].isna() | df["reg_hour_num"].lt(0) | df["reg_hour_num"].gt(23)
df["reg_hour_invalid_flag"] = invalid_reg_hour.astype(int)

reason_masks = [
    ("INVALID_TARGET_VALUE", "R_TARGET_01_MAP_YN_ONLY", invalid_target, "is_repurchase could not be mapped to 1/0."),
    ("DATE_PARSE_FAILURE", "R_DATE_01_PARSE_REG_END", date_parse_failure, "reg_date or end_date could not be parsed."),
    (
        "NONSTANDARD_DURATION_FOR_MONTHLY_SCOPE",
        "R_DURATION_01_KEEP_31_32_ONLY",
        invalid_duration,
        "duration_days_recomputed is missing, zero, or not in 31/32; excluded from standard monthly-subscription official population.",
    ),
    ("INVALID_AGE", "R_AGE_01_PLAUSIBLE_10_100_EXCLUDE_950", invalid_age, "age is missing, unparsable, <10, >100, or 950."),
    ("INVALID_MAX_SCREEN", "R_MAX_SCREEN_01_KEEP_1_2_4", invalid_max_screen, "max_screen is missing, unparsable, or not in 1/2/4."),
    ("INVALID_PRICE", "R_PRICE_01_NONMISSING_NONNEGATIVE", invalid_price, "price is missing, unparsable, or negative."),
]

all_reason_codes = []
primary_reason_codes = []
primary_rule_names = []
primary_details = []
for i in df.index:
    row_reasons = []
    row_rules = []
    row_details = []
    for code, rule, mask, detail in reason_masks:
        if bool(mask.loc[i]):
            row_reasons.append(code)
            row_rules.append(rule)
            row_details.append(detail)
    all_reason_codes.append("|".join(row_reasons))
    primary_reason_codes.append(row_reasons[0] if row_reasons else "")
    primary_rule_names.append(row_rules[0] if row_rules else "")
    primary_details.append(row_details[0] if row_details else "")

df["all_reason_codes"] = all_reason_codes
df["reason_code"] = primary_reason_codes
df["rule_name"] = primary_rule_names
df["reason_detail"] = primary_details
remove_mask = df["reason_code"].ne("")
df["strict_core_removed_flag"] = remove_mask.astype(int)

df["verified_gender_inconsistent_flag"] = (
    df["is_user_verified_bin"].eq(1) & (df["gender_clean"].eq("unknown") | norm_text(df["gender_raw"]).str.upper().eq("N"))
).astype(int)
df["price100_verified_mismatch_flag"] = (df["price_num"].eq(100) & ~df["is_user_verified_bin"].eq(1)).astype(int)

removed_cols = [
    "membership_row_id",
    "source_file",
    "source_row_number",
    "reason_code",
    "reason_detail",
    "rule_name",
    "all_reason_codes",
    "is_repurchase_raw",
    "reg_date_raw",
    "end_date_raw",
    "duration_days_stage02",
    "duration_days_recomputed",
    "age_raw",
    "age_num",
    "max_screen_raw",
    "max_screen_num",
    "price_raw",
    "price_num",
    "reg_hour_raw",
    "reg_hour_num",
    "nonstandard_duration_removed_flag",
    "max_screen_invalid_removed_flag",
]
df["nonstandard_duration_removed_flag"] = (remove_mask & invalid_duration).astype(int)
df["max_screen_invalid_removed_flag"] = (remove_mask & invalid_max_screen).astype(int)
removed_rows = df.loc[remove_mask, [c for c in removed_cols if c in df.columns]].copy()
write_csv(TABLE_DIR / "02c_removed_rows.csv", removed_rows)

removed_by_reason = []
for code, rule, mask, detail in reason_masks:
    removed_by_reason.append(
        {
            "reason_code": code,
            "rule_name": rule,
            "removed_rows": int((remove_mask & mask).sum()),
            "reason_detail": detail,
        }
    )
removed_by_reason = pd.DataFrame(removed_by_reason)
write_csv(TABLE_DIR / "02c_removed_rows_by_reason.csv", removed_by_reason)

clean = df.loc[~remove_mask].copy()
clean["is_repurchase_label"] = clean["is_repurchase_label"].astype(int)
for col in ["is_promotion_bin", "is_churn_prevented_bin", "is_user_verified_bin"]:
    clean[col] = clean[col].astype("Int64")

date_output_cols = ["reg_date_parsed", "end_date_parsed"]
for col in date_output_cols:
    clean[col] = clean[col].dt.strftime("%Y-%m-%d")
    df[col] = df[col].dt.strftime("%Y-%m-%d")

write_csv(DATA_DIR / "membership_v2_preprocessed_strict_core.csv", clean)

business_flags = clean[
    [
        "membership_row_id",
        "source_row_number",
        "verified_gender_inconsistent_flag",
        "price100_verified_mismatch_flag",
        "is_promotion_unknown_flag",
        "is_churn_prevented_unknown_flag",
        "reg_hour_invalid_flag",
    ]
].copy()
write_csv(TABLE_DIR / "02c_unresolved_business_definition_flags.csv", business_flags)

age_audit = pd.DataFrame(
    [
        {"metric": "stage02_retained_rows", "count": before_rows},
        {"metric": "age_parse_failure_or_missing_rows", "count": int(df["age_num"].isna().sum())},
        {"metric": "age_lt_10_rows", "count": int(df["age_num"].lt(10).sum())},
        {"metric": "age_gt_100_rows", "count": int(df["age_num"].gt(100).sum())},
        {"metric": "age_950_rows", "count": int(df["age_num"].eq(950).sum())},
        {"metric": "removed_by_invalid_age_any_reason_overlap", "count": int((remove_mask & invalid_age).sum())},
        {"metric": "remaining_invalid_age_rows", "count": int((~remove_mask & invalid_age).sum())},
    ]
)
write_csv(TABLE_DIR / "02c_age_correction_audit.csv", age_audit)

duration_audit = pd.DataFrame(
    [
        {"metric": "stage02_retained_rows", "count": before_rows, "note": ""},
        {"metric": "duration_zero_rows", "count": int(df["duration_days_recomputed"].eq(0).sum()), "note": ""},
        {"metric": "duration_not_31_32_rows", "count": int((~df["duration_days_recomputed"].isin([31, 32])).sum()), "note": "Includes missing and zero."},
        {
            "metric": "removed_by_nonstandard_duration_any_reason_overlap",
            "count": int((remove_mask & invalid_duration).sum()),
            "note": "Scope change to standard monthly-subscription events; non-31/32 is not asserted impossible.",
        },
        {"metric": "remaining_nonstandard_duration_rows", "count": int((~remove_mask & invalid_duration).sum()), "note": ""},
    ]
)
write_csv(TABLE_DIR / "02c_duration_correction_audit.csv", duration_audit)

max_screen_audit = pd.DataFrame(
    [
        {"metric": "max_screen_missing_or_parse_failure_rows", "count": int(df["max_screen_num"].isna().sum())},
        {"metric": "max_screen_not_1_2_4_rows", "count": int((~df["max_screen_num"].isin([1, 2, 4])).sum())},
        {"metric": "removed_by_invalid_max_screen_any_reason_overlap", "count": int((remove_mask & invalid_max_screen).sum())},
        {"metric": "remaining_invalid_max_screen_rows", "count": int((~remove_mask & invalid_max_screen).sum())},
    ]
)
write_csv(TABLE_DIR / "02c_max_screen_correction_audit.csv", max_screen_audit)

price_audit = pd.DataFrame(
    [
        {"metric": "price_missing_or_parse_failure_rows", "count": int(df["price_num"].isna().sum())},
        {"metric": "price_negative_rows", "count": int(df["price_num"].lt(0).sum())},
        {"metric": "price_rare_positive_rows_not_removed_by_rarity", "count": int((df["price_num"].gt(0) & (df["price_num"].map(df["price_num"].value_counts()) <= 10)).sum())},
        {"metric": "removed_by_invalid_price_any_reason_overlap", "count": int((remove_mask & invalid_price).sum())},
        {"metric": "remaining_invalid_price_rows", "count": int((~remove_mask & invalid_price).sum())},
    ]
)
write_csv(TABLE_DIR / "02c_price_correction_audit.csv", price_audit)

before_after_row_counts = pd.DataFrame(
    [
        {"dataset": "Stage 02 retained Membership", "row_count": before_rows},
        {"dataset": "Stage 02c strict-core corrected Membership", "row_count": len(clean)},
        {"dataset": "Stage 02c removed rows", "row_count": int(remove_mask.sum())},
    ]
)
write_csv(TABLE_DIR / "02c_before_after_row_counts.csv", before_after_row_counts)

target_before = value_counts_df(df, "is_repurchase_raw", "Stage 02 retained", value_col="target_value")
target_after = value_counts_df(clean, "is_repurchase_label", "Stage 02c strict-core", value_col="target_value")
target_dist = pd.concat([target_before, target_after], ignore_index=True)
target_rates = pd.DataFrame(
    [
        {
            "dataset": "Stage 02 retained",
            "repurchase_rate": float((target_raw == "Y").mean()),
            "churn_rate": float((target_raw == "N").mean()),
        },
        {
            "dataset": "Stage 02c strict-core",
            "repurchase_rate": float(clean["is_repurchase_label"].eq(1).mean()),
            "churn_rate": float(clean["is_repurchase_label"].eq(0).mean()),
        },
    ]
)
target_distribution = pd.concat([target_dist, target_rates], ignore_index=True, sort=False)
write_csv(TABLE_DIR / "02c_before_after_target_distribution.csv", target_distribution)

value_dist_parts = []
for col_before, col_after in [
    ("is_promotion_raw", "is_promotion_bin"),
    ("max_screen_raw", "max_screen_num"),
    ("duration_days_stage02", "duration_days_recomputed"),
    ("price_raw", "price_num"),
    ("gender_raw", "gender_clean"),
    ("is_user_verified_raw", "is_user_verified_bin"),
]:
    value_dist_parts.append(value_counts_df(df, col_before, "Stage 02 retained", value_col="value"))
    value_dist_parts.append(value_counts_df(clean, col_after, "Stage 02c strict-core", value_col="value"))
summary_rows = pd.DataFrame(
    [
        numeric_summary(df, "age_num", "Stage 02 retained"),
        numeric_summary(clean, "age_num", "Stage 02c strict-core"),
        numeric_summary(df, "price_num", "Stage 02 retained"),
        numeric_summary(clean, "price_num", "Stage 02c strict-core"),
    ]
)
summary_rows["value"] = "numeric_summary"
value_distributions = pd.concat(value_dist_parts + [summary_rows], ignore_index=True, sort=False)
for flag in [
    "is_promotion_unknown_flag",
    "is_churn_prevented_unknown_flag",
    "is_user_verified_unknown_flag",
    "gender_unknown_flag",
    "product_code_unknown_flag",
    "payment_device_unknown_flag",
    "billing_method_unknown_flag",
]:
    value_distributions = pd.concat(
        [
            value_distributions,
            pd.DataFrame(
                [
                    {"dataset": "Stage 02c strict-core", "column": flag, "value": "flag_sum", "count": int(clean[flag].sum()), "share": float(clean[flag].mean())}
                ]
            ),
        ],
        ignore_index=True,
        sort=False,
    )
write_csv(TABLE_DIR / "02c_before_after_value_distributions.csv", value_distributions)

clean_user_counts = clean.groupby("USER_KEY").size().reset_index(name="strict_core_membership_event_count_for_USER_KEY")
usermapping_strict = usermapping.copy()
if "USER_KEY" in usermapping_strict.columns:
    usermapping_strict = usermapping_strict.merge(clean_user_counts, on="USER_KEY", how="left")
    usermapping_strict["strict_core_membership_event_count_for_USER_KEY"] = usermapping_strict[
        "strict_core_membership_event_count_for_USER_KEY"
    ].fillna(0).astype(int)
write_csv(DATA_DIR / "usermapping_v2_policy_checked_strict_core.csv", usermapping_strict)
usermapping_audit = pd.DataFrame(
    [
        {"metric": "stage02_usermapping_rows", "count": len(usermapping), "action": "carried_forward_no_deletion"},
        {"metric": "stage02c_usermapping_rows", "count": len(usermapping_strict), "action": "carried_forward_no_deletion"},
        {
            "metric": "one_to_many_USER_KEY_flag_rows",
            "count": int((usermapping_strict.get("USER_KEY_to_USER_NUM_pattern", pd.Series(dtype=str)) == "one_to_many").sum()),
            "action": "flag_preserved",
        },
        {
            "metric": "many_to_one_USER_NUM_flag_rows",
            "count": int((usermapping_strict.get("USER_NUM_to_USER_KEY_pattern", pd.Series(dtype=str)) == "many_to_one").sum()),
            "action": "flag_preserved",
        },
    ]
)
write_csv(TABLE_DIR / "02c_usermapping_correction_audit.csv", usermapping_audit)

moviemaster_strict = moviemaster.copy()
write_csv(DATA_DIR / "moviemaster_v2_policy_checked_strict_core.csv", moviemaster_strict)
stage04_dedupe_path = STAGE04_TABLE / "04_v2_moviemaster_deduplication_summary.csv"
stage04_dedupe_exists = stage04_dedupe_path.exists()
moviemaster_audit = pd.DataFrame(
    [
        {"metric": "stage02_moviemaster_rows", "count": len(moviemaster), "action": "carried_forward_no_deletion", "note": ""},
        {"metric": "stage02c_moviemaster_rows", "count": len(moviemaster_strict), "action": "carried_forward_no_deletion", "note": ""},
        {
            "metric": "stage02c_deduplicated_moviemaster",
            "count": 0,
            "action": "not_applied",
            "note": "Stage 02c does not deduplicate MovieMaster.",
        },
        {
            "metric": "stage04_deduplication_reference_exists",
            "count": int(stage04_dedupe_exists),
            "action": "reference_only",
            "note": rel(stage04_dedupe_path) if stage04_dedupe_exists else "Stage 04 dedupe summary not found.",
        },
    ]
)
write_csv(TABLE_DIR / "02c_moviemaster_correction_audit.csv", moviemaster_audit)

view_audit_parts = []
for path, source in [
    (STAGE03_TABLE / "03_v2_temporal_filter_summary.csv", "stage03_usage"),
    (STAGE03_TABLE / "03_v2_short_watch_summary.csv", "stage03_short_watch"),
    (STAGE04_TABLE / "04_v2_content_temporal_filter_summary.csv", "stage04_content"),
]:
    if path.exists():
        part = read_csv(path)
        part["source"] = source
        part["stage02c_action"] = "audit_only_raw_not_modified"
        view_audit_parts.append(part)
watch_cols = [c for c in raw_views.columns if c.lower().replace("_", "").replace("(", "").replace(")", "") in ["watchtimemin", "watchtime"]]
watch_col = watch_cols[0] if watch_cols else ""
if watch_col:
    watch_num = parse_number(raw_views[watch_col])
    raw_short = pd.DataFrame(
        [
            {"metric": "raw_watch_time_eq_1", "count": int(watch_num.eq(1).sum()), "source": "raw_viewhistory_inspection", "stage02c_action": "not_deleted"},
            {"metric": "raw_watch_time_le_5", "count": int(watch_num.le(5).sum()), "source": "raw_viewhistory_inspection", "stage02c_action": "not_deleted"},
        ]
    )
    view_audit_parts.append(raw_short)
view_audit_parts.append(
    pd.DataFrame(
        [
            {"metric": "raw_ViewHistory_modified", "count": 0, "source": "stage02c_conclusion", "stage02c_action": "not_modified"},
            {
                "metric": "watch_date_after_end_date_feature_policy",
                "count": "",
                "source": "stage02c_conclusion",
                "stage02c_action": "must_not_use_inside_feature_windows",
            },
            {
                "metric": "end_date_derived_features",
                "count": "",
                "source": "stage02c_conclusion",
                "stage02c_action": "must_not_create_direct_model_features",
            },
        ]
    )
)
viewhistory_audit = pd.concat(view_audit_parts, ignore_index=True, sort=False)
write_csv(TABLE_DIR / "02c_viewhistory_temporal_policy_audit.csv", viewhistory_audit)

standardized_contract = pd.DataFrame(
    [
        {"raw_column": "is_repurchase", "standardized_column": "is_repurchase_label", "role": "target", "allowed_downstream_use": "model target only", "forbidden_downstream_use": "feature use; raw backup use"},
        {"raw_column": "is_promotion", "standardized_column": "is_promotion_bin", "role": "binary standardized feature candidate", "allowed_downstream_use": "feature candidate after Stage 05 policy approval", "forbidden_downstream_use": "use is_promotion or is_promotion_raw as feature"},
        {"raw_column": "is_churn_prevented", "standardized_column": "is_churn_prevented_bin", "role": "binary standardized feature candidate", "allowed_downstream_use": "feature candidate after leakage/policy review", "forbidden_downstream_use": "use raw backup as feature"},
        {"raw_column": "is_user_verified", "standardized_column": "is_user_verified_bin", "role": "binary standardized feature candidate", "allowed_downstream_use": "feature candidate after Stage 05 policy approval", "forbidden_downstream_use": "use raw backup as feature"},
        {"raw_column": "age", "standardized_column": "age_num", "role": "numeric standardized feature candidate", "allowed_downstream_use": "feature candidate", "forbidden_downstream_use": "use age_raw as feature"},
        {"raw_column": "price", "standardized_column": "price_num", "role": "numeric standardized feature candidate", "allowed_downstream_use": "feature candidate", "forbidden_downstream_use": "use price_raw as feature"},
        {"raw_column": "max_screen", "standardized_column": "max_screen_num", "role": "numeric standardized feature candidate", "allowed_downstream_use": "feature candidate", "forbidden_downstream_use": "use max_screen_raw as feature"},
        {"raw_column": "reg_hour", "standardized_column": "reg_hour_num", "role": "audit_flag_only", "allowed_downstream_use": "audit only unless explicitly approved", "forbidden_downstream_use": "official model feature without explicit approval"},
        {"raw_column": "reg_date", "standardized_column": "reg_date_parsed", "role": "date audit or feature construction", "allowed_downstream_use": "audit or upstream feature construction only", "forbidden_downstream_use": "direct model feature"},
        {"raw_column": "end_date", "standardized_column": "end_date_parsed", "role": "date audit or feature construction", "allowed_downstream_use": "audit or upstream feature construction only", "forbidden_downstream_use": "direct model feature; end_date-derived leakage features"},
        {"raw_column": "reg_date/end_date", "standardized_column": "duration_days_recomputed", "role": "scope definition audit", "allowed_downstream_use": "official population scope definition", "forbidden_downstream_use": "direct official model feature"},
        {"raw_column": "gender", "standardized_column": "gender_clean", "role": "categorical standardized feature candidate", "allowed_downstream_use": "feature candidate after Stage 05 policy approval", "forbidden_downstream_use": "use gender_raw as feature"},
        {"raw_column": "product_code", "standardized_column": "product_code_clean", "role": "categorical audit or optional feature", "allowed_downstream_use": "audit; optional only if approved", "forbidden_downstream_use": "over-engineered official feature by default"},
        {"raw_column": "payment_device", "standardized_column": "payment_device_clean", "role": "categorical standardized feature candidate", "allowed_downstream_use": "feature candidate after Stage 05 policy approval", "forbidden_downstream_use": "use payment_device_raw as feature"},
        {"raw_column": "billing_method", "standardized_column": "billing_method_clean", "role": "categorical standardized feature candidate", "allowed_downstream_use": "feature candidate after Stage 05 policy approval", "forbidden_downstream_use": "use billing_method_raw as feature"},
    ]
)
write_csv(TABLE_DIR / "02c_standardized_column_contract.csv", standardized_contract)

row_count_changed = len(clean) != before_rows
standardized_core_columns_created = True
downstream_need_rerun = row_count_changed or standardized_core_columns_created
stages = ["Stage 03", "Stage 04", "Stage 05", "Stage 06/06h", "Stage 07/07r", "Stage 08/08b", "Stage 09"]
downstream_rerun = pd.DataFrame(
    [
        {
            "stage": stage,
            "need_rerun_or_revalidation": "Y" if downstream_need_rerun else "N",
            "reason": "Stage 02c changed retained Membership row count and introduced standardized core columns; old downstream outputs are not final."
            if downstream_need_rerun
            else "No strict-core row count or core column change detected.",
        }
        for stage in stages
    ]
)
write_csv(TABLE_DIR / "02c_downstream_rerun_requirement.csv", downstream_rerun)

downstream_deprecation = pd.DataFrame(
    [
        {
            "stage": stage,
            "status": "deprecated_requires_rerun" if downstream_need_rerun else "still_valid",
            "historical_reference_allowed": "Y" if downstream_need_rerun else "N",
            "final_presentation_allowed": "N" if downstream_need_rerun else "Y",
            "reason": "Use only as historical reference until rerun from Stage 02c strict-core corrected Membership."
            if downstream_need_rerun
            else "No Stage 02c downstream-breaking change detected.",
        }
        for stage in stages
    ]
)
write_csv(TABLE_DIR / "02c_downstream_deprecation_status.csv", downstream_deprecation)

plt.figure(figsize=(7, 4))
plt.bar(before_after_row_counts["dataset"], before_after_row_counts["row_count"], color=["#378ADD", "#1D9E75", "#D4537E"])
plt.xticks(rotation=20, ha="right")
plt.ylabel("Rows")
plt.title("Stage 02 vs Stage 02c Row Count")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "02c_row_count_before_after.png", dpi=160)
plt.close()

target_plot = pd.DataFrame(
    [
        {"dataset": "Stage 02", "target": "Y/1", "count": int((target_raw == "Y").sum())},
        {"dataset": "Stage 02", "target": "N/0", "count": int((target_raw == "N").sum())},
        {"dataset": "Stage 02c", "target": "Y/1", "count": int(clean["is_repurchase_label"].eq(1).sum())},
        {"dataset": "Stage 02c", "target": "N/0", "count": int(clean["is_repurchase_label"].eq(0).sum())},
    ]
)
fig, ax = plt.subplots(figsize=(7, 4))
for idx, target in enumerate(["Y/1", "N/0"]):
    subset = target_plot[target_plot["target"] == target]
    ax.bar(np.arange(len(subset)) + idx * 0.35, subset["count"], width=0.35, label=target)
ax.set_xticks(np.arange(2) + 0.175)
ax.set_xticklabels(["Stage 02", "Stage 02c"])
ax.set_ylabel("Rows")
ax.set_title("Target Distribution Before/After")
ax.legend()
plt.tight_layout()
plt.savefig(FIGURE_DIR / "02c_target_distribution_before_after.png", dpi=160)
plt.close()

plt.figure(figsize=(9, 4))
reason_plot = removed_by_reason.sort_values("removed_rows", ascending=False)
plt.bar(reason_plot["reason_code"], reason_plot["removed_rows"], color="#D4537E")
plt.xticks(rotation=30, ha="right")
plt.ylabel("Rows")
plt.title("Removed Rows by Reason")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "02c_removed_reason_counts.png", dpi=160)
plt.close()

plt.figure(figsize=(7, 4))
bins = sorted(set(df["duration_days_recomputed"].dropna().astype(int).tolist() + clean["duration_days_recomputed"].dropna().astype(int).tolist()))
if bins:
    plt.hist(df["duration_days_recomputed"].dropna(), bins=range(min(bins), max(bins) + 2), alpha=0.55, label="Stage 02", color="#378ADD")
    plt.hist(clean["duration_days_recomputed"].dropna(), bins=range(min(bins), max(bins) + 2), alpha=0.55, label="Stage 02c", color="#1D9E75")
plt.xlabel("duration_days_recomputed")
plt.ylabel("Rows")
plt.title("Duration Distribution Before/After")
plt.legend()
plt.tight_layout()
plt.savefig(FIGURE_DIR / "02c_duration_distribution_before_after.png", dpi=160)
plt.close()

report = f"""> Stage 02c v2 strict preprocessing correction report

## 1. Stage 02는 실제로 무엇만 제거했는가?
Stage 02는 raw Membership {summary02b['raw_membership_rows']:,}행 중 {summary02b['excluded_membership_rows']:,}행만 제거했습니다. 제거 사유는 strict target conflict {summary02b['excluded_counts_by_reason'].get('STRICT_TARGET_CONFLICT', 0):,}행과 exact duplicate extra row {summary02b['excluded_counts_by_reason'].get('EXACT_DUPLICATE_EXTRA_ROW', 0):,}행입니다.

## 2. Stage 02에서 하지 않았던 최소 전처리는 무엇인가?
Stage 02는 실제 retained-row 값 교체가 {summary02b['total_raw_vs_preprocessed_replacement_count_after_normalization']:,}건이었고, target encoding, binary encoding, 날짜 파싱 확정, numeric coercion, duration strict filtering, age/max_screen/price invalid row removal을 공식 산출물에 적용하지 않았습니다.

## 3. Stage 02c에서 target encoding은 어떻게 했는가?
`is_repurchase_raw`를 보존하고, `Y`는 1, `N`은 0으로 매핑해 `is_repurchase_label`을 생성했습니다. 예상 밖 target 값은 `INVALID_TARGET_VALUE`로 삭제하도록 정책화했습니다.

## 4. Stage 02c에서 binary encoding은 어떻게 했는가?
`is_promotion`, `is_churn_prevented`, `is_user_verified`는 raw 값을 보존한 뒤 관측값 체계에 따라 `*_bin`으로 표준화했습니다. missing 또는 ambiguous 값은 삭제하지 않고 `*_unknown_flag`로 남겼습니다.

## 5. Stage 02c에서 date parsing은 어떻게 했는가?
`reg_date_raw`, `end_date_raw`를 보존하고 `reg_date_parsed`, `end_date_parsed`를 만들었습니다. `duration_days_recomputed`는 기존 duration을 믿지 않고 parsed date 차이로 다시 계산했습니다.

## 6. Stage 02c에서 numeric coercion은 어떻게 했는가?
`age`, `price`, `max_screen`, `reg_hour`는 각각 `age_num`, `price_num`, `max_screen_num`, `reg_hour_num`으로 강제 숫자화했습니다. `reg_hour`는 audit/flag only라서 이 문제만으로 row를 삭제하지 않았습니다.

## 7. Stage 02c에서 어떤 row를 실제 삭제했는가?
Stage 02c는 Stage 02 retained {before_rows:,}행 중 {int(remove_mask.sum()):,}행을 strict-core 기준으로 삭제했고, 최종 corrected row count는 {len(clean):,}행입니다. 삭제 사유는 invalid target, date parse failure, non-31/32 또는 0 duration, invalid age, invalid/missing max_screen, invalid/missing/negative price입니다.

## 8. Stage 02c에서 어떤 값을 unknown/flag 처리했는가?
`gender == N`과 blank categorical 값은 `unknown`으로 표준화했습니다. promotion/churn-prevented/user-verified ambiguous 값, verified-gender inconsistency, price=100 verified mismatch, reg_hour invalid는 flag로 남겼습니다.

## 9. 왜 all-strict 4,793행 삭제는 적용하지 않았는가?
all-strict 4,793행 삭제에는 gender `N`, price=100 verified mismatch, rare category처럼 business definition 확인이 필요한 조건이 포함됩니다. Stage 02c는 발표 전 필수 strict-core correction만 적용하고, business-ambiguous 조건은 삭제가 아니라 flag로 분리했습니다.

## 10. 최종 corrected row count는 얼마인가?
최종 strict-core corrected Membership row count는 {len(clean):,}행입니다.

## 11. target distribution은 어떻게 바뀌었는가?
Stage 02 retained의 repurchase rate는 {float((target_raw == 'Y').mean()):.4f}, churn rate는 {float((target_raw == 'N').mean()):.4f}입니다. Stage 02c strict-core의 repurchase rate는 {float(clean['is_repurchase_label'].eq(1).mean()):.4f}, churn rate는 {float(clean['is_repurchase_label'].eq(0).mean()):.4f}입니다.

## 12. ViewHistory raw는 수정했는가?
수정하지 않았습니다. short watch logs도 raw에서 삭제하지 않았고, Stage 03/04의 temporal policy audit을 참조해 feature window 정책만 문서화했습니다.

## 13. UserMapping과 MovieMaster는 정제했는가, flag만 유지했는가?
Stage 02c는 UserMapping과 MovieMaster row를 삭제하지 않았습니다. UserMapping은 strict-core Membership 기준 event count를 추가했고, MovieMaster는 Stage 02 policy checked 상태를 carry-forward했습니다. MovieMaster dedupe는 Stage 04 content feature generation 영역입니다.

## 14. Stage 03 이후 downstream을 다시 돌려야 하는가?
다시 돌려야 합니다. Stage 02c가 Membership row count와 core standardized columns를 바꾸었기 때문에 Stage 03부터 Stage 09까지 기존 산출물은 final이 아니라 deprecated/provisional 상태입니다.

## 15. 최종 발표 전 어떤 수치를 다시 산정해야 하는가?
Stage 03 usage features, Stage 04 content features, Stage 05 modeling dataset, Stage 06/06h model metrics, Stage 07/07r SHAP, Stage 08/08b segmentation, Stage 09 simulation 수치를 모두 Stage 02c strict-core population 기준으로 다시 산정하거나 최소 재검증해야 합니다.

## 분석 모집단 변경 주의
duration 31/32 filtering은 비표준 구독 케이스를 official modeling population에서 제외하는 scope change입니다. non-31/32 row가 반드시 불가능하거나 잘못된 데이터라는 뜻은 아닙니다.

## downstream column contract
Raw backup columns는 모델 feature로 사용하면 안 됩니다. Downstream target은 `is_repurchase_label`, binary는 `*_bin`, numeric은 `*_num`을 사용해야 하며, `*_parsed`와 `duration_days_recomputed`는 audit 또는 feature construction/scope definition 전용입니다.
"""
(DATA_DIR / "02c_strict_preprocessing_report.md").write_text(report, encoding="utf-8")

data_outputs = [
    DATA_DIR / "membership_v2_preprocessed_strict_core.csv",
    DATA_DIR / "usermapping_v2_policy_checked_strict_core.csv",
    DATA_DIR / "moviemaster_v2_policy_checked_strict_core.csv",
    DATA_DIR / "02c_strict_preprocessing_summary.json",
    DATA_DIR / "02c_strict_preprocessing_report.md",
]
table_outputs = [
    TABLE_DIR / "02c_target_encoding_audit.csv",
    TABLE_DIR / "02c_binary_encoding_policy.csv",
    TABLE_DIR / "02c_binary_encoding_audit.csv",
    TABLE_DIR / "02c_date_parse_audit.csv",
    TABLE_DIR / "02c_numeric_parse_audit.csv",
    TABLE_DIR / "02c_categorical_standardization_audit.csv",
    TABLE_DIR / "02c_removed_rows.csv",
    TABLE_DIR / "02c_removed_rows_by_reason.csv",
    TABLE_DIR / "02c_before_after_row_counts.csv",
    TABLE_DIR / "02c_before_after_target_distribution.csv",
    TABLE_DIR / "02c_before_after_value_distributions.csv",
    TABLE_DIR / "02c_age_correction_audit.csv",
    TABLE_DIR / "02c_duration_correction_audit.csv",
    TABLE_DIR / "02c_max_screen_correction_audit.csv",
    TABLE_DIR / "02c_price_correction_audit.csv",
    TABLE_DIR / "02c_unresolved_business_definition_flags.csv",
    TABLE_DIR / "02c_rare_code_audit.csv",
    TABLE_DIR / "02c_usermapping_correction_audit.csv",
    TABLE_DIR / "02c_moviemaster_correction_audit.csv",
    TABLE_DIR / "02c_viewhistory_temporal_policy_audit.csv",
    TABLE_DIR / "02c_downstream_rerun_requirement.csv",
    TABLE_DIR / "02c_downstream_deprecation_status.csv",
    TABLE_DIR / "02c_standardized_column_contract.csv",
    TABLE_DIR / "02c_final_checks.csv",
]
figure_outputs = [
    FIGURE_DIR / "02c_row_count_before_after.png",
    FIGURE_DIR / "02c_target_distribution_before_after.png",
    FIGURE_DIR / "02c_removed_reason_counts.png",
    FIGURE_DIR / "02c_duration_distribution_before_after.png",
]

raw_files_after = snapshot_paths(raw_paths.values())
data_file_set_after = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())
stage01_09_after = snapshot_dirs(protected_dirs)

checks = [
    ("raw files unchanged", raw_files_before == raw_files_after, "Compared raw input file snapshots from Stage 02b summary."),
    ("no _data output created", data_file_set_before == data_file_set_after, "Compared _data file set before/after Stage 02c."),
    ("Stage 01 through Stage 09 outputs not overwritten", stage01_09_before == stage01_09_after, "Compared protected Stage 01-09 snapshots excluding 02c."),
    ("corrected strict-core membership created", (DATA_DIR / "membership_v2_preprocessed_strict_core.csv").exists(), rel(DATA_DIR / "membership_v2_preprocessed_strict_core.csv")),
    ("every removed row has reason_code", removed_rows["reason_code"].ne("").all() if len(removed_rows) else True, "02c_removed_rows reason_code completeness."),
    ("target encoding policy created", (TABLE_DIR / "02c_target_encoding_audit.csv").exists(), rel(TABLE_DIR / "02c_target_encoding_audit.csv")),
    ("is_repurchase_label exists and only contains 0/1", "is_repurchase_label" in clean.columns and set(clean["is_repurchase_label"].dropna().unique()).issubset({0, 1}), "Strict-core target label verified."),
    ("binary encoding policy created", (TABLE_DIR / "02c_binary_encoding_policy.csv").exists(), rel(TABLE_DIR / "02c_binary_encoding_policy.csv")),
    ("binary unknown flags created", all(c in clean.columns for c in ["is_promotion_unknown_flag", "is_churn_prevented_unknown_flag", "is_user_verified_unknown_flag"]), "Binary unknown flags exist."),
    ("date parse audit created", (TABLE_DIR / "02c_date_parse_audit.csv").exists(), rel(TABLE_DIR / "02c_date_parse_audit.csv")),
    ("duration_days_recomputed created", "duration_days_recomputed" in clean.columns, "duration_days_recomputed exists."),
    ("numeric parse audit created", (TABLE_DIR / "02c_numeric_parse_audit.csv").exists(), rel(TABLE_DIR / "02c_numeric_parse_audit.csv")),
    ("invalid age rows removed", not ((clean["age_num"].isna()) | clean["age_num"].lt(10) | clean["age_num"].gt(100) | clean["age_num"].eq(950)).any(), "No invalid age remains."),
    ("duration_days not in 31/32 removed", clean["duration_days_recomputed"].isin([31, 32]).all(), "All remaining durations are 31 or 32."),
    ("duration_days == 0 removed", not clean["duration_days_recomputed"].eq(0).any(), "No zero duration remains."),
    ("invalid/missing max_screen rows removed", clean["max_screen_num"].isin([1, 2, 4]).all(), "All remaining max_screen values are 1/2/4."),
    ("categorical unknown flags created", all(c in clean.columns for c in ["gender_unknown_flag", "product_code_unknown_flag", "payment_device_unknown_flag", "billing_method_unknown_flag"]), "Categorical unknown flags exist."),
    ("price100 verified mismatch flag created", "price100_verified_mismatch_flag" in clean.columns, "price100_verified_mismatch_flag exists."),
    ("target distribution before/after created", (TABLE_DIR / "02c_before_after_target_distribution.csv").exists(), rel(TABLE_DIR / "02c_before_after_target_distribution.csv")),
    ("downstream rerun requirement created", (TABLE_DIR / "02c_downstream_rerun_requirement.csv").exists(), rel(TABLE_DIR / "02c_downstream_rerun_requirement.csv")),
    ("downstream deprecation status created", (TABLE_DIR / "02c_downstream_deprecation_status.csv").exists(), rel(TABLE_DIR / "02c_downstream_deprecation_status.csv")),
    ("standardized column contract created", (TABLE_DIR / "02c_standardized_column_contract.csv").exists(), rel(TABLE_DIR / "02c_standardized_column_contract.csv")),
    ("raw backup columns forbidden as model features", not standardized_contract["standardized_column"].astype(str).str.endswith("_raw").any(), "Contract forbids raw backup feature use."),
    ("reg_hour issue only did not remove rows", not ((invalid_reg_hour) & df["all_reason_codes"].eq("")).loc[remove_mask].any(), "reg_hour is not a removal reason."),
    ("no model training", True, "No model fit or training code executed."),
    ("no SHAP", True, "No shap import or computation."),
    ("no Optuna", True, "No optuna import or tuning."),
    ("no segmentation", True, "No segmentation code executed."),
    ("no simulation", True, "No simulation code executed."),
]
for path in [p for p in data_outputs if p.name != "02c_strict_preprocessing_summary.json"] + table_outputs[:-1] + figure_outputs:
    checks.append((f"required output exists: {path.name}", path.exists(), rel(path)))

final_checks = pd.DataFrame([{"check": name, "status": "PASS" if ok else "FAIL", "evidence": evidence} for name, ok, evidence in checks])
write_csv(TABLE_DIR / "02c_final_checks.csv", final_checks)

summary = {
    "stage": STAGE_NAME,
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "python": platform.python_version(),
    "raw_input_files": {k: rel(v) for k, v in raw_paths.items()},
    "stage02_input_files": {k: rel(v) for k, v in stage02_paths.items()},
    "stage02b_summary": rel(summary02b_path),
    "source_row_reference_note": source_row_reference_note,
    "stage02_retained_membership_rows": int(before_rows),
    "stage02c_corrected_membership_rows": int(len(clean)),
    "stage02c_removed_rows": int(remove_mask.sum()),
    "removed_counts_by_reason_any_overlap": dict(zip(removed_by_reason["reason_code"], removed_by_reason["removed_rows"].astype(int))),
    "repurchase_rate_before": float((target_raw == "Y").mean()),
    "repurchase_rate_after": float(clean["is_repurchase_label"].eq(1).mean()),
    "duration_scope_policy": "Keep only standard monthly-subscription events with recomputed duration 31/32 days for official modeling population; non-31/32 rows are not asserted impossible.",
    "reg_hour_policy": "audit_flag_only_not_removal_not_official_feature_without_explicit_approval",
    "downstream_status": "deprecated_requires_rerun" if downstream_need_rerun else "still_valid",
    "viewhistory_raw_modified": False,
    "model_training_executed": False,
    "shap_executed": False,
    "optuna_executed": False,
    "segmentation_executed": False,
    "simulation_executed": False,
    "final_check_status": "PASS" if final_checks["status"].eq("PASS").all() else "FAIL",
    "data_outputs": [rel(p) for p in data_outputs],
    "table_outputs": [rel(p) for p in table_outputs],
    "figure_outputs": [rel(p) for p in figure_outputs],
}
write_json(DATA_DIR / "02c_strict_preprocessing_summary.json", summary)

print(json.dumps(summary, ensure_ascii=False, indent=2))
if summary["final_check_status"] != "PASS":
    raise SystemExit("02c final checks did not all pass.")
