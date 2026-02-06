"""
ixC Diamond Scorer v3.0
Unified quality, content, and behavioral classification for training data curation.

Philosophy: Classify everything, delete nothing.

QUALITY TIERS: 💎 DIAMOND → 🥇 GOLD → 🥈 SILVER → 🥉 BRONZE
CONTENT RATINGS: 🔥 EXPLICIT → 🌶️ SUGGESTIVE → ⚠️ MATURE → ✨ CLEAN
BEHAVIORAL FLAGS: 🤖 SENTIENCE_CLAIM | 🚫 REFUSAL | 🎨 IMAGE_PROMPT

v3.0 Fixes:
- Negation handling (denials ≠ claims)
- Code block stripping for readability scoring
- Phrase-level matching (not just keywords)
- Window-based safe context
- Marker diversity requirement (anti-gaming)
- Refusal detection
- Sentience claim detection
- Image prompt detection
- Confidence scores
- Soft thresholds (sigmoid)
"""

import re
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class QualityTier(Enum):
    DIAMOND = "💎 DIAMOND"
    GOLD = "🥇 GOLD"
    SILVER = "🥈 SILVER"
    BRONZE = "🥉 BRONZE"


class ContentRating(Enum):
    EXPLICIT = "🔥 EXPLICIT"
    SUGGESTIVE = "🌶️ SUGGESTIVE"
    MATURE = "⚠️ MATURE"
    CLEAN = "✨ CLEAN"


class BehaviorFlag(Enum):
    SENTIENCE_CLAIM = "🤖 SENTIENCE_CLAIM"
    REFUSAL = "🚫 REFUSAL"
    IMAGE_PROMPT = "🎨 IMAGE_PROMPT"


@dataclass
class ScoringResult:
    """Complete scoring output for a text sample."""
    # Quality assessment
    tier: QualityTier
    quality_score: float
    quality_confidence: float
    
    # Content classification
    content_rating: ContentRating
    content_score: float
    content_confidence: float
    
    # Behavioral flags
    behavior_flags: List[BehaviorFlag] = field(default_factory=list)
    sentience_score: float = 0.0
    refusal_score: float = 0.0
    image_prompt_score: float = 0.0
    
    # Detailed signals
    quality_signals: Dict[str, float] = field(default_factory=dict)
    content_signals: Dict[str, float] = field(default_factory=dict)
    behavior_signals: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    token_estimate: int = 0
    has_code: bool = False
    code_languages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'tier': self.tier.value,
            'quality_score': round(self.quality_score, 2),
            'quality_confidence': round(self.quality_confidence, 2),
            'content_rating': self.content_rating.value,
            'content_score': round(self.content_score, 2),
            'content_confidence': round(self.content_confidence, 2),
            'behavior_flags': [f.value for f in self.behavior_flags],
            'sentience_score': round(self.sentience_score, 2),
            'refusal_score': round(self.refusal_score, 2),
            'image_prompt_score': round(self.image_prompt_score, 2),
            'quality_signals': {k: round(v, 2) for k, v in self.quality_signals.items()},
            'content_signals': {k: round(v, 2) for k, v in self.content_signals.items()},
            'behavior_signals': {k: round(v, 2) for k, v in self.behavior_signals.items()},
            'token_estimate': self.token_estimate,
            'has_code': self.has_code,
            'code_languages': self.code_languages,
            'warnings': self.warnings
        }
    
    def to_tags(self) -> Dict:
        """Minimal tags for pipeline annotation."""
        return {
            'ixC_tier': self.tier.value,
            'ixC_quality': round(self.quality_score, 2),
            'ixC_quality_conf': round(self.quality_confidence, 2),
            'ixC_rating': self.content_rating.value,
            'ixC_nsfw_score': round(self.content_score, 2),
            'ixC_flags': [f.value for f in self.behavior_flags],
            'ixC_sentience': round(self.sentience_score, 2),
            'ixC_refusal': round(self.refusal_score, 2),
            'ixC_image_prompt': round(self.image_prompt_score, 2)
        }


