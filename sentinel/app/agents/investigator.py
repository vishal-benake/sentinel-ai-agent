from sqlalchemy.orm import Session

from app.agents.tools import build_tool_registry
from app.database.models import IncidentDB


class IncidentInvestigator:
    MAX_STEPS = 4

    def __init__(self):
        self.registry = build_tool_registry()

    def create_plan(self, issue_type: str) -> list[str]:
        plans = {
            "missing_values": [
                "inspect_incident",
                "inspect_evidence",
                "find_related_incidents",
                "inspect_status_history",
            ],
            "duplicate_records": [
                "inspect_incident",
                "inspect_evidence",
                "find_related_incidents",
                "inspect_status_history",
            ],
            "schema_drift": [
                "inspect_incident",
                "inspect_evidence",
                "find_related_incidents",
                "inspect_status_history",
            ],
            "type_mismatch": [
                "inspect_incident",
                "inspect_evidence",
                "find_related_incidents",
                "inspect_status_history",
            ],
            "empty_dataset": [
                "inspect_incident",
                "inspect_evidence",
                "find_related_incidents",
                "inspect_status_history",
            ],
        }

        return plans.get(
            issue_type,
            ["inspect_incident", "inspect_evidence"],
        )[:self.MAX_STEPS]

    def generate_findings(
        self,
        issue_type: str,
        evidence: dict,
        related: dict,
    ) -> dict:
        explanations = {
            "missing_values": (
                "An upstream source or transformation may have "
                "produced incomplete values."
            ),
            "duplicate_records": (
                "Repeated delivery, replay or missing deduplication "
                "may explain the duplicate records."
            ),
            "schema_drift": (
                "An upstream schema change or inconsistent record "
                "structure may explain the mismatch."
            ),
            "type_mismatch": (
                "Inconsistent source values or transformation logic "
                "may explain the type mismatch."
            ),
            "empty_dataset": (
                "The pipeline may have received no records from its "
                "upstream source."
            ),
        }

        return {
            "confirmed_observation": (
                f"Detector classified this incident as '{issue_type}'."
            ),
            "possible_explanation": explanations.get(
                issue_type,
                "The incident requires further investigation.",
            ),
            "evidence": evidence,
            "related_incident_count": related.get(
                "related_count_returned", 0
            ),
            "root_cause_confirmed": False,
            "limitations": [
                "The available evidence does not establish the upstream root cause.",
                "Historical correlation does not prove causation.",
            ],
        }

    def investigate(
        self,
        db: Session,
        incident_id: str,
    ) -> dict:
        incident = db.get(IncidentDB, incident_id)

        if incident is None:
            raise LookupError("Incident not found.")

        plan = self.create_plan(incident.issue_type)

        tool_results = {}

        for tool_name in plan:
            result = self.registry.execute(
                name=tool_name,
                db=db,
                incident_id=incident_id,
            )

            tool_results[tool_name] = result

        findings = self.generate_findings(
            issue_type=incident.issue_type,
            evidence=tool_results.get(
                "inspect_evidence", {}
            ),
            related=tool_results.get(
                "find_related_incidents", {}
            ),
        )

        return {
            "agent_mode": "deterministic",
            "incident_id": incident_id,
            "plan": plan,
            "steps_executed": len(tool_results),
            "tool_results": tool_results,
            "findings": findings,
        }