# Post review-quality — follow-ups (next program seed)

**Purpose:** Backlog after GitHub surface P0–P4 ([PR #52](https://github.com/raimondskrauklis/revy/pull/52)). Baseline for the **next** findings → general plan pass — not execution yet.

**Date:** 2026-07-27  
**Prerequisite:** Merge #52 → deploy staging workers → post-merge dogfood row.

---

## What P0–P4 shipped (code)

| Area | Shipped |
|------|---------|
| L2 | Greptile-shaped issue comment; `normalize_llm_issue_comment`; **one issue comment per PR** (reuse across pushes) |
| L1 | G10 `in_progress` → `completed`; check name **`Revy Review`**; **advisory** conclusion (`neutral` for findings, `success` clean — Greptile parity) |
| L3 | Inline error/critical/warning/info when line-accurate; thread map in `summary_json`; superseded-thread resolve via GraphQL |
| Ops | Greptile + Bugbot wired to program docs; babysit on #52 (Greptile + Revybot) |

**Dogfood:** PR #52 self-review — partial L1/L2/L3 evidence before merge; full row after staging deploy. See [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md).

---

## P5 candidates (priority order — draft)

| ID | Topic | Source | Severity |
|----|--------|--------|----------|
| **GS-F1** | **Auto-resolve Revybot review threads** when finding fixed/dismissed or absent on next publish (Greptile parity; today manual `resolveReviewThread`) | PR #52 dogfood RC-D6 extension | **high** — UX |
| **GS-F2** | GraphQL thread lookup pagination (`first: 100` / `first: 20`) — cursor or batch | Revybot rev 4–5 | medium |
| **GS-F3** | N+1 GraphQL calls in `_resolve_superseded_inline_threads` — batch lookup | Revybot rev 4–5 | medium |
| **GS-F4** | Same-SHA re-review: superseded threads when publish re-runs without new inline | Revybot rev 5 | medium — verify after deploy |
| **GS-F5** | Publish tests: reduce ordered `session.scalars` side_effect fragility | Greptile + Revybot | low — maintainability |
| **GS-F6** | Inline skipped when finding has no linked `group_id` — log or harden | Revybot rev 4 | low |
| **GS-F7** | Post-merge staging deploy + **human dogfood row** (L1/L2/L3 on next real PR) | P0.4/P0.5 gates | **gate** |

---

## Track B (unchanged — not P5)

- Recall / empty findings vs Greptile on code hunks (H3)
- STRUCT / cross-file context
- Workspace `.revy/rules` (RC4)

---

## Next doc step

1. Merge PR #52.
2. Deploy staging; append dogfood row.
3. Run `create-findings` on this file + fresh dogfood → **general plan** for P5+ (or named wave).
4. Optional tag `review-github-v1` after first external-demo-quality PR.
