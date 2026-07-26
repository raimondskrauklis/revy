# Review pipeline — agent checklist

**Purpose:** Single handoff for agents when context is limited. Work **top to bottom** on active tracks; mark `[x]` as done.  
**Rules:** No direct pushes to `main`. One concern per PR. **Peer review = separate agent session** (human-invoked); never self-certified by the implementing agent.

**Last updated:** 2026-07-26 (R4–R7 `phase-execution` complete; merge stack open)

---

## Current state (snapshot)

| Item | Value |
|------|--------|
| `main` | R0–R3 shipped; tags `review-r0-v1` … `review-r3-v1`; Greptile remediation #13–#21 merged |
| R4–R7 code | Implemented on stacked PRs [#24](https://github.com/raimondskrauklis/revy/pull/24) → [#27](https://github.com/raimondskrauklis/revy/pull/27) |
| Docs | [#23](https://github.com/raimondskrauklis/revy/pull/23) (`chore/review-pipeline-docs-sync`) + status sync on feature branches |
| Migrations | `0014` (review), `0015` (reconcile), `0016` (publish) — on PR stack, not on `main` yet |
| Worker deploy | `deploy.yml` includes full `-Q` list on PR #24+ |
| Tags pending | `review-r4-v1` … `review-r7-v1` after merge |

---

## Architecture peer-review verdict (R0–R7) — [x] done

| Phase | Plan vs code | Notes |
|-------|--------------|-------|
| **R0–R3** | ✅ on `main` | See recovery archive |
| **R4** | ✅ implemented (#24) | Moonshot primary; `409 review_in_progress`; actionable findings only |
| **R5** | ✅ implemented (#25) | R5-Q1–Q3 locked; judge optional without `ANTHROPIC_API_KEY` |
| **R6** | ✅ implemented (#26) | R6-Q1/Q2; check `revy/review`; idempotent per `head_sha` |
| **R7** | ✅ implemented (#27) | Flat `/reviewer` routes; merge badge from publish + R6-Q2 |

---

## Active tracks (strict order)

### Track E — Merge PR stack

**Prerequisites:** [merge checklist](./REVIEW_PIPELINE_MERGE_CHECKLIST.md) Phase 1 complete (babysit #23–#27). Babysit **code fixes** done — see [learnings](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md).

- [x] Babysit code fixes on #23–#27 (Greptile P1 catalog in learnings doc)
- [ ] Greptile threads resolved + CI green on each PR in stack order
- [ ] Merge [#23](https://github.com/raimondskrauklis/revy/pull/23) docs (or fold into #24; close duplicate)
- [ ] Merge [#24](https://github.com/raimondskrauklis/revy/pull/24) R4 → tag `review-r4-v1`
- [ ] Rebase #25 onto `main`; merge → tag `review-r5-v1`
- [ ] Rebase #26 onto `main`; merge → tag `review-r6-v1`
- [ ] Rebase #27 onto `main`; merge → tag `review-r7-v1`

### Track F — Post-merge ops

- [ ] `alembic upgrade head` on staging/prod (`0014`–`0016`)
- [ ] Env: `MOONSHOT_API_KEY`, `VOYAGE_API_KEY`, `REVY_BOT_LOGIN`; optional `ANTHROPIC_API_KEY`
- [ ] Worker droplet consumes: `github_events,repo_sync,indexing,review,reconciliation,judge,github_publish,maintenance,default,notifications,heavy`
- [ ] Staging e2e: index → review → reconcile → publish → `/reviewer` UI ([GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md))

### Track G — R8 automation (next program slice)

**Defer until R4–R7 on `main` and dogfooded.**

**Product goal:** Greptile/Bugbot parity — **autostart** on PR open + push by default; optional **`@revy review`** on-demand re-run; workspace toggle for manual-only (today’s behavior).

- [x] Lock R8 findings: Q11 + R8-Q1–R8-Q7 in [findings](./REVIEW_PIPELINE_FINDINGS.md)
- [x] `create-general-plan` + execution for automation phase
- [x] `execution-peer-review` on R8 execution (2026-07-26 — gaps applied in execution doc)
- [ ] `phase-execution` on `feat/review-r8-automation` after R7 on `main`

---

## Completed tracks (archive)

<details>
<summary>Track A — R4 execution peer-review · Track B — R4 phase-execution · Track C — R5 locks · Track D — worker queues</summary>

### Track A — R4 execution peer-review — [x]

- [x] `execution-peer-review` on R4 execution (2026-07-26)
- [x] Gaps applied in execution docs

### Track B — R4 phase-execution — [x] PR #24

- [x] R4.1–R4.5 subphases (migration `0014`, Moonshot, service, worker, API)
- [x] `409 review_in_progress`; index + API key prerequisites
- [x] Phase gate green

### Track C — Before R5 — [x]

- [x] R5-Q1–Q3 locked in findings
- [x] R5 `phase-execution` — PR #25

### Track D — Worker queues — [x] (in PR #24)

- [x] `deploy.yml` Celery worker `-Q` includes full Revy list

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
| Strictness profiles | R4 `ReviewProfile` | **shipped** (#24) |
| Stable findings across pushes | R5 fingerprints + reconcile | **shipped** (#25) |
| Human override | R7 UI; R5 supersede/resolve | **shipped** (#25/#27) |
| Merge readiness | R6 check conclusion; R7 badge | **shipped** (#26/#27) |
| Idempotent GitHub publish | R6 update in place (R6-Q1) | **shipped** (#26) |
| Repo-wide context | R3 embeddings + R4 retrieval | **shipped** |
| Auto-trigger on push/synchronize | **defer** R8 (`Q11`) — **autostart** default |
| `@revy review` on-demand command | **defer** R8 |

**Where “rules” live:** `.cursor/rules/` (agent dev); `REVIEW_PIPELINE_FINDINGS.md` (locks + [domain states](./REVIEW_PIPELINE_FINDINGS.md#domain-states-enums)); `REVIEW_PIPELINE_PRODUCT_PATTERNS.md` (roadmap); future `workspace_review_policy` in DB.

---

## Parking lot (unowned edges)

| Item | Owner / when |
|------|----------------|
| Auto index + review on `pull_request.synchronize` / `push` | **R8** — Q11 autostart ([execution](./waves/REVIEW_PIPELINE_R8_EXECUTION.md)) |
| `@revy review` comment command (+ future `@revy <cmd>`) | **R8** |
| `index_in_progress` guard | **R8-Q5** |
| Incremental chunk hash index | **R9** (not R8) |
| Orphan delivery (crash after commit, before enqueue) | Manual replay or future sweep job |
| `REVY_REPOS_ROOT` documented but unused | Indexing uses tarball → `REVY_WORKTREES_ROOT` only |
| Workspace review rules UI | Post-R7; empty state “using workspace default profile” |
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

## Recovery archive (complete — do not redo)

<details>
<summary>Track 1 — doc baseline (#12) · Track 2a audit PRs #15–#18 closed · Track 2b fixes #13–#21 merged</summary>

- Baseline sync merged (#12)
- Audit PRs #15–#18: Greptile triage only, closed without merge
- Fix PRs: #13 GitHub API errors, #14 synchronize SHA dedup, #19 webhook commit order, #20 index safety, #21 concurrent PR insert, #22 checklist

</details>

---

## Agent resume command

```text
Read docs/review-pipeline/REVIEW_PIPELINE_RECOVERY_CHECKLIST.md (tracks E–G).
Read docs/review-pipeline/REVIEW_PIPELINE_FINDINGS.md for locked Q# + domain states.
Read docs/review-pipeline/REVIEW_PIPELINE_PRODUCT_PATTERNS.md for defer/future rationale.
Do not push to main directly. Merge stack #23→#24→#25→#26→#27; tag after each merge.
```
