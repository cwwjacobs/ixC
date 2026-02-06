#!/usr/bin/env python3
"""Offline, opt-in key rotation for Archivist archives.

WARNING:
- This rewrites encrypted archive files in-place.
- Provide correct keys; incorrect keys can render archives unreadable.
- Always back up the archive directory before running.

Usage:
  python scripts/rotate_key.py --archive-dir ~/.chats_archive --old-key <OLD> --new-key <NEW>
"""

import argparse
import base64
import json
import os
import stat
import hashlib
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet, InvalidToken

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive-dir", default="~/.chats_archive")
    ap.add_argument("--old-key", required=True)
    ap.add_argument("--new-key", required=True)
    args = ap.parse_args()

    archive_dir = Path(args.archive_dir).expanduser()
    conv_dir = archive_dir / "conversations"
    manifest_path = archive_dir / "ARCHIVE.json"

    old_cipher = Fernet(args.old_key.encode())
    new_cipher = Fernet(args.new_key.encode())

    if not conv_dir.exists():
        raise SystemExit(f"No conversations dir found at {conv_dir}")

    rotated = 0
    failed = 0

    for date_dir in conv_dir.iterdir():
        if not date_dir.is_dir():
            continue
        for fp in date_dir.glob("conv-*.enc"):
            try:
                data = json.loads(fp.read_text())
                enc_b64 = data.get("encrypted_content")
                if not enc_b64:
                    failed += 1
                    continue
                decrypted = old_cipher.decrypt(base64.b64decode(enc_b64))
                checksum = hashlib.sha256(decrypted).hexdigest()

                new_enc = new_cipher.encrypt(decrypted)
                data["encrypted_content"] = base64.b64encode(new_enc).decode()
                data["checksum"] = checksum
                data["archived_at"] = data.get("archived_at") or datetime.utcnow().isoformat()

                fp.write_text(json.dumps(data, default=str))
                os.chmod(fp, stat.S_IRUSR | stat.S_IWUSR)
                rotated += 1
            except InvalidToken:
                failed += 1
            except Exception:
                failed += 1

    # Update manifest fingerprint
    new_fp = hashlib.sha256(args.new_key.encode()).hexdigest()[:16]
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            manifest = {}
    manifest.update({
        "version": manifest.get("version") or "1.0",
        "rotated_at": datetime.utcnow().isoformat(),
        "key_fingerprint": new_fp,
    })
    manifest_path.write_text(json.dumps(manifest, indent=2))
    os.chmod(manifest_path, stat.S_IRUSR | stat.S_IWUSR)

    print(f"✅ Rotation complete. Rotated: {rotated}, Failed: {failed}")
    print("NOTE: This script does not update OS keyring. If you used keyring, import the new key accordingly.")

if __name__ == "__main__":
    main()
