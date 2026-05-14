import json
import os
import platform
import re
import sys
import warnings
from datetime import datetime
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)

RANDOM_STATE = 42
TEST_SIZE = 0.2
SAMPLE_MAX_ROWS = 2000
LOCAL_CASES_PER_TYPE = 3
AUC_DIFF_INVALID_THRESHOLD = 0.005

ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"
TARGET = "is_repurchase_label"

EXPECTED_FEATURE_SET = "pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence"
EXPECTED_MODEL = "HistGradientBoostingClassifier"

FORBIDDEN_FEATURES = {
    "USER_KEY",
    "USER_NUM",
    "MOVIE_NUM",
    "movie_title",
    "membership_row_id",
    "reg_date",
    "end_date",
    "reg_date_parsed",
    "end_date_parsed",
    "duration_days",
    "duration_days_stage02",
    "duration_days_recomputed",
    "watch_date",
    "watch_day",
    "is_repurchase",
    "is_repurchase_raw",
    "is_repurchase_label",
}
FORBIDDEN_SUBSTRINGS = ["raw calendar dates", "raw_calendar", "calendar_date"]


def find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (
            (candidate / "park.ingyeom" / "reports" / "data" / "05c_v2_modeling_dataset" / "feature_sets_v2c.json").exists()
            and (candidate / "park.ingyeom" / "reports" / "data" / "06c2_v2_corrected_baseline_modeling" / "06c2_corrected_baseline_summary.json").exists()
        ):
            return candidate
    raise FileNotFoundError("Could not locate ott-churn-prediction project root.")


PROJECT_ROOT = find_project_root(Path.cwd())
BASE = PROJECT_ROOT / "park.ingyeom"
STAGE05C_DATA = BASE / "reports" / "data" / "05c_v2_modeling_dataset"
STAGE05C_TABLES = BASE / "reports" / "tables" / "05c_v2_modeling_dataset"
STAGE06C2_DATA = BASE / "reports" / "data" / "06c2_v2_corrected_baseline_modeling"
STAGE06C2_TABLES = BASE / "reports" / "tables" / "06c2_v2_corrected_baseline_modeling"
STAGE07R_TABLES = BASE / "reports" / "tables" / "07r_v2_true_shap_interpretation"
STAGE06H_TABLES = BASE / "reports" / "tables" / "06h_v2_pruned_model_collinearity_shap_audit"

DATA_DIR = BASE / "reports" / "data" / "07c_v2_corrected_true_shap_interpretation"
TABLE_DIR = BASE / "reports" / "tables" / "07c_v2_corrected_true_shap_interpretation"
FIGURE_DIR = BASE / "reports" / "figures" / "07c_v2_corrected_true_shap_interpretation"


def rel(path: Path) -> str:
    return str(Path(path).relative_to(PROJECT_ROOT)).replace("\\", "/")


def write_csv(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, pd.DataFrame):
        obj.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame(obj).to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snapshot_dir(path: Path) -> dict:
    if not path.exists():
        return {}
    out = {}
    for file in sorted(path.rglob("*")):
        if file.is_file():
            st = file.stat()
            out[rel(file)] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
    return out


def snapshot_paths(paths: list[Path]) -> dict:
    out = {}
    for file in paths:
        if file.exists() and file.is_file():
            st = file.stat()
            out[rel(file)] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
    return out


def has_forbidden_feature(col: str) -> bool:
    return col in FORBIDDEN_FEATURES or any(token in col for token in FORBIDDEN_SUBSTRINGS)


def onehot_encoder():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def prepare_X(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    X = df[features].copy()
    for col in X.columns:
        if X[col].dtype == object:
            X[col] = X[col].map(lambda v: np.nan if pd.isna(v) or str(v) == "" else str(v))
        else:
            X[col] = pd.to_numeric(X[col], errors="coerce")
    return X


def make_pipeline(X: pd.DataFrame) -> Pipeline:
    cats = [c for c in X.columns if X[c].dtype == object]
    nums = [c for c in X.columns if c not in cats]
    transformers = []
    if nums:
        transformers.append(("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), nums))
    if cats:
        transformers.append(("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", onehot_encoder())]), cats))
    model = HistGradientBoostingClassifier(max_iter=120, learning_rate=0.06, random_state=RANDOM_STATE)
    return Pipeline([("prep", ColumnTransformer(transformers, remainder="drop")), ("model", model)])


def to_dense(matrix):
    if hasattr(matrix, "toarray"):
        return matrix.toarray()
    return np.asarray(matrix)


def sanitize_name(text, limit=80):
    text = re.sub(r"[^A-Za-z0-9가-힣_]+", "_", str(text))
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:limit] or "feature"


def transformed_to_original(name: str, known_features: list[str]) -> str:
    raw = str(name)
    if "__" in raw:
        raw = raw.split("__", 1)[1]
    for feature in sorted(known_features, key=len, reverse=True):
        if raw == feature or raw.startswith(feature + "_"):
            return feature
    return raw


