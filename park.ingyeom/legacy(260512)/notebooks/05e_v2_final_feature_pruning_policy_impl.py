import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "park.ingyeom").exists() and (candidate / "_data").exists():
            return candidate
    raise FileNotFoundError("Project root not found.")


PROJECT_ROOT = find_root(Path.cwd())
BASE = PROJECT_ROOT / "park.ingyeom"
STAGE05 = BASE / "reports" / "data" / "05_v2_modeling_dataset"
STAGE05D = BASE / "reports" / "data" / "05d_v2_feature_dictionary"
STAGE06C = BASE / "reports" / "data" / "06c_v2_overfitting_leakage_adversarial_audit"
STAGE06D_TABLE = BASE / "reports" / "tables" / "06d_v2_multicollinearity_redundancy_audit"
STAGE06E = BASE / "reports" / "data" / "06e_v2_exact_early_window_rebuild"
STAGE06F = BASE / "reports" / "data" / "06f_v2_reduced_feature_baseline_audit"

DATA_DIR = BASE / "reports" / "data" / "05e_v2_final_feature_pruning_policy"
TABLE_DIR = BASE / "reports" / "tables" / "05e_v2_final_feature_pruning_policy"
FIGURE_DIR = BASE / "reports" / "figures" / "05e_v2_final_feature_pruning_policy"
for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(Path(path).relative_to(PROJECT_ROOT)).replace("\\", "/")


def snapshot_paths(paths):
    out = {}
    for path in paths:
        path = Path(path)
        if path.exists() and path.is_file():
            st = path.stat()
            out[rel(path)] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
    return out


def snapshot_dirs(dirs):
    files = []
    for directory in dirs:
        directory = Path(directory)
        if directory.exists():
            files.extend([p for p in directory.rglob("*") if p.is_file()])
    return snapshot_paths(files)


def write_csv(path: Path, df: pd.DataFrame):
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


raw_before = snapshot_dirs([PROJECT_ROOT / "_data"])
stage05_original_paths = [
    STAGE05 / "modeling_dataset_v2_w1_3.csv",
    STAGE05 / "modeling_dataset_v2_w1_4.csv",
    STAGE05 / "feature_sets_v2.json",
]
stage05_before = snapshot_paths(stage05_original_paths)
stage01_09_dirs = []
for base_dir in [BASE / "reports" / "data", BASE / "reports" / "tables", BASE / "reports" / "figures"]:
    if base_dir.exists():
        stage01_09_dirs.extend([p for p in base_dir.iterdir() if p.is_dir() and p.name != "05e_v2_final_feature_pruning_policy"])
stage_before = snapshot_dirs(stage01_09_dirs)
data_file_set_before = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())

df13 = pd.read_csv(STAGE05 / "modeling_dataset_v2_w1_3.csv")
df14 = pd.read_csv(STAGE05 / "modeling_dataset_v2_w1_4.csv")
feature_sets_v2 = read_json(STAGE05 / "feature_sets_v2.json")
stage05d = read_json(STAGE05D / "05d_v2_feature_dictionary_summary.json")
stage06c = read_json(STAGE06C / "06c_adversarial_audit_summary.json")
stage06e = read_json(STAGE06E / "06e_exact_early_window_summary.json")
stage06f = read_json(STAGE06F / "06f_reduced_feature_baseline_summary.json")

core_06d_files = {
    "pearson": STAGE06D_TABLE / "06d_high_corr_pairs_pearson.csv",
    "spearman": STAGE06D_TABLE / "06d_high_corr_pairs_spearman.csv",
    "vif": STAGE06D_TABLE / "06d_vif_results.csv",
    "structural": STAGE06D_TABLE / "06d_structural_redundancy_notes.csv",
    "reduced_recommendation": STAGE06D_TABLE / "06d_reduced_feature_recommendation.csv",
    "grouping": STAGE06D_TABLE / "06d_interpretation_grouping_recommendation.csv",
}
stage06d_status = {k: p.exists() for k, p in core_06d_files.items()}
structural_06d = pd.read_csv(core_06d_files["structural"]) if core_06d_files["structural"].exists() else pd.DataFrame()

