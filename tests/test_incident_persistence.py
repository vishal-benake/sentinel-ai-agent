from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_incident_is_persisted():
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

    report = response.json()
    incident_id = report["incidents"][0]["id"]

    details = client.get(
        f"/api/v1/incidents/{incident_id}"
    )

    assert details.status_code == 200
    assert details.json()["id"] == incident_id
    assert details.json()["status"] == "open"


def test_incident_status_history():
    response = client.post(
        "/api/v1/incidents/analyze",
        json={
            "records": [
                {"id": 1, "name": None},
            ]
        },
    )

    incident_id = response.json()["incidents"][0]["id"]

    update = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "investigating"},
    )

    assert update.status_code == 200
    assert update.json()["status"] == "investigating"

    details = client.get(
        f"/api/v1/incidents/{incident_id}"
    ).json()

    assert len(details["history"]) == 1
    assert details["history"][0]["old_status"] == "open"
    assert details["history"][0]["new_status"] == "investigating"


def test_list_incidents():
    response = client.get("/api/v1/incidents")

    assert response.status_code == 200
    assert "incidents" in response.json()
    assert "total" in response.json()