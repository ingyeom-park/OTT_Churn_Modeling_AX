# 프로젝트 진행 계획서 v0.1

아래 문서는 지금 대화가 끊기거나, 새로운 ChatGPT 대화 또는 새로운 Codex 세션에서 이어받아도 현재 상황을 이해할 수 있도록 만든 `작업 계획서`입니다.

이 문서는 “새 분석을 다시 돌리는 계획”이 아닙니다. 지금부터의 핵심은 이미 존재하는 `park.ingyeom` 파이프라인과 `FINAL/final_note.md`를 기준으로, 발표와 대시보드에 쓸 최종 해석 구조를 정리하는 것입니다.

---

# 0. 현재 한 줄 결론

현재 프로젝트는 `park.ingyeom` 파이프라인을 최종 계산 기준으로 유지한다. `PUBLIC`은 최종 파이프라인이 아니라, 100원딜 중심 해석과 비즈니스 스토리라인을 실험한 reference branch로 둔다. 최종 세그먼트 rule과 assignment는 바꾸지 않고, 발표용 label, 세그먼트별 action tier, 100원딜 해석, 인구통계 기반 메시지 차별화 layer를 보강한다.

이 결론은 `final_note.md`에 이미 상당 부분 반영되어 있다. `final_note.md`는 최종 score source를 `LightGBM / expanded_no_payment_device / overall_with_promotion / OOF churn_risk`로 두고, 17x 대표 segment rule과 assignment는 수정하지 않으며, 발표용 label과 business action matrix, demographic personalization layer만 보정한다고 정리한다. 

---

# 1. 프로젝트의 최종 주제

공식 주제는 다음처럼 정리한다.

> XAI 기반 OTT 신규 고객 이탈 요인 분석 및 리텐션 전략

설명 문장은 다음처럼 둔다.

> 프로모션으로 유입되는 OTT 고객들의 이탈 행동 패턴 및 요인을 분석하여, 맞춤형 리텐션 전략을 포함한 비즈니스 제언을 도출한다.

다만 최종 문서에서 이 프로젝트를 `100원딜 고객만 분석한 프로젝트`처럼 너무 좁게 쓰면 안 된다. `park.ingyeom` 최종 파이프라인은 전체 23,079 row를 기준으로 하고, 그 안에서 100원딜 고객과 비100원딜 고객을 함께 해석하는 구조다. 따라서 최종 표현은 이렇게 잡는다.

> 이 프로젝트는 OTT 신규 고객의 재구매 실패 위험을 XAI 기반으로 분석하고, 특히 100원딜 프로모션으로 유입된 고객의 day0~20 행동 신호를 중심으로 리텐션 개입 전략을 도출하는 프로젝트다.

여기서 중요한 제한은 다음이다.

> 100원딜이 이탈을 유발했다는 인과 분석이 아니다. 100원딜이라는 초저가 유입 맥락에서 어떤 행동 신호가 재구매 실패와 함께 관찰되는지를 설명하는 분석이다.

이 제한은 `final_note.md`의 최상단 취지와도 맞는다. 

---

# 2. 현재 최종 기준

현재 최종 기준은 `park.ingyeom`이다.

`park.ingyeom`을 기준으로 두는 이유는 다음과 같다.

`park.ingyeom`은 06x expanded dataset 23,079행과 15x OOF score를 row_id 기준으로 맞춘 뒤 17x representative segment를 만들었다. 17x score source는 `feature_set_variant == expanded_no_payment_device`, `dataset_scope == overall_with_promotion`, `model_name == LightGBM`, row_count 23,079로 기록되어 있다. 또한 이 선택은 16x payment-removed SHAP candidate plan과 기준을 맞추기 위한 것이다. 

따라서 최종 계산 기준은 다음이다.

> 데이터 기준: `park.ingyeom` 06x expanded dataset, 23,079 rows
> score 기준: 17x에서 선택한 LightGBM OOF churn_risk
> feature 기준: expanded_no_payment_device
> scope 기준: overall_with_promotion
> 세그먼트 기준: park 17x representative segment rule과 assignment
> 해석 기준: 16x payment-removed SHAP과 17x segment evidence

중요한 점은 이것이다.

> 이 기준은 최종 운영 모델을 확정했다는 뜻이 아니다.
> 발표와 세그먼트 해석을 위해 현재 가장 계보가 정합적인 score source를 선택했다는 뜻이다.

---

