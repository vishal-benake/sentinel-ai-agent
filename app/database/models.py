from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class IncidentDB(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True)
    issue_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=False)
    status = Column(String(30), nullable=False, default="open")
    detected_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    history = relationship(
        "IncidentStatusHistory",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentStatusHistory.changed_at",
    )


class IncidentStatusHistory(Base):
    __tablename__ = "incident_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    incident_id = Column(
        String(36),
        ForeignKey("incidents.id"),
        nullable=False,
    )

    old_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False)

    changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    incident = relationship(
        "IncidentDB",
        back_populates="history",
    )