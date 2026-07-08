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

## Notes for production

This project ships with development defaults. Before deploying: set
`DEBUG=False`, move `SECRET_KEY` to an environment variable, set
`ALLOWED_HOSTS`, switch to a production database, run `collectstatic`, and serve
behind a WSGI server (gunicorn/uwsgi) + reverse proxy.
