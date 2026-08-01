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

# The prod overlay puts the container on nginx's proxy_net. Every compose call
# below needs the same -f set, or it addresses a different project.
COMPOSE=(docker compose -f docker-compose.yml)
if [ -f docker-compose.prod.yml ]; then
    COMPOSE+=(-f docker-compose.prod.yml)
    log "Using docker-compose.prod.yml overlay"
fi

log "Building and recreating containers"
# No `docker compose down` first: compose swaps the container in place, so the
# outage is the few seconds gunicorn needs to boot rather than the whole build.
# You only need `down` when networks or volumes change shape.
"${COMPOSE[@]}" up -d --build --remove-orphans

# nginx resolves a named upstream once at startup and caches the IP for the
# life of the worker, so a recreated container is unreachable until it re-reads
# its config -- a 502 with "Host is unreachable" on the old address.
if docker ps --format '{{.Names}}' | grep -qx infra_nginx; then
    if docker exec infra_nginx nginx -s reload 2>/dev/null; then
        log "Reloaded infra_nginx so it re-resolves the upstream"
    else
        log "WARNING: could not reload infra_nginx; a stale upstream IP may 502"
    fi
fi

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
    "${COMPOSE[@]}" ps
    log "Networks the container joined (must include proxy_net):"
    docker inspect darood-collection \
        --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' || true
    log "Last 60 log lines:"
    "${COMPOSE[@]}" logs --tail 60 --no-color
    log "Last 10 nginx errors:"
    docker logs --tail 10 infra_nginx 2>&1 | tail -10 || true
    exit 1
fi

log "Healthy (HTTP $code)"

log "Removing dangling images left by the rebuild"
docker image prune -f >/dev/null

log "Deployed $(git rev-parse --short HEAD) successfully"
