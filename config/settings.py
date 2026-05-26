"""Django settings for the party-invitations project."""
import os
from pathlib import Path

import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-secret-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

# Comma-separated list of origins trusted for CSRF on HTTPS POSTs. Required
# by Django 4+ for cross-scheme or cross-port form posts. In production set
# this to the public origin(s), e.g.
#   CSRF_TRUSTED_ORIGINS=https://party-invitations-xxxxx.ondigitalocean.app
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

# DO App Platform (and most PaaS/load balancers) terminate TLS at the edge
# and forward to the app over plain HTTP, setting X-Forwarded-Proto: https.
# Without this hint Django sees the request as HTTP and (a) rejects the
# HTTPS Referer in CSRF checks and (b) won't set Secure cookies. Safe here
# because the only deployment topology is "behind a proxy that always
# sets this header"; do not enable if the app is ever exposed directly.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# In production, cookies must only travel over HTTPS.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "invitations.apps.InvitationsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get(
            "DATABASE_URL",
            "postgres://postgres:postgres@localhost:5432/party_invitations",
        ),
        conn_max_age=600,
    ),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Languages a host can pick when creating an invitation. Adding a new locale:
#   1. Append the tuple here.
#   2. Run `make messages` to scaffold locale/<code>/LC_MESSAGES/django.po.
#   3. Translate the entries and `make compilemessages`.
LANGUAGES = [
    ("en", "English"),
    ("es", "Español"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "party_list"
LOGOUT_REDIRECT_URL = "login"
