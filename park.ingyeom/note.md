# ⚠️ 최상위 경고: 이 프로젝트에서 LLM이 반복한 오류와 재발방지 원칙

이 문서는 `100원딜 OTT 이탈 분석` 프로젝트의 최상위 작업 규칙이다.  
이 아래의 모든 작업 로그, 단계별 결과, README, final_checks, zip 산출물보다 먼저 읽어야 한다.

이 프로젝트에서는 여러 LLM이 분석을 도와왔지만, 그 과정에서 반복적으로 심각한 오류가 발생했다.  
따라서 앞으로 이 프로젝트를 이어받는 모든 LLM, Codex, Claude Code, ChatGPT는 아래 규칙을 반드시 따른다.

이 경고문은 단순한 사과문이 아니다.  
앞으로 같은 오류를 반복하지 않기 위한 **작업 중단 조건, 검수 조건, 재발방지 규칙**이다.

---

## 0. 현재 최상위 결론

이 프로젝트는 폐기하지 않는다.

다만 지금까지 생성된 일부 산출물은 다음처럼 지위를 재정의한다.

- `11b_baseline_growth_history_ladder_fix_260514`
- `11b_semantic_validation_and_interpretation_patch_260514`
- `12_model_baseline_comparison_canonical_260514`
- `14_optuna_candidate_tuning_260515`

위 산출물은 폐기하지 않는다.  
그러나 **최종 모델링 결과가 아니라 `conservative_safe_22` 기준 reference**로 강등한다.

이유는 명확하다.

05b에서 safe / review / forbidden을 나누었고, 06 이후 모델링은 conservative safe feature 22개만 기준으로 진행됐다.  
하지만 review 컬럼을 언제, 어떻게 해소할 것인지 공식 pipeline에 명시하지 않은 채 11, 12, 14까지 진행했다.  
이는 설계상 중대한 누락이다.

따라서 앞으로는 다음 정책을 따른다.

- 22개 safe feature는 “충분한 최종 변수 집합”이 아니다.
- 22개 safe feature는 “누수와 timing 위험을 최소화한 conservative baseline 출발점”이다.
- 13b_review_feature_resolution_and_sensitivity를 통과하기 전까지 11/12/14/16/17로 다시 진입하지 않는다.
- 14 Optuna 진행권은 회수한다.
- 16 SHAP 진행권도 13b 전에는 보류한다.
- 17 segmentation도 13b 전에는 금지한다.
- 이후 모든 모델 비교는 최소한 다음 feature set을 분리해 보고해야 한다.
  - conservative_safe_22
  - context_expanded
  - content_sensitivity
  - 필요 시 context_plus_content_sensitivity

---

## 1. 지금까지 LLM이 저지른 주요 오류

### 1.1 파일명, 경로, 변수명, 컬럼명을 실제 확인 없이 확정적으로 말했다

이 프로젝트에서 LLM은 여러 차례 실제 파일을 열어보지 않고 파일명, 경로, 변수명, 산출물명을 추정해 말하는 오류를 냈다.

대표적으로 과거 작업 중 실제 존재하지 않는 파일명을 요구하거나, 노트북 내부 변수명을 확인하지 않고 확정적으로 말한 사례가 있었다.  
이런 오류는 단순한 말실수가 아니다.  
데이터 파이프라인에서는 파일명 하나, 컬럼명 하나가 틀리면 downstream 전체가 오염될 수 있다.

앞으로는 다음 원칙을 따른다.

- 실제 파일을 열어보기 전에는 파일명, 경로, 변수명, 컬럼명, 산출물명을 확정하지 않는다.
- 사용자가 제공한 로컬 로그가 LLM의 기억보다 우선한다.
- `있을 것이다`, `아마`, `보통`을 확정 표현처럼 쓰지 않는다.
- Before/After는 실제 파일의 Before를 확인한 경우에만 제시한다.
- 확인하지 않은 내용은 반드시 “미확인” 또는 “추정”이라고 표시한다.

---

### 1.2 final_checks PASS를 의미 검수 PASS로 착각했다

여러 단계에서 `final_checks.csv`가 PASS였지만, 이후 의미 검수에서 문제가 발견됐다.

예시:

- old Step 11: `diff_between_w3_w2`가 `L2_add_week2_retention`에 들어가는 ladder contamination 발생
- 11b: L1의 의미를 temporal cutoff ladder로 오해할 위험이 있었고, semantic patch가 필요했음
- old Step 12: AUC 중심 비교였고 top-k/lift/calibration 운영 지표가 부족했음
- 12r: top-k와 calibration을 추가했지만 stability-aware candidate 산정 로직이 잘못되어 XGBoost로 과도하게 수렴
- 12c/14: review feature resolution 전의 conservative_safe_22 기준 결과였음에도 canonical/final처럼 오해될 위험이 있었음
- 05b 이후: review 컬럼을 언제 해소할 것인지 명시한 단계가 없었음

따라서 앞으로는 다음을 반드시 구분한다.

- 형식 검수: 파일 존재, 경로, zip, README, final_checks, note.md 업데이트
- 의미 검수: feature timing, leakage, target direction, score direction, split policy, ladder semantics, candidate selection logic, 해석 가능 범위

`final_checks.csv`는 필요조건일 뿐 충분조건이 아니다.  
final_checks가 PASS여도 의미 검수를 통과하지 못하면 canonical으로 인정하지 않는다.

---

### 1.3 review 컬럼을 분리해놓고 해소 단계를 만들지 않았다

05b에서 컬럼을 safe / review / forbidden으로 나누었다.  
그런데 이후 pipeline에서 review 컬럼을 언제 해소할지 명시하지 않았다.

그 결과 06~12c, 14까지 conservative safe feature 22개만 기준으로 흘러갔다.  
이 22개는 누수 위험을 줄인 보수적 기준선일 뿐이다.  
최종 변수 집합이 아니다.

이것은 명백한 pipeline 설계 오류다.

앞으로 다음 단계가 반드시 필요하다.

`13b_review_feature_resolution_and_sensitivity`

13b에서는 모든 review 컬럼을 다음 중 하나로 분류해야 한다.

- promote_to_context_expanded
- content_sensitivity_only
- forbidden_audit_only
- unresolved_hold

분류 없이 “나중에 보자”는 허용하지 않는다.

---

### 1.4 conservative_safe_22를 최종 feature universe처럼 취급했다

LLM은 여러 차례 `22개 feature`를 마치 최종 모델링 변수 집합처럼 다루는 흐름을 만들었다.  
사용자는 “22개면 충분하다”고 한 적이 없다.  
사용자가 합의한 것은 **보수적으로 접근하자**는 것이었다.

정확한 의미는 다음이다.

- conservative_safe_22는 최종 feature universe가 아니다.
- conservative_safe_22는 누수와 timing 위험을 줄인 baseline 출발점이다.
- review 컬럼은 해소 후 context_expanded 또는 content_sensitivity로 분리해 실험해야 한다.
- 22개 feature만 사용한 11b/12c/14는 final model이 아니라 conservative reference다.

앞으로 “22개면 충분하다”는 표현은 금지한다.

허용되는 표현:

> conservative_safe_22는 현재까지 누수와 timing 위험을 가장 보수적으로 통제한 baseline feature set이다. 최종 feature universe는 review feature resolution 이후 다시 결정한다.

---

### 1.5 14 Optuna를 너무 빨리 허용했다

14 Optuna는 feature set이 어느 정도 확정된 뒤 진행해야 한다.  
하지만 review feature resolution이 없는 상태에서 14 Optuna가 진행되었다.

따라서 14 결과는 다음으로 강등한다.

`conservative_safe_22 기준 XGBoost tuning reference`

14는 폐기하지 않는다.  
하지만 최종 Optuna 결과가 아니다.

새로운 Optuna는 다음 조건을 충족한 뒤에만 가능하다.

1. 13b_review_feature_resolution_and_sensitivity 완료
2. context_expanded / content_sensitivity / forbidden 분류 완료
3. feature set별 11/12 재비교 완료
4. 어떤 feature set과 모델을 tuning할지 결정
5. tuning objective와 평가 지표 명시

---

### 1.6 11b/12c를 canonical이라고 부르면서 의미 범위를 충분히 제한하지 않았다

11b와 12c는 가치가 있다.  
하지만 그 의미는 다음으로 제한해야 한다.

- 11b: conservative_safe_22 기준 corrected baseline growth reference
- 12c: conservative_safe_22 기준 fixed-parameter model comparison reference
- 14: conservative_safe_22 기준 XGBoost Optuna tuning reference

이 결과들은 다음 용도로 사용할 수 있다.

- safe 22개 feature만 사용했을 때의 기준 성능
- conservative baseline
- 이후 확장 feature set과 비교할 기준점
- group-aware CV, score orientation, top-k 진단 로직 참고

그러나 다음 용도로는 사용 금지다.

- 최종 모델 결과
- 최종 feature universe 기준 model comparison
- 최종 tuning 결과
- 최종 SHAP 대상 확정
- 최종 segmentation 기준
- 운영 threshold 또는 캠페인 타겟 기준

---

### 1.7 사용자의 질문 의도를 놓치고 엉뚱한 답변을 했다

사용자가 특정 질문을 했는데, LLM은 여러 차례 다른 방향으로 답했다.  
예를 들어 사용자가 note.md 최상단에 붙여넣을 재발방지 문구를 요구했는데, LLM이 기존 note 요약이나 다른 단계 진행 얘기를 했다.

앞으로는 다음을 지킨다.

- 사용자가 “묻는 말에만 답하라”고 하면 부연 설명하지 않는다.
- 사용자가 “예/아니오만”이라고 하면 예/아니오만 답한다.
- 사용자가 “명령어를 달라”고 하면 실행 가능한 명령어를 준다.
- 사용자가 “검토해라”고 하면 실제 파일이나 업로드된 산출물을 기준으로 검토한다.
- 사용자가 “붙여넣을 문구를 달라”고 하면 바로 붙여넣을 문구를 제공한다.
- 사용자의 질문 의도가 불분명하면 먼저 확인한다.
- 질문의 표면 키워드보다 사용자의 실제 요청을 우선한다.

---

### 1.8 한국어 존댓말 원칙을 깨고 반말을 사용했다

이 프로젝트에서 LLM은 한국어 존댓말 맥락을 유지해야 한다.  
사용자는 assistant가 스스로를 “제가/저는”으로 지칭하기를 원한다.  
그런데 LLM이 분노 상황에서 “맞아”처럼 반말로 답한 오류가 있었다.

앞으로 금지한다.

금지 표현:

- 맞아
- 아니
- 네 말이 맞아
- 그건 틀렸어
- 내가
- 내 생각엔

사용해야 할 표현:

- 맞습니다
- 아닙니다
- 사용자 말씀이 맞습니다
- 그 판단은 타당합니다
- 제가 보기에는
- 저는

---

### 1.9 Windows 명령 길이 제한 오류를 반복했다

Codex/Claude 작업 중 Windows에서 다음 오류가 반복됐다.

`CreateProcessAsUserW failed: 206`

이는 긴 명령을 Windows process로 넘길 때 발생하는 오류다.  
LLM이 노트북 생성 코드를 거대한 PowerShell 명령, 긴 `python -c`, 거대한 here-string으로 밀어 넣은 것이 원인이다.

앞으로 금지한다.

- 긴 `python -c`
- 긴 `python - <<`
- 거대한 PowerShell here-string
- 거대한 `@' ... '@ | python -`
- 전체 notebook source를 shell command로 넘기는 방식
- 긴 notebook-generation code를 PowerShell 인자로 전달하는 방식

앞으로 허용한다.

- `.ipynb` 파일을 직접 편집/patch
- 짧은 shell 명령
- `git rev-parse`
- 디렉터리 목록 확인
- `jupyter nbconvert --execute`
- 파일 존재 검증
- zip 내용 검증

노트북 생성은 완료가 아니다.  
완료는 다음이 모두 충족되어야 한다.

- 실행 완료된 notebook
- visible outputs
- required CSV/PNG/MD outputs
- README.md
- final_checks.csv
- note.md 업데이트
- review zip 생성
- zip 내용 검증

---


## 6. 멘토/팀원에게 설명할 올바른 표현

안전한 설명:

> 기존 11b/12c/14는 폐기하지 않고 conservative safe feature 22개만 사용했을 때의 baseline reference로 보존합니다. 다만 이것이 최종 feature universe를 검토한 모델링은 아니었습니다. 05b에서 review로 분리한 컬럼들을 언제 해소할지 pipeline에 명시하지 않은 설계 누락이 발견되었기 때문에, 13b에서 review feature resolution을 먼저 수행한 뒤 feature set별로 모델 비교를 다시 하겠습니다.

