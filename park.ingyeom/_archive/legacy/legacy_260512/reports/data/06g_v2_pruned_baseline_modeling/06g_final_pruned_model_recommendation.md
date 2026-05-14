# 06g 최종 pruned 모델 멘토 대응 문안

최종 후보는 `pruned_w1_3_early_safer_week1_2_without_product_code_without_watch_presence_flag`입니다.
- AUC: 0.804651
- churn-risk PR AUC: 0.611947
- top-decile lift: 2.587726
- product_code 포함 여부: N
- watch-presence flag 포함 여부: N
- timing label: early_safer_w1_3_proxy

멘토님께는 full model의 높은 AUC를 공식 조기예측 성능으로 주장하지 않고, product_code와 watch-presence shortcut을 제외한 pruned 모델을 공식 후보로 제시하겠다고 설명합니다.
