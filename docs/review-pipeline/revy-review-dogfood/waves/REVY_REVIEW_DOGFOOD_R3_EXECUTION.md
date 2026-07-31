# docs/review-pipeline/revy-review-dogfood/waves/REVY_REVIEW_DOGFOOD_R3_EXECUTION.md

# R3 — Resolution stamp unblock (execution)

Phase **R3** of [REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md](../REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md). Baseline: [REVY_REVIEW_DOGFOOD_FINDINGS.md](../REVY_REVIEW_DOGFOOD_FINDINGS.md) § RR-DG4, RR-DG11, RC-3. **R3 only.**

**Goal:** Active groups on current HEAD can close when fix is present; stale `closure_blocked_reason` cleared; pairing survives merge + ingest gaps after R1.

**Doc authority:** R3.2 trigger matches [staging validation § R3 subphase map](../REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md) — when R0.2 lists secondary `pairing_gap`, implement R3.2 + R3.3 alongside R3.1 (not gated on primary tag alone).

## Decisions locked for R3

- Implement fixes **per RR-DG4 primary tag** from R0 § R0.2 — subphase map:

| R0 tag | Subphase |
|--------|----------|
| `stale_closure_blocked` | **R3.1** (always) |
| `pairing_gap` (primary or secondary in R0.2) | **R3.2** — **always** when R0.2 memo lists secondary `pairing_gap` (current TenderPro memo); re-evaluate after R3.1 if RR-V2 still fails |
| `line_region_miss` | **R3.4** |
| `api_compare_failed` | **R3.5** |
| RR-DG11 (any tag) | **R3.3** after R1 |

- Use `closure_blocked_reason` values `compare_failed` and `head_check_failed` (`github_finding_closure_rules.py`) — not informal "compare_blocked".
- `publish_skipped_not_head` remains intentional — document in R5 (RR-DG10); RR-DG5 SHA lag treated as downstream of R1 publish success.
- Do not duplicate `paths_absent_at_head` logic.

## Out of scope for R3

- False positive suppression → **R4**
- Product merge gate → **R5**

---

## R3.1 — Stale closure_blocked_reason clear (always)

**What:** When compare succeeds on current synchronize and HEAD line-region check passes, clear stale `closure_blocked_reason` of `compare_failed` or `head_check_failed` from superseded revision; allow `resolution_status` to advance.

**Files:** `backend/app/services/github_resolution_metrics.py` (`apply_resolution_status_for_synchronize`)

**Deliverable:** Unit test: group with stale `compare_failed` + passing compare/HEAD region → `closure_blocked_reason` cleared and `resolution_status` eligible for `addressed`.

---

## R3.2 — Pairing cohort repair (secondary `pairing_gap`)

**What:** When active group's `last_seen_revision_id` is outside `pairing_revision_ids` but group was published on an earlier revision still on the PR, include in synchronize cohort (bounded: same `pull_request_id`, revision_number ≤ current, not superseded). Log `resolution_pairing_repaired` with fingerprint.

**Files:** `backend/app/services/github_resolution_metrics.py` (`apply_resolution_status_for_synchronize`, `prior_publish_pairing_revision_ids` helpers)

**Deliverable:** Unit test: group `last_seen` on rev 10, last published prior rev 10, current rev 12 after merge — group included in cohort and stamped.

**When:** R0.2 lists secondary `pairing_gap` (current TenderPro memo) — **implement in R3** alongside R3.1; not gated on primary tag alone.

---

## R3.3 — Intermediate revision gap repair (RR-DG11)

**What:** After R1 ingest fix: when `last_seen_revision_id` references a revision row that exists but has no completed publish, re-link pairing to nearest prior **published** revision for resolution stamp (do not invent revision rows).

**Files:** `backend/app/services/github_resolution_metrics.py` (`get_last_published_prior_revision`, pairing helpers)

**Deliverable:** Unit test: published rev N, failed/skipped N+1 ingest, current N+2 — group pairs through gap to published prior.

---

## R3.4 — Line-region HEAD verification (`line_region_miss` tag)

**What:** Add **new** helper `_verify_fix_at_head_line_region` in `github_resolution_metrics.py`: when prior→new compare patch does not touch finding lines but HEAD file at `new_revision.head_sha` shows fix (e.g. import present, symbol defined), stamp `addressed`. Extend existing block ~267–307 — do not replace `paths_absent_at_head`.

**Files:** `backend/app/services/github_resolution_metrics.py`

**Deliverable:** Unit test with TenderPro fixture path when available (`entities.py` / `or_` import) or synthetic file snippet.

**Skip when R0 tag is not `line_region_miss`:** no-op with test noting tag gate.

---

## R3.5 — Compare API bounded retry (`api_compare_failed` tag)

**What:** When `fetch_compare_patches` fails for resolution metrics (`resolution_metrics_compare_failed`), one bounded retry with backoff before setting `compare_failed` on cohort. Reuse `github_compare_patches.py` — resolution path only.

**Files:** `backend/app/services/github_compare_patches.py`, `backend/app/services/github_resolution_metrics.py` (`_fetch_compare_patches`)

**Deliverable:** Unit test: first compare raises `ServiceUnavailableError`, second succeeds → `compare_failed` not stamped.

**Skip when R0 tag is not `api_compare_failed`:** no-op with test noting tag gate.

---

## R3.6 — RR-V2 staging criteria doc hook

**What:** Update validation memo § RR-V2 with expected resolution rate **> 0%** on re-run after R3 on same PR cohort; reference R0 § R0.2 tag.

**Files:** `REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:** Pass rule documented; actual staging run in R5.

---

**Phase gate:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_compare_patches.py -q -k "resolution or closure or compare"
pipenv run ruff check app/services/github_resolution_metrics.py app/services/github_compare_patches.py
```

**Human gate:** R0 RR-DG4 tag implemented — R3.1 + R3.2 + R3.3 always for current memo; R3.4/R3.5 only when tag requires.

**Next:** [REVY_REVIEW_DOGFOOD_R4_EXECUTION.md](./REVY_REVIEW_DOGFOOD_R4_EXECUTION.md)
