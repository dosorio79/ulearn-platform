"""Rule engine for advisory Python code hints."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Iterable

_OUTPUT_CALLS = {"print", "display", "show"}
_SUSPICIOUS_ATTRS = {"ix", "as_matrix", "get_value", "set_value", "iteritems"}
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
_TERMINAL_METHODS = {
    "agg",
    "aggregate",
    "collect",
    "count",
    "execute",
    "fetchall",
    "fetchone",
    "fit",
    "mean",
    "predict",
    "show",
    "sum",
    "to_pandas",
    "topandas",
    "to_csv",
    "to_parquet",
}


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
    code: str

    def apply(self, tree: ast.AST, code: str) -> list[RuleOutcome]:
        raise NotImplementedError


class BareExpressionRule(Rule):
    code = "expression_result_unused"

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
            outcomes.append(
                RuleOutcome(
                    code=self.code,
                    context={"node_type": type(stmt.value).__name__},
                    line=getattr(stmt, "lineno", None),
                    col=getattr(stmt, "col_offset", None),
                )
            )
        return outcomes


class SuspiciousAttributeRule(Rule):
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
    code = "missing_terminal_operation"

    def apply(self, tree: ast.AST, code: str) -> list[RuleOutcome]:
        outcomes: list[RuleOutcome] = []
        if not isinstance(tree, ast.Module):
            return outcomes

        for stmt in tree.body:
            if not isinstance(stmt, ast.Expr):
                continue
            if _is_output_call(stmt.value):
                continue
            methods = _extract_call_chain(stmt.value)
            if not methods:
                continue
            lowered = [method.lower() for method in methods]
            if any(method in _TRANSFORM_METHODS for method in lowered) and not any(
                method in _TERMINAL_METHODS for method in lowered
            ):
                outcomes.append(
                    RuleOutcome(
                        code=self.code,
                        context={"chain": " -> ".join(reversed(methods))},
                        line=getattr(stmt, "lineno", None),
                        col=getattr(stmt, "col_offset", None),
                    )
                )
        return outcomes


class RuleEngine:
    def __init__(self, rules: Iterable[Rule] | None = None) -> None:
        self._rules = list(rules) if rules is not None else list(_default_rules())

    def run(self, code: str) -> list[RuleOutcome]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        outcomes: list[RuleOutcome] = []
        for rule in self._rules:
            outcomes.extend(rule.apply(tree, code))
        return _dedupe_outcomes(outcomes)


def _default_rules() -> Iterable[Rule]:
    return (
        BareExpressionRule(),
        MissingTerminalOperationRule(),
        SuspiciousAttributeRule(),
    )


def _is_docstring(stmt: ast.Expr, index: int) -> bool:
    if index != 0:
        return False
    return isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str)


def _is_output_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in _OUTPUT_CALLS
    if isinstance(func, ast.Attribute):
        return func.attr in _OUTPUT_CALLS
    return False


def _extract_call_chain(node: ast.AST) -> list[str]:
    methods: list[str] = []
    current = node
    while isinstance(current, ast.Call):
        func = current.func
        if isinstance(func, ast.Attribute):
            methods.append(func.attr)
            current = func.value
        else:
            break
    return methods


def _dedupe_outcomes(outcomes: list[RuleOutcome]) -> list[RuleOutcome]:
    seen: set[tuple[Any, ...]] = set()
    deduped: list[RuleOutcome] = []
    for outcome in outcomes:
        context_key = tuple(
            (key, _freeze_value(value))
            for key, value in sorted(outcome.context.items())
        )
        key = (outcome.code, outcome.line, outcome.col, context_key)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(outcome)
    return deduped


def _freeze_value(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze_value(v)) for k, v in value.items()))
    return value
