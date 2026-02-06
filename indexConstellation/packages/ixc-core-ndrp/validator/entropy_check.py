import json
import math
from pathlib import Path
import sys


def shannon_entropy(text: str) -> float:
    """
    Calculates Shannon entropy for a given string.
    """
    if not text:
        return 0.0

    # Frequency of each character
    freq = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1

    total = len(text)
    entropy = 0.0

    for count in freq.values():
        p = count / total
        entropy -= p * math.log2(p)

    return entropy


def classify_entropy(entropy_value: float) -> str:
    """
    Maps numeric entropy to low/medium/high classes.
    These thresholds can be tuned during refinement.
    """
    if entropy_value < 3.0:
        return "low"
    elif entropy_value < 4.5:
        return "medium"
    else:
        return "high"


def check_file(jsonl_path):
    """
    Computes entropy for each dataset entry and compares
    against its declared 'entropy_class'.
    """
    jsonl_path = Path(jsonl_path)

    if not jsonl_path.exists():
        print(f"Error: file not found → {jsonl_path}")
        return

    print(f"Running entropy check on: {jsonl_path}\n")

    total = 0
    mismatches = 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            total += 1
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                print(f"[Entry {i}] JSON ERROR: Could not parse line.")
                continue

            content = entry.get("content", "")
            measured_entropy = shannon_entropy(content)
            measured_class = classify_entropy(measured_entropy)
            declared_class = entry.get("entropy_class", "undefined")

            if measured_class != declared_class:
                mismatches += 1
                print(
                    f"[Entry {i}] ENTROPY MISMATCH → "
                    f"declared: {declared_class} | measured: {measured_class} "
                    f"(entropy={measured_entropy:.2f})"
                )

    print("\n--- SUMMARY ---")
    print(f"Total entries: {total}")
    print(f"Mismatches: {mismatches}")
    print(f"Match rate: {((total - mismatches) / total) * 100:.2f}%")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python entropy_check.py <dataset.jsonl>")
        sys.exit(1)

    check_file(sys.argv[1])
