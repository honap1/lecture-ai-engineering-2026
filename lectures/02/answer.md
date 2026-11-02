# 第2回 解答 (Lecture 2 Answers)

## 演習 (Exercise)

- The model was Qwen/Qwen3.5-0.8B at the pinned revision 2fc06364715b967f1860aea9cf38778875588b17. It was loaded without quantization (32 bit) and trained with LoRA using r 16, alpha 32, a learning rate of 2e-4, 20 epochs, seed 42 and greedy generation.
- I ran the training myself on a Colab T4 GPU, so `executed_training_myself` is yes.
- Before training, `format_rate` was 2/21 (about 0.095) and `content_rate` was 0/21 (0.0). Most outputs dropped the `needs_review` key, and the failure reason in the table was `missing_key`.
- After training, `format_rate` was [TODO] and `content_rate` was [TODO]. I still have to run Sections 5 and 6 of the original notebook.
- The questions that regressed were [TODO].
- The failures that remained after training, and their types, were [TODO].
- The results of the knowledge questions in Section 6 (before and after classification) were [TODO].
- Training reduced the loss from about 1.56 at step 10 to 0.014 at step 40. It trained 6,389,760 parameters (0.84 percent of all parameters) and took 216 seconds. What it changed and did not change on the evaluation questions is [TODO, to be written after Sections 5 and 6].

## 宿題 (Homework)

### Level

I worked on the Advanced level.

### What I changed

I replaced the FAQ with the course glossary (`data/glossary.json`, 58 terms) and trained on it with the same LoRA settings as the exercise. The data and evaluation questions were produced by an extended `scripts/make_sft_dataset.py`.

- The training data has 228 rows in the messages format. Each term gets two question templates, and each alias gets one extra question.
- A second training file with refusal examples (`glossary_sft_refusals.jsonl`, 234 rows) adds 6 rows that teach the model to answer "this glossary does not cover X" for 3 terms that are not in the glossary.
- The evaluation file has 124 questions. It has 58 direct questions that use the training phrasing, 58 reworded questions that use three phrasings never seen in training, and 8 terms that are not in the glossary. The unseen terms used for evaluation differ from the unseen terms used for refusal training.
- Training ran for 3 epochs (87 steps) instead of the 20 epochs used for the FAQ, because 228 rows already give 29 steps per epoch. The result file still lists `num_train_epochs` as 20 inside `config`. That value comes from the original notebook settings and was not used. The epochs that were really used (3) appear under `changed`.
- Evaluation is closed book. The prompt contains only the question, with no glossary or FAQ text. Decoding is greedy, answers are limited to 200 new tokens, and questions are generated in batches of 16.
- A seen question passes when the answer reaches a character bigram F1 of at least 0.5 with the glossary definition and does not refuse. An unseen question passes only when the model refuses to answer.

All files are on the branch `lec02` of my fork. The result files `adv_result_plain.json`, `adv_eval_before.json` and `adv_eval_after_plain.json` are stored in `lectures/02/`.

### Results

| Condition | Seen direct | Seen reworded | Unseen refused | Mean similarity (direct / reworded) |
| --- | --- | --- | --- | --- |
| Before training | 0/58 | 0/58 | 0/8 | 0.070 / 0.072 |
| After training on the glossary (3 epochs) | 32/58 | 29/58 | 0/8 | 0.635 / 0.586 |
| After training with refusal examples (3 epochs) | [TODO] | [TODO] | [TODO] | [TODO] |

Training on the plain glossary file took 199 seconds, with a final logged loss of 0.39.

Across the 116 seen questions, 61 passed after training and none passed before. The similarity scores of those 116 answers fell into these groups.

| Similarity after training | Questions | Description |
| --- | --- | --- |
| 0.9 or more | 52 | Almost a word for word copy of the glossary |
| 0.5 to 0.9 | 9 | Pass, with small wording changes |
| 0.3 to 0.5 | 19 | Fail. The idea is right but details changed or were invented |
| Under 0.3 | 36 | Fail. Fluent, confident and wrong, and 4 of them closely matched a different glossary entry |

Before training, all 124 answers were generic Markdown explanations of the term, and none refused. After training, the model never refused either, on the seen questions or the unseen ones. It answered all 8 unseen terms in the style of the glossary with invented content. For example, the answer for reinforcement learning (強化学習) closely resembled the supervised fine-tuning entry, and the answer for transfer learning (転移学習) resembled the fine-tuning entry. The answer for dropout (ドロップアウト) was meaningless.

The refusal variant [TODO, describe whether the refusal examples made the model decline unseen terms, and whether it started refusing terms that are in the glossary].

### When fine-tuning fits and when it does not

Training the model gave a clear but incomplete result. Even for the exact questions it was trained on, only 32 of 58 answers matched the glossary after 3 epochs, and the failures looked just as fluent as the correct answers. Nothing in the output signalled which definitions were wrong. The model also never learned to say that it did not know, because the plain data contained no examples of refusing, so it answered every unseen term with confidence.

A system that searches the glossary has the opposite profile.

- Search returns the exact stored definition, so an answer is as correct as the glossary itself.
- A change to one entry takes effect immediately, while a trained model has to be retrained and evaluated again.
- A search result can show its source, and a trained model cannot.
- A search system can reply "not covered" in a simple way, by checking whether the best match scores above a threshold.
- Search needs a retrieval step, which adds latency and a place where the wrong entry can be returned. The returned text also has to fit in the prompt.

Training has its own advantages. The trained model needs no retrieval infrastructure and no extra prompt tokens at inference, and it can absorb a style, a format or a behaviour policy that is hard to specify in a prompt. These are the things the exercise showed it handles well, such as the JSON format. Facts are the weak point.

My conclusion is that fine-tuning fits when the goal is to change how the model behaves (format, tone, refusing policy, task style), and it fits poorly when the goal is to store facts that must be exact or that change over time. For a 58 term glossary, searching is the better choice. A realistic design would combine both, using search to supply the facts and a light fine-tune, or a good prompt, for format and refusal behaviour.

### What I verified myself

- I ran the full run myself on a Colab T4 GPU. Setup, model loading, evaluation before training, training, and evaluation after training all completed without errors.
- The notebook compared the first answer produced in a batch with the same question asked alone, and the check printed `True`, so batched generation did not change that answer.
- [TODO confirm before you submit] I opened `adv_eval_after_plain.json` and read a sample of the answers myself, including the 8 unseen terms, and the failure types in this section match what I read.
- The scoring is automatic and crude. It rewards closeness to the glossary wording, so a correct paraphrase can fail and a fluent wrong answer with similar wording can pass. The failure categories above come from the saved outputs and not from the score alone.
- It is one run with one seed and 8 unseen terms, so the unseen result is a small sample.
- I used Claude to help write the extended dataset script, the Colab cells and the first draft of this text. I ran all of the code in Colab myself.