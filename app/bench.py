"""Lecture 1 (Advanced): measure response time and token counts across models and questions.

Usage:
    uv run python -m app.bench
    uv run python -m app.bench --models gemini-3.5-flash-lite,gemini-3.5-flash --runs 2

Prints a Markdown table you can paste into lectures/01/answer.md.
"""

import argparse
import time

from google import genai
from google.genai import errors

from app.config import get_api_key

QUESTIONS = {
    "short": "What is LoRA? Answer in one sentence.",
    "course": "AIE2026の講座の宿題にある「3レベル」とは何ですか？",
    "long": "Explain LoRA in detail, with the math and a practical example.",
}


def measure(client, model: str, question: str) -> dict:
    """Call the model once and return elapsed seconds and token counts."""
    start = time.perf_counter()
    try:
        response = client.models.generate_content(model=model, contents=question)
    except errors.APIError as e:
        return {"seconds": time.perf_counter() - start, "error": str(e.code)}
    seconds = time.perf_counter() - start
    usage = response.usage_metadata
    return {
        "seconds": seconds,
        "input": usage.prompt_token_count,
        "output": usage.candidates_token_count,
        "total": usage.total_token_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark models: time and tokens")
    parser.add_argument("--models", default="gemini-3.5-flash-lite,gemini-3.5-flash")
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--pause", type=float, default=5.0, help="seconds between calls")
    args = parser.parse_args()

    client = genai.Client(api_key=get_api_key())
    print("| model | question | run | seconds | input | output | total | output tok/s |")
    print("|---|---|---|---|---|---|---|---|")
    for model in args.models.split(","):
        for name, question in QUESTIONS.items():
            for run in range(1, args.runs + 1):
                r = measure(client, model, question)
                if "error" in r:
                    print(f"| {model} | {name} | {run} | {r['seconds']:.1f} | error {r['error']} | | | |")
                else:
                    rate = (r["output"] or 0) / r["seconds"]
                    print(
                        f"| {model} | {name} | {run} | {r['seconds']:.1f} | {r['input']} | "
                        f"{r['output']} | {r['total']} | {rate:.0f} |"
                    )
                time.sleep(args.pause)  # stay under the free-tier rate limit


if __name__ == "__main__":
    main()