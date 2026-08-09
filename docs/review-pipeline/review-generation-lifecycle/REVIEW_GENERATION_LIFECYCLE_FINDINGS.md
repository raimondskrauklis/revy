# Review generation lifecycle — findings

**Purpose:** Baseline for making Revy’s **review generation** predictable on GitHub — snapshot-on-HEAD, not append-and-merge. Platform research — **no execution steps**.

**Date:** 2026-07-27  
**Evidence:** PR [#53](https://github.com/raimondskrauklis/revy/pull/53) dogfood (feat/github-surface-hardening), operator triage vs Greptile/Bugbot, code read of pipeline/publish paths.

**Related (shipped, different scope):** [github-surface-hardening](../github-surface-hardening/) — thread auto-resolve (Option A), GraphQL pagination, publish test harness.

---

## Build principles

1. **Revy architecture stays** — index → review → reconcile → publish, fingerprints, DB truth. This program improves **when** and **whether** work touches GitHub, not a rewrite.
2. **Predictable contract** — at HEAD, after the Revy check completes, the PR shows **one generation**: summary + open inline threads match that run.
3. **Snapshot, not spill** — no per-finding drip on GitHub mid-pass; no publish from superseded revisions.
4. **Greptile / Bugbot bar** — work on latest; when newer commit arrives, **supersede** in-flight generation; **results only after finish**.
5. **Realistic load** — design for normal dev (occasional double-push, amend chains), not 10 pushes / 10 s stress tests.
6. **Verify against code** — cite `file:line`; dogfood rows override stale docs.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Generation** | One full pipeline pass for a `(pull_request, revision, head_sha)` — index through publish |
| **Snapshot semantics** | External GitHub surface reflects **one completed generation at HEAD**, not a union of partial passes |
| **Spill** | Writing findings to GitHub before the generation is complete or canonical (check early, inline one-by-one) |
| **HEAD exclusivity** | Only the publish job whose `head_sha` equals `pull_request.head_sha` may write inline comments |
| **Supersede** | New revision arrives → prior in-flight generation must not change the PR surface (cancel, skip publish, or discard) |
| **Coalesce window** | Short delay before **starting** a new generation after `synchronize` — absorbs back-to-back commits without a long fixed sleep |
| **Outdated (GitHub)** | Diff anchor moved — automatic; **not** the same as resolved |
| **Resolved (GitHub)** | `resolveReviewThread` — explicit; Option A in publish |

---

## 1. Platform question

[github-surface-hardening](../github-surface-hardening/) asked: *when a finding is fixed, do stale threads collapse?* **Mostly answered** (Option A, GH P0–P4).

This program asks:

> **When the developer pushes while Revy is still working — or pushes again soon after — is the PR surface predictable, or does it accumulate partial / stale bot output?**

PR #53 showed the second: **11 Revy inline threads**, overlapping generations, outdated-but-open comments. Greptile on the same PR felt **one pass on latest** — not because push cadence was wrong, but because **generation lifecycle** differed.

---

## 2. What exists vs genuinely new

### Shipped on `main` (verified)

| Capability | Location | Notes |
|------------|----------|-------|
| New revision per `synchronize` | `github_pull_requests.py:343–361` | `create_revision=True` |
| Pipeline enqueue per revision | `github_tasks.py:54–68` | No PR-level coalesce |
| Skip enqueue if review **same revision** in flight | `review_pipeline.py:183–192` | New push = **new revision** → does **not** block |
| Check `in_progress` at pipeline start | PRODUCT_PATTERNS G10 | Good — spinner while working |
| Issue comment reuse / update in place | `find_prior_issue_comment_id_for_pull_request`, `update_issue_comment` | Snapshot-like for **summary** |
| Inline posted in loop + checkpoints | `github_publish.py:906–979` | **Spill** — each REST call visible |
| Thread map merges prior publish jobs | `_load_inline_thread_map` `github_publish.py:295–303` | Ascending merge over prior completed jobs |
| G10 check external id per `head_sha` | `build_check_run_external_id` `github_api.py:236–242` | Each push → distinct check run; orphan `in_progress` risk if supersede not finalized |
| Check/summary land before inline loop | `github_publish.py:775–868` before inline `906+` | Summary-channel spill — not only inline |
| Option A stale resolve | `_resolve_stale_inline_threads` | Runs at publish; does not stop superseded revision publish |
| No HEAD guard on publish | `run_publish_job` — **no** `job.head_sha == pull_request.head_sha` check | Stale revision can still post inline |

### Genuinely new (this program)

| Capability | Why new |
|------------|---------|
| **HEAD-gated GitHub writes** | Stale generations must not touch inline surface |
| **PR-level generation supersede** | New revision → prior in-flight work skipped or publish-blocked |
| **Buffer-then-flush inline** | No per-finding GitHub drip during publish |
| **Optional coalesce before start** | Short quiet period after commit — not minute-scale |
| **Generation epoch / cancelled status** | DB + trace: which run was authoritative for HEAD |
| **Publish enqueue supersede guard** | `reconcile_tasks.py:68` always calls `enqueue_publish_for_review_run` — no supersede check today |
| **Stale G10 check finalize** | `finalize_pipeline_github_check_neutral` exists (`github_pipeline_trace.py:712`) — not called on supersede/skip |
| **Publish job terminal skip statuses** | `GitHubPublishJobStatus` has no `skipped_not_head` / `skipped_superseded` (`enums.py:234–240`) |

### Reuse traps

| Trap | Detail |
|------|--------|
| **Confuse with push policy** | Push frequency is operator choice; predictability is **generation policy** |
| **Confuse outdated with fixed** | Outdated = line moved | **v2:** Revy resolves outdated threads at publish (GH-Q9); DB group may stay `active` if re-reported |
| **Cancel vs block-publish only** | Letting old jobs finish DB work but blocking GitHub is cheaper than hard cancel mid-LLM — same user contract if HEAD-gated |
| **Greptile “cannot cancel” docs** | [Greptile trigger docs](https://www.greptile.com/docs/code-review-bot/trigger-code-review) say running reviews aren’t cancelled — user-visible predictability may still come from **single-pass + update-in-place**, not mid-run GitHub posts |
| **CodeRabbit incremental model** | CodeRabbit documents **incremental** reviews on new commits — different product choice; Revy target for this program is **Greptile/Bugbot snapshot bar** per operator triage |

---

## 3. Verified Revy behavior today

```text
synchronize → new revision_id → new index/review/reconcile/publish pipeline
             (parallel pipelines for rev N and N+1 are allowed)

publish:
  → update check + issue comment (can land early)     ← summary spill
  → resolve stale threads (Option A)
  → for each inline finding: REST post + checkpoint  ← inline spill
  → no check that revision is still PR HEAD
  → reconcile always enqueues publish (no supersede guard)
```

**Assumption (dogfood, not line-proven):** Greptile/Bugbot do not expose partial inline during LLM work; Revy does via publish loop.

---

## 3b. Judge vs publish (verified + locked policy)

| Fact | Location |
|------|----------|
| Judge runs in **reconcile** before `enqueue_publish_for_review_run` | `reconcile_tasks.py:41–68` |
| Dismissed → `group.state = resolved` (drops from publish) | `github_finding_judge.py:191–192` |
| `inline_publish_findings_statement` does **not** filter on judge outcome rows | `github_publish.py:207–229` — active groups only |
| Escalation candidates | `is_judge_candidate` — error/critical + security≥warning (`github_finding_judge.py:56–62`) |

**Locked (operator, RG-Q10):**

- **Do not block whole publish** because one finding lacks a judge outcome.
- **Do not publish judge-candidate findings** without a recorded outcome (upheld / dismissed / modified). Missing outcome ≠ “assume false positive” — treat as **bug** + metric; hold **that finding only**.
- **Non-candidates** publish regardless of `judge_status`.
- Generation lifecycle (HEAD gate, flush) is orthogonal — RG-6 is **per-finding eligibility**, not “wait for judge or drop the run.”

**Verified bug (RG-6):** LLM failure per candidate → `continue` with no outcome (`github_finding_judge.py:161–176`); run still sets `judge_status = completed` (`274`) even when candidates lack rows — trace/UI can lie while publish must hold candidates (P5 filter + optional status honesty fix).

---

## 3c. Summary vs inline scope (verified 2026-07-29)

| Channel | Scope today | Location |
|---------|-------------|----------|
| **Issue comment** (narrative, findings table, confidence) | **This generation** — `publishable_groups_for_review_run` for `job.review_run_id` | `_build_publish_surface` → `build_pr_review_comment` (`github_publish.py`, `github_publish_formatter.py`) |
| **Check run summary** | **Two blocks:** this generation + **Still open on PR** (filtered `pr_active_groups`) | `format_summary_comment` + `filter_pr_active_groups_for_summary` in `build_check_run_summary` / `_build_publish_surface` |
| **Inline + thread resolve** | Current **review_run** publishable fingerprints | `inline_publish_findings_statement`, `_publishable_fingerprints_for_run` |

**Per-push refresh (not append):** one issue comment per PR, body **replaced** on each successful publish at HEAD (`update_issue_comment`). Stale/superseded generations skip publish (HEAD gate).

**Review input vs resolution delta:**

| Input | Range | Purpose |
|-------|-------|---------|
| Moonshot review diff | **Full PR** `base_sha` → `head_sha` | Fresh generation each push — **no cross-push LLM memory** |
| `resolution_status` / G9 “Since last push” | **Push delta** `prior.head_sha` → `new.head_sha` | Metrics + prose only |

**RG-14 (shipped — [publish-summary-alignment](../publish-summary-alignment/README.md)):** Issue comment now mirrors check two-block summary + PR-wide verdict fields (PSA P0–P1). Staging sign-off pending.

---

## 4. Dogfood evidence (PR #53)

| Observation | Implication |
|-------------|-------------|
| Multiple phase pushes during one PR | **Valuable** — exposed generation overlap, not operator error |
| 11 Revy inline threads | Append semantics + multiple completed publishes |
| Revy marked pagination comment **Outdated** after fix | Stale-anchor logic works; thread hygiene separate |
| Greptile: one summary, 0 inline on HEAD pass | Snapshot feel on triage |
| `judge_status=not_applicable` on staging when candidates may exist | Internal pass looks “unfinished”; candidates may still publish — see RG-6 |

---

## 5. External research — industry patterns

### 5.1 Greptile (vendor docs)

| Pattern | Source | Adopt for Revy |
|---------|--------|----------------|
| `triggerOnUpdates: true` — fresh review per commit | [trigger-code-review](https://www.greptile.com/docs/code-review-bot/trigger-code-review), [greptile.json](https://www.greptile.com/docs/code-review-bot/greptile-json) | **Yes** — already on `synchronize` |
| **Single-pass** — each review independent, not iterative comment updates | Same | **Align publish** — one flush per generation |
| **Cannot cancel running reviews** (vendor doc) | Same | **Defer literal cancel** — prefer **skip publish** + **HEAD gate** if cancel is hard |
| Summary / check update in place | PRODUCT_PATTERNS | **Shipped** for issue comment + check |

### 5.2 CodeRabbit (contrast)

| Pattern | Source | Adopt for Revy |
|---------|--------|----------------|
| Incremental review on new commits | [code-review-overview](https://docs.coderabbit.ai/guides/code-review-overview) | **Reject as default** — operator wants snapshot bar |
| `@coderabbitai full review` for scratch pass | [commands](https://docs.coderabbit.ai/guides/commands) | **Analog:** `@revy review` = full generation (already) |

### 5.3 CI / review bots — concurrency (best practice)

| Pattern | Source | Adopt for Revy |
|---------|--------|----------------|
| `concurrency` + `cancel-in-progress: true` per PR | [GitHub Actions concurrency](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#concurrency), [OCR issue #58](https://github.com/alibaba/open-code-review/issues/58), [gh-aw PR #27204](https://github.com/github/gh-aw/pull/27204) | **Yes** — PR-level “latest wins” for **generation** |
| Smart concurrency — don’t cancel on bot’s own comment events | [ccs commit 25d31ce](https://github.com/kaitranntt/ccs/commit/25d31ce4329daf9512df4e0236e02d89d05b0842) | **Yes** — `@revy review` / publish webhooks must not self-supersede |
| Sleep-based debounce wastes wall-clock | CI cost guides | **Reject long sleep** — use cancel/coalesce, not 60 s `sleep` |

### 5.4 Coalesce window (advice — not vendor-mandated)

| Approach | Typical use | Revy fit |
|----------|-------------|----------|
| **Cancel in-flight** when new commit arrives | PR CI, AI review actions | Primary — immediate supersede |
| **Trailing coalesce** (≤**10 s** quiet before **start**) | Absorb amend + push pairs without two full LLM runs | **Optional** — operator cap **10 s max** |
| **Fixed 60 s+ delay** | Rare; feels sluggish | **Reject** |

**Realistic scenario:** developer pushes, notices typo, pushes fix within a few seconds — one generation after coalesce (≤10 s) is enough. **Not** designing for 10 pushes in 10 s.

---

## 6. Target contract (locked direction)

**Bottom line (operator):**

> Work on **latest HEAD**. If a **newer** commit arrives before finish, **supersede** the in-flight generation. **Only after finish** — and only if still HEAD — write results to GitHub.

```text
synchronize (head_sha = H2)
  → mark in-flight review runs + index jobs for older revisions superseded
  → mark in-flight review runs + index jobs on same HEAD superseded (re-push / @revy review)
  → schedule resolution pairing async (`apply_resolution_for_synchronize`) — do not block enqueue
  → optionally: coalesce ≤10s if another synchronize before start
  → run pipeline for H2 (DB may complete for H1 — OK)
  → on publish: if pull_request.head_sha != job.head_sha → NO GitHub writes
  → if superseded → skip publish enqueue; finalize stale G10 check neutral
  → buffer entire GitHub surface (check finalize, issue comment, resolve, inline) → single flush
  → complete check (authoritative generation only)

* G10 external id is per `head_sha` — supersede must finalize stale checks, not leave `in_progress`
```

---

## 7. Gap catalog (prioritized)

| ID | Gap | User impact | Priority |
|----|-----|-------------|----------|
| **RG-1** | **No HEAD-gated publish** | Stale revision posts inline / outdated pile | **P1** |
| **RG-2** | **Parallel generations per PR** | Unpredictable union of bot output | **P2** |
| **RG-3** | **GitHub surface spill** (check/summary early + inline drip) | Partial generation visible mid-pass | **P3** |
| **RG-4** | **No coalesce before pipeline start** | Double full run on quick amend+push | **P4** (optional) |
| **RG-5** | **No generation epoch in trace/DB** | Hard to debug “which run was authoritative” | **P5** |
| **RG-6** | **Judge candidates published without outcome** | Escalation findings hit GitHub unvetted; `judge_status=not_applicable` when candidates exist = bug | **P5** (narrow) |
| **RG-7** | **Orphan G10 checks on supersede** | Multiple stuck `in_progress` checks per PR | **P1–P2** |
| **RG-8** | **No publish enqueue supersede guard** | Stale generation reaches `run_publish_job` | **P2** |
| **RG-9** | **Underspecified supersede entity + migrations** | Rework mid-execution | **P0** |
| **RG-10** | **Same-SHA re-publish after skip** | `find_publish_job_for_head_sha` has no status filter — skipped job with copied `github_check_run_id` can win `is_update_from_other` (`484–507`) | **P1** |
| **RG-11** | **No stage-entry authority guards** | Queued H1 index can call `start_pipeline_github_check` after H2 supersedes (`index_tasks.py:56–67`); `prepare_review_after_index` → `create_review_run` with no HEAD/supersede check (`review_pipeline.py:260–267`) | **P2** |
| **RG-12** | **Pending publish after supersede** | Job created pending; H2 arrives before task runs — need `run_publish_job` re-check `review_run.status == superseded` | **P1–P2** |
| **RG-14** | **Issue comment generation-only vs check two-block** | Prior open findings omitted from issue comment when not re-reported; check still lists PR-wide open — triage confusion | **shipped** — [publish-summary-alignment](../publish-summary-alignment/README.md) |
| **RG-13** | **Judge marks completed when outcomes missing** | `judge_status=completed` despite failed candidates — see §3b | **P5** |
| **RG-15** | **Supersede omitted index jobs + inline resolution on webhook** | Push during run or `@revy review` while index pending → `pipeline_index_in_progress` or blocked `github_events` worker — no UI run until restart | **shipped** — [PR #89](https://github.com/raimondskrauklis/revy/pull/89) |

**Out of scope:** recall/STRUCT, reconcile marks-absent-resolved, human dismiss R7.6, push-frequency policy.

---

## 8. Advice / options

### Recommended path (phased)

| Phase | Deliverable | Rationale |
|-------|-------------|-----------|
| **P0** | Enum migrations + supersede helpers | RG-9 — single source of truth |
| **P1** | HEAD-gated publish + skip statuses + same-SHA retry | RG-1, RG-10 |
| **P2** | Supersede on sync + enqueue guard + G10 neutral finalize | RG-2, RG-7, RG-8 |
| **P3** | Full GitHub surface flush at publish end | RG-3 / RG-Q7 |
| **P4** | Coalesce ≤10 s (Celery ETA + revision token) | RG-4 |

### Alternatives considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Hard-cancel Celery tasks** | Clean worker utilization | Mid-transaction cleanup; judge/LLM hard to abort | **Defer** — block publish first |
| **Only debounce, no cancel** | Simple | Old run may still finish and race | **Reject alone** — need HEAD gate |
| **CodeRabbit-style incremental** | Cheaper per push | Operator triage harder | **Reject** for default |
| **Manual push discipline** | No code | Does not fix mid-review overlap | **Reject** as product contract |

---

## 9. Edge cases

| Case | Risk | Mitigation |
|------|------|------------|
| Same SHA re-publish (`@revy publish`) | Prior `skipped_not_head` job may block | Terminal skip statuses excluded from `find_publish_job_for_head_sha` / allow new publish job |
| Supersede between publish job create and task run | Stale publish executes | `run_publish_job` re-check `superseded` at task entry (RG-12) |
| Queued H1 index after H2 supersede | Orphan `in_progress` G10 for H1 | `index_pull_request_revision`: skip G10 when not authoritative (RG-Q11) |
| `@revy review` while autostart running | Double pipeline / dropped enqueue | `supersede_active_generations_for_revision` — review runs **and** index jobs (RG-15) |
| Push during Revy run | No restart; worker stuck on resolution | Defer `apply_resolution_for_synchronize`; supersede index jobs before enqueue (RG-15) |
| Bot webhook during publish | Self-supersede | Exclude bot-originated events from supersede (ccs pattern) |
| Fix in push A, break in push B | Generation B is truth | Snapshot contract — A’s threads resolved by Option A on B’s publish |
| Coalesce + manual command | Operator expects immediate | Command path bypasses coalesce |

---

## 10. Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| RG-Q1 | Is the target Greptile/Bugbot snapshot semantics? | **locked** | Yes — latest HEAD, supersede in-flight, publish after finish only |
| RG-Q2 | Is Revy architecture wrong? | **locked** | No — incremental improvements per step |
| RG-Q3 | Coalesce duration? | **locked** | Trailing **≤10 s** before autostart start; **0** = off; `@revy review` bypasses |
| RG-Q4 | Cancel task vs skip publish? | **locked** | **Skip publish + HEAD gate** v1; hard Celery cancel deferred |
| RG-Q5 | Buffer inline vs batch review API? | **locked** | Sequential post in one flush; no mid-loop GitHub persist; batch API defer |
| RG-Q6 | Relationship to github-surface-hardening | **locked** | Hardening = thread hygiene; this = generation hygiene — complementary |
| RG-Q7 | Summary channel before inline flush? | **locked** | **No** — full GitHub surface flush at publish end (stricter Greptile bar) |
| RG-Q8 | Superseded SHA checks? | **locked** | `finalize_pipeline_github_check_neutral` — “Superseded by newer commit” |
| RG-Q9 | Generation authority model? | **locked** | **`GitHubReviewRunStatus.superseded`** = source of truth; publish job terminal skip statuses; pipeline trace mirrors |
| RG-Q10 | Judge vs publish when outcome missing? | **locked** | Per-finding: hold **candidates** only; publish **rest**; missing outcome = bug, not silent dismiss |
| RG-Q11 | Non-authoritative index at task entry? | **locked** | Allow index DB work; **skip G10 start** + **skip review enqueue** when not authoritative |
| RG-Q12 | Enum migrations required? | **locked** | **No** Alembic for new `String(32)` status values unless CHECK constraints added |

---

## 11. Parking lot

- Hard Celery cancel mid-LLM (RG-Q4 defer).
- GitHub batch review API (RG-Q5 defer).
- Root-cause staging runs where `judge_status=not_applicable` but candidates exist — investigate in RG-6 / P5.
- **RG-14:** [publish-summary-alignment](../publish-summary-alignment/README.md) — PSA P0–P2 on `feat/publish-summary-alignment`.

---

## 12. Devil's advocate

| Risk | Mitigation |
|------|------------|
| HEAD gate hides slow publish — check stuck `in_progress` | Finalize superseded checks **neutral** at supersede/skip (RG-Q8); only authoritative gen completes check |
| Coalesce delays feedback on single push | Keep window short; bypass for `@revy review` |
| Over-supersede drops legitimate work | Supersede only on **new revision** / new `head_sha`, not duplicate webhooks |
| “Snapshot” fights fingerprint continuity | Continuity via **thread map + resolve**, not parallel publishes |

---

## 13. Experiment / verification

| Test | Pass |
|------|------|
| Push H1, wait for review start, push H2 before H1 publish | **No** inline from H1; H1 G10 check **neutral** (not stuck `in_progress`) |
| Single push, normal PR | One generation; inline count = publishable set |
| Fix finding, push H3 | Option A resolves; open threads ≈ H3 publishable only |
| Amend within 8 s (coalesce on) | One pipeline start (if RG-4 shipped) |
| Compare Greptile + Revy on same PR | Revy open-thread count stable at HEAD after check completes |

---

## 14. References

**Code:** `review_pipeline.py`, `github_pull_requests.py`, `github_tasks.py`, `github_publish.py`, `publish_tasks.py`

**Docs:** [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md), [GITHUB_SURFACE_HARDENING_FINDINGS.md](../github-surface-hardening/GITHUB_SURFACE_HARDENING_FINDINGS.md), [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md)

**External:** [Greptile triggers](https://www.greptile.com/docs/code-review-bot/trigger-code-review) · [CodeRabbit overview](https://docs.coderabbit.ai/guides/code-review-overview) · [GitHub Actions concurrency](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#concurrency) · [Open Code Review #58](https://github.com/alibaba/open-code-review/issues/58)

---

## 15. Peer review applied (2026-07-28)

Architecture peer review cross-checked docs vs code. **Verdict: core diagnosis correct; gaps below incorporated.**

| Finding | Action |
|---------|--------|
| Orphan G10 checks per `head_sha` | RG-7; neutral finalize on supersede/skip (RG-Q8) |
| “No spill” broader than inline | RG-3 expanded; RG-Q7 locks full surface flush |
| Supersede entity underspecified | RG-9; P0 locks `GitHubReviewRunStatus.superseded` + publish skip statuses (RG-Q12: no Alembic) |
| `enqueue_publish_for_review_run` unguarded | RG-8; P2 scope |
| Coalesce needs concrete mechanism | P4: Celery ETA + revision token; DB revision still immediate |
| Same-SHA re-publish after skip | RG-10; P1 edge case |
| Doc sync | README, prerequisite, line refs, PRODUCT_PATTERNS row |

---

## 16. Peer review pass 2 (2026-07-28)

**Verdict:** Ready for `create-execution-plan` — scope additions below incorporated.

| Gap | Action |
|-----|--------|
| P2 must guard **index start** + **review enqueue**, not only publish enqueue | RG-11; `is_authoritative_for_pull_request_head` at stage entry (RG-Q11) |
| `find_publish_job_for_head_sha` status filter | RG-10 — exclude terminal skip statuses |
| Pending publish + supersede race | RG-12; `run_publish_job` superseded check at task start |
| Judge `completed` when outcomes missing | RG-13; P5 filter + `judge_status` honesty |
| Alembic for String enums | RG-Q12 — no migration unless CHECK |
| Summary vs inline asymmetry | §3c — dogfood uses inline thread count |
| P1 + P2 both finalize G10 neutral | Idempotent; P2 at supersede moment, P1 fallback at skip-at-publish |

---

## 17. Execution peer review (2026-07-28)

**Verdict:** BLOCK cleared — critical/high gaps incorporated in P0–P5 execution files.

| Gap | Action |
|-----|--------|
| Publish gate after `processing` flash | P1.1 — gate before `job.status = processing` |
| Index guard must skip full pipeline-trace block | P2.2 — `ensure_pipeline_run_for_index_job` + G10 + stash |
| Broken P2 phase gate `pytest` | Fixed — all test paths before `-k` |
| `@revy review` same-revision supersede | P0 helper + P2.5 command path |
| P3 build vs flush Option A | Locked flush order; no GitHub in build |
| P4 coalesce cancel mechanism | v1 authority no-op; no `celery_task_id` column |
| P5 groups query + pytest | Filtered groups for review run; fixed pytest paths |
| Smart-trigger + trace contract | P0.3 module docstring |
