# Revy review — cross-repo dogfood staging validation

**Program:** [README.md](./README.md) · **Findings:** [REVY_REVIEW_DOGFOOD_FINDINGS.md](./REVY_REVIEW_DOGFOOD_FINDINGS.md)  
**Case study:** TenderPro [PR #130](https://github.com/raimondskrauklis/tender_pro/pull/130) (super-admin dashboard wave 1)  
**Status:** RR-W1 **R1–R4 shipped** on `deda3c9` (2026-07-31) — **R5 staging RR-V pending** (TenderPro #130 merged; post-deploy dogfood PR required)

---

## Evidence sources (operator)

| Artifact | Location | Notes |
|----------|----------|-------|
| Finding matrix + pass criteria | `misc/SUPER_ADMIN_DASHBOARD_STAGING_VALIDATION.md` | 25 Revy items triaged |
| Worker log | `misc/tenderprolog.txt` | 2026-07-31 15:50–16:04 UTC |
| Program execution | [waves/REVY_REVIEW_DOGFOOD_EXECUTION.md](./waves/REVY_REVIEW_DOGFOOD_EXECUTION.md) | R0–R5 LOOP index |

---

## Deploy boundaries

| Boundary | Value | Used for |
|----------|-------|----------|
| Revy transport #75 | `1c416a0` deployed `2026-07-31T12:18:17Z` | Judge transport baseline |
| TenderPro rev 12 publish | summary `b4ba498` | RR-DG4 / RR-DG5 baseline |
| TenderPro feature tip | `d915b4e` (code) · `999ad17` (doc) | RR-V1 double-push repro |
| RR-W1 R0 lock | 2026-07-31 | RR-Q5=A; RR-DG4 tag below |
| **RR-W1 R1–R4 ship** | `deda3c9` deployed `2026-07-31T19:13:21Z` | [Actions #30657955604](https://github.com/raimondskrauklis/revy/actions/runs/30657955604) — RR-V `--since` window |

---

## Dogfood PR (external)

| PR | Repo | Status |
|----|------|--------|
| [#130](https://github.com/raimondskrauklis/tender_pro/pull/130) | `tender_pro` | **merged** `999ad17` 2026-07-31 — pre-RR-W1 evidence only |
| *(open)* | `tender_pro` or `revy` | **required** for post-`deda3c9` RR-V1–V5 — see § Wave B |

---

## Revy platform log events

| Event | Count | Severity | RR-DG |
|-------|-------|----------|-------|
| `judge_llm_request_started` / `completed` | 1 | OK | RR-DG8 fixed |
| `github_publish_resolve_inline_thread_skipped` | 18 | warning | RR-DG1 |
| `github_publish_inline_comment_skipped` (422) | 1 | warning | RR-DG2 |
| `github_webhook_task_failed` (revision unique) | 1 | **error** | RR-DG3 |
| Resolution rate 0% / compare blocked 6 | summary | warning | RR-DG4 |

---

## Pass criteria (pre-RR-W1)

| Check | Pass | Evidence |
|-------|------|----------|
| Customer app merge-ready | **PASS** | No verified open bugs on `d915b4e`; CI green |
| Revy judge transport | **PASS** | `tenderprolog.txt` L6–8 |
| Revy resolution tracking | **FAIL** | 0% rate; 6 compare blocked |
| Revy publish hygiene | **FAIL** | 18 thread skips; summary SHA lag |
| Revy ingest reliability | **FAIL** | rev 13 IntegrityError |
| Revy finding accuracy | **FAIL** | High false-positive rate (operator matrix) |

---

## Dogfood pushes (operator session)

| Push | `head_sha` | Intent | Revy outcome |
|------|------------|--------|--------------|
| 1 | `e212dfe` → `3bc9627` | Revy fixes round 1 | Rev 4–5 partial |
| 2 | `f1e6325` | Merge `origin/main` | Compare blocked groups |
| 3 | `d915b4e` | Deleted users + Alerts | Inline on `999ad17`; rev 13 DB error |
| 4 | `999ad17` | README sync | Summary stale vs HEAD |

---

## R0.2 — RR-DG4 cohort diagnosis

**RR-DG4 primary tag:** `stale_closure_blocked`

**Rationale (log-based; staging DB query not run):** Rev 12 publish summary (`b4ba498`) reported **Compare blocked: 6** and **0% resolution**, but `misc/tenderprolog.txt` shows GitHub compare **HTTP 200** for the relevant SHA pairs on the same session (`054c094…b4ba498` L10; `b4ba498…d915b4e` L73; `b4ba498…999ad17` L141). That pattern fits groups retaining `closure_blocked_reason=compare_failed` from an **earlier** synchronize (likely merge push `f1e6325`) without clearing on later successful compares — not a sustained compare API outage.

**Secondary contributors (R3 scope):** `pairing_gap` after merge + `RR-DG11` intermediate revision hole from rev-13 `IntegrityError`.

| Evidence source | Observation | Implication |
|-----------------|-------------|-------------|
| Publish summary rev 12 | 6× compare blocked; 0% resolution | Cohort excluded from rate denominator |
| Worker log L10 | Compare 200 for ingest/reconcile | API path healthy at `b4ba498` |
| Worker log L73, L141 | Compare 200 post-fix SHAs | Not `api_compare_failed` as primary |
| Push 2 `f1e6325` | Merge `origin/main` | Likely origin of first `compare_failed` stamp |
| Push 3 rev 13 error | `uq_github_pr_revisions_pr_number` | Pairing gap risk (RR-DG11) |

**R3 subphase map:** R3.1 (always) + R3.2 + R3.3 when R0.2 lists secondary `pairing_gap` / RR-DG11 (current TenderPro memo — implement alongside R3.1 per [R3 execution](./waves/REVY_REVIEW_DOGFOOD_R3_EXECUTION.md) § R3.2); skip R3.5 (`api_compare_failed`).

*Operator:* run SQL in [R0 execution](./waves/REVY_REVIEW_DOGFOOD_R0_EXECUTION.md) § R0.2 against staging DB to replace log inference with row-level evidence when available.

---

## R0.5 — Thread ownership (RR-DG1)

`thread_owner=unknown` — sample: [TenderPro PR #130 files tab](https://github.com/raimondskrauklis/tender_pro/pull/130/files) (18× `github_publish_resolve_inline_thread_skipped` on rev 12 publish; bot vs human not verified in GitHub UI during R0). **R2:** counting-only taxonomy; no ownership filter until operator confirms.

---

## RR-V gates (R0.4 — staging repro)

**Repro protocol:**

1. **RR-V1 same SHA:** force-push or empty amend to same `head_sha` twice within 30s; expect one revision row.
2. **RR-V1 different SHAs:** push `d915b4e` then `999ad17` within 15s (TenderPro rev-13 scenario); expect two rows, no worker `IntegrityError`.
3. **RR-V2 cohort:** after R3 deploy, fix-push on PR #130 with line edits; expect resolution rate **> 0%** in publish summary (`resolution_pass.resolution_rate_pct` > 0 and `compare_failed_count` not stale from pre-R3 sync). Primary RR-DG4 tag: `stale_closure_blocked` — pass requires manifest stamp path, not hygiene-only closes.
4. **RR-V3:** on successful publish, issue comment `head_sha` == check run == inline `commit_id`.
5. **RR-V4:** after R2 deploy, thread resolve skips **0** or manifest breakdown (`thread_id_not_found`, `resolve_mutation_failed`).
6. **RR-V5:** after R4 deploy, matrix items **1, 2, 3, 15, 17** — **0/5** false positives published.

| Gate | Pass (findings authority) | R0 status |
|------|---------------------------|-----------|
| RR-V1 | One revision row per `head_sha`; no IntegrityError; concurrent append unit test | pending (R1) |
| RR-V2 | Resolution rate **> 0%** on fix-push cohort (manifest confirms stamp path) | pending (R3/R5) |
| RR-V3 | Successful publish: summary `head_sha` == revision `head_sha` == inline batch | pending (R1/R5) |
| RR-V4 | Thread resolve skips **0** or manifest skip breakdown | pending (R2/R5) |
| RR-V5 | Matrix items **1, 2, 3, 15, 17** — **0/5** false positives | pending (R4/R5) |

---

## Wave B — post-RR-W1 deploy (`deda3c9`)

**Deploy evidence:** CI + Droplet deploy [success](https://github.com/raimondskrauklis/revy/actions/runs/30657955604) at `2026-07-31T19:13:21Z`.

**Staging DB snapshot** (`--since 2026-07-31T19:08:32Z`):

| Metric | Value | Implication |
|--------|-------|-------------|
| `github_pull_request_revisions` | **0** | No post-deploy dogfood pushes yet |
| `github_publish_jobs` | **0** | RR-V2/V3/V4/V5 not exercisable |
| `review_context.retrieve_manifest.runs` | **0** | No completed review pipeline post-deploy |

**Operator next:** open a live PR on `tender_pro` (RR-V5 matrix) or `revy` (RR-V1–V4 ingest/publish hygiene); run repro protocol § RR-V gates; append push rows below.

| Gate | Post-deploy status | Evidence |
|------|-------------------|----------|
| RR-V1 | **pending** | 0 revisions since deploy |
| RR-V2 | **pending** | Requires fix-push on live PR + publish summary |
| RR-V3 | **pending** | Requires successful publish post-deploy |
| RR-V4 | **pending** | Requires publish with stale inline threads |
| RR-V5 | **pending** | Requires `tender_pro` PR with matrix fixtures (not #130 — merged) |

### RR-Q4 recommendation (R5.2)

**Status:** `locked` · **Recommendation:** **defer enable**

R1–R3 closure-loop code shipped on `deda3c9` (unit-tested; CI green). Do **not** enable product merge gate on 0% resolution rate until **RR-V2 PASS** on post-deploy staging dogfood (`resolution_pass.resolution_rate_pct > 0` on a fix-push cohort with line edits). If RR-V2 passes on next wave, recommend **soft enable** (warn in publish summary) before hard-blocking customer merges.

---

## Sign-off

| Party | Verdict | Date |
|-------|---------|------|
| TenderPro wave 1 | **PASS** | 2026-07-31 |
| Revy cross-repo dogfood (pre-RR-W1) | **FAIL** — drives **RR-W1** | 2026-07-31 |
| RR-W1 R0 baseline | **PASS** (log-based RR-DG4 tag) | 2026-07-31 |
| RR-W1 R1–R4 (code ship) | **PASS** — `deda3c9` CI + Droplet deploy | 2026-07-31 |
| RR-W1 R5 RR-V gates | **pending** — post-deploy dogfood PR required | — |
| RR-Q4 product gate | **defer enable** until RR-V2 PASS | 2026-07-31 |
