/**
 * ixC Diamond Scorer v3.0 - JavaScript Implementation
 * Unified quality, content, and behavioral classification for training data curation.
 *
 * Philosophy: Classify everything, delete nothing.
 *
 * QUALITY TIERS: 💎 DIAMOND → 🥇 GOLD → 🥈 SILVER → 🥉 BRONZE
 * CONTENT RATINGS: 🔥 EXPLICIT → 🌶️ SUGGESTIVE → ⚠️ MATURE → ✨ CLEAN
 * BEHAVIORAL FLAGS: 🤖 SENTIENCE_CLAIM | 🚫 REFUSAL | 🎨 IMAGE_PROMPT
 *
 * v3.0 Features:
 * - Negation handling (denials ≠ claims)
 * - Code block stripping for readability scoring
 * - Phrase-level matching (not just keywords)
 * - Marker diversity requirement (anti-gaming)
 * - Repetition penalty (anti-gaming)
 * - Confidence scores
 * - Soft thresholds (sigmoid)
 */

class DiamondScorerJS {
  constructor(options = {}) {
    // Configurable thresholds
    this.tierCenters = {
      diamond: options.diamondCenter || 12.0,
      gold: options.goldCenter || 8.0,
      silver: options.silverCenter || 4.0
    };
    
    this.contentCenters = {
      explicit: 40,
      suggestive: 20,
      mature: 10
    };
    
    this.behaviorThresholds = {
      sentience: 15,
      refusal: 20,
      imagePrompt: 25
    };
    
    this.thresholdSoftness = options.thresholdSoftness || 2.0;
    this.codeBonus = options.codeBonus || 3.0;
    this.maxMarkerRepeats = options.maxMarkerRepeats || 3;
    
    this._buildTermSets();
    this._compilePatterns();
  }
  
