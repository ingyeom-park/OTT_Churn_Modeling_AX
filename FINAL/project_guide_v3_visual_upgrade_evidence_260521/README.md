> 작업 목적
final v3 HTML을 안전하게 시각 업그레이드하기 위한 evidence extract입니다. HTML 직접 수정, final v3 직접 생성, 모델 재실행, SHAP 재계산, segmentation 재계산은 하지 않았습니다.

> 읽은 파일
- park.ingyeom/aarrr_visual_guide.html
- park.ingyeom/project_guide_v2.html
- park.ingyeom/segment_visual_guide.html
- park.ingyeom/shap_visual_guide.html
- park.ingyeom/project_guide.html
- FINAL/project_guide_v3_evidence_pack_260521/dataset_lineage_summary.csv
- FINAL/project_guide_v3_evidence_pack_260521/column_feature_contract_summary.csv
- FINAL/project_guide_v3_evidence_pack_260521/AARRR_feature_mapping_table.csv
- FINAL/project_guide_v3_evidence_pack_260521/stage_07_to_18_timeline.csv
- park.ingyeom/reports/audits/15x_payment_device_sensitivity_260516/15x_payment_removed_vs_original_comparison.csv
- park.ingyeom/reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_global_importance.csv
- park.ingyeom/reports/interpretation/16x_SHAP_candidate_interpretation_260516/16x_SHAP_family_importance.csv
- park.ingyeom/reports/segments/17x_segmentation_design_260516/17x_segment_summary.csv
- park.ingyeom/reports/segments/17x_segmentation_design_260516/17x_dashboard_handoff_datamart.csv
- FINAL/segment_interpretation_patch_260521/07_promo_aware_segment_label_mapping.csv
- FINAL/segment_interpretation_patch_260521/08_segment_business_action_matrix.csv
- FINAL/final_note.md
- FINAL/project_guide_v3_design_plan_260521.md

> 생성 산출물
HTML inventory, reusable component audit, legacy conflict audit, chart registry, chart-ready CSV, SHAP asset manifest, CSS/layout memo, recommendation, unanswered questions, final checks, source fingerprint, review zip inventory를 생성했습니다.

> 핵심 발견
`FINAL/project_guide_v3.html` 또는 `project_guide_v3_chatgpt_revised.html`은 repo에서 발견되지 않았습니다. 기존 visual guide들은 구조 참고용이며, final numeric 기준은 `FINAL/project_guide_v3_evidence_pack_260521`, 15x, 16x, 17x, FINAL patch 산출물을 따릅니다.

> final v3 업그레이드 시 주의할 점
raw 23,343은 raw source profile이고 final 기준은 23,079 subscription-event rows입니다. 100원딜, SHAP, payment-device, content_preference, general_observation, PUBLIC numeric score는 caveat를 고정해야 합니다.

> ChatGPT가 다음에 해야 할 판단
최신 final v3 HTML 파일 기준으로 section 교체 위치를 정해야 합니다. SHAP bar/family의 Chart.js vs PNG 선택과 segment action tier wording은 사용자 승인 후 확정해야 합니다.
