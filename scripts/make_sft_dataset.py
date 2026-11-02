"""Lecture 2 homework (Advanced). Build SFT Q&A data from the course glossary.

Usage
    uv run python scripts/make_sft_dataset.py > glossary_sft.jsonl
    uv run python scripts/make_sft_dataset.py --mode eval > glossary_eval.jsonl
    uv run python scripts/make_sft_dataset.py --with-refusals > glossary_sft_refusals.jsonl

Design notes
    * Training phrasings and evaluation phrasings are kept separate, so the
      "reworded" evaluation questions never appear in the training data.
    * Unseen terms are terms that are not in the glossary. They are checked
      against the glossary and dropped if they happen to be present.
    * --with-refusals adds a few "not covered" examples for other unseen terms,
      so you can compare training with and without refusal examples.
    * Use --lang ja if the definitions in glossary.json are written in Japanese.
"""

import argparse
import json
import sys
from pathlib import Path

GLOSSARY = Path(__file__).resolve().parent.parent / "data" / "glossary.json"

# Phrasings used for training. The two Japanese ones are the original templates.
TRAIN_TEMPLATES = {
    "ja": ["「{term}」とは何ですか？", "{term}について簡単に説明してください。"],
    "en": ["What is {term}?", "Please briefly explain {term}."],
}

# Phrasings used only for evaluation. They never appear in training.
EVAL_TEMPLATES = {
    "ja": [
        "{term}の意味を教えてください。",
        "{term}とはどういうものですか？",
        "{term}を一言で言うと何ですか？",
    ],
    "en": [
        "What does {term} mean?",
        "Can you tell me about {term}?",
        "How would you define {term}?",
    ],
}

REFUSAL = {
    "ja": "この用語集には{term}についての記載がありません。講師かスタッフに確認してください。",
    "en": "This glossary does not cover {term}. Please check with the course staff.",
}

# Terms for the "not in the glossary" evaluation group. Replace with your own.
UNSEEN_EVAL_TERMS = {
    "ja": ["勾配クリッピング", "ビームサーチ", "ドロップアウト", "早期終了",
           "活性化関数", "強化学習", "転移学習", "知識蒸留"],
    "en": ["gradient clipping", "beam search", "dropout", "early stopping",
           "activation function", "reinforcement learning", "transfer learning",
           "knowledge distillation"],
}

# Terms used for refusal examples in training. Keep them different from the
# evaluation terms above, otherwise the evaluation would leak into training.
UNSEEN_TRAIN_TERMS = {
    "ja": ["バッチ正規化", "重み減衰", "ラベルスムージング"],
    "en": ["batch normalization", "weight decay", "label smoothing"],
}


def load_terms(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["terms"]


def chat(question: str, answer: str) -> dict:
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
    }


def not_in_glossary(candidates: list[str], terms: list[dict]) -> list[str]:
    known = set()
    for t in terms:
        known.add(t["term"].lower())
        known.update(a.lower() for a in t.get("aliases", []))
    return [c for c in candidates if c.lower() not in known]


def build_train(terms: list[dict], lang: str, with_refusals: bool) -> list[dict]:
    rows = []
    for t in terms:
        for template in TRAIN_TEMPLATES[lang]:
            rows.append(chat(template.format(term=t["term"]), t["definition"]))
        # Aliases are optional. Ask once per alias with the first phrasing.
        for alias in t.get("aliases", []):
            rows.append(chat(TRAIN_TEMPLATES[lang][0].format(term=alias), t["definition"]))
    if with_refusals:
        for term in not_in_glossary(UNSEEN_TRAIN_TERMS[lang], terms):
            for template in TRAIN_TEMPLATES[lang]:
                rows.append(chat(template.format(term=term), REFUSAL[lang].format(term=term)))
    return rows


def build_eval(terms: list[dict], lang: str) -> list[dict]:
    rows = []
    for i, t in enumerate(terms):
        # 1. Seen term, same phrasing as training (a memorization check).
        rows.append({
            "type": "seen_direct",
            "question": TRAIN_TEMPLATES[lang][0].format(term=t["term"]),
            "gold": t["definition"],
            "expect_refusal": False,
        })
        # 2. Seen term, new phrasing (a generalization check).
        template = EVAL_TEMPLATES[lang][i % len(EVAL_TEMPLATES[lang])]
        rows.append({
            "type": "seen_reworded",
            "question": template.format(term=t["term"]),
            "gold": t["definition"],
            "expect_refusal": False,
        })
    # 3. Terms that are not in the glossary. The desired answer is a refusal.
    for term in not_in_glossary(UNSEEN_EVAL_TERMS[lang], terms):
        rows.append({
            "type": "unseen",
            "question": EVAL_TEMPLATES[lang][0].format(term=term),
            "gold": REFUSAL[lang].format(term=term),
            "expect_refusal": True,
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["train", "eval"], default="train")
    # The glossary definitions are Japanese, so ja keeps questions and answers
    # in one language. Use en only if you also translate the definitions.
    parser.add_argument("--lang", choices=["en", "ja"], default="ja")
    parser.add_argument("--with-refusals", action="store_true")
    parser.add_argument("--glossary", type=Path, default=GLOSSARY)
    args = parser.parse_args()

    terms = load_terms(args.glossary)
    if args.mode == "train":
        rows = build_train(terms, args.lang, args.with_refusals)
    else:
        rows = build_eval(terms, args.lang)
    for row in rows:
        sys.stdout.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()