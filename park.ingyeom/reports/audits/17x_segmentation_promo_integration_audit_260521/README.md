> 17x segmentation promotion-integration decision audit

## 작업 목적

park.ingyeom 17x 세그먼트를 최종 파이프라인 뼈대로 유지하면서, 100원딜 프로모션 유입 고객을 발표와 비즈니스 제언에서 어떻게 드러낼 수 있는지 검수했습니다.

## 수정하지 않은 것

- 원본 CSV
- 기존 notebook
- 기존 17x 산출물
- 기존 18x 산출물
- 모델 결과
- SHAP 결과
- segment assignment

## 읽은 입력 파일

- PUBLIC\note.md
- PUBLIC\reports\business\18_business_recommendation_storyline_hotfix_260520\18_business_storyline_memo_hotfix.md
- PUBLIC\reports\business\18_business_recommendation_storyline_hotfix_260520\18_dashboard_handoff_datamart_hotfix.csv
- PUBLIC\reports\business\18_business_recommendation_storyline_hotfix_260520\18_presentation_talking_points_hotfix.md
- PUBLIC\reports\business\18_business_recommendation_storyline_hotfix_260520\18_promo0_comparison_reference_hotfix.csv
- PUBLIC\reports\business\18_business_recommendation_storyline_hotfix_260520\18_promo1_main_business_action_matrix_hotfix.csv
- PUBLIC\reports\business\18_business_recommendation_storyline_hotfix_260520\18_safe_unsafe_wording_hotfix.csv
- PUBLIC\reports\business\18_business_recommendation_storyline_hotfix_260520\18_segment_visual_guide_v2_polished.html
- PUBLIC\reports\business\18_business_recommendation_storyline_hotfix_260520\18_storyline_comparison_clean_hotfix.csv
- PUBLIC\results\11_baseline_growth_comparison_260520\lr_baseline_promo0\feature_manifest_used.csv
- PUBLIC\results\11_baseline_growth_comparison_260520\lr_baseline_promo1\feature_manifest_used.csv
- PUBLIC\results\12_model_family_comparison_260520\four_model_comparison_review\12_final_result_metric_summary.csv
- PUBLIC\results\12_model_family_comparison_260520\gradientboosting_promo0\feature_manifest_used.csv
- PUBLIC\results\12_model_family_comparison_260520\gradientboosting_promo1\feature_manifest_used.csv
- PUBLIC\results\15_oof_score_or_sensitivity_260520\four_model_oof_scores_hotfix_260520\15_oof_metric_summary.csv
- PUBLIC\results\17_segmentation_design_260520\promo_scope_oof_behavior_segments_demographic_hotfix_260520\17_age_group_audit.csv
- PUBLIC\results\17_segmentation_design_260520\promo_scope_oof_behavior_segments_demographic_hotfix_260520\17_demographic_hotfix_summary.csv
- PUBLIC\results\17_segmentation_design_260520\promo_scope_oof_behavior_segments_demographic_hotfix_260520\17_gender_derivation_audit.csv
- PUBLIC\results\17_segmentation_design_260520\promo_scope_oof_behavior_segments_hotfix_260520\17_content_preference_signal_audit.csv
- PUBLIC\results\17_segmentation_design_260520\promo_scope_oof_behavior_segments_hotfix_260520\17_representative_segment_assignment_hotfix.csv
- PUBLIC\results\17_segmentation_design_260520\promo_scope_oof_behavior_segments_hotfix_260520\17_representative_segment_rules_hotfix.csv
- PUBLIC\results\17_segmentation_design_260520\promo_scope_oof_behavior_segments_hotfix_260520\17_segment_summary_hotfix.csv
- PUBLIC\results\17_segmentation_design_260520\promo_scope_oof_behavior_segments_quality_hotfix_260520\17_other_needs_review_decomposition_quality_hotfix.csv
- PUBLIC\results\17_segmentation_design_260520\promo_scope_oof_behavior_segments_quality_hotfix_260520\17_revised_representative_segment_proposal.csv
- PUBLIC\results\17_segmentation_design_260520\promo_scope_oof_behavior_segments_quality_hotfix_260520\17_revised_segment_assignment_simulation.csv
- PUBLIC\results\17_segmentation_design_260520\promo_scope_oof_behavior_segments_quality_hotfix_260520\17_revised_segment_summary_simulation.csv
- PUBLIC\results\17_segmentation_design_260520\promo_scope_oof_behavior_segments_quality_hotfix_260520\17_segment_quality_audit.csv
- park.ingyeom\note.md
- park.ingyeom\reports\audits\15x_payment_device_sensitivity_260516\15x_model_summary_by_scope.csv
- park.ingyeom\reports\models\12x_model_family_comparison_260516\12x_model_summary_by_scope.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_business_action_candidates.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_dashboard_handoff_datamart.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_internal_multiflag_assignment.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_internal_multiflag_definitions.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_proxy_artifact_audit.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_representative_segment_assignment.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_representative_segment_rules.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_score_source_selection.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_segment_SHAP_evidence_link.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_segment_feature_profile.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_segment_summary.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_segmentation_base_datamart.csv
- park.ingyeom\reports\segments\17x_segmentation_design_260516\README.md
- park.ingyeom\reports\segments\17x_segmentation_design_260516\note_tail_copy.md

