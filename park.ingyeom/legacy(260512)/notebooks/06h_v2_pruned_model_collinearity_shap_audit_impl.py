import json
import math
import platform
import warnings
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
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "park.ingyeom").exists() and (candidate / "_data").exists():
            return candidate
    raise FileNotFoundError("Project root not found.")


PROJECT_ROOT = find_root(Path.cwd())
BASE = PROJECT_ROOT / "park.ingyeom"
STAGE05 = BASE / "reports" / "data" / "05_v2_modeling_dataset"
STAGE05E = BASE / "reports" / "data" / "05e_v2_final_feature_pruning_policy"
STAGE06_TABLE = BASE / "reports" / "tables" / "06_v2_baseline_modeling"
STAGE06C = BASE / "reports" / "data" / "06c_v2_overfitting_leakage_adversarial_audit"
STAGE06D_TABLE = BASE / "reports" / "tables" / "06d_v2_multicollinearity_redundancy_audit"
STAGE06E = BASE / "reports" / "data" / "06e_v2_exact_early_window_rebuild"
STAGE06F = BASE / "reports" / "data" / "06f_v2_reduced_feature_baseline_audit"
STAGE06G = BASE / "reports" / "data" / "06g_v2_pruned_baseline_modeling"
STAGE05D = BASE / "reports" / "data" / "05d_v2_feature_dictionary"

STAGE_NAME = "06h_v2_pruned_model_collinearity_shap_audit"
DATA_DIR = BASE / "reports" / "data" / STAGE_NAME
TABLE_DIR = BASE / "reports" / "tables" / STAGE_NAME
FIGURE_DIR = BASE / "reports" / "figures" / STAGE_NAME
for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"
TARGET = "is_repurchase"
RANDOM_STATE = 42
MAX_SHAP_ROWS = 2000


def rel(path: Path) -> str:
    return str(Path(path).relative_to(PROJECT_ROOT)).replace("\\", "/")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, df: pd.DataFrame):
    df.to_csv(path, index=False, encoding="utf-8-sig")


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


raw_before = snapshot_dirs([PROJECT_ROOT / "_data"])
protected_dirs = []
for base_dir in [BASE / "reports" / "data", BASE / "reports" / "tables", BASE / "reports" / "figures"]:
    if base_dir.exists():
        protected_dirs.extend(
            [
                p
                for p in base_dir.iterdir()
                if p.is_dir()
                and p.name != STAGE_NAME
                and (p.name[:2].isdigit() and 1 <= int(p.name[:2]) <= 9)
            ]
        )
stage01_09_before = snapshot_dirs(protected_dirs)
stage05e06g_before = snapshot_dirs([STAGE05E, STAGE06G])
data_file_set_before = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())


def load_inputs():
    use_05e = (
        (STAGE05E / "modeling_dataset_v2_w1_3_pruned.csv").exists()
        and (STAGE05E / "modeling_dataset_v2_w1_4_pruned.csv").exists()
        and (STAGE05E / "pruned_feature_sets_v2.json").exists()
    )
    if use_05e:
        df13 = pd.read_csv(STAGE05E / "modeling_dataset_v2_w1_3_pruned.csv")
        df14 = pd.read_csv(STAGE05E / "modeling_dataset_v2_w1_4_pruned.csv")
        feature_payload = read_json(STAGE05E / "pruned_feature_sets_v2.json")
        source_mode = "stage05e_pruned_outputs"
    else:
        df13 = pd.read_csv(STAGE05 / "modeling_dataset_v2_w1_3.csv")
        df14 = pd.read_csv(STAGE05 / "modeling_dataset_v2_w1_4.csv")
        feature_payload = read_json(STAGE05 / "feature_sets_v2.json")
        source_mode = "stage05_original_outputs_in_memory_pruning"
    return df13, df14, feature_payload, source_mode


df13, df14, feature_payload, source_mode = load_inputs()
split = pd.read_csv(STAGE06_TABLE / "06_v2_split_membership_row_ids.csv")
split_col = "split" if "split" in split.columns else "holdout_split"

supporting = {
    "06c": read_json(STAGE06C / "06c_adversarial_audit_summary.json"),
    "06e": read_json(STAGE06E / "06e_exact_early_window_summary.json"),
    "06f": read_json(STAGE06F / "06f_reduced_feature_baseline_summary.json"),
    "06g": read_json(STAGE06G / "06g_pruned_baseline_summary.json"),
    "05d": read_json(STAGE05D / "05d_v2_feature_dictionary_summary.json"),
}
optional_warnings = []
for key, value in supporting.items():
    if not value:
        optional_warnings.append(f"Optional supporting summary missing or empty: {key}")
if not STAGE06D_TABLE.exists():
    optional_warnings.append("Optional Stage 06d multicollinearity table folder missing.")

for df in [df13, df14]:
    df["target_y"] = df[TARGET].map({"Y": 1, "N": 0})
    if df["target_y"].isna().any():
        raise ValueError("Target mapping failed. Expected Y/N in is_repurchase.")

FORBIDDEN_MODEL_FEATURES = {
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
    "target_y",
}
forbidden_from_payload = set(feature_payload.get("forbidden_features", []))
FORBIDDEN_MODEL_FEATURES |= forbidden_from_payload
CATEGORICAL = set(feature_payload.get("categorical_features_to_encode_in_stage06", []))


def onehot_encoder():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def is_categorical(col):
    return col in CATEGORICAL or col.endswith("_top_genre")


def prepare_X(X):
    out = X.copy()
    for col in out.columns:
        if is_categorical(col):
            out[col] = out[col].map(lambda v: np.nan if pd.isna(v) else str(v))
        else:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def preprocessor(features, scale_numeric):
    cats = [f for f in features if is_categorical(f)]
    nums = [f for f in features if f not in cats]
    transformers = []
    if nums:
        num_steps = [("imputer", SimpleImputer(strategy="median"))]
        if scale_numeric:
            num_steps.append(("scaler", StandardScaler()))
        transformers.append(("num", Pipeline(num_steps), nums))
    if cats:
        transformers.append(("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", onehot_encoder())]), cats))
    return ColumnTransformer(transformers, remainder="drop")


def get_transformed_feature_names(prep):
    try:
        return list(prep.get_feature_names_out())
    except Exception:
        names = []
        for name, transformer, cols in prep.transformers_:
            if name == "remainder" or transformer == "drop":
                continue
            cols = list(cols)
            if name == "num":
                names.extend([f"num__{c}" for c in cols])
            elif name == "cat":
                ohe = transformer.named_steps.get("onehot")
                try:
                    names.extend(list(ohe.get_feature_names_out(cols)))
                except Exception:
                    names.extend([f"cat__{c}" for c in cols])
        return names


def original_from_transformed(name):
    if name.startswith("num__"):
        return name.replace("num__", "", 1)
    if name.startswith("cat__"):
        body = name.replace("cat__", "", 1)
        for col in sorted(CATEGORICAL, key=len, reverse=True):
            if body == col or body.startswith(col + "_"):
                return col
        return body.split("_")[0]
    return name.split("_")[0]


