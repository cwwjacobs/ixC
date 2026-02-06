LLM Pair Curator (ixCurator)

Local-first tooling for inspecting, filtering, and exporting conversation datasets — without data leakage, accounts, or cloud dependence.

LLM Pair Curator (ixCurator) is a browser-based tool for working with conversation data intended for AI training, evaluation, or analysis. It focuses on structural inspection and signal filtering, not model judgment.

All processing runs locally in your browser by default.

Design Intent (Read This First)

ixCurator is designed to answer one question well:

“Given a large set of conversations, which subsets are structurally useful for downstream work?”

It does not attempt to:

Judge correctness

Score “helpfulness”

Replace human review

Perform semantic or model-based evaluation

The tool is intentionally non-LLM, non-cloud, and explainable by default.

What ixCurator Does

Loads conversation data from JSON or JSONL files

Normalizes multiple conversation schemas automatically

Computes transparent, heuristic metrics about structure and content

Allows filtering based on those metrics

Allows manual selection of conversations

Exports curated subsets in standard formats

All free/local features work offline and do not transmit data.

Input Data

Supported inputs include:

ChatGPT exports

Claude exports

API logs

Any JSON / JSONL file containing message arrays

Supported field variants:

Conversation arrays: messages, conversation, turns

Speaker keys: role, sender

Content keys: content, text, message

Data is normalized in-memory and never modified on disk.

Metrics (Heuristic by Design)
Signal Density (0–10)

A composite, deterministic score intended to approximate information density, not quality or truth.

Factors include:

Vocabulary diversity

Technical token density

Presence of code blocks

Presence of explicit reasoning markers

Penalties for filler / boilerplate language

Length normalization

Important:
Signal density is a filtering heuristic, not an evaluation. A low score does not mean “bad,” only “low signal per token.”

Additional Metrics

Token count (approximate)

Turn count

Code presence

Reasoning markers

Automatically inferred corpus type:

Code

Reasoning

Technical

Creative

Chat

All metrics are computed locally and are fully inspectable.

Selection vs Filtering (Explicit Behavior)

ixCurator supports two distinct curation mechanisms:

Filtering

Uses metric thresholds and checkboxes

Dynamically includes/excludes conversations

Intended for coarse dataset shaping

Selection

Manual, click-based selection of individual conversations

Independent of filters

Intended for deliberate, example-level curation

Current export behavior:
Exports operate on the currently visible (filtered) set. Selection is tracked and displayed but is not yet a standalone export mode.

This is intentional and will be expanded in a future update.

Export Formats

ixCurator supports three export formats:

JSONL (Recommended)

One conversation per line

Training-ready for most LLM pipelines

JSON

Human-readable

Useful for inspection and debugging

CSV

Metadata-only export

Suitable for spreadsheets and analysis

Does not include full message text

Exports include:

Original messages (unchanged)

Computed metrics

Ownership of exported data remains entirely with the user.

Privacy Model (Short, Precise)

No analytics

No tracking

No uploads

No accounts required for local use

No cookies beyond basic session needs (if cloud features are later used)

Local processing means the operator cannot access your data—even in principle.

Optional cloud features (when enabled and paid) are explicit, time-bounded, and auto-deleted.

What This Tool Is Not

ixCurator does not:

Perform semantic evaluation

Detect hallucinations

Decide “good vs bad” responses

Replace annotation or review

Claim dataset correctness or compliance by itself

It is a structural curation aid, not a labeling authority.

Intended Users

Researchers preparing datasets

Engineers cleaning training corpora

Practitioners auditing conversation logs

Anyone who needs defensible dataset filtering without cloud exposure

If you need opaque model judgments, this tool is intentionally not that.

Versioning & Status

This is an early release.

You should expect:

Conservative feature scope

Transparent heuristics

Rapid iteration driven by real usage

Planned (not included yet):

Selection-based export modes

Lightweight structural quality scoring (“Q-Lite”)

Preference-format exports

Philosophy

ixCurator is built on a simple constraint:

If a dataset cannot be explained without invoking a black box, it cannot be defended.

This tool exists to keep dataset curation observable, local, and under user control.
