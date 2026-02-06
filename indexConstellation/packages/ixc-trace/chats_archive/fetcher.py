"""
ConversationFetcher: Fetches conversations from ChatGPT's internal API.

Only makes requests to chatgpt.com backend-api (no other external services).
"""

import requests
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from enum import Enum


class APIStatus(Enum):
    """API health status categories."""
    OK = "ok"
    DEPRECATED = "deprecated"
    BLOCKED = "blocked"
    UNREACHABLE = "unreachable"
    UNKNOWN = "unknown"


class ConversationFetcher:
    """
    Fetches conversations from ChatGPT backend-api endpoints.
    
    Requires ChatGPT session bearer token (NOT an sk-* API key).
    """
    
    BASE_URL = "https://chatgpt.com/backend-api"
    
    DEFAULT_BATCH_SIZE = 100
    REQUEST_DELAY_SECONDS = 0.5
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 2
    
    def __init__(self, auth_token: str, logger=None):
        """
        Initialize fetcher with ChatGPT session bearer token.
        
        Args:
            auth_token: Valid ChatGPT session token (NOT an sk-* API key)
            logger: ProtectedLogger instance
        """
        if not auth_token or len(auth_token) < 20:
            raise ValueError("Invalid auth token format")
        
        self.auth_token = auth_token
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {auth_token}',
            'User-Agent': 'chats-archive/1.0'
        })
    
    def validate_api_status(self) -> Tuple[APIStatus, Optional[str]]:
        """Check the health of the ChatGPT backend API."""
        test_url = f"{self.BASE_URL}/conversations?limit=1"
        
        try:
            response = self.session.get(test_url, timeout=10)
            
            if response.status_code == 200:
                if 'deprecated' in response.text.lower():
                    return APIStatus.DEPRECATED, "API endpoint is deprecated"
                return APIStatus.OK, "API responding normally"
            elif response.status_code == 401:
                return APIStatus.BLOCKED, "Authentication failed (token invalid/expired)"
            elif response.status_code == 403:
                return APIStatus.BLOCKED, "Access forbidden"
            elif response.status_code == 429:
                return APIStatus.OK, "API responding (rate limited)"
            elif 500 <= response.status_code < 600:
                return APIStatus.UNREACHABLE, f"Server error {response.status_code}"
            else:
                return APIStatus.UNKNOWN, f"Unexpected status {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return APIStatus.UNREACHABLE, "Network connection failed"
        except requests.exceptions.Timeout:
            return APIStatus.UNREACHABLE, "Request timeout"
        except Exception as e:
            return APIStatus.UNKNOWN, str(e)
    
    def fetch_all_conversations(self, limit: int = None, batch_size: int = None) -> Dict:
        """Fetch all conversations for authenticated user."""
        status, message = self.validate_api_status()
        if status != APIStatus.OK:
            raise RuntimeError(f"API not available: {status.value} - {message}")
        
        batch_size = batch_size or self.DEFAULT_BATCH_SIZE
        all_conversations = []
        offset = 0
        
        if self.logger:
            self.logger.log_event("fetch_started", {"batch_size": batch_size})
        
        start_time = time.time()
        
        while True:
            if limit and len(all_conversations) >= limit:
                break
            
            batch, has_more = self._fetch_batch(offset, batch_size)
            
            if not batch:
                break
            
            all_conversations.extend(batch)
            offset += len(batch)
            time.sleep(self.REQUEST_DELAY_SECONDS)
            
            if not has_more:
                break
        
        duration = time.time() - start_time
        
        if self.logger:
            self.logger.log_fetch(
                conversation_count=len(all_conversations),
                bytes_downloaded=len(json.dumps(all_conversations).encode()),
                duration_s=duration
            )
        
        return {
            "conversations": all_conversations,
            "total": len(all_conversations),
            "offset": offset,
            "limit": batch_size
        }
    
    def _fetch_batch(self, offset: int = 0, limit: int = 100) -> Tuple[List[Dict], bool]:
        """Fetch single batch of conversations."""
        url = f"{self.BASE_URL}/conversations"
        params = {"offset": offset, "limit": limit}
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    conversations = data.get('items', [])
                    return conversations, len(conversations) == limit
                elif response.status_code == 401:
                    raise PermissionError("Auth token invalid or expired")
                elif response.status_code == 429:
                    wait_time = self.INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                    print(f"⏳ Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"API error: {response.status_code}")
            
            except requests.exceptions.Timeout:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.INITIAL_BACKOFF_SECONDS * (2 ** attempt))
                else:
                    raise
        
        return [], False
    
    def fetch_conversation_detail(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full conversation by ID."""
        url = f"{self.BASE_URL}/conversation/{conversation_id}"
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                elif response.status_code == 401:
                    raise PermissionError("Auth token invalid")
                elif response.status_code == 429:
                    time.sleep(self.INITIAL_BACKOFF_SECONDS * (2 ** attempt))
                    continue
            except requests.exceptions.Timeout:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.INITIAL_BACKOFF_SECONDS * (2 ** attempt))
                else:
                    return None
        
        return None
    
    def validate_token(self) -> bool:
        """Validate that auth token is working."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/conversations",
                params={"limit": 1},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
