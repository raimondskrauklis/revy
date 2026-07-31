# Revy review — cross-repo dogfood staging validation

**Program:** [README.md](./README.md) · **Findings:** [REVY_REVIEW_DOGFOOD_FINDINGS.md](./REVY_REVIEW_DOGFOOD_FINDINGS.md)  
**Case study (evidence source):** TenderPro [PR #130](https://github.com/raimondskrauklis/tender_pro/pull/130) — real-repo symptoms that motivated RR-W1; **not** the validation venue.  
**Validation venue:** `raimondskrauklis/revy` staging dogfood — [#78](https://github.com/raimondskrauklis/revy/pull/78) (RR-W1 ship) · [#79](https://github.com/raimondskrauklis/revy/pull/79) (R5 sign-off)  
**Status:** RR-W1 **shipped** `deda3c9` — **R5 RR-V PASS** on Revy repo staging (2026-07-31)

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

## Dogfood PRs (validation venue — `raimondskrauklis/revy`)

| PR | Role | Status |
|----|------|--------|
| [#78](https://github.com/raimondskrauklis/revy/pull/78) | RR-W1 implementation + staging dogfood (R1–R4) | **merged** `deda3c9` |
| [#79](https://github.com/raimondskrauklis/revy/pull/79) | R5 sign-off doc sync | open `e10729a` — Revy rev 1 **PASS** (info only) |

**External evidence only:** [TenderPro #130](https://github.com/raimondskrauklis/tender_pro/pull/130) (merged) — symptom catalog + operator matrix in `misc/`; not used for RR-V sign-off.

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

## RR-V gates — Revy repo staging sign-off

**Venue:** `raimondskrauklis/revy` PR #78 (9 revisions, post-`deda3c9` merge) + PR #79 rev 1.

| Gate | Status | Evidence |
|------|--------|----------|
| **RR-V1** | **PASS** | Staging DB: PR #78 revisions 1–9 — one row per `head_sha` (`sha_rows=1` each); no `IntegrityError` in worker logs; unit tests `test_github_pull_requests.py` concurrent append |
| **RR-V2** | **PASS** | Reconcile manifest PR #78 rev 5: `resolution_rate_pct=100`, `compare_failed_count=0`; rev 4 `75%`; rev 8 `25%` — stamp path active |
| **RR-V3** | **PASS** | Staging DB: all completed `github_publish_jobs` on PR #78/79 — `pub_head_sha` == revision `head_sha` |
| **RR-V4** | **PASS** | PR #79 publish `summary_json.thread_resolve_skipped`: all counters **0** |
| **RR-V5** | **PASS** | Unit matrix fixtures: `pytest tests/unit/test_github_finding_head_suppression.py` **15 passed** (rows 1, 2, 3, 15, 17 + negative cases) |

### Dogfood pushes (Revy PR #78 — staging)

| Rev | `head_sha` | Revy outcome |
|-----|------------|--------------|
| 1 | `f799dbe` | review + publish completed |
| 4 | `073bee82` | `resolution_rate_pct=75%` |
| 5 | `543fb9e` | `resolution_rate_pct=100%` |
| 7–8 | `8f6a238` / `1d0fb1b` | publish completed; rev 8 `resolution_rate_pct=25%` |
| 9 | `55649d9` | Moonshot truncated (mega-diff) — infra, not closure-loop |
| merge | `deda3c9` | RR-W1 shipped to `main` |

---

## Wave B — post-RR-W1 deploy deda3c9

**Deploy evidence:** CI + Droplet deploy [success](https://github.com/raimondskrauklis/revy/actions/runs/30657955604) at `2026-07-31T19:13:21Z`.

**Post-deploy dogfood:** PR #79 rev 1 (`e10729a`) — review + publish completed; Revy rev 1 confidence **5/5** (info only).

### RR-Q4 recommendation (R5.2)

**Status:** `locked` · **Recommendation:** **soft enable**

RR-V2 **PASS** on Revy PR #78 (`resolution_rate_pct > 0`, `compare_failed_count=0`). Recommend **soft enable**: surface resolution rate in publish summary as operator signal; defer **hard block** on customer-repo merges until a second external-repo cohort confirms (TenderPro was evidence-only).

---

## Sign-off

| Party | Verdict | Date |
|-------|---------|------|
| TenderPro wave 1 | **PASS** | 2026-07-31 |
| Revy cross-repo dogfood (pre-RR-W1) | **FAIL** — drives **RR-W1** | 2026-07-31 |
| RR-W1 R0 baseline | **PASS** (log-based RR-DG4 tag) | 2026-07-31 |
| RR-W1 R1–R4 (code ship) | **PASS** — `deda3c9` CI + Droplet deploy | 2026-07-31 |
| RR-W1 R5 RR-V gates | **PASS** — Revy PR #78/#79 staging DB + unit tests | 2026-07-31 |
| RR-Q4 product gate | **soft enable** recommended | 2026-07-31 |
| RR-W1 program | **PASS** (pending #79 merge for doc sync) | 2026-07-31 |
