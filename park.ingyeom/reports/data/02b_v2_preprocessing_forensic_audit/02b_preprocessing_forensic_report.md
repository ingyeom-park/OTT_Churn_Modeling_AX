> 02b v2 전처리 forensic audit 보고서

## 1. 실제로 삭제한 것은 무엇인가?
Stage 02에서 실제로 삭제된 Membership 행은 총 141행입니다. 삭제 사유는 `STRICT_TARGET_CONFLICT` 73행, `EXACT_DUPLICATE_EXTRA_ROW` 68행입니다.

## 2. 실제로 대체한 값은 있는가?
원시값과 전처리값을 retained row 기준으로 비교했습니다. 날짜 표기와 숫자형 표시처럼 형식 표준화 차이는 관측되지만, target conflict와 duplicate 제거 외에 이상치를 실질적으로 보정한 대체 정책은 확인되지 않았습니다. 전체 비교 결과는 `02b_raw_vs_preprocessed_value_changes.csv`에 있습니다.

## 3. 대체하지 않고 남은 이상치는 무엇인가?
age 결측 및 극단값, max_screen 결측, gender `N`, is_user_verified 결측, price와 verified 조합 의심, is_promotion 결측, is_churn_prevented 결측, 희귀 product_code/billing_method/payment_device, duration_days 비정상값이 남아 있습니다.

## 4. duration policy는 왜 적용되지 않았는가?
Stage 02 요약과 audit table에서 duration policy는 `DEFERRED`로 기록되어 있습니다. 즉 구독 기간이 31/32일이 아닌 행을 바로 삭제하면 row count와 target 분포가 바뀌므로, 사업 정의 확인 전에는 제거하지 않은 상태입니다.

## 5. age/max_screen/gender/verified/price anomaly는 어떻게 처리됐는가?
삭제나 대체가 아니라 flag 중심으로 남았습니다. age 극단값과 max_screen 결측은 final 전 Stage 02c에서 보정 또는 제외 기준을 정하는 것이 좋고, gender `N`, verified 조합, price=100 조합은 실제 코드값일 수 있어 mentor 또는 codebook 확인이 필요합니다.

## 6. UserMapping은 정제됐는가, 아니면 flag만 붙었는가?
UserMapping은 row count가 바뀌지 않았고 USER_KEY/USER_NUM 값 변경도 없습니다. one-to-many USER_KEY 문제는 flag만 붙었으며 Stage 02에서 mapping을 제거하지 않았습니다.

## 7. MovieMaster는 정제됐는가, 아니면 flag만 붙었는가?
Stage 02 policy checked MovieMaster는 dedupe하지 않고 duplicate/conflict flag만 붙였습니다. 최종 content feature join에서는 Stage 04가 deduped MovieMaster를 사용한 것이 확인됩니다.

## 8. ViewHistory raw는 수정됐는가?
ViewHistory raw는 수정되지 않았고 watch log도 raw에서 삭제되지 않았습니다. watch_date < reg_date, watch_date > end_date 로그는 feature window 계산에서 제외되거나 window 밖으로 처리됐고, 1분 또는 5분 이하 시청 로그는 삭제가 아니라 feature로 반영됐습니다.

## 9. 더 엄격하게 정리하면 row 수가 얼마나 줄어드는가?
duration strict만 적용하면 568행이 줄어듭니다. age, max_screen, duration, gender/verified, price mismatch를 모두 적용하는 all-strict 기준에서는 4,793행이 줄어듭니다. 이는 공식 데이터에 적용한 값이 아니라 what-if 계산입니다.

## 10. 최종 발표 전에 Stage 02c correction이 필요한가?
필요합니다. 다만 모든 이상치를 삭제하는 방향은 위험합니다. Stage 02c에서는 age 극단값, max_screen 결측/비정상, duration 0 및 duration not 31/32의 발표 리스크를 먼저 정책화하고, gender `N`, price=100, promotion/churn_prevented 결측, 희귀 코드값은 flag 또는 mentor decision 영역으로 분리하는 것이 안전합니다.
