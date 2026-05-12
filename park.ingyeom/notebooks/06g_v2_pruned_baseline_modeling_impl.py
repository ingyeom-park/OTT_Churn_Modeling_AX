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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "park.ingyeom").exists() and (candidate / "_data").exists():
            return candidate
    raise FileNotFoundError("Project root not found.")


PROJECT_ROOT = find_root(Path.cwd())
BASE = PROJECT_ROOT / "park.ingyeom"
STAGE05E = BASE / "reports" / "data" / "05e_v2_final_feature_pruning_policy"
STAGE05E_TABLE = BASE / "reports" / "tables" / "05e_v2_final_feature_pruning_policy"
STAGE06 = BASE / "reports" / "data" / "06_v2_baseline_modeling"
STAGE06_TABLE = BASE / "reports" / "tables" / "06_v2_baseline_modeling"
STAGE06E = BASE / "reports" / "data" / "06e_v2_exact_early_window_rebuild"
STAGE06F = BASE / "reports" / "data" / "06f_v2_reduced_feature_baseline_audit"

DATA_DIR = BASE / "reports" / "data" / "06g_v2_pruned_baseline_modeling"
TABLE_DIR = BASE / "reports" / "tables" / "06g_v2_pruned_baseline_modeling"
FIGURE_DIR = BASE / "reports" / "figures" / "06g_v2_pruned_baseline_modeling"
for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"
TARGET = "is_repurchase"
RANDOM_STATE = 42


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
stage01_09_dirs = []
for base_dir in [BASE / "reports" / "data", BASE / "reports" / "tables", BASE / "reports" / "figures"]:
    if base_dir.exists():
        stage01_09_dirs.extend([p for p in base_dir.iterdir() if p.is_dir() and p.name != "06g_v2_pruned_baseline_modeling"])
stage_before = snapshot_dirs(stage01_09_dirs)
data_file_set_before = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())

df13 = pd.read_csv(STAGE05E / "modeling_dataset_v2_w1_3_pruned.csv")
df14 = pd.read_csv(STAGE05E / "modeling_dataset_v2_w1_4_pruned.csv")
pruned_payload = read_json(STAGE05E / "pruned_feature_sets_v2.json")
stage05e_summary = read_json(STAGE05E / "05e_feature_pruning_summary.json")
stage06e = read_json(STAGE06E / "06e_exact_early_window_summary.json")
stage06f = read_json(STAGE06F / "06f_reduced_feature_baseline_summary.json")
baseline_metrics = pd.read_csv(STAGE06 / "06_v2_model_metrics.csv")
split = pd.read_csv(STAGE06_TABLE / "06_v2_split_membership_row_ids.csv")
split_col = "split" if "split" in split.columns else "holdout_split"

for df in [df13, df14]:
    df["target_y"] = df[TARGET].map({"Y": 1, "N": 0})
    if df["target_y"].isna().any():
        raise ValueError("Target mapping failed.")

FORBIDDEN = set(pruned_payload.get("forbidden_features", [])) | {"target_y"}
CATEGORICAL = set(pruned_payload.get("categorical_features_to_encode_in_stage06", []))


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


def safe_auc(y, score):
    return float(roc_auc_score(y, score)) if len(np.unique(y)) > 1 else np.nan


def clean_features(df, features):
    return [f for f in features if f in df.columns and f not in FORBIDDEN]


def evaluate(set_name, spec, model_name):
    window = spec["window"]
    source = df13 if window == "w1_3" else df14
    features = clean_features(source, spec["features"])
    train_ids = set(split.loc[split[split_col].eq("train"), ID_COL])
    test_ids = set(split.loc[split[split_col].eq("test"), ID_COL])
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
    try:
        post_count = int(pipe.named_steps["preprocess"].transform(X_test.iloc[:1]).shape[1])
    except Exception:
        post_count = np.nan
    train_groups = set(source.loc[train_mask, GROUP_COL].dropna())
    test_groups = set(source.loc[test_mask, GROUP_COL].dropna())
    row = {
        "feature_set_name": set_name,
        "window": window,
        "model": model_name,
        "timing_label": spec["timing_label"],
        "product_code_policy": spec["product_code_policy"],
        "watch_presence_policy": spec["watch_presence_policy"],
        "claim_status": spec["claim_status"],
        "includes_product_code": "Y" if "product_code" in features else "N",
        "includes_watch_presence_flag": "Y" if any("has_watch_obs" in f or "no_watch_obs_flag" in f for f in features) else "N",
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
        "train_repurchase_rate": round(float(y_train.mean()), 6),
        "test_repurchase_rate": round(float(y_test.mean()), 6),
        "feature_count": int(len(features)),
        "post_transform_feature_count": post_count,
        "train_test_USER_KEY_overlap": int(len(train_groups & test_groups)),
    }
    scored = source.loc[test_mask, [ID_COL, GROUP_COL, TARGET, "target_y"]].copy()
    scored["feature_set_name"] = set_name
    scored["window"] = window
    scored["model"] = model_name
    scored["repurchase_score"] = repurchase_score
    scored["churn_risk_score"] = churn_score
    return row, scored


