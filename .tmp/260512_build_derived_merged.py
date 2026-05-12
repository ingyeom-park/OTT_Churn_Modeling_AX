from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(r"C:\myCode\ott-churn-prediction")
PREPROCESS_DIR = (
    BASE_DIR / "kim.kwangil" / "preprocessing" / "260509_view_delete"
)
DERIVED_DIR = BASE_DIR / "kim.kwangil" / "derived_variable"
COMMON_FEATURE_SCRIPT = DERIVED_DIR / "260510_common_feature_analysis.py"
OUTPUT_FILE = DERIVED_DIR / "260512_derived_merged.csv"

MEMBERSHIP_FILE = PREPROCESS_DIR / "Membership_v2.csv"
USER_MAPPING_FILE = PREPROCESS_DIR / "User_Mapping_v2.csv"
VIEW_HISTORY_FILE = PREPROCESS_DIR / "View_History_v2.csv"
MOVIE_MASTER_FILE = PREPROCESS_DIR / "Movie_Master_v2.csv"

FINAL_DERIVED_FEATURES = [
    "mem_tenure_days",
    "mem_billing_method_value",
    "mem_screen_2_flag",
    "mem_is_verified",
    "mem_is_female",
    "mem_is_male",
    "mem_reg_hour_afternoon",
    "mem_reg_hour_evening",
    "mem_reg_hour_night",
    "mem_reg_weekday",
    "mem_reg_is_weekend",
    "mem_verified_multi_screen",
    "mem_verified_premium_screen",
    "mem_billing_method_131_flag",
    "mem_billing_method_132_flag",
    "mem_billing_method_140_flag",
    "mem_billing_method_151_flag",
    "mem_billing_method_170_flag",
    "mem_billing_method_180_flag",
    "mem_device_mobile_flag",
    "mem_device_pc_flag",
    "mem_device_smarttv_flag",
    "vh_median_watch_min",
    "vh_std_watch_min",
    "vh_max_watch_min",
    "vh_short_watch_ratio",
    "vh_max_daily_events",
    "vh_multi_event_day_ratio",
    "vh_std_daily_watch_min",
    "vh_titles_per_active_day",
    "vh_watch_min_per_active_day",
    "vh_watch_min_per_tenure_day",
    "vh_rewatch_event_ratio",
    "vh_repeat_event_count",
    "vh_avg_watch_min_per_title",
    "vh_activity_density",
    "vh_binge_index",
    "vh_weekend_ratio",
    "vh_week2_watch_ratio",
    "vh_week3_watch_ratio",
    "vh_w2_minus_w1_watch_min",
    "vh_w3_minus_w2_watch_min",
    "vh_w3_to_w1_ratio_capped",
    "vh_recent_release_180d_ratio",
    "vh_recent_release_365d_ratio",
    "vh_old_catalog_5y_ratio",
    "vh_median_content_age_days",
    "vh_genre_unique_count",
    "vh_top_genre_share",
    "genre_share__Action_Adventure",
    "genre_share__Animation_Family",
    "genre_share__Comedy",
    "genre_share__Drama",
    "genre_share__Historical_War",
    "genre_share__Horror",
    "genre_share__Other",
    "genre_share__Romance",
    "genre_share__SF_Fantasy",
    "genre_share__Thriller_Crime",
]


