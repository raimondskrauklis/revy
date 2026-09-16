# docs/agents/findings/REVY_PRODUCT_RULE_PACKS_HANDOFF.md

# Revy product — rule packs + review unit (handoff)

Attach this in the Revy repo. Consumer already ships the files; Revy needs to **load and prompt** them. Living note — extend when the product side lands.

**From:** kp-platform (consumer) · **Date:** 2026-08-14

---

## What is already true (do not re-teach in pack markdown)

Revy is a **reviewer**. It posts findings (inline comments / check). It does not rewrite the PR. Pack files must not say “do not rewrite” — that is the product, not a house rule.

The valuable behaviour to **keep and prompt**: the review unit is **every file the diff touches**, full contents, not the hunk. Unchanged lines in those files are in scope. That is how pre-existing house-rule bugs get caught when a coding agent only edits one function.

Do not comment on taste or a ~150-line “soft limit”. That is LOOP triage after comments land, not a Revy finding.

---

## Do not ingest

- `.cursorrules`, `AGENTS.md`, Cursor skills, LOOP / Bugbot docs
- Unscoped encyclopedias (`PLATFORM_CONTEXT.md`, full color-token guide) unless a later `files.json`-style pointer is scoped to matching paths

Those mix agent-chat rules (“don’t write md”, file headers on generate) with coding standards. False positives on legacy files.

Greptile shape: explicit packs + optional **path-scoped** file pointers. Not CodeRabbit auto-slurp of editor rule files.

---

## Load contract (consumer already writes this)

`.revy/review-context.json`:

```json
{
  "active_program": null,
  "programs": [],
  "rule_packs_catalog": {
    "platform": ".revy/rules/platform.md",
    "backend": ".revy/rules/backend.md",
    "frontend": ".revy/rules/frontend.md"
  }
}
```

Active program (example):

```json
{
  "id": "example",
  "scope": ["backend/**"],
  "rule_packs": ["platform", "backend"],
  "paths": [
    { "path": ".revy/rules/platform.md", "description": "rules" },
    { "path": ".revy/rules/backend.md", "description": "rules" }
  ]
}
```

| When | Load |
|:---|:---|
| `programs[].rule_packs` set | Those ids via `rule_packs_catalog` |
| Pack files also on `paths[]` (`description: "rules"`) | Load them (today’s path ingest — keep working) |
| `active_program` null (ad-hoc PR) | Derive from **files in the review set**: `backend/**` → platform+backend; `frontend/**` → platform+frontend; both → all three; neither → none |
| `rule_packs: []` (docs/corpus) | No packs. Do not apply backend/frontend rules to markdown. |

Per **file** in the review set, only apply packs that match that file’s tree. A backend-only file in a full-stack PR must not get QuietChip / `--tp-*` comments.

---

## Prompt deltas (short)

1. Review **full file text** for each path in the diff. Packs apply to unchanged lines too.
2. Output is findings (location, what’s wrong, which pack). Not a patch, not a rewritten PR.
3. Inject only the resolved pack markdown for this PR/file — not `.cursorrules`.
4. Skip: file length, “soft limit”, generate-file headers, LOOP/process.
5. Prefer one comment per distinct violation. Do not restyle-nits.

---

## Why the consumer split exists

Coding agents implement the phase. They will not re-scan the rest of a touched file for house style. Revy already does, cheaply, because it comments rather than edits. Product work is: **wire packs into that pass**, scoped, without teaching the model to “not rewrite.”

---

## Verify

- Backend-only PR: no frontend-pack comments.
- Hunk-local change; pack violation on another line in the same file: comment on that line.
- `rule_packs: []`: no SQLAlchemy/QuietChip comments on docs.
- Pack markdown does not contain “do not rewrite the PR.”
