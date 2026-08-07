# Finding resolution — general plan

**Baseline:** [FINDING_RESOLUTION_FINDINGS.md](./FINDING_RESOLUTION_FINDINGS.md) (2026-07-28)  
**Prerequisite:** R5 reconcile + judge, RQ6 `resolution_status`, generation lifecycle HEAD gate, judge input quality P0–P5 on `main`.

**Thesis:** Revy **closes** flagged issues in **layers** after each new push — fast diff signal first, reconcile + publish hygiene second, judge re-verification third — and **surfaces metrics** (resolution rate, addressed/dismissed/still open) on GitHub + API. Distills **Bugbot** (resolution-rate north star, re-check on HEAD) and **Greptile v4** (LLM addressed detection) into one pipeline without optimizing comment volume.

**North star KPI:** **resolution rate** per push pair (N−1→N) — **transitions only** (new closures this pair), not re-stamped statuses. See **FR-Q12**.

**Peer review:** Architecture peer review (2026-07-28) incorporated below — **FR-Q11–FR-Q15** lock execution edges before P1 ships.

---

## Locked decisions (from findings + operator)

| Q# | Decision |
|----|----------|
| **FR-Q1** | User-facing labels: **Addressed** (dev fixed), **Dismissed** (false positive), **Still open**, **Superseded** (identity replaced). Backend enums stay `resolution_status` + `group.state`. |
| **FR-Q2** | **Yes** — `addressed` closes group (`state=resolved`) after **closure rules** fire (not on heuristic alone mid-sync without reconcile guard). |
| **FR-Q3** | **Yes** — fingerprint **absent** on revision N + `resolution_status=addressed` on N−1 → close with method `absent_and_addressed`. |
| **FR-Q4** | **Yes** — Pass 3 verification judge on **FR-Q11 escalation set** (max 5/run, separate from discovery `JUDGE_MAX_PER_RUN=10`). |
| **FR-Q6** | **Layered** — Pass 1 push-delta diff; Pass 3 judge for escalation still-open; no full-PR re-review. |
| **FR-Q7** | **Two summary blocks** — (1) **This generation** publishable (matches inline). (2) **Still open on PR** — PR-wide groups still open for the author: `state=active`, not `resolution_status=addressed`, and not scheduled for GH-1v2 inline thread collapse (`filter_pr_active_groups_for_summary` in `github_publish_formatter.py`). Inline = generation only. |
| **FR-Q8** | **Yes** — document RG-6: any missing discovery-judge outcome → `skipped_unavailable` (already); add tests for partial LLM failure. |
| **FR-Q9** | **Superseded by FR-Q12** — transitions-only rate on manifest. |
| **FR-Q5** | Human dismiss — **P4** workspace `Permission.admin_users` API; full R7.6 UI defer. |
| **FR-Q10** | Post-merge batch re-check — **defer** v1.1. |
| **FR-Q11** | Pass 3 escalation set: `still_open` + `is_judge_candidate` + `last_seen_revision_id == prior_revision` + not `compare_failed`. |
| **FR-Q12** | Rate = transitions this pair / denominator (`active` on N−1 at sync, exclude `compare_failed` and pre-sync `resolved`). Persist on reconcile manifest — not live row scan. **Wave C (CS-Q6):** hygiene path-removed closures (`last_seen` outside pairing cohort) excluded from numerator/denominator — see [closure-scope findings](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md). |
| **FR-Q13** | Re-open: `absent_and_addressed` → re-report same fingerprint **re-opens** (`active`). `judge_dismissed` / `human_dismissed` → stay `resolved` until human or verification dismiss. |
| **FR-Q14** | Same as FR-Q7 — locked for execution cross-ref. |
| **FR-Q15** | Human dismiss auth: workspace installation route + `Permission.admin_users` (not platform super-admin). |

**Closure timing:** Developer push lands → revision N created → **Pass 1** stamps prior groups on `synchronize` → pipeline runs → **Pass 2** reconcile/publish closes threads → **Pass 3** verification judge before publish when configured. GitHub shows updated counts on **publish of revision N** (issue comment + optional inline resolve). DB may record closure earlier; **display** updates at publish.

---

## Multi-pass model (Revy vs vendors)

| Pass | When | Method | Bugbot analog | Greptile analog |
|------|------|--------|---------------|-----------------|
| **1 — Fast** | `synchronize` (before index) | Compare diff → `resolution_status` | Push landed | — |
| **2 — Identity** | After Moonshot + reconcile | Absent fingerprint + addressed → `resolved`; judge dismiss (existing) | Thread gone from HEAD set | Comment not in new review |
| **3 — Verify** | Reconcile, before publish | Judge re-check prior escalation still-open; outcomes `upheld` / `dismissed` (reuse discovery enum); push-delta patches | Re-check prior flags | LLM-as-judge “addressed” |
| Pass 4 — Surface | Publish | G9 prose + metrics block + **GH-1v2** thread resolve (Option A + B + outdated) + **summary/DB sync** (`filter_pr_active_groups_for_summary`, `_close_active_groups_for_fingerprints`) | Resolution rate UX | Addressed % in summary |

**Better than vendors for Revy:** structured `group_id` + fingerprint (not comment text matching); evidence-backed Pass 3 (not prose-only); Pass 1 free (compare API); judge only on escalation subset (cost control).

---

## Cross-cutting (every phase)

