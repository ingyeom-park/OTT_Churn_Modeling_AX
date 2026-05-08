# 260507 View History 파생변수 설명

## 1. 목적

이 문서는 아래 두 파일의 `view_history` row를 `membership` 형태로 집계할 때 사용할 파생변수를 정리한 문서입니다.

- `260507_merged1_0.csv`: 프로모션 비참여 그룹
- `260507_merged1_1.csv`: 프로모션 참여 그룹

최종 집계 단위는 `USER_NUM` 하나가 아니라 `(group, USER_NUM)` 조합입니다.  
두 파일 사이에 `USER_NUM`이 겹치는 값이 있으므로, 두 파일을 합친 뒤 `USER_NUM`만 키로 쓰면 다른 사용자가 섞입니다.

## 2. 집계 원칙

- 사용자 키: `(group, USER_NUM)`
- 모델링용 시청이력 범위: `reg_date <= watch_day <= end_date`
- 제외 권장 컬럼: `product_code`, `billing_method`, `USER_KEY`, `is_promotion`
- `USER_NUM`: 모델 입력에서는 제외, 파생변수 집계 키로만 사용
- `vh_has_safe_watch`: 데이터 정합성 확인용 변수, 본 모델 변수로는 제외 권장

## 3. 컬럼 구분

### 3.1 Membership 성격 컬럼

한 사용자 내부에서 값이 변하지 않는 컬럼입니다.

- `USER_KEY`
- `age`
- `billing_method`
- `end_date`
- `gender`
- `is_churn_prevented`
- `is_promotion`
- `is_repurchase`
- `is_user_verified`
- `max_screen`
- `payment_device`
- `price`
- `product_code`
- `reg_date`
- `reg_hour`

### 3.2 View History 성격 컬럼

한 사용자 내부에서 값이 변할 수 있는 컬럼입니다.

- `MOVIE_NUM`
- `movie_title`
- `watch_time(min)`
- `showTM`
- `ott_release_month`
- `genre`
- `watch_seq`
- `country`
- `watch_day`

## 4. 기본 기호

사용자 `u`에 대해 아래 기호를 사용합니다.

- `N_u`: 사용자 `u`의 시청 row 수
- `M_u`: 사용자 `u`의 유니크 콘텐츠 수
- `T_u`: `end_date_u - reg_date_u`
- `w_{u,i}`: 사용자 `u`의 `i`번째 row 시청시간
- `d_{u,i}`: 사용자 `u`의 `i`번째 시청일
- `r_{u,i}`: 사용자 `u`의 `i`번째 콘텐츠 러닝타임
- `L_u`: 사용자 `u`의 마지막 시청일
- `R_{u,i}`: `i`번째 시청 콘텐츠의 공개일 대비 경과일수

## 5. 핵심 파생변수 설명

### 5.1 시청 강도 계열

- `vh_event_count`
  수식: `N_u`
  설명: 전체 시청 row 수
  해석: 클수록 시청 행동이 자주 기록된 사용자

- `vh_title_count`
  수식: `M_u`
  설명: 유니크 콘텐츠 수
  해석: 클수록 여러 작품을 넓게 본 사용자

- `vh_event_per_tenure_day`
  수식: `N_u / T_u`
  설명: 가입 유지 기간 1일당 시청 row 수
  해석: 클수록 시청 빈도가 높음
  사용 포인트: 30대에서 churn 사용자와 repurchase 사용자 구분에 유효

- `vh_watch_min_per_tenure_day`
  수식: `(Σ_i w_{u,i}) / T_u`
  설명: 가입 유지 기간 1일당 평균 시청시간
  해석: 클수록 일평균 소비량이 큼
  사용 포인트: 30대 churn 구분에 유효

- `vh_watch_min_per_active_day`
  수식: `(Σ_i w_{u,i}) / active_day_count_u`
  설명: 실제 시청한 날짜 기준 일평균 시청시간
  해석: 클수록 시청한 날에는 몰아서 보는 성향
  사용 포인트: 50대에서 그룹 차이 확인

### 5.2 만기 근접 시청 계열

- `vh_last_watch_gap`
  수식: `end_date_u - L_u`
  설명: 마지막 시청일과 만기일 사이의 공백 일수
  해석: 작을수록 만기 직전까지 본 사용자
  사용 포인트: 20대, 30대에서 그룹 차이와 churn 차이가 모두 확인됨

- `vh_last_watch_gap_ratio`
  수식: `vh_last_watch_gap / T_u`
  설명: 만기 전 공백을 가입 기간으로 정규화한 비율
  해석: 작을수록 만기 직전까지 꾸준히 본 사용자
  사용 포인트: 20대, 30대에서 유효

