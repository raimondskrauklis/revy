# docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_P5_EXECUTION.md

# P5 — Dogfood gates + doc-sync (execution)

Phase **P5** of [`RESOLUTION_HONESTY_GENERAL_PLAN.md`](./RESOLUTION_HONESTY_GENERAL_PLAN.md). Baseline: [`RESOLUTION_HONESTY_FINDINGS.md`](./RESOLUTION_HONESTY_FINDINGS.md) experiment table, RH-Q10. **P5 only.**

**Goal:** Findings experiment table is pass or a named residual. Then doc-sync.

## Decisions locked for P5

- **Equivalent new PR** after P0–P4 deploy (RH-Q10). Do **not** replay dogfood `#1`’s 13 superseded D10 rows as the lifetime numerator.
- Gates (all must pass or be named residuals): four H2 fixes including Pass 2 without `addressed`; leftovers = unique claims; this-push denom ≠ 0 if a prior review existed; file delete in `path_removed` **bucket**; line insert above `eval` same group still open; two same-file leftovers not H2-closed; copy has no `0% of 0 prior`; PSR-Q15 identity holds.
- Optional `post-finish-gap-pass` before doc-sync if gaps vs findings are small.
- Changelog is user-facing (authors see honest resolved / this-push on GitHub).

## Out of scope for P5

- Remap of `#1` superseded fingerprints
- New product features
- Moonshot prompt quality (INFO vs CRITICAL)

---

## P5.1 — Equivalent new PR + memo

**What:** After P0–P4 are deployed, open an equivalent PR (same four-fix / leftover / eval-insert / optional file-delete shape) on a dogfood repo. Fill `docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_STAGING_VALIDATION.md` (new) from production/staging evidence, not placeholders.

**Files:** `docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_STAGING_VALIDATION.md` (new)

**Deliverable:** each findings experiment row is pass or a named residual.

**Human gate:** LOOP stops for sign-off on the memo.

---

## P5.2 — Post-finish gap pass (optional)

**What:** If the memo names small code/docs gaps vs findings, run `post-finish-gap-pass` and fix those items in this phase before doc-sync. Skip when the memo is clean.

**Files:** only files the gap pass names

**Deliverable:** memo residuals are empty or explicitly deferred out of this program.

---

## P5.3 — Doc-sync + changelog

**What:** README LOOP statuses Done + sha. Grep siblings for stale “Pass 2 needs addressed”, “Outdated = resolved”, D10 title fingerprint as current product identity, and “BLOCK create-execution-plan: yes”. User-facing changelog: GitHub comment resolved/this-push numbers follow real closures.

| Doc | Change |
|-----|--------|
| `docs/review-pipeline/resolution-honesty/README.md` | Phase statuses + shas |
| `docs/review-pipeline/README.md` | resolution-honesty row lists execution + shipped |
| `docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_FINDINGS.md` | FR-Q3 note: superseded by resolution-honesty RH-Q9 |
| `docs/review-pipeline/REVIEW_PIPELINE_FINDINGS.md` | R5-Q1 / D10 current identity points here |
| `frontend/src/data/changelog.json` | Honest resolved / this-push on GitHub comments |

**Files:** docs listed above, `frontend/src/data/changelog.json`

**Deliverable:**

```bash
python -m json.tool frontend/src/data/changelog.json > /dev/null
```

---

**Phase gate** (from repo root):

```bash
python -m json.tool frontend/src/data/changelog.json > /dev/null
```

**Human gate:** P5.1 memo signed. LOOP does not commit P5 until gates pass or residuals are named.

**Deploy:** P0–P4 already on the environment used for the new PR. No remap of `#1`.

**Next:** none.
