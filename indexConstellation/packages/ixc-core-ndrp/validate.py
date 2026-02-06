#!/usr/bin/env python3
"""
NDRP Validator - CLI Wrapper

This is a thin wrapper around the canonical validator in validator/validate.py.
It provides the same CLI interface for backward compatibility.

Usage:
    python validate.py <dataset.jsonl>
"""
import sys
from pathlib import Path

# Import the canonical validator
from validator.validate import validate_file


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate.py <dataset.jsonl>")
        sys.exit(1)

    jsonl_file = sys.argv[1]
    error_count = validate_file(jsonl_file)
    
    # Exit with appropriate code
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()
