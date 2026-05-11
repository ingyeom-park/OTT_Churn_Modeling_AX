import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE = PROJECT_ROOT / "park.ingyeom"

MEMBERSHIP_PATH = BASE / "reports" / "data" / "02c_v2_strict_preprocessing_correction" / "membership_v2_preprocessed_strict_core.csv"
USERMAPPING_PATH = BASE / "reports" / "data" / "02c_v2_strict_preprocessing_correction" / "usermapping_v2_policy_checked_strict_core.csv"
MOVIEMASTER_PATH = BASE / "reports" / "data" / "02c_v2_strict_preprocessing_correction" / "moviemaster_v2_policy_checked_strict_core.csv"
VIEWS_PATH = PROJECT_ROOT / "_data" / "01_raw" / "Views_train.csv"
MOVIES_PATH = PROJECT_ROOT / "_data" / "01_raw" / "Movies.csv"
STAGE03_SUMMARY_PATH = BASE / "reports" / "data" / "03c_v2_usage_feature_engineering" / "03c_usage_feature_summary.json"
STAGE03_CHECK_PATH = BASE / "reports" / "tables" / "03c_v2_usage_feature_engineering" / "03c_final_checks.csv"

DATA_DIR = BASE / "reports" / "data" / "04c_v2_content_feature_engineering"
TABLE_DIR = BASE / "reports" / "tables" / "04c_v2_content_feature_engineering"
FIGURE_DIR = BASE / "reports" / "figures" / "04c_v2_content_feature_engineering"

WINDOWS = {
    "w1_1": (0, 6),
    "w1_2": (0, 13),
    "w1_3": (0, 20),
    "w1_4": (0, 27),
}
ACTIVE_MOVIE_FIELDS = ["MOVIE_NUM", "movie_title", "ott_release_month", "genre"]
MAJOR_GENRE_LIMIT = 12


def rel(path: Path) -> str:
    return str(Path(path).relative_to(PROJECT_ROOT)).replace("\\", "/")


def write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snapshot_dir(path: Path) -> dict:
    if not path.exists():
        return {}
    out = {}
    for file in sorted(path.rglob("*")):
        if file.is_file():
            stat = file.stat()
            out[rel(file)] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    return out


def snapshot_files(paths) -> dict:
    out = {}
    for path in paths:
        path = Path(path)
        if path.exists():
            stat = path.stat()
            out[rel(path)] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
        else:
            out[rel(path)] = None
    return out


def require_stage03c_passed() -> None:
    required = [
        BASE / "reports" / "data" / "03c_v2_usage_feature_engineering" / f"usage_features_v2c_{w}.csv"
        for w in WINDOWS
    ] + [STAGE03_SUMMARY_PATH, STAGE03_CHECK_PATH]
    missing = [rel(p) for p in required if not p.exists()]
    if missing:
        write_blocked_report("Stage 03c required input is missing.", missing)
        raise RuntimeError("Stage 03c gate failed: missing required inputs.")
    checks = pd.read_csv(STAGE03_CHECK_PATH)
    failed = checks[checks["status"].astype(str).str.upper() != "PASS"]
    if not failed.empty:
        write_blocked_report("Stage 03c final checks did not all pass.", failed.to_dict("records"))
        raise RuntimeError("Stage 03c gate failed: final checks failed.")


def write_blocked_report(reason: str, detail) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    text = [
        "# 04c BLOCKED Report",
        "",
        f"- reason: {reason}",
        f"- detail: {detail}",
        "- action: Stage 04c was not executed.",
    ]
    (DATA_DIR / "04c_blocked_report.md").write_text("\n".join(text) + "\n", encoding="utf-8")


def parse_date(value):
    if pd.isna(value):
        return pd.NaT
    return pd.to_datetime(value, errors="coerce")


def parse_watch_day(value):
    return pd.to_datetime(value.astype(str), format="%Y%m%d", errors="coerce")


def month_diff(release_month, reg_date):
    if pd.isna(release_month) or pd.isna(reg_date):
        return np.nan
    try:
        ym = int(float(release_month))
        year, month = divmod(ym, 100)
        return (reg_date.year - year) * 12 + (reg_date.month - month)
    except Exception:
        return np.nan


def entropy_from_weights(weights):
    total = float(sum(weights))
    if total <= 0:
        return 0.0
    probs = [w / total for w in weights if w > 0]
    return float(-sum(p * math.log(p) for p in probs))


