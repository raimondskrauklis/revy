---
name: create-execution-plan
description: >-
  Write all per-phase execution plan files from a GENERAL_PLAN in one pass (or
  one phase when updating): README execution table, 3–6 subphases each, phase
  gates. Sized for phase-execution LOOP. Use when creating execution docs from
  findings + general plan.
---

# Create Execution Plan

**Input:** baseline-ready findings + `*_GENERAL_PLAN.md` in a plan folder.

**Default output (full pass):** **every** execution file for **every** general-plan phase (P0…Pn or C0…Cn) + **`README.md` execution table** — all in **one session**, **no code**. This is the usual workflow after `create-general-plan`.

**Optional:** user says “P0 only” / “update P3 execution” → single file.

**Not:** one monolithic file for all phases (legacy `FRAMEWORK_CALLOFF_EXECUTION_PLAN.md`).

**Next step after full pass:** **`execution-peer-review`** → then user attaches plan folder + `phase-execution`.

---

## Process

### Full pass (default)

1. Read `.cursorrules` (§2 migrations, §4 tests).
2. Read findings + general plan; list every `## P0` / `## C0` … phase block.
3. **README first:** add or update execution table with **all phases**, linear LOOP order, wave column if helpful.
4. **For each phase in order:** write `<TOPIC>_P0_EXECUTION.md` … (one file per phase).
5. **Peer review:** run **`execution-peer-review`** on the full set (one file at a time) before baseline-ready; fix findings, then re-review changed files only.
6. Each file: 3–6 subphases, phase gate, locked decisions, out of scope, **Next** link. All decisions locked — no options, no TBDs. Unit tests only (`tests/unit/`).
7. If general plan names a scope authority, link it in README + headers as `**Authority:**` (domain doc — not hardcoded in this skill).
8. **Exit criteria** — list remaining gaps explicitly; do not defer mandatory GA items as “optional follow-up”.

Do **not** stop after P0 unless the user asked for a single phase.

### Single phase (override)

User names one phase → write or update that execution file only; still update README row.

### LOOP order vs parallel general plan

General plan may allow parallel work (e.g. P1 ∥ P3 ∥ P4 after P0). **README execution table defines one linear order** for `phase-execution` commits. Typical pattern after parallel fork:

`P0 → P1 → P3 → P4 → P2 → P5 → P6 → P7 → P8`

Document depends-on in each file; order respects hard gates (e.g. P2 after P1 PASS).

---

## How big should a phase be?

**Target:** one phase = one focused agent session = one git commit in the LOOP.

| Dimension | Guideline |
|:---|:---|
| **Subphases** | **3–6** (sweet spot). **Max 8.** More → split into two general-plan phases or two execution files (e.g. C2a/C2b) and update README. |
| **Backend touch** | ~5–20 files typical; one coherent vertical slice (policy, API, scan path, UI drill). |
| **Subphase size** | One subphase = one wiring site, one migration, one UI surface, or one test bundle — **one paragraph** max. |
| **FE + BE** | Allowed in **one phase** when general plan says so — split subphases: API/read path → types → components → i18n/MSW (see `CPV2_MARKETS_C3_EXECUTION.md`). |

### Split into a new phase when

- General-plan phase would exceed **6 subphases** or **~150 lines** of execution detail.
- **Migration + wide refactor** in one breath — prefer migration subphase early or alone; `phase-execution` **pauses the LOOP** after a handwritten Alembic revision.
- **Ops / prod / human sign-off** (rescan, probe on prod, econometrics Q6) — own phase or explicit **Human gate** (LOOP stops; code may still ship).
- **Doc-only** closeout (validation memo, deploy note) — own phase (e.g. C4) or final subphase with human gate, not mixed with heavy code.
- **Legacy monolith** (P1–P4 in one file) — split into `P1_EXECUTION.md` … when touching again.

### Keep in one phase when

- Same deploy unit (ship C0 with C1 — note in **Deploy** line, still **two commits** in LOOP).
- Test-only parity phase (C2) — all subphases extend prior phase tests.
- Shared constant/policy flip with wired sites (C0) — many files, few subphases.

---

## Plan folder layout (required for phase-execution)

```
docs/<area>/<topic>/
  README.md                    ← execution table + status
  <TOPIC>_FINDINGS.md
  <TOPIC>_GENERAL_PLAN.md
  <TOPIC>_C0_EXECUTION.md      ← one per phase
  <TOPIC>_C1_EXECUTION.md
  ...
```

**README.md** must include:

| Phase | File | Status |
|:---|:---|:---|
| C0 — short label | link | pending / Done (sha) |

Optional: closeout docs, deploy notes, artifact paths (see `cpv2_markets/README.md`).

**Filename patterns:** `<TOPIC>_C0_EXECUTION.md`, `P7_signal_lifecycle_execution_plan.md`, `GRAPH_*_P3_EXECUTION.md` — phase id parseable from name or first heading.

---

## Execution file template

