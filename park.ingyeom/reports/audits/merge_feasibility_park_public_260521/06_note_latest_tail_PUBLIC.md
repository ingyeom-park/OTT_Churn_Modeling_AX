segmentation은 사용자 검수 후 별도 goal로 진행한다.

SHAP 계산 fallback은 핵심 산출물 기준으로 발생하지 않았다.



## 2026-05-20 | PUBLIC 16b feature family mapping hotfix completed

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

---

## 2026-05-20 | PUBLIC 16b feature family mapping hotfix accepted after review

16b feature family mapping hotfix review package를 검수한 결과, 핵심 mapping 보정은 통과 가능하다고 판단했다.

기존 technical_or_unknown 16개 feature가 모두 재분류되었다.

technical_or_unknown 잔여 feature는 0개다.

recency와 max_inactive_gap_days는 inactivity_recency로 재분류되었다.

is_only_w1, is_only_w2, is_only_w3는 week_specific_usage_pattern으로 재분류되었다.

active_ratio, max_day_share, day_count_over_3times는 usage_concentration으로 재분류되었다.

reg_hour_*와 reg_is_weekend는 registration_timing_context로 재분류되었다.

historical_war_ratio, sf_fantasy_ratio, other_ratio는 genre_preference로 재분류되었다.

기존 SHAP 값은 재계산하지 않았고, family mapping과 family-level 집계만 보정했다.

17 segmentation에서는 원래 technical_or_unknown bucket이 아니라 16b hotfix family mapping을 사용해야 한다.

16b_source_fingerprint_before_after.csv에서 자기참조성 있는 handoff/fingerprint/zip_inventory 파일 2개가 changed_needs_review로 남았지만, 이는 패키징 과정의 metadata self-reference 문제로 해석한다.

원천 데이터, 기존 16 core SHAP 산출물, 16b 핵심 output이 변경된 문제로 보지 않는다.

다음 작업부터 source fingerprint와 zip inventory의 self-reference limitation을 명시적으로 기록해야 한다.

연령/성별은 대표 세그먼트 규칙이 아니라 profile audit 및 action personalization layer로 사용한다.

demographic action variant는 EDA 근거가 있을 때만 제안한다.

is_churn_prevented는 approved historical context feature with caveat로 유지한다.

07~10은 여전히 pending validation이다.

다음 단계는 17 segmentation 설계 또는 demographic EDA 선행 여부를 사용자가 결정하는 것이다.


## 2026-05-20 | PUBLIC 17 promo-scope OOF behavior segmentation design completed

이번 작업은 PUBLIC 17 segmentation design 단계다.

15 OOF hotfix, 16 SHAP, 16b feature family mapping hotfix를 입력으로 사용했다.

promo1은 100원딜 고객 중심 scope이며, promo0는 비교군이다.

세그먼트는 OOF risk score와 행동 flag를 결합해 provisional로 설계했다.

16b hotfix family mapping을 사용했고, 기존 technical_or_unknown bucket은 사용하지 않았다.

연령/성별은 대표 세그먼트의 1차 기준이 아니라 demographic profile 및 action personalization layer로 사용했다.

demographic action variant는 EDA에서 분포 차이가 확인되는 경우에만 제안한다.

segment name은 final이 아니며 사용자 승인 전까지 provisional이다.

OOF score는 final campaign threshold가 아니다.

SHAP은 인과가 아니라 model explanation이다.

is_churn_prevented는 approved historical context feature with caveat로 유지했다.

07~10은 여전히 pending validation이다.

이번 작업에서는 모델 재실행, Optuna, SHAP 재계산, OOF 재생성, campaign threshold 확정을 수행하지 않았다.

`17_segment_rationale_memo_for_executives.md`를 작성해 세그먼트를 왜 이렇게 나누었는지 데이터와 비즈니스 근거를 길게 설명했다.

다음 단계는 사용자가 17 review zip을 검수한 뒤, 18 business storyline 또는 segment hotfix 여부를 결정하는 것이다.


## 2026-05-20 | PUBLIC 17 segmentation semantic hotfix completed

이번 작업은 17 segmentation semantic hotfix다.

