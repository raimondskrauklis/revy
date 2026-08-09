# PR summary rollup — P4 readability findings

**Program:** [README.md](./README.md) · **Baseline:** [PR_SUMMARY_ROLLUP_FINDINGS.md](./PR_SUMMARY_ROLLUP_FINDINGS.md) (P0–P3 shipped)

**Trigger:** Production dogfood on [kp-platform #501](https://github.com/raimondskrauklis/kp-platform/pull/501) (2026-08-09) — rollup math correct, **scan UX poor** when PR is long-lived and display-open is 0.

**Purpose:** Baseline for **P4** — clarify lifetime numbers to authors without changing rollup math or filter rules. **No execution steps.**

**Peer review:** [execution pass 2](./reviews/execution-peer-review/pass-02-2026-08-09.md) — **0 block**; splice boundary fix required in P4.1.

---

## Problem (observed)

On a clean merge (`still_open_display: 0`, tables empty), authors see:

```text
Raised on PR: 29
Resolved (lifetime): 17
  addressed: 11 · judge dismissed: 2 · path removed: 4
Still open (display): 0
Lifetime resolution rate: 100.0%
```

**Mental math fails:** `29 − 17 = 12` unaccounted for. Push block may still say `Still open from prior review: 1` while tables show none.

**Root cause (not a bug):** 12 groups remain `active` in DB but are **hidden from display** by PSA/SOS filters (`filter_snapshot`: 11 `collapsed_hidden`, 1 `orphan_never_inlined_hidden`). Lifetime rate uses **display** open count, not raw DB active count. Comment does not explain the gap.

**Verified reconciliation (#501):** `raised (29) = resolved (17) + still_open_display (0) + hidden_total (12)`.

---

## Author mental model (target)

| Bucket | Plain language | Typical cause |
|--------|----------------|---------------|
| **Raised** | Findings Revy ever tracked on this PR | All non-superseded groups |
| **Resolved** | Closed in review history | Fixed, dismissed, or file removed from PR |
| **Still open (display)** | Rows in `### Still open on PR` — **act on these** | Publishable actives after filters |
| **Hidden from display** | In history but no open GitHub thread to click | Thread collapsed after fix (GH-1v2); never inlined summary-only orphan |

**User hypothesis (partially right):** “Scanned, then file removed” → **`path_removed`** (counted under **Resolved**, not hidden). Hidden set is mostly **collapsed threads** + **orphans**, not path removal.

---

## UX direction (locked for P4 dogfood)

1. **Scan layer (always visible)** — merge decision + compact counts; **publishable status** line (PSR-Q13).
2. **Explain layer (`<details>`)** — verbose breakdown during testing; collapsed by default so expand/collapse supports “solved vs remaining” scanning.
3. **No math changes** — `raised_count`, `resolved_count`, `still_open_display`, rate formula unchanged (PSR-Q4).
4. **Do not list hidden rows in main tables** — breaks GitHub parity (PSA-D1).
5. **Post-P4 human gate** — trim default verbosity after operator sign-off (PSR-Q14).
6. **Check run** — `format_pr_rollup_check_one_liner` unchanged in P4 (compact only); full story stays in issue comment.

---

## Implementation lock (pass-01)

**Splice boundary:** `_replace_markdown_section` ends PR summary at `\n<details>` (`_SECTION_END_MARKERS` in `github_publish_formatter.py`). P4 puts `<details>` **inside** `format_pr_resolution_rollup_block()`. Without a dedicated PR-summary replace boundary, double splice (`build_pr_review_comment` + `apply_rollup_to_publish_surfaces`) can truncate or duplicate the breakdown.

**Fix (P4.1):** `_replace_pr_summary_section` (or equivalent) — section ends at next push/lifetime boundary (`\n\n**Since last push:**`, `\n### Resolution metrics`, `\n### Files needing attention`, `\n### This generation`), **not** inner `\n<details>`. Unit test: call `splice_deterministic_pr_summary_block` twice on a body that already contains the P4 block.

---

## Scope

| In | Out |
|----|-----|
| `format_pr_resolution_rollup_block()` scan + `<details>` copy | Rollup compute / migration |
| Hidden count from existing `filter_snapshot` | New DB fields |
| One-line push cross-ref **inside `<details>`** when `still_open_prior ≠ still_open_display` (PSR-Q16) | Push-block rewrite |
| Formatter + unit tests (update existing rollup/splice assertions) | Revy UI / i18n LV |
| Staging spot-check (#501-class PR) | Backfill old PR comments |
| Check-run one-liner | Hidden context on check run (deferred) |

---

## Proposed scan layer (draft copy)

```markdown
### PR summary (lifetime)

**Publishable status:** Nothing to act on in the tables below.

| | Count |
|--|--:|
| Raised on this PR | 29 |
| Resolved (lifetime) | 17 |
| Still open (in tables) | 0 |
| Hidden from tables | 12 |
```

When `still_open_display > 0`, status line: `N open — see Still open on PR`. When `display == 0` and `hidden > 0`, status may note hidden count briefly (PSR-Q13).

---

## Proposed `<details>` body (draft)

- Resolved breakdown (existing `resolved_by_method` labels).
- Hidden breakdown from `filter_snapshot`: collapsed / orphan / compare-failed.
- **Reconciliation** (guarded — PSR-Q15): print only when identity holds:
  - `raised == resolved + still_open_display + hidden_total`, **or**
  - use `filter_snapshot.raw_active_before_filters` and note `addressed`-pending actives when identity fails.
- Lifetime rate footnote: uses display open only.
- **Push cross-ref (PSR-Q16):** when `still_open_prior ≠ still_open_display`, one sentence: push block uses prior-revision filtered count; tables use display count.
- **PSR-Q9 disclosure:** `lifetime_disclosure` after scan table, before `<details>`.

---

## Decisions registry (P4)

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| PSR-Q11 | Show hidden count in scan layer? | **locked** | **Yes** when `collapsed_hidden + orphan_never_inlined_hidden + compare_failed_hidden > 0` |
| PSR-Q12 | Verbose breakdown placement | **locked** | `<details><summary>Lifetime breakdown</summary>` below scan table + disclosure; EN only |
| PSR-Q13 | Publishable status line | **locked** | `still_open_display == 0` → “Nothing to act on in the tables below” (not literal “All clear” when hidden > 0 — may add brief hidden hint); else “N open — see Still open on PR” |
| PSR-Q14 | Default verbosity after dogfood | **open** | Human gate P4.4 — trim scan table / details after operator sign-off |
| PSR-Q15 | Reconciliation sentence | **locked** | Print only when `raised == resolved + still_open_display + hidden_total`; else explain via `raw_active_before_filters` / addressed-pending note in `<details>` |
| PSR-Q16 | Push vs display mismatch | **locked** | **Cross-ref in `<details>` only** — no push-block rewrite in P4 |
| PSR-Q17 | Splice replace boundary | **locked** | Dedicated PR-summary section replace — inner `<details>` must not truncate block (P4.1) |
| PSR-Q18 | Moonshot lifetime prose | **locked** | Stub/omit scan table + `<details>` in LLM output; deterministic splice owns full P4 block |

---

## Verification (P4)

| Gate | Pass criteria |
|------|----------------|
| Unit | #501 fixture: raised 29 / resolved 17 / display 0 / hidden 12 → scan + details reconcile |
| Unit | `still_open_display > 0` → status line not “nothing to act on” |
| Unit | Hidden 0 → omit hidden row and details hidden section |
| Unit | Double `splice_deterministic_pr_summary_block` — no duplicate/truncated `<details>` |
| Unit | Update existing `test_format_pr_resolution_rollup_block_*` and splice-order tests for table layout |
| Staging | #501-class: expand `<details>` → explain `29 = 17 + 0 + 12` without reading code |
| Staging | Check run unchanged (optional note in memo — authors reading check only see one-liner) |

---

## References

| Area | Path |
|------|------|
| Formatter | `backend/app/services/github_publish_formatter.py` — `format_pr_resolution_rollup_block`, `_SECTION_END_MARKERS`, `splice_deterministic_pr_summary_block` |
| Filter audit | `backend/app/services/github_pr_resolution_rollup.py` — `compute_filter_snapshot` |
| Display filter | `filter_pr_active_groups_for_summary` (GH-1v2, SOS-5) |
| Case study PR | [kp-platform #501](https://github.com/raimondskrauklis/kp-platform/pull/501) rev 18 `8c7f8c6` |
