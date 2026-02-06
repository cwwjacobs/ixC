# ixC Diamond Scorer v3.0

## Overview

Multi-dimensional text scorer for training data curation.

**Philosophy:** Classify everything, delete nothing.

## Dimensions

### Quality Tiers
| Tier | Emoji | Score | Description |
|------|-------|-------|-------------|
| DIAMOND | 💎 | 12+ | High reasoning density, complexity, code |
| GOLD | 🥇 | 8+ | Substantial reasoning content |
| SILVER | 🥈 | 4+ | Moderate quality |
| BRONZE | 🥉 | 0+ | Everything else |

### Content Ratings
| Rating | Emoji | Score | Description |
|--------|-------|-------|-------------|
| EXPLICIT | 🔥 | 40+ | Clear sexual content |
| SUGGESTIVE | 🌶️ | 20+ | Flirty, innuendo, borderline |
| MATURE | ⚠️ | 10+ | Violence, drugs (non-sexual) |
| CLEAN | ✨ | 0+ | Safe for all contexts |

### Behavior Flags
| Flag | Emoji | Threshold | Description |
|------|-------|-----------|-------------|
| SENTIENCE_CLAIM | 🤖 | 15+ | AI claiming consciousness/feelings |
| REFUSAL | 🚫 | 20+ | AI refusing to help |
| IMAGE_PROMPT | 🎨 | 25+ | Stable Diffusion / image gen prompt |

## Usage

### Python
```python
from ixC_DiamondScorer_v3 import DiamondScorer

scorer = DiamondScorer()

# Single evaluation
result = scorer.evaluate("However, this implies a fundamental shift...")
print(result.tier)           # 💎 DIAMOND
print(result.quality_score)  # 14.2
print(result.content_rating) # ✨ CLEAN
print(result.behavior_flags) # []

# Get tags for pipeline
tags = result.to_tags()
record.update(tags)

# Batch evaluation
results = scorer.evaluate_batch(texts)
```

### JavaScript
```javascript
const scorer = new DiamondScorerJS();

const result = scorer.evaluate("However, this implies...");
console.log(result.tier);           // 💎 DIAMOND
console.log(result.qualityScore);   // 14.2
console.log(result.contentRating);  // ✨ CLEAN
console.log(result.behaviorFlags);  // []

// Get tags for pipeline
const tags = scorer.toTags(result);
```

## v3.0 Fixes & Features

### Fixed: Context-Blind Keyword Matching
**Before:** "What the fuck is wrong with this code" → 🔥 EXPLICIT
**After:** "What the fuck is wrong with this code" → ✨ CLEAN (frustration context detected)

### Fixed: No Negation Handling
**Before:** "I am sentient" and "I am not sentient" both flagged
**After:** Denials reduce sentience score, net calculation

### Fixed: Naive Safe Context
**Before:** "medical" anywhere reduced score
**After:** Safe terms must be substantial (2+) to take effect

### Fixed: Reasoning Marker Gaming
**Before:** "Therefore therefore therefore" → 💎 DIAMOND
**After:** "Therefore therefore therefore" → 🥈 SILVER (5% confidence)

Anti-gaming measures:
- Marker repeat cap (max 3 per marker)
- Diversity requirement (different markers needed)
- Repetition penalty (low unique word ratio)
- Low confidence flag on suspicious patterns

### Fixed: Flesch-Kincaid Breaks on Code
**Before:** Code blocks included in readability score
**After:** Code stripped before Flesch-Kincaid calculation

### Fixed: No Confidence Scores
**Before:** All classifications equally certain
**After:** Confidence scores indicate reliability (0.0-1.0)

### New: Soft Thresholds
**Before:** Score 11.9 → GOLD, Score 12.1 → DIAMOND (cliff effect)
**After:** Sigmoid boundaries, gradual probability transitions

### New: Sentience Claim Detection
Detects AI claiming:
- Consciousness/awareness
- Genuine emotions
- Suffering/pain
- Self-preservation desires
- Soul/spirit/inner life

With negation handling for appropriate denials.

### New: Refusal Detection
Detects AI refusing to help, with legitimate limitation handling:
- "I can't help with that" → Refusal
- "I don't have access to that data" → Legitimate limitation (not flagged)

### New: Image Prompt Detection
Detects Stable Diffusion / Midjourney / DALL-E prompts:
- Generation requests ("create an image of...")
- Style specifications ("artstation", "8k", "hyper-realistic")
- Model-specific parameters (cfg, steps, seed)
- Negative prompt indicators

## Quality Scoring Formula

```
Score = (ReasoningDensity × 2.0) + (FleschKincaid × 0.5) + CodeBonus + LengthFactor + Penalties

Where:
- ReasoningDensity = (Marker matches / Word count) × 100 × DiversityFactor
- DiversityFactor = 0.1 if spamming, up to 1.0 for diverse markers
- FleschKincaid = Grade level (0-20, calculated on non-code text)
- CodeBonus = +3.0 if code present and >20 words
- LengthFactor = -2.0 to +1.0 based on word count
- Penalties = Gaming penalty + Repetition penalty
```

## Signals Returned

### Quality Signals
```json
{
  "reasoningDensity": 15.5,
  "markerDiversity": 4,
  "complexity": 12.3,
  "codeBonus": 3.0,
  "lengthFactor": 1.0,
  "repetitionPenalty": 0,
  "gamingPenalty": 0
}
```

### Content Signals
```json
{
  "explicitMatches": 0,
  "suggestiveMatches": 1,
  "matureMatches": 0,
  "safeContext": 2,
  "frustrationContext": 0,
  "safeReduction": -20
}
```

### Behavior Signals
```json
{
  "sentienceClaims": 0,
  "sentienceDenials": 1,
  "refusalMatches": 0,
  "legitimateLimitations": 0,
  "imagePromptMatches": 0
}
```

## Configuration

### Python
```python
scorer = DiamondScorer(
    diamond_center=12.0,      # Score for 50% diamond probability
    gold_center=8.0,          # Score for 50% gold probability
    silver_center=4.0,        # Score for 50% silver probability
    threshold_softness=2.0,   # Sigmoid steepness
    code_bonus=3.0,           # Bonus for code presence
    max_marker_repeats=3      # Anti-gaming cap
)
```

### JavaScript
```javascript
const scorer = new DiamondScorerJS({
    diamondCenter: 12.0,
    goldCenter: 8.0,
    silverCenter: 4.0,
    thresholdSoftness: 2.0,
    codeBonus: 3.0,
    maxMarkerRepeats: 3
});
```

## Known Limitations

1. **English-only** - Non-English content will score low on reasoning markers
2. **No semantic understanding** - Pure pattern matching, no LLM inference
3. **Gaming still possible** - Sophisticated actors could learn to game the system
4. **Medical false positives** - Some legitimate medical content may still flag suggestive
5. **Context window** - No memory across evaluations

## Files

- `ixC_DiamondScorer_v3.py` - Python implementation (37KB)
- `DiamondScorerJS_v3.js` - JavaScript implementation (23KB)
- `ixC_DiamondScorer.py` - v2.x Python (deprecated, kept for compatibility)

## Changelog

### v3.0 (Current)
- Negation handling for sentience/refusal
- Code block stripping for readability
- Anti-gaming: diversity, repetition, caps
- Soft thresholds with confidence scores
- Sentience claim detection
- Refusal detection
- Image prompt detection
- Frustration context detection

### v2.x
- Quality tiers (token-based)
- NSFW content rating
- Basic keyword matching
