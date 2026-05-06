from pathlib import Path
from datetime import datetime
import subprocess
import requests


# ============================================================
# 기본 설정
# ============================================================

MODEL_NAME = "gemma4:e4b"
OLLAMA_URL = "http://localhost:11434/api/generate"

THIS_FILE = Path(__file__).resolve()
AGENT_HOME = THIS_FILE.parents[1]
PROJECT_ROOT = AGENT_HOME.parent

RUN_LOG_DIR = AGENT_HOME / "agent_outputs" / "run_logs"
ERROR_SUMMARY_DIR = AGENT_HOME / "agent_outputs" / "error_summaries"

RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
ERROR_SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 테스트용 실행 명령
# ============================================================
# 1차 테스트: 성공해야 정상
# RUN_NAME = "python_version_check"
# COMMAND = ["py", "--version"]

# 2차 테스트: 일부러 실패해야 정상
# RUN_NAME = "intentional_failure_test"
# COMMAND = ["py", "not_existing_file.py"]

# RUN_NAME = "project_file_check"
# COMMAND = ["py", "-c", "from pathlib import Path; print(Path('data').exists()); print(list(Path('.').iterdir())[:10])"]

# RUN_NAME = "project_data_folder_check"
# COMMAND = [
#     "py",
#     "-c",
#     "from pathlib import Path; p=Path('_data'); print('exists:', p.exists()); print('is_dir:', p.is_dir()); print('items:', [x.name for x in p.iterdir()] if p.exists() else [])"
# ]

# RUN_NAME = "raw_data_file_check"
# COMMAND = [
#     "py",
#     "-c",
#     "from pathlib import Path; p=Path('_data/01_raw'); print('exists:', p.exists()); print('is_dir:', p.is_dir()); print('items:', [x.name for x in p.iterdir()] if p.exists() else [])"
# ]

# RUN_NAME = "raw_data_schema_check"
# COMMAND = [
#     "py",
#     "-c",
#     "from pathlib import Path; import pandas as pd; base=Path('_data/01_raw'); files=['Membership.csv','Movie_Master.csv','User_Mapping.csv','View_History.csv','Wavve_movie(KOBIS).csv','Wavve_movie(Regex).csv'];\nfor f in files:\n    p=base/f\n    df=pd.read_csv(p)\n    print('\\nFILE:', f)\n    print('shape:', df.shape)\n    print('columns:', list(df.columns))"
# ]

RUN_NAME = "interim_membership_v1_file_check"
COMMAND = [
    "py",
    "-c",
    "from pathlib import Path\nbase=Path('_data/02_interim')\ntargets=[p for p in base.iterdir() if p.is_dir() and p.name.startswith('260430_membership_v1')]\nprint('target_count:', len(targets))\nfor t in targets:\n    print('TARGET:', t)\n    print('items:', [x.name for x in t.iterdir()])"
]


# ============================================================
# Ollama 프롬프트
# ============================================================

def build_prompt(command_text: str, return_code: int, stdout_text: str, stderr_text: str) -> str:
    log_text = f"""
[실행 명령]
{command_text}

[종료 코드]
{return_code}

[stdout]
{stdout_text}

[stderr]
{stderr_text}
""".strip()

    prompt = f"""
너는 데이터 분석 프로젝트의 실행 로그를 검토하는 보조자다.

중요 규칙:
- Thinking, 내부 추론, chain-of-thought를 출력하지 마라.
- 아래 형식만 사용해라.
- 사실과 추측을 구분해라.
- 전체 답변은 500자 이내로 완결해라.
- 반드시 [주의할 점]까지 작성해라.

출력 형식:

[실행 상태]
성공 또는 실패 중 하나로 작성

[오류 유형]
오류가 있으면 유형을 한 줄로 작성하고, 없으면 없음이라고 작성

[확실한 사실]
로그에서 직접 확인 가능한 사실만 작성

[가능한 원인]
추측 가능한 원인을 작성하되, 추측임을 명시

[다음 조치]
사용자가 확인해야 할 구체적 조치를 작성

[주의할 점]
과잉 해석을 피하기 위한 주의점을 작성

실행 로그:
{log_text}
""".strip()

    return prompt


# ============================================================
# 유틸 함수
# ============================================================

def ns_to_sec(value):
    if value is None:
        return 0.0
    return value / 1_000_000_000


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def run_command(command: list[str], cwd: Path):
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )

    return result.returncode, result.stdout, result.stderr


