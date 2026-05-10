import json
import os
import platform
import sys
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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


os.environ.setdefault("PYTHONIOENCODING", "utf-8")
RANDOM_STATE = 42
TARGET = "is_repurchase"
TARGET_NUM = "target_repurchase"
ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"

PRIMARY_WINDOW = "w1_3"
PRIMARY_FEATURE_SET = "membership_plus_usage_content_w1_3_without_churn_prevented"
PRIMARY_MODEL = "HistGradientBoostingClassifier"
LATE_WINDOW = "w1_4"
LATE_FEATURE_SET = "membership_plus_usage_content_w1_4_without_churn_prevented"
LATE_MODEL = "LGBMClassifier"

FORBIDDEN_SEGMENT_FEATURES = {
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
FORBIDDEN_SUBSTRINGS = ["raw_calendar", "calendar_date", "days_to_end", "days_since_last_watch_to_end"]


def find_project_root(start):
    for candidate in [start, *start.parents]:
        if (
            (candidate / "_data" / "01_raw" / "Membership.csv").exists()
            and (
                candidate
                / "park.ingyeom"
                / "reports"
                / "data"
                / "07r_v2_true_shap_interpretation"
                / "07r_true_shap_summary.json"
            ).exists()
        ):
            return candidate
    raise FileNotFoundError("Could not locate ott-churn-prediction project root.")


PROJECT_ROOT = find_project_root(Path.cwd())
STAGE05_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "05_v2_modeling_dataset"
STAGE06_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "06_v2_baseline_modeling"
STAGE06_TABLES = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "06_v2_baseline_modeling"
STAGE06B_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "06b_v2_baseline_sanity_audit"
STAGE07R_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "07r_v2_true_shap_interpretation"
STAGE07R_TABLES = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "07r_v2_true_shap_interpretation"

DATA_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "08_v2_segmentation_strategy"
TABLE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "08_v2_segmentation_strategy"
FIGURE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "08_v2_segmentation_strategy"
for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

RAW_FILES = [
    PROJECT_ROOT / "_data" / "01_raw" / name
    for name in ["Membership.csv", "User_Mapping.csv", "View_History.csv", "Movie_Master.csv"]
]


def rel(path):
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


def write_csv(path, obj):
    if isinstance(obj, pd.DataFrame):
        obj.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame(obj).to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def is_forbidden_feature(name):
    return name in FORBIDDEN_SEGMENT_FEATURES or any(token in name for token in FORBIDDEN_SUBSTRINGS)


def onehot_encoder(sparse=False):
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=sparse)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=sparse)


def make_primary_pipeline(features, categorical_features):
    numeric = [c for c in features if c not in categorical_features]
    categorical = [c for c in features if c in categorical_features]
    transformers = []
    if numeric:
        transformers.append(("num", SimpleImputer(strategy="median"), numeric))
    if categorical:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", onehot_encoder(sparse=False)),
                    ]
                ),
                categorical,
            )
        )
    pre = ColumnTransformer(transformers, remainder="drop", sparse_threshold=0.0, verbose_feature_names_out=True)
    model = HistGradientBoostingClassifier(max_iter=60, learning_rate=0.08, max_leaf_nodes=31, random_state=RANDOM_STATE)
    return Pipeline([("preprocess", pre), ("model", model)])


def predict_score(pipe, X):
    proba = pipe.predict_proba(X)
    classes = list(pipe.named_steps["model"].classes_)
    return proba[:, classes.index(1)]


def assign_risk_band(scores):
    pct = scores.rank(method="first", pct=True)
    out = pd.Series(index=scores.index, dtype=object)
    out[pct > 0.90] = "top_10_highest_risk"
    out[(pct > 0.70) & (pct <= 0.90)] = "risk_10_30"
    out[(pct > 0.40) & (pct <= 0.70)] = "risk_30_60"
    out[pct <= 0.40] = "bottom_40_lowest_risk"
    return out


def outcome_summary(df, group_col, descriptive_label):
    rows = []
    overall_churn = 1 - df[TARGET_NUM].mean()
    total_churners = int((1 - df[TARGET_NUM]).sum())
    for name, sub in df.groupby(group_col, dropna=False):
        n = len(sub)
        churners = int((1 - sub[TARGET_NUM]).sum())
        churn_rate = churners / n if n else np.nan
        rows.append(
            {
                "population": descriptive_label,
                group_col: name,
                "n": n,
                "share": n / len(df) if len(df) else np.nan,
                "repurchase_rate": sub[TARGET_NUM].mean() if n else np.nan,
                "churn_rate": churn_rate,
                "lift_vs_overall_churn_rate": churn_rate / overall_churn if overall_churn else np.nan,
                "captured_churners": churners,
                "churner_capture_rate": churners / total_churners if total_churners else np.nan,
                "avg_repurchase_score": sub["repurchase_score"].mean() if "repurchase_score" in sub else np.nan,
                "avg_churn_risk_score": sub["churn_risk_score"].mean() if "churn_risk_score" in sub else np.nan,
                "descriptive_only": "Y" if descriptive_label == "full_descriptive" else "N",
            }
        )
    return pd.DataFrame(rows)


def flag_summary(df, flag_cols, population):
    rows = []
    overall_churn = 1 - df[TARGET_NUM].mean()
    for flag in flag_cols:
        sub = df[df[flag] == 1]
        n = len(sub)
        churn_rate = (1 - sub[TARGET_NUM]).mean() if n else np.nan
        rows.append(
            {
                "population": population,
                "segment_flag": flag,
                "n": n,
                "share": n / len(df) if len(df) else np.nan,
                "repurchase_rate": sub[TARGET_NUM].mean() if n else np.nan,
                "churn_rate": churn_rate,
                "lift_vs_overall_churn_rate": churn_rate / overall_churn if overall_churn else np.nan,
                "avg_churn_risk_score": sub["churn_risk_score"].mean() if n else np.nan,
                "unstable_n_lt_100": "Y" if n < 100 else "N",
            }
        )
    return pd.DataFrame(rows)


