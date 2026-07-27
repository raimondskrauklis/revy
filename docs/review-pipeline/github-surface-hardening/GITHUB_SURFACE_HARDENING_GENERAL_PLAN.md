# GitHub surface hardening — general plan

**Baseline:** [GITHUB_SURFACE_HARDENING_FINDINGS.md](./GITHUB_SURFACE_HARDENING_FINDINGS.md) (peer-reviewed 2026-07-27)  
**Prerequisite:** [post-review-quality P0–P4](../post-review-quality/README.md) on `main` ([#52](https://github.com/raimondskrauklis/revy/pull/52)).

**Thesis:** Greptile-parity **thread lifecycle** on GitHub — auto-resolve when findings leave the current run, scalable GraphQL, trustworthy publish tests. Track B (recall/STRUCT) stays out.

**Ship model:** Docs + code in **one PR per phase** on `feat/github-surface-hardening` (local until `phase-execution` first push).

**Gap IDs:** **GH-*** in findings; **P0–P4** = program phases below (GH-Q8).

---

## Cross-cutting (every phase)

- **Tests:** `backend/tests/unit/` each phase; **P1** adds unmocked resolve tests (not deferred to P4).
- **Tenancy:** workspace scope unchanged.
- **Trace:** log resolve skips.
- **i18n:** GitHub markdown English v1.
- **Docs:** minimal README row per phase; PRODUCT_PATTERNS flip only when GH-1 ships.
- **Review context:** `.greptile/files.json` + `.cursor/BUGBOT.md` in **P0 first commit** (verified stale on `main`).

---

## P0 — Foundations + program wiring

**Goal:** Thread-map v2 migrate-on-read; Greptile/Bugbot point at this program; dogfood template.

**Scope — in:** `summary_json.github_inline_threads` v2 shape (`comment_id` + optional `thread_id`, backward-compatible read of `dict[str, int]`); update `.greptile/files.json` + `.cursor/BUGBOT.md` to hardening docs + `feat/github-surface-hardening`.

**Scope — out:** resolve logic (P1); GraphQL pagination (P2).

**Deliverables:** Schema helpers + migrate-on-read; review context wired; README P0 done.

**Depends on:** `main` (#52).

---

## P1 — Auto-resolve + persistence (GH-1, GH-1b)

**Goal:** #52-class stale threads collapse on publish without manual `resolveReviewThread`.

**Scope — in:** **Option A (GH-Q6):** resolve when fingerprint is in `inline_threads` but **not** in current `review_run_id` publishable findings; keep superseded/resolved pass. **GH-1b:** always persist `summary_json` after resolve (`flag_modified` or reassignment) even when `post_inline=False`. ≥1 **unmocked** unit test for resolve criteria + re-activation; retry on transient GraphQL failure.

**Scope — out:** reconcile changes; `resolution_status.addressed` as trigger (GH-Q2); new diff logic.

**Deliverables:** Dogfood-verifiable thread collapse on fix push; PRODUCT_PATTERNS “resolve when fixed” → **shipped**.

**Depends on:** P0.

---

## P2 — GraphQL scale (GH-2, GH-3)

**Goal:** Correct + fast resolve on busy PRs — no silent `first: 100` miss; no N+1.

**Scope — in:** Paginated `list_review_threads`; `databaseId → threadId` index once per publish; persist `thread_id` on new inline (GH-Q3); refactor resolve to use index.

**Scope — out:** Customer rate-limit UI.

**Deliverables:** ≤2 GraphQL list calls per publish with many closed groups; unit test with paginated mock.

**Depends on:** P1.

---

## P3 — Publish edge cases (GH-4, GH-5)

**Goal:** Idempotent same-SHA re-publish; visible skips when data incomplete.

**Scope — in:** Verify/fix same-SHA re-run after GH-1b; structured log (or metric) when inline skipped — missing `group_id` or line; unit tests.

**Scope — out:** Reconcile/judge changes.

**Deliverables:** Edge cases tested; dogfood waive notes if any.

**Depends on:** P2.

---

## P4 — Test harness + doc sync (GH-6, GH-7)

**Goal:** Maintainable publish tests; program sign-off.

**Scope — in:** Replace brittle ordered `session.scalars` mocks with patches/helpers; hardening dogfood row; waves + PRODUCT_PATTERNS final sync; optional `review-github-v1` tag note.

**Scope — out:** Full integration suite; track B.

**Deliverables:** Harness refactor; **GH-7** human dogfood row (staging deploy + fix-push thread collapse) or explicit waive.

**Depends on:** P3.

---

## Locked (do not re-open)

| Topic | Resolution |
|-------|------------|
| GH-Q1 | One publish path |
| GH-Q2 | No **new** diff-based resolve; Option A only |
| GH-Q3 | `thread_id` in map — P2 |
| GH-Q4 | No track B |
| GH-Q6 | Option A + superseded/resolved |
| GH-Q7 | v1 = GitHub threads only; check/summary unchanged |
| GH-Q8 | GH-* gaps vs P0–P4 phases |
| Docs + code | Same PR per phase |

---

## Open item

**GH-7** — staging deploy + dogfood proving **P1** thread auto-resolve. Required before program sign-off; may start after P0 deploy.

---

## Next step

**`create-execution-plan`** → `GITHUB_SURFACE_HARDENING_EXECUTION.md` + P0–P4 execution files (local, no push).
