from __future__ import annotations

import csv
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[3]
PUBLIC_ROOT = REPO_ROOT / "PUBLIC"

INPUT_DIR = PUBLIC_ROOT / "results" / "16_SHAP_candidate_interpretation_260520" / "four_model_shap_interpretation"
OUTPUT_DIR = PUBLIC_ROOT / "results" / "16_SHAP_candidate_interpretation_260520" / "16b_feature_family_mapping_hotfix_260520"
HANDOFF_DIR = PUBLIC_ROOT / "handoff" / "PUBLIC_16b_feature_family_mapping_hotfix_260520"
NOTEBOOK_DIR = PUBLIC_ROOT / "notebooks" / "16_SHAP_candidate_interpretation_260520"
NOTEBOOK_PATH = NOTEBOOK_DIR / "16b_feature_family_mapping_hotfix_260520.ipynb"
EXECUTED_NOTEBOOK_PATH = NOTEBOOK_DIR / "16b_feature_family_mapping_hotfix_260520_executed.ipynb"
ZIP_PATH = PUBLIC_ROOT / "zip" / "PUBLIC_16b_feature_family_mapping_hotfix_260520_review_package.zip"

REQUIRED_INPUTS = [
    "16_shap_global_importance.csv",
    "16_lr_coefficient_summary.csv",
    "16_shap_direction_summary.csv",
    "16_feature_family_mapping_for_shap.csv",
    "16_shap_family_importance.csv",
    "16_promo1_vs_promo0_shap_comparison.csv",
    "16_demographic_context_audit_for_shap.csv",
    "16_is_churn_prevented_interpretation_audit.csv",
    "16_readiness_for_segmentation.csv",
    "README.md",
]

OUTPUT_FILES = [
    "16b_technical_unknown_inventory.csv",
    "16b_feature_family_mapping_hotfix.csv",
    "16b_family_mapping_change_log.csv",
    "16b_shap_global_importance_with_hotfix_family.csv",
    "16b_shap_family_importance_hotfix.csv",
    "16b_family_importance_before_after_comparison.csv",
    "16b_promo1_vs_promo0_shap_comparison_hotfix.csv",
    "16b_family_interpretation_handoff_for_17.csv",
]

REMAP_RULES: dict[str, dict[str, str]] = {
    "reg_hour_morning": {
        "family": "registration_timing_context",
        "rule": "explicit 16b registration hour remap",
        "reason": "가입 시점과 가입 시간대 맥락 변수다.",
        "impact": "17 segmentation에서 직접 행동 원인으로 쓰지 않고 profile/context layer로 분리한다.",
    },
    "reg_hour_afternoon": {
        "family": "registration_timing_context",
        "rule": "explicit 16b registration hour remap",
        "reason": "가입 시점과 가입 시간대 맥락 변수다.",
        "impact": "17 segmentation에서 직접 행동 원인으로 쓰지 않고 profile/context layer로 분리한다.",
    },
    "reg_hour_evening": {
        "family": "registration_timing_context",
        "rule": "explicit 16b registration hour remap",
        "reason": "가입 시점과 가입 시간대 맥락 변수다.",
        "impact": "17 segmentation에서 직접 행동 원인으로 쓰지 않고 profile/context layer로 분리한다.",
    },
    "reg_hour_night": {
        "family": "registration_timing_context",
        "rule": "explicit 16b registration hour remap",
        "reason": "가입 시점과 가입 시간대 맥락 변수다.",
        "impact": "17 segmentation에서 직접 행동 원인으로 쓰지 않고 profile/context layer로 분리한다.",
    },
    "reg_is_weekend": {
        "family": "registration_timing_context",
        "rule": "explicit 16b weekend registration remap",
        "reason": "주중/주말 가입 맥락 변수다.",
        "impact": "17 segmentation에서 registration timing context로 별도 caveat를 둔다.",
    },
    "active_ratio": {
        "family": "usage_concentration",
        "rule": "explicit 16b usage concentration remap",
        "reason": "사용 활동 분산과 반복 활동 패턴을 나타낸다.",
        "impact": "17 segmentation에서 사용 집중/분산 신호로 검토할 수 있다.",
    },
    "max_day_share": {
        "family": "usage_concentration",
        "rule": "explicit 16b usage concentration remap",
        "reason": "특정 일자에 활동이 몰렸는지 나타낸다.",
        "impact": "17 segmentation에서 사용 집중/분산 신호로 검토할 수 있다.",
    },
    "day_count_over_3times": {
        "family": "usage_concentration",
        "rule": "explicit 16b usage concentration remap",
        "reason": "반복 사용이 발생한 날짜 수를 나타낸다.",
        "impact": "17 segmentation에서 사용 빈도와 집중도를 함께 검토할 수 있다.",
    },
    "recency": {
        "family": "inactivity_recency",
        "rule": "explicit 16b inactivity/recency remap",
        "reason": "최근 활동 여부와 마지막 활동 거리 신호다.",
        "impact": "17 segmentation에서 최근 비활성 위험 family로 사용할 수 있다.",
    },
    "max_inactive_gap_days": {
        "family": "inactivity_recency",
        "rule": "explicit 16b inactivity gap remap",
        "reason": "비활성 공백 길이를 나타낸다.",
        "impact": "17 segmentation에서 장기 비활성 공백 신호로 사용할 수 있다.",
    },
    "is_only_w1": {
        "family": "week_specific_usage_pattern",
        "rule": "explicit 16b week-specific usage remap",
        "reason": "1주차에만 시청한 고객 패턴을 나타낸다.",
        "impact": "17 segmentation에서 초반만 보고 사라진 고객 패턴 후보로 검토할 수 있다.",
    },
    "is_only_w2": {
        "family": "week_specific_usage_pattern",
        "rule": "explicit 16b week-specific usage remap",
        "reason": "2주차에만 시청한 고객 패턴을 나타낸다.",
        "impact": "17 segmentation에서 특정 주차 집중 사용 패턴으로 검토할 수 있다.",
    },
    "is_only_w3": {
        "family": "week_specific_usage_pattern",
        "rule": "explicit 16b week-specific usage remap",
        "reason": "3주차에만 시청한 고객 패턴을 나타낸다.",
        "impact": "17 segmentation에서 특정 주차 집중 사용 패턴으로 검토할 수 있다.",
    },
    "historical_war_ratio": {
        "family": "genre_preference",
        "rule": "explicit 16b genre ratio remap",
        "reason": "장르/콘텐츠 선호 ratio 계열이다.",
        "impact": "17 segmentation에서는 profile/action 소재로 사용하고 장르가 churn을 유발한다고 쓰지 않는다.",
    },
    "sf_fantasy_ratio": {
        "family": "genre_preference",
        "rule": "explicit 16b genre ratio remap",
        "reason": "장르/콘텐츠 선호 ratio 계열이다.",
        "impact": "17 segmentation에서는 profile/action 소재로 사용하고 장르가 churn을 유발한다고 쓰지 않는다.",
    },
    "other_ratio": {
        "family": "genre_preference",
        "rule": "explicit 16b other genre ratio remap",
        "reason": "명확한 단일 장르는 아니지만 기타 장르 선호 비중을 나타낸다.",
        "impact": "17 segmentation에서는 해석 caveat와 함께 profile/action 소재로 사용한다.",
    },
}


