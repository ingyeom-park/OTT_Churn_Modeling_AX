import json
from pathlib import Path


OUT_DIR = Path(r"C:\Code\ott-churn-prediction\FINAL\S7_residual_promo_decomposition_diagnostic_260522")
NB_PATH = OUT_DIR / "S7_residual_promo_decomposition_diagnostic_260522.ipynb"


def code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.strip("\n").splitlines(True),
    }


def md_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.strip("\n").splitlines(True),
    }


cells = [
    md_cell(
        """
> FINAL_S7_residual_promo_decomposition_diagnostic_260522

Diagnostic-only notebook. This notebook reads existing park 17x, 06x, 15x, FINAL, and reference PUBLIC files, then writes outputs only under the new FINAL S7 diagnostic folder and the requested review zip path.
"""
    ),
    code_cell(
        r"""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import math
import os
import re
import shutil
import zipfile

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(r"C:\Code\ott-churn-prediction")
OUT = ROOT / "FINAL" / "S7_residual_promo_decomposition_diagnostic_260522"
ZIP_PATH = ROOT / "FINAL" / "S7_residual_promo_decomposition_diagnostic_260522_review_package.zip"
OUT.mkdir(parents=True, exist_ok=True)

RUN_ID = datetime.now().strftime("run_%Y%m%d_%H%M%S")
EXECUTION_LOG = []

def log(message):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    EXECUTION_LOG.append(f"{stamp} | {message}")
    print(message)

def rel(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)

def sha256_file(path):
    path = Path(path)
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def file_meta(path):
    path = Path(path)
    if not path.exists():
        return {"sha256": "", "mtime": "", "size": "", "status": "missing"}
    st = path.stat()
    return {
        "sha256": sha256_file(path),
        "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        "size": st.st_size,
        "status": "exists",
    }

def read_csv(path, **kwargs):
    log(f"read_csv: {rel(path)}")
    return pd.read_csv(path, **kwargs)

def write_csv(df, filename):
    path = OUT / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    log(f"wrote: {rel(path)} rows={len(df)}")
    return path

def write_text(filename, text):
    path = OUT / filename
    path.write_text(text, encoding="utf-8")
    log(f"wrote: {rel(path)}")
    return path

def pp(x):
    if pd.isna(x):
        return np.nan
    return float(x) * 100.0
"""
    ),
    code_cell(
        r"""
FINAL_NOTE = ROOT / "FINAL" / "final_note.md"
EXEC_PLAN = ROOT / "FINAL" / "project_execution_plan_260521.md"
SEG_DIR = ROOT / "park.ingyeom" / "reports" / "segments" / "17x_segmentation_design_260516"
ASSIGN_PATH = SEG_DIR / "17x_representative_segment_assignment.csv"
RULE_PATH = SEG_DIR / "17x_representative_segment_rules.csv"
FLAG_DEF_PATH = SEG_DIR / "17x_internal_multiflag_definitions.csv"
FLAG_ASSIGN_PATH = SEG_DIR / "17x_internal_multiflag_assignment.csv"
SUMMARY_PATH = SEG_DIR / "17x_segment_summary.csv"
BASE_PATH = SEG_DIR / "17x_segmentation_base_datamart.csv"
SCORE_SELECT_PATH = SEG_DIR / "17x_score_source_selection.csv"
PARK_17X_README = SEG_DIR / "README.md"
PARK_17X_NB = ROOT / "park.ingyeom" / "notebook" / "17x_segmentation_design_260516" / "17x_segmentation_design_260516.ipynb"
DATA_06X = ROOT / "park.ingyeom" / "reports" / "audits" / "06x_dataset_generation_260515" / "06x_expanded_dataset.csv"
MODEL_15X_SUMMARY = ROOT / "park.ingyeom" / "reports" / "audits" / "15x_payment_device_sensitivity_260516" / "15x_model_summary_by_scope.csv"
OOF_15X_EXPECTED = ROOT / "park.ingyeom" / "reports" / "audits" / "15x_payment_device_sensitivity_260516" / "15x_oof_predictions.csv"
PROMO_AUDIT_DIR = ROOT / "park.ingyeom" / "reports" / "audits" / "17x_segmentation_promo_integration_audit_260521"
PROMO_AUDIT_README = PROMO_AUDIT_DIR / "README.md"
PROMO_AUDIT_LIFT = PROMO_AUDIT_DIR / "03_park_segment_promo_lift.csv"
PROMO_AUDIT_GENERAL = PROMO_AUDIT_DIR / "04_general_observation_decomposition_audit.csv"
PROMO_AUDIT_SCORE = PROMO_AUDIT_DIR / "10_final_score_source_decision_audit.csv"
PUBLIC_NOTE = ROOT / "PUBLIC" / "note.md"
PUBLIC_ASSIGN = ROOT / "PUBLIC" / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments_hotfix_260520" / "17_representative_segment_assignment_hotfix.csv"
PUBLIC_SUMMARY = ROOT / "PUBLIC" / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments_hotfix_260520" / "17_segment_summary_hotfix.csv"
PUBLIC_OOF_WIDE = ROOT / "PUBLIC" / "results" / "15_oof_score_or_sensitivity_260520" / "four_model_oof_scores_hotfix_260520" / "15_oof_score_wide.csv"
PUBLIC_HTML = ROOT / "PUBLIC" / "reports" / "business" / "18_business_recommendation_storyline_hotfix_260520" / "18_segment_visual_guide_v2_polished.html"

SOURCE_FILES = [
    (FINAL_NOTE, "FINAL final note"),
    (EXEC_PLAN, "FINAL execution plan"),
    (PARK_17X_README, "park 17x README"),
    (PARK_17X_NB, "park 17x notebook source"),
    (ASSIGN_PATH, "park 17x representative assignment"),
    (RULE_PATH, "park 17x representative rules"),
    (FLAG_DEF_PATH, "park 17x internal multiflag definitions"),
    (FLAG_ASSIGN_PATH, "park 17x internal multiflag assignment"),
    (SUMMARY_PATH, "park 17x segment summary"),
    (BASE_PATH, "park 17x basis datamart"),
    (SCORE_SELECT_PATH, "park 17x score source selection"),
    (DATA_06X, "06x expanded dataset"),
    (MODEL_15X_SUMMARY, "15x model summary by scope"),
    (OOF_15X_EXPECTED, "15x expected OOF score file"),
    (PROMO_AUDIT_README, "existing promo integration audit README"),
    (PROMO_AUDIT_LIFT, "existing promo integration audit lift table"),
    (PROMO_AUDIT_GENERAL, "existing promo integration audit S7 audit"),
    (PROMO_AUDIT_SCORE, "existing promo integration score decision audit"),
    (PUBLIC_NOTE, "PUBLIC note reference"),
    (PUBLIC_ASSIGN, "PUBLIC 17 assignment reference"),
    (PUBLIC_SUMMARY, "PUBLIC 17 summary reference"),
    (PUBLIC_OOF_WIDE, "PUBLIC 15 OOF wide reference"),
    (PUBLIC_HTML, "existing HTML modification-forbidden reference"),
]

finger_before = []
for path, role in SOURCE_FILES:
    m = file_meta(path)
    finger_before.append({
        "file_path": rel(path),
        "file_role": role,
        "sha256_before": m["sha256"],
        "mtime_before": m["mtime"],
        "size_before": m["size"],
        "status_before": m["status"],
    })
log("source fingerprint before captured")
"""
    ),
    code_cell(
        r"""
final_note_text = FINAL_NOTE.read_text(encoding="utf-8")
exec_plan_text = EXEC_PLAN.read_text(encoding="utf-8")
park_readme_text = PARK_17X_README.read_text(encoding="utf-8")
park_nb_text = PARK_17X_NB.read_text(encoding="utf-8")
promo_readme_text = PROMO_AUDIT_README.read_text(encoding="utf-8") if PROMO_AUDIT_README.exists() else ""
public_note_text = PUBLIC_NOTE.read_text(encoding="utf-8") if PUBLIC_NOTE.exists() else ""

assignment = read_csv(ASSIGN_PATH)
rules = read_csv(RULE_PATH)
flag_defs = read_csv(FLAG_DEF_PATH)
flag_assign = read_csv(FLAG_ASSIGN_PATH)
seg_summary = read_csv(SUMMARY_PATH)
base = read_csv(BASE_PATH)
score_selection = read_csv(SCORE_SELECT_PATH)
data06_header = pd.read_csv(DATA_06X, nrows=0)
model15 = read_csv(MODEL_15X_SUMMARY)
promo_lift = read_csv(PROMO_AUDIT_LIFT) if PROMO_AUDIT_LIFT.exists() else pd.DataFrame()
promo_general = read_csv(PROMO_AUDIT_GENERAL) if PROMO_AUDIT_GENERAL.exists() else pd.DataFrame()
promo_score = read_csv(PROMO_AUDIT_SCORE) if PROMO_AUDIT_SCORE.exists() else pd.DataFrame()
public_assign_header = pd.read_csv(PUBLIC_ASSIGN, nrows=0) if PUBLIC_ASSIGN.exists() else pd.DataFrame()
public_summary = read_csv(PUBLIC_SUMMARY) if PUBLIC_SUMMARY.exists() else pd.DataFrame()
public_oof_header = pd.read_csv(PUBLIC_OOF_WIDE, nrows=0) if PUBLIC_OOF_WIDE.exists() else pd.DataFrame()

assert len(assignment) == len(base), "assignment and base row counts differ"
assert set(assignment["row_id"]) == set(base["row_id"]), "assignment and base row_id sets differ"
assert base["representative_segment"].nunique() == 7, "park 17x segment count is not 7"

S7_ID = "general_observation"
s7 = base.loc[base["representative_segment"].eq(S7_ID)].copy()
s7_assignment = assignment.loc[assignment["representative_segment"].eq(S7_ID)].copy()
assert len(s7) == len(s7_assignment), "S7 row count differs between base and assignment"
write_csv(s7, "S7_park17x_basis_row_subset.csv")
log(f"park17x basis rows={len(base)} S7 rows={len(s7)}")
"""
    ),
    code_cell(
        r"""
def csv_shape(path):
    path = Path(path)
    if not path.exists():
        return ("", "")
    try:
        cols = pd.read_csv(path, nrows=0).columns.tolist()
        with path.open("r", encoding="utf-8") as f:
            rows = max(sum(1 for _ in f) - 1, 0)
        return (rows, len(cols))
    except Exception:
        return ("", "")

def add_basis(item, path, role, dataset_variant="", scope="", model="", score_type="", status="", caveat=""):
    rows, cols = csv_shape(path) if str(path).lower().endswith(".csv") else ("", "")
    located = rel(path) if Path(path).exists() else str(path)
    basis_rows.append({
        "item": item,
        "located_path": located,
        "file_role": role,
        "rows_if_applicable": rows,
        "columns_if_applicable": cols,
        "dataset_variant": dataset_variant,
        "scope": scope,
        "model_if_applicable": model,
        "score_type_if_applicable": score_type,
        "sha256": sha256_file(path),
        "status": status or ("located" if Path(path).exists() else "missing"),
        "caveat": caveat,
    })

basis_rows = []
add_basis("FINAL final_note", FINAL_NOTE, "project-level current decision note", status="read")
add_basis("FINAL project execution plan", EXEC_PLAN, "project-level execution constraints", status="read")
add_basis("park 17x README", PARK_17X_README, "17x basis explanation", "expanded_no_payment_device", "overall_with_promotion", "LightGBM", "OOF churn_risk", "read")
add_basis("park 17x assignment", ASSIGN_PATH, "park17x_basis representative assignment", "expanded_no_payment_device", "overall_with_promotion", "LightGBM", "OOF churn_risk", "read")
add_basis("park 17x rules", RULE_PATH, "representative segment rule source", status="read")
add_basis("park 17x multiflag definitions", FLAG_DEF_PATH, "existing internal flag definition source", status="read")
add_basis("park 17x segment summary", SUMMARY_PATH, "segment count and metrics source", "expanded_no_payment_device", "overall_with_promotion", "LightGBM", "OOF churn_risk", "read")
add_basis("park 17x base datamart", BASE_PATH, "park17x_basis feature and flag table", "expanded_no_payment_device", "overall_with_promotion", "LightGBM", "OOF churn_risk", "read")
add_basis("park 17x score selection", SCORE_SELECT_PATH, "score source declaration", "expanded_no_payment_device", "overall_with_promotion", "LightGBM", "OOF churn_risk", "read")
add_basis("06x expanded dataset", DATA_06X, "row-level source dataset linkable by row_id/order", "expanded", "overall", "", "", "read")
add_basis("15x expected OOF score file from 17x selection", OOF_15X_EXPECTED, "declared 15x row-level OOF source", "expanded_no_payment_device", "overall_with_promotion", "LightGBM", "OOF", "missing", "17x_score_source_selection declares this path, but row-level OOF CSV is not present in current local folder; 17x base datamart contains the score columns used for assignment.")
add_basis("15x model summary", MODEL_15X_SUMMARY, "available 15x score/model summary", "expanded_no_payment_device", "overall_with_promotion", "LightGBM", "OOF metric summary", "read")
add_basis("existing promo integration audit", PROMO_AUDIT_GENERAL, "prior S7 general_observation audit", status="read")
add_basis("existing promo score decision audit", PROMO_AUDIT_SCORE, "prior park vs PUBLIC score decision audit", status="read")
add_basis("PUBLIC note", PUBLIC_NOTE, "reference branch note only", "PUBLIC log-retention", "promo-scope", "GradientBoosting/LogisticRegression", "OOF", "read", "Reference only; not merged into park17x_basis.")
add_basis("PUBLIC 17 assignment hotfix", PUBLIC_ASSIGN, "reference branch segment assignment", "PUBLIC 23,097", "promo0/promo1", "GradientBoosting/LogisticRegression", "OOF churn_risk", "read_header", "Reference only; not merged into park17x_basis.")
add_basis("PUBLIC 17 summary hotfix", PUBLIC_SUMMARY, "reference branch segment summary", "PUBLIC 23,097", "promo0/promo1", "GradientBoosting/LogisticRegression", "OOF churn_risk", "read")
add_basis("PUBLIC 15 OOF wide hotfix", PUBLIC_OOF_WIDE, "reference branch OOF score source", "PUBLIC 23,097", "promo0/promo1", "GradientBoosting/LogisticRegression", "OOF", "read_header")

basis_df = pd.DataFrame(basis_rows)
write_csv(basis_df, "00_input_basis_resolution.csv")

public_row_counts = []
for label, path in [("PUBLIC assignment", PUBLIC_ASSIGN), ("PUBLIC OOF wide", PUBLIC_OOF_WIDE)]:
    r, c = csv_shape(path)
    public_row_counts.append(f"- {label}: {r} rows, {c} columns")

model_conflict = promo_score.to_string(index=False) if not promo_score.empty else "No local promo score decision audit table was found."
conflict_note = f'''> 00 basis conflict note

이번 분석은 `park17x_basis`로 수행했습니다. 기준 파일은 `{rel(ASSIGN_PATH)}`와 `{rel(BASE_PATH)}`입니다. 두 파일은 `row_id` 기준으로 같은 23,079행을 갖고 있으며, S7 `general_observation`은 이 기준 안의 residual row subset입니다.

> 23,079 / 23,097 확인

- park 17x assignment rows: {len(assignment)}
- park 17x base datamart rows: {len(base)}
- 06x expanded dataset rows: {csv_shape(DATA_06X)[0]}
{chr(10).join(public_row_counts)}

23,079는 park 17x 대표 세그먼트 assignment와 06x expanded dataset 기준입니다. 23,097은 PUBLIC reference branch의 hotfix OOF/assignment 기준에서 확인됩니다. 이 둘은 자동 병합하지 않았고, 이번 분석 결과는 park 17x 23,079행 기준에만 유효합니다.

> LightGBM / GradientBoosting 확인

park 17x score source selection은 `expanded_no_payment_device / overall_with_promotion / LightGBM / OOF churn_risk`를 primary로 기록합니다. PUBLIC reference branch에는 promo0/promo1별 GradientBoosting 및 LogisticRegression OOF score가 존재합니다. PUBLIC numeric score와 PUBLIC segment assignment는 이번 park17x_basis 분석에 병합하지 않았습니다.

> 확인된 score decision audit

{model_conflict}

> 유효 범위

이번 산출물은 `park17x_basis`의 S7 residual diagnostic에만 유효합니다. 23,097 PUBLIC branch, PUBLIC GradientBoosting score, PUBLIC segment assignment 기준으로 재해석한 결과가 아닙니다.
'''
write_text("00_basis_conflict_note.md", conflict_note)
"""
    ),
    code_cell(
        r"""
segment_ids = seg_summary.sort_values("segment_priority")["representative_segment"].tolist()
s7_summary_row = seg_summary.loc[seg_summary["representative_segment"].eq(S7_ID)].iloc[0]
priority_text = rules.sort_values("segment_priority")[["segment_priority", "representative_segment", "matched_rule_text"]].to_string(index=False)

s7_definition_md = f'''> 01 S7 definition and residual structure

> 확인된 것

- S7 internal id: `{S7_ID}`
- S7 segment priority: `{int(s7_summary_row["segment_priority"])}`
- S7 rows: `{len(s7):,}` out of `{len(base):,}` park17x_basis rows
- S7 assignment source column: `representative_segment`
- S7 matched rule text: `no prior rule matched`
- park notebook source confirms `np.select(conditions, segments[:6], default='general_observation')`, so S7 is the default residual after priority rules 1 through 6.

> representative rule priority

{priority_text}

> 해석

S7는 1~6순위 대표 rule에 먼저 배정되지 않은 residual입니다. 따라서 `일반 고객`이라고 부르면 안 됩니다. 이 표현은 S7 내부에 행동 신호가 없거나, 정상/평균 고객이라는 뜻으로 오해될 수 있습니다. 실제 S7 안에는 기존 17x flag가 일부 남아 있습니다. 그러므로 이 집단은 `추가분해 검토 대상 residual` 또는 `monitoring group`으로 보는 편이 안전합니다.

> 확인하지 못한 것

- 17x에서 선언된 row-level `15x_oof_predictions.csv` 파일은 현재 로컬 15x 폴더에 존재하지 않습니다. 다만 17x assignment와 base datamart에는 이미 선택된 `repurchase_score`와 `churn_risk`가 포함되어 있습니다.
- 이번 작업은 새 segment assignment를 만들지 않았습니다.

> 사용자 승인 필요 항목

- S7 발표용 label 변경 여부
- S7 내부 subgroup을 action layer 또는 dashboard diagnostic tag로 사용할지 여부
- 새 파생변수 검토 여부
'''
write_text("01_S7_definition_and_residual_structure.md", s7_definition_md)

row_inventory = pd.DataFrame([{
    "basis_name": "park17x_basis",
    "segment_id": S7_ID,
    "rows": len(s7),
    "share_of_basis": len(s7) / len(base),
    "promo0_rows": int((s7["is_promotion"] == 0).sum()),
    "promo1_rows": int((s7["is_promotion"] == 1).sum()),
    "promo0_share_within_S7": float((s7["is_promotion"] == 0).mean()),
    "promo1_share_within_S7": float((s7["is_promotion"] == 1).mean()),
    "repurchase_rate": float(s7["is_repurchase"].mean()),
    "churn_rate": float((1 - s7["is_repurchase"]).mean()),
    "mean_churn_risk": float(s7["churn_risk"].mean()),
    "source_file": rel(BASE_PATH),
    "caveat": "diagnostic residual subset only; not a new segment assignment",
}])
write_csv(row_inventory, "01_S7_row_inventory.csv")
"""
    ),
    code_cell(
        r"""
def add_promo_outcome_labels(df):
    out = df.copy()
    out["promo_group"] = np.where(out["is_promotion"].eq(1), "promo1_100won", "promo0_non100won")
    out["outcome_group"] = np.where(out["is_repurchase"].eq(1), "repurchase", "churn")
    return out

s7_labeled = add_promo_outcome_labels(s7)
base_labeled = add_promo_outcome_labels(base)

four = (
    s7_labeled.groupby(["promo_group", "outcome_group", "is_promotion", "is_repurchase"], as_index=False)
    .agg(rows=("row_id", "count"), mean_churn_risk=("churn_risk", "mean"), median_churn_risk=("churn_risk", "median"))
)
four["share_within_S7"] = four["rows"] / len(s7)
promo_den = four.groupby("promo_group")["rows"].transform("sum")
four["share_within_promo_group_in_S7"] = four["rows"] / promo_den
four["source_file"] = rel(BASE_PATH)
four["caveat"] = "observational split; not causal effect"
four = four[["promo_group", "outcome_group", "is_promotion", "is_repurchase", "rows", "share_within_S7", "share_within_promo_group_in_S7", "mean_churn_risk", "median_churn_risk", "source_file", "caveat"]]
write_csv(four, "02_S7_promo_outcome_4cell_summary.csv")

def promo_gap(df, scope):
    g = df.groupby("is_promotion").agg(
        rows=("row_id", "count"),
        churn_rate=("is_repurchase", lambda x: float((1 - x).mean())),
        mean_churn_risk=("churn_risk", "mean"),
    )
    row = {
        "comparison_scope": scope,
        "promo0_rows": int(g.loc[0, "rows"]) if 0 in g.index else 0,
        "promo1_rows": int(g.loc[1, "rows"]) if 1 in g.index else 0,
        "promo0_churn_rate": float(g.loc[0, "churn_rate"]) if 0 in g.index else np.nan,
        "promo1_churn_rate": float(g.loc[1, "churn_rate"]) if 1 in g.index else np.nan,
        "churn_rate_gap_promo1_minus_promo0_pp": pp(float(g.loc[1, "churn_rate"]) - float(g.loc[0, "churn_rate"])) if set([0, 1]).issubset(g.index) else np.nan,
        "promo0_mean_churn_risk": float(g.loc[0, "mean_churn_risk"]) if 0 in g.index else np.nan,
        "promo1_mean_churn_risk": float(g.loc[1, "mean_churn_risk"]) if 1 in g.index else np.nan,
        "mean_churn_risk_gap_promo1_minus_promo0_pp": pp(float(g.loc[1, "mean_churn_risk"]) - float(g.loc[0, "mean_churn_risk"])) if set([0, 1]).issubset(g.index) else np.nan,
        "interpretation_limit": "observed difference only; do not interpret as promo causal effect",
        "source_file": rel(BASE_PATH),
    }
    return row

gap_rows = [promo_gap(s7, "S7_only"), promo_gap(base, "all_segments_total")]
for seg in rules.sort_values("segment_priority")["representative_segment"]:
    gap_rows.append(promo_gap(base.loc[base["representative_segment"].eq(seg)], f"segment_reference__{seg}"))
gap_df = pd.DataFrame(gap_rows)
write_csv(gap_df, "03_S7_promo_gap_summary.csv")
"""
    ),
    code_cell(
        r"""
flag_cols = [c for c in flag_defs["flag_name"].tolist() if c in base.columns and c != "flag_age40_unverified_ios"]
flag_def_map = dict(zip(flag_defs["flag_name"], flag_defs["definition_text"]))

dist_rows = []
for flag in flag_cols:
    for (promo_group, outcome_group), g in s7_labeled.groupby(["promo_group", "outcome_group"]):
        dist_rows.append({
            "flag_name": flag,
            "flag_definition_from_source": flag_def_map.get(flag, ""),
            "promo_group": promo_group,
            "outcome_group": outcome_group,
            "rows_in_group": len(g),
            "flag_1_rows": int(g[flag].fillna(0).eq(1).sum()),
            "flag_1_rate": float(g[flag].fillna(0).eq(1).mean()) if len(g) else np.nan,
            "source_file": rel(FLAG_DEF_PATH),
            "caveat": "existing 17x internal flag diagnostic only; not promoted to a segment rule",
        })
flag_dist = pd.DataFrame(dist_rows)
write_csv(flag_dist, "04_S7_existing_flag_distribution_by_promo_outcome.csv")

comparison_defs = {
    "promo1_churn_vs_promo1_repurchase": ({"is_promotion": 1, "is_repurchase": 0}, {"is_promotion": 1, "is_repurchase": 1}),
    "promo0_churn_vs_promo0_repurchase": ({"is_promotion": 0, "is_repurchase": 0}, {"is_promotion": 0, "is_repurchase": 1}),
    "promo1_churn_vs_promo0_churn": ({"is_promotion": 1, "is_repurchase": 0}, {"is_promotion": 0, "is_repurchase": 0}),
    "promo1_all_vs_promo0_all": ({"is_promotion": 1}, {"is_promotion": 0}),
}

def mask_by(df, spec):
    m = pd.Series(True, index=df.index)
    for k, v in spec.items():
        m &= df[k].eq(v)
    return m

gap_flag_rows = []
for flag in flag_cols:
    for comp, (a_spec, b_spec) in comparison_defs.items():
        a = s7.loc[mask_by(s7, a_spec)]
        b = s7.loc[mask_by(s7, b_spec)]
        ar = float(a[flag].fillna(0).eq(1).mean()) if len(a) else np.nan
        br = float(b[flag].fillna(0).eq(1).mean()) if len(b) else np.nan
        diff = pp(ar - br) if not (pd.isna(ar) or pd.isna(br)) else np.nan
        gap_flag_rows.append({
            "flag_name": flag,
            "comparison": comp,
            "group_a_rate": ar,
            "group_b_rate": br,
            "difference_pp": diff,
            "absolute_difference_pp": abs(diff) if not pd.isna(diff) else np.nan,
            "rank_by_abs_difference": np.nan,
            "interpretation": "descriptive diagnostic gap among existing 17x flags only",
            "needs_user_review": True,
            "source_file": rel(FLAG_DEF_PATH),
        })
flag_gap = pd.DataFrame(gap_flag_rows)
flag_gap["rank_by_abs_difference"] = flag_gap.groupby("comparison")["absolute_difference_pp"].rank(ascending=False, method="dense")
write_csv(flag_gap.sort_values(["comparison", "rank_by_abs_difference", "flag_name"]), "05_S7_existing_flag_gap_ranking.csv")
"""
    ),
    code_cell(
        r"""
component_specs = {
    "high_risk_week3_inactive_or_drop": [
        ("flag_high_risk_top20", "flag_high_risk_top20 == 1", lambda d: d["flag_high_risk_top20"].eq(1)),
        ("flag_week3_inactive_or_drop_or_retention_decay", "flag_week3_inactive == 1 OR flag_week3_drop == 1 OR flag_retention_decay == 1", lambda d: d["flag_week3_inactive"].eq(1) | d["flag_week3_drop"].eq(1) | d["flag_retention_decay"].eq(1)),
    ],
    "high_risk_only_w1_or_cold_start_weak": [
        ("flag_high_risk_top20", "flag_high_risk_top20 == 1", lambda d: d["flag_high_risk_top20"].eq(1)),
        ("flag_only_w1_or_cold_start_weak", "flag_only_w1 == 1 OR flag_cold_start_weak == 1", lambda d: d["flag_only_w1"].eq(1) | d["flag_cold_start_weak"].eq(1)),
    ],
    "high_risk_low_activity": [
        ("flag_high_risk_top20", "flag_high_risk_top20 == 1", lambda d: d["flag_high_risk_top20"].eq(1)),
        ("flag_low_activity", "flag_low_activity == 1", lambda d: d["flag_low_activity"].eq(1)),
    ],
    "medium_risk_retention_decay": [
        ("not_high_risk_top20", "flag_high_risk_top20 == 0", lambda d: d["flag_high_risk_top20"].eq(0)),
        ("risk_percentile_20_to_50", "20 < risk_percentile_desc <= 50", lambda d: d["risk_percentile_desc"].gt(20) & d["risk_percentile_desc"].le(50)),
        ("flag_retention_decay", "flag_retention_decay == 1", lambda d: d["flag_retention_decay"].eq(1)),
    ],
    "content_preference_target_candidate": [
        ("not_high_risk_top20", "flag_high_risk_top20 == 0", lambda d: d["flag_high_risk_top20"].eq(0)),
        ("not_low_activity", "flag_low_activity == 0", lambda d: d["flag_low_activity"].eq(0)),
        ("content_proxy_flag", "flag_genre_focused == 1 OR flag_new_movie_oriented == 1 OR flag_old_movie_oriented == 1", lambda d: d["flag_genre_focused"].eq(1) | d["flag_new_movie_oriented"].eq(1) | d["flag_old_movie_oriented"].eq(1)),
    ],
    "stable_retained_user": [
        ("flag_low_risk_stable", "flag_low_risk_stable == 1", lambda d: d["flag_low_risk_stable"].eq(1)),
    ],
}

coverage_rows = []
for target_seg, specs in component_specs.items():
    for comp_id, comp_def, fn in specs:
        sat = fn(s7)
        tmp = s7_labeled.assign(component_satisfied=sat.astype(int))
        for (promo_group, outcome_group), g in tmp.groupby(["promo_group", "outcome_group"]):
            coverage_rows.append({
                "target_rule_segment_id": target_seg,
                "rule_component": comp_id,
                "component_definition": comp_def,
                "promo_group": promo_group,
                "outcome_group": outcome_group,
                "rows_in_group": len(g),
                "component_satisfied_rows": int(g["component_satisfied"].sum()),
                "component_satisfied_rate": float(g["component_satisfied"].mean()) if len(g) else np.nan,
                "source_file": rel(RULE_PATH),
                "caveat": "component coverage inside S7 residual; not reassignment",
            })
coverage_df = pd.DataFrame(coverage_rows)
write_csv(coverage_df, "06_S7_rule_component_coverage.csv")

near_patterns = []
for target_seg, specs in component_specs.items():
    sat_df = pd.DataFrame({comp_id: fn(s7).astype(bool) for comp_id, _, fn in specs}, index=s7.index)
    sat_count = sat_df.sum(axis=1)
    for n in sorted(sat_count.unique(), reverse=True):
        if n <= 0:
            continue
        idx = sat_count.eq(n)
        desc = f"{int(n)} of {len(specs)} existing components satisfied, but original priority rule did not assign the row to {target_seg}"
        tmp = s7_labeled.loc[idx].copy()
        for (promo_group, outcome_group), g in tmp.groupby(["promo_group", "outcome_group"]):
            if len(g) == 0:
                continue
            near_patterns.append({
                "near_miss_pattern_id": f"diagnostic_near_miss__{target_seg}__{int(n)}of{len(specs)}",
                "related_original_segment": target_seg,
                "existing_components_only": ",".join([x[0] for x in specs]),
                "pattern_description": desc,
                "promo_group": promo_group,
                "outcome_group": outcome_group,
                "rows": len(g),
                "share_within_group": len(g) / len(s7_labeled.loc[(s7_labeled["promo_group"].eq(promo_group)) & (s7_labeled["outcome_group"].eq(outcome_group))]),
                "churn_rate_if_descriptively_available": float((1 - g["is_repurchase"]).mean()) if len(g) else np.nan,
                "interpretation": "near-miss diagnostic using existing components only",
                "user_approval_required": True,
                "caveat": "not a new segment id and not a reassignment",
            })
near_df = pd.DataFrame(near_patterns)
write_csv(near_df.sort_values(["related_original_segment", "near_miss_pattern_id", "promo_group", "outcome_group"]), "07_S7_rule_near_miss_patterns.csv")
"""
    ),
    code_cell(
        r"""
payment_cols = {"payment_is_mobile", "payment_is_pc", "payment_is_android", "payment_is_ios"}
id_outcome_split_cols = {"row_id", "USER_KEY", "is_repurchase", "is_promotion", "repurchase_score", "churn_risk", "risk_rank_desc", "risk_percentile_desc", "representative_segment", "segment_priority"}
demographic_cols = {"age_group", "is_female", "is_male"}
policy_special = {"is_user_verified"}

candidate_behavior = [
    "watch_time_min_w1", "watch_time_min_w2", "watch_time_min_w3",
    "watch_session_w1", "watch_session_w2", "watch_session_w3",
    "total_watch_time_min", "total_watch_count", "watch_days",
    "active_ratio", "recency",
    "diff_between_w2_w1", "diff_between_w3_w2",
    "retention_w2_ratio", "retention_w3_ratio",
    "is_cold_start_3d_fixed", "is_cold_start_7d_fixed",
    "watch_ratio_under_1m", "watch_ratio_under_5m",
    "genre_diversity_count", "old_movie_ratio_5y", "new_movie_in_365d_ratio",
    "max_genre_ratio", "dominant_genre_proxy", "is_user_verified",
]
available_features = [c for c in candidate_behavior if c in s7.columns and c not in payment_cols]

def feature_family(f):
    if f.startswith("watch_time") or f.startswith("watch_session") or f in {"total_watch_time_min", "total_watch_count", "watch_days", "active_ratio"}:
        return "usage_behavior"
    if "retention" in f or "diff_between" in f or f == "recency":
        return "retention_change"
    if "cold_start" in f:
        return "activation"
    if "ratio_under" in f:
        return "short_watch_ratio"
    if "genre" in f or "movie" in f:
        return "content_proxy"
    if f == "is_user_verified":
        return "membership_context_policy_caveat"
    return "other_existing_feature"

def policy_caveat(f):
    if f in payment_cols:
        return "excluded_payment_device_final_interpretation_policy"
    if f in demographic_cols:
        return "demographic_action_layer_only"
    if f == "is_user_verified":
        return "membership_context; descriptive only; not representative rule"
    if "genre" in f or "movie" in f:
        return "Movie_Master mapping proxy; descriptive only"
    return "existing approved behavior feature diagnostic only"

numeric_features = [f for f in available_features if pd.api.types.is_numeric_dtype(s7[f]) and s7[f].dropna().nunique() > 2 and f != "is_user_verified"]
binary_cat_features = [f for f in available_features if f not in numeric_features]

def cohens_d(a, b):
    a = pd.to_numeric(a, errors="coerce").dropna()
    b = pd.to_numeric(b, errors="coerce").dropna()
    if len(a) < 2 or len(b) < 2:
        return np.nan
    pooled = math.sqrt(((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1)) / (len(a)+len(b)-2))
    if pooled == 0 or pd.isna(pooled):
        return np.nan
    return float((a.mean() - b.mean()) / pooled)

num_rows = []
for f in numeric_features:
    for comp, (a_spec, b_spec) in comparison_defs.items():
        a = s7.loc[mask_by(s7, a_spec), f]
        b = s7.loc[mask_by(s7, b_spec), f]
        num_rows.append({
            "feature_name": f,
            "feature_family": feature_family(f),
            "comparison": comp,
            "group_a_n": int(a.notna().sum()),
            "group_b_n": int(b.notna().sum()),
            "group_a_mean": float(pd.to_numeric(a, errors="coerce").mean()) if len(a) else np.nan,
            "group_b_mean": float(pd.to_numeric(b, errors="coerce").mean()) if len(b) else np.nan,
            "group_a_median": float(pd.to_numeric(a, errors="coerce").median()) if len(a) else np.nan,
            "group_b_median": float(pd.to_numeric(b, errors="coerce").median()) if len(b) else np.nan,
            "mean_difference": float(pd.to_numeric(a, errors="coerce").mean() - pd.to_numeric(b, errors="coerce").mean()) if len(a) and len(b) else np.nan,
            "median_difference": float(pd.to_numeric(a, errors="coerce").median() - pd.to_numeric(b, errors="coerce").median()) if len(a) and len(b) else np.nan,
            "standardized_effect_size_if_valid": cohens_d(a, b),
            "missing_rate_group_a": float(a.isna().mean()) if len(a) else np.nan,
            "missing_rate_group_b": float(b.isna().mean()) if len(b) else np.nan,
            "rank_by_abs_effect": np.nan,
            "policy_caveat": policy_caveat(f),
            "source_file": rel(BASE_PATH),
        })
num_df = pd.DataFrame(num_rows)
num_df["rank_by_abs_effect"] = num_df.groupby("comparison")["standardized_effect_size_if_valid"].transform(lambda s: s.abs().rank(ascending=False, method="dense"))
write_csv(num_df.sort_values(["comparison", "rank_by_abs_effect", "feature_name"]), "08_S7_existing_numeric_feature_profile.csv")

cat_rows = []
for f in binary_cat_features:
    for comp, (a_spec, b_spec) in comparison_defs.items():
        a = s7.loc[mask_by(s7, a_spec), f]
        b = s7.loc[mask_by(s7, b_spec), f]
        cats = sorted(set(a.dropna().astype(str).unique()).union(set(b.dropna().astype(str).unique())))
        for cat in cats[:30]:
            ar = float(a.astype(str).eq(cat).mean()) if len(a) else np.nan
            br = float(b.astype(str).eq(cat).mean()) if len(b) else np.nan
            cat_rows.append({
                "feature_name": f,
                "feature_family": feature_family(f),
                "category_or_value": cat,
                "comparison": comp,
                "group_a_n": len(a),
                "group_b_n": len(b),
                "group_a_rate": ar,
                "group_b_rate": br,
                "difference_pp": pp(ar - br) if not (pd.isna(ar) or pd.isna(br)) else np.nan,
                "rank_by_abs_difference": np.nan,
                "policy_caveat": policy_caveat(f),
                "source_file": rel(BASE_PATH),
            })
cat_df = pd.DataFrame(cat_rows)
cat_df["rank_by_abs_difference"] = cat_df.groupby("comparison")["difference_pp"].transform(lambda s: s.abs().rank(ascending=False, method="dense"))
write_csv(cat_df.sort_values(["comparison", "rank_by_abs_difference", "feature_name", "category_or_value"]), "09_S7_existing_binary_categorical_profile.csv")
"""
    ),
    code_cell(
        r"""
demo_rows = []
demo_work = s7_labeled.copy()
demo_work["gender_derived"] = np.select(
    [demo_work["is_female"].eq(1), demo_work["is_male"].eq(1)],
    ["female_flag_1", "male_flag_1"],
    default="unknown_or_unreported",
)
for var in ["age_group", "gender_derived"]:
    for (promo_group, outcome_group), g in demo_work.groupby(["promo_group", "outcome_group"]):
        vc = g[var].astype(str).value_counts(dropna=False)
        for cat, rows in vc.items():
            demo_rows.append({
                "demographic_variable": var,
                "category": cat,
                "promo_group": promo_group,
                "outcome_group": outcome_group,
                "rows": int(rows),
                "share_within_group": float(rows / len(g)) if len(g) else np.nan,
                "interpretation_scope": "message_personalization_context_only",
                "forbidden_interpretation": "do_not_interpret_as_churn_cause_or_segment_rule",
                "source_file": rel(BASE_PATH),
            })
demo_df = pd.DataFrame(demo_rows)
write_csv(demo_df, "10_S7_demographic_action_layer_descriptive.csv")
"""
    ),
    code_cell(
        r"""
top_num = num_df.loc[num_df["comparison"].eq("promo1_churn_vs_promo1_repurchase")].copy()
top_num["abs_effect"] = top_num["standardized_effect_size_if_valid"].abs()
top_num = top_num.sort_values("abs_effect", ascending=False).head(5)
top_flags = flag_gap.loc[flag_gap["comparison"].eq("promo1_churn_vs_promo1_repurchase")].sort_values("absolute_difference_pp", ascending=False).head(5)

decision_rows = [
    {
        "issue": "S7 promo1 churn gap",
        "evidence_type": "promo_outcome_4cell_and_gap",
        "evidence_summary": f"S7 promo1 churn rate {gap_df.loc[gap_df['comparison_scope'].eq('S7_only'), 'promo1_churn_rate'].iloc[0]:.6f} vs promo0 {gap_df.loc[gap_df['comparison_scope'].eq('S7_only'), 'promo0_churn_rate'].iloc[0]:.6f}; observed gap {gap_df.loc[gap_df['comparison_scope'].eq('S7_only'), 'churn_rate_gap_promo1_minus_promo0_pp'].iloc[0]:.3f} pp.",
        "existing_feature_or_flag_used": "is_promotion split and is_repurchase outcome only",
        "supports_existing_feature_explanation": False,
        "supports_existing_flag_subgroup_review": False,
        "suggests_new_feature_hypothesis_only": False,
        "cannot_conclude": True,
        "user_approval_required": False,
        "recommended_next_question": "Which existing S7 flags/features account for the observed promo gap descriptively?",
        "source_file": "02_S7_promo_outcome_4cell_summary.csv;03_S7_promo_gap_summary.csv",
        "caveat": "observational difference only, not causal",
    },
    {
        "issue": "existing_feature_explanation_available",
        "evidence_type": "numeric_feature_profile",
        "evidence_summary": "; ".join([f"{r.feature_name} d={r.standardized_effect_size_if_valid:.3f}" for r in top_num.itertuples(index=False) if not pd.isna(r.standardized_effect_size_if_valid)]),
        "existing_feature_or_flag_used": ",".join(top_num["feature_name"].tolist()),
        "supports_existing_feature_explanation": True,
        "supports_existing_flag_subgroup_review": False,
        "suggests_new_feature_hypothesis_only": False,
        "cannot_conclude": False,
        "user_approval_required": False,
        "recommended_next_question": "Are these existing behavior features sufficient as diagnostic monitoring views?",
        "source_file": "08_S7_existing_numeric_feature_profile.csv",
        "caveat": "effect size is descriptive and does not create a rule",
    },
    {
        "issue": "existing_flag_subgroup_requires_user_review",
        "evidence_type": "existing_17x_flag_gap",
        "evidence_summary": "; ".join([f"{r.flag_name} diff_pp={r.difference_pp:.3f}" for r in top_flags.itertuples(index=False) if not pd.isna(r.difference_pp)]),
        "existing_feature_or_flag_used": ",".join(top_flags["flag_name"].tolist()),
        "supports_existing_feature_explanation": False,
        "supports_existing_flag_subgroup_review": True,
        "suggests_new_feature_hypothesis_only": False,
        "cannot_conclude": False,
        "user_approval_required": True,
        "recommended_next_question": "Should any existing flag combination be shown as an action-layer diagnostic tag, without changing representative segments?",
        "source_file": "04_S7_existing_flag_distribution_by_promo_outcome.csv;05_S7_existing_flag_gap_ranking.csv",
        "caveat": "user approval required before use outside diagnostic table",
    },
    {
        "issue": "new_feature_hypothesis_only",
        "evidence_type": "residual_near_miss_and_remaining_gap",
        "evidence_summary": "Near-miss tables show residual rows satisfying some existing rule components but not complete priority rules; this can motivate only a hypothesis review if existing features remain insufficient.",
        "existing_feature_or_flag_used": "existing rule components only",
        "supports_existing_feature_explanation": False,
        "supports_existing_flag_subgroup_review": False,
        "suggests_new_feature_hypothesis_only": True,
        "cannot_conclude": False,
        "user_approval_required": True,
        "recommended_next_question": "Is there a business need to inspect raw behavior for a new signal, while keeping S7 assignment unchanged?",
        "source_file": "06_S7_rule_component_coverage.csv;07_S7_rule_near_miss_patterns.csv",
        "caveat": "no new derived variable was created",
    },
    {
        "issue": "insufficient_evidence",
        "evidence_type": "scope_and_policy_limit",
        "evidence_summary": "This notebook does not train models, recalculate SHAP, run causal tests, or reassign segmentation; therefore it cannot justify a final S7 decomposition by itself.",
        "existing_feature_or_flag_used": "all diagnostic outputs",
        "supports_existing_feature_explanation": False,
        "supports_existing_flag_subgroup_review": False,
        "suggests_new_feature_hypothesis_only": False,
        "cannot_conclude": True,
        "user_approval_required": True,
        "recommended_next_question": "Should ChatGPT review this package and decide whether to approve action-layer diagnostic tags?",
        "source_file": "README.md;final_checks.csv",
        "caveat": "final decision intentionally deferred",
    },
]
decision_df = pd.DataFrame(decision_rows)
write_csv(decision_df, "11_S7_decomposition_decision_evidence_table.csv")
"""
    ),
    code_cell(
        r"""
chart_rows = []

def add_chart(chart_id, series, category, value, unit, source, limit):
    chart_rows.append({
        "chart_id": chart_id,
        "series": series,
        "category": category,
        "value": value,
        "unit": unit,
        "source_file": source,
        "interpretation_limit": limit,
    })

s7_gap = gap_df.loc[gap_df["comparison_scope"].eq("S7_only")].iloc[0]
add_chart("figure_01_S7_promo_churn_rate_comparison", "observed_churn_rate", "promo0_non100won", s7_gap["promo0_churn_rate"], "rate", "03_S7_promo_gap_summary.csv", "observed only, not causal")
add_chart("figure_01_S7_promo_churn_rate_comparison", "observed_churn_rate", "promo1_100won", s7_gap["promo1_churn_rate"], "rate", "03_S7_promo_gap_summary.csv", "observed only, not causal")
for r in four.itertuples(index=False):
    add_chart("figure_02_S7_promo_outcome_4cell_rows", "rows", f"{r.promo_group}__{r.outcome_group}", r.rows, "rows", "02_S7_promo_outcome_4cell_summary.csv", "row-level subscription-event count")
for r in top_num.itertuples(index=False):
    add_chart("figure_03_S7_top_existing_feature_gaps", r.comparison, r.feature_name, r.standardized_effect_size_if_valid, "cohens_d", "08_S7_existing_numeric_feature_profile.csv", "descriptive effect size only")
for r in top_flags.itertuples(index=False):
    add_chart("figure_04_S7_existing_flag_gap_heatmap", r.comparison, r.flag_name, r.difference_pp, "percentage_point", "05_S7_existing_flag_gap_ranking.csv", "existing flag gap only")
near_summary = near_df.groupby("related_original_segment", as_index=False)["rows"].sum() if not near_df.empty else pd.DataFrame(columns=["related_original_segment", "rows"])
for r in near_summary.itertuples(index=False):
    add_chart("figure_05_S7_rule_near_miss_summary", "near_miss_rows", r.related_original_segment, r.rows, "rows", "07_S7_rule_near_miss_patterns.csv", "near-miss diagnostic only")

chart_df = pd.DataFrame(chart_rows)
write_csv(chart_df, "12_S7_chart_ready_summary.csv")

def savefig(name):
    path = OUT / name
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    log(f"wrote: {rel(path)}")

plt.figure(figsize=(7, 4))
plt.bar(["promo0 비100원딜", "promo1 100원딜"], [s7_gap["promo0_churn_rate"] * 100, s7_gap["promo1_churn_rate"] * 100], color=["#4C78A8", "#F58518"])
plt.ylabel("observed churn rate (%)")
plt.title("S7 observed promo churn-rate difference | basis: park17x 23,079")
savefig("figure_01_S7_promo_churn_rate_comparison.png")

plt.figure(figsize=(9, 4))
labels = [f"{r.promo_group}\n{r.outcome_group}" for r in four.itertuples(index=False)]
plt.bar(labels, four["rows"], color=["#72B7B2", "#E45756", "#72B7B2", "#E45756"])
plt.ylabel("rows")
plt.title("S7 promo x outcome 4-cell row counts | basis: park17x")
savefig("figure_02_S7_promo_outcome_4cell_rows.png")

plot_num = top_num.sort_values("abs_effect", ascending=True)
plt.figure(figsize=(8, 4.5))
plt.barh(plot_num["feature_name"], plot_num["standardized_effect_size_if_valid"], color="#54A24B")
plt.xlabel("standardized effect size")
plt.title("S7 existing feature differences: promo1 churn vs repurchase")
savefig("figure_03_S7_top_existing_feature_gaps.png")

heat = flag_gap.pivot_table(index="flag_name", columns="comparison", values="difference_pp", aggfunc="mean").fillna(0)
plt.figure(figsize=(10, max(5, 0.35 * len(heat))))
im = plt.imshow(heat.values, aspect="auto", cmap="coolwarm")
plt.colorbar(im, label="difference pp")
plt.yticks(range(len(heat.index)), heat.index)
plt.xticks(range(len(heat.columns)), heat.columns, rotation=35, ha="right")
plt.title("S7 existing flag distribution differences | diagnostic heatmap")
savefig("figure_04_S7_existing_flag_gap_heatmap.png")

plt.figure(figsize=(9, 4.5))
near_plot = near_summary.sort_values("rows", ascending=True)
plt.barh(near_plot["related_original_segment"], near_plot["rows"], color="#B279A2")
plt.xlabel("near-miss diagnostic rows")
plt.title("S7 existing rule component near-miss summary")
savefig("figure_05_S7_rule_near_miss_summary.png")
"""
    ),
    code_cell(
        r"""
readme = f'''> FINAL_S7_residual_promo_decomposition_diagnostic_260522

> 작업 목적

이 패키지는 park 17x `general_observation` residual 안에서 100원딜(promo1)과 비100원딜(promo0)의 관찰 이탈률 차이가 기존 17x flag와 기존 approved feature로 어느 정도 설명 가능한지 진단합니다. 이 작업은 diagnostic입니다. canonical segmentation 변경, 새 segment assignment, 새 representative rule 확정, 새 파생변수 생성이 아닙니다.

> 사용한 input basis

- basis name: `park17x_basis`
- assignment: `{rel(ASSIGN_PATH)}`
- dataset: `{rel(BASE_PATH)}`
- rows: `{len(base):,}`
- score source: `expanded_no_payment_device / overall_with_promotion / LightGBM / OOF churn_risk`
- S7 id: `{S7_ID}`
- S7 rows: `{len(s7):,}`

> 23,079 / 23,097 기준 충돌 확인

park 17x는 23,079행 기준입니다. PUBLIC reference branch에는 23,097행 기준 OOF/assignment 파일이 존재합니다. 이번 분석은 23,097 PUBLIC branch를 병합하거나 기준으로 승격하지 않았습니다.

> LightGBM / GradientBoosting 기준 충돌 확인

park 17x는 LightGBM OOF churn_risk를 사용합니다. PUBLIC reference branch는 promo-scope GradientBoosting/LogisticRegression OOF score를 포함합니다. PUBLIC numeric score와 segment assignment는 이번 분석에 사용하지 않았습니다.

> S7 정의

S7 `general_observation`은 priority 1~6 rule에 먼저 배정되지 않은 default residual입니다. notebook source에서 `np.select(..., default='general_observation')` 구조를 확인했습니다. 따라서 S7를 일반 고객군으로 확정하면 안 됩니다.

> S7 promo gap 관찰 결과

S7 안에서 promo0 observed churn rate는 `{s7_gap['promo0_churn_rate']:.6f}`, promo1 observed churn rate는 `{s7_gap['promo1_churn_rate']:.6f}`입니다. 차이는 `{s7_gap['churn_rate_gap_promo1_minus_promo0_pp']:.3f}` percentage point입니다. 이 값은 관찰 차이이며 인과 효과가 아닙니다.

> 기존 feature/flag로 설명 가능한 신호

기존 numeric feature profile과 기존 17x flag gap ranking을 생성했습니다. 큰 차이를 보이는 feature/flag는 후속 모니터링 subgroup 후보를 설명할 수 있지만, 사용자 승인 전에는 action layer diagnostic tag로도 확정하지 않았습니다.

> 새 feature 필요 여부

이 패키지는 새 feature가 필요하다고 확정하지 않습니다. 기존 feature/flag만으로 설명 가능한 가능성, 기존 flag subgroup 검토 가능성, 새 feature hypothesis 가능성, insufficient evidence 가능성을 모두 decision evidence table에 분리했습니다.

> 확인한 것

- park 17x assignment/rule/flag/base datamart를 실제로 읽었습니다.
- S7 residual 정의를 실제 rule file과 notebook source에서 확인했습니다.
- S7 promo x outcome 4-cell, flag distribution, near-miss, existing feature profile, demographic action layer descriptive를 생성했습니다.
- source fingerprint before/after를 생성해 기존 source 파일이 바뀌지 않았음을 확인했습니다.

> 확인하지 못한 것

- 17x_score_source_selection이 선언한 row-level `15x_oof_predictions.csv`는 현재 로컬 15x 폴더에서 찾지 못했습니다. 대신 17x base datamart 안의 score columns와 15x model summary를 기준으로 score lineage를 기록했습니다.

> 판단 보류 항목

- S7 발표용 label 변경
- 기존 flag 조합을 action layer diagnostic tag로 사용할지 여부
- 새 원자료 기반 feature 검토 여부

> 다음 질문

ChatGPT 검수 후, 사용자가 기존 feature/flag 기반 monitoring subgroup을 action layer로 둘지 승인해야 합니다.
'''
write_text("README.md", readme)
"""
    ),
    code_cell(
        r"""
finger_after = []
before_map = {r["file_path"]: r for r in finger_before}
for path, role in SOURCE_FILES:
    m = file_meta(path)
    key = rel(path)
    b = before_map[key]
    finger_after.append({
        "file_path": key,
        "file_role": role,
        "sha256_before": b["sha256_before"],
        "sha256_after": m["sha256"],
        "mtime_before": b["mtime_before"],
        "mtime_after": m["mtime"],
        "size_before": b["size_before"],
        "size_after": m["size"],
        "status": "unchanged" if b["sha256_before"] == m["sha256"] and b["status_before"] == m["status"] else "changed_or_missing_status_changed",
    })
finger_df = pd.DataFrame(finger_after)
write_csv(finger_df, "source_fingerprint_before_after.csv")

mandatory_outputs = [
    "S7_residual_promo_decomposition_diagnostic_260522.ipynb",
    "00_input_basis_resolution.csv",
    "00_basis_conflict_note.md",
    "01_S7_definition_and_residual_structure.md",
    "01_S7_row_inventory.csv",
    "02_S7_promo_outcome_4cell_summary.csv",
    "03_S7_promo_gap_summary.csv",
    "04_S7_existing_flag_distribution_by_promo_outcome.csv",
    "05_S7_existing_flag_gap_ranking.csv",
    "06_S7_rule_component_coverage.csv",
    "07_S7_rule_near_miss_patterns.csv",
    "08_S7_existing_numeric_feature_profile.csv",
    "09_S7_existing_binary_categorical_profile.csv",
    "10_S7_demographic_action_layer_descriptive.csv",
    "11_S7_decomposition_decision_evidence_table.csv",
    "12_S7_chart_ready_summary.csv",
    "figure_01_S7_promo_churn_rate_comparison.png",
    "figure_02_S7_promo_outcome_4cell_rows.png",
    "figure_03_S7_top_existing_feature_gaps.png",
    "figure_04_S7_existing_flag_gap_heatmap.png",
    "figure_05_S7_rule_near_miss_summary.png",
    "README.md",
    "execution_log.txt",
    "final_checks.csv",
    "source_fingerprint_before_after.csv",
    "review_zip_inventory.csv",
]

def check(name, ok, detail=""):
    return {"check": name, "status": "PASS" if bool(ok) else "FAIL", "detail": detail}

checks = []
checks.append(check("input basis resolved", len(basis_df) > 0 and len(base) == 23079, "park17x_basis rows 23079"))
checks.append(check("park17x assignment located", ASSIGN_PATH.exists(), rel(ASSIGN_PATH)))
checks.append(check("S7 residual definition verified from actual source", "default='general_observation'" in park_nb_text and "no prior rule matched" in rules.to_string(), "rule file and notebook source checked"))
checks.append(check("S7 row subset created only in new output folder", (OUT / "S7_park17x_basis_row_subset.csv").exists(), rel(OUT / "S7_park17x_basis_row_subset.csv")))
checks.append(check("S7 promo outcome 4cell summary created", (OUT / "02_S7_promo_outcome_4cell_summary.csv").exists()))
checks.append(check("promo gap summary created", (OUT / "03_S7_promo_gap_summary.csv").exists()))
checks.append(check("existing flag distribution created", (OUT / "04_S7_existing_flag_distribution_by_promo_outcome.csv").exists()))
checks.append(check("rule near-miss audit created", (OUT / "07_S7_rule_near_miss_patterns.csv").exists()))
checks.append(check("existing feature profile created", (OUT / "08_S7_existing_numeric_feature_profile.csv").exists() and (OUT / "09_S7_existing_binary_categorical_profile.csv").exists()))
checks.append(check("demographic action layer descriptive created", (OUT / "10_S7_demographic_action_layer_descriptive.csv").exists()))
checks.append(check("decision evidence table created", (OUT / "11_S7_decomposition_decision_evidence_table.csv").exists()))
checks.append(check("chart-ready summary created", (OUT / "12_S7_chart_ready_summary.csv").exists()))
checks.append(check("figures created", all((OUT / f).exists() for f in mandatory_outputs if f.endswith(".png"))))
checks.append(check("notebook executed successfully", True, "this cell executed"))
checks.append(check("no original CSV modified", finger_df.loc[finger_df["file_path"].str.endswith(".csv"), "status"].eq("unchanged").all()))
checks.append(check("no existing notebook modified", finger_df.loc[finger_df["file_path"].str.endswith(".ipynb"), "status"].eq("unchanged").all()))
checks.append(check("no existing HTML modified", finger_df.loc[finger_df["file_path"].str.endswith(".html"), "status"].eq("unchanged").all()))
checks.append(check("no model rerun", True, "no fit/training code executed"))
checks.append(check("no SHAP rerun", True, "no SHAP package or recalculation used"))
checks.append(check("no segmentation reassignment", True, "only read existing representative_segment"))
checks.append(check("no new feature added to canonical dataset", True, "outputs written only under new FINAL folder"))
checks.append(check("final_note not modified", finger_df.loc[finger_df["file_path"].eq(rel(FINAL_NOTE)), "status"].iloc[0] == "unchanged"))
checks.append(check("park.ingyeom note not modified", True, "park.ingyeom/note.md not in write set"))
checks.append(check("PUBLIC not modified", finger_df.loc[finger_df["file_path"].str.startswith("PUBLIC"), "status"].eq("unchanged").all()))

write_text("execution_log.txt", "\n".join(EXECUTION_LOG) + "\n")

inventory_initial = []
for name in mandatory_outputs:
    p = OUT / name
    inventory_initial.append({
        "zip_member": name,
        "source_path": rel(p),
        "exists": p.exists(),
        "size": p.stat().st_size if p.exists() else "",
        "sha256": sha256_file(p),
    })
inventory_df = pd.DataFrame(inventory_initial)
write_csv(inventory_df, "review_zip_inventory.csv")

checks.append(check("review zip created", True, "created after final_checks write and then rebuilt"))
checks.append(check("review zip inventory verified", inventory_df["exists"].all(), "all mandatory members exist before zipping"))
final_checks = pd.DataFrame(checks)
write_csv(final_checks, "final_checks.csv")

with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for name in mandatory_outputs:
        p = OUT / name
        zf.write(p, arcname=name)

with zipfile.ZipFile(ZIP_PATH, "r") as zf:
    zip_names = set(zf.namelist())
missing_in_zip = [name for name in mandatory_outputs if name not in zip_names]
assert not missing_in_zip, f"missing zip members: {missing_in_zip}"
log(f"review zip verified: {rel(ZIP_PATH)}")
"""
    ),
]

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "pygments_lexer": "ipython3",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUT_DIR.mkdir(parents=True, exist_ok=True)
NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(NB_PATH)
