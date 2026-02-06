# NDRP — Normalized Data Refinement Protocol

**Part of the indexConstellation.**

Deterministic data hygiene and validation. Extracts, classifies, standardizes, and scores structured data before downstream use.

## Pipeline Stages

1. **Extraction** — Load raw text, detect mode (instruction/conversation/reasoning/etc.)
2. **Standardization** — Transform to strict NDRP schema, normalize whitespace
3. **Enhancement** — (v2 — currently passthrough)
4. **Validation** — JSON Schema enforcement, coherence checks
5. **Scoring** — Data Hygiene Score (0–100) with severity weighting

## Quick Start

```bash
# Run full pipeline
python scripts/run_pipeline.py input.txt output/refined.jsonl

# Validate existing data
python ndrpy.py validate data.json

# With redaction and report
python ndrpy.py validate data.json --redact --output report.json
```

## Design Contracts

See `CONTRACT.md` for guaranteed behaviors, `BASELINE.md` for current pipeline state.

## Key Guarantee

Deterministic. No ML. Every validation failure is explainable.
