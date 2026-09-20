# docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_P0_EXECUTION.md

# P0 — Persistent identity (cutover) (execution)

Phase **P0** of [`RESOLUTION_HONESTY_GENERAL_PLAN.md`](./RESOLUTION_HONESTY_GENERAL_PLAN.md). Baseline: [`RESOLUTION_HONESTY_FINDINGS.md`](./RESOLUTION_HONESTY_FINDINGS.md) RH-Q4, RH-Q8, RH-Q11. **P0 only.**

**Goal:** One group per claim when title, severity, or line changes. This phase **is** the D10 cutover.

## Decisions locked for P0

- Unique key = `pull_request_id` + `file_path` + `category` + `claim_slot`. **`start_line` is not in the key.** Keep `uq_github_finding_groups_pr_fingerprint` on the stored hash of that key.
- `claim_slot` = first 32 hex chars of `sha256(title.strip())` at **birth**. Never update on later title rewrites. Title/severity/`start_line` are attributes.
- New `compute_fingerprint` payload: `workspace_id`, `pull_request_id`, `file_path`, `category`, `claim_slot`. Drop title and `start_line`.
- Bind order: (1) new fingerprint, (2) one-generation **old D10** hash from this finding’s title+`start_line` (P0.2), (3) continuation iff **exactly one** candidate (P0.3).
- Continuation candidate set: active groups, same `file_path` + `category`, not already bound this run. **Nearby = same `file_path`** (no numeric line window).
- Candidate count ≠ 1 → do not merge. Do **not** H2-close here (P1).
- Retire `_mark_superseded_peers` (no callers).
- Do **not** rewrite historical `fingerprint` values in Alembic (collision risk). Dual lookup covers one generation of old D10 hashes. Backfill `claim_slot` + `start_line` from the latest finding per group.
- **P0.4 option a (RH-Q11):** `github_inline_threads` keys = `str(group.id)`. **One id space** in this subphase: inline map, `publishable`, `collapsed`, `generation`, and `ever_inlined` are all `group.id` (not fingerprint). Dual-read 64-hex keys on load only. Do **not** mix UUID `ever_inlined` with fingerprint `publishable` (same hide-all-rows bug).
- Hand-written Alembic only. Head is `2026_09_19_1800_0034_github_installation_verified_at`. New revision `0035`.

## PR review context (required when code + docs ship in one PR)

- **SSOT (Moonshot inject):** `.revy/review-context.json` — `active_program: "resolution-honesty"`; `programs[]` = **one entry only**; `scope`: `["backend/**", "frontend/**"]`; three doc paths below.
- **Bugbot:** `.cursor/BUGBOT.md` — active program resolution-honesty + same three docs.
- **Agent mirror:** copy SSOT to `.agent/review-context.json`.
- **Do not** wire Greptile as a reviewer.

**Doc paths (SSOT `paths[]` only):**

- `docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_P0_EXECUTION.md`
- `docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_FINDINGS.md`
- `docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_GENERAL_PLAN.md`

## Out of scope for P0 (later phases)

- Pass 2 predicate / close without `addressed` / H2 skip when this-run findings count ≥ 1 → **P1**
- This-push N/A copy → **P2**
- Lifetime rollup raised math → **P3**
- GH-Q9 / comment scan table → **P4**
- Dogfood PR + doc-sync → **P5**
- Remap of dogfood #1’s 13 superseded rows

---

## P0.0 — Program PR review context (SSOT + Bugbot)

**What:** Switch SSOT to `resolution-honesty`; one program entry; `scope` `backend/**` and `frontend/**` (P5 changelog); update Bugbot; copy the same JSON to `.agent/review-context.json`.

**Files:** `.revy/review-context.json`, `.agent/review-context.json`, `.cursor/BUGBOT.md`

**Deliverable:**

```bash
python -m json.tool ../.revy/review-context.json > /dev/null
pipenv run pytest tests/unit/test_engineering_context_manifest.py -q
```

---

## P0.1 — Alembic `0035` group `start_line` + `claim_slot`

**What:** Hand-written revision `backend/alembic/versions/2026_09_19_2200_0035_finding_group_claim_slot.py` — `down_revision = "2026_09_19_1800_0034_github_installation_verified_at"`. Add nullable `start_line` Integer and `claim_slot` String(64) on `github_finding_groups`. Backfill both from the latest `github_findings` row per `group_id` (`created_at DESC`). Do **not** change existing `fingerprint` values. Update `GitHubFindingGroupORM`. Migration docstring = table/change label only (no phase tags).

**Files:** `backend/alembic/versions/2026_09_19_2200_0035_finding_group_claim_slot.py` (new), `backend/app/models/github_finding_group.py`

**Deliverable:** revision applies cleanly; ORM has `start_line` and `claim_slot`; unique constraint still `uq_github_finding_groups_pr_fingerprint`.

```bash
cd backend && pipenv run ruff check app/models/github_finding_group.py
```

**LOOP pause:** stop after this subphase for human migration review before P0.2.

---

## P0.2 — Fingerprint + retire peer supersede

