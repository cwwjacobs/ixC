#!/usr/bin/env python3
"""Standalone CLI wrapper for manual import."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from chats_archive.storage import LocalEncryptedStore
from chats_archive.importer import ManualImporter


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Import from ChatGPT export JSON")
    parser.add_argument("--file", "-f", required=True)
    parser.add_argument("--archive-dir", default="~/.chats_archive")
    
    args = parser.parse_args()
    
    try:
        store = LocalEncryptedStore(args.archive_dir)
        importer = ManualImporter(store)
        count = importer.import_from_file(args.file)
        print(f"\n🎉 Import complete! {count} conversations added.")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
