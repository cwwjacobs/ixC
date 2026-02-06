"""
Raw data loader for NDRP extraction stage.

Provides utilities for loading raw text files and preparing them
for entry extraction.
"""
from pathlib import Path
from typing import Iterable, Union


def load_raw_lines(path: Union[str, Path]) -> Iterable[str]:
    """
    Load raw lines from a text file, yielding non-empty lines.
    
    Args:
        path: Path to the text file to load
        
    Yields:
        Non-empty lines from the file, with leading/trailing whitespace stripped
    """
    path = Path(path)
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:  # Only yield non-empty lines
                yield line