기존 17 산출물은 row count, score direction, assignment rule은 맞았지만, content_preference_signal이 지나치게 broad하게 생성되어 segment-discriminating signal로 쓰기 위험했다.

content_preference_signal은 representative rule에서 제거 또는 강등하고, broad content-context marker 또는 action personalization 참고 변수로만 사용하도록 보정했다.

genre/content narrow 계열 segment는 genre_preference_clear 중심으로 재해석했다.

other_needs_review 비중이 큰 점을 숨기지 않고 caveat로 기록했다.

representative segment assignment와 summary를 hotfix rule 기준으로 다시 계산했다.

executive rationale memo를 임원 설득용으로 대폭 확장했다.

연령/성별은 대표 segment rule이 아니라 profile audit 및 action personalization layer로 유지했다.

SHAP은 인과가 아니라 model explanation이다.

OOF score는 final campaign threshold가 아니다.

segment label은 provisional이다.

07~10은 여전히 pending validation이다.

이번 작업에서는 모델 재실행, OOF 재생성, SHAP 재계산, Optuna, final campaign targeting을 수행하지 않았다.

다음 단계는 사용자가 17 hotfix review zip을 검수한 뒤 18 business storyline으로 갈지, 추가 segment 보정을 할지 결정하는 것이다.

## 2026-05-20 | PUBLIC 17 segmentation quality hotfix completed

- 이번 작업은 17 segmentation quality hotfix다.
- 기존 17 산출물은 row count, score direction, assignment rule 측면에서는 맞았지만, content_preference_signal broad flag, small segment, other_needs_review 비중 문제 때문에 의미 검수 hotfix가 필요했다.
- content_preference_signal은 representative rule에서 강등하고, broad content-context marker 또는 action cue로만 둔다.
- 대표 세그먼트는 최소 규모 기준을 적용한다.
- n < 300인 small segment는 기본적으로 대표 segment에서 강등하고, sub-signal/profile note/action cue로 보존한다.
- other_needs_review는 단순 중위험군이 아니라 기존 rule로 설명되지 않은 잔여군으로 정의하고, risk band와 행동 flag 기준으로 decomposition했다.
- promo1과 promo0의 같은 행동 패턴을 비교해, 공통 위험 신호인지 100원딜 고객에서 더 강하게 나타나는 신호인지 구분했다.
- revised representative segment proposal과 assignment simulation을 만들었지만, user approval 전까지 final assignment가 아니다.
- 연령/성별은 대표 rule이 아니라 action personalization layer다.
- demographic action은 EDA 근거가 있을 때만 제안한다.
- OOF score는 campaign threshold가 아니다.
- SHAP은 인과가 아니다.
- 07~10은 여전히 pending validation이다.
- 다음 단계는 사용자가 quality hotfix review zip을 검수한 뒤, revised segment proposal을 승인할지, 추가 hotfix를 할지, 18 business storyline으로 갈지 결정하는 것이다.

## 2026-05-20 | PUBLIC 17 demographic action layer hotfix completed

- 이번 작업은 17 quality hotfix 이후 demographic/action personalization layer를 복구하기 위한 hotfix다.
- 기존 revised segment assignment는 변경하지 않았다.
- age_group profile을 다시 생성했다.
- is_female/is_male 기준 gender derivation을 다시 점검했다.
- segment별 age_group behavior profile을 생성했다.
- segment별 gender behavior profile을 생성했다.
- action personalization matrix를 demographic hotfix 기준으로 다시 만들었다.
- 연령/성별은 대표 segment rule의 1차 기준이 아니라 profile audit 및 action personalization layer로만 사용한다.
- demographic action variant는 EDA에서 실제 분포 차이와 행동 차이가 확인될 때만 제안한다.
- 연령/성별을 이탈 원인으로 해석하지 않는다.
- 18 business storyline은 사용자 검수 후 진행한다.
- 이번 작업에서는 대표 segment 재배정, 모델 재실행, OOF 재생성, SHAP 재계산, Optuna, campaign threshold 확정을 수행하지 않았다.
- 07~10은 여전히 pending validation이다.

