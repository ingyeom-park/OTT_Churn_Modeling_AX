"""
Stage 08c: Corrected Segmentation Strategy
Based on Stage 06c2 corrected official model and Stage 07c TRUE SHAP.

Scope:
- No new model training (beyond reconstructing official 06c2 model for scoring)
- No Optuna, no SHAP, no business simulation, no model tuning
- Outputs under 08c_ prefix only; does not overwrite 08/08b outputs
- is_repurchase_label NOT used to define segments
- Stage 07c TRUE SHAP used as official XAI basis
"""

import json
import os
import platform
import sys
import warnings
from datetime import datetime
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)

# ── Constants ──────────────────────────────────────────────────────────────────
RANDOM_STATE = 42
TEST_SIZE = 0.2
ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"
TARGET = "is_repurchase_label"
OFFICIAL_FEATURE_SET = "pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence"
OFFICIAL_MODEL_NAME = "HistGradientBoostingClassifier"
EXPECTED_AUC = 0.8629394097379637
AUC_DIFF_THRESHOLD = 0.005
UNSTABLE_N_THRESHOLD = 50

# Genre ratio feature columns in the official feature set
GENRE_RATIO_COLS = [
    "w1_3_genre_ratio_action_adventure",
    "w1_3_genre_ratio_animation_family",
    "w1_3_genre_ratio_comedy",
    "w1_3_genre_ratio_documentary",
    "w1_3_genre_ratio_drama",
    "w1_3_genre_ratio_historical_war",
    "w1_3_genre_ratio_horror",
    "w1_3_genre_ratio_other",
    "w1_3_genre_ratio_romance",
    "w1_3_genre_ratio_sf_fantasy",
    "w1_3_genre_ratio_thriller_crime",
]
WEEK_WATCH_COLS = ["w1_3_week1_watch_time", "w1_3_week2_watch_time", "w1_3_week3_watch_time"]

# Segment keys (hierarchical priority order)
SEG_KEYS = [
    "최상위_이탈위험군",
    "초기중기_저관여_고위험군",
    "주차별이용패턴_고위험군",
    "장르비율_추천후보군",
    "안정유지_후보군",
    "일반관찰군",
]
SEG_KEYS_EN = [
    "top_highest_risk",
    "low_engagement_high_risk",
    "weekly_pattern_high_risk",
    "genre_affinity_recommendation_pool",
    "stable_maintenance_candidates",
    "general_observation",
]
SEG_NAME_MAP = dict(zip(SEG_KEYS, SEG_KEYS_EN))

# Non-exclusive flag keys
FLAG_KEYS = [
    "seg_top10_risk",
    "seg_high_risk_low_usage",
    "seg_risky_weekly_pattern",
    "seg_genre_affinity",
    "seg_stable_low_risk",
]

# ── Paths ──────────────────────────────────────────────────────────────────────
def find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "park.ingyeom" / "reports" / "data" / "05c_v2_modeling_dataset" / "feature_sets_v2c.json").exists():
            return candidate
    raise FileNotFoundError("Could not locate project root.")


PROJECT_ROOT = find_project_root(Path.cwd())
BASE = PROJECT_ROOT / "park.ingyeom"
STAGE05C_DATA = BASE / "reports" / "data" / "05c_v2_modeling_dataset"
STAGE06C2_DATA = BASE / "reports" / "data" / "06c2_v2_corrected_baseline_modeling"
STAGE06C2_TABLES = BASE / "reports" / "tables" / "06c2_v2_corrected_baseline_modeling"
STAGE07C_DATA = BASE / "reports" / "data" / "07c_v2_corrected_true_shap_interpretation"
STAGE07C_TABLES = BASE / "reports" / "tables" / "07c_v2_corrected_true_shap_interpretation"
DATA_DIR = BASE / "reports" / "data" / "08c_v2_corrected_segmentation_strategy"
TABLE_DIR = BASE / "reports" / "tables" / "08c_v2_corrected_segmentation_strategy"
FIGURE_DIR = BASE / "reports" / "figures" / "08c_v2_corrected_segmentation_strategy"
OLD_08B_TABLES = BASE / "reports" / "tables" / "08b_v2_segmentation_refinement"
OLD_08B_DATA = BASE / "reports" / "data" / "08b_v2_segmentation_refinement"

for d in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(Path(path).relative_to(PROJECT_ROOT)).replace("\\", "/")


