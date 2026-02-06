# Repair Contract

When the ChatGPT API changes, follow these steps.

---

## Step 1: Diagnose

```bash
chats-archive diagnose-api
```

Save the diagnostic token.

---

## Step 2: Match

Check if this break is known:

1. Look in `docs/BREAKLOG.md` for your diagnostic token
2. Search GitHub Issues
3. Check release notes for patches

---

## Step 3: Act

### If status is `DEPRECATED` or `BLOCKED`:
1. Manual export from ChatGPT web:
   - Settings → Data Controls → Export Data
2. Import with:
   ```bash
   chats-archive import-json --file ~/Downloads/chatgpt_export.json
   ```

### If status is `UNREACHABLE`:
1. Check https://status.openai.com
2. Wait and retry
3. If persistent, treat as `DEPRECATED`

### If status is `OK` but export fails:
1. Renew your ChatGPT token
2. Run `chats-archive auth-setup`
3. Try `chats-archive export --force-refetch`

---

## Step 4: Seek Help

Open a GitHub Issue with:
- Diagnostic token
- Full output of `diagnose-api`
- What you tried

---

## Step 5: Document

If you find a fix:
1. Document in GitHub Issue or PR
2. Update `BREAKLOG.md`
