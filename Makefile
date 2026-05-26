# Convenience targets. Run `make` (or `make help`) to list them.
#
# Defaults assume the Docker compose stack is the primary dev environment.
# Use the `install` target if you prefer a local virtualenv instead.

DC  := docker compose
WEB := $(DC) exec web

.DEFAULT_GOAL := help
.PHONY: help up down build rebuild logs ps restart shell bash \
        migrate makemigrations createsuperuser collectstatic test check \
        psql messages compilemessages clean install runserver

help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# --- Docker stack -----------------------------------------------------------

up: ## Start db + web in the background
	$(DC) up -d

down: ## Stop the stack (keeps the db volume)
	$(DC) down

build: ## Build the web image
	$(DC) build

rebuild: ## Rebuild the web image with no cache
	$(DC) build --no-cache

logs: ## Tail logs from all services
	$(DC) logs -f

ps: ## Show running containers
	$(DC) ps

restart: ## Restart the web container
	$(DC) restart web

clean: ## Stop the stack and DELETE the db volume
	$(DC) down -v

# --- Django (run inside the web container) ----------------------------------

shell: ## Open a Django shell
	$(WEB) python manage.py shell

bash: ## Open a bash shell in the web container
	$(WEB) bash

migrate: ## Apply database migrations
	$(WEB) python manage.py migrate

makemigrations: ## Generate new migrations from model changes
	$(WEB) python manage.py makemigrations

createsuperuser: ## Create an admin user
	$(WEB) python manage.py createsuperuser

collectstatic: ## Collect static files
	$(WEB) python manage.py collectstatic --noinput

test: ## Run the test suite
	$(WEB) python manage.py test

check: ## Run Django's system check
	$(WEB) python manage.py check

psql: ## Open psql in the db container
	$(DC) exec db psql -U postgres -d party_invitations

messages: ## Extract translatable strings into locale/<lang>/LC_MESSAGES/django.po
	$(WEB) python manage.py makemessages -a -i .venv --no-location

compilemessages: ## Compile .po → .mo so changes take effect
	$(WEB) python manage.py compilemessages --ignore=.venv

# --- Local virtualenv (alternative to Docker) -------------------------------

install: ## Create .venv and install dependencies locally
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

runserver: ## Run Django dev server from the local venv (needs `make install` and a running db)
	.venv/bin/python manage.py runserver
