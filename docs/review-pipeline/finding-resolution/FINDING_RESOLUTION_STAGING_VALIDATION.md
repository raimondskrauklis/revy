# Finding resolution — staging validation

**Date:** pending — fill per phase as Revy outputs are checked on staging  
**Program:** [waves/FINDING_RESOLUTION_EXECUTION.md](./waves/FINDING_RESOLUTION_EXECUTION.md) P5  
**Branch:** `feat/finding-resolution`  
**Related:** [JUDGE_INPUT_QUALITY_STAGING_VALIDATION.md](../judge/JUDGE_INPUT_QUALITY_STAGING_VALIDATION.md) (discovery judge context) · [REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md](../REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md)

**Workflow:** Human pushes after each phase; agent stops at phase boundary (no push). Record evidence here before advancing.

---

## Phase checkpoints (fill as phases land)

| Phase | Deployed | PR / commit | Staging checked | Pass |
|-------|----------|-------------|-----------------|------|
| P0 — schema `0028` | pending deploy | local commit | apply `0028` before P1 | |
| P1 — Pass 1 + Pass 2 closure | | | | |
| P2 — Pass 3 verification judge | | | | |
| P3 — metrics + G9 + API | | | | |
| P4 — dismiss + summary parity | | | | |
| P5 — full dogfood sign-off | | | | |

---

## P1 — fix + push (typical closure)

**Setup:** Staging PR with at least one ERROR inline from Moonshot.

| Step | Expected | Actual | Date |
|------|----------|--------|------|
| Before fix | Group `active`, inline thread open | | |
| Push fix (line touch) | Pass 1: `resolution_status=addressed` | | |
| After publish rev N | Pass 2: `state=resolved`, `resolution_method=absent_and_addressed` | | |
| GitHub | Thread resolved (Option A) | | |

---

## P2 — verification judge (escalation still-open)

| Step | Expected | Actual | Date |
|------|----------|--------|------|
| Escalation group still `still_open` after Pass 1–2 | In FR-Q11 set | | |
| Pipeline GET judge step | `verification_judged_count` ≤ 5, `judge_purpose=verification` | | |
| Outcome `dismissed` | `resolution_method=verification_dismissed` | | |

---

## P3 — resolution rate (FR-Q12)

| Metric | Expected | Actual | Date |
|--------|----------|--------|------|
| Reconcile manifest `resolution_pass` | `denominator_active_prior`, transitions, `resolution_rate_pct` | | |
| Issue comment | Metrics block present | | |
| Denominator | Excludes `compare_failed` + pre-sync `resolved` | | |

---

## Compare API failure (P1)

| Step | Expected | Actual | Date |
|------|----------|--------|------|
| Compare fails on sync | `closure_blocked_reason=compare_failed`, `still_open` | | |
| No false `addressed` | Group stays open | | |

---

## SQL helpers (staging)

```sql
-- Groups on dogfood PR
SELECT state, resolution_status, resolution_method, closure_blocked_reason, count(*)
FROM github_finding_groups
WHERE pull_request_id = '<pr_uuid>'
GROUP BY 1, 2, 3, 4;
```

---

## Human gate (P5 sign-off)

- [ ] Before/after metrics table complete
- [ ] Compare-failure row documented
- [ ] Verification judge sample (if any escalation case)
- [ ] Linked from [README.md](./README.md) as **shipped**
