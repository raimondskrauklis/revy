# Finding resolution — execution index

**Program:** [../README.md](../README.md) · **Baseline:** [FINDING_RESOLUTION_FINDINGS.md](../FINDING_RESOLUTION_FINDINGS.md) · **General plan:** [FINDING_RESOLUTION_GENERAL_PLAN.md](../FINDING_RESOLUTION_GENERAL_PLAN.md)

**Authority:** [REVIEW_PIPELINE_FINDINGS.md](../../REVIEW_PIPELINE_FINDINGS.md) R5-Q1–Q3 · [REVIEW_QUALITY_R5_RESOLUTION_METRICS_GENERAL_PLAN.md](../../review-quality/REVIEW_QUALITY_R5_RESOLUTION_METRICS_GENERAL_PLAN.md) · FR-Q11–FR-Q15 (peer review 2026-07-28)

**Goal:** After each push, close flagged issues in layers (diff → reconcile → verify judge) and surface **resolution rate** + addressed / dismissed / still open on GitHub + API.

**Branch:** `feat/finding-resolution` from `main`

## How we work (locked)

```text
P0 → P1 → P2 → P3 → P4 → P5
each phase: implement → pytest gate → Bugbot → local commit (operator pushes + validates staging)
```

**Operator LOOP:** Agent stops at **phase boundary** — no `git push`. Fill [FINDING_RESOLUTION_STAGING_VALIDATION.md](../FINDING_RESOLUTION_STAGING_VALIDATION.md) after each deploy check.

**LOOP pause:** after **P0.2** migration `0028` applied in deploy environments before P1 code relies on columns.

## Decisions locked for execution

- **FR-Q1–FR-Q15:** see [general plan](../FINDING_RESOLUTION_GENERAL_PLAN.md) — no re-decide in LOOP.
- **R5-Q3:** Discovery judge gate unchanged; Pass 3 cap **5/run** separate from `JUDGE_MAX_PER_RUN=10`.
- **Compare:** Pass 1 + Pass 3 use **push delta** (`prior.head_sha → new.head_sha`); discovery judge uses **full PR** (`base_sha → head_sha`).
- **FR-Q12:** Resolution rate = **transitions** this push pair on reconcile manifest; denominator = **`active` on N−1 at sync** (stamp cohort), exclude `compare_failed` and groups already `resolved` before sync.
- **FR-Q13:** `absent_and_addressed` re-opens on re-report; judge/human dismiss stays `resolved`.
- **Trace split (locked):** **Judge** step artifact — verification candidate/outcome detail (P2). **Reconcile** step `resolution_pass` sub-artifact — FR-Q12 transition metrics (P3.1, after Pass 3).
- **Reconcile trace (locked):** P1 moves `record_reconcile_pipeline_step` to **end of worker** (after transitions in P3); P3.1 writes `resolution_pass` via `record_reconcile_pipeline_step` + `_upsert_step_manifest` (not a second reconcile step).
- **Verification judge home (locked):** `verify_still_open_escalation_groups` + `VERIFICATION_JUDGE_MAX_PER_RUN` in `github_finding_closure.py` — discovery judge stays in `github_finding_judge.py`.
- **i18n:** EN + LV for reviewer resolution labels in **P4.5** (`locales/en.json` + `lv.json`).
- **Migrations:** hand-written only — `0028_finding_resolution_closure` in P0; **LOOP pause** after P0.2.

## LOOP order

| Phase | Focus | Execution | Commit | Status |
|-------|--------|-----------|--------|--------|
| P0 — Closure model | Schema `0028`, enums, compare helper, rules | [FINDING_RESOLUTION_P0_EXECUTION.md](./FINDING_RESOLUTION_P0_EXECUTION.md) | `76e8784` | done |
| P1 — Pass 1 + 2 | Sync stamp + reconcile closure on push | [FINDING_RESOLUTION_P1_EXECUTION.md](./FINDING_RESOLUTION_P1_EXECUTION.md) | `c0522ec` / `97a7e01` | done |
| P2 — Pass 3 verify | Escalation re-check judge (5/run) | [FINDING_RESOLUTION_P2_EXECUTION.md](./FINDING_RESOLUTION_P2_EXECUTION.md) | `c0522ec` | done |
| P3 — Metrics | FR-Q12 manifest, G9, API fields | [FINDING_RESOLUTION_P3_EXECUTION.md](./FINDING_RESOLUTION_P3_EXECUTION.md) | `73401aa` | done |
| P4 — Hardening | Human dismiss, RG-6, summary parity | [FINDING_RESOLUTION_P4_EXECUTION.md](./FINDING_RESOLUTION_P4_EXECUTION.md) | `8b453aa` | done |
| P5 — Staging + docs | Validation memo, program closeout | [FINDING_RESOLUTION_P5_EXECUTION.md](./FINDING_RESOLUTION_P5_EXECUTION.md) | (P5) | done (docs) |

**Peer review:** architecture + execution peer review (2026-07-28) — two passes; all critical/high gaps fixed in execution files.

**Reconcile worker order (locked):** `reconcile_review_run` (FR-Q13 re-open) → Pass 2 closure → discovery `record_review_run_judge_status` → Pass 3 verification → **`compute_resolution_transitions` + `record_reconcile_pipeline_step` (`resolution_pass`)** → `record_judge_pipeline_step` → `enqueue_publish`.

**Note:** Today `reconcile_tasks.py` records reconcile + judge steps mid-worker; **P1** reorders closure before discovery judge; **P3.1** moves reconcile-step recording to after transitions and adds `resolution_pass`.
