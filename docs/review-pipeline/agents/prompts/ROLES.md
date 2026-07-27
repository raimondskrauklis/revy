# Roles — human, master, reviewer

**Index:** [prompts/README.md](./README.md)

```text
Human    → judgment, pause, ship calls
Master   → only agent you talk to; gates before run; compile briefs; synthesize back
Reviewer → specialized subagent; smart + adversarial; no human I/O
```

| Role | Talks to human | Owns |
|------|----------------|------|
| **Human** | — | Product calls, skip, when to push |
| **Master** | yes | Memory, triage, implement, **block push until gates green**, brief reviewer |
| **Reviewer** | no | One verb on one diff — reason, don't rubber-stamp |
| **Greptile** (GitHub) | no | Post-push contract FIND |

**Master's main job:** don't let work **run** (push/ship) until pytest, ruff, Bugbot pass. Corner-cutting starts when gates are skipped.

**Reviewer is specialized, not narrow.** Same model; different task. Must trace code and challenge proposals — including Greptile's minimum fix (RC-D17).

**Reviewer verbs**

| Verb | When | Key line in brief |
|------|------|-------------------|
| **FIND** | Phase gate | SCOPE + PHASES § RQn |
| **VALIDATE** | Babysit pass 1 | `VALIDATE: <fn → failure path>` — anti-anchors on wrong mechanism |
| **CLOSE** | Pass 2+ | Prior finding titles |

### What you should expect (human)

Same tool (Bugbot), **different question** — until VERB is set, outcomes feel random.

| Verb | You are asking | Feels like | Success looks like |
|------|----------------|------------|-------------------|
| **FIND** | "What did I break in this slice?" | Open hunt — unknown unknowns | Findings + Deferred |
| **VALIDATE** | "Is Greptile's fix actually correct?" | Closed proof — one claim to break | Blocked or confirmed + Deferred if empty |
| **CLOSE** | "Is pass 1 fixed?" | Checklist — accountability | CLOSED + net-new + Deferred |

**Babysit pass 1 must be VALIDATE, not FIND.** FIND on a babysit diff wanders (random P2s) or rubber-stamps Greptile's wrong mechanism (flush case). VALIDATE needs the named path in the brief — that's the precise context.

Subagent brief: ~6 lines + OUTPUT_FORMAT tail. No chat history. See [PROMPTS.md](../PROMPTS.md).
