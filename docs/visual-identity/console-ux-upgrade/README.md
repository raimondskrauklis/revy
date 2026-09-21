# console-ux-upgrade/README.md

# Console UX + mobile/layout upgrade

**Status:** findings baselined, general plan written, architecture peer review complete, execution plans written, execution peer review pass 1 + pass 2 delta complete. Next: `phase-execution` LOOP.

This program rebuilds the reviewer page as a real operator console and makes the entire app shell responsive from phone to desktop. No new APIs. No diff viewer. No landing changes.

## Docs

| Doc | Purpose |
|-----|---------|
| [UIUX_CONSOLE_FINDINGS.md](./UIUX_CONSOLE_FINDINGS.md) | Console UX audit — merge verdict, findings table, settings, marketing, terminology, loading states (12 findings) |
| [MOBILE_AND_LAYOUT_FINDINGS.md](./MOBILE_AND_LAYOUT_FINDINGS.md) | Mobile + layout audit — sidebar hamburger/collapse, settings nav flatten, container widths, responsive tables, DevNotice token, bottom tab bar (7 findings) |
| [UIUX_CONSOLE_GENERAL_PLAN.md](./UIUX_CONSOLE_GENERAL_PLAN.md) | Combined general plan: P0 (shell/sidebar), P1 (findings UX + merge verdict), P2 (responsive tables), P3 (polish + bottom nav) |
| [reviews/architecture-peer-review/](./reviews/architecture-peer-review/) | Architecture peer review — pass 1 + pass 2 delta complete (BLOCK: no) |
| [reviews/execution-peer-review/](./reviews/execution-peer-review/) | Execution peer review — pass 1 + pass 2 delta complete (0 critical, 0 high, BLOCK: no) |

## Execution plan

Linear LOOP order. Frontend-only, all 4 phases.

| Phase | Focus | File | Status |
|-------|-------|------|--------|
| P0 | Shell, sidebar & responsive layout | [CONSOLE_UX_UPGRADE_P0_EXECUTION.md](./CONSOLE_UX_UPGRADE_P0_EXECUTION.md) | pending |
| P1 | Findings UX & merge verdict | [CONSOLE_UX_UPGRADE_P1_EXECUTION.md](./CONSOLE_UX_UPGRADE_P1_EXECUTION.md) | pending |
| P2 | Responsive tables | [CONSOLE_UX_UPGRADE_P2_EXECUTION.md](./CONSOLE_UX_UPGRADE_P2_EXECUTION.md) | pending |
| P3 | Polish, empty states & bottom nav | [CONSOLE_UX_UPGRADE_P3_EXECUTION.md](./CONSOLE_UX_UPGRADE_P3_EXECUTION.md) | pending |

## Phase summary

| Phase | Subphases | Key deliverables |
|-------|-----------|-----------------|
| P0 | 6 (P0.1–P0.6) | `SidebarProvider`, `AppSidebar`, hamburger/sheet, collapse/icon rail, settings flatten, container widths |
| P1 | 6 (P1.1–P1.6) | `'failure'` wired, `MergeReadinessBadge` states, `FindingsSummaryBar`, `FindingsToolbar`, `FindingDetailSheet`, loading skeletons |
| P2 | 5 (P2.1–P2.5) | Card layouts: findings, PR list, repo list, installations, Team table; sticky Actions desktop |
| P3 | 6 (P3.1–P3.6) | Token fix, `MobileBottomNav`, empty states (PR list + repo list), settings stubs, terminology tooltips, `/reviewer` flash fix, doc-sync + changelog |

## Dependencies

```
P0 ──→ P1 ──→ P2
 │                    │
 └──────────→ P3 ←───┘
```

- P0: foundation — everything depends on the responsive shell
- P1: depends on P0 (sheet/drawer primitives)
- P2: depends on P0 (shell) + P1 (findings table already redesigned)
- P3: depends on P0 (shell for bottom nav slot) + P1 (findings toolbar exists)

## Boundaries

- No new APIs. No diff viewer. No workspace inbox.
- Build on existing routes, hooks, and types from VI-Q9 (P0–P4 shipped).
- Landing stays as-is — thin costume, single CTA, no slop.

## Next

1. ~~`execution-peer-review` on all 4 execution files~~ ✅ [pass 1](./reviews/execution-peer-review/pass-01-2026-09-20.md) + [pass 2 delta](./reviews/execution-peer-review/pass-02-2026-09-20-delta.md) complete — 0 critical, 0 high, BLOCK: no
2. `phase-execution` LOOP (P0 → P1 → P2 → P3)
