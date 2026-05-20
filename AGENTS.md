# AGENTS.md — Parallel Subagent Workflow

> Claude Code in PyCharm can spawn multiple subagents to work in parallel. This project ships six of them under `.claude/agents/`. This doc explains who does what, when to invoke them, and how they coordinate.

## Why subagents

A monolithic Claude session forgets context as the codebase grows. Subagents are scoped — each one knows exactly one slice of the system and reads only the docs it needs. We use them to parallelize three things:
1. **Build** (backend, UDF, pipeline can be written concurrently).
2. **Test** (harness generation independent of feature code).
3. **Deploy** (Databricks Free notebook polished while local code is still being written).

## The six subagents

| Agent | Owns | Reads | Writes | Runs in parallel with |
|---|---|---|---|---|
| `spark-udf-engineer` | `src/sparkocr_vlm/processor.py`, `pipeline.py`, `utils/spark_helpers.py` | `ARCHITECTURE.md`, `MAC_INTEL_SETUP.md` | Same | `vlm-backend-engineer`, `test-harness-engineer` |
| `vlm-backend-engineer` | `src/sparkocr_vlm/backends/*` | `MODELS.md`, `ARCHITECTURE.md` | Same + `utils/cost.py` | `spark-udf-engineer`, `test-harness-engineer` |
| `test-harness-engineer` | `tests/harness/*`, `tests/conftest.py`, all `test_*.py` | `TESTING.md`, `HARNESS.md` | Same | `spark-udf-engineer`, `vlm-backend-engineer` |
| `databricks-deployer` | `notebooks/02_databricks_free.ipynb`, `scripts/push_databricks.sh` | `DATABRICKS_FREE.md` | Same | All builders |
| `eval-scorer` | `src/sparkocr_vlm/evaluator.py`, `notebooks/03_evaluation.ipynb` | `MODELS.md`, `TESTING.md` | Same + `runtime/BENCH.md` | Last (needs everything else) |
| `doc-scribe` | `runtime/PROGRESS.md`, `DECISIONS.md`, `ERRORS.md`, `COSTS.md`, `BENCH.md` | All | Only `runtime/*` | Always |

## Orchestration pattern

The orchestrator (the main Claude Code session) follows this loop:

```
1. Read tasks/00-overview.md to find the next pending task.
2. Decide which subagent owns it. Multiple tasks → multiple agents in parallel.
3. Invoke them. Each subagent reports back when done.
4. Run the harness (test-harness-engineer's domain). All green?
5. Ask doc-scribe to update runtime/PROGRESS.md and runtime/DECISIONS.md.
6. Loop.
```

In PyCharm, this is just:
```
/agent spark-udf-engineer "Implement the pandas_udf wrapper per tasks/08-processor-udf.md"
/agent vlm-backend-engineer "Implement OpenRouter backend per tasks/05-backend-openrouter.md"
```

Both run in parallel.

## Coordination contract

Subagents NEVER edit files outside their owned set. If they need a change in another agent's file, they leave a note in `runtime/DECISIONS.md` under `## Cross-Agent Requests` and the orchestrator dispatches it.

The shared contract surfaces are:
1. `src/sparkocr_vlm/schema.py` — `OCROutput` pydantic model. Frozen once written.
2. `src/sparkocr_vlm/backends/base.py` — `VLMBackend` ABC. Frozen once written.
3. `tests/harness/golden.py` — golden assertion helpers. Test-harness owns the API; others consume it.

If any of these need to change, **the orchestrator** edits them, not a subagent.

## Parallel example

Imagine we're on tasks 5 and 8:

```
parallel-block:
  - subagent: vlm-backend-engineer
    task:     tasks/05-backend-openrouter.md
  - subagent: spark-udf-engineer
    task:     tasks/08-processor-udf.md
  - subagent: test-harness-engineer
    task:     tasks/11-tests-harness.md (write fixtures + harness only — feature tests come later)
```

All three can proceed because they own disjoint files and depend only on already-frozen `schema.py` and `base.py`.

## Failure mode: agent collides with itself

If a subagent reports "I need to change `processor.py`" while it doesn't own it, the orchestrator should:
1. Stop the offending agent.
2. Read its proposed diff.
3. Apply or reject the diff itself.
4. Resume the agent with a fresh prompt that does NOT require the cross-file edit.

## When NOT to use subagents

- Trivial doc edits (under ~30 lines) — do them inline.
- Anything that touches schema.py or base.py — orchestrator only.
- Final polish passes — single coherent voice is better.

## See also

- `.claude/agents/*.md` — the actual prompt for each subagent.
- `HARNESS.md` — the harness contract that all builders write against.
- `RUNTIME.md` — where subagents report state.
