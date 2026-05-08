from __future__ import annotations

import re
from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = Path(__file__).resolve().parent
FILE_MAP = {
    0: DATA_DIR / "260507_merged1_0.csv",
    1: DATA_DIR / "260507_merged1_1.csv",
}
ORIGINAL_COLUMNS = [
    "USER_NUM",
    "MOVIE_NUM",
    "watch_time(min)",
    "watch_day",
    "watch_seq",
    "movie_title",
    "genre",
    "country",
    "showTM",
    "ott_release_month",
    "USER_KEY",
    "product_code",
    "price",
    "billing_method",
    "max_screen",
    "is_promotion",
    "is_churn_prevented",
    "is_repurchase",
    "payment_device",
    "is_user_verified",
    "gender",
    "age",
    "reg_date",
    "reg_hour",
    "end_date",
]
AGE_BANDS = [20, 30, 50]
PRIORITY_EXCLUDE = {
    "vh_has_safe_watch",
    "vh_tenure_days",
}


def parse_show_minutes(value: object) -> float:
    if pd.isna(value):
        return np.nan
    numbers = re.findall(r"\d+", str(value))
    if not numbers:
        return np.nan
    numbers = [int(num) for num in numbers]
    if len(numbers) == 1:
        return float(numbers[0])
    return float(numbers[0] * 60 + numbers[1])


def norm_two_sided_p(z_value: float) -> float:
    return 2 * (0.5 * (1 - erf(abs(z_value) / sqrt(2))))


def effect_size(left: pd.Series, right: pd.Series) -> float:
    left_var = left.var(ddof=1)
    right_var = right.var(ddof=1)
    if pd.isna(left_var) or pd.isna(right_var) or (left_var + right_var) <= 0:
        return np.nan
    pooled_std = np.sqrt((left_var + right_var) / 2)
    if pooled_std == 0 or pd.isna(pooled_std):
        return np.nan
    return (left.mean() - right.mean()) / pooled_std


def entropy_from_counts(values: pd.Series) -> float:
    array = np.asarray(values, dtype=float)
    array = array[array > 0]
    if array.size == 0:
        return np.nan
    prob = array / array.sum()
    return float(-(prob * np.log(prob)).sum())


def add_key_columns(frame: pd.DataFrame, group_id: int) -> pd.DataFrame:
    data = frame.copy()
    data["group"] = group_id
    data["user_group_key"] = (
        data["group"].astype(str) + "_" + data["USER_NUM"].astype(str)
    )
    return data


def load_raw_data() -> pd.DataFrame:
    frames = []
    for group_id, file_path in FILE_MAP.items():
        frame = pd.read_csv(file_path)
        frames.append(add_key_columns(frame, group_id))
    raw = pd.concat(frames, ignore_index=True)
    raw["watch_date"] = pd.to_datetime(
        raw["watch_day"].astype(str), format="%Y%m%d", errors="coerce"
    )
    raw["reg_date_dt"] = pd.to_datetime(raw["reg_date"], errors="coerce")
    raw["end_date_dt"] = pd.to_datetime(raw["end_date"], errors="coerce")
    raw["show_minutes"] = raw["showTM"].map(parse_show_minutes)
    release_month = raw["ott_release_month"].dropna().astype(int).astype(str) + "01"
    raw.loc[release_month.index, "release_date"] = pd.to_datetime(
        release_month, format="%Y%m%d", errors="coerce"
    )
    raw["release_date"] = pd.to_datetime(raw["release_date"], errors="coerce")
    return raw


def classify_column_roles(raw: pd.DataFrame) -> pd.DataFrame:
    columns = ["group"] + ORIGINAL_COLUMNS
    results = []
    grouped = raw.groupby("user_group_key", dropna=False)

    for column in columns:
        if column in {"group", "USER_NUM"}:
            role = "key"
            max_nunique = 1
            users_with_variation = 0
        else:
            nunique_by_user = grouped[column].nunique(dropna=False)
            max_nunique = int(nunique_by_user.max())
            users_with_variation = int((nunique_by_user > 1).sum())
            role = "view_history" if max_nunique > 1 else "membership"
        results.append(
            {
                "column_name": column,
                "role": role,
                "max_nunique_within_user": max_nunique,
                "users_with_variation": users_with_variation,
            }
        )

    role_df = pd.DataFrame(results).sort_values(
        ["role", "max_nunique_within_user", "users_with_variation", "column_name"],
        ascending=[True, False, False, True],
    )
    return role_df.reset_index(drop=True)


