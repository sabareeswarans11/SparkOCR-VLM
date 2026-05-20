#!/usr/bin/env bash
# Local pipeline smoke test using mock backend.
set -euo pipefail
cd "$(dirname "$0")/.."

uv run python - << 'PY'
from pathlib import Path
from sparkocr_vlm import OCRPipeline
from sparkocr_vlm.utils.spark_helpers import build_local_spark
from tests.harness.synthetic_pdf import SyntheticPDFBuilder
from tests.harness.golden import install_mock_table_from_fixtures

FIX = Path("tests/fixtures")
SyntheticPDFBuilder(out_dir=FIX).build_all()
install_mock_table_from_fixtures(FIX)

spark = build_local_spark(cores="2", memory="2g")
pipeline = OCRPipeline(
    backend="mock", model="mock-model",
    input_path=str(FIX), output_path="./_out_smoke",
)
df = pipeline.run(spark)
print(df.toPandas().to_string())
spark.stop()
PY

echo "✅ smoke ok"
