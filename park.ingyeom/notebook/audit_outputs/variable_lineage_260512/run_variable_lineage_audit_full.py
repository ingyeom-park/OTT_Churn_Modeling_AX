# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "park.ingyeom" / "data"
OUTPUT_DIR = Path(__file__).resolve().parent

FILES = {
    "master": DATA_DIR / "260512_derived_merged.csv",
    "membership": DATA_DIR / "Membership_v2.csv",
    "mapping": DATA_DIR / "User_Mapping_v2.csv",
    "view": DATA_DIR / "View_History_v2.csv",
    "movie": DATA_DIR / "Movie_Master_v2.csv",
    "v3": DATA_DIR / "변수_합집합_비교_v3.xlsx - v3_최종변수 (1).csv",
}

TOLERANCES = [1e-6, 1e-4, 1e-3]
DEFAULT_TOL = 1e-6
KEY = "USER_KEY"
USER_NUM = "USER_NUM"
WATCH_TIME = "watch_time(min)"

RUN_LOG: list[str] = []
CHECK_ROWS: list[dict] = []


def log(message: str = "") -> None:
    RUN_LOG.append(str(message))


def fail(message: str) -> None:
    raise RuntimeError(message)


def ensure_input_files() -> None:
    missing = [str(path) for path in FILES.values() if not path.exists()]
    if missing:
        fail("Required input file(s) missing. Missing: " + " | ".join(missing))
    log("> Input File Verification")
    for label, path in FILES.items():
        log(f"- {label}: {path}")


def read_csv_checked(path: Path) -> tuple[pd.DataFrame, str]:
    failures: list[str] = []
    for encoding in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            df = pd.read_csv(path, encoding=encoding)
            return df, encoding
        except UnicodeDecodeError as exc:
            failures.append(f"{encoding}: {exc}")
    fail(f"Could not read CSV with tested encodings: {path}. Failures: {failures}")


def as_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.normalize()


def as_watch_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series.astype("Int64").astype(str), format="%Y%m%d", errors="coerce").dt.normalize()


def format_value(value) -> str:
    if pd.isna(value):
        return "NaN"
    text = str(value)
    if len(text) > 60:
        return text[:57] + "..."
    return text


def sample_list(values, limit: int = 10) -> str:
    out = []
    for value in list(values)[:limit]:
        out.append(format_value(value))
    return "; ".join(out)


def safe_div(numerator, denominator, zero_policy: str = "zero"):
    numerator = pd.Series(numerator).astype(float)
    denominator = pd.Series(denominator).astype(float)
    result = numerator / denominator.replace(0, np.nan)
    if zero_policy == "zero":
        result = result.fillna(0.0)
    return result


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    values = pd.to_numeric(values, errors="coerce")
    weights = pd.to_numeric(weights, errors="coerce")
    valid = values.notna() & weights.notna()
    if not valid.any() or weights[valid].sum() == 0:
        return 0.0
    return float(np.average(values[valid], weights=weights[valid]))


def add_check(
    master: pd.DataFrame,
    variable: str,
    candidate: pd.Series,
    candidate_formula_id: str,
    candidate_formula_description: str,
    source_files_used: list[str],
    source_columns_used: list[str],
    join_key: str = KEY,
    date_basis: str = "",
    observation_window: str = "",
    denominator: str = "",
    zero_denominator_policy: str = "",
    missing_policy: str = "both NaN treated as match",
    tolerance: float = DEFAULT_TOL,
    null_match_handling: str = "both_nan_match",
    note: str = "",
) -> None:
    if variable not in master.columns:
        return

    cand = candidate.copy()
    cand.name = "__candidate__"
    cand_df = cand.reset_index()
    if cand_df.columns[0] != join_key:
        cand_df = cand_df.rename(columns={cand_df.columns[0]: join_key})

    if variable == join_key:
        left_df = pd.DataFrame({join_key: master[join_key], "__master_value__": master[variable]})
        master_value_col = "__master_value__"
    else:
        left_df = master[[join_key, variable]].copy()
        master_value_col = variable
    comp = left_df.merge(cand_df, on=join_key, how="left")
    left = comp[master_value_col]
    right = comp["__candidate__"]

    left_num = pd.to_numeric(left, errors="coerce")
    right_num = pd.to_numeric(right, errors="coerce")
    numeric_left_ok = left.dropna().shape[0] == left_num.dropna().shape[0]
    numeric_right_ok = right.dropna().shape[0] == right_num.dropna().shape[0]
    numeric_compare = numeric_left_ok and numeric_right_ok

    both_nan = left.isna() & right.isna()
    if numeric_compare:
        diff = (left_num - right_num).abs()
        matched = both_nan | diff.le(tolerance)
        max_abs_diff = float(diff[~both_nan].max()) if (~both_nan).any() and diff[~both_nan].notna().any() else 0.0
        mean_abs_diff = float(diff[~both_nan].mean()) if (~both_nan).any() and diff[~both_nan].notna().any() else 0.0
    else:
        matched = both_nan | (left.astype("string") == right.astype("string"))
        max_abs_diff = np.nan
        mean_abs_diff = np.nan

    compared_rows = int(len(comp))
    matched_rows = int(matched.sum())
    mismatched_rows = int(compared_rows - matched_rows)
    match_rate = matched_rows / compared_rows if compared_rows else np.nan

    mismatch_samples = []
    for _, row in comp.loc[~matched, [join_key, master_value_col, "__candidate__"]].head(3).iterrows():
        mismatch_samples.append(
            f"{join_key}={format_value(row[join_key])}, master={format_value(row[master_value_col])}, candidate={format_value(row['__candidate__'])}"
        )
    match_samples = []
    for _, row in comp.loc[matched, [join_key, master_value_col, "__candidate__"]].head(3).iterrows():
        match_samples.append(
            f"{join_key}={format_value(row[join_key])}, value={format_value(row[master_value_col])}"
        )

    CHECK_ROWS.append(
        {
            "variable": variable,
            "candidate_formula_id": candidate_formula_id,
            "candidate_formula_description": candidate_formula_description,
            "source_files_used": "; ".join(source_files_used),
            "source_columns_used": "; ".join(source_columns_used),
            "join_key": join_key,
            "date_basis": date_basis,
            "observation_window": observation_window,
            "denominator": denominator,
            "zero_denominator_policy": zero_denominator_policy,
            "missing_policy": missing_policy,
            "compared_rows": compared_rows,
            "matched_rows": matched_rows,
            "mismatched_rows": mismatched_rows,
            "match_rate": match_rate,
            "max_abs_diff": max_abs_diff,
            "mean_abs_diff": mean_abs_diff,
            "sample_mismatch_1": mismatch_samples[0] if len(mismatch_samples) > 0 else "",
            "sample_mismatch_2": mismatch_samples[1] if len(mismatch_samples) > 1 else "",
            "sample_mismatch_3": mismatch_samples[2] if len(mismatch_samples) > 2 else "",
            "sample_matches": " | ".join(match_samples),
            "sample_mismatches": " | ".join(mismatch_samples),
            "selected_candidate": False,
            "selected_as_best_candidate": False,
            "confidence_level": "",
            "null_match_handling": null_match_handling,
            "reason": "",
            "note": note,
        }
    )


def profile_dataframe(label: str, filename: str, df: pd.DataFrame, encoding: str) -> dict:
    key_cols = [col for col in [KEY, USER_NUM, "MOVIE_NUM"] if col in df.columns]
    key_unique = {col: int(df[col].nunique(dropna=True)) for col in key_cols}
    null_counts = df.isna().sum().to_dict()
    exact_duplicate_count = int(df.duplicated().sum())
    profile = {
        "label": label,
        "filename": filename,
        "loaded": True,
        "encoding": encoding,
        "row_count": int(len(df)),
        "column_count": int(df.shape[1]),
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "null_counts": null_counts,
        "key_unique_counts": key_unique,
        "duplicate_row_count": exact_duplicate_count,
        "exact_duplicate_count": exact_duplicate_count,
    }
    log(f"\n> File Profile: {filename}")
    log(f"- load_success: True")
    log(f"- encoding: {encoding}")
    log(f"- rows: {len(df)}")
    log(f"- columns: {df.shape[1]}")
    log(f"- column_names: {list(df.columns)}")
    log(f"- dtypes: {profile['dtypes']}")
    log(f"- null_counts: {null_counts}")
    log(f"- key_unique_counts: {key_unique}")
    log(f"- duplicate_row_count: {exact_duplicate_count}")
    log(f"- exact_duplicate_count: {exact_duplicate_count}")
    return profile


def value_counts_text(series: pd.Series, limit: int = 20) -> str:
    counts = series.value_counts(dropna=False).head(limit)
    return "; ".join([f"{format_value(idx)}={int(val)}" for idx, val in counts.items()])


def add_specific_profiles(
    master: pd.DataFrame,
    membership: pd.DataFrame,
    mapping: pd.DataFrame,
    view: pd.DataFrame,
    movie: pd.DataFrame,
) -> None:
    log("\n> Required Detailed Checks")
    reg = as_date(membership["reg_date"])
    end = as_date(membership["end_date"])
    log("[Membership_v2.csv]")
    log(f"- row_count: {len(membership)}")
    log(f"- USER_KEY_unique_count: {membership[KEY].nunique(dropna=True)}")
    log(f"- reg_date_range: {reg.min()} to {reg.max()}")
    log(f"- end_date_range: {end.min()} to {end.max()}")
    for col in ["is_repurchase", "gender", "age", "max_screen", "payment_device", "product_code", "billing_method"]:
        log(f"- {col}_distribution: {value_counts_text(membership[col])}")

    log("[User_Mapping_v2.csv]")
    log(f"- row_count: {len(mapping)}")
    log(f"- USER_KEY_unique_count: {mapping[KEY].nunique(dropna=True)}")
    log(f"- USER_NUM_unique_count: {mapping[USER_NUM].nunique(dropna=True)}")
    log(f"- duplicated_USER_KEY_rows: {int(mapping.duplicated(KEY).sum())}")
    log(f"- duplicated_USER_NUM_rows: {int(mapping.duplicated(USER_NUM).sum())}")
    log(f"- USER_KEY_with_multiple_USER_NUM: {int(mapping.groupby(KEY)[USER_NUM].nunique().gt(1).sum())}")
    log(f"- USER_NUM_with_multiple_USER_KEY: {int(mapping.groupby(USER_NUM)[KEY].nunique().gt(1).sum())}")

    watch_date = as_watch_date(view["watch_day"])
    log("[View_History_v2.csv]")
    log(f"- row_count: {len(view)}")
    log(f"- USER_NUM_unique_count: {view[USER_NUM].nunique(dropna=True)}")
    log(f"- MOVIE_NUM_unique_count: {view['MOVIE_NUM'].nunique(dropna=True)}")
    log(f"- watch_day_range: {watch_date.min()} to {watch_date.max()}")
    log(
        f"- watch_time(min)_min_max_mean_null: {view[WATCH_TIME].min()}, {view[WATCH_TIME].max()}, {view[WATCH_TIME].mean()}, {view[WATCH_TIME].isna().sum()}"
    )
    log(f"- watch_seq_min_max_null: {view['watch_seq'].min()}, {view['watch_seq'].max()}, {view['watch_seq'].isna().sum()}")
    log(f"- USER_NUM_not_in_mapping_count: {len(set(view[USER_NUM].dropna()) - set(mapping[USER_NUM].dropna()))}")

    release = pd.to_datetime(movie["ott_release_month"].astype("Int64").astype(str) + "01", format="%Y%m%d", errors="coerce")
    log("[Movie_Master_v2.csv]")
    log(f"- row_count: {len(movie)}")
    log(f"- MOVIE_NUM_unique_count: {movie['MOVIE_NUM'].nunique(dropna=True)}")
    log(f"- duplicated_MOVIE_NUM_rows: {int(movie.duplicated('MOVIE_NUM').sum())}")
    log(f"- exact_duplicate_count: {int(movie.duplicated().sum())}")
    log(f"- ott_release_month_range: {release.min()} to {release.max()}")
    log(f"- category_distribution: {value_counts_text(movie['category'])}")
    log(f"- View_MOVIE_NUM_not_in_Movie_Master_count: {len(set(view['MOVIE_NUM'].dropna()) - set(movie['MOVIE_NUM'].dropna()))}")

    log("[260512_derived_merged.csv]")
    log(f"- row_count: {len(master)}")
    log(f"- column_count: {master.shape[1]}")
    log(f"- USER_KEY_exists: {KEY in master.columns}")
    log(f"- USER_NUM_exists: {USER_NUM in master.columns}")
    log(f"- is_repurchase_exists: {'is_repurchase' in master.columns}")
    log(f"- columns: {list(master.columns)}")


