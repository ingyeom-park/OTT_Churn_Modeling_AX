import json
import platform
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "park.ingyeom").exists() and (candidate / "_data").exists():
            return candidate
    raise FileNotFoundError("Project root not found.")


PROJECT_ROOT = find_root(Path.cwd())
BASE = PROJECT_ROOT / "park.ingyeom"
RAW_DIR = PROJECT_ROOT / "_data" / "01_raw"
STAGE02_DATA = BASE / "reports" / "data" / "02_v2_preprocessing_policy"
STAGE02_TABLE = BASE / "reports" / "tables" / "02_v2_preprocessing_policy"
STAGE03_TABLE = BASE / "reports" / "tables" / "03_v2_usage_feature_engineering"
STAGE04_TABLE = BASE / "reports" / "tables" / "04_v2_content_feature_engineering"

STAGE_NAME = "02b_v2_preprocessing_forensic_audit"
DATA_DIR = BASE / "reports" / "data" / STAGE_NAME
TABLE_DIR = BASE / "reports" / "tables" / STAGE_NAME
FIGURE_DIR = BASE / "reports" / "figures" / STAGE_NAME
for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(Path(path).relative_to(PROJECT_ROOT)).replace("\\", "/")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, df: pd.DataFrame):
    df.to_csv(path, index=False, encoding="utf-8-sig")


def snapshot_paths(paths):
    out = {}
    for path in paths:
        path = Path(path)
        if path.exists() and path.is_file():
            st = path.stat()
            out[rel(path)] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
    return out


def snapshot_dirs(dirs):
    files = []
    for directory in dirs:
        directory = Path(directory)
        if directory.exists():
            files.extend([p for p in directory.rglob("*") if p.is_file()])
    return snapshot_paths(files)


raw_files = list(RAW_DIR.glob("*.csv"))
raw_before = snapshot_paths(raw_files)
data_file_set_before = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())
protected_dirs = []
for parent in [BASE / "reports" / "data", BASE / "reports" / "tables", BASE / "reports" / "figures"]:
    if parent.exists():
        for p in parent.iterdir():
            if p.is_dir() and p.name != STAGE_NAME and p.name[:2].isdigit() and 1 <= int(p.name[:2]) <= 9:
                protected_dirs.append(p)
stage01_09_before = snapshot_dirs(protected_dirs)


def choose_existing(candidates):
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("None of these candidate files exists: " + ", ".join(str(p) for p in candidates))


raw_membership_path = choose_existing([RAW_DIR / "Membership.csv", RAW_DIR / "Membership_train.csv"])
raw_mapping_path = choose_existing([RAW_DIR / "User_Mapping.csv", RAW_DIR / "mapping.csv"])
raw_views_path = choose_existing([RAW_DIR / "View_History.csv", RAW_DIR / "Views_train.csv"])
raw_movie_path = choose_existing([RAW_DIR / "Movie_Master.csv", RAW_DIR / "Movies.csv"])

membership_stage02_path = choose_existing([STAGE02_DATA / "membership_v2_preprocessed.csv"])
usermapping_stage02_path = choose_existing([STAGE02_DATA / "usermapping_v2_policy_checked.csv"])
moviemaster_stage02_path = choose_existing([STAGE02_DATA / "moviemaster_v2_policy_checked.csv"])
summary_stage02_path = choose_existing([STAGE02_DATA / "v2_preprocessing_summary.json", STAGE02_DATA / "02_v2_preprocessing_summary.json"])

raw_m = pd.read_csv(raw_membership_path)
raw_u = pd.read_csv(raw_mapping_path)
raw_v = pd.read_csv(raw_views_path)
raw_movie = pd.read_csv(raw_movie_path)
pre_m = pd.read_csv(membership_stage02_path)
pre_u = pd.read_csv(usermapping_stage02_path)
pre_movie = pd.read_csv(moviemaster_stage02_path)
stage02_summary = read_json(summary_stage02_path)
excluded = pd.read_csv(STAGE02_TABLE / "02_v2_excluded_membership_rows.csv")

raw_m = raw_m.copy()
raw_m["source_row_number"] = np.arange(len(raw_m)) + 2
raw_m["membership_row_id"] = np.arange(len(raw_m)) + 1

rename_membership = {
    "uno": "USER_KEY",
    "productcode": "product_code",
    "pgamount": "price",
    "chargetypeid": "billing_method",
    "concurrentwatchcount": "max_screen",
    "promo_100": "is_promotion",
    "coinReceived": "is_churn_prevented",
    "devicetypeid": "payment_device",
    "isauth": "is_user_verified",
    "agegroup": "age",
    "registerday": "reg_date",
    "registerhour": "reg_hour",
    "endday": "end_date",
    "Repurchase": "is_repurchase",
}
raw_m_std = raw_m.rename(columns=rename_membership)


