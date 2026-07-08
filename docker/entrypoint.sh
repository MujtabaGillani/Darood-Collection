#!/bin/sh
# Container startup: prepare the database, then run the app server.
set -e

echo "==> Applying database migrations"
python manage.py migrate --noinput

# Optionally load demo users + sample data on first run (SEED_DEMO=true).
if [ "${SEED_DEMO:-false}" = "true" ]; then
    echo "==> Seeding demo data"
    python manage.py seed_demo || echo "   (seed_demo skipped or already applied)"
fi

echo "==> Starting Gunicorn on port ${PORT:-8000}"
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-3}" \
    --timeout "${WEB_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
