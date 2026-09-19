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

**Config:** read `.agent/manifest.json` first — `flows`, `integrations`, `test_commands`, `review_context`, `default_scope` / `scopes`.

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
   - **`README.md`** in plan folder — execution table (Phase → file). Common convention.
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

## PR review context (Bugbot + Moonshot) — **hard gate**

Programs that ship **code + planning docs in one PR** must wire review context on the **first LOOP iteration** (same commit as first schema/bootstrap work when applicable). **Never skip.** This is how Bugbot and **Moonshot engineering inject** know which locked decisions apply.

**Do not** babysit Greptile, wait on Greptile checks, invoke `babysit-pr`, or treat `.greptile/files.json` as a reviewer. `integrations.greptile` is **false**.

Changed `.md` files appear in the PR diff, but Bugbot and Moonshot do **not** treat planning docs as authoritative unless wired.

| Consumer | Repo file | What to edit |
|:---|:---|:---|
| **Moonshot inject** (Revy pipeline) | `.revy/review-context.json` | **SSOT** — set `active_program`; add/update `programs[]` entry with `scope` + 3 doc `paths` |
| **Bugbot** | `.cursor/BUGBOT.md` | Markdown links to same docs (paths relative to `.cursor/`) |
| **Agent mirror** | `.agent/review-context.json` | Copy of SSOT after `.revy` is edited |

**SSOT workflow (RCX-D11 — mandatory on every program switch):**

1. Edit `.revy/review-context.json`:
   - `active_program` = this program's `id`
   - **`programs[]` = exactly one entry** — the active program only (`id`, `scope`, three doc `paths`). **Remove** prior/shipped program entries; do not accumulate.
2. Copy the same JSON to `.agent/review-context.json`.
3. Update `.cursor/BUGBOT.md` — **replace** program doc links with the active program's three docs only (remove shipped-program sections).
4. **Verify before phase gate:**
   ```bash
   python -m json.tool ../.revy/review-context.json > /dev/null
   pipenv run pytest tests/unit/test_engineering_context_manifest.py -q
   ```
5. If `tests/unit/test_generate_greptile_files.py` still exists, regenerate leftover `.greptile/files.json` from SSOT so CI does not drift (`python -m scripts.generate_greptile_files_from_review_context --write`). That file is **not** a reviewer and must not be babysat.
6. Commit **SSOT + agent mirror + `BUGBOT.md`** together in the first phase commit.

**Default doc paths** (when execution doc does not override):

1. **Active execution file** — current phase contract (or single-file execution plan for the whole program).
2. **Findings baseline** — locked Q# / decisions doc linked from execution header.
3. **General plan** — phase goals for the program.

**First-iteration checklist:**

- [ ] `.revy/review-context.json` — `active_program` switched; **`programs[]` has one entry only** (prior programs removed)
- [ ] `.agent/review-context.json` — identical to SSOT
- [ ] `.cursor/BUGBOT.md` — **only** active program + three doc links (shipped programs removed)
- [ ] `test_engineering_context_manifest.py` green
- [ ] All three ship in **first phase commit** — do not defer to final doc-sync phase

**Per-phase commit pattern:** phase code + **minimal** doc touch (README status row / execution table for that slice). Do **not** re-edit full findings + peer-review corpus every push (context budget).

**Not** `.cursor/rules/` — IDE-agent only; Bugbot does not read them.

**Reference:** [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](../../docs/review-pipeline/review-engineering-context/REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) RCX-D11.

If the execution doc has an explicit **PR review context** block — follow it, but **omit Greptile** even if the doc still names `files.json`.

---

## The LOOP

One **iteration** = one full phase. After success → **next phase immediately** unless a stop rule fires.

```text
FOR each phase in scope (discovered order):
  1. Read ONLY this phase's execution file (+ findings locks if doc references them)
  2. If file/README links **Authority:** — read it; stop if this phase contradicts it
  3. First iteration only: **PR review context hard gate** — SSOT `.revy/review-context.json` → `.agent` mirror → `BUGBOT.md` → `test_engineering_context_manifest.py` (see section above; never skip). Do not babysit Greptile.
  4. Cancel prior phase todos; create one todo per **remaining** subphase (from resume point if set)
  5. FOR each subphase in order (skip subphases before resume point):
       implement → run tests from **Deliverable** / doc → mark todo done
       if migration subphase (new handwritten Alembic revision): STOP — migration pause (see stop rules)
       (last phase: **`post-finish-gap-pass`** once before doc-sync subphases)
  6. **Lint** — per manifest `test_commands` for each scope glob with changes this iteration (`backend/**` → ruff fix + check + unit tests; `frontend/**` → lint + test)
  7. Run **phase gate** from execution doc — must be green
  8. **LOCAL BUGBOT** — FIND → fix → CLOSE until clean (hard gate)
  9. **Revy idle?** — when `integrations.revy: true`: `gh pr checks`; **no push while Revy `pending`/`in_progress`**
  10. **`ship-changes`** — commit, Revy gate, push, PR (one commit per phase; title per ship-changes § PR title pattern)
  11. Log: phase id, commit sha, PR URL if any, next phase id
  12. Continue LOOP
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
- **First LOOP iteration** (or any commit touching `.revy/`): phase gate **must** include:
  ```bash
  pipenv run pytest tests/unit/test_engineering_context_manifest.py -q
  ```
- **Never ship** until green. Two failures after fixes → stop LOOP; report last good commit.

---

## Local Bugbot (before every commit/push — hard gate)

**Mandatory** before **each** LOOP commit and **every** `git push` on the feature branch — including after `babysit-revy-pr` fixes.

1. Invoke **`review-bugbot`** skill (Bugbot subagent, `run_in_background: false`).
2. Default: `Diff: uncommitted changes` (or `branch changes` after staging).
3. Point at active execution file + findings in **Custom Instructions** (see [agents/PROMPTS.md](../../docs/review-pipeline/agents/PROMPTS.md)).
4. Fix **blockers**; re-run **ruff** + **phase gate** if Python changed.
5. **Do not commit or push** if Bugbot reports unresolved blockers (stop rule below).

Revy runs **after** push — it never replaces this step. Do not wait on or babysit Greptile.

---

## Revy gate (when `integrations.revy: true`)

Before **every** push in the LOOP:

1. `gh pr checks <PR>` — Revy must **not** be `pending` / `in_progress` / `queued`.
2. Push only when Revy is `pass`, `fail`, `skipping`, `neutral`, or absent (app suspended).
3. After push, Revy may restart — **wait again** before the next push.
4. Fetch Revy comments; fix actionable items; Bugbot; commit; repeat from step 1.

Details: `ship-changes` skill § Revy gate. **PR title:** `gh pr edit` when scope grows — outcome-first (`feat(<program>): …`), not bare phase id. See `ship-changes` § PR title pattern.

---

## Ship (each LOOP iteration)

Per **`ship-changes`**. LOOP extras:

- Branch must already exist (see **Branch** above) — do not create a new branch per phase.
- Commit message: `feat(<program-slug>): <PhaseId> <short goal>` — phase id in commit, not PR title alone.
- After Bugbot fixes: re-run **lint** + **phase gate** before commit.
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
- User may **`babysit-revy-pr`** separately. Do not run `babysit-pr` (Greptile is off).

**Invoke with:** attach plan folder or start execution file + `/phase-execution`. Opt out of PR: add **“no pr”**.

**Example:** `@docs/…/CPV2_MARKETS_C0_EXECUTION.md` + phase-execution → discovers C0–C4 in folder README → LOOP C0→C1→C2→C3→C4 on feature branch.
