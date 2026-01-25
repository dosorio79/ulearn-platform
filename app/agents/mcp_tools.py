"""Minimal in-process MCP tool registry."""

from __future__ import annotations

from typing import Any, Callable, Dict

ToolHandler = Callable[[dict[str, Any]], Any]

_TOOLS: Dict[str, ToolHandler] = {}


def register_tool(name: str, handler: ToolHandler) -> None:
    """Register a tool by name."""
    _TOOLS[name] = handler


def invoke_tool(name: str, payload: dict[str, Any]) -> Any:
    """Invoke a tool by name with structured input."""
    handler = _TOOLS.get(name)
    if handler is None:
        raise KeyError(f"Tool not registered: {name}")
    return handler(payload)
