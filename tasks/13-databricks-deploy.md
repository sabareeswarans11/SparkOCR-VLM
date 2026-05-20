# 13 — Databricks Free Deploy

## Outputs
- `scripts/push_databricks.sh`
- Final touches on `notebooks/02_databricks_free.ipynb`.

## push_databricks.sh
```bash
#!/usr/bin/env bash
set -euo pipefail
: "${DATABRICKS_HOST:?set DATABRICKS_HOST}"
: "${DATABRICKS_TOKEN:?set DATABRICKS_TOKEN}"
TARGET="${1:-/Users/$(databricks current-user me --output json | jq -r .userName)/sparkocr_free_demo}"
databricks workspace import "$TARGET" --file notebooks/02_databricks_free.ipynb --format JUPYTER --overwrite
echo "Imported to: $TARGET"
```

## DoD
- Running the script with a Free Edition token imports the notebook into the workspace.
- The notebook runs top-to-bottom on Free Edition.
