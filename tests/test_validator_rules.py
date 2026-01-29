import pytest

from app.agents.validator_rules import RuleEngine
from app.agents.validator import ValidatorAgent
from app.models.agents import ContentBlock, GeneratedSection

pytestmark = pytest.mark.unit


def test_rule_engine_flags_expression_result_unused():
    engine = RuleEngine()
    outcomes = engine.run("2 + 2\n")
    codes = {outcome.code for outcome in outcomes}
    assert "expression_result_unused" in codes
    assert "no_output" in codes
    suggestions = [
        suggestion
        for outcome in outcomes
        for suggestion in outcome.context.get("correction_suggestions", [])
    ]
    assert any(suggestion["intent"] == "add_visible_output" for suggestion in suggestions)


def test_rule_engine_flags_missing_terminal_operation():
    engine = RuleEngine()
    outcomes = engine.run("df.groupby('a')\n")
    codes = {outcome.code for outcome in outcomes}
    assert "missing_terminal_operation" in codes


def test_rule_engine_flags_aggregation_without_execution_terminal():
    engine = RuleEngine()
    outcomes = engine.run("df.groupby('a').sum()\n")
    codes = {outcome.code for outcome in outcomes}
    assert "missing_terminal_operation" in codes


def test_rule_engine_flags_suspicious_attribute():
    engine = RuleEngine()
    outcomes = engine.run("df.ix[0]\n")
    codes = {outcome.code for outcome in outcomes}
    assert "suspicious_attribute" in codes


def test_rule_engine_allows_printed_terminal_operation():
    engine = RuleEngine()
    outcomes = engine.run("print(df.groupby('a').sum())\n")
    assert outcomes == []


def test_rule_engine_handles_multiline_chain():
    engine = RuleEngine()
    code = "(df.groupby('a')\n    .select('b')\n)"
    outcomes = engine.run(code)
    codes = {outcome.code for outcome in outcomes}
    assert "missing_terminal_operation" in codes


def test_rule_engine_suppresses_expression_hint_when_terminal_missing():
    engine = RuleEngine()
    outcomes = engine.run("df.groupby('a')\n")
    codes = {outcome.code for outcome in outcomes}
    assert "expression_result_unused" not in codes


def test_rule_engine_flags_no_output_without_print():
    engine = RuleEngine()
    outcomes = engine.run("x = 1\n")
    codes = {outcome.code for outcome in outcomes}
    assert "no_output" in codes


def test_validator_runtime_smoke_test_flags_exception():
    validator = ValidatorAgent(runtime_smoke_test_enabled=True, runtime_smoke_test_timeout=0.1)
    sections = [
        GeneratedSection(
            id="concept",
            title="Concept",
            minutes=5,
            blocks=[ContentBlock(type="python", content="1 / 0")],
        )
    ]
    outcomes = validator.collect_rule_outcomes(sections)
    codes = {
        outcome["code"]
        for entry in outcomes
        for outcome in entry.get("outcomes", [])
    }
    assert "runtime_error" in codes
