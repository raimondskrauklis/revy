# Judge thinking-blocks — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [JUDGE_THINKING_BLOCKS_FINDINGS.md](./JUDGE_THINKING_BLOCKS_FINDINGS.md)

**Status:** *pending* — P0–P2 code on `feat/judge-parse` ([#103](https://github.com/raimondskrauklis/revy/pull/103)); fill after those commits are on the staging worker.

---

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| Baseline (pre-extract) | `2026-08-07T00:00:00Z` | 62.4% persistence; 53 thinking-first misses (45 text-later / 8 thinking-only) |
| *(post-deploy)* | TBD | fill after next `main` deploy of P0–P2 |

**Rule:** Use deploy job completion time, not merge time. See [staging-validation README](../staging-validation/README.md).

---

## Pass criteria

| Check | Pass | Fail |
|-------|------|------|
| Candidate → `outcome` | ≥95% **or** residual classified (thinking-only / `judge_json_invalid` / other) | Persistence stuck ~62% with thinking-first `Anthropic response invalid` |
| Extract-only ceiling (7 Aug window) | **94.3%** (D9) is **not** a hard fail | Treating 94.3% as fail and reopening JSON-contract |
| Split evidence | text-later vs thinking-only printed separately | Blended miss % only |
| Codes | `judge_empty_text` vs live `judge_json_invalid` vs HTTP | Empty-text lumped as `Anthropic response invalid` |
| JTB-Q5 | thinking-only recover rate after one retry recorded | Adding retries/second model from this memo |

---

## Metrics

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics --since 2026-08-07T00:00:00Z
```

Printer includes **Thinking-block split** (`text_later` / `thinking_only` / `invalid_json` / `transport` / `other`).

---

## Results (operator)

| Metric | Baseline (2026-08-21) | After P0–P2 deploy | Date |
|--------|----------------------|--------------------|------|
| Outcome persistence | **62.4%** (88/141) | pending | — |
| `parse_error` breakdown | 53 × `Anthropic response invalid` | pending (`judge_empty_text` / `judge_json_invalid` / HTTP) | — |
| text-later vs thinking-only | 45 / 8 | pending | — |
| `retry_count` > 0 | 0 | pending (JTB-Q5) | — |
| D9 ceiling noted | 94.3% | — | — |

---

## Sign-off

| Check | Status | Evidence |
|-------|--------|----------|
| Staging PASS (≥95% **or** classified residual) | pending | — |
| Do not reopen JSON-contract for 0.7pt | locked (D7/D9) | findings |

**Next:** deploy P0–P2 to staging worker → re-run metrics → fill results + JTB-Q5.
