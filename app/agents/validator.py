"""Validator agent for lesson structure and content rules."""

import ast
import signal
import threading
from typing import Dict, List

from app.core import config
from app.models.agents import GeneratedSection, ContentBlock
from app.agents.validator_rules import RuleEngine, RuleOutcome


class ValidatorAgent:
    """
    Validates generated lesson sections before rendering and delivery.
    """
    # Constants
    TARGET_TOTAL_MINUTES = 15
    MIN_SECTION_MINUTES = 3
    MIN_SECTION_COUNT = 1
    MAX_SECTION_COUNT = 3

    ALLOWED_SECTION_IDS = {"concept", "example", "exercise"}
    REQUIRED_SECTION_IDS = {"concept", "example", "exercise"}
    ALLOWED_BLOCK_TYPES = {"text", "python", "exercise"}
    MAX_PYTHON_LINES = 30
    JSON_LESSON_KEYS = {"objective", "sections"}
    JSON_SECTION_KEYS = {"id", "title", "minutes", "blocks"}
    JSON_BLOCK_KEYS = {"type", "content"}

    def __init__(
        self,
        rule_engine: RuleEngine | None = None,
        *,
        runtime_smoke_test_enabled: bool | None = None,
        runtime_smoke_test_timeout: float | None = None,
    ) -> None:
        self._rule_engine = rule_engine or RuleEngine()
        self._runtime_smoke_test_enabled = (
            config.RUNTIME_SMOKE_TEST_ENABLED
            if runtime_smoke_test_enabled is None
            else runtime_smoke_test_enabled
        )
        self._runtime_smoke_test_timeout = (
            config.RUNTIME_SMOKE_TEST_TIMEOUT_SECONDS
            if runtime_smoke_test_timeout is None
            else runtime_smoke_test_timeout
        )

    def validate(
        self,
        sections: List[GeneratedSection],
        *,
        strict_minutes: bool = False,
    ) -> List[GeneratedSection]:
        # Structural checks
        if not sections:
            raise ValueError("Lesson must include at least one section.")

        if not (self.MIN_SECTION_COUNT <= len(sections) <= self.MAX_SECTION_COUNT):
            raise ValueError(
                f"Lesson must include {self.MIN_SECTION_COUNT}-{self.MAX_SECTION_COUNT} sections."
            )

        section_ids = [section.id for section in sections]
        if len(set(section_ids)) != len(section_ids):
            raise ValueError("Section IDs must be unique.")

        if any(section.id not in self.ALLOWED_SECTION_IDS for section in sections):
            raise ValueError(
                f"Section IDs must be one of {sorted(self.ALLOWED_SECTION_IDS)}."
            )
        if set(section_ids) != self.REQUIRED_SECTION_IDS:
            raise ValueError("Lesson must include concept, example, and exercise sections.")

        python_block_found = False

        # Per-section checks
        for section in sections:
            if section.minutes < self.MIN_SECTION_MINUTES:
                raise ValueError(
                    f"Section '{section.id}' must be at least {self.MIN_SECTION_MINUTES} minutes."
                )

            if not section.blocks:
                raise ValueError(f"Section '{section.id}' must include at least one block.")

            for block in section.blocks:
                self._validate_block(block)
                if block.type == "python":
                    python_block_found = True

        if not python_block_found:
            raise ValueError("Lesson must include at least one python block.")

        # Time validation
        total_minutes = sum(section.minutes for section in sections)

        if strict_minutes and total_minutes != self.TARGET_TOTAL_MINUTES:
            raise ValueError("Total lesson duration must equal 15 minutes.")

        if total_minutes == self.TARGET_TOTAL_MINUTES:
            return sections

        # Ensure the minimum minutes constraint is feasible before scaling
        if self.MIN_SECTION_MINUTES * len(sections) > self.TARGET_TOTAL_MINUTES:
            raise ValueError("Minimum section length exceeds total lesson time.")

        adjustment_factor = self.TARGET_TOTAL_MINUTES / total_minutes
        adjusted_sections = []
        accumulated_minutes = 0

        for i, section in enumerate(sections):
            if i == len(sections) - 1:
                adjusted_minutes = self.TARGET_TOTAL_MINUTES - accumulated_minutes
            else:
                adjusted_minutes = max(
                    self.MIN_SECTION_MINUTES,
                    round(section.minutes * adjustment_factor),
                )
                accumulated_minutes += adjusted_minutes
            if i == len(sections) - 1 and adjusted_minutes < self.MIN_SECTION_MINUTES:
                raise ValueError("Minimum section length exceeds total lesson time.")
            adjusted_sections.append(
                GeneratedSection(
                    id=section.id,
                    title=section.title,
                    minutes=adjusted_minutes,
                    blocks=section.blocks,
                )
            )

        return adjusted_sections

    def validate_json_only_response(self, payload: Dict) -> None:
        """Validate a JSON-only lesson response with strict keys."""
        if not isinstance(payload, dict):
            raise ValueError("Lesson payload must be a JSON object.")
        if set(payload.keys()) != self.JSON_LESSON_KEYS:
            raise ValueError("Lesson JSON must not include extra keys.")

        sections = payload.get("sections")
        if not isinstance(sections, list):
            raise ValueError("Lesson sections must be a list.")
        section_ids = [section.get("id") for section in sections if isinstance(section, dict)]
        if set(section_ids) != self.REQUIRED_SECTION_IDS:
            raise ValueError("Lesson must include concept, example, and exercise sections.")

        for section in sections:
            if not isinstance(section, dict):
                raise ValueError("Lesson section must be a JSON object.")
            if set(section.keys()) != self.JSON_SECTION_KEYS:
                raise ValueError("Section JSON must not include extra keys.")
            blocks = section.get("blocks")
            if not isinstance(blocks, list) or not blocks:
                raise ValueError("Section must include at least one block.")
            for block in blocks:
                if not isinstance(block, dict):
                    raise ValueError("Block must be a JSON object.")
                if set(block.keys()) != self.JSON_BLOCK_KEYS:
                    raise ValueError("Block JSON must not include extra keys.")
                if block.get("type") not in {"text", "python", "exercise"}:
                    raise ValueError("Block type must be text, python, or exercise.")
                if not block.get("content"):
                    raise ValueError("Block content must be non-empty.")

    def _validate_block(self, block: ContentBlock) -> None:
        if block.type not in self.ALLOWED_BLOCK_TYPES:
            raise ValueError(
                f"Block type must be one of {sorted(self.ALLOWED_BLOCK_TYPES)}."
            )

        if not block.content or not block.content.strip():
            raise ValueError("Block content must be non-empty.")

        if ":::exercise" in block.content or "::: " in block.content:
            raise ValueError("Block content must not include :::exercise markers.")

        if block.type == "python":
            self._validate_python_block(block.content)
        if block.type == "exercise":
            self._validate_exercise_block(block.content)
        if block.type == "text":
            self._validate_text_formatting(block.content)

    def collect_rule_outcomes(self, sections: List[GeneratedSection]) -> list[dict]:
        outcomes: list[dict] = []
        for section in sections:
            for index, block in enumerate(section.blocks):
                if block.type != "python":
                    continue
                rule_outcomes = self._rule_engine.run(block.content)
                if self._runtime_smoke_test_enabled:
                    rule_outcomes.extend(self._runtime_smoke_test(block.content))
                if not rule_outcomes:
                    continue
                outcomes.append(
                    {
                        "section_id": section.id,
                        "block_index": index,
                        "outcomes": [outcome.to_dict() for outcome in rule_outcomes],
                    }
                )
        return outcomes

    def _runtime_smoke_test(self, code: str) -> list[RuleOutcome]:
        """Best-effort runtime smoke test that captures exceptions only."""
        timeout_seconds = max(self._runtime_smoke_test_timeout, 0.0)

        if threading.current_thread() is not threading.main_thread():
            return []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        if _contains_imports(tree):
            return []

        def _timeout_handler(*_args: object) -> None:
            raise TimeoutError("Execution timed out.")

        safe_builtins = {
            "print": lambda *_args, **_kwargs: None,
            "range": range,
            "len": len,
            "min": min,
            "max": max,
            "sum": sum,
            "abs": abs,
            "enumerate": enumerate,
            "zip": zip,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "map": map,
            "filter": filter,
        }

        globals_dict = {"__builtins__": safe_builtins}
        locals_dict: dict[str, object] = {}

        previous_handler = None
        signal_armed = False
        try:
            if timeout_seconds > 0:
                try:
                    previous_handler = signal.getsignal(signal.SIGALRM)
                    signal.signal(signal.SIGALRM, _timeout_handler)
                    signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
                    signal_armed = True
                except (AttributeError, ValueError, OSError):
                    return []
            exec(code, globals_dict, locals_dict)
        except Exception as exc:  # noqa: BLE001 - advisory smoke test only
            return [
                RuleOutcome(
                    code="runtime_error",
                    context={
                        "error": type(exc).__name__,
                        "message": str(exc),
                        "correction_intent": "inspect_runtime_error",
                    },
                    line=None,
                    col=None,
                )
            ]
        finally:
            if timeout_seconds > 0 and signal_armed:
                signal.setitimer(signal.ITIMER_REAL, 0)
                if previous_handler is not None:
                    signal.signal(signal.SIGALRM, previous_handler)

        return []

    def _validate_python_block(self, code: str) -> None:
        # 1. Syntax validation (non-negotiable).
        try:
            ast.parse(code)
        except SyntaxError as exc:
            raise ValueError("Python block must contain valid syntax.") from exc

        # 2. Size guardrail.
        lines = [line for line in code.splitlines() if line.strip()]
        if len(lines) > self.MAX_PYTHON_LINES:
            raise ValueError("Python block must be short and focused.")

        # 3. Visible output requirement (explicit, frontend-safe).
        if "print(" not in code:
            raise ValueError(
                "Python block must produce visible output using print(...)."
            )

        # 4. Heuristic import checks (intentionally limited).
        self._check_required_imports(code)

    def _check_required_imports(self, code: str) -> None:
        """Heuristic checks for common standard library and data-science imports."""
        checks = {
            # Data science.
            "pd.": ("import pandas as pd", "from pandas import"),
            "np.": ("import numpy as np", "from numpy import"),
            "plt.": ("import matplotlib.pyplot as plt", "from matplotlib import"),
            # Performance.
            "timeit.": ("import timeit", "from timeit import"),
            "time.": ("import time", "from time import"),
            # Math / stats.
            "math.": ("import math",),
            "statistics.": ("import statistics", "from statistics import"),
            # Randomness.
            "random.": ("import random", "from random import"),
            # Collections.
            "Counter(": ("from collections import Counter",),
            "defaultdict(": ("from collections import defaultdict",),
        }

        for symbol, required_imports in checks.items():
            if symbol in code and not any(req in code for req in required_imports):
                raise ValueError(
                    f"Missing import for symbol '{symbol}'. "
                    "Each python block must be self-contained."
                )

    def _validate_exercise_block(self, content: str) -> None:
        if "```" in content or ":::exercise" in content:
            raise ValueError("Exercise blocks must be plain text only.")

    def _validate_text_formatting(self, content: str) -> None:
        has_paragraph = "\n\n" in content
        has_bullet = "\n- " in content or "\n* " in content
        has_numbered = "\n1. " in content
        if not has_paragraph or not (has_bullet or has_numbered):
            raise ValueError(
                "Text blocks must include a paragraph and a bullet or numbered list."
            )


def _contains_imports(tree: ast.AST) -> bool:
    return any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree))
