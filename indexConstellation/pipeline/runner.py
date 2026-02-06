#!/usr/bin/env python3
"""
indexConstellation — Unified Pipeline Runner

Chains: NDRP normalization → DiamondScorer quality scoring → filtering → export.

Usage:
    python pipeline/runner.py --input data.json --normalize --score --format anthropic --output training.jsonl
    python pipeline/runner.py --input data.jsonl --score --min-tier gold --output filtered.jsonl
    python pipeline/runner.py --input data.jsonl --validate --output report.json
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add package paths
SUITE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SUITE_ROOT / "packages" / "ndrp"))
sys.path.insert(0, str(SUITE_ROOT / "packages" / "scorer"))


def load_input(input_path: Path) -> List[Dict[str, Any]]:
    """Load JSON or JSONL input."""
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with input_path.open("r", encoding="utf-8") as f:
        content = f.read()

    # Try JSON first
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            # ChatGPT export format or single entry
            if "mapping" in parsed or "conversations" in parsed:
                return [parsed]
            return [parsed]
        return [parsed]
    except json.JSONDecodeError:
        pass

    # Try JSONL
    entries = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON on line {line_no}: {e}", file=sys.stderr)
    return entries


def stage_normalize(entries: List[Dict[str, Any]], source: str = "pipeline") -> List[Dict[str, Any]]:
    """Run NDRP normalization: extract → classify → standardize."""
    try:
        from extraction.extractor import extract_entries_as_dicts
        from standardization.rewrite import to_ndrp_entry
        from enhancement.enhance import enhance_entry
    except ImportError as e:
        print(f"Error: Could not import NDRP modules: {e}", file=sys.stderr)
        print("Ensure packages/ixc-core-ndrp is in the Python path.", file=sys.stderr)
        sys.exit(1)

    normalized = []
    for entry in entries:
        # If entry already has 'content', extract from that
        content = entry.get("content", "")
        if not content and entry.get("text"):
            content = entry["text"]
        if not content:
            content = json.dumps(entry)

        # Run through NDRP stages
        lines = content.splitlines() if content else [""]
        for pre_entry in extract_entries_as_dicts(lines, source=source):
            ndrp_entry = to_ndrp_entry(pre_entry)
            enhanced = enhance_entry(ndrp_entry)
            normalized.append(enhanced)

    return normalized


def stage_validate(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run NDRP validation and hygiene scoring."""
    try:
        from validator.validate import validate_entry
        from validator.aggregation import aggregate_validator_results
    except ImportError as e:
        print(f"Error: Could not import NDRP validator: {e}", file=sys.stderr)
        sys.exit(1)

    findings = []
    entry_results = []
    for idx, entry in enumerate(entries, start=1):
        errors = validate_entry(entry, idx)
        for err in errors:
            findings.append({"entry": idx, "severity": "high", "message": err})
        entry_results.append({"entry": idx, "errors": errors, "valid": len(errors) == 0})

    aggregation = aggregate_validator_results(findings)

    return {
        "entries_checked": len(entries),
        "valid_entries": sum(1 for r in entry_results if r["valid"]),
        "total_findings": len(findings),
        "hygiene_score": aggregation["hygiene_score"],
        "rating": aggregation["rating"],
        "summary": aggregation.get("summary", []),
        "details": entry_results,
    }


def stage_score(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run DiamondScorer v3.0 quality scoring."""
    try:
        from diamond_scorer_v3 import DiamondScorer
    except ImportError as e:
        print(f"Error: Could not import DiamondScorer: {e}", file=sys.stderr)
        print("Ensure packages/ixc-vector is in the Python path.", file=sys.stderr)
        sys.exit(1)

    scorer = DiamondScorer()
    scored = []

    for entry in entries:
        # Score the content field (or full text)
        text = entry.get("content", "") or entry.get("response", "") or entry.get("text", "")
        if not text:
            text = json.dumps(entry)

        result = scorer.score(text)

        # Merge scoring results into entry
        scored_entry = dict(entry)
        scored_entry["ixc_scoring"] = result.to_dict()
        scored_entry["ixc_tier"] = result.tier.value
        scored_entry["ixc_quality_score"] = round(result.quality_score, 2)
        scored_entry["ixc_content_rating"] = result.content_rating.value
        scored_entry["ixc_behavior_flags"] = [f.value for f in result.behavior_flags]
        scored.append(scored_entry)

    return scored


def stage_filter(
    entries: List[Dict[str, Any]],
    min_tier: Optional[str] = None,
    min_hygiene: Optional[int] = None,
    exclude_flags: Optional[List[str]] = None,
    content_rating_max: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter entries based on scoring thresholds."""
    tier_rank = {"💎 DIAMOND": 4, "🥇 GOLD": 3, "🥈 SILVER": 2, "🥉 BRONZE": 1}
    tier_names = {"diamond": "💎 DIAMOND", "gold": "🥇 GOLD", "silver": "🥈 SILVER", "bronze": "🥉 BRONZE"}
    rating_rank = {"✨ CLEAN": 1, "⚠️ MATURE": 2, "🌶️ SUGGESTIVE": 3, "🔥 EXPLICIT": 4}
    rating_names = {"clean": "✨ CLEAN", "mature": "⚠️ MATURE", "suggestive": "🌶️ SUGGESTIVE", "explicit": "🔥 EXPLICIT"}

    filtered = []
    for entry in entries:
        # Tier filter
        if min_tier:
            entry_tier = entry.get("ixc_tier", "🥉 BRONZE")
            min_tier_full = tier_names.get(min_tier.lower(), min_tier)
            if tier_rank.get(entry_tier, 0) < tier_rank.get(min_tier_full, 0):
                continue

        # Flag exclusion
        if exclude_flags:
            entry_flags = entry.get("ixc_behavior_flags", [])
            flag_match = False
            for flag in exclude_flags:
                for ef in entry_flags:
                    if flag.lower() in ef.lower():
                        flag_match = True
                        break
            if flag_match:
                continue

        # Content rating filter
        if content_rating_max:
            entry_rating = entry.get("ixc_content_rating", "✨ CLEAN")
            max_rating_full = rating_names.get(content_rating_max.lower(), content_rating_max)
            if rating_rank.get(entry_rating, 0) > rating_rank.get(max_rating_full, 0):
                continue

        filtered.append(entry)

    return filtered


def stage_export(entries: List[Dict[str, Any]], fmt: str) -> List[Dict[str, Any]]:
    """Convert entries to training format."""
    exported = []

    for entry in entries:
        content = entry.get("content", "")
        instruction = entry.get("instruction", entry.get("intent", ""))
        response = entry.get("response", content)

        if fmt == "anthropic":
            exported.append({
                "messages": [
                    {"role": "user", "content": instruction or content},
                    {"role": "assistant", "content": response},
                ]
            })
        elif fmt == "openai":
            exported.append({
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": instruction or content},
                    {"role": "assistant", "content": response},
                ]
            })
        elif fmt == "alpaca":
            exported.append({
                "instruction": instruction or content,
                "input": "",
                "output": response,
            })
        elif fmt == "sharegpt":
            exported.append({
                "conversations": [
                    {"from": "human", "value": instruction or content},
                    {"from": "gpt", "value": response},
                ]
            })
        elif fmt == "jsonl":
            # Passthrough with ixC metadata
            exported.append(entry)
        else:
            exported.append(entry)

    return exported


