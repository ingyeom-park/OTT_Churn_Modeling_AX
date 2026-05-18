from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path.cwd()
PARK = ROOT / "park.ingyeom"
SRC = PARK / "project_guide.html"
DST = PARK / "project_guide_v2.html"
AUDIT = PARK / "reports" / "audits"
ZIP_DIR = PARK / "zip"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def rows(rel: str) -> list[dict[str, str]]:
    path = PARK / rel
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fnum(value: str) -> float:
    return float(value) if value not in ("", None) else 0.0


def pct(value: float, ndigits: int = 1) -> str:
    return f"{value * 100:.{ndigits}f}%"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def js(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False)


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


SOURCE_FILES = [
    ("park.ingyeom/project_guide.html", "original_html"),
    ("park.ingyeom/project_guide_v2.html", "revised_html"),
    ("park.ingyeom/reports/audits/06x_dataset_generation_260515/06x_row_policy_audit.csv", "core_csv"),
    ("park.ingyeom/reports/audits/06x_dataset_generation_260515/06x_dataset_comparison_summary.csv", "core_csv"),
    ("park.ingyeom/reports/audits/06x_dataset_generation_260515/06x_model_feature_lists.csv", "core_csv"),
    ("park.ingyeom/reports/audits/07x_feature_mapping_AARRR_260515/07x_feature_mapping_master.csv", "core_csv"),
    ("park.ingyeom/reports/audits/07x_feature_mapping_AARRR_260515/07x_AARRR_summary_by_feature_set.csv", "core_csv"),
    ("park.ingyeom/reports/audits/08x_promotion_nonpromotion_EDA_260516/08x_promotion_target_summary.csv", "core_csv"),
    ("park.ingyeom/reports/audits/09x_promotion_repurchase_2x2_EDA_260516/09x_2x2_cohort_summary.csv", "core_csv"),
    ("park.ingyeom/reports/models/14x_lightweight_candidate_tuning_260516/14x_model_summary_by_scope.csv", "core_csv"),
    ("park.ingyeom/reports/models/14x_lightweight_candidate_tuning_260516/14x_vs_12x_comparison.csv", "optional_core_csv"),
    ("park.ingyeom/reports/audits/15x_payment_device_sensitivity_260516/15x_payment_removed_vs_original_comparison.csv", "core_csv"),
    ("park.ingyeom/reports/audits/15x_payment_device_sensitivity_260516/15x_model_summary_by_scope.csv", "core_csv"),
    ("park.ingyeom/reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_global_importance.csv", "core_csv"),
    ("park.ingyeom/reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_family_importance.csv", "core_csv"),
    ("park.ingyeom/reports/segments/17x_segmentation_design_260516/17x_segment_summary.csv", "core_csv"),
    ("park.ingyeom/reports/segments/17x_segmentation_design_260516/17x_representative_segment_rules.csv", "core_csv"),
    ("park.ingyeom/reports/segments/17x_segmentation_design_260516/17x_internal_multiflag_definitions.csv", "core_csv"),
    ("park.ingyeom/reports/segments/17x_segmentation_design_260516/17x_score_source_selection.csv", "core_csv"),
    ("park.ingyeom/reports/storyline/18x_business_recommendation_storyline_260518/18x_segment_to_message_strategy.csv", "core_csv"),
    ("park.ingyeom/reports/storyline/18x_business_recommendation_storyline_260518/18x_safe_unsafe_wording.csv", "core_csv"),
    ("park.ingyeom/reports/storyline/18x_business_recommendation_storyline_260518/18x_mentor_QA_defense.csv", "core_csv"),
    ("park.ingyeom/reports/storyline/18x_business_recommendation_storyline_260518/18x_open_risks.csv", "core_csv"),
    ("park.ingyeom/reports/audits/15x_payment_device_sensitivity_260516/15x_recommendation_for_canonical_feature_contract.csv", "core_csv"),
    ("park.ingyeom/reports/audits/15x_payment_device_sensitivity_260516/15x_safe_unsafe_wording.csv", "core_csv"),
]


VAR_KO = {
    "watch_time_min_w1": "1주차 총 시청 시간, 분 단위",
    "watch_time_min_w2": "2주차 총 시청 시간, 분 단위",
    "watch_time_min_w3": "3주차 총 시청 시간, 분 단위",
    "watch_session_w1": "1주차 시청 세션 횟수",
    "watch_session_w2": "2주차 시청 세션 횟수",
    "watch_session_w3": "3주차 시청 세션 횟수",
    "retention_w2_ratio": "1주차 대비 2주차 시청 유지 비율",
    "retention_w3_ratio": "1주차 대비 3주차 시청 유지 비율",
    "diff_between_w2_w1": "2주차 시청시간 - 1주차 시청시간, 증감 신호",
    "diff_between_w3_w1": "3주차 시청시간 - 1주차 시청시간, 증감 신호",
    "diff_between_w3_w2": "3주차 시청시간 - 2주차 시청시간, 증감 신호",
    "avg_gap_w1_watch_days": "1주차 내 시청일 간 평균 간격, 일 단위",
    "avg_gap_w2_watch_days": "2주차 내 시청일 간 평균 간격, 일 단위",
    "avg_gap_w3_watch_days": "3주차 내 시청일 간 평균 간격, 일 단위",
    "is_cold_start_3d_fixed": "구독 후 3일 이내 첫 시청 여부, row-level 재계산 fixed 버전",
    "is_cold_start_7d_fixed": "구독 후 7일 이내 첫 시청 여부, row-level 재계산 fixed 버전",
    "is_only_w1": "1주차에만 시청하고 2~3주차에는 시청하지 않은 여부",
    "is_only_w2": "2주차에만 시청한 여부",
    "is_only_w3": "3주차에만 시청한 여부",
    "is_w1_over_50pct": "1주차 시청 비중이 전체 시청의 50% 초과인지 여부",
    "is_w2_over_50pct": "2주차 시청 비중이 전체 시청의 50% 초과인지 여부",
    "is_w3_over_50pct": "3주차 시청 비중이 전체 시청의 50% 초과인지 여부",
    "is_promotion": "100원딜 프로모션 유입 여부, 1=프로모션, 0=일반",
    "drama_ratio": "전체 시청 콘텐츠 중 드라마 장르 비율",
    "family_animation_ratio": "전체 시청 콘텐츠 중 가족/애니메이션 장르 비율",
    "romance_ratio": "전체 시청 콘텐츠 중 로맨스 장르 비율",
    "thriller_crime_ratio": "전체 시청 콘텐츠 중 스릴러/범죄 장르 비율",
    "action_adventure_ratio": "전체 시청 콘텐츠 중 액션/어드벤처 장르 비율",
    "age_group": "나이대 그룹, 인구통계 대리 변수",
    "is_user_verified": "본인인증 완료 여부, 인증 상태 대리 변수",
    "is_female": "여성 여부, 인구통계 대리 변수",
    "is_male": "남성 여부, 인구통계 대리 변수",
    "is_basic": "베이직 요금제 여부",
    "is_standard": "스탠다드 요금제 여부",
    "is_premium": "프리미엄 요금제 여부",
    "is_churn_prevented": "이전 이탈 방지 이력 여부, 유지 맥락 변수",
    "churn_risk": "1 - repurchase_score (모델 기반 재구매 가능성 점수), 모델 기반 이탈 위험 점수",
    "repurchase_score": "모델 기반 재구매 가능성 점수",
    "risk_percentile_desc": "이탈 위험 점수를 높은 순서로 정렬한 백분위",
    "flag_high_risk_top20": "이탈 위험 점수 상위 20% 해당 여부, 모델 기반 점수 백분위",
    "flag_low_risk_stable": "이탈 위험 점수 하위 안정 구간과 안정적 유지 패턴 여부",
    "flag_week3_inactive": "3주차 시청 비활성 여부",
    "flag_week3_drop": "3주차 시청시간이 2주차보다 감소했는지",
    "flag_retention_decay": "3주차 유지 비율이 2주차보다 낮거나 기준 미만인지",
    "flag_only_w1": "1주차에만 시청한 패턴",
    "flag_cold_start_weak": "fixed cold_start 기반 초기 활성화 약화 플래그",
    "flag_low_activity": "전체 시청시간 또는 시청횟수 하위권",
    "flag_genre_focused": "특정 장르 비율이 높은 콘텐츠 취향 대리 신호",
    "flag_new_movie_oriented": "신작 지향 대리 신호",
    "flag_old_movie_oriented": "구작 지향 대리 신호",
}


SEG_KO = {
    "high_risk_week3_inactive_or_drop": "3주차 비활성·감소 고위험 후보",
    "high_risk_only_w1_or_cold_start_weak": "초기 활성화 약화 고위험 후보",
    "high_risk_low_activity": "저활동 고위험 후보",
    "medium_risk_retention_decay": "주차별 시청 감소 중위험 후보",
    "content_preference_target_candidate": "콘텐츠 취향 대리 신호 보유 추천 후보",
    "stable_retained_user": "안정 재구매 가능성 높은 후보",
    "general_observation": "일반 관찰 대상",
}


SEG_EXPLAIN = {
    "high_risk_week3_inactive_or_drop": (
        "모델 위험도 상위 20%이면서, 관측창 마지막 주인 3주차에 안 봤거나 2주차보다 시청이 줄었거나 retention이 무너진 row입니다.",
        "처음에는 보다가 마지막 주에 식은 사람에 가깝습니다. 이탈 확정이 아니라 3주차에 식어가는 신호가 관측된 고위험 후보입니다.",
        "day21 직후 이전 관측창 콘텐츠 대리 신호 기반 재진입 추천 후보"
    ),
    "high_risk_only_w1_or_cold_start_weak": (
        "모델 위험도 상위 20%이면서, 1주차에만 활동했거나 fixed cold_start 기반 약화 조건을 만족하는 row입니다. 단, 1순위 segment에 먼저 걸리지 않은 row입니다.",
        "3주차 감소형이라기보다 초반에 시청 습관이 안정적으로 형성되지 않은 유형입니다.",
        "day7~day21 사이 낮은 마찰 온보딩, 재방문 유도 후보"
    ),
    "high_risk_low_activity": (
        "모델 위험도 상위 20%이면서, 전체 day0~20 시청시간 또는 시청횟수가 하위권인 row입니다. 단, 1~2순위 segment에 먼저 걸리지 않은 row입니다.",
        "보다가 식은 사람이라기보다 애초에 거의 안 본 사람에 가깝습니다.",
        "과한 개인화보다 낮은 강도의 broad recommendation 후보"
    ),
    "medium_risk_retention_decay": (
        "위험도 상위 20%까지는 아니지만 상위 20~50% 구간에 있고, 3주차 retention이 무너지는 row입니다.",
        "아직 최악의 고위험은 아니지만 사용하던 사람이 week2~3에 식어가는 조기 경고군입니다.",
        "week2~3 감소 감지 후 day21 전후 유지 메시지 후보"
    ),
    "content_preference_target_candidate": (
        "고위험 상위 20%도 아니고 저활동자도 아니며, 장르 집중·신작 선호·구작 선호 중 하나 이상의 콘텐츠 취향 대리 신호가 관측된 row입니다.",
        "이탈 방어 타깃이라기보다 콘텐츠 추천·유지 강화 후보에 가깝습니다. Movie_Master category mapping 기반 대리 신호이므로 진짜 취향이라고 단정하지 않습니다.",
        "유사 장르 추천, 추천 슬롯 최적화 후보"
    ),
    "stable_retained_user": (
        "모델 위험도 하위권이고 3주차 retention이 안정적인 row입니다. 단, 앞선 content_preference_target_candidate에 먼저 걸리지 않은 row일 수 있습니다.",
        "재구매 가능성이 높아 보이므로 방어성 할인보다는 유지/업셀 후보에 가깝습니다.",
        "정기 만족도 접점, 업셀 타진 후보"
    ),
    "general_observation": (
        "1~6순위 조건 중 어디에도 배정되지 않은 나머지 row입니다.",
        "특징이 없다는 뜻이 아니라, 이번 representative segment rule에서 명확한 대표 행동 패턴으로 배정되지 않은 잔여 집합입니다.",
        "추가 모니터링과 정보 수집 우선"
    ),
}


