# Review pipeline — product patterns (reference map)

**Purpose:** Catalog **good patterns** from the AI code-review category (Greptile is the primary public reference) and map each to **Revy’s phase + status**. Nothing here is dropped — items are **shipped**, **in flight**, **planned**, or **deferred**.

**Not in scope:** Greptile vendor config (`.greptile/`, `greptile.json`) in **customer** repos — Revy owns product behavior via DB + workspace policy. **Exception:** this **Revy repo** uses `.greptile/files.json` for dogfood during program PRs ([review context](./review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md)).

**Priority:** R4–R7 implemented on PR stack [#24](https://github.com/raimondskrauklis/revy/pull/24)–[#27](https://github.com/raimondskrauklis/revy/pull/27); merge to `main` then iterate on deferred rows.

**Locks:** [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) Q-registry · **Babysit learnings:** [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) · **Handoff:** [REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](./REVIEW_PIPELINE_RECOVERY_CHECKLIST.md)

**Greptile public docs (reference only):** [greptile.com/docs](https://www.greptile.com/docs/code-review/greptile-config) — strictness, comment types, triggers, output sections.

---

## How to read this file

| Status | Meaning |
|--------|---------|
| **shipped** | On `main` today |
| **in flight** | Implemented on PR stack; tag `review-r*-v*` after merge to `main` |
| **defer** | Valuable; after adjacent phases or needs product data |
| **future** | Post-R7 / R8+ or separate program |

---

## Context & retrieval

| Pattern | Greptile-style reference | Revy approach | Status |
|---------|-------------------------|---------------|--------|
| Repo-wide context beyond diff | Graph / symbol index + agent swarm | R3 pgvector chunks + R4 lens retrieval | **shipped** (R3–R4) |
| Full call graph | Deterministic cross-file callers | Embeddings + judge v1; **RQ-STRUCT-1** grep/import bridge v1.1; graph/agent v2 | **defer** v1 — [structural context](./review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |
| Reranker on retrieval | N/A (graph-heavy) | API/local reranker (`R3-Q3`) | **defer** |
| Auto-ingest rule files | Reads `CLAUDE.md`, `.cursor/rules` | Workspace/repo context attachments in policy | **future** (R8+ policy) |
| External tool context | Jira, Notion connectors | Integration layer post-core | **future** |

**Bet for R4–R6:** semantic retrieval + judge beats building call-graph parity on day one. **Updated (review-quality):** still true for v1; cross-file recall via [RQ-STRUCT-1](./review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) before Greptile “impact beyond diff” claims.

---

## Review output & signal

| Pattern | Greptile-style reference | Revy approach | Status |
|---------|-------------------------|---------------|--------|
| High-signal findings | `commentTypes`: logic default; style optional | R4-Q5: logic/security/behavior only; CI owns lint | **shipped** |
| Severity / strictness | `strictness` 1–3 | `ReviewProfile` standard / deep / critical + Kimi tier | **shipped** |
| P0–P2 on PRs (dev process) | Inline severity badges | Map to `FindingSeverity`; use in our PR workflow | **shipped** schema · process now |
| PR summary narrative | Top-level review comment | G3: compact check `output.summary`; Greptile-shaped issue comment (`build_pr_review_comment_fallback` / optional Moonshot) | **shipped** |
| Inline file+line comments | Review comments on diff | R6 inline for error/critical/warning/info when `file_path` + line; table for all severities | **shipped** |
| Suggested fix / patch | Copy-prompt, suggestion blocks | Optional `suggestion` on finding; GitHub suggestion when line-accurate | **shipped** (`R6-Q3` polish) |
| Issues table in review | `includeIssuesTable` | R7 findings table + R6 summary markdown | **shipped** |
| Sequence / ER diagrams | `includeSequenceDiagram` | Summary markdown diagrams | **future** |
| Numeric confidence 0–5 | `includeConfidenceScore` | `compute_confidence` on issue comment + check summary (0–5) | **shipped** |
| Merge readiness | Check state + optional score | Check run `conclusion` + R7 badge (R6-Q2) | **shipped** |
| Email digest on review | GitHub notification with summary + confidence | In-app + GitHub surface only v1; email **defer** | **defer** post-R7 |

---

## Stability across pushes (core differentiator)

| Pattern | Greptile-style reference | Revy approach | Status |
|---------|-------------------------|---------------|--------|
| Same issue every re-review | Learning + dedupe over time | R5 fingerprints + supersede / resolve | **shipped** |
| Idempotent GitHub surface | Known pain: new summary comment each push | R6-Q1: update check run + summary **in place**; **per-PR** issue comment reuse across pushes (#52) | **shipped** |
| Resolve review threads when fixed | Greptile auto-resolves inline threads | Option A: resolve when fingerprint ∉ current-run publishable findings; superseded/resolved groups; GraphQL `resolveReviewThread` | **shipped** |
| Check run **in progress** on PR | Greptile/Bugbot show spinner while reviewing | **G10:** `in_progress` at pipeline start (`start_pipeline_github_check`); `completed` at publish; reuses same check run id | **shipped** |
| Human dismiss / ack | Resolve threads, 👍/👎 | R7 execution **deferred** dismiss/ack → **R7.6**; judge `resolved` exists | **defer** — [review-quality peer review](./review-quality/REVIEW_QUALITY_PEER_REVIEW.md) M2 |
| Learn from team comments | Memory from PR comments, reactions, commits | Post-R7 analytics + optional rule suggestions | **future** (R8+) |
| Inferred custom rules | AI-generated rules from behavior | `workspace_review_policy` suggestions | **future** (R8+) |
| Precision metrics | Internal addressed-rate tracking | **Review quality** M2 — diff + `judge_dismissed`; human dismiss R7.6 | **in flight** — [execution](./waves/REVIEW_QUALITY_EXECUTION.md) |

---

## Triggers & automation

| Pattern | Greptile-style reference | Revy approach | Status |
|---------|-------------------------|---------------|--------|
| **Autostart on PR open** | Default auto-review (no `@` needed) | R8: `pull_request.opened` → full pipeline | **shipped** R8 |
| Review on every commit | `triggerOnUpdates: true` | R8: `pull_request.synchronize` → index → review → reconcile → publish | **shipped** R8 |
| **On-demand `@` commands** | `@greptile` / `@cursor` comment | R8: **`@revy review`** on PR comment → re-run pipeline; `@revy index`, `@revy publish` → **future** | **shipped** (`@revy review` only) |
| Manual-only reviews | `skipReview: "AUTOMATIC"` | Workspace `review_autostart_enabled=false`; admin index `trigger_source=manual` | **shipped** R8 |
| Admin re-trigger | N/A | `POST …/index`, `…/review`, `…/publish` (existing) | **shipped** |
| Draft PR reviews | `triggerOnDrafts` | Workspace setting | **future** |
| Label / path filters | Ignore patterns, directory rules | Repo path filters in workspace policy | **future** (R8+) |
| `push` re-index / re-review | Product marketing | `push` handler stub; automation unowned | **defer** (R8) |

---

## Configuration & tenancy

| Pattern | Greptile-style reference | Revy approach | Status |
|---------|-------------------------|---------------|--------|
| Custom rules in plain English | `.greptile/rules`, cascading dirs | `workspace_review_policy` in DB (EN+LV) | **future** (R8+) |
| Planning-doc context for reviewers | Greptile `files.json` + rules | Dogfood: RC0 in RQ0; product: RC4 `.revy/rules` | **in flight** (RC0) / **future** (RC4) |
| Per-directory strictness | Cascading `.greptile/` overrides | Repo/path-scoped policy rows | **future** |
| Workspace SaaS + audit | Limited in vendor SaaS | Workspace tenancy + `record_audit` on review trigger | **shipped** |
| Plan / volume gates | Credits per seat | Q9 plan gates after R4 cost data | **defer** |

---

## Advanced (separate programs)

| Pattern | Greptile-style reference | Revy approach | Status |
|---------|-------------------------|---------------|--------|
| Sandbox test generation (T-REX) | Agent writes/runs tests per PR | Out of R0–R7 scope | **future** / separate program |
| MCP / editor-native review | Greptile MCP server | Revy API + future MCP when publish stable | **future** |
| Multi-agent “swarm” | Parallel specialized agents | R4 staged pipeline; R5 judge as cross-check | **shipped** |

---

## Industry patterns (Perplexity notes — advice only)

Source: [code-review-arch_perplexity_searcj_advice_only.md](./code-review-arch_perplexity_searcj_advice_only.md). Mapped in [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md).

| Pattern | Industry reference | Revy approach | Status |
|---------|-------------------|---------------|--------|
| Async queue-first (accuracy > latency) | Hookdeck + workflow queue | Celery per stage; webhook never blocks on GitHub API | **shipped** |
| Incremental chunk hash index | SHA chunk IDs; embed diff only | Full re-index per revision (R3) | **defer** R9 |
| Evidence attached at generation | Snippet link per finding | `file_path` + line; no stored evidence blob | **defer** R9 |
| Grounding / citation judge | Claim vs evidence entailment | R5 Anthropic judge on severity rules | **partial** — extend grounding R9 |
| Static pre-filter before LLM | 50+ analyzers (CodeRabbit) | CI owns style; R4-Q5 actionable-only | **shipped** policy |
| Cross-model jury | Different families for gen vs judge | Moonshot R4 + Anthropic R5 | **shipped** |
| Shuffled-diff majority voting | Bugbot multi-pass same model | Not planned | **future** eval only |
| Resolution-rate metric | Re-check at next revision | Dismiss flows R7; analytics R9 | **future** |
| Agentic tool loop mid-review | Bugbot go-to-definition tools | Retrieval-only R4; LSP sidecar | **defer** |
| Checkpoint commit before retry | Idempotent external IDs | R6 publish surface | **shipped** — generalize R8 |

---

## Dev workflow patterns (borrow now — not product features)

Use while building Revy; optional external review on our PRs (Greptile today) for extra signal.

| Practice | Why | Revy-native equivalent (when ready) |
|----------|-----|-------------------------------------|
| Retrospective audit PR (never merge) | Full-phase review without polluting `main` | Keep; later: Revy audit on release branches |
| One concern per fix PR | High signal, easy babysit | Keep |
| Small PRs / subphases | Better defect detection | R4 execution subphases |
| Logic vs style separation | Less noise | R4-Q5 + CI |
| Babysit until review clean | Close P1 before merge | `/babysit-pr` skill |
| Severity-triage fixes | Focus velocity | P0/P1 before merge during sprints |

**External review:** Greptile (or similar) on **this repo’s PRs** is optional and complementary — not a substitute for shipping Revy’s own publish loop (R6).

---

## Revy “do better” bets (vs common complaints)

| Market pain | Revy response | Phase |
|-------------|---------------|-------|
| Comment spam on every push | Idempotent publish (R6-Q1) | R6 |
| False positives / generic advice | R5 cross-family judge; actionable-only R4 | R4–R5 |
| No tenant / audit story | Workspace-scoped findings + audit | R4/R7 |
| Vendor-owned rules file | DB-backed `workspace_review_policy` | R8+ |
| Opaque merge readiness | Severity-derived check conclusion + UI badge | **Advisory** check (`neutral`/`success`); UI `deriveMergeConclusion` mirrors (#52) | **shipped** |

---

## When to update this file

- After each phase tag (`review-r*-v*`) — move rows to **shipped**
- When locking new Q# in findings — add or upgrade a row here
- When deferring scope — **defer** / **future**, never delete the pattern

---

## R6 execution decisions (locked in implementation)

| Topic | Resolution |
|-------|------------|
| Check run name | **`Revy Review`** (was `revy/review`) |
| Check conclusion | **Advisory** — `neutral` if any active findings; `success` if clean; `failure` only on pipeline errors |
| `external_id` | `revy:{github_installation_id}:{github_pr_number}:{head_sha}` on first create (`github_installation_id` = GitHub numeric id); reuse GitHub check run id on update |
| Inline v1 subset | `error` + `critical` + `warning` + `info` with valid line range; table for all severities |
| Summary PR comment | Update **one issue comment per PR** (`find_prior_issue_comment_id_for_pull_request`) |
| Inline thread map | `github_inline_threads` v2 `{comment_id, thread_id?}` in `summary_json`; paginated `list_review_threads` + index-backed resolve; Option A auto-resolve when fingerprint ∉ current-run publishable set |
| New revision | New check run for new `head_sha`; do not mutate prior SHA’s check |
