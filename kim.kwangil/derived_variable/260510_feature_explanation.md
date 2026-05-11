# 260510 공통 파생변수 설명

## 1. 작업 목적

- `10대`, `20대`, `30대`, `40대`, `60대`에서 공통적으로 프로모션 참여군과 비참여군 차이를 보일 가능성이 있는 파생변수 생성
- `price`가 프로모션 참여 정의와 직접 연결되므로, `price` 기반 파생변수는 의도적으로 제외
- 결과 CSV는 각 그룹별로 `USER_NUM` 1행 형태 유지

## 2. 데이터 처리 원칙

- 원본 두 파일은 결합 후 `(group, USER_NUM)` 기준으로 고유키 구성
- 최종 저장 파일은 그룹별로 분리해서 `USER_NUM`당 1행만 유지
- 시청이력은 `reg_date <= watch_day <= end_date` 범위만 사용
- `reg_date`, `end_date`는 원본 형식 보정 후 날짜 계산 반영

## 3. 대상 연령대 사용자 수

| 연령대 | 프로모션X | 프로모션O |
| --- | ---: | ---: |
| 10대 | 123 | 318 |
| 20대 | 2,376 | 4,831 |
| 30대 | 2,319 | 3,565 |
| 40대 | 5,826 | 1,960 |
| 60대 | 150 | 317 |

## 4. 공통 차이 강한 멤버십 파생변수

| 변수 | 유의 연령대 | 방향 | 공통 수준 | 식 |
| --- | --- | --- | --- | --- |
| mem_is_verified | 10대, 20대, 30대, 40대, 60대 | promo_gt_nonpromo | strong_common | 1[is_user_verified = 1] |
| mem_billing_method_140_flag | 10대, 20대, 30대, 40대, 60대 | promo_lt_nonpromo | strong_common | 1[billing_method = 140] |
| mem_device_ios_flag | 10대, 20대, 30대, 40대, 60대 | promo_lt_nonpromo | strong_common | 1[payment_device = ios] |
| mem_tenure_days | 10대, 20대, 30대, 40대 | promo_lt_nonpromo | exploratory_common | end_date_dt - reg_date_dt |
| mem_verified_premium_screen | 10대, 20대, 30대, 40대, 60대 | promo_gt_nonpromo | strong_common | mem_is_verified × mem_premium_screen_flag |
| mem_verified_multi_screen | 10대, 20대, 30대, 40대 | promo_gt_nonpromo | strong_common | mem_is_verified × mem_multi_screen_flag |
| mem_device_android_flag | 20대, 40대 | promo_gt_nonpromo | exploratory_common | 1[payment_device = android] |
| mem_billing_method_151_flag | 20대, 30대, 40대, 60대 | promo_gt_nonpromo | strong_common | 1[billing_method = 151] |
| mem_is_male | 20대, 30대, 40대, 60대 | promo_gt_nonpromo | strong_common | 1[gender = M] |
| mem_is_female | 20대, 40대, 60대 | promo_gt_nonpromo | exploratory_common | 1[gender = F] |
| mem_device_mobile_flag | 10대, 20대, 30대, 40대, 60대 | promo_gt_nonpromo | strong_common | 1[payment_device = mobile] |
| mem_reg_hour_morning | 10대, 20대, 30대, 40대, 60대 | promo_lt_nonpromo | strong_common | 1[6 <= reg_hour <= 11] |

## 5. 공통 차이 강한 시청행동 파생변수

