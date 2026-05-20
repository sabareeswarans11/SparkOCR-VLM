#!/usr/bin/env bash
# One-time local setup on Intel Mac.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install with: brew install uv"
  exit 1
fi

if [[ -z "${JAVA_HOME:-}" ]]; then
  if command -v brew >/dev/null && [[ -d "$(brew --prefix openjdk@17 2>/dev/null || true)" ]]; then
    export JAVA_HOME="$(brew --prefix openjdk@17)/libexec/openjdk.jdk/Contents/Home"
    echo "Using JAVA_HOME=$JAVA_HOME"
  else
    echo "WARNING: JAVA_HOME not set and openjdk@17 not found via brew."
    echo "Install: brew install openjdk@17"
  fi
fi

uv sync --extra dev

if [[ ! -f .env ]]; then
  cp .env.template .env
  echo "Created .env from template — edit it before running real backends."
fi

echo
echo "Generating synthetic fixtures..."
uv run python -m tests.harness.synthetic_pdf --out tests/fixtures

echo
echo "Running unit tests..."
uv run pytest tests/ -m "not integration" -q

echo
echo "✅ Setup complete."
echo "Open in PyCharm: $(pwd)"
