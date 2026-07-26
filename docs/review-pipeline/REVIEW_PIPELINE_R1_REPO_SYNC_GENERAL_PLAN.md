# Review pipeline R1 — Repository sync

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** workspace tenancy on `github_repositories.workspace_id`; webhook handler never blocks on GitHub API; unit tests; hand-written Alembic.

**Authority:** [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md), [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) § R1, [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md).

---

## Goal

Mirror installation-linked repository **metadata** from webhooks and optional GitHub App API full sync — repo allowlist for PR ingestion and indexing.

**Scope:** In — `github_repositories` table (`active` \| `removed`); `apply_installation_repositories_webhook_event`; `repo_tasks.sync_installation_repositories` on `repo_sync` queue; `integrations/github_api.py` (app JWT, installation token, paginated list); `GET …/installations/{id}/repositories`; `POST …/sync-repositories` (admin, `503` when App creds missing); extend R0 `github_tasks` for `installation_repositories`. Out — git clone/mirror, branch protection rules, file blob storage (R3 paths only).

**Deliverables:** Repo rows per installation; cursor list API; webhook upsert/remove; full reconcile marks missing repos `removed`; migration `0011`; `github_api_enabled` config gate.

**Depends on:** R0.

**Status:** Shipped — tag `review-r1-v1` (`dddfde0`).

**Execution:** [waves/REVIEW_PIPELINE_R1_EXECUTION.md](./waves/REVIEW_PIPELINE_R1_EXECUTION.md).

**Next:** [REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md](./REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md).
