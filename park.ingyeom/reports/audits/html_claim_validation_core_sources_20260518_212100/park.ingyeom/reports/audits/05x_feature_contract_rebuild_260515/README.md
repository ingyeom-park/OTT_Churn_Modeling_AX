# 05x_feature_contract_rebuild_260515

## 목적
기존 05~14 pre-13b 산출물이 archive로 격리된 상태에서, 91개 전체 컬럼을 재검토하고
보수 플랜과 확장 플랜의 feature contract를 새로 작성한다.

## 왜 05x부터 다시 시작하는가
기존 pre-13b 작업은 conservative_safe_22 기준으로만 진행되어, 91개 컬럼 중 장르/recency/
membership 등 69개 review 컬럼이 "나중에" 상태로 방치되었다.
이번 05x는 91개 전체를 명시적으로 재검토하고 사용자 승인 체계를 만든다.

## 기존 pre-13b 22개 결과의 지위
archive/pre13b_conservative_safe_22_reference에 보존된 pre-13b 결과는 reference/deprecated이다.
canonical 기준선으로 복원하지 않는다. 단, conservative_safe_22 22개 feature 목록은 이번
05x에서도 보수 baseline 기준선으로 유지한다.

## LLM 최종 피처 결정 원칙
LLM(Codex/Claude)은 feature를 최종 제외하거나 승격하지 않는다.
LLM은 근거와 후보만 제시하며, 최종 사용 여부는 반드시 사용자 승인 후 확정한다.

## 보수 플랜 (conservative_safe_22)
- 기존 22개 weekly-window safe feature
- pre-13b 결과와 비교 가능한 기준선
- 추가 검증 없이 즉시 모델 투입 가능

## 확장 플랜 (expanded_feature_set)
- membership/context, total usage aggregate, content/genre 포함 후보
- 사용자 승인 전 후보 상태
- context/content caveat flag 포함

## 사용자 승인 전 다음 단계 금지
05x_user_approval_checklist.csv 검토 및 승인 전에 06x로 진행하지 않는다.
11/12/14/16/17 모델링 단계 진입 금지 유지.

## 다음 단계
사용자 승인 후 → 06x_dataset_generation
