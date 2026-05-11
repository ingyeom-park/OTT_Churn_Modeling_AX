# 04_v2 Content Feature Feasibility Check

## Inspected
- `_data/01_raw/Movie_Master.csv`
- `_data/01_raw/View_History.csv`

## Confirmed Facts
- Movie_Master rows: 14,502; columns: MOVIE_NUM, movie_title, ott_release_month, genre.
- Movie_Master MOVIE_NUM cardinality: 14,018.
- Duplicate MOVIE_NUM groups: 380; duplicate rows: 864; extra rows: 484.
- Duplicated MOVIE_NUM groups with conflicting values: 9. Conflict counts by column: {'genre': 9}.
- View_History MOVIE_NUM cardinality: 5,411; all viewed MOVIE_NUM values are covered by Movie_Master: True.
- Joining raw duplicated Movie_Master directly to View_History would produce 223,744 rows, which is 48,443 extra rows over raw View_History.

## Feasibility Judgment
- Feasible after deduplication: genre-based usage/content affinity features.
- Feasible with temporal caution: `ott_release_month` based recency or freshness features, if transformed without leaking future information.
- Weak or deferred: title-text features from `movie_title`, because they are harder to justify as business-retention signals without additional metadata.
- Not a model feature: `MOVIE_NUM`; use only for joining and aggregation.

## Recommendation Before Stage 04
- Do not join raw Movie_Master directly to View_History.
- Deduplicate Movie_Master by MOVIE_NUM first and retain a conflict audit.
- Treat genre conflicts in duplicated MOVIE_NUM rows as a Stage 04 policy decision before creating content features.

## Output
- `park.ingyeom/reports/tables/04_v2_content_feature_feasibility/04_v2_moviemaster_content_feasibility_audit.csv`
