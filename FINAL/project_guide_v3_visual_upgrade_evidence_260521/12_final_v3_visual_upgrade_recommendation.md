> final v3 visual upgrade recommendation

> 추가해야 할 컴포넌트
`dataset_lineage_waterfall`, `feature_set_flow_bar`, `AARRR_feature_count_bar`, SHAP top10/family bar, segment share/risk/watch charts, action tier distribution을 우선 추가하는 것이 좋습니다.

> 버려야 할 legacy 컴포넌트
legacy HTML의 수치 문장을 그대로 승격하는 방식은 버려야 합니다. raw 23,343과 final 23,079 혼동, 100원딜 원인화, content_preference 핵심 이탈 방어 타겟화, general_observation 일반 고객군화, payment-device 시청기기화 표현은 재사용하지 않습니다.

> Chart.js를 어디에 쓸 것인가
데이터 계보, feature count, AARRR count, payment-device AUC delta, SHAP top10, SHAP family, segment share, segment risk, action tier distribution에 Chart.js를 쓰는 것이 적합합니다.

> PNG SHAP figure를 쓸 것인가
beeswarm과 scope comparison은 PNG를 쓰는 것이 좋습니다. global top10 bar와 family bar는 Chart.js로 다시 그리는 편이 스타일 통일에 유리합니다.

> AARRR 구조
AARRR은 funnel 하나보다 observed/proxy/unobserved 상태를 함께 보여주는 stage ladder가 안전합니다. Referral은 observed feature 없음, Revenue는 is_repurchase target proxy입니다.

> 세그먼트 구조
`triage flow -> overview doughnut -> risk/repurchase bars -> action tier grouping -> segment detail cards -> appendix flag dictionary` 순서를 권장합니다.

> 기존 final v3 보강 위치
현재 `FINAL/project_guide_v3.html`은 repo에서 발견되지 않았습니다. 최신 revised HTML이 제공되면 데이터 계보, AARRR, SHAP, 세그먼트, guardrail 섹션을 본 evidence pack 기준으로 보강하면 됩니다.

> 추가 자료
최신 `project_guide_v3_chatgpt_revised.html` 파일이 필요합니다. 이 파일 없이는 정확한 교체 section을 확정할 수 없습니다.