```markdown
# docs/.../<TOPIC>_C0_EXECUTION.md

# C0 — <short title> (execution)

Phase **C0** of [`<GENERAL_PLAN>.md`](./...). Baseline: [`<FINDINGS>.md`](./...) §…. **C0 only.**

**Goal:** one line.

## Decisions locked for C0
- bullet decisions — no options downstream

## PR review context (optional — required when code + docs ship in one PR)
- **Greptile:** `.greptile/files.json` — execution + findings; `scope: ["backend/**"]` (adjust per program)
- **Bugbot:** `.cursor/BUGBOT.md` — links to same docs
- Ship in **first phase commit**; per-phase commits touch README status only (not full findings tree)

## Out of scope for C0 (later phases)
- item → **C1** / **C3**

---

## C0.1 — <title>

**What:** …

**Files:** `backend/...` (paths only)

**Deliverable:** assertion + **exact test command** (e.g. `pipenv run pytest tests/unit/...`)

## C0.2 — …

---

**Phase gate** (from `backend/`):

\`\`\`bash
pipenv run pytest tests/unit/...
\`\`\`

**Phase gate** (from `frontend/`) — when FE touched:

\`\`\`bash
npm test -- ComponentA ComponentB
\`\`\`

**Human gate:** (optional) — validation memo signed; prod rescan run. LOOP stops here even if tests pass.

**Deploy:** coupling note (e.g. ship with C1 before prod).

**Next:** [`<TOPIC>_C1_EXECUTION.md`](./...) — or **none** on final phase (must include doc sync — see below).
```

### Required sections

| Section | Purpose |
|:---|:---|
| Goal + locked decisions | No re-deciding in LOOP |
| **Out of scope** | Hard boundary for agent |
| Subphases `N.1`… | `**What**` / `**Files**` / `**Deliverable**` |
| **Phase gate** | Copy-paste commands; agent runs before Bugbot/commit |
| **Next** | Chain to following execution file — **none** on final phase |

### Subphase rules

- Use **`Deliverable`** (not `Verify`) — must name **how to verify** (pytest path, npm test pattern, or explicit assertion).
- After each subphase in LOOP, agent runs that deliverable’s tests.
- **Migration subphase:** name revision file; `hand-written only`; note LOOP pause after this subphase.
- **No** scope tables, estimates, timelines, or open questions.

### Phase gate rules

- **Always** include at least one runnable gate block.
- Backend: `cd backend && pipenv run pytest …` (enumerate files from subphases).
- Frontend: `cd frontend && npm test -- …` when phase touches `frontend/`.
- **Manual QA** / staging checks → label **non-gate** (do not block commit).
- If phase is backend-only, do not require frontend gate.

---

## Align with general plan

| General plan | Execution |
|:---|:---|
| One `## C0` block | One `*_C0_EXECUTION.md` |
| Phase goal / scope / depends | Header + out of scope |
| Deliverables (outcomes) | Subphase deliverables (verifiable) |

If general-plan phase is too large for sizing rules, **split the general plan first** (`create-general-plan`) — do not write a 12-subphase execution file.

---

## Doc sync (final phase only)

**Before doc-sync:** optional **`post-finish-gap-pass`** skill.

Last phase **Pn** must include **one doc-sync subphase** (or companion `*_Pn_6_EXECUTION.md` if Pn is full — same commit).

1. **README** — status Done + sha.
2. **Affected docs** — grep siblings; deliverable: `| Doc | Change |` table (copy shape from [`STRUCTURAL_OUTLIER_INDICATOR_P6_6_EXECUTION.md`](../../docs/ML/structural_outlier_indicator/STRUCTURAL_OUTLIER_INDICATOR_P6_6_EXECUTION.md)).
3. **Changelog** (user-facing only) — `frontend/src/data/changelog.json`: `**Bold name**`, what investigators see, advisory disclaimers; `python -m json.tool frontend/src/data/changelog.json > /dev/null`.

P0…Pn-1: README status row only when that phase ships.

---

## Anti-patterns (seen in repo)

| Pattern | Problem | Fix |
|:---|:---|:---|
| `FRAMEWORK_CALLOFF_EXECUTION_PLAN.md` — P1–P4 in one file | LOOP cannot commit per phase | Split per phase + README |
| `P0_foundations_execution_plan.md` — no **Phase gate** block | Agent derives gate; inconsistent | Add pytest block at end |
| `P7_…` — no phase gate | Same | Add gate covering P7.1–P7.3 tests |
| `market_ux_refine/` — no README | `phase-execution` cannot discover order | Add README table UX0–UX5 |
| Subphase uses **Verify:** only | Inconsistent | Rename to **Deliverable:** + command |
| Migration hidden inside big subphase | LOOP pause surprise | Dedicated migration subphase + callout |

**Good references:** `docs/investigation/market_indicators/cpv2_markets/` (gates); `docs/ML/structural_outlier_indicator/STRUCTURAL_OUTLIER_INDICATOR_P6_6_EXECUTION.md` (doc-sync table).

---

## Checklist before baseline-ready

```
- [ ] README.md execution table matches general plan phases
- [ ] One execution file per phase; 3–6 subphases each
- [ ] Each subphase: What / Files / Deliverable (with test command)
- [ ] Out of scope + locked decisions
- [ ] Phase gate block(s) — backend and/or frontend
- [ ] Migration subphases flagged for LOOP pause
- [ ] Human gate marked where ops/sign-off required
- [ ] **Code + docs in one PR:** first phase includes PR review context (`.greptile/files.json`, `.cursor/BUGBOT.md`) — see `phase-execution` skill
- [ ] **Final phase:** doc-sync subphase (+ `changelog.json` if user-facing); optional `post-finish-gap-pass`
- [ ] **`execution-peer-review`** on all files (one-by-one report) — no critical/high open
```

**Invoke with:**

- **Full pass (default):** “Create execution plans from general plan” + `@…/GRAPH_ML_CARTEL_GRAPH_GENERAL_PLAN.md` → all `*_P*_EXECUTION.md` + README table.
- **Single phase:** “Create execution plan for P0 only”.
- **Split legacy:** “Split FRAMEWORK_CALLOFF execution per phase”.