def feature_family(feature: str) -> str:
    f = str(feature)
    membership_tokens = [
        "price",
        "screen",
        "promotion",
        "verified",
        "age",
        "gender",
        "payment",
        "billing",
        "membership",
    ]
    weekly_tokens = [
        "week1",
        "week2",
        "week3",
        "w2_minus_w1",
        "w3_minus_w2",
        "ratio",
        "max_day_share",
        "first_watch_rel_day",
        "last_watch_rel_day",
    ]
    volume_tokens = [
        "total_watch_time",
        "total_sessions",
        "unique_contents",
        "unique_watch_days",
        "avg_watch_time",
        "max_daily_watch_time",
        "one_minute",
        "short_watch",
        "watch_time",
        "session_count",
        "sessions",
    ]
    if "genre" in f or "top_genre" in f:
        return "genre_ratio_proxy"
    if "release_month" in f or "ott_release_month" in f or "recent_content" in f or "old_content" in f:
        return "release_month_proxy"
    if any(token in f for token in membership_tokens):
        return "membership_context"
    if any(token in f for token in weekly_tokens):
        return "weekly_usage_pattern"
    if any(token in f for token in volume_tokens):
        return "simple_usage_volume"
    return "other"


def extract_shap_values(explanation):
    values = explanation.values
    base_values = explanation.base_values
    if isinstance(values, list):
        values = values[1] if len(values) > 1 else values[0]
    values = np.asarray(values)
    if values.ndim == 3:
        values = values[:, :, 1] if values.shape[2] > 1 else values[:, :, 0]
    base_values = np.asarray(base_values)
    if base_values.ndim == 2:
        base_values = base_values[:, 1] if base_values.shape[1] > 1 else base_values[:, 0]
    if base_values.ndim == 0:
        base_values = np.repeat(float(base_values), values.shape[0])
    return values, base_values


def official_recommendation():
    summary = json.loads((STAGE06C2_DATA / "06c2_corrected_baseline_summary.json").read_text(encoding="utf-8"))
    rec = summary["official_corrected_recommendation"]
    return rec, summary


def select_local_cases(sample_meta: pd.DataFrame) -> pd.DataFrame:
    frames = []
    true_n = sample_meta[sample_meta[TARGET] == 0].sort_values("churn_risk_score", ascending=False).head(LOCAL_CASES_PER_TYPE).copy()
    true_n["case_type"] = "high_churn_risk_true_N"
    frames.append(true_n)
    false_pos = sample_meta[sample_meta[TARGET] == 1].sort_values("churn_risk_score", ascending=False).head(LOCAL_CASES_PER_TYPE).copy()
    false_pos["case_type"] = "high_churn_risk_false_positive"
    frames.append(false_pos)
    true_y = sample_meta[sample_meta[TARGET] == 1].sort_values("churn_risk_score", ascending=True).head(LOCAL_CASES_PER_TYPE).copy()
    true_y["case_type"] = "low_churn_risk_true_Y"
    frames.append(true_y)
    mid = sample_meta.assign(distance_to_mid=(sample_meta["repurchase_score"] - 0.5).abs()).sort_values("distance_to_mid").head(LOCAL_CASES_PER_TYPE).copy()
    mid["case_type"] = "mid_score_ambiguous"
    frames.append(mid)
    out = pd.concat(frames, ignore_index=True)
    return out.drop_duplicates(subset=[ID_COL, "case_type"]).reset_index(drop=True)


def previous_shap_comparison(current_grouped: pd.DataFrame) -> pd.DataFrame:
    old_sources = [
        ("07r_historical_pre_02c_or_pre_06c2", STAGE07R_TABLES / "07r_grouped_shap_importance.csv", "mean_abs_shap"),
        ("06h_historical_provisional", STAGE06H_TABLES / "06h_true_shap_global_importance.csv", "mean_abs_shap"),
    ]
    base = current_grouped[["original_feature", "feature_family", "mean_abs_shap", "rank"]].rename(
        columns={"mean_abs_shap": "stage07c_mean_abs_shap", "rank": "stage07c_rank"}
    )
    rows = []
    for label, path, value_col in old_sources:
        if not path.exists():
            rows.append(
                {
                    "comparison_source": label,
                    "status": "not_available",
                    "note": f"{rel(path)} not found.",
                }
            )
            continue
        old = pd.read_csv(path)
        if "original_feature" not in old.columns:
            rows.append({"comparison_source": label, "status": "not_comparable", "note": "missing original_feature column"})
            continue
        if value_col not in old.columns:
            candidates = [c for c in old.columns if "mean_abs" in c or "importance" in c]
            value_col = candidates[0] if candidates else ""
        if not value_col:
            rows.append({"comparison_source": label, "status": "not_comparable", "note": "missing importance column"})
            continue
        old_comp = old[["original_feature", value_col]].copy().rename(columns={value_col: "historical_importance"})
        old_comp["historical_rank"] = old_comp["historical_importance"].rank(ascending=False, method="dense")
        merged = base.merge(old_comp, on="original_feature", how="left")
        merged["comparison_source"] = label
        merged["status"] = "historical_only_not_final_evidence"
        merged["rank_shift_stage07c_minus_historical"] = merged["stage07c_rank"] - merged["historical_rank"]
        merged["note"] = "Old SHAP is historical/provisional and must not be used as final evidence."
        rows.extend(merged.sort_values("stage07c_rank").head(30).to_dict("records"))
    return pd.DataFrame(rows)


