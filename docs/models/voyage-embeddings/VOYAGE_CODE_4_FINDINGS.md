# Voyage Code 4 — findings

Baseline for evaluating **`voyage-code-4`** and **`voyage-code-4-large`** as successors to **`voyage-code-3`** in Revy's R3 code-index pipeline.

**Date:** 2026-08-10 · **Status:** baseline-ready (API smoke done 2026-08-10; `voyage-code-4` still unavailable)

---

## Build principles

- **No silent model swap** — embedding model changes invalidate stored vectors; require explicit env change + full re-index (same rule as `0021` voyage-code-3 upgrade).
- **Verify before adopt** — dashboard visibility ≠ documented API contract; smoke-test with production key before changing defaults.
- **Code-domain first** — Revy indexes **source code chunks** for PR-scoped retrieval; general `voyage-4*` or `voyage-context-4` are separate evaluation tracks.
- **Dimension stability** — stay on **1024** unless benchmarks justify migration cost (`github_code_chunks.embedding` is `vector(1024)`).

---

## Terminology

| Term | Meaning |
|------|---------|
| **Text embed API** | `POST https://api.voyageai.com/v1/embeddings` — what Revy uses today (`voyage_embeddings.py`) |
| **Contextualized embed API** | Separate endpoint for `voyage-context-3/4` — chunk embeddings with full-document context; **not** wired in Revy |
| **Shared embedding space** | Voyage 4 **general** models (`voyage-4`, `voyage-4-large`, `voyage-4-lite`, `voyage-4-nano`) produce interchangeable vectors |
| **Code series** | `voyage-code-2` → `voyage-code-3` → **`voyage-code-4`** (inferred); separate from general `voyage-4` space until proven otherwise |

---

## What exists in Revy (verified)

| Item | Location | Notes |
|------|----------|-------|
| Default model | `backend/app/core/config.py` — `revy_embedding_model = "voyage-code-3"` | Env: `REVY_EMBEDDING_MODEL` |
| Dimensions | `revy_embedding_dimensions = 1024` | Env: `REVY_EMBEDDING_DIMENSIONS`; migration `0021` |
| Client | `backend/app/integrations/voyage_embeddings.py` | Standard `/v1/embeddings`; `input_type` query/document |
| Matryoshka guard | `_FLEXIBLE_DIMENSION_MODEL_PREFIXES` | Includes `voyage-code-3`, `voyage-4*` — **not** `voyage-code-3.5` or `voyage-code-4` yet |
| Smoke script | `backend/scripts/voyage_code_4_smoke_test.py` | Local probe; loads `backend/.env` via `settings` |
| DB column | `github_code_chunks.embedding` | `vector(1024)`; incompatible vectors cleared on dim change |
| Model policy | `docs/models/MODEL_POLICY_FINDINGS.md` | Embedding role exists; workspace UI for embedding **deferred** (MP-D5) |
| **Model run capture** | `docs/models/model-run-capture/` | **Gap:** embedding model not on index manifest or attempts — see MRC findings |
| Staging usage | Operator dashboard (2026-08-10) | `voyage-code-3` ~12.7% of 200M free tier used; staging env → `voyage-code-3.5` |

---

## External research — dashboard vs public docs

### Observed on Voyage account dashboard (operator, 2026-08-10)

Models with **200M free tokens** (new-generation quota pattern):

- `voyage-4`, `voyage-4-large`, `voyage-4-lite`
- **`voyage-code-4`**, **`voyage-code-4-large`**
- `voyage-context-3`, `voyage-context-4`
- `voyage-multimodal-3`, `voyage-multimodal-3.5`
- `rerank-2.5`, `rerank-2.5-lite`

Models with **50M free** (older tier): `voyage-code-2`, `voyage-code-3`, `voyage-finance-2`, `voyage-law-2`.

Models with **0 free** (legacy): `voyage-3`, `voyage-3-large`, `voyage-3-lite`, `voyage-3.5*`, `rerank-2*`.

