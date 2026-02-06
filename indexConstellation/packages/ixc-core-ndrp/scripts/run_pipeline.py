#!/usr/bin/env python3
"""
NDRP Pipeline Runner

This script runs the complete NDRP pipeline from raw text to refined JSONL.

Usage:
    python scripts/run_pipeline.py <input.txt> <output.jsonl>

The pipeline consists of three stages:
1. Extraction - Load raw text and extract preliminary entries
2. Standardization - Transform into NDRP schema with unified formatting
3. Enhancement - Improve clarity, density, and coherence

Output:
    A JSONL file where each line is a complete NDRP entry conforming to
    the schema defined in schema/entry_schema.json
"""
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction.loader import load_raw_lines
from extraction.extractor import extract_entries_as_dicts
from standardization.rewrite import to_ndrp_entry
from enhancement.enhance import enhance_entry


def run_pipeline(input_path: str, output_path: str):
    """
    Run the complete NDRP pipeline.
    
    Args:
        input_path: Path to raw text file
        output_path: Path to output JSONL file
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # Ensure input exists
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🌙 NDRP Pipeline v1.0")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print()
    
    # Extract source name from input path
    source_name = input_path.name
    
    entries_processed = 0
    
    with open(output_path, "w", encoding="utf-8") as out_file:
        print("Stage 1: Extraction...")
        
        # Load raw lines
        raw_lines = load_raw_lines(input_path)
        
        # Extract preliminary entries
        pre_entries = extract_entries_as_dicts(raw_lines, source=source_name)
        
        print("Stage 2: Standardization...")
        
        for pre_entry in pre_entries:
            # Standardize to NDRP format
            ndrp_entry = to_ndrp_entry(pre_entry)
            
            # Stage 3: Enhancement
            enhanced_entry = enhance_entry(ndrp_entry)
            
            # Write to output file
            json.dump(enhanced_entry, out_file)
            out_file.write("\n")
            
            entries_processed += 1
    
    print(f"\n✨ Pipeline complete!")
    print(f"Processed {entries_processed} entries")
    print(f"Output written to: {output_path}")
    print()
    print(f"To validate the output, run:")
    print(f"  python validate.py {output_path}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/run_pipeline.py <input.txt> <output.jsonl>")
        print()
        print("Example:")
        print("  python scripts/run_pipeline.py examples/sample_raw.txt output/refined.jsonl")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    run_pipeline(input_file, output_file)


if __name__ == "__main__":
    main()