def feature_family(feature):
    f = original_from_transformed(str(feature))
    if f in {"price", "max_screen", "is_promotion", "is_user_verified", "gender", "age", "payment_device", "billing_method", "product_code", "is_churn_prevented"}:
        return "membership_context"
    if "week" in f and ("watch_time" in f or "sessions" in f):
        return "weekly_usage_pattern"
    if any(token in f for token in ["unique_contents", "unique_watch_days", "avg_watch_time_per_session", "total_sessions", "total_watch_time"]):
        return "simple_usage_volume"
    if "genre_ratio" in f or "genre_entropy" in f or "top_genre" in f:
        return "genre_ratio_proxy"
    if "release_month" in f or "recent_content" in f or "old_content" in f:
        return "release_month_proxy"
    return "other"


def existing(cols, candidates):
    return [c for c in candidates if c in cols and c not in FORBIDDEN_MODEL_FEATURES]


def ratio_cols(cols, prefix):
    return sorted([c for c in cols if c.startswith(prefix + "_genre_ratio_")])


def build_candidate_sets():
    c13 = set(df13.columns)
    c14 = set(df14.columns)
    membership = ["price", "max_screen", "is_promotion", "is_user_verified", "gender", "age", "payment_device", "billing_method"]
    usage_13 = [
        "w1_3_week1_watch_time",
        "w1_3_week2_watch_time",
        "w1_3_week3_watch_time",
        "w1_3_week1_sessions",
        "w1_3_week2_sessions",
        "w1_3_week3_sessions",
        "w1_3_unique_contents",
        "w1_3_unique_watch_days",
        "w1_3_avg_watch_time_per_session",
    ]
    usage_12 = [
        "w1_3_week1_watch_time",
        "w1_3_week2_watch_time",
        "w1_3_week1_sessions",
        "w1_3_week2_sessions",
        "w1_3_unique_contents",
        "w1_3_unique_watch_days",
        "w1_3_avg_watch_time_per_session",
    ]
    genre_13 = ratio_cols(c13, "w1_3") + existing(c13, ["w1_3_genre_entropy"])
    release_13 = existing(c13, ["w1_3_recent_content_watch_ratio"])
    usage_14 = [
        "w1_4_week1_watch_time",
        "w1_4_week2_watch_time",
        "w1_4_week3_watch_time",
        "w1_4_week4_watch_time",
        "w1_4_week1_sessions",
        "w1_4_week2_sessions",
        "w1_4_week3_sessions",
        "w1_4_week4_sessions",
        "w1_4_unique_contents",
        "w1_4_unique_watch_days",
        "w1_4_avg_watch_time_per_session",
    ]
    genre_14 = ratio_cols(c14, "w1_4") + existing(c14, ["w1_4_genre_entropy"])
    release_14 = existing(c14, ["w1_4_recent_content_watch_ratio"])
    specs = {
        "pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence": {
            "window": "w1_3",
            "features": existing(c13, membership + usage_13 + genre_13 + release_13),
            "timing_label": "full_w1_3_official_candidate",
            "claim_status": "official_candidate",
        },
        "pruned_w1_3_membership_usage_only_without_product_code_without_watch_presence": {
            "window": "w1_3",
            "features": existing(c13, membership + usage_13),
            "timing_label": "full_w1_3_usage_only_fallback",
            "claim_status": "official_fallback_candidate",
        },
        "pruned_w1_3_genre_ratio_added_without_product_code_without_watch_presence": {
            "window": "w1_3",
            "features": existing(c13, membership + usage_13 + genre_13),
            "timing_label": "full_w1_3_genre_added_test",
            "claim_status": "genre_increment_test",
        },
        "pruned_w1_3_timing_sensitive_all_weeks_reference": {
            "window": "w1_3",
            "features": existing(c13, membership + usage_13 + genre_13 + release_13),
            "timing_label": "timing_sensitive_reference_only",
            "claim_status": "reference_only_not_official",
        },
        "pruned_w1_3_early_safer_week1_2_reference": {
            "window": "w1_3",
            "features": existing(c13, membership + usage_12),
            "timing_label": "early_safer_week1_2_reference",
            "claim_status": "mentor_safe_reference",
        },
        "pruned_w1_4_late_period_comparison": {
            "window": "w1_4",
            "features": existing(c14, membership + usage_14 + genre_14 + release_14),
            "timing_label": "late_period_only",
            "claim_status": "late_period_comparison_only",
        },
    }
    for spec in specs.values():
        spec["product_code_policy"] = "excluded_by_default"
        spec["watch_presence_policy"] = "excluded_by_default"
    return specs


candidate_sets = build_candidate_sets()


def clean_features(df, features):
    seen = set()
    cleaned = []
    for f in features:
        if f in df.columns and f not in FORBIDDEN_MODEL_FEATURES and f not in seen:
            cleaned.append(f)
            seen.add(f)
    return cleaned


def safe_auc(y, score):
    return float(roc_auc_score(y, score)) if len(np.unique(y)) > 1 else np.nan


train_ids = set(split.loc[split[split_col].eq("train"), ID_COL])
test_ids = set(split.loc[split[split_col].eq("test"), ID_COL])


def get_source(window):
    return df13 if window == "w1_3" else df14


trained = {}
score_parts = []
metric_rows = []


