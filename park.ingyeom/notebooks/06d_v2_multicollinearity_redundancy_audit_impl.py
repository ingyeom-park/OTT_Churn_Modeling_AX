import json
import math
import os
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import chi2_contingency


os.environ.setdefault("PYTHONIOENCODING", "utf-8")

TARGET = "is_repurchase"
ID_COL = "membership_row_id"
GROUP_COL = "USER_KEY"
PRIMARY_FEATURE_SET = "membership_plus_usage_content_w1_3_without_churn_prevented"

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

MEMBERSHIP_FEATURES = {
    "price",
    "product_code",
    "max_screen",
    "is_promotion",
    "is_user_verified",
    "gender",
    "age",
    "payment_device",
    "billing_method",
    "is_churn_prevented",
}


def find_project_root(start):
    for candidate in [start, *start.parents]:
        if (
            (
                (candidate / "_data" / "01_raw" / "Membership.csv").exists()
                or (candidate / "_data" / "01_raw" / "Membership_train.csv").exists()
            )
            and (
                candidate
                / "park.ingyeom"
                / "reports"
                / "data"
                / "05_v2_modeling_dataset"
                / "feature_sets_v2.json"
            ).exists()
        ):
            return candidate
    raise FileNotFoundError("Could not locate ott-churn-prediction project root.")


PROJECT_ROOT = find_project_root(Path.cwd())
STAGE05_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "05_v2_modeling_dataset"
STAGE06_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "06_v2_baseline_modeling"
STAGE06C_DATA = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "06c_v2_overfitting_leakage_adversarial_audit"
STAGE07R_TABLES = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "07r_v2_true_shap_interpretation"

DATA_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "data" / "06d_v2_multicollinearity_redundancy_audit"
TABLE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "tables" / "06d_v2_multicollinearity_redundancy_audit"
FIGURE_DIR = PROJECT_ROOT / "park.ingyeom" / "reports" / "figures" / "06d_v2_multicollinearity_redundancy_audit"
for directory in [DATA_DIR, TABLE_DIR, FIGURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

RAW_FILES = [
    PROJECT_ROOT / "_data" / "01_raw" / name
    for name in [
        "Membership.csv",
        "User_Mapping.csv",
        "View_History.csv",
        "Movie_Master.csv",
        "Membership_train.csv",
        "mapping.csv",
        "Views_train.csv",
        "Movies.csv",
    ]
]

STAGE01_09_PREFIXES = [
    "01_v2_data_overview_and_audit",
    "02_v2_preprocessing_policy",
    "02_v2_preprocessing_policy_validation",
    "03_v2_usage_feature_engineering",
    "04_v2_content_feature_engineering",
    "04_v2_content_feature_feasibility",
    "05_v2_modeling_dataset",
    "06_v2_baseline_modeling",
    "06b_v2_baseline_sanity_audit",
    "07_v2_xai_shap_interpretation",
    "07r_v2_true_shap_interpretation",
    "08_v2_segmentation_strategy",
    "08b_v2_segmentation_refinement",
    "09_v2_business_simulation",
]


def rel(path):
    return str(Path(path).resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")


def snapshot_paths(paths):
    out = {}
    for path in paths:
        path = Path(path)
        if path.exists() and path.is_file():
            stat = path.stat()
            out[rel(path)] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    return out


def snapshot_dirs(dirs):
    out = {}
    for directory in dirs:
        directory = Path(directory)
        if directory.exists():
            for path in directory.rglob("*"):
                if path.is_file():
                    stat = path.stat()
                    out[rel(path)] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    return out


def snapshot_stage01_09():
    out = {}
    for base_name in ["data", "tables", "figures"]:
        base = PROJECT_ROOT / "park.ingyeom" / "reports" / base_name
        for prefix in STAGE01_09_PREFIXES:
            out |= snapshot_dirs([base / prefix])
    return out


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path, obj):
    if isinstance(obj, pd.DataFrame):
        obj.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame(obj).to_csv(path, index=False, encoding="utf-8-sig")


def detect_family(col):
    if col == TARGET:
        return "target"
    if col in [ID_COL, GROUP_COL] or col in FORBIDDEN_FEATURES:
        return "metadata"
    if col in MEMBERSHIP_FEATURES:
        return "membership"
    if "release_month" in col or "recent_content" in col or "old_content" in col:
        return "release_month"
    if "genre_" in col or "top_genre" in col:
        return "genre"
    if "content_" in col or "covered" in col or "missing" in col:
        return "content"
    if col.startswith("w1_"):
        return "usage"
    return "unknown"


def detect_type(series, col):
    if col in [ID_COL, GROUP_COL] or col in FORBIDDEN_FEATURES:
        return "metadata" if col != TARGET else "target"
    if series.dtype == "object":
        return "categorical"
    vals = set(pd.Series(series.dropna().unique()).head(10).tolist())
    if vals.issubset({0, 1, 0.0, 1.0}):
        return "boolean"
    return "numeric"


def numeric_cols(df, cols):
    return [c for c in cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c]) and df[c].nunique(dropna=True) > 1]


