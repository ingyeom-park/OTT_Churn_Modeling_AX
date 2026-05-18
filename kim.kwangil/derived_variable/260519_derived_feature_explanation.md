# 260519 파생변수 설명

## 생성 파일
- CSV: `C:\myCode\ott-churn-prediction\kim.kwangil\derived_variable\260519_derived_membership_age_specific.csv`
- MD: `C:\myCode\ott-churn-prediction\kim.kwangil\derived_variable\260519_derived_feature_explanation.md`

## 사용 원천 파일
- 시청 이력 원천: `C:\myCode\ott-churn-prediction\kim.kwangil\data\260509_merged1_0.csv`
- 시청 이력 원천: `C:\myCode\ott-churn-prediction\kim.kwangil\data\260509_merged1_1.csv`
- 베이스 파생 파일: `C:\myCode\ott-churn-prediction\kim.kwangil\derived_variable\260517_derived_membership_age_specific.csv`
- 나이대 유의성 기준 참고: `C:\myCode\ott-churn-prediction\kim.kwangil\EDA\260513_derived_EDA.ipynb`

## 이번 버전의 설계 기준
- `260517`에서 이미 설명하고 있는 장르 전환, binge, 혼합 길이 중심 변수와 겹치지 않도록 시청 흐름의 시작점, 다음 활성 시청일로의 이어짐, 작품 생애주기 패턴을 중심으로 다시 설계함
- `260518`에서 탐색했던 순서형 변수도 다시 재검토하고, 최종적으로는 실제 유의성이 다시 확인된 변수만 남김
- `is_user_verified` 및 그 직접 파생 변수는 신규 생성 대상에서 제외함
- 컬럼명에 나이대 숫자나 불필요한 접두사는 사용하지 않음
- 원본 컬럼과 기존 파생 컬럼의 단순 곱셈형 상호작용은 사용하지 않음
- 두 그룹 중 한쪽이 전부 0이거나, 두 그룹 모두 전부 0인 변수는 제외함
- 이번 버전에서는 사용자 요청에 따라 `VIF`를 필수 필터로 사용하지 않음

## 병합 및 집계 기준
- 두 개의 시청 이력 파일을 세로 결합한 뒤 사용자별 시청 순서를 재구성함
- `USER_NUM`만으로 병합하면 서로 다른 멤버십 상태가 섞이는 사례가 있어 직접 병합 키로 사용하지 않음
- 동일 `USER_NUM`이 여러 멤버십 조합에 연결된 사례 수: `44`
- 아래 멤버십 원본 컬럼 조합 전체를 기준으로 시청 집계를 다시 연결함
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
- 전체 행 수: `23,343`
- 전체 컬럼 수: `105`
- `260517` 대비 신규 추가 변수 수: `7`
- 시청 이력과 직접 매칭된 행 수: `23,215`
- 시청 이력과 직접 매칭되지 않은 행 수: `128`
- 직접 매칭되지 않은 행의 신규 변수 값은 모두 `0`으로 채움

## 신규 파생변수 목록
- `fresh_start_next_active_day_ratio`
- `sampled_title_later_dominant_ratio`
- `new_open_known_dominant_day_ratio`
- `title_reentry_block_rate`
- `carryover_title_next_active_day_ratio`
- `repeat_opening_title_next_active_day_ratio`
- `mean_active_days_per_title`

## 변수별 상세 설명

### 1. `fresh_start_next_active_day_ratio`
- 사용 원천 컬럼: `watch_day`, `watch_seq`, `MOVIE_NUM`
- 의미: 사용자의 다음 활성 시청일이 직전 활성 시청일에 없던 작품으로 시작하는 비율
- 새롭게 보는 패턴: 하루가 끝난 뒤 다음에 돌아왔을 때 같은 흐름을 이어 보는지, 아니면 완전히 새 작품으로 출발하는지 보는 시작 패턴 변수
- 수식:

```text
사용자의 활성 시청일 순서를 d_1, d_2, ..., d_K 라고 하자.
F_i = 1( first_title(d_(i+1)) not in titles(d_i) ), 아니면 0

fresh_start_next_active_day_ratio = (Σ F_i) / (K - 1)
```

