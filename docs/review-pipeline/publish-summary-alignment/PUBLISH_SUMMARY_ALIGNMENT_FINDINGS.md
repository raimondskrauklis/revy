# Publish summary alignment — findings

**Date:** 2026-07-29  
**Purpose:** Baseline for completing **FR-Q7** on the GitHub **issue comment** — parity with check run, PR-wide verdict fields, and inline thread reality. **No execution steps.**

**When to start:** After [RCX P6+P7](../review-engineering-context/README.md) merged (#61). Implementation on `feat/publish-summary-alignment` from `main`.

**Discussion:** [PUBLISH_SUMMARY_ALIGNMENT_DISCUSSION.md](./PUBLISH_SUMMARY_ALIGNMENT_DISCUSSION.md) — PSA-D1–D9 locked.

**Evidence:** Code on `main` post-#61; dogfood PR #61; [generation lifecycle §3c](../review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_FINDINGS.md); [finding-resolution FR-Q7](../finding-resolution/FINDING_RESOLUTION_FINDINGS.md).

---

## Build principles

1. **Snapshot at HEAD** — one issue comment per PR, body replaced each publish; no append history (RG-Q1).
2. **Same contract on both summary channels** — check + issue comment share two-block findings scope (PSA-D1).
3. **Verdict honesty** — confidence / merge recommendation reflect **all PR active** findings, not generation-only (PSA-D2).
4. **Inline unchanged** — generation publishable only; thread collapse via GH-1v2 (PSA-D4, PSA-D6).
5. **Verify against code** — cite `file:line`; tests are contract witnesses.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Generation groups** | `publishable_groups_for_review_run` — groups linked to findings in **this** `review_run_id` |
| **PR active groups** | All `github_finding_groups` with `state=active` on the pull request |
| **Two-block summary** | `### This generation` + `### Still open on PR` (`format_summary_comment`) |
| **Verdict fields** | Confidence, merge recommendation, files needing attention, security/important-files rollups |
| **RG-14** | Gap: issue comment generation-only while check is two-block |

---

## What exists vs genuinely new

### Shipped (verified)

| Capability | Location | Notes |
|------------|----------|-------|
| Two-block **check** summary | `build_check_run_summary` `github_publish_formatter.py:317–331` | Uses `ctx.groups` + `ctx.pr_active_groups` |
| Deterministic issue-comment tables | `splice_deterministic_findings_tables` `github_publish_formatter.py` | Replaces Moonshot `### This generation` / `### Still open on PR` sections with `format_summary_comment` (FR-Q7 parity; shipped wave C #68) |
| `pr_active_groups` loaded at publish | `_load_pr_active_groups` `github_publish.py:998–1010` | Passed into `PublishFormatContext` |
| Issue comment **in-place** update | `update_issue_comment` `github_publish.py:1304–1314` | Same `github_comment_id` per PR |
| Full PR diff per review | `compare_commits(base_sha, head_sha)` `github_review.py:779–786` | Not push-delta |
| Push-delta resolution stamp | `apply_resolution_status_for_synchronize` `github_resolution_metrics.py:115+` | G9 prose only |
| GH-1v2 thread collapse | `_fingerprints_to_resolve_inline_threads` `github_publish.py:614–662` | Option A + B + outdated |
| Test: check has two blocks | `test_build_check_run_summary_two_block` `test_github_publish_formatter.py:195–208` | |
| Test: issue comment **lacks** PR block | `test_build_pr_review_comment_fallback_generation_only_not_pr_block` `test_github_publish_formatter.py:222–239` | Documents gap — flip in P0 |

### Genuinely new (this program)

| Capability | Why new |
|------------|---------|
| Two-block **issue comment** | Fallback + Moonshot paths use generation-only `### Findings` today |
| PR-wide **verdict** on issue comment | `compute_confidence(ctx.groups)` / `_merge_recommendation(ctx.groups)` — generation-only |
| Moonshot prompt parity | `_build_issue_comment_user_prompt` sends generation active JSON only |
| Product bar for PR block | `_issue_comment_meets_product_bar` does not require `### Still open on PR` |

### Reuse traps

| Trap | Detail |
|------|--------|
| **Duplicate tables** | Reuse `format_summary_comment` — do not fork markdown builders |
| **Double-count rows** | Generation findings ⊆ PR active when reconcile is healthy; table rows may appear in both blocks by design (FR-Q7) |
| **Resolved in generation** | `publishable_groups_for_review_run` includes `resolved` groups for metrics — filter with `_active_groups` for tables |
| **Moonshot thin output** | Fallback must meet full bar; LLM path validated against same structure |
| **Moonshot table drift** | Moonshot may omit rows from “This generation” while listing them under “Still open on PR” on rev 1 — **mitigation:** `splice_deterministic_findings_tables` overwrites both tables from DB JSON (`#68`) |
| **`_insert_resolution_metrics_block`** | Keys off `### Findings` today — breaks after P0 removes that heading |
| **`ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT`** | Hardcodes `### Findings` step (7) — Moonshot will ignore two-block unless P1 rewrites |
| **Greptile contract tests** | `greptile_shape`, `collapses_info` assert `### Findings` — must update in P0 (PSA-D10) |

---

## Catalog — surface alignment matrix (today vs target)

| Surface | Generation scope | PR-wide scope | Verdict (confidence/merge) | Thread state |
|---------|------------------|---------------|----------------------------|--------------|
| Check run summary | **Yes** (block 1) | **Yes** (block 2) | Generation-only ⚠️ | N/A |
| Issue comment (fallback) | **Yes** (`### Findings`) | **No** ⚠️ | Generation-only ⚠️ | N/A |
| Issue comment (Moonshot) | Partial (prompt JSON) | **Yes** (after splice) | Generation-only ⚠️ | N/A |
| Inline comments | **Yes** | No | N/A | GH-1v2 resolve |
| G9 / resolution metrics | **Yes** | No | N/A | Informs “fixed since last push” |

**Target (PSA-D1–D2):** Issue comment = two-block findings + PR-wide verdict; check verdict also PR-wide for consistency.

---

## Edge cases

| Case | Current behavior | Target |
|------|------------------|--------|
| Prior finding active, not re-reported this run | Check lists it; issue comment omits; thread may stay open | Issue comment block 2 lists it; merge says not ready |
| Fix push — `addressed`, thread collapsed | G9 prose; thread resolved GH-1v2 | Unchanged |
| Clean generation, dirty PR | Issue: “no findings”; check block 2 may list open | Issue block 2 + merge warning |
| `pr_active_groups is None` | Check falls back to `ctx.groups` | Same fallback everywhere |
| Moonshot disabled | Fallback only | Fallback meets full contract |
| Info-only in generation + priority | Collapsed `<details>` in fallback | **PSA-D10:** flat table in block 1 only (matches check) |
| Check `conclusion` vs merge copy | `compute_check_conclusion(groups)` generation-only | **Unchanged (PSA-D12)** — advisory; merge/confidence PR-wide |
| Info-only prior open (not in generation) | Hidden in issue comment | Visible in block 2 |

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| PSA-Q1 | Extend FR-Q7 to issue comment? | **locked** | Yes — PSA-D1; completes FR-Q16 |
| PSA-Q2 | Verdict fields scope? | **locked** | PR-wide active — PSA-D2 |
| PSA-Q3 | G9 / resolution metrics scope? | **locked** | Generation-only — PSA-D3 |
| PSA-Q4 | Inline scope change? | **locked** | No — PSA-D4 |
| PSA-Q5 | New closure logic? | **locked** | No — PSA-D6 |
| PSA-Q6 | Moonshot system prompt change? | **locked** | **Required** in P1 — rewrite step (7) to two-block headings (PSA-D5) |
| PSA-Q7 | Migration? | **locked** | None |
| PSA-Q8 | Staging coupling? | **locked** | Parallel validation memos — PSA-D8 |
| PSA-Q9 | Info collapse UX? | **locked** | Flat two-block tables — drop info `<details>` (PSA-D10) |
| PSA-Q10 | `summary_json` scope? | **locked** | `confidence` + `active_count` PR-wide; add `generation_active_count` + `pr_active_count` (PSA-D11) |
| PSA-Q11 | Check `conclusion` scope? | **locked** | Generation-only — **out of scope** (PSA-D12) |

**Cross-ref:** FR-Q16 → **in flight** (this program). RG-14 → **in flight**.

---

## Advice / recommended path

| Phase | Outcome |
|-------|---------|
| **P0** | Shared `verdict_groups(ctx)`; fallback two-block; PR-wide verdict + rationale + `summary_json`; metrics markers; test updates |
| **P1** | Moonshot system + user prompt; product bar; check ≡ issue blocks |
| **P2** | Staging memo + doc sync (RG-14 closed, PRODUCT_PATTERNS row) |

**Reject:** Push-only review diff; append-style comment history; auto-close groups for display convenience.

---

## External research / patterns

| Source | Pattern | Adopt |
|--------|---------|-------|
| Greptile | Single summary updated per commit; open items visible until fixed | **Adopt** — two-block + thread resolve |
| Bugbot | Resolution rate on HEAD state | **Adopt** — verdict reflects PR-wide open |
| FR-Q7 (finding-resolution) | Two-block check + generation inline | **Complete** on issue comment |

---

## Data scope & exclusions

| In scope | Out of scope |
|----------|--------------|
| `github_publish_formatter.py`, Moonshot issue-comment path | Moonshot **review** JSON / RCX inject |
| Publish build `pr_active_groups` wiring | New reconcile/closure rules |
| Formatter + publish unit tests | Frontend UI (reviewer list already shows resolution) |
| Staging dogfood validation memo | Post-merge Bugbot batch (FR-Q10) |
| **`compute_check_conclusion`** generation scope | PSA-D12 — check may `success` while PR-wide merge warns; intentional advisory split |

---

## Parking lot

| Item | When |
|------|------|
| Check run verdict also PR-wide | **P0** — display confidence in check summary (not `compute_check_conclusion`) |
| `execution-peer-review` on waves | **Done** (2026-07-29) — gaps incorporated into P0/P1 execution |
| RCX / judge-json pass 2 monitoring | Parallel — operator |

---

## Devil's advocate

1. **Longer comments** — mitigated by row caps already in `format_summary_comment`.
2. **Duplicate rows across blocks** — acceptable per FR-Q7; generation = “new/changed this pass”.
3. **Moonshot ignores block 2** — product bar rejects thin output; fallback is canonical.
4. **False confidence after fix** — if group still `active` but addressed, GH-1v2 + G9 handle; display should still show block 2 until closed.
5. **Check conclusion vs merge** — PSA-D12; advisory check may `success` while merge warns — intentional.

---

## Architecture peer review (2026-07-29)

**Verdict:** Thesis and phase split sound; findings match code. **Gaps incorporated** into P0/P1 execution before LOOP.

| Severity | Item | Resolution |
|----------|------|------------|
| Critical | `_confidence_rationale` generation-only | P0.3 — verdict wiring |
| Critical | `_insert_resolution_metrics_block` `### Findings` marker | P0.4 |
| Critical | System prompt hardcodes `### Findings` | P1.2 — **required** |
| Critical | Greptile/collapse tests break on P0 | P0.2 — PSA-D10 + test updates |
| High | `summary_json` generation-scoped | P0.3 — PSA-D11 |
| High | Missing merge-regression test | P0.3 — `test_merge_recommendation_uses_pr_active_when_generation_clean` |
| High | Info collapse undecided | PSA-D10 locked |
| High | Check conclusion vs merge | PSA-D12 out of scope |

---

## Experiment / verification

| Experiment | Pass criteria |
|------------|---------------|
| Unit: two-block issue fallback | `app/legacy.py` in `### Still open on PR` when prior-only in `pr_active_groups` |
| Unit: confidence rationale PR-wide | Clean generation + prior PR error → rationale not “no active findings” |
| Unit: merge recommendation | Prior error-only PR → not “ready to merge” on generation-clean push |
| Unit: check ≡ issue blocks | Same `format_summary_comment` output embedded in both |
| Staging: fix → push → push | Issue block 1 updates; block 2 shrinks; threads collapse; G9 prose matches |
| Staging: parallel RCX gate | RCX memo pass 2 independent — no regression |

---

## References

| Area | Path |
|------|------|
| Formatter | `backend/app/services/github_publish_formatter.py` |
| Publish | `backend/app/services/github_publish.py` |
| Moonshot | `backend/app/integrations/moonshot_review.py` |
| Tests | `backend/tests/unit/test_github_publish_formatter.py` |
| FR-Q7 / FR-Q16 | `docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_FINDINGS.md` |
| RG-14 | `docs/review-pipeline/review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_FINDINGS.md` §3c |
| GH-1v2 | `docs/review-pipeline/github-surface-hardening/GITHUB_SURFACE_HARDENING_FINDINGS.md` §4c |
