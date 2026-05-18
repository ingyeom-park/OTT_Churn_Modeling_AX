# 260518 파생변수 설명

## 생성 파일
- CSV: `C:\myCode\ott-churn-prediction\kim.kwangil\derived_variable\260518_derived_membership_age_specific.csv`
- MD: `C:\myCode\ott-churn-prediction\kim.kwangil\derived_variable\260518_derived_feature_explanation.md`

## 사용 원천 파일
- 시청 이력 원천: `C:\myCode\ott-churn-prediction\kim.kwangil\data\260509_merged1_0.csv`
- 시청 이력 원천: `C:\myCode\ott-churn-prediction\kim.kwangil\data\260509_merged1_1.csv`
- 베이스 파생 파일: `C:\myCode\ott-churn-prediction\kim.kwangil\derived_variable\260517_derived_membership_age_specific.csv`
- 나이대 유의성 기준 참고: `C:\myCode\ott-churn-prediction\kim.kwangil\EDA\260513_derived_EDA.ipynb`

## 이번 버전의 설계 기준
- `260517`에 이미 추가된 파생변수와 결이 겹치지 않도록, 단순 비율 조정이나 숫자 구간 변경이 아니라 시청 순서와 되돌아보기 흐름을 직접 반영하는 변수만 추가함
- `is_user_verified` 및 그 직접 파생 변수는 신규 생성 대상에서 제외함
- 컬럼명에 나이대 숫자, `vh` 같은 접두사는 사용하지 않음
- 원본 컬럼과 기존 파생 컬럼의 단순 곱셈형 상호작용은 사용하지 않음
- 두 그룹 중 한쪽이 전부 0이거나, 두 그룹 모두 전부 0인 변수는 제외함
- `260513_derived_EDA.ipynb`에서 프로모션 여부 차이가 유의했던 나이대 중 `20대`, `30대`, `40대`를 우선 탐색 대상으로 삼음
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
- 전체 컬럼 수: `104`
- `260517` 대비 신규 추가 변수 수: `6`
- 시청 이력과 직접 매칭된 행 수: `23,215`
- 시청 이력과 직접 매칭되지 않은 행 수: `128`
- 직접 매칭되지 않은 행의 신규 변수 값은 모두 `0`으로 채움

## 신규 파생변수 목록
- `sample_then_switch_rate`
- `sample_then_genre_jump_rate`
- `search_then_settle_day_ratio`
- `title_reentry_block_rate`
- `dominant_title_is_last_day_ratio`
- `title_return_day_ratio`

## 변수별 상세 설명

### 1. `sample_then_switch_rate`
- 사용 원천 컬럼: `watch_time(min)`, `MOVIE_NUM`, `watch_seq`
- 의미: 짧게 찍어본 뒤 바로 다른 작품으로 넘어가는 비율
- 새롭게 보는 패턴: 사용자가 한 작품을 짧게 맛본 뒤 같은 작품을 이어 보는지, 아니면 곧바로 다른 작품으로 이동하는지 파악하는 탐색형 흐름 변수
- 수식:

```text
S = {i | watch_time_i < 5 이고 i가 마지막 시청 이벤트가 아님}
I_i = 1(next_movie_i != current_movie_i), 아니면 0

sample_then_switch_rate = (Σ I_i) / |S|
```

- 해석 메모: 값이 클수록 짧은 시청 직후 동일 작품에 머무르지 않고 다른 작품으로 이동하는 경향이 강함
- 유의 나이대:
  - `20대`: p-value `0.045581`, 비프로모션 평균 `0.452795`, 프로모션 평균 `0.475217`, 0초과 관측치 `1260 / 2688`

### 2. `sample_then_genre_jump_rate`
- 사용 원천 컬럼: `watch_time(min)`, `category`, `watch_seq`
- 의미: 짧게 찍어본 뒤 바로 다른 장르로 넘어가는 비율
- 새롭게 보는 패턴: 단순히 작품만 바꾸는 수준이 아니라, 짧은 시청 직후 아예 장르 축을 바꾸는 탐색 성향 측정 변수
- 수식:

```text
S = {i | watch_time_i < 5 이고 i가 마지막 시청 이벤트가 아님}
J_i = 1(next_category_i != current_category_i), 아니면 0

sample_then_genre_jump_rate = (Σ J_i) / |S|
```

- 해석 메모: 값이 클수록 짧게 본 뒤 같은 장르 안에서 머무르지 않고 다른 장르로 이동하는 경향이 강함
- 유의 나이대:
  - `20대`: p-value `0.024666`, 비프로모션 평균 `0.356629`, 프로모션 평균 `0.378753`, 0초과 관측치 `1113 / 2411`

### 3. `search_then_settle_day_ratio`
- 사용 원천 컬럼: `watch_day`, `watch_seq`, `watch_time(min)`, `MOVIE_NUM`
- 의미: 같은 날 초반에는 여러 작품을 짧게 탐색하다가, 뒤에서 한 작품에 길게 정착하는 날의 비율
- 새롭게 보는 패턴: 하루 안에서 탐색 단계와 정착 단계가 동시에 나타나는지 보는 일별 전환 구조 변수
- 수식:

