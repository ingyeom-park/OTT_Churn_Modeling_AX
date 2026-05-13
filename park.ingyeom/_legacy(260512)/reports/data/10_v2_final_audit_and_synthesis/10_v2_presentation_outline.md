# 10 v2 Presentation Outline

Recommended slide count: 13 to 15 slides.

## 1. Problem definition
- Key message: 재구독 여부를 예측하고 보수적인 리텐션 전략 후보를 만든다.
- Supporting metric: target: is_repurchase
- Recommended figure/table: 01/05 summary tables
- Caution wording: 성과 최적화보다 누수 방지와 방어 가능한 전략이 우선.
- Source: `park.ingyeom/reports/data/05_v2_modeling_dataset/feature_sets_v2.json`

## 2. Why v2 changed the project
- Key message: v1 가정은 역사적 참고일 뿐 v2에서 재검증했다.
- Supporting metric: raw Membership 24,074 rows
- Recommended figure/table: 01_v2_raw_file_inventory.csv
- Caution wording: v1 row count/AUC를 그대로 쓰지 않는다.
- Source: `park.ingyeom/reports/tables/01_v2_data_overview_and_audit/01_v2_raw_file_inventory.csv`

## 3. Data and preprocessing audit
- Key message: strict conflict와 duplicate만 명시적으로 제외했다.
- Supporting metric: retained 23,933 rows
- Recommended figure/table: 10_v2_row_count_lineage.csv
- Caution wording: duration policy는 deferred.
- Source: `park.ingyeom/reports/tables/10_v2_final_audit_and_synthesis/10_v2_row_count_lineage.csv`

## 4. Observation windows
- Key message: w1_3은 조기 관측, w1_4는 late-period 비교다.
- Supporting metric: w1_3/w1_4 both 23,933 rows
- Recommended figure/table: 05_v2_merge_integrity_summary.csv
- Caution wording: w1_4를 early-warning으로 말하지 않는다.
- Source: `park.ingyeom/reports/tables/05_v2_modeling_dataset/05_v2_merge_integrity_summary.csv`

## 5. Baseline modeling and sanity audit
- Key message: group-aware split과 sanity audit로 높은 AUC를 점검했다.
- Supporting metric: conservative AUC 0.8705
- Recommended figure/table: 06b sanity tables
- Caution wording: 누수 없음의 절대 증명은 아니다.
- Source: `park.ingyeom/reports/data/06b_v2_baseline_sanity_audit/06b_sanity_audit_summary.json`

## 6. Why w1_3 main model
- Key message: w1_3이 intervention timing에 더 방어 가능하다.
- Supporting metric: w1_3 AUC 0.8705
- Recommended figure/table: 06 best config
- Caution wording: 최고 AUC인 w1_4는 late-period.
- Source: `park.ingyeom/reports/data/06_v2_baseline_modeling/06_v2_best_model_config.json`

## 7. TRUE SHAP interpretation
- Key message: Stage 07r TRUE SHAP으로 모델 설명을 제시한다.
- Supporting metric: top family: usage
- Recommended figure/table: 07r SHAP beeswarm/global bar
- Caution wording: SHAP은 인과가 아니다.
- Source: `park.ingyeom/reports/data/07r_v2_true_shap_interpretation/07r_true_shap_summary.json`

## 8. Risk bands
- Key message: churn_risk_score 기반 risk band가 targeting frame이다.
- Supporting metric: top decile churn rate from Stage 08b
- Recommended figure/table: 08b final segment churn figure
- Caution wording: 위험점수는 확률 보정 tier가 아니다.
- Source: `park.ingyeom/reports/tables/08b_v2_segmentation_refinement/08b_final_segment_summary_holdout.csv`

## 9. Refined final segments
- Key message: Stage 08b에서 6개 발표용 세그먼트로 정리했다.
- Supporting metric: 6 segments
- Recommended figure/table: 08b final segment summary
- Caution wording: Stage 08 원본 탐색 세그먼트를 그대로 쓰지 않는다.
- Source: `park.ingyeom/reports/tables/08b_v2_segmentation_refinement/08b_final_segment_summary_holdout.csv`

## 10. Scenario simulation
- Key message: Stage 09는 가정 기반 retained-user scenario다.
- Supporting metric: base portfolio retained users
- Recommended figure/table: 09 portfolio figure
- Caution wording: ROI와 profit은 말하지 않는다.
- Source: `park.ingyeom/reports/tables/09_v2_business_simulation/09_v2_portfolio_simulation_summary.csv`

## 11. What we can claim
- Key message: 데이터, 모델, SHAP, 세그먼트, 시나리오를 구분해 말한다.
- Supporting metric: claim registry safe claims
- Recommended figure/table: 10 claim registry
- Caution wording: status별 wording을 따른다.
- Source: `park.ingyeom/reports/tables/10_v2_final_audit_and_synthesis/10_v2_claim_registry.csv`

## 12. What we cannot claim
- Key message: 인과효과, ROI, guaranteed lift는 금지한다.
- Supporting metric: do_not_claim entries
- Recommended figure/table: 10 safe/caution summary
- Caution wording: A/B test 전 효과 주장은 금지.
- Source: `park.ingyeom/reports/tables/10_v2_final_audit_and_synthesis/10_v2_safe_caution_do_not_claim_summary.csv`

## 13. Next steps / A-B test
- Key message: 멘토 검수 후 가정값과 실험 설계를 확정한다.
- Supporting metric: ready_for_mentor_review=Y
- Recommended figure/table: 10 readiness verdict
- Caution wording: submission 전 비용/마진/실험계획 보완.
- Source: `park.ingyeom/reports/data/10_v2_final_audit_and_synthesis/10_v2_final_readiness_verdict.md`
