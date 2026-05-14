# 100원딜 OTT 이탈 분석 새 대화 인수인계

## 0. 읽는 순서

1. 이 handoff.md
2. note.md
3. canonical_outputs 폴더
4. docs 폴더의 문서가 있다면 보조로 확인

## 1. 프로젝트 목적

광일 v2 master를 기준으로 100원딜 프로모션 행과 비프로모션 행의 재구매/미재구매 신호를 비교하고, day21 이후 이탈 방어 전략 후보를 설계한다.

## 2. 절대 규칙

- 모든 작업과 산출물은 park.ingyeom 내부 기준으로 판단한다.
- 실행 작업 파일은 기본적으로 .ipynb이다.
- 분석 단위는 unique user가 아니라 row-level / subscription-event-level이다.
- USER_KEY는 group key 또는 식별 메타데이터이지 모델 feature가 아니다.
- target은 is_repurchase이고, is_repurchase=1은 재구매이다.
- repurchase_score = P(is_repurchase=1).
- churn_risk = 1 - repurchase_score.
- 4주차 또는 day21 이후 대응기간 행동은 feature로 쓰면 안 된다.
- SHAP은 원인이 아니라 model explanation이다.
- Referral은 현재 데이터에서 관측되지 않으므로 후속 실험 제안이다.

## 3. Canonical 상태

### Canonical
- 05b_column_role_dictionary_patch_260513
- 06_common_preprocessing_and_final_cohort_260513
- 09b_raw_view_window_validation_260514/run_20260514_130402
- 10_feature_eda_260513
- 11b_baseline_growth_history_ladder_fix_260514
- 11b_semantic_validation_and_interpretation_patch_260514
- 12_model_baseline_comparison_canonical_260514, 포함되어 있으면 canonical Step 12 후보

### Deprecated / Archive
- old Step 11: L2에 diff_between_w3_w2가 들어간 ladder contamination.
- old Step 12: AUC 중심 비교라 operating metrics 부족.
- old Step 12 rebuild / 12r: operating metrics는 추가했지만 stability-aware candidate 산정 로직 문제.
- archived old 12/12r은 최종 근거로 사용하지 않는다.

## 4. 주요 확정 수치

- raw master: 23,343 rows, 91 columns, missing 0.
- primary main cohort: 23,079 rows.
- duration < 21 excluded from main: 238 rows.
- additional full duplicate extra rows excluded after duration policy: 26 rows.
- conservative safe features: 22.
- main cohort nonpromotion rows: 11,175.
- main cohort promotion rows: 11,904.
- nonpromotion repurchase rate: 76.2416%.
- promotion repurchase rate: 67.5151%.
- 2x2:
  - nonpromotion_repurchase: 8,520.
  - nonpromotion_nonrepurchase: 2,655.
  - promotion_repurchase: 8,037.
  - promotion_nonrepurchase: 3,867.

## 5. 08~10 핵심 인사이트

- 08: promotion vs nonpromotion 평균 feature 차이는 negligible.
- 09: promotion x repurchase 2x2 내부 target difference가 더 강하다.
- 핵심 descriptive signal:
  - watch_time(min)_w3
  - watch_session_w3
  - is_only_w1
  - retention_w3_ratio
  - diff_between_w3_w1
  - diff_between_w3_w2
- 안전 해석:
  - 재구매 행은 미재구매 행보다 3주차 시청시간/세션이 높게 관찰되었다.
  - 1주차만 보고 이후 약해지는 패턴은 미재구매 쪽에서 더 강하게 관찰되었다.
  - 인과, p-value, 최종 모델 성능 주장은 아니다.

## 6. 09b raw view window validation

- raw View_History에는 day21+ view가 존재한다.
- day21+ view rows: 17,621.
- day21+ source rows: 6,044.
- day21+ watch_time sum: 767,791.
- 그러나 master core usage 8개 feature는 raw day0~20 재계산값과 mismatch 0이다.
- day21+를 포함하면 mismatch가 발생한다.
- 따라서 core usage feature 기준으로는 day0~20 관측창 전제가 강하게 지지된다.
- new_movie ratio exact formula는 unresolved.
- 일부 genre mismatch는 Movie_Master_v2의 MOVIE_NUM category 충돌 가능성.

## 7. 11b 상태

- old 11은 deprecated.
- 11b는 corrected canonical Step 11이다.
- 11b semantic patch에 따라 ladder는 temporal cutoff가 아니라 feature-family growth ladder이다.
- L1은 week1-only model이 아니다.
- L1은 early activation + early-only/front-loaded pattern family이다.
- is_only_w1, is_w1_over_50pct는 day21 기준 timing leakage는 아니지만 pure activation도 아니다.

## 8. 12 상태

- old 12와 12r은 archive/deprecated 처리했다.
- old 12는 AUC 중심이라 top-k/lift/calibration이 부족했다.
- 12r은 stability-aware candidate 산정 오류가 있었다.
- 현재 handoff zip에는 12_model_baseline_comparison_canonical_260514가 포함되어 있다.
- 따라서 새 대화에서는 12c를 canonical Step 12로 우선 검토한다.
- 단, 새 대화는 반드시 12c_final_checks.csv, 12c_candidate_selection_by_scope.csv, 12c_operating_metrics_at_k.csv, 12c_stability_aware_candidate_by_scope.csv를 열어 검수한 뒤 12c를 최종 기준으로 확정해야 한다.

## 9. 금지 주장

- 100원딜 때문에 이탈했다.
- 프로모션이 재구매율 감소를 유발했다.
- AUC가 높으니 마케팅 효과가 입증됐다.
- churn_risk top10%를 바로 캠페인 타겟으로 삼으면 된다.
- SHAP이 원인을 밝혔다.
- Referral 성과를 분석했다.
- unique user 분석이다.

## 10. 새 대화의 첫 할 일

1. canonical_outputs에 12_model_baseline_comparison_canonical_260514가 있는지 확인한다.
2. 있으면 12c를 canonical Step 12로 검수한다.
3. 없으면 12c부터 마무리한다.
4. 멘토 보고용으로는 canonical / deprecated / open risk를 분리해서 요약한다.

