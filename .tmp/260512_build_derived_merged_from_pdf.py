from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(r"C:\myCode\ott-churn-prediction")
PREPROCESS_DIR = (
    BASE_DIR / "kim.kwangil" / "preprocessing" / "260509_view_delete"
)
OUTPUT_FILE = (
    BASE_DIR / "kim.kwangil" / "derived_variable" / "260512_derived_merged.csv"
)


MEMBERSHIP_FILE = PREPROCESS_DIR / "Membership_v2.csv"
USER_MAPPING_FILE = PREPROCESS_DIR / "User_Mapping_v2.csv"
VIEW_HISTORY_FILE = PREPROCESS_DIR / "View_History_v2.csv"
MOVIE_MASTER_FILE = PREPROCESS_DIR / "Movie_Master_v2.csv"

PDF_FEATURE_ORDER = [
    "is_repurchase",
    "is_standard",
    "is_premium",
    "is_churn_prevented",
    "is_promotion",
    "is_user_verified",
    "age_group",
    "is_female",
    "is_male",
    "reg_is_weekend",
    "reg_hour_morning",
    "reg_hour_afternoon",
    "reg_hour_evening",
    "reg_hour_night",
    "payment_is_mobile",
    "payment_is_pc",
    "payment_is_android",
    "payment_is_ios",
    "total_watch_count",
    "unique_movie",
    "watch_days",
    "active_ratio",
    "total_watch_time",
    "watch_per_day",
    "avg_watch_time",
    "median_watch_time",
    "std_watch_time",
    "avg_daily_watch_time",
    "max_watch_time",
    "max_daily_watch_time",
    "max_daily_sessions",
    "recency",
    "avg_gap_between_watch_days",
    "avg_gap_w1_watch_days",
    "avg_gap_w2_watch_days",
    "avg_gap_w3_watch_days",
    "max_inactive_gap_days",
    "avg_rewatch_ratio",
    "weekend_watch_ratio",
    "watch_ratio_under_1m",
    "watch_ratio_under_5m",
    "is_cold_start_3d",
    "is_cold_start_7d",
    "movie_per_active_day",
    "max_day_share",
    "day_count_over_3times",
    "watch_time_w1",
    "watch_time_w2",
    "watch_time_w3",
    "watch_session_w1",
    "watch_session_w2",
    "watch_session_w3",
    "retention_w2_ratio",
    "retention_w3_ratio",
    "w3_to_w1_ratio_capped",
    "diff_between_w2_w1",
    "diff_between_w3_w1",
    "diff_between_w3_w2",
    "is_w1_over_50%",
    "is_w2_over_50%",
    "is_w3_over_50%",
    "is_only_w1",
    "is_only_w2",
    "is_only_w3",
    "new_movie_in_90d_ratio",
    "new_movie_in_180d_ratio",
    "new_movie_in_365d_ratio",
    "old_movie_ratio(5y)",
    "avg_release_year",
    "genre_diversity_count",
    "action_adventure_ratio",
    "family_animation_ratio",
    "drama_ratio",
    "thriller_crime_ratio",
    "sf_fantasy_ratio",
    "comedy_ratio",
    "romance_ratio",
    "horror_ratio",
    "documentary_ratio",
    "historical_war_ratio",
    "other_ratio",
]

GENRE_RATIO_MAP = {
    "Action/Adventure": "action_adventure_ratio",
    "Animation/Family": "family_animation_ratio",
    "Drama": "drama_ratio",
    "Thriller/Crime": "thriller_crime_ratio",
    "SF/Fantasy": "sf_fantasy_ratio",
    "Comedy": "comedy_ratio",
    "Romance": "romance_ratio",
    "Horror": "horror_ratio",
    "Documentary": "documentary_ratio",
    "Historical/War": "historical_war_ratio",
    "Other": "other_ratio",
}


def safe_divide(left: pd.Series, right: pd.Series) -> pd.Series:
    return left / right.replace(0, np.nan)


