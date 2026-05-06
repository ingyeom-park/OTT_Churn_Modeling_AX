# 실행 로그 요약

## 실행 정보

- 실행 이름: `raw_data_schema_check`
- 실행 명령: `py -c from pathlib import Path; import pandas as pd; base=Path('_data/01_raw'); files=['Membership.csv','Movie_Master.csv','User_Mapping.csv','View_History.csv','Wavve_movie(KOBIS).csv','Wavve_movie(Regex).csv'];
for f in files:
    p=base/f
    df=pd.read_csv(p)
    print('\nFILE:', f)
    print('shape:', df.shape)
    print('columns:', list(df.columns))`
- 종료 코드: `0`
- 프로젝트 루트: `C:\Users\Dell5371\Desktop\ott-churn-prediction`
- stdout 로그: `C:\Users\Dell5371\Desktop\ott-churn-prediction\__openclaw_ollama_gemma4\agent_outputs\run_logs\20260506_162501_raw_data_schema_check_stdout.txt`
- stderr 로그: `C:\Users\Dell5371\Desktop\ott-churn-prediction\__openclaw_ollama_gemma4\agent_outputs\run_logs\20260506_162501_raw_data_schema_check_stderr.txt`

## Ollama 실행 시간

- 전체 소요 시간: 50.86초
- 모델 로드 시간: 5.46초
- 프롬프트 처리 시간: 5.85초
- 응답 생성 시간: 39.09초
- 프롬프트 토큰 수: 833
- 응답 토큰 수: 856

## 요약 결과

[실행 상태]
성공

[오류 유형]
없음

[확실한 사실]
명령어에 지정된 6개 파일(Membership.csv, Movie_Master.csv, User_Mapping.csv, View_History.csv, Wavve_movie(KOBIS).csv, Wavve_movie(Regex).csv)이 모두 성공적으로 로드되었으며, 각 파일의 형태(shape)와 컬럼 목록을 확인할 수 있습니다.

[가능한 원인]
(추측) 데이터 로딩 자체에는 문제가 없으나, 각 파일 간의 키(Key) 컬럼(예: `USER_ID`, `MOVIE_ID`)의 데이터 타입 불일치나 누락된 값이 존재할 수 있습니다.

[다음 조치]
1. 모든 데이터프레임의 `df.info()`를 실행하여 데이터 타입과 결측치(Null) 여부를 확인해야 합니다.
2. 핵심 컬럼들(ID)을 기준으로 데이터프레임 간의 조인(Join) 가능 여부와 일관성을 검토해야 합니다.

[주의할 점]
로그는 단순히 파일 로드 성공 여부만 보여주므로, 데이터의 내용적 유효성(예: 날짜 형식, ID의 고유성)이나 데이터 간의 논리적 관계는 검증되지 않았음을 유의해야 합니다.