.PHONY: help build start stop remove logs sync-dev test test-unit test-api test-content-parse test-integration test-service test-hints test-frontend test-all start-demo

help:
	@echo "Targets:"
	@echo "  build           Build containers and run them"
	@echo "  start           Start containers (no rebuild)"
	@echo "  stop            Stop containers (keeps containers)"
	@echo "  remove          Stop and remove containers"
	@echo "  logs            Tail docker compose logs"
	@echo "  sync-dev        Sync backend dev dependencies"
	@echo "  test            Run backend tests (uv)"
	@echo "  test-unit       Run unit tests"
	@echo "  test-api        Run API tests"
	@echo "  test-content-parse Run content parsing tests"
	@echo "  test-integration Run integration tests"
	@echo "  test-service     Run service orchestration tests"
	@echo "  test-hints       Run rule engine + MCP hint tests"
	@echo "  test-frontend   Run frontend tests"
	@echo "  test-all        Run backend and frontend tests"
	@echo "  start-demo      Start demo mode backend (static lessons, in-memory telemetry)"

build:
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
	@set -a; . ./.env; . ./.env.test; set +a; uv run pytest

sync-dev:
	@uv sync --extra dev

test-unit:
	@set -a; . ./.env; . ./.env.test; set +a; uv run pytest -m unit

test-api:
	@set -a; . ./.env; . ./.env.test; set +a; uv run pytest -m api

test-content-parse:
	@set -a; . ./.env; . ./.env.test; set +a; uv run pytest -m content_parse

test-integration:
	@set -a; . ./.env; . ./.env.test; set +a; uv run pytest -m integration

test-service:
	@set -a; . ./.env; . ./.env.test; set +a; uv run pytest tests/test_service.py

test-hints:
	@set -a; . ./.env; . ./.env.test; set +a; uv run pytest tests/test_validator_rules.py tests/test_mcp_hints.py tests/integration/test_lesson_workflow.py

test-frontend:
	@cd frontend && npm test

test-all: test test-frontend

start-demo:
	@STATIC_LESSON_MODE=true TELEMETRY_BACKEND=memory USE_LLM_CONTENT=false uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
