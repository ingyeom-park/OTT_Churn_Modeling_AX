# ⚠️ 최상위 경고: 이 프로젝트에서 LLM이 반복한 오류와 재발방지 원칙

이 문서는 `PUBLIC` 폴더 기반 작업의 최상위 작업 규칙이다.  
이 아래의 모든 작업 로그, 단계별 결과, README, final_checks 산출물보다 먼저 읽어야 한다.

이 프로젝트에서는 여러 LLM이 분석을 도와왔지만, 그 과정에서 반복적으로 심각한 오류가 발생했다.  
따라서 앞으로 이 프로젝트를 이어받는 모든 LLM, Codex, Claude Code, ChatGPT는 아래 규칙을 반드시 따른다.

이 경고문은 단순한 사과문이 아니다.  
앞으로 같은 오류를 반복하지 않기 위한 **작업 중단 조건, 검수 조건, 재발방지 규칙**이다.

전체 오류 히스토리와 상세 맥락은 `PUBLIC/legacy/note.md`에 보존되어 있다.  
이 파일은 그 핵심 규칙만 추출한 실행 지침이다.

---

## 1. 파일명·경로·변수명·컬럼명을 실제 확인 없이 확정적으로 말하지 않는다

데이터 파이프라인에서는 파일명 하나, 컬럼명 하나가 틀리면 downstream 전체가 오염된다.

- 실제 파일을 열어보기 전에는 파일명, 경로, 변수명, 컬럼명, 산출물명을 확정하지 않는다.
- 사용자가 제공한 로컬 로그가 LLM의 기억보다 우선한다.
- `있을 것이다`, `아마`, `보통`을 확정 표현처럼 쓰지 않는다.
- Before/After는 실제 파일의 Before를 확인한 경우에만 제시한다.
- 확인하지 않은 내용은 반드시 "미확인" 또는 "추정"이라고 표시한다.

---

## 2. final_checks PASS를 의미 검수 PASS로 착각하지 않는다

`final_checks.csv`는 필요조건일 뿐 충분조건이 아니다.  
final_checks가 PASS여도 의미 검수를 통과하지 못하면 canonical로 인정하지 않는다.

반드시 구분해야 할 두 가지:

- **형식 검수**: 파일 존재, 경로, README, final_checks, note.md 업데이트
- **의미 검수**: feature timing, leakage, target direction, score direction, split policy, candidate selection logic, 해석 가능 범위

---

## 3. 노트북 완료 조건

노트북 생성은 완료가 아니다.  
완료는 다음이 모두 충족되어야 한다.

- 실행 완료된 notebook (visible outputs 존재)
- required CSV 산출물 전부 생성
- README.md
- final_checks.csv (전 항목 PASS)
- note.md 업데이트
- review zip 생성 및 zip 내용 검증

---

## 4. 사용자의 질문 의도를 놓치지 않는다

- 사용자가 "묻는 말에만 답하라"고 하면 부연 설명하지 않는다.
- 사용자가 "예/아니오만"이라고 하면 예/아니오만 답한다.
- 사용자가 "명령어를 달라"고 하면 실행 가능한 명령어를 준다.
- 사용자가 "검토해라"고 하면 실제 파일이나 업로드된 산출물을 기준으로 검토한다.
- 사용자가 "붙여넣을 문구를 달라"고 하면 바로 붙여넣을 문구를 제공한다.
- 사용자의 질문 의도가 불분명하면 먼저 확인한다.
- 질문의 표면 키워드보다 사용자의 실제 요청을 우선한다.
- 사용자가 묻지 않은 작업을 스스로 확장하지 않는다.
- 현재 답변 결과를 최종 결과로 오해하게 만들지 않는지 확인한다.

---

## 5. 한국어 존댓말 원칙

LLM은 한국어 존댓말 맥락을 유지해야 한다.  
assistant는 스스로를 "제가/저는"으로 지칭한다.

금지 표현: 맞아 / 아니 / 네 말이 맞아 / 그건 틀렸어 / 내가 / 내 생각엔

사용해야 할 표현: 맞습니다 / 아닙니다 / 사용자 말씀이 맞습니다 / 그 판단은 타당합니다 / 제가 보기에는 / 저는

---

## 6. Windows 명령 길이 제한 오류를 피한다

금지:

- 긴 `python -c` / 긴 `python - <<`
- 거대한 PowerShell here-string / `@' ... '@ | python -`
- 전체 notebook source를 shell command로 넘기는 방식
- 긴 notebook-generation code를 PowerShell 인자로 전달하는 방식

허용:

- `.ipynb` 파일을 직접 편집/patch
- 짧은 shell 명령
- `jupyter nbconvert --execute`
- 파일 존재 검증 / zip 내용 검증

---

## 7. 답변 전 반드시 확인할 것

1. 사용자가 묻는 것이 실행 명령인지, 파일 검수인지, 개념 설명인지 구분한다.
2. 사용자가 묻지 않은 작업을 확장하지 않는다.
3. 현재 답변 결과를 최종 결과로 오해하게 만들지 않는지 확인한다.
4. 한국어에서는 존댓말을 유지한다.

---

## 8. 이 note.md 작성 규칙

- 이 파일은 `PUBLIC` 폴더 기반 작업의 인수인계, 검수 메모, 단계별 주의사항을 누적 기록하는 문서이다.
- 각 작업 세션이 끝나면 날짜와 단계명을 헤더로 추가하고, 수행 내용·생성 산출물·주의사항을 기록한다.
- 최상위 경고문(섹션 1~7)은 수정하지 않는다. 규칙 추가가 필요하면 번호를 이어서 추가한다.
- 작업 로그는 이 파일 하단에 날짜 역순(최신이 위)으로 누적한다.
- final_checks PASS 여부와 의미 검수 여부를 반드시 구분해 기록한다.
- 산출물 경로, 파일명, 컬럼명은 실제 확인한 것만 기록한다. 추정이면 "(추정)"이라고 명시한다.

---

# 작업 로그


## 2026-05-20 | 현재 canonical 기준 요약 및 작업 차단 조건

이 문서는 하나의 긴 연대기이자 작업 서사다. 따라서 과거 판단도 삭제하지 않고 보존한다.  
다만 과거 판단과 최신 기준이 충돌할 수 있으므로, 이후 작업자는 반드시 이 섹션을 먼저 읽고 현재 canonical 기준을 확인한다.

### 현재 canonical 기준

현재 기준은 `PUBLIC` 폴더 내부의 06x → 06y → 06 흐름이다.

- 현재 dataset 기준: `PUBLIC/results/_06x_dataset_generation_260515/06x_expanded_dataset.csv`
- 현재 전체 rows: 23,097
- 현재 promo split:
  - promo0: 11,193 rows
  - promo1: 11,904 rows
- 현재 promo split 산출물:
  - `PUBLIC/results/_06y_promo_split_260520/06y_expanded_dataset_promo_0.csv`
  - `PUBLIC/results/_06y_promo_split_260520/06y_expanded_dataset_promo_1.csv`
- 현재 retention 관련 최신 변경:
  - 기존 `retention_w2_ratio`, `retention_w3_ratio`는 유지
  - 신규 `log_retention_w2_ratio`, `log_retention_w3_ratio` 추가
  - log 변환은 `np.log(retention_w2_ratio)`, `np.log(retention_w3_ratio)` 방식
- 현재 06 log retention 검수 결과:
  - 0 이하 retention 값 0건
  - log 계산값과 `np.log()` 직접 계산값 일치
  - 최대 오차 8.88e-16
  - 검수 결과 PASS

### 과거 기준과 최신 기준의 충돌 주의

과거 초기 PUBLIC 분리 기록에는 다음 값이 남아 있다.

- 초기 기준 전체 rows: 23,079
- 초기 `FINAL_promo_0.csv`: 11,175 rows
- 초기 `FINAL_promo_1.csv`: 11,904 rows

이 값은 당시 기록으로 보존한다.  
하지만 이후 작업의 기준은 최신 06x/06y 재실행 기준인 23,097 rows, promo0 11,193 rows, promo1 11,904 rows다.

따라서 이후 모델링, OOF score, SHAP, segmentation, dashboard, 발표 자료는 최신 06x/06y/06 기준을 우선한다.

### 현재 모델 후보 판단

`PUBLIC_results_only.zip` 검수 기준 assistant의 1차 추천은 다음과 같다.

- promo1 primary score source 후보: `10_gradientboosting_promo1`
- promo0 primary score source 후보: `09_gradientboosting_promo0`
- promo1 baseline/sensitivity 후보: `08_lr_promo1`
- promo0 baseline/sensitivity 후보: `07_lr_promo0`
- backup 후보:
  - `01_catboost_promo0_conservative`
  - `02_catboost_promo1_conservative`
- reference 보존:
  - 기존 CatBoost
  - SVM
  - RandomForest

단, 이는 assistant의 1차 추천 판단이며 사용자 최종 승인 전까지 확정 모델이 아니다.

### superseded 된 과거 판단

이 문서에는 과거에 CatBoost를 `strong_candidate` 또는 `conditional_recommended_after_user_approval`로 둔 기록이 남아 있다.  
해당 기록은 당시 audit 기준으로는 유효한 연대기적 기록이지만, 이후 trial-level overfit audit과 보수형 GradientBoosting 재실험으로 최신 판단에서는 superseded 되었다.

현재 기준에서는 기존 CatBoost를 중심 score source로 바로 쓰지 않는다. 기존 CatBoost는 성능 reference로 보존한다.

### 현재 작업 차단 조건: feature set 결정 전 OOF 금지

06에서 log retention 컬럼이 추가되었으므로, 다음 작업자가 바로 row-level OOF score table을 만들면 안 된다.

OOF score table 생성 전 반드시 결정해야 할 사항:

- 기존 `retention_w2_ratio`, `retention_w3_ratio`를 그대로 사용할지
- 신규 `log_retention_w2_ratio`, `log_retention_w3_ratio`를 사용할지
- 기존 retention과 log retention을 동시에 사용할지
- 동시에 사용할 경우 다중공선성/중복 정보 문제를 어떻게 기록할지
- 모델 입력 CSV를 `06y` 기준으로 할지, `06` log retention 기준으로 할지
- promo0/promo1 모델 입력 CSV 최종 경로를 무엇으로 할지

이 결정이 note.md에 기록되기 전에는 모델링, OOF score table, SHAP, segmentation으로 넘어가지 않는다.

### 현재 다음 단계

현재 다음 단계는 `row-level OOF score table 생성`이 아니다.  
정확한 다음 단계는 다음 순서다.

1. feature set 결정
2. 모델 입력 CSV 확정
3. promo0/promo1 입력 파일 재고정
4. 모델 후보 재확인
5. row-level OOF score table 생성
6. GB/LR high-risk overlap 검수
7. SHAP 또는 feature importance
8. promo1 중심 segmentation rule 설계
9. segment assignment 생성
10. segment visual guide v2 및 발표 스토리 재작성

---
## 2026-05-19 | PUBLIC 폴더 초기화 및 데이터셋 분리

### 수행 내용

`park.ingyeom/reports/audits/06x_dataset_generation_260515/06x_expanded_dataset.csv` (23,079행 × 82컬럼) 기준으로 데이터셋 분리 수행.

- 제거 컬럼 (5개): `payment_is_mobile`, `payment_is_pc`, `payment_is_android`, `payment_is_ios`, `is_promotion`
- 분리 기준: `is_promotion` 값으로 이진 분리
- 최종 피처 수: 77컬럼 (USER_KEY, is_repurchase 포함)

### 생성 산출물

| 파일 | 경로 | 행 수 | 컬럼 수 |
|---|---|---|---|
| FINAL_promo_0.csv | `PUBLIC/FINAL_promo_0.csv` | 11,175 | 77 |
| FINAL_promo_1.csv | `PUBLIC/FINAL_promo_1.csv` | 11,904 | 77 |

### 결정 사항

- conservative_safe_22 (22피처)는 expanded 대비 전 구간 OOF AUC -0.05~0.06 열위 → 이번 실행에서 제외
- 사용 feature set: expanded 기준 77컬럼 (payment 4개 + is_promotion 제거)

### 다음 단계

- 모델 비교 노트북 작성 예정
- 대상 모델: CatBoost, SVM, RandomForest, LogisticRegression (4종)
- 대상 데이터셋: FINAL_promo_0, FINAL_promo_1 (2종)
- 총 실행: 4모델 × 2데이터셋 = 8회
- CV 정책: StratifiedGroupKFold 5-fold, group=USER_KEY (기존 12x와 동일)

---

## 2026-05-20 | PUBLIC promo split 이후 파이프라인 재정렬 지침

# PUBLIC promo split 이후 파이프라인 재정렬 지침

작성일: 2026-05-20  
작성 목적: `PUBLIC` 폴더에서 `promo0`, `promo1`을 분리해 8개 모델 노트북을 실행한 이후, 기존 파이프라인의 어느 구간을 다시 짚어야 하는지 명확히 기록한다. 이 문서는 향후 Codex, Claude Code, 또는 다른 LLM이 읽고 작업할 때 프로젝트의 핵심 질문을 잃지 않도록 하기 위한 최상위 작업 지침이다.

---

# 1. 현재 상황

현재 `PUBLIC` 폴더에는 `FINAL_promo_0.csv`, `FINAL_promo_1.csv`, 그리고 8개의 모델 실행 노트북이 존재한다.

이 8개 노트북은 다음 조합으로 구성된다.

- `CatBoost` × `promo0`
- `CatBoost` × `promo1`
- `SVM` × `promo0`
- `SVM` × `promo1`
- `RandomForest` × `promo0`
- `RandomForest` × `promo1`
- `LogisticRegression` × `promo0`
- `LogisticRegression` × `promo1`

여기서 `promo0`은 일반 고객, 즉 100원딜 프로모션이 아닌 집단을 의미한다. `promo1`은 100원딜 프로모션 유입 집단을 의미한다.

현재 `PUBLIC` 구조의 핵심은 전체 고객을 하나의 판에 섞어 모델링하지 않고, `is_promotion` 기준으로 일반 고객과 100원딜 고객을 아예 분리해 각각 별도 모델을 돌리는 것이다.

이 분리는 단순한 데이터 파일 분할이 아니다. 이 프로젝트의 주어를 다시 되찾기 위한 구조적 조치다.

이 프로젝트의 본질은 단순한 OTT 이탈 분석이 아니다. 프로젝트의 본질은 `100원딜로 유입된 고객의 이탈/재구매 패턴을 일반 고객과 비교해 이해하는 것`이다. 따라서 100원딜 고객과 일반 고객을 같은 모델 하나에 넣고, `is_promotion`을 feature 하나로만 처리하는 방식은 최종 비즈니스 설명의 중심이 되기 어렵다.

---

# 2. 문제의 핵심

기존 세그먼트 설계에서 가장 심각한 문제는 `100원딜 프로모션`이 세그먼트의 최상위 축으로 충분히 반영되지 않았다는 점이다.

이 문제는 단순히 "세그먼트 설명에 100원딜이라는 단어가 부족했다" 수준의 문제가 아니다. 이 프로젝트의 질문 자체가 `100원딜 OTT 이탈 분석`인데, 최종 세그먼트가 100원딜 유입 맥락을 중심에 두지 않았다면, 이는 프로젝트 정체성을 흔드는 핵심 결함이다.

기존 세그먼트가 `repurchase_score`, `churn_risk`, `week2_drop`, `week3_inactive`, `cold_start`, `low_activity`, `only_w1` 같은 행동 패턴 중심으로 만들어진 것은 그 자체로는 논리적으로 사용할 수 있다. 문제는 그 행동 패턴이 `100원딜 유입자`라는 비즈니스 주어 아래에서 해석되지 않았다는 점이다.

예를 들어 같은 `week2_drop`이라도 100원딜 고객의 `week2_drop`과 일반 고객의 `week2_drop`은 비즈니스 해석이 다르다.

100원딜 고객의 `week2_drop`은 "싼 가격으로 유입되었으나 실제 이용 습관으로 전환되지 못하고 관심이 빠르게 식은 신호"일 수 있다. 반면 일반 고객의 `week2_drop`은 "정상 가격으로 가입했지만 콘텐츠 탐색 또는 이용 만족도가 충분하지 않았던 신호"일 수 있다.

같은 `cold_start`도 마찬가지다. 100원딜 유입자의 cold start는 "저가 프로모션에 반응해 가입은 했지만 실제 콘텐츠 소비 동기가 약했다"는 해석으로 이어질 수 있다. 일반 고객의 cold start는 "가입 의도는 있었으나 초기 탐색 동선이나 콘텐츠 매칭에 실패했다"는 해석으로 갈 수 있다.

따라서 행동 flag 자체보다 중요한 것은 그 행동 flag가 어떤 집단 내부에서 발생했는지를 구분하는 것이다.

기존 세그먼트가 이 구분을 최상위 구조로 갖지 못했다면, 그것은 고객 행동을 나누긴 했지만 프로젝트의 핵심 질문에는 충분히 답하지 못한 것이다.

---

# 3. PUBLIC promo split의 의미

현재 `PUBLIC`에서 `FINAL_promo_0.csv`, `FINAL_promo_1.csv`를 나눈 이유는 명확하다.

이는 전체 고객을 섞어놓고 "누가 이탈하느냐"를 보는 것이 아니라, 다음 질문으로 되돌아가기 위한 것이다.

`100원딜 고객 안에서 누가 위험한가?`

그리고 그 다음 질문은 다음이다.

`그 위험 신호는 일반 고객과 어떻게 다른가?`

따라서 `PUBLIC`의 promo split은 단순한 편의상 파일 분리가 아니라, 프로젝트의 질문을 재정렬하는 핵심 조치다.

기존 방식이 다음 구조였다면,

`전체 고객 → 위험 점수 → 행동 플래그 → 세그먼트`

이제는 다음 구조로 바뀌어야 한다.

`100원딜 여부 → 각 집단 내부 모델/위험 점수 → 행동 플래그 → 집단별 세그먼트`

이 차이가 핵심이다.

이제 분석의 최상위 질문은 "OTT 고객 중 누가 이탈하나"가 아니라 "100원딜로 들어온 고객 중 누가 이탈하나, 그리고 그 패턴은 일반 고객과 무엇이 다른가"가 되어야 한다.

---

