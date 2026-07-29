# docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_C0_EXECUTION.md

# C0 — Program lock + review context (execution)

Phase **C0** of [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md). Baseline: [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) rev 3. **C0 only.**

**Goal:** Wire wave C into LOOP tooling and execution index; no product code.

## Decisions locked for C0

- `active_program`: `finding-resolution-closure-scope`
- `programs[]`: **exactly one entry** (remove `finding-resolution-dogfood` on switch)
- Scope: `backend/**` + closure-scope doc paths
- Gap registry FR-CS1/6/7 → `planned` in execution index (not closed until C3)

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

## C0.1 — Execution index + general plan link

**What:** Ensure [FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md](./FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md) exists with C0–C4 table; link from [finding-resolution README](../README.md) and findings header.

**Files:** `docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md`, `docs/review-pipeline/finding-resolution/README.md`, `docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md` (execution link only if missing)

**Deliverable:** README wave C row points to execution index.

---

## C0.2 — FR-Q12 hygiene exclusion note

**What:** One-line cross-reference in [FINDING_RESOLUTION_GENERAL_PLAN.md](../FINDING_RESOLUTION_GENERAL_PLAN.md) FR-Q12 section: hygiene path-removed closures excluded from transition rate (CS-Q6) — detail in closure-scope findings.

**Files:** `docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_GENERAL_PLAN.md`

**Deliverable:** FR-Q12 mentions wave C exclusion; no open TBDs in C0.

---

**Phase gate** (from `backend/`):

```bash
pipenv run python -m scripts.generate_greptile_files_from_review_context --check
pipenv run pytest tests/unit/test_generate_greptile_files.py -q
```

**Deploy:** none.

**Next:** [`FINDING_RESOLUTION_CLOSURE_SCOPE_C1_EXECUTION.md`](./FINDING_RESOLUTION_CLOSURE_SCOPE_C1_EXECUTION.md)