- `vh_last_7d_watch_ratio`
  수식: `(Σ_i w_{u,i} * 1[end_date_u - d_{u,i} <= 7]) / (Σ_i w_{u,i})`
  설명: 전체 시청시간 중 만기 직전 7일에 몰린 비중
  해석: 클수록 만기 직전 시청 집중도가 높음
  사용 포인트: 20대, 30대, 50대에서 churn 분리력이 큼

- `vh_last_14d_watch_ratio`
  수식: `(Σ_i w_{u,i} * 1[end_date_u - d_{u,i} <= 14]) / (Σ_i w_{u,i})`
  설명: 전체 시청시간 중 만기 직전 14일 비중
  해석: 클수록 후반부 시청 집중도가 높음
  사용 포인트: 20대에서 보조 변수로 사용 가능

- `vh_first_half_watch_ratio`
  수식: `(Σ_i w_{u,i} * 1[(d_{u,i} - reg_date_u)/T_u <= 0.5]) / (Σ_i w_{u,i})`
  설명: 전체 시청시간 중 가입 초반 절반 구간 비중
  해석: 클수록 초반 몰아보기 성향
  사용 포인트: 30대에서 그룹 차이 확인

### 5.3 완주/샘플링 계열

- `vh_mean_event_completion`
  수식: `mean_i(min(w_{u,i} / r_{u,i}, 2))`
  설명: row 단위 평균 완주율
  해석: 클수록 한 번 시청할 때 더 길게 보는 경향
  사용 포인트: 50대에서 그룹 차이 확인

- `vh_high_completion_event_ratio`
  수식: `mean_i(1[w_{u,i} / r_{u,i} >= 0.7])`
  설명: 70% 이상 본 row 비율
  해석: 클수록 완주 성향이 강함
  사용 포인트: 50대에서 프로모션 참여군이 더 높음

- `vh_low_completion_event_ratio`
  수식: `mean_i(1[w_{u,i} / r_{u,i} <= 0.1])`
  설명: 10% 이하만 보고 끝난 row 비율
  해석: 클수록 클릭 후 바로 이탈하는 소비가 많음
  사용 포인트: 50대 churn 구분에 강함

- `vh_short_sample_ratio`
  수식: `mean_i(1[w_{u,i} <= 5])`
  설명: 5분 이하 시청 row 비율
  해석: 클수록 짧게 찍어보고 나가는 행동이 많음
  사용 포인트: 50대 churn 구분에 강함

- `vh_completed_title_ratio_80`
  수식: `mean_j(1[title_watch_min_{u,j} / title_runtime_{u,j} >= 0.8])`
  설명: 작품 단위 누적 시청시간이 러닝타임의 80% 이상인 작품 비율
  해석: 클수록 실제 작품 완주 비율이 높음
  사용 포인트: 20대 그룹 분리에 유효

- `vh_rewatch_event_ratio`
  수식: `(N_u - M_u) / N_u`
  설명: 동일 작품 재시청 row 비율
  해석: 클수록 같은 작품을 여러 번 나누어 보거나 다시 보는 비중이 큼
  사용 포인트: 50대 churn 구분에 유효

### 5.4 최신작 선호 계열

- `vh_recent_release_180d_ratio`
  수식: `mean_i(1[0 <= R_{u,i} <= 180])`
  설명: 공개 후 180일 이내 콘텐츠 시청 비율
  해석: 클수록 최신작 선호가 강함
  사용 포인트: 50대에서 그룹 차이와 churn 차이가 함께 나타남

- `vh_recent_release_365d_ratio`
  수식: `mean_i(1[0 <= R_{u,i} <= 365])`
  설명: 공개 후 1년 이내 콘텐츠 시청 비율
  해석: 클수록 최신작 중심 소비
  사용 포인트: 50대에서 특히 중요

### 5.5 장르 선호 계열

- `genre_share__X`
  수식: `(Σ_i w_{u,i} * 1[X ∈ genre_i]) / (Σ_i w_{u,i})`
  설명: 전체 시청시간 중 장르 `X`가 포함된 콘텐츠의 비중
  해석: 클수록 해당 장르 선호가 강함

연령대별로 우선순위가 높았던 장르는 아래와 같습니다.

- 20대: `genre_share__스릴러`, `genre_share__가족`, `genre_share__판타지`
- 30대: `genre_share__범죄`, `genre_share__액션`, `genre_share__SF`
- 50대: `genre_share__코미디`

