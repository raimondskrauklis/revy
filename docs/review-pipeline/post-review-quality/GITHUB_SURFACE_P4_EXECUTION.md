# GitHub surface P4 — Doc sync (execution)

Phase **P4** of [POST_REVIEW_QUALITY_GENERAL_PLAN.md](./POST_REVIEW_QUALITY_GENERAL_PLAN.md). Baseline: [POST_REVIEW_QUALITY_FINDINGS.md](./POST_REVIEW_QUALITY_FINDINGS.md) §12. **P4 only — final phase.**

**Goal:** Docs reflect shipped L1–L3 evidence; dogfood log and product map consistent.

**Authority:** [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) · [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md)

## Decisions locked for P4

- Doc-only phase — no backend feature work unless dogfood uncovered a doc lie.
- Git tags optional — not required for P4 done.
- No `changelog.json` — GitHub surface is not end-user SaaS UI copy.
- STRUCT / RC4 execution plans not created here.
- Optional **`post-finish-gap-pass`** skill before P4.4 if operator wants platform sweep.

## Out of scope for P4

- Track B programs (STRUCT, RQ-RC-1)
- `/reviewer` pipeline tab
- Customer Greptile config

---

## P4.1 — PRODUCT_PATTERNS L1–L3 rows

**What:** Flip **Status** to `shipped` only when dogfood confirms. Use exact **Pattern** column labels from [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md):

| Section | Pattern (exact row label) | When `shipped` |
|---------|---------------------------|----------------|
| Review output & signal | **PR summary narrative** | L2 pass — update Revy approach cell to note G3: compact check + full issue comment |
| Review output & signal | **Numeric confidence 0–5** | L2 pass — update Revy approach to `compute_confidence` on comment/check |
| Review output & signal | **Issues table in review** | L2 pass (already shipped — verify) |
| Review output & signal | **Inline file+line comments** | L3 pass — note warning breadth post-P3 in Revy approach cell |
| Stability across pushes | **Idempotent GitHub surface** | Already shipped — verify dogfood shows update-in-place |
| Stability across pushes | **Check run in progress on PR** | L1 pass — G10 on dogfood PR |

Do **not** flip unrelated rows (graph, reranker, human dismiss, precision metrics).

**Files:** `docs/review-pipeline/REVIEW_PIPELINE_PRODUCT_PATTERNS.md`

**Deliverable:** Listed rows match dogfood evidence; no stale `in flight` / `defer` on those rows.

---

## P4.2 — DOGFOOD #50 gap table

**What:** Update [REVIEW_QUALITY_DOGFOOD_PR50.md](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md) “Gap → wave map” — G10, G2, G3, G9 landed; link to [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md) for post-RQ evidence.

**Files:** `docs/review-pipeline/review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md`

**Deliverable:** Gap table no longer says “not landed yet” for shipped items.

---

## P4.3 — Program README + execution index

**What:** Mark P0–P4 **Done** + commit sha in [README.md](./README.md) and [GITHUB_SURFACE_EXECUTION.md](./GITHUB_SURFACE_EXECUTION.md) table.

**Files:** `docs/review-pipeline/post-review-quality/README.md`, `docs/review-pipeline/post-review-quality/GITHUB_SURFACE_EXECUTION.md`

**Deliverable:** Execution table status rows updated.

---

## P4.4 — Doc sync table

**What:** Append sync record (this subphase deliverable):

| Doc | Change |
|-----|--------|
| PRODUCT_PATTERNS | Rows per P4.1 |
| DOGFOOD #50 | Gap map |
| GITHUB_SURFACE_DOGFOOD | All program PR rows |
| post-review-quality/README | Status Done |
| GITHUB_SURFACE_EXECUTION | Status Done |
| .cursor/BUGBOT.md | Program status line → github surface complete |

**Files:** as above

**Deliverable:** Table complete in PR description or P4 commit body.

---

**Phase gate** (docs — run manually; no pytest):

```bash
test -f docs/review-pipeline/post-review-quality/GITHUB_SURFACE_DOGFOOD.md && \
grep -q "in progress on PR" docs/review-pipeline/REVIEW_PIPELINE_PRODUCT_PATTERNS.md && \
! grep -q "not landed yet" docs/review-pipeline/review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md
```

**Human gate:** Dogfood rows cover L1/L2/L3 or explicit waive in log.

**Optional:** git tag deploy bookmark — operator choice (findings §11).

**Next:** none — program complete; track B (STRUCT) is separate planning.