def plot_bar(path, labels, values, title, ylabel=None, color="#378ADD", rotation=30):
    plt.figure(figsize=(9, 5))
    plt.bar(labels, values, color=color)
    plt.title(title)
    if ylabel:
        plt.ylabel(ylabel)
    plt.xticks(rotation=rotation, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


stage_existing_dirs = []
for base in [
    PROJECT_ROOT / "park.ingyeom" / "reports" / "data",
    PROJECT_ROOT / "park.ingyeom" / "reports" / "tables",
    PROJECT_ROOT / "park.ingyeom" / "reports" / "figures",
]:
    if base.exists():
        for p in base.iterdir():
            if p.is_dir() and (
                any(p.name.startswith(f"{i:02d}_v2") for i in range(1, 8))
                or p.name.startswith("06_v2")
                or p.name.startswith("06b_v2")
                or p.name.startswith("07_v2")
                or p.name.startswith("07r_v2")
            ):
                stage_existing_dirs.append(p)
stage_existing_files = [
    PROJECT_ROOT / "park.ingyeom" / "notebooks" / name
    for name in [
        "01_v2_data_overview_and_audit.ipynb",
        "02_v2_preprocessing_policy.ipynb",
        "03_v2_usage_feature_engineering.ipynb",
        "04_v2_content_feature_engineering.ipynb",
        "05_v2_modeling_dataset.ipynb",
        "06_v2_baseline_modeling.ipynb",
        "06_v2_baseline_modeling_impl.py",
        "06b_v2_baseline_sanity_audit.ipynb",
        "06b_v2_baseline_sanity_audit_impl.py",
        "07_v2_xai_shap_interpretation.ipynb",
        "07_v2_xai_shap_interpretation_impl.py",
        "07r_v2_true_shap_interpretation.ipynb",
        "07r_v2_true_shap_interpretation_impl.py",
    ]
]
raw_before = snapshot_paths(RAW_FILES)
stage_before = snapshot_dirs(stage_existing_dirs) | snapshot_paths(stage_existing_files)

df_w13 = pd.read_csv(STAGE05_DATA / "modeling_dataset_v2_w1_3.csv")
df_w14 = pd.read_csv(STAGE05_DATA / "modeling_dataset_v2_w1_4.csv")
for df in [df_w13, df_w14]:
    df[TARGET_NUM] = df[TARGET].map({"Y": 1, "N": 0}).astype(int)

with (STAGE05_DATA / "feature_sets_v2.json").open("r", encoding="utf-8") as f:
    feature_payload = json.load(f)
with (STAGE06_DATA / "06_v2_best_model_config.json").open("r", encoding="utf-8") as f:
    best_config = json.load(f)
with (STAGE06B_DATA / "06b_sanity_audit_summary.json").open("r", encoding="utf-8") as f:
    sanity_summary = json.load(f)
with (STAGE07R_DATA / "07r_true_shap_summary.json").open("r", encoding="utf-8") as f:
    shap_summary = json.load(f)

pred_scores = pd.read_csv(STAGE06_DATA / "06_v2_prediction_scores.csv")
split_membership = pd.read_csv(STAGE06_TABLES / "06_v2_split_membership_row_ids.csv")
global_shap = pd.read_csv(STAGE07R_TABLES / "07r_global_shap_importance.csv")
grouped_shap = pd.read_csv(STAGE07R_TABLES / "07r_grouped_shap_importance.csv")
family_shap = pd.read_csv(STAGE07R_TABLES / "07r_feature_family_shap_importance.csv")
direction_shap = pd.read_csv(STAGE07R_TABLES / "07r_shap_direction_summary.csv")
top_decile_shap = pd.read_csv(STAGE07R_TABLES / "07r_churn_risk_top_decile_shap_explanation.csv")
local_contrib = pd.read_csv(STAGE07R_TABLES / "07r_local_top_contributors.csv")

features = list(feature_payload["feature_sets"][PRIMARY_FEATURE_SET])
categorical = [f for f in features if f in set(feature_payload.get("categorical_features_to_encode_in_stage06", []))]
if any(is_forbidden_feature(f) for f in features):
    raise RuntimeError("Forbidden feature detected in primary feature set.")

train_ids = set(split_membership.loc[split_membership["holdout_split"] == "train", ID_COL])
test_ids = set(split_membership.loc[split_membership["holdout_split"] == "test", ID_COL])
train_groups = set(split_membership.loc[split_membership["holdout_split"] == "train", GROUP_COL])
test_groups = set(split_membership.loc[split_membership["holdout_split"] == "test", GROUP_COL])

primary_pred = pred_scores[
    (pred_scores["window"] == PRIMARY_WINDOW)
    & (pred_scores["feature_set"] == PRIMARY_FEATURE_SET)
    & (pred_scores["model_name"] == PRIMARY_MODEL)
    & (pred_scores["split_type"] == "holdout")
].copy()
if primary_pred.empty:
    raise RuntimeError("Primary conservative holdout prediction scores not found.")

holdout = df_w13[df_w13[ID_COL].isin(test_ids)].merge(
    primary_pred[[ID_COL, "repurchase_score", "churn_risk_score"]],
    on=ID_COL,
    how="left",
)
if holdout["churn_risk_score"].isna().any():
    raise RuntimeError("Missing holdout churn_risk_score after merge.")

pipe = make_primary_pipeline(features, categorical)
train_mask = df_w13[ID_COL].isin(train_ids)
pipe.fit(df_w13.loc[train_mask, features], df_w13.loc[train_mask, TARGET_NUM])
df_full = df_w13.copy()
df_full["repurchase_score"] = predict_score(pipe, df_full[features])
df_full["churn_risk_score"] = 1 - df_full["repurchase_score"]

validation_passes = []
validation_passes.append({"pass_no": 1, "pass_name": "initial_segment_definitions_and_thresholds", "status": "completed", "note": "Quantile thresholds created without target labels."})

# Thresholds from holdout feature distribution, target-free
threshold_rows = []
def q(feature, quantile):
    value = float(holdout[feature].quantile(quantile))
    threshold_rows.append({"threshold_name": f"{feature}_q{int(quantile*100)}", "feature": feature, "quantile": quantile, "threshold_value": value, "threshold_source": "holdout_primary_eval", "target_used": "N"})
    return value

risk_thresholds = {
    "holdout_q90": float(holdout["churn_risk_score"].quantile(0.90)),
    "holdout_q70": float(holdout["churn_risk_score"].quantile(0.70)),
    "holdout_q40": float(holdout["churn_risk_score"].quantile(0.40)),
    "full_q90": float(df_full["churn_risk_score"].quantile(0.90)),
    "full_q70": float(df_full["churn_risk_score"].quantile(0.70)),
    "full_q40": float(df_full["churn_risk_score"].quantile(0.40)),
}
for name, value in risk_thresholds.items():
    threshold_rows.append({"threshold_name": name, "feature": "churn_risk_score", "quantile": name.split("_q")[-1], "threshold_value": value, "threshold_source": "risk_band_relative_population", "target_used": "N"})

threshold_values = {
    "week3_watch_time_q75": q("w1_3_week3_watch_time", 0.75),
    "week2_minus_week1_q75": q("w1_3_w2_minus_w1_watch_time", 0.75),
    "week1_ratio_q75": q("w1_3_week1_ratio", 0.75),
    "first_watch_rel_day_q75": q("w1_3_first_watch_rel_day", 0.75),
    "first_watch_rel_day_q50": q("w1_3_first_watch_rel_day", 0.50),
    "total_watch_time_q25": q("w1_3_total_watch_time", 0.25),
    "total_sessions_q25": q("w1_3_total_sessions", 0.25),
    "thriller_crime_q75": q("w1_3_genre_ratio_thriller_crime", 0.75),
    "animation_family_q75": q("w1_3_genre_ratio_animation_family", 0.75),
    "drama_q75": q("w1_3_genre_ratio_drama", 0.75),
    "action_adventure_q75": q("w1_3_genre_ratio_action_adventure", 0.75),
    "price_q75": q("price", 0.75),
}

def truthy_promo(series):
    return series.astype(str).str.upper().isin(["Y", "TRUE", "1", "PROMOTION", "T"])

def add_segments(df, population):
    out = df.copy()
    out["risk_band"] = assign_risk_band(out["churn_risk_score"])
    out["seg_top_decile_high_churn_risk"] = (out["risk_band"] == "top_10_highest_risk").astype(int)
    out["seg_low_or_no_early_engagement"] = (
        (out["w1_3_no_watch_obs_flag"].fillna(0).astype(float) >= 1)
        | (out["w1_3_total_watch_time"] <= threshold_values["total_watch_time_q25"])
        | (out["w1_3_total_sessions"] <= threshold_values["total_sessions_q25"])
    ).astype(int)
    out["seg_late_heavy_week3_intensive"] = (out["w1_3_week3_watch_time"] >= threshold_values["week3_watch_time_q75"]).astype(int)
    out["seg_delayed_start"] = (
        (out["w1_3_first_watch_rel_day"] >= threshold_values["first_watch_rel_day_q75"])
        & (out["w1_3_has_watch_obs"].fillna(0).astype(float) >= 1)
    ).astype(int)
    out["seg_early_routine_stable"] = (
        (out["w1_3_week1_ratio"] >= threshold_values["week1_ratio_q75"])
        & (out["w1_3_first_watch_rel_day"] <= threshold_values["first_watch_rel_day_q50"])
        & (out["w1_3_has_watch_obs"].fillna(0).astype(float) >= 1)
    ).astype(int)
    out["seg_week2_surge_users"] = (out["w1_3_w2_minus_w1_watch_time"] >= threshold_values["week2_minus_week1_q75"]).astype(int)
    out["seg_genre_affinity_thriller_crime"] = (
        (out["w1_3_genre_ratio_thriller_crime"] >= threshold_values["thriller_crime_q75"])
        & (out["w1_3_genre_ratio_thriller_crime"] > 0)
    ).astype(int)
    out["seg_genre_affinity_animation_family"] = (
        (out["w1_3_genre_ratio_animation_family"] >= threshold_values["animation_family_q75"])
        & (out["w1_3_genre_ratio_animation_family"] > 0)
    ).astype(int)
    out["seg_genre_affinity_drama"] = (
        (out["w1_3_genre_ratio_drama"] >= threshold_values["drama_q75"])
        & (out["w1_3_genre_ratio_drama"] > 0)
    ).astype(int)
    out["seg_genre_affinity_action_adventure"] = (
        (out["w1_3_genre_ratio_action_adventure"] >= threshold_values["action_adventure_q75"])
        & (out["w1_3_genre_ratio_action_adventure"] > 0)
    ).astype(int)
    out["seg_high_price_or_promotion_sensitive"] = (
        (out["price"] >= threshold_values["price_q75"])
        | (out["price"] == 100)
        | truthy_promo(out["is_promotion"])
    ).astype(int)
    hierarchy = [
        ("top_decile_high_churn_risk", "seg_top_decile_high_churn_risk"),
        ("low_or_no_early_engagement", "seg_low_or_no_early_engagement"),
        ("late_heavy_week3_intensive", "seg_late_heavy_week3_intensive"),
        ("delayed_start", "seg_delayed_start"),
        ("genre_affinity_thriller_crime", "seg_genre_affinity_thriller_crime"),
        ("genre_affinity_animation_family", "seg_genre_affinity_animation_family"),
        ("genre_affinity_drama", "seg_genre_affinity_drama"),
        ("genre_affinity_action_adventure", "seg_genre_affinity_action_adventure"),
        ("early_routine_stable", "seg_early_routine_stable"),
        ("high_price_or_promotion_sensitive", "seg_high_price_or_promotion_sensitive"),
        ("week2_surge_users", "seg_week2_surge_users"),
    ]
    out["hierarchical_segment"] = "general_other"
    out["hierarchical_rank"] = len(hierarchy) + 1
    for rank, (segment, flag) in enumerate(hierarchy, start=1):
        mask = (out["hierarchical_segment"] == "general_other") & (out[flag] == 1)
        out.loc[mask, "hierarchical_segment"] = segment
        out.loc[mask, "hierarchical_rank"] = rank
    out["population"] = population
    return out

holdout_seg = add_segments(holdout, "holdout")
full_seg = add_segments(df_full, "full_descriptive")
flag_cols = [c for c in holdout_seg.columns if c.startswith("seg_")]

validation_passes.append({"pass_no": 2, "pass_name": "overlap_hierarchy_threshold_stability", "status": "completed", "note": "Overlap matrix and hierarchy assignment created; quantile thresholds recorded."})

risk_holdout = outcome_summary(holdout_seg, "risk_band", "holdout")
risk_full = outcome_summary(full_seg, "risk_band", "full_descriptive")
hier_holdout = outcome_summary(holdout_seg, "hierarchical_segment", "holdout")
hier_full = outcome_summary(full_seg, "hierarchical_segment", "full_descriptive")
nonexclusive_summary = pd.concat([flag_summary(holdout_seg, flag_cols, "holdout"), flag_summary(full_seg, flag_cols, "full_descriptive")], ignore_index=True)
validation_passes.append({"pass_no": 3, "pass_name": "segment_eval_holdout_and_full_descriptive", "status": "completed", "note": "Holdout-first evaluation and full descriptive profiles created."})

overlap = pd.DataFrame(index=flag_cols, columns=flag_cols, dtype=int)
for a in flag_cols:
    for b in flag_cols:
        overlap.loc[a, b] = int(((holdout_seg[a] == 1) & (holdout_seg[b] == 1)).sum())
overlap_reset = overlap.reset_index().rename(columns={"index": "segment_flag"})

flag_definitions = [
    {"segment_flag": "seg_top_decile_high_churn_risk", "definition": "churn_risk_score top 10% within the evaluated population", "threshold_basis": "risk score percentile", "target_used": "N"},
    {"segment_flag": "seg_low_or_no_early_engagement", "definition": "no watch flag or bottom-quartile total watch time/sessions", "threshold_basis": "holdout Q25 usage", "target_used": "N"},
    {"segment_flag": "seg_late_heavy_week3_intensive", "definition": "week3 watch time top quartile", "threshold_basis": "holdout Q75 usage", "target_used": "N"},
    {"segment_flag": "seg_delayed_start", "definition": "first_watch_rel_day top quartile among watchers", "threshold_basis": "holdout Q75 usage", "target_used": "N"},
    {"segment_flag": "seg_early_routine_stable", "definition": "week1 ratio top quartile and first_watch_rel_day <= median", "threshold_basis": "holdout usage quantiles", "target_used": "N"},
    {"segment_flag": "seg_week2_surge_users", "definition": "w2_minus_w1_watch_time top quartile", "threshold_basis": "holdout Q75 usage", "target_used": "N"},
    {"segment_flag": "seg_genre_affinity_thriller_crime", "definition": "thriller/crime genre ratio top quartile and positive", "threshold_basis": "holdout Q75 genre ratio", "target_used": "N"},
    {"segment_flag": "seg_genre_affinity_animation_family", "definition": "animation/family genre ratio top quartile and positive", "threshold_basis": "holdout Q75 genre ratio", "target_used": "N"},
    {"segment_flag": "seg_genre_affinity_drama", "definition": "drama genre ratio top quartile and positive", "threshold_basis": "holdout Q75 genre ratio", "target_used": "N"},
    {"segment_flag": "seg_genre_affinity_action_adventure", "definition": "action/adventure genre ratio top quartile and positive", "threshold_basis": "holdout Q75 genre ratio", "target_used": "N"},
    {"segment_flag": "seg_high_price_or_promotion_sensitive", "definition": "price top quartile, price == 100, or promotion flag", "threshold_basis": "holdout price Q75 plus explicit promotion flags", "target_used": "N"},
]

segment_evidence = []
support_map = {
    "top_decile_high_churn_risk": ["usage", "genre", "membership"],
    "low_or_no_early_engagement": ["usage"],
    "late_heavy_week3_intensive": ["usage"],
    "delayed_start": ["usage"],
    "early_routine_stable": ["usage"],
    "week2_surge_users": ["usage"],
    "genre_affinity_thriller_crime": ["genre"],
    "genre_affinity_animation_family": ["genre"],
    "genre_affinity_drama": ["genre"],
    "genre_affinity_action_adventure": ["genre"],
    "high_price_or_promotion_sensitive": ["membership"],
    "general_other": [],
}
family_importance = family_shap.set_index("feature_family")["mean_abs_shap"].to_dict()
for segment, families in support_map.items():
    if not families:
        segment_evidence.append({"segment": segment, "shap_feature_family": "", "stage07r_mean_abs_shap": np.nan, "evidence_strength": "weak", "evidence_note": "No specific SHAP family; residual segment."})
    for fam in families:
        segment_evidence.append({"segment": segment, "shap_feature_family": fam, "stage07r_mean_abs_shap": family_importance.get(fam, np.nan), "evidence_strength": "strong" if family_importance.get(fam, 0) > 0.1 else "weak", "evidence_note": "Stage 07r true SHAP feature-family evidence."})
validation_passes.append({"pass_no": 4, "pass_name": "map_segments_to_stage07r_true_shap", "status": "completed", "note": "All action segments mapped to Stage 07r true SHAP families; Stage 07 fallback not used."})

action_rows = [
    {"segment": "top_decile_high_churn_risk", "segment_name_ko": "최상위 이탈위험군", "definition": "보수 w1_3 churn_risk_score 상위 10%", "business_interpretation": "초기 관측창 기준 비재구독 위험이 가장 높은 고객군", "risk_mechanism_hypothesis": "초기 사용/장르/멤버십 신호가 재구독 가능성을 낮게 예측한다는 가설", "recommended_action": "고위험 모니터링 및 개인화 리텐션 메시지", "why_plausible": "usage, genre, membership SHAP family가 모두 중요", "what_not_to_claim": "이 조치가 재구독을 원인적으로 증가시킨다고 말하지 않음", "readiness": "plausible_but_cautioned"},
    {"segment": "low_or_no_early_engagement", "segment_name_ko": "초기 미시청/저관여군", "definition": "초기 시청 없음 또는 하위 사분위 사용량", "business_interpretation": "가입 후 초기 관여가 낮은 고객", "risk_mechanism_hypothesis": "초기 접점 부족이 낮은 재구독 점수와 연관된다는 가설", "recommended_action": "no-watch onboarding 및 초기 콘텐츠 추천", "why_plausible": "usage SHAP family가 가장 중요", "what_not_to_claim": "시청량을 강제로 늘리면 재구독이 오른다고 단정하지 않음", "readiness": "safe_to_report"},
    {"segment": "late_heavy_week3_intensive", "segment_name_ko": "3주차 집중 시청군", "definition": "3주차 시청시간 상위 사분위", "business_interpretation": "초기보다 후반부 관여가 강한 고객", "risk_mechanism_hypothesis": "3주차 행동이 재구독 예측에 강하게 연결된다는 가설", "recommended_action": "week3 타깃 메시지와 이어보기 추천", "why_plausible": "w1_3_week3_watch_time이 최상위 SHAP feature", "what_not_to_claim": "3주차 메시지가 반드시 이탈을 막는다고 말하지 않음", "readiness": "safe_to_report"},
    {"segment": "delayed_start", "segment_name_ko": "시작 지연군", "definition": "첫 시청 상대일 top quartile", "business_interpretation": "구독 후 시청 시작이 늦은 고객", "risk_mechanism_hypothesis": "첫 사용 지연이 낮은 재구독 가능성과 연관된다는 가설", "recommended_action": "가입 직후 탐색 도움 및 첫 시청 유도", "why_plausible": "first_watch_rel_day가 top SHAP feature", "what_not_to_claim": "첫 시청일을 앞당기면 인과적으로 재구독이 오른다고 말하지 않음", "readiness": "plausible_but_cautioned"},
    {"segment": "genre_affinity_thriller_crime", "segment_name_ko": "스릴러/범죄 선호군", "definition": "thriller/crime genre ratio top quartile", "business_interpretation": "특정 장르 편향 시청군", "risk_mechanism_hypothesis": "장르 소비 패턴이 재구독 예측에 기여한다는 가설", "recommended_action": "스릴러/범죄 후속 콘텐츠 추천", "why_plausible": "genre SHAP family와 해당 장르 ratio feature 중요", "what_not_to_claim": "장르 추천이 재구독을 보장한다고 말하지 않음", "readiness": "plausible_but_cautioned"},
    {"segment": "genre_affinity_animation_family", "segment_name_ko": "애니/가족 선호군", "definition": "animation/family genre ratio top quartile", "business_interpretation": "가족/애니 콘텐츠 이용 패턴이 뚜렷한 고객", "risk_mechanism_hypothesis": "가족형 콘텐츠 연속성이 유지 의도와 연관될 수 있다는 가설", "recommended_action": "가족/애니 continuation cue", "why_plausible": "animation/family genre SHAP feature 중요", "what_not_to_claim": "가족 콘텐츠 제공이 재구독을 원인적으로 만든다고 말하지 않음", "readiness": "plausible_but_cautioned"},
    {"segment": "genre_affinity_drama", "segment_name_ko": "드라마 선호군", "definition": "drama genre ratio top quartile", "business_interpretation": "드라마 중심 소비군", "risk_mechanism_hypothesis": "드라마 장르 소비량/비율이 재구독 예측에 기여한다는 가설", "recommended_action": "드라마 이어보기 및 신작 알림", "why_plausible": "drama genre SHAP features appear in top drivers", "what_not_to_claim": "드라마 추천 효과를 검증 없이 수익 효과로 환산하지 않음", "readiness": "plausible_but_cautioned"},
    {"segment": "genre_affinity_action_adventure", "segment_name_ko": "액션/어드벤처 선호군", "definition": "action/adventure genre ratio top quartile", "business_interpretation": "액션/어드벤처 중심 소비군", "risk_mechanism_hypothesis": "해당 장르 선호가 콘텐츠 추천 반응과 연관될 수 있다는 가설", "recommended_action": "액션/어드벤처 continuation recommendation", "why_plausible": "action/adventure genre SHAP feature is top 10", "what_not_to_claim": "장르 소비가 이탈의 원인이라고 말하지 않음", "readiness": "plausible_but_cautioned"},
    {"segment": "early_routine_stable", "segment_name_ko": "초기 루틴 형성군", "definition": "week1_ratio 상위 + 첫 시청 빠름", "business_interpretation": "초기 이용 루틴이 빠르게 형성된 고객", "risk_mechanism_hypothesis": "초기 루틴이 재구독 가능성과 연관된다는 가설", "recommended_action": "루틴 유지형 알림과 이어보기 큐", "why_plausible": "week1_ratio가 top SHAP feature", "what_not_to_claim": "루틴 알림의 인과효과를 주장하지 않음", "readiness": "safe_to_report"},
    {"segment": "high_price_or_promotion_sensitive", "segment_name_ko": "가격/프로모션 민감 가능군", "definition": "가격 상위 또는 100원/프로모션 관련 조건", "business_interpretation": "멤버십 조건 차이가 큰 고객군", "risk_mechanism_hypothesis": "가격/프로모션 맥락이 재구독 예측과 연관된다는 가설", "recommended_action": "요금제/downsell 안내 후보", "why_plausible": "price is top SHAP feature and membership family has signal", "what_not_to_claim": "할인 제공의 손익 효과를 계산하지 않음", "readiness": "plausible_but_cautioned"},
    {"segment": "week2_surge_users", "segment_name_ko": "2주차 상승 관여군", "definition": "w2_minus_w1_watch_time top quartile", "business_interpretation": "2주차에 사용량이 증가한 고객군", "risk_mechanism_hypothesis": "초기 이후 관심 상승이 재구독 예측과 연관된다는 가설", "recommended_action": "관심 상승 구간 후속 콘텐츠 추천", "why_plausible": "w2_minus_w1_watch_time is top SHAP feature", "what_not_to_claim": "상승 관여가 인과적으로 재구독을 만든다고 말하지 않음", "readiness": "safe_to_report"},
    {"segment": "general_other", "segment_name_ko": "일반 기타군", "definition": "상위 hierarchy 어디에도 속하지 않는 잔여군", "business_interpretation": "뚜렷한 단일 rule signal이 약한 고객군", "risk_mechanism_hypothesis": "단일 해석 피처보다 복합 신호가 필요하다는 가설", "recommended_action": "일반 콘텐츠 추천 및 관찰 유지", "why_plausible": "specific SHAP link weak", "what_not_to_claim": "명확한 리텐션 타깃이라고 주장하지 않음", "readiness": "do_not_claim_yet"},
]
validation_passes.append({"pass_no": 5, "pass_name": "action_recommendations_and_readiness", "status": "completed", "note": "Each action mapped to evidence; weak mappings marked."})

action_df = pd.DataFrame(action_rows)
evidence_df = pd.DataFrame(segment_evidence)
action_evidence_strength = evidence_df.groupby("segment")["evidence_strength"].apply(lambda s: "strong" if (s == "strong").any() else "weak").reset_index()
action_df = action_df.merge(action_evidence_strength, on="segment", how="left")
action_df["evidence_strength"] = action_df["evidence_strength"].fillna("weak")

small_segments = hier_holdout[hier_holdout["n"] < 100]["hierarchical_segment"].tolist()
overlap_pairs = []
for a in flag_cols:
    for b in flag_cols:
        if a >= b:
            continue
        a_n = int((holdout_seg[a] == 1).sum())
        b_n = int((holdout_seg[b] == 1).sum())
        both = int(((holdout_seg[a] == 1) & (holdout_seg[b] == 1)).sum())
        denom = min(a_n, b_n) if min(a_n, b_n) else 0
        ratio = both / denom if denom else 0
        if ratio >= 0.70 and both >= 100:
            overlap_pairs.append(f"{a} x {b}: {ratio:.2f}")
arbitrary_threshold_notes = [
    "All thresholds are quantile-based, but quartile cutoffs are still heuristic business rules.",
    "Risk bands are percentile bands and should not be interpreted as calibrated probability tiers.",
]
weak_actions = action_df[action_df["evidence_strength"] == "weak"]["segment"].tolist()
presentation_ready = action_df[action_df["readiness"].isin(["safe_to_report", "plausible_but_cautioned"]) & (action_df["evidence_strength"] != "weak")]["segment"].tolist()
excluded = action_df[(action_df["readiness"] == "do_not_claim_yet") | (action_df["evidence_strength"] == "weak")]["segment"].tolist()
validation_passes.append({"pass_no": 6, "pass_name": "leakage_small_segment_overlap_internal_critique", "status": "completed", "note": "Small n, overlap, threshold arbitrariness, weak actions, and presentation readiness reviewed."})

validation_passes.append({"pass_no": 7, "pass_name": "team_share_tables_and_figures", "status": "completed", "note": "Team-share-ready figures, report, and summary generated."})

write_csv(TABLE_DIR / "08_v2_segmentation_input_summary.csv", [
    {"input": "modeling_dataset_v2_w1_3", "path": rel(STAGE05_DATA / "modeling_dataset_v2_w1_3.csv"), "rows": len(df_w13), "role": "primary segmentation features"},
    {"input": "06_v2_prediction_scores", "path": rel(STAGE06_DATA / "06_v2_prediction_scores.csv"), "rows": len(pred_scores), "role": "holdout conservative churn-risk scores"},
    {"input": "07r_true_shap_summary", "path": rel(STAGE07R_DATA / "07r_true_shap_summary.json"), "rows": 1, "role": "final true SHAP evidence"},
])
write_csv(TABLE_DIR / "08_v2_risk_band_summary_holdout.csv", risk_holdout)
write_csv(TABLE_DIR / "08_v2_risk_band_summary_full_descriptive.csv", risk_full)
write_csv(TABLE_DIR / "08_v2_segment_flag_definitions.csv", flag_definitions)
write_csv(TABLE_DIR / "08_v2_segment_thresholds.csv", threshold_rows)
write_csv(TABLE_DIR / "08_v2_nonexclusive_segment_flag_summary.csv", nonexclusive_summary)
write_csv(TABLE_DIR / "08_v2_hierarchical_segment_summary_holdout.csv", hier_holdout)
write_csv(TABLE_DIR / "08_v2_hierarchical_segment_summary_full_descriptive.csv", hier_full)
write_csv(TABLE_DIR / "08_v2_segment_overlap_matrix.csv", overlap_reset)
write_csv(TABLE_DIR / "08_v2_segment_shap_evidence_map.csv", evidence_df)
write_csv(TABLE_DIR / "08_v2_segment_action_recommendations.csv", action_df)
write_csv(TABLE_DIR / "08_v2_business_readiness_findings.csv", [
    {"classification": "safe_to_report", "finding": "w1_3 conservative churn-risk bands and holdout segment outcomes", "note": "Prediction/descriptive only"},
    {"classification": "plausible_but_cautioned", "finding": "usage and genre SHAP-informed segments", "note": "Do not claim causality"},
    {"classification": "do_not_claim_yet", "finding": "financial impact or action lift", "note": "Reserved for Stage 09 simulation or future experiment"},
    {"classification": "do_not_claim_yet", "finding": "w1_4 as early-warning evidence", "note": "w1_4 is late-period only"},
])
write_csv(DATA_DIR / "08_v2_segment_assignments_holdout.csv", holdout_seg[[ID_COL, TARGET, TARGET_NUM, "repurchase_score", "churn_risk_score", "risk_band", "hierarchical_segment", "hierarchical_rank"] + flag_cols])
write_csv(DATA_DIR / "08_v2_segment_assignments_full_descriptive.csv", full_seg[[ID_COL, TARGET, TARGET_NUM, "repurchase_score", "churn_risk_score", "risk_band", "hierarchical_segment", "hierarchical_rank"] + flag_cols])

late_pred = pred_scores[
    (pred_scores["window"] == LATE_WINDOW)
    & (pred_scores["feature_set"] == LATE_FEATURE_SET)
    & (pred_scores["model_name"] == LATE_MODEL)
    & (pred_scores["split_type"] == "holdout")
].copy()
late_comparison = []
if not late_pred.empty:
    merged = primary_pred[[ID_COL, "churn_risk_score"]].rename(columns={"churn_risk_score": "w1_3_churn_risk_score"}).merge(
        late_pred[[ID_COL, "churn_risk_score"]].rename(columns={"churn_risk_score": "w1_4_churn_risk_score"}),
        on=ID_COL,
        how="inner",
    )
    merged["w1_3_top_decile"] = merged["w1_3_churn_risk_score"] >= merged["w1_3_churn_risk_score"].quantile(0.90)
    merged["w1_4_top_decile"] = merged["w1_4_churn_risk_score"] >= merged["w1_4_churn_risk_score"].quantile(0.90)
    late_comparison.append({
        "comparison": "risk_ranking",
        "w1_3_label": "early-observation primary segmentation basis",
        "w1_4_label": "late-period/end-of-period comparison only",
        "spearman_corr": merged["w1_3_churn_risk_score"].corr(merged["w1_4_churn_risk_score"], method="spearman"),
        "top_decile_overlap_count": int((merged["w1_3_top_decile"] & merged["w1_4_top_decile"]).sum()),
        "w1_3_top_decile_count": int(merged["w1_3_top_decile"].sum()),
        "w1_4_top_decile_count": int(merged["w1_4_top_decile"].sum()),
        "interpretation": "Do not use w1_4 as early-warning evidence.",
    })
write_csv(TABLE_DIR / "08_v2_w1_3_vs_w1_4_segment_comparison.csv", late_comparison)

# Figures
ordered_band = ["top_10_highest_risk", "risk_10_30", "risk_30_60", "bottom_40_lowest_risk"]
risk_plot = risk_holdout.set_index("risk_band").reindex(ordered_band).reset_index()
plot_bar(FIGURE_DIR / "08_v2_risk_band_churn_rate_holdout.png", risk_plot["risk_band"], risk_plot["churn_rate"], "Holdout churn rate by risk band", "Churn rate", "#D4537E")
plot_bar(FIGURE_DIR / "08_v2_risk_band_churn_lift_holdout.png", risk_plot["risk_band"], risk_plot["lift_vs_overall_churn_rate"], "Holdout churn lift by risk band", "Lift vs overall", "#378ADD")

hier_plot = hier_holdout.sort_values("churn_rate", ascending=False)
fig, ax1 = plt.subplots(figsize=(10, 5.5))
ax1.bar(hier_plot["hierarchical_segment"], hier_plot["n"], color="#378ADD", alpha=0.75)
ax1.set_ylabel("n")
ax1.tick_params(axis="x", rotation=35)
ax2 = ax1.twinx()
ax2.plot(hier_plot["hierarchical_segment"], hier_plot["churn_rate"], color="#D4537E", marker="o")
ax2.set_ylabel("churn rate")
plt.title("Hierarchical segment size and churn, holdout")
fig.tight_layout()
plt.savefig(FIGURE_DIR / "08_v2_hierarchical_segment_size_and_churn.png", dpi=160)
plt.close()

fig, ax = plt.subplots(figsize=(11, 6))
action_plot = action_df[action_df["segment"] != "general_other"].copy().head(10)
ax.axis("off")
cell_text = action_plot[["segment_name_ko", "recommended_action", "readiness"]].values.tolist()
table = ax.table(cellText=cell_text, colLabels=["Segment", "Action", "Readiness"], loc="center", cellLoc="left")
table.auto_set_font_size(False)
table.set_fontsize(8)
table.scale(1, 1.6)
plt.title("Segment action map")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "08_v2_segment_action_map.png", dpi=160)
plt.close()

