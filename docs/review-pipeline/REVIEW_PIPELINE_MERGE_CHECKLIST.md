# Review pipeline — merge checklist (R4–R7 stack)

**Status:** **Archived** — stack landed on `main` via [#24](https://github.com/raimondskrauklis/revy/pull/24) (R4) and [#29](https://github.com/raimondskrauklis/revy/pull/29) (R5–R7). For current work see [REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](./REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) (Track F ops → Track G R8).

**Purpose:** Historical record of Greptile babysit + merge gates for the R4–R7 stacked PRs. Do not use for new work.

**Stack (historical):** [#23](https://github.com/raimondskrauklis/revy/pull/23) docs → [#24](https://github.com/raimondskrauklis/revy/pull/24) R4 → stacked #25–#27 → consolidated [#29](https://github.com/raimondskrauklis/revy/pull/29).

**Learnings:** [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md)

**Last updated:** 2026-07-26 — merged via #29; checklist archived.

---

## Status (2026-07-26)

| PR | Babysit code fixes | CI | Greptile threads | Notes |
|----|-------------------|-----|------------------|-------|
| **#23** | done (`d044a46`) | green | resolve on GitHub | **Recommend close** — doc sync on [#27](https://github.com/raimondskrauklis/revy/pull/27) |
| **#24** | none needed | green | clean | Ready to merge after docs decision |
| **#25** | done (`c66d219` + judge docs) | re-run after rebase | re-review | Supersede + judge exception fixes |
| **#26** | done (`60ece23` head) | re-run after rebase | re-review | Publish idempotency, guards, inline active-only |
| **#27** | done (`8cfeb19` head) | re-run after rebase | re-review | UI probe + doc sync + merge checklist |

**After each push:** wait for Greptile → resolve threads on GitHub → rebase higher PRs if lower PR changes.

---

## Phase 0 — Before any merge

- [x] Babysit code fixes applied on #23–#27 (see [learnings catalog](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md#fixed-issues-catalog-babysit-pass-2026-07-26))
- [ ] All five PRs **MERGEABLE** (rebase stack onto latest bases)
- [ ] Docs path decided: **close #23** and merge docs via #27 (recommended) — avoid duplicate `docs/review-pipeline/` on `main`
- [ ] Greptile threads **resolved** on GitHub for each PR head

---

## Phase 1 — Babysit (per PR)

| PR | Branch | Code | CI | Greptile resolved | Notes |
|----|--------|------|-----|-------------------|-------|
| **#23** | `chore/review-pipeline-docs-sync` | [x] | [ ] | [ ] | Close if folding into #27 |
| **#24** | `feat/review-r4-review-run` | [x] | [ ] | [ ] | `0014` |
| **#25** | `feat/review-r5-reconcile-judge` | [x] | [ ] | [ ] | `0015` |
| **#26** | `feat/review-r6-github-publish` | [x] | [ ] | [ ] | `0016` |
| **#27** | `feat/review-r7-reviewer-ui` | [x] | [ ] | [ ] | Frontend |

### Babysit loop (for future PRs)

```text
1. gh pr checkout <n>
2. Fetch unresolved Greptile threads (GraphQL reviewThreads)
3. Fix valid P0/P1 — see learnings doc for signal quality heuristics
4. Backend: pipenv run ruff check . && pipenv run pytest tests/unit/<targeted> -q
5. Frontend: npm run lint && npm test && npm run build
6. Commit + push; rebase stack; resolve threads on GitHub
```

---

## Phase 2 — Merge to `main` (one PR at a time)

| Merge order | PR | Tag on `main` | Migration |
|-------------|-----|---------------|-----------|
| 1 | #23 (skip if closed) | — | — |
| 2 | #24 | `review-r4-v1` | `0014` |
| 3 | #25 | `review-r5-v1` | `0015` |
| 4 | #26 | `review-r6-v1` | `0016` |
| 5 | #27 | `review-r7-v1` | — |

Per-PR gate: Greptile resolved + CI green + rebase onto previous merge + tag.

---

## Phase 3 — Post-merge ops

- [ ] `alembic upgrade head` (`0014`–`0016`)
- [ ] Env: `MOONSHOT_API_KEY`, `VOYAGE_API_KEY` (`REVY_EMBEDDING_MODEL=voyage-code-3`, `REVY_EMBEDDING_DIMENSIONS=1024`), `REVY_BOT_LOGIN`; optional `ANTHROPIC_API_KEY` + `REVY_ANTHROPIC_MODEL=claude-sonnet-5`
- [ ] Worker `-Q`: `github_events,repo_sync,indexing,review,reconciliation,judge,github_publish,maintenance,default,notifications,heavy`
- [ ] Staging e2e (Phase 4 matrix)

---

## Phase 4 — Verification matrix

| Step | Pass |
|------|------|
| R3 index → completed | [ ] |
| R4 review → findings | [ ] |
| R5 reconcile → active groups | [ ] |
| R6 publish → check `revy/review`; no inline for dismissed | [ ] |
| R7 `/reviewer` + merge badge | [ ] |
| Re-publish same `head_sha` idempotent | [ ] |
| No GitHub App → no publish job spam | [ ] |

---

## Agent resume

```text
Read REVIEW_PIPELINE_MERGE_CHECKLIST.md + REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md
Merge #24→#27 (close #23); resolve Greptile threads; staging e2e
```