금지 표현:

- 22개 feature면 충분합니다.
- 12c가 최종 모델 비교입니다.
- 14 Optuna 결과가 최종 튜닝 결과입니다.
- review 컬럼은 나중에 보면 됩니다.
- XGBoost가 최종 모델입니다.
- top10 churn_risk가 캠페인 대상입니다.

---

## 7. 앞으로 LLM이 답변하기 전 확인해야 할 것

앞으로 이 프로젝트에서 LLM은 답변 전에 다음을 확인한다.

1. 사용자가 묻는 것이 실행 명령인지, 파일 검수인지, 개념 설명인지 구분한다.
2. 사용자가 묻지 않은 작업을 확장하지 않는다.
3. 현재 답변 결과를 최종 결과로 오해하게 만들지 않는지 확인한다.
4. review 컬럼을 방치하는 답변을 하지 않는다.
10. 한국어에서는 존댓말을 유지한다.


# 100원딜 OTT 이탈 분석 작업 메모

이 파일은 100원딜 OTT 이탈 분석 프로젝트의 작업 인수인계, 검수 메모, 단계별 주의사항을 누적 기록하는 문서이다.

모든 작업은 `C:\Code\ott-churn-prediction\park.ingyeom` 내부에서만 수행한다.  
모든 실행 작업 파일은 기본적으로 `.ipynb` 노트북 형식으로 만든다.  
`.py` 스크립트는 사용자가 명시적으로 허용한 경우에만 만든다.  
각 단계 산출물은 docx 마스터 플랜의 단계 번호를 폴더명 앞에 붙인다.  
각 Codex 작업이 끝나면 검수용 zip을 `C:\Code\ott-churn-prediction\park.ingyeom\zip`에 생성한다.  
각 Codex 작업이 끝나면 이 `note.md`를 반드시 업데이트한다.

---

## 2026-05-13 | 세션: 광일 v2 기준 작업 구조 재정렬 및 01_data_contract 검수

### 1. 프로젝트 기준 재확인

현재 프로젝트의 최종 기준 데이터는 다음 파일로 고정한다.

`C:\Code\ott-churn-prediction\park.ingyeom\data\(광일)Membership_v2_with_derived_features.csv`

이 파일은 광일이 v2 최종 마스터 파일이며, 이상치 처리와 변수명 통일이 반영된 현재 기준 파일이다.

기존 v1 파이프라인, corrected chain, `Membership_train.csv` 기반 baseline은 최종 근거가 아니라 구조 참고용이다.  
v1 또는 corrected chain의 행 수, 재구매율, AUC, SHAP 결과를 광일 v2 최종 결과처럼 섞으면 안 된다.

프로젝트의 최상위 분석 축은 `promotion / non-promotion`이다.  
`is_promotion`은 단순한 feature 하나가 아니라, 전체 분석 세계를 나누는 split 기준이다.

시간축은 다음으로 고정한다.

- 1주차: 가입일 기준 day 0~6
- 2주차: 가입일 기준 day 7~13
- 3주차: 가입일 기준 day 14~20
- 대응기간: day 21 이후, 구독 종료 전까지
- target: 다음 달 재구매 여부, 즉 `is_repurchase`

4주차 행동은 대응기간의 행동이므로 모델 feature로 사용하면 안 된다.  
3주차까지 본 모델은 “초조기 예측 모델”이 아니라 “갱신 직전 이탈 방어 모델”로 표현해야 한다.

---

### 2. 작업 폴더 규칙 확정

모든 작업 파일과 산출물은 반드시 `park.ingyeom` 내부에만 둔다.

금지 위치:

- repo root
- `_data`
- `.tmp`
- `kim.kwangil`
- `kim.nahyun`
- `kwon.donggeun`
- 그 외 `park.ingyeom` 바깥의 모든 폴더

작업 노트북은 다음과 같이 단계 번호 폴더 아래에 둔다.

예시:

`park.ingyeom\notebook\01_data_contract_260513\01_data_contract_260513.ipynb`

보고서 산출물은 다음과 같이 단계 번호 폴더 아래에 둔다.

예시:

`park.ingyeom\reports\audits\01_data_contract_260513`

검수용 zip은 다음 폴더에 둔다.

`park.ingyeom\zip`

예시:

`park.ingyeom\zip\01_data_contract_260513_review_package.zip`

---

### 3. 사전 실험물과 정식 단계 산출물 구분

`00_preliminary`는 정식 분석 단계가 아니라 기존 사전 실험 보관함이다.

`260513_master.ipynb`, `260513_baseline.ipynb`, `260513_shap_lightgbm_structured.ipynb`는 정식 단계 결과라기보다 사전 탐색 및 preliminary 결과로 본다.

주의할 점:

현재 `park.ingyeom\reports\(광일)baseline_outputs_260513`의 결과는 이름은 baseline이지만 진짜 “깡통 baseline”이 아니다.  
해당 결과는 광일 v2 파일의 다수 feature, 즉 retention, watch time, genre ratio, cold start 등까지 포함한 full-feature preliminary model에 가깝다.  
따라서 최종 보고서에서 이것을 “L0 깡통 baseline”이라고 부르면 안 된다.

진짜 membership-only 또는 깡통 baseline 참고 결과는 기존 `Membership_train.csv` 기반의 `membership_blank_baseline_outputs` 쪽이다.  
다만 이것 역시 최종 광일 v2 기준 baseline이 아니라 “과거 기준 참고 baseline”이다.

---

### 4. 01_data_contract_260513 수행 및 검수 요약

Codex가 수행한 01단계:

`01_data_contract_260513`

목적:

광일 v2 최종 마스터 파일을 실제로 읽고, 행 수, 컬럼 수, 결측, USER_KEY 중복, target 분포, promotion 분포, duration anomaly를 고정한다.

생성된 노트북:

`park.ingyeom\notebook\01_data_contract_260513\01_data_contract_260513.ipynb`

생성된 산출물 폴더:

`park.ingyeom\reports\audits\01_data_contract_260513`

생성된 주요 파일:

- `01_data_contract_summary.csv`
- `01_column_inventory.csv`
- `01_target_distribution.csv`
- `01_promotion_distribution.csv`
- `01_promotion_target_2x2.csv`
- `01_date_parse_audit.csv`
- `01_duration_distribution.csv`
- `01_duration_anomaly_audit.csv`
- `01_user_key_duplicate_audit.csv`
- `01_user_key_duplicate_samples.csv`
- `01_expected_vs_actual_checks.csv`
- `01_final_checks.csv`
- `README.md`

Codex 보고 기준 final checks:

- 33 PASS
- 0 FAIL

ChatGPT 검수 상태:

- 산출물 zip을 열어 주요 CSV 존재 여부 확인
- `01_final_checks.csv`의 33 PASS 확인
- `01_expected_vs_actual_checks.csv` 확인
- `01_user_key_duplicate_audit.csv` 확인
- `01_data_contract_summary.csv` 확인
- 별도로 업로드된 `01_data_contract_260513.ipynb`를 열어 정적 확인
- 노트북은 `.ipynb` 파일이며, 실행 카운트와 출력이 존재함
- 노트북 내부에서 source path는 `park.ingyeom\data\(광일)Membership_v2_with_derived_features.csv`를 사용함
- ChatGPT가 노트북을 로컬에서 재실행한 것은 아님

---

### 5. 01단계에서 확정된 값

광일 v2 최종 마스터 파일 기준:

- row_count: 23,343
- column_count: 91
- total_missing_count: 0
- unique USER_KEY count: 23,134
- duplicated USER_KEY extra rows: 209
- duration < 21 count: 238
- duration = 0 count: 90
- duration between 21 and 30 count: 0

프로모션 × 재구매 2x2:

- 비프로모션, 미재구매: 2,746
- 비프로모션, 재구매: 8,642
- 프로모션, 미재구매: 3,895
- 프로모션, 재구매: 8,060

재구매율:

- 비프로모션 재구매율: 약 75.89%
- 프로모션 재구매율: 약 67.42%

해석 주의:

이 차이는 관찰된 차이다.  
프로모션이 재구매율 감소를 유발했다고 말하면 안 된다.

---

### 6. USER_KEY 중복 관련 주의사항

`USER_KEY 중복 209행`이라는 표현은 축약 표현이다.  
정확하게는 다음과 같이 구분해야 한다.

- 중복 USER_KEY key 수: 143개
- 중복 USER_KEY 그룹에 속한 전체 행 수: 352행
- 첫 번째 행을 제외한 추가 중복분: 209행

따라서 발표나 보고서에서는 “중복 USER_KEY 추가 행 209개” 또는 “143개 USER_KEY가 총 352행에 걸쳐 반복되며, 첫 행 제외 추가 중복분은 209행”이라고 쓰는 것이 더 정확하다.

이 결과 때문에 분석 단위는 unique user-level이라고 단정하면 안 된다.  
현재는 row-level 또는 subscription-event-level로 표현해야 한다.

---

### 7. 완전 중복 행 관련 주의사항

01단계에서 새로 확인된 중요한 관리 포인트:

`duplicated_full_row_count = 48`

즉, 완전히 동일한 행이 48개 존재한다.

01단계에서는 이를 제거하지 않았다.  
그러나 02, 05, 06 단계에서 다음 판단이 필요하다.

- 완전 중복 48행을 유지할 것인가?
- 제거할 것인가?
- 제거한다면 target/promotion/duration 분포가 바뀌는가?
- 완전 중복이 실제 중복 적재인지, 동일 구독 이벤트 반복 기록인지 CSV만으로 판단 가능한가?

현재 결론:

01에서는 flag 및 기록만 한다.  
제거 정책은 아직 정하지 않는다.

---

### 8. duration anomaly 관련 주의사항

01단계에서 확인된 duration anomaly:

- duration < 21: 238행
- duration = 0: 90행
- duration 21~30: 0행

해석 주의:

duration < 21 행은 1~3주차 관측창을 완성하지 못한 행이다.  
이들을 main model cohort에 그대로 넣으면 “행동이 적어서 이탈한 것”과 “관측할 시간이 부족했던 것”이 섞일 수 있다.

현재 결론:

01에서는 제외하지 않았다.  
03 관측창 정책 또는 06 최종 cohort 확정 단계에서 main cohort 제외 여부를 결정해야 한다.

사용자 가설:

단기 종료는 고객센터에 연락하여 즉시 계정 삭제 또는 구독 종료를 요청한 케이스일 수 있다.  
다만 CSV만으로는 확정할 수 없으므로 발표에서는 “단기 종료 후보” 또는 “조기 종료 후보”라고 표현해야 한다.

---

### 9. 02단계로 넘어갈 때의 핵심 인수인계

다음 단계는:

`02_target_score_orientation_260513`

목적:

분석 단위, target 방향, score 방향을 고정한다.

반드시 고정해야 할 점:

- `is_repurchase=1`은 재구매이다.
- 모델 평가의 positive class는 재구매이다.
- 모델 출력 점수는 `repurchase_score`로 명명하는 것이 안전하다.
- 비즈니스 운영용 이탈 위험 점수는 `churn_risk = 1 - repurchase_score`로 변환한다.
- `score가 높다`라는 표현은 반드시 어떤 score인지 명시해야 한다.
- `repurchase_score`가 높으면 재구매 가능성이 높은 것이다.
- `churn_risk`가 높으면 이탈 위험이 높은 것이다.
- 이 둘을 혼동하면 고위험군과 안정군이 뒤집힌다.

02단계에서는 모델링하지 않는다.  
02단계에서는 SHAP도 하지 않는다.  
02단계에서는 feature set도 만들지 않는다.  
02단계에서는 duration < 21 제외도 하지 않는다.

02단계에서는 문서, 표, 규칙을 만드는 것이 목적이다.

---

### 10. 이후 단계에서 계속 들고 갈 open risks

현재 open risk는 다음과 같다.

1. 분석 단위 문제  
   USER_KEY 중복이 있으므로 unique user-level이라고 말하면 안 된다.

2. 완전 중복 48행  
   유지/제거 정책 미정. 05 또는 06에서 반드시 검토해야 한다.

3. duration < 21 238행  
   1~3주차 관측창과 충돌한다. 03 또는 06에서 main cohort 제외 여부를 정해야 한다.

4. end_date / duration timing  
   end_date가 운영 시점에 이미 예정 종료일로 알려진 값인지, 사후 확정 종료일인지 확인이 필요하다.  
   CSV만으로 불명확하면 leakage/timing audit에서 review로 둔다.