def decode_membership_date(series: pd.Series) -> pd.Series:
    parts = series.astype(str).str.split("-", expand=True)
    day = pd.to_numeric(parts[0].str[-2:], errors="coerce")
    month = pd.to_numeric(parts[1], errors="coerce")
    year = 2000 + pd.to_numeric(parts[2], errors="coerce")
    return pd.to_datetime(
        pd.DataFrame({"year": year, "month": month, "day": day}),
        errors="coerce",
    )


def clean_movie_master(movie_master: pd.DataFrame) -> pd.DataFrame:
    key_col = "MOVIE_NUM"
    compare_cols = [column for column in movie_master.columns if column != key_col]

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

    merged = membership_work.merge(
        mapping_work[["USER_KEY", "USER_NUM", "merge_order"]],
        on=["USER_KEY", "merge_order"],
        how="left",
    )
    merged["membership_row_id"] = np.arange(len(merged), dtype=int)
    merged["reg_date_dt"] = decode_membership_date(merged["reg_date"])
    merged["end_date_dt"] = decode_membership_date(merged["end_date"])
    return merged


def prepare_event_frame(
    membership_mapping: pd.DataFrame,
    view_history: pd.DataFrame,
    movie_master: pd.DataFrame,
) -> pd.DataFrame:
    event = view_history.merge(
        movie_master,
        on="MOVIE_NUM",
        how="left",
    )

    raw = membership_mapping[
        ["membership_row_id", "USER_NUM", "reg_date_dt", "end_date_dt"]
    ].merge(
        event,
        on="USER_NUM",
        how="left",
    )

    raw["watch_time(min)"] = pd.to_numeric(raw["watch_time(min)"], errors="coerce")
    raw["watch_seq"] = pd.to_numeric(raw["watch_seq"], errors="coerce")
    raw["watch_date"] = pd.to_datetime(
        raw["watch_day"].astype("Int64").astype(str),
        format="%Y%m%d",
        errors="coerce",
    )
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
    raw["release_year"] = raw["release_date"].dt.year

    raw["days_from_reg"] = (
        raw["watch_date"] - raw["reg_date_dt"]
    ).dt.days
    raw = raw.loc[
        raw["watch_date"].notna()
        & raw["reg_date_dt"].notna()
        & raw["days_from_reg"].between(0, 20, inclusive="both")
    ].copy()

    raw["week_idx"] = np.select(
        [
            raw["days_from_reg"].between(0, 6, inclusive="both"),
            raw["days_from_reg"].between(7, 13, inclusive="both"),
            raw["days_from_reg"].between(14, 20, inclusive="both"),
        ],
        [1, 2, 3],
        default=0,
    )
    raw["is_weekend"] = raw["watch_date"].dt.weekday.isin([5, 6]).astype(int)
    raw["is_under_1m"] = (raw["watch_time(min)"] <= 1).astype(int)
    raw["is_under_5m"] = (raw["watch_time(min)"] <= 5).astype(int)
    raw["is_new_movie_90d"] = (raw["release_date"] >= pd.Timestamp("2021-01-01")).astype(int)
    raw["is_new_movie_180d"] = (raw["release_date"] >= pd.Timestamp("2020-09-01")).astype(int)
    raw["is_new_movie_365d"] = (raw["release_date"] >= pd.Timestamp("2020-03-01")).astype(int)
    raw["is_old_movie_5y"] = (raw["release_date"] < pd.Timestamp("2016-03-01")).astype(int)
    return raw


def compute_gap_mean(series: pd.Series) -> float:
    unique_days = np.sort(series.dropna().astype(int).unique())
    if len(unique_days) < 2:
        return 0.0
    return float(np.diff(unique_days).mean())


def compute_gap_max(series: pd.Series) -> float:
    unique_days = np.sort(series.dropna().astype(int).unique())
    if len(unique_days) < 2:
        return 0.0
    return float(np.diff(unique_days).max())


