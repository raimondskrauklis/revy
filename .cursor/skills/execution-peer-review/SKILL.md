---
name: execution-peer-review
description: >-
  Peer-review execution plan files one phase at a time (P0, P1, …) against the
  codebase, findings, and general plan. Use when the user asks to review
  execution plans, cross-check P0–P8 execution files, or validate a plan folder
  before phase-execution. Writes findings to
  plan-folder/reviews/execution-peer-review/ — chat is summary + link only.
---

# Execution peer review

Read-only review of **per-phase execution files** before `phase-execution`. **Not** a bulk skim — review **one file, report, then next file**.

**Sibling:** `architecture-peer-review` — findings + general plan; artifacts in `<plan-folder>/reviews/architecture-peer-review/`. Use **this skill** for the execution file set after `create-execution-plan`.

**Forbidden:** edit execution files, findings, general plan, or phase execution files; fix gaps; run `phase-execution`; create commits.

**Allowed:**
- Create or update files under `<plan-folder>/reviews/execution-peer-review/`
- Add or update **one index row/link** in `<plan-folder>/README.md` pointing at `reviews/execution-peer-review/README.md` (no other plan-folder README edits)

---

## Entry

User attaches:

- **Plan folder** (preferred), or
- **`README.md`** with execution table, or
- A single execution file (review that file only).

Optional user hints:

- **Re-review / pass 2+** — after a fix agent updated execution files.
- **Delta only** — re-review only phases the user lists or that changed since last pass.
- **Spot** — re-review one phase file only (e.g. P4 after splice fix).

Discover the ordered file list from **`README.md` execution table** or `waves/*_EXECUTION.md` index (same as `phase-execution`). If no README, glob `*EXECUTION*.md` in folder and sort by phase id.

Announce once in chat: plan folder, phase count, file list, LOOP order, pass number.

**Optional baseline read (once, before P0):** `*_FINDINGS.md`, `*_GENERAL_PLAN.md`, architecture peer-review latest pass — for locked decisions and phase goals. Do **not** read all execution files upfront.

---

## Review artifact (required)

All findings go to disk — chat is a **short summary + link**, not the SSOT.

### Layout

```
<plan-folder>/
  reviews/
    execution-peer-review/
      README.md              ← pass index (create on first pass)
      pass-01-YYYY-MM-DD.md  ← one file per full review pass
      pass-02-YYYY-MM-DD.md
```

**Plan folder examples:** `docs/review-pipeline/pr-summary-rollup/`, `docs/review-pipeline/pipeline-observability/`.

### Legacy (do not migrate unless user asks)

Older programs may note peer review only in chat or a single execution-file header. **New reviews** use `reviews/execution-peer-review/`. On re-review of a legacy program, start `pass-01-…` in the new layout; link historical notes from README if present.

### Pass file naming

- First pass: `pass-01-YYYY-MM-DD.md` (today’s date).
- Each **full** re-review: **new** file, increment pass (`pass-02-…`). **Never overwrite or append to a prior pass file** — each file is an immutable snapshot.
- **Delta** re-review: always create a **new** file `pass-NN-YYYY-MM-DD-delta.md` (same `NN` as the pass being delta’d, or next unused `NN` if multiple deltas that day). Link prior pass under `## Prior pass`. Put the updated `## Verdict` / **BLOCK**, rollup, and scoped phase outcomes in the **new** file only.
- **Spot** re-review (one phase file): **new** `pass-NN-YYYY-MM-DD-spot.md` (or `-delta.md` if user called it delta); never mutate the prior pass file.
- After any re-review: update reviews `README.md` status line **and** the pass index table columns (`Critical`, `High`, `Block next step`) to point at the **latest** file. Do not leave a stale BLOCK: yes on the index.

### `README.md` index (update every pass)

| Pass | File | Date | Scope | Critical | High | Block next step |
|------|------|------|-------|----------|------|-----------------|
| 1 | [pass-01-…](./pass-01-2026-08-08.md) | 2026-08-08 | P0–P3 execution | 0 | 0 | no |

Link to execution index + findings + general plan. Status line: `Latest pass: N — BLOCK phase-execution: yes/no`.

If `<plan-folder>/README.md` exists, add or update a row pointing to `reviews/execution-peer-review/README.md`.

