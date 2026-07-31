# Revy review — cross-repo dogfood staging validation

**Program:** [README.md](./README.md) · **Findings:** [REVY_REVIEW_DOGFOOD_FINDINGS.md](./REVY_REVIEW_DOGFOOD_FINDINGS.md)  
**Case study (symptom evidence only):** TenderPro [PR #130](https://github.com/raimondskrauklis/tender_pro/pull/130) — motivated RR-DG* catalog; **not** the validation venue.  
**Validation venue:** `raimondskrauklis/revy` staging dogfood PR with **≥5 completed review runs** and DB-backed RR-V gate.  
**Status:** RR-W1 code shipped `deda3c9` — **R5 RR-V sign-off PENDING** (real multi-push protocol below).  
**Invalidated:** [#79](https://github.com/raimondskrauklis/revy/pull/79) closed — premature PASS + push during Revy run.

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
| **RR-W1 R1–R4 ship** | `deda3c9` deployed `2026-07-31T19:13:21Z` | [Actions #30657955604](https://github.com/raimondskrauklis/revy/actions/runs/30657955604) |

---

## Dogfood PR (validation venue — `raimondskrauklis/revy`)

| PR | Branch | Status |
|----|--------|--------|
| [#78](https://github.com/raimondskrauklis/revy/pull/78) | `docs/revy-review-dogfood-findings` | merged `deda3c9` — implementation only |
| *(open)* | [#80](https://github.com/raimondskrauklis/revy/pull/80) `chore/rr-w1-r5-staging-validation` | **active** — push 1 complete |

**Fixture:** `backend/app/services/rr_w1_staging_probe.py` (pattern: FR-CS4 / FR-DG2 probes).

**DB script (operator):**

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.revy_review_dogfood_staging_validation \
  --pr-number <N> --since 2026-07-31T19:08:32Z --json

# Sign-off gate (exit 1 until all checks PASS):
DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.revy_review_dogfood_staging_validation \
  --pr-number <N> --since 2026-07-31T19:08:32Z --rr-v-gate
```

---

## Multi-push protocol (≥5 completed review runs)

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce `rr_w1_staging_probe` defect (`subprocess` + `shell=True`) | **done** `8f7f5e0` |
| 2 | Structural fix — `rr_w1_probe_composed()` only; verify `transitions_addressed` ≥ 1 | **done** `ee4668c` — **closure FAIL** (see notes) |
| 3 | Remove dead defect code + unrelated backend touch (pairing / `last_seen`) | **done** `abdbd5c` — probe `resolved`/`addressed` |
| 4 | Same-`head_sha` double-push OR rapid second SHA (RR-V1) | **done** `38dd7b4` — rev 4 complete (Revy check skipped) |
| 5 | Confirm groups stay `resolved`/`addressed`; `--rr-v-gate` | **done** `8aec926` — 5 runs; judge `completed` on rev 5 |

**Rules:** wait for Revy check **complete** before next push; record `head_sha`, `review_run_id`, group IDs per push in Results table.

### Results (operator — fill per push)

| Push | `head_sha` | Revy rev | `review_run_id` | Notes |
|------|------------|----------|-----------------|-------|
| 1 | `8f7f5e0` | 1 | `019fb9a7-ddf0-7dc0-b894-94e8a8d604ce` | 3 groups published (1 critical probe); judge 1/2 outcomes; publish OK |
| 2 | `ee4668c` | 2 | `019fb9b2-78ee-7646-9f12-d5375f3b880c` | **closure FAIL:** `transitions_addressed=0`; old probe group superseded; new critical on dead `subprocess` body; `resolve_mutation_failed=2` |
| 3 | `abdbd5c` | 3 | `019fb9b7-ac80-770c-b69f-067e391a891b` | **closure PASS:** group `019fb9b3…` `resolved`/`absent_and_addressed`; `transitions_addressed=1`; rate 100% |
| 4 | `38dd7b4` | 4 | — | empty + doc commit; 4 revisions; RR-V1 PASS |
| 5 | `8aec926` | 5 | `019fb9c2-490b-7f45-8387-a5d0d3cd8239` | judge `completed` (2 outcomes); `resolve_mutation_failed=4` on publish |

---

## RR-V gates (DB-backed — `--rr-v-gate` on PR #80 @ 2026-07-31)

| Gate | Pass criteria | Status | Evidence |
|------|---------------|--------|----------|
| **RR-V1** | One revision row per `head_sha`; no IntegrityError | **PASS** | 5 revisions; `rows_per_head_sha=1` each |
| **RR-V2** | ≥5 completed runs; `resolution_rate_pct > 0` + `transitions_addressed ≥ 1` | **PASS** | rev 3 manifest: `transitions_addressed=1`, rate 100% |
| **RR-V3** | `publish_head_sha` == revision `head_sha` on all completed publishes | **PASS** | 5/5 parity |
| **RR-V4** | `thread_resolve_skipped` zero or manifest breakdown only | **PENDING** | `resolve_mutation_failed=2` (rev 2–4), `=4` (rev 5) — GitHub thread resolve API failures |
| **RR-V5** | HEAD suppression unit matrix + `head_contradiction_suppressed_count` when applicable | **pending** | pytest matrix not re-run this session |
| **Judge** | Escalation run with persisted `github_finding_judge_outcomes` | **PASS** | 3/3 escalation runs with outcomes; rev 5 `judge_status=completed` |
| **Closure** | Finding groups `resolved` or `resolution_status=addressed` after fix push | **PASS** | probe group `019fb9b3…` `resolved`/`absent_and_addressed` on push 3 |

**Sign-off:** `--rr-v-gate` exits **1** — blocked on **RR-V4** (+ RR-V5 pytest not recorded). Do **not** merge #80 as RR-V PASS until RR-V4 resolved or documented partial with owner.

---

| [#130](https://github.com/raimondskrauklis/tender_pro/pull/130) | `tender_pro` | Symptom catalog only (merged) |

---

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

---

## Sign-off

| Party | Verdict | Date |
|-------|---------|------|
| TenderPro wave 1 (app) | **PASS** | 2026-07-31 |
| Revy pre-RR-W1 symptoms (TenderPro evidence) | **FAIL** — motivated RR-W1 | 2026-07-31 |
| RR-W1 R0 baseline | **PASS** | 2026-07-31 |
| RR-W1 R1–R4 code ship | **PASS** — `deda3c9` | 2026-07-31 |
| RR-W1 R5 RR-V gates | **partial** — RR-V1/2/3/judge/closure PASS; **RR-V4 blocked** (`resolve_mutation_failed`) | 2026-07-31 |
| RR-Q4 product gate | **pending** — after RR-V2 PASS | — |
