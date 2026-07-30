# Finding resolution — post–wave C general plan

**Baseline:** [FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md](./FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md)  
**Parent:** Wave C [closure scope](./FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md) (shipped); [dogfood](../finding-resolution-dogfood/README.md) (FR-DG1/2 PASS).

**Thesis:** Ship **MR-DG1** (Moonshot prompt) immediately on an isolated branch. **Wave D** closes **FR-CS4** (structural fix via Pass 3 widen + dogfood) when prioritized; **FR-CS8** stays monitor-first with optional observability.

**Cross-cutting (every phase):** unit tests (`backend/tests/unit/` only); no Pass 1a line-region loosening (PW-Q4); CS-Q10 — no judge for file deletion; EN strings via existing formatter paths; no migrations unless D2 durable column explicitly scheduled (deferred).

**Locked (from backlog):** PW-Q1 implement MR-DG1; PW-Q2 defer FR-CS4 to wave D; PW-Q3 defer FR-CS8 (monitor); PW-Q5 MR-DG1 separate branch from wave D.

---

## M0 — MR-DG1 Moonshot formatter API

**Goal:** Moonshot does not flag valid `format_summary_comment(generation_groups=…, pr_active_groups=…)` as unknown kwargs.

**Scope in:** Reviewer prompt API snippet in `moonshot_review.py`; `test_moonshot_review.py`; close MR-DG1 in dogfood findings.

**Scope out:** Formatter signature change; resolution pipeline; SSOT program switch.

**Deliverables:** Branch `chore/moonshot-formatter-signature`; pytest gate; MR-DG1 → closed in findings.

**Depends on:** `main` post–#68 / #69.

---

## D0 — FR-CS4 Pass 3 cohort widen (code)

**Goal:** Verification judge can run on PR-wide `still_open` escalation candidates, not only pairing cohort.

**Scope in:** SSOT `finding-resolution-post-wave-c`; widen `verify_still_open_escalation_groups` candidate query (mirror Pass 2 *intent* for PR-wide `addressed` close, but Pass 3 filters `still_open` + escalation); unit tests including aged/outside-pairing candidate.

**Scope out:** Pass 1a `patch_touches_line_region` change; hygiene / Track A; judge prompt/parser changes.

**Deliverables:** Product PR; pytest on `test_github_finding_closure.py` Pass 3 paths.

**Depends on:** **M0** merged (or parallel on `main` — separate PR from M0).

---

## D1 — FR-CS4 staging dogfood

**Goal:** FR-CS4 closed PASS — fix without line-region overlap closes via Pass 3 (or documents judge outcome).

**Scope in:** Chore PR with review-visible finding → structural in-file fix (no line overlap); staging memo rows; per-group DB evidence; **staging `judge_llm_enabled()` required**.

**Scope out:** Program doc churn in dogfood pushes (VAL8 backend-only for metric pushes).

**Deliverables:** Staging memo sign-off; FR-CS4 → closed PASS in gap registry.

**Depends on:** **D0** merged + deployed to staging.

**Human gate:** Operator one-push-per-Revy-cycle; LOOP stops until memo signed.

---

## D2 — FR-CS8 observability (optional)

**Goal:** Detect supersede re-orphan risk without durable DB column.

**Scope in:** Structured log (or manifest counter) when sync clears `resolution_status` from `addressed` on `active` groups; unit test.

**Scope out:** `path_removed_at_revision_id` column; skip-reset stamp persistence.

**Deliverables:** Observable signal for ops; findings note on monitor status.

**Depends on:** **D1** or explicit operator decision to skip D1 and ship D2 alone.

**Human gate:** **Optional phase** — start only when monitoring shows re-orphan or operator explicitly schedules. Default: **skip**.

---

## D3 — Program doc sync

**Goal:** README + gap registry reflect M0/D1 outcomes; restore or update SSOT; wave D complete.

**Scope in:** Execution table Done + shas; backlog findings decisions locked; dogfood + finding-resolution README; `.revy/review-context.json` off wave D when done.

**Scope out:** New product features.

**Deliverables:** Doc-only commit; execution index all Done.

**Depends on:** **M0**; **D1** PASS (or D1 skipped with FR-CS4 still open); **D2** skipped or done.

---

## Dependencies

```text
M0 → (merge)
D0 → deploy → D1 (human) → D3
D2 optional (human gate) → D3
```

M0 and D0 may use **separate PRs**. Do not mix MR-DG1 prompt with Pass 3 widen (PW-Q5).

---

## Remaining open item

**PW-Q4** locks at D0 start: Pass 3 widen only — no Pass 1a line-region change.

**Next step:** [waves/FINDING_RESOLUTION_POST_WAVE_C_EXECUTION.md](./waves/FINDING_RESOLUTION_POST_WAVE_C_EXECUTION.md) — `phase-execution` from **M0**.
