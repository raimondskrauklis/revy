# LLM Code Review / Judge — Common Architectural Pattern (Deep Technical Notes)

## Overview

Across Bugbot, CodeRabbit, and Ellipsis, the same architecture recurs despite different branding: **ingestion → parallel context-aware generators → multistage filtering/judge pipeline → agentic verification loop → resolution tracking**. None of them use a single-shot "review this diff" prompt. This doc breaks down each layer with implementation-level detail.

---

## Layer 0: Event Ingestion & Async Processing

Ellipsis's pipeline: GitHub App webhook → routed through Hookdeck (delivery reliability) → FastAPI app → pushed onto a workflow queue (Hatchet) for async processing.

**Key architectural insight:** asynchronous processing changes optimization priorities entirely — latency becomes secondary to accuracy. This unlocks multiple agent passes, deeper filtering, and multi-model consensus that would be impossible under a synchronous/real-time constraint. If you're building your own, don't design for instant response; design for a queue-and-callback model even for small diffs.

---

## Layer 1: Context Assembly (Retrieval Strategy)

Two distinct approaches observed:

**Full-repo cloning (CodeRabbit):** Clones the entire repository into sandboxed cloud execution per review, even though only a diff changed. Runs 50+ static analyzers/linters/SAST tools directly on the full checkout before any LLM involvement. Enables an "agentic exploration" sub-step where the model autonomously investigates the codebase (not just the diff) for context.

**Scoped LSP + RAG (Ellipsis):** Avoids full-repo re-indexing per commit. Uses:
- A **Code Search subagent** shared across code review, code generation, and codebase chat (reused, independently benchmarked component)
- Multi-step RAG+ combining keyword and vector search
- Two indexing methods run in parallel: (1) tree-sitter AST chunking into functions/classes for precise code lookup, (2) file-level LLM-generated summaries for higher-level architectural questions
- **Incremental indexing**: chunks the repo, uses SHA hashes as chunk IDs, diffs new vs. existing IDs in the vector DB namespace, deletes obsolete IDs, only embeds/upserts new chunks. Since most commits touch a small % of chunks, sync takes seconds, not minutes.
- Vector store: Turbopuffer, storing obfuscated metadata only (no raw customer code persisted)
- **Post-retrieval filtering nuance:** instead of relying purely on cosine-similarity thresholds/rerankers (standard RAG), an LLM-based binary classifier runs after vector search using the agent's trajectory context to decide true relevance — because for code, "is this chunk actually useful" matters more than raw similarity rank.

**Language Server integration:** Ellipsis sidecars an `Lsproxy` container (via Modal) providing go-to-definition / find-all-references as tool calls to the agent, abstracting over multiple language servers behind one API. Practical LLM-weakness workaround: since LLMs are unreliable at exact line/column numbers, the tool interface lets the agent reference symbols by name and fuzzy-matches to the nearest matching symbol rather than requiring exact coordinates.

**Takeaway for diff-scoped review:** the LSP-sidecar + incremental-chunk-hash approach is the right-sized pattern — you get symbol-level cross-file context without full-repo embedding costs on every run.

---

## Layer 2: Parallel Specialized Generators

**Core principle (Ellipsis):** decomposition over monolithic prompting — "to increase performance, make the problem easier for the LLM to solve." Instead of one massive review prompt, run dozens of small, independently benchmarked/optimized agents.

Structure:
- Multiple **Comment Generators** run in parallel, each targeting a distinct issue class (e.g., one for custom rule violations defined in a config file, one for duplicated code, others for specific bug categories).
- **Model mixing**: generators can be split across model families/providers simultaneously (e.g., GPT-4o for one generator, Claude Sonnet for another) rather than committing to a single model for the whole pipeline — each model's specific strength gets used where it fits.
- Each generator attaches **Evidence** — direct links to the specific code snippet supporting its claim — at generation time. This evidence becomes the input for the filtering stage's hallucination check (see Layer 3).

**Bugbot's variant — shuffled-diff majority voting:** Instead of parallel generators per issue-class, Bugbot runs multiple full review passes on *shuffled/reordered* versions of the same diff, then keeps only the issues that are found consistently across multiple passes. This exploits LLM positional/ordering sensitivity as a noise source and majority-voting as the denoising filter — a cheaper alternative to multi-model-family generation when you're working with a single model.

