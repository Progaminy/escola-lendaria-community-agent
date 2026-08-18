import os
from pathlib import Path

from community_agent.db import connect, init_db
from community_agent.service import (
    community_stats_data,
    create_human_followup_data,
    resolve_followup_data,
)


def prepare(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "service.db")
    init_db()
    with connect() as conn:
        conn.execute(
            "INSERT INTO learners (learner_id, display_name, course) VALUES ('L-X', 'Learner X', 'Math')"
        )


def test_followup_is_deduplicated(tmp_path: Path):
    prepare(tmp_path)
    first = create_human_followup_data("L-X", "Repeated failure", "high")
    second = create_human_followup_data("L-X", "Repeated failure", "high")
    assert first["created"] is True
    assert second["created"] is False
    assert community_stats_data()["open_followups"] == 1


def test_human_can_resolve_followup(tmp_path: Path):
    prepare(tmp_path)
    item = create_human_followup_data("L-X", "Needs teacher", "medium")
    result = resolve_followup_data(item["followup_id"], "Teacher reviewed the exercise with the learner.")
    assert result["ok"] is True
    assert community_stats_data()["open_followups"] == 0
