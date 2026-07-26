# Review pipeline R3–R7 — outline

Bundled general plans for phases not yet baseline-ready. Split into per-phase files when execution approaches (same pattern as [docs/saas-base](../saas-base/README.md)).

From [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting (every phase):** workspace tenancy, audit where mutating, EN+LV, unit tests, hand-written Alembic.

**GitHub App:** permissions and events per [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md).

---

## R3 — Indexing

**Goal:** Chunk and embed repository content for review context.

**Scope:** In — pgvector index jobs, `indexing` queue, Contents read via installation token. Out — symbol index, cross-repo search.

**Deliverables:** Embeddings stored; retrieval API for review stage.

**Depends on:** R2.

---

## R4 — Review run

**Goal:** LLM pipeline produces structured findings per PR revision.

**Scope:** In — `review_tasks`, model provider config (`moonshot`, `anthropic`, `voyage` env keys), finding schema. Out — multi-model judge (→ R5).

**Deliverables:** Review run record + findings rows; gated API for workspace members.

**Depends on:** R3.

---

## R5 — Reconciliation + judge

**Goal:** Deduplicate and escalate findings across revisions.

**Scope:** In — `reconciliation`, `judge` queues, fingerprint logic. Out — human review workflow.

**Deliverables:** Stable finding identity across pushes; judge outcomes persisted.

**Depends on:** R4.

---

## R6 — GitHub publish

**Goal:** Post check runs and review comments to GitHub.

**Scope:** In — `github_publish` tasks, Checks + Pull requests write permissions. Out — inline suggestion API v2 nuances.

**Deliverables:** Check run status on PR; summary comment posted.

**Depends on:** R5.

---

## R7 — Reviewer UI

**Goal:** In-app surfaces for PR status, findings, and review history.

**Scope:** In — `features/reviewer/`, routes, dashboard widgets, i18n EN+LV. Out — GitHub.com replacement UI.

**Deliverables:** Member can view findings for workspace PRs; links to GitHub.

**Depends on:** R4 (read-only UI can ship before R6 with caveats).

---

## Next

When R2 ships, extract **R3** into `REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md` before execution planning.