# 3. PUBLIC의 지위

`PUBLIC`은 final pipeline이 아니다.

`PUBLIC`은 100원딜 중심 promo-scope segmentation과 business storyline을 시도한 reference branch다. `final_note.md`도 PUBLIC의 numeric score, segment assignment, model decision은 FINAL 기준으로 가져오지 않는다고 정리한다. 대신 PUBLIC에서 가져올 수 있는 것은 narrative 구조, visual guide 구성, safe wording, action matrix 표현 방식이라고 기록되어 있다. 

즉, PUBLIC의 최종 지위는 다음이다.

> PUBLIC = 100원딜 중심 해석을 시도한 우회 검증 branch
> PUBLIC numeric score = 최종 기준으로 사용하지 않음
> PUBLIC segment assignment = 최종 기준으로 사용하지 않음
> PUBLIC storyline / visual guide / safe wording / action matrix 형식 = 참고 가능

PUBLIC이 완전히 헛수고였다고 기록하면 안 된다. 더 정확한 표현은 다음이다.

> PUBLIC은 최종 파이프라인으로 채택하지 않지만, 100원딜 중심 해석이 왜 필요한지, 그리고 promo-scope segmentation을 직접 final 기준으로 쓰는 것이 왜 위험한지를 확인한 reference branch다.

PUBLIC은 최종 숫자 기준이 아니라, 최종 발표의 문제의식과 문장 구조를 보강하는 데 사용한다.

---

# 4. 지금부터 절대 하지 말아야 할 것

현재 단계에서 다시 하면 안 되는 작업은 다음이다.

모델을 다시 돌리지 않는다.

SHAP을 다시 계산하지 않는다.

Optuna를 다시 실행하지 않는다.

17x segmentation rule을 다시 만들지 않는다.

17x representative segment assignment를 다시 배정하지 않는다.

PUBLIC의 score나 segment를 park 기준과 섞지 않는다.

`general_observation`과 `content_preference_target_candidate`를 임의로 제거하지 않는다.

`is_repurchase`를 사용해 새 세그먼트 rule을 만들지 않는다.

age/gender/is_user_verified/payment_device를 대표 세그먼트 rule에 넣지 않는다.

100원딜을 이탈 원인처럼 말하지 않는다.

SHAP을 원인처럼 말하지 않는다.

세그먼트를 최종 캠페인 타겟이라고 말하지 않는다.

현재는 새 분석 파이프라인을 여는 시점이 아니다. 지금은 최종 해석, 발표 구조, 대시보드 설명, action matrix를 정리하는 단계다.

---

# 5. 현재 세그먼트 구조

`final_note.md` 기준 17x segment는 다음 7개다. 모든 segment name은 provisional label이고, assignment와 rule은 그대로 유지한다. 

| 순위 | segment id                           |  rows | share | churn rate | mean churn_risk | promo1 share |
| -: | ------------------------------------ | ----: | ----: | ---------: | --------------: | -----------: |
|  1 | high_risk_week3_inactive_or_drop     | 3,793 | 16.4% |      73.2% |           0.733 |        59.0% |
|  2 | high_risk_only_w1_or_cold_start_weak |   265 |  1.1% |      71.7% |           0.698 |        70.6% |
|  3 | high_risk_low_activity               |   511 |  2.2% |      81.4% |           0.765 |        60.9% |
|  4 | medium_risk_retention_decay          | 3,195 | 13.8% |      38.8% |           0.358 |        54.6% |
|  5 | content_preference_target_candidate  | 6,195 | 26.8% |      10.1% |           0.095 |        48.5% |
|  6 | stable_retained_user                 | 1,224 |  5.3% |       1.1% |           0.017 |        34.2% |
|  7 | general_observation                  | 7,896 | 34.2% |      15.9% |           0.169 |        50.6% |

이 표에서 중요한 것은 `1~4순위`와 `5~7순위`의 역할이 다르다는 점이다.

1~3순위는 고위험군이다.

4순위는 중간위험 관찰군이다.

5~6순위는 재구매율이 높은 편이므로 이탈 방어의 1차 타겟이 아니다. 대신 정가 전환 강화, 이용 가치 강화, 콘텐츠 큐레이션 관점에서 쓴다.

7순위는 명확한 rule에 걸리지 않은 residual 성격이 강하므로, 핵심 타겟이 아니라 monitoring group으로 둔다.

---

# 6. 세그먼트 계층 재정리

