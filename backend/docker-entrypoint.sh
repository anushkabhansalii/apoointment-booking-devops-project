#!/bin/sh
# Bring the schema up to date, then hand PID 1 over to the API server.
set -eu

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

exec "$@"
