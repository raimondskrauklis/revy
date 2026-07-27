# Review quality — structural cross-file context (strategy)

**Purpose:** Capture platform-level analysis on **LSP call graphs**, **cross-file recall**, and **Greptile parity** — so decisions are not lost between review-quality v1 and post-v1 work.

**Status:** strategy locked (2026-07-27). **Not execution.**

**Related:** [REVIEW_QUALITY_FINDINGS.md](./REVIEW_QUALITY_FINDINGS.md) (D4, D13, parking lot) · [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) · [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) · [code-review-arch notes](../code-review-arch_perplexity_searcj_advice_only.md) (Ellipsis LSP sidecar, Bugbot agentic loop).

---

## Short answer

| Decision | Verdict |
|----------|---------|
| **Defer full LSP call graph in `review-quality-v1`** | **Yes** — wrong ROI before diff-first + trace + grounding ship |
| **Defer all structural cross-file context** | **No** — gap shows up fast; deferring **both** LSP **and** agents (Track A) leaves no credible answer to Greptile’s main claim |

**Honest v1 positioning:** strong **diff-first** reviewer with bounded supplemental RAG — not full **“impact beyond the diff”** until v1.1+ structural layer lands.

---

## Why this doc exists

Smoke [#44](../REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md) proved the immediate failure mode was **scope** (full-repo haystack), not missing LSP. After v1 ships diff-first (D13) + pipeline trace (O), the **next** recall gap will be **cross-file structural bugs** — the wedge Greptile markets hardest.

Without a written strategy, teams either (a) over-build LSP in Celery workers too early, or (b) assume embeddings + 3 lenses are “enough” and stall on Greptile-class bugs.

---

## Platform view — three context strategies

The market is **not** one architecture. Three production patterns dominate (2025–2026):

| Player | Cross-file strategy | Optimizes for | Public reference |
|--------|---------------------|---------------|------------------|
| **Greptile** | Persistent **repo graph** at onboarding — functions, callers, imports, dependencies | “Assess impact beyond the diff”; query graph on every review | [Graph-based codebase context](https://www.greptile.com/docs/how-greptile-works/graph-based-codebase-context) |
| **Bugbot (Cursor)** | **Diff-first** → **agentic runtime** — model pulls defs/callers when suspicious | Precision without upfront graph infra; context on demand | [Building a better Bugbot](https://cursor.com/blog/building-bugbot) |
| **Ellipsis-style** | Incremental embed + **LSP sidecar** (`Lsproxy`) as agent tools | Symbol-accurate refs without full-repo embed every push | [Architecture notes](../code-review-arch_perplexity_searcj_advice_only.md) Layer 1 |

**Revy v1** aligns with **Bugbot’s early pipeline** (diff + bounded retrieval + judge) but **defers agents** (Track A, R6+). That creates a **pinch point**: no persistent graph **and** no runtime investigator.

### North star — combine both (not A XOR B)

**Likely end-state:** Greptile-style **persistent reference graph** as the **substrate** + Bugbot-style **agents** as the **runtime** that query it. Not “graph *or* agent” — graph answers “who calls X?” cheaply and deterministically; agent decides **when** to ask and **how deep** to investigate.

```text
                    ┌─────────────────────────────────────┐
                    │  Diff-first trigger (compare + diff) │
                    └─────────────────┬───────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
     ┌────────────────┐    ┌──────────────────┐    ┌─────────────────┐
     │ Reference graph │    │ Investigator     │    │ Judge + publish │
     │ (Greptile-like) │◄───│ agent (Bugbot)   │───►│ (precision)     │
     │ callers/imports │    │ tools: graph,    │    │                 │
     └────────────────┘    │ grep, read_file  │    └─────────────────┘
                            └──────────────────┘
```

**Ellipsis pattern** is the closest production analogue: incremental embed + **LSP/graph exposed as agent tools**, not stuffed into every prompt upfront.

**Greptile’s own evolution** points the same way — graph index at install, then **agentic swarm** on each PR ([changelog](https://www.greptile.com/changelog): “rebuilt review engine around an agentic workflow”). Revy’s roadmap should assume convergence, not pick one vendor’s v1 marketing slide.

**Road to get there** (sequencing matters — cannot skip rungs):

| Rung | What ships | Role |
|------|------------|------|
| **v1** (`review-quality-v1`) | Diff-first + trace + judge + Greptile publish | Foundation; instrument structural gap (SC3) |
| **v1.1** (`RQ-STRUCT-1`) | Grep/import/hunk bridge | Cheap caller recall; validates bug class before graph infra |
| **v2** (`RQ-STRUCT-2`) | Lightweight reference index (SCIP/tree-sitter) **or** single investigator agent | First real cross-file layer |
| **v3** (Track A) | Agent + **graph tools** | Bugbot loop querying Greptile substrate |
| **v4+** | Parallel category agents / swarm | Greptile-scale; only after trace proves single-agent limits |

**SC8 (locked):** North star = **graph substrate + agent runtime**. v1–v1.1 are deliberate rungs, not the destination.

**Engineering context (companion):** Bots also need **planning-doc context** — what the PR must implement — not only code structure. See [REVIEW_QUALITY_REVIEW_CONTEXT.md](./REVIEW_QUALITY_REVIEW_CONTEXT.md) (RC track). RC0 ships in RQ0; structural (SC) and review-context (RC) layers are independent.

---

## Research — why RAG alone is insufficient for callers

| Finding | Implication for Revy |
|---------|---------------------|
| Vector RAG cannot reliably distinguish **definition vs call** with the same name | Fixed lenses on pgvector will not answer “who calls `foo`?” |
| RAG optimizes semantic similarity → **noise** can hurt review quality | More chunks ≠ better; smoke #44 was haystack noise |
| Diff-only tools miss **signature/API changes** with callers outside the diff | Monorepo / shared-library bug class ([Macroscope monorepo guide](https://macroscope.com/content/ai-code-review-monorepos-complete-guide)) |
| AST/reference graphs excel at **exact reference lookup** | Greptile’s graph is product positioning **and** a real bug class |
| Bugbot’s largest quality jump came from **agentic tool use**, not a bigger upfront graph | Path B may beat Path A for Revy if agents ship soon after v1 |

**Prior bet** ([PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md)): embeddings + judge beats call-graph parity on day one. **Updated:** still true for **v1**, but **not** for Greptile-shaped “system impact” claims — revisit with **trace metrics** after v1 dogfood.

---

## What `review-quality-v1` catches vs misses

### Catches well (ship v1)

- Bugs **inside changed hunks** (logic, security in touched code)
- Issues visible in **unified diff** (D13 primary input)
- Noise reduction vs full-repo embed (smoke #44 class)
- Grounding judge (E) + D10 fingerprint + Greptile publish (G)

### Misses systematically (Greptile wedge)

| Bug class | Example |
|-----------|---------|
| **API / signature change** | `def process(x: int)` → `str`; callers in other files not in diff |
| **Shared contracts** | Protobuf, OpenAPI, shared types, config keys used elsewhere |
| **Monorepo cross-service** | Change correct in isolation; consumer breaks |
| **Indirect / dynamic dispatch** | Reflection, barrel exports, stringly-typed calls |

### What v1 mitigations are **not**

| Mitigation | Covers | Does not cover |
|------------|--------|----------------|
| **D4 = 0** (changed files only) | Direct edits | Callers outside diff |
| **D4 v1.1 import +1 hop** | Direct import deps of touched modules | Transitive callers, dynamic calls |
| **D7 test retrieval exclusion** | Stops unrelated `tests/**` haystack in RAG | Cross-file production callers |
| **`index_mode=full`** | Whole-repo embed (expensive) | Still not deterministic caller graph; wrong default |

---

## Pushback — defer LSP, not the problem

### 1. You need **something** post-v1 — not necessarily LSP

Full **LSP in Celery workers** is operationally heavy: per-language servers, checkout lifecycle, memory, cold start, monorepo paths. Ellipsis uses an **LSP proxy sidecar** (Modal) — a **platform** investment, not a pipeline tweak.

**Fork after v1** (choose from trace data):

```text
Path A (Greptile-like)   Persistent reference index — tree-sitter, SCIP, stack-graphs
Path B (Bugbot-like)     Agent loop + read_file / grep / optional LSP on demand
Path C (cheap bridge)    Deterministic caller grep + import-follow — no LSP
```

**Do not** commit to Path A before v1 traces show recall gaps. **Do** instrument gaps in v1 (see below).

### 2. Bugbot argues against graph-first

Cursor: fixed parallel diff passes → **agent pulls context at runtime**. Supports deferring **persistent graph** if **agents** follow quickly.

Revy defers agents to **R6+**. Therefore v1 needs either:

- **Honest positioning** (“diff reviewer”, not “system impact analyzer”), or
- **Path C bridge** in v1.1 before agents/graph.

### 3. Greptile parity is a graph **product**, not a prompt tweak

Greptile builds a graph at signup and queries callers/callees per review. Marketing aside, the **bug class is real**. Greptile-shaped **comment format** (G) ≠ Greptile-shaped **recall**.

---

## Tiered roadmap (locked strategy)

### Phase 0 — `review-quality-v1` (current PR)

**In scope:** D13 diff index, O trace, E grounding, G publish, C1 incremental, M metrics.

**Explicit non-goal:** deterministic cross-file caller tracing; full LSP; agent tool loop.

**Instrumentation (ship in v1 — cheap, high value):** extend retrieval / index manifest:

| Field | Purpose |
|-------|---------|
| `changed_symbols[]` | Symbols touched in diff (tree-sitter or naive extract) |
| `structural_context_mode` | `none` \| `import_follow` \| `grep_callers` \| `graph` (future) |
| `caller_files_requested` | Paths we tried to pull for structural context |
| `caller_files_included` | Paths actually in prompt |
| `structural_context_attempted` | `false` in v1 default — makes gap visible in trace |

Use these fields to decide Path A vs B vs C after dogfood — **not** ideology.

---

### Phase 1 — `RQ-STRUCT-1` (v1.1 — likely next, weeks not months)

**Bridge without LSP.** Implement before claiming Greptile-class cross-file recall.

| Tactic | Effort | Bug-class coverage |
|--------|--------|-------------------|
| **Hunk expansion** — enclosing function/method around each diff hunk | Low | “3 lines in middle of function” uninterpretable diffs |
| **D4 +1 import-follow** — parse imports from changed files; include those file bodies in context (not whole repo) | Low | Direct deps of touched modules |
| **Ripgrep caller search** — for changed exported symbols, `rg` repo for references; cap files/tokens | Medium | ~60–70% of “signature broke callers” without LSP |
| **Compare + `full` fallback** | Already locked (D13) | Huge PRs / compare API failure |

**Out of RQ-STRUCT-1:** multi-language LSP sidecar; persistent graph at repo install; agent swarm.

**Success metric:** staging PR that changes a public function signature → manifest shows `caller_files_included` > 0 and review mentions at least one external caller **or** explicit “could not resolve callers” in trace.

---

### Phase 2 — `RQ-STRUCT-2` (v2 — data-driven fork)

After dogfood on **API-changing PRs**, read v1 traces:

| Trace signal | Likely path |
|--------------|-------------|
| Many reviews with `changed_symbols` but `caller_files_included = 0` and missed bugs | Accelerate **Path C** or **Path B** |
| Grep bridge finds callers but judge/publish drops valid cross-file findings | Fix downstream (E/G), not graph |
| Monorepo / polyglot repos with systematic misses | **Path A lite** (SCIP or tree-sitter reference index per repo) **or** **Path B** (investigator agent) |
| Most value intra-diff | Delay graph; invest in G + M + learning |

**Full LSP sidecar** justified when agents need **exact** go-to-def across languages at interactive speed — not as the first cross-file fix.

---

### Phase 3 — Track A agents (R6+ defer)

Aligns with Bugbot’s mature architecture — and **consumes** the graph from RQ-STRUCT-2 (north star SC8):

- **Investigator agent** with tools: `query_graph` (callers/callees), `read_file`, `grep`, optional LSP
- Diff-first trigger; agent pulls structural context **on demand**, not full-repo upfront
- Generators stay exploratory; precision in judge + publish (locked principle)
- Parallel category agents / swarm only after single-agent + graph tools prove stable in trace

**Not a substitute for RQ-STRUCT-1** if agents stay deferred 6+ months. **Not an alternative to graph** at maturity — agents without graph re-discover callers expensively every run.

---

## Options matrix (decision aid)

| Option | Pros | Cons | When |
|--------|------|------|------|
| **A — Persistent reference graph** | Greptile parity; deterministic callers; fast query at review time | Build + maintain per language; index invalidation; storage | Monorepos, heavy API-surface repos; trace shows grep insufficient |
| **B — Agent + tools** | No upfront graph; pulls only needed context; Bugbot-proven | Latency; cost; tool reliability; needs agent infra | After v1 trace + judge stable; Ellipsis/Bugbot pattern |
| **C — Grep/import bridge** | Days not months; no LSP ops; good ROI | Imprecise; misses dynamic calls; language quirks | **v1.1 default** before A or B |
| **D — `index_mode=full` only** | Already shipped parallel path | Expensive; still not caller graph; wrong default | Explicit `deep`/`critical` or compare fallback only |
| **E — Defer everything** | Ship v1 faster | No Greptile recall story; dogfood hits ceiling | **Reject** unless positioning is diff-only |

---

## Relationship to existing locked decisions

| Q# | Interaction |
|----|-------------|
| **D4** | v1 = 0; v1.1 import +1 hop is first structural expansion (part of RQ-STRUCT-1) |
| **D7** | Excludes **test paths from supplemental RAG only** — not diff, not CI test runs |
| **D13** | Diff index ≠ structural graph; compare gives **what changed**, not **who calls it** |
| **O3** | Manifest must record structural context fields (see Phase 0 instrumentation) |
| **A1** | Agents defer R6+ — increases urgency of RQ-STRUCT-1 bridge |
| **Parking lot “LSP / symbol hop”** | Means **full LSP call graph** — defer v1; see RQ-STRUCT-1/2 for alternatives |

---

## Decisions registry (structural context)

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **SC1** | Defer full LSP in review-quality-v1? | **locked** | **Yes** |
| **SC2** | Defer all cross-file structural context? | **locked** | **No** — plan RQ-STRUCT-1 v1.1 |
| **SC3** | v1 instrumentation for structural gap? | **locked** | **Yes** — manifest fields in Phase 0 |
| **SC4** | v1.1 default path? | **locked** | **Path C** — hunk expansion + import +1 + caller grep |
| **SC5** | v2 path selection? | **locked** | **Data-driven** from trace after v1 dogfood |
| **SC6** | Greptile “impact beyond diff” in v1 marketing? | **locked** | **No** — honest diff-first until RQ-STRUCT-1 green |
| **SC7** | Full LSP sidecar? | **open** | RQ-STRUCT-2 if Path C insufficient and agents not ready |
| **SC8** | North star architecture? | **locked** | **Graph substrate + agent runtime** — Greptile index + Bugbot investigator; see [north star](#north-star--combine-both-not-a-xor-b) |
| **RC0** | Wire Greptile/Bugbot to execution + findings? | **locked** | **Yes** — RQ0; [review context](./REVIEW_QUALITY_REVIEW_CONTEXT.md) |

---

## Honest positioning (product)

| Claim | v1 | After RQ-STRUCT-1 | After RQ-STRUCT-2 / agents |
|-------|----|-------------------|----------------------------|
| Reviews the **PR diff** with bounded context | Yes | Yes | Yes |
| **Greptile-shaped** GitHub comment | Yes (G) | Yes | Yes |
| Catches bugs **in changed hunks** | Target | Target | Target |
| **Impact beyond the diff** / caller breakage | Limited (`full` mode only; expensive) | Grep/import bridge | **Graph + agent** (SC8 north star) |
| **Deterministic call graph** | No | Partial (grep) | Yes — graph substrate |

---

## References

| Source | URL / path |
|--------|------------|
| Greptile graph docs | https://www.greptile.com/docs/how-greptile-works/graph-based-codebase-context |
| Greptile “context” blog | https://www.greptile.com/blog/ai-reviews-need-context |
| Bugbot architecture | https://cursor.com/blog/building-bugbot |
| Bugbot docs | https://cursor.com/docs/bugbot |
| RAG vs AST for code review | https://comparethemarketcareers.com/blog/comparing-context-retrieval-approaches-for-ai-code-review/ |
| Monorepo cross-file | https://macroscope.com/content/ai-code-review-monorepos-complete-guide |
| CoreGraph (graph + LSP bridge example) | https://github.com/simplecore-inc/coregraph |
| Revy architecture notes | [code-review-arch_perplexity_searcj_advice_only.md](../code-review-arch_perplexity_searcj_advice_only.md) |
| Staging smoke #44 | [REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md](../REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md) |

---

## Next

1. **v1 execution** — include manifest instrumentation (SC3) in R1/O slice.
2. **RQ0** — ship review-context wiring (RC0); see [REVIEW_QUALITY_REVIEW_CONTEXT.md](./REVIEW_QUALITY_REVIEW_CONTEXT.md).
3. **After `review-quality-v1` tag** — draft `REVIEW_QUALITY_RQ_STRUCT_1_GENERAL_PLAN.md` if dogfood confirms cross-file gaps; draft **RQ-RC-1** if review-context metrics warrant RC1/RC2.
4. **Product patterns** — keep [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) row “Full call graph” pointed at this doc.