def source_block(*names: str) -> str:
    items = "".join(f"<li>{esc(n)}</li>" for n in names if (PARK / n).exists())
    return f"<details class=\"source-details\"><summary>근거 파일 보기</summary><div class=\"detail-body\"><ul>{items}</ul></div></details>"


def section_pattern(section_id: str) -> re.Pattern[str]:
    return re.compile(rf"<!-- ===== [^\n]* ===== -->\n<section id=\"{section_id}\">.*?</section>", re.S)


def replace_section(text: str, section_id: str, content: str) -> str:
    return section_pattern(section_id).sub(content, text)


def build():
    html_text = read_text(SRC)
    html_text = html_text.replace(
        "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Apple SD Gothic Neo', sans-serif;",
        "font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;",
    )
    html_text = html_text.replace("100원딜 OTT 이탈 분석 — 프로젝트 해설서", "100원딜 OTT 이탈 분석 — 프로젝트 해설서 v2")
    html_text = html_text.replace(
        "이 문서는 프로젝트를 처음 보는 사람도 구조를 완전히 이해할 수 있도록 만든 설명형 가이드입니다.",
        "v2는 core source CSV 기준으로 오류 표현을 고치고, 팀원이 숫자의 흐름과 세그먼트 배정을 직관적으로 따라가도록 시각화를 크게 늘린 설명형 가이드입니다.",
    )

    css_extra = """
.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 18px 0; }
.chart-card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px; min-height: 280px; }
.chart-card h4 { margin-bottom: 12px; font-size: 14px; }
.chart-card canvas {
  display: block;
  width: 100% !important;
  height: 260px !important;
  max-height: 260px !important;
}
.chart-card.wide canvas,
#row_waterfall,
#observed_diff_chart,
#auc_chart,
#shap_top_chart,
#recommendation_priority_chart {
  height: 220px !important;
  max-height: 220px !important;
}
.source-details ul { padding-left: 18px; line-height: 1.7; }
.pill-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.var-pill { display: inline-block; padding: 3px 7px; border-radius: 4px; border: 1px solid var(--border); background: var(--surface2); font-size: 11px; color: var(--text2); margin: 2px; }
.explain-block { background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 18px 22px; margin: 18px 0; }
.explain-block h3 { font-size: 16px; margin-bottom: 10px; }
.plain-list { padding-left: 18px; color: var(--text2); font-size: 13px; line-height: 1.8; }
.callout-safe { border-left: 4px solid var(--success); }
.callout-warn { border-left: 4px solid var(--warn); }
.callout-danger { border-left: 4px solid var(--danger); }
.mini-caption { color: var(--text3); font-size: 12px; margin-top: 8px; }
.wide { grid-column: 1 / -1; }
@media (max-width: 900px) { .chart-grid { grid-template-columns: 1fr; } }
"""
    html_text = html_text.replace("hr.section-hr { border: none; border-top: 1px solid var(--border); margin: 28px 0; }\n</style>", f"hr.section-hr {{ border: none; border-top: 1px solid var(--border); margin: 28px 0; }}\n{css_extra}\n</style>")

    row_policy = rows("reports/audits/06x_dataset_generation_260515/06x_row_policy_audit.csv")[0]
    dup_audit = rows("reports/audits/01_data_contract_260513/01_user_key_duplicate_audit.csv")
    dup_map = {r["metric"]: r["value"] for r in dup_audit}
    data_section = f"""<!-- ===== 3. DATA ===== -->
<section id="data">
  <div class="section-header"><h2>데이터 구조 이해</h2></div>
  <div class="meta-block">
    <div class="meta-title">섹션 메타</div>
    <div class="meta-row"><span class="meta-label">이 섹션이 말하는 것</span><span class="meta-value">원본 데이터의 크기, 중복 처리, 코호트 분리 기준</span></div>
    <div class="meta-row"><span class="meta-label">왜 중요한가</span><span class="meta-value">23,079라는 숫자가 어디서 왔는지 모르면 후속 통계 해석이 흔들립니다.</span></div>
    <div class="meta-row"><span class="meta-label">오해 금지</span><span class="meta-value">USER_KEY 중복은 고객 중복이 아니라 동일 고객의 여러 구독 이벤트 row일 수 있으므로 제거 대상이 아닙니다.</span></div>
    <div class="meta-row"><span class="meta-label">source</span><span class="meta-value">06x_row_policy_audit.csv, 06x_dataset_comparison_summary.csv, 01_user_key_duplicate_audit.csv</span></div>
  </div>
  <div class="chart-grid">
    <div class="chart-card wide">
      <h4>원본 row에서 분석 cohort까지의 변화 <span class="src">[06x]</span></h4>
      <canvas id="row_waterfall" height="120"></canvas>
      <div class="mini-caption">원본 23,343행에서 구독 기간 21일 미만 238행을 제외하고, 그 뒤 남은 완전중복 추가 행 26행을 제거해 분석 cohort 23,079행이 됩니다.</div>
      {source_block("reports/audits/06x_dataset_generation_260515/06x_row_policy_audit.csv", "reports/audits/06x_dataset_generation_260515/06x_dataset_comparison_summary.csv")}
    </div>
  </div>
  <div class="card-grid col4">
    <div class="card"><div class="stat-number">{row_policy['raw_source_rows']}</div><div class="stat-label">원본 행</div><span class="src">[01x]</span><div class="stat-explain">원본 기준 pandas duplicated() 추가 행은 48개입니다.</div></div>
    <div class="card"><div class="stat-number">- {row_policy['duration_lt_21_count']}</div><div class="stat-label">duration &lt; 21일 제외</div><span class="src">[06x]</span><div class="stat-explain">day0~20 관측창을 온전히 채울 수 없는 row입니다.</div></div>
    <div class="card"><div class="stat-number">- {row_policy['full_duplicate_extra_after_duration_count']}</div><div class="stat-label">필터 후 완전중복 추가 행 제거</div><span class="src">[06x]</span><div class="stat-explain">구독 기간 필터 후 남은 완전중복 추가 행입니다.</div></div>
    <div class="card"><div class="stat-number">{row_policy['primary_main_cohort_rows']}</div><div class="stat-label">분석 cohort 행</div><span class="src">[06x]</span><div class="stat-explain">고객 수가 아니라 구독 이벤트 row 수입니다.</div></div>
  </div>
  <div class="card">
    <h4>duplicate 48과 26은 왜 충돌하지 않는가?</h4>
    <p style="font-size:13px;color:var(--text2);">원본 기준 pandas duplicated() 추가 행은 48개이고, 원본 중복 그룹에 속한 전체 행은 92개입니다. 이후 구독 기간 21일 미만 필터를 먼저 적용하면 남은 완전중복 추가 행이 26개가 됩니다. 따라서 06x row policy에서 제거한 완전중복 추가 행은 26개이며, 48과 26은 서로 다른 시점의 숫자입니다.</p>
  </div>
  <div class="card">
    <h4>USER_KEY 중복에 대한 이해 <span class="src">[01x]</span></h4>
    <table><tr><th>항목</th><th>수치</th><th>해석</th></tr>
      <tr><td>중복 USER_KEY 수</td><td>{dup_map.get('duplicated_USER_KEY_key_count','143')}개</td><td>동일 사용자가 여러 구독 이벤트를 가질 수 있습니다.</td></tr>
      <tr><td>중복 USER_KEY에 속한 행</td><td>{dup_map.get('rows_belonging_to_duplicated_USER_KEY_values','352')}행</td><td>사람 수가 아니라 이벤트 row 수입니다.</td></tr>
      <tr><td>처리 방식</td><td>제거하지 않음</td><td>분석 단위를 구독 이벤트 row로 유지합니다.</td></tr>
    </table>
  </div>
</section>"""
    html_text = replace_section(html_text, "data", data_section)

    feature_section = build_feature_section()
    html_text = replace_section(html_text, "features", feature_section)
    html_text = replace_section(html_text, "aarrr", build_aarrr_section())
    html_text = replace_section(html_text, "cohort", build_cohort_section())
    html_text = replace_section(html_text, "modeling", build_modeling_section())
    html_text = replace_section(html_text, "shap", build_shap_section())
    html_text = replace_section(html_text, "segments", build_segments_section())
    html_text = replace_section(html_text, "recommendations", build_recommendation_section())

    html_text = html_text.replace("watch_time_w3가 높다고", "watch_time_min_w3 (3주차 총 시청 시간, 분 단위)가 높다고")
    html_text = html_text.replace("watch_time_w3 값이", "watch_time_min_w3 (3주차 총 시청 시간, 분 단위) 값이")
    html_text = html_text.replace("is_cold_start_3d/7d", "is_cold_start_3d_fixed / is_cold_start_7d_fixed")
    html_text = html_text.replace("watch_time_w1/w2/w3", "watch_time_min_w1 / watch_time_min_w2 / watch_time_min_w3")
    html_text = html_text.replace("최고 모델 AUC", "후보 기준 AUC")
    html_text = html_text.replace("최종 채택 모델", "해석·세그먼트 설계 기준 후보 모델")
    html_text = html_text.replace("최종 채택 AUC", "후보 기준 AUC")
    html_text = html_text.replace("최종 채택 피처셋", "payment 제거 후 해석·세그먼트 설계 input 피처셋")
    repeated_label = "<strong>" + "그래서 이게 " + "무슨 뜻인가?" + "</strong> "
    html_text = html_text.replace(repeated_label, "")
    html_text = html_text.replace("최종 실행 결과만 반영", "현재 검증된 실행 결과를 기준으로 반영")
    html_text = html_text.replace("최종 코호트", "분석 cohort")
    html_text = html_text.replace("최종 분석 데이터셋", "분석 cohort")
    html_text = html_text.replace("최종 한 줄 결론", "가이드 한 줄 결론")
    html_text = html_text.replace(
        "80개 피처를 AARRR 프레임워크로 분류. Retention 39개가 가장 많음. Needs_user_review 4개(payment_is_* 관련) 식별.",
        "80개 피처를 AARRR 프레임워크로 분류. Retention 39개가 가장 많음. Needs_user_review 4개는 age_group (나이대 그룹), is_female (여성 여부), is_male (남성 여부), is_user_verified (본인인증 완료 여부)이며, payment_is_*는 07x에서 Acquisition_context였다가 15x에서 해석 리스크 때문에 결제기기 제거 민감도 기준으로 분리."
    )
    html_text = html_text.replace(
        "LightGBM expanded가 대부분 scope에서 최고 성능. nonpromotion 0.8838, overall_with 0.8773. LightGBM을 canonical 모델로 선정.",
        "LightGBM expanded가 12x 모델 패밀리 비교에서 후보 기준으로 강세. nonpromotion 0.8838, overall_with 0.8773. 이후 14x Optuna 후보와 15x payment 제거 민감도 분석으로 이어짐."
    )
    html_text = html_text.replace(
        "4개 결제 방식 피처 제거 실험. 평균 AUC 변화량 +0.0036으로 중립~소폭 개선. 시청 기기가 아닌 과금 환경 대리 변수라는 해석 리스크 때문에 제거 기준으로 검토. → expanded_no_payment_device(76/75개) 피처셋 정리.",
        "4개 payment_is_* 피처 제거 민감도 실험. 제거 후 AUC 변화는 대체로 중립~소폭 개선이며, 시청 기기가 아닌 과금 환경 대리 변수라는 해석 리스크 때문에 expanded_no_payment_device(76/75개)를 16x 해석·17x 세그먼트 설계 입력으로 검토."
    )
    html_text = html_text.replace(
        "overall_with_promotion LightGBM 기준: usage_retention_behavior 패밀리가 SHAP 합계 2.877로 1위. 개별 피처 1위: watch_time_min_w3. is_promotion 3위(0.376). 인과 해석 금지.",
        "overall_with_promotion LightGBM 기준: usage_retention_behavior 패밀리가 SHAP 합계 2.877로 1위. 개별 피처 1위는 watch_time_min_w3이고, is_promotion은 개별 feature 기준 2위(0.376)이며 acquisition_split_key family 기준 3위. 인과 해석 금지."
    )
    ui_replacements = {
        "row ≠ 고객": "row는 고객 수가 아님",
        "분석 단위는 <strong>subscription-event row</strong>입니다. USER_KEY에 중복이 있어(143명 = 352 rows) 이 문서의 모든 수치는 <strong>행(row) 수</strong>이지 고객 수가 아닙니다.": "분석 단위는 <strong>구독 이벤트 row</strong>입니다. USER_KEY에 중복이 있어(143명 = 352행) 이 문서의 모든 수치는 <strong>행 수</strong>이지 고객 수가 아닙니다.",
        "③ segment = provisional": "③ 세그먼트 = 임시 대표 라벨",
        "분석 대상 subscription-event rows": "분석 대상 구독 이벤트 행",
        "후보 기준 AUC (LightGBM, nonpromotion)": "후보 기준 AUC (LightGBM, 비프로모션 row)",
        "100원딜 여부(is_promotion)는 코호트 분리 기준이자 모델 피처이지만": "is_promotion (100원딜 프로모션 유입 여부)은 코호트 분리 기준이자 모델 피처이지만",
        "repurchase_score 및 churn_risk 계산": "repurchase_score (모델 기반 재구매 가능성 점수) 및 churn_risk (1 - repurchase_score, 모델 기반 이탈 위험 점수) 계산",
        "churn_risk = 1 − repurchase_score": "churn_risk (모델 기반 이탈 위험 점수) = 1 − repurchase_score (모델 기반 재구매 가능성 점수)",
        "repurchase_score (모델 기반 재구매 가능성 점수) 및 churn_risk (1 - repurchase_score, 모델 기반 이탈 위험 점수) 계산": "repurchase_score (모델 기반 재구매 가능성 점수) 및 churn_risk (1 - repurchase_score (모델 기반 재구매 가능성 점수), 모델 기반 이탈 위험 점수) 계산",
        "churn_risk (1 - repurchase_score, 모델 기반 이탈 위험 점수)": "churn_risk (1 - repurchase_score (모델 기반 재구매 가능성 점수), 모델 기반 이탈 위험 점수)",
        "재구매율 vs 이탈위험(churn_risk)": "재구매율 vs 이탈위험 (churn_risk (모델 기반 이탈 위험 점수))",
        "is_cold_start_3d / is_cold_start_7d처럼 _fixed가 빠진 이름은 실제 모델 피처명처럼 쓰지 않습니다. watch_time_min_w1 / watch_time_min_w2 / watch_time_min_w3도 표시 축약이 아니라 실제 컬럼명은 watch_time_min_w1/2/3입니다.": "is_cold_start_3d / is_cold_start_7d처럼 _fixed가 빠진 이름은 실제 모델 피처명처럼 쓰지 않습니다. 실제 컬럼명은 is_cold_start_3d_fixed (구독 후 3일 이내 첫 시청 여부, row-level 재계산 fixed 버전), is_cold_start_7d_fixed (구독 후 7일 이내 첫 시청 여부, row-level 재계산 fixed 버전), watch_time_min_w1 (1주차 총 시청 시간, 분 단위), watch_time_min_w2 (2주차 총 시청 시간, 분 단위), watch_time_min_w3 (3주차 총 시청 시간, 분 단위)입니다.",
        "07x Needs_user_review 4개는 age_group, is_female, is_male, is_user_verified입니다.": "07x Needs_user_review 4개는 age_group (나이대 그룹, 인구통계 대리 변수), is_female (여성 여부, 인구통계 대리 변수), is_male (남성 여부, 인구통계 대리 변수), is_user_verified (본인인증 완료 여부, 인증 상태 대리 변수)입니다.",
        "<td>churn_risk</td><td>1 - repurchase_score, 모델 기반 이탈 위험 점수</td>": "<td>churn_risk (1 - repurchase_score, 모델 기반 이탈 위험 점수)</td><td>1 - repurchase_score, 모델 기반 이탈 위험 점수</td>",
        "<td>repurchase_score</td><td>모델 기반 재구매 가능성 점수</td>": "<td>repurchase_score (모델 기반 재구매 가능성 점수)</td><td>모델 기반 재구매 가능성 점수</td>",
        "<td>risk_percentile_desc</td><td>이탈 위험 점수를 높은 순서로 정렬한 백분위</td>": "<td>risk_percentile_desc (이탈 위험 점수를 높은 순서로 정렬한 백분위)</td><td>이탈 위험 점수를 높은 순서로 정렬한 백분위</td>",
        "23,343 rows, 91 cols, 결측치 0, 완전 중복 48행 확인. USER_KEY 중복 143개 발견. is_promotion / is_repurchase 2×2 분포 기록.": "23,343행, 91개 컬럼, 결측치 0, 완전중복 48행 확인. USER_KEY 중복 143개 발견. is_promotion (100원딜 프로모션 유입 여부) / is_repurchase (다음 달 재구매 여부) 2×2 분포 기록.",
        "payment/auth/demographic proxy 없이 순수 주차별 시청 행동 22개 피처 확정. 이후 확장 피처셋의 기준선(baseline) 역할.": "결제, 인증, 인구통계 대리 변수 없이 순수 주차별 시청 행동 22개 피처 확정. 이후 확장 피처셋의 기준선 역할.",
        "회원 맥락(멤버십, 인구통계 proxy), 가입 시점, 결제 방식, 콘텐츠/장르 비율 등 58개 추가. payment_is_* 4개 포함(→ 15x에서 재심의).": "회원 맥락(멤버십, 인구통계 대리 변수), 가입 시점, 결제 방식, 콘텐츠/장르 비율 등 58개 추가. payment_is_* 4개 포함(15x에서 해석 리스크 재심의).",
        "23,343 → 23,079 분석 cohort. conservative(22개) / expanded(80개) 두 데이터셋 병렬 생성. 4개 scope 정의: overall_with/without_promotion, promotion_only, nonpromotion_only.": "23,343행 → 23,079행 분석 cohort. 보수 피처셋 22개 / 확장 피처셋 80개 데이터셋 병렬 생성. 4개 분석 범위 정의: 전체+100원딜 포함, 전체+100원딜 제외, 100원딜 row만, 비프로모션 row만.",
        "baseline vs expanded 모델 비교": "기준선 피처셋 vs 확장 피처셋 모델 비교",
        "conservative(RandomForest) AUC 최고 0.8318(nonpromotion). expanded(HistGBM) 0.8830. 확장 피처가 +0.05 이상 성능 향상 확인.": "보수 피처셋(RandomForest) AUC 최고 0.8318(비프로모션 row). 확장 피처셋(HistGBM) 0.8830. 확장 피처가 +0.05 이상 성능 향상 확인.",
        "LightGBM expanded가 12x 모델 패밀리 비교에서 후보 기준으로 강세. nonpromotion 0.8838, overall_with 0.8773. 이후 14x Optuna 후보와 15x payment 제거 민감도 분석으로 이어짐.": "LightGBM 확장 피처셋이 12x 모델 패밀리 비교에서 후보 기준으로 강세. 비프로모션 row 0.8838, 전체+100원딜 포함 0.8773. 이후 14x Optuna 후보와 15x 결제기기 제거 민감도 분석으로 이어짐.",
        "LightGBM Optuna 튜닝 후: overall_with 0.8797(+0.0024), nonpromotion 0.8871(+0.0033). 후보 기준 AUC.": "LightGBM Optuna 튜닝 후: 전체+100원딜 포함 0.8797(+0.0024), 비프로모션 row 0.8871(+0.0033). 후보 기준 AUC.",
        "4개 결제 방식 피처 제거 실험. mean AUC delta +0.0036(중립~소폭 개선). 시청 기기가 아닌 과금 환경 proxy임을 이유로 제거 결정. → expanded_no_payment_device(76/75개) 피처셋 확정.": "4개 결제 방식 피처 제거 실험. 평균 AUC 변화량 +0.0036으로 중립~소폭 개선. 시청 기기가 아닌 과금 환경 대리 변수라는 해석 리스크 때문에 제거 기준으로 검토. 결제기기 제거 피처셋(expanded_no_payment_device, 76/75개)을 해석·세그먼트 설계 입력으로 사용.",
        "overall_with_promotion LightGBM 기준: usage_retention_behavior 패밀리가 SHAP 합계 2.877로 1위. 개별 피처 1위는 watch_time_min_w3이고, is_promotion은 개별 feature 기준 2위(0.376)이며 acquisition_split_key family 기준 3위. 인과 해석 금지.": "전체+100원딜 포함 LightGBM 기준: usage_retention_behavior (시청·유지 행동 묶음) 패밀리가 SHAP 합계 2.877로 1위. 개별 피처 1위는 watch_time_min_w3 (3주차 총 시청 시간, 분 단위)이고, is_promotion (100원딜 프로모션 유입 여부)은 개별 피처 기준 2위(0.376)이며 acquisition_split_key (유입 구분 변수 묶음)는 family 기준 3위. 인과 해석 금지.",
        "행동 신호 기반 flag → 7개 provisional 세그먼트. payment/auth/demographic proxy 불사용. flag_age40_unverified_ios는 audit 전용 플래그로만 존재.": "행동 신호 기반 플래그와 모델 기반 이탈 위험 백분위를 결합해 7개 임시 대표 세그먼트 설계. 결제, 인증, 인구통계 대리 변수는 세그먼트 규칙에 직접 사용하지 않음. flag_age40_unverified_ios는 감사 전용 플래그로만 존재.",
        "콘텐츠 장르는 Movie_Master mapping proxy — 정확한 카테고리 아님": "콘텐츠 장르는 Movie_Master 매핑 기반 대리 신호이며, 정확한 카테고리라고 단정하면 안 됨",
        "콘텐츠 매핑 개선: Movie_Master proxy → 실제 장르 태그": "콘텐츠 매핑 개선: Movie_Master 대리 신호 → 실제 장르 태그",
        "content proxy flag == 1": "콘텐츠 취향 대리 신호 플래그 == 1",
    }
    for old, new in ui_replacements.items():
        html_text = html_text.replace(old, new)

    html_text = replace_chart_script(html_text)
    write_text(DST, html_text)
    write_checklist()
    write_fingerprint()
    update_note()
    zip_path = "(이번 소규모 UX 수정에서는 zip 생성을 건너뜀)" if os.environ.get("PROJECT_GUIDE_SKIP_ZIP") == "1" else write_review_zip()
    print(f"created={DST}")
    print(f"checklist={AUDIT / 'project_guide_v2_revision_checklist.csv'}")
    print(f"fingerprint={AUDIT / 'project_guide_v2_source_fingerprint.csv'}")
    print(f"zip={zip_path}")


