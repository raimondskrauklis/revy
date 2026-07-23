---
name: corpus-program
description: >-
  Plan and execute multi-page investigator corpus programs under
  docs/corpus_implementation/ — findings, general plan, per-phase execution,
  then author-corpus per deliverable. Use when adding a new corpus domain (market
  screens, lot indicators, scope) or 3+ related pages — not for a single typo fix.
---

# Corpus program

**What:** Structured **planning + execution** for growing `corpus/platform/en/` without duplication, stale docs, or orphan pages.

**Not:** Implementation code (unless execution phase explicitly includes YAML twins). **Not:** indexed content in `docs/` — planning only.

**Implementation:** Each execution subphase that ships a page → invoke [`author-corpus`](../author-corpus/SKILL.md) (or domain skill below).

---

## When to use

| Situation | Skill |
|:---|:---|
| Fix one corpus paragraph | `author-corpus` only |
| Platform L0 hub (workflow, alerts, grain map) | `author-platform-corpus` |
| New `IND-*-CPV` screen deep page | `author-market-screen-corpus` |
| Louvain group / overlay L1 page | `author-community-group-corpus` |
| 3+ pages, new domain, or cross-file alignment | **This skill** → then author skills per phase |
| Lot / scope indicator catalogs | `docs/corpus_implementation/INDICATOR_CORPUS_*` program |

---

## Active programs

| Program | Folder | Corpus prefix | Authority |
|:---|:---|:---|:---|
| Lot + scope indicators | `docs/corpus_implementation/` | `indicator-lot-*`, `scope-screen-*` | `INDICATOR_CORPUS_GENERAL_PLAN.md` |
| CPV market screens | `docs/corpus_implementation/market_screens/` | `cpv-market-*` | `MARKET_SCREEN_CORPUS_GENERAL_PLAN.md` |
| PG community groups | `docs/corpus_implementation/communities/` | `co-bid-graph-*` | `COMMUNITY_GROUP_CORPUS_GENERAL_PLAN.md` |
| Investigator onboarding | `docs/GenAI/corpus/` | `platform-onboarding`, `platform-grain` | `GENAI_CORPUS_ONBOARDING_GENERAL_PLAN.md` |

Programs are **siblings** — cross-link in README; do not duplicate grain/universe prose. GenAI onboarding programs live under `docs/GenAI/corpus/` (not `docs/corpus_implementation/`).

---

## Standard folder layout

```text
docs/corpus_implementation/{program}/
├── README.md                    # hub, terminology, LOOP order
├── {TOPIC}_FINDINGS.md          # code-verified inventory + ownership matrix
├── {TOPIC}_GENERAL_PLAN.md      # phases, gates, deliverables
└── execution/
    └── {TOPIC}_M0_EXECUTION.md  # 3–6 subphases per phase
```

Create with existing skills:

1. **`create-findings`** — baseline inventory, verified code paths, anti-duplication matrix.
2. **`create-general-plan`** — phased goals (M0/M1… or P0/P1…).
3. **`create-execution-plan`** — one file per phase, 3–6 subphases, phase gate, **locked decisions (no TBDs)**.
4. **`execution-peer-review`** — on **full** execution set before `phase-execution` LOOP.
5. **`phase-execution`** — implement subphases; corpus subphases call `author-corpus`.

Update `docs/corpus_implementation/README.md` with a table row for new programs.

---

## Findings bar (corpus-specific)

Extend `create-findings` with:

| Section | Required for corpus |
|:---|:---|
| **Inventory** | Every code/screen/chart with engine path |
| **Content ownership matrix** | Who owns formula vs who links |
| **Existing corpus gaps** | File exists? L1 vs L2 depth? |
| **Machine twins** | `chart_methodology.yaml` `corpus_doc_id` gaps |
| **Eval coverage** | Missing `methodology_qa.yaml` rows |
| **Terminology** | screen vs lot indicator vs scope |

**Baseline-ready** only after `rg` on `backend/app/constants/indicator_pools.py` (or domain equivalent) and peer-review.

---

## Execution subphase pattern (corpus deliverable)

Each corpus subphase in an execution file:

```markdown
## M0.2 — HHI deep corpus page

**What:** Author `corpus/platform/en/cpv-market-screen-ind-m01-hhi-allocation.md` from `concentration.compute_hhi_screen`.

**Must include:** …
**Must not include:** … (link to L0 owner)

**Skill:** author-market-screen-corpus → author-corpus ship checklist.

**Deliverable:** manifest + eval + catalog See also; `pytest tests/unit/genai/test_methodology_chat_eval.py -q`
```

---

## Phase gates (all programs)

- Coverage matrix row marked done in findings or README.
- No duplicate formula (`rg` across `corpus/platform/en/`).
- Manifest + README + eval in same PR as new `.md`.
- `chart_methodology.yaml` aligned for any chart with Explain.
- Re-index noted in PR / deploy checklist.

---

## CPV market screens (quick pointer)

**Start:** `docs/corpus_implementation/market_screens/README.md`

- 22 screens = `IND-*-CPV` at `market_cpv` grain.
- L2 filename: `cpv-market-screen-{code-kebab}-{slug}.md`
- L1 batch docs already cover N06–N40, N08, N41/N42 — **do not re-author** unless retrieval eval fails (M3).

**Skill:** [`author-market-screen-corpus`](../author-market-screen-corpus/SKILL.md)

---

## PG community groups (quick pointer)

**Start:** `docs/corpus_implementation/communities/README.md`

- Bundle `community.group.v1` — seven overlay families + L0 overview/group-reading.
- L1 filename: `co-bid-graph-overlay-{family}.md`
- L0 group-reading: `co-bid-graph-group-reading-*.md` — no overlay formulas.

**Skill:** [`author-community-group-corpus`](../author-community-group-corpus/SKILL.md)

---

## Platform onboarding (quick pointer)

**Start:** `docs/GenAI/corpus/README.md`

- L0 hubs: `platform-investigator-getting-started.md`, `platform-risk-scoring-alerts-and-typologies.md`
- Grain cross-cut: `platform-grain-lot-scope-historical-and-cpv-market-levels.md`
- Link domain L0s — **no formulas** in hub pages

**Skill:** [`author-platform-corpus`](../author-platform-corpus/SKILL.md)

---

## Quality principle

Planning docs in `docs/` can be wrong once; **corpus is canonical for GenAI**. Every execution phase re-verifies against code before writing — same bar as `create-findings` §5.