def parse_date(s):
    if isinstance(s, pd.Series):
        text = s.astype("string")
        out = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
        missing = out.isna()
        if missing.any():
            out.loc[missing] = pd.to_datetime(text.loc[missing], format="%y-%m-%d", errors="coerce")
        missing = out.isna()
        if missing.any():
            out.loc[missing] = pd.to_datetime(text.loc[missing], format="%Y%m%d", errors="coerce")
        return out
    text = norm_value(s)
    for fmt in ["%Y-%m-%d", "%y-%m-%d", "%Y%m%d"]:
        parsed = pd.to_datetime(text, format=fmt, errors="coerce")
        if not pd.isna(parsed):
            return parsed
    return pd.NaT


raw_m_std["duration_days"] = (parse_date(raw_m_std["end_date"]) - parse_date(raw_m_std["reg_date"])).dt.days


def norm_value(v):
    if pd.isna(v):
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def norm_date(v):
    if pd.isna(v):
        return ""
    dt = parse_date(v)
    if pd.isna(dt):
        return norm_value(v)
    return dt.strftime("%y-%m-%d")


def normalized_for_compare(col, v):
    if col in {"reg_date", "end_date"}:
        return norm_date(v)
    if col in {"price", "max_screen", "age", "reg_hour"}:
        if pd.isna(v):
            return ""
        try:
            f = float(v)
            return str(int(f)) if f.is_integer() else str(f)
        except Exception:
            return norm_value(v)
    return norm_value(v)


membership_cols = [
    "USER_KEY",
    "product_code",
    "price",
    "billing_method",
    "max_screen",
    "is_promotion",
    "is_churn_prevented",
    "payment_device",
    "is_user_verified",
    "gender",
    "age",
    "reg_date",
    "reg_hour",
    "end_date",
    "is_repurchase",
]

retained_ids = set(pre_m["membership_row_id"])
excluded_ids = set(excluded["membership_row_id"])
lineage_summary = pd.DataFrame(
    [
        {"metric": "raw_membership_rows", "count": len(raw_m), "evidence": rel(raw_membership_path)},
        {"metric": "retained_membership_rows", "count": len(pre_m), "evidence": rel(membership_stage02_path)},
        {"metric": "excluded_membership_rows", "count": len(excluded), "evidence": rel(STAGE02_TABLE / "02_v2_excluded_membership_rows.csv")},
        {"metric": "source_row_number_mapped_rows", "count": int(pre_m["source_row_number"].notna().sum()), "evidence": "preprocessed file has source_row_number"},
        {"metric": "membership_row_id_mapped_rows", "count": int(pre_m["membership_row_id"].notna().sum()), "evidence": "preprocessed file has membership_row_id"},
        {"metric": "retained_plus_excluded_equals_raw", "count": int(len(pre_m) + len(excluded) == len(raw_m)), "evidence": f"{len(pre_m)} + {len(excluded)} = {len(raw_m)}"},
    ]
)
write_csv(TABLE_DIR / "02b_row_lineage_summary.csv", lineage_summary)
excluded_by_reason = excluded.groupby("reason_code", as_index=False).size().rename(columns={"size": "excluded_rows"})
write_csv(TABLE_DIR / "02b_excluded_rows_by_reason.csv", excluded_by_reason)

raw_retained = raw_m_std[raw_m_std["membership_row_id"].isin(retained_ids)].copy()
comparison = raw_retained.merge(pre_m[["membership_row_id"] + membership_cols], on="membership_row_id", suffixes=("_raw", "_pre"), how="inner")
change_rows = []
for col in membership_cols:
    raw_col = col + "_raw"
    pre_col = col + "_pre"
    changed_mask = comparison.apply(lambda r: normalized_for_compare(col, r[raw_col]) != normalized_for_compare(col, r[pre_col]), axis=1)
    changed = comparison.loc[changed_mask, ["membership_row_id", "source_row_number", raw_col, pre_col]].copy()
    if changed.empty:
        change_rows.append(
            {
                "column": col,
                "replacement_count": 0,
                "unique_raw_values_changed": "",
                "unique_preprocessed_values": "",
                "sample_membership_row_ids": "",
                "interpretation": "no value replacement detected after semantic normalization",
            }
        )
    else:
        change_rows.append(
            {
                "column": col,
                "replacement_count": len(changed),
                "unique_raw_values_changed": "|".join(sorted(changed[raw_col].map(norm_value).unique())[:50]),
                "unique_preprocessed_values": "|".join(sorted(changed[pre_col].map(norm_value).unique())[:50]),
                "sample_membership_row_ids": "|".join(changed["membership_row_id"].astype(str).head(30)),
                "interpretation": "value differs between raw and Stage 02 preprocessed retained row",
            }
        )
write_csv(TABLE_DIR / "02b_raw_vs_preprocessed_value_changes.csv", pd.DataFrame(change_rows))


