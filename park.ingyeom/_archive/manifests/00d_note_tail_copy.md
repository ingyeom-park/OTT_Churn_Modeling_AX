2. 11x_feature_set_baseline_growth_comparison
3. 12x_feature_set_model_comparison
4. 14x_optuna_candidate_tuning
5. 16x_SHAP_candidate_interpretation
6. 17x_segmentation_design

여기서 11x와 12x는 기존 11b/12c를 대체하는 것이 아니라, 확장 feature set별 비교를 추가하는 단계다.

11x/12x는 반드시 다음 두 플랜을 비교한다.

- conservative_safe_22
- expanded_feature_set

단, expanded_feature_set 내부에서는 context 계열, content/genre 계열, unresolved/forbidden 계열을 구분해 기록한다.

### 6. 멘토/팀원에게 설명할 올바른 표현

안전한 설명:

“기존 11b/12c/14는 폐기하지 않고 conservative safe feature 22개만 사용했을 때의 baseline reference로 보존합니다. 다만 이것이 최종 feature universe를 검토한 모델링은 아니었습니다. 05b에서 review로 분리한 컬럼들을 언제 해소할지 pipeline에 명시하지 않은 설계 누락이 발견되었기 때문에, 13b에서 review feature resolution을 먼저 수행한 뒤 feature set별로 모델 비교를 다시 하겠습니다.”

금지 표현:

- 22개 feature면 충분합니다.
- 12c가 최종 모델 비교입니다.
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
After

이후 모든 모델 비교는 conservative_safe_22와 expanded_feature_set 두 플랜으로 단순화해 보고한다.
expanded_feature_set 내부의 context/content caveat는 별도 플래그로 관리한다.

이 원칙을 어기는 산출물은 final_checks가 PASS여도 canonical으로 인정하지 않는다.
## 00d_full_archive_standardization_260515

- 00d에서 legacy, preliminary, pre-13b conservative_safe_22 산출물, old review zip, handoff snapshot을 표준 archive 구조로 재정리했다.
- 05~14 pre-13b 산출물은 active canonical에서 제거하고 pre13b_conservative_safe_22_reference로 보존한다.
- 이들은 삭제가 아니라 보수 22개 feature 기준 reference로 보존한다.
- 이후 active modeling chain은 13b_review_feature_resolution_and_sensitivity부터 다시 시작한다.
- 모델링 플랜은 conservative_safe_22와 expanded_feature_set 두 가지다.
