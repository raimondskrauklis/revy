# Review engineering context — findings

**Date:** 2026-07-29 (platform reframed)  
**Purpose:** Baseline for wiring **intent** (locked decisions, execution contract, operator evidence) into the **Revy product pipeline** — primarily Moonshot review generation — with Greptile as a **parallel validation channel** while we tune Revy. **No execution steps.**

**Status:** Platform scope locked — ready for `create-general-plan`. [judge-json-contract](../judge-json-contract/README.md) merged (#58, `9a7b5cb`); staging deploy done, **no post-deploy judge runs yet** (validation memo pending dogfood).

**Operator context:** Revy is built **primarily for dogfood on this repo** (solo operator workflow). Greptile and Bugbot remain part of daily PR practice and the whole review surface — but **this program's P0 target is Revy**, not tuning hosted/local Bugbot.

**Evidence:** PR [#58](https://github.com/raimondskrauklis/revy/pull/58) dogfood; [REVIEW_QUALITY_REVIEW_CONTEXT.md](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md); [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md); [code-review-arch_perplexity_searcj_advice_only.md](../code-review-arch_perplexity_searcj_advice_only.md); live RTU smoke (2026-07-29).

---

## Summary

**Context is king** — Revy's Moonshot path (`prepare_review_context`) today sends PR metadata + unified diff + RAG supplemental chunks. **No engineering-context layer.** When planning `.md` ships in the same PR, Moonshot sees those hunks in the diff — but that alone misses locks on follow-up PRs, truncation at 128 KB, and the model instruction to focus on "changed logic."

**This program (RCX)** wires engineering context into **Revy first**:

1. **Manifest JSON** (Greptile `files.json` pattern) — index: `active_program`, pointed paths, `scope`.
2. **MD is the content** — LOOP co-commits execution/findings; manifest says *which* docs matter.
3. **`prepare_review_context` inject** — read manifest, resolve MD at `head_sha`, prepend bounded lock/smoke block before diff; skip files already fully in diff.
4. **Greptile parallel** — same manifest feeds `.greptile/files.json`; one edit, two consumers.

PR #58 remains the motivation: generic API advice when locks/smoke are absent from the prompt. Greptile/`revybot` false positives on that PR informed the problem; **fixing the product path is the deliverable.**

**Out of RCX P0:** hosted Bugbot dashboard tuning, `BUGBOT.md` generators — still maintained in daily workflow, not this phase's build target. **RC4–RC6** (workspace DB policy, customer repos) stay post-dogfood.

**Structural context** (call graph, SC8) stays a sibling program — both layers required.

---

## Platform view

```text
  Planning MD (content — co-committed per LOOP)
           │
           ▼
  ┌────────────────────────────┐
  │ Manifest JSON              │  active_program + paths + scope
  │ dogfood: .greptile/        │  product: .revy/review-context.json
  │   files.json + pointer     │
  └─────────────┬──────────────┘
                │
       ┌────────┴────────┐
       ▼                 ▼
  Greptile           Revy pipeline     ← P0 target
  (parallel)         prepare_review_context
                     → Moonshot prompt
                     → judge (later)
```

| Layer | Question | P0 (RCX) | Later |
|-------|----------|----------|-------|
| **Engineering** | What should this PR implement? | Manifest + Moonshot inject | RC4 workspace policy |
| **Operational** | What did live API/DB prove? | Extracted smoke/locks in inject | Same manifest |
| **Structural** | Who calls X? | SC sibling program | SC8 |
| **PR-scoped** | What changed? | Unified diff (unchanged) | — |

**JSON is the pointer. MD is the authority.** Pointing at the active program is the bet — same manifest for Greptile validation and Revy generation.

**Channel priority this phase**

| Channel | Role in RCX |
|---------|-------------|
| **Revy — Moonshot** | **P0** — `prepare_review_context` inject |
| **Revy — judge** | **P1** — reuse extracted locks where prompt allows |
| **Greptile** | **Parallel** — same manifest; validate wiring while tuning Revy |
| **Bugbot** (local + hosted `revybot`) | **Daily workflow** — important in whole pipeline; **not P0 build target** |

---

## Terminology

| Term | Meaning |
|------|---------|
| **Engineering context** | What this PR/program must implement — execution contract, findings locks, operator smoke |
| **Structural context** | Who calls X, impact beyond diff — [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](../review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |
| **Operational context** | Live API/workspace results (RTU smoke, staging SQL) — first-class, not optional appendix |
| **Manifest** | JSON index — `active_program`, paths, `scope`; MD paths resolved at `head_sha` |
| **revybot** | Hosted **Cursor Bugbot** on GitHub — daily workflow; not RCX P0 |
| **RCX** | Review engineering context program IDs (this doc) |

---

## Reviewer channels (verified)

| Channel | Mechanism | Engineering context today | RCX phase |
|---------|-----------|---------------------------|-----------|
| **Revy — Moonshot** | `prepare_review_context` → `_build_review_prompt` | Diff + PR body + RAG only; **no manifest** | **P0 inject** |
| **Revy — judge** | `_build_judge_prompt` | Snippet-first (#58); no policy rows | P1 — reuse lock extract |
| **Greptile** | `.greptile/files.json` + `scope` | Wired; 15 programs on every `backend/**` PR | **Parallel** — trim to active program |
| **Bugbot** (local + hosted) | `BUGBOT.md` + Task subagent | RC0 links; stale/noisy list | **Maintain** daily; not P0 build |

**Verified code:** `github_review.py:754` `prepare_review_context` — no manifest read, no policy injection. `DIFF_MAX_BYTES` = 128 KB (truncation drops largest patches). Prompt instruction: "Focus on introduced or changed **logic** in the unified diff."

**Moonshot diff path (baseline, not sufficient alone):** co-committed `.md` appears in `unified_diff` when under budget. Gaps: follow-up code-only PRs, truncation, model under-weighting MD hunks.

---

## Context layers (target model)

```text
  Priority (highest wins on conflict)
  ───────────────────────────────────
  1. Locked decision IDs     JC-D*, FR-Q*, RC-D* in findings
  2. Operator smoke / staging SQL   P0 matrix, validation memo
  3. Execution contract      active phase file + gates
  4. General plan / README   phase goals, out-of-scope
  5. Generic API / training prior   LOWEST — must not override 1–2
```

| Layer | Question | Today | Target (RCX P0) |
|-------|----------|-------|-----------------|
| **Engineering** | What should this PR implement? | Greptile only (vendor); Moonshot via diff luck | Manifest → Moonshot inject |
| **Operational** | What did live API/DB prove? | Manual findings tables | Extracted locks/smoke in inject |
| **Structural** | Who calls X? | SC3 manifest; RQ-STRUCT-1 | SC8 (sibling) |
| **Temporal** | Which program is active? | Stale multi-program lists | `active_program` in manifest |
| **PR-scoped** | What changed? | Unified diff | Unchanged; inject **before** diff |

---

## Problem statement

1. **Revy Moonshot has no engineering-context layer** — `prepare_review_context` never reads manifest or extracts locks; co-commit diff is necessary but not sufficient.
2. **Intent drift on program PRs** — without lock block, model falls back to generic API lore (PR #58 class: `format.name`, `output_config` advice).
3. **Greptile noise** — `files.json` lists every shipped program on `backend/**` PRs; parallel channel needs active-program trim.
4. **Manifest drift** — `.greptile/files.json` and `.cursor/BUGBOT.md` diverge today; one manifest must feed Greptile + Revy.
5. **Operator smoke** — live API/DB results belong in findings; inject must surface **extracted** smoke/locks, not full 300-line findings.
6. **Customer path (later)** — no `.greptile/` in customer repos → RC4 `workspace_review_policy` after dogfood proves inject shape.
7. **Bugbot** — stale `BUGBOT.md`, PR #58 false positives; important for daily workflow, **deferred from RCX P0 build** (maintain manually until manifest stabilizes).

---

## What exists vs genuinely new

| Asset | Status | Reuse notes |
|-------|--------|-------------|
| RC0 wiring (Greptile + Bugbot links) | **Shipped** RQ0 | Greptile pattern; Bugbot maintained separately this phase |
| `.greptile/files.json` schema | **Shipped** | Dogfood manifest shape; add `active_program` |
| `prepare_review_context` | **Shipped** | **P0 injection point** — prepend engineering block |
| `REVIEW_QUALITY_REVIEW_CONTEXT.md` | **Strategy** | RC1–RC6 ladder; RCX absorbs RC1–RC2 + RC5 dogfood |
| `OUTPUT_FORMAT.md` + babysit skill | **Shipped** | Disposition helpers (P2) |
| `.revy/review-context.json` | **Not built** | Product manifest path; dogfood uses `.greptile/files.json` first |
| `workspace_review_policy` DB | **Not built** | RC4 — post-dogfood |
| `BUGBOT.md` | **Shipped** | Daily workflow; not P0 generator target |

---

## Industry patterns (distilled)

Source: [PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md), [code-review-arch advice](../code-review-arch_perplexity_searcj_advice_only.md), Greptile docs. **Adopt / defer / reject for Revy:**

| Pattern | Industry | Revy verdict | RCX relevance |
|---------|----------|--------------|---------------|
| **Config-driven rules in repo** | `.greptile/rules`, cascading dirs | **Adopt dogfood** — already `files.json`; add RC3 per-dir later | RCX-G1 manifest |
| **Planning doc injection** | Greptile `files.json` descriptions | **Adopt** — manifest + Moonshot inject; Greptile parallel | Core program |
| **Repo graph at review time** | Greptile graph + agent swarm | **Defer** — SC8; not RCX | Sibling SC program |
| **Custom YAML rules per tenant** | Ellipsis/CodeRabbit | **Defer product** — RC4 DB EN+LV | Post-dogfood |
| **Evidence attached at generation** | Snippet link per finding | **Partial** — judge snippet-first shipped; PR bots need claim→lock citation | Align with R5 grounding |
| **Grounding / entailment judge** | Layer 3 filter | **Shipped** R5 judge; extend to **bot disposition** (human cites lock) | RCX-G5 |
| **Generator exploratory + filter precise** | Bugbot agentic loop | **Adopt philosophy** — bots may be noisy if context layer 1–2 present | Don't over-constrain hosted Bugbot format (RC-D23) |
| **Shuffled-diff majority voting** | Bugbot | **Reject v1** — eval only | Noise reduction via context, not multi-pass |
| **Incremental context index** | Chunk-hash embed | **Defer** R9 | Product retrieval, not PR bot |
| **Auto-ingest CLAUDE.md / .cursor/rules** | Greptile v3 auto-detect | **Partial** — detects dev-agent rules, **not** program findings/smoke unless in `files.json` | Explains #58 `format.name` miss |
| **Learn from PR comments** | Greptile memory | **Future** R8+ | Out of RCX v1 |
| **Active slice / phase pointer** | Implicit in good teams | **Adopt RC2** — one-line active program in `BUGBOT.md` + manifest | RCX-G3 |

**Insight:** Industry tools separate **exploration** (generators) from **precision** (filters + policy). Revy's missing piece is the **policy input** in `prepare_review_context` (layers 1–2), not another review pass.

---

## External research (web, verified 2026-07-29)

Vendor docs and context-engineering literature — **adopt / defer / reject** for RCX.

### Greptile ([config reference](https://www.greptile.com/docs/code-review/greptile-config-reference), [customization](https://www.greptile.com/docs/code-review/customization-overview))

| Finding | Implication for Revy |
|---------|-------------------|
| **`.greptile/` folder** is now recommended: `config.json` + `rules.md` + `files.json`, **cascading** per directory | Align RC3 with vendor — monorepo `backend/.greptile/` later; today root `files.json` is valid legacy shape |
| **`files.json` accumulates** from parent configs (child adds, does not replace) | Same noise risk as `BUGBOT.md` — active program trim still required (RC2) |
| **`scope` globs** on each file entry | **Already used** — `backend/**`; matches vendor best practice |
| **`context.repos`** — read related repos during review | **Defer** — Revy dogfood is single-repo |
| **Priority:** org-enforced dashboard rules → `.greptile/` → `greptile.json` | Parallels Bugbot Team Rules — dashboard can override repo files |
| **v3 agentic** — recursive codebase search, git history, graph index ([v3 blog](https://www.greptile.com/blog/greptile-v3-agentic-code-review)) | Structural layer (SC8), not RCX; Greptile explores widely but still needs **locked decisions** in `files.json` |
| **Auto-detect** `CLAUDE.md`, `.cursor/rules` ([changelog](https://www.greptile.com/changelog)) | Dev-agent conventions ≠ program execution findings — **does not replace** wiring `JUDGE_JSON_CONTRACT_FINDINGS.md` |
| **MCP server** — manage custom context from editor | **Defer** — interesting for operator workflow, not P0 |
| **Memory** from past PR comments | **Defer** R8+ — same row as PRODUCT_PATTERNS |

### Cursor Bugbot ([docs](https://cursor.com/docs/bugbot)) — reference; **not RCX P0**

| Finding | Implication for Revy |
|---------|-------------------|
| **Separate from `.cursor/rules`** — rules steer coding agent, not reviewer | Confirms RCX scope: `BUGBOT.md` ≠ `.cursor/rules`; don't duplicate AGENTS content |
| **Merge order:** Team Rules → repo rules (learned + manual) → **`BUGBOT.md`** (root + nested, walk upward from changed files) → User Rules | **Answers RCX-Q2 partially** — hosted `revybot` **does** read repo `BUGBOT.md` on `main`, but **Team Rules win** if they conflict |
| **Nested** `backend/.cursor/BUGBOT.md` included when reviewing backend paths | **Adopt RC3** — path-scoped active program block without loading full corpus |
| **Caps:** 30k chars/rule, **100k combined** rules per review | **New constraint** — long `BUGBOT.md` + six program link lists may truncate; need **slim active block** + manifest (RCX-G1) |
| **`@cursor remember [fact]`** on PR → learned repo rule | **Adopt for disposition** — operator can teach P3 lock after smoke; not a substitute for findings doc |
| **Custom effort** level — natural-language routing for infra/backend PRs | Dogfood tip for program PRs touching `anthropic_review.py` |
| **Must merge to `main`** before hosted review sees `BUGBOT.md` changes | Same as our LOOP — context updates ship with program merge |
| **Does not read** `.cursor/rules` | Engineering context must live in `BUGBOT.md` or dashboard rules explicitly |

### Context engineering (industry, non-vendor)

Sources: [Packmind playbook](https://packmind.com/context-engineering-ai-coding/context-engineering-playbook/), [design.dev guide](https://design.dev/guides/context-engineering/).

| Pattern | Adopt for RCX? |
|---------|----------------|
| **Path / file-type scoped rules** — only apply where relevant | **Yes** — RC1 + nested `BUGBOT.md` / Greptile `scope` |
| **Short imperative rules** (~25 words) + code examples | **Yes** — top of `BUGBOT.md`: “**Never** recommend `format.name` on RTU gateway (JC P3 lock)” |
| **`AGENTS.md` as cross-tool SSOT** | **Defer** — Revy uses program `findings` + `execution`; optional thin `AGENTS.md` pointer later |
| **Lost in the middle** — critical context at **start and end** of instruction file | **Yes** — active program + lock IDs at **top** of `BUGBOT.md`; links below |
| **Some tools read only first ~4k chars** of review instructions (Copilot-class) | **Yes** — active lock block must fit in first screen |
| **Drift audit** — compare context files to codebase quarterly | **Adopt** — peer-review + post-ship gap pass on program closeout |
| **Policy as code in git** — reviewers read same versioned policy | **Yes** — RCX-D1; RC4 productizes later |

**RCX-Q2 update:** Hosted Bugbot **can** consume repo context via `BUGBOT.md` (and nested files). Gap is **content design** (noise, missing smoke, char cap), not absence of a hook. **Team dashboard rules** may still override — verify what's configured on `raimondskrauklis/revy`.

---

## Dogfood evidence

### PR #58 (judge-json-contract)

| Signal | Result |
|--------|--------|
| Greptile confidence | 5/5 — still cited `format.name` (P2) from schema shape, not RTU workspace |
| Hosted revybot | Useful hygiene + **false-positive API** warnings (`output_config`, circular import) |
| Local Bugbot | Caught real issues; fixed before merge |
| Operator RTU smoke | Locks P3 — structured output off on gateway |
| Staging | #58 deployed; **no new judge runs** yet — validation metrics TBD on latest runs only |

### PR #50 (review-quality RC0)

| Signal | Result |
|--------|--------|
| RC-D3 | **Pass** — Greptile cited AS1 on `index_mode` when wired |
| RC-D20 | Greptile 👀 = ack only, not comprehension |

---

## Locked decisions

| ID | Decision |
|----|----------|
| **RCX-D1** | **Single manifest** — one JSON index per active program; Greptile + Revy consume the **same** paths. |
| **RCX-D2** | **JSON is pointer, MD is content** — LOOP co-commits planning docs; manifest resolves paths at `head_sha`. |
| **RCX-D3** | **Operator evidence is first-class** — smoke matrices, live API errors, staging SQL in findings; inject extracts locks/smoke only. |
| **RCX-D4** | **Revy product first** — `prepare_review_context` inject is P0; Greptile parallel; Bugbot maintained but not P0 build. |
| **RCX-D5** | **Out of scope v1** — replacing Greptile; SC8 graph; `BUGBOT.md` auto-generator; RC4 DB. |
| **RCX-D6** | **Latest-run metrics only** — staging validation uses post-deploy window (`--since`), not full history. |
| **RCX-D7** | **Context over format** — locked decisions + evidence beat generic API advice (RC-D23). |
| **RCX-D8** | **Moonshot inject shape** — read manifest → resolve MD at `head_sha` → prepend bounded block (active program + extracted locks/smoke) **before** unified diff; skip paths already fully in diff. |
| **RCX-D9** | **One edit, two consumers** — manifest update feeds Greptile `files.json` and Revy inject; no hand-duplicated path lists. |
| **RCX-D10** | **Raise prompt caps (dogfood)** — operator spend is low; safe to increase `DIFF_MAX_BYTES` (128 KB today) and engineering-inject budget in RCX P0. Prefer config/env over hardcoded constants; revisit after cost telemetry on program PRs. |

---

## Prompt caps (today → RCX P0)

| Cap | Today (`github_review.py`) | RCX P0 direction |
|-----|---------------------------|------------------|
| Unified diff | `DIFF_MAX_BYTES` = **128 KB** | **Raise** — dogfood spend low; fewer omitted patches on large program PRs |
| PR body | `PR_BODY_MAX_BYTES` = 4 KB | Keep or modest raise if RC2-lite bodies grow |
| Engineering inject | N/A | New bounded budget (extracted locks/smoke); can be **generous** vs 300-line findings — still extract, not dump |
| Supplemental RAG | 15 (diff) / 30 (full) chunks | Unchanged unless retrieval noise shows up |

**Operator position (2026-07-29):** Spending is low — **do not optimize caps down** at the cost of dropped MD/diff on program PRs. Inject + higher diff cap are complementary (inject for locks off-diff; cap for co-committed docs in diff).

## Moonshot inject (locked design — RCX-D8)

**Algorithm (P0):**

1. **Read manifest** — dogfood: `.greptile/files.json` + `active_program` field; product: `.revy/review-context.json` (same schema, later).
2. **Filter** — active program paths only; respect `scope` against changed files (RC1).
3. **Resolve** — fetch pointed `.md` at `head_sha` (GitHub API or compare tree).
4. **Extract** — `## Locked decisions`, operator smoke tables, active execution gates — **bounded** byte budget; not full findings corpus.
5. **Dedupe** — skip files whose full content is already represented in `unified_diff` for this revision.
6. **Prepend** — engineering context block **before** unified diff in `_build_review_prompt`; adjust review instruction to treat block as authoritative over generic prior.

**When inject adds value (beyond diff alone):**

| Scenario | Diff alone | Inject needed |
|----------|------------|---------------|
| Program PR, MD co-committed, under budget | Often sufficient | Lock block still helps model weight intent |
| Large PR, diff truncated | Partial | **Yes** — inject pointed docs even if omitted |
| Code-only follow-up PR | No intent docs | **Yes** |
| Customer repo (later) | Unlikely | **Yes** — RC4 policy rows |

---

## Success criteria (dogfood)

1. Moonshot prompt includes **engineering context block** from manifest on `backend/**` program PRs.
2. Revy findings on program PRs **do not contradict** locked IDs (JC-D*, P3 lock) when smoke is in findings.
3. **Single manifest edit** updates Greptile `files.json` and Revy inject (one edit, two consumers).
4. **Active program only** in manifest — Greptile stops loading 15 programs per PR.
5. Inject block stays **under budget** — no 300-line findings dump; extracted locks/smoke only.
6. Operator can verify inject in pipeline trace / retrieval manifest (instrumentation TBD in plan).

**Secondary (not P0 gate):** Greptile/Bugbot improvement on same PRs — tracked, not blocking ship.

---

## Deliverables (for general plan)

| # | Deliverable | Phase | Notes |
|---|-------------|-------|-------|
| **RCX-G1** | **Manifest schema** | P0 | `active_program` + paths + `scope`; dogfood: extend `.greptile/files.json` |
| **RCX-G2** | **Moonshot inject** | P0 | `prepare_review_context` — RCX-D8 algorithm; tests + manifest in trace |
| **RCX-G2b** | **Raise diff cap** | P0 | `DIFF_MAX_BYTES` via config; RCX-D10 — dogfood spend headroom |
| **RCX-G3** | **Lock/smoke extractor** | P0 | Parse findings MD sections; bounded output |
| **RCX-G4** | **Active program trim** | P0 | One program in manifest; Greptile noise fix (RC1) |
| **RCX-G5** | **Greptile sync** | P0 | Generate or validate `files.json` from manifest — parallel consumer |
| **RCX-G6** | **Judge prompt reuse** | P1 | Share extracted locks with judge path where applicable |
| **RCX-G7** | **Disposition helpers** | P2 | Babysit: lock ID + evidence in thread replies |
| **RCX-G8** | **RC4 spike** | Post-dogfood | `workspace_review_policy` EN+LV — customer manifest in DB |

**Deferred from P0:** `BUGBOT.md` generator, hosted Bugbot dashboard audit, nested `.greptile/` (RC3).

---

## Gap registry

| ID | Gap | Evidence |
|----|-----|----------|
| **RCX-1** | **Moonshot has no manifest inject** | `prepare_review_context` — diff + RAG only |
| **RCX-2** | Co-commit diff insufficient alone | 128 KB truncation; "focus on logic" instruction; code-only follow-ups |
| **RCX-3** | Greptile loads all shipped programs | 15 `files.json` entries on every `backend/**` PR |
| **RCX-4** | Manifest drift Greptile vs Bugbot | paths differ; stale active pointer in `BUGBOT.md` |
| **RCX-5** | Customer repos need DB policy | PRODUCT_PATTERNS — no `.greptile/` |
| **RCX-6** | No lock/smoke extractor | Full findings too large for prompt |
| **RCX-7** | No inject dedupe vs diff | Risk duplicating MD already in unified diff |
| **RCX-8** | Judge lacks shared lock extract | Snippet-first only (#58) |
| **RCX-9** | Bugbot stale/noisy context | PR #58; daily workflow — **not P0** |
| **RCX-10** | No disposition contract | Babysit ad hoc |
| **RCX-11** | Greptile v3 auto-ingest ≠ program findings | #58 `format.name` — needs manifest wiring |
| **RCX-12** | No pipeline trace for inject | Operator cannot verify what Moonshot saw |

---

## Discussion resolutions (operator, 2026-07-29)

### Platform reframing (accepted)

- **P0 target = Revy product** (`prepare_review_context` → Moonshot), not Bugbot tuning.
- **Greptile = parallel** — borrow `files.json` pattern; validate manifest while tuning Revy.
- **JSON = pointer, MD = content** — LOOP co-commits planning docs; manifest says which paths matter.
- **Bugbot** — daily workflow, whole pipeline; **not P0 build** for RCX (maintain manually).
- **Prompt caps** — safe to **raise** `DIFF_MAX_BYTES` and inject budget; dogfood spend is low (RCX-D10).

### RCX-Q1 — Manifest SSOT?

**Locked:** One manifest feeds **Greptile + Revy**. Dogfood: extend `.greptile/files.json` with `active_program`. Product: `.revy/review-context.json` (same schema, RC4). CI: path-exists validation. `BUGBOT.md` is **not** a manifest consumer in P0.

### RCX-Q2 — Hosted Bugbot / manifest?

**Deferred from P0.** Bugbot reads `BUGBOT.md` text, not JSON. Relevant to daily workflow; revisit after manifest + Moonshot inject ship. Dashboard Team Rules audit — operator, not blocking RCX P0.

### RCX-Q3 — Active program trim?

**Locked:** Noise is multi-program `files.json` on every `backend/**` PR — not "full corpus." Active program only (3 docs per program). Moonshot diff handles co-committed MD; inject adds locks when diff is insufficient.

### RCX-Q4 — Moonshot inject?

**Locked: Yes in RCX P0** (RCX-D8). Algorithm agreed:

1. Read manifest (`.greptile/files.json` + `active_program` or `.revy/review-context.json`)
2. Resolve pointed MD at `head_sha`
3. Prepend bounded block before diff: active program name + extracted locks/smoke
4. Skip files already fully in diff
5. Greptile keeps same manifest — one edit, two consumers

### RCX-Q5 — Fold into RQ-RC-1?

**Locked:** Standalone RCX; absorb RQ-RC-1 RC1–RC2 + RC5 dogfood inject into RCX P0–P1.

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **RCX-Q1** | Manifest SSOT? | **locked** | One manifest → Greptile + Revy; dogfood `.greptile/files.json` + `active_program` |
| **RCX-Q2** | Hosted Bugbot + manifest? | **deferred** | Not P0; maintain `BUGBOT.md` manually this phase |
| **RCX-Q3** | Active program trim? | **locked** | Active program only in manifest; not full corpus |
| **RCX-Q4** | Moonshot inject in RCX P0? | **locked** | **Yes** — RCX-D8 algorithm |
| **RCX-Q5** | Merge with RQ-RC-1? | **locked** | RCX standalone; RQ-RC-1 folds into RCX P0–P1 |

---

## Edge cases

- **Diff dedupe** — inject must not repeat MD already fully in `unified_diff`; partial hunks may still need lock extract.
- **Truncation** — 128 KB diff cap drops largest patches; inject is fallback for omitted docs.
- **Frontend program PRs** — `scope: ["backend/**"]` excludes `frontend/**`; RC3 cascading rules later.
- **Docs-only PRs** — inject still runs when manifest paths match scope.
- **Bugbot** — may stay stale this phase; operator maintains `BUGBOT.md` for daily workflow separately.
- **Conflicting locks** — two programs' findings disagree; `active_program` resolves; human escalation.

---

## Devil's advocate

- **Inject adds tokens** — bounded extract mandatory; full findings dump will hurt Moonshot quality.
- **Extractor fragility** — `## Locked decisions` heading conventions must stay stable or parser breaks.
- **Greptile parallel may lag** — if `files.json` not generated from manifest, drift returns.
- **Customer RC4** — dogfood manifest shape must generalize to DB rows or rework.

---

## Parking lot

- `BUGBOT.md` generator from manifest (post-P0).
- Hosted Bugbot dashboard audit.
- Link validation memo metrics into findings operational layer.
- RC6 `read_planning_doc` agent tool — pairs with SC8.
- Nested `.greptile/` per directory (RC3).

---

## Experiment / verification

| Pass/fail | Measure |
|-----------|---------|
| **Pass** | Pipeline trace shows engineering context block on program PR |
| **Pass** | Moonshot findings do not contradict locked IDs when smoke in findings |
| **Pass** | Single manifest edit updates Greptile + Revy inject |
| **Pass** | Inject block under byte budget; no full findings paste |
| **Fail → trim** | Greptile still loads >1 active program |

---

## References

| Source | Path |
|--------|------|
| RC strategy | [REVIEW_QUALITY_REVIEW_CONTEXT.md](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) |
| Structural sibling | [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](../review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |
| Product pattern map | [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) |
| Industry depth | [code-review-arch_perplexity_searcj_advice_only.md](../code-review-arch_perplexity_searcj_advice_only.md) |
| Greptile config | https://www.greptile.com/docs/code-review/greptile-config-reference |
| Bugbot rules | https://cursor.com/docs/bugbot |
| Context engineering | https://packmind.com/context-engineering-ai-coding/context-engineering-playbook/ |
| Bugbot contract | `.cursor/BUGBOT.md` |
| Review context code | `backend/app/services/github_review.py` (`prepare_review_context`) |
| Judge prompts | `backend/app/services/github_finding_judge.py`, `judge_prompt_context.py` |
| Agent roles | [agents/prompts/ROLES.md](../agents/prompts/ROLES.md) |
| Judge-json parallel | [JUDGE_JSON_CONTRACT_FINDINGS.md](../judge-json-contract/JUDGE_JSON_CONTRACT_FINDINGS.md) |

---

## Next steps

1. `create-general-plan` — RCX P0: manifest schema + Moonshot inject (RCX-D8) + Greptile sync.
2. Dogfood PR — verify inject in pipeline trace on next program slice.
3. Staging validation — latest runs only after post-#58 dogfood (track L, separate).
