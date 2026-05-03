#!/usr/bin/env sh
set -eu

echo "[railway] Running Alembic migrations..."
alembic upgrade head

echo "[railway] Running deployment sanity checks..."
python scripts/railway_predeploy_check.py

echo "[railway] Pre-deploy checks passed."
