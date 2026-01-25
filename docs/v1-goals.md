# V1 Goals

This document captures the V1 product goals and the minimum implementation
steps needed to reach them without expanding scope or adding new endpoints.

## Core goals (must-have)

1) MCP-backed content validation
- Status: implemented (advisory MCP layer).
- Implemented: MCP tools run after LLM generation as advisory, non-blocking checks.
- Next: feed MCP signals into content generation only if telemetry shows clear value.
- Keep the LLM as a proposer; tools provide advisory correctness signals.
- Example validators: math/stat checks, python execution checks, concept consistency.

2) Explicit content contracts (schema + semantics)
- Status: not started (beyond current structural validation).
- Formalize semantic constraints beyond structure.
- Emit typed validation failures (e.g., math_invalid, level_mismatch).
- Ensure exercises are solvable with provided context.

3) First-class telemetry for learning quality
- Status: partial (basic telemetry exists; quality metrics not yet tracked).
- Track validation retries by reason.
- Track MCP vs LLM disagreement rate.
- Track static vs LLM lesson quality deltas.
- Keep telemetry queryable even if minimal.

## Secondary goals (should-have)

4) Deterministic lesson rebuilds
- Status: not started.
- Same input spec + seed -> same lesson.
- MCP validation results reproducible for testing and review.

5) Clear agent boundary definition
- Status: implemented (documented agent boundaries).
- Planner: scope + timing.
- Content agent: generation only.
- Validator: validation only.
- Lesson service: orchestration + MCP calls.
- MCP tools: advisory signal on correctness (no gating).

## Nice-to-have (if time)

6) Runnable exercise panel with LLM feedback
- Status: not started.
- Add a UI panel for running exercise code.
- On completion, call the LLM to provide evaluation feedback.
- Record thumbs up/down feedback for each lesson.
- Keep evaluation stateless; no user accounts or grading history.

## Near-term steps (small, safe advances)

- Introduce typed validation reasons in the validator and telemetry. (partial: coarse error_type only)
- Add a single MCP-backed validator in a dry-run mode. (partial: advisory python_code_hints tool exists)
- Record retry reasons and attempt counts for evaluation. (attempt counts implemented; retry reasons not started)
- Document seed strategy without changing the public API. (not started)
