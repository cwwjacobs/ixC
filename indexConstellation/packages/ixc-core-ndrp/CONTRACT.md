# NDRP Data Contracts (v1.0)

Source of truth: `BASELINE.md` and the current pipeline behavior. These contracts describe what the system does **today** without proposing changes.

## Invariants (Guaranteed)

- **Input format**: Pipeline consumes UTF-8 text files, one logical entry per non-empty line (`extraction/loader.py` trims and drops blanks).
- **Extraction output**: Each line becomes a dictionary with `content`, detected `mode`, and optional `source` (filename) before standardization.
- **Mode detection**: Heuristic classifier returns one of `instruction | conversation | narrative | reasoning | context | meta | emotion` or the intermediate label `other`.
- **Mode normalization**: `standardization/rewrite.py` remaps any value outside the schema (including `other`) to `context`.
- **Intent mapping**: Intent strings are derived solely from normalized mode (e.g., `instruction` → “request information or action”).
- **Defaults applied**: Standardization sets `role="user"`, `context=None`, `meaning_preserved=True`, `density_goal="high"`, and `entropy_class="low"` for every entry.
- **Content normalization**: Text is whitespace-normalized (`standardization/unify_style.py`).
- **Metadata propagation**: When a `source` is present, it is emitted as `metadata.source_id`; no other metadata is added automatically.
- **Enhancement stage**: `enhancement/enhance.py` returns the standardized entry unchanged.
- **Validation rules** (`validator/validate.py` on `schema/entry_schema.json`):
  - `content` must be non-empty.
  - `meaning_preserved` must be boolean.
  - `role` must be one of `user/assistant/system`.
  - Validator permits `assistant/system`, but the pipeline emits only `user` and `schemas/output_schema.json` encodes that default.
  - `density_goal="high"` cannot coexist with `entropy_class="high"`.
- **Schemas**: Runtime validation continues to use the existing `schema/entry_schema.json` (singular directory). The new documentation contracts live in `schemas/` (`input_schema.json`, `output_schema.json`) and do not replace the runtime validator schema.

## Non-Guarantees (Not Promised)

- No persona styles, LFSL conversion, or enhancement transforms are applied in v1.
- Mode detection is keyword-based and order-dependent; misclassifications are possible.
- Multi-line entries, conversation threading, and role detection beyond the default `user` are not supported.
- Fields other than `content`, `mode`, and `source` supplied before standardization are ignored (they do not propagate to the output).
- Output density/entropy values are not tuned dynamically; they are fixed defaults.

## Handling of Unexpected Inputs

- **Unknown or intermediate modes**: Any value outside the allowed set (including `"other"`) is converted to `mode="context"` with intent “provide contextual information.”
- **Missing fields**: Absent `content` defaults to an empty string; absent `mode` defaults to `"other"` (ultimately `"context"`). Validation will still reject empty `content`.
- **Additional properties**: Extra fields in pre-standardization inputs are tolerated but dropped; extra fields in outputs are currently permitted by the validator but none are produced by the pipeline.
- **Invalid density/entropy pairing**: Outputs always set `density_goal="high"` and `entropy_class="low"`; if modified, validation will flag the forbidden `high`/`high` combination.
- **Non-boolean meaning_preserved**: Validation emits an error; the pipeline emits `true`.