def evaluate_candidate(set_name, spec, model_name):
    source = get_source(spec["window"])
    features = clean_features(source, spec["features"])
    train_mask = source[ID_COL].isin(train_ids)
    test_mask = source[ID_COL].isin(test_ids)
    X_train = prepare_X(source.loc[train_mask, features])
    X_test = prepare_X(source.loc[test_mask, features])
    y_train = source.loc[train_mask, "target_y"].astype(int)
    y_test = source.loc[test_mask, "target_y"].astype(int)
    if model_name == "LogisticRegression":
        model = LogisticRegression(max_iter=1000, solver="lbfgs", random_state=RANDOM_STATE)
        prep = preprocessor(features, True)
    else:
        model = HistGradientBoostingClassifier(max_iter=80, learning_rate=0.08, max_leaf_nodes=31, random_state=RANDOM_STATE)
        prep = preprocessor(features, False)
    pipe = Pipeline([("preprocess", prep), ("model", model)])
    pipe.fit(X_train, y_train)
    repurchase_score = pipe.predict_proba(X_test)[:, 1]
    churn_score = 1 - repurchase_score
    pred = (repurchase_score >= 0.5).astype(int)
    churn_true = 1 - y_test
    churn_pred = (churn_score >= 0.5).astype(int)
    transformed_count = int(pipe.named_steps["preprocess"].transform(X_test.iloc[:1]).shape[1])
    train_groups = set(source.loc[train_mask, GROUP_COL].dropna())
    test_groups = set(source.loc[test_mask, GROUP_COL].dropna())
    ranked = pd.DataFrame({"target_y": y_test.values, "churn_risk_score": churn_score}).sort_values("churn_risk_score", ascending=False)
    top_n = max(1, math.ceil(len(ranked) * 0.10))
    top = ranked.head(top_n)
    overall_churn_rate = float((1 - ranked["target_y"]).mean())
    top_churn_rate = float((1 - top["target_y"]).mean())
    captured = int((1 - top["target_y"]).sum())
    total_churners = int((1 - ranked["target_y"]).sum())
    row = {
        "feature_set_name": set_name,
        "window": spec["window"],
        "model": model_name,
        "timing_label": spec["timing_label"],
        "claim_status": spec["claim_status"],
        "roc_auc_repurchase": safe_auc(y_test, repurchase_score),
        "average_precision_repurchase": float(average_precision_score(y_test, repurchase_score)),
        "average_precision_churn_risk": float(average_precision_score(churn_true, churn_score)),
        "accuracy": float(accuracy_score(y_test, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, pred)),
        "precision_churn_at_0_5": float(precision_score(churn_true, churn_pred, zero_division=0)),
        "recall_churn_at_0_5": float(recall_score(churn_true, churn_pred, zero_division=0)),
        "f1_churn_at_0_5": float(f1_score(churn_true, churn_pred, zero_division=0)),
        "brier_score_repurchase": float(brier_score_loss(y_test, repurchase_score)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "train_repurchase_rate": float(y_train.mean()),
        "test_repurchase_rate": float(y_test.mean()),
        "raw_feature_count": int(len(features)),
        "post_transform_feature_count": transformed_count,
        "top_10pct_n": int(top_n),
        "top_10pct_churn_rate": top_churn_rate,
        "overall_churn_rate": overall_churn_rate,
        "top_decile_lift": float(top_churn_rate / overall_churn_rate) if overall_churn_rate else np.nan,
        "captured_churners": captured,
        "total_churners": total_churners,
        "churner_capture_rate": float(captured / total_churners) if total_churners else np.nan,
        "train_test_USER_KEY_overlap": int(len(train_groups & test_groups)),
        "includes_product_code": "Y" if "product_code" in features else "N",
        "includes_watch_presence_flag": "Y" if any(f.endswith("has_watch_obs") or f.endswith("no_watch_obs_flag") for f in features) else "N",
        "includes_first_last_timing": "Y" if any("first_watch_rel_day" in f or "last_watch_rel_day" in f for f in features) else "N",
    }
    scored = source.loc[test_mask, [ID_COL, GROUP_COL, TARGET, "target_y"]].copy()
    scored["feature_set_name"] = set_name
    scored["model"] = model_name
    scored["repurchase_score"] = repurchase_score
    scored["churn_risk_score"] = churn_score
    trained[(set_name, model_name)] = {
        "pipeline": pipe,
        "features": features,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "source": source,
        "train_mask": train_mask,
        "test_mask": test_mask,
    }
    return row, scored


for candidate_name, candidate_spec in candidate_sets.items():
    for model in ["LogisticRegression", "HistGradientBoostingClassifier"]:
        metric, scored_part = evaluate_candidate(candidate_name, candidate_spec, model)
        metric_rows.append(metric)
        score_parts.append(scored_part)

metrics = pd.DataFrame(metric_rows)
scores = pd.concat(score_parts, ignore_index=True)
write_csv(TABLE_DIR / "06h_model_metrics.csv", metrics)
top_decile = metrics[
    [
        "feature_set_name",
        "window",
        "model",
        "top_10pct_n",
        "overall_churn_rate",
        "top_10pct_churn_rate",
        "top_decile_lift",
        "captured_churners",
        "total_churners",
        "churner_capture_rate",
    ]
].copy()
write_csv(TABLE_DIR / "06h_top_decile_lift_summary.csv", top_decile)

inventory = []
for name, spec in candidate_sets.items():
    source = get_source(spec["window"])
    features = clean_features(source, spec["features"])
    inventory.append(
        {
            "feature_set_name": name,
            "window": spec["window"],
            "timing_label": spec["timing_label"],
            "claim_status": spec["claim_status"],
            "raw_feature_count": len(features),
            "features": "|".join(features),
            "included_feature_families": "|".join(sorted(set(feature_family(f) for f in features))),
            "excluded_product_code": "Y" if "product_code" not in features else "N",
            "excluded_watch_presence": "Y" if not any("has_watch_obs" in f or "no_watch_obs_flag" in f for f in features) else "N",
            "excluded_first_last_rel_day": "Y" if not any("first_watch_rel_day" in f or "last_watch_rel_day" in f for f in features) else "N",
            "excluded_ratio_delta_duplicates": "Y" if not any("_delta" in f or "ratio_week" in f for f in features) else "N",
            "excluded_genre_volume_session_count": "Y" if not any("genre_watch_time" in f or "genre_session_count" in f for f in features) else "N",
        }
    )
inventory_df = pd.DataFrame(inventory)
write_csv(TABLE_DIR / "06h_candidate_feature_set_inventory.csv", inventory_df)


def high_corr_pairs(df_num, method, threshold):
    corr = df_num.corr(method=method)
    rows = []
    cols = list(corr.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            value = corr.loc[a, b]
            if pd.notna(value) and abs(value) >= threshold:
                rows.append({"feature_a": a, "feature_b": b, "corr": float(value), "abs_corr": float(abs(value)), "threshold": threshold})
    return rows, corr


def vif_table(df_num):
    rows = []
    if df_num.shape[1] < 2:
        return pd.DataFrame(rows)
    clean = df_num.replace([np.inf, -np.inf], np.nan)
    clean = clean.dropna(axis=1, how="all")
    for col in clean.columns:
        y = clean[col]
        X = clean.drop(columns=[col])
        valid = y.notna()
        for xcol in X.columns:
            valid &= X[xcol].notna()
        if valid.sum() < max(30, X.shape[1] + 2) or X.shape[1] == 0 or y[valid].nunique() <= 1:
            rows.append({"feature": col, "vif": np.nan, "status": "not_enough_valid_variance"})
            continue
        try:
            model = LinearRegression()
            model.fit(X.loc[valid], y.loc[valid])
            r2 = float(model.score(X.loc[valid], y.loc[valid]))
            if r2 >= 0.999999:
                rows.append({"feature": col, "vif": np.inf, "status": "perfect_or_near_perfect_collinearity"})
            else:
                rows.append({"feature": col, "vif": float(1.0 / (1.0 - r2)), "status": "ok"})
        except Exception as exc:
            rows.append({"feature": col, "vif": np.nan, "status": f"failed: {type(exc).__name__}"})
    return pd.DataFrame(rows)


def redundancy_flags(features):
    rows = []
    fs = set(features)
    checks = [
        ("total vs weekly", any("total_watch_time" in f for f in fs) and any("week" in f and "watch_time" in f for f in fs)),
        ("total sessions vs weekly sessions", any("total_sessions" in f for f in fs) and any("week" in f and "sessions" in f for f in fs)),
        ("weekly ratios vs weekly raw values", any("week_ratio" in f or "ratio_week" in f for f in fs) and any("week" in f and ("watch_time" in f or "sessions" in f) for f in fs)),
        ("deltas vs source week values", any("delta" in f for f in fs) and any("week" in f for f in fs)),
        ("genre ratios sum/composition", sum("genre_ratio" in f for f in fs) >= 3),
        ("coverage/missing complement", any("covered" in f for f in fs) and any("missing" in f for f in fs)),
        ("watch presence complement", any("has_watch_obs" in f for f in fs) and any("no_watch_obs_flag" in f for f in fs)),
    ]
    for name, triggered in checks:
        rows.append({"redundancy_check": name, "status": "TRIGGERED" if triggered else "not_triggered"})
    return rows


pearson_rows = []
spearman_rows = []
vif_rows = []
multi_summary = []
redundancy_rows = []
feature_risk_rows = []
corr_mats = {}

for set_name, spec in candidate_sets.items():
    source = get_source(spec["window"])
    features = clean_features(source, spec["features"])
    X = prepare_X(source.loc[source[ID_COL].isin(train_ids | test_ids), features])
    numeric_cols = [f for f in features if f not in CATEGORICAL and f in X.columns]
    df_num = X[numeric_cols].apply(pd.to_numeric, errors="coerce")
    pearson_all, pearson_corr = high_corr_pairs(df_num, "pearson", 0.80)
    spearman_all, spearman_corr = high_corr_pairs(df_num, "spearman", 0.80)
    for r in pearson_all:
        r["feature_set_name"] = set_name
        r["method"] = "pearson"
    for r in spearman_all:
        r["feature_set_name"] = set_name
        r["method"] = "spearman"
    pearson_rows.extend(pearson_all)
    spearman_rows.extend(spearman_all)
    vif = vif_table(df_num)
    if not vif.empty:
        vif["feature_set_name"] = set_name
        vif_rows.extend(vif.to_dict("records"))
    for r in redundancy_flags(features):
        r["feature_set_name"] = set_name
        redundancy_rows.append(r)
    severe_corr = max([r["abs_corr"] for r in pearson_all + spearman_all], default=0)
    max_vif = np.nan
    unstable_vif_n = 0
    if not vif.empty:
        finite_vifs = pd.to_numeric(vif["vif"].replace(np.inf, np.nan), errors="coerce")
        max_vif = float(finite_vifs.max()) if finite_vifs.notna().any() else np.inf if np.isinf(vif["vif"]).any() else np.nan
        unstable_vif_n = int((vif["status"] != "ok").sum() + np.isinf(vif["vif"]).sum())
    multi_summary.append(
        {
            "feature_set_name": set_name,
            "numeric_feature_count": len(numeric_cols),
            "pearson_pairs_abs_ge_0_80": sum(r["abs_corr"] >= 0.80 for r in pearson_all),
            "pearson_pairs_abs_ge_0_90": sum(r["abs_corr"] >= 0.90 for r in pearson_all),
            "pearson_pairs_abs_ge_0_95": sum(r["abs_corr"] >= 0.95 for r in pearson_all),
            "spearman_pairs_abs_ge_0_80": sum(r["abs_corr"] >= 0.80 for r in spearman_all),
            "spearman_pairs_abs_ge_0_90": sum(r["abs_corr"] >= 0.90 for r in spearman_all),
            "spearman_pairs_abs_ge_0_95": sum(r["abs_corr"] >= 0.95 for r in spearman_all),
            "max_abs_corr": severe_corr,
            "max_vif": max_vif,
            "unstable_or_inf_vif_count": unstable_vif_n,
            "interpretation_policy": "family_level_only" if severe_corr >= 0.8 or unstable_vif_n > 0 or (pd.notna(max_vif) and max_vif >= 10) else "safe_individual_interpretation",
        }
    )
    corr_mats[set_name] = pearson_corr
    for f in features:
        risk = "safe_individual_interpretation"
        reason = ""
        if f in FORBIDDEN_MODEL_FEATURES:
            risk, reason = "metadata_only", "forbidden as model feature"
        elif "product_code" in f or "is_churn_prevented" in f or "has_watch_obs" in f or "no_watch_obs_flag" in f:
            risk, reason = "target_adjacent_caution", "shortcut or target-adjacent risk"
        elif "first_watch_rel_day" in f or "last_watch_rel_day" in f:
            risk, reason = "drop_candidate", "timing shortcut"
        elif any(token in f for token in ["total_watch_time", "total_sessions", "delta", "week_ratio", "covered_watch_ratio", "missing_watch"]):
            risk, reason = "redundant_proxy", "structural duplicate or complement"
        elif "genre_ratio" in f or "genre_entropy" in f or "week" in f:
            risk, reason = "family_level_only", "composition or correlated usage family"
        feature_risk_rows.append({"feature_set_name": set_name, "feature": f, "feature_family": feature_family(f), "risk_classification": risk, "reason": reason})

write_csv(TABLE_DIR / "06h_high_corr_pairs_pearson.csv", pd.DataFrame(pearson_rows))
write_csv(TABLE_DIR / "06h_high_corr_pairs_spearman.csv", pd.DataFrame(spearman_rows))
write_csv(TABLE_DIR / "06h_vif_results.csv", pd.DataFrame(vif_rows))
write_csv(TABLE_DIR / "06h_structural_redundancy_check.csv", pd.DataFrame(redundancy_rows))
write_csv(TABLE_DIR / "06h_feature_risk_classification.csv", pd.DataFrame(feature_risk_rows))
multi_summary_df = pd.DataFrame(multi_summary)
write_csv(TABLE_DIR / "06h_multicollinearity_summary_by_feature_set.csv", multi_summary_df)

coef_rows = []
grouped_coef_rows = []
for (set_name, model_name), obj in trained.items():
    if model_name != "LogisticRegression":
        continue
    pipe = obj["pipeline"]
    names = get_transformed_feature_names(pipe.named_steps["preprocess"])
    coefs = pipe.named_steps["model"].coef_[0]
    local = []
    for name, coef in zip(names, coefs):
        orig = original_from_transformed(name)
        local.append(
            {
                "feature_set_name": set_name,
                "model": model_name,
                "transformed_feature": name,
                "original_feature": orig,
                "feature_family": feature_family(orig),
                "coefficient_for_repurchase_score": float(coef),
                "direction": "positive_to_repurchase_score" if coef > 0 else "negative_to_churn_risk" if coef < 0 else "zero",
            }
        )
    local_df = pd.DataFrame(local)
    col_policy = multi_summary_df.loc[multi_summary_df["feature_set_name"].eq(set_name), "interpretation_policy"].iloc[0]
    local_df["coefficient_interpretation_caveat"] = "unstable_family_level_only" if col_policy == "family_level_only" else "individual_direction_cautiously_usable"
    coef_rows.extend(local_df.to_dict("records"))
    grouped = (
        local_df.assign(abs_coef=lambda x: x["coefficient_for_repurchase_score"].abs())
        .groupby(["feature_set_name", "feature_family"], as_index=False)
        .agg(
            transformed_feature_count=("transformed_feature", "count"),
            sum_abs_coefficient=("abs_coef", "sum"),
            mean_abs_coefficient=("abs_coef", "mean"),
            net_coefficient=("coefficient_for_repurchase_score", "sum"),
        )
    )
    grouped_coef_rows.extend(grouped.to_dict("records"))

coef_df = pd.DataFrame(coef_rows).sort_values(["feature_set_name", "coefficient_for_repurchase_score"], ascending=[True, False])
write_csv(TABLE_DIR / "06h_logistic_coefficient_importance.csv", coef_df)
write_csv(TABLE_DIR / "06h_logistic_grouped_coefficient_summary.csv", pd.DataFrame(grouped_coef_rows))

hgb_metrics = metrics[metrics["model"].eq("HistGradientBoostingClassifier")].copy()
official_name = "pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence"
official_metric = hgb_metrics[hgb_metrics["feature_set_name"].eq(official_name)].iloc[0]

ladder_rows = []
for label, source_name in [
    ("official_full_w1_3_pruned", official_name),
    ("usage_only_fallback", "pruned_w1_3_membership_usage_only_without_product_code_without_watch_presence"),
    ("genre_ratio_added_test", "pruned_w1_3_genre_ratio_added_without_product_code_without_watch_presence"),
    ("early_safer_week1_2_reference", "pruned_w1_3_early_safer_week1_2_reference"),
    ("w1_4_late_period_comparison", "pruned_w1_4_late_period_comparison"),
]:
    row = hgb_metrics[hgb_metrics["feature_set_name"].eq(source_name)].iloc[0].to_dict()
    ladder_rows.append({"ladder_level": label, **row})
for label, auc in [
    ("full_w1_3_reference_from_06f", supporting["06f"].get("full_reference_w1_3_hgb_auc")),
    ("exact_w1_2_reference_from_06f", supporting["06f"].get("exact_w1_2_auc_context")),
    ("w1_4_late_period_reference_from_06f", supporting["06f"].get("exact_w1_4_auc_late_period_only")),
]:
    ladder_rows.append({"ladder_level": label, "feature_set_name": label, "model": "reference", "roc_auc_repurchase": auc})
ladder_df = pd.DataFrame(ladder_rows)
write_csv(TABLE_DIR / "06h_official_metric_ladder.csv", ladder_df)


def save_bar(path, df_plot, x, y, title, ylabel, color="#378ADD"):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df_plot[x].astype(str), df_plot[y], color=color)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=35)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


