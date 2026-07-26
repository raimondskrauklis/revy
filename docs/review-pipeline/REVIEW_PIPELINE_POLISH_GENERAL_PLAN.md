# Review pipeline polish — general plan

General plan from [REVIEW_PIPELINE_POLISH_FINDINGS.md](./REVIEW_PIPELINE_POLISH_FINDINGS.md). **No execution steps.**

**Cross-cutting (every phase):** hand-written Alembic; `backend/tests/unit/` + Vitest; EN+LV `t()` for UI; `--app-*` tokens; no webhook or publish-idempotency changes.

**Branch:** `feat/review-polish` · **Tag (optional):** `review-polish-v1` on `main` after merge.

---

## P0 — Schema and enums

**Goal:** Add persistence for suggestions and per-run judge escalation status.

**Scope:** In — migration on `github_findings.suggestion`; `github_review_runs.judge_status` + `judge_escalation_candidate_count`; `GitHubReviewJudgeStatus` enum; ORM + Pydantic (`GitHubReviewRunResponse` judge fields; optional `suggestion` on `GitHubFindingResponse` for raw findings endpoint only — not reconciled). Out — reconciled-finding schema changes; backfill.

**Deliverables:** `alembic upgrade head` applies cleanly; API types compile; existing rows default to `suggestion=NULL`, `judge_status=not_applicable`, `candidate_count=0`.

**Depends on:** R4–R7 schema on `main` (through migration `0024`).

---

## P1 — Suggestion pipeline (R6-Q3)

**Goal:** Generate, store, and publish GitHub suggestion blocks on eligible inline comments.

**Scope:** In — extend `REVIEW_SYSTEM_PROMPT` in Moonshot + Anthropic (Bedrock imports anthropic); shared `github_suggestion.py` for parse + publish rules; `_parse_finding_row` + finding insert; reject `\n` in suggestion at parse; `format_inline_comment_body(suggestion=…)`; `is_publishable_suggestion`; publish loop wiring; unit tests. Out — UI display; multiline suggestion blocks; suggestion on check-run summary.

**Deliverables:** New reviews may persist `suggestion`; inline GitHub comments include `` ```suggestion `` when line-accurate; invalid suggestions degrade to message-only without job failure.

**Depends on:** P0.

---

## P2 — Judge skipped badge

**Goal:** Operators see when escalation judge did not run despite high-severity candidates.

**Scope:** In — `record_review_run_judge_status` (count before skip paths); set `judge_status` per J1–J5; expose on `GitHubReviewRunResponse`; `JudgeSkippedBadge` on `PullRequestDetailPage`; EN+LV strings; Vitest. Out — settings-page warning; re-trigger judge; per-outcome judge detail; badge for partial LLM failure (J5).

**Deliverables:** PR detail shows badge when latest review run has skipped judge with candidates; badge hidden when `not_applicable` or `completed`.

**Depends on:** P0 (may parallelize implementation with P1 after migration lands).

---

## Out of scope (this wave)

- R9 incremental index, evidence snippets, email digest
- `workspace_review_policy` / custom rules
- Numeric confidence score
- `@revy index` / `@revy publish`
- Publish–UI parity regression test (separate follow-up)

---

## Product patterns update

After ship, move rows in [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md):

| Pattern | Status change |
|---------|----------------|
| Suggested fix / patch (`R6-Q3`) | **defer** → **shipped** |
| Judge skipped visibility (learnings) | **future** → **shipped** |

Lock P5 in parent [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) R6-Q3 row when execution completes.

---

## Next step

**Execution:** [waves/REVIEW_PIPELINE_POLISH_P0_EXECUTION.md](./waves/REVIEW_PIPELINE_POLISH_P0_EXECUTION.md) → P1 → P2 — manual **`execution-peer-review`** → `phase-execution` on `feat/review-polish`.