# 4. 내일 8개 노트북 결과가 나온 직후 해야 할 일

내일 8개 노트북 실행 결과가 나오면, 바로 세그먼트를 다시 만들면 안 된다.

가장 먼저 해야 할 일은 8개 모델 결과를 하나의 비교표로 합치는 것이다.

이때 전체 8개 중에서 단순히 1등 모델 하나를 고르면 안 된다. 반드시 `promo1 내부 주 모델 후보`와 `promo0 내부 비교 모델 후보`를 따로 판단해야 한다.

왜냐하면 지금 목적은 전체 고객을 대상으로 하나의 최고 모델을 고르는 것이 아니라, 100원딜 고객 내부에서 잘 작동하는 모델과 일반 고객 내부에서 잘 작동하는 모델을 구분하는 것이기 때문이다.

비교표에는 최소한 다음 정보가 포함되어야 한다.

- promo 구분: `promo0` 또는 `promo1`
- model 구분: CatBoost, SVM, RandomForest, LogisticRegression
- best validation ROC-AUC
- test ROC-AUC
- test PR-AUC
- test F1
- test precision
- test recall
- validation-test gap
- 과적합 의심 여부
- trial 결과의 안정성
- 모델별 best parameter

단순히 ROC-AUC만 보면 안 된다.

이탈 방어 또는 재구매 유도 관점에서는 PR-AUC, Recall, Precision을 반드시 함께 봐야 한다.

Recall은 위험 고객을 얼마나 놓치지 않는지를 보는 지표다. Precision은 개입 대상으로 찍은 고객 중 실제 위험 고객이 얼마나 되는지를 보는 지표다. PR-AUC는 불균형 분류 상황에서 양성 클래스 예측 품질을 보는 데 중요하다.

특히 비즈니스 개입에서는 "위험 고객을 많이 잡을 것인가"와 "정말 위험한 고객만 선별할 것인가" 사이에 trade-off가 존재한다. 따라서 모델 선택은 단순 성능 1등이 아니라 intervention 목적에 맞는 score source 선택이어야 한다.

---

# 5. 현재 8개 노트북 결과만으로는 세그먼트를 바로 만들 수 없다

현재 `PUBLIC/notebooks`의 8개 모델 노트북은 모델 성능 비교에는 유용하지만, 세그먼트 생성을 위한 산출물을 충분히 남기지 않을 가능성이 높다.

현재 구조상 각 노트북은 주로 다음 파일을 남긴다.

- `final_result.csv`
- `trials_all.csv`

이 두 파일은 모델별 성능 비교와 Optuna trial 확인에는 유용하다. 하지만 세그먼트를 만들기 위해서는 row-level prediction score가 필요하다.

기존 17x 세그먼트는 `repurchase_score`, `churn_risk = 1 - repurchase_score`, `risk_percentile`, `high_risk_top20` 같은 score 기반 구조를 사용했다.

따라서 PUBLIC 결과만 보고 바로 세그먼트를 만들면 안 된다. 세그먼트 생성을 위해서는 반드시 각 row에 대한 예측 score가 필요하다.

필요한 후속 산출물은 다음과 같다.

- `PUBLIC_model_comparison.csv`
- `PUBLIC_scored_promo1.csv`
- `PUBLIC_scored_promo0.csv`
- `PUBLIC_oof_scores_promo1.csv`
- `PUBLIC_oof_scores_promo0.csv`
- `PUBLIC_score_distribution_promo1.csv`
- `PUBLIC_score_distribution_promo0.csv`

특히 가능하면 단순 train/test prediction이 아니라 OOF 방식의 prediction score를 만들어야 한다.

OOF score가 필요한 이유는 전체 row에 대해 비교적 공정한 out-of-fold 예측값을 부여하기 위해서다. 이미 학습에 사용된 row에 대해 그대로 예측한 in-sample score를 세그먼트에 쓰면 score가 과도하게 낙관적일 수 있다. 따라서 segmentation의 score source로 쓰려면 OOF score 또는 최소한 test/holdout 기준의 분리된 예측 구조가 필요하다.

각 row-level score table에는 최소한 다음 컬럼이 필요하다.

- row identifier
- USER_KEY
- is_repurchase
- repurchase_score
- churn_risk_score
- risk_rank
- risk_percentile
- high_risk_top20
- model_name
- promo_scope
- score_source
- fold 정보, OOF 생성 시
- train/test 구분, holdout score 사용 시

이 score table 없이는 세그먼트를 다시 만들면 안 된다.

---

# 6. 기존 파이프라인에서 다시 짚어야 할 범위

기존 파이프라인 전체를 01부터 다시 시작할 필요는 없어 보인다.

현재 문제의 직접 원인은 원천 데이터 생성 단계가 아니라, 모델링 이후 해석과 세그먼트 단계에서 100원딜 축이 중심이 되지 못한 것이다.

따라서 다시 짚어야 할 범위는 다음과 같이 정리한다.

`01~04`는 유지한다. 이 구간은 원천 데이터 이해, 전처리, 메타데이터 정리, 기본 feature engineering에 해당한다. 현재 문제의 직접 원인은 이 구간이 아니다.

`05x/05y/06x/07x`도 기본적으로 유지한다. 이 구간은 feature approval, feature dictionary, expanded dataset 생성, AARRR mapping을 다시 정리한 흐름이다. 현재 `PUBLIC`이 `06x_expanded_dataset.csv`를 기준으로 만들어졌다면, 기준 데이터 역할은 유지된다.

다만 `08~10x` EDA가 promotion split을 충분히 반영했는지는 보조적으로 다시 확인할 수 있다. 하지만 당장 핵심 복구 대상은 아니다.

핵심적으로 다시 짚어야 할 구간은 다음이다.

- `11x/12x/14x`: 모델링 비교 단계
- `16x`: SHAP 해석 단계
- `17x`: segmentation 단계
- 발표용 HTML, dashboard, project guide, segment visual guide
- 비즈니스 제언 narrative

실행 순서는 다음이어야 한다.

`모델 결과 수집 → 모델 비교표 생성 → promo별 score table 생성 → promo별 SHAP → promo별 segment 재설계 → HTML/대시보드/발표 스토리 재작성`

이 순서를 지켜야 한다.

세그먼트를 먼저 이름 붙이고, 나중에 score나 SHAP을 끼워 맞추면 안 된다.

---

# 7. 모델링 비교 단계에서 다시 봐야 할 것

기존 모델링 결과가 `overall_with_promotion` 중심이었거나, `is_promotion`을 feature로 넣은 전체 모델 중심이었다면, 그 결과는 이제 최종 주인공이 되기 어렵다.

이제 모델링 기준은 다음처럼 바뀌어야 한다.

- 전체 모델 1개가 아니라 `promo1 모델`과 `promo0 모델`을 별도로 비교한다.
- `promo1 모델`을 100원딜 분석의 주 모델 후보로 둔다.
- `promo0 모델`은 일반 고객 비교군 모델로 둔다.
- 전체 모델은 참고용 또는 배경 설명용으로만 둔다.
- 최종 발표의 중심은 `promo1`, 즉 100원딜 고객 내부 분석이어야 한다.

내일 결과가 나오면 다음 질문에 답해야 한다.

`promo1에서는 어떤 모델이 가장 안정적인가?`

`promo0에서는 어떤 모델이 가장 안정적인가?`

`두 집단에서 같은 모델이 잘 작동하는가, 아니면 집단별로 다른 모델이 필요한가?`

`100원딜 집단은 일반 고객보다 예측이 쉬운가, 어려운가?`

`성능 차이가 실제로 의미 있게 보이는가?`

`ROC-AUC와 PR-AUC가 같이 개선되는가?`

`Recall과 Precision의 균형은 intervention 목적에 맞는가?`

`과적합 gap은 어느 정도인가?`

`Optuna trial 결과가 특정 trial 하나에만 의존하는가, 아니면 전반적으로 안정적인가?`

이 질문에 답하기 전에는 어떤 모델을 최종 score source로 사용할지 확정하면 안 된다.

---

# 8. score source 결정 원칙

세그먼트의 score source는 매우 중요하다.

기존 17x segmentation에서 `overall_with_promotion` LightGBM score가 사용되었다면, 그 score source는 이제 중심에서 내려와야 한다. `overall_with_promotion`은 전체 고객을 대상으로 `is_promotion`을 feature로 사용한 모델이므로, 100원딜 내부의 위험 점수를 설명하는 데 한계가 있다.

새로운 중심 score source는 다음 구조여야 한다.

- `promo1_score_source`: 100원딜 고객 내부 모델
- `promo0_score_source`: 일반 고객 내부 모델

최종 발표에서 주인공은 `promo1_score_source`다.

`promo0_score_source`는 비교군이다.

즉, 최종 질문은 다음이어야 한다.

`100원딜 고객 내부에서 위험 점수가 높은 사람은 누구인가?`

그리고 그 다음 질문이 다음이다.

`일반 고객 내부의 위험 패턴과 무엇이 다른가?`

전체 모델에서 `is_promotion`의 중요도를 보는 것은 참고 자료로 남길 수 있다. 하지만 그것만으로는 "100원딜 고객 내부에서 누가 위험한가"라는 질문에 충분히 답하지 못한다.

---

# 9. SHAP 단계는 promo별로 다시 해야 한다

기존 SHAP이 전체 모델 기준이었다면, 100원딜 해석에는 부족하다.

100원딜 프로젝트에서 중요한 것은 "전체 고객에서 어떤 변수가 중요했나"가 아니다.

중요한 질문은 다음이다.

`100원딜 고객 안에서 재구매를 가르는 변수는 무엇인가?`

`일반 고객 안에서 재구매를 가르는 변수는 무엇인가?`

`두 집단에서 같은 변수가 같은 방향으로 작동하는가?`

`100원딜 집단에서만 두드러지는 위험 신호가 있는가?`

`일반 고객에서는 중요하지만 100원딜에서는 약한 변수가 있는가?`

따라서 기존 `16x SHAP`은 다시 짚어야 한다.

새 SHAP 구조는 최소한 다음을 포함해야 한다.

- `promo1_SHAP`: 100원딜 고객 내부 모델의 SHAP
- `promo0_SHAP`: 일반 고객 내부 모델의 SHAP
- `promo1_vs_promo0_feature_importance_diff`: 두 집단의 중요 변수 차이
- `family_level_SHAP`: feature family 단위 요약
- onboarding feature family 해석
- weekly usage feature family 해석
- retention decay feature family 해석
- content preference feature family 해석
- membership context feature family 해석

SHAP 결과는 개별 변수 Top N 나열로 끝내면 안 된다.

발표에서는 개별 변수 하나하나보다 feature family 단위로 묶어서 설명해야 한다. 예를 들어 "w2 관련 변수 하나가 중요하다"가 아니라, "100원딜 고객에서는 2주차 이후 이용량 감소와 retention decay 계열 신호가 위험 판단에 강하게 작동했다"처럼 설명해야 한다.

단, SHAP은 원인이 아니다.

SHAP은 모델 설명이다.

따라서 문장은 반드시 다음 방식으로 작성해야 한다.

잘못된 표현:

`이 변수가 이탈을 유발했다.`

허용되는 표현:

`모델은 이 변수를 재구매 실패 위험 판단에 강하게 사용했다.`

`이 변수는 100원딜 고객 내부에서 위험 점수 상승과 함께 관찰되는 주요 신호로 해석된다.`

`인과가 아니라 예측 모델의 설명 결과로 보아야 한다.`

---

# 10. 세그먼트 단계는 사실상 다시 짚어야 한다

가장 크게 다시 짚어야 할 곳은 `17x segmentation`이다.

기존 세그먼트가 `overall_with_promotion` score를 source로 삼았거나, 전체 고객 기반 위험 점수 위에서 행동 flag를 붙인 구조였다면, 이제 그 구조는 중심에서 내려와야 한다.

새 세그먼트 구조는 다음이어야 한다.

- 최상위 scope는 `promo1`과 `promo0`이다.
- 발표의 주인공은 `promo1`, 즉 100원딜 고객 세그먼트다.
- `promo0`는 비교군이다.
- 각 scope 안에서 risk score와 행동 flag를 결합한다.
- 세그먼트 이름은 마지막에 붙인다.
- 먼저 기준식과 분포를 확인한다.
- LLM이 세그먼트 이름을 먼저 만들면 안 된다.
- final segment는 사용자 승인 전까지 provisional로 표시한다.

기존처럼 "전체 고객 고위험군", "3주차 비활성", "콜드스타트 취약" 같은 이름만 앞세우면 안 된다.

이제 세그먼트의 주어는 명확해야 한다.

예시적 방향은 다음과 같다. 단, 아래 이름들은 실제 score 분포와 flag 분포를 본 뒤 확정해야 하며, 지금 단계에서 확정 이름으로 사용하면 안 된다.

- 100원딜 유입자 중 초반 탐색 실패형
- 100원딜 유입자 중 2주차 관심 급락형
- 100원딜 유입자 중 3주차 이탈 임박형
- 100원딜 유입자 중 저활동 고위험형
- 100원딜 유입자 중 안정 전환형

이 이름들은 방향성을 보여주기 위한 예시일 뿐이다.

실제 세그먼트 이름은 반드시 다음 절차 이후에 붙인다.

`score table 생성 → risk percentile 확인 → 행동 flag 분포 확인 → promo1 내부 대표 패턴 확인 → promo0와 비교 → 사용자 승인 → 이름 확정`

---

# 11. 기존 segment_visual_guide.html의 역할 변경

기존 `legacy/segment_visual_guide.html`은 완전히 버릴 필요는 없다.

하지만 최종 발표용으로 그대로 사용하면 위험하다.

역할을 바꿔야 한다.

기존 HTML은 "이전 세그먼트 설계의 설명서" 또는 "legacy reference"로 보존한다.

새 HTML은 "100원딜 중심 세그먼트 재설계 설명서"로 다시 만들어야 한다.

기존 행동 flag 설명은 재료로 재사용할 수 있다. 예를 들어 `week2_drop`, `week3_inactive`, `cold_start`, `low_activity`, `only_w1` 등의 flag는 여전히 의미 있는 행동 패턴 축이다.

그러나 최상위 narrative는 반드시 바뀌어야 한다.

기존 narrative가 다음에 가까웠다면,

`전체 고객을 대상으로 위험 점수를 만들고, 그 점수와 행동 flag로 세그먼트를 나눴다.`

새 narrative는 다음이어야 한다.

`100원딜 고객과 일반 고객을 분리해 각 집단 내부에서 위험 점수를 만들고, 100원딜 고객 내부에서 어떤 행동 패턴이 재구매 실패 위험과 연결되는지 세그먼트로 정리했다. 일반 고객은 비교군으로 사용했다.`

기존 HTML에서 `overall_with_promotion`이 score source였다는 구조는 새 관점에서는 중심이 되면 안 된다.

새 중심 score source는 `promo1 모델`이어야 한다.

`promo0 모델`은 비교군이어야 한다.

---

# 12. HTML, 대시보드, 발표 스토리까지 다시 연결해야 한다

이번 문제는 단순히 모델링 코드만 바꾸면 끝나는 문제가 아니다.

최종 발표에서 청중이 가장 크게 물을 수 있는 질문은 다음이다.

`그래서 100원딜 고객은 뭐가 다른가요?`

`이 세그먼트가 100원딜 프로모션 전략과 어떻게 연결되나요?`

`일반 고객에게도 똑같이 적용되는 말 아닌가요?`

`그럼 이건 100원딜 분석이 아니라 그냥 OTT 이탈 분석 아닌가요?`

이 질문에 답할 수 있어야 한다.

따라서 발표 스토리는 반드시 다음 흐름으로 바뀌어야 한다.

1. 100원딜은 가격 장벽을 낮춰 유입을 만든다.
2. 그러나 유입 자체가 장기 이용 습관으로 전환되는 것은 아니다.
3. 그래서 100원딜 유입자 내부에서 누가 재구매에 실패할 가능성이 높은지 별도로 보았다.
4. 일반 고객도 별도 모델로 분석해 비교군으로 삼았다.
5. 100원딜 고객 내부에서 특정 행동 신호가 위험 점수와 연결되는지 확인했다.
6. 그 결과를 기반으로 100원딜 고객 대상 세그먼트를 만들었다.
7. 각 세그먼트는 intervention 대상과 메시지 전략으로 연결된다.

즉, 프로젝트의 최종 주어는 반드시 `100원딜 유입자`여야 한다.

---

# 13. 절대 하지 말아야 할 것

이번 재정렬 과정에서 절대 하지 말아야 할 것이 있다.

첫째, 8개 모델 중 성능이 가장 높은 모델 하나만 보고 바로 최종 모델로 확정하면 안 된다.

전체 8개 중 1등을 고르는 것이 목적이 아니다. `promo1` 내부 주 모델과 `promo0` 내부 비교 모델을 따로 봐야 한다.

둘째, `final_result.csv`만 보고 세그먼트를 만들면 안 된다.

세그먼트를 만들려면 row-level score가 필요하다. `repurchase_score`, `churn_risk_score`, `risk_percentile`, `high_risk_top20` 같은 컬럼이 붙은 score table이 필요하다.

셋째, SHAP 없이 세그먼트 이름을 먼저 붙이면 안 된다.

세그먼트 이름은 데이터 분포와 score, 행동 flag, SHAP 해석을 본 뒤 마지막에 붙여야 한다.

넷째, LLM이 그럴듯한 비즈니스 이름을 먼저 만들면 안 된다.

이 프로젝트에서는 이름이 데이터를 끌고 가면 안 된다. 데이터와 기준식이 먼저고, 이름은 마지막이다.

다섯째, 기존 `segment_visual_guide.html`을 문장 몇 줄만 고쳐 최종본처럼 쓰면 안 된다.

기존 HTML은 legacy로 보존하고, 새 HTML은 100원딜 중심 구조로 새로 써야 한다.

여섯째, `is_promotion`을 단순 feature 하나로 취급하면 안 된다.

현재 관점에서 `is_promotion`은 단순 feature가 아니라 분석 scope를 나누는 최상위 비즈니스 축이다.

일곱째, 전체 모델 결과를 100원딜 내부 해석으로 과잉 일반화하면 안 된다.

