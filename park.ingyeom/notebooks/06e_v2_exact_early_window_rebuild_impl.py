import json
import math
import time
import warnings
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)


RANDOM_STATE = 42
TARGET = "is_repurchase"
ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"

WINDOWS = {
    "w1_1": (0, 6),
    "w1_2": (0, 13),
    "w1_3": (0, 20),
    "w1_4": (0, 27),
}
WEEK_RANGES = {
    "week1": (0, 6),
    "week2": (7, 13),
    "week3": (14, 20),
    "week4": (21, 27),
}

MEMBERSHIP_FEATURES = [
    "product_code",
    "price",
    "billing_method",
    "max_screen",
    "is_promotion",
    "is_user_verified",
    "gender",
    "age",
    "payment_device",
]
CHURN_PREVENTED_FEATURE = "is_churn_prevented"
CATEGORICAL_BASE_FEATURES = {
    "product_code",
    "billing_method",
    "is_promotion",
    "is_user_verified",
    "gender",
    "payment_device",
    "is_churn_prevented",
}

FORBIDDEN_FEATURES = {
    "USER_KEY",
    "USER_NUM",
    "MOVIE_NUM",
    "movie_title",
    "membership_row_id",
    "reg_date",
    "end_date",
    "duration_days",
    "watch_date",
    "watch_day",
    "is_repurchase",
}


def find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "park.ingyeom").exists() and (candidate / "_data").exists():
            return candidate
    raise FileNotFoundError("Project root was not found.")


PROJECT_ROOT = find_project_root(Path.cwd())
BASE = PROJECT_ROOT / "park.ingyeom"
RAW_DIR = PROJECT_ROOT / "_data" / "01_raw"
STAGE02 = BASE / "reports" / "data" / "02_v2_preprocessing_policy"
STAGE05 = BASE / "reports" / "data" / "05_v2_modeling_dataset"
STAGE06_TABLE = BASE / "reports" / "tables" / "06_v2_baseline_modeling"
STAGE06C = BASE / "reports" / "data" / "06c_v2_overfitting_leakage_adversarial_audit"
STAGE05D = BASE / "reports" / "data" / "05d_v2_feature_dictionary"

DATA_DIR = BASE / "reports" / "data" / "06e_v2_exact_early_window_rebuild"
TABLE_DIR = BASE / "reports" / "tables" / "06e_v2_exact_early_window_rebuild"
FIGURE_DIR = BASE / "reports" / "figures" / "06e_v2_exact_early_window_rebuild"
for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(Path(path).relative_to(PROJECT_ROOT)).replace("\\", "/")


def snapshot_paths(paths):
    out = {}
    for path in paths:
        path = Path(path)
        if path.exists() and path.is_file():
            stat = path.stat()
            out[rel(path)] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    return out


def snapshot_dirs(dirs):
    files = []
    for directory in dirs:
        directory = Path(directory)
        if directory.exists():
            files.extend([p for p in directory.rglob("*") if p.is_file()])
    return snapshot_paths(files)


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, df: pd.DataFrame):
    df.to_csv(path, index=False, encoding="utf-8-sig")


def choose_existing(*paths):
    for path in paths:
        path = Path(path)
        if path.exists():
            return path
    raise FileNotFoundError("None of the candidate paths exists: " + ", ".join(str(p) for p in paths))


def safe_float(value, default=np.nan):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def safe_div(n, d):
    return float(n) / float(d) if d else 0.0


def entropy_from_counter(counter: Counter) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    out = 0.0
    for value in counter.values():
        p = value / total
        if p > 0:
            out -= p * math.log2(p)
    return out


def sanitize(value) -> str:
    value = str(value).strip().lower()
    out = []
    for ch in value:
        out.append(ch if ch.isalnum() else "_")
    return "_".join("".join(out).split("_")).strip("_")


def month_diff(watch_date, release_yyyymm):
    if pd.isna(watch_date) or pd.isna(release_yyyymm):
        return None
    release_yyyymm = int(release_yyyymm)
    year = release_yyyymm // 100
    month = release_yyyymm % 100
    if month < 1 or month > 12:
        return None
    return (watch_date.year - year) * 12 + (watch_date.month - month)


def load_json_if_exists(path: Path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


raw_candidates = [
    RAW_DIR / "View_History.csv",
    RAW_DIR / "Views_train.csv",
]
movie_raw_candidates = [
    RAW_DIR / "Movie_Master.csv",
    RAW_DIR / "Movies.csv",
]
raw_view_path = choose_existing(*raw_candidates)
raw_movie_path = choose_existing(*movie_raw_candidates)

input_paths = [
    STAGE02 / "membership_v2_preprocessed.csv",
    STAGE02 / "usermapping_v2_policy_checked.csv",
    STAGE02 / "moviemaster_v2_policy_checked.csv",
    raw_view_path,
    raw_movie_path,
    STAGE05 / "feature_sets_v2.json",
    STAGE06_TABLE / "06_v2_split_membership_row_ids.csv",
    STAGE06C / "06c_adversarial_audit_summary.json",
    STAGE05D / "05d_v2_feature_dictionary_summary.json",
]
raw_before = snapshot_paths([raw_view_path, raw_movie_path])
stage01_09_dirs = []
for base_dir in [BASE / "reports" / "data", BASE / "reports" / "tables", BASE / "reports" / "figures"]:
    if base_dir.exists():
        for child in base_dir.iterdir():
            if child.is_dir() and child.name != "06e_v2_exact_early_window_rebuild":
                stage01_09_dirs.append(child)
stage_before = snapshot_dirs(stage01_09_dirs)
data_before = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())

membership = pd.read_csv(STAGE02 / "membership_v2_preprocessed.csv")
mapping = pd.read_csv(STAGE02 / "usermapping_v2_policy_checked.csv")
movie_policy = pd.read_csv(STAGE02 / "moviemaster_v2_policy_checked.csv")
views = pd.read_csv(raw_view_path)
split = pd.read_csv(STAGE06_TABLE / "06_v2_split_membership_row_ids.csv")
SPLIT_COL = "split" if "split" in split.columns else "holdout_split"
if SPLIT_COL not in split.columns:
    raise ValueError("Stage 06 split file must contain either split or holdout_split.")