최종 발표와 대시보드에서는 7개 세그먼트를 단순 나열하지 않는다.

다음 4개 action tier로 묶는다.

# 6.1 즉시 개입 우선군

해당 segment:

`high_risk_week3_inactive_or_drop`

`high_risk_low_activity`

`high_risk_only_w1_or_cold_start_weak`

이들은 재구매율이 낮고 평균 churn_risk가 높다. 본 프로젝트가 이탈 방지와 리텐션 전략을 목적으로 하므로, 이 세 집단이 1차 intervention priority다.

발표용 해석:

> 100원딜 고객 중에서도 3주차 사용이 꺾이거나, 초기 활성화가 약하거나, 전반적 활동량이 낮은 고객은 정가 전환 실패 위험이 높게 관찰된다. 이들은 리텐션 개입의 1차 우선순위 후보군이다.

주의:

`후보군`이라고 말한다. `최종 캠페인 타겟`이라고 말하지 않는다.

# 6.2 관찰 강화군

해당 segment:

`medium_risk_retention_decay`

이 집단은 고위험군만큼 위험하지는 않지만, retention decay가 관찰되는 중간위험군이다.

발표용 해석:

> 아직 고위험군으로 확정하기는 어렵지만, 사용량 감소 신호가 나타나는 고객군이므로 watchlist 또는 관찰 강화군으로 관리한다.

# 6.3 정가 전환 강화군

해당 segment:

`content_preference_target_candidate`

`stable_retained_user`

이들은 이탈 방어의 1차 타겟이 아니다. 특히 `content_preference_target_candidate`는 churn rate가 낮고 mean churn_risk도 낮기 때문에 churn target candidate라고 말하면 과하다. `final_note.md`도 이 집단을 churn target candidate로 말하는 것은 과하며, 이름 약화와 action layer 강등을 권장한다. 

발표용 해석:

> 이 집단은 이탈 방어보다 정가 전환 강화와 이용 가치 상기 전략에 적합하다. 콘텐츠 큐레이션, 취향 기반 추천, 다음 결제 전 혜택 상기 메시지를 중심으로 접근한다.

# 6.4 모니터링 / 추가분해 후보군

해당 segment:

`general_observation`

이 집단은 7,896행, 전체 34.2%로 크다. 기술적으로는 default residual이지만, 내부에 low activity, cold-start weak, retention decay, week3 inactive 신호가 일부 남아 있다고 기록되어 있다. 따라서 분석에서 제외하지 않는다. 다만 발표 핵심 세그먼트로 세우지 않고 monitoring group으로 낮춘다. 

발표용 해석:

> 명확한 대표 rule에는 걸리지 않았지만 규모가 크고 일부 행동 신호가 남아 있으므로, 즉시 타겟이 아니라 후속 모니터링과 추가 세분화 후보군으로 관리한다.

---

# 7. general_observation 처리 원칙

`general_observation`은 버리지 않는다.

하지만 핵심 이탈 방어 세그먼트로 말하지 않는다.

이 집단은 다음처럼 설명한다.

> `general_observation`은 명확한 대표 rule에 걸리지 않은 residual이다. 그러나 전체의 34.2%를 차지하고 내부에 low activity, cold-start weak, retention decay, week3 inactive 신호가 일부 존재하므로 분석에서 제외하지 않는다. 대시보드에서는 monitoring group으로 유지하고, 후속 decomposition 대상으로 관리한다.

금지 표현:

`일반 고객군이다.`

`분석에서 제외한다.`

`문제가 없는 고객이다.`

`별 특징이 없다.`

허용 표현:

`추가 관찰 필요 잔여군`

`모니터링 / 추가분해 후보군`

`명확한 rule에 걸리지 않은 residual`

`후속 세분화 후보`

---

# 8. content_preference_target_candidate 처리 원칙

`content_preference_target_candidate`도 버리지 않는다.

하지만 이탈 방어 타겟이라고 말하지 않는다.

`final_note.md`에 따르면 이 집단은 6,195행, 전체의 26.8%이며, segment churn rate는 10.1%로 전체 churn rate 28.3%보다 낮다. 내부에서 `flag_genre_focused`는 19.5%, `flag_new_movie_oriented`는 41.4%, `flag_old_movie_oriented`는 50.2%다. 따라서 churn target candidate라고 말하는 것은 과하며, 발표명은 `콘텐츠 큐레이션 반응 후보군`이 안전하다고 정리되어 있다. 

