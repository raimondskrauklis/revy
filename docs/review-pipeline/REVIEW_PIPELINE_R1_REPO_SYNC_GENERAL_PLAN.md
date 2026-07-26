# Review pipeline R1 — Repository sync

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** workspace tenancy on `github_repositories`; webhook path never blocks on GitHub API.

**Authority:** [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md), [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) (Metadata permission, `installation_repositories` event), [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md).

---

## Goal

Mirror installation-linked repository **metadata** after webhook events or admin-triggered full sync.

**Scope:** In — `github_repositories` table, `installation_repositories` webhook apply, `repo_sync` Celery task, minimal GitHub App API client (list repos), list + sync-repositories API. Out — git clone/mirror, branch protection, file content storage.

**Deliverables:** Repo rows per installation; cursor list API; full reconcile when `GITHUB_APP_ID` + private key set.

**Depends on:** R0.

**Status:** Shipped — tag `review-r1-v1`.

**Execution:** [waves/REVIEW_PIPELINE_R1_EXECUTION.md](./waves/REVIEW_PIPELINE_R1_EXECUTION.md).

**Next:** [REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md](./REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md).
