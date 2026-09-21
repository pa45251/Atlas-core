# Atlas Core — Current Codex Task

## Task: Build a local semantic gold set for Atlas v0.2.1

Run this task on the user's Windows PC where Obsidian and the existing Atlas local configuration already work.

### Goal

Create a high-quality local labeled dataset from the user's existing vault so Atlas can learn which candidate relations are actually worth linking.

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
5. Deduplicate directional candidate pairs so each note pair is reviewed once.
6. Review **all unique related-note candidate pairs**, not only HIGH-confidence pairs.
7. Review **all duplicate candidates**.
8. Review **all root-level Unclassified/domain suggestions**.
9. Use the actual note contents locally when needed.
10. Save the detailed labeled dataset only to:
    ```text
    .local/atlas-semantic-goldset.json
    ```

### Pair labels

For every unique related-note pair assign exactly one:

- `DIRECT_LINK` — a durable explicit link between the two notes would improve navigation or understanding.
- `SAME_TOPIC` — related topic, but an explicit backlink would add little value.
- `DUPLICATE` — materially overlapping notes that should later be reconciled.
- `REJECT` — superficial or misleading similarity.

For `DIRECT_LINK`, also record locally:

- preferred direction: `A_TO_B`, `B_TO_A`, or `BIDIRECTIONAL`
- a short private reason
- confidence: `HIGH`, `MEDIUM`, or `LOW`

### Duplicate labels

For each duplicate candidate:

- `TRUE_DUPLICATE`
- `RELATED_NOT_DUPLICATE`
- `REJECT`

### Domain labels

For each root-level Unclassified note:

- choose the best existing domain when clearly supported;
- otherwise label `KEEP_UNCLASSIFIED`;
- include local confidence `HIGH`, `MEDIUM`, or `LOW`.

### Local gold-set schema

Store a machine-readable JSON object with:

```json
{
  "task": "semantic_goldset_v021",
  "pairs": [
    {
      "a": "private local note path",
      "b": "private local note path",
      "label": "DIRECT_LINK|SAME_TOPIC|DUPLICATE|REJECT",
      "direction": "A_TO_B|B_TO_A|BIDIRECTIONAL|null",
      "confidence": "HIGH|MEDIUM|LOW",
      "reason": "private local reason"
    }
  ],
  "duplicates": [],
  "domains": []
}
```

This file is private and MUST stay under `.local/`.

### Sanitized GitHub handoff

After completing the local gold set, update `docs/CODEX_RESULT.md` with only non-sensitive aggregate results:

1. number of unique pairs reviewed;
2. counts of DIRECT_LINK / SAME_TOPIC / DUPLICATE / REJECT;
3. DIRECT_LINK rate overall;
4. DIRECT_LINK rate among current HIGH-confidence candidates;
5. counts by confidence;
6. duplicate adjudication counts;
7. domain adjudication counts;
8. whether there are clear systematic false-positive patterns;
9. recommendation for the next Atlas step.

Do **not** publish note bodies, private reasons, private note paths/titles, API keys, or the gold-set JSON.

### Recommendation choices

Choose one:

- `TUNE_CANDIDATE_GENERATOR`
- `BUILD_MANUAL_APPROVAL_QUEUE`
- `BUILD_SAFE_APPLY_ENGINE`

Prefer `BUILD_MANUAL_APPROVAL_QUEUE` unless the labeled gold set shows that automatic direct-link decisions are consistently reliable.

### Safety constraints

- Vault remains read-only.
- No note creation, editing, moving, renaming, merging, or deleting.
- Never expose `.env`, API keys, local certificates, note bodies, private note titles/paths, or employer-confidential information.
- Do not commit anything under `.local/`.
- Do not change Atlas code unless a real execution bug blocks the task. If a bug is found, report it first.

## Mandatory handoff

Before finishing, follow `docs/CODEX_HANDOFF_PROTOCOL.md`.

In particular:

- write the sanitized aggregate result to `docs/CODEX_RESULT.md`;
- commit and push that result to GitHub so ChatGPT can read it directly;
- keep the detailed semantic gold set under `.local/` only;
- do not require the user to copy results manually between Codex and ChatGPT.
