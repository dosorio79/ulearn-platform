# Testing

## Overview

This project includes frontend and backend test suites. Follow the sections below to run each suite locally.

## Frontend tests

Location: `frontend/`

```bash
cd frontend
npm test
```

What is covered:

- Lesson rendering from API responses (the client is mocked in frontend tests).
- Full user flow (input → generate → lesson appears).
- Python code block Run button behavior.
- Exercise block rendering.

## Backend tests

Location: project root

```bash
uv run pytest
```

If you want reproducible dependencies for local runs, sync with the lockfile first:

```bash
uv sync --extra dev --frozen
```

Integration tests live in `tests/integration/` and run with the `integration` marker:

```bash
uv run pytest -m integration
```

If you see cache permission errors, you can run with a project-local cache:

```bash
UV_CACHE_DIR=.uv-cache uv run pytest
```

What is covered:

- Agent planning and validation logic.
- Lesson orchestration.
- API contract and integration workflow.
- Telemetry model validation (happy path and invalid level).
- Text block formatting rules (paragraph + list requirement).
- UI export/copy (Markdown and notebook) and feedback interactions are covered in frontend tests.

Markers are available to focus on subsets:

- `unit`: unit tests
- `content_parse`: Content agent parsing tests (no LLM calls)
- `api`: API contract tests
- `integration`: integration tests

Example:

```bash
pytest -m unit
```

If you prefer using the system interpreter instead of `uv`, ensure `pytest` is installed in your environment, then run:

```bash
python -m pytest
```

## CI

GitHub Actions runs backend tests (with a MongoDB service) and frontend lint/test/build on every push and pull request. See `.github/workflows/ci.yml` for the exact steps.

## Notes

- Frontend tests mock the API client; the running app calls the backend.
- Integration tests that require MongoDB should run with `docker compose up`.