stage06c_summary = load_json_if_exists(STAGE06C / "06c_adversarial_audit_summary.json")
feature_dictionary_summary = load_json_if_exists(STAGE05D / "05d_v2_feature_dictionary_summary.json")

if "membership_row_id" not in membership.columns:
    raise ValueError("membership_v2_preprocessed.csv must contain membership_row_id.")
if membership["membership_row_id"].duplicated().any():
    raise ValueError("membership_v2_preprocessed.csv has duplicated membership_row_id.")

membership = membership.copy()
membership["reg_dt"] = pd.to_datetime(membership["reg_date"], format="%y-%m-%d", errors="coerce")
membership["end_dt"] = pd.to_datetime(membership["end_date"], format="%y-%m-%d", errors="coerce")
membership["target_y"] = membership[TARGET].map({"Y": 1, "N": 0})

view_col_map = {}
if "USER_ID" in views.columns:
    view_col_map["USER_ID"] = "USER_NUM"
if "MOVIE_ID" in views.columns:
    view_col_map["MOVIE_ID"] = "MOVIE_NUM"
if "DURATION" in views.columns:
    view_col_map["DURATION"] = "watch_time"
if "WATCH_DAY" in views.columns:
    view_col_map["WATCH_DAY"] = "watch_day"
views = views.rename(columns=view_col_map).copy()
required_view_cols = {"USER_NUM", "MOVIE_NUM", "watch_time", "watch_day"}
missing_view_cols = sorted(required_view_cols - set(views.columns))
if missing_view_cols:
    raise ValueError(f"View history missing required columns: {missing_view_cols}")

