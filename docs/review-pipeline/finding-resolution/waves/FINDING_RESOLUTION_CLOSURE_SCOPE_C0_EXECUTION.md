# docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_C0_EXECUTION.md

# C0 — Program lock + review context (execution)

Phase **C0** of [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md). Baseline: [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) rev 3. **C0 only.**

**Goal:** Wire wave C into LOOP tooling and execution index; no product code.

## Decisions locked for C0

- `active_program`: `finding-resolution-closure-scope`
- `programs[]`: **exactly one entry** (remove `finding-resolution-dogfood` on switch)
- Scope: `backend/**` + closure-scope doc paths
- Gap registry: FR-CS1/6/7 → `planned`; FR-CS3 → `planned` (closes on C2); FR-DG2 → `partial` until C3

## PR review context (first commit)

- **SSOT:** `.revy/review-context.json`
- **Greptile:** `cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --write`
- **Bugbot:** `.cursor/BUGBOT.md` — three doc links (execution index, findings, general plan)

## Out of scope for C0

- Hygiene code → **C1**
- Manifest/G9 → **C2**
- Staging pushes → **C3**

---

## C0.0 — Program PR review context

**What:** Set SSOT active program; regenerate Greptile; update Bugbot with wave C doc links.

**Files:** `.revy/review-context.json`, `.greptile/files.json`, `.cursor/BUGBOT.md`

**Deliverable:**

```bash
cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --check
cd backend && pipenv run pytest tests/unit/test_generate_greptile_files.py -q
```

---

## C0.1 — Execution index + README links

**What:** Ensure [FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md](./FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md) has C0–C4 table; link from [finding-resolution README](../README.md) and findings header.

**Files:** `docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md`, `docs/review-pipeline/finding-resolution/README.md`, `docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md`

**Deliverable:** README wave C row points to execution index.

---

## C0.2 — Gap registry status in execution index

**What:** Add **Gap status** table to execution index: FR-CS1/6/7/3 → `planned`; FR-DG2 → `partial PASS`; FR-CS4/8 → `defer`. Update findings gap registry status column to `planned` where applicable.

**Files:** `docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md`, `docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md` (gap table Status column only)

**Deliverable:** Execution index includes gap-status rows; grep `FR-CS1` shows `planned` in index.

---

## C0.3 — Verify FR-Q12 cross-ref (no new prose unless missing)

**What:** Confirm [FINDING_RESOLUTION_GENERAL_PLAN.md](../FINDING_RESOLUTION_GENERAL_PLAN.md) FR-Q12 row already cross-links CS-Q6 / closure-scope findings. **Do not duplicate** if present.

**Files:** none (verify only)

**Deliverable:** `grep -q "closure-scope findings" docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_GENERAL_PLAN.md`

---

**Phase gate** (from `backend/`):

```bash
pipenv run python -m scripts.generate_greptile_files_from_review_context --check
pipenv run pytest tests/unit/test_generate_greptile_files.py -q
grep -q "Gap status" docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md
```

**Deploy:** none.

**Next:** [`FINDING_RESOLUTION_CLOSURE_SCOPE_C1_EXECUTION.md`](./FINDING_RESOLUTION_CLOSURE_SCOPE_C1_EXECUTION.md)
