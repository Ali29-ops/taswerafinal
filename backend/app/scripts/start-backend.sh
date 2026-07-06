#!/bin/sh
set -eu

echo "Waiting for database migrations..."

attempt=1
while [ "$attempt" -le 20 ]; do
  if alembic upgrade head; then
    break
  fi
  echo "Migration attempt $attempt failed; retrying in 3 seconds..."
  attempt=$((attempt + 1))
  sleep 3
done

if [ "$attempt" -gt 20 ]; then
  echo "Migrations failed after 20 attempts."
  exit 1
fi

echo "Seeding default data..."
python scripts/seed.py

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