ID_METADATA = ["membership_row_id"]
GROUP_METADATA = ["USER_KEY"]
TARGET = "is_repurchase"
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
RAW_CALENDAR_TOKENS = ["calendar", "raw_date", "watch_date", "watch_day", "reg_date", "end_date"]


def exists(df, features):
    return [f for f in features if f in df.columns]


def genre_ratio_cols(df, prefix):
    return sorted([c for c in df.columns if c.startswith(f"{prefix}_genre_ratio_")])


def build_features(df, prefix, include_product_code=False, include_watch_presence=False, include_week3=True, include_genre=True, include_content=True, early_week12=False):
    membership = ["price", "max_screen", "is_promotion", "is_user_verified", "gender", "age", "payment_device", "billing_method"]
    if include_product_code:
        membership.insert(1, "product_code")
    features = exists(df, membership)
    if include_watch_presence:
        features += exists(df, [f"{prefix}_has_watch_obs"])
    features += exists(df, [
        f"{prefix}_total_sessions",
        f"{prefix}_unique_contents",
        f"{prefix}_unique_watch_days",
        f"{prefix}_avg_watch_time_per_session",
    ])
    week_features = [
        f"{prefix}_week1_watch_time",
        f"{prefix}_week2_watch_time",
        f"{prefix}_week1_sessions",
        f"{prefix}_week2_sessions",
    ]
    if include_week3 and not early_week12:
        week_features += [f"{prefix}_week3_watch_time", f"{prefix}_week3_sessions"]
        if prefix == "w1_4":
            week_features += [f"{prefix}_week4_watch_time", f"{prefix}_week4_sessions"]
    features += exists(df, week_features)
    if include_genre:
        features += genre_ratio_cols(df, prefix)
        features += exists(df, [f"{prefix}_genre_entropy"])
    if include_content:
        features += exists(df, [f"{prefix}_genre_covered_watch_ratio", f"{prefix}_recent_content_watch_ratio"])
    return list(dict.fromkeys([f for f in features if f not in FORBIDDEN_FEATURES]))


feature_sets = {
    "pruned_w1_3_core_interpretable_without_product_code_without_watch_presence_flag": {
        "window": "w1_3",
        "features": build_features(df13, "w1_3", False, False, True, True, True),
        "timing_label": "timing_sensitive_w1_3",
        "product_code_policy": "without_product_code_default",
        "watch_presence_policy": "without_watch_presence_flag_default",
        "claim_status": "presentation_candidate_with_timing_caveat",
    },
    "pruned_w1_3_core_interpretable_with_product_code_without_watch_presence_flag": {
        "window": "w1_3",
        "features": build_features(df13, "w1_3", True, False, True, True, True),
        "timing_label": "timing_sensitive_w1_3",
        "product_code_policy": "with_product_code_sensitivity",
        "watch_presence_policy": "without_watch_presence_flag_default",
        "claim_status": "sensitivity_only_product_memorization_risk",
    },
    "pruned_w1_3_core_interpretable_without_product_code_with_watch_presence_flag": {
        "window": "w1_3",
        "features": build_features(df13, "w1_3", False, True, True, True, True),
        "timing_label": "timing_sensitive_w1_3",
        "product_code_policy": "without_product_code_default",
        "watch_presence_policy": "with_watch_presence_flag_sensitivity",
        "claim_status": "sensitivity_only_watch_presence_proxy_risk",
    },
    "pruned_w1_3_membership_usage_only_without_product_code_without_watch_presence_flag": {
        "window": "w1_3",
        "features": build_features(df13, "w1_3", False, False, True, False, False),
        "timing_label": "timing_sensitive_w1_3",
        "product_code_policy": "without_product_code_default",
        "watch_presence_policy": "without_watch_presence_flag_default",
        "claim_status": "presentation_candidate_with_timing_caveat",
    },
    "pruned_w1_3_early_safer_week1_2_without_product_code_without_watch_presence_flag": {
        "window": "w1_3",
        "features": build_features(df13, "w1_3", False, False, False, False, False, True),
        "timing_label": "early_safer_w1_3_proxy",
        "product_code_policy": "without_product_code_default",
        "watch_presence_policy": "without_watch_presence_flag_default",
        "claim_status": "mentor_safe_early_safer_proxy",
    },
    "pruned_w1_3_genre_ratio_only_added_without_product_code_without_watch_presence_flag": {
        "window": "w1_3",
        "features": build_features(df13, "w1_3", False, False, False, True, False),
        "timing_label": "early_cautioned_preference_proxy",
        "product_code_policy": "without_product_code_default",
        "watch_presence_policy": "without_watch_presence_flag_default",
        "claim_status": "genre_preference_diagnostic",
    },
    "pruned_w1_4_late_period_comparison_without_product_code_without_watch_presence_flag": {
        "window": "w1_4",
        "features": build_features(df14, "w1_4", False, False, True, True, True),
        "timing_label": "late_period_only",
        "product_code_policy": "without_product_code_default",
        "watch_presence_policy": "without_watch_presence_flag_default",
        "claim_status": "late_period_comparison_only",
    },
}


