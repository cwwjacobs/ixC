# NDRP v1 Example Usage

This document demonstrates how to use NDRP v1 to transform raw text into refined, schema-compliant JSONL.

## Example Workflow

### 1. Prepare Raw Input

Create a text file with your raw data (one entry per line):

```
examples/sample_raw.txt
```

Content:
```
Hello, can you help me understand neural networks?
Please explain how backpropagation works.
I feel excited about learning AI and machine learning.
Once upon a time, there was a small model that learned to predict words.
Because neural networks use gradients, they can learn complex patterns.
What is the difference between supervised and unsupervised learning?
Thank you for your help!
This conversation is really helping me understand the concepts better.
```

### 2. Run the Pipeline

```bash
python scripts/run_pipeline.py examples/sample_raw.txt output/example_refined.jsonl
```

Output:
```
🌙 NDRP Pipeline v1.0
Input:  examples/sample_raw.txt
Output: output/example_refined.jsonl

Stage 1: Extraction...
Stage 2: Standardization...

✨ Pipeline complete!
Processed 8 entries
Output written to: output/example_refined.jsonl

To validate the output, run:
  python validate.py output/example_refined.jsonl
```

### 3. Validate the Output

```bash
python validate.py output/example_refined.jsonl
```

Output:
```
Validating: output/example_refined.jsonl

--- SUMMARY ---
Total entries: 8
Valid entries: 8
Errors found: 0
```

### 4. Inspect the Results

Each line in the output file is a complete NDRP entry:

**Entry 1 (Instruction mode):**
```json
{
    "role": "user",
    "content": "Hello, can you help me understand neural networks?",
    "intent": "request information or action",
    "mode": "instruction",
    "context": null,
    "meaning_preserved": true,
    "density_goal": "high",
    "entropy_class": "low",
    "metadata": {
        "source_id": "sample_raw.txt"
    }
}
```

**Entry 2 (Emotion mode):**
```json
{
    "role": "user",
    "content": "I feel excited about learning AI and machine learning.",
    "intent": "express feelings or emotions",
    "mode": "emotion",
    "context": null,
    "meaning_preserved": true,
    "density_goal": "high",
    "entropy_class": "low",
    "metadata": {
        "source_id": "sample_raw.txt"
    }
}
```

**Entry 3 (Narrative mode):**
```json
{
    "role": "user",
    "content": "Once upon a time, there was a small model that learned to predict words.",
    "intent": "tell a story or describe events",
    "mode": "narrative",
    "context": null,
    "meaning_preserved": true,
    "density_goal": "high",
    "entropy_class": "low",
    "metadata": {
        "source_id": "sample_raw.txt"
    }
}
```

**Entry 4 (Reasoning mode):**
```json
{
    "role": "user",
    "content": "Because neural networks use gradients, they can learn complex patterns.",
    "intent": "explain logic or reasoning",
    "mode": "reasoning",
    "context": null,
    "meaning_preserved": true,
    "density_goal": "high",
    "entropy_class": "low",
    "metadata": {
        "source_id": "sample_raw.txt"
    }
}
```

## Mode Detection Examples

NDRP v1 uses heuristic-based mode detection:

| Input Text | Detected Mode | Reason |
|------------|---------------|--------|
| "Can you explain..." | `instruction` | Question/request pattern |
| "Hello, how are you?" | `conversation` | Greeting pattern |
| "I feel happy about..." | `emotion` | Emotion keyword |
| "Once upon a time..." | `narrative` | Story marker |
| "Because X, therefore Y" | `reasoning` | Logical connective |
| "This conversation is..." | `meta` | Self-referential |
| Other text | `other` or `context` | Default fallback |

## Validation Rules

The validator checks:

1. **Schema compliance**: All required fields present and correctly typed
2. **Non-empty content**: Content field must have text after normalization
3. **Valid role**: Must be "user", "assistant", or "system"
4. **Boolean meaning_preserved**: Must be true or false, not a string
5. **Density/entropy coherence**: High density should not coexist with high entropy

## Next Steps

After generating and validating your NDRP dataset:

1. Use it for fine-tuning language models
2. Apply persona templates (planned for v2)
3. Add enhancement logic for reasoning expansion (planned for v2)
4. Convert to LFSL format (planned for future)

## Tips

- Keep one logical entry per line in your input file
- Empty lines are automatically skipped
- Mode detection is heuristic-based; review and adjust if needed
- All entries default to `role: "user"` - modify in post-processing if needed