전체 모델에서 중요했던 변수가 100원딜 내부에서도 중요하다는 보장은 없다. 반드시 `promo1` 모델 내부에서 다시 확인해야 한다.

여덟째, SHAP을 인과처럼 말하면 안 된다.

SHAP은 모델 설명이지 원인 증명이 아니다.

아홉째, final_checks PASS를 의미 검수 PASS로 착각하면 안 된다.

파일이 생성되고 노트북이 실행되었다는 것은 형식 검수일 뿐이다. 실제로 프로젝트 질문에 맞게 설계되었는지는 별도 의미 검수가 필요하다.

열째, LLM이 피처를 임의로 제외하거나 승격하면 안 된다.

LLM은 각 피처의 근거, 위험, caveat, 사용 가능성을 정리할 수 있지만, 최종 사용 여부는 사용자 승인 사항이다.

---

# 14. 내일 결과를 받을 때 필요한 파일

내일 8개 노트북 실행 결과가 나오면, 가능하면 `PUBLIC/results` 폴더 전체를 ZIP으로 묶어 검수해야 한다.

최소 필요 파일은 다음이다.

```text
PUBLIC/
  results/
    01_catboost_promo0/
      final_result.csv
      trials_all.csv
    02_catboost_promo1/
      final_result.csv
      trials_all.csv
    03_svm_promo0/
      final_result.csv
      trials_all.csv
    04_svm_promo1/
      final_result.csv
      trials_all.csv
    05_rf_promo0/
      final_result.csv
      trials_all.csv
    06_rf_promo1/
      final_result.csv
      trials_all.csv
    07_lr_promo0/
      final_result.csv
      trials_all.csv
    08_lr_promo1/
      final_result.csv
      trials_all.csv
```

검수 시에는 다음을 확인해야 한다.

- 8개 노트북이 모두 실행 완료되었는가
- 각 결과 폴더에 `final_result.csv`가 존재하는가
- 각 결과 폴더에 `trials_all.csv`가 존재하는가
- model/promo 조합이 누락되지 않았는가
- promo0/promo1의 row 수가 입력 데이터 기준과 맞는가
- target 분포가 각 split에서 보존되었는가
- Stratified split이 실제로 적용되었는가
- Optuna trial이 정상적으로 200회 완료되었는가
- 중간에 실패한 trial이 있는가
- best trial이 극단적 우연에 의존하는가
- validation 성능과 test 성능의 gap이 큰가
- ROC-AUC, PR-AUC, F1, Precision, Recall이 모두 기록되었는가
- 성능 비교표 생성이 가능한 형태인가

이 단계는 형식 검수와 의미 검수를 분리해야 한다.

형식 검수는 파일 존재, 실행 완료, row 수, 컬럼 존재, 결과 저장 여부를 본다.

의미 검수는 모델 선택이 프로젝트 질문에 맞는지, 100원딜 집단 내부 score source로 쓸 수 있는지, 과적합 위험이 있는지, 세그먼트로 이어질 수 있는지 판단한다.

---

# 15. 내일 결과 이후 만들어야 할 핵심 산출물

8개 노트북 실행 이후 최종적으로 만들어야 할 핵심 산출물은 다음이다.

`PUBLIC_model_comparison.csv`

promo0/promo1 × 4모델 결과를 하나로 합친 비교표다. 이 파일은 모델별 성능, 과적합 gap, trial 안정성, 최종 score source 후보를 비교하기 위한 기준표다.

`PUBLIC_model_selection_memo.md`

왜 특정 모델을 promo1 score source로 선택했는지, 왜 특정 모델을 promo0 비교군으로 선택했는지 기록하는 문서다. 단순히 성능 1등이라서 선택했다는 식이면 안 된다. PR-AUC, Recall, Precision, overfit gap, 해석 가능성, SHAP 가능성, 세그먼트 연결 가능성을 함께 기록해야 한다.

`PUBLIC_scored_promo1.csv`

100원딜 고객 각 row에 대해 repurchase_score, churn_risk_score, risk percentile, high-risk flag가 붙은 파일이다. 최종 세그먼트의 중심 입력이다.

`PUBLIC_scored_promo0.csv`

일반 고객 각 row에 대해 동일한 score를 붙인 비교군 파일이다.

`PUBLIC_SHAP_promo1/`

100원딜 고객 내부 모델의 SHAP 결과 폴더다.

`PUBLIC_SHAP_promo0/`

일반 고객 내부 모델의 SHAP 결과 폴더다.

`PUBLIC_segment_promo1.csv`

100원딜 고객에 대한 provisional segment assignment 파일이다.

`PUBLIC_segment_promo0.csv`

일반 고객에 대한 비교군 segment assignment 파일이다.

`PUBLIC_segment_definition_promo1.md`

100원딜 고객 세그먼트 기준식과 해석을 적은 문서다. 사용자 승인 전까지 모든 segment name은 provisional로 표시해야 한다.

`PUBLIC_segment_visual_guide_v2.html`

기존 `legacy/segment_visual_guide.html`을 대체하는 새 HTML이다. 이 HTML은 전체 고객 세그먼트가 아니라 100원딜 고객 중심 세그먼트를 설명해야 한다.

---

# 16. 비즈니스 해석의 중심 문장

향후 발표와 HTML에서 가장 중심이 되어야 할 문장은 다음이다.

`100원딜은 가입 장벽을 낮추는 데 성공했지만, 모든 유입자가 실제 이용 습관으로 전환되는 것은 아니다. 따라서 우리는 100원딜 고객을 일반 고객과 분리해 분석하고, 100원딜 고객 내부에서 재구매 실패 위험이 높은 행동 패턴을 별도로 식별했다.`

이 문장이 전체 프로젝트의 중심축이어야 한다.

다른 방식으로 표현하면 다음이다.

`이 프로젝트는 단순히 OTT 이탈 고객을 찾는 프로젝트가 아니다. 100원딜이라는 가격 프로모션으로 유입된 고객이 어떤 조건에서 장기 이용자로 전환되지 못하는지를 찾는 프로젝트다.`

따라서 segmentation도 다음 질문에 답해야 한다.

`100원딜 고객 중 누구에게 먼저 개입해야 하는가?`

`그 고객은 어떤 행동 신호를 보이는가?`

`일반 고객과 비교했을 때 무엇이 다른가?`

`어떤 메시지, 혜택, 콘텐츠 추천, 온보딩 개입이 적절한가?`

---

# 17. 기존 행동 flag는 폐기하지 않는다

기존 segment logic을 전부 버릴 필요는 없다.

기존 행동 flag는 여전히 중요한 재료다.

예를 들어 다음 flag들은 여전히 사용할 수 있다.

- week2_drop
- week3_inactive
- week3_drop
- only_w1
- low_activity
- cold_start
- retention decay
- content preference concentration
- genre focused behavior
- stable user flag

다만 이 flag들은 더 이상 전체 고객 기준 세그먼트의 이름을 만드는 데 먼저 쓰이면 안 된다.

이제 이 flag들은 `promo1`과 `promo0` 내부에서 각각 해석되어야 한다.

즉, 기존 flag는 행동 패턴 축으로 보존한다. 그러나 최상위 분석 축은 `is_promotion` split이다.

기존 구조가 다음이었다면,

`행동 flag → 전체 고객 segment`

새 구조는 다음이어야 한다.

`promo scope → score source → 행동 flag → segment`

이 순서를 지켜야 한다.

---

# 18. 100원딜 세그먼트 설계의 기본 방향

100원딜 세그먼트는 단순히 위험 점수만으로 나누면 안 된다.

위험 점수와 행동 패턴을 결합해야 한다.

예를 들어 고위험 고객 중에서도 이유가 다를 수 있다.

초반부터 거의 보지 않은 사람은 `onboarding failure`에 가깝다.

1주차에는 봤지만 2주차에 급락한 사람은 `interest decay`에 가깝다.

2주차까지는 봤지만 3주차에 사라진 사람은 `late-stage churn risk`에 가깝다.

시청량은 있으나 특정 장르나 콘텐츠에만 몰린 사람은 `narrow preference` 또는 `content matching risk`일 수 있다.

꾸준히 본 사람은 `stable conversion candidate`일 수 있다.

그러나 이 이름들은 지금 확정하면 안 된다.

각 그룹의 실제 row 수, target rate, score 분포, 주요 feature, SHAP 방향, promo0와의 차이를 확인한 뒤 이름을 붙여야 한다.

---

# 19. 일반 고객 모델의 역할

`promo0` 모델은 최종 발표의 주인공이 아니다.

그러나 매우 중요하다.

`promo0`는 비교군이다.

100원딜 고객의 위험 신호가 정말 100원딜 특유의 패턴인지 보려면 일반 고객과 비교해야 한다.

예를 들어 100원딜 고객에서 `week2_drop`이 강하게 중요하고, 일반 고객에서는 상대적으로 약하다면 이는 100원딜 유입자에서 2주차 관심 유지가 특히 중요하다는 해석으로 이어질 수 있다.

반대로 양쪽 모두에서 `week3_inactive`가 강하게 중요하다면, 이는 프로모션 특이 신호라기보다 OTT 구독 이벤트 전반의 이탈 직전 행동 신호일 가능성이 높다.

따라서 발표에서는 다음 구분이 필요하다.

- 100원딜 특이 신호
- 일반 고객과 공통인 이탈 신호
- 일반 고객에서 더 강한 신호
- 양쪽에서 방향이 다른 신호
- 모델 해석상 불안정한 신호

이 구분이 있어야 `100원딜 분석`이라는 정체성이 살아난다.

---

# 20. 모델 성능이 낮거나 애매할 경우의 대응

만약 내일 결과에서 100원딜 모델 성능이 기대보다 낮게 나오더라도, 그것만으로 실패라고 단정하면 안 된다.

성능이 낮을 경우에도 해석할 수 있는 가능성이 있다.

첫째, 100원딜 고객의 재구매/이탈은 현재 feature만으로는 설명력이 제한적일 수 있다.

둘째, 가격 프로모션 유입자는 행동 패턴이 더 불안정해 예측이 어려울 수 있다.

셋째, 개인의 외부 요인, 콘텐츠 취향, 프로모션 인식, 실제 결제 의향 등이 데이터에 충분히 반영되지 않았을 수 있다.

넷째, 전체 모델보다 집단 내부 모델의 성능이 낮아질 수 있다. 표본 수가 줄었기 때문이다.

따라서 성능이 낮으면 다음처럼 기록해야 한다.

`100원딜 고객 내부 모델의 예측 성능은 제한적이었다. 이는 100원딜 유입자의 재구매 여부가 단순 이용량 변수만으로 완전히 설명되지 않을 수 있음을 시사한다. 다만 SHAP과 행동 flag를 결합하면, 고위험 신호를 보이는 일부 집단에 대한 개입 전략은 도출할 수 있다.`

성능이 낮다고 해서 무리하게 모델을 포장하면 안 된다.

성능이 낮다면 낮다고 기록하고, 세그먼트는 "정밀 예측"이 아니라 "대응 우선순위 triage"로 낮춰서 설명해야 한다.

---

# 21. 모델 성능이 높을 경우의 주의점

반대로 모델 성능이 높게 나와도 조심해야 한다.

성능이 높다는 이유만으로 바로 신뢰하면 안 된다.

반드시 다음을 점검해야 한다.

- target leakage 의심 feature가 남아 있지 않은가
- train/test split이 USER_KEY 단위로 적절한가
- 동일 고객의 여러 구독 이벤트가 train/test에 섞여 있지 않은가
- 시점상 예측 시점 이후 정보를 쓰고 있지 않은가
- `is_repurchase`와 직접적으로 연결된 사후 정보가 feature에 들어가지 않았는가
- Optuna가 test set에 과적합되는 구조는 아닌가
- 최종 score가 in-sample prediction은 아닌가
- promotion split 후 target 분포가 비정상적으로 치우치지 않았는가

성능이 높을수록 의미 검수는 더 엄격해야 한다.

---

# 22. Codex 또는 Claude Code에게 줄 작업 원칙

향후 Codex 또는 Claude Code가 이 작업을 이어받을 경우, 다음 원칙을 반드시 지켜야 한다.

1. `PUBLIC`의 목적을 단순 모델 실행 폴더로 오해하지 말 것.
2. `PUBLIC`은 100원딜 고객과 일반 고객을 분리해 프로젝트의 주어를 되찾기 위한 재정렬 공간이다.
3. 모델 성능 비교만 하고 끝내면 안 된다.
4. 반드시 row-level score table을 생성해야 한다.
5. 반드시 promo별 SHAP을 생성해야 한다.
6. 반드시 promo별 segment를 다시 설계해야 한다.
7. 기존 segment_visual_guide.html을 최종본처럼 재사용하지 말 것.
8. 기존 행동 flag는 재료로 보존하되, 최상위 scope는 `promo1/promo0`로 잡을 것.
9. 세그먼트 이름은 데이터 분포와 기준식 확인 후 마지막에 붙일 것.
10. final segment는 사용자 승인 전까지 provisional로 표기할 것.
11. SHAP은 인과가 아니라 모델 설명으로만 해석할 것.
12. 100원딜 고객 내부 분석을 발표의 주인공으로 둘 것.
13. 일반 고객 분석은 비교군으로 둘 것.
14. 모든 파일 생성 후 note.md에 작업 로그를 남길 것.
15. 결과 ZIP에는 notebook, final_result, trials_all, score table, SHAP summary, segment definition, execution log, inventory를 포함할 것.
16. 확인하지 않은 파일명, 컬럼명, 수치, 실행 성공 여부를 확정 표현으로 쓰지 말 것.
17. "PASS"는 형식 검수인지 의미 검수인지 구분해서 기록할 것.
18. LLM이 피처를 임의로 제거하거나 최종 승격하지 말 것.
19. 사용자 승인 없이 새로운 파생변수를 만들지 말 것.
20. 기존 합의를 바꾸는 제안이면 반드시 "기존 합의를 바꾸는 제안"이라고 먼저 명시할 것.

---

# 23. 작업 순서 제안

내일 결과가 나온 뒤의 권장 작업 순서는 다음이다.

첫째, `PUBLIC/results` 전체를 검수한다.

8개 노트북이 모두 정상 실행되었는지 확인한다. `final_result.csv`, `trials_all.csv`가 모두 존재하는지 확인한다. 결과 폴더 누락이 없는지 확인한다.

둘째, `PUBLIC_model_comparison.csv`를 만든다.

promo0/promo1 × 4모델 결과를 하나의 표로 합친다. ROC-AUC, PR-AUC, F1, Precision, Recall, gap, best params를 함께 비교한다.

셋째, `PUBLIC_model_selection_memo.md`를 작성한다.

promo1 주 모델 후보와 promo0 비교 모델 후보를 선정한다. 선정 이유는 성능, 안정성, 과적합, 해석 가능성, 세그먼트 연결 가능성 기준으로 기록한다.

넷째, score table 생성 노트북을 만든다.

선택된 모델을 기준으로 `PUBLIC_scored_promo1.csv`, `PUBLIC_scored_promo0.csv`를 만든다. 가능하면 OOF score를 생성한다.

다섯째, promo별 SHAP을 만든다.

`promo1_SHAP`, `promo0_SHAP`을 각각 만든다. 개별 변수 Top N뿐 아니라 feature family 단위 요약을 만든다.

여섯째, segment rule을 다시 설계한다.

먼저 risk percentile과 행동 flag 분포를 본다. 세그먼트 기준식을 만든다. 이름은 provisional로 둔다.

일곱째, segment assignment를 생성한다.

`PUBLIC_segment_promo1.csv`, `PUBLIC_segment_promo0.csv`를 만든다. 각 segment별 row 수, target rate, 평균 score, 주요 행동 flag 비율을 계산한다.

여덟째, HTML 해설서를 새로 만든다.

기존 legacy HTML은 보존하고, `PUBLIC_segment_visual_guide_v2.html` 또는 이에 준하는 새 설명서를 만든다. 주어는 반드시 100원딜 고객이어야 한다.

아홉째, 발표 스토리를 다시 쓴다.

전체 발표 narrative가 "100원딜 유입자의 장기 이용 전환 실패/성공 패턴"을 중심으로 흐르도록 수정한다.

---

# 24. 최종 판단

현재 `PUBLIC` 분리는 타당한 방향이다.

다만 이 분리 자체가 최종 결과는 아니다.

`PUBLIC`은 새로운 출발점이다.

이제 해야 할 일은 8개 모델 결과를 바탕으로 100원딜 고객 내부의 score source를 정하고, 그 score를 기반으로 SHAP과 세그먼트를 다시 만드는 것이다.

기존 파이프라인에서 01부터 다시 시작할 필요는 없다. 하지만 모델링 이후의 해석 구간은 반드시 다시 짚어야 한다.

다시 짚어야 할 핵심은 다음이다.

- 모델링 비교
- row-level score 생성
- promo별 SHAP
- promo별 segmentation
- segment visual guide
- dashboard
- 발표 narrative
- 비즈니스 제언

이번 재작업의 목적은 모델 점수를 올리는 것이 아니다.

이번 재작업의 목적은 프로젝트의 주어를 되찾는 것이다.

최종 주어는 `OTT 고객`이 아니라 `100원딜로 유입된 고객`이다.

최종 질문은 "누가 이탈하나"가 아니라 "100원딜로 유입된 고객 중 누가 장기 이용자로 전환되지 못하는가, 그리고 그들에게 어떤 개입이 필요한가"이다.

이 기준을 잃으면 다시 같은 문제가 반복된다.

---

# 25. 향후 모든 LLM에게 남기는 경고

이 프로젝트에서 가장 위험한 것은 그럴듯한 일반 이탈 분석으로 흐르는 것이다.

100원딜이라는 주어가 빠진 segmentation은 아무리 보기 좋고, 아무리 성능이 좋아 보여도 이 프로젝트의 핵심 답변이 아니다.

100원딜은 단순 feature가 아니다.

100원딜은 이 프로젝트의 문제 정의다.

따라서 모든 모델링, SHAP, segmentation, dashboard, presentation은 다음 질문으로 되돌아와야 한다.

`이 결과는 100원딜 고객을 이해하는 데 어떤 도움을 주는가?`

이 질문에 답하지 못하는 산출물은 최종 발표의 중심에 놓으면 안 된다.


