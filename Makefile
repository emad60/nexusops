# NexusOps developer workflow
.DEFAULT_GOAL := help
COMPOSE := docker compose
COMPOSE_DEV := $(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml

# Host-run connections (containers use the compose network instead). Two roles:
#   PG_URL     — owner: migrations and bootstrap scripts only. Owning a table
#                means bypassing its RLS policies, so it never serves traffic.
#   APP_PG_URL — application role: the runtime, where the tenant policies apply.
PG_URL := postgresql+psycopg://$${POSTGRES_USER:-nexusops_owner}:$${POSTGRES_PASSWORD:-change-me-postgres}@127.0.0.1:$${NEXUSOPS_POSTGRES_PORT:-5433}/$${POSTGRES_DB:-nexusops}
APP_PG_URL := postgresql+psycopg://$${POSTGRES_APP_USER:-nexusops_app}:$${POSTGRES_APP_PASSWORD:-change-me-postgres-app}@127.0.0.1:$${NEXUSOPS_POSTGRES_PORT:-5433}/$${POSTGRES_DB:-nexusops}
REDIS := redis://127.0.0.1:$${NEXUSOPS_REDIS_PORT:-6390}/0

.PHONY: help install dev up down logs test test-backend test-backend-unit test-frontend e2e e2e-stack e2e-await-worker e2e-down \
        lint lint-backend lint-frontend format typecheck migrate makemigrations seed clean build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install backend (uv) and frontend (npm) dependencies
	cd backend && uv sync
	cd frontend && npm install

dev: ## Start full dev stack with hot reload (vite on :5173)
	$(COMPOSE_DEV) up -d --build
	@echo "→ UI:      http://localhost:$${NEXUSOPS_HTTP_PORT:-8080}   (Vite direct: http://localhost:$${NEXUSOPS_VITE_PORT:-5173})"
	@echo "→ Mailpit: http://localhost:$${NEXUSOPS_MAILPIT_HTTP_PORT:-8025}"
	@echo "→ Seeded admin credentials: printed once by the seed script output"

up: ## Start production-shaped stack (built assets behind nginx); auto-migrates
	$(COMPOSE) up -d --build
	$(MAKE) -s wait-ready
	$(MAKE) -s seed
	@echo "→ UI: http://localhost:$${NEXUSOPS_HTTP_PORT:-8080}"
	@echo "→ Seeded admin credentials: printed once by the seed script output"

wait-ready: ## Block until API AND the SPA both answer through the edge
	@echo "waiting for the stack to become ready..."
	@for i in $$(seq 1 60); do \
		if curl -fsS http://127.0.0.1:$${NEXUSOPS_HTTP_PORT:-8080}/api/v1/ready >/dev/null 2>&1 \
			&& curl -fsS http://127.0.0.1:$${NEXUSOPS_HTTP_PORT:-8080}/ >/dev/null 2>&1; then \
			echo "ready"; exit 0; fi; \
		sleep 2; \
	done; echo "stack did not become ready in time"; exit 1

down: ## Stop the stack
	$(COMPOSE_DEV) down 2>/dev/null || $(COMPOSE) down

logs: ## Tail all service logs
	$(COMPOSE_DEV) logs -f 2>/dev/null || $(COMPOSE) logs -f

test: test-backend-unit test-frontend ## Run unit suites (no external services needed)

test-backend: ## Full backend pytest suite, RLS enforced (needs postgres+redis running)
	cd backend && DATABASE_URL=$(APP_PG_URL) MIGRATION_DATABASE_URL=$(PG_URL) REDIS_URL=$(REDIS) uv run pytest

test-backend-unit: ## Backend unit tests only
	cd backend && uv run pytest -m "not integration"

test-frontend: ## Run frontend vitest suite
	cd frontend && npm test

# --- End-to-end journey -----------------------------------------------------
# `make e2e` is self-contained: its own compose project on its own host ports,
# ENVIRONMENT=test (which is what makes the seeded admin password deterministic
# — see docker-compose.e2e.yml), seeded, exercised, then torn down with its
# volume. A dev stack on the default ports is left alone.
E2E_PROJECT      ?= nexusops-e2e
E2E_HTTP_PORT    ?= 8090
E2E_MAILPIT_PORT ?= 8026
E2E_PG_PORT      ?= 5434
E2E_REDIS_PORT   ?= 6391

E2E_COMPOSE := NEXUSOPS_HTTP_PORT=$(E2E_HTTP_PORT) \
               NEXUSOPS_MAILPIT_HTTP_PORT=$(E2E_MAILPIT_PORT) \
               NEXUSOPS_POSTGRES_PORT=$(E2E_PG_PORT) \
               NEXUSOPS_REDIS_PORT=$(E2E_REDIS_PORT) \
               $(COMPOSE) -p $(E2E_PROJECT) -f docker-compose.yml -f docker-compose.e2e.yml

# Owner DSN pinned to the e2e port directly. Deliberately NOT reusing $(PG_URL):
# that one resolves the port through `${NEXUSOPS_POSTGRES_PORT:-5433}`, and
# `VAR=1 OTHER=${VAR:-x} cmd` does not pick up the sibling assignment, so it
# silently fell back to the dev port. The port is baked in here instead.
E2E_PG_URL := postgresql+psycopg://$${POSTGRES_USER:-nexusops_owner}:$${POSTGRES_PASSWORD:-change-me-postgres}@127.0.0.1:$(E2E_PG_PORT)/$${POSTGRES_DB:-nexusops}
E2E_REDIS_URL := redis://127.0.0.1:$(E2E_REDIS_PORT)/0

# Host-run seed against the e2e port. `.env` is sourced (with `set -a`, so its
# POSTGRES_* reach the URL) and ENVIRONMENT=test is what makes the admin password
# deterministic — see docker-compose.e2e.yml.
E2E_SEED := set -a; [ -f .env ] && . ./.env; set +a; \
            cd backend && ENVIRONMENT=test SIMULATION_MODE=true \
            DATABASE_URL=$(E2E_PG_URL) MIGRATION_DATABASE_URL=$(E2E_PG_URL) \
            REDIS_URL=$(E2E_REDIS_URL) uv run python scripts/seed.py

# The journey drives worker-backed work (monitor checks -> incidents ->
# notifications) seconds after this point, so the edge answering is not enough:
# Celery must answer its own healthcheck first, or the first notification lands
# after the journey has already moved on. `make up`'s wait-ready only checks the
# API and the SPA.
e2e-await-worker: ## Wait for the Celery worker to report healthy
	@for i in $$(seq 1 40); do \
		cid=$$($(E2E_COMPOSE) ps -q worker 2>/dev/null); \
		state=$$(docker inspect -f '{{.State.Health.Status}}' $$cid 2>/dev/null); \
		if [ "$$state" = "healthy" ]; then echo "worker ready"; exit 0; fi; \
		sleep 3; \
	done; echo "worker did not become healthy in time"; exit 1

e2e: ## Run the Playwright journey on a throwaway isolated stack, then tear it down
	@$(E2E_COMPOSE) up -d --build && \
	 NEXUSOPS_HTTP_PORT=$(E2E_HTTP_PORT) $(MAKE) -s wait-ready && \
	 $(MAKE) -s e2e-await-worker && \
	 ( $(E2E_SEED) ) && \
	 ( cd frontend && npx playwright install chromium >/dev/null 2>&1 || true; \
	     E2E_BASE_URL=http://127.0.0.1:$(E2E_HTTP_PORT) \
	     E2E_MAILPIT_URL=http://127.0.0.1:$(E2E_MAILPIT_PORT) npx playwright test ); \
	 status=$$?; $(E2E_COMPOSE) down -v --remove-orphans >/dev/null 2>&1 || true; \
	 if [ $$status -ne 0 ]; then echo "e2e failed (stack torn down)"; fi; exit $$status

e2e-stack: ## Bring up + seed the isolated e2e stack and leave it running (for debugging)
	@$(E2E_COMPOSE) up -d --build && \
	 NEXUSOPS_HTTP_PORT=$(E2E_HTTP_PORT) $(MAKE) -s wait-ready && \
	 $(MAKE) -s e2e-await-worker && \
	 ( $(E2E_SEED) ) && \
	 echo "→ e2e stack up: UI http://127.0.0.1:$(E2E_HTTP_PORT)  mailpit http://127.0.0.1:$(E2E_MAILPIT_PORT)" && \
	 echo "→ admin: admin@nexusops.example.com / nexusops-admin" && \
	 echo "→ run: cd frontend && E2E_BASE_URL=http://127.0.0.1:$(E2E_HTTP_PORT) E2E_MAILPIT_URL=http://127.0.0.1:$(E2E_MAILPIT_PORT) npx playwright test"

e2e-down: ## Tear down the isolated e2e stack and its volume (DESTRUCTIVE)
	@$(E2E_COMPOSE) down -v --remove-orphans

lint: lint-backend lint-frontend ## Lint everything
lint-backend:
	cd backend && uv run ruff check app scripts tests && uv run ruff format --check app scripts tests
lint-frontend:
	cd frontend && npm run lint

format: ## Auto-format the backend
	cd backend && uv run ruff format app scripts tests && uv run ruff check --fix app scripts tests

typecheck: typecheck-backend typecheck-frontend ## Type-check everything
typecheck-backend:
	cd backend && uv run mypy app
typecheck-frontend:
	cd frontend && npx tsc --noEmit

migrate: ## Apply database migrations from the host (stack must be up)
	cd backend && MIGRATION_DATABASE_URL=$(PG_URL) uv run alembic upgrade head

makemigrations: ## Autogenerate a migration: make makemigrations m="describe change"
	cd backend && MIGRATION_DATABASE_URL=$(PG_URL) uv run alembic revision --autogenerate -m "$(m)"

seed: ## Seed demo data (opt-in; generates a one-time admin password it prints once)
# Runs as the owner on purpose: seeding provisions the first organization and
# its membership, which is the one thing that cannot happen inside a tenant scope.
	cd backend && DATABASE_URL=$(PG_URL) MIGRATION_DATABASE_URL=$(PG_URL) REDIS_URL=$(REDIS) SIMULATION_MODE=true NEXUSOPS_ALLOW_SEED=1 uv run python scripts/seed.py

clean: ## Stop stack AND delete volumes (DESTRUCTIVE: all data lost)
	$(COMPOSE_DEV) down -v --remove-orphans 2>/dev/null || $(COMPOSE) down -v --remove-orphans

build: ## Build all images without starting them
	$(COMPOSE) build
