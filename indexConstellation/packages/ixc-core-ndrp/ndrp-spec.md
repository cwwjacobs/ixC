# NDRP Technical Specification (v1.0)

## Overview

The Nova Data Refinement Protocol (NDRP) is a three-stage pipeline for transforming raw, unstructured text into high-density, low-entropy training data that conforms to a unified schema.

## Entry Schema

All NDRP entries must conform to the JSON Schema defined in `schema/entry_schema.json`.

### Required Fields

- **role** (string): One of `"user"`, `"assistant"`, or `"system"`
- **content** (string): The cleaned, structured text content
- **intent** (string): Purpose of the message (free-form description)
- **mode** (string): Message type - one of:
  - `"instruction"` - requests for information or action
  - `"conversation"` - dialogue and social interaction
  - `"narrative"` - stories and descriptive content
  - `"reasoning"` - logical explanations and analysis
  - `"context"` - contextual or background information
  - `"meta"` - discussion about the conversation itself
  - `"emotion"` - emotional expression
- **meaning_preserved** (boolean): Whether the original meaning is retained
- **density_goal** (string): Target information density - `"low"`, `"medium"`, or `"high"`
- **entropy_class** (string): Assessed entropy level - `"low"`, `"medium"`, or `"high"`

### Optional Fields

- **context** (string | null): Additional contextual information
- **reasoning_expanded** (string | null): Expanded reasoning added during enhancement
- **metadata** (object): Additional metadata (source_id, timestamp, persona_style, etc.)

### Semantic Rules

Beyond structural validation, NDRP enforces:

1. **meaning_preserved** must be a boolean (true/false)
2. **content** must be non-empty after whitespace normalization
3. **role** must be exactly one of the allowed values
4. **Density/Entropy coherence**: High density should not coexist with high entropy

## Pipeline Stages

### Stage 1: Extraction

**Purpose**: Identify and isolate meaningful content from raw text.

**Process**:
1. Load raw text lines from input file
2. Detect mode using heuristic classifier
3. Create preliminary entries with metadata
4. Filter out empty lines

**Modules**:
- `extraction/loader.py` - Raw text loading
- `extraction/classifier.py` - Mode detection
- `extraction/metadata.py` - Metadata structures
- `extraction/extractor.py` - Entry creation

### Stage 2: Standardization

**Purpose**: Transform preliminary entries into NDRP-compliant format.

**Process**:
1. Normalize text (whitespace, formatting)
2. Map mode to schema-compliant value
3. Generate intent description based on mode
4. Populate required fields with defaults
5. Add metadata from extraction stage

**Defaults**:
- `role`: "user"
- `density_goal`: "high"
- `entropy_class`: "low"
- `meaning_preserved`: true
- `context`: null

**Modules**:
- `standardization/unify_style.py` - Text normalization
- `standardization/rewrite.py` - NDRP entry creation

### Stage 3: Enhancement

**Purpose**: Improve clarity, density, and coherence (v1: stub).

**Process** (planned for v2+):
1. Expand reasoning where needed
2. Add contextual clarification
3. Resolve contradictions
4. Optimize information density
5. Verify semantic preservation

**Modules**:
- `enhancement/enhance.py` - Enhancement logic (currently pass-through)

## Validation

The canonical validator (`validator/validate.py`) performs:

1. **Structural validation** using JSON Schema
2. **Semantic validation**:
   - Boolean type check for meaning_preserved
   - Non-empty content verification
   - Valid role enumeration
   - Density/entropy coherence check

Exit codes:
- `0` - All entries valid
- `1` - One or more validation errors

## Usage

### Running the Pipeline

```bash
python scripts/run_pipeline.py <input.txt> <output.jsonl>
```

### Validating Output

```bash
python validate.py <dataset.jsonl>
```

## Version History

### v1.0 (Current)

- ✅ Complete entry schema
- ✅ Three-stage pipeline scaffold
- ✅ Extraction with basic mode detection
- ✅ Standardization with text normalization
- ✅ Enhancement stub (pass-through)
- ✅ Schema validation with semantic checks

### Planned for v2+

- [ ] Advanced mode classification (ML-based)
- [ ] Reasoning expansion
- [ ] Context enrichment
- [ ] Contradiction resolution
- [ ] LFSL symbolic conversion
- [ ] Persona-style templates
- [ ] Density scoring
- [ ] Entropy measurement
