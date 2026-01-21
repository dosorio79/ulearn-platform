# Deployment and container model

## Overview

The system is composed of multiple containers that run together as a single application using Docker Compose.

Each container has a single responsibility and runs as an independent service.

There is no single “monolithic” container.

---

## Containers in this project

### Backend container

The backend container runs the application logic.

It includes:
- FastAPI application
- Agent orchestration logic
- MongoDB client (driver only)

It does NOT include:
- A database engine
- Persistent storage

The backend container exposes the API at:

- http://localhost:8000

---

### MongoDB container

MongoDB runs in its own dedicated container.

It is responsible for:
- Storing lesson generation telemetry
- Persisting data across restarts

It contains:
- The MongoDB database engine
- A persistent Docker volume for data

It does NOT contain:
- Application code
- API logic

The backend connects to MongoDB over Docker’s internal network.

---

### Frontend container

The frontend runs in a separate container.

It serves:
- A static React (Vite) build
- No server-side logic

Important notes:
- The frontend calls the backend API via the nginx proxy (`/lesson`, `/health`)
- The container exists for reproducibility and mirrors the production static build

The frontend container serves the UI at:

- http://localhost:8080

---

## Environment configuration

The backend reads environment variables from `.env` or the container environment:

- `OPENAI_API_KEY`: required when `USE_LLM_CONTENT=true`
- `MODEL`: LLM model name (defaults to `gpt-4.1-mini`)
- `USE_LLM_CONTENT`: toggle LLM-backed content generation (`true`/`false`)
- `CORS_ORIGINS`: comma-separated list of allowed origins (default: `http://localhost:8080`)
- `MONGO_FAILURE_COLLECTION`: MongoDB collection name for failure telemetry (default: `lesson_failures`)
- `STATIC_LESSON_MODE`: serve static lesson templates instead of agent-generated content (`true`/`false`)
- `TELEMETRY_BACKEND`: telemetry destination (`mongo` or `memory`)
- `DEMO_MODE`: shorthand to enable demo defaults (static lessons + memory telemetry)
- `TELEMETRY_MEMORY_CAP`: max in-memory telemetry entries when using `memory` (default: `1000`)

## Quick start

If you have Make installed, the fastest path is:

```bash
make build
```

If images are already built:

```bash
make start
```

## Render demo deployment

This repo includes a Render blueprint (`render.yaml`) that runs a static lesson demo with in-memory telemetry.

What it does:
- backend runs with `DEMO_MODE=true` (static lessons + memory telemetry)
- frontend builds a static Vite app and injects `API_BASE` into `frontend/public/runtime-config.js`

To use it:
1) Update `render.yaml` with the backend URL you want (`API_BASE`).
2) Create a new Render Blueprint from `render.yaml`.
3) Deploy the backend first, then the static site.

### Continuous deployment tips

- Keep `autoDeploy: true` in `render.yaml` for both services.
- Ensure the backend sets `CORS_ORIGINS` to the static site domain (for example, `https://ulearn-frontend.onrender.com`).
- If the backend URL changes, update `API_BASE` and redeploy the static site.
