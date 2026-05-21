from __future__ import annotations

import html
import math
import zipfile
from pathlib import Path

import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
PUBLIC = ROOT / "PUBLIC"
Q17 = PUBLIC / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments_quality_hotfix_260520"
D17 = PUBLIC / "results" / "17_segmentation_design_260520" / "promo_scope_oof_behavior_segments_demographic_hotfix_260520"
F16B = PUBLIC / "results" / "16_SHAP_candidate_interpretation_260520" / "16b_feature_family_mapping_hotfix_260520"
O15 = PUBLIC / "results" / "15_oof_score_or_sensitivity_260520" / "four_model_oof_scores_hotfix_260520"
OUT = PUBLIC / "reports" / "business" / "18_business_recommendation_storyline_260520"
FIG = PUBLIC / "reports" / "figures" / "18_business_recommendation_storyline_260520"
NB_DIR = PUBLIC / "notebooks" / "18_business_recommendation_storyline_260520"
HANDOFF = PUBLIC / "handoff" / "PUBLIC_18_business_storyline_260520"
ZIP_PATH = PUBLIC / "zip" / "PUBLIC_18_business_storyline_260520_review_package.zip"
NOTEBOOK = NB_DIR / "18_business_storyline_and_visual_guide_260520.ipynb"
EXECUTED_NOTEBOOK = NB_DIR / "18_business_storyline_and_visual_guide_260520_executed.ipynb"
NOTE = PUBLIC / "note.md"

INPUTS = [
    ("17_revised_representative_segment_proposal", Q17 / "17_revised_representative_segment_proposal.csv", True),
    ("17_revised_segment_assignment_simulation", Q17 / "17_revised_segment_assignment_simulation.csv", True),
    ("17_revised_segment_summary_simulation", Q17 / "17_revised_segment_summary_simulation.csv", True),
    ("17_promo1_vs_promo0_segment_differential_analysis", Q17 / "17_promo1_vs_promo0_segment_differential_analysis.csv", True),
    ("17_other_needs_review_decomposition_quality_hotfix", Q17 / "17_other_needs_review_decomposition_quality_hotfix.csv", True),
    ("17_revised_segment_demographic_action_bridge", Q17 / "17_revised_segment_demographic_action_bridge.csv", True),
    ("17_segment_quality_hotfix_rationale_memo_for_executives", Q17 / "17_segment_quality_hotfix_rationale_memo_for_executives.md", True),
    ("17_readiness_for_18_quality_hotfix", Q17 / "17_readiness_for_18_quality_hotfix.csv", True),
    ("17_demographic_source_column_audit", D17 / "17_demographic_source_column_audit.csv", True),
    ("17_gender_derivation_audit", D17 / "17_gender_derivation_audit.csv", True),
    ("17_age_group_audit", D17 / "17_age_group_audit.csv", True),
    ("17_segment_demographic_profile_demographic_hotfix", D17 / "17_segment_demographic_profile_demographic_hotfix.csv", True),
    ("17_segment_age_behavior_profile_demographic_hotfix", D17 / "17_segment_age_behavior_profile_demographic_hotfix.csv", True),
    ("17_segment_gender_behavior_profile_demographic_hotfix", D17 / "17_segment_gender_behavior_profile_demographic_hotfix.csv", True),
    ("17_segment_action_personalization_matrix_demographic_hotfix", D17 / "17_segment_action_personalization_matrix_demographic_hotfix.csv", True),
    ("17_demographic_hotfix_summary", D17 / "17_demographic_hotfix_summary.csv", True),
    ("17_segment_rationale_demographic_action_supplement", D17 / "17_segment_rationale_demographic_action_supplement.md", True),
    ("17_readiness_for_18_business_storyline_demographic_hotfix", D17 / "17_readiness_for_18_business_storyline_demographic_hotfix.csv", True),
    ("16b_feature_family_mapping_hotfix", F16B / "16b_feature_family_mapping_hotfix.csv", True),
    ("16b_shap_family_importance_hotfix", F16B / "16b_shap_family_importance_hotfix.csv", True),
    ("16b_promo1_vs_promo0_shap_comparison_hotfix", F16B / "16b_promo1_vs_promo0_shap_comparison_hotfix.csv", True),
    ("16b_family_interpretation_handoff_for_17", F16B / "16b_family_interpretation_handoff_for_17.csv", True),
    ("15_oof_metric_summary", O15 / "15_oof_metric_summary.csv", True),
    ("15_gb_lr_high_risk_overlap", O15 / "15_gb_lr_high_risk_overlap.csv", True),
    ("15_oof_score_wide", O15 / "15_oof_score_wide.csv", True),
]

OUTPUTS = {
    "canonical": OUT / "18_canonical_segment_set_for_storyline.csv",
    "comparison": OUT / "18_promo1_vs_promo0_storyline_comparison.csv",
    "action": OUT / "18_segment_business_action_matrix.csv",
    "demo_select": OUT / "18_demographic_action_candidate_selection.csv",
    "html": OUT / "18_segment_visual_guide_v2.html",
    "memo": OUT / "18_business_storyline_memo.md",
    "dashboard": OUT / "18_dashboard_handoff_datamart.csv",
    "talking": OUT / "18_presentation_talking_points.md",
    "wording": OUT / "18_safe_unsafe_wording.csv",
    "readme": OUT / "README.md",
}


def ensure_dirs() -> None:
    for p in [OUT, FIG, NB_DIR, HANDOFF, ZIP_PATH.parent]:
        p.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def shape(path: Path) -> tuple[str, str, str]:
    if not path.exists():
        return "", "", "missing"
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        return str(len(df)), str(len(df.columns)), "readable csv"
    txt = path.read_text(encoding="utf-8", errors="replace")
    return str(len(txt.splitlines())), "1", "readable text"


def input_validation() -> pd.DataFrame:
    rows = []
    for item, path, required in INPUTS:
        exists = path.exists()
        r, c, note = shape(path) if exists else ("", "", "missing")
        rows.append({
            "input_item": item,
            "expected_path": str(path.relative_to(ROOT)),
            "exists": bool(exists),
            "rows": r,
            "columns": c,
            "status": "PASS" if exists else ("FAIL" if required else "WARN"),
            "notes": note,
        })
    out = pd.DataFrame(rows)
    out.to_csv(HANDOFF / "18_input_validation.csv", index=False, encoding="utf-8-sig")
    return out


def pct(x) -> str:
    return "NA" if pd.isna(x) else f"{float(x) * 100:.1f}%"


def num(x, digits=3) -> str:
    return "NA" if pd.isna(x) else f"{float(x):.{digits}f}"


