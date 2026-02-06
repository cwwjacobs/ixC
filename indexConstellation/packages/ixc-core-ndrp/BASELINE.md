# NDRP v1.0 Baseline Snapshot

Factual inventory of the repository as it exists. Describes current modules, responsibilities, assumptions, configuration, data flow, inputs/outputs, and known limitations without prescribing changes.

## Major Modules and Responsibilities

- **Schema**
  - `schema/entry_schema.json`: Canonical JSON Schema used by the validator and pipeline output.
  - Root-level `entry_schema.json`: Expanded schema variant (includes `raw_source`, `extraction_notes`, `confidence`); not referenced by the pipeline or validator.
  - Placeholder schemas: `schema/metadata_schema.json` and `schema/lfsl_schema.json` exist but are empty.

- **Validator**
  - `validator/validate.py`: Loads `schema/entry_schema.json`, runs structural validation via `jsonschema`, and enforces semantic checks (boolean `meaning_preserved`, non-empty `content`, valid `role`, and forbids `density_goal="high"` with `entropy_class="high"`). Returns exit code `0` when no errors, `1` when errors are found.
  - Top-level `validate.py`: CLI wrapper that forwards to `validator.validate_file`.

- **Extraction (Stage 1)**
  - `extraction/loader.py`: Streams UTF-8 text files line by line, strips whitespace, and drops empty lines.
  - `extraction/classifier.py`: Heuristic mode detector returning one of `instruction | conversation | narrative | reasoning | context | meta | emotion` or intermediate label `other` (not part of the schema) based on keyword lists (reasoning > instruction > narrative > conversation > emotion > meta > other).
  - `extraction/metadata.py`: `ExtractionMetadata` dataclass for source and mode.
  - `extraction/extractor.py`: Wraps lines into `PreNDRPEntry` objects (content + metadata) and exposes `extract_entries_as_dicts` for downstream use.

- **Standardization (Stage 2)**
  - `standardization/unify_style.py`: Normalizes text by trimming and collapsing whitespace.
  - `standardization/rewrite.py`: Builds NDRP entries from preliminary dicts, normalizes content, maps mode to schema enum (fallback to `"context"` if unexpected), sets intent strings per mode, and applies defaults (`role="user"`, `context=None`, `meaning_preserved=True`, `density_goal="high"`, `entropy_class="low"`). Adds `metadata.source_id` when a source is provided.
  - `standardization/persona_templates/`: Contains empty `neutral.json` and `nova.json` placeholders; not used by the pipeline.

- **Enhancement (Stage 3)**
  - `enhancement/enhance.py`: Stub that returns a shallow copy of the standardized entry without modification.
  - Additional placeholder files (`context_clarity.py`, `density_boost.py`, `expand_reasoning.py`) are empty.

- **Pipeline Runner**
  - `scripts/run_pipeline.py`: Orchestrates the three stages. Inserts the repository root into `sys.path`, loads raw lines, extracts preliminary entries with `source` set to the input filename, standardizes, applies the enhancement stub, and writes one JSON object per line to the specified output path (creating parent directories as needed).
  - `scripts/build_dataset.py`: Present but empty.

- **Examples and Output**
  - `examples/sample_raw.txt`: Eight-line sample demonstrating different modes.
  - `examples/example_usage.md`: Walkthrough showing pipeline execution and sample outputs.
  - `output/`: Contains `.gitkeep` and an empty `refined_dataset.jsonl` placeholder.

- **LFSL**
  - `lfsl/encoder.py`, `lfsl/decoder.py`, and `lfsl/lexicon.json` exist as empty stubs; LFSL conversion is not implemented.

## Implicit Assumptions and Hidden Configuration

- Input is expected as UTF-8 plain text with **one logical entry per line**; blank lines are ignored by the loader.
- Mode detection is purely keyword-based:
  - Reasoning markers include “because”, “therefore”, “thus”, “let's think”, etc.; matched first.
  - Instruction markers include “how to”, “please”, “can you”, “what is/are/why/when/where”.
  - Narrative markers include “once upon”, “story”, “there was”.
  - Conversation markers include greetings/thanks with spacing heuristics (e.g., `" hey "`).
  - Emotion markers include “feel”, “happy”, “sad”, “love”, etc.
  - Meta markers reference the conversation (“this conversation”, “our discussion”).
  - Anything unmatched returns `"other"`; `rewrite.py` remaps this non-schema label to `"context"` before validation.
- Default field values applied during standardization: `role="user"`, `context=None`, `meaning_preserved=True`, `density_goal="high"`, `entropy_class="low"`.
- Intent strings are derived solely from the detected mode (e.g., `"instruction"` → “request information or action”).
- `metadata.source_id` is set to the input filename when provided to the extractor; no other metadata is auto-populated.
- Enhancement stage assumes the standardized entry is already acceptable and does not alter content or metadata.
- Validator assumes JSONL input: one JSON object per line; uses `jsonschema` library at runtime.

## Implicit Input/Output Expectations

- **Pipeline input**: Path to a text file; errors out if the file is missing. Expects readable UTF-8 content with line-delimited entries.
- **Pipeline output**: Writes newline-delimited JSON objects to the specified path; creates parent directories automatically; overwrites existing files without prompting.
- **Validator input**: Path to a JSONL file; prints and counts errors per entry; returns non-zero exit code on the first detected issue count.

## Data Flow (Raw Input → Final Output)

1. User runs `python scripts/run_pipeline.py <input.txt> <output.jsonl>`.
2. `run_pipeline.py` reads and strips lines via `extraction.loader.load_raw_lines` (empty lines skipped).
3. Each line is classified by `extraction.classifier.detect_mode`; metadata is attached with `source` set to the input filename.
4. `extract_entries_as_dicts` yields dictionaries (`content`, `source`, `mode`) to the standardization stage.
5. `standardization.rewrite.to_ndrp_entry` normalizes text, maps/normalizes mode, sets intent/defaults, and adds metadata.
6. `enhancement.enhance_entry` copies the entry unchanged (v1 stub).
7. `run_pipeline.py` writes each enhanced entry as a single JSON object per line to the output file.
8. Optional: `python validate.py <output.jsonl>` runs `validator.validate_file`, which performs schema + semantic checks and reports counts.

## Known Limitations, Ambiguities, or Undefined Behavior

- Enhancement stage is non-functional (pass-through); no reasoning expansion, context enrichment, or density tuning occurs.
- Mode detection is heuristic and order-dependent; ambiguous text may be misclassified, and unsupported modes are silently remapped to `"context"`.
- Single-line processing only: multi-line entries, conversation threading, and role detection are not supported.
- All entries are forced to `role="user"` with `meaning_preserved=True`, `density_goal="high"`, `entropy_class="low"` regardless of content.
- Placeholder persona templates, LFSL modules, and schema files exist but are unused and empty.
- Output directory ships with empty placeholders; `output/refined_dataset.jsonl` does not contain sample data.
- Duplicate schemas exist (root `entry_schema.json` vs. `schema/entry_schema.json`); validator exclusively uses the latter.
