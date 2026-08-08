# PR summary rollup — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [PR_SUMMARY_ROLLUP_FINDINGS.md](./PR_SUMMARY_ROLLUP_FINDINGS.md)

**Status:** **PASS** — post-deploy dogfood complete on [#87](https://github.com/raimondskrauklis/revy/pull/87) (pushes 1–2); `--psr-gate` green; lifetime block + rollup persist verified on staging.

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
  --repo raimondskrauklis/revy --pr-number 87 --since 2026-08-08T14:45:07Z --psr-gate --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics \
  --since 2026-08-08T14:45:07Z --json
```

### Probe run — 2026-08-08 (pre-dogfood, #85 only)

| Probe | Result | Evidence |
|-------|--------|----------|
| Alembic on staging | **PASS** | `2026_08_08_1000_0030_github_pull_request_pr_resolution_rollup` |
| Post-deploy window before #87 | **0 publishes** | expected — no dogfood PR yet |
| PR #85 full history | **excluded** | 8 pre-deploy publishes; no `pr_resolution_rollup`; [comment](https://github.com/raimondskrauklis/revy/pull/85#issuecomment-5225017749) missing lifetime block |

### Probe run — 2026-08-08 (post-dogfood #87)

| Probe | Result | Evidence |
|-------|--------|----------|
| Post-deploy revisions | **2** | PR #87 rev 1–2 since `14:45:07Z` |
| `--psr-gate` | **PASS** | `ready_for_signoff: true`; `PSR-R2` schema v1; `PSR-R3 review_count=2`; `PSR-R4 still_open_display=1` |
| PR row ≡ job rollup | **PASS** | `pr_resolution_rollup.review_count=2` on both; `PR row matches job: True` |
| Issue comment lifetime block | **PASS** | [comment 5226701333](https://github.com/raimondskrauklis/revy/pull/87#issuecomment-5226701333) updated `2026-08-08T15:14:15Z`; `### PR summary (lifetime)` before push metrics |
| `still_open_display` parity | **PASS** | rollup `still_open_display=1`; block 2 has 1 row (rev 2) |
| Check run one-liners | **PASS** | head `1d6c149`: `PR (lifetime): 1 resolved / 2 raised; 1 still open` + `This push: 1 issue fixed since last push` |

---

## Dogfood PR

| PR | Role | Status |
|----|------|--------|
| [#85](https://github.com/raimondskrauklis/revy/pull/85) (merged) | Feature PR — pre-deploy dogfood | **excluded** |
| [#87](https://github.com/raimondskrauklis/revy/pull/87) | Post-deploy PSR dogfood | **sign-off complete** — `chore/psr-staging-dogfood` |

**Fixture:** `backend/tests/fixtures/psr_staging/probe_module.py`

---

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| — | PR #85 rev 1–13 | **excluded** — pre-deploy |
| 1 | Baseline rev 1 — PR summary + rollup persist | **done** `4837aac` |
| 2 | Rev ≥2 — lifetime + push delta parity | **done** `1d6c149` |
| 3 | Check-run one-liners + API field | **done** on push 2 (one-liners); API via unit test |

---

## Pass criteria — push 2

| Check | Pass | Evidence |
|-------|------|----------|
| Issue comment has `### PR summary (lifetime)` before G9 | **yes** | [comment 5226701333](https://github.com/raimondskrauklis/revy/pull/87#issuecomment-5226701333) — lifetime block before `### Resolution metrics (this push)` |
| `pr_resolution_rollup` on completed publish job `summary_json` | **yes** | rev 2 job: `review_count=2`, `raised_count=2`, `resolved_count=1`, `schema_version=1` |
| `github_pull_requests.pr_resolution_rollup` matches job manifest | **yes** | PR row `1d6c149` — `PR row matches job: True` |
| `still_open_display` equals block-2 row count | **yes** | `still_open_display=1`; 1 row in `### Still open on PR` |
| Dogfood `--psr-gate` green | **yes** | `ready_for_signoff: true` after rev 2 |

---

## Pass criteria — push 3

| Check | Pass | Evidence |
|-------|------|----------|
| Check run one-liners (lifetime + this push) | **yes** | Revy check on `1d6c149`: lifetime + this-push lines in `output.summary` |
| API `GET publish-job` returns `pr_resolution_rollup` | **yes** | `test_github_publish_job_response_includes_pr_resolution_rollup` (PSR-Q8); job JSON on staging has field |

---

## Results (operator)

| Push | `head_sha` | `review_count` | `still_open_display` | Notes |
|------|------------|----------------|----------------------|-------|
| — | `e0f8d7d` | — | — | PR #85 rev 13 — **excluded** (pre-deploy) |
| 1 | `4837aac` | 1 | 2 | rev 1; 2 findings raised; [comment](https://github.com/raimondskrauklis/revy/pull/87#issuecomment-5226701333) first publish `15:11:09Z` |
| 2 | `1d6c149` | 2 | 1 | rev 2; 1 addressed; comment updated `15:14:15Z`; push delta + lifetime rate 50% |

**Rev 2 rollup snapshot:** `raised_count=2`, `resolved_count=1`, `still_open_display=1`, `still_open_prior=0`, `lifetime_resolution_rate_pct=50.0`.

---

## Sign-off

| Check | Status | Evidence |
|-------|--------|----------|
| Migration `0030` on staging | **PASS** | alembic `2026_08_08_1000_0030_github_pull_request_pr_resolution_rollup` |
| Post-deploy publish with rollup | **PASS** | PR #87 rev 1–2 completed publishes since `2026-08-08T14:45:07Z` |
| `--psr-gate` | **PASS** | `ready_for_signoff: true` (rev 2) |
| Staging PASS (formatter + persist) | **PASS** | [#87](https://github.com/raimondskrauklis/revy/pull/87) pushes 1–2; lifetime block + PR row parity |

**Operator sign-off (PSR):** PR lifetime rollup + push delta surfaces **PASS** on post-deploy worker. Program P3.2 human gate cleared.

---

## Doc sync (P3)

| Doc | Change |
|-----|--------|
| `README.md` | Status → shipped + staging PASS |
| `waves/PR_SUMMARY_ROLLUP_EXECUTION.md` | P3.2 sign-off PASS |
| `PR_SUMMARY_ROLLUP_GENERAL_PLAN.md` | Execution index → shipped |
