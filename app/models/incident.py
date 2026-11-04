from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Incident(BaseModel):
    id: str
    issue_type: str
    severity: Severity
    message: str
    evidence: dict = Field(default_factory=dict)
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class DetectionReport(BaseModel):
    total_records: int
    incident_count: int
    incidents: list[Incident]