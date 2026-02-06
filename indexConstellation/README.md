# indexConstellation (ixc)

Deterministic modular data curation framework.
Part of the ixcore ecosystem — https://ixcore.io


**Deterministic, auditable dataset curation from raw signal to training-ready export.**

indexConstellation is a local-first pipeline for acquiring, normalizing, scoring, inspecting, and exporting conversation datasets for AI training. Every transformation is explicit, every decision is traceable, and no data leaves your machine unless you choose to send it.

---

## Pipeline

```
Raw conversations / exports
        │
        ▼
┌──────────────┐     Secure acquisition & encrypted archival
│   Archivist  │     ChatGPT API fetch, JSON import, Fernet encryption
└──────┬───────┘     Integrity verification (fail-closed)
       │
       ▼
┌──────────────┐     Extraction → Classification → Standardization → Validation
│     NDRP     │     Mode detection, schema enforcement, hygiene scoring (0–100)
└──────┬───────┘     Deterministic, no ML, fully explainable
       │
       ▼
┌──────────────┐     Quality tiers (💎 Diamond → 🥉 Bronze)
│ DiamondScorer│     Content rating (🔥 Explicit → ✨ Clean)
│    v3.0      │     Behavioral flags (🤖 Sentience, 🚫 Refusal, 🎨 Image prompt)
└──────┬───────┘     Anti-gaming, confidence scores, negation-aware
       │
       ▼
┌──────────────┐     Browser-based, fully local
│  ixCurator   │     Filter by metrics, manual selection
└──────┬───────┘     Human-in-the-loop curation
       │
       ▼
┌──────────────┐     OpenAI, Anthropic, Alpaca, ShareGPT
│   Exporter   │     JSONL, JSON, CSV, SQLite
└──────────────┘     Training-ready output
```

---

## Quick Start

### Score a conversation file

```bash
cd packages/ixc-vector
python diamond_scorer_v3.py score input.jsonl --output scored.jsonl
```

### Run the NDRP validation pipeline

```bash
cd packages/ixc-core-ndrp
python scripts/run_pipeline.py raw_text.txt output/refined.jsonl
python ndrpy.py validate output/refined.jsonl
```

### Use the unified pipeline

```bash
python pipeline/runner.py \
  --input conversations.json \
  --normalize \
  --score \
  --min-tier silver \
  --format anthropic \
  --output training_data.jsonl
```

### Browse conversations in the browser

Open `apps/browser/index.html` — load JSON/JSONL, filter by quality tier, export subsets.

### Curate with ixCurator

Open `apps/curator/index.html` — inspect signal density, filter, select, export.

---

## Repository Structure

```
indexConstellation/
│
├── packages/                    # Core pipeline components
│   ├── archivist/               # Secure conversation acquisition & archival
│   │   ├── chats_archive/       # Core library (fetch, encrypt, store, verify)
│   │   ├── docs/                # Threat model, repair contract
│   │   └── scripts/             # Import, key rotation
│   │
│   ├── ndrp/                    # Normalized Data Refinement Protocol
│   │   ├── extraction/          # Loader, extractor, classifier
│   │   ├── standardization/     # Schema rewrite, text normalization
│   │   ├── validator/           # Validation, aggregation, density, entropy
│   │   ├── enhancement/         # (v2 — enhancement stubs)
│   │   ├── schema/              # Runtime validation schema
│   │   ├── schemas/             # Input/output contract schemas
│   │   └── scripts/             # Pipeline runner
│   │
│   ├── scorer/                  # DiamondScorer v3.0
│   │   ├── diamond_scorer_v3.py # Python implementation
│   │   ├── diamond_scorer_v3.js # JavaScript implementation (browser)
│   │   └── README.md            # Scoring dimensions & formula
│   │
│   ├── auditor/                 # Structure audit tools
│   │   ├── auditor.js           # Exhaustive JSON auditor with provenance
│   │   ├── differ.js            # Dataset diffing
│   │   └── monolith.js          # Monolithic data processor
│   │
│   └── exporter/                # Training format exporters
│       ├── training_exporter.js # OpenAI, Anthropic, Alpaca, ShareGPT
│       └── sqlite_exporter.js   # SQLite export
│
├── apps/                        # User-facing applications
│   ├── browser/                 # Conversation browser (HTML/JS/CSS)
│   │   ├── index.html           # Main application
│   │   ├── styles.css           # Styling
│   │   └── diamondScorer.js     # Browser-side scorer
│   │
│   └── curator/                 # ixCurator (HTML)
│       ├── index.html           # Curation application
│       ├── USER-GUIDE.md        # Detailed usage guide
│       ├── privacy-policy.md    # Privacy policy
│       └── terms-of-service.md  # Terms of service
│
├── pipeline/                    # Unified pipeline orchestration
│   ├── __init__.py
│   └── runner.py                # CLI: normalize → score → filter → export
│
├── docs/                        # Design philosophy & contracts
│   ├── philosophy.md            # "Not all signals are equal" — design principles
│   ├── contracts.md             # NDRP data contracts (v1.0)
│   ├── baseline.md              # NDRP baseline behavior
│   ├── threat_model.md          # Archivist security model
│   ├── verification_report.md   # NDRP verification
│   ├── invariants.md            # Core invariants
│   └── schemas/                 # Reference schemas (YAML)
│
└── tests/                       # Test suite
```