def cramers_v(x, y):
    xs = x.astype("object").where(x.notna(), "__MISSING__").astype(str)
    ys = y.astype("object").where(y.notna(), "__MISSING__").astype(str)
    table = pd.crosstab(xs, ys)
    if table.empty or min(table.shape) < 2:
        return np.nan
    chi2 = chi2_contingency(table, correction=False)[0]
    n = table.to_numpy().sum()
    r, k = table.shape
    denom = n * (min(k - 1, r - 1))
    return math.sqrt(chi2 / denom) if denom else np.nan


def corr_pairs(df, cols, method, min_abs=0.80, scope="all_numeric"):
    if len(cols) < 2:
        return pd.DataFrame(columns=["scope", "feature_a", "feature_b", "corr", "abs_corr", "threshold_band"])
    corr = df[cols].corr(method=method)
    rows = []
    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            val = corr.loc[a, b]
            if pd.notna(val) and abs(val) >= min_abs:
                abs_val = abs(val)
                rows.append(
                    {
                        "scope": scope,
                        "feature_a": a,
                        "feature_b": b,
                        "corr": float(val),
                        "abs_corr": float(abs_val),
                        "threshold_band": ">=0.95" if abs_val >= 0.95 else ">=0.90" if abs_val >= 0.90 else ">=0.80",
                    }
                )
    return pd.DataFrame(rows).sort_values("abs_corr", ascending=False) if rows else pd.DataFrame(rows)


def cluster_summary(pairs, threshold=0.90):
    rows = []
    if pairs.empty:
        return pd.DataFrame(columns=["cluster_id", "threshold", "n_features", "features", "max_abs_corr", "suggested_interpretation"])
    sub = pairs[pairs["abs_corr"].ge(threshold)]
    graph = nx.Graph()
    for _, row in sub.iterrows():
        graph.add_edge(row["feature_a"], row["feature_b"], weight=row["abs_corr"])
    for i, comp in enumerate(nx.connected_components(graph), start=1):
        features = sorted(comp)
        mask = sub["feature_a"].isin(features) & sub["feature_b"].isin(features)
        max_corr = sub.loc[mask, "abs_corr"].max()
        families = sorted({detect_family(f) for f in features})
        rows.append(
            {
                "cluster_id": f"C{i:03d}",
                "threshold": threshold,
                "n_features": len(features),
                "features": "|".join(features),
                "feature_families": "|".join(families),
                "max_abs_corr": max_corr,
                "suggested_interpretation": "Group these features when explaining SHAP or segment rules; avoid reading each variable as independent evidence.",
            }
        )
    return pd.DataFrame(rows).sort_values(["n_features", "max_abs_corr"], ascending=[False, False]) if rows else pd.DataFrame(rows)


def clean_numeric_matrix(df, cols):
    mat = df[cols].copy()
    for c in cols:
        mat[c] = pd.to_numeric(mat[c], errors="coerce")
        mat[c] = mat[c].fillna(mat[c].median())
    nunique = mat.nunique(dropna=True)
    keep = [c for c in cols if nunique[c] > 1]
    mat = mat[keep]
    std = mat.std(ddof=0).replace(0, np.nan)
    mat = (mat - mat.mean()) / std
    mat = mat.replace([np.inf, -np.inf], np.nan).fillna(0)
    return mat


def vif_from_corr(mat):
    cols = list(mat.columns)
    if len(cols) < 2:
        return pd.DataFrame({"feature": cols, "vif": [np.nan] * len(cols), "status": "BLOCKED"})
    corr = np.corrcoef(mat.to_numpy(), rowvar=False)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    np.fill_diagonal(corr, 1.0)
    rank = np.linalg.matrix_rank(corr)
    cond = np.linalg.cond(corr)
    try:
        inv = np.linalg.inv(corr)
        status = "exact_inverse"
    except np.linalg.LinAlgError:
        inv = np.linalg.pinv(corr)
        status = "pseudo_inverse_singular"
    rows = []
    for col, val in zip(cols, np.diag(inv)):
        vif = float(val) if np.isfinite(val) and val >= 0 else np.inf
        rows.append(
            {
                "feature": col,
                "family": detect_family(col),
                "vif": vif,
                "vif_band": "extreme_or_infinite" if (not np.isfinite(vif) or vif >= 50) else ">=10" if vif >= 10 else ">=5" if vif >= 5 else "<5",
                "matrix_status": status,
                "corr_matrix_rank": int(rank),
                "feature_count_in_vif_matrix": len(cols),
                "condition_number": float(cond) if np.isfinite(cond) else np.inf,
                "recommended_interpretation_action": "Group or remove before coefficient-level interpretation." if (not np.isfinite(vif) or vif >= 10) else "Usable, but still check pairwise correlation.",
            }
        )
    return pd.DataFrame(rows).sort_values("vif", ascending=False)