def classify_family(col):
    if col in ID_METADATA:
        return "metadata"
    if col in GROUP_METADATA:
        return "group_metadata"
    if col == TARGET:
        return "target"
    if col in ["price", "product_code", "max_screen", "is_promotion", "is_user_verified", "gender", "age", "payment_device", "billing_method", "is_churn_prevented"]:
        return "membership"
    if "genre_ratio" in col or "genre_entropy" in col:
        return "genre_preference"
    if "genre_watch_time" in col or "genre_session_count" in col or "genre_covered_watch_time" in col or "genre_missing_watch_time" in col:
        return "content_volume_proxy"
    if "release_month" in col or "recent_content" in col or "old_content" in col or "ott_release" in col:
        return "release_month_proxy"
    if col.startswith("w1_"):
        return "usage"
    return "unknown"


def drop_reason(col):
    if col in FORBIDDEN_FEATURES:
        return "forbidden_or_role_column"
    if col == "is_churn_prevented":
        return "excluded_from_default_policy"
    if col == "product_code":
        return "excluded_from_default_official_set_product_memorization_risk"
    if "no_watch_obs_flag" in col:
        return "complementary_watch_presence_proxy"
    if "has_watch_obs" in col:
        return "watch_presence_proxy_sensitivity_only"
    if "total_watch_time" in col:
        return "structural_duplicate_of_weekly_watch_time"
    if "week" in col and "ratio" in col:
        return "ratio_derivative_dropped"
    if "_minus_" in col:
        return "delta_derivative_dropped"
    if "first_watch_rel_day" in col or "last_watch_rel_day" in col:
        return "target_adjacent_timing_dropped"
    if "one_minute" in col or "short_watch" in col or "short_watch_time" in col:
        return "short_watch_redundancy_dropped"
    if "sessions_per_active_day" in col or "active_span_days" in col:
        return "unstable_or_redundant_session_span_dropped"
    if "genre_watch_time" in col or "genre_session_count" in col or "genre_covered_watch_time" in col or "genre_missing_watch_time" in col:
        return "content_volume_usage_proxy_dropped"
    if "genre_missing_watch_ratio" in col:
        return "complement_of_covered_ratio_dropped"
    if "top_genre" in col:
        return "top_genre_family_dropped_for_stability"
    if "avg_ott_release_month_weighted" in col or "old_content_watch_ratio" in col:
        return "release_month_complex_or_complementary_dropped"
    return "not_selected_by_final_pruned_policy"


all_selected = sorted(set(f for spec in feature_sets.values() for f in spec["features"]))
metadata_cols = ID_METADATA + GROUP_METADATA + [TARGET]
pruned13_cols = [c for c in metadata_cols + all_selected if c in df13.columns and (c in metadata_cols or c.startswith("w1_3_") or not c.startswith("w1_"))]
pruned14_cols = [c for c in metadata_cols + feature_sets["pruned_w1_4_late_period_comparison_without_product_code_without_watch_presence_flag"]["features"] if c in df14.columns]
df13[pruned13_cols].to_csv(DATA_DIR / "modeling_dataset_v2_w1_3_pruned.csv", index=False, encoding="utf-8-sig")
df14[pruned14_cols].to_csv(DATA_DIR / "modeling_dataset_v2_w1_4_pruned.csv", index=False, encoding="utf-8-sig")

