# Finding resolution — post–wave C D1 findings (FR-CS4 staging dogfood)

**Date:** 2026-07-30  
**Purpose:** Baseline for **D1** staging dogfood — structural in-file fix without line-region overlap → Pass 3 verification dismiss. No execution steps.

**Authority:** [backlog findings](./FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md) § FR-CS4 · [closure scope](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) § FR-CS4 · [D0 execution](./waves/FINDING_RESOLUTION_POST_WAVE_C_D0_EXECUTION.md) (shipped [#71](https://github.com/raimondskrauklis/revy/pull/71)).

**Parent program:** [post–wave C general plan](./FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md) · **M0** [#70](https://github.com/raimondskrauklis/revy/pull/70) + **D0** [#71](https://github.com/raimondskrauklis/revy/pull/71) merged.

---

## Build principles (D1)

1. **Hygiene is out of scope** — file/path deletion closes via Track A (CS-Q10). D1 repro must **edit the same file** without deleting it.
2. **Pass 1a unchanged** — `patch_touches_line_region` stays strict (PW-Q4). Fix must **not** overlap the finding's anchored line region.
3. **Pass 3 is the closure path** — expect `resolution_method=verification_dismissed`, not discovery `judge_dismissed`.
4. **Judge required on staging** — `settings.judge_llm_enabled()` must be true or Pass 3 is a no-op (`github_finding_closure.py:276–277`).
5. **Pass 3 fingerprint exclusion** — groups whose `fingerprint` appears in the current review run are excluded from Pass 3 (`pass3_verification_escalation_select` + post-load filter — `github_finding_closure.py:133–134`, `:309–311`). Push 2 must **not** re-report the probe finding.
6. **Per-group truth** — sign-off on `state` + `resolution_method` for the probe group id, not `pr_active_count` alone (VAL8).
7. **Operator cadence** — backend-only dogfood pushes; one push per Revy cycle; wait for publish before next commit.

---

## What exists (verified post–D0)

| Area | State | Evidence |
|------|-------|----------|
| Pass 1a line-region stamp | **Strict** | `patch_touches_line_region` — `github_resolution_metrics.py:32–64`, `130–132` |
| Pass 2 widen | **Shipped** | `addressed` groups outside pairing — `github_finding_closure.py:171–174` |
| Pass 3 widen | **Shipped (D0)** | `pass3_verification_escalation_select` + `verification_escalation_candidate_sql_filters` — `github_finding_closure.py:94–140` |
| Pass 3 cap | **5/run** | `VERIFICATION_JUDGE_MAX_PER_RUN`; `_verification_judge_slots_remaining` — `github_finding_closure.py:66`, `141–155` |
| Pass 3 fingerprint filter | **Shipped (D0)** | SQL `fingerprint.not_in(fingerprints_in_run)` + Python guard — `github_finding_closure.py:133–134`, `:309–311` |
| Verification dismiss fields | **Shipped** | `apply_resolution_method_on_verification_dismiss` — `github_finding_closure_rules.py` |
| FR-CS4 probe fixture | **Shipped** | `backend/app/services/fr_cs4_staging_probe.py` |
| Staging memo Wave D table | **Shipped** | [dogfood staging validation](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) Wave D |

---

## Problem restatement (FR-CS4)

Developer fixes a real defect **without** changing the diff hunk that contains the finding's anchored lines → Pass 1 leaves `resolution_status=still_open` → only Pass 3 verification judge can close.

**Wave C fixed:** deletion / path-gone hygiene (Track A) and Pass 2 for `addressed` absent fingerprints.  
**D0 fixed:** Pass 3 candidate cohort wall (`last_seen ∈ pairing_revision_ids` only).  
**D1 proves:** end-to-end on staging with a controlled probe PR.

---

## Probe design (locked)

| Item | Decision |
|------|----------|
| **Branch** | `chore/fr-cs4-structural-fix-staging` |
| **Fixture path** | `backend/app/services/fr_cs4_staging_probe.py` |
| **Push 1** | Introduce review-visible defect on **specific lines** (error + bug category — judge-eligible). Unit test imports fixture. |
| **Push 2** | Structural fix **elsewhere in the same file** — remove/refactor offending logic **outside** finding `start_line`/`end_line` region. **Not** file deletion. Probe fingerprint must be **absent** from push-2 review run (`gen=0`) — re-report excludes group from Pass 3. |
| **Moonshot visibility** | Defect must be real enough for ≥1 Revy finding on push 1 with anchored lines recorded in DB. |
| **Anti-pattern** | Do not fix by editing the anchored hunk (that would stamp `addressed` via Pass 1a and invalidate the experiment). Do not leave a re-reportable defect on push 2 (Pass 3 fingerprint exclusion). |

**Reference shape:** #67 push 2 removed a kwargs snippet in-file without overlapping the original finding lines — same failure mode, different fixture.

---

## Pass criteria (D1 sign-off)

| Check | Required | Notes |
|-------|----------|-------|
| Push 1 ≥1 active group on probe path | yes | Record `group_id`, `last_seen_revision_id`, `review_run_id` |
| Push 1 finding anchored lines documented | yes | For push 2 non-overlap proof |
| Push 2 diff does not touch finding line region | yes | Compare patch vs `start_line`/`end_line` |
| Push 2 probe fingerprint absent from review run (`gen=0`) | yes | Re-report → Pass 3 skips group → D1 FAIL |
| `judge_llm_enabled()` true on staging | yes | Pre-flight before push 1 |
| Group `state=resolved` after push 2 publish | yes | DB |
| `resolution_method=verification_dismissed` | yes | **Not** `judge_dismissed` (discovery) |
| Pass 3 judge outcome row exists | yes | `github_finding_judge_outcomes` with `judge_purpose=verification` |
| Deploy boundary recorded | yes | Post–#71 droplet deploy ISO in memo |

**FAIL examples:** stays `still_open`; `absent_and_addressed` (wrong pass); `judge_dismissed` only; Pass 3 skipped (judge disabled); probe fingerprint re-reported on push 2 (`gen>0`).

---

## Edge cases

| Case | Handling |
|------|----------|
| Moonshot does not flag probe on push 1 | Revise fixture (stronger defect); do not proceed to push 2. **#72 rev 1:** 0 publishable — likely post-M0 `format_summary_comment` kwargs pattern; see staging memo Wave D options **D1-O1**. |
| Moonshot re-reports probe finding on push 2 | **FAIL** — Pass 3 excludes `fingerprints_in_run`; revise push-2 fix so defect is gone without re-report |
| Discovery judge dismisses on push 1 | Document; may need separate group — primary metric is **verification** on push 2. Run D1-O7 DB query before probe revision. |
| Group outside Pass 3 SQL cohort | Should not happen post-D0 if `still_open` + aged `last_seen`; file bug if it does |
| `skipped_not_head` between pushes | Wait for publish; one push per cycle (FR-CS8 edge — monitor) |
| Revy timeout (900s) | Retry review; do not stack pushes |

---

## Decisions registry

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| **D1-Q1** | Dedicated probe fixture vs reuse `fr_dogfood`? | **locked** | **New** `fr_cs4_probe` — FR-DG probes are hygiene/FR-DG1, not structural-fix |
| **D1-Q2** | PASS resolution method? | **locked** | `verification_dismissed` (Pass 3) |
| **D1-Q3** | File deletion allowed on push 2? | **locked** | **No** — hygiene path; invalidates FR-CS4 |
| **D1-Q4** | Docs in dogfood pushes 1–2? | **locked** | **No** — VAL8 backend-only |
| **D1-Q5** | Primary metrics script? | **locked** | `judge_json_contract_staging_metrics --since <D0_deploy_iso>` + per-group SQL |
| **D1-Q6** | Push 2 may re-report probe finding? | **locked** | **No** — `fingerprints_in_run` excludes group from Pass 3; push 2 must leave `gen=0` for probe fingerprint |
| **D1-Q7** | Push 1 rev 1 zero findings — next step? | **locked** | **D1-O1** — non-formatter defect class on anchored lines; parallel **D1-O7** DB check. Reject kwargs-only retry (post-M0). See [staging memo](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) Wave D. |

---

## Parking lot

| Item | Notes |
|------|-------|
| FR-CS8 re-orphan after supersede | D2 optional; not a D1 blocker |
| Loosen Pass 1a line region | **Rejected** (PW-Q4) |
| Merge D1 with product PR | **Rejected** — chore branch only |

---

## Devil's advocate

| Risk | Mitigation |
|------|------------|
| Fix accidentally overlaps line region | Document lines on push 1; review diff before push |
| Judge disabled on staging | Pre-flight `judge_llm_enabled()`; block sign-off |
| Pass 3 cap exhausts on noisy PR | Probe PR should be minimal; cap is 5/run |
| Moonshot re-reports probe on push 2 | Document push-1 fingerprint; verify `gen=0` before sign-off; revise fixture if needed |
| Post-M0 formatter kwargs probe silent | **#72 rev 1** — use non-formatter defect (D1-O1); kwargs shape worked pre-M0 only (C3.1) |
| False PASS via Pass 2 | Require `verification_dismissed`, not `absent_and_addressed` |

---

## Experiment / verification

| Experiment | Pass |
|------------|------|
| `test_fr_cs4_probe.py` | Fixture import + defect shape unit test green |
| Staging push 1 | ≥1 Revy finding on probe file with group id captured |
| Staging push 1 retry | **#72 rev 1 FAIL** — 0 publishable; D1-O1 probe revision required |
| Staging push 2 | Group `resolved` + `verification_dismissed` + verification judge outcome row |
| Metrics window | `--since` post–#71 deploy shows verification judge activity |

---

## References

| Doc / code | Link |
|------------|------|
| D0 execution | [FINDING_RESOLUTION_POST_WAVE_C_D0_EXECUTION.md](./waves/FINDING_RESOLUTION_POST_WAVE_C_D0_EXECUTION.md) |
| D1 execution | [FINDING_RESOLUTION_POST_WAVE_C_D1_EXECUTION.md](./waves/FINDING_RESOLUTION_POST_WAVE_C_D1_EXECUTION.md) |
| VAL8 backend-only | [dogfood VAL8](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md) |
| Pass 3 E2E unit test | `test_verify_still_open_escalation_outside_pairing` |
| Staging metrics script | `backend/scripts/judge_json_contract_staging_metrics.py` |

**Next step:** [FINDING_RESOLUTION_POST_WAVE_C_D1_GENERAL_PLAN.md](./FINDING_RESOLUTION_POST_WAVE_C_D1_GENERAL_PLAN.md) → `phase-execution` from [D1 execution](./waves/FINDING_RESOLUTION_POST_WAVE_C_D1_EXECUTION.md).
