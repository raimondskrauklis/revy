# docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_POST_WAVE_C_D1_EXECUTION.md

# D1 — FR-CS4 staging dogfood (execution)

Phase **D1** of [FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md](../FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md). Baseline: [backlog findings](../FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md) § FR-CS4. **D1 authority:** [D1 findings](../FINDING_RESOLUTION_POST_WAVE_C_D1_FINDINGS.md) · [D1 general plan](../FINDING_RESOLUTION_POST_WAVE_C_D1_GENERAL_PLAN.md). **D1 only.**

**Goal:** Structural in-file fix **without** line-region overlap → group closes via Pass 3 verification judge (FR-CS4 PASS).

## Decisions locked for D1

- **Branch:** `chore/fr-cs4-structural-fix-staging` — separate from M0/D0 product PRs.
- **Probe protocol:** review-visible defect on anchored lines; push 2 fixes elsewhere in same file (delete/move snippet) — **not** file deletion (hygiene path).
- **Pass 3 fingerprint rule:** push 2 must **not** re-report the probe finding (`gen=0` for probe fingerprint on push 2). If Moonshot re-reports the same finding on push 2, Pass 3 excludes it (`fingerprints_in_run` — `github_finding_closure.py:133–134`, `:309–311`) and D1 **FAIL**.
- **Primary metric:** per-group `state` + `resolution_method` + verification judge outcome row — not `pr_active_count` alone (VAL8).
- **Deploy boundary:** post–D0 deploy ISO in staging memo.
- **Staging prerequisite:** `judge_llm_enabled()` true on staging workers — Pass 3 is a no-op when false (`github_finding_closure.py:276–277`).

## Pre-flight gate (operator — before D1.1)

On staging **`revy-worker`** (after D0 deploy):

```bash
docker exec revy-worker python -c "
from app.core.config import settings
print('judge_llm_enabled:', settings.judge_llm_enabled())
print('effective_judge_provider:', settings.effective_judge_provider)
"
```

**PASS:** `judge_llm_enabled: True` (anthropic direct or gateway, or bedrock with judge model). **FAIL:** `False` — fix judge env before any dogfood push.

## Out of scope for D1

- MR-DG1 → **M0**
- FR-CS8 → **D2**
- Program doc edits in pushes 1–2 (backend only)
- Gap registry close → **D3** (D1 delivers staging memo sign-off only)

---

## D1.0 — Staging memo stub

**What:** Add **Wave D — FR-CS4** table to [staging validation memo](../../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md): deploy ISO, push rows, group id placeholders.

**Files:** `docs/review-pipeline/finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:** Table exists with post–D0 `--since` ISO row (not TBD).

---

## D1.1 — Introduce structural probe (push 1)

**What:** Fixture module with defect on specific lines (Moonshot-visible); unit test imports fixture. After Revy publish on push 1: record group + revision ids **and** finding `start_line`/`end_line` in staging memo.

**Files:** `backend/tests/fixtures/fr_cs4_probe/` (new), `backend/tests/unit/test_fr_cs4_probe.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_fr_cs4_probe.py -q
```

**Operator (same subphase):** staging memo push-1 row with `head_sha`, `group_id`, `last_seen_revision_id`, `review_run_id`, finding `start_line`/`end_line`, probe `fingerprint`.

**Push 1 retry (if 0 publishable findings):** do **not** proceed to D1.2. Record attempt in [staging memo](../../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) Wave D; follow options **D1-O1** (revise defect class) + **D1-O7** (DB check). Reject kwargs-only / no-code retry — see D1 findings **D1-Q7**.

---

## D1.2 — Structural fix without line touch (push 2)

**What:** Remove/refactor offending code **outside** finding line region (same file). Fix must leave probe group `still_open` with fingerprint **absent** from push-2 review run (`gen=0` for probe finding). Wait for Revy publish.

**Files:** probe fixture only (backend)

**Deliverable:** Memo row with `head_sha`, `group_id`, `last_seen_revision_id`; evidence push-2 diff avoids anchored hunk; push-2 `gen=0` for probe fingerprint.

---

## D1.3 — Sign-off inspection

**What:** After publish on push 2: DB query group `state`, `resolution_method`, `resolution_status`; **`github_finding_judge_outcomes`** row for probe `group_id` with `judge_purpose=verification`; Revy resolution metrics block. Optional metrics:

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since <D0_deploy_iso> --json'
```

**Files:** staging memo rows only (operator)

**Deliverable:** FR-CS4 staging **PASS** (memo sign-off) or documented blocker with group-level evidence. Gap registry close → **D3**.

---

**Phase gate** (operator + DB):

| Check | Pass |
|-------|------|
| Pre-flight `judge_llm_enabled()` on `revy-worker` | required |
| Push 1 ≥1 active group on probe path | required |
| Push 1 memo: `group_id`, lines, `fingerprint` captured | required |
| Push 2 fix does not overlap finding line region | required |
| Push 2 probe fingerprint **not** in current run (`gen=0`) | required |
| Group `state=resolved` + `resolution_method=verification_dismissed` | required |
| `github_finding_judge_outcomes` row: `judge_purpose=verification` for probe `group_id` | required |

**Human gate:** LOOP stops after D1.3 until memo signed PASS.

**Next:** [`FINDING_RESOLUTION_POST_WAVE_C_D2_EXECUTION.md`](./FINDING_RESOLUTION_POST_WAVE_C_D2_EXECUTION.md) (optional) or [`FINDING_RESOLUTION_POST_WAVE_C_D3_EXECUTION.md`](./FINDING_RESOLUTION_POST_WAVE_C_D3_EXECUTION.md)