metric_rows = []
score_parts = []
for set_name, spec in pruned_payload["feature_sets"].items():
    for model_name in ["LogisticRegression", "HistGradientBoostingClassifier"]:
        row, scored = evaluate(set_name, spec, model_name)
        metric_rows.append(row)
        score_parts.append(scored)
metrics = pd.DataFrame(metric_rows)
scores = pd.concat(score_parts, ignore_index=True)
write_csv(TABLE_DIR / "06g_pruned_model_metrics.csv", metrics)
write_csv(DATA_DIR / "06g_pruned_prediction_scores.csv", scores)

decile_rows = []
for (set_name, model), g in scores.groupby(["feature_set_name", "model"]):
    ranked = g.sort_values("churn_risk_score", ascending=False)
    top_n = max(1, math.ceil(len(ranked) * 0.10))
    top = ranked.head(top_n)
    churn_true = 1 - ranked["target_y"]
    top_churn_true = 1 - top["target_y"]
    overall = float(churn_true.mean())
    top_rate = float(top_churn_true.mean())
    captured = int(top_churn_true.sum())
    total_churners = int(churn_true.sum())
    decile_rows.append({
        "feature_set_name": set_name,
        "model": model,
        "top_10pct_n": top_n,
        "overall_churn_rate": round(overall, 6),
        "top_10pct_churn_rate": round(top_rate, 6),
        "top_decile_lift_vs_overall": round(top_rate / overall, 6) if overall else np.nan,
        "captured_churners": captured,
        "total_churners": total_churners,
        "churner_capture_rate": round(captured / total_churners, 6) if total_churners else np.nan,
        "average_churn_risk_score": round(float(ranked["churn_risk_score"].mean()), 6),
        "average_churn_risk_score_top_decile": round(float(top["churn_risk_score"].mean()), 6),
    })
deciles = pd.DataFrame(decile_rows)
write_csv(TABLE_DIR / "06g_pruned_churn_risk_decile_summary.csv", deciles)

tradeoff = metrics.merge(deciles[["feature_set_name", "model", "top_decile_lift_vs_overall", "top_10pct_churn_rate"]], on=["feature_set_name", "model"], how="left")
tradeoff["interpretability_safety"] = tradeoff.apply(lambda r: "high" if r["timing_label"] == "early_safer_w1_3_proxy" and r["includes_product_code"] == "N" and r["includes_watch_presence_flag"] == "N" else "medium_high" if r["includes_product_code"] == "N" and r["includes_watch_presence_flag"] == "N" else "sensitivity_only", axis=1)
write_csv(TABLE_DIR / "06g_interpretability_performance_tradeoff.csv", tradeoff)

full_ref = stage06f.get("full_reference_w1_3_hgb_auc")
reduced_ref = stage06f.get("mentor_safe_hgb_auc")
exact_auc = stage06e.get("exact_auc_by_window", {})

hgb = metrics[metrics["model"].eq("HistGradientBoostingClassifier")].copy()
official_pool = hgb[
    hgb["window"].eq("w1_3")
    & hgb["includes_product_code"].eq("N")
    & hgb["includes_watch_presence_flag"].eq("N")
    & hgb["timing_label"].isin(["early_safer_w1_3_proxy", "timing_sensitive_w1_3", "early_cautioned_preference_proxy"])
].copy()
timing_rank = {"early_safer_w1_3_proxy": 0, "early_cautioned_preference_proxy": 1, "timing_sensitive_w1_3": 2}
official_pool["timing_rank"] = official_pool["timing_label"].map(timing_rank).fillna(9)
official_pool = official_pool.merge(deciles[["feature_set_name", "model", "top_decile_lift_vs_overall"]], on=["feature_set_name", "model"], how="left")
official_pool = official_pool.sort_values(["timing_rank", "roc_auc_repurchase", "top_decile_lift_vs_overall"], ascending=[True, False, False])
recommended = official_pool.iloc[0]

