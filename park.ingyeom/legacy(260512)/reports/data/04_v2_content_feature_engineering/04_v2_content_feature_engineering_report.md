# 04_v2 Content Feature Engineering Report

## Scope
- Created content features only from active v2 `Movie_Master` columns: `MOVIE_NUM`, `movie_title`, `ott_release_month`, `genre`.
- No unavailable metadata, final modeling dataset, or model training was created.

## Movie_Master Deduplication
- Raw Movie_Master rows: 14,502.
- Deduplicated MOVIE_NUM rows: 14,018.
- Genre conflict groups audited: 9.
- Dedupe rule: stable sort by MOVIE_NUM and original row order, choose first non-null genre, preserve conflicting rows in audit.

## Observation Windows
- `w1_3`: rel_day 0 through 20.
- `w1_4`: rel_day 0 through 27.

## Output Files
- park.ingyeom/reports/data/04_v2_content_feature_engineering/content_features_v2_w1_3.csv
- park.ingyeom/reports/data/04_v2_content_feature_engineering/content_features_v2_w1_4.csv
- park.ingyeom/reports/data/04_v2_content_feature_engineering/content_feature_summary.json
- park.ingyeom/reports/data/04_v2_content_feature_engineering/04_v2_content_feature_engineering_report.md

## Notes
- `MOVIE_NUM` and `movie_title` were used only for joining or audit, not as model features.
- No end_date-derived content features were created.
