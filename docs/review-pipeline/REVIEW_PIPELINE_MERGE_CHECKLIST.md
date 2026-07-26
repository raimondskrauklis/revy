# Review pipeline — merge checklist (R4–R7 stack)

**Purpose:** No corners cut between Greptile/CI green and production merge. Work **top to bottom**; do not merge the next PR until the current row is fully `[x]`.

**Stack (strict order):** [#23](https://github.com/raimondskrauklis/revy/pull/23) docs → [#24](https://github.com/raimondskrauklis/revy/pull/24) R4 → [#25](https://github.com/raimondskrauklis/revy/pull/25) R5 → [#26](https://github.com/raimondskrauklis/revy/pull/26) R6 → [#27](https://github.com/raimondskrauklis/revy/pull/27) R7.

**Last updated:** 2026-07-26 — babysit pass in progress; see § Status below.

---

## Status (2026-07-26)

| PR | Babysit fixes pushed | CI | Greptile | Notes |
|----|----------------------|-----|----------|-------|
| **#23** | — | green | 3 open threads (stale vs #27) | **Recommend close** — doc sync landed on [#27](https://github.com/raimondskrauklis/revy/pull/27) |
| **#24** | none needed | green | clean | Ready after #23 decision |
| **#25** | `f05ae6b` inline judge docs | pending re-run | re-review pending | Rebased stack head |
| **#26** | `05b2f72` publish guards + retries | pending re-run | re-review pending | Rebased onto #25 |
| **#27** | `ad3f6ba` UI fixes + full doc sync | pending re-run | re-review pending | Includes `REVIEW_PIPELINE_MERGE_CHECKLIST.md` |

**After each push:** wait for Greptile + resolve threads on GitHub; rebase higher PRs if lower PR changes.

---

## Phase 0 — Before any merge

- [ ] All five PRs open and **MERGEABLE** (no conflict with target base)
- [ ] Doc status sync committed (findings, program, merge checklist) — prefer single docs source on branch about to merge
- [ ] Decide docs path: merge **#23** first *or* fold doc commits into **#24** and close **#23** as duplicate — avoid divergent `docs/review-pipeline/` on `main`

---

## Phase 1 — Babysit (per PR, in stack order)

Complete each PR before moving to the next. After fixing a lower PR, **rebase** all higher PRs onto the updated head.

| PR | Branch | Babysit | CI | Greptile threads | Notes |
|----|--------|---------|-----|------------------|-------|
| **#23** | `chore/review-pipeline-docs-sync` | [ ] | [ ] | [ ] | Docs-only; may be superseded by doc commits on #27 |
| **#24** | `feat/review-r4-review-run` | [ ] | [ ] | [ ] | Base → `main`; migration `0014` |
| **#25** | `feat/review-r5-reconcile-judge` | [ ] | [ ] | [ ] | Base → #24; migration `0015` |
| **#26** | `feat/review-r6-github-publish` | [ ] | [ ] | [ ] | Base → #25; migration `0016` |
| **#27** | `feat/review-r7-reviewer-ui` | [ ] | [ ] | [ ] | Base → #26; frontend only |

### Babysit loop (repeat per PR)

```text
1. gh pr checkout <n>
2. Fetch unresolved Greptile threads (GraphQL reviewThreads, isResolved=false)
3. Fix valid P0/P1; triage P2 (fix or reply with rationale)
4. Backend: pipenv run ruff check . && pipenv run pytest tests/unit/<targeted> -q
5. Frontend: npm run lint && npm test && npm run build
6. Commit + push on feature branch
7. Rebase every higher PR in the stack onto the new head
8. Re-run CI on rebased PRs; re-babysit if new Greptile comments appear
```

### Known Greptile themes (2026-07-26 triage)

| PR | Severity | Topic | Action |
|----|----------|-------|--------|
| #23 | P1 | `external_id` stale in product patterns | Align with R6 execution (`revy:{github_installation_id}:…`) |
| #23 | P2 | PR comment lifecycle per `head_sha` vs PR-scoped | Document in R6 execution + findings |
| #23 | P2 | Execution file path header on R5–R7 | Remove stray line-1 path comment |
| #25 | P2 | `judge_review_run` never enqueued | Document inline judge in reconcile; task reserved for fan-out |
| #26 | P1 | Summary footer counts active vs all groups | Fix `build_summary_markdown` |
| #26 | P1 | Publish enqueued when `github_api_enabled` false | Guard in `enqueue_publish_for_review_run` |
| #26 | P1 | Celery retries swallowed on HTTP errors | Re-raise transient errors from `run_publish_job` |
| #26 | P2 | Inline 422 fails job and blocks retry | Per-comment try/except; don't fail whole publish |
| #27 | P1 | Nav probe returns true with zero PRs | Return false until reconciled API probed |
| #27 | P1 | `pickLatestRevisionId` assumes sort order | Pick by max `updated_at` |
| #27 | P2 | Dead `success` fallback in merge conclusion | Return `failure` for unknown severity |
| #27 | P2 | GitHub link missing when PR not on first page | `usePullRequest` scans cursor pages |

---

## Phase 2 — Merge to `main` (one PR at a time)

After **#23** (or folded docs) and **#24–#27** are babysat:

### Per-PR merge gate

- [ ] All Greptile threads **resolved** or explicitly dismissed with reply
- [ ] `Lint, Type Check, Build, Test` **SUCCESS** on PR head (re-run after rebase)
- [ ] No unresolved merge conflicts with target base
- [ ] Squash/merge commit message references phase (e.g. `feat(review-pipeline): R4 review run`)
- [ ] **Tag on `main`** immediately after merge (see table below)
- [ ] **Rebase** next PR in stack onto updated `main` before merging it

| Merge order | PR | Tag on `main` | Migration |
|-------------|-----|---------------|-----------|
| 1 | #23 (optional if folded) | — | — |
| 2 | #24 | `review-r4-v1` | `0014` |
| 3 | #25 | `review-r5-v1` | `0015` |
| 4 | #26 | `review-r6-v1` | `0016` |
| 5 | #27 | `review-r7-v1` | — |

```bash
git checkout main && git pull
git tag -a review-r4-v1 -m "R4: LLM review run + findings"
git push origin review-r4-v1
# repeat for r5–r7
```

---

## Phase 3 — Post-merge ops (staging / prod)

- [ ] `alembic upgrade head` on worker + API droplets (`0014` → `0016`)
- [ ] Env set: `MOONSHOT_API_KEY`, `VOYAGE_API_KEY`, `REVY_BOT_LOGIN`; optional `ANTHROPIC_API_KEY`
- [ ] Worker `-Q` includes: `github_events,repo_sync,indexing,review,reconciliation,judge,github_publish,maintenance,default,notifications,heavy`
- [ ] GitHub App: **Checks** + **Pull requests** write (R6)
- [ ] Staging e2e per [GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md): index → review → reconcile → publish → `/reviewer`

---

## Phase 4 — Verification matrix

| Step | API / UI | Pass |
|------|----------|------|
| R3 index | `POST …/index` → `index-job` completed | [ ] |
| R4 review | `POST …/review` → `review-run` completed; findings rows | [ ] |
| R5 reconcile | `GET …/findings/reconciled`; groups `active` | [ ] |
| R6 publish | Check `revy/review`; PR comment; inline on error/critical | [ ] |
| R7 UI | `/reviewer` nav; merge badge matches check conclusion | [ ] |
| Idempotent publish | Re-publish same `head_sha` updates in place | [ ] |
| No GitHub App | Reconcile completes; **no** failed publish jobs spam | [ ] |

---

## Anti-patterns (do not)

- Merge the whole stack in one click without per-PR CI on rebased heads
- Skip `alembic upgrade head` before staging smoke test
- Tag before merge commit is on `main`
- Ignore P1 Greptile because “we’ll fix on main”
- Leave #23 and #27 doc sets divergent on `main`

---

## Agent resume

```text
Read docs/review-pipeline/REVIEW_PIPELINE_MERGE_CHECKLIST.md
Babysit PR #23 → #24 → #25 → #26 → #27 in order; rebase stack after each fix
Merge only when Phase 1 row is all [x] for that PR
```