def filter_modeling_window(raw: pd.DataFrame) -> pd.DataFrame:
    safe = raw.loc[
        (raw["watch_date"] >= raw["reg_date_dt"])
        & (raw["watch_date"] <= raw["end_date_dt"])
    ].copy()
    safe["tenure_days"] = (
        safe["end_date_dt"] - safe["reg_date_dt"]
    ).dt.days.clip(lower=1)
    safe["days_from_reg"] = (
        safe["watch_date"] - safe["reg_date_dt"]
    ).dt.days.clip(lower=0)
    safe["days_to_end"] = (safe["end_date_dt"] - safe["watch_date"]).dt.days.clip(
        lower=0
    )
    safe["weekday"] = safe["watch_date"].dt.weekday
    safe["is_weekend"] = safe["weekday"].isin([5, 6]).astype(int)
    safe["runtime_completion"] = (
        safe["watch_time(min)"] / safe["show_minutes"]
    ).clip(lower=0, upper=2)
    safe["content_age_days"] = (safe["watch_date"] - safe["release_date"]).dt.days
    safe["is_recent_release_180d"] = (
        (safe["content_age_days"] >= 0) & (safe["content_age_days"] <= 180)
    ).astype(float)
    safe["is_recent_release_365d"] = (
        (safe["content_age_days"] >= 0) & (safe["content_age_days"] <= 365)
    ).astype(float)
    safe["is_old_catalog_5y"] = (safe["content_age_days"] >= 365 * 5).astype(float)
    safe["is_short_sample"] = (safe["watch_time(min)"] <= 5).astype(int)
    safe["is_high_completion_event"] = (safe["runtime_completion"] >= 0.7).astype(
        float
    )
    safe["is_low_completion_event"] = (safe["runtime_completion"] <= 0.1).astype(
        float
    )
    return safe


def build_base_user_frame(raw: pd.DataFrame, safe: pd.DataFrame) -> pd.DataFrame:
    membership_cols = [
        "user_group_key",
        "group",
        "USER_NUM",
        "USER_KEY",
        "product_code",
        "price",
        "billing_method",
        "max_screen",
        "is_promotion",
        "is_churn_prevented",
        "is_repurchase",
        "payment_device",
        "is_user_verified",
        "gender",
        "age",
        "reg_date",
        "reg_hour",
        "end_date",
        "reg_date_dt",
        "end_date_dt",
    ]
    base = raw[membership_cols].drop_duplicates("user_group_key").copy()
    base["age_band"] = (base["age"] // 10 * 10).astype("Int64")
    base["vh_has_safe_watch"] = base["user_group_key"].isin(
        set(safe["user_group_key"])
    ).astype(int)
    return base


def build_general_aggregates(safe: pd.DataFrame) -> pd.DataFrame:
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
        vh_mean_runtime_min=("show_minutes", "mean"),
        vh_mean_event_completion=("runtime_completion", "mean"),
        vh_high_completion_event_ratio=("is_high_completion_event", "mean"),
        vh_low_completion_event_ratio=("is_low_completion_event", "mean"),
        vh_short_sample_ratio=("is_short_sample", "mean"),
        vh_recent_release_180d_ratio=("is_recent_release_180d", "mean"),
        vh_recent_release_365d_ratio=("is_recent_release_365d", "mean"),
        vh_old_catalog_5y_ratio=("is_old_catalog_5y", "mean"),
        vh_mean_content_age_days=("content_age_days", "mean"),
        vh_first_watch_lag=("days_from_reg", "min"),
        vh_last_watch_gap=("days_to_end", "min"),
    )
    return feature_df.reset_index()


