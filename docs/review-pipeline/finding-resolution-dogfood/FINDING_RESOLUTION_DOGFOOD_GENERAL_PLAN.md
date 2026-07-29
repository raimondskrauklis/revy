# Finding resolution dogfood — general plan

**Baseline:** [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) (2026-07-29)  
**Prerequisite:** [finding-resolution P0–P5](../finding-resolution/FINDING_RESOLUTION_GENERAL_PLAN.md) shipped on `main`; [PSA #63](../publish-summary-alignment/PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md) dogfood complete.

**Thesis:** Close the **resolution lifecycle** gaps exposed when PSA validated two-block publish but fix pushes did not update G9 prose, `summary_json.resolution`, block-2 counts, or inline threads — using isolated staging dogfood with **one push per agent cycle**.

**North star:** Fix push on chore PR → `denominator_active_prior` ≥ 1, `transitions_addressed` ≥ 1, G9 prose not `n/a`, `pr_active_count` shrinks, stale inline collapses.

**Locked (from findings):** FR-DG1 + FR-DG2 on `chore/finding-resolution-staging-dogfood`; MR-DG1 on separate `chore/moonshot-formatter-signature`; RCX / judge-json out of scope; superseded publish (`skipped_not_head`) invalidates resolution sign-off for that push pair.

---

## Deploy boundaries (operator)

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| **PSA baseline** | `2026-07-29T11:38:12Z` | P0 metrics sanity only — [PSA memo](../publish-summary-alignment/PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md) |
| **FR-DG1** | deploy job completion after **P1 merge to `main`** | P1.4 dogfood push 2 |
| **FR-DG2 + program sign-off** | deploy job completion after **P2 merge to `main`** | P2.4 dogfood push 3; P3.1 final metrics |

**Cadence (locked):** feature phase merges to `main` → droplet deploy completes → **then** chore PR dogfood push. Never validate FR-DG1/FR-DG2 on staging before the matching phase is deployed.

---

## Cross-cutting (every phase)

- **Unit tests** — closure, manifest math, publish filter parity, prompt regression for MR-DG1.
- **Trace** — reconcile `resolution_pass` manifest + `summary_json.resolution` + issue-comment G9; operator fills staging memo from DB + GitHub.
- **Dogfood discipline** — one commit per agent cycle; correct `--since` per table above; no probe + doc in same push.
- **i18n** — N/A (backend + operator docs only this program).

---

## P0 — Repro harness & resolution observability

**Goal:** Minimal staging probe and operator visibility so each later phase can prove pass/fail without PSA noise.

**Scope — in:** Ephemeral backend probe fixture + unit hook; `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md` stub (incl. deploy-boundary table); metrics script extension for publish `summary_json` fields (read-only).

**Scope — out:** Closure logic changes; Moonshot prompt edits.

**Deliverables:** Probe module + tests; staging memo template; script `publish_summary` block.

**Depends on:** `main` post-#63; PSA boundary for P0 metrics reference only.

---

## P1 — FR-DG1: manifest pairing & G9 denominator

**Goal:** Fix push that **publishes** produces non-zero prior-active denominator and addressed transitions; G9 + resolution metrics block reflect manifest (not `n/a`).

**Scope — in:** Shared **last-published prior revision** helper wired in `reconcile_tasks`, `github_resolution_metrics`, `github_finding_closure`; manifest `denominator_active_prior` / `transitions_addressed`; G9 + `summary_json.resolution` sourced from `resolution_metrics_manifest`.

**Scope — out:** Pass 2 group `state=resolved` on code removal (P2); Moonshot FP (P4).

**Deliverables:** Backend fix + unit tests; **merge to `main` + deploy**; staging memo push-2 row (FR-DG1 only — wire/fix probe, not remove file).

**Depends on:** P0.

---

## P2 — FR-DG2: stale group retirement & thread collapse

**Goal:** When flagged code is **removed** and fingerprint absent, group closes, block 2 shrinks, inline thread resolves per GH-1v2.

**Scope — in:** `apply_pass2_closure_for_review_run` in `github_finding_closure.py`; shared prior-revision helper from P1; stale **active** groups drop from PR-wide set; `_resolve_stale_inline_threads` for orphaned lines.

**Scope — out:** Manifest denominator logic (P1); Moonshot discovery changes.

**Deliverables:** Backend fix + unit tests; **merge to `main` + deploy**; staging memo push-3 row (probe code **removal**).

**Depends on:** P1 deployed (manifest fires on push 2 before removal push 3).

---

## P3 — Staging dogfood sign-off

**Goal:** Operator sign-off on post-deploy worker; FR-DG1 + FR-DG2 pass tables filled; optional regrowth push.

**Scope — in:** Fill validation memo at **P2 deploy boundary**; close chore PR per [SV-Q7](../staging-validation/STAGING_VALIDATION_FINDINGS.md#sv-q-registry-locked--open); doc sync.

**Scope — out:** New closure logic; MR-DG1 (P4).

**Deliverables:** Completed `*_STAGING_VALIDATION.md`; findings FR-DG1/FR-DG2 closed; [staging-validation](../staging-validation/README.md) index updated.

**Depends on:** P1, P2 deployed; dogfood pushes 2–3 complete.

---

## P4 — MR-DG1: Moonshot formatter signature (parallel track)

**Goal:** Moonshot does not false-positive valid `format_summary_comment(generation_groups=…, pr_active_groups=…)` calls.

**Scope — in:** Reviewer prompt / context in `moonshot_review.py`; unit test on prompt contents.

**Scope — out:** Resolution pipeline; publish formatter signature change.

**Deliverables:** Prompt fix + tests; findings MR-DG1 **closed**.

**Depends on:** Program docs exist (P0.0); **no** probe or P1–P3 deploy required.

---

## Waves

| Wave | Phases | Branch |
|------|--------|--------|
| **A — resolution closure** | P0 → P1 → P2 → P3 | `chore/finding-resolution-staging-dogfood` + feature merges to `main` |
| **B — review quality** | P4 | `chore/moonshot-formatter-signature` (parallel after P0.0) |

---

## Open item (locked answer — peer review 2026-07-29)

**FR-DG1 pass criteria:** **Primary** = reconcile `resolution_pass` manifest (`denominator_active_prior` ≥ 1, `transitions_addressed` ≥ 1 on publish trace). **Surface** = G9 prose + `summary_json.resolution` must be wired from `resolution_metrics_manifest` in P1.3 (today `build_g9_resolution_prose` is generation-scoped on `ctx.groups` — that is the bug).

**Root-cause confirmation:** P1.1 repro test on `skipped_not_head` + last-published prior helper before staging push 2.

**Next step:** **`phase-execution`** on [P0](./waves/FINDING_RESOLUTION_DOGFOOD_P0_EXECUTION.md) (peer review applied).