def make_key_integrity_audit(master, membership, mapping, view, movie) -> pd.DataFrame:
    rows: list[dict] = []

    def add(check_name, result, expected, actual, issue_keys, severity, note):
        rows.append(
            {
                "check_name": check_name,
                "result": result,
                "expected": expected,
                "actual": actual,
                "issue_count": len(issue_keys) if not isinstance(issue_keys, int) else issue_keys,
                "sample_keys": sample_list(issue_keys if not isinstance(issue_keys, int) else [], 10),
                "severity": severity,
                "note": note,
            }
        )

    master_keys = set(master[KEY].dropna())
    membership_keys = set(membership[KEY].dropna())
    mapping_keys = set(mapping[KEY].dropna())
    master_user_nums = set(pd.to_numeric(master[USER_NUM], errors="coerce").dropna().astype(int))
    mapping_user_nums = set(mapping[USER_NUM].dropna().astype(int))
    view_user_nums = set(view[USER_NUM].dropna().astype(int))
    view_movie_nums = set(view["MOVIE_NUM"].dropna().astype(int))
    movie_nums = set(movie["MOVIE_NUM"].dropna().astype(int))

    missing = master_keys - membership_keys
    add(
        "master USER_KEY coverage in Membership_v2",
        "PASS" if not missing else "FAIL",
        "all master USER_KEY values exist in Membership_v2.csv",
        f"missing={len(missing)}",
        missing,
        "OK" if not missing else "CRITICAL",
        "USER_KEY is the primary comparison key for membership-derived variables.",
    )

    missing = membership_keys - master_keys
    add(
        "Membership_v2 USER_KEY coverage in master",
        "PASS" if not missing else "FAIL",
        "all Membership_v2 USER_KEY values exist in master",
        f"missing={len(missing)}",
        missing,
        "OK" if not missing else "HIGH",
        "Membership rows not represented in master would block full lineage reconstruction.",
    )

    missing = membership_keys - mapping_keys
    add(
        "Membership_v2 USER_KEY coverage in User_Mapping_v2",
        "PASS" if not missing else "FAIL",
        "all Membership_v2 USER_KEY values exist in User_Mapping_v2.csv",
        f"missing={len(missing)}",
        missing,
        "OK" if not missing else "HIGH",
        "Missing mapping rows affect view-history reconstruction.",
    )

    missing = master_user_nums - mapping_user_nums
    add(
        "master USER_NUM coverage in User_Mapping_v2",
        "PASS" if not missing else "FAIL",
        "all non-null master USER_NUM values exist in User_Mapping_v2.csv",
        f"missing={len(missing)}",
        missing,
        "OK" if not missing else "HIGH",
        "USER_NUM connects master users to view history.",
    )

    null_count = int(master[USER_NUM].isna().sum())
    add(
        "master USER_NUM missing",
        "PASS" if null_count == 0 else "FAIL",
        "master USER_NUM has no missing values",
        f"missing={null_count}",
        null_count,
        "OK" if null_count == 0 else "HIGH",
        "Missing USER_NUM blocks view-history reconstruction for affected users.",
    )

    missing = view_user_nums - mapping_user_nums
    add(
        "View_History_v2 USER_NUM coverage in User_Mapping_v2",
        "PASS" if not missing else "FAIL",
        "all View_History_v2 USER_NUM values exist in User_Mapping_v2.csv",
        f"missing={len(missing)}",
        missing,
        "OK" if not missing else "HIGH",
        "Unmapped view rows cannot be assigned to USER_KEY.",
    )

    missing = mapping_user_nums - view_user_nums
    add(
        "User_Mapping_v2 USER_NUM coverage in View_History_v2",
        "PASS" if not missing else "FAIL",
        "all mapping USER_NUM values appear at least once in View_History_v2.csv",
        f"missing={len(missing)}",
        missing,
        "OK" if not missing else "LOW",
        "Users without views are valid but affect zero-fill policy checks.",
    )

    missing = view_movie_nums - movie_nums
    add(
        "View_History_v2 MOVIE_NUM coverage in Movie_Master_v2",
        "PASS" if not missing else "FAIL",
        "all View_History_v2 MOVIE_NUM values exist in Movie_Master_v2.csv",
        f"missing={len(missing)}",
        missing,
        "OK" if not missing else "HIGH",
        "Missing movie metadata blocks content-derived reconstruction.",
    )

    dup_movie_groups = movie.groupby("MOVIE_NUM").size()
    duplicated_movie_nums = set(dup_movie_groups[dup_movie_groups > 1].index)
    conflicting = []
    for movie_num, group in movie[movie["MOVIE_NUM"].isin(duplicated_movie_nums)].groupby("MOVIE_NUM"):
        if group[["movie_title", "ott_release_month", "category"]].drop_duplicates().shape[0] > 1:
            conflicting.append(movie_num)
    impacted = set(conflicting) & view_movie_nums
    add(
        "Movie_Master_v2 duplicate MOVIE_NUM content feature impact",
        "PASS" if not impacted else "FAIL",
        "duplicate MOVIE_NUM rows are exact duplicates or unused by view history",
        f"duplicated_MOVIE_NUM={len(duplicated_movie_nums)}, conflicting_metadata_used={len(impacted)}",
        impacted,
        "OK" if not impacted else "MEDIUM",
        "Conflicting duplicate metadata can change genre and release-date features depending on dedup policy.",
    )

    return pd.DataFrame(rows)


def corrupted_date_candidate(source_dt: pd.Series) -> pd.Series:
    out = []
    for value in source_dt:
        if pd.isna(value):
            out.append(pd.NaT)
            continue
        year = 2000 + int(value.day)
        month = int(value.month)
        day = int(value.year) % 100
        try:
            out.append(pd.Timestamp(year=year, month=month, day=day))
        except ValueError:
            out.append(pd.NaT)
    return pd.Series(out, index=source_dt.index)


