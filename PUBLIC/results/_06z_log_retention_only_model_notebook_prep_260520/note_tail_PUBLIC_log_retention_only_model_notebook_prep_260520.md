
# 미해결 리스크

- final_checks PASS는 형식 검수 PASS이며, 의미 검수 PASS가 아닙니다.
- 일부 PR-AUC 계열 train/valid metric은 final_result에 없어서 비교표에서 missing으로 남겼습니다.
- 후보 모델은 자동 확정이 아니라 사용자 승인 전 preflight 후보입니다.

<!-- PUBLIC_MODEL_AUDIT_260520_END -->


> 주의: 아래 `PUBLIC overfit-adjusted model selection` 기록은 기존 8개 모델 결과 기준으로 CatBoost를 조건부 후보로 둔 중간 판단이다.  
> 이후 보수형 CatBoost 및 보수형 GradientBoosting 추가 실행 결과, 최신 1차 추천 후보는 GradientBoosting conservative로 이동했다.  
> 아래 기록은 연대기적 중간 판단으로 보존하되, 최신 작업 기준으로 직접 사용하지 않는다.

<!-- PUBLIC_MODEL_SELECTION_OVERFIT_260520_START -->

> 2026-05-20 PUBLIC overfit-adjusted model selection

# 작업일

2026-05-20

# 작업명

PUBLIC overfit-adjusted model selection

# 작업 목적

`PUBLIC/results`의 8개 모델 결과를 다시 읽고, 기존 성능 지표에 trial-level overfit 비율을 반영해 promo1/promo0별 score source 후보를 다시 정리했습니다.

# 입력으로 확인한 results 폴더

- results

# 확인한 final_result.csv 개수

8

# 확인한 trials_all.csv 개수

8

# 8개 모델 overfit_rate 요약

- promo0 CatBoost: overfit_rate=86.5%, risk=severe_overfit_pool, top5=100.0%, top10=100.0%, top20=100.0%
- promo0 LogisticRegression: overfit_rate=0.0%, risk=low_overfit_pool, top5=0.0%, top10=0.0%, top20=0.0%
- promo0 RandomForest: overfit_rate=97.5%, risk=severe_overfit_pool, top5=100.0%, top10=100.0%, top20=100.0%
- promo0 SVM: overfit_rate=27.5%, risk=mild_overfit_pool, top5=0.0%, top10=0.0%, top20=0.0%
- promo1 CatBoost: overfit_rate=90.0%, risk=severe_overfit_pool, top5=100.0%, top10=100.0%, top20=100.0%
- promo1 LogisticRegression: overfit_rate=0.0%, risk=low_overfit_pool, top5=0.0%, top10=0.0%, top20=0.0%
- promo1 RandomForest: overfit_rate=98.0%, risk=severe_overfit_pool, top5=100.0%, top10=100.0%, top20=100.0%
- promo1 SVM: overfit_rate=28.5%, risk=mild_overfit_pool, top5=0.0%, top10=0.0%, top20=5.0%

# CatBoost promo0/promo1 overfit 비율

- CatBoost promo0: 86.5%
- CatBoost promo1: 90.0%

# 기존 판단과 달라진 점

이전 판단은 성능 지표 중심이었고, 이번 판단은 `trials_all.csv` 전체의 overfit pool risk를 함께 반영했습니다. CatBoost는 성능상 강하지만 사용자 승인 전까지 조건부 후보로 둡니다.

# promo1 모델 후보

- 1순위 조건부 후보: CatBoost
- recommendation: conditional_recommended_after_user_approval
- 사용자 승인 필요

# promo0 모델 후보

- 1순위 조건부 후보: CatBoost
- recommendation: conditional_recommended_after_user_approval
- 사용자 승인 필요

# backup candidate

- promo1 backup: SVM
- promo0 backup: SVM

# baseline candidate

- promo1 baseline: LogisticRegression
- promo0 baseline: LogisticRegression

# 아직 확정하지 않은 것

- 최종 모델 확정 안 함
- promo1 score source 확정 안 함
- promo0 score source 확정 안 함
- row-level OOF score table 생성 방식 확정 안 함
- SHAP 기준 모델 확정 안 함
- segmentation 기준 score 확정 안 함

# 다음 단계: row-level OOF score table 생성

사용자 승인 이후, 선택된 모델 후보 기준으로 row-level OOF score table을 생성합니다.

# 이번 단계에서 하지 않은 것

- row-level score table 생성 안 함
- OOF score 생성 안 함
- SHAP 생성 안 함
- segmentation 생성 안 함
- HTML 수정 안 함

# 미해결 리스크

- score source 후보는 최종 확정이 아니라 사용자 승인 전 조건부 후보입니다.
- overfit_risk_level은 preflight heuristic입니다.
- final_result와 trials_all은 파싱되었지만, score table은 아직 생성하지 않았습니다.

# 생성한 산출물

