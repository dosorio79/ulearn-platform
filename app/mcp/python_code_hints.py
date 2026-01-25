"""MCP tool wrapper for advisory Python code hints."""

from __future__ import annotations

from typing import Any

from app.agents.mcp_tools import register_tool
from app.services.mcp_hints import (
    collect_hints_from_generated_sections,
    collect_hints_from_markdown_sections,
)


def _python_code_hints_tool(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    mode = payload.get("mode")
    sections = payload.get("sections", [])
    if mode == "agentic":
        return collect_hints_from_generated_sections(sections)
    if mode == "static":
        return collect_hints_from_markdown_sections(sections)
    raise ValueError(f"Unsupported MCP hint mode: {mode}")


register_tool("python_code_hints", _python_code_hints_tool)
