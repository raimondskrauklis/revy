# Distilled prompts — agent review & implementation

**Parent:** [agents/README.md](../README.md) · **LOOP:** [ORCHESTRATION.md](../ORCHESTRATION.md) · **Copy-paste shells:** [PROMPTS.md](../PROMPTS.md)

Thin routers for **smart agents with good context**. Verbose prompts are not the product — **contract docs + phase scope + output shape** are.

---

## Why a separate folder

| Problem | Fix |
|---------|-----|
| Same model, two jobs (ship code vs find bugs) | [TWO_AGENTS.md](./TWO_AGENTS.md) — different task → different reasoning |
| Bugbot “thought 3 bugs, reported 0” | [OUTPUT_FORMAT.md](./OUTPUT_FORMAT.md) — pass 2 must emit **closed** + **deferred** tables |
| Re-pasting long Custom Instructions every gate | [PHASES.md](./PHASES.md) — one distilled block per RQn |
| Thinking trace is gold, final line is not | [chain_of_thoughts/](../chain_of_thoughts/) — archive UI exports; distill rows in [DOGFOOD](../../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md) |

**Wiring (unchanged):** `.cursor/BUGBOT.md` → active phase + links to EXECUTION/FINDINGS. Greptile → `.greptile/files.json`. This folder is **how to invoke and what to ask for**, not the locked contract.

---

## Stack (what the agent actually reads)

```text
  .cursor/BUGBOT.md          ← 8–12 lines: active RQ + file hints
        │
        ├── waves/REVIEW_QUALITY_EXECUTION.md § RQn   ← scope, routes, gates
        ├── review-quality/REVIEW_QUALITY_FINDINGS.md ← locked Q#
        │
        └── agents/prompts/
              ├── OUTPUT_FORMAT.md   ← pass 1 vs pass 2 response
              └── PHASES.md          ← Custom Instructions distill
```

**Implementer (Composer):** reads EXECUTION § RQn, writes code, runs pytest/ruff.  
**Reviewer (Bugbot subagent):** same repo + **diff** + BUGBOT.md + OUTPUT_FORMAT + PHASES § RQn.

---

## Gate sequence (prompt role)

```text
Pass 1 — FIND     Custom Instructions: PHASES § RQn + “report all actionable bugs”
Fix blockers
Pass 2 — CLOSE    “Verify pass 1 closed; NEW bugs only; REQUIRED deferred table”
Fix blockers (if any)
Pass 3+ — repeat until clean
commit → push → Greptile (post-push, different axis)
```

See RC-D14 in [DOGFOOD_PR50 § RQ4 pass 2](../../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#rq4-bugbot-pass-2--closure-vs-thinking-trace-rc-d14).

---

## Files

| File | Use when |
|------|----------|
| [TWO_AGENTS.md](./TWO_AGENTS.md) | Onboarding; why implementer misses what reviewer catches |
| [OUTPUT_FORMAT.md](./OUTPUT_FORMAT.md) | Every Bugbot invoke — paste tail into Custom Instructions |
| [PHASES.md](./PHASES.md) | Per-RQ Custom Instructions body |
| [PROMPTS.md](../PROMPTS.md) | Full subagent shell (path, Diff, + PHASES + OUTPUT_FORMAT) |

**Evidence:** [chain_of_thoughts/](../chain_of_thoughts/) — commit when a run teaches something (e.g. `local_bugbot_from_ui_1.txt`).
