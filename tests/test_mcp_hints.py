import pytest

from app.agents.mcp_tools import invoke_tool
from app.core import config
from app.mcp import python_code_hints
from app.models.agents import ContentBlock, GeneratedSection
from app.mcp import python_code_hints  # noqa: F401
from app.services.mcp_hints import collect_hints_from_generated_sections, inspect_python_code

pytestmark = pytest.mark.unit


def test_inspect_python_code_flags_syntax_error():
    hints = inspect_python_code("def broken(:\n    pass")
    codes = {hint["code"] for hint in hints}
    assert "syntax_error" in codes


def test_inspect_python_code_flags_unsafe_import_and_call():
    hints = inspect_python_code("import os\nos.system('ls')\n")
    codes = {hint["code"] for hint in hints}
    assert "unsafe_import" in codes
    assert "unsafe_call" in codes
    assert "no_output" in codes


def test_collect_hints_from_generated_sections_summary():
    sections = [
        GeneratedSection(
            id="example",
            title="Example",
            minutes=5,
            blocks=[
                ContentBlock(type="python", content="import os\nos.system('ls')\n"),
            ],
        )
    ]

    hints, summary = collect_hints_from_generated_sections(sections)

    assert summary is not None
    assert summary["python_blocks"] == 1
    assert summary["blocks_with_hints"] == 1
    assert summary["total_hints"] >= 2
    assert hints


def test_collect_hints_invokes_mcp_tool():
    sections = [
        GeneratedSection(
            id="example",
            title="Example",
            minutes=5,
            blocks=[
                ContentBlock(type="python", content="print('ok')\n"),
            ],
        )
    ]

    hints, summary = invoke_tool(
        "python_code_hints",
        {"mode": "agentic", "sections": sections},
    )

    assert hints == []
    assert summary is not None


def test_filter_mcp_hints_excludes_environment_codes():
    from app.services.lesson_service import _filter_mcp_hints

    hints = [
        {
            "section_id": "example",
            "block_index": 0,
            "hints": [
                {"code": "third_party_import", "message": "env"},
                {"code": "no_output", "message": "learner"},
            ],
        }
    ]

    learner, environment = _filter_mcp_hints(hints)

    assert learner
    assert environment
    learner_codes = {hint["code"] for hint in learner[0]["hints"]}
    environment_codes = {hint["code"] for hint in environment[0]["hints"]}
    assert "no_output" in learner_codes
    assert "third_party_import" in environment_codes


def test_collect_hints_accepts_rule_outcomes():
    sections = [
        GeneratedSection(
            id="example",
            title="Example",
            minutes=5,
            blocks=[
                ContentBlock(type="python", content="print('ok')\n"),
            ],
        )
    ]
    rule_outcomes = [
        {
            "section_id": "example",
            "block_index": 0,
            "outcomes": [
                {
                    "code": "expression_result_unused",
                    "context": {},
                    "line": 1,
                    "col": 0,
                }
            ],
        }
    ]

    hints, summary = invoke_tool(
        "python_code_hints",
        {"mode": "agentic", "sections": sections, "rule_outcomes": rule_outcomes},
    )

    assert summary is not None
    hint_codes = {
        hint["code"]
        for entry in hints
        for hint in entry.get("hints", [])
    }
    assert "expression_result_unused" in hint_codes


def test_collect_hints_does_not_mutate_blocks():
    section = GeneratedSection(
        id="example",
        title="Example",
        minutes=5,
        blocks=[
            ContentBlock(type="python", content="print('ok')\n"),
        ],
    )

    _ = collect_hints_from_generated_sections([section])

    assert section.blocks[0].content == "print('ok')\n"


def test_inspect_python_code_flags_no_output():
    hints = inspect_python_code("x = 1\n")
    codes = {hint["code"] for hint in hints}
    assert "no_output" in codes


def test_inspect_python_code_flags_long_line():
    hints = inspect_python_code("x = '" + ("a" * 120) + "'\n")
    codes = {hint["code"] for hint in hints}
    assert "style_long_line" in codes


def test_inspect_python_code_flags_pandas_apply():
    hints = inspect_python_code("df.apply(lambda x: x)\n")
    codes = {hint["code"] for hint in hints}
    assert "pandas_apply" in codes


def test_inspect_python_code_flags_third_party_import():
    hints = inspect_python_code("import requests\n")
    codes = {hint["code"] for hint in hints}
    assert "third_party_import" in codes


