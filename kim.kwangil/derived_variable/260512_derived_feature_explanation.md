# 260512 파생변수 설명

## 1. 작업 목적
- `10대`, `20대`, `30대`, `40대`, `60대`에서 프로모션 참여 그룹과 비참여 그룹의 이탈률 차이를 설명할 수 있는 파생변수 재구성
- 원본 멤버십 컬럼은 그대로 유지하고, 파생변수만 추가하는 구조로 재작성
- 상관관계와 VIF 기준은 원본 변수가 아니라 최종 선택된 파생변수끼리만 점검

## 2. 원본 유지 기준
- 결과 CSV에는 `USER_NUM` 단위에서 값이 고정되는 원본 멤버십 컬럼을 그대로 유지
- `watch_day`, `watch_time(min)`, `MOVIE_NUM`, `genre`처럼 같은 `USER_NUM` 안에서 여러 행으로 바뀌는 시청 이력 원본 컬럼은 1행 구조와 충돌하므로 그대로 둘 수 없고 파생변수로만 반영
- 따라서 이번 결과는 `원본 멤버십 컬럼 + 시청 이력 요약 파생변수` 구조

## 3. 데이터 처리 기준
- 원본 파일: `260509_merged1_0.csv`, `260509_merged1_1.csv`
- 파생변수 후보 풀: 기존 사용자 단위 후보 테이블 `260510_user_features_0.csv`, `260510_user_features_1.csv`
- 후보 파생변수 수: `125`개
- 선택 우선순위: `유의 나이대 수` 내림차순, `평균 절대 효과크기` 내림차순, `최소 p값` 오름차순
- 파생변수 선별 기준: `pairwise |corr| <= 0.65`, `Centered VIF <= 5.0`

## 4. 유의 나이대 사용자 수
| 나이대 | 비참여 그룹 | 참여 그룹 |
| --- | ---: | ---: |
| 10대 | 123 | 318 |
| 20대 | 2,376 | 4,831 |
| 30대 | 2,319 | 3,565 |
| 40대 | 5,826 | 1,960 |
| 60대 | 150 | 317 |

## 5. 최종 선택 결과
- 최종 선택 파생변수 수: `36`개
- 멤버십 파생변수 수: `21`개
- 시청 이력 파생변수 수: `15`개
- 최종 파생변수 집합 최대 절대상관: `mem_verified_multi_screen` vs `mem_verified_premium_screen` = `0.618`
- 최종 파생변수 집합 최대 Centered VIF: `mem_billing_method_140_flag` = `2.893`

## 6. 최종 선택 변수 요약
| 변수명 | 구분 | 선택 등급 | 유의 나이대 수 | 유의 나이대 | 최대 절대상관 | Centered VIF |
| --- | --- | --- | ---: | --- | ---: | ---: |
| mem_is_verified | 멤버십 | strong_common | 5 | 10대, 20대, 30대, 40대, 60대 | 0.537 | 1.602 |
| mem_billing_method_140_flag | 멤버십 | strong_common | 5 | 10대, 20대, 30대, 40대, 60대 | 0.537 | 2.893 |
| mem_reg_hour_morning | 멤버십 | strong_common | 5 | 10대, 20대, 30대, 40대, 60대 | 0.274 | 1.168 |
| mem_verified_premium_screen | 멤버십 | strong_common | 5 | 10대, 20대, 30대, 40대, 60대 | 0.618 | 1.667 |
| mem_is_churn_prevented_flag | 멤버십 | strong_common | 5 | 10대, 20대, 30대, 40대, 60대 | 0.181 | 1.056 |
| mem_reg_hour | 멤버십 | strong_common | 5 | 10대, 20대, 30대, 40대, 60대 | 0.263 | 1.079 |
| mem_device_mobile_flag | 멤버십 | strong_common | 5 | 10대, 20대, 30대, 40대, 60대 | 0.212 | 1.427 |
| mem_device_pc_flag | 멤버십 | strong_common | 5 | 10대, 20대, 30대, 40대, 60대 | 0.238 | 1.436 |
| mem_tenure_days | 멤버십 | common_core | 4 | 10대, 20대, 30대, 40대 | 0.140 | 1.133 |
| mem_verified_multi_screen | 멤버십 | common_core | 4 | 10대, 20대, 30대, 40대 | 0.618 | 1.852 |
| mem_billing_method_151_flag | 멤버십 | common_core | 4 | 20대, 30대, 40대, 60대 | 0.280 | 2.598 |
| mem_is_male | 멤버십 | common_core | 4 | 20대, 30대, 40대, 60대 | 0.237 | 1.110 |
| vh_active_day_ratio | 시청 이력 | common_core | 4 | 20대, 30대, 40대, 60대 | 0.513 | 1.996 |
| mem_device_smarttv_flag | 멤버십 | common_core | 4 | 10대, 20대, 30대, 40대 | 0.084 | 1.070 |
| mem_reg_weekday | 멤버십 | common_support | 3 | 10대, 20대, 30대 | 0.046 | 1.010 |
| mem_billing_method_134_flag | 멤버십 | common_support | 3 | 30대, 40대, 60대 | 0.280 | 2.688 |
| vh_end_near_watch_ratio | 시청 이력 | common_support | 3 | 20대, 30대, 40대 | 0.613 | 2.720 |
| vh_gap_stability_index | 시청 이력 | common_support | 3 | 20대, 40대, 60대 | 0.513 | 1.418 |
| mem_billing_method_190_flag | 멤버십 | common_support | 3 | 20대, 30대, 40대 | 0.175 | 1.717 |
| mem_billing_method_180_flag | 멤버십 | common_support | 3 | 20대, 30대, 40대 | 0.188 | 1.816 |
| vh_last_14d_watch_ratio | 시청 이력 | common_support | 3 | 20대, 30대, 40대 | 0.613 | 2.426 |
| mem_billing_method_132_flag | 멤버십 | age_specific_exploratory | 2 | 20대, 40대 | 0.190 | 1.827 |
| mem_billing_method_170_flag | 멤버십 | age_specific_exploratory | 2 | 10대, 20대 | 0.082 | 1.119 |
| mem_device_ott_flag | 멤버십 | age_specific_exploratory | 2 | 20대, 30대 | 0.050 | 1.020 |
| vh_short_watch_ratio | 시청 이력 | age_specific_strong | 1 | 20대 | 0.303 | 1.169 |
| vh_recent_release_180d_ratio | 시청 이력 | age_specific_strong | 1 | 60대 | 0.303 | 1.243 |
| vh_multi_event_day_ratio | 시청 이력 | age_specific_exploratory | 1 | 40대 | 0.158 | 1.060 |
| mem_reg_hour_afternoon | 멤버십 | age_specific_exploratory | 1 | 20대 | 0.274 | 1.084 |
| vh_light_genre_share | 시청 이력 | age_specific_strong | 1 | 60대 | 0.254 | 1.178 |
| vh_w3_to_w1_ratio_capped | 시청 이력 | age_specific_strong | 1 | 60대 | 0.250 | 1.150 |
| vh_std_gap_days | 시청 이력 | age_specific_strong | 1 | 60대 | 0.303 | 1.256 |
| genre_share__Action_Adventure | 시청 이력 | age_specific_exploratory | 1 | 40대 | 0.240 | 1.188 |
| vh_nonfiction_genre_share | 시청 이력 | age_specific_exploratory | 1 | 20대 | 0.173 | 1.131 |
| vh_week4_watch_ratio | 시청 이력 | age_specific_exploratory | 1 | 30대 | 0.604 | 2.190 |
| vh_week4_watch_min | 시청 이력 | age_specific_exploratory | 1 | 30대 | 0.540 | 1.576 |
| vh_tension_genre_share | 시청 이력 | age_specific_exploratory | 1 | 30대 | 0.254 | 1.162 |

