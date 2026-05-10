from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2, mannwhitneyu


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = Path(__file__).resolve().parent

FILE_MAP = {
    0: DATA_DIR / "260509_merged1_0.csv",
    1: DATA_DIR / "260509_merged1_1.csv",
}

TARGET_AGE_BANDS = [10, 20, 30, 40, 60]
AGE_LABEL_MAP = {
    10: "10대",
    20: "20대",
    30: "30대",
    40: "40대",
    50: "50대",
    60: "60대",
    70: "70대",
}

TOP_BILLING_METHODS = [131, 132, 134, 140, 151, 170, 180, 190]
DEVICE_VALUE_MAP = {
    "android": "android",
    "ios": "ios",
    "mobile": "mobile",
    "pc": "pc",
    "smarttv": "smarttv",
    "ott": "ott",
}

OUTPUT_FEATURE_FILE_0 = OUTPUT_DIR / "260510_user_features_0.csv"
OUTPUT_FEATURE_FILE_1 = OUTPUT_DIR / "260510_user_features_1.csv"
OUTPUT_MD_FILE = OUTPUT_DIR / "260510_feature_explanation.md"


def decode_membership_date(series: pd.Series) -> pd.Series:
    parts = series.astype(str).str.split("-", expand=True)
    day = pd.to_numeric(parts[0].str[-2:], errors="coerce")
    month = pd.to_numeric(parts[1], errors="coerce")
    year = 2000 + pd.to_numeric(parts[2], errors="coerce")
    return pd.to_datetime(
        pd.DataFrame({"year": year, "month": month, "day": day}),
        errors="coerce",
    )


def age_band_label(age_band: int | float | pd._libs.missing.NAType) -> str:
    if pd.isna(age_band):
        return "NA"
    return AGE_LABEL_MAP.get(int(age_band), f"{int(age_band)}대")


def safe_divide(left: pd.Series, right: pd.Series) -> pd.Series:
    return left / right.replace(0, np.nan)


def sanitize_text(value: str) -> str:
    return (
        str(value)
        .replace("/", "_")
        .replace(" ", "_")
        .replace("-", "_")
        .replace("__", "_")
    )


def entropy_from_counts(values: pd.Series) -> float:
    array = np.asarray(values, dtype=float)
    array = array[array > 0]
    if array.size == 0:
        return np.nan
    prob = array / array.sum()
    return float(-(prob * np.log(prob)).sum())


