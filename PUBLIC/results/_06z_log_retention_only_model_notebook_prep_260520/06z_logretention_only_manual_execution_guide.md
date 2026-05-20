# 06z log retention only manual execution guide

## 실행 대상 노트북

- `PUBLIC/notebooks/06z_gb_promo0_logretention_only.ipynb`
- `PUBLIC/notebooks/06z_gb_promo1_logretention_only.ipynb`
- `PUBLIC/notebooks/06z_lr_promo0_logretention_only.ipynb`
- `PUBLIC/notebooks/06z_lr_promo1_logretention_only.ipynb`

## 4명 분담 예시

- 1번 사람: `06z_gb_promo0_logretention_only.ipynb`
- 2번 사람: `06z_gb_promo1_logretention_only.ipynb`
- 3번 사람: `06z_lr_promo0_logretention_only.ipynb`
- 4번 사람: `06z_lr_promo1_logretention_only.ipynb`

## 각자 실행 전 확인

- repo 경로가 `C:\Code\ott-churn-prediction`인지 확인한다.
- `PUBLIC\data\06z_model_input_promo_0_log_retention_only.csv` 존재를 확인한다.
- `PUBLIC\data\06z_model_input_promo_1_log_retention_only.csv` 존재를 확인한다.
- 자기 담당 노트북의 `DATA` 경로를 확인한다.
- 자기 담당 노트북의 `OUT_DIR` 경로를 확인한다.
- `N_TRIALS = 100`인지 확인한다.

## 각자 실행 후 제출할 결과

각 OUT_DIR 안에 다음 두 파일이 있어야 한다.

- `final_result.csv`
- `trials_all.csv`

## 예상 결과 폴더

- `PUBLIC\results\_06z_log_retention_only_model_rerun_260520\gb_promo0`
- `PUBLIC\results\_06z_log_retention_only_model_rerun_260520\gb_promo1`
- `PUBLIC\results\_06z_log_retention_only_model_rerun_260520\lr_promo0`
- `PUBLIC\results\_06z_log_retention_only_model_rerun_260520\lr_promo1`

## 실행 후 결과 ZIP 명령어

다음 명령은 노트북 ZIP이 아니라 실행 결과 폴더 4개만 묶는 결과 ZIP 명령이다.

```powershell
Compress-Archive -LiteralPath `
  'PUBLIC\results\_06z_log_retention_only_model_rerun_260520\gb_promo0',`
  'PUBLIC\results\_06z_log_retention_only_model_rerun_260520\gb_promo1',`
  'PUBLIC\results\_06z_log_retention_only_model_rerun_260520\lr_promo0',`
  'PUBLIC\results\_06z_log_retention_only_model_rerun_260520\lr_promo1' `
  -DestinationPath 'PUBLIC\zip\PUBLIC_log_retention_only_model_execution_results_260520.zip' -Force
```

## 주의

- 기존 `PUBLIC/results` 결과 삭제 금지.
- 기존 01~10 결과 삭제 금지.
- 기존 노트북 수정 금지.
- 실행 중 에러가 나면 캡처 또는 로그를 보존한다.
- 결과 파일이 없으면 임의로 만들지 말고 실패로 기록한다.