**Inference (assumption):** `voyage-code-4` / `voyage-code-4-large` are provisioned on the API but **not yet publicly documented** — soft launch ahead of blog/docs, same pattern as early dashboard exposure for other Voyage 4 models.

### Public documentation (verified 2026-08-10)

| Source | `voyage-code-4` | `voyage-code-4-large` | Latest code model listed |
|--------|-----------------|----------------------|--------------------------|
| [docs.voyageai.com/embeddings](https://docs.voyageai.com/docs/embeddings) (updated 2026-01-07) | **No** | **No** | `voyage-code-3` |
| [docs.voyageai.com/pricing](https://docs.voyageai.com/docs/pricing) (updated 2026-07-28) | **No** | **No** | `voyage-code-3` @ $0.18/M |
| [Embeddings API OpenAPI](https://docs.voyageai.com/reference/embeddings-api) | **No** | **No** | recommends `voyage-code-3` |
| Voyage blog | **No dedicated post** | **No dedicated post** | [voyage-code-3](https://blog.voyageai.com/2024/12/04/voyage-code-3/) (Dec 2024) |
| MongoDB Voyage docs | **No** | **No** | `voyage-code-3` |

**Web search:** zero indexed results for exact strings `voyage-code-4` or `voyage-code-4-large` (Aug 2026).

### API smoke (verified 2026-08-10, operator key, `output_dimension=1024`)

Run: `cd backend && PYTHONPATH=. pipenv run python scripts/voyage_code_4_smoke_test.py`

| Model | HTTP | Result | Notes |
|-------|------|--------|-------|
| `voyage-code-3` | 200 | ✅ 1024-dim, 18 tokens | Production default; baseline |
| **`voyage-code-3.5`** | 200 | ✅ 1024-dim, 18 tokens | **Callable but undocumented** on embeddings docs page; API error lists include `voyage-code-3-5` (hyphen) but working id is **`voyage-code-3.5`** (dot) |
| `voyage-code-4` | 503 | ❌ | `"voyage-code-4 server is under heavy load"` — model is **recognized** (not 400) but **not serving** after 5× retry |
| `voyage-code-4-large` | 400 | ❌ | `"Model voyage-code-4-large is not supported"` — **dashboard quota exists; API not deployed** |
| `voyage-4-large` | 200 | ✅ 1024-dim | General model; works as control |

**Cosine similarity (same code sample, 1024-dim):**

| Pair | Similarity | Implication |
|------|------------|-------------|
| `voyage-code-3` vs `voyage-code-3.5` | **0.430** | Different embedding spaces — re-index required to switch |
| `voyage-code-3` vs `voyage-4-large` | **-0.025** | Unrelated spaces — not a drop-in for code index |

**Conclusion:** Dashboard shows future/pre-release models. **`voyage-code-3.5` is the nearest callable upgrade** today; **`voyage-code-4*`** is provisioned in billing UI but not production-ready on the embed API.

### Web research — `voyage-code-3.5` (2026-08-10)

| Source | `voyage-code-3.5` mentioned? | Notes |
|--------|------------------------------|-------|
| [docs.voyageai.com/embeddings](https://docs.voyageai.com/docs/embeddings) | **No** | Latest **code** model listed: `voyage-code-3` only |
| [docs.voyageai.com/pricing](https://docs.voyageai.com/docs/pricing) | **No** | Code pricing row is `voyage-code-3` @ $0.18/M |
| Voyage blog (all posts) | **No** | No `voyage-code-3.5` announcement |
| MongoDB / Pinecone / Vercel / Hugging Face | **No** | Only `voyage-code-3` documented |
| Web search (`"voyage-code-3.5"`) | **Zero hits** | Model exists on API only (stealth) |

**Do not confuse with `voyage-3.5`** (general-purpose, [May 2025 blog](https://blog.voyageai.com/2025/05/20/voyage-3-5/)):

- `voyage-3.5` is evaluated on a **CODE** domain among 8 domains — but it is **not** the code-specialized model.
- Voyage's own guidance (Vercel gateway, Claude docs): for code retrieval use **`voyage-code-3`**, not `voyage-3.5`.
- `voyage-3.5-lite` handles code as one of eight domains for **cost-sensitive moderate accuracy** — wrong fit for Revy's primary code-index path.

**Inferred release pattern (assumption):**

| Series | v3 | v3.5 (incremental) | v4 (major) |
|--------|-----|----------------------|------------|
| General | `voyage-3` | `voyage-3.5` (May 2025, blog) | `voyage-4*` (Jan 2026, blog) |
| Code | `voyage-code-3` (Dec 2024, blog) | **`voyage-code-3.5` (API only)** | **`voyage-code-4*` (dashboard; API 503/400)** |

Gap code-2 → code-3 was **~11 months** (Jan → Dec 2024). Code-3.5 has no public benchmarks — magnitude of gain over code-3 is **unknown**.

### Web research — `voyage-code-4` (2026-08-10)

| Source | Finding |
|--------|---------|
| Voyage blog / docs | **No** `voyage-code-4` post; general [voyage-4 blog](https://blog.voyageai.com/2026/01/15/voyage-4/) does not mention a code variant |
| Web search | No indexed announcement |
| Our API | `voyage-code-4` → 503; `voyage-code-4-large` → 400 unsupported |
| Dashboard | 200M free tier provisioned (billing ahead of API) |

**Likely:** code-4 will mirror voyage-4 (MoE flagship + mid tier + shared code-4 embedding space) — but **unverified** until Voyage ships docs.

### Analogous announced models (pattern for expectations)

| Family | General | Code-specialized | Notes |
|--------|---------|------------------|-------|
| v3 era | `voyage-3-large` | `voyage-code-3` | Separate models; code-3 blog Dec 2024 |
| v4 era | `voyage-4`, `voyage-4-large`, `voyage-4-lite` | **`voyage-code-4`, `voyage-code-4-large`** (dashboard only) | [voyage-4 blog](https://blog.voyageai.com/2026/01/15/voyage-4/) — shared space within **general** 4-series |
| Contextualized | — | — | `voyage-context-4` announced Jun 2026; different API + auto-chunking |

**Likely characteristics (assumption, pending vendor confirmation):**

1. Same `/v1/embeddings` endpoint as `voyage-code-3`.
2. 32K context; Matryoshka dims 256/512/1024/2048 (matches code-3 and voyage-4 series).
3. `voyage-code-4-large` = MoE flagship (mirrors `voyage-4-large`); `voyage-code-4` = mid tier.
4. **Not** interchangeable with `voyage-code-3` vectors — model change ⇒ full re-index (same as any embedding model swap).
5. **Unknown** whether `voyage-code-4` and `voyage-code-4-large` share a code-specific embedding space (analogous to general voyage-4 series).

### Related models — not the same upgrade path

| Model | Revy fit | Why separate |
|-------|----------|--------------|
| `voyage-4-large` | Secondary eval | General-purpose; may underperform code-3 on code benchmarks per Voyage's own positioning |
| `voyage-context-4` | Future R3+ track | Contextualized chunk API; could reduce chunking engineering but requires new client + indexing design |
| `rerank-2.5` | Post-R3 retrieval stage | Reranker, not embedder — architecture §11.3 stage 3 |

---

## Advice / options

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A — Stay on voyage-code-3** | No change | Documented, proven in staging (~25M tokens used), zero migration | Miss `voyage-code-3.5` gains |
| **B — Eval voyage-code-3.5** | Smoke + offline retrieval benchmark | **API-verified callable**; likely incremental upgrade over code-3 | Undocumented on main docs page; re-index; prefix fix in client |
| **C — Wait for voyage-code-4** | Monitor dashboard + retry smoke | Presumed next-gen code model; 200M free tier reserved | **503 / not serving** as of 2026-08-10 |
| **D — Eval voyage-code-4-large** | When API supports it | Expected flagship code MoE | **400 unsupported** today despite dashboard |
| **E — voyage-context-4** | New indexing architecture | Better chunk-context semantics | New API, not a drop-in; largest engineering scope |

**Lean (updated 2026-08-10):** **Wait for `voyage-code-4`** — stay on `voyage-code-3` in production. Optional: low-cost staging eval of `voyage-code-3.5` **only if** you need data before code-4 ships; do **not** re-index production for 3.5 without measured gain.

**Lean (revised 2026-08-10, operator constraint):** **Switch forward to `voyage-code-3.5`** — if past PR indexes are disposable. Dashboard spend UI lists `voyage-code-3.5` (alongside `voyage-code-3`); `voyage-code-4` series not in spend UI yet.

### Decision: switch to 3.5 now vs wait for code-4 official

| Factor | Switch to `voyage-code-3.5` now | Wait for `voyage-code-4` |
|--------|--------------------------------|--------------------------|
| Public benchmarks | ❌ None | ❌ None yet (expected with launch) |
| Docs / pricing | ❌ Undocumented | ❌ Not shipped |
| API readiness | ✅ Callable | ❌ 503 / 400 today |
| Re-index cost | Full re-index now | One re-index when stable |
| **Double re-index risk** | **High** — likely re-index again for code-4 within months | **Low** — single migration |
| Current model standing | `voyage-code-3` still Voyage's **published** code SOTA | — |
| Staging usage | ~25M tokens on code-3; working well | 200M free tier reserved on dashboard |

**Recommendation (revised): switch to `voyage-code-3.5` for new indexing** — if you do not need historical PR retrieval quality.

Operator constraints that change the calculus:
- **No past-PR re-index required** — eliminates the main cost argument for waiting.
- **Dashboard spend UI** shows `voyage-code-3.5` as a billable model (Aug 2026); `voyage-code-4` series not present there yet — 3.5 is the active next step, not a throwaway beta.
- **Revy retrieval is per-revision** (`search_revision_chunks` filters by `revision_id`) — new pushes get indexed with whatever model is in env; old revisions keep code-3 vectors unless re-indexed.

**Caveat (accepted):** After env switch, **query** embeddings use 3.5 but **old revision chunks** remain code-3 — cross-model search is broken (cosine ~0.43). Fine if old PRs are not reviewed again.

**When to move to code-4:** when it appears in dashboard spend + smoke test returns 200; optionally re-index only PRs you still care about.

**Switch checklist:**
1. `REVY_EMBEDDING_MODEL=voyage-code-3.5` in env (staging → prod).
2. No migration — still `vector(1024)`.
3. No code change required — `voyage-code-3.5` matches existing `voyage-code-3` prefix in `_FLEXIBLE_DIMENSION_MODEL_PREFIXES`.
4. New index jobs only; ignore stale revisions.

---

## Revy code changes (if adopted)

Minimal surface — no schema change if staying at 1024:

1. `config.py` / `.env.example` — document `REVY_EMBEDDING_MODEL=voyage-code-4-large` (or `-4`).
2. `voyage_embeddings.py` — add `voyage-code-4` to `_FLEXIBLE_DIMENSION_MODEL_PREFIXES`.
3. **Full re-index** all workspaces after model switch (embeddings incompatible).
4. Optional: staging metrics script coverage for new model id in observability rows.
5. Model catalog / workspace policy — still out of scope per MP-D5 unless we explicitly expand embedding UI.

---

## Data scope & exclusions

**In scope:** R3 PR revision code chunks, dense pgvector retrieval, Voyage API path.

**Out of scope (this doc):** local/HF `EmbeddingBackend`, hybrid FTS+RRF, `voyage-context-4` auto-chunking redesign, reranker integration, multimodal models.

---

## Edge cases

| Case | Risk |
|------|------|
| API accepts `voyage-code-4` but docs omit rate limits / batch token caps | May differ from `voyage-code-3` (120K tokens/request) |
| `voyage-code-4` ≠ `voyage-code-4-large` embedding space | Cannot mix query/doc models without validation |
| Partial re-index after switch | Stale chunks from old model pollute search — must invalidate all embeddings on switch |
| Dashboard free tier 200M vs pricing page silence | Bill risk after eval — confirm $/M before production |
| `voyage-code-3` 50M vs `voyage-code-4` 200M free buckets | Separate quotas; eval can use code-4 bucket without touching code-3 production usage |

---

## Decisions registry

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| VC4-Q1 | Are `voyage-code-4` models callable on our API key? | **partial** | `voyage-code-4` → 503 (recognized, not serving); `voyage-code-4-large` → 400 unsupported |
| VC4-Q1b | Is `voyage-code-3.5` callable? | **resolved** | ✅ HTTP 200 @ 1024; use dot form `voyage-code-3.5` not `voyage-code-3-5` |
| VC4-Q2 | Do code-4 models share embedding space with each other? | **open** | Cannot test until code-4 serves |
| VC4-Q3 | Compatible with `voyage-code-3` vectors? | **resolved (code-3.5)** | **No** — cosine 0.43 on identical input; full re-index required |
| VC4-Q4 | Pricing per 1M tokens? | **open** | Check dashboard billing + watch pricing page |
| VC4-Q5 | Default upgrade target: `-4`, `-4-large`, or `-3.5`? | **resolved** | **Switch to `voyage-code-3.5`** for forward indexing; wait for code-4 when in spend UI + API 200 |
| VC4-Q6 | Stay at 1024 dimensions? | **open** (lean **yes**) | Avoids migration `0021`-style schema change |
| VC4-Q7 | Document folder | **locked** | `docs/models/voyage-embeddings/` |

---

## Parking lot

- Phase-0: Re-run `scripts/voyage_code_4_smoke_test.py` until `voyage-code-4` returns 200.
- Retrieval eval harness: compare `voyage-code-3` vs **`voyage-code-3.5`** on fixed Revy PR corpus.
- Ask Voyage (Discord/sales) for pre-release docs on code-4 series.
- Watch [voyageai blog](https://blog.voyageai.com/) and docs `llms.txt` for announcement.
- Separate findings slice for `voyage-context-4` if chunking strategy becomes a bottleneck.

---

## Devil's advocate

- **Premature upgrade:** code-3 is SOTA-documented for code; undocument code-4 may be identical provisioning placeholder.
- **Wrong model family:** `voyage-4-large` shared-space flexibility might tempt asymmetric query/doc — but code retrieval may still need code-specific models.
- **context-4 leapfrog:** if Voyage's direction is contextualized embeddings, investing in code-4 text embed may be shortly superseded by a larger indexing refactor.

---

## Experiment / verification

| Step | Pass criteria |
|------|---------------|
| API smoke | HTTP 200; embedding length 1024; `usage.total_tokens` > 0 |
| Space check | code-4 vs code-4-large cosine ≈ 1.0 on same input **if** shared space claimed |
| Incompat check | code-3 vs code-4-large cosine ≪ 1.0 on same input |
| Staging index | Index one PR revision; retrieval returns sensible chunks vs code-3 baseline |
| Cost | Record tokens/index job; extrapolate vs code-3 $0.18/M |

---

## References

**Revy code**

- `backend/app/core/config.py` — embedding defaults
- `backend/app/integrations/voyage_embeddings.py` — API client
- `backend/scripts/voyage_code_4_smoke_test.py` — local API probe
- `backend/alembic/versions/2026_07_26_2000_0021_github_code_chunks_embedding_dim.py`
- `docs/review-pipeline/waves/REVIEW_PIPELINE_R3_EXECUTION.md`
- `docs/models/MODEL_POLICY_FINDINGS.md` — MP-D5 embedding UI defer
- `docs/models/model-run-capture/MODEL_RUN_CAPTURE_FINDINGS.md` — per-run model capture program

**Voyage (public)**

- [Text embeddings docs](https://docs.voyageai.com/docs/embeddings)
- [Pricing](https://docs.voyageai.com/docs/pricing)
- [voyage-code-3 blog](https://blog.voyageai.com/2024/12/04/voyage-code-3/)
- [voyage-4 blog](https://blog.voyageai.com/2026/01/15/voyage-4/)
- [voyage-context-4 blog](https://blog.voyageai.com/2026/06/29/voyage-context-4/)
