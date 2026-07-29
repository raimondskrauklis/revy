# Finding resolution — closure scope general plan (wave C)

**Baseline:** [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) (rev 2)  
**Peer review:** 2026-07-29 — Pass 2 widen + compare-first + CS-Q7 incorporated.

**Thesis:** **HEAD-truth hygiene** (path gone on PR) closes stale groups across multi-push PRs via Pass 1b stamp + **widened Pass 2** query, while **FR-Q12 pairing metrics** stay on Pass 1a only.

**North star:** PSA #63 class — code/path gone on HEAD → group resolved + thread collapsed.

---

## Locked decisions (rev 2)

| Q# | Decision |
|----|----------|
| **CS-Q3** | Pass 1a = pairing cohort (metrics). Pass 1b = hygiene path-gone on **all active groups** on affected `file_path`. |
| **CS-Q7** | Hygiene path-gone keyed to **full-PR compare** (`base_sha → head_sha`), not push-delta only. |
| **CS-Q8** | Hygiene stamp applies to **`deleted_paths` only** — not rename `previous_filename`. |
| **CS-Q9** | **Pass 2 must widen** — candidates include pairing cohort **OR** `resolution_status == addressed` from hygiene; `should_close_absent_and_addressed` unchanged. |
| **CS-Q4** | Reuse `absent_and_addressed`; no new `resolution_method` v1. |
| **CS-Q6** | Exclude hygiene closures from `resolution_rate_pct`; **visible** G9 line (`Closed as path removed: N`). |
| **CS-Q5** | Merge #67 **evidence-only** now; does not block C1 implementation. |
| **CS-OPS** | Backend-only dogfood pushes; E2E tests mandatory. |

---

## Phases

### C0 — Lock decisions + peer-review sign-off

**Goal:** Lock CS-Q6, CS-Q7, CS-Q8, CS-Q9; merge #67 evidence to `main` (optional, non-blocking for C1 coding).

**Deliverables:** Findings rev 2; FR-Q12 hygiene exclusion note (doc).

---

### C1 — Hygiene pipeline (code) — **not Pass 1 only**

**Goal:** End-to-end aged cohort closure.

**In scope:**

| Change | Detail |
|--------|--------|
| Compare-first | `apply_resolution_status_for_synchronize`: fetch compare before cohort check; never early-return before 1b |
| `deleted_paths` split | Extend `ComparePatchesResult` — `deleted_paths` vs `renamed_from_paths` |
| Pass 1a | Unchanged grain — pairing cohort, line region |
| Pass 1b | All **active** groups with `file_path ∈ head_gone_paths` → `addressed` |
| Pass 2 widen | `github_finding_closure.py` query — pairing cohort **OR** hygiene-addressed actives |
| HEAD compare helper | Reuse/compare pattern from `fetch_compare_review_context` for path-gone set |
| Tests | **E2E:** `apply_resolution_status_for_synchronize` → `apply_pass2_closure_for_review_run` on aged group |

**Out of scope:** Pass 3 widen (note FR-CS4); Moonshot prompt.

**R2 mitigation:** Evaluate durable `path_removed_at_revision_id` vs close-before-supersede in same worker — decision in C1 design note.

**Deliverables:** PR `fix/fr-closure-scope-hygiene` (Pass 1b + Pass 2 + compare split).

---

### C2 — Manifest + G9 (required with C1)

**Goal:** CS-Q6 — exclude hygiene from rate **and** show on surface.

**In scope:**

- Predicate excluding hygiene-aged closures from `resolution_rate_pct` math.
- `hygiene_path_removed_count` (or similar) on reconcile manifest.
- `format_resolution_metrics_block` + G9 line: path-removed count outside push pair.
- Formatter unit tests.

**Not sufficient:** manifest field alone without exclusion predicate + visible prose.

---

### C3 — Staging sign-off

| Step | Action |
|------|--------|
| **C3.0** | Smoke: delete-only push publishes (Moonshot + reconcile complete) |
| **C3.1** | Introduce backend probe |
| **C3.2** | Unrelated commit (age cohort) |
| **C3.3** | Delete probe — aged + adjacent groups close; inline collapse |
| **C3.4** | Rename scenario — no mass closure (R1) |

**Deploy boundary:** post-C1+C2 droplet ISO.

---

### C4 — Doc sync

Close FR-CS1/FR-CS6/FR-CS7 on PASS; FR-DG2 → closed PASS.

---

## Dependencies

```text
C0 (lock) → C1 (hygiene Pass 1b + Pass 2 widen) + C2 (manifest/G9) → deploy → C3 → C4
```

C1 and C2 ship in **one PR** — shipping C1 without C2 risks silent metric lie.

---

## Success criteria

| Check | Target |
|-------|--------|
| E2E unit: aged group | sync + Pass 2 → `absent_and_addressed` |
| Staging C3.3 | `019faf58`-class orphan closes |
| FR-Q12 rate | Hygiene excluded; visible path-removed line |
| Rename R1 | No PR-wide closure on rename old path |
| FR-Q13 | Re-report re-opens |

---

## What changed from wave C v1

| v1 gap | v2 fix |
|--------|--------|
| Pass 2 out of scope | **CS-Q9** — Pass 2 widen in C1 |
| Early return before compare | Compare-first restructure |
| Push-delta `removed_paths` only | **CS-Q7** — full-PR HEAD path-gone |
| CS-Q6 optional field | Exclusion predicate + **visible G9** |
| Unit tests on resolver only | **E2E** sync → Pass 2 |
| #67 merge circular | CS-Q5 evidence-only |

---

## References

- [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md)
- [#67](https://github.com/raimondskrauklis/revy/pull/67) · [#66](https://github.com/raimondskrauklis/revy/pull/66)
