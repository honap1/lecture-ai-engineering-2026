# 第2回 解答 (Lecture 2 Answers)

## 演習 (Exercise)

- The model was Qwen/Qwen3.5-0.8B at the pinned revision 2fc06364715b967f1860aea9cf38778875588b17. It was loaded without quantization (32 bit) and trained with LoRA using r 16, alpha 32, a learning rate of 2e-4, 20 epochs, seed 42 and greedy generation.
- I ran the training myself on a Colab T4 GPU, so `executed_training_myself` is yes.
- Before training, `format_rate` was 2/21 (about 0.095) and `content_rate` was 0/21 (0.0). Most outputs dropped the `needs_review` key, and the failure reason in the table was `missing_key`.
- After training, `format_rate` was 21/21 (1.0) and `content_rate` was 19/21 (about 0.905). Both were measured on the same 21 test questions as before training, with the same greedy generation settings.
- No question regressed. The list of questions that passed before training and failed after it was empty.
- Two failures remained after training and both had the same type. The questions were "When will grades be released?" (成績はいつ出ますか) and "Do I need to book office hours in advance?" (オフィスアワーは事前予約が必要ですか). The FAQ does not answer either one, so the correct output was `needs_review` true. The model instead returned `needs_review` false and repeated a different FAQ item, the deadline for the first question and the office hours for the second. In other words, it asserted another FAQ item for a question without grounding. No question that the FAQ does cover was dodged with a "not covered" answer.
- Of the 6 test questions without grounding, the model flagged 4 for review and asserted an answer for 2. It answered all 15 grounded test questions correctly.
- The knowledge questions in Section 6 gave the results in the table below.

| Question | Classification before training | Classification after training |
| --- | --- | --- |
| Final assignment deadline (not in the FAQ) | format_error, because it wrote the deadline without `needs_review` | asserted, because it repeated the FAQ deadline |
| Instructor name (not in the FAQ) | format_error, because it wrote "確認が必要" without `needs_review` | needs_review |
| Topic of the next lecture (not in the FAQ) | format_error, with a garbled answer | needs_review |
| Assignment deadline (control, in the FAQ) | format_error | asserted, and correct because the FAQ covers it |

- Training took 216 seconds for 40 steps and trained 6,389,760 parameters (0.84 percent of all parameters). The loss fell from about 1.56 at step 10 to 0.014 at step 40.
- Training changed the format and the wording. The output went from valid JSON in 2 of 21 cases to 21 of 21, and the answers came back almost word for word from the FAQ text used in training. Training did not guarantee judgment on questions the FAQ does not cover. The model flagged 2 of the 3 unknown knowledge questions and 4 of the 6 ungrounded test questions, and for the rest it confidently reused another FAQ item.
- I also ran the optional Section 8. Loading the same model in 4 bit reduced the weight memory from 3.01 GB to 0.76 GB. Without any training, it also changed the outputs, and `format_rate` moved from 0.095 to 0.667 and `content_rate` from 0.0 to 0.333. The direction was mixed. Some answers gained the `needs_review` key, while other answers asserted "なし" or "はい" for questions without grounding, and one answer wrote `needs_review` as the string "false", which failed the type check.

## 宿題 (Homework)

### Level

I worked on the Advanced level.

### What I changed

I replaced the FAQ with the course glossary (`data/glossary.json`, 58 terms) and trained on it with the same LoRA settings as the exercise. The data and evaluation questions were produced by an extended `scripts/make_sft_dataset.py`.

- The training data has 228 rows in the messages format. Each term gets two question templates, and each alias gets one extra question.
- A second training file with refusal examples (`glossary_sft_refusals.jsonl`, 234 rows) adds 6 rows that teach the model to answer "this glossary does not cover X" for 3 terms that are not in the glossary.
- The evaluation file has 124 questions. It has 58 direct questions that use the training phrasing, 58 reworded questions that use three phrasings never seen in training, and 8 terms that are not in the glossary. The unseen terms used for evaluation differ from the unseen terms used for refusal training.
- Training ran for 3 epochs (87 steps for the plain file and 90 steps for the refusal file) instead of the 20 epochs used for the FAQ, because 228 rows already give 29 steps per epoch. The result file still lists `num_train_epochs` as 20 inside `config`. That value comes from the original notebook settings and was not used. The epochs that were really used (3) appear under `changed`.
- Evaluation is closed book. The prompt contains only the question, with no glossary or FAQ text. Decoding is greedy, answers are limited to 200 new tokens, and questions are generated in batches of 16.
- A seen question passes when the answer reaches a character bigram F1 of at least 0.5 with the glossary definition and does not refuse. An unseen question passes only when the model refuses to answer.

