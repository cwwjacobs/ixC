#!/usr/bin/env python3
"""
xiConversationArchiver - Command Line Interface

Commands:
  auth-setup      Store ChatGPT session token
  auth-status     Check token validity
  export          Fetch and archive conversations
  import-json     Import from ChatGPT export file
  list            List archived conversations
  read            Read a specific conversation
  export-markdown Export all to Markdown files
  key-export      Backup encryption key
  key-import      Restore encryption key
  verify-api      Test API endpoints
  diagnose-api    Diagnose API issues
  verify-archive  Verify archive integrity (operator)
  status          Show archive statistics
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

from chats_archive.auth import TokenManager, ProtectedLogger
from chats_archive.orchestrator import ArchiveOrchestrator
from chats_archive.storage import LocalEncryptedStore, EncryptionKeyManager
from chats_archive.fetcher import ConversationFetcher, APIStatus
from chats_archive.importer import ManualImporter


def auth_setup(args):
    """Set up authentication token."""
    token = args.token
    if not token:
        print("Enter your ChatGPT session bearer token.")
        print("(See README for how to obtain this)")
        token = input("> ").strip()
    
    manager = TokenManager()
    if manager.store_token(token, force_env_fallback=args.force_env_fallback):
        print("✅ Token stored successfully")
        return 0
    else:
        print("❌ Failed to store token")
        return 1


def auth_status(args):
    """Check authentication status."""
    manager = TokenManager()
    token = manager.retrieve_token()
    
    if token:
        print("✅ Authentication token found")
        print(f"   Token hash: {manager.token_hash(token)}")
        
        fetcher = ConversationFetcher(token, ProtectedLogger())
        if fetcher.validate_token():
            print("   Token validated with ChatGPT API")
        else:
            print("   ⚠️  Token may be invalid or expired")
        return 0
    else:
        print("❌ No authentication token found")
        print("   Run: chats-archive auth-setup")
        return 1


def export(args):
    """Export conversations."""
    logger = ProtectedLogger()
    token_manager = TokenManager()
    
    try:
        orchestrator = ArchiveOrchestrator(
            token_manager=token_manager,
            archive_dir=args.archive_dir,
            logger=logger
        )
        job_id = orchestrator.run_export(
            resume_job_id=args.resume,
            force_refetch=args.force_refetch
        )
        print(f"\n✅ Export job completed: {job_id}")
        return 0
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return 1


def import_json(args):
    """Import from ChatGPT export JSON."""
    try:
        store = LocalEncryptedStore(args.archive_dir)
        importer = ManualImporter(store)
        count = importer.import_from_file(args.file)
        if count > 0:
            print(f"✅ Imported {count} conversations")
        else:
            print("⚠️  No conversations were imported")
        return 0
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return 1


def list_conversations(args):
    """List all archived conversations."""
    store = LocalEncryptedStore(args.archive_dir)
    archive_path = store.conversations_dir
    
    if not archive_path.exists():
        print("No archive found.")
        return 0
    
    conversations = []
    
    for date_dir in sorted(archive_path.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for filepath in date_dir.glob("conv-*.enc"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                metadata = data.get("metadata", {})
                conversations.append({
                    "id": metadata.get("id", filepath.stem.replace("conv-", ""))[:8],
                    "title": metadata.get("title", "Untitled"),
                    "date": date_dir.name
                })
            except Exception:
                continue
    
    if not conversations:
        print("No archived conversations found.")
        return 0
    
    print(f"{'ID':<10} {'Date':<12} {'Title'}")
    print("-" * 60)
    for c in conversations:
        title = c["title"][:35] + "..." if len(c["title"]) > 35 else c["title"]
        print(f"{c['id']:<10} {c['date']:<12} {title}")
    
    print(f"\nTotal: {len(conversations)} conversations")
    return 0


def read_conversation(args):
    """Decrypt and display a conversation (fails closed if integrity is not VALID)."""
    store = LocalEncryptedStore(args.archive_dir)

    integrity = store.verify_conversation(args.id)
    if integrity.state.value != 'valid':
        print(f"❌ Conversation {args.id} is not readable as VALID")
        print(f"   State: {integrity.state.value}")
        if integrity.error_code:
            print(f"   Error: {integrity.error_code}")
        if integrity.filepath:
            print(f"   File: {integrity.filepath}")
        return 1

    conv = store.retrieve_conversation(args.id)
    if not conv:
        print(f"❌ Conversation {args.id} could not be loaded")
        return 1
    
    title = conv.get("title", "Untitled")
    print(f"# {title}\n")
    
    mapping = conv.get("mapping", {})
    
    # Find root (no parent)
    root_id = None
    for node_id, node in mapping.items():
        if node.get("parent") is None:
            root_id = node_id
            break
    
    def walk(node_id):
        node = mapping.get(node_id, {})
        msg = node.get("message")
        
        if msg and msg.get("content"):
            role = msg.get("author", {}).get("role", "unknown")
            parts = msg.get("content", {}).get("parts", [])
            text = "".join(str(p) for p in parts if isinstance(p, str))
            
            if text.strip():
                if role == "user":
                    print(f"**User:**\n{text}\n")
                elif role == "assistant":
                    print(f"**Assistant:**\n{text}\n")
                print("---\n")
        
        for child_id in node.get("children", []):
            walk(child_id)
    
    if root_id:
        walk(root_id)
    else:
        print("(Could not parse conversation structure)")
    
    return 0


def export_markdown(args):
    """Export all conversations to Markdown files."""
    store = LocalEncryptedStore(args.archive_dir)
    output_dir = Path(args.output).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    archive_path = store.conversations_dir
    
    if not archive_path.exists():
        print("No archive found.")
        return 0
    
    exported = 0
    failed = 0
    
    for date_dir in archive_path.iterdir():
        if not date_dir.is_dir():
            continue
        for filepath in date_dir.glob("conv-*.enc"):
            try:
                wrapper = None
                try:
                    with open(filepath, "r") as f:
                        wrapper = json.load(f)
                except Exception:
                    wrapper = None

                md_meta = wrapper.get("metadata", {}) if isinstance(wrapper, dict) else {}
                conv_id = md_meta.get("id") or md_meta.get("conversation_id") or "unknown"
                integrity = store.verify_conversation(conv_id)
                if integrity.state.value != 'valid':
                    failed += 1
                    continue

                conv = store.retrieve_conversation(conv_id)
                if not conv:
                    failed += 1
                    continue
                
                md = format_conversation_markdown(conv)
                
                title = conv.get("title", "untitled")[:50]
                safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
                safe_title = safe_title.strip().replace(" ", "_")
                
                out_file = output_dir / f"{date_dir.name}_{safe_title}_{conv_id[:8]}.md"
                out_file.write_text(md, encoding="utf-8")
                exported += 1
                
            except Exception as e:
                print(f"  ✗ {filepath.name}: {e}")
                failed += 1
    
    print(f"✅ Exported {exported} conversations to {output_dir}")
    if failed:
        print(f"⚠️  Failed: {failed}")
    return 0


def format_conversation_markdown(conv: dict) -> str:
    """Convert conversation dict to Markdown string."""
    lines = []
    
    title = conv.get("title", "Untitled")
    lines.append(f"# {title}\n")
    
    create_time = conv.get("create_time")
    if create_time:
        dt = datetime.fromtimestamp(create_time)
        lines.append(f"*Created: {dt.strftime('%Y-%m-%d %H:%M')}*\n")
    
    lines.append("---\n")
    
    mapping = conv.get("mapping", {})
    
    root_id = None
    for node_id, node in mapping.items():
        if node.get("parent") is None:
            root_id = node_id
            break
    
    def walk(node_id):
        node = mapping.get(node_id, {})
        msg = node.get("message")
        
        if msg and msg.get("content"):
            role = msg.get("author", {}).get("role", "unknown")
            parts = msg.get("content", {}).get("parts", [])
            text = "".join(str(p) for p in parts if isinstance(p, str))
            
            if text.strip():
                if role == "user":
                    lines.append(f"## User\n\n{text}\n")
                elif role == "assistant":
                    lines.append(f"## Assistant\n\n{text}\n")
                lines.append("---\n")
        
        for child_id in node.get("children", []):
            walk(child_id)
    
    if root_id:
        walk(root_id)
    
    return "\n".join(lines)


def key_export(args):
    """Export encryption key for backup."""
    manager = EncryptionKeyManager()
    
    key = None
    
    if manager.keyring:
        key = manager.keyring.get_password(manager.SERVICE_NAME, manager.KEY_NAME)
    
    if not key:
        key_file = Path.home() / ".chats_archive" / ".encryption_key"
        if key_file.exists():
            key = key_file.read_text().strip()
    
    if not key:
        print("❌ No encryption key found")
        print("   Run an export first to generate a key")
        return 1
    
    print("=" * 60)
    print("⚠️  ENCRYPTION KEY - HANDLE WITH CARE")
    print("=" * 60)
    print()
    print("This key decrypts ALL your archived conversations.")
    print()
    print("DO:")
    print("  • Store in a password manager")
    print("  • Save to encrypted storage")
    print("  • Keep offline backup")
    print()
    print("DO NOT:")
    print("  • Share with anyone")
    print("  • Commit to git")
    print("  • Store in plaintext on cloud sync")
    print()
    print("=" * 60)
    
    if args.output:
        import os
        out_path = Path(args.output).expanduser()
        out_path.write_text(key)
        os.chmod(out_path, 0o600)
        print(f"✅ Key written to: {out_path}")
    else:
        print(f"KEY: {key}")
    
    print("=" * 60)
    return 0


def key_import(args):
    """Import encryption key from backup."""
    from cryptography.fernet import Fernet
    import os
    
    if args.file:
        key_path = Path(args.file).expanduser()
        if not key_path.exists():
            print(f"❌ File not found: {args.file}")
            return 1
        key = key_path.read_text().strip()
    elif args.key:
        key = args.key.strip()
    else:
        print("Enter encryption key:")
        key = input().strip()
    
    try:
        Fernet(key.encode())
    except Exception:
        print("❌ Invalid key format")
        print("   Expected: Fernet key (base64 string, 44 characters)")
        return 1
    
    manager = EncryptionKeyManager()
    
    if manager.keyring:
        try:
            manager.keyring.set_password(manager.SERVICE_NAME, manager.KEY_NAME, key)
            print("✅ Key imported to OS credential manager")
            return 0
        except Exception as e:
            print(f"⚠️  Could not store in credential manager: {e}")
    
    key_file = Path.home() / ".chats_archive" / ".encryption_key"
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_text(key)
    os.chmod(key_file, 0o600)
    print(f"✅ Key imported to {key_file}")
    
    return 0


def verify_api(args):
    """Verify API endpoints are working."""
    import requests
    
    token_manager = TokenManager()
    token = token_manager.retrieve_token()
    
    if not token:
        print("❌ No token found. Run: chats-archive auth-setup")
        return 1
    
    base_url = "https://chatgpt.com/backend-api"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "chats-archive/1.0"
    }
    
    print("🔍 Verifying API endpoints...\n")
    
    results = []
    
    # Test 1: List conversations
    print("1. Testing /conversations endpoint...")
    try:
        resp = requests.get(
            f"{base_url}/conversations",
            params={"limit": 1},
            headers=headers,
            timeout=10
        )
        results.append({
            "endpoint": "/conversations",
            "status": resp.status_code,
            "ok": resp.status_code == 200
        })
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            print(f"   ✅ Status: {resp.status_code}")
            print(f"   ✅ Returned {len(items)} conversation(s)")
            
            if items:
                conv_id = items[0].get("id")
                print(f"\n2. Testing /conversation/{{id}} endpoint...")
                
                resp2 = requests.get(
                    f"{base_url}/conversation/{conv_id}",
                    headers=headers,
                    timeout=10
                )
                results.append({
                    "endpoint": f"/conversation/{{id}}",
                    "status": resp2.status_code,
                    "ok": resp2.status_code == 200
                })
                if resp2.status_code == 200:
                    print(f"   ✅ Status: {resp2.status_code}")
                else:
                    print(f"   ❌ Status: {resp2.status_code}")
        else:
            print(f"   ❌ Status: {resp.status_code}")
            if resp.status_code == 401:
                print("   → Token invalid or expired")
            elif resp.status_code == 403:
                print("   → Access forbidden")
    
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed")
        results.append({"endpoint": "/conversations", "status": "UNREACHABLE", "ok": False})
    except requests.exceptions.Timeout:
        print("   ❌ Request timeout")
        results.append({"endpoint": "/conversations", "status": "TIMEOUT", "ok": False})
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append({"endpoint": "/conversations", "status": "ERROR", "ok": False})
    
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    all_ok = all(r.get("ok") for r in results)
    
    for r in results:
        icon = "✅" if r["ok"] else "❌"
        print(f"{icon} {r['endpoint']}: {r['status']}")
    
    if all_ok:
        print("\n✅ API verification passed")
        print("   You can proceed with: chats-archive export")
    else:
        print("\n❌ API verification failed")
        print("   Check your token or try again later")
    
    return 0 if all_ok else 1


def diagnose_api(args):
    """Diagnose API status."""
    token_manager = TokenManager()
    token = token_manager.retrieve_token()
    
    if not token:
        print("❌ No authentication token found")
        print("   Run: chats-archive auth-setup first")
        return 1
    
    print("🔍 Running API diagnostic...")
    print("-" * 50)
    
    fetcher = ConversationFetcher(token, ProtectedLogger())
    status, message = fetcher.validate_api_status()
    
    print(f"Status: {status.value.upper()}")
    print(f"Message: {message}")
    print("-" * 50)
    
    diagnostic_token = f"break-{status.value}-{hash(message) % 10000:04d}"
    print(f"\nDiagnostic token: {diagnostic_token}")
    return 0



def verify_archive_cmd(args):
    """Verify archive integrity without emitting conversation content."""
    store = LocalEncryptedStore(args.archive_dir)
    report = store.verify_archive()
    counts = report.get("counts", {})
    problems = report.get("problems", [])
    total = report.get("total_files", 0)

    print("🔎 Archive Verification")
    print("-" * 50)
    print(f"Total files: {total}")
    for k in sorted(counts.keys()):
        print(f"{k}: {counts[k]}")
    print("-" * 50)

    if problems:
        print("Problems:")
        for p in problems[:50]:
            cid = p.get("conversation_id", "unknown")
            state = p.get("state", "unknown")
            code = p.get("error_code", "")
            fp = p.get("filepath", "")
            print(f" - {cid[:12]}  {state}  {code}  {fp}")
        if len(problems) > 50:
            print(f"… and {len(problems) - 50} more")
        return 2

    print("✅ Archive verified (no problems detected)")
    return 0

def status(args):
    """Show archive status."""
    store = LocalEncryptedStore(args.archive_dir)
    stats = store.get_storage_stats()
    
    print("📊 Archive Status")
    print("-" * 50)
    print(f"Total conversations: {stats['total_conversations']}")
    print(f"Total size: {stats['total_size_bytes'] / 1024 / 1024:.1f} MB")
    if stats['total_conversations'] > 0:
        print(f"Oldest conversation: {stats['oldest_conversation'].date()}")
        print(f"Newest conversation: {stats['newest_conversation'].date()}")
    print("-" * 50)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="xiConversationArchiver - Sovereign ChatGPT backup tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  auth-setup       Store ChatGPT session token
  auth-status      Check token validity
  export           Fetch and archive conversations
  import-json      Import from ChatGPT export file
  list             List archived conversations
  read             Read a specific conversation
  export-markdown  Export all to Markdown files
  key-export       Backup encryption key
  key-import       Restore encryption key
  verify-api       Test API endpoints
  diagnose-api     Diagnose API issues
  status           Show archive statistics
"""
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # auth-setup
    p = subparsers.add_parser("auth-setup", help="Set up authentication token")
    p.add_argument("--token", help="ChatGPT session bearer token")
    p.add_argument("--force-env-fallback", action="store_true")
    p.set_defaults(func=auth_setup)
    
    # auth-status
    p = subparsers.add_parser("auth-status", help="Check authentication status")
    p.set_defaults(func=auth_status)
    
    # export
    p = subparsers.add_parser("export", help="Export conversations")
    p.add_argument("--archive-dir", default="~/.chats_archive")
    p.add_argument("--resume", help="Resume a previous export job")
    p.add_argument("--force-refetch", action="store_true")
    p.set_defaults(func=export)
    
    # import-json
    p = subparsers.add_parser("import-json", help="Import from ChatGPT export JSON")
    p.add_argument("--file", "-f", required=True)
    p.add_argument("--archive-dir", default="~/.chats_archive")
    p.set_defaults(func=import_json)
    
    # list
    p = subparsers.add_parser("list", help="List archived conversations")
    p.add_argument("--archive-dir", default="~/.chats_archive")
    p.set_defaults(func=list_conversations)
    
    # read
    p = subparsers.add_parser("read", help="Read a conversation")
    p.add_argument("id", help="Conversation ID (or prefix)")
    p.add_argument("--archive-dir", default="~/.chats_archive")
    p.set_defaults(func=read_conversation)
    
    # export-markdown
    p = subparsers.add_parser("export-markdown", help="Export all to Markdown")
    p.add_argument("--output", "-o", default="~/chats_export")
    p.add_argument("--archive-dir", default="~/.chats_archive")
    p.set_defaults(func=export_markdown)
    
    # key-export
    p = subparsers.add_parser("key-export", help="Export encryption key for backup")
    p.add_argument("--output", "-o", help="Write to file instead of stdout")
    p.set_defaults(func=key_export)
    
    # key-import
    p = subparsers.add_parser("key-import", help="Import encryption key from backup")
    p.add_argument("--file", "-f", help="Read key from file")
    p.add_argument("--key", "-k", help="Key string directly")
    p.set_defaults(func=key_import)
    
    # verify-api
    p = subparsers.add_parser("verify-api", help="Verify API endpoints")
    p.set_defaults(func=verify_api)
    
    # diagnose-api
    p = subparsers.add_parser("diagnose-api", help="Diagnose API status")
    p.set_defaults(func=diagnose_api)
    

    # verify-archive (operator)
    p = subparsers.add_parser("verify-archive", help="Verify archive integrity (operator)")
    p.add_argument("--archive-dir", default="~/.chats_archive")
    p.set_defaults(func=verify_archive_cmd)

    # status
    p = subparsers.add_parser("status", help="Show archive status")
    p.add_argument("--archive-dir", default="~/.chats_archive")
    p.set_defaults(func=status)
    
    args = parser.parse_args()
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
