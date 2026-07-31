# docs/review-pipeline/finding-resolution-dogfood/FR_CS4_D1_PASS3_HANDOFF.md

# Agent handoff — FR-CS4 / Pass 3 verification (Wave D, D1 FAIL)

**Date:** 2026-07-31  
**Audience:** Implementer agent (full repo access assumed)  
**Status:** D1 staging dogfood **FAIL** — product gap identified; not a judge-LLM outage

**Related:** [staging validation memo](./FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) Wave D · [D1 findings](../finding-resolution/FINDING_RESOLUTION_POST_WAVE_C_D1_FINDINGS.md) · PR [#72](https://github.com/raimondskrauklis/revy/pull/72)

---

## Mission context

Revy’s finding-resolution pipeline must close findings when a developer fixes a defect **without editing the diff hunk that contains the finding’s anchored lines**. That scenario is **FR-CS4** (backlog § FR-CS4).

**Program state:**

| Phase | Status |
|-------|--------|
| **D0** ([#71](https://github.com/raimondskrauklis/revy/pull/71)) | Shipped — widened Pass 3 candidate SQL from pairing-window-only to PR-wide `still_open` escalation groups |
| **D1** ([#72](https://github.com/raimondskrauklis/revy/pull/72)) | **FAIL** at sign-off (D1.3) |
| **D3** | Pending — gap registry sync depends on FR-CS4 PASS vs documented blocker |

**Authority docs:**

| Doc | Path |
|-----|------|
| D1 baseline + pass criteria | `docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_POST_WAVE_C_D1_FINDINGS.md` |
| Staging evidence | `docs/review-pipeline/finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md` (Wave D) |
| Product definition | `docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md` § FR-CS4 |
| Execution checklist | `docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_POST_WAVE_C_D1_EXECUTION.md` |

---

## What FR-CS4 is supposed to do (intended behavior)

1. **Push 1:** Moonshot publishes a judge-eligible finding with anchored `start_line` / `end_line`.
2. **Pass 1a** (`patch_touches_line_region` in `github_resolution_metrics.py:32–64`): push-2 diff does **not** overlap anchored lines → group stays `resolution_status=still_open` (not `addressed`).
3. **Push 2:** Developer structurally fixes the defect elsewhere in the same file (no file deletion — that’s Track A hygiene).
4. Original finding fingerprint is **absent** from push-2 review run (`gen=0` for cohort fingerprint).
5. **Pass 3** (`verify_still_open_escalation_groups` in `github_finding_closure.py:268+`) runs verification judge on the aged `still_open` group.
6. Judge returns **`dismissed`** → `apply_resolution_method_on_verification_dismiss` (`github_finding_closure_rules.py:63–76`) sets `state=resolved`, `resolution_method=verification_dismissed`.
7. Publish shows finding closed; `github_finding_judge_outcomes` has `judge_purpose=verification`.

**Not acceptable closures for this experiment:** `absent_and_addressed` (Pass 2), `judge_dismissed` (discovery only), `human_dismissed`, hygiene path removal.

---

## What actually happened on staging (PR #72)

### Push 1 — PASS (after 7 probe iterations)

Cohort locked at rev 7 (`ff89066`):

| Field | Value |
|-------|-------|
| `group_id` | `019fb461-00d4-75f5-b27e-d9a0a1b77536` |
| `fingerprint` | `27c16742932165d08ca72896bbdf7d37bc09ae93d0d1bd08e0aa752362f29b48` |
| `review_run_id` | `019fb45c-e935-7f71-a3ba-4d246633af18` |
| `last_seen_revision_id` | `019fb45c-c4a7-7ac8-b118-2abf049c82ea` |
| Lines | 16–16 (`subprocess.call(..., shell=True)`) |
| `severity` / `category` | `critical` / `security` |
| Discovery judge | `completed`, upheld |

Probe: `backend/app/services/fr_cs4_staging_probe.py` — defect in `_fr_cs4_review_visible_defect`; push 2 removes invocation via `fr_cs4_probe_composed()` only.

### Push 2 — partial mechanical success, sign-off FAIL

Commit `203239d` / rev 8:

| Check | Result |
|-------|--------|
| Diff did not touch lines 16–16 | **PASS** |
| Cohort fingerprint `27c16742…` absent from rev-8 run (`gen=0`) | **PASS** |
| Cohort `state=resolved` | **FAIL** — `019fb461` → `superseded` |
| `resolution_method=verification_dismissed` | **FAIL** — count 0 |
| `judge_purpose=verification` outcome | **FAIL** — only discovery on rev 7–8 |
| Publish `still_open_count` | **FAIL** — 1 |

**Rev-8 side effects:**

- New group `019fb6c9-fa81-73e6-a671-6da94c3c5628` (fingerprint `de13b1e5…`) — Moonshot re-flagged the **dead** `subprocess` body still present in file (uncalled after push 2).
- Cohort `019fb461` → `state=superseded`, `resolution_status=still_open` (never resolved).

---

## Primary product problem (the one to fix)

**Pass 3 never got a chance to run on the FR-CS4 cohort**, not because the judge LLM is broken, but because **reconcile supersedes the cohort before Pass 3 executes**.

### Pipeline order (`reconcile_tasks.py:47–73`)

```text
1. reconcile_review_run              ← links new findings, may supersede peers
2. apply_pass2_closure_for_review_run
3. record_review_run_judge_status    ← discovery judge
4. verify_still_open_escalation_groups  ← Pass 3 verification
```

### Supersede logic (`github_finding_reconcile.py:73–98`)

When reconcile creates or reactivates a group with a **new fingerprint** on the same `(pull_request_id, file_path, category)`, `_mark_superseded_peers` sets all other **active** peers on that file+category to `state=superseded` if `last_seen_revision_id != current revision`.

On rev 8:

1. Moonshot emitted new finding → new fingerprint `de13b1e5…` → new group `019fb6c9`.
2. Reconcile step 1 superseded cohort `019fb461` (`27c16742…`).
3. Pass 3 step 4 queried candidates with `state == active` (`verification_escalation_candidate_sql_filters` / `is_verification_escalation_candidate` — `github_finding_closure.py:75–110`).
4. Superseded cohort **excluded**.
5. New group `019fb6c9` has fingerprint **in** `fingerprints_in_run` → **also excluded** (`pass3_verification_escalation_select` lines 133–134 + post-load filter 337).

**Result:** zero Pass 3 candidates → zero verification outcomes → FR-CS4 path never exercised end-to-end despite D0 widen.

### Why this is a real product gap, not probe sloppiness alone

The D1 probe violated the anti-pattern “don’t leave re-reportable dead code on push 2” (D1 findings § Probe design). But the **same failure mode applies to real PRs**:

> Developer fixes a security bug structurally (removes call site, leaves dead vulnerable code in file for later cleanup). Moonshot files a *new* finding on the dead code. Reconcile supersedes the original `still_open` group **before** Pass 3 can verify-dismiss the original finding as adequately addressed.

`gen=0` on the **original fingerprint is necessary but not sufficient** when same-file/same-category re-report triggers supersede.

| Solved (D0) | Not solved (D1 exposed) |
|-------------|-------------------------|
| Pairing-window wall — groups outside `pairing_revision_ids` can reach Pass 3 | Supersede-before-Pass-3 race |
| | Fingerprint-in-run exclusion on the *replacement* finding blocking closure of the *original* cohort |

---

## Secondary observations (do not confuse with “judge broken”)

### Discovery judge — working on #72

- Revs 1–6: `judge_status=not_applicable` (no judge-eligible publishable findings — probe tuning documented in staging memo).
- Rev 7–8: `judge_status=completed`, discovery outcomes recorded.
- Pre-flight: `judge_llm_enabled: True` on staging worker.

### Verification judge — implemented, rarely exercised on staging

- Since D0 deploy (`2026-07-30T08:28:45Z`): **0** verification outcomes on staging.
- All-time staging: **2** verification outcomes, both **`upheld`** — **`verification_dismissed` has never been observed in production staging data**.
- Unit test for happy path: `test_verify_still_open_escalation_outside_pairing` in `test_github_finding_closure.py:587+` — does **not** model reconcile supersede.

### Discovery judge reliability (separate ops concern)

`judge_json_contract_staging_metrics --since 2026-07-30T08:28:45Z`: many runs with `judge_escalation_candidate_count > 0` but zero outcomes (`all_failed`) and `skipped_unavailable` counts. Investigate separately; **not** the FR-CS4 rev-8 failure mechanism.

---

## Probe design constraint (D1-O13)

Current probe (`fr_cs4_staging_probe.py`):

- Push 2 removes **invocation** but leaves `_fr_cs4_review_visible_defect` body intact (required: cannot edit anchored hunk per Pass 1a experiment).
- Moonshot still sees `subprocess.call(..., shell=True)` on line 16 → new finding.

**Probe-only retry options** (if re-running dogfood before product fix):

- Defect class that becomes non-reportable when uncalled (hard — security patterns often re-flag dead code).
- Move anchored lines to code removed on push 2 outside line region without leaving re-reportable residue.
- Accept that probe cannot validate FR-CS4 until product fix lands.

---

## Design space for fix (product)

### A. Pipeline ordering

Run Pass 3 **before** reconcile supersede, or snapshot `still_open` escalation candidates at start of reconcile and judge them even if later superseded.

**Risk:** judging groups that reconcile will immediately supersede; need clear resolution semantics (resolve original before supersede? transfer closure to successor?).

### B. Supersede semantics vs FR-CS4

When new fingerprint supersedes old group on same file+category:

- Should Pass 3 still run on the **superseded** group if `gen=0` on its fingerprint and fix was structural?
- Should supersede **inherit** `still_open` escalation state from predecessor?
- Should verification dismiss on predecessor **prevent** supersede or auto-resolve successor as duplicate?

See parking lot **FR-CS8** (re-orphan after supersede) — related but distinct.

### C. Fingerprint-in-run filter intent

`fingerprints_in_run` exclusion (`github_finding_closure.py:133–134`) prevents judging groups **re-reported in current run**. Correct for exact re-report; **blocks** judging original cohort when a *different* fingerprint on same issue appears.

May need: exclude only when **same fingerprint** reappears, not when any finding exists in file.

### D. Pass 1a vs Pass 3 boundary

`patch_touches_line_region` is intentionally strict (PW-Q4 locked). FR-CS4 closure must stay on Pass 3 — do not loosen Pass 1a as a workaround.

---

## Verification queries / tooling

```bash
cd backend && DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics --since 2026-07-30T08:28:45Z --json
```

`PRODUCTION_DATABASE_URL` in `backend/.env` → staging DB.

Useful tables: `github_finding_groups`, `github_findings`, `github_finding_judge_outcomes`, `github_review_runs`, `github_pull_request_revisions` (filter PR #72 shas).

---

## Key code map

| Concern | File |
|---------|------|
| Reconcile pipeline order | `backend/app/workers/reconcile_tasks.py` |
| Supersede peers | `backend/app/services/github_finding_reconcile.py:73–98`, call sites `:154–203` |
| Pass 3 selection + judge | `backend/app/services/github_finding_closure.py:75–140`, `:268–449` |
| Verification dismiss fields | `backend/app/services/github_finding_closure_rules.py:63–76` |
| Pass 1a line region | `backend/app/services/github_resolution_metrics.py:32–64`, `:130–132` |
| Discovery judge | `backend/app/services/github_finding_judge.py` |
| Verification prompt | `backend/app/services/anthropic_review.py` (search `VERIFICATION_JUDGE`) |
| Fingerprint computation | `github_finding_reconcile.py` — `compute_fingerprint` |
| D1 probe fixture | `backend/app/services/fr_cs4_staging_probe.py` |
| D1 unit test | `backend/tests/unit/test_fr_cs4_probe.py` |
| Pass 3 E2E unit test (no supersede) | `backend/tests/unit/test_github_finding_closure.py:587+` |
| Reconcile task tests | `backend/tests/unit/test_reconcile_tasks.py` |

---

## Success criteria (re-run D1 or close FR-CS4 in D3)

From `FINDING_RESOLUTION_POST_WAVE_C_D1_FINDINGS.md` § Pass criteria — all required:

1. Push-2 diff does not overlap push-1 anchored lines.
2. Cohort fingerprint `gen=0` on push-2 run.
3. Cohort `state=resolved` after push-2 publish.
4. `resolution_method=verification_dismissed` (not discovery dismiss, not Pass 2).
5. `github_finding_judge_outcomes` row with `judge_purpose=verification` on push-2 `review_run_id`.
6. Staging memo sign-off → D3 closes FR-CS4 in gap registry.

**Current status:** criteria 1–2 pass; 3–6 fail.

---

## Recommended work order

1. **Decide product fix** for supersede-before-Pass-3 (A/B/C above) — core blocker for structural fixes.
2. **Add unit/integration test** that models: push-1 group `still_open` + push-2 new fingerprint same file → Pass 3 must still close original (or document intentional new semantics).
3. **Either** re-design probe for D1-O13 **or** ship product fix first then re-run dogfood on #72 or successor PR.
4. **D3 doc sync** — FR-CS4 status in backlog + execution table (`FINDING_RESOLUTION_POST_WAVE_C_EXECUTION.md` still shows D1 in progress).
5. **Optional:** investigate discovery `all_failed` / `skipped_unavailable` metrics — separate reliability track.

**Do not** mark FR-CS4 PASS on `gen=0` alone. **Do not** conflate discovery judge health with Pass 3 eligibility. **Do not** loosen Pass 1a line-region guard.