views["watch_time"] = pd.to_numeric(views["watch_time"], errors="coerce").fillna(0.0)
views["watch_day_str"] = views["watch_day"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(8)
views["watch_dt"] = pd.to_datetime(views["watch_day_str"], format="%Y%m%d", errors="coerce")

movie = movie_policy.rename(columns={"ott_release_month": "release_month"}).copy()
if "MOVIE_NUM" not in movie.columns:
    raw_movie = pd.read_csv(raw_movie_path)
    raw_movie = raw_movie.rename(columns={"MOVIE_ID": "MOVIE_NUM", "TITLE": "movie_title", "RELEASE_MONTH": "release_month", "Category": "genre"})
    movie = raw_movie
movie["MOVIE_NUM"] = pd.to_numeric(movie["MOVIE_NUM"], errors="coerce")
movie["release_month"] = pd.to_numeric(movie["release_month"], errors="coerce")
movie = movie.sort_values(["MOVIE_NUM"]).drop_duplicates("MOVIE_NUM", keep="first")

mapping_simple = mapping[["USER_KEY", "USER_NUM"]].drop_duplicates()
member_map = membership.merge(mapping_simple, on="USER_KEY", how="left")
member_view = member_map[
    [ID_COL, GROUP_COL, "USER_NUM", "reg_dt", "end_dt"]
].merge(views[["USER_NUM", "MOVIE_NUM", "watch_time", "watch_day", "watch_dt"]], on="USER_NUM", how="left")
member_view["rel_day"] = (member_view["watch_dt"] - member_view["reg_dt"]).dt.days
member_view["has_view_row"] = member_view["watch_dt"].notna()
member_view["before_reg"] = member_view["has_view_row"] & (member_view["rel_day"] < 0)
member_view["after_end"] = member_view["has_view_row"] & member_view["end_dt"].notna() & (member_view["watch_dt"] > member_view["end_dt"])
member_view["valid_temporal"] = (
    member_view["has_view_row"]
    & member_view["reg_dt"].notna()
    & member_view["watch_dt"].notna()
    & (member_view["rel_day"] >= 0)
    & (~member_view["after_end"])
)

member_view = member_view.merge(
    movie[["MOVIE_NUM", "movie_title", "release_month", "genre"]],
    on="MOVIE_NUM",
    how="left",
)

valid_for_major = member_view[member_view["valid_temporal"] & (member_view["rel_day"].between(0, 27))]
genre_watch_for_major = (
    valid_for_major.dropna(subset=["genre"])
    .assign(genre=lambda d: d["genre"].astype(str).str.strip())
    .query("genre != ''")
    .groupby("genre")["watch_time"]
    .sum()
    .sort_values(ascending=False)
)
major_genres = list(genre_watch_for_major.head(10).index)
genre_slug = {genre: sanitize(genre) for genre in major_genres}


def included_logs_for_window(window_name):
    start, end = WINDOWS[window_name]
    return member_view[member_view["valid_temporal"] & member_view["rel_day"].between(start, end)].copy()


def build_usage_features(window_name: str, logs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = {mid: g for mid, g in logs.groupby(ID_COL)}
    window_end = WINDOWS[window_name][1]
    used_weeks = [week for week, (_, w_end) in WEEK_RANGES.items() if w_end <= window_end]
    for mid in membership[ID_COL]:
        g = grouped.get(mid)
        row = {ID_COL: mid}
        prefix = f"{window_name}_"
        if g is None or g.empty:
            sessions = 0
            total = 0.0
            first_rel = ""
            last_rel = ""
            active_days = 0
            contents = 0
            daily = pd.Series(dtype=float)
            one_minute = 0
            short_count = 0
            short_time = 0.0
        else:
            sessions = len(g)
            total = float(g["watch_time"].sum())
            first_rel = int(g["rel_day"].min())
            last_rel = int(g["rel_day"].max())
            active_days = int(g["rel_day"].nunique())
            contents = int(g["MOVIE_NUM"].nunique())
            daily = g.groupby("rel_day")["watch_time"].sum()
            one_minute = int((g["watch_time"] == 1).sum())
            short_mask = g["watch_time"] <= 5
            short_count = int(short_mask.sum())
            short_time = float(g.loc[short_mask, "watch_time"].sum())
        max_daily = float(daily.max()) if len(daily) else 0.0
        row[prefix + "has_watch_obs"] = 1 if sessions > 0 else 0
        row[prefix + "no_watch_obs_flag"] = 1 if sessions == 0 else 0
        row[prefix + "total_watch_time"] = round(total, 6)
        row[prefix + "total_sessions"] = sessions
        row[prefix + "unique_contents"] = contents
        row[prefix + "unique_watch_days"] = active_days
        row[prefix + "avg_watch_time_per_session"] = round(safe_div(total, sessions), 6)
        row[prefix + "sessions_per_active_day"] = round(safe_div(sessions, active_days), 6)
        row[prefix + "active_span_days"] = int(last_rel - first_rel + 1) if sessions else 0
        row[prefix + "first_watch_rel_day"] = first_rel
        row[prefix + "last_watch_rel_day"] = last_rel
        row[prefix + "max_daily_watch_time"] = round(max_daily, 6)
        row[prefix + "max_day_share"] = round(safe_div(max_daily, total), 6)
        row[prefix + "one_minute_watch_count"] = one_minute
        row[prefix + "short_watch_count_le5"] = short_count
        row[prefix + "short_watch_time_le5"] = round(short_time, 6)
        week_watch = {}
        week_sessions = {}
        for week in used_weeks:
            w_start, w_end = WEEK_RANGES[week]
            if g is None or g.empty:
                wg = pd.DataFrame()
            else:
                wg = g[g["rel_day"].between(w_start, w_end)]
            week_watch[week] = float(wg["watch_time"].sum()) if len(wg) else 0.0
            week_sessions[week] = int(len(wg))
            row[prefix + f"{week}_watch_time"] = round(week_watch[week], 6)
            row[prefix + f"{week}_sessions"] = week_sessions[week]
        for week in used_weeks:
            row[prefix + f"{week}_ratio"] = round(safe_div(week_watch[week], total), 6)
        if "week2" in used_weeks:
            row[prefix + "w2_minus_w1_watch_time"] = round(week_watch["week2"] - week_watch["week1"], 6)
        if "week3" in used_weeks:
            row[prefix + "w3_minus_w1_watch_time"] = round(week_watch["week3"] - week_watch["week1"], 6)
        if "week4" in used_weeks:
            row[prefix + "w4_minus_w1_watch_time"] = round(week_watch["week4"] - week_watch["week1"], 6)
            row[prefix + "w4_minus_w3_watch_time"] = round(week_watch["week4"] - week_watch["week3"], 6)
        rows.append(row)
    return pd.DataFrame(rows)


def build_content_features(window_name: str, logs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = {mid: g for mid, g in logs.groupby(ID_COL)}
    for mid in membership[ID_COL]:
        g = grouped.get(mid)
        row = {ID_COL: mid}
        prefix = f"{window_name}_"
        total = 0.0 if g is None or g.empty else float(g["watch_time"].sum())
        genre_covered = 0.0
        genre_missing = 0.0
        release_covered = 0.0
        release_weighted = 0.0
        recent_watch = 0.0
        old_watch = 0.0
        genre_watch = Counter()
        genre_sessions = Counter()
        if g is not None and not g.empty:
            for _, record in g.iterrows():
                wt = safe_float(record["watch_time"], 0.0)
                genre = "" if pd.isna(record["genre"]) else str(record["genre"]).strip()
                if genre:
                    genre_covered += wt
                    genre_watch[genre] += wt
                    genre_sessions[genre] += 1
                else:
                    genre_missing += wt
                release_month = safe_float(record["release_month"], np.nan)
                if not pd.isna(release_month):
                    release_covered += wt
                    release_weighted += wt * release_month
                    age_months = month_diff(record["watch_dt"], release_month)
                    if age_months is not None and 0 <= age_months <= 12:
                        recent_watch += wt
                    if age_months is not None and age_months >= 60:
                        old_watch += wt
        top_genre = ""
        top_genre_watch = 0.0
        if genre_watch:
            top_genre, top_genre_watch = genre_watch.most_common(1)[0]
        row[prefix + "content_has_watch_obs"] = 1 if total > 0 else 0
        row[prefix + "genre_covered_watch_time"] = round(genre_covered, 6)
        row[prefix + "genre_missing_watch_time"] = round(genre_missing, 6)
        row[prefix + "genre_covered_watch_ratio"] = round(safe_div(genre_covered, total), 6)
        row[prefix + "genre_missing_watch_ratio"] = round(safe_div(genre_missing, total), 6)
        row[prefix + "genre_unique_count"] = len(genre_watch)
        row[prefix + "top_genre"] = top_genre
        row[prefix + "top_genre_watch_time"] = round(top_genre_watch, 6)
        row[prefix + "top_genre_watch_ratio"] = round(safe_div(top_genre_watch, genre_covered), 6)
        row[prefix + "genre_entropy"] = round(entropy_from_counter(genre_watch), 6)
        for genre in major_genres:
            slug = genre_slug[genre]
            row[prefix + f"genre_ratio_{slug}"] = round(safe_div(genre_watch[genre], genre_covered), 6)
            row[prefix + f"genre_watch_time_{slug}"] = round(genre_watch[genre], 6)
            row[prefix + f"genre_session_count_{slug}"] = genre_sessions[genre]
        row[prefix + "release_month_covered_watch_ratio"] = round(safe_div(release_covered, total), 6)
        row[prefix + "avg_ott_release_month_weighted"] = round(safe_div(release_weighted, release_covered), 6) if release_covered else ""
        row[prefix + "recent_content_watch_ratio"] = round(safe_div(recent_watch, release_covered), 6)
        row[prefix + "old_content_watch_ratio"] = round(safe_div(old_watch, release_covered), 6)
        rows.append(row)
    return pd.DataFrame(rows)


feature_tables = {}
row_summary_rows = []
view_summary_rows = []
for window_name in WINDOWS:
    logs = included_logs_for_window(window_name)
    usage = build_usage_features(window_name, logs)
    content = build_content_features(window_name, logs)
    table = membership.merge(usage, on=ID_COL, how="left").merge(content, on=ID_COL, how="left")
    feature_tables[window_name] = table
    write_csv(DATA_DIR / f"06e_exact_features_{window_name}.csv", table)

    total_view_rows = int(member_view["has_view_row"].sum())
    start, end = WINDOWS[window_name]
    outside_window = member_view["valid_temporal"] & (~member_view["rel_day"].between(start, end))
    rows_with_no_watch = int((usage[f"{window_name}_no_watch_obs_flag"] == 1).sum())
    genre_total = float(logs["watch_time"].sum()) if len(logs) else 0.0
    genre_covered = float(logs.loc[logs["genre"].notna() & (logs["genre"].astype(str).str.strip() != ""), "watch_time"].sum()) if len(logs) else 0.0
    row_summary_rows.append(
        {
            "window": window_name,
            "rel_day_start": start,
            "rel_day_end": end,
            "feature_rows": len(table),
            "membership_row_id_count": table[ID_COL].nunique(),
            "rows_with_no_watch": rows_with_no_watch,
            "included_view_logs": len(logs),
            "genre_coverage_rate": round(safe_div(genre_covered, genre_total), 6),
            "one_row_per_membership_status": "PASS" if len(table) == membership[ID_COL].nunique() else "FAIL",
        }
    )
    view_summary_rows.append(
        {
            "window": window_name,
            "raw_view_source": rel(raw_view_path),
            "raw_movie_source": rel(raw_movie_path),
            "policy_movie_source": rel(STAGE02 / "moviemaster_v2_policy_checked.csv"),
            "joined_membership_event_view_rows": total_view_rows,
            "included_view_logs": len(logs),
            "excluded_before_reg_date": int(member_view["before_reg"].sum()),
            "excluded_after_end_date": int(member_view["after_end"].sum()),
            "excluded_outside_window_but_temporally_valid": int(outside_window.sum()),
            "missing_user_mapping_memberships": int(member_map["USER_NUM"].isna().sum()),
            "movie_metadata_missing_rows_in_window": int(logs["genre"].isna().sum()) if len(logs) else 0,
        }
    )

row_summary = pd.DataFrame(row_summary_rows)
view_summary = pd.DataFrame(view_summary_rows)
write_csv(TABLE_DIR / "06e_window_feature_row_summary.csv", row_summary)
write_csv(TABLE_DIR / "06e_view_log_inclusion_summary.csv", view_summary)


def is_categorical_feature(col: str) -> bool:
    return col in CATEGORICAL_BASE_FEATURES or col.endswith("_top_genre")


def prepare_model_matrix(X: pd.DataFrame) -> pd.DataFrame:
    out = X.copy()
    for col in out.columns:
        if is_categorical_feature(col):
            out[col] = out[col].where(out[col].notna(), np.nan)
            out[col] = out[col].map(lambda v: np.nan if pd.isna(v) else str(v))
        else:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def make_preprocessor(X: pd.DataFrame, scale_numeric=False) -> ColumnTransformer:
    categorical_cols = [c for c in X.columns if is_categorical_feature(c)]
    numeric_cols = [c for c in X.columns if c not in categorical_cols]
    transformers = []
    if numeric_cols:
        steps = [("imputer", SimpleImputer(strategy="median"))]
        if scale_numeric:
            steps.append(("scaler", StandardScaler()))
        transformers.append(("num", Pipeline(steps), numeric_cols))
    if categorical_cols:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical_cols,
            )
        )
    return ColumnTransformer(transformers, remainder="drop")


def safe_metric(fn, y_true, y_score):
    try:
        if len(np.unique(y_true)) < 2:
            return np.nan
        return float(fn(y_true, y_score))
    except Exception:
        return np.nan


def get_post_transform_count(pipeline, X):
    try:
        return int(pipeline.named_steps["preprocess"].transform(X.iloc[:1]).shape[1])
    except Exception:
        return np.nan


def evaluate_model(df: pd.DataFrame, window_name: str, feature_set_name: str, features, model_name: str, include_churn_prevented: str):
    features = [f for f in features if f in df.columns and f not in FORBIDDEN_FEATURES]
    if not features:
        return None, None
    work = df[[ID_COL, GROUP_COL, TARGET, "target_y"] + features].copy()
    train_ids = set(split.loc[split[SPLIT_COL] == "train", ID_COL])
    test_ids = set(split.loc[split[SPLIT_COL] == "test", ID_COL])
    train_mask = work[ID_COL].isin(train_ids)
    test_mask = work[ID_COL].isin(test_ids)
    X_train = prepare_model_matrix(work.loc[train_mask, features])
    y_train = work.loc[train_mask, "target_y"].astype(int)
    X_test = prepare_model_matrix(work.loc[test_mask, features])
    y_test = work.loc[test_mask, "target_y"].astype(int)
    if len(X_train) == 0 or len(X_test) == 0:
        return None, None
    if model_name == "LogisticRegression":
        model = LogisticRegression(max_iter=1000, solver="lbfgs", random_state=RANDOM_STATE)
        preprocessor = make_preprocessor(X_train, scale_numeric=True)
    else:
        model = HistGradientBoostingClassifier(max_iter=80, learning_rate=0.08, max_leaf_nodes=31, random_state=RANDOM_STATE)
        preprocessor = make_preprocessor(X_train, scale_numeric=False)
    pipe = Pipeline([("preprocess", preprocessor), ("model", model)])
    pipe.fit(X_train, y_train)
    repurchase_score = pipe.predict_proba(X_test)[:, 1]
    churn_score = 1 - repurchase_score
    repurchase_pred = (repurchase_score >= 0.5).astype(int)
    churn_true = 1 - y_test
    churn_pred = (churn_score >= 0.5).astype(int)
    result = {
        "window": window_name,
        "feature_set": feature_set_name,
        "include_is_churn_prevented": include_churn_prevented,
        "model": model_name,
        "roc_auc_repurchase": safe_metric(roc_auc_score, y_test, repurchase_score),
        "average_precision_repurchase": safe_metric(average_precision_score, y_test, repurchase_score),
        "average_precision_churn_risk": safe_metric(average_precision_score, churn_true, churn_score),
        "accuracy": float(accuracy_score(y_test, repurchase_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, repurchase_pred)),
        "precision_churn_at_0_5": float(precision_score(churn_true, churn_pred, zero_division=0)),
        "recall_churn_at_0_5": float(recall_score(churn_true, churn_pred, zero_division=0)),
        "f1_churn_at_0_5": float(f1_score(churn_true, churn_pred, zero_division=0)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "train_positive_rate": round(float(y_train.mean()), 6),
        "test_positive_rate": round(float(y_test.mean()), 6),
        "feature_count": int(len(features)),
        "post_transform_feature_count": get_post_transform_count(pipe, X_test),
        "train_test_USER_KEY_overlap": int(len(set(work.loc[train_mask, GROUP_COL].dropna()) & set(work.loc[test_mask, GROUP_COL].dropna()))),
    }
    scored = work.loc[test_mask, [ID_COL, GROUP_COL, TARGET, "target_y"]].copy()
    scored["repurchase_score"] = repurchase_score
    scored["churn_risk_score"] = churn_score
    scored["window"] = window_name
    scored["feature_set"] = feature_set_name
    scored["model"] = model_name
    scored["include_is_churn_prevented"] = include_churn_prevented
    return result, scored


def feature_sets_for_window(df: pd.DataFrame, window_name: str):
    usage_cols = [c for c in df.columns if c.startswith(f"{window_name}_") and not any(t in c for t in ["genre_", "top_genre", "content_", "release_month", "recent_content", "old_content", "ott_release"])]
    content_cols = [c for c in df.columns if c.startswith(f"{window_name}_") and c not in usage_cols]
    membership_without = [c for c in MEMBERSHIP_FEATURES if c in df.columns]
    membership_with = membership_without + ([CHURN_PREVENTED_FEATURE] if CHURN_PREVENTED_FEATURE in df.columns else [])
    simple_usage = [
        f"{window_name}_has_watch_obs",
        f"{window_name}_total_watch_time",
        f"{window_name}_total_sessions",
        f"{window_name}_unique_contents",
        f"{window_name}_unique_watch_days",
        f"{window_name}_avg_watch_time_per_session",
        f"{window_name}_sessions_per_active_day",
        f"{window_name}_one_minute_watch_count",
        f"{window_name}_short_watch_count_le5",
    ]
    genre_ratios = [c for c in content_cols if f"{window_name}_genre_ratio_" in c]
    return [
        ("membership_only_without_churn_prevented", "N", membership_without),
        ("membership_only_with_churn_prevented", "Y", membership_with),
        ("membership_plus_usage_only_without_churn_prevented", "N", membership_without + usage_cols),
        ("membership_plus_usage_only_with_churn_prevented", "Y", membership_with + usage_cols),
        ("membership_plus_usage_content_without_churn_prevented", "N", membership_without + usage_cols + content_cols),
        ("membership_plus_usage_content_with_churn_prevented", "Y", membership_with + usage_cols + content_cols),
        ("usage_only", "N", usage_cols),
        ("content_only", "N", content_cols),
        ("reduced_interpretable_without_churn_prevented", "N", membership_without + [c for c in simple_usage if c in df.columns] + genre_ratios),
    ]


metric_rows = []
score_frames = []
for window_name, df in feature_tables.items():
    for feature_set_name, include_churn_prevented, features in feature_sets_for_window(df, window_name):
        for model_name in ["LogisticRegression", "HistGradientBoostingClassifier"]:
            result, scored = evaluate_model(df, window_name, feature_set_name, features, model_name, include_churn_prevented)
            if result is not None:
                metric_rows.append(result)
                score_frames.append(scored)

metrics = pd.DataFrame(metric_rows)
scores = pd.concat(score_frames, ignore_index=True) if score_frames else pd.DataFrame()
write_csv(TABLE_DIR / "06e_exact_window_model_metrics.csv", metrics)
write_csv(DATA_DIR / "06e_exact_window_prediction_scores.csv", scores)

default_mask = (
    (metrics["model"] == "HistGradientBoostingClassifier")
    & (metrics["feature_set"] == "membership_plus_usage_content_without_churn_prevented")
)
auc_by_window = metrics.loc[default_mask, [
    "window",
    "feature_set",
    "model",
    "roc_auc_repurchase",
    "average_precision_repurchase",
    "average_precision_churn_risk",
    "feature_count",
    "post_transform_feature_count",
]].sort_values("window")
write_csv(TABLE_DIR / "06e_auc_by_window.csv", auc_by_window)

decile_rows = []
for (window_name, feature_set, model_name), group in scores.groupby(["window", "feature_set", "model"]):
    if feature_set not in ["membership_plus_usage_content_without_churn_prevented", "reduced_interpretable_without_churn_prevented"]:
        continue
    n = len(group)
    if n == 0:
        continue
    top_n = max(1, math.ceil(n * 0.10))
    ranked = group.sort_values("churn_risk_score", ascending=False).copy()
    top = ranked.head(top_n)
    overall_churn = float((1 - ranked["target_y"]).mean())
    top_churn = float((1 - top["target_y"]).mean())
    captured = int((1 - top["target_y"]).sum())
    total_churners = int((1 - ranked["target_y"]).sum())
    decile_rows.append(
        {
            "window": window_name,
            "feature_set": feature_set,
            "model": model_name,
            "n_test": n,
            "top_10pct_n": top_n,
            "overall_churn_rate": round(overall_churn, 6),
            "top_10pct_churn_rate": round(top_churn, 6),
            "top_decile_lift_vs_overall": round(safe_div(top_churn, overall_churn), 6),
            "captured_churners": captured,
            "total_churners": total_churners,
            "churner_capture_rate": round(safe_div(captured, total_churners), 6),
        }
    )
deciles = pd.DataFrame(decile_rows)
write_csv(TABLE_DIR / "06e_churn_risk_decile_by_window.csv", deciles)

proxy_auc = stage06c_summary.get("ultra_conservative_w1_2_proxy_auc")
exact_w12_row = auc_by_window[auc_by_window["window"] == "w1_2"]
exact_w12_auc = float(exact_w12_row["roc_auc_repurchase"].iloc[0]) if len(exact_w12_row) else np.nan
proxy_compare = pd.DataFrame(
    [
        {
            "metric": "stage06c_proxy_w1_2_auc",
            "roc_auc_repurchase": proxy_auc,
            "basis": "Stage 06c proxy from saved w1_3 columns",
            "interpretation": "Proxy was not exact early-window rebuild.",
        },
        {
            "metric": "stage06e_exact_w1_2_auc",
            "roc_auc_repurchase": exact_w12_auc,
            "basis": "Exact rel_day 0-13 rebuild from view logs",
            "interpretation": "Exact early-window audit result.",
        },
        {
            "metric": "difference_exact_minus_proxy",
            "roc_auc_repurchase": None if proxy_auc is None else exact_w12_auc - float(proxy_auc),
            "basis": "Exact minus proxy",
            "interpretation": "Positive value means Stage 06c proxy was pessimistic.",
        },
    ]
)
write_csv(TABLE_DIR / "06e_stage06c_proxy_vs_exact_w1_2.csv", proxy_compare)


def timing_class(window_name):
    if window_name == "w1_1":
        return "early_safe"
    if window_name == "w1_2":
        return "early_cautioned"
    if window_name == "w1_3":
        return "target_adjacent"
    return "late_period_only"


timing_table = auc_by_window.copy()
timing_table["timing_classification"] = timing_table["window"].map(timing_class)
timing_table["interpretation"] = timing_table["window"].map(
    {
        "w1_1": "가입 후 7일 이내만 사용하므로 가장 보수적인 조기 신호입니다.",
        "w1_2": "가입 후 14일 이내 신호라 비교적 조기이지만 이용 지연과 무시청이 이미 반영됩니다.",
        "w1_3": "가입 후 21일 이내 신호로 현재 보수 후보이나 후반 이용 행태가 성능을 끌어올릴 수 있습니다.",
        "w1_4": "가입 후 28일 전체 관찰에 가까워 조기경보 성능으로 제시하면 안 됩니다.",
    }
)
write_csv(TABLE_DIR / "06e_timing_interpretation_table.csv", timing_table)

full_reference_auc = stage06c_summary.get("full_w1_3_auc") or stage06c_summary.get("primary_auc") or stage06c_summary.get("current_full_auc")
if full_reference_auc is None:
    for key, value in stage06c_summary.items():
        if "auc" in key.lower() and "w1_3" in key.lower() and isinstance(value, (int, float)):
            full_reference_auc = value
            break

ladder_rows = []
if full_reference_auc is not None:
    ladder_rows.append(
        {
            "row_type": "full_current_w1_3_reference",
            "window": "w1_3",
            "model": "Stage 06 reference",
            "feature_set": "current Stage 06/06c reference",
            "roc_auc_repurchase": float(full_reference_auc),
            "recommended_mentor_facing_number": "N",
            "recommended_presentation_number": "N",
            "caution_wording": "기존 고성능 기준값이며, 06e 정확 조기 윈도우 재구축과 구분해야 합니다.",
        }
    )
for _, row in auc_by_window.iterrows():
    window = row["window"]
    ladder_rows.append(
        {
            "row_type": f"exact_{window}_result",
            "window": window,
            "model": row["model"],
            "feature_set": row["feature_set"],
            "roc_auc_repurchase": row["roc_auc_repurchase"],
            "recommended_mentor_facing_number": "Y" if window == "w1_2" else "N",
            "recommended_presentation_number": "Y" if window == "w1_3" else "N",
            "caution_wording": timing_table.loc[timing_table["window"] == window, "interpretation"].iloc[0],
        }
    )
mentor_ladder = pd.DataFrame(ladder_rows)
write_csv(TABLE_DIR / "06e_mentor_safe_metric_ladder.csv", mentor_ladder)


def plot_auc():
    fig, ax = plt.subplots(figsize=(8, 4.8))
    plot_df = auc_by_window.sort_values("window")
    ax.plot(plot_df["window"], plot_df["roc_auc_repurchase"], marker="o", linewidth=2)
    ax.set_title("Exact AUC by Observation Window")
    ax.set_xlabel("Observation window")
    ax.set_ylabel("ROC AUC, repurchase")
    ax.set_ylim(0.5, max(1.0, float(plot_df["roc_auc_repurchase"].max()) + 0.03))
    for _, r in plot_df.iterrows():
        ax.text(r["window"], r["roc_auc_repurchase"] + 0.01, f"{r['roc_auc_repurchase']:.3f}", ha="center")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "06e_auc_by_time_window.png", dpi=160)
    plt.close(fig)


def plot_decile():
    fig, ax = plt.subplots(figsize=(8, 4.8))
    plot_df = deciles[
        (deciles["model"] == "HistGradientBoostingClassifier")
        & (deciles["feature_set"] == "membership_plus_usage_content_without_churn_prevented")
    ].sort_values("window")
    ax.bar(plot_df["window"], plot_df["top_10pct_churn_rate"], color="#4C78A8")
    ax.set_title("Top Decile Churn Rate by Window")
    ax.set_xlabel("Observation window")
    ax.set_ylabel("Top 10% churn rate")
    ax.set_ylim(0, max(1.0, float(plot_df["top_10pct_churn_rate"].max()) + 0.05) if len(plot_df) else 1)
    for _, r in plot_df.iterrows():
        ax.text(r["window"], r["top_10pct_churn_rate"] + 0.01, f"{r['top_10pct_churn_rate']:.3f}", ha="center")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "06e_churn_risk_top_decile_by_window.png", dpi=160)
    plt.close(fig)


