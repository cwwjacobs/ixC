"""
Metadata structures for NDRP extraction stage.

Defines metadata classes used during the extraction process.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExtractionMetadata:
    """
    Metadata collected during the extraction stage.
    
    Attributes:
        source: Optional source identifier (filename, URL, etc.)
        mode: Detected mode of the entry (instruction, conversation, etc.)
    """
    source: Optional[str] = None
    mode: Optional[str] = None
