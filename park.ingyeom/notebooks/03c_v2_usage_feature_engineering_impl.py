import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MEMBERSHIP_PATH = (
    PROJECT_ROOT
    / "park.ingyeom"
    / "reports"
    / "data"
    / "02c_v2_strict_preprocessing_correction"
    / "membership_v2_preprocessed_strict_core.csv"
)
USERMAPPING_PATH = (
    PROJECT_ROOT
    / "park.ingyeom"
    / "reports"
    / "data"
    / "02c_v2_strict_preprocessing_correction"
    / "usermapping_v2_policy_checked_strict_core.csv"
)
RAW_VIEW_PATH = PROJECT_ROOT / "_data" / "01_raw" / "Views_train.csv"

DATA_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "03c_v2_usage_feature_engineering"
TABLE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "03c_v2_usage_feature_engineering"
FIGURE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "03c_v2_usage_feature_engineering"

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
WINDOW_WEEKS = {
    "w1_1": ["week1"],
    "w1_2": ["week1", "week2"],
    "w1_3": ["week1", "week2", "week3"],
    "w1_4": ["week1", "week2", "week3", "week4"],
}

BASE_FEATURES = [
    "has_watch_obs",
    "total_watch_time",
    "total_sessions",
    "unique_contents",
    "unique_watch_days",
    "avg_watch_time_per_session",
    "max_daily_watch_time",
    "max_day_share",
    "one_minute_watch_count",
    "short_watch_count_le5",
    "short_watch_time_le5",
]
DERIVED_REDUNDANT_FEATURES = [
    "week1_ratio",
    "week2_ratio",
    "week3_ratio",
    "week4_ratio",
    "w2_minus_w1_watch_time",
    "w3_minus_w2_watch_time",
    "w4_minus_w3_watch_time",
]
FORBIDDEN_FEATURE_NAMES = {
    "USER_KEY",
    "USER_NUM",
    "USER_ID",
    "MOVIE_ID",
    "reg_date",
    "end_date",
    "reg_date_parsed",
    "end_date_parsed",
    "watch_date",
    "WATCH_DAY",
    "watch_rel_day",
    "duration_days",
    "is_repurchase",
}


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path):
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def snapshot_files(paths):
    result = {}
    for path in paths:
        if path.exists():
            result[rel(path)] = {"size": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns}
        else:
            result[rel(path)] = None
    return result


def snapshot_dir(path):
    if not path.exists():
        return {}
    return {
        rel(file): {"size": file.stat().st_size, "mtime_ns": file.stat().st_mtime_ns}
        for file in sorted(path.rglob("*"))
        if file.is_file()
    }


