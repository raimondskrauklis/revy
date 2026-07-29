# Finding resolution dogfood — post-validation findings

**Date:** 2026-07-29  
**Purpose:** Baseline after PR [#65](https://github.com/raimondskrauklis/revy/pull/65) staging dogfood — **what passed, what failed, why, and how to fix it properly**. No execution steps.

**Evidence:** [staging memo](./FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) · [operator locks](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md) · staging DB `revy-staging` · code read on `main` + dogfood branch `a937df9`.

---

## Build principles

1. **Separate mechanism proof from sign-off metric** — `absent_and_addressed` working on one cohort does not sign off FR-DG2 if the probe-removal cohort failed.
2. **Verify Pass 1 before blaming Pass 2** — FR-Q3 closure requires `resolution_status=addressed` on the prior pairing revision; no stamp → no close.
3. **Dogfood PRs are noisy** — program docs + probe removal in one PR invalidates `pr_active_count` shrink as a sole metric.
4. **Fix shared infra** — file-deletion stamping belongs in `github_resolution_metrics.py` / compare helper, not a one-off dogfood workaround.

---

## Validation outcomes (verified)

| Gap | Staging result | Rev | Key evidence |
|-----|----------------|-----|--------------|
| **FR-DG1** | **PASS** | 3 `9d32ea2` | `denominator_active_prior=3`, `transitions_addressed=2`, `summary_json.resolution.addressed=2`, run `019faf31-0671-7069-9732-6e057a45e077` |
| **FR-DG2** | **PARTIAL** | 4 `66d64e5` | `pr_active` 3→7; `0` `absent_and_addressed` closures on rev 4; probe group still `active`; run `019faf36-7090-794c-ad6e-bdd77d5f20d2` |

**Mechanism partially proven:** two doc groups from rev 2 closed `resolved` + `absent_and_addressed` on rev 3 (`019faf30-f550-7b57-b300-0e4de850912d`) after Pass 1 stamped `addressed` on 2c doc edits.

**Sign-off failed:** rev 4 probe tree deletion did not close rev 2 `probe_module.py` group (`019faf29-9c6e`) and spawned five new active groups about the removal itself.

---

## What exists vs what dogfood exposed

| Layer | Shipped (wave A #64) | Verified in dogfood |
|-------|----------------------|---------------------|
| Prior-revision pairing | `get_last_published_prior_revision` + unpublished-gap cohort | Works — rev 3 denominator 3 |
| Pass 1 line-region stamp | `resolve_group_resolution_status` + `patch_touches_line_region` | Works for **modified** files (doc cohort) |
| Pass 1 on **deleted** file | **Not implemented** | Probe file deletion → `resolution_status` stays `still_open` / `None` |
| Pass 2 `absent_and_addressed` | `should_close_absent_and_addressed` in `github_finding_closure_rules.py:17` | Works when Pass 1 stamped `addressed` |
| G9 + `summary_json.resolution` | `resolution_metrics_manifest` path | FR-DG1 PASS |
| Inline collapse Option B | `github_publish.py:657` — collapse when `resolution_status=addressed` | Did not fire for probe — never stamped |
| Compare removed paths | `CompareCommitsResult.paths_to_remove` in `github_api.py:52` | **Exists but unused** by resolution Pass 1 |

---

## Root cause analysis

### RC-1 — Pass 1 ignores file deletion (primary code gap)

**Verified chain:**

1. `fetch_compare_patches` builds `patches_by_file` with `if item.patch` only (`github_compare_patches.py:80`) — deleted files typically have `patch=None`.
2. `resolve_group_resolution_status` returns `still_open` when `patches_by_file.get(file_path)` is `None` (`github_resolution_metrics.py:109-111`).
3. Pass 2 requires `resolution_status == addressed` (`github_finding_closure_rules.py:29`).
4. On rev 4, probe group `019faf29-9c6e` remained `active`, `resolution_status=None` after full file + test deletion.

**Conclusion:** FR-DG2 as originally scoped (remove flagged code → group closes) **cannot pass** for file-deletion fixes until Pass 1 treats GitHub compare `removed` status as `addressed`. This is the same class of bug as PSA #63 stale inline — heuristic only handles in-file line edits.

### RC-2 — Dogfood sequence conflated two cohorts

| Push | Intent | Cohort affected |
|------|--------|-----------------|
| 2b | Introduce findings | 3 groups (probe + 2 docs) |
| 2c | FR-DG1 fix | Doc groups stamped `addressed`; probe finding about 2a/2b plan **not** line-addressed |
| 3 | FR-DG2 remove probe | Deletion push — expects probe closure |

2c proved FR-DG1 on the **doc** cohort. Push 3 was meant to prove **probe removal** closure but probe never received `addressed` on 2c (different line region / finding semantics), then deletion hit RC-1.

### RC-3 — `pr_active_count` shrink is a weak sign-off metric on dogfood PRs

Rev 4: `pr_active_count` 3→7 while Moonshot reported new issues about probe removal, memo state, and README formatting. **Group-level** closure is the correct primary metric; aggregate `pr_active_count` mixes closure with new discovery.

### RC-4 — Push 2a wire produced zero findings (VAL6)

Test-fixture-only wire insufficient for Moonshot publishable finding — required push 2b PSA-class snippet. Protocol lesson: probe must be in a **review-visible** defect pattern, not only a unit-test import.

---

## Advice — improvement tracks (recommended order)

### Track A — File-deletion Pass 1 stamp (code, **required for FR-DG2 close**)

| Item | Detail |
|------|--------|
| **Change** | Thread `paths_to_remove` (or full `CompareFileChange` list) from compare into `apply_resolution_status_for_synchronize` |
| **Rule** | If `group.file_path` ∈ removed paths → `resolution_status=addressed` (same as line-region touch) |
| **Files** | `github_compare_patches.py`, `github_resolution_metrics.py`, tests in `test_github_resolution_metrics.py` |
| **Risk** | Renames: use `previous_filename` from compare when `status=renamed` |
| **Re-open** | FR-Q13 unchanged — re-report same fingerprint after `absent_and_addressed` still re-opens |

**Adopt** — fixes RC-1 at the shared layer; matches product intent (“code gone = addressed”).

### Track B — Focused FR-DG2 staging repro (process)

After Track A ships + deploy:

| Push | Action | Pass criteria |
|------|--------|---------------|
| 1 | Introduce minimal probe in **single non-doc file** (one fixable defect) | ≥1 active group |
| 2 | Fix defect in-file (line touch) | FR-DG1 manifest PASS |
| 3 | Delete probe file entirely | Group `absent_and_addressed`; `pr_active` stable or ↓ vs push 2 |

**Rules:** new chore PR; **no program doc edits** in pushes 1–3; one push per Revy cycle.

### Track C — Metrics / operator tooling (observability)

| Gap | Improvement |
|-----|-------------|
| Window aggregates mask per-rev | Add `--review-run-id` or `--head-sha` filter to `judge_json_contract_staging_metrics.py` |
| `pr_active_count` noise | Staging memo should record **per-group** `state` / `resolution_method` row, not only summary JSON |
| Inline map growth | Record `len(github_inline_threads)` per publish row (already in `summary_json`) |

**Adopt** Track C.1–C.2 for next dogfood; defer script flag until next validation wave.

### Track D — Reject / defer

| Option | Verdict | Why |
|--------|---------|-----|
| Pass 2 closes without Pass 1 `addressed` on file delete | **Reject** | Breaks FR-Q3 two-step model; hides compare failures |
| Mark FR-DG2 closed on partial doc cohort | **Reject** | Wrong gap — PSA #63 symptom was **code removal**, not doc edit |
| Merge #65 as FR-DG2 sign-off | **Reject** | Documented PARTIAL; merge for FR-DG1 + wave A cleanup only |

---

## Decisions registry

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| **DG-PV-Q1** | Is FR-DG1 staging-closed? | **locked** | **Yes** — rev 3 manifest + surface PASS |
| **DG-PV-Q2** | Is FR-DG2 staging-closed? | **locked** | **Partial PASS** — wave C required for product close |
| **DG-PV-Q7** | Next platform work? | **locked** | [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](../finding-resolution/FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md) wave C |
| **DG-PV-Q3** | Root cause of probe survival? | **locked** | RC-1 — deleted files not stamped `addressed` |
| **DG-PV-Q4** | Next code work? | **locked** | Track A shipped in `fix/fr-dg2-file-deletion-pass1` |
| **DG-PV-Q5** | Merge #65? | **open** | Safe for FR-DG1; not FR-DG2 sign-off |
| **DG-PV-Q6** | New gap ID for Track A? | **locked** | **FR-DG2a** — file-deletion Pass 1 stamp |

---

## Devil's advocate

| Challenge | Response |
|-----------|----------|
| “Doc `absent_and_addressed` proves FR-DG2” | Proves Pass 2 only; FR-DG2 symptom in PSA #63 was **removing code**, not editing docs |
| “Judge should dismiss probe meta findings” | Out of scope — does not fix stale **original** group |
| “Use `paths_to_index` instead” | Index paths exclude `removed` — must use `paths_to_remove` |
| “Close on absent fingerprint without addressed” | Re-opens PSA compare-failure / false-positive risk |

---

## Experiment / verification (Track A + B)

| Step | Pass | Fail |
|------|------|------|
| Unit: `resolve_group_resolution_status` when file ∈ `paths_to_remove` | returns `addressed` | `still_open` |
| Unit: Pass 2 closes group after delete push | `state=resolved`, `method=absent_and_addressed` | stays `active` |
| Staging push 3 on clean repro PR | probe group closes; inline thread collapses | same as #65 rev 4 |
| `pr_active_count` | stable or ↓ vs push 2 | irrelevant if group-level PASS |

---

## Parking lot

- **MR-DG1** — Moonshot `format_summary_comment` signature FP (wave B, unchanged).
- **P1.5 execution doc drift** — goal line still says “push 2b fix” for FR-DG1; update when P3.3 sync runs.
- **Probe cleanup on `main`** — #65 deletes fixture; merge or cherry-pick before next repro.

---

## References

| Area | Path |
|------|------|
| Pass 1 stamp | `backend/app/services/github_resolution_metrics.py` — `apply_resolution_status_for_synchronize`, `resolve_group_resolution_status` |
| Compare patches | `backend/app/services/github_compare_patches.py:80` |
| Removed paths | `backend/app/integrations/github_api.py:52` — `paths_to_remove` |
| Pass 2 close | `backend/app/services/github_finding_closure.py:132`, `github_finding_closure_rules.py:17` |
| Inline collapse B | `backend/app/services/github_publish.py:657` |
| FR-Q3 locked rule | `docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_GENERAL_PLAN.md` |
| PSA #63 incident | `docs/review-pipeline/finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_FINDINGS.md` § FR-DG2 |
