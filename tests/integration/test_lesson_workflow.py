import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core import config
from app.services import mongo

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
