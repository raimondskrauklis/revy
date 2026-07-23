---
name: author-market-screen-corpus
description: >-
  Author CPV market screen (IND-*-CPV) methodology in corpus/platform/en/.
  Wraps author-corpus with code paths, layering, ownership matrix, and
  chart_methodology twin rules. Use for any -CPV screen page or market tier-2
  chart doc — not for lot indicators or -SCOPE screens.
---

# Author market screen corpus

**Prerequisite:** Read and follow [`author-corpus`](../author-corpus/SKILL.md) (manifest, eval, ship checklist).

**Program:** `docs/corpus_implementation/market_screens/` — inventory, **[`AGENT_BRIEF.md`](../../../docs/corpus_implementation/market_screens/AGENT_BRIEF.md)**, findings § Corpus split policy.

**Split rule (RAG):** Default **one screen → one L2 file**. L1 catalog lists all screens for non-chart questions. Family batch **only** when one `chart_id` serves multiple screens (M2: C14+C15 `moments`). Never a nine-screen formula megadoc.

**Terminology (locked):**

| Say | Code |
|:---|:---|
| **market screen** | `IND-*-CPV`, `AnalysisLevel.market_cpv` |
| **lot indicator** | `IND-*` without suffix, `tender_lot` |
| **scope screen** | `IND-*-SCOPE`, `historical` |

---

## Before you write — decision tree

```
Is the screen already covered at L2 depth?
├── N08, N41, N42 → dedicated advisory MD — STOP (link only)
├── N06, N37–N40 → network-rotation batch MD — STOP unless M3 retrieval miss
├── Catalog row only → needs L2? Check findings inventory
└── No L2 yet → proceed (filename below)
```

**Source of truth for active codes:** `backend/app/constants/indicator_pools.py` → `_MARKET_CPV_INDICATORS` (22 screens).

---

## Mandatory code reads (by family)

Read the **compute_*_screen** function and its insufficient branch.

| Family | Codes | Engine module | Also read |
|:---|:---|:---|:---|
| Allocation / HHI | M01, M07, M08, M09 | `market/engine/concentration.py` | `accumulate_win_values` |
| Single-bid | M06 | `market/engine/allocation_context.py` | |
| Price / dist | C01, C03, C11–C17 | `market/engine/price_distribution.py` | `conspicuous.py` for C16 |
| Network | N06, N37, N38 | `market/engine/network.py` | `MARKET_NETWORK_BREACH_CODES` |
| Rotation RD | N39, N40 | `market/engine/rotation_rd.py` | |
| Advisory N08 | N08 | PG batch / communities | existing advisory MD |
| Advisory N41/N42 | N41, N42 | ML / econometric batch | existing advisory MD |

**Shared (every scored screen):**

- `backend/app/constants/market_support.py` — `SCREEN_SUPPORT_GATES`, `SCREEN_DIRECTIONS`, `SCREEN_BAND_LADDERS`, `MARKET_ADVISORY_SCREEN_CODES`
- `backend/app/constants/market_scoring.py` — `MARKET_SCREEN_WEIGHTS`
- Universe rules — link [`cpv-market-exclusions-universe-a-b-participant-counts.md`](../../../corpus/platform/en/cpv-market-exclusions-universe-a-b-participant-counts.md); verify A vs B in engine inputs

**Charts / GenAI:**

- `backend/app/resources/genai/chart_methodology.yaml` — chart block for this screen
- `backend/app/services/genai/composer/market_chart_summary.py` — reader mapping

---

## Layering — do not duplicate

| Topic | Owner corpus file | Your L2 page |
|:---|:---|:---|
| Q16, CPV2/CPV4 | `cpv-market-definition-…` | link |
| Universe A/B tables | `cpv-market-exclusions-…` | link |
| `market_risk` composite | `cpv-market-monitoring-overview-…` | link |
| Screen list + gate summary | `cpv-market-screen-catalog-…` | link; add **See also** from catalog side |
| Grain suffixes | `platform-grain-…` | link |
| **This screen’s formula** | **your L2 file** | own |
| **Bands vs breach vs percentile** | **your L2 file** if screen has bands | own |
| **chart_id bundle semantics** | L2 or L3 chart doc | own when chart-heavy |

Full matrix: `docs/corpus_implementation/market_screens/MARKET_SCREEN_CORPUS_FINDINGS.md` § Content ownership.

---

## L2 filename + doc_id

```text
cpv-market-screen-{code-kebab}-{short-slug}.md
```

**`doc_id` pattern (locked):** `platform:cpv_market_ind_{code}:en` — allocation `m06`…`m09`, price `c01`…`c17`, paired `c14_c15`; slug suffix only when already shipped (`m01_hhi`).