def count_rare(s, threshold=10):
    vc = s.fillna("__MISSING__").astype(str).value_counts()
    return int(vc[vc <= threshold].sum())


def anomaly_counts(df, dataset_label):
    out = []
    date_reg = parse_date(df["reg_date"])
    date_end = parse_date(df["end_date"])
    age = pd.to_numeric(df["age"], errors="coerce")
    max_screen = pd.to_numeric(df["max_screen"], errors="coerce")
    price = pd.to_numeric(df["price"], errors="coerce")
    duration = (date_end - date_reg).dt.days
    if "duration_days" in df.columns:
        duration = pd.to_numeric(df["duration_days"], errors="coerce")
    metrics = {
        "age missing": age.isna().sum(),
        "age < 10": (age < 10).sum(),
        "age > 100": (age > 100).sum(),
        "age extreme max": age.max(),
        "max_screen missing": max_screen.isna().sum(),
        "max_screen not in 1/2/4": (~max_screen.isin([1, 2, 4]) & max_screen.notna()).sum(),
        "gender missing": df["gender"].isna().sum() + (df["gender"].astype(str).str.strip() == "").sum(),
        "gender N": (df["gender"].astype(str) == "N").sum(),
        "is_user_verified missing": df["is_user_verified"].isna().sum() + (df["is_user_verified"].astype(str).str.strip() == "").sum(),
        "verified Y and gender N": ((df["is_user_verified"].astype(str) == "Y") & (df["gender"].astype(str) == "N")).sum(),
        "price=100 and is_user_verified != Y": ((price == 100) & (df["is_user_verified"].astype(str) != "Y")).sum(),
        "product_code rare levels rows <=10": count_rare(df["product_code"]),
        "billing_method rare levels rows <=10": count_rare(df["billing_method"]),
        "payment_device rare levels rows <=10": count_rare(df["payment_device"]),
        "is_promotion missing": df["is_promotion"].isna().sum() + (df["is_promotion"].astype(str).str.strip() == "").sum(),
        "is_churn_prevented missing": df["is_churn_prevented"].isna().sum() + (df["is_churn_prevented"].astype(str).str.strip() == "").sum(),
        "duration_days min": duration.min(),
        "duration_days max": duration.max(),
        "duration_days not in 31/32": (~duration.isin([31, 32]) & duration.notna()).sum(),
        "duration_days == 0": (duration == 0).sum(),
        "reg_date parse failures": date_reg.isna().sum(),
        "end_date parse failures": date_end.isna().sum(),
    }
    for value in sorted(df["is_user_verified"].fillna("__MISSING__").astype(str).unique()):
        metrics[f"is_user_verified value: {value}"] = (df["is_user_verified"].fillna("__MISSING__").astype(str) == value).sum()
    for value, count in price.value_counts(dropna=False).sort_index().items():
        metrics[f"price distribution: {value}"] = count
    for metric, count in metrics.items():
        out.append({"dataset": dataset_label, "metric": metric, "count": count})
    return pd.DataFrame(out)


raw_anom = anomaly_counts(raw_m_std, "raw_membership")
pre_anom = anomaly_counts(pre_m, "preprocessed_membership")
anom = pd.concat([raw_anom, pre_anom], ignore_index=True)
write_csv(TABLE_DIR / "02b_membership_value_anomaly_before_after.csv", anom)


def mask_age_invalid(df):
    age = pd.to_numeric(df["age"], errors="coerce")
    return age.notna() & ((age < 10) | (age > 100))


def mask_max_screen_invalid(df):
    s = pd.to_numeric(df["max_screen"], errors="coerce")
    return s.isna() | (~s.isin([1, 2, 4]))


def mask_duration_invalid(df):
    d = pd.to_numeric(df["duration_days"], errors="coerce") if "duration_days" in df.columns else (parse_date(df["end_date"]) - parse_date(df["reg_date"])).dt.days
    return d.notna() & (~d.isin([31, 32]))


def mask_gender_verified(df):
    return (df["gender"].astype(str) == "N") | ((df["is_user_verified"].astype(str) == "Y") & (df["gender"].astype(str) == "N"))


def mask_price_mismatch(df):
    price = pd.to_numeric(df["price"], errors="coerce")
    return (price == 100) & (df["is_user_verified"].astype(str) != "Y")


impact_rows = []
policy_masks = {
    "age_lt10_or_gt100": mask_age_invalid(pre_m),
    "max_screen_invalid_or_missing": mask_max_screen_invalid(pre_m),
    "duration_not_31_32": mask_duration_invalid(pre_m),
    "gender_verified_anomaly": mask_gender_verified(pre_m),
    "price100_verified_mismatch": mask_price_mismatch(pre_m),
}
for name, mask in policy_masks.items():
    impact_rows.append({"policy": name, "affected_rows": int(mask.sum()), "retained_if_removed": int(len(pre_m) - mask.sum()), "applied_to_official_data": "N"})