def feature_label(name: str) -> str:
    return f"{name} ({VAR_KO.get(name, '정의 파일 기준 확인 필요')})"


def translate_flag_basis(definition: str, columns: str, threshold: str) -> str:
    definition_map = {
        "churn_risk descending top 20 percent": "이탈 위험 점수가 높은 순서 기준 상위 20%",
        "week3 watch time or sessions equal zero": "3주차 시청 시간 또는 시청 세션이 0",
        "week3 usage below week2 and diff negative": "3주차 사용량이 2주차보다 낮고 증감값이 음수",
        "week3 retention below week2 or below 0.5": "3주차 유지 비율이 2주차보다 낮거나 0.5 미만",
        "only week1 watched": "1주차에만 시청하고 2~3주차에는 시청하지 않음",
        "fixed cold start 3d or 7d flag": "fixed cold_start 3일/7일 조건 중 하나를 만족",
        "low total watch time or low watch sessions": "전체 시청 시간 또는 전체 시청 세션이 하위권",
        "max genre ratio above q75": "가장 높은 장르 비율이 상위 25% 구간",
        "new movie in 365d ratio above q75": "최근 365일 이내 신작 비율이 상위 25% 구간",
        "old movie ratio 5y above q75": "5년 초과 구작 비율이 상위 25% 구간",
        "low churn_risk and stable week3 retention": "이탈 위험이 낮고 3주차 유지 패턴이 안정적",
        "cold start fixed flags indicate weak activation": "fixed cold_start 조건상 초기 활성화가 약한 것으로 표시",
        "bottom 20 percent risk and stable week3 retention": "이탈 위험 하위 20%이면서 3주차 유지 패턴이 안정적",
    }
    threshold_map = {
        "top20 fixed percentile": "고정 상위 20% 백분위",
        "zero": "0 기준",
        "fixed zero": "0 기준",
        "w3 < w2 and diff < 0": "3주차 < 2주차, 증감값 < 0",
        "observed decrease": "관측된 감소 조건",
        "w3 ratio < w2 ratio or w3 ratio < 0.5": "3주차 유지 비율 < 2주차 유지 비율 또는 3주차 유지 비율 < 0.5",
        "fixed 0.5 plus relative drop": "0.5 고정 기준 또는 전주 대비 하락",
        "logical week-only pattern": "주차별 시청 여부 논리 조건",
        "fixed cold start columns": "fixed cold_start 컬럼 기준",
        "06x fixed flags": "06x fixed cold_start 플래그 기준",
        "q25": "하위 25% 기준",
        "q75": "상위 25% 기준",
        "bottom20 risk and stable retention": "위험도 하위 20%와 안정적 유지 조건",
        "bottom20 fixed percentile plus behavior": "고정 하위 20% 백분위와 행동 조건 결합",
    }
    ko_definition = definition_map.get(definition, definition or "정의 파일 기준 확인 필요")
    ko_threshold = threshold_map.get(threshold, threshold or "기준 확인 필요")
    return f"{ko_definition} / 사용 컬럼: {describe_columns(columns)} / 기준: {ko_threshold}"