def main():
    for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    raw_before = snapshot_dir(PROJECT_ROOT / "_data")
    protected_before = snapshot_dir(STAGE06C2_DATA) | snapshot_dir(STAGE06C2_TABLES)
    protected_before = protected_before | snapshot_dir(BASE / "reports" / "data" / "07r_v2_true_shap_interpretation")
    protected_before = protected_before | snapshot_dir(BASE / "reports" / "tables" / "07r_v2_true_shap_interpretation")
    protected_before = protected_before | snapshot_dir(BASE / "reports" / "data" / "06h_v2_pruned_model_collinearity_shap_audit")
    protected_before = protected_before | snapshot_dir(BASE / "reports" / "tables" / "06h_v2_pruned_model_collinearity_shap_audit")

    blocked_reasons = []
    if sys.version_info[:2] != (3, 11):
        blocked_reasons.append(f"Python 3.11 required; got {platform.python_version()}")
    try:
        import shap

        shap_version = shap.__version__
        print(shap.__version__)
    except Exception as exc:
        shap = None
        shap_version = ""
        blocked_reasons.append(f"shap import failed: {exc}")

    required_inputs = [
        STAGE05C_DATA / "modeling_dataset_v2c_w1_3.csv",
        STAGE05C_DATA / "feature_sets_v2c.json",
        STAGE06C2_DATA / "06c2_corrected_baseline_summary.json",
        STAGE06C2_DATA / "06c2_final_model_recommendation.md",
        STAGE06C2_TABLES / "06c2_model_metrics.csv",
        STAGE06C2_TABLES / "06c2_group_split_summary.csv",
        STAGE06C2_TABLES / "06c2_group_leakage_check.csv",
    ]
    missing = [rel(p) for p in required_inputs if not p.exists()]
    if missing:
        blocked_reasons.append(f"missing required inputs: {missing}")

    if blocked_reasons:
        write_json(DATA_DIR / "07c_true_shap_summary.json", {"stage": "07c", "status": "BLOCKED", "blocked_reasons": blocked_reasons})
        write_csv(TABLE_DIR / "07c_final_checks.csv", [{"check": "blocked", "status": "BLOCKED", "detail": "; ".join(blocked_reasons)}])
        raise RuntimeError("BLOCKED: " + "; ".join(blocked_reasons))

    rec, stage06_summary = official_recommendation()
    official_model = rec.get("recommended_model", EXPECTED_MODEL)
    official_feature_set = rec.get("recommended_feature_set", EXPECTED_FEATURE_SET)
    official_window = rec.get("recommended_window", "w1_3")
    if official_model != EXPECTED_MODEL:
        raise RuntimeError(f"BLOCKED: Stage 07c supports official HistGradientBoostingClassifier only; got {official_model}")

    feature_payload = json.loads((STAGE05C_DATA / "feature_sets_v2c.json").read_text(encoding="utf-8"))
    feature_sets = feature_payload["feature_sets"]
    if official_feature_set not in feature_sets:
        raise RuntimeError(f"BLOCKED: official feature set not found in feature_sets_v2c.json: {official_feature_set}")
    spec = feature_sets[official_feature_set]
    df = pd.read_csv(STAGE05C_DATA / f"modeling_dataset_v2c_{official_window}.csv")
    features = list(spec["features"])
    forbidden_used = [f for f in features if has_forbidden_feature(f)]
    if forbidden_used:
        raise RuntimeError(f"BLOCKED: forbidden features used by official feature set: {forbidden_used}")

    y = pd.to_numeric(df[TARGET], errors="coerce").astype(int).to_numpy()
    groups = df[GROUP_COL].astype(str).to_numpy()
    splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    train_idx, test_idx = next(splitter.split(df, y, groups))
    train_groups = set(groups[train_idx])
    test_groups = set(groups[test_idx])
    group_overlap = len(train_groups & test_groups)
    if group_overlap != 0:
        raise RuntimeError(f"BLOCKED: train/test USER_KEY overlap is {group_overlap}")

    X = prepare_X(df, features)
    pipe = make_pipeline(X)
    pipe.fit(X.iloc[train_idx], y[train_idx])
    repurchase_score = pipe.predict_proba(X.iloc[test_idx])[:, 1]
    churn_risk_score = 1 - repurchase_score
    y_test = y[test_idx]
    rebuilt_auc = float(roc_auc_score(y_test, repurchase_score))
    rebuilt_ap = float(average_precision_score(y_test, repurchase_score))

    metrics = pd.read_csv(STAGE06C2_TABLES / "06c2_model_metrics.csv")
    rec_rows = metrics[
        metrics["feature_set_name"].eq(official_feature_set)
        & metrics["model"].eq(official_model)
        & metrics["window"].eq(official_window)
    ]
    if rec_rows.empty:
        raise RuntimeError("BLOCKED: Stage 06c2 recorded metric row not found for official model.")
    recorded_auc = float(rec_rows.iloc[0]["roc_auc_repurchase"])
    auc_diff = abs(rebuilt_auc - recorded_auc)
    reconstruction_status = "PASS" if auc_diff <= AUC_DIFF_INVALID_THRESHOLD else "INVALID"
    reconstruction = pd.DataFrame(
        [
            {
                "official_model": official_model,
                "official_feature_set": official_feature_set,
                "official_window": official_window,
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "train_test_USER_KEY_overlap": int(group_overlap),
                "reconstructed_auc": rebuilt_auc,
                "stage06c2_recorded_auc": recorded_auc,
                "absolute_auc_difference": auc_diff,
                "auc_difference_threshold": AUC_DIFF_INVALID_THRESHOLD,
                "reconstruction_status": reconstruction_status,
            }
        ]
    )
    write_csv(TABLE_DIR / "07c_model_reconstruction_check.csv", reconstruction)
    if reconstruction_status != "PASS":
        write_json(
            DATA_DIR / "07c_true_shap_summary.json",
            {
                "stage": "07c_v2_corrected_true_shap_interpretation",
                "status": "INVALID",
                "reason": "AUC difference materially large; SHAP not computed.",
                "reconstruction": reconstruction.to_dict("records"),
            },
        )
        raise RuntimeError("INVALID: reconstructed AUC differs materially from Stage 06c2.")

    test_meta = df.iloc[test_idx][[ID_COL, GROUP_COL, TARGET]].copy().reset_index(drop=True)
    test_meta["repurchase_score"] = repurchase_score
    test_meta["churn_risk_score"] = churn_risk_score
    sample_meta = test_meta.sample(n=min(SAMPLE_MAX_ROWS, len(test_meta)), random_state=RANDOM_STATE).sort_values(ID_COL).reset_index(drop=True)
    sample_ids = set(sample_meta[ID_COL])
    sample_mask = test_meta[ID_COL].isin(sample_ids).to_numpy()
    raw_sample = X.iloc[test_idx].reset_index(drop=True).loc[sample_mask].reset_index(drop=True)
    sample_meta = test_meta.loc[sample_mask].reset_index(drop=True)
    write_csv(DATA_DIR / "07c_shap_sample_membership_rows.csv", sample_meta[[ID_COL, GROUP_COL, TARGET, "repurchase_score", "churn_risk_score"]])

    prep = pipe.named_steps["prep"]
    model = pipe.named_steps["model"]
    X_trans = to_dense(prep.transform(raw_sample))
    feature_names = list(prep.get_feature_names_out())
    X_trans_df = pd.DataFrame(X_trans, columns=feature_names)
    explainer = shap.TreeExplainer(model)
    explanation = explainer(X_trans_df)
    shap_values, base_values = extract_shap_values(explanation)
    original_features = [transformed_to_original(name, features) for name in feature_names]
    families = [feature_family(f) for f in original_features]

    global_df = pd.DataFrame(
        {
            "transformed_feature": feature_names,
            "original_feature": original_features,
            "feature_family": families,
            "mean_abs_shap": np.abs(shap_values).mean(axis=0),
            "mean_shap": shap_values.mean(axis=0),
            "positive_mean_shap": np.where(shap_values > 0, shap_values, np.nan).mean(axis=0),
            "negative_mean_shap": np.where(shap_values < 0, shap_values, np.nan).mean(axis=0),
            "shap_direction": np.where(shap_values.mean(axis=0) >= 0, "pushes_toward_repurchase_score", "pushes_toward_churn_risk"),
        }
    ).sort_values("mean_abs_shap", ascending=False)
    global_df["rank"] = np.arange(1, len(global_df) + 1)
    write_csv(TABLE_DIR / "07c_global_shap_importance.csv", global_df)

    grouped_values = pd.DataFrame(shap_values, columns=feature_names)
    grouped_by_original = {}
    for feature in sorted(set(original_features)):
        cols = [name for name, orig in zip(feature_names, original_features) if orig == feature]
        grouped_by_original[feature] = grouped_values[cols].sum(axis=1).to_numpy()
    grouped_matrix = pd.DataFrame(grouped_by_original)
    grouped_df = pd.DataFrame(
        {
            "original_feature": list(grouped_matrix.columns),
            "feature_family": [feature_family(f) for f in grouped_matrix.columns],
            "mean_abs_shap": np.abs(grouped_matrix.to_numpy()).mean(axis=0),
            "mean_shap": grouped_matrix.mean(axis=0).to_numpy(),
        }
    ).sort_values("mean_abs_shap", ascending=False)
    grouped_df["rank"] = np.arange(1, len(grouped_df) + 1)
    grouped_df["shap_direction"] = np.where(grouped_df["mean_shap"] >= 0, "pushes_toward_repurchase_score", "pushes_toward_churn_risk")
    write_csv(TABLE_DIR / "07c_grouped_shap_importance.csv", grouped_df)

    family_df = (
        grouped_df.groupby("feature_family", as_index=False)
        .agg(mean_abs_shap=("mean_abs_shap", "sum"), feature_count=("original_feature", "nunique"))
        .sort_values("mean_abs_shap", ascending=False)
    )
    family_df["rank"] = np.arange(1, len(family_df) + 1)
    write_csv(TABLE_DIR / "07c_feature_family_shap_importance.csv", family_df)

    direction_rows = []
    for feature in grouped_df["original_feature"]:
        vals = grouped_matrix[feature].to_numpy()
        direction_rows.append(
            {
                "original_feature": feature,
                "feature_family": feature_family(feature),
                "mean_abs_shap": float(np.abs(vals).mean()),
                "mean_shap": float(vals.mean()),
                "positive_share": float((vals > 0).mean()),
                "negative_share": float((vals < 0).mean()),
                "primary_direction": "pushes_toward_repurchase_score" if vals.mean() >= 0 else "pushes_toward_churn_risk",
                "score_direction_note": "Positive SHAP pushes toward repurchase_score; negative SHAP pushes toward churn risk.",
            }
        )
    direction_df = pd.DataFrame(direction_rows).sort_values("mean_abs_shap", ascending=False)
    write_csv(TABLE_DIR / "07c_shap_direction_summary.csv", direction_df)

    top_n = max(1, int(np.ceil(len(sample_meta) * 0.1)))
    ordered = sample_meta.sort_values("churn_risk_score", ascending=False).reset_index(drop=True)
    top_ids = set(ordered.head(top_n)[ID_COL])
    low_ids = set(ordered.tail(top_n)[ID_COL])
    top_mask = sample_meta[ID_COL].isin(top_ids).to_numpy()
    low_mask = sample_meta[ID_COL].isin(low_ids).to_numpy()
    churn_rows = []
    for feature in grouped_df["original_feature"]:
        vals = grouped_matrix[feature].to_numpy()
        churn_rows.append(
            {
                "original_feature": feature,
                "feature_family": feature_family(feature),
                "top_decile_mean_shap": float(vals[top_mask].mean()),
                "low_decile_mean_shap": float(vals[low_mask].mean()),
                "top_minus_low_mean_shap": float(vals[top_mask].mean() - vals[low_mask].mean()),
                "top_decile_abs_mean_shap": float(np.abs(vals[top_mask]).mean()),
                "interpretation": "negative_top_decile_mean_pushes_toward_churn_risk" if vals[top_mask].mean() < 0 else "positive_top_decile_mean_pushes_toward_repurchase",
            }
        )
    churn_df = pd.DataFrame(churn_rows).sort_values("top_decile_abs_mean_shap", ascending=False)
    write_csv(TABLE_DIR / "07c_churn_risk_top_decile_shap_explanation.csv", churn_df)

    local_cases = select_local_cases(sample_meta)
    write_csv(DATA_DIR / "07c_local_explanation_cases.csv", local_cases)
    sample_index_by_id = {mid: i for i, mid in enumerate(sample_meta[ID_COL])}
    local_rows = []
    for _, case in local_cases.iterrows():
        idx = sample_index_by_id.get(case[ID_COL])
        if idx is None:
            continue
        row_vals = grouped_matrix.iloc[idx].sort_values(key=np.abs, ascending=False).head(12)
        for rank, (feature, val) in enumerate(row_vals.items(), start=1):
            local_rows.append(
                {
                    "membership_row_id": case[ID_COL],
                    "case_type": case["case_type"],
                    "actual_is_repurchase_label": int(case[TARGET]),
                    "repurchase_score": float(case["repurchase_score"]),
                    "churn_risk_score": float(case["churn_risk_score"]),
                    "rank": rank,
                    "original_feature": feature,
                    "feature_family": feature_family(feature),
                    "shap_value": float(val),
                    "direction": "pushes_toward_repurchase_score" if val >= 0 else "pushes_toward_churn_risk",
                }
            )
    local_top_df = pd.DataFrame(local_rows)
    write_csv(TABLE_DIR / "07c_local_top_contributors.csv", local_top_df)

    prev_df = previous_shap_comparison(grouped_df)
    write_csv(TABLE_DIR / "07c_previous_shap_comparison.csv", prev_df)

    plt.figure()
    shap.summary_plot(shap_values, X_trans_df, feature_names=feature_names, show=False, max_display=25)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "07c_shap_beeswarm_red_blue_corrected_official.png", dpi=170, bbox_inches="tight")
    plt.close()

    plt.figure()
    shap.summary_plot(shap_values, X_trans_df, feature_names=feature_names, plot_type="bar", show=False, max_display=25)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "07c_shap_global_bar_corrected_official.png", dpi=170, bbox_inches="tight")
    plt.close()

    fam_plot = family_df.sort_values("mean_abs_shap")
    plt.figure(figsize=(7.2, 4.8))
    plt.barh(fam_plot["feature_family"], fam_plot["mean_abs_shap"])
    plt.xlabel("Mean absolute SHAP")
    plt.title("Corrected official model feature-family SHAP")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "07c_shap_feature_family_importance_corrected_official.png", dpi=160)
    plt.close()

    push_plot = churn_df.head(12).iloc[::-1]
    plt.figure(figsize=(8.2, 5.2))
    plt.barh(push_plot["original_feature"], push_plot["top_minus_low_mean_shap"])
    plt.axvline(0, color="black", linewidth=0.8)
    plt.xlabel("Top churn-risk decile minus low-risk decile mean SHAP")
    plt.title("Corrected official model churn-risk top-decile SHAP push")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "07c_churn_risk_top_decile_shap_push.png", dpi=160)
    plt.close()

    dependence_files = []
    for rank, feature in enumerate(grouped_df.head(5)["original_feature"].tolist(), start=1):
        vals = grouped_matrix[feature].to_numpy()
        raw = raw_sample[feature].reset_index(drop=True)
        plt.figure(figsize=(6.4, 4.7))
        if pd.api.types.is_numeric_dtype(raw):
            plt.scatter(raw, vals, s=10, alpha=0.45, c=sample_meta["churn_risk_score"], cmap="coolwarm")
            plt.colorbar(label="churn_risk_score")
            plt.xlabel(feature)
        else:
            codes = pd.Categorical(raw.astype(str)).codes
            plt.scatter(codes, vals, s=10, alpha=0.45, c=sample_meta["churn_risk_score"], cmap="coolwarm")
            plt.colorbar(label="churn_risk_score")
            plt.xlabel(f"{feature} category code")
        plt.ylabel("Grouped SHAP toward repurchase score")
        plt.title(f"Dependence-style top {rank}: {feature}")
        plt.tight_layout()
        fname = f"07c_shap_dependence_top{rank:02d}_{sanitize_name(feature)}.png"
        plt.savefig(FIGURE_DIR / fname, dpi=160)
        plt.close()
        dependence_files.append(fname)

    waterfall_files = []
    for _, case in local_cases.iterrows():
        idx = sample_index_by_id.get(case[ID_COL])
        if idx is None:
            continue
        exp = shap.Explanation(
            values=shap_values[idx],
            base_values=np.asarray(base_values).ravel()[idx],
            data=X_trans_df.iloc[idx].values,
            feature_names=feature_names,
        )
        plt.figure()
        shap.plots.waterfall(exp, max_display=14, show=False)
        plt.tight_layout()
        prefix = {
            "high_churn_risk_true_N": "07c_waterfall_high_churn_risk_true_N",
            "high_churn_risk_false_positive": "07c_waterfall_high_churn_risk_false_positive",
            "low_churn_risk_true_Y": "07c_waterfall_low_churn_risk_true_Y",
            "mid_score_ambiguous": "07c_waterfall_mid_score_ambiguous",
        }[case["case_type"]]
        fname = f"{prefix}_{int(case[ID_COL])}.png"
        plt.savefig(FIGURE_DIR / fname, dpi=160, bbox_inches="tight")
        plt.close()
        waterfall_files.append(fname)

    figure_inventory = []
    recommended_names = {
        "07c_shap_beeswarm_red_blue_corrected_official.png",
        "07c_shap_global_bar_corrected_official.png",
        "07c_shap_feature_family_importance_corrected_official.png",
        "07c_churn_risk_top_decile_shap_push.png",
    }
    for path in sorted(FIGURE_DIR.glob("*.png")):
        figure_inventory.append(
            {
                "figure_file": path.name,
                "path": rel(path),
                "size_bytes": path.stat().st_size,
                "recommended_for_team_share": "Y" if path.name in recommended_names else "N",
            }
        )
    team_figs = [row["path"] for row in figure_inventory if row["recommended_for_team_share"] == "Y"]

    top10 = grouped_df.head(10)
    top_positive = direction_df[direction_df["mean_shap"] > 0].head(10)
    top_negative = direction_df[direction_df["mean_shap"] < 0].head(10)

    team_lines = [
        "# 07c Corrected TRUE SHAP Team Share Summary",
        "",
        "## Status",
        "- TRUE SHAP was computed for the corrected official Stage 06c2 model only.",
        f"- Model: {official_model}.",
        f"- Feature set: `{official_feature_set}`.",
        f"- Reconstructed AUC: {rebuilt_auc:.6f}; Stage 06c2 AUC: {recorded_auc:.6f}; difference: {auc_diff:.10f}.",
        "",
        "## Direction",
        "- Target `is_repurchase_label`: 1 = repurchase, 0 = non-repurchase / churn risk.",
        "- Positive SHAP pushes toward `repurchase_score`.",
        "- Negative SHAP pushes toward higher churn risk.",
        "",
        "## Top SHAP Features",
    ]
    for _, row in top10.iterrows():
        team_lines.append(f"- {row['original_feature']}: {row['mean_abs_shap']:.6f} ({row['feature_family']})")
    team_lines.extend(["", "## Feature Families"])
    for _, row in family_df.iterrows():
        team_lines.append(f"- {row['feature_family']}: {row['mean_abs_shap']:.6f}")
    team_lines.extend(
        [
            "",
            "## Recommended Figures",
        ]
    )
    for fig in team_figs:
        team_lines.append(f"- {fig}")
    team_lines.extend(
        [
            "",
            "## Do Not Claim",
            "- Do not claim causality, ROI, intervention lift, or business simulation results.",
            "- Do not use old 07r or 06h SHAP as final evidence.",
            "- Do not treat w1_4 as early-warning evidence.",
        ]
    )
    (DATA_DIR / "07c_team_share_shap_summary.md").write_text("\n".join(team_lines) + "\n", encoding="utf-8")

    report_lines = [
        "# 07c Corrected TRUE SHAP Interpretation Report",
        "",
        "## 1. TRUE SHAP Status",
        "- TRUE SHAP was successfully computed.",
        f"- SHAP version: {shap_version}.",
        f"- Python executable: `{sys.executable}`.",
        "",
        "## 2. Corrected Official Model Explained",
        f"- Model: {official_model}.",
        f"- Feature set: `{official_feature_set}`.",
        f"- Window: {official_window}.",
        "",
        "## 3. Model Reconstruction",
        f"- Reconstructed AUC: {rebuilt_auc:.6f}.",
        f"- Stage 06c2 recorded AUC: {recorded_auc:.6f}.",
        f"- Absolute difference: {auc_diff:.10f}.",
        "- Train/test USER_KEY overlap: 0.",
        "",
        "## 4. Top SHAP Features",
    ]
    for _, row in top10.iterrows():
        report_lines.append(f"- {row['original_feature']} ({row['feature_family']}): mean abs SHAP {row['mean_abs_shap']:.6f}.")
    report_lines.extend(["", "## 5. Top SHAP Feature Families"])
    for _, row in family_df.iterrows():
        report_lines.append(f"- {row['feature_family']}: mean abs SHAP {row['mean_abs_shap']:.6f}.")
    report_lines.extend(["", "## 6. Features Pushing Toward Repurchase"])
    for _, row in top_positive.iterrows():
        report_lines.append(f"- {row['original_feature']}: mean SHAP {row['mean_shap']:.6f}.")
    report_lines.extend(["", "## 7. Features Pushing Toward Churn Risk"])
    for _, row in top_negative.iterrows():
        report_lines.append(f"- {row['original_feature']}: mean SHAP {row['mean_shap']:.6f}.")
    report_lines.extend(
        [
            "",
            "## 8. Difference From Old 07r/06h SHAP",
            "- 07c explains the corrected official Stage 06c2 model and corrected v2c dataset.",
            "- Old 07r and 06h SHAP outputs are historical/provisional only because they were based on earlier pre-02c or pre-06c2 data.",
            "- Use `07c_previous_shap_comparison.csv` only for historical comparison, not final evidence.",
            "",
            "## 9. Figures To Share",
        ]
    )
    for fig in team_figs:
        report_lines.append(f"- {fig}")
    report_lines.extend(
        [
            "",
            "## 10. Must Not Be Claimed",
            "- Do not claim causality.",
            "- Do not claim ROI, profit, retention lift, or business simulation results.",
            "- Do not claim segmentation results from Stage 07c.",
            "- Do not claim old 07r or 06h SHAP as final evidence.",
            "- Do not reverse the SHAP direction. Positive SHAP means higher repurchase score, not higher churn risk.",
            "- Do not claim w1_4 as early-warning evidence.",
        ]
    )
    (DATA_DIR / "07c_true_shap_interpretation_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    summary_payload = {
        "stage": "07c_v2_corrected_true_shap_interpretation",
        "status": "PASS",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "sklearn_version": sklearn.__version__,
        "shap_version": shap_version,
        "true_shap_computed": True,
        "official_model": official_model,
        "official_feature_set": official_feature_set,
        "official_window": official_window,
        "target_mapping": {"is_repurchase_label": "1=repurchase, 0=non-repurchase/churn risk"},
        "score_direction": {
            "repurchase_score": "P(is_repurchase_label = 1)",
            "churn_risk_score": "1 - repurchase_score",
            "positive_shap": "pushes toward repurchase_score",
            "negative_shap": "pushes toward churn risk",
        },
        "reconstruction": reconstruction.to_dict("records")[0],
        "sample_rows": int(len(sample_meta)),
        "top10_shap_features": top10[["original_feature", "feature_family", "mean_abs_shap", "mean_shap"]].to_dict("records"),
        "top_feature_families": family_df.to_dict("records"),
        "recommended_team_figures": team_figs,
        "previous_shap_outputs_status": "07r and 06h are historical/provisional only.",
        "no_segmentation": True,
        "no_business_simulation": True,
        "no_optuna": True,
    }
    write_json(DATA_DIR / "07c_true_shap_summary.json", summary_payload)

    raw_after = snapshot_dir(PROJECT_ROOT / "_data")
    protected_after = snapshot_dir(STAGE06C2_DATA) | snapshot_dir(STAGE06C2_TABLES)
    protected_after = protected_after | snapshot_dir(BASE / "reports" / "data" / "07r_v2_true_shap_interpretation")
    protected_after = protected_after | snapshot_dir(BASE / "reports" / "tables" / "07r_v2_true_shap_interpretation")
    protected_after = protected_after | snapshot_dir(BASE / "reports" / "data" / "06h_v2_pruned_model_collinearity_shap_audit")
    protected_after = protected_after | snapshot_dir(BASE / "reports" / "tables" / "06h_v2_pruned_model_collinearity_shap_audit")

    required_tables = [
        TABLE_DIR / "07c_model_reconstruction_check.csv",
        TABLE_DIR / "07c_global_shap_importance.csv",
        TABLE_DIR / "07c_grouped_shap_importance.csv",
        TABLE_DIR / "07c_feature_family_shap_importance.csv",
        TABLE_DIR / "07c_shap_direction_summary.csv",
        TABLE_DIR / "07c_churn_risk_top_decile_shap_explanation.csv",
        TABLE_DIR / "07c_local_top_contributors.csv",
        TABLE_DIR / "07c_previous_shap_comparison.csv",
    ]
    required_data = [
        DATA_DIR / "07c_true_shap_summary.json",
        DATA_DIR / "07c_shap_sample_membership_rows.csv",
        DATA_DIR / "07c_local_explanation_cases.csv",
        DATA_DIR / "07c_team_share_shap_summary.md",
        DATA_DIR / "07c_true_shap_interpretation_report.md",
    ]
    required_figures = [
        FIGURE_DIR / "07c_shap_beeswarm_red_blue_corrected_official.png",
        FIGURE_DIR / "07c_shap_global_bar_corrected_official.png",
        FIGURE_DIR / "07c_shap_feature_family_importance_corrected_official.png",
        FIGURE_DIR / "07c_churn_risk_top_decile_shap_push.png",
    ]
    final_checks = [
        ("raw_files_unchanged", raw_before == raw_after, "No files under _data changed."),
        ("no_data_output_created", not (PROJECT_ROOT / "_data" / "07c_v2_corrected_true_shap_interpretation").exists(), "No 07c output under _data."),
        ("old_stage07_07r_06h_06c2_outputs_not_overwritten", protected_before == protected_after, "Protected historical and 06c2 snapshots unchanged."),
        ("shap_import_succeeded", bool(shap_version), shap_version),
        ("true_shap_values_computed", shap_values.size > 0, str(shap_values.shape)),
        ("red_blue_shap_beeswarm_created", required_figures[0].exists(), rel(required_figures[0])),
        ("official_corrected_model_reconstructed", reconstruction_status == "PASS", f"auc_diff={auc_diff:.10f}"),
        ("auc_difference_from_06c2_documented", (TABLE_DIR / "07c_model_reconstruction_check.csv").exists(), "reconstruction table created."),
        ("no_forbidden_features_used", not forbidden_used, f"violations={len(forbidden_used)}"),
        ("target_mapping_documented", True, "is_repurchase_label: 1=repurchase, 0=non-repurchase/churn risk."),
        ("score_direction_documented", True, "Positive SHAP pushes toward repurchase_score."),
        ("train_test_USER_KEY_overlap_zero", group_overlap == 0, f"overlap={group_overlap}"),
        ("feature_family_shap_table_created", (TABLE_DIR / "07c_feature_family_shap_importance.csv").exists(), "feature-family SHAP table created."),
        ("local_explanation_cases_created", (DATA_DIR / "07c_local_explanation_cases.csv").exists(), "local cases created."),
        ("previous_shap_comparison_created", (TABLE_DIR / "07c_previous_shap_comparison.csv").exists(), "historical comparison created."),
        ("no_segmentation_created", not any("08c" in str(p) or "segmentation" in str(p).lower() for p in DATA_DIR.rglob("*")), "Stage 07c created no segmentation."),
        ("no_business_simulation_created", not any("simulation" in str(p).lower() for p in DATA_DIR.rglob("*")), "Stage 07c created no business simulation."),
        ("no_optuna_run", "optuna" not in sys.modules, "Optuna not imported."),
        ("all_required_tables_created", all(p.exists() for p in required_tables), f"required_tables={len(required_tables)}"),
        ("all_required_data_outputs_created", all(p.exists() for p in required_data), f"required_data={len(required_data)}"),
        ("all_required_core_figures_created", all(p.exists() for p in required_figures), f"required_figures={len(required_figures)}"),
        ("dependence_style_top5_created", len(dependence_files) == 5, f"files={len(dependence_files)}"),
        ("local_waterfall_plots_created", len(waterfall_files) > 0, f"files={len(waterfall_files)}"),
    ]
    final_df = pd.DataFrame([{"check": n, "status": "PASS" if ok else "FAIL", "detail": d} for n, ok, d in final_checks])
    write_csv(TABLE_DIR / "07c_final_checks.csv", final_df)
    if (final_df["status"] != "PASS").any():
        raise RuntimeError("Stage 07c final checks failed.")

    print("07c_v2_corrected_true_shap_interpretation completed.")
    for row in final_df.to_dict("records"):
        print(f"{row['check']}: {row['status']} - {row['detail']}")


if __name__ == "__main__":
    main()