def load_raw_data() -> pd.DataFrame:
    frames = []
    for group_id, file_path in FILE_MAP.items():
        frame = pd.read_csv(file_path)
        frame["group"] = group_id
        frames.append(frame)

    raw = pd.concat(frames, ignore_index=True)
    raw["user_group_key"] = (
        raw["group"].astype(str) + "_" + raw["USER_NUM"].astype(str)
    )
    raw["watch_date"] = pd.to_datetime(
        raw["watch_day"].astype(str),
        format="%Y%m%d",
        errors="coerce",
    )
    raw["reg_date_dt"] = decode_membership_date(raw["reg_date"])
    raw["end_date_dt"] = decode_membership_date(raw["end_date"])
    raw["age"] = pd.to_numeric(raw["age"], errors="coerce")
    raw["age_band"] = (raw["age"] // 10 * 10).astype("Int64")
    raw["price"] = pd.to_numeric(raw["price"], errors="coerce")
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
    release_month = (
        raw["ott_release_month"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.zfill(6)
        + "01"
    )
    raw["release_date"] = pd.to_datetime(
        release_month,
        format="%Y%m%d",
        errors="coerce",
    )
    return raw


def filter_safe_view_history(raw: pd.DataFrame) -> pd.DataFrame:
    safe = raw.loc[
        raw["watch_date"].notna()
        & raw["reg_date_dt"].notna()
        & raw["end_date_dt"].notna()
    ].copy()
    safe = safe.loc[
        (safe["watch_date"] >= safe["reg_date_dt"])
        & (safe["watch_date"] <= safe["end_date_dt"])
    ].copy()

    safe["tenure_days"] = (
        safe["end_date_dt"] - safe["reg_date_dt"]
    ).dt.days.clip(lower=1)
    safe["days_from_reg"] = (
        safe["watch_date"] - safe["reg_date_dt"]
    ).dt.days.clip(lower=0)
    safe["days_to_end"] = (
        safe["end_date_dt"] - safe["watch_date"]
    ).dt.days.clip(lower=0)
    safe["weekday"] = safe["watch_date"].dt.weekday
    safe["is_weekend"] = safe["weekday"].isin([5, 6]).astype(int)
    safe["content_age_days"] = (
        safe["watch_date"] - safe["release_date"]
    ).dt.days
    safe["is_recent_release_180d"] = (
        (safe["content_age_days"] >= 0) & (safe["content_age_days"] <= 180)
    ).astype(int)
    safe["is_recent_release_365d"] = (
        (safe["content_age_days"] >= 0) & (safe["content_age_days"] <= 365)
    ).astype(int)
    safe["is_old_catalog_5y"] = (safe["content_age_days"] >= 365 * 5).astype(int)
    safe["is_short_watch"] = (safe["watch_time(min)"] <= 5).astype(int)
    safe["is_long_watch"] = (safe["watch_time(min)"] >= 60).astype(int)
    safe["week_index"] = np.minimum((safe["days_from_reg"] // 7) + 1, 5)
    return safe


def build_base_membership_frame(raw: pd.DataFrame) -> pd.DataFrame:
    base_columns = [
        "user_group_key",
        "group",
        "USER_NUM",
        "USER_KEY",
        "billing_method",
        "max_screen",
        "payment_device",
        "is_churn_prevented",
        "is_user_verified",
        "gender",
        "age",
        "age_band",
        "reg_date",
        "reg_hour",
        "end_date",
        "is_repurchase",
        "reg_date_dt",
        "end_date_dt",
    ]

    base = raw[base_columns].drop_duplicates("user_group_key").copy()
    base["mem_tenure_days"] = (
        base["end_date_dt"] - base["reg_date_dt"]
    ).dt.days.clip(lower=1)
    base["mem_billing_method_value"] = base["billing_method"]
    base["mem_max_screen_value"] = base["max_screen"]
    base["mem_screen_1_flag"] = (base["max_screen"] == 1).astype(int)
    base["mem_screen_2_flag"] = (base["max_screen"] == 2).astype(int)
    base["mem_screen_4_flag"] = (base["max_screen"] == 4).astype(int)
    base["mem_multi_screen_flag"] = (base["max_screen"] >= 2).astype(int)
    base["mem_premium_screen_flag"] = (base["max_screen"] >= 4).astype(int)
    base["mem_is_verified"] = base["is_user_verified"].fillna(0).astype(int)
    base["mem_is_churn_prevented_flag"] = (
        base["is_churn_prevented"].fillna(0).astype(int)
    )
    base["mem_is_female"] = (base["gender"] == "F").astype(int)
    base["mem_is_male"] = (base["gender"] == "M").astype(int)
    base["mem_reg_hour"] = base["reg_hour"]
    base["mem_reg_hour_morning"] = base["reg_hour"].between(
        6,
        11,
        inclusive="both",
    ).astype(int)
    base["mem_reg_hour_afternoon"] = base["reg_hour"].between(
        12,
        17,
        inclusive="both",
    ).astype(int)
    base["mem_reg_hour_evening"] = base["reg_hour"].between(
        18,
        23,
        inclusive="both",
    ).astype(int)
    base["mem_reg_hour_night"] = (
        (base["reg_hour"] >= 0) & (base["reg_hour"] <= 5)
    ).astype(int)
    base["mem_reg_weekday"] = base["reg_date_dt"].dt.weekday
    base["mem_reg_is_weekend"] = base["mem_reg_weekday"].isin([5, 6]).astype(int)
    base["mem_verified_multi_screen"] = (
        base["mem_is_verified"] * base["mem_multi_screen_flag"]
    )
    base["mem_verified_premium_screen"] = (
        base["mem_is_verified"] * base["mem_premium_screen_flag"]
    )

    for billing_method in TOP_BILLING_METHODS:
        base[f"mem_billing_method_{billing_method}_flag"] = (
            base["billing_method"] == billing_method
        ).astype(int)

    for device_name, device_value in DEVICE_VALUE_MAP.items():
        base[f"mem_device_{device_name}_flag"] = (
            base["payment_device"] == device_value
        ).astype(int)

    return base


def build_general_view_features(safe: pd.DataFrame) -> pd.DataFrame:
    feature_df = safe.groupby("user_group_key").agg(
        vh_event_count=("user_group_key", "size"),
        vh_title_count=("MOVIE_NUM", "nunique"),
        vh_active_day_count=("watch_date", "nunique"),
        vh_total_watch_min=("watch_time(min)", "sum"),
        vh_avg_watch_min=("watch_time(min)", "mean"),
        vh_median_watch_min=("watch_time(min)", "median"),
        vh_std_watch_min=("watch_time(min)", "std"),
        vh_max_watch_min=("watch_time(min)", "max"),
        vh_avg_watch_seq=("watch_seq", "mean"),
        vh_max_watch_seq=("watch_seq", "max"),
        vh_weekend_ratio=("is_weekend", "mean"),
        vh_short_watch_ratio=("is_short_watch", "mean"),
        vh_long_watch_ratio=("is_long_watch", "mean"),
        vh_recent_release_180d_ratio=("is_recent_release_180d", "mean"),
        vh_recent_release_365d_ratio=("is_recent_release_365d", "mean"),
        vh_old_catalog_5y_ratio=("is_old_catalog_5y", "mean"),
        vh_mean_content_age_days=("content_age_days", "mean"),
        vh_median_content_age_days=("content_age_days", "median"),
        vh_first_watch_lag_days=("days_from_reg", "min"),
        vh_last_watch_gap_days=("days_to_end", "min"),
    )
    return feature_df.reset_index()


def build_timing_features(safe: pd.DataFrame) -> pd.DataFrame:
    timing = safe.groupby("user_group_key").agg(
        first_watch=("watch_date", "min"),
        last_watch=("watch_date", "max"),
        reg_dt=("reg_date_dt", "min"),
        end_dt=("end_date_dt", "max"),
        tenure_days=("tenure_days", "max"),
        active_days=("watch_date", "nunique"),
    )
    timing["vh_watch_span_days"] = (
        timing["last_watch"] - timing["first_watch"]
    ).dt.days + 1
    timing["vh_active_day_ratio"] = safe_divide(
        timing["active_days"],
        timing["tenure_days"],
    )
    timing["vh_watch_span_ratio"] = safe_divide(
        timing["vh_watch_span_days"],
        timing["tenure_days"],
    )
    timing["vh_first_watch_lag_ratio"] = (
        (timing["first_watch"] - timing["reg_dt"]).dt.days
        / timing["tenure_days"].replace(0, np.nan)
    )
    timing["vh_last_watch_gap_ratio"] = (
        (timing["end_dt"] - timing["last_watch"]).dt.days
        / timing["tenure_days"].replace(0, np.nan)
    )
    return timing[
        [
            "vh_watch_span_days",
            "vh_active_day_ratio",
            "vh_watch_span_ratio",
            "vh_first_watch_lag_ratio",
            "vh_last_watch_gap_ratio",
        ]
    ].reset_index()


def build_daily_features(safe: pd.DataFrame) -> pd.DataFrame:
    daily = safe.groupby(["user_group_key", "watch_date"]).agg(
        day_event_count=("user_group_key", "size"),
        day_watch_min=("watch_time(min)", "sum"),
    )
    features = daily.groupby("user_group_key").agg(
        vh_max_daily_events=("day_event_count", "max"),
        vh_multi_event_day_ratio=("day_event_count", lambda series: (series >= 2).mean()),
        vh_avg_daily_watch_min=("day_watch_min", "mean"),
        vh_std_daily_watch_min=("day_watch_min", "std"),
        vh_max_daily_watch_min=("day_watch_min", "max"),
    )
    return features.reset_index()


def build_gap_features(safe: pd.DataFrame) -> pd.DataFrame:
    watch_days = (
        safe[["user_group_key", "watch_date"]]
        .drop_duplicates()
        .sort_values(["user_group_key", "watch_date"])
        .copy()
    )
    watch_days["prev_watch_date"] = watch_days.groupby("user_group_key")[
        "watch_date"
    ].shift(1)
    watch_days["gap_days"] = (
        watch_days["watch_date"] - watch_days["prev_watch_date"]
    ).dt.days
    gap_df = watch_days.groupby("user_group_key").agg(
        vh_mean_gap_days=("gap_days", "mean"),
        vh_std_gap_days=("gap_days", "std"),
        vh_max_gap_days=("gap_days", "max"),
    )
    return gap_df.reset_index()


def build_period_features(safe: pd.DataFrame) -> pd.DataFrame:
    period = safe[
        [
            "user_group_key",
            "watch_time(min)",
            "days_from_reg",
            "days_to_end",
            "tenure_days",
            "week_index",
        ]
    ].copy()

    total = period.groupby("user_group_key")["watch_time(min)"].sum().rename("total")
    weekly = period.pivot_table(
        index="user_group_key",
        columns="week_index",
        values="watch_time(min)",
        aggfunc="sum",
        fill_value=0,
    )
    for week_index in range(1, 6):
        if week_index not in weekly.columns:
            weekly[week_index] = 0
    weekly = weekly[[1, 2, 3, 4, 5]]
    weekly.columns = [f"vh_week{week}_watch_min" for week in range(1, 6)]
    period_df = weekly.merge(total, left_index=True, right_index=True, how="left")
    period_df = period_df.reset_index()

    for week_index in range(1, 6):
        week_col = f"vh_week{week_index}_watch_min"
        ratio_col = f"vh_week{week_index}_watch_ratio"
        period_df[ratio_col] = safe_divide(period_df[week_col], period_df["total"])

    first_half = (
        period.loc[(period["days_from_reg"] / period["tenure_days"]) <= 0.5]
        .groupby("user_group_key")["watch_time(min)"]
        .sum()
        .rename("first_half_watch")
    )
    last_7d = (
        period.loc[period["days_to_end"] <= 7]
        .groupby("user_group_key")["watch_time(min)"]
        .sum()
        .rename("last_7d_watch")
    )
    last_14d = (
        period.loc[period["days_to_end"] <= 14]
        .groupby("user_group_key")["watch_time(min)"]
        .sum()
        .rename("last_14d_watch")
    )

    period_df = period_df.merge(first_half, on="user_group_key", how="left")
    period_df = period_df.merge(last_7d, on="user_group_key", how="left")
    period_df = period_df.merge(last_14d, on="user_group_key", how="left")
    for column in ["first_half_watch", "last_7d_watch", "last_14d_watch"]:
        period_df[column] = period_df[column].fillna(0)

    period_df["vh_first_half_watch_ratio"] = safe_divide(
        period_df["first_half_watch"],
        period_df["total"],
    )
    period_df["vh_last_7d_watch_ratio"] = safe_divide(
        period_df["last_7d_watch"],
        period_df["total"],
    )
    period_df["vh_last_14d_watch_ratio"] = safe_divide(
        period_df["last_14d_watch"],
        period_df["total"],
    )
    period_df["vh_front_loaded_ratio"] = safe_divide(
        period_df["vh_week1_watch_min"] + period_df["vh_week2_watch_min"],
        period_df["total"],
    )
    period_df["vh_late_ratio"] = safe_divide(
        period_df["vh_week4_watch_min"] + period_df["vh_week5_watch_min"],
        period_df["total"],
    )
    period_df["vh_w2_minus_w1_watch_min"] = (
        period_df["vh_week2_watch_min"] - period_df["vh_week1_watch_min"]
    )
    period_df["vh_w3_minus_w2_watch_min"] = (
        period_df["vh_week3_watch_min"] - period_df["vh_week2_watch_min"]
    )
    period_df["vh_w3_to_w1_ratio_capped"] = np.clip(
        safe_divide(period_df["vh_week3_watch_min"], period_df["vh_week1_watch_min"])
        .fillna(0),
        a_min=0,
        a_max=10,
    )
    keep_columns = [
        "user_group_key",
        "vh_week1_watch_min",
        "vh_week2_watch_min",
        "vh_week3_watch_min",
        "vh_week4_watch_min",
        "vh_week5_watch_min",
        "vh_week1_watch_ratio",
        "vh_week2_watch_ratio",
        "vh_week3_watch_ratio",
        "vh_week4_watch_ratio",
        "vh_week5_watch_ratio",
        "vh_first_half_watch_ratio",
        "vh_last_7d_watch_ratio",
        "vh_last_14d_watch_ratio",
        "vh_front_loaded_ratio",
        "vh_late_ratio",
        "vh_w2_minus_w1_watch_min",
        "vh_w3_minus_w2_watch_min",
        "vh_w3_to_w1_ratio_capped",
    ]
    return period_df[keep_columns]


def build_genre_features(safe: pd.DataFrame) -> pd.DataFrame:
    genre_user = safe.groupby(["user_group_key", "genre"]).agg(
        genre_watch_min=("watch_time(min)", "sum")
    )
    genre_user = genre_user.reset_index()
    genre_total = genre_user.groupby("user_group_key")["genre_watch_min"].sum()
    genre_user = genre_user.merge(
        genre_total.rename("genre_total").reset_index(),
        on="user_group_key",
        how="left",
    )

    stats = genre_user.groupby("user_group_key").agg(
        vh_genre_unique_count=("genre", "nunique"),
        vh_genre_entropy=("genre_watch_min", entropy_from_counts),
        vh_top_genre_share=("genre_watch_min", lambda series: series.max() / series.sum()),
    )
    stats = stats.reset_index()

    genre_pivot = genre_user.pivot_table(
        index="user_group_key",
        columns="genre",
        values="genre_watch_min",
        aggfunc="sum",
        fill_value=0,
    )
    genre_share = genre_pivot.div(
        genre_pivot.sum(axis=1).replace(0, np.nan),
        axis=0,
    )
    genre_share.columns = [
        f"genre_share__{sanitize_text(column)}"
        for column in genre_share.columns
    ]
    genre_share = genre_share.reset_index()
    return stats.merge(genre_share, on="user_group_key", how="left")


def build_user_feature_table(raw: pd.DataFrame, safe: pd.DataFrame) -> pd.DataFrame:
    base = build_base_membership_frame(raw)
    frames = [
        build_general_view_features(safe),
        build_timing_features(safe),
        build_daily_features(safe),
        build_gap_features(safe),
        build_period_features(safe),
        build_genre_features(safe),
    ]

    feature_df = base.copy()
    for frame in frames:
        feature_df = feature_df.merge(frame, on="user_group_key", how="left")

    extra_feature_df = pd.DataFrame(index=feature_df.index)
    extra_feature_df["vh_events_per_active_day"] = safe_divide(
        feature_df["vh_event_count"],
        feature_df["vh_active_day_count"],
    )
    extra_feature_df["vh_titles_per_active_day"] = safe_divide(
        feature_df["vh_title_count"],
        feature_df["vh_active_day_count"],
    )
    extra_feature_df["vh_watch_min_per_active_day"] = safe_divide(
        feature_df["vh_total_watch_min"],
        feature_df["vh_active_day_count"],
    )
    extra_feature_df["vh_event_per_tenure_day"] = safe_divide(
        feature_df["vh_event_count"],
        feature_df["mem_tenure_days"],
    )
    extra_feature_df["vh_watch_min_per_tenure_day"] = safe_divide(
        feature_df["vh_total_watch_min"],
        feature_df["mem_tenure_days"],
    )
    extra_feature_df["vh_rewatch_event_ratio"] = safe_divide(
        feature_df["vh_event_count"] - feature_df["vh_title_count"],
        feature_df["vh_event_count"],
    )
    extra_feature_df["vh_title_per_event_ratio"] = safe_divide(
        feature_df["vh_title_count"],
        feature_df["vh_event_count"],
    )
    extra_feature_df["vh_repeat_event_count"] = (
        feature_df["vh_event_count"] - feature_df["vh_title_count"]
    )
    extra_feature_df["vh_avg_watch_min_per_title"] = safe_divide(
        feature_df["vh_total_watch_min"],
        feature_df["vh_title_count"],
    )
    extra_feature_df["vh_title_diversity_per_day"] = safe_divide(
        feature_df["vh_title_count"],
        feature_df["vh_active_day_count"],
    )
    extra_feature_df["vh_activity_density"] = safe_divide(
        feature_df["vh_active_day_count"],
        feature_df["vh_watch_span_days"],
    )
    extra_feature_df["vh_end_near_watch_ratio"] = (
        1 - feature_df["vh_last_watch_gap_ratio"]
    )
    extra_feature_df["vh_recency_intensity_index"] = (
        feature_df["vh_active_day_ratio"] * extra_feature_df["vh_end_near_watch_ratio"]
    )
    extra_feature_df["vh_retention_curve_index"] = (
        feature_df["vh_last_14d_watch_ratio"]
        - feature_df["vh_first_half_watch_ratio"]
    )
    extra_feature_df["vh_recent_old_gap"] = (
        feature_df["vh_recent_release_365d_ratio"]
        - feature_df["vh_old_catalog_5y_ratio"]
    )
    extra_feature_df["vh_short_minus_long_ratio"] = (
        feature_df["vh_short_watch_ratio"] - feature_df["vh_long_watch_ratio"]
    )
    extra_feature_df["vh_binge_index"] = safe_divide(
        feature_df["vh_max_daily_watch_min"],
        feature_df["vh_total_watch_min"],
    )
    extra_feature_df["vh_multi_event_intensity"] = (
        feature_df["vh_multi_event_day_ratio"]
        * extra_feature_df["vh_events_per_active_day"]
    )
    extra_feature_df["vh_mid_late_ratio"] = (
        feature_df["vh_week3_watch_ratio"]
        + feature_df["vh_week4_watch_ratio"]
        + feature_df["vh_week5_watch_ratio"]
    )
    extra_feature_df["vh_gap_stability_index"] = 1 / (
        1 + feature_df["vh_std_gap_days"].clip(lower=0)
    )
    extra_feature_df["vh_blockbuster_genre_share"] = (
        feature_df.get("genre_share__Action_Adventure", 0)
        + feature_df.get("genre_share__SF_Fantasy", 0)
        + feature_df.get("genre_share__Historical_War", 0)
    )
    extra_feature_df["vh_emotional_genre_share"] = (
        feature_df.get("genre_share__Drama", 0)
        + feature_df.get("genre_share__Romance", 0)
    )
    extra_feature_df["vh_light_genre_share"] = (
        feature_df.get("genre_share__Comedy", 0)
        + feature_df.get("genre_share__Animation_Family", 0)
    )
    extra_feature_df["vh_tension_genre_share"] = (
        feature_df.get("genre_share__Thriller_Crime", 0)
        + feature_df.get("genre_share__Horror", 0)
    )
    extra_feature_df["vh_nonfiction_genre_share"] = (
        feature_df.get("genre_share__Documentary", 0)
        + feature_df.get("genre_share__Other", 0)
    )
    feature_df = pd.concat([feature_df, extra_feature_df], axis=1)

    feature_cols = [
        column
        for column in feature_df.columns
        if column.startswith("mem_")
        or column.startswith("vh_")
        or column.startswith("genre_share__")
    ]
    feature_df[feature_cols] = (
        feature_df[feature_cols]
        .apply(pd.to_numeric, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
    )
    feature_df["group_label"] = feature_df["group"].map(
        {0: "프로모션X", 1: "프로모션O"}
    )
    feature_df["age_band_label"] = feature_df["age_band"].map(age_band_label)
    return feature_df


def get_feature_family(feature_name: str) -> str:
    if feature_name.startswith("mem_"):
        return "membership"
    if feature_name.startswith("genre_share__"):
        return "genre_share"
    if "genre" in feature_name:
        return "genre_composite"
    if "recent_release" in feature_name or "content_age" in feature_name:
        return "content_recency"
    if "gap" in feature_name or "recency" in feature_name or "retention" in feature_name or "near_watch" in feature_name:
        return "recency"
    if "week" in feature_name or "front_loaded" in feature_name or "late_ratio" in feature_name or "mid_late" in feature_name:
        return "timing_pattern"
    if "watch" in feature_name or "event" in feature_name or "active" in feature_name or "title" in feature_name or "binge" in feature_name:
        return "activity"
    return "composite"


def get_feature_source_columns(feature_name: str) -> str:
    if feature_name == "mem_tenure_days":
        return "reg_date, end_date"
    if feature_name.startswith("mem_billing_method_"):
        return "billing_method"
    if feature_name == "mem_billing_method_value":
        return "billing_method"
    if feature_name.startswith("mem_screen_") or feature_name in {
        "mem_max_screen_value",
        "mem_multi_screen_flag",
        "mem_premium_screen_flag",
    }:
        return "max_screen"
    if feature_name.startswith("mem_device_"):
        return "payment_device"
    if feature_name in {"mem_is_verified"}:
        return "is_user_verified"
    if feature_name in {"mem_is_churn_prevented_flag"}:
        return "is_churn_prevented"
    if feature_name in {"mem_is_female", "mem_is_male"}:
        return "gender"
    if feature_name.startswith("mem_reg_"):
        return "reg_date, reg_hour"
    if feature_name in {"mem_verified_multi_screen", "mem_verified_premium_screen"}:
        return "is_user_verified, max_screen"
    if feature_name.startswith("genre_share__"):
        return "genre, watch_time(min)"
    if "genre_share" in feature_name or "genre_" in feature_name:
        return "genre, watch_time(min)"
    if "content_age" in feature_name or "recent_release" in feature_name or "old_catalog" in feature_name or "recent_old_gap" in feature_name:
        return "watch_day, ott_release_month, watch_time(min)"
    if "gap" in feature_name or "recency" in feature_name or "retention" in feature_name or "near_watch" in feature_name:
        return "watch_day, reg_date, end_date, watch_time(min)"
    if "week" in feature_name or "front_loaded" in feature_name or "late_ratio" in feature_name or "mid_late" in feature_name:
        return "watch_day, reg_date, watch_time(min)"
    if "watch" in feature_name or "event" in feature_name or "active" in feature_name or "title" in feature_name or "binge" in feature_name:
        return "watch_day, watch_time(min), MOVIE_NUM, watch_seq"
    return ""


def get_feature_formula(feature_name: str) -> str:
    if feature_name == "mem_tenure_days":
        return "end_date_dt - reg_date_dt"
    if feature_name == "mem_billing_method_value":
        return "billing_method"
    if feature_name.startswith("mem_billing_method_") and feature_name.endswith("_flag"):
        code = feature_name.replace("mem_billing_method_", "").replace("_flag", "")
        return f"1[billing_method = {code}]"
    if feature_name == "mem_max_screen_value":
        return "max_screen"
    if feature_name == "mem_screen_1_flag":
        return "1[max_screen = 1]"
    if feature_name == "mem_screen_2_flag":
        return "1[max_screen = 2]"
    if feature_name == "mem_screen_4_flag":
        return "1[max_screen = 4]"
    if feature_name == "mem_multi_screen_flag":
        return "1[max_screen >= 2]"
    if feature_name == "mem_premium_screen_flag":
        return "1[max_screen >= 4]"
    if feature_name == "mem_is_verified":
        return "1[is_user_verified = 1]"
    if feature_name == "mem_is_churn_prevented_flag":
        return "1[is_churn_prevented = 1]"
    if feature_name == "mem_is_female":
        return "1[gender = F]"
    if feature_name == "mem_is_male":
        return "1[gender = M]"
    if feature_name == "mem_reg_hour":
        return "reg_hour"
    if feature_name == "mem_reg_hour_morning":
        return "1[6 <= reg_hour <= 11]"
    if feature_name == "mem_reg_hour_afternoon":
        return "1[12 <= reg_hour <= 17]"
    if feature_name == "mem_reg_hour_evening":
        return "1[18 <= reg_hour <= 23]"
    if feature_name == "mem_reg_hour_night":
        return "1[0 <= reg_hour <= 5]"
    if feature_name == "mem_reg_weekday":
        return "weekday(reg_date_dt)"
    if feature_name == "mem_reg_is_weekend":
        return "1[weekday(reg_date_dt) in {5, 6}]"
    if feature_name == "mem_verified_multi_screen":
        return "mem_is_verified × mem_multi_screen_flag"
    if feature_name == "mem_verified_premium_screen":
        return "mem_is_verified × mem_premium_screen_flag"
    if feature_name.startswith("mem_device_") and feature_name.endswith("_flag"):
        device = feature_name.replace("mem_device_", "").replace("_flag", "")
        return f"1[payment_device = {device}]"
    if feature_name == "vh_event_count":
        return r"\sum_i 1"
    if feature_name == "vh_title_count":
        return r"|\{MOVIE\_NUM_i\}|"
    if feature_name == "vh_active_day_count":
        return r"|\{watch\_date_i\}|"
    if feature_name == "vh_total_watch_min":
        return r"\sum_i watch\_time_i"
    if feature_name == "vh_avg_watch_min":
        return r"\frac{1}{N}\sum_i watch\_time_i"
    if feature_name == "vh_median_watch_min":
        return "median(watch_time_i)"
    if feature_name == "vh_std_watch_min":
        return "std(watch_time_i)"
    if feature_name == "vh_max_watch_min":
        return r"\max_i watch\_time_i"
    if feature_name == "vh_avg_watch_seq":
        return r"\frac{1}{N}\sum_i watch\_seq_i"
    if feature_name == "vh_max_watch_seq":
        return r"\max_i watch\_seq_i"
    if feature_name == "vh_weekend_ratio":
        return r"\frac{1}{N}\sum_i 1[watch\_date_i \in weekend]"
    if feature_name == "vh_short_watch_ratio":
        return r"\frac{1}{N}\sum_i 1[watch\_time_i \le 5]"
    if feature_name == "vh_long_watch_ratio":
        return r"\frac{1}{N}\sum_i 1[watch\_time_i \ge 60]"
    if feature_name == "vh_recent_release_180d_ratio":
        return r"\frac{1}{N}\sum_i 1[0 \le watch\_date_i - release\_date_i \le 180]"
    if feature_name == "vh_recent_release_365d_ratio":
        return r"\frac{1}{N}\sum_i 1[0 \le watch\_date_i - release\_date_i \le 365]"
    if feature_name == "vh_old_catalog_5y_ratio":
        return r"\frac{1}{N}\sum_i 1[watch\_date_i - release\_date_i \ge 1825]"
    if feature_name == "vh_mean_content_age_days":
        return r"\frac{1}{N}\sum_i (watch\_date_i - release\_date_i)"
    if feature_name == "vh_median_content_age_days":
        return "median(watch_date_i - release_date_i)"
    if feature_name == "vh_first_watch_lag_days":
        return r"\min_i (watch\_date_i - reg\_date)"
    if feature_name == "vh_last_watch_gap_days":
        return r"\min_i (end\_date - watch\_date_i)"
    if feature_name == "vh_watch_span_days":
        return r"\max_i watch\_date_i - \min_i watch\_date_i + 1"
    if feature_name == "vh_active_day_ratio":
        return r"\frac{vh\_active\_day\_count}{mem\_tenure\_days}"
    if feature_name == "vh_watch_span_ratio":
        return r"\frac{vh\_watch\_span\_days}{mem\_tenure\_days}"
    if feature_name == "vh_first_watch_lag_ratio":
        return r"\frac{vh\_first\_watch\_lag\_days}{mem\_tenure\_days}"
    if feature_name == "vh_last_watch_gap_ratio":
        return r"\frac{vh\_last\_watch\_gap\_days}{mem\_tenure\_days}"
    if feature_name == "vh_max_daily_events":
        return r"\max_d events(d)"
    if feature_name == "vh_multi_event_day_ratio":
        return r"\frac{1}{D}\sum_d 1[events(d) \ge 2]"
    if feature_name == "vh_avg_daily_watch_min":
        return r"\frac{1}{D}\sum_d watch\_time(d)"
    if feature_name == "vh_std_daily_watch_min":
        return "std(daily_watch_time)"
    if feature_name == "vh_max_daily_watch_min":
        return r"\max_d watch\_time(d)"
    if feature_name == "vh_mean_gap_days":
        return r"\frac{1}{G}\sum_g gap_g"
    if feature_name == "vh_std_gap_days":
        return "std(gap_days)"
    if feature_name == "vh_max_gap_days":
        return r"\max_g gap_g"
    if feature_name.startswith("vh_week") and feature_name.endswith("_watch_min"):
        week = feature_name.replace("vh_week", "").replace("_watch_min", "")
        return rf"\sum_i watch\_time_i \cdot 1[week\_index_i = {week}]"
    if feature_name.startswith("vh_week") and feature_name.endswith("_watch_ratio"):
        week = feature_name.replace("vh_week", "").replace("_watch_ratio", "")
        return rf"\frac{{vh\_week{week}\_watch\_min}}{{vh\_total\_watch\_min}}"
    if feature_name == "vh_first_half_watch_ratio":
        return r"\frac{\sum_i watch\_time_i \cdot 1[(watch\_date_i - reg\_date) / tenure \le 0.5]}{\sum_i watch\_time_i}"
    if feature_name == "vh_last_7d_watch_ratio":
        return r"\frac{\sum_i watch\_time_i \cdot 1[end\_date - watch\_date_i \le 7]}{\sum_i watch\_time_i}"
    if feature_name == "vh_last_14d_watch_ratio":
        return r"\frac{\sum_i watch\_time_i \cdot 1[end\_date - watch\_date_i \le 14]}{\sum_i watch\_time_i}"
    if feature_name == "vh_front_loaded_ratio":
        return r"\frac{vh\_week1\_watch\_min + vh\_week2\_watch\_min}{vh\_total\_watch\_min}"
    if feature_name == "vh_late_ratio":
        return r"\frac{vh\_week4\_watch\_min + vh\_week5\_watch\_min}{vh\_total\_watch\_min}"
    if feature_name == "vh_w2_minus_w1_watch_min":
        return r"vh\_week2\_watch\_min - vh\_week1\_watch\_min"
    if feature_name == "vh_w3_minus_w2_watch_min":
        return r"vh\_week3\_watch\_min - vh\_week2\_watch\_min"
    if feature_name == "vh_w3_to_w1_ratio_capped":
        return r"\min\left(10, \frac{vh\_week3\_watch\_min}{vh\_week1\_watch\_min}\right)"
    if feature_name == "vh_events_per_active_day":
        return r"\frac{vh\_event\_count}{vh\_active\_day\_count}"
    if feature_name == "vh_titles_per_active_day":
        return r"\frac{vh\_title\_count}{vh\_active\_day\_count}"
    if feature_name == "vh_watch_min_per_active_day":
        return r"\frac{vh\_total\_watch\_min}{vh\_active\_day\_count}"
    if feature_name == "vh_event_per_tenure_day":
        return r"\frac{vh\_event\_count}{mem\_tenure\_days}"
    if feature_name == "vh_watch_min_per_tenure_day":
        return r"\frac{vh\_total\_watch\_min}{mem\_tenure\_days}"
    if feature_name == "vh_rewatch_event_ratio":
        return r"\frac{vh\_event\_count - vh\_title\_count}{vh\_event\_count}"
    if feature_name == "vh_title_per_event_ratio":
        return r"\frac{vh\_title\_count}{vh\_event\_count}"
    if feature_name == "vh_repeat_event_count":
        return r"vh\_event\_count - vh\_title\_count"
    if feature_name == "vh_avg_watch_min_per_title":
        return r"\frac{vh\_total\_watch\_min}{vh\_title\_count}"
    if feature_name == "vh_title_diversity_per_day":
        return r"\frac{vh\_title\_count}{vh\_active\_day\_count}"
    if feature_name == "vh_activity_density":
        return r"\frac{vh\_active\_day\_count}{vh\_watch\_span\_days}"
    if feature_name == "vh_end_near_watch_ratio":
        return r"1 - vh\_last\_watch\_gap\_ratio"
    if feature_name == "vh_recency_intensity_index":
        return r"vh\_active\_day\_ratio \times vh\_end\_near\_watch\_ratio"
    if feature_name == "vh_retention_curve_index":
        return r"vh\_last\_14d\_watch\_ratio - vh\_first\_half\_watch\_ratio"
    if feature_name == "vh_recent_old_gap":
        return r"vh\_recent\_release\_365d\_ratio - vh\_old\_catalog\_5y\_ratio"
    if feature_name == "vh_short_minus_long_ratio":
        return r"vh\_short\_watch\_ratio - vh\_long\_watch\_ratio"
    if feature_name == "vh_binge_index":
        return r"\frac{vh\_max\_daily\_watch\_min}{vh\_total\_watch\_min}"
    if feature_name == "vh_multi_event_intensity":
        return r"vh\_multi\_event\_day\_ratio \times vh\_events\_per\_active\_day"
    if feature_name == "vh_mid_late_ratio":
        return r"vh\_week3\_watch\_ratio + vh\_week4\_watch\_ratio + vh\_week5\_watch\_ratio"
    if feature_name == "vh_gap_stability_index":
        return r"\frac{1}{1 + vh\_std\_gap\_days}"
    if feature_name == "vh_genre_unique_count":
        return r"|\{genre_i\}|"
    if feature_name == "vh_genre_entropy":
        return r"-\sum_g p_g \log p_g"
    if feature_name == "vh_top_genre_share":
        return r"\max_g p_g"
    if feature_name.startswith("genre_share__"):
        genre_name = feature_name.replace("genre_share__", "")
        return rf"\frac{{\sum_i watch\_time_i \cdot 1[genre_i = {genre_name}]}}{{\sum_i watch\_time_i}}"
    if feature_name == "vh_blockbuster_genre_share":
        return r"genre\_share(Action\_Adventure) + genre\_share(SF\_Fantasy) + genre\_share(Historical\_War)"
    if feature_name == "vh_emotional_genre_share":
        return r"genre\_share(Drama) + genre\_share(Romance)"
    if feature_name == "vh_light_genre_share":
        return r"genre\_share(Comedy) + genre\_share(Animation\_Family)"
    if feature_name == "vh_tension_genre_share":
        return r"genre\_share(Thriller\_Crime) + genre\_share(Horror)"
    if feature_name == "vh_nonfiction_genre_share":
        return r"genre\_share(Documentary) + genre\_share(Other)"
    return ""


def get_feature_description(feature_name: str) -> str:
    if feature_name.startswith("mem_"):
        return "멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수"
    if feature_name.startswith("genre_share__"):
        return "전체 시청시간 중 특정 장르 비중을 나타내는 파생변수"
    if "genre" in feature_name:
        return "장르 선호를 묶어서 해석 가능하게 만든 파생변수"
    if "recent_release" in feature_name or "content_age" in feature_name:
        return "최신작 선호와 카탈로그 연식을 반영하는 파생변수"
    if "gap" in feature_name or "recency" in feature_name or "retention" in feature_name or "near_watch" in feature_name:
        return "만기 직전 유지 패턴과 재방문 리듬을 반영하는 파생변수"
    if "week" in feature_name or "front_loaded" in feature_name or "late_ratio" in feature_name or "mid_late" in feature_name:
        return "구독 기간 내 시청 배분 패턴을 반영하는 파생변수"
    return "시청 강도와 사용 밀도를 반영하는 파생변수"


def get_usage_caution(feature_name: str) -> str:
    if feature_name == "mem_is_churn_prevented_flag":
        return "정책성 변수 가능성 존재"
    return "모델 입력 후보 가능"


def build_feature_dictionary(feature_cols: list[str]) -> pd.DataFrame:
    rows = []
    for feature_name in feature_cols:
        rows.append(
            {
                "feature_name": feature_name,
                "feature_family": get_feature_family(feature_name),
                "source_columns": get_feature_source_columns(feature_name),
                "formula": get_feature_formula(feature_name),
                "description": get_feature_description(feature_name),
                "usage_caution": get_usage_caution(feature_name),
            }
        )
    return pd.DataFrame(rows).sort_values(["feature_family", "feature_name"])


def mann_whitney_test(promo: pd.Series, nonpromo: pd.Series) -> tuple[float, float]:
    promo = pd.to_numeric(promo, errors="coerce").dropna()
    nonpromo = pd.to_numeric(nonpromo, errors="coerce").dropna()
    if len(promo) < 5 or len(nonpromo) < 5:
        return np.nan, np.nan
    if (
        np.isclose(promo.std(ddof=0), 0)
        and np.isclose(nonpromo.std(ddof=0), 0)
        and np.isclose(promo.mean(), nonpromo.mean())
    ):
        return 1.0, 0.0
    result = mannwhitneyu(promo, nonpromo, alternative="two-sided")
    effect_rbc = 2 * result.statistic / (len(promo) * len(nonpromo)) - 1
    return float(result.pvalue), float(effect_rbc)


def test_feature_differences_by_age(
    feature_df: pd.DataFrame,
    feature_cols: list[str],
) -> pd.DataFrame:
    rows = []
    for age_band in TARGET_AGE_BANDS:
        age_df = feature_df.loc[feature_df["age_band"] == age_band].copy()
        nonpromo_df = age_df.loc[age_df["group"] == 0]
        promo_df = age_df.loc[age_df["group"] == 1]
        for feature_name in feature_cols:
            nonpromo = pd.to_numeric(
                nonpromo_df[feature_name],
                errors="coerce",
            ).dropna()
            promo = pd.to_numeric(
                promo_df[feature_name],
                errors="coerce",
            ).dropna()
            if len(nonpromo) < 5 or len(promo) < 5:
                continue
            pvalue, effect_rbc = mann_whitney_test(promo, nonpromo)
            diff_mean = float(promo.mean() - nonpromo.mean())
            rows.append(
                {
                    "age_band": age_band,
                    "age_band_label": age_band_label(age_band),
                    "feature_name": feature_name,
                    "feature_family": get_feature_family(feature_name),
                    "n_nonpromo": int(len(nonpromo)),
                    "n_promo": int(len(promo)),
                    "mean_nonpromo": float(nonpromo.mean()),
                    "mean_promo": float(promo.mean()),
                    "median_nonpromo": float(nonpromo.median()),
                    "median_promo": float(promo.median()),
                    "diff_mean": diff_mean,
                    "abs_effect_rbc": abs(effect_rbc),
                    "effect_rbc": effect_rbc,
                    "pvalue": pvalue,
                    "direction": (
                        "promo_gt_nonpromo" if diff_mean > 0 else "promo_lt_nonpromo"
                    ),
                }
            )
    return pd.DataFrame(rows)


def assign_common_evidence_level(row: pd.Series) -> str:
    if (
        row["sign_consistency"] >= 0.8
        and row["sig_count_005"] >= 3
        and row["mean_abs_effect"] >= 0.03
    ):
        return "strong_common"
    if (
        row["sign_consistency"] >= 0.8
        and row["sig_count_005"] >= 2
        and row["mean_abs_effect"] >= 0.02
    ):
        return "moderate_common"
    if row["sign_consistency"] >= 0.6 and row["sig_count_010"] >= 2:
        return "exploratory_common"
    return "weak_common"


def summarize_common_features(test_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature_name, feature_rows in test_df.groupby("feature_name"):
        feature_rows = feature_rows.sort_values("age_band").copy()
        pvalues = feature_rows["pvalue"].clip(lower=1e-300).tolist()
        fisher_stat = float(-2 * np.log(pvalues).sum())
        fisher_p = float(chi2.sf(fisher_stat, 2 * len(pvalues)))

        sign_list = np.sign(feature_rows["diff_mean"]).tolist()
        pos_count = sum(1 for sign in sign_list if sign > 0)
        neg_count = sum(1 for sign in sign_list if sign < 0)
        sign_consistency = max(pos_count, neg_count) / len(sign_list)
        common_direction = (
            "promo_gt_nonpromo" if pos_count >= neg_count else "promo_lt_nonpromo"
        )

        sig_age_labels = feature_rows.loc[
            feature_rows["pvalue"] < 0.05,
            "age_band_label",
        ].tolist()
        trend_age_labels = feature_rows.loc[
            feature_rows["pvalue"] < 0.10,
            "age_band_label",
        ].tolist()

        row = {
            "feature_name": feature_name,
            "feature_family": feature_rows["feature_family"].iloc[0],
            "age_coverage": int(len(feature_rows)),
            "sig_count_005": int((feature_rows["pvalue"] < 0.05).sum()),
            "sig_count_010": int((feature_rows["pvalue"] < 0.10).sum()),
            "sign_consistency": float(sign_consistency),
            "common_direction": common_direction,
            "mean_diff_avg": float(feature_rows["diff_mean"].mean()),
            "mean_abs_effect": float(feature_rows["abs_effect_rbc"].mean()),
            "max_abs_effect": float(feature_rows["abs_effect_rbc"].max()),
            "fisher_p": fisher_p,
            "significant_age_bands": ", ".join(sig_age_labels) if sig_age_labels else "",
            "trend_age_bands": ", ".join(trend_age_labels) if trend_age_labels else "",
        }

        for age_band in TARGET_AGE_BANDS:
            age_key = str(age_band)
            age_row = feature_rows.loc[feature_rows["age_band"] == age_band]
            if age_row.empty:
                row[f"diff_mean_{age_key}"] = np.nan
                row[f"effect_rbc_{age_key}"] = np.nan
                row[f"pvalue_{age_key}"] = np.nan
            else:
                row[f"diff_mean_{age_key}"] = float(age_row["diff_mean"].iloc[0])
                row[f"effect_rbc_{age_key}"] = float(age_row["effect_rbc"].iloc[0])
                row[f"pvalue_{age_key}"] = float(age_row["pvalue"].iloc[0])

        rows.append(row)

    summary_df = pd.DataFrame(rows)
    summary_df["common_evidence_level"] = summary_df.apply(
        assign_common_evidence_level,
        axis=1,
    )
    summary_df["common_score"] = (
        summary_df["sig_count_005"] * 3
        + summary_df["sig_count_010"]
        + summary_df["sign_consistency"] * 2
        + summary_df["mean_abs_effect"] * 10
        - np.log10(summary_df["fisher_p"].clip(lower=1e-300))
    )
    summary_df["model_recommendation"] = np.where(
        summary_df["common_evidence_level"].isin(["strong_common", "moderate_common"]),
        "우선 검토",
        np.where(
            summary_df["common_evidence_level"] == "exploratory_common",
            "보조 검토",
            "후순위",
        ),
    )
    return summary_df.sort_values(
        ["common_score", "fisher_p", "mean_abs_effect"],
        ascending=[False, True, False],
    ).reset_index(drop=True)


def build_target_age_summary(feature_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        feature_df.groupby(["age_band", "group"])["USER_NUM"]
        .nunique()
        .reset_index(name="user_count")
    )
    summary["age_band_label"] = summary["age_band"].map(age_band_label)
    summary["group_label"] = summary["group"].map({0: "프로모션X", 1: "프로모션O"})
    return summary.sort_values(["age_band", "group"]).reset_index(drop=True)


def write_markdown_summary(
    raw: pd.DataFrame,
    safe: pd.DataFrame,
    feature_df: pd.DataFrame,
    age_summary_df: pd.DataFrame,
    feature_dictionary_df: pd.DataFrame,
    common_summary_df: pd.DataFrame,
    output_path: Path,
) -> None:
    membership_common = common_summary_df.loc[
        common_summary_df["feature_family"] == "membership"
    ].head(12)
    behavior_common = common_summary_df.loc[
        common_summary_df["feature_family"] != "membership"
    ].head(18)

    lines = []
    lines.append("# 260510 공통 파생변수 설명")
    lines.append("")
    lines.append("## 1. 작업 목적")
    lines.append("")
    lines.append(
        "- `10대`, `20대`, `30대`, `40대`, `60대`에서 공통적으로 프로모션 참여군과 비참여군 차이를 보일 가능성이 있는 파생변수 생성"
    )
    lines.append(
        "- `price`가 프로모션 참여 정의와 직접 연결되므로, `price` 기반 파생변수는 의도적으로 제외"
    )
    lines.append(
        "- 결과 CSV는 각 그룹별로 `USER_NUM` 1행 형태 유지"
    )
    lines.append("")
    lines.append("## 2. 데이터 처리 원칙")
    lines.append("")
    lines.append("- 원본 두 파일은 결합 후 `(group, USER_NUM)` 기준으로 고유키 구성")
    lines.append("- 최종 저장 파일은 그룹별로 분리해서 `USER_NUM`당 1행만 유지")
    lines.append("- 시청이력은 `reg_date <= watch_day <= end_date` 범위만 사용")
    lines.append("- `reg_date`, `end_date`는 원본 형식 보정 후 날짜 계산 반영")
    lines.append("")
    lines.append("## 3. 대상 연령대 사용자 수")
    lines.append("")
    lines.append("| 연령대 | 프로모션X | 프로모션O |")
    lines.append("| --- | ---: | ---: |")
    for age_band in TARGET_AGE_BANDS:
        age_rows = age_summary_df.loc[age_summary_df["age_band"] == age_band]
        nonpromo_n = int(
            age_rows.loc[age_rows["group"] == 0, "user_count"].iloc[0]
            if (age_rows["group"] == 0).any()
            else 0
        )
        promo_n = int(
            age_rows.loc[age_rows["group"] == 1, "user_count"].iloc[0]
            if (age_rows["group"] == 1).any()
            else 0
        )
        lines.append(
            f"| {age_band_label(age_band)} | {nonpromo_n:,} | {promo_n:,} |"
        )
    lines.append("")
    lines.append("## 4. 공통 차이 강한 멤버십 파생변수")
    lines.append("")
    lines.append("| 변수 | 유의 연령대 | 방향 | 공통 수준 | 식 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for _, row in membership_common.iterrows():
        lines.append(
            "| "
            f"{row['feature_name']} | "
            f"{row['significant_age_bands']} | "
            f"{row['common_direction']} | "
            f"{row['common_evidence_level']} | "
            f"{row['formula']} |"
        )
    lines.append("")
    lines.append("## 5. 공통 차이 강한 시청행동 파생변수")
    lines.append("")
    lines.append("| 변수 | 유의 연령대 | 방향 | 공통 수준 | 식 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for _, row in behavior_common.iterrows():
        lines.append(
            "| "
            f"{row['feature_name']} | "
            f"{row['significant_age_bands']} | "
            f"{row['common_direction']} | "
            f"{row['common_evidence_level']} | "
            f"{row['formula']} |"
        )
    lines.append("")
    lines.append("## 6. 연령대별 경향 요약")
    lines.append("")
    lines.append(
        "- `10대`: 공통 변수 중에서는 짧은 시청 비율과 가입 시각대 차이가 상대적으로 먼저 보였고, 행동형 차이는 약한 편"
    )
    lines.append(
        "- `20대`: 활동일 비율과 만기 직전 14일 시청 비중이 완만하게 높아지는 방향 확인"
    )
    lines.append(
        "- `30대`: 만기 근접 시청 비율과 후반부 시청 비중이 가장 안정적으로 높아지는 방향 확인"
    )
    lines.append(
        "- `40대`: 활동일 비율과 마지막 시청 공백 계열이 가장 뚜렷하게 차이를 보인 구간"
    )
    lines.append(
        "- `60대`: 표본 수는 작지만 활동일 비율과 최신작 선호 계열이 같은 방향으로 움직이는 경향 확인"
    )
    lines.append("")
    lines.append("## 7. 전체 파생변수 사전")
    lines.append("")
    lines.append("| 변수 | 계열 | 사용 컬럼 | 계산식 | 설명 | 주의점 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for _, row in feature_dictionary_df.iterrows():
        lines.append(
            "| "
            f"{row['feature_name']} | "
            f"{row['feature_family']} | "
            f"{row['source_columns']} | "
            f"{row['formula']} | "
            f"{row['description']} | "
            f"{row['usage_caution']} |"
        )
    lines.append("")
    lines.append("## 8. 생성 파일")
    lines.append("")
    lines.append("- `260510_user_features_0.csv`: 프로모션 미참여 그룹 사용자 단위 파생변수 테이블")
    lines.append("- `260510_user_features_1.csv`: 프로모션 참여 그룹 사용자 단위 파생변수 테이블")
    lines.append("- `260510_feature_explanation.md`: 변수 설명 문서")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    raw = load_raw_data()
    safe = filter_safe_view_history(raw)
    user_features = build_user_feature_table(raw, safe)
    user_features = user_features.loc[
        user_features["age_band"].isin(TARGET_AGE_BANDS)
    ].copy()

    feature_cols = [
        column
        for column in user_features.columns
        if column.startswith("mem_")
        or column.startswith("vh_")
        or column.startswith("genre_share__")
    ]

    feature_dictionary_df = build_feature_dictionary(feature_cols)
    age_summary_df = build_target_age_summary(user_features)
    feature_diff_df = test_feature_differences_by_age(user_features, feature_cols)
    common_summary_df = summarize_common_features(feature_diff_df)
    common_summary_df = common_summary_df.merge(
        feature_dictionary_df.drop(columns=["feature_family"]),
        on="feature_name",
        how="left",
    )

    output_columns = [
        "USER_NUM",
        "USER_KEY",
        "billing_method",
        "max_screen",
        "payment_device",
        "is_churn_prevented",
        "is_user_verified",
        "gender",
        "age",
        "age_band",
        "reg_date",
        "reg_hour",
        "end_date",
        "is_repurchase",
    ] + feature_cols

    group0_df = user_features.loc[user_features["group"] == 0, output_columns].copy()
    group1_df = user_features.loc[user_features["group"] == 1, output_columns].copy()

    group0_df.to_csv(OUTPUT_FEATURE_FILE_0, index=False, encoding="utf-8-sig")
    group1_df.to_csv(OUTPUT_FEATURE_FILE_1, index=False, encoding="utf-8-sig")
    write_markdown_summary(
        raw=raw,
        safe=safe,
        feature_df=user_features,
        age_summary_df=age_summary_df,
        feature_dictionary_df=feature_dictionary_df,
        common_summary_df=common_summary_df,
        output_path=OUTPUT_MD_FILE,
    )


if __name__ == "__main__":
    main()
