# 10_feature_eda_260513

This is step 10 only.

actual_output_folder: `C:\Code\ott-churn-prediction\park.ingyeom\reports\eda\10_feature_eda_260513`
actual_figure_folder: `C:\Code\ott-churn-prediction\park.ingyeom\reports\figures\10_feature_eda_260513`
detected_09b_output_folder: `C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\09b_raw_view_window_validation_260514\run_20260514_130402`
KOREAN_FONT_USED: `Malgun Gothic`

## Scope

- This is descriptive feature EDA only.
- No modeling was performed.
- No predictions were created.
- No repurchase_score or churn_risk was created.
- No SHAP was performed.
- No Optuna was performed.
- No statistical significance testing was performed.
- No p-values were created.
- No feature engineering for modeling was performed.
- No additional row exclusion was performed.
- Review columns were not used in standard conservative feature EDA.
- 09b core usage window validation passed and supports day0~20 core usage interpretation.
- 10 inspects distribution shape behind 09 SMD signals.
- Bins are exploratory EDA bins, not final segment thresholds.
- Next recommended step is 11_baseline_growth_history_260513, unless the team wants additional review-column resolution first.

## 시각화 해석 주의

- 모든 그림은 descriptive EDA용이다.
- p-value, 인과효과, 모델 성능을 의미하지 않는다.
- bin은 exploratory EDA bin이며 final segment threshold가 아니다.
- 막대 라벨의 퍼센트 denominator는 각 그림 설명에 따른다.
- Korean font warning: preferred Korean font found.

## CSV outputs

총 21개 CSV를 생성한다. README.md, note.md, ipynb, PNG figures는 CSV 개수에 포함하지 않는다.

## Figures

모든 PNG는 matplotlib only로 생성되며, figure inventory의 input_table은 실제 생성된 Step 10 CSV 파일명으로 연결된다.