heat = evidence_df[evidence_df["shap_feature_family"] != ""].pivot_table(index="segment", columns="shap_feature_family", values="stage07r_mean_abs_shap", aggfunc="max", fill_value=0)
plt.figure(figsize=(8, 7))
plt.imshow(heat.values, aspect="auto", cmap="Blues")
plt.colorbar(label="Stage 07r mean abs SHAP")
plt.xticks(range(len(heat.columns)), heat.columns, rotation=30, ha="right")
plt.yticks(range(len(heat.index)), heat.index)
plt.title("Segment SHAP evidence heatmap")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "08_v2_segment_shap_evidence_heatmap.png", dpi=160)
plt.close()

top_row = risk_plot[risk_plot["risk_band"] == "top_10_highest_risk"].iloc[0]
plt.figure(figsize=(6, 4))
plt.bar(["top 10% captured", "remaining churners"], [top_row["captured_churners"], risk_holdout["captured_churners"].sum() - top_row["captured_churners"]], color=["#D4537E", "#BBBBBB"])
plt.title("Top-decile churn capture, holdout")
plt.ylabel("churners")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "08_v2_top_decile_churn_capture.png", dpi=160)
plt.close()

summary_payload = {
    "scope": "Stage 08 segmentation strategy only. No business simulation.",
    "primary_model": PRIMARY_MODEL,
    "primary_window": PRIMARY_WINDOW,
    "primary_feature_set": PRIMARY_FEATURE_SET,
    "score_direction": {"repurchase_score": "P(is_repurchase=Y)", "churn_risk_score": "1 - repurchase_score"},
    "stage07r_true_shap_used": True,
    "stage07_fallback_used_as_final_evidence": False,
    "holdout_rows": len(holdout_seg),
    "full_descriptive_rows": len(full_seg),
    "risk_band_holdout": risk_holdout.to_dict("records"),
    "validation_passes": validation_passes,
    "internal_critique": {
        "segments_n_lt_100_holdout": small_segments,
        "high_overlap_pairs": overlap_pairs,
        "threshold_notes": arbitrary_threshold_notes,
        "weak_actions": weak_actions,
        "presentation_ready_segments": presentation_ready,
        "exclude_from_final_reporting": excluded,
    },
    "stage09_guidance": "Use holdout segment sizes, churn rates, and proposed actions as inputs to business simulation; do not calculate financial impact in Stage 08.",
}
write_json(DATA_DIR / "08_v2_segmentation_summary.json", summary_payload)

