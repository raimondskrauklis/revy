# Judge input quality P2 — Evidence capture at review ingest (execution)

Phase **P2** of [JUDGE_INPUT_QUALITY_GENERAL_PLAN.md](../JUDGE_INPUT_QUALITY_GENERAL_PLAN.md). Baseline: [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](../JUDGE_INPUT_INVESTIGATION_FINDINGS.md) J-2, J-3, J-9, J-12. **P2 only.**

**Goal:** Raise `evidence_snippet` and `start_line` coverage on judge-eligible findings (staging baseline ~53%).

## Decisions locked for P2

- `EVIDENCE_CONTEXT_LINES` = **15** (was 5).
- `normalize_patch_file_key` used in `resolve_evidence_snippet` lookup (from P0).
- `normalize_start_line(raw)` — accept `int` or numeric `str`; `0` → `None`; invalid → `None`.
- Apply normalization in `_parse_finding_row` before persist (not a separate `_parse_review_finding` symbol).
- Compare failure / empty `patches_by_file` → evidence may remain NULL; supplemental fallback unchanged — no fake patch.
- Staging SQL appendix documents `missing_file_path` + `index_mode` breakdown — non-gate.

## Out of scope for P2

- Judge prompt / compare reload → **P3**
- PR body → **P4**

---

## P2.1 — `start_line` normalization (J-12)

**What:** Add `normalize_finding_start_line(raw: Any) -> int | None`; use in `_parse_finding_row`; unit tests for int, str, 0, garbage.

**Files:** `backend/app/services/github_review.py`, `backend/tests/unit/test_github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k start_line -q
```

---

## P2.2 — Path-normalized patch lookup (J-9)

**What:** `resolve_evidence_snippet` looks up patch via `normalize_patch_file_key`; if direct key fails, try normalized key against all `patches_by_file` keys.

**Files:** `backend/app/services/github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k "evidence_snippet or patch_key" -q
```

---

## P2.3 — Wider evidence window

**What:** Set `EVIDENCE_CONTEXT_LINES = 15`; test that snippet includes more context lines around anchor.

**Files:** `backend/app/services/github_review.py`, `backend/tests/unit/test_github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k evidence -q
```

---

## P2.4 — Ingest integration tests

**What:** Fixture: finding with line-less path but file patch present → non-null `evidence_snippet` (file patch fallback). Fixture: normalized path matches compare filename.

**Files:** `backend/tests/unit/test_github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k "evidence or finding_parse" -q
```

---

## P2.5 — Staging SQL checklist (non-gate)

**What:** Add “P2 validation queries” subsection to findings reproduce section: `missing_file_path`, optional join to index job for `index_mode` / compare fallback.

**Files:** `docs/review-pipeline/judge/JUDGE_INPUT_INVESTIGATION_FINDINGS.md`

**Deliverable:** SQL block present under reproduce section — manual staging run after deploy.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_review.py -q
pipenv run ruff check app/services/github_review.py
```

**Next:** [JUDGE_INPUT_QUALITY_P3_EXECUTION.md](./JUDGE_INPUT_QUALITY_P3_EXECUTION.md)
