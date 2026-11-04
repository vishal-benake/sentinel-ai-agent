
from google import genai
from google.genai import errors, types
from sqlalchemy.orm import Session

from app.agents.tools import build_tool_registry
from app.config import settings
from app.database.models import IncidentDB


class GeminiConfigurationError(Exception):
    pass


class GeminiServiceError(Exception):
    pass


class GeminiInvestigator:
    MAX_TOOL_CALLS = 4

    def __init__(self, client=None):
        # Client injection allows tests to use a fake Gemini client.
        self._client = client
        self.registry = build_tool_registry()

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not settings.gemini_api_key:
            raise GeminiConfigurationError(
                "Gemini API key is not configured."
            )

        self._client = genai.Client(
            api_key=settings.gemini_api_key
        )

        return self._client

    def _build_gemini_tool(self):
        declarations = []

        for tool in self.registry.list_tools():
            declarations.append(
                types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters_json_schema={
                        "type": "object",
                        "properties": {},
                    },
                )
            )

        return types.Tool(
            function_declarations=declarations
        )

    def _generate(self, contents, tool):
        try:
            return self._get_client().models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=[tool],
                ),
            )
        except errors.APIError as exc:
            print(
                f"[Gemini API Error] "
                f"Code: {getattr(exc, 'code', 'Unknown')} | "
                f"Message: {getattr(exc, 'message', str(exc))}"
            )

            raise GeminiServiceError(
                "Gemini API request failed."
            ) from exc

    def investigate(
        self,
        db: Session,
        incident_id: str,
    ) -> dict:
        incident = db.get(IncidentDB, incident_id)

        if incident is None:
            raise LookupError("Incident not found.")

        tool = self._build_gemini_tool()

        prompt = f"""
You are Sentinel, an AI data pipeline incident investigator.

Investigate the incident using the available read-only tools.

Incident type: {incident.issue_type}
Severity: {incident.severity}

Rules:
1. Inspect the available evidence before drawing conclusions.
2. Select tools only when their results help the investigation.
3. You may inspect only the current incident.
4. Do not invent evidence or claim actions you did not perform.
5. Distinguish confirmed observations from possible explanations.
6. Historical correlation does not prove causation.
7. Never claim the root cause is confirmed unless evidence proves it.
8. Do not suggest that remediation has been performed.

Evidence completeness requirements:
9. Examine every relevant field returned by the evidence inspection tool.
10. For schema_drift incidents, explicitly report:
    - Each affected record index.
    - Missing fields for each affected record.
    - Unexpected fields for each affected record.
    - Aggregate missing-field counts.
    - Aggregate unexpected-field counts.
11. Do not omit unexpected fields merely because missing fields are also present.
12. Clearly distinguish record-level observations from aggregate statistics.
13. Do not infer information that is absent from the inspected evidence.
14. If evidence is truncated or incomplete, explicitly disclose that limitation.

Provide a concise final investigation report containing:
- Confirmed observations
- Evidence examined
- Possible explanations
- Related incident patterns
- Recommended next investigation steps
- Whether the root cause is confirmed
"""

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt)
                ],
            )
        ]

        response = self._generate(contents, tool)

        tool_results = {}
        tool_calls_executed = 0

        while response.function_calls:
            calls = response.function_calls

            if (
                tool_calls_executed + len(calls)
                > self.MAX_TOOL_CALLS
            ):
                break

            if not response.candidates:
                raise GeminiServiceError(
                    "Gemini returned no candidate response."
                )

            model_content = response.candidates[0].content

            if model_content is None:
                raise GeminiServiceError(
                    "Gemini returned an invalid tool-call response."
                )

            contents.append(model_content)

            function_responses = []

            for call in calls:
                try:
                    arguments = dict(call.args or {})

                    # The incident ID is controlled by Sentinel.
                    # Gemini cannot select another incident.
                    if arguments:
                        raise ValueError(
                            "This tool does not accept arguments."
                        )

                    result = self.registry.execute(
                        name=call.name,
                        db=db,
                        incident_id=incident_id,
                    )

                except (ValueError, LookupError) as exc:
                    result = {"error": str(exc)}

                tool_results[call.name] = result

                function_responses.append(
                    types.Part.from_function_response(
                        name=call.name,
                        response={"result": result},
                    )
                )

                tool_calls_executed += 1

            contents.append(
                types.Content(
                    role="user",
                    parts=function_responses,
                )
            )

            response = self._generate(contents, tool)

        if response.function_calls:
            return {
                "agent_mode": "gemini",
                "incident_id": incident_id,
                "steps_executed": tool_calls_executed,
                "tool_results": tool_results,
                "final_analysis": None,
                "status": "tool_limit_reached",
                "root_cause_confirmed": False,
            }

        final_analysis = response.text

        if not final_analysis:
            raise GeminiServiceError(
                "Gemini did not return a final investigation report."
            )

        return {
            "agent_mode": "gemini",
            "incident_id": incident_id,
            "steps_executed": tool_calls_executed,
            "tool_results": tool_results,
            "final_analysis": final_analysis,
            "status": "completed",
            "root_cause_confirmed": False,
        }
