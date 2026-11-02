"""Lecture 1: ask a plain LLM a question (single-shot, or chat with history).

Usage:
    uv run python -m app.ask "What is LoRA?"
    uv run python -m app.ask            # no question: asks a course-specific one
    uv run python -m app.ask --chat     # keep conversation history (empty line or "exit" to quit)

The default mode has no tools and no history: a "plain" LLM call.
Ask something specific to this course and check whether it says "I don't know"
or confidently gives a plausible but wrong general answer.
(In lecture 3 this becomes an agent that searches the glossary.)
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# Course-specific question. The correct answer is homework-levels in data/glossary.json
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def format_usage(response) -> str:
    """Build a display string of input/output token counts from response.usage_metadata."""
    usage = response.usage_metadata
    if usage is None:
        return "[tokens] unavailable"
    return (
        f"[tokens] input: {usage.prompt_token_count} / "
        f"output: {usage.candidates_token_count}"
    )


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    # Exercise: print input and output token counts
    print(format_usage(response))

    return response.text


def chat_loop(first_question: str | None = None) -> None:
    """Keep asking questions while preserving conversation history (Implementation level).

    The chat object from client.chats.create() appends each exchange to an internal
    history on every send_message call and sends it along with the next request.
    That is why a follow-up like "Why is that?" can refer to the previous answer.
    """
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)

    question = first_question
    while True:
        if question is None:
            try:
                question = input("\n> ").strip()
            except EOFError:
                break
        if question.lower() in ("", "exit", "quit"):
            break

        response = chat.send_message(question)
        print(f"\n{response.text}")
        print(format_usage(response))
        question = None

    turns = len(chat.get_history()) // 2
    print(f"\n[done] {turns} exchanges in this conversation.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a plain LLM a question")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--chat",
        action="store_true",
        help="keep conversation history across questions (interactive mode)",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[question] {args.question}\n")
    try:
        if args.chat:
            chat_loop(args.question)
        else:
            print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
