# Threat Model — Archivist (xiConversationArchiver)

## Scope and goals
**Goal:** Export ChatGPT conversations and store them locally with encryption at rest, minimizing secret leakage and preserving auditability.

**Non-goals:**
- Defending against a fully compromised host OS.
- Bypassing ChatGPT/OpenAI controls.
- Providing anonymity/anti-forensics.
- Unattended automation.

## Assets
- Conversation content (highest sensitivity)
- Session bearer token
- Encryption key
- Metadata and operational logs

## Trust boundaries
- Local machine boundary (filesystem, process memory, OS credential store)
- Network boundary (HTTPS to chatgpt.com backend-api)
- User boundary (manual token retrieval and CLI initiation)

## Threats and mitigations (summary)
- Token exfiltration: prefer OS credential store; never log tokens; warn on env fallback.
- Key theft/loss: OS keyring preferred; local fallback restricted perms; user must back up key securely.
- Archive theft: ciphertext protected; metadata may leak.
- Tamper/corruption: fail-closed reads via checksum verification; archive-wide verification.
- Wrong-key usage: archive manifest key fingerprint binding; explicit wrong-key error codes.
- API drift: verify/diagnose tooling; treat as operational risk; manual export/import fallback.

## Residual risk
If the host is compromised, confidentiality is lost. API endpoints are undocumented and may change without warning.
