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
If findings are empty after deep review: REQUIRED "Deferred" table (same columns as pass 2).
Do not answer only "no bugs" without Findings (or empty) + Deferred tables.
```

**VALIDATE** (babysit pass 1):

```text
PASS: 1 (validate)
Prove Greptile's proposed fix — trace the VALIDATE path; read/grep as needed.
Challenge the mechanism; do not rubber-stamp the thread.
Format findings: severity · file:line · title · why (same as FIND).
Deferred table required if findings empty; do not answer only "confirmed" without Findings/Deferred.
```

**Expected sections (FIND):**

1. **Findings** — table or bullets (empty allowed if truly none)
2. **Deferred** — **required when findings empty** — hypotheses considered but not filed (RC-D16)
3. **Scope note** — one line: which EXECUTION § RQn reviewed

**Expected sections (VALIDATE):** Findings + Deferred; scope note = Greptile thread + VALIDATE path (no RQn).

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
| **Deferred** | **Required** even when new findings empty — captures “talked itself out” items worth human scan |

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