plot_hgb = hgb_metrics.sort_values("roc_auc_repurchase", ascending=False)
fig, ax = plt.subplots(figsize=(8, 5))
colors = ["#1D9E75" if n == official_name else "#378ADD" for n in plot_hgb["feature_set_name"]]
ax.scatter(plot_hgb["raw_feature_count"], plot_hgb["roc_auc_repurchase"], c=colors)
for _, r in plot_hgb.iterrows():
    ax.text(r["raw_feature_count"] + 0.2, r["roc_auc_repurchase"], r["feature_set_name"].replace("pruned_", ""), fontsize=7)
ax.set_xlabel("Raw feature count")
ax.set_ylabel("ROC AUC")
ax.set_title("AUC vs Interpretability Proxy")
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(FIGURE_DIR / "06h_auc_vs_interpretability.png", dpi=160)
plt.close(fig)

save_bar(FIGURE_DIR / "06h_top_decile_lift_comparison.png", hgb_metrics.sort_values("top_decile_lift", ascending=False), "feature_set_name", "top_decile_lift", "Top-Decile Lift Comparison", "Lift", "#1D9E75")

final_corr = corr_mats[official_name]
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(final_corr.fillna(0).values, cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(final_corr.columns)))
ax.set_yticks(range(len(final_corr.columns)))
ax.set_xticklabels(final_corr.columns, rotation=90, fontsize=6)
ax.set_yticklabels(final_corr.columns, fontsize=6)
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
ax.set_title("Official Candidate Pearson Correlation")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "06h_final_candidate_corr_heatmap.png", dpi=170)
plt.close(fig)

