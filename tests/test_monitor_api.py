import os
from pathlib import Path

from fastapi.testclient import TestClient

from community_agent.api import app
from community_agent.db import connect, init_db


def test_monitor_api(tmp_path: Path):
    os.environ["COMMUNITY_AGENT_DB"] = str(tmp_path / "monitor-api.db")
    os.environ["MONITOR_ENABLED"] = "false"

    init_db()

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO learners
            (learner_id, display_name, course,
             last_active_at, failed_attempts, completed_lessons)
            VALUES (
                'L-MON',
                'Monitor Learner',
                'Math',
                '2020-01-01T00:00:00Z',
                0,
                3
            )
            """
        )

    with TestClient(app) as client:
        run = client.post("/monitor/run")
        assert run.status_code == 200
        assert run.json()["new_alerts"] >= 1

        state = client.get("/monitor/state")
        assert state.status_code == 200
        assert state.json()["count"] >= 1

        runs = client.get("/monitor/runs")
        assert runs.status_code == 200
        assert runs.json()["count"] >= 1
