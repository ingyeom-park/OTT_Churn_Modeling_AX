# 260517 파생변수 설명

## 생성 파일
- CSV: `C:\myCode\ott-churn-prediction\kim.kwangil\derived_variable\260517_derived_membership_age_specific.csv`
- MD: `C:\myCode\ott-churn-prediction\kim.kwangil\derived_variable\260517_derived_feature_explanation.md`

## 사용 원천 파일
- 시청 이력 원천: `C:\myCode\ott-churn-prediction\kim.kwangil\data\260509_merged1_0.csv`
- 시청 이력 원천: `C:\myCode\ott-churn-prediction\kim.kwangil\data\260509_merged1_1.csv`
- 베이스 파일: `C:\myCode\ott-churn-prediction\kim.kwangil\derived_variable\260513_derived_membership.csv`
- 나이대 비교 기준 참고: `260513_derived_EDA.ipynb`

## 이번 설계 기준
- `20대`, `30대`, `40대`에서 해석이 바로 되는 직관적인 시청 행동 패턴을 우선 설계함
- `is_user_verified` 및 그 직접 파생 변수는 새로 만들지 않음
- 컬럼명에 나이대 숫자나 `vh` 같은 접두사를 넣지 않음
- 단순 곱셈형 상호작용은 제외함
- 기존 원본 컬럼이나 기존 파생변수와 결이 다른, 시청 순서와 하루 단위 구조 중심의 새 변수를 설계함
- 이번 버전은 요청에 따라 `VIF`는 고려하지 않음
- 유의한 나이대에서는 두 그룹 모두 0이 아닌 값이 실제로 존재하는 경우만 채택함

## 병합 기준
- 두 시청 이력 파일을 세로 결합한 뒤 파생변수를 생성함
- `USER_NUM` 단독 기준으로는 멤버십 상태가 섞이는 경우가 있어 그대로 쓰지 않음
- 복수 멤버십 상태와 연결된 `USER_NUM` 수: `44`
- 아래 원본 멤버십 조합 전체를 키로 사용해 집계 및 병합함
- `USER_KEY`
- `product_code`
- `price`
- `billing_method`
- `max_screen`
- `is_promotion`
- `is_churn_prevented`
- `payment_device`
- `is_user_verified`
- `gender`
- `age`
- `reg_date`
- `reg_hour`
- `end_date`
- `is_repurchase`

## 최종 CSV 구조
- 행 수: `23,343`
- 열 수: `98`
- 신규 파생변수 수: `7`
- 원시 시청 이력과 직접 매칭된 행 수: `23,215`
- 원시 시청 이력과 직접 매칭되지 않은 행 수: `128`
- 직접 매칭되지 않은 행의 신규 시청 변수값은 `0`으로 채움

## 신규 파생변수 목록
- `genre_switch_rate`
- `fast_drop_title_ratio`
- `multi_genre_binge_day_ratio`
- `multi_title_binge_day_ratio`
- `single_genre_binge_day_ratio`
- `mixed_length_day_ratio`
- `mixed_length_multi_title_day_ratio`

## 변수별 상세 설명

### 1. `genre_switch_rate`
- 사용 원천 컬럼: `watch_day`, `watch_seq`, `category`
- 의미: 연속된 시청 이벤트 사이에서 장르가 바뀌는 비율
- 새로 보는 패턴: 한 콘텐츠에 머무르기보다 장르를 자주 바꾸며 보는 패턴
- 수식:

```text
N = 사용자 시청 이벤트 수
I(category_t != category_(t-1)) = 연속 두 이벤트의 장르가 다르면 1, 같으면 0
genre_switch_rate = [Σ_t I(category_t != category_(t-1))] / (N - 1)
```

- 유의 나이대: `20대`, `30대`
- `20대`: p-value `0.046548`, 비프로모션 평균 `0.503985`, 프로모션 평균 `0.522614`, 비영값 수 `1836 / 3834`
- `30대`: p-value `0.047609`, 비프로모션 평균 `0.504282`, 프로모션 평균 `0.522388`, 비영값 수 `1801 / 2812`

### 2. `fast_drop_title_ratio`
- 사용 원천 컬럼: `MOVIE_NUM`, `watch_time(min)`
- 의미: 한 번만 보고 끝났고, 총 시청시간도 5분 미만인 작품의 비율
- 새로 보는 패턴: 짧게 찍어보고 바로 이탈하는 작품 소비 패턴
- 수식:

```text
M = 사용자가 본 전체 작품 수
D_m = 작품 m의 총 시청시간
E_m = 작품 m의 시청 이벤트 수
I(E_m = 1 and D_m < 5) = 조건 충족 시 1, 아니면 0
fast_drop_title_ratio = [Σ_m I(E_m = 1 and D_m < 5)] / M
```

- 유의 나이대: `20대`, `30대`
- `20대`: p-value `0.018879`, 비프로모션 평균 `0.215863`, 프로모션 평균 `0.232340`, 비영값 수 `1232 / 2605`
- `30대`: p-value `0.031969`, 비프로모션 평균 `0.224616`, 프로모션 평균 `0.239490`, 비영값 수 `1223 / 1971`

### 3. `multi_genre_binge_day_ratio`
- 사용 원천 컬럼: `watch_day`, `category`
- 의미: 활동일 중 `3회 이상` 시청하면서 `2개 이상` 장르를 본 날의 비율
- 새로 보는 패턴: 하루에 여러 번 몰입해서 보면서도 장르를 넓게 탐색하는 패턴
- 수식:

