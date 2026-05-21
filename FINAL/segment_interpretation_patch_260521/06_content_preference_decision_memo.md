> content_preference_target_candidate decision memo

작성일: 2026-05-21
기준 파일: park.ingyeom 17x segmentation outputs
분석 단위: row-level / subscription-event-level

> 1. 이 세그먼트는 실제로 콘텐츠 취향이 뚜렷한가?

부분적으로만 그렇습니다. rule은 `flag_genre_focused`, `flag_new_movie_oriented`, `flag_old_movie_oriented` 중 하나라도 켜지면 content proxy 조건을 만족시키는 OR 구조입니다. segment 내부에서 `flag_genre_focused` 비중은 19.5%, `flag_new_movie_oriented` 비중은 41.4%, `flag_old_movie_oriented` 비중은 50.2%입니다.

따라서 모든 row가 뚜렷한 장르 취향을 가진다고 말하면 과장입니다. 이 세그먼트는 콘텐츠 취향 확정군이라기보다 Movie_Master 기반 content proxy가 관찰된 row의 넓은 묶음입니다.

> 2. broad content proxy marker인가?

그렇습니다. 이 segment는 6,195행이며 전체의 26.8%입니다. 전체 23,079행에서 세 content proxy 중 하나라도 켜진 비중은 62.4%입니다. PUBLIC에서 broad content signal을 강등했던 문제와 완전히 같은 파일은 아니지만, 발표 label이 넓은 proxy를 실제 취향으로 과잉 해석할 위험은 유사합니다.

> 3. target candidate라는 표현이 과한가?

과합니다. 이 segment의 churn rate는 10.1%이고 mean churn_risk는 0.095입니다. 전체 churn rate 28.3%, 전체 mean churn_risk 0.279보다 낮습니다. 즉 이 집단은 이탈 방어 campaign target이라기보다, 이미 어느 정도 이용 맥락이 있는 row에 대한 큐레이션 또는 유지 action 후보에 가깝습니다.

> 4. 추천 action layer로만 남겨야 하는가?

추천 action layer로 낮추는 편이 안전합니다. segment assignment와 rule은 유지하되, 발표에서는 콘텐츠 취향 타겟보다 콘텐츠 큐레이션 반응 후보 또는 콘텐츠 맥락 보유군처럼 약한 표현을 사용해야 합니다.

> 5. 발표용 이름

추천 발표명은 `콘텐츠 큐레이션 반응 후보군`입니다. 100원딜 문맥에서는 `100원딜 콘텐츠 큐레이션 후보군`으로 표현할 수 있습니다. 다만 이는 rule 변경이 아니라 label 후보입니다.

> 6. 유지 / 이름 약화 / 강등 중 추천

`이름 약화 + action layer 강등`을 추천합니다. segment 자체는 park 17x rule 결과이므로 유지합니다. 그러나 final storyline의 핵심 churn segment로 올리지는 않습니다.
