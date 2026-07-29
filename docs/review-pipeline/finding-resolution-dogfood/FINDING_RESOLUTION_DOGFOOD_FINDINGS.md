# Finding resolution dogfood — findings (post-PSA #63)

**Date:** 2026-07-29  
**Purpose:** Baseline for gaps **deferred** from [PSA #63](../publish-summary-alignment/PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md) dogfood. **No execution steps.**

**Trigger:** Push 3 on PR #63 expected G9 addressed prose, block-2 shrink, and inline thread collapse after a fix push — all **failed**. Push 4 confirmed two-block + `summary_json` parity but not resolution closure.

**Evidence:** PR [#63](https://github.com/raimondskrauklis/revy/pull/63) rev 5–8 staging runs; `github_publish_jobs.summary_json`; issue comment [#5117353181](https://github.com/raimondskrauklis/revy/pull/63#issuecomment-5117353181); [PSA validation memo](../publish-summary-alignment/PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md).

---

## Build principles

1. **Dogfood isolation** — resolution bugs are not PSA formatter bugs; validate on a fresh chore PR after #63 merges.
2. **Single-push cadence** — wait for publish to complete before the next commit (superseded rev → `0/0 prior active`).
3. **DB + GitHub** — pass criteria require `summary_json.resolution` **and** issue-comment G9 block **and** inline thread state.
4. **Minimal repro** — each gap gets a dedicated probe commit sequence (introduce → fix → optional re-introduce).

---

## Gap registry

| ID | Gap | Severity | Target PR | Status |
|----|-----|----------|-----------|--------|
| **FR-DG1** | G9 / resolution manifest `0/0 prior active` | high | `chore/finding-resolution-staging-dogfood` | **closed PASS** — rev 3 `9d32ea2` ([#65](https://github.com/raimondskrauklis/revy/pull/65)) |
| **FR-DG2** | Stale finding group survives code removal (block 2 + inline orphan) | high | follow-up after Track A | **partial** — doc cohort closed rev 3; probe deletion failed rev 4 — [post-validation](./FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md) |
| **FR-DG2a** | Pass 1 does not stamp `addressed` when `file_path` deleted in compare | high | `fix/fr-dg2-file-deletion-pass1` | **code ready** — Track A shipped; Track B staging repro pending |
| **MR-DG1** | Moonshot hallucinates `format_summary_comment` signature | medium | `chore/moonshot-formatter-signature` | open |

### Out of scope (this program)

| Item | Why excluded |
|------|----------------|
| RCX retrieve / inject changes | [review-engineering-context](../review-engineering-context/README.md) program |
| Judge JSON contract / parse failures | [judge-json-contract](../judge-json-contract/README.md) program |

---

## FR-DG1 — G9 / resolution `0/0 prior active`

### Symptom

On PR #63 push 3 (rev 6 `0e0e60a`), issue comment showed:

- `Since last push: n/a`
- `Resolution rate: 0.0% (0/0 prior active)`
- `Closed as fixed: 0`
- `summary_json.resolution`: all counts `0`

Fix push removed bogus `format_summary_comment` test call; no addressed transitions recorded.

### Likely cause

| Factor | Evidence |
|--------|----------|
| **Superseded revision** | Rev 5 (`61f8b5f`) `publish_status=skipped_not_head`; publish only on rev 6 (`0e0e60a`) which included an extra docs commit |
| **Pass 1 not paired** | `apply_resolution_status_for_synchronize` may not have stamped prior groups when the fix revision never published |
| **Denominator empty** | `build_resolution_pass_manifest` → `denominator_active_prior=0` → G9 block shows `n/a` |

### Code touchpoints

| Area | Path |
|------|------|
| Pass 1 stamp on synchronize | `backend/app/services/github_resolution_metrics.py` — `apply_resolution_status_for_synchronize` |
| Manifest for publish | `build_resolution_pass_manifest`, `get_resolution_metrics_for_review_run` |
| G9 prose gate | `backend/app/services/github_publish_formatter.py` — `build_g9_resolution_prose`, `format_resolution_metrics_block` |
| Head gate | `backend/app/services/github_publish.py` — `skipped_not_head` |

### Pass criteria (dogfood)

**Primary (manifest):** reconcile `resolution_pass` on publish trace — `denominator_active_prior` ≥ 1; `transitions_addressed` ≥ 1.

**Surface (after P1.3):** G9 `Since last push:` not `n/a`; `summary_json.resolution.addressed` ≥ 1 — both fed from `resolution_metrics_manifest`, not generation-scoped `ctx.groups` alone.

| Check | Expected |
|-------|----------|
| Fix push publishes (no supersede) | rev N publish `completed` |
| Pass 1 | prior active groups get `resolution_status=addressed` when diff touches region |
| Manifest | `denominator_active_prior` ≥ 1; `transitions_addressed` ≥ 1 |
| G9 prose | lists addressed count (not `n/a`) |
| `summary_json.resolution.addressed` | ≥ 1 (manifest-aligned) |

**Dogfood push:** push 2 on chore PR — **wire/fix probe only** (not remove file); after P1 merge + deploy.

---

## FR-DG2 — Stale fingerprint after code removal

### Symptom

Push 3 removed `test_format_summary_comment_emits_two_block_headings` (valid `generation_groups=` call). Block 2 on rev 8 still listed:

> error — Test calls `format_summary_comment` with unknown keyword argument `generation_groups`

Inline thread on `test_psa_staging_validation_behavior.py` had `line: null` (orphaned) but finding remained **active** in PR-wide table.

### Likely cause

| Factor | Evidence |
|--------|----------|
| **Group not closed** | Fingerprint persisted on `github_finding_groups` with `state=active` though source lines gone |
| **Moonshot re-report gap** | Absent fingerprint in new run did not trigger Pass 2 `absent_and_addressed` closure |
| **PR-wide block 2** | `verdict_groups` / `pr_active_groups` still include stale active group |

### Code touchpoints

| Area | Path |
|------|------|
| Pass 2 reconcile closure | `github_finding_reconcile.py`, resolution pass in reconcile task |
| PR-wide publish set | `verdict_groups`, `publishable_groups_for_review_run` |
| Thread collapse GH-1v2 | `github_publish.py` — `_resolve_stale_inline_threads`, `_fingerprints_to_resolve_inline_threads` |
| Option A / B | [GH-1v2 §4c](../github-surface-hardening/GITHUB_SURFACE_HARDENING_FINDINGS.md#gh-1v2--collapse-triggers-shipped-post-p4) |

### Pass criteria (dogfood)

| Check | Expected |
|-------|----------|
| Remove flagged code | generation no longer reports removed issue |
| Block 2 shrink | `pr_active_count` decreases vs prior rev |
| Inline collapse | thread `resolved` on GitHub or removed from open set |
| Group state | `resolved` + `resolution_method=absent_and_addressed` OR superseded |

**Dogfood push:** push 3 on chore PR — **remove probe code**; after P2 merge + deploy (not same push as FR-DG1).

**Staging result (2026-07-29):** **PARTIAL** on [#65](https://github.com/raimondskrauklis/revy/pull/65) rev 4 — RC-1 fixed in **FR-DG2a** (`fix/fr-dg2-file-deletion-pass1`); Track B staging repro pending.

**Staging result (2026-07-29):** **PARTIAL** on [#65](https://github.com/raimondskrauklis/revy/pull/65) rev 4 — doc cohort `absent_and_addressed` on rev 3; probe file deletion did not close group. Root cause: Pass 1 never stamps `addressed` for deleted files — see [post-validation findings](./FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md) RC-1 / Track A.

---

## MR-DG1 — Moonshot `format_summary_comment` signature hallucination

### Symptom

On PR #63 push 2 (rev 4 `d52e790`), Moonshot flagged:

> error — Test calls `format_summary_comment` with unknown keyword argument `generation_groups`

The call was **valid** — signature in `github_publish_formatter.py:328` uses `generation_groups` and `pr_active_groups`. Unit tests pass.

### Likely cause

Moonshot reviewer prompt does not include formatter API surface; model inferred wrong kwargs from partial context.

### Code touchpoints

| Area | Path |
|------|------|
| Reviewer prompt | `backend/app/integrations/moonshot_review.py` |
| Formatter signature (reference) | `backend/app/services/github_publish_formatter.py` — `format_summary_comment` |
| Existing parity tests | `backend/tests/unit/test_github_publish_formatter.py` |

### Pass criteria (dogfood)

| Check | Expected |
|-------|----------|
| Valid formatter test in diff | Moonshot does **not** flag `generation_groups` as unknown |
| Or judge dismiss | false positive dismissed before inline publish |

**Note:** Separate PR from FR-DG1/DG2 — prompt-only change, no resolution pipeline dependency.

---

## Incident timeline (PR #63)

| Rev | `head_sha` | Publish | `gen` / `pr` | Resolution notes |
|-----|------------|---------|--------------|------------------|
| 4 | `d52e790` | completed | 1 / 4 | Moonshot FP on `generation_groups` introduced |
| 5 | `61f8b5f` | **skipped_not_head** | — | Fix push superseded before publish |
| 6 | `0e0e60a` | completed | 3 / 7 | G9 `n/a`, `0/0 prior active` |
| 8 | `d84b83b` | completed | 2 / 8 | Stale FP still in block 2 |

---

## Dogfood plan (next PR)

**Branch:** `chore/finding-resolution-staging-dogfood`  
**Open after:** PR #63 merged + [P0](./waves/FINDING_RESOLUTION_DOGFOOD_P0_EXECUTION.md) ships.

| Push | When | Validates |
|------|------|-----------|
| 1 | P0.4 | probe introduced |
| 2 | P1.4 after **P1 merge + deploy** | FR-DG1 (wire probe) |
| 3 | P2.4 after **P2 merge + deploy** | FR-DG2 (remove probe) |
| 4 | P3.4 optional | block-1 regrowth |

See [execution index](./waves/FINDING_RESOLUTION_DOGFOOD_EXECUTION.md) for full LOOP.

---

## Related docs

| Doc | Link |
|-----|------|
| Finding resolution (shipped) | [FINDING_RESOLUTION_FINDINGS.md](../finding-resolution/FINDING_RESOLUTION_FINDINGS.md) |
| PSA validation (complete) | [PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md](../publish-summary-alignment/PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md) |
| Staging validation meta | [STAGING_VALIDATION_FINDINGS.md](../staging-validation/STAGING_VALIDATION_FINDINGS.md) |
| GitHub thread collapse | [GITHUB_SURFACE_HARDENING_FINDINGS.md](../github-surface-hardening/GITHUB_SURFACE_HARDENING_FINDINGS.md) |