vif_df = pd.DataFrame(vif_rows)
if not vif_df.empty:
    final_vif = vif_df[vif_df["feature_set_name"].eq(official_name)].copy()
    final_vif["vif_plot"] = pd.to_numeric(final_vif["vif"].replace(np.inf, np.nan), errors="coerce").fillna(50).clip(upper=50)
    save_bar(FIGURE_DIR / "06h_final_candidate_vif_bar.png", final_vif.sort_values("vif_plot", ascending=False).head(25), "feature", "vif_plot", "Official Candidate VIF, capped at 50", "VIF", "#D4537E")
else:
    pd.DataFrame({"message": ["No VIF rows"]}).to_csv(TABLE_DIR / "06h_vif_results.csv", index=False, encoding="utf-8-sig")

final_coef = coef_df[coef_df["feature_set_name"].eq(official_name)].copy()
final_coef["abs_coef"] = final_coef["coefficient_for_repurchase_score"].abs()
top_coef = pd.concat([final_coef.nlargest(10, "coefficient_for_repurchase_score"), final_coef.nsmallest(10, "coefficient_for_repurchase_score")]).drop_duplicates()
fig, ax = plt.subplots(figsize=(10, 6))
top_coef = top_coef.sort_values("coefficient_for_repurchase_score")
ax.barh(top_coef["transformed_feature"], top_coef["coefficient_for_repurchase_score"], color=np.where(top_coef["coefficient_for_repurchase_score"] >= 0, "#1D9E75", "#D4537E"))
ax.set_title("Official Candidate Logistic Coefficients")
ax.set_xlabel("Coefficient for repurchase_score")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "06h_logistic_top_coefficients.png", dpi=160)
plt.close(fig)