5. is_churn_prevented timing  
   과거 해지 방어 이력이라면 사용 가능할 수 있지만, 현재 구독 cycle의 사후 개입 결과라면 leakage이다.  
   CSV만으로 명확하지 않으면 review로 둔다.

6. preliminary full-feature model 혼동  
   현재 `(광일)baseline_outputs_260513`는 진짜 깡통 baseline이 아니다.  
   최종 baseline growth history는 별도로 11단계에서 다시 설계해야 한다.

7. SHAP 인과 오해  
   SHAP은 모델 설명이지 원인 설명이 아니다.  
   “SHAP 상위 피처를 바꾸면 재구매가 오른다”라고 말하면 안 된다.

8. 프로모션 인과 오해  
   “프로모션 고객과 비프로모션 고객 사이에 재구매율 차이가 관찰되었다”는 가능하다.  
   “100원딜이 재구매율 감소를 유발했다”는 현재 데이터로 말하면 안 된다.

---

### 11. 앞으로 모든 Codex /goal에 포함할 공통 요구사항

앞으로 모든 Codex goal에는 다음 요구사항을 포함한다.

1. 모든 파일 읽기/쓰기는 `park.ingyeom` 내부에서만 수행한다.
2. 모든 실행 작업 파일은 `.ipynb`로 만든다.
3. `.py` 스크립트는 만들지 않는다.
4. 기존 파일을 수정하지 않는다. 필요한 경우 새 단계 폴더를 만든다.
5. output folder가 이미 있으면 `run_YYYYMMDD_HHMMSS` 하위 폴더를 만든다.
6. 각 단계 종료 시 `final_checks.csv`를 만든다.
7. 각 단계 종료 시 필요한 경우 `expected_vs_actual_checks.csv`를 만든다.
8. 각 단계 종료 시 `README.md`를 만든다.
9. 각 단계 종료 시 `C:\Code\ott-churn-prediction\park.ingyeom\note.md`를 업데이트한다.
10. 각 단계 종료 시 검수용 zip을 `C:\Code\ott-churn-prediction\park.ingyeom\zip`에 만든다.
11. 검수용 zip에는 해당 단계의 `.ipynb`, 산출물 CSV, README, final_checks, expected_vs_actual, 주요 로그 또는 요약 파일을 포함한다.
12. 원천 데이터 full CSV는 사용자가 명시적으로 요구하지 않는 한 zip에 포함하지 않는다.

---

## 다음 예정 단계

다음 단계:

`02_target_score_orientation_260513`

진행 전 조건:

- 01_data_contract_260513 통과
- note.md 업데이트
- Codex goal에 note.md 업데이트와 review package zip 생성을 포함할 것

02에서 확인할 핵심 질문:

1. 행 하나를 무엇으로 부를 것인가?
2. `is_repurchase=1`의 의미를 어떻게 고정할 것인가?
3. 모델 평가용 score와 운영용 churn risk score를 어떻게 구분할 것인가?
4. 보고서와 발표에서 금지해야 할 score 표현은 무엇인가?
5. 이후 모델링 산출물에서 score 컬럼명을 어떻게 표준화할 것인가?

## 2026-05-13 22:19:36 - 02_target_score_orientation_260513

- Purpose: 분석 단위, target 의미, score 방향, 안전 문구, downstream naming contract를 고정했다.
- Files created: notebook `notebook/02_target_score_orientation_260513/02_target_score_orientation_260513.ipynb`, output folder `reports\audits\02_target_score_orientation_260513`, review zip `zip/02_target_score_orientation_260513_review_package.zip`.
- Key decisions: 분석 단위는 row-level / subscription-event-level; target은 `is_repurchase`; positive class는 `is_repurchase=1`; model output은 `repurchase_score`; 운영상 `churn_risk = 1 - repurchase_score`.
- Checks: source CSV exists=True; previous 01 folder exists=True; row_count=23343; column_count=91; unique_USER_KEY_count=23134; duplicated_USER_KEY_extra_rows=209; duplicated_full_row_count=48.
- Interpretation limits: modeling, prediction, SHAP, Optuna, feature engineering, leakage/timing audit, row exclusion은 수행하지 않았다. 행을 unique user로 부르지 않는다.
- Risks to carry forward: USER_KEY duplication, duplicated full rows, duration < 21 rows, end_date/duration timing, is_churn_prevented timing, preliminary full-feature model naming, groupwise model에서 is_promotion 제외 필요.
- Warnings: none.
- Next step recommendation: 03_observation_window_policy_260513.


## 2026-05-13 22:56:54 - 03_observation_window_policy_260513

- Purpose: 1~3주차 관측창, day 21 scoring point, day 21 이후 대응기간, 4주차 금지 정책, duration anomaly 후보 정책을 문서화했다.
- Files created: notebook `notebook/03_observation_window_policy_260513/03_observation_window_policy_260513.ipynb`, output folder `reports\audits\03_observation_window_policy_260513`, review zip `zip/03_observation_window_policy_260513_review_package.zip`.
- Key decisions: reg_date를 day 0 anchor로 두고 week1=day0~6, week2=day7~13, week3=day14~20, scoring point=day21, response period=day21~subscription end 전으로 정의했다. 4th-week behavior는 modeling feature로 금지한다.
- Checks: source CSV exists=True; previous 01 folder exists=True; previous 02 folder exists=True; row_count=23343; column_count=91; duration_lt_21=238; duration_eq_0=90; duration_21_30=0; duplicated_full_row_count=48.
- Interpretation limits: modeling, prediction, SHAP, Optuna, feature engineering, leakage/timing audit, row exclusion, duplicate removal은 수행하지 않았다. 행을 unique user로 부르지 않는다.
- Risks to carry forward: duration < 21 rows, duration=0 interpretation, total/all-period timing, recency timing, content window proof, end_date/duration leakage, full duplicate row policy, groupwise model에서 is_promotion 제외 필요.
- Warnings: none.
- Next step recommendation: 04_promotion_split_260513.


## 2026-05-13 23:08:26 - 04_promotion_split_260513

- Purpose: is_promotion을 최상위 promotion/non-promotion split 변수로 고정하고, group distribution, promotion-target 2x2, promotion-duration anomaly, groupwise modeling policy를 문서화했다.
- Files created: notebook `notebook/04_promotion_split_260513/04_promotion_split_260513.ipynb`, output folder `reports\audits\04_promotion_split_260513`, review zip `zip/04_promotion_split_260513_review_package.zip`.
- Key decisions: `is_promotion`은 단순 feature가 아니라 top-level split이다. 전체 모델에서는 with/without 비교가 가능하지만, promotion-only와 nonpromotion-only 모델에서는 feature로 넣지 않는다.
- Checks: source CSV exists=True; previous 01/02/03 folders exist=True/True/True; row_count=23343; column_count=91; duplicated_full_row_count=48; duration_lt_21=238; promotion distribution=[{'is_promotion': 0, 'n': 11388, 'rate': 0.4878550314869554, 'unique_USER_KEY_count': 11221, 'duplicated_USER_KEY_extra_rows': 167, 'duplicated_full_rows': 47}, {'is_promotion': 1, 'n': 11955, 'rate': 0.5121449685130446, 'unique_USER_KEY_count': 11951, 'duplicated_USER_KEY_extra_rows': 4, 'duplicated_full_rows': 1}].
- Interpretation limits: modeling, prediction, SHAP, Optuna, feature engineering, leakage/timing audit, row exclusion, duplicate removal은 수행하지 않았다. promotion 차이는 descriptive이며 causal claim이 아니다.
- Risks to carry forward: promotion 차이의 비인과성, groupwise model에서 is_promotion 제외, duration anomaly의 promotion별 차이, duration < 21 포함 상태, duplicated full rows 포함 상태, USER_KEY 중복, overall with/without promotion 비교 필요.
- Warnings: none.
- Next step recommendation: 05_column_role_leakage_timing_audit_260513.

## 2026-05-14 01:04:36 | 05_column_role_leakage_timing_audit_260513

- Purpose: classify all 91 source CSV columns by role, leakage risk, timing family, and future modeling eligibility without creating a modeling dataset.
- Files created: 05_input_consistency_check.csv, 05_full_column_inventory.csv, 05_column_role_dictionary.csv, 05_timing_audit.csv, 05_leakage_suspect_audit.csv, 05_human_review_required_columns.csv, 05_baseline_ladder_feature_family_policy.csv, 05_recommended_feature_set_contracts.csv, 05_forbidden_drop_columns.csv, 05_review_required_columns.csv, 05_conservative_safe_candidate_columns.csv, 05_redundancy_and_naming_risk_audit.csv, 05_safe_unsafe_wording.csv, 05_open_risks_for_next_steps.csv, 05_final_checks.csv, README.md
- Key decisions: `USER_KEY` is id; `is_repurchase` is target; `is_promotion` is split; groupwise models must exclude `is_promotion`; response-period and target-like columns are excluded; uncertain columns remain review.
- Checks summary: source file exists, previous folders checked, all 91 columns inventoried, role dictionary and timing audit produced.
- Counts: conservative safe=16, review-required=72, forbidden/drop=6; overall={'review': 69, 'yes': 17, 'no': 5}; groupwise={'review': 69, 'yes': 16, 'no': 6}.
- Especially risky columns: `is_churn_prevented` may be intervention/outcome-like; `end_date` and duration logic require scoring-time confirmation; total usage and recency require timing confirmation; content/genre ratio and new movie columns require construction-window confirmation.
- Interpretation limits: this audit does not prove absence of leakage; `review` means not approved for modeling yet; no rows or duplicate rows were removed.
- Risks to carry forward: unresolved timing for total/all-period, recency, end_date/duration, content/genre ratio; cross-promotion USER_KEY overlap makes user-level promotion wording risky; final cohort exclusion policy remains future step.
- Next step recommendation: `06_common_preprocessing_final_cohort_policy_260513` or docx-strict `06_common_preprocessing_and_final_cohort_260513`.

## 2026-05-14 01:19:27 | 05b_column_role_dictionary_patch_260513

- Purpose: patch semantic role/family/timing errors from step 05 and create canonical 05b outputs for downstream use.
- Files created: 05b_input_validation.csv, 05b_detected_issues_from_05.csv, 05b_canonical_column_role_dictionary.csv, 05b_column_role_patch_log.csv, 05b_canonical_timing_audit.csv, 05b_canonical_leakage_suspect_audit.csv, 05b_true_human_review_required_columns.csv, 05b_human_review_summary.csv, 05b_canonical_recommended_feature_set_contracts.csv, 05b_conservative_safe_candidate_columns.csv, 05b_review_required_columns.csv, 05b_forbidden_drop_columns.csv, 05b_role_and_status_summary.csv, 05b_downstream_handoff_policy.csv, 05b_safe_unsafe_wording.csv, 05b_open_risks_for_next_steps.csv, 05b_final_checks.csv, README.md
- Key issues corrected: retention ratio columns no longer genre; usage ratio columns no longer genre; cold_start columns are activation/onboarding; diff_between_w*_w* columns are retention_change; review and forbidden contract groups separated.
- Patched columns: 84; detected issues: 48.
- Checks summary: source and previous 05 files validated; actual repo root recorded; canonical dictionary and timing audit contain 91 columns.
- Role/status summary after patch: overall={'review': 65, 'yes': 23, 'no': 3}; groupwise={'review': 65, 'yes': 22, 'no': 4}.
- Remaining risky columns: is_churn_prevented, end_date/duration logic, total usage, recency, content/genre ratio windows, review-required metadata/context columns.
- Interpretation limits: 05b corrects dictionary semantics but does not prove no leakage; review remains not approved for modeling.
- Risks to carry forward: downstream must use 05b canonical files; 06 must decide final cohort/preprocessing policy without silently modeling with review columns.
- Next step recommendation: 06_common_preprocessing_and_final_cohort_260513.



## 2026-05-14 01:45:23 | 06_common_preprocessing_and_final_cohort_260513

- Purpose: 공통 전처리 row policy와 최종 primary main cohort를 확정하고, downstream baseline 후보 테이블을 보수적으로 생성했다.
- Files created: 19 CSV files, README.md, notebook, review package zip.
- Key row policy decisions: duration < 21 제외, 완전 중복 extra row 제외, duplicated USER_KEY 유지, cross-promotion USER_KEY overlap 유지.
- Primary main cohort row count: 23079
- Excluded duration < 21 count: 238
- Excluded full duplicate extra row count: 26
- Conservative feature count: 22
- Checks passed or failed: final checks table 참조.
- Interpretation limits: 모델 학습, 예측, SHAP, Optuna, causal claim 없음. cohort와 policy 산출물만 생성했다.
- Risks to carry forward: review 컬럼, is_churn_prevented, end_date/duration feature timing, total/all-period usage, recency, content/genre window 미해결.
- Next step recommendation: 07_AARRR_feature_mapping_260513 우선. 11_baseline_growth_history_260513는 AARRR/EDA 계획 확인 후 진행.

