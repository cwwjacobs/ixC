# NDRP v1.0 Implementation Notes

## Overview

This document describes the v1.0 implementation of the Nova Data Refinement Protocol (NDRP).

## What Was Implemented

### Core Infrastructure

1. **Schema (`schema/entry_schema.json`)**
   - Complete JSON Schema for NDRP entries
   - Required fields: role, content, intent, mode, meaning_preserved, density_goal, entropy_class
   - Optional fields: context, reasoning_expanded, metadata

2. **Canonical Validator (`validator/validate.py`)**
   - Structural validation using JSON Schema
   - Semantic validation:
     - Boolean type for meaning_preserved
     - Non-empty content after normalization
     - Valid role enumeration (user, assistant, system)
     - Density/entropy coherence (high density ≠ high entropy)
   - Returns proper exit codes (0 = success, 1 = errors)

3. **CLI Wrapper (`validate.py`)**
   - Thin wrapper around canonical validator
   - Maintains backward compatibility
   - Same UX: `python validate.py <dataset.jsonl>`

### Pipeline Stages

#### Stage 1: Extraction (`extraction/`)

**Purpose**: Load raw text and create preliminary entries

**Components**:
- `loader.py`: Load text files, filter empty lines
- `classifier.py`: Heuristic mode detection
- `metadata.py`: ExtractionMetadata dataclass
- `extractor.py`: PreNDRPEntry creation

**Mode Detection Heuristics**:
- **instruction**: "can you", "explain", "what is", etc.
- **conversation**: "hello", "hi ", " hey ", "thanks"
- **narrative**: "once upon", "story", "there was"
- **reasoning**: "because", "therefore", "thus"
- **emotion**: "feel", "happy", "sad", "love"
- **meta**: "this conversation", "our discussion"
- **other**: fallback for unmatched patterns

#### Stage 2: Standardization (`standardization/`)

**Purpose**: Transform to NDRP schema format

**Components**:
- `unify_style.py`: Text normalization (whitespace cleanup)
- `rewrite.py`: NDRP entry creation with defaults

**Defaults Applied**:
- `role`: "user"
- `density_goal`: "high"
- `entropy_class`: "low"
- `meaning_preserved`: true
- `context`: null

**Intent Mapping**:
- instruction → "request information or action"
- conversation → "engage in dialogue"
- narrative → "tell a story or describe events"
- reasoning → "explain logic or reasoning"
- emotion → "express feelings or emotions"
- meta → "discuss the conversation itself"
- context → "provide contextual information"

#### Stage 3: Enhancement (`enhancement/`)

**Purpose**: Improve clarity and density (v1: stub)

**Components**:
- `enhance.py`: Pass-through function (enhancement planned for v2)

### Pipeline Runner (`scripts/run_pipeline.py`)

**Usage**: `python scripts/run_pipeline.py <input.txt> <output.jsonl>`

**Flow**:
1. Load raw lines (extraction/loader)
2. Extract preliminary entries (extraction/extractor)
3. Standardize to NDRP format (standardization/rewrite)
4. Enhance (currently pass-through)
5. Write JSONL output

## Testing Summary

### Test Coverage

1. **Unit Testing**:
   - Mode detection tested on all modes
   - Validator tested with valid and invalid entries
   - Exit codes verified (0 for success, 1 for errors)

2. **Integration Testing**:
   - Full pipeline on 8-entry sample
   - Full pipeline on 10-entry comprehensive test
   - All outputs validate successfully

3. **Validation Testing**:
   - Schema compliance
   - Semantic rules (role, density/entropy, boolean types)
   - Empty content detection
   - Exit code correctness

### Test Results

- ✅ Sample data (8 entries): 100% valid
- ✅ Comprehensive test (10 entries): 100% valid
- ✅ Mode detection accuracy: Good for heuristic-based v1
- ✅ No security vulnerabilities (CodeQL scan)
- ✅ No syntax errors

## Known Limitations (v1)

1. **Simple Mode Detection**
   - Uses keyword heuristics, not ML
   - May misclassify ambiguous text
   - "hey" substring matches can cause false positives (mitigated with " hey ")

2. **Single-Line Processing**
   - One entry per line only
   - No multi-line entry support
   - No conversation threading

3. **Stub Enhancement**
   - Enhancement stage is pass-through
   - No reasoning expansion
   - No context enrichment

4. **Fixed Defaults**
   - All entries get role="user"
   - density_goal="high", entropy_class="low" for all
   - No role detection

5. **No LFSL Support**
   - LFSL conversion not implemented
   - Planned for future release

## Design Decisions

### Why Heuristic Mode Detection?

For v1, we prioritized:
- Simplicity and transparency
- No external dependencies
- Easy debugging and modification
- Predictable behavior

ML-based classification planned for v2.

### Why Stub Enhancement?

Enhancement logic requires:
- Sophisticated NLP understanding
- Reasoning expansion capabilities
- Contradiction detection
- Potentially LLM assistance

These features are complex and warrant their own focused development in v2+.

### Why JSONL Format?

JSONL (JSON Lines) is ideal for datasets because:
- One entry per line (streaming-friendly)
- Standard in ML/NLP communities
- Easy to validate, parse, and process
- Compatible with most training frameworks

## Future Roadmap (v2+)

### Planned Enhancements

1. **Advanced Classification**
   - ML-based mode detection
   - Role detection (user vs assistant)
   - Confidence scoring

2. **Real Enhancement**
   - Reasoning expansion using LLM
   - Context enrichment
   - Contradiction resolution
   - Density optimization

3. **LFSL Integration**
   - LFSL encoder/decoder
   - Symbolic compression
   - Grammar validation

4. **Multi-Entry Support**
   - Conversation threading
   - Multi-turn dialogue handling
   - Context propagation

5. **Persona Templates**
   - Nova style
   - Neutral assistant
   - Domain-specific personas

6. **Quality Metrics**
   - Entropy scoring
   - Density measurement
   - Coherence analysis

## Usage Recommendations

### For Best Results

1. **Input Preparation**
   - One logical unit per line
   - Remove unnecessary formatting
   - Keep entries focused and clear

2. **Post-Processing**
   - Review mode assignments
   - Adjust roles if needed (user/assistant/system)
   - Add context manually for important entries

3. **Validation**
   - Always validate output before training
   - Review error messages carefully
   - Fix or remove invalid entries

4. **Integration**
   - Use validated JSONL directly for fine-tuning
   - Consider persona overlays for specific use cases
   - Monitor model behavior after training

## Conclusion

NDRP v1.0 provides a solid foundation for dataset refinement with:
- Complete pipeline infrastructure
- Robust validation
- Clear documentation
- Room for growth

While v1 has limitations (heuristic classification, stub enhancement), it successfully demonstrates the core NDRP concept and provides immediate value for dataset preparation.

Future versions will build on this foundation to deliver the advanced features outlined in the original vision.
