from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from statsmodels.stats.outliers_influence import variance_inflation_factor


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "kim.kwangil" / "data"
DERIVED_DIR = PROJECT_DIR / "kim.kwangil" / "derived_variable"

RAW_FILE_MAP = {
    0: DATA_DIR / "260509_merged1_0.csv",
    1: DATA_DIR / "260509_merged1_1.csv",
}

CANDIDATE_FILE_MAP = {
    0: DERIVED_DIR / "260510_user_features_0.csv",
    1: DERIVED_DIR / "260510_user_features_1.csv",
}

OUTPUT_FILE_MAP = {
    0: DERIVED_DIR / "260512_derived_user_features_0.csv",
    1: DERIVED_DIR / "260512_derived_user_features_1.csv",
}

SUMMARY_FILE = DERIVED_DIR / "260512_derived_feature_summary.csv"
MD_FILE = DERIVED_DIR / "260512_derived_feature_explanation.md"

TARGET_AGE_BANDS = [10, 20, 30, 40, 60]
CORR_THRESHOLD = 0.65
VIF_THRESHOLD = 5.0

BASE_OUTPUT_COLUMNS = [
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
]

BASE_CANDIDATE_COLUMNS = {
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
    "group",
}

GENRE_LABEL_MAP = {
    "Action_Adventure": "Action_Adventure",
    "Animation_Family": "Animation_Family",
    "Comedy": "Comedy",
    "Documentary": "Documentary",
    "Drama": "Drama",
    "Historical_War": "Historical_War",
    "Horror": "Horror",
    "Other": "Other",
    "Romance": "Romance",
    "SF_Fantasy": "SF_Fantasy",
    "Thriller_Crime": "Thriller_Crime",
}


def age_band_label(age_band: int) -> str:
    return f"{int(age_band)}대"


def load_candidate_tables() -> tuple[pd.DataFrame, list[str]]:
    frames = []
    for group_id, file_path in CANDIDATE_FILE_MAP.items():
        frame = pd.read_csv(file_path)
        frame["group"] = group_id
        frames.append(frame)

    candidate_df = pd.concat(frames, ignore_index=True)
    candidate_df["age_band"] = pd.to_numeric(
        candidate_df["age_band"],
        errors="coerce",
    ).astype("Int64")

    derived_features = [
        column
        for column in candidate_df.columns
        if (
            column.startswith("mem_")
            or column.startswith("vh_")
            or column.startswith("genre_share__")
        )
        and column not in BASE_CANDIDATE_COLUMNS
        and pd.api.types.is_numeric_dtype(candidate_df[column])
    ]
    return candidate_df, derived_features


