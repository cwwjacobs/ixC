# Storage Format Migrations

This directory contains migration scripts for storage format changes.

## Current Version
- **1.0** – Initial versioned format

## Migration Policy
1. Never break backward compatibility without a migration path
2. Migration scripts must be idempotent
3. Archive files are never automatically rewritten; migration is opt-in

## Running Migrations
```bash
python migrations/v1.0_to_v1.1.py --archive-dir ~/.chats_archive
```
