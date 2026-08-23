# NexusOps developer workflow
.DEFAULT_GOAL := help
COMPOSE := docker compose
COMPOSE_DEV := $(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml

.PHONY: help install dev up down logs test test-backend test-frontend e2e lint format typecheck migrate makemigrations seed clean build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install backend (uv) + frontend (pnpm) dependencies
	cd backend && uv sync --all-extras
	cd frontend && pnpm install

dev: ## Start full dev stack with hot reload (postgres/redis/api/worker/scheduler/vite/nginx)
	$(COMPOSE_DEV) up -d --build
	@echo "→ UI:      http://localhost:$${NEXUSOPS_HTTP_PORT:-8080}  (Vite direct: http://localhost:$${NEXUSOPS_VITE_PORT:-5173})"
	@echo "→ Mailpit: http://localhost:$${NEXUSOPS_MAILPIT_HTTP_PORT:-8025}"

up: ## Start production-shaped stack (built assets via nginx)
	$(COMPOSE) up -d --build
	@echo "→ UI: http://localhost:$${NEXUSOPS_HTTP_PORT:-8080}"

down: ## Stop the stack
	$(COMPOSE_DEV) down --remove-logs 2>/dev/null || $(COMPOSE) down

logs: ## Tail all service logs
	$(COMPOSE_DEV) logs -f 2>/dev/null || $(COMPOSE) logs -f

test: test-backend test-frontend ## Run backend and frontend tests

test-backend: ## Run backend pytest suite (needs postgres+redis: make dev or local services)
	cd backend && uv run pytest

test-backend-unit: ## Run backend unit tests only (no external services)
	cd backend && uv run pytest -m "not integration"

test-frontend: ## Run frontend vitest suite
	cd frontend && pnpm test --run

e2e: ## Run Playwright end-to-end suite (stack must be running)
	cd tests/e2e && pnpm install && pnpm exec playwright install chromium && pnpm exec playwright test

lint: lint-backend lint-frontend ## Lint everything

lint-backend:
	cd backend && uv run ruff check app tests && uv run ruff format --check app

lint-frontend:
	cd frontend && pnpm lint

format: ## Auto-format backend and frontend
	cd backend && uv run ruff format app tests && uv run ruff check --fix app tests
	cd frontend && pnpm format

typecheck: typecheck-backend typecheck-frontend ## Type-check everything

typecheck-backend:
	cd backend && uv run mypy app

typecheck-frontend:
	cd frontend && pnpm typecheck

migrate: ## Apply database migrations (host-run; uses localhost ports)
	cd backend && DATABASE_URL=postgresql+psycopg://$${POSTGRES_USER:-nexusops}:$${POSTGRES_PASSWORD:-change-me-postgres}@127.0.0.1:$${NEXUSOPS_POSTGRES_PORT:-5433}/$${POSTGRES_DB:-nexusops} REDIS_URL=redis://127.0.0.1:$${NEXUSOPS_REDIS_PORT:-6380}/0 uv run alembic upgrade head

makemigrations: ## Autogenerate a migration from model changes
	cd backend && DATABASE_URL=postgresql+psycopg://$${POSTGRES_USER:-nexusops}:$${POSTGRES_PASSWORD:-change-me-postgres}@127.0.0.1:$${NEXUSOPS_POSTGRES_PORT:-5433}/$${POSTGRES_DB:-nexusops} uv run alembic revision --autogenerate -m "$(m)"

seed: ## Seed realistic demo data (idempotent-ish: wipes domain tables first)
	cd backend && DATABASE_URL=postgresql+psycopg://$${POSTGRES_USER:-nexusops}:$${POSTGRES_PASSWORD:-change-me-postgres}@127.0.0.1:$${NEXUSOPS_POSTGRES_PORT:-5433}/$${POSTGRES_DB:-nexusops} REDIS_URL=redis://127.0.0.1:$${NEXUSOPS_REDIS_PORT:-6380}/0 SIMULATION_MODE=true uv run python -m scripts.seed

clean: ## Stop stack and remove volumes (DESTRUCTIVE: deletes all data)
	$(COMPOSE_DEV) down -v --remove-orphans 2>/dev/null || $(COMPOSE) down -v --remove-orphans

build: ## Build all images without starting
	$(COMPOSE) build
