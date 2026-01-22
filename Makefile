.PHONY: help build start stop remove logs test test-unit test-api test-content-parse test-integration test-frontend test-all frontend-build start-demo

help:
	@echo "Targets:"
	@echo "  build           Build frontend and run containers"
	@echo "  start           Start containers (no rebuild)"
	@echo "  stop            Stop containers (keeps containers)"
	@echo "  remove          Stop and remove containers"
	@echo "  logs            Tail docker compose logs"
	@echo "  test            Run backend tests (uv)"
	@echo "  test-unit       Run unit tests"
	@echo "  test-api        Run API tests"
	@echo "  test-content-parse Run content parsing tests"
	@echo "  test-integration Run integration tests"
	@echo "  test-frontend   Run frontend tests"
	@echo "  test-all        Run backend and frontend tests"
	@echo "  start-demo      Start demo mode backend (static lessons, in-memory telemetry)"

frontend-build:
	@if [ ! -d frontend/node_modules ]; then \
		cd frontend && npm install; \
	fi
	@cd frontend && npm run build

build: frontend-build
	@docker compose up --build

start:
	@docker compose start

stop:
	@docker compose stop

remove:
	@docker compose down

logs:
	@docker compose logs -f

test:
	@uv sync --extra dev
	@uv run pytest

test-unit:
	@uv sync --extra dev
	@uv run pytest -m unit

test-api:
	@uv sync --extra dev
	@uv run pytest -m api

test-content-parse:
	@uv sync --extra dev
	@uv run pytest -m content_parse

test-integration:
	@uv sync --extra dev
	@uv run pytest -m integration

test-frontend:
	@cd frontend && npm test

test-all: test test-frontend

start-demo:
	@STATIC_LESSON_MODE=true TELEMETRY_BACKEND=memory USE_LLM_CONTENT=false uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
