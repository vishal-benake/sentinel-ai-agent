
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.agents.investigator import IncidentInvestigator
from app.agents.gemini_investigator import (
    GeminiInvestigator,
    GeminiConfigurationError,
    GeminiServiceError,
)


router = APIRouter(
    prefix="/api/v1/incidents",
    tags=["AI Investigations"],
)

investigator = IncidentInvestigator()
gemini_investigator = GeminiInvestigator()


@router.post("/{incident_id}/investigate")
def investigate_incident(
    incident_id: str,
    db: Session = Depends(get_db),
):
    try:
        return investigator.investigate(
            db=db,
            incident_id=incident_id,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.post("/{incident_id}/investigate-ai")
def investigate_incident_with_ai(
    incident_id: str,
    db: Session = Depends(get_db),
):
    try:
        return gemini_investigator.investigate(
            db=db,
            incident_id=incident_id,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except GeminiConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except GeminiServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
