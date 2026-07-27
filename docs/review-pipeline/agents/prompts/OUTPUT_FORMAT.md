# Bugbot output format (distilled)

**Index:** [prompts/README.md](./README.md) · Paste the **Pass** section below into Custom Instructions.

Smart reviewer + good context needs **shape**, not length. Prevents “199 lines of thinking → 1 line clean” without audit trail (RC-D14).

---

## Pass 1 — FIND

Append to Custom Instructions:

```text
PASS: 1 (find)
Report ALL actionable bugs introduced by the diff.
Format each: severity (high|medium|low) · file:line · one-line title · 2–3 sentence why.
Cite locked FINDINGS/EXECUTION IDs when applicable (e.g. G10, C1, O2).
Do not report pre-existing issues outside the diff unless the diff worsens them.
```

**Expected sections:**

1. **Findings** — table or bullets (may be empty only if diff is trivially safe)
2. **Scope note** — one line: which EXECUTION § RQn reviewed

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

## Example deferred row (from RQ4 pass 2)

| Sev | Topic | Why deferred |
|-----|-------|----------------|
| low | Draft PR leaves G10 check `in_progress` | Pre-existing; needs `neutral` finalize (RQ7/G10 parking) |
| — | — | Fixed in follow-up commit: embed fail partial commit; review enqueue G10 |

---

## Subagent shell (parent copies from PROMPTS.md)

```text
Full Repository Path: /Users/…/revy
Diff: uncommitted changes | branch changes
Change Description: <optional 5–10 bullets>
Custom Instructions:
  <PHASES.md § RQn block>
  <OUTPUT_FORMAT Pass 1 or Pass 2 block>
```

---

## When to archive thinking

If **Deferred** contains a row that later becomes a fix or RC-D# learning → export UI thinking to `chain_of_thoughts/` and link from [DOGFOOD](../../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md). Thin exports (`cursor_bugbot_rq4_pass_6.md`) are insufficient alone.
