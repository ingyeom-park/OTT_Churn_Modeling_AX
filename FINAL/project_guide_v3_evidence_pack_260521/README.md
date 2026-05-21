> README

> 작업 목적

최종 `project_guide_v3.html`을 직접 만들기 전에, ChatGPT와 사용자가 guide v3 설계를 정확히 할 수 있도록 데이터셋 lineage, preprocessing policy, feature contract, derived feature, AARRR, 07x~18x timeline, score source, segmentation basis를 실제 파일 기준으로 정리한 evidence pack이다.

> 읽은 파일

- `FINAL\final_note.md`
- `FINAL\project_execution_plan_260521.md`
- `park.ingyeom\note.md`
- `PUBLIC\note.md`
- `park.ingyeom\reports\audits\01_data_contract_260513\01_data_contract_summary.csv`
- `park.ingyeom\reports\audits\01_data_contract_260513\01_column_inventory.csv`
- `park.ingyeom\reports\audits\01_data_contract_260513\01_duration_anomaly_audit.csv`
- `park.ingyeom\reports\audits\01_data_contract_260513\01_user_key_duplicate_audit.csv`
- `park.ingyeom\reports\audits\02_target_score_orientation_260513\02_target_contract.csv`
- `park.ingyeom\reports\audits\02_target_score_orientation_260513\02_analysis_unit_contract.csv`
- `park.ingyeom\reports\audits\03_observation_window_policy_260513\03_observation_window_policy.csv`
- `park.ingyeom\reports\audits\04_promotion_split_260513\04_promotion_split_contract.csv`
- `park.ingyeom\reports\audits\05x_feature_contract_rebuild_260515\05x_conservative_safe_22_contract.csv`
- `park.ingyeom\reports\audits\05x_feature_contract_rebuild_260515\05x_expanded_feature_set_candidate_contract.csv`
- `park.ingyeom\reports\audits\05y_feature_approval_and_dictionary_patch2_260515\05y_patch2_conservative_safe_feature_contract.csv`
- `park.ingyeom\reports\audits\05y_feature_approval_and_dictionary_patch2_260515\05y_patch2_expanded_feature_contract.csv`
- `park.ingyeom\reports\audits\05y_feature_approval_and_dictionary_patch2_260515\05y_patch2_excluded_feature_contract.csv`
- `park.ingyeom\reports\audits\06x_dataset_generation_260515\06x_source_master_profile.csv`
- `park.ingyeom\reports\audits\06x_dataset_generation_260515\06x_row_policy_audit.csv`
- `park.ingyeom\reports\audits\06x_dataset_generation_260515\06x_dataset_comparison_summary.csv`
- `park.ingyeom\reports\audits\06x_dataset_generation_260515\06x_dataset_schema_conservative.csv`
- `park.ingyeom\reports\audits\06x_dataset_generation_260515\06x_dataset_schema_expanded.csv`
- `park.ingyeom\reports\audits\06x_dataset_generation_260515\06x_model_feature_lists.csv`
- `park.ingyeom\reports\audits\07x_feature_mapping_AARRR_260515\07x_feature_mapping_master.csv`
- `park.ingyeom\reports\audits\07x_feature_mapping_AARRR_260515\07x_AARRR_summary_by_feature_set.csv`
- `park.ingyeom\reports\audits\08x_promotion_nonpromotion_EDA_260516\08x_dataset_scope_summary.csv`
- `park.ingyeom\reports\audits\09x_promotion_repurchase_2x2_EDA_260516\09x_2x2_cohort_summary.csv`
- `park.ingyeom\reports\audits\10x_feature_distribution_redundancy_pre_audit_260516\10x_downstream_handoff.csv`
- `park.ingyeom\reports\models\11x_baseline_growth_comparison_260516\11x_model_summary_by_scope.csv`
- `park.ingyeom\reports\models\12x_model_family_comparison_260516\12x_model_summary_by_scope.csv`
- `park.ingyeom\reports\models\12x_model_family_comparison_260516\12x_candidate_selection_by_scope.csv`
- `park.ingyeom\reports\models\14x_lightweight_candidate_tuning_260516\14x_candidate_recommendation_summary.csv`
- `park.ingyeom\reports\audits\15x_payment_device_sensitivity_260516\15x_model_summary_by_scope.csv`
- `park.ingyeom\reports\audits\15x_payment_device_sensitivity_260516\15x_payment_device_feature_policy.csv`
- `park.ingyeom\reports\audits\15x_payment_device_sensitivity_260516\15x_expanded_no_payment_device_feature_list.csv`
- `park.ingyeom\reports\audits\15x_payment_device_sensitivity_260516\15x_recommendation_for_canonical_feature_contract.csv`
- `park.ingyeom\reports\interpretation\16x_SHAP_candidate_interpretation_260516\16x_SHAP_candidate_plan.csv`
- `park.ingyeom\reports\interpretation\16x_SHAP_candidate_interpretation_260516\16x_payment_removed_input_gate.csv`
- `park.ingyeom\reports\interpretation\16x_SHAP_candidate_interpretation_260516\16x_model_refit_summary.csv`
- `park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_score_source_selection.csv`
- `park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_segment_summary.csv`
- `park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_representative_segment_rules.csv`
- `park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_internal_multiflag_definitions.csv`
- `park.ingyeom\reports\storyline\18x_business_recommendation_storyline_260518\18x_segment_priority_for_presentation.csv`
- `park.ingyeom\reports\storyline\18x_business_recommendation_storyline_260518\18x_mentor_QA_defense.csv`
- `park.ingyeom\reports\storyline\18x_business_recommendation_storyline_260518\18x_safe_unsafe_wording.csv`
- `FINAL\segment_interpretation_patch_260521\07_promo_aware_segment_label_mapping.csv`
- `FINAL\segment_interpretation_patch_260521\08_segment_business_action_matrix.csv`
- `FINAL\final_note_role_reclassification_patch_260521\final_note_patch_diff_summary.md`
- `PUBLIC\reports\business\18_business_recommendation_storyline_hotfix_260520\18_business_storyline_memo_hotfix.md`
- `PUBLIC\reports\business\18_business_recommendation_storyline_hotfix_260520\18_safe_unsafe_wording_hotfix.csv`
- `PUBLIC\reports\business\18_business_recommendation_storyline_hotfix_260520\18_segment_visual_guide_v2_polished.html`
- `park.ingyeom\notebook\06x_dataset_generation_260515\06x_dataset_generation_260515.ipynb`
- `park.ingyeom\notebook\07x_feature_mapping_AARRR_260515\07x_feature_mapping_AARRR_260515.ipynb`
- `park.ingyeom\notebook\11x_baseline_growth_comparison_260516\11x_baseline_growth_comparison_260516.ipynb`
- `park.ingyeom\notebook\12x_model_family_comparison_260516\12x_model_family_comparison_260516.ipynb`
- `park.ingyeom\notebook\16x_SHAP_candidate_interpretation_260516\16x_SHAP_candidate_interpretation_260516.ipynb`
- `park.ingyeom\notebook\17x_segmentation_design_260516\17x_segmentation_design_260516.ipynb`