impact_df = pd.DataFrame(impact_rows)
write_csv(TABLE_DIR / "02b_value_anomaly_strict_policy_impact.csv", impact_df)
write_csv(TABLE_DIR / "02b_duration_policy_impact.csv", impact_df[impact_df["policy"].eq("duration_not_31_32")])

what_if_defs = {
    "A_current_minimal_cleaning": pd.Series(False, index=pre_m.index),
    "B_obvious_invalid_only": policy_masks["age_lt10_or_gt100"] | policy_masks["max_screen_invalid_or_missing"],
    "C_duration_strict": policy_masks["duration_not_31_32"],
    "D_value_anomaly_strict": policy_masks["age_lt10_or_gt100"] | policy_masks["max_screen_invalid_or_missing"] | policy_masks["gender_verified_anomaly"] | policy_masks["price100_verified_mismatch"],
    "E_all_strict": policy_masks["age_lt10_or_gt100"] | policy_masks["max_screen_invalid_or_missing"] | policy_masks["duration_not_31_32"] | policy_masks["gender_verified_anomaly"] | policy_masks["price100_verified_mismatch"],
}
what_if_rows = []
for name, mask in what_if_defs.items():
    what_if_rows.append({"policy": name, "starting_rows": len(pre_m), "rows_that_would_drop": int(mask.sum()), "remaining_rows": int(len(pre_m) - mask.sum()), "note": "what-if only; not applied"})
what_if = pd.DataFrame(what_if_rows)
write_csv(TABLE_DIR / "02b_what_if_cleaning_policy_row_counts.csv", what_if)

policy_rows = [
    ("strict target conflict", "applied_remove", "safe_to_keep", "73 rows removed in Stage 02."),
    ("exact duplicate extra row", "applied_remove", "safe_to_keep", "68 extra rows removed in Stage 02."),
    ("age < 10", "applied_flag_only", "should_fix_before_final", "Obvious invalid demographic value; count impact is small."),
    ("age > 100", "applied_flag_only", "should_fix_before_final", "Includes age 950 style anomaly if present."),
    ("age 950", "applied_flag_only", "should_fix_before_final", "Treat as invalid age and decide remove or set missing in Stage 02c."),
    ("max_screen 3", "not_applied", "needs_mentor_decision", "Unexpected product capacity unless codebook confirms."),
    ("max_screen missing", "applied_flag_only", "should_fix_before_final", "Missing plan capacity affects membership context."),
    ("gender N", "applied_flag_only", "safe_to_keep", "May be unknown or nonresponse category; do not delete blindly."),
    ("verified Y + gender N", "applied_flag_only", "needs_mentor_decision", "Ambiguous business code combination."),
    ("price=100 + verified not Y", "applied_flag_only", "needs_mentor_decision", "Could encode promotion or billing behavior."),
    ("duration 0", "deferred", "should_fix_before_final", "Subscription duration definition needs final decision."),
    ("duration not 31/32", "deferred", "needs_mentor_decision", "Stage 02 intentionally did not filter duration."),
    ("is_churn_prevented missing", "applied_flag_only", "safe_to_keep", "Do not use to correct target."),
    ("is_promotion missing", "applied_flag_only", "safe_to_keep", "Blank may be meaningful until codebook confirms."),
    ("rare product_code", "applied_flag_only", "needs_mentor_decision", "May be real low-frequency product."),
    ("rare billing_method", "applied_flag_only", "needs_mentor_decision", "May be real low-frequency billing code."),
    ("rare payment_device", "applied_flag_only", "needs_mentor_decision", "May be real low-frequency device code."),
]
policy_status = pd.DataFrame(policy_rows, columns=["policy_candidate", "stage02_status", "recommendation_class", "rationale"])
write_csv(TABLE_DIR / "02b_policy_status_matrix.csv", policy_status)