def build_timing_features(safe: pd.DataFrame) -> pd.DataFrame:
    timing = safe.groupby("user_group_key").agg(
        first_watch=("watch_date", "min"),
        last_watch=("watch_date", "max"),
        reg_dt=("reg_date_dt", "min"),
        end_dt=("end_date_dt", "min"),
        active_days=("watch_date", "nunique"),
    )
    timing["vh_watch_span_days"] = (timing["last_watch"] - timing["first_watch"]).dt.days + 1
    timing["vh_tenure_days"] = (timing["end_dt"] - timing["reg_dt"]).dt.days.clip(
        lower=1
    )
    timing["vh_active_day_ratio"] = (
        timing["active_days"] / timing["vh_tenure_days"]
    )
    timing["vh_watch_span_ratio"] = (
        timing["vh_watch_span_days"] / timing["vh_tenure_days"]
    )
    timing["vh_first_watch_lag_ratio"] = (
        (timing["first_watch"] - timing["reg_dt"]).dt.days / timing["vh_tenure_days"]
    )
    timing["vh_last_watch_gap_ratio"] = (
        (timing["end_dt"] - timing["last_watch"]).dt.days / timing["vh_tenure_days"]
    )
    return timing[
        [
            "vh_watch_span_days",
            "vh_tenure_days",
            "vh_active_day_ratio",
            "vh_watch_span_ratio",
            "vh_first_watch_lag_ratio",
            "vh_last_watch_gap_ratio",
        ]
    ].reset_index()


def build_rate_features(feature_df: pd.DataFrame) -> pd.DataFrame:
    data = feature_df.copy()
    active_day = data["vh_active_day_count"].replace(0, np.nan)
    tenure_day = data["vh_tenure_days"].replace(0, np.nan)
    event_cnt = data["vh_event_count"].replace(0, np.nan)

    data["vh_events_per_active_day"] = data["vh_event_count"] / active_day
    data["vh_titles_per_active_day"] = data["vh_title_count"] / active_day
    data["vh_watch_min_per_active_day"] = data["vh_total_watch_min"] / active_day
    data["vh_event_per_tenure_day"] = data["vh_event_count"] / tenure_day
    data["vh_watch_min_per_tenure_day"] = data["vh_total_watch_min"] / tenure_day
    data["vh_rewatch_event_ratio"] = (
        data["vh_event_count"] - data["vh_title_count"]
    ) / event_cnt
    return data


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


def build_title_features(safe: pd.DataFrame) -> pd.DataFrame:
    title_df = safe.groupby(["user_group_key", "MOVIE_NUM"]).agg(
        title_watch_min=("watch_time(min)", "sum"),
        title_runtime_min=("show_minutes", "max"),
        title_event_count=("user_group_key", "size"),
    )
    title_df = title_df.reset_index()
    title_df = title_df.loc[
        title_df["title_runtime_min"].notna() & (title_df["title_runtime_min"] > 0)
    ].copy()
    title_df["title_completion"] = (
        title_df["title_watch_min"] / title_df["title_runtime_min"]
    ).clip(lower=0, upper=2)
    title_df["is_completed_title_50"] = (title_df["title_completion"] >= 0.5).astype(
        float
    )
    title_df["is_completed_title_80"] = (title_df["title_completion"] >= 0.8).astype(
        float
    )
    title_df["is_sampled_title_10"] = (title_df["title_completion"] <= 0.1).astype(
        float
    )
    title_total = title_df.groupby("user_group_key")["title_watch_min"].transform("sum")
    title_df["title_watch_share"] = title_df["title_watch_min"] / title_total

    features = title_df.groupby("user_group_key").agg(
        vh_mean_title_completion=("title_completion", "mean"),
        vh_completed_title_ratio_50=("is_completed_title_50", "mean"),
        vh_completed_title_ratio_80=("is_completed_title_80", "mean"),
        vh_sampled_title_ratio_10=("is_sampled_title_10", "mean"),
        vh_avg_events_per_title=("title_event_count", "mean"),
        vh_title_watch_hhi=("title_watch_share", lambda series: np.square(series).sum()),
    )
    return features.reset_index()