categorical = [c for c in feature_sets_v2.get("categorical_features_to_encode_in_stage06", []) if c != "is_churn_prevented"]
payload = {
    "target_column": TARGET,
    "id_metadata_columns": ID_METADATA,
    "group_metadata_columns": GROUP_METADATA,
    "forbidden_features": sorted(FORBIDDEN_FEATURES),
    "categorical_features_to_encode_in_stage06": categorical,
    "target_mapping": {"Y": 1, "N": 0},
    "score_direction": {"repurchase_score": "P(is_repurchase=Y)", "churn_risk_score": "1 - repurchase_score"},
    "official_recommendation_priority": [
        "no_forbidden_features",
        "without_product_code_by_default",
        "without_watch_presence_shortcut_by_default",
        "lower_target_adjacent_timing_risk",
        "reduced_structural_redundancy",
        "auc",
        "top_decile_lift",
    ],
    "feature_sets": feature_sets,
}
write_json(DATA_DIR / "pruned_feature_sets_v2.json", payload)

decision_rows = []
for window, source_df in [("w1_3", df13), ("w1_4", df14)]:
    for col in source_df.columns:
        selected_sets = [name for name, spec in feature_sets.items() if spec["window"] == window and col in spec["features"]]
        if col in ID_METADATA:
            action = "keep_metadata"
            reason = "ID metadata only, not a model feature."
        elif col in GROUP_METADATA:
            action = "keep_group_metadata"
            reason = "Group split metadata only, not a model feature."
        elif col == TARGET:
            action = "keep_target"
            reason = "Target only."
        elif selected_sets:
            action = "keep_feature"
            reason = "Selected by final pruned policy variants."
        else:
            action = "drop_feature"
            reason = drop_reason(col)
        decision_rows.append({
            "window": window,
            "feature": col,
            "family": classify_family(col),
            "action": action,
            "reason": reason,
            "selected_feature_sets": "|".join(selected_sets),
            "product_code_policy": "sensitivity_only" if col == "product_code" else "",
            "watch_presence_policy": "sensitivity_only" if "has_watch_obs" in col or "no_watch_obs_flag" in col else "",
            "timing_label": "target_adjacent_or_timing_sensitive" if any(t in col for t in ["week3", "week4", "first_watch", "last_watch"]) else "",
        })
decision_log = pd.DataFrame(decision_rows)
write_csv(TABLE_DIR / "05e_feature_pruning_decision_log.csv", decision_log)
write_csv(TABLE_DIR / "05e_dropped_feature_inventory.csv", decision_log[decision_log["action"].eq("drop_feature")])
write_csv(TABLE_DIR / "05e_kept_feature_inventory.csv", decision_log[decision_log["action"].ne("drop_feature")])

inventory_rows = []
for name, spec in feature_sets.items():
    feats = spec["features"]
    inventory_rows.append({
        "feature_set_name": name,
        "window": spec["window"],
        "feature_count": len(feats),
        "includes_product_code": "Y" if "product_code" in feats else "N",
        "includes_watch_presence_flag": "Y" if any("has_watch_obs" in f or "no_watch_obs_flag" in f for f in feats) else "N",
        "includes_week3": "Y" if any("week3" in f for f in feats) else "N",
        "timing_label": spec["timing_label"],
        "product_code_policy": spec["product_code_policy"],
        "watch_presence_policy": spec["watch_presence_policy"],
        "claim_status": spec["claim_status"],
        "target_adjacent_risk_rating": "high" if spec["timing_label"] in ["late_period_only", "timing_sensitive_w1_3"] else "low_to_medium",
        "multicollinearity_risk_rating": "reduced_medium" if "core_interpretable" in name else "low_to_medium",
        "interpretation_safety_rating": "medium" if spec["timing_label"] == "timing_sensitive_w1_3" else "high" if "early_safer" in name else "medium_high",
        "features": "|".join(feats),
    })
