# Changelog

All notable changes to this project will be documented in this file.

## Repository history note

This repository was extracted from a larger monorepo during the AI Dev Tools Zoomcamp course. Earlier course exercises and unrelated modules were intentionally excluded. See `README.md` for the full migration context and rationale.

## [Unreleased]

### Added
- GitHub Actions CI workflow covering backend tests with MongoDB and frontend lint/test/build.
- Content parsing test marker (`content_parse`) for clarity.

### Changed
- Frontend CI now includes a production build step.

### Docs
- Documented CI behavior in the README and testing docs.
- Updated testing commands to use the `content_parse` marker.

## [0.3.0] - 2026-01-19

### Added
- Failure telemetry stored in Mongo for schema validation errors and unexpected exceptions.
- Markdown export controls (copy/download full lesson, copy per section).
- Frontend UX refinements (loading phases/progress, “Why it works”, feedback buttons, header logo).
- Loading error toast, elapsed seconds, and section chip actions.
- Runtime API base override via `frontend/public/runtime-config.js` for flexible frontend deployment.
- Nginx reverse proxy for `/lesson` and `/health` in the frontend container.

### Changed
- Refined frontend typography hierarchy for clearer primary/secondary/tertiary text contrast.
- Tweaked header/logo styling and in-card spacing for a tighter, calmer layout.
- Polished lesson section styling (section borders, larger chips, icon-only copy control).
- Enforced structured text formatting in validator and prompts.
- Updated exercise markdown fence format for frontend rendering.
- Removed legacy lovable tagger and updated meta images.
- Frontend API client now supports same-origin requests and runtime base selection.
- Backend LLM content generation uses async execution with robust result parsing.
- `/lesson` endpoint serves without trailing-slash redirects.
- Integration tests target localhost Mongo when run from the host.

### Docs
- Documented runtime config, prompt editing, and frontend UX behavior.

## [0.2.0] - 2026-01-17

### Added
- Runtime API base override via `frontend/public/runtime-config.js` for flexible frontend deployment.
- Nginx reverse proxy for `/lesson` and `/health` in the frontend container.

### Changed
- Frontend API client supports same-origin requests and runtime base selection.
- LLM content generation uses async execution with robust result parsing.
- `/lesson` serves without trailing-slash redirects.
- Integration tests target localhost Mongo when run from the host.

### Docs
- Documented runtime config and Docker proxy behavior in frontend and root docs.

## [0.1.0] - 2026-01-01

### Added
- Initial FastAPI backend with `/lesson` and `/health`.
- Agent pipeline (planner, content, validator) and Mongo telemetry.
- React + Vite frontend with lesson rendering and Pyodide execution.
