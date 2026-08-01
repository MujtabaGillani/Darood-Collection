# Darood Collection

A web app to **count and collect the daily Darood Shareef** recited by users.
Managers record counts on behalf of users, and everyone can track progress by
**day, week, month or year** with charts. Built with **Django + Django REST
Framework**, a server-rendered **Bootstrap 5** UI and **Chart.js** graphs.

---

## Roles

| Role           | Can do |
|----------------|--------|
| **Simple User** | Log in and view *their own* progress (day / month / year) with charts. |
| **Manager**     | Everything above **+** record darood for any simple user or manager (search → select → enter quantity) and view the collection overview. |
| **Super Admin** | Everything **+** the dashboard: activate/deactivate accounts, change roles, and view collection graphs across all users. |

Key rules:

- **New sign-ups are inactive** — they cannot log in until a Super Admin
  activates them from the dashboard.
- A **Manager**'s user search shows simple users and managers (never super admins).
- A **Super Admin**'s search shows everyone.
- Each darood entry is dated by the person recording it (any date is allowed),
  and the recorder is stored for audit.

---

## Tech stack

- **Backend:** Django 5.1, Django REST Framework
- **Database:** SQLite (default; swap `DATABASES` in `config/settings.py` for Postgres/MySQL)
- **Frontend:** Django templates + Bootstrap 5 + Bootstrap Icons + Chart.js (via CDN)
- **Auth:** Django's session auth with a custom `accounts.User` model (adds `role`)

---

## Getting started

```bash
# 1. Create & activate a virtual environment
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4a. Create your own super admin ...
python manage.py createsuperuser

# 4b. ... OR load demo users + sample darood data (recommended for a first look)
python manage.py seed_demo

# 5. Run the server
python manage.py runserver
```

Open http://127.0.0.1:8000/

### Demo accounts (after `seed_demo`)

All demo passwords are **`darood123`**.

| Username   | Role        | Notes |
|------------|-------------|-------|
| `admin`    | Super Admin | Lands on the dashboard |
| `manager1` | Manager     | Bilal Ahmed |
| `manager2` | Manager     | Fatima Khan |
| `user1`    | Simple User | Usman Ali |
| `user2`    | Simple User | Ayesha Malik |
| `user3`    | Simple User | Hamza Sheikh |
| `pending1` | Simple User | **Inactive** — activate it from the dashboard to demo approval |

---

## How the app is organised

```
config/            Django project settings + root URLconf
accounts/          Custom User (roles), auth, registration, dashboard, user management
darood/            DaroodEntry model, add-entry flow, overview/progress views, chart & search APIs
  services.py        Period filtering + time-series aggregation helpers
  management/commands/seed_demo.py   Demo data loader
templates/         Bootstrap 5 templates (base, auth, dashboard, darood pages)
static/css/app.css UI styling
```

### Main pages

| URL | Who | Purpose |
|-----|-----|---------|
| `/login/`, `/register/`, `/logout/` | Public | Auth |
| `/` | Any logged-in | Redirects to the right landing page for the role |
| `/dashboard/` | Super Admin | User management + collection graphs |
| `/darood/add/` | Manager, Super Admin | Search a user, pick a date, enter quantity |
| `/darood/overview/` | Manager, Super Admin | All users' totals, leaderboard, recent entries (period filter) |
| `/me/` | Any logged-in | The user's own progress + trend chart |
| `/users/<id>/darood/` | Manager, Super Admin | A single user's breakdown + chart |

### JSON APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/users/search/?q=` | Autocomplete for the add-darood search box (role-scoped) |
| `GET /api/chart/?scope=all&granularity=day\|month\|year` | Time-series totals for Chart.js (`scope=mine` or `user=<id>`) |

The Django admin is also available at `/admin/` for a super admin.

---

## Run with Docker

The image runs Django under **Gunicorn**, serves static files with
**WhiteNoise**, and keeps the SQLite database on a named volume so it survives
rebuilds. Migrations run automatically on startup.

```bash
# 1. (optional) create your env file and set a real secret key
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"   # paste into DJANGO_SECRET_KEY

# 2. build and start
docker compose up -d --build

# 3. create a super admin (or set SEED_DEMO=true in .env to load demo data)
docker compose exec web python manage.py createsuperuser
```

Open http://127.0.0.1:8000/  (change the host port with `HOST_PORT` in `.env`).

Useful commands:

```bash
docker compose logs -f web      # tail logs
docker compose exec web sh      # shell inside the container
docker compose down             # stop (data is kept in the volume)
docker compose down -v          # stop and delete the database volume
```

### Configuration (environment variables)