def plot_ladder():
    fig, ax = plt.subplots(figsize=(9, 4.8))
    plot_df = mentor_ladder[mentor_ladder["row_type"].str.startswith("exact_")].copy()
    colors = ["#59A14F" if w in ["w1_1", "w1_2"] else "#F28E2B" if w == "w1_3" else "#E15759" for w in plot_df["window"]]
    ax.bar(plot_df["window"], plot_df["roc_auc_repurchase"], color=colors)
    ax.set_title("Mentor Metric Ladder")
    ax.set_xlabel("Exact rebuilt window")
    ax.set_ylabel("ROC AUC, repurchase")
    ax.set_ylim(0.5, max(1.0, float(plot_df["roc_auc_repurchase"].max()) + 0.03))
    for _, r in plot_df.iterrows():
        ax.text(r["window"], r["roc_auc_repurchase"] + 0.01, f"{r['roc_auc_repurchase']:.3f}", ha="center")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "06e_metric_ladder_for_mentor.png", dpi=160)
    plt.close(fig)


plot_auc()
plot_decile()
plot_ladder()


def get_auc(window):
    row = auc_by_window[auc_by_window["window"] == window]
    return float(row["roc_auc_repurchase"].iloc[0]) if len(row) else np.nan


def get_decile_lift(window):
    row = deciles[
        (deciles["window"] == window)
        & (deciles["model"] == "HistGradientBoostingClassifier")
        & (deciles["feature_set"] == "membership_plus_usage_content_without_churn_prevented")
    ]
    return float(row["top_decile_lift_vs_overall"].iloc[0]) if len(row) else np.nan