최종 해석:

> 이 집단은 고위험 이탈 방어군이 아니라, 콘텐츠 큐레이션 기반 정가 전환 강화군이다.

금지 표현:

`명확한 콘텐츠 취향 세그먼트`

`이탈 방어 타겟`

`콘텐츠 취향이 재구매를 유발했다`

`추천하면 반드시 전환된다`

허용 표현:

`콘텐츠 큐레이션 반응 후보군`

`콘텐츠 선호 proxy 기반 action layer`

`정가 전환 강화군`

`콘텐츠 추천과 이용 가치 상기 메시지 후보`

PUBLIC에서도 content signal이 broad하면 대표 segment discriminator로 과장하면 안 된다는 교훈이 남아 있다. PUBLIC 17 quality hotfix는 content_preference_signal을 representative rule에서 강등하고 broad content-context marker 또는 action cue로만 두라고 기록했다. 

---

# 9. 100원딜 해석 원칙

100원딜은 강하게 말한다.

하지만 인과처럼 말하지 않는다.

최종 발표에서 사용할 핵심 문장은 다음과 같다.

> 100원딜은 가입 장벽을 극단적으로 낮춘 유입 장치다. 따라서 정가 가입자보다 이용 동기와 지불 의향이 이질적인 고객이 함께 유입될 가능성이 크다. 이 때문에 100원딜 고객은 가입 자체보다 가입 이후 1~3주차에 실제 이용 습관으로 전환되는지가 핵심이며, 특히 3주차 이용 유지 여부는 정가 전환 실패 위험을 설명하는 중요한 행동 신호로 볼 수 있다.

이 문장은 강하지만 안전하다.

금지 문장:

`100원딜이 이탈을 유발했다.`

`100원딜 고객은 어차피 이탈한다.`

`100원딜 때문에 충성도가 낮다.`

허용 문장:

`100원딜은 유입 장벽을 낮춘다.`

`100원딜 고객은 이용 동기와 지불 의향이 이질적일 수 있다.`

`100원딜 고객에게 중요한 것은 가입 이후 이용 습관 전환이다.`

`3주차 이용 유지 여부는 정가 전환 실패 위험을 설명하는 중요한 행동 신호다.`

`3주차 초입 또는 종료 직전은 리텐션 개입의 핵심 타이밍 후보로 볼 수 있다.`

---

# 10. age/gender personalization layer

age/gender는 segment rule에 넣지 않는다.

age/gender는 이탈 원인이 아니다.

age/gender는 메시지, 채널, 콘텐츠 묶음을 조정하는 personalization layer다. `final_note.md`도 20대는 짧고 즉시성 있는 인기 콘텐츠, 친구추천 또는 쿠폰 메시지, 모바일 push가 적합한 후보이고, 30대는 퇴근 후 또는 주말 시청 맥락, 시간 효율, 취향 기반 추천, 40대 이상은 명확한 혜택 안내, 장르 기반 추천, 가족 또는 주말 시청 맥락을 사용할 수 있다고 정리한다. 

최종 구조:

1차: 행동 기반 segment

2차: 100원딜 여부에 따른 해석 차이

3차: age/gender 기반 메시지 variant

예시:

`3주차 이탈 임박 고위험군`

100원딜 고객에게는 “100원딜 종료 전, 지금 이어볼 콘텐츠” 메시지.

20대에게는 모바일 푸시, 짧고 즉시성 있는 인기 콘텐츠, 친구추천/쿠폰 메시지.

30대에게는 퇴근 후/주말 시청 맥락, 시간 효율, 취향 기반 추천.

40대 이상에게는 명확한 혜택 안내, 장르 기반 추천, 가족/주말 시청 맥락.

주의:

age/gender를 세그먼트 이름에 넣지 않는다.

`20대 여성 이탈형` 같은 표현은 금지한다.

---

# 11. payment-device 처리 원칙

payment-device 계열은 최종 해석 기준에서 제거된 것으로 본다.

대상 feature:

`payment_is_mobile`

`payment_is_pc`

`payment_is_android`

`payment_is_ios`

이 feature들은 viewing device, 즉 시청기기가 아니라 payment/account/acquisition context proxy로 본다. `final_note.md`도 이 feature들을 segment rule, label, action strategy의 기준으로 사용하지 않는다고 정리한다. 원본 CSV나 기존 feature set을 삭제한 것은 아니고, 해석 기준에서 제거했을 뿐이다. 

