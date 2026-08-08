# Review pipeline — staging smoke validation (2026-07-27)

**Purpose:** Record the first successful end-to-end run on staging (index → review → reconcile → publish) after polish wave + hotfix stack, including failures encountered, fixes shipped, and review-quality observations.

**Test PR:** [#44 — `test/review-pipeline-smoke`](https://github.com/raimondskrauklis/revy/pull/44) (tiny change in `backend/tests/unit/test_review_pipeline.py`).

**Repo under review:** `raimondskrauklis/revy` @ `78a5c0cb` (PR head SHA indexed).

**Staging config (representative):**

| Key | Value |
|-----|--------|
| Reviewer | Moonshot `kimi-k2.7-code` (`REVY_REVIEWER_PROVIDER=moonshot`) |
| Judge | Anthropic / Bedrock (escalation only) |
| Embeddings | Voyage `voyage-code-3` (tier 1 after free-trial 3 RPM limit) |
| Index scope | Full repo tarball at `head_sha` (R3 behaviour — not PR diff) |

---

## Outcome

| Stage | Result | Notes |
|-------|--------|-------|
| Webhook → index | ✅ | ~32s, 12 Voyage embedding batches |
| Review (R4) | ✅ | Moonshot HTTP 200, ~535s |
| Reconcile (R5) | ✅ | `github_reconcile_complete` ~0.2s |
| Publish (R6) | ✅ | Check run + PR summary comment ~1.6s |
| GitHub surface | ✅ | Check run + “Revy review summary” table on PR #44 |

**Verdict:** Pipeline infrastructure is **validated on staging**. Review *signal quality* on this smoke PR is **low** (see § Review output quality).

---

## Successful run (Celery log excerpt)

**Window:** 2026-07-27 ~01:15–01:24 UTC (worker restart ~01:13).

```text
github_index_job_complete                          (~31s index)
review_pull_request_revision received
4× Voyage embed_query (context search)
POST api.moonshot.ai/v1/chat/completions 200 OK    (~535s review)
github_review_run_complete
reconcile_review_run received
github_reconcile_complete                          (~0.2s)
publish_for_review_run → publish_review_run
POST …/check-runs 201 Created
POST …/issues/44/comments 201 Created
github_publish_complete                            (~1.6s)
```

---

## Published findings (PR #44)

### GitHub vs Revy (same run, different surfaces)

| Surface | What you see | Why |
|---------|----------------|-----|
| **GitHub** — PR summary comment / check run table | Severity, category, **title**, file only | R6 `build_summary_markdown()` — columns are `Severity \| Category \| Title \| File`; **no message column** (keeps GitHub table compact; link to Revy for detail). |
| **Revy** — `/reviewer/...` findings table | Severity, category, state, **title**, file, **message** | R7 UI shows full `github_finding_groups.message` per row. |
| **GitHub** — inline review comments | Title + message (error/critical only) | `format_inline_comment_body()` — not used for these warnings. |

So “GitHub had just the title; Revy had the text as well” is **expected**, not a publish bug. Detail lives in Revy; GitHub is the summary + deep link.

### Two rows in Revy (not one duplicate swallowed)

Revy showed **two active groups** with the same title and file but **different messages**:

1. *…passes as long as session.add is called, even if the function returns None…*
2. *…satisfied whenever a job object is added… `maybe_enqueue_pipeline_for_revision`… Use `assert job_id is not None` instead.*

**Why two groups:** R5 fingerprint = `hash(workspace, pr, file_path, category, **normalized message**)` (`compute_fingerprint` in `github_finding_reconcile.py`). Same title and file, but the model paraphrased the nit twice (lines 124 & 167) → **two fingerprints** → two `github_finding_groups` rows. Reconcile did not merge them; nothing was dropped after publish.

**GitHub table** showed two identical-looking rows (title + file only), which hid that the messages differed.

**Code (lines 124 & 167):**

```python
assert job_id is not None or session.add.called
```

**Assessment:** Low-value test-file nits on a smoke PR. Judge did not run (`warning` + `maintainability` — outside R5 escalation). Product follow-up: consider fingerprinting on `title` + anchored line (or `title` + file) instead of full message to collapse LLM paraphrase duplicates; optional truncated message column on GitHub summary.

### GitHub summary table (as published)

| Severity | Category | Title | File |
|----------|----------|-------|------|
| warning | maintainability | Weak OR assertion masks missing return value | `backend/tests/unit/test_review_pipeline.py` |
| warning | maintainability | Weak OR assertion masks missing return value | `backend/tests/unit/test_review_pipeline.py` |

---

## Incidents and fixes (chronological)

| # | Symptom | Root cause | Fix PR |
|---|---------|------------|--------|
| 1 | Index 429 / slow | Voyage free trial 3 RPM; env typo `oyage-code-3` | [#45](https://github.com/raimondskrauklis/revy/pull/45) — client retry + config strip |
| 2 | Review `AttributeError: 'str' has no attribute 'value'` on `run.profile` | SQLAlchemy String enum hydrated as `str` | [#46](https://github.com/raimondskrauklis/revy/pull/46) — `_review_profile_str()` + worker retry policy |
| 3 | Moonshot **400** on review | `kimi-k2.7-code` rejects `temperature≠1.0` | [#47](https://github.com/raimondskrauklis/revy/pull/47) — per-model request body |
| 4 | Moonshot **200** but `github_review_run_failed` / `Moonshot review response truncated` | `max_completion_tokens` too low — K2/K3 `reasoning_content` exhausts budget before JSON/markdown `content` | [#48](https://github.com/raimondskrauklis/revy/pull/48) omitted cap (API default ~1024); set `REVY_MOONSHOT_MAX_COMPLETION_TOKENS=32768` (min 16000 per Moonshot docs) |
| 5 | Reconcile `category.value` on `str` | Same String-enum hydration pattern | [#49](https://github.com/raimondskrauklis/revy/pull/49) — `stored_enum_value()` |
| 6 | Publish stuck `processing` (Bugbot) | Permanent HTTP error with `persist_github_surface=True` returned without `failed` | [#47](https://github.com/raimondskrauklis/revy/pull/47) (publish half) |

**Deploy note:** Fixes landed across #46–#49; successful e2e run above was after #48 (Moonshot budget) and #49 (reconcile enum) were on staging.

---

## Learnings

### 1. String-mapped enums + async SQLAlchemy

**Pattern:** ORM columns declared `Mapped[SomeEnum]` with `mapped_column(String(...))` may hydrate as plain `str` on read.

**Safe:**

- `stored_enum_value(field)` for serialization / fingerprints / logging
- `str(field)` in worker logs
- `== SomeEnum.member` comparisons (`str` enums compare equal to string values)
- `_review_profile_str()` for `ReviewProfile`

**Risky:**

- `field.value` after DB load → `AttributeError`

**String-mapped enum columns (review domain):** `github_findings` severity/category; `github_finding_groups` state/severity/category; `github_review_runs` status/profile/judge_status; `github_index_jobs` status/trigger_source; `github_publish_jobs` status; `github_pull_requests.state`; `github_finding_judge_outcomes.outcome`.

**Lower risk:** native PostgreSQL `Enum(...)` columns (`users.status`, `workspace_memberships.role`).

### 2. Moonshot `kimi-k2.7-code`

| Topic | Detail |
|-------|--------|
| Temperature | Must omit or use default `1.0` — `0.2` → 400 |
| Thinking | Always on; do not pass `thinking` param for k2.7 |
| Completion budget | `reasoning_content` + `content` share `max_completion_tokens`. Set `REVY_MOONSHOT_MAX_COMPLETION_TOKENS` (default **32768**, min 16000). Omitting the param uses API default ~1024 → `finish_reason: length`, empty `content`, review run `failed` |
| K3 (`deep` / `critical`) | Use `reasoning_effort` in code (`high` / `max`), not env. Omit `max_completion_tokens` — API default 131072 |

### 3. Worker retries (post-#46)

| Queue | Policy |
|-------|--------|
| `review` | Retry only classified transient errors (408/429/5xx); permanent → `failed` |
| `indexing` | `max_retries=0`; Voyage client handles burst 429; job marked `failed` in service |
| `reconciliation` | Celery blind retry (pre-R6-style) — reconcile failures retry with backoff |

### 4. Review output quality (this smoke PR)

| Factor | Effect |
|--------|--------|
| Full-repo index | RAG context includes unrelated files (e.g. tests) |
| Tiny PR diff | Model reviews indexed haystack, not the 1-line change |
| Standard profile | No judge on warnings; style category dropped at parse |
| ~9 min review | High latency for two low-signal test nits |

**Not swallowed:** findings shown are what the reviewer produced after parse filters; reconcile and publish did not drop them.

---

## Post–review-quality re-smoke (2026-07-27+)

**When:** After PR #50 + RQ9 merge and `alembic upgrade head` through `0026` on staging.

**Differs from § Outcome above:** index uses **compare + diff-scoped tarball** (D13), not full-repo tarball. Check run should show **`in_progress`** during review (G10), then `completed`.

| Gate | Check |
|------|--------|
| Index mode | `github_index_jobs.index_mode = diff` on autostart job |
| Pipeline trace | `GET …/pipeline` returns `retrieve` → `review` → … steps |
| D10 | Re-push same PR — no duplicate active groups |
| RQ6 | Deletion-only sync sets `resolution_status` on prior groups |
| G3 | Compact check body; Greptile narrative in issue comment |
| G10 RQ9 | Open PR indexed → convert to draft before review enqueue → check `neutral` (not stuck `in_progress`) |
| O8 | Celery beat running; `pipeline_purge_tasks` registered |

**Test PR:** [#44](https://github.com/raimondskrauklis/revy/pull/44) or new tiny diff PR.

---

## Follow-ups (product / engineering)

| Priority | Item | Track |
|----------|------|-------|
| High | Diff-scoped / incremental indexing (index PR changed files only) | **review-quality** (merged #50) + RQ9 hardening |
| Medium | Deprioritize or exclude `**/tests/**` in standard profile unless PR touches tests | Prompt / index policy |
| Medium | Reconcile Celery retry → same transient classification as review/publish | Hardening |
| Low | Dedupe paraphrase duplicates (fingerprint includes full `message`) | R5 fingerprint policy |
| Low | Optional message snippet in GitHub summary table | R6 publish UX |
| Ops | Close smoke PR #44 or merge if still needed for regression | — |

---

## Re-run checklist

1. Staging on `main` with #45–#49 merged.
2. `MOONSHOT_API_KEY`, `VOYAGE_API_KEY`, `REVY_EMBEDDING_MODEL=voyage-code-3`, GitHub App PEM mounted.
3. Worker queues: `github_events,repo_sync,indexing,review,reconciliation,judge,github_publish,…`
4. Push to open PR or comment `@revy review` (R8).
5. Confirm log sequence: `github_index_job_complete` → `github_review_run_complete` → `github_reconcile_complete` → `github_publish_complete`.
6. GitHub: check run + summary comment on PR.

---

## Related docs

- [REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](./REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) — Track F ops
- [GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md) — local / dev webhook flow
- [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) — Greptile + product patterns
- Polish wave: [REVIEW_PIPELINE_POLISH_GENERAL_PLAN.md](./REVIEW_PIPELINE_POLISH_GENERAL_PLAN.md) ([#43](https://github.com/raimondskrauklis/revy/pull/43))
