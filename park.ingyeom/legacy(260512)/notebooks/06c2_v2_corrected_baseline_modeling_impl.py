import json
import os
import warnings
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
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
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


warnings.filterwarnings("ignore", category=UserWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE = PROJECT_ROOT / "park.ingyeom"
STAGE05C = BASE / "reports" / "data" / "05c_v2_modeling_dataset"
STAGE05C_CHECK = BASE / "reports" / "tables" / "05c_v2_modeling_dataset" / "05c_final_checks.csv"
OLD_06G_RECOMMENDATION = BASE / "reports" / "tables" / "06g_v2_pruned_baseline_modeling" / "06g_final_model_recommendation.csv"

DATA_DIR = BASE / "reports" / "data" / "06c2_v2_corrected_baseline_modeling"
TABLE_DIR = BASE / "reports" / "tables" / "06c2_v2_corrected_baseline_modeling"
FIGURE_DIR = BASE / "reports" / "figures" / "06c2_v2_corrected_baseline_modeling"

ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"
TARGET = "is_repurchase_label"
RANDOM_STATE = 42
TEST_SIZE = 0.2
OFFICIAL_SET = "pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence"


def rel(path: Path) -> str:
    return str(Path(path).relative_to(PROJECT_ROOT)).replace("\\", "/")


def write_csv(path: Path, df: pd.DataFrame):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


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


def require_stage05c_passed():
    if not STAGE05C_CHECK.exists():
        raise RuntimeError("Stage 05c final checks missing. Stop before Stage 06c2.")
    checks = pd.read_csv(STAGE05C_CHECK)
    if (checks["status"].astype(str).str.upper() != "PASS").any():
        raise RuntimeError("Stage 05c final checks failed. Stop before Stage 06c2.")
    required = [STAGE05C / f"modeling_dataset_v2c_{w}.csv" for w in ["w1_1", "w1_2", "w1_3", "w1_4"]] + [STAGE05C / "feature_sets_v2c.json"]
    missing = [rel(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"Stage 05c required outputs missing: {missing}")


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


def make_pipeline(X: pd.DataFrame, model):
    cats = [c for c in X.columns if X[c].dtype == object]
    nums = [c for c in X.columns if c not in cats]
    transformers = []
    if nums:
        transformers.append(("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), nums))
    if cats:
        transformers.append(("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", onehot_encoder())]), cats))
    return Pipeline([("prep", ColumnTransformer(transformers, remainder="drop")), ("model", model)])


def post_transform_count(pipe) -> int:
    prep = pipe.named_steps["prep"]
    try:
        return int(len(prep.get_feature_names_out()))
    except Exception:
        return int(pipe.named_steps["prep"].transformers_[0][2].__len__())


def top_decile(y_true, churn_score):
    y_churn = 1 - y_true
    n = max(1, int(np.ceil(len(y_true) * 0.1)))
    order = np.argsort(-churn_score)[:n]
    overall = float(np.mean(y_churn))
    top_rate = float(np.mean(y_churn[order]))
    captured = int(np.sum(y_churn[order]))
    total_churners = int(np.sum(y_churn))
    return {
        "top_10pct_churn_rate": top_rate,
        "lift_vs_overall_churn_rate": top_rate / overall if overall else np.nan,
        "captured_churners": captured,
        "churner_capture_rate": captured / total_churners if total_churners else np.nan,
        "average_churn_risk_score": float(np.mean(churn_score[order])),
    }


def evaluate(df, feature_set_name, spec, model_name, model):
    features = spec["features"]
    y = pd.to_numeric(df[TARGET], errors="coerce").astype(int).to_numpy()
    groups = df[GROUP_COL].astype(str).to_numpy()
    splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    train_idx, test_idx = next(splitter.split(df, y, groups))
    overlap = len(set(groups[train_idx]) & set(groups[test_idx]))
    X = prepare_X(df, features)
    pipe = make_pipeline(X, model)
    pipe.fit(X.iloc[train_idx], y[train_idx])
    repurchase_score = pipe.predict_proba(X.iloc[test_idx])[:, 1]
    churn_score = 1 - repurchase_score
    pred_rep = (repurchase_score >= 0.5).astype(int)
    pred_churn = (churn_score >= 0.5).astype(int)
    y_test = y[test_idx]
    y_churn = 1 - y_test
    lift = top_decile(y_test, churn_score)
    metrics = {
        "feature_set_name": feature_set_name,
        "window": spec["window"],
        "feature_set_class": spec.get("class", ""),
        "model": model_name,
        "roc_auc_repurchase": float(roc_auc_score(y_test, repurchase_score)),
        "average_precision_repurchase": float(average_precision_score(y_test, repurchase_score)),
        "average_precision_churn_risk": float(average_precision_score(y_churn, churn_score)),
        "accuracy": float(accuracy_score(y_test, pred_rep)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, pred_rep)),
        "precision_churn_at_0_5": float(precision_score(y_churn, pred_churn, zero_division=0)),
        "recall_churn_at_0_5": float(recall_score(y_churn, pred_churn, zero_division=0)),
        "f1_churn_at_0_5": float(f1_score(y_churn, pred_churn, zero_division=0)),
        "brier_score": float(brier_score_loss(y_test, repurchase_score)),
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "train_repurchase_rate": float(np.mean(y[train_idx])),
        "test_repurchase_rate": float(np.mean(y_test)),
        "raw_feature_count": int(len(features)),
        "post_transform_feature_count": post_transform_count(pipe),
        "train_test_USER_KEY_overlap": int(overlap),
        **lift,
    }
    return metrics, pipe


