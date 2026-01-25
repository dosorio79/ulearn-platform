"""MCP tool wrapper for advisory Python code hints."""

from __future__ import annotations

from typing import Any

import re

from app.agents.mcp_tools import register_tool
from app.core import config
from app.services.context7_client import fetch_context_snippets
from app.services.mcp_hints import (
    collect_hints_from_generated_sections,
    collect_hints_from_markdown_sections,
)

_IMPORT_MESSAGE_RE = re.compile(r"Import (?:of|from) '([^']+)'")


def _python_code_hints_tool(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    mode = payload.get("mode")
    sections = payload.get("sections", [])
    if mode == "agentic":
        hints, summary = collect_hints_from_generated_sections(sections)
    elif mode == "static":
        hints, summary = collect_hints_from_markdown_sections(sections)
    else:
        raise ValueError(f"Unsupported MCP hint mode: {mode}")

    _append_context7_hints(hints)
    return hints, summary


def _append_context7_hints(hints: list[dict[str, Any]]) -> None:
    api_key = config.CONTEXT7_API_KEY
    if not api_key:
        return

    for entry in hints:
        modules = _extract_modules(entry.get("hints", []))
        if not modules:
            continue
        context_hints = []
        for module in modules:
            query = f"How to use {module} in Python"
            try:
                snippets = fetch_context_snippets(
                    api_key=api_key,
                    library_name=module,
                    query=query,
                )
            except Exception:
                continue
            if not snippets:
                continue
            snippet = snippets[0]
            title = snippet.get("title", "Context7 snippet")
            source = snippet.get("source", "context7.com")
            context_hints.append(
                {
                    "code": "context7_context",
                    "message": f"Context7: {title} ({source}).",
                }
            )
        if context_hints:
            entry["hints"].extend(context_hints)


def _extract_modules(hints: list[dict[str, Any]]) -> list[str]:
    modules: list[str] = []
    for hint in hints:
        if hint.get("code") not in {"third_party_import", "heavy_import"}:
            continue
        message = hint.get("message", "")
        match = _IMPORT_MESSAGE_RE.search(message)
        if match:
            modules.append(match.group(1))
    return modules


register_tool("python_code_hints", _python_code_hints_tool)