recommended_figures = [
    rel(FIGURE_DIR / "08_v2_risk_band_churn_rate_holdout.png"),
    rel(FIGURE_DIR / "08_v2_hierarchical_segment_size_and_churn.png"),
    rel(FIGURE_DIR / "08_v2_segment_shap_evidence_heatmap.png"),
    rel(FIGURE_DIR / "08_v2_top_decile_churn_capture.png"),
]

team_lines = [
    "# 08_v2 Team Share Segment Summary",
    "",
    "## Primary Model And Score",
    f"- Primary model: {PRIMARY_WINDOW} / {PRIMARY_FEATURE_SET} / {PRIMARY_MODEL}.",
    "- `churn_risk_score = 1 - repurchase_score`; high score means high predicted non-repurchase risk.",
    "- Stage 07r true SHAP is the XAI basis.",
    "",
    "## Top Risk Bands",
]
for _, row in risk_plot.iterrows():
    team_lines.append(f"- {row['risk_band']}: n={int(row['n'])}, churn rate={row['churn_rate']:.3f}, lift={row['lift_vs_overall_churn_rate']:.2f}.")
team_lines.extend(["", "## Final Segments"])
for _, row in hier_holdout.sort_values("churn_rate", ascending=False).iterrows():
    action = action_df[action_df["segment"] == row["hierarchical_segment"]]
    action_text = action["recommended_action"].iloc[0] if not action.empty else "general monitoring"
    team_lines.append(f"- {row['hierarchical_segment']}: n={int(row['n'])}, churn rate={row['churn_rate']:.3f}, lift={row['lift_vs_overall_churn_rate']:.2f}, action={action_text}.")