def prepare_feature_matrix(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    matrix = df[columns].copy()
    matrix = matrix.replace([np.inf, -np.inf], np.nan)
    for column in matrix.columns:
        matrix[column] = pd.to_numeric(matrix[column], errors="coerce")
        median_value = matrix[column].median()
        if pd.isna(median_value):
            median_value = 0.0
        matrix[column] = matrix[column].fillna(median_value)
    return matrix


def calculate_feature_scores(
    candidate_df: pd.DataFrame,
    derived_features: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    target_df = candidate_df.loc[
        candidate_df["age_band"].isin(TARGET_AGE_BANDS)
    ].copy()

    detail_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for feature_name in derived_features:
        series = target_df[feature_name]
        if series.dropna().nunique() <= 1:
            continue

        feature_detail_rows = []
        significant_age_bands = []
        significant_directions = []

        for age_band in TARGET_AGE_BANDS:
            sub = target_df.loc[
                target_df["age_band"] == age_band,
                ["group", feature_name],
            ].dropna()

            group_0 = sub.loc[sub["group"] == 0, feature_name]
            group_1 = sub.loc[sub["group"] == 1, feature_name]

            if len(group_0) < 10 or len(group_1) < 10:
                continue

            statistic, pvalue = mannwhitneyu(
                group_0,
                group_1,
                alternative="two-sided",
            )
            effect_rbc = (2 * statistic) / (len(group_0) * len(group_1)) - 1
            direction = (
                "promo_gt_nonpromo"
                if group_1.mean() > group_0.mean()
                else "promo_lt_nonpromo"
            )
            is_significant = int(pvalue < 0.05)

            row = {
                "feature_name": feature_name,
                "age_band": age_band,
                "age_band_label": age_band_label(age_band),
                "n_nonpromo": int(len(group_0)),
                "n_promo": int(len(group_1)),
                "mean_nonpromo": float(group_0.mean()),
                "mean_promo": float(group_1.mean()),
                "median_nonpromo": float(group_0.median()),
                "median_promo": float(group_1.median()),
                "pvalue": float(pvalue),
                "effect_rbc": float(effect_rbc),
                "abs_effect_rbc": float(abs(effect_rbc)),
                "direction": direction,
                "is_significant_05": is_significant,
            }
            detail_rows.append(row)
            feature_detail_rows.append(row)

            if is_significant:
                significant_age_bands.append(age_band_label(age_band))
                significant_directions.append(
                    f"{age_band_label(age_band)}:{direction}"
                )

        if not feature_detail_rows:
            continue

        summary_rows.append(
            {
                "feature_name": feature_name,
                "significant_age_count": len(significant_age_bands),
                "significant_age_bands": ", ".join(significant_age_bands),
                "direction_on_significant_bands": "; ".join(significant_directions),
                "min_pvalue": float(
                    min(row["pvalue"] for row in feature_detail_rows)
                ),
                "mean_abs_effect_rbc": float(
                    np.mean([row["abs_effect_rbc"] for row in feature_detail_rows])
                ),
                "max_abs_effect_rbc": float(
                    np.max([row["abs_effect_rbc"] for row in feature_detail_rows])
                ),
            }
        )

    detail_df = pd.DataFrame(detail_rows)
    summary_df = pd.DataFrame(summary_rows).sort_values(
        by=[
            "significant_age_count",
            "mean_abs_effect_rbc",
            "min_pvalue",
        ],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    return detail_df, summary_df


def calculate_centered_vif(df: pd.DataFrame) -> dict[str, float]:
    if df.shape[1] == 1:
        return {df.columns[0]: 1.0}

    working = df.copy()
    working = (working - working.mean()) / working.std(ddof=0).replace(0, 1)
    values = working.to_numpy(dtype=float)
    return {
        column: float(variance_inflation_factor(values, idx))
        for idx, column in enumerate(working.columns)
    }


def select_derived_features(
    candidate_df: pd.DataFrame,
    score_df: pd.DataFrame,
) -> list[str]:
    candidate_names = score_df.loc[
        score_df["significant_age_count"] >= 1,
        "feature_name",
    ].tolist()
    feature_matrix = prepare_feature_matrix(candidate_df, candidate_names)

    selected_features: list[str] = []

    for feature_name in candidate_names:
        trial_features = selected_features + [feature_name]
        trial_matrix = feature_matrix[trial_features].copy()

        corr_ok = True
        if len(trial_features) > 1:
            corr = trial_matrix.corr().abs()
            max_corr = corr.where(
                ~pd.DataFrame(
                    np.eye(len(trial_features), dtype=bool),
                    index=trial_features,
                    columns=trial_features,
                )
            ).max().max()
            if pd.notna(max_corr) and max_corr > CORR_THRESHOLD:
                corr_ok = False

        if not corr_ok:
            continue

        vif_ok = True
        vif_map = calculate_centered_vif(trial_matrix)
        if max(vif_map.values()) > VIF_THRESHOLD:
            vif_ok = False

        if vif_ok:
            selected_features.append(feature_name)

    return selected_features


def calculate_collinearity(
    candidate_df: pd.DataFrame,
    selected_features: list[str],
) -> pd.DataFrame:
    matrix = prepare_feature_matrix(candidate_df, selected_features)
    corr = matrix.corr().abs()
    vif_map = calculate_centered_vif(matrix)

    rows = []
    for feature_name in selected_features:
        other_corr = corr[feature_name].drop(index=feature_name)
        if other_corr.empty:
            max_corr = 0.0
            max_partner = ""
        else:
            max_corr = float(other_corr.max())
            max_partner = str(other_corr.idxmax())

        rows.append(
            {
                "feature_name": feature_name,
                "max_abs_corr_in_final_set": max_corr,
                "max_corr_partner": max_partner,
                "vif_centered": float(vif_map[feature_name]),
            }
        )

    return pd.DataFrame(rows)


def classify_feature_tier(
    significant_age_count: int,
    max_abs_effect_rbc: float,
) -> str:
    if significant_age_count >= 5:
        return "strong_common"
    if significant_age_count >= 4:
        return "common_core"
    if significant_age_count >= 3:
        return "common_support"
    if max_abs_effect_rbc >= 0.08:
        return "age_specific_strong"
    return "age_specific_exploratory"


def get_feature_domain(feature_name: str) -> str:
    if feature_name.startswith("mem_"):
        return "membership"
    return "view_history"


def get_feature_metadata(feature_name: str) -> dict[str, str]:
    billing_match = re.fullmatch(r"mem_billing_method_(\d+)_flag", feature_name)
    device_match = re.fullmatch(r"mem_device_([a-z]+)_flag", feature_name)
    genre_match = re.fullmatch(r"genre_share__([A-Za-z_]+)", feature_name)

    if feature_name == "mem_tenure_days":
        return {
            "source_columns": "reg_date, end_date",
            "formula": "mem_tenure_days = (end_date_dt - reg_date_dt).days",
            "short_description": "가입 시작일부터 종료일까지의 멤버십 유지 일수",
        }
    if feature_name == "mem_is_verified":
        return {
            "source_columns": "is_user_verified",
            "formula": "mem_is_verified = 1[is_user_verified = 1]",
            "short_description": "본인 인증 완료 여부",
        }
    if feature_name == "mem_is_churn_prevented_flag":
        return {
            "source_columns": "is_churn_prevented",
            "formula": "mem_is_churn_prevented_flag = 1[is_churn_prevented = 1]",
            "short_description": "이탈 방지 플래그 보유 여부",
        }
    if feature_name == "mem_is_male":
        return {
            "source_columns": "gender",
            "formula": "mem_is_male = 1[gender = 'M']",
            "short_description": "남성 사용자 여부",
        }
    if feature_name == "mem_reg_hour":
        return {
            "source_columns": "reg_hour",
            "formula": "mem_reg_hour = reg_hour",
            "short_description": "가입 시각 원값",
        }
    if feature_name == "mem_reg_weekday":
        return {
            "source_columns": "reg_date",
            "formula": "mem_reg_weekday = weekday(reg_date_dt)",
            "short_description": "가입 요일 숫자",
        }
    if feature_name == "mem_reg_hour_morning":
        return {
            "source_columns": "reg_hour",
            "formula": "mem_reg_hour_morning = 1[6 <= reg_hour <= 11]",
            "short_description": "오전 시간대 가입 여부",
        }
    if feature_name == "mem_reg_hour_afternoon":
        return {
            "source_columns": "reg_hour",
            "formula": "mem_reg_hour_afternoon = 1[12 <= reg_hour <= 17]",
            "short_description": "오후 시간대 가입 여부",
        }
    if feature_name == "mem_verified_premium_screen":
        return {
            "source_columns": "is_user_verified, max_screen",
            "formula": "mem_verified_premium_screen = 1[is_user_verified = 1] x 1[max_screen >= 4]",
            "short_description": "인증 완료와 프리미엄 동시 시청 옵션 동시 충족 여부",
        }
    if feature_name == "mem_verified_multi_screen":
        return {
            "source_columns": "is_user_verified, max_screen",
            "formula": "mem_verified_multi_screen = 1[is_user_verified = 1] x 1[max_screen >= 2]",
            "short_description": "인증 완료와 멀티 스크린 옵션 동시 충족 여부",
        }
    if billing_match:
        code = billing_match.group(1)
        return {
            "source_columns": "billing_method",
            "formula": f"{feature_name} = 1[billing_method = {code}]",
            "short_description": f"청구 방식 코드 {code} 사용 여부",
        }
    if device_match:
        device_name = device_match.group(1)
        return {
            "source_columns": "payment_device",
            "formula": f"{feature_name} = 1[payment_device = '{device_name}']",
            "short_description": f"{device_name} 기기 또는 채널 사용 여부",
        }
    if feature_name == "vh_active_day_ratio":
        return {
            "source_columns": "watch_day, reg_date, end_date",
            "formula": "vh_active_day_ratio = vh_active_day_count / mem_tenure_days",
            "short_description": "멤버십 기간 대비 실제 시청이 있었던 날짜 비율",
        }
    if feature_name == "vh_end_near_watch_ratio":
        return {
            "source_columns": "watch_day, reg_date, end_date",
            "formula": "vh_end_near_watch_ratio = 1 - vh_last_watch_gap_ratio",
            "short_description": "종료일에 가까운 시청 집중 정도",
        }
    if feature_name == "vh_gap_stability_index":
        return {
            "source_columns": "watch_day",
            "formula": "vh_gap_stability_index = 1 / (1 + vh_std_gap_days)",
            "short_description": "시청 간격의 안정성 지수",
        }
    if feature_name == "vh_last_14d_watch_ratio":
        return {
            "source_columns": "watch_day, watch_time(min), end_date",
            "formula": "vh_last_14d_watch_ratio = sum_i watch_time_i x 1[end_date_dt - watch_date_i <= 14] / sum_i watch_time_i",
            "short_description": "전체 시청 시간 중 종료 14일 이내 시청 비중",
        }
    if feature_name == "vh_short_watch_ratio":
        return {
            "source_columns": "watch_time(min)",
            "formula": "vh_short_watch_ratio = (1 / N) x sum_i 1[watch_time_i <= 5]",
            "short_description": "5분 이하 짧은 시청 이벤트 비중",
        }
    if feature_name == "vh_recent_release_180d_ratio":
        return {
            "source_columns": "watch_day, ott_release_month",
            "formula": "vh_recent_release_180d_ratio = (1 / N) x sum_i 1[0 <= (watch_date_i - release_date_i).days <= 180]",
            "short_description": "최근 180일 이내 공개 작품 시청 비중",
        }
    if feature_name == "vh_multi_event_day_ratio":
        return {
            "source_columns": "watch_day, watch_seq",
            "formula": "vh_multi_event_day_ratio = (1 / D) x sum_d 1[events(d) >= 2]",
            "short_description": "하루 2회 이상 시청한 날의 비중",
        }
    if feature_name == "vh_light_genre_share":
        return {
            "source_columns": "genre, watch_time(min)",
            "formula": "vh_light_genre_share = genre_share(Comedy) + genre_share(Animation_Family)",
            "short_description": "가벼운 오락 계열 장르 시청 비중",
        }
    if feature_name == "vh_nonfiction_genre_share":
        return {
            "source_columns": "genre, watch_time(min)",
            "formula": "vh_nonfiction_genre_share = genre_share(Documentary) + genre_share(Other)",
            "short_description": "논픽션 또는 비정형 장르 시청 비중",
        }
    if feature_name == "vh_tension_genre_share":
        return {
            "source_columns": "genre, watch_time(min)",
            "formula": "vh_tension_genre_share = genre_share(Thriller_Crime) + genre_share(Horror)",
            "short_description": "긴장감 계열 장르 시청 비중",
        }
    if feature_name == "vh_w3_to_w1_ratio_capped":
        return {
            "source_columns": "watch_day, watch_time(min), reg_date",
            "formula": "vh_w3_to_w1_ratio_capped = min(10, vh_week3_watch_min / vh_week1_watch_min)",
            "short_description": "3주차 대비 1주차 시청 강도 비율 상한값",
        }
    if feature_name == "vh_std_gap_days":
        return {
            "source_columns": "watch_day",
            "formula": "vh_std_gap_days = std(gap_days)",
            "short_description": "연속 시청일 사이 간격의 표준편차",
        }
    if feature_name == "vh_week4_watch_ratio":
        return {
            "source_columns": "watch_day, watch_time(min), reg_date",
            "formula": "vh_week4_watch_ratio = vh_week4_watch_min / vh_total_watch_min",
            "short_description": "전체 시청 시간 중 4주차 시청 비중",
        }
    if feature_name == "vh_week4_watch_min":
        return {
            "source_columns": "watch_day, watch_time(min), reg_date",
            "formula": "vh_week4_watch_min = sum_i watch_time_i x 1[week_index_i = 4]",
            "short_description": "가입 후 4주차 누적 시청 시간",
        }
    if feature_name == "vh_last_watch_gap_days":
        return {
            "source_columns": "watch_day, end_date",
            "formula": "vh_last_watch_gap_days = min_i (end_date_dt - watch_date_i).days",
            "short_description": "마지막 시청과 종료일 사이 최소 일수",
        }
    if genre_match:
        genre_name = genre_match.group(1)
        genre_label = GENRE_LABEL_MAP.get(genre_name, genre_name)
        return {
            "source_columns": "genre, watch_time(min)",
            "formula": f"{feature_name} = sum_i watch_time_i x 1[genre_i = {genre_label}] / sum_i watch_time_i",
            "short_description": f"{genre_label} 장르 시청 비중",
        }

    return {
        "source_columns": "",
        "formula": feature_name,
        "short_description": feature_name,
    }


def build_feature_summary(
    selected_features: list[str],
    score_df: pd.DataFrame,
    collinearity_df: pd.DataFrame,
) -> pd.DataFrame:
    summary_df = score_df.loc[
        score_df["feature_name"].isin(selected_features)
    ].copy()
    summary_df = summary_df.merge(
        collinearity_df,
        on="feature_name",
        how="left",
    )

    meta_rows = []
    for feature_name in selected_features:
        meta = get_feature_metadata(feature_name)
        score_row = summary_df.loc[
            summary_df["feature_name"] == feature_name
        ].iloc[0]
        meta_rows.append(
            {
                "feature_name": feature_name,
                "domain": get_feature_domain(feature_name),
                "source_columns": meta["source_columns"],
                "formula": meta["formula"],
                "short_description": meta["short_description"],
                "selection_tier": classify_feature_tier(
                    int(score_row["significant_age_count"]),
                    float(score_row["max_abs_effect_rbc"]),
                ),
            }
        )

    meta_df = pd.DataFrame(meta_rows)
    summary_df = meta_df.merge(summary_df, on="feature_name", how="left")
    summary_df = summary_df.sort_values(
        by=[
            "significant_age_count",
            "mean_abs_effect_rbc",
            "min_pvalue",
        ],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    return summary_df[
        [
            "feature_name",
            "domain",
            "selection_tier",
            "source_columns",
            "formula",
            "short_description",
            "significant_age_count",
            "significant_age_bands",
            "direction_on_significant_bands",
            "min_pvalue",
            "mean_abs_effect_rbc",
            "max_abs_effect_rbc",
            "max_abs_corr_in_final_set",
            "max_corr_partner",
            "vif_centered",
        ]
    ]


def load_original_base(raw_file: Path) -> pd.DataFrame:
    base = pd.read_csv(raw_file, usecols=BASE_OUTPUT_COLUMNS)
    base = base.drop_duplicates("USER_NUM").sort_values("USER_NUM").reset_index(drop=True)
    return base


def build_output_tables(selected_features: list[str]) -> dict[int, pd.DataFrame]:
    output_tables: dict[int, pd.DataFrame] = {}

    for group_id in [0, 1]:
        base_df = load_original_base(RAW_FILE_MAP[group_id])
        feature_df = pd.read_csv(
            CANDIDATE_FILE_MAP[group_id],
            usecols=["USER_NUM", *selected_features],
        )
        feature_df = feature_df.sort_values("USER_NUM").reset_index(drop=True)

        merged = base_df.merge(
            feature_df,
            on="USER_NUM",
            how="left",
            validate="one_to_one",
        )
        output_tables[group_id] = merged

    return output_tables


def build_markdown(
    selected_features: list[str],
    summary_df: pd.DataFrame,
    detail_df: pd.DataFrame,
    candidate_feature_count: int,
    output_tables: dict[int, pd.DataFrame],
) -> str:
    membership_count = sum(
        feature_name.startswith("mem_")
        for feature_name in selected_features
    )
    view_history_count = len(selected_features) - membership_count

    max_corr_row = summary_df.sort_values(
        by="max_abs_corr_in_final_set",
        ascending=False,
    ).iloc[0]
    max_vif_row = summary_df.sort_values(
        by="vif_centered",
        ascending=False,
    ).iloc[0]

    target_count_lines = []
    combined = pd.concat(
        [
            output_tables[0].assign(group=0),
            output_tables[1].assign(group=1),
        ],
        ignore_index=True,
    )
    for age_band in TARGET_AGE_BANDS:
        sub = combined.loc[(combined["age"] // 10 * 10) == age_band]
        count_nonpromo = int((sub["group"] == 0).sum())
        count_promo = int((sub["group"] == 1).sum())
        target_count_lines.append(
            f"| {age_band_label(age_band)} | {count_nonpromo:,} | {count_promo:,} |"
        )

    summary_lines = [
        "| 변수명 | 구분 | 선택 등급 | 유의 나이대 수 | 유의 나이대 | 최대 절대상관 | Centered VIF |",
        "| --- | --- | --- | ---: | --- | ---: | ---: |",
    ]
    for row in summary_df.itertuples(index=False):
        domain_label = "멤버십" if row.domain == "membership" else "시청 이력"
        summary_lines.append(
            f"| {row.feature_name} | {domain_label} | {row.selection_tier} | "
            f"{row.significant_age_count} | {row.significant_age_bands or '-'} | "
            f"{row.max_abs_corr_in_final_set:.3f} | {row.vif_centered:.3f} |"
        )

    detail_sections: list[str] = []
    for row in summary_df.itertuples(index=False):
        domain_label = "멤버십 관련 파생변수" if row.domain == "membership" else "시청 이력 관련 파생변수"
        detail_stats = detail_df.loc[
            detail_df["feature_name"] == row.feature_name
        ].sort_values("age_band")

        detail_lines = []
        for stat_row in detail_stats.itertuples(index=False):
            direction_label = (
                "프로모션 그룹 평균 > 비참여 그룹 평균"
                if stat_row.direction == "promo_gt_nonpromo"
                else "프로모션 그룹 평균 < 비참여 그룹 평균"
            )
            detail_lines.append(
                f"- {stat_row.age_band_label}: p={stat_row.pvalue:.6g}, "
                f"effect_rbc={stat_row.effect_rbc:.4f}, {direction_label}"
            )

        detail_sections.append(
            "\n".join(
                [
                    f"### {row.feature_name}",
                    f"- 분류: {domain_label}",
                    f"- 선택 등급: {row.selection_tier}",
                    f"- 사용 컬럼: `{row.source_columns}`",
                    f"- 수식: `{row.formula}`",
                    f"- 설명: {row.short_description}",
                    f"- 유의 나이대: {row.significant_age_bands or '없음'}",
                    f"- 최대 절대상관: {row.max_abs_corr_in_final_set:.3f} "
                    f"(상대 변수: {row.max_corr_partner})",
                    f"- Centered VIF: {row.vif_centered:.3f}",
                    "- 연령대별 검정 결과:",
                    *detail_lines,
                ]
            )
        )

    markdown = "\n".join(
        [
            "# 260512 파생변수 설명",
            "",
            "## 1. 작업 목적",
            "- `10대`, `20대`, `30대`, `40대`, `60대`에서 프로모션 참여 그룹과 비참여 그룹의 이탈률 차이를 설명할 수 있는 파생변수 재구성",
            "- 원본 멤버십 컬럼은 그대로 유지하고, 파생변수만 추가하는 구조로 재작성",
            "- 상관관계와 VIF 기준은 원본 변수가 아니라 최종 선택된 파생변수끼리만 점검",
            "",
            "## 2. 원본 유지 기준",
            "- 결과 CSV에는 `USER_NUM` 단위에서 값이 고정되는 원본 멤버십 컬럼을 그대로 유지",
            "- `watch_day`, `watch_time(min)`, `MOVIE_NUM`, `genre`처럼 같은 `USER_NUM` 안에서 여러 행으로 바뀌는 시청 이력 원본 컬럼은 1행 구조와 충돌하므로 그대로 둘 수 없고 파생변수로만 반영",
            "- 따라서 이번 결과는 `원본 멤버십 컬럼 + 시청 이력 요약 파생변수` 구조",
            "",
            "## 3. 데이터 처리 기준",
            "- 원본 파일: `260509_merged1_0.csv`, `260509_merged1_1.csv`",
            "- 파생변수 후보 풀: 기존 사용자 단위 후보 테이블 `260510_user_features_0.csv`, `260510_user_features_1.csv`",
            "- 후보 파생변수 수: "
            f"`{candidate_feature_count}`개",
            "- 선택 우선순위: `유의 나이대 수` 내림차순, `평균 절대 효과크기` 내림차순, `최소 p값` 오름차순",
            "- 파생변수 선별 기준: `pairwise |corr| <= 0.65`, `Centered VIF <= 5.0`",
            "",
            "## 4. 유의 나이대 사용자 수",
            "| 나이대 | 비참여 그룹 | 참여 그룹 |",
            "| --- | ---: | ---: |",
            *target_count_lines,
            "",
            "## 5. 최종 선택 결과",
            f"- 최종 선택 파생변수 수: `{len(selected_features)}`개",
            f"- 멤버십 파생변수 수: `{membership_count}`개",
            f"- 시청 이력 파생변수 수: `{view_history_count}`개",
            f"- 최종 파생변수 집합 최대 절대상관: "
            f"`{max_corr_row.feature_name}` vs `{max_corr_row.max_corr_partner}` = "
            f"`{max_corr_row.max_abs_corr_in_final_set:.3f}`",
            f"- 최종 파생변수 집합 최대 Centered VIF: "
            f"`{max_vif_row.feature_name}` = `{max_vif_row.vif_centered:.3f}`",
            "",
            "## 6. 최종 선택 변수 요약",
            *summary_lines,
            "",
            "## 7. 변수 상세 설명",
            *detail_sections,
            "",
            "## 8. 생성 파일",
            "- `260512_derived_user_features_0.csv`: 프로모션 비참여 그룹 사용자 단위 데이터",
            "- `260512_derived_user_features_1.csv`: 프로모션 참여 그룹 사용자 단위 데이터",
            "- `260512_derived_feature_summary.csv`: 파생변수 간략 설명 CSV",
            "- `260512_derived_feature_explanation.md`: 파생변수 상세 설명 문서",
        ]
    )
    return markdown + "\n"


def main() -> None:
    candidate_df, derived_features = load_candidate_tables()
    detail_df, score_df = calculate_feature_scores(candidate_df, derived_features)
    selected_features = select_derived_features(candidate_df, score_df)
    collinearity_df = calculate_collinearity(candidate_df, selected_features)
    summary_df = build_feature_summary(selected_features, score_df, collinearity_df)
    output_tables = build_output_tables(selected_features)

    for group_id, output_table in output_tables.items():
        output_table.to_csv(
            OUTPUT_FILE_MAP[group_id],
            index=False,
            encoding="utf-8-sig",
        )

    summary_df.to_csv(SUMMARY_FILE, index=False, encoding="utf-8-sig")

    markdown = build_markdown(
        selected_features=selected_features,
        summary_df=summary_df,
        detail_df=detail_df,
        candidate_feature_count=len(derived_features),
        output_tables=output_tables,
    )
    MD_FILE.write_text(markdown, encoding="utf-8-sig")

    print(f"candidate_feature_count={len(derived_features)}")
    print(f"selected_feature_count={len(selected_features)}")
    print(f"max_corr={summary_df['max_abs_corr_in_final_set'].max():.6f}")
    print(f"max_vif={summary_df['vif_centered'].max():.6f}")
    for group_id, output_table in output_tables.items():
        duplicate_count = int(output_table["USER_NUM"].duplicated().sum())
        print(
            f"group={group_id}, rows={len(output_table)}, "
            f"unique_users={output_table['USER_NUM'].nunique()}, "
            f"duplicated_user_num={duplicate_count}"
        )


if __name__ == "__main__":
    main()
