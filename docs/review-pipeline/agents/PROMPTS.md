# Agent prompts (copy-paste)

**Index:** [agents/README.md](./README.md) · **Distilled prompts:** [prompts/README.md](./prompts/README.md) · **LOOP:** [ORCHESTRATION.md](./ORCHESTRATION.md)

Per-RQ Custom Instructions live in **[prompts/PHASES.md](./prompts/PHASES.md)**.  
Response shape (pass 1 vs pass 2 + **Deferred** table): **[prompts/OUTPUT_FORMAT.md](./prompts/OUTPUT_FORMAT.md)**.

---

## Local Bugbot — template

```text
Full Repository Path: /Users/raimonds.krauklis/projects/revy
Diff: uncommitted changes
Change Description:
  <5–10 bullets on what changed — optional but helps pass 2>

Custom Instructions:
  <paste PHASES.md § RQn block>
  <paste OUTPUT_FORMAT.md Pass 1 or Pass 2 block>
```

**Pass 1:** after implement, before first commit on slice.  
**Pass 2+:** after fixes; must include Deferred table even if clean (RC-D14).

---

## phase-execution invoke

```text
@docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md /phase-execution
```

Migration pause: stop after RQ0 until staging `alembic upgrade head`.

---

## babysit-pr

```text
/babysit-pr 50
```

Greptile is post-push. Re-run **Pass 1** Bugbot on fixes before push.

---

## Generic parent reminders

```text
- Implementer ≠ reviewer — same model, different task (prompts/TWO_AGENTS.md).
- Local Bugbot Pass 1 → fix → Pass 2 (with Deferred table) → push.
- Read only current RQ execution section.
- Update .cursor/BUGBOT.md active phase line each RQ.
```

Legacy per-phase blocks below are **superseded by prompts/PHASES.md** — kept for grep only.

---

## Review quality — RQ0 (schema)

See [prompts/PHASES.md § RQ0](./prompts/PHASES.md#rq0--schema).

---

## Review quality — RQ1 (diff + compare)

See [prompts/PHASES.md § RQ1](./prompts/PHASES.md#rq1--diff--compare).

---

## Review quality — RQ7 (Greptile publish)

See [prompts/PHASES.md § RQ7](./prompts/PHASES.md#rq7--greptile-publish).