발표용 문장:

> 결제기기 정보는 실제 시청기기가 아니라 결제 환경과 계정 생성 맥락을 반영할 수 있으므로, 최종 해석 기준에서는 제외했습니다.

이 문장은 반드시 유지한다.

---

# 12. Referral 처리 원칙

Referral은 현재 데이터에서 직접 관측되지 않는다.

따라서 분석 결과로 말하지 않는다.

`final_note.md`도 Referral은 17x segment rule에 넣지 않고, 친구추천, 추천인 쿠폰, invite 메시지는 20대 또는 promo1 action strategy에서 후속 A/B test 제안으로만 둔다고 기록한다. 현재 산출물만으로 referral 효과를 검증했다고 말하지 않는다. 

최종 위치:

> Referral은 AARRR 프레임에 포함하되, 데이터 분석 결과가 아니라 후속 실험 제안으로 둔다.

20대/30대 대상 친구추천 100원딜 쿠폰 아이디어는 사용할 수 있다.

단, 표현은 다음처럼 제한한다.

> 모바일 친화 고객군을 대상으로 친구추천 100원딜 쿠폰 실험을 제안할 수 있다. 다만 현재 데이터에는 referral 로그가 없으므로 효과는 실제 캠페인 또는 A/B test로 검증해야 한다.

---

# 13. Activation 처리 원칙

Activation은 day0~20 기준이다.

day21 이후 행동은 대응기간으로 본다.

`final_note.md`도 Activation과 retention 해석은 day0~20 관측창 기준이며, 3주차 신호는 day0~20 안의 행동 변화이고, 4주차 이후 행동이나 장기 재구매 원인을 본 것처럼 말하지 않는다고 기록한다. 

최종 문장:

> 본 프로젝트의 Activation은 day0~20 관측창 안에서 발생한 첫 시청 또는 초기 이용 행동으로 정의한다. day21 이후 행동은 대응기간에 해당하므로 모델 feature나 segment rule로 사용하지 않는다.

---

# 14. campaign target 표현 원칙

세그먼트를 최종 캠페인 타겟이라고 말하지 않는다.

`final_note.md`도 이번 FINAL에서는 `개입 우선순위 후보군`, `검토 후보군`, `monitoring group`, `action layer` 표현을 우선 사용하고, 실제 캠페인 집행 전에는 팀 검토와 A/B test가 필요하다고 기록한다. 

표현 강도는 다음 순서다.

가장 안전:

`개입 우선순위 후보군`

중간:

`리텐션 캠페인 후보군`

강함:

`캠페인 타겟 후보군`

금지:

`최종 캠페인 타겟`

---

# 15. glossary: 영어와 변수명 풀이

# 15.1 row-level / subscription-event-level

`row-level`은 행 단위라는 뜻이다.

`subscription-event-level`은 구독 이벤트 단위라는 뜻이다.

이 프로젝트에서는 한 행을 한 명의 unique customer라고 부르면 안 된다. USER_KEY 중복과 구독 이벤트 단위 문제가 있기 때문이다. 따라서 row count를 고객 수라고 말하지 않는다.

# 15.2 is_repurchase

`is_repurchase`는 재구매 여부다.

`1`이면 다음 달 재구매.

`0`이면 다음 달 미재구매.

이 프로젝트의 target이다.

# 15.3 repurchase_score

`repurchase_score`는 재구매 가능성 점수다.

수식:

`repurchase_score = P(is_repurchase = 1)`

즉, 모델이 예측한 “다음 달에 재구매할 확률”이다.

# 15.4 churn_risk

`churn_risk`는 이탈 위험 점수다.

수식:

`churn_risk = 1 - repurchase_score`

재구매 가능성이 낮을수록 churn_risk는 높다.

# 15.5 OOF

`OOF`는 `Out-Of-Fold`의 약자다.

교차검증에서 자기 자신을 학습하지 않은 모델이 예측한 점수다.

OOF score는 in-sample score보다 안전하지만, 최종 캠페인 threshold는 아니다.

# 15.6 LightGBM

LightGBM은 gradient boosting 계열의 머신러닝 모델이다.

여기서는 17x segmentation score source로 사용됐다.

단, 최종 운영 모델 확정이라는 뜻은 아니다.

# 15.7 expanded_no_payment_device

`expanded_no_payment_device`는 expanded feature set에서 payment-device 계열 네 개를 제외한 feature set이다.

