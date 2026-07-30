# docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_POST_WAVE_C_D3_EXECUTION.md

# D3 — Program doc sync (execution)

Phase **D3** of [FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md](../FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md). **D3 only — final phase.**

**Goal:** Execution index + gap registry + SSOT reflect shipped M0/D1/D2 outcomes; wave D program complete.

## Decisions locked for D3

- **Closed on D1 PASS:** FR-CS4
- **Closed on M0:** MR-DG1 (if not already in M0.3)
- **FR-CS8:** closed only if D2 shipped; else remains **monitor**
- Restore SSOT to `finding-resolution-dogfood` when wave D ends (unless new program active)

## Out of scope for D3

- New product code

---

## D3.1 — Gap registry + backlog findings

**What:** Update backlog findings gap table (FR-CS4, FR-CS8, MR-DG1 if not closed in M0.2); lock PW-Q4; closure-scope execution defer rows → closed where applicable.

**Files:** `FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md`, `waves/FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md`, `FINDING_RESOLUTION_DOGFOOD_FINDINGS.md` (MR-DG1 row if M0.2 missed)

**Deliverable:** FR-CS4 closed PASS (if D1 PASS); FR-CS8 status accurate.

---

## D3.2 — README + execution table

**What:** Mark M0–D3 Done + commit shas (include **D0 merge sha** for D1 deploy boundary); finding-resolution README post–wave C status; dogfood README next steps; flip gap table FR-CS4/FR-CS8 in LOOP index.

**Files:** `waves/FINDING_RESOLUTION_POST_WAVE_C_EXECUTION.md`, `finding-resolution/README.md`, `finding-resolution-dogfood/README.md`

**Deliverable:**

```bash
grep -q "closed PASS" docs/review-pipeline/finding-resolution-dogfood/README.md
grep -q "Done" docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_POST_WAVE_C_EXECUTION.md
```

---

## D3.3 — SSOT restore

**What:** Set `active_program` back to `finding-resolution-dogfood`; regenerate Greptile; update Bugbot; fix `test_engineering_context_manifest.py` if needed.

**Files:** `.revy/review-context.json`, `.greptile/files.json`, `.cursor/BUGBOT.md`, `backend/tests/unit/test_engineering_context_manifest.py`

**Deliverable:**

```bash
cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --check
pipenv run pytest tests/unit/test_generate_greptile_files.py tests/unit/test_engineering_context_manifest.py -q
```

---

**Phase gate** (doc consistency):

```bash
test -f docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md
test -f docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_POST_WAVE_C_EXECUTION.md
grep -q "closed PASS" docs/review-pipeline/finding-resolution-dogfood/README.md
grep -q "Done" docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_POST_WAVE_C_EXECUTION.md
cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --check
pipenv run pytest tests/unit/test_engineering_context_manifest.py -q
```

**Next:** none — post–wave C program complete. FR-CS8 durable column → parking lot.
