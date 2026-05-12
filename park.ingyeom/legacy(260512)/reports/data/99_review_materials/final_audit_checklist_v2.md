# Final Audit Checklist — OTT Churn Prediction v2

> Stage 10 실행 전에 이 체크리스트를 완료하십시오.
> **모든 항목은 Stage 02b forensic audit 완료 이후 재검증해야 합니다.**
> 02b 완료 전 downstream 결과는 PROVISIONAL로 간주합니다.

---

## 사전 조건 확인

- [ ] Stage 02b forensic audit이 완료되었는가?
- [ ] 02b 결과에 따라 Stage 03~09가 재실행되었는가?
- [ ] 재실행된 결과물이 `/reports/data/` 하위 각 Stage 폴더에 저장되었는가?

> **⚠ 위 세 항목 중 하나라도 미완료이면 Stage 10 실행을 보류합니다.**

---

## 1. Row Count Lineage

데이터가 각 단계를 거치며 정확하게 흘러내려갔는지 확인합니다.

| 체크 항목 | 기준 | 확인 |
|---|---|---|
| 원본 Membership 행 수 | 24,074 (Stage 01 기준) | [ ] |
| 중복 제거 후 행 수 | [PLACEHOLDER: confirmed after 02b] | [ ] |
| 타겟 충돌 제거 후 행 수 | [PLACEHOLDER: confirmed after 02b] | [ ] |
| 02b 추가 제외 후 최종 행 수 | [PLACEHOLDER: confirmed after 02b] | [ ] |
| Stage 03 usage feature 행 수 (w1_3) | [PLACEHOLDER] | [ ] |
| Stage 03 usage feature 행 수 (w1_4) | [PLACEHOLDER] | [ ] |
| Stage 04 content feature 행 수 (w1_3) | [PLACEHOLDER] | [ ] |
| Stage 05 modeling dataset 행 수 (w1_3) | [PLACEHOLDER] | [ ] |
| Stage 06 train/test 분리 후 행 수 합계 | Stage 05와 일치 여부 | [ ] |

**확인 방법:** 각 Stage 산출물의 `*_summary.csv` 또는 `*_audit.csv` 파일의 행 수와 비교합니다.

---

## 2. Preprocessing

전처리 정책이 일관되게 적용되었는지 확인합니다.

| 체크 항목 | 확인 |
|---|---|
| 중복 제거 기준이 Stage 02 정책 문서와 일치하는가? | [ ] |
| 타겟 충돌 처리 기준이 문서화되어 있는가? | [ ] |
| age=40 / gender=N 집단 처리가 02b 결론에 따라 반영되었는가? | [ ] |
| iOS 결제 사용자 처리가 02b 결론에 따라 반영되었는가? | [ ] |
| 구독 종료 후 시청 기록이 피처 생성에서 제외되었는가? | [ ] |
| 관측 윈도우 기준(w1_3, w1_4)이 일관되게 적용되었는가? | [ ] |
| 타겟 비율 (Y/N) 이 02b 이후 확정값과 일치하는가? | [ ] |

---

## 3. Feature Pruning

최종 피처셋이 감사된 정책을 따르는지 확인합니다.

| 체크 항목 | 확인 |
|---|---|
| Stage 05e 피처 프루닝 정책 문서가 최신 상태인가? | [ ] |
| 제거된 피처 목록이 기록되어 있는가? | [ ] |
| 제거 이유가 각 피처에 대해 명시되어 있는가? (중복, 리키지, 낮은 중요도 등) | [ ] |
| 관측 윈도우 이후 데이터를 참조하는 피처가 없는가? (타임 리키지 검사) | [ ] |
| 타겟 변수와 직접 파생된 피처가 없는가? (타겟 리키지 검사) | [ ] |
| 최종 피처셋이 Stage 06 모델링에 사용된 피처셋과 일치하는가? | [ ] |
| 다중공선성이 높은 피처 쌍에 대한 처리 결정이 기록되어 있는가? | [ ] |

---

## 4. Model Metric

모델 성능 수치가 신뢰 가능한지 확인합니다.

| 체크 항목 | 확인 |
|---|---|
| 그룹 분리(USER_KEY 기반)가 train/test 전체에 적용되었는가? | [ ] |
| 동일 USER_KEY가 훈련셋과 테스트셋에 동시에 등장하지 않는가? | [ ] |
| AUC 수치에 윈도우(w1_3/w1_4)와 모델명이 명시되어 있는가? | [ ] |
| 권장 모델 선택 기준이 문서화되어 있는가? | [ ] |
| w1_3 권장 모델 AUC: [PLACEHOLDER: confirmed after 02b rerun] | [ ] |
| w1_4 최고 성능 모델 AUC: [PLACEHOLDER: confirmed after 02b rerun] | [ ] |
| DummyClassifier 베이스라인 대비 유의미한 차이가 있는가? | [ ] |
| 모든 피처셋 × 모델 조합의 결과가 `06_v2_model_metrics_summary.csv`에 기록되어 있는가? | [ ] |
| Stage 06b~06h 감사 결과 이상 없음이 확인되었는가? | [ ] |

