# Privacy Policy - LLM Pair Curator

**Last Updated:** January 26, 2026

## Core Principle: We Don't Have Your Data

This is a **local-first, privacy-preserving** tool. Your conversation data stays on your device unless you explicitly pay for cloud analysis.

---

## What We Collect (Spoiler: Almost Nothing)

### When Using Local Features (Free)

**Data Collected: ZERO**

- Your files are processed in your browser
- No analytics, no tracking, no cookies
- No data leaves your device
- We literally cannot see your data

**Technical Details:**
- Processing: Web Workers (local CPU)
- Storage: Browser IndexedDB (local)
- Network: None (offline-capable)

### When Using Cloud Features (Paid)

**Data Temporarily Processed:**

Only when you:
1. Click "Analyze with Cloud" AND
2. Have paid for credits

We receive:
- The conversation pairs you selected
- Your user ID (to deduct credits)
- Timestamp of request

**Data Retention:**
- Processed for analysis only
- Automatically deleted after 24 hours
- Not used for training our models
- Not shared with anyone
- Not stored long-term

**Technical Details:**
- Transmission: HTTPS (encrypted)
- Processing: Serverless functions (ephemeral)
- Storage: Temporary (auto-deleted)

### Payment Information

**Via Stripe (not us):**
- Credit card details: Stored by Stripe (PCI compliant)
- We receive: User ID, amount paid, timestamp
- We DO NOT see: Card numbers, CVV, billing address

### Cookies & Tracking

**We use:**
- None for analytics
- None for advertising
- Session cookie only (if you log in for cloud features)

**We do NOT use:**
- Google Analytics
- Facebook Pixel
- Third-party trackers
- Fingerprinting

---

## How We Use Information

### Local Features
- No usage data collected
- No analytics
- No tracking
- You're anonymous to us

### Cloud Features
- User ID: Link payments to cloud credits
- Conversation data: Compute quality metrics (then delete)
- Timestamps: Prevent abuse, manage quotas

### We NEVER:
- Sell your data
- Train models on your data
- Share data with third parties
- Use data for advertising
- Re-identify anonymous users

---

## Data Security

### Local Features
- Your data never leaves your device
- Security = your device's security
- Use HTTPS when loading the page
- No server-side vulnerabilities

### Cloud Features (When Used)
- TLS 1.3 encryption in transit
- Encrypted at rest (if temporarily stored)
- Serverless functions (no persistent storage)
- Auto-deletion after 24 hours
- No backups of your data

### In Case of Breach
If our payment system is breached:
- Stripe handles this (not us)
- We notify you within 72 hours
- Your conversation data is unaffected (we don't have it)

---

## Your Rights (GDPR & CCPA Compliant)

### Right to Access
**Local data:** You already have it (it's on your device)
**Cloud data:** Request a copy within 24 hours (before auto-deletion)

### Right to Delete
**Local data:** Clear your browser data
**Cloud data:** Auto-deleted after 24 hours anyway

### Right to Export
**Local data:** Use our export feature
**Cloud data:** Download results before 24-hour deletion

### Right to Opt-Out
**Local features:** No opt-out needed (we don't track)
**Cloud features:** Simply don't use them

### Right to Object
- Object to cloud processing: Don't use cloud features
- Object to payments: Don't purchase credits

---

## Third-Party Services

### We Use:

**Stripe (Payment Processing):**
- Privacy policy: https://stripe.com/privacy
- They handle: Credit cards, billing
- We receive: User ID, payment amount

**[Cloud Provider - AWS/Vercel/Modal]:**
- For serverless functions only
- Processes data temporarily (24hr max)
- Does not retain user data

**OpenAI / Anthropic APIs (Optional):**
- Used only for quality scoring (if you pay)
- Your data is sent to their APIs
- Subject to their privacy policies
- We do not control their data retention

### We Do NOT Use:
- Google Analytics
- Facebook / Social trackers
- Ad networks
- Data brokers

---

## Children's Privacy (COPPA)

This service is not intended for children under 13.

- We do not knowingly collect data from children
- If local-only: No data collected anyway
- If you're a parent: This is a technical tool, not for kids

---

## International Users (GDPR)

**EU/EEA Users:**
- Local features: No data transfer (GDPR compliant by design)
- Cloud features: Data processed in [US/EU - specify region]
- Right to lodge complaint: Contact your data protection authority

**Legal Basis:**
- Legitimate interest: Provide free local tools
- Contract: Deliver paid cloud services
- Consent: Explicit opt-in for cloud features

---

## California Residents (CCPA)

**Do Not Sell My Personal Information:**
- We don't sell your information (period)
- No data to sell (local-first design)

**Your Rights:**
- Right to know: What data we collect (see above)
- Right to delete: Already auto-deleted
- Right to opt-out: Don't use cloud features

---

## Changes to This Policy

- We may update this policy
- Material changes require 30 days notice
- Notice via email (if you have cloud account)
- Notice on website homepage

**Recent Changes:**
- 2026-01-26: Initial version

---

## Data Retention Summary

| Data Type | Retention Period |
|-----------|-----------------|
| Local conversation data | Forever (on your device, your control) |
| Cloud analysis requests | 24 hours (auto-deleted) |
| Payment records | 7 years (tax/legal requirement) |
| User IDs | As long as you have account |
| Analytics | N/A (we don't collect) |

---

## Contact Us

**Privacy Questions:**
Email: [YOUR EMAIL]
Response time: 48 hours

**Data Deletion Requests:**
Email: [YOUR EMAIL]
Response time: 24 hours (but data auto-deletes anyway)

**Data Protection Officer:**
[If required in your jurisdiction]

---

## Summary (Plain English)

**Local features (free):**
- Your data = your device only
- We see NOTHING
- No tracking, no cookies, no BS

**Cloud features (paid):**
- You send data ONLY when you click "Analyze"
- We process it (compute metrics)
- We delete it after 24 hours
- We never train on it or sell it

**Payments:**
- Stripe handles your card (not us)
- We only see: "User X paid $Y"

**Your rights:**
- Export your data anytime
- Delete your data anytime (or wait 24hr)
- Stop using the service anytime

**Trust model:**
- We can't see your local data (even if we wanted to)
- Cloud data is temporary (by design)
- We're transparent about what we do

---

**Questions? Email [YOUR EMAIL]**

---

END OF PRIVACY POLICY
