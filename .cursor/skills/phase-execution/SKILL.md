---
name: phase-execution
description: >-
  Run a full execution-plan LOOP from a pointed start file or plan folder:
  auto-discover all phases, implement every subphase, ruff, phase gate, Bugbot, commit
  and push per phase, auto-open GitHub PR on first push, continue through all
  phases without pausing. Use when the user attaches a plan folder or execution
  file and invokes phase-execution.
---

# Phase execution (LOOP)

**Entry:** user attaches a **plan folder** or **start execution file** and invokes this skill. **Do not ask** for phase ids or “LOOP” — discover from path + sibling docs.

**Folder attachment:** if the user points at a directory (e.g. `…/cpv2_markets/`), use that as **plan folder** and **start file** = first execution file in `README.md` execution table (or lowest phase id from glob).

**Default:** run **all phases** from start through last, one LOOP iteration per phase — no chat pause between subphases **except stop rules below**.

**Never ask** “Continue?” after a subphase — keep implementing until the phase ships or a **stop rule** fires.

**Sibling:** `execution-peer-review` = read-only review before LOOP. **`post-finish-gap-pass`** = last phase, before doc-sync. **`ship-changes`** = Bugbot + commit + push + PR.

---

## Start file → plan folder → phase list

1. **Start file** = the execution plan path the user attached (e.g. `…/cpv2_markets/CPV2_MARKETS_C0_EXECUTION.md`).
2. **Plan folder** = directory containing that file. All discovery is scoped to this folder unless the README links elsewhere.
3. **Start phase id** = parse from the start file:
   - Filename: `_C0_`, `_P7_`, `_UX0_`, `P7_…_execution`, etc.
   - Or first heading / “Phase **C0**” line in the doc.
4. **Ordered phase list** (first match wins):
   - **`README.md`** in plan folder — execution table (Phase → file). KP convention.
   - **`*_GENERAL_PLAN.md`** in plan folder — phase blocks (`## C0`, `## P0`, …) in doc order.
   - **Glob** `*EXECUTION*.md` / `*execution_plan*.md` in plan folder — sort by phase id (numeric suffix: 0, 1, 2…).
5. **Scope** = every phase from **start phase** through **last** in the ordered list. Pointing at the first execution file = **full plan**.

Announce once before coding: plan folder, start phase, end phase, file per phase (compact list).

**Optional override** (rare): user explicitly says “only C0”, “through C2”, or **“from P0.3”** / **“resume P0.3”** — narrow scope or skip completed subphases; otherwise **full LOOP**.

---

## Branch (hard gate)

- **Forbidden:** implement, commit, or **push** on `main`, `master`, or the repo default production branch.
- If on forbidden branch: **stop** — ask user to create/checkout a feature branch. Do not push to fix this.
- Confirm branch name once at start; all phase commits stay on it.

---

## PR review context (Greptile + Bugbot)

Programs that ship **code + planning docs in one PR** should wire review bots on the **first LOOP iteration** (same commit as first schema/bootstrap work when applicable).

Changed `.md` files appear in the PR diff, but Greptile/Bugbot do **not** treat planning docs as authoritative unless wired.

| Tool | Repo file | Content |
|:---|:---|:---|
| **Greptile** | `.greptile/files.json` | `path` entries + `scope` (e.g. `backend/**`) |
| **Bugbot** | `.cursor/BUGBOT.md` | Markdown links to the same docs (paths relative to `.cursor/`) |

**Default paths to wire** (when execution doc does not override):

1. **Active execution file** — current phase contract (or single-file execution plan for the whole program).
2. **Findings baseline** — locked Q# / decisions doc linked from execution header.
3. **Authority** doc — only if execution file links `**Authority:**`.

**First-iteration checklist:**

- [ ] `.greptile/files.json` exists; scopes match touched code (`backend/**`, `frontend/**`, …).
- [ ] `.cursor/BUGBOT.md` links execution + findings (and authority when present).
- [ ] Both ship in **first phase commit** — do not defer to final doc-sync phase.

**Per-phase commit pattern:** phase code + **minimal** doc touch (README status row / execution table for that slice). Do **not** re-edit full findings + peer-review corpus every push (context budget).

**Not** `.cursor/rules/` — IDE-agent only; Bugbot does not read them.

**Reference:** [REVIEW_QUALITY_EXECUTION.md](../../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md) § PR review context.

If the execution doc has an explicit **PR review context** block — follow it over these defaults.

**RCX Greptile sync:** after editing `.greptile/review-context.json`, run `cd backend && python -m scripts.generate_greptile_files_from_review_context --write` and commit SSOT + generated `.greptile/files.json` together.

---

## The LOOP

One **iteration** = one full phase. After success → **next phase immediately** unless a stop rule fires.