def ask_ollama(prompt: str):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "num_predict": 1000,
        },
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=300)
    response.raise_for_status()

    data = response.json()

    result_text = data.get("response", "").strip()

    if not result_text:
        result_text = (
            "[실행 상태]\n"
            "요약 실패\n\n"
            "[오류 유형]\n"
            "Ollama 응답 본문 없음\n\n"
            "[확실한 사실]\n"
            "명령 실행 로그는 저장되었으나, Ollama가 비어 있는 응답을 반환했습니다.\n\n"
            "[가능한 원인]\n"
            "(추측) num_predict 제한에 걸렸거나, 모델이 내부 thinking에 토큰을 소모했을 수 있습니다.\n\n"
            "[다음 조치]\n"
            "num_predict 값을 늘리고, 프롬프트를 더 짧게 조정하세요.\n\n"
            "[주의할 점]\n"
            "원본 stderr 로그를 우선 확인해야 합니다."
        )

    timing = {
        "total_duration_sec": ns_to_sec(data.get("total_duration")),
        "load_duration_sec": ns_to_sec(data.get("load_duration")),
        "prompt_eval_duration_sec": ns_to_sec(data.get("prompt_eval_duration")),
        "eval_duration_sec": ns_to_sec(data.get("eval_duration")),
        "prompt_eval_count": data.get("prompt_eval_count"),
        "eval_count": data.get("eval_count"),
    }

    return result_text, timing


def write_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


def build_summary_report(
    run_name: str,
    command_text: str,
    return_code: int,
    stdout_path: Path,
    stderr_path: Path,
    summary_text: str,
    timing: dict,
) -> str:
    report = f"""
# 실행 로그 요약

## 실행 정보

- 실행 이름: `{run_name}`
- 실행 명령: `{command_text}`
- 종료 코드: `{return_code}`
- 프로젝트 루트: `{PROJECT_ROOT}`
- stdout 로그: `{stdout_path}`
- stderr 로그: `{stderr_path}`

## Ollama 실행 시간

- 전체 소요 시간: {timing["total_duration_sec"]:.2f}초
- 모델 로드 시간: {timing["load_duration_sec"]:.2f}초
- 프롬프트 처리 시간: {timing["prompt_eval_duration_sec"]:.2f}초
- 응답 생성 시간: {timing["eval_duration_sec"]:.2f}초
- 프롬프트 토큰 수: {timing["prompt_eval_count"]}
- 응답 토큰 수: {timing["eval_count"]}

## 요약 결과

{summary_text}
""".strip()

    return report


# ============================================================
# 메인 실행
# ============================================================

def main():
    stamp = now_stamp()
    command_text = " ".join(COMMAND)

    print("THIS_FILE:", THIS_FILE)
    print("AGENT_HOME:", AGENT_HOME)
    print("PROJECT_ROOT:", PROJECT_ROOT)
    print("RUN_NAME:", RUN_NAME)
    print("COMMAND:", command_text)
    print()

    return_code, stdout_text, stderr_text = run_command(COMMAND, cwd=PROJECT_ROOT)

    stdout_path = RUN_LOG_DIR / f"{stamp}_{RUN_NAME}_stdout.txt"
    stderr_path = RUN_LOG_DIR / f"{stamp}_{RUN_NAME}_stderr.txt"

    write_text(stdout_path, stdout_text)
    write_text(stderr_path, stderr_text)

    print("명령 실행 완료")
    print("종료 코드:", return_code)
    print("stdout 저장:", stdout_path)
    print("stderr 저장:", stderr_path)
    print()

    prompt = build_prompt(
        command_text=command_text,
        return_code=return_code,
        stdout_text=stdout_text,
        stderr_text=stderr_text,
    )

    summary_text, timing = ask_ollama(prompt)

    summary_report = build_summary_report(
        run_name=RUN_NAME,
        command_text=command_text,
        return_code=return_code,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        summary_text=summary_text,
        timing=timing,
    )

    summary_path = ERROR_SUMMARY_DIR / f"{stamp}_{RUN_NAME}_summary.md"
    write_text(summary_path, summary_report)

    print("요약 결과 저장 완료:")
    print(summary_path)
    print()

    print("[Ollama 실행 시간]")
    print(f"전체 소요 시간: {timing['total_duration_sec']:.2f}초")
    print(f"모델 로드 시간: {timing['load_duration_sec']:.2f}초")
    print(f"프롬프트 처리 시간: {timing['prompt_eval_duration_sec']:.2f}초")
    print(f"응답 생성 시간: {timing['eval_duration_sec']:.2f}초")
    print(f"프롬프트 토큰 수: {timing['prompt_eval_count']}")
    print(f"응답 토큰 수: {timing['eval_count']}")
    print()

    print(summary_text)


if __name__ == "__main__":
    main()