def describe_columns(columns: str) -> str:
    if not columns:
        return "정의 파일 기준 확인 필요"
    parts = [c.strip() for c in columns.split(",") if c.strip()]
    return ", ".join(feature_label(p) for p in parts)


def rule_with_descriptions(rule: str) -> str:
    replacements = {
        "flag_high_risk_top20": feature_label("flag_high_risk_top20"),
        "flag_week3_inactive": feature_label("flag_week3_inactive"),
        "flag_week3_drop": feature_label("flag_week3_drop"),
        "flag_retention_decay": feature_label("flag_retention_decay"),
        "flag_only_w1": feature_label("flag_only_w1"),
        "flag_cold_start_weak": feature_label("flag_cold_start_weak"),
        "flag_low_activity": feature_label("flag_low_activity"),
        "flag_low_risk_stable": feature_label("flag_low_risk_stable"),
    }
    out = rule.replace("churn_risk top 20-50 percent", f"{feature_label('churn_risk')} 상위 20~50% 구간")
    out = out.replace("content proxy flag", "콘텐츠 취향 대리 신호 플래그")
    for old, new in replacements.items():
        out = re.sub(rf"\b{re.escape(old)}\b", new, out)
    return out


def build_feature_section() -> str:
    return f"""<!-- ===== 5. FEATURES ===== -->
<section id="features">
  <div class="section-header"><h2>피처 세트 계보와 변수명 기준</h2></div>
  <div class="meta-block">
    <div class="meta-title">섹션 메타</div>
    <div class="meta-row"><span class="meta-label">이 섹션이 말하는 것</span><span class="meta-value">22개 → 80개 → 76/75개로 피처가 어떻게 진화했는지</span></div>
    <div class="meta-row"><span class="meta-label">오해 금지</span><span class="meta-value">14x는 expanded_feature_set 기준 Optuna 후보이고, 15x는 expanded_no_payment_device 기준 민감도 분석입니다.</span></div>
  </div>
  <div class="chart-grid">
    <div class="chart-card"><h4>피처 개수 변화</h4><canvas id="feature_count_flow" height="220"></canvas>{source_block("reports/audits/06x_dataset_generation_260515/06x_dataset_comparison_summary.csv", "reports/audits/15x_payment_device_sensitivity_260516/15x_model_summary_by_scope.csv")}</div>
    <div class="chart-card"><h4>cold_start fixed hotfix 영향</h4><canvas id="cold_start_fix" height="220"></canvas>{source_block("reports/audits/06x_dataset_generation_260515/06x_fixed_feature_validation.csv")}</div>
  </div>
  <div class="card-grid col3">
    <div class="card callout-safe"><h4>보수 피처셋 <span class="muted">(conservative_safe_22)</span></h4><div class="stat-number">22</div><div class="stat-label">day0~20 행동 중심 피처</div><p class="muted">결제, 인증, 인구통계 대리 변수를 빼고 주차별 시청 행동만 사용합니다.</p></div>
    <div class="card callout-warn"><h4>확장 피처셋 <span class="muted">(expanded_feature_set)</span></h4><div class="stat-number">80</div><div class="stat-label">14x Optuna 후보 기준</div><p class="muted">회원 맥락, 콘텐츠 취향 대리 신호, 100원딜 구분 변수를 포함합니다. 14x AUC는 이 피처셋 기준입니다.</p></div>
    <div class="card callout-danger"><h4>결제기기 제거 피처셋 <span class="muted">(expanded_no_payment_device)</span></h4><div class="stat-number">76/75</div><div class="stat-label">15x 민감도 분석 기준</div><p class="muted">payment_is_* 4개를 제거한 해석·세그먼트 설계 입력 피처셋입니다. 최종 모델 확정은 아닙니다.</p></div>
  </div>
  <div class="card">
    <h4>실제 컬럼명 기준 예시</h4>
    <div class="pill-row">
      <span class="var-pill">{feature_label('watch_time_min_w1')}</span>
      <span class="var-pill">{feature_label('watch_time_min_w2')}</span>
      <span class="var-pill">{feature_label('watch_time_min_w3')}</span>
      <span class="var-pill">{feature_label('is_cold_start_3d_fixed')}</span>
      <span class="var-pill">{feature_label('is_cold_start_7d_fixed')}</span>
      <span class="var-pill">{feature_label('is_promotion')}</span>
      <span class="var-pill">{feature_label('age_group')}</span>
      <span class="var-pill">{feature_label('is_user_verified')}</span>
    </div>
    <div class="warn-bar" style="margin-top:14px;">is_cold_start_3d / is_cold_start_7d처럼 _fixed가 빠진 이름은 실제 모델 피처명처럼 쓰지 않습니다. watch_time_w1/w2/w3도 표시 축약이 아니라 실제 컬럼명은 watch_time_min_w1/2/3입니다.</div>
  </div>
</section>"""


def build_aarrr_section() -> str:
    return f"""<!-- ===== 6. AARRR ===== -->
<section id="aarrr">
  <div class="section-header"><h2>AARRR 프레임워크와 해석 경계</h2></div>
  <div class="meta-block">
    <div class="meta-title">섹션 메타</div>
    <div class="meta-row"><span class="meta-label">정정 사항</span><span class="meta-value">07x Needs_user_review 4개는 age_group, is_female, is_male, is_user_verified입니다. payment_is_* 4개는 07x에서 Acquisition_context였고, 15x에서 해석 리스크 때문에 제거 기준으로 이동했습니다.</span></div>
    <div class="meta-row"><span class="meta-label">source</span><span class="meta-value">07x_feature_mapping_master.csv, 07x_AARRR_summary_by_feature_set.csv</span></div>
  </div>
  <div class="chart-grid">
    <div class="chart-card"><h4>conservative_safe_22 AARRR 분포</h4><canvas id="aarrr_conservative" height="220"></canvas></div>
    <div class="chart-card"><h4>expanded_feature_set AARRR 분포</h4><canvas id="aarrr_expanded" height="220"></canvas></div>
  </div>
  <table>
    <tr><th>AARRR 단계</th><th>conservative(22)</th><th>expanded(80)</th><th>대표 피처 예시</th></tr>
    <tr><td>Acquisition</td><td>0</td><td>1</td><td>{feature_label('is_promotion')}</td></tr>
    <tr><td>Acquisition_context</td><td>0</td><td>12</td><td>payment_is_mobile / payment_is_pc / payment_is_android / payment_is_ios (결제 환경 대리 변수, 15x에서 제거 검토), 요금제/가입 맥락</td></tr>
    <tr><td>Activation</td><td>6</td><td>6</td><td>{feature_label('is_cold_start_3d_fixed')}, {feature_label('is_only_w1')}</td></tr>
    <tr><td>Retention</td><td>16</td><td>39</td><td>{feature_label('watch_time_min_w3')}, {feature_label('retention_w3_ratio')}</td></tr>
    <tr><td>Retention_context</td><td>0</td><td>18</td><td>{feature_label('drama_ratio')}, {feature_label('romance_ratio')}</td></tr>
    <tr><td>Needs_user_review</td><td>0</td><td>4</td><td>{feature_label('age_group')}, {feature_label('is_female')}, {feature_label('is_male')}, {feature_label('is_user_verified')}</td></tr>
    <tr><td>Revenue</td><td>타겟</td><td>타겟</td><td>is_repurchase (다음 달 재구매 여부, 매출 대리 타겟, 모델 피처로 사용하지 않음)</td></tr>
    <tr><td>Referral</td><td>없음</td><td>없음</td><td>추천인 코드, 공유 활동, 바이럴 지표는 현재 데이터에 없음. 추후 instrumentation 후보입니다.</td></tr>
  </table>
  {source_block("reports/audits/07x_feature_mapping_AARRR_260515/07x_feature_mapping_master.csv", "reports/audits/07x_feature_mapping_AARRR_260515/07x_AARRR_summary_by_feature_set.csv")}
</section>"""


def build_cohort_section() -> str:
    return f"""<!-- ===== 7. COHORT ===== -->
<section id="cohort">
  <div class="section-header"><h2>코호트 분포와 관찰 차이</h2></div>
  <div class="meta-block">
    <div class="meta-title">섹션 메타</div>
    <div class="meta-row"><span class="meta-label">오해 금지</span><span class="meta-value">67.52%와 76.24%의 차이는 관찰 차이이며, 100원딜의 인과효과가 아닙니다.</span></div>
  </div>
  <div class="chart-grid">
    <div class="chart-card"><h4>프로모션 vs 비프로모션 재구매율</h4><canvas id="cohort_bar" height="220"></canvas>{source_block("reports/audits/08x_promotion_nonpromotion_EDA_260516/08x_promotion_target_summary.csv")}</div>
    <div class="chart-card"><h4>2x2 분포</h4><canvas id="twobytwo" height="220"></canvas>{source_block("reports/audits/09x_promotion_repurchase_2x2_EDA_260516/09x_2x2_cohort_summary.csv")}</div>
    <div class="chart-card wide"><h4>08x 상위 관찰 차이 feature</h4><canvas id="observed_diff_chart" height="120"></canvas>{source_block("reports/audits/08x_promotion_nonpromotion_EDA_260516/08x_top_observed_differences_for_review.csv")}</div>
  </div>
</section>"""


def best_auc(stage: str, rel: str, model: str | None = None, feature_set: str | None = None):
    out = {}
    for r in rows(rel):
        if model and r.get("model_name") != model:
            continue
        fs = r.get("feature_set_name") or r.get("feature_set_variant")
        if feature_set and fs != feature_set:
            continue
        scope = r.get("dataset_scope")
        auc = fnum(r.get("oof_auc", "0"))
        if scope and (scope not in out or auc > out[scope]):
            out[scope] = auc
    return out


