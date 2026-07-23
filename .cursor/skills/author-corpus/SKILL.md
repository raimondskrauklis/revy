---
name: author-corpus
description: >-
  Write GenAI Documents RAG markdown in corpus/ — flat platform/en/, manifest
  + README prefix registry. Distill from code; docs/ is hints only. Use when
  adding or updating investigator corpus pages. For multi-page programs use
  corpus-program first; for platform L0 hubs use author-platform-corpus; for
  IND-*-CPV screens use author-market-screen-corpus; for tender_lot IND-* use
  author-lot-indicator-corpus.
---

# Author corpus

**What:** Curated markdown for **Documents RAG** — definitions, methodology, pipeline order. `corpus/manifest.yaml` → pgvector.

**Not:** `docs/` (never prod-indexed). **Not:** live scores, drill values, or instance-specific thresholds unless labelled as “from scan JSON”.

**Registry:** `corpus/README.md` (prefixes + files). Architecture: `docs/GenAI/GENAI_RAG_ARCHITECTURE_FINDINGS.md` §4.2.

**Related skills:**

| Skill | When |
|:---|:---|
| [`corpus-program`](../corpus-program/SKILL.md) | New subsystem or 3+ pages — findings → plan → execution |
| [`author-platform-corpus`](../author-platform-corpus/SKILL.md) | Platform L0 hubs — workflow, alerts, grain (no formulas) |
| [`author-market-screen-corpus`](../author-market-screen-corpus/SKILL.md) | Any `IND-*-CPV` market screen page |
| [`author-lot-indicator-corpus`](../author-lot-indicator-corpus/SKILL.md) | Lot `IND-*` **indicators** |
| [`author-scope-screen-corpus`](../author-scope-screen-corpus/SKILL.md) | `IND-*-SCOPE` **scope screens** |
| `md-formatting` | All `.md` under `corpus/` and `docs/` |

---

## Layout

```text
corpus/
├── README.md
├── manifest.yaml
├── platform/en/*.md      # flat until ~100 files
└── eval/en/methodology_qa.yaml   # NOT indexed — gold Q/A per new page
```

Indexer: `backend/app/workers/genai_corpus_tasks.py`.

---

## Code grounding protocol (mandatory)

**Docs are hints. Code is canonical.** Never ship a corpus fact you have not verified in `backend/`.

### Before writing

1. Read `corpus/README.md` — prefix, existing siblings, layer (L0/L1/L2).
2. `rg` the indicator code / chart_id / route in `backend/app/`.
3. Read the **compute function** (not only constants): engine module, gates, insufficient branches, metadata keys.
4. Read `market_support.py` (gates, directions, band ladders) when the topic is a screen or indicator.
5. Skim **one** `docs/` guide only for vocabulary — reconcile every claim against code.

### Every methodology page must cite

| Fact type | Verify in |
|:---|:---|
| Formula / algorithm | `backend/app/services/analytics/**/engine/*.py` or calculator |
| Gates, universes, directions | `backend/app/constants/market_support.py` |
| Weights, composite | `backend/app/constants/market_scoring.py` |
| Active codes | `backend/app/constants/indicator_pools.py` |
| GenAI chart explain pins | `backend/app/resources/genai/chart_methodology.yaml` |
| Grain / suffix rules | `platform-grain` corpus + `AnalysisLevel` in enums |

### Mark in prose

- **Verified constants** — name the Python symbol (`SCREEN_BAND_LADDERS["IND-M01-CPV"]`).
- **Live data** — breach threshold, percentile, numeric_value: “cite from scan/chart bundle JSON when present”.
- **Do not** copy numeric thresholds from `docs/investigation/` without code check.

### Anti-patterns (reject before PR)

- Paraphrasing a findings doc into corpus without opening the engine.
- Duplicating a full formula already owned by another corpus file (link instead).
- Inventing OECD/DOJ bands not in `SCREEN_BAND_LADDERS` or `chart_methodology.yaml`.
- Calling `-CPV` codes “indicators” without “market screen” context.
- Stating breach threshold = literature band (they are separate in KP).

---

## Layering and single ownership

Corpus is chunked for RAG — **one topic owns each fact**.

| Layer | Role | Duplicate? |
|:---|:---|:---:|
| **L0** | Overview, definition, universes | Owns cross-cutting tables |
| **L1** | Catalog, batch families | Index + gates; **no deep formulas** |
| **L2** | Per-screen or tight family deep dive | Owns formula + interpretation |
| **L3** | Chart ↔ screen mapping | Owns `chart_id` bundle fields |

**Rule:** L2 links to L0/L1 with relative `./sibling.md` paths. L1 adds **See also** to L2 — one line, no formula repeat.

`cpv-market` layer table: `corpus/README.md` § CPV market layers.

---

## Filename pattern

```text
{domain-prefix}-{topic-kebab}.md
```