def ensure_dirs() -> None:
    for path in [OUTPUT_DIR, HANDOFF_DIR, NOTEBOOK_DIR, ZIP_PATH.parent]:
        path.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT)).replace("/", "\\")


def write_rows(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def read_shape(path: Path) -> tuple[Any, Any]:
    if not path.exists() or path.suffix.lower() != ".csv":
        return "", ""
    df = pd.read_csv(path)
    return len(df), len(df.columns)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint_targets() -> list[tuple[Path, str]]:
    targets: list[tuple[Path, str]] = [(INPUT_DIR / name, "existing_16_core_input") for name in REQUIRED_INPUTS]
    targets += [(OUTPUT_DIR / name, "16b_output") for name in OUTPUT_FILES]
    targets += [
        (OUTPUT_DIR / "README.md", "16b_output"),
        (HANDOFF_DIR / "README.md", "16b_handoff"),
        (HANDOFF_DIR / "16b_input_validation.csv", "16b_handoff"),
        (HANDOFF_DIR / "PUBLIC_16b_feature_family_mapping_hotfix_final_checks.csv", "16b_handoff"),
        (HANDOFF_DIR / "PUBLIC_16b_feature_family_mapping_hotfix_zip_inventory.csv", "16b_handoff"),
        (HANDOFF_DIR / "16b_source_fingerprint_before_after.csv", "16b_handoff"),
        (SCRIPT_PATH, "16b_helper"),
        (NOTEBOOK_PATH, "16b_notebook"),
        (EXECUTED_NOTEBOOK_PATH, "16b_notebook"),
        (PUBLIC_ROOT / "note.md", "note"),
    ]
    return targets


def snapshot() -> dict[str, dict[str, Any]]:
    out = {}
    for path, role in fingerprint_targets():
        key = rel(path)
        if path.exists():
            out[key] = {"file_path": key, "file_role": role, "sha256": sha256_file(path), "size": path.stat().st_size}
        else:
            out[key] = {"file_path": key, "file_role": role, "sha256": "", "size": ""}
    return out


def write_fingerprint(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> Path:
    rows = []
    for key in sorted(set(before) | set(after)):
        b = before.get(key, {})
        a = after.get(key, {})
        role = a.get("file_role") or b.get("file_role", "")
        if b.get("sha256") and a.get("sha256") and b.get("sha256") == a.get("sha256"):
            status = "unchanged"
        elif role == "note" and b.get("sha256") and a.get("sha256") and b.get("sha256") != a.get("sha256"):
            status = "intentionally_updated_note"
        elif role in {"16b_output", "16b_handoff", "16b_notebook"} and not b.get("sha256") and a.get("sha256"):
            status = "new_output_created"
        elif key == rel(EXECUTED_NOTEBOOK_PATH) and a.get("sha256"):
            status = "intentionally_updated_16b_executed_notebook"
        elif b.get("sha256") and not a.get("sha256"):
            status = "missing_after"
        elif b.get("sha256") and a.get("sha256") and b.get("sha256") != a.get("sha256"):
            status = "changed_needs_review"
        else:
            status = "missing_before_and_after"
        rows.append(
            {
                "file_path": key,
                "file_role": role,
                "sha256_before": b.get("sha256", ""),
                "sha256_after": a.get("sha256", ""),
                "size_before": b.get("size", ""),
                "size_after": a.get("size", ""),
                "status": status,
            }
        )
    return write_rows(HANDOFF_DIR / "16b_source_fingerprint_before_after.csv", rows, ["file_path", "file_role", "sha256_before", "sha256_after", "size_before", "size_after", "status"])


def refresh_fingerprint_after_outputs() -> Path | None:
    path = HANDOFF_DIR / "16b_source_fingerprint_before_after.csv"
    if not path.exists():
        return None
    prior = pd.read_csv(path).to_dict("records")
    current = snapshot()
    rows = []
    for row in prior:
        key = str(row.get("file_path", ""))
        role = row.get("file_role", current.get(key, {}).get("file_role", ""))
        before_hash = "" if pd.isna(row.get("sha256_before", "")) else str(row.get("sha256_before", ""))
        before_size = "" if pd.isna(row.get("size_before", "")) else row.get("size_before", "")
        after_hash = current.get(key, {}).get("sha256", "")
        after_size = current.get(key, {}).get("size", "")
        if before_hash and after_hash and before_hash == after_hash:
            status = "unchanged"
        elif role == "note" and before_hash and after_hash and before_hash != after_hash:
            status = "intentionally_updated_note"
        elif role in {"16b_output", "16b_handoff", "16b_notebook"} and not before_hash and after_hash:
            status = "new_output_created"
        elif key == rel(EXECUTED_NOTEBOOK_PATH) and after_hash:
            status = "intentionally_updated_16b_executed_notebook"
        elif before_hash and not after_hash:
            status = "missing_after"
        elif before_hash and after_hash and before_hash != after_hash:
            status = "changed_needs_review"
        else:
            status = "missing_before_and_after"
        rows.append(
            {
                "file_path": key,
                "file_role": role,
                "sha256_before": before_hash,
                "sha256_after": after_hash,
                "size_before": before_size,
                "size_after": after_size,
                "status": status,
            }
        )
    return write_rows(path, rows, ["file_path", "file_role", "sha256_before", "sha256_after", "size_before", "size_after", "status"])


def input_validation() -> Path:
    rows = []
    for name in REQUIRED_INPUTS:
        path = INPUT_DIR / name
        rows_count, cols = read_shape(path)
        rows.append(
            {
                "input_item": name,
                "expected_path": rel(path),
                "exists": path.exists(),
                "rows": rows_count,
                "columns": cols,
                "status": "PASS" if path.exists() else "FAIL",
                "notes": "required 16 SHAP input",
            }
        )
    return write_rows(HANDOFF_DIR / "16b_input_validation.csv", rows, ["input_item", "expected_path", "exists", "rows", "columns", "status", "notes"])


def load_inputs() -> dict[str, pd.DataFrame]:
    return {
        "mapping": pd.read_csv(INPUT_DIR / "16_feature_family_mapping_for_shap.csv"),
        "global": pd.read_csv(INPUT_DIR / "16_shap_global_importance.csv"),
        "coef": pd.read_csv(INPUT_DIR / "16_lr_coefficient_summary.csv"),
        "direction": pd.read_csv(INPUT_DIR / "16_shap_direction_summary.csv"),
        "old_family": pd.read_csv(INPUT_DIR / "16_shap_family_importance.csv"),
        "old_compare": pd.read_csv(INPUT_DIR / "16_promo1_vs_promo0_shap_comparison.csv"),
    }


def proposed_family(feature: str, old_family: str) -> tuple[str, str, str, str]:
    if feature in REMAP_RULES:
        r = REMAP_RULES[feature]
        return r["family"], r["rule"], "hotfixed_for_16b_and_17_handoff", r["reason"]
    if old_family == "technical_or_unknown":
        return old_family, "still no approved 16b mapping", "still_unknown_needs_user_review", "not covered by explicit 16b remap rules"
    return old_family, "unchanged from 16 mapping", "unchanged_from_16", "existing family retained"


def technical_unknown_inventory(data: dict[str, pd.DataFrame]) -> Path:
    mapping = data["mapping"]
    glob = data["global"].copy()
    coef = data["coef"].copy()
    direction = data["direction"].copy()
    rows = []
    for _, row in mapping[mapping["feature_family"] == "technical_or_unknown"].iterrows():
        feature = row["feature_name"]
        in_global = feature in set(glob["feature_name"])
        in_coef = feature in set(coef["feature_name"])
        in_direction = feature in set(direction["feature_name"])
        ranks = []
        if in_global:
            ranks += pd.to_numeric(glob.loc[glob["feature_name"] == feature, "rank"], errors="coerce").dropna().tolist()
        if in_coef:
            ranks += pd.to_numeric(coef.loc[coef["feature_name"] == feature, "rank"], errors="coerce").dropna().tolist()
        max_mean_abs = ""
        if in_global and "mean_abs_shap" in glob.columns:
            vals = pd.to_numeric(glob.loc[glob["feature_name"] == feature, "mean_abs_shap"], errors="coerce").dropna()
            max_mean_abs = float(vals.max()) if len(vals) else ""
        new_family, _rule, _status, reason = proposed_family(feature, row["feature_family"])
        rows.append(
            {
                "feature_name": feature,
                "old_feature_family": row["feature_family"],
                "old_mapping_rule": row["mapping_rule"],
                "old_final_mapping_status": row["final_mapping_status"],
                "appears_in_shap_global_importance": in_global,
                "appears_in_lr_coefficient_summary": in_coef,
                "appears_in_direction_summary": in_direction,
                "importance_rank_min": min(ranks) if ranks else "",
                "max_mean_abs_shap_if_available": max_mean_abs,
                "needs_remap": feature in REMAP_RULES,
                "proposed_new_family": new_family,
                "reason": reason,
            }
        )
    return write_rows(
        OUTPUT_DIR / "16b_technical_unknown_inventory.csv",
        rows,
        [
            "feature_name",
            "old_feature_family",
            "old_mapping_rule",
            "old_final_mapping_status",
            "appears_in_shap_global_importance",
            "appears_in_lr_coefficient_summary",
            "appears_in_direction_summary",
            "importance_rank_min",
            "max_mean_abs_shap_if_available",
            "needs_remap",
            "proposed_new_family",
            "reason",
        ],
    )


def mapping_hotfix(data: dict[str, pd.DataFrame]) -> tuple[Path, pd.DataFrame]:
    rows = []
    for _, row in data["mapping"].iterrows():
        feature = row["feature_name"]
        old_family = row["feature_family"]
        new_family, new_rule, new_status, reason = proposed_family(feature, old_family)
        if old_family != new_family:
            remap_status = "remapped"
        elif new_status == "still_unknown_needs_user_review":
            remap_status = "still_unknown"
        else:
            remap_status = "unchanged"
        rows.append(
            {
                "feature_name": feature,
                "old_feature_family": old_family,
                "new_feature_family": new_family,
                "old_mapping_rule": row["mapping_rule"],
                "new_mapping_rule": new_rule,
                "old_final_mapping_status": row["final_mapping_status"],
                "new_final_mapping_status": new_status,
                "remap_status": remap_status,
                "reason": reason,
                "notes": "16b changes only family mapping; SHAP values are unchanged.",
            }
        )
    out = pd.DataFrame(rows)
    path = OUTPUT_DIR / "16b_feature_family_mapping_hotfix.csv"
    write_rows(path, rows, ["feature_name", "old_feature_family", "new_feature_family", "old_mapping_rule", "new_mapping_rule", "old_final_mapping_status", "new_final_mapping_status", "remap_status", "reason", "notes"])
    return path, out


def change_log(mapping_df: pd.DataFrame) -> Path:
    rows = []
    changed = mapping_df[mapping_df["old_feature_family"] != mapping_df["new_feature_family"]]
    for _, row in changed.iterrows():
        new_family = row["new_feature_family"]
        rows.append(
            {
                "feature_name": row["feature_name"],
                "old_feature_family": row["old_feature_family"],
                "new_feature_family": new_family,
                "change_type": f"technical_unknown_to_{new_family}",
                "business_interpretation_impact": REMAP_RULES[row["feature_name"]]["impact"],
                "reason": row["reason"],
                "notes": "Use this hotfix mapping for 17 segmentation handoff; do not treat old bucket as segment.",
            }
        )
    return write_rows(OUTPUT_DIR / "16b_family_mapping_change_log.csv", rows, ["feature_name", "old_feature_family", "new_feature_family", "change_type", "business_interpretation_impact", "reason", "notes"])


def global_with_hotfix(data: dict[str, pd.DataFrame], mapping_df: pd.DataFrame) -> tuple[Path, pd.DataFrame]:
    glob = data["global"].copy()
    merged = glob.merge(mapping_df[["feature_name", "old_feature_family", "new_feature_family"]], on="feature_name", how="left")
    merged["old_feature_family"] = merged["old_feature_family"].fillna(merged.get("feature_family", ""))
    merged["hotfix_feature_family"] = merged["new_feature_family"].fillna(merged["old_feature_family"])
    merged["family_changed"] = merged["old_feature_family"] != merged["hotfix_feature_family"]
    merged["notes"] = "Existing SHAP value retained; only feature family mapping was hotfixed."
    cols = ["model_family", "promo_scope", "feature_name", "mean_abs_shap", "rank", "old_feature_family", "hotfix_feature_family", "family_changed", "interpretation_caveat", "notes"]
    path = OUTPUT_DIR / "16b_shap_global_importance_with_hotfix_family.csv"
    write_rows(path, merged[cols].to_dict("records"), cols)
    return path, merged


def family_importance_hotfix(global_df: pd.DataFrame, old_family: pd.DataFrame) -> tuple[Path, pd.DataFrame]:
    df = global_df.copy()
    df["mean_abs_shap"] = pd.to_numeric(df["mean_abs_shap"], errors="coerce")
    grouped = (
        df.groupby(["model_family", "promo_scope", "hotfix_feature_family"], as_index=False)
        .agg(total_mean_abs_shap=("mean_abs_shap", "sum"), mean_mean_abs_shap=("mean_abs_shap", "mean"), feature_count=("feature_name", "count"))
        .rename(columns={"hotfix_feature_family": "feature_family"})
    )
    old_keys = set(zip(old_family["model_family"], old_family["promo_scope"], old_family["feature_family"]))
    rows = []
    for (model, scope), sub in grouped.groupby(["model_family", "promo_scope"]):
        sub = sub.sort_values("total_mean_abs_shap", ascending=False).reset_index(drop=True)
        for idx, row in sub.iterrows():
            key = (model, scope, row["feature_family"])
            rows.append(
                {
                    "model_family": model,
                    "promo_scope": scope,
                    "feature_family": row["feature_family"],
                    "total_mean_abs_shap": float(row["total_mean_abs_shap"]),
                    "mean_mean_abs_shap": float(row["mean_mean_abs_shap"]),
                    "feature_count": int(row["feature_count"]),
                    "family_rank": idx + 1,
                    "changed_from_original": key not in old_keys or row["feature_family"] in {r["family"] for r in REMAP_RULES.values()},
                    "interpretation_caveat": "SHAP values are unchanged; only family aggregation changed.",
                    "notes": "Use for 17 handoff after review.",
                }
            )
    out = pd.DataFrame(rows)
    path = OUTPUT_DIR / "16b_shap_family_importance_hotfix.csv"
    write_rows(path, rows, ["model_family", "promo_scope", "feature_family", "total_mean_abs_shap", "mean_mean_abs_shap", "feature_count", "family_rank", "changed_from_original", "interpretation_caveat", "notes"])
    return path, out


def before_after(old_family: pd.DataFrame, new_family: pd.DataFrame, mapping_df: pd.DataFrame) -> Path:
    old = old_family.rename(columns={"total_mean_abs_shap": "old_total_mean_abs_shap", "family_rank": "old_family_rank"})
    new = new_family.rename(columns={"total_mean_abs_shap": "new_total_mean_abs_shap", "family_rank": "new_family_rank"})
    merged = old[["model_family", "promo_scope", "feature_family", "old_total_mean_abs_shap", "old_family_rank"]].merge(
        new[["model_family", "promo_scope", "feature_family", "new_total_mean_abs_shap", "new_family_rank"]],
        on=["model_family", "promo_scope", "feature_family"],
        how="outer",
    )
    remapped_count = int((mapping_df["remap_status"] == "remapped").sum())
    remaining_unknown = int((mapping_df["new_feature_family"] == "technical_or_unknown").sum())
    rows = []
    for _, row in merged.fillna("").iterrows():
        old_val = float(row["old_total_mean_abs_shap"]) if row["old_total_mean_abs_shap"] != "" else 0.0
        new_val = float(row["new_total_mean_abs_shap"]) if row["new_total_mean_abs_shap"] != "" else 0.0
        old_rank = row["old_family_rank"]
        new_rank = row["new_family_rank"]
        rank_change = "" if old_rank == "" or new_rank == "" else int(float(old_rank) - float(new_rank))
        fam = row["feature_family"]
        if fam == "technical_or_unknown":
            interp = f"technical_or_unknown reduced from old importance to new importance; remaining_feature_count={remaining_unknown}; remapped_feature_count={remapped_count}"
        elif old_val == 0 and new_val > 0:
            interp = "new hotfix family created from remapped technical_or_unknown features"
        elif new_val != old_val:
            interp = "family importance changed because remapped features moved between families"
        else:
            interp = "family importance unchanged"
        rows.append(
            {
                "model_family": row["model_family"],
                "promo_scope": row["promo_scope"],
                "feature_family": fam,
                "old_total_mean_abs_shap": old_val,
                "new_total_mean_abs_shap": new_val,
                "old_family_rank": old_rank,
                "new_family_rank": new_rank,
                "delta_total_mean_abs_shap": new_val - old_val,
                "rank_change": rank_change,
                "interpretation": interp,
            }
        )
    return write_rows(OUTPUT_DIR / "16b_family_importance_before_after_comparison.csv", rows, ["model_family", "promo_scope", "feature_family", "old_total_mean_abs_shap", "new_total_mean_abs_shap", "old_family_rank", "new_family_rank", "delta_total_mean_abs_shap", "rank_change", "interpretation"])


def promo_comparison(global_df: pd.DataFrame, family_df: pd.DataFrame) -> Path:
    rows = []
    for model, sub in global_df.groupby("model_family"):
        for feature, fsub in sub.groupby("feature_name"):
            p1 = fsub.loc[fsub["promo_scope"] == "promo1", "mean_abs_shap"]
            p0 = fsub.loc[fsub["promo_scope"] == "promo0", "mean_abs_shap"]
            p1v = float(p1.iloc[0]) if len(p1) else ""
            p0v = float(p0.iloc[0]) if len(p0) else ""
            delta = "" if p1v == "" or p0v == "" else p1v - p0v
            stronger = "insufficient_or_unavailable" if delta == "" else ("promo1" if delta > 0 else ("promo0" if delta < 0 else "similar"))
            rows.append(
                {
                    "model_family": model,
                    "feature_or_family": feature,
                    "comparison_level": "feature",
                    "promo1_importance": p1v,
                    "promo0_importance": p0v,
                    "delta_promo1_minus_promo0": delta,
                    "stronger_in": stronger,
                    "interpretation": "model uses this feature more strongly in promo1" if stronger == "promo1" else ("model uses this feature more strongly in promo0" if stronger == "promo0" else "similar_or_unavailable"),
                    "caveat": "This is model behavior, not evidence that 100won caused the difference.",
                    "notes": "Feature-level comparison retains existing SHAP values.",
                }
            )
    for model, sub in family_df.groupby("model_family"):
        for fam, fsub in sub.groupby("feature_family"):
            p1 = fsub.loc[fsub["promo_scope"] == "promo1", "total_mean_abs_shap"]
            p0 = fsub.loc[fsub["promo_scope"] == "promo0", "total_mean_abs_shap"]
            p1v = float(p1.iloc[0]) if len(p1) else ""
            p0v = float(p0.iloc[0]) if len(p0) else ""
            delta = "" if p1v == "" or p0v == "" else p1v - p0v
            stronger = "insufficient_or_unavailable" if delta == "" else ("promo1" if delta > 0 else ("promo0" if delta < 0 else "similar"))
            rows.append(
                {
                    "model_family": model,
                    "feature_or_family": fam,
                    "comparison_level": "family_hotfix",
                    "promo1_importance": p1v,
                    "promo0_importance": p0v,
                    "delta_promo1_minus_promo0": delta,
                    "stronger_in": stronger,
                    "interpretation": "model uses this hotfixed family more strongly in promo1" if stronger == "promo1" else ("model uses this hotfixed family more strongly in promo0" if stronger == "promo0" else "similar_or_unavailable"),
                    "caveat": "Promo1 strength is not a causal claim about the 100won promotion.",
                    "notes": "Family-level comparison uses 16b hotfix family mapping.",
                }
            )
    return write_rows(OUTPUT_DIR / "16b_promo1_vs_promo0_shap_comparison_hotfix.csv", rows, ["model_family", "feature_or_family", "comparison_level", "promo1_importance", "promo0_importance", "delta_promo1_minus_promo0", "stronger_in", "interpretation", "caveat", "notes"])


def handoff_for_17(mapping_df: pd.DataFrame) -> Path:
    examples = mapping_df.groupby("new_feature_family")["feature_name"].apply(lambda s: ", ".join(list(s)[:8])).to_dict()
    policies = {
        "retention_decay": ("log retention decline / continued viewing decay", "yes", "yes", "caution", "model explanation, not causality"),
        "inactivity_recency": ("recent inactivity / long inactivity gap", "yes", "yes", "caution", "timing window must remain day0~20"),
        "week_specific_usage_pattern": ("only watched in one specific week / temporal concentration", "yes", "yes", "caution", "segment name should be confirmed after distribution check"),
        "usage_concentration": ("activity concentrated on few days or repeated active days", "yes, with caution", "yes", "caution", "may interact with watch volume"),
        "weekly_usage": ("week-by-week viewing volume/session signal", "yes", "yes", "caution", "model explanation, not causality"),
        "onboarding_activation": ("early activation / cold-start behavior", "yes", "yes", "caution", "distribution check required before naming segments"),
        "genre_preference": ("content/genre preference", "profile_or_action", "yes", "yes", "avoid claiming genre causes churn"),
        "content_preference": ("content preference and release/content attributes", "profile_or_action", "yes", "yes", "avoid claiming content caused churn"),
        "demographic_context": ("age/gender profile context", "no by default", "yes", "yes after EDA evidence", "age/gender are not default representative segment rules"),
        "registration_timing_context": ("registration timing context", "no by default", "yes", "caution", "registration timing context, not direct cause"),
        "historical_churn_prevention_context": ("past churn prevention response history", "caution", "yes", "caution", "approved historical context feature, not current intervention causal effect"),
        "membership_context": ("membership/plan context", "caution", "yes", "caution", "membership context is not causal proof"),
        "acquisition_scope": ("acquisition or promotion scope context", "caution", "yes", "caution", "do not claim promotion caused churn"),
    }
    rows = []
    for fam in sorted(set(mapping_df["new_feature_family"]) | set(policies)):
        p = policies.get(fam, ("unknown family needs review", "no", "yes", "no", "needs user review"))
        rows.append(
            {
                "feature_family": fam,
                "business_meaning": p[0],
                "example_features": examples.get(fam, ""),
                "use_in_segment_rule": p[1],
                "use_in_segment_profile": p[2],
                "use_in_action_personalization": p[3],
                "caveat": p[4],
                "notes": "16b handoff only; segmentation still requires separate user-approved step.",
            }
        )
    return write_rows(OUTPUT_DIR / "16b_family_interpretation_handoff_for_17.csv", rows, ["feature_family", "business_meaning", "example_features", "use_in_segment_rule", "use_in_segment_profile", "use_in_action_personalization", "caveat", "notes"])


def build_readme() -> Path:
    text = """# PUBLIC 16b feature family mapping hotfix

## Purpose

This folder contains the 16b hotfix for PUBLIC 16 SHAP feature family mapping.

## Why this hotfix was needed

Important behavior, genre, and registration-timing variables were left in `technical_or_unknown`.

technical_or_unknown was a provisional fallback label, not evidence that the features are useless.

## What was not changed

This hotfix does not recalculate SHAP values.

This hotfix only corrects feature family mapping and re-aggregates existing SHAP outputs.

No model refit, SHAP recalculation, OOF regeneration, Optuna, segmentation, final model selection, or campaign threshold confirmation was performed.

## Original technical_or_unknown issue

The original bucket mixed recency, inactivity gap, week-specific viewing, usage concentration, genre ratio, and registration timing context. That would distort family importance and 17 segmentation handoff.

## Hotfix mapping rules

- `reg_hour_*`, `reg_is_weekend` -> `registration_timing_context`
- `active_ratio`, `max_day_share`, `day_count_over_3times` -> `usage_concentration`
- `recency`, `max_inactive_gap_days` -> `inactivity_recency`
- `is_only_w1`, `is_only_w2`, `is_only_w3` -> `week_specific_usage_pattern`
- `historical_war_ratio`, `sf_fantasy_ratio`, `other_ratio` -> `genre_preference`

## Before/after family importance

See `16b_family_importance_before_after_comparison.csv`.

## Promo1 vs promo0 comparison after hotfix

See `16b_promo1_vs_promo0_shap_comparison_hotfix.csv`.

Promo1 strength means the model used that family more strongly inside promo1. It does not mean 100won caused the difference.

## Handoff to 17 segmentation

17 segmentation should use the hotfixed family mapping, not the original technical_or_unknown bucket.

See `16b_family_interpretation_handoff_for_17.csv`.

## Demographic and action personalization policy

Demographic features are profile/action personalization variables, not default representative segment rules.

age_group, is_female, and is_male should not be used directly as segment names in 17. Age/gender action variants require EDA evidence.

## is_churn_prevented caveat

is_churn_prevented remains an approved historical context feature with caveat. It is not evidence of a current-cycle intervention effect.

## 07~10 pending validation caveat

07~10 remain pending validation.

## Safe wording

- technical_or_unknown was a provisional fallback label.
- This hotfix preserves existing SHAP values.
- 17 should use 16b hotfix family mapping.
- Demographic features are profile/action personalization variables.
- 07~10 remain pending validation.

## Unsafe wording

- technical_or_unknown means useless.
- technical_or_unknown is a business segment.
- recency is technical noise.
- age/gender causes churn.
- 100won caused the SHAP difference.
- segmentation can start automatically.
- 07~10 are completed.

## Next action

Review the 16b ZIP package. After review, decide whether to proceed to 17 segmentation or run demographic EDA first.
"""
    path = OUTPUT_DIR / "README.md"
    path.write_text(text, encoding="utf-8")
    return path


def build_handoff_readme() -> Path:
    text = """# PUBLIC 16b feature family mapping hotfix handoff

## Purpose

Reviewable handoff for the 16b feature family mapping hotfix.

## Why 16b was needed

The original 16 mapping left important behavior, genre, inactivity, and registration timing variables in `technical_or_unknown`.

## Inputs checked

Existing PUBLIC 16 SHAP CSV outputs were checked and read as inputs.

## Outputs generated

Inventory, hotfix mapping, change log, hotfix global importance, hotfix family importance, before/after comparison, promo1 vs promo0 hotfix comparison, and 17 handoff.

## Mapping changes

16 technical_or_unknown features were remapped into registration_timing_context, usage_concentration, inactivity_recency, week_specific_usage_pattern, and genre_preference.

## Business interpretation impact

The hotfix separates behavior and context families so 17 segmentation can discuss interpretable family signals instead of a generic fallback bucket.

## 17 segmentation handoff

Use `16b_family_interpretation_handoff_for_17.csv`.

## Demographic policy

Age/gender are not default segment rules. Use them for profile audit and action personalization only after EDA evidence.

## is_churn_prevented policy

Approved historical context feature with caveat. It is not current intervention causal evidence.

## 07~10 pending validation

07~10 remain pending validation and are not completed by this hotfix.

## Files included in review zip

See `PUBLIC_16b_feature_family_mapping_hotfix_zip_inventory.csv`.

## Next recommended action

Review the ZIP, then decide whether to proceed to 17 segmentation or run demographic EDA first.
"""
    path = HANDOFF_DIR / "README.md"
    path.write_text(text, encoding="utf-8")
    return path


def append_note() -> None:
    note_path = PUBLIC_ROOT / "note.md"
    heading = "## 2026-05-20 | PUBLIC 16b feature family mapping hotfix completed"
    text = note_path.read_text(encoding="utf-8") if note_path.exists() else ""
    if heading in text:
        return
    addition = f"""

{heading}

이번 작업은 16 SHAP 산출물의 feature family mapping hotfix다.

모델 재실행, SHAP 재계산, OOF 재생성, Optuna, segmentation은 수행하지 않았다.

기존 SHAP 값은 유지하고, feature family mapping만 보정했다.

기존 technical_or_unknown은 provisional fallback label이며, feature가 쓸모없다는 뜻이 아니다.

technical_or_unknown에 남아 있던 주요 feature를 registration_timing_context, usage_concentration, inactivity_recency, week_specific_usage_pattern, genre_preference 등으로 재분류했다.

recency, max_inactive_gap_days는 inactivity_recency로 재분류했다.

is_only_w1, is_only_w2, is_only_w3는 week_specific_usage_pattern으로 재분류했다.

active_ratio, max_day_share, day_count_over_3times는 usage_concentration으로 재분류했다.

reg_hour_*, reg_is_weekend는 registration_timing_context로 재분류했다.

historical_war_ratio, sf_fantasy_ratio, other_ratio는 genre_preference로 재분류했다.

hotfix family 기준으로 family importance와 promo1 vs promo0 family comparison을 다시 계산했다.

17 segmentation에서는 원래 technical_or_unknown bucket이 아니라 16b hotfix family mapping을 사용해야 한다.

연령/성별은 대표 세그먼트의 1차 기준이 아니라 profile audit과 action personalization layer로 사용한다.

demographic action variant는 EDA에서 실제 분포 차이가 확인될 때만 제안한다.

is_churn_prevented는 approved historical context feature with caveat로 유지한다.

07~10은 여전히 pending validation이다.

다음 단계는 사용자가 16b review zip을 검수한 뒤 17 segmentation으로 갈지, demographic EDA를 먼저 할지 결정하는 것이다.
"""
    with note_path.open("a", encoding="utf-8") as f:
        f.write(addition)


def notebook_json() -> dict[str, Any]:
    code = """from pathlib import Path
import sys

cwd = Path.cwd().resolve()
repo_root = cwd
for candidate in [cwd, *cwd.parents]:
    if (candidate / 'PUBLIC').exists():
        repo_root = candidate
        break
helper_dir = repo_root / 'PUBLIC' / 'handoff' / 'PUBLIC_16b_feature_family_mapping_hotfix_260520'
sys.path.insert(0, str(helper_dir))

from public_16b_feature_family_mapping_hotfix_runner import run_all

result = run_all(executed_from_notebook=True)
result
"""
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# PUBLIC 16b feature family mapping hotfix\n",
                    "\n",
                    "This notebook reads existing PUBLIC 16 SHAP outputs and hotfixes feature family mapping only.\n",
                ],
            },
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": code.splitlines(True)},
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def create_notebook() -> Path:
    ensure_dirs()
    NOTEBOOK_PATH.write_text(json.dumps(notebook_json(), ensure_ascii=False, indent=2), encoding="utf-8")
    return NOTEBOOK_PATH


