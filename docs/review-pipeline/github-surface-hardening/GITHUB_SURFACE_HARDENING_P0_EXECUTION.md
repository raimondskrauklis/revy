# GitHub surface hardening P0 — Foundations (execution)

Phase **P0** of [GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md](./GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md). Baseline: [GITHUB_SURFACE_HARDENING_FINDINGS.md](./GITHUB_SURFACE_HARDENING_FINDINGS.md) §2, §8. **P0 only.**

**Goal:** Thread-map v2 migrate-on-read; Greptile/Bugbot wired to this program.

## Decisions locked for P0

- Thread map v2 entry: `{ "comment_id": int, "thread_id"?: str }` per fingerprint.
- Legacy `dict[str, int]` migrates on read; **all writes** use `serialize_inline_thread_map` (v2 shape).
- Internal working type stays `dict[str, int]` (comment ids only) until P2 adds `thread_id`.
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

## P0.2 — Thread map v2 serialize / deserialize helpers

**What:** Add three helpers in `github_publish.py`:

- `deserialize_inline_thread_map(raw) -> dict[str, int]` — accept legacy `int` or v2 `{comment_id, thread_id?}`; return comment-id map for callers.
- `serialize_inline_thread_map(comment_map: dict[str, int], *, prior_v2?: dict) -> dict` — emit v2 `{ fingerprint: { "comment_id": int, "thread_id"?: str } }`; preserve existing `thread_id` when fingerprint unchanged.
- `_load_inline_thread_map(jobs)` — delegate to `deserialize_inline_thread_map` per job summary.

Wire **write** sites to `serialize_inline_thread_map` (not raw `dict[str, int]`):

- `run_publish_job` initial `job.summary_json` (~596–598)
- `run_publish_job` post-inline `job.summary_json` (~798–801)

**Files:** `backend/app/services/github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "serialize_inline_thread_map or deserialize_inline_thread_map" -q
```

---

## P0.3 — Thread map unit tests

**What:** Tests: legacy `{ "fp": 100 }` deserializes to comment_id 100; v2 `{ "fp": { "comment_id": 200, "thread_id": "PRRT_x" } }` deserializes to 200; serialize round-trip emits v2 dict (not legacy int); newest job still wins per fingerprint in `_load_inline_thread_map`.

**Files:** `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "inline_thread_map or serialize_inline_thread_map or deserialize_inline_thread_map or test_load_inline_thread_map" -q
```

---

## P0.4 — Dogfood template

**What:** Ensure [GITHUB_SURFACE_HARDENING_DOGFOOD.md](./GITHUB_SURFACE_HARDENING_DOGFOOD.md) exists with row template (verify-only — file shipped in execution index pass).

**Files:** `docs/review-pipeline/github-surface-hardening/GITHUB_SURFACE_HARDENING_DOGFOOD.md`

**Deliverable:** File present; README execution table links it.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_github_publish.py -k "inline_thread_map or serialize_inline_thread_map or deserialize_inline_thread_map or test_load_inline_thread_map" -q
```

**Human gate:** none.

**Next:** [GITHUB_SURFACE_HARDENING_P1_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P1_EXECUTION.md)