- 해석 메모: 값이 클수록 다음 활성 시청일을 전날 보던 작품군과 다른 작품으로 여는 경향이 강함
- 유의 나이대 `20대`: p-value `0.040387`, 비프로모션 평균 `0.614546`, 프로모션 평균 `0.634702`, 0초과 관측치 `1757 / 3640`

### 2. `sampled_title_later_dominant_ratio`
- 사용 원천 컬럼: `watch_time(min)`, `watch_day`, `watch_seq`, `MOVIE_NUM`
- 의미: 첫 시청은 매우 짧았지만 이후 어느 날에는 그날의 주력 작품이 된 타이틀의 비율
- 새롭게 보는 패턴: 처음에는 가볍게 찍어본 작품이 나중에 실제 몰입 대상이 되는지 보는 샘플링 이후 성장 패턴 변수
- 수식:

```text
S = {m | title m의 첫 시청 이벤트 시간이 5분 미만}
D(m) = 1(title m이 어느 활성 시청일에서든 dominant title이 된 적이 있음), 아니면 0

sampled_title_later_dominant_ratio = (Σ D(m)) / |S|
```

- 해석 메모: 값이 클수록 처음에는 짧게 본 작품이라도 나중에 본격적으로 파고드는 경향이 강함
- 유의 나이대 `20대`: p-value `0.025155`, 비프로모션 평균 `0.327332`, 프로모션 평균 `0.348434`, 0초과 관측치 `1070 / 2307`

### 3. `new_open_known_dominant_day_ratio`
- 사용 원천 컬럼: `watch_day`, `watch_seq`, `MOVIE_NUM`, `watch_time(min)`
- 의미: 하루를 새 작품으로 시작했지만, 결국 그날 가장 오래 본 작품은 이미 예전에 보던 작품이었던 날의 비율
- 새롭게 보는 패턴: 새 작품을 탐색해도 결국 익숙한 작품으로 정착하는지 보는 익숙함 회귀 패턴 변수
- 수식:

```text
활성 시청일 d 이전까지 본 적 있는 작품 집합을 H_d 라고 하자.
Q_d = 1( first_title(d) not in H_d 이고 dominant_title(d) in H_d ), 아니면 0
M = 고유 작품 수가 2개 이상인 활성 시청일 집합

new_open_known_dominant_day_ratio = (Σ_{d in M} Q_d) / |M|
```

- 해석 메모: 값이 클수록 새 작품을 먼저 눌러봐도 결국 익숙한 작품이 그날의 중심이 되는 경향이 강함
- 유의 나이대 `20대`: p-value `0.027658`, 비프로모션 평균 `0.031628`, 프로모션 평균 `0.024744`, 0초과 관측치 `152 / 247`

### 4. `title_reentry_block_rate`
- 사용 원천 컬럼: `watch_day`, `watch_seq`, `MOVIE_NUM`
- 의미: 다른 작품을 본 뒤 다시 예전에 보던 작품으로 돌아오는 블록의 비율
- 새롭게 보는 패턴: 작품별 연속 시청 구간을 블록으로 압축했을 때, 과거 작품으로 다시 되돌아오는 왕복형 소비가 얼마나 자주 일어나는지 보는 변수
- 수식:

```text
연속된 동일 작품 시청을 하나의 블록으로 압축하여
B = [b_1, b_2, ..., b_T] 를 만든다.
movie(b_t)는 t번째 블록의 작품 번호
R_t = 1( movie(b_t)가 이전 블록 중 이미 등장 ), 아니면 0

title_reentry_block_rate = (Σ R_t) / T
```

- 해석 메모: 값이 클수록 한 작품을 보다 다른 작품을 끼워 넣고, 다시 원래 작품으로 돌아오는 경향이 강함
- 유의 나이대 `30대`: p-value `0.011901`, 비프로모션 평균 `0.067571`, 프로모션 평균 `0.075670`, 0초과 관측치 `727 / 1218`