| Rule | Example |
|:---|:---|
| Default | `IND-M07-CPV` → `platform:cpv_market_ind_m07:en` |
| Slug suffix only when already shipped | `IND-M01-CPV` → `platform:cpv_market_ind_m01_hhi:en` (**never rename**) |
| ❌ Do not use | `platform:cpv_market_screen_ind_m07:en` (alternate pattern retired) |

| Code | File | doc_id |
|:---|:---|:---|
| `IND-M01-CPV` | `cpv-market-screen-ind-m01-hhi-allocation.md` | `platform:cpv_market_ind_m01_hhi:en` |
| `IND-M06-CPV` | `cpv-market-screen-ind-m06-single-bid-share.md` | `platform:cpv_market_ind_m06:en` |
| `IND-C03-CPV` | `cpv-market-screen-ind-c03-benford.md` | `platform:cpv_market_ind_c03:en` |
| `IND-C14`, `C15-CPV` | `cpv-market-screen-ind-c14-c15-moments.md` | `platform:cpv_market_ind_c14_c15:en` |

---

## L2 section checklist (scored screen)

Copy structure from exemplar `cpv-market-screen-ind-m01-hhi-allocation.md`:

1. **Screen identity** — code, grain, scored/advisory, worse direction, lot analogue warning
2. **What it measures** — universe (A or B) with link to exclusions doc
3. **Formula and scale** — from engine; insufficient_data conditions
4. **Support gate** — `SCREEN_SUPPORT_GATES[code]` metric + minimum
5. **Interpreting the number** — split:
   - raw `numeric_value`
   - `SCREEN_BAND_LADDERS` / literature bands (**reference only**)
   - breach badge vs calibrated threshold (**from live JSON**)
   - percentile + `SCREEN_DIRECTIONS`
6. **Entity grouping** — if chart supports raw/owner/network
7. **Tier-2 chart** — `chart_id`, bundle composer, Lorenz/cumulative warnings
8. **Workspace reading** — UI labels → meaning (link overview for `market_risk`)
9. **What not to claim** — screen-specific mistakes (see HHI exemplar)
10. **References (code)** — bullet paths

**Advisory screens (N08, N41, N42):** already authored — only extend on retrieval failure with program approval (M3).

---

## Band ladders and GenAI

If `SCREEN_BAND_LADDERS` has an entry for your code:

- Corpus must state the **exact** thresholds from Python (not DOJ from memory).
- If `chart_methodology.yaml` lists `reference_numbers` / `literature_bands`, corpus **must agree** on scale and points.
- Always separate **breach_band labels** from **KP breach threshold** in investigator prose.

---

## Manifest

```yaml
indicator_codes:
  - IND-M01-CPV   # exact codes this page defines
metadata:
  domain_prefix: cpv-market
```

---

## Eval pairs (required)

Add to `corpus/eval/en/methodology_qa.yaml`:

1. **Definition** — formula, universe, gate.
2. **Interpretation** — bands vs breach, or worse direction, or chart caveat.

Tags should include `cpv_market` and screen code slug (`ind_m01`, etc.).

---

## Catalog sync

In `cpv-market-screen-catalog-ind-cpv-scored-and-advisory.md`, add to the screen’s table row:

```markdown
| `IND-M01-CPV` | HHI … | Higher — **deep:** [cpv-market-screen-ind-m01-hhi-allocation.md](./cpv-market-screen-ind-m01-hhi-allocation.md) |
```

Do **not** paste the formula into the catalog.

---

## chart_methodology.yaml sync

When shipping L2 for a chart that currently points at `platform:cpv_market_screen_catalog:en`:

```yaml
  concentration_partshare:
    indicator_code: IND-M07-CPV
    corpus_doc_id: platform:cpv_market_screen_ind_m07:en   # update to new doc_id
```

Same PR: backend YAML + `docs/GenAI/chart_methodology.yaml` mirror if repo keeps both.

---

## Batch vs per-screen

| Shape | When | Examples |
|:---|:---|:---|
| **Per-screen L2** | Default — chart Explain, distinct gates/universe | M0 M01, M1 M06–M09, M2 C01/C03/C11–C13/C16/C17 |
| **Family L2 (2 screens)** | One `chart_id` → multiple screens | M2: C14+C15 → `cpv-market-screen-ind-c14-c15-moments.md` |
| **L1 family batch** | Same investigator workflow, no chart-pin need | M3: N06–N40 network-rotation (keep unless retrieval miss) |
| **L1 catalog** | Full screen list, no formulas | Already exists — use for “which screens?” |

❌ **No** `cpv-market-screens-price-universe-a.md` with all nine formulas. ❌ **No** allocation-universe-b batch for M06–M09.

---

## Ship

Complete [`author-corpus`](../author-corpus/SKILL.md) ship checklist, then:

- [ ] Findings inventory row → L2 done
- [ ] Catalog See also updated
- [ ] `chart_methodology.yaml` `corpus_doc_id` updated (if chart)
- [ ] `rg 'IND-{code}-CPV' corpus/` — formula only in L2 owner
