"""
Text normalization for NDRP standardization stage.

Provides utilities for normalizing text style and formatting.
"""


def normalize_text(text: str) -> str:
    """
    Normalize text by cleaning whitespace and formatting.
    
    This function:
    - Strips leading and trailing whitespace
    - Collapses internal whitespace to single spaces
    - Ensures consistent formatting
    
    Args:
        text: The text to normalize
        
    Returns:
        Normalized text with consistent whitespace
    """
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Collapse internal whitespace to single spaces
    text = " ".join(text.split())
    
    return text
