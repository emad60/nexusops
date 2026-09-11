# NexusOps developer workflow
.DEFAULT_GOAL := help
COMPOSE := docker compose
COMPOSE_DEV := $(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml

# Host-run connections (containers use the compose network instead)
PG_URL := postgresql+psycopg://$${POSTGRES_USER:-nexusops}:$${POSTGRES_PASSWORD:-change-me-postgres}@127.0.0.1:$${NEXUSOPS_POSTGRES_PORT:-5433}/$${POSTGRES_DB:-nexusops}
REDIS := redis://127.0.0.1:$${NEXUSOPS_REDIS_PORT:-6390}/0

.PHONY: help install dev up down logs test test-backend test-backend-unit test-frontend e2e \
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

test-backend: ## Full backend pytest suite (needs postgres+redis running)
	cd backend && DATABASE_URL=$(PG_URL) REDIS_URL=$(REDIS) uv run pytest

test-backend-unit: ## Backend unit tests only
	cd backend && uv run pytest -m "not integration"

test-frontend: ## Run frontend vitest suite
	cd frontend && npm test

e2e: wait-ready ## Run Playwright journey against a running stack (make up first)
	cd frontend && npx playwright install chromium 2>/dev/null; npx playwright test

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
	cd backend && DATABASE_URL=$(PG_URL) uv run alembic upgrade head

makemigrations: ## Autogenerate a migration: make makemigrations m="describe change"
	cd backend && DATABASE_URL=$(PG_URL) uv run alembic revision --autogenerate -m "$(m)"

seed: ## Seed demo data (opt-in; generates a one-time admin password it prints once)
	cd backend && DATABASE_URL=$(PG_URL) REDIS_URL=$(REDIS) SIMULATION_MODE=true NEXUSOPS_ALLOW_SEED=1 uv run python scripts/seed.py

clean: ## Stop stack AND delete volumes (DESTRUCTIVE: all data lost)
	$(COMPOSE_DEV) down -v --remove-orphans 2>/dev/null || $(COMPOSE) down -v --remove-orphans

build: ## Build all images without starting them
	$(COMPOSE) build
