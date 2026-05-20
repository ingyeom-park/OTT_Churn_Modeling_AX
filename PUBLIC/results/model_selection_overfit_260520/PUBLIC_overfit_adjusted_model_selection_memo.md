# 작업 목적

이번 작업은 result 1~8의 성능 지표와 trial-level overfit 비율을 함께 고려해 promo1/promo0별 score source 후보를 다시 선정하는 단계입니다.

# 확인한 입력

- final_result.csv 개수: 8
- results/01_catboost_promo0/final_result.csv
- results/02_catboost_promo1/final_result.csv
- results/03_svm_promo0/final_result.csv
- results/04_svm_promo1/final_result.csv
- results/05_rf_promo0/final_result.csv
- results/06_rf_promo1/final_result.csv
- results/07_lr_promo0/final_result.csv
- results/08_lr_promo1/final_result.csv
- trials_all.csv 개수: 8
- results/01_catboost_promo0/trials_all.csv
- results/02_catboost_promo1/trials_all.csv
- results/03_svm_promo0/trials_all.csv
- results/04_svm_promo1/trials_all.csv
- results/05_rf_promo0/trials_all.csv
- results/06_rf_promo1/trials_all.csv
- results/07_lr_promo0/trials_all.csv
- results/08_lr_promo1/trials_all.csv

# 기존 판단의 한계

이전 audit에서는 CatBoost가 성능상 1차 후보였지만, trial-level overfit 비율을 충분히 반영하지 못했습니다. 이번 재선정은 final_result의 test 성능뿐 아니라 `trials_all.csv` 전체의 overfit pool risk, top5/top10/top20 overfit 비율, best non-overfit trial의 성능 손실을 함께 봅니다.

# overfit 비율 요약

- promo0 CatBoost: overfit_rate=86.5%, risk=severe_overfit_pool, top5=100.0%, top10=100.0%, top20=100.0%
- promo0 LogisticRegression: overfit_rate=0.0%, risk=low_overfit_pool, top5=0.0%, top10=0.0%, top20=0.0%
- promo0 RandomForest: overfit_rate=97.5%, risk=severe_overfit_pool, top5=100.0%, top10=100.0%, top20=100.0%
- promo0 SVM: overfit_rate=27.5%, risk=mild_overfit_pool, top5=0.0%, top10=0.0%, top20=0.0%
- promo1 CatBoost: overfit_rate=90.0%, risk=severe_overfit_pool, top5=100.0%, top10=100.0%, top20=100.0%
- promo1 LogisticRegression: overfit_rate=0.0%, risk=low_overfit_pool, top5=0.0%, top10=0.0%, top20=0.0%
- promo1 RandomForest: overfit_rate=98.0%, risk=severe_overfit_pool, top5=100.0%, top10=100.0%, top20=100.0%
- promo1 SVM: overfit_rate=28.5%, risk=mild_overfit_pool, top5=0.0%, top10=0.0%, top20=5.0%

CatBoost promo0 overfit_rate는 86.5%입니다. CatBoost promo1 overfit_rate는 90.0%입니다.

# promo1 모델 재선정

- 성능 기준 1위 모델: CatBoost (test_roc_auc=0.863456810385, test_pr_auc=0.92866841882, overfit_rate=90.0%, type=performance_leader_but_overfit_risk, recommendation=conditional_recommended_after_user_approval)
- overfit 반영 후 1순위 조건부 후보: CatBoost (test_roc_auc=0.863456810385, test_pr_auc=0.92866841882, overfit_rate=90.0%, type=performance_leader_but_overfit_risk, recommendation=conditional_recommended_after_user_approval)
- backup candidate: SVM (test_roc_auc=0.841922743977, test_pr_auc=0.916235511128, overfit_rate=28.5%, type=unstable_candidate, recommendation=backup_candidate)
- conservative baseline: LogisticRegression (test_roc_auc=0.839461730803, test_pr_auc=0.914621925974, overfit_rate=0.0%, type=conservative_baseline, recommendation=baseline_only)
- 최종 사용자 승인 필요 여부: 필요
- score table 생성 시 사용할 수 있는 모델/파라미터 후보: CatBoost best_trial=44; params=param_border_count=39; param_depth=4; param_iterations=835; param_l2_leaf_reg=1.874062773851922; param_learning_rate=0.013642508707566272

# promo0 모델 재선정

