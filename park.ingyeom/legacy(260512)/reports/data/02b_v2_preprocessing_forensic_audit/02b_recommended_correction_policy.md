> 02b recommended correction policy

## 현재 공식 전처리로 유지할 것
strict target conflict 제거와 exact duplicate extra row 제거는 유지합니다. UserMapping과 MovieMaster는 Stage 02에서 삭제하지 않고 flag만 붙이는 현재 방식도 유지 가능합니다.

## Stage 02c에서 추가 검토할 것
age < 10, age > 100, age 950, max_screen 결측 또는 비정상, duration 0, duration not in 31/32는 최종 발표 전에 보정 정책을 정하는 것이 좋습니다. 이 정책은 row count를 바꾸므로 Stage 02c에서 별도 산출물로 분리해야 합니다.

## flag로 남겨도 되는 것
gender `N`, is_promotion 결측, is_churn_prevented 결측은 실제 코드값 또는 미응답일 수 있으므로 무조건 삭제하지 않는 편이 안전합니다.

## mentor 또는 business definition이 필요한 것
price=100 + verified not Y, rare product_code, rare billing_method, rare payment_device, max_screen 3은 상품 및 결제 코드 정의를 확인해야 합니다.

## 바꾸면 안 되는 것
raw files는 수정하지 않습니다. ViewHistory short watch logs는 삭제하지 않고 featureized 상태로 둡니다. MovieMaster duplicate raw도 Stage 02에서 직접 삭제하지 않고 Stage 04 dedupe join 정책으로 관리합니다.
