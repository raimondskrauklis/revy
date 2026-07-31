---
name: bootstrap-workflow
description: >-
  Install or upgrade agent-workflow-pack in a target repo: audit skills catalog,
  adapt manifest, materialize .agent/, .cursor/, docs/agents/, backend scripts.
  Use when user asks to bootstrap agent workflow, install workflow pack, audit
  skills, or port workflow to another project.
---

# Bootstrap workflow pack

**When:** user points at a target repo and asks to install/port/upgrade the agent workflow pack or audit skills.

**Pack location:** `internal-docs/agent-workflow-pack/` (or user-provided path).

**Rule:** Nothing runs from the pack directory. **Materialize** into the target repo.

**Catalog:** `skills.catalog.json` — full inventory. **Audit:** `patterns/skills-audit.md`.

---

## 1. Discover target repo

1. Confirm target repo root.
2. Scan: `AGENTS.md`, `.cursor/skills/`, `.cursor/mcp.json`, `.agent/`, `.revy/`, `docs/`, `backend/`.
3. Read pack `skills.catalog.json`, `project.manifest.template.json`, `patterns/review-context.schema.json`.

---

## 2. Write `.agent/manifest.json`

Adapt template — set `integrations.greptile: false` unless user explicitly asks.

Write `.agent/flows/*.json` from pack templates.

---

## 3. Skill audit (required)

Follow `patterns/skills-audit.md`.

1. Load pack `skills.catalog.json`.
2. For each skill, decide: **install** | **upgrade** | **keep** | **skip** | **remove**.
3. Print compact table for user before copying files.

**Default install (most repos):** `bootstrap-workflow`, `phase-execution`, `ship-changes`, `chunk-execution`.

**Planning tier** — install when `docs/` has program artifacts (`*EXECUTION*`, `*_FINDINGS*`, `*_GENERAL_PLAN*`) or user does phased work:
`create-findings`, `create-general-plan`, `create-execution-plan`, `architecture-peer-review`, `execution-peer-review`, `devils-advocate`, `post-finish-gap-pass`.

**Optional:**
- `babysit-pr` — only if `integrations.greptile: true`; **remove** if greptile off and skill present
- `sentry-fix-issues` — only if Sentry MCP in `.cursor/mcp.json`
- `md-formatting`, `md-docx-export`, `docx-md-export` — docs export handoff repos or user asks

4. Copy selected skills from `templates/.cursor/skills/<id>/` → target `.cursor/skills/<id>/`.
   - Skills with `copy_scripts: true` — copy full folder (scripts, assets).
   - **Upgrade:** overwrite when pack template is authoritative (core workflow skills).
5. Copy catalog → `.agent/skills.catalog.json`; set `manifest.json` → `skills.installed` to installed ids.
6. If `integrations.revy` or `*_STAGING_VALIDATION.md` found — install `staging-validation`; set `manifest.validation` from overlay (`overlays/revy/staging-validation.md`) or generic template.

---

## 4. Review context SSOT

Create `.agent/review-context.json`. Mirror to `.revy/` when `integrations.revy: true`.

---

## 5. `.cursor/BUGBOT.md`

From `patterns/BUGBOT.md.template` — paths relative to `.cursor/`.

---

## 6. `docs/agents/`

Copy from `templates/docs/agents/` + optional `templates/docs/utils/CURSOR_AGENT_WORKFLOW.md`.

---

## 7. Merge `AGENTS.md`

Merge `templates/AGENTS.workflow.snippet.md` — list **installed** skills only (from audit), grouped by tier. Point to `.agent/skills.catalog.json`.

---

## 8. Greptile backend (only if `integrations.greptile: true`)

Implement from `patterns/backend/` in target `backend/`. Do not implement otherwise.

---

## 9. Verify

```text
[ ] .agent/manifest.json + skills.catalog.json
[ ] Skill audit table executed; skills.installed matches .cursor/skills/
[ ] .agent/review-context.json valid
[ ] .cursor/BUGBOT.md links resolve
[ ] AGENTS.md skills table matches installed set
[ ] If greptile: generator --check passes
```

Report: audit table, files created, integrations, gaps.

---

## Upgrade / re-audit only

User says "audit skills" or "upgrade workflow pack" without full bootstrap:

1. Run **skill audit** only — compare installed vs catalog + repo signals.
2. Upgrade outdated core skills; add missing; remove `babysit-pr` if greptile disabled.
3. Bump `.agent/skills.catalog.json` `pack_version`.

---

## Upgrade existing Revy repo

See `overlays/revy/README.md`. Add `.agent/` layer; do not delete `docs/review-pipeline/agents/`.

---

## Not in scope

- SaaS scaffold (`starter-pack`)
- CI/CD unless user asks
- Greptile vendor account setup
