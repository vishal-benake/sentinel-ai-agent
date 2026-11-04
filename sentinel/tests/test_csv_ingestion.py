from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_csv_upload_detects_missing_values():
    response = client.post(
        "/api/v1/ingestion/csv",
        files={
            "file": (
                "events.csv",
                "id,name\n1,Alice\n2,\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["records_processed"] == 2
    assert data["incident_count"] >= 1

    assert any(
        item["issue_type"] == "missing_values"
        for item in data["incidents"]
    )


def test_csv_upload_detects_duplicates():
    response = client.post(
        "/api/v1/ingestion/csv",
        files={
            "file": (
                "events.csv",
                "id,name\n1,Alice\n1,Alice\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    assert any(
        item["issue_type"] == "duplicate_records"
        for item in response.json()["incidents"]
    )


def test_csv_rejects_invalid_row_length():
    response = client.post(
        "/api/v1/ingestion/csv",
        files={
            "file": (
                "events.csv",
                "id,name\n1,Alice,extra\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 422


def test_csv_rejects_non_csv_file():
    response = client.post(
        "/api/v1/ingestion/csv",
        files={
            "file": (
                "events.txt",
                "some text",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400