# Finding resolution dogfood P1.5 — Post-merge dogfood continuation (execution)

Phase **P1.5** of [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md). Baseline: [FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md](../FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md) FR-DG-VAL1–VAL4. **P1.5 only.**

**Goal:** Resume staging dogfood after #64 merge + deploy; wire probe (push 2a), then fix push (push 2b) for FR-DG1 sign-off.

## Decisions locked for P1.5

- **#64 merged wave A** — P1+P2 code live on staging after deploy `2026-07-29T17:50:43Z`; dogfood continues on **new open** chore PR ([FR-DG-VAL1](../FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md#fr-dg-val1--wave-a-merged-in-one-pr-64)).
- **FR-DG1 needs rev ≥ 2** on open dogfood PR — wire-only rev 1 does not sign off FR-DG1 ([FR-DG-VAL2](../FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md#fr-dg-val2--fr-dg1-requires-rev--2-on-open-dogfood-pr)).
- **Push 2a:** wire `FR_DOGFOOD_PROBE_MARKER` in `probe_module.py` (single commit); wait Revy.
- **Push 2b:** minimal fix addressing active finding from 2a; FR-DG1 PASS criteria apply on **this** publish.
- **Push 3 (P2.4):** separate commit removing probe — FR-DG2; not combined with 2b.
- **One push per agent cycle** — human gate between 2a and 2b.

## Out of scope for P1.5

- FR-DG2 sign-off → push 3 after 2b complete
- MR-DG1 → P4
- Program P3 final sign-off tables → after push 3

---

## P1.5.1 — Record deploy boundary + push 1 row

**What:** Update [FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md](../FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) with deploy ISO, #64 merge, push-1 PASS row ([FR-DG-VAL3](../FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md)).

**Files:** `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md`, `FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md`

**Deliverable:** Memo deploy row `2026-07-29T17:50:43Z`; push-1 `5bb55ea` PASS.

---

## P1.5.2 — Open chore PR + push 2a (wire probe)

**What:** Branch `chore/finding-resolution-staging-dogfood` from `main`; wire marker in `fr_dogfood_probe_value()`; update unit test; open PR; **wait for Revy**.

**Files:** `backend/tests/fixtures/fr_dogfood/probe_module.py`, `backend/tests/unit/test_fr_dogfood_probe.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_fr_dogfood_probe.py -q
```

**Human gate:** Revy publish `completed` on push 2a before P1.5.3.

---

## P1.5.3 — Push 2b fix (FR-DG1 sign-off)

**What:** Single commit fixing active finding from 2a (touch flagged region); push; wait Revy; fill FR-DG1 pass table.

**Pass criteria:** `denominator_active_prior` ≥ 1; `transitions_addressed` ≥ 1; G9 not `n/a`; `summary_json.resolution.addressed` ≥ 1.

**Files:** staging memo FR-DG1 table, `probe_module.py` (or flagged file)

**Deliverable:** Memo FR-DG1 row PASS or FAIL with evidence.

**Human gate:** Agent complete before push 3 (FR-DG2).

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_fr_dogfood_probe.py tests/unit/test_github_resolution_metrics.py tests/unit/test_github_publish_formatter.py -q
```

**Next:** [FINDING_RESOLUTION_DOGFOOD_P2_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P2_EXECUTION.md) § P2.4 (push 3)