def build_period_ratio_features(safe: pd.DataFrame) -> pd.DataFrame:
    period = safe[
        [
            "user_group_key",
            "watch_time(min)",
            "days_from_reg",
            "days_to_end",
            "tenure_days",
        ]
    ].copy()
    period["elapsed_ratio"] = period["days_from_reg"] / period["tenure_days"]
    period["is_first_half"] = period["elapsed_ratio"] <= 0.5
    period["is_last_7d"] = period["days_to_end"] <= 7
    period["is_last_14d"] = period["days_to_end"] <= 14

    total = period.groupby("user_group_key")["watch_time(min)"].sum().rename(
        "total_watch_min"
    )
    first_half = (
        period.loc[period["is_first_half"]]
        .groupby("user_group_key")["watch_time(min)"]
        .sum()
        .rename("first_half_watch_min")
    )
    last_7d = (
        period.loc[period["is_last_7d"]]
        .groupby("user_group_key")["watch_time(min)"]
        .sum()
        .rename("last_7d_watch_min")
    )
    last_14d = (
        period.loc[period["is_last_14d"]]
        .groupby("user_group_key")["watch_time(min)"]
        .sum()
        .rename("last_14d_watch_min")
    )

    merged = pd.concat([total, first_half, last_7d, last_14d], axis=1).reset_index()
    for col in ["first_half_watch_min", "last_7d_watch_min", "last_14d_watch_min"]:
        merged[col] = merged[col].fillna(0)
    merged["vh_first_half_watch_ratio"] = (
        merged["first_half_watch_min"] / merged["total_watch_min"]
    )
    merged["vh_last_7d_watch_ratio"] = (
        merged["last_7d_watch_min"] / merged["total_watch_min"]
    )
    merged["vh_last_14d_watch_ratio"] = (
        merged["last_14d_watch_min"] / merged["total_watch_min"]
    )
    return merged[
        [
            "user_group_key",
            "vh_first_half_watch_ratio",
            "vh_last_7d_watch_ratio",
            "vh_last_14d_watch_ratio",
        ]
    ]


def build_genre_features(safe: pd.DataFrame) -> pd.DataFrame:
    genre_df = safe[["user_group_key", "genre", "watch_time(min)"]].copy()
    genre_df["genre_item"] = genre_df["genre"].fillna("").str.split(",")
    genre_df = genre_df.explode("genre_item")
    genre_df["genre_item"] = genre_df["genre_item"].str.strip()
    genre_df = genre_df.loc[genre_df["genre_item"] != ""].copy()

    grouped = genre_df.groupby(["user_group_key", "genre_item"]).agg(
        genre_watch_min=("watch_time(min)", "sum")
    )
    grouped = grouped.reset_index()

    stats = grouped.groupby("user_group_key").agg(
        vh_genre_unique_count=("genre_item", "nunique"),
        vh_genre_watch_entropy=("genre_watch_min", entropy_from_counts),
        vh_top_genre_share=("genre_watch_min", lambda series: series.max() / series.sum()),
    )
    stats = stats.reset_index()

    top_genres = genre_df["genre_item"].value_counts().head(10).index.tolist()
    total_watch = (
        grouped.groupby("user_group_key")["genre_watch_min"].sum().rename("genre_total")
    )
    grouped = grouped.merge(total_watch.reset_index(), on="user_group_key", how="left")

    share_frames = []
    for genre_name in top_genres:
        share_df = grouped.loc[grouped["genre_item"] == genre_name, [
            "user_group_key",
            "genre_watch_min",
            "genre_total",
        ]].copy()
        feature_name = f"genre_share__{genre_name}"
        share_df[feature_name] = share_df["genre_watch_min"] / share_df["genre_total"]
        share_frames.append(share_df[["user_group_key", feature_name]])

    if share_frames:
        pivot_df = share_frames[0]
        for share_df in share_frames[1:]:
            pivot_df = pivot_df.merge(share_df, on="user_group_key", how="outer")
    else:
        pivot_df = pd.DataFrame({"user_group_key": []})

    return stats.merge(pivot_df, on="user_group_key", how="left")


