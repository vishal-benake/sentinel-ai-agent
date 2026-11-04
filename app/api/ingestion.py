from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.csv_ingestion import parse_csv_content
from app.services.incident_detector import detect_incidents
from app.services.incident_repository import save_incidents

router = APIRouter(
    prefix="/api/v1/ingestion",
    tags=["Data Ingestion"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/csv")
async def ingest_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if Path(file.filename or "").suffix.lower() != ".csv":
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="CSV file exceeds the 5 MB limit.",
        )

    try:
        records = parse_csv_content(content)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    report = detect_incidents(records)

    save_incidents(db, report.incidents)

    return {
        "filename": file.filename,
        "records_processed": len(records),
        "incident_count": report.incident_count,
        "incidents": report.incidents,
    }