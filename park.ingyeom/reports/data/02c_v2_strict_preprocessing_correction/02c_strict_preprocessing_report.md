> Stage 02c v2 strict preprocessing correction report

## 1. Stage 02는 실제로 무엇만 제거했는가?
Stage 02는 raw Membership 24,074행 중 141행만 제거했습니다. 제거 사유는 strict target conflict 73행과 exact duplicate extra row 68행입니다.

## 2. Stage 02에서 하지 않았던 최소 전처리는 무엇인가?
Stage 02는 실제 retained-row 값 교체가 0건이었고, target encoding, binary encoding, 날짜 파싱 확정, numeric coercion, duration strict filtering, age/max_screen/price invalid row removal을 공식 산출물에 적용하지 않았습니다.

## 3. Stage 02c에서 target encoding은 어떻게 했는가?
`is_repurchase_raw`를 보존하고, `Y`는 1, `N`은 0으로 매핑해 `is_repurchase_label`을 생성했습니다. 예상 밖 target 값은 `INVALID_TARGET_VALUE`로 삭제하도록 정책화했습니다.

## 4. Stage 02c에서 binary encoding은 어떻게 했는가?
`is_promotion`, `is_churn_prevented`, `is_user_verified`는 raw 값을 보존한 뒤 관측값 체계에 따라 `*_bin`으로 표준화했습니다. missing 또는 ambiguous 값은 삭제하지 않고 `*_unknown_flag`로 남겼습니다.

## 5. Stage 02c에서 date parsing은 어떻게 했는가?
`reg_date_raw`, `end_date_raw`를 보존하고 `reg_date_parsed`, `end_date_parsed`를 만들었습니다. `duration_days_recomputed`는 기존 duration을 믿지 않고 parsed date 차이로 다시 계산했습니다.

## 6. Stage 02c에서 numeric coercion은 어떻게 했는가?
`age`, `price`, `max_screen`, `reg_hour`는 각각 `age_num`, `price_num`, `max_screen_num`, `reg_hour_num`으로 강제 숫자화했습니다. `reg_hour`는 audit/flag only라서 이 문제만으로 row를 삭제하지 않았습니다.

## 7. Stage 02c에서 어떤 row를 실제 삭제했는가?
Stage 02c는 Stage 02 retained 23,933행 중 818행을 strict-core 기준으로 삭제했고, 최종 corrected row count는 23,115행입니다. 삭제 사유는 invalid target, date parse failure, non-31/32 또는 0 duration, invalid age, invalid/missing max_screen, invalid/missing/negative price입니다.

## 8. Stage 02c에서 어떤 값을 unknown/flag 처리했는가?
`gender == N`과 blank categorical 값은 `unknown`으로 표준화했습니다. promotion/churn-prevented/user-verified ambiguous 값, verified-gender inconsistency, price=100 verified mismatch, reg_hour invalid는 flag로 남겼습니다.

## 9. 왜 all-strict 4,793행 삭제는 적용하지 않았는가?
all-strict 4,793행 삭제에는 gender `N`, price=100 verified mismatch, rare category처럼 business definition 확인이 필요한 조건이 포함됩니다. Stage 02c는 발표 전 필수 strict-core correction만 적용하고, business-ambiguous 조건은 삭제가 아니라 flag로 분리했습니다.

## 10. 최종 corrected row count는 얼마인가?
최종 strict-core corrected Membership row count는 23,115행입니다.

## 11. target distribution은 어떻게 바뀌었는가?
Stage 02 retained의 repurchase rate는 0.7198, churn rate는 0.2802입니다. Stage 02c strict-core의 repurchase rate는 0.7178, churn rate는 0.2822입니다.

## 12. ViewHistory raw는 수정했는가?
수정하지 않았습니다. short watch logs도 raw에서 삭제하지 않았고, Stage 03/04의 temporal policy audit을 참조해 feature window 정책만 문서화했습니다.

## 13. UserMapping과 MovieMaster는 정제했는가, flag만 유지했는가?
Stage 02c는 UserMapping과 MovieMaster row를 삭제하지 않았습니다. UserMapping은 strict-core Membership 기준 event count를 추가했고, MovieMaster는 Stage 02 policy checked 상태를 carry-forward했습니다. MovieMaster dedupe는 Stage 04 content feature generation 영역입니다.

## 14. Stage 03 이후 downstream을 다시 돌려야 하는가?
다시 돌려야 합니다. Stage 02c가 Membership row count와 core standardized columns를 바꾸었기 때문에 Stage 03부터 Stage 09까지 기존 산출물은 final이 아니라 deprecated/provisional 상태입니다.

## 15. 최종 발표 전 어떤 수치를 다시 산정해야 하는가?
Stage 03 usage features, Stage 04 content features, Stage 05 modeling dataset, Stage 06/06h model metrics, Stage 07/07r SHAP, Stage 08/08b segmentation, Stage 09 simulation 수치를 모두 Stage 02c strict-core population 기준으로 다시 산정하거나 최소 재검증해야 합니다.

## 분석 모집단 변경 주의
duration 31/32 filtering은 비표준 구독 케이스를 official modeling population에서 제외하는 scope change입니다. non-31/32 row가 반드시 불가능하거나 잘못된 데이터라는 뜻은 아닙니다.

## downstream column contract
Raw backup columns는 모델 feature로 사용하면 안 됩니다. Downstream target은 `is_repurchase_label`, binary는 `*_bin`, numeric은 `*_num`을 사용해야 하며, `*_parsed`와 `duration_days_recomputed`는 audit 또는 feature construction/scope definition 전용입니다.
