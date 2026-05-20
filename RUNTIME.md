# RUNTIME.md — Files Claude Code Writes During a Session

> While Claude Code works inside PyCharm, it keeps state in `runtime/`. These files are commit-friendly markdown — readable both by humans and by future Claude sessions. The `doc-scribe` subagent owns updates.

## Files

### `runtime/PROGRESS.md`
Current task + percentage. Updated whenever a task starts or finishes.

```md
# PROGRESS

- Last updated: 2026-05-19T15:01:22Z
- Current task: tasks/08-processor-udf.md
- Status: in_progress (60%)

## Done
- 01-scaffold
- 02-schema-config
- 03-page-extractor
- 04-backends-base
- 05-backend-openrouter
- 06-backend-together
- 07-backend-gemini

## In flight
- 08-processor-udf  (spark-udf-engineer)
- 11-tests-harness  (test-harness-engineer)

## Up next
- 09-pipeline
- 10-evaluator
```

### `runtime/DECISIONS.md`
ADR-lite. Append-only. One block per decision.

```md
## 2026-05-19 — UDF: pandas_udf over mapInPandas
**Context:** Need to call the OpenRouter API once per page.
**Decision:** Use `pandas_udf` for now. Switch to `mapInPandas` if we add a rate-limited backend that needs whole-batch sleeping.
**Trade-off:** `pandas_udf` is per-row in spirit; we lose easy cross-row sleeps.
**Author:** spark-udf-engineer
```

### `runtime/ERRORS.md`
Anything that failed and how it got resolved. Useful for future sessions that hit the same wall.

```md
## 2026-05-19T14:33Z — `JAVA_HOME` not set, Spark init failed
- Symptom: `Cannot find Java executable`.
- Root cause: PyCharm's interpreter env didn't inherit `~/.zshrc`.
- Fix: Added `JAVA_HOME` to the Run Configuration's environment variables.
- Owner: spark-udf-engineer
```

### `runtime/COSTS.md`
Running tally of API spend during development. Updated by every backend call (in dev mode only; production runs log to MLflow instead).

```md
# COSTS

Total dev spend so far: $0.0421

| Date (UTC)        | Model                              | Pages | Cost     |
|-------------------|------------------------------------|-------|----------|
| 2026-05-19T13:01Z | deepseek-ai/DeepSeek-OCR-v2:free   | 12    | $0.0000  |
| 2026-05-19T13:14Z | qwen/qwen3-vl-instruct             | 5     | $0.0089  |
| 2026-05-19T14:02Z | deepseek-ai/DeepSeek-OCR-v2        | 20    | $0.0332  |
```

### `runtime/BENCH.md`
Output of the last `python -m tests.harness.perf` run.

```md
# BENCH — 2026-05-19T15:00Z

Backend:  mock
Pages:    20
Wall:     4.12s
PPS:      4.85 pages/sec
Mean lat: 0.206s/page
Cost:     $0.000

## Notes
- Mock backend used; numbers are upper-bound for Spark plumbing.
- Real-backend numbers belong in MLflow, not here.
```

## When to update each file

| File | Trigger |
|---|---|
| `PROGRESS.md` | Task starts, task ends, parallel batch dispatched. |
| `DECISIONS.md` | Any non-obvious choice. Future-you needs to know why. |
| `ERRORS.md` | A real error happens. Don't log expected exceptions. |
| `COSTS.md` | Backend call in dev mode (controlled by `SPARKOCR_LOG_COSTS=1`). |
| `BENCH.md` | Perf harness runs. |

## How subagents write to runtime/

Each subagent has a one-liner in its prompt: *"After finishing, ask doc-scribe to update runtime/."* `doc-scribe` is cheap to spawn and serializes updates so we don't get merge conflicts in markdown.

Manually, you can also append directly — the schema is loose enough that any orderly markdown will do.

## Should these files be committed?

Yes — they're part of the project's living memory. They DO get gitignored if `SPARKOCR_PRIVATE_RUNTIME=1` is set (for users who don't want their cost numbers in git history).

In this repo's default `.gitignore`, `runtime/` is committed. Override locally if needed.
