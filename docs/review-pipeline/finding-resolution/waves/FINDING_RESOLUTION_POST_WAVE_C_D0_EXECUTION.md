# docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_POST_WAVE_C_D0_EXECUTION.md

# D0 — FR-CS4 Pass 3 cohort widen (execution)

Phase **D0** of [FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md](../FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md). Baseline: [backlog findings](../FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md) § FR-CS4. **D0 only.**

**Goal:** `verify_still_open_escalation_groups` considers PR-wide `still_open` escalation candidates, not only `last_seen_revision_id ∈ pairing_revision_ids`.

## Decisions locked for D0

- **PW-Q4:** Pass 3 query widen only — **no** Pass 1a line-region change.
- Widen pattern: select all `active` groups on PR, filter with `is_verification_escalation_candidate` (still `still_open` + judge-eligible); remove pairing-only `last_seen` filter on candidate query (`github_finding_closure.py:249–256`).
- Cap unchanged: `VERIFICATION_JUDGE_MAX_PER_RUN` (5).
- **Branch:** separate from M0 — e.g. `fix/fr-cs4-pass3-widen`.

## PR review context (first commit)

- **SSOT:** `.revy/review-context.json` — `active_program: finding-resolution-post-wave-c`; one `programs[]` entry; scope `backend/**`; three doc paths (execution index, backlog findings, general plan).
- **Greptile:** `cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --write`
- **Bugbot:** `.cursor/BUGBOT.md` — wave D doc links

## Out of scope for D0

- Staging dogfood → **D1**
- FR-CS8 observability → **D2**
- Pass 1a / hygiene → shipped wave C

---

## D0.0 — Program PR review context

**What:** SSOT + Greptile + Bugbot for wave D product work. Update `test_parse_committed_ssot_file` for `active_program: finding-resolution-post-wave-c` and three doc paths (same commit as SSOT switch).

**Files:** `.revy/review-context.json`, `.greptile/files.json`, `.cursor/BUGBOT.md`, `backend/tests/unit/test_engineering_context_manifest.py`

**Deliverable:**

```bash
cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --check
pipenv run pytest tests/unit/test_generate_greptile_files.py tests/unit/test_engineering_context_manifest.py -q
```

---

## D0.1 — Pass 3 candidate query widen

**What:** Replace pairing-only candidate filter in `verify_still_open_escalation_groups` with PR-wide active groups before `is_verification_escalation_candidate` filter.

**Files:** `backend/app/services/github_finding_closure.py`

**Deliverable:** D0.2 test `test_verify_still_open_escalation_outside_pairing` (or equivalent) passes — aged `still_open` outside pairing window is judged when `judge_llm_enabled`.

---

## D0.2 — Unit tests (Pass 3 widen)

**What:** Add test mirroring Pass 2 template `test_apply_pass2_closure_e2e_aged_group_outside_pairing`: aged `still_open` group outside pairing window is eligible for Pass 3 when judge enabled; in-window behavior unchanged.

**Files:** `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py -q -k "verification or pass3 or escalation or outside_pairing"
```

---

## D0.3 — No Pass 1 regression

**What:** Confirm `patch_touches_line_region` / Pass 1 stamp logic in `github_resolution_metrics.py` unchanged in this phase.

**Files:** none (grep gate)

**Deliverable:**

```bash
cd backend && rg 'patch_touches_line_region' app/services/github_resolution_metrics.py app/services/github_finding_closure.py
# expect: definition + callers only in github_resolution_metrics.py — no new callers in github_finding_closure.py
pipenv run pytest tests/unit/test_github_resolution_metrics.py -q -k patch_touches
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/services/github_finding_closure.py
pipenv run pytest tests/unit/test_github_finding_closure.py tests/unit/test_github_resolution_metrics.py -q
```

**Deploy:** merge D0 to `main` + droplet deploy before **D1**.

**Next:** [`FINDING_RESOLUTION_POST_WAVE_C_D1_EXECUTION.md`](./FINDING_RESOLUTION_POST_WAVE_C_D1_EXECUTION.md)
