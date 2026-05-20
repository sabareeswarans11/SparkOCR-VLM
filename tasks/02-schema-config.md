# 02 — Schema + Config

## Goal
Frozen `OCROutput` pydantic model + `Settings` from env + `PipelineConfig`. These are the contract surfaces; don't change them after this task.

## Outputs
- `src/sparkocr_vlm/schema.py`
- `src/sparkocr_vlm/config.py`

## `schema.py`
Define `OCROutput`:
```python
class OCROutput(BaseModel):
    markdown: str
    doc_type: Literal["invoice","report","scan","form","other","unknown"] = "unknown"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    model: str = ""
    error: str | None = None
```

Also export the Spark schema:
```python
OCR_OUTPUT_SPARK_SCHEMA = StructType([...])
```

## `config.py`
```python
class Settings(BaseSettings):
    openrouter_api_key: SecretStr | None = None
    together_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None
    modal_token_id: SecretStr | None = None
    modal_token_secret: SecretStr | None = None
    log_costs: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
```

`PipelineConfig` is a frozen pydantic model with all `OCRPipeline.__init__` args.

## DoD
- `from sparkocr_vlm.schema import OCROutput` works.
- `Settings()` reads `.env` without crashing on missing keys.
