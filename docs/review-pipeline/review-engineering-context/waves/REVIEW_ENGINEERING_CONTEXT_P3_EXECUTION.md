# Review engineering context P3 — Greptile sync (execution)

Phase **P3** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: RCX-D9, D11, G4, G5. **P3 only.**

**Goal:** SSOT trim to active program; generate `.greptile/files.json` from SSOT; CI validates paths.

## Decisions locked for P3

- SSOT `.greptile/review-context.json` lists **only** `review-engineering-context` program (remove shipped programs from SSOT — historical programs remain in git history, not active manifest).
- Generator: `backend/scripts/generate_greptile_files_from_review_context.py` (or `python -m scripts.generate_greptile_files_from_review_context`) reads SSOT, writes Greptile-shaped `{"files": [{"path", "description", "scope"}]}`.
- LOOP commit includes **both** SSOT update and generated `files.json` — never hand-edit `files.json` after P3.
- CI: `pytest` or small script invoked from existing lint — assert `files.json` matches generator output (fail if drift).
- Trim legacy 15-entry `files.json` down to RCX program paths (3 docs) + shared agent workflow refs if still needed for Greptile.

## Out of scope for P3

- `BUGBOT.md` generator
- Judge → **P4** (may ship in parallel after P2 on branch)

---

## P3.1 — Trim SSOT to active program

**What:** Update `.greptile/review-context.json` — `active_program: review-engineering-context`; single program block with execution, findings, general plan paths.

**Files:** `.greptile/review-context.json`, `docs/review-pipeline/review-engineering-context/README.md` (status row)

**Deliverable:**

```bash
python -m json.tool .greptile/review-context.json > /dev/null
cd backend && pipenv run pytest tests/unit/test_engineering_context_manifest.py -q
```

---

## P3.2 — Generator script

**What:** Implement generator; `--check` mode exits 1 on drift vs committed `files.json`.

**Files:** `backend/scripts/generate_greptile_files_from_review_context.py`, `backend/tests/unit/test_generate_greptile_files.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_generate_greptile_files.py -q
pipenv run sh -c 'python -m scripts.generate_greptile_files_from_review_context --check'
```

---

## P3.3 — Regenerate and commit `files.json`

**What:** Run generator; replace `.greptile/files.json` with output (≤4 entries for RCX + optional shared refs).

**Files:** `.greptile/files.json`

**Deliverable:**

```bash
python -m json.tool .greptile/files.json > /dev/null
pipenv run sh -c 'python -m scripts.generate_greptile_files_from_review_context --check'
```

---

## P3.4 — CI drift check + phase-execution note

**What:** Add generator `--check` to backend lint script or pytest marker; one-line note in `.cursor/skills/phase-execution/SKILL.md` — LOOP updates SSOT then runs generator.

**Files:** `backend/Pipfile` or `scripts/lint` hook, `.cursor/skills/phase-execution/SKILL.md`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_generate_greptile_files.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check scripts/generate_greptile_files_from_review_context.py
pipenv run pytest tests/unit/test_generate_greptile_files.py tests/unit/test_engineering_context_manifest.py -q
pipenv run sh -c 'python -m scripts.generate_greptile_files_from_review_context --check'
```

**Deploy:** confirm staging `REVY_DIFF_MAX_BYTES=524288` in env if not default from code.

**Next:** [REVIEW_ENGINEERING_CONTEXT_P4_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P4_EXECUTION.md)
