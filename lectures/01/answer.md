# 第1回 解答 (Lecture 1 Answers)

## 演習 (Exercise)

- Model's answer to the course-specific question (summary is fine):
  - Asked "AIE2026の講座の宿題にある「3レベル」とは何ですか？" with gemini-3.5-flash-lite. The model did not say it didn't know. It confidently guessed that "3 levels" means a generic beginner / intermediate / advanced split (or AI user / builder / engineer levels), and told me to check Slack or the course materials.
- What I noticed compared with the glossary's correct meaning:
  - The correct answer (`homework-levels` in `data/glossary.json`): the homework has three levels (Basic, Implementation, Advanced), and completing any one of them completes that lecture's homework.
  - The model's answer was plausible and partly overlapping (three difficulty levels), but it missed the key facts that you only need to do one level and that it is not graded. It presented several guesses with confidence, which shows a plain LLM does not know course-specific facts and can sound authoritative anyway.
- Token counts displayed (input / output):
  - `[tokens] input: 21 / output: 673`

## 宿題 (Homework)

- Level completed: **Implementation**
- What I did:
  - Added a `--chat` option to `app/ask.py` so follow-up questions can be asked while keeping the conversation history.
  - Used `client.chats.create(model=MODEL)` from `google-genai` to create a chat object and `send_message()` to send each question. The chat object appends every exchange (question and answer) to its internal history and sends that history along with the next call.
  - The loop ends on an empty line, `exit` or `quit`, and prints the number of exchanges at the end.
  - Also completed the exercise TODO: `format_usage()` reads input and output token counts from `response.usage_metadata`, and both the single-question mode and chat mode print them on every call.
- Result:
  - Ran `uv run python -m app.ask --chat "What is LoRA?"` and then asked the follow-up "Why is that?". The second answer correctly continued the LoRA topic ("Why does LoRA work so well while being so small?"), so the history was kept. Without history, the model would not have known what "that" referred to.
  - Turn 1 tokens: `input: 6 / output: 725`. Turn 2 tokens: `input: 737 / output: 519`.
- Observations / questions:
  - Turn 2's input tokens jumped from 6 to 737, which is roughly turn 1's question plus its 725-token answer plus the new question. This confirms the whole history is resent on every turn, so input cost grows with conversation length. Long conversations will use up the free-tier token and rate limits much faster.
  - The model guessed what the vague follow-up "Why is that?" meant and said so explicitly, which was helpful but is also a sign it can fill in gaps by assumption.
  - Open question: how should an application trim or summarize old history when conversations get long, while keeping the context that matters?