def exact_duplicate_audit(df, cols):
    rows = []
    num_cols = numeric_cols(df, cols)
    for i, a in enumerate(num_cols):
        sa = df[a]
        for b in num_cols[i + 1 :]:
            sb = df[b]
            both = pd.concat([sa, sb], axis=1).dropna()
            if both.empty:
                continue
            if both.iloc[:, 0].equals(both.iloc[:, 1]):
                rows.append({"audit_type": "exact_identical_numeric", "feature_a": a, "feature_b": b, "detail": "Values are exactly identical on non-null rows.", "severity": "high"})
            vals_a = set(sa.dropna().unique())
            vals_b = set(sb.dropna().unique())
            if vals_a.issubset({0, 1}) and vals_b.issubset({0, 1}) and (both.iloc[:, 0] + both.iloc[:, 1]).eq(1).all():
                rows.append({"audit_type": "exact_inverse_binary", "feature_a": a, "feature_b": b, "detail": "Binary complements; one variable is 1 - the other.", "severity": "high"})
            if sa.notna().equals(sb.notna()) and a != b:
                rows.append({"audit_type": "same_non_null_pattern", "feature_a": a, "feature_b": b, "detail": "Missing/non-missing pattern is identical.", "severity": "low"})
    near = corr_pairs(df, num_cols, method="pearson", min_abs=0.995, scope="near_identical_numeric")
    for _, row in near.iterrows():
        rows.append({"audit_type": "near_identical_corr_ge_0.995", "feature_a": row["feature_a"], "feature_b": row["feature_b"], "detail": f"Pearson abs corr={row['abs_corr']:.6f}", "severity": "high"})
    return pd.DataFrame(rows)


def structural_notes(df, window):
    rows = []
    p = f"{window}_"
    checks = [
        ("total_watch_time", f"{p}total_watch_time", [f"{p}week1_watch_time", f"{p}week2_watch_time", f"{p}week3_watch_time"] + ([f"{p}week4_watch_time"] if window == "w1_4" else []), "total = sum of weekly watch_time"),
        ("total_sessions", f"{p}total_sessions", [f"{p}week1_sessions", f"{p}week2_sessions", f"{p}week3_sessions"] + ([f"{p}week4_sessions"] if window == "w1_4" else []), "total = sum of weekly sessions"),
        ("genre_covered_watch_time", f"{p}genre_covered_watch_time", [c for c in df.columns if c.startswith(f"{p}genre_watch_time_")], "covered watch time approx sum of genre watch_time variables"),
        ("genre_ratio_sum", None, [c for c in df.columns if c.startswith(f"{p}genre_ratio_")], "genre ratios sum approximately to 1 when genre-covered watch exists"),
        ("genre_missing_ratio_complement", f"{p}genre_missing_watch_ratio", [f"{p}genre_covered_watch_ratio"], "missing ratio approx 1 - covered ratio"),
    ]
    for group, lhs, rhs_cols, relation in checks:
        rhs_cols = [c for c in rhs_cols if c in df.columns]
        if lhs and lhs not in df.columns:
            status = "BLOCKED"
            max_abs_error = np.nan
        elif not rhs_cols:
            status = "BLOCKED"
            max_abs_error = np.nan
        else:
            if group == "genre_missing_ratio_complement":
                diff = df[lhs] - (1 - df[rhs_cols[0]])
            elif group == "genre_ratio_sum":
                mask = df[rhs_cols].sum(axis=1) > 0
                diff = df.loc[mask, rhs_cols].sum(axis=1) - 1
            else:
                diff = df[lhs] - df[rhs_cols].sum(axis=1)
            max_abs_error = float(np.nanmax(np.abs(diff))) if len(diff) else np.nan
            status = "CONFIRMED" if pd.notna(max_abs_error) and max_abs_error < 1e-6 else "APPROX_OR_PARTIAL"
        rows.append(
            {
                "window": window,
                "variable_group": group,
                "relationship": relation,
                "lhs_feature": lhs or "",
                "rhs_features": "|".join(rhs_cols),
                "status": status,
                "max_abs_error": max_abs_error,
                "keep_all_for_prediction": "Y",
                "group_for_interpretation": "Y",
                "remove_in_reduced_feature_model": "Consider removing derivatives or totals, keeping one representative per concept.",
            }
        )
    return rows


def reduced_action(feature):
    fam = detect_family(feature)
    if feature == TARGET:
        return "target_only"
    if feature in [ID_COL, GROUP_COL] or feature in FORBIDDEN_FEATURES:
        return "metadata_only"
    if any(t in feature for t in ["week3_watch_time", "week4_watch_time", "first_watch_rel_day", "last_watch_rel_day"]):
        return "use_with_caution"
    if any(t in feature for t in ["week1_watch_time", "week2_watch_time", "total_watch_time", "total_sessions", "week1_sessions", "week2_sessions", "week3_sessions", "week4_sessions"]):
        return "group_for_interpretation"
    if "ratio" in feature or "minus" in feature:
        return "group_for_interpretation"
    if "genre_watch_time" in feature or "genre_session_count" in feature:
        return "group_for_interpretation"
    if "release_month" in feature or "recent_content" in feature or "old_content" in feature:
        return "use_with_caution"
    if feature in ["price", "product_code", "max_screen", "is_promotion"]:
        return "use_with_caution"
    if fam in ["genre", "usage"]:
        return "group_for_interpretation"
    return "keep"


