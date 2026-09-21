# Atlas Core security boundary

Atlas Core is public during its early development phase. Treat every committed byte, issue, pull request, workflow log, and test fixture as public information.

## Never commit

- Obsidian API keys or other credentials
- `.env` files containing real values
- the Obsidian vault or exported personal notes
- employer-confidential material
- internal process recipes, wafer data, process windows, defect data, or internal slides
- proprietary or licensed documents that cannot be redistributed

## Local Obsidian boundary

Version 0.1 is deliberately read-only:

- allowed: server status, list vault directories, search, read an existing note
- not implemented: PUT, PATCH, DELETE, note creation, command execution
- connector accepts only HTTPS loopback endpoints
- HTTP is rejected
- the API key is loaded locally and is never printed
- the local CA certificate is stored under `.local/`, which is gitignored

The `bootstrap-ca` command makes one certificate-unverified request only to a validated HTTPS loopback host and only to the plugin's fixed CA-certificate endpoint. All normal requests use certificate verification.

## Knowledge policy

Obsidian is the source of truth. Atlas may later propose organization, links, summaries, and derived notes, but source captures should remain recoverable and AI-generated interpretation must be distinguishable from user-authored material.
