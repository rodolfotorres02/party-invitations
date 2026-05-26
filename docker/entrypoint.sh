#!/usr/bin/env bash
# Runs at every container start. Applies migrations, collects static, then
# execs the container CMD (gunicorn by default, runserver under compose).
set -euo pipefail

python manage.py migrate --noinput
python manage.py collectstatic --noinput
# Compile .po translation sources to .mo. Idempotent and quick; runs at every
# container start so dev bind-mounts always reflect the latest .po files.
python manage.py compilemessages --ignore=.venv --ignore=venv

exec "$@"
