# Review engineering context P1 — Loader + extractor (execution)

Phase **P1** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: RCX-G3, G3b, RCX-D12 (extract only). **P1 only.**

**Goal:** Fetch SSOT + pointed `.md` at `head_sha`; extract bounded locks and operator smoke.

## Decisions locked for P1

- `fetch_repository_file_at_sha(client, owner, repo, path, ref)` in `github_api.py` — GitHub Contents API `GET /repos/{owner}/{repo}/contents/{path}?ref={sha}`; base64 decode; map 404 → `NotFoundError`; reuse rate-limit handling from `compare_commits`.
- Loader: `load_manifest_at_sha(...)` reads `.greptile/review-context.json` at revision `head_sha`.
- **Scope (RCX-D11):** resolve `manifest.active_program` → single matching `programs[]` entry; then require `changed_files` ∩ `program.scope` non-empty (fnmatch). Never merge multiple programs.
- Extractor: section heading match `^## Locked decisions` (optional trailing ` (...)` ); table rows `| **ID** |` or `| ID |`; smoke: `## P0 smoke`, `### P0 smoke matrix`, `**Queried:**` validation tables, `### Baseline captured` — byte cap from `settings.revy_engineering_context_max_bytes`.
- Fixtures: snippets from `JUDGE_JSON_CONTRACT_FINDINGS.md` (§ P0 smoke matrix), `REVIEW_ENGINEERING_CONTEXT_FINDINGS.md` (§ Locked decisions + § Baseline captured), `JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md` (§ P0 smoke matrix).
- `EngineeringContextPack`: `active_program`, `lock_ids: list[str]`, `extracted_text: str`, `source_paths: list[str]`, `errors: list[str]`.

## Out of scope for P1

- Prompt inject → **P2**
- Greptile generation → **P3**
- Judge → **P4**
- Dedupe (RCX-D12) → **P2**

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

## P1.3 — Active program + scope filter

**What:** `resolve_active_program(manifest) -> ProgramEntry`; `program_applies_to_changed_files(program, changed_files) -> bool`; return empty pack when `active_program` id missing or scope mismatch.

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

**What:** Orchestrate loader + active program + path fetches + extract merge → `EngineeringContextPack`.

**Files:** `backend/app/services/engineering_context/pack.py`, `backend/tests/unit/test_engineering_context_pack.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_engineering_context_pack.py -q
```

---

## P1.7 — PR #60 review findings (cleanup)

**What:** Greptile + revybot findings on RCX P0–P1 — all fixed before P2:

| Fix | File |
|-----|------|
| Catch `binascii.Error` on Contents decode | `pack.py` |
| Path traversal guard on SSOT paths | `validate.py` |
| URL-encode Contents API path | `github_api.py` |
| Skip duplicate nested smoke sections | `extract.py` |
| Top-level `import json` | `manifest.py` |

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_engineering_context_validate.py tests/unit/test_engineering_context_extract.py tests/unit/test_engineering_context_pack.py tests/unit/test_github_api.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/integrations/github_api.py app/services/engineering_context/
pipenv run pytest tests/unit/test_github_api.py tests/unit/test_engineering_context_loader.py tests/unit/test_engineering_context_scope.py tests/unit/test_engineering_context_extract.py tests/unit/test_engineering_context_pack.py -q
```

**Next:** [REVIEW_ENGINEERING_CONTEXT_P2_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P2_EXECUTION.md)