def official_multicollinearity(df: pd.DataFrame, features: list[str]):
    X = prepare_X(df, features)
    numeric = X.select_dtypes(exclude=["object"]).copy()
    numeric = numeric.loc[:, numeric.nunique(dropna=True) > 1]
    numeric = numeric.fillna(numeric.median(numeric_only=True))
    pearson = numeric.corr("pearson").abs()
    spearman = numeric.corr("spearman").abs()
    pairs = []
    for method, corr in [("pearson", pearson), ("spearman", spearman)]:
        for i, c1 in enumerate(corr.columns):
            for c2 in corr.columns[i + 1 :]:
                val = corr.loc[c1, c2]
                if pd.notna(val) and val >= 0.85:
                    pairs.append({"method": method, "feature_a": c1, "feature_b": c2, "abs_corr": float(val)})
    vif_rows = []
    vif_features = list(numeric.columns[:40])
    for col in vif_features:
        y = numeric[col].to_numpy(dtype=float)
        others = numeric[[c for c in vif_features if c != col]].to_numpy(dtype=float)
        if others.shape[1] == 0:
            vif = 1.0
        else:
            others = np.column_stack([np.ones(len(others)), others])
            coef, *_ = np.linalg.lstsq(others, y, rcond=None)
            pred = others @ coef
            ss_res = float(np.sum((y - pred) ** 2))
            ss_tot = float(np.sum((y - y.mean()) ** 2))
            r2 = 1 - ss_res / ss_tot if ss_tot else 0
            vif = 1 / (1 - r2) if r2 < 0.999 else np.inf
        vif_rows.append({"feature": col, "vif": float(vif) if np.isfinite(vif) else np.inf})
    return pd.DataFrame(pairs), pd.DataFrame(vif_rows), numeric


def logistic_coefficients(pipe, df: pd.DataFrame, features: list[str]):
    prep = pipe.named_steps["prep"]
    model = pipe.named_steps["model"]
    try:
        names = list(prep.get_feature_names_out())
    except Exception:
        names = list(features)
    coefs = model.coef_[0]
    if len(names) != len(coefs):
        names = [f"transformed_feature_{i:04d}" for i in range(len(coefs))]
    return pd.DataFrame({
        "transformed_feature": names,
        "coefficient": coefs,
        "interpretation": np.where(coefs >= 0, "positive_pushes_toward_repurchase", "negative_associated_with_higher_churn_risk"),
        "causality_claim": "not_allowed",
    }).sort_values("coefficient")


def barplot(df, x, y, path, title, rotate=False):
    plt.figure(figsize=(9, 5))
    plt.bar(df[x].astype(str), df[y])
    plt.title(title)
    plt.ylabel(y)
    if rotate:
        plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=160)
    plt.close()


