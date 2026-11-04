from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_analyze_endpoint():
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

    data = response.json()

    assert data["total_records"] == 2
    assert data["incident_count"] >= 1
    assert any(
        item["issue_type"] == "missing_values"
        for item in data["incidents"]
    )


def test_analyze_empty_dataset():
    response = client.post(
        "/api/v1/incidents/analyze",
        json={"records": []},
    )

    assert response.status_code == 200
    assert response.json()["incidents"][0]["issue_type"] == "empty_dataset"