## 2026-05-20 | PUBLIC 18 business storyline and segment visual guide v2 completed

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

---

## 2026-05-20 | PUBLIC 18 Business Storyline Polish Hotfix

### 수행 내용

기존 `18_business_recommendation_storyline_260520` 산출물의 품질 문제를 발견하고, 발표 수준으로 정제하는 hotfix를 수행했다. 모델 재실행, OOF 재생성, SHAP 재계산, segment assignment 변경은 수행하지 않았다.

### 발견된 주요 문제 (audit 결과)

1. demographic action candidate 60개 all `include_in_storyline=yes` — 과도하게 낙관적; 동일 age_group 중복 등장
2. promo0 action matrix에서 `final_status=provisional_business_candidate` — promo0는 comparison_reference여야 함
3. `genre_or_content_action_cue` (n=11 promo1, n=5 promo0)가 main storyline에 포함 — n<300 기준 미달
4. `mid_risk_retention_watchlist`가 storyline comparison에서 누락 (n=1,309; delta +18.4%p로 최대)
5. HTML visual guide에 flag dictionary, segment KPI cards, safe/unsafe wording, demographic layer 없음

### 생성 산출물 (모두 신규 파일, 기존 파일 수정 없음)

**출력 디렉터리:** `PUBLIC/reports/business/18_business_recommendation_storyline_hotfix_260520/`

| 파일 | 설명 |
|---|---|
| 18_existing_storyline_quality_audit.csv | 14개 audit 항목 (blocking 1, major 8, minor 3, pass 2) |
| 18_promo1_main_business_action_matrix_hotfix.csv | promo1 5개 segment action matrix |
| 18_promo0_comparison_reference_hotfix.csv | promo0 비교 기준 5행 (action 없음) |
| 18_demographic_action_candidate_shortlist_hotfix.csv | 60행 → 16행 shortlist (promo1 yes:8, limited:2; comparison_only:6) |
| 18_storyline_comparison_clean_hotfix.csv | genre demoted + mid_risk 추가 (6행) |
| 18_segment_visual_guide_v2_polished.html | 종합 HTML (flag dict, segment cards, safe/unsafe, demo layer) |
| 18_business_storyline_memo_hotfix.md | 10,000자+ 한국어 상세 메모 |
| 18_presentation_talking_points_hotfix.md | 8개 Q&A + 방어 문장 + 금지 표현 |
| 18_dashboard_handoff_datamart_hotfix.csv | 10행 (promo1×5 + promo0×5) |
| 18_safe_unsafe_wording_hotfix.csv | 14개 wording 가이드 |
| README.md | hotfix 전체 요약 |

**Handoff 디렉터리:** `PUBLIC/handoff/PUBLIC_18_business_storyline_polish_hotfix_260520/`

- 18_hotfix_input_validation.csv (30개 입력 파일 전체 PASS)
- final_checks, source_fingerprint, zip_inventory, README

### 핵심 수치 확인 (변경 없음)

- promo1 high_risk_week3: n=1893, churn=0.7427, gb_risk=0.7399
- promo1 high_risk_activation: n=370, churn=0.7838, gb_risk=0.7317
- promo1 mid_risk_watchlist: n=1309, churn=0.6012, gb_risk=0.5276
- promo1 stable: n=1999, churn=0.1196, gb_risk=0.1341
- promo1 other_residual: n=6333, churn=0.1808, gb_risk=0.1941

### 주의사항

- 모든 segment는 provisional이다
- OOF score는 campaign threshold가 아니다
- SHAP은 인과가 아니다
- demographic은 personalization layer이며 이탈 원인이 아니다
- 07~10 validation은 여전히 pending이다
- other residual (53.2%)은 중위험군이 아님을 반드시 명시해야 한다
- genre_or_content_action_cue (n=11)는 main storyline에서 강등 완료

### 다음 단계

1. 팀 검토: segment label, demographic shortlist, safe/unsafe wording
2. Visual guide 검토 및 발표 자료 적용
3. 07~10 validation 진행
4. other_needs_review_residual 내부 decomposition 분석 (별도 단계)
5. threshold 설정 및 A/B test 설계 (별도 단계)
