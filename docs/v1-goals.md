# V1 Goals

This document captures the V1 product goals and the minimum implementation
steps needed to reach them without expanding scope or adding new endpoints.

## Core goals (must-have)

1) MCP-backed content validation
- Add a validation layer that calls MCP tools after LLM generation.
- Keep the LLM as a proposer; tools arbitrate correctness.
- Example validators: math/stat checks, python execution checks, concept consistency.

2) Explicit content contracts (schema + semantics)
- Formalize semantic constraints beyond structure.
- Emit typed validation failures (e.g., math_invalid, level_mismatch).
- Ensure exercises are solvable with provided context.

3) First-class telemetry for learning quality
- Track validation retries by reason.
- Track MCP vs LLM disagreement rate.
- Track static vs LLM lesson quality deltas.
- Keep telemetry queryable even if minimal.

## Secondary goals (should-have)

4) Deterministic lesson rebuilds
- Same input spec + seed -> same lesson.
- MCP validation results reproducible for testing and review.

5) Clear agent boundary definition
- Planner: scope + timing.
- Content agent: generation only.
- Validator: orchestration + MCP calls.
- MCP tools: authority on correctness.

## Nice-to-have (if time)

6) Runnable exercise panel with LLM feedback
- Add a UI panel for running exercise code.
- On completion, call the LLM to provide evaluation feedback.
- Record thumbs up/down feedback for each lesson.
- Keep evaluation stateless; no user accounts or grading history.

## Near-term steps (small, safe advances)

- Introduce typed validation reasons in the validator and telemetry.
- Add a single MCP-backed validator in a dry-run mode.
- Record retry reasons and attempt counts for evaluation.
- Document seed strategy without changing the public API.