```text
FOR each phase in scope (discovered order):
  1. Read ONLY this phase's execution file (+ findings locks if doc references them)
  2. If file/README links **Authority:** — read it; stop if this phase contradicts it
  3. First iteration only: ensure **PR review context** wiring (`.greptile/files.json`, `.cursor/BUGBOT.md`) per section above
  4. Cancel prior phase todos; create one todo per **remaining** subphase (from resume point if set)
  5. FOR each subphase in order (skip subphases before resume point):
       implement → run tests from **Deliverable** / doc → mark todo done
       if migration subphase (new handwritten Alembic revision): STOP — migration pause (see stop rules)
       (last phase: **`post-finish-gap-pass`** once before doc-sync subphases)
  6. **Ruff** (backend) — safe fixes only; must pass before phase gate
  7. Run **phase gate** from execution doc — must be green
  8. **`ship-changes`** — Bugbot, commit, push, PR (one commit per phase)
  9. Log: phase id, commit sha, PR URL if any, next phase id
  10. Continue LOOP
```

**Context hygiene:** only the **current** phase execution file is active scope; respect **Out of scope** / **Depends on** in that file; do not re-implement prior phases.

---

## Subphase rules

- In doc order; no merging; no “Continue?” prompts.
- **Resume:** if user said **from Pn.x** — skip earlier subphases in that phase (verify tree; do not re-implement).
- After each subphase: run **Deliverable** verification → mark todo done → next subphase (unless migration pause).
- **Migration subphase:** after deliverable tests pass → **stop LOOP** — do not run later subphases or ship this phase yet.
- Backend: `backend/` + `pipenv run …`. Migrations: handwritten only — no `--autogenerate`.
- **Last phase:** `post-finish-gap-pass` → doc-sync per `create-execution-plan`.

---

## Ruff (before phase gate)

When the phase touches **backend Python** (always run if any `backend/` file changed this iteration):

From **`backend/`**:

```bash
pipenv run ruff check --fix .
pipenv run ruff check .
```

- **`--fix`** applies **safe** fixes only — matches CI (`ruff check .` in `.github/workflows/deploy.yml`).
- **Never** pass `--unsafe-fixes` or `--unsafe-fix`.
- Second `ruff check .` (no fix) must exit **0** before phase gate. Fix remaining issues manually; do not commit with ruff errors.
- After Bugbot fixes that touch Python, re-run both commands before re-gate.

---

## Phase gate (before ship)

- Use the execution doc **phase gate** block when present.
- **Never ship** until green. Two failures after fixes → stop LOOP; report last good commit.

---

## Local Bugbot (before every commit/push — hard gate)

**Mandatory** before **each** LOOP commit and **every** `git push` on the feature branch — including after `babysit-pr` fixes.

1. Invoke **`review-bugbot`** skill (Bugbot subagent, `run_in_background: false`).
2. Default: `Diff: uncommitted changes` (or `branch changes` after staging).
3. Point at active execution file + findings in **Custom Instructions** (see [agents/PROMPTS.md](../../docs/review-pipeline/agents/PROMPTS.md)).
4. Fix **blockers**; re-run **ruff** + **phase gate** if Python changed.
5. **Do not commit or push** if Bugbot reports unresolved blockers (stop rule below).

Greptile and Revy run **after** push — they never replace this step.

---

## Ship (each LOOP iteration)

Per **`ship-changes`**. LOOP extras:

- Branch must already exist (see **Branch** above) — do not create a new branch per phase.
- Commit message: `feat(scope): <PhaseId> <short goal>`
- After Bugbot fixes: re-run **ruff** + **phase gate** before commit.
- Opt out of PR: user said **no pr** in the invoke message.

---

## Stop rules (break the LOOP)

| Rule | Action |
|:---|:---|
| All scoped phases complete | Stop; summary of commits + optional PR |
| **Migration subphase** done | Stop after its deliverable tests. **More subphases in phase:** report revision + next id; resume `phase-execution` + **from Pn.x**. **Migration was last subphase:** resume same phase file → ruff → gate → **`ship-changes`** (no `from` needed). |
| Phase gate failed twice | Stop |
| **Ruff** still failing after fix | Stop; do not commit |
| Bugbot blockers unresolved | Stop; no commit |
| User override “only …” / “through …” | Stop at named boundary |

**Resume start** (`from Pn.x` / `resume Pn.x`) is **not** a stop — it skips completed subphases and continues the LOOP.

**Only** the migration subphase may mid-phase stop. All other subphases run through to phase ship.

---

## Execution doc contract

Plans must follow **`create-execution-plan`** (one file per phase, README, phase gate, 3–6 subphases). If gate missing, propose minimal gate before implementing.

Programs with code + docs in one PR: execution doc **first phase** should include **PR review context** (or link to a single-file execution §) — see **PR review context** section above.

---

## After the LOOP

- Summary: phases completed, SHAs, **PR URL**, early-stop reason.
- User may **`babysit`** the PR separately.

**Invoke with:** attach plan folder or start execution file + `/phase-execution`. Opt out of PR: add **“no pr”**.

**Example:** `@docs/…/CPV2_MARKETS_C0_EXECUTION.md` + phase-execution → discovers C0–C4 in folder README → LOOP C0→C1→C2→C3→C4 on feature branch.