### 5. `carryover_title_next_active_day_ratio`
- 사용 원천 컬럼: `watch_day`, `watch_seq`, `MOVIE_NUM`
- 의미: 어떤 활성 시청일의 마지막 작품이 다음 활성 시청일의 첫 작품으로 이어지는 비율
- 새롭게 보는 패턴: 하루가 바뀌어도 바로 전 흐름을 이어보는지 보는 시청 연속성 변수
- 수식:

```text
사용자의 활성 시청일 순서를 d_1, d_2, ..., d_K 라고 하자.
C_i = 1( last_title(d_i) = first_title(d_(i+1)) ), 아니면 0

carryover_title_next_active_day_ratio = (Σ C_i) / (K - 1)
```

- 해석 메모: 값이 클수록 전 활성 시청일의 마지막 작품을 다음 활성 시청일 첫 작품으로 이어 보는 경향이 강함
- 유의 나이대 `40대`: p-value `0.048539`, 비프로모션 평균 `0.143705`, 프로모션 평균 `0.155345`, 0초과 관측치 `1898 / 675`

### 6. `repeat_opening_title_next_active_day_ratio`
- 사용 원천 컬럼: `watch_day`, `watch_seq`, `MOVIE_NUM`
- 의미: 연속된 두 활성 시청일이 같은 작품으로 시작하는 비율
- 새롭게 보는 패턴: 사용자가 다음에 다시 들어왔을 때도 같은 작품으로 문을 여는 반복 진입 습관 변수
- 수식:

```text
사용자의 활성 시청일 순서를 d_1, d_2, ..., d_K 라고 하자.
O_i = 1( first_title(d_i) = first_title(d_(i+1)) ), 아니면 0

repeat_opening_title_next_active_day_ratio = (Σ O_i) / (K - 1)
```

- 해석 메모: 값이 클수록 연속된 활성 시청일에서 같은 작품을 첫 진입 작품으로 반복 선택하는 경향이 강함
- 유의 나이대 `40대`: p-value `0.019387`, 비프로모션 평균 `0.141331`, 프로모션 평균 `0.156504`, 0초과 관측치 `1884 / 675`

### 7. `mean_active_days_per_title`
- 사용 원천 컬럼: `watch_day`, `MOVIE_NUM`
- 의미: 한 사용자가 본 작품 하나당 평균 몇 개의 활성 시청일에 걸쳐 이어졌는지 나타내는 값
- 새롭게 보는 패턴: 작품 소비가 하루 안에 끝나는 편인지, 여러 활성 시청일에 걸쳐 이어지는 편인지 보는 작품 생애주기 변수
- 수식:

```text
T = 사용자가 본 고유 작품 집합
A(m) = 작품 m을 시청한 고유 활성 시청일 수

mean_active_days_per_title = (Σ_{m in T} A(m)) / |T|
```

- 해석 메모: 값이 클수록 한 작품을 여러 활성 시청일에 걸쳐 나누어 보는 경향이 강함
- 유의 나이대 `40대`: p-value `0.021920`, 비프로모션 평균 `1.232252`, 프로모션 평균 `1.259067`, 0초과 관측치 `5827 / 1960`

## 종합 해석 메모
- `20대`에서는 다음 활성 시청일을 새로운 작품으로 시작하거나, 처음에는 짧게 본 작품을 나중에 주력 작품으로 키우는 패턴이 상대적으로 더 많이 나타났음
- `20대`에서는 새 작품으로 하루를 시작해도 결국 익숙한 작품이 그날의 중심이 되는 패턴도 함께 관찰되었음
- `30대`에서는 작품을 끊어 보다가 다시 돌아오는 구조가 상대적으로 더 많이 나타났음
- `40대`에서는 전 활성 시청일의 흐름을 다음 활성 시청일로 이어 가져가거나, 한 작품을 여러 활성 시청일에 걸쳐 나누어 보는 경향이 상대적으로 더 많이 나타났음
- 이번 버전은 `260517`의 within-day switching, binge, mixed-length 축과 달리, active-day boundary와 title life-cycle 중심으로 설계된 점에서 결이 다름
