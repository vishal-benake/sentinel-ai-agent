
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from google.genai import types

from app.agents.gemini_investigator import GeminiInvestigator
from app.database.database import Base
from app.database.models import IncidentDB


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    incident = IncidentDB(
        id="test-incident-001",
        issue_type="missing_values",
        severity="high",
        message="Missing values detected.",
        evidence={"field": "name", "count": 1},
        status="open",
        detected_at=datetime.now(timezone.utc),
    )

    session.add(incident)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


class FakeModels:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)

        if not self.responses:
            raise AssertionError(
                "Unexpected Gemini API request."
            )

        return self.responses.pop(0)


class FakeGeminiClient:
    def __init__(self, responses):
        self.models = FakeModels(responses)


def function_call(name, args=None):
    return SimpleNamespace(
        name=name,
        args=args or {},
    )


def function_response(name, args=None):
    content = types.Content(
        role="model",
        parts=[
            types.Part.from_function_call(
                name=name,
                args=args or {},
            )
        ],
    )

    return SimpleNamespace(
        function_calls=[function_call(name, args)],
        candidates=[
            SimpleNamespace(content=content)
        ],
        text=None,
    )


def final_response(text="Investigation completed."):
    return SimpleNamespace(
        function_calls=None,
        candidates=[],
        text=text,
    )


def test_gemini_executes_selected_tool(db):
    client = FakeGeminiClient([
        function_response("inspect_evidence"),
        final_response(),
    ])

    investigator = GeminiInvestigator(client=client)

    result = investigator.investigate(
        db=db,
        incident_id="test-incident-001",
    )

    assert result["agent_mode"] == "gemini"
    assert result["status"] == "completed"
    assert result["steps_executed"] == 1

    assert "inspect_evidence" in result["tool_results"]
    assert result["tool_results"]["inspect_evidence"]["evidence"] == {
        "field": "name",
        "count": 1,
    }

    assert result["final_analysis"] == "Investigation completed."
    assert len(client.models.calls) == 2


def test_gemini_does_not_accept_model_supplied_incident_id(db):
    client = FakeGeminiClient([
        function_response(
            "inspect_incident",
            {"incident_id": "another-incident"},
        ),
        final_response(),
    ])

    investigator = GeminiInvestigator(client=client)

    result = investigator.investigate(
        db=db,
        incident_id="test-incident-001",
    )

    tool_result = result["tool_results"]["inspect_incident"]

    assert "error" in tool_result
    assert "does not accept arguments" in tool_result["error"]
    assert result["incident_id"] == "test-incident-001"


def test_gemini_stops_at_tool_call_limit(db):
    responses = [
        function_response("inspect_incident")
        for _ in range(5)
    ]

    client = FakeGeminiClient(responses)
    investigator = GeminiInvestigator(client=client)

    result = investigator.investigate(
        db=db,
        incident_id="test-incident-001",
    )

    assert result["status"] == "tool_limit_reached"
    assert result["steps_executed"] == 4
    assert len(result["tool_results"]) == 1
    assert len(client.models.calls) == 5


def test_gemini_does_not_call_model_for_unknown_incident(db):
    client = FakeGeminiClient([])
    investigator = GeminiInvestigator(client=client)

    with pytest.raises(LookupError):
        investigator.investigate(
            db=db,
            incident_id="nonexistent-incident",
        )

    assert len(client.models.calls) == 0


def test_gemini_returns_error_when_no_final_text(db):
    client = FakeGeminiClient([
        final_response(text=None),
    ])

    investigator = GeminiInvestigator(client=client)

    from app.agents.gemini_investigator import GeminiServiceError

    with pytest.raises(GeminiServiceError):
        investigator.investigate(
            db=db,
            incident_id="test-incident-001",
        )
