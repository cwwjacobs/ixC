# Archivist — Secure Conversation Acquisition

**Part of the indexConstellation. Pipeline entry point.**

Local-first CLI tool for exporting, encrypting, verifying, and reading ChatGPT conversations as a long-lived personal archive. Prioritizes correctness, auditability, and failure safety.

## What It Does

- Fetches conversations from ChatGPT API (with resume support)
- Encrypts at rest with Fernet (OS credential manager or local key)
- Verifies integrity on every read (fail-closed)
- Imports from JSON exports (offline)
- Supports key rotation

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[archivist]"

# Verify installation (offline-safe)
chats-archive verify-archive

# Import from JSON export
python scripts/import_from_json.py export.json
```

## Security Model

- Content encrypted at rest (Fernet)
- Wrong keys detected and refused
- Compromised host compromises archive
- Lost keys = unrecoverable data

See `docs/THREAT_MODEL.md` for full analysis.

## Philosophy

Archivist prefers refusal over silent failure.
If integrity, keys, or provenance are uncertain, it stops.
