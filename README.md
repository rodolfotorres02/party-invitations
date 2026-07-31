# party-invitations

A small Django app for creating shareable party-invitation links and
collecting RSVPs. The organizer creates a link labeled with a recipient
(e.g. "The Smiths") and a guest count, then copies the link to share
however they like (SMS, email, paper). The recipient opens the link and
RSVPs yes/no/maybe.

## Architecture

```
invitations/
├── models.py              # ORM definitions (Party, Invitation, RSVP)
├── repositories/          # Pure data access — only place ORM queries live
│   ├── party_repository.py
│   ├── invitation_repository.py
│   └── rsvp_repository.py
├── services/              # Business logic — orchestrates repositories, no ORM
│   ├── party_service.py
│   ├── invitation_service.py
│   └── rsvp_service.py
├── views.py               # Thin controllers — parse request, call service, render
├── forms.py
├── urls.py
└── templates/invitations/
```

**Rules of the road:**
- Views never touch the ORM. They call services.
- Services never touch the ORM. They call repositories.
- Repositories are the only layer that imports `Model.objects`.
- All imports are at module top — no function-level imports anywhere.

## Setup — Docker (recommended)

```bash
cp .env.sample .env       # already populated with dev defaults
make up                   # start Postgres + Django
make createsuperuser      # create an admin account
```

App: http://localhost:8000 · Admin: http://localhost:8000/admin/

Compose runs Postgres + Django with the source bind-mounted for hot reload.
The entrypoint applies migrations and collects static on every start.

Run `make` (or `make help`) to see all available targets — `up`, `down`,
`logs`, `migrate`, `makemigrations`, `shell`, `psql`, `test`, `clean`, etc.

## Setup — local virtualenv

```bash
cp .env.sample .env       # if not already present
make install              # creates .venv and installs requirements
make up                   # bring up Postgres in Docker for the venv to use
make runserver            # runs Django dev server from .venv
```

## Production image

The Dockerfile is production-shaped: non-root user, gunicorn (3 workers) as
CMD, no source bind mount.

```bash
docker build -t party-invitations .
docker run --rm -p 8000:8000 \
  -e DJANGO_SECRET_KEY=... \
  -e DJANGO_DEBUG=False \
  -e DJANGO_ALLOWED_HOSTS=yourdomain.com \
  -e DATABASE_URL=postgres://user:pass@host:5432/db \
  party-invitations
```

## Routes

| URL | Description |
|---|---|
| `/` | Host's party list (login required) |
| `/parties/new/` | Create a new party |
| `/parties/<id>/` | Party detail + invitation-link list |
| `/parties/<id>/invitations/new/` | Create a new invitation link |
| `/parties/<id>/invitations/<id>/` | Show the shareable URL with a copy button, plus the RSVP |
| `/parties/<id>/invitations/<id>/edit/` | Edit the link's settings — the token is unchanged |
| `/i/<token>/` | Public invitation page — recipient sees details and RSVP form |
| `/admin/` | Django admin |
