# Code review learnings — Greptile babysit + industry patterns

**Purpose:** Capture what we learned babysitting the R4–R7 PR stack (#23–#27), how to use external AI review on **this repo**, and product improvements for Revy itself. **Not execution steps.**

**Related:** [REVIEW_PIPELINE_MERGE_CHECKLIST.md](./REVIEW_PIPELINE_MERGE_CHECKLIST.md) · [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) · [code-review-arch_perplexity_searcj_advice_only.md](./code-review-arch_perplexity_searcj_advice_only.md) (advice only, not tasks)

---

## How to use this file

| Audience | Use |
|----------|-----|
| **Agents shipping R8+** | Product backlog + pitfalls to avoid in our own pipeline |
| **Humans merging R4–R7** | What Greptile caught that was real; what to ignore |
| **Product** | Prioritize improvements that reduce false positives and publish drift |

---

## Greptile PR #27 (R7 reviewer UI) — latest

**Confidence:** **4/5** (UI safe; inline Celery fallback tightened)

| Finding | Severity | Status | Notes |
|---------|----------|--------|-------|
| `FindingRow` missing `state` column | P2 UX | **fixed locally** | Shows `active` / `superseded` / `resolved` (EN+LV) |
| `usePullRequest` unbounded pagination | P2 UX | **fixed locally** | `MAX_PULL_REQUEST_SCAN_PAGES` (50); proper fix = `GET …/pull-requests/{id}` |
| Inline fallback `CancelledError` → stuck `processing` | P1 | **fixed locally** | `_finalize_inline_publish_failure` + re-raise on cancel (SIGTERM / deploy) |

**Takeaway:** R7 UI is additive; publish `create_task` path needs **BaseException** awareness — fire-and-forget ≠ sync `run()`.

---

## Greptile on our PRs — signal quality

### Trust and fix (P0/P1 — data correctness)

Greptile was **most valuable** on cross-step consistency and async/DB edge cases — exactly where unit tests with mocks often miss commit boundaries.

| Theme | Example (fixed) | Why it matters for Revy |
|-------|-----------------|------------------------|
| **Transaction + retry** | R6: flush `github_check_run_id` then rollback on `raise` → duplicate check runs on Celery retry | Our publish loop must persist external IDs before retryable failures |
| **Pipeline stage drift** | R6: inline comments posted for judge-dismissed (`resolved`) groups | Summary, check conclusion, and inline publish must share the same **active group** filter |
| **TOCTOU / locking** | R6: two `publish_for_review_run` tasks both create jobs | Auto-trigger must match admin path: row lock → commit job → enqueue |
| **Guard missing on auto path** | R6: publish enqueued when `github_api_enabled` false | Every enqueue path needs the same guards as the API |
| **Reconcile correctness** | R5: `_mark_superseded_peers` skipped on fingerprint update path | Stable fingerprints are useless if old groups stay `active` |
| **Exception scope** | R5: `ServiceUnavailableError` not caught in judge loop → full reconcile rollback | Per-finding judge failures must not abort reconcile |
| **UI/API contract** | R7: nav probe true with zero PRs; revision picked from unsorted list | Never assume cursor list order; probe the actual API surface |

### Fix or document (P2 — clarity)

| Theme | Example | Action taken |
|-------|---------|--------------|
| Doc drift in same PR | R23: `external_id` in product patterns vs R6 execution | Lock decisions in one place; cross-link |
| Ambiguous lifecycle | R6: PR comment per `head_sha` vs PR-scoped | Documented per-SHA create/update (R6-Q1 scoped) |
| Dead code / intent | R5: `judge_review_run` never enqueued | Documented inline judge; queue reserved for fan-out |
| Markdown output safety | R6: `\|` in finding title breaks GitHub table | Escape table cells in `build_summary_markdown` |
| Broker gap | R6: `.delay()` fails after DB commit | `dispatch_publish_review_run` inline fallback |

### Often skip (unless team agrees)

- Cosmetic doc header style (execution file path comments) — low user impact
- Suggestions that contradict locked Q# without new evidence
- “Use a bigger abstraction” refactors outside the PR scope

**Rule of thumb:** If the finding describes **two subsystems disagreeing** (judge vs publish, DB vs GitHub, UI vs API), treat as P1 until disproven.

---

## Fixed issues catalog (babysit pass 2026-07-26)

| PR | Severity | Issue | Resolution |
|----|----------|-------|------------|
| #23 | P1 | Stale `external_id` in product patterns | Locked `revy:{github_installation_id}:…` |
| #23 | P2 | PR comment lifecycle unclear | Per-`head_sha` documented |
| #25 | P2 | Judge task vs inline judge | Documented; inline in reconcile |
| #25 | P1 | Supersede peers on update path | `_mark_superseded_peers` in else branch |
| #25 | P1 | Judge exception rolls back reconcile | Catch `ServiceUnavailableError` |
| #26 | P1 | Summary footer counts superseded groups | Count `active` only |
| #26 | P1 | Publish without GitHub API | `github_api_enabled` guard on enqueue |
| #26 | P1 | Celery retries dead (swallowed HTTP errors) | `PublishJobRetryableError` + checkpoint commit |
| #26 | P2 | Inline 422 fails whole publish | Per-comment try/except |
| #26 | P2 | Markdown pipe in cells | `_escape_markdown_table_cell` |
| #26 | P2 | Orphan pending job if broker fails | Inline `publish_review_run.run` fallback |
| #26 | P1 | Cross-job inline skip when reusing prior check run | `existing.inline_comments_posted` gates `post_inline` (R6-DEFER-01) |
| #26 | P1 | Inline comments for dismissed groups | Join `github_finding_groups` `state=active` |
| #27 | P1 | Nav probe bypass | `false` when no PRs to probe |
| #27 | P1 | Wrong revision from list order | `pickLatestRevisionId` by `updated_at` |
| #27 | P2 | Merge conclusion dead `success` path | `failure` for unknown severity |
| #27 | P2 | GitHub link missing past page 1 | `usePullRequest` scans cursors |

### Open / deferred (verify before closing)

| ID | Severity | Issue | Status | Where to verify |
|----|----------|-------|--------|----------------|
| R6-DEFER-01 | P1 | Inline permanently skipped when Job B reuses Job A’s check run but Job A never posted inline | **fixed** | `test_run_publish_job_posts_inline_when_prior_job_failed_before_inline` |

---

## What Revy should do better (product backlog)

Lessons from **building** a review product while **using** Greptile on our PRs.

| Lesson | Revy improvement | Status |
|--------|------------------|--------|
| **One source of truth for “what to show”** | Publish, check conclusion, and UI must all filter the same group set (`active` only) | **shipped** R6 fix; add regression test in staging |
| **Persist before retry** | Any step that calls an external API with an idempotent key must commit IDs before retryable work | **shipped** R6 checkpoint; pattern for R8 automation |
| **Auto path = admin path** | Reconcile → publish uses same locking/enqueue as `POST …/publish` | **shipped** R6 |
| **Judge is optional but reconcile is not** | Document + monitor when `ANTHROPIC_API_KEY` unset (R5-Q3) | **shipped** — judge skipped badge on `/reviewer` PR detail (polish P2) |
| **Evidence for claims** | Findings have `file_path` + line; add explicit **evidence snippet** on row for judge grounding | **defer** R9 — see Perplexity Layer 2 |
| **Resolution metric** | Track dismiss / addressed / still-open at next revision — not raw finding count | **defer** R9 analytics |
| **Incremental index** | Hash chunks; re-embed only changed chunks on `synchronize` | **defer** R9 — Perplexity Layer 1 |
| **Deduplication before publish** | R5 fingerprints groups; consider generator-level dedupe before judge | **partial** R5 |
| **Deterministic pre-filter** | CI owns style; Revy owns logic/security — never duplicate linter noise | **locked** R4-Q5 |
| **Cross-model judge** | Moonshot generate + Anthropic judge (different families) | **shipped** R5 |
| **GET single PR** | Detail page should not scan PR list pages | **defer** R7.1 API `GET …/pull-requests/{id}` |
| **Publish–UI parity tests** | Contract test: if group `resolved`, never in inline export set | **defer** add to `test_github_publish.py` |

---

## Industry patterns (Perplexity) → Revy map

Source: [code-review-arch_perplexity_searcj_advice_only.md](./code-review-arch_perplexity_searcj_advice_only.md). **Advice only** — mapped to phases, not committed work.

| Industry pattern | Revy today (R0–R7) | Recommendation |
|------------------|-------------------|----------------|
| **Async queue, accuracy > latency** | Celery per stage; manual admin trigger | **Keep**; R8 **autostart** on `opened` / `synchronize` |
| **Incremental chunk hash index** | Full re-index per revision (R3) | **R9** — embed diff for `synchronize` only |
| **LSP / symbol lookup** | Embedding retrieval only | **Defer** until staging recall gaps |
| **Parallel specialized generators** | Single Moonshot pass (R4) | **R8+** optional multi-generator by category |
| **Evidence attached to findings** | file + line + message | **R9** store retrieved snippet used in prompt |
| **Dedup filter** | R5 fingerprint per PR | **Keep**; add near-duplicate merge in judge input |
| **Grounding / hallucination judge** | R5 Anthropic judge on severity rules | **Extend** — judge checks claim vs evidence snippet |
| **Static pre-filter** | CI + R4-Q5 actionable-only | **Keep** — highest leverage per Perplexity |
| **Cross-model jury** | Moonshot + Anthropic (R4+R5) | **Keep** — avoid same-family judge |
| **Checkpoint commit before retry** | R6 publish surface | **Generalize** to review/index workers |
| **Resolution rate metric** | Not tracked | **R9** — re-check at next revision |
| **Hookdeck / delivery reliability** | `github_webhook_deliveries` dedupe | **Keep**; optional replay sweep job |
| **Config-driven custom rules** | `workspace_review_policy` (future) | **R8+** DB-backed rules EN+LV |

**Design principle we already follow:** generators (R4) can be exploratory; precision control lives in reconcile + judge + publish (R5–R6). **Do not** make the primary prompt overly conservative — fix downstream.

---

## Process learnings (this repo)

| Practice | Verdict |
|----------|---------|
| **Babysit per PR in stack order** | Required — lower PR fixes must rebase up |
| **P1 = data correctness** | Fix before merge; aligns with our own `FindingSeverity.error` |
| **Small PRs / stacked phases** | Greptile quality higher when scope is one concern |
| **Optional Greptile on our PRs** | Useful complement; not a substitute for staging e2e |
| **Audit PR (never merge)** | Still valid for full-phase retrospective |
| **Resolve threads on GitHub** | Mark fixed after push so score/confidence reflects current head |
| **Greptile email artifact** | PR summary + confidence + sequence diagram — archive in [GREPTILE_PR26_EMAIL](./REVIEW_PIPELINE_GREPTILE_PR26_EMAIL.md) |

---

## Open gaps (post-babysit, pre-merge)

| Gap | Owner | When |
|-----|-------|------|
| Close or fold **#23** vs docs on **#27** | Human | Before merge |
| Staging e2e matrix ([merge checklist](./REVIEW_PIPELINE_MERGE_CHECKLIST.md) Phase 4) | Ops | After merge |
| `GET …/pull-requests/{id}` for reviewer detail | R7.1 / R8 | Product |
| Regression: dismissed group never inline-published | Test | Small follow-up on R6 branch or R8 |
| Incremental index on `synchronize` | R9 | [Q11](./REVIEW_PIPELINE_FINDINGS.md) deferred scope |
| **Autostart** (PR open + push) + **`@revy review`** on-demand | R8 | [Q11](./REVIEW_PIPELINE_FINDINGS.md); Greptile/Bugbot parity |
| Resolution / dismiss analytics | R9 | After R7 dismiss flows |

---

## References

| Path | Role |
|------|------|
| [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) | Locked Q# + domain states |
| [REVIEW_PIPELINE_MERGE_CHECKLIST.md](./REVIEW_PIPELINE_MERGE_CHECKLIST.md) | Merge gates |
| [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) | Pattern → phase map |
| [code-review-arch_perplexity_searcj_advice_only.md](./code-review-arch_perplexity_searcj_advice_only.md) | External architecture notes |
