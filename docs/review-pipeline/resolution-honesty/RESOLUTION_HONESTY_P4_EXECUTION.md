# docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_P4_EXECUTION.md

# P4 — Comment + GitHub threads (execution)

Phase **P4** of [`RESOLUTION_HONESTY_GENERAL_PLAN.md`](./RESOLUTION_HONESTY_GENERAL_PLAN.md). Baseline: [`RESOLUTION_HONESTY_FINDINGS.md`](./RESOLUTION_HONESTY_FINDINGS.md) RH-Q5, RH-Q6, RH-Q12. **P4 only.**

**Goal:** Author-facing comment and thread collapse agree with P1–P3. Keep GH-Q9 Outdated **UI** collapse. Numbers follow H2 only.

## Decisions locked for P4

- **Keep GH-Q9:** `_fingerprints_to_resolve_inline_threads` still unions `outdated_comment_ids`. Do not rip `github_publish.py` outdated resolve.
- Option A / identity collapse keys on **group.id** (P0.4 already switched formatter/rollup/metrics/`InlinePostSpec`). Collapse when the group is unbound/closed **or** the hunk is Outdated. Outdated is **not** H2 and does **not** set `state=resolved` by itself (`github_publish.py` `_close_active_groups_for_fingerprints` stays gated on the P1 predicate). Do **not** mix UUID maps with `group.fingerprint in inline_threads`.
- Scan + details: no `0% (0/0 prior active)` (P2 formatter). Lifetime details keep PSR-Q15 four-term copy when the identity holds.
- GitHub markdown stays English. No new reviewer UI strings in this phase.

## Out of scope for P4 (later phases)

- Dogfood PR / sign-off memo → **P5**
- New GitHub App settings
- Counting Outdated as lifetime resolved
- Changelog / sibling doc-sync → **P5**

---

## P4.1 — Keep Outdated thread collapse

**What:** Regression: given an inline map keyed by `group.id` and `outdated_comment_ids` containing that comment, the fingerprint/id is in the resolve set even if the group is still `active` (leftover line-shift). Assert `state` stays `active` unless P1 H2 also closed it.

**Files:** `backend/app/services/github_publish.py`, `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "outdated or inline_thread or close_active" -q
```

---

## P4.2 — Option A on group.id, not H2

**What:** Identity-gone resolve still uses “key not in publishable” after P0.4 UUID keys. Unit test: closed group → thread resolve; leftover eval still `active` → may still collapse if Outdated, DB not `resolved`.

**Files:** `backend/app/services/github_publish.py`, `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "inline_thread or close_active or outdated" -q
```

---

## P4.3 — Lifetime scan copy vs details

**What:** `format_pr_resolution_rollup_block` scan numbers match P3 rollup. Details identity sentence remains four-term (RH-Q12). Push block (P2) N/A must appear in a combined comment fixture so authors never see `0% of 0 prior`.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:** combined fixture: lifetime table + this-push N/A or nonzero rate; no `0.0% (0/0`.

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "format_pr_resolution_rollup_block or format_resolution_metrics_block" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_publish.py tests/unit/test_github_publish_formatter.py -q
pipenv run ruff check app/services/github_publish.py app/services/github_publish_formatter.py
```

**Deploy:** no migration. Do not change GitHub App permissions.

**Next:** [`RESOLUTION_HONESTY_P5_EXECUTION.md`](./RESOLUTION_HONESTY_P5_EXECUTION.md)
