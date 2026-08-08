# PR summary rollup — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [PR_SUMMARY_ROLLUP_FINDINGS.md](./PR_SUMMARY_ROLLUP_FINDINGS.md)

**Status:** **PARTIAL** — PSR #85 merged and deployed (`a4e4ce3`); migration applied on staging; **no post-deploy publish yet** — formatter/rollup sign-off pending post-deploy dogfood PR.

---

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| PSR #85 merge + deploy | `2026-08-08T14:45:07Z` | **PSR sign-off window** — workflow `31262529057`, deploy job finished after merge `a4e4ce3` |
| Pre-deploy feature deploy | `2026-08-08T08:42:10Z` | informational only — workflow `31248927641` (`e0f8d7d`); no new publish on #85 after this boundary |

**Rule:** Use deploy job completion time, not merge time. Merge: `2026-08-08T14:40:25Z`.

**Pre-deploy note:** PR [#85](https://github.com/raimondskrauklis/revy/pull/85) dogfood ran on `feat/pr-summary-rollup` with 13 revisions and 8 completed publishes (latest rev 13 `e0f8d7d`, issue comment `2026-08-08T06:56:26Z`). All publishes ran **before** PSR code was on the staging worker — **excluded** from PSR sign-off (same pattern as PSA #62).

---

## Metrics scripts

```bash
cd backend

# Post-deploy window (PSR sign-off)
DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.revy_review_dogfood_staging_validation \
  --repo raimondskrauklis/revy --pr-number <N> --since 2026-08-08T14:45:07Z --psr-gate --json

# Full PR history (debug / pre-deploy exclusion check)
DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.revy_review_dogfood_staging_validation \
  --repo raimondskrauklis/revy --pr-number <N> --psr-gate --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics \
  --since 2026-08-08T14:45:07Z --json
```

### Probe run — 2026-08-08 (post #85 deploy)

| Probe | Result | Evidence |
|-------|--------|----------|
| Alembic on staging | **PASS** | `2026_08_08_1000_0030_github_pull_request_pr_resolution_rollup` |
| Post-deploy `--since 14:45:07Z` revisions | **0** | dogfood JSON: `revision_count: 0`, `completed_review_runs: 0` |
| Post-deploy completed publishes | **0** | `psr_rollup_gate`: `PSR-R1_rollup_persisted` **PENDING** — `no completed publish jobs yet` |
| Judge metrics post-deploy | **0 jobs** | `judge_json_contract_staging_metrics --since 2026-08-08T14:45:07Z`: no completed publish jobs in window |
| PR #85 full history (pre-deploy) | 8 completed publishes, **no rollup** | rev 5–13; all `pr_resolution_rollup: null` on job `summary_json`; PR row `pr_resolution_rollup: null` |
| PR #85 issue comment (rev 13) | **no lifetime block** | [comment 5225017749](https://github.com/raimondskrauklis/revy/pull/85#issuecomment-5225017749) — pre-deploy formatter; missing `### PR summary (lifetime)` |
| `--psr-gate` (full #85 history) | **FAIL** | `PSR-R1_rollup_persisted`: `completed publish jobs missing pr_resolution_rollup` (pre-deploy publishes) |

---

## Dogfood PR

| PR | Role | Status |
|----|------|--------|
| [#85](https://github.com/raimondskrauklis/revy/pull/85) (merged) | Feature PR — multi-revision dogfood pre-deploy | **excluded** from sign-off |
| *(next)* | Post-deploy PSR dogfood | **not opened** — `chore/psr-staging-dogfood` |

---

## Validation plan (operator)

Follow [staging-validation README](../staging-validation/README.md) SV-Q2 pattern (PSA #63).

1. **Open post-deploy dogfood PR** — branch `chore/psr-staging-dogfood` off `main` (`a4e4ce3`+); minimal `backend/**` touch (probe file or noop comment).
2. **Push 1** — baseline rev 1 after deploy; wait for Revy publish; confirm issue comment has `### PR summary (lifetime)` before G9 / `### This generation`.
3. **Push 2** — second revision; verify lifetime + push delta parity, `review_count >= 2`, `still_open_display` matches block-2 row count.
4. **Push 3** (optional) — cleanup / regrowth; verify check-run one-liners (lifetime + this push).
5. **Run probes** after each publish:
   - `revy_review_dogfood_staging_validation --psr-gate --since 2026-08-08T14:45:07Z`
   - GitHub: issue comment URL + check run output
   - SQL parity: `github_publish_jobs.summary_json.pr_resolution_rollup` ≡ `github_pull_requests.pr_resolution_rollup`
6. **Sign-off** when `--psr-gate` `ready_for_signoff: true` on post-deploy PR.

**Do not** re-trigger Revy on merged #85 for sign-off — merged PR will not get new revisions; use a new chore PR.

---

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| — | PR #85 rev 1–13 (feature branch) | **excluded** — pre-deploy |
| 1 | Baseline rev 1 — PR summary + rollup persist | pending (post-deploy PR) |
| 2 | Rev ≥2 — lifetime + push delta parity | pending |
| 3 | Check-run one-liners + API field | pending |

---

## Pass criteria — push 2

| Check | Pass | Evidence |
|-------|------|----------|
| Issue comment has `### PR summary (lifetime)` before G9 | pending | — |
| `pr_resolution_rollup` on completed publish job `summary_json` | pending | — |
| `github_pull_requests.pr_resolution_rollup` matches job manifest | pending | — |
| `still_open_display` equals block-2 row count | pending | — |
| Dogfood `--psr-gate` green | pending | post-deploy: `PSR-R1` PENDING (no jobs); pre-deploy #85: FAIL |

---

## Pass criteria — push 3

| Check | Pass | Evidence |
|-------|------|----------|
| Check run one-liners (lifetime + this push) | pending | — |
| API `GET publish-job` returns `pr_resolution_rollup` | pending | — |

---

## Results (operator)

| Push | `head_sha` | Notes |
|------|------------|-------|
| — | `e0f8d7d` | PR #85 rev 13 — **excluded**; [comment](https://github.com/raimondskrauklis/revy/pull/85#issuecomment-5225017749); no lifetime block; `pr_resolution_rollup` null on job + PR row |
| 1 | — | pending post-deploy dogfood PR |

**Pre-deploy PR #85 summary (staging DB):** 13 revisions, 8 completed review runs, 23 finding groups (11 resolved). Latest publish rev 13 — no rollup persisted (worker lacked PSR flush at publish time).

---

## Sign-off

| Check | Status | Evidence |
|-------|--------|----------|
| Migration `0030` on staging | **PASS** | alembic `2026_08_08_1000_0030_github_pull_request_pr_resolution_rollup` |
| Post-deploy publish with rollup | **pending** | 0 completed publishes since `2026-08-08T14:45:07Z` |
| `--psr-gate` | **pending** | `ready_for_signoff: false` |
| Staging PASS (formatter + persist) | **pending** | Open `chore/psr-staging-dogfood`; complete pushes 1–2 per validation plan |

**Unit gate (local, not staging):** `test_github_pr_resolution_rollup.py`, `test_github_publish_formatter.py`, `test_revy_review_dogfood_staging_validation.py` — green on merge branch (Revy pass on `e0f8d7d`).

**Note:** SOS P2 orphan-filter fix ([#86](https://github.com/raimondskrauklis/revy/pull/86)) merged separately — document if observed during post-deploy dogfood; does not block PSR code ship.

---

## Doc sync (P3)

| Doc | Change |
|-----|--------|
| `README.md` | Program shipped; link this memo; staging sign-off row stays pending |
| `waves/PR_SUMMARY_ROLLUP_EXECUTION.md` | P0–P3 Done; P3.2 human gate open until sign-off PASS |
| `PR_SUMMARY_ROLLUP_GENERAL_PLAN.md` | Execution index → shipped; staging pending |
