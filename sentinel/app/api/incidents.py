from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.incident_detector import detect_incidents
from app.services.incident_repository import (
    save_incidents,
    list_incidents,
    get_incident,
    update_incident_status,
)

router = APIRouter(
    prefix="/api/v1/incidents",
    tags=["Incidents"],
)


class AnalyzeRequest(BaseModel):
    records: list[dict] = Field(
        ...,
        description="Records to analyze",
    )


class StatusUpdateRequest(BaseModel):
    status: Literal[
        "open",
        "investigating",
        "resolved",
        "dismissed",
    ]


def serialize_incident(incident):
    return {
        "id": incident.id,
        "issue_type": incident.issue_type,
        "severity": incident.severity,
        "message": incident.message,
        "evidence": incident.evidence,
        "status": incident.status,
        "detected_at": incident.detected_at.isoformat(),
    }


@router.post("/analyze")
def analyze_records(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    report = detect_incidents(request.records)

    save_incidents(db, report.incidents)

    return report


@router.get("")
def get_all_incidents(db: Session = Depends(get_db)):
    incidents = list_incidents(db)

    return {
        "total": len(incidents),
        "incidents": [
            serialize_incident(item)
            for item in incidents
        ],
    }


@router.get("/{incident_id}")
def get_incident_details(
    incident_id: str,
    db: Session = Depends(get_db),
):
    incident = get_incident(db, incident_id)

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    result = serialize_incident(incident)

    result["history"] = [
        {
            "old_status": item.old_status,
            "new_status": item.new_status,
            "changed_at": item.changed_at.isoformat(),
        }
        for item in incident.history
    ]

    return result


@router.patch("/{incident_id}/status")
def change_incident_status(
    incident_id: str,
    request: StatusUpdateRequest,
    db: Session = Depends(get_db),
):
    incident = get_incident(db, incident_id)

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    incident = update_incident_status(
        db,
        incident,
        request.status,
    )

    return serialize_incident(incident)