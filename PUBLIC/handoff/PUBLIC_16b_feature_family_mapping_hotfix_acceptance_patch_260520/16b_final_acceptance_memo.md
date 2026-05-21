# 16b Feature Family Mapping Hotfix — Final Acceptance Memo

**Date:** 2026-05-20
**Patch:** PUBLIC_16b_feature_family_mapping_hotfix_acceptance_patch_260520

---

## 이번 patch의 목적

이번 patch는 16b mapping 결과를 수정하는 작업이 아니다. ChatGPT가 실제 ZIP을 열어 검수한 결과를 반영해 acceptance 상태를 명시적으로 기록하고, source fingerprint의 자기참조/패키징 파일 변경 caveat를 정리하는 작업이다.

---

## 검수 결과 요약

- 16b mapping hotfix는 내용상 통과 가능하다.
- 기존 `technical_or_unknown` 16개 feature가 모두 business family로 재분류되었다.
- technical_or_unknown 잔여 feature는 0개다.
- 기존 SHAP 값은 재계산하지 않았다.
- family mapping만 보정했고, family-level 산출물(shap_family_importance, family_importance_before_after_comparison, promo1_vs_promo0_shap_comparison_hotfix)을 재집계했다.

---

## Feature Remap 확정 내역

| feature | new_family |
|---|---|
| recency | inactivity_recency |
| max_inactive_gap_days | inactivity_recency |
| is_only_w1 | week_specific_usage_pattern |
| is_only_w2 | week_specific_usage_pattern |
| is_only_w3 | week_specific_usage_pattern |
| active_ratio | usage_concentration |
| max_day_share | usage_concentration |
| day_count_over_3times | usage_concentration |
| reg_hour_afternoon | registration_timing_context |
| reg_hour_evening | registration_timing_context |
| reg_hour_morning | registration_timing_context |
| reg_hour_night | registration_timing_context |
| reg_is_weekend | registration_timing_context |
| historical_war_ratio | genre_preference |
| sf_fantasy_ratio | genre_preference |
| other_ratio | genre_preference |

---

## 17 Segmentation 지침

- 17 segmentation에서는 16b hotfix family mapping을 사용해야 한다.
- 17 segmentation에서 원래 technical_or_unknown bucket을 사용하면 안 된다.
- 연령/성별은 대표 세그먼트 규칙이 아니라 profile audit 및 action personalization layer로 사용한다.
- demographic action variant는 EDA 근거가 있을 때만 제안한다.

---

## 지속 유효한 caveat

- `is_churn_prevented`는 approved historical context feature with caveat로 유지한다.
- 07~10은 여전히 pending validation이다.

---

## Source Fingerprint Self-Reference Caveat

`16b_source_fingerprint_before_after.csv`에서 다음 두 파일이 `changed_needs_review`로 남았다.

- `16b_source_fingerprint_before_after.csv` (자기참조: fingerprint가 자신의 hash를 기록할 때 발생하는 self-reference loop)
- `PUBLIC_16b_feature_family_mapping_hotfix_zip_inventory.csv` (패키징 metadata self-reference: inventory가 자신을 포함한 zip을 기술)

이 두 파일은 원천 데이터, 기존 16 core SHAP 산출물, 16b mapping 결과가 아니다. 패키징 과정에서 갱신되는 handoff metadata 파일이다. 분석 결과 변경으로 해석하지 않는다.

모든 core SHAP CSV와 16b output CSV는 fingerprint에서 `unchanged`로 확인되었다.

다음 작업부터는 source fingerprint 생성 순서와 zip inventory 생성 순서를 분리해 self-reference limitation을 명시적으로 기록해야 한다.

---

## 다음 단계

사용자가 17 segmentation 설계 또는 demographic EDA 선행 여부를 결정한다.

- **17 segmentation 선행**: 16b hotfix family mapping을 기반으로 세그먼트 설계 시작
- **demographic EDA 선행**: 연령/성별 분포와 이탈 패턴 간 관계를 먼저 탐색한 뒤 action personalization layer 확정