def build_modeling_section() -> str:
    return f"""<!-- ===== 8. MODELING ===== -->
<section id="modeling">
  <div class="section-header"><h2>모델링 결과: 11x → 12x → 14x → 15x</h2></div>
  <div class="meta-block">
    <div class="meta-title">섹션 메타</div>
    <div class="meta-row"><span class="meta-label">정정 사항</span><span class="meta-value">14x는 expanded_feature_set 기준 Optuna 후보 AUC입니다. 15x는 expanded_no_payment_device 기준 payment 제거 민감도 결과입니다.</span></div>
    <div class="meta-row"><span class="meta-label">오해 금지</span><span class="meta-value">14x/15x/16x/17x 모두 최종 모델 선택 또는 최종 캠페인 기준값이 아닙니다. 운영 전 진단용 점수입니다.</span></div>
  </div>
  <div class="chart-grid">
    <div class="chart-card wide"><h4>AUC 흐름: 11x 기준선 → 12x 모델 비교 → 14x Optuna 후보 → 15x 결제기기 제거</h4><canvas id="auc_chart" height="130"></canvas></div>
    <div class="chart-card"><h4>15x 결제기기 제거 전후 AUC 변화</h4><canvas id="payment_delta_chart" height="220"></canvas></div>
    <div class="chart-card"><h4>15x 결제기기 제거 후 모델별 AUC</h4><canvas id="nopay_auc_chart" height="220"></canvas></div>
  </div>
  <table>
    <tr><th>단계</th><th>기준</th><th>overall_with</th><th>overall_without</th><th>promotion_only</th><th>nonpromotion_only</th><th>해석</th></tr>
    <tr><td>11x</td><td>기준선/확장 피처 비교</td><td>0.8770</td><td>0.8725</td><td>0.8606</td><td>0.8830</td><td>확장 피처의 후보 성능 확인</td></tr>
    <tr><td>12x</td><td>expanded_feature_set LightGBM</td><td>0.8773</td><td>0.8733</td><td>0.8616</td><td>0.8838</td><td>모델 패밀리 비교 기준</td></tr>
    <tr><td>14x</td><td>expanded_feature_set 기준 LightGBM Optuna 후보</td><td>0.8797 (80)</td><td>0.8756 (79)</td><td>0.8634 (79)</td><td>0.8871 (79)</td><td>Optuna 후보 기준 AUC, 최종 선택 아님</td></tr>
    <tr><td>15x</td><td>expanded_no_payment_device 기준 민감도 분석</td><td>0.8787 (76, LightGBM)</td><td>0.8738 (75, LightGBM)</td><td>0.8620 (75, LightGBM)</td><td>0.8847 (75, LightGBM) / 0.8865 (CatBoost)</td><td>결제기기 제거 후 해석·세그먼트 입력 검토</td></tr>
  </table>
  <div class="explain-block callout-danger">
    <h3>왜 payment_is_* 4개를 제거 기준으로 봤는가?</h3>
    <p style="font-size:13px;color:var(--text2);line-height:1.8;">payment_is_mobile / payment_is_pc / payment_is_android / payment_is_ios는 시청기기가 아니라 결제기기 또는 결제환경의 흔적에 가깝습니다. 결제자와 실제 시청자가 다를 수 있고, iOS 또는 Android 결제 여부가 콘텐츠 선호, 시청 만족도, 재구매를 직접 만든다고 볼 수도 없습니다. 따라서 이 변수가 SHAP이나 세그먼트에서 크게 보이면 성능상 이득보다 해석 리스크가 커질 수 있습니다.</p>
    <div class="card-grid col3" style="margin-top:12px;">
      <div class="card"><div class="stat-number">+0.003590</div><div class="stat-label">평균 AUC 변화량</div><div class="stat-explain">15x 결제기기 제거 민감도 분석의 평균 변화입니다.</div></div>
      <div class="card"><div class="stat-number">-0.000150</div><div class="stat-label">가장 나쁜 AUC 변화</div><div class="stat-explain">성능 손실은 near-neutral 수준으로 기록됐습니다.</div></div>
      <div class="card"><div class="stat-number">high</div><div class="stat-label">해석 리스크</div><div class="stat-explain">15x recommendation 파일에서 interpretation risk가 high로 관리됐습니다.</div></div>
    </div>
    <p style="font-size:13px;color:var(--text2);line-height:1.8;margin-top:12px;">이 결정은 “결제기기가 나쁘다”는 뜻이 아닙니다. 현재 프로젝트 목적이 팀원이 이해 가능한 행동 기반 이탈 방어 설명을 만드는 것이므로, 결제환경 대리 변수를 고객 특성이나 시청 경험처럼 읽을 위험을 줄이기 위한 해석 안전장치입니다.</p>
    {source_block("reports/audits/15x_payment_device_sensitivity_260516/15x_payment_removed_vs_original_comparison.csv", "reports/audits/15x_payment_device_sensitivity_260516/15x_recommendation_for_canonical_feature_contract.csv", "reports/audits/15x_payment_device_sensitivity_260516/15x_safe_unsafe_wording.csv")}
  </div>
  {source_block("reports/models/14x_lightweight_candidate_tuning_260516/14x_model_summary_by_scope.csv", "reports/models/14x_lightweight_candidate_tuning_260516/14x_vs_12x_comparison.csv", "reports/audits/15x_payment_device_sensitivity_260516/15x_payment_removed_vs_original_comparison.csv", "reports/audits/15x_payment_device_sensitivity_260516/15x_model_summary_by_scope.csv")}
</section>"""


def build_shap_section() -> str:
    return f"""<!-- ===== 9. SHAP ===== -->
<section id="shap">
  <div class="section-header"><h2>SHAP 해석: 모델 설명, 인과 아님</h2></div>
  <div class="meta-block">
    <div class="meta-title">섹션 메타</div>
    <div class="meta-row"><span class="meta-label">정정 사항</span><span class="meta-value">개별 피처 기준 is_promotion (100원딜 프로모션 유입 여부)은 2위이며, family 기준 acquisition_split_key는 3위입니다.</span></div>
    <div class="meta-row"><span class="meta-label">오해 금지</span><span class="meta-value">SHAP은 fitted model explanation입니다. 시청 시간이 재구매를 일으킨다는 뜻이 아닙니다.</span></div>
  </div>
  <div class="chart-grid">
    <div class="chart-card wide"><h4>16x SHAP 개별 피처 Top 10</h4><canvas id="shap_top_chart" height="150"></canvas>{source_block("reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_global_importance.csv")}</div>
    <div class="chart-card"><h4>SHAP family 중요도</h4><canvas id="shap_family_chart" height="220"></canvas>{source_block("reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_family_importance.csv")}</div>
    <div class="chart-card"><h4>주요 feature 방향성 caveat</h4><canvas id="shap_direction_chart" height="220"></canvas>{source_block("reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_direction_summary.csv")}</div>
  </div>
  <div class="card"><h4>Top feature 한국어 설명</h4><div class="pill-row">
    <span class="var-pill">{feature_label('watch_time_min_w3')}</span>
    <span class="var-pill">{feature_label('is_promotion')}</span>
    <span class="var-pill">{feature_label('retention_w2_ratio')}</span>
    <span class="var-pill">{feature_label('retention_w3_ratio')}</span>
    <span class="var-pill">{feature_label('drama_ratio')}</span>
    <span class="var-pill">{feature_label('family_animation_ratio')}</span>
    <span class="var-pill">{feature_label('romance_ratio')}</span>
    <span class="var-pill">{feature_label('thriller_crime_ratio')}</span>
    <span class="var-pill">{feature_label('action_adventure_ratio')}</span>
    <span class="var-pill">{feature_label('diff_between_w2_w1')}</span>
  </div></div>
</section>"""


def build_segments_section() -> str:
    seg_rows = rows("reports/segments/17x_segmentation_design_260516/17x_segment_summary.csv")
    rule_rows = {r["representative_segment"]: r for r in rows("reports/segments/17x_segmentation_design_260516/17x_representative_segment_rules.csv")}
    cards = []
    for r in seg_rows:
        name = r["representative_segment"]
        klass = "high-risk" if name.startswith("high_risk") else "medium-risk" if name.startswith("medium") else "low-risk" if name in ("content_preference_target_candidate", "stable_retained_user") else "general"
        simple, feature, response = SEG_EXPLAIN[name]
        rule = rule_rows[name]["matched_rule_text"]
        cards.append(f"""<div class="segment-card {klass}">
  <div class="segment-name-ko">{SEG_KO[name]}</div>
  <div class="segment-name-en">대표 라벨 ID: {esc(name)} <span class="src">[17x] 우선순위 {esc(r['segment_priority'])}</span></div>
  <div class="segment-stats">
    <div class="segment-stat"><div class="n">{int(float(r['row_count'])):,}</div><div class="lbl">행 ({pct(fnum(r['row_share']))})</div></div>
    <div class="segment-stat"><div class="n">{pct(fnum(r['repurchase_rate']))}</div><div class="lbl">재구매율</div></div>
    <div class="segment-stat"><div class="n">{pct(fnum(r['mean_churn_risk']))}</div><div class="lbl">평균 이탈위험</div></div>
  </div>
  <p style="font-size:13px;color:var(--text2);"><strong>쉬운 설명:</strong> {esc(simple)}</p>
  <p style="font-size:13px;color:var(--text2);"><strong>특징:</strong> {esc(feature)}</p>
  <p style="font-size:13px;color:var(--text2);"><strong>대응:</strong> {esc(response)}</p>
  <details><summary>변수 설명이 붙은 원본 규칙 보기</summary><div class="detail-body"><code>{esc(rule_with_descriptions(rule))}</code></div></details>
</div>""")

    flags = ["churn_risk", "repurchase_score", "risk_percentile_desc", "flag_high_risk_top20", "flag_week3_inactive", "flag_week3_drop", "flag_retention_decay", "flag_only_w1", "flag_cold_start_weak", "flag_low_activity", "flag_genre_focused", "flag_new_movie_oriented", "flag_old_movie_oriented", "flag_low_risk_stable"]
    def_rows = {r["flag_name"]: r for r in rows("reports/segments/17x_segmentation_design_260516/17x_internal_multiflag_definitions.csv")}
    flag_table = ""
    for fl in flags:
        d = def_rows.get(fl)
        if d:
            basis = translate_flag_basis(d["definition_text"], d["columns_used"], d["threshold_source"])
        else:
            basis = "17x_internal_multiflag_definitions.csv에 직접 행은 없지만 score source와 규칙에서 파생됨"
        flag_table += f"<tr><td>{esc(feature_label(fl))}</td><td>{esc(VAR_KO.get(fl, '정의 파일 기준 확인 필요'))}</td><td>{esc(basis)}</td></tr>\n"

    return f"""<!-- ===== 10. SEGMENTS ===== -->
<section id="segments">
  <div class="section-header"><h2>7개 대표 세그먼트: 어떻게 나눴는가?</h2></div>
  <div class="explain-block callout-warn">
    <h3>세그먼트는 고객 유형이 아니라 provisional representative label입니다</h3>
    <ul class="plain-list">
      <li>단위는 고객 1명이 아니라 구독 이벤트 row 1개입니다.</li>
      <li>한 row는 여러 플래그를 동시에 가질 수 있지만, 발표와 대응 설계를 위해 우선순위 1~7에 따라 대표 세그먼트 하나만 부여했습니다.</li>
      <li>순수 행동 규칙만 사용한 것이 아닙니다. 일부 규칙은 모델 기반 이탈 위험 백분위와 day0~20 행동 플래그를 결합합니다.</li>
      <li>churn_risk (1 - repurchase_score, 모델 기반 이탈 위험 점수)는 15x expanded_no_payment_device, overall_with_promotion, LightGBM OOF 진단 점수에서 왔습니다.</li>
      <li>이 점수는 최종 캠페인 기준값이 아니라 세그먼트 설계용 진단 점수입니다.</li>
      <li>대표 세그먼트 규칙에는 결제, 인증, 인구통계 대리 변수를 직접 쓰지 않았지만, 점수 모델에는 결제기기 외의 대리 변수 caveat가 남아 있을 수 있습니다.</li>
    </ul>
  </div>
  <div class="explain-block callout-safe">
    <h3>왜 이 score source를 썼는가?</h3>
    <p style="font-size:13px;color:var(--text2);line-height:1.8;">17x 세그먼트의 이탈위험 점수는 15x OOF prediction 중 expanded_no_payment_device, overall_with_promotion, LightGBM 조건을 primary score source로 사용했습니다. 이유는 16x payment-removed SHAP 해석도 LightGBM 기준으로 수행됐기 때문입니다. 즉 세그먼트의 위험 점수와 SHAP 근거가 서로 다른 모델을 바라보지 않도록 모델 기준을 맞춘 것입니다.</p>
    <p style="font-size:13px;color:var(--text2);line-height:1.8;">이 선택은 최종 운영 모델 확정이 아닙니다. 발표에서는 “해석과 세그먼트 설계의 기준을 맞추기 위해 선택한 OOF 진단 점수”라고 말해야 안전합니다. 이 점수로 최종 캠페인 컷오프나 자동 타깃팅 정책을 확정했다고 말하면 안 됩니다.</p>
    {source_block("reports/segments/17x_segmentation_design_260516/17x_score_source_selection.csv", "reports/segments/17x_segmentation_design_260516/17x_segment_SHAP_evidence_link.csv", "reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_global_importance.csv")}
  </div>
  <div class="chart-grid">
    <div class="chart-card"><h4>세그먼트 row 비중 파이차트</h4><canvas id="segment_pie" height="240"></canvas></div>
    <div class="chart-card"><h4>세그먼트별 행 수</h4><canvas id="segment_dist" height="240"></canvas></div>
    <div class="chart-card"><h4>재구매율 vs 이탈위험(churn_risk)</h4><canvas id="segment_risk" height="240"></canvas></div>
    <div class="chart-card"><h4>세그먼트별 주차 시청시간 패턴</h4><canvas id="segment_weekly_watch" height="240"></canvas></div>
  </div>
  <div class="card"><h4>세그먼트에서 쓰인 주요 플래그 사전</h4><table><tr><th>변수명</th><th>한국어 설명</th><th>계산 기준</th></tr>{flag_table}</table>{source_block("reports/segments/17x_segmentation_design_260516/17x_internal_multiflag_definitions.csv", "reports/segments/17x_segmentation_design_260516/17x_representative_segment_rules.csv", "reports/segments/17x_segmentation_design_260516/17x_score_source_selection.csv")}</div>
  {''.join(cards)}
  {source_block("reports/segments/17x_segmentation_design_260516/17x_segment_summary.csv", "reports/segments/17x_segmentation_design_260516/17x_segment_feature_profile.csv", "reports/segments/17x_segmentation_design_260516/17x_representative_segment_rules.csv")}
</section>"""


