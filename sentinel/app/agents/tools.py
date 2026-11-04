
from dataclasses import dataclass
from typing import Callable, Any

from sqlalchemy.orm import Session

from app.database.models import IncidentDB


@dataclass
class AgentTool:
    name: str
    description: str
    handler: Callable[..., dict]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool):
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")

        self._tools[tool.name] = tool

    def execute(
        self,
        name: str,
        db: Session,
        incident_id: str,
    ) -> dict:
        tool = self._tools.get(name)

        if tool is None:
            raise ValueError(f"Unknown agent tool: {name}")

        return tool.handler(db=db, incident_id=incident_id)

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in self._tools.values()
        ]


def inspect_incident(db: Session, incident_id: str) -> dict:
    incident = db.get(IncidentDB, incident_id)

    if incident is None:
        raise LookupError("Incident not found.")

    return {
        "id": incident.id,
        "issue_type": incident.issue_type,
        "severity": incident.severity,
        "message": incident.message,
        "status": incident.status,
        "detected_at": incident.detected_at.isoformat(),
    }


def inspect_evidence(db: Session, incident_id: str) -> dict:
    incident = db.get(IncidentDB, incident_id)

    if incident is None:
        raise LookupError("Incident not found.")

    return {
        "issue_type": incident.issue_type,
        "evidence": incident.evidence,
    }


def find_related_incidents(db: Session, incident_id: str) -> dict:
    incident = db.get(IncidentDB, incident_id)

    if incident is None:
        raise LookupError("Incident not found.")

    related = (
        db.query(IncidentDB)
        .filter(
            IncidentDB.issue_type == incident.issue_type,
            IncidentDB.id != incident_id,
        )
        .order_by(IncidentDB.detected_at.desc())
        .limit(5)
        .all()
    )

    return {
        "matching_issue_type": incident.issue_type,
        "related_count_returned": len(related),
        "incidents": [
            {
                "id": item.id,
                "severity": item.severity,
                "status": item.status,
                "detected_at": item.detected_at.isoformat(),
            }
            for item in related
        ],
    }


def inspect_status_history(db: Session, incident_id: str) -> dict:
    incident = db.get(IncidentDB, incident_id)

    if incident is None:
        raise LookupError("Incident not found.")

    return {
        "incident_id": incident.id,
        "history": [
            {
                "old_status": item.old_status,
                "new_status": item.new_status,
                "changed_at": item.changed_at.isoformat(),
            }
            for item in incident.history
        ],
    }


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        AgentTool(
            name="inspect_incident",
            description="Read the incident's core details.",
            handler=inspect_incident,
        )
    )

    registry.register(
        AgentTool(
            name="inspect_evidence",
            description=(
                "Read detector evidence for missing values, duplicate records, "
                "and schema drift. Evidence includes affected record counts, "
                "record locations, affected record details, duplicate groups, "
                "missing and unexpected fields, and aggregate field counts."
            ),
            handler=inspect_evidence,
        )
    )

    registry.register(
        AgentTool(
            name="find_related_incidents",
            description="Find recent incidents with the same issue type.",
            handler=find_related_incidents,
        )
    )

    registry.register(
        AgentTool(
            name="inspect_status_history",
            description="Read the incident's status-change history.",
            handler=inspect_status_history,
        )
    )

    return registry
