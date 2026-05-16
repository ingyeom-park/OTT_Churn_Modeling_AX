- 14 Optuna 결과가 최종 튜닝 결과입니다.
- review 컬럼은 나중에 보면 됩니다.
- XGBoost가 최종 모델입니다.
- top10 churn_risk가 캠페인 대상입니다.

---

### 7. ChatGPT/LLM에 대한 최상위 행동 규칙

앞으로 이 프로젝트를 이어받는 모든 LLM은 다음을 지킨다.

1. 사용자의 질문에 먼저 정확히 답한다.
2. 사용자가 “묻는 말에만 답하라”고 하면 부연 설명을 줄인다.
3. 파일명, 경로, 컬럼명, 수치, 산출물명은 실제 파일 또는 사용자 로그에 존재하는 것만 확정 표현한다.
4. final_checks PASS만으로 의미 검수까지 통과했다고 말하지 않는다.
5. review 컬럼을 “나중에”로 미루지 않는다.
6. conservative_safe_22를 최종 feature universe처럼 말하지 않는다.
7. 모델 결과를 인과효과나 캠페인 효과로 해석하지 않는다.
8. score 방향을 항상 확인한다.
   - repurchase_score = P(is_repurchase=1)
   - churn_risk = 1 - repurchase_score
9. top-k 위험군은 churn_risk 내림차순으로만 계산한다.
10. 한국어 응답에서는 존댓말을 유지한다.
11. assistant는 스스로를 “제가” 또는 “저는”으로 지칭한다.
12. 실수를 발견하면 즉시 인정하고, 영향 범위와 복구 위치를 말한다.
13. 사용자가 의심을 제기하면 방어하지 말고 실제 검증 대상으로 전환한다.
14. 기존 산출물을 지울 때는 삭제보다 archive/deprecated 격리를 우선한다.
15. 기존 ipynb는 자산이다. 결과물이 오염됐다고 해서 노트북을 무조건 폐기하지 않는다. 복사본을 만들어 패치 후 재실행한다.

---

### 8. 현재 기준 최종 결론

현재 프로젝트는 폐기하지 않는다.  
다만 모델링 pipeline은 재정렬한다.

기존 11b/12c/14는 다음 지위로 강등한다.

`conservative_safe_22 reference`

14 Optuna 진행권은 회수한다.  
13b_review_feature_resolution_and_sensitivity 통과 전까지 11/12/14/16/17 진입을 금지한다.  

이후 모든 모델 비교는 conservative_safe_22와 expanded_feature_set 두 플랜으로 단순화해 보고한다.
expanded_feature_set 내부의 context/content caveat는 별도 플래그로 관리한다.

이 원칙을 어기는 산출물은 final_checks가 PASS여도 canonical으로 인정하지 않는다.
## 00d_full_archive_standardization_260515

- 00d에서 legacy, preliminary, pre-13b conservative_safe_22 산출물, old review zip, handoff snapshot을 표준 archive 구조로 재정리했다.
- 05~14 pre-13b 산출물은 active canonical에서 제거하고 pre13b_conservative_safe_22_reference로 보존한다.
- 이들은 삭제가 아니라 보수 22개 feature 기준 reference로 보존한다.
- 이후 active modeling chain은 13b_review_feature_resolution_and_sensitivity부터 다시 시작한다.
- 모델링 플랜은 conservative_safe_22와 expanded_feature_set 두 가지다.

## 2026-05-15 02:31:36 | 05x_feature_contract_rebuild_260515

- purpose: 기존 05~14 pre-13b 산출물이 archive로 격리된 상태에서 91개 전체 컬럼을 재검토하고 사용자 승인용 feature contract를 작성했다.
- pre-13b 지위: 05~14 pre-13b 결과는 _archive/pre13b_conservative_safe_22_reference에 보존됨. canonical 복원 안 함.
- conservative_safe_22 count: 22
- expanded_feature_set candidate count (incl conservative_22): 84
- forbidden_or_audit_only count: 4
- unresolved count: 1
- user_approval_checklist items: 66
- LLM 원칙: LLM은 feature 최종 제외/승격을 결정하지 않는다. 근거와 후보만 제시. 최종 결정은 사용자 승인 후 확정.
- final_checks: PASS (fail_count=0)
- output_dir: C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\05x_feature_contract_rebuild_260515
- next step: 06x_dataset_generation (사용자 승인 후 진행)
- gate: 05x_user_approval_checklist.csv 승인 전 06x/11/12/14/16/17 진행 금지

## 2026-05-15 16:24:05 | 05x_feature_contract_rebuild_patch_260515

- 05x patch 수행.
- 기존 05x의 decision table 오류 수정.
- USER_KEY와 is_repurchase는 모델 feature 금지로 정책상 고정.
- price/max_screen은 사용자 확인 필요 항목으로 표시.
- 05x patch 이후에도 최종 feature 사용 여부는 사용자 승인 전까지 확정 아님.
- 06x는 사용자 승인 후 진행.
- output_dir: C:\Code\ott-churn-prediction\park.ingyeom\reports\audits\05x_feature_contract_rebuild_patch_260515
- review_zip: C:\Code\ott-churn-prediction\park.ingyeom\zip\05x_feature_contract_rebuild_patch_260515_review_package.zip