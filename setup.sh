#!/usr/bin/env bash
# Bootstrap script: copy this tree to ~/Projects_26/SparkOCR-VLM, init git, wire remote.
# Run from inside the unpacked sparkocr-vlm/ directory.

set -euo pipefail

DEST="${1:-$HOME/Projects_26/SparkOCR-VLM}"
REMOTE="${REMOTE:-https://github.com/sabareeswarans11/SparkOCR-VLM.git}"

SRC="$(cd "$(dirname "$0")" && pwd)"
echo "Source: $SRC"
echo "Dest:   $DEST"
echo "Remote: $REMOTE"
echo

if [[ -d "$DEST" ]]; then
  echo "Destination exists. Backing up to ${DEST}.bak.$(date +%s)"
  mv "$DEST" "${DEST}.bak.$(date +%s)"
fi

mkdir -p "$(dirname "$DEST")"
cp -R "$SRC" "$DEST"
chmod +x "$DEST"/scripts/*.sh "$DEST"/setup.sh || true

cd "$DEST"

if [[ ! -d .git ]]; then
  git init -b main
fi

git add -A
git -c user.email="sabareeswarans11@gmail.com" -c user.name="Sab" \
    commit -m "Initial scaffold: SparkOCR-VLM" || true

if git remote | grep -q '^origin$'; then
  git remote set-url origin "$REMOTE"
else
  git remote add origin "$REMOTE"
fi

cat <<EOF

✅ Project laid down at: $DEST
✅ Git initialised with remote: $REMOTE

Next steps:
  1. cd "$DEST"
  2. bash scripts/setup_local.sh        # uv sync + tests
  3. cp .env.template .env              # then add OPENROUTER_API_KEY
  4. git push -u origin main            # pushes to GitHub (run yourself)
  5. Open the folder in PyCharm and start Claude Code.

EOF
