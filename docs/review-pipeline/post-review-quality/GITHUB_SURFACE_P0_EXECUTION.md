# GitHub surface P0 — Worker current + first dogfood (execution)

Phase **P0** of [POST_REVIEW_QUALITY_GENERAL_PLAN.md](./POST_REVIEW_QUALITY_GENERAL_PLAN.md). Baseline: [POST_REVIEW_QUALITY_FINDINGS.md](./POST_REVIEW_QUALITY_FINDINGS.md) §7–8. **P0 only.**

**Goal:** Staging workers run post-merge publisher code; first PR branch push produces a dogfood row and answers PQ-2 (formatter on GitHub).

**Status:** **Merged** [PR #52](https://github.com/raimondskrauklis/revy/pull/52). Human gates P0.4/P0.5: deploy + post-merge dogfood row.

## Decisions locked for P0

- Reviews run on **PR `head_sha`** via `pull_request` `opened` / `synchronize` — pre-merge, same timing as Greptile.
- **`main` deploy** refreshes worker/API image only — not when review triggers.
- P0 code fixes **only** if publish posts wrong body (JSON leak, formatter bypass) — not L2 copy polish (P1).
- First [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md) row is a **human** step after ops + PR push.

## Out of scope for P0 (later phases)

- L2 section/copy polish beyond wiring → **P1**
- G10 ack snack → **P2**
- Inline warnings → **P3**
- PRODUCT_PATTERNS full sweep → **P4** (surgical flip in P0.5 if L2 passes)
- Track B recall investigation → log in dogfood only

---

## P0.1 — Program PR review context

**What:** Wire Greptile + Bugbot to this program’s docs for `backend/**` publish work.

**Files:** `.greptile/files.json`, `.cursor/BUGBOT.md`

**Deliverable:** JSON valid; Bugbot links to `post-review-quality/` findings, general plan, and `GITHUB_SURFACE_EXECUTION.md`.

```bash
python -m json.tool .greptile/files.json > /dev/null
```

---

## P0.2 — Publish path: issue comment uses formatter markdown

**What:** Add `test_run_publish_job_posts_formatted_issue_comment`: mock `create_issue_comment` / `update_issue_comment` and assert `body` equals `formatted.issue_comment` (markdown from formatter), not `json.dumps(summary_json)`. Fix `run_publish_job` wiring only if test fails.

**Files:** `backend/app/services/github_publish.py`, `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py::test_run_publish_job_posts_formatted_issue_comment -q
```

---

## P0.3 — Autostart on `synchronize`

**What:** Add `test_process_github_event_enqueues_pipeline_on_pull_request_synchronize` — mirror opened test but `action=synchronize` and `new_revision=True`. Today only `opened` is covered in `test_github_tasks_autostart.py`.

**Files:** `backend/tests/unit/test_github_tasks_autostart.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_tasks_autostart.py::test_process_github_event_enqueues_pipeline_on_pull_request_synchronize -q
```

---

## P0.4 — Human gate: staging worker ops

**What:** Once before first dogfood PR (after `main` includes this program branch merge or worker deploy):

| Step | Verify |
|------|--------|
| `main` deploy completed | Worker + beat image matches repo |
| `alembic upgrade head` through `0026` | Staging DB current |
| Revy GitHub App enabled | Webhooks deliver |
| `review_autostart_enabled=true` | Workspace setting |

**Files:** none (ops)

**Deliverable:** Checklist noted in dogfood row or operator log. **Non-gate for pytest** — LOOP may commit P0.1–P0.3 before ops complete. **Required before README marks P0 Done.**

---

## P0.5 — Human gate: first dogfood row

**What:** Open PR with real branch (docs + code). Push → wait for Revy + Greptile on **same PR**. Fill first row in [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md) (L1/L2/L3 Y/N, H1–H4).

**Files:** `docs/review-pipeline/post-review-quality/GITHUB_SURFACE_DOGFOOD.md`

**Deliverable:** At least one row with PR # and `head_sha`. **Non-gate for pytest**; **required before README marks P0 Done**. Blocks **P1** if L2 = N due to JSON/wiring (fix in P0.2 or P1).

**Optional (same commit if L2 = Y):** Surgical PRODUCT_PATTERNS — flip **Check run in progress on PR** + **Numeric confidence 0–5** rows to `shipped` (exact labels in P4.1).

---

**Phase gate** (from `backend/` — code subphases only):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_publish.py::test_run_publish_job_posts_formatted_issue_comment \
  tests/unit/test_github_tasks_autostart.py::test_process_github_event_enqueues_pipeline_on_pull_request_synchronize \
  tests/unit/test_github_tasks_autostart.py::test_process_github_event_enqueues_pipeline_after_pull_request_opened \
  tests/unit/test_github_publish_formatter.py -q
```

**Human gate (required for README P0 Done, not for pytest gate above):** P0.4 ops checklist + P0.5 dogfood row.

**Deploy:** Worker image must include merged publisher code before P0.5 dogfood is meaningful.

**Next:** [GITHUB_SURFACE_P1_EXECUTION.md](./GITHUB_SURFACE_P1_EXECUTION.md)
