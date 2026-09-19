# docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_GENERAL_PLAN.md

# Resolution honesty — general plan

**Baseline:** [RESOLUTION_HONESTY_FINDINGS.md](./RESOLUTION_HONESTY_FINDINGS.md) (RH-Q1–Q12 locked).  
**Prerequisite:** finding-resolution Pass 1–2 + PSR lifetime rollup on `main`.  
**Architecture:** pass-02 **BLOCK create-execution-plan: no.** Pass-01 locks stand. Pass-02 high is an H2 matching rule (ambiguous continuation), not a new RH-Q.

**Thesis:** Revy keeps **one group per claim**. A claim is **resolved** only when a successful compare shows the path gone or **zero** this-run findings in that file+category, or a judge **dismissed** it. GitHub Outdated is UI collapse only. Line drift updates `start_line` in place; it does not close-and-re-raise. Leftovers stay open while ≥ 1 finding remains.

**North star:** On a fix-some-leave-some push, lifetime **resolved** counts the fixes, **still open** counts the leftovers (same identities), this-push is **not** 0/0.

---

## Locked decisions

| Q# | Decision |
|----|----------|
| **RH-Q1** | Outdated ≠ resolved. H2 = compare ok **and** (path gone **or** this-run findings count == 0). |
| **RH-Q2** | Stop creating file+category `superseded`. Historical superseded stay excluded unless remapped. Resolved = H2 or dismiss. |
| **RH-Q3** | This-push prior set = last published **group ids**. Empty denom → N/A. |
| **RH-Q4** | Title out of identity. Unique key excludes `start_line`. Continuation updates the line attribute. Not “old line absent ⇒ resolved.” |
| **RH-Q5** | Never render 0/0 as 0%. |
| **RH-Q6** | Collapse GitHub when unbound/closed **or** (keep GH-Q9) Outdated. Numbers follow H2. |
| **RH-Q7** | Pass 1 stays line-region. |
| **RH-Q8** | Two in-run findings at the same path+category+line stay two groups (`claim_slot`). |
| **RH-Q9** | Pass 2 **without** Pass 1 `addressed`. **Supersedes FR-Q3.** Method `absent_and_addressed`; `path_removed` is a display bucket. H2 uses this-run **findings** count: close if 0 or path gone; skip if ≥ 1. P0 bind ≠ 1 is merge-only. |
| **RH-Q10** | P5 = equivalent **new** PR. Remap of dogfood #1’s 13 superseded rows is optional. |
| **RH-Q11** | Fingerprint rewrite and `github_inline_threads` keys = `group.id`. Same subphase: map, publishable, collapsed, generation, ever_inlined — one id space. |
| **RH-Q12** | Keep PSR-Q15: `raised == resolved + still_open_display + hidden_total`. |

**This program supersedes:** FR-Q3 / CS Option B; PSR `raised_count = state != superseded` (forward only); **R5-Q1** / D10 title+line fingerprint. **Does not supersede:** GH-Q9, PSR-Q15, FR-Q1 (vocabulary).

**What we will not do:** treat Outdated or a line-shifted leftover as fixed; H2-close leftovers while ≥ 1 this-run finding remains in that file+category; whole-file touch as addressed; drop rewritten titles from raised so the rate looks clean.

---

## Cross-cutting (every phase)

- **Unit tests** for continuation (line insert above `eval` stays one open group), **ambiguous continuation** (two same-file leftovers stay `still_open`), collision (`claim_slot`), Pass 2 without `addressed`, compare-fail does not close, PSR-Q15 identity, no duplicate inlines.
- **Lineage** in comment details: four-term equation; N/A labeled.
- **No product i18n** on GitHub markdown (English as today). Reviewer UI strings EN+LV if any labels change.
- **No silent close** on compare failure (`closure_blocked_reason` set).
- **Bind then H2.** Bind `claim_slot`, then exact line, then continuation iff **exactly one** unbound **group** in the set (same path+category, nearby). Then H2 only if path gone or this-run **findings** count == 0. FR-Q11 Pass 3 volume may drop for missed-line **fixes**; do not also H2-close leftovers while findings count ≥ 1.

