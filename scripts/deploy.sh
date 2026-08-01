#!/usr/bin/env bash
#
# Rebuild the image and restart the container, then prove the app answers
# before declaring success. Called by .github/workflows/ci-cd.yml after the
# server has already fetched the new code; safe to run by hand too:
#
#   cd /srv/hosting/apps/Darood-Collection && bash scripts/deploy.sh
#
# Database migrations are not run here -- docker/entrypoint.sh applies them
# every time the container starts.
set -euo pipefail

# Reached through infra_nginx, so a 200 here proves the whole
# nginx -> gunicorn -> Django path works, not just that a process is up.
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8085/login/}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-90}"

cd "$(dirname "$0")/.."

log() { printf '==> %s\n' "$*"; }

log "Building and recreating containers"
# No `docker compose down` first: compose swaps the container in place, so the
# outage is the few seconds gunicorn needs to boot rather than the whole build.
# You only need `down` when networks or volumes change shape.
docker compose up -d --build --remove-orphans

log "Waiting up to ${HEALTH_TIMEOUT}s for $HEALTH_URL"
code=000
deadline=$((SECONDS + HEALTH_TIMEOUT))
while [ "$SECONDS" -lt "$deadline" ]; do
    code="$(curl -sS -o /dev/null -w '%{http_code}' "$HEALTH_URL" 2>/dev/null || echo 000)"
    [ "$code" = "200" ] && break
    sleep 3
done

if [ "$code" != "200" ]; then
    log "DEPLOY FAILED: last response was HTTP $code"
    log "Container status:"
    docker compose ps
    log "Last 60 log lines:"
    docker compose logs --tail 60 --no-color
    exit 1
fi

log "Healthy (HTTP $code)"

log "Removing dangling images left by the rebuild"
docker image prune -f >/dev/null

log "Deployed $(git rev-parse --short HEAD) successfully"
