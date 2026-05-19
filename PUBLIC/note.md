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