- 성능 기준 1위 모델: CatBoost (test_roc_auc=0.898067469475, test_pr_auc=0.963654904907, overfit_rate=86.5%, type=performance_leader_but_overfit_risk, recommendation=conditional_recommended_after_user_approval)
- overfit 반영 후 1순위 조건부 후보: CatBoost (test_roc_auc=0.898067469475, test_pr_auc=0.963654904907, overfit_rate=86.5%, type=performance_leader_but_overfit_risk, recommendation=conditional_recommended_after_user_approval)
- backup candidate: SVM (test_roc_auc=0.87047315279, test_pr_auc=0.953699985759, overfit_rate=27.5%, type=unstable_candidate, recommendation=backup_candidate)
- conservative baseline: LogisticRegression (test_roc_auc=0.867332763057, test_pr_auc=0.951251136482, overfit_rate=0.0%, type=conservative_baseline, recommendation=baseline_only)
- 최종 사용자 승인 필요 여부: 필요
- score table 생성 시 사용할 수 있는 모델/파라미터 후보: CatBoost best_trial=69; params=param_border_count=63; param_depth=3; param_iterations=694; param_l2_leaf_reg=0.127913010953486; param_learning_rate=0.02448234473262313

# CatBoost 판단

CatBoost는 promo1과 promo0에서 성능상 강한 후보입니다. 다만 trial-level overfit pool risk가 낮지 않으면 성능 1위라는 이유만으로 바로 score source로 확정하면 안 됩니다. CatBoost promo0의 best non-overfit valid AUC는 0.881089890213이고, best trial 대비 손실은 0.00251575263634입니다. CatBoost promo1의 best non-overfit valid AUC는 0.860146846917이고, best trial 대비 손실은 0.00285382377042입니다.

# 대안 모델 판단

RandomForest는 promo1에서 recall-heavy candidate인지 확인했습니다. RandomForest promo1은 recall=0.922263681592, precision=0.766012396694입니다.

SVM은 objective std와 overfit pool 기준으로 unstable_candidate 여부를 확인했습니다. SVM promo0 objective_std=0.0520557006621, SVM promo1 objective_std=0.0450255528192입니다.

LogisticRegression은 conservative baseline으로 확인했습니다. 성능은 CatBoost보다 낮지만, overfit_rate가 낮고 구조가 단순하므로 baseline candidate로 남깁니다.

# 최종 권고

- promo1 1순위 score source 후보: CatBoost (test_roc_auc=0.863456810385, test_pr_auc=0.92866841882, overfit_rate=90.0%, type=performance_leader_but_overfit_risk, recommendation=conditional_recommended_after_user_approval)
- promo1 조건부 caveat: CatBoost가 포함될 경우 overfit pool risk와 best non-overfit trial 성능 손실을 사용자 승인 전 확인해야 합니다.
- promo1 2순위 backup candidate: SVM (test_roc_auc=0.841922743977, test_pr_auc=0.916235511128, overfit_rate=28.5%, type=unstable_candidate, recommendation=backup_candidate)
- promo1 baseline candidate: LogisticRegression (test_roc_auc=0.839461730803, test_pr_auc=0.914621925974, overfit_rate=0.0%, type=conservative_baseline, recommendation=baseline_only)
- promo0 1순위 score source 후보: CatBoost (test_roc_auc=0.898067469475, test_pr_auc=0.963654904907, overfit_rate=86.5%, type=performance_leader_but_overfit_risk, recommendation=conditional_recommended_after_user_approval)
- promo0 조건부 caveat: CatBoost가 포함될 경우 overfit pool risk와 best non-overfit trial 성능 손실을 사용자 승인 전 확인해야 합니다.
- promo0 2순위 backup candidate: SVM (test_roc_auc=0.87047315279, test_pr_auc=0.953699985759, overfit_rate=27.5%, type=unstable_candidate, recommendation=backup_candidate)
- promo0 baseline candidate: LogisticRegression (test_roc_auc=0.867332763057, test_pr_auc=0.951251136482, overfit_rate=0.0%, type=conservative_baseline, recommendation=baseline_only)
- 다음 2번 작업에서 row-level score table을 생성할 때 사용할 모델 제안: 사용자 승인 후 promo1 후보 파라미터 `CatBoost best_trial=44; params=param_border_count=39; param_depth=4; param_iterations=835; param_l2_leaf_reg=1.874062773851922; param_learning_rate=0.013642508707566272` 및 promo0 후보 파라미터 `CatBoost best_trial=69; params=param_border_count=63; param_depth=3; param_iterations=694; param_l2_leaf_reg=0.127913010953486; param_learning_rate=0.02448234473262313`를 기준으로 검토합니다.
- 사용자 승인 필요 사항: promo1/promo0 각각 어떤 후보를 score source로 사용할지 승인해야 합니다.

# 하지 않은 것

- row-level score table 생성 안 함
- OOF score 생성 안 함
- SHAP 생성 안 함
- segmentation 생성 안 함
- HTML 수정 안 함

# 다음 단계

다음 단계는 사용자가 승인한 모델을 기준으로 row-level OOF score table을 생성하는 것입니다.
