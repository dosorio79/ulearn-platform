# MCP (In-Process Tooling)

## Scope

MCP is used as an internal tool boundary to run advisory checks without changing lesson validation or output. There are no external services, servers, or network calls. MCP usage is deterministic, non-blocking, and logged for telemetry analysis only.

## Tool registry

The registry lives in `app/agents/mcp_tools.py` and provides:
- `register_tool(name, handler)`
- `invoke_tool(name, payload)`

Tools are registered in-process and invoked with structured inputs.

## Tool: `python_code_hints`

Purpose: Run advisory, static inspection of Python code blocks after lesson generation.

Registration:
- `app/mcp/python_code_hints.py`

Input payload:
```json
{
  "mode": "agentic" | "static",
  "sections": []
}
```

Behavior:
- `agentic` mode → calls `collect_hints_from_generated_sections`
- `static` mode → calls `collect_hints_from_markdown_sections`
- Returns `(hints, summary)` with the existing hint structure

Hint categories include:
- Syntax errors and unsafe calls
- Missing output (no `print`/`display`)
- Suspicious third-party imports (excluding `pandas`, `numpy`, `scipy`)
- Heavy libraries (`sklearn`, `torch`, `tensorflow`)
- Style nits (long lines)
- Common pandas pitfalls (e.g., `df.apply`)

Hints are:
- logged and stored in telemetry
- never shown to users
- never used for validation or gating

## Execution flow

1. Lesson content is generated (agentic or static).
2. The service invokes `python_code_hints` via the tool registry.
3. Hints are logged and stored in telemetry only.
4. Lesson output and validation are unchanged.
