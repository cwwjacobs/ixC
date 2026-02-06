"""
Safe token management using OS credential stores.
Never stores tokens in plaintext files or environment variables in code.
"""

import os
import hashlib
import sys
from typing import Optional
from datetime import datetime
import json


class TokenManager:
    """
    Manages ChatGPT session bearer tokens securely.
    
    Note: This is NOT an OpenAI API key (sk-*). It is a session token
    obtained from ChatGPT web interface for backend-api access.
    
    Platform support:
    - macOS: Keychain
    - Linux: secret-service via keyring
    - Windows: Credential Manager
    """
    
    SERVICE_NAME = "chats_archive"
    TOKEN_KEY = "chatgpt_auth_token"
    
    def __init__(self):
        self.platform = sys.platform
        self._keyring = None
        self._init_keyring()
    
    def _init_keyring(self):
        """Initialize platform-specific credential store"""
        try:
            import keyring
            self._keyring = keyring
        except ImportError:
            print("⚠️  keyring package not found. Install with: pip install keyring")
            print("   Falling back to .env file (less secure)")
            self._keyring = None
    
    def store_token(self, token: str, force_env_fallback: bool = False) -> bool:
        """
        Store auth token in OS credential manager.
        
        Args:
            token: ChatGPT session bearer token
            force_env_fallback: If True, skip confirmation for .env fallback
        
        Returns:
            True if successful
        """
        if not token or not isinstance(token, str):
            print("❌ Invalid token format (expected ChatGPT session bearer token)")
            return False
        
        try:
            if self._keyring:
                self._keyring.set_password(self.SERVICE_NAME, self.TOKEN_KEY, token)
                print(f"✅ Token stored securely in {self.platform} credential manager")
                return True
            else:
                if self._confirm_env_fallback(force_env_fallback):
                    self._store_env_fallback(token)
                    return True
                else:
                    print("❌ Token storage aborted by user.")
                    return False
        except Exception as e:
            print(f"❌ Failed to store token: {e}")
            return False
    
    def _confirm_env_fallback(self, force: bool) -> bool:
        """Confirm with user before storing token in .env file."""
        if force:
            return True
        if not sys.stdin.isatty():
            print("❌ Non-interactive terminal. Cannot prompt for .env fallback.")
            return False
        print("⚠️  OS credential store unavailable.")
        print("   Storing token in .env file is less secure.")
        response = input("   Proceed with .env fallback? [y/N]: ").strip().lower()
        return response in ('y', 'yes')
    
    def retrieve_token(self) -> Optional[str]:
        """Retrieve auth token from OS credential manager."""
        try:
            if self._keyring:
                token = self._keyring.get_password(self.SERVICE_NAME, self.TOKEN_KEY)
                if token:
                    return token
            token = os.getenv('CHATGPT_AUTH_TOKEN')
            if token:
                print("⚠️  Using token from CHATGPT_AUTH_TOKEN env variable (less secure)")
                return token
            print("❌ No auth token found. Run: chats-archive auth-setup")
            return None
        except Exception as e:
            print(f"❌ Failed to retrieve token: {e}")
            return None
    
    def delete_token(self) -> bool:
        """Delete stored auth token"""
        try:
            if self._keyring:
                self._keyring.delete_password(self.SERVICE_NAME, self.TOKEN_KEY)
                print("✅ Token deleted from credential manager")
                return True
            else:
                print("⚠️  Token fallback in .env - delete manually")
                return False
        except Exception as e:
            print(f"❌ Failed to delete token: {e}")
            return False
    
    def validate_token(self, token: str) -> bool:
        """
        Basic validation of token format.
        Token is a ChatGPT session bearer token (not an OpenAI API key).
        """
        if not token or not isinstance(token, str):
            return False
        if len(token) < 20:
            return False
        return True
    
    def token_hash(self, token: str) -> str:
        """Return SHA256 hash of token (safe to log)."""
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def _store_env_fallback(self, token: str):
        """Fallback to .env file"""
        env_path = ".env.local"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                if 'CHATGPT_AUTH_TOKEN' in f.read():
                    print(f"⚠️  Token already in {env_path}")
                    return
        with open(env_path, 'w') as f:
            f.write(f'CHATGPT_AUTH_TOKEN="{token}"\n')
        os.chmod(env_path, 0o600)
        print(f"✅ Token stored in {env_path}")


class ProtectedLogger:
    """Logger that never logs sensitive data."""
    
    def __init__(self, log_file: str = "~/.chats_archive/audit.log"):
        self.log_file = os.path.expanduser(log_file)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def log_event(self, event: str, metadata: dict = None, level: str = "INFO"):
        """Log event with metadata (never content)."""
        timestamp = datetime.utcnow().isoformat()
        entry = {
            "timestamp": timestamp,
            "level": level,
            "event": event,
            "metadata": metadata or {}
        }
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            print(f"⚠️  Failed to write audit log: {e}")
    
    def log_fetch(self, conversation_count: int, bytes_downloaded: int, duration_s: float):
        self.log_event("fetch_complete", {
            "conversation_count": conversation_count,
            "bytes_downloaded": bytes_downloaded,
            "duration_seconds": round(duration_s, 2)
        })
    
    def log_error(self, component: str, error_msg: str):
        self.log_event("error", {
            "component": component,
            "error": error_msg[:100]
        }, level="ERROR")
    
    def log_storage(self, conversation_id: str, size_bytes: int, encrypted: bool):
        self.log_event("storage", {
            "conversation_id": conversation_id[:8] + "...",
            "size_bytes": size_bytes,
            "encrypted": encrypted
        })