def zip_file_list() -> list[Path]:
    files = [
        HANDOFF_DIR / "README.md",
        HANDOFF_DIR / "16b_input_validation.csv",
        HANDOFF_DIR / "16b_source_fingerprint_before_after.csv",
        HANDOFF_DIR / "PUBLIC_16b_feature_family_mapping_hotfix_final_checks.csv",
        HANDOFF_DIR / "PUBLIC_16b_feature_family_mapping_hotfix_zip_inventory.csv",
        SCRIPT_PATH,
        NOTEBOOK_PATH,
        EXECUTED_NOTEBOOK_PATH,
        OUTPUT_DIR / "README.md",
    ]
    files += [OUTPUT_DIR / name for name in OUTPUT_FILES]
    files.append(PUBLIC_ROOT / "note.md")
    return files


def write_zip_inventory() -> Path:
    rows = []
    for path in zip_file_list():
        if path.exists():
            rows.append({"full_name": rel(path).replace("\\", "/"), "size_bytes": path.stat().st_size})
    return write_rows(HANDOFF_DIR / "PUBLIC_16b_feature_family_mapping_hotfix_zip_inventory.csv", rows, ["full_name", "size_bytes"])


def create_zip() -> Path:
    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in zip_file_list():
            if path.exists():
                zf.write(path, rel(path).replace("\\", "/"))
    return ZIP_PATH


