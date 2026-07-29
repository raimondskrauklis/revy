# Finding resolution — closure scope general plan (wave C)

**Baseline:** [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md)  
**Parent:** [FINDING_RESOLUTION_GENERAL_PLAN.md](./FINDING_RESOLUTION_GENERAL_PLAN.md) (P0–P5 shipped)  
**Dogfood:** [finding-resolution-dogfood](../finding-resolution-dogfood/README.md) waves A + B complete; FR-DG2 **partial PASS**.

**Thesis:** Split **metrics Pass 1** (pairing cohort, FR-Q12) from **hygiene Pass 1b** (all active groups on deleted `file_path`) so file removal closes stale groups across multi-push PRs without breaking transition-only rate math.

**North star:** PSA #63 class — **code/path gone → group resolved + thread collapsed** — on any push, not only when `last_seen == prior_revision`.

---

## Locked decisions (proposed — confirm before execution)

| Q# | Decision |
|----|----------|
| **CS-Q3** | **Two Pass 1 tracks:** (a) pairing cohort — line region + unchanged FR-Q12; (b) hygiene — `file_path ∈ removed_paths` → `addressed` for **all active groups** on path. |
| **CS-Q4** | Reuse `absent_and_addressed` on Pass 2; no new `resolution_method` v1. |
| **CS-Q6** | Hygiene closures on aged cohort: either (i) count in `transitions_addressed` **and** expand denominator rule for path-gone, or (ii) separate manifest field `hygiene_closed_count` excluded from rate — **prefer (ii)** for FR-Q12 purity. |
| **CS-OPS** | Staging dogfood: backend-only pushes; per-group DB evidence; no program-doc edits in repro pushes. |

---

## Phases (wave C)

### C0 — Decision + doc lock

**Goal:** Peer-review findings + this plan; lock CS-Q6 metrics split; update gap registry (FR-CS1 → planned).

**Deliverables:** Findings CS-Q* locked; amendment note on FR-Q12 if needed (doc only).

**Depends on:** Dogfood #67 evidence merged to `main`.

---

### C1 — Hygiene Pass 1b (code)

**Goal:** `apply_resolution_status_for_synchronize` stamps `addressed` on **all active groups** where `group.file_path ∈ compare_result.removed_paths`, after pairing-cohort Pass 1a.

**Scope in:** `github_resolution_metrics.py`; unit tests (aged cohort + adjacent); manifest field if CS-Q6 (ii).

**Scope out:** Pass 2 rule changes; Moonshot prompt.

**Deliverables:** PR `fix/fr-closure-scope-hygiene-pass1b`; pytest gate.

---

### C2 — Manifest / G9 alignment (if CS-Q6 ii)

**Goal:** Reconcile manifest exposes `hygiene_closed_count` (or similar) so G9 prose doesn’t imply false resolution rate spikes.

**Scope in:** `build_resolution_pass_manifest`, `format_resolution_metrics_block`, formatter tests.

**Deliverables:** Manifest schema documented in findings; no user-facing rate lie.

---

### C3 — Staging sign-off (dogfood Track C)

**Goal:** Close FR-DG2 + FR-CS1 on staging.

**Protocol:**

| Push | Action | Pass |
|------|--------|------|
| C3.1 | New chore PR; introduce minimal backend probe (1 defect) | ≥1 active group |
| C3.2 | Unrelated backend commit (optional — ages cohort) | publish completes |
| C3.3 | Delete probe file | target + aged groups `absent_and_addressed`; inline collapse |

**Deploy boundary:** post-C1 merge droplet ISO.

**Deliverables:** [FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) Track C rows; FR-DG2 → **closed PASS**.

---

### C4 — Program doc sync

**Goal:** Parent + dogfood README; close FR-CS*; SV-Q7 chore PR merge policy.

**Out of scope:** MR-DG1 (wave B dogfood).

---

## Dependencies

```text
C0 (lock) → C1 (code) → deploy → C3 (staging)
                ↘ C2 (manifest) — parallel if CS-Q6 ii
C3 PASS → C4 (docs)
```

---

## PR strategy

| PR | Content |
|----|---------|
| `fix/fr-closure-scope-hygiene-pass1b` | C1 (+ C2 if needed) |
| `chore/fr-dg2-track-c-staging` | C3 dogfood only |
| Docs on `main` | C0 + C4 |

**Do not** fold hygiene fix into open #67 — #67 is evidence PR; wave C is product fix + clean repro.

---

## Success criteria

| Check | Target |
|-------|--------|
| Unit: aged group on deleted path | `addressed` → Pass 2 → `absent_and_addressed` |
| Staging C3.3 | Push-1 cohort closes after delete on rev ≥3 |
| FR-Q12 rate | No false 100% from hygiene-only rows |
| FR-Q13 | Re-report same fingerprint re-opens |

---

## References

- [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md)
- [#67 dogfood evidence](https://github.com/raimondskrauklis/revy/pull/67)
- [#66 deletion stamp](https://github.com/raimondskrauklis/revy/pull/66)
