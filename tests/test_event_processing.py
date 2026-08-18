import os
from pathlib import Path

from community_agent.db import connect, init_db
from community_agent.service import community_stats_data, process_event_locally


def prepare(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "events.db")
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO learners
            (learner_id, display_name, course, current_lesson, failed_attempts)
            VALUES ('L-X', 'Learner X', 'Math', 'Fractions', 3)
            """
        )


def test_event_is_idempotent(tmp_path: Path):
    prepare(tmp_path)
    first = process_event_locally(
        event_id="evt-1",
        learner_id="L-X",
        event_type="repeated_failure",
        details="Learner failed 3 times.",
        severity_hint="medium",
    )
    second = process_event_locally(
        event_id="evt-1",
        learner_id="L-X",
        event_type="repeated_failure",
        details="Learner failed 3 times.",
        severity_hint="medium",
    )
    assert first["duplicate"] is False
    assert second["duplicate"] is True
    stats = community_stats_data()
    assert stats["events"] == 1
    assert stats["decisions"] == 1
    assert stats["open_followups"] == 1


def test_unknown_learner_is_escalated(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "unknown.db")
    result = process_event_locally(
        event_id="evt-unknown",
        learner_id="missing",
        event_type="question",
        details="I need help.",
        severity_hint="low",
    )
    assert result["decision"]["escalate"] is True
    assert result["decision"]["owner_role"] == "administrator"
