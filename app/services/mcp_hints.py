"""MCP-style advisory hints for Python code blocks."""

from __future__ import annotations

import ast
import re
import sys
from typing import Any, Sequence

from app.models.agents import GeneratedSection
from app.models.api import LessonSection

_PYTHON_FENCE_RE = re.compile(r"```python\s*\r?\n(.*?)```", re.DOTALL)

_UNSAFE_MODULES = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
}
_UNSAFE_CALLS = {
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
}
_ALLOWED_THIRD_PARTY = {"pandas", "numpy", "scipy"}
_HEAVY_LIBS = {
    "sklearn",
    "torch",
    "tensorflow",
}
_DEFAULT_STDLIB = {
    "argparse",
    "collections",
    "datetime",
    "functools",
    "itertools",
    "json",
    "math",
    "pathlib",
    "random",
    "re",
    "statistics",
    "string",
    "typing",
}
_LINE_LENGTH_LIMIT = 100


def inspect_python_code(code: str) -> list[dict[str, str]]:
    """Return advisory hints for syntax and safety issues."""
    hints: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    stdlib_modules = getattr(sys, "stdlib_module_names", _DEFAULT_STDLIB)

    def add_hint(code_id: str, message: str) -> None:
        key = (code_id, message)
        if key in seen:
            return
        seen.add(key)
        hints.append({"code": code_id, "message": message})

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        location = f"line {exc.lineno}, column {exc.offset}" if exc.lineno else "unknown location"
        add_hint("syntax_error", f"SyntaxError: {exc.msg} ({location}).")
        return hints

    saw_output = False
    saw_apply = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                if module in _UNSAFE_MODULES:
                    add_hint(
                        "unsafe_import",
                        f"Import of '{module}' may not be supported in the browser runtime.",
                    )
                if module in _ALLOWED_THIRD_PARTY:
                    continue
                if module in _HEAVY_LIBS:
                    add_hint(
                        "heavy_import",
                        f"Import of '{module}' may be heavy for a quick demo snippet.",
                    )
                elif module not in stdlib_modules:
                    add_hint(
                        "third_party_import",
                        f"Import of '{module}' may require extra dependencies.",
                    )
        elif isinstance(node, ast.ImportFrom):
            if not node.module:
                continue
            module = node.module.split(".")[0]
            if module in _UNSAFE_MODULES:
                add_hint(
                    "unsafe_import",
                    f"Import from '{module}' may not be supported in the browser runtime.",
                )
            if module in _ALLOWED_THIRD_PARTY:
                continue
            if module in _HEAVY_LIBS:
                add_hint(
                    "heavy_import",
                    f"Import from '{module}' may be heavy for a quick demo snippet.",
                )
            elif module not in stdlib_modules:
                add_hint(
                    "third_party_import",
                    f"Import from '{module}' may require extra dependencies.",
                )
        elif isinstance(node, ast.Call):
            func_name = _get_call_name(node.func)
            if not func_name:
                continue
            if func_name in _UNSAFE_CALLS:
                add_hint(
                    "unsafe_call",
                    f"Use of '{func_name}' is discouraged in lesson snippets.",
                )
            root = func_name.split(".")[0]
            if root in _UNSAFE_MODULES:
                add_hint(
                    "unsafe_call",
                    f"Call to '{func_name}' may not be supported in the browser runtime.",
                )
            if func_name == "print" or func_name.endswith(".display") or func_name == "display":
                saw_output = True
            if func_name.endswith(".apply"):
                saw_apply = True

    if not saw_output:
        add_hint(
            "no_output",
            "Snippet does not print or display output; consider adding print(...) for clarity.",
        )
    if saw_apply:
        add_hint(
            "pandas_apply",
            "Using DataFrame.apply can be slow on large data; prefer vectorized operations.",
        )

    for line in code.splitlines():
        if len(line) > _LINE_LENGTH_LIMIT:
            add_hint(
                "style_long_line",
                f"Line exceeds {_LINE_LENGTH_LIMIT} characters; consider wrapping for readability.",
            )
            break

    return hints




def collect_hints_from_generated_sections(
    sections: Sequence[GeneratedSection],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Collect MCP hints from generated sections."""
    hints: list[dict[str, Any]] = []
    python_blocks = 0
    for section in sections:
        for index, block in enumerate(section.blocks):
            if block.type != "python":
                continue
            python_blocks += 1
            block_hints = inspect_python_code(block.content)
            if block_hints:
                hints.append(
                    {
                        "section_id": section.id,
                        "block_index": index,
                        "hints": block_hints,
                    }
                )

    summary = _build_summary(python_blocks, hints)
    return hints, summary


def collect_hints_from_markdown_sections(
    sections: Sequence[LessonSection],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Collect MCP hints from markdown sections (static/demo mode)."""
    hints: list[dict[str, Any]] = []
    python_blocks = 0
    for section in sections:
        matches = list(_PYTHON_FENCE_RE.finditer(section.content_markdown))
        for index, match in enumerate(matches):
            python_blocks += 1
            code = match.group(1).rstrip()
            block_hints = inspect_python_code(code)
            if block_hints:
                hints.append(
                    {
                        "section_id": section.id,
                        "block_index": index,
                        "hints": block_hints,
                    }
                )

    summary = _build_summary(python_blocks, hints)
    return hints, summary


def _get_call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _get_call_name(node.value)
        if base:
            return f"{base}.{node.attr}"
        return node.attr
    return None


def _build_summary(
    python_blocks: int,
    hints: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    if python_blocks == 0:
        return None
    hint_count = sum(len(entry.get("hints", [])) for entry in hints)
    return {
        "python_blocks": python_blocks,
        "blocks_with_hints": len(hints),
        "total_hints": hint_count,
    }
