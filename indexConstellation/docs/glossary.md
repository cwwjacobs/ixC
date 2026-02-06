# indexConstellation glossary

- **indexConstellation**: The unified suite name. A deterministic modular data curation framework.
- **ixc**: Short technical prefix used for CLI, packages, and schema namespaces.
- **Core**: Shared pipeline + NDRP normalization + orchestration glue.
- **Lens**: Verification / diff / integrity checks (auditing surface).
- **Vector**: Scoring and quality signal generation (ranking surface).
- **Beacon**: Export surfaces (JSONL / training formats / SQLite).
- **Trace**: Archival, provenance, retention, and evidence trail.

## Naming rules (the “gravity well”)

- External door: `ixc <verb>` (single entry point)
- Package prefix: `ixc-*`
- Schema namespace: `ixc.schema.<domain>.v<major>`
