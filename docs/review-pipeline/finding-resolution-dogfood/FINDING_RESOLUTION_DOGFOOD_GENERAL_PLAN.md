# Finding resolution dogfood — general plan

**Baseline:** [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) (2026-07-29)  
**Prerequisite:** [finding-resolution P0–P5](../finding-resolution/FINDING_RESOLUTION_GENERAL_PLAN.md) shipped on `main`; [PSA #63](../publish-summary-alignment/PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md) dogfood complete.

**Thesis:** Close the **resolution lifecycle** gaps exposed when PSA validated two-block publish but fix pushes did not update G9 prose, `summary_json.resolution`, block-2 counts, or inline threads — using isolated staging dogfood with **one push per agent cycle**.

**North star:** Fix push on chore PR → `denominator_active_prior` ≥ 1, `transitions_addressed` ≥ 1, G9 prose not `n/a`, `pr_active_count` shrinks, stale inline collapses.

**Locked (from findings):** FR-DG1 + FR-DG2 on `chore/finding-resolution-staging-dogfood`; MR-DG1 on separate `chore/moonshot-formatter-signature`; RCX / judge-json out of scope; superseded publish (`skipped_not_head`) invalidates resolution sign-off for that push pair.

---

## Cross-cutting (every phase)

- **Unit tests** — closure, manifest math, publish filter parity, prompt regression for MR-DG1.
- **Trace** — `summary_json.resolution` + reconcile `resolution_pass` manifest; operator fills staging memo from DB + GitHub.
- **Dogfood discipline** — one commit per agent cycle; deploy-boundary `--since`; no probe + doc in same push.
- **i18n** — N/A (backend + operator docs only this program).

---

## P0 — Repro harness & resolution observability

**Goal:** Minimal staging probe and operator visibility so each later phase can prove pass/fail without PSA noise.

**Scope — in:** Ephemeral backend probe fixture + unit hook; `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md` stub; metrics script extension for `summary_json.resolution` / `generation_active_count` / `pr_active_count` (read-only probes).

**Scope — out:** Closure logic changes; Moonshot prompt edits.

**Deliverables:** Probe module + tests; staging memo template; script flags or JSON fields documented for operator.

**Depends on:** `main` post-#63 merge + deploy boundary recorded.

---

## P1 — FR-DG1: manifest pairing & G9 denominator

**Goal:** Fix push that **publishes** produces non-zero prior-active denominator and addressed transitions; G9 block not `n/a`.

**Scope — in:** `apply_resolution_status_for_synchronize` + `build_resolution_pass_manifest` pairing across revisions; correct prior revision when intermediate rev was `skipped_not_head`; G9 prose gate when `denominator_active_prior` > 0.

**Scope — out:** Stale-fingerprint retirement (P2); Moonshot FP (P4).

**Deliverables:** Backend fix + unit tests; staging memo push-2 row showing `resolution.addressed` ≥ 1 and G9 prose populated.

**Depends on:** P0.

---

## P2 — FR-DG2: stale group retirement & thread collapse

**Goal:** When flagged code is removed and fingerprint absent, group closes (`absent_and_addressed` or equivalent), block 2 shrinks, inline thread resolves per GH-1v2.

**Scope — in:** Pass 2 reconcile closure for absent fingerprint + addressed stamp; PR-wide `verdict_groups` / publish set excludes closed groups; `_resolve_stale_inline_threads` for orphaned lines.

**Scope — out:** New Moonshot discovery rules; human dismiss API.

**Deliverables:** Backend fix + unit tests; staging memo showing `pr_active_count` decrease and collapsed inline on fix push.

**Depends on:** P1 (manifest must fire before collapse is meaningful).

---

## P3 — Staging dogfood sign-off

**Goal:** Operator sign-off on post-deploy worker — 3-push sequence (introduce → fix → optional re-introduce) all PASS.

**Scope — in:** Fill staging validation memo; run shared metrics script at deploy boundary; close chore PR or merge memo-only per SV-Q7.

**Scope — out:** Production feature work; RCX / judge-json gates.

**Deliverables:** Completed `*_STAGING_VALIDATION.md`; FR-DG1 + FR-DG2 pass tables; index update in [staging-validation](../staging-validation/README.md).

**Depends on:** P1, P2.

---

## P4 — MR-DG1: Moonshot formatter signature (parallel track)

**Goal:** Moonshot does not false-positive valid `format_summary_comment(generation_groups=…, pr_active_groups=…)` calls.

**Scope — in:** Reviewer prompt / context in `moonshot_review.py`; unit test on prompt contents or integration fixture.

**Scope — out:** Resolution pipeline; publish formatter signature change.

**Deliverables:** Prompt fix + tests; optional tiny dogfood PR or PSA-style repro in diff; note in findings registry **closed**.

**Depends on:** P0 (can ship in parallel with P1–P3 on separate branch).

---

## Waves

| Wave | Phases | Branch |
|------|--------|--------|
| **A — resolution closure** | P0 → P1 → P2 → P3 | `chore/finding-resolution-staging-dogfood` |
| **B — review quality** | P4 | `chore/moonshot-formatter-signature` (parallel after P0) |

---

## Open item

**Root-cause confirmation for FR-DG1:** P0 dogfood push 1 must reproduce `0/0 prior active` on a **single-publish** fix push before P1 codes a fix — if repro only occurs with supersede, P1 scopes to prior-revision selection; if Pass 1 never stamps, P1 scopes to synchronize timing.

**Next step:** **`execution-peer-review`** → attach `finding-resolution-dogfood/` + **`phase-execution`** on [P0](./waves/FINDING_RESOLUTION_DOGFOOD_P0_EXECUTION.md).