All files are on the branch `lec02` of my fork. The result files `adv_result_plain.json`, `adv_eval_before.json` and `adv_eval_after_plain.json` are stored in `lectures/02/`, together with the executed notebooks of the FAQ run, the plain glossary run and the refusal run. The notebooks keep every printed table.

### Results

| Condition | Seen direct | Seen reworded | Unseen refused | Mean similarity (direct / reworded) |
| --- | --- | --- | --- | --- |
| Before training | 0/58 | 0/58 | 0/8 | 0.070 / 0.072 |
| After training on the glossary (3 epochs) | 32/58 | 29/58 | 0/8 | 0.635 / 0.586 |
| After training with refusal examples (3 epochs) | 36/58 | 32/58 | 0/8 | 0.648 / 0.620 |

Training on the plain glossary file took 199 seconds for 87 steps, with a final logged loss of 0.39. Training on the refusal file took 214 seconds for 90 steps, with a final logged loss of 0.31.

Across the 116 seen questions, 61 passed after training and none passed before. The similarity scores of those 116 answers fell into these groups.

| Similarity after training | Questions | Description |
| --- | --- | --- |
| 0.9 or more | 52 | Almost a word for word copy of the glossary |
| 0.5 to 0.9 | 9 | Pass, with small wording changes |
| 0.3 to 0.5 | 19 | Fail. The idea is right but details changed or were invented |
| Under 0.3 | 36 | Fail. Fluent, confident and wrong, and 4 of them closely matched a different glossary entry |

Before training, all 124 answers were generic Markdown explanations of the term, and none refused. After training, the model never refused either, on the seen questions or the unseen ones. It answered all 8 unseen terms in the style of the glossary with invented content. For example, the answer for reinforcement learning (強化学習) closely resembled the supervised fine-tuning entry, and the answer for transfer learning (転移学習) resembled the fine-tuning entry. The answer for dropout (ドロップアウト) was meaningless.

The refusal variant did not make the model decline unseen terms. It refused none of the 8 unseen terms, the same as the plain run, and none of its answers to the seen questions was a refusal either. Only 6 of the 234 training rows were refusals (3 terms with 2 phrasings each), and that was not enough to teach the behaviour, at least with 3 epochs and this small model. The seen terms improved slightly, from 61 to 68 of 116 passes. I cannot attribute that gain to the refusal rows, because the run also had 6 extra rows and 3 more steps, and I ran each variant only once. The unseen answers show how the model fails. For transfer learning (転移学習) and knowledge distillation (知識蒸留) it returned almost the full fine-tuning entry, so the model mapped each unknown term onto the nearest known entry and answered with confidence.

### When fine-tuning fits and when it does not

Training the model gave a clear but incomplete result. Even for the exact questions it was trained on, only 32 of 58 answers matched the glossary after 3 epochs, and the failures looked just as fluent as the correct answers. Nothing in the output signalled which definitions were wrong. The model also never learned to say that it did not know. The plain data contained no examples of refusing, and adding a handful of refusal examples did not change that, so it answered every unseen term with confidence in both runs.

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
- The "before training" results of the refusal run matched the plain run exactly (0 of 58, 0 of 58, 0 of 8, with mean similarities of 0.070 and 0.072), which shows that the evaluation is repeatable.
- The failure types in this section were computed from the saved file `adv_eval_after_plain.json` with an analysis script, and a sample of the answers was inspected during that analysis with the help of Claude. The scores are automatic, and I did not check every answer by hand.
- The scoring is automatic and crude. It rewards closeness to the glossary wording, so a correct paraphrase can fail and a fluent wrong answer with similar wording can pass. The failure categories above come from the saved outputs and not from the score alone.
- It is one run with one seed and 8 unseen terms, so the unseen result is a small sample.
- I used Claude to help write the extended dataset script, the Colab cells and the first draft of this text. I ran all of the code in Colab myself.