### Pass file header (required)

```markdown
# Execution peer review — pass N

**Plan folder:** `docs/…/`  
**Date:** YYYY-MM-DD  
**Scope:** full (P0–Pn) | delta (phases …) | spot (Pn only)  
**Reviewer:** execution-peer-review skill  
**Baseline:** [FINDINGS.md](…), [GENERAL_PLAN.md](…), [EXECUTION index](…), codebase paths cited below  

## Verdict

Review complete: X critical, Y high, Z medium/low.  
**BLOCK phase-execution:** yes/no — one-line reason.

## Prior pass

Link to pass N-1 if re-review; note what the fix agent was asked to address.

## Rollup (critical / high)

| Severity | Phase | Title |
|:---|:---|:---|

## Per-phase findings

(one section per execution file reviewed)

## Execution contract checklist

- [ ] …

**Next:** named skill or human gate.
```

### Chat response (after writing files)

1. One sentence: pass number, scope, BLOCK yes/no.
2. **Link** to the pass file (relative path from repo root).
3. Link to `reviews/execution-peer-review/README.md`.
4. List **critical/high titles only** (no full per-phase tables in chat).
5. If BLOCK: what must be fixed before `phase-execution`; suggest fix agent reads pass file.

---

## One file at a time (strict)

For **each** execution file in order:

1. **Read only this execution file** (+ grep/read **repo paths cited in this file**).
2. Cross-check **this phase** against:
   - Matching **general plan** `## Pn` block
   - **Findings** locked decisions (no re-opening; flag if execution contradicts)
   - **Architecture peer-review** latest pass (if present)
   - **`create-execution-plan` contract** (checklist below)
   - **Prior phases** only via what *this file* claims — note cross-phase contradictions; do not re-read prior execution files unless needed to confirm
3. **Append findings for this phase to the pass file** (template below).
4. **Then** open the next execution file. Never defer per-file findings to a final mega-summary.

If a phase is clean: one line `**Pn — no gaps found.**` + **Verified OK** bullets.

---

## Per-phase output template

```markdown
## Pn — `<relative/path/to/FILE.md>`

| Severity | Area | Finding |
|:---|:---|:---|
| critical | codebase | … |
| high | general plan | … |
| medium | execution contract | … |
| low | clarity | … |

**Verified OK:** (1–3 bullets)
```

**Severity:** critical = wrong behavior / rework if implemented; high = contradicts findings or general plan; medium = missing gate, vague deliverable, scope leak; low = wording, optional clarity.

**Questions:** only if blocking — `## Open questions` in pass file (max 3).

---

## Re-review modes

| Mode | When | What to read | Output |
|------|------|--------------|--------|
| **Full** | First review, or user says “full re-review” | All execution files in LOOP order | New `pass-NN-…md` |
| **Delta** | User says “re-review after fixes” | Changed phase files + prior pass | New `pass-NN-…-delta.md` (never append to prior) |
| **Spot** | User names one phase | That `*_Pn_EXECUTION.md` only | New `pass-NN-…-spot.md` (never append to prior) |

**Delta / spot rules:**

- Re-read prior pass findings for scoped phases; mark each **resolved / open / new** in the **new** file.
- Do not re-copy unchanged clean phases verbatim — one line `**Pn — no new gaps** (verified unchanged).`
- If a “fixed” item is still broken, escalate severity.
- Put fresh `## Verdict` / **BLOCK** and rollup in the new file; update reviews `README.md` to the latest file. Leave prior pass files untouched.

**Iteration loop (typical):**

```
create-execution-plan → execution-peer-review (pass 1)
  → fix agent (edits execution files per pass-01)
  → execution-peer-review (pass 2, delta or spot)
  → … until BLOCK: no → phase-execution from P0
```

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
| **Human gate** if spike/ops/sign-off | |
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

## Anti-patterns

- Dump full per-phase tables in chat instead of the pass file.
- Read all `*_EXECUTION.md` files, then one combined gap list.
- Skip a phase because “similar to P2”.
- Edit execution files to fix findings.
- Overwrite prior pass files.

**Invoke with:** attach plan folder or README + “execution peer review” / “review all execution files P0–P8” / “re-review pass 2 after P4 fix”.