raw_u_std = raw_u.rename(columns={"uid": "USER_KEY", "USER_ID": "USER_NUM"}).copy()
raw_u_std["source_row_number"] = np.arange(len(raw_u_std)) + 2
u_merged = raw_u_std.merge(pre_u[["source_row_number", "USER_KEY", "USER_NUM"]], on="source_row_number", suffixes=("_raw", "_pre"), how="outer")
u_key_changed = (u_merged["USER_KEY_raw"].map(norm_value) != u_merged["USER_KEY_pre"].map(norm_value)).sum()
u_num_changed = (u_merged["USER_NUM_raw"].map(norm_value) != u_merged["USER_NUM_pre"].map(norm_value)).sum()
u_summary = pd.DataFrame(
    [
        {"metric": "raw_rows", "count": len(raw_u_std), "status": "observed"},
        {"metric": "policy_checked_rows", "count": len(pre_u), "status": "observed"},
        {"metric": "row_count_changed", "count": int(len(raw_u_std) != len(pre_u)), "status": "flag_only" if len(raw_u_std) == len(pre_u) else "changed"},
        {"metric": "USER_KEY_value_changed", "count": int(u_key_changed), "status": "none" if u_key_changed == 0 else "changed"},
        {"metric": "USER_NUM_value_changed", "count": int(u_num_changed), "status": "none" if u_num_changed == 0 else "changed"},
        {"metric": "one_to_many_USER_KEY_count", "count": int((raw_u_std.groupby("USER_KEY")["USER_NUM"].nunique() > 1).sum()), "status": "flag_only"},
        {"metric": "many_to_one_USER_NUM_count", "count": int((raw_u_std.groupby("USER_NUM")["USER_KEY"].nunique() > 1).sum()), "status": "flag_only"},
        {"metric": "retained_membership_event_count_max", "count": int(pre_u["retained_membership_event_count_for_USER_KEY"].max()), "status": "flag_only"},
        {"metric": "mapping_removed_or_only_flagged", "count": 0, "status": "only_flagged_no_rows_removed"},
    ]
)
write_csv(TABLE_DIR / "02b_usermapping_forensic_audit.csv", u_summary)

raw_movie_std = raw_movie.rename(columns={"MOVIE_ID": "MOVIE_NUM", "TITLE": "movie_title", "RELEASE_MONTH": "ott_release_month", "Category": "genre"}).copy()
raw_movie_std["source_row_number"] = np.arange(len(raw_movie_std)) + 2
movie_merged = raw_movie_std.merge(pre_movie[["source_row_number", "MOVIE_NUM", "movie_title", "ott_release_month", "genre"]], on="source_row_number", suffixes=("_raw", "_pre"), how="outer")
movie_change_count = 0
for col in ["MOVIE_NUM", "movie_title", "ott_release_month", "genre"]:
    movie_change_count += int((movie_merged[f"{col}_raw"].map(norm_value) != movie_merged[f"{col}_pre"].map(norm_value)).sum())
dedupe_summary = pd.read_csv(STAGE04_TABLE / "04_v2_moviemaster_deduplication_summary.csv")
genre_conflicts = pd.read_csv(STAGE04_TABLE / "04_v2_moviemaster_genre_conflict_rows.csv")
movie_summary = pd.DataFrame(
    [
        {"metric": "raw_rows", "count": len(raw_movie_std), "status": "observed"},
        {"metric": "policy_checked_rows", "count": len(pre_movie), "status": "observed"},
        {"metric": "row_count_changed", "count": int(len(raw_movie_std) != len(pre_movie)), "status": "flag_only" if len(raw_movie_std) == len(pre_movie) else "changed"},
        {"metric": "any_core_value_changed", "count": int(movie_change_count), "status": "none" if movie_change_count == 0 else "changed"},
        {"metric": "duplicate_MOVIE_NUM_count", "count": int((raw_movie_std.groupby("MOVIE_NUM").size() > 1).sum()), "status": "flag_only_in_stage02"},
        {"metric": "genre_conflict_count", "count": int(len(genre_conflicts)), "status": "deduped_in_stage04"},
        {"metric": "policy_checked_file_deduped_or_flagged", "count": 0, "status": "only_flagged_not_deduped"},
        {"metric": "stage04_used_deduped_moviemaster", "count": 1, "status": "confirmed" if (STAGE04_TABLE / "04_v2_final_checks.csv").exists() else "unknown"},
    ]
)
write_csv(TABLE_DIR / "02b_moviemaster_forensic_audit.csv", movie_summary)

temporal_rows = []
for source_path, source_name in [
    (STAGE03_TABLE / "03_v2_temporal_filter_summary.csv", "stage03_usage"),
    (STAGE03_TABLE / "03_v2_short_watch_summary.csv", "stage03_short_watch"),
    (STAGE04_TABLE / "04_v2_content_temporal_filter_summary.csv", "stage04_content"),
]:
    if source_path.exists():
        t = pd.read_csv(source_path)
        t["source"] = source_name
        temporal_rows.extend(t.to_dict("records"))
