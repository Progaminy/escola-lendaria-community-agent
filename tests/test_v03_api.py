import os
from pathlib import Path

from fastapi.testclient import TestClient

from community_agent.api import app
from community_agent.db import connect, init_db


def test_v03_endpoints_expose_deterministic_evidence_in_policy_mode(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "v03-api.db")
    os.environ["COMMUNITY_AGENT_MODE"] = "policy"
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO learners (learner_id, display_name, course)
            VALUES ('L-API-3', 'Learner API', 'Math')
            """
        )
        conn.execute(
            """
            INSERT INTO followups
            (learner_id, reason, urgency, owner_role, created_at, event_id)
            VALUES ('L-API-3', 'Review repeated difficulty', 'high', 'teacher',
                    '2026-08-31 08:00:00', 'evt-api-3')
            """
        )

    client = TestClient(app)

    # Human dashboard/API keeps internal identifiers so an authorized person can resolve work.
    plan = client.get("/attention-plan").json()
    assert plan["count"] == 1
    assert plan["items"][0]["learner_id"] == "L-API-3"
    assert plan["items"][0]["priority_score"] >= 100
    assert "advisory ordering" in plan["authority"]

    impact = client.get("/impact").json()
    assert impact["open_human_followups"] == 1
    assert "not a causal" in impact["measurement_scope"]

    # Community briefing gets the same ranking evidence without stable identifiers.
    briefing = client.post("/agent/community-briefing").json()
    assert briefing["ok"] is True
    assert briefing["agent_mode"] == "policy"
    assert briefing["attention_plan"]["count"] == 1
    assert "impact" in briefing
    serialized_plan = repr(briefing["attention_plan"])
    assert "L-API-3" not in serialized_plan
    assert "evt-api-3" not in serialized_plan
    assert "learner_id" not in serialized_plan
    assert "event_id" not in serialized_plan
