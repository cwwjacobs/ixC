"""
LocalEncryptedStore: Secure local storage with encryption at rest.

Design goals:
- Confidentiality: conversation content encrypted (Fernet)
- Integrity: checksum verified on read (fail closed)
- Auditability: metadata stored plaintext for indexing (minimized)
- Verifiability: explicit integrity states (VALID/CORRUPT/UNREADABLE/MISSING/UNKNOWN)
"""

import os
import hashlib
import json
import base64
from typing import Optional, List, Dict, Any, Iterator, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from cryptography.fernet import Fernet, InvalidToken
import stat

from chats_archive.models import EncryptedConversation, ConversationMetadata


class IntegrityState(Enum):
    VALID = "valid"
    CORRUPT = "corrupt"          # decrypt ok, checksum mismatch
    UNREADABLE = "unreadable"    # decrypt failed (wrong key/tamper)
    MISSING = "missing"          # no wrapper found for the requested id
    UNKNOWN = "unknown"          # malformed wrapper/unexpected structure


@dataclass(frozen=True)
class IntegrityResult:
    conversation_id: str
    state: IntegrityState
    filepath: Optional[str] = None
    size_bytes: Optional[int] = None
    expected_checksum: Optional[str] = None
    actual_checksum: Optional[str] = None
    error_code: Optional[str] = None


class EncryptionKeyManager:
    """Manages encryption key using OS credential manager."""

    SERVICE_NAME = "chats_archive"
    KEY_NAME = "encryption_key"

    def __init__(self):
        try:
            import keyring
            self.keyring = keyring
        except ImportError:
            self.keyring = None

    def get_or_create_key(self) -> bytes:
        """Get existing encryption key or create new one."""
        if self.keyring:
            stored_key = self.keyring.get_password(self.SERVICE_NAME, self.KEY_NAME)
            if stored_key:
                try:
                    Fernet(stored_key.encode())
                    return stored_key.encode()
                except Exception:
                    pass

        # Check fallback file
        key_file = Path.home() / ".chats_archive" / ".encryption_key"
        if key_file.exists():
            stored_key = key_file.read_text().strip()
            try:
                Fernet(stored_key.encode())
                return stored_key.encode()
            except Exception:
                pass

        # Create new key
        new_key = Fernet.generate_key().decode()

        if self.keyring:
            try:
                self.keyring.set_password(self.SERVICE_NAME, self.KEY_NAME, new_key)
                print("✅ Encryption key stored in OS credential manager")
            except Exception as e:
                print(f"⚠️  Could not store key in credential manager: {e}")
                self._store_key_locally(new_key)
        else:
            self._store_key_locally(new_key)

        return new_key.encode()

    def _store_key_locally(self, key: str):
        """Fallback: store key locally with restricted permissions."""
        key_file = Path.home() / ".chats_archive" / ".encryption_key"
        key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(key_file, 'w') as f:
            f.write(key)
        os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)
        print(f"⚠️  Encryption key stored locally at {key_file}")