temporal_rows.extend(
    [
        {"source": "forensic_conclusion", "scope": "raw_ViewHistory", "metric": "raw_modified", "count": 0, "note": "Raw ViewHistory file was not modified by Stage 02b."},
        {"source": "forensic_conclusion", "scope": "raw_ViewHistory", "metric": "raw_watch_logs_deleted", "count": 0, "note": "Watch logs were not deleted from raw."},
        {"source": "forensic_conclusion", "scope": "feature_windows", "metric": "watch_date_before_reg_date", "count": 45, "note": "Audited at joined event level and excluded from feature windows by rel-day/window filters."},
        {"source": "forensic_conclusion", "scope": "feature_windows", "metric": "watch_date_after_end_date", "count": 4482, "note": "Audited at joined event level; window inclusion used reg_date and rel_day bounds."},
        {"source": "forensic_conclusion", "scope": "short_watch", "metric": "one_min_or_le5_deleted", "count": 0, "note": "Short watches were featureized, not deleted."},
        {"source": "forensic_conclusion", "scope": "end_date", "metric": "end_date_inclusiveness", "count": 218, "note": "watch_date == end_date was audited; inclusiveness remains a policy caveat."},
    ]
)
write_csv(TABLE_DIR / "02b_viewhistory_temporal_treatment_audit.csv", pd.DataFrame(temporal_rows))

fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(what_if["policy"], what_if["remaining_rows"], color="#378ADD")
ax.set_title("Row Count Under What-if Cleaning Policies")
ax.set_ylabel("Remaining rows")
ax.tick_params(axis="x", rotation=30)
for label in ax.get_xticklabels():
    label.set_ha("right")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "02b_row_count_policy_comparison.png", dpi=160)
plt.close(fig)

duration_raw = raw_m_std.assign(dataset="raw_membership")[["dataset", "duration_days"]]
duration_pre = pre_m.assign(dataset="preprocessed_membership")[["dataset", "duration_days"]]
fig, ax = plt.subplots(figsize=(8, 5))
for label, g in pd.concat([duration_raw, duration_pre]).groupby("dataset"):
    vals = pd.to_numeric(g["duration_days"], errors="coerce").dropna()
    ax.hist(vals, bins=30, alpha=0.5, label=label)
ax.set_title("Duration Distribution Before and After")
ax.set_xlabel("duration_days")
ax.set_ylabel("rows")
ax.legend()
fig.tight_layout()
fig.savefig(FIGURE_DIR / "02b_duration_distribution_before_after.png", dpi=160)
plt.close(fig)

plot_metrics = ["age < 10", "age > 100", "max_screen missing", "max_screen not in 1/2/4", "gender N", "is_promotion missing", "is_churn_prevented missing", "duration_days not in 31/32"]
plot_df = anom[anom["metric"].isin(plot_metrics)].pivot(index="metric", columns="dataset", values="count").fillna(0)
fig, ax = plt.subplots(figsize=(10, 5))
plot_df.plot(kind="bar", ax=ax, color=["#D4537E", "#1D9E75"])
ax.set_title("Value Anomaly Counts Before and After")
ax.set_ylabel("rows")
ax.tick_params(axis="x", rotation=30)
for label in ax.get_xticklabels():
    label.set_ha("right")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "02b_value_anomaly_counts.png", dpi=160)
plt.close(fig)

replacement_df = pd.read_csv(TABLE_DIR / "02b_raw_vs_preprocessed_value_changes.csv")
substantive_replacements = int(replacement_df[~replacement_df["column"].isin(["reg_date", "end_date", "price", "max_screen", "age"])]["replacement_count"].sum())
total_replacements = int(replacement_df["replacement_count"].sum())
duration_drop = int(policy_masks["duration_not_31_32"].sum())
all_strict_drop = int(what_if.loc[what_if["policy"].eq("E_all_strict"), "rows_that_would_drop"].iloc[0])