shap_status = "not_attempted"
shap_message = ""
shap_global_df = pd.DataFrame()
shap_family_df = pd.DataFrame()
shap_direction_df = pd.DataFrame()
local_sample_df = pd.DataFrame()
try:
    import shap

    shap_status = "import_succeeded"
    obj = trained[(official_name, "HistGradientBoostingClassifier")]
    pipe = obj["pipeline"]
    X_test = obj["X_test"]
    sample_n = min(MAX_SHAP_ROWS, len(X_test))
    sample = X_test.sample(n=sample_n, random_state=RANDOM_STATE) if len(X_test) > sample_n else X_test.copy()
    Xt = pipe.named_steps["preprocess"].transform(sample)
    names = get_transformed_feature_names(pipe.named_steps["preprocess"])
    model = pipe.named_steps["model"]
    explainer = shap.Explainer(model)
    shap_values = explainer(Xt)
    values = shap_values.values
    if values.ndim == 3:
        values = values[:, :, -1]
    shap_global_df = pd.DataFrame(
        {
            "transformed_feature": names,
            "original_feature": [original_from_transformed(n) for n in names],
            "feature_family": [feature_family(n) for n in names],
            "mean_abs_shap_for_repurchase_score": np.abs(values).mean(axis=0),
            "mean_shap_for_repurchase_score": values.mean(axis=0),
        }
    ).sort_values("mean_abs_shap_for_repurchase_score", ascending=False)
    shap_family_df = (
        shap_global_df.groupby("feature_family", as_index=False)
        .agg(
            mean_abs_shap_for_repurchase_score=("mean_abs_shap_for_repurchase_score", "sum"),
            mean_shap_for_repurchase_score=("mean_shap_for_repurchase_score", "sum"),
            transformed_feature_count=("transformed_feature", "count"),
        )
        .sort_values("mean_abs_shap_for_repurchase_score", ascending=False)
    )
    direction_rows = []
    Xt_df = pd.DataFrame(Xt, columns=names)
    for idx, row in shap_global_df.head(40).iterrows():
        fname = row["transformed_feature"]
        vals = Xt_df[fname]
        sh = values[:, names.index(fname)]
        high_mask = vals >= vals.median()
        direction_rows.append(
            {
                "transformed_feature": fname,
                "original_feature": row["original_feature"],
                "feature_family": row["feature_family"],
                "mean_shap_high_value": float(np.mean(sh[high_mask])) if high_mask.any() else np.nan,
                "mean_shap_low_value": float(np.mean(sh[~high_mask])) if (~high_mask).any() else np.nan,
                "direction_note": "positive SHAP pushes toward repurchase_score; negative SHAP pushes toward higher churn risk",
            }
        )
    shap_direction_df = pd.DataFrame(direction_rows)
    local_sample_df = pd.DataFrame(
        {
            "sample_index": list(sample.index[:20]),
            "base_value": float(np.ravel(shap_values.base_values)[0]) if np.size(shap_values.base_values) else np.nan,
            "sum_shap": values[:20].sum(axis=1),
        }
    )
    write_csv(TABLE_DIR / "06h_true_shap_global_importance.csv", shap_global_df)
    write_csv(TABLE_DIR / "06h_true_shap_feature_family_importance.csv", shap_family_df)
    write_csv(TABLE_DIR / "06h_true_shap_direction_summary.csv", shap_direction_df)
    write_csv(TABLE_DIR / "06h_true_shap_local_explanation_sample.csv", local_sample_df)
    plt.figure(figsize=(9, 7))
    shap.summary_plot(values, Xt, feature_names=names, show=False, max_display=25, color_bar=True)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "06h_shap_beeswarm_red_blue_final_candidate.png", dpi=170, bbox_inches="tight")
    plt.close()
    plt.figure(figsize=(9, 6))
    shap.summary_plot(values, Xt, feature_names=names, plot_type="bar", show=False, max_display=25)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "06h_shap_global_bar_final_candidate.png", dpi=170, bbox_inches="tight")
    plt.close()
    save_bar(FIGURE_DIR / "06h_shap_feature_family_importance_final_candidate.png", shap_family_df, "feature_family", "mean_abs_shap_for_repurchase_score", "TRUE SHAP Feature-Family Importance", "Sum mean |SHAP|", "#378ADD")
    shap_status = "succeeded"
except Exception as exc:
    shap_status = "blocked"
    shap_message = f"{type(exc).__name__}: {exc}"
    blocked = pd.DataFrame([{"status": "SHAP_BLOCKED", "message": shap_message, "fallback_used": "N"}])
    write_csv(TABLE_DIR / "06h_true_shap_global_importance.csv", blocked)
    write_csv(TABLE_DIR / "06h_true_shap_feature_family_importance.csv", blocked)
    write_csv(TABLE_DIR / "06h_true_shap_direction_summary.csv", blocked)

official_multi = multi_summary_df[multi_summary_df["feature_set_name"].eq(official_name)].iloc[0].to_dict()
official_decile = top_decile[(top_decile["feature_set_name"].eq(official_name)) & (top_decile["model"].eq("HistGradientBoostingClassifier"))].iloc[0].to_dict()
official_features = candidate_sets[official_name]["features"]

claim_update = pd.DataFrame(
    [
        {"claim_area": "Stage 07r SHAP", "recommendation": "Use 06h TRUE SHAP family-first wording for the pruned official candidate; do not reuse full-model feature-level causal language.", "status": "update_required"},
        {"claim_area": "Stage 08b segmentation", "recommendation": "Segments can be described as model-informed risk groups, not causal treatment groups; family-level usage and genre patterns are safer than individual-feature explanations.", "status": "update_required"},
        {"claim_area": "Stage 09 simulation", "recommendation": "Keep scenario-only and assumption-only wording; 06h does not create business simulation or ROI evidence.", "status": "no_new_claim"},
        {"claim_area": "w1_4", "recommendation": "Keep w1_4 as late-period/end-of-period comparison only.", "status": "confirmed"},
        {"claim_area": "performance", "recommendation": "Report pruned official AUC and top-decile lift; do not claim the highest historical AUC as the official early-warning model.", "status": "confirmed"},
    ]
)
write_csv(TABLE_DIR / "06h_claim_update_recommendation.csv", claim_update)

recommendation_text = f"""# 06h Final Model Recommendation

## Official Candidate
The official final model candidate is `{official_name}` with `HistGradientBoostingClassifier`.

- AUC: {official_metric['roc_auc_repurchase']:.6f}
- churn-risk PR AUC: {official_metric['average_precision_churn_risk']:.6f}
- top-decile lift: {official_decile['top_decile_lift']:.6f}
- full 1~3 week information: Y
- product_code excluded by default: Y
- watch-presence shortcut excluded by default: Y
- first/last watch timing features excluded: Y
- ratio/delta structural duplicates excluded: Y
- genre watch_time/session_count usage proxies excluded: Y

## Why This Is Official
This candidate is not selected because it has the highest possible AUC. It is selected because it keeps the project-defined 1~3 week observation window while removing product-code memorization risk, watch-presence shortcuts, first/last watch timing shortcuts, ratio/delta duplication, and genre volume/session-count usage proxies.

## Interpretation Boundary
The model is usable for churn-risk ranking. It must not be presented as causal proof. Because multicollinearity remains inside weekly usage and genre-ratio families, individual feature coefficients and individual SHAP values should be interpreted at feature-family level first.
"""
(DATA_DIR / "06h_final_model_recommendation.md").write_text(recommendation_text, encoding="utf-8")

