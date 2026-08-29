#!/usr/bin/env sh
set -e

echo "Running database migrations via Alembic..."
python -m alembic upgrade head

echo "Running MatchIQ bootstrap sequence..."
python scripts/bootstrap.py

echo "Starting MatchIQ Uvicorn API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
