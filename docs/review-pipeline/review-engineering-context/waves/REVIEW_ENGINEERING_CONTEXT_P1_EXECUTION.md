# Review engineering context P1 — Loader + extractor (execution)

Phase **P1** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: RCX-G3, G3b, RCX-D12 (extract only). **P1 only.**

**Goal:** Fetch SSOT + pointed `.md` at `head_sha`; extract bounded locks and operator smoke.

## Decisions locked for P1

- `fetch_repository_file_at_sha(client, owner, repo, path, ref)` in `github_api.py` — GitHub Contents API `GET /repos/{owner}/{repo}/contents/{path}?ref={sha}`; base64 decode; map 404 → `NotFoundError`; reuse rate-limit handling from `compare_commits`.
- Loader: `load_manifest_at_sha(...)` reads `.greptile/review-context.json` at revision `head_sha`.
- Scope: include program when any `changed_files` path matches any glob in `program.scope` (fnmatch).
- Extractor: section heading match `^## Locked decisions` (optional trailing ` (...)` ); table rows `| **ID** |` or `| ID |`; smoke: `## P0 smoke` or `### P0 smoke matrix` sections; byte cap from `settings.revy_engineering_context_max_bytes`.
- Fixtures: copy snippets from `JUDGE_JSON_CONTRACT_FINDINGS.md`, `REVIEW_ENGINEERING_CONTEXT_FINDINGS.md`, and `waves/REVIEW_ENGINEERING_CONTEXT_P0_EXECUTION.md` into `backend/tests/fixtures/engineering_context/`.
- `EngineeringContextPack`: `active_program`, `lock_ids: list[str]`, `extracted_text: str`, `source_paths: list[str]`, `errors: list[str]`.

## Out of scope for P1

- Prompt inject → **P2**
- Greptile generation → **P3**
- Judge → **P4**

---

## P1.1 — `fetch_repository_file_at_sha`

**What:** Implement Contents API fetch; unit tests with mocked httpx response (200 base64, 404).

**Files:** `backend/app/integrations/github_api.py`, `backend/tests/unit/test_github_api.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_api.py -k "fetch_repository_file" -q
```

---

## P1.2 — Manifest loader at SHA

**What:** `load_review_context_manifest_at_sha(session/client, installation, owner, repo, head_sha)` → `ReviewContextManifest`; errors append to trace-safe list.

**Files:** `backend/app/services/engineering_context/loader.py`, `backend/tests/unit/test_engineering_context_loader.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_engineering_context_loader.py -q
```

---

## P1.3 — Scope filter

**What:** `filter_programs_for_changed_files(manifest, changed_files)` → active program entry + paths list; empty when no scope match.

**Files:** `backend/app/services/engineering_context/scope.py`, `backend/tests/unit/test_engineering_context_scope.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_engineering_context_scope.py -q
```

---

## P1.4 — Lock/smoke extractor

**What:** `extract_engineering_context(md_text, *, max_bytes)` — tolerant headings; truncate UTF-8 safely.

**Files:** `backend/app/services/engineering_context/extract.py`, `backend/tests/fixtures/engineering_context/*.md`, `backend/tests/unit/test_engineering_context_extract.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_engineering_context_extract.py -q
```

---

## P1.5 — `build_engineering_context_pack`

**What:** Orchestrate loader + scope + parallel fetches for program paths + extract merge → `EngineeringContextPack`.

**Files:** `backend/app/services/engineering_context/pack.py`, `backend/tests/unit/test_engineering_context_pack.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_engineering_context_pack.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/integrations/github_api.py app/services/engineering_context/
pipenv run pytest tests/unit/test_github_api.py tests/unit/test_engineering_context_loader.py tests/unit/test_engineering_context_scope.py tests/unit/test_engineering_context_extract.py tests/unit/test_engineering_context_pack.py -q
```

**Next:** [REVIEW_ENGINEERING_CONTEXT_P2_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P2_EXECUTION.md)