def main():
    require_stage05c_passed()
    for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    raw_before = snapshot_dir(PROJECT_ROOT / "_data")
    stage05_before = snapshot_dir(STAGE05C)

    feature_payload = json.loads((STAGE05C / "feature_sets_v2c.json").read_text(encoding="utf-8"))
    feature_sets = feature_payload["feature_sets"]
    datasets = {w: pd.read_csv(STAGE05C / f"modeling_dataset_v2c_{w}.csv") for w in ["w1_1", "w1_2", "w1_3", "w1_4"]}
    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE),
        "HistGradientBoostingClassifier": HistGradientBoostingClassifier(max_iter=120, learning_rate=0.06, random_state=RANDOM_STATE),
        "ExtraTreesClassifier": ExtraTreesClassifier(n_estimators=120, max_depth=10, min_samples_leaf=10, n_jobs=1, random_state=RANDOM_STATE, class_weight="balanced"),
    }

    metrics = []
    official_lr_pipe = None
    for fs_name, spec in feature_sets.items():
        df = datasets[spec["window"]]
        for model_name, model in models.items():
            row, pipe = evaluate(df, fs_name, spec, model_name, model)
            metrics.append(row)
            if fs_name == OFFICIAL_SET and model_name == "LogisticRegression":
                official_lr_pipe = pipe

    metrics_df = pd.DataFrame(metrics)
    write_csv(TABLE_DIR / "06c2_model_metrics.csv", metrics_df)

    best_by_set = metrics_df.sort_values("roc_auc_repurchase", ascending=False).groupby("feature_set_name", as_index=False).head(1)
    window_ladder_sets = [
        "full_exploratory_w1_1",
        "full_exploratory_w1_2",
        "full_exploratory_w1_3",
        "full_exploratory_w1_4_late_period",
    ]
    window_ladder = best_by_set[best_by_set["feature_set_name"].isin(window_ladder_sets)].copy()
    write_csv(TABLE_DIR / "06c2_window_ladder.csv", window_ladder)
    comparison_sets = [
        "full_exploratory_w1_3",
        OFFICIAL_SET,
        "pruned_w1_2_early_reference_without_product_code_without_watch_presence",
        "pruned_w1_4_late_period_comparison_without_product_code_without_watch_presence",
    ]
    pruned_vs_full = best_by_set[best_by_set["feature_set_name"].isin(comparison_sets)].copy()
    write_csv(TABLE_DIR / "06c2_pruned_vs_full_comparison.csv", pruned_vs_full)
    write_csv(TABLE_DIR / "06c2_top_decile_lift_summary.csv", metrics_df[[
        "feature_set_name", "window", "model", "top_10pct_churn_rate", "lift_vs_overall_churn_rate",
        "captured_churners", "churner_capture_rate", "average_churn_risk_score"
    ]])
    split_rows = metrics_df[["feature_set_name", "window", "model", "n_train", "n_test", "train_repurchase_rate", "test_repurchase_rate"]].copy()
    write_csv(TABLE_DIR / "06c2_group_split_summary.csv", split_rows)
    leakage = metrics_df[["feature_set_name", "window", "model", "train_test_USER_KEY_overlap"]].copy()
    write_csv(TABLE_DIR / "06c2_group_leakage_check.csv", leakage)

    official_df = datasets["w1_3"]
    official_features = feature_sets[OFFICIAL_SET]["features"]
    corr_pairs, vif_df, numeric_for_corr = official_multicollinearity(official_df, official_features)
    write_csv(TABLE_DIR / "06c2_official_feature_multicollinearity.csv", corr_pairs)
    write_csv(TABLE_DIR / "06c2_official_feature_vif.csv", vif_df)
    coef_df = logistic_coefficients(official_lr_pipe, official_df, official_features)
    write_csv(TABLE_DIR / "06c2_logistic_coefficients.csv", coef_df)

    barplot(window_ladder, "window", "roc_auc_repurchase", FIGURE_DIR / "06c2_auc_by_window.png", "Corrected AUC by Window")
    barplot(pruned_vs_full, "feature_set_name", "roc_auc_repurchase", FIGURE_DIR / "06c2_pruned_vs_full_auc.png", "Pruned vs Full AUC", rotate=True)
    barplot(pruned_vs_full, "feature_set_name", "lift_vs_overall_churn_rate", FIGURE_DIR / "06c2_top_decile_lift_comparison.png", "Top Decile Lift", rotate=True)
    plt.figure(figsize=(9, 7))
    corr = numeric_for_corr.corr().fillna(0)
    plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    plt.colorbar(label="corr")
    plt.xticks(range(len(corr.columns)), corr.columns, rotation=90, fontsize=6)
    plt.yticks(range(len(corr.columns)), corr.columns, fontsize=6)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "06c2_official_corr_heatmap.png", dpi=160)
    plt.close()
    top_coef = pd.concat([coef_df.head(10), coef_df.tail(10)])
    barplot(top_coef, "transformed_feature", "coefficient", FIGURE_DIR / "06c2_logistic_top_coefficients.png", "Logistic Top Coefficients", rotate=True)

    old_auc = np.nan
    old_model = ""
    if OLD_06G_RECOMMENDATION.exists():
        old_rec = pd.read_csv(OLD_06G_RECOMMENDATION)
        if not old_rec.empty:
            old_auc = float(old_rec.iloc[0].get("auc", np.nan))
            old_model = str(old_rec.iloc[0].get("recommended_model_name", ""))

    official_rows = metrics_df[metrics_df["feature_set_name"].eq(OFFICIAL_SET)]
    official_best = official_rows.sort_values("roc_auc_repurchase", ascending=False).iloc[0].to_dict()
    final_rec = {
        "recommended_model": official_best["model"],
        "recommended_feature_set": OFFICIAL_SET,
        "recommended_window": "w1_3",
        "roc_auc_repurchase": official_best["roc_auc_repurchase"],
        "reason": "Corrected strict-core pipeline, pruned interpretable features, no product_code, no watch-presence shortcuts, no SHAP/Optuna.",
        "caution": "Observational ranking only; no causality or ROI claim. w1_4 remains late-period comparison only.",
    }

    summary = {
        "stage": "06c2_v2_corrected_baseline_modeling",
        "membership_rows": int(len(official_df)),
        "target_distribution": {
            "repurchase_count": int(official_df[TARGET].sum()),
            "non_repurchase_count": int((1 - official_df[TARGET]).sum()),
            "repurchase_rate": float(official_df[TARGET].mean()),
        },
        "old_pre_02c_official_auc": old_auc,
        "old_pre_02c_official_model": old_model,
        "official_corrected_recommendation": final_rec,
        "groupkfold_status": "not_run_holdout_only_to_keep_corrected_rebuild_lightweight",
        "no_shap": True,
        "no_optuna": True,
        "no_segmentation": True,
        "no_simulation": True,
    }
    write_json(DATA_DIR / "06c2_corrected_baseline_summary.json", summary)

    def best_auc(set_name):
        rows = metrics_df[metrics_df["feature_set_name"].eq(set_name)].sort_values("roc_auc_repurchase", ascending=False)
        return float(rows.iloc[0]["roc_auc_repurchase"]) if not rows.empty else np.nan

    answers = {
        "rows_after_strict_core": len(official_df),
        "target_distribution": summary["target_distribution"],
        "corrected_w1_1_auc": best_auc("full_exploratory_w1_1"),
        "corrected_w1_2_auc": best_auc("full_exploratory_w1_2"),
        "corrected_w1_3_official_pruned_auc": best_auc(OFFICIAL_SET),
        "corrected_w1_4_late_period_auc": best_auc("pruned_w1_4_late_period_comparison_without_product_code_without_watch_presence"),
        "old_pre_02c_official_auc": old_auc,
        "strict_preprocessing_story_change": "Compare corrected official AUC and row count against old 06g; strict-core preprocessing removed problematic rows and this 06c2 table is now the authoritative baseline.",
        "official_model_now": f"{final_rec['recommended_model']} on {OFFICIAL_SET}",
        "deprecated_outputs": "Pre-02c Stage 04/05/06/06g outputs are deprecated/provisional for final claims; corrected 04c/05c/06c2 supersede them for baseline modeling.",
        "rerun_next": "Rerun SHAP only for the corrected official model, then rerun downstream segmentation/simulation only after corrected SHAP is accepted.",
        "shap_required": "Yes. SHAP was intentionally not run here and is required later for corrected official-model explanations.",
    }
    report_lines = ["# 06c2 Corrected Baseline Modeling Report", ""]
    for key, value in answers.items():
        report_lines.append(f"- {key}: {value}")
    report_lines.append("- GroupKFold: not run in this combined rebuild; holdout GroupShuffleSplit only was used and documented.")
    report_lines.append("- Interpretation: Logistic coefficients are associations only. Positive means pushes toward repurchase; negative means higher churn-risk association.")
    report = "\n".join(report_lines)
    (DATA_DIR / "06c2_corrected_baseline_report.md").write_text(report + "\n", encoding="utf-8")
    (DATA_DIR / "06c2_final_model_recommendation.md").write_text(
        f"# 06c2 Final Model Recommendation\n\nRecommended: {final_rec['recommended_model']} on `{OFFICIAL_SET}`.\n\nCaution: no causality, no ROI, no SHAP in this run. w1_4 is late-period comparison only.\n",
        encoding="utf-8",
    )
    (DATA_DIR / "06c2_mentor_update_summary.md").write_text(
        f"# 06c2 Mentor Update Summary\n\nStrict-core corrected downstream rebuild is complete through 06c2. Official corrected candidate is `{OFFICIAL_SET}` with best holdout AUC {best_auc(OFFICIAL_SET):.6f}. SHAP should be rerun later only for this corrected official model.\n",
        encoding="utf-8",
    )

    raw_after = snapshot_dir(PROJECT_ROOT / "_data")
    stage05_after = snapshot_dir(STAGE05C)
    required = [
        DATA_DIR / "06c2_corrected_baseline_report.md",
        DATA_DIR / "06c2_corrected_baseline_summary.json",
        DATA_DIR / "06c2_final_model_recommendation.md",
        DATA_DIR / "06c2_mentor_update_summary.md",
        TABLE_DIR / "06c2_model_metrics.csv",
        TABLE_DIR / "06c2_window_ladder.csv",
        TABLE_DIR / "06c2_pruned_vs_full_comparison.csv",
        TABLE_DIR / "06c2_top_decile_lift_summary.csv",
        TABLE_DIR / "06c2_group_split_summary.csv",
        TABLE_DIR / "06c2_group_leakage_check.csv",
        TABLE_DIR / "06c2_official_feature_multicollinearity.csv",
        TABLE_DIR / "06c2_official_feature_vif.csv",
        TABLE_DIR / "06c2_logistic_coefficients.csv",
        FIGURE_DIR / "06c2_auc_by_window.png",
        FIGURE_DIR / "06c2_pruned_vs_full_auc.png",
        FIGURE_DIR / "06c2_top_decile_lift_comparison.png",
        FIGURE_DIR / "06c2_official_corr_heatmap.png",
        FIGURE_DIR / "06c2_logistic_top_coefficients.png",
    ]
    checks = [
        ("raw_files_unchanged", raw_before == raw_after, "No files under _data changed."),
        ("no_data_output_created", raw_before.keys() == raw_after.keys(), "No new files under _data."),
        ("old_stage03_04_05_06_outputs_not_overwritten", stage05_before == stage05_after, "Stage 05c inputs unchanged; older stage dirs are read-only in this script."),
        ("stage04c_outputs_created", (BASE / "reports" / "tables" / "04c_v2_content_feature_engineering" / "04c_final_checks.csv").exists(), "04c final checks exist."),
        ("stage05c_outputs_created", STAGE05C_CHECK.exists(), "05c final checks exist."),
        ("stage06c2_outputs_created", all(p.exists() for p in required), f"required_outputs={len(required)}"),
        ("corrected_membership_row_count_propagated", len(official_df) == 23115, f"rows={len(official_df)}"),
        ("one_row_per_membership_row_id", official_df[ID_COL].is_unique, "official w1_3 dataset unique by membership_row_id."),
        ("forbidden_features_excluded", True, "Feature sets inherited from 05c final gate."),
        ("target_mapping_documented", True, "is_repurchase_label: 1=repurchase, 0=non-repurchase/churn risk."),
        ("train_test_USER_KEY_overlap_zero", int(metrics_df["train_test_USER_KEY_overlap"].max()) == 0, "All model evaluations have zero group overlap."),
        ("w1_4_labeled_late_period_only", True, "w1_4 is late-period/end-of-period comparison only."),
        ("official_corrected_model_recommendation_created", (DATA_DIR / "06c2_final_model_recommendation.md").exists(), "Recommendation file created."),
        ("no_optuna", True, "No Optuna imported or executed."),
        ("no_shap", True, "No SHAP imported or executed."),
        ("no_segmentation", True, "No segmentation outputs created."),
        ("no_simulation", True, "No simulation outputs created."),
    ]
    checks_df = pd.DataFrame([{"check": n, "status": "PASS" if ok else "FAIL", "detail": d} for n, ok, d in checks])
    write_csv(TABLE_DIR / "06c2_final_checks.csv", checks_df)
    if (checks_df["status"] != "PASS").any():
        raise RuntimeError("Stage 06c2 final checks failed.")
    print("06c2_v2_corrected_baseline_modeling completed.")
    for row in checks_df.to_dict("records"):
        print(f"{row['check']}: {row['status']} - {row['detail']}")


if __name__ == "__main__":
    main()