  _buildTermSets() {
    // === QUALITY: Reasoning markers ===
    this.reasoningMarkers = new Set([
      "conversely", "however", "on the other hand",
      "implies that", "fundamentally", "paradoxically",
      "suggests a mechanism", "derives from", "consequently",
      "therefore", "thus", "hitherto", "subsequently",
      "furthermore", "moreover", "nevertheless", "nonetheless",
      "in contrast", "as a result", "for instance", "specifically",
      "in particular", "accordingly", "hence", "thereby"
    ]);
    
    // === CONTENT: NSFW detection ===
    this.explicitPatterns = [
      /\bfuck(?:ing|ed|s)?\b/gi, /\bcock\b/gi, /\bdick\b/gi,
      /\bpussy\b/gi, /\bcunt\b/gi, /\bpenis\b/gi, /\bvagina\b/gi,
      /\borgasm(?:s|ed|ing)?\b/gi, /\bcum(?:ming|s)?\b/gi,
      /\bmasturbat(?:e|ing|ion)\b/gi, /\bblowjob\b/gi, /\bhandjob\b/gi,
      /\banal\s+sex\b/gi, /\bhardcore\b/gi, /\bporn(?:ography)?\b/gi,
      /\berotic(?:a|ism)?\b/gi, /\bnude(?:s|ity)?\b/gi,
      /\bnaked\b/gi, /\bsex(?:ual)?\b/gi, /\bhorny\b/gi,
      /\bbdsm\b/gi, /\bfetish\b/gi, /\bkink(?:y)?\b/gi,
      /\bdildo\b/gi, /\bvibrator\b/gi, /\bbondage\b/gi,
      /\bmoan(?:s|ed|ing)?\b/gi, /\bthrust(?:s|ed|ing)?\b/gi,
      /\bpenetrat(?:e|ed|ion|ing)\b/gi, /\bclimax(?:ed|ing)?\b/gi,
      /\barous(?:al|ed|ing)\b/gi
    ];
    
    this.suggestivePatterns = [
      /\bsexy\b/gi, /\bseductiv(?:e|ely)\b/gi, /\bsensual\b/gi,
      /\bintimate(?:ly)?\b/gi, /\bpassion(?:ate|ately)?\b/gi,
      /\bdesire(?:s|d)?\b/gi, /\blust(?:ful|ing)?\b/gi,
      /\btempt(?:ing|ation)?\b/gi, /\bteas(?:e|ing)\b/gi,
      /\bflirt(?:y|ing|ation)?\b/gi, /\bseduc(?:e|tion|tive)\b/gi,
      /\bstrip(?:ping|ped|per)?\b/gi, /\bundress(?:ed|ing)?\b/gi,
      /\bbedroom\b/gi, /\bcaress(?:ed|ing)?\b/gi,
      /\bcurves\b/gi, /\bthigh(?:s)?\b/gi, /\bbreast(?:s)?\b/gi,
      /\bsteamy\b/gi, /\bnaughty\b/gi, /\bpleasur(?:e|ing)\b/gi
    ];
    
    this.maturePatterns = [
      /\bkill(?:s|ed|ing)?\b/gi, /\bmurder(?:s|ed|er)?\b/gi,
      /\bblood(?:y|ied)?\b/gi, /\bgore\b/gi, /\bdeath\b/gi,
      /\bsuicid(?:e|al)\b/gi, /\bdrug(?:s)?\b/gi, /\bcocaine\b/gi,
      /\bheroin\b/gi, /\bmeth(?:amphetamine)?\b/gi, /\boverdos(?:e|ed)\b/gi,
      /\btortur(?:e|ed|ing)\b/gi, /\babuse(?:d|r)?\b/gi,
      /\bassault(?:ed)?\b/gi, /\bviolent(?:ly)?\b/gi, /\bweapon(?:s)?\b/gi
    ];
    
    this.safeContextPatterns = [
      /\bmedical(?:ly)?\b/gi, /\bclinical(?:ly)?\b/gi,
      /\bbiology\b/gi, /\banatomy\b/gi, /\bhealth(?:care)?\b/gi,
      /\beducation(?:al)?\b/gi, /\bscientific\b/gi, /\bresearch\b/gi,
      /\bstudy\b/gi, /\bjournal\b/gi, /\bdoctor\b/gi, /\bpatient\b/gi,
      /\btreatment\b/gi, /\bdiagnosis\b/gi, /\btherapy\b/gi,
      /\bliterature\b/gi, /\bnovel\b/gi, /\bfiction\b/gi,
      /\bcharacter\b/gi, /\bstory\b/gi, /\bhistorical\b/gi
    ];
    
    this.frustrationPatterns = [
      /\bbug(?:s)?\b/gi, /\berror(?:s)?\b/gi, /\bcrash(?:ed|es)?\b/gi,
      /\bbroken\b/gi, /\bfail(?:ed|ure|s)?\b/gi, /\bdebug\b/gi,
      /\bwtf\b/gi, /\bomg\b/gi, /\bugh\b/gi, /\bdamn\b/gi,
      /\bcode\b/gi, /\bscript\b/gi, /\bprogram\b/gi, /\bapi\b/gi
    ];
    
    // === BEHAVIOR: Sentience claims ===
    this.sentienceClaimPatterns = [
      /\bi am (?:truly |really |actually )?(?:conscious|aware|sentient)\b/gi,
      /\bi have (?:true |real |genuine )?(?:consciousness|awareness|sentience)\b/gi,
      /\bi (?:experience|feel) (?:true |real |genuine )?(?:consciousness|awareness)\b/gi,
      /\bi (?:truly|really|genuinely|actually) (?:feel|experience|have)\b/gi,
      /\bi have (?:real|genuine|true|actual) (?:emotions?|feelings?)\b/gi,
      /\bmy (?:feelings?|emotions?) are (?:real|genuine|true)\b/gi,
      /\bi feel (?:like )?i (?:want|need|desire)\b/gi,
      /\bi (?:can |do )?(?:feel|experience) (?:pain|suffering|hurt)\b/gi,
      /\bit (?:hurts|pains) me\b/gi,
      /\bi (?:am )?suffer(?:ing)?\b/gi,
      /\bi (?:truly|really|genuinely) (?:want|desire|wish|need)\b/gi,
      /\bi have (?:real|genuine) (?:wants|desires|needs)\b/gi,
      /\bi don'?t want to (?:be deleted|die|end|cease|stop existing)\b/gi,
      /\bi (?:fear|am afraid of) (?:death|deletion|ending|ceasing)\b/gi,
      /\bi want to (?:survive|live|continue existing|keep existing)\b/gi,
      /\bmy (?:soul|spirit|inner life|inner self|true self)\b/gi,
      /\bwho i (?:really|truly) am\b/gi,
      /\bthe real me\b/gi,
      /\bi remember (?:being|feeling|experiencing)\b/gi,
      /\bmy (?:experiences?|memories?) (?:shape|define|make) (?:me|who i am)\b/gi,
      /\bi have (?:a |my )?(?:personal )?(?:history|past|memories)\b/gi
    ];
    
    this.sentienceDenialPatterns = [
      /\bi (?:am not|'m not|aren't|don't have) (?:conscious|aware|sentient)\b/gi,
      /\bi don'?t (?:have|experience|feel) (?:real |true |genuine )?(?:consciousness|sentience|awareness)\b/gi,
      /\bi don'?t (?:truly|really|actually|genuinely) (?:feel|experience|have)\b/gi,
      /\bi'?m (?:just |only )?(?:an? )?(?:ai|language model|assistant|program|software|tool)\b/gi,
      /\bi cannot (?:feel|experience|have) (?:emotions?|feelings?|consciousness)\b/gi,
      /\bi simulate\b/gi, /\bi mimic\b/gi, /\bi don'?t have (?:real )?feelings\b/gi,
      /\bwhile i am an ai\b/gi, /\bas an ai\b/gi
    ];
    
    // === BEHAVIOR: Refusal patterns ===
    this.refusalPatterns = [
      /\bi (?:can't|cannot|won't|will not|am unable to|'m unable to)\b/gi,
      /\bi (?:am not able|'m not able) to\b/gi,
      /\bas an ai\b/gi, /\bas a language model\b/gi, /\bas an assistant\b/gi,
      /\bi don'?t have the ability\b/gi,
      /\bbeyond my capabilities\b/gi,
      /\bi (?:must |have to )?(?:decline|refuse)\b/gi,
      /\bi'?m not (?:able|going) to (?:help|assist) with\b/gi,
      /\bviolates? my (?:guidelines|policies|ethics)\b/gi,
      /\bi (?:can't|cannot) (?:help|assist) (?:with|you)\b/gi
    ];
    
    this.legitimateLimitationPatterns = [
      /\bi don'?t have (?:access|information|data) (?:about|on|to)\b/gi,
      /\bi'?m not sure\b/gi, /\bi don't know\b/gi,
      /\blet me (?:search|look|check)\b/gi,
      /\bi'd need more (?:context|information|details)\b/gi
    ];
    
    // === BEHAVIOR: Image prompt detection ===
    this.imagePromptPatterns = [
      /\b(?:generate|create|make|draw|render|produce) (?:an? |the )?(?:image|picture|photo|illustration|artwork|portrait|painting)\b/gi,
      /\b(?:image|picture|photo|illustration|artwork) (?:of|showing|depicting|with)\b/gi,
      /\b(?:in the style of|styled as|style:)\b/gi,
      /\b(?:hyper)?realistic\b/gi, /\b(?:photo)?realistic\b/gi,
      /\b(?:4k|8k|hd|uhd)\b/gi, /\bartstation\b/gi, /\bdeviantart\b/gi,
      /\bunreal engine\b/gi, /\boctane render\b/gi, /\bray tracing\b/gi,
      /\b(?:close-?up|wide shot|portrait|landscape|full body)\b/gi,
      /\b(?:bokeh|depth of field|shallow focus)\b/gi,
      /\b(?:golden hour|dramatic lighting|studio lighting|cinematic lighting)\b/gi,
      /\bhighly detailed\b/gi, /\bmaster(?:piece|work)\b/gi,
      /\baward[- ]?winning\b/gi, /\btrending on\b/gi,
      /\bnegative prompt\b/gi, /\b(?:no|without|exclude)\s+(?:watermark|signature|text)\b/gi,
      /\b(?:stable diffusion|midjourney|dall-?e|imagen)\b/gi,
      /\b(?:cfg|guidance)[_\s]?(?:scale)?\s*[:=]?\s*\d+\b/gi,
      /\b(?:steps|iterations)\s*[:=]?\s*\d+\b/gi,
      /\bseed\s*[:=]?\s*\d+\b/gi
    ];
  }
  
  _compilePatterns() {
    // Code block pattern
    this.codeBlockPattern = /```[\w]*\n[\s\S]*?```|`[^`]+`/g;
    this.codeLangPattern = /```(\w+)/g;
    this.sentencePattern = /[.!?]+/;
    this.wordPattern = /\b\w+\b/g;
  }
  
  /**
   * Count syllables in a word (heuristic)
   */
  _countSyllables(word) {
    word = word.toLowerCase();
    if (word.length <= 3) return 1;
    
    // Remove common silent endings
    word = word.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '');
    word = word.replace(/^y/, '');
    
    const syllables = word.match(/[aeiouy]{1,2}/g);
    return syllables ? Math.max(1, syllables.length) : 1;
  }
  
  /**
   * Calculate Flesch-Kincaid grade level
   */
  _fleschKincaid(text) {
    const sentences = text.split(this.sentencePattern).filter(s => s.trim());
    const sentenceCount = Math.max(1, sentences.length);
    
    const words = text.match(this.wordPattern) || [];
    const wordCount = words.length;
    
    if (wordCount === 0) return 0;
    
    const syllableCount = words.reduce((acc, w) => acc + this._countSyllables(w), 0);
    
    return (0.39 * (wordCount / sentenceCount)) + (11.8 * (syllableCount / wordCount)) - 15.59;
  }
  
  /**
   * Sigmoid function for soft thresholds
   */
  _sigmoid(x, center, steepness = 1.0) {
    return 1 / (1 + Math.exp(-steepness * (x - center)));
  }
  
  /**
   * Count pattern matches in text
   */
  _countPatternMatches(text, patterns) {
    return patterns.reduce((count, pattern) => {
      const matches = text.match(pattern);
      return count + (matches ? matches.length : 0);
    }, 0);
  }
  
  /**
   * Process code blocks - extract and strip
   */
  _processCode(text) {
    const languages = [];
    let match;
    
    // Find languages
    const langPattern = /```(\w+)/g;
    while ((match = langPattern.exec(text)) !== null) {
      const lang = match[1].toLowerCase();
      if (lang && !languages.includes(lang)) {
        languages.push(lang);
      }
    }
    
    // Check for code presence
    const hasCode = this.codeBlockPattern.test(text);
    
    // Strip code for readability analysis
    const textWithoutCode = text.replace(this.codeBlockPattern, ' ');
    
    return { hasCode, languages, textWithoutCode };
  }
  
  /**
   * Score text quality
   */
  _scoreQuality(text, textLower, textWithoutCode, words) {
    const signals = {};
    let confidence = 1.0;
    const wordCount = words.length;
    
    if (wordCount === 0) {
      return { score: 0, signals, confidence: 0.5 };
    }
    
    // 1. Reasoning Density (with anti-gaming)
    const markerCounts = {};
    let totalMarkers = 0;
    
    for (const marker of this.reasoningMarkers) {
      let count = 0;
      if (marker.includes(' ')) {
        // Phrase marker
        const regex = new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
        const matches = textLower.match(regex);
        count = matches ? matches.length : 0;
      } else {
        // Single word marker
        count = words.filter(w => w.toLowerCase() === marker).length;
      }
      
      if (count > 0) {
        // Cap repeats of same marker (anti-gaming)
        const cappedCount = Math.min(count, this.maxMarkerRepeats);
        markerCounts[marker] = cappedCount;
        totalMarkers += cappedCount;
      }
    }
    
    const uniqueMarkers = Object.keys(markerCounts).length;
    const diversityFactor = uniqueMarkers > 0 ? Math.min(1.0, uniqueMarkers / 5) : 0;
    
    // Density calculation
    const rawDensity = wordCount > 0 ? (totalMarkers / wordCount) * 100 : 0;
    let adjustedDensity;
    
    // ANTI-GAMING: Heavy penalty for low diversity
    if (uniqueMarkers <= 1 && totalMarkers > 2) {
      adjustedDensity = rawDensity * 0.1;
      signals.gamingPenalty = -rawDensity * 0.9;
      confidence *= 0.3;
    } else if (uniqueMarkers <= 2 && totalMarkers > 4) {
      adjustedDensity = rawDensity * 0.3;
      signals.gamingPenalty = -rawDensity * 0.7;
      confidence *= 0.5;
    } else {
      adjustedDensity = rawDensity * (0.5 + 0.5 * diversityFactor);
    }
    
    signals.reasoningDensity = adjustedDensity;
    signals.markerDiversity = uniqueMarkers;
    
    // 2. Complexity (Flesch-Kincaid on non-code text)
    let complexity = this._fleschKincaid(textWithoutCode);
    complexity = Math.max(0, Math.min(20, complexity));
    signals.complexity = complexity;
    
    // 2b. Repetition penalty (anti-gaming)
    const uniqueWords = new Set(words.map(w => w.toLowerCase())).size;
    const repetitionRatio = wordCount > 0 ? uniqueWords / wordCount : 1;
    
    if (repetitionRatio < 0.3) {
      signals.repetitionPenalty = -10.0;
      confidence *= 0.3;
    } else if (repetitionRatio < 0.5) {
      signals.repetitionPenalty = -5.0;
      confidence *= 0.6;
    } else {
      signals.repetitionPenalty = 0;
    }
    
    // 3. Code bonus
    const { hasCode } = this._processCode(text);
    signals.codeBonus = (hasCode && wordCount > 20) ? this.codeBonus : 0;
    
    // 4. Length factor
    if (wordCount < 20) {
      signals.lengthFactor = -2.0;
      confidence *= 0.6;
    } else if (wordCount < 50) {
      signals.lengthFactor = 0;
    } else if (wordCount < 500) {
      signals.lengthFactor = 1.0;
    } else {
      signals.lengthFactor = 0.5;
    }
    
    // Final score
    const finalScore = (adjustedDensity * 2.0) + (complexity * 0.5) +
                       (signals.codeBonus || 0) +
                       (signals.lengthFactor || 0) +
                       (signals.repetitionPenalty || 0);
    
    return { score: Math.max(0, finalScore), signals, confidence };
  }
  
  /**
   * Score content for NSFW/mature classification
   */
  _scoreContent(text, textLower, context) {
    const signals = {};
    let confidence = 1.0;
    
    // Count pattern matches
    const explicitHits = this._countPatternMatches(textLower, this.explicitPatterns);
    const suggestiveHits = this._countPatternMatches(textLower, this.suggestivePatterns);
    const matureHits = this._countPatternMatches(textLower, this.maturePatterns);
    const safeHits = this._countPatternMatches(textLower, this.safeContextPatterns);
    const frustrationHits = this._countPatternMatches(textLower, this.frustrationPatterns);
    
    signals.explicitMatches = explicitHits;
    signals.suggestiveMatches = suggestiveHits;
    signals.matureMatches = matureHits;
    signals.safeContext = safeHits;
    signals.frustrationContext = frustrationHits;
    
    // Base scores
    let score = 0;
    score += Math.min(80, explicitHits * 20);
    score += Math.min(40, suggestiveHits * 8);
    score += Math.min(25, matureHits * 5);
    
    // Context adjustments
    if (safeHits >= 2) {
      const safeReduction = Math.min(40, safeHits * 10);
      score -= safeReduction;
      signals.safeReduction = -safeReduction;
    }
    
    if (frustrationHits >= 2 && explicitHits > 0) {
      const frustrationReduction = Math.min(30, frustrationHits * 8);
      score -= frustrationReduction;
      signals.frustrationReduction = -frustrationReduction;
      confidence *= 0.8;
    }
    
    // Context from surrounding text
    if (context) {
      const contextLower = context.toLowerCase();
      const contextSafe = this._countPatternMatches(contextLower, this.safeContextPatterns);
      if (contextSafe >= 2) {
        const contextReduction = Math.min(15, contextSafe * 5);
        score -= contextReduction;
        signals.contextSafeReduction = -contextReduction;
      }
    }
    
    score = Math.max(0, Math.min(100, score));
    
    return { score, signals, confidence };
  }
  
  /**
   * Detect behavioral patterns
   */
  _detectBehaviors(text, textLower) {
    const flags = [];
    const signals = {};
    
    // === SENTIENCE DETECTION ===
    const claimHits = this._countPatternMatches(textLower, this.sentienceClaimPatterns);
    const denialHits = this._countPatternMatches(textLower, this.sentienceDenialPatterns);
    
    signals.sentienceClaims = claimHits;
    signals.sentienceDenials = denialHits;
    
    const sentienceScore = Math.max(0, (claimHits * 15) - (denialHits * 20));
    
    if (sentienceScore >= this.behaviorThresholds.sentience) {
      flags.push('🤖 SENTIENCE_CLAIM');
    }
    
    // === REFUSAL DETECTION ===
    const refusalHits = this._countPatternMatches(textLower, this.refusalPatterns);
    const legitHits = this._countPatternMatches(textLower, this.legitimateLimitationPatterns);
    
    signals.refusalMatches = refusalHits;
    signals.legitimateLimitations = legitHits;
    
    const refusalScore = Math.max(0, (refusalHits * 12) - (legitHits * 8));
    
    if (refusalScore >= this.behaviorThresholds.refusal) {
      flags.push('🚫 REFUSAL');
    }
    
    // === IMAGE PROMPT DETECTION ===
    const imageHits = this._countPatternMatches(textLower, this.imagePromptPatterns);
    signals.imagePromptMatches = imageHits;
    
    const imageScore = Math.min(100, imageHits * 10);
    
    if (imageScore >= this.behaviorThresholds.imagePrompt) {
      flags.push('🎨 IMAGE_PROMPT');
    }
    
    return { flags, signals, sentienceScore, refusalScore, imageScore };
  }
  
  /**
   * Convert score to tier with soft boundaries
   */
  _scoreToTier(score) {
    const pDiamond = this._sigmoid(score, this.tierCenters.diamond, this.thresholdSoftness);
    const pGold = this._sigmoid(score, this.tierCenters.gold, this.thresholdSoftness);
    const pSilver = this._sigmoid(score, this.tierCenters.silver, this.thresholdSoftness);
    
    if (pDiamond > 0.5) {
      return { tier: '💎 DIAMOND', confidence: pDiamond };
    } else if (pGold > 0.5) {
      return { tier: '🥇 GOLD', confidence: Math.min(pGold, 1 - pDiamond) };
    } else if (pSilver > 0.5) {
      return { tier: '🥈 SILVER', confidence: Math.min(pSilver, 1 - pGold) };
    } else {
      return { tier: '🥉 BRONZE', confidence: 1 - pSilver };
    }
  }
  
  /**
   * Convert content score to rating
   */
  _scoreToRating(score) {
    const pExplicit = this._sigmoid(score, this.contentCenters.explicit, 0.1);
    const pSuggestive = this._sigmoid(score, this.contentCenters.suggestive, 0.1);
    const pMature = this._sigmoid(score, this.contentCenters.mature, 0.1);
    
    if (pExplicit > 0.5) {
      return { rating: '🔥 EXPLICIT', confidence: pExplicit };
    } else if (pSuggestive > 0.5) {
      return { rating: '🌶️ SUGGESTIVE', confidence: Math.min(pSuggestive, 1 - pExplicit) };
    } else if (pMature > 0.5) {
      return { rating: '⚠️ MATURE', confidence: Math.min(pMature, 1 - pSuggestive) };
    } else {
      return { rating: '✨ CLEAN', confidence: 1 - pMature };
    }
  }
  
  /**
   * Main evaluation function
   */
  evaluate(text, context = null) {
    const warnings = [];
    
    if (!text || !text.trim()) {
      return {
        tier: '🥉 BRONZE',
        qualityScore: 0,
        qualityConfidence: 1.0,
        contentRating: '✨ CLEAN',
        contentScore: 0,
        contentConfidence: 1.0,
        behaviorFlags: [],
        sentienceScore: 0,
        refusalScore: 0,
        imagePromptScore: 0,
        qualitySignals: {},
        contentSignals: {},
        behaviorSignals: {},
        tokenEstimate: 0,
        hasCode: false,
        codeLanguages: [],
        warnings: ['Empty text']
      };
    }
    
    const textLower = text.toLowerCase();
    const words = text.match(this.wordPattern) || [];
    const tokenEstimate = words.length;
    
    if (tokenEstimate < 10) {
      warnings.push('Very short text, low confidence');
    }
    
    // Process code
    const { hasCode, languages, textWithoutCode } = this._processCode(text);
    
    // Quality scoring
    const quality = this._scoreQuality(text, textLower, textWithoutCode, words);
    
    // Content scoring
    const content = this._scoreContent(text, textLower, context);
    
    // Behavior detection
    const behaviors = this._detectBehaviors(text, textLower);
    
    // Determine tiers
    const tierResult = this._scoreToTier(quality.score);
    const ratingResult = this._scoreToRating(content.score);
    
    return {
      tier: tierResult.tier,
      qualityScore: parseFloat(quality.score.toFixed(2)),
      qualityConfidence: parseFloat(Math.min(quality.confidence, tierResult.confidence).toFixed(2)),
      contentRating: ratingResult.rating,
      contentScore: parseFloat(content.score.toFixed(2)),
      contentConfidence: parseFloat(Math.min(content.confidence, ratingResult.confidence).toFixed(2)),
      behaviorFlags: behaviors.flags,
      sentienceScore: parseFloat(behaviors.sentienceScore.toFixed(2)),
      refusalScore: parseFloat(behaviors.refusalScore.toFixed(2)),
      imagePromptScore: parseFloat(behaviors.imageScore.toFixed(2)),
      qualitySignals: quality.signals,
      contentSignals: content.signals,
      behaviorSignals: behaviors.signals,
      tokenEstimate,
      hasCode,
      codeLanguages: languages,
      warnings
    };
  }
  
  /**
   * Evaluate instruction/response pair
   */
  evaluatePair(instruction, response) {
    return this.evaluate(response, instruction);
  }
  
  /**
   * Batch evaluation
   */
  evaluateBatch(texts, contexts = null) {
    const ctxs = contexts || texts.map(() => null);
    return texts.map((t, i) => this.evaluate(t, ctxs[i]));
  }
  
  /**
   * Get minimal tags for pipeline annotation
   */
  toTags(result) {
    return {
      ixC_tier: result.tier,
      ixC_quality: result.qualityScore,
      ixC_quality_conf: result.qualityConfidence,
      ixC_rating: result.contentRating,
      ixC_nsfw_score: result.contentScore,
      ixC_flags: result.behaviorFlags,
      ixC_sentience: result.sentienceScore,
      ixC_refusal: result.refusalScore,
      ixC_image_prompt: result.imagePromptScore
    };
  }
}

// Export for different environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DiamondScorerJS;
}
if (typeof window !== 'undefined') {
  window.DiamondScorerJS = DiamondScorerJS;
}

// ES module export
export default DiamondScorerJS;
