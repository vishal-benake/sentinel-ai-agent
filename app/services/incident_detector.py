
from collections import Counter
from uuid import uuid4

from app.models.incident import (
    DetectionReport,
    Incident,
    Severity,
)


MAX_MISSING_VALUE_SAMPLES = 20


def create_incident(
    issue_type: str,
    severity: Severity,
    message: str,
    evidence: dict,
) -> Incident:
    return Incident(
        id=str(uuid4()),
        issue_type=issue_type,
        severity=severity,
        message=message,
        evidence=evidence,
    )


def detect_incidents(records: list[dict]) -> DetectionReport:
    incidents = []

    if not records:
        incidents.append(
            create_incident(
                "empty_dataset",
                Severity.CRITICAL,
                "Pipeline received no records.",
                {"record_count": 0},
            )
        )
        return DetectionReport(
            total_records=0,
            incident_count=1,
            incidents=incidents,
        )

    # Detect missing values
    missing_count = 0
    missing_by_field = Counter()
    affected_record_indices = set()
    missing_locations = []
    locations_truncated = False

    for index, record in enumerate(records):
        for field, value in record.items():
            if value is None or value == "":
                missing_count += 1
                missing_by_field[field] += 1
                affected_record_indices.add(index)

                if len(missing_locations) < MAX_MISSING_VALUE_SAMPLES:
                    missing_locations.append(
                        {
                            "record_index": index,
                            "field": field,
                        }
                    )
                else:
                    locations_truncated = True

    if missing_count:
        incidents.append(
            create_incident(
                "missing_values",
                Severity.HIGH,
                "Dataset contains missing values.",
                {
                    "missing_value_count": missing_count,
                    "affected_record_count": len(
                        affected_record_indices
                    ),
                    "missing_by_field": dict(missing_by_field),
                    "locations": missing_locations,
                    "locations_truncated": locations_truncated,
                },
            )
        )

    # Detect duplicate records
    record_groups = {}

    for index, record in enumerate(records):
        serialized = str(sorted(record.items()))
        record_groups.setdefault(serialized, []).append(index)

    duplicate_count = 0
    affected_record_indices = set()
    duplicate_groups = []
    groups_truncated = False

    for indices in record_groups.values():
        if len(indices) <= 1:
            continue

        duplicate_count += len(indices) - 1
        affected_record_indices.update(indices)

        if len(duplicate_groups) < MAX_MISSING_VALUE_SAMPLES:
            duplicate_groups.append(
                {
                    "original_record_index": indices[0],
                    "duplicate_record_indices": indices[1:],
                }
            )
        else:
            groups_truncated = True

    if duplicate_count:
        incidents.append(
            create_incident(
                "duplicate_records",
                Severity.MEDIUM,
                "Dataset contains duplicate records.",
                {
                    "duplicate_count": duplicate_count,
                    "affected_record_count": len(affected_record_indices),
                    "duplicate_groups": duplicate_groups,
                    "groups_truncated": groups_truncated,
                },
            )
        )

    # Detect inconsistent schemas
    expected_fields = set(records[0].keys())
    drift_records = []
    missing_field_counts = Counter()
    unexpected_field_counts = Counter()

    for index, record in enumerate(records):
        actual_fields = set(record.keys())

        missing_fields = expected_fields - actual_fields
        unexpected_fields = actual_fields - expected_fields

        if missing_fields or unexpected_fields:
            drift_records.append(
                {
                    "record_index": index,
                    "missing_fields": sorted(missing_fields),
                    "unexpected_fields": sorted(unexpected_fields),
                }
            )

            missing_field_counts.update(missing_fields)
            unexpected_field_counts.update(unexpected_fields)

    if drift_records:
        common_missing_fields = set(
            drift_records[0]["missing_fields"]
        )

        common_unexpected_fields = set(
            drift_records[0]["unexpected_fields"]
        )

        for item in drift_records[1:]:
            common_missing_fields.intersection_update(
                item["missing_fields"]
            )
            common_unexpected_fields.intersection_update(
                item["unexpected_fields"]
            )

        affected_records = drift_records[
            :MAX_MISSING_VALUE_SAMPLES
        ]

        affected_records_truncated = (
            len(drift_records) > MAX_MISSING_VALUE_SAMPLES
        )

        for item in drift_records:
            incidents.append(
                create_incident(
                    "schema_drift",
                    Severity.HIGH,
                    "Record contains unexpected or missing fields.",
                    {
                        **item,
                        "expected_fields": sorted(expected_fields),
                        "total_affected_records": len(drift_records),
                        "affected_records": affected_records,
                        "affected_records_truncated": (
                            affected_records_truncated
                        ),
                        "missing_field_counts": dict(
                            missing_field_counts
                        ),
                        "unexpected_field_counts": dict(
                            unexpected_field_counts
                        ),
                        "common_missing_fields": sorted(
                            common_missing_fields
                        ),
                        "common_unexpected_fields": sorted(
                            common_unexpected_fields
                        ),
                    },
                )
            )

    # Detect inconsistent data types
    field_types = {}

    for record in records:
        for field, value in record.items():
            if value is None:
                continue

            current_type = type(value).__name__
            field_types.setdefault(field, set()).add(current_type)

    for field, types in field_types.items():
        if len(types) > 1:
            incidents.append(
                create_incident(
                    "type_mismatch",
                    Severity.HIGH,
                    f"Field '{field}' contains inconsistent data types.",
                    {
                        "field": field,
                        "observed_types": sorted(types),
                    },
                )
            )

    return DetectionReport(
        total_records=len(records),
        incident_count=len(incidents),
        incidents=incidents,
    )
