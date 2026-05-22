> derived feature lineage

이 문서는 guide v3에 들어갈 주요 파생변수 설명 초안이 아니라 근거 요약이다. 공식 수식 확정은 05y/06x/07x 산출물과 함께 확인해야 한다.

> is_basic

- source columns: max_screen or product plan context
- formula or definition: 1 if basic product condition is met in source derivation
- timing window: membership context, not watch behavior
- final usage: expanded feature set only
- caveat: plan/product proxy; do not over-interpret as preference

> is_cold_start_3d_fixed

- source columns: View_History timing + user/subscription start
- formula or definition: flag fixed cold-start within first 3 days according to 06x hotfix
- timing window: day0 early observation
- final usage: conservative and expanded; Activation
- caveat: fixed replacement, not original raw cold_start field

> is_cold_start_7d_fixed

- source columns: View_History timing + user/subscription start
- formula or definition: flag fixed cold-start within first 7 days according to 06x hotfix
- timing window: day0~6 early observation
- final usage: conservative and expanded; Activation
- caveat: fixed replacement, not original raw cold_start field

> age_group

- source columns: age
- formula or definition: bucketed age group
- timing window: membership context at registration
- final usage: expanded feature and action personalization layer
- caveat: demographic layer only; not a churn cause

> is_female / is_male

- source columns: gender
- formula or definition: binary gender flags from source gender coding
- timing window: membership context
- final usage: expanded feature and action personalization layer
- caveat: gender variant only; not a churn cause

> payment_is_*

- source columns: payment_device
- formula or definition: one-hot payment environment flags
- timing window: membership/payment context
- final usage: removed from expanded_no_payment_device and final interpretation basis
- caveat: payment device is not viewing device

> registration time-band flags

- source columns: reg_date / reg_hour
- formula or definition: reg_is_weekend and morning/afternoon/evening/night flags
- timing window: registration timing
- final usage: expanded feature set
- caveat: context proxy, not direct intent

> retention_w2_ratio / retention_w3_ratio

- source columns: watch_time/session by week
- formula or definition: week2 or week3 usage relative to earlier observed usage
- timing window: day0~20
- final usage: conservative and expanded; Retention
- caveat: ratio can be unstable for low-activity rows

> diff_between_w*

- source columns: weekly watch_time values
- formula or definition: week-to-week difference features such as w2-w1, w3-w2, w3-w1
- timing window: day0~20
- final usage: conservative and expanded; Retention
- caveat: observed signal, not causal drop

> watch_ratio_under_1m / 5m

- source columns: watch history duration
- formula or definition: share of short viewing events under 1 minute or 5 minutes
- timing window: day0~20
- final usage: expanded feature set
- caveat: may reflect sampling, browsing, or interrupted viewing

> genre ratio

- source columns: Movie_Master genre/category mapping + watch history
- formula or definition: share of watched content by mapped genre category
- timing window: day0~20
- final usage: expanded feature set; content proxy
- caveat: proxy, not confirmed taste

> new_movie / old_movie ratio

- source columns: Movie release year/date + watch history
- formula or definition: share of watched content classified as new or old by configured thresholds
- timing window: day0~20
- final usage: expanded feature set; content proxy
- caveat: content recency proxy

> recency / inactive gap

- source columns: watch dates
- formula or definition: recency and inactive gap metrics inside observation window
- timing window: day0~20
- final usage: expanded feature set; Retention
- caveat: do not use day21+ behavior

> only_w1 / only_w2 / only_w3

- source columns: weekly activity flags
- formula or definition: activity exists only in one week bucket
- timing window: day0~20
- final usage: conservative and expanded; Activation/Retention
- caveat: behavior signal only, not cause

> evidence files

- `park.ingyeom\reports\audits\05y_feature_approval_and_dictionary_patch2_260515\05y_patch2_expanded_feature_contract.csv`
- `park.ingyeom\reports\audits\06x_dataset_generation_260515\06x_model_feature_lists.csv`
- `park.ingyeom\reports\audits\07x_feature_mapping_AARRR_260515\07x_feature_mapping_master.csv`
