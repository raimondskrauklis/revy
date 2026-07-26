# Review pipeline — agent checklist

**Purpose:** Single handoff for agents when context is limited. Work **top to bottom** on active tracks; mark `[x]` as done.  
**Rules:** No direct pushes to `main`. One concern per PR. **Peer review = separate agent session** (human-invoked); never self-certified by the implementing agent.

**Last updated:** 2026-07-26 — R8 code on [#31](https://github.com/raimondskrauklis/revy/pull/31); **active: Track F (ops) → merge R8**

---

## Current state (snapshot)

| Item | Value |
|------|--------|
| `main` | R0–R7 shipped; `e413487` (docs #30 on top of #29 `c8bf883`) |
| `feat/review-r8-automation` | R8.1–R8.6 + migration `0018` (`is_draft` guard) — PR [#31](https://github.com/raimondskrauklis/revy/pull/31) |
| Tags | `review-r0-v1` … `review-r3-v1` on `main`; **`review-r4-v1` … `review-r8-v1` pending** after merges |
| Migrations on branch | `0001`–`0018` (`0017` autostart, `0018` `is_draft`) |
| Worker deploy | `deploy.yml` worker `-Q` includes `reconciliation`, `judge`, `github_publish` |
| Next program slice | **Merge R8** → staging e2e → **R9** incremental index (when scoped) |

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

### Track F — Post-merge ops (before R8 dogfood)

- [ ] `alembic upgrade head` on staging/prod (through `0021` for `voyage-code-3` embeddings)
- [ ] Env: `MOONSHOT_API_KEY`, `VOYAGE_API_KEY` (`REVY_EMBEDDING_MODEL=voyage-code-3`, `REVY_EMBEDDING_DIMENSIONS=1024`), `REVY_BOT_LOGIN`; optional `ANTHROPIC_API_KEY` + `REVY_ANTHROPIC_MODEL=claude-sonnet-5`
- [ ] Redeploy or restart worker so droplet runs latest `deploy.yml` `-Q` list:
  `github_events,repo_sync,indexing,review,reconciliation,judge,github_publish,maintenance,default,notifications,heavy`
- [ ] Staging e2e: autostart + `@revy review` + toggle off ([GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md) § R8)
- [ ] Optional: `git tag review-r4-v1` … `review-r7-v1` on `main` (and `review-r8-v1` after #31 merge)

### Track G — R8 automation — [x] code on `feat/review-r8-automation`

- [x] Lock R8 findings: Q11 + R8-Q1–R8-Q7 in [findings](./REVIEW_PIPELINE_FINDINGS.md)
- [x] `create-general-plan` + execution for automation phase
- [x] `execution-peer-review` on R8 execution (2026-07-26)
- [x] `phase-execution` R8.1–R8.6 (migrations `0017`–`0018`, orchestrator, webhooks, UI, docs)
- [ ] Merge PR [#31](https://github.com/raimondskrauklis/revy/pull/31) → `main`; tag `review-r8-v1`; GitHub App subscribe **Issue comments**

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
| Auto-trigger on `opened` / `synchronize` | **R8** (`Q11`) — **next** |
| `@revy review` on-demand command | **R8** — **next** |

**Where “rules” live:** `.cursor/rules/` (agent dev); `REVIEW_PIPELINE_FINDINGS.md` (locks + [domain states](./REVIEW_PIPELINE_FINDINGS.md#domain-states-enums)); `REVIEW_PIPELINE_PRODUCT_PATTERNS.md` (roadmap); future `workspace_review_policy` in DB.

---

## Parking lot (unowned edges)

| Item | Owner / when |
|------|----------------|
| Auto index + review on `pull_request.synchronize` | **R8** — Q11 autostart ([execution](./waves/REVIEW_PIPELINE_R8_EXECUTION.md)) |
| `@revy review` comment command (+ future `@revy <cmd>`) | **R8** |
| `index_in_progress` guard | **R8-Q5** |
| Incremental chunk hash index | **R9** (not R8) |
| Orphan delivery (crash after commit, before enqueue) | Manual replay or future sweep job |
| `REVY_REPOS_ROOT` documented but unused | Indexing uses tarball → `REVY_WORKTREES_ROOT` only |
| Workspace review rules UI | Post-R8; empty state “using workspace default profile” |
| Symbol / call-graph index | Defer — parking lot |
| Precision metrics (dismiss / addressed rate) | Post-R7 when dismiss flows exist |
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
Read docs/review-pipeline/REVIEW_PIPELINE_RECOVERY_CHECKLIST.md (tracks F–G).
Read docs/review-pipeline/REVIEW_PIPELINE_FINDINGS.md for locked Q# + domain states.
Merge or babysit PR #31 (R8); after merge: alembic 0017–0018, staging e2e § R8, tag review-r8-v1.
Do not push to main directly.
```
