import pytest

from app.agents.mcp_tools import invoke_tool
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
