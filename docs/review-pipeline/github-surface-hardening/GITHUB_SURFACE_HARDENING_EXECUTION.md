# GitHub surface hardening — execution index

**Program:** [README.md](./README.md) · **Baseline:** [GITHUB_SURFACE_HARDENING_FINDINGS.md](./GITHUB_SURFACE_HARDENING_FINDINGS.md) · **General plan:** [GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md](./GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md)

**Authority:** [GITHUB_WEBHOOK_DEV.md](../GITHUB_WEBHOOK_DEV.md) · [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) · [GITHUB_APP_SETUP.md](../../utils/GITHUB_APP_SETUP.md)

**Goal:** GH-1 thread auto-resolve (Option A) + GraphQL scale + publish test harness. Track B out.

**Branch:** `feat/github-surface-hardening` — docs + code same PR per phase; first push opens ONE PR.

## How we work (locked)

```text
P0 → P1 → P2 → P3 → P4
each phase: implement → pytest gate → Bugbot → commit (no push until user/LOOP)
```

**Gap IDs (GH-*):** findings catalog. **P0–P4:** program phases below.

## Decisions locked for execution

- **GH-Q6:** Resolve when fingerprint ∈ `inline_threads` but ∉ current run publishable findings (Option A) + existing superseded/resolved pass.
- **GH-1b:** Persist `summary_json` after every resolve (even `post_inline=False`).
- **GH-Q7:** v1 collapses GitHub threads only — reconcile/check unchanged.
- **GH-Q2:** No `resolution_status.addressed` trigger in v1.
- **Thread map v2:** `{ fingerprint: { "comment_id": int, "thread_id"?: str } }` — migrate-on-read from `dict[str, int]`; `serialize_inline_thread_map` / `deserialize_inline_thread_map` (P0).
- **Migrations:** none expected; JSONB shape only.
- **i18n:** GitHub markdown EN v1.

## LOOP order

| Phase | Focus | Execution | Status |
|-------|--------|-----------|--------|
| P0 — Foundations | Thread map v2 + Greptile/Bugbot | [GITHUB_SURFACE_HARDENING_P0_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P0_EXECUTION.md) | Done (d61f4ed) |
| P1 — Auto-resolve | GH-1, GH-1b | [GITHUB_SURFACE_HARDENING_P1_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P1_EXECUTION.md) | pending |
| P2 — GraphQL scale | GH-2, GH-3 | [GITHUB_SURFACE_HARDENING_P2_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P2_EXECUTION.md) | pending |
| P3 — Edge cases | GH-4, GH-5 | [GITHUB_SURFACE_HARDENING_P3_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P3_EXECUTION.md) | pending |
| P4 — Harness + sign-off | GH-6, GH-7, doc sync | [GITHUB_SURFACE_HARDENING_P4_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P4_EXECUTION.md) | pending |

**Dogfood log:** [GITHUB_SURFACE_HARDENING_DOGFOOD.md](./GITHUB_SURFACE_HARDENING_DOGFOOD.md)

**Peer review:** `execution-peer-review` complete — P0/P1 serialize contract, P1 rename/dedupe, P2 cap constants, P4 PRODUCT_PATTERNS specificity applied. Ready for `phase-execution`.