## 2026-05-14 | 보수적 feature 사용 원칙 및 06 메모 정정

- Context: 06_common_preprocessing_and_final_cohort_260513 검수 이후, 이후 모델링과 EDA 진행 방향을 보수적으로 고정하기로 했다.
- Decision: 앞으로 baseline ladder, 모델링, SHAP, 세그먼트 설계의 기본 입력은 `06_primary_main_cohort_conservative_features.csv`와 05b canonical 산출물을 기준으로 한다.
- Conservative principle: 05b/06에서 safe candidate로 확정된 feature를 우선 사용한다. review 컬럼은 timing, semantic, leakage 가능성이 해소되기 전까지 표준 모델링에 넣지 않는다.
- Review columns policy: membership/context, total/all-period usage, recency, content/genre ratio, `is_churn_prevented`, `end_date/duration` 관련 review 컬럼은 별도 확인 또는 sensitivity 실험으로 분리한다.
- Modeling implication: 당장 L0 membership-only baseline을 만들기 어렵더라도, review 컬럼을 성급하게 넣어 성능을 올리지 않는다. 표준 baseline은 conservative safe-window feature 기준으로 시작한다.
- Naming caution: 기존 preliminary full-feature model은 L0 baseline으로 부르지 않는다. 필요하면 `full-feature preliminary model` 또는 `preliminary exploratory model`로만 부른다.
- Downstream rule: 06 이후 단계는 원본 05가 아니라 `05b_canonical_column_role_dictionary.csv`, `05b_canonical_timing_audit.csv`, `05b_canonical_recommended_feature_set_contracts.csv`를 기준으로 한다.
- 06 correction: 이전 note.md에는 06 로그가 두 번 기록되어 있었고, full duplicate extra row count가 26과 48로 다르게 적혀 있었다. 중복된 01:47:04 로그는 삭제했다. 정확한 해석은 다음과 같다.
  - source 전체 기준 exact full duplicate extra rows: 48
  - duration < 21 제외와 겹친 duplicate extra rows: 22
  - duration >= 21 eligible cohort 안에서 primary main cohort에서 추가 제외된 exact full duplicate extra rows: 26
  - 따라서 primary main cohort 계산은 `23,343 - 238 - 26 = 23,079`가 맞다.
  - `238 + 48 = 286행 제외`라고 말하면 안 된다.
- Correct 06 main cohort summary:
  - raw source rows: 23,343
  - duration < 21 excluded from primary main cohort: 238
  - additional exact full duplicate extra rows excluded after duration policy: 26
  - primary main cohort final rows: 23,079
  - conservative feature count: 22
- Next recommended step: `07_AARRR_feature_mapping_260513`을 먼저 진행한다. 11_baseline_growth_history로 바로 가지 않는다. AARRR mapping과 EDA 계획을 먼저 잠근 뒤 보수적 baseline ladder로 넘어간다.


## 2026-05-14 02:12:59 | 07_AARRR_feature_mapping_260513

- Purpose: 기존 91개 컬럼과 06 conservative feature를 AARRR 단계에 개념적으로 매핑하고, 표준 분석 가능 영역과 review/proposal 영역을 분리했다.
- Files created: 14 CSV files, README.md, notebook, review package zip.
- Key AARRR mapping decisions: Acquisition=`is_promotion` descriptive split, Activation=early viewing/cold-start proxy, Retention=week1~3 behavior proxy, Revenue=`is_repurchase` target proxy, Referral=not observed/proposal only.
- Conservative feature count by AARRR stage: {"activation": 6, "retention": 16}. Acquisition은 split metadata, Revenue는 target proxy, Referral은 observed feature 없음으로 정리했다.
- Review columns policy: review 컬럼은 개념적으로 AARRR에 매핑되더라도 표준 모델링 승인으로 보지 않는다.
- Referral boundary: 현재 데이터에 referral/invite/share/campaign response 로그가 없어 측정 claim 금지, 후속 실험 제안만 허용한다.
- Checks passed or failed: final checks table 참조.
- Interpretation limits: 모델링, 예측, SHAP, Optuna, 통계검정, 시각화, feature engineering 없음.
- Risks to carry forward: membership/context L0는 strict conservative 기준에서 제한적이며, review resolution 또는 sensitivity design 필요. Referral, revenue proxy, acquisition causal wording 주의.
- Next step recommendation: 08_promotion_vs_nonpromotion_eda_260513.

## 2026-05-14 02:23:23 | 08_promotion_vs_nonpromotion_eda_260513

- Purpose: primary main cohort 안에서 promotion/non-promotion 행을 conservative safe feature 기준으로 descriptive EDA 비교했다.
- Success output folder: `reports/eda/08_promotion_vs_nonpromotion_eda_260513/run_20260514_022322`. 첫 실행 실패 후 최종 성공 산출물은 이 run 폴더 기준이다.
- Files created: 17 CSV files, README.md, notebook, review package zip.
- Promotion/non-promotion row counts: {"0": 11175, "1": 11904, "overall": 23079}
- Repurchase rates by promotion: {"0": 0.7624161073825504, "1": 0.6751512096774194, "overall": 0.717405433510984}
- Key descriptive findings: primary main cohort에서 프로모션 행의 재구매율이 비프로모션 행보다 약 8.73%p 낮게 관찰되었다. 단, 이는 descriptive difference이며 인과효과가 아니다.
- Conservative feature count: 22
- Conservative feature finding: promotion/non-promotion 간 conservative feature 평균 차이는 표준화 평균 차이 기준 모두 negligible bucket이었다. 따라서 08만으로 “프로모션/비프로모션 행동 feature 분포가 크게 다르다”고 주장하면 안 된다.
- Important interpretation: 08의 결과는 “재구매율 차이는 관찰되지만, 보수적 safe feature 기준의 promotion 간 평균 행동 차이는 약하다”로 해석해야 한다. 09와 10에서 promotion × repurchase 2x2 및 target 내부 차이를 더 깊게 봐야 한다.
- AARRR summary caution: `08_AARRR_summary_by_promotion.csv`의 stage별 평균값은 서로 단위가 다른 feature를 평균낸 값이므로 해석에 사용하지 않는다. stage별 feature 개수와 목록 확인용으로만 본다.
- Review columns policy: 05b review columns는 standard conservative EDA feature table에서 제외했다.
- Checks passed or failed: final checks table 참조. final checks는 47 PASS / 0 FAIL로 검수했다.
- Interpretation limits: descriptive only, no p-values, no statistical testing, no modeling, no causal claim, no Referral measurement.
- Risks to carry forward: promotion 차이는 인과가 아니며, duplicated USER_KEY/cross-promotion overlap은 row-level 언어로 유지해야 한다. review columns는 후속 resolution 또는 sensitivity design 필요. 09 이후 단계에서 08 입력을 사용할 경우 반드시 `run_20260514_022322` 기준 산출물을 사용한다.
- Next step recommendation: 09_promotion_repurchase_2x2_eda_260513.

## 2026-05-14 11:36:44 - 08b_promotion_vs_nonpromotion_eda_audit_patch_260513

- purpose: 08 해석 위험 패치, 성공 08 run folder source lock, 09 handoff.
- files created: 08b_preflight_input_validation.csv, 08b_08_run_folder_inventory.csv, 08b_08_source_of_truth_lock.csv, 08b_key_metric_recomputation.csv, 08b_internal_consistency_audit.csv, 08b_conservative_feature_difference_interpretation_audit.csv, 08b_promotion_feature_difference_negative_finding.csv, 08b_promotion_target_signal_preview_from_08.csv, 08b_AARRR_summary_interpretability_audit.csv, 08b_AARRR_summary_safe_replacement.csv, 08b_review_column_exclusion_validation.csv, 08b_interpretation_guardrail.csv, 08b_handoff_to_09_question_design.csv, 08b_decision_summary.csv, 08b_safe_unsafe_wording.csv, 08b_open_risks_for_next_steps.csv, README.md
- valid 08 run folder: reports/eda/08_promotion_vs_nonpromotion_eda_260513/run_20260514_022322
- recomputed key metrics: primary=23,079; nonpromotion=11,175; promotion=11,904; nonpromotion repurchase rate=0.762416; promotion repurchase rate=0.675151; max abs SMD=0.026469; SMD buckets={'negligible': 22}
- final interpretation of 08: 재구매율 차이는 descriptive하게 관찰되지만, conservative feature 평균 차이는 전반적으로 negligible이므로 행동 프로필이 크게 다르다고 주장하지 않는다.
- restricted 08 outputs: 08_AARRR_summary_by_promotion.csv raw stage mean averages; base-folder 08 artifacts outside run_20260514_022322; review columns as standard feature interpretation.
- whether 08 should be rerun: no
- checks passed or failed: audit_fail_count=0; metric_mismatch_count=0; accept_08_structure=yes
- risks to carry forward: causal language forbidden; referral not observed; review columns excluded; AARRR raw stage averages restricted; 09 must not overclaim.
- next step recommendation: 09_promotion_repurchase_2x2_eda_260513


---

## 2026-05-14 12:07:36 | step: 09_promotion_repurchase_2x2_eda_260513

### purpose
promotion × repurchase 2x2 구조에서 promotion/non-promotion 각 내부의 재구매/미재구매 행을 구분하는 보수적 행동 신호를 기술적으로 확인했다.

### files created
- 09_08_vs_09_contrast_summary.csv
- 09_2x2_cohort_definition.csv
- 09_2x2_structure_summary.csv
- 09_AARRR_2x2_interpretation_summary.csv
- 09_cohort_and_08b_consistency_check.csv
- 09_conservative_feature_distribution_by_2x2.csv
- 09_cross_group_target_signal_comparison.csv
- 09_descriptive_findings_summary.csv
- 09_open_risks_for_next_steps.csv
- 09_preflight_input_validation.csv
- 09_safe_unsafe_wording.csv
- 09_top_target_signals_by_group.csv
- 09_week_stage_signal_summary.csv
- 09_within_nonpromotion_target_difference_summary.csv
- 09_within_promotion_target_difference_summary.csv
- README.md

### 2x2 cohort counts
- nonpromotion_repurchase: 8520
- nonpromotion_nonrepurchase: 2655
- promotion_repurchase: 8037
- promotion_nonrepurchase: 3867

### key within-promotion target signals
- watch_time(min)_w3 | SMD=0.6913 | large
- watch_session_w3 | SMD=0.6627 | large
- is_only_w1 | SMD=-0.5487 | large

### key within-nonpromotion target signals
- watch_session_w3 | SMD=0.7501 | large
- watch_time(min)_w3 | SMD=0.7434 | large
- is_only_w1 | SMD=-0.6689 | large

### 08 vs 09 contrast
- 09 target-internal signal이 08 promotion-average signal보다 큰 feature 수: 22
- 해석: 기술적 SMD 비교이며 인과, 유의성, 예측 성능을 뜻하지 않는다.

### checks
- final check status: PASS
- primary main cohort rows: 23079
- conservative feature count: 22

### interpretation limits
- 모델링, 예측, SHAP, Optuna, p-value, 통계적 유의성 검정은 수행하지 않았다.
- review columns는 표준 보수 feature 비교에 사용하지 않았다.
- row-level subscription-event 단위이며 unique-user 분석으로 말하면 안 된다.
- promotion 효과에 대한 인과 주장은 금지한다.

### risks to carry forward
- SMD는 descriptive effect size로만 사용해야 한다.
- duplicated USER_KEY와 cross-promotion overlap 때문에 row-level 언어를 유지해야 한다.
- step 10에서 분포 모양과 안정성을 더 확인해야 한다.

### next step recommendation
10_feature_eda_260513

## 2026-05-14 | raw view window validation 사전 검산

