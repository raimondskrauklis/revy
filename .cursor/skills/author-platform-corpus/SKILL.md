---
name: author-platform-corpus
description: >-
  Author cross-cutting platform L0 corpus pages in corpus/platform/en/ —
  workflow hubs, grain maps, alerts/scoring overviews. Wraps author-corpus.
  Use for platform-* prefix pages — not lot indicators, -CPV, -SCOPE, or
  co-bid-graph overlays.
---

# Author platform corpus

**Prerequisite:** [`author-corpus`](../author-corpus/SKILL.md) (manifest, eval, ship checklist).

**Program:** [`docs/GenAI/corpus/`](../../../docs/GenAI/corpus/README.md) — onboarding hubs; grain doc updates under same prefix family.

**What this skill owns:** Investigator **navigation and mental model** — workflow, layers, reading order, alert routing summary. **Not** per-code formulas (domain skills own those).

---

## When to use

| Task | Skill |
|:---|:---|
| New hub: getting started, alerts/L2, terminology slice | **This skill** |
| Edit `platform-grain-lot-scope-historical-and-cpv-market-levels.md` | **This skill** |
| Cross-link edits only (catalog, report sections) | `author-corpus` ship checklist |
| Lot `IND-*` L2 formula | `author-lot-indicator-corpus` |
| `-CPV` / `-SCOPE` screen L2 | `author-market-screen-corpus` / `author-scope-screen-corpus` |
| 3+ pages, findings → plan → LOOP | `corpus-program` |

---

## Prefix and filenames

| Prefix | Registry row | Examples |
|:---|:---|:---|
| `platform-grain` | existing | `platform-grain-lot-scope-historical-and-cpv-market-levels.md` |
| `platform-onboarding` | add in same PR as first hub file | `platform-investigator-getting-started.md`, `platform-risk-scoring-alerts-and-typologies.md` |

Pattern: `platform-{topic-kebab}.md` · **`doc_id`:** `platform:platform_{topic_snake}:en`

---

## L0 rules (different from L2 methodology)

| Do | Don't |
|:---|:---|
| Link to owning L0/L1/L2 with relative paths | Duplicate formulas from `indicator-lot-*` or `cpv-market-screen-*` |
| Distill `docs/corpus_implementation/TERMINOLOGY.md` — link, don't fork glossary | Index full TERMINOLOGY as corpus |
| Cite `backend/app/constants/l2_scoring.py` for L2 pool list/weights | Paraphrase findings without code check |
| One ¶ threshold posture: operational defaults; tiers differ | LU / econometric alignment prose |
| Workflow diagram or layer table | Per-indicator breach tables (→ lot catalog) |
| Disambiguate alert L1/L2/L3 vs scope-screen L1/L2/L3 | Use "L2" without namespace |

**Grain (locked):** indicator = lot `IND-*`; screen = `-SCOPE` / `-CPV`; signal = fired state.

---

## Mandatory code reads (by page type)

| Page type | Verify in |
|:---|:---|
| Getting started / workflow | `corpus/README.md` L0 index; existing grain + market + scope catalog headers |
| Alerts / L2 / typologies | `l2_scoring.py`, `seed_analytics.py` (TYP `is_active`, `generates_alerts`), `docs/alerts/ALERT_FRAMEWORK_V3.md` (hints only) |
| Grain / suffix | `AnalysisLevel` in `enums.py`, `ANALYSIS_LEVEL_DESIGN.md` (hints) |

No `chart_methodology.yaml` twin for platform L0 hubs.

---

## Eval (`methodology_qa.yaml`)

- ≥2 rows per new hub page.
- Questions: workflow ("where do I start?"), layer grain, `L2-SCORE` vs scope L2 — not formula drill-down.
- `expected_doc_id` = manifest `doc_id`.

```bash
cd backend && pipenv run pytest tests/unit/genai/test_methodology_chat_eval.py -q
```

---

## Ship checklist (adds to author-corpus)

- [ ] Hub links to domain L0s; no formula duplication (`rg` key phrases across `corpus/platform/en/`)
- [ ] `platform-onboarding` row in `corpus/README.md` when first hub ships
- [ ] Cross-links from grain / framework-pools / report sections if in execution scope
- [ ] No LU / external research strings in body
