# GitHub surface hardening P0 — Foundations (execution)

Phase **P0** of [GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md](./GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md). Baseline: [GITHUB_SURFACE_HARDENING_FINDINGS.md](./GITHUB_SURFACE_HARDENING_FINDINGS.md) §2, §8. **P0 only.**

**Goal:** Thread-map v2 migrate-on-read; Greptile/Bugbot wired to this program.

## Decisions locked for P0

- Thread map v2 entry: `{ "comment_id": int, "thread_id"?: str }` per fingerprint.
- Legacy `dict[str, int]` migrates on read in `_load_inline_thread_map` / write helpers.
- No resolve behavior changes — **P1**.
- First LOOP commit includes `.greptile/files.json` + `.cursor/BUGBOT.md`.

## PR review context (first commit)

- **Greptile:** `.greptile/files.json` — hardening execution index, findings, general plan; `scope: ["backend/**"]`
- **Bugbot:** `.cursor/BUGBOT.md` — links to same docs; branch `feat/github-surface-hardening`

## Out of scope for P0

- Option A resolve (GH-1) → **P1**
- GraphQL pagination → **P2**
- PRODUCT_PATTERNS flip → **P1** (GH-1) / **P4** (final sync)

---

## P0.1 — Program PR review context

**What:** Replace post-review-quality paths in `.greptile/files.json` and `.cursor/BUGBOT.md` with `github-surface-hardening/` docs; keep `REVIEW_QUALITY_EXECUTION.md` + agent workflow refs for engine contract.

**Files:** `.greptile/files.json`, `.cursor/BUGBOT.md`

**Deliverable:**

```bash
python -m json.tool .greptile/files.json > /dev/null
```

---

## P0.2 — Thread map v2 helpers

**What:** Add `normalize_inline_thread_map` / `merge_inline_thread_entry` (or equivalent) in `github_publish.py`: read legacy `int` values and v2 dicts; write v2 on new inline posts (comment_id only until P2 adds thread_id).

**Files:** `backend/app/services/github_publish.py`

**Deliverable:** `_load_inline_thread_map` returns `dict[str, int]` comment ids via normalized read (unchanged caller contract until P2).

---

## P0.3 — Thread map unit tests

**What:** Tests: legacy `{ "fp": 100 }` reads as comment_id 100; v2 `{ "fp": { "comment_id": 200, "thread_id": "PRRT_x" } }` reads comment_id 200; newest job still wins per fingerprint.

**Files:** `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "inline_thread_map" -q
```

---

## P0.4 — Dogfood template

**What:** Ensure [GITHUB_SURFACE_HARDENING_DOGFOOD.md](./GITHUB_SURFACE_HARDENING_DOGFOOD.md) exists with row template (done in execution index pass if missing).

**Files:** `docs/review-pipeline/github-surface-hardening/GITHUB_SURFACE_HARDENING_DOGFOOD.md`

**Deliverable:** File present; README execution table links it.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_github_publish.py -k "inline_thread_map or test_load_inline_thread_map" -q
```

**Human gate:** none.

**Next:** [GITHUB_SURFACE_HARDENING_P1_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P1_EXECUTION.md)