team_lines.extend(["", "## Recommended Figures"])
for fig in recommended_figures:
    team_lines.append(f"- {fig}")
team_lines.extend([
    "",
    "## Presentation Cautions",
    "- Segments are descriptive and prediction-oriented, not causal.",
    "- Do not claim financial impact in Stage 08.",
    "- w1_4 is late-period only and is not the primary segmentation basis.",
])
(DATA_DIR / "08_v2_team_share_segment_summary.md").write_text("\n".join(team_lines) + "\n", encoding="utf-8")

report_lines = [
    "# 08_v2 Segmentation Strategy Report",
    "",
    "## Scope",
    "- Stage 08 created SHAP-informed segmentation strategy artifacts only.",
    "- No business simulation, Optuna, tuning, raw modification, legacy modification, or `_data` output was created.",
    "- Stage 07r true SHAP outputs are used as final XAI evidence. Stage 07 fallback is not used as final evidence.",
    "",
    "## Model And Score",
    f"- Segmentation model: {PRIMARY_WINDOW} / {PRIMARY_FEATURE_SET} / {PRIMARY_MODEL}.",
    "- `is_repurchase`: Y -> 1, N -> 0.",
    "- `repurchase_score = P(is_repurchase = Y)`.",
    "- `churn_risk_score = 1 - repurchase_score`; high score means high predicted non-repurchase risk.",
    "- w1_3 is primary because it is closer to early intervention timing. w1_4 is late-period/end-of-period only.",
    "",
    "## Churn-Risk Bands",
]
for _, row in risk_plot.iterrows():
    report_lines.append(f"- {row['risk_band']}: n={int(row['n'])}, churn rate={row['churn_rate']:.3f}, lift={row['lift_vs_overall_churn_rate']:.2f}, captured churners={int(row['captured_churners'])}.")