class LocalEncryptedStore:
    """Stores conversations locally with encryption at rest, with verifiable integrity."""

    STORAGE_VERSION = "1.1"

    def __init__(self, archive_dir: str = "~/.chats_archive", logger=None):
        self.archive_dir = Path(archive_dir).expanduser()
        self.conversations_dir = self.archive_dir / "conversations"
        self.logger = logger
        self._init_directories()
        self.key_manager = EncryptionKeyManager()
        self.encryption_key = self.key_manager.get_or_create_key()
        self.cipher = Fernet(self.encryption_key)

        # Archive manifest binds this archive to the encryption key fingerprint (non-secret)
        self.key_fingerprint = hashlib.sha256(self.encryption_key).hexdigest()[:16]
        self._manifest_path = self.archive_dir / "ARCHIVE.json"
        self._key_mismatch = False
        self._load_or_init_manifest()

    def _init_directories(self):
        """Create archive directory structure with secure permissions"""
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.archive_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    # -------------------------
    # Storage identity helpers
    # -------------------------

    @staticmethod
    def _file_token(conversation_id: str) -> str:
        """Stable, collision-resistant token for filenames."""
        return hashlib.sha256(conversation_id.encode()).hexdigest()[:16]

    def _iter_archive_files(self, pattern: str = "conv-*.enc") -> Iterator[Path]:
        """Iterate over all archive files regardless of date directory."""
        if not self.conversations_dir.exists():
            return
        for date_dir in self.conversations_dir.iterdir():
            if not date_dir.is_dir():
                continue
            for filepath in date_dir.glob(pattern):
                yield filepath

    def _wrapper_path_for(self, conversation_id: str, date_str: str) -> Path:
        token = self._file_token(conversation_id)
        return (self.conversations_dir / date_str) / f"conv-{token}.enc"

    # -------------------------
    # Write path
    # -------------------------

    def _load_or_init_manifest(self):
        """Create or validate archive manifest (key fingerprint binding)."""
        try:
            if self._manifest_path.exists():
                data = json.loads(self._manifest_path.read_text())
                fp = data.get("key_fingerprint")
                if fp and fp != self.key_fingerprint:
                    self._key_mismatch = True
                    if self.logger:
                        self.logger.log_error("archive_manifest", "Key fingerprint mismatch")
            else:
                manifest = {
                    "version": self.STORAGE_VERSION,
                    "created_at": datetime.utcnow().isoformat(),
                    "key_fingerprint": self.key_fingerprint,
                }
                self._manifest_path.write_text(json.dumps(manifest, indent=2))
                os.chmod(self._manifest_path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception as e:
            # If manifest can't be read/written, prefer safety: mark as mismatch so reads fail closed
            self._key_mismatch = True
            if self.logger:
                self.logger.log_error("archive_manifest", str(e)[:200])

    def _ensure_key_matches_manifest(self) -> bool:
        """Return False if key mismatch detected; used to fail closed."""
        return not getattr(self, "_key_mismatch", False)

    def store_conversation(self, conversation: Dict[str, Any], metadata_dict: Dict[str, Any]) -> bool:
        """Store conversation with encryption."""
        try:
            conversation_json = json.dumps(conversation, default=str)
            conversation_bytes = conversation_json.encode()
            checksum = hashlib.sha256(conversation_bytes).hexdigest()
            encrypted = self.cipher.encrypt(conversation_bytes)
            encrypted_b64 = base64.b64encode(encrypted).decode()

            today = datetime.utcnow().strftime("%Y-%m-%d")
            date_dir = self.conversations_dir / today
            date_dir.mkdir(parents=True, exist_ok=True)

            conv_id = metadata_dict.get('id') or metadata_dict.get('conversation_id', 'unknown')
            if not conv_id or conv_id == "unknown":
                # Safety: still store, but don't pretend it's identifiable
                conv_id = conv_id or "unknown"

            filepath = self._wrapper_path_for(conv_id, today)

            stored_obj = {
                "metadata": metadata_dict,
                "encrypted_content": encrypted_b64,
                "encryption_version": "fernet-v1",
                "checksum": checksum,
                "archived_at": datetime.utcnow().isoformat(),
                "version": self.STORAGE_VERSION
            }

            with open(filepath, 'w') as f:
                json.dump(stored_obj, f, default=str)

            os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)

            if self.logger:
                self.logger.log_storage(conv_id, len(conversation_bytes), True)

            return True
        except Exception as e:
            if self.logger:
                self.logger.log_error("store_conversation", str(e))
            return False

    # -------------------------
    # Verification primitives
    # -------------------------

    def _load_wrapper(self, filepath: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            if self.logger:
                self.logger.log_error("load_wrapper", str(e))
            return None

    def _decrypt_bytes(self, wrapper: Dict[str, Any]) -> Tuple[Optional[bytes], Optional[str]]:
        """Return (decrypted_bytes, error_code)."""
        encrypted_b64 = wrapper.get("encrypted_content", "")
        if not encrypted_b64:
            return None, "WRAPPER_NO_CONTENT"
        try:
            encrypted = base64.b64decode(encrypted_b64)
        except Exception:
            return None, "WRAPPER_B64_DECODE_FAIL"
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted)
            return decrypted_bytes, None
        except InvalidToken:
            return None, "DECRYPT_INVALID_TOKEN"
        except Exception:
            return None, "DECRYPT_FAIL"

    def _verify_wrapper(self, conversation_id: str, filepath: Path, wrapper: Dict[str, Any], return_content: bool = False):
        """Verify wrapper integrity; optionally return decrypted content dict."""
        expected_checksum = wrapper.get("checksum", None)
        decrypted_bytes, err = self._decrypt_bytes(wrapper)
        if decrypted_bytes is None:
            res = IntegrityResult(
                conversation_id=conversation_id,
                state=IntegrityState.UNREADABLE if err else IntegrityState.UNKNOWN,
                filepath=str(filepath),
                size_bytes=filepath.stat().st_size if filepath.exists() else None,
                expected_checksum=expected_checksum,
                actual_checksum=None,
                error_code=err or "VERIFY_UNKNOWN"
            )
            return res, None

        actual_checksum = hashlib.sha256(decrypted_bytes).hexdigest()
        if expected_checksum and actual_checksum != expected_checksum:
            if self.logger:
                self.logger.log_error("checksum_mismatch", f"{conversation_id[:8]} expected != actual")
            res = IntegrityResult(
                conversation_id=conversation_id,
                state=IntegrityState.CORRUPT,
                filepath=str(filepath),
                size_bytes=filepath.stat().st_size if filepath.exists() else None,
                expected_checksum=expected_checksum,
                actual_checksum=actual_checksum,
                error_code="CHECKSUM_MISMATCH"
            )
            return res, None

        res = IntegrityResult(
            conversation_id=conversation_id,
            state=IntegrityState.VALID,
            filepath=str(filepath),
            size_bytes=filepath.stat().st_size if filepath.exists() else None,
            expected_checksum=expected_checksum,
            actual_checksum=actual_checksum,
            error_code=None
        )

        if not return_content:
            return res, None

        try:
            return res, json.loads(decrypted_bytes.decode())
        except Exception:
            return IntegrityResult(
                conversation_id=conversation_id,
                state=IntegrityState.UNKNOWN,
                filepath=str(filepath),
                size_bytes=filepath.stat().st_size if filepath.exists() else None,
                expected_checksum=expected_checksum,
                actual_checksum=actual_checksum,
                error_code="JSON_DECODE_FAIL"
            ), None

    # -------------------------
    # Lookup helpers (new + legacy)
    # -------------------------

    def _find_by_new_token(self, conversation_id: str) -> Optional[Path]:
        token = self._file_token(conversation_id)
        for fp in self._iter_archive_files(f"conv-{token}.enc"):
            return fp
        return None

    def _find_by_legacy_prefix(self, conversation_id: str) -> Optional[Path]:
        prefix = conversation_id[:8]
        for fp in self._iter_archive_files(f"conv-{prefix}*.enc"):
            return fp
        return None

    def _find_by_metadata_scan(self, conversation_id: str) -> Optional[Path]:
        for fp in self._iter_archive_files("conv-*.enc"):
            wrapper = self._load_wrapper(fp)
            if not wrapper:
                continue
            md = wrapper.get("metadata", {})
            cid = md.get("id") or md.get("conversation_id")
            if cid == conversation_id:
                return fp
        return None

    def find_wrapper_path_for_conversation(self, conversation_id: str) -> Optional[Path]:
        """Best-effort: new scheme -> legacy prefix -> metadata scan."""
        return (
            self._find_by_new_token(conversation_id)
            or self._find_by_legacy_prefix(conversation_id)
            or self._find_by_metadata_scan(conversation_id)
        )

    # -------------------------
    # Public verification API (C1)
    # -------------------------

    # -------------------------
    # Public verification API (C1)
    # -------------------------

    def verify_conversation(self, conversation_id: str) -> IntegrityResult:
        """Verify integrity of a stored conversation without returning content."""
        if not self._ensure_key_matches_manifest():
            return IntegrityResult(
                conversation_id=conversation_id,
                state=IntegrityState.UNREADABLE,
                error_code="WRONG_KEY_MANIFEST_MISMATCH"
            )

        filepath = self.find_wrapper_path_for_conversation(conversation_id)
        if not filepath:
            return IntegrityResult(
                conversation_id=conversation_id,
                state=IntegrityState.MISSING,
                error_code="NOT_FOUND"
            )

        wrapper = self._load_wrapper(filepath)
        if not wrapper:
            return IntegrityResult(
                conversation_id=conversation_id,
                state=IntegrityState.UNKNOWN,
                filepath=str(filepath),
                error_code="WRAPPER_LOAD_FAIL"
            )

        result, _ = self._verify_wrapper(conversation_id, filepath, wrapper, return_content=False)
        return result

    def has_valid_conversation(self, conversation_id: str) -> bool:
        """Check if conversation exists AND passes integrity verification."""
        result = self.verify_conversation(conversation_id)
        return result.state == IntegrityState.VALID

    def retrieve_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt conversation content (fails closed on integrity issues)."""
        if not self._ensure_key_matches_manifest():
            if self.logger:
                self.logger.log_error("retrieve_conversation", "WRONG_KEY_MANIFEST_MISMATCH")
            return None

        filepath = self.find_wrapper_path_for_conversation(conversation_id)
        if not filepath:
            return None

        wrapper = self._load_wrapper(filepath)
        if not wrapper:
            return None

        result, content = self._verify_wrapper(conversation_id, filepath, wrapper, return_content=True)

        if result.state != IntegrityState.VALID:
            if self.logger:
                self.logger.log_error("retrieve_conversation", f"{conversation_id[:8]} {result.state.value}")
            return None

        return content

    def get_archive_stats(self) -> Dict[str, Any]:
        """Return archive statistics."""
        conversation_ids = set()
        total_size = 0
        oldest_date = None
        newest_date = None

        for filepath in self._iter_archive_files():
            wrapper = self._load_wrapper(filepath)
            if wrapper:
                md = wrapper.get("metadata", {})
                cid = md.get("id") or md.get("conversation_id")
                if cid:
                    conversation_ids.add(cid)
            total_size += filepath.stat().st_size

            date_dir = filepath.parent
            if date_dir.name:
                try:
                    dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                    if not oldest_date or dir_date < oldest_date:
                        oldest_date = dir_date
                    if not newest_date or dir_date > newest_date:
                        newest_date = dir_date
                except ValueError:
                    pass

        return {
            "total_conversations": len(conversation_ids),
            "total_size_bytes": total_size,
            "oldest_conversation": oldest_date or datetime.utcnow(),
            "newest_conversation": newest_date or datetime.utcnow(),
            "last_export": datetime.utcnow()
        }
