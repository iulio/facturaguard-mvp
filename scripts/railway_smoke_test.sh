#!/usr/bin/env sh
set -eu

if [ "$#" -lt 1 ]; then
  echo "Usage: sh scripts/railway_smoke_test.sh <backend-url> [frontend-url] [--include-auth-flow]"
  exit 1
fi

BACKEND_URL="$1"
FRONTEND_URL="${2:-}"
EXTRA="${3:-}"

if [ -n "$FRONTEND_URL" ]; then
  python scripts/railway_smoke_test.py --backend "$BACKEND_URL" --frontend "$FRONTEND_URL" $EXTRA
else
  python scripts/railway_smoke_test.py --backend "$BACKEND_URL" $EXTRA
fi
