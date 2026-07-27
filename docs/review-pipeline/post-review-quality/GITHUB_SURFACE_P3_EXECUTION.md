# GitHub surface P3 — L3 inline action (execution)

Phase **P3** of [POST_REVIEW_QUALITY_GENERAL_PLAN.md](./POST_REVIEW_QUALITY_GENERAL_PLAN.md). Baseline: [POST_REVIEW_QUALITY_FINDINGS.md](./POST_REVIEW_QUALITY_FINDINGS.md) §4 L3. **P3 only.**

**Goal:** Developers act from the diff — inline threads for **warnings** (and info when line-accurate), not only error/critical. Table remains summary for all severities.

**Authority:** `backend/app/services/github_publish.py` (`inline_publish_findings_statement`) · `backend/app/integrations/github_api.py` (`format_inline_comment_body`)

## Decisions locked for P3

- Extend severity filter in `inline_publish_findings_statement` to include `FindingSeverity.warning` and `FindingSeverity.info` when `file_path` + `start_line` present.
- Reuse `format_inline_comment_body` + R6 `is_publishable_suggestion` — no P-badge markup parity.
- Skip 404/422 inline posts (existing behavior) — table is overflow fallback.
- If table has warnings but no inline after P3: investigate finding line fields (DB) — not formatter.

## Out of scope for P3 (later phases)

- P0/P1/P2 presentation → prior phases
- Track B recall / prompt tuning
- Greptile thread volume on docs-only PRs
- P-badge strings (`P1`/`P2` Greptile style)

---

## P3.1 — Extend inline eligibility query

**What:** Add `warning` and `info` to `GitHubFindingORM.severity.in_(...)` in `inline_publish_findings_statement`; keep active-group join and line guards.

**Files:** `backend/app/services/github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -q -k "inline_publish"
```

---

## P3.2 — Unit test: warning finding posts inline

**What:** Add `test_inline_publish_findings_statement_includes_warning` and `test_run_publish_job_posts_inline_for_warning_finding` (net-new — today only error/critical paths exist).

**Files:** `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest \
  tests/unit/test_github_publish.py::test_inline_publish_findings_statement_includes_warning \
  tests/unit/test_github_publish.py::test_run_publish_job_posts_inline_for_warning_finding -q
```

---

## P3.3 — Suggestion block on inline when publishable

**What:** Assert warning inline body includes ```suggestion fence when `is_publishable_suggestion` true (existing path — extend test coverage if only error/critical tested).

**Files:** `backend/tests/unit/test_github_publish.py`, `backend/tests/unit/test_github_suggestion.py` (if exists)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py tests/unit/test_github_suggestion.py -q
```

---

## P3.4 — Dogfood L3 row

**What:** On PR with warning+ line findings, confirm inline thread on GitHub; update [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md) L3 = Y.

**Files:** `docs/review-pipeline/post-review-quality/GITHUB_SURFACE_DOGFOOD.md`

**Deliverable:** Dogfood row L3 = Y or note “no warning findings this PR — deferred”. **Non-gate** for pytest.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_publish.py::test_inline_publish_findings_statement_includes_warning \
  tests/unit/test_github_publish.py::test_run_publish_job_posts_inline_for_warning_finding \
  tests/unit/test_github_publish.py tests/unit/test_github_api_publish.py tests/unit/test_github_suggestion.py -q
```

**Next:** [GITHUB_SURFACE_P4_EXECUTION.md](./GITHUB_SURFACE_P4_EXECUTION.md)