제외된 feature:

`payment_is_mobile`

`payment_is_pc`

`payment_is_android`

`payment_is_ios`

# 15.8 overall_with_promotion

`overall_with_promotion`은 promotion 고객과 non-promotion 고객을 함께 포함하고, promotion 정보를 사용할 수 있는 전체 scope다.

다만 최종 해석에서는 100원딜을 segment rule이 아니라 interpretation/action layer로 살린다.

# 15.9 promo1 / promo0

`promo1`은 100원딜 고객이다.

`promo0`는 비100원딜 고객이다.

최종 발표에서는 promo1을 100원딜 고객, promo0를 비100원딜 비교군으로 설명한다.

# 15.10 SHAP

SHAP은 모델 설명 기법이다.

모델이 어떤 feature를 중요하게 사용했는지 보여준다.

SHAP은 원인이 아니다.

# 15.11 action layer

`action layer`는 세그먼트를 다시 나누는 기준이 아니라, 세그먼트별 메시지, 채널, 혜택, 콘텐츠 추천 전략을 조정하는 층이다.

age/gender/promo 여부는 action layer에서 쓴다.

# 15.12 residual

`residual`은 기존 rule로 설명되지 않고 남은 잔여 집단이라는 뜻이다.

`general_observation`은 residual에 가깝다.

# 15.13 monitoring group

`monitoring group`은 즉시 캠페인 타겟은 아니지만, dashboard와 후속 분석에서 계속 추적해야 하는 집단이다.

# 15.14 content proxy

`content proxy`는 콘텐츠 선호를 직접 측정한 완전한 지표가 아니라, 장르 비율, 신작/구작 비율 등으로 간접 추정한 지표라는 뜻이다.

# 15.15 personalization layer

`personalization layer`는 고객의 연령, 성별, 프로모션 여부에 따라 메시지나 추천 방식을 조정하는 층이다.

---

# 16. 앞으로의 작업 순서

# 16.1 지금 완료된 상태

`final_note.md`는 최종 원칙 문서로 사용할 수 있는 수준에 도달했다.

role reclassification patch도 들어갔다.

즉, 이제 새 모델이나 새 세그먼트를 돌릴 단계가 아니다.

# 16.2 다음 작업: project_guide_v3 설계

다음에 만들 산출물은 `project_guide_v3.html` 또는 이에 준하는 최종 발표/대시보드 설명서다.

이 문서는 FINAL 기준으로 만들어야 한다.

반드시 포함할 내용:

프로젝트 주제.

데이터 기준.

score source 기준.

PUBLIC reference branch 설명.

세그먼트 7개 요약.

세그먼트 action tier 4개.

100원딜 해석.

age/gender personalization layer.

general_observation과 content_preference_target_candidate의 역할 재분류.

safe/unsafe wording.

멘토 방어 Q&A.

# 16.3 Codex 작업 방식

Codex에게 바로 자유롭게 “HTML 만들어줘”라고 하면 안 된다.

먼저 ChatGPT가 구조와 문장을 설계한다.

그다음 Codex는 이 설계에 따라 파일을 만든다.

Codex의 역할:

파일 생성.

HTML 생성.

CSV 생성.

README 작성.

final_checks 생성.

source fingerprint 생성.

review zip 생성.

Codex에게 금지할 것:

새 모델.

새 SHAP.

새 segmentation.

새 representative segment rule.

PUBLIC numeric score 병합.

park artifact 수정.

원본 CSV 수정.

# 16.4 ChatGPT 검수 방식

Codex가 만든 ZIP을 다시 ChatGPT 대화에 업로드한다.

검수 기준:

final_note와 일치하는가.

PUBLIC을 reference로만 썼는가.

park 수치를 기준으로 했는가.

세그먼트 rule을 바꾸지 않았는가.

100원딜 해석이 충분히 강한가.

general/content를 버리지 않고 역할 재분류했는가.

age/gender를 원인처럼 쓰지 않았는가.

HTML 표가 깨지지 않는가.

---

# 17. project_guide_v3의 권장 목차

`project_guide_v3.html`은 화려한 대시보드가 아니라 읽기 좋은 설명서여야 한다.

권장 목차는 다음이다.

# 17.1 프로젝트 한 줄 요약

100원딜 유입 고객의 day0~20 이용 행동을 기반으로 정가 전환 실패 위험을 설명하고, 세그먼트별 리텐션 개입 우선순위를 제안한다.