inventory = pd.DataFrame(inventory_rows)
write_csv(TABLE_DIR / "05e_pruned_feature_set_inventory.csv", inventory)

structural_rows = [
    {"conflict_group": "watch_presence_complement", "resolution": "keep no default flag; has_watch_obs sensitivity only; drop no_watch_obs_flag", "affected_features": "has_watch_obs|no_watch_obs_flag"},
    {"conflict_group": "total_vs_weekly_watch_time", "resolution": "weekly pattern design; drop total_watch_time from pruned feature sets", "affected_features": "total_watch_time|week*_watch_time"},
    {"conflict_group": "weekly_ratios", "resolution": "drop ratios because weekly source variables are kept", "affected_features": "week*_ratio"},
    {"conflict_group": "weekly_deltas", "resolution": "drop deltas because source weekly variables are kept", "affected_features": "w*_minus_*"},
    {"conflict_group": "genre_volume_proxy", "resolution": "keep genre_ratio and genre_entropy; drop genre watch_time/session_count", "affected_features": "genre_ratio_*|genre_watch_time_*|genre_session_count_*"},
    {"conflict_group": "coverage_complements", "resolution": "keep genre_covered_watch_ratio only; drop missing ratio and watch-time coverage totals", "affected_features": "genre_covered_watch_ratio|genre_missing_watch_ratio"},
]
write_csv(TABLE_DIR / "05e_structural_redundancy_resolution.csv", pd.DataFrame(structural_rows))

target_adjacent_rows = decision_log[decision_log["reason"].str.contains("target_adjacent|watch_presence|timing", case=False, na=False)].copy()
write_csv(TABLE_DIR / "05e_target_adjacent_feature_resolution.csv", target_adjacent_rows)

multi_summary = pd.DataFrame([
    {"source": "06d_structural_redundancy_notes", "available": stage06d_status["structural"], "rows": len(structural_06d), "use": "confirmed total-week, session-week, genre-volume, ratio-complement relations"},
    {"source": "06d_high_corr_pairs_pearson", "available": stage06d_status["pearson"], "rows": int(pd.read_csv(core_06d_files["pearson"]).shape[0]) if stage06d_status["pearson"] else 0, "use": "supporting correlation risk evidence"},
    {"source": "06d_vif_results", "available": stage06d_status["vif"], "rows": int(pd.read_csv(core_06d_files["vif"]).shape[0]) if stage06d_status["vif"] else 0, "use": "supporting multicollinearity evidence"},
    {"source": "deterministic_column_rules", "available": True, "rows": len(decision_log), "use": "primary implementation rule when model-performance-independent pruning is required"},
])
write_csv(TABLE_DIR / "05e_multicollinearity_resolution_summary.csv", multi_summary)

report_lines = [
    "# 05e v2 Final Feature Pruning Policy Report",
    "",
    "## Why Pruning Was Necessary",
    "- Stage 05 full datasets are exploratory because original variables and derived variables coexist.",
    "- Stage 06c classified high AUC as target-adjacent but not direct leakage.",
    "- Stage 06d found structural redundancy and multicollinearity risk, making individual feature interpretation unsafe.",
    "- Stage 06f showed reduced diagnostic models can retain useful ranking, so final reporting datasets should be pruned.",
    "",
    "## Key Policy Corrections",
    "- `product_code` is excluded from default official feature sets and appears only in sensitivity variants.",
    "- `has_watch_obs` is treated as a behavior-presence proxy and appears only in sensitivity variants.",
    "- Any w1_3 feature set with week3 variables is labeled `timing_sensitive_w1_3`.",
    "- A week1/week2-only early-safer variant is created.",
    "- w1_4 is labeled `late_period_only` and is not an early-warning candidate.",
    "",
    "## Kept Feature Families",
    "- Membership context without `product_code` by default.",
    "- Weekly source watch/session variables instead of totals, ratios, and deltas.",
    "- Genre ratio and entropy features as preference proxies.",
    "- Minimal coverage/release proxy features where interpretable.",
    "",
    "## Dropped Feature Families",
    "- Forbidden role columns from feature sets.",
    "- `no_watch_obs_flag`, default `has_watch_obs`, total watch time, ratios, deltas, first/last watch rel day, short-watch variables, top_genre family, genre watch_time/session_count, and content volume proxies.",
    "",
    "## Final Candidate Feature Sets",
]
for name, spec in feature_sets.items():
    report_lines.append(f"- `{name}`: {len(spec['features'])} features, label `{spec['timing_label']}`, claim `{spec['claim_status']}`.")
