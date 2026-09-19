# Agent prompts (copy-paste)

**Index:** [agents/README.md](./README.md) · **Distilled prompts:** [prompts/README.md](./prompts/README.md) · **LOOP:** [ORCHESTRATION.md](./ORCHESTRATION.md)

Per-RQ Custom Instructions live in **[prompts/PHASES.md](./prompts/PHASES.md)**.  
Response shape: **[prompts/OUTPUT_FORMAT.md](./prompts/OUTPUT_FORMAT.md)** — context over format; master synthesizes from thinking.

---

## Subagent brief (master compiles — keep short)

Smart reviewer needs **verb + scope + one hook**, not volume.

```text
Full Repository Path: /Users/raimonds.krauklis/projects/revy
Diff: uncommitted changes

Custom Instructions:
VERB: FIND | VALIDATE | CLOSE
SCOPE: <files>
VALIDATE: <fn → failure path>   # VALIDATE only — stops wrong-mechanism fixes
OUT OF SCOPE: <one line>
Any output format fine — master reads thinking if answer thin (RC-D23)
<PHASES § RQn — FIND only>
<revybot verbatim — VALIDATE only>
<OUTPUT_FORMAT pass block>
```

**VALIDATE** must name a failure path to trace — not "protect diagnostics."  
Roles: [prompts/ROLES.md](./prompts/ROLES.md).

---

## phase-execution invoke

```text
@docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md /phase-execution
```

Migration pause: stop after RQ0 until staging `alembic upgrade head`.

---

## babysit-revy-pr

```text
/babysit-revy-pr
```

Revy is post-push. Poll until idle → fix revybot comments → **VALIDATE** → **CLOSE** until clean → push. **Do not** run `/babysit-pr` (Greptile is off). Authoritative flow: [babysit-revy-pr skill](../../../.cursor/skills/babysit-revy-pr/SKILL.md).

---

## Generic parent reminders

```text
- Implementer ≠ reviewer — same model, different task (prompts/TWO_AGENTS.md).
- Babysit: VALIDATE → fix → CLOSE; re-CLOSE until clean → push.
- Phase LOOP: FIND → fix → CLOSE; re-CLOSE until clean → push.
- Read only current RQ execution section.
- Update `.cursor/BUGBOT.md` when starting a **new** program slice
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