def build_feature_frame(event_df: pd.DataFrame) -> pd.DataFrame:
    user_ids = pd.Index(
        sorted(event_df["membership_row_id"].dropna().astype(int).unique()),
        name="membership_row_id",
    )
    feature_df = pd.DataFrame(index=user_ids)

    grouped = event_df.groupby("membership_row_id")
    daily = (
        event_df.groupby(["membership_row_id", "watch_date"], dropna=False)
        .agg(
            daily_sessions=("watch_date", "size"),
            daily_watch_time=("watch_time(min)", "sum"),
            day_idx=("days_from_reg", "min"),
        )
        .reset_index()
    )
    daily_grouped = daily.groupby("membership_row_id")

    feature_df["total_watch_count"] = grouped.size()
    feature_df["unique_movie"] = grouped["MOVIE_NUM"].nunique()
    feature_df["watch_days"] = grouped["watch_date"].nunique()
    feature_df["total_watch_time"] = grouped["watch_time(min)"].sum()
    feature_df["watch_per_day"] = safe_divide(
        feature_df["total_watch_count"],
        feature_df["watch_days"],
    )
    feature_df["active_ratio"] = feature_df["watch_days"] / 21.0

    feature_df["avg_watch_time"] = grouped["watch_time(min)"].mean()
    feature_df["median_watch_time"] = grouped["watch_time(min)"].median()
    feature_df["std_watch_time"] = grouped["watch_time(min)"].agg(
        lambda series: float(series.std(ddof=0))
    )
    feature_df["avg_daily_watch_time"] = safe_divide(
        feature_df["total_watch_time"],
        feature_df["watch_days"],
    )
    feature_df["max_watch_time"] = grouped["watch_time(min)"].max()
    feature_df["max_daily_watch_time"] = daily_grouped["daily_watch_time"].max()
    feature_df["max_daily_sessions"] = daily_grouped["daily_sessions"].max()
    feature_df["max_day_share"] = safe_divide(
        feature_df["max_daily_watch_time"],
        feature_df["total_watch_time"],
    )
    feature_df["day_count_over_3times"] = daily_grouped["daily_sessions"].agg(
        lambda series: int((series >= 3).sum())
    )

    feature_df["recency"] = 20 - grouped["days_from_reg"].max()
    feature_df["avg_gap_between_watch_days"] = daily_grouped["day_idx"].agg(
        compute_gap_mean
    )
    feature_df["max_inactive_gap_days"] = daily_grouped["day_idx"].agg(
        compute_gap_max
    )

    for week_idx, feature_name in {
        1: "avg_gap_w1_watch_days",
        2: "avg_gap_w2_watch_days",
        3: "avg_gap_w3_watch_days",
    }.items():
        week_daily = daily.loc[daily["day_idx"].between((week_idx - 1) * 7, week_idx * 7 - 1)]
        week_gap = week_daily.groupby("membership_row_id")["day_idx"].agg(compute_gap_mean)
        feature_df[feature_name] = week_gap

    feature_df["avg_rewatch_ratio"] = safe_divide(
        feature_df["total_watch_count"] - feature_df["unique_movie"],
        feature_df["total_watch_count"],
    )
    feature_df["weekend_watch_ratio"] = grouped["is_weekend"].mean()
    feature_df["watch_ratio_under_1m"] = grouped["is_under_1m"].mean()
    feature_df["watch_ratio_under_5m"] = grouped["is_under_5m"].mean()

    first_watch_day = grouped["days_from_reg"].min()
    feature_df["is_cold_start_3d"] = (first_watch_day <= 2).astype(int)
    feature_df["is_cold_start_7d"] = (first_watch_day <= 6).astype(int)
    feature_df["movie_per_active_day"] = safe_divide(
        feature_df["unique_movie"],
        feature_df["watch_days"],
    )

    weekly_watch_time = (
        event_df.pivot_table(
            index="membership_row_id",
            columns="week_idx",
            values="watch_time(min)",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=[1, 2, 3], fill_value=0)
    )
    weekly_sessions = (
        event_df.pivot_table(
            index="membership_row_id",
            columns="week_idx",
            values="watch_time(min)",
            aggfunc="size",
            fill_value=0,
        )
        .reindex(columns=[1, 2, 3], fill_value=0)
    )

    weekly_watch_time.columns = ["watch_time_w1", "watch_time_w2", "watch_time_w3"]
    weekly_sessions.columns = ["watch_session_w1", "watch_session_w2", "watch_session_w3"]

    feature_df = feature_df.join(weekly_watch_time, how="left")
    feature_df = feature_df.join(weekly_sessions, how="left")

    feature_df["retention_w2_ratio"] = safe_divide(
        feature_df["watch_time_w2"],
        feature_df["watch_time_w1"],
    )
    feature_df["retention_w3_ratio"] = safe_divide(
        feature_df["watch_time_w3"],
        feature_df["total_watch_time"],
    )
    feature_df["w3_to_w1_ratio_capped"] = np.clip(
        safe_divide(
            feature_df["watch_time_w3"],
            feature_df["watch_time_w1"],
        ).fillna(0),
        a_min=0,
        a_max=10,
    )
    feature_df["diff_between_w2_w1"] = (
        feature_df["watch_time_w2"] - feature_df["watch_time_w1"]
    )
    feature_df["diff_between_w3_w1"] = (
        feature_df["watch_time_w3"] - feature_df["watch_time_w1"]
    )
    feature_df["diff_between_w3_w2"] = (
        feature_df["watch_time_w3"] - feature_df["watch_time_w2"]
    )
    feature_df["is_w1_over_50%"] = (
        safe_divide(
            feature_df["watch_time_w1"],
            feature_df["total_watch_time"],
        ).fillna(0)
        >= 0.5
    ).astype(int)
    feature_df["is_w2_over_50%"] = (
        safe_divide(
            feature_df["watch_time_w2"],
            feature_df["total_watch_time"],
        ).fillna(0)
        >= 0.5
    ).astype(int)
    feature_df["is_w3_over_50%"] = (
        safe_divide(
            feature_df["watch_time_w3"],
            feature_df["total_watch_time"],
        ).fillna(0)
        >= 0.5
    ).astype(int)
    feature_df["is_only_w1"] = (
        (feature_df["watch_time_w1"] > 0)
        & (feature_df["watch_time_w2"] == 0)
        & (feature_df["watch_time_w3"] == 0)
    ).astype(int)
    feature_df["is_only_w2"] = (
        (feature_df["watch_time_w1"] == 0)
        & (feature_df["watch_time_w2"] > 0)
        & (feature_df["watch_time_w3"] == 0)
    ).astype(int)
    feature_df["is_only_w3"] = (
        (feature_df["watch_time_w1"] == 0)
        & (feature_df["watch_time_w2"] == 0)
        & (feature_df["watch_time_w3"] > 0)
    ).astype(int)

    feature_df["new_movie_in_90d_ratio"] = grouped["is_new_movie_90d"].mean()
    feature_df["new_movie_in_180d_ratio"] = grouped["is_new_movie_180d"].mean()
    feature_df["new_movie_in_365d_ratio"] = grouped["is_new_movie_365d"].mean()
    feature_df["old_movie_ratio(5y)"] = grouped["is_old_movie_5y"].mean()
    feature_df["avg_release_year"] = grouped["release_year"].mean()
    feature_df["genre_diversity_count"] = grouped["genre"].nunique()

    genre_watch = (
        event_df.groupby(["membership_row_id", "genre"], dropna=False)["watch_time(min)"]
        .sum()
        .reset_index()
    )
    genre_pivot = genre_watch.pivot_table(
        index="membership_row_id",
        columns="genre",
        values="watch_time(min)",
        aggfunc="sum",
        fill_value=0,
    )
    genre_ratio = genre_pivot.div(
        genre_pivot.sum(axis=1).replace(0, np.nan),
        axis=0,
    )

    for genre_name, feature_name in GENRE_RATIO_MAP.items():
        if genre_name in genre_ratio.columns:
            feature_df[feature_name] = genre_ratio[genre_name]
        else:
            feature_df[feature_name] = 0.0

    feature_df = feature_df.reset_index()
    return feature_df


