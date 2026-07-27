# Post review-quality — follow-ups (next program seed)

**Superseded by:** [github-surface-hardening/](../github-surface-hardening/README.md) — findings baseline written 2026-07-27.

This file remains as the PR #52 backlog snapshot. Use [GITHUB_SURFACE_HARDENING_FINDINGS.md](../github-surface-hardening/GITHUB_SURFACE_HARDENING_FINDINGS.md) for planning.

---

## What P0–P4 shipped (code)

| Area | Shipped |
|------|---------|
| L2 | Greptile-shaped issue comment; `normalize_llm_issue_comment`; **one issue comment per PR** (reuse across pushes) |
| L1 | G10 `in_progress` → `completed`; check name **`Revy`**; **advisory** conclusion (`neutral` for findings, `success` clean — Greptile parity) |
| L3 | Inline error/critical/warning/info when line-accurate; thread map in `summary_json`; superseded-thread resolve via GraphQL |
| Ops | Greptile + Bugbot wired to program docs; babysit on #52 (Greptile + Revybot) |

**Dogfood:** PR #52 self-review — partial L1/L2/L3 evidence. See [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md).

---

## Backlog → hardening findings

| Seed ID | Hardening ID |
|---------|----------------|
| GS-F1 Auto-resolve threads | **GH-1** |
| GS-F2 GraphQL pagination | **GH-2** |
| GS-F3 N+1 GraphQL | **GH-3** |
| GS-F4 Same-SHA re-review | **GH-4** |
| GS-F5 Test mocking | **GH-6** |
| GS-F6 Missing group_id | **GH-5** |
| GS-F7 Staging dogfood | **GH-7** |

---

## Track B (unchanged)

- Recall / empty findings vs Greptile on code hunks (H3)
- STRUCT / cross-file context
- Workspace `.revy/rules` (RC4)