```text
D = 사용자의 활동일 집합
E_d = 활동일 d의 시청 이벤트 수
C_d = 활동일 d의 고유 장르 수
I(E_d >= 3 and C_d >= 2) = 조건 충족 시 1, 아니면 0
multi_genre_binge_day_ratio = [Σ_d I(E_d >= 3 and C_d >= 2)] / |D|
```

- 유의 나이대: `20대`
- `20대`: p-value `0.004066`, 비프로모션 평균 `0.711538`, 프로모션 평균 `0.743324`, 비영값 수 `1702 / 3591`

### 4. `multi_title_binge_day_ratio`
- 사용 원천 컬럼: `watch_day`, `MOVIE_NUM`
- 의미: 활동일 중 `3회 이상` 시청하면서 `2개 이상` 작품을 본 날의 비율
- 새로 보는 패턴: 하루 안에서 여러 작품을 오가며 길게 소비하는 패턴
- 수식:

```text
D = 사용자의 활동일 집합
E_d = 활동일 d의 시청 이벤트 수
M_d = 활동일 d의 고유 작품 수
I(E_d >= 3 and M_d >= 2) = 조건 충족 시 1, 아니면 0
multi_title_binge_day_ratio = [Σ_d I(E_d >= 3 and M_d >= 2)] / |D|
```

- 유의 나이대: `20대`
- `20대`: p-value `0.005680`, 비프로모션 평균 `0.743311`, 프로모션 평균 `0.772718`, 비영값 수 `1778 / 3733`

### 5. `single_genre_binge_day_ratio`
- 사용 원천 컬럼: `watch_day`, `category`
- 의미: 활동일 중 `3회 이상` 시청하면서도 `1개` 장르 안에 머문 날의 비율
- 새로 보는 패턴: 하루에 몰입해서 보되 장르는 넓히지 않고 한 장르에 머무는 패턴
- 수식:

```text
D = 사용자의 활동일 집합
E_d = 활동일 d의 시청 이벤트 수
C_d = 활동일 d의 고유 장르 수
I(E_d >= 3 and C_d = 1) = 조건 충족 시 1, 아니면 0
single_genre_binge_day_ratio = [Σ_d I(E_d >= 3 and C_d = 1)] / |D|
```

- 유의 나이대: `30대`
- `30대`: p-value `0.000512`, 비프로모션 평균 `0.069628`, 프로모션 평균 `0.048247`, 비영값 수 `163 / 172`

### 6. `mixed_length_day_ratio`
- 사용 원천 컬럼: `watch_day`, `watch_time(min)`
- 의미: 같은 날에 짧은 시청과 긴 시청이 함께 나타난 날의 비율
- 새로 보는 패턴: 하루 안에서 가볍게 찍어보는 행동과 오래 보는 행동이 같이 나타나는 혼합 시청 패턴
- 수식:

```text
D = 사용자의 활동일 집합
S_d = 활동일 d에 watch_time(min) < 5 인 이벤트가 하나라도 있으면 1
L_d = 활동일 d에 watch_time(min) >= 20 인 이벤트가 하나라도 있으면 1
I(S_d = 1 and L_d = 1) = 조건 충족 시 1, 아니면 0
mixed_length_day_ratio = [Σ_d I(S_d = 1 and L_d = 1)] / |D|
```

- 유의 나이대: `20대`, `40대`
- `20대`: p-value `0.016632`, 비프로모션 평균 `0.579013`, 프로모션 평균 `0.608363`, 비영값 수 `1385 / 2939`
- `40대`: p-value `0.044760`, 비프로모션 평균 `0.586020`, 프로모션 평균 `0.611735`, 비영값 수 `3454 / 1199`

### 7. `mixed_length_multi_title_day_ratio`
- 사용 원천 컬럼: `watch_day`, `watch_time(min)`, `MOVIE_NUM`
- 의미: 같은 날에 짧은 시청과 긴 시청이 함께 나타나고, 동시에 `2개 이상` 작품을 본 날의 비율
- 새로 보는 패턴: 하루 안에서 여러 작품을 오가며 짧은 시청과 긴 시청이 섞이는 혼합 탐색 패턴
- 수식:

```text
D = 사용자의 활동일 집합
S_d = 활동일 d에 watch_time(min) < 5 인 이벤트가 하나라도 있으면 1
L_d = 활동일 d에 watch_time(min) >= 20 인 이벤트가 하나라도 있으면 1
M_d = 활동일 d의 고유 작품 수
I(S_d = 1 and L_d = 1 and M_d >= 2) = 조건 충족 시 1, 아니면 0
mixed_length_multi_title_day_ratio = [Σ_d I(S_d = 1 and L_d = 1 and M_d >= 2)] / |D|
```

- 유의 나이대: `20대`, `40대`
- `20대`: p-value `0.005144`, 비프로모션 평균 `0.552676`, 프로모션 평균 `0.587249`, 비영값 수 `1322 / 2837`
- `40대`: p-value `0.032913`, 비프로모션 평균 `0.563794`, 프로모션 평균 `0.591327`, 비영값 수 `3323 / 1159`

## 해석 메모
- `20대`에서는 장르를 자주 바꾸거나, 하루에 여러 장르와 여러 작품을 오가며 binge하는 패턴이 프로모션 참여군에서 더 높게 나타났음
- `30대`에서는 장르 전환과 짧게 찍어보고 끝내는 작품 비중이 프로모션 참여군에서 더 높았고, 반대로 한 장르에 머무는 binge 패턴은 더 낮았음
- `40대`에서는 짧은 시청과 긴 시청이 같은 날에 섞여 나타나는 혼합 시청 패턴이 프로모션 참여군에서 더 높았음
