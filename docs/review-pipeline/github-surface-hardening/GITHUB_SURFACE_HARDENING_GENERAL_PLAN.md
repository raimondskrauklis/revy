# GitHub surface hardening — general plan

**Baseline:** [GITHUB_SURFACE_HARDENING_FINDINGS.md](./GITHUB_SURFACE_HARDENING_FINDINGS.md)  
**Prerequisite:** [post-review-quality P0–P4](../post-review-quality/README.md) on `main` ([#52](https://github.com/raimondskrauklis/revy/pull/52)).

**Thesis:** Greptile-parity **thread lifecycle** on GitHub — auto-resolve when findings close, scalable GraphQL, trustworthy publish tests. Track B (recall/STRUCT) stays out.

**Ship model:** Docs + code in **one PR per phase** (program docs in this folder ship with implementation commits).

---

## Cross-cutting (every phase)

- **Tests:** `backend/tests/unit/` for publish + `github_api` changes each phase.
- **Tenancy:** workspace scope unchanged on publish paths.
- **Trace:** log resolve skips; no new pipeline stages.
- **i18n:** GitHub markdown English v1; EN+LV only if new app/ack strings.
- **Docs:** update this folder README status row + [PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) when GH-1 ships.
- **Review context:** extend `.greptile/files.json` + `.cursor/BUGBOT.md` in **P0** (first commit).

---

## P0 — Foundations + program wiring

**Goal:** Thread-map schema ready for `thread_id`; program docs wired for Greptile/Bugbot; staging dogfood checklist explicit.

**Scope — in:** `summary_json.github_inline_threads` v2 shape (comment id + optional `thread_id`, migrate-on-read); wire hardening docs to review tools; dogfood row template for this program.

**Scope — out:** auto-resolve logic (P1); GraphQL pagination (P2).

**Deliverables:** Backward-compatible thread map read/write; program PR context files; README P0 done.

**Depends on:** `main` with P0–P4 surface.

---

## P1 — Auto-resolve (GH-1)

**Goal:** Stale inline threads collapse on publish when fingerprint has no **active** group — Greptile parity without manual `resolveReviewThread`.

**Scope — in:** Extend resolve pass: map fingerprint → active groups; resolve + pop when absent or group `superseded`/`resolved`; unit tests for re-activation and transient failure retry.

**Scope — out:** diff-based resolve (GH-Q2 **locked defer**); separate Revybot resolver (GH-Q1).

**Deliverables:** Dogfood-verifiable auto-resolve on fix push; PRODUCT_PATTERNS row → **shipped** for “resolve threads when fixed”.

**Depends on:** P0.

---

## P2 — GraphQL scale (GH-2, GH-3)

**Goal:** One paginated thread index per publish; batch resolve — no `first: 100` silent miss; no N+1 lookups.

**Scope — in:** `list_review_threads` with cursor pagination; `databaseId → threadId` index; persist `thread_id` on inline post (GH-Q3 **locked yes**); refactor `_resolve_superseded_inline_threads` to use index.

**Scope — out:** Customer-repo GraphQL rate-limit policy UI.

**Deliverables:** ≤2 GraphQL list calls per publish with many closed groups; thread id stored on new inline comments.

**Depends on:** P1 (resolve behavior stable).

---

## P3 — Publish edge cases (GH-4, GH-5)

**Goal:** Idempotent publish paths leave GitHub consistent on same-SHA re-run and data gaps.

**Scope — in:** Same-SHA re-publish resolve path verified/fixed; structured log when inline skipped (missing `group_id` or line); unit tests.

**Scope — out:** Reconcile/judge logic changes.

**Deliverables:** Edge cases covered in tests; dogfood note if any waive.

**Depends on:** P2.

---

## P4 — Test harness + doc sync (GH-6, GH-7)

**Goal:** Publish tests survive internal call-order changes; docs and dogfood log match shipped behavior.

**Scope — in:** Replace brittle ordered `session.scalars` mocks with targeted patches/helpers; hardening dogfood row after staging deploy; PRODUCT_PATTERNS + waves index final sync; optional `review-github-v1` tag note.

**Scope — out:** Full integration test suite; track B programs.

**Deliverables:** Maintainable publish test patterns; human gate GH-7 dogfood row or explicit waive.

**Depends on:** P3.

---

## Locked (do not re-open)

| Topic | Resolution |
|-------|------------|
| GH-Q1 | One publish path — no separate Revybot resolver |
| GH-Q2 | No diff-based resolve in v1 |
| GH-Q3 | Store `thread_id` in thread map (P2) |
| GH-Q4 | No track B in this program |
| Docs + code | Same PR per phase |

---

## Open item

**GH-7** — staging deploy + post-merge dogfood row (human). Can run parallel to P1 after P0; required before program sign-off.

---

## Next step

**`create-execution-plan`** → [GITHUB_SURFACE_HARDENING_EXECUTION.md](./GITHUB_SURFACE_HARDENING_EXECUTION.md) + per-phase P0–P4 execution files.
