"""
NDRP entry rewriter for standardization stage.

Converts preliminary entries into full NDRP-compliant entries.
"""
from typing import Mapping, Any

from .unify_style import normalize_text


def to_ndrp_entry(pre_entry: Mapping[str, Any]) -> dict:
    """
    Convert a preliminary entry to a full NDRP entry.
    
    This function takes a preliminary entry from the extraction stage
    and transforms it into a complete NDRP entry that conforms to the
    schema defined in schema/entry_schema.json.
    
    Args:
        pre_entry: A dictionary-like preliminary entry with at least
                   'content' and 'mode' fields
                   
    Returns:
        A complete NDRP entry dictionary with all required fields
    """
    # Normalize the content
    content = normalize_text(pre_entry.get("content", ""))
    
    # Get mode from extraction
    mode = pre_entry.get("mode", "other")
    
    # Map mode to a valid schema mode if needed
    # The schema allows: instruction, conversation, narrative, reasoning, context, meta, emotion
    valid_modes = ["instruction", "conversation", "narrative", "reasoning", "context", "meta", "emotion"]
    if mode not in valid_modes:
        mode = "context"  # Default fallback
    
    # Determine intent based on mode
    intent_map = {
        "instruction": "request information or action",
        "conversation": "engage in dialogue",
        "narrative": "tell a story or describe events",
        "reasoning": "explain logic or reasoning",
        "context": "provide contextual information",
        "meta": "discuss the conversation itself",
        "emotion": "express feelings or emotions"
    }
    intent = intent_map.get(mode, "provide information")
    
    # Build the NDRP entry with required fields
    ndrp_entry = {
        "role": "user",  # Default to user; can be overridden by caller
        "content": content,
        "intent": intent,
        "mode": mode,
        "context": None,  # Can be populated in enhancement stage
        "meaning_preserved": True,  # Assumed true for v1
        "density_goal": "high",  # NDRP aims for high density
        "entropy_class": "low",  # NDRP aims for low entropy
    }
    
    # Add optional metadata if present
    if "source" in pre_entry and pre_entry["source"]:
        ndrp_entry["metadata"] = {
            "source_id": pre_entry["source"]
        }
    
    return ndrp_entry
