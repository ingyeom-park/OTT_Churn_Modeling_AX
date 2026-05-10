from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests


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

MEMBERSHIP_COLUMNS = [
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

RECOMMENDED_FEATURE_SPECS = [
    {
        "age_band": 10,
        "base_feature": "vh_short_watch_ratio",
        "feature_name": "dv_age10_short_watch_ratio",
        "category": "age_interaction",
        "source_columns": "watch_time(min), watch_day, age",
        "aggregation_logic": "10대 여부 * 5분 이하 시청 비율",
        "why_it_may_help": "10대에서는 프로모션 참여군이 짧게 찍어보는 비율이 더 높게 나타나는 경향 반영",
    },
    {
        "age_band": 10,
        "base_feature": "vh_long_watch_ratio",
        "feature_name": "dv_age10_long_watch_ratio",
        "category": "age_interaction",
        "source_columns": "watch_time(min), watch_day, age",
        "aggregation_logic": "10대 여부 * 60분 이상 시청 비율",
        "why_it_may_help": "10대에서는 프로모션 참여군의 장시간 시청 비율이 낮아지는 방향 차이 반영",
    },
    {
        "age_band": 10,
        "base_feature": "genre_share__Romance",
        "feature_name": "dv_age10_romance_share",
        "category": "age_interaction",
        "source_columns": "genre, watch_time(min), age",
        "aggregation_logic": "10대 여부 * Romance 장르 시청시간 비중",
        "why_it_may_help": "10대 프로모션 참여군에서 로맨스 시청 비중이 높아지는 경향 반영",
    },
    {
        "age_band": 20,
        "base_feature": "vh_active_day_ratio",
        "feature_name": "dv_age20_active_day_ratio",
        "category": "age_interaction",
        "source_columns": "watch_day, reg_date, end_date, age",
        "aggregation_logic": "20대 여부 * 활동일 비율",
        "why_it_may_help": "20대 프로모션 참여군이 구독 기간 대비 더 자주 돌아오는 경향 반영",
    },
    {
        "age_band": 20,
        "base_feature": "vh_end_near_watch_ratio",
        "feature_name": "dv_age20_end_near_watch_ratio",
        "category": "age_interaction",
        "source_columns": "watch_day, reg_date, end_date, age",
        "aggregation_logic": "20대 여부 * 만기 근접 시청 비율",
        "why_it_may_help": "20대 프로모션 참여군이 만기 직전까지 시청을 이어가는 경향 반영",
    },
    {
        "age_band": 20,
        "base_feature": "vh_last_14d_watch_ratio",
        "feature_name": "dv_age20_last14d_watch_ratio",
        "category": "age_interaction",
        "source_columns": "watch_day, watch_time(min), end_date, age",
        "aggregation_logic": "20대 여부 * 만기 직전 14일 시청 비중",
        "why_it_may_help": "20대에서 프로모션 참여군이 후반부 사용 비중을 더 높게 가져가는지 반영",
    },
    {
        "age_band": 20,
        "base_feature": "vh_short_watch_ratio",
        "feature_name": "dv_age20_short_watch_ratio",
        "category": "age_interaction",
        "source_columns": "watch_time(min), age",
        "aggregation_logic": "20대 여부 * 5분 이하 시청 비율",
        "why_it_may_help": "20대에서 프로모션 참여군의 탐색형 짧은 시청 비중 차이 반영",
    },
    {
        "age_band": 20,
        "base_feature": "genre_share__Other",
        "feature_name": "dv_age20_other_genre_share",
        "category": "age_interaction",
        "source_columns": "genre, watch_time(min), age",
        "aggregation_logic": "20대 여부 * Other 장르 시청시간 비중",
        "why_it_may_help": "20대에서 비주류 장르 소비 비중 차이 반영",
    },
    {
        "age_band": 30,
        "base_feature": "vh_end_near_watch_ratio",
        "feature_name": "dv_age30_end_near_watch_ratio",
        "category": "age_interaction",
        "source_columns": "watch_day, reg_date, end_date, age",
        "aggregation_logic": "30대 여부 * 만기 근접 시청 비율",
        "why_it_may_help": "30대 프로모션 참여군이 만기 전까지 시청을 늦게까지 유지하는 패턴 반영",
    },
    {
        "age_band": 30,
        "base_feature": "vh_last_14d_watch_ratio",
        "feature_name": "dv_age30_last14d_watch_ratio",
        "category": "age_interaction",
        "source_columns": "watch_day, watch_time(min), end_date, age",
        "aggregation_logic": "30대 여부 * 만기 직전 14일 시청 비중",
        "why_it_may_help": "30대에서 후반부 시청 집중 차이 반영",
    },
    {
        "age_band": 30,
        "base_feature": "vh_week4_watch_ratio",
        "feature_name": "dv_age30_week4_watch_ratio",
        "category": "age_interaction",
        "source_columns": "watch_day, watch_time(min), reg_date, age",
        "aggregation_logic": "30대 여부 * 4주차 시청 비중",
        "why_it_may_help": "30대 프로모션 참여군이 구독 후반 주차에 시청을 더 배분하는 패턴 반영",
    },
    {
        "age_band": 30,
        "base_feature": "vh_late_ratio",
        "feature_name": "dv_age30_late_ratio",
        "category": "age_interaction",
        "source_columns": "watch_day, watch_time(min), reg_date, age",
        "aggregation_logic": "30대 여부 * 후반부 시청 비중",
        "why_it_may_help": "30대에서 초반보다 후반 사용이 늘어나는 프로모션 참여군 패턴 반영",
    },
    {
        "age_band": 30,
        "base_feature": "genre_share__Thriller_Crime",
        "feature_name": "dv_age30_thriller_crime_share",
        "category": "age_interaction",
        "source_columns": "genre, watch_time(min), age",
        "aggregation_logic": "30대 여부 * Thriller/Crime 장르 시청시간 비중",
        "why_it_may_help": "30대 프로모션 참여군의 장르 선호 차이 반영",
    },
    {
        "age_band": 40,
        "base_feature": "vh_active_day_ratio",
        "feature_name": "dv_age40_active_day_ratio",
        "category": "age_interaction",
        "source_columns": "watch_day, reg_date, end_date, age",
        "aggregation_logic": "40대 여부 * 활동일 비율",
        "why_it_may_help": "40대에서 가장 뚜렷한 차이를 보인 재방문 밀도 반영",
    },
    {
        "age_band": 40,
        "base_feature": "vh_end_near_watch_ratio",
        "feature_name": "dv_age40_end_near_watch_ratio",
        "category": "age_interaction",
        "source_columns": "watch_day, reg_date, end_date, age",
        "aggregation_logic": "40대 여부 * 만기 근접 시청 비율",
        "why_it_may_help": "40대 프로모션 참여군이 만기 직전까지 시청을 유지하는 패턴 반영",
    },
    {
        "age_band": 40,
        "base_feature": "vh_last_14d_watch_ratio",
        "feature_name": "dv_age40_last14d_watch_ratio",
        "category": "age_interaction",
        "source_columns": "watch_day, watch_time(min), end_date, age",
        "aggregation_logic": "40대 여부 * 만기 직전 14일 시청 비중",
        "why_it_may_help": "40대의 후반부 사용 차이 반영",
    },
    {
        "age_band": 40,
        "base_feature": "genre_share__Action_Adventure",
        "feature_name": "dv_age40_action_adventure_share",
        "category": "age_interaction",
        "source_columns": "genre, watch_time(min), age",
        "aggregation_logic": "40대 여부 * Action/Adventure 장르 시청시간 비중",
        "why_it_may_help": "40대 프로모션 참여군의 장르 선호 차이 반영",
    },
    {
        "age_band": 40,
        "base_feature": "vh_multi_event_day_ratio",
        "feature_name": "dv_age40_multi_event_day_ratio",
        "category": "age_interaction",
        "source_columns": "watch_day, watch_seq, age",
        "aggregation_logic": "40대 여부 * 하루 다중 시청일 비율",
        "why_it_may_help": "40대에서 집중 시청일 구조 차이 반영",
    },
    {
        "age_band": 60,
        "base_feature": "vh_recent_release_180d_ratio",
        "feature_name": "dv_age60_recent_release_180d_ratio",
        "category": "age_interaction",
        "source_columns": "ott_release_month, watch_day, age",
        "aggregation_logic": "60대 여부 * 최근 180일 공개작 시청 비중",
        "why_it_may_help": "60대 프로모션 참여군에서 최신작 선호 경향 반영",
    },
    {
        "age_band": 60,
        "base_feature": "vh_recent_release_365d_ratio",
        "feature_name": "dv_age60_recent_release_365d_ratio",
        "category": "age_interaction",
        "source_columns": "ott_release_month, watch_day, age",
        "aggregation_logic": "60대 여부 * 최근 365일 공개작 시청 비중",
        "why_it_may_help": "60대에서 최신 콘텐츠 소비 차이 반영",
    },
    {
        "age_band": 60,
        "base_feature": "vh_w3_to_w1_ratio_capped",
        "feature_name": "dv_age60_w3_to_w1_ratio_capped",
        "category": "age_interaction",
        "source_columns": "watch_day, watch_time(min), reg_date, age",
        "aggregation_logic": "60대 여부 * 3주차/1주차 시청시간 비율 capped",
        "why_it_may_help": "60대 프로모션 참여군에서 중반 시청 확장 패턴 반영",
    },
    {
        "age_band": 60,
        "base_feature": "vh_active_day_ratio",
        "feature_name": "dv_age60_active_day_ratio",
        "category": "age_interaction",
        "source_columns": "watch_day, reg_date, end_date, age",
        "aggregation_logic": "60대 여부 * 활동일 비율",
        "why_it_may_help": "60대 프로모션 참여군의 방문 빈도 차이 반영",
    },
]


@dataclass
class TestResult:
    age_band: int
    feature: str
    n_nonpromo: int
    n_promo: int
    mean_nonpromo: float
    mean_promo: float
    median_nonpromo: float
    median_promo: float
    diff_mean: float
    effect_rbc: float
    pvalue: float
    fdr_bh: float | None = None


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


def sanitize_genre_name(value: str) -> str:
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


def classify_column_roles(raw: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "group",
        "USER_NUM",
        "MOVIE_NUM",
        "watch_time(min)",
        "watch_day",
        "watch_seq",
        "movie_title",
        "ott_release_month",
        "genre",
    ] + MEMBERSHIP_COLUMNS

    grouped = raw.groupby("user_group_key", dropna=False)
    rows = []

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

        rows.append(
            {
                "column_name": column,
                "role": role,
                "max_nunique_within_user": max_nunique,
                "users_with_variation": users_with_variation,
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["role", "max_nunique_within_user", "users_with_variation", "column_name"],
        ascending=[True, False, False, True],
    )


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


def build_base_user_frame(raw: pd.DataFrame, safe: pd.DataFrame) -> pd.DataFrame:
    base_columns = [
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
        "payment_device",
        "is_user_verified",
        "gender",
        "age",
        "reg_date",
        "reg_hour",
        "end_date",
        "is_repurchase",
        "age_band",
        "reg_date_dt",
        "end_date_dt",
    ]

    base = raw[base_columns].drop_duplicates("user_group_key").copy()
    base["vh_has_safe_watch"] = base["user_group_key"].isin(
        set(safe["user_group_key"])
    ).astype(int)
    base["vh_tenure_days"] = (
        base["end_date_dt"] - base["reg_date_dt"]
    ).dt.days.clip(lower=1)
    return base


def build_general_features(safe: pd.DataFrame) -> pd.DataFrame:
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
    timing["vh_active_day_ratio"] = (
        timing["active_days"] / timing["tenure_days"].replace(0, np.nan)
    )
    timing["vh_watch_span_ratio"] = (
        timing["vh_watch_span_days"] / timing["tenure_days"].replace(0, np.nan)
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
        period_df[ratio_col] = (
            period_df[week_col] / period_df["total"].replace(0, np.nan)
        )

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

    total_nonzero = period_df["total"].replace(0, np.nan)
    period_df["vh_first_half_watch_ratio"] = (
        period_df["first_half_watch"] / total_nonzero
    )
    period_df["vh_last_7d_watch_ratio"] = period_df["last_7d_watch"] / total_nonzero
    period_df["vh_last_14d_watch_ratio"] = period_df["last_14d_watch"] / total_nonzero
    period_df["vh_front_loaded_ratio"] = (
        period_df["vh_week1_watch_min"] + period_df["vh_week2_watch_min"]
    ) / total_nonzero
    period_df["vh_late_ratio"] = (
        period_df["vh_week4_watch_min"] + period_df["vh_week5_watch_min"]
    ) / total_nonzero
    period_df["vh_w2_minus_w1_watch_min"] = (
        period_df["vh_week2_watch_min"] - period_df["vh_week1_watch_min"]
    )
    period_df["vh_w3_minus_w2_watch_min"] = (
        period_df["vh_week3_watch_min"] - period_df["vh_week2_watch_min"]
    )
    period_df["vh_w3_to_w1_ratio"] = (
        period_df["vh_week3_watch_min"]
        / period_df["vh_week1_watch_min"].replace(0, np.nan)
    )
    period_df["vh_w3_to_w1_ratio_capped"] = np.clip(
        period_df["vh_w3_to_w1_ratio"],
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
        "vh_w3_to_w1_ratio",
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
        f"genre_share__{sanitize_genre_name(column)}"
        for column in genre_share.columns
    ]
    genre_share = genre_share.reset_index()

    return stats.merge(genre_share, on="user_group_key", how="left")


def build_user_features(raw: pd.DataFrame, safe: pd.DataFrame) -> pd.DataFrame:
    base = build_base_user_frame(raw, safe)
    frames = [
        build_general_features(safe),
        build_timing_features(safe),
        build_daily_features(safe),
        build_gap_features(safe),
        build_period_features(safe),
        build_genre_features(safe),
    ]

    feature_df = base.copy()
    for frame in frames:
        feature_df = feature_df.merge(frame, on="user_group_key", how="left")

    feature_cols = [
        column
        for column in feature_df.columns
        if column.startswith("vh_") or column.startswith("genre_share__")
    ]

    for column in feature_cols:
        feature_df[column] = pd.to_numeric(feature_df[column], errors="coerce")

    zero_fill_cols = [
        column
        for column in feature_cols
        if column not in {"vh_mean_content_age_days", "vh_median_content_age_days"}
    ]
    feature_df[zero_fill_cols] = feature_df[zero_fill_cols].fillna(0)
    feature_df["vh_events_per_active_day"] = (
        feature_df["vh_event_count"]
        / feature_df["vh_active_day_count"].replace(0, np.nan)
    )
    feature_df["vh_titles_per_active_day"] = (
        feature_df["vh_title_count"]
        / feature_df["vh_active_day_count"].replace(0, np.nan)
    )
    feature_df["vh_watch_min_per_active_day"] = (
        feature_df["vh_total_watch_min"]
        / feature_df["vh_active_day_count"].replace(0, np.nan)
    )
    feature_df["vh_event_per_tenure_day"] = (
        feature_df["vh_event_count"] / feature_df["vh_tenure_days"].replace(0, np.nan)
    )
    feature_df["vh_watch_min_per_tenure_day"] = (
        feature_df["vh_total_watch_min"]
        / feature_df["vh_tenure_days"].replace(0, np.nan)
    )
    feature_df["vh_rewatch_event_ratio"] = (
        feature_df["vh_event_count"] - feature_df["vh_title_count"]
    ) / feature_df["vh_event_count"].replace(0, np.nan)
    feature_df["vh_end_near_watch_ratio"] = 1 - feature_df["vh_last_watch_gap_ratio"]

    numeric_cols = [
        "vh_events_per_active_day",
        "vh_titles_per_active_day",
        "vh_watch_min_per_active_day",
        "vh_event_per_tenure_day",
        "vh_watch_min_per_tenure_day",
        "vh_rewatch_event_ratio",
        "vh_end_near_watch_ratio",
    ]

    for column in numeric_cols:
        feature_df[column] = (
            pd.to_numeric(feature_df[column], errors="coerce")
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0)
        )

    feature_df["age_band_label"] = feature_df["age_band"].map(age_band_label)
    return feature_df


def build_age_interaction_features(feature_df: pd.DataFrame) -> pd.DataFrame:
    data = feature_df.copy()

    for spec in RECOMMENDED_FEATURE_SPECS:
        age_band = spec["age_band"]
        base_feature = spec["base_feature"]
        feature_name = spec["feature_name"]
        age_mask = (data["age_band"] == age_band).fillna(False).astype(int)
        data[feature_name] = age_mask * pd.to_numeric(
            data[base_feature],
            errors="coerce",
        ).fillna(0)

    return data


def mann_whitney_with_effect(
    promo: pd.Series,
    nonpromo: pd.Series,
) -> tuple[float, float]:
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
    rank_biserial = 2 * result.statistic / (len(promo) * len(nonpromo)) - 1
    return float(result.pvalue), float(rank_biserial)


def test_feature_differences_by_age(
    feature_df: pd.DataFrame,
    feature_cols: list[str],
) -> pd.DataFrame:
    rows: list[TestResult] = []

    for age_band in TARGET_AGE_BANDS:
        age_df = feature_df.loc[feature_df["age_band"] == age_band].copy()
        nonpromo_df = age_df.loc[age_df["group"] == 0]
        promo_df = age_df.loc[age_df["group"] == 1]

        for feature in feature_cols:
            nonpromo = pd.to_numeric(nonpromo_df[feature], errors="coerce").dropna()
            promo = pd.to_numeric(promo_df[feature], errors="coerce").dropna()
            if len(nonpromo) < 5 or len(promo) < 5:
                continue

            pvalue, effect = mann_whitney_with_effect(promo, nonpromo)
            rows.append(
                TestResult(
                    age_band=age_band,
                    feature=feature,
                    n_nonpromo=len(nonpromo),
                    n_promo=len(promo),
                    mean_nonpromo=float(nonpromo.mean()),
                    mean_promo=float(promo.mean()),
                    median_nonpromo=float(nonpromo.median()),
                    median_promo=float(promo.median()),
                    diff_mean=float(promo.mean() - nonpromo.mean()),
                    effect_rbc=effect,
                    pvalue=pvalue,
                )
            )

    result_df = pd.DataFrame([row.__dict__ for row in rows])
    if result_df.empty:
        return result_df

    result_df["age_band_label"] = result_df["age_band"].map(age_band_label)

    for age_band, index in result_df.groupby("age_band").groups.items():
        adjusted = multipletests(
            result_df.loc[index, "pvalue"].fillna(1.0),
            method="fdr_bh",
        )[1]
        result_df.loc[index, "fdr_bh"] = adjusted

    result_df["abs_effect"] = result_df["effect_rbc"].abs()
    result_df["direction"] = np.where(
        result_df["diff_mean"] > 0,
        "promo_gt_nonpromo",
        "promo_lt_nonpromo",
    )
    result_df = result_df.sort_values(
        ["age_band", "fdr_bh", "pvalue", "abs_effect"],
        ascending=[True, True, True, False],
    )
    return result_df.reset_index(drop=True)


def assign_evidence_level(row: pd.Series) -> str:
    if row["fdr_bh"] < 0.05 and abs(row["effect_rbc"]) >= 0.05:
        return "strong"
    if row["pvalue"] < 0.05 and abs(row["effect_rbc"]) >= 0.03:
        return "moderate"
    if row["pvalue"] < 0.10 and abs(row["effect_rbc"]) >= 0.05:
        return "exploratory"
    return "weak"


def build_priority_table(test_df: pd.DataFrame) -> pd.DataFrame:
    spec_df = pd.DataFrame(RECOMMENDED_FEATURE_SPECS)
    merged = spec_df.merge(
        test_df,
        left_on=["age_band", "base_feature"],
        right_on=["age_band", "feature"],
        how="left",
    )
    merged["age_band_label"] = merged["age_band"].map(age_band_label)
    merged["evidence_level"] = merged.apply(assign_evidence_level, axis=1)
    merged["recommended_usage"] = np.where(
        merged["evidence_level"].isin(["strong", "moderate"]),
        "모델 입력 권장",
        np.where(
            merged["evidence_level"] == "exploratory",
            "탐색 변수 권장",
            "보조 변수 권장",
        ),
    )
    merged["group_difference_summary"] = merged.apply(
        lambda row: (
            f"비프로모션 평균 {row['mean_nonpromo']:.4f}, "
            f"프로모션 평균 {row['mean_promo']:.4f}, "
            f"차이 {row['diff_mean']:+.4f}, "
            f"p={row['pvalue']:.4g}, "
            f"FDR={row['fdr_bh']:.4g}, "
            f"RBC={row['effect_rbc']:+.4f}"
        )
        if pd.notna(row["pvalue"])
        else "검정 정보 없음"
    , axis=1)
    return merged[
        [
            "age_band",
            "age_band_label",
            "base_feature",
            "feature_name",
            "category",
            "source_columns",
            "aggregation_logic",
            "why_it_may_help",
            "n_nonpromo",
            "n_promo",
            "mean_nonpromo",
            "mean_promo",
            "median_nonpromo",
            "median_promo",
            "diff_mean",
            "effect_rbc",
            "pvalue",
            "fdr_bh",
            "evidence_level",
            "recommended_usage",
            "group_difference_summary",
        ]
    ].sort_values(["age_band", "pvalue", "feature_name"])


def build_feature_dictionary(priority_df: pd.DataFrame) -> pd.DataFrame:
    dictionary = priority_df[
        [
            "feature_name",
            "category",
            "source_columns",
            "aggregation_logic",
            "why_it_may_help",
            "age_band_label",
            "evidence_level",
            "recommended_usage",
            "group_difference_summary",
        ]
    ].copy()
    dictionary = dictionary.rename(
        columns={
            "why_it_may_help": "description",
            "age_band_label": "age_focus",
        }
    )
    return dictionary.sort_values(["age_focus", "feature_name"]).reset_index(drop=True)


def build_age_sample_summary(feature_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        feature_df.groupby(["age_band", "group"])["USER_NUM"]
        .nunique()
        .reset_index(name="user_count")
    )
    summary["age_band_label"] = summary["age_band"].map(age_band_label)
    summary["group_label"] = summary["group"].map({0: "프로모션X", 1: "프로모션O"})
    return summary.sort_values(["age_band", "group"]).reset_index(drop=True)


def write_markdown_summary(
    feature_df: pd.DataFrame,
    safe: pd.DataFrame,
    priority_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_path: Path,
) -> None:
    total_users = feature_df["user_group_key"].nunique()
    total_rows = sum(len(pd.read_csv(path)) for path in FILE_MAP.values())
    safe_rows = len(safe)
    age_summary = build_age_sample_summary(feature_df)

    lines = []
    lines.append("# 260509 시청이력 기반 파생변수 제안")
    lines.append("")
    lines.append("## 1. 작업 목적")
    lines.append("")
    lines.append(
        "- 프로모션 미참여 그룹과 참여 그룹의 이탈 차이가 유의했던 `10대`, `20대`, `30대`, `40대`, `60대`를 대상으로 시청행동 기반 파생변수 후보 정리"
    )
    lines.append(
        "- 원본 시청 row를 `(group, USER_NUM)` 단위 1행으로 집계해서 모델 입력용 테이블 생성"
    )
    lines.append("")
    lines.append("## 2. 데이터 확인")
    lines.append("")
    lines.append(f"- 원본 row 수: `{total_rows:,}`")
    lines.append(f"- 사용자 단위 row 수: `{total_users:,}`")
    lines.append(f"- 안전한 구독 구간 내 시청 row 수: `{safe_rows:,}`")
    lines.append(
        "- `reg_date`, `end_date`는 문자열 형태가 뒤섞여 있어 해석 보정 후 사용"
    )
    lines.append("")
    lines.append("### 2.1 연령대별 사용자 수")
    lines.append("")
    lines.append("| 연령대 | 프로모션X | 프로모션O |")
    lines.append("| --- | ---: | ---: |")
    for age_band in TARGET_AGE_BANDS:
        age_rows = age_summary.loc[age_summary["age_band"] == age_band]
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
    lines.append("## 3. 집계 원칙")
    lines.append("")
    lines.append("- 멤버십 관련 컬럼은 사용자 내에서 변하지 않는 값으로 유지")
    lines.append("- 시청이력 관련 컬럼은 총량, 비율, 시점, 장르 선호 형태로 집계")
    lines.append("- 만기 직전 사용성, 활동일 비율, 주차별 사용 비중을 주요 후보로 우선 검토")
    lines.append("")
    lines.append("## 4. 연령대별 추천 파생변수")
    lines.append("")

    for age_band in TARGET_AGE_BANDS:
        age_priority = priority_df.loc[priority_df["age_band"] == age_band].copy()
        if age_priority.empty:
            continue

        lines.append(f"### 4.{TARGET_AGE_BANDS.index(age_band) + 1} {age_band_label(age_band)}")
        lines.append("")

        if age_band in {10, 60}:
            lines.append(
                "- 표본 수가 상대적으로 작아서 `exploratory` 성격 변수 비중이 큼"
            )
        else:
            lines.append(
                "- 아래 변수는 프로모션 그룹 간 평균 차이와 순위 기반 효과크기를 함께 확인한 후보"
            )
        lines.append("")
        lines.append("| 변수 | 의미 | 비프로모션 평균 | 프로모션 평균 | p-value | FDR | 효과크기(RBC) | 근거 수준 |")
        lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")

        for _, row in age_priority.iterrows():
            lines.append(
                "| "
                f"{row['feature_name']} | "
                f"{row['aggregation_logic']} | "
                f"{row['mean_nonpromo']:.4f} | "
                f"{row['mean_promo']:.4f} | "
                f"{row['pvalue']:.4g} | "
                f"{row['fdr_bh']:.4g} | "
                f"{row['effect_rbc']:+.4f} | "
                f"{row['evidence_level']} |"
            )

        lines.append("")
        for _, row in age_priority.iterrows():
            lines.append(
                f"- `{row['feature_name']}`: {row['description'] if 'description' in row else row['why_it_may_help']}"
            )
        lines.append("")

    strong_count = int(priority_df["evidence_level"].isin(["strong", "moderate"]).sum())
    exploratory_count = int((priority_df["evidence_level"] == "exploratory").sum())
    lines.append("## 5. 해석 요약")
    lines.append("")
    lines.append(
        f"- 강한 또는 중간 수준 근거 변수 수: `{strong_count}`"
    )
    lines.append(
        f"- 탐색 수준 변수 수: `{exploratory_count}`"
    )
    lines.append(
        "- 30대와 40대는 `만기 근접 시청`, `마지막 14일 시청 비중`, `활동일 비율` 계열이 가장 일관되게 차이를 보임"
    )
    lines.append(
        "- 20대는 차이가 있더라도 효과크기가 작아 보조 변수 또는 상호작용 변수로 쓰는 편이 안전"
    )
    lines.append(
        "- 60대는 `최신 공개작 선호`와 `중반 주차 확장` 패턴이 보이지만 표본 수가 작아 검증을 한 번 더 거치는 것이 좋음"
    )
    lines.append(
        "- 10대는 이탈 차이는 있었지만 시청행동 차이는 이번 파일 기준으로 뚜렷하지 않아 탐색 변수로만 권장"
    )
    lines.append("")
    lines.append("## 6. 생성 파일")
    lines.append("")
    lines.append("- `260509_user_features.csv`: 사용자 단위 집계 테이블")
    lines.append("- `260509_group_diff_by_age.csv`: 연령대별 그룹 차이 검정 전체 결과")
    lines.append("- `260509_feature_priority_by_age.csv`: 추천 파생변수 우선순위")
    lines.append("- `260509_feature_dictionary.csv`: 추천 변수 설명")
    lines.append("- `260509_column_role_summary.csv`: 사용자 내 고정/변동 컬럼 구분")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    raw = load_raw_data()
    safe = filter_safe_view_history(raw)
    column_role_df = classify_column_roles(raw)
    user_features = build_user_features(raw, safe)
    user_features = build_age_interaction_features(user_features)

    base_feature_cols = [
        column
        for column in user_features.columns
        if (
            column.startswith("vh_") or column.startswith("genre_share__")
        )
        and not column.startswith("dv_")
        and column not in {"vh_has_safe_watch", "vh_tenure_days"}
    ]

    test_df = test_feature_differences_by_age(user_features, base_feature_cols)
    priority_df = build_priority_table(test_df)
    feature_dictionary_df = build_feature_dictionary(priority_df)

    column_role_df.to_csv(
        OUTPUT_DIR / "260509_column_role_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )
    user_features.to_csv(
        OUTPUT_DIR / "260509_user_features.csv",
        index=False,
        encoding="utf-8-sig",
    )
    test_df.to_csv(
        OUTPUT_DIR / "260509_group_diff_by_age.csv",
        index=False,
        encoding="utf-8-sig",
    )
    priority_df.to_csv(
        OUTPUT_DIR / "260509_feature_priority_by_age.csv",
        index=False,
        encoding="utf-8-sig",
    )
    feature_dictionary_df.to_csv(
        OUTPUT_DIR / "260509_feature_dictionary.csv",
        index=False,
        encoding="utf-8-sig",
    )
    write_markdown_summary(
        feature_df=user_features,
        safe=safe,
        priority_df=priority_df,
        test_df=test_df,
        output_path=OUTPUT_DIR / "260509_feature_explanation.md",
    )


if __name__ == "__main__":
    main()