**Config-driven customization pattern:** production tools expose custom review rules via YAML config (e.g., `confidence_threshold`, freeform rule strings like "Code should be DRY", "Functions should only do one thing") that get injected into generator prompts — this is the standard mechanism for letting users tune false-positive tolerance and house style without changing code.

---

## Layer 3: Filtering / Judge Pipeline

This is explicitly called out as the layer where **actual quality control happens** — the generator layer is intentionally noisy/cheap; correctness is enforced downstream.

Ellipsis's multistage filter chain (all filters chained sequentially on the raw generator output):
1. **Deduplication Filter** — removes near-duplicate comments, important because parallel generators frequently produce overlapping findings on the same code region.
2. **Confidence Filter** — threshold-based drop of low-confidence comments (each comment carries a numeric confidence score from the generator).
3. **Logical Correctness / Hallucination Filter** — the key anti-hallucination step: takes each comment plus its attached Evidence (the code snippet link from Layer 2) and runs a separate LLM-judge call to verify the claim is actually supported by that evidence, rather than a fabricated/misread interpretation. This is a grounding-check, not a general correctness check — it verifies "is this claim entailed by the cited code," not "is this claim true in some absolute sense."
4. **Comment Editing** — a cleanup pass adjusting line numbers and inline code-suggestion formatting before the comment is ever shown to a human.

CodeRabbit's variant on this layer: separates deterministic and probabilistic checks explicitly — 50+ static analyzers/linters/SAST tools run first and catch anything rule-based or syntactic, and the LLM judge layer is reserved only for semantic-level correctness that static tooling structurally cannot catch. This split (**code where you can, model where you must**) is the single highest-leverage cost/accuracy optimization across all three tools — it means the LLM budget is spent only on the subset of issues that actually require semantic reasoning.

**General hallucination taxonomy relevant to designing your own filter (from the broader grounding-evaluation literature):** hallucinations in this context split into four distinct failure modes, each needing a different detector — factual (claim contradicts world knowledge, fixed via upstream retrieval/tool-call), grounding (claim contradicts the supplied context/diff, fixed via claim-level entailment scoring against the retrieved code, not just an answer-level score), citation (the referenced code/line doesn't actually contain what's claimed, fixed via structural + resolvability + semantic verification of the citation), and reasoning (correct-looking conclusion via a broken inference chain, fixed via step-by-step trace scoring rather than answer-only scoring). For code review specifically, **grounding** and **citation** failure modes dominate (a bot claiming a bug exists at a line that doesn't actually contain that pattern), so your filter should prioritize claim-level entailment against the Evidence snippet over general fact-checking.

---

## Layer 4: Agentic Loop vs. Fixed Pipeline

Bugbot's most significant reported quality jump came not from better prompts but from an architecture change: moving from a fixed generate→filter pipeline to a genuinely agentic loop where the model can call tools mid-review (pull a referenced function's definition, check other call sites, inspect related files) before committing to a final verdict on any single issue.

This came with a prompting-philosophy inversion: earlier versions tried to "calm the model down" to suppress false positives; the redesigned agentic version instead *aggressively encourages* the model to investigate anything that looks suspicious, because the downstream filtering/verification layer (Layer 3) is now responsible for suppressing false positives — not the generation prompt itself. This is an important separation-of-concerns lesson: don't try to make the generator conservative; make the generator maximally exploratory and push all precision control into a dedicated filtering/judge stage.

---

## Layer 5: Cross-Model Verification ("Jury" / Mixture-of-Critics Pattern)

An alternative/complementary design to same-model shuffled-diff voting (Layer 2 Bugbot variant): spread reviewers across genuinely different model families, not just multiple passes of one model. Rationale: same-family multi-pass voting shares correlated blind spots and exhibits self-preference bias (a model — or judge from the same lab/family — tends to rate outputs from its own family more favorably, a known LLM-judge weakness).