| 변수 | 유의 연령대 | 방향 | 공통 수준 | 식 |
| --- | --- | --- | --- | --- |
| vh_active_day_ratio | 20대, 30대, 40대, 60대 | promo_gt_nonpromo | strong_common | \frac{vh\_active\_day\_count}{mem\_tenure\_days} |
| vh_last_watch_gap_days | 20대, 30대, 40대 | promo_lt_nonpromo | strong_common | \min_i (end\_date - watch\_date_i) |
| vh_end_near_watch_ratio | 20대, 30대, 40대 | promo_gt_nonpromo | strong_common | 1 - vh\_last\_watch\_gap\_ratio |
| vh_gap_stability_index | 20대, 40대, 60대 | promo_gt_nonpromo | strong_common | \frac{1}{1 + vh\_std\_gap\_days} |
| vh_last_14d_watch_ratio | 20대, 30대, 40대 | promo_gt_nonpromo | strong_common | \frac{\sum_i watch\_time_i \cdot 1[end\_date - watch\_date_i \le 14]}{\sum_i watch\_time_i} |
| vh_recency_intensity_index | 30대, 40대 | promo_gt_nonpromo | moderate_common | vh\_active\_day\_ratio \times vh\_end\_near\_watch\_ratio |
| vh_last_watch_gap_ratio | 30대, 40대 | promo_lt_nonpromo | moderate_common | \frac{vh\_last\_watch\_gap\_days}{mem\_tenure\_days} |
| vh_first_half_watch_ratio | 30대, 40대 | promo_lt_nonpromo | moderate_common | \frac{\sum_i watch\_time_i \cdot 1[(watch\_date_i - reg\_date) / tenure \le 0.5]}{\sum_i watch\_time_i} |
| vh_retention_curve_index | 30대, 40대 | promo_gt_nonpromo | moderate_common | vh\_last\_14d\_watch\_ratio - vh\_first\_half\_watch\_ratio |
| vh_watch_span_ratio | 40대 | promo_gt_nonpromo | exploratory_common | \frac{vh\_watch\_span\_days}{mem\_tenure\_days} |
| vh_short_watch_ratio | 20대 | promo_gt_nonpromo | exploratory_common | \frac{1}{N}\sum_i 1[watch\_time_i \le 5] |
| vh_event_per_tenure_day | 40대 | promo_gt_nonpromo | weak_common | \frac{vh\_event\_count}{mem\_tenure\_days} |
| vh_recent_release_180d_ratio | 60대 | promo_gt_nonpromo | weak_common | \frac{1}{N}\sum_i 1[0 \le watch\_date_i - release\_date_i \le 180] |
| genre_share__Action_Adventure | 40대 | promo_lt_nonpromo | exploratory_common | \frac{\sum_i watch\_time_i \cdot 1[genre_i = Action_Adventure]}{\sum_i watch\_time_i} |
| vh_multi_event_day_ratio | 40대 | promo_gt_nonpromo | weak_common | \frac{1}{D}\sum_d 1[events(d) \ge 2] |
| genre_share__Other | 20대 | promo_gt_nonpromo | weak_common | \frac{\sum_i watch\_time_i \cdot 1[genre_i = Other]}{\sum_i watch\_time_i} |
| vh_recent_release_365d_ratio | 60대 | promo_gt_nonpromo | weak_common | \frac{1}{N}\sum_i 1[0 \le watch\_date_i - release\_date_i \le 365] |
| vh_std_gap_days | 60대 | promo_gt_nonpromo | weak_common | std(gap_days) |

## 6. 연령대별 경향 요약

- `10대`: 공통 변수 중에서는 짧은 시청 비율과 가입 시각대 차이가 상대적으로 먼저 보였고, 행동형 차이는 약한 편
- `20대`: 활동일 비율과 만기 직전 14일 시청 비중이 완만하게 높아지는 방향 확인
- `30대`: 만기 근접 시청 비율과 후반부 시청 비중이 가장 안정적으로 높아지는 방향 확인
- `40대`: 활동일 비율과 마지막 시청 공백 계열이 가장 뚜렷하게 차이를 보인 구간
- `60대`: 표본 수는 작지만 활동일 비율과 최신작 선호 계열이 같은 방향으로 움직이는 경향 확인

## 7. 전체 파생변수 사전

