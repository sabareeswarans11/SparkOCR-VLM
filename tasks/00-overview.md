# 00-overview.md — Build Order Index

Read `CLAUDE.md` first. Then work through these in order. Tasks marked `[parallel-ok]` can be dispatched to subagents simultaneously.

| # | Task | Owner | Parallel? | Status |
|---|---|---|---|---|
| 01 | `01-scaffold.md` — pyproject, dirs, empty modules | orchestrator | no | pending |
| 02 | `02-schema-config.md` — `OCROutput`, `PipelineConfig`, settings | orchestrator | no | pending |
| 03 | `03-page-extractor.md` — PDF → PNG via pymupdf | spark-udf-engineer | [parallel-ok with 04] | pending |
| 04 | `04-backends-base.md` — `VLMBackend` ABC + Mock | vlm-backend-engineer | [parallel-ok with 03] | pending |
| 05 | `05-backend-openrouter.md` — DeepSeek + Qwen via OpenRouter | vlm-backend-engineer | [parallel-ok with 06,07] | pending |
| 06 | `06-backend-together.md` — Together.ai alt | vlm-backend-engineer | [parallel-ok with 05,07] | pending |
| 07 | `07-backend-gemini.md` — Gemini alt | vlm-backend-engineer | [parallel-ok with 05,06] | pending |
| 08 | `08-processor-udf.md` — pandas_udf wrapping backend | spark-udf-engineer | no | pending |
| 09 | `09-pipeline.md` — `OCRPipeline` orchestrator | spark-udf-engineer | no | pending |
| 10 | `10-evaluator.md` — edit-distance + golden scorer | eval-scorer | [parallel-ok with 11] | pending |
| 11 | `11-tests-harness.md` — fixtures, harness, all tests | test-harness-engineer | [parallel-ok with 10] | pending |
| 12 | `12-notebooks.md` — 3 notebooks | orchestrator | no | pending |
| 13 | `13-databricks-deploy.md` — Free Edition demo | databricks-deployer | no | pending |
| 14 | `14-readme-demo.md` — README polish + demo gif | doc-scribe | no | pending |

## Definition of Done (per task)

A task is done when:
1. All files listed in its `Outputs` section exist.
2. `pytest tests/ -m "not integration"` passes.
3. `runtime/PROGRESS.md` is updated by `doc-scribe`.
4. The harness perf still completes: `python -m tests.harness.perf --backend mock`.

## How to use these with subagents

```
/agent vlm-backend-engineer "Execute tasks/05-backend-openrouter.md from start to finish. Stop and report when done."
```

For parallel tasks, dispatch multiple agents in the same turn. See `AGENTS.md`.