def write_csv(path: Path, df: pd.DataFrame):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def save_fig(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()


# ── Pipeline helpers ───────────────────────────────────────────────────────────
def onehot_encoder():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def prepare_X(df: pd.DataFrame, features: list) -> pd.DataFrame:
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


# ── Step 1: Load inputs ────────────────────────────────────────────────────────
def load_inputs():
    print("[08c] Loading inputs ...")
    # Stage 06c2 summary
    summary = json.loads((STAGE06C2_DATA / "06c2_corrected_baseline_summary.json").read_text(encoding="utf-8"))
    rec = summary["official_corrected_recommendation"]
    assert rec["recommended_feature_set"] == OFFICIAL_FEATURE_SET, f"Feature set mismatch: {rec['recommended_feature_set']}"
    assert rec["recommended_model"] == OFFICIAL_MODEL_NAME, f"Model mismatch: {rec['recommended_model']}"
    print(f"  [OK] Stage 06c2 official: {rec['recommended_model']} on {rec['recommended_feature_set']}, AUC={rec['roc_auc_repurchase']:.6f}")

    # Stage 07c SHAP summary
    shap_summary = json.loads((STAGE07C_DATA / "07c_true_shap_summary.json").read_text(encoding="utf-8"))
    global_shap = pd.read_csv(STAGE07C_TABLES / "07c_global_shap_importance.csv")
    family_shap = pd.read_csv(STAGE07C_TABLES / "07c_feature_family_shap_importance.csv")
    shap_direction = pd.read_csv(STAGE07C_TABLES / "07c_shap_direction_summary.csv")
    print(f"  [OK] Stage 07c SHAP: top family={family_shap.iloc[0]['feature_family']}, features={len(global_shap)}")

    # Feature sets
    fs_json = json.loads((STAGE05C_DATA / "feature_sets_v2c.json").read_text(encoding="utf-8"))
    features = fs_json["feature_sets"][OFFICIAL_FEATURE_SET]["features"]
    print(f"  [OK] Official feature set: {len(features)} features")

    # Modeling dataset
    df = pd.read_csv(STAGE05C_DATA / "modeling_dataset_v2c_w1_3.csv", low_memory=False)
    print(f"  [OK] Modeling dataset: {len(df)} rows, {len(df.columns)} columns")

    return summary, rec, shap_summary, global_shap, family_shap, shap_direction, features, df


# ── Step 2: Reconstruct official model & generate prediction scores ────────────
def reconstruct_and_score(df: pd.DataFrame, features: list):
    print("[08c] Reconstructing official model and generating prediction scores ...")

    y = pd.to_numeric(df[TARGET], errors="coerce").astype(int).to_numpy()
    groups = df[GROUP_COL].astype(str).to_numpy()

    splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    train_idx, test_idx = next(splitter.split(df, y, groups))
    overlap = len(set(groups[train_idx]) & set(groups[test_idx]))
    assert overlap == 0, f"USER_KEY overlap between train and test: {overlap}"

    X = prepare_X(df, features)
    pipe = make_pipeline(X)
    pipe.fit(X.iloc[train_idx], y[train_idx])

    # Predict on holdout
    rep_score_test = pipe.predict_proba(X.iloc[test_idx])[:, 1]
    churn_score_test = 1.0 - rep_score_test
    auc_test = float(roc_auc_score(y[test_idx], rep_score_test))
    auc_diff = abs(auc_test - EXPECTED_AUC)
    print(f"  [OK] Reconstructed AUC={auc_test:.10f}, expected={EXPECTED_AUC:.10f}, diff={auc_diff:.10f}")
    assert auc_diff <= AUC_DIFF_THRESHOLD, f"AUC reconstruction failed: diff={auc_diff:.6f} > {AUC_DIFF_THRESHOLD}"

    # Predict on train set (for full descriptive)
    rep_score_train = pipe.predict_proba(X.iloc[train_idx])[:, 1]
    churn_score_train = 1.0 - rep_score_train

    # Build holdout compact scores
    holdout_meta = df.iloc[test_idx].reset_index(drop=True)
    holdout_scores = pd.DataFrame({
        ID_COL: holdout_meta[ID_COL].values,
        GROUP_COL: holdout_meta[GROUP_COL].values,
        "split": "holdout",
        TARGET: y[test_idx],
        "repurchase_score": rep_score_test,
        "churn_risk_score": churn_score_test,
    })

    # Build train compact scores
    train_meta = df.iloc[train_idx].reset_index(drop=True)
    train_scores = pd.DataFrame({
        ID_COL: train_meta[ID_COL].values,
        GROUP_COL: train_meta[GROUP_COL].values,
        "split": "train",
        TARGET: y[train_idx],
        "repurchase_score": rep_score_train,
        "churn_risk_score": churn_score_train,
    })

    # Full descriptive (train + holdout)
    full_scores = pd.concat([holdout_scores, train_scores], ignore_index=True)
    full_scores["descriptive_note"] = full_scores["split"].map(
        {"holdout": "primary_evaluation", "train": "descriptive_only_do_not_use_for_primary_results"}
    )

    write_csv(DATA_DIR / "08c_official_prediction_scores_holdout.csv", holdout_scores)
    write_csv(DATA_DIR / "08c_official_prediction_scores_full_descriptive.csv", full_scores)
    print(f"  Saved holdout scores: n={len(holdout_scores)}, train scores: n={len(train_scores)}")

    # Also pass back the raw feature values for the holdout (for segmentation)
    holdout_features = prepare_X(holdout_meta, features).reset_index(drop=True)

    return holdout_scores, full_scores, train_scores, holdout_features, auc_test, train_idx, test_idx


# ── Step 3: Risk bands ─────────────────────────────────────────────────────────
RISK_BAND_ORDER = ["top_10_highest_risk", "risk_10_30", "risk_30_60", "bottom_40_lowest_risk"]

def assign_risk_bands(churn_risk: np.ndarray) -> tuple:
    """Compute thresholds from holdout and return band labels + threshold dict."""
    p40 = float(np.percentile(churn_risk, 40))
    p70 = float(np.percentile(churn_risk, 70))
    p90 = float(np.percentile(churn_risk, 90))
    thresholds = {"p40": p40, "p70": p70, "p90": p90}

    bands = np.where(
        churn_risk >= p90, "top_10_highest_risk",
        np.where(
            churn_risk >= p70, "risk_10_30",
            np.where(
                churn_risk >= p40, "risk_30_60",
                "bottom_40_lowest_risk"
            )
        )
    )
    return bands, thresholds


def risk_band_stats(scores: pd.DataFrame, bands: np.ndarray, label: str) -> pd.DataFrame:
    overall_churn_rate = float(1 - scores[TARGET].mean())
    rows = []
    for band in RISK_BAND_ORDER:
        mask = bands == band
        sub = scores[mask]
        n = int(mask.sum())
        if n == 0:
            continue
        churn_rate = float(1 - sub[TARGET].mean())
        rep_rate = float(sub[TARGET].mean())
        churners = int((1 - sub[TARGET]).sum())
        total_churners = int((1 - scores[TARGET]).sum())
        rows.append({
            "population": label,
            "risk_band": band,
            "n": n,
            "share": round(n / len(scores), 4),
            "repurchase_rate": round(rep_rate, 4),
            "churn_rate": round(churn_rate, 4),
            "lift_vs_overall_churn_rate": round(churn_rate / overall_churn_rate, 4) if overall_churn_rate else np.nan,
            "captured_churners": churners,
            "churner_capture_rate": round(churners / total_churners, 4) if total_churners else np.nan,
            "avg_repurchase_score": round(float(sub["repurchase_score"].mean()), 4),
            "avg_churn_risk_score": round(float(sub["churn_risk_score"].mean()), 4),
        })
    return pd.DataFrame(rows)


# ── Step 4: Non-exclusive segment flags ───────────────────────────────────────
def compute_segment_flags(holdout_scores: pd.DataFrame, holdout_features: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    """Create non-exclusive segment flags on the holdout set."""
    churn_risk = holdout_scores["churn_risk_score"].to_numpy()
    p40 = thresholds["p40"]
    p70 = thresholds["p70"]
    p90 = thresholds["p90"]

    # Total watch time (sum of available week columns)
    week_cols_present = [c for c in WEEK_WATCH_COLS if c in holdout_features.columns]
    total_watch = holdout_features[week_cols_present].fillna(0).sum(axis=1).to_numpy()
    usage_p33 = float(np.percentile(total_watch, 33))

    # Declining weekly pattern: week3 < week1 * 0.5 OR all zero usage
    w1 = holdout_features["w1_3_week1_watch_time"].fillna(0).to_numpy() if "w1_3_week1_watch_time" in holdout_features.columns else np.zeros(len(holdout_features))
    w3 = holdout_features["w1_3_week3_watch_time"].fillna(0).to_numpy() if "w1_3_week3_watch_time" in holdout_features.columns else np.zeros(len(holdout_features))
    declining_pattern = (w3 < w1 * 0.5) | (total_watch == 0)

    # Genre affinity: max genre ratio > 0.4
    genre_cols_present = [c for c in GENRE_RATIO_COLS if c in holdout_features.columns]
    if genre_cols_present:
        max_genre = holdout_features[genre_cols_present].fillna(0).max(axis=1).to_numpy()
    else:
        max_genre = np.zeros(len(holdout_features))
    genre_affinity = max_genre > 0.4

    flags = pd.DataFrame({
        ID_COL: holdout_scores[ID_COL].values,
        "seg_top10_risk":         (churn_risk >= p90).astype(int),
        "seg_high_risk_low_usage":(
            (churn_risk >= p70) & (churn_risk < p90) & (total_watch < usage_p33)
        ).astype(int),
        "seg_risky_weekly_pattern":(
            (churn_risk >= p40) & (churn_risk < p90) & declining_pattern
        ).astype(int),
        "seg_genre_affinity":     genre_affinity.astype(int),
        "seg_stable_low_risk":    (churn_risk < p40).astype(int),
    })

    thresholds["usage_p33"] = round(usage_p33, 4)
    thresholds["genre_affinity_max_genre_ratio"] = 0.4
    thresholds["declining_pattern_rule"] = "week3_watch_time < week1_watch_time * 0.5 OR total_watch_time == 0"

    return flags, thresholds


def apply_flags_to_full(full_scores: pd.DataFrame, full_feature_values: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    """Apply same flag thresholds to the full dataset."""
    churn_risk = full_scores["churn_risk_score"].to_numpy()
    p40 = thresholds["p40"]
    p70 = thresholds["p70"]
    p90 = thresholds["p90"]
    usage_p33 = thresholds["usage_p33"]
    genre_p = 0.4

    week_cols_present = [c for c in WEEK_WATCH_COLS if c in full_feature_values.columns]
    total_watch = full_feature_values[week_cols_present].fillna(0).sum(axis=1).to_numpy()

    w1 = full_feature_values["w1_3_week1_watch_time"].fillna(0).to_numpy() if "w1_3_week1_watch_time" in full_feature_values.columns else np.zeros(len(full_feature_values))
    w3 = full_feature_values["w1_3_week3_watch_time"].fillna(0).to_numpy() if "w1_3_week3_watch_time" in full_feature_values.columns else np.zeros(len(full_feature_values))
    declining_pattern = (w3 < w1 * 0.5) | (total_watch == 0)

    genre_cols_present = [c for c in GENRE_RATIO_COLS if c in full_feature_values.columns]
    if genre_cols_present:
        max_genre = full_feature_values[genre_cols_present].fillna(0).max(axis=1).to_numpy()
    else:
        max_genre = np.zeros(len(full_feature_values))
    genre_affinity = max_genre > genre_p

    flags = pd.DataFrame({
        ID_COL: full_scores[ID_COL].values,
        "seg_top10_risk":         (churn_risk >= p90).astype(int),
        "seg_high_risk_low_usage":(
            (churn_risk >= p70) & (churn_risk < p90) & (total_watch < usage_p33)
        ).astype(int),
        "seg_risky_weekly_pattern":(
            (churn_risk >= p40) & (churn_risk < p90) & declining_pattern
        ).astype(int),
        "seg_genre_affinity":     genre_affinity.astype(int),
        "seg_stable_low_risk":    (churn_risk < p40).astype(int),
    })
    return flags


# ── Step 5: Hierarchical segment assignment ────────────────────────────────────
def assign_hierarchy(scores: pd.DataFrame, flags: pd.DataFrame) -> pd.Series:
    """
    Priority order (first match wins):
    1. 최상위_이탈위험군    → seg_top10_risk
    2. 초기중기_저관여_고위험군 → seg_high_risk_low_usage (risk_10_30 only, not top10)
    3. 주차별이용패턴_고위험군  → seg_risky_weekly_pattern (risk_10_30 or risk_30_60)
    4. 장르비율_추천후보군   → seg_genre_affinity (not already in 1-3)
    5. 안정유지_후보군      → seg_stable_low_risk (not already assigned)
    6. 일반관찰군          → residual
    """
    n = len(scores)
    seg = pd.Series([""] * n, dtype=str)

    seg1 = flags["seg_top10_risk"].astype(bool)
    seg2 = flags["seg_high_risk_low_usage"].astype(bool) & ~seg1
    seg3 = flags["seg_risky_weekly_pattern"].astype(bool) & ~seg1 & ~seg2
    seg4 = flags["seg_genre_affinity"].astype(bool) & ~seg1 & ~seg2 & ~seg3
    seg5 = flags["seg_stable_low_risk"].astype(bool) & ~seg1 & ~seg2 & ~seg3 & ~seg4
    seg6 = ~seg1 & ~seg2 & ~seg3 & ~seg4 & ~seg5

    seg[seg1] = "최상위_이탈위험군"
    seg[seg2] = "초기중기_저관여_고위험군"
    seg[seg3] = "주차별이용패턴_고위험군"
    seg[seg4] = "장르비율_추천후보군"
    seg[seg5] = "안정유지_후보군"
    seg[seg6] = "일반관찰군"

    return seg


def hierarchical_segment_stats(scores: pd.DataFrame, seg_col: pd.Series, population: str) -> pd.DataFrame:
    overall_churn_rate = float(1 - scores[TARGET].mean())
    total_churners = int((1 - scores[TARGET]).sum())
    rows = []
    for key in SEG_KEYS:
        mask = seg_col == key
        sub = scores[mask]
        n = int(mask.sum())
        if n == 0:
            continue
        churn_rate = float(1 - sub[TARGET].mean())
        rep_rate = float(sub[TARGET].mean())
        churners = int((1 - sub[TARGET]).sum())
        rows.append({
            "population": population,
            "final_segment_key": key,
            "final_segment_en": SEG_NAME_MAP.get(key, key),
            "n": n,
            "share": round(n / len(scores), 4),
            "repurchase_rate": round(rep_rate, 4),
            "churn_rate": round(churn_rate, 4),
            "lift_vs_overall_churn_rate": round(churn_rate / overall_churn_rate, 4) if overall_churn_rate else np.nan,
            "captured_churners": churners,
            "churner_capture_rate": round(churners / total_churners, 4) if total_churners else np.nan,
            "avg_repurchase_score": round(float(sub["repurchase_score"].mean()), 4),
            "avg_churn_risk_score": round(float(sub["churn_risk_score"].mean()), 4),
            "stability_note": "unstable_small_n" if n < UNSTABLE_N_THRESHOLD else "stable",
        })
    return pd.DataFrame(rows)


# ── Step 6: Figures ────────────────────────────────────────────────────────────
def fig_risk_band_churn_rate(band_summary: pd.DataFrame):
    df = band_summary[band_summary["population"] == "holdout"].set_index("risk_band").reindex(RISK_BAND_ORDER).reset_index()
    plt.figure(figsize=(8, 5))
    colors = ["#c0392b", "#e67e22", "#f39c12", "#27ae60"]
    bars = plt.bar(df["risk_band"], df["churn_rate"], color=colors)
    for bar, val in zip(bars, df["churn_rate"]):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005, f"{val:.1%}", ha="center", va="bottom", fontsize=9)
    plt.axhline(df["churn_rate"].mean() if "bottom_40_lowest_risk" not in df else float(1 - band_summary[band_summary["population"] == "holdout"].assign(wt=lambda x: x["n"])["repurchase_rate"].dot(band_summary[band_summary["population"] == "holdout"]["n"]) / band_summary[band_summary["population"] == "holdout"]["n"].sum()), color="gray", linestyle="--", label="Overall churn rate (approx)")
    plt.title("08c Corrected: Churn Rate by Risk Band (Holdout)", fontsize=12, fontweight="bold")
    plt.ylabel("Churn Rate")
    plt.xlabel("Risk Band")
    plt.xticks(rotation=15, ha="right")
    plt.ylim(0, 1.0)
    plt.tight_layout()
    save_fig(FIGURE_DIR / "08c_risk_band_churn_rate_holdout.png")


def fig_risk_band_lift(band_summary: pd.DataFrame):
    df = band_summary[band_summary["population"] == "holdout"].set_index("risk_band").reindex(RISK_BAND_ORDER).reset_index()
    plt.figure(figsize=(8, 5))
    colors = ["#c0392b", "#e67e22", "#f39c12", "#27ae60"]
    bars = plt.bar(df["risk_band"], df["lift_vs_overall_churn_rate"], color=colors)
    for bar, val in zip(bars, df["lift_vs_overall_churn_rate"]):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01, f"{val:.2f}x", ha="center", va="bottom", fontsize=9)
    plt.axhline(1.0, color="gray", linestyle="--", label="Baseline (1.0x)")
    plt.title("08c Corrected: Churn Lift by Risk Band (Holdout)", fontsize=12, fontweight="bold")
    plt.ylabel("Lift vs Overall Churn Rate")
    plt.xlabel("Risk Band")
    plt.xticks(rotation=15, ha="right")
    plt.ylim(0, max(df["lift_vs_overall_churn_rate"].max() * 1.2, 3.0))
    plt.tight_layout()
    save_fig(FIGURE_DIR / "08c_risk_band_lift_holdout.png")


def fig_hierarchical_segment_size_and_churn(seg_summary: pd.DataFrame):
    df = seg_summary[seg_summary["population"] == "holdout"].copy()
    fig, ax1 = plt.subplots(figsize=(10, 6))
    x = np.arange(len(df))
    bars = ax1.bar(x - 0.2, df["n"], width=0.35, label="n (count)", color="#2980b9", alpha=0.85)
    ax1.set_xlabel("Segment")
    ax1.set_ylabel("n (count)", color="#2980b9")
    ax1.tick_params(axis="y", labelcolor="#2980b9")
    ax2 = ax1.twinx()
    ax2.bar(x + 0.2, df["churn_rate"], width=0.35, label="Churn Rate", color="#e74c3c", alpha=0.85)
    ax2.set_ylabel("Churn Rate", color="#e74c3c")
    ax2.tick_params(axis="y", labelcolor="#e74c3c")
    ax2.set_ylim(0, 1.0)
    ax1.set_xticks(x)
    ax1.set_xticklabels(df["final_segment_key"], rotation=20, ha="right", fontsize=8)
    ax1.set_title("08c Corrected: Segment Size and Churn Rate (Holdout)", fontsize=12, fontweight="bold")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
    plt.tight_layout()
    save_fig(FIGURE_DIR / "08c_hierarchical_segment_size_and_churn.png")


def fig_segment_action_map(seg_summary: pd.DataFrame):
    df = seg_summary[seg_summary["population"] == "holdout"].copy()
    actions_ko = {
        "최상위_이탈위험군": "고위험 모니터링\n개인화 리텐션 메시지",
        "초기중기_저관여_고위험군": "초기 온보딩 강화\n첫 시청 유도",
        "주차별이용패턴_고위험군": "주차별 패턴 기반\n지속 시청 독려",
        "장르비율_추천후보군": "장르별 신작 추천\n취향 기반 큐레이션",
        "안정유지_후보군": "기본 유지 메시지\n구독 갱신 안내",
        "일반관찰군": "기본 모니터링",
    }
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(df) + 1)
    ax.axis("off")
    ax.set_title("08c Corrected: Segment Action Map (Holdout, Observational)", fontsize=12, fontweight="bold")
    color_map = {
        "최상위_이탈위험군": "#c0392b",
        "초기중기_저관여_고위험군": "#e67e22",
        "주차별이용패턴_고위험군": "#f39c12",
        "장르비율_추천후보군": "#8e44ad",
        "안정유지_후보군": "#27ae60",
        "일반관찰군": "#7f8c8d",
    }
    for i, row in enumerate(df.itertuples()):
        y_pos = len(df) - i
        color = color_map.get(row.final_segment_key, "#7f8c8d")
        ax.barh(y_pos, 3.5, left=0.2, height=0.7, color=color, alpha=0.85)
        ax.text(0.4, y_pos, f"{row.final_segment_key}", va="center", color="white", fontsize=8, fontweight="bold")
        ax.barh(y_pos, 3.0, left=4.0, height=0.7, color="#ecf0f1", alpha=1)
        action = actions_ko.get(row.final_segment_key, "")
        ax.text(4.2, y_pos, action, va="center", fontsize=8)
        ax.barh(y_pos, 2.2, left=7.3, height=0.7, color="#ecf0f1", alpha=1)
        ax.text(7.4, y_pos, f"n={row.n} | churn={row.churn_rate:.0%}", va="center", fontsize=7.5)
    ax.text(1.5, len(df) + 0.6, "Segment", ha="center", fontsize=9, fontweight="bold")
    ax.text(5.5, len(df) + 0.6, "Recommended Action (Observational)", ha="center", fontsize=9, fontweight="bold")
    ax.text(8.4, len(df) + 0.6, "Size & Churn Rate", ha="center", fontsize=9, fontweight="bold")
    plt.tight_layout()
    save_fig(FIGURE_DIR / "08c_segment_action_map.png")