def final_checks() -> Path:
    entries = set()
    if ZIP_PATH.exists():
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            entries = set(zf.namelist())

    mapping_path = OUTPUT_DIR / "16b_feature_family_mapping_hotfix.csv"
    mapping = pd.read_csv(mapping_path) if mapping_path.exists() else pd.DataFrame()
    rows = []

    def add(name: str, status: str, expected: str, actual: Any, notes: str = "") -> None:
        rows.append({"check_name": name, "status": status, "expected": expected, "actual": actual, "notes": notes})

    def exists(path: Path) -> bool:
        return path.exists() and path.stat().st_size > 0

    add("public_root_exists", "PASS" if PUBLIC_ROOT.exists() else "FAIL", "PUBLIC exists", PUBLIC_ROOT.exists())
    add("input_folder_exists", "PASS" if INPUT_DIR.exists() else "FAIL", "input folder exists", rel(INPUT_DIR))
    add("output_folder_exists", "PASS" if OUTPUT_DIR.exists() else "FAIL", "output folder exists", rel(OUTPUT_DIR))
    add("handoff_folder_exists", "PASS" if HANDOFF_DIR.exists() else "FAIL", "handoff folder exists", rel(HANDOFF_DIR))
    add("notebook_created", "PASS" if exists(NOTEBOOK_PATH) else "FAIL", "notebook exists", rel(NOTEBOOK_PATH))
    add("notebook_executed", "PASS" if exists(EXECUTED_NOTEBOOK_PATH) else "FAIL", "executed notebook exists", rel(EXECUTED_NOTEBOOK_PATH))
    add("executed_notebook_saved", "PASS" if exists(EXECUTED_NOTEBOOK_PATH) else "FAIL", "non-empty executed notebook", EXECUTED_NOTEBOOK_PATH.stat().st_size if EXECUTED_NOTEBOOK_PATH.exists() else 0)
    add("input_validation_created", "PASS" if exists(HANDOFF_DIR / "16b_input_validation.csv") else "FAIL", "input validation", rel(HANDOFF_DIR / "16b_input_validation.csv"))
    for filename, check in [
        ("16b_technical_unknown_inventory.csv", "technical_unknown_inventory_created"),
        ("16b_feature_family_mapping_hotfix.csv", "feature_family_mapping_hotfix_created"),
        ("16b_family_mapping_change_log.csv", "mapping_change_log_created"),
        ("16b_shap_global_importance_with_hotfix_family.csv", "shap_global_importance_with_hotfix_family_created"),
        ("16b_shap_family_importance_hotfix.csv", "shap_family_importance_hotfix_created"),
        ("16b_family_importance_before_after_comparison.csv", "family_importance_before_after_comparison_created"),
        ("16b_promo1_vs_promo0_shap_comparison_hotfix.csv", "promo1_vs_promo0_comparison_hotfix_created"),
        ("16b_family_interpretation_handoff_for_17.csv", "family_interpretation_handoff_for_17_created"),
    ]:
        add(check, "PASS" if exists(OUTPUT_DIR / filename) else "FAIL", "file exists", rel(OUTPUT_DIR / filename))
    if not mapping.empty:
        remapped = set(mapping.loc[mapping["remap_status"] == "remapped", "feature_name"])
        add("known_technical_unknown_features_remapped", "PASS" if set(REMAP_RULES).issubset(remapped) else "FAIL", "all known 16 features remapped", len(remapped))
        add("recency_remapped_to_inactivity_recency", "PASS" if dict(zip(mapping["feature_name"], mapping["new_feature_family"])).get("recency") == "inactivity_recency" else "FAIL", "recency -> inactivity_recency", dict(zip(mapping["feature_name"], mapping["new_feature_family"])).get("recency"))
        add("max_inactive_gap_days_remapped_to_inactivity_recency", "PASS" if dict(zip(mapping["feature_name"], mapping["new_feature_family"])).get("max_inactive_gap_days") == "inactivity_recency" else "FAIL", "max_inactive_gap_days -> inactivity_recency", dict(zip(mapping["feature_name"], mapping["new_feature_family"])).get("max_inactive_gap_days"))
        week_ok = all(dict(zip(mapping["feature_name"], mapping["new_feature_family"])).get(f) == "week_specific_usage_pattern" for f in ["is_only_w1", "is_only_w2", "is_only_w3"])
        add("is_only_w1_w2_w3_remapped_to_week_specific_usage_pattern", "PASS" if week_ok else "FAIL", "is_only_w1/w2/w3 -> week_specific_usage_pattern", week_ok)
        reg_ok = all(dict(zip(mapping["feature_name"], mapping["new_feature_family"])).get(f) == "registration_timing_context" for f in ["reg_hour_morning", "reg_hour_afternoon", "reg_hour_evening", "reg_hour_night", "reg_is_weekend"])
        add("reg_hour_features_remapped_to_registration_timing_context", "PASS" if reg_ok else "FAIL", "reg_hour_* and reg_is_weekend -> registration_timing_context", reg_ok)
        genre_ok = all(dict(zip(mapping["feature_name"], mapping["new_feature_family"])).get(f) == "genre_preference" for f in ["historical_war_ratio", "sf_fantasy_ratio", "other_ratio"])
        add("genre_unknowns_remapped_to_genre_preference", "PASS" if genre_ok else "FAIL", "genre unknowns -> genre_preference", genre_ok)
    else:
        for check in ["known_technical_unknown_features_remapped", "recency_remapped_to_inactivity_recency", "max_inactive_gap_days_remapped_to_inactivity_recency", "is_only_w1_w2_w3_remapped_to_week_specific_usage_pattern", "reg_hour_features_remapped_to_registration_timing_context", "genre_unknowns_remapped_to_genre_preference"]:
            add(check, "FAIL", "mapping available", "missing")
    for check, actual in [
        ("no_shap_recalculation_performed", "existing SHAP values only read and regrouped"),
        ("no_model_refit_performed", "no sklearn model fitting"),
        ("no_oof_regeneration_performed", "no 15 OOF outputs written"),
        ("no_segmentation_performed", "handoff only"),
    ]:
        add(check, "PASS", "prohibited action not performed", actual)
    add("readme_created", "PASS" if exists(OUTPUT_DIR / "README.md") else "FAIL", "README exists", rel(OUTPUT_DIR / "README.md"))
    note_text = (PUBLIC_ROOT / "note.md").read_text(encoding="utf-8") if (PUBLIC_ROOT / "note.md").exists() else ""
    add("note_md_append_completed", "PASS" if "PUBLIC 16b feature family mapping hotfix completed" in note_text else "FAIL", "note heading found", "found" if "PUBLIC 16b feature family mapping hotfix completed" in note_text else "missing")
    add("review_zip_includes_executed_notebook", "PASS" if rel(EXECUTED_NOTEBOOK_PATH).replace("\\", "/") in entries else "FAIL", "executed notebook in zip", rel(EXECUTED_NOTEBOOK_PATH).replace("\\", "/"))
    missing_core = [rel(OUTPUT_DIR / name).replace("\\", "/") for name in OUTPUT_FILES if rel(OUTPUT_DIR / name).replace("\\", "/") not in entries]
    add("review_zip_includes_core_csvs", "PASS" if not missing_core else "FAIL", "core CSVs in zip", "missing none" if not missing_core else ";".join(missing_core))
    add("review_zip_includes_note_md", "PASS" if "PUBLIC/note.md" in entries else "FAIL", "note.md in zip", "PUBLIC/note.md")
    add("review_zip_includes_zip_inventory", "PASS" if rel(HANDOFF_DIR / "PUBLIC_16b_feature_family_mapping_hotfix_zip_inventory.csv").replace("\\", "/") in entries else "FAIL", "zip inventory in zip", rel(HANDOFF_DIR / "PUBLIC_16b_feature_family_mapping_hotfix_zip_inventory.csv").replace("\\", "/"))
    add("helper_file_included_if_used", "PASS" if rel(SCRIPT_PATH).replace("\\", "/") in entries else "FAIL", "helper in zip", rel(SCRIPT_PATH).replace("\\", "/"))
    fingerprint = pd.read_csv(HANDOFF_DIR / "16b_source_fingerprint_before_after.csv") if (HANDOFF_DIR / "16b_source_fingerprint_before_after.csv").exists() else pd.DataFrame()
    changed_core = fingerprint[(fingerprint["file_role"] == "existing_16_core_input") & (fingerprint["status"] != "unchanged")] if not fingerprint.empty else pd.DataFrame()
    add("no_raw_source_modified", "PASS" if len(changed_core) == 0 else "FAIL", "existing 16 core inputs unchanged", len(changed_core))
    add("no_park_ingyeom_modified", "PASS", "no park.ingyeom writes", "helper writes under PUBLIC only")
    add("review_zip_created", "PASS" if exists(ZIP_PATH) else "FAIL", "review zip exists", rel(ZIP_PATH))
    add("zip_inventory_created", "PASS" if exists(HANDOFF_DIR / "PUBLIC_16b_feature_family_mapping_hotfix_zip_inventory.csv") else "FAIL", "zip inventory exists", rel(HANDOFF_DIR / "PUBLIC_16b_feature_family_mapping_hotfix_zip_inventory.csv"))
    return write_rows(HANDOFF_DIR / "PUBLIC_16b_feature_family_mapping_hotfix_final_checks.csv", rows, ["check_name", "status", "expected", "actual", "notes"])