def build_recommendation_section() -> str:
    recs = rows("reports/storyline/18x_business_recommendation_storyline_260518/18x_business_recommendation_matrix.csv")
    business_problem_ko = {
        "late observation-window cooling signal may need quick re-entry support": "관측창 후반부 시청 감소 신호가 있어 빠른 재진입 유도가 필요한 후보입니다.",
        "initial viewing habit may not have formed": "초기 시청 습관이 안정적으로 형성되지 않았을 가능성이 있는 후보입니다.",
        "low engagement makes high-intensity personalization risky": "활동량이 낮아 강한 개인화보다 낮은 마찰 메시지가 더 안전한 후보입니다.",
        "risk is moderate, but decay can be detected before it becomes severe": "고위험은 아니지만 시청 감소가 감지되는 중위험 후보입니다.",
        "recommendation can use content proxy, with mapping caveat": "콘텐츠 취향 대리 신호를 추천에 활용할 수 있지만 장르 매핑 한계가 있는 후보입니다.",
        "defensive discount may be inefficient for already stable rows": "이미 안정적인 row라 방어성 할인 효율이 낮을 수 있는 후보입니다.",
        "needs monitoring or additional information rather than a sharp claim": "강한 규칙으로 단정하기보다 추가 관찰과 정보 수집이 필요한 후보입니다.",
    }
    success_metric_ko = {
        "next-cycle repurchase, day21+ re-entry, watch activity recovery, message engagement": "다음 주기 재구매, day21 이후 재진입, 시청 회복, 메시지 반응률",
    }
    trs = []
    for r in recs:
        trs.append(f"<tr><td>{esc(SEG_KO.get(r['representative_segment'], r['representative_segment']))}<br><span class=\"muted\">대표 라벨 ID: {esc(r['representative_segment'])}</span></td><td>{esc(business_problem_ko.get(r['business_problem'], r['business_problem']))}</td><td>{esc(r['recommended_action_candidate'])}</td><td>{esc(r['message_timing'])}</td><td>{esc(success_metric_ko.get(r['success_metric_candidate'], r['success_metric_candidate']))}</td></tr>")
    return f"""<!-- ===== 11. RECOMMENDATIONS ===== -->
<section id="recommendations">
  <div class="section-header"><h2>비즈니스 제언: 세그먼트별 대응 후보</h2></div>
  <div class="meta-block">
    <div class="meta-title">섹션 메타</div>
    <div class="meta-row"><span class="meta-label">오해 금지</span><span class="meta-value">제언은 캠페인 후보이며, A/B 테스트 전 최종 운영 정책이 아닙니다.</span></div>
  </div>
  <div class="chart-grid">
    <div class="chart-card wide"><h4>세그먼트별 대응 우선순위와 비율 지표</h4><canvas id="recommendation_priority_chart" height="130"></canvas>{source_block("reports/storyline/18x_business_recommendation_storyline_260518/18x_business_recommendation_matrix.csv")}</div>
  </div>
  <table><tr><th>세그먼트</th><th>비즈니스 문제</th><th>대응 후보</th><th>타이밍</th><th>성공 지표 후보</th></tr>{''.join(trs)}</table>
  <div class="explain-block callout-warn">
    <h3>발표 문장 안전선: 이렇게 말하면 안 됩니다</h3>
    <table>
      <tr><th>위험한 표현</th><th>왜 위험한가</th><th>대신 쓸 표현</th></tr>
      <tr><td>100원딜이 이탈을 유발했다</td><td>관찰 차이를 인과효과처럼 말하는 표현입니다.</td><td>100원딜 여부에 따라 관측된 재구매율과 행동 신호 차이가 있었다.</td></tr>
      <tr><td>SHAP이 원인을 밝혔다</td><td>SHAP은 모델 설명이지 원인 증명이 아닙니다.</td><td>SHAP은 모델이 재구매 여부를 구분할 때 중요하게 사용한 신호를 보여준다.</td></tr>
      <tr><td>payment_device는 시청기기다</td><td>payment_device는 결제기기 또는 결제환경에 가깝습니다.</td><td>payment_is_*는 결제환경·계정 생성·인증 구조의 대리 신호일 수 있다.</td></tr>
      <tr><td>40대 미인증 iOS 고객군</td><td>인구통계·인증·결제환경 artifact를 고객 유형처럼 이름 붙이는 표현입니다.</td><td>해당 조합은 audit flag로만 관리하며 대표 세그먼트명이나 제언 근거로 쓰지 않는다.</td></tr>
      <tr><td>이 세그먼트가 최종 고객 유형이다</td><td>17x 세그먼트는 임시 대표 라벨입니다.</td><td>세그먼트는 대응 설계를 위한 provisional representative label이다.</td></tr>
      <tr><td>이 결과로 바로 캠페인을 집행하면 된다</td><td>18x는 운영 정책 확정 단계가 아닙니다.</td><td>제언은 캠페인 후보이며 A/B 테스트와 운영 검증이 필요하다.</td></tr>
    </table>
    {source_block("reports/storyline/18x_business_recommendation_storyline_260518/18x_safe_unsafe_wording.csv", "reports/storyline/18x_business_recommendation_storyline_260518/18x_open_risks.csv")}
  </div>
  <div class="explain-block callout-safe">
    <h3>멘토가 깊게 물을 때의 방어 답변</h3>
    <details open><summary>왜 15x LightGBM 점수를 세그먼트 기준으로 썼나요?</summary><div class="detail-body">16x payment-removed SHAP 해석이 LightGBM 기준이었기 때문에, 세그먼트 위험 점수와 SHAP 근거의 모델 기준을 맞추기 위해서입니다. 서로 다른 모델의 점수와 설명을 섞으면 “이 세그먼트를 왜 이렇게 해석했는가”에 대한 근거가 흐려집니다. 단, 이것은 최종 운영 모델 확정이 아니라 세그먼트 설계용 OOF 진단 점수입니다.</div></details>
    <details><summary>payment_is_*를 빼면 중요한 정보를 버린 것 아닌가요?</summary><div class="detail-body">버린 것이 아니라 해석 리스크를 낮춘 것입니다. payment_is_*는 시청기기가 아니라 결제환경에 가깝고, 결제자와 실제 시청자가 다를 수 있습니다. 15x에서 제거 후 평균 AUC 변화는 +0.003590, worst delta는 -0.000150으로 near-neutral이었습니다. 따라서 성능 이득보다 잘못된 고객 해석을 막는 가치가 더 크다고 보는 것이 안전합니다.</div></details>
    <details><summary>SHAP 상위 피처를 그대로 캠페인 메시지 근거로 써도 되나요?</summary><div class="detail-body">그대로 쓰면 안 됩니다. SHAP은 모델이 어떤 피처를 사용했는지 설명하는 도구이지, 고객에게 보낼 메시지의 원인을 증명하는 도구가 아닙니다. 메시지 설계에는 day0~20 행동 신호와 콘텐츠 대리 신호를 후보 근거로만 사용하고, 실제 효과는 A/B 테스트로 확인해야 합니다.</div></details>
    <details><summary>고위험 top20은 바로 캠페인 타깃인가요?</summary><div class="detail-body">아닙니다. flag_high_risk_top20은 세그먼트 설계에서 위험군을 나누기 위한 진단용 백분위입니다. 최종 캠페인 threshold, 예산 배분 기준, 자동 발송 기준은 별도의 운영 실험과 비용·피로도 검토가 있어야 정할 수 있습니다.</div></details>
    <details><summary>결제·인증·인구통계 변수를 세그먼트 rule에 직접 쓰지 않은 이유는 뭔가요?</summary><div class="detail-body">이 변수들은 고객 성향이라기보다 결제 경로, 본인인증 정책, 계정 생성 구조의 artifact일 수 있습니다. 그래서 대표 세그먼트명이나 비즈니스 제언의 직접 근거로 쓰면 “iOS 고객”, “40대 미인증 고객” 같은 위험한 결론으로 미끄러질 수 있습니다. 17x에서는 이들을 audit/caveat로 관리하고, 대표 rule은 행동 신호 중심으로 설계했습니다.</div></details>
    <details><summary>콘텐츠 취향 세그먼트는 진짜 취향을 의미하나요?</summary><div class="detail-body">아닙니다. Movie_Master category mapping 기반 콘텐츠 대리 신호입니다. “이 사람은 이 장르를 좋아한다”가 아니라 “관측창 안에서 특정 장르 비율이 높게 나타났다”가 안전한 표현입니다. 따라서 추천도 확정 개인화가 아니라 추천 후보로 말해야 합니다.</div></details>
    <details><summary>stable_retained_user는 할인하지 않아도 된다는 결론인가요?</summary><div class="detail-body">확정 결론은 아닙니다. 다만 평균 재구매율과 이탈위험 기준으로 보면 방어성 할인보다 만족도 유지, 업셀, 리뷰·추천 유도 후보가 더 자연스럽다는 해석입니다. 실제 할인 제외 정책은 실험으로 검증해야 합니다.</div></details>
    {source_block("reports/storyline/18x_business_recommendation_storyline_260518/18x_mentor_QA_defense.csv", "reports/storyline/18x_business_recommendation_storyline_260518/18x_safe_unsafe_wording.csv", "reports/storyline/18x_business_recommendation_storyline_260518/18x_open_risks.csv", "reports/segments/17x_segmentation_design_260516/17x_score_source_selection.csv")}
  </div>
</section>"""


def replace_chart_script(text: str) -> str:
    script = build_chart_script()
    return re.sub(r"<script>\n// Dark mode.*?</script>", script, text, flags=re.S)


def chart_data():
    aarrr = rows("reports/audits/07x_feature_mapping_AARRR_260515/07x_AARRR_summary_by_feature_set.csv")
    aarrr_cons = {r["AARRR_stage"]: int(r["feature_count"]) for r in aarrr if r["feature_set_name"] == "conservative_safe_22"}
    aarrr_exp = {r["AARRR_stage"]: int(r["feature_count"]) for r in aarrr if r["feature_set_name"] == "expanded_feature_set"}
    coh = rows("reports/audits/08x_promotion_nonpromotion_EDA_260516/08x_promotion_target_summary.csv")
    coh = [r for r in coh if r["feature_set_name"] == "expanded_feature_set"]
    two = rows("reports/audits/09x_promotion_repurchase_2x2_EDA_260516/09x_2x2_cohort_summary.csv")
    two = [r for r in two if r["feature_set_name"] == "expanded_feature_set"]
    obs = rows("reports/audits/08x_promotion_nonpromotion_EDA_260516/08x_top_observed_differences_for_review.csv")
    obs = [r for r in obs if r["feature_set_name"] == "expanded_feature_set"][:8]
    seg = rows("reports/segments/17x_segmentation_design_260516/17x_segment_summary.csv")
    prof = rows("reports/segments/17x_segmentation_design_260516/17x_segment_feature_profile.csv")
    prof_map = {(r["representative_segment"], r["feature"]): fnum(r["mean"]) for r in prof}
    shap = [r for r in rows("reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_global_importance.csv") if r["dataset_scope"] == "overall_with_promotion" and r["model_name"] == "LightGBM"][:10]
    fam = [r for r in rows("reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_family_importance.csv") if r["dataset_scope"] == "overall_with_promotion" and r["model_name"] == "LightGBM"][:6]
    direc = [r for r in rows("reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_direction_summary.csv") if r["dataset_scope"] == "overall_with_promotion" and r["model_name"] == "LightGBM"][:8]
    delta = [r for r in rows("reports/audits/15x_payment_device_sensitivity_260516/15x_payment_removed_vs_original_comparison.csv") if r["model_name"] in ("LightGBM", "CatBoost")]
    nopay = [r for r in rows("reports/audits/15x_payment_device_sensitivity_260516/15x_model_summary_by_scope.csv") if r["model_name"] in ("LightGBM", "CatBoost")]
    return {
        "aarrr_cons": aarrr_cons,
        "aarrr_exp": aarrr_exp,
        "cohort": coh,
        "two": two,
        "obs": obs,
        "seg": seg,
        "prof_map": prof_map,
        "shap": shap,
        "fam": fam,
        "direc": direc,
        "delta": delta,
        "nopay": nopay,
    }


