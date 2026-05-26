# syntax=docker/dockerfile:1.7
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# psycopg[binary] ships its own libpq, so we only need runtime tools.
# gettext is needed at runtime so `manage.py compilemessages` can build
# .mo files from the .po sources.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gettext \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first — cached unless requirements.txt changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Non-root runtime user.
RUN useradd --create-home --shell /bin/bash app

COPY --chown=app:app . .
RUN chmod +x /app/docker/entrypoint.sh

USER app
EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
