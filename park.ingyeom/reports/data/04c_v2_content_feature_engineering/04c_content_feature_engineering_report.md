# 04c Corrected Content Feature Engineering Report

- strict-core membership rows: 23115
- deduplicated MovieMaster rows: 14018
- genre conflict rows audited: 32
- active movie fields only: MOVIE_NUM, movie_title, ott_release_month, genre
- w1_4 is late-period/end-of-period only, not an early-warning window.
- full content tables include exploratory genre watch-time/session features; Stage 05c prunes those from official candidates.