### 5.6 국가 선호 계열

- `country_share__X`
  수식: `(Σ_i w_{u,i} * 1[X ∈ country_i]) / (Σ_i w_{u,i})`
  설명: 전체 시청시간 중 국가 `X`가 포함된 콘텐츠 비중
  해석: 클수록 해당 국가 제작 콘텐츠 선호가 강함

주의사항:

- `country`는 복수 국가가 한 셀에 함께 들어가는 경우가 있어 분해 후 집계해야 함
- 표본이 작은 국가 비중 변수는 과적합 위험이 있어 보조 변수로만 권장

## 6. 연령대별 추천 파생변수

### 6.1 20대 추천

20대는 프로모션 참여군의 churn rate가 더 높았고, 만기 직전 시청 패턴과 장르 선호가 차이를 만들었습니다.

- `vh_last_7d_watch_ratio`
  그룹 차이: 참여군 `0.0008`, 비참여군 `0.0073`
  churn 차이: churn `0.0073`, repurchase `0.0000`
  해석: 만기 직전 7일 집중 시청은 churn 사용자 쪽에서 더 큼

- `vh_last_watch_gap`
  그룹 차이: 참여군 `15.39`, 비참여군 `15.79`
  churn 차이: churn `15.29`, repurchase `15.68`
  해석: churn 사용자가 오히려 만기 직전까지 시청 흔적을 남기는 패턴

- `vh_last_watch_gap_ratio`
  그룹 차이: 참여군 `0.4966`, 비참여군 `0.5064`
  churn 차이: churn `0.4928`, repurchase `0.5044`
  해석: 절대 일수보다 비율로 정규화해도 같은 방향

- `genre_share__스릴러`
  그룹 차이: 참여군 `0.1417`, 비참여군 `0.1538`
  churn 차이: churn `0.1430`, repurchase `0.1476`
  해석: 스릴러 비중이 낮은 쪽이 참여군과 연결되는 경향

- `vh_completed_title_ratio_80`
  그룹 차이: 참여군 `0.4199`, 비참여군 `0.3944`
  해석: 참여군이 작품 단위 완주 비율은 조금 더 높음
  주의: churn 직접 연결성은 약하므로 보조 변수로 사용 권장

- `vh_mean_runtime_min`
  그룹 차이: 참여군 `106.98`, 비참여군 `107.89`
  churn 차이: churn `106.57`, repurchase `107.75`
  해석: 상대적으로 짧은 러닝타임 콘텐츠 소비가 churn 쪽과 연결될 가능성

### 6.2 30대 추천

30대는 활동량 자체보다, 만기 근접 패턴과 범죄/액션 성향이 churn 구분에 더 유효했습니다.

- `vh_last_watch_gap`
  그룹 차이: 참여군 `15.22`, 비참여군 `15.67`
  churn 차이: churn `15.09`, repurchase `15.52`
  해석: 30대도 churn 사용자가 만기 직전 시청 흔적을 더 남김

- `vh_last_watch_gap_ratio`
  그룹 차이: 참여군 `0.4915`, 비참여군 `0.5048`
  churn 차이: churn `0.4892`, repurchase `0.4996`
  해석: 가입 기간 길이 차이를 제거해도 동일한 방향

- `vh_watch_min_per_tenure_day`
  그룹 차이: 참여군 `10.79`, 비참여군 `10.33`
  churn 차이: churn `12.16`, repurchase `10.02`
  해석: 30대 churn 사용자는 기간 대비 더 많이 봄

- `vh_event_per_tenure_day`
  그룹 차이: 참여군 `0.2439`, 비참여군 `0.2363`
  churn 차이: churn `0.2638`, repurchase `0.2322`
  해석: row 빈도가 높은 사용자가 churn 쪽에 가까움

- `genre_share__범죄`
  churn 차이: churn `0.1211`, repurchase `0.1071`
  해석: 범죄 장르 비중이 높은 30대는 churn 쪽으로 더 치우침

- `genre_share__액션`
  churn 차이: churn `0.1877`, repurchase `0.1723`
  해석: 액션 장르 비중도 같은 방향

- `vh_recent_release_365d_ratio`
  그룹 차이: 참여군 `0.2670`, 비참여군 `0.2444`
  해석: 참여군은 최신작 소비 비중이 더 높음
  주의: churn 직접 연결성은 약하므로 그룹 분리 보조 변수로 사용 권장

### 6.3 50대 추천

50대는 최신작 선호, 짧은 샘플링, 낮은 완주율이 가장 강한 축이었습니다.

