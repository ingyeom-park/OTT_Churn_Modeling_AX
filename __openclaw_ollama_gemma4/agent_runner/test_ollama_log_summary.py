# py .\__openclaw_ollama_gemma4\agent_runner\test_ollama_log_summary.py

from pathlib import Path
import requests


MODEL_NAME = "gemma4:e4b"
OLLAMA_URL = "http://localhost:11434/api/generate"

THIS_FILE = Path(__file__).resolve()
AGENT_HOME = THIS_FILE.parents[1]

OUTPUT_DIR = AGENT_HOME / "agent_outputs" / "error_summaries"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_TEXT = """
FileNotFoundError: [Errno 2] No such file or directory: './data/membership.csv'
""".strip()


PROMPT = f"""
너는 데이터 분석 프로젝트의 실행 로그를 검토하는 보조자다.

중요 규칙:
- 내부 추론 과정, Thinking, 사고 과정, chain-of-thought를 출력하지 마라.
- 아래 출력 형식만 사용해라.
- 사실과 추측을 반드시 구분해라.
- 코드를 직접 수정했다고 말하지 마라.
- 최종 제출용 결론처럼 단정하지 마라.
- 전체 답변은 500자 이내로 작성해라.
- 각 항목은 최대 2줄만 작성해라.
- 불필요한 설명, 예시, 일반론은 쓰지 마라.

출력 형식:

[실행 상태]
성공 또는 실패 중 하나로 작성

[오류 유형]
오류 유형을 한 줄로 작성

[확실한 사실]
로그에서 직접 확인 가능한 사실만 작성

[가능한 원인]
추측 가능한 원인을 작성하되, 추측임을 명시

[다음 조치]
사용자가 확인해야 할 구체적 조치를 작성

[주의할 점]
과잉 해석을 피하기 위한 주의점을 작성

실행 로그:
{LOG_TEXT}
""".strip()


def ns_to_sec(value):
    if value is None:
        return 0.0
    return value / 1_000_000_000


def ask_ollama(prompt: str):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "num_predict": 300,
        },
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=300)
    response.raise_for_status()

    data = response.json()

    result_text = data["response"].strip()

    timing = {
        "total_duration_sec": ns_to_sec(data.get("total_duration")),
        "load_duration_sec": ns_to_sec(data.get("load_duration")),
        "prompt_eval_duration_sec": ns_to_sec(data.get("prompt_eval_duration")),
        "eval_duration_sec": ns_to_sec(data.get("eval_duration")),
        "prompt_eval_count": data.get("prompt_eval_count"),
        "eval_count": data.get("eval_count"),
    }

    return result_text, timing


def build_report(result: str, timing: dict) -> str:
    report = f"""
# Ollama 로그 요약 테스트

## 경로 정보

- THIS_FILE: `{THIS_FILE}`
- AGENT_HOME: `{AGENT_HOME}`

## Ollama 실행 시간

- 전체 소요 시간: {timing["total_duration_sec"]:.2f}초
- 모델 로드 시간: {timing["load_duration_sec"]:.2f}초
- 프롬프트 처리 시간: {timing["prompt_eval_duration_sec"]:.2f}초
- 응답 생성 시간: {timing["eval_duration_sec"]:.2f}초
- 프롬프트 토큰 수: {timing["prompt_eval_count"]}
- 응답 토큰 수: {timing["eval_count"]}

## 요약 결과

{result}
""".strip()

    return report


def main():
    print("THIS_FILE:", THIS_FILE)
    print("AGENT_HOME:", AGENT_HOME)

    result, timing = ask_ollama(PROMPT)
    report = build_report(result, timing)

    output_path = OUTPUT_DIR / "test_error_summary.md"
    output_path.write_text(report, encoding="utf-8")

    print("요약 결과 저장 완료:")
    print(output_path)
    print()

    print("[Ollama 실행 시간]")
    print(f"전체 소요 시간: {timing['total_duration_sec']:.2f}초")
    print(f"모델 로드 시간: {timing['load_duration_sec']:.2f}초")
    print(f"프롬프트 처리 시간: {timing['prompt_eval_duration_sec']:.2f}초")
    print(f"응답 생성 시간: {timing['eval_duration_sec']:.2f}초")
    print(f"프롬프트 토큰 수: {timing['prompt_eval_count']}")
    print(f"응답 토큰 수: {timing['eval_count']}")
    print()

    print(result)


if __name__ == "__main__":
    main()