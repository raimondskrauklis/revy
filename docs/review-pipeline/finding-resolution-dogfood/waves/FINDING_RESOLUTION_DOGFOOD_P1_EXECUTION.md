# Finding resolution dogfood P1 — FR-DG1 manifest & G9 (execution)

Phase **P1** of [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md). Baseline: findings § FR-DG1. **P1 only.**

**Goal:** Fix push that publishes yields `denominator_active_prior` ≥ 1, `transitions_addressed` ≥ 1; G9 + resolution metrics block reflect manifest (not `n/a`).

## Decisions locked for P1

- **Shared helper:** `get_last_published_prior_revision(session, pull_request_id, current_revision)` — walks revisions backward to last with completed publish; skips `skipped_not_head`. Wired in **all three** call sites:
  - `backend/app/workers/reconcile_tasks.py` (manifest `prior_revision_number` — today `revision_number - 1` at ~line 87)
  - `backend/app/services/github_resolution_metrics.py` (`apply_resolution_status_for_synchronize` — today `revision_number - 1` at ~line 125)
  - `backend/app/services/github_finding_closure.py` (`_load_prior_revision` — today `revision_number - 1` at ~line 92)
- **`get_resolution_metrics_for_review_run`:** reads reconcile `resolution_pass` only — no prior-revision logic here; fix is upstream in reconcile + Pass 1.
- **G9 + summary_json:** `build_g9_resolution_prose` and `summary_json.resolution` must use `ctx.resolution_metrics_manifest` (`transitions_addressed`, `denominator_active_prior`) — not generation-scoped `ctx.groups` alone (current bug at `github_publish_formatter.py` ~599, ~816–826).
- **Dogfood push 2 (P1.4):** wire unused probe const or minor fix — **do not remove probe file** (that is FR-DG2 / push 3 after P2 deploy).

## Out of scope for P1

- Pass 2 `state=resolved` on code removal → **P2**
- Moonshot prompt → **P4**
- Program sign-off → **P3**

---

## P1.1 — Repro confirmation test

**What:** Unit tests: rev N−1 `skipped_not_head` + rev N publish → helper returns last **published** prior; manifest `denominator_active_prior` ≥ 1.

**Files:** `backend/tests/unit/test_github_resolution_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py -k "skipped_not_head or prior_published or last_published" -q
```

---

## P1.2 — Last-published prior revision helper

**What:** Implement `get_last_published_prior_revision`; replace naive `revision_number - 1` in reconcile_tasks, github_resolution_metrics, github_finding_closure.

**Files:** `backend/app/services/github_resolution_metrics.py` (helper + Pass 1), `backend/app/workers/reconcile_tasks.py`, `backend/app/services/github_finding_closure.py`

**Deliverable:** P1.1 tests pass; no caller uses `revision_number - 1` for resolution pairing.

---

## P1.3 — Manifest + G9/summary_json wiring

**What:** `build_resolution_pass_manifest` uses helper for denominator/transitions; publish path passes manifest into G9 block and `summary_json.resolution` (aligned with `format_resolution_metrics_block`).

**Files:** `backend/app/services/github_resolution_metrics.py`, `backend/app/services/github_publish_formatter.py`, `backend/app/services/github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_publish_formatter.py -k "resolution or g9" -q
```

---

## P1.4 — Merge, deploy, dogfood push 2 (FR-DG1)

**What:** Merge P1 to `main`; wait for droplet deploy; record **post-P1 deploy ISO** in staging memo; chore PR **single commit** wiring probe const (not deleting probe); push; **wait for agent**.

**Pass criteria (push 2):** reconcile trace `transitions_addressed` ≥ 1; G9 not `n/a`; `summary_json.resolution.addressed` ≥ 1 (manifest-aligned).

**Files:** `backend/tests/fixtures/fr_dogfood/probe_module.py`, staging memo push-2 row

**Deliverable:** Memo row PASS for FR-DG1 manifest + surface fields.

**Human gate:** Deploy complete before push 2; agent complete before P2 code.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_publish_formatter.py tests/unit/test_github_pipeline_trace.py -q
```

**Next:** [FINDING_RESOLUTION_DOGFOOD_P2_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P2_EXECUTION.md)
