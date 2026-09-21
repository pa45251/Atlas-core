# Atlas Core — Current Codex Task

## Task: Semantic adjudication of Shadow Mode v0.2.1

Run this task on the user's Windows PC where Obsidian and the existing Atlas local configuration already work.

### Goal

Measure whether Atlas v0.2.1 is precise enough to move toward Safe Auto linking.

Do **not** modify the Obsidian vault.

### Inputs

- Repository: `pa45251/Atlas-core`
- Branch: `main`
- Local report: `.local/atlas-shadow-report.json`
- Obsidian access: existing read-only Local REST API connection

### Procedure

1. Update local `Atlas-core` to the latest `main`.
2. Reinstall the editable package if needed.
3. Run:
   ```powershell
   atlas organize --shadow
   ```
4. Read the local shadow report.
5. Review **all HIGH-confidence related-note pairs** from the report.
6. Review **all duplicate candidates**.
7. Review **all root-level domain suggestions**.
8. For each reviewed item, use the actual note contents locally when needed, but do not copy note bodies into GitHub, commits, logs, or any public artifact.

### Relationship labels

For each HIGH-confidence related pair, assign exactly one:

- `DIRECT_LINK` — the two notes express concepts that should explicitly link to each other.
- `SAME_TOPIC` — related topic, but a direct backlink would add little value.
- `DUPLICATE` — materially overlapping notes that may later deserve merge/reconciliation.
- `REJECT` — similarity is superficial or misleading.

For each duplicate candidate, assign:

- `TRUE_DUPLICATE`
- `RELATED_NOT_DUPLICATE`
- `REJECT`

For each root-level domain suggestion, assign:

- `ACCEPT_DOMAIN`
- `REVIEW_DOMAIN`
- `REJECT_DOMAIN`

### Output

Return a concise Traditional Chinese report containing:

1. HIGH-confidence pair count.
2. Count by relationship label.
3. Precision estimate:
   - strict precision = DIRECT_LINK / reviewed HIGH pairs
   - useful relation precision = (DIRECT_LINK + SAME_TOPIC + DUPLICATE) / reviewed HIGH pairs
4. The 5 strongest DIRECT_LINK examples, with note titles/paths only and a short reason.
5. Any HIGH-confidence false positives and why they failed.
6. Duplicate-candidate adjudication.
7. Root-level domain suggestion adjudication.
8. Recommendation:
   - `NOT_READY`
   - `READY_FOR_MANUAL_APPROVAL_MODE`
   - `READY_FOR_SAFE_AUTO_LINKS`

### Decision rule

Do **not** recommend Safe Auto solely from similarity scores.

Recommend `READY_FOR_SAFE_AUTO_LINKS` only if:

- at least 80% of reviewed HIGH pairs are `DIRECT_LINK`, and
- there are no systematic false-positive patterns, and
- no privacy/security boundary is violated.

Otherwise recommend `READY_FOR_MANUAL_APPROVAL_MODE` or `NOT_READY`.

### Safety constraints

- Vault must remain read-only.
- No note creation, editing, moving, renaming, merging, or deleting.
- Never expose `.env`, API keys, local certificates, or note bodies.
- Do not commit `.local/` reports.
- Do not push private note content to GitHub.
- Do not change Atlas code unless a real execution bug blocks the task. If a bug is found, report it first.
