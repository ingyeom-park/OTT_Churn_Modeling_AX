> model and score source summary

> 12x model comparison 요약

12x는 model family comparison reference다. 상위 OOF AUC 후보는 다음과 같다.

```text
    feature_set_name     dataset_scope           model_name  oof_auc  row_count  feature_count
expanded_feature_set nonpromotion_only             LightGBM 0.883833      11175             79
expanded_feature_set nonpromotion_only HistGradientBoosting 0.882967      11175             79
expanded_feature_set nonpromotion_only             CatBoost 0.878657      11175             79
expanded_feature_set nonpromotion_only              XGBoost 0.878486      11175             79
expanded_feature_set nonpromotion_only     GradientBoosting 0.878323      11175             79
```

이 비교는 final campaign model 확정이 아니라 고정 파라미터 기반 model family comparison이다.

> CatBoost가 강했지만 final score source가 아닌 이유

CatBoost는 일부 scope에서 강한 후보로 기록되어 있다. 그러나 17x의 score source는 15x `expanded_no_payment_device / overall_with_promotion / LightGBM` OOF score로 고정되어 있다. 16x SHAP candidate plan도 overall_with_promotion에서 LightGBM을 explanation basis로 사용한다. 따라서 CatBoost 성능이 좋았다는 사실만으로 17x segmentation score source를 바꾸지 않는다.

> LightGBM을 쓴 이유

17x는 `17x_score_source_selection.csv`에서 LightGBM OOF score를 primary로 선택했다. 선택 조건은 feature_set_variant `expanded_no_payment_device`, dataset_scope `overall_with_promotion`, model_name `LightGBM`, row_count 23,079이다. 이 기준은 payment-device 제거와 16x explanation basis를 맞추기 위한 것이다.

> PUBLIC GB를 final로 쓰지 않는 이유

PUBLIC GB는 PUBLIC reference branch의 산출물이다. PUBLIC은 100원딜 중심 narrative와 visual guide 구조를 참고하는 branch이지, park.ingyeom final score source를 대체하지 않는다. guide v3에서는 PUBLIC numeric score를 FINAL 기준으로 병합하지 않는다.

> OOF churn_risk의 뜻

OOF는 out-of-fold prediction이다. 각 row가 자기 fold의 학습에 직접 쓰이지 않은 상태에서 받은 `repurchase_score`를 기준으로 `churn_risk = 1 - repurchase_score`를 계산한다. 이는 segmentation ranking에 쓰는 score source이지 확정 campaign threshold가 아니다.

> 제한

이 score source는 final model 확정이 아니다. 17x segmentation score source이며, guide v3에서는 이 제한을 처음 등장하는 위치에서 반드시 설명해야 한다.

> evidence files

- `park.ingyeom\reports\models\12x_model_family_comparison_260516\12x_model_summary_by_scope.csv`
- `park.ingyeom\reports\audits\15x_payment_device_sensitivity_260516\15x_model_summary_by_scope.csv`
- `park.ingyeom\reports\interpretation\16x_SHAP_candidate_interpretation_260516\16x_SHAP_candidate_plan.csv`
- `park.ingyeom\reports\segments\17x_segmentation_design_260516\17x_score_source_selection.csv`
