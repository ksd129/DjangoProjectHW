# Get user id for macOS and Linux
ifeq ($(shell uname),Darwin)
	USER_ID := $(shell id -u)
else
	USER_ID := $(shell id --user)
endif

#-include .env

.PHONY: echo-i-uid
# Echo user id
echo-i-uid:
	@echo ${USER_ID}

.PHONY: d-homework-i-run
# Make all actions needed for run homework from zero.
d-homework-i-run: init-configs d-run

.PHONY: d-homework-i-purge
# Make all actions needed for purge homework related data.
d-homework-i-purge:
	@make d-purge


.PHONY: init-configs
# Configuration files initialization
init-configs:
	@cp .env.example .env &&\
		cp compose.override.dev.yaml compose.override.yaml

.PHONY: d-run
# Just run
d-run:
	@export USER_ID=${USER_ID} &&\
	COMPOSE_PROFILES=full_dev \
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
		docker compose up \
			--build

.PHONY: d-run-i-local-dev
# Run services for local development
d-run-i-local-dev:
	@export USER_ID=${USER_ID} &&\
	COMPOSE_PROFILES=local_dev \
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
		docker compose up \
			--build

.PHONY: d-purge
# Purge all data related with services
d-purge:
	@export USER_ID=${USER_ID} &&\
	COMPOSE_PROFILES=full_dev \
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
		docker compose down --volumes --remove-orphans --rmi local --timeout 0

.PHONY: d-compose-inspect
# Get information about current compose configuration
d-compose-inspect:
	@export USER_ID=${USER_ID} &&\
	COMPOSE_PROFILES=full_dev \
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
		docker compose convert

.PHONY: init-dev
# Init environment for development
init-dev:
	@make poetry-install && \
	pre-commit install

.PHONY: homework-i-run
# Run homework.
homework-i-run:
	@python main.py

.PHONY: homework-i-purge
homework-i-purge:
	@echo Goodbye


# [pre-commit]-[BEGIN]
.PHONY: pre-commit-run
# Run tools for files from commit.
pre-commit-run:
	@pre-commit run

.PHONY: pre-commit-run-all
# Run tools for all files.
pre-commit-run-all:
	@pre-commit run --all-files

.PHONY: pre-commit-autoupdate
# Update "rev" version of all pre-commit hooks.
pre-commit-autoupdate:
	@pre-commit autoupdate
# [pre-commit]-[END]


# [poetry]-[BEGIN]
.PHONY: poetry-up-latest
# Update all packages to the latest version allowed by the current constraints.
poetry-up-latest:
	@poetry up --latest

.PHONY: poetry-up-latest-no-install
# Update all packages to the latest version allowed by the current constraints.
poetry-up-latest-no-install:
	@poetry up --latest --no-install

.PHONY: poetry-lock
# Lock the current dependencies.
poetry-lock:
	@poetry lock

.PHONY: poetry-install
# Install the current dependencies.
poetry-install:
	@poetry install --no-root --sync


.PHONY: poetry-self-show-plugins
# Show plugins for poetry.
poetry-self-show-plugins:
	@poetry self show --plugins


.PHONY: poetry-export-requirements
# Export the current dependencies to requirements.txt.
poetry-export-requirements:
	@poetry export --format requirements.txt --output requirements.txt --without-hashes
# [poetry]-[END]

# [extra_python]-[BEGIN]
.PHONY: install-pipx
# Install pipx.
# Note: Reloading shell is needed after this action.
# Note: Make not from virtual environment.
install-pipx:
	@python3.12 -m ensurepip &&\
	python3.12 -m pip install --upgrade pip &&\
	python3.12 -m pip install --user pipx &&\
	python3.12 -m pipx ensurepath

.PHONY: install-poetry
# Install poetry.
# Note: Reloading shell is needed after this action.
install-poetry:
	@pipx install poetry &&\
	pipx upgrade poetry &&\
	poetry self add poetry-plugin-export ;\
	poetry self add poetry-plugin-up

.PHONY: install-pre-commit
# Install pre-commit.
install-pre-commit:
	@pipx install pre-commit &&\
	pipx upgrade pre-commit

.PHONY: install-ruff
# Install black.
install-ruff:
	@pipx install ruff &&\
	pipx upgrade ruff

# [extra_python]-[END]

.PHONY: migrations
# Make migrations
migrations:
	@python manage.py makemigrations

.PHONY: migrate
# Migrate
migrate:
	@python manage.py migrate


.PHONY: init-data
# Init data
init-data:
	@python manage.py posts_generate --amount 23 --initial

DJANGO_SUPERUSER_PASSWORD ?= admin123
DJANGO_SUPERUSER_USERNAME ?= admin
DJANGO_SUPERUSER_EMAIL ?= admin@gmail.com

.PHONY: init-dev-i-create-superuser
# Create superuser
init-dev-i-create-superuser:
	@DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD} \
		python manage.py createsuperuser \
			--user ${DJANGO_SUPERUSER_USERNAME} \
			--email ${DJANGO_SUPERUSER_EMAIL} \
			--no-input