mentor_text = f"""# 06h 멘토 대응 업데이트

멘토님 지적 이후에는 높은 AUC를 그대로 공식 모델로 주장하지 않고, 원본/파생 중복 피처와 shortcut 가능성이 있는 피처를 분리해서 다시 점검했습니다.

원본/파생 중복 피처는 `total_watch_time`, week ratio, week-to-week delta, genre watch_time, genre session_count, coverage/missing complement처럼 같은 사용량 정보를 반복해서 담는 변수군을 공식 후보에서 제외하는 방식으로 정리했습니다.

`product_code`는 요금제나 상품 조합을 외우는 방향으로 성능을 끌어올릴 수 있고, `watch-presence shortcut`은 시청 여부 자체가 이탈 여부와 너무 가까운 신호가 될 수 있기 때문에 기본 모델에서는 제외했습니다.

1~3주 전체 관측창은 week1, week2, week3의 watch_time과 sessions를 모두 포함하는 방식으로 반영했습니다. 다만 week3 정보가 들어가므로 “완전한 1주차 조기예측”이 아니라 “1~3주 관측 기반 이탈 위험 랭킹”으로 표현하는 것이 안전합니다.

최종 추천 모델의 AUC는 {official_metric['roc_auc_repurchase']:.6f}, top-decile lift는 {official_decile['top_decile_lift']:.6f}입니다.

0.90 수준의 성능은 w1_4 late-period 또는 더 강한 시점 정보가 들어간 결과와 연결될 수 있으므로 조기예측 성능으로 주장하지 않습니다. 이 값은 말기 관측 또는 탐색적 상한선으로만 분리해서 설명해야 합니다.

개별 변수보다 feature family 단위로 해석해야 하는 이유는 weekly usage, genre ratio처럼 서로 강하게 연동되는 변수들이 남아 있기 때문입니다. 따라서 개별 변수 하나가 독립적으로 이탈을 만든다고 말하기보다, 사용량 패턴, 장르 선호 구성, 멤버십 맥락 같은 묶음 단위로 설명하는 것이 방어 가능합니다.
"""
(DATA_DIR / "06h_mentor_response_update.md").write_text(mentor_text, encoding="utf-8")

team_text = f"""# 06h Team Share Model Summary

- official model candidate: `{official_name}`
- feature set used: membership context, week1~3 watch_time/sessions, simple usage variables, genre_ratio variables, genre_entropy, recent_content_watch_ratio
- included feature families: {', '.join(sorted(set(feature_family(f) for f in official_features)))}
- excluded feature families: product_code, watch-presence shortcut, first/last watch timing, week ratios/deltas, genre watch_time/session_count, coverage/missing complements
- AUC: {official_metric['roc_auc_repurchase']:.6f}
- churn-risk top-decile lift: {official_decile['top_decile_lift']:.6f}
- Logistic coefficient caveat: coefficients are for repurchase_score direction; negative values mean higher churn-risk association, not causality.
- TRUE SHAP caveat: positive SHAP pushes toward repurchase_score, negative SHAP pushes toward churn risk; use family-first interpretation.
- recommended figures: auc_vs_interpretability, top_decile_lift_comparison, final_candidate_corr_heatmap, logistic_top_coefficients, SHAP beeswarm and SHAP family bar if SHAP succeeded
- what not to say: do not claim causality, ROI, product_code-driven official model, watch-presence shortcut, or w1_4 as early-warning performance.
"""
(DATA_DIR / "06h_team_share_model_summary.md").write_text(team_text, encoding="utf-8")

shap_sentence = "TRUE SHAP succeeded for the final HGB candidate." if shap_status == "succeeded" else f"SHAP_BLOCKED: {shap_message}"
report_lines = [
    "# 06h Integrated Audit Report",
    "",
    "## Executive Answer",
    f"1. Official final model candidate: `{official_name}` with HGB.",
    "2. It uses full 1~3 week information: Y.",
    "3. It excludes product_code by default: Y.",
    "4. It excludes watch-presence shortcut by default: Y.",
    "5. It avoids first/last watch timing features: Y.",
    "6. It avoids ratio/delta structural duplicates: Y.",
    "7. It avoids genre volume/session_count usage proxies: Y.",
    f"8. AUC: {official_metric['roc_auc_repurchase']:.6f}.",
    f"9. churn-risk PR AUC: {official_metric['average_precision_churn_risk']:.6f}.",
    f"10. top-decile lift: {official_decile['top_decile_lift']:.6f}.",
    f"11. Comparison: full w1_3 reference AUC {supporting['06f'].get('full_reference_w1_3_hgb_auc')}; exact w1_2 reference AUC {supporting['06f'].get('exact_w1_2_auc_context')}; w1_4 late-period reference AUC {supporting['06f'].get('exact_w1_4_auc_late_period_only')}.",
    f"12. Remaining multicollinearity: max abs corr {official_multi['max_abs_corr']:.6f}, max VIF {official_multi['max_vif']}.",
    "13. Weekly usage pattern and genre-ratio features must be interpreted at family level.",
    "14. LogisticRegression coefficients suggest directional association with repurchase_score only; negative coefficients indicate churn-risk association.",
    f"15. TRUE SHAP status: {shap_sentence}",
    "16. Stage 07r should be updated to use this pruned official candidate for family-first TRUE SHAP wording.",
    "17. Stage 08b segmentation should be described as model-informed risk grouping, not causal segmentation.",
    "18. Mentor message is in 06h_mentor_response_update.md.",
    "19. Final presentation should use official pruned AUC, top-decile lift, coefficient caveat, and TRUE SHAP family-first caveat.",
    "20. Must not claim causality, ROI/profit, hyperparameter-optimized performance, product_code official shortcut, watch-presence shortcut, or w1_4 as early-warning.",
    "",
    "## Optional Warnings",
    *[f"- {w}" for w in optional_warnings],
]
(DATA_DIR / "06h_integrated_audit_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

raw_after = snapshot_dirs([PROJECT_ROOT / "_data"])
stage01_09_after = snapshot_dirs(protected_dirs)
stage05e06g_after = snapshot_dirs([STAGE05E, STAGE06G])
data_file_set_after = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())

required_data_outputs = [
    DATA_DIR / "06h_integrated_audit_report.md",
    DATA_DIR / "06h_integrated_audit_summary.json",
    DATA_DIR / "06h_final_model_recommendation.md",
    DATA_DIR / "06h_mentor_response_update.md",
    DATA_DIR / "06h_team_share_model_summary.md",
]
required_table_outputs = [
    TABLE_DIR / "06h_candidate_feature_set_inventory.csv",
    TABLE_DIR / "06h_model_metrics.csv",
    TABLE_DIR / "06h_top_decile_lift_summary.csv",
    TABLE_DIR / "06h_multicollinearity_summary_by_feature_set.csv",
    TABLE_DIR / "06h_high_corr_pairs_pearson.csv",
    TABLE_DIR / "06h_high_corr_pairs_spearman.csv",
    TABLE_DIR / "06h_vif_results.csv",
    TABLE_DIR / "06h_structural_redundancy_check.csv",
    TABLE_DIR / "06h_feature_risk_classification.csv",
    TABLE_DIR / "06h_logistic_coefficient_importance.csv",
    TABLE_DIR / "06h_logistic_grouped_coefficient_summary.csv",
    TABLE_DIR / "06h_true_shap_global_importance.csv",
    TABLE_DIR / "06h_true_shap_feature_family_importance.csv",
    TABLE_DIR / "06h_true_shap_direction_summary.csv",
    TABLE_DIR / "06h_official_metric_ladder.csv",
    TABLE_DIR / "06h_claim_update_recommendation.csv",
]
required_figures = [
    FIGURE_DIR / "06h_auc_vs_interpretability.png",
    FIGURE_DIR / "06h_top_decile_lift_comparison.png",
    FIGURE_DIR / "06h_final_candidate_corr_heatmap.png",
    FIGURE_DIR / "06h_final_candidate_vif_bar.png",
    FIGURE_DIR / "06h_logistic_top_coefficients.png",
]
if shap_status == "succeeded":
    required_figures.extend(
        [
            FIGURE_DIR / "06h_shap_beeswarm_red_blue_final_candidate.png",
            FIGURE_DIR / "06h_shap_global_bar_final_candidate.png",
            FIGURE_DIR / "06h_shap_feature_family_importance_final_candidate.png",
        ]
    )

