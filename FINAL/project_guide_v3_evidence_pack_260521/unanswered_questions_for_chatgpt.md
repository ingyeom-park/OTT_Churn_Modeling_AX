> unanswered questions for ChatGPT

> data/file로 확인 가능한 것

- 06x primary main cohort가 23,079 row라는 점
- duration < 21 row 238개와 exact full duplicate extra row 26개가 제외되었다는 점
- conservative dataset은 22 feature, expanded dataset은 80 feature 기준이라는 점
- 17x score source가 LightGBM / expanded_no_payment_device / overall_with_promotion / OOF churn_risk라는 점
- 17x segment assignment와 7개 representative rule은 이미 저장되어 있다는 점

> 사용자 의사결정이 필요한 것

- guide v3에서 `content_preference_target_candidate`의 발표명을 `콘텐츠 큐레이션 반응 후보군`으로 확정할지
- `general_observation`을 `추가 관찰 필요 잔여군`으로 확정할지
- 100원딜 narrative의 표현 강도를 어느 수준까지 허용할지
- age/gender personalization 문구를 본문에 넣을지 appendix로 뺄지

> 발표 전략 판단이 필요한 것

- 1~4순위 우선순위군을 몇 장의 슬라이드 또는 HTML section으로 나눌지
- 5~7순위 role reclassification을 본문에서 얼마나 길게 설명할지
- 멘토 Q&A를 guide v3 마지막에 넣을지 별도 appendix로 둘지
- PUBLIC reference branch를 어느 정도까지 언급할지

> 현재 산출물만으로 확인 불가능한 것

- 전체 고객 DB에서 동일 rule을 재적용했을 때 segment별 row 수와 반응률
- 실제 캠페인 uplift 또는 A/B test 효과
- 고객의 실제 이용 동기와 지불 의향
- referral 메시지의 효과
- age/gender별 메시지 variant의 실제 성과
