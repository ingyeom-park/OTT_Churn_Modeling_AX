# 05f v2c 공식 feature dictionary 보고서

생성 시각: 2026-05-12T10:25:59

## 기준

- 공식 feature set: `pruned_w1_3_all_weeks_interpretable_without_product_code_without_watch_presence`
- 공식 모델: `HistGradientBoostingClassifier`
- 공식 AUC: 0.862939
- 데이터 행 수: 23,115
- 공식 feature 수: 30
- SHAP 근거: Stage 07c TRUE SHAP만 사용했습니다. 07r/06h SHAP은 최종 근거로 사용하지 않았습니다.

## 1. 어떤 원본 피처가 남아 있는가?

공식 모델에 직접 남은 원천형 멤버십 정보는 `price_num`, `max_screen_num`, `age_num`, `gender_clean`, `payment_device_clean`, `billing_method_clean`, `is_promotion_bin`, `is_user_verified_bin`입니다. 이 변수들은 원천 Membership 값을 숫자형, 이진형, 정리된 범주형으로 표준화한 feature입니다.

목록: price_num, max_screen_num, is_promotion_bin, is_user_verified_bin, age_num, gender_clean, payment_device_clean, billing_method_clean

## 2. 어떤 파생 피처가 남아 있는가?

공식 모델의 파생 피처는 1~3주 관측창의 주차별 시청 시간과 세션 수, 단순 이용량 요약, 장르 비율, 장르 entropy, 최근 콘텐츠 시청 비율입니다.

목록: w1_3_week1_watch_time, w1_3_week2_watch_time, w1_3_week3_watch_time, w1_3_week1_sessions, w1_3_week2_sessions, w1_3_week3_sessions, w1_3_unique_contents, w1_3_unique_watch_days, w1_3_avg_watch_time_per_session, w1_3_genre_ratio_action_adventure, w1_3_genre_ratio_animation_family, w1_3_genre_ratio_comedy, w1_3_genre_ratio_documentary, w1_3_genre_ratio_drama, w1_3_genre_ratio_historical_war, w1_3_genre_ratio_horror, w1_3_genre_ratio_other, w1_3_genre_ratio_romance, w1_3_genre_ratio_sf_fantasy, w1_3_genre_ratio_thriller_crime, w1_3_genre_entropy, w1_3_recent_content_watch_ratio

상위 SHAP family: weekly_usage_pattern rank 1; genre_ratio_proxy rank 2; membership_context rank 3; simple_usage_volume rank 4; release_month_proxy rank 5

## 3. 어떤 메타데이터와 타깃이 있는가?

`membership_row_id`와 `USER_KEY`는 추적 및 사용자 단위 분리 확인용 metadata입니다. `is_repurchase_label`은 target입니다. 이 세 컬럼은 엑셀에 표시했지만 공식 모델 feature로 표시하지 않았습니다.

목록: is_repurchase_label, membership_row_id, USER_KEY

## 4. 어떤 변수들이 공식 모델에서 제외되었는가?

공식 모델 제외 변수는 product_code, watch-presence 계열, first/last timing 계열, week ratio/delta 계열, 총 시청 시간, 장르별 절대 시청량과 세션 수, 정책/target 인접 후보, duration/raw date/raw backup 계열입니다.

목록: duration_days, duration_days_recomputed, end_date, first_watch_rel_day, has_watch_obs, is_churn_prevented, is_churn_prevented_bin, last_watch_rel_day, no_watch_obs_flag, product_code, reg_date, w1_3_content_has_watch_obs, w1_3_genre_session_count_action_adventure, w1_3_genre_session_count_animation_family, w1_3_genre_session_count_comedy, w1_3_genre_session_count_documentary, w1_3_genre_session_count_drama, w1_3_genre_session_count_historical_war, w1_3_genre_session_count_horror, w1_3_genre_session_count_other, w1_3_genre_session_count_romance, w1_3_genre_session_count_sf_fantasy, w1_3_genre_session_count_thriller_crime, w1_3_genre_watch_time_action_adventure, w1_3_genre_watch_time_animation_family, w1_3_genre_watch_time_comedy, w1_3_genre_watch_time_documentary, w1_3_genre_watch_time_drama, w1_3_genre_watch_time_historical_war, w1_3_genre_watch_time_horror, w1_3_genre_watch_time_other, w1_3_genre_watch_time_romance, w1_3_genre_watch_time_sf_fantasy, w1_3_genre_watch_time_thriller_crime, w1_3_has_watch_obs, w1_3_total_watch_time, w1_3_w2_minus_w1_watch_time, w1_3_w3_minus_w2_watch_time, w1_3_week1_ratio, w1_3_week2_ratio, w1_3_week3_ratio, watch_date, watch_day

## 5. 왜 주요 변수군을 제외했는가?

`product_code`는 상품 코드 자체를 외워 버리는 위험을 줄이기 위해 제외했습니다. `has_watch_obs`와 `no_watch_obs_flag` 계열은 시청 기록 존재 여부 자체가 shortcut이 될 수 있어 제외했습니다. `first_watch_rel_day`와 `last_watch_rel_day`는 재구독 판단 시점에 가까운 timing proxy가 될 수 있어 제외했습니다. `week*_ratio`와 `w*_minus_*` 계열은 주차별 시청 시간과 구조적으로 중복될 수 있어 제외했습니다. `genre_watch_time_*`와 `genre_session_count_*`는 장르 취향보다 사용량 proxy가 섞일 위험이 있어 제외했습니다.

## 6. 팀원은 이 엑셀을 어떻게 읽어야 하는가?

`변수 설명` 시트에서 `비고`가 `공식 모델 사용`인 행만 06c2/07c corrected official model의 실제 feature입니다. `target`, `metadata only`, `공식 모델 제외`로 표시된 행은 모델 입력 feature가 아닙니다. `SHAP 중요 변수` 시트는 07c TRUE SHAP 기반의 해석 보조 자료이며, 원인 효과나 ROI 근거가 아닙니다. `제외 변수 사유` 시트는 발표나 팀 공유 때 왜 특정 변수를 쓰지 않았는지 설명하는 용도로 읽으면 됩니다.