| Variable | Default | Purpose |
|----------|---------|---------|
| `DJANGO_SECRET_KEY` | insecure dev key | **Set a real value in production.** |
| `DJANGO_DEBUG` | `False` (image) / `True` (local) | Debug mode. |
| `DJANGO_ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | — | Comma-separated origins trusted for POST. Include the port if it isn't 80/443; a bare `host:port` covers http and https. |
| `DJANGO_USE_X_FORWARDED_HOST` | `False` | Read the public host from `X-Forwarded-Host`. |
| `DJANGO_USE_X_FORWARDED_PORT` | `False` | Read the public port from `X-Forwarded-Port`. |
| `DJANGO_SECURE_SSL` | `False` | Enable secure cookies + HSTS + SSL redirect (behind TLS). |
| `DJANGO_SQLITE_PATH` | `/app/data/db.sqlite3` | DB file location (kept on the volume). |
| `HOST_PORT` | `8000` | Host port mapped to the container. |
| `SEED_DEMO` | `false` | Load demo users + sample data on first start. |
| `WEB_CONCURRENCY` | `3` | Gunicorn worker processes. |

Behind a reverse proxy that terminates TLS, set `DJANGO_SECURE_SSL=True` and add
your domain to `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`.

**"CSRF verification failed" on login behind a proxy.** `ALLOWED_HOSTS=*` does
not cover this: Django separately checks the browser's `Origin` header against
`CSRF_TRUSTED_ORIGINS`, scheme and port included. Serving on
`http://203.0.113.10:8085` while nginx forwards `Host: 203.0.113.10` to the
container makes the two disagree, so every POST is rejected. Fix it by setting
`DJANGO_CSRF_TRUSTED_ORIGINS=203.0.113.10:8085` (or by having nginx pass
`proxy_set_header Host $http_host;`, which keeps the port intact). The exact
reason is logged to `docker logs` even with `DEBUG=False`.

## CI/CD

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) runs on every push
and pull request:

| Job | What it does | Gates the deploy? |
|-----|--------------|-------------------|
| `test` | `manage.py check`, `makemigrations --check` (fails if a model changed without a migration), `manage.py test` | yes |
| `build` | `docker build` of the real Dockerfile, so a broken build or `collectstatic` failure shows up here | yes |
| `deploy` | SSH to the server, fast-forward to `origin/main`, run [`scripts/deploy.sh`](scripts/deploy.sh) | — |

`deploy` only runs for pushes to `main` that pass both other jobs. Use the
**Run workflow** button (`workflow_dispatch`) to redeploy the current `main`
without pushing. Deploys are serialised — a second push waits rather than
interrupting a build in progress.

### One-time setup

Generate a key pair for the runner to log in with, on the server:

```bash
ssh-keygen -t ed25519 -C 'github-actions-deploy' -f ~/.ssh/gh_deploy -N ''
cat ~/.ssh/gh_deploy.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/gh_deploy          # the private key -> DEPLOY_SSH_KEY secret
ssh-keyscan -H <server-ip>    # -> DEPLOY_KNOWN_HOSTS secret
```

Then add these under **Settings → Secrets and variables → Actions**:

| Secret | Value |
|--------|-------|
| `DEPLOY_SSH_KEY` | Contents of `~/.ssh/gh_deploy` (the private key, including the BEGIN/END lines) |
| `DEPLOY_KNOWN_HOSTS` | Output of `ssh-keyscan -H <server-ip>` — pins the host key so a spoofed server can't collect your key |
| `DEPLOY_HOST` | Server IP or hostname |
| `DEPLOY_USER` | `serveradmin` |
| `DEPLOY_PATH` | `/srv/hosting/apps/Darood-Collection` |
| `DEPLOY_PORT` | Only if SSH isn't on 22 |

The deploy user needs to run `docker` without a password prompt:
`sudo usermod -aG docker serveradmin` (log out and back in to take effect).

### What the deploy does differently from doing it by hand

`scripts/deploy.sh` replaces `docker compose down && docker compose up --build -d`
with a single `docker compose up -d --build`. Same result, but the old container
keeps serving traffic *during* the build instead of the site being down for it —
`down` is only necessary when networks or volumes change shape. The script then
polls the app through nginx until it returns 200 and **fails the workflow** with
`docker compose ps` and the last 60 log lines if it doesn't, so a broken deploy
is visible in GitHub rather than only in your browser. Migrations still run in
[`docker/entrypoint.sh`](docker/entrypoint.sh) on container start.

To roll back, revert the commit on `main` and let the pipeline deploy it, or on
the server: `git reset --hard <good-sha> && bash scripts/deploy.sh`.

## Notes for production

The settings read all of the above from the environment, so no code changes are
needed to deploy. To swap SQLite for Postgres/MySQL, update `DATABASES` in
`config/settings.py` (and add the driver to `requirements.txt`).

The pipeline builds on the production host, which is fine at this size but
competes with the running app for CPU. If that starts to hurt, switch to
building in CI and pushing to GHCR, then have the server `docker compose pull`
a tagged image instead of `--build`.
