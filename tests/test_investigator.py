from fastapi.testclient import TestClient

from app.main import app

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


def test_investigator_executes_tools():
    incident_id = create_test_incident()

    response = client.post(
        f"/api/v1/incidents/{incident_id}/investigate"
    )

    assert response.status_code == 200

    result = response.json()

    assert result["agent_mode"] == "deterministic"
    assert result["incident_id"] == incident_id
    assert result["steps_executed"] == 4

    assert "inspect_incident" in result["tool_results"]
    assert "inspect_evidence" in result["tool_results"]
    assert "find_related_incidents" in result["tool_results"]
    assert "inspect_status_history" in result["tool_results"]


def test_investigator_does_not_claim_confirmed_root_cause():
    incident_id = create_test_incident()

    response = client.post(
        f"/api/v1/incidents/{incident_id}/investigate"
    )

    assert response.status_code == 200

    findings = response.json()["findings"]

    assert findings["root_cause_confirmed"] is False
    assert findings["possible_explanation"]


def test_investigator_returns_404_for_unknown_incident():
    response = client.post(
        "/api/v1/incidents/nonexistent-id/investigate"
    )

    assert response.status_code == 404