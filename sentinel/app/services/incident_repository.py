from sqlalchemy.orm import Session

from app.database.models import IncidentDB, IncidentStatusHistory


def save_incidents(db: Session, incidents: list):
    for incident in incidents:
        existing = db.get(IncidentDB, incident.id)

        if existing:
            continue

        db.add(
            IncidentDB(
                id=incident.id,
                issue_type=incident.issue_type,
                severity=incident.severity.value,
                message=incident.message,
                evidence=incident.evidence,
                status="open",
                detected_at=incident.detected_at,
            )
        )

    db.commit()


def list_incidents(db: Session):
    return (
        db.query(IncidentDB)
        .order_by(IncidentDB.detected_at.desc())
        .all()
    )


def get_incident(db: Session, incident_id: str):
    return db.get(IncidentDB, incident_id)


def update_incident_status(
    db: Session,
    incident: IncidentDB,
    new_status: str,
):
    old_status = incident.status

    if old_status == new_status:
        return incident

    incident.status = new_status

    db.add(
        IncidentStatusHistory(
            incident_id=incident.id,
            old_status=old_status,
            new_status=new_status,
        )
    )

    db.commit()
    db.refresh(incident)

    return incident