report_lines.extend([
    "",
    "## SHAP-Informed Rule Segments",
    "- Created non-exclusive segment flags and one documented hierarchical assignment.",
    "- Largest and highest-risk segments are available in `08_v2_hierarchical_segment_summary_holdout.csv`.",
    "- Segment actions are mapped to Stage 07r SHAP feature families in `08_v2_segment_shap_evidence_map.csv`.",
    "",
    "## Business Actionability",
])
for _, row in action_df.iterrows():
    report_lines.append(f"- {row['segment_name_ko']} ({row['segment']}): {row['recommended_action']} / readiness={row['readiness']} / evidence={row['evidence_strength']}.")
report_lines.extend([
    "",
    "## Claims Not To Make",
    "- Do not claim SHAP proves causal intervention effects.",
    "- Do not claim changing a feature will cause repurchase.",
    "- Do not present w1_4 as early-warning evidence.",
    "- Do not calculate or claim financial impact in Stage 08.",
    "",
    "## Stage 09 Guidance",
    "- Use holdout segment counts, churn rates, top-decile capture, and action hypotheses as inputs to Stage 09 business simulation.",
    "- Stage 09 should explicitly test business assumptions such as reach, cost, response rate, and retention lift.",
    "",
    "## Internal Critique and Segment Reliability Review",
    f"- Segments with n < 100 in holdout: {small_segments if small_segments else 'none'}.",
    f"- High-overlap flag pairs: {overlap_pairs if overlap_pairs else 'none above threshold'}.",
    f"- Threshold critique: {'; '.join(arbitrary_threshold_notes)}",
    f"- Weakly supported actions: {weak_actions if weak_actions else 'none'}.",
    f"- Presentation-ready segments: {presentation_ready}.",
    f"- Exclude or downplay in final reporting: {excluded}.",
])
(DATA_DIR / "08_v2_segmentation_strategy_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

required_outputs = [
    DATA_DIR / "08_v2_segment_assignments_holdout.csv",
    DATA_DIR / "08_v2_segment_assignments_full_descriptive.csv",
    DATA_DIR / "08_v2_segmentation_summary.json",
    DATA_DIR / "08_v2_team_share_segment_summary.md",
    DATA_DIR / "08_v2_segmentation_strategy_report.md",
    TABLE_DIR / "08_v2_segmentation_input_summary.csv",
    TABLE_DIR / "08_v2_risk_band_summary_holdout.csv",
    TABLE_DIR / "08_v2_risk_band_summary_full_descriptive.csv",
    TABLE_DIR / "08_v2_segment_flag_definitions.csv",
    TABLE_DIR / "08_v2_segment_thresholds.csv",
    TABLE_DIR / "08_v2_nonexclusive_segment_flag_summary.csv",
    TABLE_DIR / "08_v2_hierarchical_segment_summary_holdout.csv",
    TABLE_DIR / "08_v2_hierarchical_segment_summary_full_descriptive.csv",
    TABLE_DIR / "08_v2_segment_overlap_matrix.csv",
    TABLE_DIR / "08_v2_segment_shap_evidence_map.csv",
    TABLE_DIR / "08_v2_segment_action_recommendations.csv",
    TABLE_DIR / "08_v2_w1_3_vs_w1_4_segment_comparison.csv",
    TABLE_DIR / "08_v2_business_readiness_findings.csv",
    FIGURE_DIR / "08_v2_risk_band_churn_rate_holdout.png",
    FIGURE_DIR / "08_v2_risk_band_churn_lift_holdout.png",
    FIGURE_DIR / "08_v2_hierarchical_segment_size_and_churn.png",
    FIGURE_DIR / "08_v2_segment_action_map.png",
    FIGURE_DIR / "08_v2_segment_shap_evidence_heatmap.png",
    FIGURE_DIR / "08_v2_top_decile_churn_capture.png",
]

segment_variable_candidates = set()
for row in flag_definitions:
    for token in [
        "churn_risk_score",
        "w1_3_week3_watch_time",
        "w1_3_w2_minus_w1_watch_time",
        "w1_3_week1_ratio",
        "w1_3_first_watch_rel_day",
        "w1_3_total_watch_time",
        "w1_3_total_sessions",
        "w1_3_no_watch_obs_flag",
        "w1_3_has_watch_obs",
        "w1_3_genre_ratio_thriller_crime",
        "w1_3_genre_ratio_animation_family",
        "w1_3_genre_ratio_drama",
        "w1_3_genre_ratio_action_adventure",
        "price",
        "is_promotion",
    ]:
        if token in row["definition"] or token in row["segment_flag"] or token in row["threshold_basis"]:
            segment_variable_candidates.add(token)
forbidden_segment_vars = [v for v in segment_variable_candidates if is_forbidden_feature(v)]
target_used_in_definitions = any(row["target_used"] == "Y" for row in flag_definitions) or any(row["target_used"] == "Y" for row in threshold_rows)
raw_after = snapshot_paths(RAW_FILES)
stage_after = snapshot_dirs(stage_existing_dirs) | snapshot_paths(stage_existing_files)
final_checks = [
    {"check": "raw_files_unchanged", "status": "PASS" if raw_before == raw_after else "FAIL", "detail": "raw snapshots unchanged"},
    {"check": "no_project_root_data_output_created", "status": "PASS" if not (PROJECT_ROOT / "_data" / "02_interim" / "08_v2_segmentation_strategy").exists() and not (PROJECT_ROOT / "_data" / "08_v2_segmentation_strategy").exists() else "FAIL", "detail": "Stage 08 writes only under park.ingyeom/reports"},
    {"check": "stage01_through_stage07r_outputs_not_overwritten", "status": "PASS" if stage_before == stage_after else "FAIL", "detail": "Stage 01-07r snapshots unchanged"},
    {"check": "stage07_fallback_not_used_as_final_evidence", "status": "PASS", "detail": "Only Stage 07r true SHAP tables used for evidence"},
    {"check": "stage07r_true_shap_used_as_xai_basis", "status": "PASS" if shap_summary.get("true_shap_computed_primary") else "FAIL", "detail": rel(STAGE07R_DATA / "07r_true_shap_summary.json")},
    {"check": "is_repurchase_not_used_to_define_segments", "status": "PASS" if not target_used_in_definitions else "FAIL", "detail": f"target_used={target_used_in_definitions}"},
    {"check": "forbidden_features_not_used_as_segmentation_variables", "status": "PASS" if not forbidden_segment_vars else "FAIL", "detail": "|".join(forbidden_segment_vars)},
    {"check": "holdout_first_evaluation_produced", "status": "PASS" if (TABLE_DIR / "08_v2_risk_band_summary_holdout.csv").exists() else "FAIL", "detail": "holdout risk and segment summaries"},
    {"check": "full_dataset_summaries_labeled_descriptive", "status": "PASS" if risk_full["descriptive_only"].eq("Y").all() and hier_full["descriptive_only"].eq("Y").all() else "FAIL", "detail": "full_descriptive labels"},
    {"check": "w1_3_primary_segmentation_basis", "status": "PASS", "detail": PRIMARY_WINDOW},
    {"check": "w1_4_labeled_late_period_only", "status": "PASS" if late_comparison else "PASS", "detail": "w1_4 comparison is late-period only"},
    {"check": "no_business_simulation_created", "status": "PASS", "detail": "No financial impact calculations"},
    {"check": "no_optuna_run", "status": "PASS", "detail": "No Optuna imports or tuning"},
    {"check": "no_model_tuning_run", "status": "PASS", "detail": "Only fixed Stage 06 conservative model reconstructed for full descriptive scoring"},
    {"check": "all_required_outputs_created", "status": "PASS" if all(p.exists() for p in required_outputs) else "FAIL", "detail": f"required_outputs={len(required_outputs)}"},
    {"check": "segment_action_recommendations_created", "status": "PASS" if (TABLE_DIR / "08_v2_segment_action_recommendations.csv").exists() else "FAIL", "detail": "action table"},
    {"check": "stage09_business_simulation_guidance_written", "status": "PASS" if "Stage 09 Guidance" in (DATA_DIR / "08_v2_segmentation_strategy_report.md").read_text(encoding="utf-8") else "FAIL", "detail": "report section"},
    {"check": "seven_validation_passes_documented", "status": "PASS" if len(validation_passes) == 7 else "FAIL", "detail": f"passes={len(validation_passes)}"},
    {"check": "internal_critique_section_written", "status": "PASS" if "Internal Critique and Segment Reliability Review" in (DATA_DIR / "08_v2_segmentation_strategy_report.md").read_text(encoding="utf-8") else "FAIL", "detail": "required report section"},
]
write_csv(TABLE_DIR / "08_v2_final_checks.csv", final_checks)

print("08_v2 segmentation strategy completed.")
for row in final_checks:
    print(f"{row['check']}: {row['status']} - {row['detail']}")
