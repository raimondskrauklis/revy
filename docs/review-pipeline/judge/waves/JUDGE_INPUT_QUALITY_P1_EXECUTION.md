# Judge input quality P1 — Verifier prompt contract (execution)

Phase **P1** of [JUDGE_INPUT_QUALITY_GENERAL_PLAN.md](../JUDGE_INPUT_QUALITY_GENERAL_PLAN.md). Baseline: [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](../JUDGE_INPUT_INVESTIGATION_FINDINGS.md) J-5, J-7, J-10. **P1 only.**

**Goal:** Judge LLM contract = Moonshot **verifier** — one claim only; no full PR review; conservative outcomes when evidence thin.

**Note:** Verifier `JUDGE_SYSTEM_PROMPT`, Moonshot header, and framing unit tests are **already in working tree** — P1 may be a thin commit (verify + J-10 doc) unless prompts need re-touch.

## Decisions locked for P1

- `JUDGE_SYSTEM_PROMPT` in `anthropic_review.py` — verification judge, Moonshot-named, forbids scope creep.
- `_build_judge_prompt` header: “Automated reviewer (Moonshot)… Verify this claim only.”
- E2 grounding strings (`_GROUNDING_WITH_EVIDENCE` / `_GROUNDING_WITHOUT_EVIDENCE`) unchanged unless wording conflicts — then align with verifier tone only.
- **J-10 v1 locked:** `modified` application stays `group.severity = FindingSeverity.warning` — document in findings gap table; no code change to outcome handler.
- Bedrock judge imports `JUDGE_SYSTEM_PROMPT` — no forked string.
- No file patch in prompt — **P3**.

## Out of scope for P1

- Evidence/hunk primitives → **P0** (may land same PR if LOOP merges P0+P1)
- `modified` severity logic expansion → deferred past J-10 v1
- Gateway client → already on gateway branch

---

## P1.1 — Verifier system prompt

**What:** Ship `JUDGE_SYSTEM_PROMPT` verifier contract in `anthropic_review.py` (working-tree draft is authoritative).

**Files:** `backend/app/integrations/anthropic_review.py`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/integrations/anthropic_review.py
```

---

## P1.2 — Verifier user-prompt header

**What:** Ship Moonshot verifier header lines at top of `_build_judge_prompt`; retain line/suggestion/E2 blocks.

**Files:** `backend/app/services/github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/services/github_finding_judge.py
```

---

## P1.3 — J-10 documentation lock

**What:** Update findings J-10 row: v1 = `modified` → `warning` only; execution defers message/severity-specific downgrades. Update general plan cross-ref if needed.

**Files:** `docs/review-pipeline/judge/JUDGE_INPUT_INVESTIGATION_FINDINGS.md`

**Deliverable:** J-10 status = **Locked v1** in findings gap table.

---

## P1.4 — Unit tests (verifier framing)

**What:** Assert `Automated reviewer (Moonshot)`, `Verify this claim only`, `Do not introduce new findings` in built user prompt; assert `verification judge` + `Moonshot` + `full PR review` in `JUDGE_SYSTEM_PROMPT`.

**Files:** `backend/tests/unit/test_github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "judge_prompt or judge_system" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_judge.py -q
pipenv run ruff check app/integrations/anthropic_review.py app/services/github_finding_judge.py
```

**Next:** [JUDGE_INPUT_QUALITY_P2_EXECUTION.md](./JUDGE_INPUT_QUALITY_P2_EXECUTION.md)
