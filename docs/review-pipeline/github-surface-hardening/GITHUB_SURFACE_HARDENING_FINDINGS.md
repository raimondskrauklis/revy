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
| **GH-1** | **No auto-resolve when finding fixed** | Stale open threads; PR looks “dirty”; Greptile contrast | `github_publish.py` | **program P1** |
| **GH-1b** | **`summary_json` not persisted after resolve when `post_inline=False`** | Same-SHA re-resolve loops; stale map in DB | `github_publish.py:734–801` | **program P1** (with GH-1) |
| **GH-2** | **GraphQL pagination** (`first: 100` threads, `first: 20` comments) | Silent miss on busy PRs — **correctness**, not only perf | `github_api.py:460–465` | **program P2** |
| **GH-3** | **N+1 GraphQL** in supersede loop | Slow publish; API rate limits | `github_publish.py:318–340` | **program P2** |
| **GH-4** | **Same-SHA re-publish idempotency** | Re-run publish without new inline | `run_publish_job` | **program P3** — verify after GH-1b |
| **GH-5** | **Missing `group_id` on finding** | Inline skipped silently | `github_publish.py:758–764` | **program P3** |
| **GH-6** | **Brittle publish unit tests** | Regressions slip through | `test_github_publish.py` | **program P4** (P1 adds direct resolve tests) |
| **GH-7** | **Post-merge staging dogfood** | Unvalidated deploy | Ops + dogfood log | **Gate** — after P1 for GH-1 proof |

**Out of scope:** recall (H3), STRUCT, RC4 rules, `/reviewer` pipeline tab, human dismiss R7.6.

---

## 4. GH-1 deep dive — auto-resolve (north star)

### #52 root cause (peer-reviewed, verified)

PR #52 threads stayed open **after code fix** because:

1. **Reconcile does not close absent groups** — `reconcile_review_run` only iterates findings in the current run (`github_finding_reconcile.py:110–180`). When the LLM stops emitting a finding, the group stays **`active`** with a stale `last_seen_revision_id`.
2. **Resolve only queries `superseded`/`resolved`** — `_resolve_superseded_inline_threads` (`github_publish.py:305–316`) never sees those groups.
3. **“No active group” is the wrong trigger** — #52 groups were still **active**; they were simply **absent from the new review run**.

### Greptile behavior (benchmark)

On each review pass, Greptile re-evaluates the diff and **collapses threads** it believes are fixed — without waiting for DB `group.state` to change.

### Revy today

```text
publish → load github_inline_threads from prior jobs
       → for group in superseded|resolved ONLY: resolve thread
       → post new inline for active findings in current run
```

### Locked v1 resolve trigger (GH-Q6)

**Option A (primary):** resolve when `fingerprint` is in `inline_threads` but **not** in the current `review_run_id` publishable finding set (`inline_publish_findings_statement` fingerprints). Run-scoped — not new diff logic.

**Also keep:** existing resolve for groups in `superseded`/`resolved` state.

**Explicitly not v1:**

| Option | Why deferred (v1) | v2 status |
|--------|-------------------|-----------|
| **B** — `resolution_status == addressed` | Diff-based signal already exists (`github_resolution_metrics.py:139–194`) but does not change `group.state`; adopting it is a second trigger — consider post-v1 alignment only | **Shipped (GH-Q9)** — see §4c |
| **C** — reconcile marks absent groups resolved | Fixes check/summary too but is reconcile scope change — out of this program | Still reconcile-only (finding-resolution P1–P2) |

**v1 scope for check/summary (GH-Q7):** GH-1 **collapses GitHub threads only**. Active groups absent from the new run may still appear in check/summary until reconcile changes (separate program). Do not block GH-1 on reconcile.

### GH-1v2 — collapse triggers (shipped post P4)

