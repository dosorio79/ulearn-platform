"""Rule engine for advisory Python code hints.

This module provides deterministic, AST-based heuristics to detect
common Python code usage issues. All rules are advisory: they never
raise, never block generation, and never execute code.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Iterable


# Functions that produce visible output in the execution environment
_OUTPUT_CALLS = {"print", "display", "show"}

# Deprecated / suspicious attributes seen across common data libraries
_SUSPICIOUS_ATTRS = {"ix", "as_matrix", "get_value", "set_value", "iteritems"}

# Methods typically used to transform data but not execute it
_TRANSFORM_METHODS = {
    "groupby",
    "select",
    "filter",
    "where",
    "join",
    "withcolumn",
    "map",
    "apply",
}

# Methods that usually trigger execution / materialization
_EXECUTION_TERMINALS = {
    "collect",
    "execute",
    "fetchall",
    "fetchone",
    "show",
    "to_pandas",
    "topandas",
    "to_csv",
    "to_parquet",
}

# Aggregations that may look terminal but are often lazy / non-executing
_AGGREGATION_METHODS = {
    "agg",
    "aggregate",
    "count",
    "fit",
    "mean",
    "predict",
    "sum",
}


# ----------------------------
# Core data structures
# ----------------------------

@dataclass(frozen=True)
class RuleOutcome:
    code: str
    context: dict[str, Any]
    line: int | None = None
    col: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "context": self.context,
            "line": self.line,
            "col": self.col,
        }


class Rule:
    """Base class for all advisory rules."""

    code: str

    def apply(self, tree: ast.AST, code: str) -> list[RuleOutcome]:
        raise NotImplementedError


# ----------------------------
# Rules
# ----------------------------

class BareExpressionRule(Rule):
    """Detect expressions whose result is neither used nor shown."""

    code = "expression_result_unused"
    _correction_intent = "add_visible_output"

    def apply(self, tree: ast.AST, code: str) -> list[RuleOutcome]:
        outcomes: list[RuleOutcome] = []

        if not isinstance(tree, ast.Module):
            return outcomes

        for index, stmt in enumerate(tree.body):
            if not isinstance(stmt, ast.Expr):
                continue
            if _is_docstring(stmt, index):
                continue
            if _is_output_call(stmt.value):
                continue
            expression_source = ast.get_source_segment(code, stmt.value) or ""

            outcomes.append(
                RuleOutcome(
                    code=self.code,
                    context={
                        "node_type": type(stmt.value).__name__,
                        "expression_source": expression_source.strip(),
                        "correction_intent": self._correction_intent,
                    },
                    line=getattr(stmt, "lineno", None),
                    col=getattr(stmt, "col_offset", None),
                )
            )

        return outcomes


class SuspiciousAttributeRule(Rule):
    """Detect deprecated or suspicious attribute usage."""

    code = "suspicious_attribute"

    def apply(self, tree: ast.AST, code: str) -> list[RuleOutcome]:
        outcomes: list[RuleOutcome] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute):
                continue
            if node.attr not in _SUSPICIOUS_ATTRS:
                continue

            outcomes.append(
                RuleOutcome(
                    code=self.code,
                    context={"attribute": node.attr},
                    line=getattr(node, "lineno", None),
                    col=getattr(node, "col_offset", None),
                )
            )

        return outcomes


class MissingTerminalOperationRule(Rule):
    """Detect transformation or aggregation chains without execution."""

    code = "missing_terminal_operation"
    _correction_intent = "add_execution_step"

    def apply(self, tree: ast.AST, code: str) -> list[RuleOutcome]:
        outcomes: list[RuleOutcome] = []

        if not isinstance(tree, ast.Module):
            return outcomes

        for stmt in tree.body:
            if not isinstance(stmt, ast.Expr):
                continue
            if _is_output_call(stmt.value):
                continue

            methods = _extract_attribute_chain(stmt.value)
            if not methods:
                continue

            lowered = [m.lower() for m in methods]

            has_transform = any(m in _TRANSFORM_METHODS for m in lowered)
            has_aggregation = any(m in _AGGREGATION_METHODS for m in lowered)
            has_execution = any(m in _EXECUTION_TERMINALS for m in lowered)

            if (has_transform or has_aggregation) and not has_execution:
                outcomes.append(
                    RuleOutcome(
                        code=self.code,
                        context={
                            "chain": " -> ".join(methods),
                            "correction_intent": self._correction_intent,
                        },
                        line=getattr(stmt, "lineno", None),
                        col=getattr(stmt, "col_offset", None),
                    )
                )

        return outcomes


class NoOutputRule(Rule):
    """Detect code blocks that never produce visible output."""

    code = "no_output"
    _correction_intent = "add_visible_output"

    def apply(self, tree: ast.AST, code: str) -> list[RuleOutcome]:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name) and func.id in _OUTPUT_CALLS:
                return []
            if isinstance(func, ast.Attribute) and func.attr in _OUTPUT_CALLS:
                return []
        return [
            RuleOutcome(
                code=self.code,
                context={"correction_intent": self._correction_intent},
                line=None,
                col=None,
            )
        ]


# ----------------------------
# Engine
# ----------------------------

class RuleEngine:
    """Applies a set of advisory rules to Python source code."""

    def __init__(self, rules: Iterable[Rule] | None = None) -> None:
        self._rules = list(rules) if rules is not None else list(_default_rules())

    def run(self, code: str) -> list[RuleOutcome]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Hard validation already failed upstream
            return []

        outcomes: list[RuleOutcome] = []
        for rule in self._rules:
            outcomes.extend(rule.apply(tree, code))

        outcomes = _attach_correction_suggestions(outcomes)
        outcomes = _apply_precedence(outcomes)
        return _dedupe_outcomes(outcomes)


def _default_rules() -> Iterable[Rule]:
    return (
        BareExpressionRule(),
        MissingTerminalOperationRule(),
        NoOutputRule(),
        SuspiciousAttributeRule(),
    )


# ----------------------------
# Helpers
# ----------------------------

def _is_docstring(stmt: ast.Expr, index: int) -> bool:
    return (
        index == 0
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    )


def _is_output_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False

    func = node.func
    if isinstance(func, ast.Name):
        return func.id in _OUTPUT_CALLS
    if isinstance(func, ast.Attribute):
        return func.attr in _OUTPUT_CALLS

    return False


def _extract_attribute_chain(node: ast.AST) -> list[str]:
    """Extract chained attribute names from a call or attribute expression."""

    methods: list[str] = []
    current = node

    while True:
        if isinstance(current, ast.Call):
            current = current.func
            continue
        if isinstance(current, ast.Attribute):
            methods.append(current.attr)
            current = current.value
            continue
        if isinstance(current, ast.Subscript):
            current = current.value
            continue
        break

    methods.reverse()
    return methods


def _apply_precedence(outcomes: list[RuleOutcome]) -> list[RuleOutcome]:
    """Suppress lower-value hints when higher-value ones fire on the same line."""

    suppress_lines = {
        o.line
        for o in outcomes
        if o.code == "missing_terminal_operation" and o.line is not None
    }

    if not suppress_lines:
        return outcomes

    filtered: list[RuleOutcome] = []
    for outcome in outcomes:
        if (
            outcome.code == "expression_result_unused"
            and outcome.line in suppress_lines
        ):
            continue
        filtered.append(outcome)

    return filtered


def _dedupe_outcomes(outcomes: list[RuleOutcome]) -> list[RuleOutcome]:
    seen: set[tuple[Any, ...]] = set()
    deduped: list[RuleOutcome] = []

    for outcome in outcomes:
        context_key = tuple(
            (k, _freeze_value(v))
            for k, v in sorted(outcome.context.items())
        )
        key = (outcome.code, outcome.line, outcome.col, context_key)

        if key in seen:
            continue

        seen.add(key)
        deduped.append(outcome)

    return deduped


def _attach_correction_suggestions(outcomes: list[RuleOutcome]) -> list[RuleOutcome]:
    updated: list[RuleOutcome] = []
    for outcome in outcomes:
        intent = outcome.context.get("correction_intent")
        if intent == "add_visible_output":
            expression = outcome.context.get("expression_source", "")
            if expression:
                context = dict(outcome.context)
                context["correction_suggestions"] = [
                    {
                        "intent": intent,
                        "suggested_code": f"print({expression})",
                    }
                ]
                outcome = RuleOutcome(
                    code=outcome.code,
                    context=context,
                    line=outcome.line,
                    col=outcome.col,
                )
        updated.append(outcome)
    return updated


def _freeze_value(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze_value(v)) for k, v in value.items()))
    return value
