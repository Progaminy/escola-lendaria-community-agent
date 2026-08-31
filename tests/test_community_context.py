import json
import os
from pathlib import Path

from community_agent.community_context import community_overview_data
from community_agent.db import connect, init_db


def test_community_overview_is_aggregate_only(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "community.db")
    init_db()
    with connect() as conn:
        conn.execute(
            "INSERT INTO learners (learner_id, display_name, course) VALUES ('L-PRIVATE', 'Private Name', 'Math')"
        )
        conn.execute(
            """
            INSERT INTO followups (learner_id, reason, urgency, owner_role)
            VALUES ('L-PRIVATE', 'Needs human review', 'high', 'teacher')
            """
        )

    overview = community_overview_data()
    serialized = json.dumps(overview)

    assert overview["privacy_scope"].startswith("aggregate-only")
    assert overview["stats"]["learners"] == 1
    assert overview["stats"]["open_followups"] == 1
    assert "Private Name" not in serialized
    assert "L-PRIVATE" not in serialized
    assert "learner_id" not in serialized