best_without_product = hgb[hgb["includes_product_code"].eq("N")].sort_values("roc_auc_repurchase", ascending=False).iloc[0]
best_with_product = hgb[hgb["includes_product_code"].eq("Y")].sort_values("roc_auc_repurchase", ascending=False).iloc[0]
best_without_decile = deciles[(deciles["feature_set_name"].eq(best_without_product["feature_set_name"])) & (deciles["model"].eq(best_without_product["model"]))].iloc[0]
best_with_decile = deciles[(deciles["feature_set_name"].eq(best_with_product["feature_set_name"])) & (deciles["model"].eq(best_with_product["model"]))].iloc[0]
product_code_collapse = (
    float(best_with_product["roc_auc_repurchase"]) - float(best_without_product["roc_auc_repurchase"]) > 0.05
    and float(best_with_decile["top_decile_lift_vs_overall"]) - float(best_without_decile["top_decile_lift_vs_overall"]) > 0.30
)

comparison_rows = [
    {"comparison_class": "full_exploratory_model", "auc": full_ref, "source": "06f full_reference_w1_3", "role": "exploratory upper bound, not official interpretation model"},
    {"comparison_class": "reduced_no_target_adjacent_timing", "auc": reduced_ref, "source": "06f reduced baseline", "role": "prior reduced diagnostic reference"},
    {"comparison_class": "exact_w1_2_early_window", "auc": exact_auc.get("w1_2"), "source": "06e exact early-window rebuild", "role": "mentor-safe early-window context"},
    {"comparison_class": "w1_4_late_period", "auc": exact_auc.get("w1_4"), "source": "06e exact early-window rebuild", "role": "late-period comparison only"},
]
for _, row in hgb.iterrows():
    comparison_rows.append({"comparison_class": "pruned_model", "auc": row["roc_auc_repurchase"], "source": row["feature_set_name"], "role": row["timing_label"]})
comparison = pd.DataFrame(comparison_rows)
write_csv(TABLE_DIR / "06g_pruned_vs_full_comparison.csv", comparison)

ladder = pd.DataFrame([
    {"level": "A_full_exploratory_w1_3", "auc": full_ref, "role": "full exploratory model", "claim_status": "exploratory_upper_bound_only"},
    {"level": "B_timing_sensitive_pruned_w1_3", "auc": float(hgb[hgb["timing_label"].eq("timing_sensitive_w1_3") & hgb["includes_product_code"].eq("N") & hgb["includes_watch_presence_flag"].eq("N")]["roc_auc_repurchase"].max()), "role": "timing-sensitive pruned w1_3", "claim_status": "presentation_with_timing_caveat"},
    {"level": "C_early_safer_pruned_w1_3", "auc": float(hgb[hgb["timing_label"].eq("early_safer_w1_3_proxy")]["roc_auc_repurchase"].max()), "role": "early-safer pruned w1_3 proxy", "claim_status": "mentor_safe"},
    {"level": "D_exact_w1_2", "auc": exact_auc.get("w1_2"), "role": "exact early-window context", "claim_status": "mentor_safe"},
    {"level": "E_late_period_w1_4", "auc": float(hgb[hgb["timing_label"].eq("late_period_only")]["roc_auc_repurchase"].max()), "role": "late-period comparison model", "claim_status": "do_not_claim_as_early_prediction"},
])
write_csv(TABLE_DIR / "06g_pruned_metric_ladder.csv", ladder)

rec_decile = deciles[(deciles["feature_set_name"].eq(recommended["feature_set_name"])) & (deciles["model"].eq(recommended["model"]))].iloc[0]
recommendation = pd.DataFrame([{
    "recommended_model_name": recommended["model"],
    "recommended_feature_set": recommended["feature_set_name"],
    "includes_product_code": recommended["includes_product_code"],
    "includes_watch_presence_flag": recommended["includes_watch_presence_flag"],
    "timing_label": recommended["timing_label"],
    "auc": recommended["roc_auc_repurchase"],
    "churn_risk_pr_auc": recommended["average_precision_churn_risk"],
    "top_decile_lift": rec_decile["top_decile_lift_vs_overall"],
    "feature_count": recommended["feature_count"],
    "reason": "Chosen by revised priority: no forbidden features, no product_code, no watch-presence shortcut, lower timing risk, reduced redundancy, then AUC and lift.",
    "caveat": "This is still observational churn-risk ranking, not causal proof. w1_3 timing-sensitive alternatives may score higher but carry timing caveats.",
    "presentation_wording": "공식 발표 모델은 product_code와 watch-presence shortcut을 제외한 pruned 모델이며, 조기 안전성과 해석 가능성을 성능보다 우선했다.",
    "mentor_wording": "멘토님 지적 이후 full model은 탐색적 상한선으로 분리하고, product memorization과 watch-presence shortcut을 제외한 보수적 pruned 모델을 공식 후보로 선택했다.",
    "product_code_collapse_rule_triggered": "Y" if product_code_collapse else "N",
}])
write_csv(TABLE_DIR / "06g_final_model_recommendation.csv", recommendation)