Structure of the pattern:
- Independent critics from different model families each evaluate the same diff/claim.
- An **orchestrator acts as judge**, not an averager — it can outright *refute* a critic's proposal rather than blending scores, preserving disagreement signal instead of smoothing it away.
- A **deterministic diff-check** sits above the LLM jury entirely and can override even a unanimous LLM verdict — i.e., ground-truth code inspection retains veto power over model consensus.

For a from-scratch build, this suggests: use one model family (e.g., Kimi K2.7 Code) as the primary generator, and a *different* lab's model as the sole verifier/judge in Layer 3's hallucination filter — deliberately avoiding same-family judge-of-self setups.

---

## Layer 6: Reliability & Fault-Tolerance Engineering

Production-grade patterns observed (Ellipsis):
- Simple retries + timeouts on every LLM call.
- **Model fallback chains** — e.g., falling back from Sonnet to GPT-4o if a provider is down, rather than failing the whole review.
- Tool-call errors fed back into the agent as context for self-correction rather than hard-failing.
- **Tool-level isolation** — if the vector DB is unavailable, keyword search continues to function independently rather than taking down the whole retrieval layer.
- **Agent-level isolation** — if one parallel Comment Generator crashes, the others still complete and submit their findings; a single generator failure doesn't block the whole review.
- **Graceful degradation** — if an agent hits an unexpected error mid-task, it's instructed to submit output based on whatever partial work it completed rather than erroring out entirely.
- Descriptive fallback user-facing messaging if all LLM providers are simultaneously unavailable.

---

## Layer 7: Success Metric — Resolution Rate, Not Detection Count

Bugbot's optimization target is explicitly **not** "number of issues flagged." It's whether flagged issues are actually still present (unresolved) versus fixed by the time a PR merges — tracked via a dedicated AI-judge that re-checks the final merged diff against previously raised issues. This "resolution rate" metric was pushed from roughly 52% to over 70% across ~40 iterative experiments, and is treated as the primary quality signal for the whole system, above raw bug-count or false-positive-rate in isolation.

**Practical implication for a DIY build:** don't evaluate your bot by counting flagged issues per PR. Track whether a flagged issue's associated code region changes in a subsequent commit (proxy for "user acted on it") versus stays static (proxy for either irrelevance or the user ignoring a valid flag — worth separate manual review to distinguish).

---

## Consolidated Reference Architecture

```
GitHub webhook (diff/PR event)
   │
   ▼
Async queue (accuracy > latency priority)
   │
   ▼
Context Assembly
   ├─ LSP sidecar: symbol lookup scoped to diff-touched code
   └─ Incremental vector index (hash-diffed chunks, AST-based)
   │
   ▼
Parallel Generators (2-4x)
   ├─ Multiple model families OR shuffled-diff passes of one model
   ├─ Each generator tagged by issue class (logic/security/style/perf)
   └─ Each finding carries attached Evidence (code snippet reference)
   │
   ▼
Deterministic Pre-Filter
   └─ Static analyzers / linters / rule-based checks (cheap, no LLM)
   │
   ▼
LLM Filtering Pipeline
   ├─ Deduplication
   ├─ Confidence thresholding
   ├─ Grounding/hallucination check (claim vs. Evidence, cross-model judge)
   └─ Line/formatting cleanup
   │
   ▼
Deterministic diff-check (veto power over LLM consensus)
   │
   ▼
Output: PR comments
   │
   ▼
Resolution tracking (re-check at next commit/merge → feeds eval loop)
```

## Key Design Principles Extracted

1. Decompose into many small, independently benchmarked agents rather than one large prompt.
2. Separate concerns strictly: generators should be exploratory/aggressive; precision control belongs entirely to the filtering stage.
3. Use deterministic/static tooling for anything rule-based; reserve LLM judge calls only for genuinely semantic questions.
4. Every generator claim needs attached Evidence; every filter stage checks claims against Evidence, not against general world-knowledge.
5. Prefer cross-model-family judging over same-model self-judging to avoid correlated blind spots and self-preference bias.
6. Design for async/queued processing — this unlocks multi-pass and multi-model strategies that real-time constraints would forbid.
7. Build fault isolation at both the tool level and the agent level so partial failures degrade gracefully instead of failing the whole review.
8. Measure success via downstream resolution/fix rate, not raw issue-count — count-based metrics reward noisy over-flagging.
