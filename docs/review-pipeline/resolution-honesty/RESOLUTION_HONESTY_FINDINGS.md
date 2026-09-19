# docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_FINDINGS.md

# Resolution honesty — findings

**Date:** 2026-09-19  
**Status:** baseline-ready — RH-Q1–Q12 locked; pass-02 matching rule (ambiguous continuation) applied. **BLOCK create-execution-plan: no.**  
**Purpose:** Baseline for making Revy’s **resolved / still open / this push / lifetime** story match reality. **No execution steps.**  
**Evidence:** code on `main` (post github-onboarding); production DB for `rtudatadev-dotcom/revy-dogfood` PR **#1** (workspace gaz-66); GitHub GraphQL threads; vendor docs.

**Related:** [finding-resolution](../finding-resolution/FINDING_RESOLUTION_FINDINGS.md) (FR-Q3 Pass 2, GH-1v2) · [pr-summary-rollup](../pr-summary-rollup/PR_SUMMARY_ROLLUP_FINDINGS.md) (PSR-Q1 lifetime vs FR-Q12 push) · [github-surface-hardening](../github-surface-hardening/GITHUB_SURFACE_HARDENING_FINDINGS.md) (outdated collapse).

---

## Build principles

1. **Never mislead.** A table that says “resolved 0” after the author fixed issues is a product bug, not a footnote problem.
2. **Separate channels stay named.** GitHub `isOutdated`, GitHub `isResolved`, `group.state`, `resolution_status`, and “not in this generation” are not one enum.
3. **Identity before metrics.** If the fingerprint changes, lifetime/push math will lie even when closure rules are correct.
4. **Two horizons, honest denominators.** This-push uses the **prior published set**. Lifetime raised after P0 is identities we persist; historical `superseded` rows stay out unless remapped (RH-Q10).
5. **Real data only.** Do not impute “fixed” from Outdated alone. Do not drop identities from “raised” because a later title string differed.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Identity (today)** | D10: workspace + PR + path + category + **title** + start_line (`github_finding_reconcile.py:49–70`) |
| **Identity (target)** | Persistent group. Unique key = PR + path + category + `claim_slot` (**not** start_line). Bind `claim_slot`, then exact line, then **continuation** (exactly one nearby candidate). |
| **Continuation candidate set** | Unbound groups, same path + category, not already bound this run, **nearby** (same file; line window is execution). |
| **Peer supersede** | Same file + category, other active group not last-seen this revision → `state=superseded` (`_mark_superseded_peers`) |
| **Pass 1** | `apply_resolution_status_for_synchronize` — stamps `addressed` / `still_open` from push compare + path hygiene |
| **Pass 2 (today)** | Close `active` only if fingerprint absent **and** `resolution_status=addressed` (FR-Q3) |
| **Pass 2 (target)** | Close if compare/HEAD ok **and** (path gone **or** this-run **findings** count in that file+category == 0). Does not require Pass 1 `addressed` (RH-Q9). Findings count ≥ 1 → leftovers stay `still_open`. |
| **This-push** | FR-Q12 `resolution_pass` — transitions on current revision vs prior published pairing |
| **Lifetime** | PSR rollup — `raised_count` = groups with `state != superseded`; `resolved_count` = those with `state=resolved` |
| **GitHub Outdated** | `reviewThread.isOutdated` — the **diff hunk moved**. Not “the bug is gone.” |
| **GitHub resolved** | `resolveReviewThread` — UI conversation closed. Revy also does this for Option A/B/outdated. |

---

## Dogfood snapshot (verified, production)

PR #1, two revisions: `a3c972a` (intentional issues) then `af6cfa9` (four fixes). Query 2026-09-19.

| Fact | Value |
|------|-------|
| Finding groups | **23** (13 first-gen + 10 second-gen) |
| `state` | 13 `superseded`, 10 `active`, **0 `resolved`** |
| `resolution_method` | **all null** |
| Pass 1 `addressed` | **2** (GitHub PAT line 4, AWS key line 5) — both then superseded |
| First-gen still `still_open` after the fix push | SQL SELECT (line 14; code changed line 16), innerHTML (line 4; code changed line 4), plus unfixed leftovers |
| Lifetime job 2 | `raised_count=10`, `resolved_count=0`, `still_open_display=10`, rate **0.0%** |
| This-push job 2 | comment **0.0% (0/0 prior active)**, **Closed as fixed: 0**; `summary_json.resolution_pass` absent (metrics live on reconcile pipeline artifact) |
| GitHub | First-gen INFO threads `isResolved=true` (several `isOutdated`); 10 new CRITICAL/ERROR threads open |