---

## 5. SHAP

SHAP 분석이 올바르게 수행되었고 적절하게 해석되었는지 확인합니다.

| 체크 항목 | 확인 |
|---|---|
| SHAP 분석이 테스트셋(훈련셋 아닌)에 대해 수행되었는가? | [ ] |
| 사용된 모델이 최종 확정 모델과 일치하는가? | [ ] |
| SHAP summary plot이 02b 이후 재실행된 결과물인가? | [ ] |
| 보고서/발표에서 SHAP을 인과 분석으로 표현한 문장이 없는가? | [ ] |
| 상관 피처 간 SHAP 분산 가능성에 대한 주의사항이 명시되어 있는가? | [ ] |
| 상위 피처 목록이 `claim_wording_guardrail_v2.md` 기준에 맞게 서술되어 있는가? | [ ] |

---

## 6. Segmentation

세그먼테이션 결과가 일관성 있고 해석 가능한지 확인합니다.

| 체크 항목 | 확인 |
|---|---|
| 세그먼테이션이 02b 이후 재실행된 데이터/피처 기반인가? | [ ] |
| 세그먼트 수와 기준이 문서화되어 있는가? | [ ] |
| 각 세그먼트의 규모와 이탈 비율이 확정 수치로 기록되었는가? | [ ] |
| 세그먼트 레이블(명칭)이 인과적 표현 없이 기술적으로 작성되었는가? | [ ] |
| 세그먼트 정의가 Stage 08b refinement 결과를 반영하고 있는가? | [ ] |
| 세그먼트별 개입 전략 제안이 "관찰 기반 권고" 수준으로 표현되어 있는가? | [ ] |

---

## 7. Simulation

비즈니스 시뮬레이션 가정이 명시적이고 수치가 추적 가능한지 확인합니다.

| 체크 항목 | 확인 |
|---|---|
| 시뮬레이션 기반 모델이 최종 확정 모델인가? | [ ] |
| 개입 대상 비율(상위 X%) 가정이 명시되어 있는가? | [ ] |
| 개입 성공률 가정이 명시되어 있고 근거가 제시되어 있는가? | [ ] |
| ARPU 또는 구독료 가정이 명시되어 있는가? | [ ] |
| 민감도 분석(가정 변경 시 ROI 변동)이 포함되어 있는가? | [ ] |
| "개입 효과 = A/B 테스트 미검증" 면책 문구가 포함되어 있는가? | [ ] |
| ROI 수치가 확정값이 아닌 추정값으로 표현되어 있는가? | [ ] |

---

## 8. Claim Registry

보고서와 발표에 사용된 주요 수치와 주장이 추적 가능한지 확인합니다.

| 주장 항목 | 출처 파일 | 확정 여부 | 비고 |
|---|---|---|---|
| 최종 분석 대상 행 수 | `02_v2_filter_summary.csv` | [ ] 02b 이후 | PLACEHOLDER |
| 타겟 비율 (Y:N) | `02_v2_*` | [ ] 02b 이후 | PLACEHOLDER |
| 권장 모델 AUC (w1_3) | `06_v2_model_metrics_summary.csv` | [ ] 02b rerun | PLACEHOLDER |
| 최고 성능 모델 AUC (w1_4) | `06_v2_model_metrics_summary.csv` | [ ] 02b rerun | PLACEHOLDER |
| SHAP 상위 피처 | `07_v2_*` | [ ] 02b rerun | PLACEHOLDER |
| 세그먼트 수 및 비율 | `08_v2_*` | [ ] 02b rerun | PLACEHOLDER |
| 시뮬레이션 ROI | `09_v2_*` | [ ] 02b rerun | PLACEHOLDER |
| "상위 10% 이탈 위험군 = 이탈의 X% 포착" | `06_v2_churn_prevented_sensitivity.csv` | [ ] 02b rerun | PLACEHOLDER |

**규칙:** 위 표의 수치를 발표나 보고서에 사용할 때, 반드시 출처 파일과 "provisional / confirmed" 여부를 함께 기록합니다.

---

## 최종 서명 (완료 시 기입)

| 항목 | 완료일 | 확인자 |
|---|---|---|
| Stage 02b 완료 | | |
| Stage 03~09 재실행 완료 | | |
| 본 체크리스트 전항목 완료 | | |
| Stage 10 실행 승인 | | |
