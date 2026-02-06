import json
from pathlib import Path
import math
import sys


def compute_density(text: str) -> float:
    """
    Computes a density score based on:
    - token/character ratio
    - punctuation frequency
    - average word length
    - compression indicator (lower = denser)

    Output range is normalized to 0.0 – 1.0
    (1.0 = very dense, 0.0 = very sparse)
    """

    if not text or not text.strip():
        return 0.0

    chars = len(text)
    words = text.split()
    word_count = len(words)

    if word_count == 0:
        return 0.0

    avg_word_len = sum(len(w) for w in words) / word_count
    punctuation = sum(text.count(p) for p in ".,;:!?")
    token_ratio = word_count / chars

    # Normalize factors
    token_factor = max(0.0, min(1.0, 1 - token_ratio * 4))
    wordlen_factor = max(0.0, min(1.0, (avg_word_len - 3) / 7))
    punct_factor = max(0.0, min(1.0, punctuation / (word_count + 1)))

    # Composite density score
    density = (token_factor + wordlen_factor + punct_factor) / 3
    return round(density, 4)


def score_file(jsonl_path):
    """
    Computes and prints density scores for each entry.
    """

    jsonl_path = Path(jsonl_path)

    if not jsonl_path.exists():
        print(f"Error: File not found → {jsonl_path}")
        return

    print(f"Computing density scores for: {jsonl_path}\n")

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                print(f"[Entry {i}] JSON ERROR")
                continue

            content = entry.get("content", "")
            density = compute_density(content)
            print(f"[Entry {i}] Density: {density}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python density_score.py <dataset.jsonl>")
        sys.exit(1)

    score_file(sys.argv[1])
