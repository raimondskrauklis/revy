---
name: author-lot-indicator-corpus
description: >-
  Author tender_lot (IND-* without suffix) methodology in corpus/platform/en/.
  Wraps author-corpus with code paths, L0/L1/L2 layering, and split policy
  aligned with cpv-market screen corpus. Use for lot indicator pages — not
  for -SCOPE or -CPV screens.
---

# Author lot indicator corpus

**Prerequisite:** Read and follow [`author-corpus`](../author-corpus/SKILL.md) (manifest, eval, ship checklist).

**Program:** `docs/corpus_implementation/` — [`AGENT_BRIEF.md`](../../../docs/corpus_implementation/AGENT_BRIEF.md), [`INDICATOR_CORPUS_FINDINGS.md`](../../../docs/corpus_implementation/INDICATOR_CORPUS_FINDINGS.md) §Catalog.

**Split rule (RAG):** Default **one active lot indicator → one L2 file** owns the formula. **L1 master catalog** lists all codes for “which indicators exist?” — **no formulas** in the catalog. Family batch **only** for locked pairs/clusters below. Never a nine-indicator category megadoc.

**Terminology (locked):**

| Say | Code |
|:---|:---|
| **lot indicator** | `IND-*` (no suffix), `AnalysisLevel.tender_lot` |
| **scope indicator** | `IND-*-SCOPE`, `historical` | use `author-scope-screen-corpus` when added |
| **market screen** | `IND-*-CPV` — use `author-market-screen-corpus` |

---

## Before you write — decision tree

```
Is the code already covered at L2 depth?
├── KNAB-01…05 → L1 twin-parity page only — STOP (no five L2 pages)
├── Task is “list all lot indicators” → L1 catalog — STOP (no formulas)
└── No L2 yet → proceed (filename below)
```

**Source of truth for active codes:** `backend/scripts/seed_analytics.py` (`is_active`, `analysis_level = tender_lot`) + `indicator_pools.py`.

---

## Mandatory code reads (by family)

Read the **calculator method** and insufficient branch — not seed prose alone.

| Family | Codes (active) | Engine module | Also read |
|:---|:---|:---|:---|
| Price | C01–C05, C08–C10 | `calculators/price_calculator.py` | `cpv_thresholds.py` (DB L2 chain) |
| Time | T01, T05 | `calculators/time_calculator.py` | |
| Behavior | U01, U02, U04–U09, U11 | `calculators/behavior_calculator.py` | financial normalized U04–U06 |
| Market | M01, M02, M06 | `calculators/market_calculator.py` | HHI pick-one contract tests |
| Network | N01–N03, N06, N10, N23–N25, N28, N33, N34, N36 | `calculators/network_calculator.py` | `cross_operator_submission_ip.py` |
| Qualitative | Q03 | document pipeline | `calculation_type: llm`, not `IndicatorCalculator` |

**Shared (every lot page):**

- `backend/app/constants/indicator_pools.py` — `INDICATORS_ALL`, `INDICATORS_FRAMEWORK`
- Scan exclusions — link L0 [`indicator-lot-framework-pools-and-scan-exclusions.md`](../../../corpus/platform/en/indicator-lot-framework-pools-and-scan-exclusions.md)
- Grain — link [`platform-grain-lot-scope-historical-and-cpv-market-levels.md`](../../../corpus/platform/en/platform-grain-lot-scope-historical-and-cpv-market-levels.md)

**No `chart_methodology.yaml` twin** for lot indicators today — eval pairs only.

---

## Layering — do not duplicate

| Topic | Owner corpus file | Your L2 page |
|:---|:---|:---|
| Three grains / suffix rule | `platform-grain-…` | link |
| Framework pool + scan exclusions | `indicator-lot-framework-pools-…` | link |
| Full active list | `indicator-lot-catalog-active-indicators` | link |
| **This indicator’s formula + gates** | **your L2 file** | own |
| CPV market twin | `cpv-market-screen-*` | link when `-CPV` exists |
| Scope twin | `scope-screen-ind-*-scope` (P2) | link when `-SCOPE` exists |

Full matrix: `docs/corpus_implementation/INDICATOR_CORPUS_FINDINGS.md` §Catalog.

---

## L2 filename + doc_id

```text
indicator-lot-ind-{code-kebab}-{short-slug}.md
```

**`doc_id` pattern (locked):** `platform:indicator_lot_ind_{code_lower}:en`

| Code | File (pattern) | doc_id |
|:---|:---|:---|
| `IND-C01` | `indicator-lot-ind-c01-coefficient-of-variation.md` | `platform:indicator_lot_ind_c01:en` |
| `IND-N10`, `IND-N36` | `indicator-lot-ind-n10-n36-submission-ip-exact-vs-subnet.md` | `platform:indicator_lot_ind_n10_n36:en` |
| `IND-U04`–`U07` | `indicator-lot-ind-u04-u07-financial-capacity-normalized.md` | `platform:indicator_lot_ind_u04_u07:en` |

---

## L2 section checklist (lot indicator)

Copy structure from exemplar [`cpv-market-screen-ind-m01-hhi-allocation.md`](../../../corpus/platform/en/cpv-market-screen-ind-m01-hhi-allocation.md) — adapt for lot grain:

1. **Indicator identity** — code, `tender_lot` grain, global scan vs excluded, worse direction
2. **What it measures** — one paragraph; link pools/exclusions L0
3. **Formula and scale** — from calculator; insufficient-data conditions
4. **Threshold resolution** — CPV2 → CPV4 → default (`cpv_thresholds.py`); seed default as reference only
5. **Interpreting the number** — raw value vs breach; no live lot scores in corpus
6. **Twin caveat** — link scope/CPV pages when same base code differs
7. **What not to claim**
8. **References (code)** — bullet paths

---

## Batch vs per-indicator

| Shape | When | Examples |
|:---|:---|:---|
| **Per-indicator L2** | Default — distinct formula or gate | C01, M01, N06, U01, Q03 |
| **Family L2 (2 codes)** | Same investigator workflow, paired contrast | N10 + N36 (exact IP vs /24) |
| **Family L2 (cluster)** | Shared calculator module, `##` per code | U04–U07 financial normalized |
| **L1 catalog** | Full active list, no formulas | `indicator-lot-catalog-active-indicators.md` |
| **L1 KNAB parity** | Twin codes, zero extra logic | `indicator-lot-knab-twin-parity-…` |

❌ **No** `indicator-lot-catalog-price-ind-c-t-series.md` with eight formulas. ❌ **No** category megadocs.

---

## L1 catalog sync

In `indicator-lot-catalog-active-indicators.md`, each row:

```markdown
| `IND-C01` | Price CV | Higher — **deep:** [indicator-lot-ind-c01-coefficient-of-variation.md](./indicator-lot-ind-c01-coefficient-of-variation.md) |
```

Do **not** paste the formula into the catalog.

---

## Eval pairs (required)

Add to `corpus/eval/en/methodology_qa.yaml`:

1. **Definition** — formula, gate, engine path.
2. **Twin trap** (when applicable) — lot vs scope vs CPV.

Tags: `indicator_lot`, code slug (`ind_c01`).

---

## Ship

Complete [`author-corpus`](../author-corpus/SKILL.md) ship checklist, then:

- [ ] L1 catalog **See also** updated for this code
- [ ] `rg 'IND-{code}' corpus/` — formula only in L2 owner
- [ ] Inventory test still passes (`test_corpus_indicator_inventory.py`)
