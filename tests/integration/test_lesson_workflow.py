import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core import config
from app.services import mongo
from app.services import lesson_service

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("static_mode", [True, False])
def test_lesson_endpoint_records_mcp_summary(monkeypatch, static_mode):
    monkeypatch.setattr(config, "STATIC_LESSON_MODE", static_mode)
    monkeypatch.setattr(config, "TELEMETRY_BACKEND", "memory")
    mongo.reset_memory_store()

    client = TestClient(app)
    response = client.post(
        "/lesson",
        json={"topic": "Pandas groupby performance", "level": "beginner"},
    )

    assert response.status_code == 200
    runs = mongo.get_memory_runs()
    assert runs
    assert "mcp_summary" in runs[-1]


def test_lesson_endpoint_records_rule_engine_hints(monkeypatch):
    monkeypatch.setattr(config, "STATIC_LESSON_MODE", False)
    monkeypatch.setattr(config, "TELEMETRY_BACKEND", "memory")
    mongo.reset_memory_store()

    def fake_collect_rule_outcomes(sections):
        return [
            {
                "section_id": sections[0].id,
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

    monkeypatch.setattr(
        lesson_service.validator_agent,
        "collect_rule_outcomes",
        fake_collect_rule_outcomes,
    )

    client = TestClient(app)
    response = client.post(
        "/lesson",
        json={"topic": "Pandas groupby performance", "level": "beginner"},
    )

    assert response.status_code == 200
    runs = mongo.get_memory_runs()
    assert runs
    hint_codes = {
        hint.get("code")
        for entry in runs[-1].get("mcp_hints", [])
        for hint in entry.get("hints", [])
    }
    assert "expression_result_unused" in hint_codes