```text
한 사용자의 활성일 집합을 D라고 하자.

day d가 아래 조건을 모두 만족하면 Q_d = 1, 아니면 0
1) 첫 장시간 시청이 등장하기 전까지 watch_time < 5 인 이벤트가 2개 이상 존재
2) 그 짧은 시청 이벤트들이 서로 다른 작품 2개 이상을 포함
3) 이후에 watch_time >= 20 인 이벤트가 같은 날 안에 존재

search_then_settle_day_ratio = (Σ Q_d) / |D|
```

- 해석 메모: 값이 클수록 같은 날 안에서 여러 작품을 둘러본 뒤 결국 하나에 길게 머무르는 경향이 강함
- 유의 나이대:
  - `20대`: p-value `0.028644`, 비프로모션 평균 `0.083194`, 프로모션 평균 `0.099151`, 0초과 관측치 `199 / 479`
  - `40대`: p-value `0.047303`, 비프로모션 평균 `0.077706`, 프로모션 평균 `0.091837`, 0초과 관측치 `458 / 180`

### 4. `title_reentry_block_rate`
- 사용 원천 컬럼: `MOVIE_NUM`, `watch_seq`
- 의미: 다른 작품을 본 뒤 다시 예전에 보던 작품으로 돌아오는 블록의 비율
- 새롭게 보는 패턴: 시청 이벤트를 작품 단위 연속 블록으로 압축한 뒤, 과거에 보던 작품이 이후 블록에서 다시 등장하는지 보는 재진입 흐름 변수
- 수식:

```text
연속된 동일 작품 시청을 하나의 블록으로 압축하여
B = [b_1, b_2, ..., b_K] 를 만든다.
movie(b_k)는 k번째 블록의 작품 번호

R_k = 1(movie(b_k)가 이전 블록들 중 이미 한 번 이상 등장), 아니면 0

title_reentry_block_rate = (Σ R_k) / K
```

- 해석 메모: 값이 클수록 한 작품을 보다가 끝내지 않고, 다른 작품을 거친 뒤 다시 돌아오는 왕복형 시청 패턴이 강함
- 유의 나이대:
  - `30대`: p-value `0.011658`, 비프로모션 평균 `0.067531`, 프로모션 평균 `0.075670`, 0초과 관측치 `727 / 1218`

### 5. `dominant_title_is_last_day_ratio`
- 사용 원천 컬럼: `watch_day`, `watch_seq`, `MOVIE_NUM`, `watch_time(min)`
- 의미: 하루의 마지막 작품이 그날 가장 오래 본 작품인 날의 비율
- 새롭게 보는 패턴: 그날 이것저것 보다가 마지막에 실제 주력 시청 작품으로 마무리하는지 확인하는 일별 종료 패턴 변수
- 수식:

```text
활성일 d마다
L_d = 그날 마지막 시청 이벤트의 작품
T_d(m) = 그날 작품 m의 총 시청시간
M_d = argmax_m T_d(m)

Z_d = 1(L_d = M_d), 아니면 0

dominant_title_is_last_day_ratio = (Σ Z_d) / |D|
```

- 해석 메모: 값이 클수록 하루 끝에서 가장 오래 본 작품으로 정리되는 마감형 시청 패턴이 강함
- 유의 나이대:
  - `30대`: p-value `0.034949`, 비프로모션 평균 `0.388723`, 프로모션 평균 `0.416269`, 0초과 관측치 `910 / 1484`

### 6. `title_return_day_ratio`
- 사용 원천 컬럼: `watch_day`, `watch_seq`, `MOVIE_NUM`
- 의미: 같은 날 안에서 한 작품을 보다가 다른 작품을 거친 후 다시 원래 작품으로 돌아오는 날의 비율
- 새롭게 보는 패턴: 하루 안에서 작품 간 왕복이 발생하는지 보는 일별 재방문 구조 변수
- 수식:

```text
활성일 d의 시청 순서를 [m_1, m_2, ..., m_n] 이라고 하자.

day d가 아래 조건을 만족하면 Y_d = 1, 아니면 0
어떤 i < j < k 가 존재하여
m_i = m_k 이고
m_j != m_i

title_return_day_ratio = (Σ Y_d) / |D|
```

- 해석 메모: 값이 클수록 같은 날 안에서 한 작품을 이어서 끝까지 보기보다, 다른 작품을 들렀다가 다시 돌아오는 패턴이 강함
- 유의 나이대:
  - `30대`: p-value `0.012858`, 비프로모션 평균 `0.310551`, 프로모션 평균 `0.341655`, 0초과 관측치 `727 / 1218`

## 종합 해석 메모
- `20대`에서는 짧게 찍어본 뒤 다른 작품 또는 다른 장르로 바로 이동하는 탐색형 흐름이 더 뚜렷하게 나타남
- `30대`에서는 한 작품을 보다 다른 작품을 거친 뒤 다시 돌아오거나, 하루 마지막을 주력 작품으로 마무리하는 구조가 상대적으로 더 많이 나타남
- `40대`에서는 하루 초반 탐색 후 한 작품에 길게 정착하는 패턴이 유의하게 관찰됨
- 이번 6개 변수는 기존 `260517`의 binge, 혼합 길이, 장르 전환 비율보다 더 직접적으로 시청 순서와 되돌아보기 구조를 설명하는 변수라는 점에서 성격이 다름