def write_output(data: Any, output_path: Path, as_jsonl: bool = True):
    """Write output as JSON or JSONL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        if as_jsonl and isinstance(data, list):
            for item in data:
                json.dump(item, f, ensure_ascii=False)
                f.write("\n")
        else:
            json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Output written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="indexConstellation — Unified Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Full pipeline:
    python pipeline/runner.py --input data.json --normalize --score --format anthropic --output training.jsonl

  Score and filter:
    python pipeline/runner.py --input data.jsonl --score --min-tier gold --output filtered.jsonl

  Validate only:
    python pipeline/runner.py --input data.jsonl --validate --output report.json
        """,
    )
    parser.add_argument("--input", "-i", required=True, help="Input file (JSON or JSONL)")
    parser.add_argument("--output", "-o", required=True, help="Output file")
    parser.add_argument("--normalize", action="store_true", help="Run NDRP normalization")
    parser.add_argument("--validate", action="store_true", help="Run NDRP validation (outputs report)")
    parser.add_argument("--score", action="store_true", help="Run DiamondScorer quality scoring")
    parser.add_argument("--min-tier", choices=["diamond", "gold", "silver", "bronze"], help="Minimum quality tier")
    parser.add_argument("--min-hygiene", type=int, help="Minimum hygiene score (0-100)")
    parser.add_argument("--exclude-flags", help="Comma-separated behavior flags to exclude")
    parser.add_argument("--max-content-rating", choices=["clean", "mature", "suggestive", "explicit"], help="Maximum content rating to include")
    parser.add_argument("--format", "-f", choices=["jsonl", "anthropic", "openai", "alpaca", "sharegpt"], default="jsonl", help="Output format")
    parser.add_argument("--source", default="ixc-pipeline", help="Source identifier for provenance")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    print(f"indexConstellation Pipeline")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print()

    # Load
    entries = load_input(input_path)
    print(f"Loaded {len(entries)} entries")

    # Normalize
    if args.normalize:
        print("\n── Stage: NDRP Normalization ──")
        entries = stage_normalize(entries, source=args.source)
        print(f"  Normalized to {len(entries)} entries")

    # Validate
    if args.validate:
        print("\n── Stage: NDRP Validation ──")
        report = stage_validate(entries)
        print(f"  Checked: {report['entries_checked']}")
        print(f"  Valid: {report['valid_entries']}")
        print(f"  Hygiene: {report['hygiene_score']}/100 ({report['rating']})")
        for line in report.get("summary", []):
            print(f"  → {line}")
        write_output(report, output_path, as_jsonl=False)
        return

    # Score
    if args.score:
        print("\n── Stage: DiamondScorer v3.0 ──")
        entries = stage_score(entries)
        tiers = {}
        for e in entries:
            t = e.get("ixc_tier", "unknown")
            tiers[t] = tiers.get(t, 0) + 1
        for tier, count in sorted(tiers.items()):
            print(f"  {tier}: {count}")

    # Filter
    if args.min_tier or args.exclude_flags or args.max_content_rating:
        print("\n── Stage: Filter ──")
        before = len(entries)
        exclude_flags = args.exclude_flags.split(",") if args.exclude_flags else None
        entries = stage_filter(
            entries,
            min_tier=args.min_tier,
            exclude_flags=exclude_flags,
            content_rating_max=args.max_content_rating,
        )
        print(f"  {before} → {len(entries)} entries (filtered {before - len(entries)})")

    # Export
    if args.format != "jsonl":
        print(f"\n── Stage: Export ({args.format}) ──")
        entries = stage_export(entries, args.format)

    # Write
    print()
    write_output(entries, output_path)
    print(f"Pipeline complete. {len(entries)} entries written.")


if __name__ == "__main__":
    main()
