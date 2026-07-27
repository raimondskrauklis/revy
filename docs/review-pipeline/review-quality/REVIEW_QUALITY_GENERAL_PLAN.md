# Review quality — general plan index

Per-phase goals in **separate files** — same discipline as [REVIEW_PIPELINE_GENERAL_PLAN.md](../REVIEW_PIPELINE_GENERAL_PLAN.md). **No execution steps.**

**Baseline:** [REVIEW_QUALITY_FINDINGS.md](./REVIEW_QUALITY_FINDINGS.md) — devil's-advocate pass resolved (2026-07-27).

**Ship model:** **One PR** (`feat/review-quality`) — R1–R5 are **documentation slices**, not merge order. One execution file: `waves/REVIEW_QUALITY_EXECUTION.md`. Tag: `review-quality-v1`.

**Prerequisite:** R0–R8 on `main`; AS2 staging e2e gate in RQ8 (fix code only if gate fails).

---

## Why index + per-phase plans (not one huge doc)

| Approach | Verdict |
|----------|---------|
| **One monolithic general plan** (all R1–R5) | **No** — duplicates findings; too heavy to navigate. |
| **One general plan per track** (D, O, G, …) | **No** — D+O ship together (D11/S1); tracks are planning labels. |
| **Index + one general plan per slice** (R1–R5) | **Yes** — readable slices; **one PR** implements all. |

---

## Slices (R1–R5) — one PR

| Slice | General plan | Tracks | Focus |
|-------|--------------|--------|-------|
| **R1** | [R1 diff + trace](./REVIEW_QUALITY_R1_DIFF_AND_TRACE_GENERAL_PLAN.md) | **D + O** | Compare, diff index (D13), context pack, pipeline trace, `items_view` API, purge |
| **R2** | [R2 incremental index](./REVIEW_QUALITY_R2_INCREMENTAL_INDEX_GENERAL_PLAN.md) | **I + C1** | Copy-forward, content_hash, delta embed |
| **R3** | [R3 GitHub publish](./REVIEW_QUALITY_R3_GITHUB_PUBLISH_GENERAL_PLAN.md) | **G** | Greptile PR comment; G3 split check vs comment |
| **R4** | [R4 evidence + judge](./REVIEW_QUALITY_R4_EVIDENCE_JUDGE_GENERAL_PLAN.md) | **E** | Evidence snippet; grounding judge |
| **R5** | [R5 resolution metrics](./REVIEW_QUALITY_R5_RESOLUTION_METRICS_GENERAL_PLAN.md) | **M + G9** | `resolution_status`; feeds R3 prose |
| **R6+** | — | **A** | Multi-agent — **defer** |

## Execution

| File | Status |
|------|--------|
| `waves/REVIEW_QUALITY_EXECUTION.md` | **next** — all slices, 3–6 subphases per slice |

Execution lives under [../waves/](../waves/) (same as R0–R8).

---

## Cross-cutting (whole PR)

Workspace tenancy on all new rows; pipeline trace on every LLM/retrieval step; **`items_view`** pipeline read (O9); **`admin_users`** retention/export; EN+LV only for new user-facing strings; unit tests; hand-written Alembic; milestone `review-quality-v1`.

**GitHub-first:** PR comment + check run primary; `/reviewer` trace tab out of scope.

**Full-repo index:** never removed — `index_mode=full` for `deep`/`critical` (AS1) with warnings (D3).

**Diff index (D13):** compare for file list + unified diff; tarball bytes for changed paths only; manifest always records `changed_files`, `index_mode`, `fallback_reason`.

---

## Locked calibration (findings — no longer open)

D4=0, D5=128KB, D7=test retrieval exclusion (not CI), D10=fingerprint shape, C1=copy-forward, G3=split bodies, G9=R5 owns resolution prose input. **Post-v1 cross-file:** [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) (SC1–SC8, RQ-STRUCT-1/2). **Post-v1 review context:** [REVIEW_QUALITY_REVIEW_CONTEXT.md](./REVIEW_QUALITY_REVIEW_CONTEXT.md) (RC0–RC6, RQ-RC-1).

---

## Next

1. **[Peer review](./REVIEW_QUALITY_PEER_REVIEW.md)** — pre-execution locks applied.
2. **`phase-execution`** on `feat/review-quality` starting at RQ0.