w_auc = {w: get_auc(w) for w in WINDOWS}
w_lift = {w: get_decile_lift(w) for w in WINDOWS}
auc_increase_w11_w14 = w_auc["w1_4"] - w_auc["w1_1"]
auc_increase_w12_w13 = w_auc["w1_3"] - w_auc["w1_2"]
stage06c_verdict = stage06c_summary.get("final_verdict", "target_adjacent_but_not_direct_leakage")
recommended_mentor_window = "w1_2"
recommended_presentation_window = "w1_3"

report_lines = [
    "# 06e v2 Exact Early-Window Rebuild and Timing-Sensitivity Audit",
    "",
    "## Scope",
    "- This stage rebuilt exact early-window usage/content features from Stage 02 membership/user/movie policy outputs and raw view logs.",
    "- No Optuna, SHAP, segmentation, business simulation, or production model tuning was performed.",
    "- New outputs were written only under `06e_v2_exact_early_window_rebuild` report folders.",
    "",
    "## Source File Note",
    f"- Requested raw view path was checked by alias; actual raw view source used: `{rel(raw_view_path)}`.",
    f"- Requested raw movie path was checked by alias; actual raw movie source used: `{rel(raw_movie_path)}`.",
    f"- Movie metadata used for modeling came from policy-checked and deduplicated `{rel(STAGE02 / 'moviemaster_v2_policy_checked.csv')}`.",
    "",
    "## Exact AUC Answers",
    f"1. Exact `w1_1` AUC: {w_auc['w1_1']:.6f}.",
    f"2. Exact `w1_2` AUC: {w_auc['w1_2']:.6f}.",
    f"3. Exact `w1_3` AUC: {w_auc['w1_3']:.6f}.",
    f"4. Exact `w1_4` AUC: {w_auc['w1_4']:.6f}.",
    f"5. AUC increase from `w1_1` to `w1_4`: {auc_increase_w11_w14:.6f}; from `w1_2` to `w1_3`: {auc_increase_w12_w13:.6f}.",
    "",
    "## Timing Interpretation",
    "- `w1_1` is the cleanest early-window audit because it uses only rel_day 0 through 6.",
    "- `w1_2` remains mentor-safe for a conservative response because it uses rel_day 0 through 13 and is exact, not proxy-derived.",
    "- `w1_3` is the current conservative candidate but should be described as timing-sensitive because it includes behavior through rel_day 20.",
    "- `w1_4` is late-period/end-of-period only and must not be presented as early-warning performance.",
    f"- After Stage 06c, the high AUC remains classified as `{stage06c_verdict}`.",
    "",
    "## Stage 06c Proxy vs Exact w1_2",
    f"- Stage 06c proxy `w1_2` AUC: {proxy_auc if proxy_auc is not None else 'not available'}.",
    f"- Stage 06e exact `w1_2` AUC: {exact_w12_auc:.6f}.",
    "- If the exact value is higher than the proxy, the proxy under-estimated because it reconstructed an early window indirectly from saved `w1_3` columns instead of rebuilding event-level features.",
    "- If the exact value is similar, early-window signal is genuinely limited.",
    "",
    "## Mentor-Safe Recommendation",
    f"- Safest mentor-facing number: exact `{recommended_mentor_window}` AUC {w_auc[recommended_mentor_window]:.6f}.",
    f"- Suitable presentation number with caveats: exact `{recommended_presentation_window}` AUC {w_auc[recommended_presentation_window]:.6f}.",
    "- Do not present the `w1_4` AUC as early-warning performance because it uses observation through rel_day 27.",
    "- Do not claim causality or operational readiness from high AUC alone.",
    "",
    "## Required Output Tables",
    f"- `{rel(TABLE_DIR / '06e_exact_window_model_metrics.csv')}`",
    f"- `{rel(TABLE_DIR / '06e_auc_by_window.csv')}`",
    f"- `{rel(TABLE_DIR / '06e_mentor_safe_metric_ladder.csv')}`",
]
report_path = DATA_DIR / "06e_exact_early_window_rebuild_report.md"
report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

