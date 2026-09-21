# Atlas Core

Atlas Core is a local-first personal knowledge intelligence engine.

Its first integration is a read-only connector to an Obsidian vault through the Local REST API plugin.

## Design principles

- Obsidian is the source of truth.
- Secrets and vault contents stay local and are never committed.
- Public repository code must be safe to disclose.
- Start read-only; writing requires an explicit future opt-in.
- Prefer simple, testable components over multi-agent complexity.

## Phase 1

Connect to Obsidian at `https://127.0.0.1:27124`, list files, search existing notes, and read selected notes without modifying the vault.
