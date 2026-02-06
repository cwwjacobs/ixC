"""
ArchiveOrchestrator: Orchestrates exports with fault recovery.
"""

import sqlite3
import json
import os
import sys
import time
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import uuid

from chats_archive.auth import ProtectedLogger, TokenManager
from chats_archive.fetcher import ConversationFetcher, APIStatus
from chats_archive.storage import LocalEncryptedStore


class LockFile:
    """Platform-appropriate file locking."""

    def __init__(self, lock_path: str):
        self.lock_path = Path(lock_path).expanduser()
        self.lock_file = None
        self._lock_acquired = False
        self._fcntl = None
        self._msvcrt = None

        if sys.platform != "win32":
            try:
                import fcntl
                self._fcntl = fcntl
            except ImportError:
                pass
        else:
            try:
                import msvcrt
                self._msvcrt = msvcrt
            except ImportError:
                pass

    def acquire(self, timeout: float = 0.0) -> bool:
        start = time.time()
        while True:
            try:
                self.lock_file = open(self.lock_path, 'w')
                if self._fcntl:
                    self._fcntl.flock(self.lock_file, self._fcntl.LOCK_EX | self._fcntl.LOCK_NB)
                elif self._msvcrt:
                    self._msvcrt.locking(self.lock_file.fileno(), self._msvcrt.LK_NBLCK, 1)
                else:
                    self.lock_file.write(str(os.getpid()))
                    self.lock_file.flush()
                os.chmod(self.lock_path, 0o600)
                self._lock_acquired = True
                return True
            except (IOError, OSError, BlockingIOError):
                self._close_file()
                if timeout <= 0 or (time.time() - start) >= timeout:
                    return False
                time.sleep(0.1)
            except Exception:
                self._close_file()
                return False

    def release(self):
        if not self._lock_acquired:
            return
        try:
            if self._fcntl:
                self._fcntl.flock(self.lock_file, self._fcntl.LOCK_UN)
            elif self._msvcrt:
                self._msvcrt.locking(self.lock_file.fileno(), self._msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
        finally:
            self._close_file()
            self._lock_acquired = False

    def _close_file(self):
        if self.lock_file:
            try:
                self.lock_file.close()
            except Exception:
                pass
            self.lock_file = None

    def __enter__(self):
        if not self.acquire(timeout=5.0):
            raise RuntimeError(f"Could not acquire lock at {self.lock_path}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


class JobTracker:
    """SQLite-based job tracking."""

    def __init__(self, db_path: str = "~/.chats_archive/jobs.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    total_conversations INTEGER DEFAULT 0,
                    successful_conversations INTEGER DEFAULT 0,
                    failed_conversations INTEGER DEFAULT 0,
                    errors TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())[:8]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO jobs (job_id, started_at, status) VALUES (?, ?, ?)",
                (job_id, datetime.utcnow().isoformat(), "pending")
            )
            conn.commit()
        return job_id

    def update_job_status(self, job_id: str, status: str, **kwargs):
        updates = {"status": status}
        updates.update(kwargs)
        if status in ("completed", "failed"):
            updates["completed_at"] = datetime.utcnow().isoformat()
        if "errors" in updates and isinstance(updates["errors"], list):
            updates["errors"] = json.dumps(updates["errors"])

        with sqlite3.connect(self.db_path) as conn:
            for key, value in updates.items():
                conn.execute(f"UPDATE jobs SET {key} = ? WHERE job_id = ?", (value, job_id))
            conn.commit()

    def get_job(self, job_id: str) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
        if not row:
            return None
        return {
            "job_id": row[0], "started_at": row[1], "completed_at": row[2],
            "total_conversations": row[3], "successful_conversations": row[4],
            "failed_conversations": row[5], "errors": json.loads(row[6]) if row[6] else [],
            "status": row[7]
        }

    def get_last_job(self) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 1")
            row = cursor.fetchone()
        if not row:
            return None
        return {
            "job_id": row[0], "started_at": row[1], "completed_at": row[2],
            "total_conversations": row[3], "successful_conversations": row[4],
            "failed_conversations": row[5], "errors": json.loads(row[6]) if row[6] else [],
            "status": row[7]
        }


class ArchiveOrchestrator:
    """Orchestrates exports with resume capability and integrity-aware skipping."""

    def __init__(self, token_manager: TokenManager, archive_dir: str = "~/.chats_archive", logger: Optional[ProtectedLogger] = None):
        self.token_manager = token_manager
        self.archive_dir = archive_dir
        self.logger = logger or ProtectedLogger()
        self.job_tracker = JobTracker()
        self.lock_path = Path(archive_dir).expanduser() / ".lock"

    def run_export(self, resume_job_id: Optional[str] = None, force_refetch: bool = False) -> str:
        try:
            with LockFile(self.lock_path):
                return self._run_export_locked(resume_job_id, force_refetch)
        except RuntimeError as e:
            print(f"❌ {e}")
            raise

    def _run_export_locked(self, resume_job_id: Optional[str] = None, force_refetch: bool = False) -> str:
        if resume_job_id:
            job_id = resume_job_id
            job = self.job_tracker.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            print(f"📋 Resuming job {job_id}")
        else:
            job_id = self.job_tracker.create_job()
            print(f"📋 Created export job {job_id}")

        self.job_tracker.update_job_status(job_id, "in_progress")

        try:
            auth_token = self.token_manager.retrieve_token()
            if not auth_token:
                raise RuntimeError("No auth token available")

            fetcher = ConversationFetcher(auth_token, self.logger)
            store = LocalEncryptedStore(self.archive_dir, self.logger)

            print("🔍 Checking API status...")
            api_status, message = fetcher.validate_api_status()

            if api_status != APIStatus.OK:
                print(f"\n⚠️  API STATUS: {api_status.value.upper()}")
                print(f"   {message}")
                self.job_tracker.update_job_status(job_id, "failed", errors=[f"API {api_status.value}: {message}"])
                return job_id

            if not fetcher.validate_token():
                raise RuntimeError("Auth token validation failed")

            print("✅ Auth token validated")
            print("📥 Fetching conversations...")

            fetch_result = fetcher.fetch_all_conversations()
            conversations_list = fetch_result.get("conversations", [])
            total_conversations = len(conversations_list)

            print(f"📦 Retrieved {total_conversations} conversations")

            successful = 0
            failed = 0
            errors: List[str] = []

            # Split-brain signals (list ok, detail failing)
            detail_failures = 0
            consecutive_detail_failures = 0
            detail_401 = 0
            detail_403 = 0
            detail_404 = 0
            detail_429 = 0

            for i, conv_metadata in enumerate(conversations_list, 1):
                conv_id = conv_metadata.get('id', 'unknown')

                try:
                    # Integrity-aware skip: only skip if stored AND decrypt+checksum verifies
                    if not force_refetch and conv_id != "unknown" and store.has_valid_conversation(conv_id):
                        successful += 1
                        continue

                    full_conv = fetcher.fetch_conversation_detail(conv_id)

                    if full_conv:
                        consecutive_detail_failures = 0

                        # Normalize stored metadata with explicit provenance
                        md = dict(conv_metadata)
                        md["source"] = md.get("source", "fetch")
                        md["job_id"] = job_id

                        if store.store_conversation(full_conv, md):
                            successful += 1
                        else:
                            failed += 1
                            errors.append(f"storage_failed:{conv_id[:8]}")
                            if self.logger:
                                self.logger.log_error("store", f"{conv_id[:8]} storage_failed")
                    else:
                        failed += 1
                        detail_failures += 1
                        consecutive_detail_failures += 1
                        errors.append(f"fetch_failed:{conv_id[:8]}")

                except PermissionError as e:
                    failed += 1
                    detail_failures += 1
                    consecutive_detail_failures += 1
                    msg = str(e).lower()
                    if "401" in msg or "expired" in msg or "invalid" in msg:
                        detail_401 += 1
                    errors.append(f"auth_failed:{conv_id[:8]}")
                    if self.logger:
                        self.logger.log_error("detail_auth", f"{conv_id[:8]} {e}")

                except Exception as e:
                    failed += 1
                    detail_failures += 1
                    consecutive_detail_failures += 1
                    errors.append(f"detail_error:{conv_id[:8]}")
                    if self.logger:
                        self.logger.log_error("detail_exception", f"{conv_id[:8]} {e}")

                if i % 10 == 0:
                    print(f"  ✓ {i}/{total_conversations}")

                # Early warning: persistent detail failure while list succeeded
                if consecutive_detail_failures >= 25:
                    print("\n⚠️  Persistent failures fetching conversation details.")
                    print("   This may indicate token expiry, rate limiting, or endpoint drift.")
                    print("   Suggested actions:")
                    print("     1) Run: chats-archive auth-status")
                    print("     2) Refresh token (auth-setup)")
                    print("     3) If persistent, use: import-json")
                    consecutive_detail_failures = 0  # avoid spamming

            self.job_tracker.update_job_status(
                job_id, "completed",
                total_conversations=total_conversations,
                successful_conversations=successful,
                failed_conversations=failed,
                errors=errors
            )

            print(f"\n✅ Export complete!")
            print(f"   Total: {total_conversations}")
            print(f"   ✓ Successful: {successful}")
            print(f"   ✗ Failed: {failed}")

            if detail_failures:
                print(f"\nℹ️  Detail fetch failures observed: {detail_failures}")
                if detail_401:
                    print("   • Some failures look like auth/token issues (refresh token).")
                if detail_429:
                    print("   • Some failures may be rate limiting (retry later).")
                if detail_404:
                    print("   • Some failures may be missing conversations or endpoint drift.")

            return job_id

        except Exception as e:
            self.job_tracker.update_job_status(job_id, "failed", errors=[str(e)])
            self.logger.log_error("orchestrator", str(e))
            print(f"\n❌ Export failed: {e}")
            raise

    def get_job_status(self, job_id: str) -> Optional[dict]:
        return self.job_tracker.get_job(job_id)

    def get_last_export(self) -> Optional[dict]:
        return self.job_tracker.get_last_job()
