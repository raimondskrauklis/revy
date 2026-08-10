## Core Thesis: Full-Codebase Context vs. Diff-Only Review

Greptile's differentiating architectural bet is that every pull request review is evaluated against a graph representation of the *entire* indexed repository, not just the changed lines. Most competing tools (CodeRabbit, GitHub Copilot Code Review, Qodo Merge) analyze diffs in isolation and only pull in surrounding codebase context on-demand or heuristically, whereas Greptile builds and persists a full graph index at connection time and re-queries it on every review. This full-context approach is the mechanism behind independently reported benchmark gaps — 82% bug catch rate for Greptile vs. 44% for CodeRabbit, at the cost of a higher false-positive rate (roughly 11 vs. 2 per run).[^1][^2][^3][^4]

## Indexing Pipeline: From Raw Repo to Code Graph

When a repository is connected, Greptile runs a discrete indexing pipeline before any review can occur (typically 3-5 minutes for small repos, over an hour for large monorepos):[^5][^6]

- **Repository scanning**: parses every file to extract directories, files, functions, classes, and variables as discrete graph nodes.[^7]
- **Relationship mapping**: connects nodes via function calls, imports, dependency edges, and variable usage, producing a language-agnostic call graph.[^3][^7]
- **Graph storage**: the completed graph is persisted (in the cloud offering, in Greptile's database; self-hosted, in PostgreSQL with pgvector) for low-latency querying during reviews.[^8][^7]
- **Incremental updates**: the index updates continuously as new commits land rather than requiring a full re-index per PR.[^2][^9]

Critically, per Greptile's original Launch HN technical disclosure, code is not embedded directly. Instead, the pipeline parses the abstract syntax tree (AST) of the codebase, recursively generates natural-language docstrings for each AST node, and embeds those docstrings rather than raw source text. This design choice stems from an internal finding that semantic search performance on code improves substantially when code is first translated to natural language before embedding, and when chunking is done at per-function granularity rather than per-file — tighter chunks reduce retrieval noise.[^10][^11]

## Retrieval Strategy: Beyond Vector Similarity

Greptile's retrieval layer combines three complementary mechanisms rather than relying on vector search alone:[^11]

| Mechanism | Function |
|---|---|
| Vector similarity search | Matches query embeddings against docstring embeddings of code chunks[^11] |
| Keyword search | Catches exact-match terms (identifiers, symbol names) that embeddings may under-weight[^11] |
| Agentic graph traversal | An agent reviews initial search-result relevance and actively follows references ("command+clicking") through the call graph to pull in dependent code[^11][^12] |

This hybrid approach is explicitly framed by Greptile as "codebase-optimized RAG" — a retrieval-augmented generation system tuned to mirror how an experienced engineer navigates unfamiliar code: building a mental map first, then following references outward from a starting point rather than treating the repo as a flat list of files.[^12]

## Review-Time Query Flow

During an actual pull request review, the graph is queried multiple times to assemble context beyond the literal diff:[^13][^14]

- **Direct dependencies**: functions called, imports used, and variables accessed by the changed code.[^7]
- **Usage/impact analysis**: every call site of a modified function across the repository, so the reviewer can flag "this change affects 3 other files" type impacts.[^3][^7]
- **Pattern consistency checks**: comparison against structurally similar functions elsewhere in the repo (e.g., flagging a SQL function using string concatenation when sibling functions use parameterized queries).[^7]
- **Multi-hop investigation (v4 agent, released March 2026)**: rather than a single retrieval pass, the agent performs iterative reasoning hops — tracing dependency chains, consulting git history, and following call trees to a configurable depth — before finalizing a comment. Each hop is framed internally as "given this change, what else could break?".[^9][^3]
- **Confidence scoring**: every flagged issue receives a confidence score reflecting how well-supported it is by concrete evidence in the graph, allowing high-confidence structural bugs to be triaged separately from speculative low-confidence style flags.[^15][^9][^3]

Feedback then closes the loop: Greptile ingests thumbs-up/down reactions and other engineers' PR comments to progressively suppress noise categories the team doesn't care about, typically converging after roughly two to three weeks of active use.[^16][^13]

## Self-Hosted / On-Premises Architecture

For teams requiring data sovereignty, Greptile is fully self-hostable via the `akupara` deployment repository, using either Docker Compose (up to ~100 developers, single VM) or Kubernetes with Helm charts (100+ developers, horizontal scaling). The service topology exposes the indexing pipeline as discrete, independently scalable workers:[^17][^18][^8]

| Service | Role |
|---|---|
| `greptile-indexer-chunker` | Splits repositories into chunks for indexing (CPU/memory intensive; scales to ~10 replicas in production)[^8] |
| `greptile-indexer-summarizer` | Generates repository/function summaries — LLM-bound, scales heavily (up to ~50 replicas) with indexing load[^8] |
| `greptile-reviews` | Runs the LLM-driven PR review agent (LLM-bound, up to ~36 replicas)[^8] |
| `greptile-llmproxy` | Routes requests to configured LLM providers (OpenAI, Anthropic, AWS Bedrock, Azure OpenAI, GCP Vertex AI)[^8][^18] |
| `greptile-postgres` (pgvector-enabled) | Stores repository metadata, code embeddings, review history[^8] |
| Hatchet (`hatchet-engine`, `hatchet-rabbitmq`, `hatchet-postgres`) | Workflow orchestration and message queuing for background indexing jobs[^8] |

Notably, embeddings are called out as "the largest storage component" in capacity planning guidance, underscoring how the docstring-then-embed pipeline generates significant per-function vector data at scale. Self-hosted deployments require three distinct LLM model classes to be configured: a "smart" reasoning model (Claude 3.5 Sonnet-class or better) for review/agent tasks, a "fast" model (GPT-4o-mini/Claude Haiku-class) for summarization, and a dedicated embeddings model (text-embedding-3-small, Titan V2, etc.) for indexing.[^18][^8]

## Cross-Repository and Monorepo Handling

For microservice or monorepo setups, Greptile supports clustering related repositories (e.g., grouping frontend, backend, and documentation repos) so that graph context spans repository boundaries — Greptile can suggest these clusters automatically — which matters when a change in one service silently breaks a contract consumed by another. This is configured via a `patternsRepo` field in a `greptile.json` config file that lets teams explicitly point at related repos for extra context even outside formal clustering.[^13][^16]

## Data Handling and Security Model

In the original architecture disclosed publicly, Greptile does not persist raw source code on its servers after initial processing — it pulls snippets on-demand from the GitHub/GitLab API at query time, and its OAuth permissions are read-only despite GitHub's "act on your behalf" phrasing during sign-in. The self-hosted/air-gapped deployment path exists specifically for teams (e.g., regulated or government-adjacent environments) that cannot rely on this cloud-side snippet-pulling model and need indexing, storage, and inference to remain entirely inside their own infrastructure perimeter.[^19][^17][^11]

## Practical Implication for Full-Codebase (Non-Diff) Review Use Cases

Beyond PR review, the same graph/index underlies Greptile's natural-language codebase Q&A/chat capability — useful for onboarding or architecture exploration — since the identical retrieval stack (AST-derived docstring embeddings + keyword search + agentic graph traversal) answers "how does X work" queries the same way it assembles review context. This means the "full codebase review" behavior is not a separate mode bolted onto diff review — it is the same underlying indexed graph and hybrid retrieval system, simply invoked with a review-specific prompt/workflow instead of a chat query.[^20][^21][^22][^2][^12]

---

## References

1. [AI Code Review | Greptile | Merge 4X Faster, Catch 3X More ...](https://www.greptile.com/) - Greptile constructs a graph index of your codebase, then uses a swarm of agents to catch potential i...

2. [Greptile Review 2026: AI Code Review with Full Codebase ...](https://aitoolscoop.com/tool/greptile/) - Greptile is an AI code review and codebase intelligence tool that indexes your entire repository to ...

3. [Greptile Review 2026: 82% Bug Catch Rate, the $1/Review Trap, and Who Should Pay $30/Month](https://dev.to/jovan_chan_9500711396d4e6/greptile-review-2026-82-bug-catch-rate-the-1review-trap-and-who-should-pay-30month-4jao) - Greptile's unique codebase indexing offers an 82% bug catch rate for $30/month per developer, but wi...

4. [Greptile Review: The AI Code Review Tool That Actually ...](https://www.agentrank.tech/blog/greptile-review-codebase-aware-pr-reviewer) - Greptile reviews your PRs with full codebase context — not just diffs. At $30/dev/month, is it worth...

5. [docs/quickstart.mdx at main · greptileai/docs](https://github.com/greptileai/docs/blob/main/quickstart.mdx) - Contribute to greptileai/docs development by creating an account on GitHub.

6. [Greptile](https://docs.dev.steelengine.com/tools/greptile) - AI-powered codebase search and Q&A

7. [Graph-based Codebase Context](https://www.greptile.com/docs/how-greptile-works/graph-based-codebase-context) - Greptile builds a complete codebase graph to understand function relationships, dependencies, and pa...

8. [System Architecture](https://www.greptile.com/docs/system-architecture) - Detailed system architecture for self-hosted Greptile deployments. Covers Docker Compose and Kuberne...

9. [Greptile Review 2026: AI Code Review That Understands Your ...](https://baeseokjae.github.io/posts/greptile-review-2026/) - Greptile leads AI code review benchmarks with 82% bug catch rate and 100% high-severity detection — ...

10. [Codebases are uniquely hard to search semantically](https://www.greptile.com/blog/semantic-codebase-search) - Discover why AI struggles with semantic search in codebases and how Greptile's AI programming assist...

11. [Launch HN: Greptile (YC W24) - RAG on codebases that actually works](https://news.ycombinator.com/item?id=39604961)

12. [Announcing our $4.1M seed round](https://www.greptile.com/blog/seed) - Greptile raises $4.1M seed round to transform AI code review with their innovative API. Learn how th...

13. [Key Features - Greptile](https://www.greptile.com/docs/code-review-bot/key-features)

14. [Key Features](https://www.greptile.com/docs/code-review/key-features)

15. [AI Code Review: What Developers Need to Know - Greptile](https://www.greptile.com/blog/ai-code-review) - Lessons from 3.4M AI code reviews. Why AI-generated code needs an independent reviewer, how confiden...

16. [Greptile v3.0.7: Self-hostable AI code review tool](https://www.reddit.com/r/selfhosted/comments/1tym7yt/greptile_v307_selfhostable_ai_code_review_tool/) - Greptile v3.0.7: Self-hostable AI code review tool

17. [Self-Hosting Overview](https://www.greptile.com/docs/self-hosting/overview) - Complete guide to deploying Greptile infrastructure on-premises

18. [Deployment Options - Docker Compose](https://www.greptile.com/docs/deployment-options) - Compare Greptile cloud vs self-hosted deployment options. Learn about Docker Compose and Kubernetes ...

19. [Self-Hosted Greptile](https://www.greptile.com/docs/security/selfhost) - Deploy Greptile in your own infrastructure with Docker Compose. Supports AWS, GCP, Azure, air-gapped...

20. [Developer Quick Reference](https://www.greptile.com/docs/developer-quick-reference)

21. [Overview - What is Greptile?](https://www.greptile.com/docs/introduction)

22. [GitHub - sosacrazy126/greptile-mcp](https://github.com/sosacrazy126/greptile-mcp) - Contribute to sosacrazy126/greptile-mcp development by creating an account on GitHub.

