---
name: architecture-peer-review
description: >-
  After an architecture or implementation plan is drafted, perform a careful
  peer review against the real codebase. Use when cross-checking findings,
  general plan, or design docs (not execution files). For per-phase execution
  file sets, use execution-peer-review instead. Writes findings to
  plan-folder/reviews/architecture-peer-review/ — chat is summary + link only.
---

# Architecture peer review

Read-only review of **one** baseline doc set (findings + general plan, or a standalone design spec). **Not** for per-phase execution files — use **`execution-peer-review`** (P0…Pn **one file at a time**).

**Forbidden:** edit findings, general plan, or execution files; fix gaps; run `phase-execution`; create commits.

**Allowed:**
- Create or update files under `<plan-folder>/reviews/architecture-peer-review/`
- Add or update **one index row/link** in `<plan-folder>/README.md` pointing at `reviews/architecture-peer-review/README.md` (no other plan-folder README edits)

**Sibling:** `execution-peer-review` — execution file set after `create-execution-plan` (mirror layout: `reviews/execution-peer-review/`).

---

## Entry

User attaches:

- **Plan folder** (preferred), or
- **General plan** / findings / design doc path(s).

Optional user hints:

- **Re-review / pass 2+** — after a fix agent updated findings or general plan.
- **Delta only** — re-review only sections the user lists or that changed since last pass.

Discover baseline paths (first match wins per type):

| Doc | Typical locations |
|:---|:---|
| Findings | `<plan-folder>/*_FINDINGS.md` |
| General plan | `<plan-folder>/*_GENERAL_PLAN.md`, `<plan-folder>/general/*_GENERAL_PLAN.md` |
| Program index | `<plan-folder>/README.md` |
| Linked specs | paths in plan header `**Baseline:**`, `**Depends on:**`, `**Authority:**` |

Announce once in chat: plan folder, docs reviewed, pass number.

**Do not** read execution files unless the user explicitly asks to cross-check execution against general plan (that is `execution-peer-review`).

---

## Review artifact (required)

All findings go to disk — chat is a **short summary + link**, not the SSOT.

### Layout

```
<plan-folder>/
  reviews/
    architecture-peer-review/
      README.md              ← pass index (create on first pass)
      pass-01-YYYY-MM-DD.md  ← one file per full review pass
      pass-02-YYYY-MM-DD.md
```

**Plan folder examples:** `docs/review-pipeline/pr-summary-rollup/`, `docs/agents/foo/`, `docs/utils/some-program/`.

### Legacy (do not migrate unless user asks)

Older programs may have a single `<TOPIC>_PEER_REVIEW.md` at plan-folder root (e.g. `REVIEW_QUALITY_PEER_REVIEW.md`). **New reviews** use `reviews/architecture-peer-review/` only. On re-review of a legacy program, start `pass-01-…` in the new layout; link the legacy file from README as “historical”.

### Pass file naming

- First pass: `pass-01-YYYY-MM-DD.md` (today’s date).
- Each **full** re-review: **new** file, increment pass (`pass-02-…`). **Never overwrite or append to a prior pass file** — each file is an immutable snapshot.
- **Delta** re-review: always create a **new** file `pass-NN-YYYY-MM-DD-delta.md` (same `NN` as the pass being delta’d, or next unused `NN` if multiple deltas that day). Link prior pass under `## Prior pass`. Put the updated `## Verdict` / **BLOCK**, rollup, and scoped section outcomes in the **new** file only.
- **Spot** re-review: same as delta — **new** `pass-NN-YYYY-MM-DD-spot.md` (or `-delta.md` if the user called it a delta); never mutate the prior pass file.
- After any re-review: update reviews `README.md` status line **and** the pass index table columns (`Critical`, `High`, `Block next step`) to point at the **latest** file. Do not leave a stale BLOCK: yes on the index.

### `README.md` index (update every pass)

| Pass | File | Date | Scope | Critical | High | Block next step |
|------|------|------|-------|----------|------|-----------------|
| 1 | [pass-01-…](./pass-01-2026-08-08.md) | 2026-08-08 | findings + general | 0 | 2 | no |

Link to findings + general plan. Status line: `Latest pass: N — BLOCK <next-step>: yes/no` where `<next-step>` is `create-general-plan`, `create-execution-plan`, or `phase-execution` as appropriate.

If `<plan-folder>/README.md` exists, add or update a row pointing to `reviews/architecture-peer-review/README.md`.

### Pass file header (required)

```markdown
# Architecture peer review — pass N

**Plan folder:** `docs/…/`  
**Date:** YYYY-MM-DD  
**Scope:** full | delta (sections …)  
**Reviewer:** architecture-peer-review skill  
**Baseline:** [FINDINGS.md](…), [GENERAL_PLAN.md](…), codebase paths cited below  

## Verdict

Review complete: X critical, Y high, Z medium/low.  
**BLOCK <next-step>:** yes/no — one-line reason.

## Prior pass

Link to pass N-1 if re-review; note what the fix agent was asked to address.

## Verified (docs match codebase)

| Claim | Code evidence |
|:---|:---|
| … | `path:line` — short note |

## Rollup (critical / high)

| Severity | Section | Title |
|:---|:---|:---|

## Per-section findings

…

## Open questions (max 3)

…

## Pre-execution checklist

- [ ] …

**Next:** named skill or human gate.
```

