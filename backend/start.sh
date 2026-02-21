#!/usr/bin/env bash
set -e

echo "Running DB migrations..."
alembic upgrade head

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}