---

## Design Principles

**From [signal-to-dataset-core](docs/philosophy.md):**

- Not all signals are equal
- Not all transformations are safe
- Not all datasets should exist

**Applied as:**

1. **Determinism first** — identical inputs produce identical outputs
2. **Classify everything, delete nothing** — DiamondScorer tags, never discards
3. **Explainability over automation** — every score traces to explicit signals
4. **Local-first** — no data leaves your machine by default
5. **Fail closed** — Archivist refuses on uncertainty; NDRP rejects on schema violation
6. **Human authority** — ixCurator puts the human at the selection gate

---

## Components

### Archivist (packages/ixc-trace)

Encrypted local archival for ChatGPT conversations. Fetches via API, encrypts at rest with Fernet, verifies integrity on every read. Supports offline operations, key rotation, and JSON import.

**Key guarantee:** Wrong keys are detected and refused. Corruption is detected and reported. Silent failure is not possible.

### NDRP (packages/ixc-core-ndrp)

Normalized Data Refinement Protocol. Extracts text, classifies mode (instruction, conversation, reasoning, etc.), standardizes to a strict schema, validates, and scores data hygiene (0–100).

**Key guarantee:** Deterministic. No ML. Every validation failure is explainable.

### DiamondScorer v3.0 (packages/ixc-vector)

Multi-dimensional text scorer with three classification axes:
- **Quality** — Reasoning density × complexity → 💎 Diamond / 🥇 Gold / 🥈 Silver / 🥉 Bronze
- **Content** — NSFW detection with context awareness → 🔥 Explicit / 🌶️ Suggestive / ⚠️ Mature / ✨ Clean
- **Behavior** — AI pattern detection → 🤖 Sentience claims / 🚫 Refusals / 🎨 Image prompts

Anti-gaming: marker diversity required, repetition penalized, confidence scores on every classification.

### ixCurator (apps/curator)

Browser-based, fully local conversation inspector. Computes heuristic signal density, supports filtering and manual selection, exports curated subsets. No backend, no analytics, no tracking.

### Exporter (packages/ixc-beacon)

Converts curated data into standard training formats: OpenAI fine-tuning, Anthropic Messages, Alpaca instruction, ShareGPT conversation. Also exports to SQLite for analysis.

---

## Pipeline Runner

The unified pipeline runner chains components:

```bash
# Full pipeline: normalize → score → filter → export
python pipeline/runner.py \
  --input raw_conversations.json \
  --normalize \
  --score \
  --min-tier silver \
  --min-hygiene 70 \
  --exclude-flags sentience_claim,refusal \
  --format anthropic \
  --output training.jsonl

# Score only
python pipeline/runner.py --input data.jsonl --score --output scored.jsonl

# Validate only  
python pipeline/runner.py --input data.jsonl --validate --output report.json
```

---

## Requirements

**Python components:**
- Python 3.9+
- `jsonschema` (NDRP validation)
- `cryptography` (Archivist encryption)

**Browser components:**
- Any modern browser (no installation needed)

**Optional:**
- Node.js (for running JS exporters/auditor from CLI)

```bash
pip install jsonschema cryptography
```

---

## License

MIT — See individual package LICENSE files for component-specific terms.

---

## Philosophy

> The model is not the product.
> The product is selectively saved, high-value decision artifacts produced during controlled simulation.

**ixC — Intelligence by Clarity.**