def parse_iso_or_yy_mm_dd(value):
    text = (value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unsupported date value: {value!r}")


def parse_watch_day(value):
    return datetime.strptime(str(value).strip(), "%Y%m%d").date()


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_int_string(value):
    try:
        return str(int(float(str(value).strip())))
    except (TypeError, ValueError):
        return str(value).strip()


def init_stats():
    return {
        "total_watch_time": 0.0,
        "total_sessions": 0,
        "contents": set(),
        "days": set(),
        "daily_watch": Counter(),
        "week_watch": {week: 0.0 for week in WEEK_RANGES},
        "week_sessions": {week: 0 for week in WEEK_RANGES},
        "one_minute": 0,
        "short_count_le5": 0,
        "short_time_le5": 0.0,
    }


def build_feature_names(window):
    names = ["membership_row_id"]
    names.extend(f"{window}_{feature}" for feature in BASE_FEATURES)
    for week in WINDOW_WEEKS[window]:
        names.append(f"{window}_{week}_watch_time")
        names.append(f"{window}_{week}_sessions")
    for derived in DERIVED_REDUNDANT_FEATURES:
        if derived.startswith("week"):
            week = derived.split("_", 1)[0]
            if week in WINDOW_WEEKS[window]:
                names.append(f"{window}_{derived}")
        elif derived.startswith("w2_") and "week2" in WINDOW_WEEKS[window]:
            names.append(f"{window}_{derived}")
        elif derived.startswith("w3_") and "week3" in WINDOW_WEEKS[window]:
            names.append(f"{window}_{derived}")
        elif derived.startswith("w4_") and "week4" in WINDOW_WEEKS[window]:
            names.append(f"{window}_{derived}")
    return names


def build_feature_row(membership_id, window, stats):
    total = stats["total_watch_time"]
    sessions = stats["total_sessions"]
    active_days = len(stats["days"])
    max_daily = max(stats["daily_watch"].values()) if stats["daily_watch"] else 0.0
    row = {"membership_row_id": membership_id}

    def put(name, value):
        row[f"{window}_{name}"] = value

    put("has_watch_obs", 1 if sessions else 0)
    put("total_watch_time", round(total, 6))
    put("total_sessions", sessions)
    put("unique_contents", len(stats["contents"]))
    put("unique_watch_days", active_days)
    put("avg_watch_time_per_session", round(total / sessions, 6) if sessions else 0)
    put("max_daily_watch_time", round(max_daily, 6))
    put("max_day_share", round(max_daily / total, 6) if total else 0)
    put("one_minute_watch_count", stats["one_minute"])
    put("short_watch_count_le5", stats["short_count_le5"])
    put("short_watch_time_le5", round(stats["short_time_le5"], 6))

    for week in WINDOW_WEEKS[window]:
        put(f"{week}_watch_time", round(stats["week_watch"][week], 6))
        put(f"{week}_sessions", stats["week_sessions"][week])
    for week in WINDOW_WEEKS[window]:
        put(f"{week}_ratio", round(stats["week_watch"][week] / total, 6) if total else 0)
    if "week2" in WINDOW_WEEKS[window]:
        put("w2_minus_w1_watch_time", round(stats["week_watch"]["week2"] - stats["week_watch"]["week1"], 6))
    if "week3" in WINDOW_WEEKS[window]:
        put("w3_minus_w2_watch_time", round(stats["week_watch"]["week3"] - stats["week_watch"]["week2"], 6))
    if "week4" in WINDOW_WEEKS[window]:
        put("w4_minus_w3_watch_time", round(stats["week_watch"]["week4"] - stats["week_watch"]["week3"], 6))
    return row


def numeric_summary(rows, window, fieldnames):
    summary = []
    for column in fieldnames:
        if column == "membership_row_id":
            continue
        values = []
        for row in rows:
            try:
                values.append(float(row[column]))
            except (TypeError, ValueError):
                pass
        values.sort()
        if not values:
            continue
        summary.append(
            {
                "window": window,
                "feature": column,
                "count": len(values),
                "min": values[0],
                "max": values[-1],
                "mean": round(sum(values) / len(values), 6),
                "zero_count": sum(1 for value in values if value == 0),
                "derived_redundant_for_later_pruning": int(
                    any(column.endswith("_" + name) for name in DERIVED_REDUNDANT_FEATURES)
                ),
            }
        )
    return summary


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    protected_input_files = [MEMBERSHIP_PATH, USERMAPPING_PATH, RAW_VIEW_PATH]
    raw_before = snapshot_dir(PROJECT_ROOT / "_data")
    protected_before = snapshot_files(protected_input_files)
    old_stage03_before = {
        "data": snapshot_dir(PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "03_v2_usage_feature_engineering"),
        "tables": snapshot_dir(PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "03_v2_usage_feature_engineering"),
        "figures": snapshot_dir(PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "03_v2_usage_feature_engineering"),
    }

    membership_cols, membership = read_csv(MEMBERSHIP_PATH)
    mapping_cols, usermapping = read_csv(USERMAPPING_PATH)
    view_cols, view_rows = read_csv(RAW_VIEW_PATH)

    membership_by_id = {}
    membership_ids_by_user_key = defaultdict(list)
    for row in membership:
        membership_id = int(row["membership_row_id"])
        reg_date = parse_iso_or_yy_mm_dd(row.get("reg_date_parsed")) or parse_iso_or_yy_mm_dd(row.get("reg_date"))
        end_date = parse_iso_or_yy_mm_dd(row.get("end_date_parsed")) or parse_iso_or_yy_mm_dd(row.get("end_date"))
        if reg_date is None or end_date is None:
            raise ValueError(f"Missing parsed dates for membership_row_id={membership_id}")
        row["_membership_id"] = membership_id
        row["_reg_date"] = reg_date
        row["_end_date"] = end_date
        membership_by_id[membership_id] = row
        membership_ids_by_user_key[row["USER_KEY"]].append(membership_id)

    keys_by_user_num = defaultdict(set)
    user_nums_by_user_key = defaultdict(set)
    for row in usermapping:
        user_key = row["USER_KEY"]
        user_num = safe_int_string(row["USER_NUM"])
        keys_by_user_num[user_num].add(user_key)
        user_nums_by_user_key[user_key].add(user_num)

    input_summary = [
        {
            "input_name": "membership_v2_preprocessed_strict_core",
            "path": rel(MEMBERSHIP_PATH),
            "row_count": len(membership),
            "column_count": len(membership_cols),
            "role": "02c strict-core corrected Membership rows",
        },
        {
            "input_name": "usermapping_v2_policy_checked_strict_core",
            "path": rel(USERMAPPING_PATH),
            "row_count": len(usermapping),
            "column_count": len(mapping_cols),
            "role": "USER_KEY to USER_NUM temporary join bridge only",
        },
        {
            "input_name": "Views_train",
            "path": rel(RAW_VIEW_PATH),
            "row_count": len(view_rows),
            "column_count": len(view_cols),
            "role": "Raw usage logs, read only",
        },
    ]

    stats_by_window = {window: {mid: init_stats() for mid in membership_by_id} for window in WINDOWS}
    attachment_dist = Counter()
    join_counts = Counter()
    temporal_counts = Counter()
    temporal_by_window = {window: Counter() for window in WINDOWS}
    short_counts_by_window = {window: Counter() for window in WINDOWS}
    valid_expanded_log_count = 0

    for view in view_rows:
        user_num = safe_int_string(view["USER_ID"])
        user_keys = keys_by_user_num.get(user_num, set())
        attached_memberships = set()
        for user_key in user_keys:
            attached_memberships.update(membership_ids_by_user_key.get(user_key, []))
        attachment_dist[len(attached_memberships)] += 1
        if not attached_memberships:
            join_counts["raw_view_rows_with_no_strict_core_membership_attachment"] += 1
            continue
        if len(attached_memberships) > 1:
            join_counts["raw_view_rows_attached_to_multiple_memberships"] += 1

        watch_date = parse_watch_day(view["WATCH_DAY"])
        watch_time = safe_float(view["DURATION"])
        movie_id = safe_int_string(view["MOVIE_ID"])

        for membership_id in attached_memberships:
            member = membership_by_id[membership_id]
            rel_day = (watch_date - member["_reg_date"]).days
            if watch_date < member["_reg_date"]:
                temporal_counts["excluded_watch_date_lt_reg_date"] += 1
            elif watch_date > member["_end_date"]:
                temporal_counts["excluded_watch_date_gt_end_date"] += 1
            else:
                valid_expanded_log_count += 1

            for window, (start_day, end_day) in WINDOWS.items():
                in_window = start_day <= rel_day <= end_day
                in_membership_period = member["_reg_date"] <= watch_date <= member["_end_date"]
                if not in_membership_period:
                    temporal_by_window[window]["excluded_outside_membership_period"] += 1
                    continue
                if not in_window:
                    temporal_by_window[window]["excluded_outside_window"] += 1
                    continue

                temporal_by_window[window]["included_logs"] += 1
                s = stats_by_window[window][membership_id]
                s["total_watch_time"] += watch_time
                s["total_sessions"] += 1
                s["contents"].add(movie_id)
                s["days"].add(rel_day)
                s["daily_watch"][rel_day] += watch_time
                for week, (week_start, week_end) in WEEK_RANGES.items():
                    if week_start <= rel_day <= week_end:
                        s["week_watch"][week] += watch_time
                        s["week_sessions"][week] += 1
                if watch_time == 1:
                    s["one_minute"] += 1
                    short_counts_by_window[window]["one_minute_watch_count"] += 1
                if watch_time <= 5:
                    s["short_count_le5"] += 1
                    s["short_time_le5"] += watch_time
                    short_counts_by_window[window]["short_watch_count_le5"] += 1
                    short_counts_by_window[window]["short_watch_time_le5"] += watch_time

    feature_rows = {}
    fieldnames_by_window = {}
    for window in WINDOWS:
        rows = [
            build_feature_row(membership_id, window, stats_by_window[window][membership_id])
            for membership_id in sorted(membership_by_id)
        ]
        fieldnames = build_feature_names(window)
        feature_rows[window] = rows
        fieldnames_by_window[window] = fieldnames
        write_csv(DATA_DIR / f"usage_features_v2c_{window}.csv", rows, fieldnames)

    join_expansion_summary = [
        {
            "metric": "raw_Views_train_rows",
            "count": len(view_rows),
            "ratio_to_raw_rows": 1.0,
            "note": "Raw usage rows before temporary membership attachment.",
        },
        {
            "metric": "valid_temporary_membership_log_rows",
            "count": valid_expanded_log_count,
            "ratio_to_raw_rows": round(valid_expanded_log_count / len(view_rows), 6) if view_rows else 0,
            "note": "Temporary attached rows after reg_date and end_date policy, before window filters.",
        },
        {
            "metric": "raw_view_rows_attached_to_multiple_memberships",
            "count": join_counts["raw_view_rows_attached_to_multiple_memberships"],
            "ratio_to_raw_rows": round(join_counts["raw_view_rows_attached_to_multiple_memberships"] / len(view_rows), 6)
            if view_rows
            else 0,
            "note": "Expected when the same USER_KEY has multiple Membership events. Aggregated back to membership_row_id.",
        },
        {
            "metric": "raw_view_rows_with_no_strict_core_membership_attachment",
            "count": join_counts["raw_view_rows_with_no_strict_core_membership_attachment"],
            "ratio_to_raw_rows": round(
                join_counts["raw_view_rows_with_no_strict_core_membership_attachment"] / len(view_rows), 6
            )
            if view_rows
            else 0,
            "note": "Raw usage rows that could not attach to 02c strict-core Membership rows.",
        },
    ]
    for attach_count, count in sorted(attachment_dist.items()):
        join_expansion_summary.append(
            {
                "metric": f"attachment_count_{attach_count}",
                "count": count,
                "ratio_to_raw_rows": round(count / len(view_rows), 6) if view_rows else 0,
                "note": "Number of strict-core membership_row_id attachments for one raw usage row.",
            }
        )

    temporal_filter_summary = [
        {
            "scope": "membership_log_attachment",
            "metric": metric,
            "count": count,
            "note": "watch_rel_day was recomputed as watch_date minus reg_date.",
        }
        for metric, count in sorted(temporal_counts.items())
    ]
    for window, counts in temporal_by_window.items():
        for metric, count in sorted(counts.items()):
            temporal_filter_summary.append(
                {
                    "scope": window,
                    "metric": metric,
                    "count": count,
                    "note": "Window filters are independent and do not mix rows across windows.",
                }
            )

    window_row_count_summary = []
    no_watch_summary = []
    short_watch_summary = []
    for window, rows in feature_rows.items():
        has_watch_col = f"{window}_has_watch_obs"
        has_watch_count = sum(int(row[has_watch_col]) for row in rows)
        no_watch_count = len(rows) - has_watch_count
        window_row_count_summary.append(
            {
                "window": window,
                "feature_rows": len(rows),
                "unique_membership_row_id": len({row["membership_row_id"] for row in rows}),
                "expected_strict_core_membership_rows": len(membership),
                "status": "PASS"
                if len(rows) == len(membership) == len({row["membership_row_id"] for row in rows})
                else "FAIL",
            }
        )
        no_watch_summary.append(
            {
                "window": window,
                "membership_rows": len(rows),
                "has_watch_obs_rows": has_watch_count,
                "no_watch_obs_rows": no_watch_count,
                "no_watch_rate": round(no_watch_count / len(rows), 6) if rows else 0,
            }
        )
        short_watch_summary.append(
            {
                "window": window,
                "one_minute_watch_count": int(short_counts_by_window[window]["one_minute_watch_count"]),
                "short_watch_count_le5": int(short_counts_by_window[window]["short_watch_count_le5"]),
                "short_watch_time_le5": round(short_counts_by_window[window]["short_watch_time_le5"], 6),
                "action": "kept_as_features_not_deleted",
            }
        )

    numeric_rows = []
    for window, rows in feature_rows.items():
        numeric_rows.extend(numeric_summary(rows, window, fieldnames_by_window[window]))

    feature_contract_rows = []
    for window, fieldnames in fieldnames_by_window.items():
        for feature in fieldnames:
            if feature == "membership_row_id":
                continue
            feature_contract_rows.append(
                {
                    "window": window,
                    "feature": feature,
                    "feature_family": "usage",
                    "derived_redundant_for_later_pruning": int(
                        any(feature.endswith("_" + name) for name in DERIVED_REDUNDANT_FEATURES)
                    ),
                    "uses_identifier_as_feature": 0,
                    "uses_end_date_derived_signal": 0,
                }
            )

    write_csv(
        TABLE_DIR / "03c_input_row_count_summary.csv",
        input_summary,
        ["input_name", "path", "row_count", "column_count", "role"],
    )
    write_csv(
        TABLE_DIR / "03c_join_expansion_summary.csv",
        join_expansion_summary,
        ["metric", "count", "ratio_to_raw_rows", "note"],
    )
    write_csv(
        TABLE_DIR / "03c_temporal_filter_summary.csv",
        temporal_filter_summary,
        ["scope", "metric", "count", "note"],
    )
    write_csv(
        TABLE_DIR / "03c_window_row_count_summary.csv",
        window_row_count_summary,
        ["window", "feature_rows", "unique_membership_row_id", "expected_strict_core_membership_rows", "status"],
    )
    write_csv(
        TABLE_DIR / "03c_no_watch_summary.csv",
        no_watch_summary,
        ["window", "membership_rows", "has_watch_obs_rows", "no_watch_obs_rows", "no_watch_rate"],
    )
    write_csv(
        TABLE_DIR / "03c_short_watch_summary.csv",
        short_watch_summary,
        ["window", "one_minute_watch_count", "short_watch_count_le5", "short_watch_time_le5", "action"],
    )
    write_csv(
        TABLE_DIR / "03c_usage_feature_numeric_summary.csv",
        numeric_rows,
        ["window", "feature", "count", "min", "max", "mean", "zero_count", "derived_redundant_for_later_pruning"],
    )

    data_outputs = [DATA_DIR / f"usage_features_v2c_{window}.csv" for window in WINDOWS]
    data_outputs.append(DATA_DIR / "03c_usage_feature_summary.json")
    audit_outputs = [
        TABLE_DIR / "03c_input_row_count_summary.csv",
        TABLE_DIR / "03c_join_expansion_summary.csv",
        TABLE_DIR / "03c_temporal_filter_summary.csv",
        TABLE_DIR / "03c_window_row_count_summary.csv",
        TABLE_DIR / "03c_no_watch_summary.csv",
        TABLE_DIR / "03c_short_watch_summary.csv",
        TABLE_DIR / "03c_usage_feature_numeric_summary.csv",
        TABLE_DIR / "03c_final_checks.csv",
    ]
    report_path = DATA_DIR / "03c_usage_feature_engineering_report.md"
    summary_path = DATA_DIR / "03c_usage_feature_summary.json"
    write_json(summary_path, {"status": "pending_final_checks"})
    write_csv(TABLE_DIR / "03c_final_checks.csv", [], ["check", "status", "detail"])
    report_path.write_text("# 03c v2 Usage Feature Engineering Report\n\nPending final checks.\n", encoding="utf-8")

    raw_after = snapshot_dir(PROJECT_ROOT / "_data")
    protected_after = snapshot_files(protected_input_files)
    old_stage03_after = {
        "data": snapshot_dir(PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "03_v2_usage_feature_engineering"),
        "tables": snapshot_dir(PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "03_v2_usage_feature_engineering"),
        "figures": snapshot_dir(PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "03_v2_usage_feature_engineering"),
    }

    all_feature_cols = set()
    for names in fieldnames_by_window.values():
        all_feature_cols.update(names)
    forbidden_cols = sorted(
        col
        for col in all_feature_cols
        if col in FORBIDDEN_FEATURE_NAMES
        or any(col.endswith("_" + forbidden) for forbidden in FORBIDDEN_FEATURE_NAMES)
    )
    end_date_cols = sorted(col for col in all_feature_cols if "end_date" in col or "to_end" in col)
    content_feature_cols = sorted(
        col
        for col in all_feature_cols
        if any(token in col.lower() for token in ["genre", "actor", "director", "movie_id", "movie_num", "content_id"])
    )

    final_checks = [
        {
            "check": "raw_files_unchanged",
            "status": "PASS" if raw_before == raw_after and protected_before == protected_after else "FAIL",
            "detail": "_data snapshot and protected input file snapshots unchanged",
        },
        {
            "check": "no_data_output_created",
            "status": "PASS" if raw_before == raw_after else "FAIL",
            "detail": "No files were created or modified under _data",
        },
        {
            "check": "old_stage03_outputs_not_overwritten",
            "status": "PASS" if old_stage03_before == old_stage03_after else "FAIL",
            "detail": "Existing 03_v2 output directory snapshots unchanged",
        },
        {
            "check": "one_row_per_membership_row_id_in_every_window",
            "status": "PASS" if all(row["status"] == "PASS" for row in window_row_count_summary) else "FAIL",
            "detail": "; ".join(f"{row['window']} rows={row['feature_rows']}" for row in window_row_count_summary),
        },
        {
            "check": "row_count_matches_02c_strict_core_membership",
            "status": "PASS" if all(row["feature_rows"] == len(membership) for row in window_row_count_summary) else "FAIL",
            "detail": f"strict_core_membership_rows={len(membership)}",
        },
        {
            "check": "w1_1_w1_2_w1_3_w1_4_separated",
            "status": "PASS"
            if all(
                all(col == "membership_row_id" or col.startswith(f"{window}_") for col in fieldnames_by_window[window])
                for window in WINDOWS
            )
            else "FAIL",
            "detail": "Each window table uses its own prefixed feature columns",
        },
        {
            "check": "no_model_training",
            "status": "PASS",
            "detail": "No estimator, fit, prediction, or model artifact is created",
        },
        {
            "check": "no_shap",
            "status": "PASS",
            "detail": "No SHAP package, explainer, or SHAP artifact is used",
        },
        {
            "check": "no_content_features",
            "status": "PASS" if not content_feature_cols else "FAIL",
            "detail": "none" if not content_feature_cols else "|".join(content_feature_cols),
        },
        {
            "check": "no_modeling_dataset",
            "status": "PASS",
            "detail": "Only per-window usage feature tables and audit artifacts were created",
        },
        {
            "check": "no_identifier_or_date_model_features",
            "status": "PASS" if not forbidden_cols and not end_date_cols else "FAIL",
            "detail": "none" if not forbidden_cols and not end_date_cols else "|".join(forbidden_cols + end_date_cols),
        },
        {
            "check": "all_required_outputs_created",
            "status": "PASS" if all(path.exists() for path in data_outputs + audit_outputs + [report_path]) else "FAIL",
            "detail": f"required_outputs={len(data_outputs + audit_outputs) + 1}",
        },
    ]
    write_csv(TABLE_DIR / "03c_final_checks.csv", final_checks, ["check", "status", "detail"])

    summary_payload = {
        "stage": "03c_v2_usage_feature_engineering",
        "scope": "Usage feature engineering only from 02c strict-core corrected Membership.",
        "inputs": [rel(path) for path in protected_input_files],
        "membership_rows": len(membership),
        "views_train_rows": len(view_rows),
        "windows": {
            window: {
                "rel_day_start": bounds[0],
                "rel_day_end": bounds[1],
                "feature_rows": len(feature_rows[window]),
                "available_weeks": WINDOW_WEEKS[window],
            }
            for window, bounds in WINDOWS.items()
        },
        "data_outputs": [rel(path) for path in data_outputs],
        "audit_outputs": [rel(path) for path in audit_outputs],
        "figure_output_dir": rel(FIGURE_DIR),
        "derived_redundant_features_for_later_pruning": DERIVED_REDUNDANT_FEATURES,
        "feature_contract": feature_contract_rows,
        "final_checks": final_checks,
    }
    write_json(summary_path, summary_payload)

    report_lines = [
        "# 03c v2 Usage Feature Engineering Report",
        "",
        "## Scope",
        "- Rebuilt usage features from 02c strict-core corrected Membership rows.",
        "- Raw files were read only.",
        "- Outputs were written only under the new 03c report folders.",
        "- No model training, SHAP, content features, or modeling dataset was created.",
        "",
        "## Temporal Policy",
        "- Dates use `reg_date_parsed` and `end_date_parsed` from 02c when available.",
        "- `watch_rel_day` was recomputed as `watch_date - reg_date`.",
        "- Logs before `reg_date` and after `end_date` were excluded from feature windows.",
        "- No end_date-derived feature was created.",
        "",
        "## Windows",
    ]
    for window, bounds in WINDOWS.items():
        report_lines.append(
            f"- `{window}`: rel_day {bounds[0]} through {bounds[1]}, rows {len(feature_rows[window]):,}."
        )
    report_lines.extend(
        [
            "",
            "## Derived Feature Note",
            "- Week ratios and week deltas are included as derived/redundant audit columns and marked for later pruning.",
            "",
            "## Final Checks",
        ]
    )
    for row in final_checks:
        report_lines.append(f"- {row['check']}: {row['status']} ({row['detail']})")
    report_lines.extend(["", "## Output Files"])
    for path in data_outputs + audit_outputs + [report_path]:
        report_lines.append(f"- {rel(path)}")
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print("03c v2 usage feature engineering completed.")
    for row in final_checks:
        print(f"{row['check']}: {row['status']} - {row['detail']}")


if __name__ == "__main__":
    main()