- `vh_recent_release_365d_ratio`
  그룹 차이: 참여군 `0.2472`, 비참여군 `0.2980`
  churn 차이: churn `0.2984`, repurchase `0.2493`
  해석: 최신작 비중이 높을수록 churn 쪽으로 가까움

- `vh_recent_release_180d_ratio`
  그룹 차이: 참여군 `0.1986`, 비참여군 `0.2438`
  churn 차이: churn `0.2412`, repurchase `0.2018`
  해석: 특히 6개월 이내 최신작 선호가 churn 신호로 작동

- `vh_short_sample_ratio`
  그룹 차이: 참여군 `0.3278`, 비참여군 `0.3595`
  churn 차이: churn `0.3761`, repurchase `0.3224`
  해석: 짧게 찍어보기 비율이 높을수록 churn 위험 증가

- `vh_low_completion_event_ratio`
  그룹 차이: 참여군 `0.3885`, 비참여군 `0.4111`
  churn 차이: churn `0.4334`, repurchase `0.3803`
  해석: 클릭 후 초반 이탈이 많은 사용자가 churn 쪽

- `vh_rewatch_event_ratio`
  그룹 차이: 참여군 `0.2147`, 비참여군 `0.2266`
  churn 차이: churn `0.2445`, repurchase `0.2079`
  해석: 같은 작품을 여러 row로 소비하는 패턴이 churn 쪽에서 큼

- `vh_mean_event_completion`
  그룹 차이: 참여군 `0.4500`, 비참여군 `0.4084`
  해석: 참여군은 한 row 기준으로는 더 길게 보는 경향
  주의: churn 직접 연결성은 약하므로 그룹 분리 보조 변수로 사용 권장

- `vh_avg_watch_min`
  그룹 차이: 참여군 `47.02`, 비참여군 `42.93`
  해석: 참여군은 한 번 볼 때 더 길게 보는 경향
  주의: churn 직접 연결성은 약함

- `vh_high_completion_event_ratio`
  그룹 차이: 참여군 `0.3271`, 비참여군 `0.2811`
  해석: 참여군은 높은 완주 row 비율이 더 큼
  주의: churn 직접 연결성은 약함

## 7. 최종 모델 입력 권장안

### 7.1 공통 코어 변수

아래 변수는 세 연령대를 공통으로 깔고 가는 것이 좋습니다.

- `vh_event_per_tenure_day`
- `vh_watch_min_per_tenure_day`
- `vh_last_watch_gap`
- `vh_last_watch_gap_ratio`
- `vh_last_7d_watch_ratio`
- `vh_last_14d_watch_ratio`
- `vh_mean_event_completion`
- `vh_low_completion_event_ratio`
- `vh_short_sample_ratio`
- `vh_rewatch_event_ratio`
- `vh_recent_release_180d_ratio`
- `vh_recent_release_365d_ratio`

### 7.2 연령대 상호작용 변수

나이대별로 아래 상호작용을 붙이는 것을 권장합니다.

- 20대: `age20 * genre_share__스릴러`
- 20대: `age20 * vh_completed_title_ratio_80`
- 20대: `age20 * vh_last_7d_watch_ratio`
- 30대: `age30 * genre_share__범죄`
- 30대: `age30 * genre_share__액션`
- 30대: `age30 * vh_watch_min_per_tenure_day`
- 50대: `age50 * vh_recent_release_365d_ratio`
- 50대: `age50 * vh_short_sample_ratio`
- 50대: `age50 * vh_low_completion_event_ratio`

## 8. 사용 시 주의사항

- `watch_day > end_date`인 row는 제외 후 파생 생성 필요
- `watch_day < reg_date`인 row도 제외 필요
- `country_share__*`는 표본이 적은 국가는 불안정할 수 있어 1차 모델에서는 후순위 권장
- count 계열과 시간 계열은 `log1p` 변환을 함께 검토 권장
- 장르 비중 변수는 합이 1이 되는 구조가 아니므로 다중공선성 확인 필요

## 9. 산출물 경로

- 사용자 단위 파생 테이블: `kim.kwangil/derived_variable/260507_user_features.csv`
- 그룹 차이 테이블: `kim.kwangil/derived_variable/260507_group_diff_by_age.csv`
- churn 차이 테이블: `kim.kwangil/derived_variable/260507_churn_diff_by_age.csv`
- 우선순위 테이블: `kim.kwangil/derived_variable/260507_feature_priority_by_age.csv`
- 생성 스크립트: `kim.kwangil/derived_variable/260507_view_history_feature_analysis.py`
