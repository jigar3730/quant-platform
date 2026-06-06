#!/usr/bin/env bash
# Create github.com/jigar3730/quant-platform and push main.
# Prerequisite: gh auth login

set -euo pipefail
cd "$(dirname "$0")/.."

if ! gh auth status >/dev/null 2>&1; then
  echo "Not logged in. Run: gh auth login"
  echo "  - GitHub.com"
  echo "  - HTTPS"
  echo "  - Login with a web browser"
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote 'origin' already exists:"
  git remote -v
  git push -u origin main
else
  gh repo create quant-platform \
    --public \
    --source=. \
    --remote=origin \
    --description "Quantitative breakout stock scanner with Streamlit dashboard" \
    --push
fi

echo ""
echo "Done: https://github.com/jigar3730/quant-platform"