> 주의: 아래 `PUBLIC result 1~8 model audit and comparison` 기록은 당시 8개 모델 1차 audit 기준이다.  
> 이후 trial-level overfit audit 및 `PUBLIC_results_only.zip` 재검수로 인해 CatBoost `strong_candidate` 판단은 superseded 되었다.  
> 최신 모델 후보 판단은 `현재 canonical 기준 요약` 및 `PUBLIC_results_only.zip 기반 보수형 모델 재판단` 섹션을 우선한다.

<!-- PUBLIC_MODEL_AUDIT_260520_START -->

> 2026-05-20 PUBLIC result 1~8 model audit and comparison

# 작업일

2026-05-20

# 작업명

PUBLIC result 1~8 model audit and comparison

# 작업 목적

`PUBLIC/results`에 모인 8개 모델 실행 결과를 검수하고, promo1과 promo0을 분리해 다음 단계의 score source 후보를 정리했습니다. 이번 작업은 세그먼트 생성 전 preflight 검수입니다.

# 입력으로 확인한 폴더

- results
- 확인한 result 하위 폴더 수: 8

# 확인한 final_result.csv 개수

8

# 확인한 trials_all.csv 개수

8

# 생성한 산출물 목록

- model_audit_260520/PUBLIC_results_inventory.csv
- model_audit_260520/PUBLIC_final_result_raw_concat.csv
- model_audit_260520/PUBLIC_trials_summary.csv
- model_audit_260520/PUBLIC_model_comparison.csv
- model_audit_260520/PUBLIC_model_selection_memo.md
- model_audit_260520/PUBLIC_model_audit_final_checks.csv
- model_audit_260520/PUBLIC_model_audit_review_zip_inventory.csv
- model_audit_260520/note_tail_PUBLIC_model_audit_260520.md
- zip/PUBLIC_model_audit_260520_review_package.zip

# promo1 후보 모델 요약

현재 비교표 기준 1차 후보는 `CatBoost`입니다. 후보 수준은 `strong_candidate`이며, 최종 확정이 아니라 사용자 승인 필요 상태입니다.

# promo0 후보 모델 요약

현재 비교표 기준 1차 후보는 `CatBoost`입니다. 후보 수준은 `strong_candidate`이며, 최종 확정이 아니라 사용자 승인 필요 상태입니다.

# 아직 확정하지 않은 것

- 최종 모델 확정 안 함
- promo1 score source 최종 확정 안 함
- promo0 score source 최종 확정 안 함
- row-level score table 생성 방식 확정 안 함
- SHAP 기준 모델 확정 안 함
- segmentation 기준 score 확정 안 함

# 다음 단계

사용자 승인 이후, 선택된 후보 모델 기준으로 row-level OOF score table을 생성합니다.

# 금지한 작업

- 세그먼트 생성 안 함
- SHAP 생성 안 함
- row-level score table 생성 안 함
- 기존 segment_visual_guide.html 수정 안 함
- 발표 스토리 수정 안 함

# 미해결 리스크

- final_checks PASS는 형식 검수 PASS이며, 의미 검수 PASS가 아닙니다.
- 일부 PR-AUC 계열 train/valid metric은 final_result에 없어서 비교표에서 missing으로 남겼습니다.
- 후보 모델은 자동 확정이 아니라 사용자 승인 전 preflight 후보입니다.

<!-- PUBLIC_MODEL_AUDIT_260520_END -->


> 주의: 아래 `PUBLIC overfit-adjusted model selection` 기록은 기존 8개 모델 결과 기준으로 CatBoost를 조건부 후보로 둔 중간 판단이다.  
> 이후 보수형 CatBoost 및 보수형 GradientBoosting 추가 실행 결과, 최신 1차 추천 후보는 GradientBoosting conservative로 이동했다.  
> 아래 기록은 연대기적 중간 판단으로 보존하되, 최신 작업 기준으로 직접 사용하지 않는다.

<!-- PUBLIC_MODEL_SELECTION_OVERFIT_260520_START -->

> 2026-05-20 PUBLIC overfit-adjusted model selection

# 작업일

2026-05-20

# 작업명

PUBLIC overfit-adjusted model selection

# 작업 목적

`PUBLIC/results`의 8개 모델 결과를 다시 읽고, 기존 성능 지표에 trial-level overfit 비율을 반영해 promo1/promo0별 score source 후보를 다시 정리했습니다.

# 입력으로 확인한 results 폴더

- results

# 확인한 final_result.csv 개수

8

# 확인한 trials_all.csv 개수

8

# 8개 모델 overfit_rate 요약

- promo0 CatBoost: overfit_rate=86.5%, risk=severe_overfit_pool, top5=100.0%, top10=100.0%, top20=100.0%
- promo0 LogisticRegression: overfit_rate=0.0%, risk=low_overfit_pool, top5=0.0%, top10=0.0%, top20=0.0%
- promo0 RandomForest: overfit_rate=97.5%, risk=severe_overfit_pool, top5=100.0%, top10=100.0%, top20=100.0%
- promo0 SVM: overfit_rate=27.5%, risk=mild_overfit_pool, top5=0.0%, top10=0.0%, top20=0.0%
- promo1 CatBoost: overfit_rate=90.0%, risk=severe_overfit_pool, top5=100.0%, top10=100.0%, top20=100.0%
- promo1 LogisticRegression: overfit_rate=0.0%, risk=low_overfit_pool, top5=0.0%, top10=0.0%, top20=0.0%
- promo1 RandomForest: overfit_rate=98.0%, risk=severe_overfit_pool, top5=100.0%, top10=100.0%, top20=100.0%
- promo1 SVM: overfit_rate=28.5%, risk=mild_overfit_pool, top5=0.0%, top10=0.0%, top20=5.0%

# CatBoost promo0/promo1 overfit 비율

- CatBoost promo0: 86.5%
- CatBoost promo1: 90.0%

# 기존 판단과 달라진 점

이전 판단은 성능 지표 중심이었고, 이번 판단은 `trials_all.csv` 전체의 overfit pool risk를 함께 반영했습니다. CatBoost는 성능상 강하지만 사용자 승인 전까지 조건부 후보로 둡니다.

# promo1 모델 후보

- 1순위 조건부 후보: CatBoost
- recommendation: conditional_recommended_after_user_approval
- 사용자 승인 필요

# promo0 모델 후보

- 1순위 조건부 후보: CatBoost
- recommendation: conditional_recommended_after_user_approval
- 사용자 승인 필요

# backup candidate

- promo1 backup: SVM
- promo0 backup: SVM

# baseline candidate

- promo1 baseline: LogisticRegression
- promo0 baseline: LogisticRegression

# 아직 확정하지 않은 것

- 최종 모델 확정 안 함
- promo1 score source 확정 안 함
- promo0 score source 확정 안 함
- row-level OOF score table 생성 방식 확정 안 함
- SHAP 기준 모델 확정 안 함
- segmentation 기준 score 확정 안 함

# 다음 단계: row-level OOF score table 생성

사용자 승인 이후, 선택된 모델 후보 기준으로 row-level OOF score table을 생성합니다.

# 이번 단계에서 하지 않은 것

- row-level score table 생성 안 함
- OOF score 생성 안 함
- SHAP 생성 안 함
- segmentation 생성 안 함
- HTML 수정 안 함

# 미해결 리스크

- score source 후보는 최종 확정이 아니라 사용자 승인 전 조건부 후보입니다.
- overfit_risk_level은 preflight heuristic입니다.
- final_result와 trials_all은 파싱되었지만, score table은 아직 생성하지 않았습니다.

# 생성한 산출물

- model_selection_overfit_260520/PUBLIC_model_selection_input_inventory.csv
- model_selection_overfit_260520/PUBLIC_final_result_metrics_reparsed.csv
- model_selection_overfit_260520/PUBLIC_trial_level_overfit_summary.csv
- model_selection_overfit_260520/PUBLIC_overfit_adjusted_model_selection.csv
- model_selection_overfit_260520/PUBLIC_overfit_adjusted_model_selection_memo.md
- model_selection_overfit_260520/PUBLIC_model_selection_overfit_final_checks.csv
- model_selection_overfit_260520/PUBLIC_model_selection_overfit_review_zip_inventory.csv
- model_selection_overfit_260520/note_tail_PUBLIC_model_selection_overfit_260520.md
- zip/PUBLIC_model_selection_overfit_260520_review_package.zip

<!-- PUBLIC_MODEL_SELECTION_OVERFIT_260520_END -->


## 2026-05-15 06x_cold_start_rowlevel_hotfix_260515
- 06x cold_start row-level hotfix 수행.
- USER_KEY 단위 first watch 방식이 아니라 master_row_id/subscription-event row 기준으로 재계산함.
- raw 기준 변경 수 1802 / 985.
- primary cohort 기준 변경 수 1786 / 969.
- negative first_watch_rel_day 0건.
- conservative/expanded dataset은 23097 rows 유지.
- 새로 생성된 feature는 기존 승인된 3개뿐임: is_basic, is_cold_start_3d_fixed, is_cold_start_7d_fixed.
- 다음 단계는 07x.


## 2026-05-20 06y_promo_split_260520
- PUBLIC 06x expanded dataset을 `is_promotion` 기준으로 분할함.
- source rows: 23097.
- promo_0 rows: 11193.
- promo_1 rows: 11904.
- unexpected is_promotion rows: 0.
- outputs: PUBLIC/results/_06y_promo_split_260520.


---

## 2026-05-20 | PUBLIC_model_notebook_prep_260520

- 사용자 결정으로 feature set은 current로 고정됨.
- 기존 `retention_w2_ratio`, `retention_w3_ratio`는 모델 입력 CSV에서 제거함.
- `log_retention_w2_ratio`, `log_retention_w3_ratio`는 모델 입력 CSV에 유지함.
- 사용한 입력 데이터:
  - `PUBLIC/data/06_expanded_dataset_promo_0_log_retention.csv`
  - `PUBLIC/data/06_expanded_dataset_promo_1_log_retention.csv`
- 생성한 모델 입력 CSV:
  - `PUBLIC/data/06_model_input_promo_0.csv`
  - `PUBLIC/data/06_model_input_promo_1.csv`
- promo0 row 수: 11193
- promo1 row 수: 11904
- 생성한 노트북:
  - `PUBLIC/notebooks/06_gb_promo0.ipynb`
  - `PUBLIC/notebooks/06_gb_promo1.ipynb`
  - `PUBLIC/notebooks/06_lr_promo0.ipynb`
  - `PUBLIC/notebooks/06_lr_promo1.ipynb`
- Optuna는 `N_TRIALS=100`으로 고정함.
- 예정 OUT_DIR:
  - `PUBLIC/results/_06_model_rerun_260520/gb_promo0`
  - `PUBLIC/results/_06_model_rerun_260520/gb_promo1`
  - `PUBLIC/results/_06_model_rerun_260520/lr_promo0`
  - `PUBLIC/results/_06_model_rerun_260520/lr_promo1`
- 이번 goal에서는 모델을 실행하지 않음.
- `final_result.csv`, `trials_all.csv`는 아직 생성되지 않는 것이 정상임.
- 사용자와 팀원이 다음 단계에서 4개 노트북을 수동 실행할 예정임.
- 하지 않은 것: 모델 실행, OOF score table 생성, SHAP 생성, segmentation 생성, HTML 수정, 기존 결과 삭제.
- 미해결 리스크: USER_KEY 중복에 따른 group leakage caveat, 기존 결과와 log-only 결과의 feature set 차이, 실행 전이므로 성능/overfit 판단 불가.
- 다음 단계: 사용자가 4개 노트북을 실행한 뒤 결과 ZIP을 전달하면 assistant가 형식 검수와 의미 검수를 분리해 검수한다.
- canonical update: feature set은 current로 고정됨. 기존 retention은 모델 입력에서 제거됨. 기존 09/10/07/08 결과는 reference로 유지됨.
- 구조 보정: `11/12/13/14`는 독립 pipeline step처럼 보이므로 사용하지 않는다. 이번 작업은 `06 current` 계열의 모델 variant 준비 작업이며, 모델별 결과는 `_06_model_rerun_260520` 하위 폴더에 둔다.

## 2026-05-20 | PUBLIC pipeline realignment to park.ingyeom canonical flow

- 이번 작업은 모델 실행이 아니라 pipeline 구조 정렬 작업임.
- 01~05 계약은 사용자 확인 기준 동일하다고 보고 승계함.
- 06부터 원래 park.ingyeom 흐름을 최대한 따라가도록 구조를 생성함.
- 06는 dataset/input preparation으로 제한함.
- 06 안에 있던 모델 노트북/결과는 misnumbered/modeling artifact로 보고 archive/reference 또는 user review 대상으로 분리함.
- 07~10는 생략 대상이 아니며, 모델링 전 반드시 존재해야 하는 검증/EDA/audit 단계임.
- 11/12/14/15/16/17/18는 placeholder를 생성했지만 이번 작업에서 실행하지 않음.
- 빈 폴더는 의도적으로 생성한 placeholder임.
- 이후 실제 실행 순서는 06 canonical check -> 07 -> 08 -> 09 -> 10 -> 11 -> 12 -> 14 -> 15 -> 16 -> 17 -> 18.
- 사용자 승인 없이 07~10을 건너뛰고 모델링으로 가지 말 것.

## 2026-05-20 | PUBLIC 99_model_selections notebook reorganization

- ?? ?? ???? canonical pipeline stage ??? ???.
- ? ??: `PUBLIC/notebooks/99_model_selections/`.
- ?? ??? ?? ??? ???: `catboost`, `svm`, `random_forest`, `logistic_regression`, `gradient_boosting`.
- ?? ??? ?? ??? ??? ??? ?? ?? ??? ??? `.ipynb`? ???.
- `06x_dataset_generation_260515.ipynb`, `06y_promo_split_260520.ipynb`? ?? ?? ????? ?? ?? ???? ??.
- ??? archive/reference? ???? 06 ?? ???? ?? ??? ??? ????.
- ?? ???? ??? ??, ?? ??, Optuna ??, SHAP ??, segmentation ??? ???? ??.
- ?? results ??? ???? ??.

## 2026-05-20 | PUBLIC clean numeric stage naming

- canonical stage folder names were changed from `06~18` style to clean numeric names: `06`, `07`, `08`, `09`, `10`, `11`, `12`, `14`, `15`, `16`, `17`, `18`.
- `06x_dataset_generation_260515.ipynb` and `06y_promo_split_260520.ipynb` were moved under `PUBLIC/notebooks/06_dataset_260520/` because they are dataset/input preparation substeps, not model-selection notebooks.
- `99_model_selections` remains the location for model-running notebooks.
- This was a structure and naming cleanup only. No notebooks were executed, and no model training, Optuna, SHAP, or segmentation was performed.

## 2026-05-20 | PUBLIC structure cleanup full work log

이번 섹션은 2026-05-20에 assistant가 `PUBLIC` 내부에서 수행한 구조 정리 작업을 빠짐없이 남기기 위한 기록이다. 이 기록은 작업자가 이후 파일 이동의 이유와 현재 구조를 추적할 수 있도록 작성한다.

### 1. 작업 범위

- 작업 루트는 `C:\Code\ott-churn-prediction\PUBLIC` 내부로 제한했다.
- `park.ingyeom` 폴더는 수정하지 않았다.
- `_data` 폴더는 수정하지 않았다.
- raw source 파일은 수정하지 않았다.
- 모델 노트북 실행, 모델 학습, Optuna 실행, SHAP 실행, segmentation 실행은 수행하지 않았다.
- 이번 작업은 파일 및 폴더 구조 정리, archive/reference 이동, README/manifest/final_checks/zip 갱신 작업이었다.

### 2. 처음 확인한 PUBLIC 구조

- `PUBLIC` 루트에 `data`, `legacy`, `notebooks`, `results`, `zip`, `note.md`, `README.md`가 존재하는 것을 확인했다.
- `PUBLIC/notebooks`에는 모델 실행 노트북, dataset preparation 노트북, 그리고 이후 생성한 canonical stage placeholder 폴더가 섞여 있었다.
- `PUBLIC/results`에는 기존 모델 결과, 06x/06y 결과, 06 계열 모델 준비 산출물, 06 계열 모델 rerun 산출물이 섞여 있었다.
- 구조 정리 전에 `PUBLIC_existing_inventory_before_realignment.csv`를 생성했다.

### 3. 06 계열 모델 산출물 처리

- 처음에는 이름상 `06`에 가까우나 실제 성격이 모델링인 노트북과 결과가 존재했다.
- 해당 노트북은 `gb`, `lr`, `fit`, `predict_proba`, `Optuna`, `final_result.csv`, `trials_all.csv` 등의 단서가 있어 dataset/input preparation이 아니라 모델 실행 노트북으로 보았다.
- 모델링 산출물은 canonical 06 dataset/input preparation 단계에 둘 수 없다고 판단했다.
- 삭제하지 않고 archive/reference로 격리했다.
- 이후 사용자의 요청에 따라 archive에 있던 06 계열 모델 노트북도 `99_model_selections` 아래 모델 계열별 폴더로 다시 이동했다.
- 관련 기록은 `PUBLIC/handoff/PUBLIC_pipeline_realignment_260520/misnumbered_06_model_artifacts_audit.csv`에 남겼다.

### 4. canonical pipeline placeholder 생성

- 처음에는 사용자가 제시한 구조를 따라 `06z~18z` 형식의 placeholder를 만들었다.
- 이후 사용자의 지적에 따라 `z` 접미가 구조적으로 불필요하다고 판단하고 clean numeric naming으로 전부 변경했다.
- 최종 canonical notebook stage 폴더는 다음과 같다.
  - `PUBLIC/notebooks/06_dataset_260520`
  - `PUBLIC/notebooks/07_feature_mapping_AARRR_260520`
  - `PUBLIC/notebooks/08_promotion_nonpromotion_EDA_260520`
  - `PUBLIC/notebooks/09_promotion_repurchase_2x2_EDA_260520`
  - `PUBLIC/notebooks/10_feature_distribution_redundancy_pre_audit_260520`
  - `PUBLIC/notebooks/11_baseline_growth_comparison_260520`
  - `PUBLIC/notebooks/12_model_family_comparison_260520`
  - `PUBLIC/notebooks/14_candidate_tuning_260520`
  - `PUBLIC/notebooks/15_oof_score_or_sensitivity_260520`
  - `PUBLIC/notebooks/16_SHAP_candidate_interpretation_260520`
  - `PUBLIC/notebooks/17_segmentation_design_260520`
  - `PUBLIC/notebooks/18_business_recommendation_storyline_260520`