report_lines += [
    "",
    "## Original Stage 05 Status",
    "- Original Stage 05 modeling datasets should now be treated as exploratory/full datasets, not final reporting datasets.",
]
(DATA_DIR / "05e_feature_pruning_policy_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

summary = {
    "stage": "05e_v2_final_feature_pruning_policy",
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "input_rows": {"w1_3": len(df13), "w1_4": len(df14)},
    "output_columns": {"w1_3_pruned": len(pruned13_cols), "w1_4_pruned": len(pruned14_cols)},
    "stage06d_status": stage06d_status,
    "stage06c_verdict": stage06c.get("final_verdict"),
    "stage06e_exact_auc_by_window": stage06e.get("exact_auc_by_window"),
    "stage06f_mentor_safe_feature_set": stage06f.get("mentor_safe_feature_set"),
    "feature_sets": {k: {"window": v["window"], "feature_count": len(v["features"]), "timing_label": v["timing_label"], "product_code_policy": v["product_code_policy"], "watch_presence_policy": v["watch_presence_policy"]} for k, v in feature_sets.items()},
    "data_outputs": [rel(DATA_DIR / "modeling_dataset_v2_w1_3_pruned.csv"), rel(DATA_DIR / "modeling_dataset_v2_w1_4_pruned.csv"), rel(DATA_DIR / "pruned_feature_sets_v2.json")],
}
write_json(DATA_DIR / "05e_feature_pruning_summary.json", summary)

raw_after = snapshot_dirs([PROJECT_ROOT / "_data"])
stage05_after = snapshot_paths(stage05_original_paths)
stage_after = snapshot_dirs(stage01_09_dirs)
data_file_set_after = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())