- model_selection_overfit_260520/PUBLIC_model_selection_input_inventory.csv
- model_selection_overfit_260520/PUBLIC_final_result_metrics_reparsed.csv
- model_selection_overfit_260520/PUBLIC_trial_level_overfit_summary.csv
- model_selection_overfit_260520/PUBLIC_overfit_adjusted_model_selection.csv
- model_selection_overfit_260520/PUBLIC_overfit_adjusted_model_selection_memo.md
- model_selection_overfit_260520/PUBLIC_model_selection_overfit_final_checks.csv
- model_selection_overfit_260520/PUBLIC_model_selection_overfit_review_zip_inventory.csv
- model_selection_overfit_260520/note_tail_PUBLIC_model_selection_overfit_260520.md
- zip/PUBLIC_model_selection_overfit_260520_review_package.zip

<!-- PUBLIC_MODEL_SELECTION_OVERFIT_260520_END -->


## 2026-05-15 06x_cold_start_rowlevel_hotfix_260515
- 06x cold_start row-level hotfix 수행.
- USER_KEY 단위 first watch 방식이 아니라 master_row_id/subscription-event row 기준으로 재계산함.
- raw 기준 변경 수 1802 / 985.
- primary cohort 기준 변경 수 1786 / 969.
- negative first_watch_rel_day 0건.
- conservative/expanded dataset은 23097 rows 유지.
- 새로 생성된 feature는 기존 승인된 3개뿐임: is_basic, is_cold_start_3d_fixed, is_cold_start_7d_fixed.
- 다음 단계는 07x.


## 2026-05-20 06y_promo_split_260520
- PUBLIC 06x expanded dataset을 `is_promotion` 기준으로 분할함.
- source rows: 23097.
- promo_0 rows: 11193.
- promo_1 rows: 11904.
- unexpected is_promotion rows: 0.
- outputs: PUBLIC/results/_06y_promo_split_260520.


---

## 2026-05-20 | PUBLIC_log_retention_only_model_notebook_prep_260520

- 사용자 결정으로 feature set은 log retention only로 고정됨.
- 기존 `retention_w2_ratio`, `retention_w3_ratio`는 모델 입력 CSV에서 제거함.
- `log_retention_w2_ratio`, `log_retention_w3_ratio`는 모델 입력 CSV에 유지함.
- 사용한 입력 데이터:
  - `PUBLIC/data/06z_expanded_dataset_promo_0_log_retention.csv`
  - `PUBLIC/data/06z_expanded_dataset_promo_1_log_retention.csv`
- 생성한 모델 입력 CSV:
  - `PUBLIC/data/06z_model_input_promo_0_log_retention_only.csv`
  - `PUBLIC/data/06z_model_input_promo_1_log_retention_only.csv`
- promo0 row 수: 11193
- promo1 row 수: 11904
- 생성한 노트북:
  - `PUBLIC/notebooks/06z_gb_promo0_logretention_only.ipynb`
  - `PUBLIC/notebooks/06z_gb_promo1_logretention_only.ipynb`
  - `PUBLIC/notebooks/06z_lr_promo0_logretention_only.ipynb`
  - `PUBLIC/notebooks/06z_lr_promo1_logretention_only.ipynb`
- Optuna는 `N_TRIALS=100`으로 고정함.
- 예정 OUT_DIR:
  - `PUBLIC/results/_06z_log_retention_only_model_rerun_260520/gb_promo0`
  - `PUBLIC/results/_06z_log_retention_only_model_rerun_260520/gb_promo1`
  - `PUBLIC/results/_06z_log_retention_only_model_rerun_260520/lr_promo0`
  - `PUBLIC/results/_06z_log_retention_only_model_rerun_260520/lr_promo1`
- 이번 goal에서는 모델을 실행하지 않음.
- `final_result.csv`, `trials_all.csv`는 아직 생성되지 않는 것이 정상임.
- 사용자와 팀원이 다음 단계에서 4개 노트북을 수동 실행할 예정임.
- 하지 않은 것: 모델 실행, OOF score table 생성, SHAP 생성, segmentation 생성, HTML 수정, 기존 결과 삭제.
- 미해결 리스크: USER_KEY 중복에 따른 group leakage caveat, 기존 결과와 log-only 결과의 feature set 차이, 실행 전이므로 성능/overfit 판단 불가.
- 다음 단계: 사용자가 4개 노트북을 실행한 뒤 결과 ZIP을 전달하면 assistant가 형식 검수와 의미 검수를 분리해 검수한다.
- canonical update: feature set은 log retention only로 고정됨. 기존 retention은 모델 입력에서 제거됨. 기존 09/10/07/08 결과는 reference로 유지됨.
- 구조 보정: `11/12/13/14`는 독립 pipeline step처럼 보이므로 사용하지 않는다. 이번 작업은 `06z log retention only` 계열의 모델 variant 준비 작업이며, 모델별 결과는 `_06z_log_retention_only_model_rerun_260520` 하위 폴더에 둔다.