def save_heatmap(df, cols, path, title, max_cols=35):
    cols = cols[:max_cols]
    plt.figure(figsize=(12, 10))
    if len(cols) < 2:
        plt.text(0.5, 0.5, "Not enough numeric features", ha="center", va="center")
        plt.axis("off")
    else:
        corr = df[cols].corr()
        sns.heatmap(corr, cmap="coolwarm", center=0, vmin=-1, vmax=1, square=False, cbar=True)
        plt.title(title)
        plt.xticks(rotation=75, ha="right", fontsize=7)
        plt.yticks(rotation=0, fontsize=7)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def save_bar(df, label_col, value_col, path, title, top_n=25):
    plot = df.head(top_n).copy()
    plt.figure(figsize=(11, 6))
    if plot.empty:
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
    else:
        plt.bar(plot[label_col].astype(str), plot[value_col])
        plt.xticks(rotation=70, ha="right", fontsize=8)
        plt.title(title)
        plt.ylabel(value_col)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def write_notebook():
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 06d v2 Multicollinearity and Feature Redundancy Audit\n",
                    "\n",
                    "Audit-only notebook. It checks redundancy, correlation, VIF, categorical association, and interpretation grouping. It does not train production models, run Optuna, run SHAP, create segmentation, or create business simulation.\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["%run 06d_v2_multicollinearity_redundancy_audit_impl.py\n"],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    nb_path = PROJECT_ROOT / "park.ingyeom" / "notebooks" / "06d_v2_multicollinearity_redundancy_audit.ipynb"
    nb_path.write_text(json.dumps(nb, ensure_ascii=False, indent=2), encoding="utf-8")


raw_before = snapshot_paths(RAW_FILES)
data_before = snapshot_dirs([PROJECT_ROOT / "_data"])
stage_before = snapshot_stage01_09()

df_w13 = pd.read_csv(STAGE05_DATA / "modeling_dataset_v2_w1_3.csv")
df_w14 = pd.read_csv(STAGE05_DATA / "modeling_dataset_v2_w1_4.csv")
feature_sets = read_json(STAGE05_DATA / "feature_sets_v2.json")["feature_sets"]
metrics = pd.read_csv(STAGE06_DATA / "06_v2_model_metrics.csv")
audit06c = read_json(STAGE06C_DATA / "06c_adversarial_audit_summary.json")
global_shap = pd.read_csv(STAGE07R_TABLES / "07r_global_shap_importance.csv")
family_shap = pd.read_csv(STAGE07R_TABLES / "07r_feature_family_shap_importance.csv")

primary_features = [f for f in feature_sets[PRIMARY_FEATURE_SET] if f in df_w13.columns]
primary_shap = global_shap[
    (global_shap["model_role"].eq("primary_conservative"))
    & (global_shap["window"].eq("w1_3"))
    & (global_shap["model_name"].eq("HistGradientBoostingClassifier"))
].copy()
primary_shap = primary_shap.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
primary_shap["shap_rank"] = np.arange(1, len(primary_shap) + 1)
shap_map = primary_shap.drop_duplicates("original_feature").set_index("original_feature").to_dict(orient="index")

inventory_rows = []
for name, df in [("w1_3", df_w13), ("w1_4", df_w14)]:
    metadata_cols = [c for c in df.columns if c in [ID_COL, GROUP_COL]]
    target_cols = [c for c in df.columns if c == TARGET]
    candidate_cols = [c for c in df.columns if c not in metadata_cols + target_cols and c not in FORBIDDEN_FEATURES]
    numeric = [c for c in candidate_cols if pd.api.types.is_numeric_dtype(df[c])]
    categorical = [c for c in candidate_cols if df[c].dtype == "object"]
    boolean = [c for c in numeric if set(df[c].dropna().unique()).issubset({0, 1, 0.0, 1.0})]
    constant = [c for c in candidate_cols if df[c].nunique(dropna=True) <= 1]
    near_constant = []
    for c in candidate_cols:
        vc = df[c].value_counts(normalize=True, dropna=False)
        if not vc.empty and vc.iloc[0] >= 0.995 and c not in constant:
            near_constant.append(c)
    miss = df[candidate_cols].isna().mean()
    inventory_rows.append(
        {
            "dataset": name,
            "total_columns": len(df.columns),
            "metadata_columns": len(metadata_cols),
            "target_columns": len(target_cols),
            "candidate_feature_columns": len(candidate_cols),
            "numeric_features": len(numeric),
            "categorical_features": len(categorical),
            "boolean_features": len(boolean),
            "constant_columns": len(constant),
            "constant_column_names": "|".join(constant),
            "near_constant_columns": len(near_constant),
            "near_constant_column_names": "|".join(near_constant),
            "missing_rate_mean": float(miss.mean()) if len(miss) else 0,
            "missing_rate_max": float(miss.max()) if len(miss) else 0,
        }
    )
feature_inventory = pd.DataFrame(inventory_rows)
write_csv(TABLE_DIR / "06d_feature_inventory.csv", feature_inventory)

primary_inventory_rows = []
for feat in primary_features:
    s = df_w13[feat]
    info = shap_map.get(feat, {})
    primary_inventory_rows.append(
        {
            "feature_name": feat,
            "family": detect_family(feat),
            "type": detect_type(s, feat),
            "missing_rate": float(s.isna().mean()),
            "unique_count": int(s.nunique(dropna=True)),
            "included_in_primary_model": "Y",
            "top_shap_rank": info.get("shap_rank", ""),
            "mean_abs_shap": info.get("mean_abs_shap", ""),
            "interpretation_note": "Group with related structural features if highly correlated or derived.",
        }
    )
primary_inventory = pd.DataFrame(primary_inventory_rows)
write_csv(TABLE_DIR / "06d_primary_feature_set_inventory.csv", primary_inventory)

duplicate_features = exact_duplicate_audit(df_w13, primary_features)
write_csv(TABLE_DIR / "06d_exact_duplicate_features.csv", duplicate_features)

