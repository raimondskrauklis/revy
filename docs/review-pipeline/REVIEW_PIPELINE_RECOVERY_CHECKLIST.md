# Review pipeline — agent checklist

**Purpose:** Single handoff for agents when context is limited. Work **top to bottom** on active tracks; mark `[x]` as done.  
**Rules:** No direct pushes to `main`. One concern per PR. **Peer review = separate agent session** (human-invoked); never self-certified by the implementing agent.

**Last updated:** 2026-08-10 — pipeline-observability P0 shipped (#92); generation-lifecycle restart fix merged (#89)

---

## Current state (snapshot)

| Item | Value |
|------|--------|
| `main` | R0–R8 + review-quality RQ0–RQ8 shipped |
| Tags | `review-r0-v1` … `review-r3-v1`; optional `review-r4-v1` … `review-r8-v1`; **`review-quality-v1`** after human gate |
| Migrations on `main` | `0001`–`0031` (pipeline-observability P0) |
| Worker deploy | `deploy.yml` worker `-Q` includes `reconciliation`, `judge`, `github_publish`, `maintenance` |
| Next | RQ9 hardening (`docs/agent-work`) → staging `0026` + AS2 e2e → tag `review-quality-v1` |

---

## Architecture peer-review verdict (R0–R7) — [x] done

| Phase | Plan vs code | Notes |
|-------|--------------|-------|
| **R0–R3** | ✅ on `main` | Tags `review-r0-v1` … `review-r3-v1` |
| **R4** | ✅ on `main` (#24) | Moonshot primary; `409 review_in_progress`; actionable findings only |
| **R5** | ✅ on `main` (#29) | R5-Q1–Q3 locked; judge optional without `ANTHROPIC_API_KEY` |
| **R6** | ✅ on `main` (#29) | R6-Q1/Q2; check `revy/review`; idempotent per `head_sha` |
| **R7** | ✅ on `main` (#29) | Flat `/reviewer` routes; merge badge from publish + R6-Q2 |

---

## Active tracks (strict order)

### Track F — Post-merge ops (staging / prod)

- [ ] `alembic upgrade head` on staging/prod (through **`0031`** on `main`)
- [ ] GitHub App: **Install App** on target account → register **installation ID** in Revy (pro plan) — see [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) § App ID vs installation ID
- [ ] PEM: `/mnt/revy_volume/secrets/github-app.pem` readable by container (`chown 1000:deploy`, `chmod 640`); verify with `docker exec -i revy-api python …` in [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) § Verify on droplet (`GET /app: 200`, `token mint: 201`)
- [ ] Env: `MOONSHOT_API_KEY`, `VOYAGE_API_KEY` (`REVY_EMBEDDING_MODEL=voyage-code-3`, `REVY_EMBEDDING_DIMENSIONS=1024`), `REVY_BOT_LOGIN=<slug>[bot]`; optional `ANTHROPIC_API_KEY` + `REVY_ANTHROPIC_MODEL=claude-sonnet-5`
- [ ] Redeploy or restart worker **and Celery beat** so droplet runs latest `deploy.yml` `-Q` list:
  `github_events,repo_sync,indexing,review,reconciliation,judge,github_publish,maintenance,default,notifications,heavy`
- [ ] Staging e2e: autostart + `@revy review` + toggle off ([GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md) § R8)
- [ ] Optional: `git tag review-r4-v1` … `review-r8-v1` on `main`

### Track G — R8 automation — [x] merged (#31)

- [x] Lock R8 findings: Q11 + R8-Q1–R8-Q7 in [findings](./REVIEW_PIPELINE_FINDINGS.md)
- [x] `create-general-plan` + execution for automation phase
- [x] `execution-peer-review` on R8 execution (2026-07-26)
- [x] `phase-execution` R8.1–R8.6 (migrations `0017`–`0018`, orchestrator, webhooks, UI, docs)
- [x] Merge PR [#31](https://github.com/raimondskrauklis/revy/pull/31) → `main`; GitHub App subscribe **Issue comments**
- [ ] Tag `review-r8-v1` (optional)

### Track H — Review quality — **merged** (PR #50)

- [x] Findings + general plans R1–R5 locked — [review-quality/findings](./review-quality/REVIEW_QUALITY_FINDINGS.md)
- [x] Architecture peer review — [REVIEW_QUALITY_PEER_REVIEW.md](./review-quality/REVIEW_QUALITY_PEER_REVIEW.md)
- [x] Execution plan — [REVIEW_QUALITY_EXECUTION.md](./waves/REVIEW_QUALITY_EXECUTION.md)
- [x] `execution-peer-review` (2026-07-27, two passes)
- [x] `phase-execution` RQ0–RQ8 → merged to `main`
- [ ] Human gate S4 + AS2 — [execution](./waves/REVIEW_QUALITY_EXECUTION.md) RQ8 + RQ9
- [ ] Tag `review-quality-v1` on `main`

### Track I — RQ9 hardening — **active** (`docs/agent-work`)

- [ ] G10 `neutral` finalize when PR becomes draft/closed after index (no orphan `in_progress`)
- [ ] Unit test: split `get_db_context` in `index_tasks` (check survives index TX)
- [ ] Expand `.greptile/files.json` + `.cursor/BUGBOT.md` orchestration scope
- [ ] Staging smoke § post–review-quality re-run after deploy
- [ ] Merge `docs/agent-work` → `main` (with doc sync bundle)

### Track J — Generation lifecycle — **shipped** (PR #54 + restart hotfix #89 on `main`)

- [x] P0–P5 LOOP — HEAD gate, supersede, surface flush, coalesce, judge publish gate, trace fields
- [x] Merge PR [#54](https://github.com/raimondskrauklis/revy/pull/54) → `main`
- [x] Merge PR [#89](https://github.com/raimondskrauklis/revy/pull/89) — index-job supersede, resolution Celery task, G9-before-pipeline enqueue, event-anchored coalesce, stale coalesce handoff, Moonshot 520–524 retry (RG-15)
- [ ] Staging dogfood — push during run + `@revy review` restart ([P2 § P2.7](./review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_P2_EXECUTION.md#p27--post-ship-restart-hotfix-pr-89))
- [ ] Optional tag `review-generation-lifecycle-v1` on `main`

### Track L — Judge JSON contract — **merged** (#58) · staging validation in progress

- [x] P0–P5 LOOP merged to `main` (`9a7b5cb`)
- [x] Validation memo + metrics script — [judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](./judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md)
- [ ] Deploy `main` to staging worker
- [ ] Operator dogfood — ≥95% judge outcome persistence on staging PR
- [ ] Sign-off validation memo

### Track M — Review engineering context — **shipped (code)** · human gate pending

- [x] Findings + general plan + P0–P5 execution LOOP (code on PR #60)
- [x] P0–P4 shipped — Moonshot inject, Greptile `files.json` generator, judge locks
- [ ] Staging deploy + dogfood — [REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](./review-engineering-context/REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md)
- [ ] Operator sign-off (P5.2–P5.3, P5.5 narrative)

### Track K — Finding resolution — **code-complete** (PR #57, `feat/finding-resolution`)

- [x] P0–P5 LOOP — closure passes, FR-Q12 metrics, dismiss API, reviewer UI
- [x] Validation memo — [finding-resolution/FINDING_RESOLUTION_STAGING_VALIDATION.md](./finding-resolution/FINDING_RESOLUTION_STAGING_VALIDATION.md)
- [ ] Apply migration **`0028`** on staging
- [ ] Operator dogfood — fix → push → metrics → thread resolve (§ P5.1 table)
- [ ] Merge PR [#57](https://github.com/raimondskrauklis/revy/pull/57) → `main`

### Track L — Publish summary alignment (RG-14 / FR-Q16) — **code-complete**

- [x] Findings + discussion + general plan + P0–P2 execution — [publish-summary-alignment/README.md](./publish-summary-alignment/README.md)
- [x] Architecture peer review — gaps incorporated into P0/P1 execution (2026-07-29)
- [x] `phase-execution` P0–P1 on `feat/publish-summary-alignment`
- [ ] Staging validation — [PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md](./publish-summary-alignment/PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md) (parallel RCX / judge-json pass 2)

### Track N — Pipeline observability — **P0 shipped** · P1 active

- [x] Findings + general plan + architecture peer review (pass 2 BLOCK: no)
- [x] Execution peer review (pass 2 BLOCK: no)
- [x] `phase-execution` P0 → merged [#92](https://github.com/raimondskrauklis/revy/pull/92) (`be16bc7`) — migration `0031`, recorder, commit graph
- [ ] Apply migration **`0031`** on staging (human gate before P1 dogfood)
- [ ] Post-#92 review run on staging — re-run `pipeline_observability_staging_metrics --po-p0-gate` ([memo](./pipeline-observability/PIPELINE_OBSERVABILITY_STAGING_VALIDATION.md))
- [ ] RG-15 push-during-run dogfood — re-run `generation_lifecycle_staging_metrics --rg15-gate` ([memo](./review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_STAGING_VALIDATION.md))
- [ ] `phase-execution` P1 — Moonshot / Anthropic judge / Voyage instrumentation ([P1 execution](./pipeline-observability/waves/PIPELINE_OBSERVABILITY_P1_EXECUTION.md))

---

## Completed tracks (archive)

<details>
<summary>Track E — Merge PR stack (#23–#27) · Track A–D · recovery archive</summary>

### Track E — Merge PR stack — [x] (2026-07-26)

- [x] Babysit code fixes on #23–#27 (Greptile P1 catalog in [learnings](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md))
- [x] [#24](https://github.com/raimondskrauklis/revy/pull/24) R4 → `main`
- [x] [#29](https://github.com/raimondskrauklis/revy/pull/29) R5–R7 stack → `main` (supersedes stacked #25–#27 merge path)
- [x] #23 closed / docs folded via stack; #25–#27 merged indirectly via #29

Historical babysit detail: [REVIEW_PIPELINE_MERGE_CHECKLIST.md](./REVIEW_PIPELINE_MERGE_CHECKLIST.md) (archived).

### Track A — R4 execution peer-review — [x]

- [x] `execution-peer-review` on R4 execution (2026-07-26)
- [x] Gaps applied in execution docs

### Track B — R4 phase-execution — [x] PR #24

- [x] R4.1–R4.5 subphases (migration `0014`, Moonshot, service, worker, API)
- [x] `409 review_in_progress`; index + API key prerequisites
- [x] Phase gate green

### Track C — Before R5 — [x]

- [x] R5-Q1–Q3 locked in findings
- [x] R5 `phase-execution` — shipped via #29

### Track D — Worker queues — [x]

- [x] `deploy.yml` Celery worker `-Q` includes full Revy list (on `main`)

### Recovery archive (complete — do not redo)

- Baseline sync merged (#12)
- Audit PRs #15–#18: Greptile triage only, closed without merge
- Fix PRs: #13–#21 merged; checklist #22

</details>

---

## Revy review QA (process + product roadmap)

**Process:** Borrow proven PR-review practices while building Revy (audit PRs, severity, small PRs, babysit). Optional Greptile on **this repo’s** PRs for extra signal — not required forever.

**Product:** Every useful pattern is mapped in [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) — **shipped**, **defer**, or **future**. No vendor rules files in repo; Revy implements behavior in app + findings registry.

| Practice | Apply while shipping R0–R7 |
|----------|----------------------------|
| Retrospective audit PR | Base = prior phase tag, head = phase commit; **never merge**; triage → fix PRs |
| One concern per fix PR | Keeps review signal high (#13–#21 pattern) |
| Severity tiers P0–P2 | Map to R4 `FindingSeverity`; fix P0/P1 before merge during velocity sprints |
| Small PRs | R4 subphases; &lt;400 LOC where practical |
| Logic vs style | Findings = actionable; lint/style = CI only |
| Babysit open PRs | `/babysit-pr` until external review + CI clean |

**Quick product map (detail in product patterns doc):**

| Capability | Revy home | Status |
|------------|-----------|--------|
| Custom standards / lenses | Workspace review policy | **future** R8+ |
| Strictness profiles | R4 `ReviewProfile` | **shipped** |
| Stable findings across pushes | R5 fingerprints + reconcile | **shipped** |
| Human override | R7 UI; R5 supersede/resolve | **shipped** |
| Merge readiness | R6 check conclusion; R7 badge | **shipped** |
| Idempotent GitHub publish | R6 update in place (R6-Q1) | **shipped** |
| Repo-wide context | R3 embeddings + R4 retrieval | **shipped** |
| Auto-trigger on `opened` / `synchronize` | **R8** — Q11 autostart | **shipped** |
| `@revy review` on-demand command | **R8** | **shipped** |

**Where “rules” live:** `.cursor/rules/` (agent dev); `REVIEW_PIPELINE_FINDINGS.md` (locks + [domain states](./REVIEW_PIPELINE_FINDINGS.md#domain-states-enums)); `REVIEW_PIPELINE_PRODUCT_PATTERNS.md` (roadmap); future `workspace_review_policy` in DB.

---

## Parking lot (unowned edges)

| Item | Owner / when |
|------|----------------|
| Auto index + review on `pull_request.synchronize` | **R8** — shipped |
| `@revy review` comment command (+ future `@revy <cmd>`) | **R8** — shipped |
| `index_in_progress` guard | **R8-Q5** — shipped |
| Incremental chunk hash index | **Review quality** C1 — [execution](./waves/REVIEW_QUALITY_EXECUTION.md) RQ4 |
| Orphan delivery (crash after commit, before enqueue) | Manual replay or future sweep job |
| `REVY_REPOS_ROOT` documented but unused | Indexing uses tarball → `REVY_WORKTREES_ROOT` only |
| Workspace review rules UI | Post-R8; empty state “using workspace default profile” |
| Symbol / call-graph index | Defer v1 — [structural context](./review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |
| Precision metrics (dismiss / addressed rate) | **Review quality** M2 — [execution](./waves/REVIEW_QUALITY_EXECUTION.md) RQ6 (judge + diff heuristic; human dismiss R7.6) |
| Plan-gated review volume | Q9 — after staging cost data |
| nginx GitHub IP allowlist, OAuth install UI, `heavy_job` cleanup | Existing parking lot |

---

## Locked R4–R6 decisions (quick ref)

| Decision | Value |
|----------|--------|
| Trigger permission | `admin_users` |
| Concurrent runs | `409 review_in_progress` |
| Prerequisites | Completed index job + `VOYAGE_API_KEY` + `github_api_enabled` + `MOONSHOT_API_KEY` |
| Primary LLM | Moonshot Kimi — `kimi-k2.7-code` (Standard), `kimi-k3` (Deep/Critical) |
| Finding scope (R4) | Actionable logic/security/behavior — not style/lint |
| Group states (R5) | `active` · `superseded` · `resolved` |
| Check conclusion (R6) | `failure` if active `error`/`critical`; `success` if none; `neutral` for warning/info only |

---

## Agent resume command

```text
Read docs/review-pipeline/REVIEW_PIPELINE_RECOVERY_CHECKLIST.md (Track F ops + Track H human gate).
Read docs/utils/CURSOR_AGENT_WORKFLOW.md for agent roles.
Human gate: staging 0026 + AS2 → tag review-quality-v1. Do not push to main directly.
```
