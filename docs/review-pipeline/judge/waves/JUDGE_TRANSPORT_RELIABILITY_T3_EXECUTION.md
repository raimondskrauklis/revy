# docs/review-pipeline/judge/waves/JUDGE_TRANSPORT_RELIABILITY_T3_EXECUTION.md

# T3 — Staging verification & ops gate (execution)

Phase **T3** of [JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md](../JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md). Baseline: [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](../JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md) § Experiment / verification. **T3 only — final phase.**

**Goal:** Staging PASS for judge transport after T1+T2 — observable logs, fallback behavior, metrics improvement vs T0 baseline.

## Decisions locked for T3

- Full gate requires RTU up for gateway path; **partial PASS** documented if RTU still down (direct fallback + smoke `--compare-direct` only).
- JT-Q5 (`REVY_JUDGE_STRUCTURED_OUTPUT`) enabled only if post-deploy metrics show parse failures — default **leave off**.
- FR-CS4 / Pass 3 supersede — not validated in this phase.
- No `changelog.json` — backend-only; no user-facing product change.

## Out of scope for T3

- FR-CS4 product fix
- Prometheus counters
- Manifest CLI export tool

---

## T3.1 — Smoke script gate

**What:** Run `test_anthropic_judge_gateway --compare-direct --print-raw` on staging worker or operator laptop with staging `.env`. Record gateway vs direct results in validation memo.

**Files:** `docs/review-pipeline/judge/JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md`

**Deliverable:**

```bash
cd backend && pipenv run python -m scripts.test_anthropic_judge_gateway --compare-direct --print-raw
```

Memo § Smoke matrix filled (gateway / direct / structured=n/a).

---

## T3.2 — Post-deploy metrics

**What:** Re-run `judge_json_contract_staging_metrics` with same `--since` as T0; compare `all_failed`, `skipped_unavailable` to baseline.

**Files:** `docs/review-pipeline/judge/JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md`

**Deliverable:**

```bash
cd backend && DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics --since 2026-07-30T08:28:45Z --json
```

Same `--since` as T0.2 (post–#71 D0 deploy `2026-07-30T08:28:45Z`).

Memo § After deploy table — trend documented (improved / flat / N/A).

---

## T3.3 — Live review + worker log check

**What:** Trigger staging PR review with ≥1 judge-eligible finding (or use existing open PR). Confirm worker tail shows `judge_llm_request_completed` with `profile` + `outcome` OR successful publish with outcome row.

**Files:** Validation memo only

**Deliverable:** Memo § Live run — `head_sha`, `review_run_id`, log snippet (redacted), `judge_status`, outcome count.

**Human gate:** Operator runs review on staging; LOOP stops until memo signed PASS or documented FAIL.

---

## T3.4 — Doc sync

**What:** Update program docs; close JT gaps in findings where verified.

**Files:** See table below

**Deliverable:**

| Doc | Change |
|-----|--------|
| [waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md](./JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md) | T0–T3 Status Done + commit shas |
| [../README.md](../README.md) | Program status line for transport reliability |
| [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](../JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md) | JT-1–JT-4 status column if gaps closed |
| [JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md](../JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md) | Sign-off PASS/FAIL |
| [JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md](../JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md) | Optional one-line status in header |

Optional ops note in validation memo: `LOG_FORMAT=json` on worker for richer `extra` fields.

```bash
rg 'JUDGE_TRANSPORT' docs/review-pipeline/judge/ --files-with-matches | wc -l
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_anthropic_review.py tests/unit/test_github_finding_judge.py -q
```

**Human gate:** T3.3 staging sign-off required for program PASS.

**Next:** none — optional `post-finish-gap-pass` before merge.