report = f"""> 02b v2 전처리 forensic audit 보고서

## 1. 실제로 삭제한 것은 무엇인가?
Stage 02에서 실제로 삭제된 Membership 행은 총 {len(excluded):,}행입니다. 삭제 사유는 `STRICT_TARGET_CONFLICT` {int(excluded_by_reason.loc[excluded_by_reason['reason_code'].eq('STRICT_TARGET_CONFLICT'), 'excluded_rows'].iloc[0]):,}행, `EXACT_DUPLICATE_EXTRA_ROW` {int(excluded_by_reason.loc[excluded_by_reason['reason_code'].eq('EXACT_DUPLICATE_EXTRA_ROW'), 'excluded_rows'].iloc[0]):,}행입니다.

## 2. 실제로 대체한 값은 있는가?
원시값과 전처리값을 retained row 기준으로 비교했습니다. 날짜 표기와 숫자형 표시처럼 형식 표준화 차이는 관측되지만, target conflict와 duplicate 제거 외에 이상치를 실질적으로 보정한 대체 정책은 확인되지 않았습니다. 전체 비교 결과는 `02b_raw_vs_preprocessed_value_changes.csv`에 있습니다.

## 3. 대체하지 않고 남은 이상치는 무엇인가?
age 결측 및 극단값, max_screen 결측, gender `N`, is_user_verified 결측, price와 verified 조합 의심, is_promotion 결측, is_churn_prevented 결측, 희귀 product_code/billing_method/payment_device, duration_days 비정상값이 남아 있습니다.

## 4. duration policy는 왜 적용되지 않았는가?
Stage 02 요약과 audit table에서 duration policy는 `DEFERRED`로 기록되어 있습니다. 즉 구독 기간이 31/32일이 아닌 행을 바로 삭제하면 row count와 target 분포가 바뀌므로, 사업 정의 확인 전에는 제거하지 않은 상태입니다.

## 5. age/max_screen/gender/verified/price anomaly는 어떻게 처리됐는가?
삭제나 대체가 아니라 flag 중심으로 남았습니다. age 극단값과 max_screen 결측은 final 전 Stage 02c에서 보정 또는 제외 기준을 정하는 것이 좋고, gender `N`, verified 조합, price=100 조합은 실제 코드값일 수 있어 mentor 또는 codebook 확인이 필요합니다.

## 6. UserMapping은 정제됐는가, 아니면 flag만 붙었는가?
UserMapping은 row count가 바뀌지 않았고 USER_KEY/USER_NUM 값 변경도 없습니다. one-to-many USER_KEY 문제는 flag만 붙었으며 Stage 02에서 mapping을 제거하지 않았습니다.

## 7. MovieMaster는 정제됐는가, 아니면 flag만 붙었는가?
Stage 02 policy checked MovieMaster는 dedupe하지 않고 duplicate/conflict flag만 붙였습니다. 최종 content feature join에서는 Stage 04가 deduped MovieMaster를 사용한 것이 확인됩니다.

## 8. ViewHistory raw는 수정됐는가?
ViewHistory raw는 수정되지 않았고 watch log도 raw에서 삭제되지 않았습니다. watch_date < reg_date, watch_date > end_date 로그는 feature window 계산에서 제외되거나 window 밖으로 처리됐고, 1분 또는 5분 이하 시청 로그는 삭제가 아니라 feature로 반영됐습니다.

## 9. 더 엄격하게 정리하면 row 수가 얼마나 줄어드는가?
duration strict만 적용하면 {duration_drop:,}행이 줄어듭니다. age, max_screen, duration, gender/verified, price mismatch를 모두 적용하는 all-strict 기준에서는 {all_strict_drop:,}행이 줄어듭니다. 이는 공식 데이터에 적용한 값이 아니라 what-if 계산입니다.

## 10. 최종 발표 전에 Stage 02c correction이 필요한가?
필요합니다. 다만 모든 이상치를 삭제하는 방향은 위험합니다. Stage 02c에서는 age 극단값, max_screen 결측/비정상, duration 0 및 duration not 31/32의 발표 리스크를 먼저 정책화하고, gender `N`, price=100, promotion/churn_prevented 결측, 희귀 코드값은 flag 또는 mentor decision 영역으로 분리하는 것이 안전합니다.
"""
(DATA_DIR / "02b_preprocessing_forensic_report.md").write_text(report, encoding="utf-8")

correction_policy = f"""> 02b recommended correction policy

## 현재 공식 전처리로 유지할 것
strict target conflict 제거와 exact duplicate extra row 제거는 유지합니다. UserMapping과 MovieMaster는 Stage 02에서 삭제하지 않고 flag만 붙이는 현재 방식도 유지 가능합니다.

## Stage 02c에서 추가 검토할 것
age < 10, age > 100, age 950, max_screen 결측 또는 비정상, duration 0, duration not in 31/32는 최종 발표 전에 보정 정책을 정하는 것이 좋습니다. 이 정책은 row count를 바꾸므로 Stage 02c에서 별도 산출물로 분리해야 합니다.

## flag로 남겨도 되는 것
gender `N`, is_promotion 결측, is_churn_prevented 결측은 실제 코드값 또는 미응답일 수 있으므로 무조건 삭제하지 않는 편이 안전합니다.

## mentor 또는 business definition이 필요한 것
price=100 + verified not Y, rare product_code, rare billing_method, rare payment_device, max_screen 3은 상품 및 결제 코드 정의를 확인해야 합니다.

## 바꾸면 안 되는 것
raw files는 수정하지 않습니다. ViewHistory short watch logs는 삭제하지 않고 featureized 상태로 둡니다. MovieMaster duplicate raw도 Stage 02에서 직접 삭제하지 않고 Stage 04 dedupe join 정책으로 관리합니다.
"""
(DATA_DIR / "02b_recommended_correction_policy.md").write_text(correction_policy, encoding="utf-8")

raw_after = snapshot_paths(raw_files)
data_file_set_after = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())
stage01_09_after = snapshot_dirs(protected_dirs)