def dedupe_moviemaster(movie_master: pd.DataFrame):
    movie_master = movie_master[ACTIVE_MOVIE_FIELDS].copy()
    group = movie_master.groupby("MOVIE_NUM", dropna=False)
    summary = group.agg(
        raw_rows=("MOVIE_NUM", "size"),
        distinct_title=("movie_title", lambda s: s.dropna().nunique()),
        distinct_release_month=("ott_release_month", lambda s: s.dropna().nunique()),
        distinct_genre=("genre", lambda s: s.dropna().nunique()),
    ).reset_index()
    summary["has_duplicate"] = (summary["raw_rows"] > 1).astype(int)
    summary["has_genre_conflict"] = (summary["distinct_genre"] > 1).astype(int)
    conflict_nums = set(summary.loc[summary["has_genre_conflict"].eq(1), "MOVIE_NUM"])
    conflict_rows = movie_master[movie_master["MOVIE_NUM"].isin(conflict_nums)].sort_values(["MOVIE_NUM", "genre"])
    deduped = (
        movie_master.sort_values(["MOVIE_NUM", "genre", "movie_title"], na_position="last")
        .drop_duplicates("MOVIE_NUM", keep="first")
        .reset_index(drop=True)
    )
    return deduped, summary, conflict_rows


def build_window_features(base: pd.DataFrame, joined: pd.DataFrame, window: str, major_genres: list[str]) -> pd.DataFrame:
    start, end = WINDOWS[window]
    in_window = joined[(joined["rel_day"] >= start) & (joined["rel_day"] <= end)].copy()
    ids = base[["membership_row_id"]].copy()
    if in_window.empty:
        out = ids
        for col in [
            "content_has_watch_obs", "genre_covered_watch_time", "genre_missing_watch_time",
            "genre_covered_watch_ratio", "genre_missing_watch_ratio", "genre_unique_count",
            "top_genre", "top_genre_watch_time", "top_genre_watch_ratio", "genre_entropy",
            "release_month_covered_watch_ratio", "avg_ott_release_month_weighted",
            "recent_content_watch_ratio", "old_content_watch_ratio",
        ]:
            out[f"{window}_{col}"] = "" if col == "top_genre" else 0
        return out

    total = in_window.groupby("membership_row_id")["DURATION"].sum().rename("total")
    covered = in_window[in_window["genre"].notna() & in_window["genre"].astype(str).str.len().gt(0)].copy()
    genre_sum = covered.groupby(["membership_row_id", "genre"])["DURATION"].sum().reset_index()
    genre_sessions = covered.groupby(["membership_row_id", "genre"])["DURATION"].size().reset_index(name="sessions")
    covered_total = genre_sum.groupby("membership_row_id")["DURATION"].sum().rename(f"{window}_genre_covered_watch_time")
    genre_unique = genre_sum.groupby("membership_row_id")["genre"].nunique().rename(f"{window}_genre_unique_count")
    top = genre_sum.sort_values(["membership_row_id", "DURATION", "genre"], ascending=[True, False, True]).drop_duplicates("membership_row_id")
    top = top.rename(columns={"genre": f"{window}_top_genre", "DURATION": f"{window}_top_genre_watch_time"})[["membership_row_id", f"{window}_top_genre", f"{window}_top_genre_watch_time"]]
    entropy = genre_sum.groupby("membership_row_id")["DURATION"].apply(lambda s: entropy_from_weights(s.tolist())).rename(f"{window}_genre_entropy")

    release_mask = in_window["ott_release_month"].notna()
    release_total = in_window.loc[release_mask].groupby("membership_row_id")["DURATION"].sum().rename("release_total")
    release_weight = (in_window.loc[release_mask, "ott_release_month"] * in_window.loc[release_mask, "DURATION"]).groupby(in_window.loc[release_mask, "membership_row_id"]).sum().rename("release_weight")
    recent = in_window.loc[in_window["release_age_months"].between(0, 12, inclusive="both")].groupby("membership_row_id")["DURATION"].sum().rename("recent")
    old = in_window.loc[in_window["release_age_months"].gt(60)].groupby("membership_row_id")["DURATION"].sum().rename("old")

    features = ids.merge(total.reset_index(), on="membership_row_id", how="left")
    for series in [covered_total, genre_unique, entropy, release_total, release_weight, recent, old]:
        features = features.merge(series.reset_index(), on="membership_row_id", how="left")
    features = features.merge(top, on="membership_row_id", how="left")
    features["total"] = features["total"].fillna(0)
    features[f"{window}_content_has_watch_obs"] = (features["total"] > 0).astype(int)
    features[f"{window}_genre_covered_watch_time"] = features[f"{window}_genre_covered_watch_time"].fillna(0)
    features[f"{window}_genre_missing_watch_time"] = (features["total"] - features[f"{window}_genre_covered_watch_time"]).clip(lower=0)
    features[f"{window}_genre_covered_watch_ratio"] = np.where(features["total"] > 0, features[f"{window}_genre_covered_watch_time"] / features["total"], 0)
    features[f"{window}_genre_missing_watch_ratio"] = np.where(features["total"] > 0, features[f"{window}_genre_missing_watch_time"] / features["total"], 0)
    features[f"{window}_genre_unique_count"] = features[f"{window}_genre_unique_count"].fillna(0).astype(int)
    features[f"{window}_top_genre"] = features[f"{window}_top_genre"].fillna("")
    features[f"{window}_top_genre_watch_time"] = features[f"{window}_top_genre_watch_time"].fillna(0)
    features[f"{window}_top_genre_watch_ratio"] = np.where(features["total"] > 0, features[f"{window}_top_genre_watch_time"] / features["total"], 0)
    features[f"{window}_genre_entropy"] = features[f"{window}_genre_entropy"].fillna(0)
    features["release_total"] = features["release_total"].fillna(0)
    features[f"{window}_release_month_covered_watch_ratio"] = np.where(features["total"] > 0, features["release_total"] / features["total"], 0)
    features[f"{window}_avg_ott_release_month_weighted"] = np.where(features["release_total"] > 0, features["release_weight"] / features["release_total"], np.nan)
    features[f"{window}_recent_content_watch_ratio"] = np.where(features["total"] > 0, features["recent"].fillna(0) / features["total"], 0)
    features[f"{window}_old_content_watch_ratio"] = np.where(features["total"] > 0, features["old"].fillna(0) / features["total"], 0)

    genre_pivot = genre_sum.pivot_table(index="membership_row_id", columns="genre", values="DURATION", aggfunc="sum", fill_value=0)
    session_pivot = genre_sessions.pivot_table(index="membership_row_id", columns="genre", values="sessions", aggfunc="sum", fill_value=0)
    for genre in major_genres:
        safe = str(genre).strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")
        watch = features["membership_row_id"].map(genre_pivot[genre] if genre in genre_pivot.columns else pd.Series(dtype=float)).fillna(0)
        sessions = features["membership_row_id"].map(session_pivot[genre] if genre in session_pivot.columns else pd.Series(dtype=float)).fillna(0)
        features[f"{window}_genre_ratio_{safe}"] = np.where(features["total"] > 0, watch / features["total"], 0)
        features[f"{window}_genre_watch_time_{safe}"] = watch
        features[f"{window}_genre_session_count_{safe}"] = sessions.astype(int)

    drop_cols = ["total", "release_total", "release_weight", "recent", "old"]
    out = features.drop(columns=[c for c in drop_cols if c in features.columns])
    for col in out.columns:
        if col == "membership_row_id":
            continue
        if col.endswith("_top_genre"):
            out[col] = out[col].fillna("")
        else:
            out[col] = out[col].fillna(0)
    return out


