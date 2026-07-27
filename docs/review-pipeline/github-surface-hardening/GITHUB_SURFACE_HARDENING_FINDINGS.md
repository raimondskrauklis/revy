# GitHub surface hardening — findings

**Purpose:** Baseline for the program after [post-review-quality P0–P4](../post-review-quality/README.md) ([#52](https://github.com/raimondskrauklis/revy/pull/52)). Platform research — **no execution steps**.

**Date:** 2026-07-27  
**Code:** P0–P4 on `main` (`3034c97`). Staging deploy + post-merge dogfood still open.

**Evidence:** PR #52 dogfood ([GITHUB_SURFACE_DOGFOOD.md](../post-review-quality/GITHUB_SURFACE_DOGFOOD.md)), Greptile + Revybot babysit, [CODE_REVIEW_LEARNINGS § Target GitHub surface](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md#target-github-surface-greptile-reference), [PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md).

---

## Build principles

1. **Greptile parity on lifecycle** — if Greptile collapses a thread after a fix, Revy should too (no manual `gh api graphql`).
2. **Publish path owns GitHub threads** — finding inline comments and check/issue comment are one pipeline; no second bot writer.
3. **No track B in this program** — recall, STRUCT, prompts stay deferred (H3).
4. **Verify against code** — cite `file:line`; dogfood rows override stale docs.
5. **Production only** — pagination and batch GraphQL, not silent truncation.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Finding inline thread** | PR review comment on a line, keyed by `GitHubFindingGroupORM.fingerprint` in `publish_job.summary_json.github_inline_threads` |
| **Revybot thread** | Same GitHub object — author is GitHub App (`revybot`); not a separate code path today |
| **Advisory check** | `compute_check_conclusion` → `neutral` for any active finding, `success` when clean (`github_publish.py:162–167`) |
| **Supersede resolve** | `_resolve_superseded_inline_threads` — GraphQL `resolveReviewThread` when group is `superseded`/`resolved` |

---

## 1. Platform question

P0–P4 answered: *does Revy look like Greptile on L1–L3?* **Mostly yes** after #52.

This program answers:

> **When a developer fixes a finding and pushes again, does the PR stay clean — or do stale Revy threads pile up like unresolved homework?**

PR #52 proved the gap: **four Revybot ERROR threads stayed open after fixes** while Greptile auto-resolved. Operator had to run `resolveReviewThread` manually.

---

## 2. What exists vs genuinely new

### Shipped on `main` (verified)

| Capability | Location | Notes |
|------------|----------|-------|
| Advisory check conclusion | `github_publish.py:162–167` | Greptile-class; not merge gate |
| Check name `Revy` | `github_api.py:226` | Display on GitHub checks |
| Issue comment reuse per PR | `find_prior_issue_comment_id_for_pull_request` `github_publish.py:380–409` | Not per-`head_sha` duplicate |
| Inline all severities w/ line | `inline_publish_findings_statement` | error/critical/warning/info |
| Thread map merge (newest wins) | `_load_inline_thread_map` `github_publish.py:249–260` | `for prior in jobs` ascending |
| Supersede resolve on every publish | `_resolve_superseded_inline_threads` before inline post `github_publish.py:734–744` | Even when `post_inline=False` |
| GraphQL thread lookup + resolve | `find_review_thread_id_for_comment`, `resolve_review_thread` `github_api.py:440–538` | `first: 100` / `first: 20` hard cap |
| Comment id validation | `create_pull_request_review_comment` `github_api.py:432` | Rejects `id <= 0` |
| Null-safe GraphQL nodes | `github_api.py:501–503` | Skips non-dict comment nodes |

### Genuinely new (this program)

| Capability | Why new |
|------------|---------|
| **Auto-resolve threads when finding gone/fixed** | Today resolve only when DB group is `superseded`/`resolved`; no diff-based or “not in active publish set” pass |
| **Persist `thread_id` (PRRT_…)** | Map stores REST `comment_id` only; every resolve needs full thread scan |
| **Paginated / batched GraphQL** | Single query; misses threads on busy PRs |
| **Publish integration test harness** | Tests rely on ordered `session.scalars` side_effects — brittle |

### Reuse traps

| Trap | Detail |
|------|--------|
| **Two thread namespaces** | There is only one — `revybot` inline = publish inline. Do not build a parallel “bot review” resolver. |
| **Resolve only on closed groups** | Re-activated finding posts new comment but old thread may stay open if group flickers `active` → `resolved` → `active` without map update |
| **`find_review_thread_id_for_comment` per fingerprint** | N GraphQL round-trips per publish when many closed groups — rate limit risk |
| **Autouse test fixture** | `_publish_formatter_defaults` mocks `_load_prior_inline_thread_map` — hides scalars call-order bugs |

---

## 3. Gap catalog (prioritized)

| ID | Gap | User impact | Code touch | Priority |
|----|-----|-------------|------------|----------|
| **GH-1** | **No auto-resolve when finding fixed** | Stale open threads; PR looks “dirty”; Greptile contrast | `github_publish.py`, maybe new helper | **P0** |
| **GH-2** | **GraphQL pagination** (`first: 100` threads, `first: 20` comments) | Silent miss on large PRs | `github_api.py:460–465` | **P1** |
| **GH-3** | **N+1 GraphQL** in supersede loop | Slow publish; API rate limits | `github_publish.py:318–340` | **P1** |
| **GH-4** | **Same-SHA re-publish** edge cases | Threads not resolved when job re-runs without new inline | `run_publish_job` idempotency | **P2** — verify in dogfood |
| **GH-5** | **Missing `group_id` on finding** | Inline skipped silently | `github_publish.py:758–764` | **P2** |
| **GH-6** | **Brittle publish unit tests** | Regressions slip through | `test_github_publish.py` | **P2** |
| **GH-7** | **Post-merge staging dogfood** | Unvalidated deploy | Ops + dogfood log | **Gate** (human) |

**Out of scope:** recall (H3), STRUCT, RC4 rules, `/reviewer` pipeline tab, human dismiss R7.6.

---

## 4. GH-1 deep dive — auto-resolve (north star)

### Greptile behavior (benchmark)

On each review pass, Greptile compares diff + prior threads → **marks resolved** when it believes the issue is fixed. Threads collapse on GitHub without human action.

### Revy today

```text
publish → load github_inline_threads from prior jobs
       → for group in superseded|resolved: find thread by comment_id → resolveReviewThread
       → post new inline for active findings
```

**Gaps:**

1. **Active finding removed from publish set** (judge dismissed, reconciled away) but group not yet `resolved`/`superseded` — thread stays open.
2. **Code fixed, group still `active`** until next reconcile — thread stays open (Greptile would resolve on diff).
3. **No stored `thread_id`** — must scan all threads per `comment_id` (`github_api.py:456–506`).

### Recommended direction (advice — not execution)

**Phase A (minimal, fingerprint-based):**

- After reconcile, on publish: for each `fingerprint` in `inline_threads`, if no matching **active** group with that fingerprint → resolve thread and pop map.
- Extends current supersede logic beyond `superseded`/`resolved` states.

**Phase B (scale):**

- Store `thread_id` in `github_inline_threads` value (object or parallel map).
- One paginated `reviewThreads` fetch per publish; batch resolve.

**Phase C (Greptile-class, optional later):**

- Diff-aware resolve (line removed or hunk changed) — overlaps track B; defer unless dogfood demands.

---

## 5. GH-2 / GH-3 — GraphQL scale

**Verified:** `find_review_thread_id_for_comment` uses non-paginated `first: 100` / `first: 20` (`github_api.py:460–465`). Returns `None` on `errors` (`github_api.py:479`) — silent skip.

**Verified:** `_resolve_superseded_inline_threads` calls lookup **once per closed group** (`github_publish.py:323`) — O(n) HTTP.

**Advice:** Add `list_review_threads` with cursor pagination; build `databaseId → threadId` index once per publish; reuse for resolve + optional GH-1.

---

## 6. Dogfood evidence (PR #52)

| Observation | Layer | Implication |
|-------------|-------|-------------|
| Greptile Successful; Revy neutral after advisory fix | L1 | Parity achieved |
| JSON body → unwrap fix; single summary comment | L2 | Ship validated |
| Inline threads on later pushes | L3 | Ship validated |
| 4 Revybot threads open after code fix | **Lifecycle** | **GH-1** |
| Greptile auto-resolved P1 thread map bug | Lifecycle | Target behavior |
| Manual `resolveReviewThread` via `gh` | Ops | Not product |

Row: [GITHUB_SURFACE_DOGFOOD.md](../post-review-quality/GITHUB_SURFACE_DOGFOOD.md).

---

## 7. Edge cases

| Case | Risk |
|------|------|
| Finding re-activated after resolve | New inline comment; map must keep **newest** id (fixed #52) |
| Transient GraphQL failure | Pop only after success (fixed #52) — retry on next publish |
| Thread on old commit line after push | GitHub may mark outdated; resolve anyway if fingerprint closed |
| Docs-only PR, no line findings | GH-1 loop no-op; no inline spam |
| Multiple comments same fingerprint historical | Newest wins in `_load_inline_thread_map` |

---

## 8. Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **GH-Q1** | Separate “Revybot resolver” from publish? | **locked** | **No** — one publish path |
| **GH-Q2** | Diff-based resolve in v1? | **locked** | **No** — fingerprint + group state (P1); see general plan |
| **GH-Q3** | Store `thread_id` in summary_json? | **locked** | **Yes** — P2 |
| **GH-Q4** | Track B in this program? | **locked** | **No** |
| **GH-Q5** | Program name / folder | **locked** | `github-surface-hardening` |

---

## 9. Parking lot

- Optional G10 ack snack (Greptile 👀) — was P2 optional in prior program; still defer unless dogfood asks.
- Orphan G10 check if pipeline link fails — log only.
- Email digest — defer.
- Tag `review-github-v1` — after GH-7 dogfood pass.

---

## 10. Devil's advocate

| Risk | Mitigation |
|------|------------|
| Over-resolve threads while finding still active | Only resolve when fingerprint not in active set + explicit state transition |
| GraphQL pagination complexity | Ship GH-1A first with current query; paginate before customer scale |
| summary_json shape change | Version key or migrate on read |
| Test refactor scope creep | GH-6 as own subphase; don’t block GH-1 |

---

## 11. Verification (program done when)

| Check | Pass |
|-------|------|
| Push fix on dogfood PR → Revy thread collapses without manual `gh` | GH-1 |
| PR with >100 threads (simulated or staging) → resolve still finds target | GH-2 |
| Publish with 10 closed groups → ≤2 GraphQL list calls | GH-3 |
| Staging deploy + dogfood row L1/L2/L3 Y | GH-7 |
| Local Bugbot clean on each phase | Process |

---

## 12. References

| Resource | Path |
|----------|------|
| Publish orchestration | `backend/app/services/github_publish.py` |
| GitHub API / GraphQL | `backend/app/integrations/github_api.py` |
| Publish tests | `backend/tests/unit/test_github_publish.py` |
| Prior program dogfood | `docs/review-pipeline/post-review-quality/GITHUB_SURFACE_DOGFOOD.md` |
| Greptile resolve pattern | `docs/review-pipeline/REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md` § Inline comment shape |
| PRODUCT_PATTERNS partial row | `docs/review-pipeline/REVIEW_PIPELINE_PRODUCT_PATTERNS.md` — “Resolve review threads when fixed” |

---

## Next step

1. ~~`create-general-plan`~~ → [GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md](./GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md).
2. `create-execution-plan` → `GITHUB_SURFACE_HARDENING_EXECUTION.md` + P0–P4 execution files.