def test_inspect_python_code_flags_heavy_import():
    hints = inspect_python_code("import tensorflow\n")
    codes = {hint["code"] for hint in hints}
    assert "heavy_import" in codes


def test_context7_hint_appended_when_enabled(monkeypatch):
    monkeypatch.setattr(config, "CONTEXT7_API_KEY", "ctx7sk-test")

    def fake_fetch_context_snippets(*, api_key, library_name, query):
        assert api_key == "ctx7sk-test"
        assert library_name == "requests"
        return [
            {"title": "Requests Quickstart", "content": "Use requests.get", "source": "requests.readthedocs.io"}
        ]

    monkeypatch.setattr(python_code_hints, "fetch_context_snippets", fake_fetch_context_snippets)

    sections = [
        GeneratedSection(
            id="example",
            title="Example",
            minutes=5,
            blocks=[
                ContentBlock(type="python", content="import requests\nrequests.get('https://example.com')\n"),
            ],
        )
    ]

    hints, summary = invoke_tool(
        "python_code_hints",
        {"mode": "agentic", "sections": sections},
    )

    assert summary is not None
    assert hints
    summary_entries = [entry for entry in hints if entry.get("section_id") is None]
    assert summary_entries
    hint_codes = {hint["code"] for hint in summary_entries[0]["hints"]}
    assert "context7_reference" in hint_codes


def test_context7_hint_added_for_allowed_third_party_import(monkeypatch):
    monkeypatch.setattr(config, "CONTEXT7_API_KEY", "ctx7sk-test")

    def fake_fetch_context_snippets(*, api_key, library_name, query):
        assert api_key == "ctx7sk-test"
        assert library_name == "pandas"
        return [
            {"title": "Pandas Basics", "content": "Use DataFrame", "source": "pandas.pydata.org"}
        ]

    monkeypatch.setattr(python_code_hints, "fetch_context_snippets", fake_fetch_context_snippets)

    sections = [
        GeneratedSection(
            id="example",
            title="Example",
            minutes=5,
            blocks=[
                ContentBlock(type="python", content="import pandas as pd\nprint('ok')\n"),
            ],
        )
    ]

    hints, summary = invoke_tool(
        "python_code_hints",
        {"mode": "agentic", "sections": sections},
    )

    assert summary is not None
    assert hints
    summary_entries = [entry for entry in hints if entry.get("section_id") is None]
    assert summary_entries
    hint_codes = {hint["code"] for hint in summary_entries[0]["hints"]}
    assert "context7_reference" in hint_codes


def test_context7_missing_hint_when_no_snippet(monkeypatch):
    monkeypatch.setattr(config, "CONTEXT7_API_KEY", "ctx7sk-test")

    def fake_fetch_context_snippets(*, api_key, library_name, query):
        return []

    monkeypatch.setattr(python_code_hints, "fetch_context_snippets", fake_fetch_context_snippets)

    sections = [
        GeneratedSection(
            id="example",
            title="Example",
            minutes=5,
            blocks=[
                ContentBlock(type="python", content="import duckdb\nprint('ok')\n"),
            ],
        )
    ]

    hints, _ = invoke_tool(
        "python_code_hints",
        {"mode": "agentic", "sections": sections},
    )

    summary_entries = [entry for entry in hints if entry.get("section_id") is None]
    assert not summary_entries


def test_context7_error_hint_on_exception(monkeypatch):
    monkeypatch.setattr(config, "CONTEXT7_API_KEY", "ctx7sk-test")

    def fake_fetch_context_snippets(*, api_key, library_name, query):
        raise RuntimeError("boom")

    monkeypatch.setattr(python_code_hints, "fetch_context_snippets", fake_fetch_context_snippets)

    sections = [
        GeneratedSection(
            id="example",
            title="Example",
            minutes=5,
            blocks=[
                ContentBlock(type="python", content="import duckdb\nprint('ok')\n"),
            ],
        )
    ]

    hints, _ = invoke_tool(
        "python_code_hints",
        {"mode": "agentic", "sections": sections},
    )

    summary_entries = [entry for entry in hints if entry.get("section_id") is None]
    assert summary_entries
    hint_codes = {hint["code"] for hint in summary_entries[0]["hints"]}
    assert "context7_error" in hint_codes
