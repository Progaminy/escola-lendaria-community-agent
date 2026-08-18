import os
from pathlib import Path

from community_agent.db import connect, init_db


def test_followup_storage(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "test.db")
    init_db()

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO learners (learner_id, display_name, course)
            VALUES ('L-100', 'Test Learner', 'Math')
            """
        )
        conn.execute(
            """
            INSERT INTO followups (learner_id, reason, urgency, owner_role)
            VALUES ('L-100', 'Repeated failure', 'high', 'teacher')
            """
        )
        row = conn.execute(
            "SELECT * FROM followups WHERE learner_id = 'L-100'"
        ).fetchone()

    assert row["status"] == "open"
    assert row["urgency"] == "high"
