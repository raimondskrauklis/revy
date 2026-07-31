# Revy review — cross-repo dogfood staging validation

**Program:** [README.md](./README.md) · **Findings:** [REVY_REVIEW_DOGFOOD_FINDINGS.md](./REVY_REVIEW_DOGFOOD_FINDINGS.md)  
**Case study:** TenderPro [PR #130](https://github.com/raimondskrauklis/tender_pro/pull/130) (super-admin dashboard wave 1)  
**Status:** evidence captured 2026-07-31 — **Revy product FAIL** / **customer app PASS**

---

## Evidence sources (operator)

| Artifact | Location | Notes |
|----------|----------|-------|
| Finding matrix + pass criteria | `misc/SUPER_ADMIN_DASHBOARD_STAGING_VALIDATION.md` | 25 Revy items triaged |
| Worker log | `misc/tenderprolog.txt` | 2026-07-31 15:50–16:04 UTC |

---

## Deploy boundaries

| Boundary | Value | Used for |
|----------|-------|----------|
| Revy transport #75 | `1c416a0` deployed `2026-07-31T12:18:17Z` | Judge transport baseline |
| TenderPro session | rev 12 summary `b4ba498` | Stale vs `999ad17` tip |

---

## Dogfood PR (external)

| PR | Repo | Status |
|----|------|--------|
| [#130](https://github.com/raimondskrauklis/tender_pro/pull/130) | `tender_pro` | open — app merge-ready; Revy tuning ongoing |

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

## Pass criteria

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

## Sign-off

| Party | Verdict | Date |
|-------|---------|------|
| TenderPro wave 1 | **PASS** | 2026-07-31 |
| Revy cross-repo dogfood | **FAIL** — drives **RR-W1** | 2026-07-31 |

**Next:** Peer-review findings → general plan → execution (RR-W1). Do **not** merge TenderPro probe artifacts into Revy `main`.