Author-visible: four issues gone from the tables. Product-visible: **nothing was resolved**, **nothing was raised before**, **0/0 this push**.

---

## What exists vs genuinely new

### Shipped (verified)

| Capability | Where | Honesty trap |
|------------|-------|----------------|
| Title fingerprint D10 | `github_finding_reconcile.py:49–70` | Title/severity rewrite = **new identity** |
| Peer supersede | `_mark_superseded_peers` `:73–98` | Same file+**category** (all these were `security`) → **whole file’s prior groups die** when any new finding lands |
| Lifetime excludes superseded | `github_pr_resolution_rollup.py:231–237` | PSR-Q lock: “Resolved superseded groups” out of raised **and** resolved |
| This-push excludes superseded | `build_resolution_pass_manifest` `:712–720` | Computed **after** reconcile supersede (`reconcile_tasks.py:101–114`) → empty cohort |
| Pass 2 needs addressed + absent | `github_finding_closure_rules.py:18–32` | Option A GitHub collapse does **not** close DB if Pass 1 missed (`github_publish.py:1411–1414`) |
| Path gone → addressed | `hygiene_path_gone` + Pass 1b | File delete works; **line-level gone** is only the hunk heuristic |
| Outdated → resolve GitHub thread | `_fingerprints_to_resolve_inline_threads` `:730–733` | Collapses UI; **does not** set `state=resolved` by itself |
| Comment copy | `github_publish_formatter.py:658–716` | Details admit push vs tables differ; **scan table still says resolved 0** |

### Genuinely new (this program)

| Gap | Why the dogfood lied |
|-----|----------------------|
| **Supersede hides fixes** | Two `addressed` groups never became `resolved`; they became `superseded` and vanished from lifetime |
| **This-push after supersede** | Denominator 0 even though 13 prior identities existed |
| **Title is identity** | INFO “Hardcoded GitHub PAT” vs later CRITICAL “Hardcoded admin credentials” are **different groups**; leftover bugs look brand new |
| **Line heuristic miss** | SELECT finding anchored line **14**; fix was line **16** → `still_open` then superseded |
| **Outdated ≠ fixed** | Revy already collapses outdated threads; counting that as lifetime resolved would **over-close** (industry: lines moved) |
| **File/code gone under-counted** | Path-delete hygiene exists; “snippet gone, file remains” is not Pass 2 without `addressed` |

### Reuse traps

| Trap | Detail |
|------|--------|
| “Just include superseded in raised” | Would inflate raised with replaced titles **and** real fixes unless you **classify why** superseded |
| “Outdated = resolved” | GitHub docs/practice: hunk moved; CodeRabbit Change Stack keeps **open / addressed / superseded / skipped** distinct |
| Reuse FR-Q12 rate for lifetime | Already forbidden (PSR). Tonight the **push** rate was also empty for a different reason |
| Option A = author fixed it | Fingerprint not publishable includes **title-changed re-report**, not only deletions |

---

## Causal chain (this PR)

```text
rev2 review uses new titles/severity
  → new fingerprints (10 active)
  → _mark_superseded_peers (file + security)
  → 13 first-gen groups superseded (2 of them had addressed)
  → compute_resolution_transitions ignores superseded
  → 0/0 this push
  → rollup raised = non-superseded = 10, resolved = 0
  → GitHub Option A resolves old threads (fingerprint ∉ publishable)
```

Pass 1 **did** see the PAT/AWS line edits (`addressed`). Closure never ran: Pass 2 requires `state=active` + addressed + absent; supersede flipped `state` first.

---

## Catalog — honesty workstreams

