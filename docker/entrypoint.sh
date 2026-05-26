#!/usr/bin/env bash
# Runs at every container start. Applies migrations, collects static, then
# execs the container CMD (gunicorn by default, runserver under compose).
set -euo pipefail

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
