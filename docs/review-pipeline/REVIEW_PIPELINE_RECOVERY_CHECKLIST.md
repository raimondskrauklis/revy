# Review pipeline — recovery checklist

**Purpose:** Agent handoff when context is limited. Work **top to bottom**; mark `[x]` as done.  
**Rules:** No direct pushes to `main`. Audit PRs are **never merged**. One concern per PR. **Peer review = separate agent session** (human-invoked); never self-certified by the writing agent.

**Last updated:** 2026-07-26

---

## Current state (snapshot)

| Item | Value |
|------|--------|
| `main` head | R0–R3 shipped; tags `review-r0-v1` … `review-r3-v1` |
| R4 execution plan | On `main` (`waves/REVIEW_PIPELINE_R4_EXECUTION.md`) |
| R4 code WIP | Git stash `r4-wip-pre-recovery` on branch `feat/review-r4-review-run` — **do not merge until Track 4** |
| Greptile backlog | Audit PRs #15–#18 triaged; fix PRs #19–#21 open |
| Worker deploy | `deploy.yml` still `-Q default,notifications,heavy` |

---

## Track 1 — Doc baseline reset

**Branch:** `chore/review-pipeline-baseline-sync` → PR #12 → merge

- [x] `REVIEW_PIPELINE_FINDINGS.md` — header R0–R3 shipped; next R4; R2/R3 in shipped table; genuinely new R4–R7; catalog R4 execution link; verification through `0013`
- [x] `REVIEW_PIPELINE_PROGRAM.md` — fix model paths (`github_*`); `GITHUB_APP_PRIVATE_KEY_PATH`; remove “to be created”; add recovery checklist link
- [x] `README.md` — recovery table tags include R2/R3
- [x] `REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md` — status “execution ready”
- [x] `waves/REVIEW_PIPELINE_R4_EXECUTION.md` — prerequisites (embeddings + GitHub API); concurrency (`409 review_in_progress`); idempotency_guard; env vars
- [x] `backend/.env.example` — `REVY_LLM_PROVIDER`, model override vars
- [x] Commit + push + open PR #12 + Greptile

---

## Track 2a — Audit PRs (do not merge)

**Audit tip:** Point base/head branches at **feature commits** (not docs-sync tags) — see PRs #15–#18.

| Phase | Branch | Base | Head commit | PR # | Greptile done | Closed |
|-------|--------|------|-------------|------|---------------|--------|
| R0 | `audit/review-r0-retro` | `saas-base-v1.1` (`48c361e`) | `d017dfc` | #15 | [x] | [x] |
| R1 | `audit/review-r1-retro` | `d017dfc` | `fd29fd5` | #16 | [x] | [x] |
| R2 | `audit/review-r2-retro` | `fd29fd5` | `035f304` | #17 | [x] | [x] |
| R3 | `audit/review-r3-retro` | `035f304` | `a299d14` | #18 | [x] | [x] |

**Known P1 (pre-audit):**

- R0: Celery enqueue before DB commit; dedupe race
- R1: `list_installation_repositories` pagination without `raise_for_status`
- R2: `synchronize` appends revision without SHA guard
- R3: chunks deleted before embed success; job stuck on exception

---

## Track 2b — Shipped-code fixes (merge to main)

| # | Branch | Fix | PR # | Merged |
|---|--------|-----|------|--------|
| 1 | `fix/review-r1-github-api-errors` | Use `_request()` in repo list pagination | #13 | [x] |
| 2 | `fix/review-r2-synchronize-dedup` | Skip `_append_revision` when SHA unchanged | #14 | [x] |
| 3 | `fix/review-r0-webhook-commit-order` | Commit before enqueue; dedupe hardening | #19 | [ ] |
| 4 | `fix/review-r3-index-job-safety` | Delete chunks after embed; chunk pagination | #20 | [ ] |
| 5 | `fix/review-r2-concurrent-pr-insert` | IntegrityError retry on concurrent PR insert | #21 | [ ] |

Each: tests + `pipenv run lint` + `babysit-pr` until Greptile clean.

---

## Track 3 — General plan peer-review (R0–R7)

**Manual gate:** human attaches plan files and invokes **`architecture-peer-review`** in a **new agent** session (not the author).

**Skill:** `architecture-peer-review` on each `REVIEW_PIPELINE_R*_GENERAL_PLAN.md` vs `main` code.

- [ ] R0 general plan
- [ ] R1 general plan
- [ ] R2 general plan
- [ ] R3 general plan
- [ ] R4 general plan
- [ ] R5 general plan
- [ ] R6 general plan
- [ ] R7 general plan
- [ ] Docs PR `chore/review-general-plans-sync` (if edits needed)

---

## Track 4 — R4 phase-execution

**Prerequisites:** Track 1 merged; Track 2b #1–#2 merged (required); #3–#5 merged (recommended before R4 staging e2e); **manual** `execution-peer-review` on R4 execution doc (separate agent — [ ]).

**Branch:** `feat/review-r4-review-run` (rebase on `main`)

**Note:** Stashed R4 WIP predates Moonshot-primary docs — on pop, set `revy_llm_provider=moonshot`, Kimi model tier env vars, and drop `moonshot-v1-8k` placeholder.

| Subphase | Scope | Done |
|----------|--------|------|
| R4.1 | Migration `0014`, models, enums, `models/__init__.py` | [ ] |
| R4.2 | `anthropic_review.py`, `moonshot_review.py`, config, unit tests | [ ] |
| R4.3 | `services/github_review.py`, schemas, unit tests | [ ] |
| R4.4 | `workers/review_tasks.py`, celery import | [ ] |
| R4.5 | API routes, audit, route tests, `GITHUB_WEBHOOK_DEV.md` | [ ] |
| Ops | `deploy.yml` worker `-Q github_events,repo_sync,indexing,review,…` + secrets volume | [ ] |

- [ ] Phase gate green (see R4 execution file)
- [ ] PR + Greptile + merge
- [ ] Tag `review-r4-v1`

---

## Locked R4 decisions

| Decision | Value |
|----------|--------|
| Trigger permission | `admin_users` (same as R3 index) |
| Concurrent runs | `409 review_in_progress` if pending/processing exists |
| Prerequisites | Completed index job + `VOYAGE_API_KEY` + `github_api_enabled` + `MOONSHOT_API_KEY` |
| Primary LLM | Moonshot Kimi — `kimi-k2.7-code` (Standard), `kimi-k3` (Deep/Critical) |
| Embeddings | Voyage API first (`voyage-3-lite` shipped); local HF parallel (`architecture.md` §11.3.1) |
| Judge LLM (R5) | Anthropic Claude — cross-family only |
| Worker queues (min) | `github_events,repo_sync,indexing,review` (+ SaaS queues) |

---

## Branch cleanup (after merges)

- [ ] Delete `feat/review-r3-indexing` (merged)
- [ ] Delete `audit/review-r*-retro` branches after close

---

## Agent resume command

```text
Read docs/review-pipeline/REVIEW_PIPELINE_RECOVERY_CHECKLIST.md.
Continue from the first unchecked item in Track 1–4.
Do not push to main directly. One PR per branch.
```