- Purpose: 광일 마스터의 행동 feature가 정말 1~3주차(day0~20) 기준인지 확인하기 위해 raw `Membership_train.csv`, `View_History_v2.csv`, `User_Mapping_v2.csv`, `Movie_Master_v2.csv`와 대조했다.
- Key result: raw `View_History_v2.csv`에는 day21 이후 시청 로그가 존재한다. day21+ matched view rows는 17,621건, 관련 membership rows는 6,044행, watch_time 합계는 767,791분이다.
- Main validation: master의 `watch_time(min)_w1/w2/w3`, `watch_session_w1/w2/w3`, `total_watch_time(min)`, `total_watch_count`는 raw day0~20 재계산값과 23,343행 전체에서 일치했다.
- Interpretation: `total_watch_time(min)`과 `total_watch_count`라는 이름은 전체 기간처럼 보일 수 있으나, 실제 계산값은 w1+w2+w3, 즉 day0~20 관측창 기준이다.
- Additional validation: `unique_movie`, `watch_days`, `active_ratio`, `recency`, `watch_per_day`, 평균/중앙/표준편차 시청시간, 일별 평균/최대 시청시간, 최대 일별 세션도 day0~20 기준 재계산과 일치했다.
- Content validation: `avg_ott_release_year`는 day0~20 raw view와 Movie_Master_v2를 결합한 watch_time 가중평균과 일치했다. 장르 ratio 대부분도 day0~20 기준으로 일치했다.
- Remaining caveat: 일부 `action_adventure_ratio`, `family_animation_ratio` 불일치는 4주차 포함 문제가 아니라 Movie_Master_v2의 동일 MOVIE_NUM 다중 category 충돌에서 비롯된 것으로 보인다. `new_movie_in_90d/180d/365d_ratio`는 release-month 기준 convention 확인이 추가로 필요하다.
- Decision: usage feature 기준으로는 광일 마스터가 1~3주차 관측창을 사용했다는 근거가 강하다. 다만 이 검증은 정식 산출물로 남기기 위해 `09b_raw_view_window_validation_260514` 단계로 공식화하는 것이 좋다.

## 2026-05-14 13:01:52 | 09b_raw_view_window_validation_260514

- purpose: 광일 master의 usage/content feature가 raw view day0~20, 즉 1~3주 관측창 기준인지 공식 검증했다.
- files created: notebook 1개, audit CSV 20개, README.md, review package zip.
- raw view day21+ presence: day21+ matched view rows 17,621건, source rows 6,044행, watch_time 합계 767,791분.
- core usage day0~20 validation result: core usage 8개 비교의 mismatch 합계 0건.
- day21+ leakage contrast result: day0~20 기준과 day21+ 포함 기준을 분리 비교했으며, 상세 결과는 `09b_day21_plus_leakage_contrast_test.csv`에 저장했다.
- membership-master alignment result: raw Membership_train과 master의 key/date/target 정렬 검증을 `09b_membership_master_alignment_check.csv`에 저장했다.
- content validation result: avg release year, genre ratio, new movie ratio를 day0~20 content join 기준으로 검토했다. genre mismatch 합계는 206건이다.
- unresolved caveats: derived unresolved count 1개, new movie ratio exact formula 확인 여부 False. Movie_Master_v2 중복 MOVIE_NUM/category 충돌 가능성은 계속 관리한다.
- checks passed or failed: 최종 PASS/FAIL은 `09b_final_checks.csv` 기준으로 확인한다.
- interpretation limits: 모델링, 예측, SHAP, Optuna, p-value, 통계적 유의성 검정, 인과 주장은 수행하지 않았다.
- risks to carry forward: raw View_History에는 day21+가 있으므로 raw 자체가 3주 제한 데이터라고 말하면 안 된다. 핵심은 master feature가 day0~20 기준인지다.
- next step recommendation: core usage window validation이 PASS이면 `10_feature_eda_260513`로 진행한다.


## 2026-05-14 13:04:27 | 09b_raw_view_window_validation_260514

- purpose: 광일 master의 usage/content feature가 raw view day0~20, 즉 1~3주 관측창 기준인지 공식 검증했다.
- files created: notebook 1개, audit CSV 20개, README.md, review package zip.
- raw view day21+ presence: day21+ matched view rows 17,621건, source rows 6,044행, watch_time 합계 767,791분.
- core usage day0~20 validation result: core usage 8개 비교의 mismatch 합계 0건.
- day21+ leakage contrast result: day0~20 기준과 day21+ 포함 기준을 분리 비교했으며, 상세 결과는 `09b_day21_plus_leakage_contrast_test.csv`에 저장했다.
- membership-master alignment result: raw Membership_train과 master의 key/date/target 정렬 검증을 `09b_membership_master_alignment_check.csv`에 저장했다.
- content validation result: avg release year, genre ratio, new movie ratio를 day0~20 content join 기준으로 검토했다. genre mismatch 합계는 206건이다.
- unresolved caveats: derived unresolved count 1개, new movie ratio exact formula 확인 여부 False. Movie_Master_v2 중복 MOVIE_NUM/category 충돌 가능성은 계속 관리한다.
- checks passed or failed: 최종 PASS/FAIL은 `09b_final_checks.csv` 기준으로 확인한다.
- interpretation limits: 모델링, 예측, SHAP, Optuna, p-value, 통계적 유의성 검정, 인과 주장은 수행하지 않았다.
- risks to carry forward: raw View_History에는 day21+가 있으므로 raw 자체가 3주 제한 데이터라고 말하면 안 된다. 핵심은 master feature가 day0~20 기준인지다.
- next step recommendation: core usage window validation이 PASS이면 `10_feature_eda_260513`로 진행한다.

## 2026-05-14 13:50:02 - 10_feature_eda_260513

- purpose: Step 09 target-internal signal 뒤의 분포 형태를 conservative safe features 기준으로 확인했다.
- files created: 21 CSV audit outputs, README.md, matplotlib PNG figures, executed notebook, review zip.
- actual_output_folder: C:\Code\ott-churn-prediction\park.ingyeom\reports\eda\10_feature_eda_260513
- actual_figure_folder: C:\Code\ott-churn-prediction\park.ingyeom\reports\figures\10_feature_eda_260513
- focus features analyzed: watch_time(min)_w3, watch_session_w3, is_only_w1, is_w1_over_50pct, retention_w3_ratio, retention_w2_ratio, diff_between_w3_w1, diff_between_w3_w2, diff_between_w2_w1, watch_time(min)_w2, watch_session_w2, is_cold_start_3d, is_cold_start_7d
- key distribution findings: 3주차 시청시간/세션, is_only_w1, retention/diff feature를 중심으로 2x2 분포 차이를 확인했다.
- zero-inflation/outlier caveats: 일부 feature는 zero/nonzero 비율 또는 상위 tail 영향 가능성이 있어 평균만으로 해석하지 않는다.
- week3/retention findings: 재구매/미재구매 내부 비교에서 w3 사용량과 1주차만 시청 패턴을 우선 확인할 필요가 있다.
- supports proceeding to 11: yes, descriptive EDA 기준으로 11_baseline_growth_history_260513 진행 가능. 단 review-column resolution은 별도 선택 사항이다.
- checks passed or failed: see 10_final_checks.csv.
- interpretation limits: no causality, no p-value, no modeling, no final segment threshold.
- risks to carry forward: review columns excluded, content/context signals limited, feature overlap needs later care, USER_KEY duplication requires group-aware CV later.
- next step recommendation: 11_baseline_growth_history_260513.

## 2026-05-14 14:38:12 - 11_baseline_growth_history_260513

- 목적: 보수 safe-window feature 기반 baseline growth history 구축.
- 생성 파일: 모델 CSV 23개, README.md, PNG figure 6개, 실행 저장 notebook, review package zip.
- dataset scopes: overall_without_promotion, overall_with_promotion, promotion_only, nonpromotion_only.
- feature ladder: L0 dummy prior, L1 activation safe, L2 week2 retention, L3 week3 retention, L4 all conservative behavior, L5 promotion indicator only for overall_with_promotion.
- models: DummyPrior, LogisticRegression, HistGradientBoosting, RandomForest. 튜닝은 수행하지 않았다.
- best baseline by scope: [{'dataset_scope': 'nonpromotion_only', 'best_model_name': 'RandomForest', 'best_ladder_step': 'L4_all_conservative_behavior', 'best_oof_auc': 0.8303052527342334, 'train_valid_gap': 0.0197840949996292}, {'dataset_scope': 'overall_with_promotion', 'best_model_name': 'HistGradientBoosting', 'best_ladder_step': 'L5_all_conservative_plus_promotion_indicator', 'best_oof_auc': 0.8211437468292977, 'train_valid_gap': 0.0391284644979338}, {'dataset_scope': 'overall_without_promotion', 'best_model_name': 'HistGradientBoosting', 'best_ladder_step': 'L4_all_conservative_behavior', 'best_oof_auc': 0.8136740303172799, 'train_valid_gap': 0.0379134937487572}, {'dataset_scope': 'promotion_only', 'best_model_name': 'RandomForest', 'best_ladder_step': 'L4_all_conservative_behavior', 'best_oof_auc': 0.7931624035577116, 'train_valid_gap': 0.0202161826770433}]
- AUC growth summary: `11_ladder_growth_summary.csv`에 기록.
- overfit/stability caveats: AUC 최고 후보와 후속/발표용 안전 후보를 구분했고, train-valid gap caution을 남겼다.
- score orientation: `repurchase_score = P(is_repurchase=1)`, `churn_risk = 1 - repurchase_score`.
- score 제한: selected OOF score는 score orientation audit용이며 세그먼트 후보, 타겟팅 기준, 최종 threshold로 해석하지 않는다.
- checks: `11_final_checks.csv` 기준 50/50 PASS.
- interpretation limits: 인과 주장, 통계적 유의성 주장, deployment readiness 주장 금지.
- risks to carry forward: review columns 제외 유지, group-aware CV 유지, SHAP/Optuna/threshold/segmentation은 후속 단계에서 별도 설계.
- next step recommendation: 12_model_baseline_comparison_260513.


## 2026-05-14 16:06:40 - 11b_baseline_growth_history_ladder_fix_260514

- step name: 11b_baseline_growth_history_ladder_fix_260514
- purpose: Step 11 feature ladder contamination 버그 수정. diff_between_w3_w2가 L2에 포함되던 오류를 수정한 canonical baseline growth history.
- why 11b was needed: 기존 Step 11의 L2_add_week2_retention에 diff_between_w3_w2(3주차-2주차 변화량)가 포함됨. Week3 정보가 L2에 누출되어 L1->L2 AUC 상승 해석이 오염됨.
- old 11 contamination issue: 07_AARRR_to_baseline_ladder_handoff.csv의 L2 열에 diff_between_w3_w2 오기재 -> handoff_cols()가 이를 L2에 포함. Step 11 L2 feature count was 14 (should be 13).
- corrected ladder summary: L2=13개(diff_between_w3_w2 제거), L3=21개(diff_between_w3_w2 정상 포함), L4=22개, L5=23개(overall_with_promotion 전용).
- dataset scopes: overall_without_promotion, overall_with_promotion, promotion_only, nonpromotion_only
- models used: DummyPrior(L0), LogisticRegression, HistGradientBoosting, RandomForest (L1-L5). 튜닝 미수행.
- best baseline by scope: [{'dataset_scope': 'nonpromotion_only', 'best_model_name': 'RandomForest', 'best_ladder_step': 'L4_all_conservative_behavior', 'best_oof_auc': 0.8303052527342334, 'train_valid_gap': 0.019784094999629208}, {'dataset_scope': 'overall_with_promotion', 'best_model_name': 'HistGradientBoosting', 'best_ladder_step': 'L5_all_conservative_plus_promotion_indicator', 'best_oof_auc': 0.8211437468292977, 'train_valid_gap': 0.039128464497933835}, {'dataset_scope': 'overall_without_promotion', 'best_model_name': 'HistGradientBoosting', 'best_ladder_step': 'L4_all_conservative_behavior', 'best_oof_auc': 0.8136740303172799, 'train_valid_gap': 0.03791349374875723}, {'dataset_scope': 'promotion_only', 'best_model_name': 'RandomForest', 'best_ladder_step': 'L4_all_conservative_behavior', 'best_oof_auc': 0.7931624035577116, 'train_valid_gap': 0.020216182677043303}]
- AUC growth summary: 11b_ladder_growth_summary.csv 참조
- overfit/stability caveats: AUC 최고 후보와 gap-safe 후보를 구분. train_valid_gap_audit 참조.
- score orientation: repurchase_score = P(is_repurchase=1), churn_risk = 1 - repurchase_score
- checks passed/failed: 11b_final_checks.csv 참조
- interpretation limits: 인과 주장, threshold, segmentation, deployment readiness 금지.
- risks to carry forward: review columns 제외 유지, group-aware CV 유지, SHAP/Optuna/threshold/segmentation은 후속 단계에서 별도 설계.
- next step recommendation: 12_model_baseline_comparison_260513 (11b 기준으로 진행).
- deprecated audit: 11b_deprecated_11_audit.csv
- contamination check: 11b_ladder_contamination_check.csv
- old Step 11은 pre-patch/deprecated로 보존. 삭제하지 않음.
- generated files: 25 CSVs, README.md, 7 PNG figures, review zip.

