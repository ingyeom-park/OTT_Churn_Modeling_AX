> CSS and layout pattern memo

> sidebar navigation
AARRR, project guide v2, segment visual guide의 sidebar 구조는 final v3에서도 재사용 가치가 높습니다. 데이터 계보, AARRR, 모델, SHAP, 세그먼트, appendix가 긴 문서이기 때문입니다.

> dark/light mode toggle
dark/light mode는 재사용 가능하지만, Chart.js 색상과 표 대비가 깨지지 않도록 CSS variable 중심으로 제한하는 편이 안전합니다.

> card layout
warning cards와 segment detail cards는 재사용 가능합니다. 단, 각 카드는 하나의 주장 또는 하나의 시각 자료만 담는 방식이 좋습니다.

> table-wrap
기존 HTML에서 table-wrap은 강하게 표준화되어 있지 않습니다. final v3에는 긴 evidence table이 들어가므로 `overflow-x: auto` wrapper를 새로 표준화하는 편이 좋습니다.

> Chart.js canvas wrapper
Chart.js canvas는 고정 height wrapper와 source caption을 붙여야 합니다. 데이터 파일명을 chart 아래에 노출하면 검수성이 좋아집니다.

> variable tooltip
`is_promotion`, `churn_risk`, `payment_is_*`, `content_preference_target_candidate`, `general_observation`에 tooltip을 붙이는 것을 권장합니다.

> warning cards
final v3 첫 화면에는 23,079 subscription-event basis, no causality, SHAP non-causal, payment-device is not viewing-device, PUBLIC numeric score exclusion을 고정해야 합니다.

> triage flow
segment visual guide의 triage flow는 assignment explanation only로 재사용해야 하며, 새 segment rule처럼 보이면 안 됩니다.

> collapsible details
SHAP PNG, scope comparison, segment flag dictionary, source fingerprint는 appendix collapsible details로 보내는 편이 안전합니다.

> hero summary
hero는 과장된 성과보다 `100원딜 OTT 이탈 분석 가이드`처럼 내용 식별 중심이 안전합니다.

> appendix split
본문은 Chart.js 요약, appendix는 PNG와 evidence table로 나누는 구조가 가장 안전합니다.

> mobile responsiveness
모바일에서는 1열 흐름, sticky sidebar 해제, chart height 제한, table horizontal scroll이 필요합니다.