### Chat response (after writing files)

1. One sentence: pass number, scope, BLOCK yes/no.
2. **Link** to the pass file (relative path from repo root).
3. Link to `reviews/architecture-peer-review/README.md`.
4. List **critical/high titles only** (no full tables in chat).
5. If BLOCK: what must be fixed before the named next step; suggest fix agent reads pass file.

---

## Re-review modes

| Mode | When | What to read | Output |
|------|------|--------------|--------|
| **Full** | First review, or user says “full re-review” | Findings + general plan (+ linked specs) | New `pass-NN-…md` |
| **Delta** | User says “re-review after fixes” | Changed sections + prior pass | New `pass-NN-…-delta.md` (never append to prior) |
| **Spot** | User names one general-plan phase | That `## Pn` block only | New `pass-NN-…-spot.md` (never append to prior) |

**Delta / spot rules:**

- Re-read prior pass findings for scoped sections; mark each **resolved / open / new** in the **new** file.
- Do not re-copy unchanged clean sections verbatim — one line `**Pn — no new gaps** (verified unchanged).`
- If a “fixed” item is still broken, escalate severity.
- Put fresh `## Verdict` / **BLOCK** and `## Rollup (critical / high)` in the new file; update reviews `README.md` status line and pass index table to the latest file. Leave prior pass files untouched.

**Iteration loop (typical):**

```
create-findings → create-general-plan → architecture-peer-review (pass 1)
  → fix agent (edits findings / general plan per pass-01)
  → architecture-peer-review (pass 2, delta or full)
  → … until BLOCK: no → create-execution-plan → execution-peer-review
```

---

## Review workflow

1. Read findings (locked decisions, decisions registry, grep claims).
2. Read general plan phase blocks (`## P0`, `## P1`, …) in order — or spec sections if no general plan yet.
3. For **each phase block**, grep/read **repo paths cited** (models, services, APIs, migrations, tests, frontend if in scope).
4. Cross-check against:
   - Findings locked table / decisions registry (do not re-open locked items; flag if plan contradicts)
   - Depends-on programs and **merged** prerequisite PRs/branches when cited
   - Precedent waves or shipped slices named in the plan
5. **Write findings to the pass file** (per-section template below).
6. Finish verdict + rollup; update `reviews/architecture-peer-review/README.md`.

Mark **verified** (with path) vs **assumption** if not read.

**Questions:** only if blocking — `## Open questions` in pass file (max 3).

---

## Per-section output template

Use general-plan phase ids (`P0`, `P1`, …) or spec section headings. Findings-only review: use findings major sections instead of `Pn`.

```markdown
## Pn — (phase title from general plan)

| Severity | Area | Finding |
|:---|:---|:---|
| critical | codebase | … |
| high | general plan | … |
| medium | findings | … |
| low | clarity | … |

**Verified OK:** (1–3 bullets)
```

**Severity:** critical = wrong behavior / rework if implemented; high = contradicts findings or locked decision; medium = missing gate, vague deliverable, dependency not on main; low = wording, stale line ref.

**Cross-cutting section** (once per pass, after per-phase sections): locked-decision parity across findings ↔ general plan, prerequisite merge status, migration policy, test/dogfood gates, i18n/theme rules if FE in scope.

---

## General-plan contract checklist

Flag missing or broken items (adapt to stack — backend/FE/ops):

| Check | |
|:---|:---|
| Header links findings + program README / authority docs | |
| Locked decisions in general plan match findings registry | |
| Each phase: **Goal**, **Scope** (in/out), **Deliverables**, **Depends on** | |
| Prerequisites cited as merged on target branch are actually merged | |
| New persistence: migration subphase implied; handwritten Alembic only (no `--autogenerate`) | |
| APIs/services/models named in plan exist or are explicitly **new** | |
| Test paths in deliverables exist or named as **new** in a subphase | |
| Human/ops gates (staging sign-off, deploy) in correct phase — not mixed with code-only phases | |
| No TBD / no open options in decisions table | |
| **Next step** at end of general plan matches findings (execution-plan vs general-plan) | |

Add domain-specific rows in the pass file when the program needs them (e.g. `active_program` / review-context, consumer grep before delete, calculator dispatch maps) — do not bake one product’s checklist into this skill.

---

## Codebase verification

- Paths in plan **Files** / citations exist (or correctly named new files).
- Migrations: revision chain plausible.
- Import consumers and call sites match “what exists vs new” tables in findings.
- Stale line numbers, renamed symbols, wrong module paths.
- Stale docs referencing old paths (flag for doc-sync phase; usually not blocking architecture review).

---

## Anti-patterns

- Dump full per-section tables in chat instead of the pass file.
- Skim general plan without grep on cited repo paths.
- Edit findings or general plan to fix findings (report only).
- Overwrite prior pass files.
- Review execution files in bulk (`execution-peer-review`).
- Calculator-/monolith-only checklist baked into every project.

**Invoke with:** plan folder + findings/general paths + “architecture peer review” / “re-review pass 2 after fixes”.