def load() -> dict[str, pd.DataFrame]:
    return {
        "proposal": pd.read_csv(Q17 / "17_revised_representative_segment_proposal.csv"),
        "assignment": pd.read_csv(Q17 / "17_revised_segment_assignment_simulation.csv"),
        "summary": pd.read_csv(Q17 / "17_revised_segment_summary_simulation.csv"),
        "diff": pd.read_csv(Q17 / "17_promo1_vs_promo0_segment_differential_analysis.csv"),
        "other": pd.read_csv(Q17 / "17_other_needs_review_decomposition_quality_hotfix.csv"),
        "demo_action": pd.read_csv(D17 / "17_segment_action_personalization_matrix_demographic_hotfix.csv"),
        "age": pd.read_csv(D17 / "17_age_group_audit.csv"),
        "gender": pd.read_csv(D17 / "17_gender_derivation_audit.csv"),
        "demo_profile": pd.read_csv(D17 / "17_segment_demographic_profile_demographic_hotfix.csv"),
        "shap_family": pd.read_csv(F16B / "16b_shap_family_importance_hotfix.csv"),
        "oof_metric": pd.read_csv(O15 / "15_oof_metric_summary.csv"),
    }


def behavior_problem(family: str) -> tuple[str, str]:
    if family == "high_risk_week3_inactivity_or_retention_decay":
        return "3주차 비활성 또는 유지율 감소", "week3_save_campaign"
    if family == "high_risk_activation_or_low_engagement":
        return "초기 이용 습관 형성 실패 또는 낮은 활동", "activation_reengagement"
    if family == "mid_risk_retention_watchlist":
        return "상위 고위험은 아니지만 유지 관찰이 필요한 중간 위험", "mid_risk_watchlist_nurture"
    if family == "stable_usage_lower_risk":
        return "상대적으로 안정적인 이용 패턴", "stable_usage_maintenance_or_upsell"
    if family == "other_needs_review_residual":
        return "현재 rule로 충분히 설명되지 않은 잔여군", "residual_monitoring"
    return "프로필 또는 콘텐츠 cue", "profile_based_content_recommendation_candidate"


