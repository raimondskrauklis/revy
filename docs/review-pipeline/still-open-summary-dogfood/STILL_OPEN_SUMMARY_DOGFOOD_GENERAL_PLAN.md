# Still-open summary vs inline collapse — general plan

**Baseline:** [STILL_OPEN_SUMMARY_DOGFOOD_FINDINGS.md](./STILL_OPEN_SUMMARY_DOGFOOD_FINDINGS.md) (2026-08-07)  
**Evidence PR:** kp-platform [#491](https://github.com/raimondskrauklis/kp-platform/pull/491)

**Thesis:** On **new publishes** after #83, inline thread collapse and block 2 / verdict / G9 copy stay aligned. Fix the **current implementation** when dogfood finds bugs.

**Execution:** [waves/STILL_OPEN_SUMMARY_DOGFOOD_EXECUTION.md](./waves/STILL_OPEN_SUMMARY_DOGFOOD_EXECUTION.md)

---

## Locked decisions

| ID | Decision |
|----|----------|
| SOS-D1 | Block 2 omits collapsed-not-publishable fingerprints (`filter_pr_active_groups_for_summary`) |
| SOS-D2 | `already_resolved` on GitHub is successful collapse (#83) |
| SOS-D3 | Cross-revision memory in `summary_json.collapsed_inline_fingerprints` |
| SOS-D4 | **No backfill** for pre-#83 PRs |
| SOS-D5 | Option-A DB rows may stay `active`/`still_open` |
| SOS-D6 | Reconcile Pass 1 changes → finding-resolution |
| SOS-D7 | Omit never-inlined orphans from block 2 when not in generation (P1) |
| SOS-D8 | G9 / resolution block use display still-open count from filtered verdict (P1) |

---

## P0 — Forward path (#83) — **shipped**

Merged `a5bb273` `2026-08-07`; validated #491 rev 1→2.

---

## P1 — SOS-5 orphan filter + metrics — **in progress**

**Goal:** Clean generation + all inline collapsed → no ghost block-2 row; G9/confidence align.

**Deliverables:** See [P1 execution](./waves/STILL_OPEN_SUMMARY_DOGFOOD_P1_EXECUTION.md).

---

## P2 — Sign-off

**Goal:** Dogfood PASS post-P1; README Done.

**Depends on:** P1 deployed.

---

## Out of scope

- SOS-1 / backfill (#489)
- Reconcile Pass 1 (SOS-2)
- `compute_check_conclusion` PR-wide alignment
