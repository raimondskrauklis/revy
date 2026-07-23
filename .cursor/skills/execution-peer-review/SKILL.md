---
name: execution-peer-review
description: >-
  Peer-review execution plan files one phase at a time (P0, P1, …) against the
  codebase, findings, and general plan. Reports gaps after each file; no edits.
  Use when the user asks to review execution plans, cross-check P0–P8 execution
  files, or validate a plan folder before phase-execution.
---

# Execution peer review

Read-only review of **per-phase execution files** before `phase-execution`. **Not** a bulk skim — review **one file, report, then next file**.

**Sibling:** `architecture-peer-review` — single plan/spec doc. Use that for findings or general plan only; use **this skill** for the execution file set.

**Forbidden:** edit any file; fix gaps; run `phase-execution`; create commits.

---

## Entry

User attaches:

- **Plan folder** (preferred), or
- **`README.md`** with execution table, or
- A single execution file (review that file only).

Discover the ordered file list from **`README.md` execution table** (same as `phase-execution`). If no README, glob `*EXECUTION*.md` in folder and sort by phase id.

Announce once: plan folder, phase count, file list, LOOP order.

**Optional baseline read (once, before P0):** `*_FINDINGS.md`, `*_GENERAL_PLAN.md` — for locked decisions and phase goals. Do **not** read all execution files upfront.

---

## One file at a time (strict)

For **each** execution file in order:

1. **Read only this execution file** (+ grep/read **repo paths cited in this file** — models, services, APIs, migrations, frontend paths).
2. Cross-check **this phase** against:
   - Matching **general plan** `## Pn` block (goal, scope, deliverables, depends)
   - **Findings** locked decisions (no re-opening; flag if execution contradicts)
   - **`create-execution-plan` contract** (checklist below)
   - **Prior phases** only via what *this file* claims (depends, out of scope, imports) — if a cross-phase contradiction is suspected, note it; do not re-read prior execution files unless one line needed to confirm
3. **Print findings for this file immediately** (template below).
4. **Then** open the next execution file. Never defer per-file findings to a final mega-summary.

If a file is clean: say `**Pn — no gaps found.**` (still one line on what was verified).

---

## Per-file output template

```markdown
## Pn — `<relative/path/to/FILE.md>`

| Severity | Area | Finding |
|:---|:---|:---|
| critical | codebase | … |
| high | general plan | … |
| medium | execution contract | … |
| low | clarity | … |

**Verified OK:** (1–3 bullets — phase gate present, subphase count, key paths exist)
```

**Severity:** critical = wrong behavior / rework if implemented; high = contradicts findings or general plan; medium = missing gate, vague deliverable, scope leak; low = wording, optional clarity.

**Questions:** only if blocking ambiguity — max 1–2 per file.

---

## Execution contract checklist (per file)

Flag missing or broken items:

| Check | |
|:---|:---|
| Header links general plan + findings | |
| **Goal** + **decisions locked** for this phase | |
| **Out of scope** lists later phases | |
| **3–6 subphases** (flag if >8) | |
| Each subphase: `**What**` / `**Files**` / `**Deliverable**` | |
| **Deliverable** includes verify command or concrete assertion | |
| **Phase gate** — copy-paste `pytest` / `npm test` block | |
| **Migration** subphase flagged + handwritten-only note if Alembic | |
| **Human gate** if spike/ops/sign-off (P1-style) | |
| **Next** → following execution file | |
| No TBD / no open options / no “choose A or B” | |
| FE phase has frontend gate when `frontend/` touched | |
| **Final phase** | Doc-sync per `create-execution-plan`; optional `post-finish-gap-pass` |

---

## Codebase verification (per file)

Same bar as `architecture-peer-review` — **evidence in repo**:

- Paths in **Files** exist (or are correctly named new files).
- Migrations: revision chain plausible; no `--autogenerate` assumed.
- APIs, services, models, hooks, components referenced match real names.
- Test paths in **Deliverable** / phase gate exist or are named as **new** in subphase.
- Flag stale line numbers, renamed symbols, wrong module paths.

Mark findings **verified** (with path) vs **assumption** if not read.

---

## After last file

Short rollup only — counts by severity, list **critical/high** across all phases (no re-explaining every medium). Suggest whether safe for `phase-execution` or must fix first.

```
Review complete: N files, X critical, Y high, Z medium/low.
BLOCK phase-execution: yes/no — reason.
```

---

## Anti-patterns (do not do)

- Read all `*_EXECUTION.md` files, then one combined gap list.
- Skip a phase because “similar to P2”.
- Edit execution files to fix findings.
- Generic brainstorming unrelated to this phase’s **Files**.

**Invoke with:** attach plan folder or README + “execution peer review” / “review all execution files P0–P8”.