num_primary = numeric_cols(df_w13, primary_features)
usage_numeric = [c for c in num_primary if detect_family(c) == "usage"]
genre_content_numeric = [c for c in num_primary if detect_family(c) in ["genre", "content", "release_month"]]
membership_numeric = [c for c in num_primary if detect_family(c) == "membership"]

pearson_parts = [
    corr_pairs(df_w13, num_primary, "pearson", 0.80, "all_numeric"),
    corr_pairs(df_w13, usage_numeric, "pearson", 0.80, "usage_only"),
    corr_pairs(df_w13, genre_content_numeric, "pearson", 0.80, "genre_content_only"),
    corr_pairs(df_w13, membership_numeric, "pearson", 0.80, "membership_numeric_only"),
]
spearman_parts = [
    corr_pairs(df_w13, num_primary, "spearman", 0.80, "all_numeric"),
    corr_pairs(df_w13, usage_numeric, "spearman", 0.80, "usage_only"),
    corr_pairs(df_w13, genre_content_numeric, "spearman", 0.80, "genre_content_only"),
    corr_pairs(df_w13, membership_numeric, "spearman", 0.80, "membership_numeric_only"),
]
pearson_pairs = pd.concat([p for p in pearson_parts if not p.empty], ignore_index=True) if any(not p.empty for p in pearson_parts) else pd.DataFrame()
spearman_pairs = pd.concat([p for p in spearman_parts if not p.empty], ignore_index=True) if any(not p.empty for p in spearman_parts) else pd.DataFrame()
write_csv(TABLE_DIR / "06d_high_corr_pairs_pearson.csv", pearson_pairs)
write_csv(TABLE_DIR / "06d_high_corr_pairs_spearman.csv", spearman_pairs)

cluster_df = cluster_summary(pearson_pairs[pearson_pairs["scope"].eq("all_numeric")] if not pearson_pairs.empty else pearson_pairs, threshold=0.90)
write_csv(TABLE_DIR / "06d_corr_cluster_summary.csv", cluster_df)

structural_rows = structural_notes(df_w13, "w1_3") + structural_notes(df_w14, "w1_4")
structural_df = pd.DataFrame(structural_rows)
write_csv(TABLE_DIR / "06d_structural_redundancy_notes.csv", structural_df)

