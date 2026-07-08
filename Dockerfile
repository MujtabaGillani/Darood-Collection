# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Darood Collection — production image
# Django 5.1 + Gunicorn, static served by WhiteNoise, SQLite on a volume.
# ---------------------------------------------------------------------------
FROM python:3.12-slim

# Container-friendly Python defaults.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# ---- Python dependencies (own layer so code changes don't re-install) ------
COPY requirements.txt ./
RUN pip install -r requirements.txt

# ---- Application code -------------------------------------------------------
COPY . .

# Collect + hash static files into STATIC_ROOT, baked into the image.
# DEBUG must be off here so the manifest storage is used.
RUN DJANGO_DEBUG=False python manage.py collectstatic --noinput

# ---- Non-root runtime user + writable data dir for the SQLite DB -----------
RUN useradd --uid 1000 --create-home appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

ENV DJANGO_DEBUG=False \
    DJANGO_SQLITE_PATH=/app/data/db.sqlite3 \
    PORT=8000

EXPOSE 8000

# Runs migrations (and optional seeding) then starts Gunicorn.
ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
