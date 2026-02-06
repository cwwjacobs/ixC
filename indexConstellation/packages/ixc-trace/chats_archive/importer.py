"""
Manual import from ChatGPT export JSON files.
"""

import json
import hashlib
from typing import Dict, Any, List
from datetime import datetime, timezone
from pathlib import Path

from chats_archive.storage import LocalEncryptedStore


class ManualImporter:
    """Imports conversations from ChatGPT export JSON format."""
    
    def __init__(self, store: LocalEncryptedStore):
        self.store = store
    
    def import_from_file(self, json_path: str) -> int:
        """Import conversations from JSON export file."""
        path = Path(json_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {json_path}")
        
        print(f"📂 Reading {path}...")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'conversations' in data:
            conversations = data['conversations']
        elif isinstance(data, list):
            conversations = data
        else:
            raise ValueError("Unexpected JSON structure")
        
        print(f"Found {len(conversations)} conversations in export.")
        
        imported = 0
        for i, conv in enumerate(conversations, 1):
            try:
                if self._import_single_conversation(conv):
                    imported += 1
                if i % 10 == 0:
                    print(f"  Processed {i}/{len(conversations)}...")
            except Exception as e:
                print(f"  ⚠️  Failed to import conversation {i}: {e}")
        
        print(f"\n✅ Successfully imported {imported}/{len(conversations)} conversations.")
        return imported
    
    def _import_single_conversation(self, conv_data: Dict[str, Any]) -> bool:
        """Import a single conversation."""
        conv_id = conv_data.get('id', '')
        if not conv_id:
            conv_hash = hashlib.md5(json.dumps(conv_data, sort_keys=True).encode()).hexdigest()[:16]
            conv_id = f"imp_{conv_hash}"
        
        create_time = conv_data.get('create_time')
        update_time = conv_data.get('update_time')
        
        metadata = {
            'id': conv_id,
            'title': conv_data.get('title', 'Imported Conversation'),
            'created_at': self._timestamp_to_iso(create_time) if create_time else datetime.utcnow().isoformat(),
            'updated_at': self._timestamp_to_iso(update_time) if update_time else datetime.utcnow().isoformat(),
            'is_archived': False,
            'source': 'manual_import'
        }
        
        return self.store.store_conversation(conv_data, metadata)
    
    @staticmethod
    def _timestamp_to_iso(timestamp: float) -> str:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
