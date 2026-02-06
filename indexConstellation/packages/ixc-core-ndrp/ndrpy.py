#!/usr/bin/env python3
"""
NDRP CLI wrapper (v1)

Thin orchestration layer to validate NDRP data, compute hygiene scores, and
optionally emit a JSON report.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from validator.aggregation import aggregate_validator_results
from validator.validate import validate_entry

# Validation errors do not currently expose severities; map them to "high"
# (10-point weight) for deterministic scoring.
DEFAULT_ERROR_SEVERITY = "high"
REDACTED_PLACEHOLDER = "[REDACTED]"


def _load_entries(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load entries from a JSON or JSONL file.

    Accepts:
    - JSON object (treated as single entry)
    - JSON array of objects
    - JSONL where each non-empty line is an object
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as f:
        raw_content = f.read()

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        entries: List[Dict[str, Any]] = []
        for line_no, line in enumerate(raw_content.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                parsed_line = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc.msg}") from exc
            if not isinstance(parsed_line, dict):
                raise ValueError(f"Entry on line {line_no} must be a JSON object")
            entries.append(parsed_line)
        if not entries:
            raise ValueError("No entries found in input file")
        return entries
    else:
        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, list):
            entries = []
            for idx, item in enumerate(parsed, start=1):
                if not isinstance(item, dict):
                    raise ValueError(f"Entry {idx} in array must be a JSON object")
                entries.append(item)
            if not entries:
                raise ValueError("Input JSON array is empty")
            return entries
        raise ValueError("Input JSON must be an object or array of objects")


def _collect_validation_results(entries: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run existing validation logic on provided entries and return structured
    results annotated with severities. All findings are tagged as "high" to
    align with deterministic hygiene scoring until validators emit severity.
    """
    results: List[Dict[str, Any]] = []

    for index, entry in enumerate(entries, start=1):
        errors = validate_entry(entry, index)
        for err in errors:
            results.append({"entry": index, "severity": DEFAULT_ERROR_SEVERITY, "message": err})

    return results


def _redact_entries(entries: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply a simple redaction pass to sensitive free-text fields.
    """
    redacted: List[Dict[str, Any]] = []
    for entry in entries:
        sanitized = dict(entry)
        for field in ("content", "context", "reasoning_expanded"):
            if field in sanitized:
                sanitized[field] = REDACTED_PLACEHOLDER
        redacted.append(sanitized)
    return redacted


def _print_summary(aggregation: Mapping[str, Any], finding_count: int) -> None:
    print(f"Hygiene Score: {aggregation['hygiene_score']}")
    print(f"Rating: {aggregation['rating']}")
    print(f"Findings: {finding_count}")
    print("Summary:")
    for line in aggregation.get("summary", []):
        print(f"- {line}")


def _write_report(
    report_path: Path,
    input_path: Path,
    entries: List[Dict[str, Any]],
    validator_results: List[Dict[str, Any]],
    aggregation: Mapping[str, Any],
    redacted: bool,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload = _redact_entries(entries) if redacted else entries
    report = {
        "input_path": str(input_path),
        "validator_results": validator_results,
        "aggregation": dict(aggregation),
        "summary": aggregation.get("summary", []),
        "payload": payload,
        "redacted": redacted,
    }

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


def handle_validate(args: argparse.Namespace) -> int:
    try:
        input_path = Path(args.path)
        entries = _load_entries(input_path)
        validator_results = _collect_validation_results(entries)
        aggregation = aggregate_validator_results(validator_results)

        _print_summary(aggregation, len(validator_results))

        if args.output:
            _write_report(
                Path(args.output),
                input_path,
                entries,
                validator_results,
                aggregation,
                args.redact,
            )

        return 0 if not validator_results else 1
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ndrpy", description="NDRP CLI wrapper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate data and compute hygiene score")
    validate_parser.add_argument("path", help="Path to JSON/JSONL input")
    validate_parser.add_argument("--redact", action="store_true", help="Apply redaction to report payload")
    validate_parser.add_argument(
        "--output",
        "-o",
        help="Write JSON report to the provided path",
    )
    validate_parser.set_defaults(func=handle_validate)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
