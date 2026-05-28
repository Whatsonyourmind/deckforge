#!/usr/bin/env bash
# DeckForge Render container entrypoint.
#
# Runs database migrations BEFORE the web server accepts traffic so a missing
# table (e.g. api_keys / usage_records) can never surface as a runtime 500.
#
# Idempotent: `alembic upgrade head` is a no-op when already at head.
# Fail-loud-but-continue: if migrations error (e.g. transient DB blip while the
# schema is already current) we log loudly and still start the server rather
# than crash-loop forever. A genuinely missing schema would then surface as a
# clean 401 from the fail-closed auth path instead of an opaque 500.
set -uo pipefail

echo "[entrypoint] Running database migrations (alembic upgrade head)..."
if alembic upgrade head; then
    echo "[entrypoint] Migrations applied (or already at head)."
else
    echo "[entrypoint] WARNING: 'alembic upgrade head' failed (exit $?)." >&2
    echo "[entrypoint] Starting server anyway; check DECKFORGE_DATABASE_URL and migration logs." >&2
fi

echo "[entrypoint] Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn deckforge.main:app --host 0.0.0.0 --port "${PORT:-8000}"