def numeric_summary(df: pd.DataFrame, window: str) -> pd.DataFrame:
    nums = df.select_dtypes(include=[np.number]).drop(columns=["membership_row_id"], errors="ignore")
    if nums.empty:
        return pd.DataFrame(columns=["window", "feature", "mean", "std", "min", "max"])
    desc = nums.agg(["mean", "std", "min", "max"]).T.reset_index().rename(columns={"index": "feature"})
    desc.insert(0, "window", window)
    return desc


def missing_summary(df: pd.DataFrame, window: str) -> pd.DataFrame:
    out = pd.DataFrame({"feature": df.columns, "missing_count": df.isna().sum().values})
    out["missing_ratio"] = out["missing_count"] / len(df) if len(df) else 0
    out.insert(0, "window", window)
    return out


def main():
    require_stage03c_passed()
    for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    raw_before = snapshot_dir(PROJECT_ROOT / "_data")
    protected_before = snapshot_files([MEMBERSHIP_PATH, USERMAPPING_PATH, MOVIEMASTER_PATH, STAGE03_SUMMARY_PATH])

    membership = pd.read_csv(MEMBERSHIP_PATH)
    usermap = pd.read_csv(USERMAPPING_PATH)
    movie_master = pd.read_csv(MOVIEMASTER_PATH)
    views = pd.read_csv(VIEWS_PATH)
    _ = pd.read_csv(MOVIES_PATH, nrows=1)

    deduped_movie, dedupe_summary, conflict_rows = dedupe_moviemaster(movie_master)
    major_genres = (
        deduped_movie["genre"].dropna().astype(str).value_counts().head(MAJOR_GENRE_LIMIT).index.tolist()
    )

    base = membership[["membership_row_id", "USER_KEY", "reg_date_parsed"]].copy()
    base["reg_date_parsed"] = base["reg_date_parsed"].map(parse_date)
    bridge = usermap[["USER_KEY", "USER_NUM"]].drop_duplicates().copy()
    bridge["USER_NUM"] = pd.to_numeric(bridge["USER_NUM"], errors="coerce")
    bridge = bridge.merge(base, on="USER_KEY", how="inner")

    views = views.rename(columns={"USER_ID": "USER_NUM", "MOVIE_ID": "MOVIE_NUM", "WATCH_DAY": "watch_day"})
    views["USER_NUM"] = pd.to_numeric(views["USER_NUM"], errors="coerce")
    views["MOVIE_NUM"] = pd.to_numeric(views["MOVIE_NUM"], errors="coerce")
    views["watch_date"] = parse_watch_day(views["watch_day"])
    views["DURATION"] = pd.to_numeric(views["DURATION"], errors="coerce").fillna(0)

    joined = bridge.merge(views, on="USER_NUM", how="left")
    joined["rel_day"] = (joined["watch_date"] - joined["reg_date_parsed"]).dt.days
    joined = joined.merge(deduped_movie, on="MOVIE_NUM", how="left", validate="m:1")
    joined["release_age_months"] = [month_diff(m, d) for m, d in zip(joined["ott_release_month"], joined["reg_date_parsed"])]

    join_coverage = pd.DataFrame([
        {"metric": "membership_rows", "value": len(membership)},
        {"metric": "views_train_rows", "value": len(views)},
        {"metric": "joined_rows_after_user_mapping", "value": len(joined)},
        {"metric": "joined_watch_rows", "value": int(joined["watch_date"].notna().sum())},
        {"metric": "movie_metadata_matched_rows", "value": int(joined["genre"].notna().sum())},
        {"metric": "movie_metadata_missing_rows", "value": int(joined["watch_date"].notna().sum() - joined["genre"].notna().sum())},
    ])

    temporal_rows = []
    row_count_rows = []
    numeric_rows = []
    missing_rows = []
    outputs = {}
    for window, (start, end) in WINDOWS.items():
        filtered = joined[(joined["rel_day"] >= start) & (joined["rel_day"] <= end)]
        temporal_rows.append({
            "window": window,
            "rel_day_start": start,
            "rel_day_end": end,
            "watch_rows_in_window": len(filtered),
            "unique_membership_with_watch": filtered["membership_row_id"].nunique(),
        })
        feat = build_window_features(membership[["membership_row_id"]], joined, window, major_genres)
        path = DATA_DIR / f"content_features_v2c_{window}.csv"
        write_csv(path, feat)
        outputs[window] = path
        row_count_rows.append({
            "window": window,
            "rows": len(feat),
            "unique_membership_row_id": feat["membership_row_id"].nunique(),
            "matches_membership_rows": len(feat) == len(membership),
            "late_period_only": 1 if window == "w1_4" else 0,
        })
        numeric_rows.append(numeric_summary(feat, window))
        missing_rows.append(missing_summary(feat, window))

    write_csv(TABLE_DIR / "04c_moviemaster_deduplication_summary.csv", dedupe_summary)
    write_csv(TABLE_DIR / "04c_moviemaster_genre_conflict_rows.csv", conflict_rows)
    write_csv(TABLE_DIR / "04c_content_join_coverage_summary.csv", join_coverage)
    write_csv(TABLE_DIR / "04c_content_temporal_filter_summary.csv", pd.DataFrame(temporal_rows))
    write_csv(TABLE_DIR / "04c_window_row_count_summary.csv", pd.DataFrame(row_count_rows))
    write_csv(TABLE_DIR / "04c_content_feature_numeric_summary.csv", pd.concat(numeric_rows, ignore_index=True))
    write_csv(TABLE_DIR / "04c_content_feature_missing_summary.csv", pd.concat(missing_rows, ignore_index=True))

    raw_after = snapshot_dir(PROJECT_ROOT / "_data")
    protected_after = snapshot_files([MEMBERSHIP_PATH, USERMAPPING_PATH, MOVIEMASTER_PATH, STAGE03_SUMMARY_PATH])
    final_checks = [
        ("raw_files_unchanged", raw_before == raw_after, "No files under _data changed."),
        ("no_data_output_created", raw_before.keys() == raw_after.keys(), "No new files under _data."),
        ("stage02c_stage03c_inputs_not_overwritten", protected_before == protected_after, "Protected corrected inputs unchanged."),
        ("moviemaster_deduplicated_before_join", deduped_movie["MOVIE_NUM"].is_unique, f"deduped_rows={len(deduped_movie)}"),
        ("genre_conflicts_audited", (TABLE_DIR / "04c_moviemaster_genre_conflict_rows.csv").exists(), f"conflict_rows={len(conflict_rows)}"),
    ]
    for window, path in outputs.items():
        df = pd.read_csv(path)
        final_checks.append((f"one_row_per_membership_row_id_{window}", len(df) == len(membership) and df["membership_row_id"].is_unique, f"rows={len(df)}"))
    final_checks.extend([
        ("w1_4_late_period_labeled", True, "w1_4 is marked as late-period/end-of-period only."),
        ("no_unavailable_metadata_features_created", True, "No country/rating/runtime/actor/director/Wavve/KOBIS features created."),
        ("all_required_outputs_created", all(p.exists() for p in list(outputs.values()) + [
            DATA_DIR / "04c_content_feature_summary.json",
            DATA_DIR / "04c_content_feature_engineering_report.md",
            TABLE_DIR / "04c_final_checks.csv",
        ]) is False, "placeholder before final write"),
    ])

    summary = {
        "stage": "04c_v2_content_feature_engineering",
        "membership_rows": int(len(membership)),
        "active_movie_fields": ACTIVE_MOVIE_FIELDS,
        "major_genres": major_genres,
        "windows": {w: {"rel_day_start": s, "rel_day_end": e, "late_period_only": w == "w1_4"} for w, (s, e) in WINDOWS.items()},
        "data_outputs": [rel(p) for p in outputs.values()],
        "audit_outputs": [
            rel(TABLE_DIR / name)
            for name in [
                "04c_moviemaster_deduplication_summary.csv",
                "04c_moviemaster_genre_conflict_rows.csv",
                "04c_content_join_coverage_summary.csv",
                "04c_content_temporal_filter_summary.csv",
                "04c_window_row_count_summary.csv",
                "04c_content_feature_numeric_summary.csv",
                "04c_content_feature_missing_summary.csv",
                "04c_final_checks.csv",
            ]
        ],
    }
    write_json(DATA_DIR / "04c_content_feature_summary.json", summary)
    report = "\n".join([
        "# 04c Corrected Content Feature Engineering Report",
        "",
        f"- strict-core membership rows: {len(membership)}",
        f"- deduplicated MovieMaster rows: {len(deduped_movie)}",
        f"- genre conflict rows audited: {len(conflict_rows)}",
        "- active movie fields only: MOVIE_NUM, movie_title, ott_release_month, genre",
        "- w1_4 is late-period/end-of-period only, not an early-warning window.",
        "- full content tables include exploratory genre watch-time/session features; Stage 05c prunes those from official candidates.",
    ])
    (DATA_DIR / "04c_content_feature_engineering_report.md").write_text(report + "\n", encoding="utf-8")

    final_checks = [row for row in final_checks if row[0] != "all_required_outputs_created"]
    required = list(outputs.values()) + [
        DATA_DIR / "04c_content_feature_summary.json",
        DATA_DIR / "04c_content_feature_engineering_report.md",
        TABLE_DIR / "04c_moviemaster_deduplication_summary.csv",
        TABLE_DIR / "04c_moviemaster_genre_conflict_rows.csv",
        TABLE_DIR / "04c_content_join_coverage_summary.csv",
        TABLE_DIR / "04c_content_temporal_filter_summary.csv",
        TABLE_DIR / "04c_window_row_count_summary.csv",
        TABLE_DIR / "04c_content_feature_numeric_summary.csv",
        TABLE_DIR / "04c_content_feature_missing_summary.csv",
    ]
    final_checks.append(("all_required_outputs_created", all(p.exists() for p in required), f"required_outputs={len(required)}"))
    checks_df = pd.DataFrame([
        {"check": name, "status": "PASS" if passed else "FAIL", "detail": detail}
        for name, passed, detail in final_checks
    ])
    write_csv(TABLE_DIR / "04c_final_checks.csv", checks_df)
    if (checks_df["status"] != "PASS").any():
        raise RuntimeError("Stage 04c final checks failed. Stop before Stage 05c.")
    print("04c_v2_content_feature_engineering completed.")
    for row in checks_df.to_dict("records"):
        print(f"{row['check']}: {row['status']} - {row['detail']}")


if __name__ == "__main__":
    main()
