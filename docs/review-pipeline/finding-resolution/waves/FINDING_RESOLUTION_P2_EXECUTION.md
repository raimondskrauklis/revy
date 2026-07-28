# Finding resolution P2 — Pass 3 verification judge (execution)

Phase **P2** of [FINDING_RESOLUTION_GENERAL_PLAN.md](../FINDING_RESOLUTION_GENERAL_PLAN.md). **P2 only.**

**Goal:** FR-Q11 escalation groups still `still_open` after Pass 1–2 get verification judge with push-delta evidence — `upheld` → stay open; `dismissed` → `verification_dismissed`.

## Decisions locked for P2

- Escalation set (FR-Q11): `resolution_status=still_open` + `is_judge_candidate` + `last_seen_revision_id == prior_revision` + `closure_blocked_reason != compare_failed`.
- Cap **5** verification calls per review run (`VERIFICATION_JUDGE_MAX_PER_RUN = 5`).
- Runs **after** discovery `record_review_run_judge_status`, **before** `enqueue_publish_for_review_run`.
- Reuse `GitHubJudgeOutcome` (`upheld` / `dismissed`); no `still_valid` enum.
- `judge_purpose=verification` on new outcome rows; discovery rows stay `discovery`.
- Push-delta patches via `fetch_compare_patches(prior.head_sha, new.head_sha)` — not full-PR compare.
- **Prior revision (locked):** load `prior_revision` where `revision_number == current_revision.revision_number - 1` (same query as `apply_resolution_status_for_synchronize` in `github_resolution_metrics.py`).
- Verification prompt: “Original claim from prior revision — still valid on this push delta?” — conservative dismiss.
- `dismissed` → `group.state=resolved`, `resolution_method=verification_dismissed`.
- **Trace split (locked):** P2 writes verification detail on **judge** pipeline step artifact (`verification_judged_count`, candidate `group_ids`, outcomes). **Do not** write `resolution_pass` / FR-Q12 metrics here — **P3.1** owns reconcile-step `resolution_pass`.
- **Module home (locked):** `verify_still_open_escalation_groups`, `VERIFICATION_JUDGE_MAX_PER_RUN`, and verification LLM loop live in **`github_finding_closure.py`**. Discovery judge (`record_review_run_judge_status`, `JUDGE_MAX_PER_RUN`) stays in **`github_finding_judge.py`**.

## Out of scope for P2

- Metrics counting → **P3**
- Non-escalation warnings
- Post-merge batch (FR-Q10)

---

## P2.1 — Verification judge prompt + parser

**What:** `VERIFICATION_JUDGE_SYSTEM_PROMPT` in `anthropic_review.py`; `build_verification_judge_prompt(group, push_delta_patch, evidence)`; reuse `parse_judge_outcome`.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k verification -q
```

---

## P2.2 — `verify_still_open_escalation_groups`

**What:** In `github_finding_closure.py`: load FR-Q11 set for `(pull_request, prior_revision, current_revision)`; resolve `prior_revision` via `revision_number - 1`; run verification LLM loop (cap `VERIFICATION_JUDGE_MAX_PER_RUN = 5`) with push-delta context (`prior_revision.head_sha → current_revision.head_sha`); persist outcomes with `judge_purpose=verification` via `llm_dispatch` + `parse_judge_outcome`.

**Files:** `backend/app/services/github_finding_closure.py`, `backend/app/services/github_compare_patches.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py -k verification -q
```

---

## P2.3 — Wire reconcile worker

**What:** `reconcile_tasks.py` order: `reconcile_review_run` → Pass 2 closure → discovery judge → **Pass 3 verify** → (P3.1: transitions + reconcile trace) → judge trace → publish enqueue. Pass 3 loads `prior_revision` (`revision_number - 1`) before push-delta compare.

**Files:** `backend/app/workers/reconcile_tasks.py`, `backend/tests/unit/test_reconcile_tasks.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_reconcile_tasks.py -k "reconcile or verification" -q
```

---

## P2.4 — Judge pipeline trace for verification

**What:** Extend **judge** pipeline step artifact via `record_judge_pipeline_step` (or companion fields): `verification_judged_count`, verification candidate `group_ids`, outcomes. **Not** reconcile `resolution_pass` — that is P3.1.

**Files:** `backend/app/services/github_pipeline_trace.py`, `backend/app/workers/reconcile_tasks.py`, `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py -k judge -q
```

---

## P2.5 — Cap + skip when judge disabled

**What:** In `github_finding_closure.py`: verification skipped when `judge_llm_enabled()` false (same as discovery); enforce `VERIFICATION_JUDGE_MAX_PER_RUN = 5`; no publish block for verification skip.

**Files:** `backend/app/services/github_finding_closure.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py -k "verification or cap" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_closure.py tests/unit/test_reconcile_tasks.py tests/unit/test_github_pipeline_trace.py -q
pipenv run ruff check app/services/github_finding_closure.py app/workers/reconcile_tasks.py
```

**Next:** [FINDING_RESOLUTION_P3_EXECUTION.md](./FINDING_RESOLUTION_P3_EXECUTION.md)
