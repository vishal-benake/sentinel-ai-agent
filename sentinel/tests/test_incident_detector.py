from app.services.incident_detector import detect_incidents


def test_detect_missing_values():
    records = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": None},
    ]

    report = detect_incidents(records)

    assert any(
        incident.issue_type == "missing_values"
        for incident in report.incidents
    )


def test_detect_duplicate_records():
    records = [
        {"id": 1, "name": "Alice"},
        {"id": 1, "name": "Alice"},
    ]

    report = detect_incidents(records)

    assert any(
        incident.issue_type == "duplicate_records"
        for incident in report.incidents
    )


def test_detect_schema_drift():
    records = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "email": "test@example.com"},
    ]

    report = detect_incidents(records)

    assert any(
        incident.issue_type == "schema_drift"
        for incident in report.incidents
    )


def test_detect_type_mismatch():
    records = [
        {"id": 1},
        {"id": "two"},
    ]

    report = detect_incidents(records)

    assert any(
        incident.issue_type == "type_mismatch"
        for incident in report.incidents
    )


def test_empty_dataset():
    report = detect_incidents([])

    assert report.incident_count == 1
    assert report.incidents[0].issue_type == "empty_dataset"


def test_missing_value_evidence_includes_record_locations():
    report = detect_incidents(
        [
            {"id": 1, "name": "Alice", "email": ""},
            {"id": 2, "name": None, "email": "bob@example.com"},
        ]
    )

    incident = next(
        item
        for item in report.incidents
        if item.issue_type == "missing_values"
    )

    assert incident.evidence["missing_value_count"] == 2
    assert incident.evidence["affected_record_count"] == 2

    assert incident.evidence["missing_by_field"] == {
        "email": 1,
        "name": 1,
    }

    assert incident.evidence["locations"] == [
        {"record_index": 0, "field": "email"},
        {"record_index": 1, "field": "name"},
    ]

    assert incident.evidence["locations_truncated"] is False

def test_duplicate_evidence_includes_record_locations():
    report = detect_incidents(
        [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 1, "name": "Alice"},
            {"id": 1, "name": "Alice"},
        ]
    )

    incident = next(
        item
        for item in report.incidents
        if item.issue_type == "duplicate_records"
    )

    assert incident.evidence["duplicate_count"] == 2
    assert incident.evidence["affected_record_count"] == 3

    assert incident.evidence["duplicate_groups"] == [
        {
            "original_record_index": 0,
            "duplicate_record_indices": [2, 3],
        }
    ]

    assert incident.evidence["groups_truncated"] is False


def test_duplicate_evidence_limits_reported_groups():
    records = []

    for index in range(21):
        records.append({"id": index})
        records.append({"id": index})

    report = detect_incidents(records)

    incident = next(
        item
        for item in report.incidents
        if item.issue_type == "duplicate_records"
    )

    assert incident.evidence["duplicate_count"] == 21
    assert incident.evidence["affected_record_count"] == 42
    assert len(incident.evidence["duplicate_groups"]) == 20
    assert incident.evidence["groups_truncated"] is True

def test_schema_drift_evidence_includes_field_differences():
    report = detect_incidents(
        [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie", "phone": "1234567890"},
        ]
    )

    incidents = [
        item
        for item in report.incidents
        if item.issue_type == "schema_drift"
    ]

    assert len(incidents) == 2

    first = next(
        item for item in incidents
        if item.evidence["record_index"] == 1
    )

    second = next(
        item for item in incidents
        if item.evidence["record_index"] == 2
    )

    assert first.evidence["missing_fields"] == ["email"]
    assert first.evidence["unexpected_fields"] == []

    assert second.evidence["missing_fields"] == ["email"]
    assert second.evidence["unexpected_fields"] == ["phone"]

    assert first.evidence["total_affected_records"] == 2

    assert first.evidence["missing_field_counts"] == {
        "email": 2,
    }

    assert first.evidence["unexpected_field_counts"] == {
        "phone": 1,
    }

    assert first.evidence["common_missing_fields"] == ["email"]
    assert first.evidence["common_unexpected_fields"] == []


def test_schema_drift_evidence_includes_all_affected_records():
    records = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie", "phone": "1234567890"},
    ]

    report = detect_incidents(records)

    schema_incidents = [
        incident
        for incident in report.incidents
        if incident.issue_type == "schema_drift"
    ]

    assert len(schema_incidents) == 2

    evidence = schema_incidents[0].evidence

    assert evidence["affected_records"] == [
        {
            "record_index": 1,
            "missing_fields": ["email"],
            "unexpected_fields": [],
        },
        {
            "record_index": 2,
            "missing_fields": ["email"],
            "unexpected_fields": ["phone"],
        },
    ]

    assert evidence["affected_records_truncated"] is False
    assert evidence["total_affected_records"] == 2


def test_schema_drift_evidence_limits_affected_records():
    records = [
        {"id": 0, "name": "User 0", "email": "user0@example.com"}
    ]

    records.extend(
        {"id": index, "name": f"User {index}"}
        for index in range(1, 22)
    )

    report = detect_incidents(records)

    schema_incident = next(
        incident
        for incident in report.incidents
        if incident.issue_type == "schema_drift"
    )

    evidence = schema_incident.evidence

    assert evidence["total_affected_records"] == 21
    assert len(evidence["affected_records"]) == 20
    assert evidence["affected_records_truncated"] is True
