# Finding resolution — post–wave C backlog findings

**Purpose:** After wave C ([#68](https://github.com/raimondskrauklis/revy/pull/68) product, [#69](https://github.com/raimondskrauklis/revy/pull/69) C3 PASS), decide what to **implement next** vs **defer**. Baseline for a general plan — no execution steps.

**Authority:** Code on `main` post-#68; dogfood sign-off [memo](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md); closure-scope [findings](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md).

---

## Build principles (this backlog)

1. **Hygiene is shipped** — file deletion / path-gone closes via Track A; do not re-open FR-DG2.
2. **Separate tracks** — Moonshot prompt quality (MR-DG1) ≠ closure cohort logic (FR-CS4/8).
3. **Dogfood before sign-off** — structural-fix closure needs a repro PR, not unit tests alone.
4. **No judge for deletion** — CS-Q10 locked; Pass 3 is for ambiguous *still_open*, not path removal.

---

## Recommendation summary

| ID | Gap | Verdict | Wave | Effort | Why |
|----|-----|---------|------|--------|-----|
| **MR-DG1** | Moonshot hallucinates `format_summary_comment` kwargs | **Implement** | P4 (dogfood B) | **S** | Prompt-only; execution doc ready; no pipeline coupling |
| **FR-CS4** | Line-region `addressed` false negatives; Pass 3 pairing wall | **Dogfood (D1)** | Wave D | **M** | D0 code shipped [#71](https://github.com/raimondskrauklis/revy/pull/71); staging repro pending |
| **FR-CS8** | Ephemeral `resolution_status` on fast supersede | **Defer** (monitor) | Wave D optional | **S** | C3 happy path OK; edge case only; durable column optional |

**Suggested order:** MR-DG1 → (pause) → wave D scoping when a real structural-fix dogfood repro is prioritized.

---

## What exists (verified)

| Area | State | Evidence |
|------|-------|----------|
| Track A hygiene | **Shipped** | `github_resolution_metrics.py` Pass 1b + `paths_absent_at_head`; Pass 2 widen `resolution_status == addressed` (`github_finding_closure.py:171–174`) |
| Track B metrics | **Shipped** | Pass 1a pairing + `deleted_paths` only (CS-Q11); manifest excludes hygiene from rate (CS-Q6) |
| FR-DG2 sign-off | **PASS** | #69 rev 6 — `absent_and_addressed`, `hygiene_path_removed_count=1` |
| Pass 3 verification | **Shipped (D0 #71)** | `pass3_verification_escalation_select` — PR-wide `still_open` + SQL predicates (`github_finding_closure.py:94–140`) |
| Moonshot reviewer prompt | **No formatter API** | `moonshot_review.py` — `REVIEW_SYSTEM_PROMPT` only; no `format_summary_comment` / `generation_groups` |
| Formatter signature | **Stable** | `format_summary_comment(*, generation_groups, pr_active_groups)`; `filter_pr_active_groups_for_summary` for GH-1v2-aligned PR block — `github_publish_formatter.py` |
| MR-DG1 execution | **Written, not run** | [P4 execution](../finding-resolution-dogfood/waves/FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md) |

---

## MR-DG1 — Moonshot formatter signature hallucination

### Symptom (verified)

PR #63 rev 4: Moonshot flagged valid test call `format_summary_comment(..., generation_groups=…)` as unknown kwarg. Signature uses those names; unit tests pass.

### Root cause (verified)

Reviewer prompt does not include publish-formatter public API. Model infers kwargs from partial diff context.

### Scope (locked from P4)

- **In:** Short API block in `moonshot_review.py` reviewer prompt; pytest on prompt content.
- **Out:** Formatter signature change; resolution pipeline; judge JSON contract.
- **Branch:** `chore/moonshot-formatter-signature` (parallel to dogfood).

### Pass criteria

| Check | Expected |
|-------|----------|
| Prompt contains `format_summary_comment`, `generation_groups`, `pr_active_groups` | Unit test green |
| Staging diff with valid formatter test call | Moonshot does not flag kwargs (manual or dogfood push) |

### Verdict: **Implement**

Low risk, isolated, pre-planned. Closes the last open dogfood wave B item without touching closure logic.

---

## FR-CS4 — Line-region false negatives + Pass 3 cohort wall

### Problem (verified)

Pass 1a stamps `addressed` only when push-pair diff **overlaps finding line region** (`patch_touches_line_region`, `github_resolution_metrics.py:32–64`, `130–132`). Fixes elsewhere in the file (refactor, delete snippet, move logic) stay `still_open`.

Pass 3 verification judge only sees groups with `last_seen_revision_id ∈ pairing_revision_ids` (`github_finding_closure.py:249–256`). **Pass 2 was widened in wave C; Pass 3 was not** — same FR-CS6-class gap for judge path.

### What wave C already fixed (do not re-litigate)

- File / path removal → Track A hygiene → **not FR-CS4**.
- Aged deletion cohort (#67 VAL10) → **closed** on #69.

### Remaining user-visible gap

Developer **fixes the issue** without touching anchored lines → group stays `still_open`; inline may stay open; resolution rate does not credit fix.

**Example shape:** #67 push 2 removed wrong-kwargs snippet (file edited, line region of original finding may not overlap). That cohort was pairing-scoped Track B, not hygiene.

### Options

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **A — Widen Pass 3 cohort** (mirror Pass 2: all `still_open` escalation-eligible on PR) | Reuses judge; bounded cap (5/run) | Cost; needs dogfood repro | **Preferred when implementing** |
| **B — Loosen `patch_touches_line_region`** (e.g. any hunk in file → `addressed`) | Cheap | Over-stamps refactors; hurts FR-Q12 honesty | **Reject** |
| **C — Pass 3 only, no Pass 1 change** | Clear separation | Leaves `still_open` until reconcile | Part of A |
| **D — Full-file semantic judge** | Highest accuracy | Expensive; overlaps judge-json-contract | **Defer** |

### Verdict: **Defer** (wave D)

Not a production blocker after hygiene PASS. Needs:

1. **Dogfood repro PR** — introduce finding → fix without line overlap → expect closure via judge (not deletion).
2. **Pass 3 query widen** + tests mirroring `test_apply_pass2_closure_e2e_aged_group_outside_pairing`.
3. **Staging sign-off** separate from FR-DG2.

Do **not** block MR-DG1 or ops work on this.

---

## FR-CS8 — Ephemeral `resolution_status` stamp

### Problem (verified)

Every `synchronize`, all non-superseded groups get `resolution_status = None` before restamp (`github_resolution_metrics.py:224–225`). Stamp is recomputed in same sync; Pass 2 runs later in reconcile **on the same review run** when publish completes normally.

### What wave C mitigated

- Compare-first + hygiene Pass 1b runs even when pairing cohort empty (aged groups).
- Pass 2 widen closes `addressed` groups outside pairing window.
- C3 proved end-to-end close when publish completes in order.

### Remaining edge (R2)

Fast follow-up push before prior publish finishes → `skipped_not_head` → next sync wipes stamp → group may re-orphan if hygiene does not apply.

**Frequency:** Low under dogfood protocol (one push per Revy cycle). Real in noisy CI / multi-commit pushes.

### Options

| Option | Effort | Verdict |
|--------|--------|---------|
| **Monitor** — no code; watch for re-orphan after supersede | None | **Now** |
| **Observability** — log/metric when stamp cleared while `state=active` and prior stamp was `addressed` | S | Optional wave D.0 |
| **Durable column** `path_removed_at_revision_id` / stamp persistence | M | **Defer** — C3 same-run close sufficient for FR-DG2 PASS |
| **Skip reset** for groups already `addressed` same revision pair | M | Risky; needs design |

### Verdict: **Defer** (monitor)

Re-open only if staging/production shows re-orphan after supersede **without** path-gone. Not paired with MR-DG1.

---

## Parking lot (related, not in scope)

| Item | Notes |
|------|-------|
| Batch Git tree API for HEAD checks | Optimize when rate limits bite |
| R5 `judge_dismissed` mislabel | Pre-existing metrics accuracy |
| C3.4 rename guard / C3.5 FR-Q13 | Optional; timeboxed; not gated |
| `judge_json_contract` `--head-sha` filter | Operator ergonomics (DG-PV lesson) |

---

## Decisions registry

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| **PW-Q1** | Implement MR-DG1 next? | **recommended** | **Yes** — P4 prompt-only on `chore/moonshot-formatter-signature` |
| **PW-Q2** | Implement FR-CS4 now? | **locked** | **D0 done** — D1 staging dogfood in progress |
| **PW-Q3** | Implement FR-CS8 now? | **recommended** | **No** — monitor; observability optional |
| **PW-Q4** | Pass 3 widen without Pass 1 line change? | **locked** | **Yes** — D0 only; see [D0 execution](./waves/FINDING_RESOLUTION_POST_WAVE_C_D0_EXECUTION.md) |
| **PW-Q5** | MR-DG1 same PR as wave D? | **locked** | **No** — separate branch per P4 execution |

---

## Devil's advocate

| Risk | Mitigation |
|------|------------|
| MR-DG1 prompt bloat → reviewer noise | Keep API block &lt; 20 lines; names only, no full formatter source |
| FR-CS4 “fix” over-closes refactors | Use judge verification, not broader Pass 1a |
| FR-CS8 durable column premature | C3 PASS is sufficient product bar for deletion |
| Doing wave D without repro | Repeat #65 mistake — metric noise vs group-level truth |

---

## Experiment / verification

| Experiment | Pass |
|------------|------|
| MR-DG1 prompt test | `test_moonshot_review.py` asserts formatter API snippet in prompt |
| MR-DG1 staging | Valid `generation_groups` test in diff → no Moonshot error finding |
| FR-CS4 (wave D) | Fix-without-line-touch → Pass 3 judge → `state=resolved` + `resolution_method=verification_dismissed` |
| FR-CS8 monitor | After `skipped_not_head`, query group `resolution_status` + `state` — document if re-orphan |

---

## References

| Doc | Link |
|-----|------|
| MR-DG1 baseline | [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md § MR-DG1](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) |
| P4 execution | [FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md](../finding-resolution-dogfood/waves/FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md) |
| Wave C gaps | [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md § Gap registry](./FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) |
| C3 sign-off | [FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md § Track C](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) |
| Pass 2 aged E2E test | `backend/tests/unit/test_github_finding_closure.py` — `test_apply_pass2_closure_e2e_aged_group_outside_pairing` |

**Next step:** [FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md](./FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md) → [execution index](./waves/FINDING_RESOLUTION_POST_WAVE_C_EXECUTION.md) — start **M0**.