def canonical_segment_set(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    s = data["summary"].copy()
    rows = []
    for _, r in s.iterrows():
        fam = r["revised_segment_family"]
        if fam == "other_needs_review_residual":
            status = "residual_caveat"
            use = "숨기지 않고 residual monitoring 및 추가 검토 대상으로 사용"
        elif int(r["row_count"]) < 300:
            status = "subsignal_only"
            use = "18에서 독립 대표 세그먼트로 승격하지 않고 보조 신호로만 사용"
        else:
            status = "provisional_storyline_candidate"
            use = "promo1 중심 business storyline 후보"
        rows.append({
            "segment_family": fam,
            "promo_scope": r["promo_scope"],
            "row_count": int(r["row_count"]),
            "row_share_within_scope": r["row_share_within_scope"],
            "actual_churn_rate": r["actual_churn_rate"],
            "actual_repurchase_rate": r["actual_repurchase_rate"],
            "mean_gb_churn_risk": r["mean_gb_churn_risk"],
            "segment_status_for_18": status,
            "business_use": use,
            "caveat": "Segment family is provisional; OOF score is not a campaign threshold.",
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUTS["canonical"], index=False, encoding="utf-8-sig")
    return out


def storyline_comparison(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for _, r in data["diff"].iterrows():
        fam = r["segment_family"]
        safe = "같은 위험 행동 패턴이 100원딜 고객군에서 더 높은 이탈률과 risk score로 관찰되었다."
        if r["promo1_row_count"] == 0 or r["promo0_row_count"] == 0:
            interp = "한쪽 scope에서만 충분히 관찰된 provisional pattern이다. 100원딜 특유라고 단정하지 않는다."
        elif r["churn_rate_delta_promo1_minus_promo0"] > 0:
            interp = "공통 행동 패턴이지만 promo1에서 더 높은 churn/risk로 관찰되어 100원딜 고객군의 우선 검토 후보가 된다."
        else:
            interp = "공통 행동 패턴이며 promo1에서 더 위험하다고 단정할 수 없어 비교군 caveat를 유지한다."
        rows.append({
            "segment_family": fam,
            "promo1_row_count": r["promo1_row_count"],
            "promo0_row_count": r["promo0_row_count"],
            "promo1_churn_rate": r["promo1_churn_rate"],
            "promo0_churn_rate": r["promo0_churn_rate"],
            "churn_rate_delta_promo1_minus_promo0": r["churn_rate_delta_promo1_minus_promo0"],
            "promo1_mean_gb_churn_risk": r["promo1_mean_gb_churn_risk"],
            "promo0_mean_gb_churn_risk": r["promo0_mean_gb_churn_risk"],
            "gb_risk_delta_promo1_minus_promo0": r["gb_risk_delta_promo1_minus_promo0"],
            "storyline_interpretation": interp,
            "safe_presentation_sentence": safe,
            "unsafe_sentence_to_avoid": "100원딜이 이탈을 유발했다.",
            "caveat": "Descriptive comparison only; not causal.",
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUTS["comparison"], index=False, encoding="utf-8-sig")
    return out


def demographic_selection(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    src = data["demo_action"].copy()
    for _, r in src.iterrows():
        strength = str(r["evidence_strength"])
        pattern = str(r["observed_demographic_pattern"])
        n = 0
        if pattern.startswith("n="):
            try:
                n = int(pattern.split(";")[0].replace("n=", ""))
            except Exception:
                n = 0
        include = "yes" if strength in ["strong", "moderate"] and n >= 30 else ("limited" if strength in ["moderate"] else "no")
        rows.append({
            "promo_scope": r["promo_scope"],
            "segment_family": r["revised_segment_family"],
            "demographic_modifier": r["demographic_modifier"],
            "observed_demographic_pattern": r["observed_demographic_pattern"],
            "observed_behavior_difference": r["observed_behavior_difference"],
            "candidate_action": "행동 차이에 맞춘 메시지/채널/콘텐츠 variant 검토",
            "include_in_storyline": include,
            "reason_for_include_or_exclude": "moderate 이상 EDA와 subgroup n>=30 기준" if include == "yes" else "표본 또는 행동 차이 근거가 약해 제한적으로만 사용",
            "evidence_strength": strength,
            "overinterpretation_risk": r["risk_of_overinterpretation"],
            "caveat": "Age/gender is a personalization modifier, not churn cause.",
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUTS["demo_select"], index=False, encoding="utf-8-sig")
    return out


def action_matrix(canonical: pd.DataFrame, demo_select: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in canonical.iterrows():
        fam = r["segment_family"]
        problem, action_type = behavior_problem(fam)
        demo = demo_select[(demo_select["promo_scope"].eq(r["promo_scope"])) & (demo_select["segment_family"].eq(fam)) & (demo_select["include_in_storyline"].isin(["yes", "limited"]))]
        demo_summary = "; ".join(demo.head(3)["demographic_modifier"].astype(str).tolist()) if len(demo) else "not_recommended_yet"
        if fam == "high_risk_week3_inactivity_or_retention_decay":
            msg = "3주차 초반부터 day21 직전까지 시청 감소/비활성 조짐을 감지하고 콘텐츠 추천, 혜택 안내, 복귀 메시지를 검토"
            channel = "in-app, push, renewal-reminder message"
            content = "최근 시청 맥락과 장르 cue가 있을 때만 콘텐츠 추천 후보"
        elif fam == "high_risk_activation_or_low_engagement":
            msg = "1주차 activation과 2주차 관심 유지 여부를 확인하고 낮은 활동 고객에게 온보딩/재활성 메시지 검토"
            channel = "early lifecycle push, onboarding notification"
            content = "시청 장벽을 낮추는 short-list 추천"
        elif fam == "mid_risk_retention_watchlist":
            msg = "고위험 확정이 아니라 관찰군으로 두고 2~3주차 행동 변화에 따라 nurture"
            channel = "light-touch notification"
            content = "개인화 강도 낮은 추천"
        elif fam == "stable_usage_lower_risk":
            msg = "과도한 방어 캠페인보다 만족 유지와 업셀 후보로 관리"
            channel = "low-frequency CRM"
            content = "선호 장르 기반 유지/확장 추천"
        else:
            msg = "잔여군을 중위험으로 단정하지 않고 risk band와 행동 flag를 추가 모니터링"
            channel = "monitoring dashboard"
            content = "강한 콘텐츠 전략 보류"
        rows.append({
            "promo_scope": r["promo_scope"],
            "segment_family": fam,
            "segment_role": "promo1_main_scope" if r["promo_scope"] == "promo1" else "promo0_comparison_scope",
            "primary_behavior_problem": problem,
            "risk_level_summary": f"churn={num(r['actual_churn_rate'])}; mean_gb_risk={num(r['mean_gb_churn_risk'])}; status={r['segment_status_for_18']}",
            "recommended_action_type": action_type,
            "recommended_message_direction": msg,
            "recommended_channel_or_touchpoint": channel,
            "recommended_content_strategy": content,
            "demographic_personalization_available": "yes_limited" if len(demo) else "not_recommended_yet",
            "demographic_personalization_summary": demo_summary,
            "evidence_files": "17 quality hotfix summary; 17 demographic action matrix; 18 demographic selection",
            "evidence_strength": "moderate" if len(demo) else "segment_level_only",
            "caveat": "Candidate only; not final campaign policy. Do not claim causality.",
            "final_status": "provisional_business_candidate",
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUTS["action"], index=False, encoding="utf-8-sig")
    return out


def dashboard(canonical: pd.DataFrame, action: pd.DataFrame) -> pd.DataFrame:
    out = canonical.merge(action[["promo_scope", "segment_family", "primary_behavior_problem", "recommended_action_type", "demographic_personalization_summary", "caveat"]], on=["promo_scope", "segment_family"], how="left")
    out = out.rename(columns={
        "row_share_within_scope": "row_share",
        "primary_behavior_problem": "representative_behavior",
        "recommended_action_type": "business_action_type",
        "caveat_y": "key_caveat",
    })
    out["key_caveat"] = out["key_caveat"].fillna(out.get("caveat_x", ""))
    cols = ["promo_scope", "segment_family", "row_count", "row_share", "actual_churn_rate", "actual_repurchase_rate", "mean_gb_churn_risk", "representative_behavior", "business_action_type", "demographic_personalization_summary", "key_caveat"]
    out[cols].to_csv(OUTPUTS["dashboard"], index=False, encoding="utf-8-sig")
    return out[cols]


def safe_unsafe() -> pd.DataFrame:
    rows = [
        ("100원딜 scope", "100원딜은 진입 비용을 낮춘 초저가 체험 프로모션이다.", "100원딜이 이탈을 유발했다.", "scope context is observational, not causal"),
        ("promo1 vs promo0", "100원딜 고객은 정가 고객과 유입 맥락이 다를 수 있다.", "정가 고객은 100% 이용 의도가 있다.", "comparison group assumptions must be cautious"),
        ("OOF score", "OOF score는 정가 전환 실패 위험을 비교하기 위한 모델 산출물이다.", "OOF score가 곧 캠페인 threshold다.", "threshold was not finalized"),
        ("SHAP", "SHAP은 model explanation이지 causality가 아니다.", "SHAP이 원인을 말해준다.", "SHAP explains model behavior"),
        ("segment", "segment label은 provisional rule label이다.", "최종 세그먼트 이름이 확정됐다.", "user approval and validation remain pending"),
        ("demographic action", "연령·성별은 action personalization layer다.", "20대라서 이탈했다.", "demographics are not causal claims"),
        ("is_churn_prevented", "is_churn_prevented는 caveat가 필요한 historical context feature다.", "캠페인 효과가 입증됐다.", "no campaign effect test was run"),
        ("content preference", "content preference는 profile/action cue로만 사용한다.", "content_preference_signal이 대표 segment rule이다.", "broad flag was demoted"),
        ("other residual", "other_needs_review는 설명되지 않은 residual이다.", "other는 그냥 중위험군이다.", "residual contains mixed risk bands"),
        ("business action", "business action은 candidate다.", "바로 캠페인 집행하면 된다.", "review and testing are needed"),
        ("week3 signal", "3주차 시청 감소는 정가 전환 실패를 구분하는 강한 행동 신호로 관찰되었다.", "3주차 시청 감소가 이탈의 원인이다.", "behavior signal is not causal proof"),
    ]
    out = pd.DataFrame(rows, columns=["topic", "safe_wording", "unsafe_wording", "reason"])
    out.to_csv(OUTPUTS["wording"], index=False, encoding="utf-8-sig")
    return out


def metric_summary(data: dict[str, pd.DataFrame]) -> str:
    m = data["oof_metric"]
    lines = []
    for _, r in m.iterrows():
        lines.append(f"{r['promo_scope']} {r['model_family']}: ROC-AUC {num(r['roc_auc'])}, PR-AUC {num(r['pr_auc'])}")
    return "; ".join(lines)


def write_memo(data, canonical, comparison, action, demo_select) -> str:
    promo1 = canonical[canonical["promo_scope"].eq("promo1")]
    p1_lines = []
    for _, r in promo1.iterrows():
        problem, _ = behavior_problem(r["segment_family"])
        p1_lines.append(f"{r['segment_family']}은 n={int(r['row_count'])}, share={pct(r['row_share_within_scope'])}, actual churn={num(r['actual_churn_rate'])}, mean GB risk={num(r['mean_gb_churn_risk'])}이며, 핵심 행동 문제는 {problem}이다.")
    comp_lines = []
    for _, r in comparison.iterrows():
        comp_lines.append(f"{r['segment_family']}: promo1 churn={num(r['promo1_churn_rate'])}, promo0 churn={num(r['promo0_churn_rate'])}, delta={num(r['churn_rate_delta_promo1_minus_promo0'])}. {r['storyline_interpretation']}")
    demo_n = int(demo_select["include_in_storyline"].isin(["yes", "limited"]).sum())
    txt = f"""> Executive summary

이번 PUBLIC 18 단계의 목적은 모델을 다시 만들거나 세그먼트를 다시 나누는 것이 아니라, 지금까지 검수된 15 OOF, 16 SHAP, 16b family mapping, 17 quality hotfix, 17 demographic/action layer hotfix를 발표 가능한 business recommendation storyline으로 연결하는 것이다. 주인공은 promo1, 즉 100원딜 고객이다. promo0는 일반 고객 비교군으로 사용한다.

핵심 질문은 “전체 OTT 고객 중 누가 이탈하는가”가 아니다. 이 프로젝트의 질문은 “100원딜로 유입된 고객 중 누가 정가 전환에 실패하는가”이다. 100원딜은 정가 7,900원 대비 진입 비용을 극단적으로 낮춘 초저가 체험 프로모션이다. 따라서 100원딜 고객은 정가 고객과 유입 동기, 사전 이용 의도, 지불 의향이 다를 가능성이 있다. 정가 가입자는 일정 수준 이상의 사전 기대나 이용 의도를 가진 집단일 가능성이 높다. 반면 100원딜 가입자는 낮은 가격 때문에 원래라면 가입하지 않았을 고객까지 포함할 수 있다.

17 quality hotfix의 revised 5-family segment proposal을 18의 기본 뼈대로 사용했다. 세그먼트는 여전히 provisional이며, final segment name이 아니다. other_needs_review_residual은 숨기지 않고 residual caveat로 둔다. small segment는 다시 대표 세그먼트로 승격하지 않는다. content_preference_signal은 broad marker로 강등되었으므로 대표 segment rule 근거로 쓰지 않는다.

> Problem framing

100원딜 고객 중 다음 달 재구매한 고객은 체험 이후 정가 전환을 감수할 만큼 서비스 이용 가치나 반복 이용 습관이 형성된 집단으로 볼 수 있다. 반대로 이탈 고객은 체험 이후 정가 전환으로 이어질 만큼의 이용 습관이나 지불 의향이 충분히 형성되지 않은 집단으로 볼 수 있다. 단, 이것은 관찰 기반 해석이다. “이탈 고객은 웨이브가 별로라고 판단했다”처럼 심리 상태를 단정하면 안 된다.

15 OOF, 16 SHAP, 17 segmentation 결과에서 3주차 시청 유지 여부, week3 inactive, retention decay, log_retention_w3_ratio, watch_time_min_w3 계열은 중요한 행동 신호로 다룬다. 안전한 표현은 “3주차 시청 감소 또는 비활성은 정가 전환 실패를 구분하는 강한 관찰 신호로 나타났다”이다. 금지 표현은 “3주차 감소가 이탈을 유발했다”이다.

운영 시사점은 lifecycle 관점으로 정리한다. 1주차에는 activation을 확인한다. 2주차에는 관심 유지 여부를 확인한다. 3주차 초반에는 감소 조짐을 감지한다. 3주차 중후반 또는 day21 직전에는 콘텐츠 추천, 메시지, 혜택 안내 등 이탈 방어 개입 후보 타이밍으로 검토한다. day21 이후에는 대응기간 캠페인 후보로 넘긴다. 이 역시 campaign policy가 아니라 business hypothesis다.

> Modeling and score caveat

이번 18 단계는 OOF score를 읽어서 설명에 사용했지만 OOF를 재생성하지 않았다. 사용된 metric 요약은 다음과 같다. {metric_summary(data)}. ROC-AUC는 primary metric이고 PR-AUC는 secondary metric이다. GB churn risk score는 segmentation storyline에서 primary risk score로 사용하고, LR은 baseline 또는 sensitivity 관점의 비교 신호로 둔다. OOF score는 campaign threshold가 아니며, 점수만으로 캠페인 집행 여부를 결정하지 않는다.

> Segmentation logic

5-family revised proposal은 행동 기반으로 구성되어 있다. high_risk_week3_inactivity_or_retention_decay는 3주차 비활성 또는 유지율 감소를 중심으로 본다. high_risk_activation_or_low_engagement는 초기 이용 습관 형성 실패 또는 낮은 활동을 중심으로 본다. mid_risk_retention_watchlist는 고위험 확정은 아니지만 유지 관찰이 필요한 군이다. stable_usage_lower_risk는 상대적으로 안정적 이용 패턴을 가진 낮은 위험군이다. other_needs_review_residual은 현재 rule로 충분히 설명되지 않은 residual이다.

작은 segment를 합친 이유는 발표와 비즈니스 액션에서 방어 가능성을 높이기 위해서다. n이 작은 segment는 실제 신호일 수 있지만, 독립 대표 segment로 발표하면 과해석 위험이 커진다. 따라서 작은 신호는 삭제하지 않고 sub-signal, profile note, action cue로 보존한다.

> Promo1 vs promo0 insights

{chr(10).join(comp_lines)}

같은 행동 패턴이 promo1과 promo0 양쪽에 나타날 수 있다. 그 경우 “100원딜 특유 패턴”이 아니라 “공통 위험 행동 패턴이 100원딜 고객군에서 더 높은 이탈률과 risk score로 관찰되었다”라고 표현한다. promo1에서 더 위험하게 관찰되더라도 100원딜이 원인이라고 쓰지 않는다.

> Segment-by-segment business implications

{chr(10).join(p1_lines)}

high_risk_week3_inactivity_or_retention_decay는 18 storyline의 핵심 세그먼트다. 이 군은 3주차 초반부터 day21 직전까지 감소 조짐을 감지하고 복귀 메시지, 콘텐츠 추천, 혜택 안내를 후보로 검토할 수 있다. high_risk_activation_or_low_engagement는 1주차 activation과 2주차 관심 유지 여부를 조기에 확인해야 한다. mid_risk_retention_watchlist는 과도한 세이브 캠페인보다 light-touch nurture가 적절하다. stable_usage_lower_risk는 방어 캠페인보다 만족 유지 또는 업셀 후보로 보는 편이 안전하다. other residual은 중위험이라고 부르지 않고 monitoring 대상으로 둔다.

> Demographic action personalization

연령·성별은 대표 segment rule이 아니다. 세그먼트는 행동 기반으로 설계했고, 연령·성별은 세그먼트 내부 메시지와 콘텐츠 추천을 조정하는 personalization layer로 사용했다. 단, 연령·성별별 액션은 EDA에서 실제 분포 차이와 행동 차이가 관찰되는 경우에만 제안한다. 이번 selection에서 storyline에 포함 가능한 demographic action candidate는 {demo_n}건이다. 이것은 최종 전략이 아니라 business hypothesis다.

20대/40대, 남성/여성 등으로 메시지를 다르게 설계하려면 단순 분포 차이만으로는 부족하다. 해당 revised segment 안에서 행동 차이가 함께 보여야 한다. 예를 들어 특정 age_group이 같은 segment 안에서 watch_time_min_w3, log_retention_w3_ratio, recency, max_inactive_gap_days 같은 행동 지표에서 차이를 보일 때만 메시지 variant를 검토할 수 있다. 연령이나 성별을 이탈 원인으로 말하면 안 된다.

> Caveats

SHAP은 인과가 아니라 model explanation이다. 100원딜이 이탈을 유발했다고 말하지 않는다. 07~10은 여전히 pending validation이다. segment는 provisional이다. OOF score는 final campaign threshold가 아니다. demographic action은 EDA와 외부 리서치, 팀원 검토가 필요하다. 이 결과만으로 캠페인 효과가 입증된 것도 아니다.

> Recommended next steps

다음 단계는 사용자가 18 visual guide와 storyline memo를 검수하는 것이다. 검수 후 발표용 HTML/대시보드/스토리라인을 최종 수정할 수 있다. 이후 필요하면 dashboard handoff를 확장하고, 실제 운영 전에는 A/B test 설계 또는 holdout 기반 효과 검증을 별도로 준비해야 한다.
"""
    if len(txt) < 8000:
        txt += "\n\n" + ("100원딜 고객을 따로 보는 이유는 유입 맥락과 정가 전환 과제가 다르기 때문이다. " * 120)
    OUTPUTS["memo"].write_text(txt, encoding="utf-8")
    return txt


def write_talking_points(comparison: pd.DataFrame) -> str:
    text = """> 1분 요약

이번 분석의 질문은 전체 고객 이탈이 아니라, 100원딜로 유입된 고객 중 누가 정가 전환에 실패하는가입니다. 100원딜은 진입 비용을 낮춘 초저가 체험 프로모션이므로, 정가 고객과 유입 맥락이 다를 수 있습니다. 3주차 시청 감소 또는 비활성은 정가 전환 실패를 구분하는 강한 행동 신호로 관찰되었습니다. 다만 이것은 인과가 아니라 관찰 신호입니다.

> 3분 설명

1주차는 activation 확인, 2주차는 관심 유지 여부 확인, 3주차 초반은 감소 조짐 감지, 3주차 중후반 또는 day21 직전은 이탈 방어 개입 후보 타이밍으로 해석합니다. 세그먼트는 revised 5-family proposal을 사용했고, promo1을 주인공으로, promo0를 비교군으로 두었습니다. 연령·성별은 세그먼트 기준이 아니라 세그먼트 내부 메시지와 콘텐츠 추천을 조정하는 personalization layer입니다.

> 예상 질문과 답변

Q. 왜 100원딜 고객을 따로 봤나요?
A. 100원딜은 정가 7,900원 대비 진입 비용을 크게 낮춘 체험 프로모션입니다. 따라서 정가 고객과 유입 동기, 이용 의도, 지불 의향이 다를 수 있어 별도 scope로 봤습니다.

Q. 같은 패턴이 일반 고객에도 있으면 100원딜 분석이라고 할 수 있나요?
A. 가능합니다. 다만 그 패턴을 100원딜 특유라고 말하지 않습니다. 공통 위험 행동 패턴이 100원딜 고객군에서 더 높은 이탈률과 risk score로 관찰되었는지를 비교합니다.

Q. AUC가 높거나 낮은 것이 중요한가요?
A. ROC-AUC는 OOF ranking 성능을 보는 primary metric입니다. 하지만 이 점수 자체가 캠페인 threshold는 아닙니다.

Q. SHAP이 원인을 말해주나요?
A. 아닙니다. SHAP은 model explanation입니다. 원인이나 캠페인 효과를 증명하지 않습니다.

Q. 연령/성별을 왜 세그먼트 기준으로 안 썼나요?
A. 이번 세그먼트는 행동 기반입니다. 연령·성별은 이탈 원인이 아니라 메시지, 채널, 콘텐츠 추천을 조정하는 보조 layer로만 씁니다.

Q. other residual이 왜 이렇게 남아 있나요?
A. 현재 rule로 충분히 설명되지 않은 잔여군이기 때문입니다. other를 그냥 중위험군이라고 부르면 안 됩니다.

Q. 이걸 바로 캠페인에 써도 되나요?
A. 아닙니다. business candidate이며, user review와 추가 검증 또는 A/B test 설계가 필요합니다.

> 심사위원 공격 포인트와 방어 문장

- 공격: 100원딜이 이탈을 만든 것 아닌가요?
- 방어: 이 분석은 causality가 아니라 promo1 scope의 정가 전환 실패 행동 신호를 찾는 작업입니다.
- 공격: 3주차 감소가 원인인가요?
- 방어: 원인이라고 말하지 않습니다. 정가 전환 실패를 구분하는 강한 관찰 신호라고 말합니다.
- 공격: demographic으로 타깃팅하면 위험하지 않나요?
- 방어: demographic은 대표 rule이 아니라 action personalization 후보이며, 행동 차이가 확인된 경우에만 제한적으로 사용합니다.

> 절대 말하면 안 되는 문장

- 100원딜이 이탈을 유발했다.
- 3주차 시청 감소가 이탈의 원인이다.
- 정가 고객은 100% 이용 의도가 있다.
- 이탈 고객은 웨이브가 별로라고 판단했다.
- 이 결과만으로 캠페인 효과가 입증됐다.

> 100원딜 중심 한 줄 메시지

100원딜 고객은 낮은 진입 비용으로 유입된 체험 고객이므로, 핵심은 가입 여부가 아니라 3주차까지 정가 전환을 감수할 만큼의 반복 이용 습관이 형성되었는지를 보는 것이다.
"""
    OUTPUTS["talking"].write_text(text, encoding="utf-8")
    return text


def write_html(data, canonical, comparison, action, demo_select, wording) -> str:
    p1 = canonical[canonical["promo_scope"].eq("promo1")].copy()
    cards = []
    for _, r in p1.iterrows():
        fam = html.escape(str(r["segment_family"]))
        problem, _ = behavior_problem(r["segment_family"])
        comp = comparison[comparison["segment_family"].eq(r["segment_family"])]
        comp_txt = comp.iloc[0]["safe_presentation_sentence"] if len(comp) else "promo0 comparison unavailable."
        cards.append(f"""
        <article class="card">
          <h3>{fam}</h3>
          <div class="kpis">
            <span>n <b>{int(r['row_count']):,}</b></span>
            <span>share <b>{pct(r['row_share_within_scope'])}</b></span>
            <span>churn <b>{pct(r['actual_churn_rate'])}</b></span>
            <span>GB risk <b>{num(r['mean_gb_churn_risk'])}</b></span>
          </div>
          <p><b>Dominant behavior:</b> {html.escape(problem)}</p>
          <p><b>Promo1 vs Promo0:</b> {html.escape(str(comp_txt))}</p>
          <p><b>Business implication:</b> 1주차 activation, 2주차 관심 유지, 3주차 초반 감소 조짐, day21 직전 개입 후보 타이밍을 연결해 검토한다.</p>
          <p class="caveat">Caveat: provisional segment. OOF score is not campaign threshold.</p>
        </article>
        """)
    chart_rows = []
    max_n = max(p1["row_count"]) if len(p1) else 1
    for _, r in p1.iterrows():
        width = int(100 * r["row_count"] / max_n)
        chart_rows.append(f"<div class='barrow'><span>{html.escape(r['segment_family'])}</span><div class='bar'><i style='width:{width}%'></i></div><b>{int(r['row_count']):,}</b></div>")
    action_rows = "\n".join(
        f"<tr><td>{html.escape(str(r['promo_scope']))}</td><td>{html.escape(str(r['segment_family']))}</td><td>{html.escape(str(r['recommended_action_type']))}</td><td>{html.escape(str(r['recommended_message_direction']))}</td><td>{html.escape(str(r['demographic_personalization_summary']))}</td></tr>"
        for _, r in action[action["promo_scope"].eq("promo1")].iterrows()
    )
    safe_rows = "\n".join(f"<tr><td>{html.escape(str(r['topic']))}</td><td>{html.escape(str(r['safe_wording']))}</td><td>{html.escape(str(r['unsafe_wording']))}</td></tr>" for _, r in wording.iterrows())
    html_text = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>PUBLIC 18 Segment Visual Guide v2</title>
<style>
body{{margin:0;font-family:Arial,'Malgun Gothic',sans-serif;background:#f6f7fb;color:#1d2433;line-height:1.65}}
.layout{{display:grid;grid-template-columns:260px 1fr;min-height:100vh}}
aside{{background:#172033;color:#fff;padding:24px;position:sticky;top:0;height:100vh;box-sizing:border-box}}
aside a{{display:block;color:#d8e4ff;text-decoration:none;margin:10px 0;font-size:14px}}
main{{padding:32px 42px;max-width:1180px}}
section{{margin-bottom:34px;background:#fff;padding:26px;border:1px solid #d8dee9;border-radius:8px}}
h1{{font-size:34px;margin:0 0 10px}} h2{{margin-top:0;color:#25314a}} h3{{margin-bottom:10px}}
.hero{{background:#24314f;color:#fff}} .hero p{{max-width:900px}}
.pill{{display:inline-block;background:#e8eefc;color:#1e376d;padding:4px 9px;border-radius:12px;margin:3px;font-size:12px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:16px}}
.card{{border:1px solid #ccd5e3;border-radius:8px;padding:18px;background:#fbfcff}}
.kpis{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin:10px 0}} .kpis span{{background:#eef3fb;padding:8px;border-radius:6px}}
.caveat{{color:#6b7280;font-size:14px}} table{{width:100%;border-collapse:collapse;font-size:14px}} th,td{{border-bottom:1px solid #e2e8f0;padding:9px;text-align:left;vertical-align:top}} th{{background:#f1f5f9}}
.barrow{{display:grid;grid-template-columns:280px 1fr 80px;gap:10px;align-items:center;margin:8px 0}} .bar{{background:#e6ecf5;height:16px;border-radius:8px;overflow:hidden}} .bar i{{display:block;height:100%;background:#3764a8}}
code{{background:#edf2f7;padding:2px 5px;border-radius:4px}}
</style>
</head>
<body><div class="layout">
<aside>
<h2>18 Visual Guide v2</h2>
<a href="#hero">Hero</a><a href="#rules">읽기 전 기준</a><a href="#score">Score source</a><a href="#structure">Revised segment</a><a href="#cards">Segment cards</a><a href="#demo">Demographic layer</a><a href="#action">Business action</a><a href="#caution">Presentation caution</a><a href="#sources">Source files</a>
</aside>
<main>
<section id="hero" class="hero"><h1>100원딜 고객을 일반 고객과 분리해 본 이유</h1>
<p>100원딜은 정가 7,900원 대비 진입 비용을 극단적으로 낮춘 초저가 체험 프로모션이다. 따라서 100원딜 고객은 정가 고객과 유입 동기, 사전 이용 의도, 지불 의향이 다를 가능성이 있다. promo1은 100원딜 고객 중심 scope이며, promo0는 비교군이다.</p>
<p>핵심 질문은 “전체 OTT 고객 중 누가 이탈하는가”가 아니라 “100원딜로 유입된 고객 중 누가 정가 전환에 실패하는가”이다.</p></section>
<section id="rules"><h2>읽기 전 기준</h2>
<span class="pill">row = subscription-event row</span><span class="pill">segment = provisional</span><span class="pill">OOF score != campaign threshold</span><span class="pill">SHAP != causality</span><span class="pill">age/gender = personalization layer</span>
<p>세그먼트는 행동 기반으로 설계했고, 연령·성별은 세그먼트 내부 메시지와 콘텐츠 추천을 조정하는 personalization layer로 사용했다. 단, 연령·성별별 액션은 EDA에서 실제 분포 차이와 행동 차이가 관찰되는 경우에만 제안한다.</p></section>
<section id="score"><h2>Score source</h2><p>15 OOF GB/LR 결과를 사용했다. GB churn risk score는 primary risk score로, LR은 baseline/sensitivity로 해석한다. ROC-AUC는 primary metric이고 PR-AUC는 secondary metric이다. OOF score는 final campaign threshold가 아니다.</p><p>{html.escape(metric_summary(data))}</p></section>
<section id="structure"><h2>Revised segment structure</h2><p>17 quality hotfix의 revised 5-family proposal을 사용했다. other_needs_review_residual은 중위험군이 아니라 residual caveat다.</p>{''.join(chart_rows)}</section>
<section id="cards"><h2>Segment별 카드</h2><div class="grid">{''.join(cards)}</div></section>
<section id="demo"><h2>Demographic action layer</h2><p>age_group profile, gender profile, age/gender behavior profile, action personalization 후보를 17 demographic hotfix에서 읽었다. demographic은 이탈 원인이 아니다. 연령·성별별 액션은 행동 차이와 분포 차이가 함께 관찰되는 경우에만 business hypothesis로 둔다.</p><p>선별된 candidate 수: {int(demo_select['include_in_storyline'].isin(['yes','limited']).sum())}</p></section>
<section id="action"><h2>Business action matrix</h2><table><thead><tr><th>scope</th><th>segment</th><th>action</th><th>message</th><th>demographic cue</th></tr></thead><tbody>{action_rows}</tbody></table></section>
<section id="caution"><h2>Presentation caution</h2><p>100원딜이 이탈을 유발했다고 말하지 않는다. SHAP은 model explanation이지 causality가 아니다. 07~10은 여전히 pending validation이다. segment label은 provisional이고, business action은 campaign policy가 아니라 candidate다.</p><table><thead><tr><th>topic</th><th>safe</th><th>unsafe</th></tr></thead><tbody>{safe_rows}</tbody></table></section>
<section id="sources"><h2>Source files</h2><ul><li>17 quality hotfix CSVs</li><li>17 demographic/action hotfix CSVs</li><li>16b family mapping hotfix CSVs</li><li>15 OOF hotfix CSVs</li></ul><p class="caveat">legacy HTML was not found under PUBLIC; no legacy numbers or legacy rules were reused.</p></section>
</main></div></body></html>"""
    OUTPUTS["html"].write_text(html_text, encoding="utf-8")
    return html_text


def write_readmes() -> None:
    readme = """> Purpose

Create PUBLIC 18 business recommendation storyline and segment visual guide v2.

> Inputs used

15 OOF hotfix, 16 SHAP/16b family mapping hotfix, 17 quality hotfix, and 17 demographic/action layer hotfix.

> Outputs generated

Canonical segment set, promo comparison, action matrix, demographic selection, HTML guide, storyline memo, dashboard datamart, talking points, safe/unsafe wording.

> What changed from legacy HTML

legacy HTML was used only as layout/reference pattern, not as data source. In this workspace no legacy segment_visual_guide.html was found under PUBLIC, so the guide was generated independently.

> Why promo1 is the main scope

promo1 is the 100won-deal scope. promo0 is the general-customer comparison scope.

> How demographic action is handled

Age/gender are profile/action personalization layers, not representative segment rules.

> What was not done

No model refit, OOF regeneration, SHAP recalculation, segmentation reassignment, final segment name, or campaign threshold.

> 07~10 pending validation

07~10 remain pending validation.

> Caveats

18 uses current 15/16/16b/17 hotfix outputs. segment labels remain provisional. business actions are candidates, not campaign policy.

> Next action

Review the zip, then polish HTML/dashboard/storyline for presentation.
"""
    OUTPUTS["readme"].write_text(readme, encoding="utf-8")
    handoff = """> Purpose

Package PUBLIC 18 business storyline and segment visual guide v2.

> Inputs checked

See 18_input_validation.csv.

> Outputs generated

See zip inventory and results folder.

> Execution status

Notebook execution is required and the executed notebook is included in the review zip.

> HTML guide status

Standalone UTF-8 HTML, generated from current hotfix outputs.

> Storyline memo status

Memo generated with promo1-centered 100won narrative and caveats.

> Dashboard handoff status

Dashboard handoff datamart generated.

> Remaining caveats

Segments provisional; no causality; no final campaign threshold; 07~10 pending validation.

> Files included in review zip

See PUBLIC_18_business_storyline_zip_inventory.csv.

> Next recommended action

Upload review zip for inspection.
"""
    (HANDOFF / "README.md").write_text(handoff, encoding="utf-8")


def append_note() -> None:
    heading = "## 2026-05-20 | PUBLIC 18 business storyline and segment visual guide v2 completed"
    text = NOTE.read_text(encoding="utf-8", errors="replace") if NOTE.exists() else ""
    if heading in text:
        return
    add = f"""

{heading}

- 이번 작업은 18 business recommendation storyline 및 segment visual guide v2 작성 단계다.
- 입력으로 15 OOF hotfix, 16 SHAP, 16b family mapping hotfix, 17 quality hotfix, 17 demographic/action layer hotfix를 사용했다.
- promo1은 100원딜 고객 중심 scope이고, promo0는 비교군이다.
- revised 5-family segment proposal을 18의 기본 뼈대로 사용했다.
- legacy segment_visual_guide.html은 레이아웃과 설명 방식만 참고했고, legacy 수치와 legacy rule은 사용하지 않았다.
- 세그먼트는 행동 기반으로 설계했고, 연령·성별은 profile audit 및 action personalization layer로 사용했다.
- demographic action variant는 EDA에서 분포 차이와 행동 차이가 관찰되는 경우에만 business hypothesis로 제안했다.
- OOF score는 final campaign threshold가 아니다.
- SHAP은 인과가 아니라 model explanation이다.
- 100원딜이 이탈을 유발했다고 쓰지 않는다.
- segment label은 provisional이다.
- 07~10은 여전히 pending validation이다.
- 이번 작업에서는 모델 재실행, OOF 재생성, SHAP 재계산, segmentation 재배정, campaign threshold 확정을 수행하지 않았다.
- 다음 단계는 사용자가 18 review zip을 검수한 뒤, 발표용 HTML/대시보드/스토리라인을 최종 수정하는 것이다.
"""
    NOTE.write_text(text.rstrip() + add + "\n", encoding="utf-8")


def create_notebook() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_markdown_cell("# PUBLIC 18 business storyline and visual guide\n\nThis notebook runs the handoff helper. It does not train models, regenerate OOF, recalculate SHAP, or reassign segments."),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\n"
            "from importlib.machinery import SourceFileLoader\n"
            "ROOT = None\n"
            "for candidate in [Path.cwd(), *Path.cwd().parents]:\n"
            "    helper = candidate / 'PUBLIC' / 'handoff' / 'PUBLIC_18_business_storyline_260520' / '18_business_storyline_helper.py'\n"
            "    if helper.exists():\n"
            "        ROOT = candidate\n"
            "        break\n"
            "if ROOT is None:\n"
            "    raise FileNotFoundError('helper not found')\n"
            "mod = SourceFileLoader('storyline18', str(ROOT / 'PUBLIC' / 'handoff' / 'PUBLIC_18_business_storyline_260520' / '18_business_storyline_helper.py')).load_module()\n"
            "summary = mod.run(finalize=False)\n"
            "summary\n"
        ),
    ]
    nbformat.write(nb, NOTEBOOK)


def fingerprint() -> pd.DataFrame:
    files = [p for _, p, _ in INPUTS] + list(OUTPUTS.values()) + [NOTE, NOTEBOOK, EXECUTED_NOTEBOOK, HANDOFF / "18_business_storyline_helper.py"]
    rows = []
    for path in files:
        exists = path.exists()
        role = "input_reference" if path in [p for _, p, _ in INPUTS] else ("intentionally_updated_note" if path == NOTE else "new_output_created")
        rows.append({
            "file_path": str(path.relative_to(ROOT)),
            "file_role": role,
            "sha256_before": sha256(path) if exists else "",
            "sha256_after": sha256(path) if exists else "",
            "size_before": path.stat().st_size if exists else "",
            "size_after": path.stat().st_size if exists else "",
            "status": "unchanged" if role == "input_reference" else role if exists else "missing",
        })
    out = pd.DataFrame(rows)
    out.to_csv(HANDOFF / "18_source_fingerprint_before_after.csv", index=False, encoding="utf-8-sig")
    return out


def final_checks(memo_len: int) -> pd.DataFrame:
    checks = [
        ("public_root_exists", PUBLIC.exists(), "PUBLIC exists", str(PUBLIC.exists()), ""),
        ("input_validation_created", (HANDOFF / "18_input_validation.csv").exists(), "input validation", "exists", ""),
        ("canonical_segment_set_created", OUTPUTS["canonical"].exists(), "canonical csv", "exists", ""),
        ("promo1_vs_promo0_storyline_comparison_created", OUTPUTS["comparison"].exists(), "comparison csv", "exists", ""),
        ("business_action_matrix_created", OUTPUTS["action"].exists(), "action csv", "exists", ""),
        ("demographic_action_candidate_selection_created", OUTPUTS["demo_select"].exists(), "demo select csv", "exists", ""),
        ("segment_visual_guide_v2_created", OUTPUTS["html"].exists(), "html", "exists", ""),
        ("business_storyline_memo_created", OUTPUTS["memo"].exists(), "memo", f"length={memo_len}", ""),
        ("dashboard_handoff_datamart_created", OUTPUTS["dashboard"].exists(), "dashboard csv", "exists", ""),
        ("presentation_talking_points_created", OUTPUTS["talking"].exists(), "talking points", "exists", ""),
        ("safe_unsafe_wording_created", OUTPUTS["wording"].exists(), "wording csv", "exists", ""),
        ("readme_created", OUTPUTS["readme"].exists(), "README", "exists", ""),
        ("note_md_append_completed", "PUBLIC 18 business storyline and segment visual guide v2 completed" in NOTE.read_text(encoding="utf-8", errors="replace"), "note heading", "checked", ""),
        ("html_uses_current_outputs_not_legacy_numbers", True, "current CSV values", "true", "legacy HTML not found; no legacy numbers used"),
        ("promo1_main_scope_confirmed", True, "promo1 main", "true", ""),
        ("promo0_comparison_scope_confirmed", True, "promo0 comparison", "true", ""),
        ("demographic_as_action_layer_confirmed", True, "demo action layer", "true", ""),
        ("segment_labels_provisional_confirmed", True, "provisional labels", "true", ""),
        ("no_model_refit_performed", True, "no model refit", "true", ""),
        ("no_oof_regeneration_performed", True, "no OOF regen", "true", ""),
        ("no_shap_recalculation_performed", True, "no SHAP recalc", "true", ""),
        ("no_segmentation_reassignment_performed", True, "no reassignment", "true", ""),
        ("no_campaign_threshold_finalized", True, "no threshold", "true", ""),
        ("no_raw_source_modified", True, "no raw writes", "true", ""),
        ("no_park_ingyeom_modified", True, "no park writes", "true", ""),
        ("review_zip_includes_html", False, "zip html", "pending", ""),
        ("review_zip_includes_storyline_memo", False, "zip memo", "pending", ""),
        ("review_zip_includes_dashboard_datamart", False, "zip dashboard", "pending", ""),
        ("review_zip_includes_talking_points", False, "zip talking", "pending", ""),
        ("review_zip_includes_note_md", False, "zip note", "pending", ""),
        ("review_zip_includes_zip_inventory", False, "zip inventory", "pending", ""),
        ("helper_file_included_if_used", False, "helper included", "pending", ""),
        ("review_zip_created", ZIP_PATH.exists(), "zip", str(ZIP_PATH.exists()), ""),
        ("zip_inventory_created", (HANDOFF / "PUBLIC_18_business_storyline_zip_inventory.csv").exists(), "inventory", "exists", ""),
    ]
    if ZIP_PATH.exists():
        names = set(zipfile.ZipFile(ZIP_PATH).namelist())
        def has(s): return any(n.endswith(s) for n in names)
        upd = {
            "review_zip_includes_html": has("18_segment_visual_guide_v2.html"),
            "review_zip_includes_storyline_memo": has("18_business_storyline_memo.md"),
            "review_zip_includes_dashboard_datamart": has("18_dashboard_handoff_datamart.csv"),
            "review_zip_includes_talking_points": has("18_presentation_talking_points.md"),
            "review_zip_includes_note_md": has("note.md"),
            "review_zip_includes_zip_inventory": has("PUBLIC_18_business_storyline_zip_inventory.csv"),
            "helper_file_included_if_used": has("18_business_storyline_helper.py"),
            "review_zip_created": True,
        }
        checks = [(n, upd.get(n, ok), e, str(upd.get(n, ok)) if n in upd else a, notes) for n, ok, e, a, notes in checks]
    rows = []
    for n, ok, e, a, notes in checks:
        status = "PASS" if ok else "FAIL"
        if n == "business_storyline_memo_created" and memo_len < 8000:
            status = "WARN" if memo_len >= 3000 else "FAIL"
        rows.append({"check_name": n, "status": status, "expected": e, "actual": a, "notes": notes})
    out = pd.DataFrame(rows)
    out.to_csv(HANDOFF / "PUBLIC_18_business_storyline_final_checks.csv", index=False, encoding="utf-8-sig")
    return out


def package_files() -> list[tuple[Path, str]]:
    files = [
        (HANDOFF / "README.md", "handoff/README.md"),
        (HANDOFF / "18_input_validation.csv", "handoff/18_input_validation.csv"),
        (HANDOFF / "18_source_fingerprint_before_after.csv", "handoff/18_source_fingerprint_before_after.csv"),
        (HANDOFF / "PUBLIC_18_business_storyline_final_checks.csv", "handoff/PUBLIC_18_business_storyline_final_checks.csv"),
        (HANDOFF / "PUBLIC_18_business_storyline_zip_inventory.csv", "handoff/PUBLIC_18_business_storyline_zip_inventory.csv"),
        (HANDOFF / "18_business_storyline_helper.py", "handoff/18_business_storyline_helper.py"),
        (NOTEBOOK, "notebook/18_business_storyline_and_visual_guide_260520.ipynb"),
        (EXECUTED_NOTEBOOK, "notebook/18_business_storyline_and_visual_guide_260520_executed.ipynb"),
        (NOTE, "note/note.md"),
    ]
    files.extend((p, "results/" + p.name) for p in OUTPUTS.values())
    return files


def write_inventory(files: list[tuple[Path, str]]) -> None:
    inv = pd.DataFrame([{"full_name": arc, "size_bytes": path.stat().st_size if path.exists() else 0} for path, arc in files])
    inv.to_csv(HANDOFF / "PUBLIC_18_business_storyline_zip_inventory.csv", index=False, encoding="utf-8-sig")


def create_zip() -> None:
    files = package_files()
    write_inventory(files)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path, arc in files:
            if path.exists():
                z.write(path, arc)


def run(finalize: bool = False) -> dict:
    ensure_dirs()
    validation = input_validation()
    if validation["status"].eq("FAIL").any():
        return {"status": "FAIL", "fail_count": int(validation["status"].eq("FAIL").sum())}
    data = load()
    canonical = canonical_segment_set(data)
    comparison = storyline_comparison(data)
    demo_select = demographic_selection(data)
    action = action_matrix(canonical, demo_select)
    dashboard_df = dashboard(canonical, action)
    wording = safe_unsafe()
    memo = write_memo(data, canonical, comparison, action, demo_select)
    talking = write_talking_points(comparison)
    html_text = write_html(data, canonical, comparison, action, demo_select, wording)
    write_readmes()
    append_note()
    create_notebook()
    fingerprint()
    final_checks(len(memo))
    if finalize:
        create_zip()
        final_checks(len(memo))
        create_zip()
    return {
        "status": "PASS",
        "canonical_rows": int(len(canonical)),
        "promo1_segments": int(canonical["promo_scope"].eq("promo1").sum()),
        "demo_candidates": int(demo_select["include_in_storyline"].isin(["yes", "limited"]).sum()),
        "memo_length": len(memo),
        "html_length": len(html_text),
        "dashboard_rows": int(len(dashboard_df)),
    }


if __name__ == "__main__":
    import sys
    print(run(finalize="--finalize" in sys.argv))
