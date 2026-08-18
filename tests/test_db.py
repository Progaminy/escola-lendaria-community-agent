import os
from pathlib import Path

from community_agent.db import connect, init_db


def test_init_db(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "test.db")
    init_db()

    with connect() as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

    assert "learners" in tables
    assert "signals" in tables
    assert "followups" in tables
    assert "agent_actions" in tables
