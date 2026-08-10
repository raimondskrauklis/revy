# Review generation lifecycle — dogfood log (PR #54)

**PR:** [#54](https://github.com/raimondskrauklis/revy/pull/54) · **branch:** `feat/review-generation-lifecycle` · **not merged to `main`**
**Last HEAD:** `f055f4a` — P0 + P1 + merge `main` (#53) + Moonshot formatter fix
**Distilled:** [CODE_REVIEW_LEARNINGS § PR #54](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md#dogfood-log--pr-54-generation-lifecycle--moonshot-format)

---

## Push chronology

| SHA | When | What | Greptile | Revy |
|-----|------|------|----------|------|
| `5709fd7` | rev 1 | P0 foundations | 3× P2 threads; conf **4/5** | ERROR supersede + WARNING resolve N+1; raw JSON issue comment |
| `2e84978` | rev 2 | P1 HEAD gates + merge + babysit fixes | Summary → conf **5/5**; 2 threads resolved | Stale ERROR supersede; INFO dup logic |
| `f055f4a` | rev 3 | `complete_issue_comment_markdown` | conf **5/5**; notes Moonshot split | Proper markdown summary; new WARNING JSON wrapper + ERROR null guard |

**Checks (rev 3):** CI SUCCESS · Greptile SUCCESS · Revy NEUTRAL (3/5)

---

## Summary comment comparison (rev 3, `f055f4a`)

| | Greptile | Revy |
|---|----------|------|
| **Format** | HTML + mermaid sequence diagram | Markdown tables + sections |
| **Confidence** | **5/5** — safe to merge, additive | **3/5** — address errors first |
| **Scope read** | P0+P1 gates + Moonshot refactor understood | Mixed — cites fixed supersede bug + new formatter edge case |
| **Files needing attention** | None (minor dead guard) | 3 files flagged |

Greptile summary updated through `f055f4a`. Revy issue comment **fixed** from raw `{"review_comment":…}` (rev 1–2) to formatted markdown (rev 3).

---

## Open inline threads (rev 3)

| Bot | Sev | Path | Verdict | Notes |
|-----|-----|------|---------|-------|
| Revy | ERROR | `github_generation_lifecycle.py:54` | **False positive** | Still describes `id != keep_revision_id`; code uses `revision_number < keep` since `2e84978` |
| Revy | WARNING | `github_publish.py:489` | Defer | Outdated on `5709fd7`; resolve N+1 pre-existing |
| Revy | INFO | `github_generation_lifecycle.py:73` | Defer P5 | Extract shared supersede helper + trace fields |
| Revy | WARNING | `github_publish_formatter.py:48` | **Valid** | `_looks_like_json_wrapper` too broad — tighten to known keys |
| Revy | ERROR | `github_publish.py:709` | **False positive** | `run is None` checked at lines 711–715 before `is_review_run_superseded` |
| Greptile | P2 | `config.py` | Fixed | Resolved — clamp warning |
| Greptile | P2 | rename helper | Fixed | Resolved — `mark_active_*`; thread outdated |
| Greptile | P2 | test flush | Fixed | Resolved on `f055f4a` |

---

## Distillation IDs (see learnings RC-D13+)

| ID | Topic |
|----|-------|
| **RC-D13** | Moonshot `json_object` on format path → raw JSON on GitHub |
| **RC-D14** | Revy vs Greptile complementarity on lifecycle PR |
| **RC-D15** | Stale inline threads after fix push |
| **RC-D16** | `_looks_like_json_wrapper` scope |
| **RC-D17** | Dedicated LLM completion per output shape (findings JSON vs issue markdown) |

---

## Improvements backlog (study — not scheduled)

| Area | Observation | Product / code direction |
|------|-------------|---------------------------|
| **Publish formatter** | Separate Moonshot calls for findings vs narrative | **Shipped** `complete_issue_comment_markdown`; tighten wrapper guard |
| **Revy re-review** | Carries prior finding text without re-reading fixed lines | Resolution / diff-aware re-review (RQ5+); or close stale threads manually |
| **Greptile** | Reads program docs + sequence diagram; high merge confidence when additive | Keep `.greptile/files.json` wired per program |
| **Revy inline** | ERROR on cross-layer paths (publish + lifecycle) | Good for pre-P2 wiring; expect false positives on already-guarded code |
| **Lifecycle P2** | Supersede wired to webhooks on `main` (#54); index-job + deferred resolution hotfix [#89](https://github.com/raimondskrauklis/revy/pull/89) | Staging proof — push during run |

---

## When to update

- After each push on #54 or successor PR until P5 dogfood row complete
- After merge to `main` — move summary row to [PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) snapshot row → **shipped** / **in flight**