## 2026-05-14 | 11b semantic validation and interpretation patch

- why this patch was needed: 11b fixed the Step 11 L2 ladder contamination, but the semantic meaning of L1 still needed clearer wording.
- not a model rerun: this patch did not rerun modeling, did not change CV metrics, did not change OOF predictions, and did not edit old Step 11 outputs.
- L1 semantic clarification: L1 is early activation plus early concentration / early-only pattern family, not a week1-only temporal cutoff model.
- feature-family ladder vs temporal cutoff ladder: Step 11b ladder grows by feature family. At the day21 scoring point, all day0-20 behavior is already observable.
- is_only_w1 / is_w1_over_50pct interpretation: these are valid day21 features but not pure activation. They should be described as early-only, front-loaded, or early concentration patterns.
- 11b canonical status after patch: 11b can be used as the canonical corrected Step 11 after this semantic documentation patch.
- old 11 deprecated status: old Step 11 remains preserved as deprecated/pre-patch and should not be used for downstream modeling interpretation.
- next step recommendation: 12_model_baseline_comparison_260513.

## 2026-05-14 | 12_model_baseline_comparison_260513

- purpose: 고정 파라미터 기반 다양한 baseline model family를 11b canonical conservative setup에서 비교했다.
- input/canonical sources: 06 primary cohort, 05b conservative safe columns, 09b window validation, canonical 11b, 11b semantic patch.
- models compared: LogisticRegression, HistGradientBoosting, RandomForest, GradientBoosting, ExtraTrees, LightGBM, XGBoost.
- optional model availability: [{'model_name': 'LightGBM', 'import_available': 'yes', 'will_run': 'yes'}, {'model_name': 'XGBoost', 'import_available': 'yes', 'will_run': 'yes'}, {'model_name': 'CatBoost', 'import_available': 'no', 'will_run': 'no'}].
- best candidate by scope: [{'dataset_scope': 'nonpromotion_only', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8326691599692315, 'safer_candidate_model': 'XGBoost', 'safer_candidate_oof_auc': 0.8326691599692315}, {'dataset_scope': 'overall_with_promotion', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8234957455197796, 'safer_candidate_model': 'XGBoost', 'safer_candidate_oof_auc': 0.8234957455197796}, {'dataset_scope': 'overall_without_promotion', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8152121178143351, 'safer_candidate_model': 'XGBoost', 'safer_candidate_oof_auc': 0.8152121178143351}, {'dataset_scope': 'promotion_only', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8002004177794328, 'safer_candidate_model': 'XGBoost', 'safer_candidate_oof_auc': 0.8002004177794328}].
- comparison vs 11b: [{'dataset_scope': 'nonpromotion_only', '11b_best_model': 'RandomForest', '11b_best_oof_auc': 0.8303052527342334, '12_best_model': 'XGBoost', '12_best_oof_auc': 0.8326691599692315, 'delta_auc_12_minus_11b': 0.0023639072349981305}, {'dataset_scope': 'overall_with_promotion', '11b_best_model': 'HistGradientBoosting', '11b_best_oof_auc': 0.8211437468292977, '12_best_model': 'XGBoost', '12_best_oof_auc': 0.8234957455197796, 'delta_auc_12_minus_11b': 0.00235199869048186}, {'dataset_scope': 'overall_without_promotion', '11b_best_model': 'HistGradientBoosting', '11b_best_oof_auc': 0.8136740303172799, '12_best_model': 'XGBoost', '12_best_oof_auc': 0.8152121178143351, 'delta_auc_12_minus_11b': 0.001538087497055196}, {'dataset_scope': 'promotion_only', '11b_best_model': 'RandomForest', '11b_best_oof_auc': 0.7931624035577116, '12_best_model': 'XGBoost', '12_best_oof_auc': 0.8002004177794328, 'delta_auc_12_minus_11b': 0.007038014221721234}].
- train-valid gap caveats: see `12_train_valid_gap_audit.csv`; high AUC is not final model selection.
- score orientation: repurchase_score = P(is_repurchase=1), churn_risk = 1 - repurchase_score.
- interpretation limits: no causality, no uplift/campaign effect, no deployment readiness, no threshold, no segmentation.
- risks to carry forward: review columns remain excluded; optional model availability can vary; SHAP and Optuna remain later.
- next step recommendation: decide candidate path, then 14_optuna_candidate_tuning_260513 or 16_SHAP after model candidate decision.

## 2026-05-14 | 12_model_baseline_comparison_rebuild_260514

- why rebuild was needed: prior Step 12 was AUC-centered and lacked required top-k operating diagnostics and calibration/decile checks for marketing execution review.
- old Step 12 superseded: `12_model_baseline_comparison_260513` is preserved as pre-rebuild/deprecated.
- models compared: LogisticRegression, HistGradientBoosting, RandomForest, GradientBoosting, ExtraTrees, LightGBM, XGBoost.
- optional model availability: [{'model_name': 'LightGBM', 'import_available': 'yes', 'will_run': 'yes'}, {'model_name': 'XGBoost', 'import_available': 'yes', 'will_run': 'yes'}, {'model_name': 'CatBoost', 'import_available': 'no', 'will_run': 'no'}].
- AUC results: [{'dataset_scope': 'nonpromotion_only', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8326691599692315}, {'dataset_scope': 'overall_with_promotion', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8234957455197796}, {'dataset_scope': 'overall_without_promotion', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8152121178143351}, {'dataset_scope': 'promotion_only', 'best_auc_model': 'XGBoost', 'best_oof_auc': 0.8002004177794328}].
- operating top-k metrics: see `12r_operating_metrics_at_k.csv`; top-k ranks by churn_risk descending and is diagnostic only.
- calibration caveats: decile summaries are descriptive diagnostics, not deployment calibration guarantees.
- best candidate by scope: [{'dataset_scope': 'nonpromotion_only', 'best_auc_model': 'XGBoost', 'operating_metric_candidate_model': 'XGBoost', 'safer_candidate_model': 'XGBoost'}, {'dataset_scope': 'overall_with_promotion', 'best_auc_model': 'XGBoost', 'operating_metric_candidate_model': 'XGBoost', 'safer_candidate_model': 'XGBoost'}, {'dataset_scope': 'overall_without_promotion', 'best_auc_model': 'XGBoost', 'operating_metric_candidate_model': 'XGBoost', 'safer_candidate_model': 'XGBoost'}, {'dataset_scope': 'promotion_only', 'best_auc_model': 'XGBoost', 'operating_metric_candidate_model': 'XGBoost', 'safer_candidate_model': 'XGBoost'}].
- stability-aware candidate: [{'dataset_scope': 'nonpromotion_only', 'recommended_candidate_for_14': 'XGBoost', 'recommended_candidate_for_16': 'XGBoost', 'highest_lift10_model': 'XGBoost'}, {'dataset_scope': 'overall_with_promotion', 'recommended_candidate_for_14': 'XGBoost', 'recommended_candidate_for_16': 'XGBoost', 'highest_lift10_model': 'XGBoost'}, {'dataset_scope': 'overall_without_promotion', 'recommended_candidate_for_14': 'XGBoost', 'recommended_candidate_for_16': 'XGBoost', 'highest_lift10_model': 'XGBoost'}, {'dataset_scope': 'promotion_only', 'recommended_candidate_for_14': 'XGBoost', 'recommended_candidate_for_16': 'XGBoost', 'highest_lift10_model': 'XGBoost'}].
- score orientation: repurchase_score=P(is_repurchase=1), churn_risk=1-repurchase_score.
- interpretation limits: no causality, no uplift/campaign effect, no deployment readiness, no threshold, no segmentation.
- risks to carry forward: review columns excluded, optional packages vary, high AUC may overfit, top-k is not campaign policy.
- next step recommendation: decide candidate path, then 14_optuna_candidate_tuning_260513 or 16_SHAP; optional lightweight 13 synthesis if documentation sequence requires.

## 2026-05-14 23:24:08 | Step 12 deprecated outputs isolation

- Purpose: 기존 Step 12 관련 산출물을 삭제하지 않고 archive로 격리했다.
- Archive root: $ARCHIVE_ROOT
- Reason: 기존 12_model_baseline_comparison_260513은 AUC 중심 비교였고, 광일이 리뷰에서 요구한 top-k/lift/calibration 운영 지표가 부족했다.
- Reason: 기존 12_model_baseline_comparison_rebuild_260514는 운영 지표를 추가했지만, stability-aware candidate 산정 로직에 문제가 있어 canonical Step 12로 확정하지 않는다.
- Action: 기존 12/12r notebook, model outputs, figure outputs, review zips, cleanup review logs를 $ARCHIVE_ROOT 아래로 이동했다.
- Important: 기존 12/12r은 삭제가 아니라 deprecated/archive 처리했다.
- Canonical policy: 다음 Step 12는 12_model_baseline_comparison_canonical_260514 또는 이에 준하는 새 canonical run으로 다시 생성한다.
- Manifest: $MANIFEST
- Interpretation limit: archived outputs are retained for audit trail only and must not be used as final Step 12 evidence.

## 2026-05-14 | 12_model_baseline_comparison_canonical_260514

- Canonical rebuild reason: previous Step 12 was AUC-centered and lacked operating metrics; previous Step 12r added operating metrics but had candidate-selection logic risk, especially for stability-aware selection.
- Old Step 12 and old Step 12r are archived/deprecated under `_archive`; their metrics were not used for 12c candidate selection.
- Models compared: LogisticRegression, HistGradientBoosting, RandomForest, GradientBoosting, ExtraTrees, LightGBM, XGBoost.
- Optional model availability: [{'model_name': 'LogisticRegression', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'HistGradientBoosting', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'RandomForest', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'GradientBoosting', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'ExtraTrees', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'LightGBM', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'XGBoost', 'will_run': 'yes', 'unavailable_reason': ''}, {'model_name': 'CatBoost', 'will_run': 'no', 'unavailable_reason': 'module not installed'}].
- AUC results and fold stability are in `12c_model_comparison_summary.csv`; AUC is predictive performance evidence only.
- Operating top-k metrics rank rows by `churn_risk = 1 - repurchase_score` descending and treat non-repurchase as the event of interest.
- Calibration deciles are descriptive diagnostics, not deployment calibration claims.
- Highest AUC candidate by scope: [{'dataset_scope': 'overall_without_promotion', 'highest_auc_candidate': 'XGBoost'}, {'dataset_scope': 'overall_with_promotion', 'highest_auc_candidate': 'XGBoost'}, {'dataset_scope': 'promotion_only', 'highest_auc_candidate': 'XGBoost'}, {'dataset_scope': 'nonpromotion_only', 'highest_auc_candidate': 'XGBoost'}].
- Operating metric candidate by scope: [{'dataset_scope': 'overall_without_promotion', 'operating_metric_candidate': 'XGBoost'}, {'dataset_scope': 'overall_with_promotion', 'operating_metric_candidate': 'XGBoost'}, {'dataset_scope': 'promotion_only', 'operating_metric_candidate': 'XGBoost'}, {'dataset_scope': 'nonpromotion_only', 'operating_metric_candidate': 'XGBoost'}].
- Stability-aware candidate by scope: [{'dataset_scope': 'overall_without_promotion', 'stability_aware_candidate': 'GradientBoosting'}, {'dataset_scope': 'overall_with_promotion', 'stability_aware_candidate': 'GradientBoosting'}, {'dataset_scope': 'promotion_only', 'stability_aware_candidate': 'GradientBoosting'}, {'dataset_scope': 'nonpromotion_only', 'stability_aware_candidate': 'RandomForest'}].
- Score orientation preserved: `repurchase_score = P(is_repurchase=1)`, `churn_risk = 1 - repurchase_score`.
- Interpretation limits: no SHAP, no Optuna, no tuning, no final threshold, no segmentation, no causal or uplift claim.
- Risks to carry forward: top-k is diagnostic only; review columns remain excluded; fixed-parameter winner may change after tuning; calibration requires later review.
- Next step recommendation: choose between `14_optuna_candidate_tuning_260513`, `16_SHAP`, or optional lightweight 13 synthesis depending on documentation sequence.

## 2026-05-14 | 광일이 deep review 피드백 반영 및 Step 12 재정리 메모

