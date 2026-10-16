#!/bin/sh
# Bring the schema up to date, then hand PID 1 over to the API server.
set -eu

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  python -m app.wait_for_db
  echo "Running database migrations..."
  alembic upgrade head
fi

exec "$@"
