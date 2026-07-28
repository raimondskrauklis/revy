# Review engineering context — findings

**Date:** 2026-07-29 (expanded)  
**Purpose:** Baseline for wiring **intent** (locked decisions, execution contract, operator evidence) into **all** reviewers — PR bots and the Revy product pipeline — not only Greptile and Cursor Bugbot. **No execution steps.**

**Status:** Findings expanded — ready for `create-general-plan` + discussion. [judge-json-contract](../judge-json-contract/README.md) merged (#58, `9a7b5cb`); staging deploy done, **no post-deploy judge runs yet** (validation memo pending dogfood).

**Evidence:** PR [#58](https://github.com/raimondskrauklis/revy/pull/58) dogfood; [REVIEW_QUALITY_REVIEW_CONTEXT.md](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md); [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md); [code-review-arch_perplexity_searcj_advice_only.md](../code-review-arch_perplexity_searcj_advice_only.md); live RTU smoke (2026-07-29).

---

## Summary

**Context is king** — but Revy currently wires it **unevenly**. Greptile and Cursor Bugbot get program docs via RC0 (`.greptile/files.json`, `.cursor/BUGBOT.md`). **Hosted GitHub Bugbot** (`revybot[bot]`) and the **Revy product pipeline** (Moonshot review + Anthropic judge) do **not** get the same engineering context — so they fall back to generic API lore and miss locked program decisions.

PR #58 is the canonical failure mode: Greptile recommended `format.name` (wrong for RTU); `revybot` questioned `output_config` vs `output` (wrong — gateway accepts `output_config`; failure is feature unsupported). Operator smoke locked P3. **Neither bot had operator evidence; revybot had no program docs at all.**

This program is the **RC track extension** (RCX): dogfood wiring first, then product (`workspace_review_policy` / RC4–RC6). **Structural context** (call graph, SC8) stays a sibling program — both layers are required.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Engineering context** | What this PR/program must implement — execution contract, findings locks, operator smoke |
| **Structural context** | Who calls X, impact beyond diff — [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](../review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |
| **Operational context** | Live API/workspace results (RTU smoke, staging SQL) — first-class, not optional appendix |
| **Active program pointer** | Which slice is current (RC2) — reduces noise from 6+ shipped programs in `BUGBOT.md` |
| **revybot** | Hosted **Cursor Bugbot** on GitHub (`revybot[bot]`) — distinct from local Task Bugbot subagent |
| **RCX** | Review engineering context program IDs (this doc) |

---

## Reviewer channels (verified)

| Channel | Mechanism | Engineering context today | Structural context | Operational evidence |
|---------|-----------|---------------------------|------------------|----------------------|
| **Greptile** | `.greptile/files.json` + `scope` | **Partial** — wired paths; stale multi-program list | Vendor graph (external) | Only if findings updated manually |
| **Cursor local Bugbot** | Task subagent + brief + `BUGBOT.md` | **Yes** when master passes contract § | Diff only | Master reads thinking export (RC-D23) |
| **Hosted GitHub Bugbot** | `revybot[bot]` + `.cursor/BUGBOT.md` on `main` | **Weak** — appended to Cursor default; no path-scoped slice | Diff only | **No** |
| **Revy product — Moonshot** | `prepare_review_context` → `_build_review_prompt` | **No** — PR title/body + diff + RAG chunks only | R3/R4 retrieval only | N/A |
| **Revy product — judge** | `_build_judge_prompt` / verification prompt | **Partial** — snippet-first tier (shipped #58); no workspace policy | Scoped patch/snippet | Parse retry + manifest (shipped #58) |

**Verified paths:** `.greptile/files.json` (15 program entries, all `backend/**`); `.cursor/BUGBOT.md` (lists judge-input-quality, generation-lifecycle, hardening, review-quality, finding-resolution, judge-json-contract — **no active pointer**); `github_review.py:754` `prepare_review_context` — no policy/rules injection.

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

| Layer | Question | v1 dogfood | Target (RCX) |
|-------|----------|------------|--------------|
| **Engineering** | What should this PR implement? | Greptile + local Bugbot | All PR bots + product inject |
| **Operational** | What did live API/DB prove? | Manual findings tables | Same manifest as engineering |
| **Structural** | Who calls X? Blast radius? | SC3 manifest; RQ-STRUCT-1 | Graph agent (SC8) |
| **Temporal** | Which program phase is active? | Manual README edits | RC2 pointer in one file |
| **PR-scoped** | What changed in this diff? | All channels get diff | Unchanged |

---

## Problem statement (expanded)

1. **Intent drift** — hosted `revybot` flags code matching **locked** decisions (P3 structured-output lock, RTU gateway shape).
2. **Incomplete context even where wired** — Greptile has findings docs but not **operator smoke** until human updates findings (P0 matrix on #58 after operator run).
3. **Context noise** — `files.json` + `BUGBOT.md` list **every shipped program**; reviewers cite wrong phase (RC2 gap).
4. **Triple maintenance** — each new program: Greptile JSON + Bugbot MD + (missing) revybot/hosted path; phase-execution RC0 covers two only.
5. **Product gap** — customer repos won't have `.greptile/`; Moonshot/judge must get policy from DB (RC4–RC5), not vendor files.
6. **Same failure class as judge-json-contract** — prompt-only contract without structured context → parse/contract failures; PR review bots exhibit **advice hallucination** when engineering context missing (symmetric problem, different surface).
7. **Disposition friction** — closing bot threads requires **locked ID + evidence** reply; no standard helper (RCX-G5).

---

## What exists vs genuinely new

| Asset | Status | Reuse notes |
|-------|--------|-------------|
| RC0 wiring (Greptile + Bugbot links) | **Shipped** RQ0 | Extend, don't fork |
| `.greptile/files.json` schema | **Shipped** | Single source candidate for RCX-G1 |
| `BUGBOT.md` | **Shipped** | Stale program list; needs RC2 block at top |
| `REVIEW_QUALITY_REVIEW_CONTEXT.md` | **Strategy doc** | RC1–RC6 ladder; RCX implements RC1–RC2 + revybot |
| `OUTPUT_FORMAT.md` + babysit skill | **Shipped** | Disposition + VALIDATE/CLOSE verbs |
| `prepare_review_context` | **Shipped** | Injection point for RC5 product path |
| `workspace_review_policy` DB | **Not built** | RC4 — post-dogfood |
| Hosted Bugbot dashboard rules | **External** | May override repo `BUGBOT.md` — document precedence (ROLES.md) |

**Trap:** Hand-copying `files.json` paths into a second revybot config **will drift** (RCX-D2).

---

## Industry patterns (distilled)

Source: [PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md), [code-review-arch advice](../code-review-arch_perplexity_searcj_advice_only.md), Greptile docs. **Adopt / defer / reject for Revy:**

| Pattern | Industry | Revy verdict | RCX relevance |
|---------|----------|--------------|---------------|
| **Config-driven rules in repo** | `.greptile/rules`, cascading dirs | **Adopt dogfood** — already `files.json`; add RC3 per-dir later | RCX-G1 manifest |
| **Planning doc injection** | Greptile `files.json` descriptions | **Adopt** — extend to hosted Bugbot + product | Core program |
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

**Insight:** Industry tools separate **exploration** (generators) from **precision** (filters + policy). Revy's missing piece for **dogfood PR bots** is the **policy/filter input** (layers 1–2), not another review pass.

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

### Cursor Bugbot ([docs](https://cursor.com/docs/bugbot))

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
| **RCX-D1** | **Single source of truth** — one doc set per active program; all reviewers consume the **same** paths. |
| **RCX-D2** | **Do not duplicate Greptile JSON by hand** — shared manifest from `.greptile/files.json` (or generated wrapper). |
| **RCX-D3** | **Operator evidence is first-class** — smoke matrices, live API errors, staging SQL belong in findings; priority layer 2. |
| **RCX-D4** | **Dogfood first** — wire hosted `revybot` + tighten Greptile/Bugbot noise before RC4 DB. |
| **RCX-D5** | **Out of scope v1** — replacing Greptile; SC8 graph; auto-sync every LOOP commit without human findings touch. |
| **RCX-D6** | **Latest-run metrics only** — staging validation and operational context use post-deploy window (`--since`), not full history. |
| **RCX-D7** | **Context over format** — hosted/local Bugbot output shape is not the gate; locked decisions + evidence are (RC-D23). |

---

## Success criteria (dogfood)

1. Hosted `revybot` cites **locked IDs** (JC-D*, P3 lock) when flagging contract issues — same bar as Greptile RC-D3 on PR #50.
2. Hosted `revybot` does **not** recommend changes that contradict findings (e.g. `format.name` on RTU).
3. One findings smoke update visible to **Greptile + Bugbot + hosted path** without three edits.
4. **Active program pointer** — reviewers stop citing shipped programs (judge-input-quality on #58-scale PRs).
5. False-positive rate on program PRs drops vs PR #58 baseline (operator-tracked).
6. Disposition template: thread reply = lock ID + smoke/sql evidence (babysit).

---

## Deliverables (for general plan)

| # | Deliverable | Notes |
|---|-------------|--------|
| **RCX-G1** | Shared context manifest | Parse `.greptile/files.json`; **generate slim `BUGBOT.md` header** (locks + active program under 4k) |
| **RCX-G2** | Hosted Bugbot / revybot dogfood wiring | Cursor team rules or manifest injection — verify dashboard precedence |
| **RCX-G3** | Active program pointer | Top of `BUGBOT.md` + manifest; RC2 |
| **RCX-G4** | Findings smoke section contract | Standard table (operator); link from manifest |
| **RCX-G5** | Disposition helpers | Babysit: lock ID + evidence in thread replies |
| **RCX-G6** | RC1 path-scoped subsets | `backend/**` → active program docs only, not full corpus |
| **RCX-G7** | RC4 spike | `workspace_review_policy` shape EN+LV — post-dogfood |
| **RCX-G8** | RC5 product inject | `prepare_review_context` + judge prompts read workspace policy rows |

---

## Gap registry

| ID | Gap | Evidence |
|----|-----|----------|
| **RCX-1** | Hosted `revybot` has no engineering context | PR #58 API false positives |
| **RCX-2** | Greptile lacks live smoke unless findings updated | P0 matrix after operator run |
| **RCX-3** | Three+ manual wires per program | phase-execution RC0 = 2 channels |
| **RCX-4** | `BUGBOT.md` / `files.json` context noise | 6+ shipped programs listed |
| **RCX-5** | Customer repos need DB policy | PRODUCT_PATTERNS — no `.greptile/` |
| **RCX-6** | Moonshot review has no workspace/program policy | `prepare_review_context` — diff+RAG only |
| **RCX-7** | No context priority / conflict rule encoded | Bots override locks with generic API advice |
| **RCX-8** | Hosted vs local Bugbot precedence unclear | ROLES.md dashboard override; RC-D23 |
| **RCX-9** | No disposition contract for lock+cite replies | Babysit ad hoc |
| **RCX-10** | Product judge fixed in #58; **PR review bots** still prompt-only policy | Symmetric context gap |
| **RCX-11** | Bugbot **100k combined rule cap** — six-program `BUGBOT.md` may truncate | [Cursor Bugbot docs](https://cursor.com/docs/bugbot) |
| **RCX-12** | **Team Rules** precede repo `BUGBOT.md` — dashboard may override dogfood wiring | Same precedence class as Greptile org rules |
| **RCX-13** | Greptile v3 auto-ingest ≠ program findings — `files.json` still manual per program | #58 `format.name` |
| **RCX-14** | No **short lock block** at top of review instructions | Industry lost-in-the-middle + 4k limits |

---

## Decisions registry (open)

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **RCX-Q1** | Is `.greptile/files.json` the manifest SSOT? | **proposed** | Yes — RCX-D1/D2; generate Bugbot header from it |
| **RCX-Q2** | Can hosted Bugbot read engineering context? | **partial** | **Yes** via `BUGBOT.md` + nested files; Team Rules override; 100k cap — slim active block + manifest |
| **RCX-Q3** | RC1 subset per program vs global trim? | **proposed** | Active program only in v1; full corpus via `files.json` scope or nested Greptile |
| **RCX-Q4** | Inject engineering context into Moonshot prompt in v1? | **open** | RCX-G8 — likely RC5 not RCX P0 |
| **RCX-Q5** | Merge with RQ-RC-1 or separate program? | **proposed** | RCX = engineering context program; RQ-RC-1 items fold in |

---

## Edge cases

- **Dashboard rules override repo `BUGBOT.md`** — dogfood changes may not affect hosted `revybot` until team settings updated.
- **Frontend program PRs** — `scope: ["backend/**"]` excludes `frontend/**`; RC3 cascading rules needed later.
- **Docs-only PRs** — bots may still fire; active pointer prevents wrong backend contract citations.
- **Conflicting locks** — two programs' findings disagree; need active pointer + human resolution (no auto-merge of locks).

---

## Devil's advocate

- **Manifest may not fix hosted Bugbot** if Cursor ignores repo files — program becomes Greptile-only + local Bugbot improvement.
- **More context can increase noise** — RC1 subset mandatory before adding more docs.
- **Product RC4 duplicates Greptile** for customers — must prove DB policy > vendor files for tenancy/audit.
- **Operator evidence rots** — smoke tables need dates; stale smoke is worse than none (RCX-D3 discipline).

---

## Parking lot

- Auto-generate `BUGBOT.md` from manifest on each program closeout.
- Link validation memo metrics into findings operational layer.
- Eval: shuffled-diff voting for Moonshot (reject v1 — see industry table).
- RC6 `read_planning_doc` agent tool — pairs with SC8.

---

## Experiment / verification

| Pass/fail | Measure |
|-----------|---------|
| **Pass** | On next program PR, hosted `revybot` does not recommend `format.name`-class contradictions |
| **Pass** | Greptile/revybot cite `JC-D*` or P3 lock in at least one relevant thread |
| **Pass** | Single manifest edit updates all wired channels |
| **Fail → RC1** | Reviewer cites wrong shipped program (e.g. judge-input-quality on unrelated PR) |

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

1. **Discuss** — RCX-Q1–Q5, scope of P0 (dogfood manifest vs product inject).
2. `create-general-plan` from this doc.
3. Staging validation — re-run metrics on **latest runs only** after first post-#58 dogfood PR (separate track L).
