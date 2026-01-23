# API contract tests
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app
from app.core import config
from app.services import mongo
import pytest

pytestmark = pytest.mark.api

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"


def test_lesson_endpoint():
    response = client.post(
        "/lesson",
        json={
            "session_id": "5c05c610-1d1a-4b3d-8b66-9c7b8c4d6c2f",
            "topic": "pandas groupby performance",
            "level": "beginner",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_minutes"] == 15
    assert body["objective"].startswith("Learn pandas groupby performance")
    assert isinstance(body["sections"], list)
    assert body["sections"][0]["id"] == "concept"


def test_lesson_inserts_telemetry():
    with patch("app.services.lesson_service.insert_lesson_run") as mock_insert:
        response = client.post("/lesson", json={"topic": "x", "level": "beginner"})
        assert response.status_code == 200
        mock_insert.assert_called_once()
        doc = mock_insert.call_args.args[0]
        assert doc["topic"] == "x"
        assert doc["level"] == "beginner"
        assert doc["attempt_count"] == 1
        assert "session_id" in doc


def test_lesson_endpoint_static_mode(monkeypatch):
    monkeypatch.setattr(config, "STATIC_LESSON_MODE", True)
    monkeypatch.setattr(config, "TELEMETRY_BACKEND", "memory")
    mongo.reset_memory_store()

    response = client.post(
        "/lesson",
        json={"topic": "Pandas groupby performance", "level": "intermediate"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_minutes"] == 15
    assert "groupby" in body["sections"][1]["content_markdown"].lower()
    assert mongo.get_memory_runs()


def test_lesson_endpoint_retries_llm_failures(monkeypatch):
    from app.services import lesson_service
    from app.models.agents import GeneratedSection, ContentBlock

    class DummyPlanner:
        def plan(self, topic: str, level: str):
            return []

    class DummyValidator:
        def validate(self, sections):
            return sections

    class DummyContent:
        def __init__(self):
            self.calls = 0
            self.repair_calls = 0

        async def generate(self, topic: str, level: str, planned_sections):
            self.calls += 1
            raise ValueError("Bad formatting")

        async def generate_with_repair(
            self,
            topic: str,
            level: str,
            planned_sections,
            error_summary: str,
        ):
            self.repair_calls += 1
            return [
                GeneratedSection(
                    id="concept",
                    title="Concept",
                    minutes=5,
                    blocks=[ContentBlock(type="text", content="Paragraph.\n\n- bullet\n\n1. step")],
                ),
                GeneratedSection(
                    id="example",
                    title="Example",
                    minutes=5,
                    blocks=[
                        ContentBlock(type="text", content="Paragraph.\n\n- bullet\n\n1. step"),
                        ContentBlock(
                            type="python",
                            content="import pandas as pd\n\nprint('ok')",
                        ),
                    ],
                ),
                GeneratedSection(
                    id="exercise",
                    title="Exercise",
                    minutes=5,
                    blocks=[ContentBlock(type="exercise", content="Do the thing.")],
                ),
            ]

    dummy_content = DummyContent()

    monkeypatch.setattr(config, "USE_LLM_CONTENT", True)
    monkeypatch.setattr(lesson_service, "planner_agent", DummyPlanner())
    monkeypatch.setattr(lesson_service, "content_agent", dummy_content)
    monkeypatch.setattr(lesson_service, "validator_agent", DummyValidator())
    monkeypatch.setattr(lesson_service, "insert_lesson_run", lambda doc: None)
    monkeypatch.setattr(lesson_service, "insert_lesson_failure", lambda doc: None)

    response = client.post(
        "/lesson",
        json={"topic": "x", "level": "beginner"},
    )

    assert response.status_code == 200
    assert dummy_content.calls == 1
    assert dummy_content.repair_calls == 1
