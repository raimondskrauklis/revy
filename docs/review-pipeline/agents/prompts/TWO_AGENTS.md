# Two agents, same brain — implement vs review

**Index:** [prompts/README.md](./README.md)

We use the same model family (Composer 2.5) for **shipping** and **reviewing**. That is a feature, not a contradiction — the **task** changes what “good reasoning” looks like.

---

## Implementer (parent / phase-execution)

| | |
|-|-|
| **Goal** | Make RQn true in code |
| **Context** | EXECUTION § RQn, findings locks, surrounding files |
| **Optimizes for** | Progress, happy path, deliverable pytest green |
| **Blind spot** | Cross-worker consistency, retry/idempotency, “commit on failed return”, G10 lifecycle edges |
| **Prompt weight** | Medium execution doc + skills (LOOP, ruff, gates) |

The implementer **wrote** the branch. It holds a mental model of intent. Edge cases that only appear when **another worker** or **second Celery attempt** runs are easy to miss — not stupidity, **task framing**.

---

## Reviewer (Bugbot subagent)

| | |
|-|-|
| **Goal** | Break the diff against the contract |
| **Context** | Diff + BUGBOT.md + EXECUTION § RQn + FINDINGS + read/grep callers |
| **Optimizes for** | Failure modes, invariants, “what if retry / None / empty set” |
| **Blind spot** | Over-reporting pre-existing issues; drowning in hypotheses |
| **Prompt weight** | **Thin** — smart + contract; see [PHASES.md](./PHASES.md) + [OUTPUT_FORMAT.md](./OUTPUT_FORMAT.md) |

The reviewer **did not write** the branch. It adversarially traces paths the implementer already “knows” are fine. That is why [RQ1 iterative Bugbot](../../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#iterative-agent-review--rq1-local-bugbot) found lifecycle bugs Greptile missed on the same slice.

---

## “Talked itself out of most of them”

Long thinking traces (see `chain_of_thoughts/local_bugbot_from_ui_1.txt`) often show:

```text
hypothesis → read code → contradict → new hypothesis → … → conservative final answer
```

That is **healthy** for a reviewer. The failure mode is **output**: only printing the last line (`Bugbot found no bugs`) and hiding:

- pass 1 items verified closed
- plausible issues **deferred** (pre-existing, out of diff scope, parking)

**Fix:** mandatory [OUTPUT_FORMAT.md](./OUTPUT_FORMAT.md) — not more prompt volume.

---

## Focus vs bias (RQ2 lesson)

| Layer | Implementer | Reviewer |
|-------|-------------|----------|
| **Focus** | Build the slice in EXECUTION | Diff + contract Q# |
| **Bias** | Toward shipping | Toward invariant violations |
| **Contract** | FINDINGS + EXECUTION | Same — **steers reviewer, not generic “best practices”** |

Category bias (“check security”) stays light. **Contract focus** is the distill target for customer Revy (RC4 / RQ7).

---

## What we distill into the product (RQ4+)

| Reference behavior | Revy target |
|--------------------|-------------|
| Multi-pass review on same slice | Resolution + re-review (RQ5–RQ6) |
| Read/grep cross-file | Pipeline trace + future trace agents |
| Execution-doc citations | RC0 wiring → customer rules pack |
| “Considered but deferred” audit trail | Pipeline artifacts + operator UI |

External Bugbot/Greptile remain **benchmarks**; [ORCHESTRATION.md](../ORCHESTRATION.md) golden rule stays: **local Bugbot before every push**.
