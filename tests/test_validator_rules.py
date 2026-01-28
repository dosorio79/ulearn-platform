import pytest

from app.agents.validator_rules import RuleEngine

pytestmark = pytest.mark.unit


def test_rule_engine_flags_expression_result_unused():
    engine = RuleEngine()
    outcomes = engine.run("2 + 2\n")
    codes = {outcome.code for outcome in outcomes}
    assert "expression_result_unused" in codes


def test_rule_engine_flags_missing_terminal_operation():
    engine = RuleEngine()
    outcomes = engine.run("df.groupby('a')\n")
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