mentor_lines = [
    "# 06e 멘토 대응용 보수 성능 요약",
    "",
    "## 핵심 답변",
    "멘토님의 지적처럼 기존 0.87~0.90 수준의 AUC를 그대로 조기경보 성능이라고 주장하지 않는 것이 안전합니다. 06e에서는 원본 조회 로그를 membership_row_id 단위로 다시 붙여 `w1_1`, `w1_2`, `w1_3`, `w1_4`를 정확히 재구축했습니다.",
    "",
    "## 정확 조기 윈도우 결과",
    f"- `w1_1` rel_day 0~6 AUC: {w_auc['w1_1']:.6f}",
    f"- `w1_2` rel_day 0~13 AUC: {w_auc['w1_2']:.6f}",
    f"- `w1_3` rel_day 0~20 AUC: {w_auc['w1_3']:.6f}",
    f"- `w1_4` rel_day 0~27 AUC: {w_auc['w1_4']:.6f}",
    "",
    "## 발표 수치 권고",
    f"- 멘토님께 가장 보수적으로 답할 수 있는 수치: exact `w1_2` AUC {w_auc['w1_2']:.6f}",
    f"- 최종 발표에서 쓸 수 있는 수치: exact `w1_3` AUC {w_auc['w1_3']:.6f}, 단 rel_day 20까지의 행동을 포함한 timing-sensitive 성능이라고 명시해야 합니다.",
    "- `w1_4`는 말기 관찰 성능이므로 조기 예측 성능으로 말하면 안 됩니다.",
    "",
    "## 말하면 안 되는 표현",
    "- 0.90 AUC가 가입 직후 조기경보 성능이라고 말하면 안 됩니다.",
    "- 시청 행동 변수가 재구독을 인과적으로 만든다고 말하면 안 됩니다.",
    "- Stage 06c 이후 해석은 direct leakage가 아니라 target-adjacent timing signal이라는 보수적 표현을 사용해야 합니다.",
]
(DATA_DIR / "06e_mentor_safe_metric_summary.md").write_text("\n".join(mentor_lines) + "\n", encoding="utf-8")