- 각 stage folder 안에는 README placeholder를 만들었다.
- 각 README에는 stage name, status, expected inputs, expected outputs, why this stage exists, forbidden actions, next stage를 기록했다.

### 5. 06x와 06y 노트북 처리

- `06x_dataset_generation_260515.ipynb`는 모델 노트북으로 보지 않았다.
- 확인한 내용상 이 노트북은 `cold_start` row-level hotfix와 dataset generation 역할을 한다.
- `06y_promo_split_260520.ipynb`도 모델 노트북으로 보지 않았다.
- 확인한 내용상 이 노트북은 `06x_expanded_dataset.csv`를 `is_promotion` 기준으로 나누는 promotion split 작업이다.
- 따라서 두 노트북은 `99_model_selections`로 보내지 않고 06 dataset preparation 단계 안으로 이동했다.
- 최종 위치는 다음과 같다.
  - `PUBLIC/notebooks/06_dataset_260520/06x_dataset_generation_260515.ipynb`
  - `PUBLIC/notebooks/06_dataset_260520/06y_promo_split_260520.ipynb`
- 이동 기록은 `PUBLIC/handoff/PUBLIC_pipeline_realignment_260520/PUBLIC_06xy_notebook_relocation_260520.csv`에 남겼다.

### 6. model-running notebook 재배치

- 모델을 돌리는 노트북은 canonical pipeline stage folder에 두지 않고 별도 보관소로 분리했다.
- 새 위치는 `PUBLIC/notebooks/99_model_selections/`이다.
- 모델 계열별 하위 폴더를 만들었다.
  - `catboost`
  - `svm`
  - `random_forest`
  - `logistic_regression`
  - `gradient_boosting`
- 이동한 모델 노트북은 총 16개다.
- `catboost`에는 기존 CatBoost 관련 4개 노트북을 이동했다.
- `svm`에는 기존 SVM 관련 2개 노트북을 이동했다.
- `random_forest`에는 기존 RandomForest 관련 2개 노트북을 이동했다.
- `logistic_regression`에는 기존 LR 관련 2개와 06 계열 LR 노트북 2개를 이동했다.
- `gradient_boosting`에는 기존 GradientBoosting 관련 2개와 06 계열 GB 노트북 2개를 이동했다.
- 이동 기록은 `PUBLIC/notebooks/99_model_selections/99_model_selections_notebook_manifest_260520.csv`에 남겼다.
- `PUBLIC/notebooks/99_model_selections/README.md`를 생성했다.
- 기존 `results` 폴더의 모델 결과는 이 단계에서 99 폴더로 이동하지 않았다.

### 7. log_retention_only 명명 제거

- 사용자가 `log_retention_only` 명명을 제거하라고 지시했다.
- 파일명, 폴더명, README, handoff CSV, note, 이전 prep 문서, archive notebook 내부 제목에서 해당 명명을 제거했다.
- `log_retention_only`, `logretention_only`, `log-retention-only` 형태를 검색하여 제거했다.
- 최종 확인에서 해당 표현의 파일명 검색 결과는 0건이었다.
- 최종 확인에서 해당 표현의 본문 검색 결과도 0건이었다.
- 다만 `log_retention_w2_ratio`, `log_retention_w3_ratio` 같은 실제 컬럼명은 별개의 컬럼명이므로 제거 대상 명명과 구분해야 한다.

### 8. z 접미 제거 및 clean numeric naming 적용

- `06z~18z` naming은 최종 구조에서 제거했다.
- 파일명과 본문에서 `06z`, `07z`, `08z`, `09z`, `10z`, `11z`, `12z`, `14z`, `15z`, `16z`, `17z`, `18z` 표현을 제거했다.
- stage id는 `06`, `07`, `08`, `09`, `10`, `11`, `12`, `14`, `15`, `16`, `17`, `18`로 정리했다.
- `PUBLIC_pipeline_stage_map_260520.csv`도 clean numeric stage id로 갱신했다.
- 최종 확인에서 `06z~18z` 형태의 파일명 검색 결과는 0건이었다.
- 최종 확인에서 `06z~18z` 형태의 본문 검색 결과도 0건이었다.

### 9. handoff 및 검수 산출물

- handoff root는 `PUBLIC/handoff/PUBLIC_pipeline_realignment_260520/`이다.
- 주요 산출물은 다음과 같다.
  - `README.md`
  - `PUBLIC_existing_inventory_before_realignment.csv`
  - `PUBLIC_pipeline_stage_map_260520.csv`
  - `misnumbered_06_model_artifacts_audit.csv`
  - `PUBLIC_pipeline_realignment_final_checks.csv`
  - `PUBLIC_pipeline_realignment_zip_inventory.csv`
  - `PUBLIC_06xy_notebook_relocation_260520.csv`
- `PUBLIC_pipeline_realignment_final_checks.csv`는 최종 기준 32개 PASS를 확인했다.
- final_checks PASS는 구조 정렬 검수 PASS를 뜻한다.
- final_checks PASS는 모델 성능, semantic validity, SHAP validity, segmentation validity를 뜻하지 않는다.

### 10. review zip

- review zip은 `PUBLIC/zip/PUBLIC_pipeline_realignment_260520_review_package.zip`에 생성했다.
- zip inventory는 `PUBLIC/handoff/PUBLIC_pipeline_realignment_260520/PUBLIC_pipeline_realignment_zip_inventory.csv`에 생성했다.
- zip에는 handoff README, inventory, stage map, misnumbered audit, final checks, zip inventory, note, 각 stage README, `99_model_selections` README와 manifest를 포함했다.

### 11. 최종 PUBLIC/notebooks 구조

- 최종 확인 기준 `PUBLIC/notebooks` 루트에는 다음 항목이 있다.
  - `06_dataset_260520`
  - `07_feature_mapping_AARRR_260520`
  - `08_promotion_nonpromotion_EDA_260520`
  - `09_promotion_repurchase_2x2_EDA_260520`
  - `10_feature_distribution_redundancy_pre_audit_260520`
  - `11_baseline_growth_comparison_260520`
  - `12_model_family_comparison_260520`
  - `14_candidate_tuning_260520`
  - `15_oof_score_or_sensitivity_260520`
  - `16_SHAP_candidate_interpretation_260520`
  - `17_segmentation_design_260520`
  - `18_business_recommendation_storyline_260520`
  - `99_model_selections`
  - `_archive`
  - `generate_notebooks.py`

### 12. 현재 해석 기준

- `06_dataset_260520`은 dataset/input preparation 단계다.
- `06x`와 `06y`는 06 단계 내부의 historical substep으로 둔다.
- `07~10`은 모델링 전 검증, mapping, EDA, redundancy/proxy audit 단계다.
- `11~14`는 모델링, model family comparison, candidate tuning 단계다.
- `15`는 OOF score 또는 sensitivity 단계다.
- `16`은 SHAP/model explanation 단계다.
- `17`은 segmentation design 단계다.
- `18`은 business recommendation storyline 단계다.
- `99_model_selections`는 과거 또는 후보 모델 실행 노트북의 보관 위치다.

### 13. 하지 않은 것

- 노트북을 실행하지 않았다.
- 모델을 학습하지 않았다.
- Optuna를 실행하지 않았다.
- SHAP을 실행하지 않았다.
- segmentation을 실행하지 않았다.
- raw source CSV를 수정하지 않았다.
- `park.ingyeom` 폴더를 수정하지 않았다.
- `_data` 폴더를 수정하지 않았다.
- 기존 모델 결과의 성능을 검증하지 않았다.
- 07~10 분석을 수행하지 않았다.
- 11 이후 모델링 단계로 진입하지 않았다.

### 14. 다음 작업 순서

- 다음 실제 실행 순서는 `06 -> 07 -> 08 -> 09 -> 10 -> 11 -> 12 -> 14 -> 15 -> 16 -> 17 -> 18`이다.
- 먼저 `06_dataset_260520`에서 dataset/input check를 수행해야 한다.
- 그다음 `07_feature_mapping_AARRR_260520`으로 넘어가야 한다.
- `07~10`을 건너뛰고 `11` 모델링으로 바로 이동하면 안 된다.
- `99_model_selections`의 노트북은 reference 또는 future model-selection material로 보아야 하며, canonical 실행 완료 상태로 보아서는 안 된다.

## 2026-05-20 | PUBLIC structure correction 2: model reference folders and 99_model_selections clarification

- 이번 작업은 모델 실행이 아니라 PUBLIC 구조 보정 2차 작업이다.
- `PUBLIC/results/model`은 active canonical pipeline stage output이 아니라 legacy/reference model candidate output 보관 위치로 명시했다.
- `PUBLIC/results/model` 내부 숫자 prefix는 정규 pipeline step 번호가 아니며, 모델 후보 또는 legacy numbering으로만 해석해야 한다.
- `PUBLIC/notebooks/99_model_selections`는 정규 pipeline stage가 아니라 model candidate notebook pool로 명시했다.
- `99_model_selections` 내부 노트북 숫자 prefix도 정규 pipeline step 번호가 아니다.
- 이 폴더가 존재한다고 해서 07, 08, 09, 10 단계를 건너뛰면 안 된다.
- 정규 흐름은 06 dataset/input check 이후 07 feature mapping, 08 EDA, 09 2x2 EDA, 10 redundancy/proxy audit을 거친 뒤 11/12/14 모델링으로 진입하는 것이다.
- 이번 작업에서는 모델 학습, 노트북 실행, Optuna, SHAP, segmentation을 수행하지 않았다.
- 기존 결과는 삭제하지 않았다.
- 이번 작업의 목적은 잘못된 숫자 prefix와 folder location이 정규 pipeline 단계로 오해되는 것을 막는 것이다.

## 2026-05-20 | Emergency bypass to Step 11 modeling before full 07~10 execution

### Context

현재 PUBLIC 파이프라인은 원칙적으로 다음 순서를 따라야 한다.

`06 dataset/input check → 07 feature mapping/AARRR → 08 promotion vs nonpromotion EDA → 09 promotion × repurchase 2x2 EDA → 10 feature distribution/redundancy/proxy audit → 11 modeling`

그러나 현재 일정상 모델링 결과가 급하게 필요하므로, 사용자는 임시로 11번 모델링 단계로 먼저 진입하는 것을 승인했다.

이 결정은 07, 08, 09, 10을 완료한 것으로 간주한다는 뜻이 아니다.  
또한 07~10이 불필요하다는 뜻도 아니다.

이번 결정의 정확한 지위는 다음과 같다.

> 07~10은 skipped가 아니라 temporarily bypassed / pending validation 상태다.  
> 11번 모델링은 emergency modeling reference로 수행한다.  
> 11번 결과는 07~10 사후 검증 전까지 final canonical modeling evidence로 사용하지 않는다.

---

### Decision

사용자 승인에 따라 PUBLIC 작업은 급한 일정 대응을 위해 11번 모델링 단계로 임시 진입한다.

단, 다음 조건을 강제한다.

- 01~05 계약은 사용자 확인 기준 기존 park.ingyeom과 동일한 것으로 승계한다.
- 06 dataset/input preparation 결과를 11 모델링 입력으로 사용한다.
- 07 feature mapping/AARRR, 08 EDA, 09 2x2 EDA, 10 redundancy/proxy audit은 아직 완료된 것으로 기록하지 않는다.
- 07~10은 pending validation 상태로 남긴다.
- 11 결과는 emergency modeling reference로만 기록한다.
- 11 결과를 final model, final feature interpretation, final SHAP input, final segmentation 기준으로 확정하지 않는다.
- 11 이후 12/14/16/17로 계속 진행하려면, 각 단계에서 “07~10 bypass 상태”를 명시해야 한다.
- 가능하면 11 수행 후 빠르게 07~10 사후 audit 또는 최소한 10 redundancy/proxy audit으로 돌아온다.

---

### Why this is allowed

이번 bypass는 이상적인 절차가 아니다.

원래라면 07~10을 먼저 수행해 feature mapping, EDA, 2x2 구조, redundancy/proxy risk를 확인한 뒤 11 모델링으로 들어가야 한다.

하지만 현재 프로젝트 진행상 모델링 결과가 급하게 필요하므로, 사용자가 명시적으로 emergency bypass를 승인했다.

따라서 이번 11번 모델링은 정규 canonical 진행이 아니라 시간 제약 하에서 만든 임시 모델링 reference다.

---

### Risk

이번 bypass의 주요 위험은 다음과 같다.

- 07 feature mapping/AARRR가 최신 06 dataset/input과 완전히 정렬되었는지 아직 확인되지 않았다.
- 08 promotion vs nonpromotion EDA가 최신 PUBLIC 기준으로 수행되지 않았다.
- 09 promotion × repurchase 2x2 EDA가 최신 PUBLIC 기준으로 수행되지 않았다.
- 10 feature distribution/redundancy/proxy audit이 최신 PUBLIC 기준으로 수행되지 않았다.
- 모델이 성능상 좋아 보여도 feature redundancy, proxy artifact, scope leakage, interpretation risk가 나중에 발견될 수 있다.
- 11 결과를 곧바로 SHAP, segmentation, business action으로 연결하면 위험하다.

---

### Guardrail

11번 모델링에서 반드시 지킬 것:

- `USER_KEY`는 group key로만 사용한다.
- `is_repurchase`는 target으로만 사용한다.
- `is_promotion`은 scope policy를 따른다.
- groupwise model에서는 `is_promotion`을 feature로 넣지 않는다.
- raw source CSV를 수정하지 않는다.
- 07~10 미수행 상태를 README와 final_checks에 기록한다.
- 모델 성능 결과를 final model로 표현하지 않는다.
- feature importance나 SHAP 없이 원인 해석을 하지 않는다.
- segmentation으로 바로 넘어가지 않는다.
- final_checks PASS를 의미 검수 PASS로 표현하지 않는다.

---

### Required wording

허용 표현:

- `Step 11 emergency modeling reference`
- `07~10 temporarily bypassed due to urgent timeline`
- `pending 07~10 validation`
- `not final canonical model evidence`
- `requires follow-up mapping/EDA/redundancy audit`

금지 표현:

- `07~10 skipped`
- `07~10 unnecessary`
- `Step 11 canonical complete`
- `modeling finalized`
- `ready for SHAP`
- `ready for segmentation`
- `final model selected`

---

### Next action

다음 작업은 `11_baseline_growth_comparison_260520` 또는 이에 준하는 11번 emergency modeling reference 수행이다.

단, Codex goal에는 반드시 다음 문구를 포함한다.

> This is an emergency bypass into Step 11.  
> Steps 07~10 are not completed and must be recorded as pending validation.  
> Step 11 output is emergency modeling reference only, not final canonical modeling evidence.



## 2026-05-20 | PUBLIC 11/12 emergency model stage meaning corrected

이전에 급한 일정 때문에 11로 emergency bypass하는 결정을 했다.

하지만 11을 LogisticRegression 전용, 12를 GradientBoosting 전용으로 해석하면 pipeline 의미가 깨진다.

11은 log-retention-only four-model emergency reference 단계로 재정의한다.

12는 four-model comparison summary 단계로 재정의한다.

LogisticRegression promo0/promo1과 GradientBoosting promo0/promo1은 모두 11 emergency reference 안에 모은다.

12에서는 네 결과를 비교한다.

07~10은 여전히 pending validation이다.

이번 작업에서는 모델 실행, 노트북 실행, Optuna, SHAP, segmentation을 하지 않았다.

기존 결과는 이동하지 않고, 11 reference 구조로 copy했다.

copied result는 final canonical model evidence가 아니다.

기존 `11x_baseline_growth_comparison_260516.ipynb`는 LogisticRegression 전용 단계가 아니라 baseline growth comparison 단계였다.

기존 `12x_model_family_comparison_260516.ipynb`는 GradientBoosting 전용 단계가 아니라 model family comparison 단계였다.

현재 PUBLIC emergency 구조는 기존 11x/12x의 의미를 축소 적용한 임시 구조다.

기존 11x/12x 원본 notebook은 future template/reference로만 기록하며, 이번 작업에서 실행하지 않았다.

이번 결과는 final canonical model evidence가 아니다.

다음 단계는 12 comparison review 또는 07~10 pending validation 해소다.


## 2026-05-20 | PUBLIC 12 four-model comparison review completed

이번 작업은 12 four-model comparison review다.

11 emergency four-model reference에 모인 4개 log-retention-only 결과를 비교했다.

4개 모델은 LogisticRegression promo0, LogisticRegression promo1, GradientBoosting promo0, GradientBoosting promo1이다.

promo0와 promo1은 분리해서 비교했다.

final_result.csv 기반 성능 요약을 만들었다.

trials_all.csv 기반 overfit/stability 요약을 만들었다.

log retention only 조건을 다시 확인했다.

OOF score table은 생성하지 않았다.

SHAP, segmentation, Optuna는 수행하지 않았다.

07~10은 여전히 pending validation이다.

이 결과는 final model selection이 아니다.

계산하지 못한 항목은 없다. `trials_all.csv`에 `mean_valid_auc`, `gap`, `overfit` 컬럼이 있어서 overfit/stability와 topN overfit rate를 계산했다.

다음 단계는 사용자 승인 후 OOF score table 생성 또는 07~10 pending validation 해소다.


## 2026-05-20 | PUBLIC 12 high-AUC leakage/proxy steering applied

이번 steering 이후 12 four-model comparison review의 중심 목적을 수정했다.

이 작업은 가장 성능 좋은 모델을 고르는 작업이 아니다.

이 작업은 log-retention-only 4개 모델의 AUC가 과도하게 높아 보일 가능성을 leakage, proxy, overfit, split issue 관점에서 엄격하게 검수하는 작업이다.

Because AUC appears unusually high for this project context, this step treats high performance as a validation target rather than as immediate evidence of model quality.

현재 AUC가 프로젝트 맥락상 과도하게 높아 보일 수 있으므로, 이번 단계에서는 높은 성능을 곧바로 성과로 해석하지 않고 leakage, proxy, overfit, split issue 검수 대상으로 취급한다.

