# Review pipeline — agent checklist

**Purpose:** Single handoff for agents when context is limited. Work **top to bottom** on active tracks; mark `[x]` as done.  
**Rules:** No direct pushes to `main`. One concern per PR. **Peer review = separate agent session** (human-invoked); never self-certified by the implementing agent.

**Last updated:** 2026-07-26 (post-recovery; Track 1–2 + architecture peer-review complete)

---

## Current state (snapshot)

| Item | Value |
|------|--------|
| `main` | R0–R3 shipped; Greptile remediation #13–#21 merged; tags `review-r0-v1` … `review-r3-v1` |
| Planning ladder | Recovered — findings → general plans R0–R7 → R0–R3 execution shipped |
| R4 | Execution plan ready; code WIP on `feat/review-r4-review-run` (stash `r4-wip-pre-recovery`) |
| External PR review | Optional (Greptile on our PRs today) — patterns catalogued in [product patterns](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) |
| Worker deploy | **P0 ops gap:** `deploy.yml` still `-Q default,notifications,heavy` — Revy queues not consumed in staging/prod |

---

## Architecture peer-review verdict (R0–R7) — [x] done

| Phase | Plan vs `main` | Notes |
|-------|----------------|-------|
| **R0** | ✅ aligned | Commit-before-enqueue + nested dedupe on main (#19) |
| **R1** | ✅ aligned | Pagination errors fixed (#13) |
| **R2** | ✅ aligned | SHA dedup (#14), concurrent insert (#21); auto-trigger deferred per Q11 (R2 plan out-scope) |
| **R3** | ✅ aligned | Tarball not shallow clone; chunk list offset/limit intentional; embed-after-delete (#20) |
| **R4** | execution-ready | General plan thin — detail in execution file; config/LLM wiring in R4.1–R4.2 |
| **R5** | needs decisions | R5-Q1–Q3 locked in findings; execution peer-review before R5 `phase-execution` |
| **R6** | partially locked | R6-Q1/Q2 locked; execution draft has check run + publish details |
| **R7** | adequate skeleton | Execution draft exists; can start after R4 API (read-only); badge needs R6 |

**Cross-cutting risks (not architecture mistakes):** worker queue deploy; doc drift (this file + findings); `push` webhook stub unowned; R5 vagueness blocks R6.

---

## Active tracks (strict order)

### Track A — R4 execution peer-review

**Manual gate:** separate agent + `execution-peer-review` on [waves/REVIEW_PIPELINE_R4_EXECUTION.md](./waves/REVIEW_PIPELINE_R4_EXECUTION.md).

- [x] `execution-peer-review` complete (2026-07-26) — gaps applied in execution docs
- [ ] Docs PR for execution peer-review fixes (this batch)

### Track B — R4 phase-execution

**Prerequisites:** Track A done; `main` includes all Track 2b fixes (#19–#21).

**Branch:** `feat/review-r4-review-run` — rebase on `main`, pop stash `r4-wip-pre-recovery`, align Moonshot env (`revy_llm_provider=moonshot`, Kimi tier vars; drop `moonshot-v1-8k` placeholder).

| Subphase | Scope | Done |
|----------|--------|------|
| R4.1 | Migration `0014`, models, enums, `models/__init__.py` | [ ] |
| R4.2 | `moonshot_review.py`, judge adapter stub only (`anthropic_review.py` — no R5 logic), `config.py` LLM wiring, unit tests | [ ] |
| R4.3 | `services/github_review.py`, schemas, unit tests; **actionable findings only** (logic/security/behavior — not style/lint) | [ ] |
| R4.4 | `workers/review_tasks.py`, celery import | [ ] |
| R4.5 | API routes, audit on review trigger, route tests | [ ] |
| Ops | `deploy.yml` worker `-Q github_events,repo_sync,indexing,review,maintenance,default,notifications,heavy` + secrets | [ ] |

**R4 implementation guards:**

- [ ] `409 review_in_progress` for concurrent runs on same revision
- [ ] Prerequisites: completed index job + `VOYAGE_API_KEY` + `github_api_enabled` + `MOONSHOT_API_KEY`
- [ ] Consider token/cost ceiling in R4.3 (max chunks × max tokens) — document in findings if deferred
- [ ] Phase gate green → PR → external review clean → merge → tag `review-r4-v1`

### Track C — Before R5 phase-execution

**Prerequisites:** R4 shipped (`review-r4-v1`); R5-Q1–Q3 **locked** in [findings](./REVIEW_PIPELINE_FINDINGS.md); [R5 execution](./waves/REVIEW_PIPELINE_R5_EXECUTION.md) peer-reviewed.

- [x] Lock R5-Q1 fingerprint algorithm in findings
- [x] Lock R5-Q2 reconciliation schema + API in findings
- [x] Lock R5-Q3 judge trigger policy in findings
- [ ] `execution-peer-review` on R5 execution (separate agent) — after R4 ships

### Track D — Worker queues (ops)

Can ship with R4 Ops subphase or as immediate follow-up PR — **required before staging e2e**.

- [ ] `.github/workflows/deploy.yml` Celery worker `-Q` includes `github_events,repo_sync,indexing,review,maintenance` (SaaS export jobs use `maintenance`)
- [ ] Documented in deploy supplement / env examples

---

## Revy review QA (process + product roadmap)

**Process:** Borrow proven PR-review practices while building Revy (audit PRs, severity, small PRs, babysit). Optional Greptile on **this repo’s** PRs for extra signal — not required forever.

**Product:** Every useful pattern is mapped in [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) — **shipped**, **R4–R7**, **defer**, or **future**. No vendor rules files in repo; Revy implements behavior in app + findings registry.

| Practice | Apply while shipping R0–R7 |
|----------|----------------------------|
| Retrospective audit PR | Base = prior phase tag, head = phase commit; **never merge**; triage → fix PRs |
| One concern per fix PR | Keeps review signal high (#13–#21 pattern) |
| Severity tiers P0–P2 | Map to R4 `FindingSeverity`; fix P0/P1 before merge during velocity sprints |
| Small PRs | R4 subphases; &lt;400 LOC where practical |
| Logic vs style | Findings = actionable; lint/style = CI only |
| Babysit open PRs | `/babysit-pr` until external review + CI clean |

**Quick product map (detail in product patterns doc):**

| Capability | Revy home |
|------------|-----------|
| Custom standards / lenses | Workspace review policy (**future** R8+) |
| Strictness profiles | R4 `ReviewProfile` |
| Stable findings across pushes | R5 fingerprints + reconcile |
| Human override | R7 dismiss/acknowledge; R5 supersede/resolve |
| Merge readiness | R6 check conclusion; R7 badge |
| Idempotent GitHub publish | R6 update in place (R6-Q1) |
| Repo-wide context | R3 embeddings + R4 lenses |
| Auto-trigger on push/synchronize | **defer** R8 (`Q11`) |

**Where “rules” live:** `.cursor/rules/` (agent dev); `REVIEW_PIPELINE_FINDINGS.md` (locks); `REVIEW_PIPELINE_PRODUCT_PATTERNS.md` (roadmap); future `workspace_review_policy` in DB.

---

## Parking lot (unowned edges)

| Item | Owner / when |
|------|----------------|
| Auto index + review on `pull_request.synchronize` / `push` | **Defer R8 / automation** — R3/R4 manual admin trigger until pipeline stable (Q11) |
| `push` handler stub | Same as above; target config lists push for future re-index |
| Orphan delivery (crash after commit, before enqueue) | Edge case — manual replay or future delivery sweep job |
| Concurrent index jobs per revision | No `index_in_progress` guard yet; mirror R4 pattern if needed before staging |
| `REVY_REPOS_ROOT` documented but unused | Indexing uses tarball → `REVY_WORKTREES_ROOT` only |
| `record_audit` on index trigger | R4 audits review trigger only for now |
| Workspace review rules UI | Post-R7; empty state “using workspace default profile” |
| Symbol / call-graph index | Defer — ship retrieval + R5 judge first; add only if staging misses cross-file bugs |
| Precision metrics (dismiss / addressed rate) | Post-R7 when dismiss flows exist |
| Plan-gated review volume | Q9 — after R4 cost data |
| nginx GitHub IP allowlist, OAuth install UI, `heavy_job` cleanup | Existing parking lot |

---

## Locked R4 decisions (quick ref)

| Decision | Value |
|----------|--------|
| Trigger permission | `admin_users` |
| Concurrent runs | `409 review_in_progress` |
| Prerequisites | Completed index job + `VOYAGE_API_KEY` + `github_api_enabled` + `MOONSHOT_API_KEY` |
| Primary LLM | Moonshot Kimi — `kimi-k2.7-code` (Standard), `kimi-k3` (Deep/Critical) |
| Embeddings | Voyage API first (`voyage-3-lite`); local HF parallel per `architecture.md` §11.3.1 |
| Judge LLM (R5) | Anthropic Claude — cross-family only |
| Finding scope (R4) | Actionable logic/security/behavior — not style/lint (CI handles style) |

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
Read docs/review-pipeline/REVIEW_PIPELINE_RECOVERY_CHECKLIST.md (tracks A–D).
Read docs/review-pipeline/REVIEW_PIPELINE_FINDINGS.md for locked Q# decisions.
Read docs/review-pipeline/REVIEW_PIPELINE_PRODUCT_PATTERNS.md for defer/future rationale.
Do not push to main directly. One PR per branch.
```
