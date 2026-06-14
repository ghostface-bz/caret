#!/bin/sh
# Shared entrypoint for the `backend` and `worker` services.
# Applies Alembic migrations (idempotent) before running the given command.
set -e

echo "Running Alembic migrations..."
alembic upgrade head || echo "WARNING: alembic upgrade failed (continuing; app falls back to create_all)"

exec "$@"