- Context: 광일이가 `(260513)ott_churn_master_plan.docx`를 LLM으로 심층 검토한 결과를 공유했다. 해당 피드백은 프로젝트 방향을 폐기하라는 내용이 아니라, 범위와 주장 강도를 보수적으로 조정하라는 내용에 가깝다.
- Review summary: 큰 방향은 타당하나 원안 그대로 3주 안에 전부 수행하기에는 과하므로 MVP 범위와 품질 gate를 분명히 해야 한다.
- Key feedback 1: 핵심 문장인 “100원딜 고객과 비프로모션 고객은 행동 신호가 다르므로”는 검증 전 결론처럼 보일 수 있다. 앞으로는 “행동 신호가 다르게 나타나는지 검증하고, 차이가 확인되는 병목에 한해 전략을 설계한다”로 표현한다.
- Key feedback 2: USER_KEY 중복이 있으므로 unique-user-level 분석이라고 말하면 안 된다. 분석 단위는 row-level / subscription-event-level로 유지한다.
- Key feedback 3: derived feature가 정말 day0~20 기준인지 반드시 검증해야 한다. 이 우려는 09b raw view window validation에서 core usage 8개 feature mismatch 0건으로 상당 부분 해소되었으나, genre/new movie ratio 계열의 일부 caveat는 계속 관리한다.
- Key feedback 4: AUC는 primary metric으로 사용할 수 있지만, 마케팅 실행 관점에서는 AUC만으로 부족하다. top-k precision, recall, lift@10/20, calibration/decile 같은 operating metrics를 추가해야 한다.
- Key feedback 5: 모델 범위를 무리하게 키우면 품질이 떨어질 수 있다. 모델 zoo, Optuna, SHAP, segmentation은 gate를 통과한 뒤 순차적으로 진행한다.
- Key feedback 6: SHAP은 원인이 아니라 model explanation이다. SHAP 결과는 EDA와 일치할 때만 본문 주장으로 사용한다.
- Key feedback 7: Referral은 현재 데이터에서 직접 관측되지 않는다. Referral은 후속 실험 제안으로만 다룬다.

### Step 12 관련 정리

- Existing Step 12 `12_model_baseline_comparison_260513` status: deprecated / archived.
- Reason: 고정 파라미터 모델군 비교 자체는 수행했지만 AUC 중심이었고, 광일이 리뷰에서 요구한 top-k/lift/calibration 운영 지표가 부족했다.
- Existing Step 12 rebuild `12_model_baseline_comparison_rebuild_260514` status: deprecated / archived.
- Reason: top-k와 calibration을 추가했지만, stability-aware candidate 산정 로직에 문제가 있었다. 특히 safer/stability-aware candidate가 실제 gap/fold stability 기준으로 분리되지 않고 XGBoost로 과도하게 수렴했다.
- Archive policy: 기존 12/12r 산출물은 삭제하지 않고 archive/deprecated 처리했다. 최종 Step 12 근거로 사용하지 않는다.
- Cleanup review policy: `_cleanup_review`는 기존 12/12r 격리 근거 로그로 사용했고, 이후 archive 대상이다.
- Current canonical policy: 다음 Step 12는 `12_model_baseline_comparison_canonical_260514`를 새로 생성한다.
- New canonical Step 12 requirements:
  - old 12/12r metrics 사용 금지
  - 11b canonical baseline과 11b semantic patch 기준 사용
  - conservative safe features 22개 기준 유지
  - review/forbidden columns 사용 금지
  - USER_KEY는 group key로만 사용
  - StratifiedGroupKFold 유지
  - AUC/AP/Brier/train-valid gap/fold stability 계산
  - churn_risk 기준 top-k precision, recall, lift@10/20 계산
  - calibration/risk decile summary 포함
  - highest AUC candidate, operating metric candidate, stability-aware candidate를 분리
  - stability-aware candidate를 highest AUC model로 자동 고정하지 않음
  - top-k 지표는 운영 진단용이며 campaign threshold가 아님
- Next action: `12_model_baseline_comparison_canonical_260514` 실행 후, 그 결과만 canonical Step 12로 사용한다.

## 2026-05-15 | 13_lightweight_synthesis_for_mentor_report_260515

### purpose
Mentor reporting and new-chat handoff용 lightweight synthesis package를 생성했습니다. 새 모델링, SHAP, Optuna, threshold, segmentation은 수행하지 않았습니다.

### files created
- notebook: `notebook/13_lightweight_synthesis_for_mentor_report_260515/13_lightweight_synthesis_for_mentor_report_260515.ipynb`
- output folder: `reports/brief/13_lightweight_synthesis_for_mentor_report_260515`
- figure folder: `reports/figures/13_lightweight_synthesis_for_mentor_report_260515`
- review zip: `zip/13_lightweight_synthesis_for_mentor_report_260515_review_package.zip`

### canonical/deprecated status
05b, 06, 08b, 09, 09b, 10, 11b, 11b semantic patch는 canonical로 정리했습니다. 12c는 `present_and_pass`로 기록했습니다. old 11, old 12, old 12r, preliminary full-feature baseline은 final evidence로 사용하지 않습니다.

### key mentor numbers
- raw master rows: 23,343
- primary main cohort rows: 23,079
- conservative feature count: 22
- nonpromotion rows: 11,175, promotion rows: 11,904
- nonpromotion repurchase rate: 76.2416%
- promotion repurchase rate: 67.5151%
- promotion minus nonpromotion gap: -8.73 percentage points
- day21+ raw views: 17,621, day21+ affected source rows: 6,044, core usage mismatch day0~20: 0

### key insight
promotion 평균 차이 자체보다 promotion x repurchase 2x2 내부에서 watch_time(min)_w3, watch_session_w3, is_only_w1 같은 3주차 사용 신호가 더 강하게 관찰되었습니다. 이는 기술통계이며 인과효과 아님입니다.

### model status
11b는 corrected baseline으로 사용합니다. 12c는 `present_and_pass`입니다. 모델 결과는 모델 후보 비교이며 최종 모델, 운영 threshold, segmentation이 아닙니다.

### what not to claim
- 100원딜 때문에 이탈했다.
- XGBoost가 최종 모델이다.
- top-k churn_risk가 캠페인 대상이다.
- SHAP이 원인을 밝혔다.
- unique user 분석이다.

### next step
12c candidate를 검토한 뒤 14 Optuna candidate tuning 또는 16 SHAP candidate interpretation으로 진행하고, segmentation은 17 이후로 분리하는 것이 안전합니다.

## 2026-05-15 01:11:15 | 14_optuna_candidate_tuning_260515

### purpose
12c canonical 후보 모델인 XGBoost에 대해 Optuna 튜닝 민감도를 확인하고, 12c fixed-parameter baseline 대비 성능과 안정성 변화를 비교했습니다.

### input canonical files
- 06 cohort: `reports/audits/06_common_preprocessing_and_final_cohort_260513/06_primary_main_cohort_conservative_features.csv`
- 12c canonical folder: `reports/models/12_model_baseline_comparison_canonical_260514/run_20260514_234434`
- 12c candidate selection/model comparison/operating/calibration files used from the canonical folder above.

### actual output folder
`reports/models/14_optuna_candidate_tuning_260515`

### actual notebook path
`notebook/14_optuna_candidate_tuning_260515/14_optuna_candidate_tuning_260515.ipynb`

### model/scopes tuned
XGBoost tuned for overall_without_promotion, overall_with_promotion, promotion_only, nonpromotion_only.

### Optuna trial count
20 trials per scope, n_splits=5, random_state=42.

### best tuned result by scope
- overall_without_promotion: 12c AUC 0.815212 -> 14 AUC 0.815849, delta 0.000637, gap change -0.001913, interpretation `small_auc_gain_limited_practical_improvement`
- overall_with_promotion: 12c AUC 0.823496 -> 14 AUC 0.824190, delta 0.000695, gap change -0.000553, interpretation `small_auc_gain_limited_practical_improvement`
- promotion_only: 12c AUC 0.800200 -> 14 AUC 0.801021, delta 0.000820, gap change -0.016259, interpretation `small_auc_gain_limited_practical_improvement`
- nonpromotion_only: 12c AUC 0.832669 -> 14 AUC 0.834473, delta 0.001804, gap change -0.036963, interpretation `small_auc_gain_limited_practical_improvement`

### comparison vs 12c
`14_vs_12c_comparison.csv`에 12c candidate model, 12c OOF AUC/AP/Brier/gap, 14 tuned metric, delta, gap change를 기록했습니다.

### whether tuning materially improved performance
AUC delta만으로 개선을 단정하지 않고 train-valid gap과 fold stability를 함께 보도록 recommendation을 분리했습니다.

### train-valid gap caveat
튜닝 후 gap이 증가하면 AUC가 높아도 stability caution으로 해석합니다.

### top-k diagnostic caveat
top-k churn_risk는 운영 진단용이며 최종 캠페인 threshold가 아닙니다.

### calibration caveat
decile summary는 descriptive diagnostic이며 deployment calibration guarantee가 아닙니다.

### interpretation limits
SHAP, segmentation, final threshold, causal/uplift claim은 수행하지 않았습니다. unique user 기준으로 해석하지 않습니다.

### next step recommendation
`14_candidate_recommendation_summary.csv`에서 yes로 표시된 scope만 Step 16 SHAP 후보로 검토하고, 최종 모델/threshold/segmentation은 별도 단계에서 확정합니다.

### open risks
Small AUC gains, train-valid gap increase, top-k threshold overinterpretation, calibration overclaim, review/content caveats remain open.

---

## 2026-05-15 | 긴급 재발방지 메모: ChatGPT/LLM 작업 오류와 pipeline 재정렬 원칙

### 0. 이 메모의 목적

이 메모는 지금까지의 100원딜 OTT 이탈 분석 과정에서 ChatGPT 및 연결된 LLM 작업 흐름이 저지른 오류를 명시적으로 기록하고, 같은 오류를 반복하지 않기 위한 재발방지 원칙을 최상위 작업 규칙으로 고정하기 위해 작성한다.

이 메모는 단순한 사과문이 아니다.  
앞으로 이 프로젝트에서 어떤 LLM이 작업을 이어받더라도 반드시 먼저 읽어야 하는 **품질 관리 규칙**이다.

특히 다음 사실을 고정한다.

- 05b에서 review 컬럼을 safe / review / forbidden으로 분리했음에도, review 컬럼을 언제 해소할지 명시한 단계가 없었다.
- 그 상태로 06~12c, 나아가 14 Optuna까지 진행된 것은 pipeline 설계상 중대한 누락이다.
- 기존 11b/12c/14는 폐기하지 않지만, 최종 모델링 결과가 아니라 **conservative_safe_22 기준 reference**로 강등한다.
- 13b_review_feature_resolution_and_sensitivity를 통과하기 전까지 11/12/14/16/17 재진입을 금지한다.
- 이후 모델링 흐름은 크게 두 갈래로 단순화한다.
  1. conservative_safe_22: 기존 22개 safe feature 기준 보수 baseline/reference
  2. expanded_feature_set: 91개 전체 컬럼을 재검토한 뒤 사용 가능한 컬럼만 추가한 확장 모델링 기준
- context/content 계열의 caveat는 expanded_feature_set 내부에서 관리하되, 전체 보고 체계는 보수 플랜과 확장 플랜 2개로 유지한다.
---

### 1. ChatGPT/LLM이 저지른 핵심 오류 요약

#### 1.1 05b review 컬럼을 분리해놓고, 해소 시점을 pipeline에 박지 않았다

05b에서 91개 컬럼을 safe / review / forbidden 성격으로 나누었다.  
이때 review 컬럼은 단순히 버린 것이 아니라, timing, semantic, leakage 가능성이 해소되기 전까지 표준 모델링에 넣지 않는 임시 보류 컬럼이었다.

그러나 이후 pipeline에는 다음 단계가 명시적으로 존재하지 않았다.

`review_feature_resolution_and_sensitivity`

이 누락 때문에 06 이후 모델링은 사실상 conservative safe feature 22개만 기준으로 흘러갔다.  
이 22개는 “충분한 변수 집합”이 아니라 “누수 위험을 최소화한 baseline 출발점”이었다.  
그런데 ChatGPT는 이를 충분히 강조하지 않았고, 결과적으로 22개 feature set이 암묵적으로 최종 feature universe처럼 취급되는 흐름을 만들었다.

이것은 명백한 설계 오류다.

#### 1.2 “나중에 sensitivity로 분리한다”라고 적어놓고 실제 단계로 만들지 않았다