def build_membership_derived_columns(base_df: pd.DataFrame) -> pd.DataFrame:
    output = base_df.copy()
    output["age"] = pd.to_numeric(output["age"], errors="coerce")
    output["max_screen"] = pd.to_numeric(output["max_screen"], errors="coerce")
    output["reg_hour"] = pd.to_numeric(output["reg_hour"], errors="coerce")

    output["age_group"] = (output["age"] // 10 * 10)
    output["is_standard"] = (output["max_screen"] == 2).astype(int)
    output["is_premium"] = (output["max_screen"] == 4).astype(int)
    output["is_female"] = (output["gender"] == "F").astype(int)
    output["is_male"] = (output["gender"] == "M").astype(int)
    output["reg_hour_morning"] = output["reg_hour"].between(6, 11, inclusive="both").astype(int)
    output["reg_hour_afternoon"] = output["reg_hour"].between(12, 17, inclusive="both").astype(int)
    output["reg_hour_evening"] = output["reg_hour"].between(18, 23, inclusive="both").astype(int)
    output["reg_hour_night"] = output["reg_hour"].between(0, 5, inclusive="both").astype(int)
    output["reg_is_weekend"] = output["reg_date_dt"].dt.weekday.isin([5, 6]).astype(int)
    output["payment_is_mobile"] = (output["payment_device"] == "mobile").astype(int)
    output["payment_is_pc"] = (output["payment_device"] == "pc").astype(int)
    output["payment_is_android"] = (output["payment_device"] == "android").astype(int)
    output["payment_is_ios"] = (output["payment_device"] == "ios").astype(int)
    return output


def main() -> None:
    membership = pd.read_csv(MEMBERSHIP_FILE)
    user_mapping = pd.read_csv(USER_MAPPING_FILE)
    view_history = pd.read_csv(VIEW_HISTORY_FILE)
    movie_master = pd.read_csv(MOVIE_MASTER_FILE)

    movie_final = clean_movie_master(movie_master)
    membership_mapping = build_membership_mapping(membership, user_mapping)
    event_df = prepare_event_frame(membership_mapping, view_history, movie_final)
    feature_df = build_feature_frame(event_df)

    membership_base = build_membership_derived_columns(membership_mapping)
    merged = membership_base.merge(
        feature_df,
        on="membership_row_id",
        how="left",
    )

    watch_feature_defaults = {
        feature_name: 0.0
        for feature_name in PDF_FEATURE_ORDER
        if feature_name not in {
            "is_repurchase",
            "is_churn_prevented",
            "is_promotion",
            "is_user_verified",
            "age_group",
            "is_female",
            "is_male",
            "reg_is_weekend",
            "reg_hour_morning",
            "reg_hour_afternoon",
            "reg_hour_evening",
            "reg_hour_night",
            "payment_is_mobile",
            "payment_is_pc",
            "payment_is_android",
            "payment_is_ios",
            "is_standard",
            "is_premium",
        }
    }
    for column_name, default_value in watch_feature_defaults.items():
        if column_name not in merged.columns:
            merged[column_name] = default_value
        else:
            merged[column_name] = pd.to_numeric(
                merged[column_name],
                errors="coerce",
            ).fillna(default_value)

    merged["recency"] = merged["recency"].fillna(21)

    original_membership_columns = list(pd.read_csv(MEMBERSHIP_FILE, nrows=0).columns)
    extra_columns = [
        column_name
        for column_name in PDF_FEATURE_ORDER
        if column_name not in original_membership_columns
    ]
    output_columns = (
        ["USER_KEY", "USER_NUM"]
        + [column for column in original_membership_columns if column != "USER_KEY"]
        + extra_columns
    )

    output = merged[output_columns].copy()
    output.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"output_file={OUTPUT_FILE}")
    print(f"rows={len(output)}")
    print(f"cols={len(output.columns)}")
    print(f"event_rows_in_21d_window={len(event_df)}")
    print(f"missing_usernum={int(output['USER_NUM'].isna().sum())}")
    print(f"duplicate_usernum={int(output['USER_NUM'].duplicated().sum())}")
    print(f"added_columns={len(extra_columns)}")


if __name__ == "__main__":
    main()