## 생성 산출물

- 01_park_segment_rule_detail.csv
- 02_park_segment_promo_distribution.csv
- 03_park_segment_promo_lift.csv
- 04_general_observation_decomposition_audit.csv
- 05_content_preference_target_candidate_validity_audit.csv
- 06_segmentation_strategy_comparison.csv
- 07_promo_aware_label_proposal.csv
- 08_PUBLIC_segment_importability_audit.csv
- 09_campaign_targeting_language_audit.csv
- 10_final_score_source_decision_audit.csv
- 11_segmentation_promo_integration_recommendation.md

## 핵심 발견

- park 17x는 behavior/risk 기반 segment rule을 유지하고 있으며 is_promotion은 rule 조건이 아니라 segment 내부 composition으로 확인하는 편이 방어 가능합니다.
- promo-aware label overlay는 가능합니다. 다만 label은 새 rule이 아니라 presentation layer라고 명시해야 합니다.
- PUBLIC promo-scope segmentation은 rule import보다 label, action narrative, visual structure import가 더 안전합니다.
- content_preference_target_candidate는 발표용 추천 타겟으로 바로 쓰기보다 content-context 또는 genre-cue 후보로 낮추는 편이 안전합니다.
- general_observation은 지금 audit 범위에서는 residual/general bucket으로 두는 편이 안전합니다.

## blocking issue

- None.

## non-blocking issue

- PUBLIC과 park는 row count와 score basis가 다르므로 단순 병합하면 안 됩니다.
- PUBLIC content_preference_signal broad-flag 이슈는 park content label 검토의 중요한 caveat입니다.
- promo-aware label은 사용자 승인 없이 final segment label로 확정하면 안 됩니다.

## 사용자 결정 필요 항목

- promo-aware presentation label 사용 여부
- general_observation 이름 변경 여부
- content_preference_target_candidate 강등 또는 이름 변경 여부
- PUBLIC action narrative를 park 발표에 가져올 범위
- 별도 promo-scope segmentation redesign 착수 여부

## ChatGPT가 다음에 검수해야 할 파일

- 01_park_segment_rule_detail.csv
- 02_park_segment_promo_distribution.csv
- 04_general_observation_decomposition_audit.csv
- 05_content_preference_target_candidate_validity_audit.csv
- 06_segmentation_strategy_comparison.csv
- 07_promo_aware_label_proposal.csv
- 10_final_score_source_decision_audit.csv
- 11_segmentation_promo_integration_recommendation.md