**What:** Add `claim_slot_key(title)`. Rewrite `compute_fingerprint` to take `claim_slot` (no title, no `start_line`). Keep `compute_legacy_d10_fingerprint(...)`. Delete `_mark_superseded_peers` and every call in `reconcile_review_run`. Bind this subphase as new fingerprint **or** legacy D10 (continuation is P0.3). New groups set `claim_slot` at insert and copy `start_line` onto the group. Update every `compute_fingerprint(` call site (`github_finding_closure.py` `_fingerprints_in_review_run` included). Update `test_compute_fingerprint_*` and `test_reconcile_existing_group_supersedes_peers` in the same subphase. **Do not** change `should_close_absent_and_addressed` (P1). P0.2 pytest on `test_github_finding_closure.py` is signature-only for `compute_fingerprint(claim_slot=)`.

**Files:** `backend/app/services/github_finding_reconcile.py`, `backend/app/services/github_finding_closure.py`, `backend/tests/unit/test_github_finding_reconcile.py`

**Deliverable:** fingerprint ignores title and `start_line`; two titles at the same path+category+line produce two fingerprints (`claim_slot`). No `_mark_superseded_peers` symbol.

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_reconcile.py tests/unit/test_github_finding_closure.py -q
```

---

## P0.3 — Bind order + continuation

**What:** In `reconcile_review_run`, bind each finding: new fingerprint → legacy D10 fingerprint → continuation if the candidate set has **exactly one** group. Continuation updates group `start_line`, title, severity, `last_seen_revision_id`; `claim_slot` stays. Two in-run findings at the same path+category+line stay two groups. Candidate count ≠ 1 → birth a new group (do not merge, do not close).

**Files:** `backend/app/services/github_finding_reconcile.py`, `backend/tests/unit/test_github_finding_reconcile.py`

**Deliverable:** INFO→CRITICAL rewrite with one leftover in the file stays one **open** group; line insert above `eval` stays one group; two leftover same-category claims in one file are not merged.

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_reconcile.py -q
```

---

## P0.4 — Inline thread keys → `group.id` (all consumers)

**What:** Key `github_inline_threads` by `str(group.id)`. Dual-read 64-hex fingerprint keys on load; re-key to `group.id`; no duplicate entries. **Same subphase, one `group.id` space** for map + the four filter sets:

- `serialize_inline_thread_map` / loaders / `_fingerprints_to_resolve_inline_threads` (`group.id in inline_threads`, not `group.fingerprint`)
- `_close_active_groups_for_fingerprints` loads by `id`
- `InlinePostSpec` stores `str(group.id)` (rename field to `group_id` if it is still `group_fingerprint`)
- `_publishable_fingerprints_for_run` and `_load_prior_collapsed_inline_fingerprints` emit `group.id`
- `filter_pr_active_groups_for_summary` / `display_still_open_prior_count` compare `group.id` to `collapsed`, `publishable`, `generation`, `ever_inlined`
- rollup orphan / `ever_inlined` filter (`github_pr_resolution_rollup.py`)
- `_fingerprints_from_publish_summary` (`github_resolution_metrics.py`) treats map keys as group ids

Do **not** change GH-Q9 outdated comment-id union (P4). Do **not** ship UUID writes while any of those sets still uses fingerprint.

**Files:** `backend/app/services/github_publish.py`, `backend/app/services/github_publish_formatter.py`, `backend/app/services/github_pr_resolution_rollup.py`, `backend/app/services/github_resolution_metrics.py`, `backend/tests/unit/test_github_publish.py`, `backend/tests/unit/test_github_publish_formatter.py`, `backend/tests/unit/test_github_pr_resolution_rollup.py`, `backend/tests/unit/test_github_resolution_metrics.py`

**Deliverable:** round-trip map uses UUID keys; fingerprint-keyed prior map does not duplicate; a still-open group with an inline remains **displayable**. `filter_pr_active_groups_for_summary` with UUID `ever_inlined` + UUID `publishable`/`collapsed`/`generation` does not hide every active row. `_close_active_groups_for_fingerprints` tests still pass.

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py tests/unit/test_github_publish_formatter.py tests/unit/test_github_pr_resolution_rollup.py tests/unit/test_github_resolution_metrics.py -q
```

---

## P0.5 — Reconcile unit tests (identity gates)

**What:** Continuation + collision + dual-lookup tests not already in P0.2/P0.3: line insert above `eval` stays one group; two leftover same-category claims are not merged; legacy D10 dual lookup binds one generation; `_mark_superseded_peers` symbol is gone.

**Files:** `backend/tests/unit/test_github_finding_reconcile.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_reconcile.py tests/unit/test_engineering_context_manifest.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_reconcile.py tests/unit/test_github_publish.py tests/unit/test_github_publish_formatter.py tests/unit/test_github_pr_resolution_rollup.py tests/unit/test_github_resolution_metrics.py tests/unit/test_github_finding_closure.py tests/unit/test_engineering_context_manifest.py -q
pipenv run ruff check app/models/github_finding_group.py app/services/github_finding_reconcile.py app/services/github_publish.py app/services/github_publish_formatter.py app/services/github_pr_resolution_rollup.py app/services/github_resolution_metrics.py app/services/github_finding_closure.py
```

**Deploy:** apply `0035` before workers run the new fingerprint. Dual lookup keeps old D10 rows bindable until they match.

**Next:** [`RESOLUTION_HONESTY_P1_EXECUTION.md`](./RESOLUTION_HONESTY_P1_EXECUTION.md)