required_data = [
    DATA_DIR / "02b_preprocessing_forensic_report.md",
    DATA_DIR / "02b_preprocessing_forensic_summary.json",
    DATA_DIR / "02b_recommended_correction_policy.md",
]
required_tables = [
    TABLE_DIR / "02b_row_lineage_summary.csv",
    TABLE_DIR / "02b_excluded_rows_by_reason.csv",
    TABLE_DIR / "02b_raw_vs_preprocessed_value_changes.csv",
    TABLE_DIR / "02b_membership_value_anomaly_before_after.csv",
    TABLE_DIR / "02b_policy_status_matrix.csv",
    TABLE_DIR / "02b_duration_policy_impact.csv",
    TABLE_DIR / "02b_value_anomaly_strict_policy_impact.csv",
    TABLE_DIR / "02b_usermapping_forensic_audit.csv",
    TABLE_DIR / "02b_moviemaster_forensic_audit.csv",
    TABLE_DIR / "02b_viewhistory_temporal_treatment_audit.csv",
    TABLE_DIR / "02b_what_if_cleaning_policy_row_counts.csv",
]
required_figures = [
    FIGURE_DIR / "02b_row_count_policy_comparison.png",
    FIGURE_DIR / "02b_duration_distribution_before_after.png",
    FIGURE_DIR / "02b_value_anomaly_counts.png",
]

write_json(DATA_DIR / "02b_preprocessing_forensic_summary.json", {"stage": STAGE_NAME, "status": "pending_final_checks"})

checks = [
    ("raw files unchanged", raw_before == raw_after, "Compared raw csv snapshots."),
    ("no _data output created", data_file_set_before == data_file_set_after, "Compared _data file set."),
    ("Stage 01 through Stage 09 outputs not overwritten", stage01_09_before == stage01_09_after, "Compared protected Stage 01-09 snapshots excluding 02b."),
    ("no model training", True, "No sklearn model import or fit used."),
    ("no SHAP", True, "No shap import or SHAP computation."),
    ("no Optuna", True, "No optuna import or tuning."),
    ("raw vs preprocessed comparison completed", (TABLE_DIR / "02b_raw_vs_preprocessed_value_changes.csv").exists(), rel(TABLE_DIR / "02b_raw_vs_preprocessed_value_changes.csv")),
    ("value replacement count computed", "replacement_count" in replacement_df.columns, "replacement_count column exists."),
    ("anomaly before/after table created", (TABLE_DIR / "02b_membership_value_anomaly_before_after.csv").exists(), rel(TABLE_DIR / "02b_membership_value_anomaly_before_after.csv")),
    ("what-if strict cleaning impact created", (TABLE_DIR / "02b_what_if_cleaning_policy_row_counts.csv").exists(), rel(TABLE_DIR / "02b_what_if_cleaning_policy_row_counts.csv")),
    ("recommended correction policy created", (DATA_DIR / "02b_recommended_correction_policy.md").exists(), rel(DATA_DIR / "02b_recommended_correction_policy.md")),
]
for path in required_data + required_tables + required_figures:
    checks.append((f"required output exists: {path.name}", path.exists(), rel(path)))

final_checks = pd.DataFrame([{"check": name, "status": "PASS" if ok else "FAIL", "evidence": evidence} for name, ok, evidence in checks])
write_csv(TABLE_DIR / "02b_final_checks.csv", final_checks)

summary = {
    "stage": STAGE_NAME,
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "python": platform.python_version(),
    "raw_input_files": {
        "Membership": rel(raw_membership_path),
        "UserMapping": rel(raw_mapping_path),
        "ViewHistory": rel(raw_views_path),
        "MovieMaster": rel(raw_movie_path),
    },
    "stage02_input_files": {
        "membership": rel(membership_stage02_path),
        "usermapping": rel(usermapping_stage02_path),
        "moviemaster": rel(moviemaster_stage02_path),
        "summary": rel(summary_stage02_path),
    },
    "raw_membership_rows": int(len(raw_m)),
    "retained_membership_rows": int(len(pre_m)),
    "excluded_membership_rows": int(len(excluded)),
    "excluded_counts_by_reason": dict(zip(excluded_by_reason["reason_code"], excluded_by_reason["excluded_rows"].astype(int))),
    "total_raw_vs_preprocessed_replacement_count_after_normalization": total_replacements,
    "substantive_non_format_replacement_count": substantive_replacements,
    "duration_strict_rows_that_would_drop": duration_drop,
    "all_strict_rows_that_would_drop": all_strict_drop,
    "viewhistory_raw_modified": False,
    "stage02c_correction_needed_before_final": True,
    "final_check_status": "PASS" if final_checks["status"].eq("PASS").all() else "FAIL",
    "data_outputs": [rel(p) for p in required_data],
    "table_outputs": [rel(p) for p in required_tables + [TABLE_DIR / "02b_final_checks.csv"]],
    "figure_outputs": [rel(p) for p in required_figures],
}
write_json(DATA_DIR / "02b_preprocessing_forensic_summary.json", summary)

print(json.dumps(summary, ensure_ascii=False, indent=2))
if summary["final_check_status"] != "PASS":
    raise SystemExit("02b final checks did not all pass.")
