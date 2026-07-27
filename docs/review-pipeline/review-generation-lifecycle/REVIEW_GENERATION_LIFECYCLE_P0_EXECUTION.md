# Review generation lifecycle P0 — Foundations (execution)

Phase **P0** of [REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md](./REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md). Baseline: [REVIEW_GENERATION_LIFECYCLE_FINDINGS.md](./REVIEW_GENERATION_LIFECYCLE_FINDINGS.md) §2, RG-9, RG-Q9, RG-Q11, RG-Q12. **P0 only.**

**Goal:** Generation lifecycle primitives — enum values, authority helpers, coalesce setting, PR review context.

## Decisions locked for P0

- `GitHubReviewRunStatus.superseded` added to `enums.py` — **no Alembic** (RG-Q12).
- `GitHubPublishJobStatus.skipped_not_head` + `skipped_superseded` — terminal skip states.
- New module `github_generation_lifecycle.py` owns `is_authoritative_for_pull_request_head`, `mark_review_runs_superseded_for_pull_request`, `is_review_run_superseded`.
- `is_authoritative_for_pull_request_head`: `revision.head_sha == pull_request.head_sha` for the revision’s PR.
- `mark_review_runs_superseded_for_pull_request`: set `superseded` on pending/processing review runs for **older revisions** on same PR; leave `keep_revision_id` authoritative.
- `mark_pending_review_runs_superseded_for_revision(session, *, revision_id)` (or equivalent): set `superseded` on pending/processing runs for **that revision** — used when `@revy review` supersedes autostart on same HEAD (P2).
- `review_coalesce_seconds`: int, **default 0** (off), max **10**; validated in `Settings`.
- First LOOP commit updates `.greptile/files.json` + `.cursor/BUGBOT.md` to this program.
- Module docstring documents **trace field contract** (manifest keys added in P5) and **smart-trigger guard** table (bot events that must not supersede).

## PR review context (first commit)

- **Greptile:** `.greptile/files.json` — execution index, findings, general plan; `scope: ["backend/**"]`
- **Bugbot:** `.cursor/BUGBOT.md` — links to same docs; branch `feat/review-generation-lifecycle`

## Out of scope for P0

- HEAD-gated publish → **P1**
- Supersede on synchronize / stage guards → **P2**
- Surface flush → **P3**
- Coalesce task wiring → **P4**

---

## P0.1 — Program PR review context

**What:** Point `.greptile/files.json` and `.cursor/BUGBOT.md` at `review-generation-lifecycle/` docs (keep `REVIEW_QUALITY_EXECUTION.md` + agent workflow refs).

**Files:** `.greptile/files.json`, `.cursor/BUGBOT.md`

**Deliverable:**

```bash
python -m json.tool .greptile/files.json > /dev/null
```

---

## P0.2 — Status enum values

**What:** Add `superseded` to `GitHubReviewRunStatus`; add `skipped_not_head`, `skipped_superseded` to `GitHubPublishJobStatus`. No DB migration (RG-Q12); `stored_enum_value` needs no change.

**Files:** `backend/app/constants/enums.py`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/constants/enums.py
```

---

## P0.3 — Generation lifecycle service

**What:** Create `github_generation_lifecycle.py` with:

- `async def is_authoritative_for_pull_request_head(session, *, revision_id: UUID) -> bool`
- `async def mark_review_runs_superseded_for_pull_request(session, *, pull_request_id: UUID, keep_revision_id: UUID) -> list[UUID]` — older revisions only; returns superseded review_run ids
- `async def mark_pending_review_runs_superseded_for_revision(session, *, revision_id: UUID) -> list[UUID]` — same revision, pending/processing only (command vs autostart)
- `def is_review_run_superseded(run: GitHubReviewRunORM) -> bool`

Log `generation_superseded` with `review_run_id`, `revision_id`, `pull_request_id`.

**Module docstring — trace field contract (implemented in P5):** `generation_superseded_at`, `publish_skipped_not_head` on pipeline/publish artifacts.

**Module docstring — smart-trigger guard (do not supersede / coalesce):**

| Event | Path | Today |
|-------|------|-------|
| Bot `@revy review` comment | `apply_issue_comment_webhook_event` | ignored (`github_pull_requests.py:487`) |
| `pull_request_review` submitted | `apply_pull_request_review_webhook_event` | records review only — no pipeline enqueue |
| Publish-driven GitHub API | N/A | no webhook back into supersede hook |

**Files:** `backend/app/services/github_generation_lifecycle.py`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/services/github_generation_lifecycle.py
```

---

## P0.4 — Coalesce setting

**What:** Add `review_coalesce_seconds: int = 0` to `Settings`; validator clamps `0 <= value <= 10`. Document in `backend/.env.example` comment (no secret).

**Files:** `backend/app/core/config.py`, `backend/.env.example`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/core/config.py
```

---

## P0.5 — Unit tests (authority + supersede marking)

**What:** Tests: authoritative when revision matches PR `head_sha`; not authoritative when superseded by newer revision; `mark_review_runs_superseded_for_pull_request` flips pending/processing runs on old revisions only; `mark_pending_review_runs_superseded_for_revision` flips same-revision pending/processing; completed runs unchanged.

**Files:** `backend/tests/unit/test_github_generation_lifecycle.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_generation_lifecycle.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check .
pipenv run pytest tests/unit/test_github_generation_lifecycle.py -q
```

**Next:** [REVIEW_GENERATION_LIFECYCLE_P1_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_P1_EXECUTION.md)
