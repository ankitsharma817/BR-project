#!/usr/bin/env bash
# Run database migrations then start the API server
set -e
export PYTHONPATH="$(pwd)"

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting API server..."
uvicorn api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --log-level info