| Track | Question | Method |
|-------|----------|--------|
| **H1 Identity** | What is a finding across pushes? | Persistent group. Unique key PR+path+category+`claim_slot` (not start_line). Bind `claim_slot`, then exact line, then **continuation** (nearby, **exactly one** candidate). Title/severity/start_line update in place. |
| **H2 Closure** | When is it resolved? | Compare succeeded **and** (path gone **or** this-run findings count == 0 in that file+category). Pass 1 `addressed` is **not** required (supersedes FR-Q3). Findings count ≥ 1 → leftovers stay `still_open`. Outdated is **not** H2. Judge dismiss stays explicit. |
| **H3 This-push** | What is the prior set? | Last **published group ids** (RH-Q11), including groups this reconcile would have superseded historically. |
| **H4 Lifetime** | What is raised / resolved? | Raised = distinct identities ever seen **after P0** (no new file+category supersede). Resolved = H2 or dismiss. PSR-Q15: raised = resolved + still_open_display + hidden. Historical `superseded` rows stay excluded unless remapped. |
| **H5 GitHub** | What do we collapse? | Option A when identity gone or group closed. **Keep GH-Q9** Outdated **thread** collapse. Never count Outdated as H2 / lifetime resolved. |
| **H6 Copy** | What does the comment say? | Scan row “Resolved (lifetime)” must match H4. 0/0 this-push → **N/A** (no prior cohort), never **0%**. |

---

## Advice / options

| Option | Do | Do not |
|--------|----|--------|
| **RH-1 (recommended)** | Continuation identity; Pass 2 on path-gone or this-run findings count == 0; skip H2 when count ≥ 1; this-push from last published group ids; GH-Q9 UI only | Treat Outdated, old-line-absent, or leftovers as resolved |
| **RH-2** | Keep D10 title fingerprint; map “same file+category+nearby line” as continuation | Leaves INFO→CRITICAL as new raised every push |
| **RH-3** | Count all superseded as resolved | Counts title rewrites as author wins |

**Recommended:** RH-1. RH-3 would make tonight look “13 resolved” including unfixed leftovers that were only retitled.

---

## External research / patterns