def save_bar(path, df_plot, x, y, title, ylabel):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df_plot[x], df_plot[y], color="#4C78A8")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=35)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


plot_hgb = hgb.sort_values("roc_auc_repurchase", ascending=False)
save_bar(FIGURE_DIR / "06g_pruned_auc_comparison.png", plot_hgb, "feature_set_name", "roc_auc_repurchase", "Pruned AUC Comparison", "ROC AUC")

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(plot_hgb["feature_count"], plot_hgb["roc_auc_repurchase"], color="#59A14F")
for _, r in plot_hgb.iterrows():
    ax.text(r["feature_count"] + 0.2, r["roc_auc_repurchase"], r["feature_set_name"].replace("pruned_", ""), fontsize=7)
ax.set_xlabel("Feature count")
ax.set_ylabel("ROC AUC")
ax.set_title("Feature Count vs AUC, Pruned")
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(FIGURE_DIR / "06g_feature_count_vs_auc_pruned.png", dpi=160)
plt.close(fig)

save_bar(FIGURE_DIR / "06g_pruned_metric_ladder.png", ladder, "level", "auc", "Pruned Metric Ladder", "ROC AUC")

lift_plot = deciles[deciles["model"].eq("HistGradientBoostingClassifier")].sort_values("top_decile_lift_vs_overall", ascending=False)
save_bar(FIGURE_DIR / "06g_top_decile_lift_pruned.png", lift_plot, "feature_set_name", "top_decile_lift_vs_overall", "Top Decile Lift, Pruned", "Lift")

