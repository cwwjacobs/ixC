# ixCurator User Guide

**Welcome to ixCurator** - your privacy-first tool for curating conversation datasets for AI training.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [What is ixCurator?](#what-is-ixcurator)
3. [Getting Started](#getting-started)
4. [Loading Your Conversations](#loading-your-conversations)
5. [Understanding the Interface](#understanding-the-interface)
6. [Understanding Metrics](#understanding-metrics)
7. [Filtering Conversations](#filtering-conversations)
8. [Exporting Your Dataset](#exporting-your-dataset)
9. [Common Use Cases](#common-use-cases)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)
12. [Tips & Best Practices](#tips--best-practices)

---

## Quick Start

**5-Minute Tutorial:**

1. **Visit ixCurator:** https://[your-github-username].github.io/ixCurator/
2. **Download test data:** Right-click [sample-conversations.jsonl](sample-conversations.jsonl) → Save
3. **Load the file:** Click "📁 Load File" → Select `sample-conversations.jsonl`
4. **Explore:** Watch metrics appear, try filters
5. **Export:** Click "💾 Export" → Choose JSONL

**That's it! You just curated your first dataset.**

---

## What is ixCurator?

### The Problem
You have conversations with ChatGPT or Claude. You want to use them to fine-tune an AI model. But:
- Which conversations are high quality?
- Which have good technical content vs. casual chat?
- How do you filter thousands of conversations?
- How do you prove your dataset composition for compliance?

### The Solution
ixCurator analyzes conversations and helps you:
- **Filter** by quality ("signal density")
- **Classify** by type (code, reasoning, creative, etc.)
- **Export** in training-ready formats
- **Document** provenance for compliance (EU AI Act ready)

### Why ixCurator?
- ✅ **Privacy-first** - Runs in your browser, data never uploaded
- ✅ **Free** - No subscription, no limits
- ✅ **Fast** - Process thousands of conversations in seconds
- ✅ **Compliant** - EU AI Act-ready provenance tracking
- ✅ **Open source** - Audit the code yourself

---

## Getting Started

### Requirements
- **Browser:** Chrome, Firefox, Safari, or Edge (any modern browser)
- **No installation required** - Just visit the website
- **Works offline** - Once loaded, no internet needed

### First Time Setup
1. Visit ixCurator website
2. Bookmark it (optional)
3. That's it! No signup, no account needed.

### Privacy Notice
**Your data stays on your device.** ixCurator:
- ❌ Does NOT upload your conversations
- ❌ Does NOT track you
- ❌ Does NOT use cookies or analytics
- ✅ Processes everything locally in your browser

---

## Loading Your Conversations

### Supported Formats

ixCurator works with:
- **JSON** (single file with array of conversations)
- **JSONL** (JSON Lines - one conversation per line)

### Where to Get Conversation Files

**ChatGPT:**
1. Go to ChatGPT settings
2. Click "Data controls"
3. Click "Export data"
4. Wait for email with download link
5. Download and unzip
6. Load `conversations.json` into ixCurator

**Claude:**
1. In a conversation, click "..." menu
2. Select "Export conversation"
3. Save as JSON
4. Load into ixCurator

**API Logs:**
- If you've saved API request/response logs
- Format as JSONL (one conversation per line)
- Load into ixCurator

### File Format Requirements

**Minimal format:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ]
}
```

**Supported variations:**
- `messages`, `conversation`, or `turns` (conversation array)
- `role` or `sender` (who's speaking)
- `content`, `text`, or `message` (what they said)

ixCurator auto-detects and normalizes different formats.

### How to Load

**Method 1: Click Button**
1. Click "📁 Load File" button
2. Select your JSON/JSONL file
3. Wait for analysis (a few seconds)

**Method 2: Drag & Drop**
1. Drag your file from file browser
2. Drop onto the ixCurator window
3. Wait for analysis

---

## Understanding the Interface

### Layout

```
┌─────────────────────────────────────────┐
│  [📁 Load] [💾 Export] [🗑️ Clear]       │  ← Toolbar
├─────────────┬───────────────────────────┤
│  Filters &  │  Conversation List        │
│  Stats      │                           │
│             │  ✓ conv_001 (Code)        │
│  📊 Stats   │  ✓ conv_002 (Reasoning)   │
│  🎯 Filters │  ✓ conv_003 (Technical)   │
│  📈 Density │  ...                      │
│  🎛️ Advanced│                           │
│             │                           │
└─────────────┴───────────────────────────┘
```

### Sidebar (Left)

**Dataset Stats:**
- Total conversations loaded
- How many pass your filters
- How many you've selected
- Average signal density

**Filters:**
- Corpus type (code, reasoning, etc.)
- Density range (quality threshold)
- Advanced filters (tokens, turns, features)

### Main Area (Right)

**Conversation List:**
- Each conversation shown as a card
- Shows: ID, type, token count, turn count, density score
- Click to select/deselect
- Checkmark (✓) = passes filters
- X mark (✗) = filtered out

---

## Understanding Metrics

### Signal Density (0-10 score)

**What it measures:** Information quality per token

**Higher scores mean:**
- More unique vocabulary (not repetitive)
- More technical terms
- Includes code or reasoning
- Less filler ("I understand", "Let me help")

**Score guide:**
- **0-3:** Low quality (casual chat, lots of filler)
- **4-6:** Medium quality (some useful info)
- **7-8:** High quality (substantive content)
- **9-10:** Excellent (dense technical/educational content)

**Example:**
```
Low density (2.5):
User: "hey whats up"
Assistant: "Hello! I'm doing well, thank you for asking. 
How can I help you today?"

High density (8.2):
User: "Implement binary search in Python"
Assistant: "Here's an efficient O(log n) implementation:
```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```
Time complexity: O(log n), Space: O(1)"
```

### Corpus Type

**Automatic classification based on content:**

- **Code:** Contains programming code, functions, algorithms
- **Reasoning:** Shows step-by-step thinking, analysis
- **Creative:** Stories, creative writing, poems
- **Technical:** Technical explanations without code
- **Chat:** Casual conversation, greetings, simple Q&A

### Other Metrics

**Token Count:**
- Approximate word count × 0.75
- Useful for training data budgets

**Turn Count:**
- Number of back-and-forth exchanges
- Multi-turn conversations often higher quality

**Has Code:**
- Detects code blocks (```)
- Detects function keywords

**Has Reasoning:**
- Detects reasoning phrases
- "step by step", "therefore", "because", etc.

---

## Filtering Conversations

### Corpus Type Filter

**Use when:**
- You want only coding conversations
- You need reasoning examples
- You want to exclude casual chat

**How to use:**
1. Check/uncheck corpus types in sidebar
2. List updates immediately
3. Stats show how many match

**Example:**
- Training a code model? → Check only "Code"
- Training reasoning? → Check "Reasoning" + "Technical"
- Diverse dataset? → Check all types

### Density Filter

**Use when:**
- You want only high-quality conversations
- You need to filter low-effort exchanges

**How to use:**
1. Drag "Minimum" slider (e.g., 7.0)
2. Drag "Maximum" slider (e.g., 10.0)
3. Only conversations in range shown

**Recommended thresholds:**
- **7.0+:** High quality dataset
- **5.0+:** Medium quality, more data
- **3.0+:** Include everything except junk

### Advanced Filters

**Token Range:**
- Minimum: Filter out too-short conversations
- Maximum: Filter out extremely long ones
- Typical: 100-2000 tokens

**Turn Count:**
- Minimum: Multi-turn conversations only
- Maximum: Exclude marathon sessions
- Typical: 2-20 turns

**Feature Filters:**
- "Has Code Blocks" → Only conversations with code
- "Has Reasoning" → Only conversations showing thought process

### Combining Filters

**Example: High-Quality Code Dataset**
```
Corpus Type: ✓ Code only
Density: 7.0 - 10.0
Tokens: 200 - 1500
Has Code: ✓ Yes
```

**Example: Diverse Reasoning Dataset**
```
Corpus Type: ✓ Reasoning, ✓ Technical
Density: 6.0 - 10.0
Tokens: 300 - 2000
Has Reasoning: ✓ Yes
```

---

## Exporting Your Dataset

### Export Formats

**JSONL (Recommended for training):**
```jsonl
{"messages": [...], "metrics": {...}}
{"messages": [...], "metrics": {...}}
```
- One conversation per line
- Standard for LLM training
- Works with most training tools

**JSON (Readable format):**
```json
[
  {"messages": [...], "metrics": {...}},
  {"messages": [...], "metrics": {...}}
]
```
- Pretty-printed, indented
- Good for inspection
- Larger file size

**CSV (Spreadsheet format):**
```csv
id,type,tokens,turns,density
conv_001,code,1234,8,8.2
conv_002,reasoning,890,5,7.5
```
- Open in Excel/Google Sheets
- Good for analysis
- Doesn't include full conversation text

### Export Options

**What to export:**
1. Click "💾 Export"
2. Choose format (1=JSONL, 2=JSON, 3=CSV)
3. File downloads automatically

**What gets exported:**
- **Current filters applied:** Only conversations that pass filters
- **Metrics included:** All computed scores
- **Original messages:** Preserved exactly

### Provenance Export (Optional)

**If you want compliance-ready exports:**

1. Select "Compliance-Ready Export"
2. Fill in attestation form:
   - Your name/organization
   - Data source
   - Intended use
   - Compliance declarations
3. Export includes `_xi_provenance` metadata

**Use when:**
- Training production models
- Need audit trail
- EU AI Act compliance required
- Want to prove dataset composition

---

## Common Use Cases

### Use Case 1: Fine-Tuning a Code Assistant

**Goal:** Create dataset of high-quality coding conversations

**Steps:**
1. Load your ChatGPT/Claude export
2. Filters:
   - Corpus Type: ✓ Code only
   - Density: 7.5 - 10.0
   - Has Code: ✓ Yes
3. Review: Check you have 100-1000 examples
4. Export: JSONL format
5. Use with: OpenAI fine-tuning, Axolotl, etc.

**Expected results:**
- 5-20% of conversations pass (that's normal!)
- High-quality code examples
- Training-ready format

---

### Use Case 2: Research Dataset

**Goal:** Create diverse, well-documented dataset for research

**Steps:**
1. Load conversations
2. Filters:
   - Corpus Type: All types
   - Density: 5.0 - 10.0
   - Tokens: 200 - 2000
3. Enable provenance export
4. Attest:
   - Research purpose
   - Academic use
   - Source: Personal conversations
5. Export: JSONL with provenance

**Expected results:**
- Auditable dataset
- Diverse conversation types
- Publication-ready documentation

---

### Use Case 3: Quality Analysis

**Goal:** Understand what's in your conversation history

**Steps:**
1. Load all conversations
2. Don't filter yet
3. Look at stats:
   - How many of each type?
   - What's the average density?
   - Token distribution?
4. Adjust filters to explore
5. Optional: Export CSV for spreadsheet analysis

**Expected results:**
- Understand your conversation patterns
- Find high-quality examples
- Data for blog post / analysis

---

### Use Case 4: Compliance Documentation

**Goal:** Prove dataset composition for regulatory compliance

**Steps:**
1. Load conversations
2. Apply quality filters
3. Enable provenance export
4. Attest ALL required fields:
   - Organization details
   - Legal basis for data
   - Copyright clearance
   - Intended use
   - Compliance declarations
5. Export with cryptographic signatures

**Expected results:**
- EU AI Act-ready dataset
- Cryptographic audit trail
- Legally defensible documentation

---

## Troubleshooting

### Problem: File Won't Load

**Symptoms:** Click "Load File", select file, nothing happens

**Solutions:**
1. **Check file format:** Must be `.json` or `.jsonl`
2. **Check file size:** Browser may struggle with >100MB files
3. **Check JSON validity:** Use JSONLint.com to validate
4. **Try different browser:** Chrome handles large files best
5. **Check console:** Press F12, look for error messages

**Common causes:**
- Corrupted export file
- Invalid JSON syntax
- Browser memory limits
- File too large

---

### Problem: No Conversations After Filtering

**Symptoms:** Load file successfully, but 0 conversations after filters

**Solutions:**
1. **Reset all filters:**
   - Check all corpus types
   - Set density to 0.0 - 10.0
   - Set tokens to 0 - 5000
2. **Check your thresholds:** Maybe too strict?
3. **Look at raw stats:** What's the average density of your data?

**Example:**
- If average density is 4.5
- And you filter for 7.0+
- You'll exclude most conversations
- Solution: Lower threshold or improve conversation quality

---

### Problem: Export Doesn't Work

**Symptoms:** Click export, nothing downloads

**Solutions:**
1. **Check browser popup blocker**
2. **Try different export format**
3. **Check disk space**
4. **Try smaller dataset** (select fewer conversations)

---

### Problem: Metrics Seem Wrong

**Symptoms:** Density scores don't match your intuition

**Remember:**
- Metrics are heuristic, not perfect
- Short conversations score lower (less data)
- Filler language reduces scores
- Code presence boosts scores

**If truly wrong:**
- Check if conversation was parsed correctly
- Look at actual content
- Metrics are starting point, use judgment

---

### Problem: Slow Performance

**Symptoms:** Takes forever to analyze conversations

**Solutions:**
1. **Close other browser tabs** (free up memory)
2. **Process smaller batches** (<1000 at a time)
3. **Use faster browser** (Chrome > Firefox > Safari)
4. **Check computer resources** (CPU/RAM usage)

**Normal performance:**
- 100 conversations: <1 second
- 1,000 conversations: 2-5 seconds
- 10,000 conversations: 10-30 seconds

---

## FAQ

### General Questions

**Q: Is this really free?**  
A: Yes. Free forever for local processing. Optional paid features coming later for cloud-based analysis.

**Q: Do you see my data?**  
A: No. Everything runs in your browser. We literally cannot access your conversations.

**Q: Can I use this offline?**  
A: Yes! Once the page loads, you can disconnect from internet.

**Q: Does this work on mobile?**  
A: Yes, but desktop is better for large datasets.

---

### Data & Privacy

**Q: Where is my data stored?**  
A: In your browser's local storage (IndexedDB). Never uploaded anywhere.

**Q: Can I delete my data?**  
A: Clear your browser data or click "🗑️ Clear" in ixCurator.

**Q: Is this GDPR compliant?**  
A: Yes. Since data never leaves your device, there's nothing to be non-compliant about.

**Q: What if I accidentally upload sensitive data?**  
A: You can't "upload" - there's no server to upload to. It only processes locally.

---

### Features & Usage

**Q: Can I edit conversations before export?**  
A: Not yet. Current version is filter-only. Editing coming in future update.

**Q: Can I merge multiple export files?**  
A: Load them separately, export each, then combine the JSONL files manually.

**Q: Can I save filter presets?**  
A: Not yet. Coming in future update. For now, screenshot your settings.

**Q: What's the maximum file size?**  
A: Depends on your computer. Tested up to 50MB (tens of thousands of conversations).

---

### Technical Questions

**Q: What format does this export for fine-tuning?**  
A: JSONL with `messages` array - compatible with OpenAI, Anthropic, HuggingFace, Axolotl.

**Q: Can I use this for RLHF / preference tuning?**  
A: Yes for initial data filtering. You'll need to add preference labels separately.

**Q: Does this work with GPT-4, Claude, other models?**  
A: Works with conversation exports from any source. Format is universal.

**Q: Can I customize the density calculation?**  
A: Not in the UI. But it's open source - you can fork and modify.

---

### Provenance & Compliance

**Q: Do I need provenance for personal projects?**  
A: No. Provenance is optional - only needed for compliance/production use.

**Q: Does provenance make this legally compliant?**  
A: It provides the framework. YOU attest to compliance. Consult a lawyer for legal questions.

**Q: Can I use this for commercial training?**  
A: Yes, but YOU are responsible for copyright clearance and compliance.

**Q: What's the EU AI Act?**  
A: European regulation requiring documentation of training data. ixCurator provides compliance-ready provenance.

---

## Tips & Best Practices

### Curation Strategy

**Start Broad, Then Narrow:**
1. Load all your data first
2. Look at overall stats
3. Understand what you have
4. Then apply filters

**Quality Over Quantity:**
- 100 high-quality examples > 1000 mediocre ones
- Aim for density 7.0+ for production training
- Don't be afraid to exclude 80% of conversations

**Diverse Types:**
- Mix of corpus types often better than single type
- Code + Reasoning works well together
- Pure chat rarely useful for training

### Filter Recommendations

**For Code Models:**
```
Corpus: Code only
Density: 7.5+
Has Code: Yes
Tokens: 200-1500
```

**For Reasoning Models:**
```
Corpus: Reasoning + Technical
Density: 7.0+
Has Reasoning: Yes
Tokens: 300-2000
```

**For General Assistant:**
```
Corpus: All types
Density: 6.0+
Tokens: 150-2000
Turns: 2+
```

### Export Tips

**Always export to JSONL first:**
- Most compatible format
- Smallest file size
- Training-ready

**Keep original exports:**
- Don't delete your ChatGPT/Claude exports
- You might want to re-filter later
- ixCurator doesn't modify originals

**Name files descriptively:**
```
✅ Good: code-conversations-high-quality-2026-01.jsonl
❌ Bad: export.jsonl
```

### Provenance Best Practices

**Only use provenance when needed:**
- Personal projects: Skip it
- Research/academic: Use it
- Commercial/production: Definitely use it

**Be honest in attestations:**
- Don't claim copyright clearance if unsure
- Don't attest compliance you can't prove
- When in doubt, consult a lawyer

**Keep records:**
- Save provenance exports separately
- Document your curation decisions
- Maintain audit trail

---

## Getting Help

### Documentation
- **This guide:** Comprehensive usage instructions
- **README.md:** Technical overview
- **GitHub Issues:** Bug reports and feature requests

### Community
- **GitHub Discussions:** Ask questions, share tips
- **Discord:** [Link if you create one]

### Support
- **Email:** [your-email] for serious issues
- **Response time:** Best effort, usually 24-48 hours
- **Bug reports:** GitHub Issues preferred

---

## What's Next?

### Upcoming Features (Roadmap)
- 🔄 **Conversation editing** (modify before export)
- 💾 **Filter presets** (save common filter combinations)
- 🔍 **Search** (find specific conversations)
- 📊 **Advanced analytics** (distribution charts)
- ☁️ **Cloud features** (LLM-powered quality scoring)

### Stay Updated
- **Watch repo:** Get notified of updates
- **Star repo:** Show support
- **Contribute:** Pull requests welcome!

---

## Contributing

ixCurator is open source. You can help by:

**Reporting Bugs:**
1. Check if already reported
2. Include: browser, file size, error message
3. Steps to reproduce

**Suggesting Features:**
1. Open GitHub Issue
2. Describe use case
3. Why it's valuable

**Contributing Code:**
1. Fork repository
2. Make changes
3. Submit pull request
4. Follow code style

---

## Appendix: Supported Conversation Formats

### OpenAI API Format
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ]
}
```

### Anthropic API Format
```json
{
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ]
}
```

### ChatGPT Export Format
```json
{
  "title": "Conversation Title",
  "create_time": 1234567890,
  "mapping": {
    "...": {
      "message": {
        "role": "user",
        "content": {"parts": ["Hello"]}
      }
    }
  }
}
```

ixCurator normalizes all these automatically.

---

**End of User Guide**

**Questions? Check the FAQ or open a GitHub Issue.**

**Happy curating! 🚀**
