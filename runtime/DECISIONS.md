# DECISIONS

ADR-lite log. Append-only. One block per decision.

## 2026-05-19 — Default backend = OpenRouter free tier
**Context:** User has only Databricks Free Edition and an Intel Mac. Needs free-tier access to both DeepSeek-OCR-v2 and Qwen3-VL.
**Decision:** Default `OCRPipeline(backend="openrouter")`. Together.ai and Gemini are alternates.
**Trade-off:** OpenRouter free tier is rate-limited; production users will likely switch to paid OpenRouter or Together.
**Author:** orchestrator
