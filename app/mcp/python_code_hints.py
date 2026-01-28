"""MCP tool wrapper for advisory Python code hints."""

from __future__ import annotations

import ast
import logging
import re
import sys
from typing import Any

from app.agents.mcp_tools import register_tool
from app.core import config
from app.services.context7_client import fetch_context_snippets
from app.services.mcp_hints import (
    collect_hints_from_generated_sections,
    collect_hints_from_markdown_sections,
    explain_rule_outcomes,
)

_PYTHON_FENCE_RE = re.compile(r"```python\s*\r?\n(.*?)```", re.DOTALL)
logger = logging.getLogger(__name__)


def _python_code_hints_tool(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    mode = payload.get("mode")
    sections = payload.get("sections", [])
    rule_outcomes = payload.get("rule_outcomes", [])
    if mode == "agentic":
        hints, summary = collect_hints_from_generated_sections(sections)
    elif mode == "static":
        hints, summary = collect_hints_from_markdown_sections(sections)
    else:
        raise ValueError(f"Unsupported MCP hint mode: {mode}")

    if rule_outcomes:
        hints.extend(explain_rule_outcomes(rule_outcomes))

    python_blocks = summary["python_blocks"] if summary else _count_python_blocks(sections, mode)
    _append_context7_hints(hints, sections, mode)
    summary = _rebuild_summary(hints, python_blocks)
    return hints, summary


def _append_context7_hints(
    hints: list[dict[str, Any]],
    sections: list[Any],
    mode: str,
) -> None:
    api_key = config.CONTEXT7_API_KEY
    if not api_key:
        return

    libraries = _collect_third_party_libraries(sections, mode)
    if not libraries:
        return

    context_hints: list[dict[str, str]] = []
    cache: dict[str, dict[str, Any] | None] = {}
    for library in sorted(libraries):
        if library not in cache:
            cache[library] = _fetch_context_snippet(api_key, library)
            snippet = cache[library]
            logger.debug(
                "context7_query",
                extra={"library": library, "returned": bool(snippet and not snippet.get("error"))},
            )

        snippet = cache[library]
        if not snippet:
            continue
        if snippet.get("error"):
            context_hints.append(
                {
                    "code": "context7_error",
                    "message": f"Context7: error fetching documentation for '{library}'.",
                }
            )
            continue
        context_hints.append(
            {
                "code": "context7_reference",
                "message": f"Context7: reference documentation available for '{library}'.",
            }
        )

    if context_hints:
        hints.append(
            {
                "section_id": None,
                "block_index": None,
                "hints": context_hints,
            }
        )


def _collect_third_party_libraries(
    sections: list[Any],
    mode: str,
) -> set[str]:
    stdlib_modules = getattr(sys, "stdlib_module_names", set())
    libraries: set[str] = set()

    if mode == "agentic":
        for section in sections:
            for block in section.blocks:
                if block.type != "python":
                    continue
                libraries |= _extract_third_party_imports(block.content, stdlib_modules)
    else:
        for section in sections:
            for match in _PYTHON_FENCE_RE.finditer(section.content_markdown):
                code = match.group(1).rstrip()
                libraries |= _extract_third_party_imports(code, stdlib_modules)

    return libraries


def _count_python_blocks(sections: list[Any], mode: str) -> int:
    if mode == "agentic":
        return sum(
            1
            for section in sections
            for block in section.blocks
            if block.type == "python"
        )
    return sum(
        len(_PYTHON_FENCE_RE.findall(section.content_markdown))
        for section in sections
    )


def _extract_third_party_imports(code: str, stdlib_modules: set[str]) -> set[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()

    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split(".")[0])

    return {module for module in modules if module not in stdlib_modules}


def _fetch_context_snippet(api_key: str, module: str) -> dict[str, Any] | None:
    query = f"{module} API reference"
    try:
        snippets = fetch_context_snippets(
            api_key=api_key,
            library_name=module,
            query=query,
        )
    except Exception as exc:
        return {"error": str(exc)}
    if not snippets:
        return None
    return snippets[0]


def _rebuild_summary(
    hints: list[dict[str, Any]],
    python_blocks: int,
) -> dict[str, Any] | None:
    if python_blocks == 0:
        return None
    hint_count = sum(len(entry.get("hints", [])) for entry in hints)
    return {
        "python_blocks": python_blocks,
        "blocks_with_hints": len(hints),
        "total_hints": hint_count,
    }


register_tool("python_code_hints", _python_code_hints_tool)