report_lines = [
    "# 06g v2 Pruned Baseline Modeling Report",
    "",
    "## Result Classes",
    f"- Full exploratory model: AUC {full_ref:.6f}; use only as exploratory upper bound.",
    f"- Timing-sensitive pruned w1_3 model: best no-product/no-presence AUC {ladder.loc[ladder['level'].eq('B_timing_sensitive_pruned_w1_3'), 'auc'].iloc[0]:.6f}; usable only with timing caveat.",
    f"- Early-safer pruned w1_3 or exact w1_2: pruned early-safer AUC {ladder.loc[ladder['level'].eq('C_early_safer_pruned_w1_3'), 'auc'].iloc[0]:.6f}; exact w1_2 AUC {exact_auc.get('w1_2'):.6f}.",
    f"- Late-period w1_4 comparison model: AUC {ladder.loc[ladder['level'].eq('E_late_period_w1_4'), 'auc'].iloc[0]:.6f}; not early prediction.",
    "",
    "## Final Recommendation",
    f"- Recommended model: `{recommended['model']}`.",
    f"- Recommended feature set: `{recommended['feature_set_name']}`.",
    f"- AUC: {recommended['roc_auc_repurchase']:.6f}.",
    f"- Churn-risk PR AUC: {recommended['average_precision_churn_risk']:.6f}.",
    f"- Top-decile lift: {rec_decile['top_decile_lift_vs_overall']:.6f}.",
    f"- Feature count: {int(recommended['feature_count'])}.",
    "- Reason: selected by safety priority before performance.",
    "",
    "## Answers",
    f"1. Best pruned w1_3 model by AUC: `{plot_hgb[plot_hgb['window'].eq('w1_3')].iloc[0]['feature_set_name']}`.",
    f"2. Most interpretable pruned model: `{recommended['feature_set_name']}` under the revised priority order.",
    f"3. AUC loss versus full w1_3 exploratory model: {float(full_ref) - float(recommended['roc_auc_repurchase']):.6f}.",
    "4. Pruning reduces redundancy by removing totals with weekly variables, ratios, deltas, content volume proxies, and default product/watch-presence shortcuts.",
    f"5. Pruning preserves useful ranking: recommended top-decile lift {rec_decile['top_decile_lift_vs_overall']:.6f}.",
    f"6. Official final presentation candidate: `{recommended['feature_set_name']}`.",
    "7. Full model results should be treated as exploratory upper bounds.",
    "8. Removed derived/original duplication: total_watch_time, ratios, deltas, coverage complements.",
    "9. Removed target-adjacent features: first/last watch rel day and default watch-presence shortcut.",
    "10. Removed content-volume usage proxies: genre watch_time and genre session_count.",
    "11. Mentor wording is in the final recommendation table and markdown.",
]
(DATA_DIR / "06g_pruned_baseline_modeling_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

mentor_lines = [
    "# 06g 최종 pruned 모델 멘토 대응 문안",
    "",
    f"최종 후보는 `{recommended['feature_set_name']}`입니다.",
    f"- AUC: {recommended['roc_auc_repurchase']:.6f}",
    f"- churn-risk PR AUC: {recommended['average_precision_churn_risk']:.6f}",
    f"- top-decile lift: {rec_decile['top_decile_lift_vs_overall']:.6f}",
    f"- product_code 포함 여부: {recommended['includes_product_code']}",
    f"- watch-presence flag 포함 여부: {recommended['includes_watch_presence_flag']}",
    f"- timing label: {recommended['timing_label']}",
    "",
    "멘토님께는 full model의 높은 AUC를 공식 조기예측 성능으로 주장하지 않고, product_code와 watch-presence shortcut을 제외한 pruned 모델을 공식 후보로 제시하겠다고 설명합니다.",
]
(DATA_DIR / "06g_final_pruned_model_recommendation.md").write_text("\n".join(mentor_lines) + "\n", encoding="utf-8")

summary = {
    "stage": "06g_v2_pruned_baseline_modeling",
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "python": platform.python_version(),
    "target_mapping": "Y -> 1 repurchase; N -> 0 non-repurchase/churn risk",
    "split_file": rel(STAGE06_TABLE / "06_v2_split_membership_row_ids.csv"),
    "train_test_USER_KEY_overlap_max": int(metrics["train_test_USER_KEY_overlap"].max()),
    "recommended_feature_set": str(recommended["feature_set_name"]),
    "recommended_model": str(recommended["model"]),
    "recommended_auc": float(recommended["roc_auc_repurchase"]),
    "recommended_churn_risk_pr_auc": float(recommended["average_precision_churn_risk"]),
    "recommended_top_decile_lift": float(rec_decile["top_decile_lift_vs_overall"]),
    "recommended_includes_product_code": str(recommended["includes_product_code"]),
    "recommended_includes_watch_presence_flag": str(recommended["includes_watch_presence_flag"]),
    "recommended_timing_label": str(recommended["timing_label"]),
    "product_code_collapse_rule_triggered": bool(product_code_collapse),
    "result_classes_separated": ["full_exploratory_model", "timing_sensitive_pruned_w1_3", "early_safer_pruned_or_exact_w1_2", "late_period_w1_4_comparison"],
}
write_json(DATA_DIR / "06g_pruned_baseline_summary.json", summary)

raw_after = snapshot_dirs([PROJECT_ROOT / "_data"])
stage_after = snapshot_dirs(stage01_09_dirs)
data_file_set_after = set(rel(p) for p in (PROJECT_ROOT / "_data").rglob("*") if p.is_file())
required_outputs = [
    TABLE_DIR / "06g_pruned_model_metrics.csv",
    TABLE_DIR / "06g_pruned_churn_risk_decile_summary.csv",
    TABLE_DIR / "06g_pruned_metric_ladder.csv",
    TABLE_DIR / "06g_pruned_vs_full_comparison.csv",
    TABLE_DIR / "06g_interpretability_performance_tradeoff.csv",
    TABLE_DIR / "06g_final_model_recommendation.csv",
    DATA_DIR / "06g_pruned_baseline_modeling_report.md",
    DATA_DIR / "06g_pruned_baseline_summary.json",
    DATA_DIR / "06g_final_pruned_model_recommendation.md",
    FIGURE_DIR / "06g_pruned_auc_comparison.png",
    FIGURE_DIR / "06g_feature_count_vs_auc_pruned.png",
    FIGURE_DIR / "06g_pruned_metric_ladder.png",
    FIGURE_DIR / "06g_top_decile_lift_pruned.png",
]
checks = [
    {"check": "raw files unchanged", "status": "PASS" if raw_before == raw_after else "FAIL", "evidence": "Compared _data snapshots."},
    {"check": "no _data output created", "status": "PASS" if data_file_set_before == data_file_set_after else "FAIL", "evidence": "Compared _data file set."},
    {"check": "Stage 01 through Stage 09 outputs not overwritten", "status": "PASS" if stage_before == stage_after else "FAIL", "evidence": "Compared non-06g artifact snapshots."},
    {"check": "Stage 06 split reused", "status": "PASS", "evidence": rel(STAGE06_TABLE / "06_v2_split_membership_row_ids.csv")},
    {"check": "USER_KEY train/test overlap is 0", "status": "PASS" if int(metrics["train_test_USER_KEY_overlap"].max()) == 0 else "FAIL", "evidence": str(int(metrics["train_test_USER_KEY_overlap"].max()))},
    {"check": "forbidden features excluded", "status": "PASS" if not any(f in FORBIDDEN for spec in pruned_payload["feature_sets"].values() for f in spec["features"]) else "FAIL", "evidence": "Checked feature sets."},
    {"check": "target mapping documented", "status": "PASS", "evidence": "Y -> 1; N -> 0."},
    {"check": "w1_3/w1_4 separated", "status": "PASS" if all((spec["window"] == "w1_3" and not any(f.startswith("w1_4_") for f in spec["features"])) or (spec["window"] == "w1_4" and not any(f.startswith("w1_3_") for f in spec["features"])) for spec in pruned_payload["feature_sets"].values()) else "FAIL", "evidence": "Checked prefixes."},
    {"check": "w1_4 labeled late-period only", "status": "PASS" if all(spec["timing_label"] == "late_period_only" for spec in pruned_payload["feature_sets"].values() if spec["window"] == "w1_4") else "FAIL", "evidence": "Checked metadata."},
    {"check": "pruned baseline models evaluated", "status": "PASS" if len(metrics) >= len(pruned_payload["feature_sets"]) * 2 else "FAIL", "evidence": str(len(metrics))},
    {"check": "no Optuna run", "status": "PASS", "evidence": "No optuna import or tuning loop."},
    {"check": "no SHAP run", "status": "PASS", "evidence": "No shap import or SHAP computation."},
    {"check": "no segmentation created", "status": "PASS", "evidence": "No segmentation outputs."},
    {"check": "no business simulation created", "status": "PASS", "evidence": "No simulation outputs."},
    {"check": "final recommendation follows revised priority order", "status": "PASS" if recommended["includes_product_code"] == "N" and recommended["includes_watch_presence_flag"] == "N" else "FAIL", "evidence": str(recommended["feature_set_name"])},
    {"check": "full, timing-sensitive, early-safer, and late-period results are separated", "status": "PASS" if set(summary["result_classes_separated"]) == {"full_exploratory_model", "timing_sensitive_pruned_w1_3", "early_safer_pruned_or_exact_w1_2", "late_period_w1_4_comparison"} else "FAIL", "evidence": "|".join(summary["result_classes_separated"])},
    {"check": "final pruned model recommendation created", "status": "PASS" if (TABLE_DIR / "06g_final_model_recommendation.csv").exists() else "FAIL", "evidence": rel(TABLE_DIR / "06g_final_model_recommendation.csv")},
    {"check": "mentor-facing wording created", "status": "PASS" if (DATA_DIR / "06g_final_pruned_model_recommendation.md").exists() else "FAIL", "evidence": rel(DATA_DIR / "06g_final_pruned_model_recommendation.md")},
]
for path in required_outputs:
    checks.append({"check": f"required output exists: {path.name}", "status": "PASS" if path.exists() else "FAIL", "evidence": rel(path)})
final_checks = pd.DataFrame(checks)
write_csv(TABLE_DIR / "06g_final_checks.csv", final_checks)
summary["final_checks_path"] = rel(TABLE_DIR / "06g_final_checks.csv")
summary["final_check_status"] = "PASS" if (final_checks["status"] == "PASS").all() else "FAIL"
write_json(DATA_DIR / "06g_pruned_baseline_summary.json", summary)

print(json.dumps({
    "stage": "06g",
    "final_check_status": summary["final_check_status"],
    "recommended_feature_set": summary["recommended_feature_set"],
    "recommended_auc": summary["recommended_auc"],
    "recommended_top_decile_lift": summary["recommended_top_decile_lift"],
}, ensure_ascii=False, indent=2))
