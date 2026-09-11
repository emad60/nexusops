#!/bin/sh
# NexusOps container entrypoint.
#
# Applies migrations before the API serves traffic so `docker compose up`
# yields a working stack with zero manual steps. Workers/schedulers wait for
# the api healthcheck in compose, which guarantees migrations are applied.
set -e

if [ "${RUN_MIGRATIONS_ON_START:-true}" = "true" ]; then
    echo "[nexusops] applying database migrations..."
    alembic upgrade head
fi

exec "$@"
