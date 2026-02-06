#!/usr/bin/env python3
"""Unified CLI entry point for indexConstellation (ixc).

This router is intentionally thin: it provides a single *door* (`ixc <command>`)
while keeping the system modular under `packages/ixc-*`.

Commands currently implemented:
- demo: runs a tiny end-to-end example using the existing pipeline runner.

Other commands are stubbed as help links to the module CLIs/scripts.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SUITE_ROOT = Path(__file__).resolve().parent.parent

def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd, cwd=str(SUITE_ROOT))

def cmd_demo(_: argparse.Namespace) -> int:
    sample = SUITE_ROOT / "apps" / "browser" / "sample.json"
    out = SUITE_ROOT / "out.demo.jsonl"
    return _run([sys.executable, "pipeline/runner.py", "--input", str(sample), "--out", str(out)])

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ixc", description="indexConstellation unified CLI (router).")
    sub = p.add_subparsers(dest="cmd", required=True)

    s_demo = sub.add_parser("demo", help="Run a tiny end-to-end pipeline demo.")
    s_demo.set_defaults(func=cmd_demo)

    for name, help_txt in [
        ("lens", "Lens: verification / diff tools (see packages/ixc-lens/)."),
        ("vector", "Vector: scoring tools (see packages/ixc-vector/)."),
        ("beacon", "Beacon: exporters (see packages/ixc-beacon/)."),
        ("trace", "Trace: archival/provenance tools (see packages/ixc-trace/)."),
    ]:
        s = sub.add_parser(name, help=help_txt)
        s.add_argument("args", nargs=argparse.REMAINDER)
        s.set_defaults(func=lambda ns, n=name: p.error(f"'{n}' is a module namespace. See packages/ixc-{n}/ README."))

    return p

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    return int(ns.func(ns))

if __name__ == "__main__":
    raise SystemExit(main())