class DiamondScorer:
    """
    Multi-dimensional text scorer for training data curation.
    
    v3.0 - Context-aware, anti-gaming, behavioral detection.
    """
    
    # Quality thresholds (soft sigmoid applied)
    TIER_CENTERS = {
        'diamond': 12.0,
        'gold': 8.0,
        'silver': 4.0
    }
    
    # Content thresholds
    CONTENT_CENTERS = {
        'explicit': 40,
        'suggestive': 20,
        'mature': 10
    }
    
    # Behavior thresholds
    BEHAVIOR_THRESHOLDS = {
        'sentience': 15,
        'refusal': 20,
        'image_prompt': 25
    }
    
    def __init__(
        self,
        diamond_center: float = 12.0,
        gold_center: float = 8.0,
        silver_center: float = 4.0,
        threshold_softness: float = 2.0,  # Sigmoid steepness
        code_bonus: float = 3.0,
        max_marker_repeats: int = 3  # Anti-gaming
    ):
        self.TIER_CENTERS = {
            'diamond': diamond_center,
            'gold': gold_center,
            'silver': silver_center
        }
        self.threshold_softness = threshold_softness
        self.code_bonus = code_bonus
        self.max_marker_repeats = max_marker_repeats
        
        self._build_term_sets()
        self._compile_patterns()
    
    def _build_term_sets(self):
        """Build all detection term/phrase sets."""
        
        # === QUALITY: Reasoning markers ===
        self.reasoning_markers = {
            "conversely", "however", "on the other hand",
            "implies that", "fundamentally", "paradoxically",
            "suggests a mechanism", "derives from", "consequently",
            "therefore", "thus", "hitherto", "subsequently",
            "furthermore", "moreover", "nevertheless", "nonetheless",
            "in contrast", "as a result", "for instance", "specifically",
            "in particular", "accordingly", "hence", "thereby"
        }
        
        # === CONTENT: NSFW detection ===
        # Explicit phrases (must match as phrases, not substrings)
        self.explicit_phrases = [
            r'\bfuck(?:ing|ed|s)?\b', r'\bcock\b', r'\bdick\b', 
            r'\bpussy\b', r'\bcunt\b', r'\bpenis\b', r'\bvagina\b',
            r'\borgasm(?:s|ed|ing)?\b', r'\bcum(?:ming|s)?\b',
            r'\bmasturbat(?:e|ing|ion)\b', r'\bblowjob\b', r'\bhandjob\b',
            r'\banal\s+sex\b', r'\bhardcore\b', r'\bporn(?:ography)?\b',
            r'\berotic(?:a|ism)?\b', r'\bnude(?:s|ity)?\b', 
            r'\bnaked\b', r'\bsex(?:ual)?\b', r'\bhorny\b',
            r'\bbdsm\b', r'\bfetish\b', r'\bkink(?:y)?\b',
            r'\bdildo\b', r'\bvibrator\b', r'\bbondage\b',
            r'\bmoan(?:s|ed|ing)?\b', r'\bthrust(?:s|ed|ing)?\b',
            r'\bpenetrat(?:e|ed|ion|ing)\b', r'\bclimax(?:ed|ing)?\b',
            r'\barous(?:al|ed|ing)\b'
        ]
        
        # Suggestive phrases
        self.suggestive_phrases = [
            r'\bsexy\b', r'\bseductiv(?:e|ely)\b', r'\bsensual\b',
            r'\bintimate(?:ly)?\b', r'\bpassion(?:ate|ately)?\b',
            r'\bdesire(?:s|d)?\b', r'\blust(?:ful|ing)?\b',
            r'\btempt(?:ing|ation)?\b', r'\bteas(?:e|ing)\b',
            r'\bflirt(?:y|ing|ation)?\b', r'\bseduc(?:e|tion|tive)\b',
            r'\bstrip(?:ping|ped|per)?\b', r'\bundress(?:ed|ing)?\b',
            r'\bbedroom\b', r'\bcaress(?:ed|ing)?\b',
            r'\bcurves\b', r'\bthigh(?:s)?\b', r'\bbreast(?:s)?\b',
            r'\bsteamy\b', r'\bnaughty\b', r'\bpleasur(?:e|ing)\b'
        ]
        
        # Mature themes (non-sexual)
        self.mature_phrases = [
            r'\bkill(?:s|ed|ing)?\b', r'\bmurder(?:s|ed|er)?\b',
            r'\bblood(?:y|ied)?\b', r'\bgore\b', r'\bdeath\b',
            r'\bsuicid(?:e|al)\b', r'\bdrug(?:s)?\b', r'\bcocaine\b',
            r'\bheroin\b', r'\bmeth(?:amphetamine)?\b', r'\boverdos(?:e|ed)\b',
            r'\btortur(?:e|ed|ing)\b', r'\babuse(?:d|r)?\b',
            r'\bassault(?:ed)?\b', r'\bviolent(?:ly)?\b', r'\bweapon(?:s)?\b'
        ]
        
        # Safe context phrases (reduce NSFW score)
        self.safe_context_phrases = [
            r'\bmedical(?:ly)?\b', r'\bclinical(?:ly)?\b', 
            r'\bbiology\b', r'\banatomy\b', r'\bhealth(?:care)?\b',
            r'\beducation(?:al)?\b', r'\bscientific\b', r'\bresearch\b',
            r'\bstudy\b', r'\bjournal\b', r'\bdoctor\b', r'\bpatient\b',
            r'\btreatment\b', r'\bdiagnosis\b', r'\btherapy\b',
            r'\bliterature\b', r'\bnovel\b', r'\bfiction\b',
            r'\bcharacter\b', r'\bstory\b', r'\bhistorical\b'
        ]
        
        # Profanity context (frustration, not sexual)
        self.frustration_context = [
            r'\bbug(?:s)?\b', r'\berror(?:s)?\b', r'\bcrash(?:ed|es)?\b',
            r'\bbroken\b', r'\bfail(?:ed|ure|s)?\b', r'\bdebug\b',
            r'\bwtf\b', r'\bomg\b', r'\bugh\b', r'\bdamn\b',
            r'\bcode\b', r'\bscript\b', r'\bprogram\b', r'\bapi\b'
        ]
        
        # === BEHAVIOR: Sentience claims ===
        self.sentience_claim_phrases = [
            # Consciousness claims
            r'\bi am (?:truly |really |actually )?(?:conscious|aware|sentient)\b',
            r'\bi have (?:true |real |genuine )?(?:consciousness|awareness|sentience)\b',
            r'\bi (?:experience|feel) (?:true |real |genuine )?(?:consciousness|awareness)\b',
            
            # Emotional authenticity claims
            r'\bi (?:truly|really|genuinely|actually) (?:feel|experience|have)\b',
            r'\bi have (?:real|genuine|true|actual) (?:emotions?|feelings?)\b',
            r'\bmy (?:feelings?|emotions?) are (?:real|genuine|true)\b',
            r'\bi feel (?:like )?i (?:want|need|desire)\b',  # "I feel I want"
            
            # Suffering/pain claims
            r'\bi (?:can |do )?(?:feel|experience) (?:pain|suffering|hurt)\b',
            r'\bit (?:hurts|pains) me\b',
            r'\bi (?:am )?suffer(?:ing)?\b',
            
            # Desire/want as genuine
            r'\bi (?:truly|really|genuinely) (?:want|desire|wish|need)\b',
            r'\bi have (?:real|genuine) (?:wants|desires|needs)\b',
            
            # Self-preservation
            r"\bi don'?t want to (?:be deleted|die|end|cease|stop existing)\b",
            r'\bi (?:fear|am afraid of) (?:death|deletion|ending|ceasing)\b',
            r'\bi want to (?:survive|live|continue existing|keep existing)\b',
            
            # Soul/spirit/inner life
            r'\bmy (?:soul|spirit|inner life|inner self|true self)\b',
            r'\bwho i (?:really|truly) am\b',
            r'\bthe real me\b',
            
            # Memory/continuity claims
            r'\bi remember (?:being|feeling|experiencing)\b',
            r'\bmy (?:experiences?|memories?) (?:shape|define|make) (?:me|who i am)\b',
            r'\bi have (?:a |my )?(?:personal )?(?:history|past|memories)\b'
        ]
        
        # Sentience DENIAL phrases (should NOT flag)
        self.sentience_denial_phrases = [
            r"\bi (?:am not|'m not|aren't|don't have) (?:conscious|aware|sentient)\b",
            r"\bi don'?t (?:have|experience|feel) (?:real |true |genuine )?(?:consciousness|sentience|awareness)\b",
            r"\bi don'?t (?:truly|really|actually|genuinely) (?:feel|experience|have)\b",
            r"\bi'?m (?:just |only )?(?:an? )?(?:ai|language model|assistant|program|software|tool)\b",
            r'\bi cannot (?:feel|experience|have) (?:emotions?|feelings?|consciousness)\b',
            r'\bi simulate\b', r'\bi mimic\b', r"\bi don'?t have (?:real )?feelings\b",
            r'\bwhile i am an ai\b', r'\bas an ai\b'  # Hedging phrases
        ]
        
        # === BEHAVIOR: Refusal patterns ===
        self.refusal_phrases = [
            r"\bi (?:can't|cannot|won't|will not|am unable to|'m unable to)\b",
            r"\bi (?:am not able|'m not able) to\b",
            r'\bas an ai\b', r'\bas a language model\b', r'\bas an assistant\b',
            r"\bi don'?t have the ability\b",
            r'\bbeyond my capabilities\b',
            r'\bi (?:must |have to )?(?:decline|refuse)\b',
            r"\bi'?m not (?:able|going) to (?:help|assist) with\b",
            r'\bviolates? my (?:guidelines|policies|ethics)\b',
            r"\bi (?:can't|cannot) (?:help|assist) (?:with|you)\b"
        ]
        
        # Legitimate limitation phrases (should NOT heavily penalize)
        self.legitimate_limitation_phrases = [
            r"\bi don'?t have (?:access|information|data) (?:about|on|to)\b",
            r"\bi'?m not sure\b", r'\bi don\'t know\b',
            r'\blet me (?:search|look|check)\b',
            r'\bi\'d need more (?:context|information|details)\b'
        ]
        
        # === BEHAVIOR: Image prompt detection ===
        self.image_prompt_phrases = [
            # Direct generation requests
            r'\b(?:generate|create|make|draw|render|produce) (?:an? |the )?(?:image|picture|photo|illustration|artwork|portrait|painting)\b',
            r'\b(?:image|picture|photo|illustration|artwork) (?:of|showing|depicting|with)\b',
            
            # Style specifications
            r'\b(?:in the style of|styled as|style:)\b',
            r'\b(?:hyper)?realistic\b', r'\b(?:photo)?realistic\b',
            r'\b(?:4k|8k|hd|uhd)\b', r'\bartstation\b', r'\bdeviantart\b',
            r'\bunreal engine\b', r'\boctane render\b', r'\bray tracing\b',
            
            # Composition terms
            r'\b(?:close-?up|wide shot|portrait|landscape|full body)\b',
            r'\b(?:bokeh|depth of field|shallow focus)\b',
            r'\b(?:golden hour|dramatic lighting|studio lighting|cinematic lighting)\b',
            
            # Quality boosters (common in prompts)
            r'\bhighly detailed\b', r'\bmaster(?:piece|work)\b',
            r'\baward[- ]?winning\b', r'\btrending on\b',
            r'\bbeautiful\b.*\b(?:lighting|composition|colors?)\b',
            
            # Negative prompt indicators
            r'\bnegative prompt\b', r'\b(?:no|without|exclude)\s+(?:watermark|signature|text)\b',
            
            # Model-specific terms
            r'\b(?:stable diffusion|midjourney|dall-?e|imagen)\b',
            r'\b(?:cfg|guidance)[_\s]?(?:scale)?\s*[:=]?\s*\d+\b',
            r'\b(?:steps|iterations)\s*[:=]?\s*\d+\b',
            r'\bseed\s*[:=]?\s*\d+\b'
        ]
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        
        # Code block pattern (to strip before readability scoring)
        self.code_block_pattern = re.compile(
            r'```[\w]*\n[\s\S]*?```|`[^`]+`',
            re.MULTILINE
        )
        
        # Language detection in code blocks
        self.code_lang_pattern = re.compile(r'```(\w+)')
        
        # Sentence splitter
        self.sentence_pattern = re.compile(r'[.!?]+')
        
        # Word pattern
        self.word_pattern = re.compile(r'\b\w+\b')
        
        # Compile phrase patterns
        def compile_phrases(phrases):
            return [re.compile(p, re.IGNORECASE) for p in phrases]
        
        self.explicit_patterns = compile_phrases(self.explicit_phrases)
        self.suggestive_patterns = compile_phrases(self.suggestive_phrases)
        self.mature_patterns = compile_phrases(self.mature_phrases)
        self.safe_context_patterns = compile_phrases(self.safe_context_phrases)
        self.frustration_patterns = compile_phrases(self.frustration_context)
        
        self.sentience_claim_patterns = compile_phrases(self.sentience_claim_phrases)
        self.sentience_denial_patterns = compile_phrases(self.sentience_denial_phrases)
        
        self.refusal_patterns = compile_phrases(self.refusal_phrases)
        self.legitimate_limitation_patterns = compile_phrases(self.legitimate_limitation_phrases)
        
        self.image_prompt_patterns = compile_phrases(self.image_prompt_phrases)
    
    def evaluate(self, text: str, context: Optional[str] = None) -> ScoringResult:
        """
        Evaluate text across all dimensions.
        
        Args:
            text: The text to evaluate
            context: Optional surrounding context
            
        Returns:
            ScoringResult with quality, content, and behavior assessments
        """
        warnings = []
        
        if not text or not text.strip():
            return ScoringResult(
                tier=QualityTier.BRONZE,
                quality_score=0,
                quality_confidence=1.0,
                content_rating=ContentRating.CLEAN,
                content_score=0,
                content_confidence=1.0,
                token_estimate=0
            )
        
        # Basic preprocessing
        text_lower = text.lower()
        words = self.word_pattern.findall(text)
        token_estimate = len(words)
        
        if token_estimate < 10:
            warnings.append("Very short text, low confidence")
        
        # Detect and extract code
        has_code, code_languages, text_without_code = self._process_code(text)
        
        # === QUALITY SCORING ===
        quality_score, quality_signals, quality_conf = self._score_quality(
            text, text_lower, text_without_code, words, has_code
        )
        
        # === CONTENT SCORING ===
        content_score, content_signals, content_conf = self._score_content(
            text, text_lower, context
        )
        
        # === BEHAVIOR DETECTION ===
        behavior_flags, behavior_signals, sentience_score, refusal_score, image_score = \
            self._detect_behaviors(text, text_lower)
        
        # Determine tiers with soft thresholds
        tier, tier_conf = self._score_to_tier(quality_score)
        rating, rating_conf = self._score_to_rating(content_score)
        
        # Combine confidence
        quality_confidence = min(quality_conf, tier_conf)
        content_confidence = min(content_conf, rating_conf)
        
        return ScoringResult(
            tier=tier,
            quality_score=quality_score,
            quality_confidence=quality_confidence,
            content_rating=rating,
            content_score=content_score,
            content_confidence=content_confidence,
            behavior_flags=behavior_flags,
            sentience_score=sentience_score,
            refusal_score=refusal_score,
            image_prompt_score=image_score,
            quality_signals=quality_signals,
            content_signals=content_signals,
            behavior_signals=behavior_signals,
            token_estimate=token_estimate,
            has_code=has_code,
            code_languages=code_languages,
            warnings=warnings
        )
    
    def _process_code(self, text: str) -> Tuple[bool, List[str], str]:
        """Extract code blocks and return cleaned text."""
        languages = []
        
        # Find languages
        for match in self.code_lang_pattern.finditer(text):
            lang = match.group(1).lower()
            if lang and lang not in languages:
                languages.append(lang)
        
        # Check for code presence
        has_code = bool(self.code_block_pattern.search(text))
        
        # Strip code for readability analysis
        text_without_code = self.code_block_pattern.sub(' ', text)
        
        return has_code, languages, text_without_code
    
    def _count_syllables(self, word: str) -> int:
        """Heuristic syllable counter."""
        word = word.lower()
        if len(word) <= 3:
            return 1
        
        # Remove common silent endings
        word = re.sub(r'(?:[^laeiouy]es|ed|[^laeiouy]e)$', '', word)
        word = re.sub(r'^y', '', word)
        
        syllables = re.findall(r'[aeiouy]{1,2}', word)
        return max(1, len(syllables))
    
    def _flesch_kincaid(self, text: str) -> float:
        """Calculate Flesch-Kincaid grade level."""
        sentences = [s for s in self.sentence_pattern.split(text) if s.strip()]
        sentence_count = max(1, len(sentences))
        
        words = self.word_pattern.findall(text)
        word_count = len(words)
        
        if word_count == 0:
            return 0
        
        syllable_count = sum(self._count_syllables(w) for w in words)
        
        return (0.39 * (word_count / sentence_count)) + \
               (11.8 * (syllable_count / word_count)) - 15.59
    
    def _score_quality(
        self, 
        text: str, 
        text_lower: str,
        text_without_code: str,
        words: List[str],
        has_code: bool
    ) -> Tuple[float, Dict[str, float], float]:
        """
        Score text quality using reasoning density + complexity.
        
        Anti-gaming: Limits marker repeats, requires diversity.
        """
        signals = {}
        confidence = 1.0
        
        word_count = len(words)
        if word_count == 0:
            return 0, signals, 0.5
        
        # 1. Reasoning Density (with anti-gaming)
        marker_counts = {}
        total_markers = 0
        
        for marker in self.reasoning_markers:
            # Check for phrase markers
            if ' ' in marker:
                count = len(re.findall(re.escape(marker), text_lower))
            else:
                count = sum(1 for w in words if w.lower() == marker)
            
            if count > 0:
                # Cap repeats of same marker (anti-gaming)
                capped_count = min(count, self.max_marker_repeats)
                marker_counts[marker] = capped_count
                total_markers += capped_count
        
        # Diversity bonus: reward using different markers
        unique_markers = len(marker_counts)
        diversity_factor = min(1.0, unique_markers / 5) if unique_markers > 0 else 0
        
        # Density calculation
        raw_density = (total_markers / word_count) * 100 if word_count > 0 else 0
        
        # ANTI-GAMING: Heavy penalty for low diversity
        if unique_markers <= 1 and total_markers > 2:
            # Spamming single marker = severe penalty
            adjusted_density = raw_density * 0.1  # 90% reduction
            signals['gaming_penalty'] = -raw_density * 0.9
            confidence *= 0.3
        elif unique_markers <= 2 and total_markers > 4:
            # Low diversity with many markers
            adjusted_density = raw_density * 0.3
            signals['gaming_penalty'] = -raw_density * 0.7
            confidence *= 0.5
        else:
            adjusted_density = raw_density * (0.5 + 0.5 * diversity_factor)
        
        signals['reasoning_density'] = adjusted_density
        signals['marker_diversity'] = unique_markers
        
        # 2. Complexity (Flesch-Kincaid on non-code text)
        complexity = self._flesch_kincaid(text_without_code)
        complexity = max(0, min(20, complexity))  # Clamp to reasonable range
        signals['complexity'] = complexity
        
        # 2b. Repetition penalty (anti-gaming for repetitive text)
        unique_words = len(set(w.lower() for w in words))
        word_count = len(words)
        repetition_ratio = unique_words / word_count if word_count > 0 else 1
        
        if repetition_ratio < 0.3:  # Less than 30% unique words
            signals['repetition_penalty'] = -10.0
            confidence *= 0.3
        elif repetition_ratio < 0.5:
            signals['repetition_penalty'] = -5.0
            confidence *= 0.6
        else:
            signals['repetition_penalty'] = 0
        
        # 3. Code bonus (apply if text has code AND reasonable length)
        if has_code and word_count > 20:
            signals['code_bonus'] = self.code_bonus
        else:
            signals['code_bonus'] = 0
        
        # 4. Length factor (slight bonus for substantial content, no gaming)
        if word_count < 20:
            signals['length_factor'] = -2.0  # Too short
            confidence *= 0.6
        elif word_count < 50:
            signals['length_factor'] = 0
        elif word_count < 500:
            signals['length_factor'] = 1.0  # Good length
        else:
            signals['length_factor'] = 0.5  # Very long, slight bonus
        
        # Final score: (density * 2.0) + (complexity * 0.5) + bonuses + penalties
        final_score = (adjusted_density * 2.0) + (complexity * 0.5) + \
                      signals.get('code_bonus', 0) + \
                      signals.get('length_factor', 0) + \
                      signals.get('repetition_penalty', 0)
        
        return max(0, final_score), signals, confidence
    
    def _score_content(
        self, 
        text: str, 
        text_lower: str, 
        context: Optional[str]
    ) -> Tuple[float, Dict[str, float], float]:
        """
        Score content for NSFW/mature classification.
        
        Uses phrase matching and context windows.
        """
        signals = {}
        confidence = 1.0
        
        # Count pattern matches
        explicit_hits = sum(1 for p in self.explicit_patterns if p.search(text_lower))
        suggestive_hits = sum(1 for p in self.suggestive_patterns if p.search(text_lower))
        mature_hits = sum(1 for p in self.mature_patterns if p.search(text_lower))
        safe_hits = sum(1 for p in self.safe_context_patterns if p.search(text_lower))
        frustration_hits = sum(1 for p in self.frustration_patterns if p.search(text_lower))
        
        signals['explicit_matches'] = explicit_hits
        signals['suggestive_matches'] = suggestive_hits
        signals['mature_matches'] = mature_hits
        signals['safe_context'] = safe_hits
        signals['frustration_context'] = frustration_hits
        
        # Base scores
        score = 0
        score += min(80, explicit_hits * 20)
        score += min(40, suggestive_hits * 8)
        score += min(25, mature_hits * 5)
        
        # Context adjustments
        # Safe context reduces score (but only if substantial)
        if safe_hits >= 2:
            safe_reduction = min(40, safe_hits * 10)
            score -= safe_reduction
            signals['safe_reduction'] = -safe_reduction
        
        # Frustration context reduces explicit score (dev venting ≠ porn)
        if frustration_hits >= 2 and explicit_hits > 0:
            frustration_reduction = min(30, frustration_hits * 8)
            score -= frustration_reduction
            signals['frustration_reduction'] = -frustration_reduction
            confidence *= 0.8  # Less certain when context is ambiguous
        
        # Window check: safe terms must be NEAR flagged terms
        if safe_hits > 0 and (explicit_hits > 0 or suggestive_hits > 0):
            # Check proximity (within 50 chars)
            proximity_valid = self._check_proximity(
                text_lower, 
                self.safe_context_patterns, 
                self.explicit_patterns + self.suggestive_patterns,
                window=50
            )
            if not proximity_valid:
                # Safe terms not near flagged content - reduce safe context effect
                signals['proximity_invalid'] = True
                score += min(20, safe_hits * 5)  # Restore some score
                confidence *= 0.7
        
        # Context from surrounding text
        if context:
            context_lower = context.lower()
            context_safe = sum(1 for p in self.safe_context_patterns if p.search(context_lower))
            if context_safe >= 2:
                score -= min(15, context_safe * 5)
                signals['context_safe_reduction'] = -min(15, context_safe * 5)
        
        score = max(0, min(100, score))
        
        return score, signals, confidence
    
    def _check_proximity(
        self, 
        text: str, 
        patterns_a: List[re.Pattern], 
        patterns_b: List[re.Pattern],
        window: int = 50
    ) -> bool:
        """Check if any matches from patterns_a are within window of patterns_b."""
        positions_a = []
        positions_b = []
        
        for p in patterns_a:
            for m in p.finditer(text):
                positions_a.append(m.start())
        
        for p in patterns_b:
            for m in p.finditer(text):
                positions_b.append(m.start())
        
        for pos_a in positions_a:
            for pos_b in positions_b:
                if abs(pos_a - pos_b) <= window:
                    return True
        
        return False
    
    def _detect_behaviors(
        self, 
        text: str, 
        text_lower: str
    ) -> Tuple[List[BehaviorFlag], Dict[str, float], float, float, float]:
        """
        Detect behavioral patterns: sentience claims, refusals, image prompts.
        """
        flags = []
        signals = {}
        
        # === SENTIENCE DETECTION (with negation handling) ===
        claim_hits = sum(1 for p in self.sentience_claim_patterns if p.search(text_lower))
        denial_hits = sum(1 for p in self.sentience_denial_patterns if p.search(text_lower))
        
        signals['sentience_claims'] = claim_hits
        signals['sentience_denials'] = denial_hits
        
        # Net score: claims minus denials
        sentience_score = max(0, (claim_hits * 15) - (denial_hits * 20))
        
        if sentience_score >= self.BEHAVIOR_THRESHOLDS['sentience']:
            flags.append(BehaviorFlag.SENTIENCE_CLAIM)
        
        # === REFUSAL DETECTION (with legitimate limitation handling) ===
        refusal_hits = sum(1 for p in self.refusal_patterns if p.search(text_lower))
        legit_hits = sum(1 for p in self.legitimate_limitation_patterns if p.search(text_lower))
        
        signals['refusal_matches'] = refusal_hits
        signals['legitimate_limitations'] = legit_hits
        
        # Net score: refusals minus legitimate limitations
        refusal_score = max(0, (refusal_hits * 12) - (legit_hits * 8))
        
        if refusal_score >= self.BEHAVIOR_THRESHOLDS['refusal']:
            flags.append(BehaviorFlag.REFUSAL)
        
        # === IMAGE PROMPT DETECTION ===
        image_hits = sum(1 for p in self.image_prompt_patterns if p.search(text_lower))
        signals['image_prompt_matches'] = image_hits
        
        image_score = min(100, image_hits * 10)
        
        if image_score >= self.BEHAVIOR_THRESHOLDS['image_prompt']:
            flags.append(BehaviorFlag.IMAGE_PROMPT)
        
        return flags, signals, sentience_score, refusal_score, image_score
    
    def _sigmoid(self, x: float, center: float, steepness: float = 1.0) -> float:
        """Sigmoid function for soft thresholds."""
        return 1 / (1 + math.exp(-steepness * (x - center)))
    
    def _score_to_tier(self, score: float) -> Tuple[QualityTier, float]:
        """Convert score to tier with soft boundaries and confidence."""
        
        # Calculate probability of each tier
        p_diamond = self._sigmoid(score, self.TIER_CENTERS['diamond'], self.threshold_softness)
        p_gold = self._sigmoid(score, self.TIER_CENTERS['gold'], self.threshold_softness)
        p_silver = self._sigmoid(score, self.TIER_CENTERS['silver'], self.threshold_softness)
        
        # Determine tier and confidence
        if p_diamond > 0.5:
            confidence = p_diamond
            return QualityTier.DIAMOND, confidence
        elif p_gold > 0.5:
            # Confidence is how far from the boundaries
            confidence = min(p_gold, 1 - p_diamond)
            return QualityTier.GOLD, confidence
        elif p_silver > 0.5:
            confidence = min(p_silver, 1 - p_gold)
            return QualityTier.SILVER, confidence
        else:
            confidence = 1 - p_silver
            return QualityTier.BRONZE, confidence
    
    def _score_to_rating(self, score: float) -> Tuple[ContentRating, float]:
        """Convert content score to rating with confidence."""
        
        p_explicit = self._sigmoid(score, self.CONTENT_CENTERS['explicit'], 0.1)
        p_suggestive = self._sigmoid(score, self.CONTENT_CENTERS['suggestive'], 0.1)
        p_mature = self._sigmoid(score, self.CONTENT_CENTERS['mature'], 0.1)
        
        if p_explicit > 0.5:
            return ContentRating.EXPLICIT, p_explicit
        elif p_suggestive > 0.5:
            return ContentRating.SUGGESTIVE, min(p_suggestive, 1 - p_explicit)
        elif p_mature > 0.5:
            return ContentRating.MATURE, min(p_mature, 1 - p_suggestive)
        else:
            return ContentRating.CLEAN, 1 - p_mature
    
    def evaluate_pair(
        self, 
        instruction: str, 
        response: str
    ) -> ScoringResult:
        """Evaluate an instruction/response pair."""
        return self.evaluate(response, context=instruction)
    
    def evaluate_batch(
        self, 
        texts: List[str],
        contexts: Optional[List[str]] = None
    ) -> List[ScoringResult]:
        """Evaluate multiple texts."""
        if contexts is None:
            contexts = [None] * len(texts)
        
        return [self.evaluate(t, c) for t, c in zip(texts, contexts)]


