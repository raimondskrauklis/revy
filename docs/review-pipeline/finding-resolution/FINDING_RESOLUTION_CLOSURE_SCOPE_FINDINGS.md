# Finding resolution — closure scope findings (platform)

**Date:** 2026-07-29 (rev 2 — peer-review corrections)  
**Purpose:** Platform baseline after dogfood waves A + B. **Why FR-DG2 is partial PASS and what to build next — no execution steps.**

**Evidence:** Staging DB; code on `main` `111e851`; [dogfood post-validation](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md).

---

## Build principles

1. **Hygiene ≠ metrics grain** — “Is this finding still valid on **HEAD**?” ≠ “What **transitioned** on pair N−1→N?” — **separable design choices**; do not use strict FR-Q12 rate math to justify window-scoped hygiene.
2. **No silent closure** — compare failure, rename side-effects, and ambiguous diff must stay explicit.
3. **End-to-end proof** — unit tests on `resolve_group_resolution_status` alone are insufficient; aged cohort must be driven through **sync → reconcile Pass 2 → publish**.
4. **Industry bar** — re-check on **HEAD** ([Bugbot](https://cursor.com/bugbot), Greptile addressed detection), not only push-pair delta.

---

## Platform promise (what users expect)

| User mental model | Revy contract (target) |
|-------------------|------------------------|
| I fixed the line you flagged | Group → **Addressed**; thread collapses on publish |
| I removed the file / feature | Group on that path → **Resolved** on HEAD; block 2 + inline shrink |
| I didn’t touch it | Stays **Still open** unless judge dismisses |
| Bot was wrong | **Dismissed**; stays dismissed until rebuttal |

**PSA #63 / FR-DG2:** code removed but group stayed **active** in block 2 — violates row 2.

---

## Verified root cause (code)

The cohort filter appears in **three** passes — not only Pass 1:

| Pass | File | Lines | Filter |
|------|------|-------|--------|
| Pass 1 stamp | `github_resolution_metrics.py` | 223–227 | `last_seen_revision_id ∈ pairing_revision_ids` |
| Pass 1 early exit | `github_resolution_metrics.py` | 228–230 | **returns before compare** if pairing cohort empty |
| Pass 2 close | `github_finding_closure.py` | 166–174 | same `last_seen_revision_id` filter |
| Pass 3 verify | `github_finding_closure.py` | 246–254 | same filter |

**#67 rev-3 orphan (`019faf58`):** `last_seen` = rev 1; pairing on rev 3 = rev 2 only → excluded from Pass 1 **and** Pass 2. Rev-2 group (`019faf5b`) closed `absent_and_addressed` — proves mechanism **within** pairing window only.

**Peer-review correction:** Wave C v1 scoped **Pass 1b only** and left Pass 2 out of scope — **that would not fix aged groups.** Hygiene requires **both** Pass 1b stamp **and** Pass 2 candidate widening (rules at `github_finding_closure_rules.py:17` unchanged).

---

## Gap registry

| ID | Gap | Severity | Status |
|----|-----|----------|--------|
| **FR-CS1** | Hygiene signals keyed to **push-pair** diff window only | **high** | open |
| **FR-CS6** | Pass 2 (and Pass 3) use same pairing cohort filter as Pass 1 | **high** | open — **blocker for C1** |
| **FR-CS3** | Hygiene closures skew `resolution_rate_pct` (numerator + denominator via `_in_sync_stamp_cohort` resolved branch) | **medium** | open |
| **FR-CS4** | Line-region `addressed` false negatives (structural fixes) | **medium** | open — same cohort wall for Pass 3 |
| **FR-CS7** | No **HEAD-truth** path-gone signal (`base_sha → head_sha`) | **high** | open — **CS-Q7** |
| **FR-CS8** | `resolution_status` reset every sync — hygiene stamp not durable if publish superseded | **medium** | open |
| **FR-CS5** | Dogfood doc churn invalidates metrics | **low** | locked — VAL8 |
| **FR-DG1** | Manifest / G9 | — | closed PASS |
| **FR-DG2a** | Deletion stamp in pairing cohort (#66) | — | closed PASS |
| **FR-DG2** | End-to-end file removal on PR | — | partial PASS |

*Removed FR-CS2 as separate child — it duplicates FR-CS1/FR-CS6.*

---

## Options (revised)

### Option A — Hygiene track: Pass 1b + Pass 2 widen (recommended baseline)

| Item | Detail |
|------|--------|
| **Pass 1 restructure** | Fetch compare **first**; run 1a (pairing cohort, FR-Q12) + 1b (all active groups on path-gone). |
| **Pass 2 widen** | Include active groups where `resolution_status == addressed` **OR** in pairing cohort; `should_close_absent_and_addressed` remains the guard. |
| **Path-gone source** | See **CS-Q7** — push-delta `removed_paths` vs full-PR compare. |
| **Renames** | **Deletions only** for Pass 1b — split `deleted_paths` vs `renamed_from_paths` (#66 `paths_to_remove` mixes both). |
| **Adopt** | Minimal rule change; fixes #67 aged shape when combined with Pass 2. |
| **Insufficient alone** | Without Pass 2 widen + compare-first restructure → **no-op** for aged groups. |

### Option A′ — HEAD-truth path-gone (recommended upgrade to A)

| Item | Detail |
|------|--------|
| **What** | Hygiene keyed to **full-PR compare** (`base_sha → head_sha`): path absent from HEAD tree → path-gone for all active groups on that `file_path`. |
| **Why** | Matches “re-check on HEAD”; idempotent; survives superseded intermediate publishes better than push-delta-only. |
| **Plumbing** | `fetch_compare_review_context` already loads full-PR compare for Moonshot. |
| **Adopt** | **CS-Q7 recommended default** — collapses FR-CS1 for most real shapes. |

### Option B — Pass 2 close without `addressed` stamp

**Reject** — breaks FR-Q3; hides compare failures.

### Option C / E — Expand all actives / brute outdated resolve

**Reject** — see v1 findings.

---

## Correctness risks (must address in wave C)

| ID | Risk | Mitigation |
|----|------|------------|
| **R1** | Rename adds `previous_filename` to `paths_to_remove` → PR-wide silent closure on old path | Pass 1b: **`deleted_paths` only**; renames handled separately |
| **R2** | `resolution_status = None` reset every sync (`:220–221`); stamp lost if publish superseded | Consider durable `path_removed_at_revision_id` or close in same pipeline run before supersede |
| **R3** | Pass 3 same cohort filter — FR-CS4 hits same wall | Document; defer or widen with hygiene |
| **R4** | Compare fail on hygiene path: groups reset, no `closure_blocked_reason` | Explicit hygiene compare-fail signal or inherit blocked reason |
| **R5** | `resolve_group_resolution_status` maps all `resolved` → `judge_dismissed` (`:102–103`) | Pre-existing; ticket for `count_resolution_status` accuracy |

---

## CS-Q6 / manifest (peer-review precision)

Today `_in_sync_stamp_cohort` (`:283–284`) already puts hygiene closures into **both** `transitions` and `denominator_groups` when `resolved_at_revision_id == current` — rate skews toward 100%, not “maybe counted.”

**Required (not optional field only):**

1. **Exclude** hygiene closures from `resolution_rate_pct` numerator/denominator via explicit predicate.
2. **Surface** them visibly: e.g. `Closed as path removed: N (outside this push pair)` in `format_resolution_metrics_block` / G9 — not silent shrink of `pr_active_count`.

---

## Decisions registry

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| **CS-Q1** | FR-DG2 product-closed after #67? | **locked** | **No** |
| **CS-Q2** | #66 sufficient? | **locked** | **No** — pairing scope |
| **CS-Q3** | Split Pass 1a vs 1b? | **locked** | **Yes** |
| **CS-Q4** | New `resolution_method`? | **locked** | **No** — reuse `absent_and_addressed` |
| **CS-Q5** | Merge #67? | **locked** | **Evidence-only merge** — unblocks C0; does not block C1 code |
| **CS-Q6** | Metrics vs hygiene on surface? | **proposed** | Exclude from rate + **visible G9 line** |
| **CS-Q7** | Push-delta vs full-PR path-gone? | **proposed** | **Full-PR HEAD-truth** (Option A′) |
| **CS-Q8** | Renames = path gone? | **proposed** | **No** — deletions only for hygiene stamp |
| **CS-Q9** | Pass 2 widen strategy? | **locked** | Widen query; rules unchanged |

---

## Verification (wave C — expanded)

| Scenario | Pass |
|----------|------|
| **E2E aged delete** | sync → Pass 2 → group `absent_and_addressed` (not isolated unit on `resolve_*`) |
| **Adjacent delete** | Rev1 introduce → Rev2 delete |
| **Aged delete** | Rev1 introduce → Rev2 unrelated → Rev3 delete |
| **Rename** | No mass closure on `previous_filename` (R1) |
| **Compare fail on delete push** | No silent orphan; blocked reason visible (R4) |
| **Superseded publish after stamp** | No re-orphan (R2) |
| **Delete-only push publishes** | Moonshot runs on delete-only diff (C3.0 smoke) |
| **Re-open FR-Q13** | Re-add file + same fingerprint |
| **Metrics** | Rate excludes hygiene; G9 shows path-removed line |

---

## Peer-review alignment (2026-07-29)

| Peer claim | Verdict |
|------------|---------|
| Diagnosis / Option A direction correct | **Agree** |
| C1 Pass-1-only would not fix aged groups | **Agree** — Pass 2 `:170` confirmed |
| Early return skips compare when cohort empty | **Agree** — `:228–230` |
| CS-Q6 needs exclusion predicate + visible surface | **Agree** — `_in_sync_stamp_cohort` already counts today |
| Full-PR path-gone (CS-Q7) | **Agree** — recommended upgrade |
| Rename silent closure (R1) | **Agree** — `paths_to_remove` includes renames |
| Ephemeral `resolution_status` (R2) | **Agree** |
| Pass 3 same filter (R3) | **Agree** — `:250` |
| FR-CS2 duplicate / need FR-CS6 | **Agree** |
| C3 delete-only publish untested | **Agree** — add C3.0 smoke |
| #67 merge circular dependency | **Fixed** — CS-Q5 evidence-only |

---

## References

| Area | Path |
|------|------|
| Pass 1 cohort + early exit | `github_resolution_metrics.py:223–237` |
| Pass 2 cohort | `github_finding_closure.py:166–174` |
| Pass 3 cohort | `github_finding_closure.py:246–254` |
| Manifest cohort | `github_resolution_metrics.py:274–288` |
| Rename in remove paths | `github_api.py:52–59` |
| Close rules | `github_finding_closure_rules.py:17` |
