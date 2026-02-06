# Changelog

## [1.0.0] – 2025-01-24

### Added
- Initial release of xiConversationArchiver
- Local encryption with OS-managed keys
- Stateless deduplication (file existence check)
- Manual import from ChatGPT JSON export
- API endpoint verification command
- Key export/import for backup and recovery
- Conversation listing and reading commands
- Markdown export for readable archives
- Structured audit logging
- Concurrent-run prevention (advisory locks)

### Security
- Fernet encryption at rest
- Token never logged (only hashes)
- File permissions: 0600 for sensitive files
- No network egress beyond `chatgpt.com`

### Philosophy
- No automation – user initiates all exports
- No hidden state – no cron, no daemons
- No silent updates – user chooses when to update
- Truth-first documentation – declares API dependency risk

### Known Limitations
- Depends on ChatGPT internal API (may break)
- User responsible for key backup
- No incremental sync – full metadata fetch each run
