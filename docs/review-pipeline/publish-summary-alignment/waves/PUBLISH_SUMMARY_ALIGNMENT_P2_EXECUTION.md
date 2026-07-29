# Publish summary alignment P2 — Staging validation + doc sync (execution)

Phase **P2** of [PUBLISH_SUMMARY_ALIGNMENT_GENERAL_PLAN.md](../PUBLISH_SUMMARY_ALIGNMENT_GENERAL_PLAN.md). **P2 only — final phase.**

**Goal:** Operator sign-off; RG-14 / FR-Q16 closed in corpus; parallel staging tracks noted.

## Decisions locked for P2

- Validation memo: [PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md](../PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md).
- RCX + judge-json validations continue independently — note pass/fail in memo § Parallel tracks.
- No `changelog.json` (backend-only).
- Close RG-14 gap row in generation-lifecycle; FR-Q16 → **addressed**.
- README index already lists PSA — P2.3 is **status + cross-link** updates, not new folder entry.

## Out of scope for P2

- Production sign-off
- `compute_check_conclusion` alignment (PSA-D12)

---

## P2.1 — Staging dogfood (multi-push PR)

**What:** Deploy PSA branch; run dogfood steps in validation memo (3-push scenario).

**Files:** manual — staging + GitHub PR

**Deliverable (non-gate):** Results table in validation memo.

---

## P2.2 — Inline vs summary vs check conclusion sanity

**What:** On dogfood PR, document in memo: (a) open **inline thread count** ≈ generation publishable, not block 2 rows; (b) check **conclusion** may be `success` while issue merge line warns — expected per PSA-D12.

**Files:** validation memo only

**Deliverable (non-gate):** Memo § inline + check conclusion note.

---

## P2.3 — Doc sync

**What:** Update:

| Doc | Change |
|-----|--------|
| `publish-summary-alignment/README.md` | Status Done + sha |
| `review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_FINDINGS.md` | RG-14 → **shipped**; §3c target state |
| `finding-resolution/FINDING_RESOLUTION_FINDINGS.md` | FR-Q16 → **addressed**; FR-Q7 note complete |
| `REVIEW_PIPELINE_PRODUCT_PATTERNS.md` | Issue comment two-block + PR-wide verdict row |
| `REVIEW_PIPELINE_RECOVERY_CHECKLIST.md` | Track L → shipped |
| `PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md` | Architecture peer review → incorporated |

**Files:** docs listed above

**Deliverable:**

| Check | Command / assertion |
|-------|---------------------|
| RG-14 shipped | `rg "RG-14.*shipped" docs/review-pipeline/review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_FINDINGS.md` |
| FR-Q16 addressed | `rg "FR-Q16.*addressed" docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_FINDINGS.md` |
| PRODUCT_PATTERNS row | `rg "two-block" docs/review-pipeline/REVIEW_PIPELINE_PRODUCT_PATTERNS.md` |
| README status | `rg "Done" docs/review-pipeline/publish-summary-alignment/README.md` |

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_publish_formatter.py -q
```

**Human gate:** Operator signs [PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md](../PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md). LOOP stops here even if unit tests pass.

**Deploy:** Ship with RCX/judge-json staging deploy window if convenient — not a hard coupling.

**Next:** none — program complete.
