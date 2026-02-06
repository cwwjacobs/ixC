import json
import jsonschema
from jsonschema import validate
import sys
from pathlib import Path

# Load entry schema
SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "entry_schema.json"

with open(SCHEMA_PATH, "r") as f:
    ENTRY_SCHEMA = json.load(f)


def validate_entry(entry, index):
    """
    Validates a single dataset entry using the NDRP entry schema.
    Returns a list of error strings (empty if valid).
    """
    errors = []

    try:
        validate(instance=entry, schema=ENTRY_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        errors.append(f"[Entry {index}] SCHEMA ERROR: {e.message}")

    # Additional checks beyond JSON Schema:

    # 1. Meaning preservation field should match boolean type
    if not isinstance(entry.get("meaning_preserved"), bool):
        errors.append(f"[Entry {index}] meaning_preserved must be true or false")

    # 2. Density & entropy must be coherent
    if entry.get("density_goal") == "high" and entry.get("entropy_class") == "high":
        errors.append(f"[Entry {index}] High density cannot coexist with high entropy")

    # 3. Content must not be empty
    if not entry.get("content") or entry["content"].strip() == "":
        errors.append(f"[Entry {index}] Content is empty")

    # 4. Role must be valid
    if entry.get("role") not in ["user", "assistant", "system"]:
        errors.append(f"[Entry {index}] Invalid role: {entry.get('role')}")

    return errors


def validate_file(jsonl_path):
    """
    Validates all entries in a .jsonl dataset file.
    Returns the number of errors found.
    """
    jsonl_path = Path(jsonl_path)

    if not jsonl_path.exists():
        print(f"Error: File not found → {jsonl_path}")
        return -1

    print(f"Validating: {jsonl_path}\n")

    total = 0
    valid = 0
    errors_found = 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            total += 1
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                print(f"[Entry {i}] JSON ERROR: Invalid JSON line.")
                errors_found += 1
                continue

            errors = validate_entry(entry, i)

            if errors:
                errors_found += len(errors)
                for err in errors:
                    print(err)
            else:
                valid += 1

    print("\n--- SUMMARY ---")
    print(f"Total entries: {total}")
    print(f"Valid entries: {valid}")
    print(f"Errors found: {errors_found}")
    
    return errors_found


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate.py <dataset.jsonl>")
        sys.exit(1)

    error_count = validate_file(sys.argv[1])
    
    # Return appropriate exit code based on validation results
    sys.exit(0 if error_count == 0 else 1)
