"""
Entry extractor for NDRP extraction stage.

Converts raw text lines into preliminary NDRP entries with metadata.
"""
from dataclasses import dataclass, asdict
from typing import Iterable, Optional, Any, Mapping

from .classifier import detect_mode
from .metadata import ExtractionMetadata


@dataclass
class PreNDRPEntry:
    """
    A preliminary NDRP entry created during extraction.
    
    This is an intermediate representation before full standardization.
    It contains the raw content and basic metadata from the extraction stage.
    
    Attributes:
        content: The raw text content
        metadata: Extraction metadata (source, mode, etc.)
    """
    content: str
    metadata: ExtractionMetadata


def extract_entries(
    lines: Iterable[str],
    source: Optional[str] = None
) -> Iterable[PreNDRPEntry]:
    """
    Extract preliminary NDRP entries from raw text lines.
    
    Args:
        lines: Iterable of raw text lines
        source: Optional source identifier for metadata
        
    Yields:
        PreNDRPEntry objects with detected mode and metadata
    """
    for line in lines:
        # Detect mode using classifier
        mode = detect_mode(line)
        
        # Create metadata
        metadata = ExtractionMetadata(
            source=source,
            mode=mode
        )
        
        # Create preliminary entry
        yield PreNDRPEntry(
            content=line,
            metadata=metadata
        )


def extract_entries_as_dicts(
    lines: Iterable[str],
    source: Optional[str] = None
) -> Iterable[dict]:
    """
    Extract preliminary NDRP entries as dictionaries.
    
    This is a convenience function that converts PreNDRPEntry objects
    to flat dictionaries suitable for downstream processing.
    
    Args:
        lines: Iterable of raw text lines
        source: Optional source identifier for metadata
        
    Yields:
        Dictionary representations of preliminary entries
    """
    for entry in extract_entries(lines, source):
        # Convert to a flat dictionary for easier processing
        entry_dict = {
            "content": entry.content,
            "source": entry.metadata.source,
            "mode": entry.metadata.mode,
        }
        yield entry_dict