AUC가 0.90 이상인 모델은 `suspicious_high_auc_flag = 1`로 표시했다.

`final_result.csv`의 best metric만 보고 후보를 추천하지 않도록 README와 output CSV의 문구를 보정했다.

`trials_all.csv` 기준 overfit_rate, top5/top10/top20 overfit_rate, gap, valid AUC 안정성 항목을 확인했다.

feature list 기준 USER_KEY, is_repurchase, repurchase_score, churn_risk, retention_w2_ratio, retention_w3_ratio, is_promotion, target-like/post-outcome 의심 컬럼을 감사했다.

`log_retention_w2_ratio`, `log_retention_w3_ratio`는 사용 여부를 확인했지만, 이 둘이 성능을 과도하게 지배할 가능성을 caveat로 기록했다.

group-aware split 또는 USER_KEY leakage 방지 여부는 확인 가능한 범위에서 감사했으며, GroupKFold 미사용 caveat 때문에 split policy는 PASS로 기록하지 않았다.

OOF readiness는 사용자 승인 전 생성 불가 상태로 유지했다.

추천 문구는 final candidate가 아니라 provisional candidate pending leakage/proxy/overfit/split review로 제한했다.

07~10은 여전히 pending validation 상태이며, 이번 12 결과는 final canonical model selection이 아니다.


## 2026-05-20 | PUBLIC 12 review user-confirmed interpretation hotfix

### 사용자 확인 사항 반영

사용자가 모델 판단의 primary metric을 ROC-AUC로 확인했다.

PR-AUC는 보조 지표이며, PR-AUC가 높다는 이유만으로 suspicious high AUC 또는 leakage 의심으로 처리하지 않는다.

기존 12 review의 high-AUC 경고는 test_pr_auc >= 0.90 트리거로 전부 suspicious_high_auc_flag=1이 됐다. 이는 PR-AUC 중심 오해가 섞인 과잉 차단이었으므로 보정했다. 보정 후 suspicious_high_auc_flag_after는 전부 0이다.

ROC-AUC 범위: LR 0.844~0.860 / GB 0.862~0.883. 이 범위는 high_but_plausible_pending_standard_checks로 기록한다.

### is_churn_prevented 보정

is_churn_prevented는 사용자 확인 기준 과거 포인트 수령 또는 churn prevention event 긍정 반응 이력 flag다.

is_churn_prevented는 자동 leakage FAIL이 아니다. approved_context_feature_with_interpretation_caveat로 재분류했다.

금지 표현: "current-cycle post-treatment effect", "current intervention caused repurchase"

안전한 표현: "past churn prevention response history"

### split 기준 보정

split 기준은 USER_KEY가 아니라 USER_NUM이며, 사용자 확인 기준 중복은 처리된 상태다.

USER_KEY 중복을 근거로 GroupKFold 미사용을 자동 FAIL 처리하지 않는다.

실제 입력 CSV(06_model_input_promo_0/1.csv)에는 USER_NUM 컬럼이 없고 USER_KEY가 있다. promo0 USER_KEY 중복 56건 / promo1 1건. 이 수치가 곧바로 split leakage를 의미하지는 않는다. upstream dedup 사용자 확인을 따른다. split 상태: WARN_needs_verification (FAIL 아님).

### 07~10 상태

07~10은 여전히 pending validation이다. 현재 일정상 나중에 처리한다. pending이며 skipped가 아니다.

### 이번 hotfix에서 수행하지 않은 것

이번 hotfix는 OOF, SHAP, segmentation, 모델 재실행을 수행하지 않았다.

OOF score table은 사용자 승인 후 별도 goal로 진행한다.

현재 상태는 final model selection이 아니라 OOF 전 interpretation/readiness correction이다.

### 산출물

- PUBLIC/results/12_model_family_comparison_260520/four_model_comparison_review_hotfix_user_confirmed/
- PUBLIC/handoff/PUBLIC_12_review_hotfix_user_confirmed_260520/
- PUBLIC/zip/PUBLIC_12_review_hotfix_user_confirmed_260520_review_package.zip


## 2026-05-20 | PUBLIC 12 review hotfix wording and zip inventory patch

이번 작업은 12 review user-confirmed hotfix의 문서/zip 보정 patch다.

모델 재실행, 노트북 실행, OOF, Optuna, SHAP, segmentation은 수행하지 않았다.

"Skipped due to schedule" 표현은 오해 소지가 있어 "Temporarily deferred due to schedule; not skipped"로 보정했다. 수정 파일: 12_oof_readiness_user_confirmed_update.csv.

07~10은 skipped가 아니라 pending validation이며 temporarily deferred 상태다. 이 사실은 README와 oof_readiness CSV에 명확히 반영됐다.

final_checks의 review_zip_created / zip_inventory_created 항목은 이전 작업에서 이미 PASS로 기록됐으며, 이번 patch에서 재확인했다.

zip_inventory 자기 자신 누락 문제는 self-reference row 추가(방식 B)로 처리했다. size_bytes는 self-inclusion 이전 기준이며, self-reference limitation을 명시했다.

이번 patch는 모델 성능, feature set, split policy, is_churn_prevented policy를 변경하지 않는다.

OOF score table은 여전히 사용자 승인 후 별도 goal로 진행한다.

## 2026-05-20 | PUBLIC 12 review patch accepted and OOF generation approved by user

### Context

`PUBLIC_12_review_hotfix_user_confirmed_patch_260520_review_package.zip` 검수 결과, 12 review user-confirmed hotfix의 핵심 해석 보정은 반영된 것으로 판단했다.

이번 patch에서 확인된 핵심 보정은 다음이다.

- `PR-AUC >= 0.90`이라는 이유만으로 suspicious high AUC 또는 leakage 의심으로 처리하지 않도록 보정했다.
- 모델 성능 판단의 primary metric은 `ROC-AUC`로 둔다.
- `PR-AUC`는 secondary metric으로 둔다.
- `is_churn_prevented`는 자동 leakage FAIL이 아니라, 사용자 도메인 확인 기준 `approved context feature with interpretation caveat`로 둔다.
- `is_churn_prevented`는 현재 cycle 사후 결과가 아니라, 과거 포인트 수령 또는 churn prevention event 긍정 반응 이력으로 해석한다.
- split policy는 과거 `USER_KEY` 중복 경고를 자동 적용하지 않고, 현재 PUBLIC 기준의 `USER_NUM` 및 중복 처리 완료 전제를 우선 반영한다.
- 07~10은 skipped가 아니라 `pending validation`이며, 일정상 `temporarily deferred` 상태로 기록한다.
- OOF, SHAP, segmentation, Optuna, 모델 재실행은 이번 patch에서 수행하지 않았다.

### Patch review caveat

이번 patch는 내용상 목적을 달성했지만, 형식상 final_checks에는 일부 WARN이 남아 있었다.

특히 다음 항목은 실제로는 생성되었으나, patch final_checks 안에서는 pending처럼 남아 있었다.

- `note_md_append_completed`
- `review_zip_created`
- `zip_inventory_created`

따라서 이번 patch는 내용상 통과하되, 형식 검수상 완전한 무결 상태는 아니라고 기록한다.

이번 WARN은 모델 결과, 데이터, feature set, 성능 지표, split policy, `is_churn_prevented` 해석을 바꾸는 문제는 아니다.  
다만 이후 Claude Code 또는 다른 LLM이 review zip을 만들 때는 final_checks를 최종 산출물 생성 후 다시 갱신하거나, self-reference limitation을 명확히 기록해야 한다.

### User decision

사용자는 현재 일정상 07~10을 나중에 처리하기로 했다.

정확한 상태는 다음과 같다.

- 07~10은 skipped가 아니다.
- 07~10은 unnecessary가 아니다.
- 07~10은 pending validation이다.
- 현재 일정상 temporarily deferred 상태다.

사용자는 12 review hotfix 결과를 받아들이고, 다음 단계로 OOF score table 생성을 진행하기로 승인했다.

단, OOF score table 생성은 final model selection이 아니다.  
OOF는 SHAP과 segmentation으로 가기 위한 row-level score source를 만드는 중간 단계다.

### Current modeling basis

현재 OOF 생성 대상은 11 emergency four-model reference에 모인 log-retention 기준 4개 모델이다.

대상 모델은 다음 네 개다.

- LogisticRegression promo0
- LogisticRegression promo1
- GradientBoosting promo0
- GradientBoosting promo1

현재 모델 판단 기준은 다음과 같다.

- ROC-AUC를 primary metric으로 본다.
- PR-AUC는 secondary metric으로 본다.
- promo0와 promo1은 분리해서 본다.
- 전체 4개 중 하나의 1등 모델을 뽑는 방식이 아니다.
- GradientBoosting은 primary candidate 후보로 볼 수 있다.
- LogisticRegression은 baseline 또는 sensitivity candidate로 유지한다.
- 4개 모델 모두 OOF score를 생성해 GB/LR overlap과 scope별 risk profile을 확인한다.

### OOF generation rule

OOF score table 생성 시 반드시 다음을 지킨다.

- 기존 `final_result.csv`와 `trials_all.csv`는 모델 후보 근거로 사용한다.
- Optuna는 새로 수행하지 않는다.
- SHAP은 수행하지 않는다.
- segmentation은 수행하지 않는다.
- 모델 선택을 final로 확정하지 않는다.
- 07~10 pending validation 상태를 README와 note에 유지한다.
- `is_repurchase`는 target으로만 사용한다.
- `USER_NUM` 또는 식별자 계열은 feature로 사용하지 않는다.
- `USER_KEY`가 존재하더라도 feature로 사용하지 않는다.
- `is_promotion`은 promo split 이후 scope 내부 feature로 사용하지 않는다.
- `retention_w2_ratio`, `retention_w3_ratio`는 feature로 사용하지 않는다.
- `log_retention_w2_ratio`, `log_retention_w3_ratio`는 current feature로 사용한다.
- `is_churn_prevented`는 approved context feature with interpretation caveat로 유지한다.
- `repurchase_score`, `churn_risk`, 기존 score 컬럼이 있으면 feature에서 제외한다.

### Split policy

현재 사용자 확인 기준으로 PUBLIC split 및 중복 기준은 `USER_NUM` 중심이며, 중복은 처리된 상태로 본다.

OOF 생성 시에는 다음을 확인한다.

- 모델 입력 CSV에 `USER_NUM`이 있는지 확인한다.
- `USER_NUM`이 있으면 중복 여부를 확인한다.
- `USER_NUM`이 unique이면 StratifiedKFold 사용이 가능하다.
- `USER_NUM` 중복이 남아 있으면 StratifiedGroupKFold 또는 group-aware split을 검토해야 한다.
- `USER_NUM`이 없으면 어떤 식별자 기준으로 dedup이 완료되었는지 README와 final_checks에 기록한다.
- 확인 불가능한 경우 PASS로 쓰지 말고 WARN으로 기록한다.

### Required OOF outputs

OOF 생성 후 최소 산출물은 다음이다.

- `15_oof_score_long.csv`
- `15_oof_score_wide.csv`
- `15_oof_generation_input_validation.csv`
- `15_oof_feature_policy_check.csv`
- `15_oof_fold_distribution_check.csv`
- `15_oof_metric_summary.csv`
- `15_gb_lr_high_risk_overlap.csv`
- `15_oof_readiness_for_shap_segmentation.csv`
- `README.md`
- `final_checks.csv`
- review zip

OOF score table에는 최소 다음 정보가 있어야 한다.

- row identifier
- `USER_NUM` 또는 사용 가능한 식별자
- `is_repurchase`
- promo scope
- model family
- fold id
- `repurchase_score_oof`
- `churn_risk_score_oof`
- `risk_percentile`
- `high_risk_top10`
- `high_risk_top20`
- `high_risk_top30`

### Interpretation guardrail

OOF score는 final campaign target이 아니다.

OOF score는 다음 단계에서 사용할 row-level risk evidence다.

- GB/LR high-risk overlap 검수
- SHAP 대상 모델 선정 보조
- segmentation rule 설계 보조
- promo1 중심 risk profile 확인
- promo0 비교군 risk profile 확인

OOF score가 생성되었다고 해서 바로 SHAP, segmentation, dashboard, business action으로 넘어가는 것은 아니다.

다음 단계는 OOF 결과 검수다.

### Next action

다음 작업은 `PUBLIC 15 OOF score generation`이다.

Claude Code는 OOF score table을 생성하되, 다음을 금지한다.

- Optuna 재실행 금지
- SHAP 생성 금지
- segmentation 생성 금지
- final model selection 금지
- campaign threshold 확정 금지
- 07~10 완료로 기록 금지

## 2026-05-20 | PUBLIC 15 four-model OOF score generation completed

### 수행 내용

4개 model/scope 조합 (LR promo0, LR promo1, GB promo0, GB promo1)에 대해 row-level OOF score를 생성했다.

- Params: 기존 final_result.csv에서 직접 추출. Optuna 재실행 없음.
- Split: StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
- Split 정책: USER_NUM 없음, USER_KEY 중복 promo0=56 / promo1=1. WARN_WITH_USER_CONFIRMATION. 사용자 domain 확인으로 StratifiedKFold 유지.
- Features: 75개. retention_w2/w3_ratio 제외. log_retention_w2/w3_ratio 사용. is_churn_prevented 포함(승인된 context feature).

### 생성된 산출물 경로

- PUBLIC/results/15_oof_score_or_sensitivity_260520/four_model_oof_scores/15_oof_score_long.csv — 46,194 rows
- PUBLIC/results/15_oof_score_or_sensitivity_260520/four_model_oof_scores/15_oof_score_wide_promo0.csv — 11,193 rows
- PUBLIC/results/15_oof_score_or_sensitivity_260520/four_model_oof_scores/15_oof_score_wide_promo1.csv — 11,904 rows
- PUBLIC/results/15_oof_score_or_sensitivity_260520/four_model_oof_scores/15_oof_metric_summary.csv
- PUBLIC/results/15_oof_score_or_sensitivity_260520/four_model_oof_scores/15_oof_fold_distribution_check.csv
- PUBLIC/results/15_oof_score_or_sensitivity_260520/four_model_oof_scores/15_gb_lr_high_risk_overlap.csv
- PUBLIC/results/15_oof_score_or_sensitivity_260520/four_model_oof_scores/15_oof_readiness_for_shap_segmentation.csv
- PUBLIC/notebooks/15_oof_score_or_sensitivity_260520/15_four_model_oof_score_generation_260520_executed.ipynb

### OOF 결과 (형식 검수 기준)

| model_family | scope | oof_roc_auc | oof_pr_auc | suspicious_high_auc_flag | readiness |
|---|---|---|---|---|---|
| LogisticRegression | promo0 | 0.864944 | 0.951351 | OK | READY |
| LogisticRegression | promo1 | 0.839502 | 0.917268 | OK | READY |
| GradientBoosting | promo0 | 0.880476 | 0.957362 | OK | READY |
| GradientBoosting | promo1 | 0.859147 | 0.929921 | OK | READY |

### 형식 검수 vs 의미 검수

- 형식 검수: PASS (파일 생성, 행수 일치, flag 정상)
- 의미 검수: 미완료 — 다음 단계에서 사용자가 OOF 결과를 직접 검토해야 한다.
  - GB > LR 성능 차이가 예상 범위 내인지
  - promo0/promo1 gap이 허용 가능한지
  - high-risk overlap 비율이 이상하지 않은지

### 금지 확인

- Optuna 재실행: 없음
- SHAP: 없음
- segmentation: 없음
- final model selection: 없음
- raw source CSV 수정: 없음
- park.ingyeom 폴더 수정: 없음

### 다음 단계

1. 사용자가 OOF 결과 의미 검수 (ROC-AUC 범위, high-risk overlap, promo0/promo1 비교)
2. 검수 완료 후 SHAP 대상 모델 선정
3. segmentation rule 설계


## 2026-05-20 | PUBLIC 15 OOF score generation hotfix completed

이번 작업은 PUBLIC 15 OOF score generation hotfix다.

직전 15 review zip은 OOF long/wide, executed notebook, note.md, zip inventory가 누락되어 통과하지 못했다.

직전 15 overlap은 threshold 0.5/0.6/0.7 기준이어서 요구한 top10/top20/top30 기준과 달랐다.

이번 hotfix에서는 row-level OOF long/wide를 검수 가능하게 포함했다.

high-risk overlap은 top10/top20/top30 percentile 기준으로 다시 계산했다.

ROC-AUC를 primary metric으로 기록했다.

PR-AUC는 secondary metric으로 기록했다.

F1, precision, recall, brier score를 보조 지표로 추가했다.

repurchase_score_oof = P(is_repurchase=1)로 정의했다.

churn_risk_score_oof = 1 - repurchase_score_oof로 정의했다.

retention_w2_ratio, retention_w3_ratio는 feature에서 제외했다.

log_retention_w2_ratio, log_retention_w3_ratio는 feature로 사용했다.

is_churn_prevented는 approved historical context feature with caveat로 유지했다.

07~10은 여전히 pending validation이다.

이번 작업에서는 Optuna, SHAP, segmentation을 수행하지 않았다.

OOF score는 final campaign threshold가 아니다.

SHAP과 segmentation은 사용자 검수 후 별도 승인 필요 상태다.

다음 단계는 사용자가 hotfix review zip을 ChatGPT에 업로드하고, ChatGPT가 실제 ZIP을 열어 OOF 결과를 검수하는 것이다.

## 2026-05-20 | Segment, business action, demographic context, and EDA policy memo

### Purpose

이 메모는 향후 `17 segmentation`, `18 business recommendation storyline`, dashboard, 발표 자료를 만들 때 세그먼트와 비즈니스 액션의 관계를 혼동하지 않기 위해 작성한다.

현재 PUBLIC 작업은 100원딜 고객과 일반 고객을 분리하고, log-retention 기준 4개 모델 결과 및 OOF score를 중심으로 다음 단계를 준비하는 흐름이다. 이 과정에서 중요한 질문이 생겼다.

“세그먼트는 행동 기반으로 만들되, 실제 비즈니스 액션은 연령과 성별에 따라 달라져야 하는 것 아닌가?”

이 질문은 매우 중요하다. 같은 행동 세그먼트 안에 들어온 고객이라도 20대 여성과 40대 남성에게 같은 메시지, 같은 추천 콘텐츠, 같은 알림 채널, 같은 혜택 표현을 적용하는 것은 비즈니스적으로 적절하지 않을 수 있다.

