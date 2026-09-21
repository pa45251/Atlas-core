# Atlas Core

Atlas Core is a local-first personal knowledge intelligence engine.

Obsidian is the source of truth. Atlas is the processing layer that will eventually organize, connect, retrieve, and reason over your knowledge without turning the vault into a cloud dependency.

## Design principles

- Obsidian remains the canonical knowledge store.
- Secrets and vault contents stay on the local computer and are never committed.
- Public repository code must be safe to disclose.
- Version 0.1 is read-only. Writing requires a later explicit opt-in.
- Prefer simple, testable components over multi-agent complexity.

## Phase 1: read-only Obsidian connector

Atlas v0.1 supports only four operations:

- check whether Local REST API is running
- list vault folders/files
- search existing notes
- read an existing note

It does not implement note creation, PUT, PATCH, DELETE, or Obsidian command execution.

## Windows setup

Prerequisites: Obsidian is open and the `Local REST API with MCP` community plugin is enabled on `https://127.0.0.1:27124`.

```powershell
git clone https://github.com/pa45251/Atlas-core.git
cd Atlas-core
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item .env.example .env
```

Open `.env` locally and paste your Obsidian API key after `OBSIDIAN_API_KEY=`. Never paste the key into GitHub, an issue, a pull request, or chat.

Then bootstrap trust for the plugin's local certificate:

```powershell
atlas obsidian bootstrap-ca
```

Normal Atlas requests use certificate verification after that bootstrap step.

## Read-only validation using your existing notes

```powershell
atlas obsidian status
atlas obsidian list
atlas obsidian search "英文"
```

Take a path returned by `list` or `search`, then read it:

```powershell
atlas obsidian read "英文/你的既有筆記.md"
```

You do not need to create a test note. Use any existing note that you are comfortable reading locally.

## Security

See `docs/SECURITY.md`. The repository may be public during early development, but the vault, API key, local certificate, personal notes, and any employer-confidential material must remain outside Git.
