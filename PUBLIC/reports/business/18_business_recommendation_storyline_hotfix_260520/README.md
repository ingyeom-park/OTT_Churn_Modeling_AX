# 18 Business Recommendation Storyline — Polish Hotfix

**작성일:** 2026-05-20  
**버전:** hotfix  
**상태:** 완료 (모델 재실행 없음, 기존 segment assignment 변경 없음)

---

## 목적

기존 `18_business_recommendation_storyline_260520` 산출물의 품질 문제를 발견하고 발표 수준으로 정제하는 hotfix 작업.

---

## 왜 Hotfix가 필요했는가

1. **60개 all-yes demographic candidate**: 60개 행 전부 `include_in_storyline=yes`로 표시 — 과도하게 낙관적이며 동일 age_group이 중복 등장
2. **promo0 action matrix 혼동**: promo0 행이 `segment_role=promo0_comparison_scope`이면서 `final_status=provisional_business_candidate` — promo0 should be comparison_reference only
3. **Small-n signal in main storyline**: `genre_or_content_action_cue` (n=11 promo1, n=5 promo0)가 main comparison에 포함 — n<300 기준 미달
4. **mid_risk 누락**: `mid_risk_retention_watchlist`가 storyline comparison에서 누락 — n=1,309에 delta +18.4%p로 가장 중요한 비교 포인트
5. **HTML 미흡**: flag dictionary, segment cards with KPI, promo0 comparison, safe/unsafe wording, demographic layer 모두 없음

---

## 무엇을 변경했는가

| 항목 | 기존 | Hotfix |
|---|---|---|
| demographic candidate | 60행 all-yes | 16행 shortlist (promo1 yes:8 / limited:2 / comparison_only:6) |
| promo0 action matrix | provisional_business_candidate와 동일 | 별도 comparison_reference 파일로 분리 |
| storyline comparison | genre_or_content_action_cue 포함, mid_risk 누락 | genre demoted, mid_risk 추가, 6행으로 정리 |
| HTML visual guide | 요약 수준 | 종합 가이드 (flag dict, segment cards, wording, demo layer) |
| memo | 기본 서술 | 10,000자+ 상세 한국어 서술 |
| talking points | 기본 Q&A 7개 | 8개 Q&A + 심사위원 방어 + 절대 금지 문장 추가 |

---

## 무엇을 보존했는가

- 모든 모델 재실행 없음
- OOF score, SHAP 값 변경 없음
- segment assignment 재실행 없음
- canonical segment set (n, churn rate, GB risk) 변경 없음
- 기존 18 원본 파일 그대로 보존

---

## Promo1 Main Scope (행동 기반 5개 family)

| Segment | n | Churn | GB Risk | Priority |
|---|---|---|---|---|
| high_risk_week3_inactivity_or_retention_decay | 1,893 | 74.3% | 0.740 | 1 — 최우선 |
| high_risk_activation_or_low_engagement | 370 | 78.4% | 0.732 | 2 — 조기 개입 |
| mid_risk_retention_watchlist | 1,309 | 60.1% | 0.528 | 3 — 관찰군 |
| stable_usage_lower_risk | 1,999 | 12.0% | 0.134 | 4 — 유지/업셀 |
| other_needs_review_residual | 6,333 | 18.1% | 0.194 | RESIDUAL |

---

## Promo0 Comparison Scope (비교 reference only)

| Segment | n | Churn | Delta vs promo1 |
|---|---|---|---|
| high_risk_week3 | 1,890 | 68.0% | +6.2%p |
| high_risk_activation | 273 (subsignal) | 75.1% | +3.3%p |
| mid_risk_watchlist | 1,195 | 41.7% | +18.4%p (최대) |
| stable_lower_risk | 1,966 | 6.8% | +5.2%p |
| other_residual | 5,869 | 9.1% | +9.0%p |

promo0에 대한 별도 action 제안 없음.

---

## Demographic Action Shortlist

- 원본 60행 → hotfix 16행으로 축소
- promo1 include_in_storyline=yes: 8개
- promo1 include_in_storyline=limited: 2개
- promo0 comparison_only: 6개 (storyline 제외)

연령/성별은 이탈 원인이 아니라 action personalization layer임을 반드시 명시.

---

## Small Signal Cleanup

- `genre_or_content_action_cue`: n=11(promo1), n=5(promo0) → main storyline에서 제외, profile/action cue로 강등
- 기준: main comparison 최소 n=300
- 제거가 아닌 강등: 데이터 보존, 역할 재정의

---

## Visual Guide Polish

`18_segment_visual_guide_v2_polished.html`에 다음 추가:
- Flag dictionary (7개 flag 정의)
- Segment cards with full KPI boxes (promo0 comparison 포함)
- Safe/Unsafe wording per segment
- Demographic action layer 설명
- 100원딜 narrative 강화 (lifecycle timing)
- Score source 설명 (GB OOF primary)
- promo0 비교 기준 섹션 명확화

---

## What Was NOT Done (재실행 없음)

- 모델 재실행 없음
- OOF score 재산출 없음
- SHAP 재실행 없음
- Segment assignment 변경 없음
- 원본 18 파일 수정 없음

---

## 07~10 Pending Validation

현재 모든 segment와 action candidate는 provisional이다. 07~10 validation이 완료될 때까지 어떠한 segment name도 확정 확정으로 사용하지 않는다.

---

## Next Action

1. 팀 검토: segment label, demographic shortlist, safe/unsafe wording 검토
2. Visual guide 검토 및 발표 자료 적용
3. 07~10 validation 진행
4. threshold 설정 및 A/B test 설계 (별도 단계)
5. other_needs_review_residual 내부 decomposition 분석

---

## 산출물 목록

| 파일명 | 설명 |
|---|---|
| 18_existing_storyline_quality_audit.csv | 기존 산출물 품질 감사 결과 (14개 항목) |
| 18_promo1_main_business_action_matrix_hotfix.csv | promo1 전용 action matrix (5행) |
| 18_promo0_comparison_reference_hotfix.csv | promo0 비교 기준 (5행, action 없음) |
| 18_demographic_action_candidate_shortlist_hotfix.csv | demographic 후보 shortlist (16행) |
| 18_storyline_comparison_clean_hotfix.csv | storyline 비교 정제 (6행) |
| 18_segment_visual_guide_v2_polished.html | 종합 HTML 가이드 |
| 18_business_storyline_memo_hotfix.md | 상세 한국어 서술 메모 |
| 18_presentation_talking_points_hotfix.md | 발표 talking points (8개 Q&A) |
| 18_dashboard_handoff_datamart_hotfix.csv | 대시보드 handoff 데이터마트 (10행) |
| 18_safe_unsafe_wording_hotfix.csv | safe/unsafe wording 가이드 (14행) |