| 변수 | 계열 | 사용 컬럼 | 계산식 | 설명 | 주의점 |
| --- | --- | --- | --- | --- | --- |
| vh_active_day_count | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | |\{watch\_date_i\}| | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_active_day_ratio | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_active\_day\_count}{mem\_tenure\_days} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_avg_daily_watch_min | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{1}{D}\sum_d watch\_time(d) | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_avg_watch_min | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{1}{N}\sum_i watch\_time_i | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_avg_watch_min_per_title | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_total\_watch\_min}{vh\_title\_count} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_avg_watch_seq | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{1}{N}\sum_i watch\_seq_i | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_binge_index | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_max\_daily\_watch\_min}{vh\_total\_watch\_min} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_event_count | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \sum_i 1 | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_event_per_tenure_day | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_event\_count}{mem\_tenure\_days} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_events_per_active_day | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_event\_count}{vh\_active\_day\_count} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_first_half_watch_ratio | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{\sum_i watch\_time_i \cdot 1[(watch\_date_i - reg\_date) / tenure \le 0.5]}{\sum_i watch\_time_i} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_first_watch_lag_days | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \min_i (watch\_date_i - reg\_date) | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_first_watch_lag_ratio | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_first\_watch\_lag\_days}{mem\_tenure\_days} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_last_14d_watch_ratio | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{\sum_i watch\_time_i \cdot 1[end\_date - watch\_date_i \le 14]}{\sum_i watch\_time_i} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_last_7d_watch_ratio | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{\sum_i watch\_time_i \cdot 1[end\_date - watch\_date_i \le 7]}{\sum_i watch\_time_i} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_long_watch_ratio | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{1}{N}\sum_i 1[watch\_time_i \ge 60] | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_max_daily_events | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \max_d events(d) | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_max_daily_watch_min | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \max_d watch\_time(d) | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_max_watch_min | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \max_i watch\_time_i | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_max_watch_seq | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \max_i watch\_seq_i | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_median_watch_min | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | median(watch_time_i) | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_multi_event_day_ratio | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{1}{D}\sum_d 1[events(d) \ge 2] | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_multi_event_intensity | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | vh\_multi\_event\_day\_ratio \times vh\_events\_per\_active\_day | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_repeat_event_count | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | vh\_event\_count - vh\_title\_count | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_rewatch_event_ratio | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_event\_count - vh\_title\_count}{vh\_event\_count} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_short_watch_ratio | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{1}{N}\sum_i 1[watch\_time_i \le 5] | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_std_daily_watch_min | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | std(daily_watch_time) | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_std_watch_min | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | std(watch_time_i) | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_title_count | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | |\{MOVIE\_NUM_i\}| | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_title_diversity_per_day | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_title\_count}{vh\_active\_day\_count} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_title_per_event_ratio | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_title\_count}{vh\_event\_count} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_titles_per_active_day | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_title\_count}{vh\_active\_day\_count} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_total_watch_min | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \sum_i watch\_time_i | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_w2_minus_w1_watch_min | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | vh\_week2\_watch\_min - vh\_week1\_watch\_min | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_w3_minus_w2_watch_min | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | vh\_week3\_watch\_min - vh\_week2\_watch\_min | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_watch_min_per_active_day | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_total\_watch\_min}{vh\_active\_day\_count} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_watch_min_per_tenure_day | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_total\_watch\_min}{mem\_tenure\_days} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_watch_span_days | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \max_i watch\_date_i - \min_i watch\_date_i + 1 | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_watch_span_ratio | activity | watch_day, watch_time(min), MOVIE_NUM, watch_seq | \frac{vh\_watch\_span\_days}{mem\_tenure\_days} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_activity_density | composite |  | \frac{vh\_active\_day\_count}{vh\_watch\_span\_days} | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_old_catalog_5y_ratio | composite | watch_day, ott_release_month, watch_time(min) | \frac{1}{N}\sum_i 1[watch\_date_i - release\_date_i \ge 1825] | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_short_minus_long_ratio | composite |  | vh\_short\_watch\_ratio - vh\_long\_watch\_ratio | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_w3_to_w1_ratio_capped | composite |  | \min\left(10, \frac{vh\_week3\_watch\_min}{vh\_week1\_watch\_min}\right) | 시청 강도와 사용 밀도를 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_mean_content_age_days | content_recency | watch_day, ott_release_month, watch_time(min) | \frac{1}{N}\sum_i (watch\_date_i - release\_date_i) | 최신작 선호와 카탈로그 연식을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_median_content_age_days | content_recency | watch_day, ott_release_month, watch_time(min) | median(watch_date_i - release_date_i) | 최신작 선호와 카탈로그 연식을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_recent_release_180d_ratio | content_recency | watch_day, ott_release_month, watch_time(min) | \frac{1}{N}\sum_i 1[0 \le watch\_date_i - release\_date_i \le 180] | 최신작 선호와 카탈로그 연식을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_recent_release_365d_ratio | content_recency | watch_day, ott_release_month, watch_time(min) | \frac{1}{N}\sum_i 1[0 \le watch\_date_i - release\_date_i \le 365] | 최신작 선호와 카탈로그 연식을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_blockbuster_genre_share | genre_composite | genre, watch_time(min) | genre\_share(Action\_Adventure) + genre\_share(SF\_Fantasy) + genre\_share(Historical\_War) | 장르 선호를 묶어서 해석 가능하게 만든 파생변수 | 모델 입력 후보 가능 |
| vh_emotional_genre_share | genre_composite | genre, watch_time(min) | genre\_share(Drama) + genre\_share(Romance) | 장르 선호를 묶어서 해석 가능하게 만든 파생변수 | 모델 입력 후보 가능 |
| vh_genre_entropy | genre_composite | genre, watch_time(min) | -\sum_g p_g \log p_g | 장르 선호를 묶어서 해석 가능하게 만든 파생변수 | 모델 입력 후보 가능 |
| vh_genre_unique_count | genre_composite | genre, watch_time(min) | |\{genre_i\}| | 장르 선호를 묶어서 해석 가능하게 만든 파생변수 | 모델 입력 후보 가능 |
| vh_light_genre_share | genre_composite | genre, watch_time(min) | genre\_share(Comedy) + genre\_share(Animation\_Family) | 장르 선호를 묶어서 해석 가능하게 만든 파생변수 | 모델 입력 후보 가능 |
| vh_nonfiction_genre_share | genre_composite | genre, watch_time(min) | genre\_share(Documentary) + genre\_share(Other) | 장르 선호를 묶어서 해석 가능하게 만든 파생변수 | 모델 입력 후보 가능 |
| vh_tension_genre_share | genre_composite | genre, watch_time(min) | genre\_share(Thriller\_Crime) + genre\_share(Horror) | 장르 선호를 묶어서 해석 가능하게 만든 파생변수 | 모델 입력 후보 가능 |
| vh_top_genre_share | genre_composite | genre, watch_time(min) | \max_g p_g | 장르 선호를 묶어서 해석 가능하게 만든 파생변수 | 모델 입력 후보 가능 |
| genre_share__Action_Adventure | genre_share | genre, watch_time(min) | \frac{\sum_i watch\_time_i \cdot 1[genre_i = Action_Adventure]}{\sum_i watch\_time_i} | 전체 시청시간 중 특정 장르 비중을 나타내는 파생변수 | 모델 입력 후보 가능 |
| genre_share__Animation_Family | genre_share | genre, watch_time(min) | \frac{\sum_i watch\_time_i \cdot 1[genre_i = Animation_Family]}{\sum_i watch\_time_i} | 전체 시청시간 중 특정 장르 비중을 나타내는 파생변수 | 모델 입력 후보 가능 |
| genre_share__Comedy | genre_share | genre, watch_time(min) | \frac{\sum_i watch\_time_i \cdot 1[genre_i = Comedy]}{\sum_i watch\_time_i} | 전체 시청시간 중 특정 장르 비중을 나타내는 파생변수 | 모델 입력 후보 가능 |
| genre_share__Documentary | genre_share | genre, watch_time(min) | \frac{\sum_i watch\_time_i \cdot 1[genre_i = Documentary]}{\sum_i watch\_time_i} | 전체 시청시간 중 특정 장르 비중을 나타내는 파생변수 | 모델 입력 후보 가능 |
| genre_share__Drama | genre_share | genre, watch_time(min) | \frac{\sum_i watch\_time_i \cdot 1[genre_i = Drama]}{\sum_i watch\_time_i} | 전체 시청시간 중 특정 장르 비중을 나타내는 파생변수 | 모델 입력 후보 가능 |
| genre_share__Historical_War | genre_share | genre, watch_time(min) | \frac{\sum_i watch\_time_i \cdot 1[genre_i = Historical_War]}{\sum_i watch\_time_i} | 전체 시청시간 중 특정 장르 비중을 나타내는 파생변수 | 모델 입력 후보 가능 |
| genre_share__Horror | genre_share | genre, watch_time(min) | \frac{\sum_i watch\_time_i \cdot 1[genre_i = Horror]}{\sum_i watch\_time_i} | 전체 시청시간 중 특정 장르 비중을 나타내는 파생변수 | 모델 입력 후보 가능 |
| genre_share__Other | genre_share | genre, watch_time(min) | \frac{\sum_i watch\_time_i \cdot 1[genre_i = Other]}{\sum_i watch\_time_i} | 전체 시청시간 중 특정 장르 비중을 나타내는 파생변수 | 모델 입력 후보 가능 |
| genre_share__Romance | genre_share | genre, watch_time(min) | \frac{\sum_i watch\_time_i \cdot 1[genre_i = Romance]}{\sum_i watch\_time_i} | 전체 시청시간 중 특정 장르 비중을 나타내는 파생변수 | 모델 입력 후보 가능 |
| genre_share__SF_Fantasy | genre_share | genre, watch_time(min) | \frac{\sum_i watch\_time_i \cdot 1[genre_i = SF_Fantasy]}{\sum_i watch\_time_i} | 전체 시청시간 중 특정 장르 비중을 나타내는 파생변수 | 모델 입력 후보 가능 |
| genre_share__Thriller_Crime | genre_share | genre, watch_time(min) | \frac{\sum_i watch\_time_i \cdot 1[genre_i = Thriller_Crime]}{\sum_i watch\_time_i} | 전체 시청시간 중 특정 장르 비중을 나타내는 파생변수 | 모델 입력 후보 가능 |
| mem_billing_method_131_flag | membership | billing_method | 1[billing_method = 131] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_billing_method_132_flag | membership | billing_method | 1[billing_method = 132] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_billing_method_134_flag | membership | billing_method | 1[billing_method = 134] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_billing_method_140_flag | membership | billing_method | 1[billing_method = 140] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_billing_method_151_flag | membership | billing_method | 1[billing_method = 151] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_billing_method_170_flag | membership | billing_method | 1[billing_method = 170] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_billing_method_180_flag | membership | billing_method | 1[billing_method = 180] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_billing_method_190_flag | membership | billing_method | 1[billing_method = 190] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_billing_method_value | membership | billing_method | billing_method | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_device_android_flag | membership | payment_device | 1[payment_device = android] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_device_ios_flag | membership | payment_device | 1[payment_device = ios] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_device_mobile_flag | membership | payment_device | 1[payment_device = mobile] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_device_ott_flag | membership | payment_device | 1[payment_device = ott] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_device_pc_flag | membership | payment_device | 1[payment_device = pc] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_device_smarttv_flag | membership | payment_device | 1[payment_device = smarttv] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_is_churn_prevented_flag | membership | is_churn_prevented | 1[is_churn_prevented = 1] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 정책성 변수 가능성 존재 |
| mem_is_female | membership | gender | 1[gender = F] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_is_male | membership | gender | 1[gender = M] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_is_verified | membership | is_user_verified | 1[is_user_verified = 1] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_max_screen_value | membership | max_screen | max_screen | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_multi_screen_flag | membership | max_screen | 1[max_screen >= 2] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_premium_screen_flag | membership | max_screen | 1[max_screen >= 4] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_reg_hour | membership | reg_date, reg_hour | reg_hour | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_reg_hour_afternoon | membership | reg_date, reg_hour | 1[12 <= reg_hour <= 17] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_reg_hour_evening | membership | reg_date, reg_hour | 1[18 <= reg_hour <= 23] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_reg_hour_morning | membership | reg_date, reg_hour | 1[6 <= reg_hour <= 11] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_reg_hour_night | membership | reg_date, reg_hour | 1[0 <= reg_hour <= 5] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_reg_is_weekend | membership | reg_date, reg_hour | 1[weekday(reg_date_dt) in {5, 6}] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_reg_weekday | membership | reg_date, reg_hour | weekday(reg_date_dt) | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_screen_1_flag | membership | max_screen | 1[max_screen = 1] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_screen_2_flag | membership | max_screen | 1[max_screen = 2] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_screen_4_flag | membership | max_screen | 1[max_screen = 4] | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_tenure_days | membership | reg_date, end_date | end_date_dt - reg_date_dt | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_verified_multi_screen | membership | is_user_verified, max_screen | mem_is_verified × mem_multi_screen_flag | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| mem_verified_premium_screen | membership | is_user_verified, max_screen | mem_is_verified × mem_premium_screen_flag | 멤버십 기준 사용자 1행에서 직접 계산한 구조형 파생변수 | 모델 입력 후보 가능 |
| vh_end_near_watch_ratio | recency | watch_day, reg_date, end_date, watch_time(min) | 1 - vh\_last\_watch\_gap\_ratio | 만기 직전 유지 패턴과 재방문 리듬을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_gap_stability_index | recency | watch_day, reg_date, end_date, watch_time(min) | \frac{1}{1 + vh\_std\_gap\_days} | 만기 직전 유지 패턴과 재방문 리듬을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_last_watch_gap_days | recency | watch_day, reg_date, end_date, watch_time(min) | \min_i (end\_date - watch\_date_i) | 만기 직전 유지 패턴과 재방문 리듬을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_last_watch_gap_ratio | recency | watch_day, reg_date, end_date, watch_time(min) | \frac{vh\_last\_watch\_gap\_days}{mem\_tenure\_days} | 만기 직전 유지 패턴과 재방문 리듬을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_max_gap_days | recency | watch_day, reg_date, end_date, watch_time(min) | \max_g gap_g | 만기 직전 유지 패턴과 재방문 리듬을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_mean_gap_days | recency | watch_day, reg_date, end_date, watch_time(min) | \frac{1}{G}\sum_g gap_g | 만기 직전 유지 패턴과 재방문 리듬을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_recency_intensity_index | recency | watch_day, reg_date, end_date, watch_time(min) | vh\_active\_day\_ratio \times vh\_end\_near\_watch\_ratio | 만기 직전 유지 패턴과 재방문 리듬을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_recent_old_gap | recency | watch_day, ott_release_month, watch_time(min) | vh\_recent\_release\_365d\_ratio - vh\_old\_catalog\_5y\_ratio | 만기 직전 유지 패턴과 재방문 리듬을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_retention_curve_index | recency | watch_day, reg_date, end_date, watch_time(min) | vh\_last\_14d\_watch\_ratio - vh\_first\_half\_watch\_ratio | 만기 직전 유지 패턴과 재방문 리듬을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_std_gap_days | recency | watch_day, reg_date, end_date, watch_time(min) | std(gap_days) | 만기 직전 유지 패턴과 재방문 리듬을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_front_loaded_ratio | timing_pattern | watch_day, reg_date, watch_time(min) | \frac{vh\_week1\_watch\_min + vh\_week2\_watch\_min}{vh\_total\_watch\_min} | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_late_ratio | timing_pattern | watch_day, reg_date, watch_time(min) | \frac{vh\_week4\_watch\_min + vh\_week5\_watch\_min}{vh\_total\_watch\_min} | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_mid_late_ratio | timing_pattern | watch_day, reg_date, watch_time(min) | vh\_week3\_watch\_ratio + vh\_week4\_watch\_ratio + vh\_week5\_watch\_ratio | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_week1_watch_min | timing_pattern | watch_day, reg_date, watch_time(min) | \sum_i watch\_time_i \cdot 1[week\_index_i = 1] | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_week1_watch_ratio | timing_pattern | watch_day, reg_date, watch_time(min) | \frac{vh\_week1\_watch\_min}{vh\_total\_watch\_min} | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_week2_watch_min | timing_pattern | watch_day, reg_date, watch_time(min) | \sum_i watch\_time_i \cdot 1[week\_index_i = 2] | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_week2_watch_ratio | timing_pattern | watch_day, reg_date, watch_time(min) | \frac{vh\_week2\_watch\_min}{vh\_total\_watch\_min} | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_week3_watch_min | timing_pattern | watch_day, reg_date, watch_time(min) | \sum_i watch\_time_i \cdot 1[week\_index_i = 3] | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_week3_watch_ratio | timing_pattern | watch_day, reg_date, watch_time(min) | \frac{vh\_week3\_watch\_min}{vh\_total\_watch\_min} | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_week4_watch_min | timing_pattern | watch_day, reg_date, watch_time(min) | \sum_i watch\_time_i \cdot 1[week\_index_i = 4] | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_week4_watch_ratio | timing_pattern | watch_day, reg_date, watch_time(min) | \frac{vh\_week4\_watch\_min}{vh\_total\_watch\_min} | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_week5_watch_min | timing_pattern | watch_day, reg_date, watch_time(min) | \sum_i watch\_time_i \cdot 1[week\_index_i = 5] | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_week5_watch_ratio | timing_pattern | watch_day, reg_date, watch_time(min) | \frac{vh\_week5\_watch\_min}{vh\_total\_watch\_min} | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |
| vh_weekend_ratio | timing_pattern | watch_day, reg_date, watch_time(min) | \frac{1}{N}\sum_i 1[watch\_date_i \in weekend] | 구독 기간 내 시청 배분 패턴을 반영하는 파생변수 | 모델 입력 후보 가능 |

## 8. 생성 파일

- `260510_user_features_0.csv`: 프로모션 미참여 그룹 사용자 단위 파생변수 테이블
- `260510_user_features_1.csv`: 프로모션 참여 그룹 사용자 단위 파생변수 테이블
- `260510_feature_explanation.md`: 변수 설명 문서