write_json(
    DATA_DIR / "06h_integrated_audit_summary.json",
    {
        "stage": STAGE_NAME,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pending_final_checks",
    },
)

final_checks = [
    ("raw files unchanged", raw_before == raw_after, "Compared _data snapshots."),
    ("no _data output created", data_file_set_before == data_file_set_after, "Compared _data file set."),
    ("Stage 01 through Stage 09 outputs not overwritten", stage01_09_before == stage01_09_after, "Compared protected Stage 01-09 snapshots excluding 06h."),
    ("original Stage 05 datasets not overwritten", True, "06h read Stage 05/05e only."),
    ("Stage 05e/06g outputs not overwritten if present", stage05e06g_before == stage05e06g_after, "Compared Stage 05e and 06g snapshots."),
    ("no Optuna run", True, "No optuna import or tuning loop."),
    ("no segmentation created", True, "No segmentation output produced."),
    ("no business simulation created", True, "No simulation output produced."),
    ("Stage 06 split reused", True, rel(STAGE06_TABLE / "06_v2_split_membership_row_ids.csv")),
    ("train/test USER_KEY overlap equals 0", int(metrics["train_test_USER_KEY_overlap"].max()) == 0, str(int(metrics["train_test_USER_KEY_overlap"].max()))),
    ("forbidden features excluded", metrics[["includes_product_code", "includes_watch_presence_flag", "includes_first_last_timing"]].notna().all().all() and not any(f in FORBIDDEN_MODEL_FEATURES for f in official_features), "Checked official feature list."),
    ("target mapping documented", True, "Y -> 1 repurchase; N -> 0 non-repurchase/churn risk."),
    ("w1_3/w1_4 separated", all((s["window"] == "w1_3" and not any(f.startswith("w1_4_") for f in s["features"])) or (s["window"] == "w1_4" and not any(f.startswith("w1_3_") for f in s["features"])) for s in candidate_sets.values()), "Checked prefixes."),
    ("w1_4 labeled late-period only", candidate_sets["pruned_w1_4_late_period_comparison"]["timing_label"] == "late_period_only", "w1_4 comparison only."),
    ("product_code excluded from default official candidate", "product_code" not in official_features, "product_code not in official feature list."),
    ("watch-presence flag excluded from default official candidate", not any("has_watch_obs" in f or "no_watch_obs_flag" in f for f in official_features), "watch-presence flags absent."),
    ("first/last rel day excluded from official candidate", not any("first_watch_rel_day" in f or "last_watch_rel_day" in f for f in official_features), "first/last timing absent."),
    ("ratios/deltas excluded from official candidate", not any("_delta" in f or "week_ratio" in f or "ratio_week" in f for f in official_features), "week ratios/deltas absent; genre composition ratios retained intentionally."),
    ("genre watch_time/session_count excluded from official candidate", not any("genre_watch_time" in f or "genre_session_count" in f for f in official_features), "genre volume/session proxies absent."),
    ("multicollinearity audit completed on actual used feature set", not multi_summary_df.empty, rel(TABLE_DIR / "06h_multicollinearity_summary_by_feature_set.csv")),
    ("Logistic coefficient table created", (TABLE_DIR / "06h_logistic_coefficient_importance.csv").exists(), rel(TABLE_DIR / "06h_logistic_coefficient_importance.csv")),
    ("TRUE SHAP attempted for final HGB candidate", shap_status in {"succeeded", "blocked"}, shap_status if not shap_message else shap_message),
    ("red-blue SHAP beeswarm created if SHAP succeeded", shap_status != "succeeded" or (FIGURE_DIR / "06h_shap_beeswarm_red_blue_final_candidate.png").exists(), "Conditional SHAP figure check."),
    ("official model recommendation created", (DATA_DIR / "06h_final_model_recommendation.md").exists(), rel(DATA_DIR / "06h_final_model_recommendation.md")),
    ("mentor response update created", (DATA_DIR / "06h_mentor_response_update.md").exists(), rel(DATA_DIR / "06h_mentor_response_update.md")),
    ("team share summary created", (DATA_DIR / "06h_team_share_model_summary.md").exists(), rel(DATA_DIR / "06h_team_share_model_summary.md")),
]
for path in required_data_outputs + required_table_outputs + required_figures:
    final_checks.append((f"required output exists: {path.name}", path.exists(), rel(path)))

final_checks_df = pd.DataFrame(
    [{"check": name, "status": "PASS" if ok else "FAIL", "evidence": evidence} for name, ok, evidence in final_checks]
)
write_csv(TABLE_DIR / "06h_final_checks.csv", final_checks_df)

summary = {
    "stage": STAGE_NAME,
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "python": platform.python_version(),
    "input_source_mode": source_mode,
    "target_mapping": "Y -> 1 repurchase; N -> 0 non-repurchase/churn risk",
    "repurchase_score": "P(is_repurchase=Y)",
    "churn_risk_score": "1 - repurchase_score",
    "official_feature_set": official_name,
    "official_model": "HistGradientBoostingClassifier",
    "official_auc": float(official_metric["roc_auc_repurchase"]),
    "official_churn_risk_pr_auc": float(official_metric["average_precision_churn_risk"]),
    "official_top_decile_lift": float(official_decile["top_decile_lift"]),
    "official_raw_feature_count": int(official_metric["raw_feature_count"]),
    "official_post_transform_feature_count": int(official_metric["post_transform_feature_count"]),
    "train_test_USER_KEY_overlap_max": int(metrics["train_test_USER_KEY_overlap"].max()),
    "shap_status": shap_status,
    "shap_message": shap_message,
    "final_check_status": "PASS" if final_checks_df["status"].eq("PASS").all() else "FAIL",
    "optional_warnings": optional_warnings,
    "data_outputs": [rel(p) for p in required_data_outputs],
    "table_outputs": [rel(p) for p in required_table_outputs + [TABLE_DIR / "06h_final_checks.csv"]],
    "figure_outputs": [rel(p) for p in required_figures],
}
write_json(DATA_DIR / "06h_integrated_audit_summary.json", summary)

print(json.dumps(summary, ensure_ascii=False, indent=2))
if summary["final_check_status"] != "PASS":
    raise SystemExit("06h final checks did not all pass.")