# 17.2 데이터와 시간축

row-level / subscription-event-level.

day0~20 관측기간.

day21 이후 대응기간.

target은 is_repurchase.

# 17.3 score 구조

repurchase_score.

churn_risk.

OOF score.

LightGBM score source.

# 17.4 왜 park.ingyeom을 기준으로 삼는가

23,079 rows.

payment-device removed.

16x SHAP과 17x segmentation 기준 정합성.

# 17.5 PUBLIC의 지위

reference branch.

100원딜 중심 narrative와 visual guide 구조만 참고.

numeric score와 assignment는 가져오지 않음.

# 17.6 100원딜 해석

가입 장벽을 낮춘 유입 장치.

이용 동기와 지불 의향의 이질성.

1~3주차 이용 습관 전환.

3주차 이용 유지 신호.

# 17.7 세그먼트 전체 구조

7개 segment.

각 segment의 rows, churn rate, mean churn_risk, promo1 share.

# 17.8 action tier 구조

즉시 개입 우선군.

관찰 강화군.

정가 전환 강화군.

모니터링 / 추가분해 후보군.

# 17.9 세그먼트별 비즈니스 전략

각 segment별:

행동 신호.

100원딜 맥락.

주요 메시지.

콘텐츠 추천.

쿠폰/혜택.

age/gender variant.

# 17.10 general_observation 처리

버리는 것 아님.

monitoring group.

후속 decomposition.

# 17.11 content_preference 처리

이탈 방어 아님.

콘텐츠 큐레이션 기반 정가 전환 강화군.

content proxy caveat.

# 17.12 인구통계 layer

20대.

30대.

40대 이상.

남성/여성 variant는 원인 아님.

# 17.13 Referral 실험 제안

AARRR의 Referral은 직접 관측되지 않음.

후속 실험 제안으로만 둠.

# 17.14 Safe / Unsafe wording

금지 표현과 허용 표현.

# 17.15 멘토 Q&A

왜 100원딜 분석인가?

왜 PUBLIC을 최종 기준으로 쓰지 않았나?

왜 general을 버리지 않았나?

왜 content segment는 고위험군이 아닌가?

왜 age/gender를 rule로 쓰지 않았나?

왜 campaign target이 아니라 후보군인가?

---

# 18. 다음 대화 또는 Codex에게 전달할 최상위 원칙

새로운 대화나 Codex가 이 프로젝트를 이어받을 경우 반드시 아래 원칙부터 읽어야 한다.

> 최종 계산 기준은 `park.ingyeom`이다.
> PUBLIC은 reference branch다.
> 최종 score source는 `LightGBM / expanded_no_payment_device / overall_with_promotion / OOF churn_risk`다.
> 17x segment rule과 assignment는 바꾸지 않는다.
> 100원딜은 segment rule이 아니라 presentation label, interpretation, business action layer에서 강하게 살린다.
> age/gender는 segment rule이 아니라 action personalization layer다.
> payment-device 계열은 최종 해석 기준에서 제거한다.
> general_observation은 버리지 않고 monitoring / 추가분해 후보군으로 둔다.
> content_preference_target_candidate는 고위험 이탈 방어군이 아니라 콘텐츠 큐레이션 기반 정가 전환 강화군으로 둔다.
> 1~4순위는 리텐션 개입 우선순위, 5~7순위는 역할 재분류 대상이다.
> 새 모델, 새 SHAP, 새 segmentation은 하지 않는다.
> 지금부터는 최종 발표/HTML/대시보드 문서화 단계다.

---

# 19. 지금 당장 다음 행동

다음 행동은 제가 `project_guide_v3 설계안`을 작성하는 것이다.

그 설계안을 사용자님이 검토한다.

그 다음 제가 Codex에게 줄 `project_guide_v3 생성 goal`을 작성한다.

Codex가 실제 HTML, CSV, README, final_checks, review zip을 만든다.

사용자님이 ZIP을 업로드한다.

제가 다시 검수한다.

이 순서가 현재 가장 안전하다.

지금 Codex에게 바로 맡기면 안 된다. 먼저 제가 guide 설계를 작성해야 한다. Codex는 문맥을 모르기 때문에, 세부 설계 없이 파일 생성을 맡기면 PUBLIC을 잘못 섞거나, content/general을 잘못 과장하거나, 100원딜 문장을 너무 약하게 만들 가능성이 높다.
