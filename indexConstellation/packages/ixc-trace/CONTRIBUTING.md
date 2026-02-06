# Contributing

This project is open source because when the API breaks, community patches arrive faster than fixes.

---

## Principles

1. **Truth over completion** – Document limitations honestly
2. **Sovereignty over automation** – No silent updates, no forced upgrades
3. **Constraint over cleverness** – Simple solutions over complex ones
4. **Repair over pretend** – Fix breaks, don't hide them

---

## How to Help

### Report a Break
1. Run `chats-archive diagnose-api`
2. Open an Issue with the diagnostic token
3. Note what you were trying to do

### Submit a Fix
1. Fork the repository
2. Create a branch: `fix/break-{token}`
3. Add test if possible
4. Update `BREAKLOG.md` with the break and fix
5. Submit a Pull Request

---

## Code Style

- Type hints for public functions
- Docstrings for modules, classes, public methods
- f-strings for formatting
- Explicit errors – don't swallow exceptions

---

## Security

- Never log tokens or conversation content
- Use 0600 permissions for sensitive files
- Prefer OS-managed secrets over local files
