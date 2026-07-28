# Finding resolution — staging validation

**Date:** 2026-07-28 (partial — rev 2 dogfood on PR #57)  
**Program:** [waves/FINDING_RESOLUTION_EXECUTION.md](./waves/FINDING_RESOLUTION_EXECUTION.md)  
**Branch:** `feat/finding-resolution` · head `c0522ec`  
**Related:** [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](./FINDING_RESOLUTION_TECHNICAL_FINDINGS.md) · [JUDGE_INPUT_QUALITY_STAGING_VALIDATION.md](../judge/JUDGE_INPUT_QUALITY_STAGING_VALIDATION.md)

**Workflow:** Human pushes after each phase; record evidence here before advancing.

---

## Phase checkpoints

| Phase | Deployed | PR / commit | Staging checked | Pass |
|-------|----------|-------------|-----------------|------|
| P0 — schema `0028` | staging still `0027` | `76e8784` | migration not applied on staging DB | — |
| P1 — Pass 1 + Pass 2 closure | `c0522ec` on PR head | Revy rev 2 run | partial (see below) | partial |
| P2 — Pass 3 verification judge | `c0522ec` | no escalation `still_open` sample yet | — | — |
| P3 — metrics + G9 + API | | | | |
| P4 — dismiss + summary parity | | | | |
| P5 — full dogfood sign-off | | | | |

---

## Staging run — rev 2 (`c0522ec`, 2026-07-28 ~18:15 UTC)

| Check | Expected | Actual | Pass |
|-------|----------|--------|------|
| Pipeline completes | index → review → reconcile → judge → publish | Completed | yes |
| Moonshot review | findings JSON parses | `parsed_count=1`, `dropped_count=0` | yes |
| Discovery judge | outcome row for escalation candidate | **0** outcomes; `judge_status=skipped_unavailable` | **no** — judge JSON parse fail (see technical findings) |
| RG-6 publish gate | Withhold inline without outcome | Escalation finding not inline-published; issue comment reused | yes (by design) |
| Pass 2 on rev 2 | N/A first rev with P1 code | Not exercised (no prior `addressed` groups on rev 1) | — |

**Judge incident:** Not a finding-resolution regression — Anthropic 200 but no persisted outcome; separate judge-json-contract wave (next).

---

## Bot review triage — PR #57 (`c0522ec`)

| Source | Finding | Verdict | Action |
|--------|---------|---------|--------|
| Greptile P1 | FK `ondelete=SET NULL` on ORM | **Fixed** in branch | resolved thread |
| Greptile P2 | `closure_blocked_reason` clear on close | **Fixed** | resolved thread |
| Greptile P2 | `None` in skip-set undocumented | **Intentional** — legacy resolved rows | docstring updated |
| Greptile summary | Verification judge must reject `modified` | **Valid** | fixed in branch |
| Revy WARNING | `base_sha==head_sha` guard on judge path | **Already fixed** — `skip_when_same_sha=False` on `fetch_compare_patches_by_file` | stale thread |
| Revy WARNING | `should_close` ignores non-compare block reasons | **Fixed** — `closure_blocked_reason is None` | stale thread |
| Revy INFO | P0 doc `judge_purpose` nullable | **Already fixed** in execution doc | stale thread |
| Revy/Moonshot rev 2 | Pass 2 overwrites `judge_dismissed` groups | **Valid** | fixed — Pass 2 active groups only |
| CI | ruff I001 test imports | **Fixed** locally | pending push |

---

## P1 — fix + push (typical closure)

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

## Compare API failure (P1)

| Step | Expected | Actual | Date |
|------|----------|--------|------|
| Compare fails on sync | `closure_blocked_reason=compare_failed`, `still_open` | | |
| No false `addressed` | Group stays open | | |

---

## SQL helpers (staging)

```sql
SELECT state, resolution_status, resolution_method, closure_blocked_reason, count(*)
FROM github_finding_groups
WHERE pull_request_id = '<pr_uuid>'
GROUP BY 1, 2, 3, 4;
```

Full repro queries: [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](./FINDING_RESOLUTION_TECHNICAL_FINDINGS.md).

---

## Human gate (P5 sign-off)

- [ ] Before/after metrics table complete
- [ ] Compare-failure row documented
- [ ] Verification judge sample (if any escalation case)
- [ ] Discovery judge parse rate acceptable (judge-json-contract wave)
- [ ] Linked from [README.md](./README.md) as **shipped**
