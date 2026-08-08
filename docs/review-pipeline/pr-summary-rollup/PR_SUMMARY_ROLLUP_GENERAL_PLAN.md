# PR summary rollup — general plan

**Baseline:** [PR_SUMMARY_ROLLUP_FINDINGS.md](./PR_SUMMARY_ROLLUP_FINDINGS.md) (2026-08-08, pass-01 incorporated)

**North star:** Every successful publish leaves an honest **PR lifetime** story and a **this-push** story on GitHub — persisted, filter-aligned, no interim compute-only path.

**Execution index:** [`waves/PR_SUMMARY_ROLLUP_EXECUTION.md`](./waves/PR_SUMMARY_ROLLUP_EXECUTION.md)

**Prerequisite:** SOS-5 / [#84](https://github.com/raimondskrauklis/revy/pull/84) on `main` (`2d7462b`) — **satisfied**.

---

## Locked decisions (from findings)

PSR-Q1–Q10 · pass-01 implementation locks (post-collapse compute, `_load_pr_groups_for_rollup`, dedicated review_count query).

**Cross-cutting (every phase):** unit tests for manifest + display parity; deterministic markdown + Moonshot splice; dogfood script; `github_pr_resolution_rollup.py` for lifetime math.

---

## P0 — Rollup contract, migration, compute, persist

**Goal:** Authoritative `pr_resolution_rollup` computed at correct flush points and stored on job + PR.

**Scope — in:** Alembic `github_pull_requests.pr_resolution_rollup` JSONB; `github_pr_resolution_rollup.py` with `build_pr_resolution_rollup()` + `_load_pr_groups_for_rollup()`; wire compute from `apply_publish_summary_thread_collapse` and final flush before `completed`; atomic PR row write; `filter_snapshot` v1 keys; dedicated completed-publish count query. **Out:** markdown, Moonshot, API.

**Deliverables:** Migration; rollup module + tests (rev 1, collapsed, resolved mix, post-collapse parity).

**Depends on:** SOS-5 on `main` (done).

---

## P1 — Formatter surfaces (GitHub comment + check)

**Goal:** User-visible two-horizon layout; formatter reads persisted rollup from P0.

**Scope — in:** `format_pr_resolution_rollup_block()` + PSR-Q9 disclosure; section order (PR summary before G9); `splice_deterministic_pr_summary_block`; review metadata footer; check-run one-liners; `_build_summary_json` includes rollup on display paths. **Out:** full API ship (P2).

**Deliverables:** Formatter + Greptile-shape tests; PSR-Q8 spike note (routes audit).

**Depends on:** P0.

---

## P2 — Moonshot + API + dogfood + trace

**Goal:** LLM cannot drift; API exposes rollup; operators verify in staging.

**Scope — in:** `ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` + user prompt; `GitHubPublishJobResponse.pr_resolution_rollup` (or `summary_json` subset per PSR-Q8); dogfood script gates; optional publish-step trace `rollup_pass` key. **Out:** Frontend UI.

**Deliverables:** Moonshot tests; schema + route tests; dogfood script updates.

**Depends on:** P1.

---

## P3 — Staging sign-off

**Goal:** Dogfood PASS on multi-revision PR post-deploy.

**Scope — in:** Validation on kp-platform (or revy) PR ≥2 revisions; `PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md`; README → shipped. Note SOS orphan-filter dependency if SOS P2 sign-off still open. **Out:** backfill tooling.

**Deliverables:** Signed staging memo; program README updated.

**Depends on:** P2 deployed to staging.

---

**Next step:** `execution-peer-review` → `phase-execution` on `feat/pr-summary-rollup` from `main`.
