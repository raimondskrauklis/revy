# Review engineering context P3 — Greptile sync (execution)

Phase **P3** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: RCX-D9, D11, G4, G5. **P3 only.**

**Goal:** Generate `.greptile/files.json` from SSOT; replace legacy 15-entry file; CI validates generator output + SSOT paths.

## Decisions locked for P3

- P0 already ships rcx-only SSOT — **P3.1 is generator + `files.json` replace**, not re-trim SSOT (update SSOT paths only if program docs moved).
- Generator: `python -m scripts.generate_greptile_files_from_review_context` reads SSOT; writes Greptile `{"files": [{"path", "description", "scope"}]}`.
- **Generated `files.json` has exactly 3 entries** — the three RCX SSOT paths. **No** shared agent workflow refs in v1 (drop `CURSOR_AGENT_WORKFLOW`, `ROLES`, etc. from Greptile for this program).
- LOOP commit includes SSOT (if changed) + generated `files.json` — never hand-edit `files.json` after P3.
- Generator `--check` runs in pytest + phase gate; also calls `validate_review_context_paths_exist` on SSOT before emit.
- `pipenv run lint` is ruff-only — register generator check via **pytest** (`test_generate_greptile_files.py`) not Pipfile lint alone.

## Out of scope for P3

- `BUGBOT.md` generator
- Judge → **P4**

---

## P3.1 — Generator script

**What:** Implement generator with `--check` and `--write`; validate SSOT paths exist; map each SSOT path to one `files[]` row with program `scope`.

**Files:** `backend/scripts/generate_greptile_files_from_review_context.py`, `backend/tests/unit/test_generate_greptile_files.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_generate_greptile_files.py -q
```

---

## P3.2 — Regenerate and commit `files.json`

**What:** Run generator; replace `.greptile/files.json` (15 legacy entries → **3** RCX entries).

**Files:** `.greptile/files.json`

**Deliverable:**

```bash
python -m json.tool .greptile/files.json > /dev/null
pipenv run sh -c 'python -m scripts.generate_greptile_files_from_review_context --check'
```

---

## P3.3 — CI drift check in pytest

**What:** Test invokes generator `--check` against repo root; fails on drift vs committed `files.json`.

**Files:** `backend/tests/unit/test_generate_greptile_files.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_generate_greptile_files.py -k "check or drift" -q
```

---

## P3.4 — phase-execution skill note

**What:** One-line in `.cursor/skills/phase-execution/SKILL.md` — after SSOT edit, run `python -m scripts.generate_greptile_files_from_review_context` and commit both files.

**Files:** `.cursor/skills/phase-execution/SKILL.md`, `docs/review-pipeline/review-engineering-context/README.md` (status)

**Deliverable:**

```bash
grep -q "generate_greptile_files_from_review_context" .cursor/skills/phase-execution/SKILL.md
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check scripts/generate_greptile_files_from_review_context.py
pipenv run pytest tests/unit/test_generate_greptile_files.py tests/unit/test_engineering_context_validate.py -q
pipenv run sh -c 'python -m scripts.generate_greptile_files_from_review_context --check'
```

**Next:** [REVIEW_ENGINEERING_CONTEXT_P4_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P4_EXECUTION.md)
