"""
Pydantic models for ChatGPT conversation archival.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class ConversationMetadata(BaseModel):
    """Metadata for a single conversation"""
    conversation_id: str = Field(..., alias="id")
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_archived: bool = False
    
    class Config:
        allow_population_by_field_name = True
    
    @validator('conversation_id')
    def validate_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("conversation_id must be non-empty string")
        return v


class EncryptedConversation(BaseModel):
    """Stored representation: metadata plaintext, content encrypted"""
    metadata: ConversationMetadata
    encrypted_content: str  # base64-encoded encrypted JSON
    encryption_version: str = "fernet-v1"
    checksum: str
    archived_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0")
    
    class Config:
        arbitrary_types_allowed = True


class ExportJob(BaseModel):
    """Tracks export attempt for resume/retry"""
    job_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_conversations: int = 0
    successful_conversations: int = 0
    failed_conversations: int = 0
    errors: List[str] = Field(default_factory=list)
    status: str = "pending"
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class StorageStats(BaseModel):
    """Statistics about archived conversations"""
    total_conversations: int
    total_size_bytes: int
    oldest_conversation: datetime
    newest_conversation: datetime
    last_export: datetime