required_outputs = [
    DATA_DIR / "modeling_dataset_v2_w1_3_pruned.csv",
    DATA_DIR / "modeling_dataset_v2_w1_4_pruned.csv",
    DATA_DIR / "pruned_feature_sets_v2.json",
    DATA_DIR / "05e_feature_pruning_summary.json",
    DATA_DIR / "05e_feature_pruning_policy_report.md",
    TABLE_DIR / "05e_feature_pruning_decision_log.csv",
    TABLE_DIR / "05e_pruned_feature_set_inventory.csv",
    TABLE_DIR / "05e_dropped_feature_inventory.csv",
    TABLE_DIR / "05e_kept_feature_inventory.csv",
    TABLE_DIR / "05e_structural_redundancy_resolution.csv",
    TABLE_DIR / "05e_target_adjacent_feature_resolution.csv",
    TABLE_DIR / "05e_multicollinearity_resolution_summary.csv",
]
checks = [
    {"check": "raw files unchanged", "status": "PASS" if raw_before == raw_after else "FAIL", "evidence": "Compared _data file snapshots."},
    {"check": "no _data output created", "status": "PASS" if data_file_set_before == data_file_set_after else "FAIL", "evidence": "Compared _data file set."},
    {"check": "Stage 01 through Stage 09 outputs not overwritten", "status": "PASS" if stage_before == stage_after else "FAIL", "evidence": "Compared non-05e artifact snapshots."},
    {"check": "original Stage 05 datasets not overwritten", "status": "PASS" if stage05_before == stage05_after else "FAIL", "evidence": "Compared Stage 05 source file snapshots."},
    {"check": "pruned datasets created separately", "status": "PASS" if (DATA_DIR / "modeling_dataset_v2_w1_3_pruned.csv").exists() and (DATA_DIR / "modeling_dataset_v2_w1_4_pruned.csv").exists() else "FAIL", "evidence": rel(DATA_DIR)},
    {"check": "forbidden features excluded from feature sets", "status": "PASS" if not any(f in FORBIDDEN_FEATURES for spec in feature_sets.values() for f in spec["features"]) else "FAIL", "evidence": "Checked all pruned feature sets."},
    {"check": "target mapping documented", "status": "PASS", "evidence": "Y -> 1; N -> 0."},
    {"check": "w1_3/w1_4 separated", "status": "PASS" if all((spec["window"] == "w1_3" and not any(f.startswith("w1_4_") for f in spec["features"])) or (spec["window"] == "w1_4" and not any(f.startswith("w1_3_") for f in spec["features"])) for spec in feature_sets.values()) else "FAIL", "evidence": "Checked feature prefixes."},
    {"check": "w1_4 labeled late-period only", "status": "PASS" if feature_sets["pruned_w1_4_late_period_comparison_without_product_code_without_watch_presence_flag"]["timing_label"] == "late_period_only" else "FAIL", "evidence": "w1_4 feature-set metadata."},
    {"check": "product_code default exclusion and sensitivity variant created", "status": "PASS" if any("with_product_code" in k for k in feature_sets) and any("without_product_code" in k for k in feature_sets) else "FAIL", "evidence": "Feature set names and metadata."},
    {"check": "watch-presence default exclusion and sensitivity variant created", "status": "PASS" if any("with_watch_presence_flag" in k for k in feature_sets) and any("without_watch_presence_flag" in k for k in feature_sets) else "FAIL", "evidence": "Feature set names and metadata."},
    {"check": "week3-containing variants labeled timing_sensitive_w1_3", "status": "PASS" if all(spec["timing_label"] == "timing_sensitive_w1_3" for spec in feature_sets.values() if spec["window"] == "w1_3" and any("week3" in f for f in spec["features"])) else "FAIL", "evidence": "Checked week3-containing sets."},
    {"check": "early-safer week1/week2 variant exists", "status": "PASS" if "pruned_w1_3_early_safer_week1_2_without_product_code_without_watch_presence_flag" in feature_sets else "FAIL", "evidence": "Feature set exists."},
    {"check": "structural redundancy decisions documented", "status": "PASS" if (TABLE_DIR / "05e_structural_redundancy_resolution.csv").exists() else "FAIL", "evidence": rel(TABLE_DIR / "05e_structural_redundancy_resolution.csv")},
    {"check": "dropped feature inventory created", "status": "PASS" if (TABLE_DIR / "05e_dropped_feature_inventory.csv").exists() else "FAIL", "evidence": rel(TABLE_DIR / "05e_dropped_feature_inventory.csv")},
    {"check": "kept feature inventory created", "status": "PASS" if (TABLE_DIR / "05e_kept_feature_inventory.csv").exists() else "FAIL", "evidence": rel(TABLE_DIR / "05e_kept_feature_inventory.csv")},
    {"check": "pruned feature sets created", "status": "PASS" if (DATA_DIR / "pruned_feature_sets_v2.json").exists() else "FAIL", "evidence": rel(DATA_DIR / "pruned_feature_sets_v2.json")},
]
for path in required_outputs:
    checks.append({"check": f"required output exists: {path.name}", "status": "PASS" if path.exists() else "FAIL", "evidence": rel(path)})
final_checks = pd.DataFrame(checks)
write_csv(TABLE_DIR / "05e_final_checks.csv", final_checks)
summary["final_checks_path"] = rel(TABLE_DIR / "05e_final_checks.csv")
summary["final_check_status"] = "PASS" if (final_checks["status"] == "PASS").all() else "FAIL"
write_json(DATA_DIR / "05e_feature_pruning_summary.json", summary)

print(json.dumps({
    "stage": "05e",
    "final_check_status": summary["final_check_status"],
    "feature_sets": list(feature_sets.keys()),
}, ensure_ascii=False, indent=2))
