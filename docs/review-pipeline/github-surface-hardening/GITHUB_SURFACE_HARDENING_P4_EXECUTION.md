# GitHub surface hardening P4 — Harness + sign-off (execution)

Phase **P4** of [GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md](./GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md). Baseline: [GITHUB_SURFACE_HARDENING_FINDINGS.md](./GITHUB_SURFACE_HARDENING_FINDINGS.md) GH-6, GH-7, §11. **P4 only — final phase.**

**Goal:** Maintainable publish tests; program doc sync; human dogfood gate.

## Decisions locked for P4

- Refactor brittle `session.scalars` side_effect chains to targeted patches (`find_publish_job_for_head_sha`, `find_prior_issue_comment_id_for_pull_request`, etc.).
- No `changelog.json` — not user-facing SaaS UI.
- Optional `review-github-v1` tag note in README only — not a LOOP gate.

## Out of scope for P4

- Track B programs
- Full integration / e2e suite

---

## P4.1 — Publish test harness refactor

**What:** Extract `_publish_job_context` helpers or shared fixtures; replace ordered scalars lists in `test_run_publish_job_*` with explicit patches documented in test module header. Keep autouse formatter defaults; document which tests disable resolve mock.

**Files:** `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -q
```

---

## P4.2 — Doc sync

**What:** Update docs per table below; mark execution README rows Done; waves hardening section complete.

| Doc | Change |
|-----|--------|
| `github-surface-hardening/README.md` | All phases Done |
| `GITHUB_SURFACE_HARDENING_EXECUTION.md` | Status column Done |
| `waves/README.md` | Hardening phases Done |
| `post-review-quality/README.md` | Link to hardening complete |
| `REVIEW_PIPELINE_PRODUCT_PATTERNS.md` | GH-2/3 rows if needed |

**Files:** paths in table

**Deliverable:** Grep confirms no `pending` in hardening execution table.

---

## P4.3 — Human gate: GH-7 dogfood

**What:** After staging deploy of full program branch: open PR or push → fix a finding → verify Revy thread collapses without manual `gh`. Record row in [GITHUB_SURFACE_HARDENING_DOGFOOD.md](./GITHUB_SURFACE_HARDENING_DOGFOOD.md).

**Files:** `GITHUB_SURFACE_HARDENING_DOGFOOD.md`

**Deliverable:** Dogfood row with PR #, SHA, Thread auto-resolve = Y — or explicit waive note with reason.

**Non-gate for pytest** — LOOP may commit P4.1–P4.2 before row exists; **required for program sign-off.**

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_publish.py \
  tests/unit/test_github_api_publish.py -q
```

**Human gate (required for program complete):** P4.3 dogfood row or documented waive.

**Next:** none — program complete after GH-7.