summary = {
    "stage": "06e_v2_exact_early_window_rebuild",
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "raw_view_source_used": rel(raw_view_path),
    "raw_movie_source_used": rel(raw_movie_path),
    "membership_rows": int(len(membership)),
    "major_genres": major_genres,
    "default_metric_basis": "HistGradientBoostingClassifier / membership_plus_usage_content_without_churn_prevented",
    "exact_auc_by_window": {k: float(v) for k, v in w_auc.items()},
    "top_decile_lift_by_window": {k: float(v) if not pd.isna(v) else None for k, v in w_lift.items()},
    "stage06c_proxy_w1_2_auc": proxy_auc,
    "stage06e_exact_w1_2_auc": exact_w12_auc,
    "stage06c_verdict": stage06c_verdict,
    "recommended_mentor_facing_window": recommended_mentor_window,
    "recommended_mentor_facing_auc": float(w_auc[recommended_mentor_window]),
    "recommended_presentation_window": recommended_presentation_window,
    "recommended_presentation_auc": float(w_auc[recommended_presentation_window]),
    "w1_4_label": "late_period_only",
    "data_outputs": [rel(DATA_DIR / f"06e_exact_features_{w}.csv") for w in WINDOWS] + [
        rel(DATA_DIR / "06e_exact_window_prediction_scores.csv"),
        rel(DATA_DIR / "06e_exact_early_window_rebuild_report.md"),
        rel(DATA_DIR / "06e_mentor_safe_metric_summary.md"),
    ],
    "table_outputs": [rel(p) for p in TABLE_DIR.glob("06e_*.csv")],
    "figure_outputs": [rel(p) for p in FIGURE_DIR.glob("06e_*.png")],
    "feature_dictionary_context": feature_dictionary_summary,
}
write_json(DATA_DIR / "06e_exact_early_window_summary.json", summary)

