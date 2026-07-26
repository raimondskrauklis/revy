# Review pipeline polish — findings

Baseline for **visible product polish** after R6–R7: **R6-Q3 GitHub suggestion blocks** on inline comments and a **“Judge skipped” badge** in the reviewer UI. **No execution steps.**

**Date:** 2026-07-27 · **Status:** shipped (polish wave P0–P2).

**Program:** [README.md](./README.md) · **Deferred source:** [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) R6-Q3 · [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) (judge skipped UI).

**Depends on:** R4–R7 on `main`; independent of R8 merge (can ship on `feat/review-polish` in parallel with PR [#31](https://github.com/raimondskrauklis/revy/pull/31)).

---

## Goal

Close two deferred polish items that improve developer-facing signal without opening R9 (incremental index) or policy/automation scope:

1. **R6-Q3** — When the reviewer LLM returns a line-accurate fix, publish it as a GitHub **suggestion block** on inline PR comments (one-click apply).
2. **Judge skipped** — When R5 escalation judge does not run because credentials/provider are unavailable **but** escalation candidates exist, show a clear badge on `/reviewer` PR detail (operators today must read worker logs).

---

## Build principles

- **Additive** — no change to reconcile fingerprints, publish idempotency (R6-Q1), or merge-readiness rules (R6-Q2).
- **Conservative v1** — omit suggestion blocks when anchor or content is ambiguous; never block publish on bad suggestion text.
- **Persist judge outcome at reconcile time** — do not derive skip state from current env at API read (keys may change between runs).
- **Hand-written Alembic**; unit tests only; **EN+LV** for new UI strings; `--app-*` tokens.

---

## What exists today (verified)

### R6 inline publish

| Piece | Location | Behavior |
|-------|----------|----------|
| Inline subset | `github_publish.py` `inline_publish_findings_statement` | `error`/`critical`, active group, `file_path` + `start_line` |
| Comment body | `integrations/github_api.py` `format_inline_comment_body` | `**[SEVERITY] title**\n\n{message}` only — **no suggestion** |
| Post loop | `github_publish.py` `run_publish_job` | `create_pull_request_review_comment` per finding; 404/422 → log + skip line |

### R4 findings schema

| Piece | Location | Behavior |
|-------|----------|----------|
| ORM | `models/github_finding.py` | `title`, `message`, `file_path`, `start_line`, `end_line` — **no `suggestion` column** |
| LLM JSON | `moonshot_review.py`, `anthropic_review.py` `REVIEW_SYSTEM_PROMPT` | Findings array without `suggestion` field |
| Parse | `services/github_review.py` `_parse_finding_row` | Drops `style`; no suggestion handling |

### R5 judge

| Piece | Location | Behavior |
|-------|----------|----------|
| Skip when disabled | `github_finding_judge.py` `run_judge_for_review_run` | `if not settings.judge_llm_enabled(): return 0` — **no persisted skip flag** |
| Skip on model resolve fail | same | logs `github_finding_judge_model_resolve_failed`, returns 0 |
| Orchestration | `workers/reconcile_tasks.py` | reconcile → judge → publish; logs `judge_outcomes` count only |
| Outcomes table | `github_finding_judge_outcomes` | Rows only when judge **ran** |

### R7 reviewer UI

| Piece | Location | Behavior |
|-------|----------|----------|
| PR detail header | `PullRequestDetailPage.tsx` | `MergeReadinessBadge`, review-run status, publish status — **no judge indicator** |
| Review run API | `schemas/github_review.py` `GitHubReviewRunResponse` | `status`, `profile`, `provider` — **no `model_id` in response** (ORM has `model_id`); **no judge fields** |
| Reviewer prompts | `moonshot_review.py`, `anthropic_review.py` | Separate `REVIEW_SYSTEM_PROMPT` constants (same shape; Bedrock imports anthropic) |

### Locked deferral (parent findings)

| Q# | Resolution |
|----|------------|
| **R6-Q3** | Optional `suggestion` on finding row; GitHub suggestion block **only when line-accurate** |
| R5-Q3 | Judge optional when `ANTHROPIC_API_KEY` / Bedrock judge unset — reconcile still completes |

---

## Genuinely new work

| Track | New |
|-------|-----|
| **Suggestions** | DB column; `github_suggestion.py`; prompt + parse; publish formatter; unit tests |
| **Judge badge** | DB column(s) on `github_review_runs`; set in reconcile/judge path; API field; `JudgeSkippedBadge` + i18n |

**Not in scope (v1):** suggestion in Revy findings table UI; **`GET …/findings/reconciled`** carrying suggestion; numeric confidence; email digest; re-prompting judge when keys are added later. Raw per-revision **`GET …/findings`** may expose `suggestion` on `GitHubFindingResponse` (admin/debug; reviewer UI does not use it).

---

## Track A — GitHub suggestion blocks (R6-Q3)

### GitHub format

Inline review comment body may append a fenced block:

```markdown
```suggestion
proposed line content
```
```

GitHub applies it as a one-click patch on the commented line. Multi-line suggestions are supported by the API but increase risk of hunk mismatch.

### v1 eligibility (locked — P2, P5–P7)

Publish a suggestion block **only when all** hold:

| Rule | Rationale |
|------|-----------|
| `suggestion` non-empty after strip | No empty blocks |
| **Single-line text:** no `\n` or `\r` in suggestion | v1 “single-line fix” — reject multiline suggestion bodies |
| `file_path` and `start_line` set | Already required for inline |
| **Single-line anchor:** `end_line` is `null` or equals `start_line` | R6-Q3 “line-accurate” |
| No `` ``` `` substring in suggestion text | Avoid breaking markdown fence |
| `len(suggestion) ≤ 2000` | P5 cap |
| Finding still in inline publish set (`error`/`critical`, active group) | Unchanged R6 subset |

Reject at **parse** (`_parse_finding_row`) and **publish** (`is_publishable_suggestion`) via shared `app/services/github_suggestion.py` — same rules both places.

If any rule fails: publish normal inline comment (message only); **do not fail** the publish job.

### LLM contract

Extend `REVIEW_SYSTEM_PROMPT` in **both** `moonshot_review.py` and `anthropic_review.py` (Bedrock reviewer imports anthropic) with optional `"suggestion":"single-line fix or omit"` on each finding. Instruction: one physical line only; omit for architectural or multi-hunk fixes. Optional cleanup (shared constant module) → parking lot.

### Data

- Column: `github_findings.suggestion` `TEXT NULL` (migration `0025` or next head after `0024`).
- Historical runs: `NULL` — no backfill.

---

## Track B — Judge skipped badge

### Problem

When `judge_llm_enabled()` is false (or judge model cannot be resolved) **and** the review run has ≥1 escalation candidate (`is_judge_candidate`), reconcile completes and publish proceeds **without** second-opinion filtering. The UI shows no indication; [CODE_REVIEW_LEARNINGS](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) calls this out.

### Escalation candidates (unchanged)

`is_judge_candidate`: `severity ∈ {error, critical}` OR (`category = security` AND `severity ≥ warning`). Max 10 per run (R5).

### Persisted fields (locked — J1–J5)

On `github_review_runs` at end of reconcile task (after judge call):

| Column | Type | Meaning |
|--------|------|---------|
| `judge_escalation_candidate_count` | `INTEGER NOT NULL DEFAULT 0` | Candidates considered for this run |
| `judge_status` | `VARCHAR(32) NOT NULL` | See enum below |

**`judge_status` enum** (`GitHubReviewJudgeStatus` in `enums.py`):

| Value | When |
|-------|------|
| `not_applicable` | `judge_escalation_candidate_count = 0` |
| `completed` | Judge path entered: credentials ok, `resolve_model(judge)` succeeded, ≥0 `call_judge_llm` attempts (including all calls failing — see J5) |
| `skipped_disabled` | `candidate_count > 0` and `!judge_llm_enabled()` at reconcile time |
| `skipped_unavailable` | `candidate_count > 0`, judge enabled, but `resolve_model(judge)` failed before any call |

**Implementation:** single entry point `record_review_run_judge_status(session, review_run_id)` in `github_finding_judge.py` — count candidates → set columns → run judge when applicable. Called from `reconcile_tasks`; reusable by future `judge_tasks` fan-out. **Do not** early-return before candidate count (today’s `run_judge_for_review_run` returns 0 when disabled before loading candidates).

**UI rule:** Show **Judge skipped** badge only when `judge_status ∈ {skipped_disabled, skipped_unavailable}` and review run `status = completed`.

Do **not** show badge for `not_applicable` (no high-severity candidates) or `completed` (including partial LLM failures per J5).

**J5 (v1 non-goal):** When judge is enabled, model resolves, but **every** `call_judge_llm` fails (`continue` on error), status is still `completed` with `judged == 0` — **no badge**. Operators rely on worker logs (`github_finding_judge_failed`). Distinct status (e.g. `completed_with_errors`) → parking lot / R9+.

### API

Extend `GitHubReviewRunResponse` with `judge_status`, `judge_escalation_candidate_count` (member read on existing `GET …/review-run`).

### Frontend

- Component `JudgeSkippedBadge` — mirror `MergeReadinessBadge` chip styling; muted/warning token.
- `PullRequestDetailPage` header — beside review-run status when `useReviewRun` returns skipped status.
- i18n: `reviewer.judge.skipped`, `reviewer.judge.skippedUnavailable` (optional sub-label) — EN + LV.

---

## Edge cases

| Case | Handling |
|------|----------|
| Suggestion for line not in PR diff | GitHub returns 422 — existing skip path; no suggestion retry |
| Multiline `end_line` with suggestion | Drop suggestion; post message-only inline |
| Multiline suggestion text (`\n`) | Drop at parse and publish |
| `end_line: 0` from LLM | Normalize `0` → `null` in `_parse_finding_row` (P7) |
| Judge enabled mid-flight | Status reflects env **at reconcile** for that run |
| Judge all LLM calls fail | `completed`, no badge (J5) |
| Re-review new run | New `github_review_runs` row; badge per latest run only |
| Bedrock judge configured | `judge_llm_enabled()` true — `skipped_disabled` only when false |
| R8 autostart | No change — polish applies to all trigger paths |
| Empty reconciled list / no `revisionId` | `useReviewRun` disabled — badge absent until reconciled findings load; acceptable v1 |
| Reconcile in progress | Judge columns unset until reconcile task commits — badge absent briefly |

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| P1 | Store suggestion on finding row? | **locked** | `github_findings.suggestion TEXT NULL` |
| P2 | When to emit GitHub suggestion block? | **locked** | Single-line anchor only; rules in Track A |
| P3 | Suggestion in Revy UI v1? | **locked** | **No** — GitHub inline only |
| P4 | Reconciled API carries suggestion? | **locked** | **No** on `GET …/findings/reconciled`; optional on raw `GET …/findings` (`GitHubFindingResponse`) |
| P5 | Suggestion max length | **locked** | **2000** chars |
| P6 | Multiline suggestion text | **locked** | Reject `\n`/`\r` at parse **and** publish |
| P7 | `end_line: 0` from LLM | **locked** | Normalize to `null` in `_parse_finding_row` |
| J1 | Persist judge skip on review run? | **locked** | `judge_status` + `judge_escalation_candidate_count` |
| J2 | Derive skip at API read from env? | **locked** | **No** — persist at reconcile |
| J3 | Badge when no candidates? | **locked** | **No** — `not_applicable` hides badge |
| J4 | Sub-reason in UI | **locked** | `skipped` vs `skippedUnavailable` copy — EN+LV |
| J5 | Judge partial LLM failure UI | **locked** | **`completed`**, no badge — v1 non-goal; logs only |

---

## Parking lot

| Item | When |
|------|------|
| Show suggestion text in `FindingRow` | Post-polish UX |
| `judge_status=completed_with_errors` when all LLM calls fail | R9+ ops / monitoring |
| Shared `REVIEW_SYSTEM_PROMPT` module (dedupe Moonshot + Anthropic) | Optional refactor |
| Re-run judge when keys added | R9+ ops |
| Publish–UI parity test (resolved → not inline) | Separate small test PR ([learnings](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md)) |
| Numeric confidence 0–5 | R6 defer — unchanged |
| Expose `model_id` on `GitHubReviewRunResponse` | Separate API hygiene PR |
| Normalize `start_line: 0` from LLM | Same class as today — optional hardening |

---

## Experiment / verification

| Check | Pass |
|-------|------|
| Unit: `_parse_finding_row` accepts/drops suggestion | Valid single-line kept; `\n` in text or multiline anchor drops suggestion |
| Unit: `format_inline_comment_body` with suggestion | Body contains `` ```suggestion `` fence |
| Unit: publish skips suggestion when `` ``` `` or `\n` in text | Message-only body |
| Unit: `end_line: 0` normalizes to null | Single-line anchor eligible when `start_line` set |
| Unit: judge sets `skipped_disabled` when candidates + disabled | Mock `judge_llm_enabled` false |
| Unit: `JudgeSkippedBadge` renders when skipped | Vitest |
| Staging (optional) | Inline comment on GitHub shows “Apply suggestion” for one `error` finding |

---

## References

| Path | Role |
|------|------|
| [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) | R6-Q3, R5-Q3 |
| [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) | Suggested fix row — **defer** → this wave |
| `backend/app/services/github_publish.py` | Inline publish |
| `backend/app/services/github_suggestion.py` | Shared suggestion eligibility (P1) |
| `backend/app/services/github_finding_judge.py` | Judge skip behavior |
| `frontend/src/features/reviewer/pages/PullRequestDetailPage.tsx` | Badge placement |

**Next:** [REVIEW_PIPELINE_POLISH_GENERAL_PLAN.md](./REVIEW_PIPELINE_POLISH_GENERAL_PLAN.md) → [waves/](./waves/) P0–P2 execution → `execution-peer-review` → `phase-execution`.
