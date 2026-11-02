# 第1回 解答 (Lecture 1 Answers)

## 演習 (Exercise)

- Model's answer to the course-specific question (summary is fine):
  - Asked "AIE2026の講座の宿題にある「3レベル」とは何ですか？" with gemini-3.5-flash-lite. The model did not say it didn't know. It confidently guessed that "3 levels" means a generic beginner / intermediate / advanced split (or AI user / builder / engineer levels), and told me to check Slack or the course materials.
- What I noticed compared with the glossary's correct meaning:
  - The correct answer (`homework-levels` in `data/glossary.json`): the homework has three levels (Basic, Implementation, Advanced), and completing any one of them completes that lecture's homework.
  - The model's answer was plausible and partly overlapping (three difficulty levels), but it missed that you only need to do one level and that it is not graded. A plain LLM does not know course-specific facts and can sound authoritative anyway.
- Token counts displayed (input / output):
  - `[tokens] input: 21 / output: 673`

## 宿題 (Homework)

- Level completed: **Advanced** (I also did Implementation)
- What I did:
  - Implementation: added a `--chat` option to `app/ask.py` using `client.chats.create(model=MODEL)` and `send_message()`, so follow-up questions keep the conversation history. Also implemented the exercise TODO: `format_usage()` prints input/output token counts from `response.usage_metadata`.
  - Advanced: added `app/bench.py`, which calls each model on three questions twice, measures wall-clock time with `time.perf_counter()`, and reads token counts from `usage_metadata`. It pauses 5 s between calls to stay under rate limits and prints a Markdown table.
  - Models: `gemini-3.5-flash-lite` and `gemini-3.5-flash`. Questions: short ("What is LoRA? Answer in one sentence."), course (the "3 levels" question), long ("Explain LoRA in detail, with the math and a practical example."). 2 runs each, 12 calls in total.
- Result:
  - Chat mode: "What is LoRA?" then "Why is that?" continued the LoRA topic, so history was kept. Input tokens went from 6 (turn 1) to 737 (turn 2) because the previous question and answer are resent.
  - Benchmark (seconds, tokens as reported by the API; "thinking" = total - input - output):

| model | question | run | seconds | input | output | total | thinking |
|---|---|---|---|---|---|---|---|
| flash-lite | short | 1 | 1.0 | 11 | 37 | 48 | 0 |
| flash-lite | short | 2 | 1.0 | 11 | 39 | 50 | 0 |
| flash-lite | course | 1 | 3.5 | 21 | 690 | 711 | 0 |
| flash-lite | course | 2 | 2.7 | 21 | 461 | 482 | 0 |
| flash-lite | long | 1 | 5.8 | 15 | 1921 | 1936 | 0 |
| flash-lite | long | 2 | 6.4 | 15 | 1988 | 2003 | 0 |
| flash | short | 1 | 3.3 | 11 | 44 | 511 | 456 |
| flash | short | 2 | 2.9 | 11 | 47 | 482 | 424 |
| flash | course | 1 | 10.0 | 21 | 603 | 1651 | 1027 |
| flash | course | 2 | 10.6 | 21 | 689 | 1653 | 943 |
| flash | long | 1 | 22.2 | 15 | 2697 | 4149 | 1437 |
| flash | long | 2 | 23.2 | 15 | 2766 | 4317 | 1536 |

- Observations / analysis:
  - Latency grows with output length and with the model. For the same question, gemini-3.5-flash took about 3-4x longer than flash-lite (short ~3.1 s vs ~1.0 s; course ~10.3 s vs ~3.1 s; long ~22.7 s vs ~6.1 s).
  - The extra time and tokens come from thinking. Flash-lite reported no thinking tokens (total = input + output), while flash spent roughly 420-1540 thinking tokens per call, even on a one-sentence question. Thinking tokens are included in the total but not in the output count, so the `output tok/s` column understates how fast flash works; its time includes the thinking phase.
  - Within one model and question, the two runs were close in time, but output length varied (flash-lite course question: 690 vs 461 tokens), and time followed output length. With only 2 runs per cell, these numbers are indicative, not statistically solid.
  - The model name `gemini-3.5-flash` may be forwarded to a newer model (the lecture notes say it is deprecated and forwards to 3.6 flash), so I can't be sure which model actually served those calls.
  - Relation to free-tier rate limits: free quotas are limited per minute and per day in requests and in tokens. A cheap-looking one-sentence question on a thinking model still used ~500 tokens in total, and long answers used 2,000-4,300. So token-based limits are reached much sooner than the number of requests suggests, and longer or slower calls also hold up anything running sequentially. The history in chat mode makes this worse, since input tokens grow every turn. I paused 5 s between calls and hit no 429 in these 12 calls, but a tight loop would likely trigger one. I did not look up the exact quota numbers, so check the official rate-limit page for the current values.
  - Practical takeaways: use flash-lite for simple or high-volume calls, use the thinking model only when it is worth the latency and tokens, cap or trim conversation history, and add retry with backoff for 429/503.