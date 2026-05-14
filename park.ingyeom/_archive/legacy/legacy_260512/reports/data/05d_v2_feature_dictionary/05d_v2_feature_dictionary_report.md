# 05d v2 Feature Dictionary Report

Generated at: 2026-05-11T16:58:36

- w1_3 columns: 84
- w1_4 columns: 89
- union columns covered: 160
- primary model features: 80
- target-adjacent or redundancy caution rows: 96
- Stage 06c verdict: target_adjacent_but_not_direct_leakage

## Top TRUE SHAP Features
- 1. w1_3_week3_watch_time / 1~3주 3주차 시청 시간 / usage / mean_abs_shap=0.619701
- 2. w1_3_w2_minus_w1_watch_time / 1~3주 w2 minus w1 watch time / usage / mean_abs_shap=0.264763
- 3. w1_3_week1_ratio / 1~3주 1주차 시청 비중 / usage / mean_abs_shap=0.227194
- 4. price / 가격 / membership / mean_abs_shap=0.191771
- 5. w1_3_first_watch_rel_day / 1~3주 첫 시청 상대일 / usage / mean_abs_shap=0.173888
- 6. w1_3_genre_ratio_thriller_crime / 1~3주 thriller/crime 장르 비중 / genre / mean_abs_shap=0.164927
- 7. w1_3_genre_ratio_animation_family / 1~3주 animation/family 장르 비중 / genre / mean_abs_shap=0.127053
- 8. w1_3_genre_ratio_drama / 1~3주 drama 장르 비중 / genre / mean_abs_shap=0.113679
- 9. w1_3_genre_session_count_drama / 1~3주 drama 장르 세션 수 / genre / mean_abs_shap=0.109960
- 10. w1_3_genre_ratio_action_adventure / 1~3주 action/adventure 장르 비중 / genre / mean_abs_shap=0.109491

## How To Use
- 코드에서는 원 컬럼명을 유지합니다.
- 팀 공유와 발표에서는 presentation_label_ko를 사용합니다.
- final_use_recommendation이 group_for_interpretation인 변수는 개별 효과처럼 말하지 않고 묶어서 설명합니다.
- Stage 07r TRUE SHAP만 최종 XAI 근거로 사용합니다.

## What Not To Claim
- 개별 피처가 이탈의 원인이라고 말하지 않습니다.
- country, rating, runtime, actor, director, Wavve, KOBIS metadata를 사용했다고 말하지 않습니다.
- USER_KEY, membership_row_id, raw date, target을 모델 feature처럼 말하지 않습니다.
