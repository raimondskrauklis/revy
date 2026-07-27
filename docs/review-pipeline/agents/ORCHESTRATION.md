# Agent orchestration

**Index:** [agents/README.md](./README.md) · **Prompts:** [PROMPTS.md](./PROMPTS.md)

Distill how to run **phase-execution** on large program PRs with **local Bugbot**, **Greptile**, and **Revy**. Grows from [PR #50 dogfood](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md).

**Audience:** Humans + parent agents (Composer) orchestrating subagents.

---

## Golden rule: local Bugbot before **every** push

| When | Gate | Skippable? |
|------|------|------------|
| Before **first** push on a branch | Local Bugbot on `uncommitted changes` or `branch changes` | **No** |
| Before **each phase** commit (LOOP) | Same | **No** |
| After fixing Greptile (`babysit-pr`) | Re-run Bugbot, then push | **No** |
| After `ruff`/test fixes only | Re-run Bugbot if Python changed | **No** |

**Greptile / Revy on GitHub are post-push** — they do not replace pre-push Bugbot.

```text
implement → pytest → ruff → phase gate → LOCAL BUGBOT → commit → push
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
            Greptile (PR review)                              Revy autostart (deployed stack)
            babysit-pr fixes valid threads                    (may lag branch — note in dogfood)
                    │
                    └── fix → ruff → LOCAL BUGBOT again → push
```

---

## Three reviewers — roles

| Agent | When | Input contract | Output use |
|-------|------|----------------|------------|
| **Bugbot** (local) | Pre-push | `.cursor/BUGBOT.md` + diff | Block commit on real bugs; table in chat |
| **Greptile** | Post-push | `.greptile/files.json` | Inline P1/P2 + summary; `babysit-pr` |
| **Revy** | Post-push | Shipped code on staging/prod | Table check + app link; RQ1+ improves |

**Visual/context bar:** Greptile/Bugbot — [dogfood visual §](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#visual--context-ux--greptile--bugbot-vs-revy-target-bar).

---

## Parent agent (orchestrator) discipline

Patterns that worked on PR #50 (Composer-class parent):

### Scope and memory

| Do | Don't |
|----|-------|
| Read **only** the current phase execution file + findings locks it cites | Re-read entire findings corpus every subphase |
| One **active** execution contract per LOOP iteration | Merge RQn+1 work into RQn commit |
| **Docs baseline** commit, then phase commits | 20 MD files + code in every push |
| Update `BUGBOT.md` **active phase** line each RQ | Stale phase pointer |

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
| **execution-peer-review** — read-only, separate session | Babysit fixes (parent implements) |
| **explore** — broad codebase unknowns | Single-file grep/read when path known |

**Do not** spawn Bugbot in parallel with implementation — **sequential:** code complete → Bugbot → fix → push.

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
[ ] LOCAL BUGBOT — blockers fixed, re-gate if needed
[ ] Commit: feat(review-quality): RQn …
[ ] Push
[ ] Optional: note dogfood row (Greptile/Revy when available)
[ ] Migration pause? STOP — do not continue LOOP
```

**First iteration only:** `.greptile/files.json` + `.cursor/BUGBOT.md` (RC0).

Copy-paste prompts: [PROMPTS.md](./PROMPTS.md).

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
| Push without local Bugbot | Greptile/Revy are slower feedback; miss easy blockers |
| Treat Greptile as pre-push gate | Runs after push only |
| Full findings edit every commit | Blows Bugbot/Greptile context budget |
| Parent + Bugbot same turn as half-done code | Wastes review; review incomplete diff |
| Ignore migration pause | Staging breaks; RQn+1 depends on schema |

---

## Backlog (evolve this folder)

- [ ] Per-RQ prompt blocks in [PROMPTS.md](./PROMPTS.md)
- [ ] `SUBAGENTS.md` — Task vs explore decision tree
- [ ] `DOGFOOD_INDEX.md` — one row per program PR
- [ ] RC-API: fetch Revy run JSON for agent babysit without paste