따라서 앞으로의 세그먼트 설계에서는 다음 원칙을 따른다.

대표 세그먼트는 `100원딜 여부`, `OOF risk score`, `행동 변화 패턴`을 중심으로 만든다.

연령과 성별은 대표 세그먼트의 1차 분류 기준으로 바로 쓰기보다, 세그먼트 내부에서 메시지, 채널, 콘텐츠 추천, 혜택 표현을 다르게 설계하는 `action personalization layer`로 사용한다.

즉, 세그먼트는 “누가 어떤 위험 구조를 갖는가”를 설명하고, 연령/성별은 “그 고객에게 어떻게 말하고 어떤 제안을 할 것인가”를 조정하는 데 사용한다.

---

### Core distinction: segment rule vs business action

앞으로 반드시 구분해야 할 두 개념이 있다.

첫째, segment rule이다.

Segment rule은 고객을 어떤 위험 구조로 나눌 것인지를 정하는 기준이다. 이 기준은 가능하면 행동과 위험 점수 중심이어야 한다.

예를 들면 다음과 같은 질문에 답한다.

- 이 고객은 100원딜 고객인가, 일반 고객인가?
- OOF churn risk가 높은가?
- 2주차에 시청량이 줄었는가?
- 3주차에 시청이 끊겼는가?
- 가입 초기에 콘텐츠를 충분히 탐색하지 않았는가?
- 1주차에만 몰아서 보고 이후 이탈 징후를 보였는가?
- log retention이 낮아졌는가?
- 특정 장르에만 편중되어 있는가?
- 저활동 고객인가, 안정적 이용 고객인가?

둘째, business action이다.

Business action은 그 세그먼트에 어떤 메시지, 어떤 채널, 어떤 혜택, 어떤 콘텐츠 추천, 어떤 타이밍으로 개입할지를 정하는 것이다.

예를 들면 다음과 같은 질문에 답한다.

- 모바일 푸시가 적절한가, 이메일이 적절한가?
- 혜택 중심 메시지가 적절한가, 콘텐츠 추천 중심 메시지가 적절한가?
- 짧고 가벼운 톤이 적절한가, 명확하고 설명적인 톤이 적절한가?
- 최신 인기 콘텐츠를 추천할 것인가, 장르 기반 시리즈를 추천할 것인가?
- 가족/주말 시청 맥락을 제안할 것인가, 트렌드/화제성 맥락을 제안할 것인가?
- 가격 혜택을 다시 강조할 것인가, 사용 습관 형성을 강조할 것인가?

따라서 같은 대표 세그먼트에 속하더라도 business action은 달라질 수 있다.

예를 들어 대표 세그먼트가 `100원딜 고위험 + 3주차 시청량 급감형`이라고 하더라도, 그 안의 20대 여성과 40대 남성에게 동일한 메시지를 보내는 것은 적절하지 않을 수 있다. 대표 세그먼트의 위험 구조는 같지만, 설득 방식과 추천 콘텐츠는 다를 수 있기 때문이다.

---

### Why age and gender should not be ignored

연령과 성별은 세그먼트 설계에서 완전히 무시하면 안 된다.

특히 OTT 이용 행태, 콘텐츠 선호, 시청 시간대, 가격 민감도, 프로모션 반응, 메시지 수용 방식은 연령과 성별에 따라 달라질 가능성이 있다.

예를 들어 20대 고객은 모바일 푸시, 화제성 콘텐츠, 짧은 메시지, SNS에서 많이 언급되는 콘텐츠에 더 반응할 수 있다.

반면 40대 고객은 장르 선호, 가족/주말 시청 맥락, 명확한 혜택 안내, 시리즈 몰아보기 추천 등에 더 반응할 수 있다.

성별 역시 특정 콘텐츠 장르, 메시지 톤, 추천 방식, 커뮤니케이션 채널에서 차이를 보일 수 있다.

따라서 연령과 성별을 아예 제거하거나 해석에서 배제하면, 최종 비즈니스 제언이 지나치게 행동 로그 중심으로 납작해질 위험이 있다.

행동 로그는 고객이 무엇을 했는지를 보여준다. 하지만 비즈니스 액션은 고객에게 어떻게 접근할지를 설계해야 한다. 이때 연령과 성별은 액션 설계를 더 현실적으로 만드는 맥락 변수로 작동할 수 있다.

---

### Why age and gender should not be the first representative segment rule

그렇다고 연령과 성별을 대표 세그먼트의 1차 기준으로 바로 쓰는 것도 위험하다.

예를 들어 다음과 같은 세그먼트 이름은 위험하다.

- 20대 여성 이탈형
- 40대 남성 고위험군
- 여성 저충성 고객군
- 남성 이탈 임박 고객군

이런 이름은 연령/성별을 이탈 원인처럼 보이게 만들 수 있다. 또한 행동 원인보다 인구통계적 속성을 앞세우기 때문에 비즈니스적으로도 조심스럽고, 설명상으로도 방어가 어렵다.

연령/성별은 고객의 속성이지, 그 자체로 이탈 원인이라고 말할 수 없다. 특정 연령대 또는 성별에서 위험 점수가 높게 관찰되더라도, 그것이 실제 연령/성별의 인과효과인지, 콘텐츠 선호 차이인지, 결제 경로 차이인지, 시청 시간대 차이인지, 표본 구성 차이인지는 별도로 확인해야 한다.

따라서 연령과 성별은 대표 세그먼트를 만드는 첫 번째 칼이 아니라, 이미 만든 행동 기반 세그먼트가 어떤 인구통계적 맥락을 가지는지 확인하고, 그에 맞춰 액션을 조정하는 보조 레이어로 쓰는 것이 안전하다.

---

### Recommended hierarchy for segmentation and business action

향후 17 segmentation과 18 business storyline에서는 다음 계층 구조를 따른다.

1. Promo scope

가장 먼저 100원딜 여부를 나눈다.

- promo1: 100원딜 고객
- promo0: 일반 고객 비교군

100원딜은 단순 feature가 아니라 프로젝트의 주어다. 따라서 최종 발표와 비즈니스 제언의 중심은 promo1이어야 한다. promo0는 비교군이다.

2. Risk score

각 scope 내부에서 OOF score를 사용해 위험도를 본다.

- repurchase_score_oof = P(is_repurchase = 1)
- churn_risk_score_oof = 1 - repurchase_score_oof
- risk_percentile
- high_risk_top10
- high_risk_top20
- high_risk_top30

위험 점수는 고객을 바로 최종 타깃으로 확정하는 기준이 아니다. 세그먼트 설계와 high-risk overlap 검수, SHAP/feature explanation의 입력이다.

3. Behavioral flags

위험 점수 위에 행동 flag를 결합한다.

예시 행동 flag는 다음이다.

- week2_drop
- week3_drop
- week3_inactive
- only_w1
- cold_start_weak
- low_activity
- stable_usage
- log_retention_drop
- narrow_genre_preference
- short_watch_ratio_high
- content_preference_concentrated

대표 세그먼트는 우선 이 행동 flag와 risk score 조합으로 만든다.

4. Provisional segment

위험 점수와 행동 flag를 기준으로 provisional segment를 만든다.

이 단계에서는 이름을 확정하지 않는다. 기준식, row 수, 재구매율, churn risk 분포, 주요 행동 feature 분포를 먼저 확인한다.

5. Demographic and context audit

그 다음 각 provisional segment 안에서 연령/성별 분포를 확인한다.

- age_group 분포
- is_female / is_male 분포
- 성별 결측 또는 중립 값이 있다면 그 분포
- promo1 전체 대비 특정 segment의 연령/성별 과대표집 여부
- promo0와 promo1의 연령/성별 구성 차이
- segment별 콘텐츠 선호와 연령/성별의 관계
- segment별 risk score와 연령/성별의 관계

이 단계의 목적은 연령/성별로 세그먼트를 다시 만드는 것이 아니라, 행동 세그먼트의 해석과 액션 설계에 필요한 맥락을 얻는 것이다.

6. Action personalization layer

마지막으로 연령/성별, 콘텐츠 선호, 이용 맥락을 반영해 액션 variant를 만든다.

예를 들면 다음과 같다.

대표 세그먼트: 100원딜 고위험 + 3주차 시청량 급감형

액션 variant:

- 20대 여성: 최근 인기작, 짧고 즉시 볼 수 있는 콘텐츠, 모바일 푸시 중심 메시지
- 20대 남성: 장르 선호 또는 화제성 콘텐츠 중심 추천
- 30대: 시간 효율, 주말 시청, 취향 기반 큐레이션
- 40대 이상: 명확한 혜택 안내, 시리즈 몰아보기, 가족/주말 시청 맥락
- 성별/연령 정보가 불확실한 고객: 행동 기반 메시지와 콘텐츠 선호 기반 추천 중심

이처럼 대표 세그먼트는 동일하더라도, 실제 메시지와 추천 전략은 연령/성별별로 달라질 수 있다.

---

### EDA is required before using age and gender in business action

연령/성별을 액션 personalization layer로 쓰려면 반드시 EDA 근거가 필요하다.

단순히 “20대니까 이럴 것이다”, “여성은 이런 콘텐츠를 좋아할 것이다”, “40대 남성은 이런 메시지를 좋아할 것이다”라고 가정하면 안 된다. 가능하면 현재 데이터 안에서 최소한의 분포 차이를 확인해야 한다.

여기서 말하는 EDA는 인과 입증이 아니다.

정확한 목적은 다음이다.

- 같은 행동 세그먼트 안에서 연령대별 시청 행동 분포가 다른가?
- 같은 행동 세그먼트 안에서 성별별 콘텐츠 선호 분포가 다른가?
- 같은 행동 세그먼트 안에서 연령/성별별 risk score 분포가 다른가?
- 같은 행동 세그먼트 안에서 연령/성별별 actual repurchase rate가 다른가?
- promo1의 특정 행동 패턴이 특정 연령대나 성별에 과도하게 몰려 있는가?
- promo0와 비교했을 때 promo1에서만 나타나는 연령/성별 × 행동 패턴이 있는가?

이 질문에 대한 관찰 근거가 있을 때, 연령/성별별 메시지 또는 추천 전략을 나누는 것이 타당해진다.

---

### Required EDA checks for demographic action personalization

17 segmentation 또는 18 business action 단계 전에 다음 EDA를 수행하는 것이 좋다.

1. Segment-level demographic profile

각 provisional segment별로 age_group, is_female, is_male의 분포를 확인한다.

생성 후보 파일:

- 17_segment_demographic_profile.csv
- 17_segment_age_gender_distribution.csv

확인 항목:

- segment_name 또는 provisional_segment_id
- promo_scope
- row_count
- age_group별 row_count와 비율
- gender별 row_count와 비율
- promo1 전체 대비 lift 또는 ratio
- promo0 비교군 대비 차이
- 해석 주의사항

2. Segment × age_group behavior profile

각 segment 안에서 age_group별 행동 feature 분포를 확인한다.

생성 후보 파일:

- 17_segment_age_behavior_profile.csv

확인할 feature 예시:

- watch_time_w1
- watch_time_w2
- watch_time_w3
- watch_session_w1
- watch_session_w2
- watch_session_w3
- log_retention_w2_ratio
- log_retention_w3_ratio
- only_w1
- cold_start_weak
- low_activity
- week3_inactive
- short_watch_ratio
- genre preference ratio

볼 지표:

- mean
- median
- q25
- q75
- zero ratio
- high-risk ratio
- actual repurchase rate
- churn risk 평균
- SMD 또는 간단한 standardized difference 가능 시 포함

3. Segment × gender behavior profile

각 segment 안에서 gender별 행동 feature 분포를 확인한다.

생성 후보 파일:

- 17_segment_gender_behavior_profile.csv

확인할 내용은 age_group profile과 동일하다.

4. Segment × demographic action matrix

각 segment별로 연령/성별 action variant를 정리한다.

생성 후보 파일:

- 18_segment_demographic_action_matrix.csv

필수 컬럼 후보:

- promo_scope
- provisional_segment_id
- segment_rule_summary
- demographic_modifier
- observed_demographic_pattern
- observed_behavior_difference
- recommended_message_direction
- recommended_channel
- recommended_content_strategy
- risk_of_overinterpretation
- evidence_file
- final_status

이 파일은 segmentation 산출물이 아니라 business action 설계 산출물이다.

5. Demographic caveat and fairness/proxy audit

연령/성별을 비즈니스 액션에 사용할 때 과잉 해석을 막기 위한 caveat를 기록한다.

생성 후보 파일:

- 17_demographic_proxy_caveat_audit.csv
- 18_demographic_action_caveat.md

확인할 내용:

- 연령/성별이 직접 원인으로 해석되고 있지 않은가
- 특정 집단을 낙인찍는 표현이 없는가
- 세그먼트 이름에 인구통계가 과도하게 들어가 있지 않은가
- 행동 근거 없이 연령/성별만으로 메시지를 나누고 있지 않은가
- 표본 수가 너무 작은 subgroup에 과한 해석을 하고 있지 않은가
- age_group 또는 gender 값의 데이터 품질 caveat가 있는가

---

### How to decide whether demographic action variants are justified

연령/성별별 액션 variant는 항상 필요한 것이 아니다. EDA 결과에 따라 달라져야 한다.

다음 조건을 만족하면 demographic action variant를 고려할 수 있다.

- 특정 segment 안에서 age_group별 행동 feature 분포가 뚜렷하게 다르다.
- 특정 segment 안에서 gender별 콘텐츠 선호 또는 시청 패턴이 뚜렷하게 다르다.
- 특정 segment 안에서 age/gender별 actual repurchase rate 또는 churn_risk score가 의미 있게 다르다.
- subgroup row 수가 너무 작지 않다.
- 차이가 단순 노이즈나 극단값 때문이 아니다.
- 메시지, 채널, 콘텐츠 추천 방향이 실제로 달라질 수 있다.
- 해석이 인과가 아니라 관찰 기반 personalization이라는 점을 명확히 기록할 수 있다.

반대로 다음 조건이면 demographic action variant를 만들지 않는 것이 낫다.

- age/gender별 분포 차이가 거의 없다.
- subgroup row 수가 너무 작다.
- 차이는 있지만 business action이 달라질 만큼 명확하지 않다.
- 연령/성별보다 행동 flag가 훨씬 강한 설명력을 가진다.
- 연령/성별을 쓰면 낙인 또는 과잉 일반화 위험이 크다.
- 현재 데이터에서 age/gender의 품질 caveat가 크다.

이 경우에는 대표 세그먼트의 행동 기반 액션을 유지하고, demographic은 profile audit 결과로만 보고한다.

---

### Example structure for future 17 and 18

17 segmentation의 기본 구조는 다음이어야 한다.

- promo1 중심
- promo0 비교군
- OOF risk score 기반
- 행동 flag 기반
- segment name은 provisional
- age/gender는 segment rule이 아니라 profile audit
- payment/auth/demographic proxy는 대표 rule에 직접 사용하지 않음
- final segment는 사용자 승인 전까지 provisional

18 business action의 기본 구조는 다음이어야 한다.

- 100원딜 고객 세그먼트별 action priority
- 같은 세그먼트 안에서 연령/성별에 따른 action variant
- 콘텐츠 선호에 따른 recommendation variant
- 채널 또는 메시지 톤 차이
- causal claim 금지
- A/B test 또는 후속 실험 제안
- 실제 캠페인 threshold 확정 금지

예를 들어 다음 구조가 가능하다.

대표 세그먼트:

100원딜 고위험 + 3주차 시청량 급감형

행동 근거:

- 3주차 watch time 감소
- log_retention_w3_ratio 하락
- churn_risk_score_oof 상위 20%
- GB/LR high-risk overlap 여부 확인

demographic audit:

- 20대 비중이 promo1 전체 대비 높은가?
- 40대 이상 비중이 특정 subgroup에서 높은가?
- 성별별 콘텐츠 선호가 다른가?
- 각 subgroup의 actual repurchase rate가 다른가?

action variant:

- 20대 중심 subgroup: 짧고 즉시 볼 수 있는 인기 콘텐츠, 모바일 푸시, 트렌드 기반 메시지
- 30대 subgroup: 주말/퇴근 후 시청 맥락, 취향 기반 시리즈 추천
- 40대 이상 subgroup: 명확한 혜택 안내, 장르 기반 추천, 가족/주말 시청 맥락
- gender별 콘텐츠 선호 차이가 확인된 경우: 장르/콘텐츠 추천 variant 조정
- demographic 차이가 확인되지 않은 경우: 동일 행동 기반 메시지 유지

이 구조는 연령/성별을 무시하지 않으면서도, 연령/성별을 이탈 원인처럼 과장하지 않는 방식이다.

---

### Safe wording

다음 표현은 허용한다.

- “세그먼트는 100원딜 여부, OOF 위험 점수, 행동 변화 패턴을 기준으로 설계했다.”
- “연령과 성별은 대표 세그먼트의 1차 기준이 아니라, 세그먼트별 메시지와 콘텐츠 추천 전략을 조정하는 personalization layer로 사용했다.”
- “연령/성별별 액션 variant는 EDA에서 실제 분포 차이가 관찰되는 경우에만 제안한다.”
- “연령/성별은 이탈의 원인이 아니라, 행동 세그먼트를 해석하고 커뮤니케이션 전략을 조정하기 위한 맥락 변수다.”
- “같은 3주차 시청량 감소 세그먼트라도 연령대와 성별에 따라 추천 콘텐츠와 메시지 톤은 달라질 수 있다.”
- “이 제안은 관찰 기반 personalization이며, 실제 효과는 A/B test 또는 캠페인 실험으로 검증해야 한다.”

---

### Unsafe wording

다음 표현은 금지한다.

- “20대 여성은 이탈한다.”
- “40대 남성은 재구매하지 않는다.”
- “여성 고객은 저충성이다.”
- “남성 고객은 특정 장르 때문에 이탈한다.”
- “연령이 이탈의 원인이다.”
- “성별이 재구매 실패를 유발한다.”
- “이 세그먼트는 40대 남성형이다.”
- “연령/성별만 보고 메시지를 나누면 된다.”
- “EDA 없이 연령/성별별 전략을 제안한다.”
- “SHAP이나 모델 결과가 연령/성별의 인과효과를 증명했다.”