vif_exclude = {
    "w1_3_no_watch_obs_flag",
    "w1_3_genre_missing_watch_ratio",
    "w1_3_total_watch_time",
    "w1_3_total_sessions",
}
vif_cols = [c for c in num_primary if c not in vif_exclude and df_w13[c].nunique(dropna=True) > 1]
vif_matrix = clean_numeric_matrix(df_w13, vif_cols)
vif_results = vif_from_corr(vif_matrix)
vif_results["excluded_from_vif_reason"] = ""
for c in vif_exclude:
    if c in num_primary:
        vif_results = pd.concat(
            [
                vif_results,
                pd.DataFrame(
                    [
                        {
                            "feature": c,
                            "family": detect_family(c),
                            "vif": np.nan,
                            "vif_band": "excluded_structural",
                            "matrix_status": "excluded_before_vif",
                            "corr_matrix_rank": "",
                            "feature_count_in_vif_matrix": len(vif_cols),
                            "condition_number": "",
                            "recommended_interpretation_action": "Excluded because it is a known structural complement or total.",
                            "excluded_from_vif_reason": "known structural redundancy/complement",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
write_csv(TABLE_DIR / "06d_vif_results.csv", vif_results)

cat_features = [c for c in primary_features if c in df_w13.columns and df_w13[c].dtype == "object"]
cat_targets = [c for c in ["product_code", "is_promotion", "is_user_verified", "gender", "payment_device", "billing_method", "w1_3_top_genre"] if c in cat_features]
assoc_rows = []
for c in cat_targets:
    vc = df_w13[c].fillna("__MISSING__").astype(str).value_counts()
    rare = int((vc < 50).sum())
    row = {
        "categorical_feature": c,
        "family": detect_family(c),
        "cardinality": int(vc.size),
        "rare_level_count_lt50": rare,
        "top_levels": "; ".join([f"{idx}:{cnt}" for idx, cnt in vc.head(5).items()]),
        "sparse_interpretation_risk": "Y" if rare > 0 or vc.size > 20 else "N",
    }
    for other in ["price", "product_code", "max_screen", "is_promotion"]:
        if other == c or other not in df_w13.columns:
            continue
        if df_w13[other].dtype == "object":
            row[f"cramers_v_with_{other}"] = cramers_v(df_w13[c], df_w13[other])
        else:
            binned = pd.qcut(df_w13[other].rank(method="first"), q=min(5, df_w13[other].nunique()), duplicates="drop")
            row[f"cramers_v_with_{other}"] = cramers_v(df_w13[c], pd.Series(binned, index=df_w13.index))
    assoc_rows.append(row)
categorical_assoc = pd.DataFrame(assoc_rows)
write_csv(TABLE_DIR / "06d_categorical_association_summary.csv", categorical_assoc)

top_shap_features = list(primary_shap.head(30)["original_feature"])
pair_lookup = {}
if not pearson_pairs.empty:
    for _, row in pearson_pairs[pearson_pairs["scope"].eq("all_numeric")].iterrows():
        pair_lookup[frozenset([row["feature_a"], row["feature_b"]])] = row["abs_corr"]
shap_rows = []
for _, row in primary_shap.head(30).iterrows():
    feat = row["original_feature"]
    correlated = []
    for other in top_shap_features:
        if other == feat:
            continue
        val = pair_lookup.get(frozenset([feat, other]))
        if val is not None and val >= 0.80:
            correlated.append(f"{other}:{val:.3f}")
    if any(t in feat for t in ["week3", "week4", "first_watch_rel_day", "last_watch_rel_day"]):
        cls = "target-adjacent timing feature"
    elif any(t in feat for t in ["ratio", "minus"]):
        cls = "structural derivative"
    elif any(t in feat for t in ["genre_watch_time", "genre_session_count", "total_watch_time", "sessions"]):
        cls = "redundant proxy"
    elif detect_family(feat) in ["membership"]:
        cls = "presentation-with-caution feature"
    else:
        cls = "safe presentation feature" if not correlated else "redundant proxy"
    shap_rows.append(
        {
            "shap_rank": int(row["shap_rank"]),
            "feature_name": feat,
            "family": row["feature_family"],
            "mean_abs_shap": row["mean_abs_shap"],
            "correlated_top_shap_features_abs_ge_0_80": "|".join(correlated),
            "redundancy_classification": cls,
            "interpretation_action": "Explain at feature-family or grouped-concept level." if correlated or cls != "safe presentation feature" else "Can be explained individually with standard predictive caveat.",
        }
    )
shap_redundancy = pd.DataFrame(shap_rows)
write_csv(TABLE_DIR / "06d_shap_redundancy_audit.csv", shap_redundancy)

recommend_rows = []
for feat in primary_features:
    action = reduced_action(feat)
    recommend_rows.append(
        {
            "feature_name": feat,
            "family": detect_family(feat),
            "recommendation": action,
            "reason": "Structurally derived or highly related to other behavior/content variables." if action == "group_for_interpretation" else "Timing-sensitive or interpretation-sensitive feature." if action == "use_with_caution" else "Metadata/target handling only." if action in ["metadata_only", "target_only"] else "Relatively safe standalone feature.",
            "future_reduced_model_note": "Consider one representative from the group, not all derivatives." if action == "group_for_interpretation" else "Keep only if business timing and leakage framing are acceptable." if action == "use_with_caution" else "Keep.",
            "shap_rank": shap_map.get(feat, {}).get("shap_rank", ""),
            "mean_abs_shap": shap_map.get(feat, {}).get("mean_abs_shap", ""),
        }
    )
reduced_recommendation = pd.DataFrame(recommend_rows)
write_csv(TABLE_DIR / "06d_reduced_feature_recommendation.csv", reduced_recommendation)

grouping_rows = []
for group_name, patterns, presentation_label in [
    ("usage_volume", ["total_watch_time", "week1_watch_time", "week2_watch_time", "week3_watch_time", "total_sessions", "week1_sessions", "week2_sessions", "week3_sessions"], "시청량 및 주차별 활동량"),
    ("usage_timing", ["first_watch_rel_day", "last_watch_rel_day", "week3", "week4"], "초기/후기 시청 타이밍"),
    ("usage_derivatives", ["ratio", "minus", "max_day_share"], "시청 비중과 변화량"),
    ("short_watch", ["short", "one_minute"], "짧은 시청 행동"),
    ("genre_preference_ratio", ["genre_ratio", "top_genre", "genre_entropy"], "장르 선호 비중"),
    ("genre_volume_proxy", ["genre_watch_time", "genre_session_count", "top_genre_watch_time"], "장르별 시청량 proxy"),
    ("release_month_proxy", ["release_month", "recent_content", "old_content"], "공개월 proxy"),
    ("membership_context", ["price", "product_code", "max_screen", "is_promotion"], "멤버십/가격/프로모션 맥락"),
]:
    feats = [f for f in primary_features if any(p in f for p in patterns)]
    grouping_rows.append(
        {
            "interpretation_group": group_name,
            "presentation_label_ko": presentation_label,
            "feature_count": len(feats),
            "features": "|".join(feats),
            "recommended_story": "Use as grouped interpretation, not as independent causal variables.",
            "presentation_caution": "Tree prediction can use correlated features, but explanation should avoid double-counting related signals.",
        }
    )
grouping_df = pd.DataFrame(grouping_rows)
write_csv(TABLE_DIR / "06d_interpretation_grouping_recommendation.csv", grouping_df)

save_heatmap(df_w13, num_primary, FIGURE_DIR / "06d_primary_numeric_corr_heatmap.png", "Primary Numeric Pearson Correlation")
save_heatmap(df_w13, usage_numeric, FIGURE_DIR / "06d_usage_corr_heatmap.png", "Usage Feature Pearson Correlation")
save_heatmap(df_w13, genre_content_numeric, FIGURE_DIR / "06d_genre_content_corr_heatmap.png", "Genre/Content Feature Pearson Correlation")
save_bar(vif_results[vif_results["vif"].apply(lambda x: pd.notna(x) and np.isfinite(float(x)))].sort_values("vif", ascending=False), "feature", "vif", FIGURE_DIR / "06d_top_vif_features.png", "Top VIF Features")
cluster_plot = cluster_df.copy()
if not cluster_plot.empty:
    cluster_plot["label"] = cluster_plot["cluster_id"] + " n=" + cluster_plot["n_features"].astype(str)
    save_bar(cluster_plot, "label", "n_features", FIGURE_DIR / "06d_shap_redundancy_cluster_map.png", "High-Correlation Cluster Sizes")
else:
    save_bar(cluster_plot, "cluster_id", "n_features", FIGURE_DIR / "06d_shap_redundancy_cluster_map.png", "High-Correlation Cluster Sizes")

severe_corr_count = int((pearson_pairs["abs_corr"].ge(0.95)).sum()) if not pearson_pairs.empty else 0
vif_ge_10 = int((pd.to_numeric(vif_results["vif"], errors="coerce") >= 10).sum())
extreme_vif = int((vif_results["vif_band"] == "extreme_or_infinite").sum())
redundant_groups = grouping_df[grouping_df["feature_count"].gt(0)]["interpretation_group"].tolist()

report_lines = [
    "# 06d v2 Multicollinearity and Feature Redundancy Audit",
    "",
    f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
    "",
    "## Scope",
    "This stage audits feature redundancy and multicollinearity only. It does not train production models, tune models, run Optuna, run SHAP, create segmentation, or create business simulation.",
    "",
    "## 1. Are there severe multicollinearity or redundancy issues?",
    f"Yes. Pearson high-correlation pairs at abs(corr) >= 0.95: {severe_corr_count}. VIF >= 10 features: {vif_ge_10}. Extreme/infinite VIF features: {extreme_vif}. This is a serious interpretation issue, even if tree models can still predict with correlated inputs.",
    "",
    "## 2. Which feature groups are most redundant?",
    "The most redundant groups are weekly usage volume, usage ratios/deltas, genre watch-time/session-count proxies, genre ratio compositions, and coverage/missing complement variables.",
    "",
    "## 3. Which variables should not be interpreted individually?",
    "Do not interpret total/weekly watch-time, weekly ratios, deltas, genre watch-time, genre session-count, and complement flags as independent evidence. They are structurally related.",
    "",
    "## 4. Which variables should be grouped as usage behavior?",
    "Group total watch time, weekly watch time, sessions, active days, first/last watch rel_day, ratios, deltas, max-day concentration, and short-watch behavior as usage behavior.",
    "",
    "## 5. Which variables should be grouped as genre/content proxies?",
    "Group genre ratios, top genre, genre entropy, genre watch-time, genre session-count, and release-month proxies as content/genre proxy signals.",
    "",
    "## 6. Which variables are structurally derived from others?",
    "Weekly totals, ratios, deltas, genre ratio sums, genre watch-time sums, and coverage/missing complements are structurally derived or compositional.",
    "",
    "## 7. Which variables remain safe to explain individually?",
    "Relatively safer standalone variables include basic membership context such as max_screen, age, gender, payment_device, and billing_method, but price/product/promotion still require cohort-policy caution.",
    "",
    "## 8. How should this change SHAP interpretation?",
    "SHAP should be interpreted mostly at feature-family or grouped-concept level. Individual SHAP ranks can split credit across redundant derivatives, so rank order should not be read as independent causal importance.",
    "",
    "## 9. Should any feature be removed before final presentation or future modeling?",
    "No current production model is changed here. For future reduced-feature modeling, use one representative from each structural group and consider dropping complements, totals plus components, and duplicated volume proxies.",
    "",
    "## 10. What should be told to the mentor?",
    "The high AUC is not only target-adjacent per Stage 06c; it also relies on many correlated and structurally related behavior/content variables. Prediction may remain valid for ranking, but interpretation must be grouped and cautious.",
    "",
    "## Key Output Tables",
    f"- Feature inventory: `{rel(TABLE_DIR / '06d_feature_inventory.csv')}`",
    f"- High corr pairs: `{rel(TABLE_DIR / '06d_high_corr_pairs_pearson.csv')}`",
    f"- VIF: `{rel(TABLE_DIR / '06d_vif_results.csv')}`",
    f"- Reduced recommendation: `{rel(TABLE_DIR / '06d_reduced_feature_recommendation.csv')}`",
]
(DATA_DIR / "06d_multicollinearity_audit_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

mentor_lines = [
    "# 06d 멘토 공유용 다중공선성 요약",
    "",
    "## 다중공선성을 왜 지금 확인했는가",
    "Stage 06c에서 높은 AUC가 직접 누수라기보다는 target-adjacent 행동 proxy일 가능성이 크다고 판단했습니다. 그 다음으로 확인해야 할 문제는 같은 행동 신호가 여러 파생변수로 반복되어 해석을 과장하거나 SHAP 중요도를 분산시키는지입니다.",
    "",
    "## 어떤 변수군이 중복성이 강한가",
    "주차별 시청 시간, 총 시청 시간, 주차별 세션 수, 비율 변수, 주차 간 변화량, 장르별 watch_time/session_count, 장르 비율 변수, 장르 coverage/missing 변수에서 구조적 중복성이 강합니다.",
    "",
    "## 트리 모델 성능에는 큰 문제가 아닐 수 있지만 해석에는 왜 조심해야 하는가",
    "트리 모델은 상관된 변수가 여러 개 있어도 예측 성능을 낼 수 있습니다. 하지만 변수들이 같은 정보를 나눠 가지면, 개별 변수의 중요도나 SHAP 순위가 독립적인 원인처럼 보일 수 있습니다. 따라서 성능보다 해석에서 더 위험합니다.",
    "",
    "## SHAP 중요도를 feature family 단위로 해석해야 하는 이유",
    "week3_watch_time, total/weekly usage, ratio, delta, genre watch_time은 서로 연결된 신호입니다. SHAP 값은 이 연결된 변수들 사이에 기여도를 나눠 배분할 수 있으므로, 개별 변수 순위보다 usage, genre/content, membership 같은 feature family 단위가 더 안전합니다.",
    "",
    "## 최종 발표에서는 어떤 변수를 묶어서 설명할 것인가",
    "최종 발표에서는 시청량 및 주차별 활동량, 시청 타이밍, 시청 비중과 변화량, 짧은 시청 행동, 장르 선호 비중, 장르별 시청량 proxy, 공개월 proxy, 멤버십/가격/프로모션 맥락으로 묶어 설명하는 것이 안전합니다.",
]
(DATA_DIR / "06d_mentor_facing_multicollinearity_summary.md").write_text("\n".join(mentor_lines) + "\n", encoding="utf-8")

raw_after = snapshot_paths(RAW_FILES)
data_after = snapshot_dirs([PROJECT_ROOT / "_data"])
stage_after = snapshot_stage01_09()
final_checks = pd.DataFrame(
    [
        ("raw_files_unchanged", "PASS" if raw_before == raw_after else "FAIL", "raw file snapshots unchanged" if raw_before == raw_after else "raw snapshot changed"),
        ("no__data_output_created", "PASS" if data_before == data_after else "FAIL", "_data snapshot unchanged" if data_before == data_after else "_data snapshot changed"),
        ("stage01_through_stage09_outputs_not_overwritten", "PASS" if stage_before == stage_after else "FAIL", "Stage 01-09 snapshots unchanged" if stage_before == stage_after else "Stage 01-09 snapshot changed"),
        ("no_model_training_performed", "PASS", "Only correlation, VIF, association, and descriptive audits were computed."),
        ("no_optuna_run", "PASS", "No optuna import or execution."),
        ("no_shap_run", "PASS", "Read Stage 07r SHAP CSV outputs only; no shap package execution."),
        ("no_segmentation_created", "PASS", "No Stage 08/08b outputs created."),
        ("no_business_simulation_created", "PASS", "No Stage 09 outputs created."),
        ("primary_feature_set_audited", "PASS" if len(primary_inventory) == len(primary_features) else "FAIL", f"audited={len(primary_inventory)}, expected={len(primary_features)}"),
        ("correlation_audit_completed", "PASS" if (TABLE_DIR / "06d_high_corr_pairs_pearson.csv").exists() else "FAIL", "Pearson and Spearman outputs written."),
        ("vif_audit_completed_or_blocked_reason_documented", "PASS" if not vif_results.empty else "FAIL", f"rows={len(vif_results)}"),
        ("structural_redundancy_audit_completed", "PASS" if not structural_df.empty else "FAIL", f"rows={len(structural_df)}"),
        ("shap_redundancy_audit_completed_using_stage07r", "PASS" if not shap_redundancy.empty else "FAIL", f"rows={len(shap_redundancy)}"),
        ("reduced_feature_recommendation_created", "PASS" if not reduced_recommendation.empty else "FAIL", f"rows={len(reduced_recommendation)}"),
        ("mentor_facing_summary_created", "PASS" if (DATA_DIR / "06d_mentor_facing_multicollinearity_summary.md").exists() else "FAIL", rel(DATA_DIR / "06d_mentor_facing_multicollinearity_summary.md")),
    ],
    columns=["check", "status", "detail"],
)
write_csv(TABLE_DIR / "06d_final_checks.csv", final_checks)

summary = {
    "scope": "Stage 06d multicollinearity and redundancy audit only.",
    "primary_feature_set": PRIMARY_FEATURE_SET,
    "primary_feature_count": len(primary_features),
    "numeric_primary_feature_count": len(num_primary),
    "pearson_high_corr_pair_count_abs_ge_0_80": int(len(pearson_pairs)) if not pearson_pairs.empty else 0,
    "pearson_high_corr_pair_count_abs_ge_0_90": int((pearson_pairs["abs_corr"].ge(0.90)).sum()) if not pearson_pairs.empty else 0,
    "pearson_high_corr_pair_count_abs_ge_0_95": severe_corr_count,
    "correlation_cluster_count_abs_ge_0_90": int(len(cluster_df)),
    "vif_ge_5_count": int((pd.to_numeric(vif_results["vif"], errors="coerce") >= 5).sum()),
    "vif_ge_10_count": vif_ge_10,
    "extreme_vif_count": extreme_vif,
    "structural_relationship_count": int(len(structural_df)),
    "top_redundant_groups": redundant_groups,
    "stage06c_verdict": audit06c.get("final_verdict"),
    "final_interpretation_verdict": "severe_redundancy_for_interpretation_tree_prediction_still_possible",
    "final_checks_passed": bool(final_checks["status"].eq("PASS").all()),
}
write_json(DATA_DIR / "06d_multicollinearity_audit_summary.json", summary)

write_notebook()

print("06d multicollinearity redundancy audit completed.")
for _, row in final_checks.iterrows():
    print(f"{row['check']}: {row['status']} - {row['detail']}")
print("final_interpretation_verdict:", summary["final_interpretation_verdict"])
