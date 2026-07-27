# Review quality — dogfood PR #50 (Greptile + Revy)

**PR:** [#50](https://github.com/raimondskrauklis/revy/pull/50) · **branch:** `feat/review-quality` · **phase:** RQ0  
**Raw paste:** [actual_output_revy_greptile.txt](./actual_output_revy_greptile.txt) (GitHub copy, 2026-07-27)  
**Strategy:** [REVIEW_QUALITY_REVIEW_CONTEXT.md](./REVIEW_QUALITY_REVIEW_CONTEXT.md) · **Lessons:** [CODE_REVIEW_LEARNINGS](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md)

**Deploy context:** Revy autostart ran on **pre-RQ0 production/staging** — findings about `github_review.py` reflect **shipped** code, not this branch. Greptile/Bugbot reviewed **this PR diff** with RC0 wiring.

---

## What we can fetch automatically

| Source | `gh` / API | Full detail | Gap |
|--------|------------|-------------|-----|
| **Greptile** threads | GraphQL `reviewThreads` + REST `pulls/comments` | P1/P2 body, path, line, suggestions | Need filter `greptile-apps` login |
| **Greptile** summary | Check run `output.summary` | Confidence, files needing attention | In check run API |
| **Revy** check | `gh pr checks` / check-runs API | Compact table + link to Revy UI | No pipeline trace until RQ3 ships |
| **Revy** reviewer UI | — | Full messages, judge, dismiss | Needs app login — not in `gh` |
| **Bugbot** | Local subagent only | Pre-push diff review | Not on GitHub Checks unless Cursor PR integration |

**Babysit workflow:** GraphQL gives all Greptile inline threads; no extra GitHub permissions needed beyond repo read. Revy internal run detail requires Revy API or UI — document paste (like `actual_output_revy_greptile.txt`) until pipeline GET ships (RQ3).

---

## Side-by-side (RQ0 commit)

| Dimension | Greptile | Revy (old deploy) |
|-----------|----------|-------------------|
| **Checks UX** | `in_progress` spinner ~5m | Appears only at end — **G10** |
| **Wired to execution doc** | Yes (RC0 `files.json`) | No — reviews code behavior only |
| **Confidence / narrative** | 3/5 + summary prose | Table only |
| **Schema review** | Strong — FK semantics, O8 index | N/A |
| **Intent vs code** | Migration + ORM vs execution | Flags RQ1 gap (full RAG) |
| **Planning doc findings** | Low | Yes — README, findings, execution |

---

## Greptile — triage (babysit)

| Sev | Location | Finding | Action |
|-----|----------|---------|--------|
| P1 | `0026_review_quality.py` | Nullable pipeline FKs need `ON DELETE SET NULL` | **Fixed** |
| P1 | `github_pipeline.py` | ORM FK `ondelete` match | **Fixed** |
| P1 | `0026_review_quality.py` | `ix_github_pipeline_runs_created_at` for O8 purge | **Fixed** |
| P2 | `0026_review_quality.py` | Historical `index_mode` backfill → `full` | **Fixed** |
| P2 | `0026_review_quality.py` | `revision_id` → `ON DELETE CASCADE` | **Fixed** |
| P2 | `0026_review_quality.py` | Artifact `CHECK` content present | **Fixed** |

**Greptile verdict:** RC0 wiring worked — cited O8, execution contract, migration file. Confidence 3/5 was fair before FK fixes.

---

## Revy — triage (old deploy)

| Sev | Location | Finding | Action |
|-----|----------|---------|--------|
| error | `github_review.py` | Full-revision RAG not diff-first | **RQ1** — expected; not a babysit fix |
| warning | `README.md` | Inconsistent dependency baseline | **Doc** — align prerequisite line (RQ8) |
| warning | `FINDINGS.md` | Raw LLM storage / encryption | **Parking** — O4/O6; ops note for v1 |
| warning | `EXECUTION.md` | Duplicate index job on deep/critical | **Verify AS1** in RQ1 — execution already locks behavior |

**Revy verdict:** Useful product dogfood — caught the main RQ1 gap without reading Greptile. Check `failure` is expected until RQ1 lands on deploy.

---

## What is good (keep)

| # | Observation |
|---|-------------|
| G1 | Greptile + RC0 reads execution/findings — schema defects caught pre-staging |
| G2 | Revy autostart on planning PR — validates intent drift even on doc-heavy diffs |
| G3 | Local Bugbot pre-push — zero findings on RQ0 ORM |
| G4 | CI green on migration + models |
| G5 | Greptile confidence + “files needing attention” — good triage surface |

---

## What needs updates (parallel waves)

| ID | Wave | Item |
|----|------|------|
| **G10** | RQ3 + RQ7 | `revy/review` check `in_progress` → `completed` (Greptile/Bugbot parity) |
| **RQ1** | RQ1 | Diff-first retrieval — fixes Revy error on deploy |
| **RQ3** | RQ3 | Pipeline GET — agents can read trace without UI paste |
| **RC1** | RQ-RC-1 | Scope Greptile files to active RQ slice if noise grows |
| **RC-API** | Post-RQ3 | Expose check-run / run metadata via API for babysit automation |
| **O-sec** | Parking | Document retention + secret redaction in pipeline artifacts (Revy warning) |

---

## Permissions / tooling notes

- **`gh api graphql`** — sufficient for Greptile babysit on private repo (repo scope).
- **Revy run detail** — `gh` only sees GitHub check output; link `Open in Revy` needs human or future Revy API token for agents.
- **Paste file** — keep `actual_output_revy_greptile.txt` or per-PR snapshots when API gap matters.

---

## Next entries (per RQ phase)

After each LOOP commit on #50, add a row:

| Phase | Greptile | Revy | Notes |
|-------|----------|------|-------|
| RQ0 | 6 threads, FK fixes | 4 findings, 1 error (RQ1) | This doc |
| RQ1 | — | — | Diff-first deploy target |
