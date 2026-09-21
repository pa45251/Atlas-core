# Codex ↔ ChatGPT GitHub Handoff Protocol

This file defines how local Codex tasks report results back to the Atlas Core repository so the user does not need to act as a messenger between Codex and ChatGPT.

## Mandatory result publishing

For every future Atlas task that Codex executes locally:

1. Perform the requested local work.
2. Keep private Obsidian data local.
3. Write the detailed private report, if needed, only under `.local/`.
4. Write a **sanitized result summary** to:
   ```text
   docs/CODEX_RESULT.md
   ```
5. Commit and push only that sanitized summary to GitHub.
6. Do not wait for the user to manually copy the result back into ChatGPT.

The latest `docs/CODEX_RESULT.md` is the canonical handoff that ChatGPT can inspect through the connected GitHub integration.

## What may be published

Safe examples:

- task name
- Atlas commit SHA
- PASS / FAIL
- aggregate counts and metrics
- precision / recall style measurements
- anonymized relationship labels
- bug description that does not expose private content
- tests run and their result
- recommendation / next action
- whether the vault was modified
- whether private-data leakage occurred

## What must never be published

Never commit or push:

- Obsidian note bodies
- excerpts from private notes
- API keys or `.env`
- local certificates
- the Obsidian vault
- private attachments
- personal secrets
- employer-confidential information
- internal process recipes, wafer data, process windows, defect data, or internal slides
- local absolute paths that reveal unnecessary personal information

If note-level examples are necessary, prefer anonymized identifiers such as `note_01`, `note_02`. A note title/path may only be included when the task explicitly permits it and it is safe to make public.

## Required result format

`docs/CODEX_RESULT.md` should use this compact structure:

```markdown
# Codex Result

Task: <task name>
Atlas commit: <sha>
Completed: <timestamp>

## Outcome
PASS / PARTIAL / FAIL

## Metrics
- ...

## Findings
- ...

## Recommendation
...

## Safety
- Vault modified: NO
- Private note content pushed to GitHub: NO
- API key exposed: NO
- .env committed: NO
```

## Public repository rule

Atlas Core is currently public. Treat every committed result as public information.

If a useful result cannot be safely summarized without exposing private data, Codex must keep the detailed result under `.local/` and publish only:

- that the task completed,
- aggregate non-sensitive metrics,
- a safe recommendation,
- and a statement that detailed evidence remains local.

## Code changes

If Codex discovers a real code bug:

- it may fix it only when the current task explicitly allows code changes;
- it must report the bug and validation result in `docs/CODEX_RESULT.md`;
- private evidence used to diagnose the bug must remain local.
