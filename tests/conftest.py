"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


FIXTURES = Path(__file__).parent / "fixtures"
FIXTURES.mkdir(exist_ok=True)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: requires real API keys; skipped by default")
    config.addinivalue_line("markers", "slow: takes > 10s")
    config.addinivalue_line("markers", "databricks: requires databricks workspace")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip integration tests unless explicitly selected."""
    selected = config.getoption("-m") or ""
    if "integration" in selected:
        return
    skip_int = pytest.mark.skip(reason="needs -m integration")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_int)


@pytest.fixture(scope="session", autouse=True)
def _generate_synthetic_pdfs():
    """Generate synthetic PDFs once per test session."""
    from tests.harness.synthetic_pdf import SyntheticPDFBuilder
    SyntheticPDFBuilder(out_dir=FIXTURES).build_all()
    yield


@pytest.fixture(scope="session", autouse=True)
def _install_mock_table(_generate_synthetic_pdfs):
    """Wire synthetic PDFs to their golden markdown via the mock backend."""
    from tests.harness.golden import install_mock_table_from_fixtures
    install_mock_table_from_fixtures(FIXTURES)
    yield


@pytest.fixture(scope="session")
def spark():
    """Local SparkSession sized for a 16GB Intel MBP test run."""
    from sparkocr_vlm.utils.spark_helpers import build_local_spark
    s = build_local_spark(cores="2", memory="2g")
    s.sparkContext.setLogLevel("WARN")
    yield s
    s.stop()


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def synth_invoice_bytes() -> bytes:
    return (FIXTURES / "synth_invoice.pdf").read_bytes()


@pytest.fixture
def synth_report_bytes() -> bytes:
    return (FIXTURES / "synth_report.pdf").read_bytes()


@pytest.fixture
def synth_table_bytes() -> bytes:
    return (FIXTURES / "synth_table.pdf").read_bytes()


@pytest.fixture
def mock_pipeline():
    from sparkocr_vlm import OCRPipeline
    return OCRPipeline(backend="mock", model="mock-model")