def build_country_features(safe: pd.DataFrame) -> pd.DataFrame:
    country_df = safe[["user_group_key", "country", "watch_time(min)"]].copy()
    country_df["country_item"] = country_df["country"].fillna("").str.split(",")
    country_df = country_df.explode("country_item")
    country_df["country_item"] = country_df["country_item"].str.strip()
    country_df = country_df.loc[country_df["country_item"] != ""].copy()

    grouped = country_df.groupby(["user_group_key", "country_item"]).agg(
        country_watch_min=("watch_time(min)", "sum")
    )
    grouped = grouped.reset_index()

    stats = grouped.groupby("user_group_key").agg(
        vh_country_unique_count=("country_item", "nunique"),
        vh_country_watch_entropy=("country_watch_min", entropy_from_counts),
        vh_top_country_share=("country_watch_min", lambda series: series.max() / series.sum()),
    )
    stats = stats.reset_index()

    top_countries = country_df["country_item"].value_counts().head(5).index.tolist()
    total_watch = (
        grouped.groupby("user_group_key")["country_watch_min"].sum().rename("country_total")
    )
    grouped = grouped.merge(total_watch.reset_index(), on="user_group_key", how="left")

    share_frames = []
    for country_name in top_countries:
        share_df = grouped.loc[grouped["country_item"] == country_name, [
            "user_group_key",
            "country_watch_min",
            "country_total",
        ]].copy()
        feature_name = f"country_share__{country_name}"
        share_df[feature_name] = share_df["country_watch_min"] / share_df["country_total"]
        share_frames.append(share_df[["user_group_key", feature_name]])

    if share_frames:
        pivot_df = share_frames[0]
        for share_df in share_frames[1:]:
            pivot_df = pivot_df.merge(share_df, on="user_group_key", how="outer")
    else:
        pivot_df = pd.DataFrame({"user_group_key": []})

    return stats.merge(pivot_df, on="user_group_key", how="left")


def build_user_feature_frame(raw: pd.DataFrame) -> pd.DataFrame:
    safe = filter_modeling_window(raw)
    base = build_base_user_frame(raw, safe)

    feature_parts = [
        build_general_aggregates(safe),
        build_timing_features(safe),
        build_daily_features(safe),
        build_gap_features(safe),
        build_title_features(safe),
        build_period_ratio_features(safe),
        build_genre_features(safe),
        build_country_features(safe),
    ]

    features = feature_parts[0]
    for part in feature_parts[1:]:
        features = features.merge(part, on="user_group_key", how="left")
    features = build_rate_features(features)

    user_df = base.merge(features, on="user_group_key", how="left")
    return user_df


def summarize_split_difference(
    user_df: pd.DataFrame,
    feature_cols: list[str],
    age_bands: list[int],
    split_col: str,
    left_value: int,
    right_value: int,
    left_label: str,
    right_label: str,
) -> pd.DataFrame:
    records = []

    for age_band in age_bands:
        age_slice = user_df.loc[user_df["age_band"] == age_band].copy()
        left_slice = age_slice.loc[age_slice[split_col] == left_value]
        right_slice = age_slice.loc[age_slice[split_col] == right_value]

        for feature in feature_cols:
            left_series = pd.to_numeric(left_slice[feature], errors="coerce").dropna()
            right_series = pd.to_numeric(right_slice[feature], errors="coerce").dropna()
            if len(left_series) < 20 or len(right_series) < 20:
                continue

            mean_left = left_series.mean()
            mean_right = right_series.mean()
            left_var = left_series.var(ddof=1)
            right_var = right_series.var(ddof=1)
            diff_value = mean_left - mean_right
            smd_value = effect_size(left_series, right_series)

            if pd.isna(left_var) or pd.isna(right_var):
                p_value = np.nan
            else:
                std_error = np.sqrt(left_var / len(left_series) + right_var / len(right_series))
                if std_error == 0 or pd.isna(std_error):
                    p_value = np.nan
                else:
                    z_value = diff_value / std_error
                    p_value = norm_two_sided_p(z_value)

            records.append(
                {
                    "age_band": age_band,
                    "feature": feature,
                    f"mean_{left_label}": mean_left,
                    f"mean_{right_label}": mean_right,
                    f"diff_{left_label}_minus_{right_label}": diff_value,
                    "smd": smd_value,
                    "abs_smd": abs(smd_value) if pd.notna(smd_value) else np.nan,
                    "p_value_approx": p_value,
                    f"n_{left_label}": len(left_series),
                    f"n_{right_label}": len(right_series),
                }
            )

    return pd.DataFrame(records)


