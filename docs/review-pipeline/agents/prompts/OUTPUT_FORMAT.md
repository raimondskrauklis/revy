# Bugbot output format (distilled)

**Index:** [prompts/README.md](./README.md) · Paste the **Pass** section below into Custom Instructions.

Smart reviewer + good context needs **shape**, not length. Prevents “199 lines of thinking → 1 line clean” without audit trail (RC-D14).

---

## Pass 1 — FIND or VALIDATE

Append to Custom Instructions.

**FIND** (phase gate):

```text
PASS: 1 (find)
Report ALL actionable bugs introduced by the diff.
Format each: severity (high|medium|low) · file:line · one-line title · 2–3 sentence why.
Cite locked FINDINGS/EXECUTION IDs when applicable (e.g. G10, C1, O2).
Do not report pre-existing issues outside the diff unless the diff worsens them.
REQUIRED output (always): Findings table + Deferred table + Scope note (§ RQn).
Use markdown tables; if platform XML conflicts, put tables in Description/details.
Deferred required even when findings non-empty — log hypotheses considered but not filed (RC-D16, RC-D19).
Do not answer only "no bugs" without Findings + Deferred + Scope note.
```

**VALIDATE** (babysit pass 1):

```text
PASS: 1 (validate)
Prove Greptile's proposed fix — trace the VALIDATE path; read/grep as needed.
Challenge the mechanism; do not rubber-stamp the thread.
Format findings: severity · file:line · title · why (same as FIND).
REQUIRED output (always): Findings table + Deferred table + Scope note (Greptile thread + VALIDATE path).
Use markdown tables; if platform XML conflicts, put tables in Description/details.
Do not answer only "confirmed" without Findings + Deferred + Scope note.
```

**Expected sections (FIND):**

1. **Findings** — table or bullets (empty allowed if truly none)
2. **Deferred** — **always required** — hypotheses considered but not filed (RC-D16); not only when findings empty
3. **Scope note** — one line: which EXECUTION § RQn reviewed

**Platform note (RC-D19):** Cursor Bugbot may prefer system XML over your table request. Still emit Findings + Deferred + Scope note — master reads UI thinking export when Deferred is missing ([ui_7](../chain_of_thoughts/cursor_bugbot_form_ui_7.txt)).

**Expected sections (VALIDATE):** Findings + Deferred (always) + scope note = Greptile thread + VALIDATE path.

---

## Pass 2+ — CLOSE

Append to Custom Instructions:

```text
PASS: 2 (closure)
Prior pass 1 findings (list IDs/titles from handoff).
Verify each is fixed in the current diff — mark CLOSED or STILL OPEN.
Report NEW actionable bugs only (not re-listed pass 1 items unless STILL OPEN).
REQUIRED: "Deferred" table — issues considered in review but NOT filed as bugs:
  columns: severity · topic · why deferred (pre-existing | out of scope | parking | needs product decision)
Do not answer only "no bugs" without Closed + Deferred tables.
```

**Expected sections:**

| Section | Required |
|---------|----------|
| **Pass 1 closure** | Each item → CLOSED or STILL OPEN + evidence |
| **New findings** | Only net-new bugs (empty allowed if truly none) |
| **Deferred** | **Always required** — even when new findings empty — captures “talked itself out” items worth human scan |

---

## Greptile + PR body (RC2-lite)

Greptile **👀** on PR open = queued ack, not comprehension. Wired `.greptile/files.json` + diff matter more than PR prose — but a short body helps scope:

```markdown
## Scope
RQ9 — <one line>

## Mechanism
<failure path or locked decision, e.g. draft-after-index not draft-autostart>

## Contract
REVIEW_QUALITY_EXECUTION.md § RQn

## Test plan
- [ ] …

## Out of scope
…
```

**After push:** log Greptile first comment in [DOGFOOD § PR #51](../../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#dogfood-pr-51--docsagent-work-rq9) — did it cite execution § RQn or only diff?

---

## Example deferred rows

### RQ4 pass 2 (closure)

| Sev | Topic | Why deferred |
|-----|-------|----------------|
| low | Draft PR leaves G10 check `in_progress` | Pre-existing; needs `neutral` finalize (RQ7/G10 parking) |
| — | — | Fixed in follow-up commit: embed fail partial commit; review enqueue G10 |

### Greptile babysit pass (RC-D16 — pass 1, findings empty)

Source: [local_bugbot_from_ui_2](../chain_of_thoughts/local_bugbot_from_ui_2) · commit `71e4911`.

| Sev | Topic | Why deferred |
|-----|-------|--------------|
| low | Worker dies after TX1, before TX2 | Celery redelivery; not introduced by split |
| medium | Migration supersede → publish before reconcile → green check | One-shot deploy; D10-M accepted |
| low | Duplicate Celery → second GitHub check | Pre-existing race |
| low | Re-dispatch on completed job → orphan check | Pre-existing; split does not worsen |
| low | Draft/closed PR G10 stuck `in_progress` | Parking — RQ7 |
| low | Bulk supersede `UPDATE` table lock | One-shot migration |

---

## Subagent shell (parent copies from PROMPTS.md)

```text
Full Repository Path: /Users/…/revy
Diff: uncommitted changes | branch changes
Custom Instructions:
  VERB: FIND | VALIDATE | CLOSE
  SCOPE: <files>
  VALIDATE: <fn → path>   # VALIDATE only
  OUT OF SCOPE: <one line>
  <PHASES § RQn — FIND only>
  <Greptile verbatim — VALIDATE only>
  <OUTPUT_FORMAT tail>
```

---

## When to archive thinking

If **Deferred** contains a row that later becomes a fix or RC-D# learning → export UI thinking to `chain_of_thoughts/` and link from [DOGFOOD](../../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md). Thin exports (`cursor_bugbot_rq4_pass_6.md`) are insufficient alone.

### Bugbot pass 1 — format compliance (RC-D19)

Source: [cursor_bugbot_form_ui_7.txt](../chain_of_thoughts/cursor_bugbot_form_ui_7.txt) · RQ9 FIND on `docs/agent-work`.

| Sev | Topic | Why deferred / learning |
|-----|-------|-------------------------|
| — | **Output shape** | Rich thinking (~230 lines) but no Deferred table + no Scope note in final output; platform XML won over table request (L165) |
| — | **Master action** | Read thinking export when Deferred missing; pass 2 CLOSE on process compliance |
| — | **Value retained** | Medium finding (draft smoke vs `maybe_enqueue`) still landed — reasoning ≠ handoff |
