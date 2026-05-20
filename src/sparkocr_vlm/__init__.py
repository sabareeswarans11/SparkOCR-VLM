"""SparkOCR-VLM — distributed VLM-based OCR on PySpark."""

from sparkocr_vlm.pipeline import BudgetExceeded, OCRPipeline
from sparkocr_vlm.schema import OCROutput, PipelineConfig

__version__ = "0.1.0"
__all__ = ["OCRPipeline", "OCROutput", "PipelineConfig", "BudgetExceeded", "__version__"]
