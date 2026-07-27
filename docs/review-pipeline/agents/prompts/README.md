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

See RC-D14 in [DOGFOOD_PR50 § RQ4 pass 2](../../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#rq4-bugbot-pass-2--closure-vs-thinking-trace-rc-d14). RC-D16: pass 1 also requires Deferred when empty — [§](../../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#greptile-babysit-vs-bugbot-depth-rc-d16).

---

## Greptile babysit (shallow fix + Bugbot deep gate)

**Skill:** [babysit-pr](../../../.cursor/skills/babysit-pr/SKILL.md) · **Evidence:** RC-D16 in [DOGFOOD](../../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#greptile-babysit-vs-bugbot-depth-rc-d16)

Greptile and Bugbot are **different axes** on the same PR. Babysit fixes listed threads only; Bugbot adversarially traces failure modes. **Never skip Bugbot** because Greptile already ran.

```text
1. Fetch open greptile-apps threads → fix valid P1/P2 vs locked Q#
2. pytest + ruff (if backend touched)
3. Local Bugbot — paste pre-feed + OUTPUT_FORMAT Pass 1 (see below)
4. commit → push (operator may hold push for manual thought review)
```

**Babysit agent (parent) — stay shallow:**

```text
Scope: open Greptile threads only. Verify fix vs FINDINGS/EXECUTION locks.
Do NOT deep-review — that is Bugbot's job.
```

**Pre-Bugbot Custom Instructions (paste before OUTPUT_FORMAT Pass 1):**

```text
Context: Greptile babysit fixes on PR #50.
Locked: D10-M one-shot supersede in migration 0026 (no fingerprint backfill).
Ignore unless diff worsens: pre-existing Celery duplicate delivery, missing unique on
  pipeline_runs.index_job_id, narrow deploy reconcile→publish window, draft-PR G10 parking (RQ7).
```

Then append [OUTPUT_FORMAT.md](./OUTPUT_FORMAT.md) Pass 1 block (Deferred required even when findings empty).

---

## Files

| File | Use when |
|------|----------|
| [TWO_AGENTS.md](./TWO_AGENTS.md) | Onboarding; why implementer misses what reviewer catches |
| [OUTPUT_FORMAT.md](./OUTPUT_FORMAT.md) | Every Bugbot invoke — paste tail into Custom Instructions |
| [PHASES.md](./PHASES.md) | Per-RQ Custom Instructions body |
| [PROMPTS.md](../PROMPTS.md) | Full subagent shell (path, Diff, + PHASES + OUTPUT_FORMAT) |

**Evidence:** [chain_of_thoughts/](../chain_of_thoughts/) — commit when a run teaches something (e.g. `local_bugbot_from_ui_1.txt`).