def build_chart_script() -> str:
    d = chart_data()
    seg_labels = [SEG_KO[r["representative_segment"]] for r in d["seg"]]
    stage_ko = {
        "Activation": "활성화",
        "Retention": "유지",
        "Acquisition": "획득",
        "Acquisition_context": "획득 맥락",
        "Needs_user_review": "사용자 검토 필요",
        "Retention_context": "유지 맥락",
    }
    cohort_ko = {"promotion": "100원딜", "nonpromotion": "비프로모션"}
    two_ko = {
        "promotion_repurchase": "100원딜 재구매",
        "promotion_nonrepurchase": "100원딜 미재구매",
        "nonpromotion_repurchase": "비프로모션 재구매",
        "nonpromotion_nonrepurchase": "비프로모션 미재구매",
    }
    family_ko = {
        "usage_retention_behavior": "시청·유지 행동",
        "content_preference_context": "콘텐츠 취향 맥락",
        "acquisition_split_key": "유입 구분 변수",
        "other_feature_family": "기타 피처 묶음",
        "membership_context": "멤버십 맥락",
        "demographic_proxy_caveat": "인구통계 대리 변수 주의",
    }
    scope_ko = {
        "overall_with_promotion": "전체+100원딜 포함",
        "overall_without_promotion": "전체+100원딜 제외",
        "promotion_only": "100원딜 row만",
        "nonpromotion_only": "비프로모션 row만",
    }
    weekly = {
        "w1": [d["prof_map"].get((r["representative_segment"], "watch_time_min_w1"), 0) for r in d["seg"]],
        "w2": [d["prof_map"].get((r["representative_segment"], "watch_time_min_w2"), 0) for r in d["seg"]],
        "w3": [d["prof_map"].get((r["representative_segment"], "watch_time_min_w3"), 0) for r in d["seg"]],
    }
    script_data = {
        "aarrrConsLabels": [stage_ko.get(k, k) for k in d["aarrr_cons"].keys()],
        "aarrrConsValues": list(d["aarrr_cons"].values()),
        "aarrrExpLabels": [stage_ko.get(k, k) for k in d["aarrr_exp"].keys()],
        "aarrrExpValues": list(d["aarrr_exp"].values()),
        "cohortLabels": [cohort_ko.get(r["group_name"], r["group_name"]) for r in d["cohort"]],
        "cohortRates": [round(fnum(r["repurchase_rate"]) * 100, 2) for r in d["cohort"]],
        "twoLabels": [two_ko.get(r["cohort_2x2_label"], r["cohort_2x2_label"]) for r in d["two"]],
        "twoCounts": [int(r["row_count"]) for r in d["two"]],
        "obsLabels": [f"{r['safe_model_feature_name']} ({VAR_KO.get(r['safe_model_feature_name'], '관찰 feature')})" for r in d["obs"]],
        "obsValues": [round(fnum(r["effect_size_or_abs_smd"]), 4) for r in d["obs"]],
        "segLabels": seg_labels,
        "segCounts": [int(float(r["row_count"])) for r in d["seg"]],
        "segRepurchase": [round(fnum(r["repurchase_rate"]) * 100, 1) for r in d["seg"]],
        "segRisk": [round(fnum(r["mean_churn_risk"]) * 100, 1) for r in d["seg"]],
        "weekly": weekly,
        "shapLabels": [f"{r['feature']} ({VAR_KO.get(r['feature'], r['feature_family'])})" for r in d["shap"]],
        "shapValues": [round(fnum(r["mean_abs_shap"]), 4) for r in d["shap"]],
        "famLabels": [family_ko.get(r["feature_family"], r["feature_family"]) for r in d["fam"]],
        "famValues": [round(fnum(r["mean_abs_shap_sum"]), 4) for r in d["fam"]],
        "directionLabels": [f"{r['feature']} ({VAR_KO.get(r['feature'], 'feature')})" for r in d["direc"]],
        "directionValues": [round(fnum(r["feature_value_shap_corr"]), 3) for r in d["direc"]],
        "deltaLabels": [f"{scope_ko.get(r['dataset_scope'], r['dataset_scope'])} {r['model_name']}" for r in d["delta"]],
        "deltaValues": [round(fnum(r["delta_auc_no_payment_minus_original"]) * 1000, 3) for r in d["delta"]],
        "nopayLabels": [f"{scope_ko.get(r['dataset_scope'], r['dataset_scope'])} {r['model_name']}" for r in d["nopay"]],
        "nopayValues": [round(fnum(r["oof_auc"]), 4) for r in d["nopay"]],
    }
    return f"""<script>
const DATA = {js(script_data)};
const charts = [];
const isDark = () => document.body.classList.contains('dark');
const textColor = () => isDark() ? '#b1bac4' : '#495057';
const gridColor = () => isDark() ? '#30363d' : '#dee2e6';
const borderColor = () => isDark() ? '#161b22' : '#fff';
const palette = ['#378ADD','#D4537E','#1D9E75','#f08c00','#ae3ec9','#868e96','#1971c2','#2f9e44'];
function makeChart(id, cfg) {{
  const el = document.getElementById(id);
  if (!el) return null;
  const c = new Chart(el, cfg);
  charts.push(c);
  return c;
}}
function applyThemeToCharts() {{
  charts.forEach(c => {{
    if (c.options.plugins && c.options.plugins.legend) c.options.plugins.legend.labels.color = textColor();
    Object.values(c.options.scales || {{}}).forEach(s => {{
      if (s.ticks) s.ticks.color = textColor();
      if (s.grid) s.grid.color = gridColor();
      if (s.title) s.title.color = textColor();
    }});
    c.data.datasets.forEach(ds => {{ if ('borderColor' in ds && Array.isArray(ds.backgroundColor)) ds.borderColor = borderColor(); }});
    c.update();
  }});
}}
const saved = localStorage.getItem('theme');
if (saved === 'dark') {{
  document.body.classList.add('dark');
  const btn = document.querySelector('.dark-toggle');
  if (btn) btn.textContent = '☀️ 라이트';
}}
const btn = document.querySelector('.dark-toggle');
if (btn) btn.addEventListener('click', function() {{
  document.body.classList.toggle('dark');
  this.textContent = document.body.classList.contains('dark') ? '☀️ 라이트' : '🌙 다크';
  localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
  applyThemeToCharts();
}});
function barOpts(horizontal=false) {{
  return {{
    indexAxis: horizontal ? 'y' : 'x',
    responsive: true,
    maintainAspectRatio: false,
    resizeDelay: 120,
    scales: {{
      x: {{ ticks: {{ color: textColor() }}, grid: {{ color: gridColor() }} }},
      y: {{ ticks: {{ color: textColor() }}, grid: {{ color: gridColor() }} }}
    }},
    plugins: {{ legend: {{ labels: {{ color: textColor() }} }} }}
  }};
}}
makeChart('row_waterfall', {{type:'bar',data:{{labels:['원본','21일 미만 제외 후','완전중복 추가 행 제거 후','분석 cohort'],datasets:[{{label:'행 수',data:[23343,23105,23079,23079],backgroundColor:['#378ADD','#f08c00','#D4537E','#1D9E75']}}]}},options:barOpts()}});
makeChart('feature_count_flow', {{type:'bar',data:{{labels:['보수 피처셋 22개','확장 피처셋 80개','결제기기 제거 전체 76개','결제기기 제거 기타 75개'],datasets:[{{label:'피처 수',data:[22,80,76,75],backgroundColor:palette}}]}},options:barOpts()}});
makeChart('cold_start_fix', {{type:'bar',data:{{labels:['3일 fixed 전체','7일 fixed 전체','3일 fixed 분석 cohort','7일 fixed 분석 cohort'],datasets:[{{label:'수정된 행 수',data:[1782,964,1767,958],backgroundColor:['#D4537E','#D4537E','#378ADD','#378ADD']}}]}},options:barOpts()}});
makeChart('aarrr_conservative', {{type:'doughnut',data:{{labels:DATA.aarrrConsLabels,datasets:[{{data:DATA.aarrrConsValues,backgroundColor:palette,borderColor:borderColor(),borderWidth:2}}]}},options:{{plugins:{{legend:{{labels:{{color:textColor()}}}}}}}}}});
makeChart('aarrr_expanded', {{type:'doughnut',data:{{labels:DATA.aarrrExpLabels,datasets:[{{data:DATA.aarrrExpValues,backgroundColor:palette,borderColor:borderColor(),borderWidth:2}}]}},options:{{plugins:{{legend:{{labels:{{color:textColor(),font:{{size:11}}}}}}}}}}}});
makeChart('cohort_bar', {{type:'bar',data:{{labels:DATA.cohortLabels,datasets:[{{label:'재구매율(%)',data:DATA.cohortRates,backgroundColor:['#D4537E','#1D9E75']}}]}},options:barOpts()}});
makeChart('twobytwo', {{type:'bar',data:{{labels:DATA.twoLabels,datasets:[{{label:'행 수',data:DATA.twoCounts,backgroundColor:['#1D9E75','#D4537E','#1D9E75','#D4537E']}}]}},options:barOpts()}});
makeChart('observed_diff_chart', {{type:'bar',data:{{labels:DATA.obsLabels,datasets:[{{label:'관찰 차이 크기',data:DATA.obsValues,backgroundColor:'#378ADD'}}]}},options:barOpts(true)}});
makeChart('auc_chart', {{type:'line',data:{{labels:['11x 확장','12x LightGBM','14x Optuna 후보','15x 결제기기 제거'],datasets:[
  {{label:'전체+100원딜 포함',data:[0.8770,0.8773,0.8797,0.8787],borderColor:'#378ADD',backgroundColor:'#378ADD',tension:.25}},
  {{label:'전체+100원딜 제외',data:[0.8725,0.8733,0.8756,0.8738],borderColor:'#D4537E',backgroundColor:'#D4537E',tension:.25}},
  {{label:'100원딜 row만',data:[0.8606,0.8616,0.8634,0.8620],borderColor:'#f08c00',backgroundColor:'#f08c00',tension:.25}},
  {{label:'비프로모션 row만',data:[0.8830,0.8838,0.8871,0.8847],borderColor:'#1D9E75',backgroundColor:'#1D9E75',tension:.25}}
]}},options:barOpts()}});
makeChart('payment_delta_chart', {{type:'bar',data:{{labels:DATA.deltaLabels,datasets:[{{label:'AUC 변화량 x1000',data:DATA.deltaValues,backgroundColor:DATA.deltaValues.map(v=>v>=0?'#1D9E75':'#D4537E')}}]}},options:barOpts(true)}});
makeChart('nopay_auc_chart', {{type:'bar',data:{{labels:DATA.nopayLabels,datasets:[{{label:'15x AUC',data:DATA.nopayValues,backgroundColor:'#378ADD'}}]}},options:barOpts(true)}});
makeChart('shap_top_chart', {{type:'bar',data:{{labels:DATA.shapLabels,datasets:[{{label:'mean |SHAP|',data:DATA.shapValues,backgroundColor:'#378ADD'}}]}},options:barOpts(true)}});
makeChart('shap_family_chart', {{type:'doughnut',data:{{labels:DATA.famLabels,datasets:[{{data:DATA.famValues,backgroundColor:palette,borderColor:borderColor(),borderWidth:2}}]}},options:{{plugins:{{legend:{{labels:{{color:textColor(),font:{{size:11}}}}}}}}}}}});
makeChart('shap_direction_chart', {{type:'bar',data:{{labels:DATA.directionLabels,datasets:[{{label:'피처값과 SHAP 방향 상관',data:DATA.directionValues,backgroundColor:DATA.directionValues.map(v=>v>=0?'#1D9E75':'#D4537E')}}]}},options:barOpts(true)}});
makeChart('segment_pie', {{type:'pie',data:{{labels:DATA.segLabels,datasets:[{{data:DATA.segCounts,backgroundColor:palette,borderColor:borderColor(),borderWidth:2}}]}},options:{{plugins:{{legend:{{labels:{{color:textColor(),font:{{size:10}}}}}}}}}}}});
makeChart('segment_dist', {{type:'bar',data:{{labels:DATA.segLabels,datasets:[{{label:'행 수',data:DATA.segCounts,backgroundColor:palette}}]}},options:barOpts(true)}});
makeChart('segment_risk', {{type:'bar',data:{{labels:DATA.segLabels,datasets:[{{label:'재구매율(%)',data:DATA.segRepurchase,backgroundColor:'#1D9E75'}},{{label:'평균 이탈위험(%)',data:DATA.segRisk,backgroundColor:'#D4537E'}}]}},options:barOpts(true)}});
makeChart('segment_weekly_watch', {{type:'bar',data:{{labels:DATA.segLabels,datasets:[{{label:'1주차 시청시간(분)',data:DATA.weekly.w1,backgroundColor:'#378ADD'}},{{label:'2주차 시청시간(분)',data:DATA.weekly.w2,backgroundColor:'#D4537E'}},{{label:'3주차 시청시간(분)',data:DATA.weekly.w3,backgroundColor:'#1D9E75'}}]}},options:barOpts(true)}});
makeChart('recommendation_priority_chart', {{type:'bar',data:{{labels:DATA.segLabels,datasets:[{{label:'재구매율(%)',data:DATA.segRepurchase,backgroundColor:'#1D9E75'}},{{label:'평균 이탈위험(%)',data:DATA.segRisk,backgroundColor:'#D4537E'}}]}},options:barOpts()}});
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.sidebar-nav a');
window.addEventListener('scroll', () => {{
  let current = '';
  sections.forEach(s => {{ if (window.scrollY >= s.offsetTop - 80) current = s.id; }});
  navLinks.forEach(a => {{ a.classList.remove('active'); if (a.getAttribute('href') === '#' + current) a.classList.add('active'); }});
}});
</script>"""


