# Review pipeline — findings

Baseline for Revy **AI code review on GitHub** after SaaS base W0–W8 + P4 installations. **No execution steps.**

**Status:** baseline-ready (2026-07-26). **Shipped on `main`:** R0–R3 (`review-r0-v1` … `review-r3-v1`); remediation PRs #13–#21 merged. **Implemented (PR stack, pending merge):** R4–R7 — [#24](https://github.com/raimondskrauklis/revy/pull/24) … [#27](https://github.com/raimondskrauklis/revy/pull/27). **General plans:** R0–R7 complete; execution peer-review done for R4. **Next:** merge stack → migrations `0014`–`0016` → tags `review-r4-v1` … `review-r7-v1` ([checklist](./REVIEW_PIPELINE_RECOVERY_CHECKLIST.md)).

**Program:** [README.md](./README.md) · **Authority (full):** `internal-docs/product/revy/docs/architecture.md`, `WEBHOOKS.md`, `REVY_PRODUCT_SLICE.md`.

---

## Goal

Ship the **Revy review pipeline** additively on the SaaS shell: GitHub App webhooks → repository metadata → PR ingestion → indexing → LLM review → publish → in-app reviewer UI. One repo, feature branches, milestone tags on `main`.

**GitHub App (external):** register and configure per committed runbooks — not code in this repo, but required for live webhooks and API sync.

---

## Build principles

- **Additive** on SaaS shell — no fork; workspace tenancy on all domain rows.
- **GitHub App** webhooks + installation API; Celery queues per [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md).
- **Planning order:** findings (this file) → per-phase **general plan** → **execution** under `waves/` → `phase-execution` on a feature branch.
- **Folder layout:** mirror [docs/saas-base](../saas-base/README.md) — findings + general plans here; execution files under `waves/` only.
- **Hand-written Alembic**; unit tests only (`backend/tests/unit/`).
- **EN+LV** for user-facing strings; `--app-*` tokens.
- **Never block webhook HTTP** on GitHub API — persist + enqueue.

---

## GitHub App — ops docs (committed)

Revy code does not replace GitHub App registration. Use these before expecting webhooks or repo sync to work:

| Doc | When |
|-----|------|
| [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) | Step-by-step create App; minimal permissions for **today** (R0–R1) |
| [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) | Register **once** with full R0–R7 permissions/events (recommended for prod/staging) |
| [GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md) | Local smee.io / tunnel, secret alignment, verify delivery |
| [GITHUB_APP_DESCRIPTION.md](../utils/GITHUB_APP_DESCRIPTION.md) | Form copy-paste for App description |

**Env (backend):** `GITHUB_WEBHOOK_SECRET` (R0+); `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY_PATH` (R1 full sync); see `backend/.env.example`.

**Product note:** SaaS shell runs without GitHub configured. Review features degrade gracefully (`503` / skip) until secrets and App are wired.

---

## What exists vs genuinely new

### Verified — shipped in repo

| Layer | Capability | Evidence | Tag |
|-------|------------|----------|-----|
| **P4 Installations** | `github_installations`, list + dev register API/UI | `features/installations/`, migration `0008` | `saas-base-v1` |
| **R0 Webhooks** | `POST /api/v1/webhooks/github`, HMAC, dedupe, `github_events` | `webhooks/github.py`, `0010`, `github_tasks` | `review-r0-v1` |
| **R1 Repositories** | `github_repositories`, webhook apply, `repo_sync`, list/sync API | `github_repositories.py`, `0011`, `repo_tasks` | `review-r1-v1` |
| **R2 Pull requests** | `github_pull_requests`, revisions, `pull_request` webhooks, list API | `github_pull_requests.py`, `0012`, `github_tasks` | `review-r2-v1` |
| **R3 Indexing** | `github_index_jobs`, `github_code_chunks`, Voyage API embeddings (`voyage-3-lite`), semantic search | `github_indexing.py`, `voyage_embeddings.py`, `0013`, `index_tasks` | `review-r3-v1` |
| **GitHub API client** | App JWT + installation token + list repos | `integrations/github_api.py` | `review-r1-v1` |
| **Stripe webhook pattern** | Idempotent ingest (reference) | `webhooks/stripe.py` | SaaS W4 |

### Verified — config / infra

