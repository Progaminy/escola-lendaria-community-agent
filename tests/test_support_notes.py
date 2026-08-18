import os
from pathlib import Path

from community_agent.db import connect, init_db
from community_agent.service import record_support_note_data, support_notes_data


def test_support_note_is_persisted(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "notes.db")
    init_db()
    with connect() as conn:
        conn.execute(
            "INSERT INTO learners (learner_id, display_name, course) VALUES ('L-N', 'Learner N', 'Math')"
        )
    result = record_support_note_data("L-N", "Offer a worked example, then ask for a new attempt.", "evt-note")
    assert result["created"] is True
    notes = support_notes_data("L-N")
    assert notes["count"] == 1
    assert "worked example" in notes["items"][0]["note"]
