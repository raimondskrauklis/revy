# Finding resolution — closure scope general plan (wave C)

**Baseline:** [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) (rev 3)  
**Parent:** [FINDING_RESOLUTION_GENERAL_PLAN.md](./FINDING_RESOLUTION_GENERAL_PLAN.md) (P0–P5 shipped)  
**Authority:** Findings § decisions registry (CS-Q3–Q10 locked).

**Thesis:** **Track A (HEAD hygiene)** — path absent at `revision.head_sha` → Pass 1b `addressed` stamp + widened Pass 2 close. **Track B (FR-Q12)** — Pass 1a pairing cohort (`deleted_paths` + line region; CS-Q11). **Track C (judge)** — out of scope.

**North star:** PSA #63 / #67 — file/path gone on HEAD → `absent_and_addressed` + thread collapsed on any push.

**Cross-cutting (every phase):** unit tests (`backend/tests/unit/` only); no silent metric/surface lies (CS-Q6); EN publish strings via existing formatter paths; no new migrations in wave C.

**Locked (from findings):** CS-Q7 path absent at `head_sha` (Contents 404); CS-Q8 deletions-only hygiene (not rename); CS-Q9 Pass 2 query widen; CS-Q11 Pass 1a `deleted_paths` only; CS-Q4 reuse `absent_and_addressed`; CS-Q6 exclude hygiene from rate + visible G9 line; CS-Q10 hygiene before FR-CS4.

---

## C0 — Program lock + review context

**Goal:** Baseline findings rev 3 + this plan for LOOP; wire SSOT/Greptile/Bugbot for wave C.

**Scope in:** `.revy/review-context.json`, `.greptile/files.json`, `.cursor/BUGBOT.md`, README execution table, gap registry → planned.

**Scope out:** Product code → **C1**.

**Deliverables:** `finding-resolution-closure-scope` active program; execution index; FR-CS* marked planned.

**Depends on:** Findings rev 3 locked.

---

## C1 — HEAD hygiene pipeline

**Goal:** Aged + adjacent file-delete groups close end-to-end (#67 VAL10, #66 regression).

**Scope in:** Compare-first sync; `deleted_paths` / `renamed_from_paths` split; Pass 1a `deleted_paths` only (CS-Q11); HEAD path-absent via `fetch_repository_file_at_sha` (+ compare `deleted_paths` fast path); Pass 1b; Pass 2 widen; R4 fail-closed; E2E tests.

**Scope out:** Pass 3 widen; Moonshot prompt; FR-CS4 line-region; durable DB column (R2 defer).

**Deliverables:** Branch `fix/fr-closure-scope-hygiene`; pytest gate on hygiene + Pass 2.

**Depends on:** **C0**.

---

## C2 — Manifest + G9 honesty

**Goal:** CS-Q6 — hygiene path-removed closures excluded from `resolution_rate_pct` and visible on publish surface.

**Scope in:** `build_resolution_pass_manifest` (hygiene exclusion + `head_check_failed_count`); `format_resolution_metrics_block`; formatter tests. **Closes FR-CS3.**

**Scope out:** Frontend; API schema changes.

**Deliverables:** `hygiene_path_removed_count` on manifest; G9 line “Closed as path removed”.

**Depends on:** **C1** (same PR / deploy unit as C1).

---

## C3 — Staging sign-off (dogfood Track C)

**Goal:** FR-DG2 + FR-CS1/6/7 closed PASS on staging post-deploy.

**Scope in:** Review-visible probe PR (import hook + unit test per dogfood protocol); aged-delete + rename + optional FR-Q13; staging memo rows.

**Scope out:** Product code unless C3 repro finds gap → hotfix branch.

**Deliverables:** Track C rows in dogfood staging memo; FR-DG2 + FR-CS1/6/7 → closed PASS; deploy-boundary `--since` ISO.

**Depends on:** **C1 + C2** deployed to staging.

**Human gate:** Operator push protocol (VAL8); LOOP stops after C3 until sign-off recorded.

---

## C4 — Program doc sync

**Goal:** Close gap registry; update parent + dogfood README status.

**Scope in:** README tables; FR-CS1/3/6/7 + FR-DG2 → closed; optional merge #67 evidence.

**Scope out:** MR-DG1; FR-CS4; FR-CS8.

**Deliverables:** Doc-only commit; execution table all Done.

**Depends on:** **C3** PASS.

---

## Dependencies

```text
C0 → C1 → C2 → deploy → C3 (human) → C4
```

C1 + C2 ship one PR (`fix/fr-closure-scope-hygiene`); two LOOP commits acceptable.

---

## Remaining open item

None on direction — calibration only: staging deploy ISO for C3 `--since` (recorded at deploy time).

**Next step:** [`create-execution-plan`](../../../.cursor/skills/create-execution-plan/SKILL.md) → [waves/FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md](./waves/FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md).
