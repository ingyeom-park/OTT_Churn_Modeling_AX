# 06 current model notebook prep memo

# 작업 목적

기존 retention을 제거하고 log retention만 사용한 모델 입력 CSV를 만들고, 사용자가 수동 실행할 4개 모델 노트북을 준비했다.

# 사용자 결정

사용자 결정으로 feature set은 current로 고정되었다. feature set 논의는 종료되었고, 기존 `retention_w2_ratio`, `retention_w3_ratio`는 모델 입력에서 삭제한다.

# 입력 데이터

- promo_0: rows=11193, cols=84
- promo_1: rows=11904, cols=84

# retention 검수

- `retention_w2_ratio`는 모델 입력 CSV에 없다.
- `retention_w3_ratio`는 모델 입력 CSV에 없다.
- `log_retention_w2_ratio`는 모델 입력 CSV에 있다.
- `log_retention_w3_ratio`는 모델 입력 CSV에 있다.

# 생성한 모델 입력 CSV

- `PUBLIC/data/06_model_input_promo_0.csv`
- `PUBLIC/data/06_model_input_promo_1.csv`

# 생성한 노트북

- `PUBLIC/notebooks/06_gb_promo0.ipynb`
- `PUBLIC/notebooks/06_gb_promo1.ipynb`
- `PUBLIC/notebooks/06_lr_promo0.ipynb`
- `PUBLIC/notebooks/06_lr_promo1.ipynb`

# Optuna 설정

`N_TRIALS = 100`으로 고정했다. 200 trials는 사용하지 않는다.

# 실행 상태

이번 goal에서는 모델을 실행하지 않았다. `final_result.csv`, `trials_all.csv`는 아직 생성되지 않은 것이 정상이다.

# 하지 않은 것

- 모델 실행 안 함
- row-level OOF score table 생성 안 함
- SHAP 생성 안 함
- segmentation 생성 안 함
- HTML 수정 안 함
- 기존 결과 삭제 안 함

# 다음 단계

사용자가 4개 노트북을 팀원들과 나눠 실행한다. 실행 후 결과 폴더 4개를 ZIP으로 묶어 assistant에게 전달한다. assistant는 결과 ZIP을 실제로 열어 형식 검수와 의미 검수를 분리해 검수한다.

# 미해결 리스크

- USER_KEY 중복에 따른 group leakage caveat
- 기존 결과와 새 log-only 결과의 feature set 차이
- 실행은 아직 수행되지 않았으므로 성능/overfit 판단 불가
- OOF 생성 전 사용자 승인 필요