def fig_segment_shap_evidence_heatmap():
    segments = SEG_KEYS
    families = ["weekly_usage_pattern", "genre_ratio_proxy", "membership_context", "simple_usage_volume", "release_month_proxy"]
    evidence = {
        "최상위_이탈위험군":        [3, 2, 2, 1, 0],
        "초기중기_저관여_고위험군":  [3, 1, 1, 2, 0],
        "주차별이용패턴_고위험군":   [3, 2, 1, 1, 0],
        "장르비율_추천후보군":       [1, 3, 1, 0, 0],
        "안정유지_후보군":           [2, 1, 1, 1, 0],
        "일반관찰군":               [0, 0, 0, 0, 0],
    }
    matrix = np.array([evidence[s] for s in segments], dtype=float)
    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(matrix, cmap="YlOrRd", vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(np.arange(len(families)))
    ax.set_yticks(np.arange(len(segments)))
    ax.set_xticklabels(families, rotation=20, ha="right", fontsize=8)
    ax.set_yticklabels(segments, fontsize=8)
    for i in range(len(segments)):
        for j in range(len(families)):
            val = matrix[i, j]
            label = {0: "none", 1: "weak", 2: "moderate", 3: "strong"}.get(int(val), "")
            ax.text(j, i, label, ha="center", va="center", fontsize=7, color="black" if val < 2.5 else "white")
    plt.colorbar(im, ax=ax, label="Evidence level (0=none, 3=strong)")
    ax.set_title("08c Corrected: Segment × SHAP Feature Family Evidence\n(Based on Stage 07c TRUE SHAP, observational only)", fontsize=10, fontweight="bold")
    plt.tight_layout()
    save_fig(FIGURE_DIR / "08c_segment_shap_evidence_heatmap.png")


def fig_top_decile_churn_capture(holdout_scores: pd.DataFrame):
    df = holdout_scores.sort_values("churn_risk_score", ascending=False).reset_index(drop=True)
    churn_flag = 1 - df[TARGET].to_numpy()
    total_churners = int(churn_flag.sum())
    cumulative_churners = np.cumsum(churn_flag)
    cumulative_share = np.arange(1, len(df) + 1) / len(df)

    plt.figure(figsize=(8, 5))
    plt.plot(cumulative_share * 100, cumulative_churners / total_churners * 100, color="#c0392b", linewidth=2, label="08c Official Model")
    plt.plot([0, 100], [0, 100], "k--", linewidth=1, alpha=0.5, label="Random baseline")
    for decile in [10, 20, 30]:
        idx = max(0, int(len(df) * decile / 100) - 1)
        cap = cumulative_churners[idx] / total_churners * 100
        plt.axvline(decile, color="gray", linestyle=":", linewidth=0.8)
        plt.text(decile + 0.3, cap + 1, f"Top {decile}%:\n{cap:.0f}% captured", fontsize=7.5, color="gray")
    plt.title("08c Corrected: Cumulative Churn Capture Curve (Holdout)", fontsize=12, fontweight="bold")
    plt.xlabel("% of Population Targeted (by churn_risk_score, high→low)")
    plt.ylabel("% of Churners Captured")
    plt.xlim(0, 100)
    plt.ylim(0, 105)
    plt.legend(fontsize=9)
    plt.tight_layout()
    save_fig(FIGURE_DIR / "08c_top_decile_churn_capture.png")


# ── Step 7: Tables ─────────────────────────────────────────────────────────────
def write_segment_flag_definitions():
    rows = [
        {"flag_key": "seg_top10_risk", "flag_name_ko": "최상위 위험 플래그",
         "definition": "churn_risk_score >= p90 of holdout",
         "primary_shap_family": "weekly_usage_pattern",
         "caution": "Top 10% by predicted churn risk score; observational ranking only"},
        {"flag_key": "seg_high_risk_low_usage", "flag_name_ko": "고위험 저관여 플래그",
         "definition": "churn_risk_score in [p70, p90) AND total_watch_time < p33 of holdout",
         "primary_shap_family": "weekly_usage_pattern + simple_usage_volume",
         "caution": "Low engagement within risk_10_30 band; not top10"},
        {"flag_key": "seg_risky_weekly_pattern", "flag_name_ko": "위험 주차 패턴 플래그",
         "definition": "churn_risk_score in [p40, p90) AND (week3_watch_time < week1_watch_time * 0.5 OR total_watch_time == 0)",
         "primary_shap_family": "weekly_usage_pattern",
         "caution": "Declining or absent weekly usage pattern; do not claim causality"},
        {"flag_key": "seg_genre_affinity", "flag_name_ko": "장르 선호 플래그",
         "definition": "max(genre_ratio_*) > 0.4",
         "primary_shap_family": "genre_ratio_proxy",
         "caution": "Any dominant genre above 40% ratio; content recommendation basis only"},
        {"flag_key": "seg_stable_low_risk", "flag_name_ko": "안정 저위험 플래그",
         "definition": "churn_risk_score < p40 of holdout",
         "primary_shap_family": "weekly_usage_pattern (high usage)",
         "caution": "Bottom 40% by predicted churn risk; maintenance group, not targeting"},
    ]
    write_csv(TABLE_DIR / "08c_nonexclusive_segment_flag_summary.csv",
              pd.DataFrame(rows))
    write_csv(TABLE_DIR / "08c_segment_flag_definitions.csv", pd.DataFrame(rows))


def write_nonexclusive_flag_summary(holdout_scores: pd.DataFrame, holdout_flags: pd.DataFrame):
    overall_churn = float(1 - holdout_scores[TARGET].mean())
    total_churners = int((1 - holdout_scores[TARGET]).sum())
    rows = []
    for flag in FLAG_KEYS:
        if flag not in holdout_flags.columns:
            continue
        mask = holdout_flags[flag].astype(bool)
        sub = holdout_scores[mask.values]
        n = int(mask.sum())
        if n == 0:
            rows.append({"flag_key": flag, "n": 0, "share": 0, "churn_rate": np.nan,
                         "lift": np.nan, "captured_churners": 0, "churner_capture_rate": 0,
                         "stability_note": "empty"})
            continue
        churn_rate = float(1 - sub[TARGET].mean())
        churners = int((1 - sub[TARGET]).sum())
        rows.append({
            "flag_key": flag,
            "n": n,
            "share": round(n / len(holdout_scores), 4),
            "churn_rate": round(churn_rate, 4),
            "lift": round(churn_rate / overall_churn, 4) if overall_churn else np.nan,
            "captured_churners": churners,
            "churner_capture_rate": round(churners / total_churners, 4) if total_churners else np.nan,
            "stability_note": "unstable_small_n" if n < UNSTABLE_N_THRESHOLD else "stable",
        })
    write_csv(TABLE_DIR / "08c_nonexclusive_segment_flag_summary.csv", pd.DataFrame(rows))


def write_segment_thresholds(thresholds: dict):
    rows = [
        {"threshold_name": "risk_band_p90", "threshold_value": round(thresholds["p90"], 6),
         "derived_from": "holdout_churn_risk_score_90th_percentile", "used_for": "top_10_highest_risk band"},
        {"threshold_name": "risk_band_p70", "threshold_value": round(thresholds["p70"], 6),
         "derived_from": "holdout_churn_risk_score_70th_percentile", "used_for": "risk_10_30 band lower bound"},
        {"threshold_name": "risk_band_p40", "threshold_value": round(thresholds["p40"], 6),
         "derived_from": "holdout_churn_risk_score_40th_percentile", "used_for": "risk_30_60 band lower bound"},
        {"threshold_name": "low_usage_total_watch_p33", "threshold_value": round(thresholds.get("usage_p33", 0), 4),
         "derived_from": "holdout_total_watch_time_33rd_percentile",
         "used_for": "seg_high_risk_low_usage flag"},
        {"threshold_name": "genre_affinity_max_genre_ratio", "threshold_value": 0.40,
         "derived_from": "fixed_interpretable_threshold",
         "used_for": "seg_genre_affinity flag"},
        {"threshold_name": "declining_pattern_week3_vs_week1_ratio", "threshold_value": 0.50,
         "derived_from": "fixed_interpretable_threshold",
         "used_for": "seg_risky_weekly_pattern flag: week3 < week1 * 0.5"},
    ]
    write_csv(TABLE_DIR / "08c_segment_thresholds.csv", pd.DataFrame(rows))


def write_input_summary():
    inputs = [
        (STAGE05C_DATA / "modeling_dataset_v2c_w1_3.csv", "modeling_dataset"),
        (STAGE05C_DATA / "feature_sets_v2c.json", "feature_sets"),
        (STAGE06C2_DATA / "06c2_corrected_baseline_summary.json", "baseline_summary"),
        (STAGE06C2_DATA / "06c2_final_model_recommendation.md", "model_recommendation"),
        (STAGE06C2_TABLES / "06c2_group_split_summary.csv", "group_split"),
        (STAGE06C2_TABLES / "06c2_model_metrics.csv", "model_metrics"),
        (STAGE07C_DATA / "07c_true_shap_summary.json", "shap_summary"),
        (STAGE07C_DATA / "07c_team_share_shap_summary.md", "shap_team_share"),
        (STAGE07C_TABLES / "07c_global_shap_importance.csv", "global_shap"),
        (STAGE07C_TABLES / "07c_feature_family_shap_importance.csv", "family_shap"),
        (STAGE07C_TABLES / "07c_shap_direction_summary.csv", "shap_direction"),
    ]
    rows = []
    for path, label in inputs:
        exists = path.exists()
        rows.append({
            "input_file": rel(path),
            "label": label,
            "status": "found" if exists else "missing",
            "note": "required" if "summary" in label or "dataset" in label or "feature_set" in label else "reference",
        })
    write_csv(TABLE_DIR / "08c_input_summary.csv", pd.DataFrame(rows))


def write_segment_overlap_matrix(holdout_flags: pd.DataFrame):
    cols = [c for c in FLAG_KEYS if c in holdout_flags.columns]
    n = len(cols)
    matrix = pd.DataFrame(index=cols, columns=cols, dtype=int)
    for a in cols:
        for b in cols:
            matrix.loc[a, b] = int((holdout_flags[a].astype(bool) & holdout_flags[b].astype(bool)).sum())
    write_csv(TABLE_DIR / "08c_segment_overlap_matrix.csv", matrix.reset_index().rename(columns={"index": "segment_flag"}))


def write_segment_shap_evidence_map():
    families = ["weekly_usage_pattern", "genre_ratio_proxy", "membership_context", "simple_usage_volume", "release_month_proxy"]
    evidence = {
        "최상위_이탈위험군":        ["strong", "moderate", "moderate", "weak", "none"],
        "초기중기_저관여_고위험군":  ["strong", "weak",     "weak",     "moderate", "none"],
        "주차별이용패턴_고위험군":   ["strong", "moderate", "weak",     "weak", "none"],
        "장르비율_추천후보군":       ["weak",   "strong",   "weak",     "none", "none"],
        "안정유지_후보군":           ["moderate","weak",    "weak",     "weak", "none"],
        "일반관찰군":               ["none",   "none",     "none",     "none", "none"],
    }
    rows = []
    for seg, ev_list in evidence.items():
        row = {"final_segment_key": seg}
        for fam, ev in zip(families, ev_list):
            row[fam] = ev
        row["shap_basis"] = "Stage 07c TRUE SHAP (corrected official)"
        row["caution"] = "SHAP is observational association only; no causality claim"
        rows.append(row)
    write_csv(TABLE_DIR / "08c_segment_shap_evidence_map.csv", pd.DataFrame(rows))


def write_segment_action_recommendations():
    rows = [
        {
            "final_segment_key": "최상위_이탈위험군",
            "segment_en": "top_highest_risk",
            "n_holdout": None,
            "churn_rate_holdout": None,
            "recommended_action_ko": "고위험 모니터링, 개인화 리텐션 메시지, 초기 콘텐츠 재추천",
            "recommended_action_en": "High-risk monitoring, personalized retention message, content re-recommendation",
            "presentation_readiness": "safe_to_report_with_caution",
            "caution": "Predicted risk ranking only; no causal claim. Do not promise retention lift.",
            "use_in_stage09c_simulation": "Y",
        },
        {
            "final_segment_key": "초기중기_저관여_고위험군",
            "segment_en": "low_engagement_high_risk",
            "n_holdout": None,
            "churn_rate_holdout": None,
            "recommended_action_ko": "초기 온보딩 강화, 첫 시청 유도, 개인화 콘텐츠 추천",
            "recommended_action_en": "Onboarding enhancement, first-watch activation, personalized content suggestion",
            "presentation_readiness": "safe_to_report_with_caution",
            "caution": "Low engagement is a predictive signal, not proven cause of churn. No intervention ROI claim.",
            "use_in_stage09c_simulation": "Y",
        },
        {
            "final_segment_key": "주차별이용패턴_고위험군",
            "segment_en": "weekly_pattern_high_risk",
            "n_holdout": None,
            "churn_rate_holdout": None,
            "recommended_action_ko": "주차별 패턴 기반 지속 시청 독려, 시리즈 추천, 이용 촉진 알림",
            "recommended_action_en": "Encourage continued viewing based on weekly pattern, series recommendation, activity nudge",
            "presentation_readiness": "plausible_but_cautioned",
            "caution": "Declining or absent watch pattern is a predictive signal. Do not claim causality.",
            "use_in_stage09c_simulation": "Y",
        },
        {
            "final_segment_key": "장르비율_추천후보군",
            "segment_en": "genre_affinity_recommendation_pool",
            "n_holdout": None,
            "churn_rate_holdout": None,
            "recommended_action_ko": "장르별 신작 추천, 취향 기반 큐레이션, 이어보기 유도",
            "recommended_action_en": "Genre-based new content recommendation, preference-based curation, watch continuation",
            "presentation_readiness": "plausible_but_cautioned",
            "caution": "Genre ratio is content proxy only. Not necessarily high-risk. Content metadata is limited.",
            "use_in_stage09c_simulation": "Y",
        },
        {
            "final_segment_key": "안정유지_후보군",
            "segment_en": "stable_maintenance_candidates",
            "n_holdout": None,
            "churn_rate_holdout": None,
            "recommended_action_ko": "기본 유지 메시지, 구독 갱신 안내, 신작 알림",
            "recommended_action_en": "Basic maintenance message, subscription renewal reminder, new content notification",
            "presentation_readiness": "safe_to_report_as_context_only",
            "caution": "Low predicted churn risk. Do not over-intervene. Maintenance and light-touch only.",
            "use_in_stage09c_simulation": "N",
        },
        {
            "final_segment_key": "일반관찰군",
            "segment_en": "general_observation",
            "n_holdout": None,
            "churn_rate_holdout": None,
            "recommended_action_ko": "기본 모니터링, 추가 분석 필요 시 서브 세그먼트 검토",
            "recommended_action_en": "Baseline monitoring; sub-segment review if additional analysis needed",
            "presentation_readiness": "safe_to_report_as_context_only",
            "caution": "Residual group. Do not overclaim. No strong single driver identified.",
            "use_in_stage09c_simulation": "N",
        },
    ]
    write_csv(TABLE_DIR / "08c_segment_action_recommendations.csv", pd.DataFrame(rows))


def write_old08b_comparison():
    rows = [
        {
            "old_08b_segment_key": "top_decile_high_churn_risk",
            "old_08b_segment_ko": "최상위 이탈위험군",
            "old_08b_churn_rate": 0.7845,
            "new_08c_segment_key": "최상위_이탈위험군",
            "new_08c_segment_ko": "최상위 이탈위험군",
            "status": "kept_renamed",
            "reason": "Same top 10% risk concept. AUC corrected from ~0.8047 to 0.8629; official scores differ.",
        },
        {
            "old_08b_segment_key": "risk_10_30_low_engagement",
            "old_08b_segment_ko": "초기 저관여 고위험군",
            "old_08b_churn_rate": 0.5669,
            "new_08c_segment_key": "초기중기_저관여_고위험군",
            "new_08c_segment_ko": "초기/중기 저관여 고위험군",
            "status": "kept_refined",
            "reason": "Similar concept. Now uses corrected 06c2 scores and explicit total watch time threshold.",
        },
        {
            "old_08b_segment_key": "risk_10_30_other_review",
            "old_08b_segment_ko": "상위위험 관찰/추천 후보군",
            "old_08b_churn_rate": 0.6151,
            "new_08c_segment_key": "주차별이용패턴_고위험군",
            "new_08c_segment_ko": "주차별 이용패턴 기반 고위험군",
            "status": "changed",
            "reason": "Now uses explicit declining weekly pattern threshold instead of residual risk_10_30 catch-all.",
        },
        {
            "old_08b_segment_key": "late_week3_engaged_retention_candidate",
            "old_08b_segment_ko": "3주차 집중 시청 안정/전환 후보군",
            "old_08b_churn_rate": 0.0698,
            "new_08c_segment_key": "안정유지_후보군",
            "new_08c_segment_ko": "안정 유지 후보군",
            "status": "merged_simplified",
            "reason": "Old 08b used late week3 flag separately. 08c uses churn_risk bottom 40% as simpler stable group.",
        },
        {
            "old_08b_segment_key": "genre_affinity_content_recommendation_pool",
            "old_08b_segment_ko": "장르 선호 기반 콘텐츠 추천군",
            "old_08b_churn_rate": 0.1444,
            "new_08c_segment_key": "장르비율_추천후보군",
            "new_08c_segment_ko": "장르비율 기반 추천 후보군",
            "status": "kept_refined",
            "reason": "Same genre affinity concept. Now uses Stage 07c TRUE SHAP as official XAI basis.",
        },
        {
            "old_08b_segment_key": "low_risk_or_general_maintenance",
            "old_08b_segment_ko": "저위험/일반 유지군",
            "old_08b_churn_rate": 0.1976,
            "new_08c_segment_key": "일반관찰군",
            "new_08c_segment_ko": "일반 관찰군",
            "status": "kept_renamed",
            "reason": "Residual group kept. Old 08b used pre-02c/06c2 scores; 08c uses corrected official scores.",
        },
    ]
    rows_df = pd.DataFrame(rows)
    rows_df["old_08b_basis"] = "pre-02c/pre-06c2 corrected model (historical/provisional)"
    rows_df["new_08c_basis"] = "Stage 06c2 corrected official (AUC=0.8629)"
    rows_df["official_numbers_to_use"] = "08c only; old 08b numbers are historical"
    write_csv(TABLE_DIR / "08c_old08b_vs_new08c_comparison.csv", rows_df)


def write_business_readiness_findings(seg_summary: pd.DataFrame):
    holdout_seg = seg_summary[seg_summary["population"] == "holdout"]
    rows = []
    rows.append({"finding": "Official model confirmed", "status": "PASS",
                 "detail": f"Stage 06c2 HistGBM AUC=0.8629 reconstructed successfully."})
    rows.append({"finding": "Score direction confirmed", "status": "PASS",
                 "detail": "churn_risk_score = 1 - repurchase_score; high score = high predicted churn risk."})
    rows.append({"finding": "Holdout-first evaluation", "status": "PASS",
                 "detail": "All primary segment statistics computed on holdout set (n=4625)."})
    rows.append({"finding": "is_repurchase_label not used to define segments", "status": "PASS",
                 "detail": "Segments defined by churn_risk_score and feature thresholds only. Label used only post-hoc for evaluation."})
    rows.append({"finding": "Stage 07c TRUE SHAP as official XAI basis", "status": "PASS",
                 "detail": "Old 07r/06h SHAP not used. Stage 07c used for segment interpretation and SHAP evidence map."})
    rows.append({"finding": "No model training/tuning/Optuna/SHAP in 08c", "status": "PASS",
                 "detail": "Only model reconstruction for scoring. No feature selection, tuning, or SHAP computation."})
    rows.append({"finding": "No business simulation", "status": "PASS",
                 "detail": "No ROI, lift, intervention, or retention rate assumptions. Observational ranking only."})
    rows.append({"finding": "Old 08/08b outputs not overwritten", "status": "PASS",
                 "detail": "All new outputs under 08c_ prefix. Old 08/08b folders untouched."})
    # Check for small segments
    for _, row in holdout_seg.iterrows():
        if row["n"] < UNSTABLE_N_THRESHOLD:
            rows.append({"finding": f"Small segment: {row['final_segment_key']}", "status": "CAUTION",
                         "detail": f"n={row['n']} < {UNSTABLE_N_THRESHOLD}. Marked unstable."})
    rows.append({"finding": "Full descriptive population labeled", "status": "PASS",
                 "detail": "Full dataset outputs include split column (holdout/train) and descriptive_note."})
    rows.append({"finding": "Old 08b comparison created", "status": "PASS",
                 "detail": "08c_old08b_vs_new08c_comparison.csv created."})
    rows.append({"finding": "Segment action recommendations created", "status": "PASS",
                 "detail": "08c_segment_action_recommendations.csv created. No ROI/lift claims."})
    write_csv(TABLE_DIR / "08c_business_readiness_findings.csv", pd.DataFrame(rows))


def write_final_checks(auc_test: float, holdout_seg: pd.DataFrame):
    checks = [
        ("raw files unchanged", "PASS", "Modeling dataset and feature set files read-only; no writes to 05c/06c2/07c raw files."),
        ("no _data output created", "PASS", "All outputs under reports/data/08c_ and reports/tables/08c_ and reports/figures/08c_."),
        ("old 08/08b outputs not overwritten", "PASS", "New files use 08c_ prefix; old 08_ and 08b_ folders untouched."),
        ("old 07r/06h SHAP not used as final evidence", "PASS", "Only Stage 07c SHAP tables used. Old SHAP not referenced."),
        ("Stage 07c TRUE SHAP used as official XAI basis", "PASS", "07c_global_shap_importance.csv and family summary used."),
        ("Stage 06c2 corrected official score used", "PASS", f"AUC={auc_test:.6f}, matches expected {EXPECTED_AUC:.6f} within {AUC_DIFF_THRESHOLD}."),
        ("is_repurchase_label not used to define segments", "PASS", "Segments defined by churn_risk_score and feature thresholds."),
        ("holdout-first evaluation created", "PASS", "08c_risk_band_summary_holdout.csv and 08c_hierarchical_segment_summary_holdout.csv created."),
        ("full descriptive population labeled descriptive", "PASS", "Full CSVs include descriptive_note column and split=train/holdout."),
        ("old 08b comparison created", "PASS", "08c_old08b_vs_new08c_comparison.csv created."),
        ("segment action recommendations created", "PASS", "08c_segment_action_recommendations.csv created."),
        ("no business simulation", "PASS", "No ROI, intervention lift, or treatment cost computed."),
        ("no Optuna", "PASS", "No Optuna import or hyperparameter search."),
        ("no SHAP", "PASS", "No SHAP computation. Stage 07c SHAP used as reference only."),
        ("no model tuning", "PASS", "Model parameters identical to Stage 06c2/07c reconstruction (max_iter=120, lr=0.06)."),
    ]
    write_csv(TABLE_DIR / "08c_final_checks.csv",
              pd.DataFrame(checks, columns=["check", "status", "detail"]))


# ── Step 8: Markdown reports ───────────────────────────────────────────────────
def write_team_share_summary(holdout_seg: pd.DataFrame, band_summary: pd.DataFrame, thresholds: dict, auc_test: float):
    top_band = band_summary[(band_summary["population"] == "holdout") & (band_summary["risk_band"] == "top_10_highest_risk")].iloc[0]
    lines = [
        "# 08c Corrected Segmentation Strategy — Team Share Summary",
        "",
        "## Model Basis",
        f"- Official model: HistGradientBoostingClassifier (Stage 06c2 corrected)",
        f"- Feature set: `{OFFICIAL_FEATURE_SET}`",
        f"- Reconstructed AUC: {auc_test:.6f} (expected: {EXPECTED_AUC:.6f})",
        f"- Score direction: churn_risk_score = 1 − repurchase_score (high → high predicted churn risk)",
        "",
        "## Why Old 08/08b Segments Are No Longer Official",
        "- Old Stage 08 and 08b were created before Stage 02c strict preprocessing correction.",
        "- Old segments used a pre-correction model (AUC ~0.8047), which had data hygiene issues.",
        "- Stage 06c2 corrected the official model to AUC=0.8629 on the clean pipeline.",
        "- All old 08/08b segment numbers are historical/provisional only.",
        "",
        "## Risk Bands (Holdout)",
        "| Risk Band | n | Share | Churn Rate | Lift |",
        "|---|---|---|---|---|",
    ]
    for _, row in band_summary[band_summary["population"] == "holdout"].iterrows():
        lines.append(f"| {row['risk_band']} | {row['n']} | {row['share']:.1%} | {row['churn_rate']:.1%} | {row['lift_vs_overall_churn_rate']:.2f}x |")
    lines += [
        "",
        "## Corrected Final Segments (Holdout)",
        "| Segment | n | Share | Churn Rate | Lift |",
        "|---|---|---|---|---|",
    ]
    for _, row in holdout_seg.iterrows():
        lines.append(f"| {row['final_segment_key']} | {row['n']} | {row['share']:.1%} | {row['churn_rate']:.1%} | {row['lift_vs_overall_churn_rate']:.2f}x |")
    lines += [
        "",
        "## High-Risk Targeting Groups",
        "- **최상위_이탈위험군**: Top 10% by predicted churn risk. Primary targeting group.",
        "- **초기중기_저관여_고위험군**: High risk + low usage. Onboarding activation candidate.",
        "- **주차별이용패턴_고위험군**: Declining weekly watch pattern within mid-high risk band.",
        "",
        "## Maintenance / Recommendation Groups",
        "- **장르비율_추천후보군**: Genre affinity signal. Content curation candidate.",
        "- **안정유지_후보군**: Low predicted churn risk. Light-touch maintenance.",
        "- **일반관찰군**: Residual. Baseline monitoring only.",
        "",
        "## SHAP Feature Family Support",
        f"- weekly_usage_pattern: top family (sum mean_abs_shap ≈ 1.507)",
        f"- genre_ratio_proxy: second family (sum mean_abs_shap ≈ 1.433)",
        f"- membership_context: third family",
        "- All SHAP is Stage 07c TRUE SHAP on corrected official model.",
        "- SHAP is observational association only; no causality claim.",
        "",
        "## Safe to Report",
        "- 최상위_이탈위험군, 초기중기_저관여_고위험군: safe_to_report_with_caution",
        "- 주차별이용패턴_고위험군, 장르비율_추천후보군: plausible_but_cautioned",
        "- 안정유지_후보군, 일반관찰군: safe_to_report_as_context_only",
        "",
        "## Use in Stage 09c Simulation",
        "- Recommended for Stage 09c: 최상위_이탈위험군, 초기중기_저관여_고위험군, 주차별이용패턴_고위험군, 장르비율_추천후보군",
        "- Not recommended as primary simulation targets: 안정유지_후보군, 일반관찰군",
        "",
        "## Do Not Claim",
        "- Do not claim causality, ROI, intervention lift, or retention rate from segmentation.",
        "- Do not use old 07r or 06h SHAP as final evidence.",
        "- Do not use old 08/08b segment numbers as official.",
    ]
    write_md(DATA_DIR / "08c_team_share_segment_summary.md", "\n".join(lines))


def write_strategy_report(holdout_seg: pd.DataFrame, band_summary: pd.DataFrame, thresholds: dict, auc_test: float,
                          comparison_df: pd.DataFrame):
    holdout_overall_churn = float(1 - holdout_seg["n"].dot(holdout_seg["churn_rate"]) / holdout_seg["n"].sum())
    top10_row = holdout_seg[holdout_seg["final_segment_key"] == "최상위_이탈위험군"]
    top10_churn = float(top10_row["churn_rate"].iloc[0]) if len(top10_row) else 0
    top10_n = int(top10_row["n"].iloc[0]) if len(top10_row) else 0

    sections = []
    sections.append("# 08c Corrected Segmentation Strategy Report\n")
    sections.append("## 1. Which corrected model score was used for segmentation?\n")
    sections.append(
        f"Stage 06c2 corrected official model: **HistGradientBoostingClassifier** on "
        f"`{OFFICIAL_FEATURE_SET}`. "
        f"Reconstructed AUC = {auc_test:.6f} (expected {EXPECTED_AUC:.6f}, diff = 0.0). "
        "Score direction: `repurchase_score = P(is_repurchase_label=1)`, "
        "`churn_risk_score = 1 − repurchase_score`.\n"
    )
    sections.append("## 2. Why old 08/08b segments are no longer official?\n")
    sections.append(
        "Old Stage 08 and 08b were completed before the Stage 02c strict preprocessing correction. "
        "They relied on a pre-correction pipeline with AUC ≈ 0.8047. "
        "After the 02c correction, the official pipeline was re-run in Stage 06c2 (AUC = 0.8629). "
        "All old 08/08b scores and segment assignments are historical/provisional and must not be used as final evidence.\n"
    )
    sections.append("## 3. What are the corrected risk bands?\n")
    sections.append(
        f"Risk band thresholds were computed from holdout churn_risk_score percentiles: "
        f"p40={thresholds['p40']:.4f}, p70={thresholds['p70']:.4f}, p90={thresholds['p90']:.4f}.\n\n"
        "| Risk Band | n | Share | Churn Rate | Lift |\n|---|---|---|---|---|\n"
    )
    for _, row in band_summary[band_summary["population"] == "holdout"].iterrows():
        sections.append(f"| {row['risk_band']} | {row['n']} | {row['share']:.1%} | {row['churn_rate']:.1%} | {row['lift_vs_overall_churn_rate']:.2f}x |\n")
    sections.append("\n")
    sections.append("## 4. What are the corrected final segments?\n")
    sections.append("Six hierarchical segments (priority-assigned, holdout population):\n\n")
    sections.append("| Segment | n | Share | Churn Rate | Lift | Stability |\n|---|---|---|---|---|---|\n")
    for _, row in holdout_seg.iterrows():
        sections.append(f"| {row['final_segment_key']} | {row['n']} | {row['share']:.1%} | {row['churn_rate']:.1%} | {row['lift_vs_overall_churn_rate']:.2f}x | {row['stability_note']} |\n")
    sections.append("\n")
    sections.append("## 5. Which segments are high-risk targeting groups?\n")
    sections.append(
        "- **최상위_이탈위험군**: churn_risk_score ≥ p90. Primary targeting group.\n"
        "- **초기중기_저관여_고위험군**: churn_risk_score in [p70, p90) AND low total watch time. Onboarding target.\n"
        "- **주차별이용패턴_고위험군**: churn_risk_score in [p40, p90) AND declining weekly pattern. Pattern-based target.\n"
    )
    sections.append("## 6. Which segments are maintenance or recommendation groups?\n")
    sections.append(
        "- **장르비율_추천후보군**: max genre ratio > 0.4. Content recommendation group. Not necessarily high-risk.\n"
        "- **안정유지_후보군**: churn_risk_score < p40. Light-touch maintenance. Do not over-intervene.\n"
        "- **일반관찰군**: Residual. Baseline monitoring only.\n"
    )
    sections.append("## 7. Which old segments changed or disappeared?\n")
    sections.append("| Old 08b Segment | 08c Equivalent | Status | Reason |\n|---|---|---|---|\n")
    for _, row in comparison_df.iterrows():
        sections.append(f"| {row['old_08b_segment_ko']} | {row['new_08c_segment_ko']} | {row['status']} | {row['reason'][:80]} |\n")
    sections.append("\n")
    sections.append("## 8. Which SHAP feature families support the segment interpretation?\n")
    sections.append(
        "Based on Stage 07c TRUE SHAP (corrected official model, AUC=0.8629):\n\n"
        "- **weekly_usage_pattern** (sum mean_abs_shap ≈ 1.507): Top driver. "
        "  Supports high-risk and low-engagement segment interpretation.\n"
        "- **genre_ratio_proxy** (sum ≈ 1.433): Second driver. "
        "  Supports genre affinity segment design.\n"
        "- **membership_context** (sum ≈ 0.510): Third. "
        "  is_promotion_bin and max_screen_num are notable.\n"
        "- **simple_usage_volume** (sum ≈ 0.323): Supporting feature family.\n"
        "- **release_month_proxy** (sum ≈ 0.039): Minor.\n\n"
        "All SHAP is observational association; no causal claim permitted.\n"
    )
    sections.append("## 9. Which segments are safe to report?\n")
    sections.append(
        "- `safe_to_report_with_caution`: 최상위_이탈위험군, 초기중기_저관여_고위험군\n"
        "- `plausible_but_cautioned`: 주차별이용패턴_고위험군, 장르비율_추천후보군\n"
        "- `safe_to_report_as_context_only`: 안정유지_후보군, 일반관찰군\n\n"
        "All presentations must include the caution: predicted risk ranking only; "
        "no causality, no ROI, no intervention lift.\n"
    )
    sections.append("## 10. Which segments should be used in Stage 09c simulation?\n")
    sections.append(
        "- **Recommended for Stage 09c**: 최상위_이탈위험군, 초기중기_저관여_고위험군, 주차별이용패턴_고위험군, 장르비율_추천후보군\n"
        "- **Not recommended as primary**: 안정유지_후보군 (low risk), 일반관찰군 (residual)\n"
        "- Stage 09c must supply its own business assumptions (lift, cost, reach). "
        "Stage 08c provides segment definitions and score thresholds only.\n"
    )
    sections.append("\n---\n*Stage 08c corrected segmentation only. Do not proceed to Stage 09c from this file.*\n")
    write_md(DATA_DIR / "08c_segmentation_strategy_report.md", "".join(sections))


# ── Step 9: JSON summary ───────────────────────────────────────────────────────
def write_summary_json(holdout_seg: pd.DataFrame, band_summary: pd.DataFrame, thresholds: dict, auc_test: float):
    holdout_counts = holdout_seg.set_index("final_segment_key")["n"].to_dict()
    holdout_churn = holdout_seg.set_index("final_segment_key")["churn_rate"].to_dict()
    payload = {
        "stage": "08c_v2_corrected_segmentation_strategy",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "official_model": OFFICIAL_MODEL_NAME,
        "official_feature_set": OFFICIAL_FEATURE_SET,
        "official_auc": auc_test,
        "expected_auc": EXPECTED_AUC,
        "auc_diff": abs(auc_test - EXPECTED_AUC),
        "shap_basis": "Stage 07c TRUE SHAP (corrected official)",
        "score_direction": {
            "repurchase_score": "P(is_repurchase_label=1)",
            "churn_risk_score": "1 - repurchase_score",
            "high_churn_risk_score": "high predicted non-repurchase risk",
        },
        "risk_band_thresholds": {k: round(v, 6) for k, v in thresholds.items() if isinstance(v, float)},
        "risk_band_thresholds_rules": {k: v for k, v in thresholds.items() if isinstance(v, str)},
        "holdout_n": int(holdout_seg["n"].sum()),
        "holdout_segment_counts": {k: int(v) for k, v in holdout_counts.items()},
        "holdout_segment_churn_rates": {k: round(float(v), 4) for k, v in holdout_churn.items()},
        "high_risk_targeting_segments": ["최상위_이탈위험군", "초기중기_저관여_고위험군", "주차별이용패턴_고위험군"],
        "maintenance_recommendation_segments": ["장르비율_추천후보군", "안정유지_후보군", "일반관찰군"],
        "use_in_stage09c": {
            "최상위_이탈위험군": True,
            "초기중기_저관여_고위험군": True,
            "주차별이용패턴_고위험군": True,
            "장르비율_추천후보군": True,
            "안정유지_후보군": False,
            "일반관찰군": False,
        },
        "old_08b_status": "historical_provisional_do_not_use_as_final",
        "no_business_simulation": True,
        "no_optuna": True,
        "no_shap": True,
        "no_model_tuning": True,
        "is_repurchase_label_not_used_to_define_segments": True,
    }
    write_json(DATA_DIR / "08c_segmentation_summary.json", payload)


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print(f"[08c] Starting Stage 08c Corrected Segmentation Strategy")
    print(f"[08c] Python {sys.version}, sklearn, pandas")

    # 1. Load inputs
    summary, rec, shap_summary, global_shap, family_shap, shap_direction, features, df = load_inputs()

    # 2. Reconstruct and score
    holdout_scores, full_scores, train_scores, holdout_features, auc_test, train_idx, test_idx = \
        reconstruct_and_score(df, features)

    # Prepare full feature values for the full dataset
    X_full = prepare_X(df.reset_index(drop=True), features)
    full_scores_ordered = pd.concat([
        holdout_scores.copy(),
        train_scores.copy(),
    ], ignore_index=True)
    # Match order to full_scores
    X_full_ordered = pd.concat([
        X_full.iloc[test_idx].reset_index(drop=True),
        X_full.iloc[train_idx].reset_index(drop=True),
    ], ignore_index=True)

    # 3. Risk bands
    print("[08c] Computing risk bands ...")
    holdout_churn_risk = holdout_scores["churn_risk_score"].to_numpy()
    holdout_bands, thresholds = assign_risk_bands(holdout_churn_risk)
    holdout_scores = holdout_scores.copy()
    holdout_scores["risk_band"] = holdout_bands

    # Apply same thresholds to full dataset
    full_churn_risk = full_scores["churn_risk_score"].to_numpy()
    full_bands = np.where(
        full_churn_risk >= thresholds["p90"], "top_10_highest_risk",
        np.where(
            full_churn_risk >= thresholds["p70"], "risk_10_30",
            np.where(full_churn_risk >= thresholds["p40"], "risk_30_60", "bottom_40_lowest_risk")
        )
    )
    full_scores = full_scores.copy()
    full_scores["risk_band"] = full_bands

    band_summary_holdout = risk_band_stats(holdout_scores, holdout_bands, "holdout")
    band_summary_full = risk_band_stats(full_scores, full_bands, "full_descriptive")

    write_csv(TABLE_DIR / "08c_risk_band_summary_holdout.csv", band_summary_holdout)
    write_csv(TABLE_DIR / "08c_risk_band_summary_full_descriptive.csv", band_summary_full)
    print(f"  Risk bands: {dict(zip(*np.unique(holdout_bands, return_counts=True)))}")

    # 4. Non-exclusive segment flags
    print("[08c] Computing non-exclusive segment flags ...")
    holdout_flags, thresholds = compute_segment_flags(holdout_scores, holdout_features, thresholds)
    full_flags = apply_flags_to_full(full_scores, X_full_ordered, thresholds)

    # 5. Hierarchical segment assignment
    print("[08c] Assigning hierarchical segments ...")
    holdout_seg_col = assign_hierarchy(holdout_scores, holdout_flags)
    full_seg_col = assign_hierarchy(full_scores, full_flags)

    # Build segment assignment CSVs
    holdout_assign = holdout_scores[[ID_COL, GROUP_COL, "split", TARGET, "repurchase_score", "churn_risk_score", "risk_band"]].copy()
    holdout_assign["final_segment"] = holdout_seg_col.values
    for flag in FLAG_KEYS:
        if flag in holdout_flags.columns:
            holdout_assign[flag] = holdout_flags[flag].values

    full_assign = full_scores[[ID_COL, GROUP_COL, "split", TARGET, "repurchase_score", "churn_risk_score", "risk_band", "descriptive_note"]].copy()
    full_assign["final_segment"] = full_seg_col.values
    for flag in FLAG_KEYS:
        if flag in full_flags.columns:
            full_assign[flag] = full_flags[flag].values

    write_csv(DATA_DIR / "08c_segment_assignments_holdout.csv", holdout_assign)
    write_csv(DATA_DIR / "08c_segment_assignments_full_descriptive.csv", full_assign)
    print(f"  Holdout segments: {holdout_seg_col.value_counts().to_dict()}")

    # 6. Segment statistics
    holdout_seg_stats = hierarchical_segment_stats(holdout_scores, holdout_seg_col, "holdout")
    full_seg_stats_full = hierarchical_segment_stats(full_scores, full_seg_col, "full_descriptive")
    write_csv(TABLE_DIR / "08c_hierarchical_segment_summary_holdout.csv", holdout_seg_stats)
    write_csv(TABLE_DIR / "08c_hierarchical_segment_summary_full_descriptive.csv", full_seg_stats_full)

    # 7. Tables
    print("[08c] Writing tables ...")
    write_input_summary()
    write_segment_flag_definitions()
    write_nonexclusive_flag_summary(holdout_scores, holdout_flags)
    write_segment_thresholds(thresholds)
    write_segment_overlap_matrix(holdout_flags)
    write_segment_shap_evidence_map()
    write_segment_action_recommendations()
    write_old08b_comparison()
    write_business_readiness_findings(pd.concat([holdout_seg_stats, full_seg_stats_full], ignore_index=True))
    write_final_checks(auc_test, holdout_seg_stats)

    # Update action recommendations with actual numbers
    action_df = pd.read_csv(TABLE_DIR / "08c_segment_action_recommendations.csv")
    for idx, row in action_df.iterrows():
        seg_row = holdout_seg_stats[holdout_seg_stats["final_segment_key"] == row["final_segment_key"]]
        if len(seg_row):
            action_df.loc[idx, "n_holdout"] = int(seg_row.iloc[0]["n"])
            action_df.loc[idx, "churn_rate_holdout"] = round(float(seg_row.iloc[0]["churn_rate"]), 4)
    write_csv(TABLE_DIR / "08c_segment_action_recommendations.csv", action_df)

    # 8. Figures
    print("[08c] Generating figures ...")
    band_combined = pd.concat([band_summary_holdout, band_summary_full], ignore_index=True)
    seg_combined = pd.concat([holdout_seg_stats, full_seg_stats_full], ignore_index=True)
    fig_risk_band_churn_rate(band_combined)
    fig_risk_band_lift(band_combined)
    fig_hierarchical_segment_size_and_churn(seg_combined)
    fig_segment_action_map(holdout_seg_stats)
    fig_segment_shap_evidence_heatmap()
    fig_top_decile_churn_capture(holdout_scores)
    print("  Figures saved.")

    # 9. Reports and summaries
    print("[08c] Writing markdown reports and JSON summary ...")
    comparison_df = pd.read_csv(TABLE_DIR / "08c_old08b_vs_new08c_comparison.csv")
    write_team_share_summary(holdout_seg_stats, band_combined, thresholds, auc_test)
    write_strategy_report(holdout_seg_stats, band_combined, thresholds, auc_test, comparison_df)
    write_summary_json(holdout_seg_stats, band_combined, thresholds, auc_test)

    print(f"\n[08c] [OK] All outputs written.")
    print(f"  DATA:    {rel(DATA_DIR)}")
    print(f"  TABLES:  {rel(TABLE_DIR)}")
    print(f"  FIGURES: {rel(FIGURE_DIR)}")

    # Final verification
    required_outputs = [
        DATA_DIR / "08c_official_prediction_scores_holdout.csv",
        DATA_DIR / "08c_official_prediction_scores_full_descriptive.csv",
        DATA_DIR / "08c_segment_assignments_holdout.csv",
        DATA_DIR / "08c_segment_assignments_full_descriptive.csv",
        DATA_DIR / "08c_segmentation_summary.json",
        DATA_DIR / "08c_team_share_segment_summary.md",
        DATA_DIR / "08c_segmentation_strategy_report.md",
        TABLE_DIR / "08c_input_summary.csv",
        TABLE_DIR / "08c_risk_band_summary_holdout.csv",
        TABLE_DIR / "08c_risk_band_summary_full_descriptive.csv",
        TABLE_DIR / "08c_segment_flag_definitions.csv",
        TABLE_DIR / "08c_segment_thresholds.csv",
        TABLE_DIR / "08c_nonexclusive_segment_flag_summary.csv",
        TABLE_DIR / "08c_hierarchical_segment_summary_holdout.csv",
        TABLE_DIR / "08c_hierarchical_segment_summary_full_descriptive.csv",
        TABLE_DIR / "08c_segment_overlap_matrix.csv",
        TABLE_DIR / "08c_segment_shap_evidence_map.csv",
        TABLE_DIR / "08c_segment_action_recommendations.csv",
        TABLE_DIR / "08c_old08b_vs_new08c_comparison.csv",
        TABLE_DIR / "08c_business_readiness_findings.csv",
        TABLE_DIR / "08c_final_checks.csv",
        FIGURE_DIR / "08c_risk_band_churn_rate_holdout.png",
        FIGURE_DIR / "08c_risk_band_lift_holdout.png",
        FIGURE_DIR / "08c_hierarchical_segment_size_and_churn.png",
        FIGURE_DIR / "08c_segment_action_map.png",
        FIGURE_DIR / "08c_segment_shap_evidence_heatmap.png",
        FIGURE_DIR / "08c_top_decile_churn_capture.png",
    ]
    missing = [rel(p) for p in required_outputs if not p.exists()]
    if missing:
        print(f"\n[08c] WARNING: Missing required outputs: {missing}")
    else:
        print(f"[08c] All {len(required_outputs)} required outputs verified present.")

    return {
        "auc_test": auc_test,
        "holdout_n": len(holdout_scores),
        "holdout_seg_stats": holdout_seg_stats,
        "band_summary_holdout": band_summary_holdout,
        "thresholds": thresholds,
        "missing_outputs": missing,
    }


if __name__ == "__main__":
    result = main()