def make_date_error_audit(master: pd.DataFrame, membership: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    source = membership[[KEY, "reg_date", "end_date"]].rename(
        columns={"reg_date": "membership_reg_date", "end_date": "membership_end_date"}
    )
    target = master[[KEY, "reg_date", "end_date"]].rename(
        columns={"reg_date": "master_reg_date", "end_date": "master_end_date"}
    )
    audit = source.merge(target, on=KEY, how="inner")
    membership_reg_dt = as_date(audit["membership_reg_date"])
    membership_end_dt = as_date(audit["membership_end_date"])
    master_reg_dt = as_date(audit["master_reg_date"])
    master_end_dt = as_date(audit["master_end_date"])

    audit["reg_date_equal"] = membership_reg_dt.eq(master_reg_dt)
    audit["end_date_equal"] = membership_end_dt.eq(master_end_dt)
    corrupt_reg = corrupted_date_candidate(membership_reg_dt)
    corrupt_end = corrupted_date_candidate(membership_end_dt)
    audit["suspected_reg_date_transformation"] = np.where(
        corrupt_reg.eq(master_reg_dt),
        "source day used as master year and source year suffix used as master day",
        "not_matching_tested_transformation",
    )
    audit["suspected_end_date_transformation"] = np.where(
        corrupt_end.eq(master_end_dt),
        "source day used as master year and source year suffix used as master day",
        "not_matching_tested_transformation",
    )
    audit["note"] = np.where(
        audit["reg_date_equal"] & audit["end_date_equal"],
        "master date matches membership date",
        "master date differs from Membership_v2.csv; use Membership_v2.csv for date-derived reconstruction",
    )
    summary = {
        "reg_match_rate": float(audit["reg_date_equal"].mean()) if len(audit) else np.nan,
        "end_match_rate": float(audit["end_date_equal"].mean()) if len(audit) else np.nan,
        "reg_suspected_transform_rate": float((corrupt_reg.eq(master_reg_dt)).mean()) if len(audit) else np.nan,
        "end_suspected_transform_rate": float((corrupt_end.eq(master_end_dt)).mean()) if len(audit) else np.nan,
    }
    return audit, summary


def safe_name(name: str) -> str:
    replacement = name.replace("%", "pct")
    replacement = replacement.replace("(", "_").replace(")", "")
    replacement = replacement.replace("/", "_").replace(" ", "_")
    replacement = re.sub(r"[^0-9A-Za-z_]+", "_", replacement)
    replacement = re.sub(r"_+", "_", replacement).strip("_")
    if replacement and replacement[0].isdigit():
        replacement = "col_" + replacement
    return replacement or "unnamed_variable"


def risky_name_flags(name: str) -> list[str]:
    flags = []
    if "%" in name:
        flags.append("contains_percent")
    if "(" in name or ")" in name:
        flags.append("contains_parentheses")
    if re.search(r"\s", name):
        flags.append("contains_space")
    if "/" in name:
        flags.append("contains_slash")
    if re.search(r"[가-힣]", name):
        flags.append("contains_korean")
    if re.search(r"[^0-9A-Za-z_가-힣%()/\s]", name):
        flags.append("contains_other_special_char")
    if name and name[0].isdigit():
        flags.append("starts_with_digit")
    return flags


def make_v3_master_comparison(master: pd.DataFrame, v3: pd.DataFrame) -> pd.DataFrame:
    if "변수명" not in v3.columns:
        fail("v3 definition file is missing required column: 변수명")
    v3_names = set(v3["변수명"].dropna().astype(str).str.strip())
    master_names = set(master.columns)
    simplified_to_master = {}
    for col in master_names:
        simplified_to_master.setdefault(re.sub(r"[^0-9a-z]+", "", col.lower()), []).append(col)

    rows = []
    for name in sorted(master_names | v3_names):
        simple = re.sub(r"[^0-9a-z]+", "", name.lower())
        semantic = [candidate for candidate in simplified_to_master.get(simple, []) if candidate != name]
        flags = risky_name_flags(name)
        rows.append(
            {
                "variable_name": name,
                "in_master": name in master_names,
                "in_v3_definition": name in v3_names,
                "exact_match": name in master_names and name in v3_names,
                "possible_semantic_master_match": "; ".join(semantic),
                "name_risk_flags": "; ".join(flags),
                "recommended_safe_column_name": safe_name(name) if flags else name,
            }
        )
    return pd.DataFrame(rows)


def prepare_source_tables(master, membership, mapping, view, movie):
    membership_u = membership.drop_duplicates(KEY, keep="first").copy()
    membership_u["membership_reg_dt"] = as_date(membership_u["reg_date"])
    membership_u["membership_end_dt"] = as_date(membership_u["end_date"])
    mapping_u_by_key = mapping.drop_duplicates(KEY, keep="first").copy()

    view_base = view.copy()
    view_base["watch_date"] = as_watch_date(view_base["watch_day"])
    view_base = view_base.merge(mapping[[USER_NUM, KEY]], on=USER_NUM, how="left")
    view_base = view_base.merge(membership_u[[KEY, "membership_reg_dt", "membership_end_dt"]], on=KEY, how="left")
    view_base["rel_day"] = (view_base["watch_date"] - view_base["membership_reg_dt"]).dt.days
    view_base["days_before_end"] = (view_base["membership_end_dt"] - view_base["watch_date"]).dt.days
    view_base["watch_weekday"] = view_base["watch_date"].dt.weekday
    view_base[WATCH_TIME] = pd.to_numeric(view_base[WATCH_TIME], errors="coerce")

    movie_base = movie.copy()
    movie_base["release_year"] = pd.to_numeric(movie_base["ott_release_month"], errors="coerce") // 100
    movie_base["release_month_date"] = pd.to_datetime(
        movie_base["ott_release_month"].astype("Int64").astype(str) + "01", format="%Y%m%d", errors="coerce"
    ).dt.normalize()
    return membership_u, mapping_u_by_key, view_base, movie_base


def compare_membership_family(master, membership_u, mapping_u_by_key):
    mem_index = membership_u.set_index(KEY)
    if KEY in master.columns:
        add_check(
            master,
            KEY,
            pd.Series(mem_index.index, index=mem_index.index),
            "membership_raw_copy_USER_KEY",
            "Membership_v2.csv USER_KEY copied as master USER_KEY",
            ["Membership_v2.csv"],
            [KEY],
            note="Raw source comparison; row order is not used.",
        )
    for col in membership_u.columns:
        if col == KEY:
            continue
        if col in ["membership_reg_dt", "membership_end_dt"]:
            continue
        if col in master.columns:
            add_check(
                master,
                col,
                mem_index[col],
                f"membership_raw_copy_{col}",
                f"Membership_v2.csv `{col}` copied by USER_KEY",
                ["Membership_v2.csv"],
                [col],
                note="Raw source comparison; row order is not used.",
            )

    if USER_NUM in master.columns:
        add_check(
            master,
            USER_NUM,
            mapping_u_by_key.set_index(KEY)[USER_NUM],
            "mapping_user_num_by_user_key",
            "User_Mapping_v2.csv USER_NUM joined to master by USER_KEY",
            ["User_Mapping_v2.csv"],
            [KEY, USER_NUM],
            note="Uses USER_KEY as join key; duplicate mapping keys are separately audited.",
        )

    h = pd.to_numeric(mem_index["max_screen"], errors="coerce")
    if "is_standard" in master.columns:
        add_check(master, "is_standard", (h == 2).astype(int), "is_standard_max_screen_eq_2", "max_screen == 2", ["Membership_v2.csv"], ["max_screen"])
        add_check(master, "is_standard", (h == 1).astype(int), "is_standard_max_screen_eq_1", "max_screen == 1", ["Membership_v2.csv"], ["max_screen"])
    if "is_premium" in master.columns:
        add_check(master, "is_premium", (h == 4).astype(int), "is_premium_max_screen_eq_4", "max_screen == 4", ["Membership_v2.csv"], ["max_screen"])
        add_check(master, "is_premium", (h >= 4).astype(int), "is_premium_max_screen_ge_4", "max_screen >= 4", ["Membership_v2.csv"], ["max_screen"])

    gender = mem_index["gender"].astype("string").str.strip().str.upper()
    if "is_female" in master.columns:
        add_check(master, "is_female", (gender == "F").astype(int), "is_female_gender_F", "gender == 'F'", ["Membership_v2.csv"], ["gender"])
    if "is_male" in master.columns:
        add_check(master, "is_male", (gender == "M").astype(int), "is_male_gender_M", "gender == 'M'", ["Membership_v2.csv"], ["gender"])

    age = pd.to_numeric(mem_index["age"], errors="coerce")
    if "age_group" in master.columns:
        add_check(master, "age_group", (np.floor(age / 10) * 10), "age_group_decade_floor", "floor(age / 10) * 10", ["Membership_v2.csv"], ["age"])
        bins = pd.cut(age, bins=[0, 19, 29, 39, 49, 59, 69, 200], labels=[10, 20, 30, 40, 50, 60, 70], include_lowest=True)
        add_check(master, "age_group", bins.astype(float), "age_group_closed_decade_bins", "age binned as 10s, 20s, 30s ...", ["Membership_v2.csv"], ["age"])

    reg_dt = mem_index["membership_reg_dt"]
    if "reg_is_weekend" in master.columns:
        add_check(
            master,
            "reg_is_weekend",
            (reg_dt.dt.weekday >= 5).astype(int),
            "reg_is_weekend_membership_reg_date",
            "Membership_v2.csv reg_date weekday is Saturday or Sunday",
            ["Membership_v2.csv"],
            ["reg_date"],
            date_basis="Membership_v2.csv reg_date",
        )

    reg_hour = pd.to_numeric(mem_index["reg_hour"], errors="coerce")
    hour_candidates = {
        "reg_hour_morning": (reg_hour >= 6) & (reg_hour < 12),
        "reg_hour_afternoon": (reg_hour >= 12) & (reg_hour < 18),
        "reg_hour_evening": (reg_hour >= 18) & (reg_hour < 24),
        "reg_hour_night": (reg_hour >= 0) & (reg_hour < 6),
    }
    for col, mask in hour_candidates.items():
        if col in master.columns:
            add_check(master, col, mask.astype(int), f"{col}_standard_6h_bins", f"{col} from reg_hour using 06-12-18-24 bins", ["Membership_v2.csv"], ["reg_hour"])

    payment = mem_index["payment_device"].astype("string").str.strip().str.lower()
    payment_candidates = {
        "payment_is_pc": {"pc_eq": payment.eq("pc")},
        "payment_is_android": {"android_eq": payment.eq("android")},
        "payment_is_ios": {"ios_eq": payment.eq("ios")},
        "payment_is_mobile": {
            "mobile_literal": payment.eq("mobile"),
            "android_or_ios_or_mobile": payment.isin(["android", "ios", "mobile"]),
            "not_pc": payment.notna() & ~payment.eq("pc"),
        },
    }
    for col, candidates in payment_candidates.items():
        if col in master.columns:
            for suffix, mask in candidates.items():
                add_check(master, col, mask.astype(int), f"{col}_{suffix}", f"{col} from payment_device: {suffix}", ["Membership_v2.csv"], ["payment_device"])


def gap_stats_series(grouped_rel_days, start: int, end: int) -> pd.DataFrame:
    rows = []
    for user_key, values in grouped_rel_days:
        arr = np.array(sorted(pd.Series(values).dropna().astype(int).unique()))
        if len(arr) <= 1:
            avg_gap = 0.0
            max_gap = 0.0
            max_gap_minus_1 = 0.0
        else:
            diffs = np.diff(arr)
            avg_gap = float(np.mean(diffs))
            max_gap = float(np.max(diffs))
            max_gap_minus_1 = float(np.max(diffs - 1))
        if len(arr) == 0:
            edge_gap = float(end - start + 1)
        else:
            edge_parts = [arr[0] - start, end - arr[-1]]
            if len(arr) > 1:
                edge_parts.extend(list(np.diff(arr) - 1))
            edge_gap = float(max(edge_parts))
        rows.append(
            {
                KEY: user_key,
                "avg_gap": avg_gap,
                "max_gap": max_gap,
                "max_gap_minus_1": max_gap_minus_1,
                "max_inactive_with_edges": edge_gap,
            }
        )
    return pd.DataFrame(rows).set_index(KEY) if rows else pd.DataFrame(columns=["avg_gap", "max_gap", "max_gap_minus_1", "max_inactive_with_edges"]).rename_axis(KEY)


def window_definitions(view_base: pd.DataFrame) -> dict:
    return {
        "reg_day0_to_day20": {"mask": view_base["rel_day"].between(0, 20, inclusive="both"), "length": 21, "start": 0, "end": 20, "date_basis": "Membership_v2.csv reg_date"},
        "reg_day1_to_day21": {"mask": view_base["rel_day"].between(1, 21, inclusive="both"), "length": 21, "start": 1, "end": 21, "date_basis": "Membership_v2.csv reg_date"},
        "reg_day0_to_day21": {"mask": view_base["rel_day"].between(0, 21, inclusive="both"), "length": 22, "start": 0, "end": 21, "date_basis": "Membership_v2.csv reg_date"},
        "end_minus20_to_end": {"mask": view_base["days_before_end"].between(0, 20, inclusive="both"), "length": 21, "start": -20, "end": 0, "date_basis": "Membership_v2.csv end_date"},
    }


def compare_watch_family(master: pd.DataFrame, view_base: pd.DataFrame):
    all_keys = pd.Index(master[KEY].drop_duplicates(), name=KEY)
    for window_id, spec in window_definitions(view_base).items():
        win = view_base.loc[spec["mask"] & view_base[KEY].notna()].copy()
        group = win.groupby(KEY, dropna=False)
        count = group.size().reindex(all_keys).fillna(0).astype(float)
        total_time = group[WATCH_TIME].sum().reindex(all_keys).fillna(0.0)
        unique_movie = group["MOVIE_NUM"].nunique().reindex(all_keys).fillna(0).astype(float)
        watch_days = group["watch_day"].nunique().reindex(all_keys).fillna(0).astype(float)
        avg_watch = group[WATCH_TIME].mean().reindex(all_keys).fillna(0.0)
        median_watch = group[WATCH_TIME].median().reindex(all_keys).fillna(0.0)
        std0 = group[WATCH_TIME].std(ddof=0).reindex(all_keys).fillna(0.0)
        std1 = group[WATCH_TIME].std(ddof=1).reindex(all_keys).fillna(0.0)
        max_watch = group[WATCH_TIME].max().reindex(all_keys).fillna(0.0)
        first_rel = group["rel_day"].min().reindex(all_keys)
        last_rel = group["rel_day"].max().reindex(all_keys)

        daily = win.groupby([KEY, "rel_day"], dropna=False)[WATCH_TIME].agg(["sum", "size"]).reset_index()
        daily_group = daily.groupby(KEY, dropna=False)
        daily_time_mean_active = daily_group["sum"].mean().reindex(all_keys).fillna(0.0)
        daily_time_max = daily_group["sum"].max().reindex(all_keys).fillna(0.0)
        daily_session_max = daily_group["size"].max().reindex(all_keys).fillna(0.0)
        day_count_gt3 = daily_group["size"].apply(lambda s: (s > 3).sum()).reindex(all_keys).fillna(0).astype(float)
        day_count_ge3 = daily_group["size"].apply(lambda s: (s >= 3).sum()).reindex(all_keys).fillna(0).astype(float)

        gaps = gap_stats_series(group["rel_day"], spec["start"], spec["end"]).reindex(all_keys).fillna(0.0)
        duplicated_extra = (count - unique_movie).clip(lower=0)
        duplicate_row_ratio = safe_div(duplicated_extra, count, "zero")
        repeated_movie_row_ratio = group["MOVIE_NUM"].apply(lambda s: s.duplicated(keep=False).mean() if len(s) else 0).reindex(all_keys).fillna(0.0)
        weekend_row_ratio = group.apply(lambda g: (g["watch_weekday"] >= 5).mean() if len(g) else 0, include_groups=False).reindex(all_keys).fillna(0.0)
        weekend_time_ratio = group.apply(
            lambda g: float(g.loc[g["watch_weekday"] >= 5, WATCH_TIME].sum() / g[WATCH_TIME].sum()) if g[WATCH_TIME].sum() else 0,
            include_groups=False,
        ).reindex(all_keys).fillna(0.0)
        under_1_le = group[WATCH_TIME].apply(lambda s: (s <= 1).mean() if len(s) else 0).reindex(all_keys).fillna(0.0)
        under_1_lt = group[WATCH_TIME].apply(lambda s: (s < 1).mean() if len(s) else 0).reindex(all_keys).fillna(0.0)
        under_5_le = group[WATCH_TIME].apply(lambda s: (s <= 5).mean() if len(s) else 0).reindex(all_keys).fillna(0.0)
        under_5_lt = group[WATCH_TIME].apply(lambda s: (s < 5).mean() if len(s) else 0).reindex(all_keys).fillna(0.0)

        base_meta = {
            "source_files_used": ["View_History_v2.csv", "User_Mapping_v2.csv", "Membership_v2.csv"],
            "source_columns_used": [USER_NUM, "MOVIE_NUM", WATCH_TIME, "watch_day", "watch_seq", "reg_date"],
            "date_basis": spec["date_basis"],
            "observation_window": window_id,
        }

        candidates = {
            "total_watch_count": [(count, "row_count", "view row count in observation window", "")],
            "unique_movie": [(unique_movie, "distinct_movie", "distinct MOVIE_NUM count in observation window", "")],
            "watch_days": [(watch_days, "distinct_watch_day", "distinct watch_day count in observation window", "")],
            "total_watch_time": [(total_time, "watch_time_sum", "sum of watch_time(min) in observation window", "")],
            "avg_watch_time": [(avg_watch, "row_mean_watch_time", "mean watch_time(min) per view row", "")],
            "median_watch_time": [(median_watch, "row_median_watch_time", "median watch_time(min) per view row", "")],
            "std_watch_time": [(std0, "row_std_ddof0", "std watch_time(min), ddof=0", ""), (std1, "row_std_ddof1", "std watch_time(min), ddof=1", "")],
            "avg_daily_watch_time": [
                (daily_time_mean_active, "daily_sum_mean_active_days", "mean of daily watch_time sums over active days only", "active watch days"),
                (total_time / spec["length"], "daily_sum_mean_full_window", "sum watch_time divided by observation window length", str(spec["length"])),
            ],
            "max_watch_time": [(max_watch, "max_row_watch_time", "maximum watch_time(min) for a single view row", "")],
            "max_daily_watch_time": [(daily_time_max, "max_daily_watch_time", "maximum daily sum of watch_time(min)", "")],
            "max_daily_sessions": [(daily_session_max, "max_daily_view_rows", "maximum daily view row count", "")],
            "recency": [
                ((spec["end"] - last_rel).fillna(spec["length"]), "window_end_minus_last_rel_day", "observation-window end relative day minus last watch relative day", "window end"),
                (last_rel.fillna(-1), "last_relative_watch_day", "last watch relative day", ""),
            ],
            "avg_gap_between_watch_days": [(gaps["avg_gap"], "unique_watch_day_gap_mean", "mean gap between sorted distinct watch days", "")],
            "max_inactive_gap_days": [
                (gaps["max_gap"], "max_gap_between_watch_days", "maximum difference between consecutive active watch days", ""),
                (gaps["max_gap_minus_1"], "max_inactive_between_active_days", "maximum inactive days between active watch days", ""),
                (gaps["max_inactive_with_edges"], "max_inactive_including_edges", "maximum inactive gap including observation-window start and end", ""),
            ],
            "avg_rewatch_ratio": [
                (duplicate_row_ratio, "extra_duplicate_views_over_total_rows", "(view rows - distinct MOVIE_NUM) / view rows", "view rows"),
                (repeated_movie_row_ratio, "rows_belonging_to_repeated_movies_ratio", "rows whose MOVIE_NUM appears more than once / view rows", "view rows"),
            ],
            "weekend_watch_ratio": [
                (weekend_row_ratio, "weekend_view_rows_over_all_rows", "weekend view row count / all view row count", "view rows"),
                (weekend_time_ratio, "weekend_watch_time_over_total_time", "weekend watch_time sum / total watch_time", "watch_time sum"),
            ],
            "watch_ratio_under_1m": [
                (under_1_le, "watch_time_le_1_over_rows", "watch_time(min) <= 1 / view rows", "view rows"),
                (under_1_lt, "watch_time_lt_1_over_rows", "watch_time(min) < 1 / view rows", "view rows"),
            ],
            "watch_ratio_under_5m": [
                (under_5_le, "watch_time_le_5_over_rows", "watch_time(min) <= 5 / view rows", "view rows"),
                (under_5_lt, "watch_time_lt_5_over_rows", "watch_time(min) < 5 / view rows", "view rows"),
            ],
            "is_cold_start_3d": [
                ((first_rel <= 2).fillna(False).astype(int), "first_watch_rel_day_le_2", "first watch relative day <= 2", ""),
                ((first_rel <= 3).fillna(False).astype(int), "first_watch_rel_day_le_3", "first watch relative day <= 3", ""),
            ],
            "is_cold_start_7d": [
                ((first_rel <= 6).fillna(False).astype(int), "first_watch_rel_day_le_6", "first watch relative day <= 6", ""),
                ((first_rel <= 7).fillna(False).astype(int), "first_watch_rel_day_le_7", "first watch relative day <= 7", ""),
            ],
            "movie_per_active_day": [
                (safe_div(unique_movie, watch_days, "zero"), "unique_movie_over_watch_days", "distinct MOVIE_NUM / active watch days", "watch_days"),
                (safe_div(count, watch_days, "zero"), "view_rows_over_watch_days", "view rows / active watch days", "watch_days"),
            ],
            "max_day_share": [
                (safe_div(daily_time_max, total_time, "zero"), "max_daily_time_over_total_time", "maximum daily watch_time / total watch_time", "total_watch_time"),
                (safe_div(daily_session_max, count, "zero"), "max_daily_sessions_over_total_sessions", "maximum daily sessions / total sessions", "total_watch_count"),
            ],
            "day_count_over_3times": [
                (day_count_gt3, "daily_sessions_gt_3_count", "number of days with more than 3 view rows", ""),
                (day_count_ge3, "daily_sessions_ge_3_count", "number of days with at least 3 view rows", ""),
            ],
        }

        for denominator in [spec["length"], 20, 21, 31]:
            candidates.setdefault("active_ratio", []).append((watch_days / denominator, f"watch_days_over_{denominator}", f"watch_days / {denominator}", str(denominator)))
            candidates.setdefault("watch_per_day", []).append((count / denominator, f"view_rows_over_{denominator}", f"total_watch_count / {denominator}", str(denominator)))
        candidates.setdefault("watch_per_day", []).append((safe_div(count, watch_days, "zero"), "view_rows_over_active_days", "total_watch_count / watch_days", "watch_days"))

        for week_label, start, end in [("w1", 0, 6), ("w2", 7, 13), ("w3", 14, 20)]:
            col = f"avg_gap_{week_label}_watch_days"
            if col in master.columns:
                week_win = win[win["rel_day"].between(start, end, inclusive="both")]
                week_gaps = gap_stats_series(week_win.groupby(KEY)["rel_day"], start, end).reindex(all_keys).fillna(0.0)
                add_check(
                    master,
                    col,
                    week_gaps["avg_gap"],
                    f"{col}_{window_id}_unique_day_gap_mean",
                    f"mean gap between sorted distinct watch days inside {week_label}",
                    **base_meta,
                )

        for variable, formulas in candidates.items():
            if variable not in master.columns:
                continue
            for values, formula_id, desc, denom in formulas:
                add_check(
                    master,
                    variable,
                    pd.Series(values, index=all_keys),
                    f"{variable}_{window_id}_{formula_id}",
                    desc,
                    denominator=denom,
                    zero_denominator_policy="zero when denominator is zero" if "over" in formula_id or "ratio" in formula_id else "",
                    **base_meta,
                )


def weekly_candidates(view_base: pd.DataFrame, scheme: str) -> pd.DataFrame:
    df = view_base[view_base[KEY].notna()].copy()
    if scheme == "A_reg_0_6_7_13_14_20":
        conditions = [df["rel_day"].between(0, 6), df["rel_day"].between(7, 13), df["rel_day"].between(14, 20)]
    elif scheme == "B_reg_1_7_8_14_15_21":
        conditions = [df["rel_day"].between(1, 7), df["rel_day"].between(8, 14), df["rel_day"].between(15, 21)]
    elif scheme == "C_calendar_week_from_reg_week":
        reg_monday = df["membership_reg_dt"] - pd.to_timedelta(df["membership_reg_dt"].dt.weekday, unit="D")
        watch_monday = df["watch_date"] - pd.to_timedelta(df["watch_date"].dt.weekday, unit="D")
        calendar_week_idx = ((watch_monday - reg_monday).dt.days // 7) + 1
        conditions = [calendar_week_idx.eq(1), calendar_week_idx.eq(2), calendar_week_idx.eq(3)]
    else:
        fail(f"Unknown weekly scheme: {scheme}")
    week = np.select(conditions, [1, 2, 3], default=0)
    df["week_idx"] = week
    df = df[df["week_idx"].isin([1, 2, 3])]
    agg = df.groupby([KEY, "week_idx"])[WATCH_TIME].agg(["sum", "size"]).reset_index()
    time = agg.pivot(index=KEY, columns="week_idx", values="sum").rename(columns={1: "watch_time_w1", 2: "watch_time_w2", 3: "watch_time_w3"})
    sess = agg.pivot(index=KEY, columns="week_idx", values="size").rename(columns={1: "watch_session_w1", 2: "watch_session_w2", 3: "watch_session_w3"})
    out = pd.concat([time, sess], axis=1).fillna(0.0)
    for col in ["watch_time_w1", "watch_time_w2", "watch_time_w3", "watch_session_w1", "watch_session_w2", "watch_session_w3"]:
        if col not in out.columns:
            out[col] = 0.0
    return out


def compare_weekly_family(master: pd.DataFrame, view_base: pd.DataFrame):
    all_keys = pd.Index(master[KEY].drop_duplicates(), name=KEY)
    schemes = ["A_reg_0_6_7_13_14_20", "B_reg_1_7_8_14_15_21", "C_calendar_week_from_reg_week"]
    for scheme in schemes:
        weekly = weekly_candidates(view_base, scheme).reindex(all_keys).fillna(0.0)
        source_files = ["View_History_v2.csv", "User_Mapping_v2.csv", "Membership_v2.csv"]
        source_cols = [USER_NUM, WATCH_TIME, "watch_day", "reg_date"]
        for col in ["watch_time_w1", "watch_time_w2", "watch_time_w3", "watch_session_w1", "watch_session_w2", "watch_session_w3"]:
            if col in master.columns:
                add_check(master, col, weekly[col], f"{col}_{scheme}", f"{col} under weekly scheme {scheme}", source_files, source_cols, date_basis="Membership_v2.csv reg_date", observation_window=scheme)

        w1 = weekly["watch_time_w1"]
        w2 = weekly["watch_time_w2"]
        w3 = weekly["watch_time_w3"]
        total3 = w1 + w2 + w3
        ratio_candidates = {
            "retention_w2_ratio": [(w2, w1, "w2_over_w1"), (w2, w1 + 1, "w2_over_w1_plus_1"), (w2 + 1, w1 + 1, "w2_plus_1_over_w1_plus_1")],
            "retention_w3_ratio": [(w3, w2, "w3_over_w2"), (w3, w2 + 1, "w3_over_w2_plus_1"), (w3 + 1, w2 + 1, "w3_plus_1_over_w2_plus_1")],
        }
        for variable, formulas in ratio_candidates.items():
            if variable not in master.columns:
                continue
            for numerator, denominator, suffix in formulas:
                for zero_policy in ["zero", "nan"]:
                    values = safe_div(numerator, denominator, zero_policy)
                    add_check(
                        master,
                        variable,
                        values,
                        f"{variable}_{scheme}_{suffix}_zero_{zero_policy}",
                        f"{suffix}; denominator zero policy={zero_policy}",
                        source_files,
                        source_cols,
                        date_basis="Membership_v2.csv reg_date",
                        observation_window=scheme,
                        denominator=suffix.split("_over_")[-1],
                        zero_denominator_policy=zero_policy,
                    )

        if "w3_to_w1_ratio_capped" in master.columns:
            raw_ratio = safe_div(w3, w1, "zero")
            add_check(master, "w3_to_w1_ratio_capped", raw_ratio, f"w3_to_w1_{scheme}_uncapped_zero", "watch_time_w3 / watch_time_w1, zero denominator -> 0, uncapped", source_files, source_cols, date_basis="Membership_v2.csv reg_date", observation_window=scheme, denominator="watch_time_w1", zero_denominator_policy="zero")
            for cap in [1, 2, 5, 10, 20, 50, 100]:
                add_check(master, "w3_to_w1_ratio_capped", raw_ratio.clip(upper=cap), f"w3_to_w1_{scheme}_cap_{cap}", f"watch_time_w3 / watch_time_w1 capped at {cap}", source_files, source_cols, date_basis="Membership_v2.csv reg_date", observation_window=scheme, denominator="watch_time_w1", zero_denominator_policy="zero")

        diff_map = {
            "diff_between_w2_w1": w2 - w1,
            "diff_between_w3_w1": w3 - w1,
            "diff_between_w3_w2": w3 - w2,
        }
        for col, values in diff_map.items():
            if col in master.columns:
                add_check(master, col, values, f"{col}_{scheme}", f"{col} calculated from weekly watch_time sums", source_files, source_cols, date_basis="Membership_v2.csv reg_date", observation_window=scheme)

        week_times = {"w1": w1, "w2": w2, "w3": w3}
        for week_name, values in week_times.items():
            col = f"is_{week_name}_over_50%"
            if col in master.columns:
                for denom_name, denom_values in {"three_week_sum": total3, "master_total_watch_time_equivalent": total3}.items():
                    ratio = safe_div(values, denom_values, "zero")
                    add_check(master, col, (ratio >= 0.5).astype(int), f"{col}_{scheme}_{denom_name}_ge_0p5", f"{week_name} watch_time / {denom_name} >= 0.5", source_files, source_cols, date_basis="Membership_v2.csv reg_date", observation_window=scheme, denominator=denom_name, zero_denominator_policy="zero")
                    add_check(master, col, (ratio > 0.5).astype(int), f"{col}_{scheme}_{denom_name}_gt_0p5", f"{week_name} watch_time / {denom_name} > 0.5", source_files, source_cols, date_basis="Membership_v2.csv reg_date", observation_window=scheme, denominator=denom_name, zero_denominator_policy="zero")

        only_defs = {
            "is_only_w1": (w1 > 0) & (w2 == 0) & (w3 == 0),
            "is_only_w2": (w2 > 0) & (w1 == 0) & (w3 == 0),
            "is_only_w3": (w3 > 0) & (w1 == 0) & (w2 == 0),
        }
        s1, s2, s3 = weekly["watch_session_w1"], weekly["watch_session_w2"], weekly["watch_session_w3"]
        only_session_defs = {
            "is_only_w1": (s1 > 0) & (s2 == 0) & (s3 == 0),
            "is_only_w2": (s2 > 0) & (s1 == 0) & (s3 == 0),
            "is_only_w3": (s3 > 0) & (s1 == 0) & (s2 == 0),
        }
        for col, mask in only_defs.items():
            if col in master.columns:
                add_check(master, col, mask.astype(int), f"{col}_{scheme}_watch_time_only", f"only {col[-2:]} has watch_time > 0", source_files, source_cols, date_basis="Membership_v2.csv reg_date", observation_window=scheme)
                add_check(master, col, only_session_defs[col].astype(int), f"{col}_{scheme}_session_only", f"only {col[-2:]} has session count > 0", source_files, source_cols, date_basis="Membership_v2.csv reg_date", observation_window=scheme)


def movie_dedup_variants(movie_base: pd.DataFrame) -> dict[str, pd.DataFrame]:
    variants = {}
    exact = movie_base.drop_duplicates().copy()
    variants["exact_duplicates_removed_then_first_MOVIE_NUM"] = exact.drop_duplicates("MOVIE_NUM", keep="first").copy()
    variants["MOVIE_NUM_first"] = movie_base.drop_duplicates("MOVIE_NUM", keep="first").copy()
    variants["MOVIE_NUM_latest_ott_release_month"] = (
        movie_base.sort_values(["MOVIE_NUM", "ott_release_month"]).drop_duplicates("MOVIE_NUM", keep="last").copy()
    )
    mode_rows = []
    for movie_num, group in movie_base.groupby("MOVIE_NUM", dropna=False):
        category_mode = group["category"].mode(dropna=True)
        release_mode = group["ott_release_month"].mode(dropna=True)
        mode_rows.append(
            {
                "MOVIE_NUM": movie_num,
                "movie_title": group["movie_title"].dropna().iloc[0] if group["movie_title"].notna().any() else np.nan,
                "ott_release_month": release_mode.iloc[0] if len(release_mode) else np.nan,
                "category": category_mode.iloc[0] if len(category_mode) else np.nan,
            }
        )
    mode_df = pd.DataFrame(mode_rows)
    mode_df["release_year"] = pd.to_numeric(mode_df["ott_release_month"], errors="coerce") // 100
    mode_df["release_month_date"] = pd.to_datetime(
        mode_df["ott_release_month"].astype("Int64").astype(str) + "01", format="%Y%m%d", errors="coerce"
    ).dt.normalize()
    variants["MOVIE_NUM_mode_category_mode_release"] = mode_df
    variants["no_dedup_join_all_rows"] = movie_base.copy()
    return variants


def category_column_map() -> dict[str, str]:
    return {
        "Action/Adventure": "action_adventure_ratio",
        "Animation/Family": "family_animation_ratio",
        "Family/Animation": "family_animation_ratio",
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


def compare_content_family(master: pd.DataFrame, view_base: pd.DataFrame, movie_base: pd.DataFrame):
    all_keys = pd.Index(master[KEY].drop_duplicates(), name=KEY)
    source_files = ["View_History_v2.csv", "User_Mapping_v2.csv", "Membership_v2.csv", "Movie_Master_v2.csv"]
    source_cols = [USER_NUM, "MOVIE_NUM", WATCH_TIME, "watch_day", "reg_date", "ott_release_month", "category"]
    windows = window_definitions(view_base)
    variants = movie_dedup_variants(movie_base)
    content_windows = ["reg_day0_to_day20", "reg_day1_to_day21", "reg_day0_to_day21"]

    for window_id in content_windows:
        spec = windows[window_id]
        win = view_base.loc[spec["mask"] & view_base[KEY].notna()].copy()
        for variant_name, movie_variant in variants.items():
            merged = win.merge(movie_variant, on="MOVIE_NUM", how="left", suffixes=("", "_movie"))
            group = merged.groupby(KEY, dropna=False)
            row_count = group.size().reindex(all_keys).fillna(0.0)
            total_time = group[WATCH_TIME].sum().reindex(all_keys).fillna(0.0)

            for threshold in [90, 180, 365]:
                col = f"new_movie_in_{threshold}d_ratio"
                if col not in master.columns:
                    continue
                for basis_name, basis_date in {"reg_date": merged["membership_reg_dt"], "watch_date": merged["watch_date"]}.items():
                    days_since_release = (basis_date - merged["release_month_date"]).dt.days
                    is_new = days_since_release.between(0, threshold, inclusive="both")
                    row_ratio = group.apply(lambda g, mask=is_new: float(mask.loc[g.index].sum() / len(g)) if len(g) else 0, include_groups=False).reindex(all_keys).fillna(0.0)
                    time_ratio = group.apply(
                        lambda g, mask=is_new: float(g.loc[mask.loc[g.index], WATCH_TIME].sum() / g[WATCH_TIME].sum()) if g[WATCH_TIME].sum() else 0,
                        include_groups=False,
                    ).reindex(all_keys).fillna(0.0)
                    add_check(master, col, row_ratio, f"{col}_{window_id}_{variant_name}_{basis_name}_row_ratio", f"release month within {threshold} days before {basis_name}; row-count ratio", source_files, source_cols, date_basis=f"Membership_v2.csv {basis_name}", observation_window=window_id, denominator="view rows", zero_denominator_policy="zero")
                    add_check(master, col, time_ratio, f"{col}_{window_id}_{variant_name}_{basis_name}_time_ratio", f"release month within {threshold} days before {basis_name}; watch-time ratio", source_files, source_cols, date_basis=f"Membership_v2.csv {basis_name}", observation_window=window_id, denominator="watch_time sum", zero_denominator_policy="zero")

            if "old_movie_ratio(5y)" in master.columns:
                old_defs = {
                    "reg_year_minus_5": merged["release_year"] <= (merged["membership_reg_dt"].dt.year - 5),
                    "watch_year_minus_5": merged["release_year"] <= (merged["watch_date"].dt.year - 5),
                    "static_release_year_le_2016": merged["release_year"] <= 2016,
                }
                for basis_name, mask in old_defs.items():
                    row_ratio = group.apply(lambda g, mask=mask: float(mask.loc[g.index].sum() / len(g)) if len(g) else 0, include_groups=False).reindex(all_keys).fillna(0.0)
                    time_ratio = group.apply(
                        lambda g, mask=mask: float(g.loc[mask.loc[g.index], WATCH_TIME].sum() / g[WATCH_TIME].sum()) if g[WATCH_TIME].sum() else 0,
                        include_groups=False,
                    ).reindex(all_keys).fillna(0.0)
                    add_check(master, "old_movie_ratio(5y)", row_ratio, f"old_movie_5y_{window_id}_{variant_name}_{basis_name}_row_ratio", f"old movie 5y definition={basis_name}; row-count ratio", source_files, source_cols, date_basis=basis_name, observation_window=window_id, denominator="view rows", zero_denominator_policy="zero")
                    add_check(master, "old_movie_ratio(5y)", time_ratio, f"old_movie_5y_{window_id}_{variant_name}_{basis_name}_time_ratio", f"old movie 5y definition={basis_name}; watch-time ratio", source_files, source_cols, date_basis=basis_name, observation_window=window_id, denominator="watch_time sum", zero_denominator_policy="zero")

            if "avg_release_year" in master.columns:
                row_mean = group["release_year"].mean().reindex(all_keys).fillna(0.0)
                time_weighted = group.apply(lambda g: weighted_mean(g["release_year"], g[WATCH_TIME]), include_groups=False).reindex(all_keys).fillna(0.0)
                unique_mean = (
                    merged.drop_duplicates([KEY, "MOVIE_NUM"]).groupby(KEY)["release_year"].mean().reindex(all_keys).fillna(0.0)
                )
                add_check(master, "avg_release_year", row_mean, f"avg_release_year_{window_id}_{variant_name}_row_mean", "mean release year weighted by view rows", source_files, source_cols, date_basis="Movie_Master_v2.csv ott_release_month", observation_window=window_id, denominator="view rows")
                add_check(master, "avg_release_year", time_weighted, f"avg_release_year_{window_id}_{variant_name}_watch_time_weighted", "mean release year weighted by watch_time", source_files, source_cols, date_basis="Movie_Master_v2.csv ott_release_month", observation_window=window_id, denominator="watch_time sum")
                add_check(master, "avg_release_year", unique_mean, f"avg_release_year_{window_id}_{variant_name}_unique_movie_mean", "mean release year over distinct MOVIE_NUM", source_files, source_cols, date_basis="Movie_Master_v2.csv ott_release_month", observation_window=window_id, denominator="unique movie")

            if "genre_diversity_count" in master.columns:
                row_cat = group["category"].nunique().reindex(all_keys).fillna(0.0)
                unique_cat = merged.drop_duplicates([KEY, "MOVIE_NUM"]).groupby(KEY)["category"].nunique().reindex(all_keys).fillna(0.0)
                add_check(master, "genre_diversity_count", row_cat, f"genre_diversity_{window_id}_{variant_name}_row_category_nunique", "distinct category count among joined view rows", source_files, source_cols, observation_window=window_id)
                add_check(master, "genre_diversity_count", unique_cat, f"genre_diversity_{window_id}_{variant_name}_unique_movie_category_nunique", "distinct category count among distinct watched MOVIE_NUM", source_files, source_cols, observation_window=window_id)

            for category, col in category_column_map().items():
                if col not in master.columns:
                    continue
                cat_mask = merged["category"].eq(category)
                row_ratio = group.apply(lambda g, mask=cat_mask: float(mask.loc[g.index].sum() / len(g)) if len(g) else 0, include_groups=False).reindex(all_keys).fillna(0.0)
                time_ratio = group.apply(
                    lambda g, mask=cat_mask: float(g.loc[mask.loc[g.index], WATCH_TIME].sum() / g[WATCH_TIME].sum()) if g[WATCH_TIME].sum() else 0,
                    include_groups=False,
                ).reindex(all_keys).fillna(0.0)
                unique_counts = merged.drop_duplicates([KEY, "MOVIE_NUM"])
                unique_group = unique_counts.groupby(KEY)
                unique_ratio = unique_group.apply(lambda g, category=category: float(g["category"].eq(category).sum() / len(g)) if len(g) else 0, include_groups=False).reindex(all_keys).fillna(0.0)
                add_check(master, col, row_ratio, f"{col}_{window_id}_{variant_name}_row_ratio", f"{category} row count / all joined rows", source_files, source_cols, observation_window=window_id, denominator="view rows", zero_denominator_policy="zero")
                add_check(master, col, time_ratio, f"{col}_{window_id}_{variant_name}_watch_time_ratio", f"{category} watch_time / total watch_time", source_files, source_cols, observation_window=window_id, denominator="watch_time sum", zero_denominator_policy="zero")
                add_check(master, col, unique_ratio, f"{col}_{window_id}_{variant_name}_unique_movie_ratio", f"{category} distinct MOVIE_NUM / all distinct watched MOVIE_NUM", source_files, source_cols, observation_window=window_id, denominator="unique movie", zero_denominator_policy="zero")


def finalize_reconstruction_checks() -> pd.DataFrame:
    checks = pd.DataFrame(CHECK_ROWS)
    if checks.empty:
        return checks
    checks["_order"] = np.arange(len(checks))
    checks = checks.sort_values(["variable", "match_rate", "matched_rows", "_order"], ascending=[True, False, False, True])
    best_idx = checks.groupby("variable", sort=False).head(1).index
    checks["selected_candidate"] = False
    checks["selected_as_best_candidate"] = False
    checks.loc[best_idx, "selected_candidate"] = True
    checks.loc[best_idx, "selected_as_best_candidate"] = True
    checks["confidence_level"] = ""
    for idx in best_idx:
        rate = checks.loc[idx, "match_rate"]
        if pd.isna(rate):
            level = "UNKNOWN"
        elif rate >= 0.999:
            level = "CONFIRMED"
        elif rate >= 0.95:
            level = "STRONG_INFERENCE"
        else:
            level = "UNKNOWN"
        checks.loc[idx, "confidence_level"] = level
        checks.loc[idx, "reason"] = f"best candidate match_rate={rate:.6f}, mismatched_rows={int(checks.loc[idx, 'mismatched_rows'])}"
    checks = checks.sort_values("_order").drop(columns=["_order"])
    return checks


def classify_variable(col: str, membership_cols: set[str], mapping_cols: set[str], view_cols: set[str], movie_cols: set[str]) -> dict:
    categories = []
    processing = []
    source_files = []
    source_cols = []

    if col in [KEY, USER_NUM]:
        categories.append("key")
    if col == "is_repurchase":
        categories.append("target")
    if col in membership_cols:
        categories.extend(["raw_membership", "copied_from_source"])
        processing.append("copied_from_source")
        source_files.append("Membership_v2.csv")
        source_cols.append(col)
    if col == USER_NUM:
        categories.extend(["raw_mapping", "renamed_from_source"])
        processing.append("renamed_from_source")
        source_files.append("User_Mapping_v2.csv")
        source_cols.extend([KEY, USER_NUM])

    one_hot = {
        "is_standard",
        "is_premium",
        "is_female",
        "is_male",
        "reg_hour_morning",
        "reg_hour_afternoon",
        "reg_hour_evening",
        "reg_hour_night",
        "payment_is_mobile",
        "payment_is_pc",
        "payment_is_android",
        "payment_is_ios",
    }
    if col in one_hot:
        categories.append("one_hot_encoded")
        processing.append("one_hot_encoded")
        source_files.append("Membership_v2.csv")
    if col == "age_group":
        categories.append("binned")
        processing.append("binned")
        source_files.append("Membership_v2.csv")
        source_cols.append("age")
    if col in ["reg_is_weekend"]:
        categories.append("date_derived")
        processing.append("date_basis_calculation")
        source_files.append("Membership_v2.csv")
        source_cols.append("reg_date")

    watch_general = {
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
    }
    weekly = {
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
    }
    content = {"new_movie_in_90d_ratio", "new_movie_in_180d_ratio", "new_movie_in_365d_ratio", "old_movie_ratio(5y)", "avg_release_year", "genre_diversity_count"}
    genre = set(category_column_map().values())

    if col in watch_general:
        categories.extend(["raw_view_history", "user_watch_aggregate", "watch_pattern_feature"])
        processing.append("groupby_aggregate")
        source_files.extend(["View_History_v2.csv", "User_Mapping_v2.csv", "Membership_v2.csv"])
        source_cols.extend([USER_NUM, "MOVIE_NUM", WATCH_TIME, "watch_day", "reg_date"])
    if col in weekly:
        categories.extend(["weekly_watch_aggregate", "watch_pattern_feature"])
        processing.append("weekly_groupby_aggregate")
        source_files.extend(["View_History_v2.csv", "User_Mapping_v2.csv", "Membership_v2.csv"])
        source_cols.extend([USER_NUM, WATCH_TIME, "watch_day", "reg_date"])
    if col in content:
        categories.extend(["content_metadata_feature", "raw_movie_metadata"])
        processing.append("metadata_join_and_aggregate")
        source_files.extend(["View_History_v2.csv", "Movie_Master_v2.csv", "User_Mapping_v2.csv", "Membership_v2.csv"])
        source_cols.extend(["MOVIE_NUM", WATCH_TIME, "watch_day", "ott_release_month", "category", "reg_date"])
    if col in genre:
        categories.extend(["genre_ratio_feature", "content_metadata_feature"])
        processing.append("genre_ratio")
        source_files.extend(["View_History_v2.csv", "Movie_Master_v2.csv"])
        source_cols.extend(["MOVIE_NUM", WATCH_TIME, "category"])

    if "ratio" in col or col.endswith("_share") or "retention" in col:
        categories.append("ratio_feature")
    if col.startswith("diff_between"):
        categories.append("difference_feature")
    if "recency" in col or "release" in col or "new_movie" in col or "old_movie" in col:
        categories.append("recency_feature")

    if not categories:
        categories.append("unknown")
    if not processing:
        processing.append("unknown")
    return {
        "variable_category": "; ".join(sorted(set(categories))),
        "source_file": "; ".join(sorted(set(source_files))),
        "source_columns": "; ".join(sorted(set(source_cols))),
        "processing_type": "; ".join(sorted(set(processing))),
    }


def build_lineage_tables(
    master: pd.DataFrame,
    membership: pd.DataFrame,
    mapping: pd.DataFrame,
    view: pd.DataFrame,
    movie: pd.DataFrame,
    v3_compare: pd.DataFrame,
    reconstruction: pd.DataFrame,
    date_summary: dict,
    key_audit: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    best = reconstruction[reconstruction["selected_candidate"]].set_index("variable") if not reconstruction.empty else pd.DataFrame()
    v3_names = set(v3_compare.loc[v3_compare["in_v3_definition"], "variable_name"])
    risky_lookup = v3_compare.set_index("variable_name")["name_risk_flags"].to_dict()
    safe_lookup = v3_compare.set_index("variable_name")["recommended_safe_column_name"].to_dict()
    membership_cols = set(membership.columns)
    mapping_cols = set(mapping.columns)
    view_cols = set(view.columns)
    movie_cols = set(movie.columns)

    collinearity_set = {
        "total_watch_time",
        "watch_time_w1",
        "watch_time_w2",
        "watch_time_w3",
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
    }
    leakage_policy_dependent = {
        "is_churn_prevented",
        "end_date",
        "is_repurchase",
        "recency",
        "watch_time_w3",
        "retention_w3_ratio",
        "diff_between_w3_w1",
    }
    view_or_content_markers = [
        "watch",
        "movie",
        "genre",
        "drama",
        "thriller",
        "horror",
        "comedy",
        "romance",
        "documentary",
        "historical",
        "action",
        "family",
        "fantasy",
    ]

    rows = []
    risky_rows = []
    for col in master.columns:
        info = classify_variable(col, membership_cols, mapping_cols, view_cols, movie_cols)
        risk_flags = []
        if risky_lookup.get(col):
            risk_flags.append("VARIABLE_NAME_RISK")
        if col in ["reg_date", "end_date"]:
            risk_flags.append("MASTER_DATE_ERROR")
        if "date_derived" in info["variable_category"] or col in ["is_cold_start_3d", "is_cold_start_7d", "recency"]:
            risk_flags.append("DATE_ERROR_IMPACT_POSSIBLE")
        if col in collinearity_set:
            risk_flags.append("COLLINEARITY_RISK")
        if col == "is_repurchase":
            risk_flags.append("TARGET_DO_NOT_USE_AS_FEATURE")
        if col in leakage_policy_dependent or any(marker in col for marker in view_or_content_markers):
            risk_flags.append("POLICY_DEPENDENT_LEAKAGE_RISK")
        if "ratio" in col or "retention" in col or col.endswith("_share"):
            risk_flags.append("ZERO_DENOMINATOR_POLICY_NEEDS_CONFIRMATION")
        if key_audit.loc[key_audit["severity"].isin(["HIGH", "CRITICAL"]), :].shape[0] > 0 and ("view" in info["variable_category"] or "mapping" in info["variable_category"]):
            risk_flags.append("KEY_INTEGRITY_IMPACT_POSSIBLE")

        if not best.empty and col in best.index:
            best_row = best.loc[col]
            match_rate = best_row["match_rate"]
            mismatch_count = int(best_row["mismatched_rows"])
            formula = best_row["candidate_formula_description"]
            formula_id = best_row["candidate_formula_id"]
            observation_window = best_row["observation_window"]
            denominator = best_row["denominator"]
            zero_policy = best_row["zero_denominator_policy"]
            missing_policy = best_row["missing_policy"]
            date_basis = best_row["date_basis"]
            sample_mismatch_keys = " | ".join(
                [str(best_row.get("sample_mismatch_1", "")), str(best_row.get("sample_mismatch_2", "")), str(best_row.get("sample_mismatch_3", ""))]
            ).strip(" |")
            confidence = best_row["confidence_level"] or "UNKNOWN"
            reason = best_row["reason"]
        else:
            match_rate = np.nan
            mismatch_count = np.nan
            formula = ""
            formula_id = ""
            observation_window = ""
            denominator = ""
            zero_policy = ""
            missing_policy = ""
            date_basis = ""
            sample_mismatch_keys = ""
            confidence = "UNKNOWN"
            reason = "No reconstruction candidate was generated from the six allowed files."

        if col in ["reg_date", "end_date"]:
            confidence = "ERROR"
            which = "reg" if col == "reg_date" else "end"
            transform_rate = date_summary[f"{which}_suspected_transform_rate"]
            source_match_rate = date_summary[f"{which}_match_rate"]
            reason = (
                f"Membership_v2.csv date equality rate={source_match_rate:.6f}; tested suspected day/year-suffix transformation rate={transform_rate:.6f}."
            )

        teammate_check_needed = confidence in ["UNKNOWN", "ERROR"] or bool(set(risk_flags) & {"ZERO_DENOMINATOR_POLICY_NEEDS_CONFIRMATION", "POLICY_DEPENDENT_LEAKAGE_RISK", "VARIABLE_NAME_RISK"})
        if confidence == "CONFIRMED":
            recommended = formula
        elif confidence == "STRONG_INFERENCE":
            recommended = "Recommended candidate, not source-code confirmed: " + formula
        elif col in ["reg_date", "end_date"]:
            recommended = "Use Membership_v2.csv original date; repair or regenerate master date column."
        else:
            recommended = "Human confirmation required before standard definition is finalized."

        row = {
            "master_column": col,
            "v3_variable_name": col if col in v3_names else "",
            "in_master": True,
            "in_v3_definition": col in v3_names,
            "variable_category": info["variable_category"],
            "source_file": info["source_file"],
            "source_columns": info["source_columns"],
            "processing_type": info["processing_type"],
            "inferred_formula": formula,
            "calculation_unit": "per USER_KEY",
            "key_used_for_merge": KEY,
            "date_basis": date_basis,
            "observation_window": observation_window,
            "denominator_definition": denominator,
            "zero_denominator_handling": zero_policy,
            "missing_value_handling": missing_policy,
            "expected_dtype": "",
            "actual_master_dtype": str(master[col].dtype),
            "master_missing_count": int(master[col].isna().sum()),
            "master_unique_count": int(master[col].nunique(dropna=True)),
            "reconstruction_possible": col in best.index if not best.empty else False,
            "best_matching_candidate_formula": formula_id,
            "match_rate": match_rate,
            "mismatch_count": mismatch_count,
            "sample_mismatch_keys": sample_mismatch_keys,
            "confidence_level": confidence,
            "confidence_reason": reason,
            "risk_flags": "; ".join(sorted(set(risk_flags))),
            "recommended_standard_definition": recommended,
            "recommended_safe_column_name": safe_lookup.get(col, col),
            "teammate_check_needed": teammate_check_needed,
            "notes": "",
        }
        rows.append(row)
        if risk_flags:
            risky_rows.append(row.copy())

    lineage = pd.DataFrame(rows)
    unresolved = lineage[lineage["confidence_level"].isin(["UNKNOWN", "ERROR"])].copy()
    issue_types = []
    for _, row in unresolved.iterrows():
        flags = row["risk_flags"]
        if row["confidence_level"] == "ERROR" and "MASTER_DATE_ERROR" in flags:
            issue_types.append("DATE_ERROR")
        elif "VARIABLE_NAME_RISK" in flags:
            issue_types.append("VARIABLE_NAME_RISK")
        elif "ZERO_DENOMINATOR" in flags:
            issue_types.append("ZERO_DENOMINATOR_AMBIGUITY")
        elif row["match_rate"] is not np.nan and pd.notna(row["match_rate"]):
            issue_types.append("LOW_MATCH_RATE")
        else:
            issue_types.append("SOURCE_NOT_FOUND")
    unresolved_out = pd.DataFrame(
        {
            "variable": unresolved["master_column"],
            "issue_type": issue_types,
            "why_unresolved": unresolved["confidence_reason"],
            "tested_candidates": unresolved["best_matching_candidate_formula"],
            "best_match_rate": unresolved["match_rate"],
            "required_human_decision": "Confirm source formula or regenerate master from agreed script.",
            "recommended_next_action": unresolved["recommended_standard_definition"],
        }
    )
    risky = pd.DataFrame(risky_rows)
    return lineage, unresolved_out, risky


def make_summary(lineage: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for level, group in lineage.groupby("confidence_level", dropna=False):
        rows.append(
            {
                "summary_type": "confidence_level",
                "group": level,
                "count": len(group),
                "variables": "; ".join(group["master_column"].astype(str).tolist()),
            }
        )
    exploded = []
    for _, row in lineage.iterrows():
        for cat in str(row["variable_category"]).split("; "):
            exploded.append((cat, row["master_column"]))
    cat_df = pd.DataFrame(exploded, columns=["category", "variable"])
    for cat, group in cat_df.groupby("category"):
        rows.append(
            {
                "summary_type": "variable_category",
                "group": cat,
                "count": group["variable"].nunique(),
                "variables": "; ".join(group["variable"].astype(str).tolist()),
            }
        )
    return pd.DataFrame(rows)


def write_report(
    profiles: list[dict],
    date_summary: dict,
    date_audit: pd.DataFrame,
    key_audit: pd.DataFrame,
    lineage: pd.DataFrame,
    unresolved: pd.DataFrame,
    risky: pd.DataFrame,
) -> str:
    counts = lineage["confidence_level"].value_counts().to_dict()
    profile_by_label = {p["label"]: p for p in profiles}
    examples = date_audit.loc[~(date_audit["reg_date_equal"] & date_audit["end_date_equal"])].head(10)
    date_example_lines = []
    for _, row in examples.iterrows():
        date_example_lines.append(
            f"- USER_KEY={format_value(row[KEY])}: reg {row['membership_reg_date']} -> {row['master_reg_date']}, end {row['membership_end_date']} -> {row['master_end_date']}"
        )

    top_risks = [
        "master reg_date/end_date are not reliable and match the tested day/year-suffix transformation pattern.",
        "Prediction-time policy is not defined in the six audited files, so watch/content variables carry policy-dependent leakage risk.",
        "Ratio variables require explicit zero-denominator policy confirmation before script regeneration.",
        "Weekly watch-time family is structurally redundant and needs feature redundancy audit before modeling.",
        "Movie_Master_v2 duplicate MOVIE_NUM policy can affect content-derived variables if conflicting duplicate metadata is used.",
    ]
    report = []
    report.append("# Variable Lineage Audit Report")
    report.append("")
    report.append("## 1. Executive Summary")
    report.append(f"- Master file: {profile_by_label['master']['row_count']} rows, {profile_by_label['master']['column_count']} columns.")
    report.append(
        "- Source files: "
        + "; ".join(
            [
                f"{p['filename']}={p['row_count']} rows/{p['column_count']} columns"
                for p in profiles
                if p["label"] in ["membership", "mapping", "view", "movie"]
            ]
        )
        + "."
    )
    report.append(
        f"- Confidence counts: CONFIRMED={counts.get('CONFIRMED', 0)}, STRONG_INFERENCE={counts.get('STRONG_INFERENCE', 0)}, UNKNOWN={counts.get('UNKNOWN', 0)}, ERROR={counts.get('ERROR', 0)}."
    )
    report.append("- Confirmed items are based on source-to-master value reconstruction, not on the v3 reference description alone.")
    report.append("- Unconfirmed items are left as UNKNOWN or ERROR rather than being forced into a formula.")
    report.append("- Largest risks:")
    report.extend([f"  - {risk}" for risk in top_risks])

    report.append("")
    report.append("## 2. Files Audited")
    for p in profiles:
        report.append(f"### {p['filename']}")
        report.append(f"- Encoding: {p['encoding']}")
        report.append(f"- Shape: {p['row_count']} rows x {p['column_count']} columns")
        report.append(f"- Columns: {', '.join(p['columns'])}")
        report.append(f"- Key unique counts: {p['key_unique_counts']}")
        report.append(f"- Exact duplicate count: {p['exact_duplicate_count']}")

    report.append("")
    report.append("## 3. Critical Finding: master reg_date/end_date error")
    report.append(f"- reg_date equality rate against Membership_v2.csv: {date_summary['reg_match_rate']:.6f}")
    report.append(f"- end_date equality rate against Membership_v2.csv: {date_summary['end_match_rate']:.6f}")
    report.append(f"- Tested suspected reg_date transformation rate: {date_summary['reg_suspected_transform_rate']:.6f}")
    report.append(f"- Tested suspected end_date transformation rate: {date_summary['end_suspected_transform_rate']:.6f}")
    report.append("- Examples:")
    report.extend(date_example_lines)
    report.append("- Reason master dates must not be used: the audited master dates do not equal the Membership_v2.csv dates and match a systematic day/year-suffix swap pattern.")
    report.append("- Date-derived reconstruction in this audit uses Membership_v2.csv reg_date and end_date.")

    report.append("")
    report.append("## 4. Key Integrity Findings")
    for _, row in key_audit.iterrows():
        report.append(f"- {row['check_name']}: {row['result']} / severity={row['severity']} / issue_count={row['issue_count']}. {row['note']}")

    report.append("")
    report.append("## 5. Variable Lineage Summary")
    for level in ["CONFIRMED", "STRONG_INFERENCE", "UNKNOWN", "ERROR"]:
        report.append(f"- {level}: {counts.get(level, 0)}")
    cat_counts = lineage.assign(category=lineage["variable_category"].str.split("; ")).explode("category").groupby("category")["master_column"].nunique()
    for category, count in cat_counts.sort_index().items():
        report.append(f"- {category}: {count}")

    report.append("")
    report.append("## 6. Membership-derived Variables")
    mem = lineage[lineage["source_file"].str.contains("Membership_v2.csv", na=False)]
    for level in ["CONFIRMED", "STRONG_INFERENCE", "UNKNOWN", "ERROR"]:
        vars_ = mem.loc[mem["confidence_level"].eq(level), "master_column"].tolist()
        report.append(f"- {level}: {', '.join(vars_) if vars_ else 'None'}")

    report.append("")
    report.append("## 7. Watch-history-derived Variables")
    watch = lineage[lineage["variable_category"].str.contains("watch|weekly", case=False, na=False)]
    report.append("- Observation-window and weekly definitions were compared through candidate formulas in variable_reconstruction_check.csv.")
    for level in ["CONFIRMED", "STRONG_INFERENCE", "UNKNOWN", "ERROR"]:
        vars_ = watch.loc[watch["confidence_level"].eq(level), "master_column"].tolist()
        report.append(f"- {level}: {', '.join(vars_) if vars_ else 'None'}")

    report.append("")
    report.append("## 8. Content-derived Variables")
    content = lineage[lineage["variable_category"].str.contains("content|genre|movie", case=False, na=False)]
    report.append("- Movie_Master dedup candidates tested: exact duplicate removal, MOVIE_NUM first, latest release month, mode metadata, and no-dedup join.")
    for level in ["CONFIRMED", "STRONG_INFERENCE", "UNKNOWN", "ERROR"]:
        vars_ = content.loc[content["confidence_level"].eq(level), "master_column"].tolist()
        report.append(f"- {level}: {', '.join(vars_) if vars_ else 'None'}")

    report.append("")
    report.append("## 9. Ratio and Zero Denominator Policies")
    ratio = lineage[lineage["risk_flags"].str.contains("ZERO_DENOMINATOR", na=False)]
    for _, row in ratio.iterrows():
        report.append(f"- {row['master_column']}: denominator={row['denominator_definition']}; zero_policy={row['zero_denominator_handling']}; confidence={row['confidence_level']}")

    report.append("")
    report.append("## 10. Risk Register")
    report.append("- Date error: master reg_date/end_date are ERROR and require repair.")
    report.append("- Key duplicates: see key_integrity_audit.csv for USER_KEY/USER_NUM coverage and duplicate findings.")
    report.append("- Metadata duplicates: Movie_Master_v2 duplicate MOVIE_NUM handling is tracked in key_integrity_audit.csv and reconstruction candidates.")
    report.append("- Variable name risk: columns with %, parentheses, slash, Korean, spaces, or special characters are listed in risky_variables sheet.")
    report.append("- Multicollinearity risk: weekly watch-time family variables are flagged.")
    report.append("- Target leakage possibility: is_repurchase is target-only; watch/content variables are policy-dependent on prediction timing.")
    report.append("이 변수들은 후보 변수로는 유지할 수 있으나, 모델링 전 feature redundancy audit 또는 VIF/correlation/permutation importance/SHAP stability 검사를 통해 중복성을 검토해야 한다.")

    report.append("")
    report.append("## 11. Recommended Standard Definitions")
    report.append("- CONFIRMED variables can use the selected formula in variable_lineage_audit.xlsx.")
    report.append("- STRONG_INFERENCE variables should be treated as recommended candidates, not as source-code-confirmed facts.")
    report.append("- UNKNOWN variables require teammate confirmation of the original generating logic.")
    report.append("- ERROR date columns should be repaired from Membership_v2.csv before regenerating date-derived features.")

    report.append("")
    report.append("## 12. Next Actions")
    report.append("- Team members should review UNKNOWN and ERROR variables in unresolved_variables.csv.")
    report.append("- The team should define the prediction point before using watch/content features as model inputs.")
    report.append("- The team should standardize zero-denominator behavior for all ratio variables.")
    report.append("- Before regenerating master, repair date parsing and document Movie_Master dedup policy.")
    return "\n".join(report) + "\n"


def write_outputs(
    profiles,
    reconstruction,
    lineage,
    summary,
    date_audit,
    key_audit,
    unresolved,
    risky,
    v3_compare,
    report,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    reconstruction.to_csv(OUTPUT_DIR / "variable_reconstruction_check.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(OUTPUT_DIR / "variable_lineage_summary.csv", index=False, encoding="utf-8-sig")
    date_audit.to_csv(OUTPUT_DIR / "date_error_audit.csv", index=False, encoding="utf-8-sig")
    key_audit.to_csv(OUTPUT_DIR / "key_integrity_audit.csv", index=False, encoding="utf-8-sig")
    unresolved.to_csv(OUTPUT_DIR / "unresolved_variables.csv", index=False, encoding="utf-8-sig")
    lineage.to_csv(OUTPUT_DIR / "variable_lineage.csv", index=False, encoding="utf-8-sig")
    risky.to_csv(OUTPUT_DIR / "risky_variables.csv", index=False, encoding="utf-8-sig")
    v3_compare.to_csv(OUTPUT_DIR / "v3_master_comparison.csv", index=False, encoding="utf-8-sig")

    reconstruction[reconstruction["source_files_used"].str.contains("Membership_v2.csv", na=False)].to_csv(
        OUTPUT_DIR / "membership_column_match_check.csv", index=False, encoding="utf-8-sig"
    )
    reconstruction[reconstruction["variable"].str.contains("watch|recency|cold|gap|daily|session|active", case=False, na=False)].to_csv(
        OUTPUT_DIR / "watch_feature_recalculation_check.csv", index=False, encoding="utf-8-sig"
    )
    reconstruction[reconstruction["source_files_used"].str.contains("Movie_Master_v2.csv", na=False)].to_csv(
        OUTPUT_DIR / "content_feature_recalculation_check.csv", index=False, encoding="utf-8-sig"
    )
    reconstruction[reconstruction["variable"].str.contains("ratio|drama|thriller|horror|comedy|romance|documentary|historical|action|family|fantasy|other", case=False, na=False)].to_csv(
        OUTPUT_DIR / "genre_feature_recalculation_check.csv", index=False, encoding="utf-8-sig"
    )

    with pd.ExcelWriter(OUTPUT_DIR / "variable_lineage_audit.xlsx", engine="openpyxl") as writer:
        lineage.to_excel(writer, sheet_name="variable_lineage", index=False)
        reconstruction.to_excel(writer, sheet_name="reconstruction_checks", index=False)
        date_audit.to_excel(writer, sheet_name="date_error_audit", index=False)
        key_audit.to_excel(writer, sheet_name="key_integrity_audit", index=False)
        unresolved.to_excel(writer, sheet_name="unresolved_variables", index=False)
        risky.to_excel(writer, sheet_name="risky_variables", index=False)
        v3_compare.to_excel(writer, sheet_name="v3_master_comparison", index=False)

    (OUTPUT_DIR / "audit_report.md").write_text(report, encoding="utf-8")
    log("\n> Output Files")
    for name in [
        "variable_lineage_audit.xlsx",
        "variable_reconstruction_check.csv",
        "variable_lineage_summary.csv",
        "date_error_audit.csv",
        "key_integrity_audit.csv",
        "unresolved_variables.csv",
        "audit_report.md",
        "run_log.txt",
    ]:
        log(f"- {OUTPUT_DIR / name}")
    (OUTPUT_DIR / "run_log.txt").write_text("\n".join(RUN_LOG) + "\n", encoding="utf-8")


def main() -> None:
    ensure_input_files()
    loaded = {}
    encodings = {}
    for label, path in FILES.items():
        loaded[label], encodings[label] = read_csv_checked(path)

    master = loaded["master"]
    membership = loaded["membership"]
    mapping = loaded["mapping"]
    view = loaded["view"]
    movie = loaded["movie"]
    v3 = loaded["v3"]

    required_columns = {
        "master": [KEY],
        "membership": [KEY, "reg_date", "end_date"],
        "mapping": [KEY, USER_NUM],
        "view": [USER_NUM, "MOVIE_NUM", WATCH_TIME, "watch_day", "watch_seq"],
        "movie": ["MOVIE_NUM", "movie_title", "ott_release_month", "category"],
        "v3": ["변수명"],
    }
    for label, columns in required_columns.items():
        missing = [col for col in columns if col not in loaded[label].columns]
        if missing:
            fail(f"{FILES[label].name} is missing required columns: {missing}")

    profiles = [
        profile_dataframe(label, FILES[label].name, loaded[label], encodings[label])
        for label in ["master", "membership", "mapping", "view", "movie", "v3"]
    ]
    add_specific_profiles(master, membership, mapping, view, movie)

    key_audit = make_key_integrity_audit(master, membership, mapping, view, movie)
    date_audit, date_summary = make_date_error_audit(master, membership)
    v3_compare = make_v3_master_comparison(master, v3)

    membership_u, mapping_u_by_key, view_base, movie_base = prepare_source_tables(master, membership, mapping, view, movie)
    compare_membership_family(master, membership_u, mapping_u_by_key)
    compare_watch_family(master, view_base)
    compare_weekly_family(master, view_base)
    compare_content_family(master, view_base, movie_base)

    reconstruction = finalize_reconstruction_checks()
    lineage, unresolved, risky = build_lineage_tables(
        master,
        membership,
        mapping,
        view,
        movie,
        v3_compare,
        reconstruction,
        date_summary,
        key_audit,
    )
    summary = make_summary(lineage)
    report = write_report(profiles, date_summary, date_audit, key_audit, lineage, unresolved, risky)
    write_outputs(profiles, reconstruction, lineage, summary, date_audit, key_audit, unresolved, risky, v3_compare, report)


if __name__ == "__main__":
    main()
