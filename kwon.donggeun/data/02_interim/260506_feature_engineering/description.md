# Membership v3 파생변수 설명서

- **원본 파일**: `promotion_0_membership_v2.csv` (15개 컬럼)
- **생성 파일**: `promotion_0_membership_v3.csv` (48개 컬럼)
- **추가 파생변수**: 33개

---

## 원본 변수 (15개)

| 변수 | 설명 |
|------|------|
| `USER_KEY` | 유저 식별자 |
| `product_code` | 구독 상품 코드 |
| `price` | 결제 금액 |
| `billing_method` | 결제 방식 코드 |
| `max_screen` | 동시 접속 가능 화면 수 |
| `is_promotion` | 100원 프로모션 여부 |
| `is_churn_prevented` | 이탈 방지 처리 여부 |
| `is_repurchase` | 재구매 여부 (타겟 변수, 0=이탈 1=재구매) |
| `payment_device` | 결제 기기 |
| `is_user_verified` | 본인인증 여부 |
| `gender` | 성별 (M/F) |
| `age` | 나이 (5세 단위, 예: 35=31~35세) |
| `reg_date` | 가입일 |
| `reg_hour` | 가입 시각 |
| `end_date` | 구독 종료일 |

---

## 파생변수 (33개)

### 📅 날짜/시간 (5개)

| 변수 | 설명 | 계산 방법 |
|------|------|-----------|
| `duration_days` | 구독 기간 (일) | end_date - reg_date |
| `reg_weekday` | 가입 요일 | 0=월요일 ~ 6=일요일 |
| `is_weekend_reg` | 주말 가입 여부 | reg_weekday가 5 또는 6이면 1 |
| `is_month_start_reg` | 월초(1~10일) 가입 여부 | 급여일 이후 충동 구매 가설 |
| `reg_hour_group` | 가입 시간대 | 0=새벽(0~5시), 1=오전(6~11시), 2=오후(12~17시), 3=저녁(18~23시) |

### 💰 가격 (4개)

| 변수 | 설명 | 계산 방법 |
|------|------|-----------|
| `is_usd` | 달러 결제 여부 | price < 100이면 1 (9.99달러, 13.49달러 등) |
| `price_per_day` | 하루당 비용 | price / duration_days |
| `price_per_screen` | 화면당 비용 | price / max_screen (실질 1인 체감 비용) |
| `price_tier` | 가격 티어 | 달러 / 저가(~5000) / 중가(~9000) / 고가(~12000) / 프리미엄(12000+) |

### 📦 상품/기기/결제 (5개)

| 변수 | 설명 | 계산 방법 |
|------|------|-----------|
| `is_new_product` | 신규 상품 여부 | product_code가 pk_2xxx이면 1 (pk_1xxx는 구상품) |
| `is_family_plan` | 공유 계정 여부 | max_screen > 1이면 1 |
| `device_group` | 기기 그룹 | mobile(ios/android/mobile) / pc / tv(smarttv/ott) |
| `billing_group` | 결제 방식 그룹 | apple / google / onestore / card / mobile_pay / paypal / other |
| `is_apple_ecosystem` | 애플 생태계 유저 여부 | iOS 기기 + Apple Pay 동시 사용 (해지가 쉬운 환경) |

### 👤 인구통계 (8개)

| 변수 | 설명 | 계산 방법 |
|------|------|-----------|
| `age_group` | 연령대 | 0=10대, 1=20대, 2=30대, 3=40대, 4=50대+ |
| `gender_enc` | 성별 인코딩 | M=1, F=0, 미상=2 |
| `age_x_screen` | 나이 × 동시접속 수 | 가족 공유 패턴 (나이 많고 화면 많으면 가족 공유) |
| `verified_x_age` | 본인인증 × 나이 | 인증한 고연령 유저 = 충성 유저 가설 |
| `is_senior_unverified` | 50대+ 미인증 여부 | 이탈 위험군 가설 |
| `is_young_unverified` | 25세 이하 미인증 여부 | 체험 후 이탈 가설 |
| `is_long_sub` | 장기 구독 여부 | duration_days >= 31이면 1 |
| `hour_x_weekend` | 가입 시간 × 주말 여부 | 새벽 주말 충동 구매 패턴 |

### 🎬 장르/콘텐츠 (11개)

View History + Movie 데이터를 유저 단위로 집계한 피처

| 변수 | 설명 |
|------|------|
| `genre_diversity` | 시청한 장르 종류 수 (취향 다양성) |
| `korean_ratio` | 한국 영화 시청 비율 (0~1) |
| `avg_showtime` | 평균 영화 러닝타임 (분) |
| `genre_액션_ratio` | 액션 장르 시청 비율 (0~1) |
| `genre_드라마_ratio` | 드라마 장르 시청 비율 (0~1) |
| `genre_로맨스_ratio` | 로맨스 장르 시청 비율 (0~1) |
| `genre_스릴러_ratio` | 스릴러 장르 시청 비율 (0~1) |
| `genre_애니메이션_ratio` | 애니메이션 장르 시청 비율 (0~1) |
| `genre_공포_ratio` | 공포 장르 시청 비율 (0~1) |
| `genre_코미디_ratio` | 코미디 장르 시청 비율 (0~1) |
| `genre_SF_ratio` | SF 장르 시청 비율 (0~1) |

> 시청 이력이 없는 유저의 장르 관련 피처는 모두 0으로 처리
