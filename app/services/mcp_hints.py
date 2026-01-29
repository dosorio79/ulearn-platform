"""Shared helpers for advisory Python code hints."""

from __future__ import annotations

import ast
import re
import sys
from typing import Any

_PYTHON_FENCE_RE = re.compile(r"```python\s*\r?\n(.*?)```", re.DOTALL)

_ALLOWED_THIRD_PARTY = {"numpy", "pandas", "scipy"}
_HEAVY_IMPORTS = {"sklearn", "tensorflow", "torch"}
_UNSAFE_IMPORTS = {"os", "subprocess"}
_UNSAFE_CALLS = {"call", "popen", "Popen", "run", "system"}
_RULE_TERMINAL_EXAMPLES = (
    "sum",
    "agg",
    "collect",
    "to_pandas",
    "show",
    "execute",
    "fetchall",
)

_RULE_HINT_TEMPLATES = {
    "expression_result_unused": (
        "Expression result is unused; in scripts it won't display. "
        "Assign it or wrap it in print(...)."
    ),
    "missing_terminal_operation": (
        "Call chain '{chain}' has no terminal operation. "
        "Add a terminal step like {examples}."
    ),
    "suspicious_attribute": (
        "Attribute '{attribute}' looks suspicious or deprecated; verify the API name."
    ),
    "runtime_error": (
        "Runtime error: {error} — {message}."
    ),
}


def inspect_python_code(code: str) -> list[dict[str, str]]:
    hints: list[dict[str, str]] = []
    seen_codes: set[str] = set()

    def add_hint(code_id: str, message: str) -> None:
        if code_id in seen_codes:
            return
        seen_codes.add(code_id)
        hints.append({"code": code_id, "message": message})

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        add_hint("syntax_error", f"Syntax error detected: {exc.msg}.")
        return hints

    if any(len(line) > 100 for line in code.splitlines()):
        add_hint("style_long_line", "Line exceeds 100 characters.")

    imports = _collect_imports(tree)
    stdlib_modules = getattr(sys, "stdlib_module_names", set())

    third_party = {
        module
        for module in imports
        if module not in stdlib_modules and module not in _ALLOWED_THIRD_PARTY
    }
    for module in sorted(third_party):
        add_hint("third_party_import", f"Third-party import '{module}' may be unavailable.")

    for module in sorted(imports & _HEAVY_IMPORTS):
        add_hint("heavy_import", f"Heavy dependency '{module}' may be slow or unavailable.")

    if imports & _UNSAFE_IMPORTS:
        add_hint("unsafe_import", "Potentially unsafe module import detected.")

    saw_apply = False
    saw_unsafe_call = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id in {"eval", "exec"}:
                    saw_unsafe_call = True
            elif isinstance(func, ast.Attribute):
                if func.attr == "apply":
                    saw_apply = True
                if func.attr in _UNSAFE_CALLS:
                    saw_unsafe_call = True

    if saw_unsafe_call:
        add_hint("unsafe_call", "Potentially unsafe system call detected.")

    if saw_apply:
        add_hint("pandas_apply", "Pandas apply can be slow; consider vectorized operations.")

    return hints


def summarize_rule_outcomes(rule_outcomes: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rule_outcomes:
        return None
    counts: dict[str, int] = {}
    total_outcomes = 0
    for entry in rule_outcomes:
        for outcome in entry.get("outcomes", []):
            code_id = outcome.get("code")
            if not code_id:
                continue
            counts[code_id] = counts.get(code_id, 0) + 1
            total_outcomes += 1
    return {
        "blocks_with_outcomes": len(rule_outcomes),
        "total_outcomes": total_outcomes,
        "unique_codes": len(counts),
        "by_code": counts,
    }


def explain_rule_outcomes(rule_outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for entry in rule_outcomes:
        entry_hints: list[dict[str, str]] = []
        for outcome in entry.get("outcomes", []):
            code_id = outcome.get("code")
            context = outcome.get("context") or {}
            template = _RULE_HINT_TEMPLATES.get(code_id)
            if template:
                message = template.format(
                    chain=context.get("chain", "unknown"),
                    attribute=context.get("attribute", "unknown"),
                    error=context.get("error", "Error"),
                    message=context.get("message", "No message"),
                    examples=", ".join(_RULE_TERMINAL_EXAMPLES),
                )
            else:
                message = f"Rule triggered: {code_id}."
            entry_hints.append({"code": code_id, "message": message})
        if entry_hints:
            hints.append(
                {
                    "section_id": entry.get("section_id"),
                    "block_index": entry.get("block_index"),
                    "hints": entry_hints,
                }
            )
    return hints


def collect_hints_from_generated_sections(
    sections: list[Any],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
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

    return hints, _rebuild_summary(hints, python_blocks)


def collect_hints_from_markdown_sections(
    sections: list[Any],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
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

    return hints, _rebuild_summary(hints, python_blocks)


def _collect_imports(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split(".")[0])
    return modules


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