**Motivation:** Dogfood PRs ([#52](https://github.com/raimondskrauklis/revy/pull/52), [#53](https://github.com/raimondskrauklis/revy/pull/53), [#61](https://github.com/raimondskrauklis/revy/pull/61)) showed Greptile threads collapsing while Revybot threads stayed open: Moonshot **re-reported** fixed findings (Option A never fired), and **line drift** left outdated threads unresolved.

**Where (code):**

| Piece | Location |
|-------|----------|
| Resolve criteria | `_fingerprints_to_resolve_inline_threads()` → `github_publish.py` |
| GraphQL resolve + map pop | `_resolve_stale_inline_threads()` → same module |
| Thread index (`isOutdated`, `isResolved`) | `build_review_thread_index()` → `github_api.py` |
| When it runs | Publish flush only — `run_publish_job` → `_flush_publish_surface` (Celery `publish_review_run`). **Not** a GitHub Action or `synchronize` webhook. |

**Flush order (unchanged):** `build_review_thread_index` → `_resolve_stale_inline_threads` → check run → issue comment → inline posts → persist `summary_json.github_inline_threads` (GH-1b).

**Triggers (union — any match collapses the thread):**

| ID | Trigger | Condition |
|----|---------|-----------|
| **Option A** | Not in current publishable set | Fingerprint ∈ `inline_threads` and ∉ `_publishable_fingerprints_for_run(review_run_id)` |
| **Option B** | Pass 1 addressed | Fingerprint ∈ `inline_threads` and group `resolution_status=addressed` (may still be `active` + re-reported — intentional) |
| **Outdated** | GitHub anchor moved | REST `comment_id` for fingerprint maps to thread with `isOutdated=true` |
| **Synced** | Already resolved on GitHub | `comment_id` on thread with `isResolved=true` — pop map entry only, no `resolveReviewThread` call |
| **Closed** | DB lifecycle | Group `state` ∈ `resolved` \| `superseded` (P1 behavior) |

**Explicit non-triggers:**

- Greptile / other bots' review threads (Revy only resolves fingerprints in Revy's `github_inline_threads` map).
- Issue-comment summary rows (not in thread map).
- `resolution_status=still_open` alone (no outdated signal, still publishable, not addressed).

**Tests:** `test_resolve_stale_inline_threads_option_a`, `_outdated_comment`, `_addressed_while_still_publishable`, `_pops_already_resolved_without_graphql`; `test_build_review_thread_index_tracks_outdated_and_resolved`.

**Still deferred (follow-up):** verification judge for warning/info false positives; title+file fingerprint to reduce line-drift identity splits; GH-7 dogfood row after staging deploy of v2.

### GH-1b — thread-map persistence (same program phase as GH-1)

**Verified bug:** `_resolve_superseded_inline_threads` mutates `inline_threads` in place (`pop` at `github_publish.py:340`), but `job.summary_json` is only reassigned inside `if post_inline:` (`798–801`). No `flag_modified` in backend. In-place JSONB mutation may not persist on flush.

**Fix:** always reassign `job.summary_json` (or `flag_modified`) after resolve — even when `post_inline=False`.

### Scale (program P2)

- Store `thread_id` in thread map (GH-Q3).
- Paginated `reviewThreads` index; batch resolve (GH-2, GH-3).

### Diff-based resolve (deferred)

GH-Q2 locked **no** new diff-based resolve logic. M2 `resolution_status` may inform a future phase — document only.

---

## 4b. `resolution_status` coupling

| Fact | Location |
|------|----------|
| `apply_resolution_status_for_synchronize` stamps diff-based `addressed` on push | `github_resolution_metrics.py:139–194` |
| Does **not** change `group.state` by itself | same |
| `count_resolution_status` excludes `addressed` while group still `active` | `github_publish_formatter.py:97–100` — L2 prose under-counts fixes |
| Thread resolve **v2:** Option B collapses when `resolution_status=addressed` | `_fingerprints_to_resolve_inline_threads` — see §4c (GH-Q9) |

Option B does not flip `group.state`; it only collapses the GitHub thread so the PR surface matches “dev fixed this hunk” even when Moonshot re-reports the same fingerprint.

---

## 5. GH-2 / GH-3 — GraphQL scale

**Verified:** `find_review_thread_id_for_comment` uses non-paginated `first: 100` / `first: 20` (`github_api.py:460–465`). Returns `None` on `errors` (`github_api.py:479`) — silent skip.

**Verified:** `_resolve_superseded_inline_threads` calls lookup **once per closed group** (`github_publish.py:323`) — O(n) HTTP.

**Advice:** Add `list_review_threads` with cursor pagination; build `databaseId → threadId` index once per publish. **Until P2 ships**, busy PRs (>100 threads) can silently miss resolves (`None` at `332–333`) — acceptable for internal dogfood only.

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
| Re-activation same publish | Resolve runs before inline post (`734` then `746`) — test fingerprint reappearing |
| `post_inline=False` | Must still persist map after resolve (GH-1b) |
| Thread map v2 shape | Migrate-on-read: current `dict[str, int]` → `{ "fp": { "comment_id": int, "thread_id"?: str } }` or equivalent — execution must specify |

---

## 8. Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **GH-Q1** | Separate “Revybot resolver” from publish? | **locked** | **No** — one publish path |
| **GH-Q2** | New diff-based resolve logic in v1? | **locked** | **No** — Option A (run-scoped fingerprints) |
| **GH-Q3** | Store `thread_id` in summary_json? | **locked** | **Yes** — program P2 |
| **GH-Q4** | Track B in this program? | **locked** | **No** |
| **GH-Q5** | Program name / folder | **locked** | `github-surface-hardening` |
| **GH-Q6** | GH-1 resolve trigger v1? | **locked** | **Option A** + existing superseded/resolved pass |
| **GH-Q7** | Stale active groups — threads vs check/summary? | **locked** | **Threads only** in v1; reconcile unchanged |
| **GH-Q8** | Gap ID vs program phase naming? | **locked** | **GH-*** = gap id; **P0–P4** = program phase in general/execution plan |
| **GH-Q9** | GH-1v2 collapse beyond Option A? | **locked** | **Option B** (`addressed`) + **outdated** + **already-resolved sync** — see §4c; GH-Q2 unchanged for v1 history |

**Naming:** findings “Priority” column used GH-1 **P0** (urgency) vs program **P1** (phase) — use **GH-*** ids in execution docs to avoid “ship P0 twice” confusion.

**Review context (verified stale on `main`):** `.greptile/files.json` and `.cursor/BUGBOT.md` still point at post-review-quality / `feat/revy-github` — program P0 deliverable.

**Tests (verified):** zero direct unit tests for `_resolve_superseded_inline_threads` (autouse mock at `test_github_publish.py:30–44`). Program P1 must add ≥1 unmocked test; full harness refactor stays P4.

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
| Over-resolve threads while finding still active | Resolve only when fingerprint **not in current run publishable set** (Option A) |
| GraphQL pagination complexity | Ship GH-1 with current query; GH-2 before customer-scale busy PRs |
| summary_json shape change | Version key or migrate on read |
| Test refactor scope creep | GH-6 as own subphase; don’t block GH-1 |

---

## 11. Verification (program done when)

| Check | Pass |
|-------|------|
| Push fix on dogfood PR → Revy thread collapses without manual `gh` | GH-1 + GH-1b (program P1) |
| PR with >100 threads (unit mock) → resolve still finds target | GH-2 (program P2) |
| Publish with 10 closed groups → ≤2 GraphQL list calls | GH-3 (program P2) |
| Staging deploy + dogfood: thread auto-resolve on fix push | GH-7 — **after P1**, before program sign-off |
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

| Reconcile | `backend/app/services/github_finding_reconcile.py` |
| Resolution metrics | `backend/app/services/github_resolution_metrics.py` |

---

## 13. Peer review adjustments (2026-07-27)

Architecture peer-review cross-checked findings + plan against publish, reconcile, resolution metrics, tests, and review-context wiring. **Accepted** — see §4 (#52 root cause), GH-Q6–Q8, GH-1b, review-context stale, P1 tests. **Deferred** — Option B/C as v1 triggers; reconcile changes.

---

## Next step

1. ~~`create-general-plan`~~ → [GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md](./GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md).
2. ~~`create-execution-plan`~~ → [GITHUB_SURFACE_HARDENING_EXECUTION.md](./GITHUB_SURFACE_HARDENING_EXECUTION.md) + P0–P4 files.
3. `execution-peer-review` → then `phase-execution` on `feat/github-surface-hardening`.