def write_checklist() -> None:
    checklist = [
        ("01", "AARRR Needs_user_review 오류", "payment_is_*를 Needs_user_review로 표기", "age/gender/auth proxy 4개로 정정하고 payment_is_*는 07x Acquisition_context, 15x removal risk로 분리", "FIXED", "07x_feature_mapping_master.csv", ""),
        ("02", "cold_start 변수명", "_fixed 없는 변수명을 최종 피처처럼 표기", "is_cold_start_3d_fixed / is_cold_start_7d_fixed 기준으로 설명", "FIXED", "06x_model_feature_lists.csv", ""),
        ("03", "watch_time 변수명", "watch_time_w1/w2/w3 축약 표기", "watch_time_min_w1/w2/w3 실제 safe name 기준으로 수정", "FIXED", "06x_model_feature_lists.csv", ""),
        ("04", "14x/15x 혼동", "14x AUC를 no-payment 76/75로 표기", "14x expanded_feature_set와 15x expanded_no_payment_device를 분리", "FIXED", "14x_model_summary_by_scope.csv;15x_model_summary_by_scope.csv", ""),
        ("05", "최종 표현 과잉", "최종 모델/최종 AUC/최종 채택", "candidate AUC, diagnostic score, not final model selection wording으로 완화", "FIXED", "14x_safe_unsafe_wording.csv;15x_safe_unsafe_wording.csv", ""),
        ("06", "SHAP is_promotion 순위", "is_promotion 3위", "개별 feature 2위, acquisition_split_key family 3위로 정정", "FIXED", "16x_SHAP_global_importance.csv;16x_SHAP_family_importance.csv", ""),
        ("07", "segmentation rule 설명", "행동 rule only처럼 읽힘", "churn_risk percentile + day0~20 behavior flag 결합 및 우선순위 배정 설명 추가", "FIXED", "17x_representative_segment_rules.csv", ""),
        ("08", "AARRR Revenue/Referral", "누락", "Revenue target proxy와 Referral not observed 카드/테이블 행 추가", "FIXED", "07x_AARRR_summary_by_feature_set.csv", ""),
        ("09", "duplicate 48/26", "숫자 충돌처럼 보임", "필터 전/후 기준 차이로 설명", "FIXED", "01_user_key_duplicate_audit.csv;06x_row_policy_audit.csv", ""),
        ("10", "source artifact", "단계명만 표기", "주요 수치에 source details 추가", "FIXED", "core source csvs", ""),
        ("11", "Noto Sans KR", "font fallback 누락", "CSS font-family에 Noto Sans KR 추가", "FIXED", "project_guide_v2.html", ""),
        ("12", "Chart.js dark mode", "toggle 후 색상 미갱신 가능", "chart array와 applyThemeToCharts() 구현", "FIXED", "project_guide_v2.html", ""),
        ("13", "변수명 한국어 설명", "영어명 단독 다수", "주요 변수와 flag에 괄호 설명 추가", "FIXED", "06x/16x/17x core CSV", ""),
        ("14", "세그먼트 상세 해설", "카드 중심 짧은 설명", "세그먼트 배정 원리, 우선순위, 7개 segment 쉬운 설명 보강", "FIXED", "17x_segment_summary.csv;17x_representative_segment_rules.csv", ""),
        ("15", "Flag dictionary", "누락", "17x_internal_multiflag_definitions 기준 dictionary 추가", "FIXED", "17x_internal_multiflag_definitions.csv", ""),
        ("16", "시각화 보강", "기존 차트 수 제한", "row waterfall, feature flow, AARRR, cohort, AUC, SHAP, segment pie/weekly 패턴 등 추가", "FIXED", "summary/profile CSVs", ""),
        ("17", "score source 선택 이유", "15x LightGBM score 사용 사실만 있고 이유 부족", "16x SHAP 기준과 17x segmentation score 기준을 맞추기 위한 선택임을 추가", "FIXED", "17x_score_source_selection.csv;17x_segment_SHAP_evidence_link.csv", ""),
        ("18", "payment_is 제거 이유", "해석 리스크만 짧게 언급", "결제기기/시청기기 차이, 결제자와 시청자 불일치 가능성, near-neutral 성능 변화, SHAP/segment 해석 리스크를 명시", "FIXED", "15x_payment_removed_vs_original_comparison.csv;15x_recommendation_for_canonical_feature_contract.csv", ""),
        ("19", "발표 방어 QA", "기초 경고 중심", "row 단위 반복을 늘리지 않고 score source, payment proxy, SHAP, threshold, segment policy 중심 심화 QA 추가", "FIXED", "18x_mentor_QA_defense.csv;18x_safe_unsafe_wording.csv;18x_open_risks.csv", ""),
    ]
    path = AUDIT / "project_guide_v2_revision_checklist.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "issue", "before_summary", "after_summary", "status", "source_artifact", "note"])
        w.writerows(checklist)


def write_fingerprint() -> None:
    path = AUDIT / "project_guide_v2_source_fingerprint.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file_path", "file_role", "sha256", "mtime", "size_bytes", "status"])
        for rel, role in SOURCE_FILES:
            p = ROOT / rel
            if p.exists():
                st = p.stat()
                w.writerow([rel, role, file_sha(p), datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"), st.st_size, "FOUND"])
            else:
                w.writerow([rel, role, "", "", "", "MISSING"])


def update_note() -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    note = PARK / "note.md"
    existing = note.read_text(encoding="utf-8") if note.exists() else ""
    existing = re.sub(
        r"\n## \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| project_guide\.html 2차 수정\n.*?(?=\n## \d{4}-\d{2}-\d{2}|\Z)",
        "",
        existing,
        flags=re.S,
    )
    append = f"""

## {now} | project_guide.html 2차 수정

작업명: `project_guide.html` 2차 수정 및 `project_guide_v2.html` 생성.

수정 이유: ChatGPT claim validation audit와 core source CSV 검수에서 기존 HTML의 FAIL/WARN 성격 오류가 확인되었다. 주요 오류는 07x Needs_user_review와 payment_is_* 혼동, cold_start `_fixed` 변수명 누락, watch_time safe name 불일치, 14x Optuna 결과와 15x no-payment sensitivity 결과 혼합, 최종 모델처럼 읽히는 과잉 표현, SHAP `is_promotion` 순위 오기, 세그먼트가 행동 rule only처럼 읽히는 설명 부족이었다.

주요 수정 항목:
- 07x Needs_user_review 4개를 `age_group`, `is_female`, `is_male`, `is_user_verified`로 정정했다.
- `is_cold_start_3d_fixed`, `is_cold_start_7d_fixed` 기준을 반영했다.
- `watch_time_min_w1`, `watch_time_min_w2`, `watch_time_min_w3` safe name 기준으로 설명했다.
- 14x `expanded_feature_set` Optuna 후보 결과와 15x `expanded_no_payment_device` sensitivity 결과를 분리했다.
- “최종 모델”, “최종 채택 AUC”처럼 운영 확정으로 읽힐 수 있는 표현을 후보 기준 AUC, diagnostic score, not final model selection 표현으로 완화했다.
- 16x SHAP에서 개별 feature 기준 `is_promotion`은 2위, family 기준 `acquisition_split_key`는 3위로 정정했다.
- 17x 세그먼트 설명을 `churn_risk` percentile + day0~20 행동 flag + 우선순위 대표 라벨 방식으로 보강했다.
- 세그먼트별 쉬운 한국어 설명, 대응 후보, flag dictionary를 추가했다.
- source artifact details와 다수의 Chart.js 시각화를 추가했다.
- score source 선택 이유를 추가했다. 17x 세그먼트 점수는 15x `expanded_no_payment_device` / `overall_with_promotion` / `LightGBM` OOF 진단 점수를 사용했고, 이는 16x SHAP 근거와 모델 기준을 맞추기 위한 선택이다.
- `payment_is_*` 제거 이유를 결론 수준으로 보강했다. 결제기기와 시청기기가 다르며, 결제자와 실제 시청자가 다를 수 있고, 15x sensitivity에서 성능 손실이 near-neutral 수준이었다는 점을 명시했다.
- 18x safe/unsafe wording과 멘토 방어 QA를 추가했다. 기존 row 단위 반복을 늘리지 않고 score source, payment proxy, SHAP, threshold, 제언 정책화 리스크 중심으로 구성했다.

생성 산출물:
- `park.ingyeom/project_guide_v2.html`
- `park.ingyeom/reports/audits/project_guide_v2_revision_checklist.csv`
- `park.ingyeom/reports/audits/project_guide_v2_source_fingerprint.csv`
- `park.ingyeom/zip/project_guide_v2_review_package_*.zip`

아직 남은 검수 필요 사항:
- OOF 기반 AUC 직접 재계산은 이번 HTML 수정 범위 밖이다.
- `project_guide_v2.html`은 ChatGPT 또는 사람 기준 2차 검수가 필요하다.
- 차트는 summary/profile CSV 기반 설명용 시각화이며, 새 모델 학습이나 새 통계 검정을 수행한 것이 아니다.

주의:
- 이 HTML은 설명형 guide이며, 최종 모델 확정 문서가 아니다.
- segment는 provisional representative label이다.
- row count는 customer count가 아니라 subscription-event row count다.
"""
    note.write_text(existing.rstrip() + append, encoding="utf-8", newline="\n")


def write_review_zip() -> Path:
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    inv = AUDIT / "project_guide_v2_review_inventory.csv"
    files = [
        PARK / "project_guide.html",
        PARK / "project_guide_v2.html",
        PARK / "note.md",
        AUDIT / "project_guide_v2_revision_checklist.csv",
        AUDIT / "project_guide_v2_source_fingerprint.csv",
    ]
    with inv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["relative_path", "file_name", "extension", "size_bytes", "sha256"])
        for p in files + [inv]:
            rel = str(p.relative_to(ROOT))
            w.writerow([rel, p.name, p.suffix, p.stat().st_size, file_sha(p)])
    files.append(inv)
    zip_path = ZIP_DIR / f"project_guide_v2_review_package_{ts}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(ROOT))
    return zip_path


if __name__ == "__main__":
    build()