def build_priority_table(
    group_diff: pd.DataFrame,
    churn_diff: pd.DataFrame,
) -> pd.DataFrame:
    group_rank = group_diff[["age_band", "feature", "abs_smd"]].rename(
        columns={"abs_smd": "group_abs_smd"}
    )
    churn_rank = churn_diff[["age_band", "feature", "abs_smd"]].rename(
        columns={"abs_smd": "churn_abs_smd"}
    )
    priority = group_rank.merge(churn_rank, on=["age_band", "feature"], how="inner")
    priority = priority.loc[~priority["feature"].isin(PRIORITY_EXCLUDE)].copy()
    priority["priority_score_sum"] = (
        priority["group_abs_smd"] + priority["churn_abs_smd"]
    )
    priority["priority_score_product"] = (
        priority["group_abs_smd"] * priority["churn_abs_smd"]
    )
    return priority.sort_values(
        ["age_band", "priority_score_sum", "priority_score_product"],
        ascending=[True, False, False],
    ).reset_index(drop=True)


def save_outputs(
    role_df: pd.DataFrame,
    user_df: pd.DataFrame,
    group_diff: pd.DataFrame,
    churn_diff: pd.DataFrame,
    priority_df: pd.DataFrame,
) -> None:
    role_df.to_csv(
        OUTPUT_DIR / "260507_column_role_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )
    user_df.to_csv(
        OUTPUT_DIR / "260507_user_features.csv",
        index=False,
        encoding="utf-8-sig",
    )
    group_diff.to_csv(
        OUTPUT_DIR / "260507_group_diff_by_age.csv",
        index=False,
        encoding="utf-8-sig",
    )
    churn_diff.to_csv(
        OUTPUT_DIR / "260507_churn_diff_by_age.csv",
        index=False,
        encoding="utf-8-sig",
    )
    priority_df.to_csv(
        OUTPUT_DIR / "260507_feature_priority_by_age.csv",
        index=False,
        encoding="utf-8-sig",
    )


def print_summary(
    raw: pd.DataFrame,
    role_df: pd.DataFrame,
    user_df: pd.DataFrame,
    priority_df: pd.DataFrame,
) -> None:
    membership_cols = role_df.loc[role_df["role"] == "membership", "column_name"].tolist()
    view_cols = role_df.loc[role_df["role"] == "view_history", "column_name"].tolist()

    print(f"raw_rows={len(raw):,}")
    print(f"unique_users={user_df['user_group_key'].nunique():,}")
    print(f"membership_columns={membership_cols}")
    print(f"view_history_columns={view_cols}")
    print()

    for age_band in AGE_BANDS:
        top_df = priority_df.loc[priority_df["age_band"] == age_band].head(10)
        print(f"age_band={age_band}")
        if top_df.empty:
            print("  no_features")
            continue
        print(
            top_df[
                [
                    "feature",
                    "group_abs_smd",
                    "churn_abs_smd",
                    "priority_score_sum",
                    "priority_score_product",
                ]
            ].to_string(index=False)
        )
        print()


def main() -> None:
    raw = load_raw_data()
    role_df = classify_column_roles(raw)
    user_df = build_user_feature_frame(raw)

    feature_cols = [
        col
        for col in user_df.columns
        if col.startswith("vh_")
        or col.startswith("genre_share__")
        or col.startswith("country_share__")
    ]

    group_diff = summarize_split_difference(
        user_df=user_df,
        feature_cols=feature_cols,
        age_bands=AGE_BANDS,
        split_col="group",
        left_value=1,
        right_value=0,
        left_label="group1",
        right_label="group0",
    )
    churn_diff = summarize_split_difference(
        user_df=user_df,
        feature_cols=feature_cols,
        age_bands=AGE_BANDS,
        split_col="is_repurchase",
        left_value=0,
        right_value=1,
        left_label="churn0",
        right_label="repurchase1",
    )
    priority_df = build_priority_table(group_diff, churn_diff)

    save_outputs(
        role_df=role_df,
        user_df=user_df,
        group_diff=group_diff,
        churn_diff=churn_diff,
        priority_df=priority_df,
    )
    print_summary(
        raw=raw,
        role_df=role_df,
        user_df=user_df,
        priority_df=priority_df,
    )


if __name__ == "__main__":
    main()