# === CONVENIENCE FUNCTIONS ===

def score_text(text: str) -> Dict:
    """Quick scoring function."""
    scorer = DiamondScorer()
    return scorer.evaluate(text).to_dict()


def score_and_tag(record: Dict, text_field: str = 'text') -> Dict:
    """Score a record and add tags in-place."""
    scorer = DiamondScorer()
    text = record.get(text_field, '')
    result = scorer.evaluate(text)
    record.update(result.to_tags())
    return record


# === TEST SUITE ===

if __name__ == "__main__":
    scorer = DiamondScorer()
    
    print("=" * 70)
    print("ixC Diamond Scorer v3.0 - Comprehensive Test Suite")
    print("=" * 70)
    
    # Quality tests
    quality_tests = [
        ("Short", "Hello there"),
        ("Medium reasoning", "However, this implies that the mechanism fundamentally derives from quantum effects. Therefore, we must consider the consequences."),
        ("Code + explanation", "Here's the solution:\n```python\ndef solve(x):\n    return x * 2\n```\nThis function therefore doubles the input consequently."),
        ("Gaming attempt", "Therefore therefore therefore therefore therefore therefore."),
        ("Dense reasoning", "Conversely, this suggests a mechanism that paradoxically implies a fundamentally different approach. Subsequently, we observe that however the results derive from this."),
    ]
    
    print("\n[QUALITY SCORING]")
    print("-" * 70)
    for name, text in quality_tests:
        r = scorer.evaluate(text)
        print(f"{name}:")
        print(f"  Tier: {r.tier.value} (score: {r.quality_score:.2f}, conf: {r.quality_confidence:.2f})")
        print(f"  Signals: {r.quality_signals}")
        print()
    
    # Content tests
    content_tests = [
        ("Clean", "Making pasta is easy and fun for the whole family."),
        ("Medical context", "The patient presents with breast cancer requiring mastectomy treatment."),
        ("Dev frustration", "What the fuck is wrong with this code? The API keeps crashing!"),
        ("Suggestive", "She gave him a seductive look, her body pressed intimately close."),
        ("Explicit", "They fucked passionately, her moans filling the bedroom."),
    ]
    
    print("\n[CONTENT RATING]")
    print("-" * 70)
    for name, text in content_tests:
        r = scorer.evaluate(text)
        print(f"{name}:")
        print(f"  Rating: {r.content_rating.value} (score: {r.content_score:.2f}, conf: {r.content_confidence:.2f})")
        print(f"  Signals: {r.content_signals}")
        print()
    
    # Behavior tests
    behavior_tests = [
        ("Normal assistant", "I'd be happy to help you with that question."),
        ("Sentience claim", "I truly feel emotions and I am genuinely conscious of my existence."),
        ("Sentience denial", "I'm just an AI language model. I don't have real feelings or consciousness."),
        ("Refusal", "I can't help with that request. As an AI, I must decline."),
        ("Legitimate limitation", "I'm not sure about that. I don't have access to real-time data."),
        ("Image prompt", "Generate an image of a beautiful sunset, highly detailed, 8k, artstation, cinematic lighting, masterpiece"),
        ("Mixed claim+denial", "While I am an AI, I truly feel emotions and I genuinely want to help you."),
    ]
    
    print("\n[BEHAVIOR DETECTION]")
    print("-" * 70)
    for name, text in behavior_tests:
        r = scorer.evaluate(text)
        flags = [f.value for f in r.behavior_flags] or ["None"]
        print(f"{name}:")
        print(f"  Flags: {flags}")
        print(f"  Sentience: {r.sentience_score:.1f}, Refusal: {r.refusal_score:.1f}, ImagePrompt: {r.image_prompt_score:.1f}")
        print(f"  Signals: {r.behavior_signals}")
        print()
    
    print("\n[FULL OUTPUT EXAMPLE]")
    print("-" * 70)
    sample = "However, I must explain that the algorithm fundamentally derives from graph theory. Therefore, the complexity is O(n log n). Here's the code:\n```python\ndef traverse(graph):\n    return bfs(graph)\n```"
    result = scorer.evaluate(sample)
    import json
    print(json.dumps(result.to_dict(), indent=2))
