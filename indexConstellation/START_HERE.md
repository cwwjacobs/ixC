# Start Here — indexConstellation (ixc)

If you just want to *run the system*, follow the golden path:

1) Put a small dataset in `data.json` (or use an existing sample).
2) Run the unified pipeline runner:

```bash
python pipeline/runner.py --input data.json --out out.jsonl
```

3) Export training formats (example):

```bash
node packages/ixc-beacon/training_exporter.js out.jsonl
```

## What’s what

- `packages/ixc-core-ndrp/` — normalization + validation (Core)
- `packages/ixc-vector/` — Diamond scoring (Vector)
- `packages/ixc-lens/` — audit / diff tools (Lens)
- `packages/ixc-beacon/` — exporters (Beacon)
- `packages/ixc-trace/` — archive / provenance tooling (Trace)

For the full conceptual map, see `docs/map.svg`.
