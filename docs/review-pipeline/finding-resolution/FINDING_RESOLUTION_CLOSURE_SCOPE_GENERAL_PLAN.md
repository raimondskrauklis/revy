# Finding resolution — closure scope general plan (wave C)

**Baseline:** [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) (rev 3)  
**Date:** 2026-07-29  
**Status:** Decisions locked — ready for C1 execution after C0 sign-off.

**Thesis:** **Track A (HEAD hygiene)** closes stale groups when a finding’s `file_path` no longer exists at `revision.head_sha`, via Pass 1b stamp + **widened Pass 2**, while **Track B (FR-Q12 pairing metrics)** stays on Pass 1a only. **Track C (judge)** unchanged in wave C.

**North star:** PSA #63 / #67 — code or path gone on HEAD → group `absent_and_addressed` + thread collapsed — on **any** push, regardless of `last_seen_revision_id`.

**Read first:** Findings doc sections [Architecture: three tracks](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md#architecture-three-tracks-not-five-passes) and [Why compare windows fail](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md#why-compare-window-signals-are-not-enough).

---

## Why this plan exists (context for future you)

1. **#66** fixed deletion stamping **inside the pairing cohort** — correct for “deleted this push” on groups last seen on the prior revision.
2. **#67 VAL10** proved aged groups (`last_seen` = rev 1) stay **active** after file delete on rev 3 — Pass 1 **and** Pass 2 exclude them.
3. **Peer review** caught that wave C v1 (“Pass 1b only, Pass 2 out of scope”) would still **never close** aged groups.
4. **pr-comments skill** validated the durable pattern: **re-check HEAD**, not diff anchors or push windows.
5. **CS-Q7 refinement:** full-PR `base→head` compare still misses **add-then-delete** (#67 probe). Locked signal: **path absent at `head_sha`** via Contents API 404 (or tree batch).

**Reliable > perfect:** wave C ships deterministic file-deletion hygiene. Line-region false negatives (FR-CS4) are a separate problem — do not block FR-DG2 on them.

---

## Locked decisions (rev 3 — do not re-litigate in C1)

| Q# | Decision | Rationale |
|----|----------|-----------|
| **CS-Q3** | **Two Pass 1 tracks:** 1a = pairing cohort (FR-Q12 metrics); 1b = hygiene on **all active** groups whose path is gone on HEAD. | Separates “what transitioned this pair” from “is finding still valid” |
| **CS-Q7** | Hygiene primary signal = **path absent at `revision.head_sha`** (`fetch_repository_file_at_ref` 404). Compare `deleted_paths` = fast path only, not sole source. | Catches add-then-delete; idempotent on HEAD; matches pr-comments / Bugbot bar |
| **CS-Q8** | Hygiene applies to **`deleted_paths` only** — not `renamed_from_paths` / `previous_filename`. | R1 — rename must not mass-close old path |
| **CS-Q9** | **Pass 2 query must widen** — candidates = pairing cohort **OR** `resolution_status == addressed` from hygiene this run. Rules at `github_finding_closure_rules.py:17` **unchanged**. | Without this, Pass 1b stamp is a no-op for aged groups |
| **CS-Q4** | Reuse `resolution_method=absent_and_addressed`; no new method v1. | FR-Q3 two-step preserved |
| **CS-Q6** | Exclude hygiene path-removed closures from `resolution_rate_pct`; show **visible** G9 line. | Rate lie + silent `pr_active_count` drop both unacceptable |
| **CS-Q5** | Merge #67 **evidence-only**; does not block C1 coding. | Breaks circular “depends on #67 merged” |
| **CS-Q10** | Track A hygiene ships before FR-CS4 / Pass 3 widen. | FR-DG2 scope = file removal, not perfect fix detection |
| **CS-OPS** | Dogfood: backend-only pushes; per-group DB evidence; E2E test mandatory. | VAL8 |

---

## Phases

### C0 — Lock + sign-off

**Goal:** Treat findings rev 3 + this plan as execution baseline. Optional: merge #67 evidence to `main`.

**Deliverables:**

- Team sign-off on CS-Q7 (HEAD path-absent, not compare-only).
- Short FR-Q12 amendment note: hygiene closures excluded from transition rate (doc).
- Gap registry: FR-CS1/6/7 → `planned`.

**Gate:** No C1 PR until CS-Q7/8/9 acknowledged in PR description.

---

### C1 — Track A hygiene pipeline (code)

**Goal:** End-to-end closure for aged + adjacent delete scenarios (#67 VAL10, #66 regression).

#### C1.1 — Compare-first restructure

**Problem:** `apply_resolution_status_for_synchronize` returns at `:228–230` when pairing cohort is empty, **before** fetching compare. Aged-only actives never reach hygiene.

**Change:** Fetch compare (and/or HEAD path checks) **first**. Run Pass 1a on pairing cohort; run Pass 1b on **all PR active groups** independently of cohort size.

#### C1.2 — HEAD path-gone helper

**Add** (name illustrative): `path_absent_at_head(session, pull_request, revision, file_path) -> bool | None`

- `True` — Contents API 404 at `revision.head_sha` → path gone.
- `False` — file exists at HEAD.
- `None` — API error → fail closed (no hygiene stamp; set/compare blocked reason per R4).

**Batching:** v1 may check per unique `file_path` on active groups; optimize with tree API later if needed.

**Fast path:** if `file_path ∈ deleted_paths` from push-pair or full-PR compare (deletions only, CS-Q8), may skip Contents call — but **add-then-delete** must still hit Signal 3.

#### C1.3 — Split `deleted_paths` vs `renamed_from_paths`

Extend `ComparePatchesResult` / `github_api.py` paths_to_remove split:

- `deleted_paths` — hygiene eligible.
- `renamed_from_paths` — **not** hygiene eligible (CS-Q8).

#### C1.4 — Pass 1b stamp

For each **active** group on PR where `path_absent_at_head` is `True`:

- Set `resolution_status = addressed` (same as line-region / deletion stamp today).
- Do **not** filter by `last_seen_revision_id`.

Pass 1a unchanged: pairing cohort + `patch_touches_line_region` + push-pair `deleted_paths`.

#### C1.5 — Pass 2 widen

In `apply_pass2_closure_for_review_run` (`github_finding_closure.py`):

- **Before:** `last_seen_revision_id.in_(pairing_revision_ids)` only.
- **After:** pairing cohort **OR** (`resolution_status == addressed` AND hygiene path-absent this sync).

`should_close_absent_and_addressed` still requires fingerprint absent + no compare block.

#### C1.6 — R2 mitigation (same-run close)

Hygiene stamp and Pass 2 close should run in the **same reconcile transaction** before publish can supersede. Document in PR; durable `path_removed_at_revision_id` column is **optional deferral**.

#### C1.7 — Tests (mandatory)

| Test | Why |
|------|-----|
| E2E: aged group, delete file | Proves 1b + Pass 2 widen — **the v1 plan gap** |
| Adjacent delete | #66 regression |
| Add-then-delete | Proves CS-Q7 Signal 3 (compare-only insufficient) |
| Rename | R1 — no hygiene stamp on `previous_filename` |
| Compare-first: empty pairing cohort, aged actives | Proves early-return fix |
| HEAD API failure | R4 — fail closed |

**Out of scope C1:** Pass 3 widen; Moonshot prompt; FR-CS4 line-region improvements.

**Deliverable:** PR `fix/fr-closure-scope-hygiene` (C1 only — manifest in C2, same release train).

---

### C2 — Manifest + G9 (ship with C1)

**Goal:** CS-Q6 — honest rate + visible accounting.

**Why required with C1:** Shipping hygiene without C2 causes rate skew (`_in_sync_stamp_cohort`) and silent active-count drops.

**In scope:**

1. Predicate: hygiene path-removed closures **excluded** from `resolution_rate_pct` numerator/denominator.
2. Manifest field: `hygiene_path_removed_count` (or equivalent).
3. `format_resolution_metrics_block` + G9 prose, e.g.  
   `- **Closed as path removed:** N (outside this push pair)`
4. Formatter unit tests.

**Gate:** C1 PR must include C2 — single merge, single deploy.

---

### C3 — Staging sign-off (dogfood Track C)

**Deploy boundary:** ISO timestamp after C1+C2 droplet deploy. Metrics `--since` = that ISO.

| Step | Action | Pass criterion |
|------|--------|----------------|
| **C3.0** | Delete-only push smoke | Moonshot + reconcile + publish complete |
| **C3.1** | New chore PR; backend probe (1 defect) | ≥1 active group |
| **C3.2** | Unrelated backend commit (optional) | Ages cohort |
| **C3.3** | Delete probe file | Aged + adjacent groups `absent_and_addressed`; inline collapse |
| **C3.4** | Rename probe file | Old-path groups **stay open** (R1) |

**Deliverables:** Track C rows in [FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md); FR-DG2 → **closed PASS**.

---

### C4 — Program doc sync

Close FR-CS1, FR-CS6, FR-CS7 on C3 PASS; update parent README gap tables; FR-DG2 closed.

---

## Dependencies

```text
C0 (lock rev 3) → C1 + C2 (one PR) → deploy → C3 (staging) → C4 (docs)
```

```mermaid
flowchart LR
  C0[C0 lock] --> C1[C1 hygiene + Pass 2]
  C1 --> C2[C2 manifest G9]
  C2 --> DEP[deploy]
  DEP --> C3[C3 staging]
  C3 --> C4[C4 doc sync]
```

---

## PR strategy

| PR | Branch | Content |
|----|--------|---------|
| `fix/fr-closure-scope-hygiene` | feature | C1 + C2 |
| `chore/fr-dg2-track-c-staging` | chore | C3 dogfood only |
| #67 | `chore/fr-dg2-staging-dogfood` | Evidence + findings rev 3 — merge evidence-only |

**Do not** fold hygiene fix into #67 — evidence PR vs product fix.

---

## Success criteria

| Check | Target |
|-------|--------|
| E2E unit: aged group | `apply_resolution_status_for_synchronize` → Pass 2 → `absent_and_addressed` |
| Unit: add-then-delete | Path absent at HEAD closes without base→head compare removal |
| Staging C3.3 | `019faf58`-class orphan closes |
| FR-Q12 rate | Hygiene excluded; G9 path-removed line visible |
| Rename C3.4 | No PR-wide closure on old path |
| FR-Q13 | Re-add + same fingerprint re-opens |

---

## Evolution log (why the plan changed)

| Version | Gap | Fix |
|---------|-----|-----|
| **v1** | Pass 1b only; Pass 2 out of scope | Would not close aged groups |
| **v2** | Peer review: Pass 2 widen, compare-first, full-PR CS-Q7 | Still missed add-then-delete |
| **v3** | pr-comments / HEAD truth | **CS-Q7 = path absent at `head_sha`**; three-track architecture; verbose context |

---

## References

- [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) (rev 3)
- [FINDING_RESOLUTION_GENERAL_PLAN.md](./FINDING_RESOLUTION_GENERAL_PLAN.md) — FR-Q3, FR-Q12, FR-Q13
- [#67 evidence](https://github.com/raimondskrauklis/revy/pull/67) · [#66 deletion stamp](https://github.com/raimondskrauklis/revy/pull/66)
- [pr-comments skill](https://github.com/WhatIfWeDigDeeper/agent-skills/blob/9853a067e4a8149d8bdb592024fbfa522948db5d/skills/pr-comments/SKILL.md) — HEAD re-read pattern