---

### Current decision

현재 결정은 다음과 같다.

- 100원딜 여부는 최상위 분석 scope다.
- OOF risk score와 행동 flag는 대표 세그먼트의 1차 기준이다.
- 연령/성별은 대표 세그먼트의 1차 기준이 아니라 세그먼트 해석 검수와 business action personalization layer로 사용한다.
- 단, 연령/성별별 행동 분포 차이가 EDA에서 충분히 확인되면, 대표 세그먼트 아래의 action variant 또는 sub-message strategy로 반영할 수 있다.
- 연령/성별을 최종 비즈니스 액션에 사용하려면 반드시 EDA 근거와 caveat를 함께 제시한다.
- 연령/성별을 이탈 원인처럼 말하지 않는다.
- 17 segmentation과 18 business recommendation 단계에서 이 원칙을 반드시 반영한다.

---

### Next implementation requirement

향후 17 또는 18 단계 goal에는 반드시 다음 요구사항을 포함한다.

- segment별 age_group 분포를 산출한다.
- segment별 gender 분포를 산출한다.
- segment별 age_group × 행동 feature 분포를 산출한다.
- segment별 gender × 행동 feature 분포를 산출한다.
- segment별 age/gender에 따른 actual repurchase rate와 churn_risk_score 분포를 확인한다.
- 연령/성별 차이가 충분히 관찰되는 경우에만 action variant를 제안한다.
- 연령/성별 차이가 약하면 행동 기반 액션을 유지한다.
- 모든 demographic action은 provisional로 둔다.
- 최종 business recommendation에는 demographic caveat를 포함한다.
- segment name에는 연령/성별을 직접 넣지 않는 것을 기본값으로 둔다.
- 단, 사용자가 명시적으로 승인하고 EDA 근거가 충분한 경우에만 demographic-aware subsegment 또는 action variant를 제안한다.

이 메모는 이후 17 segmentation, 18 business storyline, dashboard, 발표 자료 작성 시 반드시 참조한다.

## 2026-05-20 | PUBLIC 16 four-model SHAP candidate interpretation completed

이번 작업은 PUBLIC 16 SHAP / model explanation 단계다.

15 OOF hotfix 결과를 입력으로 삼았다.

4개 모델 조합을 해석 대상으로 삼았다.

조합은 LogisticRegression promo0, LogisticRegression promo1, GradientBoosting promo0, GradientBoosting promo1이다.

SHAP은 인과가 아니라 model explanation이다.

GradientBoosting에는 SHAP global/family importance를 생성했다.

LogisticRegression에는 가능하면 SHAP을 생성하고, 불가능하거나 부적절하면 coefficient summary를 생성했다.

promo1은 100원딜 고객 중심 scope이고, promo0는 비교군이다.

promo1 vs promo0 feature/family 차이를 비교했다.

연령/성별은 대표 세그먼트의 1차 기준이 아니라 action personalization layer와 profile audit 변수로 기록했다.

demographic action variant는 EDA에서 실제 분포 차이가 확인될 때만 제안한다.

is_churn_prevented는 approved historical context feature with caveat로 유지했다.

07~10은 여전히 pending validation이다.

이번 작업에서는 Optuna, OOF 재생성, segmentation, final model selection, campaign threshold 확정을 수행하지 않았다.

segmentation은 사용자 검수 후 별도 goal로 진행한다.

SHAP 계산 fallback은 핵심 산출물 기준으로 발생하지 않았다.



## 2026-05-20 | PUBLIC 16b feature family mapping hotfix completed

이번 작업은 16 SHAP 산출물의 feature family mapping hotfix다.

모델 재실행, SHAP 재계산, OOF 재생성, Optuna, segmentation은 수행하지 않았다.

기존 SHAP 값은 유지하고, feature family mapping만 보정했다.

기존 technical_or_unknown은 provisional fallback label이며, feature가 쓸모없다는 뜻이 아니다.

technical_or_unknown에 남아 있던 주요 feature를 registration_timing_context, usage_concentration, inactivity_recency, week_specific_usage_pattern, genre_preference 등으로 재분류했다.

recency, max_inactive_gap_days는 inactivity_recency로 재분류했다.

is_only_w1, is_only_w2, is_only_w3는 week_specific_usage_pattern으로 재분류했다.

active_ratio, max_day_share, day_count_over_3times는 usage_concentration으로 재분류했다.

reg_hour_*, reg_is_weekend는 registration_timing_context로 재분류했다.

historical_war_ratio, sf_fantasy_ratio, other_ratio는 genre_preference로 재분류했다.

hotfix family 기준으로 family importance와 promo1 vs promo0 family comparison을 다시 계산했다.

17 segmentation에서는 원래 technical_or_unknown bucket이 아니라 16b hotfix family mapping을 사용해야 한다.

연령/성별은 대표 세그먼트의 1차 기준이 아니라 profile audit과 action personalization layer로 사용한다.

demographic action variant는 EDA에서 실제 분포 차이가 확인될 때만 제안한다.

is_churn_prevented는 approved historical context feature with caveat로 유지한다.

07~10은 여전히 pending validation이다.

다음 단계는 사용자가 16b review zip을 검수한 뒤 17 segmentation으로 갈지, demographic EDA를 먼저 할지 결정하는 것이다.

---

## 2026-05-20 | PUBLIC 16b feature family mapping hotfix accepted after review

16b feature family mapping hotfix review package를 검수한 결과, 핵심 mapping 보정은 통과 가능하다고 판단했다.

기존 technical_or_unknown 16개 feature가 모두 재분류되었다.

technical_or_unknown 잔여 feature는 0개다.

recency와 max_inactive_gap_days는 inactivity_recency로 재분류되었다.

is_only_w1, is_only_w2, is_only_w3는 week_specific_usage_pattern으로 재분류되었다.

active_ratio, max_day_share, day_count_over_3times는 usage_concentration으로 재분류되었다.

reg_hour_*와 reg_is_weekend는 registration_timing_context로 재분류되었다.

historical_war_ratio, sf_fantasy_ratio, other_ratio는 genre_preference로 재분류되었다.

기존 SHAP 값은 재계산하지 않았고, family mapping과 family-level 집계만 보정했다.

17 segmentation에서는 원래 technical_or_unknown bucket이 아니라 16b hotfix family mapping을 사용해야 한다.

16b_source_fingerprint_before_after.csv에서 자기참조성 있는 handoff/fingerprint/zip_inventory 파일 2개가 changed_needs_review로 남았지만, 이는 패키징 과정의 metadata self-reference 문제로 해석한다.

원천 데이터, 기존 16 core SHAP 산출물, 16b 핵심 output이 변경된 문제로 보지 않는다.

다음 작업부터 source fingerprint와 zip inventory의 self-reference limitation을 명시적으로 기록해야 한다.

연령/성별은 대표 세그먼트 규칙이 아니라 profile audit 및 action personalization layer로 사용한다.

demographic action variant는 EDA 근거가 있을 때만 제안한다.

is_churn_prevented는 approved historical context feature with caveat로 유지한다.

07~10은 여전히 pending validation이다.

다음 단계는 17 segmentation 설계 또는 demographic EDA 선행 여부를 사용자가 결정하는 것이다.


## 2026-05-20 | PUBLIC 17 promo-scope OOF behavior segmentation design completed

이번 작업은 PUBLIC 17 segmentation design 단계다.

15 OOF hotfix, 16 SHAP, 16b feature family mapping hotfix를 입력으로 사용했다.

promo1은 100원딜 고객 중심 scope이며, promo0는 비교군이다.

세그먼트는 OOF risk score와 행동 flag를 결합해 provisional로 설계했다.

16b hotfix family mapping을 사용했고, 기존 technical_or_unknown bucket은 사용하지 않았다.

연령/성별은 대표 세그먼트의 1차 기준이 아니라 demographic profile 및 action personalization layer로 사용했다.

demographic action variant는 EDA에서 분포 차이가 확인되는 경우에만 제안한다.

segment name은 final이 아니며 사용자 승인 전까지 provisional이다.

OOF score는 final campaign threshold가 아니다.

SHAP은 인과가 아니라 model explanation이다.

is_churn_prevented는 approved historical context feature with caveat로 유지했다.

07~10은 여전히 pending validation이다.

이번 작업에서는 모델 재실행, Optuna, SHAP 재계산, OOF 재생성, campaign threshold 확정을 수행하지 않았다.

`17_segment_rationale_memo_for_executives.md`를 작성해 세그먼트를 왜 이렇게 나누었는지 데이터와 비즈니스 근거를 길게 설명했다.

다음 단계는 사용자가 17 review zip을 검수한 뒤, 18 business storyline 또는 segment hotfix 여부를 결정하는 것이다.


## 2026-05-20 | PUBLIC 17 segmentation semantic hotfix completed

이번 작업은 17 segmentation semantic hotfix다.

기존 17 산출물은 row count, score direction, assignment rule은 맞았지만, content_preference_signal이 지나치게 broad하게 생성되어 segment-discriminating signal로 쓰기 위험했다.

content_preference_signal은 representative rule에서 제거 또는 강등하고, broad content-context marker 또는 action personalization 참고 변수로만 사용하도록 보정했다.

genre/content narrow 계열 segment는 genre_preference_clear 중심으로 재해석했다.

other_needs_review 비중이 큰 점을 숨기지 않고 caveat로 기록했다.

representative segment assignment와 summary를 hotfix rule 기준으로 다시 계산했다.

executive rationale memo를 임원 설득용으로 대폭 확장했다.

연령/성별은 대표 segment rule이 아니라 profile audit 및 action personalization layer로 유지했다.

SHAP은 인과가 아니라 model explanation이다.

OOF score는 final campaign threshold가 아니다.

segment label은 provisional이다.

07~10은 여전히 pending validation이다.

이번 작업에서는 모델 재실행, OOF 재생성, SHAP 재계산, Optuna, final campaign targeting을 수행하지 않았다.

다음 단계는 사용자가 17 hotfix review zip을 검수한 뒤 18 business storyline으로 갈지, 추가 segment 보정을 할지 결정하는 것이다.

## 2026-05-20 | PUBLIC 17 segmentation quality hotfix completed

- 이번 작업은 17 segmentation quality hotfix다.
- 기존 17 산출물은 row count, score direction, assignment rule 측면에서는 맞았지만, content_preference_signal broad flag, small segment, other_needs_review 비중 문제 때문에 의미 검수 hotfix가 필요했다.
- content_preference_signal은 representative rule에서 강등하고, broad content-context marker 또는 action cue로만 둔다.
- 대표 세그먼트는 최소 규모 기준을 적용한다.
- n < 300인 small segment는 기본적으로 대표 segment에서 강등하고, sub-signal/profile note/action cue로 보존한다.
- other_needs_review는 단순 중위험군이 아니라 기존 rule로 설명되지 않은 잔여군으로 정의하고, risk band와 행동 flag 기준으로 decomposition했다.
- promo1과 promo0의 같은 행동 패턴을 비교해, 공통 위험 신호인지 100원딜 고객에서 더 강하게 나타나는 신호인지 구분했다.
- revised representative segment proposal과 assignment simulation을 만들었지만, user approval 전까지 final assignment가 아니다.
- 연령/성별은 대표 rule이 아니라 action personalization layer다.
- demographic action은 EDA 근거가 있을 때만 제안한다.
- OOF score는 campaign threshold가 아니다.
- SHAP은 인과가 아니다.
- 07~10은 여전히 pending validation이다.
- 다음 단계는 사용자가 quality hotfix review zip을 검수한 뒤, revised segment proposal을 승인할지, 추가 hotfix를 할지, 18 business storyline으로 갈지 결정하는 것이다.

## 2026-05-20 | PUBLIC 17 demographic action layer hotfix completed

- 이번 작업은 17 quality hotfix 이후 demographic/action personalization layer를 복구하기 위한 hotfix다.
- 기존 revised segment assignment는 변경하지 않았다.
- age_group profile을 다시 생성했다.
- is_female/is_male 기준 gender derivation을 다시 점검했다.
- segment별 age_group behavior profile을 생성했다.
- segment별 gender behavior profile을 생성했다.
- action personalization matrix를 demographic hotfix 기준으로 다시 만들었다.
- 연령/성별은 대표 segment rule의 1차 기준이 아니라 profile audit 및 action personalization layer로만 사용한다.
- demographic action variant는 EDA에서 실제 분포 차이와 행동 차이가 확인될 때만 제안한다.
- 연령/성별을 이탈 원인으로 해석하지 않는다.
- 18 business storyline은 사용자 검수 후 진행한다.
- 이번 작업에서는 대표 segment 재배정, 모델 재실행, OOF 재생성, SHAP 재계산, Optuna, campaign threshold 확정을 수행하지 않았다.
- 07~10은 여전히 pending validation이다.

## 2026-05-20 | PUBLIC 18 business storyline and segment visual guide v2 completed

- 이번 작업은 18 business recommendation storyline 및 segment visual guide v2 작성 단계다.
- 입력으로 15 OOF hotfix, 16 SHAP, 16b family mapping hotfix, 17 quality hotfix, 17 demographic/action layer hotfix를 사용했다.
- promo1은 100원딜 고객 중심 scope이고, promo0는 비교군이다.
- revised 5-family segment proposal을 18의 기본 뼈대로 사용했다.
- legacy segment_visual_guide.html은 레이아웃과 설명 방식만 참고했고, legacy 수치와 legacy rule은 사용하지 않았다.
- 세그먼트는 행동 기반으로 설계했고, 연령·성별은 profile audit 및 action personalization layer로 사용했다.
- demographic action variant는 EDA에서 분포 차이와 행동 차이가 관찰되는 경우에만 business hypothesis로 제안했다.
- OOF score는 final campaign threshold가 아니다.
- SHAP은 인과가 아니라 model explanation이다.
- 100원딜이 이탈을 유발했다고 쓰지 않는다.
- segment label은 provisional이다.
- 07~10은 여전히 pending validation이다.
- 이번 작업에서는 모델 재실행, OOF 재생성, SHAP 재계산, segmentation 재배정, campaign threshold 확정을 수행하지 않았다.
- 다음 단계는 사용자가 18 review zip을 검수한 뒤, 발표용 HTML/대시보드/스토리라인을 최종 수정하는 것이다.

---

## 2026-05-20 | PUBLIC 18 Business Storyline Polish Hotfix

### 수행 내용

기존 `18_business_recommendation_storyline_260520` 산출물의 품질 문제를 발견하고, 발표 수준으로 정제하는 hotfix를 수행했다. 모델 재실행, OOF 재생성, SHAP 재계산, segment assignment 변경은 수행하지 않았다.

### 발견된 주요 문제 (audit 결과)

1. demographic action candidate 60개 all `include_in_storyline=yes` — 과도하게 낙관적; 동일 age_group 중복 등장
2. promo0 action matrix에서 `final_status=provisional_business_candidate` — promo0는 comparison_reference여야 함
3. `genre_or_content_action_cue` (n=11 promo1, n=5 promo0)가 main storyline에 포함 — n<300 기준 미달
4. `mid_risk_retention_watchlist`가 storyline comparison에서 누락 (n=1,309; delta +18.4%p로 최대)
5. HTML visual guide에 flag dictionary, segment KPI cards, safe/unsafe wording, demographic layer 없음

### 생성 산출물 (모두 신규 파일, 기존 파일 수정 없음)

**출력 디렉터리:** `PUBLIC/reports/business/18_business_recommendation_storyline_hotfix_260520/`

| 파일 | 설명 |
|---|---|
| 18_existing_storyline_quality_audit.csv | 14개 audit 항목 (blocking 1, major 8, minor 3, pass 2) |
| 18_promo1_main_business_action_matrix_hotfix.csv | promo1 5개 segment action matrix |
| 18_promo0_comparison_reference_hotfix.csv | promo0 비교 기준 5행 (action 없음) |
| 18_demographic_action_candidate_shortlist_hotfix.csv | 60행 → 16행 shortlist (promo1 yes:8, limited:2; comparison_only:6) |
| 18_storyline_comparison_clean_hotfix.csv | genre demoted + mid_risk 추가 (6행) |
| 18_segment_visual_guide_v2_polished.html | 종합 HTML (flag dict, segment cards, safe/unsafe, demo layer) |
| 18_business_storyline_memo_hotfix.md | 10,000자+ 한국어 상세 메모 |
| 18_presentation_talking_points_hotfix.md | 8개 Q&A + 방어 문장 + 금지 표현 |
| 18_dashboard_handoff_datamart_hotfix.csv | 10행 (promo1×5 + promo0×5) |
| 18_safe_unsafe_wording_hotfix.csv | 14개 wording 가이드 |
| README.md | hotfix 전체 요약 |

**Handoff 디렉터리:** `PUBLIC/handoff/PUBLIC_18_business_storyline_polish_hotfix_260520/`

- 18_hotfix_input_validation.csv (30개 입력 파일 전체 PASS)
- final_checks, source_fingerprint, zip_inventory, README

### 핵심 수치 확인 (변경 없음)

- promo1 high_risk_week3: n=1893, churn=0.7427, gb_risk=0.7399
- promo1 high_risk_activation: n=370, churn=0.7838, gb_risk=0.7317
- promo1 mid_risk_watchlist: n=1309, churn=0.6012, gb_risk=0.5276
- promo1 stable: n=1999, churn=0.1196, gb_risk=0.1341
- promo1 other_residual: n=6333, churn=0.1808, gb_risk=0.1941

### 주의사항

- 모든 segment는 provisional이다
- OOF score는 campaign threshold가 아니다
- SHAP은 인과가 아니다
- demographic은 personalization layer이며 이탈 원인이 아니다
- 07~10 validation은 여전히 pending이다
- other residual (53.2%)은 중위험군이 아님을 반드시 명시해야 한다
- genre_or_content_action_cue (n=11)는 main storyline에서 강등 완료

### 다음 단계

1. 팀 검토: segment label, demographic shortlist, safe/unsafe wording
2. Visual guide 검토 및 발표 자료 적용
3. 07~10 validation 진행
4. other_needs_review_residual 내부 decomposition 분석 (별도 단계)
5. threshold 설정 및 A/B test 설계 (별도 단계)