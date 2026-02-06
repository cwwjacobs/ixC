"""
xiConversationArchiver - A sovereign tool for backing up ChatGPT conversations.

No automation, no hidden state, no silent updates.
"""

__version__ = "1.0.1"
__author__ = "Closure Systems Engineering"
__license__ = "MIT"

from chats_archive.auth import TokenManager, ProtectedLogger
from chats_archive.fetcher import ConversationFetcher, APIStatus
from chats_archive.storage import LocalEncryptedStore
from chats_archive.orchestrator import ArchiveOrchestrator
from chats_archive.models import (
    ConversationMetadata,
    EncryptedConversation,
    ExportJob,
    StorageStats,
)

__all__ = [
    "TokenManager",
    "ProtectedLogger",
    "ConversationFetcher",
    "LocalEncryptedStore",
    "ArchiveOrchestrator",
    "ConversationMetadata",
    "EncryptedConversation",
    "ExportJob",
    "StorageStats",
    "APIStatus",
]
