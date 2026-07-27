# Agent orchestration

**Index:** [agents/README.md](./README.md) · **Prompts:** [PROMPTS.md](./PROMPTS.md)

Distill how to run **phase-execution** on large program PRs: ship **Revy**, run **Greptile + local Bugbot + Revy** on our PRs (#50 has **no GitHub Bugbot**) and distill what to absorb — not depend on external tools long-term. Grows from [PR #50 dogfood](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md).

**North star:** tune Revy to do what Greptile (and GitHub Bugbot-class depth, from operator/arch reference) do well. External tools = **reference + dogfood**, not product architecture.

**Audience:** Humans + master agent (Composer) orchestrating reviewer subagents.

**Roles:** [prompts/ROLES.md](./prompts/ROLES.md) — human talks to master only; master compiles briefs for Bugbot.

---

## Golden rule: local Bugbot before **every** push

Master **blocks run** until gate green. Skipping Bugbot to save time is when corners get cut.

| When | Gate | Skippable? |
|------|------|------------|
| Before **first** push on a branch | Local Bugbot on `uncommitted changes` or `branch changes` | **No** |
| Before **each phase** commit (LOOP) | Same | **No** |
| After fixing Greptile (`babysit-pr`) | VALIDATE → CLOSE (re-CLOSE until clean) | **No** |
| After `ruff`/test fixes only | Re-run Bugbot if Python changed | **No** |

**Greptile on PR is post-push** dogfood — distill into findings. **Local Bugbot** stays (Cursor, pre-push). **Revy GitHub App suspended** for #50 (2026-07-27) — no webhook/autostart/token burn; re-enable at deploy milestones. **GitHub Bugbot** not on #50; operator/arch reference for RQ4+ bar.

```text
implement → pytest → ruff → phase gate → LOCAL BUGBOT → commit → push
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
            Greptile (PR review)                              Revy — suspended on GitHub for #50 dogfood (no new runs)
            babysit-pr fixes valid threads                    (may lag branch — note in dogfood)
                    │
                    └── fix → ruff → VALIDATE → CLOSE (until clean) → push
```

---

## Reference reviewers — distill, don’t depend

Run in **parallel on our PRs** while building Revy. Capture **what they do well and how** → findings → RQ waves. Customer-facing product is **Revy only**.

| Reference | On PR #50? | Why we care | What to distill into Revy | Stays after v1? |
|-----------|------------|-------------|---------------------------|-----------------|
| **Local Bugbot** (Cursor) | Yes (pre-push) | Hygiene; included in IDE | Fast diff pass; agent read/grep on harder hunks | **Yes** — dev workflow |
| **Greptile** (GitHub) | Yes (post-push) | Contract/spec via RC0 `files.json` | Execution-doc findings; P-badge inline; confidence (RQ7) | **No** — patterns → Revy |
| **GitHub Bugbot** | **No** on #50 | Operator knowledge + arch notes — deeper than local, often finds more | Multi-pass / agentic trace (RQ4+) | **No** — patterns → Revy |
| **Revy** (deploy) | Yes | Product on real stack | Gap vs Greptile UX + retrieval | **Yes** — the product |

**Hypothesis:** Greptile and GitHub Bugbot (where used) are **agent loops** under the hood — same class as local Bugbot, more passes/PR context. Revy implements distilled mechanics; we do not stack vendors.

**Visual/context bar:** Greptile/Bugbot UX — [dogfood visual §](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#visual--context-ux--greptile--bugbot-vs-revy-target-bar).

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

**Pass 2+ output:** require **Closed** + **Deferred** tables — not only “no bugs” ([OUTPUT_FORMAT.md](./prompts/OUTPUT_FORMAT.md), RC-D14).

**Iterative expectation:** each Bugbot pass after fixes may surface **new** bugs on the same diff (lifecycle, cross-file). That is correct behavior — same as Greptile multi-pass on PRs. See [RQ1 local Bugbot §](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#iterative-agent-review--rq1-local-bugbot) and RC-D8 in [learnings](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md).

**Dogfood stance:** Cursor + local Bugbot complement Revy while we build (RC-D7). Product north star: **Revy on repo** replaces external review for customers.

### Parallelism (safe)

| Parallel | Sequential |
|----------|------------|
| Human applies staging migration while Greptile runs on PR | Bugbot → commit → push |
| Multiple `gh` queries while planning | Migration subphase + later subphases same session |
| User triages Greptile while agent stopped at pause | Push before Bugbot green |

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
[ ] Commit: feat(review-quality): RQn …
[ ] Push
[ ] Optional: note dogfood row (Greptile/Revy when available)
[ ] Migration pause? STOP — do not continue LOOP
```

**First iteration only:** `.greptile/files.json` + `.cursor/BUGBOT.md` (RC0).

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
| **Rely** on Greptile/GitHub Bugbot as permanent product stack | We distill their strengths into Revy; parallel runs are research |
| Push without local Bugbot | Cheap pre-push gate while building (Cursor) |
| Parent paraphrases Greptile; Bugbot never gets VALIDATE hook | Anchors on wrong minimum fix (RC-D17) |
| Master reports "Bugbot clean" without synthesis | Human must hear *why*, not subagent transcript |
| Treat Greptile findings as “done” without dogfood row | Distillation is the deliverable — update DOGFOOD / learnings |
| Copy full Bugbot transcripts into learnings | Archive in `chain_of_thoughts/`; distill one row per pattern |
| Expect local Bugbot = GitHub Bugbot | Same class (agents), different depth/passes — both inform Revy design |
| Treat Greptile as pre-push gate | Runs after push only |
| Full findings edit every commit | Blows Bugbot/Greptile context budget |
| Parent + Bugbot same turn as half-done code | Wastes review; review incomplete diff |
| Ignore migration pause | Staging breaks; RQn+1 depends on schema |

---

## Backlog (evolve this folder)

- [x] Per-RQ distill in [prompts/PHASES.md](./prompts/PHASES.md)
- [x] Pass 1/2 output contract [prompts/OUTPUT_FORMAT.md](./prompts/OUTPUT_FORMAT.md)
- [ ] `SUBAGENTS.md` — Task vs explore decision tree
- [ ] `DOGFOOD_INDEX.md` — one row per program PR
- [ ] RC-API: fetch Revy run JSON for agent babysit without paste
