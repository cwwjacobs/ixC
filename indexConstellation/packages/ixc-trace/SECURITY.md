# Security Policy

## Supported versions
Only the most recent release/tag is supported for security fixes.

## Reporting a vulnerability
Report privately. Include version, OS, steps, and sanitized logs (no tokens, no keys, no conversation content).

## Security issues
- Token/key exposure via logs or unsafe defaults
- Unencrypted content at rest
- Integrity failures (corruption not detected on read)
- Unsafe file permissions for secrets
- Code execution vulnerabilities

## Not security issues
- API endpoint drift/breakage (undocumented endpoints by design)
- Rate limiting or transient availability errors