- Lowercase, hyphens, **one topic**, ≤80 chars.
- **`{domain-prefix}`** must match `corpus/README.md` **Domain prefix registry**.
- Reuse prefix — do not invent synonyms (`market-cpv` when `cpv-market` exists).

**Before any file:** `corpus/README.md` + `rg '{prefix}-' corpus/` — no duplicate topic, no orphan prefix.

New subsystem → new registry row in **same PR** as first file.

---

## `doc_id` + manifest

Stable forever — changing `doc_id` orphans vectors.

Pattern: `platform:{topic_snake}:en`

```yaml
  - doc_id: platform:cpv_market_ind_m01_hhi:en
    corpus_type: platform
    lang: en
    path: corpus/platform/en/cpv-market-screen-ind-m01-hhi-allocation.md
    title: CPV market screen — IND-M01-CPV HHI allocation concentration
    indicator_codes:
      - IND-M01-CPV
    metadata:
      domain_prefix: cpv-market
```

- `indicator_codes`: all `IND-*` the page defines (else `[]`).
- Every new file: **manifest row + README Files table row**.

---

## Machine twin (`chart_methodology.yaml`)

When a tier-2 chart has GenAI Explain (`market.chart_summary.v1`):

1. `corpus_doc_id` in `backend/app/resources/genai/chart_methodology.yaml` **must equal** manifest `doc_id`.
2. `reference_numbers`, `literature_bands`, `prompt_hint` in YAML are the **validator allow-list** — corpus prose must agree (same scale, same band points).
3. Mirror copy lives at `docs/GenAI/chart_methodology.yaml` if present in repo pattern.

If you add L2 corpus for a chart that still points at catalog `doc_id`, update YAML in the **same PR**.

---

## Eval pairs (`corpus/eval/en/methodology_qa.yaml`)

**Not indexed.** Add ≥1 row per new L2 (≥2 for screens with bands/threshold nuance).

```yaml
  - question: …investigator-style question…
    expected_doc_id: platform:…:en
    expected_answer: >-
      Reviewer gold — grounded in corpus body, code-verified numbers only.
    source_path: corpus/platform/en/{file}.md
    tags: [cpv_market, …]
```

`expected_doc_id` must exist in `manifest.yaml`.

**Verify:**

```bash
cd backend && pipenv run pytest tests/unit/genai/test_methodology_chat_eval.py -q
```

CI target: ≥80% recall on golden pairs (`RECALL_TARGET` in test). Staging: `scripts/genai/run_retrieval_eval.py`. Do **not** use `pytest -k m01` — tests are not keyed by screen tags.

---

## File template

```markdown
# corpus/platform/en/{filename}.md

# {Title}

**Purpose:** …
**Audience:** KP/KNAB investigators
**doc_id:** `platform:…:en`
**Last verified:** YYYY-MM-DD

---

## …
```

`##` sections = chunk boundaries. Use `md-formatting` skill (blank lines before lists/tables).

### Recommended sections (methodology / screen)

Use what applies — omit empty sections.

| Section | Content |
|:---|:---|
| Screen/entity identity | Code, grain, scored vs advisory, worse direction |
| What it measures | One paragraph + universe link |
| Formula and scale | Step list from engine; insufficient branch |
| Support gate | Metric + minimum from `SCREEN_SUPPORT_GATES` |
| Interpreting the number | Separate raw value, bands, breach, percentile |
| Charts / UI | `chart_id`, bundle type, grouping modes |
| What not to claim | Explicit negations (common investigator mistakes) |
| References (code) | Bullet list of `backend/…py` paths |

Exemplar L2 screen: `corpus/platform/en/cpv-market-screen-ind-m01-hhi-allocation.md`.

---

## Workflow

1. Confirm layer + ownership (no duplicate formula).
2. Code grounding protocol (above).
3. Write `corpus/platform/en/{prefix}-{slug}.md`.
4. Update `manifest.yaml` + `corpus/README.md`.
5. Add `methodology_qa.yaml` row(s).
6. Sync `chart_methodology.yaml` if applicable.
7. L1 catalog **See also** link only (if L2).
8. Ship checklist (below).

One agent → one file per session when possible. Do not bulk-copy `docs/` into corpus.

---

## Ship checklist

- [ ] Every numeric constant traced to Python (not docs alone)
- [ ] `rg` shows formula prose in **one** owner file
- [ ] `doc_id` in MD header = manifest = chart_methodology (if chart)
- [ ] `indicator_codes` manifest matches page
- [ ] Eval pair(s) added; pytest eval passes
- [ ] `Last verified` date updated
- [ ] Post-merge: re-index corpus on deploy

---

## Re-index (droplet)

```bash
cd backend
pipenv run celery -A app.workers.celery_app call app.workers.genai_corpus_tasks.index_corpus_manifest
```
