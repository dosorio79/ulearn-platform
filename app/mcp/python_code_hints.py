"""MCP tool wrapper for advisory Python code hints."""

from __future__ import annotations

import ast
import re
import sys
from typing import Any

from app.agents.mcp_tools import register_tool
from app.core import config
from app.services.context7_client import fetch_context_snippets
from app.services.mcp_hints import (
    collect_hints_from_generated_sections,
    collect_hints_from_markdown_sections,
)

_PYTHON_FENCE_RE = re.compile(r"```python\s*\r?\n(.*?)```", re.DOTALL)


def _python_code_hints_tool(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    mode = payload.get("mode")
    sections = payload.get("sections", [])
    if mode == "agentic":
        hints, summary = collect_hints_from_generated_sections(sections)
    elif mode == "static":
        hints, summary = collect_hints_from_markdown_sections(sections)
    else:
        raise ValueError(f"Unsupported MCP hint mode: {mode}")

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

    modules_by_block = _collect_third_party_modules(sections, mode)
    if not modules_by_block:
        return

    cache: dict[str, dict[str, Any] | None] = {}
    for key, modules in modules_by_block.items():
        if not modules:
            continue
        entry = _ensure_entry(hints, key)
        context_hints = []
        for module in modules:
            if module not in cache:
                cache[module] = _fetch_context_snippet(api_key, module)
            snippet = cache[module]
            if not snippet:
                context_hints.append(
                    {
                        "code": "context7_missing",
                        "message": f"Context7: no snippet returned for '{module}'.",
                    }
                )
                continue
            if snippet.get("error"):
                context_hints.append(
                    {
                        "code": "context7_error",
                        "message": f"Context7: error fetching '{module}': {snippet['error']}.",
                    }
                )
                continue
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


def _collect_third_party_modules(
    sections: list[Any],
    mode: str,
) -> dict[tuple[str, int], set[str]]:
    modules_by_block: dict[tuple[str, int], set[str]] = {}
    stdlib_modules = getattr(sys, "stdlib_module_names", set())

    if mode == "agentic":
        for section in sections:
            for index, block in enumerate(section.blocks):
                if block.type != "python":
                    continue
                modules = _extract_third_party_imports(block.content, stdlib_modules)
                modules_by_block[(section.id, index)] = modules
    else:
        for section in sections:
            matches = list(_PYTHON_FENCE_RE.finditer(section.content_markdown))
            for index, match in enumerate(matches):
                code = match.group(1).rstrip()
                modules = _extract_third_party_imports(code, stdlib_modules)
                modules_by_block[(section.id, index)] = modules

    return modules_by_block


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


def _ensure_entry(hints: list[dict[str, Any]], key: tuple[str, int]) -> dict[str, Any]:
    section_id, block_index = key
    for entry in hints:
        if entry.get("section_id") == section_id and entry.get("block_index") == block_index:
            return entry
    entry = {"section_id": section_id, "block_index": block_index, "hints": []}
    hints.append(entry)
    return entry


def _fetch_context_snippet(api_key: str, module: str) -> dict[str, Any] | None:
    query = f"How to use {module} in Python with examples"
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