---

## P0 — Persistent identity (cutover)

**Goal:** One group per claim when title, severity, or **line** changes. This phase **is** the D10 cutover, not calibration.

**Scope — in:** Drop title from identity; store `start_line` on the group; unique key **without** start_line (PR + path + category + `claim_slot`); bind order + candidate set; retire `_mark_superseded_peers`; handwritten Alembic after `0034`; dual lookup for one generation of old D10 hashes; migrate `github_inline_threads` keys to `group.id` **and** publishable / collapsed / generation / ever_inlined in the same change (RH-Q11). **Out:** Pass 2 predicate (P1), rollup copy.

**Deliverables:** INFO→CRITICAL rewrite and a one-line insert above `eval` keep one **open** group. Two same-line claims stay two groups. Two leftover same-category claims in one file are **not** merged (continuation skipped). No duplicate inline threads.

**Depends on:** `main`.

---

## P1 — Honest closure (H2)

**Goal:** Close a group when compare succeeded and the path is gone or this-run **findings** in that file+category are **zero**. Do not close because the GitHub hunk is Outdated, do not require Pass 1 `addressed` (RH-Q9), and do **not** close leftovers while ≥ 1 finding remains.

**Scope — in:** Pass 2 predicate `closure_blocked_reason is None` + (path gone **or** this-run finding count == 0); skip H2 when finding count ≥ 1; keep method `absent_and_addressed`; `path_removed` as display bucket; Pass 1 stays line-region. **Out:** this-push/lifetime formatter.

**Deliverables:** PAT / AWS / SELECT / innerHTML-class (line-miss) become `resolved` via Pass 2 when that file/category has **zero** this-run findings. Leftover `eval` after a line insert stays **open**. Two same-file leftovers stay **open**. Two same-file **fixes** both close.

**Depends on:** P0.

---

## P2 — This-push metrics

**Goal:** “Closed as fixed” and the rate use last published identities (`group.id`).

**Scope — in:** `resolution_pass` prior set (RH-Q3); N/A when denominator is 0 in **both** the manifest and `format_resolution_metrics_block`. **Out:** lifetime table.

**Deliverables:** Fix-some push shows closed ≥ the H2 closures this pair; never 0% of 0 when a prior review existed.

**Depends on:** P1.

---

## P3 — Lifetime rollup

**Goal:** Scan table matches H4 and PSR-Q15. New PRs do not create file+category superseded, so raised is not emptied by rewrite.

**Scope — in:** `build_pr_resolution_rollup` raised/resolved; hidden term kept. **Out:** remapping historical superseded (RH-Q10); GitHub thread mutations.

**Deliverables:** On a **new** PR after P0: raised = unique claims, resolved = H2 closures, still open = leftovers, four-term identity holds. Dogfood #1’s 13 superseded rows stay excluded unless a later remap.

**Depends on:** P2.

---

## P4 — Comment + GitHub threads

**Goal:** Author-facing comment and thread collapse agree with P1–P3.

**Scope — in:** Scan + details copy (RH-Q5, RH-Q12); Option A keyed on unbound or closed identity (RH-Q6). **Keep GH-Q9:** Outdated threads still collapse in the GitHub UI. **Out:** new GitHub App settings; counting Outdated as H2.

**Deliverables:** No “0% (0/0 prior active)”; details identity equation holds; threads collapse when the identity is unbound/closed **or** the hunk is Outdated (UI only).

**Depends on:** P3.

---

## P5 — Dogfood gates

**Goal:** Findings experiment table is pass or a named residual.

**Scope — in:** **Equivalent new PR** (RH-Q10): four fixes, leftovers, file delete, line-insert above `eval`, two same-file leftovers if present. **Out:** assuming #1’s superseded rows become the lifetime numerator.

**Deliverables:** Sign-off against the findings gates, including “same group still open” for the eval insert and “ambiguous leftovers not H2-closed.”

**Depends on:** P4.

---

**Next:** `execution-peer-review` on P0–P5, then `phase-execution` from P0.