def load_common_feature_module():
    spec = importlib.util.spec_from_file_location(
        "common_feature_analysis",
        COMMON_FEATURE_SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def clean_movie_master(movie_master: pd.DataFrame) -> pd.DataFrame:
    key_col = "MOVIE_NUM"
    compare_cols = [col for col in movie_master.columns if col != key_col]

    movie_num_count = movie_master.groupby(key_col)[key_col].transform("size")
    is_duplicate_key = movie_num_count.ge(2)
    is_same_row_duplicate = movie_master.duplicated(
        subset=[key_col] + compare_cols,
        keep="first",
    )
    drop_mask = is_duplicate_key & is_same_row_duplicate
    movie_clean = movie_master.loc[~drop_mask].copy()

    remaining_duplicate_keys = (
        movie_clean[key_col]
        .value_counts()
        .loc[lambda series: series >= 2]
        .index
    )
    keep_mask = ~(
        movie_clean[key_col].isin(remaining_duplicate_keys)
        & movie_clean.duplicated(subset=[key_col], keep="first")
    )
    movie_final = movie_clean.loc[keep_mask].copy()
    return movie_final


def build_membership_mapping(
    membership: pd.DataFrame,
    user_mapping: pd.DataFrame,
) -> pd.DataFrame:
    membership_work = membership.copy()
    mapping_work = user_mapping.copy()

    membership_work["merge_order"] = membership_work.groupby("USER_KEY").cumcount()
    mapping_work["merge_order"] = mapping_work.groupby("USER_KEY").cumcount()

    membership_mapping = membership_work.merge(
        mapping_work[["USER_KEY", "USER_NUM", "merge_order"]],
        on=["USER_KEY", "merge_order"],
        how="left",
    )
    membership_mapping["membership_row_id"] = np.arange(
        len(membership_mapping),
        dtype=int,
    )
    membership_mapping["user_group_key"] = (
        "row_" + membership_mapping["membership_row_id"].astype(str)
    )
    membership_mapping["group"] = pd.to_numeric(
        membership_mapping["is_promotion"],
        errors="coerce",
    ).fillna(0).astype(int)
    return membership_mapping


def parse_membership_dates(series: pd.Series) -> pd.Series:
    parts = series.astype(str).str.split("-", expand=True)
    day = pd.to_numeric(parts[0].str[-2:], errors="coerce")
    month = pd.to_numeric(parts[1], errors="coerce")
    year = 2000 + pd.to_numeric(parts[2], errors="coerce")
    return pd.to_datetime(
        pd.DataFrame({"year": year, "month": month, "day": day}),
        errors="coerce",
    )


def prepare_raw_event_frame(
    membership_mapping: pd.DataFrame,
    view_history: pd.DataFrame,
    movie_master: pd.DataFrame,
) -> pd.DataFrame:
    view_movie = view_history.merge(
        movie_master,
        on="MOVIE_NUM",
        how="left",
    )

    raw = membership_mapping.merge(
        view_movie,
        on="USER_NUM",
        how="left",
    )

    raw["USER_NUM"] = pd.to_numeric(raw["USER_NUM"], errors="coerce")
    raw["age"] = pd.to_numeric(raw["age"], errors="coerce")
    raw["billing_method"] = pd.to_numeric(raw["billing_method"], errors="coerce")
    raw["max_screen"] = pd.to_numeric(raw["max_screen"], errors="coerce")
    raw["is_churn_prevented"] = pd.to_numeric(
        raw["is_churn_prevented"],
        errors="coerce",
    )
    raw["is_user_verified"] = pd.to_numeric(
        raw["is_user_verified"],
        errors="coerce",
    )
    raw["is_repurchase"] = pd.to_numeric(raw["is_repurchase"], errors="coerce")
    raw["reg_hour"] = pd.to_numeric(raw["reg_hour"], errors="coerce")
    raw["watch_time(min)"] = pd.to_numeric(raw["watch_time(min)"], errors="coerce")
    raw["watch_seq"] = pd.to_numeric(raw["watch_seq"], errors="coerce")

    raw["reg_date_dt"] = parse_membership_dates(raw["reg_date"])
    raw["end_date_dt"] = parse_membership_dates(raw["end_date"])
    raw["watch_date"] = pd.to_datetime(
        raw["watch_day"].astype("Int64").astype(str),
        format="%Y%m%d",
        errors="coerce",
    )
    raw["age_band"] = (raw["age"] // 10 * 10).astype("Int64")

    release_month = (
        raw["ott_release_month"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.replace("nan", "", regex=False)
        .str.zfill(6)
    )
    raw["release_date"] = pd.to_datetime(
        release_month + "01",
        format="%Y%m%d",
        errors="coerce",
    )
    return raw


def build_output_frame(
    membership_mapping: pd.DataFrame,
    feature_df: pd.DataFrame,
) -> pd.DataFrame:
    for feature_name in FINAL_DERIVED_FEATURES:
        if feature_name not in feature_df.columns:
            feature_df[feature_name] = 0.0

    feature_subset = feature_df[["user_group_key"] + FINAL_DERIVED_FEATURES].copy()

    base_columns = ["USER_NUM"] + list(pd.read_csv(MEMBERSHIP_FILE, nrows=0).columns)
    output = membership_mapping[["user_group_key"] + base_columns].copy()
    output = output.merge(feature_subset, on="user_group_key", how="left")
    output[FINAL_DERIVED_FEATURES] = (
        output[FINAL_DERIVED_FEATURES]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
    )
    output = output.drop(columns=["user_group_key"])
    return output


def main() -> None:
    common_module = load_common_feature_module()

    membership = pd.read_csv(MEMBERSHIP_FILE)
    user_mapping = pd.read_csv(USER_MAPPING_FILE)
    view_history = pd.read_csv(VIEW_HISTORY_FILE)
    movie_master = pd.read_csv(MOVIE_MASTER_FILE)

    movie_final = clean_movie_master(movie_master)
    membership_mapping = build_membership_mapping(membership, user_mapping)
    raw = prepare_raw_event_frame(membership_mapping, view_history, movie_final)
    safe = common_module.filter_safe_view_history(raw)
    feature_df = common_module.build_user_feature_table(raw, safe)

    output = build_output_frame(membership_mapping, feature_df)
    output.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    missing_usernum = int(output["USER_NUM"].isna().sum())
    duplicated_usernum = int(output["USER_NUM"].duplicated().sum())
    safe_user_count = int(feature_df["user_group_key"].nunique())

    print(f"output_file={OUTPUT_FILE}")
    print(f"rows={len(output)}")
    print(f"cols={len(output.columns)}")
    print(f"derived_feature_count={len(FINAL_DERIVED_FEATURES)}")
    print(f"missing_usernum={missing_usernum}")
    print(f"duplicated_usernum={duplicated_usernum}")
    print(f"safe_feature_user_count={safe_user_count}")


if __name__ == "__main__":
    main()
