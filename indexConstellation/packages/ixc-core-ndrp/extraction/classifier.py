"""
Mode classifier for NDRP extraction stage.

Detects the mode/type of text entries using simple heuristics.
"""
from typing import Literal


ModeType = Literal["instruction", "conversation", "narrative", "reasoning", "context", "meta", "emotion", "other"]


def detect_mode(text: str) -> ModeType:
    """
    Detect the mode of a text entry using simple heuristics.
    
    This is a basic classifier that uses text patterns to determine
    the likely mode of the entry. More sophisticated classification
    can be added in future versions.
    
    Args:
        text: The text to classify
        
    Returns:
        One of: "instruction", "conversation", "narrative", "reasoning",
                "context", "meta", "emotion", "other"
    """
    text_lower = text.lower()
    
    # Reasoning patterns (check first - more specific)
    reasoning_markers = [
        "because", "therefore", "thus", "hence",
        "consequently", "as a result", "this means",
        "let's think", "step by step", "first,", "second,"
    ]
    if any(marker in text_lower for marker in reasoning_markers):
        return "reasoning"
    
    # Instruction patterns
    instruction_markers = [
        "how to", "please", "can you", "could you", "would you",
        "tell me", "show me", "explain", "describe", "define",
        "what is", "what are", "why", "when", "where"
    ]
    if any(marker in text_lower for marker in instruction_markers):
        return "instruction"
    
    # Narrative patterns (check before conversation - more specific)
    narrative_markers = [
        "once upon", "story", "tale", "long ago",
        "there was", "there were", "in the beginning"
    ]
    if any(marker in text_lower for marker in narrative_markers):
        return "narrative"
    
    # Conversation patterns
    conversation_markers = [
        "hello", "hi ", " hey ", "thanks", "thank you",
        "goodbye", "bye", "see you", "nice to"
    ]
    if any(marker in text_lower for marker in conversation_markers):
        return "conversation"
    
    # Emotion patterns
    emotion_markers = [
        "feel", "feeling", "felt", "emotion", "happy", "sad",
        "angry", "excited", "worried", "anxious", "love", "hate"
    ]
    if any(marker in text_lower for marker in emotion_markers):
        return "emotion"
    
    # Meta patterns (discussing the conversation itself)
    meta_markers = [
        "this conversation", "our discussion", "what we're talking about",
        "the topic", "let's change", "back to"
    ]
    if any(marker in text_lower for marker in meta_markers):
        return "meta"
    
    # Default to "other" if no clear pattern is detected
    return "other"
