import os
from pathlib import Path

from fastapi.testclient import TestClient

from community_agent.api import app
from community_agent.db import connect, init_db


def test_api_end_to_end(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "api.db")
    os.environ["COMMUNITY_AGENT_MODE"] = "policy"
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO learners
            (learner_id, display_name, course, current_lesson, failed_attempts)
            VALUES ('L-API', 'API Learner', 'Electricity', 'Series circuits', 3)
            """
        )

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        response = client.post(
            "/events",
            json={
                "event_id": "api-event-1",
                "learner_id": "L-API",
                "event_type": "repeated_failure",
                "details": "Learner failed 3 times and requested help.",
                "severity_hint": "medium",
            },
        )
        assert response.status_code == 200
        body = response.json()["result"]
        assert body["decision"]["escalate"] is True
        followups = client.get("/followups").json()
        assert followups["count"] == 1
        decisions = client.get("/decisions").json()
        assert decisions["count"] == 1