| Source | Pattern | Adopt / reject |
|--------|---------|----------------|
| [Outdated means the lines moved](https://jonroosevelt.com/blog/outdated-means-the-lines-moved-not-that-you-fixed-it/) | `isOutdated` ≠ fixed; `require_conversation_resolution` still counts unresolved outdated threads | **Reject** Outdated-as-resolved. **Adopt** explicit `isResolved` for GitHub UI |
| GitHub GraphQL `isOutdated` | Hunk/commit position changed | **Adopt** as UI collapse signal only (already GH-Q9) |
| [CodeRabbit Change Stack](https://docs.coderabbit.ai/change-stack/findings) | Drivers: **open / addressed / superseded / skipped** — skipped ≠ fixed | **Adopt** four-way status; skipped/rewrite must stay visible |
| CodeRabbit `@coderabbitai resolve` | Human/bot **explicit** resolve all threads | **Defer** command; don’t auto-resolve meaning “fixed” |
| Cursor Bugbot / Greptile | Resolution rate = flags **fixed or dismissed**, not comment volume | **Adopt** as north star — tonight’s 0% is the opposite |
| FR findings (this repo) | Path F: outdated collapses GitHub, **no DB resolved** | **Confirmed** still true (`github_publish.py:1411–1414`) |

**Push-back on “Outdated = resolved”:** agree on **file gone** and **snippet not re-reported**. Disagree that GitHub’s Outdated badge is sufficient. A one-line insert above a still-vulnerable `eval()` makes the old thread Outdated and leaves the bug.

**Agree on “code or file gone”:** that is H2 (compare ok + path gone **or** zero continuation candidates). Continuation must run **before** that test. Ambiguous leftovers (≠ 1 candidate) stay open. We **under-count** today because title identity + file+category supersede + FR-Q3 (`addressed` required) run first.

---

## This program supersedes

| Prior lock | Keep / replace |
|------------|----------------|
| **FR-Q3** / CS Option B | **Replace.** Pass 2 closes when compare ok and identity unbound. Method stays `absent_and_addressed`. |
| **PSR** `raised_count` = `state != superseded` | **Replace forward.** Stop creating those rows. Historical superseded stay excluded (RH-Q2, RH-Q10). |
| **PSR-Q15** four-term identity | **Keep.** |
| **GH-Q9** Outdated thread collapse | **Keep.** Do not count as H2. |
| **R5-Q1** / D10 (title + start_line in fingerprint) | **Replace** (RH-Q4). Not FR-Q1 (that is product vocabulary). |

---

## Data scope and exclusions

**In:** `github_finding_groups` / findings / reconcile / Pass 1–2 / publish formatter / rollup / GH-1v2. Production dogfood PR #1.

**Out:** Moonshot prompt quality (INFO vs CRITICAL on the same bugs) except as it **feeds** identity churn. Human dismiss UI. Post-merge loops.

---

## Edge cases

| Case | Today | Honest target |
|------|-------|----------------|
| Fix line N, finding anchored N-2 | `still_open` → superseded | Unbound after continuation → H2 if **zero** candidates (RH-Q9) |
| Delete file | Path hygiene addressed → Pass 2 if still active | Lifetime resolved `path_removed` bucket |
| Retitle same bug | New group + supersede old | Same identity, still_open |
| Line insert above `eval` | GitHub Outdated; today may supersede | **Same group still open** (continuation binds). Must not H2-close the old line and raise a new identity. |
| Two leftovers same path+category (≠ 1 candidate) | Peer supersede / title churn | Continuation skipped. **Do not H2-close** those leftovers (`still_open`). Close only if zero candidates or path gone. |
| Two findings same path+category+line | Title kept them distinct | Stay two groups (`claim_slot`). Continuation does not merge when two candidates. |
| First publish | this-push N/A | Keep N/A, not 0% |
| Compare fail | `still_open` + blocked reason | Say blocked, don’t imply 0 fixed |

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| RH-Q1 | Is GitHub Outdated product-resolved? | **locked** | **No.** H2 = compare succeeded and (path gone **or** this-run findings count == 0). Outdated is UI only. Leftovers stay open while findings count ≥ 1. |
| RH-Q2 | Do superseded groups count in lifetime raised/resolved? | **locked** | **This program supersedes** PSR `raised_count = non-superseded` for **new** groups: stop creating file+category superseded. Historical superseded **stay excluded** unless an explicit remap. Resolved = H2 or dismiss only. |
| RH-Q3 | Compute this-push before peer supersede? | **locked** | Prior set = last **published identities**. Empty denominator → **N/A**, not 0%. After P0, peer supersede is gone so 0/0 from that path stops for new PRs. |
| RH-Q4 | Title and start_line in fingerprint? | **locked** | Title **out**. Start_line is an **attribute** on the group, updated by continuation. Unique key **excludes** start_line (PR + path + category + `claim_slot`). Exact-line bind, then nearby unique candidate. **Not** “absent old line ⇒ resolved + new line ⇒ new raised.” |
| RH-Q5 | Render 0/0 as 0%? | **locked** | **N/A** when denominator is 0. |
| RH-Q6 | Option A vs Outdated threads? | **locked** | Collapse when identity unbound or group closed. **Keep GH-Q9** Outdated thread collapse. Numbers follow H2, not `isOutdated`. |
| RH-Q7 | Widen Pass 1 region? | **locked** | **No** whole-file touch. Pass 1 stays line-region. |
| RH-Q8 | Two claims, same path+category+line? | **locked** | Stay **two groups**. Frozen `claim_slot` at birth (normalized title hash). Continuation only if **exactly one** candidate. |
| RH-Q9 | Pass 2 without Pass 1 `addressed`? | **locked** | **Yes.** **Supersedes FR-Q3.** Predicate: `closure_blocked_reason is None` **and** (path gone **or** this-run findings count == 0) → `resolved` + `absent_and_addressed`. Skip H2 when findings count ≥ 1. P0 bind “≠ 1 **groups**” is merge-only, not the close predicate. `path_removed` is a display bucket. |
| RH-Q10 | Dogfood #1 remap vs new PR? | **locked** | P5 = **equivalent new PR** after P0–P4. Remap of the 13 superseded D10 rows is **optional**, not assumed. |
| RH-Q11 | Inline thread map keys? | **locked** | Keys = `group.id`. Dual-read old 64-hex fingerprints on load. **Same P0.4 change:** map, publishable, collapsed, generation, ever_inlined — one id space. No duplicate inlines. |
| RH-Q12 | PSR-Q15 four-term identity? | **locked** | Keep `raised == resolved + still_open_display + hidden_total`. Not a three-term scan equation. |

---

## Parking lot

- Reviewer/judge **severity flip** (INFO fixture → CRITICAL) is a quality issue; identity+continuation must absorb it.
- `innerHTML` line 4 stayed `still_open` after an edit — unit-test compare mapping (not only SELECT 14 vs 16).
- `resolution_pass` often missing from publish `summary_json`; comment reads the pipeline artifact.

**Phase-0 prerequisites:**

- RH-Q1–Q12 locked; pass-02 matching rule applied (2026-09-19). Architecture **BLOCK create-execution-plan: no**.
- Named supersedes: **FR-Q3** / CS Option B; **PSR raised = non-superseded** (forward only); **R5-Q1** / D10 title+line fingerprint. **Not** GH-Q9. **Not** FR-Q1.
- P0 **is** the D10 cutover. H2 skips leftovers when continuation candidate count ≠ 1.
- Do not “fix the footnote” without identity + Pass 2 predicate + rollup.

---

## Devil's advocate

- **“Peer supersede is working as designed.”** For “two findings same file, keep the newer.” It is the wrong tool for “Moonshot renamed the title.” Design was file+category, not claim identity.
- **“PSR already excluded superseded.”** Yes — and that lock is what made tonight’s comment honest to the **schema** and false to the **author**.
- **“Closing on Outdated is what authors want.”** Until a line-shift leaves a CRITICAL `eval` in place with a green lifetime rate.
- **“start_line in the hash + absent after compare.”** Same lie as Outdated: old line resolved, new line raised. Continuation exists so that cannot happen.
- **“Unbound ⇒ resolved.”** False when two same-category leftovers share a file: continuation sees ≠ 1 candidate and must **not** H2-close them.

---

## Experiment / verification

**P5 uses an equivalent new PR**, not a replay of #1’s superseded rows (RH-Q10).

Pass only if **all** hold:

| Gate | Pass | Fail |
|------|------|------|
| Four real fixes | Lifetime resolved ≥ 4 (PAT, AWS, SELECT, innerHTML) via H2, including Pass 2 **without** Pass 1 `addressed` | resolved 0 |
| Leftovers | Still open = remaining **unique claims**, not “brand new” titles. Two same-file leftovers stay open when continuation is ambiguous | Duplicate identities as new raised; leftovers H2-closed because unbound |
| This-push | Closed as fixed ≥ H2 closures; denominator ≠ 0 if a prior review existed | 0/0 shown as 0% |
| File delete | Extra resolved counted in `path_removed` **bucket** | stays open |
| Line insert above `eval` | **Same group still open** (continuation) | Old line H2-closed and a new identity raised |
| Copy | No “0% of 0 prior”; PSR-Q15 identity holds | details contradict the table |

---

## References

- `backend/app/services/github_finding_reconcile.py` (`compute_fingerprint`, `_mark_superseded_peers`)
- `backend/app/services/github_pr_resolution_rollup.py` (`build_pr_resolution_rollup`)
- `backend/app/services/github_resolution_metrics.py` (`apply_resolution_status_for_synchronize`, `build_resolution_pass_manifest`)
- `backend/app/services/github_finding_closure_rules.py`
- `backend/app/services/github_publish.py` (`_fingerprints_to_resolve_inline_threads`, `_close_active_groups_for_fingerprints`)
- `backend/app/services/github_publish_formatter.py` (`format_pr_resolution_rollup_block`, `format_resolution_metrics_block`)
- `backend/app/workers/reconcile_tasks.py` (resolution_pass after reconcile)
- Production: `github_finding_groups` for PR `01a0baec-ac0f-7322-93af-8c70b2473b90`
- [finding-resolution findings](../finding-resolution/FINDING_RESOLUTION_FINDINGS.md) § catalog D/F
- [PR summary rollup findings](../pr-summary-rollup/PR_SUMMARY_ROLLUP_FINDINGS.md) PSR-Q9 / superseded exclusion