raw_after = snapshot_paths([raw_view_path, raw_movie_path])
stage_after = snapshot_dirs(stage01_09_dirs)
data_after = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())

required_outputs = [
    DATA_DIR / "06e_exact_early_window_rebuild_report.md",
    DATA_DIR / "06e_exact_early_window_summary.json",
    DATA_DIR / "06e_mentor_safe_metric_summary.md",
    TABLE_DIR / "06e_window_feature_row_summary.csv",
    TABLE_DIR / "06e_view_log_inclusion_summary.csv",
    TABLE_DIR / "06e_exact_window_model_metrics.csv",
    TABLE_DIR / "06e_auc_by_window.csv",
    TABLE_DIR / "06e_churn_risk_decile_by_window.csv",
    TABLE_DIR / "06e_stage06c_proxy_vs_exact_w1_2.csv",
    TABLE_DIR / "06e_mentor_safe_metric_ladder.csv",
    TABLE_DIR / "06e_timing_interpretation_table.csv",
    FIGURE_DIR / "06e_auc_by_time_window.png",
    FIGURE_DIR / "06e_churn_risk_top_decile_by_window.png",
    FIGURE_DIR / "06e_metric_ladder_for_mentor.png",
]
final_checks = [
    {"check": "raw files unchanged", "status": "PASS" if raw_before == raw_after else "FAIL", "evidence": json.dumps({"before": raw_before, "after": raw_after}, ensure_ascii=False)},
    {"check": "no _data output created", "status": "PASS" if data_before == data_after else "FAIL", "evidence": "Compared _data file set before and after."},
    {"check": "Stage 01 through Stage 09 outputs not overwritten", "status": "PASS" if stage_before == stage_after else "FAIL", "evidence": "Compared non-06e report artifact size and mtime snapshots."},
    {"check": "no Optuna run", "status": "PASS", "evidence": "Script imports no optuna and runs no tuning loop."},
    {"check": "no SHAP run", "status": "PASS", "evidence": "Script imports no shap and computes no SHAP values."},
    {"check": "no segmentation created", "status": "PASS", "evidence": "No segmentation outputs were written."},
    {"check": "no business simulation created", "status": "PASS", "evidence": "No simulation outputs were written."},
    {"check": "exact w1_1/w1_2 attempt completed or blocked reason documented", "status": "PASS", "evidence": f"Exact windows completed: {list(WINDOWS.keys())}."},
    {"check": "same Stage 06 split reused", "status": "PASS", "evidence": rel(STAGE06_TABLE / "06_v2_split_membership_row_ids.csv")},
    {"check": "forbidden features excluded", "status": "PASS", "evidence": "Feature construction excludes ID/date/target columns from model feature lists."},
    {"check": "target mapping documented", "status": "PASS", "evidence": "Y -> 1 repurchase, N -> 0 non-repurchase/churn risk."},
    {"check": "w1_4 labeled late-period only", "status": "PASS", "evidence": "06e_timing_interpretation_table.csv and report label w1_4 late_period_only."},
    {"check": "mentor-safe metric ladder created", "status": "PASS" if (TABLE_DIR / "06e_mentor_safe_metric_ladder.csv").exists() else "FAIL", "evidence": rel(TABLE_DIR / "06e_mentor_safe_metric_ladder.csv")},
    {"check": "final report created", "status": "PASS" if report_path.exists() else "FAIL", "evidence": rel(report_path)},
]
for output in required_outputs:
    final_checks.append({"check": f"required output exists: {output.name}", "status": "PASS" if output.exists() else "FAIL", "evidence": rel(output)})
write_csv(TABLE_DIR / "06e_final_checks.csv", pd.DataFrame(final_checks))

summary["final_checks_path"] = rel(TABLE_DIR / "06e_final_checks.csv")
summary["final_check_status"] = "PASS" if all(row["status"] == "PASS" for row in final_checks) else "FAIL"
write_json(DATA_DIR / "06e_exact_early_window_summary.json", summary)

print(json.dumps({
    "stage": "06e",
    "default_auc_by_window": summary["exact_auc_by_window"],
    "mentor_facing_auc": summary["recommended_mentor_facing_auc"],
    "presentation_auc": summary["recommended_presentation_auc"],
    "final_check_status": summary["final_check_status"],
}, ensure_ascii=False, indent=2))
