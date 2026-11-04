
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.agents.gemini_investigator import (
    GeminiConfigurationError,
    GeminiServiceError,
)

client = TestClient(app)


def create_test_incident():
    response = client.post(
        "/api/v1/incidents/analyze",
        json={
            "records": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": None},
            ]
        },
    )
    assert response.status_code == 200
    return response.json()["incidents"][0]["id"]


def test_ai_endpoint_returns_investigation():
    incident_id = create_test_incident()

    expected_result = {
        "agent_mode": "gemini",
        "incident_id": incident_id,
        "steps_executed": 2,
        "tool_results": {"inspect_incident": {}},
        "final_analysis": "Missing values were detected.",
        "status": "completed",
        "root_cause_confirmed": False,
    }

    with patch(
        "app.api.investigations.gemini_investigator.investigate",
        return_value=expected_result,
    ):
        response = client.post(
            f"/api/v1/incidents/{incident_id}/investigate-ai"
        )

    assert response.status_code == 200
    assert response.json() == expected_result


def test_ai_endpoint_returns_404_for_unknown_incident():
    response = client.post(
        "/api/v1/incidents/nonexistent-id/investigate-ai"
    )

    assert response.status_code == 404


def test_ai_endpoint_returns_503_without_configuration():
    incident_id = create_test_incident()

    with patch(
        "app.api.investigations.gemini_investigator.investigate",
        side_effect=GeminiConfigurationError(
            "Gemini API key is not configured."
        ),
    ):
        response = client.post(
            f"/api/v1/incidents/{incident_id}/investigate-ai"
        )

    assert response.status_code == 503


def test_ai_endpoint_returns_502_for_gemini_failure():
    incident_id = create_test_incident()

    with patch(
        "app.api.investigations.gemini_investigator.investigate",
        side_effect=GeminiServiceError(
            "Gemini API request failed."
        ),
    ):
        response = client.post(
            f"/api/v1/incidents/{incident_id}/investigate-ai"
        )

    assert response.status_code == 502
