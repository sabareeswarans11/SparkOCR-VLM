#!/usr/bin/env bash
# Push the demo notebook to a Databricks Free Edition workspace.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${DATABRICKS_HOST:?set DATABRICKS_HOST in .env or environment}"
: "${DATABRICKS_TOKEN:?set DATABRICKS_TOKEN in .env or environment}"

if ! command -v databricks >/dev/null 2>&1; then
  echo "Install the Databricks CLI: brew tap databricks/tap && brew install databricks"
  exit 1
fi

USER_EMAIL="${DATABRICKS_USER:-$(databricks current-user me --output json | jq -r .userName)}"
TARGET="${1:-/Users/${USER_EMAIL}/sparkocr_free_demo}"

databricks workspace import "$TARGET" \
  --file notebooks/02_databricks_free.ipynb \
  --format JUPYTER \
  --overwrite

echo "✅ Imported: $TARGET"
echo "Open it in your workspace and run."
