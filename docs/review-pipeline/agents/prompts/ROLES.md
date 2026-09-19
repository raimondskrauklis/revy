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
| **Revy** (GitHub) | no | Post-push product review |

**Master's main job:** don't let work **run** (push/ship) until pytest, ruff, Bugbot pass. Corner-cutting starts when gates are skipped.

**Reviewer is specialized, not narrow.** Same model; different task. Must trace code and challenge proposals — including a thin Revy comment's minimum fix.

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
| **FIND** | "What did I break in this slice?" | Open hunt — unknown unknowns | Master read thinking; bugs fixed or deferred with reason |
| **VALIDATE** | "Is this Revy fix actually correct?" | Closed proof — one claim to break | Mechanism traced; master confirms from thinking + answer |
| **CLOSE** | "Is pass 1 fixed?" | Checklist — accountability | CLOSED/STILL OPEN evident in reasoning; net-new only |

**Output format:** Accept whatever the subagent returns (XML, one line, prose). **Do not fight platform shape** — context in thinking export is the gate input ([OUTPUT_FORMAT § context over format](./OUTPUT_FORMAT.md)).

**Babysit pass 1 must be VALIDATE, not FIND.** FIND on a babysit diff wanders (random P2s) or rubber-stamps the wrong mechanism. VALIDATE needs the named path in the brief — that's the precise context. Do not babysit Greptile.

### Two Bugbot runtimes (RC-D23)

| Channel | Role | Tune how far? |
|---------|------|-------------|
| **Hosted GitHub Bugbot** | Post-push on PR | `.cursor/BUGBOT.md` on **`main`** — **appended** to Cursor default ([forum](https://forum.cursor.com/t/does-bugbot-md-override-cursor-s-default-base-prompt/150078)); team dashboard rules override repo; `@cursor remember` on PR |
| **Local Task subagent** | Pre-push gate; master orchestrates | `VERB` + failure path + contract § in brief; **accept XML / any shape** — master reads thinking export ([bugbot_1](../chain_of_thoughts/cursor_bugbot_1.txt)) |

**Internal reviewer:** Task `bugbot` + good brief + **master synthesis from thinking** is the job. No need to force table OUTPUT_FORMAT on the subagent. **Product:** Revy verifier on customer repos ([RC-D7](../../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md)).

Subagent brief: ~6 lines + OUTPUT_FORMAT tail. No chat history. See [PROMPTS.md](../PROMPTS.md).