## 7. 변수 상세 설명
### mem_is_verified
- 분류: 멤버십 관련 파생변수
- 선택 등급: strong_common
- 사용 컬럼: `is_user_verified`
- 수식: `mem_is_verified = 1[is_user_verified = 1]`
- 설명: 본인 인증 완료 여부
- 유의 나이대: 10대, 20대, 30대, 40대, 60대
- 최대 절대상관: 0.537 (상대 변수: mem_billing_method_140_flag)
- Centered VIF: 1.602
- 연령대별 검정 결과:
- 10대: p=1.7061e-08, effect_rbc=-0.0976, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=1.41206e-106, effect_rbc=-0.0964, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=2.85625e-89, effect_rbc=-0.1078, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0, effect_rbc=-0.8059, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=1.10209e-07, effect_rbc=-0.0867, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_billing_method_140_flag
- 분류: 멤버십 관련 파생변수
- 선택 등급: strong_common
- 사용 컬럼: `billing_method`
- 수식: `mem_billing_method_140_flag = 1[billing_method = 140]`
- 설명: 청구 방식 코드 140 사용 여부
- 유의 나이대: 10대, 20대, 30대, 40대, 60대
- 최대 절대상관: 0.537 (상대 변수: mem_is_verified)
- Centered VIF: 2.893
- 연령대별 검정 결과:
- 10대: p=3.49356e-12, effect_rbc=0.1463, 프로모션 그룹 평균 < 비참여 그룹 평균
- 20대: p=1.13198e-263, effect_rbc=0.2302, 프로모션 그룹 평균 < 비참여 그룹 평균
- 30대: p=2.82166e-125, effect_rbc=0.1496, 프로모션 그룹 평균 < 비참여 그룹 평균
- 40대: p=0, effect_rbc=0.4924, 프로모션 그룹 평균 < 비참여 그룹 평균
- 60대: p=3.47261e-06, effect_rbc=0.0667, 프로모션 그룹 평균 < 비참여 그룹 평균
### mem_reg_hour_morning
- 분류: 멤버십 관련 파생변수
- 선택 등급: strong_common
- 사용 컬럼: `reg_hour`
- 수식: `mem_reg_hour_morning = 1[6 <= reg_hour <= 11]`
- 설명: 오전 시간대 가입 여부
- 유의 나이대: 10대, 20대, 30대, 40대, 60대
- 최대 절대상관: 0.274 (상대 변수: mem_reg_hour_afternoon)
- Centered VIF: 1.168
- 연령대별 검정 결과:
- 10대: p=1.38667e-15, effect_rbc=0.3334, 프로모션 그룹 평균 < 비참여 그룹 평균
- 20대: p=9.37647e-53, effect_rbc=0.1437, 프로모션 그룹 평균 < 비참여 그룹 평균
- 30대: p=6.14788e-26, effect_rbc=0.1138, 프로모션 그룹 평균 < 비참여 그룹 평균
- 40대: p=0.018661, effect_rbc=0.0245, 프로모션 그룹 평균 < 비참여 그룹 평균
- 60대: p=7.02082e-05, effect_rbc=0.1669, 프로모션 그룹 평균 < 비참여 그룹 평균
### mem_verified_premium_screen
- 분류: 멤버십 관련 파생변수
- 선택 등급: strong_common
- 사용 컬럼: `is_user_verified, max_screen`
- 수식: `mem_verified_premium_screen = 1[is_user_verified = 1] x 1[max_screen >= 4]`
- 설명: 인증 완료와 프리미엄 동시 시청 옵션 동시 충족 여부
- 유의 나이대: 10대, 20대, 30대, 40대, 60대
- 최대 절대상관: 0.618 (상대 변수: mem_verified_multi_screen)
- Centered VIF: 1.667
- 연령대별 검정 결과:
- 10대: p=5.42453e-05, effect_rbc=-0.1920, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=3.5043e-74, effect_rbc=-0.1851, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=7.64868e-32, effect_rbc=-0.1124, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=2.34545e-125, effect_rbc=-0.1379, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.00212286, effect_rbc=-0.1149, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_is_churn_prevented_flag
- 분류: 멤버십 관련 파생변수
- 선택 등급: strong_common
- 사용 컬럼: `is_churn_prevented`
- 수식: `mem_is_churn_prevented_flag = 1[is_churn_prevented = 1]`
- 설명: 이탈 방지 플래그 보유 여부
- 유의 나이대: 10대, 20대, 30대, 40대, 60대
- 최대 절대상관: 0.181 (상대 변수: mem_billing_method_140_flag)
- Centered VIF: 1.056
- 연령대별 검정 결과:
- 10대: p=3.18301e-08, effect_rbc=0.2603, 프로모션 그룹 평균 < 비참여 그룹 평균
- 20대: p=1.02742e-49, effect_rbc=0.1481, 프로모션 그룹 평균 < 비참여 그룹 평균
- 30대: p=1.16311e-27, effect_rbc=0.1188, 프로모션 그룹 평균 < 비참여 그룹 평균
- 40대: p=6.33823e-08, effect_rbc=-0.0485, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=1.79333e-05, effect_rbc=0.1563, 프로모션 그룹 평균 < 비참여 그룹 평균
### mem_reg_hour
- 분류: 멤버십 관련 파생변수
- 선택 등급: strong_common
- 사용 컬럼: `reg_hour`
- 수식: `mem_reg_hour = reg_hour`
- 설명: 가입 시각 원값
- 유의 나이대: 10대, 20대, 30대, 40대, 60대
- 최대 절대상관: 0.263 (상대 변수: mem_reg_hour_morning)
- Centered VIF: 1.079
- 연령대별 검정 결과:
- 10대: p=0.0037414, effect_rbc=-0.1775, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=2.12776e-19, effect_rbc=-0.1301, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=7.15973e-16, effect_rbc=-0.1241, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=6.84461e-08, effect_rbc=-0.0812, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.0218858, effect_rbc=-0.1311, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_device_mobile_flag
- 분류: 멤버십 관련 파생변수
- 선택 등급: strong_common
- 사용 컬럼: `payment_device`
- 수식: `mem_device_mobile_flag = 1[payment_device = 'mobile']`
- 설명: mobile 기기 또는 채널 사용 여부
- 유의 나이대: 10대, 20대, 30대, 40대, 60대
- 최대 절대상관: 0.212 (상대 변수: mem_device_pc_flag)
- Centered VIF: 1.427
- 연령대별 검정 결과:
- 10대: p=0.00839822, effect_rbc=-0.1165, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=8.18414e-63, effect_rbc=-0.1825, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=6.03392e-33, effect_rbc=-0.1165, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=4.09739e-10, effect_rbc=-0.0420, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=7.02949e-05, effect_rbc=-0.1128, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_device_pc_flag
- 분류: 멤버십 관련 파생변수
- 선택 등급: strong_common
- 사용 컬럼: `payment_device`
- 수식: `mem_device_pc_flag = 1[payment_device = 'pc']`
- 설명: pc 기기 또는 채널 사용 여부
- 유의 나이대: 10대, 20대, 30대, 40대, 60대
- 최대 절대상관: 0.238 (상대 변수: mem_billing_method_151_flag)
- Centered VIF: 1.436
- 연령대별 검정 결과:
- 10대: p=0.00624722, effect_rbc=-0.1280, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=9.60969e-21, effect_rbc=-0.1036, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=2.73526e-07, effect_rbc=-0.0559, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=5.13553e-22, effect_rbc=-0.0769, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.0432056, effect_rbc=0.0851, 프로모션 그룹 평균 < 비참여 그룹 평균
### mem_tenure_days
- 분류: 멤버십 관련 파생변수
- 선택 등급: common_core
- 사용 컬럼: `reg_date, end_date`
- 수식: `mem_tenure_days = (end_date_dt - reg_date_dt).days`
- 설명: 가입 시작일부터 종료일까지의 멤버십 유지 일수
- 유의 나이대: 10대, 20대, 30대, 40대
- 최대 절대상관: 0.140 (상대 변수: mem_billing_method_140_flag)
- Centered VIF: 1.133
- 연령대별 검정 결과:
- 10대: p=4.12066e-09, effect_rbc=0.1301, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=1.92821e-235, effect_rbc=0.2211, 프로모션 그룹 평균 < 비참여 그룹 평균
- 30대: p=2.68155e-105, effect_rbc=0.1436, 프로모션 그룹 평균 < 비참여 그룹 평균
- 40대: p=0, effect_rbc=0.4808, 프로모션 그룹 평균 < 비참여 그룹 평균
- 60대: p=0.111843, effect_rbc=0.0296, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_verified_multi_screen
- 분류: 멤버십 관련 파생변수
- 선택 등급: common_core
- 사용 컬럼: `is_user_verified, max_screen`
- 수식: `mem_verified_multi_screen = 1[is_user_verified = 1] x 1[max_screen >= 2]`
- 설명: 인증 완료와 멀티 스크린 옵션 동시 충족 여부
- 유의 나이대: 10대, 20대, 30대, 40대
- 최대 절대상관: 0.618 (상대 변수: mem_verified_premium_screen)
- Centered VIF: 1.852
- 연령대별 검정 결과:
- 10대: p=0.00573233, effect_rbc=-0.1431, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=3.05883e-19, effect_rbc=-0.1092, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.00411044, effect_rbc=-0.0372, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=1.30267e-190, effect_rbc=-0.2633, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.24421, effect_rbc=-0.0554, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_billing_method_151_flag
- 분류: 멤버십 관련 파생변수
- 선택 등급: common_core
- 사용 컬럼: `billing_method`
- 수식: `mem_billing_method_151_flag = 1[billing_method = 151]`
- 설명: 청구 방식 코드 151 사용 여부
- 유의 나이대: 20대, 30대, 40대, 60대
- 최대 절대상관: 0.280 (상대 변수: mem_billing_method_134_flag)
- Centered VIF: 2.598
- 연령대별 검정 결과:
- 10대: p=0.0825443, effect_rbc=-0.0738, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=1.18194e-15, effect_rbc=-0.0737, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=3.9344e-17, effect_rbc=-0.0955, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=4.52447e-118, effect_rbc=-0.2324, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.00358082, effect_rbc=-0.1215, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_is_male
- 분류: 멤버십 관련 파생변수
- 선택 등급: common_core
- 사용 컬럼: `gender`
- 수식: `mem_is_male = 1[gender = 'M']`
- 설명: 남성 사용자 여부
- 유의 나이대: 20대, 30대, 40대, 60대
- 최대 절대상관: 0.237 (상대 변수: mem_is_verified)
- Centered VIF: 1.110
- 연령대별 검정 결과:
- 10대: p=0.910289, effect_rbc=-0.0058, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=1.28763e-06, effect_rbc=-0.0569, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.00209922, effect_rbc=-0.0402, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=9.52115e-138, effect_rbc=-0.2662, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.0449477, effect_rbc=0.0972, 프로모션 그룹 평균 < 비참여 그룹 평균
### vh_active_day_ratio
- 분류: 시청 이력 관련 파생변수
- 선택 등급: common_core
- 사용 컬럼: `watch_day, reg_date, end_date`
- 수식: `vh_active_day_ratio = vh_active_day_count / mem_tenure_days`
- 설명: 멤버십 기간 대비 실제 시청이 있었던 날짜 비율
- 유의 나이대: 20대, 30대, 40대, 60대
- 최대 절대상관: 0.513 (상대 변수: vh_gap_stability_index)
- Centered VIF: 1.996
- 연령대별 검정 결과:
- 10대: p=0.623461, effect_rbc=-0.0299, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.0126747, effect_rbc=-0.0358, 프로모션 그룹 평균 < 비참여 그룹 평균
- 30대: p=0.0138633, effect_rbc=-0.0376, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=1.26964e-09, effect_rbc=-0.0913, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.0498094, effect_rbc=-0.1112, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_device_smarttv_flag
- 분류: 멤버십 관련 파생변수
- 선택 등급: common_core
- 사용 컬럼: `payment_device`
- 수식: `mem_device_smarttv_flag = 1[payment_device = 'smarttv']`
- 설명: smarttv 기기 또는 채널 사용 여부
- 유의 나이대: 10대, 20대, 30대, 40대
- 최대 절대상관: 0.084 (상대 변수: mem_verified_multi_screen)
- Centered VIF: 1.070
- 연령대별 검정 결과:
- 10대: p=0.0230302, effect_rbc=0.0163, 프로모션 그룹 평균 < 비참여 그룹 평균
- 20대: p=2.231e-12, effect_rbc=0.0131, 프로모션 그룹 평균 < 비참여 그룹 평균
- 30대: p=1.35323e-05, effect_rbc=0.0148, 프로모션 그룹 평균 < 비참여 그룹 평균
- 40대: p=0.000100751, effect_rbc=0.0136, 프로모션 그룹 평균 < 비참여 그룹 평균
- 60대: p=0.180626, effect_rbc=0.0137, 프로모션 그룹 평균 < 비참여 그룹 평균
### mem_reg_weekday
- 분류: 멤버십 관련 파생변수
- 선택 등급: common_support
- 사용 컬럼: `reg_date`
- 수식: `mem_reg_weekday = weekday(reg_date_dt)`
- 설명: 가입 요일 숫자
- 유의 나이대: 10대, 20대, 30대
- 최대 절대상관: 0.046 (상대 변수: vh_week4_watch_ratio)
- Centered VIF: 1.010
- 연령대별 검정 결과:
- 10대: p=0.000991208, effect_rbc=-0.1992, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.000510135, effect_rbc=-0.0496, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=1.10661e-06, effect_rbc=-0.0740, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.516055, effect_rbc=-0.0097, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.306713, effect_rbc=-0.0578, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_billing_method_134_flag
- 분류: 멤버십 관련 파생변수
- 선택 등급: common_support
- 사용 컬럼: `billing_method`
- 수식: `mem_billing_method_134_flag = 1[billing_method = 134]`
- 설명: 청구 방식 코드 134 사용 여부
- 유의 나이대: 30대, 40대, 60대
- 최대 절대상관: 0.280 (상대 변수: mem_billing_method_151_flag)
- Centered VIF: 2.688
- 연령대별 검정 결과:
- 10대: p=0.89978, effect_rbc=-0.0065, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.996518, effect_rbc=0.0000, 프로모션 그룹 평균 < 비참여 그룹 평균
- 30대: p=0.0261958, effect_rbc=0.0261, 프로모션 그룹 평균 < 비참여 그룹 평균
- 40대: p=1.63068e-28, effect_rbc=-0.1130, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.000262848, effect_rbc=0.1630, 프로모션 그룹 평균 < 비참여 그룹 평균
### vh_end_near_watch_ratio
- 분류: 시청 이력 관련 파생변수
- 선택 등급: common_support
- 사용 컬럼: `watch_day, reg_date, end_date`
- 수식: `vh_end_near_watch_ratio = 1 - vh_last_watch_gap_ratio`
- 설명: 종료일에 가까운 시청 집중 정도
- 유의 나이대: 20대, 30대, 40대
- 최대 절대상관: 0.613 (상대 변수: vh_last_14d_watch_ratio)
- Centered VIF: 2.720
- 연령대별 검정 결과:
- 10대: p=0.247044, effect_rbc=-0.0709, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.027417, effect_rbc=-0.0318, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.000244581, effect_rbc=-0.0563, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.0102334, effect_rbc=-0.0387, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.285675, effect_rbc=-0.0610, 프로모션 그룹 평균 > 비참여 그룹 평균
### vh_gap_stability_index
- 분류: 시청 이력 관련 파생변수
- 선택 등급: common_support
- 사용 컬럼: `watch_day`
- 수식: `vh_gap_stability_index = 1 / (1 + vh_std_gap_days)`
- 설명: 시청 간격의 안정성 지수
- 유의 나이대: 20대, 40대, 60대
- 최대 절대상관: 0.513 (상대 변수: vh_active_day_ratio)
- Centered VIF: 1.418
- 연령대별 검정 결과:
- 10대: p=0.94175, effect_rbc=0.0044, 프로모션 그룹 평균 < 비참여 그룹 평균
- 20대: p=0.00510913, effect_rbc=-0.0394, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.0778959, effect_rbc=-0.0264, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.0290456, effect_rbc=-0.0321, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.0207885, effect_rbc=-0.1278, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_billing_method_190_flag
- 분류: 멤버십 관련 파생변수
- 선택 등급: common_support
- 사용 컬럼: `billing_method`
- 수식: `mem_billing_method_190_flag = 1[billing_method = 190]`
- 설명: 청구 방식 코드 190 사용 여부
- 유의 나이대: 20대, 30대, 40대
- 최대 절대상관: 0.175 (상대 변수: mem_device_mobile_flag)
- Centered VIF: 1.717
- 연령대별 검정 결과:
- 10대: p=0.217598, effect_rbc=-0.0426, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=1.94806e-14, effect_rbc=-0.0605, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=1.61125e-14, effect_rbc=-0.0595, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=3.44608e-07, effect_rbc=-0.0264, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.0737664, effect_rbc=-0.0368, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_billing_method_180_flag
- 분류: 멤버십 관련 파생변수
- 선택 등급: common_support
- 사용 컬럼: `billing_method`
- 수식: `mem_billing_method_180_flag = 1[billing_method = 180]`
- 설명: 청구 방식 코드 180 사용 여부
- 유의 나이대: 20대, 30대, 40대
- 최대 절대상관: 0.188 (상대 변수: mem_billing_method_134_flag)
- Centered VIF: 1.816
- 연령대별 검정 결과:
- 10대: p=0.359941, effect_rbc=-0.0327, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=4.14878e-15, effect_rbc=-0.0711, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.000362638, effect_rbc=-0.0270, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=5.41988e-06, effect_rbc=-0.0251, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.271067, effect_rbc=0.0264, 프로모션 그룹 평균 < 비참여 그룹 평균
### vh_last_14d_watch_ratio
- 분류: 시청 이력 관련 파생변수
- 선택 등급: common_support
- 사용 컬럼: `watch_day, watch_time(min), end_date`
- 수식: `vh_last_14d_watch_ratio = sum_i watch_time_i x 1[end_date_dt - watch_date_i <= 14] / sum_i watch_time_i`
- 설명: 전체 시청 시간 중 종료 14일 이내 시청 비중
- 유의 나이대: 20대, 30대, 40대
- 최대 절대상관: 0.613 (상대 변수: vh_end_near_watch_ratio)
- Centered VIF: 2.426
- 연령대별 검정 결과:
- 10대: p=0.327951, effect_rbc=-0.0578, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.0344873, effect_rbc=-0.0295, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.00227864, effect_rbc=-0.0453, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.00303706, effect_rbc=-0.0428, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.967897, effect_rbc=0.0022, 프로모션 그룹 평균 < 비참여 그룹 평균
### mem_billing_method_132_flag
- 분류: 멤버십 관련 파생변수
- 선택 등급: age_specific_exploratory
- 사용 컬럼: `billing_method`
- 수식: `mem_billing_method_132_flag = 1[billing_method = 132]`
- 설명: 청구 방식 코드 132 사용 여부
- 유의 나이대: 20대, 40대
- 최대 절대상관: 0.190 (상대 변수: mem_billing_method_134_flag)
- Centered VIF: 1.827
- 연령대별 검정 결과:
- 10대: p=0.953569, effect_rbc=0.0019, 프로모션 그룹 평균 < 비참여 그룹 평균
- 20대: p=0.00865438, effect_rbc=-0.0209, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.884011, effect_rbc=-0.0012, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=7.9083e-22, effect_rbc=-0.0643, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.0782297, effect_rbc=-0.0609, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_billing_method_170_flag
- 분류: 멤버십 관련 파생변수
- 선택 등급: age_specific_exploratory
- 사용 컬럼: `billing_method`
- 수식: `mem_billing_method_170_flag = 1[billing_method = 170]`
- 설명: 청구 방식 코드 170 사용 여부
- 유의 나이대: 10대, 20대
- 최대 절대상관: 0.082 (상대 변수: mem_device_mobile_flag)
- Centered VIF: 1.119
- 연령대별 검정 결과:
- 10대: p=0.00911268, effect_rbc=0.0294, 프로모션 그룹 평균 < 비참여 그룹 평균
- 20대: p=3.11897e-05, effect_rbc=-0.0137, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.874753, effect_rbc=-0.0004, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.48217, effect_rbc=-0.0016, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.199991, effect_rbc=0.0102, 프로모션 그룹 평균 < 비참여 그룹 평균
### mem_device_ott_flag
- 분류: 멤버십 관련 파생변수
- 선택 등급: age_specific_exploratory
- 사용 컬럼: `payment_device`
- 수식: `mem_device_ott_flag = 1[payment_device = 'ott']`
- 설명: ott 기기 또는 채널 사용 여부
- 유의 나이대: 20대, 30대
- 최대 절대상관: 0.050 (상대 변수: mem_verified_multi_screen)
- Centered VIF: 1.020
- 연령대별 검정 결과:
- 10대: p=1, effect_rbc=0.0000, 프로모션 그룹 평균 < 비참여 그룹 평균
- 20대: p=5.23964e-06, effect_rbc=0.0048, 프로모션 그룹 평균 < 비참여 그룹 평균
- 30대: p=1.07167e-06, effect_rbc=0.0088, 프로모션 그룹 평균 < 비참여 그룹 평균
- 40대: p=0.101441, effect_rbc=0.0029, 프로모션 그룹 평균 < 비참여 그룹 평균
- 60대: p=1, effect_rbc=0.0000, 프로모션 그룹 평균 < 비참여 그룹 평균
### vh_short_watch_ratio
- 분류: 시청 이력 관련 파생변수
- 선택 등급: age_specific_strong
- 사용 컬럼: `watch_time(min)`
- 수식: `vh_short_watch_ratio = (1 / N) x sum_i 1[watch_time_i <= 5]`
- 설명: 5분 이하 짧은 시청 이벤트 비중
- 유의 나이대: 20대
- 최대 절대상관: 0.303 (상대 변수: vh_recent_release_180d_ratio)
- Centered VIF: 1.169
- 연령대별 검정 결과:
- 10대: p=0.0620915, effect_rbc=-0.1132, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.0109259, effect_rbc=-0.0364, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.862823, effect_rbc=-0.0026, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.689805, effect_rbc=-0.0060, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.190089, effect_rbc=-0.0743, 프로모션 그룹 평균 > 비참여 그룹 평균
### vh_recent_release_180d_ratio
- 분류: 시청 이력 관련 파생변수
- 선택 등급: age_specific_strong
- 사용 컬럼: `watch_day, ott_release_month`
- 수식: `vh_recent_release_180d_ratio = (1 / N) x sum_i 1[0 <= (watch_date_i - release_date_i).days <= 180]`
- 설명: 최근 180일 이내 공개 작품 시청 비중
- 유의 나이대: 60대
- 최대 절대상관: 0.303 (상대 변수: vh_short_watch_ratio)
- Centered VIF: 1.243
- 연령대별 검정 결과:
- 10대: p=0.356746, effect_rbc=-0.0504, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.434808, effect_rbc=-0.0102, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.110573, effect_rbc=-0.0222, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.216784, effect_rbc=-0.0168, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.0233572, effect_rbc=-0.1185, 프로모션 그룹 평균 > 비참여 그룹 평균
### vh_multi_event_day_ratio
- 분류: 시청 이력 관련 파생변수
- 선택 등급: age_specific_exploratory
- 사용 컬럼: `watch_day, watch_seq`
- 수식: `vh_multi_event_day_ratio = (1 / D) x sum_d 1[events(d) >= 2]`
- 설명: 하루 2회 이상 시청한 날의 비중
- 유의 나이대: 40대
- 최대 절대상관: 0.158 (상대 변수: vh_week4_watch_min)
- Centered VIF: 1.060
- 연령대별 검정 결과:
- 10대: p=0.195553, effect_rbc=-0.0787, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.536926, effect_rbc=-0.0088, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.123973, effect_rbc=0.0234, 프로모션 그룹 평균 < 비참여 그룹 평균
- 40대: p=0.0307774, effect_rbc=0.0322, 프로모션 그룹 평균 < 비참여 그룹 평균
- 60대: p=0.220158, effect_rbc=-0.0694, 프로모션 그룹 평균 > 비참여 그룹 평균
### mem_reg_hour_afternoon
- 분류: 멤버십 관련 파생변수
- 선택 등급: age_specific_exploratory
- 사용 컬럼: `reg_hour`
- 수식: `mem_reg_hour_afternoon = 1[12 <= reg_hour <= 17]`
- 설명: 오후 시간대 가입 여부
- 유의 나이대: 20대
- 최대 절대상관: 0.274 (상대 변수: mem_reg_hour_morning)
- Centered VIF: 1.084
- 연령대별 검정 결과:
- 10대: p=0.119521, effect_rbc=-0.0696, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.000233503, effect_rbc=-0.0397, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.396171, effect_rbc=-0.0095, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.834618, effect_rbc=-0.0023, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.178962, effect_rbc=-0.0580, 프로모션 그룹 평균 > 비참여 그룹 평균
### vh_light_genre_share
- 분류: 시청 이력 관련 파생변수
- 선택 등급: age_specific_strong
- 사용 컬럼: `genre, watch_time(min)`
- 수식: `vh_light_genre_share = genre_share(Comedy) + genre_share(Animation_Family)`
- 설명: 가벼운 오락 계열 장르 시청 비중
- 유의 나이대: 60대
- 최대 절대상관: 0.254 (상대 변수: vh_tension_genre_share)
- Centered VIF: 1.178
- 연령대별 검정 결과:
- 10대: p=0.429685, effect_rbc=-0.0454, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.490224, effect_rbc=-0.0094, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.834231, effect_rbc=0.0030, 프로모션 그룹 평균 < 비참여 그룹 평균
- 40대: p=0.838516, effect_rbc=-0.0029, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.0293659, effect_rbc=-0.1174, 프로모션 그룹 평균 > 비참여 그룹 평균
### vh_w3_to_w1_ratio_capped
- 분류: 시청 이력 관련 파생변수
- 선택 등급: age_specific_strong
- 사용 컬럼: `watch_day, watch_time(min), reg_date`
- 수식: `vh_w3_to_w1_ratio_capped = min(10, vh_week3_watch_min / vh_week1_watch_min)`
- 설명: 3주차 대비 1주차 시청 강도 비율 상한값
- 유의 나이대: 60대
- 최대 절대상관: 0.250 (상대 변수: vh_std_gap_days)
- Centered VIF: 1.150
- 연령대별 검정 결과:
- 10대: p=0.429369, effect_rbc=-0.0433, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.934264, effect_rbc=-0.0011, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.540447, effect_rbc=0.0084, 프로모션 그룹 평균 < 비참여 그룹 평균
- 40대: p=0.443696, effect_rbc=-0.0103, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.0353092, effect_rbc=-0.1071, 프로모션 그룹 평균 > 비참여 그룹 평균
### vh_std_gap_days
- 분류: 시청 이력 관련 파생변수
- 선택 등급: age_specific_strong
- 사용 컬럼: `watch_day`
- 수식: `vh_std_gap_days = std(gap_days)`
- 설명: 연속 시청일 사이 간격의 표준편차
- 유의 나이대: 60대
- 최대 절대상관: 0.303 (상대 변수: vh_end_near_watch_ratio)
- Centered VIF: 1.256
- 연령대별 검정 결과:
- 10대: p=0.789332, effect_rbc=-0.0159, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.419869, effect_rbc=-0.0113, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.830893, effect_rbc=-0.0032, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.257607, effect_rbc=-0.0165, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.0393669, effect_rbc=-0.1132, 프로모션 그룹 평균 > 비참여 그룹 평균
### genre_share__Action_Adventure
- 분류: 시청 이력 관련 파생변수
- 선택 등급: age_specific_exploratory
- 사용 컬럼: `genre, watch_time(min)`
- 수식: `genre_share__Action_Adventure = sum_i watch_time_i x 1[genre_i = Action_Adventure] / sum_i watch_time_i`
- 설명: Action_Adventure 장르 시청 비중
- 유의 나이대: 40대
- 최대 절대상관: 0.240 (상대 변수: vh_recent_release_180d_ratio)
- Centered VIF: 1.188
- 연령대별 검정 결과:
- 10대: p=0.865543, effect_rbc=0.0091, 프로모션 그룹 평균 < 비참여 그룹 평균
- 20대: p=0.248416, effect_rbc=0.0144, 프로모션 그룹 평균 < 비참여 그룹 평균
- 30대: p=0.0684662, effect_rbc=-0.0243, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.0470291, effect_rbc=-0.0259, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.26269, effect_rbc=0.0541, 프로모션 그룹 평균 < 비참여 그룹 평균
### vh_nonfiction_genre_share
- 분류: 시청 이력 관련 파생변수
- 선택 등급: age_specific_exploratory
- 사용 컬럼: `genre, watch_time(min)`
- 수식: `vh_nonfiction_genre_share = genre_share(Documentary) + genre_share(Other)`
- 설명: 논픽션 또는 비정형 장르 시청 비중
- 유의 나이대: 20대
- 최대 절대상관: 0.173 (상대 변수: vh_recent_release_180d_ratio)
- Centered VIF: 1.131
- 연령대별 검정 결과:
- 10대: p=0.753411, effect_rbc=-0.0136, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.0285716, effect_rbc=-0.0229, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.389812, effect_rbc=0.0094, 프로모션 그룹 평균 < 비참여 그룹 평균
- 40대: p=0.665688, effect_rbc=-0.0047, 프로모션 그룹 평균 > 비참여 그룹 평균
- 60대: p=0.116251, effect_rbc=-0.0660, 프로모션 그룹 평균 > 비참여 그룹 평균
### vh_week4_watch_ratio
- 분류: 시청 이력 관련 파생변수
- 선택 등급: age_specific_exploratory
- 사용 컬럼: `watch_day, watch_time(min), reg_date`
- 수식: `vh_week4_watch_ratio = vh_week4_watch_min / vh_total_watch_min`
- 설명: 전체 시청 시간 중 4주차 시청 비중
- 유의 나이대: 30대
- 최대 절대상관: 0.604 (상대 변수: vh_last_14d_watch_ratio)
- Centered VIF: 2.190
- 연령대별 검정 결과:
- 10대: p=0.490742, effect_rbc=-0.0315, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.690476, effect_rbc=-0.0044, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.0109452, effect_rbc=-0.0293, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.414938, effect_rbc=0.0093, 프로모션 그룹 평균 < 비참여 그룹 평균
- 60대: p=0.57383, effect_rbc=-0.0244, 프로모션 그룹 평균 > 비참여 그룹 평균
### vh_week4_watch_min
- 분류: 시청 이력 관련 파생변수
- 선택 등급: age_specific_exploratory
- 사용 컬럼: `watch_day, watch_time(min), reg_date`
- 수식: `vh_week4_watch_min = sum_i watch_time_i x 1[week_index_i = 4]`
- 설명: 가입 후 4주차 누적 시청 시간
- 유의 나이대: 30대
- 최대 절대상관: 0.540 (상대 변수: vh_week4_watch_ratio)
- Centered VIF: 1.576
- 연령대별 검정 결과:
- 10대: p=0.473662, effect_rbc=-0.0328, 프로모션 그룹 평균 > 비참여 그룹 평균
- 20대: p=0.845364, effect_rbc=-0.0022, 프로모션 그룹 평균 < 비참여 그룹 평균
- 30대: p=0.0132457, effect_rbc=-0.0286, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.373046, effect_rbc=0.0101, 프로모션 그룹 평균 < 비참여 그룹 평균
- 60대: p=0.645978, effect_rbc=-0.0199, 프로모션 그룹 평균 > 비참여 그룹 평균
### vh_tension_genre_share
- 분류: 시청 이력 관련 파생변수
- 선택 등급: age_specific_exploratory
- 사용 컬럼: `genre, watch_time(min)`
- 수식: `vh_tension_genre_share = genre_share(Thriller_Crime) + genre_share(Horror)`
- 설명: 긴장감 계열 장르 시청 비중
- 유의 나이대: 30대
- 최대 절대상관: 0.254 (상대 변수: vh_light_genre_share)
- Centered VIF: 1.162
- 연령대별 검정 결과:
- 10대: p=0.732778, effect_rbc=0.0191, 프로모션 그룹 평균 < 비참여 그룹 평균
- 20대: p=0.743572, effect_rbc=-0.0043, 프로모션 그룹 평균 > 비참여 그룹 평균
- 30대: p=0.0212267, effect_rbc=-0.0326, 프로모션 그룹 평균 > 비참여 그룹 평균
- 40대: p=0.770059, effect_rbc=0.0040, 프로모션 그룹 평균 < 비참여 그룹 평균
- 60대: p=0.726302, effect_rbc=0.0180, 프로모션 그룹 평균 < 비참여 그룹 평균

## 8. 생성 파일
- `260512_derived_user_features_0.csv`: 프로모션 비참여 그룹 사용자 단위 데이터
- `260512_derived_user_features_1.csv`: 프로모션 참여 그룹 사용자 단위 데이터
- `260512_derived_feature_summary.csv`: 파생변수 간략 설명 CSV
- `260512_derived_feature_explanation.md`: 파생변수 상세 설명 문서