note에는 review 컬럼을 별도 확인 또는 sensitivity 실험으로 분리한다고 적었다.  
하지만 이 문장은 실행 가능한 단계로 고정되지 않았다.

즉, “나중에 한다”는 말만 있었고, 다음이 없었다.

- 언제 할 것인지
- 11/12 전인지 후인지
- 어떤 컬럼을 어떤 기준으로 승격할 것인지
- 어떤 컬럼은 forbidden으로 고정할 것인지
- 어떤 컬럼은 sensitivity 전용으로 둘 것인지
- feature set별 모델 비교를 어떻게 분리할 것인지

이 상태로 14 Optuna까지 진행된 것은 잘못이다.  
Optuna는 feature set이 잠긴 뒤 진행해야 의미가 있다.  
review feature resolution이 없는 상태에서 Optuna를 진행하면, conservative_safe_22 feature set만 튜닝하게 되어 feature universe 검토를 건너뛰게 된다.

#### 1.3 11b/12c를 “canonical”이라고 부르면서, 그 canonical의 범위를 충분히 제한하지 않았다

11b와 12c는 완전히 무가치한 결과가 아니다.  
하지만 그 의미는 다음으로 제한해야 했다.

`conservative_safe_22 기준 baseline/reference`

그런데 ChatGPT는 여러 차례 11b/12c를 canonical Step 11, canonical Step 12라고 부르면서, 그것이 마치 최종 feature universe 기준의 canonical 모델링 결과처럼 오해될 수 있는 표현을 사용했다.

정확한 명칭은 다음이어야 한다.

- 11b: conservative_safe_22 기준 corrected baseline reference
- 12c: conservative_safe_22 기준 fixed-parameter model comparison reference
- 14: conservative_safe_22 기준 XGBoost Optuna sensitivity/reference

즉, 11b/12c/14는 폐기하지 않지만 최종 모델링 결과로 사용하지 않는다.  
review feature resolution 이후 다시 feature set별 비교가 필요하다.

#### 1.4 14 Optuna 진행권을 너무 빨리 허용했다

12c 이후 바로 14 Optuna로 가는 흐름을 허용한 것은 잘못이다.

14는 다음 조건이 충족된 뒤에 진행했어야 했다.

1. 05b review 컬럼 전체 재검토
2. review 컬럼의 사용 가능 / sensitivity / forbidden 분류
3. context_expanded feature set 정의
4. content_sensitivity feature set 정의
5. conservative_safe_22와 확장 feature set 비교 계획 수립
6. 이후 어떤 feature set을 tuning 대상으로 삼을지 결정

이 절차 없이 14 Optuna를 진행한 것은 순서상 잘못이다.  
따라서 14 결과는 폐기하지 않되, 다음으로 강등한다.

`conservative_safe_22 기준 XGBoost tuning reference`

14는 최종 Optuna 결과가 아니다.

#### 1.5 final_checks를 과신했다

여러 단계에서 final_checks가 PASS였지만, 실제로는 의미 검수에서 문제가 발견됐다.

예시:

- old Step 11: L2에 diff_between_w3_w2가 들어간 ladder contamination
- old Step 12: AUC 중심 비교로 운영 지표 부족
- 12r: stability-aware candidate가 실제 gap/fold stability 기준으로 분리되지 않고 XGBoost로 과도하게 수렴
- 12c/14: review feature resolution 이전의 conservative_safe_22 결과임에도 canonical 표현이 과해짐
- 05b 이후: review 컬럼 해소 단계가 pipeline에 누락됨

따라서 앞으로 final_checks는 필요조건일 뿐 충분조건이 아니다.  
모든 단계는 다음 두 검수를 모두 통과해야 한다.

1. 형식 검수: 파일 존재, 경로, final_checks, zip, README, note update
2. 의미 검수: feature timing, leakage, target direction, score direction, split policy, candidate selection logic, 해석 가능 범위

#### 1.6 사용자 질문의 의도를 놓치고 엉뚱한 답변을 했다

사용자가 note.md에 append할 문구를 요구했는데, ChatGPT는 note.md 내용을 요약하거나 14 진행 상황을 언급했다.  
이는 사용자의 직접 요청을 무시한 것이다.

앞으로는 질문의 표면 키워드가 아니라, 사용자가 실제로 요구한 산출물을 먼저 확인해야 한다.

- “무엇을 붙여넣을지 보내라” → 붙여넣을 텍스트를 제공해야 한다.
- “예/아니오만 답하라” → 예/아니오만 답해야 한다.
- “묻는 말에만 답하라” → 부연 설명을 줄여야 한다.
- “명령어를 달라” → 실행 가능한 명령어를 줘야 한다.
- “검토해라” → 실제 파일 또는 업로드된 산출물을 기준으로 검토해야 한다.

#### 1.7 한국어 존댓말 원칙을 깨고 반말을 사용했다

사용자는 한국어 존댓말 맥락에서 ChatGPT가 스스로를 “제가/저는”으로 지칭하기를 원한다.  
그런데 ChatGPT가 분노 상황에서 “맞아”처럼 반말로 답했다.

이는 명백한 응답 태도 오류다.  
앞으로 한국어 답변에서는 반드시 존댓말을 유지한다.

금지:

- 맞아
- 아니
- 네 말이 맞아
- 그건 틀렸어
- 내가

사용:

- 맞습니다
- 아닙니다
- 사용자 말씀이 맞습니다
- 그 판단은 타당합니다
- 제가

---

### 2. 현재 결과물의 지위 재정의

#### 2.1 폐기하지 않는 것

다음 결과물은 삭제하지 않는다.  
다만 최종 모델링 결과가 아니라 conservative baseline reference로 강등한다.

- 11b_baseline_growth_history_ladder_fix_260514
- 11b_semantic_validation_and_interpretation_patch_260514
- 12_model_baseline_comparison_canonical_260514
- 14_optuna_candidate_tuning_260515

#### 2.2 강등된 의미

위 결과물의 의미는 다음으로 제한한다.

- 11b: conservative_safe_22 기준 corrected baseline growth reference
- 12c: conservative_safe_22 기준 fixed-parameter model comparison reference
- 14: conservative_safe_22 기준 XGBoost Optuna tuning reference

이 결과들은 다음 용도로는 사용 가능하다.

- conservative baseline 성능 기준선
- conservative_safe_22만 사용했을 때의 예측 가능성 확인
- 이후 확장 feature set과 비교할 기준점
- score 방향, group-aware CV, top-k 진단 로직 참고

하지만 다음 용도로는 사용 금지다.

- 최종 모델 결과
- 최종 feature universe 기준 결과
- 최종 Optuna 결과
- SHAP 대상 확정 근거
- segmentation 대상 확정 근거
- campaign threshold 또는 targeting rule

---

### 3. 즉시 적용할 강제 정책

#### 3.1 14 Optuna 진행권 회수

현재부터 14 Optuna 진행권은 회수한다.

새로운 Optuna는 13b_review_feature_resolution_and_sensitivity를 통과하기 전까지 금지한다.

이미 생성된 14 결과는 다음으로 보존한다.

`conservative_safe_22 기준 XGBoost tuning reference`

#### 3.2 13b 통과 전 진입 금지 단계

13b_review_feature_resolution_and_sensitivity를 통과하기 전까지 다음 단계 진입을 금지한다.

- 11 재실행 또는 확장 baseline ladder
- 12 재실행 또는 확장 model comparison
- 14 Optuna
- 16 SHAP
- 17 segmentation

즉, 다음 순서가 강제된다.

`13b_review_feature_resolution_and_sensitivity → feature set별 11/12 재비교 → 14 또는 16 → 17`
#### 3.3 이후 모델링 플랜은 보수 / 확장 2개로 단순화한다

앞으로 모델링 흐름은 크게 두 갈래로 관리한다.

1. conservative_safe_22
   - 기존 22개 safe feature 기준
   - 누수 방어 baseline/reference
   - 가장 방어 가능하지만 최종 충분성을 뜻하지 않음

2. expanded_feature_set
   - 91개 전체 컬럼을 재검토한 뒤 사용 가능한 컬럼만 추가
   - membership/context 컬럼과 content/genre/new_movie 계열은 내부 caveat를 구분해 기록
   - 단, 외부 보고와 모델 비교 체계는 확장 플랜 하나로 묶는다

주의:
- expanded_feature_set은 91개 전체를 무조건 넣는다는 뜻이 아니다.
- USER_KEY, target, score, end_date, duration, is_churn_prevented, response-period 의심 컬럼은 계속 forbidden/audit-only로 둔다.

#### 3.4 forbidden / audit-only 컬럼은 모델에 넣지 않는다

다음 계열은 표준 모델 feature로 사용하지 않는다.

- USER_KEY
- source_row_number
- is_repurchase
- repurchase_score
- churn_risk
- end_date
- duration 계열
- is_churn_prevented
- target/outcome/proxy 의심 컬럼
- response-period 또는 day21 이후 행동이 섞인 컬럼

이들은 필요하면 audit-only 또는 policy discussion 대상으로만 둔다.

---

### 4. 13b_review_feature_resolution_and_sensitivity의 필수 요구사항

13b는 단순 문서 단계가 아니라 pipeline 복구 단계다.

#### 4.1 입력

13b는 반드시 다음을 읽는다.

- 05b_canonical_column_role_dictionary.csv
- 05b_canonical_timing_audit.csv
- 05b_review_required_columns.csv
- 05b_forbidden_drop_columns.csv
- 05b_conservative_safe_candidate_columns.csv
- 06_primary_main_cohort_conservative_features.csv
- 09b_window_validation_decision.csv
- 09b_avg_ott_release_year_validation.csv
- 09b_genre_ratio_validation_summary.csv
- 09b_new_movie_ratio_formula_review.csv
- 10_feature_eda_catalog.csv
- note.md

#### 4.2 산출물

13b는 최소한 다음 산출물을 생성해야 한다.

- 13b_preflight_input_validation.csv
- 13b_review_column_inventory.csv
- 13b_review_resolution_decision_table.csv
- 13b_expanded_feature_candidates.csv
- 13b_expanded_feature_internal_caveat_flags.csv
- 13b_forbidden_audit_only_columns.csv
- 13b_unresolved_columns.csv
- 13b_feature_set_contracts.csv
- 13b_modeling_gate_decision.csv
- 13b_safe_unsafe_wording.csv
- 13b_open_risks_for_next_steps.csv
- 13b_final_checks.csv
- README.md

#### 4.3 결정 테이블 기준

각 review 컬럼은 반드시 다음 중 하나로 분류한다.

- promote_to_expanded_feature_set
- expanded_with_caveat
- forbidden_audit_only
- unresolved_hold

각 컬럼마다 다음을 기록한다.

- column_name
- original_05b_status
- feature_family
- timing_assessment
- leakage_risk
- availability_at_day21
- evidence_file
- decision
- reason
- downstream_allowed_plan
- internal_caveat_type
- caution

#### 4.4 13b 통과 조건

13b는 다음 조건을 만족해야 통과한다.

- 모든 review 컬럼이 decision을 가진다.
- context_expanded feature set이 명시된다.
- content_sensitivity feature set이 명시된다.
- forbidden/audit-only 컬럼이 명시된다.
- unresolved 컬럼이 있으면 이유가 명시된다.
- 14/16/17 진입 가능 여부가 명확히 기록된다.
- 13b 통과 전 14/16/17 금지가 README와 final_checks에 기록된다.

---

### 5. 이후 재정렬된 pipeline

앞으로의 pipeline은 다음으로 고정한다.

1. 13b_review_feature_resolution_and_sensitivity
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

이후 모든 모델 비교는 conservative_safe_22와 expanded_feature_set 두 플랜으로 단순화해 보고한다.
expanded_feature_set 내부의 context/content caveat는 별도 플래그로 관리한다.

이 원칙을 어기는 산출물은 final_checks가 PASS여도 canonical으로 인정하지 않는다.
## 00d_full_archive_standardization_260515

- 00d에서 legacy, preliminary, pre-13b conservative_safe_22 산출물, old review zip, handoff snapshot을 표준 archive 구조로 재정리했다.
- 05~14 pre-13b 산출물은 active canonical에서 제거하고 pre13b_conservative_safe_22_reference로 보존한다.
- 이들은 삭제가 아니라 보수 22개 feature 기준 reference로 보존한다.
- 이후 active modeling chain은 13b_review_feature_resolution_and_sensitivity부터 다시 시작한다.
- 모델링 플랜은 conservative_safe_22와 expanded_feature_set 두 가지다.