| Item | State |
|------|--------|
| Celery routes | `github_events`, `repo_sync`, `indexing`, `review`, `reconciliation`, `judge`, `github_publish`, … in `celery_app.py` |
| Worker deploy (CI) | `deploy.yml` worker `-Q` includes full Revy list (PR #24+) — see [PROGRAM](./REVIEW_PIPELINE_PROGRAM.md) §5 |
| Migrations | `0001`–`0013` on `main`; `0014`–`0016` on PR stack (#24–#26) |
| pgvector | Extension in deploy SQL; `github_code_chunks.embedding` vector(512) — **R3 shipped** |

### Verified — implemented (PR stack #24–#27, pending merge)

| Layer | Capability | Evidence | PR |
|-------|------------|----------|-----|
| **R4 Review run** | `github_review_runs`, `github_findings`, Moonshot LLM, `review_tasks` | `services/github_review.py`, `integrations/moonshot_review.py`, `0014` | [#24](https://github.com/raimondskrauklis/revy/pull/24) |
| **R5 Reconcile + judge** | `github_finding_groups`, judge outcomes, fingerprint reconcile | `services/github_finding_reconcile.py`, `github_finding_judge.py`, `0015` | [#25](https://github.com/raimondskrauklis/revy/pull/25) |
| **R6 GitHub publish** | Check run `revy/review`, PR comments, `publish_tasks` | `services/github_publish.py`, `0016` | [#26](https://github.com/raimondskrauklis/revy/pull/26) |
| **R7 Reviewer UI** | `features/reviewer/`, `/reviewer` routes, merge badge | `frontend/src/features/reviewer/` | [#27](https://github.com/raimondskrauklis/revy/pull/27) |

### Reuse caveats / traps

| Trap | Detail |
|------|--------|
| **Orphan installation** | Webhook for unknown `github_installation_id` → log + **200**; register via `/installations` first |
| **GitHub optional at runtime** | Empty `GITHUB_WEBHOOK_SECRET` → webhooks disabled; empty App id/key → full sync disabled |
| **OAuth install UI** | Not shipped — manual register (P4) until later phase |
| **`heavy_job`** | Routed in `celery_app.py` but undefined — SaaS carryover |
| **Judge without Anthropic** | R5 reconcile completes; judge skipped when `ANTHROPIC_API_KEY` unset (R5-Q3) |
| **Skipped planning on R0/R1** | Code shipped first; general plans + findings updated retroactively — **do not repeat for R2+** |
| **Retrospective PR review** | Audit PR pattern (never merge) + fix PRs — see [agent checklist](./REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) § Revy review QA |

---

## Catalog (phased)

| Phase | Capability | General plan | Execution | Status |
|-------|------------|--------------|-----------|--------|
| **R0** | Webhook ingest + HMAC + dedupe + `github_events` | [R0](./REVIEW_PIPELINE_R0_WEBHOOKS_GENERAL_PLAN.md) | [R0 exec](./waves/REVIEW_PIPELINE_R0_EXECUTION.md) | **shipped** |
| **R1** | Repository metadata + `repo_sync` | [R1](./REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md) | [R1 exec](./waves/REVIEW_PIPELINE_R1_EXECUTION.md) | **shipped** |
| **R2** | PR ingestion + revisions | [R2](./REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md) | [R2 exec](./waves/REVIEW_PIPELINE_R2_EXECUTION.md) | **shipped** |
| **R3** | Indexing (chunks, pgvector) | [R3](./REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md) | [R3 exec](./waves/REVIEW_PIPELINE_R3_EXECUTION.md) | **shipped** |
| **R4** | LLM review + findings | [R4](./REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md) | [R4 exec](./waves/REVIEW_PIPELINE_R4_EXECUTION.md) | **implemented** — PR [#24](https://github.com/raimondskrauklis/revy/pull/24) |
| **R5** | Reconciliation + judge | [R5](./REVIEW_PIPELINE_R5_RECONCILE_JUDGE_GENERAL_PLAN.md) | [R5 exec](./waves/REVIEW_PIPELINE_R5_EXECUTION.md) | **implemented** — PR [#25](https://github.com/raimondskrauklis/revy/pull/25) |
| **R6** | GitHub publish | [R6](./REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md) | [R6 exec](./waves/REVIEW_PIPELINE_R6_EXECUTION.md) | **implemented** — PR [#26](https://github.com/raimondskrauklis/revy/pull/26) |
| **R7** | Reviewer UI | [R7](./REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md) | [R7 exec](./waves/REVIEW_PIPELINE_R7_EXECUTION.md) | **implemented** — PR [#27](https://github.com/raimondskrauklis/revy/pull/27) |

---

## Domain states (enums)

Source of truth: `backend/app/constants/enums.py`. String values are stored in Postgres.

| Table / concept | Column / field | Values | Phase |
|-----------------|----------------|--------|-------|
| `github_installations` | `status` | `active` · `suspended` · `removed` | P4 |
| `github_repositories` | `status` | `active` · `removed` | R1 |
| `github_pull_requests` | `state` | `open` · `closed` | R2 |
| `github_pull_request_reviews` | `state` | `approved` · `changes_requested` · `commented` · `dismissed` · `pending` | R2 |
| `github_index_jobs` | `status` | `pending` · `processing` · `completed` · `failed` | R3 |
| `github_review_runs` | `status` | `pending` · `processing` · `completed` · `failed` | R4 |
| `github_findings` | `severity` | `info` · `warning` · `error` · `critical` | R4 |
| `github_findings` | `category` | `security` · `bug` · `performance` · `style` · `maintainability` · `other` | R4 |
| Review profile (API + run) | `profile` | `standard` · `deep` · `critical` | R4 |
| `github_finding_groups` | `state` | `active` · `superseded` · `resolved` | R5 |
| `github_finding_judge_outcomes` | `outcome` | `upheld` · `dismissed` · `modified` | R5 |
| `github_publish_jobs` | `status` | `pending` · `processing` · `completed` · `failed` | R6 |
| GitHub check run | `conclusion` (API) | `success` · `failure` · `neutral` — derived from active group severities ([R6-Q2](#decisions-registry)) | R6 |

**R5 group lifecycle:** new finding fingerprint → `active` group; superseded revision match → prior group `superseded`; judge dismiss → group `resolved` (finding may remain for audit).

**R4 run lifecycle:** admin trigger → `pending` → worker `processing` → `completed` or `failed`; concurrent trigger → `409 review_in_progress` while `pending`/`processing`.

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| Q1 | Same repo vs fork? | **locked** | Same repo; `saas-base-v1` tag |
| Q2 | Webhook path | **locked** | `POST /api/v1/webhooks/github` |
| Q3 | Delivery dedupe store | **locked** | `github_webhook_deliveries` (Stripe pattern) |
| Q4 | Handler response | **locked** | Verify → dedupe → enqueue → **200**; no GitHub API in handler |
| Q5 | R0 event scope | **locked** | `installation`, `installation_repositories`, `push` |
| Q6 | Repository table name | **locked** | `github_repositories` (not generic `repositories`) |
| Q7 | GitHub App registration | **locked** | Committed runbooks in `docs/utils/`; target config for one-time prod setup |
| Q8 | Worker deploy | **locked** | Document v1 queue list; CI worker update when ops ready |
| Q9 | Plan gates on review | **defer** | After R4 — LLM cost gating TBD |
| Q10 | OAuth GitHub App install UI | **defer** | Manual register until post-R2 |
| R2-Q1 | PR table naming | **locked** | `github_pull_requests` + `github_pull_request_revisions` |
| R2-Q2 | `pull_request` actions v1 | **locked** | `opened`, `synchronize`, `closed`, `reopened` |
| R2-Q3 | Unknown repository on PR webhook | **locked** | Log + **200** (orphan policy) |
| R2-Q4 | PR list API | **locked** | `GET …/repositories/{repo_id}/pull-requests` cursor list |
| R2-Q5 | `pull_request_review` v1 | **locked** | Store review activity row; no publish |
| R3-Q1 | Embedding backend v1 | **locked** | **API first:** Voyage (`voyage-3-lite`, dim 512 shipped). **Parallel track:** self-hosted via `EmbeddingBackend` + `REVY_HF_CACHE_PATH` (`jina-embeddings-v2-base-code`, `nomic-embed-code`) — `architecture.md` §11.3.1 |
| R3-Q2 | Embedding env | **locked** | `VOYAGE_API_KEY` + `REVY_EMBEDDING_MODEL` / `REVY_EMBEDDING_DIMENSIONS`; future `REVY_EMBEDDING_BACKEND=voyage\|local` |
| R3-Q3 | Reranker (retrieval) | **defer** | API vs local `bge-reranker-v2-m3` — post-R3 eval (`REVY_RERANKER_BACKEND`) |
| R4-Q1 | Review trigger permission | **locked** | `admin_users` (same as R3 index trigger) |
| R4-Q2 | Concurrent review runs | **locked** | `409 review_in_progress` if pending/processing run exists for revision |
| R4-Q3 | Review prerequisites | **locked** | Latest index job `completed` + `VOYAGE_API_KEY` + `github_api_enabled` + `MOONSHOT_API_KEY` |
| R4-Q4 | Primary LLM / model tiers | **locked** | Moonshot Kimi — `kimi-k2.7-code` (Standard), `kimi-k3` (Deep/Critical). Anthropic Claude = judge / cross-check in **R5** only (`architecture.md` §13–14) |
| R4-Q5 | Finding scope (R4 v1) | **locked** | Actionable logic/security/behavior only — not style/lint (CI owns style) |
| R4-Q6 | Token / cost ceiling | **defer** | Max chunks × max tokens in R4.3 — lock after first staging runs |
| Q11 | Auto index/review on webhook | **locked** | **Manual admin trigger** through R7; **R8** ships autostart + `@revy review` — [R8 plan](./REVIEW_PIPELINE_R8_AUTOMATION_GENERAL_PLAN.md) |
| R8-Q1 | Workspace autostart default | **locked** | `workspaces.review_autostart_enabled` default `true`; admin PATCH |
| R8-Q2 | Autostart webhook actions | **locked** | `pull_request` `opened` + `synchronize` only; enqueue on `synchronize` only when new revision row created |
| R8-Q3 | On-demand command | **locked** | `issue_comment` `created` with `@revy review` on open PR → full pipeline; ignore bot self-comments; skip closed/draft |
| R8-Q4 | Chain prerequisites | **locked** | Orchestrator skips with log when API/LLM keys disabled; no failed-job spam; webhook HTTP stays 200 |
| R8-Q5 | Index concurrency | **locked** | `409 index_in_progress` guard (mirror R4 `review_in_progress`) |
| R8-Q6 | Single PR read API | **locked** | `GET …/pull-requests/{pull_request_id}` for reviewer detail |
| R8-Q7 | Manual index isolation | **locked** | Admin `POST …/index` sets `trigger_source=manual`; index-complete does **not** auto-enqueue review |
| R5-Q1 | Fingerprint algorithm | **locked** | `sha256(workspace_id ‖ pull_request_id ‖ file_path ‖ category ‖ normalize(message)[:500])` — scoped per PR |
| R5-Q2 | Reconciliation schema + API | **locked** | `github_finding_groups` (`pull_request_id` FK, fingerprint unique per PR); `github_findings.group_id`; states `active` \| `superseded` \| `resolved`; API `GET …/findings/reconciled` |
| R5-Q3 | Judge trigger policy | **locked** | Judge when `severity ∈ {error, critical}` OR (`category = security` AND `severity ≥ warning`); max 10 calls/run; skip judge when `ANTHROPIC_API_KEY` unset (reconcile still completes) |
| R6-Q1 | Idempotent publish | **locked** | Update **check run** in place per `head_sha`; update stored PR summary comment in place when `publish_job` has `github_comment_id` — no new top-level comment per re-review (comment strategy detail in R6 execution) |
| R6-Q2 | Merge readiness v1 | **locked** | Check run `conclusion`: `failure` if any active `error` or `critical`; `success` if none; `neutral` if only `warning`/`info`; optional R7 badge — **no** numeric 0–5 score v1 |
| R6-Q3 | Suggested fix text | **defer** | Optional `suggestion` on finding row; GitHub suggestion block in R6 only when line-accurate |

---

## Edge cases

| Case | Handling |
|------|----------|
| Duplicate `X-GitHub-Delivery` | Idempotent ack; nested savepoint on concurrent insert (#19) |
| Crash after DB commit, before Celery enqueue | Delivery row exists; GitHub will not retry — manual replay or future sweep job |
| Webhook for unknown `installation_id` | Log + **200** |
| Installation `removed` / `suspended` | `github_installations.status` on `installation` event |
| Repo removed from installation | `github_repositories.status = removed` on `installation_repositories` |
| Cross-workspace installation ID conflict | Blocked at register (`ConflictError`) |
| Migrations on pooled DB | **AUTOCOMMIT** in `alembic/env.py` (`saas-base-v1.1`) |

---

## Experiment / verification

| Check | Pass |
|-------|------|
| `alembic upgrade head` | Tables through `0016` on PR stack (`0014` review, `0015` reconcile, `0016` publish) |
| [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) Step 1–3 | App created, webhook URL + secret set |
| Manual installation register | Row in `github_installations` |
| R0: smee.io / staging → API | **200**, delivery row, Celery `github_events` |
| R1: `installation_repositories` or sync API | Rows in `github_repositories` |
| R2: `pull_request` `opened` delivery | PR row + revision `1` in `github_pull_requests` |
| R3: index revision + chunk search | Index job `completed`; `search_revision_chunks` returns rows |
| R4: trigger review on indexed revision | `github_review_runs.status=completed`; `github_findings` rows; member list API |
| R5: reconcile after review | `github_finding_groups.state=active`; `GET …/findings/reconciled` |
| R6: publish after reconcile | Check run `revy/review`; `github_publish_jobs.status=completed` |
| R7: UI lists findings | `/reviewer` routes; merge readiness badge; EN+LV strings |

---

## Parking lot

- **R8 execution** — [waves/REVIEW_PIPELINE_R8_EXECUTION.md](./waves/REVIEW_PIPELINE_R8_EXECUTION.md) (autostart + `@revy review` — items below folded into R8-Q#)
- Auto index/review on `push` to default branch (secondary to PR `synchronize`; post-R8)
- **Incremental chunk hash index** on `synchronize` — **R9** (not R8)
- **Evidence snippet on findings** — store retrieved chunk used in R4 prompt; R5 judge grounds claim vs evidence (Perplexity Layer 2–3)
- **Publish–UI parity regression** — contract test: `resolved` groups never in inline publish set (caught by Greptile babysit R6)
- **`GET …/pull-requests/{id}`** — reviewer detail should not scan cursor list pages → **R8-Q6**
- Symbol / call-graph index (defer — embeddings + R5 judge first; see product patterns)
- Precision metrics — dismiss / addressed / resolution rate (post-R7 when dismiss flows exist)
- Generator exploratory + filter conservative — keep R4 broad; tighten in R5 judge, not primary prompt (Perplexity Layer 4)
- Orphan webhook delivery replay / sweep job
- `index_in_progress` guard (mirror R4 `review_in_progress` if concurrent index jobs bite staging)
- Workspace review policy / custom lenses (post-R7 product)
- **Review-complete email notifications** — author digest with summary + merge signal (Greptile sends via GitHub email; Revy defer — see [GREPTILE_PR26_EMAIL](./REVIEW_PIPELINE_GREPTILE_PR26_EMAIL.md))
- **`github_publish_jobs` index on `(workspace_id, revision_id)`** — Greptile P2 on `0016`; **fixed** in `0016` migration
- nginx GitHub IP allowlist
- In-app OAuth install redirect + Setup URL
- `heavy_job` task definition or route removal
- Worker autoscaling per queue
- GitHub App registration automation

---

## References

| Path | Role |
|------|------|
| [REVIEW_PIPELINE_PROGRAM.md](./REVIEW_PIPELINE_PROGRAM.md) | Branching, tags, releases |
| [REVIEW_PIPELINE_MERGE_CHECKLIST.md](./REVIEW_PIPELINE_MERGE_CHECKLIST.md) | Pre-merge babysit + merge gates (R4–R7 stack) |
| [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) | Greptile babysit retrospective + Perplexity → R8 backlog |
| [REVIEW_PIPELINE_GREPTILE_PR26_EMAIL.md](./REVIEW_PIPELINE_GREPTILE_PR26_EMAIL.md) | Archived Greptile PR #26 email + triage vs fixes |
| [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) | Greptile-style patterns → Revy phases (defer/future map) |
| [code-review-arch_perplexity_searcj_advice_only.md](./code-review-arch_perplexity_searcj_advice_only.md) | External architecture notes (advice only) |
| [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md) | P4 installations |
| [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) | App create + minimal config |
| [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) | Full target permissions/events |
| [GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md) | Local webhook dev |
| `backend/app/api/v1/webhooks/stripe.py` | Webhook idempotency pattern |
| `internal-docs/product/revy/docs/WEBHOOKS.md` | Full webhook spec |
