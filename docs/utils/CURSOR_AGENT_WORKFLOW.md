# Cursor agent workflow — quick ref

**Status:** review-quality merged to `main` (PR #50). **RQ9** hardening on `docs/agent-work`. Human gate: staging `0026` + AS2 → tag `review-quality-v1`.

Short map of how we work with agents in this repo. Detail: [agents/README.md](../review-pipeline/agents/README.md).

---

## Point the agent here first

| Who | File |
|-----|------|
| Any new chat | [AGENTS.md](../../AGENTS.md) |
| Master — LOOP / review-pipeline | [agents/README.md](../review-pipeline/agents/README.md) |
| Bugbot subagent (pre-push) | [.cursor/BUGBOT.md](../../.cursor/BUGBOT.md) |
| Roles + verbs | [agents/prompts/ROLES.md](../review-pipeline/agents/prompts/ROLES.md) |

---

## Three roles

```text
Human    → judgment, pause, when to push
Master   → only agent you talk to; memory, implement, gate before run, compile briefs
Reviewer → Bugbot subagent; one task per spawn; no human chat
```

Greptile (GitHub) = post-push contract reviewer; feeds babysit, not your chat.

---

## Two tracks (same Bugbot, different verb)

| Track | When | Verb | Your question |
|-------|------|------|---------------|
| **Phase LOOP** | RQ slice done | FIND → CLOSE | What did I break? |
| **Babysit** | Greptile thread fixed | VALIDATE → CLOSE | Is Greptile's fix real? |
| **Doc sync** | Agent docs changed | FIND | Do our docs contradict? |

Master must set **VERB** in the brief — agent won't infer the track.

---

## Subagent brief (~6 lines)

```text
VERB: FIND | VALIDATE | CLOSE
SCOPE: <files>
VALIDATE: <fn → failure path>   # babysit only — stops wrong-mechanism fixes
OUT OF SCOPE: <one line>
OUTPUT: Findings + Deferred + Scope note (always) — see OUTPUT_FORMAT.md
<OUTPUT_FORMAT tail from agents/prompts/OUTPUT_FORMAT.md>
```

No chat history. Smart reviewer needs **verb + scope + one hook**, not volume.

Shell: [agents/PROMPTS.md](../review-pipeline/agents/PROMPTS.md)

---

## Gate before run

```text
implement → pytest → ruff → LOCAL BUGBOT → commit → push
                              │
                    babysit: VALIDATE → fix → CLOSE (until clean)
```

**Do not push** with open Bugbot blockers. Skipping the gate is when corners get cut.

Skills: `phase-execution` · `ship-changes` · `babysit-pr`

---

## Greptile + Bugbot (different jobs)

| | Greptile | Local Bugbot |
|--|----------|--------------|
| When | After push | Before push |
| Job | Contract / symptom | Prove mechanism / break diff |
| Babysit | Says *where* | VALIDATE says *does the fix work* |

Greptile minimum fix ≠ production fix (RC-D17). Always VALIDATE with a named failure path.

**Greptile 👀** on PR open = queued ack (RC-D20), not “read your summary.” Log first comment in [DOGFOOD § PR #51](../review-pipeline/review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#dogfood-pr-51--docsagent-work-rq9) — did it cite execution § RQn?

**Bugbot gate:** `VERB` + trace quality in thinking export — **not** subagent table shape (RC-D23). Master synthesizes for human; accept XML / one-line answers.

**Two runtimes (RC-D23):** Hosted GitHub Bugbot vs local Task subagent — different channels; same rule: **context over format**.

---

## Priority now vs later

| Now | Later (Revy product) |
|-----|----------------------|
| Cursor ops — master + Bugbot + Greptile parallel | Distill patterns into Revy |
| Fix schema/ops while diff is small | Customer pipeline without Cursor parent |
| Keep agent docs in sync — agents read them | **G-UX+** ack affordances (👀 parity) — post-v1 |

---

## Evidence

Dogfood rows: [DOGFOOD_PR50](../review-pipeline/review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md)  
Raw Bugbot thinking: [agents/chain_of_thoughts/](../review-pipeline/agents/chain_of_thoughts/)
