# Agent orchestration

**Index:** [agents/README.md](./README.md) · **Prompts:** [PROMPTS.md](./PROMPTS.md)

Distill how to run **phase-execution** on large program PRs: ship **Revy**, run **local Bugbot + Revy** on our PRs. Grows from [PR #50 dogfood](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md).

**North star:** tune Revy. External vendor reviewers are not part of the agent LOOP. `integrations.greptile` is false.

**Audience:** Humans + master agent (Composer) orchestrating reviewer subagents.

**Roles:** [prompts/ROLES.md](./prompts/ROLES.md) — human talks to master only; master compiles briefs for Bugbot.

---

## Golden rule: local Bugbot before **every** push

Master **blocks run** until gate green. Skipping Bugbot to save time is when corners get cut.

| When | Gate | Skippable? |
|------|------|------------|
| Before **first** push on a branch | Local Bugbot on `uncommitted changes` or `branch changes` | **No** |
| Before **each phase** commit (LOOP) | Same | **No** |
| Before **push** when Revy check active on PR | Revy idle — `gh pr checks`; no push while `pending`/`in_progress` | **No** |
| After fixing Revy (`babysit-revy-pr`) | Poll 120s until idle → fix → Bugbot → push → loop | **No** |
| After `ruff`/test fixes only | Re-run Bugbot if Python changed | **No** |

**Revy on PR (when app enabled):** post-push check on our own PRs — **wait for idle before the next push** so we do not stack runs or push over an in-flight review. If Revy is suspended (no check row), gate is a no-op.

**Do not** babysit Greptile. **Local Bugbot** stays (Cursor, pre-push).

```text
implement → pytest → ruff → phase gate → LOCAL BUGBOT → commit
                                              │
                    Revy idle? (if check on PR) ──no pending──► push
                                              │
                                              ▼
                                    Revy (PR check, when enabled)
                                    wait idle → babysit-revy-pr → push fixes
```

---

## Reviewers on our PRs

| Reviewer | When | Stays? |
|----------|------|--------|
| **Local Bugbot** (Cursor) | Pre-push | **Yes** — LOOP hard gate |
| **Revy** (deploy) | Post-push | **Yes** — the product |
| **Greptile** | — | **No** — off; do not babysit |

Historical dogfood vs Greptile (PR #50) stays in [DOGFOOD_PR50](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md). It is not part of the current agent LOOP.

---

## Parent agent (orchestrator) discipline

Patterns that worked on PR #50 (Composer-class parent):

### Scope and memory

| Do | Don't |
|----|-------|
| Read **only** the current phase execution file + findings locks it cites | Re-read entire findings corpus every subphase |
| One **active** execution contract per LOOP iteration | Merge RQn+1 work into RQn commit |
| **Docs baseline** commit, then phase commits | 20 MD files + code in every push |
| Update `BUGBOT.md` when a **new** program starts | Stale contract pointer |

### LOOP control

| Do | Don't |
|----|-------|
| `feat/<topic>` from `main`; announce branch once | Implement on `main` |
| Stop at **migration pause**; report next phase id | Auto-continue RQ1 before human applies migration |
| `feat(review-quality): RQn …` commit messages | Vague "wip" commits |
| Capture dogfood row in [DOGFOOD_PR50](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md) | Rely on memory |

### Subagent use (when / when not)

| Use subagent | Use parent direct tools |
|--------------|-------------------------|
| **Bugbot** — pre-push review (`review-bugbot`, `run_in_background: false`) | Implementation, pytest, ruff, migration authoring |
| **After Bugbot** — skim subagent transcript; save gate exports when useful | Distill durable patterns into learnings/dogfood (not full transcript paste) |
| **execution-peer-review** — read-only, separate session | Babysit fixes (parent implements) |
| **explore** — broad codebase unknowns | Single-file grep/read when path known |

**Evidence archive:** [`chain_of_thoughts/`](./chain_of_thoughts/) holds committed Bugbot gate exports and long Cursor chats — **primary evidence**, not optional fluff. Add files **when a run is worth keeping** (not every spin). Day-to-day context: read transcripts on demand; **learnings** hold distilled rows (RC-D7–D9, dogfood tables).

**Do not** spawn Bugbot in parallel with implementation — **sequential:** code complete → Bugbot → fix → **re-Bugbot if blockers** → push.

**Pass 2+ gate:** master reads thinking export; clean reasoning + no open blockers — not subagent table shape ([OUTPUT_FORMAT.md](./prompts/OUTPUT_FORMAT.md), RC-D23).

**Iterative expectation:** each Bugbot pass after fixes may surface **new** bugs on the same diff (lifecycle, cross-file). That is correct behavior — same as Greptile multi-pass on PRs. See [RQ1 local Bugbot §](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#iterative-agent-review--rq1-local-bugbot) and RC-D8 in [learnings](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md).

**Dogfood stance:** Cursor + local Bugbot complement Revy while we build (RC-D7). Product north star: **Revy on repo** replaces external review for customers.

### Parallelism (safe)

| Parallel | Sequential |
|----------|------------|
| Human applies staging migration while Revy runs on PR | Bugbot → commit → push |
| Multiple `gh` queries while planning | Migration subphase + later subphases same session |
| User triages Revy while agent stopped at pause | Push before Bugbot green |

---

## Per-phase checklist (parent agent)

```text
[ ] On feat branch (not main)
[ ] Read execution § RQn only
[ ] Implement + deliverable pytest
[ ] ruff (backend if touched)
[ ] Phase gate green
[ ] LOCAL BUGBOT Pass 1 — blockers fixed
[ ] LOCAL BUGBOT Pass 2+ — Closed + Deferred tables; re-gate if blockers
[ ] Revy idle on PR? (if check present — no pending/in_progress)
[ ] Commit: feat(<program>): <PhaseId> …
[ ] Push
[ ] Optional: note dogfood row (Revy when available)
[ ] Migration pause? STOP — do not continue LOOP
```

**First iteration only:** `.revy/review-context.json` + `.agent/review-context.json` + `.cursor/BUGBOT.md`.

Copy-paste prompts: [PROMPTS.md](./PROMPTS.md) · Distilled: [prompts/](./prompts/).

---

## PR #50 distilled outcomes

| Lesson | Doc |
|--------|-----|
| Local Bugbot clean on RQ0 ORM; Greptile caught schema FK/index | [DOGFOOD_PR50](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md) |
| Revy (old deploy) still valuable for intent vs code | RC-D2 |
| Greptile visual/context = RQ7 target | RC-D6 |
| Babysit fixed 6 Greptile threads; new P1 `index_mode` → RQ1 | Greptile triage table |
| G10 in-progress check | [REVIEW_CONTEXT](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) |

---

## Anti-patterns

| Anti-pattern | Why |
|--------------|-----|
| **Babysit Greptile** | Off — `integrations.greptile` is false |
| Push without local Bugbot | Cheap pre-push gate while building (Cursor) |
| Master reports "Bugbot clean" without synthesis | Human must hear *why*, not subagent transcript |
| Copy full Bugbot transcripts into learnings | Archive in `chain_of_thoughts/`; distill one row per pattern |
| Full findings edit every commit | Blows Bugbot context budget |
| Parent + Bugbot same turn as half-done code | Wastes review; review incomplete diff |
| Ignore migration pause | Staging breaks; RQn+1 depends on schema |

---

## Backlog (evolve this folder)

- [x] Per-RQ distill in [prompts/PHASES.md](./prompts/PHASES.md)
- [x] Pass 1/2 output contract [prompts/OUTPUT_FORMAT.md](./prompts/OUTPUT_FORMAT.md)
- [ ] `SUBAGENTS.md` — Task vs explore decision tree
- [ ] `DOGFOOD_INDEX.md` — one row per program PR
- [ ] RC-API: fetch Revy run JSON for agent babysit without paste