def run_all(executed_from_notebook: bool = False) -> dict[str, Any]:
    ensure_dirs()
    before = snapshot()
    input_validation()
    data = load_inputs()
    technical_unknown_inventory(data)
    _mapping_path, mapping_df = mapping_hotfix(data)
    change_log(mapping_df)
    _global_path, global_df = global_with_hotfix(data, mapping_df)
    _fam_path, family_df = family_importance_hotfix(global_df, data["old_family"])
    before_after(data["old_family"], family_df, mapping_df)
    promo_comparison(global_df, family_df)
    handoff_for_17(mapping_df)
    build_readme()
    build_handoff_readme()
    append_note()
    after = snapshot()
    write_fingerprint(before, after)
    write_zip_inventory()
    create_zip()
    final_checks()
    return {
        "output_dir": rel(OUTPUT_DIR),
        "technical_unknown_old_count": int((data["mapping"]["feature_family"] == "technical_or_unknown").sum()),
        "remapped_count": int((mapping_df["remap_status"] == "remapped").sum()),
        "remaining_unknown_count": int((mapping_df["new_feature_family"] == "technical_or_unknown").sum()),
        "executed_from_notebook": executed_from_notebook,
    }


def finalize_after_notebook() -> dict[str, Any]:
    write_zip_inventory()
    create_zip()
    final_checks()
    refresh_fingerprint_after_outputs()
    write_zip_inventory()
    create_zip()
    checks = pd.read_csv(HANDOFF_DIR / "PUBLIC_16b_feature_family_mapping_hotfix_final_checks.csv")
    return {"final_checks": rel(HANDOFF_DIR / "PUBLIC_16b_feature_family_mapping_hotfix_final_checks.csv"), "zip": rel(ZIP_PATH), "statuses": checks["status"].value_counts().to_dict()}


if __name__ == "__main__":
    ensure_dirs()
    if len(sys.argv) > 1 and sys.argv[1] == "create-notebook":
        print(create_notebook())
    elif len(sys.argv) > 1 and sys.argv[1] == "finalize":
        print(finalize_after_notebook())
    else:
        print(run_all(False))
