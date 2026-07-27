# Code review learnings — GitHub surface, Greptile reference, agent patterns

**Purpose:** Capture (1) what a **useful GitHub PR review** looks like (Greptile on our closed PRs), (2) how **iterative multi-pass** review works in practice, (3) industry / multi-agent patterns worth adopting in Revy, and (4) babysit learnings from the R4–R7 stack. **Not execution steps.**

**Related:** [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) · [REVIEW_PIPELINE_MERGE_CHECKLIST.md](./REVIEW_PIPELINE_MERGE_CHECKLIST.md) · [REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md](./REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md) · [code-review-arch_perplexity_searcj_advice_only.md](./code-review-arch_perplexity_searcj_advice_only.md) (advice only — mined for ideas, not copied as architecture)

**Greptile examples in this repo:** [#35](https://github.com/raimondskrauklis/revy/pull/35) (model-policy M0, 13 review passes) · [#36](https://github.com/raimondskrauklis/revy/pull/36) (clean migration fix, 2 passes)

---

## How to use this file

| Audience | Use |
|----------|-----|
| **Product / R9+ planning** | Target GitHub output shape + agent pipeline backlog |
| **Agents shipping publish UX** | Match Greptile-style summary sections; no mermaid v1 |
| **Humans merging our PRs** | Triage Greptile P0/P1 vs P2; expect multiple review rounds |
| **Babysit workflow** | Cross-subsystem bugs = P1; resolve threads after fix push |

---

## Target GitHub surface (Greptile reference)

Revy today publishes a **compact** check-run summary (`Severity | Category | Title | File`) plus inline comments for error/critical only. Greptile on our PRs shows a richer **top-level PR comment** that is the primary triage surface. That is the bar for a future Revy publish UX (R9+ / polish), not a copy of Greptile vendor config.

### Anatomy of a good PR summary comment

Observed on [#35](https://github.com/raimondskrauklis/revy/pull/35) and [#36](https://github.com/raimondskrauklis/revy/pull/36):

| Section | What it gives the reader | Revy today | Target |
|---------|--------------------------|------------|--------|
| **Narrative summary** | 2–4 sentences: what the PR does, who it affects, major subsystems touched | Partial — table only | **Add** — LLM-generated or template-filled from run metadata |
| **Themed bullets** | Group changes by concern (migrations, pipeline wiring, API, frontend) with file anchors | Missing | **Add** — from review run + changed-file list |
| **Confidence score (0–5)** | Merge triage at a glance; prose explains *why* this score | Missing — check `conclusion` only | **Add** — derived from active finding severities + blocker history on this `head_sha` |
| **Merge verdict** | One line: “Safe to merge” / “Address P1 first” + what was fixed since last pass | Missing | **Add** — compare current vs prior revision findings |
| **Files needing attention** | Short list: `path` — one-line risk statement; “none” when clean ([#36](https://github.com/raimondskrauklis/revy/pull/36)) | Missing | **Add** — top N active groups or “No files require special attention” |
| **Important files changed** | Collapsible table: filename → overview (not just diff stats) | Missing | **Add** — per-file one-liner from indexer or reviewer |
| **Inline threads** | P0/P1/P2 badges, explanation, optional `suggestion` block | **Partial** — error/critical inline only; P2 warnings table-only | **Extend** — configurable inline threshold |
| **Review metadata footer** | Last reviewed commit SHA, re-trigger link, review count | Missing | **Add** — `head_sha`, link to Revy run, `@revy review` hint |
| **Sequence diagram** | Mermaid call flow | N/A | **Skip** — low ROI vs narrative + file table for Revy v1 |

**Design principle:** GitHub is the **triage and action** surface; Revy UI is the **detail and workflow** surface (full message, dismiss/ack, judge outcome). Today’s split (title on GitHub, message in Revy) is intentional but incomplete — we still lack summary narrative and confidence.

### Inline comment shape (actionable)

Greptile inline threads on [#35](https://github.com/raimondskrauklis/revy/pull/35) follow a repeatable pattern Revy should mirror:

1. **Severity badge** — P0 / P1 / P2 (map to `FindingSeverity`)
2. **Title** — short, specific (“Workspace-override credential check uses platform provider”)
3. **Explanation** — why it matters, including cross-file / cross-layer impact
4. **Suggested fix** — fenced `suggestion` block when line-accurate (already in R6 `format_inline_comment_body`)
5. **Resolution** — thread marked resolved on GitHub after fix lands (human or bot)

Example class (P2, resolved after push): `bedrock_review.py` — dead `settings.aws_region` fallback after `_require_bedrock_configured` already guarantees non-empty region.

### Confidence score semantics (industry + Greptile)

Greptile documents [0–5 contextual merge readiness](https://www.greptile.com/docs/code-review/first-pr-review). Useful mapping for Revy:

| Score | Meaning | Typical action |
|-------|---------|----------------|
| **5/5** | No open P0/P1; prior blockers addressed | Merge after human skim |
| **4/5** | P2 only or documented accepted risk | Merge after minor fixes |
| **3/5** | Open P1 or ambiguous cross-layer issue | Fix or discuss before merge |
| **0–2/5** | P0, data loss, security, broken deploy path | Block merge |

Score prose should cite **what changed since last review** (e.g. [#35](https://github.com/raimondskrauklis/revy/pull/35): “All previously flagged blockers … are addressed. Two remaining findings are confined to the display path …”).

---

## Iterative review is expected (not a failure mode)

Greptile does **not** find every issue in one pass. That is normal and desirable.

### [#35](https://github.com/raimondskrauklis/revy/pull/35) chronology (13 Greptile reviews)

| Pass (approx.) | Commit focus | New findings (examples) | Outcome |
|----------------|--------------|-------------------------|---------|
| 1 | Initial M0 stack | P2 dead code in `model_policy.py`; P2 dead region fallback in `bedrock_review.py`; P1 `asyncio.TimeoutError` on review + judge paths; P2 test flag bleed in `config.py` | Threads opened |
| 2 | Alembic fix push | P1 **forked head** — `0022` pointed at `0020` not `0021` | Blocker until fixed |
| 3 | Credential / 503 path | P1 GET model-policy 503 on fresh deploy; P1 workspace override checks platform creds not override provider | Blockers |
| 4 | `require_credentials` threading | P1 catalog validation breaks read path when creds absent | Blocker |
| 5 | Bedrock region hardening | P1 security — arbitrary client-supplied AWS region | Blocker |
| 6+ | Timeout + polish commits | Summary updated; confidence **5/5**; only P2 display-path nits remain | Merged |

**Takeaways for Revy product and process:**

| Lesson | Implication |
|--------|-------------|
| **Review runs on every push** | `synchronize` → re-index → re-review → update summary **in place** (R6-Q1, R8 autostart) |
| **Summary must be revision-aware** | Regenerate narrative + confidence per `head_sha`; call out fixed vs still-open |
| **Not all bugs on loop 1** | Single-shot reviewer will miss cross-layer bugs; judge + second push catch them |
| **Resolve threads when fixed** | Greptile marks threads resolved; confidence on summary comment updates on later passes |
| **P1 blockers can appear late** | Migration graph bug appeared on pass 2, not pass 1 — staging `alembic upgrade head` still essential |
| **Stochastic generators OK** | Precision control is reconcile + judge + publish, not “never comment twice” |

Same pattern on our R4–R7 babysit: Greptile on [#26](https://github.com/raimondskrauklis/revy/pull/26) surfaced publish/judge drift across multiple commits, not one shot.

---

## Greptile on our PRs — what to trust (R4–R7 babysit)

### Trust and fix (P0/P1 — data correctness)

Greptile was **most valuable** on cross-step consistency and async/DB edge cases — exactly where unit tests with mocks miss commit boundaries.

| Theme | Example (fixed) | Why it matters for Revy |
|-------|-----------------|------------------------|
| **Transaction + retry** | R6: flush `github_check_run_id` then rollback on `raise` → duplicate check runs on Celery retry | Publish must persist external IDs before retryable failures |
| **Pipeline stage drift** | R6: inline comments for judge-dismissed (`resolved`) groups | Summary, check conclusion, inline must share **active group** filter |
| **TOCTOU / locking** | R6: two `publish_for_review_run` tasks both create jobs | Auto-trigger = admin path: row lock → commit job → enqueue |
| **Guard missing on auto path** | R6: publish when `github_api_enabled` false | Every enqueue path needs same guards as API |
| **Reconcile correctness** | R5: `_mark_superseded_peers` skipped on fingerprint update | Fingerprints useless if old groups stay `active` |
| **Exception scope** | R5: `ServiceUnavailableError` not caught in judge loop | Per-finding judge failures must not abort reconcile |
| **UI/API contract** | R7: nav probe true with zero PRs; revision from unsorted list | Never assume cursor list order |

**Rule of thumb:** If the finding describes **two subsystems disagreeing** (judge vs publish, DB vs GitHub, UI vs API), treat as P1 until disproven.

### Fix or document (P2 — clarity)

| Theme | Example | Action |
|-------|---------|--------|
| Doc drift in same PR | R23: `external_id` in product patterns vs R6 execution | Lock decisions; cross-link |
| Dead code / misleading fallback | #35: `resolved_region = region or settings.aws_region` after guard | Fix or document invariant |
| Markdown output safety | R6: `\|` in title breaks GitHub table | Escape cells in `build_summary_markdown` |
| Broker gap | R6: `.delay()` fails after DB commit | Inline `publish_review_run.run` fallback |

### Often skip

- Cosmetic doc header style
- Suggestions contradicting locked Q# without new evidence
- Refactors outside PR scope

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
| #26 | P2 | Orphan pending job if broker fails | Inline fallback |
| #26 | P1 | Cross-job inline skip when reusing check run | `existing.inline_comments_posted` gates `post_inline` |
| #26 | P1 | Inline comments for dismissed groups | Join `state=active` |
| #27 | P1 | Nav probe bypass | `false` when no PRs |
| #27 | P1 | Wrong revision from list order | `pickLatestRevisionId` by `updated_at` |
| #27 | P2 | Merge conclusion dead `success` path | `failure` for unknown severity |
| #27 | P2 | GitHub link missing past page 1 | `usePullRequest` scans cursors |
| #35 | P1 | Alembic forked head, 503 on model-policy GET, creds/region bugs | Fixed across 5+ pushes before merge |

---

## Industry patterns → Revy (synthesis)

Sources: [Perplexity notes](./code-review-arch_perplexity_searcj_advice_only.md) (layers 0–7), Greptile docs, Ellipsis/ZenML write-ups, multi-agent orchestrator repos (agent-review-orchestrator, multi-model-code-review-agent), Optibot/Vigil triage patterns. **Extract principles; do not copy vendor stacks wholesale.**

### Pipeline layers (consolidated)

| Layer | What production tools do | Revy today | Recommendation |
|-------|-------------------------|------------|----------------|
| **0 — Ingest** | Webhook → queue; accuracy > latency | R0 + Celery | **Keep**; R8 autostart |
| **1 — Context** | Incremental chunk hash index; optional LSP/symbol tools | Diff-scoped index (review-quality D13); LSP defer v1 | **v1** diff-first + trace; **v1.1** [RQ-STRUCT-1](./review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md); agents R6+ |
| **2 — Generators** | Parallel specialized agents OR shuffled-diff voting; attach **evidence** per claim | Single Moonshot pass (R4) | **R9+** — optional category agents; store evidence snippet |
| **3 — Deterministic pre-filter** | Linters/SAST before LLM | CI + R4-Q5 actionable-only | **Keep** — highest leverage |
| **4 — Judge / filter** | Dedup → confidence → grounding check (claim vs evidence) → format | R5 fingerprint + Anthropic judge | **Extend** grounding judge; near-dup merge |
| **5 — Adversarial second pass** | Devil’s advocate reviews *findings + diff* independently; runs even on zero-finding diffs | Judge only on escalation rules | **Consider** — lightweight DA agent on all `error`/`critical` |
| **6 — Publish** | One structured PR comment + inline; update in place on push | R6 check + summary table + subset inline | **Extend** — Greptile-style sections (above) |
| **7 — Metrics** | Resolution rate at next commit, not raw issue count | Not tracked | **R9** — dismiss/addressed/still-open |

**Design principle (locked):** Generators stay exploratory; precision lives in reconcile + judge + publish. Do not make the primary prompt overly conservative.

### Multi-agent patterns worth adopting

| Pattern | Description | Revy mapping |
|---------|-------------|--------------|
| **Orchestrator + workers** | Thin orchestrator gathers context; specialists review in parallel; synthesizer dedupes | Celery stages today; **future:** parallel R4 generators by category |
| **Isolated reviewer context** | Each agent gets clean context — no prior agent reasoning (avoids bias) | Judge already separate from reviewer; keep judge input = finding + evidence only |
| **Devil’s advocate** | Second agent challenges KEEP / WEAKEN / DROP; can add missed findings | Optional post-R4 agent before reconcile |
| **Cross-model jury** | Different model families; orchestrator refutes, not averages | **Shipped** Moonshot + Anthropic (R4+R5) |
| **Convergence loop** | Re-review after fixes until no blocking findings or “stuck” fingerprint | **Product:** `@revy review` + human fix loop; not autonomous merge |
| **Claims verifier** | PR description claims vs actual diff (Vigil-style) | **Future** — pre-review signal, not finding replacement |
| **Checkpoint before retry** | Commit external IDs before retryable API failure | **Shipped** R6 publish; generalize to review/index |
| **Generator fault isolation** | One crashed parallel agent does not fail whole review | **Future** when multi-generator lands |

### Hallucination taxonomy (filter design)

For code review, prioritize detectors for:

| Mode | Failure | Revy detector |
|------|---------|---------------|
| **Grounding** | Claim contradicts supplied diff/context | Judge vs evidence snippet (R9) |
| **Citation** | Line/file does not support claim | Structural check on `file_path` + line range |
| **Factual** | Wrong API/framework fact | Optional retrieval tool call |
| **Reasoning** | Broken inference chain | Step-wise judge prompt (defer) |

---

## Proposed agent roles (Revy R9+ backlog)

Not shipped — naming for planning and findings doc. Maps to Celery tasks or sub-prompts, not necessarily separate microservices.

| Agent | Input | Output | Stage |
|-------|-------|--------|-------|
| **Context assembler** | PR diff, `head_sha`, index chunks | Retrieval set + per-file one-liners | Pre-R4 |
| **Logic / security reviewer** | Diff + retrieval | Raw findings + evidence | R4 parallel |
| **Maintainability reviewer** | Diff + tests touched | Raw findings (optional profile) | R4 parallel |
| **Claims checker** | PR body + diff stat | Warnings only (undocumented deps, env vars) | Pre-R4 or post |
| **Dedup synthesizer** | Raw findings | Merged candidate list | Pre-R5 |
| **Judge** | Finding + evidence | dismiss / escalate / severity | R5 **shipped** |
| **Devil’s advocate** | Diff + candidate findings | KEEP / WEAKEN / DROP + gaps | R5+ optional |
| **Publisher formatter** | Active groups + PR metadata | GitHub summary markdown + inline set | R6 **extend** |
| **Resolution tracker** | Prior `head_sha` findings vs new diff | Metrics + “fixed since last review” prose | R9 |

---

## Revy GitHub publish — gap vs target

| Item | Status | Phase |
|------|--------|-------|
| Check run + summary table | **shipped** R6 | — |
| Inline error/critical + suggestion | **shipped** R6 | — |
| Update check/summary in place per `head_sha` | **shipped** R6-Q1 | — |
| Narrative PR summary | **gap** | R9 / publish polish |
| Confidence 0–5 + merge verdict prose | **gap** | R9 |
| Files needing attention list | **gap** | R9 |
| Important files changed table | **gap** | R9 |
| Revision-aware “fixed since last review” | **gap** | R9 |
| P2 inline (configurable) | **gap** | policy |
| Message snippet in summary table | **gap** (low) | R6 UX |
| Email digest | **defer** | post-R7 |

---

## Product backlog (cross-cutting)

| Lesson | Revy improvement | Status |
|--------|------------------|--------|
| **GitHub = triage, Revy = detail** | Rich summary comment; keep deep link to `/reviewer` | **gap** |
| **One source of truth for “what to show”** | Publish, check, UI filter same `active` groups | **shipped** R6 |
| **Persist before retry** | External API IDs committed before retryable work | **shipped** R6 |
| **Auto path = admin path** | Same locks/guards on autostart | **shipped** R6/R8 |
| **Evidence for claims** | Store retrieved snippet on finding row | **defer** R9 |
| **Resolution metric** | Re-check at next revision | **defer** R9 |
| **Incremental index** | Hash chunks; embed diff only on `synchronize` | **defer** R9 |
| **Dedup before publish** | Fingerprint + near-duplicate merge | **partial** R5 |
| **Deterministic pre-filter** | CI owns style; Revy logic/security | **locked** R4-Q5 |
| **Cross-model judge** | Moonshot + Anthropic | **shipped** R5 |
| **GET single PR** | Detail page without list scan | **defer** R7.1 |
| **Publish–UI parity tests** | `resolved` never in inline export | **defer** |

---

## Process learnings (this repo)

| Practice | Verdict |
|----------|---------|
| **Babysit per PR in stack order** | Required — lower PR fixes rebase up |
| **P1 = data correctness** | Fix before merge |
| **Expect multiple Greptile / Revy passes** | Normal; late P1s (migrations, creds) are why we re-review on push |
| **Resolve GitHub threads after fix** | So confidence and open-thread count reflect current head |
| **Small PRs / one concern** | Higher signal per pass |
| **Greptile complement, not substitute** | Staging e2e still required ([smoke validation](./REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md)) |
| **Optional Greptile on our PRs** | Use for cross-layer bugs; ignore cosmetic P2 when merging |

---

## Open gaps

| Gap | Owner | When |
|-----|-------|------|
| Diff-first review + pipeline trace | **D + O** | [Review quality findings](./review-quality/REVIEW_QUALITY_FINDINGS.md) — **R1** |
| Rich GitHub summary (Greptile-shaped) | Track G | [Review quality findings](./review-quality/REVIEW_QUALITY_FINDINGS.md) — R3 |
| Incremental index on `synchronize` | Track I | [Review quality findings](./review-quality/REVIEW_QUALITY_FINDINGS.md) — R2 |
| Evidence + grounding judge | Track E | [Review quality findings](./review-quality/REVIEW_QUALITY_FINDINGS.md) — R4 |
| Multi-generator + DA agent | Track A | [Review quality findings](./review-quality/REVIEW_QUALITY_FINDINGS.md) — R6+ |
| Resolution / dismiss analytics | Track M | [Review quality findings](./review-quality/REVIEW_QUALITY_FINDINGS.md) — R5 |
| Staging e2e matrix | Ops | [merge checklist](./REVIEW_PIPELINE_MERGE_CHECKLIST.md) |
| `GET …/pull-requests/{id}` | R7.1 | API |

---

## PR review context (Greptile + Bugbot dogfood)

When shipping **large program PRs** (code + planning docs), wire bots to the **execution contract** — not only the diff.

| Practice | Detail |
|----------|--------|
| **Greptile** | `.greptile/files.json` — execution + findings; `scope` matches touched paths |
| **Bugbot** | `.cursor/BUGBOT.md` — links to same docs |
| **When** | First phase commit (RQ0); `phase-execution` skill enforces |
| **Per-phase commits** | Code + minimal README status — avoid re-editing full findings each push |
| **Post-v1** | [REVIEW_QUALITY_REVIEW_CONTEXT.md](./review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) — RQ-RC-1 (scoped subsets, active slice pointer) |

**Lesson from planning:** Greptile/Bugbot catch **intent vs implementation** drift (wrong routes, missing columns) when wired; without wiring, `.md` in diff is ignored as spec.

---

## References

| Path | Role |
|------|------|
| [review-quality/REVIEW_QUALITY_FINDINGS.md](./review-quality/REVIEW_QUALITY_FINDINGS.md) | Review quality baseline — diff-first + trace + GitHub |
| [review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md](./review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) | Greptile/Bugbot planning-doc wiring — RC track |
| [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) | Locked Q# + domain states |
| [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) | Pattern → phase map |
| [REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md](./REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md) | Staging e2e + infra learnings |
| [code-review-arch_perplexity_searcj_advice_only.md](./code-review-arch_perplexity_searcj_advice_only.md) | External architecture notes |
| [REVIEW_PIPELINE_GREPTILE_PR26_EMAIL.md](./REVIEW_PIPELINE_GREPTILE_PR26_EMAIL.md) | Archived Greptile email artifact |
| [Greptile first PR review docs](https://www.greptile.com/docs/code-review/first-pr-review) | Public anatomy of summary + confidence + inline |