> 생성 산출물

- `dataset_lineage_summary.csv`
- `preprocessing_policy_summary.md`
- `column_feature_contract_summary.csv`
- `derived_feature_lineage.md`
- `AARRR_design_summary.md`
- `AARRR_feature_mapping_table.csv`
- `stage_07_to_18_timeline.csv`
- `model_and_score_source_summary.md`
- `segmentation_basis_summary.md`
- `guide_v3_required_content_checklist.csv`
- `unanswered_questions_for_chatgpt.md`
- `README.md`
- `final_checks.csv`
- `source_fingerprint_before_after.csv`
- `review_zip_inventory.csv`

> 핵심 발견

- raw master는 23,343행, 91컬럼이다.
- duration < 21 row 238개와 exact full duplicate extra row 26개 제외 후 primary main cohort는 23,079행이다.
- conservative dataset은 22 feature, expanded dataset은 80 feature 기준이다.
- expanded_no_payment_device는 overall_with_promotion 기준 76 feature다.
- guide v3의 final score source 설명은 `LightGBM / expanded_no_payment_device / overall_with_promotion / OOF churn_risk`로 둔다.
- PUBLIC은 final numeric basis가 아니라 reference branch다.

> guide v3에 반드시 반영할 점

row count를 unique customer count로 말하지 말아야 한다. 100원딜은 인과가 아니라 acquisition context로 설명해야 한다. age/gender는 원인이 아니라 personalization layer다. Referral은 결과가 아니라 후속 실험 제안이다. 17x segment rule과 assignment는 그대로 유지한다.

> ChatGPT가 다음에 판단해야 할 점

guide v3의 섹션 순서, 시각화 배치, 멘토 Q&A 깊이, 5~7순위 role reclassification의 설명 길이, PUBLIC reference branch 언급 범위를 결정해야 한다.
