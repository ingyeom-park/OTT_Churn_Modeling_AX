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