- **Unit tests** — closure rules, metrics math, publish filter parity, judge pass caps.
- **Trace** — `resolution_pass` sub-artifact on **reconcile** step manifest (pass counts, methods, resolution_rate, `compare_failed`). Written once at end of reconcile worker (P3.1). No new `PipelineStepType` v1.
- **Reconcile worker** — `reconcile_review_run` → Pass 2 → discovery judge → Pass 3 verify → transitions + reconcile trace → judge trace → publish enqueue.
- **Tenancy** — workspace-scoped reads; no cross-PR leakage.
- **i18n** — EN + LV for reviewer UI metric labels (`t()`); backend enums snake_case.
- **No silent closure** — compare failure → `still_open` + `closure_blocked_reason=compare_failed` (column or manifest; P1 must distinguish from “file not in diff”).
- **Compare ranges** — Pass 1 + Pass 3: **push delta** (`prior.head_sha → new.head_sha`). Discovery judge: **full PR** (`base_sha → head_sha`). Shared `fetch_compare_patches` helper.
- **Re-open** — **FR-Q13** (not heuristic-only vague rule).

---

## P0 — Closure model & schema

**Goal:** One closure contract — `resolution_method`, `resolved_at_revision_id`, optional `closure_blocked_reason`; rules module shared by sync, reconcile, judge.

**Scope — in:** Hand-written migration (`0028`); `resolution_method`, `resolved_at_revision_id`, optional `closure_blocked_reason` on `github_finding_groups`; `ResolutionMethod` enum (`absent_and_addressed`, `judge_dismissed`, `verification_dismissed`, `human_dismissed`); closure rules module; shared `fetch_compare_patches(base_sha, head_sha)`; Pass 1 stamps `resolution_status` only (no state flip).

**Scope — out:** Judge prompt changes; UI; new `PipelineStepType`.

**Deliverables:** ORM + migration; closure rules module + tests; findings/doc registry R5-Q1 title fix.

**Depends on:** `main` through `0027`.

---

## P1 — Pass 1 + Pass 2 closure on push

**Goal:** After new push, prior flags **close** when diff says addressed and Moonshot does not re-raise same fingerprint.

**Scope — in:** `apply_resolution_status_for_synchronize` threads `compare_failed` from fetch; reconcile worker reorder: `reconcile_review_run` → **Pass 2 closure** → discovery judge (defer `record_reconcile_pipeline_step` to P3.1); absent+addressed → `resolved` + method; addressed+re-reported → keep `active` (FR-Q13); Option A on closed groups.

**Scope — out:** Pass 3 judge.

**Deliverables:** Push-to-close behavior for typical fix; unit + integration tests; staging dogfood checklist row.

**Depends on:** P0.

---

## P2 — Pass 3 verification judge

**Goal:** FR-Q11 escalation groups still `still_open` after Pass 1–2 get verification judge with **push-delta** evidence — `upheld` → stay open; `dismissed` → close (`resolution_method=verification_dismissed`).

**Scope — in:** `verify_still_open_escalation_groups()` in **`github_finding_closure.py`**, wired from `reconcile_tasks` **after** discovery judge, **before** transitions/publish; verification prompt + `judge_purpose` on outcome row; cap 5/run; push-delta patches via shared compare helper.

**Scope — out:** Non-escalation warnings; `still_valid` as new enum value.

**Deliverables:** Pass 3 wired in `reconcile_tasks`; tests; pipeline GET shows verification outcomes.

**Depends on:** P0, judge input quality on `main`.

---

## P3 — Metrics & display

**Goal:** Operators and developers see **resolution rate** and counts after each push.

**Scope — in:** Reconcile manifest `resolution_metrics` (FR-Q12 transitions); refactor `count_resolution_status` to use `resolution_method` (not `state==resolved` → judge_dismissed for all); G9 + metrics block (addressed / dismissed breakdown / still open / rate %); reconciled API exposes `resolution_status`, `resolution_method`, `resolved_at_revision_id`.

**Scope — out:** Workspace analytics dashboard; Langfuse.

**Deliverables:** Visible GitHub summary metrics; API fields; formatter tests; EN+LV strings for UI labels.

**Depends on:** P1 (closure methods populated).

---

## P4 — Human dismiss + hardening

**Goal:** Admin can dismiss without judge; judge status honest; summary/inline parity.

**Scope — in:** `POST …/finding-groups/{id}/dismiss` on installation route (`Permission.admin_users`); `resolved` + `resolution_method=human_dismissed`; RG-6 tests (partial LLM failure → `skipped_unavailable`); FR-Q7 two-block summary implementation.

**Scope — out:** Full R7.6 ack/merge UX.

**Deliverables:** API + unit tests; Babysit-grade publish parity test.

**Depends on:** P0, P3.

---

## P5 — Staging gate & doc sync

**Goal:** Prove resolution rate and closure on staging PR (fix → push → metrics → thread resolve).

**Scope — in:** `FINDING_RESOLUTION_STAGING_VALIDATION.md`; recovery checklist track; row for compare API failure → no false addressed; update [README](./README.md) status.

**Scope — out:** Tag; production sign-off.

**Deliverables:** Before/after metrics table; dogfood log entry; program marked **shipped** on branch merge.

**Depends on:** P1–P4.

---

## Out of scope (program)

Post-merge Bugbot-class batch (FR-Q10); workspace policy rules; retroactive backfill; changing R5-Q3 discovery judge gate; Moonshot prompt volume tuning.

---

## Next step

**`phase-execution`** from [waves/FINDING_RESOLUTION_EXECUTION.md](./waves/FINDING_RESOLUTION_EXECUTION.md) on `feat/finding-resolution`. Staging dogfood validates Pass 1–3 as phases land.
