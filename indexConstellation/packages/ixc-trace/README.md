# xiConversationArchiver

A sovereign tool for backing up ChatGPT conversations.  
No automation, no hidden state, no silent updates.

---

## ⚠️ TRUTH STATEMENT

This tool depends on **ChatGPT's internal backend-api** which may change without warning.

**Your data is encrypted locally.**  
**Your risk is tied to API stability.**

---

## 🚀 Quick Start

```bash
# Install
git clone https://github.com/yourusername/chats-archive.git
cd chats-archive
pip install -e .

# Verify API works
chats-archive verify-api

# Set up authentication
chats-archive auth-setup

# Export conversations
chats-archive export

# View what you archived
chats-archive list
chats-archive read <id>

# Export to readable Markdown
chats-archive export-markdown
```

---

## 🔑 How to Get Your Session Token

This tool requires a ChatGPT **session bearer token** (not an OpenAI API key).

### Steps:

1. **Open ChatGPT** in your browser: https://chatgpt.com

2. **Open Developer Tools**
   - Chrome/Edge: `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
   - Firefox: `F12`

3. **Go to Network tab**

4. **Refresh the page** or send a message

5. **Find a request** to `chatgpt.com/backend-api/*`
   - Click any request starting with `backend-api`

6. **Copy the token**
   - Look in Request Headers for `Authorization`
   - Copy the value after `Bearer ` (the long string)

7. **Store it**
   ```bash
   chats-archive auth-setup
   # Paste token when prompted
   ```

### Token Expiration

- Tokens expire periodically (hours to days)
- If export fails with 401, get a fresh token
- The tool stores tokens in your OS keychain (never plaintext)

---

## 🔧 Commands

| Command | Purpose |
|---------|---------|
| `auth-setup` | Store ChatGPT session token |
| `auth-status` | Validate token and check connectivity |
| `export` | Fetch and archive conversations |
| `import-json` | Import from ChatGPT export file |
| `list` | List all archived conversations |
| `read <id>` | Display a specific conversation |
| `export-markdown` | Export all to readable Markdown files |
| `key-export` | Backup your encryption key |
| `key-import` | Restore encryption key from backup |
| `verify-api` | Test if API endpoints work |
| `diagnose-api` | Diagnose API issues |
| `status` | Show archive statistics |

---


## Security & Threat Model

This tool encrypts conversation content at rest and avoids logging secrets, but it does **not** protect you on a compromised machine and it relies on undocumented ChatGPT endpoints.

- Read: `docs/THREAT_MODEL.md`
- Treat your session token like a password.
- Back up your encryption key securely (lost key = unrecoverable archives).
- Keep your archive directory out of cloud sync and out of repo working trees.
- Do not commit `.env.local`, keys, or archives.

## 🛡️ Security

- **Encryption at rest** – Fernet (AES-128-CBC + HMAC)
- **Token never logged** – Only SHA-256 hashes in audit logs
- **File permissions** – 0600 for sensitive files
- **No network egress** – Only communicates with `chatgpt.com`
- **Key storage** – OS credential manager (Keychain, Credential Manager, secret-service)

### ⚠️ Key Backup

**No built-in automatic key recovery.**

```bash
# Backup your key NOW
chats-archive key-export --output ~/secure/chatgpt-key.txt

# To restore on new machine
chats-archive key-import --file ~/secure/chatgpt-key.txt
```

**Lost key = unrecoverable archives.**

---

## ⚠️ API Dependency

This tool uses **undocumented internal ChatGPT endpoints**:

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `GET /backend-api/conversations` | List conversations | ASSUMED |
| `GET /backend-api/conversation/{id}` | Get full conversation | ASSUMED |

### Before First Use

```bash
chats-archive verify-api
```

### If API Changes

1. Run `chats-archive diagnose-api` for status
2. Check GitHub Issues for known breaks
3. Use `import-json` as fallback (manual ChatGPT export)

---

## 📁 Archive Structure

```
~/.chats_archive/
├── conversations/
│   └── 2025-01-24/
│       └── conv-abc123.enc
├── jobs.db
├── .encryption_key (fallback)
├── .lock
└── audit.log
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Truth before completion.**  
**Sovereignty before convenience.**
