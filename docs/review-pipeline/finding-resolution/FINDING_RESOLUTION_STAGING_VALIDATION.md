# Finding resolution — staging validation

**Date:** 2026-07-28 (updated — code-complete on branch; staging sign-off pending)  
**Program:** [waves/FINDING_RESOLUTION_EXECUTION.md](./waves/FINDING_RESOLUTION_EXECUTION.md)  
**Branch:** `feat/finding-resolution` · pushed head `73401aa` · local `8b453aa` (P4)  
**Related:** [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](./FINDING_RESOLUTION_TECHNICAL_FINDINGS.md) · [JUDGE_INPUT_QUALITY_STAGING_VALIDATION.md](../judge/JUDGE_INPUT_QUALITY_STAGING_VALIDATION.md)

**Workflow:** Operator pushes after each phase; record evidence here before advancing.

---

## Phase checkpoints

| Phase | Commit | Deployed staging | Staging checked | Pass |
|-------|--------|------------------|-----------------|------|
| P0 — schema `0028` | `76e8784` | still `0027` | migration not applied | pending ops |
| P1 — Pass 1 + Pass 2 | `c0522ec` / `97a7e01` | partial (rev 2) | partial — see rev 2 run | partial |
| P2 — Pass 3 verification | `c0522ec` | same | no escalation sample yet | pending |
| P3 — metrics + G9 + API | `73401aa` | not yet | — | pending deploy |
| P4 — dismiss + summary parity | `8b453aa` (local) | not yet | — | pending deploy |
| P5 — doc sync + sign-off | this commit | — | — | code-complete |

---

## Staging run — rev 2 (`c0522ec`, 2026-07-28 ~18:15 UTC)

| Check | Expected | Actual | Pass |
|-------|----------|--------|------|
| Pipeline completes | index → review → reconcile → judge → publish | Completed | yes |
| Moonshot review | findings JSON parses | `parsed_count=1`, `dropped_count=0` | yes |
| Discovery judge | outcome row for escalation candidate | **0** outcomes; `judge_status=skipped_unavailable` | **no** — judge JSON parse fail (see technical findings) |
| RG-6 publish gate | Withhold inline without outcome | Escalation finding not inline-published; issue comment reused | yes (by design) |
| Pass 2 on rev 2 | Close absent+addressed groups | Not exercised (no prior `addressed` groups on rev 1) | — |

**Judge incident:** Not a finding-resolution regression — Anthropic 200 but no persisted outcome; separate [judge-json-contract](../judge-json-contract/README.md) wave (next).

---

## Compare API failure (P1 / P5.2)

**Expected (locked):** On `synchronize`, when GitHub compare fails, Pass 1 stamps `resolution_status=still_open` and `closure_blocked_reason=compare_failed`. Pass 2 must **not** close the group as `addressed`.

| Step | Expected | Staging | Unit coverage |
|------|----------|---------|---------------|
| Compare fails on sync | `closure_blocked_reason=compare_failed`, `still_open` | not exercised on staging | `test_apply_resolution_status_for_synchronize_stamps_compare_failed` |
| No false `addressed` | Group stays `active`, not `resolved` | — | `test_should_not_close_when_compare_failed` |
| Denominator exclusion | `compare_failed` excluded from FR-Q12 denominator | — | `test_build_resolution_pass_manifest_counts_transitions` |

---

## P1 — fix + push (typical closure)

| Step | Expected | Actual | Date |
|------|----------|--------|------|
| Before fix | Group `active`, inline thread open | pending dogfood | |
| Push fix (line touch) | Pass 1: `resolution_status=addressed` | pending | |
| After publish rev N | Pass 2: `state=resolved`, `resolution_method=absent_and_addressed` | pending | |
| GitHub | Thread resolved (Option A) | pending | |

---

## P2 — verification judge (escalation still-open)

| Step | Expected | Actual | Date |
|------|----------|--------|------|
| Escalation group still `still_open` after Pass 1–2 | In FR-Q11 set | pending sample PR | |
| Pipeline GET judge step | `verification_judged_count` ≤ 5, `judge_purpose=verification` | pending | |
| Outcome `dismissed` | `resolution_method=verification_dismissed` | pending | |

---

## P3 — resolution metrics (after deploy)

| Step | Expected | Actual | Date |
|------|----------|--------|------|
| Reconcile manifest | `resolution_pass` on reconcile step | pending | |
| Issue comment | Resolution metrics block + G9 prose | pending | |
| API | `resolution_status`, `resolution_method` on reconciled list | pending | |

---

## P4 — human dismiss + two-block summary

| Step | Expected | Actual | Date |
|------|----------|--------|------|
| Admin dismiss API | `human_dismissed` on HEAD revision | unit + route tests pass | 2026-07-28 |
| Check run summary | Two blocks: generation + PR still open | unit tests pass | 2026-07-28 |
| Reviewer UI | Badges + dismiss on active groups | FindingRow tests pass | 2026-07-28 |

---

## Before/after metrics table (P5.1 — operator)

| Metric | Before fix push | After fix + publish | Date |
|--------|-----------------|---------------------|------|
| `resolution_rate_pct` (manifest) | | | |
| `transitions_addressed` | | | |
| Active groups on PR | | | |
| Inline thread state | | | |

---

## Bot review triage — PR #57

| Source | Finding | Verdict | Action |
|--------|---------|---------|--------|
| Greptile P1 | FK `ondelete=SET NULL` on ORM | **Fixed** | resolved |
| Greptile P2 | `closure_blocked_reason` clear on close | **Fixed** | resolved |
| Greptile P2 | `None` in skip-set | **Intentional** | docstring |
| Revy | Circular imports closure ↔ judge | **Fixed** `208a074` | resolved |
| Revy | Pass 2 overwrites resolved groups | **Fixed** `97a7e01` | resolved |

---

## SQL helpers (staging)

```sql
SELECT state, resolution_status, resolution_method, closure_blocked_reason, count(*)
FROM github_finding_groups
WHERE pull_request_id = '<pr_uuid>'
GROUP BY 1, 2, 3, 4;

SELECT content_json->'resolution_pass' AS resolution_pass
FROM github_pipeline_artifacts a
JOIN github_pipeline_steps s ON s.id = a.step_id
WHERE s.step_type = 'reconcile'
ORDER BY a.created_at DESC
LIMIT 1;
```

Full repro queries: [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](./FINDING_RESOLUTION_TECHNICAL_FINDINGS.md).

---

## Human gate (P5 sign-off)

- [ ] Apply migration `0028` on staging
- [ ] Deploy branch through P4 (`8b453aa+`)
- [ ] Before/after metrics table complete (§ P5.1)
- [x] Compare-failure row documented (§ Compare API failure)
- [ ] Verification judge sample on escalation PR
- [ ] Discovery judge parse rate acceptable ([judge-json-contract](../judge-json-contract/README.md))
- [x] Program docs marked **shipped** on branch (P5.4)
- [ ] Merge PR #57 → `main`
